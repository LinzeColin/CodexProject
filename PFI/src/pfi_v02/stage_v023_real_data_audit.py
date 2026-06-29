from __future__ import annotations

import csv
import hashlib
import json
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from pfi_v02.stage_v023_data_state import CORE_METRICS, build_metric_state


VERSION = "v0.2.3"
STAGE = "Stage 2"
PHASE_ID = "V023-S2-P2.2"
PHASE_NAME = "真实数据审计"

PERSONAL_DATA_EXTENSIONS = (".csv", ".tsv", ".json", ".jsonl", ".sqlite", ".db", ".parquet", ".xlsx")
IGNORED_REPO_PARTS = {
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "assets",
    "cache",
    "docs",
    "fx_snapshots",
    "reports",
    "stage_0",
    "stage_1",
    "stage_2",
    "systemAudit",
    "tests",
    "web",
}


@dataclass(frozen=True)
class Stage2Phase22Contract:
    version: str
    stage: str
    phase_id: str
    phase_name: str
    current_phase_only: bool
    max_one_phase_per_run: bool
    no_mock_financial_data: bool
    allowed_files: tuple[str, ...]
    validation_commands: tuple[str, ...]
    evidence_files: tuple[str, ...]
    explicitly_not_done: tuple[str, ...]


def build_stage2_phase22_contract() -> dict[str, Any]:
    contract = Stage2Phase22Contract(
        version=VERSION,
        stage=STAGE,
        phase_id=PHASE_ID,
        phase_name=PHASE_NAME,
        current_phase_only=True,
        max_one_phase_per_run=True,
        no_mock_financial_data=True,
        allowed_files=(
            "PFI/src/pfi_v02/stage_v023_real_data_audit.py",
            "PFI/src/pfi_v02/stage_v023_data_state.py",
            "PFI/tests/test_v023_stage2_data_state_machine.py",
            "PFI/tests/test_v023_no_mock_financial_data.py",
            "PFI/docs/pfi_v023/STAGE2_DATA_TRUST.md",
            "PFI/reports/pfi_v023/stage_2/*",
        ),
        validation_commands=(
            "python3 -m py_compile PFI/src/pfi_v02/stage_v023_real_data_audit.py",
            "python3 -m pytest PFI/tests/test_v023_stage2_data_state_machine.py -q",
            "python3 -m pytest PFI/tests/test_v023_no_mock_financial_data.py -q",
            "git diff --check -- PFI",
        ),
        evidence_files=(
            "PFI/docs/pfi_v023/STAGE2_DATA_TRUST.md",
            "PFI/reports/pfi_v023/stage_2/phase_2_2/evidence.json",
            "PFI/reports/pfi_v023/stage_2/phase_2_2/terminal.log",
            "PFI/reports/pfi_v023/stage_2/phase_2_2/changed_files.txt",
        ),
        explicitly_not_done=(
            "页面门禁接入",
            "核心指标接入 UI",
            "截图验收",
            "app bundle reinstall",
            "GitHub main upload for intermediate phase",
        ),
    )
    return asdict(contract)


def build_real_data_audit(pfi_root: Path) -> dict[str, Any]:
    pfi_root = pfi_root.resolve()
    candidate_paths = _candidate_paths(pfi_root)
    ignored_repo_files = _ignored_repo_files(pfi_root)
    data_files = _discover_personal_data_files(candidate_paths)

    file_records = [_file_audit_record(path) for path in data_files]
    file_count = len(file_records)
    raw_record_count = sum(record["record_count"] for record in file_records if record["record_count"] is not None)
    standardized_record_count = sum(
        record["record_count"]
        for record in file_records
        if record["record_count"] is not None and _is_standardized_path(record["path"])
    )
    date_range = _date_range_from_records(file_records)
    as_of = _latest_modified_at(file_records)
    audit_status = "ready" if file_count else "not_mounted"
    blocking_reasons = [] if file_count else ["未挂载真实个人财务数据源；当前只发现 README、FX 快照或系统验收文件。"]

    return {
        "version": VERSION,
        "stage": STAGE,
        "phase_id": PHASE_ID,
        "phase_name": PHASE_NAME,
        "audit_status": audit_status,
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "candidate_paths": [record for record in candidate_paths],
        "ignored_repo_files": ignored_repo_files,
        "personal_data_files": file_records,
        "file_count": file_count,
        "raw_record_count": raw_record_count,
        "standardized_record_count": standardized_record_count,
        "date_range": date_range,
        "as_of": as_of,
        "account_count": 0,
        "holding_count": 0,
        "read_model_hash": _metadata_hash(file_records) if file_records else None,
        "last_updated": as_of,
        "blocking_reasons": blocking_reasons,
        "no_mock_financial_data": True,
        "core_metric_states": _core_metric_states(audit_status),
    }


def _candidate_paths(pfi_root: Path) -> list[dict[str, Any]]:
    candidates = (
        (Path("/Users/linzezhang/MetaDatabase/PFI"), "external_home_metadatabase"),
        (Path("/Users/linzezhang/Documents/MetaDatabase/PFI"), "external_documents_metadatabase"),
        (Path("/Users/linzezhang/Documents/Codex/MetaDatabase/PFI"), "external_codex_metadatabase"),
        (Path("/Users/linzezhang/Documents/Codex/CodexProject/PFI/MetaDatabase"), "main_repo_pfi_metadatabase"),
        (pfi_root / "MetaDatabase", "current_worktree_pfi_metadatabase"),
        (pfi_root / "data", "current_worktree_pfi_data"),
    )
    records: list[dict[str, Any]] = []
    for path, role in candidates:
        records.append(
            {
                "path": str(path),
                "exists": path.exists(),
                "role": role,
                "file_count": _safe_file_count(path) if path.exists() else 0,
            }
        )
    return records


def _discover_personal_data_files(candidate_paths: Iterable[dict[str, Any]]) -> list[Path]:
    found: list[Path] = []
    seen: set[str] = set()
    for record in candidate_paths:
        path = Path(record["path"])
        if not record["exists"] or not path.exists():
            continue
        for file_path in path.rglob("*"):
            if not file_path.is_file():
                continue
            if _is_ignored_path(file_path):
                continue
            if file_path.suffix.lower() not in PERSONAL_DATA_EXTENSIONS:
                continue
            resolved = str(file_path.resolve())
            if resolved not in seen:
                found.append(file_path)
                seen.add(resolved)
    return sorted(found, key=lambda item: str(item))


def _ignored_repo_files(pfi_root: Path) -> list[str]:
    ignored: list[str] = []
    for base in (pfi_root / "MetaDatabase", pfi_root / "data"):
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            if _is_ignored_path(path) or path.suffix.lower() not in PERSONAL_DATA_EXTENSIONS:
                ignored.append(_relative_to_pfi(path, pfi_root))
    return sorted(set(ignored))


def _file_audit_record(path: Path) -> dict[str, Any]:
    stat = path.stat()
    record_count = _count_records(path)
    return {
        "path": str(path),
        "extension": path.suffix.lower(),
        "size_bytes": stat.st_size,
        "modified_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "record_count": record_count,
    }


def _count_records(path: Path) -> int | None:
    suffix = path.suffix.lower()
    try:
        if suffix in {".csv", ".tsv"}:
            delimiter = "\t" if suffix == ".tsv" else ","
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                return sum(1 for _ in csv.DictReader(handle, delimiter=delimiter))
        if suffix == ".jsonl":
            with path.open("r", encoding="utf-8") as handle:
                return sum(1 for line in handle if line.strip())
        if suffix == ".json":
            payload = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(payload, list):
                return len(payload)
            if isinstance(payload, dict):
                for key in ("records", "transactions", "items", "rows", "holdings", "accounts"):
                    value = payload.get(key)
                    if isinstance(value, list):
                        return len(value)
            return 0
        if suffix in {".sqlite", ".db"}:
            return _count_sqlite_rows(path)
    except (OSError, UnicodeError, csv.Error, json.JSONDecodeError, sqlite3.Error):
        return None
    return None


def _count_sqlite_rows(path: Path) -> int:
    total = 0
    with sqlite3.connect(str(path)) as connection:
        rows = connection.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        for (table_name,) in rows:
            if table_name == "sqlite_sequence":
                continue
            quoted = '"' + table_name.replace('"', '""') + '"'
            total += int(connection.execute(f"SELECT COUNT(*) FROM {quoted}").fetchone()[0])
    return total


def _date_range_from_records(file_records: list[dict[str, Any]]) -> dict[str, Any]:
    # Phase 2.2 does not inspect private field values deeply. Date extraction is
    # left null unless a future mounted read model exposes an explicit date index.
    if not file_records:
        return {"start": None, "end": None}
    return {"start": None, "end": None}


def _latest_modified_at(file_records: list[dict[str, Any]]) -> str | None:
    values = [record["modified_at"] for record in file_records if record.get("modified_at")]
    return max(values) if values else None


def _metadata_hash(file_records: list[dict[str, Any]]) -> str:
    payload = json.dumps(file_records, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _core_metric_states(audit_status: str) -> list[dict[str, Any]]:
    status = "not_mounted" if audit_status == "not_mounted" else "review_required"
    message = "未挂载真实个人财务数据源" if status == "not_mounted" else "真实数据审计完成，仍需接入 read model"
    return [
        build_metric_state(metric_id, label, status=status, currency=currency, message_zh=message)
        for metric_id, label, currency in CORE_METRICS
    ]


def _is_standardized_path(path_text: str) -> bool:
    lowered = path_text.lower()
    return "processed" in lowered or "standardized" in lowered or "normalized" in lowered


def _is_ignored_path(path: Path) -> bool:
    parts = set(path.parts)
    if path.name in {"README.md", ".gitkeep"}:
        return True
    return bool(parts & IGNORED_REPO_PARTS)


def _safe_file_count(path: Path) -> int:
    try:
        return sum(1 for item in path.rglob("*") if item.is_file())
    except OSError:
        return 0


def _relative_to_pfi(path: Path, pfi_root: Path) -> str:
    try:
        return "PFI/" + str(path.relative_to(pfi_root))
    except ValueError:
        return str(path)
