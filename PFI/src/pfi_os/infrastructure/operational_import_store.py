from __future__ import annotations

import os
import sqlite3
import threading
import fcntl
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator
from uuid import uuid4

from pfi_os.application.operational_store import OperationalStore, default_operational_db_path
from pfi_os.infrastructure.operational_store_runtime import (
    execute_sql_statements,
    operational_store_guard,
    operational_transaction,
)


MIGRATION_ID = "v025_stage7_import_review_ledger_v1"
MIGRATION_PATH = Path(__file__).resolve().parents[1] / "migrations" / "v025_stage7_import_review_ledger.sql"
_INITIALIZE_LOCK = threading.Lock()


class ImportOperationalStore:
    """Additive import/review/ledger persistence on the canonical operational DB."""

    def __init__(
        self,
        db_path: Path | str | None = None,
        raw_store_dir: Path | str | None = None,
    ) -> None:
        self.db_path = Path(db_path).expanduser() if db_path is not None else default_operational_db_path()
        self.raw_store_dir = (
            Path(raw_store_dir).expanduser()
            if raw_store_dir is not None
            else self.db_path.parent.parent / "imports" / "raw"
        )

    def initialize(self) -> Path:
        with _INITIALIZE_LOCK:
            with _exclusive_file_lock(self._migration_lock_path()):
                existed_before = self.db_path.is_file() and self.db_path.stat().st_size > 0
                migration_applied = self._migration_applied() if existed_before else False
                if existed_before and not migration_applied:
                    self._backup_before_migration()
                OperationalStore(self.db_path).initialize()
                if not migration_applied:
                    self._apply_migration()
        self.raw_store_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(self.raw_store_dir, 0o700)
        return self.db_path

    @contextmanager
    def preview_lock(self) -> Iterator[None]:
        """Serialize raw-write, DB-reference, and cleanup as one process-safe unit."""

        with _exclusive_file_lock(self.db_path.with_name(f".{self.db_path.name}.import-preview.lock")):
            yield

    def _migration_lock_path(self) -> Path:
        return self.db_path.with_name(f".{self.db_path.name}.migration.lock")

    @contextmanager
    def connect(self, *, immediate: bool = False) -> Iterator[sqlite3.Connection]:
        with operational_transaction(self.db_path, immediate=immediate) as conn:
            yield conn

    def write_raw(self, content_sha256: str, content: bytes) -> str:
        digest = _sha256(content)
        if digest != content_sha256:
            raise ValueError("raw import hash does not match content")
        self.raw_store_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(self.raw_store_dir, 0o700)
        target = self.raw_store_dir / f"{content_sha256}.bin"
        if target.exists():
            if _sha256(target.read_bytes()) != content_sha256:
                raise ValueError("existing raw import content failed hash verification")
            return f"private://imports/raw/{content_sha256}"
        temporary = self.raw_store_dir / f".{content_sha256}.{uuid4().hex}.tmp"
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            with os.fdopen(descriptor, "wb", closefd=True) as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            if _sha256(temporary.read_bytes()) != content_sha256:
                raise ValueError("raw import temporary content failed hash verification")
            if target.exists():
                temporary.unlink(missing_ok=True)
            else:
                temporary.replace(target)
                os.chmod(target, 0o600)
                directory_fd = os.open(self.raw_store_dir, os.O_RDONLY)
                try:
                    os.fsync(directory_fd)
                finally:
                    os.close(directory_fd)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise
        return f"private://imports/raw/{content_sha256}"

    def read_raw(self, content_sha256: str) -> bytes:
        path = self.raw_store_dir / f"{content_sha256}.bin"
        if not path.is_file():
            raise FileNotFoundError(f"raw import content is unavailable for hash {content_sha256}")
        content = path.read_bytes()
        if _sha256(content) != content_sha256:
            raise ValueError("raw import content failed hash verification")
        return content

    def discard_raw_if_unreferenced(self, content_sha256: str) -> None:
        referenced = False
        try:
            with self.connect() as conn:
                referenced = conn.execute(
                    "SELECT 1 FROM import_files WHERE content_sha256 = ? LIMIT 1",
                    (content_sha256,),
                ).fetchone() is not None
        except sqlite3.DatabaseError:
            return
        if not referenced:
            (self.raw_store_dir / f"{content_sha256}.bin").unlink(missing_ok=True)

    def integrity(self) -> dict[str, object]:
        with self.connect() as conn:
            foreign_keys = [tuple(row) for row in conn.execute("PRAGMA foreign_key_check").fetchall()]
            integrity = str(conn.execute("PRAGMA integrity_check").fetchone()[0])
        return {
            "foreign_key_check": "pass" if not foreign_keys else "fail",
            "foreign_key_issue_count": len(foreign_keys),
            "integrity_check": integrity,
        }

    def _migration_applied(self) -> bool:
        with operational_store_guard(self.db_path):
            try:
                conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True, timeout=5)
                table = conn.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name='pfi_schema_migrations'"
                ).fetchone()
                if table is None:
                    return False
                return conn.execute(
                    "SELECT 1 FROM pfi_schema_migrations WHERE migration_id = ?", (MIGRATION_ID,)
                ).fetchone() is not None
            except sqlite3.DatabaseError:
                return False
            finally:
                if "conn" in locals():
                    conn.close()

    def _backup_before_migration(self) -> Path:
        backup_dir = self.db_path.parent.parent.parent / "runtime" / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(backup_dir, 0o700)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        target = backup_dir / f"pre-{MIGRATION_ID}-{stamp}.sqlite"
        serial = 1
        while target.exists():
            target = backup_dir / f"pre-{MIGRATION_ID}-{stamp}-{serial}.sqlite"
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

    def _apply_migration(self) -> None:
        migration_sql = MIGRATION_PATH.read_text(encoding="utf-8")
        with operational_transaction(self.db_path, immediate=True) as conn:
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
                (MIGRATION_ID,),
            ).fetchone() is not None:
                return
            execute_sql_statements(conn, migration_sql)
            conn.execute(
                "INSERT INTO pfi_schema_migrations(migration_id, applied_at) VALUES (?, ?)",
                (MIGRATION_ID, _now()),
            )


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _sha256(content: bytes) -> str:
    import hashlib

    return hashlib.sha256(content).hexdigest()


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
