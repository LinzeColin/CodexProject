from app.core.discipline import deviation_events
from app.config import Settings


def test_deviation_over_threshold_triggers_rebalance_candidate():
    settings = Settings.load()
    events = deviation_events(
        [
            {
                "asset_code": "FUND001",
                "deviation": 0.011,
            }
        ],
        settings,
    )
    assert len(events) == 1
    assert events[0].severity == "Alert"
    assert "FUND001" in events[0].trigger_reason


def test_deviation_at_one_percent_maintains():
    settings = Settings.load()
    events = deviation_events(
        [
            {
                "asset_code": "FUND001",
                "deviation": 0.01,
            }
        ],
        settings,
    )
    assert events == []
