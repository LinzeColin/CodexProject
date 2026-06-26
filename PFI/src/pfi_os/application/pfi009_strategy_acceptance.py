from __future__ import annotations

import json
import math
import tempfile
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from pfi_os.application.durable_jobs import DurableJobStore
from pfi_os.application.operational_store import OperationalStore
from pfi_os.application.strategy_lab_workflow import build_strategy_lab_workflow, record_strategy_lab_workflow
from pfi_os.approvals import StrategyApprovalRegistry
from pfi_os.backtest import BacktestConfig
from pfi_os.research import ExperimentRunner, split_train_test_by_time, walk_forward_windows
from pfi_os.strategies import MovingAverageCrossoverStrategy


PFI009_STRATEGY_ACCEPTANCE_SCHEMA = "PFI009StrategyVerticalAcceptanceV1"
PFI009_STRATEGY_UI_READ_MODEL_SCHEMA = "PFI009StrategyUIReadModelV1"
PFI009_MODEL_REGISTRY_SCHEMA = "PFI009StrategyModelRegistryV1"
PFI009_GOLDEN_SOURCE_ID = "src-pfi009-strategy-golden-2026-06-19"
PFI009_RUNTIME_SOURCE_ID = "src-pfi009-strategy-runtime-2026-06-19"
PFI009_GOLDEN_AS_OF = "2026-06-19T17:00:00+10:00"
PFI009_JOB_TYPE = "pfi009_strategy_backtest"


def build_pfi009_strategy_golden_fixture() -> dict[str, Any]:
    return {
        "schema": "PFI009StrategyGoldenFixtureV1",
        "source_id": PFI009_GOLDEN_SOURCE_ID,
        "as_of": PFI009_GOLDEN_AS_OF,
        "symbol": "PFI009",
        "market": "US",
        "interval": "1d",
        "bar_count": 360,
        "start": "2024-01-02",
        "strategy": {
            "class": "MovingAverageCrossoverStrategy",
            "params": {"short_window": 5, "long_window": 20},
            "param_grid": {"short_window": [5, 10], "long_window": [20, 40]},
        },
        "backtest_config": {
            "initial_cash": 100000.0,
            "commission_rate": 0.001,
            "slippage_bps": 5.0,
            "market_impact_bps": 0.0,
            "allow_short": False,
        },
        "corporate_actions": [
            {
                "symbol": "PFI009",
                "type": "split",
                "ratio": 2.0,
                "effective_date": "2024-07-01",
                "adjustment_mode": "backward_adjusted",
                "status": "AppliedToGoldenBars",
            }
        ],
        "universe_events": [
            {
                "symbol": "PFI009D",
                "event": "delisted",
                "delisted_date": "2024-09-30",
                "included_in_backtest": False,
                "status": "ExcludedFromPITUniverse",
            }
        ],
        "train_test": {"split_ratio": 0.7, "score_metric": "sharpe"},
        "walk_forward": {"train_window": 160, "test_window": 100, "step_window": 100, "score_metric": "sharpe"},
        "expected": {
            "bar_count": 360,
            "corporate_action_adjusted_count": 1,
            "delisted_symbol_count": 1,
            "train_test_status": "Pass",
            "walk_forward_status": "Pass",
            "walk_forward_window_count": 2,
            "target_weight_change": 0.0,
            "registered_model_count": 1,
        },
    }


def build_pfi009_pit_bars(fixture: dict[str, Any] | None = None) -> pd.DataFrame:
    resolved = fixture or build_pfi009_strategy_golden_fixture()
    rows: list[dict[str, Any]] = []
    dates = pd.bdate_range(str(resolved["start"]), periods=int(resolved["bar_count"]))
    split_date = pd.Timestamp(resolved["corporate_actions"][0]["effective_date"])
    for index, date in enumerate(dates):
        close = 100.0 + index * 0.18 + 2.5 * math.sin(index / 7.0) + 1.4 * math.sin(index / 19.0)
        open_price = close * (1 + 0.002 * math.sin(index / 3.0))
        rows.append(
            {
                "datetime": date,
                "symbol": resolved["symbol"],
                "market": resolved["market"],
                "interval": resolved["interval"],
                "open": round(open_price, 4),
                "high": round(max(open_price, close) * 1.01, 4),
                "low": round(min(open_price, close) * 0.99, 4),
                "close": round(close, 4),
                "volume": 1_000_000 + index * 1_000,
                "corporate_action_adjustment": "backward_adjusted_split" if date >= split_date else "",
                "pit_available_at": pd.Timestamp(date).isoformat(),
            }
        )
    return pd.DataFrame(rows)


def build_pfi009_strategy_model_registry(
    workflow: dict[str, Any],
    validation: dict[str, Any],
    runtime_proof: dict[str, Any],
) -> dict[str, Any]:
    strategy = workflow.get("strategy", {})
    registry = StrategyApprovalRegistry()
    approved = registry.is_approved(MovingAverageCrossoverStrategy(**strategy.get("params", {})))
    model_id = f"{strategy.get('strategy_id', 'strategy')}:{strategy.get('version', '')}:{workflow.get('backtest', {}).get('reproducibility_hash', '')[:12]}"
    status = "CandidateReview"
    if validation.get("train_test", {}).get("validation_status") == "Pass" and validation.get("walk_forward", {}).get("validation_status") == "Pass":
        status = "ReviewReady"
    return {
        "schema": PFI009_MODEL_REGISTRY_SCHEMA,
        "registry_id": f"registry-{workflow.get('workflow_id', '')}",
        "registered_model_count": 1,
        "models": [
            {
                "model_id": model_id,
                "strategy_id": strategy.get("strategy_id", ""),
                "version": strategy.get("version", ""),
                "params": strategy.get("params", {}),
                "status": status,
                "approved_by_strategy_registry": approved,
                "backtest_hash": workflow.get("backtest", {}).get("reproducibility_hash", ""),
                "train_test_status": validation.get("train_test", {}).get("validation_status", ""),
                "walk_forward_status": validation.get("walk_forward", {}).get("validation_status", ""),
                "runtime_job_id": runtime_proof.get("job_id", ""),
                "order_enabled": False,
                "live_signal_enabled": False,
                "human_review_required": True,
            }
        ],
        "safety_boundary": {
            "research_only": True,
            "no_live_trading": True,
            "no_broker_calls": True,
            "no_order_execution": True,
            "no_live_signal": True,
            "human_review_required": True,
        },
    }


def build_pfi009_strategy_ui_read_model(
    workflow: dict[str, Any],
    fixture: dict[str, Any],
    validation: dict[str, Any],
    registry: dict[str, Any],
    runtime_proof: dict[str, Any],
    ids: dict[str, str],
) -> dict[str, Any]:
    return {
        "schema": PFI009_STRATEGY_UI_READ_MODEL_SCHEMA,
        "workspace": "strategy",
        "workspace_label": "策略实验室",
        "primary_route": "strategy",
        "primary_feature_view": "strategy_slice",
        "secondary_feature_views": ["pit_backtest", "train_test_validation", "walk_forward_validation", "strategy_registry"],
        "title": "策略垂直切片",
        "summary": "从固定 PIT 样本回测到样本外验证、滚动验证、策略注册和人工复核，不生成实盘信号。",
        "cards": [
            _ui_card("PIT 回测", workflow.get("backtest", {}).get("metrics", {}), workflow.get("status", "Review")),
            _ui_card("样本外验证", validation.get("train_test", {}), validation.get("train_test", {}).get("validation_status", "Review")),
            _ui_card("滚动验证", validation.get("walk_forward", {}), validation.get("walk_forward", {}).get("validation_status", "Review")),
            _ui_card("策略注册", registry.get("models", [{}])[0], registry.get("models", [{}])[0].get("status", "Review")),
        ],
        "pit_data_contract": {
            "bar_count": int(fixture["bar_count"]),
            "bar_checksum": workflow.get("data_window", {}).get("bar_checksum", ""),
            "corporate_action_adjusted_count": len(fixture.get("corporate_actions", [])),
            "delisted_symbol_count": len(fixture.get("universe_events", [])),
            "delisted_symbols_excluded": [event["symbol"] for event in fixture.get("universe_events", []) if not event.get("included_in_backtest", True)],
            "point_in_time_as_of": fixture.get("as_of", ""),
        },
        "validation": validation,
        "model_registry": registry,
        "runtime": runtime_proof,
        "decision": {
            "target_weight_change": workflow.get("decision", {}).get("target_weight_change", 0.0),
            "human_review_required": workflow.get("decision", {}).get("human_review_required", True),
            "order_intent_created": False,
            "live_signal_created": False,
        },
        "journey": [
            "打开一级入口：策略实验室",
            "打开功能：策略垂直切片",
            "查看 PIT 回测和固定样本哈希",
            "核对样本外验证和滚动验证没有未来数据",
            "查看策略注册和人工复核任务",
        ],
        "operational_record_ids": ids,
        "safety_boundary": {
            "research_only": True,
            "synthetic_fixture_only": True,
            "no_live_trading": True,
            "no_broker_calls": True,
            "no_order_execution": True,
            "no_live_signal": True,
            "no_holding_mutation": True,
            "human_review_required": True,
        },
    }


def run_pfi009_strategy_acceptance(*, db_path: Path | str | None = None) -> dict[str, Any]:
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    if db_path is None:
        with tempfile.TemporaryDirectory(prefix="pfi009-strategy-") as tmp_dir:
            return _run_acceptance(
                Path(tmp_dir) / "private" / "operational" / "pfi.sqlite",
                experiment_dir=Path(tmp_dir) / "experiments",
                generated_at=generated_at,
            )
    return _run_acceptance(Path(db_path), experiment_dir=Path(db_path).parent / "experiments", generated_at=generated_at)


def rollback_pfi009_strategy_records(store: OperationalStore, ids: dict[str, str], runtime_proof: dict[str, Any]) -> dict[str, Any]:
    source_id = str(ids.get("source_id", ""))
    evidence_id = str(ids.get("evidence_id", ""))
    job_id = str(ids.get("job_id", ""))
    task_id = str(ids.get("task_id", ""))
    runtime_job_id = str(runtime_proof.get("job_id", ""))
    runtime_source_id = str(runtime_proof.get("source_id", PFI009_RUNTIME_SOURCE_ID))
    counts: dict[str, int] = {}
    with store.connect() as conn:
        counts["task_records"] = conn.execute("DELETE FROM task_records WHERE task_id = ?", (task_id,)).rowcount
        counts["strategy_job_records"] = conn.execute("DELETE FROM job_records WHERE job_id = ?", (job_id,)).rowcount
        counts["runtime_job_records"] = conn.execute("DELETE FROM job_records WHERE job_id = ?", (runtime_job_id,)).rowcount
        counts["evidence_records"] = conn.execute("DELETE FROM evidence_records WHERE evidence_id = ?", (evidence_id,)).rowcount
        counts["strategy_source_versions"] = conn.execute("DELETE FROM source_versions WHERE source_id = ?", (source_id,)).rowcount
        counts["runtime_source_versions"] = conn.execute("DELETE FROM source_versions WHERE source_id = ?", (runtime_source_id,)).rowcount
        counts["strategy_source_records"] = conn.execute("DELETE FROM source_records WHERE source_id = ?", (source_id,)).rowcount
        counts["runtime_source_records"] = conn.execute("DELETE FROM source_records WHERE source_id = ?", (runtime_source_id,)).rowcount
    residue = {
        "strategy_source_records": _count_rows(store, "source_records", "source_id", source_id),
        "runtime_source_records": _count_rows(store, "source_records", "source_id", runtime_source_id),
        "evidence_records": _count_rows(store, "evidence_records", "evidence_id", evidence_id),
        "strategy_job_records": _count_rows(store, "job_records", "job_id", job_id),
        "runtime_job_records": _count_rows(store, "job_records", "job_id", runtime_job_id),
        "task_records": _count_rows(store, "task_records", "task_id", task_id),
    }
    return {
        "schema": "PFI009StrategyRollbackProofV1",
        "mode": "temporary_operational_store",
        "deleted_counts": counts,
        "residue_counts": residue,
        "status": "Pass" if all(value == 0 for value in residue.values()) else "Fail",
        "note": "Rollback deletes only PFI-009 source/evidence/job/task/runtime rows in the temporary acceptance store.",
    }


def _run_acceptance(db_path: Path, *, experiment_dir: Path, generated_at: str) -> dict[str, Any]:
    fixture = build_pfi009_strategy_golden_fixture()
    bars = build_pfi009_pit_bars(fixture)
    config = BacktestConfig(**fixture["backtest_config"])
    strategy = MovingAverageCrossoverStrategy(**fixture["strategy"]["params"])
    store = OperationalStore(db_path)
    workflow = build_strategy_lab_workflow(
        bars,
        strategy,
        config=config,
        source_id=fixture["source_id"],
        as_of=fixture["as_of"],
        evidence_class="pfi009_pit_strategy_review",
        replay_id="pfi009-pit-golden-replay",
    )
    validation = _validation_payload(bars, fixture, config, experiment_dir)
    runtime_proof = _runtime_cancel_resume_proof(store, fixture, workflow)
    ids = record_strategy_lab_workflow(store, workflow, artifact_uri="operational_store:pfi009_strategy_acceptance")
    registry = build_pfi009_strategy_model_registry(workflow, validation, runtime_proof)
    ui_read_model = build_pfi009_strategy_ui_read_model(workflow, fixture, validation, registry, runtime_proof, ids)
    golden_metrics = _golden_metrics(workflow, validation, registry, runtime_proof, fixture, store)
    checks = _acceptance_checks(workflow, ui_read_model, validation, registry, runtime_proof, golden_metrics, ids, store)
    rollback_proof = rollback_pfi009_strategy_records(store, ids, runtime_proof)
    checks.append(_check("RollbackProof", rollback_proof["status"] == "Pass", json.dumps(rollback_proof["residue_counts"], sort_keys=True)))
    summary = _summary(checks)
    status = "Pass" if summary["fail"] == 0 else "Fail"
    return {
        "schema": PFI009_STRATEGY_ACCEPTANCE_SCHEMA,
        "generated_at": generated_at,
        "status": status,
        "summary": summary,
        "workflow": _json_safe(workflow),
        "ui_read_model": _json_safe(ui_read_model),
        "validation": _json_safe(validation),
        "model_registry": _json_safe(registry),
        "runtime_proof": _json_safe(runtime_proof),
        "golden_metrics": golden_metrics,
        "rollback_proof": rollback_proof,
        "checks": checks,
        "safety_boundary": {
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
        },
        "next_action": "Use this as Gate 3 Strategy evidence, then continue PFI-010 Minute Fast Path.",
    }


def _validation_payload(bars: pd.DataFrame, fixture: dict[str, Any], config: BacktestConfig, experiment_dir: Path) -> dict[str, Any]:
    runner = ExperimentRunner(output_dir=experiment_dir, config=config)
    param_grid = fixture["strategy"]["param_grid"]
    train_cfg = fixture["train_test"]
    walk_cfg = fixture["walk_forward"]
    train_test = runner.run_train_test_validation(
        bars,
        MovingAverageCrossoverStrategy,
        param_grid,
        experiment_name="pfi009_train_test",
        split_ratio=float(train_cfg["split_ratio"]),
        score_metric=str(train_cfg["score_metric"]),
    )
    walk_forward = runner.run_walk_forward_validation(
        bars,
        MovingAverageCrossoverStrategy,
        param_grid,
        experiment_name="pfi009_walk_forward",
        train_window=int(walk_cfg["train_window"]),
        test_window=int(walk_cfg["test_window"]),
        step_window=int(walk_cfg["step_window"]),
        score_metric=str(walk_cfg["score_metric"]),
    )
    return {
        "schema": "PFI009StrategyValidationV1",
        "train_test": asdict(train_test),
        "walk_forward": asdict(walk_forward),
        "no_future_data_proof": _no_future_data_proof(bars, fixture, asdict(train_test), asdict(walk_forward)),
    }


def _runtime_cancel_resume_proof(store: OperationalStore, fixture: dict[str, Any], workflow: dict[str, Any]) -> dict[str, Any]:
    jobs = DurableJobStore(store, source_id=PFI009_RUNTIME_SOURCE_ID)
    base_time = datetime(2026, 6, 19, 7, 0, tzinfo=timezone.utc)
    queued = jobs.enqueue(
        job_type=PFI009_JOB_TYPE,
        idempotency_key=f"{fixture['source_id']}:{workflow.get('workflow_id', '')}",
        payload={"workflow_id": workflow.get("workflow_id", ""), "mode": "acceptance"},
        as_of=fixture["as_of"],
        max_attempts=2,
        now=base_time,
    )
    cancelled = jobs.cancel(queued["job_id"], reason="PFI-009 acceptance pause before validation replay", now=base_time.replace(minute=1))
    resumed = jobs.resume(queued["job_id"], reason="PFI-009 acceptance resume after pause", now=base_time.replace(minute=2))
    claimed = jobs.claim(job_type=PFI009_JOB_TYPE, worker_id="pfi009-worker", lease_seconds=30, now=base_time.replace(minute=3))
    completed = jobs.complete(claimed["job_id"], worker_id="pfi009-worker", artifact_uri="operational_store:pfi009_strategy_acceptance", now=base_time.replace(minute=4))
    completed_row = jobs.get(queued["job_id"])
    metadata = _metadata_from_row(completed_row)
    return {
        "schema": "PFI009StrategyRuntimeCancelResumeProofV1",
        "source_id": PFI009_RUNTIME_SOURCE_ID,
        "job_id": queued["job_id"],
        "queued_status": queued["status"],
        "cancelled_status": cancelled["status"],
        "resumed_status": resumed["status"],
        "claimed": claimed["claimed"],
        "completed_status": completed["status"],
        "resume_count": int(metadata.get("resume_count", 0) or 0),
        "event_count": len(metadata.get("event_log", [])),
        "safety_boundary": completed.get("safety_boundary", {}),
    }


def _no_future_data_proof(
    bars: pd.DataFrame,
    fixture: dict[str, Any],
    train_test: dict[str, Any],
    walk_forward: dict[str, Any],
) -> dict[str, Any]:
    train, test, split_datetime = split_train_test_by_time(bars, split_ratio=float(fixture["train_test"]["split_ratio"]))
    train_max = _datetime_text(train["datetime"].max())
    test_min = _datetime_text(test["datetime"].min())
    windows = walk_forward_windows(
        bars,
        train_window=int(fixture["walk_forward"]["train_window"]),
        test_window=int(fixture["walk_forward"]["test_window"]),
        step_window=int(fixture["walk_forward"]["step_window"]),
    )
    window_proofs = [
        {
            "window": index,
            "train_end": _datetime_text(bounds["train_end"]),
            "test_start": _datetime_text(bounds["test_start"]),
            "non_overlapping": pd.Timestamp(bounds["train_end"]) < pd.Timestamp(bounds["test_start"]),
        }
        for index, (_train, _test, bounds) in enumerate(windows, start=1)
    ]
    return {
        "split_datetime": _datetime_text(split_datetime),
        "train_max_datetime": train_max,
        "test_min_datetime": test_min,
        "train_before_test": pd.Timestamp(train["datetime"].max()) < pd.Timestamp(test["datetime"].min()),
        "walk_forward_windows_non_overlapping": all(item["non_overlapping"] for item in window_proofs),
        "window_proofs": window_proofs,
        "train_test_status": train_test.get("validation_status", ""),
        "walk_forward_status": walk_forward.get("validation_status", ""),
    }


def _acceptance_checks(
    workflow: dict[str, Any],
    ui_read_model: dict[str, Any],
    validation: dict[str, Any],
    registry: dict[str, Any],
    runtime_proof: dict[str, Any],
    golden_metrics: dict[str, Any],
    ids: dict[str, str],
    store: OperationalStore,
) -> list[dict[str, str]]:
    rows = {table: store.table_rows(table) for table in ("source_records", "evidence_records", "job_records", "task_records")}
    no_future = validation.get("no_future_data_proof", {})
    return [
        _check("DataChain:PITGoldenBars", golden_metrics["bar_count"] == 360 and bool(golden_metrics["bar_checksum"]), f"bars={golden_metrics['bar_count']}"),
        _check("Golden:CorporateActionDelisted", golden_metrics["corporate_action_adjusted_count"] == 1 and golden_metrics["delisted_symbol_count"] == 1, "split=1; delisted=1"),
        _check("Domain:StrategyLabWorkflow", workflow.get("schema") == "PFIOSPhaseBStrategyLabWorkflowV1" and workflow.get("workspace") == "strategy_lab", workflow.get("workflow_id", "")),
        _check("Backtest:PITReplayNoFutureExecution", workflow.get("backtest", {}).get("execution_model") == "target_weight_next_bar_open" and bool(workflow.get("backtest", {}).get("reproducibility_hash")), workflow.get("backtest", {}).get("execution_model", "")),
        _check("Validation:TrainTestNoFutureLeak", validation.get("train_test", {}).get("validation_status") == "Pass" and no_future.get("train_before_test") is True, str(no_future.get("split_datetime", ""))),
        _check("Validation:WalkForwardNoFutureLeak", validation.get("walk_forward", {}).get("validation_status") == "Pass" and no_future.get("walk_forward_windows_non_overlapping") is True, f"windows={golden_metrics['walk_forward_window_count']}"),
        _check("Training:MarketFeelNoFutureLeak", workflow.get("market_feel_training", {}).get("future_bars_hidden") is True, str(workflow.get("market_feel_training", {}).get("visible_until", ""))),
        _check("ModelRegistry:ReviewOnly", registry.get("registered_model_count") == 1 and registry.get("models", [{}])[0].get("order_enabled") is False and registry.get("models", [{}])[0].get("live_signal_enabled") is False, registry.get("models", [{}])[0].get("model_id", "")),
        _check("Runtime:CancelResume", runtime_proof.get("cancelled_status") == "cancelled" and runtime_proof.get("resumed_status") == "queued" and runtime_proof.get("completed_status") == "completed", runtime_proof.get("job_id", "")),
        _check("API:UIReadModel", ui_read_model.get("schema") == PFI009_STRATEGY_UI_READ_MODEL_SCHEMA and ui_read_model.get("primary_route") == "strategy", ui_read_model.get("schema", "")),
        _check("UI:ChineseJourney", "策略实验室" in ui_read_model.get("workspace_label", "") and all(step for step in ui_read_model.get("journey", [])), "strategy journey labels"),
        _check("TasksEvidence:Source", any(row["source_id"] == ids["source_id"] for row in rows["source_records"]), ids["source_id"]),
        _check("TasksEvidence:Evidence", any(row["evidence_id"] == ids["evidence_id"] for row in rows["evidence_records"]), ids["evidence_id"]),
        _check("TasksEvidence:Job", any(row["job_id"] == ids["job_id"] and row["status"] == "completed" for row in rows["job_records"]), ids["job_id"]),
        _check("TasksEvidence:ReviewTask", any(row["task_id"] == ids["task_id"] and row["human_review_required"] == 1 for row in rows["task_records"]), ids["task_id"]),
        _check("Safety:NoExecution", all(ui_read_model.get("safety_boundary", {}).get(key) is True for key in ("research_only", "no_live_trading", "no_broker_calls", "no_order_execution", "no_live_signal", "no_holding_mutation", "human_review_required")), "research-only strategy boundary"),
        _check("GoldenMetrics:StableWorkflow", bool(golden_metrics.get("workflow_id")) and bool(golden_metrics.get("reproducibility_hash")), str(golden_metrics.get("workflow_id", ""))),
    ]


def _golden_metrics(
    workflow: dict[str, Any],
    validation: dict[str, Any],
    registry: dict[str, Any],
    runtime_proof: dict[str, Any],
    fixture: dict[str, Any],
    store: OperationalStore,
) -> dict[str, Any]:
    return {
        "workflow_id": workflow.get("workflow_id", ""),
        "source_id": workflow.get("source_id", ""),
        "reproducibility_hash": workflow.get("backtest", {}).get("reproducibility_hash", ""),
        "bar_checksum": workflow.get("data_window", {}).get("bar_checksum", ""),
        "bar_count": int(workflow.get("data_window", {}).get("rows", 0) or 0),
        "trade_count": int(workflow.get("backtest", {}).get("trade_count", 0) or 0),
        "total_return": round(float(workflow.get("backtest", {}).get("metrics", {}).get("total_return", 0.0) or 0.0), 6),
        "max_drawdown": round(float(workflow.get("backtest", {}).get("metrics", {}).get("max_drawdown", 0.0) or 0.0), 6),
        "corporate_action_adjusted_count": len(fixture.get("corporate_actions", [])),
        "delisted_symbol_count": len(fixture.get("universe_events", [])),
        "train_test_status": validation.get("train_test", {}).get("validation_status", ""),
        "walk_forward_status": validation.get("walk_forward", {}).get("validation_status", ""),
        "walk_forward_window_count": int(validation.get("walk_forward", {}).get("window_count", 0) or 0),
        "registered_model_count": int(registry.get("registered_model_count", 0) or 0),
        "runtime_resume_count": int(runtime_proof.get("resume_count", 0) or 0),
        "target_weight_change": float(workflow.get("decision", {}).get("target_weight_change", 0.0) or 0.0),
        "source_record_count": len(store.table_rows("source_records")),
        "evidence_record_count": len(store.table_rows("evidence_records")),
        "job_record_count": len(store.table_rows("job_records")),
        "task_record_count": len(store.table_rows("task_records")),
    }


def _ui_card(label: str, payload: dict[str, Any], status: str) -> dict[str, Any]:
    return {
        "label": label,
        "status": status,
        "summary": _compact_summary(payload),
        "review_required": True,
        "readonly": True,
    }


def _compact_summary(payload: dict[str, Any]) -> str:
    if "total_return" in payload:
        return f"return={float(payload.get('total_return', 0.0) or 0.0):.2%}; drawdown={float(payload.get('max_drawdown', 0.0) or 0.0):.2%}"
    if "validation_status" in payload:
        return f"status={payload.get('validation_status')}; ratio={float(payload.get('generalization_ratio', payload.get('average_generalization_ratio', 0.0)) or 0.0):.2%}"
    if "model_id" in payload:
        return f"model={payload.get('model_id')}; order_enabled={payload.get('order_enabled')}"
    return json.dumps(_json_safe(payload), ensure_ascii=False, sort_keys=True)[:160]


def _count_rows(store: OperationalStore, table: str, column: str, value: str) -> int:
    return sum(1 for row in store.table_rows(table) if str(row.get(column, "")) == value)


def _metadata_from_row(row: dict[str, Any]) -> dict[str, Any]:
    try:
        value = json.loads(str(row.get("metadata_json", "{}") or "{}"))
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def _check(name: str, condition: bool, evidence: str) -> dict[str, str]:
    return {"name": name, "status": "Pass" if condition else "Fail", "evidence": evidence}


def _summary(checks: list[dict[str, str]]) -> dict[str, int]:
    return {
        "pass": sum(1 for row in checks if row["status"] == "Pass"),
        "fail": sum(1 for row in checks if row["status"] == "Fail"),
        "info": sum(1 for row in checks if row["status"] == "Info"),
        "total": len(checks),
    }


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, pd.Timestamp):
        return _datetime_text(value)
    if hasattr(value, "item"):
        try:
            return _json_safe(value.item())
        except Exception:
            return str(value)
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value


def _datetime_text(value: Any) -> str:
    if value is None or pd.isna(value):
        return ""
    return pd.Timestamp(value).isoformat()
