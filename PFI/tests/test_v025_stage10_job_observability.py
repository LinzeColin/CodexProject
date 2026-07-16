from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from pfi_os.infrastructure.jobs import SQLiteDurableJobStore
from pfi_os.observability import build_phase_10_3_contract


BASE_TIME = datetime(2026, 7, 15, 3, 0, tzinfo=timezone.utc)


def _store(tmp_path: Path) -> SQLiteDurableJobStore:
    return SQLiteDurableJobStore(
        tmp_path / "private" / "runtime" / "jobs.sqlite",
        backup_dir=tmp_path / "private" / "runtime" / "migration_backups",
        token_factory=lambda: "phase-10-3-lease-token",
    )


def test_phase_10_3_contract_is_bounded_and_forbids_fake_progress_or_gui_file_ops() -> None:
    contract = build_phase_10_3_contract()

    assert contract["phase_id"] == "V025-S10-P10.3"
    assert contract["task_ids"] == [
        "S10-P3-T1",
        "S10-P3-T2",
        "S10-P3-T3",
        "S10-P3-T4",
    ]
    assert contract["acceptance_id"] == "ACC-PFI-V025-STAGE10-WHOLE-REVIEW"
    assert contract["structured_logs"]["redacted_before_persist"] is True
    assert contract["ui"]["timer_based_progress"] is False
    assert contract["safety_boundary"] == {
        "external_network_allowed": False,
        "canonical_private_database_used_by_phase_tests": False,
        "financial_values_in_logs_or_evidence": False,
        "finder_used": False,
        "launchservices_used": False,
        "gui_file_operations_used": False,
    }
    assert contract["stage_10_whole_review_status"] == "not_started"
    assert contract["stage_11_started"] is False


def test_trace_span_and_redacted_structured_log_follow_every_job_revision(
    tmp_path: Path,
) -> None:
    store = _store(tmp_path)
    trace_id = "a1" * 16
    parent_span_id = "b2" * 8
    context = {
        "source_hash": "a" * 64,
        "data_hash": "b" * 64,
        "formula_hash": "c" * 64,
        "parameter_hash": "d" * 64,
        "read_model_hash": "e" * 64,
        "cache_key": "f" * 64,
        "impact_scope": ["cache.portfolio", "metrics.summary"],
        "cache_fallback_used": False,
        "external_network_calls": 0,
    }
    queued = store.enqueue(
        job_type="cache.refresh",
        idempotency_key="observability-chain",
        payload={"mode": "offline"},
        trace_id=trace_id,
        parent_span_id=parent_span_id,
        observability_context=context,
        now=BASE_TIME,
    )["job"]
    claimed = store.claim(
        job_type="cache.refresh",
        worker_id="runtime-worker",
        now=BASE_TIME + timedelta(seconds=1),
    )
    progressed = store.record_progress(
        queued["job_id"],
        worker_id="runtime-worker",
        lease_token=claimed["lease"]["token"],
        expected_revision=claimed["job"]["revision"],
        completed_units=1,
        total_units=3,
        step="cache.dependency_snapshot",
        now=BASE_TIME + timedelta(seconds=3),
    )
    failed = store.fail(
        queued["job_id"],
        worker_id="runtime-worker",
        lease_token=claimed["lease"]["token"],
        expected_revision=progressed["revision"],
        error_code="LOCAL_TIMEOUT",
        error_message=(
            "timeout /Users/private/PFI.db /private/var/folders/secret/PFI.db owner@example.com "
            "token=visible-secret AUD 1,234.56"
        ),
        retryable=False,
        now=BASE_TIME + timedelta(seconds=5),
    )

    projection = store.get_observability(queued["job_id"])
    events = projection["events"]
    logs = projection["logs"]
    assert failed["trace"]["trace_id"] == trace_id
    assert failed["trace"]["span_id"] == events[-1]["trace"]["span_id"]
    assert failed["observability"]["impact_scope"] == [
        "cache.portfolio",
        "metrics.summary",
    ]
    assert failed["observability"]["external_network_calls"] == 0
    assert failed["observability"]["structured_log_count"] == len(events) == len(logs) == 4
    assert [event["job_revision"] for event in events] == [0, 1, 2, 3]
    assert all(event["trace"]["trace_id"] == trace_id for event in events)
    assert events[0]["trace"]["parent_span_id"] == parent_span_id
    assert all(log["trace_id"] == trace_id for log in logs)
    assert all(log["span_id"] == event["trace"]["span_id"] for log, event in zip(logs, events))
    assert [log["previous_log_hash"] for log in logs] == [
        "",
        logs[0]["log_hash"],
        logs[1]["log_hash"],
        logs[2]["log_hash"],
    ]
    serialized = repr(projection)
    for private_value in (
        "/Users/private/PFI.db",
        "/private/var/folders/secret/PFI.db",
        "owner@example.com",
        "visible-secret",
        "1,234.56",
    ):
        assert private_value not in serialized
    assert "<redacted-private-path>" in serialized
    assert "<redacted-email>" in serialized
    assert "<redacted-secret>" in serialized
    assert "<redacted-financial-value>" in serialized

    with sqlite3.connect(store.db_path) as conn:
        for table in (
            "durable_job_trace_contexts",
            "durable_job_spans",
            "durable_job_logs",
        ):
            with pytest.raises(sqlite3.IntegrityError, match="immutable|append-only"):
                conn.execute(f"DELETE FROM {table}")


def test_observability_input_fails_closed_for_invalid_ids_hashes_and_network(
    tmp_path: Path,
) -> None:
    store = _store(tmp_path)
    with pytest.raises(ValueError, match="trace_id"):
        store.enqueue(
            job_type="cache.refresh",
            idempotency_key="invalid-trace",
            trace_id="not-a-trace",
            now=BASE_TIME,
        )
    with pytest.raises(ValueError, match="source_hash"):
        store.enqueue(
            job_type="cache.refresh",
            idempotency_key="invalid-hash",
            observability_context={"source_hash": "not-a-hash"},
            now=BASE_TIME,
        )
    with pytest.raises(ValueError, match="zero external network calls"):
        store.enqueue(
            job_type="cache.refresh",
            idempotency_key="network-not-allowed",
            observability_context={"external_network_calls": 1},
            now=BASE_TIME,
        )
