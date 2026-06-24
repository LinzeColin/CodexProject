from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from app.adapters.manual_sources import PricePoint


@dataclass(frozen=True)
class AssetMetrics:
    returns: dict[str, float | None]
    max_drawdown: float | None
    recovery_time_days: int | None
    recovered: bool
    drawdown_7d: float | None
    point_count: int
    history_span_days: int | None


WINDOWS = ("1m", "3m", "12m", "10d")


def _return_from_start(points: list[PricePoint], start_index: int) -> float | None:
    if not points or len(points) <= start_index:
        return None
    start = points[start_index].close
    end = points[-1].close
    if start == 0:
        return None
    return (end / start) - 1.0


def _index_for_days(points: list[PricePoint], days: int) -> int | None:
    if not points:
        return None
    target = points[-1].date - timedelta(days=days)
    candidates = [idx for idx, point in enumerate(points) if point.date <= target]
    return max(candidates) if candidates else None


def calculate_returns(points: list[PricePoint]) -> dict[str, float | None]:
    if len(points) < 2:
        return {window: None for window in WINDOWS}
    one_month_idx = _index_for_days(points, 31)
    three_month_idx = _index_for_days(points, 93)
    twelve_month_idx = _index_for_days(points, 365)
    ten_day_idx = len(points) - 11 if len(points) >= 11 else None
    return {
        "1m": _return_from_start(points, one_month_idx) if one_month_idx is not None else None,
        "3m": _return_from_start(points, three_month_idx) if three_month_idx is not None else None,
        "12m": _return_from_start(points, twelve_month_idx) if twelve_month_idx is not None else None,
        "10d": _return_from_start(points, ten_day_idx) if ten_day_idx is not None else None,
    }


def max_drawdown_and_recovery(points: list[PricePoint]) -> tuple[float | None, int | None, bool]:
    if len(points) < 2:
        return None, None, False

    peak = points[0]
    worst_drawdown = 0.0
    worst_peak = points[0]
    worst_trough = points[0]

    for point in points:
        if point.close > peak.close:
            peak = point
        drawdown = (peak.close - point.close) / peak.close if peak.close else 0.0
        if drawdown > worst_drawdown:
            worst_drawdown = drawdown
            worst_peak = peak
            worst_trough = point

    if worst_drawdown == 0.0:
        return 0.0, 0, True

    for point in points:
        if point.date > worst_trough.date and point.close >= worst_peak.close:
            return worst_drawdown, (point.date - worst_trough.date).days, True
    return worst_drawdown, (points[-1].date - worst_trough.date).days, False


def drawdown_over_last_n(points: list[PricePoint], count: int = 7) -> float | None:
    if len(points) < 2:
        return None
    recent = points[-count:]
    peak = max(point.close for point in recent)
    latest = recent[-1].close
    if peak == 0:
        return None
    return (peak - latest) / peak


def calculate_metrics(points: list[PricePoint]) -> AssetMetrics:
    returns = calculate_returns(points)
    mdd, recovery, recovered = max_drawdown_and_recovery(points)
    history_span_days = (points[-1].date - points[0].date).days if len(points) >= 2 else None
    return AssetMetrics(
        returns=returns,
        max_drawdown=mdd,
        recovery_time_days=recovery,
        recovered=recovered,
        drawdown_7d=drawdown_over_last_n(points, 7),
        point_count=len(points),
        history_span_days=history_span_days,
    )
