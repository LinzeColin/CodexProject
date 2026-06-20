from pathlib import Path

from pfi_os.application import (
    PFI008_PORTFOLIO_ACCEPTANCE_SCHEMA,
    PFI008_PORTFOLIO_UI_READ_MODEL_SCHEMA,
    OperationalStore,
    build_pfi008_portfolio_golden_fixture,
    build_pfi008_portfolio_ui_read_model,
    build_pfi008_reviewed_holdings,
    build_portfolio_workflow,
    record_portfolio_workflow,
    rollback_pfi008_portfolio_records,
    run_pfi008_portfolio_acceptance,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
WEB_ROOT = PROJECT_ROOT / "web"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _portfolio_workflow_from_fixture() -> tuple[dict, dict]:
    fixture = build_pfi008_portfolio_golden_fixture()
    constraints = fixture["optimizer_constraints"]
    workflow = build_portfolio_workflow(
        build_pfi008_reviewed_holdings(fixture),
        source_id=fixture["source_id"],
        as_of=fixture["as_of"],
        portfolio_id=fixture["portfolio_id"],
        evidence_class="pfi008_private_portfolio_review",
        max_single_weight=float(constraints["max_single_weight"]),
        max_top3_weight=float(constraints["max_top3_weight"]),
    )
    return fixture, workflow


def test_pfi008_acceptance_runs_import_reconciliation_risk_decision_and_rollback_chain():
    payload = run_pfi008_portfolio_acceptance()

    assert payload["schema"] == PFI008_PORTFOLIO_ACCEPTANCE_SCHEMA
    assert payload["status"] == "Pass"
    assert payload["summary"]["fail"] == 0
    assert payload["summary"]["pass"] >= 16
    check_names = {row["name"] for row in payload["checks"]}
    for required in {
        "DataChain:SyntheticBrokerImport",
        "Golden:CorporateActionFxCash",
        "Domain:PortfolioWorkflow",
        "Reconciliation:BrokerToSnapshot",
        "API:UIReadModel",
        "UI:ChineseJourney",
        "OptimizerConstraints:ReviewOnly",
        "DecisionProposal:HumanReview",
        "TasksEvidence:Source",
        "TasksEvidence:Evidence",
        "TasksEvidence:Job",
        "TasksEvidence:ReviewTask",
        "TasksEvidence:HoldingSnapshot",
        "Safety:NoExecution",
        "GoldenMetrics:StableWorkflow",
        "RollbackProof",
    }:
        assert required in check_names
    assert payload["ui_read_model"]["schema"] == PFI008_PORTFOLIO_UI_READ_MODEL_SCHEMA
    assert payload["rollback_proof"]["status"] == "Pass"
    assert payload["safety_boundary"] == {
        "research_only": True,
        "synthetic_fixture_only": True,
        "provider_fetch_required": False,
        "broker_required": False,
        "llm_required": False,
        "no_real_broker_connection": True,
        "no_live_trading": True,
        "no_broker_calls": True,
        "no_order_execution": True,
        "no_holding_mutation": True,
        "human_review_required": True,
    }


def test_pfi008_golden_metrics_are_deterministic_and_review_only():
    first = run_pfi008_portfolio_acceptance()
    second = run_pfi008_portfolio_acceptance()

    first_metrics = first["golden_metrics"]
    second_metrics = second["golden_metrics"]
    assert first_metrics["workflow_id"] == second_metrics["workflow_id"]
    assert first_metrics["snapshot_checksum"] == second_metrics["snapshot_checksum"]
    assert first_metrics["import_record_count"] == 5
    assert first_metrics["broker_count"] == 3
    assert first_metrics["corporate_action_adjusted_count"] == 1
    assert first_metrics["fx_converted_count"] == 1
    assert first_metrics["cash_balance_usd"] == 500.0
    assert first_metrics["holding_count"] == 5
    assert first_metrics["total_position_value_usd"] == 9500.0
    assert first_metrics["target_weight_change"] == 0.0
    assert first_metrics["constraint_violation_count"] >= 2


def test_pfi008_ui_read_model_exposes_portfolio_journey_reconciliation_and_decision():
    fixture, workflow = _portfolio_workflow_from_fixture()
    ids = {
        "source_id": "src-pfi008",
        "evidence_id": "evidence-pfi008",
        "job_id": "job-pfi008",
        "task_id": "task-pfi008",
        "snapshot_id": "holdingSnapshot-pfi008",
    }

    ui = build_pfi008_portfolio_ui_read_model(workflow, fixture, ids)

    assert ui["schema"] == PFI008_PORTFOLIO_UI_READ_MODEL_SCHEMA
    assert ui["workspace"] == "portfolio"
    assert ui["workspace_label"] == "持仓"
    assert ui["primary_feature_view"] == "portfolio_slice"
    assert set(ui["secondary_feature_views"]) == {"portfolio_reconciliation", "portfolio_risk", "portfolio_decision"}
    assert ui["import_reconciliation"]["status"] == "Pass"
    assert ui["golden_inputs"]["synthetic_broker_imports"] == 5
    assert ui["golden_inputs"]["corporate_action_adjusted_count"] == 1
    assert ui["golden_inputs"]["fx_converted_count"] == 1
    assert ui["golden_inputs"]["cash_balance_usd"] == 500.0
    assert ui["decision_proposal"]["order_intent_created"] is False
    assert ui["decision_proposal"]["target_weight_change"] == 0.0
    assert ui["decision_proposal"]["human_review_required"] is True
    assert ui["decision_proposal"]["constraint_violation_count"] >= 2
    assert "打开一级入口：持仓" in ui["journey"]
    assert any("合成券商" in step for step in ui["journey"])
    assert ui["safety_boundary"]["no_real_broker_connection"] is True
    assert ui["safety_boundary"]["no_order_execution"] is True


def test_pfi008_rollback_removes_temporary_source_evidence_job_task_and_snapshot_records(tmp_path: Path):
    fixture, workflow = _portfolio_workflow_from_fixture()
    store = OperationalStore(tmp_path / "private" / "operational" / "pfi.sqlite")
    ids = record_portfolio_workflow(store, workflow, artifact_uri="operational_store:pfi008_portfolio_acceptance")

    proof = rollback_pfi008_portfolio_records(store, ids)

    assert proof["schema"] == "PFI008PortfolioRollbackProofV1"
    assert proof["status"] == "Pass"
    assert proof["residue_counts"] == {
        "source_records": 0,
        "evidence_records": 0,
        "job_records": 0,
        "task_records": 0,
        "holding_snapshots": 0,
    }
    assert proof["deleted_counts"]["source_records"] == 1
    assert proof["deleted_counts"]["evidence_records"] == 1
    assert proof["deleted_counts"]["job_records"] == 1
    assert proof["deleted_counts"]["task_records"] == 1
    assert proof["deleted_counts"]["holding_snapshots"] == 1


def test_pfi008_web_shell_exposes_same_shell_portfolio_controls():
    js = _text(WEB_ROOT / "app" / "shell.js")

    for view in ["portfolio_slice", "portfolio_reconciliation", "portfolio_risk", "portfolio_decision"]:
        assert f'view: "{view}"' in js
    for label in ["持仓垂直切片", "导入对账", "风险约束", "决策提案"]:
        assert label in js
    for text in ["合成券商", "公司行动", "汇率换算", "现金固定样本", "不连接真实券商", "不提交券商"]:
        assert text in js
    assert '持仓垂直切片: { view: "portfolio_slice"' in js
    assert '导入对账: { view: "portfolio_reconciliation"' in js
    assert '风险约束: { view: "portfolio_risk"' in js
    assert '决策提案: { view: "portfolio_decision"' in js
    assert "window.open" not in js
    assert "location.reload" not in js
    assert "window.location.href" not in js


def test_pfi008_script_and_target_gate_are_wired_without_heavy_smoke():
    script = _text(PROJECT_ROOT / "scripts" / "pfi008PortfolioAcceptance.sh")
    gate = _text(PROJECT_ROOT / "scripts" / "pfiGate.sh")
    gitignore = _text(PROJECT_ROOT / ".gitignore")

    assert "PFI008PortfolioAcceptance" in script
    assert "run_pfi008_portfolio_acceptance" in script
    assert "tests/contract/test_pfi008_portfolio_vertical_acceptance.py" in gate
    assert "data/systemAudit/PFI008PortfolioAcceptance*.json" in gitignore
    assert "finalAcceptanceCheck" not in script
    assert "ciSmoke" not in script
