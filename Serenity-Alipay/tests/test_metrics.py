from datetime import date, timedelta

from app.adapters.manual_sources import PricePoint
from app.core.metrics import calculate_returns


def _points(count: int, start: date = date(2026, 6, 1)) -> list[PricePoint]:
    return [
        PricePoint(asset_code="TEST", date=start + timedelta(days=idx), close=100.0 + idx)
        for idx in range(count)
    ]


def test_returns_are_none_when_required_windows_are_not_covered():
    returns = calculate_returns(_points(10))

    assert returns["10d"] is None
    assert returns["1m"] is None
    assert returns["3m"] is None
    assert returns["12m"] is None


def test_returns_use_only_covered_windows():
    returns = calculate_returns(_points(120, start=date(2026, 1, 1)))

    assert returns["10d"] is not None
    assert returns["1m"] is not None
    assert returns["3m"] is not None
    assert returns["12m"] is None


def test_returns_include_twelve_month_window_when_covered():
    returns = calculate_returns(_points(400, start=date(2025, 5, 1)))

    assert returns["12m"] is not None
