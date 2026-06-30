from __future__ import annotations

import csv
import hashlib
import json
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
        "message_zh": "未挂载真实个人财务数据源",
        "generated_at_utc": generated_at,
    }

    if not data_root_path.exists():
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
            "evidence_hash": _hash_files(source_paths),
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
        "message_zh": read_input["message_zh"],
        "generated_at_utc": read_input["generated_at_utc"],
    }


def iter_stage6_transactions(read_input: dict[str, Any]) -> Iterable[dict[str, str]]:
    if read_input.get("status") != "ready":
        return ()
    path = Path(str(read_input["transactions_path"]))
    return _iter_csv_rows(path)


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


def _count_transactions(path: Path) -> int:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return sum(1 for _row in csv.DictReader(handle))


def _iter_csv_rows(path: Path) -> Iterable[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            yield {str(key): str(value or "") for key, value in row.items()}


def _hash_files(paths: Iterable[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths, key=lambda item: str(item)):
        digest.update(str(path.name).encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return "sha256:" + digest.hexdigest()


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
