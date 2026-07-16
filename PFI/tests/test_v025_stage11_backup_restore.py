from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

from pfi_os.application.operational_store import OFFICIAL_TABLES, OperationalStore
from pfi_os.infrastructure.operational_store_backup import (
    BackupRestoreError,
    RestoreRolledBackError,
    SQLiteInvariant,
    SnapshotVerificationError,
    create_online_backup,
    restore_verified_backup,
    verify_sqlite_snapshot,
)
from pfi_os.infrastructure.jobs.sqlite_store import SQLiteDurableJobStore
from pfi_os.infrastructure.operational_store_runtime import (
    OPERATIONAL_MIGRATION_REGISTRY_ID,
    operational_store_guard,
    operational_transaction,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
CLI = REPO_ROOT / "PFI" / "scripts" / "v025" / "pfi_operational_backup_restore.py"
REAL_REHEARSAL_CLI = (
    REPO_ROOT / "PFI" / "scripts" / "v025" / "stage11_readonly_backup_rehearsal.py"
)
REQUIRED_TABLES = tuple(sorted({*OFFICIAL_TABLES, "stage11_restore_state"}))
REQUIRED_MIGRATIONS = (OPERATIONAL_MIGRATION_REGISTRY_ID,)


def _state_invariant(expected: str) -> SQLiteInvariant:
    return SQLiteInvariant(
        "restore_state_matches_expected",
        "SELECT state FROM stage11_restore_state WHERE singleton=1",
        expected,
    )


def _build_database(path: Path, state: str) -> Path:
    store = OperationalStore(path)
    store.initialize()
    with store.connect(immediate=True) as conn:
        conn.execute(
            "CREATE TABLE stage11_restore_state("
            "singleton INTEGER PRIMARY KEY CHECK(singleton=1), state TEXT NOT NULL)"
        )
        conn.execute(
            "INSERT INTO stage11_restore_state(singleton,state) VALUES (1,?)",
            (state,),
        )
        conn.execute(
            "CREATE TABLE stage11_writer_events("
            "event_id INTEGER PRIMARY KEY, marker TEXT NOT NULL)"
        )
    return path


def _read_state(path: Path) -> str:
    with sqlite3.connect(path) as conn:
        return str(
            conn.execute(
                "SELECT state FROM stage11_restore_state WHERE singleton=1"
            ).fetchone()[0]
        )


def _inspect(path: Path, state: str) -> dict[str, object]:
    return verify_sqlite_snapshot(
        path,
        required_tables=REQUIRED_TABLES,
        required_migrations=REQUIRED_MIGRATIONS,
        invariants=(_state_invariant(state),),
        exclusive=True,
    )


def test_online_backup_is_consistent_during_concurrent_commits(tmp_path: Path) -> None:
    source = _build_database(tmp_path / "source" / "pfi.sqlite", "online")
    backup = tmp_path / "backups" / "online.sqlite"
    with operational_transaction(source, immediate=True) as conn:
        conn.execute("CREATE TABLE stage11_parent(item_id INTEGER PRIMARY KEY)")
        conn.execute(
            "CREATE TABLE stage11_child("
            "item_id INTEGER PRIMARY KEY REFERENCES stage11_parent(item_id))"
        )
        conn.execute("CREATE TABLE stage11_padding(item_id INTEGER PRIMARY KEY, payload BLOB)")
        conn.executemany(
            "INSERT INTO stage11_padding(item_id,payload) VALUES (?,zeroblob(2048))",
            ((index,) for index in range(1500)),
        )

    started = threading.Event()

    def writer() -> None:
        for index in range(1, 81):
            with operational_transaction(source, immediate=True) as conn:
                conn.execute("INSERT INTO stage11_parent(item_id) VALUES (?)", (index,))
                conn.execute("INSERT INTO stage11_child(item_id) VALUES (?)", (index,))
            started.set()
            time.sleep(0.001)

    thread = threading.Thread(target=writer, daemon=True)
    thread.start()
    assert started.wait(timeout=5)
    receipt = create_online_backup(
        source,
        backup,
        required_tables=(*REQUIRED_TABLES, "stage11_parent", "stage11_child"),
        required_migrations=REQUIRED_MIGRATIONS,
        invariants=(
            _state_invariant("online"),
            SQLiteInvariant(
                "parent_child_transaction_pairing",
                "SELECT (SELECT COUNT(*) FROM stage11_parent) - "
                "(SELECT COUNT(*) FROM stage11_child)",
                0,
            ),
        ),
        pages_per_step=1,
        sleep_seconds=0.001,
    )
    thread.join(timeout=10)
    assert not thread.is_alive()

    with sqlite3.connect(backup) as snapshot, sqlite3.connect(source) as current:
        snapshot_count = int(snapshot.execute("SELECT COUNT(*) FROM stage11_parent").fetchone()[0])
        current_count = int(current.execute("SELECT COUNT(*) FROM stage11_parent").fetchone()[0])
        assert snapshot_count == int(
            snapshot.execute("SELECT COUNT(*) FROM stage11_child").fetchone()[0]
        )
        assert 1 <= snapshot_count <= current_count == 80
    assert receipt["status"] == "pass"
    assert receipt["method"] == "sqlite_online_backup_api"
    assert receipt["online_file_copy_used"] is False
    assert receipt["source_open_mode"] == "sqlite_uri_mode_ro_query_only"
    assert receipt["source_directory_mutated"] is False
    assert receipt["source_guard"] == "sqlite_online_backup_consistent_snapshot"
    assert receipt["verification"]["integrity_check"] == ["ok"]
    assert receipt["verification"]["foreign_key_issue_count"] == 0


def test_online_backup_does_not_create_or_change_any_source_directory_entry(
    tmp_path: Path,
) -> None:
    source = _build_database(tmp_path / "source" / "pfi.sqlite", "read-only-source")
    backup = tmp_path / "backups" / "snapshot.sqlite"
    source_directory = source.parent
    source_lock = source_directory / f".{source.name}.pfi-operation.lock"
    source_lock.unlink(missing_ok=True)
    source_stat_before = source.stat()
    entries_before = {
        path.name: (path.stat().st_ino, path.stat().st_size, path.stat().st_mtime_ns)
        for path in source_directory.iterdir()
    }

    receipt = create_online_backup(
        source,
        backup,
        required_tables=REQUIRED_TABLES,
        required_migrations=REQUIRED_MIGRATIONS,
        invariants=(_state_invariant("read-only-source"),),
    )

    source_stat_after = source.stat()
    entries_after = {
        path.name: (path.stat().st_ino, path.stat().st_size, path.stat().st_mtime_ns)
        for path in source_directory.iterdir()
    }
    assert entries_after == entries_before
    assert source_stat_after.st_ino == source_stat_before.st_ino
    assert source_stat_after.st_size == source_stat_before.st_size
    assert source_stat_after.st_mtime_ns == source_stat_before.st_mtime_ns
    assert not source_lock.exists()
    assert receipt["source_directory_mutated"] is False


def test_restore_verifies_candidate_then_atomically_replaces_target(tmp_path: Path) -> None:
    desired = _build_database(tmp_path / "desired" / "pfi.sqlite", "new")
    target = _build_database(tmp_path / "target" / "pfi.sqlite", "old")
    backup = tmp_path / "backups" / "desired.sqlite"
    create_online_backup(
        desired,
        backup,
        required_tables=REQUIRED_TABLES,
        required_migrations=REQUIRED_MIGRATIONS,
        invariants=(_state_invariant("new"),),
    )
    target_before = _inspect(target, "old")

    receipt = restore_verified_backup(
        backup,
        target,
        staging_directory=tmp_path / "restore_staging",
        rollback_directory=tmp_path / "rollback",
        expected_target_sha256=str(target_before["database_sha256"]),
        candidate_required_tables=REQUIRED_TABLES,
        candidate_required_migrations=REQUIRED_MIGRATIONS,
        candidate_invariants=(_state_invariant("new"),),
        target_required_tables=REQUIRED_TABLES,
        target_required_migrations=REQUIRED_MIGRATIONS,
        target_invariants=(_state_invariant("old"),),
    )

    assert receipt["status"] == "restored"
    assert receipt["candidate_verified_before_replace"] is True
    assert receipt["rollback_snapshot_verified_before_replace"] is True
    assert receipt["same_filesystem_atomic_replace"] is True
    assert receipt["exclusive_operational_lock"] is True
    assert receipt["automatic_rollback_performed"] is False
    assert _read_state(target) == "new"
    rollback = (
        tmp_path
        / "rollback"
        / f"pre-restore-{target.stem}-{receipt['restore_id']}.sqlite"
    )
    assert rollback.is_file()
    assert _read_state(rollback) == "old"
    assert not list((tmp_path / "restore_staging").glob("*.candidate.sqlite"))


def test_failed_candidate_invariant_never_touches_target(tmp_path: Path) -> None:
    rejected = _build_database(tmp_path / "rejected" / "pfi.sqlite", "bad")
    target = _build_database(tmp_path / "target" / "pfi.sqlite", "old")
    backup = tmp_path / "backups" / "rejected.sqlite"
    create_online_backup(
        rejected,
        backup,
        required_tables=REQUIRED_TABLES,
        required_migrations=REQUIRED_MIGRATIONS,
        invariants=(_state_invariant("bad"),),
    )
    target_before = _inspect(target, "old")

    with pytest.raises(SnapshotVerificationError):
        restore_verified_backup(
            backup,
            target,
            staging_directory=tmp_path / "restore_staging",
            rollback_directory=tmp_path / "rollback",
            expected_target_sha256=str(target_before["database_sha256"]),
            candidate_required_tables=REQUIRED_TABLES,
            candidate_required_migrations=REQUIRED_MIGRATIONS,
            candidate_invariants=(_state_invariant("new"),),
            target_invariants=(_state_invariant("old"),),
        )

    assert _inspect(target, "old")["database_sha256"] == target_before["database_sha256"]
    assert not list((tmp_path / "restore_staging").glob("*.sqlite"))


def test_post_replace_failure_automatically_rolls_back_original(tmp_path: Path) -> None:
    desired = _build_database(tmp_path / "desired" / "pfi.sqlite", "new")
    target = _build_database(tmp_path / "target" / "pfi.sqlite", "old")
    backup = tmp_path / "backups" / "desired.sqlite"
    create_online_backup(
        desired,
        backup,
        required_tables=REQUIRED_TABLES,
        required_migrations=REQUIRED_MIGRATIONS,
        invariants=(_state_invariant("new"),),
    )
    target_before = _inspect(target, "old")

    def inject(stage: str) -> None:
        if stage == "after_atomic_replace":
            raise RuntimeError("forced post-replace failure")

    with pytest.raises(RestoreRolledBackError) as captured:
        restore_verified_backup(
            backup,
            target,
            staging_directory=tmp_path / "restore_staging",
            rollback_directory=tmp_path / "rollback",
            expected_target_sha256=str(target_before["database_sha256"]),
            candidate_required_tables=REQUIRED_TABLES,
            candidate_required_migrations=REQUIRED_MIGRATIONS,
            candidate_invariants=(_state_invariant("new"),),
            target_required_tables=REQUIRED_TABLES,
            target_required_migrations=REQUIRED_MIGRATIONS,
            target_invariants=(_state_invariant("old"),),
            failure_injector=inject,
        )

    receipt = captured.value.receipt
    assert receipt["status"] == "rolled_back"
    assert receipt["automatic_rollback_performed"] is True
    assert receipt["rollback_verification"]["status"] == "pass"
    assert _read_state(target) == "old"
    assert _inspect(target, "old")["database_sha256"] == receipt["rollback_verification"][
        "database_sha256"
    ]


def test_exclusive_restore_lock_waits_then_rejects_stale_target_hash(tmp_path: Path) -> None:
    desired = _build_database(tmp_path / "desired" / "pfi.sqlite", "new")
    target = _build_database(tmp_path / "target" / "pfi.sqlite", "old")
    backup = tmp_path / "backups" / "desired.sqlite"
    create_online_backup(
        desired,
        backup,
        required_tables=REQUIRED_TABLES,
        required_migrations=REQUIRED_MIGRATIONS,
        invariants=(_state_invariant("new"),),
    )
    stale_hash = str(_inspect(target, "old")["database_sha256"])
    writer_ready = threading.Event()
    release_writer = threading.Event()
    outcome: list[BaseException] = []

    def writer() -> None:
        with operational_transaction(target, immediate=True) as conn:
            conn.execute(
                "INSERT INTO stage11_writer_events(marker) "
                "VALUES ('committed-before-restore')"
            )
            writer_ready.set()
            assert release_writer.wait(timeout=5)

    def restore() -> None:
        try:
            restore_verified_backup(
                backup,
                target,
                staging_directory=tmp_path / "restore_staging",
                rollback_directory=tmp_path / "rollback",
                expected_target_sha256=stale_hash,
                candidate_required_tables=REQUIRED_TABLES,
                candidate_required_migrations=REQUIRED_MIGRATIONS,
                candidate_invariants=(_state_invariant("new"),),
                target_required_tables=REQUIRED_TABLES,
                target_required_migrations=REQUIRED_MIGRATIONS,
                target_invariants=(_state_invariant("old"),),
            )
        except BaseException as exc:  # captured for the main test thread
            outcome.append(exc)

    writer_thread = threading.Thread(target=writer, daemon=True)
    restore_thread = threading.Thread(target=restore, daemon=True)
    writer_thread.start()
    assert writer_ready.wait(timeout=5)
    restore_thread.start()
    time.sleep(0.1)
    assert restore_thread.is_alive(), "restore must wait for the active shared transaction lock"
    release_writer.set()
    writer_thread.join(timeout=5)
    restore_thread.join(timeout=10)

    assert not writer_thread.is_alive() and not restore_thread.is_alive()
    assert len(outcome) == 1
    assert isinstance(outcome[0], BackupRestoreError)
    assert "changed after operator inspection" in str(outcome[0])
    assert _read_state(target) == "old"
    with sqlite3.connect(target) as conn:
        assert conn.execute("SELECT COUNT(*) FROM stage11_writer_events").fetchone()[0] == 1


def test_cli_backup_inspect_and_restore_use_same_verified_contract(tmp_path: Path) -> None:
    desired = _build_database(tmp_path / "desired" / "pfi.sqlite", "new")
    target = _build_database(tmp_path / "target" / "pfi.sqlite", "old")
    backup = tmp_path / "backups" / "desired.sqlite"

    backup_run = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "backup",
            "--database",
            str(desired),
            "--output",
            str(backup),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert backup_run.returncode == 0, backup_run.stderr
    backup_payload = json.loads(backup_run.stdout)
    assert backup_payload["method"] == "sqlite_online_backup_api"
    assert backup_payload["backup_path_included"] is False
    assert not str(tmp_path) in backup_run.stdout

    inspect_run = subprocess.run(
        [sys.executable, str(CLI), "inspect", "--database", str(target)],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert inspect_run.returncode == 0, inspect_run.stderr
    inspect_payload = json.loads(inspect_run.stdout)
    assert inspect_payload["database_path_included"] is False
    assert not str(tmp_path) in inspect_run.stdout
    expected_hash = inspect_payload["database_sha256"]

    restore_run = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "restore",
            "--backup",
            str(backup),
            "--target",
            str(target),
            "--staging-directory",
            str(tmp_path / "restore_staging"),
            "--rollback-directory",
            str(tmp_path / "rollback"),
            "--expected-target-sha256",
            expected_hash,
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert restore_run.returncode == 0, restore_run.stderr
    payload = json.loads(restore_run.stdout)
    assert payload["status"] == "restored"
    assert payload["target_database_path_included"] is False
    assert payload["rollback_directory_path_included"] is False
    assert not str(tmp_path) in restore_run.stdout
    assert (tmp_path / "rollback" / payload["rollback_artifact_name"]).is_file()
    assert _read_state(target) == "new"


def test_backup_refuses_overwrite_and_restore_refuses_unknown_target(tmp_path: Path) -> None:
    source = _build_database(tmp_path / "source" / "pfi.sqlite", "source")
    target = _build_database(tmp_path / "target" / "pfi.sqlite", "target")
    backup = tmp_path / "backups" / "snapshot.sqlite"
    create_online_backup(
        source,
        backup,
        required_tables=REQUIRED_TABLES,
        required_migrations=REQUIRED_MIGRATIONS,
        invariants=(_state_invariant("source"),),
    )
    with pytest.raises(BackupRestoreError, match="overwrite is forbidden"):
        create_online_backup(source, backup)

    with pytest.raises(BackupRestoreError, match="changed after operator inspection"):
        restore_verified_backup(
            backup,
            target,
            staging_directory=tmp_path / "restore_staging",
            rollback_directory=tmp_path / "rollback",
            expected_target_sha256="0" * 64,
            candidate_required_tables=REQUIRED_TABLES,
            candidate_required_migrations=REQUIRED_MIGRATIONS,
            candidate_invariants=(_state_invariant("source"),),
            target_required_tables=REQUIRED_TABLES,
            target_required_migrations=REQUIRED_MIGRATIONS,
            target_invariants=(_state_invariant("target"),),
        )
    assert _read_state(target) == "target"


def test_readonly_backup_rehearsal_is_path_free_and_source_stable(tmp_path: Path) -> None:
    source = _build_database(tmp_path / "source" / "pfi.sqlite", "rehearsal")
    source_lock = source.parent / f".{source.name}.pfi-operation.lock"
    source_lock.unlink(missing_ok=True)
    source_state_before = (
        source.stat().st_ino,
        source.stat().st_size,
        source.stat().st_mtime_ns,
        sorted(path.name for path in source.parent.iterdir()),
    )

    completed = subprocess.run(
        [sys.executable, str(REAL_REHEARSAL_CLI), "--database", str(source)],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr + completed.stdout
    payload = json.loads(completed.stdout)
    assert payload["status"] == "pass"
    assert payload["canonical_private_database_used"] is False
    assert payload["source_file_state_unchanged"] is True
    assert payload["source_directory_entries_unchanged"] is True
    assert payload["source_lock_created"] is False
    assert payload["isolated_success_restore_status"] == "restored"
    assert payload["isolated_rollback_status"] == "rolled_back"
    assert payload["private_values_emitted"] is False
    assert not str(tmp_path) in completed.stdout
    source_state_after = (
        source.stat().st_ino,
        source.stat().st_size,
        source.stat().st_mtime_ns,
        sorted(path.name for path in source.parent.iterdir()),
    )
    assert source_state_after == source_state_before


def test_verification_separately_rejects_foreign_key_damage_and_corruption(
    tmp_path: Path,
) -> None:
    foreign_key_broken = _build_database(tmp_path / "fk" / "pfi.sqlite", "fk")
    with sqlite3.connect(foreign_key_broken) as conn:
        conn.execute("PRAGMA foreign_keys = OFF")
        conn.execute("CREATE TABLE invariant_parent(item_id INTEGER PRIMARY KEY)")
        conn.execute(
            "CREATE TABLE invariant_child("
            "item_id INTEGER PRIMARY KEY REFERENCES invariant_parent(item_id))"
        )
        conn.execute("INSERT INTO invariant_child(item_id) VALUES (1)")
        conn.commit()

    with pytest.raises(SnapshotVerificationError) as foreign_key_failure:
        verify_sqlite_snapshot(
            foreign_key_broken,
            required_tables=REQUIRED_TABLES,
            required_migrations=REQUIRED_MIGRATIONS,
            invariants=(_state_invariant("fk"),),
            exclusive=True,
        )
    assert foreign_key_failure.value.report["integrity_check"] == ["ok"]
    assert foreign_key_failure.value.report["foreign_key_issue_count"] == 1

    corrupted = _build_database(tmp_path / "corrupt" / "pfi.sqlite", "corrupt")
    with corrupted.open("r+b") as handle:
        handle.write(b"not-a-sqlite-db!")
        handle.flush()
    with pytest.raises(SnapshotVerificationError) as corruption_failure:
        verify_sqlite_snapshot(corrupted, exclusive=True)
    assert corruption_failure.value.report["status"] == "fail"
    assert corruption_failure.value.report["error_type"] == "DatabaseError"


def test_backup_refuses_public_directory_without_changing_permissions(tmp_path: Path) -> None:
    source = _build_database(tmp_path / "source" / "pfi.sqlite", "source")
    public_directory = tmp_path / "public-backups"
    public_directory.mkdir(mode=0o755)
    os.chmod(public_directory, 0o755)

    with pytest.raises(BackupRestoreError, match="must not grant group or other access"):
        create_online_backup(source, public_directory / "snapshot.sqlite")

    assert stat_mode(public_directory) == 0o755


def stat_mode(path: Path) -> int:
    return path.stat().st_mode & 0o777


def test_durable_job_transactions_participate_in_exclusive_maintenance_lock(
    tmp_path: Path,
) -> None:
    database = tmp_path / "jobs" / "pfi.sqlite"
    store = SQLiteDurableJobStore(database)
    store.initialize()
    transaction_ready = threading.Event()
    release_transaction = threading.Event()
    maintenance_acquired = threading.Event()

    def active_job_transaction() -> None:
        with store._transaction(immediate=True):
            transaction_ready.set()
            assert release_transaction.wait(timeout=5)

    def maintenance() -> None:
        with operational_store_guard(database, exclusive=True):
            maintenance_acquired.set()

    transaction_thread = threading.Thread(target=active_job_transaction, daemon=True)
    maintenance_thread = threading.Thread(target=maintenance, daemon=True)
    transaction_thread.start()
    assert transaction_ready.wait(timeout=5)
    maintenance_thread.start()
    time.sleep(0.1)
    assert not maintenance_acquired.is_set()
    release_transaction.set()
    transaction_thread.join(timeout=5)
    maintenance_thread.join(timeout=5)
    assert maintenance_acquired.is_set()
