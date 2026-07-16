from __future__ import annotations

import hashlib
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from pfi_os.application.supervisor import RuntimeJobSupervisor


BASE_TIME = datetime(2026, 7, 15, 4, 0, tzinfo=timezone.utc)


def _hash(label: str) -> str:
    return hashlib.sha256(f"phase-10-3:{label}".encode()).hexdigest()


def _policy() -> dict[str, object]:
    return {
        "dependency_registry_sha256": _hash("registry"),
        "data_hash": _hash("data"),
        "formula_hash": _hash("formula"),
        "parameter_hash": _hash("parameter"),
        "read_model_hash": _hash("read-model"),
        "streamlit_cache_key": _hash("cache"),
        "dependency_snapshot_valid": True,
        "ordinary_run_network_allowed": False,
        "no_diff_network_allowed": False,
    }


def _supervisor(
    tmp_path: Path,
    *,
    builder=_policy,
    lease_seconds: int = 5,
    timeout_seconds: float = 1.0,
    clock=lambda: BASE_TIME,
) -> RuntimeJobSupervisor:
    return RuntimeJobSupervisor(
        tmp_path / "private" / "operational" / "pfi.sqlite",
        backup_dir=tmp_path / "private" / "runtime" / "migration_backups",
        cache_policy_builder=builder,
        lease_seconds=lease_seconds,
        timeout_seconds=timeout_seconds,
        auto_start=False,
        clock=clock,
    )


def test_offline_cache_refresh_uses_persistent_progress_and_hash_only_logs(
    tmp_path: Path,
) -> None:
    supervisor = _supervisor(tmp_path)
    submitted = supervisor.submit_cache_refresh(request_id="offline-success")
    repeated = supervisor.submit_cache_refresh(request_id="offline-success")

    assert submitted["created"] is True
    assert repeated["created"] is False
    assert repeated["job"]["job_id"] == submitted["job"]["job_id"]
    assert submitted["external_network_calls"] == 0
    result = supervisor.run_pending_once()
    assert result is not None
    assert result["status"] == "succeeded"

    projection = supervisor.get(submitted["job"]["job_id"])
    job = projection["job"]
    assert job["status"] == "succeeded"
    assert job["progress"] == {
        "completed_units": 3,
        "total_units": 3,
        "percent": 100.0,
        "step": "cache.runtime_ready",
        "source": "durable_job_events",
        "timer_based": False,
    }
    assert job["result"]["artifact_uri"] == f"artifact://runtime-cache/{_hash('cache')}"
    assert job["trace"]["trace_id"]
    assert job["observability"]["external_network_calls"] == 0
    assert [event["event_type"] for event in projection["events"]] == [
        "queued",
        "claimed",
        "progressed",
        "progressed",
        "progressed",
        "succeeded",
    ]
    assert len(projection["events"]) == len(projection["logs"]) == 6
    serialized = repr(projection)
    assert "/Users/" not in serialized
    assert "amount" not in serialized.lower()
    assert "balance" not in serialized.lower()


def test_timeout_is_an_explicit_failed_state_with_cache_fallback(tmp_path: Path) -> None:
    def slow_policy() -> dict[str, object]:
        time.sleep(0.08)
        return _policy()

    supervisor = _supervisor(
        tmp_path,
        builder=slow_policy,
        timeout_seconds=0.01,
    )
    submitted = supervisor.submit_cache_refresh(request_id="timeout-failure")
    result = supervisor.run_pending_once()
    assert result is not None
    assert result["status"] == "failed"

    job = supervisor.get(submitted["job"]["job_id"])["job"]
    assert job["status"] == "failed"
    assert job["error"] == {
        "code": "LOCAL_TIMEOUT",
        "message": "local cache refresh exceeded its bounded timeout",
    }
    assert job["observability"]["cache_fallback_used"] is True
    assert job["progress"]["percent"] is None


def test_policy_claiming_an_external_call_fails_before_runtime_work(tmp_path: Path) -> None:
    def unsafe_policy() -> dict[str, object]:
        return {**_policy(), "external_network_calls": 1}

    supervisor = _supervisor(tmp_path, builder=unsafe_policy)
    submitted = supervisor.submit_cache_refresh(request_id="network-claim-rejected")
    result = supervisor.run_pending_once()
    assert result is not None
    assert result["status"] == "failed"
    job = supervisor.get(submitted["job"]["job_id"])["job"]
    assert job["error"]["code"] == "CACHE_REFRESH_ERROR"
    assert job["observability"]["external_network_calls"] == 0
    assert job["progress"]["completed_units"] == 0


def test_healthy_long_task_heartbeats_without_duplicate_execution(tmp_path: Path) -> None:
    calls = 0

    def long_policy() -> dict[str, object]:
        nonlocal calls
        calls += 1
        if calls == 2:
            time.sleep(1.35)
        return _policy()

    supervisor = _supervisor(
        tmp_path,
        builder=long_policy,
        lease_seconds=1,
        timeout_seconds=3.0,
        clock=lambda: datetime.now(timezone.utc),
    )
    submitted = supervisor.submit_cache_refresh(request_id="healthy-long-task")
    result: dict[str, object] = {}

    def execute() -> None:
        outcome = supervisor.run_pending_once()
        assert outcome is not None
        result.update(outcome)

    worker = threading.Thread(target=execute)
    worker.start()
    while worker.is_alive():
        supervisor.recover_and_resume()
        time.sleep(0.1)
    worker.join(timeout=5)

    assert result["status"] == "succeeded"
    projection = supervisor.get(submitted["job"]["job_id"])
    job = projection["job"]
    event_types = [event["event_type"] for event in projection["events"]]
    assert job["attempt_count"] == 1
    assert job["observability"]["retry_count"] == 0
    assert event_types.count("heartbeat") >= 2
    assert "lease_expired_requeued" not in event_types
    assert calls == 2


def test_restart_recovers_killed_worker_lease_and_resumes_from_sqlite(
    tmp_path: Path,
) -> None:
    clock = {"now": BASE_TIME}
    first = _supervisor(tmp_path, clock=lambda: clock["now"])
    submitted = first.submit_cache_refresh(request_id="killed-worker")
    claimed = first.store.claim(
        job_type="cache.refresh",
        worker_id="pfi-runtime-cache-worker",
        lease_seconds=5,
        now=clock["now"],
    )
    progress = first.store.record_progress(
        submitted["job"]["job_id"],
        worker_id="pfi-runtime-cache-worker",
        lease_token=claimed["lease"]["token"],
        expected_revision=claimed["job"]["revision"],
        completed_units=1,
        total_units=3,
        step="cache.dependency_snapshot",
        now=clock["now"] + timedelta(seconds=1),
    )
    assert progress["status"] == "running"

    clock["now"] += timedelta(seconds=6)
    restarted = _supervisor(tmp_path, clock=lambda: clock["now"])
    recovered = restarted.recover_and_resume(now=clock["now"])
    assert recovered["recovered_count"] == 1
    assert recovered["recovered_job_ids"] == [submitted["job"]["job_id"]]
    assert recovered["resumable_job_ids"] == [submitted["job"]["job_id"]]
    assert recovered["scheduled_job_ids"] == []

    clock["now"] += timedelta(seconds=1)
    resumed = restarted.run_pending_once(now=clock["now"])
    assert resumed is not None
    assert resumed["status"] == "succeeded"
    final = restarted.get(submitted["job"]["job_id"])["job"]
    assert final["status"] == "succeeded"
    assert final["attempt_count"] == 2
    assert final["observability"]["retry_count"] == 1
    assert final["progress"]["completed_units"] == 3
    assert restarted.store.integrity()["status"] == "pass"
