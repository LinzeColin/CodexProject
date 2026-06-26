from __future__ import annotations

import hashlib
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pfi_os.application.operational_store import (
    OFFICIAL_TABLES,
    default_data_home,
    default_operational_db_path,
)
from pfi_os.storage import atomic_write_json


PHASE_D_BACKUP_RESTORE_ACCEPTANCE_SCHEMA = "PFIOSPhaseDBackupRestoreAcceptanceV1"
PHASE_D_BACKUP_RESTORE_CONTRACT_SCHEMA = "PFIOSPhaseDBackupRestoreContractV1"


def build_phase_d_backup_restore_contract(
    project_root: Path | str,
    data_home: Path | str | None = None,
) -> dict[str, Any]:
    root = _resolve(project_root)
    resolved_data_home = _resolve(data_home) if data_home is not None else _resolve(default_data_home())
    return {
        "schema": PHASE_D_BACKUP_RESTORE_CONTRACT_SCHEMA,
        "phase": "Phase D",
        "acceptance_schema": PHASE_D_BACKUP_RESTORE_ACCEPTANCE_SCHEMA,
        "project_root": str(root),
        "data_home": str(resolved_data_home),
        "required_input": "$PFI_DATA_HOME/private/operational/pfi.sqlite",
        "artifact_policy": {
            "backup_dir": "$PFI_DATA_HOME/runtime/backups",
            "restore_staging_dir": "$PFI_DATA_HOME/runtime/restore_staging",
            "manifest_scope": "private_runtime_only",
            "commit_sqlite_to_git": False,
            "commit_private_manifest_to_git": False,
            "public_summary_must_be_sanitized": True,
        },
        "verification_policy": {
            "sqlite_integrity_check": True,
            "official_table_row_counts_must_match": True,
            "backup_checksum_recorded": True,
            "restored_checksum_recorded": True,
        },
        "safety_boundary": _safety_boundary(),
    }


def run_phase_d_backup_restore_acceptance(
    project_root: Path | str,
    data_home: Path | str | None = None,
    *,
    now: datetime | None = None,
    write_manifest: bool = True,
) -> dict[str, Any]:
    root = _resolve(project_root)
    resolved_data_home = _resolve(data_home) if data_home is not None else _resolve(default_data_home())
    operational_db = _resolve(default_operational_db_path(resolved_data_home))
    generated_at = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    run_id = _run_id(generated_at)
    backup_dir = resolved_data_home / "runtime" / "backups"
    restore_root = resolved_data_home / "runtime" / "restore_staging"
    restore_run_dir = restore_root / run_id
    backup_path = backup_dir / f"{run_id}.sqlite"
    restored_path = restore_run_dir / "pfi.sqlite"
    manifest_path = backup_dir / f"{run_id}.manifest.json"

    checks: list[dict[str, Any]] = []
    checks.extend(_preflight_checks(root, resolved_data_home, operational_db))

    if any(check["required"] and check["status"] == "Fail" for check in checks):
        return _payload(
            root=root,
            data_home=resolved_data_home,
            operational_db=operational_db,
            generated_at=generated_at,
            run_id=run_id,
            checks=checks,
            backup_path=backup_path,
            restored_path=restored_path,
            manifest_path=manifest_path,
            manifest_written=False,
            source_counts={},
            restored_counts={},
        )

    manifest_written = False
    source_counts: dict[str, int] = {}
    restored_counts: dict[str, int] = {}
    try:
        backup_dir.mkdir(parents=True, exist_ok=True)
        restore_run_dir.mkdir(parents=True, exist_ok=True)
        _sqlite_backup(operational_db, backup_path)
        _sqlite_backup(backup_path, restored_path)

        source_counts = _table_counts(operational_db)
        backup_counts = _table_counts(backup_path)
        restored_counts = _table_counts(restored_path)
        backup_integrity = _sqlite_integrity_check(backup_path)
        restored_integrity = _sqlite_integrity_check(restored_path)

        checks.extend(
            [
                _check(
                    category="backup_restore",
                    code="BACKUP_WRITTEN",
                    status="Pass" if backup_path.exists() and backup_path.stat().st_size > 0 else "Fail",
                    required=True,
                    message="Operational SQLite backup was written under private runtime backups.",
                    evidence_scope="private_runtime",
                ),
                _check(
                    category="backup_restore",
                    code="RESTORE_STAGED",
                    status="Pass" if restored_path.exists() and restored_path.stat().st_size > 0 else "Fail",
                    required=True,
                    message="Backup was restored into private runtime restore staging.",
                    evidence_scope="private_runtime",
                ),
                _check(
                    category="backup_restore",
                    code="BACKUP_SQLITE_INTEGRITY",
                    status="Pass" if backup_integrity == "ok" else "Fail",
                    required=True,
                    message=f"Backup SQLite integrity_check returned {backup_integrity}.",
                    evidence_scope="checksum_only",
                ),
                _check(
                    category="backup_restore",
                    code="RESTORED_SQLITE_INTEGRITY",
                    status="Pass" if restored_integrity == "ok" else "Fail",
                    required=True,
                    message=f"Restored SQLite integrity_check returned {restored_integrity}.",
                    evidence_scope="checksum_only",
                ),
                _check(
                    category="backup_restore",
                    code="OFFICIAL_TABLE_COUNTS_MATCH",
                    status="Pass" if source_counts == backup_counts == restored_counts else "Fail",
                    required=True,
                    message="Official Operational Store table row counts match source, backup, and restore.",
                    evidence_scope="row_counts_only",
                ),
            ]
        )

        manifest = _manifest_payload(
            generated_at=generated_at,
            run_id=run_id,
            source_counts=source_counts,
            restored_counts=restored_counts,
            backup_checksum=_sha256_file(backup_path),
            restored_checksum=_sha256_file(restored_path),
            backup_size=backup_path.stat().st_size,
            restored_size=restored_path.stat().st_size,
        )
        if write_manifest:
            atomic_write_json(manifest_path, manifest, sort_keys=True)
            manifest_written = manifest_path.exists()
        checks.append(
            _check(
                category="backup_restore",
                code="PRIVATE_MANIFEST_WRITTEN",
                status="Pass" if manifest_written or not write_manifest else "Fail",
                required=write_manifest,
                message="Private manifest is written outside public Git.",
                evidence_scope="private_runtime",
            )
        )
    except Exception as exc:  # pragma: no cover - contract tests cover fail-closed branches.
        checks.append(
            _check(
                category="backup_restore",
                code="BACKUP_RESTORE_EXCEPTION",
                status="Fail",
                required=True,
                message=f"{type(exc).__name__}: {exc}",
                evidence_scope="error_message",
            )
        )

    return _payload(
        root=root,
        data_home=resolved_data_home,
        operational_db=operational_db,
        generated_at=generated_at,
        run_id=run_id,
        checks=checks,
        backup_path=backup_path,
        restored_path=restored_path,
        manifest_path=manifest_path,
        manifest_written=manifest_written,
        source_counts=source_counts,
        restored_counts=restored_counts,
    )


def _preflight_checks(project_root: Path, data_home: Path, operational_db: Path) -> list[dict[str, Any]]:
    return [
        _check(
            category="data_boundary",
            code="DATA_HOME_OUTSIDE_REPO",
            status="Pass" if not _is_relative_to(data_home, project_root) else "Fail",
            required=True,
            message="$PFI_DATA_HOME must stay outside public Git before backup/restore acceptance.",
            evidence_scope="path_policy",
        ),
        _check(
            category="data_boundary",
            code="OPERATIONAL_DB_EXISTS",
            status="Pass" if operational_db.exists() else "Fail",
            required=True,
            message="Operational SQLite must exist before backup/restore acceptance.",
            evidence_scope="path_policy",
        ),
        _check(
            category="data_boundary",
            code="OPERATIONAL_DB_OUTSIDE_REPO",
            status="Pass" if not _is_relative_to(operational_db, project_root) else "Fail",
            required=True,
            message="Operational SQLite must not be stored in public Git.",
            evidence_scope="path_policy",
        ),
        _check(
            category="backup_restore",
            code="BACKUP_DIR_UNDER_DATA_HOME",
            status="Pass" if _is_relative_to(data_home / "runtime" / "backups", data_home) else "Fail",
            required=True,
            message="Backup target is scoped under $PFI_DATA_HOME/runtime/backups.",
            evidence_scope="path_policy",
        ),
        _check(
            category="backup_restore",
            code="RESTORE_DIR_UNDER_DATA_HOME",
            status="Pass" if _is_relative_to(data_home / "runtime" / "restore_staging", data_home) else "Fail",
            required=True,
            message="Restore staging is scoped under $PFI_DATA_HOME/runtime/restore_staging.",
            evidence_scope="path_policy",
        ),
    ]


def _payload(
    *,
    root: Path,
    data_home: Path,
    operational_db: Path,
    generated_at: datetime,
    run_id: str,
    checks: list[dict[str, Any]],
    backup_path: Path,
    restored_path: Path,
    manifest_path: Path,
    manifest_written: bool,
    source_counts: dict[str, int],
    restored_counts: dict[str, int],
) -> dict[str, Any]:
    status = _overall_status(checks)
    public_summary = {
        "schema": PHASE_D_BACKUP_RESTORE_ACCEPTANCE_SCHEMA,
        "phase": "Phase D",
        "status": status,
        "run_id": run_id,
        "generated_at": generated_at.isoformat(timespec="seconds"),
        "artifact_policy": "private_runtime_only",
        "backup_scope": "$PFI_DATA_HOME/runtime/backups",
        "restore_scope": "$PFI_DATA_HOME/runtime/restore_staging",
        "official_table_counts_match": bool(source_counts) and source_counts == restored_counts,
        "manifest_written": manifest_written,
        "failed_checks": [check["code"] for check in checks if check["status"] == "Fail"],
    }
    return {
        "schema": PHASE_D_BACKUP_RESTORE_ACCEPTANCE_SCHEMA,
        "phase": "Phase D",
        "status": status,
        "generated_at": generated_at.isoformat(timespec="seconds"),
        "run_id": run_id,
        "project_root": str(root),
        "data_home": str(data_home),
        "operational_db_path": str(operational_db),
        "checks": checks,
        "private_artifacts": {
            "backup_path": str(backup_path),
            "restored_path": str(restored_path),
            "manifest_path": str(manifest_path),
            "commit_to_git": False,
        },
        "sanitized_public_summary": public_summary,
        "source_table_counts": source_counts,
        "restored_table_counts": restored_counts,
        "safety_boundary": _safety_boundary(),
        "next_action": _next_action(status),
    }


def _manifest_payload(
    *,
    generated_at: datetime,
    run_id: str,
    source_counts: dict[str, int],
    restored_counts: dict[str, int],
    backup_checksum: str,
    restored_checksum: str,
    backup_size: int,
    restored_size: int,
) -> dict[str, Any]:
    return {
        "schema": PHASE_D_BACKUP_RESTORE_ACCEPTANCE_SCHEMA,
        "run_id": run_id,
        "generated_at": generated_at.isoformat(timespec="seconds"),
        "artifact_policy": "private_runtime_only",
        "backup_scope": "$PFI_DATA_HOME/runtime/backups",
        "restore_scope": "$PFI_DATA_HOME/runtime/restore_staging",
        "backup_sha256": backup_checksum,
        "restored_sha256": restored_checksum,
        "backup_size_bytes": backup_size,
        "restored_size_bytes": restored_size,
        "source_table_counts": source_counts,
        "restored_table_counts": restored_counts,
        "commit_to_git": False,
    }


def _sqlite_backup(source_path: Path, target_path: Path) -> None:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(source_path) as source, sqlite3.connect(target_path) as target:
        source.backup(target)


def _sqlite_integrity_check(db_path: Path) -> str:
    with sqlite3.connect(db_path) as conn:
        row = conn.execute("PRAGMA integrity_check").fetchone()
    return str(row[0]) if row else ""


def _table_counts(db_path: Path) -> dict[str, int]:
    with sqlite3.connect(db_path) as conn:
        existing = {
            row[0]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
        }
        counts: dict[str, int] = {}
        for table_name in sorted(OFFICIAL_TABLES):
            counts[table_name] = (
                int(conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0])
                if table_name in existing
                else -1
            )
    return counts


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _check(
    *,
    category: str,
    code: str,
    status: str,
    required: bool,
    message: str,
    evidence_scope: str,
) -> dict[str, Any]:
    return {
        "category": category,
        "code": code,
        "status": status,
        "required": required,
        "message": message,
        "evidence_scope": evidence_scope,
    }


def _overall_status(checks: list[dict[str, Any]]) -> str:
    if any(check["required"] and check["status"] == "Fail" for check in checks):
        return "Blocked"
    return "Pass"


def _next_action(status: str) -> str:
    if status == "Pass":
        return "Use sanitized public summary in Phase 5 package; keep SQLite artifacts outside Git."
    return "Fix data-home boundary or Operational SQLite availability, then rerun backup/restore acceptance."


def _safety_boundary() -> dict[str, bool]:
    return {
        "read_only": False,
        "creates_private_runtime_artifacts": True,
        "mutates_operational_db": False,
        "starts_services": False,
        "network_calls": False,
        "provider_calls": False,
        "broker_calls": False,
        "order_execution": False,
        "holding_mutation": False,
        "research_only": True,
    }


def _run_id(generated_at: datetime) -> str:
    return f"phase_d_backup_restore_{generated_at.strftime('%Y%m%dT%H%M%SZ')}"


def _resolve(path: Path | str) -> Path:
    return Path(path).expanduser().resolve(strict=False)


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False
