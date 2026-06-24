from datetime import date, timedelta

from app.core.indicator_discipline import IndicatorDay, evaluate_exclusion_rule


def _day(idx: int, negative: int, total: int = 9) -> IndicatorDay:
    return IndicatorDay(
        metric_date=date(2026, 6, 1) + timedelta(days=idx),
        alpha=-1.0 if negative > 0 else 1.0,
        beta=-1.0 if negative > 1 else 1.0,
        gamma=-1.0 if negative > 2 else 1.0,
        theta=-1.0 if negative > 3 else 1.0,
        vega=-1.0 if negative > 4 else 1.0,
        sharpe=-1.0 if negative > 5 else 1.0,
        sortino=-1.0 if negative > 6 else 1.0,
        calmar=-1.0 if negative > 7 else 1.0,
        treynor=-1.0 if negative > 8 else 1.0,
        negative_indicator_count=negative,
        total_indicator_count=total,
        benchmark_code="SPX",
        benchmark_label="标普500",
    )


def test_five_day_eighty_percent_negative_indicator_rule_blocks():
    decision = evaluate_exclusion_rule([_day(idx, 8) for idx in range(5)])

    assert decision.should_exclude is True
    assert decision.rule_window_days == 5
    assert decision.negative_count == 40
    assert decision.threshold_count == 36


def test_ten_day_sixty_percent_negative_indicator_rule_blocks_when_five_day_does_not():
    decision = evaluate_exclusion_rule([_day(idx, 6) for idx in range(10)])

    assert decision.should_exclude is True
    assert decision.rule_window_days == 10
    assert decision.negative_count == 60
    assert decision.threshold_count == 54
