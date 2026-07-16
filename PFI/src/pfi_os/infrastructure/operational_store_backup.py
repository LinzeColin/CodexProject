from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import stat
import uuid
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

from pfi_os.infrastructure.operational_store_runtime import operational_store_guard


ONLINE_BACKUP_RECEIPT_SCHEMA = "PFIV025SQLiteOnlineBackupReceiptV1"
RESTORE_RECEIPT_SCHEMA = "PFIV025SQLiteRestoreReceiptV1"
SNAPSHOT_VERIFICATION_SCHEMA = "PFIV025SQLiteSnapshotVerificationV1"
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,127}$")
_INVARIANT_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_READ_ONLY_QUERY = re.compile(r"^\s*(?:SELECT|WITH)\b", re.IGNORECASE)
_SIDECAR_SUFFIXES = ("-journal", "-wal", "-shm")


class BackupRestoreError(RuntimeError):
    """Base class for fail-closed backup/restore errors."""


class SnapshotVerificationError(BackupRestoreError):
    def __init__(self, message: str, *, report: dict[str, object]):
        super().__init__(message)
        self.report = report


class RestoreRolledBackError(BackupRestoreError):
    def __init__(self, message: str, *, receipt: dict[str, object]):
        super().__init__(message)
        self.receipt = receipt


class RestoreRollbackError(BackupRestoreError):
    def __init__(self, message: str, *, receipt: dict[str, object]):
        super().__init__(message)
        self.receipt = receipt


@dataclass(frozen=True)
class SQLiteInvariant:
    invariant_id: str
    query: str
    expected_scalar: object

    def validate(self) -> None:
        if not _INVARIANT_ID.fullmatch(str(self.invariant_id)):
            raise ValueError(f"invalid invariant_id: {self.invariant_id!r}")
        normalized = str(self.query).strip()
        if not _READ_ONLY_QUERY.match(normalized) or ";" in normalized:
            raise ValueError(
                f"invariant {self.invariant_id!r} must be one read-only SELECT/WITH statement"
            )


def verify_sqlite_snapshot(
    database_path: Path | str,
    *,
    required_tables: Iterable[str] = (),
    required_migrations: Iterable[str] = (),
    invariants: Sequence[SQLiteInvariant] = (),
    exclusive: bool = False,
) -> dict[str, object]:
    path = _existing_regular_file(database_path, label="database")
    with operational_store_guard(path, exclusive=exclusive):
        return _verify_sqlite_snapshot_unlocked(
            path,
            required_tables=required_tables,
            required_migrations=required_migrations,
            invariants=invariants,
            guard_mode="exclusive" if exclusive else "shared",
        )


def create_online_backup(
    source_database: Path | str,
    backup_path: Path | str,
    *,
    required_tables: Iterable[str] = (),
    required_migrations: Iterable[str] = (),
    invariants: Sequence[SQLiteInvariant] = (),
    pages_per_step: int = 256,
    sleep_seconds: float = 0.025,
) -> dict[str, object]:
    source = _existing_regular_file(source_database, label="source database")
    target = _new_file_path(backup_path, label="backup")
    _require_distinct_paths(source, target)
    _prepare_private_directory(target.parent)

    try:
        copy_result = _copy_database_unlocked(
            source,
            target,
            pages_per_step=pages_per_step,
            sleep_seconds=sleep_seconds,
        )
        verification = _verify_sqlite_snapshot_unlocked(
            target,
            required_tables=required_tables,
            required_migrations=required_migrations,
            invariants=invariants,
            guard_mode="isolated_backup",
        )
    except BaseException:
        target.unlink(missing_ok=True)
        _fsync_directory(target.parent)
        raise

    return {
        "schema": ONLINE_BACKUP_RECEIPT_SCHEMA,
        "status": "pass",
        "method": "sqlite_online_backup_api",
        "online_file_copy_used": False,
        "source_open_mode": "sqlite_uri_mode_ro_query_only",
        "source_directory_mutated": False,
        "source_guard": "sqlite_online_backup_consistent_snapshot",
        "backup_overwrite_allowed": False,
        "backup_sha256": verification["database_sha256"],
        "backup_size_bytes": verification["database_size_bytes"],
        "pages_per_step": pages_per_step,
        "progress_step_count": copy_result["progress_step_count"],
        "reported_page_count": copy_result["reported_page_count"],
        "verification": verification,
    }


def restore_verified_backup(
    backup_path: Path | str,
    target_database: Path | str,
    *,
    staging_directory: Path | str,
    rollback_directory: Path | str,
    expected_target_sha256: str,
    candidate_required_tables: Iterable[str] = (),
    candidate_required_migrations: Iterable[str] = (),
    candidate_invariants: Sequence[SQLiteInvariant] = (),
    target_required_tables: Iterable[str] | None = None,
    target_required_migrations: Iterable[str] | None = None,
    target_invariants: Sequence[SQLiteInvariant] | None = None,
    pages_per_step: int = 256,
    sleep_seconds: float = 0.025,
    failure_injector: Callable[[str], None] | None = None,
) -> dict[str, object]:
    backup = _existing_regular_file(backup_path, label="backup")
    target = _existing_regular_file(target_database, label="target database")
    staging = _directory_path(staging_directory, label="staging directory")
    rollback_root = _directory_path(rollback_directory, label="rollback directory")
    expected_hash = _normalize_sha256(expected_target_sha256)
    _prepare_private_directory(staging)
    _prepare_private_directory(rollback_root)
    _require_distinct_paths(backup, target)
    _require_same_device(target.parent, staging, rollback_root)

    candidate_tables = tuple(_validated_identifiers(candidate_required_tables, "table"))
    candidate_migrations = tuple(str(item) for item in candidate_required_migrations)
    original_tables = tuple(
        candidate_tables
        if target_required_tables is None
        else _validated_identifiers(target_required_tables, "table")
    )
    original_migrations = (
        candidate_migrations
        if target_required_migrations is None
        else tuple(str(item) for item in target_required_migrations)
    )
    original_invariants = candidate_invariants if target_invariants is None else target_invariants

    backup_verification = verify_sqlite_snapshot(
        backup,
        required_tables=candidate_tables,
        required_migrations=candidate_migrations,
        invariants=candidate_invariants,
    )
    restore_id = uuid.uuid4().hex
    candidate = staging / f".{target.name}.{restore_id}.candidate.sqlite"
    rollback = rollback_root / f"pre-restore-{target.stem}-{restore_id}.sqlite"
    _new_file_path(candidate, label="restore candidate")
    _new_file_path(rollback, label="rollback snapshot")

    installed = False
    rollback_verification: dict[str, object] | None = None
    candidate_verification: dict[str, object] | None = None
    target_before_verification: dict[str, object] | None = None
    installed_verification: dict[str, object] | None = None
    try:
        with operational_store_guard(backup):
            _copy_database_unlocked(
                backup,
                candidate,
                pages_per_step=pages_per_step,
                sleep_seconds=sleep_seconds,
            )
        candidate_verification = _verify_sqlite_snapshot_unlocked(
            candidate,
            required_tables=candidate_tables,
            required_migrations=candidate_migrations,
            invariants=candidate_invariants,
            guard_mode="isolated_restore_candidate",
        )
        _inject(failure_injector, "after_candidate_verification")

        with operational_store_guard(target, exclusive=True):
            try:
                _require_no_sqlite_sidecars(target)
                target_before_verification = _verify_sqlite_snapshot_unlocked(
                    target,
                    required_tables=original_tables,
                    required_migrations=original_migrations,
                    invariants=original_invariants,
                    guard_mode="exclusive_restore_precondition",
                )
                if target_before_verification["database_sha256"] != expected_hash:
                    raise BackupRestoreError(
                        "target database changed after operator inspection; "
                        "refusing unknown overwrite"
                    )

                _copy_database_unlocked(
                    target,
                    rollback,
                    pages_per_step=pages_per_step,
                    sleep_seconds=sleep_seconds,
                )
                rollback_verification = _verify_sqlite_snapshot_unlocked(
                    rollback,
                    required_tables=original_tables,
                    required_migrations=original_migrations,
                    invariants=original_invariants,
                    guard_mode="verified_rollback_snapshot",
                )
                _inject(failure_injector, "after_rollback_snapshot")
                _require_no_sqlite_sidecars(target)
                if _sha256_file(target) != expected_hash:
                    raise BackupRestoreError(
                        "target database changed during restore preparation; "
                        "refusing atomic replacement"
                    )

                os.replace(candidate, target)
                installed = True
                os.chmod(target, 0o600)
                _fsync_file(target)
                _fsync_directory(candidate.parent)
                _fsync_directory(target.parent)
                _inject(failure_injector, "after_atomic_replace")

                installed_verification = _verify_sqlite_snapshot_unlocked(
                    target,
                    required_tables=candidate_tables,
                    required_migrations=candidate_migrations,
                    invariants=candidate_invariants,
                    guard_mode="exclusive_post_replace",
                )
                if (
                    installed_verification["database_sha256"]
                    != candidate_verification["database_sha256"]
                ):
                    raise BackupRestoreError(
                        "installed database no longer matches verified candidate"
                    )
                _inject(failure_injector, "after_post_replace_verification")
            except BaseException as exc:
                if installed:
                    receipt = _rollback_after_failed_replace(
                        target=target,
                        rollback=rollback,
                        restore_id=restore_id,
                        failure=exc,
                        required_tables=original_tables,
                        required_migrations=original_migrations,
                        invariants=original_invariants,
                        rollback_verification=rollback_verification,
                    )
                    raise RestoreRolledBackError(
                        "restore failed after atomic replacement; original database was restored",
                        receipt=receipt,
                    ) from exc
                raise

        return {
            "schema": RESTORE_RECEIPT_SCHEMA,
            "status": "restored",
            "restore_id": restore_id,
            "backup_sha256": backup_verification["database_sha256"],
            "target_before_sha256": target_before_verification["database_sha256"],
            "candidate_sha256": candidate_verification["database_sha256"],
            "installed_sha256": installed_verification["database_sha256"],
            "rollback_snapshot_sha256": rollback_verification["database_sha256"],
            "candidate_verified_before_replace": True,
            "rollback_snapshot_verified_before_replace": True,
            "expected_target_hash_enforced": True,
            "same_filesystem_atomic_replace": True,
            "exclusive_operational_lock": True,
            "atomic_replace_performed": True,
            "automatic_rollback_performed": False,
            "rollback_artifact_retained": rollback.exists(),
            "verification": installed_verification,
        }
    except (RestoreRolledBackError, RestoreRollbackError):
        candidate.unlink(missing_ok=True)
        raise
    except BaseException as exc:
        candidate.unlink(missing_ok=True)
        rollback.unlink(missing_ok=True)
        _fsync_directory(staging)
        _fsync_directory(rollback_root)
        if isinstance(exc, BackupRestoreError):
            raise
        raise BackupRestoreError(f"restore preparation failed: {type(exc).__name__}") from exc


def _rollback_after_failed_replace(
    *,
    target: Path,
    rollback: Path,
    restore_id: str,
    failure: BaseException,
    required_tables: Iterable[str],
    required_migrations: Iterable[str],
    invariants: Sequence[SQLiteInvariant],
    rollback_verification: dict[str, object] | None,
) -> dict[str, object]:
    receipt: dict[str, object] = {
        "schema": RESTORE_RECEIPT_SCHEMA,
        "status": "rollback_failed",
        "restore_id": restore_id,
        "failure_type": type(failure).__name__,
        "atomic_replace_performed": True,
        "automatic_rollback_attempted": True,
        "automatic_rollback_performed": False,
    }
    try:
        if rollback_verification is None or not rollback.exists():
            raise BackupRestoreError("verified rollback snapshot is unavailable")
        os.replace(rollback, target)
        os.chmod(target, 0o600)
        _fsync_file(target)
        _fsync_directory(rollback.parent)
        _fsync_directory(target.parent)
        restored = _verify_sqlite_snapshot_unlocked(
            target,
            required_tables=required_tables,
            required_migrations=required_migrations,
            invariants=invariants,
            guard_mode="exclusive_automatic_rollback",
        )
        if restored["database_sha256"] != rollback_verification["database_sha256"]:
            raise BackupRestoreError("automatic rollback content hash mismatch")
        receipt.update(
            {
                "status": "rolled_back",
                "automatic_rollback_performed": True,
                "rollback_verification": restored,
                "rollback_snapshot_consumed": True,
            }
        )
        return receipt
    except BaseException as rollback_exc:
        receipt["rollback_failure_type"] = type(rollback_exc).__name__
        raise RestoreRollbackError(
            "restore failed and automatic rollback could not be verified",
            receipt=receipt,
        ) from rollback_exc


def _verify_sqlite_snapshot_unlocked(
    database_path: Path,
    *,
    required_tables: Iterable[str],
    required_migrations: Iterable[str],
    invariants: Sequence[SQLiteInvariant],
    guard_mode: str,
) -> dict[str, object]:
    path = _existing_regular_file(database_path, label="database")
    tables_required = tuple(_validated_identifiers(required_tables, "table"))
    migrations_required = tuple(
        sorted({str(item).strip() for item in required_migrations if str(item).strip()})
    )
    for invariant in invariants:
        invariant.validate()

    uri = f"{path.as_uri()}?mode=ro"
    conn: sqlite3.Connection | None = None
    try:
        conn = sqlite3.connect(uri, uri=True, timeout=30, isolation_level=None)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA query_only = ON")
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA busy_timeout = 30000")
        integrity_rows = [str(row[0]) for row in conn.execute("PRAGMA integrity_check")]
        foreign_key_rows = conn.execute("PRAGMA foreign_key_check").fetchall()
        observed_tables = {
            str(row[0])
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
        }
        missing_tables = sorted(set(tables_required) - observed_tables)
        schema_rows = [
            tuple(str(value or "") for value in row)
            for row in conn.execute(
                "SELECT type, name, tbl_name, sql FROM sqlite_master "
                "WHERE sql IS NOT NULL ORDER BY type, name"
            )
        ]
        serialized_schema = json.dumps(
            schema_rows,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        schema_sha256 = hashlib.sha256(serialized_schema).hexdigest()
        migration_ids, migration_registry_valid = _migration_state(conn, observed_tables)
        missing_migrations = sorted(set(migrations_required) - migration_ids)
        invariant_results = []
        for invariant in invariants:
            try:
                rows = conn.execute(invariant.query).fetchall()
                passed = (
                    len(rows) == 1
                    and len(rows[0]) == 1
                    and rows[0][0] == invariant.expected_scalar
                )
                invariant_results.append(
                    {
                        "invariant_id": invariant.invariant_id,
                        "status": "pass" if passed else "fail",
                        "result_shape": [len(rows), len(rows[0]) if rows else 0],
                    }
                )
            except sqlite3.DatabaseError as exc:
                invariant_results.append(
                    {
                        "invariant_id": invariant.invariant_id,
                        "status": "fail",
                        "error_type": type(exc).__name__,
                    }
                )
        page_count = int(conn.execute("PRAGMA page_count").fetchone()[0])
        page_size = int(conn.execute("PRAGMA page_size").fetchone()[0])
        journal_mode = str(conn.execute("PRAGMA journal_mode").fetchone()[0]).upper()
        user_version = int(conn.execute("PRAGMA user_version").fetchone()[0])
        application_id = int(conn.execute("PRAGMA application_id").fetchone()[0])
    except sqlite3.DatabaseError as exc:
        report = {
            "schema": SNAPSHOT_VERIFICATION_SCHEMA,
            "status": "fail",
            "guard_mode": guard_mode,
            "database_sha256": _sha256_file(path),
            "database_size_bytes": path.stat().st_size,
            "error_type": type(exc).__name__,
        }
        raise SnapshotVerificationError(
            "SQLite snapshot could not be structurally verified",
            report=report,
        ) from exc
    finally:
        if conn is not None:
            conn.close()

    status_value = (
        "pass"
        if integrity_rows == ["ok"]
        and not foreign_key_rows
        and not missing_tables
        and not missing_migrations
        and migration_registry_valid
        and all(row["status"] == "pass" for row in invariant_results)
        else "fail"
    )
    report: dict[str, object] = {
        "schema": SNAPSHOT_VERIFICATION_SCHEMA,
        "status": status_value,
        "guard_mode": guard_mode,
        "database_sha256": _sha256_file(path),
        "database_size_bytes": path.stat().st_size,
        "integrity_check": integrity_rows,
        "foreign_key_issue_count": len(foreign_key_rows),
        "required_tables": list(tables_required),
        "missing_tables": missing_tables,
        "observed_table_count": len(observed_tables),
        "required_migrations": list(migrations_required),
        "missing_migrations": missing_migrations,
        "observed_migration_count": len(migration_ids),
        "migration_registry_valid": migration_registry_valid,
        "schema_sha256": schema_sha256,
        "page_count": page_count,
        "page_size": page_size,
        "journal_mode": journal_mode,
        "user_version": user_version,
        "application_id": application_id,
        "application_invariants": invariant_results,
    }
    if status_value != "pass":
        raise SnapshotVerificationError("SQLite snapshot verification failed", report=report)
    return report


def _migration_state(
    conn: sqlite3.Connection,
    observed_tables: set[str],
) -> tuple[set[str], bool]:
    migration_ids: set[str] = set()
    registry_valid = True
    if "pfi_operational_migrations" in observed_tables:
        rows = conn.execute(
            "SELECT migration_id, checksum_sha256, applied_at, sqlite_version "
            "FROM pfi_operational_migrations ORDER BY migration_id"
        ).fetchall()
        for row in rows:
            migration_ids.add(str(row["migration_id"]))
            registry_valid = registry_valid and bool(
                _HEX64.fullmatch(str(row["checksum_sha256"]))
                and str(row["applied_at"]).strip()
                and str(row["sqlite_version"]).strip()
            )
    if "pfi_schema_migrations" in observed_tables:
        rows = conn.execute(
            "SELECT migration_id, applied_at FROM pfi_schema_migrations ORDER BY migration_id"
        ).fetchall()
        for row in rows:
            migration_ids.add(str(row["migration_id"]))
            registry_valid = registry_valid and bool(str(row["applied_at"]).strip())
    return migration_ids, registry_valid


def _copy_database_unlocked(
    source: Path,
    target: Path,
    *,
    pages_per_step: int,
    sleep_seconds: float,
) -> dict[str, int]:
    if pages_per_step <= 0:
        raise ValueError("pages_per_step must be positive")
    if sleep_seconds < 0:
        raise ValueError("sleep_seconds must be non-negative")
    _new_file_path(target, label="backup destination")
    progress_step_count = 0
    reported_page_count = 0

    def progress(_status: int, _remaining: int, total: int) -> None:
        nonlocal progress_step_count, reported_page_count
        progress_step_count += 1
        reported_page_count = int(total)

    source_conn: sqlite3.Connection | None = None
    target_conn: sqlite3.Connection | None = None
    try:
        source_conn = sqlite3.connect(
            f"{source.as_uri()}?mode=ro",
            uri=True,
            timeout=30,
            isolation_level=None,
        )
        source_conn.execute("PRAGMA query_only = ON")
        source_conn.execute("PRAGMA busy_timeout = 30000")
        target_conn = sqlite3.connect(target, timeout=30, isolation_level=None)
        target_conn.execute("PRAGMA busy_timeout = 30000")
        source_conn.backup(
            target_conn,
            pages=pages_per_step,
            progress=progress,
            sleep=sleep_seconds,
        )
        target_conn.commit()
    except BaseException:
        if target_conn is not None:
            target_conn.close()
            target_conn = None
        target.unlink(missing_ok=True)
        raise
    finally:
        if target_conn is not None:
            target_conn.close()
        if source_conn is not None:
            source_conn.close()
    os.chmod(target, 0o600)
    _fsync_file(target)
    _fsync_directory(target.parent)
    return {
        "progress_step_count": progress_step_count,
        "reported_page_count": reported_page_count,
    }


def _existing_regular_file(path_value: Path | str, *, label: str) -> Path:
    raw = _absolute_path(path_value)
    if raw.is_symlink():
        raise BackupRestoreError(f"{label} must not be a symbolic link")
    path = raw.resolve(strict=False)
    if not path.exists():
        raise BackupRestoreError(f"{label} does not exist")
    mode = path.stat().st_mode
    if not stat.S_ISREG(mode) or path.stat().st_size <= 0:
        raise BackupRestoreError(f"{label} must be a non-empty regular file")
    return path


def _new_file_path(path_value: Path | str, *, label: str) -> Path:
    raw = _absolute_path(path_value)
    if raw.is_symlink():
        raise BackupRestoreError(f"{label} must not be a symbolic link")
    path = raw.resolve(strict=False)
    if path.exists():
        raise BackupRestoreError(f"{label} already exists; overwrite is forbidden")
    return path


def _directory_path(path_value: Path | str, *, label: str) -> Path:
    raw = _absolute_path(path_value)
    if raw.is_symlink():
        raise BackupRestoreError(f"{label} must not be a symbolic link")
    return raw.resolve(strict=False)


def _absolute_path(path_value: Path | str) -> Path:
    path = Path(path_value).expanduser()
    return path if path.is_absolute() else (Path.cwd() / path)


def _prepare_private_directory(path: Path) -> None:
    if path.is_symlink():
        raise BackupRestoreError("managed backup/restore directory must not be a symbolic link")
    existed = path.exists()
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    if not path.is_dir():
        raise BackupRestoreError("managed backup/restore path must be a directory")
    if existed:
        permissions = stat.S_IMODE(path.stat().st_mode)
        if permissions & 0o077:
            raise BackupRestoreError(
                "existing backup/restore directory must not grant group or other access"
            )
    else:
        os.chmod(path, 0o700)


def _require_distinct_paths(*paths: Path) -> None:
    normalized = [path.resolve(strict=False) for path in paths]
    if len(set(normalized)) != len(normalized):
        raise BackupRestoreError("backup, candidate, rollback and target paths must be distinct")


def _require_same_device(target_parent: Path, *directories: Path) -> None:
    device = os.stat(target_parent).st_dev
    if any(os.stat(directory).st_dev != device for directory in directories):
        raise BackupRestoreError(
            "restore staging and rollback directories must share target filesystem"
        )


def _require_no_sqlite_sidecars(target: Path) -> None:
    present = [
        suffix for suffix in _SIDECAR_SUFFIXES if Path(f"{target}{suffix}").exists()
    ]
    if present:
        raise BackupRestoreError(
            "target has SQLite sidecars and is not quiesced for atomic restore: "
            + ",".join(present)
        )


def _validated_identifiers(values: Iterable[str], label: str) -> list[str]:
    normalized = sorted({str(value).strip() for value in values if str(value).strip()})
    invalid = [value for value in normalized if not _IDENTIFIER.fullmatch(value)]
    if invalid:
        raise ValueError(f"invalid required {label} identifiers: {invalid}")
    return normalized


def _normalize_sha256(value: str) -> str:
    normalized = str(value).strip().lower()
    if normalized.startswith("sha256:"):
        normalized = normalized[7:]
    if not _HEX64.fullmatch(normalized):
        raise ValueError("expected_target_sha256 must be a 64-character SHA-256")
    return normalized


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _fsync_file(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _inject(injector: Callable[[str], None] | None, stage: str) -> None:
    if injector is not None:
        injector(stage)


__all__ = [
    "BackupRestoreError",
    "ONLINE_BACKUP_RECEIPT_SCHEMA",
    "RESTORE_RECEIPT_SCHEMA",
    "RestoreRollbackError",
    "RestoreRolledBackError",
    "SNAPSHOT_VERIFICATION_SCHEMA",
    "SQLiteInvariant",
    "SnapshotVerificationError",
    "create_online_backup",
    "restore_verified_backup",
    "verify_sqlite_snapshot",
]
