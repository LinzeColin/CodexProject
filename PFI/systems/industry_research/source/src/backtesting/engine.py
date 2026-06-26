from __future__ import annotations

from collections import defaultdict
from math import sqrt
from statistics import mean, pstdev


def run_equal_weight_backtest(
    price_rows: list[dict[str, str]],
    symbols: list[str],
    commission: float = 0.0003,
    tax: float = 0.001,
    slippage: float = 0.0005,
) -> dict[str, object]:
    by_date: dict[str, dict[str, float]] = defaultdict(dict)
    for row in price_rows:
        if row["symbol"] in symbols:
            by_date[row["date"]][row["symbol"]] = float(row["close"])

    dates = sorted(date for date, values in by_date.items() if all(symbol in values for symbol in symbols))
    if len(dates) < 2 or not symbols:
        return {"metrics": {}, "equity_curve": []}

    equity = 1.0
    curve = [{"date": dates[0], "equity": equity, "daily_return": 0.0}]
    daily_returns: list[float] = []
    total_cost = commission + tax + slippage
    for prev_date, date in zip(dates, dates[1:]):
        symbol_returns = [
            by_date[date][symbol] / by_date[prev_date][symbol] - 1 for symbol in symbols
        ]
        gross_return = mean(symbol_returns)
        net_return = gross_return - total_cost / max(len(dates) - 1, 1)
        equity *= 1 + net_return
        daily_returns.append(net_return)
        curve.append({"date": date, "equity": round(equity, 6), "daily_return": round(net_return, 6)})

    running_peak = 1.0
    max_drawdown = 0.0
    for point in curve:
        running_peak = max(running_peak, float(point["equity"]))
        drawdown = float(point["equity"]) / running_peak - 1
        max_drawdown = min(max_drawdown, drawdown)

    annual_return = equity ** (252 / len(daily_returns)) - 1
    annual_vol = pstdev(daily_returns) * sqrt(252) if len(daily_returns) > 1 else 0.0
    sharpe = annual_return / annual_vol if annual_vol else 0.0
    calmar = annual_return / abs(max_drawdown) if max_drawdown else 0.0
    wins = [ret for ret in daily_returns if ret > 0]
    losses = [ret for ret in daily_returns if ret < 0]
    metrics = {
        "cumulative_return": round(equity - 1, 6),
        "annual_return": round(annual_return, 6),
        "annual_volatility": round(annual_vol, 6),
        "max_drawdown": round(max_drawdown, 6),
        "sharpe_ratio": round(sharpe, 4),
        "calmar_ratio": round(calmar, 4),
        "win_rate": round(len(wins) / len(daily_returns), 6),
        "profit_loss_ratio": round(abs(mean(wins) / mean(losses)), 4) if wins and losses else 0.0,
        "turnover": round(len(symbols) * 2 / len(daily_returns), 6),
        "max_single_trade_loss": round(min(daily_returns), 6),
        "consecutive_losses": _max_consecutive_losses(daily_returns),
        "cost_assumption": {
            "commission": commission,
            "tax": tax,
            "slippage": slippage,
        },
        "data_rules": [
            "仅使用交易日当日及以前数据",
            "样例未覆盖涨跌停、停牌、退市，生产环境需接入交易状态表",
            "样例价格为已复权口径占位",
        ],
    }
    return {"metrics": metrics, "equity_curve": curve}


def _max_consecutive_losses(returns: list[float]) -> int:
    best = current = 0
    for ret in returns:
        if ret < 0:
            current += 1
            best = max(best, current)
        else:
            current = 0
    return best
