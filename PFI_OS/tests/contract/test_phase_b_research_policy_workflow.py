from pathlib import Path

from pfi_os.application import (
    OperationalStore,
    RESEARCH_POLICY_WORKFLOW_SCHEMA,
    build_phase_b_research_policy_contract,
    build_research_policy_workflow,
    record_research_policy_workflow,
)
from pfi_os.policy import create_policy_opportunity


DECISION_FIELDS = {
    "decision_id",
    "entity_id",
    "action",
    "horizon",
    "target_weight_change",
    "status",
    "confidence",
    "evidence_class",
    "as_of",
    "thesis",
    "catalysts",
    "counter_evidence",
    "invalidation_conditions",
    "risks",
    "portfolio_effect",
    "model_versions",
    "source_ids",
    "human_review_required",
}


CARD_FIELDS = {"card_id", "title", "status", "summary", "source_ids", "as_of", "evidence_class", "review_required"}


def _policy_opportunities():
    return [
        create_policy_opportunity(
            published_date="2026-06-18",
            title="Official AI compute grant",
            source_name="Department of Industry",
            source_type="Government",
            source_url="https://example.gov/ai-compute-grant",
            jurisdiction="AU",
            policy_level="National",
            opportunity_type="IndustrySupport",
            sectors="AI, Semiconductor",
            affected_entities="AI infrastructure suppliers",
            impact_summary="Official grant may affect AI compute supply-chain demand.",
            required_action="Review eligibility and deadline.",
            authority_score=95,
            relevance_score=85,
            urgency_score=80,
            feasibility_score=70,
            review_status="Reviewed",
        ),
        create_policy_opportunity(
            published_date="2026-06-17",
            title="News summary of proposed tax setting",
            source_name="News Desk",
            source_type="News",
            source_url="https://example.com/tax-summary",
            opportunity_type="Tax",
            sectors="Software",
            affected_entities="Software companies",
            authority_score=70,
            relevance_score=80,
            urgency_score=60,
            feasibility_score=50,
            review_status="Reviewed",
        ),
    ]


def _report_decision_payload():
    return {
        "schema": "PFIOSReportDecisionSupportIndexV1",
        "record_count": 1,
        "records": [
            {
                "run": "RunMetadata_20260619",
                "date_folder": "2026-06-19",
                "strategy_id": "ma_crossover",
                "symbol": "AAPL",
                "market": "US",
                "report_readiness": "NeedsMoreEvidence",
                "critical_missing_evidence": "数据质量状态; 多源交叉校验; walk-forward 验证",
                "metadata_path": "/tmp/reports/RunMetadata_20260619.json",
                "linked_report_path": "/tmp/reports/BacktestReport_20260619.docx",
            }
        ],
    }


def test_phase_b_research_policy_contract_declares_authority_gap_and_safety_constraints():
    contract = build_phase_b_research_policy_contract()

    assert contract["schema"] == "PFIOSPhaseBResearchPolicyContractV1"
    assert contract["workflow_schema"] == RESEARCH_POLICY_WORKFLOW_SCHEMA
    assert contract["workspace"] == "research"
    assert contract["subworkspace"] == "policy"
    assert "build_policy_radar" in contract["required_steps"]
    assert "build_report_evidence_gap_tasks" in contract["required_steps"]
    assert contract["required_fact_fields"] == ["source_id", "as_of", "evidence_class"]
    assert set(contract["required_card_fields"]) == CARD_FIELDS
    assert set(contract["decision_contract_fields"]) == DECISION_FIELDS
    assert contract["non_regression_constraints"] == {
        "research_policy_vertical_slice": True,
        "policy_authority_visible": True,
        "research_gap_tasks_visible": True,
        "no_government_portal_action": True,
        "no_live_trading": True,
        "human_review_required": True,
        "llm_required": False,
    }


def test_research_policy_workflow_builds_policy_radar_gap_tasks_cards_and_decision(tmp_path: Path):
    payload = build_research_policy_workflow(
        source_id="src-research-policy-2026-06-19",
        as_of="2026-06-19",
        opportunities=_policy_opportunities(),
        report_decision_payload=_report_decision_payload(),
        project_root=tmp_path,
        report_root=tmp_path / "reports",
    )

    assert payload["schema"] == RESEARCH_POLICY_WORKFLOW_SCHEMA
    assert payload["workspace"] == "research"
    assert payload["subworkspace"] == "policy"
    assert payload["source_id"] == "src-research-policy-2026-06-19"
    assert payload["evidence_class"] == "research_policy_evidence"
    assert payload["model_versions"] == ["DisabledProvider"]
    assert payload["policy_radar"]["schema"] == "PFIOSPolicyIntelligenceRadarV1"
    assert payload["policy_radar"]["summary"]["total_records"] == 2
    assert payload["policy_radar"]["summary"]["actionable_count"] == 1
    assert payload["policy_radar"]["runtime_summary"]["authoritative_source_records"] == 1
    assert payload["report_gap_tasks"]["schema"] == "PFIOSReportEvidenceGapTasksV1"
    assert payload["report_gap_tasks"]["task_count"] >= 3
    assert {row["evidence_gap"] for row in payload["report_gap_tasks"]["gap_counts"]} >= {"DataQuality", "CrossSourceValidation", "WalkForwardValidation"}
    assert {card["card_id"] for card in payload["cards"]} == {"policy_authority", "policy_opportunities", "research_evidence_gaps"}
    for card in payload["cards"]:
        assert set(card) == CARD_FIELDS
        assert card["source_ids"] == ["src-research-policy-2026-06-19"]
    assert set(payload["decision"]) == DECISION_FIELDS
    assert payload["decision"]["action"] == "review_research_policy_evidence"
    assert payload["decision"]["target_weight_change"] == 0.0
    assert payload["decision"]["human_review_required"] is True
    assert payload["decision"]["counter_evidence"]
    assert payload["decision"]["invalidation_conditions"]
    assert payload["decision"]["portfolio_effect"]["no_private_holdings_used"] is True
    assert payload["safety_boundary"] == {
        "research_only": True,
        "no_live_trading": True,
        "no_broker_calls": True,
        "no_order_execution": True,
        "no_government_portal_action": True,
        "no_legal_or_tax_advice": True,
        "human_review_required": True,
    }


def test_research_policy_workflow_is_stable_for_identical_inputs(tmp_path: Path):
    opportunities = _policy_opportunities()
    report_payload = _report_decision_payload()
    kwargs = {
        "source_id": "src-research-policy-stable",
        "as_of": "2026-06-19",
        "opportunities": opportunities,
        "report_decision_payload": report_payload,
        "project_root": tmp_path,
        "report_root": tmp_path / "reports",
    }

    first = build_research_policy_workflow(**kwargs)
    second = build_research_policy_workflow(**kwargs)

    assert first["workflow_id"] == second["workflow_id"]
    assert first["cards"] == second["cards"]
    assert first["report_gap_tasks"]["gap_counts"] == second["report_gap_tasks"]["gap_counts"]


def test_research_policy_workflow_records_operational_store_evidence_job_and_review_task(tmp_path: Path):
    payload = build_research_policy_workflow(
        source_id="src-research-policy-store",
        as_of="2026-06-19",
        opportunities=_policy_opportunities(),
        report_decision_payload=_report_decision_payload(),
        project_root=tmp_path,
        report_root=tmp_path / "reports",
    )
    store = OperationalStore(tmp_path / "private" / "operational" / "pfi.sqlite")

    ids = record_research_policy_workflow(store, payload)

    sources = store.table_rows("source_records")
    evidence = store.table_rows("evidence_records")
    jobs = store.table_rows("job_records")
    tasks = store.table_rows("task_records")

    assert ids == {
        "source_id": "src-research-policy-store",
        "evidence_id": f"evidence-{payload['workflow_id']}",
        "job_id": f"job-{payload['workflow_id']}",
        "task_id": f"task-{payload['workflow_id']}",
    }
    assert sources[0]["source_type"] == "research_policy_vertical_slice"
    assert sources[0]["evidence_class"] == "research_policy_evidence"
    assert evidence[0]["entity_id"] == "research_policy"
    assert "Research + Policy workflow" in evidence[0]["summary"]
    assert jobs[0]["status"] == "completed"
    assert jobs[0]["progress"] == 1.0
    assert tasks[0]["owner_workspace"] == "research"
    assert tasks[0]["human_review_required"] == 1
