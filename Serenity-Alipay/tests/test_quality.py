from datetime import date

from tests.test_scoring import _candidate, _rule, _settings
from app.adapters.manual_sources import PricePoint
from app.core.metrics import calculate_metrics
from app.core.scoring import score_candidate


def test_missing_nav_or_holding_days_triggers_manual_review():
    points = [
        PricePoint("FUNDX", date(2026, 3, 1), 1.0),
        PricePoint("FUNDX", date(2026, 5, 1), 1.2),
        PricePoint("FUNDX", date(2026, 6, 1), 1.4),
    ]
    result = score_candidate(
        _candidate(missing_nav_days=3),
        _rule(),
        calculate_metrics(points),
        {"1m": 0.01, "3m": 0.02, "10d": 0.01},
        {"1m": 0.01, "3m": 0.02, "10d": 0.01},
        _settings(),
    )
    assert result.grade == "Manual Review"
    assert result.manual_review_required is True


def test_official_source_count_below_two_prevents_action_ready():
    points = [
        PricePoint("FUNDX", date(2026, 3, 1), 1.0),
        PricePoint("FUNDX", date(2026, 5, 1), 1.2),
        PricePoint("FUNDX", date(2026, 6, 1), 1.4),
    ]
    result = score_candidate(
        _candidate(official_source_count=1),
        _rule(),
        calculate_metrics(points),
        {"1m": 0.01, "3m": 0.02, "10d": 0.01},
        {"1m": 0.01, "3m": 0.02, "10d": 0.01},
        _settings(),
    )
    assert result.grade != "Action-Ready"
    assert result.action_label == "Pause New"
