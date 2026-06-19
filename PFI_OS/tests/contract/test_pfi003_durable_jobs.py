import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from pfi_os.application import (
    DurableJobStore,
    OperationalStore,
    PFI003_DURABLE_JOB_STORE_SCHEMA,
    PFI003_RUNTIME_SUPERVISOR_SCHEMA,
    build_pfi003_runtime_supervisor_contract,
    durable_job_id,
)


def test_pfi003_runtime_supervisor_contract_declares_job_lifecycle_and_safety_boundary():
    contract = build_pfi003_runtime_supervisor_contract()

    assert contract["schema"] == PFI003_RUNTIME_SUPERVISOR_SCHEMA
    assert contract["job_store_schema"] == PFI003_DURABLE_JOB_STORE_SCHEMA
    assert contract["storage"] == {
        "table": "job_records",
        "schema_migration": "non_destructive_metadata_contract",
        "new_tables": False,
    }
    for state in ["queued", "running", "completed", "retrying", "cancelled", "resumed", "dead_letter"]:
        assert state in contract["states"]
    assert contract["claiming"]["atomic_claim"] is True
    assert contract["claiming"]["sqlite_lock"] == "BEGIN IMMEDIATE"
    assert contract["claiming"]["double_worker_behavior"] == "only_one_worker_receives_active_lease"
    assert contract["recovery"]["expired_lease_requeue"] is True
    assert contract["recovery"]["dead_letter_after_max_attempts"] is True
    assert contract["recovery"]["cancel"] is True
    assert contract["recovery"]["resume"] is True
    assert contract["readiness"] == {"web": "separate", "api": "separate", "worker": "separate"}
    assert contract["safety_boundary"]["no_live_trading"] is True
    assert contract["safety_boundary"]["no_broker_calls"] is True
    assert contract["safety_boundary"]["no_order_execution"] is True
    assert contract["safety_boundary"]["no_payment_or_betting"] is True


def test_enqueue_is_idempotent_and_persists_metadata_without_new_tables(tmp_path: Path):
    jobs = DurableJobStore(_store(tmp_path))

    first = jobs.enqueue(job_type="fast_path_refresh", idempotency_key="market:SPY:2026-06-20", payload={"symbol": "SPY"})
    duplicate = jobs.enqueue(job_type="fast_path_refresh", idempotency_key="market:SPY:2026-06-20", payload={"symbol": "QQQ"})

    row = _job_row(jobs, first["job_id"])
    metadata = json.loads(row["metadata_json"])

    assert first["queued"] is True
    assert duplicate["queued"] is False
    assert duplicate["job_id"] == first["job_id"] == durable_job_id(
        job_type="fast_path_refresh",
        idempotency_key="market:SPY:2026-06-20",
    )
    assert len(jobs.store.table_rows("job_records")) == 1
    assert metadata["schema"] == PFI003_DURABLE_JOB_STORE_SCHEMA
    assert metadata["idempotency_key"] == "market:SPY:2026-06-20"
    assert metadata["payload"] == {"symbol": "SPY"}
    assert metadata["safety_boundary"]["no_order_execution"] is True


def test_atomic_claim_allows_only_one_worker_to_hold_active_lease(tmp_path: Path):
    jobs = DurableJobStore(_store(tmp_path))
    jobs.enqueue(job_type="fast_path_refresh", idempotency_key="market:SPY:2026-06-20")

    first = jobs.claim(job_type="fast_path_refresh", worker_id="worker-a", lease_seconds=30, now=_dt(10, 0, 0))
    second = jobs.claim(job_type="fast_path_refresh", worker_id="worker-b", lease_seconds=30, now=_dt(10, 0, 1))

    assert first["claimed"] is True
    assert first["status"] == "running"
    assert first["lease_owner"] == "worker-a"
    assert second["claimed"] is False
    assert second["status"] == "idle"
    with pytest.raises(PermissionError):
        jobs.heartbeat(first["job_id"], worker_id="worker-b", progress=0.5, now=_dt(10, 0, 2))


def test_heartbeat_extends_lease_and_complete_requires_owner(tmp_path: Path):
    jobs = DurableJobStore(_store(tmp_path))
    jobs.enqueue(job_type="strategy_backtest", idempotency_key="backtest:SPY:ma")
    claimed = jobs.claim(job_type="strategy_backtest", worker_id="worker-a", lease_seconds=10, now=_dt(10, 0, 0))

    heartbeat = jobs.heartbeat(
        claimed["job_id"],
        worker_id="worker-a",
        progress=0.45,
        phase="running_backtest",
        lease_seconds=20,
        now=_dt(10, 0, 5),
    )

    assert heartbeat["phase"] == "running_backtest"
    assert heartbeat["progress"] == 0.45
    assert heartbeat["heartbeat_at"].endswith("10:00:05+00:00")
    assert heartbeat["lease_expires_at"].endswith("10:00:25+00:00")
    with pytest.raises(PermissionError):
        jobs.complete(claimed["job_id"], worker_id="worker-b")
    completed = jobs.complete(claimed["job_id"], worker_id="worker-a", artifact_uri="operational_store:artifact")
    assert completed["status"] == "completed"
    assert completed["phase"] == "completed"
    assert completed["progress"] == 1.0
    assert completed["artifact_uri"] == "operational_store:artifact"


def test_fail_or_retry_is_bounded_and_moves_to_dead_letter(tmp_path: Path):
    jobs = DurableJobStore(_store(tmp_path))
    jobs.enqueue(job_type="research_report_refresh", idempotency_key="report:alpha", max_attempts=2)
    claimed = jobs.claim(job_type="research_report_refresh", worker_id="worker-a", now=_dt(10, 0, 0))

    retry = jobs.fail_or_retry(claimed["job_id"], worker_id="worker-a", error_message="network source unavailable", now=_dt(10, 0, 1))
    reclaimed = jobs.claim(job_type="research_report_refresh", worker_id="worker-b", now=_dt(10, 0, 2))
    dead = jobs.fail_or_retry(reclaimed["job_id"], worker_id="worker-b", error_message="network source unavailable", now=_dt(10, 0, 3))

    assert retry["status"] == "retrying"
    assert retry["retry_count"] == 1
    assert retry["queued"] is True
    assert reclaimed["claimed"] is True
    assert reclaimed["lease_owner"] == "worker-b"
    assert dead["status"] == "dead_letter"
    assert dead["phase"] == "dead_letter"
    assert dead["retry_count"] == 2
    assert dead["dead_letter_reason"] == "network source unavailable"


def test_cancel_and_resume_make_job_claimable_again(tmp_path: Path):
    jobs = DurableJobStore(_store(tmp_path))
    queued = jobs.enqueue(job_type="portfolio_reconcile", idempotency_key="portfolio:main")

    cancelled = jobs.cancel(queued["job_id"], reason="user paused run", now=_dt(10, 0, 0))
    no_claim = jobs.claim(job_type="portfolio_reconcile", worker_id="worker-a", now=_dt(10, 0, 1))
    resumed = jobs.resume(queued["job_id"], reason="user resumed run", now=_dt(10, 0, 2))
    claimed = jobs.claim(job_type="portfolio_reconcile", worker_id="worker-a", now=_dt(10, 0, 3))

    assert cancelled["status"] == "cancelled"
    assert no_claim["claimed"] is False
    assert resumed["status"] == "queued"
    assert resumed["phase"] == "resumed"
    assert claimed["claimed"] is True
    assert claimed["job_id"] == queued["job_id"]


def test_expired_lease_recovery_requeues_then_dead_letters_after_attempts(tmp_path: Path):
    jobs = DurableJobStore(_store(tmp_path))
    jobs.enqueue(job_type="minute_fast_path", idempotency_key="fast:path", max_attempts=2)
    first = jobs.claim(job_type="minute_fast_path", worker_id="worker-a", lease_seconds=5, now=_dt(10, 0, 0))

    recovered_once = jobs.recover_expired_leases(now=_dt(10, 0, 6), job_type="minute_fast_path")
    second = jobs.claim(job_type="minute_fast_path", worker_id="worker-b", lease_seconds=5, now=_dt(10, 0, 7))
    recovered_twice = jobs.recover_expired_leases(now=_dt(10, 0, 13), job_type="minute_fast_path")
    row = _job_row(jobs, first["job_id"])

    assert recovered_once["recovered_count"] == 1
    assert recovered_once["recovered"][0]["status"] == "retrying"
    assert recovered_once["recovered"][0]["retry_count"] == 1
    assert second["claimed"] is True
    assert second["lease_owner"] == "worker-b"
    assert recovered_twice["recovered_count"] == 1
    assert recovered_twice["recovered"][0]["status"] == "dead_letter"
    assert row["status"] == "dead_letter"
    assert row["phase"] == "dead_letter"
    assert row["retry_count"] == 2


def test_readiness_reports_web_api_worker_separately_and_has_no_execution_path(tmp_path: Path):
    jobs = DurableJobStore(_store(tmp_path))
    jobs.enqueue(job_type="minute_fast_path", idempotency_key="fast:path")

    readiness = jobs.readiness(worker_id="worker-a")
    serialized = json.dumps(readiness, ensure_ascii=False)

    assert readiness["schema"] == PFI003_RUNTIME_SUPERVISOR_SCHEMA
    assert readiness["web"]["ready"] is True
    assert readiness["api"]["ready"] is True
    assert readiness["worker"]["ready"] is True
    assert readiness["job_store"]["active_jobs"] == 1
    assert "broker" in serialized
    assert "order_execution" in serialized
    assert readiness["safety_boundary"]["no_broker_calls"] is True
    assert readiness["safety_boundary"]["no_order_execution"] is True


def _store(tmp_path: Path) -> OperationalStore:
    return OperationalStore(tmp_path / "private" / "operational" / "pfi.sqlite")


def _job_row(jobs: DurableJobStore, job_id: str) -> dict:
    return next(row for row in jobs.store.table_rows("job_records") if row["job_id"] == job_id)


def _dt(hour: int, minute: int, second: int) -> datetime:
    return datetime(2026, 6, 20, hour, minute, second, tzinfo=timezone.utc)
