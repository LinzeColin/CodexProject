from pathlib import Path

from pfi_os.application import (
    OperationalStore,
    STRATEGY_LAB_WORKFLOW_SCHEMA,
    build_phase_b_strategy_lab_contract,
    build_strategy_lab_workflow,
    record_strategy_lab_workflow,
)
from pfi_os.backtest import BacktestConfig
from pfi_os.data.models import BarDataRequest
from pfi_os.data.providers import SampleDataProvider
from pfi_os.strategies import MovingAverageCrossoverStrategy


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


def _sample_bars():
    return SampleDataProvider(seed=42).get_bars(
        BarDataRequest(symbol="AAPL", market="US", interval="1d", start="2020-01-01", end="2023-12-31")
    )


def test_phase_b_strategy_lab_contract_declares_non_regression_constraints():
    contract = build_phase_b_strategy_lab_contract()

    assert contract["schema"] == "PFIOSPhaseBStrategyLabContractV1"
    assert contract["workflow_schema"] == STRATEGY_LAB_WORKFLOW_SCHEMA
    assert contract["workspace"] == "strategy_lab"
    assert "run_approved_strategy_backtest" in contract["required_steps"]
    assert contract["required_fact_fields"] == ["source_id", "as_of", "evidence_class"]
    assert set(contract["decision_contract_fields"]) == DECISION_FIELDS
    assert contract["non_regression_constraints"] == {
        "market_feel_training_retained": True,
        "strategy_backtesting_core": True,
        "no_live_trading": True,
        "human_review_required": True,
        "llm_required": False,
    }


def test_strategy_lab_workflow_builds_reproducible_research_decision():
    bars = _sample_bars()
    strategy = MovingAverageCrossoverStrategy(short_window=5, long_window=20)
    config = BacktestConfig(initial_cash=100_000, commission_rate=0.001, slippage_bps=5)

    first = build_strategy_lab_workflow(
        bars,
        strategy,
        config=config,
        source_id="src-strategy-aapl-2026-06-19",
        as_of="2026-06-19T09:30:00+10:00",
        replay_id="replay-aapl-sample",
    )
    second = build_strategy_lab_workflow(
        bars,
        strategy,
        config=config,
        source_id="src-strategy-aapl-2026-06-19",
        as_of="2026-06-19T09:30:00+10:00",
        replay_id="replay-aapl-sample",
    )

    assert first["schema"] == STRATEGY_LAB_WORKFLOW_SCHEMA
    assert first["workspace"] == "strategy_lab"
    assert first["source_id"] == "src-strategy-aapl-2026-06-19"
    assert first["evidence_class"] == "replay_backtest_result"
    assert first["model_versions"] == ["DisabledProvider"]
    assert first["data_window"]["symbol"] == "AAPL"
    assert first["data_window"]["bar_checksum"]
    assert first["backtest"]["reproducibility_hash"] == second["backtest"]["reproducibility_hash"]
    assert first["backtest"]["config"]["initial_cash"] == 100_000
    assert first["backtest"]["trade_count"] > 0
    assert first["validation"]["risk_status"] in {"Pass", "Watch", "Review", "Failed"}
    assert set(first["decision"]) == DECISION_FIELDS
    assert first["decision"]["action"] == "review_strategy_candidate"
    assert first["decision"]["target_weight_change"] == 0.0
    assert first["decision"]["human_review_required"] is True
    assert first["decision"]["source_ids"] == ["src-strategy-aapl-2026-06-19"]
    assert first["decision"]["counter_evidence"]
    assert first["decision"]["invalidation_conditions"]
    assert first["safety_boundary"] == {
        "research_only": True,
        "no_live_trading": True,
        "no_broker_calls": True,
        "no_order_execution": True,
        "human_review_required": True,
    }


def test_strategy_lab_workflow_retains_market_feel_training_without_future_leakage():
    payload = build_strategy_lab_workflow(
        _sample_bars(),
        MovingAverageCrossoverStrategy(short_window=5, long_window=20),
        source_id="src-strategy-market-feel",
        as_of="2026-06-19T09:30:00+10:00",
        answer_horizon=5,
    )

    training = payload["market_feel_training"]

    assert training["status"] == "Pass"
    assert training["future_bars_hidden"] is True
    assert training["visible_until"] < training["hidden_start_date"]
    assert training["hidden_start_date"] <= training["hidden_end_date"]
    assert "future bars" in payload["assumptions"][2]
    assert any("Market-feel training is a human pattern-recognition exercise" in item for item in payload["decision"]["counter_evidence"])


def test_strategy_lab_workflow_records_operational_store_evidence_job_and_review_task(tmp_path: Path):
    payload = build_strategy_lab_workflow(
        _sample_bars(),
        MovingAverageCrossoverStrategy(short_window=5, long_window=20),
        source_id="src-strategy-store",
        as_of="2026-06-19T09:30:00+10:00",
    )
    store = OperationalStore(tmp_path / "private" / "operational" / "pfi.sqlite")

    ids = record_strategy_lab_workflow(store, payload)

    sources = store.table_rows("source_records")
    evidence = store.table_rows("evidence_records")
    jobs = store.table_rows("job_records")
    tasks = store.table_rows("task_records")

    assert ids == {
        "source_id": "src-strategy-store",
        "evidence_id": f"evidence-{payload['workflow_id']}",
        "job_id": f"job-{payload['workflow_id']}",
        "task_id": f"task-{payload['workflow_id']}",
    }
    assert sources[0]["source_type"] == "strategy_lab_verification"
    assert sources[0]["evidence_class"] == "replay_backtest_result"
    assert evidence[0]["entity_id"] == "AAPL"
    assert "verification for AAPL" in evidence[0]["summary"]
    assert jobs[0]["status"] == "completed"
    assert jobs[0]["progress"] == 1.0
    assert tasks[0]["owner_workspace"] == "strategy_lab"
    assert tasks[0]["human_review_required"] == 1
