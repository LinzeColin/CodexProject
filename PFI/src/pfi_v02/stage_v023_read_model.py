from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


VERSION = "v0.2.3"
STAGE = "Stage 6"
PHASE_ID = "V023-S6-P6.1"

ALIPAY_DIR = Path("alipay_daily")
PROCESSED_DIR = ALIPAY_DIR / "processed"
RAW_DIR = ALIPAY_DIR / "raw"
TRANSACTIONS_FILE = PROCESSED_DIR / "alipay_transactions.csv"
MANIFEST_FILE = PROCESSED_DIR / "alipay_import_manifest.json"


def build_stage6_read_model_input(
    project_root: str | Path | None = None,
    *,
    data_root: str | Path | None = None,
) -> dict[str, Any]:
    pfi_root, repo_root = _resolve_roots(project_root)
    data_root_path = Path(data_root).expanduser().resolve() if data_root else (repo_root / "MetaDatabase" / "PFI").resolve()
    transactions_path = data_root_path / TRANSACTIONS_FILE
    manifest_path = data_root_path / MANIFEST_FILE
    raw_dir = data_root_path / RAW_DIR
    generated_at = _utc_now()

    base = {
        "schema": "PFIV023Stage6ReadModelInputV1",
        "version": VERSION,
        "stage": STAGE,
        "phase_id": PHASE_ID,
        "status": "not_mounted",
        "source_type": "metadatabase_pfi",
        "storage_mode": "filesystem",
        "pfi_root": str(pfi_root),
        "repo_root": str(repo_root),
        "data_root": str(data_root_path),
        "transactions_path": str(transactions_path),
        "manifest_path": str(manifest_path),
        "raw_dir": str(raw_dir),
        "raw_files": [],
        "raw_file_count": 0,
        "transaction_count": 0,
        "date_range": {"start": None, "end": None},
        "event_counts": {},
        "review_count": 0,
        "columns": [],
        "as_of": None,
        "evidence_hash": None,
        "git_ref": None,
        "git_object_status": None,
        "git_raw_paths": [],
        "git_transactions_path": None,
        "git_manifest_path": None,
        "message_zh": "未挂载真实个人财务数据源",
        "generated_at_utc": generated_at,
    }

    if not data_root_path.exists():
        if data_root is None:
            git_tree_input = _build_git_tree_input(base, repo_root)
            if git_tree_input is not None:
                return git_tree_input
        return base
    if not transactions_path.exists() or not manifest_path.exists():
        base["status"] = "path_error"
        base["message_zh"] = "真实数据路径不完整，缺少交易文件或导入清单"
        return base

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        columns = _read_csv_columns(transactions_path)
        raw_files = sorted(path for path in raw_dir.glob("*") if path.is_file()) if raw_dir.exists() else []
    except PermissionError:
        base["status"] = "permission_error"
        base["message_zh"] = "无权限读取真实个人财务数据"
        return base
    except (OSError, UnicodeError, csv.Error, json.JSONDecodeError):
        base["status"] = "parse_error"
        base["message_zh"] = "真实个人财务数据解析失败"
        return base

    transaction_count = int(manifest.get("transaction_count") or _count_transactions(transactions_path))
    date_start = manifest.get("date_start")
    date_end = manifest.get("date_end")
    source_paths = [manifest_path, transactions_path, *raw_files]
    base.update(
        {
            "status": "ready",
            "raw_files": [str(path) for path in raw_files],
            "raw_file_count": len(raw_files),
            "transaction_count": transaction_count,
            "date_range": {"start": date_start, "end": date_end},
            "event_counts": dict(manifest.get("event_counts") or {}),
            "review_count": int(manifest.get("review_count") or 0),
            "columns": columns,
            "as_of": date_end,
            "evidence_hash": _hash_files(source_paths, root=data_root_path),
            "message_zh": "真实 MetaDatabase/PFI 数据已加载",
        }
    )
    return base


def build_stage6_read_model_audit(
    project_root: str | Path | None = None,
    *,
    data_root: str | Path | None = None,
) -> dict[str, Any]:
    read_input = build_stage6_read_model_input(project_root=project_root, data_root=data_root)
    return {
        "schema": "PFIV023Stage6ReadModelAuditV1",
        "version": VERSION,
        "stage": STAGE,
        "phase_id": PHASE_ID,
        "status": read_input["status"],
        "source_type": read_input["source_type"],
        "storage_mode": read_input["storage_mode"],
        "data_root": read_input["data_root"],
        "transactions_path": read_input["transactions_path"],
        "manifest_path": read_input["manifest_path"],
        "raw_file_count": read_input["raw_file_count"],
        "transaction_count": read_input["transaction_count"],
        "date_range": read_input["date_range"],
        "event_counts": read_input["event_counts"],
        "review_count": read_input["review_count"],
        "columns": read_input["columns"],
        "as_of": read_input["as_of"],
        "evidence_hash": read_input["evidence_hash"],
        "git_ref": read_input["git_ref"],
        "git_object_status": read_input["git_object_status"],
        "git_raw_paths": read_input["git_raw_paths"],
        "git_transactions_path": read_input["git_transactions_path"],
        "git_manifest_path": read_input["git_manifest_path"],
        "message_zh": read_input["message_zh"],
        "generated_at_utc": read_input["generated_at_utc"],
    }


def iter_stage6_transactions(read_input: dict[str, Any]) -> Iterable[dict[str, str]]:
    if read_input.get("status") != "ready":
        return ()
    if read_input.get("storage_mode") == "git_tree":
        repo_root = Path(str(read_input["repo_root"]))
        git_path = str(read_input.get("git_transactions_path") or "")
        raw = _git_blob(repo_root, git_path, ref=str(read_input.get("git_ref") or "HEAD"))
        if raw is None:
            return ()
        return _iter_csv_rows_text(raw.decode("utf-8-sig"))
    path = Path(str(read_input["transactions_path"]))
    return _iter_csv_rows(path)


def _build_git_tree_input(base: dict[str, Any], repo_root: Path) -> dict[str, Any] | None:
    git_ref = _git_commit_oid(repo_root)
    if git_ref is None:
        return None
    git_data_root = Path("MetaDatabase") / "PFI"
    manifest_rel = git_data_root / MANIFEST_FILE
    transactions_rel = git_data_root / TRANSACTIONS_FILE
    raw_dir_rel = git_data_root / RAW_DIR

    tracked_paths = _git_tree_files(repo_root, git_data_root.as_posix(), ref=git_ref)
    git_metadata = {
        "storage_mode": "git_tree",
        "git_ref": git_ref,
        "git_transactions_path": transactions_rel.as_posix(),
        "git_manifest_path": manifest_rel.as_posix(),
    }
    if tracked_paths is None:
        base.update(git_metadata)
        base["git_object_status"] = "unavailable"
        base["message_zh"] = "当前 Git tree 财务数据对象不可用，未允许网络补取"
        return base

    required_paths = {manifest_rel.as_posix(), transactions_rel.as_posix()}
    if not required_paths.issubset(tracked_paths):
        return None
    base.update(git_metadata)

    manifest_raw = _git_blob(repo_root, manifest_rel.as_posix(), ref=git_ref)
    transactions_raw = _git_blob(repo_root, transactions_rel.as_posix(), ref=git_ref)
    if manifest_raw is None or transactions_raw is None:
        base["git_object_status"] = "unavailable"
        base["message_zh"] = "当前 Git tree 财务数据对象不可用，未允许网络补取"
        return base

    raw_prefix = raw_dir_rel.as_posix() + "/"
    raw_paths = [path for path in tracked_paths if path.startswith(raw_prefix)]
    raw_blobs: list[tuple[str, bytes]] = []
    for raw_path in raw_paths:
        raw = _git_blob(repo_root, raw_path, ref=git_ref)
        if raw is None:
            base["git_object_status"] = "unavailable"
            base["message_zh"] = "当前 Git tree 财务数据对象不可用，未允许网络补取"
            return base
        relative_path = Path(raw_path).relative_to(git_data_root).as_posix()
        raw_blobs.append((relative_path, raw))

    try:
        manifest = json.loads(manifest_raw.decode("utf-8"))
        transactions_text = transactions_raw.decode("utf-8-sig")
        columns = _read_csv_columns_text(transactions_text)
    except (UnicodeError, csv.Error, json.JSONDecodeError):
        base["status"] = "parse_error"
        base["git_object_status"] = "available"
        base["message_zh"] = "当前 Git tree 财务数据解析失败"
        return base

    transaction_count = int(manifest.get("transaction_count") or _count_transactions_text(transactions_text))
    date_start = manifest.get("date_start")
    date_end = manifest.get("date_end")
    source_blobs = [
        (MANIFEST_FILE.as_posix(), manifest_raw),
        (TRANSACTIONS_FILE.as_posix(), transactions_raw),
        *raw_blobs,
    ]
    base.update(
        {
            "status": "ready",
            "storage_mode": "git_tree",
            "raw_files": raw_paths,
            "raw_file_count": len(raw_paths),
            "transaction_count": transaction_count,
            "date_range": {"start": date_start, "end": date_end},
            "event_counts": dict(manifest.get("event_counts") or {}),
            "review_count": int(manifest.get("review_count") or 0),
            "columns": columns,
            "as_of": date_end,
            "evidence_hash": _hash_blobs(source_blobs),
            "git_object_status": "available",
            "git_raw_paths": raw_paths,
            "message_zh": "真实 MetaDatabase/PFI 数据已从当前 Git tree 只读加载",
        }
    )
    return base


def _resolve_roots(project_root: str | Path | None) -> tuple[Path, Path]:
    if project_root is None:
        pfi_root = Path(__file__).resolve().parents[2]
        return pfi_root, pfi_root.parent

    raw_root = Path(project_root).expanduser().resolve()
    if (raw_root / "src" / "pfi_v02").exists():
        return raw_root, raw_root.parent
    if (raw_root / "PFI" / "src" / "pfi_v02").exists():
        return raw_root / "PFI", raw_root
    return raw_root, raw_root


def _read_csv_columns(path: Path) -> list[str]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or [])


def _read_csv_columns_text(text: str) -> list[str]:
    reader = csv.DictReader(io.StringIO(text))
    return list(reader.fieldnames or [])


def _count_transactions(path: Path) -> int:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return sum(1 for _row in csv.DictReader(handle))


def _count_transactions_text(text: str) -> int:
    return sum(1 for _row in csv.DictReader(io.StringIO(text)))


def _iter_csv_rows(path: Path) -> Iterable[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            yield {str(key): str(value or "") for key, value in row.items()}


def _iter_csv_rows_text(text: str) -> Iterable[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(text))
    for row in reader:
        yield {str(key): str(value or "") for key, value in row.items()}


def _hash_files(paths: Iterable[Path], *, root: Path) -> str:
    return _hash_blobs((path.relative_to(root).as_posix(), path.read_bytes()) for path in paths)


def _hash_blobs(blobs: Iterable[tuple[str, bytes]]) -> str:
    digest = hashlib.sha256()
    for name, raw in sorted(blobs, key=lambda item: item[0]):
        digest.update(name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(raw)
        digest.update(b"\0")
    return "sha256:" + digest.hexdigest()


def _git_blob(repo_root: Path, path: str, *, ref: str) -> bytes | None:
    try:
        completed = subprocess.run(
            ["git", "cat-file", "blob", f"{ref}:{path}"],
            cwd=repo_root,
            capture_output=True,
            env=_git_environment(),
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return completed.stdout if completed.returncode == 0 else None


def _git_commit_oid(repo_root: Path) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "--verify", "HEAD^{commit}"],
            cwd=repo_root,
            capture_output=True,
            env=_git_environment(),
            text=True,
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    oid = completed.stdout.strip().lower()
    if completed.returncode != 0 or len(oid) not in {40, 64} or any(char not in "0123456789abcdef" for char in oid):
        return None
    return oid


def _git_tree_files(repo_root: Path, path: str, *, ref: str) -> list[str] | None:
    try:
        completed = subprocess.run(
            ["git", "ls-tree", "-r", "--name-only", ref, "--", path],
            cwd=repo_root,
            capture_output=True,
            env=_git_environment(),
            text=True,
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if completed.returncode != 0:
        return None
    return sorted(line.strip() for line in completed.stdout.splitlines() if line.strip())


def _git_environment() -> dict[str, str]:
    env = dict(os.environ)
    env["GIT_NO_LAZY_FETCH"] = "1"
    return env


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
