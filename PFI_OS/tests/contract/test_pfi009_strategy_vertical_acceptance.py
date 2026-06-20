from datetime import datetime, timezone
from pathlib import Path

import pytest

from pfi_os.application import (
    PFI009_STRATEGY_ACCEPTANCE_SCHEMA,
    PFI009_STRATEGY_UI_READ_MODEL_SCHEMA,
    OperationalStore,
    build_pfi009_pit_bars,
    build_pfi009_strategy_golden_fixture,
    build_strategy_lab_workflow,
    record_strategy_lab_workflow,
    rollback_pfi009_strategy_records,
    run_pfi009_strategy_acceptance,
)
from pfi_os.application.durable_jobs import DurableJobStore
from pfi_os.application.pfi009_strategy_acceptance import PFI009_JOB_TYPE, PFI009_RUNTIME_SOURCE_ID
from pfi_os.backtest import BacktestConfig
from pfi_os.strategies import MovingAverageCrossoverStrategy


PROJECT_ROOT = Path(__file__).resolve().parents[2]
WEB_ROOT = PROJECT_ROOT / "web"
pytestmark = pytest.mark.filterwarnings("ignore:Downcasting object dtype arrays on .fillna:FutureWarning")


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _strategy_workflow_from_fixture() -> tuple[dict, dict]:
    fixture = build_pfi009_strategy_golden_fixture()
    workflow = build_strategy_lab_workflow(
        build_pfi009_pit_bars(fixture),
        MovingAverageCrossoverStrategy(**fixture["strategy"]["params"]),
        config=BacktestConfig(**fixture["backtest_config"]),
        source_id=fixture["source_id"],
        as_of=fixture["as_of"],
        evidence_class="pfi009_pit_strategy_review",
        replay_id="pfi009-pit-golden-replay",
    )
    return fixture, workflow


def test_pfi009_acceptance_runs_pit_backtest_validation_registry_runtime_and_rollback_chain():
    payload = run_pfi009_strategy_acceptance()

    assert payload["schema"] == PFI009_STRATEGY_ACCEPTANCE_SCHEMA
    assert payload["status"] == "Pass"
    assert payload["summary"]["fail"] == 0
    assert payload["summary"]["pass"] >= 18
    check_names = {row["name"] for row in payload["checks"]}
    for required in {
        "DataChain:PITGoldenBars",
        "Golden:CorporateActionDelisted",
        "Domain:StrategyLabWorkflow",
        "Backtest:PITReplayNoFutureExecution",
        "Validation:TrainTestNoFutureLeak",
        "Validation:WalkForwardNoFutureLeak",
        "Training:MarketFeelNoFutureLeak",
        "ModelRegistry:ReviewOnly",
        "Runtime:CancelResume",
        "API:UIReadModel",
        "UI:ChineseJourney",
        "TasksEvidence:Source",
        "TasksEvidence:Evidence",
        "TasksEvidence:Job",
        "TasksEvidence:ReviewTask",
        "Safety:NoExecution",
        "GoldenMetrics:StableWorkflow",
        "RollbackProof",
    }:
        assert required in check_names
    assert payload["ui_read_model"]["schema"] == PFI009_STRATEGY_UI_READ_MODEL_SCHEMA
    assert payload["rollback_proof"]["status"] == "Pass"
    assert payload["safety_boundary"] == {
        "research_only": True,
        "synthetic_fixture_only": True,
        "provider_fetch_required": False,
        "broker_required": False,
        "llm_required": False,
        "no_live_trading": True,
        "no_broker_calls": True,
        "no_order_execution": True,
        "no_live_signal": True,
        "no_holding_mutation": True,
        "human_review_required": True,
    }


def test_pfi009_golden_metrics_are_deterministic_and_review_only():
    first = run_pfi009_strategy_acceptance()
    second = run_pfi009_strategy_acceptance()

    first_metrics = first["golden_metrics"]
    second_metrics = second["golden_metrics"]
    assert first_metrics["workflow_id"] == second_metrics["workflow_id"]
    assert first_metrics["reproducibility_hash"] == second_metrics["reproducibility_hash"]
    assert first_metrics["bar_checksum"] == second_metrics["bar_checksum"]
    assert first_metrics["bar_count"] == 360
    assert first_metrics["corporate_action_adjusted_count"] == 1
    assert first_metrics["delisted_symbol_count"] == 1
    assert first_metrics["train_test_status"] == "Pass"
    assert first_metrics["walk_forward_status"] == "Pass"
    assert first_metrics["walk_forward_window_count"] == 2
    assert first_metrics["registered_model_count"] == 1
    assert first_metrics["runtime_resume_count"] == 1
    assert first_metrics["target_weight_change"] == 0.0


def test_pfi009_validation_proves_no_future_data_and_keeps_market_feel_training():
    payload = run_pfi009_strategy_acceptance()
    validation = payload["validation"]
    proof = validation["no_future_data_proof"]
    workflow = payload["workflow"]

    assert workflow["backtest"]["execution_model"] == "target_weight_next_bar_open"
    assert workflow["market_feel_training"]["future_bars_hidden"] is True
    assert proof["train_before_test"] is True
    assert proof["walk_forward_windows_non_overlapping"] is True
    assert len(proof["window_proofs"]) == 2
    assert all(item["non_overlapping"] is True for item in proof["window_proofs"])
    assert validation["train_test"]["validation_status"] == "Pass"
    assert validation["walk_forward"]["validation_status"] == "Pass"
    assert payload["ui_read_model"]["pit_data_contract"]["delisted_symbols_excluded"] == ["PFI009D"]


def test_pfi009_ui_read_model_exposes_strategy_journey_validation_registry_and_runtime():
    payload = run_pfi009_strategy_acceptance()
    ui = payload["ui_read_model"]

    assert ui["schema"] == PFI009_STRATEGY_UI_READ_MODEL_SCHEMA
    assert ui["workspace"] == "strategy"
    assert ui["workspace_label"] == "策略实验室"
    assert ui["primary_feature_view"] == "strategy_slice"
    assert set(ui["secondary_feature_views"]) == {"pit_backtest", "train_test_validation", "walk_forward_validation", "strategy_registry"}
    assert ui["pit_data_contract"]["bar_count"] == 360
    assert ui["pit_data_contract"]["corporate_action_adjusted_count"] == 1
    assert ui["validation"]["no_future_data_proof"]["train_before_test"] is True
    assert ui["model_registry"]["registered_model_count"] == 1
    assert ui["model_registry"]["models"][0]["order_enabled"] is False
    assert ui["model_registry"]["models"][0]["live_signal_enabled"] is False
    assert ui["runtime"]["completed_status"] == "completed"
    assert ui["decision"]["target_weight_change"] == 0.0
    assert ui["decision"]["order_intent_created"] is False
    assert ui["decision"]["live_signal_created"] is False
    assert "打开一级入口：策略实验室" in ui["journey"]
    assert any("没有未来数据" in step for step in ui["journey"])
    assert ui["safety_boundary"]["no_live_signal"] is True
    assert ui["safety_boundary"]["no_order_execution"] is True


def test_pfi009_rollback_removes_strategy_and_runtime_rows(tmp_path: Path):
    fixture, workflow = _strategy_workflow_from_fixture()
    store = OperationalStore(tmp_path / "private" / "operational" / "pfi.sqlite")
    ids = record_strategy_lab_workflow(store, workflow, artifact_uri="operational_store:pfi009_strategy_acceptance")
    jobs = DurableJobStore(store, source_id=PFI009_RUNTIME_SOURCE_ID)
    queued = jobs.enqueue(
        job_type=PFI009_JOB_TYPE,
        idempotency_key=f"{fixture['source_id']}:{workflow['workflow_id']}",
        payload={"workflow_id": workflow["workflow_id"]},
        as_of=fixture["as_of"],
        now=datetime(2026, 6, 19, 7, 0, tzinfo=timezone.utc),
    )

    proof = rollback_pfi009_strategy_records(store, ids, {"job_id": queued["job_id"], "source_id": PFI009_RUNTIME_SOURCE_ID})

    assert proof["schema"] == "PFI009StrategyRollbackProofV1"
    assert proof["status"] == "Pass"
    assert proof["residue_counts"] == {
        "strategy_source_records": 0,
        "runtime_source_records": 0,
        "evidence_records": 0,
        "strategy_job_records": 0,
        "runtime_job_records": 0,
        "task_records": 0,
    }
    assert proof["deleted_counts"]["strategy_source_records"] == 1
    assert proof["deleted_counts"]["runtime_source_records"] == 1
    assert proof["deleted_counts"]["evidence_records"] == 1
    assert proof["deleted_counts"]["strategy_job_records"] == 1
    assert proof["deleted_counts"]["runtime_job_records"] == 1
    assert proof["deleted_counts"]["task_records"] == 1


def test_pfi009_web_shell_exposes_same_shell_strategy_controls():
    js = _text(WEB_ROOT / "app" / "shell.js")

    for view in ["strategy_slice", "pit_backtest", "train_test_validation", "walk_forward_validation", "strategy_registry"]:
        assert f'view: "{view}"' in js
    for label in ["策略垂直切片", "PIT回测", "样本外验证", "滚动验证", "策略注册"]:
        assert label in js
    for text in ["固定样本哈希", "没有未来数据", "不生成实盘信号", "不提交订单", "人工复核"]:
        assert text in js
    assert '策略垂直切片: { view: "strategy_slice"' in js
    assert 'PIT回测: { view: "pit_backtest"' in js
    assert '样本外验证: { view: "train_test_validation"' in js
    assert '滚动验证: { view: "walk_forward_validation"' in js
    assert '策略注册: { view: "strategy_registry"' in js
    assert "window.open" not in js
    assert "location.reload" not in js
    assert "window.location.href" not in js


def test_pfi009_script_and_target_gate_are_wired_without_heavy_smoke():
    script = _text(PROJECT_ROOT / "scripts" / "pfi009StrategyAcceptance.sh")
    gate = _text(PROJECT_ROOT / "scripts" / "pfiGate.sh")
    gitignore = _text(PROJECT_ROOT / ".gitignore")

    assert "PFI009StrategyAcceptance" in script
    assert "run_pfi009_strategy_acceptance" in script
    assert "tests/contract/test_pfi009_strategy_vertical_acceptance.py" in gate
    assert "data/systemAudit/PFI009StrategyAcceptance*.json" in gitignore
    assert "finalAcceptanceCheck" not in script
    assert "ciSmoke" not in script
