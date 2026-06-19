import json
from pathlib import Path

import pandas as pd

from pfi_os.application import (
    PORTFOLIO_WORKFLOW_SCHEMA,
    OperationalStore,
    build_phase_b_portfolio_contract,
    build_portfolio_workflow,
    record_portfolio_workflow,
)


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


CARD_FIELDS = {"card_id", "title", "status", "summary", "source_ids", "as_of", "evidence_class", "review_required", "data_domain"}


def _holdings() -> pd.DataFrame:
    updated_at = pd.Timestamp.today(tz="UTC").isoformat()
    rows = [
        ("AAPL", "Apple", "US", 2100.0, "手动录入"),
        ("MSFT", "Microsoft", "US", 2000.0, "手动录入"),
        ("510300", "CSI 300 ETF", "CN", 1900.0, "量化回测系统导入"),
        ("GLD", "Gold ETF", "US", 1900.0, "量化回测系统导入"),
        ("TLT", "Treasury ETF", "US", 2100.0, "量化回测系统导入"),
    ]
    return pd.DataFrame(
        [
            {
                "source_system": source_system,
                "source_file": f"{symbol}.csv",
                "symbol": symbol,
                "name": name,
                "market": market,
                "quantity": 10.0,
                "cost_basis": value * 0.9,
                "position_value": value,
                "unrealized_pnl": value * 0.1,
                "weight": 0.0,
                "updated_at": updated_at,
                "source_modified_time": updated_at,
            }
            for symbol, name, market, value, source_system in rows
        ]
    )


def test_phase_b_portfolio_contract_declares_private_boundary_snapshot_and_safety_constraints():
    contract = build_phase_b_portfolio_contract()

    assert contract["schema"] == "PFIOSPhaseBPortfolioContractV1"
    assert contract["workflow_schema"] == PORTFOLIO_WORKFLOW_SCHEMA
    assert contract["workspace"] == "portfolio"
    assert "canonicalize_holding_snapshot" in contract["required_steps"]
    assert "publish_evidence_snapshot_and_review_task" in contract["required_steps"]
    assert contract["required_fact_fields"] == ["source_id", "as_of", "evidence_class"]
    assert set(contract["required_card_fields"]) == CARD_FIELDS
    assert set(contract["decision_contract_fields"]) == DECISION_FIELDS
    assert contract["non_regression_constraints"] == {
        "portfolio_vertical_slice": True,
        "private_holdings_stay_outside_public_git": True,
        "holding_snapshot_operational_store": True,
        "exposure_and_concentration_visible": True,
        "no_live_trading": True,
        "no_broker_calls": True,
        "no_order_execution": True,
        "no_holding_mutation": True,
        "human_review_required": True,
        "llm_required": False,
    }


def test_portfolio_workflow_builds_private_snapshot_cards_risk_review_and_decision():
    payload = build_portfolio_workflow(
        _holdings(),
        source_id="src-portfolio-2026-06-19",
        as_of="2026-06-19T16:00:00+10:00",
        portfolio_id="core",
    )

    assert payload["schema"] == PORTFOLIO_WORKFLOW_SCHEMA
    assert payload["workspace"] == "portfolio"
    assert payload["source_id"] == "src-portfolio-2026-06-19"
    assert payload["portfolio_id"] == "core"
    assert payload["evidence_class"] == "private_portfolio_review"
    assert payload["data_domain"] == "PRIVATE_DERIVED"
    assert payload["model_versions"] == ["DisabledProvider"]
    assert payload["holdings_snapshot"]["data_domain"] == "PRIVATE_DERIVED"
    assert payload["holdings_snapshot"]["public_git_allowed"] is False
    assert payload["holdings_snapshot"]["holding_count"] == 5
    assert len(payload["holdings_snapshot"]["holdings"]) == 5
    assert payload["portfolio_summary"]["holding_count"] == 5
    assert round(float(payload["portfolio_summary"]["total_abs_position_value"]), 2) == 10000.0
    assert payload["portfolio_summary"]["max_single_weight"] < 0.35
    assert payload["portfolio_summary"]["top3_weight"] < 0.65
    assert {card["card_id"] for card in payload["cards"]} == {"portfolio_holdings", "portfolio_exposure", "portfolio_risk_review"}
    for card in payload["cards"]:
        assert set(card) == CARD_FIELDS
        assert card["source_ids"] == ["src-portfolio-2026-06-19"]
        assert card["data_domain"] == "PRIVATE_DERIVED"
    assert set(payload["decision"]) == DECISION_FIELDS
    assert payload["decision"]["action"] == "review_portfolio_risk"
    assert payload["decision"]["target_weight_change"] == 0.0
    assert payload["decision"]["human_review_required"] is True
    assert payload["decision"]["counter_evidence"]
    assert payload["decision"]["invalidation_conditions"]
    assert payload["decision"]["portfolio_effect"]["private_holdings_used"] is True
    assert payload["decision"]["portfolio_effect"]["data_domain"] == "PRIVATE_DERIVED"
    assert payload["safety_boundary"] == {
        "research_only": True,
        "private_data_not_for_public_git": True,
        "no_live_trading": True,
        "no_broker_calls": True,
        "no_order_execution": True,
        "no_holding_mutation": True,
        "human_review_required": True,
    }


def test_portfolio_workflow_is_stable_for_identical_inputs():
    holdings = _holdings()
    kwargs = {
        "source_id": "src-portfolio-stable",
        "as_of": "2026-06-19T16:00:00+10:00",
        "portfolio_id": "core",
    }

    first = build_portfolio_workflow(holdings, **kwargs)
    second = build_portfolio_workflow(holdings, **kwargs)

    assert first["workflow_id"] == second["workflow_id"]
    assert first["holdings_snapshot"]["checksum"] == second["holdings_snapshot"]["checksum"]
    assert first["cards"] == second["cards"]


def test_portfolio_workflow_blocks_empty_holdings_without_creating_order_intent():
    payload = build_portfolio_workflow(
        pd.DataFrame(),
        source_id="src-portfolio-empty",
        as_of="2026-06-19T16:00:00+10:00",
        portfolio_id="core",
    )

    assert payload["status"] == "Blocked"
    assert payload["holdings_snapshot"]["holding_count"] == 0
    assert payload["risk_review"]["status"] == "Blocked"
    assert payload["decision"]["target_weight_change"] == 0.0
    assert payload["missing_data_log"]
    assert payload["safety_boundary"]["no_order_execution"] is True


def test_portfolio_workflow_records_operational_store_evidence_job_review_task_and_snapshot(tmp_path: Path):
    payload = build_portfolio_workflow(
        _holdings(),
        source_id="src-portfolio-store",
        as_of="2026-06-19T16:00:00+10:00",
        portfolio_id="core",
    )
    store = OperationalStore(tmp_path / "private" / "operational" / "pfi.sqlite")

    ids = record_portfolio_workflow(store, payload)

    sources = store.table_rows("source_records")
    evidence = store.table_rows("evidence_records")
    jobs = store.table_rows("job_records")
    tasks = store.table_rows("task_records")
    snapshots = store.table_rows("holding_snapshots")

    assert ids == {
        "source_id": "src-portfolio-store",
        "evidence_id": f"evidence-{payload['workflow_id']}",
        "job_id": f"job-{payload['workflow_id']}",
        "task_id": f"task-{payload['workflow_id']}",
        "snapshot_id": payload["holdings_snapshot"]["snapshot_id"],
    }
    assert sources[0]["source_type"] == "portfolio_vertical_slice"
    assert sources[0]["domain"] == "PRIVATE_DERIVED"
    assert sources[0]["evidence_class"] == "private_portfolio_review"
    assert evidence[0]["entity_id"] == "core"
    assert "Portfolio workflow for core" in evidence[0]["summary"]
    assert jobs[0]["status"] == "completed"
    assert jobs[0]["progress"] == 1.0
    assert tasks[0]["owner_workspace"] == "portfolio"
    assert tasks[0]["human_review_required"] == 1
    assert snapshots[0]["portfolio_id"] == "core"
    assert snapshots[0]["data_domain"] == "PRIVATE_DERIVED"
    assert len(json.loads(snapshots[0]["holdings_json"])) == 5
