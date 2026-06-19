from __future__ import annotations

import math

import pandas as pd


def max_drawdown(equity: pd.Series) -> float:
    if equity.empty:
        return 0.0
    peak = equity.cummax()
    drawdown = equity / peak - 1
    return float(drawdown.min())


def drawdown_curve(equity: pd.Series) -> pd.Series:
    if equity.empty:
        return equity.copy()
    return equity / equity.cummax() - 1


def performance_metrics(
    equity_curve: pd.DataFrame,
    trades: pd.DataFrame,
    initial_cash: float,
    annualization: int = 252,
) -> dict[str, float | int]:
    if equity_curve.empty:
        return {}
    equity = equity_curve["equity"]
    returns = equity.pct_change().fillna(0.0)
    total_return = equity.iloc[-1] / initial_cash - 1
    periods = max(len(equity_curve), 1)
    annualized_return = (1 + total_return) ** (annualization / periods) - 1 if total_return > -1 else -1
    volatility = returns.std() * math.sqrt(annualization)
    sharpe = (returns.mean() * annualization / volatility) if volatility else 0.0
    downside = returns[returns < 0].std() * math.sqrt(annualization)
    sortino = (returns.mean() * annualization / downside) if downside else 0.0
    mdd = max_drawdown(equity)
    calmar = annualized_return / abs(mdd) if mdd else 0.0

    round_trips = _round_trip_pnls(trades)
    wins = [p for p in round_trips if p > 0]
    losses = [p for p in round_trips if p < 0]
    win_rate = len(wins) / len(round_trips) if round_trips else 0.0
    average_gain = sum(wins) / len(wins) if wins else 0.0
    average_loss = sum(losses) / len(losses) if losses else 0.0
    turnover = trades["notional"].abs().sum() / initial_cash if not trades.empty else 0.0
    cost_column = "execution_cost" if not trades.empty and "execution_cost" in trades.columns else "cost"
    cost_total = trades[cost_column].sum() if not trades.empty else 0.0
    buy_count = int((trades["side"] == "BUY").sum()) if not trades.empty and "side" in trades.columns else 0
    sell_count = int((trades["side"] == "SELL").sum()) if not trades.empty and "side" in trades.columns else 0

    return {
        "total_return": float(total_return),
        "annualized_return": float(annualized_return),
        "volatility": float(volatility),
        "sharpe": float(sharpe),
        "sortino": float(sortino),
        "calmar": float(calmar),
        "max_drawdown": float(mdd),
        "win_rate": float(win_rate),
        "trade_count": int(len(trades)),
        "buy_count": buy_count,
        "sell_count": sell_count,
        "round_trip_count": int(len(round_trips)),
        "turnover": float(turnover),
        "average_gain": float(average_gain),
        "average_loss": float(average_loss),
        "cost_total": float(cost_total),
        "ending_equity": float(equity.iloc[-1]),
    }


def _round_trip_pnls(trades: pd.DataFrame) -> list[float]:
    if trades.empty:
        return []
    position = 0.0
    avg_cost = 0.0
    realized = []
    for row in trades.itertuples(index=False):
        qty = float(row.quantity)
        price = float(row.price)
        signed_qty = qty
        if signed_qty > 0:
            new_position = position + signed_qty
            avg_cost = ((position * avg_cost) + (signed_qty * price)) / new_position if new_position else 0.0
            position = new_position
        elif signed_qty < 0 and position > 0:
            sell_qty = min(abs(signed_qty), position)
            realized.append((price - avg_cost) * sell_qty - float(row.cost))
            position -= sell_qty
            if position <= 0:
                position = 0.0
                avg_cost = 0.0
    return realized
