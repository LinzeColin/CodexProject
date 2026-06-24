from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date

from app.adapters.manual_sources import Candidate, PricePoint


TRADING_DAYS_PER_YEAR = 252
INDICATOR_FIELDS = ("alpha", "beta", "gamma", "theta", "vega", "sharpe", "sortino", "calmar", "treynor")


@dataclass(frozen=True)
class IndicatorDay:
    metric_date: date
    alpha: float | None
    beta: float | None
    gamma: float | None
    theta: float | None
    vega: float | None
    sharpe: float | None
    sortino: float | None
    calmar: float | None
    treynor: float | None
    negative_indicator_count: int
    total_indicator_count: int
    benchmark_code: str
    benchmark_label: str


@dataclass(frozen=True)
class ExclusionDecision:
    should_exclude: bool
    reason: str | None
    rule_window_days: int | None
    negative_count: int
    threshold_count: int
    total_count: int


def _daily_returns(points: list[PricePoint]) -> dict[date, float]:
    rows: dict[date, float] = {}
    for previous, current in zip(points, points[1:]):
        if previous.close:
            rows[current.date] = current.close / previous.close - 1.0
    return rows


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def _std(values: list[float]) -> float | None:
    if len(values) < 2:
        return None
    avg = sum(values) / len(values)
    variance = sum((value - avg) ** 2 for value in values) / (len(values) - 1)
    return math.sqrt(variance)


def _covariance(left: list[float], right: list[float]) -> float | None:
    if len(left) != len(right) or len(left) < 2:
        return None
    left_avg = sum(left) / len(left)
    right_avg = sum(right) / len(right)
    return sum((l - left_avg) * (r - right_avg) for l, r in zip(left, right)) / (len(left) - 1)


def _beta(asset_returns: list[float], benchmark_returns: list[float]) -> float | None:
    benchmark_std = _std(benchmark_returns)
    if benchmark_std is None or benchmark_std == 0:
        return None
    cov = _covariance(asset_returns, benchmark_returns)
    return None if cov is None else cov / (benchmark_std**2)


def _annualized_return(returns: list[float]) -> float | None:
    avg = _mean(returns)
    return None if avg is None else avg * TRADING_DAYS_PER_YEAR


def _sharpe(returns: list[float]) -> float | None:
    avg = _mean(returns)
    std = _std(returns)
    if avg is None or std is None or std == 0:
        return None
    return avg / std * math.sqrt(TRADING_DAYS_PER_YEAR)


def _sortino(returns: list[float]) -> float | None:
    avg = _mean(returns)
    downside = [value for value in returns if value < 0]
    downside_std = _std(downside)
    if avg is None or downside_std is None or downside_std == 0:
        return None
    return avg / downside_std * math.sqrt(TRADING_DAYS_PER_YEAR)


def _max_drawdown_from_returns(returns: list[float]) -> float | None:
    if not returns:
        return None
    value = 1.0
    peak = 1.0
    worst = 0.0
    for item in returns:
        value *= 1.0 + item
        peak = max(peak, value)
        if peak:
            worst = max(worst, (peak - value) / peak)
    return worst


def _calmar(returns: list[float]) -> float | None:
    annualized = _annualized_return(returns)
    mdd = _max_drawdown_from_returns(returns)
    if annualized is None or mdd is None or mdd == 0:
        return None
    return annualized / mdd


def _window_metric(
    *,
    metric_date: date,
    asset_returns: list[float],
    benchmark_returns: list[float],
    previous_beta: float | None,
    benchmark_code: str,
    benchmark_label: str,
) -> IndicatorDay:
    beta = _beta(asset_returns, benchmark_returns)
    asset_ann = _annualized_return(asset_returns)
    bench_ann = _annualized_return(benchmark_returns)
    alpha = asset_ann - (beta * bench_ann) if asset_ann is not None and beta is not None and bench_ann is not None else None
    excess_returns = [asset - bench for asset, bench in zip(asset_returns, benchmark_returns)]
    theta = _mean(excess_returns[-20:])
    asset_std = _std(asset_returns)
    bench_std = _std(benchmark_returns)
    vega = (asset_std / bench_std - 1.0) if asset_std is not None and bench_std not in (None, 0) else None
    gamma = beta - previous_beta if beta is not None and previous_beta is not None else None
    sharpe = _sharpe(asset_returns)
    sortino = _sortino(asset_returns)
    calmar = _calmar(asset_returns)
    treynor = (asset_ann - bench_ann) / beta if asset_ann is not None and bench_ann is not None and beta not in (None, 0) else None
    values = {
        "alpha": alpha,
        "beta": beta,
        "gamma": gamma,
        "theta": theta,
        "vega": vega,
        "sharpe": sharpe,
        "sortino": sortino,
        "calmar": calmar,
        "treynor": treynor,
    }
    known = [value for value in values.values() if value is not None]
    return IndicatorDay(
        metric_date=metric_date,
        alpha=alpha,
        beta=beta,
        gamma=gamma,
        theta=theta,
        vega=vega,
        sharpe=sharpe,
        sortino=sortino,
        calmar=calmar,
        treynor=treynor,
        negative_indicator_count=sum(1 for value in known if value < 0),
        total_indicator_count=len(known),
        benchmark_code=benchmark_code,
        benchmark_label=benchmark_label,
    )


def _candidate_benchmark(candidate: Candidate, benchmark_history: dict[str, list[PricePoint]]) -> tuple[str, str, list[PricePoint]]:
    text = " ".join([candidate.asset_name, candidate.market, candidate.theme, candidate.asset_type]).lower()
    if any(marker in text for marker in ("qdii", "纳斯达克", "美股", "us", "全球")) and benchmark_history.get("SPX"):
        return "SPX", "标普500", benchmark_history["SPX"]
    if benchmark_history.get("000001.SH"):
        return "000001.SH", "沪指", benchmark_history["000001.SH"]
    for code, points in benchmark_history.items():
        if points:
            return code, code, points
    return "", "无可用基准", []


def calculate_indicator_days(
    candidate: Candidate,
    points: list[PricePoint],
    benchmark_history: dict[str, list[PricePoint]],
    *,
    lookback_days: int = 10,
    rolling_window: int = 63,
) -> list[IndicatorDay]:
    benchmark_code, benchmark_label, benchmark_points = _candidate_benchmark(candidate, benchmark_history)
    asset_daily = _daily_returns(points)
    benchmark_daily = _daily_returns(benchmark_points)
    aligned = [
        (day, asset_daily[day], benchmark_daily[day])
        for day in sorted(asset_daily)
        if day in benchmark_daily
    ]
    if len(aligned) < max(20, rolling_window):
        return []
    result: list[IndicatorDay] = []
    previous_beta: float | None = None
    for end_index in range(max(rolling_window, len(aligned) - lookback_days + 1), len(aligned) + 1):
        window = aligned[end_index - rolling_window : end_index]
        metric = _window_metric(
            metric_date=window[-1][0],
            asset_returns=[item[1] for item in window],
            benchmark_returns=[item[2] for item in window],
            previous_beta=previous_beta,
            benchmark_code=benchmark_code,
            benchmark_label=benchmark_label,
        )
        previous_beta = metric.beta
        result.append(metric)
    return result[-lookback_days:]


def evaluate_exclusion_rule(days: list[IndicatorDay]) -> ExclusionDecision:
    for window_days, ratio in ((5, 0.80), (10, 0.60)):
        if len(days) < window_days:
            continue
        window = days[-window_days:]
        total = sum(day.total_indicator_count for day in window)
        negative = sum(day.negative_indicator_count for day in window)
        threshold = math.ceil(ratio * total)
        if total > 0 and negative >= threshold:
            return ExclusionDecision(
                should_exclude=True,
                reason=(
                    f"连续{window_days}个交易日希腊字母/风险指标负项 {negative}/{total} "
                    f">= {ratio:.0%} 阈值 {threshold}"
                ),
                rule_window_days=window_days,
                negative_count=negative,
                threshold_count=threshold,
                total_count=total,
            )
    total = sum(day.total_indicator_count for day in days[-10:])
    negative = sum(day.negative_indicator_count for day in days[-10:])
    return ExclusionDecision(False, None, None, negative, 0, total)
