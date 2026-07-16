from __future__ import annotations

import fcntl
import hashlib
import os
import re
import sqlite3
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator


SQLITE_WAL_RISK_ID = "sqlite-wal-reset-2026-03"
SQLITE_WAL_FIX_URL = "https://sqlite.org/wal.html"
SQLITE_WAL_RELEASE_URL = "https://sqlite.org/releaselog/3_51_3.html"
OPERATIONAL_MIGRATION_REGISTRY_ID = "v025_stage11_operational_migration_registry_v1"
_VERSION_PATTERN = re.compile(r"^(\d+)\.(\d+)\.(\d+)")
_MIGRATION_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")

OPERATIONAL_MIGRATION_REGISTRY_SQL = """
CREATE TABLE IF NOT EXISTS pfi_operational_migrations (
    migration_id TEXT PRIMARY KEY,
    checksum_sha256 TEXT NOT NULL CHECK (length(checksum_sha256) = 64),
    applied_at TEXT NOT NULL,
    sqlite_version TEXT NOT NULL
)
"""


class UnsafeSQLiteRuntimeError(RuntimeError):
    """Raised when WAL is requested on a runtime without the required fix."""


class MigrationLifecycleError(RuntimeError):
    """Raised when a versioned migration violates the lifecycle contract."""


class MigrationChecksumMismatch(MigrationLifecycleError):
    """Raised when migration source no longer matches its pinned checksum."""


@dataclass(frozen=True)
class SQLiteRuntimeAssessment:
    version: str
    source_id: str
    threadsafety: int
    wal_safe: bool
    journal_default: str
    risk_id: str
    decision: str
    fix_versions: tuple[str, ...]
    official_sources: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def evaluate_sqlite_runtime(
    *,
    version: str | None = None,
    source_id: str | None = None,
) -> SQLiteRuntimeAssessment:
    runtime_version = str(version or sqlite3.sqlite_version)
    parsed = _parse_version(runtime_version)
    wal_safe = (
        parsed >= (3, 51, 3)
        or (parsed[:2] == (3, 50) and parsed[2] >= 7)
        or (parsed[:2] == (3, 44) and parsed[2] >= 6)
    )
    runtime_source_id = str(source_id or _sqlite_source_id())
    decision = (
        "wal_allowed_on_officially_fixed_runtime"
        if wal_safe
        else "wal_rejected_use_delete_rollback_journal"
    )
    return SQLiteRuntimeAssessment(
        version=runtime_version,
        source_id=runtime_source_id,
        threadsafety=int(sqlite3.threadsafety),
        wal_safe=wal_safe,
        journal_default="DELETE",
        risk_id=SQLITE_WAL_RISK_ID,
        decision=decision,
        fix_versions=("3.44.6", "3.50.7", "3.51.3"),
        official_sources=(SQLITE_WAL_FIX_URL, SQLITE_WAL_RELEASE_URL),
    )


def select_journal_mode(
    assessment: SQLiteRuntimeAssessment,
    *,
    request_wal: bool = False,
) -> str:
    if not request_wal:
        return "DELETE"
    if not assessment.wal_safe:
        raise UnsafeSQLiteRuntimeError(
            "WAL requested but SQLite "
            f"{assessment.version} is not in the approved fixed-version set; "
            "use DELETE rollback journal or upgrade to 3.44.6, 3.50.7, 3.51.3, or later."
        )
    return "WAL"


def configure_sqlite_connection(
    conn: sqlite3.Connection,
    *,
    assessment: SQLiteRuntimeAssessment | None = None,
    request_wal: bool = False,
) -> dict[str, object]:
    runtime = assessment or evaluate_sqlite_runtime()
    selected_mode = select_journal_mode(runtime, request_wal=request_wal)

    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 30000")
    current_mode = str(conn.execute("PRAGMA journal_mode").fetchone()[0]).upper()
    if current_mode != selected_mode:
        actual_mode = str(
            conn.execute(f"PRAGMA journal_mode = {selected_mode}").fetchone()[0]
        ).upper()
        if actual_mode != selected_mode:
            raise UnsafeSQLiteRuntimeError(
                f"failed to enforce journal_mode={selected_mode}; SQLite returned {actual_mode}"
            )
    conn.execute("PRAGMA synchronous = FULL")

    settings = audit_sqlite_connection(conn)
    if settings["journal_mode"] != selected_mode:
        raise UnsafeSQLiteRuntimeError(
            f"journal policy drift: expected {selected_mode}, got {settings['journal_mode']}"
        )
    if not settings["foreign_keys"]:
        raise MigrationLifecycleError("PRAGMA foreign_keys failed to enable")
    if settings["busy_timeout_ms"] != 30000:
        raise MigrationLifecycleError("PRAGMA busy_timeout failed to enforce 30000ms")
    if settings["synchronous"] != "FULL":
        raise MigrationLifecycleError("PRAGMA synchronous failed to enforce FULL")
    return settings


def audit_sqlite_connection(conn: sqlite3.Connection) -> dict[str, object]:
    synchronous_code = int(conn.execute("PRAGMA synchronous").fetchone()[0])
    synchronous_names = {0: "OFF", 1: "NORMAL", 2: "FULL", 3: "EXTRA"}
    journal_mode = str(conn.execute("PRAGMA journal_mode").fetchone()[0]).upper()
    return {
        "journal_mode": journal_mode,
        "wal_enabled": journal_mode == "WAL",
        "synchronous": synchronous_names.get(synchronous_code, f"UNKNOWN_{synchronous_code}"),
        "synchronous_code": synchronous_code,
        "foreign_keys": bool(conn.execute("PRAGMA foreign_keys").fetchone()[0]),
        "busy_timeout_ms": int(conn.execute("PRAGMA busy_timeout").fetchone()[0]),
    }


def operational_store_lock_path(db_path: Path | str) -> Path:
    path = Path(db_path).expanduser().resolve(strict=False)
    return path.with_name(f".{path.name}.pfi-operation.lock")


@contextmanager
def operational_store_guard(
    db_path: Path | str,
    *,
    exclusive: bool = False,
) -> Iterator[Path]:
    """Coordinate ordinary transactions with maintenance/restore operations."""

    path = Path(db_path).expanduser().resolve(strict=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = operational_store_lock_path(path)
    flags = os.O_RDWR | os.O_CREAT
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(lock_path, flags, 0o600)
    try:
        os.chmod(lock_path, 0o600)
        fcntl.flock(descriptor, fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH)
        yield lock_path
    finally:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


@contextmanager
def operational_transaction(
    db_path: Path | str,
    *,
    immediate: bool = False,
    request_wal: bool = False,
) -> Iterator[sqlite3.Connection]:
    path = Path(db_path).expanduser().resolve(strict=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    with operational_store_guard(path):
        conn = sqlite3.connect(path, timeout=30, isolation_level=None)
        conn.row_factory = sqlite3.Row
        try:
            configure_sqlite_connection(conn, request_wal=request_wal)
            conn.execute("BEGIN IMMEDIATE" if immediate else "BEGIN")
            try:
                yield conn
            except BaseException:
                conn.rollback()
                raise
            else:
                try:
                    conn.commit()
                except BaseException:
                    conn.rollback()
                    raise
        finally:
            conn.close()


def migration_checksum(migration_sql: str) -> str:
    normalized = str(migration_sql).replace("\r\n", "\n").strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def execute_sql_statements(conn: sqlite3.Connection, script: str) -> int:
    statements = tuple(_split_sql_statements(script))
    for statement in statements:
        first_token = _leading_sql_keyword(statement)
        if first_token in {
            "ATTACH",
            "BEGIN",
            "COMMIT",
            "DETACH",
            "END",
            "PRAGMA",
            "RELEASE",
            "ROLLBACK",
            "SAVEPOINT",
            "VACUUM",
        }:
            raise MigrationLifecycleError(
                f"migration statement controls the transaction boundary: {first_token}"
            )
        conn.execute(statement)
    return len(statements)


def ensure_operational_migration_registry(conn: sqlite3.Connection) -> dict[str, str]:
    checksum = migration_checksum(OPERATIONAL_MIGRATION_REGISTRY_SQL)
    conn.execute(OPERATIONAL_MIGRATION_REGISTRY_SQL)
    existing = conn.execute(
        "SELECT checksum_sha256, applied_at, sqlite_version "
        "FROM pfi_operational_migrations WHERE migration_id = ?",
        (OPERATIONAL_MIGRATION_REGISTRY_ID,),
    ).fetchone()
    if existing is not None:
        if str(existing["checksum_sha256"]) != checksum:
            raise MigrationChecksumMismatch(
                f"migration checksum mismatch for {OPERATIONAL_MIGRATION_REGISTRY_ID}"
            )
        return {
            "migration_id": OPERATIONAL_MIGRATION_REGISTRY_ID,
            "checksum_sha256": checksum,
            "applied_at": str(existing["applied_at"]),
            "sqlite_version": str(existing["sqlite_version"]),
            "status": "already_applied",
        }

    applied_at = _now()
    conn.execute(
        "INSERT INTO pfi_operational_migrations("
        "migration_id, checksum_sha256, applied_at, sqlite_version"
        ") VALUES (?, ?, ?, ?)",
        (OPERATIONAL_MIGRATION_REGISTRY_ID, checksum, applied_at, sqlite3.sqlite_version),
    )
    return {
        "migration_id": OPERATIONAL_MIGRATION_REGISTRY_ID,
        "checksum_sha256": checksum,
        "applied_at": applied_at,
        "sqlite_version": sqlite3.sqlite_version,
        "status": "applied",
    }


def apply_operational_migration(
    db_path: Path | str,
    *,
    migration_id: str,
    migration_sql: str,
    expected_checksum: str,
) -> dict[str, object]:
    if not _MIGRATION_ID_PATTERN.fullmatch(str(migration_id)):
        raise MigrationLifecycleError(f"invalid migration_id: {migration_id!r}")
    actual_checksum = migration_checksum(migration_sql)
    if actual_checksum != str(expected_checksum):
        raise MigrationChecksumMismatch(
            f"migration checksum mismatch for {migration_id}: source does not match expected checksum"
        )

    with operational_transaction(db_path, immediate=True) as conn:
        ensure_operational_migration_registry(conn)
        existing = conn.execute(
            "SELECT checksum_sha256, applied_at, sqlite_version "
            "FROM pfi_operational_migrations WHERE migration_id = ?",
            (migration_id,),
        ).fetchone()
        if existing is not None:
            if str(existing["checksum_sha256"]) != actual_checksum:
                raise MigrationChecksumMismatch(f"migration checksum mismatch for {migration_id}")
            return {
                "migration_id": migration_id,
                "checksum_sha256": actual_checksum,
                "applied_at": str(existing["applied_at"]),
                "sqlite_version": str(existing["sqlite_version"]),
                "status": "already_applied",
                "lifecycle": ["planned", "verified", "already_applied"],
            }

        execute_sql_statements(conn, migration_sql)
        applied_at = _now()
        conn.execute(
            "INSERT INTO pfi_operational_migrations("
            "migration_id, checksum_sha256, applied_at, sqlite_version"
            ") VALUES (?, ?, ?, ?)",
            (migration_id, actual_checksum, applied_at, sqlite3.sqlite_version),
        )
        return {
            "migration_id": migration_id,
            "checksum_sha256": actual_checksum,
            "applied_at": applied_at,
            "sqlite_version": sqlite3.sqlite_version,
            "status": "applied",
            "lifecycle": ["planned", "applying", "applied"],
        }


def _split_sql_statements(script: str) -> Iterator[str]:
    buffer = ""
    for character in str(script):
        buffer += character
        if character == ";" and sqlite3.complete_statement(buffer):
            statement = buffer.strip()
            buffer = ""
            if statement:
                yield statement
    if buffer.strip():
        if not sqlite3.complete_statement(buffer + ";"):
            raise MigrationLifecycleError("incomplete SQL migration statement")
        yield buffer.strip()


def _parse_version(version: str) -> tuple[int, int, int]:
    match = _VERSION_PATTERN.match(str(version).strip())
    if match is None:
        raise ValueError(f"unsupported SQLite version format: {version!r}")
    return tuple(int(part) for part in match.groups())  # type: ignore[return-value]


def _leading_sql_keyword(statement: str) -> str:
    remaining = statement.lstrip()
    while remaining:
        if remaining.startswith("--"):
            newline = remaining.find("\n")
            remaining = "" if newline < 0 else remaining[newline + 1 :].lstrip()
            continue
        if remaining.startswith("/*"):
            closing = remaining.find("*/", 2)
            if closing < 0:
                raise MigrationLifecycleError("unterminated SQL block comment")
            remaining = remaining[closing + 2 :].lstrip()
            continue
        break
    match = re.match(r"[A-Za-z]+", remaining)
    return match.group(0).upper() if match is not None else ""


def _sqlite_source_id() -> str:
    with sqlite3.connect(":memory:") as conn:
        return str(conn.execute("SELECT sqlite_source_id()").fetchone()[0])


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
