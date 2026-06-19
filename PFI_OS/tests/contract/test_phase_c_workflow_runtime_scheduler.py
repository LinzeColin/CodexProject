import json
from datetime import datetime, timezone
from pathlib import Path

from pfi_os.application import (
    DataDomain,
    EvidenceRecord,
    JobRecord,
    OperationalStore,
    SourceRecord,
    TaskRecord,
    WORKFLOW_RUNTIME_REFRESH_JOB_TYPE,
    WORKFLOW_RUNTIME_SCHEDULER_SCHEMA,
    build_phase_c_workflow_runtime_scheduler_contract,
    execute_workflow_runtime_refresh_job,
    refresh_workflow_runtime_cache,
    schedule_workflow_runtime_refresh,
)


def test_phase_c_workflow_runtime_scheduler_contract_declares_local_fast_path_and_safety_boundary():
    contract = build_phase_c_workflow_runtime_scheduler_contract()

    assert contract["schema"] == WORKFLOW_RUNTIME_SCHEDULER_SCHEMA
    assert contract["phase"] == "Phase C"
    assert contract["job_type"] == WORKFLOW_RUNTIME_REFRESH_JOB_TYPE
    assert contract["read_model_schema"] == "PFIOSPhaseCWorkflowRuntimeReadModelV1"
    assert contract["target_seconds"] == 60
    assert contract["retry_policy"] == {
        "max_attempts": 3,
        "backoff_seconds": [1, 5, 15],
        "fail_closed": True,
        "retryable_statuses": ["queued", "running", "error"],
    }
    assert contract["writes"]["new_tables"] is False
    assert contract["external_dependencies"] == {
        "provider_fetch_required": False,
        "broker_required": False,
        "llm_required": False,
        "network_required": False,
    }
    assert contract["safety_boundary"]["no_order_execution"] is True
    assert contract["safety_boundary"]["human_review_required"] is True


def test_schedule_workflow_runtime_refresh_is_idempotent_and_writes_queued_job(tmp_path: Path):
    store = _store_with_phase_b_workflows(tmp_path)
    as_of = "2026-06-20T10:00:00+10:00"

    first = schedule_workflow_runtime_refresh(store, as_of=as_of)
    second = schedule_workflow_runtime_refresh(store, as_of=as_of)

    scheduler_jobs = [
        row for row in store.table_rows("job_records") if row["job_type"] == WORKFLOW_RUNTIME_REFRESH_JOB_TYPE
    ]
    scheduler_sources = [
        row for row in store.table_rows("source_records") if row["source_type"] == "phase_c_workflow_runtime_scheduler"
    ]

    assert first["schema"] == "PFIOSPhaseCWorkflowRuntimeSchedulerRunV1"
    assert first["status"] == "queued"
    assert first["queued"] is True
    assert second["job_id"] == first["job_id"]
    assert second["queued"] is False
    assert len(scheduler_jobs) == 1
    assert len(scheduler_sources) == 1
    assert scheduler_jobs[0]["status"] == "queued"
    assert scheduler_jobs[0]["retry_count"] == 0
    metadata = json.loads(scheduler_jobs[0]["metadata_json"])
    assert metadata["idempotency_key"] == first["idempotency_key"]
    assert metadata["safety_boundary"]["no_broker_calls"] is True


def test_refresh_workflow_runtime_cache_completes_within_sixty_second_acceptance_and_records_evidence(
    tmp_path: Path,
):
    store = _store_with_phase_b_workflows(tmp_path)
    now = datetime(2026, 6, 20, 10, 0, tzinfo=timezone.utc)

    report = refresh_workflow_runtime_cache(store, as_of="2026-06-20T10:00:00+10:00", now=now)

    scheduler_job = next(row for row in store.table_rows("job_records") if row["job_id"] == report["job_id"])
    runtime_evidence = next(
        row
        for row in store.table_rows("evidence_records")
        if row["evidence_id"] == report["runtime_ids"]["evidence_id"]
    )
    runtime_task = next(
        row
        for row in store.table_rows("task_records")
        if row["task_id"] == report["runtime_ids"]["task_id"]
    )

    assert report["status"] == "completed"
    assert report["target_seconds"] == 60
    assert report["elapsed_seconds"] <= 60
    assert report["within_target_seconds"] is True
    assert report["fast_path"]["status"] == "Pass"
    assert scheduler_job["status"] == "completed"
    assert scheduler_job["phase"] == "cache_refreshed"
    scheduler_metadata = json.loads(scheduler_job["metadata_json"])
    assert scheduler_metadata["within_target_seconds"] is True
    assert scheduler_metadata["runtime_ids"] == report["runtime_ids"]
    assert runtime_evidence["evidence_class"] == "workflow_runtime_read_model"
    assert runtime_task["owner_workspace"] == "data"
    assert runtime_task["human_review_required"] == 1
    serialized = json.dumps(report, ensure_ascii=False)
    assert "holdings_json" not in serialized
    assert "super-secret-position" not in serialized


def test_execute_workflow_runtime_refresh_job_retries_then_fails_closed(tmp_path: Path):
    store = _store_with_phase_b_workflows(tmp_path)
    scheduled = schedule_workflow_runtime_refresh(store, as_of="2026-06-20T10:00:00+10:00")

    first = execute_workflow_runtime_refresh_job(store, scheduled["job_id"], builder=_failing_builder)
    second = execute_workflow_runtime_refresh_job(store, scheduled["job_id"], builder=_failing_builder)
    third = execute_workflow_runtime_refresh_job(store, scheduled["job_id"], builder=_failing_builder)
    fourth = execute_workflow_runtime_refresh_job(store, scheduled["job_id"], builder=_failing_builder)

    scheduler_job = next(row for row in store.table_rows("job_records") if row["job_id"] == scheduled["job_id"])
    metadata = json.loads(scheduler_job["metadata_json"])

    assert first["status"] == "queued"
    assert first["phase"] == "retry_scheduled"
    assert first["retry_count"] == 1
    assert first["next_retry_after_seconds"] == 1
    assert second["status"] == "queued"
    assert second["retry_count"] == 2
    assert second["next_retry_after_seconds"] == 5
    assert third["status"] == "failed"
    assert third["phase"] == "fail_closed"
    assert third["retry_count"] == 3
    assert third["next_retry_after_seconds"] is None
    assert fourth["status"] == "failed"
    assert fourth["attempt_number"] == 3
    assert fourth["retry_count"] == 3
    assert scheduler_job["status"] == "failed"
    assert scheduler_job["phase"] == "fail_closed"
    assert scheduler_job["retry_count"] == 3
    assert "synthetic builder failure" in scheduler_job["error_message"]
    assert metadata["fail_closed_review_required"] is True
    assert metadata["attempts_remaining"] == 0


def _failing_builder(_store: OperationalStore, _now: datetime | None, _target_seconds: int) -> dict:
    raise RuntimeError("synthetic builder failure")


def _store_with_phase_b_workflows(tmp_path: Path) -> OperationalStore:
    store = OperationalStore(tmp_path / "private" / "operational" / "pfi.sqlite")
    store.initialize()
    _insert_workflow(
        store,
        workspace="strategy_lab",
        domain=DataDomain.PUBLIC_SHARED_CANONICAL,
        source_type="strategy_lab_verification",
        job_type="strategy_lab_verification",
        evidence_class="replay_backtest_result",
    )
    _insert_workflow(
        store,
        workspace="markets",
        domain=DataDomain.PUBLIC_SHARED_CANONICAL,
        source_type="markets_vertical_slice",
        job_type="markets_vertical_slice",
        evidence_class="market_observation",
    )
    _insert_workflow(
        store,
        workspace="research",
        domain=DataDomain.PUBLIC_SHARED_CANONICAL,
        source_type="research_policy_vertical_slice",
        job_type="research_policy_vertical_slice",
        evidence_class="research_policy_evidence",
    )
    _insert_workflow(
        store,
        workspace="portfolio",
        domain=DataDomain.PRIVATE_DERIVED,
        source_type="portfolio_vertical_slice",
        job_type="portfolio_vertical_slice",
        evidence_class="private_portfolio_review",
        holding_snapshot=True,
    )
    return store


def _insert_workflow(
    store: OperationalStore,
    *,
    workspace: str,
    domain: DataDomain,
    source_type: str,
    job_type: str,
    evidence_class: str,
    holding_snapshot: bool = False,
) -> None:
    source_id = f"src-{workspace}"
    evidence_id = f"evidence-{workspace}"
    as_of = "2026-06-20T09:30:00+10:00"
    store.upsert_source(
        SourceRecord(
            source_id=source_id,
            domain=domain,
            source_type=source_type,
            uri=f"operational_store:{source_type}",
            as_of=as_of,
            evidence_class=evidence_class,
            title=f"{workspace} workflow",
            metadata={"workflow_id": f"wf-{workspace}"},
        )
    )
    store.upsert_entity(workspace, entity_type="workflow", display_name=workspace, canonical_symbol=workspace)
    store.record_evidence(
        EvidenceRecord(
            evidence_id=evidence_id,
            source_id=source_id,
            entity_id=workspace,
            as_of=as_of,
            evidence_class=evidence_class,
            summary=f"{workspace} workflow evidence ready.",
            artifact_uri=f"operational_store:{source_type}",
            metadata={"decision": {"human_review_required": True}},
        )
    )
    store.upsert_job(
        JobRecord(
            job_id=f"job-{workspace}",
            source_id=source_id,
            as_of=as_of,
            job_type=job_type,
            status="completed",
            phase="evidence_recorded",
            progress=1.0,
        )
    )
    store.upsert_task(
        TaskRecord(
            task_id=f"task-{workspace}",
            source_id=source_id,
            evidence_id=evidence_id,
            as_of=as_of,
            owner_workspace=workspace,
            action=f"Review {workspace} workflow evidence.",
            status="open",
            priority="P1",
            human_review_required=True,
        )
    )
    if holding_snapshot:
        store.upsert_holding_snapshot(
            snapshot_id="holdingSnapshot-main",
            source_id=source_id,
            evidence_id=evidence_id,
            as_of=as_of,
            portfolio_id="main",
            holdings=[{"symbol": "super-secret-position", "weight": 1.0}],
            domain=DataDomain.PRIVATE_DERIVED,
        )
