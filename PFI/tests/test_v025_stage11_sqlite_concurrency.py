from __future__ import annotations

import multiprocessing
import sqlite3
import time
from pathlib import Path

import pytest

from pfi_os.application.operational_store import OperationalStore
from pfi_os.infrastructure.operational_store_runtime import (
    UnsafeSQLiteRuntimeError,
    audit_sqlite_connection,
    evaluate_sqlite_runtime,
    operational_transaction,
    select_journal_mode,
)


def _concurrent_writer(db_path: str, worker_id: int, row_count: int, start: object) -> None:
    start.wait(timeout=10)
    for row_index in range(row_count):
        with operational_transaction(Path(db_path), immediate=True) as conn:
            conn.execute(
                "INSERT INTO stage11_concurrency(worker_id, row_index) VALUES (?, ?)",
                (worker_id, row_index),
            )


def _uncommitted_writer(db_path: str, ready: object) -> None:
    with operational_transaction(Path(db_path), immediate=True) as conn:
        conn.execute("INSERT INTO stage11_kill_probe(marker) VALUES ('must_rollback')")
        ready.set()
        time.sleep(60)


@pytest.mark.parametrize(
    ("version", "wal_safe"),
    (
        ("3.44.5", False),
        ("3.44.6", True),
        ("3.49.2", False),
        ("3.50.4", False),
        ("3.50.7", True),
        ("3.51.2", False),
        ("3.51.3", True),
        ("3.53.3", True),
    ),
)
def test_sqlite_wal_runtime_gate_matches_official_fixed_versions(
    version: str, wal_safe: bool
) -> None:
    assessment = evaluate_sqlite_runtime(version=version, source_id="test-source-id")

    assert assessment.version == version
    assert assessment.wal_safe is wal_safe
    assert assessment.source_id == "test-source-id"
    if wal_safe:
        assert select_journal_mode(assessment, request_wal=True) == "WAL"
    else:
        with pytest.raises(UnsafeSQLiteRuntimeError, match="WAL"):
            select_journal_mode(assessment, request_wal=True)


def test_active_operational_store_is_transactional_and_auditable(tmp_path: Path) -> None:
    db_path = tmp_path / "private" / "operational" / "pfi.sqlite"
    store = OperationalStore(db_path)
    store.initialize()

    with store.connect(immediate=True) as conn:
        conn.execute("CREATE TABLE stage11_rollback_probe(marker TEXT PRIMARY KEY)")
        settings = audit_sqlite_connection(conn)

    assert settings == {
        "journal_mode": "DELETE",
        "wal_enabled": False,
        "synchronous": "FULL",
        "synchronous_code": 2,
        "foreign_keys": True,
        "busy_timeout_ms": 30000,
    }

    with pytest.raises(RuntimeError, match="forced rollback"):
        with store.connect(immediate=True) as conn:
            conn.execute("INSERT INTO stage11_rollback_probe VALUES ('must_rollback')")
            raise RuntimeError("forced rollback")

    with store.connect() as conn:
        assert conn.execute("SELECT COUNT(*) FROM stage11_rollback_probe").fetchone()[0] == 0
        registry = conn.execute(
            "SELECT migration_id, checksum_sha256 FROM pfi_operational_migrations"
        ).fetchall()
    assert len(registry) == 1
    assert registry[0]["migration_id"] == "v025_stage11_operational_migration_registry_v1"
    assert len(registry[0]["checksum_sha256"]) == 64


def test_concurrent_writes_and_process_kill_recover_without_partial_commit(tmp_path: Path) -> None:
    db_path = tmp_path / "private" / "operational" / "pfi.sqlite"
    store = OperationalStore(db_path)
    store.initialize()
    with store.connect(immediate=True) as conn:
        conn.execute(
            """
            CREATE TABLE stage11_concurrency(
                worker_id INTEGER NOT NULL,
                row_index INTEGER NOT NULL,
                PRIMARY KEY(worker_id, row_index)
            )
            """
        )
        conn.execute("CREATE TABLE stage11_kill_probe(marker TEXT PRIMARY KEY)")

    context = multiprocessing.get_context("spawn")
    start = context.Event()
    workers = [
        context.Process(target=_concurrent_writer, args=(str(db_path), worker_id, 20, start))
        for worker_id in range(4)
    ]
    for worker in workers:
        worker.start()
    start.set()
    for worker in workers:
        worker.join(timeout=30)
        assert worker.exitcode == 0

    ready = context.Event()
    victim = context.Process(target=_uncommitted_writer, args=(str(db_path), ready))
    victim.start()
    assert ready.wait(timeout=10)
    victim.kill()
    victim.join(timeout=10)
    assert victim.exitcode is not None and victim.exitcode != 0

    with store.connect() as conn:
        assert conn.execute("SELECT COUNT(*) FROM stage11_concurrency").fetchone()[0] == 80
        assert conn.execute("SELECT COUNT(*) FROM stage11_kill_probe").fetchone()[0] == 0
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []


def test_current_runtime_never_silently_uses_unsafe_wal() -> None:
    assessment = evaluate_sqlite_runtime()

    assert assessment.version == sqlite3.sqlite_version
    if assessment.wal_safe:
        assert select_journal_mode(assessment, request_wal=True) == "WAL"
    else:
        assert select_journal_mode(assessment, request_wal=False) == "DELETE"
        with pytest.raises(UnsafeSQLiteRuntimeError, match=assessment.version):
            select_journal_mode(assessment, request_wal=True)
