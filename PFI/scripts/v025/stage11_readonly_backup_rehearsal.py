#!/usr/bin/env python3
"""Rehearse a real SQLite backup and isolated restore without mutating the source."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sqlite3
import stat
import sys
import tempfile


PFI_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PFI_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from pfi_os.application.operational_store import (  # noqa: E402
    OFFICIAL_TABLES,
    default_operational_db_path,
)
from pfi_os.infrastructure.operational_store_backup import (  # noqa: E402
    RestoreRolledBackError,
    SQLiteInvariant,
    create_online_backup,
    restore_verified_backup,
    verify_sqlite_snapshot,
)


SCHEMA = "PFIV025Stage11ReadOnlyRealBackupRestoreRehearsalV1"


def _core_invariants() -> tuple[SQLiteInvariant, ...]:
    return (
        SQLiteInvariant(
            "source_records_required_fields",
            "SELECT COUNT(*) FROM source_records "
            "WHERE trim(source_id)='' OR trim(as_of)='' OR trim(evidence_class)=''",
            0,
        ),
        SQLiteInvariant(
            "source_versions_required_fields",
            "SELECT COUNT(*) FROM source_versions "
            "WHERE trim(version_id)='' OR trim(source_id)='' OR trim(as_of)='' "
            "OR trim(evidence_class)=''",
            0,
        ),
        SQLiteInvariant(
            "evidence_records_required_fields",
            "SELECT COUNT(*) FROM evidence_records "
            "WHERE trim(evidence_id)='' OR trim(source_id)='' OR trim(as_of)='' "
            "OR trim(evidence_class)=''",
            0,
        ),
        SQLiteInvariant(
            "job_progress_bounds",
            "SELECT COUNT(*) FROM job_records WHERE progress < 0 OR progress > 1",
            0,
        ),
        SQLiteInvariant(
            "task_review_flag_boolean",
            "SELECT COUNT(*) FROM task_records WHERE human_review_required NOT IN (0,1)",
            0,
        ),
    )


def _file_state(path: Path) -> tuple[int, int, int, int, int, int]:
    current = path.stat()
    return (
        current.st_ino,
        current.st_size,
        current.st_mtime_ns,
        current.st_ctime_ns,
        stat.S_IMODE(current.st_mode),
        current.st_nlink,
    )


def _directory_state(path: Path) -> dict[str, tuple[int, int, int, int, int, int]]:
    return {entry.name: _file_state(entry) for entry in sorted(path.iterdir())}


def _add_isolated_marker(path: Path, marker: str) -> None:
    with sqlite3.connect(path) as conn:
        conn.execute(
            "CREATE TABLE stage11_isolated_restore_marker("
            "singleton INTEGER PRIMARY KEY CHECK(singleton=1), marker TEXT NOT NULL)"
        )
        conn.execute(
            "INSERT INTO stage11_isolated_restore_marker(singleton,marker) VALUES (1,?)",
            (marker,),
        )
        conn.commit()


def _marker_exists(path: Path) -> bool:
    with sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True) as conn:
        return conn.execute(
            "SELECT COUNT(*) FROM sqlite_master "
            "WHERE type='table' AND name='stage11_isolated_restore_marker'"
        ).fetchone()[0] == 1


def run_rehearsal(database: Path) -> dict[str, object]:
    source = database.expanduser().resolve(strict=True)
    if not source.is_file() or source.is_symlink() or source.stat().st_size <= 0:
        raise ValueError("source must be a non-empty regular SQLite file")
    required_tables = tuple(sorted(OFFICIAL_TABLES))
    invariants = _core_invariants()
    source_file_before = _file_state(source)
    source_directory_before = _directory_state(source.parent)
    source_lock_name = f".{source.name}.pfi-operation.lock"
    source_lock_existed_before = source_lock_name in source_directory_before
    canonical_source = source == default_operational_db_path().expanduser().resolve(strict=False)

    with tempfile.TemporaryDirectory(prefix="pfi-stage11-readonly-rehearsal-") as temp_name:
        root = Path(temp_name)
        os.chmod(root, 0o700)
        backup = root / "backups" / "online.sqlite"
        online = create_online_backup(
            source,
            backup,
            required_tables=required_tables,
            invariants=invariants,
        )

        source_file_after_backup = _file_state(source)
        source_directory_after_backup = _directory_state(source.parent)
        if source_file_after_backup != source_file_before:
            raise RuntimeError("source file metadata changed during read-only backup")
        if source_directory_after_backup != source_directory_before:
            raise RuntimeError("source directory changed during read-only backup")

        success_target = root / "success-target" / "pfi.sqlite"
        create_online_backup(
            backup,
            success_target,
            required_tables=required_tables,
            invariants=invariants,
        )
        _add_isolated_marker(success_target, "success-target-only")
        success_before = verify_sqlite_snapshot(
            success_target,
            required_tables=required_tables,
            invariants=invariants,
            exclusive=True,
        )
        success_restore = restore_verified_backup(
            backup,
            success_target,
            staging_directory=root / "success-staging",
            rollback_directory=root / "success-rollback",
            expected_target_sha256=str(success_before["database_sha256"]),
            candidate_required_tables=required_tables,
            candidate_invariants=invariants,
            target_required_tables=required_tables,
            target_invariants=invariants,
        )
        success_marker_removed = not _marker_exists(success_target)

        rollback_target = root / "rollback-target" / "pfi.sqlite"
        create_online_backup(
            backup,
            rollback_target,
            required_tables=required_tables,
            invariants=invariants,
        )
        _add_isolated_marker(rollback_target, "rollback-target-only")
        rollback_before = verify_sqlite_snapshot(
            rollback_target,
            required_tables=required_tables,
            invariants=invariants,
            exclusive=True,
        )

        def inject(stage: str) -> None:
            if stage == "after_atomic_replace":
                raise RuntimeError("stage11 isolated rollback injection")

        try:
            restore_verified_backup(
                backup,
                rollback_target,
                staging_directory=root / "rollback-staging",
                rollback_directory=root / "rollback-artifacts",
                expected_target_sha256=str(rollback_before["database_sha256"]),
                candidate_required_tables=required_tables,
                candidate_invariants=invariants,
                target_required_tables=required_tables,
                target_invariants=invariants,
                failure_injector=inject,
            )
        except RestoreRolledBackError as exc:
            rollback_receipt = exc.receipt
        else:
            raise RuntimeError("injected isolated restore failure did not roll back")

        rollback_marker_preserved = _marker_exists(rollback_target)
        final_source_file_state = _file_state(source)
        final_source_directory_state = _directory_state(source.parent)
        verification = online["verification"]
        invariant_results = verification["application_invariants"]
        payload: dict[str, object] = {
            "schema": SCHEMA,
            "status": "pass",
            "source_classification": (
                "canonical_private_operational_database"
                if canonical_source
                else "operator_selected_operational_database"
            ),
            "canonical_private_database_used": canonical_source,
            "canonical_private_database_mutated": False,
            "real_database_pages_read": True,
            "real_financial_rows_exported": False,
            "private_values_emitted": False,
            "source_path_included": False,
            "source_sha256_included": False,
            "source_file_state_unchanged": final_source_file_state == source_file_before,
            "source_directory_entries_unchanged": (
                final_source_directory_state == source_directory_before
            ),
            "source_lock_existed_before": source_lock_existed_before,
            "source_lock_created": (
                not source_lock_existed_before
                and source_lock_name in final_source_directory_state
            ),
            "source_open_mode": online["source_open_mode"],
            "source_directory_mutated": online["source_directory_mutated"],
            "online_backup_method": online["method"],
            "online_file_copy_used": online["online_file_copy_used"],
            "backup_integrity_check": verification["integrity_check"],
            "backup_foreign_key_issue_count": verification["foreign_key_issue_count"],
            "backup_missing_table_count": len(verification["missing_tables"]),
            "backup_observed_table_count": verification["observed_table_count"],
            "backup_observed_migration_count": verification["observed_migration_count"],
            "application_invariant_count": len(invariant_results),
            "application_invariants_pass": all(
                row["status"] == "pass" for row in invariant_results
            ),
            "isolated_success_restore_status": success_restore["status"],
            "isolated_candidate_verified_before_replace": success_restore[
                "candidate_verified_before_replace"
            ],
            "isolated_same_filesystem_atomic_replace": success_restore[
                "same_filesystem_atomic_replace"
            ],
            "isolated_success_marker_removed": success_marker_removed,
            "isolated_rollback_status": rollback_receipt["status"],
            "isolated_automatic_rollback_performed": rollback_receipt[
                "automatic_rollback_performed"
            ],
            "isolated_rollback_marker_preserved": rollback_marker_preserved,
            "temporary_private_artifacts_retained": False,
            "finder_used": False,
            "launchservices_used": False,
            "gui_file_operations_used": False,
            "external_network_performed": False,
        }
        required_truths = (
            payload["source_file_state_unchanged"],
            payload["source_directory_entries_unchanged"],
            not payload["source_lock_created"],
            payload["application_invariants_pass"],
            payload["isolated_candidate_verified_before_replace"],
            payload["isolated_same_filesystem_atomic_replace"],
            payload["isolated_success_marker_removed"],
            payload["isolated_automatic_rollback_performed"],
            payload["isolated_rollback_marker_preserved"],
        )
        if not all(required_truths):
            payload["status"] = "fail"
        return payload


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--database",
        type=Path,
        default=default_operational_db_path(),
        help="Operational SQLite source; the path is never emitted in the receipt.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        payload = run_rehearsal(args.database)
    except Exception as exc:
        payload = {
            "schema": SCHEMA,
            "status": "fail",
            "error_type": type(exc).__name__,
            "source_path_included": False,
            "private_values_emitted": False,
        }
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if payload["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
