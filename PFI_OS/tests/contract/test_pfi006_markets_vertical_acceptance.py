from pathlib import Path

from pfi_os.application import (
    PFI006_MARKETS_ACCEPTANCE_SCHEMA,
    PFI006_MARKETS_UI_READ_MODEL_SCHEMA,
    OperationalStore,
    build_pfi006_markets_golden_fixture,
    build_pfi006_markets_ui_read_model,
    build_markets_workflow,
    record_markets_workflow,
    rollback_pfi006_markets_records,
    run_pfi006_markets_acceptance,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
WEB_ROOT = PROJECT_ROOT / "web"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_pfi006_acceptance_runs_data_domain_api_ui_task_evidence_and_rollback_chain():
    payload = run_pfi006_markets_acceptance()

    assert payload["schema"] == PFI006_MARKETS_ACCEPTANCE_SCHEMA
    assert payload["status"] == "Pass"
    assert payload["summary"]["fail"] == 0
    assert payload["summary"]["pass"] >= 12
    check_names = {row["name"] for row in payload["checks"]}
    for required in {
        "DataChain:MarketEventLog",
        "Domain:HotspotSentimentDecision",
        "API:UIReadModel",
        "UI:ChineseJourney",
        "TasksEvidence:Source",
        "TasksEvidence:Evidence",
        "TasksEvidence:Job",
        "TasksEvidence:ReviewTask",
        "PortfolioOverlay:NoPrivateHoldings",
        "AlertSavedView:Present",
        "GoldenMetrics:StableWorkflow",
        "RollbackProof",
        "Safety:NoExecution",
    }:
        assert required in check_names
    assert payload["ui_read_model"]["schema"] == PFI006_MARKETS_UI_READ_MODEL_SCHEMA
    assert payload["rollback_proof"]["status"] == "Pass"
    assert payload["safety_boundary"] == {
        "research_only": True,
        "provider_fetch_required": False,
        "broker_required": False,
        "llm_required": False,
        "no_live_trading": True,
        "no_broker_calls": True,
        "no_order_execution": True,
        "no_private_holdings_used": True,
        "human_review_required": True,
    }


def test_pfi006_golden_metrics_are_deterministic_and_review_only():
    first = run_pfi006_markets_acceptance()
    second = run_pfi006_markets_acceptance()

    first_metrics = first["golden_metrics"]
    second_metrics = second["golden_metrics"]
    assert first_metrics["workflow_id"] == second_metrics["workflow_id"]
    assert first_metrics["checksum"] == second_metrics["checksum"]
    assert first_metrics["event_count"] == 90
    assert first_metrics["observed_symbol_count"] == 4
    assert first_metrics["target_weight_change"] == 0.0
    assert first_metrics["alert_count"] >= 2
    assert first_metrics["saved_view_count"] >= 2
    assert 0.0 <= first_metrics["confidence"] <= 0.85


def test_pfi006_ui_read_model_exposes_market_journey_overlay_alerts_and_saved_views():
    fixture = build_pfi006_markets_golden_fixture()
    workflow = build_markets_workflow(
        fixture["price_frames"],
        fixture["instruments"],
        source_id=fixture["source_id"],
        as_of=fixture["as_of"],
        data_source="PFI006GoldenFixture",
        market=fixture["market"],
        interval=fixture["interval"],
        max_snapshots=12,
    )
    ids = {
        "source_id": "src-pfi006",
        "evidence_id": "evidence-pfi006",
        "job_id": "job-pfi006",
        "task_id": "task-pfi006",
    }

    ui = build_pfi006_markets_ui_read_model(workflow, ids)

    assert ui["schema"] == PFI006_MARKETS_UI_READ_MODEL_SCHEMA
    assert ui["workspace"] == "market"
    assert ui["workspace_label"] == "市场"
    assert ui["primary_feature_view"] == "market_slice"
    assert set(ui["secondary_feature_views"]) == {"hotspots", "market_overlay", "market_alerts"}
    assert {card["label"] for card in ui["cards"]} == {"市场事件", "热点扩散", "市场情绪"}
    assert ui["portfolio_overlay"]["target_weight_change"] == 0.0
    assert ui["portfolio_overlay"]["no_private_holdings_used"] is True
    assert ui["portfolio_overlay"]["review_required"] is True
    assert {alert["alert_id"] for alert in ui["alerts"]} >= {"market_freshness_review", "hotspot_divergence_review"}
    assert {view["view_id"] for view in ui["saved_views"]} >= {"market_us_daily_review", "market_hotspot_watch"}
    assert all(view["readonly"] is True for view in ui["saved_views"])
    assert "打开一级入口：市场" in ui["journey"]
    assert ui["safety_boundary"]["no_order_execution"] is True


def test_pfi006_rollback_removes_temporary_source_evidence_job_and_task_records(tmp_path: Path):
    fixture = build_pfi006_markets_golden_fixture()
    workflow = build_markets_workflow(
        fixture["price_frames"],
        fixture["instruments"],
        source_id=fixture["source_id"],
        as_of=fixture["as_of"],
        data_source="PFI006GoldenFixture",
        market=fixture["market"],
        interval=fixture["interval"],
        max_snapshots=12,
    )
    store = OperationalStore(tmp_path / "private" / "operational" / "pfi.sqlite")
    ids = record_markets_workflow(store, workflow, artifact_uri="operational_store:pfi006_markets_acceptance")

    proof = rollback_pfi006_markets_records(store, ids)

    assert proof["schema"] == "PFI006MarketsRollbackProofV1"
    assert proof["status"] == "Pass"
    assert proof["residue_counts"] == {
        "source_records": 0,
        "evidence_records": 0,
        "job_records": 0,
        "task_records": 0,
    }
    assert proof["deleted_counts"]["source_records"] == 1
    assert proof["deleted_counts"]["evidence_records"] == 1
    assert proof["deleted_counts"]["job_records"] == 1
    assert proof["deleted_counts"]["task_records"] == 1


def test_pfi006_web_shell_exposes_same_shell_market_vertical_slice_controls():
    js = _text(WEB_ROOT / "app" / "shell.js")

    for view in ["market_slice", "market_overlay", "market_alerts"]:
        assert f'view: "{view}"' in js
    for label in ["市场垂直切片", "组合影响覆盖层", "提醒与保存视图"]:
        assert label in js
    for text in ["市场事件、热点扩散和市场情绪", "不读取私有持仓", "保存视图只读", "不触发交易"]:
        assert text in js
    assert '市场垂直切片: { view: "market_slice"' in js
    assert '组合影响覆盖: { view: "market_overlay"' in js
    assert '提醒与保存视图: { view: "market_alerts"' in js
    assert "window.open" not in js
    assert "location.reload" not in js
    assert "window.location.href" not in js


def test_pfi006_script_and_target_gate_are_wired_without_heavy_smoke():
    script = _text(PROJECT_ROOT / "scripts" / "pfi006MarketsAcceptance.sh")
    gate = _text(PROJECT_ROOT / "scripts" / "pfiGate.sh")
    gitignore = _text(PROJECT_ROOT / ".gitignore")

    assert "PFI006MarketsAcceptance" in script
    assert "run_pfi006_markets_acceptance" in script
    assert "tests/contract/test_pfi006_markets_vertical_acceptance.py" in gate
    assert "data/systemAudit/PFI006MarketsAcceptance*.json" in gitignore
    assert "finalAcceptanceCheck" not in script
    assert "ciSmoke" not in script
    assert "broker" not in script.lower()
