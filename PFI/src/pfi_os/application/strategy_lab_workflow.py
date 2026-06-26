from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

import pandas as pd

from pfi_os.analysis.market_feel import market_feel_training_case
from pfi_os.application.operational_store import (
    DataDomain,
    EvidenceRecord,
    JobRecord,
    OperationalStore,
    SourceRecord,
    TaskRecord,
)
from pfi_os.backtest import BacktestConfig, BacktestEngine
from pfi_os.strategies.base import Strategy


STRATEGY_LAB_WORKFLOW_SCHEMA = "PFIOSPhaseBStrategyLabWorkflowV1"


def build_strategy_lab_workflow(
    bars: pd.DataFrame,
    strategy: Strategy,
    *,
    config: BacktestConfig | None = None,
    source_id: str,
    as_of: str,
    evidence_class: str = "replay_backtest_result",
    replay_id: str = "",
    model_version: str = "DisabledProvider",
    answer_horizon: int = 5,
) -> dict[str, Any]:
    """Build a deterministic Strategy Lab verification workflow payload.

    The workflow is research-only: it can create evidence and review tasks, but
    it cannot place broker orders or mutate holdings.
    """
    clean_bars = _prepare_bars(bars)
    if clean_bars.empty:
        return _blocked_payload(
            source_id=source_id,
            as_of=as_of,
            evidence_class=evidence_class,
            strategy=strategy,
            model_version=model_version,
            reason="No OHLCV bars were available for strategy verification.",
        )

    backtest_config = config or BacktestConfig()
    result = BacktestEngine(backtest_config).run(clean_bars, strategy)
    strategy_metadata = result.metadata.get("strategy", strategy.metadata())
    symbol = _frame_value(clean_bars, "symbol")
    market = _frame_value(clean_bars, "market")
    interval = _frame_value(clean_bars, "interval")
    first_datetime = _datetime_text(clean_bars["datetime"].min())
    last_datetime = _datetime_text(clean_bars["datetime"].max())
    data_window = {
        "symbol": symbol,
        "market": market,
        "interval": interval,
        "start": first_datetime,
        "end": last_datetime,
        "rows": int(len(clean_bars)),
        "bar_checksum": _bars_checksum(clean_bars),
        "replay_id": replay_id,
    }
    backtest = {
        "metrics": _json_safe(result.metrics),
        "config": asdict(backtest_config),
        "trade_count": int(len(result.trades)),
        "signal_count": int(len(result.signals)),
        "execution_model": result.metadata.get("backtest", {}).get("execution_model", "target_weight_next_bar_open"),
        "reproducibility_hash": _reproducibility_hash(clean_bars, strategy_metadata, backtest_config),
    }
    validation = _validation_summary(result.metrics, result.trades, clean_bars)
    market_feel = _market_feel_section(clean_bars, symbol=symbol, market=market, answer_horizon=answer_horizon)
    decision = _decision_object(
        source_id=source_id,
        as_of=as_of,
        evidence_class=evidence_class,
        symbol=symbol,
        strategy_metadata=strategy_metadata,
        backtest=backtest,
        validation=validation,
        market_feel=market_feel,
        model_version=model_version,
    )
    status = "Pass" if validation["risk_status"] in {"Pass", "Watch"} else "Review"
    return {
        "schema": STRATEGY_LAB_WORKFLOW_SCHEMA,
        "workspace": "strategy_lab",
        "workflow_id": decision["decision_id"],
        "status": status,
        "source_id": source_id,
        "as_of": as_of,
        "evidence_class": evidence_class,
        "model_versions": [model_version],
        "data_window": data_window,
        "strategy": _json_safe(strategy_metadata),
        "backtest": backtest,
        "validation": validation,
        "market_feel_training": market_feel,
        "decision": decision,
        "assumptions": [
            "Strategy Lab uses historical bars, replay batches, or sanitized fixtures only.",
            "Backtest output is reproducible for the same bars, strategy version, parameters, and cost model.",
            "Market-feel training hides future bars before the answer reveal.",
            "All outputs are research evidence and require human review before any real-world action.",
        ],
        "safety_boundary": {
            "research_only": True,
            "no_live_trading": True,
            "no_broker_calls": True,
            "no_order_execution": True,
            "human_review_required": True,
        },
        "missing_data_log": market_feel.get("missing_data_log", []),
    }


def record_strategy_lab_workflow(
    store: OperationalStore,
    payload: dict[str, Any],
    *,
    artifact_uri: str = "operational_store:strategy_lab_workflow",
) -> dict[str, str]:
    if payload.get("schema") != STRATEGY_LAB_WORKFLOW_SCHEMA:
        raise ValueError(f"payload schema must be {STRATEGY_LAB_WORKFLOW_SCHEMA}")
    store.initialize()
    source_id = str(payload["source_id"])
    as_of = str(payload["as_of"])
    evidence_class = str(payload["evidence_class"])
    strategy = payload.get("strategy", {})
    data_window = payload.get("data_window", {})
    symbol = str(data_window.get("symbol") or payload.get("decision", {}).get("entity_id") or "UNKNOWN")
    workflow_id = str(payload["workflow_id"])
    evidence_id = f"evidence-{workflow_id}"
    job_id = f"job-{workflow_id}"
    task_id = f"task-{workflow_id}"
    strategy_version = f"{strategy.get('strategy_id', 'strategy')}:{strategy.get('version', '')}"

    store.upsert_source(
        SourceRecord(
            source_id=source_id,
            domain=DataDomain.PUBLIC_SHARED_CANONICAL,
            source_type="strategy_lab_verification",
            uri=artifact_uri,
            as_of=as_of,
            evidence_class=evidence_class,
            title=f"Strategy Lab verification for {symbol}",
            checksum=str(payload.get("backtest", {}).get("reproducibility_hash", "")),
            metadata={
                "workflow_id": workflow_id,
                "strategy": strategy,
                "data_window": data_window,
                "safety_boundary": payload.get("safety_boundary", {}),
            },
        )
    )
    store.upsert_entity(symbol, entity_type="market_symbol", display_name=symbol, canonical_symbol=symbol)
    store.record_evidence(
        EvidenceRecord(
            evidence_id=evidence_id,
            source_id=source_id,
            entity_id=symbol,
            as_of=as_of,
            evidence_class=evidence_class,
            summary=_evidence_summary(payload),
            artifact_uri=artifact_uri,
            model_version=",".join(payload.get("model_versions", ["DisabledProvider"])),
            strategy_version=strategy_version,
            metadata={
                "workflow_id": workflow_id,
                "backtest": payload.get("backtest", {}),
                "validation": payload.get("validation", {}),
                "decision": payload.get("decision", {}),
            },
        )
    )
    store.upsert_job(
        JobRecord(
            job_id=job_id,
            source_id=source_id,
            as_of=as_of,
            job_type="strategy_lab_verification",
            status="completed",
            phase="evidence_recorded",
            progress=1.0,
            artifact_uri=artifact_uri,
            metadata={"workflow_id": workflow_id, "schema": STRATEGY_LAB_WORKFLOW_SCHEMA},
        )
    )
    store.upsert_task(
        TaskRecord(
            task_id=task_id,
            source_id=source_id,
            evidence_id=evidence_id,
            as_of=as_of,
            owner_workspace="strategy_lab",
            action="Review strategy evidence, counter-evidence, and invalidation conditions before reuse.",
            status="open",
            priority="P1",
            human_review_required=True,
            metadata={"workflow_id": workflow_id, "decision": payload.get("decision", {})},
        )
    )
    return {"source_id": source_id, "evidence_id": evidence_id, "job_id": job_id, "task_id": task_id}


def build_phase_b_strategy_lab_contract() -> dict[str, Any]:
    return {
        "schema": "PFIOSPhaseBStrategyLabContractV1",
        "workflow_schema": STRATEGY_LAB_WORKFLOW_SCHEMA,
        "workspace": "strategy_lab",
        "required_steps": [
            "load_replay_or_sanitized_bars",
            "run_approved_strategy_backtest",
            "record_reproducibility_hash",
            "build_market_feel_training_case",
            "publish_evidence_and_review_task",
        ],
        "required_fact_fields": ["source_id", "as_of", "evidence_class"],
        "decision_contract_fields": [
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
        ],
        "non_regression_constraints": {
            "market_feel_training_retained": True,
            "strategy_backtesting_core": True,
            "no_live_trading": True,
            "human_review_required": True,
            "llm_required": False,
        },
    }


def _prepare_bars(bars: pd.DataFrame) -> pd.DataFrame:
    required = {"datetime", "symbol", "open", "high", "low", "close", "volume"}
    missing = required - set(bars.columns)
    if missing:
        raise ValueError(f"Strategy Lab bars missing columns: {', '.join(sorted(missing))}")
    data = bars.copy()
    data["datetime"] = pd.to_datetime(data["datetime"], errors="coerce")
    data = data.dropna(subset=["datetime", "open", "high", "low", "close", "volume"])
    return data.sort_values("datetime").reset_index(drop=True)


def _blocked_payload(
    *,
    source_id: str,
    as_of: str,
    evidence_class: str,
    strategy: Strategy,
    model_version: str,
    reason: str,
) -> dict[str, Any]:
    strategy_metadata = strategy.metadata()
    workflow_id = _stable_id("strategy-lab-blocked", source_id, as_of, strategy_metadata)
    return {
        "schema": STRATEGY_LAB_WORKFLOW_SCHEMA,
        "workspace": "strategy_lab",
        "workflow_id": workflow_id,
        "status": "Blocked",
        "source_id": source_id,
        "as_of": as_of,
        "evidence_class": evidence_class,
        "model_versions": [model_version],
        "strategy": _json_safe(strategy_metadata),
        "data_window": {"rows": 0},
        "backtest": {},
        "validation": {"risk_status": "Blocked", "notes": reason},
        "market_feel_training": {"status": "Skipped", "missing_data_log": [{"dataset": "market_feel_training", "status": "Missing", "message": reason}]},
        "decision": {},
        "assumptions": [],
        "safety_boundary": {"research_only": True, "no_live_trading": True, "no_broker_calls": True, "no_order_execution": True, "human_review_required": True},
        "missing_data_log": [{"dataset": "ohlcv", "status": "Missing", "message": reason}],
    }


def _market_feel_section(clean_bars: pd.DataFrame, *, symbol: str, market: str, answer_horizon: int) -> dict[str, Any]:
    if len(clean_bars) < 60 + int(answer_horizon):
        return {
            "status": "Skipped",
            "future_bars_hidden": True,
            "missing_data_log": [
                {
                    "dataset": "market_feel_training",
                    "status": "InsufficientData",
                    "message": "Market-feel training requires at least 60 visible bars plus the answer horizon.",
                }
            ],
        }
    case = market_feel_training_case(clean_bars, symbol=symbol, market=market, answer_horizon=answer_horizon)
    return {
        "status": "Pass",
        "future_bars_hidden": True,
        "answer_horizon": int(case.answer_horizon),
        "visible_until": case.result.latest_date,
        "hidden_start_date": case.hidden_start_date,
        "hidden_end_date": case.hidden_end_date,
        "technical_expected_direction": case.technical_expected_direction,
        "actual_direction": case.actual_direction,
        "technical_alignment": case.technical_alignment,
        "market_feel_score": float(case.result.market_feel_score),
        "pre_result_analysis": case.pre_result_analysis,
        "post_result_review": case.post_result_review,
        "fairness_note": case.fairness_note,
        "missing_data_log": [],
    }


def _validation_summary(metrics: dict[str, Any], trades: pd.DataFrame, bars: pd.DataFrame) -> dict[str, Any]:
    total_return = float(metrics.get("total_return", 0.0) or 0.0)
    max_drawdown = float(metrics.get("max_drawdown", 0.0) or 0.0)
    sharpe = float(metrics.get("sharpe", 0.0) or 0.0)
    trade_count = int(len(trades))
    if len(bars) < 120:
        status = "Review"
        notes = "Sample is short; require more data before operational reuse."
    elif max_drawdown <= -0.35:
        status = "Failed"
        notes = "Maximum drawdown is too deep for a default research candidate."
    elif sharpe < 0 or total_return < -0.05:
        status = "Watch"
        notes = "Performance is weak; keep as research evidence only."
    else:
        status = "Pass"
        notes = "Backtest is usable as research evidence after human review."
    return {
        "risk_status": status,
        "notes": notes,
        "trade_count": trade_count,
        "checks": {
            "has_metrics": bool(metrics),
            "has_cost_model": True,
            "has_trade_log": trade_count > 0,
            "long_only_default": True,
            "sample_rows": int(len(bars)),
        },
    }


def _decision_object(
    *,
    source_id: str,
    as_of: str,
    evidence_class: str,
    symbol: str,
    strategy_metadata: dict[str, Any],
    backtest: dict[str, Any],
    validation: dict[str, Any],
    market_feel: dict[str, Any],
    model_version: str,
) -> dict[str, Any]:
    strategy_id = str(strategy_metadata.get("strategy_id", "strategy"))
    version = str(strategy_metadata.get("version", ""))
    decision_id = _stable_id("strategy-lab", source_id, as_of, strategy_metadata, backtest.get("reproducibility_hash", ""))
    confidence = _confidence(validation, market_feel)
    return {
        "decision_id": decision_id,
        "entity_id": symbol,
        "action": "review_strategy_candidate",
        "horizon": "research_only_backtest_window",
        "target_weight_change": 0.0,
        "status": "ReviewRequired",
        "confidence": confidence,
        "evidence_class": evidence_class,
        "as_of": as_of,
        "thesis": [
            f"Strategy {strategy_id} {version} was tested on a deterministic historical bar window.",
            "The run includes cost, slippage, drawdown, trade count, and reproducibility metadata.",
        ],
        "catalysts": [
            "Use only after comparing with fresh data, benchmark behavior, and strategy-library approval state.",
        ],
        "counter_evidence": [
            validation["notes"],
            "A single backtest window can overfit and does not prove future edge.",
            "Market-feel training is a human pattern-recognition exercise, not a trading signal.",
        ],
        "invalidation_conditions": [
            "Replay checksum, strategy version, parameters, or cost model changes.",
            "Out-of-sample, walk-forward, or live-paper observation materially disagrees with this run.",
            "Data source freshness, coverage, or corporate-action adjustment is later rejected.",
        ],
        "risks": [
            "Backtest bias",
            "Regime dependency",
            "Execution cost sensitivity",
            "Insufficient human review",
        ],
        "portfolio_effect": {
            "estimated_return": float(backtest.get("metrics", {}).get("total_return", 0.0) or 0.0),
            "estimated_max_drawdown": float(backtest.get("metrics", {}).get("max_drawdown", 0.0) or 0.0),
            "no_private_holdings_used": True,
        },
        "model_versions": [model_version],
        "source_ids": [source_id],
        "human_review_required": True,
    }


def _confidence(validation: dict[str, Any], market_feel: dict[str, Any]) -> float:
    base = 0.55
    if validation.get("risk_status") == "Pass":
        base += 0.15
    elif validation.get("risk_status") in {"Failed", "Blocked"}:
        base -= 0.2
    if market_feel.get("status") == "Pass":
        base += 0.05
    return round(min(max(base, 0.0), 0.85), 2)


def _evidence_summary(payload: dict[str, Any]) -> str:
    strategy_id = payload.get("strategy", {}).get("strategy_id", "strategy")
    symbol = payload.get("data_window", {}).get("symbol", "symbol")
    metrics = payload.get("backtest", {}).get("metrics", {})
    total_return = float(metrics.get("total_return", 0.0) or 0.0)
    max_drawdown = float(metrics.get("max_drawdown", 0.0) or 0.0)
    return f"{strategy_id} verification for {symbol}: return={total_return:.4f}, max_drawdown={max_drawdown:.4f}."


def _bars_checksum(bars: pd.DataFrame) -> str:
    columns = [column for column in ["datetime", "symbol", "market", "interval", "open", "high", "low", "close", "volume"] if column in bars.columns]
    normalized = bars[columns].copy()
    normalized["datetime"] = pd.to_datetime(normalized["datetime"]).dt.strftime("%Y-%m-%dT%H:%M:%S")
    csv_text = normalized.to_csv(index=False)
    return hashlib.sha256(csv_text.encode("utf-8")).hexdigest()


def _reproducibility_hash(bars: pd.DataFrame, strategy_metadata: dict[str, Any], config: BacktestConfig) -> str:
    return _stable_id("repro", _bars_checksum(bars), strategy_metadata, asdict(config))


def _stable_id(*parts: Any) -> str:
    payload = json.dumps(_json_safe(parts), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


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
            return value.item()
        except Exception:
            return str(value)
    return value


def _datetime_text(value: Any) -> str:
    if value is None or pd.isna(value):
        return ""
    return pd.Timestamp(value).isoformat()


def _frame_value(frame: pd.DataFrame, column: str) -> str:
    if column not in frame or frame.empty:
        return ""
    values = [str(item) for item in frame[column].dropna().unique()]
    return values[0] if values else ""
