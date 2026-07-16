from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from pfi_os.infrastructure.operational_store_runtime import (
    MigrationChecksumMismatch,
    MigrationLifecycleError,
    apply_operational_migration,
    migration_checksum,
)


def test_versioned_migration_is_checksum_pinned_and_idempotent(tmp_path: Path) -> None:
    db_path = tmp_path / "pfi.sqlite"
    migration_id = "v025_stage11_test_accounts_v1"
    migration_sql = """
    CREATE TABLE stage11_accounts(
        account_id TEXT PRIMARY KEY,
        display_name TEXT NOT NULL
    );
    INSERT INTO stage11_accounts(account_id, display_name)
    VALUES ('contract-sentinel', 'non-financial-test');
    """
    checksum = migration_checksum(migration_sql)

    applied = apply_operational_migration(
        db_path,
        migration_id=migration_id,
        migration_sql=migration_sql,
        expected_checksum=checksum,
    )
    replayed = apply_operational_migration(
        db_path,
        migration_id=migration_id,
        migration_sql=migration_sql,
        expected_checksum=checksum,
    )

    assert applied["status"] == "applied"
    assert applied["lifecycle"] == ["planned", "applying", "applied"]
    assert replayed["status"] == "already_applied"
    assert replayed["lifecycle"] == ["planned", "verified", "already_applied"]
    with sqlite3.connect(db_path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM stage11_accounts").fetchone()[0] == 1
        assert conn.execute(
            "SELECT checksum_sha256 FROM pfi_operational_migrations WHERE migration_id = ?",
            (migration_id,),
        ).fetchone()[0] == checksum


def test_migration_checksum_drift_fails_closed_without_mutation(tmp_path: Path) -> None:
    db_path = tmp_path / "pfi.sqlite"
    migration_id = "v025_stage11_checksum_guard_v1"
    original = "CREATE TABLE checksum_guard(value TEXT NOT NULL);"
    apply_operational_migration(
        db_path,
        migration_id=migration_id,
        migration_sql=original,
        expected_checksum=migration_checksum(original),
    )

    drifted = original.replace("NOT NULL", "")
    with pytest.raises(MigrationChecksumMismatch, match=migration_id):
        apply_operational_migration(
            db_path,
            migration_id=migration_id,
            migration_sql=drifted,
            expected_checksum=migration_checksum(drifted),
        )

    with sqlite3.connect(db_path) as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM pfi_operational_migrations WHERE migration_id = ?",
            (migration_id,),
        ).fetchone()[0] == 1
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def test_failed_migration_rolls_back_schema_data_and_registry_entry(tmp_path: Path) -> None:
    db_path = tmp_path / "pfi.sqlite"
    migration_id = "v025_stage11_forced_failure_v1"
    migration_sql = """
    CREATE TABLE must_not_survive(value TEXT PRIMARY KEY);
    INSERT INTO must_not_survive(value) VALUES ('partial-write');
    INSERT INTO table_that_does_not_exist(value) VALUES ('force-failure');
    """

    with pytest.raises(sqlite3.OperationalError, match="table_that_does_not_exist"):
        apply_operational_migration(
            db_path,
            migration_id=migration_id,
            migration_sql=migration_sql,
            expected_checksum=migration_checksum(migration_sql),
        )

    with sqlite3.connect(db_path) as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='must_not_survive'"
        ).fetchone()[0] == 0
        registry_exists = conn.execute(
            "SELECT COUNT(*) FROM sqlite_master "
            "WHERE type='table' AND name='pfi_operational_migrations'"
        ).fetchone()[0]
        if registry_exists:
            assert conn.execute(
                "SELECT COUNT(*) FROM pfi_operational_migrations WHERE migration_id = ?",
                (migration_id,),
            ).fetchone()[0] == 0
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


@pytest.mark.parametrize(
    "migration_sql",
    (
        "-- disguised transaction control\nBEGIN;",
        "/* disguised journal drift */ PRAGMA journal_mode=WAL;",
        "SAVEPOINT bypass;",
        "ATTACH DATABASE '/tmp/out-of-scope.sqlite' AS escaped;",
    ),
)
def test_migration_cannot_escape_owned_transaction_or_database(
    tmp_path: Path, migration_sql: str
) -> None:
    db_path = tmp_path / "pfi.sqlite"
    with pytest.raises(MigrationLifecycleError, match="transaction boundary"):
        apply_operational_migration(
            db_path,
            migration_id="v025_stage11_escape_attempt_v1",
            migration_sql=migration_sql,
            expected_checksum=migration_checksum(migration_sql),
        )
