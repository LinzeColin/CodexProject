from __future__ import annotations

import sqlite3
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Barrier

import pytest

from pfi_os.application.jobs import (
    ACCEPTANCE_ID,
    JOB_STATUSES,
    PHASE_ID,
    TASK_IDS,
    JobConflictError,
    JobLifecycleError,
    JobTransitionError,
    LeaseConflictError,
    StaleRevisionError,
    build_phase_10_1_contract,
)
from pfi_os.infrastructure.jobs import SQLiteDurableJobStore


BASE_TIME = datetime(2026, 7, 15, 1, 0, tzinfo=timezone.utc)


def _store(tmp_path: Path, *, token: str = "opaque-contract-token") -> SQLiteDurableJobStore:
    return SQLiteDurableJobStore(
        tmp_path / "private" / "runtime" / "jobs.sqlite",
        backup_dir=tmp_path / "private" / "runtime" / "migration_backups",
        token_factory=lambda: token,
    )


def _claim(
    store: SQLiteDurableJobStore,
    *,
    key: str,
    max_attempts: int = 3,
    contains_financial_facts: bool = False,
    now: datetime = BASE_TIME,
) -> dict[str, object]:
    store.enqueue(
        job_type="report.generate",
        idempotency_key=key,
        payload={"sentinel": key},
        max_attempts=max_attempts,
        contains_financial_facts=contains_financial_facts,
        now=now,
    )
    result = store.claim(
        job_type="report.generate",
        worker_id="worker-1",
        lease_seconds=60,
        now=now,
    )
    assert result["claimed"] is True
    return result


def test_phase_contract_is_exactly_phase_10_1_and_does_not_claim_stage_acceptance() -> None:
    contract = build_phase_10_1_contract()

    assert contract["phase_id"] == PHASE_ID == "V025-S10-P10.1"
    assert contract["task_ids"] == list(TASK_IDS) == [
        "S10-P1-T1",
        "S10-P1-T2",
        "S10-P1-T3",
        "S10-P1-T4",
    ]
    assert contract["acceptance_id"] == ACCEPTANCE_ID
    assert contract["states"] == list(JOB_STATUSES)
    assert contract["storage"]["process_memory_only"] is False
    assert contract["worker_protocol"]["claim_compare_and_swap"] == "job_id + revision + prior status"
    assert contract["worker_protocol"]["lease_token_persisted"] is False
    assert contract["progress"]["timer_based"] is False
    assert contract["progress"]["heartbeat_counts_as_progress"] is False
    assert contract["sqlite"]["journal_mode"] == "DELETE"
    assert contract["sqlite"]["wal_enabled"] is False
    assert "3.51.3" in contract["sqlite"]["reason"]
    assert "3.50.7" in contract["sqlite"]["reason"]
    assert contract["safety_boundary"]["external_network_allowed"] is False
    assert contract["safety_boundary"]["background_publish_unverified_financial_facts"] is False
    assert contract["safety_boundary"]["real_database_used_by_phase_tests"] is False
    assert contract["safety_boundary"]["finder_used"] is False
    assert contract["phase_10_2_started"] is False
    assert contract["phase_10_3_started"] is False
    assert contract["stage_10_whole_review_status"] == "not_started"


def test_additive_migration_backs_up_existing_state_and_records_sqlite_gate(tmp_path: Path) -> None:
    db_path = tmp_path / "private" / "runtime" / "jobs.sqlite"
    db_path.parent.mkdir(parents=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute("CREATE TABLE existing_private_state(key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        conn.execute("INSERT INTO existing_private_state VALUES ('preserve', 'yes')")

    store = _store(tmp_path)
    backups = list((tmp_path / "private" / "runtime" / "migration_backups").glob("*.sqlite"))
    assert len(backups) == 1
    with sqlite3.connect(backups[0]) as backup:
        assert backup.execute(
            "SELECT value FROM existing_private_state WHERE key = 'preserve'"
        ).fetchone()[0] == "yes"
        assert backup.execute("PRAGMA integrity_check").fetchone()[0] == "ok"

    integrity = store.integrity()
    snapshot = store.schema_snapshot()
    python_sqlite3_module_version = integrity.pop("python_sqlite3_module_version")
    assert python_sqlite3_module_version
    assert integrity == {
        "status": "pass",
        "sqlite_runtime_version": sqlite3.sqlite_version,
        "journal_mode": "DELETE",
        "wal_enabled": False,
        "foreign_keys": True,
        "busy_timeout_ms": 30000,
        "synchronous": 2,
        "explicit_transactions": True,
        "rollback_on_error": True,
        "migration_id": "v025_stage10_durable_jobs_v1",
        "observability_migration_id": "v025_stage10_job_observability_v1",
        "migration_ids": [
            "v025_stage10_durable_jobs_v1",
            "v025_stage10_job_observability_v1",
        ],
        "migration_count": 2,
        "integrity_check": "ok",
        "foreign_key_check": "pass",
        "foreign_key_issue_count": 0,
        "job_count": 0,
        "event_count": 0,
        "trace_count": 0,
        "span_count": 0,
        "log_count": 0,
        "observability_consistent": True,
    }
    assert set(snapshot["tables"]) == {
        "durable_jobs",
        "durable_job_events",
        "durable_job_trace_contexts",
        "durable_job_spans",
        "durable_job_logs",
        "pfi_schema_migrations",
    }
    for column in ("status", "revision", "lease_owner", "lease_expires_at", "heartbeat_at"):
        assert column in snapshot["tables"]["durable_jobs"]
    assert snapshot["triggers"] == [
        "durable_job_events_no_delete",
        "durable_job_events_no_update",
        "durable_job_logs_no_delete",
        "durable_job_logs_no_update",
        "durable_job_spans_no_delete",
        "durable_job_spans_no_update",
        "durable_job_trace_contexts_no_delete",
        "durable_job_trace_contexts_no_update",
    ]


def test_enqueue_is_idempotent_but_conflicting_immutable_input_fails_closed(tmp_path: Path) -> None:
    store = _store(tmp_path)
    first = store.enqueue(
        job_type="report.generate",
        idempotency_key="same-key",
        payload={"b": 2, "a": 1},
        max_attempts=2,
        now=BASE_TIME,
    )
    repeated = store.enqueue(
        job_type="report.generate",
        idempotency_key="same-key",
        payload={"a": 1, "b": 2},
        max_attempts=2,
        now=BASE_TIME + timedelta(seconds=1),
    )

    assert first["created"] is True
    assert repeated["created"] is False
    assert repeated["job"] == first["job"]
    assert "payload" not in first["job"]
    assert len(store.list_events(first["job"]["job_id"])) == 1

    with pytest.raises(JobConflictError, match="different immutable inputs"):
        store.enqueue(
            job_type="report.generate",
            idempotency_key="same-key",
            payload={"a": 9},
            max_attempts=2,
            now=BASE_TIME,
        )
    with pytest.raises(TypeError, match="must be a boolean"):
        store.enqueue(
            job_type="report.generate",
            idempotency_key="invalid-bool",
            payload={},
            contains_financial_facts="false",  # type: ignore[arg-type]
            now=BASE_TIME,
        )
    with pytest.raises(JobConflictError, match="different immutable inputs"):
        store.enqueue(
            job_type="report.generate",
            idempotency_key="same-key",
            payload={"a": 1, "b": 2},
            max_attempts=3,
            now=BASE_TIME,
        )


def test_concurrent_claim_has_one_winner_and_all_worker_writes_are_revision_cas(tmp_path: Path) -> None:
    store = _store(tmp_path, token="claim-winner-token")
    queued = store.enqueue(
        job_type="report.generate",
        idempotency_key="concurrent-claim",
        payload={"sentinel": True},
        now=BASE_TIME,
    )["job"]
    barrier = Barrier(2)

    def claim_as(worker_id: str) -> dict[str, object]:
        barrier.wait(timeout=5)
        return store.claim(
            job_type="report.generate",
            worker_id=worker_id,
            lease_seconds=30,
            now=BASE_TIME,
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(claim_as, ("worker-a", "worker-b")))

    winners = [result for result in results if result["claimed"]]
    losers = [result for result in results if not result["claimed"]]
    assert len(winners) == 1
    assert len(losers) == 1
    winner = winners[0]
    worker_id = winner["lease"]["owner"]
    assert winner["job"]["revision"] == 1
    assert winner["job"]["attempt_count"] == 1
    assert winner["job"]["lease"]["token_exposed"] is False

    with sqlite3.connect(store.db_path) as conn:
        raw = conn.execute(
            "SELECT lease_token_hash, payload_json FROM durable_jobs WHERE job_id = ?",
            (queued["job_id"],),
        ).fetchone()
    assert raw[0] != winner["lease"]["token"]
    assert winner["lease"]["token"] not in raw[0]
    assert winner["payload"] == {"sentinel": True}

    with pytest.raises(LeaseConflictError, match="token"):
        store.heartbeat(
            queued["job_id"],
            worker_id=worker_id,
            lease_token="wrong-token",
            expected_revision=1,
            now=BASE_TIME + timedelta(seconds=1),
        )
    heartbeat = store.heartbeat(
        queued["job_id"],
        worker_id=worker_id,
        lease_token=winner["lease"]["token"],
        expected_revision=1,
        now=BASE_TIME + timedelta(seconds=1),
    )
    assert heartbeat["revision"] == 2
    assert heartbeat["progress"]["percent"] is None
    with pytest.raises(StaleRevisionError, match="expected revision 1"):
        store.heartbeat(
            queued["job_id"],
            worker_id=worker_id,
            lease_token=winner["lease"]["token"],
            expected_revision=1,
            now=BASE_TIME + timedelta(seconds=2),
        )


def test_progress_comes_only_from_monotonic_events_and_financial_result_stays_unpublished(
    tmp_path: Path,
) -> None:
    store = _store(tmp_path)
    claimed = _claim(store, key="real-progress", contains_financial_facts=True)
    job_id = claimed["job"]["job_id"]
    token = claimed["lease"]["token"]
    worker_id = claimed["lease"]["owner"]

    first = store.record_progress(
        job_id,
        worker_id=worker_id,
        lease_token=token,
        expected_revision=claimed["job"]["revision"],
        completed_units=1,
        total_units=3,
        step="parse-input",
        now=BASE_TIME + timedelta(seconds=1),
    )
    assert first["progress"] == {
        "completed_units": 1,
        "total_units": 3,
        "percent": 33.33,
        "step": "parse-input",
        "source": "durable_job_events",
        "timer_based": False,
    }
    with pytest.raises(JobLifecycleError, match="advance units or record a new real step"):
        store.record_progress(
            job_id,
            worker_id=worker_id,
            lease_token=token,
            expected_revision=first["revision"],
            completed_units=1,
            total_units=3,
            step="parse-input",
            now=BASE_TIME + timedelta(seconds=2),
        )
    with pytest.raises(JobLifecycleError, match="monotonic"):
        store.record_progress(
            job_id,
            worker_id=worker_id,
            lease_token=token,
            expected_revision=first["revision"],
            completed_units=0,
            total_units=3,
            step="regress",
            now=BASE_TIME + timedelta(seconds=2),
        )
    with pytest.raises(JobTransitionError, match="real completed_units"):
        store.succeed(
            job_id,
            worker_id=worker_id,
            lease_token=token,
            expected_revision=first["revision"],
            now=BASE_TIME + timedelta(seconds=2),
        )

    final_progress = store.record_progress(
        job_id,
        worker_id=worker_id,
        lease_token=token,
        expected_revision=first["revision"],
        completed_units=3,
        total_units=3,
        step="persist-report",
        now=BASE_TIME + timedelta(seconds=3),
    )
    done = store.succeed(
        job_id,
        worker_id=worker_id,
        lease_token=token,
        expected_revision=final_progress["revision"],
        result_uri="private://reports/sentinel",
        now=BASE_TIME + timedelta(seconds=4),
    )
    assert done["status"] == "succeeded"
    assert done["progress"]["percent"] == 100.0
    assert done["result"] == {
        "artifact_uri": "private://reports/sentinel",
        "review_state": "pending_human_review",
        "publishable": False,
    }
    with pytest.raises(ValueError, match="result_uri"):
        store.succeed(
            job_id,
            worker_id=worker_id,
            lease_token=token,
            expected_revision=done["revision"],
            result_uri="https://example.invalid/public",
            now=BASE_TIME + timedelta(seconds=5),
        )

    events = store.list_events(job_id)
    assert [event["job_revision"] for event in events] == list(range(len(events)))
    assert [event["event_type"] for event in events] == [
        "queued",
        "claimed",
        "progressed",
        "progressed",
        "succeeded",
    ]
    for index, event in enumerate(events):
        assert event["progress"]["timer_based"] is False
        assert event["previous_event_hash"] == ("" if index == 0 else events[index - 1]["event_hash"])

    with sqlite3.connect(store.db_path) as conn:
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            conn.execute(
                "UPDATE durable_job_events SET event_type = 'tampered' WHERE job_id = ?",
                (job_id,),
            )


def test_retry_failed_cancelled_and_dead_letter_states_are_durable(tmp_path: Path) -> None:
    store = _store(tmp_path, token="state-token")
    retry_claim = _claim(store, key="retry-then-fail", max_attempts=3)
    job_id = retry_claim["job"]["job_id"]
    retrying = store.fail(
        job_id,
        worker_id="worker-1",
        lease_token=retry_claim["lease"]["token"],
        expected_revision=retry_claim["job"]["revision"],
        error_code="TRANSIENT_IO",
        error_message="temporary local input issue",
        retryable=True,
        now=BASE_TIME + timedelta(seconds=1),
    )
    assert retrying["status"] == "retrying"
    assert retrying["finished_at"] == ""

    second_claim = store.claim(
        job_type="report.generate",
        worker_id="worker-1",
        now=BASE_TIME + timedelta(seconds=2),
    )
    assert second_claim["job"]["job_id"] == job_id
    assert second_claim["job"]["attempt_count"] == 2
    failed = store.fail(
        job_id,
        worker_id="worker-1",
        lease_token=second_claim["lease"]["token"],
        expected_revision=second_claim["job"]["revision"],
        error_code="INPUT_INVALID",
        error_message="permanent validation error at /Users/private/raw.csv",
        retryable=False,
        now=BASE_TIME + timedelta(seconds=3),
    )
    assert failed["status"] == "failed"
    assert failed["error"]["message"] == "permanent validation error at <redacted-private-path>"
    quarantined = store.dead_letter(
        job_id,
        expected_revision=failed["revision"],
        reason_code="MANUAL_QUARANTINE",
        reason="owner-visible terminal quarantine",
        now=BASE_TIME + timedelta(seconds=4),
    )
    assert quarantined["status"] == "dead_letter"

    exhausted_claim = _claim(
        store,
        key="exhausted",
        max_attempts=1,
        now=BASE_TIME + timedelta(seconds=5),
    )
    exhausted = store.fail(
        exhausted_claim["job"]["job_id"],
        worker_id="worker-1",
        lease_token=exhausted_claim["lease"]["token"],
        expected_revision=exhausted_claim["job"]["revision"],
        error_code="RETRY_EXHAUSTED",
        error_message="single attempt exhausted",
        retryable=True,
        now=BASE_TIME + timedelta(seconds=6),
    )
    assert exhausted["status"] == "dead_letter"

    cancelled_claim = _claim(store, key="cancel-running", now=BASE_TIME + timedelta(seconds=7))
    cancelled = store.cancel(
        cancelled_claim["job"]["job_id"],
        expected_revision=cancelled_claim["job"]["revision"],
        reason="owner requested cancellation",
        now=BASE_TIME + timedelta(seconds=8),
    )
    assert cancelled["status"] == "cancelled"
    with pytest.raises(StaleRevisionError):
        store.record_progress(
            cancelled["job_id"],
            worker_id="worker-1",
            lease_token=cancelled_claim["lease"]["token"],
            expected_revision=cancelled_claim["job"]["revision"],
            completed_units=1,
            total_units=1,
            step="stale-worker-write",
            now=BASE_TIME + timedelta(seconds=9),
        )


def test_restart_recovers_expired_lease_then_dead_letters_after_bounded_attempts(
    tmp_path: Path,
) -> None:
    first_store = _store(tmp_path, token="first-lease-token")
    claimed = _claim(first_store, key="crash-recovery", max_attempts=2)
    job_id = claimed["job"]["job_id"]
    progress = first_store.record_progress(
        job_id,
        worker_id="worker-1",
        lease_token=claimed["lease"]["token"],
        expected_revision=claimed["job"]["revision"],
        completed_units=1,
        total_units=4,
        step="durable-checkpoint",
        now=BASE_TIME + timedelta(seconds=1),
    )
    assert progress["revision"] == 2

    restarted = SQLiteDurableJobStore(
        first_store.db_path,
        backup_dir=tmp_path / "private" / "runtime" / "migration_backups",
        token_factory=lambda: "second-lease-token",
    )
    recovered = restarted.recover_expired_leases(now=BASE_TIME + timedelta(seconds=61))
    assert recovered["recovered_count"] == 1
    assert recovered["jobs"][0]["status"] == "retrying"
    assert recovered["jobs"][0]["progress"]["completed_units"] == 1

    reclaimed = restarted.claim(
        job_type="report.generate",
        worker_id="worker-2",
        lease_seconds=30,
        now=BASE_TIME + timedelta(seconds=62),
    )
    assert reclaimed["claimed"] is True
    assert reclaimed["job"]["attempt_count"] == 2
    assert reclaimed["lease"]["token"] == "second-lease-token"
    final_recovery = restarted.recover_expired_leases(now=BASE_TIME + timedelta(seconds=93))
    assert final_recovery["recovered_count"] == 1
    assert final_recovery["jobs"][0]["status"] == "dead_letter"
    assert restarted.get(job_id)["status"] == "dead_letter"
    assert restarted.integrity()["status"] == "pass"
