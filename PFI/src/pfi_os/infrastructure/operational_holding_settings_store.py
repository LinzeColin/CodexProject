from __future__ import annotations

import os
import sqlite3
import threading
import fcntl
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from pfi_os.application.operational_store import OperationalStore, default_operational_db_path
from pfi_os.infrastructure.operational_store_runtime import (
    execute_sql_statements,
    operational_store_guard,
    operational_transaction,
)


HOLDING_SETTINGS_MIGRATION_ID = "v025_stage7_holding_settings_v1"
MIGRATION_PATH = Path(__file__).resolve().parents[1] / "migrations" / "v025_stage7_holding_settings.sql"
HOLDING_IDEMPOTENCY_MIGRATION_ID = "v025_stage7_holding_idempotency_v2"
IDEMPOTENCY_MIGRATION_PATH = (
    Path(__file__).resolve().parents[1] / "migrations" / "v025_stage7_holding_idempotency.sql"
)
_INITIALIZE_LOCK = threading.Lock()


class HoldingSettingsOperationalStore:
    """SQLite boundary for Phase 7.2 holdings and settings persistence."""

    def __init__(
        self,
        db_path: Path | str | None = None,
        backup_dir: Path | str | None = None,
    ) -> None:
        self.db_path = Path(db_path).expanduser() if db_path is not None else default_operational_db_path()
        data_home = self.db_path.parent.parent.parent
        self.backup_dir = (
            Path(backup_dir).expanduser()
            if backup_dir is not None
            else data_home / "runtime" / "backups"
        )

    def initialize(self) -> Path:
        with _INITIALIZE_LOCK:
            with _exclusive_file_lock(
                self.db_path.with_name(f".{self.db_path.name}.migration.lock")
            ):
                existed_before = self.db_path.is_file() and self.db_path.stat().st_size > 0
                base_applied = self._migration_applied(HOLDING_SETTINGS_MIGRATION_ID) if existed_before else False
                idempotency_applied = (
                    self._migration_applied(HOLDING_IDEMPOTENCY_MIGRATION_ID) if existed_before else False
                )
                if existed_before and (not base_applied or not idempotency_applied):
                    pending_id = (
                        HOLDING_SETTINGS_MIGRATION_ID if not base_applied else HOLDING_IDEMPOTENCY_MIGRATION_ID
                    )
                    self._backup_before_migration(pending_id)

                OperationalStore(self.db_path).initialize()
                if not base_applied:
                    self._apply_migration(HOLDING_SETTINGS_MIGRATION_ID, MIGRATION_PATH)
                if not idempotency_applied:
                    self._apply_migration(HOLDING_IDEMPOTENCY_MIGRATION_ID, IDEMPOTENCY_MIGRATION_PATH)
        return self.db_path

    @contextmanager
    def connect(self, *, immediate: bool = False) -> Iterator[sqlite3.Connection]:
        with operational_transaction(self.db_path, immediate=immediate) as conn:
            yield conn

    def integrity(self) -> dict[str, object]:
        with self.connect() as conn:
            foreign_keys = [tuple(row) for row in conn.execute("PRAGMA foreign_key_check").fetchall()]
            integrity = str(conn.execute("PRAGMA integrity_check").fetchone()[0])
            sqlite_version = str(conn.execute("SELECT sqlite_version()").fetchone()[0])
            migration_count = int(
                conn.execute(
                    "SELECT COUNT(*) FROM pfi_schema_migrations WHERE migration_id = ?",
                    (HOLDING_SETTINGS_MIGRATION_ID,),
                ).fetchone()[0]
            )
            idempotency_migration_count = int(
                conn.execute(
                    "SELECT COUNT(*) FROM pfi_schema_migrations WHERE migration_id = ?",
                    (HOLDING_IDEMPOTENCY_MIGRATION_ID,),
                ).fetchone()[0]
            )
        return {
            "foreign_key_check": "pass" if not foreign_keys else "fail",
            "foreign_key_issue_count": len(foreign_keys),
            "integrity_check": integrity,
            "sqlite_version": sqlite_version,
            "migration_id": HOLDING_SETTINGS_MIGRATION_ID,
            "migration_count": migration_count,
            "idempotency_migration_id": HOLDING_IDEMPOTENCY_MIGRATION_ID,
            "idempotency_migration_count": idempotency_migration_count,
        }

    def _migration_applied(self, migration_id: str) -> bool:
        with operational_store_guard(self.db_path):
            try:
                conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True, timeout=5)
                table = conn.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name='pfi_schema_migrations'"
                ).fetchone()
                if table is None:
                    return False
                row = conn.execute(
                    "SELECT 1 FROM pfi_schema_migrations WHERE migration_id = ?",
                    (migration_id,),
                ).fetchone()
                return row is not None
            except sqlite3.DatabaseError:
                return False
            finally:
                if "conn" in locals():
                    conn.close()

    def _backup_before_migration(self, migration_id: str) -> Path:
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        os.chmod(self.backup_dir, 0o700)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        target = self.backup_dir / f"pre-{migration_id}-{stamp}.sqlite"
        serial = 1
        while target.exists():
            target = self.backup_dir / f"pre-{migration_id}-{stamp}-{serial}.sqlite"
            serial += 1
        with operational_store_guard(self.db_path):
            source = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True, timeout=30)
            destination = sqlite3.connect(target)
            try:
                source.backup(destination)
                destination.commit()
            finally:
                destination.close()
                source.close()
        os.chmod(target, 0o600)
        return target

    def _apply_migration(self, migration_id_value: str, migration_path: Path) -> None:
        migration_sql = migration_path.read_text(encoding="utf-8")
        with operational_transaction(self.db_path, immediate=True) as conn:
            # The database write lock and migration recheck must be in the same
            # transaction.  A process-local lock alone cannot serialize two app
            # processes starting against the same operational database.
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS pfi_schema_migrations (
                    migration_id TEXT PRIMARY KEY,
                    applied_at TEXT NOT NULL
                )
                """
            )
            if conn.execute(
                "SELECT 1 FROM pfi_schema_migrations WHERE migration_id = ?",
                (migration_id_value,),
            ).fetchone() is not None:
                return
            execute_sql_statements(conn, migration_sql)
            conn.execute(
                "INSERT INTO pfi_schema_migrations(migration_id, applied_at) VALUES (?, ?)",
                (migration_id_value, _now()),
            )


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@contextmanager
def _exclusive_file_lock(path: Path) -> Iterator[None]:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        os.chmod(path, 0o600)
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)
