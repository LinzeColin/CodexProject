from __future__ import annotations

import math
from dataclasses import dataclass

import pandas as pd

from pfi_os.backtest import BacktestResult


@dataclass(frozen=True)
class StrategyDiagnostics:
    trade_quality: pd.DataFrame
    cost_sensitivity: pd.DataFrame
    regime_breakdown: pd.DataFrame
    failure_checks: pd.DataFrame
    round_trips: pd.DataFrame


def build_strategy_diagnostics(result: BacktestResult) -> StrategyDiagnostics:
    round_trips = round_trip_frame(result.trades)
    trade_quality = trade_quality_frame(round_trips, result.trades)
    cost_sensitivity = cost_sensitivity_frame(result)
    regime_breakdown = market_regime_breakdown(result)
    failure_checks = failure_check_frame(result, trade_quality, cost_sensitivity, regime_breakdown)
    return StrategyDiagnostics(
        trade_quality=trade_quality,
        cost_sensitivity=cost_sensitivity,
        regime_breakdown=regime_breakdown,
        failure_checks=failure_checks,
        round_trips=round_trips,
    )


def round_trip_frame(trades: pd.DataFrame) -> pd.DataFrame:
    if trades is None or trades.empty:
        return pd.DataFrame(columns=_ROUND_TRIP_COLUMNS)
    frame = trades.copy().sort_values("datetime").reset_index(drop=True)
    position = 0.0
    avg_cost_per_unit = 0.0
    open_dt = None
    rows = []
    for row in frame.itertuples(index=False):
        quantity = float(getattr(row, "quantity", 0.0) or 0.0)
        price = float(getattr(row, "price", 0.0) or 0.0)
        execution_cost = float(getattr(row, "execution_cost", getattr(row, "cost", 0.0)) or 0.0)
        timestamp = pd.Timestamp(getattr(row, "datetime"))
        symbol = str(getattr(row, "symbol", ""))
        if quantity > 0:
            buy_cost_per_unit = (quantity * price + execution_cost) / quantity if quantity else price
            new_position = position + quantity
            avg_cost_per_unit = ((position * avg_cost_per_unit) + (quantity * buy_cost_per_unit)) / new_position if new_position else 0.0
            position = new_position
            if open_dt is None:
                open_dt = timestamp
        elif quantity < 0 and position > 0:
            closed_quantity = min(abs(quantity), position)
            basis = closed_quantity * avg_cost_per_unit
            proceeds = closed_quantity * price
            net_pnl = proceeds - basis - execution_cost
            holding_days = max((timestamp - open_dt).days, 0) if open_dt is not None else 0
            rows.append(
                {
                    "open_datetime": open_dt,
                    "close_datetime": timestamp,
                    "symbol": symbol,
                    "quantity": closed_quantity,
                    "entry_cost_per_unit": avg_cost_per_unit,
                    "exit_price": price,
                    "net_pnl": net_pnl,
                    "return": net_pnl / basis if basis else 0.0,
                    "holding_days": holding_days,
                }
            )
            position -= closed_quantity
            if position <= 1e-8:
                position = 0.0
                avg_cost_per_unit = 0.0
                open_dt = None
    return pd.DataFrame(rows, columns=_ROUND_TRIP_COLUMNS)


def trade_quality_frame(round_trips: pd.DataFrame, trades: pd.DataFrame | None = None) -> pd.DataFrame:
    trade_count = 0 if trades is None or trades.empty else len(trades)
    if round_trips is None or round_trips.empty:
        return pd.DataFrame(
            [
                _quality_row("交易次数", "Trade Count", trade_count, "number"),
                _quality_row("完成回合", "Completed Round Trips", 0, "number"),
                _quality_row("盈利回合占比", "Profitable Round Trip Rate", 0.0, "percent"),
            ]
        )
    pnl = pd.to_numeric(round_trips["net_pnl"], errors="coerce").fillna(0.0)
    returns = pd.to_numeric(round_trips["return"], errors="coerce").fillna(0.0)
    wins = pnl[pnl > 0]
    losses = pnl[pnl < 0]
    gross_profit = float(wins.sum())
    gross_loss = abs(float(losses.sum()))
    payoff_ratio = (float(wins.mean()) / abs(float(losses.mean()))) if not wins.empty and not losses.empty and losses.mean() else 0.0
    profit_factor = gross_profit / gross_loss if gross_loss else (math.inf if gross_profit > 0 else 0.0)
    rows = [
        _quality_row("交易次数", "Trade Count", trade_count, "number"),
        _quality_row("完成回合", "Completed Round Trips", len(round_trips), "number"),
        _quality_row("盈利回合占比", "Profitable Round Trip Rate", float((pnl > 0).mean()), "percent"),
        _quality_row("平均单回合收益", "Average Round Trip Return", float(returns.mean()), "percent"),
        _quality_row("平均单回合损益", "Average Round Trip PnL", float(pnl.mean()), "currency"),
        _quality_row("盈利因子", "Profit Factor", profit_factor, "number"),
        _quality_row("盈亏比", "Payoff Ratio", payoff_ratio, "number"),
        _quality_row("平均持仓天数", "Average Holding Days", float(round_trips["holding_days"].mean()), "number"),
        _quality_row("最大单回合盈利", "Largest Winning Round Trip", float(pnl.max()), "currency"),
        _quality_row("最大单回合亏损", "Largest Losing Round Trip", float(pnl.min()), "currency"),
        _quality_row("连续亏损回合", "Consecutive Losing Round Trips", _max_consecutive_losses(pnl), "number"),
    ]
    return pd.DataFrame(rows)


def cost_sensitivity_frame(result: BacktestResult, multipliers: tuple[float, ...] = (1.0, 2.0, 3.0)) -> pd.DataFrame:
    equity = result.equity_curve
    if equity is None or equity.empty:
        return pd.DataFrame(columns=["成本倍数 Cost Multiplier", "调整后总收益 Adjusted Total Return", "额外成本 Additional Cost", "状态 Status"])
    initial_cash = float(result.metadata.get("backtest", {}).get("initial_cash", equity["equity"].iloc[0]))
    ending_equity = float(equity["equity"].iloc[-1])
    base_cost = float(result.metrics.get("cost_total", 0.0) or 0.0)
    rows = []
    for multiplier in multipliers:
        additional_cost = max(multiplier - 1.0, 0.0) * base_cost
        adjusted_equity = ending_equity - additional_cost
        adjusted_return = adjusted_equity / initial_cash - 1.0 if initial_cash else 0.0
        rows.append(
            {
                "成本倍数 Cost Multiplier": f"{multiplier:.1f}x",
                "调整后总收益 Adjusted Total Return": adjusted_return,
                "额外成本 Additional Cost": additional_cost,
                "期末权益 Ending Equity": adjusted_equity,
                "状态 Status": "Pass" if adjusted_return > 0 else "Review",
            }
        )
    return pd.DataFrame(rows)


def market_regime_breakdown(result: BacktestResult) -> pd.DataFrame:
    equity = result.equity_curve[["datetime", "equity"]].copy() if result.equity_curve is not None else pd.DataFrame()
    positions = result.positions[["datetime", "close"]].copy() if result.positions is not None and "close" in result.positions.columns else pd.DataFrame()
    if equity.empty or positions.empty:
        return pd.DataFrame(columns=_REGIME_COLUMNS)
    equity["datetime"] = pd.to_datetime(equity["datetime"])
    positions["datetime"] = pd.to_datetime(positions["datetime"])
    frame = equity.merge(positions.drop_duplicates("datetime"), on="datetime", how="inner").sort_values("datetime")
    if len(frame) < 3:
        return pd.DataFrame(columns=_REGIME_COLUMNS)
    frame["strategy_return"] = pd.to_numeric(frame["equity"], errors="coerce").pct_change().fillna(0.0)
    frame["target_return"] = pd.to_numeric(frame["close"], errors="coerce").pct_change().fillna(0.0)
    frame["volatility"] = frame["target_return"].rolling(20, min_periods=3).std().fillna(frame["target_return"].std() or 0.0)
    frame["direction_regime"] = frame["target_return"].apply(_direction_regime)
    median_vol = float(frame["volatility"].median()) if not frame["volatility"].empty else 0.0
    frame["vol_regime"] = frame["volatility"].apply(lambda value: "高波动 High Volatility" if value >= median_vol and value > 0 else "低波动 Low Volatility")
    rows = []
    for regime_type, column in [("方向 Direction", "direction_regime"), ("波动 Volatility", "vol_regime")]:
        for regime, group in frame.groupby(column, sort=False):
            rows.append(_regime_row(regime_type, regime, group))
    return pd.DataFrame(rows, columns=_REGIME_COLUMNS)


def failure_check_frame(
    result: BacktestResult,
    trade_quality: pd.DataFrame,
    cost_sensitivity: pd.DataFrame,
    regime_breakdown: pd.DataFrame,
) -> pd.DataFrame:
    checks = []
    max_drawdown = float(result.metrics.get("max_drawdown", 0.0) or 0.0)
    checks.append(
        _failure_row(
            "最大回撤",
            "Maximum Drawdown",
            "Review" if max_drawdown <= -0.20 else "Pass",
            f"{max_drawdown:.2%}",
            "回撤超过 20% 时进入复核。 / Review when drawdown is worse than 20%.",
        )
    )
    cost_ratio = _cost_ratio(result)
    checks.append(
        _failure_row(
            "交易摩擦占比",
            "Trading Friction Ratio",
            "Review" if cost_ratio >= 0.08 else "Pass",
            f"{cost_ratio:.2%}",
            "建模交易摩擦超过期末权益 8% 时复核。 / Review when modeled friction exceeds 8% of ending equity.",
        )
    )
    losing_streak = _quality_value(trade_quality, "连续亏损回合")
    checks.append(
        _failure_row(
            "连续亏损",
            "Consecutive Losses",
            "Review" if losing_streak >= 3 else "Pass",
            f"{int(losing_streak)}",
            "连续 3 个以上亏损回合时降低信任度。 / Reduce confidence after 3 or more losing round trips.",
        )
    )
    stressed = cost_sensitivity[cost_sensitivity["状态 Status"] == "Review"] if not cost_sensitivity.empty else pd.DataFrame()
    checks.append(
        _failure_row(
            "成本压力",
            "Cost Stress",
            "Review" if not stressed.empty else "Pass",
            "Fail" if not stressed.empty else "Pass",
            "成本翻倍或三倍后仍应保持正收益。 / Strategy should stay positive under 2x or 3x modeled costs.",
        )
    )
    high_vol = regime_breakdown[regime_breakdown["市场环境 Market Regime"] == "高波动 High Volatility"] if not regime_breakdown.empty else pd.DataFrame()
    high_vol_return = float(high_vol["策略收益 Strategy Return"].iloc[0]) if not high_vol.empty else 0.0
    checks.append(
        _failure_row(
            "高波动表现",
            "High-Volatility Performance",
            "Review" if high_vol_return < 0 else "Pass",
            f"{high_vol_return:.2%}",
            "高波动环境亏损时标记可能失效。 / Flag possible failure when high-volatility periods are negative.",
        )
    )
    return pd.DataFrame(checks)


def _regime_row(regime_type: str, regime: str, group: pd.DataFrame) -> dict[str, object]:
    strategy_return = (1.0 + group["strategy_return"]).prod() - 1.0
    target_return = (1.0 + group["target_return"]).prod() - 1.0
    return {
        "类型 Type": regime_type,
        "市场环境 Market Regime": regime,
        "样本数 Observations": int(len(group)),
        "策略收益 Strategy Return": float(strategy_return),
        "目标收益 Target Return": float(target_return),
        "相对收益 Relative Return": float(strategy_return - target_return),
        "周期胜率 Period Win Rate": float((group["strategy_return"] > 0).mean()),
        "最差单期 Worst Period": float(group["strategy_return"].min()),
    }


def _direction_regime(value: float) -> str:
    if value > 0.001:
        return "上涨 Up"
    if value < -0.001:
        return "下跌 Down"
    return "震荡 Flat"


def _max_consecutive_losses(pnl: pd.Series) -> int:
    longest = 0
    current = 0
    for value in pnl:
        if value < 0:
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return int(longest)


def _quality_row(chinese: str, english: str, value: float | int, value_type: str) -> dict[str, object]:
    return {"中文": chinese, "English": english, "Value": value, "Type": value_type}


def _quality_value(frame: pd.DataFrame, chinese: str) -> float:
    if frame.empty:
        return 0.0
    row = frame[frame["中文"] == chinese]
    if row.empty:
        return 0.0
    return float(row.iloc[0]["Value"])


def _cost_ratio(result: BacktestResult) -> float:
    ending_equity = float(result.metrics.get("ending_equity", 0.0) or 0.0)
    cost_total = float(result.metrics.get("cost_total", 0.0) or 0.0)
    return cost_total / ending_equity if ending_equity else 0.0


def _failure_row(chinese: str, english: str, status: str, evidence: str, action: str) -> dict[str, str]:
    return {
        "检查项 Check": f"{chinese} {english}",
        "状态 Status": status,
        "证据 Evidence": evidence,
        "建议动作 Suggested Action": action,
    }


_ROUND_TRIP_COLUMNS = [
    "open_datetime",
    "close_datetime",
    "symbol",
    "quantity",
    "entry_cost_per_unit",
    "exit_price",
    "net_pnl",
    "return",
    "holding_days",
]

_REGIME_COLUMNS = [
    "类型 Type",
    "市场环境 Market Regime",
    "样本数 Observations",
    "策略收益 Strategy Return",
    "目标收益 Target Return",
    "相对收益 Relative Return",
    "周期胜率 Period Win Rate",
    "最差单期 Worst Period",
]
