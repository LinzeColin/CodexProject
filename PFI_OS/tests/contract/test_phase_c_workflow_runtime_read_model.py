import json
from datetime import datetime, timezone
from pathlib import Path

from pfi_os.application import (
    DataDomain,
    DurableJobStore,
    EvidenceRecord,
    JobRecord,
    OperationalStore,
    PFI003_SUPERVISOR_RUNTIME_READ_MODEL_SCHEMA,
    SourceRecord,
    TaskRecord,
    WORKFLOW_RUNTIME_READ_MODEL_SCHEMA,
    build_homepage_summary,
    build_phase_c_workflow_runtime_contract,
    build_workflow_runtime_read_model,
    record_workflow_runtime_read_model,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
WEB_ROOT = PROJECT_ROOT / "web"

CARD_FIELDS = {
    "workspace",
    "title",
    "status",
    "source_type",
    "evidence_class",
    "data_domain",
    "source_id",
    "evidence_id",
    "job_id",
    "task_count",
    "open_task_count",
    "latest_as_of",
    "review_required",
    "freshness",
}


def test_phase_c_workflow_runtime_contract_declares_fast_path_retry_and_safety_constraints():
    contract = build_phase_c_workflow_runtime_contract()

    assert contract["schema"] == "PFIOSPhaseCWorkflowRuntimeContractV1"
    assert contract["read_model_schema"] == WORKFLOW_RUNTIME_READ_MODEL_SCHEMA
    assert contract["phase"] == "Phase C"
    assert contract["required_workflows"] == ["strategy", "market", "research", "portfolio"]
    assert contract["fast_path"]["target_seconds"] == 60
    assert contract["fast_path"]["provider_fetch_required"] is False
    assert contract["fast_path"]["broker_required"] is False
    assert contract["fast_path"]["llm_required"] is False
    assert contract["fast_path"]["retry_policy"]["max_attempts"] == 3
    assert contract["fast_path"]["retry_policy"]["backoff_seconds"] == [1, 5, 15]
    assert "supervisor_runtime" in contract["required_runtime_sections"]
    assert set(contract["required_card_fields"]) == CARD_FIELDS
    assert contract["non_regression_constraints"] == {
        "phase_b_workflows_promoted": True,
        "web_shell_cached_read_model": True,
        "sixty_second_fast_path_contract": True,
        "retry_backoff_visible": True,
        "pfi003_supervisor_runtime_visible": True,
        "private_holdings_not_exposed": True,
        "no_live_trading": True,
        "no_broker_calls": True,
        "no_order_execution": True,
        "human_review_required": True,
    }


def test_workflow_runtime_read_model_promotes_phase_b_records_without_private_holdings_leak(tmp_path: Path):
    store = _store_with_phase_b_workflows(tmp_path)

    payload = build_workflow_runtime_read_model(store, now=datetime(2026, 6, 20, 10, 0, tzinfo=timezone.utc))

    assert payload["schema"] == WORKFLOW_RUNTIME_READ_MODEL_SCHEMA
    assert payload["phase"] == "Phase C"
    assert payload["fast_path"]["status"] == "Pass"
    assert payload["fast_path"]["target_seconds"] == 60
    assert payload["fast_path"]["estimated_seconds"] <= 60
    assert payload["fast_path"]["ready_workflow_count"] == 4
    assert payload["fast_path"]["provider_fetch_required"] is False
    assert payload["fast_path"]["broker_required"] is False
    assert payload["fast_path"]["llm_required"] is False
    assert {card["workspace"] for card in payload["workflow_cards"]} == {"strategy", "market", "research", "portfolio"}
    for card in payload["workflow_cards"]:
        assert set(card) >= CARD_FIELDS
        assert card["status"] == "Ready"
        assert card["source_id"]
        assert card["evidence_id"]
        assert card["job_id"]
        assert card["review_required"] is True
        assert card["freshness"]["status"] in {"Fresh", "Delayed"}
    portfolio = next(card for card in payload["workflow_cards"] if card["workspace"] == "portfolio")
    assert portfolio["data_domain"] == "PRIVATE_DERIVED"
    assert portfolio["holding_snapshot_count"] == 1
    assert len(payload["background_jobs"]) == 4
    assert len(payload["task_center_rows"]) >= 4
    assert payload["supervisor_runtime"]["schema"] == PFI003_SUPERVISOR_RUNTIME_READ_MODEL_SCHEMA
    assert payload["supervisor_runtime"]["web_shell_visible"] is True
    assert payload["retry_policy"]["fail_closed"] is True
    assert payload["safety_boundary"]["no_order_execution"] is True
    assert payload["safety_boundary"]["private_holdings_not_exposed"] is True
    serialized = json.dumps(payload, ensure_ascii=False)
    assert "holdings_json" not in serialized
    assert "super-secret-position" not in serialized


def test_workflow_runtime_read_model_surfaces_pfi003_supervisor_jobs(tmp_path: Path):
    store = _store_with_phase_b_workflows(tmp_path)
    supervisor = DurableJobStore(store)
    queued = supervisor.enqueue(
        job_type="pfi003_supervisor_network_recovery",
        idempotency_key="network-recovery-1",
        max_attempts=3,
        now=datetime(2026, 6, 20, 10, 0, tzinfo=timezone.utc),
    )
    claimed = supervisor.claim(
        job_type="pfi003_supervisor_network_recovery",
        worker_id="worker-a",
        lease_seconds=30,
        now=datetime(2026, 6, 20, 10, 0, 1, tzinfo=timezone.utc),
    )
    supervisor.fail_or_retry(
        claimed["job_id"],
        worker_id="worker-a",
        error_message="simulated network source unavailable",
        now=datetime(2026, 6, 20, 10, 0, 2, tzinfo=timezone.utc),
    )

    payload = build_workflow_runtime_read_model(store, now=datetime(2026, 6, 20, 10, 0, 3, tzinfo=timezone.utc))
    supervisor_runtime = payload["supervisor_runtime"]
    task_rows = payload["task_center_rows"]

    assert queued["status"] == "queued"
    assert supervisor_runtime["schema"] == PFI003_SUPERVISOR_RUNTIME_READ_MODEL_SCHEMA
    assert supervisor_runtime["status"] == "Running"
    assert supervisor_runtime["total_job_count"] == 1
    assert supervisor_runtime["active_job_count"] == 1
    assert supervisor_runtime["retrying_job_count"] == 1
    assert supervisor_runtime["latest_job_id"] == claimed["job_id"]
    assert supervisor_runtime["latest_event"]["action"] == "fail_or_retry"
    assert any(row["object"] == "PFI-003 监督器" for row in task_rows)
    assert any(row["job_type"] == "pfi003_supervisor_network_recovery" and row["supervisor_managed"] for row in payload["background_jobs"])
    assert supervisor_runtime["safety_boundary"]["no_order_execution"] is True


def test_workflow_runtime_missing_phase_b_records_review_fails_closed(tmp_path: Path):
    store = OperationalStore(tmp_path / "private" / "operational" / "pfi.sqlite")
    store.initialize()
    _insert_workflow(
        store,
        workspace="market",
        domain=DataDomain.PUBLIC_SHARED_CANONICAL,
        source_type="markets_vertical_slice",
        job_type="markets_vertical_slice",
        evidence_class="market_observation",
    )

    payload = build_workflow_runtime_read_model(store, now=datetime(2026, 6, 20, 10, 0, tzinfo=timezone.utc))

    assert payload["fast_path"]["status"] == "Review"
    assert payload["fast_path"]["ready_workflow_count"] == 1
    assert payload["fast_path"]["blocked_workflow_count"] == 3
    assert {row["message"] for row in payload["missing_data_log"]} >= {
        "Strategy Lab workflow evidence is missing.",
        "Research + Policy workflow evidence is missing.",
        "Portfolio workflow evidence is missing.",
    }


def test_homepage_summary_carries_phase_c_workflow_runtime_read_model(tmp_path: Path):
    store = _store_with_phase_b_workflows(tmp_path)

    summary = build_homepage_summary(store, now=datetime(2026, 6, 20, 10, 0, tzinfo=timezone.utc))

    assert summary["schema"] == "PFIOSHomeSummaryV1"
    assert summary["workflow_runtime"]["schema"] == WORKFLOW_RUNTIME_READ_MODEL_SCHEMA
    assert summary["workflow_runtime"]["fast_path"]["status"] == "Pass"
    assert {card["workspace"] for card in summary["workflow_runtime"]["workflow_cards"]} == {"strategy", "market", "research", "portfolio"}


def test_record_workflow_runtime_read_model_writes_operational_evidence_job_and_review_task(tmp_path: Path):
    store = _store_with_phase_b_workflows(tmp_path)
    payload = build_workflow_runtime_read_model(store, now=datetime(2026, 6, 20, 10, 0, tzinfo=timezone.utc))

    ids = record_workflow_runtime_read_model(store, payload, source_id="src-phase-c-runtime", as_of="2026-06-20T10:00:00+10:00")

    sources = [row for row in store.table_rows("source_records") if row["source_id"] == "src-phase-c-runtime"]
    evidence = [row for row in store.table_rows("evidence_records") if row["evidence_id"] == ids["evidence_id"]]
    jobs = [row for row in store.table_rows("job_records") if row["job_id"] == ids["job_id"]]
    tasks = [row for row in store.table_rows("task_records") if row["task_id"] == ids["task_id"]]

    assert ids["source_id"] == "src-phase-c-runtime"
    assert sources[0]["source_type"] == "phase_c_workflow_runtime_read_model"
    assert sources[0]["domain"] == "PRIVATE_DERIVED"
    assert evidence[0]["evidence_class"] == "workflow_runtime_read_model"
    assert "fast_path=Pass" in evidence[0]["summary"]
    assert jobs[0]["status"] == "completed"
    assert tasks[0]["owner_workspace"] == "data"
    assert tasks[0]["human_review_required"] == 1


def test_web_shell_static_assets_accept_phase_c_workflow_runtime_summary():
    html = (WEB_ROOT / "index.html").read_text(encoding="utf-8")
    js = (WEB_ROOT / "app" / "shell.js").read_text(encoding="utf-8")

    assert "PFIOSPhaseCWorkflowRuntimeReadModelV1" in html
    assert "workflow_runtime" in html
    assert "applyWorkflowRuntime" in js
    assert "快速路径" in js
    assert "target_seconds" in js
    assert "estimated_seconds" in js


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
