from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable

import numpy as np
import pandas as pd

from qbvs.backtest import CostModel, compare_to_buy_hold, normalize_ohlcv, run_buy_hold, run_target_weight_backtest
from qbvs.strategies import BehaviorStrategySpec, generate_signals


@dataclass(frozen=True)
class FastScreenConfig:
    initial_cash: float = 100_000.0
    commission_rate: float = 0.001
    slippage_bps: float = 5.0
    market_impact_bps: float = 0.0
    annualization: int = 252

    def cost_model(self) -> CostModel:
        return CostModel(**asdict(self))


def fast_target_weight_backtest(
    bars: pd.DataFrame,
    signals: pd.DataFrame,
    config: FastScreenConfig | None = None,
) -> dict[str, object]:
    """Vectorized approximation for large-scale screening.

    This intentionally skips trade-lot accounting and intrabar execution details.
    Use it to narrow candidate strategies, then rerun finalists through
    run_target_weight_backtest before treating results as strategy evidence.
    """
    config = config or FastScreenConfig()
    frame = normalize_ohlcv(bars)
    signal_frame = signals[["datetime", "target_weight"]].copy()
    signal_frame["datetime"] = pd.to_datetime(signal_frame["datetime"])
    frame = frame.merge(signal_frame, on="datetime", how="left")
    frame["target_weight"] = frame["target_weight"].ffill().fillna(0.0).clip(0.0, 1.0)

    close = frame["close"].astype(float).to_numpy()
    target = frame["target_weight"].astype(float).shift(1).fillna(0.0).to_numpy()
    returns = np.zeros(len(close), dtype=float)
    valid = close[:-1] != 0
    returns[1:][valid] = close[1:][valid] / close[:-1][valid] - 1.0

    turnover = np.abs(np.diff(target, prepend=0.0))
    cost_rate = config.commission_rate + (config.slippage_bps + config.market_impact_bps) / 10_000
    strategy_returns = target * returns - turnover * cost_rate
    strategy_returns = np.clip(strategy_returns, -0.999999, None)
    equity_values = config.initial_cash * np.cumprod(1.0 + strategy_returns)

    equity = pd.DataFrame(
        {
            "datetime": frame["datetime"],
            "close": frame["close"],
            "equity": equity_values,
            "target_weight": target,
            "return": strategy_returns,
        }
    )
    equity["drawdown"] = _drawdown_array(equity_values)
    metrics = fast_performance_metrics(equity_values, strategy_returns, turnover, config)
    return {"equity": equity, "metrics": metrics}


def fast_buy_hold(bars: pd.DataFrame, config: FastScreenConfig | None = None) -> dict[str, object]:
    config = config or FastScreenConfig()
    frame = normalize_ohlcv(bars)
    signals = pd.DataFrame({"datetime": frame["datetime"], "target_weight": 1.0})
    return fast_target_weight_backtest(frame, signals, config)


def fast_performance_metrics(
    equity: np.ndarray,
    returns: np.ndarray,
    turnover: np.ndarray,
    config: FastScreenConfig,
) -> dict[str, object]:
    start = float(config.initial_cash)
    end = float(equity[-1])
    total_return = end / start - 1.0
    periods = max(1, len(equity) - 1)
    annualized_return = (1 + total_return) ** (config.annualization / periods) - 1 if end > 0 else -1.0
    drawdowns = _drawdown_array(equity)
    volatility = float(np.std(returns, ddof=0) * np.sqrt(config.annualization))
    sharpe = float(annualized_return / volatility) if volatility > 1e-12 else 0.0
    var_5 = float(np.quantile(returns, 0.05))
    tail = returns[returns <= var_5]
    cvar_5 = float(np.mean(tail)) if len(tail) else var_5
    changed = turnover > 1e-12
    trade_count = int(changed.sum())
    commission_total = float(np.sum(turnover * start * config.commission_rate))
    return {
        "total_return": float(total_return),
        "annualized_return": float(annualized_return),
        "max_drawdown": float(np.min(drawdowns)),
        "volatility": volatility,
        "sharpe": sharpe,
        "var_5": var_5,
        "cvar_5": cvar_5,
        "trade_count": trade_count,
        "commission_total": commission_total,
        "turnover": float(np.sum(turnover)),
    }


def fast_validate_one(
    frame: pd.DataFrame,
    spec: BehaviorStrategySpec,
    config: FastScreenConfig | None = None,
) -> dict[str, object]:
    config = config or FastScreenConfig()
    bars = normalize_ohlcv(frame)
    signals = generate_signals(bars, spec)
    strategy = fast_target_weight_backtest(bars, signals, config)
    benchmark = fast_buy_hold(bars, config)
    comparison = compare_to_buy_hold(strategy["metrics"], benchmark["metrics"])
    return {
        "strategy_id": spec.strategy_id,
        "symbol": str(bars["symbol"].iloc[0]),
        "market": str(bars["market"].iloc[0]),
        "start": str(pd.Timestamp(bars["datetime"].iloc[0]).date()),
        "end": str(pd.Timestamp(bars["datetime"].iloc[-1]).date()),
        "bars": int(len(bars)),
        "engine": "fast_screen",
        **{f"strategy_{k}": v for k, v in strategy["metrics"].items()},
        **{f"buy_hold_{k}": v for k, v in benchmark["metrics"].items()},
        **comparison,
    }


def fast_validate_universe(
    data_by_symbol: dict[str, pd.DataFrame],
    specs: Iterable[BehaviorStrategySpec],
    config: FastScreenConfig | None = None,
) -> pd.DataFrame:
    rows = []
    for spec in specs:
        for symbol, frame in data_by_symbol.items():
            try:
                rows.append(fast_validate_one(frame, spec, config))
            except Exception as exc:
                rows.append({"strategy_id": spec.strategy_id, "symbol": symbol, "engine": "fast_screen", "error": str(exc)})
    return pd.DataFrame(rows)


def compare_fast_to_exact(
    frame: pd.DataFrame,
    specs: Iterable[BehaviorStrategySpec],
    config: FastScreenConfig | None = None,
) -> pd.DataFrame:
    config = config or FastScreenConfig()
    rows = []
    bars = normalize_ohlcv(frame)
    exact_benchmark = run_buy_hold(bars, config.cost_model())["metrics"]
    fast_benchmark = fast_buy_hold(bars, config)["metrics"]
    for spec in specs:
        signals = generate_signals(bars, spec)
        exact = run_target_weight_backtest(bars, signals, config.cost_model())["metrics"]
        fast = fast_target_weight_backtest(bars, signals, config)["metrics"]
        rows.append(
            {
                "strategy_id": spec.strategy_id,
                "symbol": str(bars["symbol"].iloc[0]),
                "market": str(bars["market"].iloc[0]),
                "exact_total_return": exact["total_return"],
                "fast_total_return": fast["total_return"],
                "total_return_abs_diff": abs(float(exact["total_return"]) - float(fast["total_return"])),
                "exact_annualized_return": exact["annualized_return"],
                "fast_annualized_return": fast["annualized_return"],
                "annualized_return_abs_diff": abs(float(exact["annualized_return"]) - float(fast["annualized_return"])),
                "exact_max_drawdown": exact["max_drawdown"],
                "fast_max_drawdown": fast["max_drawdown"],
                "drawdown_abs_diff": abs(float(exact["max_drawdown"]) - float(fast["max_drawdown"])),
                "exact_buy_hold_total_return": exact_benchmark["total_return"],
                "fast_buy_hold_total_return": fast_benchmark["total_return"],
            }
        )
    return pd.DataFrame(rows)


def fast_summary(results: pd.DataFrame) -> pd.DataFrame:
    if results.empty:
        return pd.DataFrame()
    if "error" in results.columns:
        valid = results[results["error"].fillna("").astype(str).str.len() == 0].copy()
    else:
        valid = results.copy()
    if valid.empty:
        return pd.DataFrame()
    grouped = valid.groupby("strategy_id", dropna=False)
    summary = grouped.agg(
        samples=("symbol", "count"),
        pass_rate=("passes_user_floor", "mean"),
        avg_total_gap=("total_return_gap", "mean"),
        median_total_gap=("total_return_gap", "median"),
        avg_annualized_gap=("annualized_return_gap", "mean"),
        avg_drawdown_improvement=("drawdown_improvement", "mean"),
        avg_strategy_return=("strategy_total_return", "mean"),
        avg_buy_hold_return=("buy_hold_total_return", "mean"),
        avg_var_5=("strategy_var_5", "mean"),
        avg_cvar_5=("strategy_cvar_5", "mean"),
        avg_turnover=("strategy_turnover", "mean"),
        avg_trades=("strategy_trade_count", "mean"),
    ).reset_index()
    return summary.sort_values(
        ["pass_rate", "avg_annualized_gap", "avg_drawdown_improvement", "avg_total_gap"],
        ascending=[False, False, False, False],
    )


def benchmark_summary(comparison: pd.DataFrame) -> pd.DataFrame:
    if comparison.empty:
        return pd.DataFrame()
    return pd.DataFrame(
        [
            {
                "strategy_id": "fast_vs_exact_engine",
                "samples": len(comparison),
                "pass_rate": float((comparison["total_return_abs_diff"] <= 0.05).mean()),
                "avg_total_gap": float(comparison["total_return_abs_diff"].mean()),
                "avg_annualized_gap": float(comparison["annualized_return_abs_diff"].mean()),
                "avg_drawdown_improvement": float(comparison["drawdown_abs_diff"].mean()),
                "avg_var_5": 0.0,
                "avg_cvar_5": 0.0,
            }
        ]
    )


def _drawdown_array(equity: np.ndarray) -> np.ndarray:
    running_max = np.maximum.accumulate(equity)
    running_max = np.where(running_max == 0, np.nan, running_max)
    drawdowns = equity / running_max - 1.0
    return np.nan_to_num(drawdowns, nan=0.0)
