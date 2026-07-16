#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PFI_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PFI_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from pfi_os.application.operational_store import OFFICIAL_TABLES  # noqa: E402
from pfi_os.infrastructure.operational_store_backup import (  # noqa: E402
    BackupRestoreError,
    RestoreRollbackError,
    RestoreRolledBackError,
    SQLiteInvariant,
    SnapshotVerificationError,
    create_online_backup,
    restore_verified_backup,
    verify_sqlite_snapshot,
)
from pfi_os.infrastructure.operational_store_runtime import (  # noqa: E402
    OPERATIONAL_MIGRATION_REGISTRY_ID,
)


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


def _policy(
    args: argparse.Namespace,
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[SQLiteInvariant, ...]]:
    tables = set(args.required_table or ())
    migrations = set(args.required_migration or ())
    invariants: tuple[SQLiteInvariant, ...] = ()
    if not args.minimal_policy:
        tables.update(OFFICIAL_TABLES)
        migrations.add(OPERATIONAL_MIGRATION_REGISTRY_ID)
        invariants = _core_invariants()
    return tuple(sorted(tables)), tuple(sorted(migrations)), invariants


def _add_policy_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--minimal-policy",
        action="store_true",
        help=(
            "Verify only explicitly supplied tables/migrations; "
            "default is the PFI operational policy."
        ),
    )
    parser.add_argument("--required-table", action="append", default=[])
    parser.add_argument("--required-migration", action="append", default=[])


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="PFI v0.2.5 consistent SQLite backup and verified atomic restore"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser(
        "inspect",
        help="Take an exclusive maintenance lock and produce a stable target SHA/integrity report.",
    )
    inspect_parser.add_argument("--database", type=Path, required=True)
    _add_policy_arguments(inspect_parser)

    backup_parser = subparsers.add_parser(
        "backup",
        help="Create a new consistent snapshot using sqlite3.Connection.backup().",
    )
    backup_parser.add_argument("--database", type=Path, required=True)
    backup_parser.add_argument("--output", type=Path, required=True)
    _add_policy_arguments(backup_parser)

    restore_parser = subparsers.add_parser(
        "restore",
        help="Verify in isolation, atomically replace, and automatically roll back on failure.",
    )
    restore_parser.add_argument("--backup", type=Path, required=True)
    restore_parser.add_argument("--target", type=Path, required=True)
    restore_parser.add_argument("--staging-directory", type=Path, required=True)
    restore_parser.add_argument("--rollback-directory", type=Path, required=True)
    restore_parser.add_argument("--expected-target-sha256", required=True)
    _add_policy_arguments(restore_parser)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    tables, migrations, invariants = _policy(args)
    try:
        if args.command == "inspect":
            result = verify_sqlite_snapshot(
                args.database,
                required_tables=tables,
                required_migrations=migrations,
                invariants=invariants,
                exclusive=True,
            )
            payload = {**result, "database_path_included": False}
        elif args.command == "backup":
            result = create_online_backup(
                args.database,
                args.output,
                required_tables=tables,
                required_migrations=migrations,
                invariants=invariants,
            )
            payload = {**result, "backup_path_included": False}
        else:
            result = restore_verified_backup(
                args.backup,
                args.target,
                staging_directory=args.staging_directory,
                rollback_directory=args.rollback_directory,
                expected_target_sha256=args.expected_target_sha256,
                candidate_required_tables=tables,
                candidate_required_migrations=migrations,
                candidate_invariants=invariants,
                target_required_tables=tables,
                target_required_migrations=migrations,
                target_invariants=invariants,
            )
            rollback_name = (
                f"pre-restore-{args.target.stem}-{result['restore_id']}.sqlite"
            )
            payload = {
                **result,
                "target_database_path_included": False,
                "rollback_artifact_name": rollback_name,
                "rollback_directory_path_included": False,
            }
    except RestoreRolledBackError as exc:
        print(json.dumps(exc.receipt, ensure_ascii=False, sort_keys=True, indent=2))
        return 2
    except RestoreRollbackError as exc:
        print(json.dumps(exc.receipt, ensure_ascii=False, sort_keys=True, indent=2))
        return 3
    except SnapshotVerificationError as exc:
        print(json.dumps(exc.report, ensure_ascii=False, sort_keys=True, indent=2))
        return 2
    except (BackupRestoreError, OSError, ValueError) as exc:
        print(
            json.dumps(
                {"status": "failed", "error_type": type(exc).__name__, "message": str(exc)},
                ensure_ascii=False,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 2
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
