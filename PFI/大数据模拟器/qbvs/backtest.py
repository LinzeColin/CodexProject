from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class CostModel:
    initial_cash: float = 100_000.0
    commission_rate: float = 0.001
    slippage_bps: float = 5.0
    market_impact_bps: float = 0.0
    annualization: int = 252


def normalize_ohlcv(data: pd.DataFrame, symbol: str = "UNKNOWN", market: str = "UNKNOWN") -> pd.DataFrame:
    frame = data.copy()
    lower_map = {c: c.lower() for c in frame.columns}
    frame = frame.rename(columns=lower_map)
    if "date" in frame.columns and "datetime" not in frame.columns:
        frame = frame.rename(columns={"date": "datetime"})
    required = {"datetime", "close"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"missing required columns: {missing}")
    frame["datetime"] = pd.to_datetime(frame["datetime"])
    for col in ["open", "high", "low"]:
        if col not in frame.columns:
            frame[col] = frame["close"]
    if "volume" not in frame.columns:
        frame["volume"] = 0.0
    if "symbol" not in frame.columns:
        frame["symbol"] = symbol
    if "market" not in frame.columns:
        frame["market"] = market
    cols = ["datetime", "symbol", "market", "open", "high", "low", "close", "volume"]
    frame = frame[cols].sort_values("datetime").dropna(subset=["close"]).reset_index(drop=True)
    for col in ["open", "high", "low", "close", "volume"]:
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    frame = frame.dropna(subset=["open", "high", "low", "close"]).reset_index(drop=True)
    if len(frame) < 30:
        raise ValueError("not enough bars for validation; need at least 30")
    return frame


def run_target_weight_backtest(
    bars: pd.DataFrame,
    signals: pd.DataFrame,
    cost: CostModel | None = None,
) -> dict[str, Any]:
    cost = cost or CostModel()
    frame = normalize_ohlcv(bars)
    signal_frame = signals[["datetime", "target_weight"]].copy()
    signal_frame["datetime"] = pd.to_datetime(signal_frame["datetime"])
    frame = frame.merge(signal_frame, on="datetime", how="left")
    frame["target_weight"] = frame["target_weight"].ffill().fillna(0.0).clip(0.0, 1.0)
    frame["execution_weight"] = frame["target_weight"].shift(1).fillna(0.0)

    cash = float(cost.initial_cash)
    quantity = 0.0
    rows: list[dict[str, Any]] = []
    trades: list[dict[str, Any]] = []

    for row in frame.itertuples(index=False):
        open_price = float(row.open)
        close_price = float(row.close)
        target_weight = float(row.execution_weight)
        equity_before = cash + quantity * open_price
        target_value = equity_before * target_weight
        current_value = quantity * open_price
        trade_value = target_value - current_value
        if abs(trade_value) > 1e-8 and open_price > 0:
            side = 1 if trade_value > 0 else -1
            execution_bps = cost.slippage_bps + cost.market_impact_bps
            slip_price = open_price * (1 + side * execution_bps / 10_000)
            trade_qty = trade_value / slip_price
            if trade_qty < -quantity:
                trade_qty = -quantity
            notional = trade_qty * slip_price
            commission_cost = max(abs(notional) * cost.commission_rate, 0.0)
            slippage_cost = abs(notional) * cost.slippage_bps / 10_000
            market_impact_cost = abs(notional) * cost.market_impact_bps / 10_000
            cash -= notional + commission_cost
            quantity += trade_qty
            trades.append(
                {
                    "datetime": row.datetime,
                    "side": "BUY" if trade_qty > 0 else "SELL",
                    "quantity": trade_qty,
                    "price": slip_price,
                    "notional": notional,
                    "commission_cost": commission_cost,
                    "slippage_cost": slippage_cost,
                    "market_impact_cost": market_impact_cost,
                    "target_weight": target_weight,
                }
            )
        equity = cash + quantity * close_price
        rows.append(
            {
                "datetime": row.datetime,
                "close": close_price,
                "cash": cash,
                "position_value": quantity * close_price,
                "equity": equity,
                "target_weight": target_weight,
                "actual_weight": (quantity * close_price / equity) if equity else 0.0,
            }
        )

    equity = pd.DataFrame(rows)
    trades_frame = pd.DataFrame(trades)
    equity["return"] = equity["equity"].pct_change().fillna(0.0)
    equity["drawdown"] = drawdown(equity["equity"])
    metrics = performance_metrics(equity, trades_frame, cost)
    return {"equity": equity, "trades": trades_frame, "metrics": metrics}


def run_buy_hold(bars: pd.DataFrame, cost: CostModel | None = None) -> dict[str, Any]:
    cost = cost or CostModel()
    frame = normalize_ohlcv(bars)
    signals = pd.DataFrame({"datetime": frame["datetime"], "target_weight": 1.0})
    return run_target_weight_backtest(frame, signals, cost)


def drawdown(equity: pd.Series) -> pd.Series:
    running_max = equity.cummax().replace(0, np.nan)
    return (equity / running_max - 1.0).fillna(0.0)


def performance_metrics(equity: pd.DataFrame, trades: pd.DataFrame, cost: CostModel) -> dict[str, Any]:
    start = float(cost.initial_cash)
    end = float(equity["equity"].iloc[-1])
    total_return = end / start - 1.0
    periods = max(1, len(equity) - 1)
    annualized_return = (1 + total_return) ** (cost.annualization / periods) - 1 if end > 0 else -1.0
    max_drawdown = float(equity["drawdown"].min())
    returns = equity["return"].astype(float)
    volatility = float(returns.std(ddof=0) * np.sqrt(cost.annualization))
    sharpe = float(annualized_return / volatility) if volatility > 1e-12 else 0.0
    var_5 = float(returns.quantile(0.05))
    cvar_5 = float(returns[returns <= var_5].mean()) if (returns <= var_5).any() else var_5
    trade_count = int(len(trades))
    cost_total = float(trades.get("commission_cost", pd.Series(dtype=float)).sum()) if trade_count else 0.0
    turnover = float(trades.get("notional", pd.Series(dtype=float)).abs().sum() / start) if trade_count else 0.0
    return {
        "total_return": float(total_return),
        "annualized_return": float(annualized_return),
        "max_drawdown": max_drawdown,
        "volatility": volatility,
        "sharpe": sharpe,
        "var_5": var_5,
        "cvar_5": cvar_5,
        "trade_count": trade_count,
        "commission_total": cost_total,
        "turnover": turnover,
    }


def compare_to_buy_hold(strategy_metrics: dict[str, Any], buy_hold_metrics: dict[str, Any]) -> dict[str, float | bool]:
    total_gap = float(strategy_metrics["total_return"] - buy_hold_metrics["total_return"])
    annualized_gap = float(strategy_metrics["annualized_return"] - buy_hold_metrics["annualized_return"])
    drawdown_improvement = float(strategy_metrics["max_drawdown"] - buy_hold_metrics["max_drawdown"])
    return {
        "total_return_gap": total_gap,
        "annualized_return_gap": annualized_gap,
        "drawdown_improvement": drawdown_improvement,
        "passes_user_floor": bool(total_gap >= -0.08 and annualized_gap >= -0.03 and drawdown_improvement >= -0.005),
    }
