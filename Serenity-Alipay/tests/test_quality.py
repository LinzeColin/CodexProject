from datetime import date, timedelta

from tests.test_scoring import _candidate, _rule, _settings
from app.adapters.manual_sources import PricePoint
from app.core.metrics import calculate_metrics
from app.core.scoring import score_candidate


def test_missing_nav_or_holding_days_triggers_manual_review():
    points = [
        PricePoint("FUNDX", date(2024, 1, 1) + timedelta(days=idx), 1.0 + idx * 0.001)
        for idx in range(760)
    ]
    result = score_candidate(
        _candidate(missing_nav_days=3),
        _rule(),
        calculate_metrics(points),
        {"1m": 0.01, "3m": 0.02, "12m": 0.03, "10d": 0.01},
        {"1m": 0.01, "3m": 0.02, "12m": 0.03, "10d": 0.01},
        _settings(),
    )
    assert result.grade == "Manual Review"
    assert result.manual_review_required is True


def test_official_source_count_below_two_prevents_action_ready():
    points = [
        PricePoint("FUNDX", date(2024, 1, 1) + timedelta(days=idx), 1.0 + idx * 0.001)
        for idx in range(760)
    ]
    result = score_candidate(
        _candidate(official_source_count=1),
        _rule(),
        calculate_metrics(points),
        {"1m": 0.01, "3m": 0.02, "12m": 0.03, "10d": 0.01},
        {"1m": 0.01, "3m": 0.02, "12m": 0.03, "10d": 0.01},
        _settings(),
    )
    assert result.grade != "Action-Ready"
    assert result.action_label == "Pause New"
