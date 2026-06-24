from dataclasses import replace
from datetime import date, timedelta

from app.adapters.manual_sources import Candidate, FundRule, PricePoint
from app.config import Settings
from app.core.metrics import calculate_metrics
from app.core.scoring import score_candidate


def _candidate(**overrides):
    base = Candidate(
        asset_id="FUNDX",
        asset_code="FUNDX",
        asset_name="Aggressive Growth Fund",
        asset_type="off_platform_fund",
        market="CN/US",
        fund_company="Manual",
        risk_level="high",
        theme="AI",
        is_off_platform_fund=True,
        is_excluded=False,
        exclusion_reason="",
        official_source_count=2,
        fallback_aggregated=False,
        evidence_level="Strong",
        source_name="official",
        source_type="official",
        source_url="manual",
        missing_nav_days=0,
        missing_holding_days=0,
        conflict_flag=False,
        as_of="2026-06-12",
    )
    return replace(base, **overrides)


def _rule(**overrides):
    base = FundRule(
        asset_code="FUNDX",
        subscription_status="open",
        redemption_status="open",
        cutoff_time="15:00",
        confirm_lag="T+1",
        redeem_lag="T+3",
        subscription_fee=0.001,
        redemption_fee=0.005,
        management_fee=0.012,
        custody_fee=0.002,
        sales_service_fee=0.0,
        min_purchase_amount=10.0,
        source_name="official",
        source_type="official",
        source_priority=3,
        url_or_path="manual",
        evidence_level="Strong",
        fallback_aggregated=False,
        as_of="2026-06-12",
        subscription_fee_schedule="M<100万元 0.10%",
        redemption_fee_schedule="N<7天 0.50%；N>=7天 0.00%",
        fee_schedule_as_of="2026-06-12",
        fee_schedule_note="synthetic test fixture",
    )
    return replace(base, **overrides)


def _settings():
    return Settings.load()


def test_max_drawdown_40_percent_blocks():
    points = [
        PricePoint("FUNDX", date(2024, 1, 1) + timedelta(days=idx), 1.0)
        for idx in range(760)
    ]
    points[500] = PricePoint("FUNDX", points[500].date, 1.2)
    points[520] = PricePoint("FUNDX", points[520].date, 0.70)
    result = score_candidate(
        _candidate(),
        _rule(),
        calculate_metrics(points),
        {"1m": 0.01, "3m": 0.02, "12m": 0.03, "10d": 0.01},
        {"1m": 0.01, "3m": 0.02, "12m": 0.03, "10d": 0.01},
        _settings(),
    )
    assert result.grade == "Block"
    assert result.action_label == "Clear"
    assert "max_drawdown" in result.hard_block_reason


def test_recovery_365_days_hard_downgrades():
    points = [
        PricePoint("FUNDX", date(2024, 1, 1), 1.4),
        PricePoint("FUNDX", date(2024, 1, 2), 1.0),
        PricePoint("FUNDX", date(2026, 1, 3), 1.2),
    ]
    result = score_candidate(
        _candidate(),
        _rule(),
        calculate_metrics(points),
        {"1m": 0.01, "3m": 0.02, "12m": 0.03, "10d": 0.01},
        {"1m": 0.01, "3m": 0.02, "12m": 0.03, "10d": 0.01},
        _settings(),
    )
    assert result.grade in {"Manual Review", "Block"}
    assert result.manual_review_required is True
    assert "recovery_time_days" in result.hard_block_reason


def test_aggregated_fallback_cannot_be_action_ready():
    points = [
        PricePoint("FUNDX", date(2024, 1, 1) + timedelta(days=idx), 1.0 + idx * 0.001)
        for idx in range(760)
    ]
    result = score_candidate(
        _candidate(fallback_aggregated=True),
        _rule(),
        calculate_metrics(points),
        {"1m": 0.01, "3m": 0.02, "12m": 0.03, "10d": 0.01},
        {"1m": 0.01, "3m": 0.02, "12m": 0.03, "10d": 0.01},
        _settings(),
    )
    assert result.grade != "Action-Ready"
    assert result.action_label == "Pause New"


def test_platform_trade_status_is_advisory_only():
    points = [
        PricePoint("FUNDX", date(2026, 1, 1) + timedelta(days=idx), 1.0 + idx * 0.01)
        for idx in range(760)
    ]
    result = score_candidate(
        _candidate(),
        _rule(
            alipay_trade_status="支付宝交易页待确认",
            moomoo_trade_status="MooMoo未验证场外基金交易",
            platform_trade_note="只作交易路径建议，不参与候选池排除",
        ),
        calculate_metrics(points),
        {"1m": 0.01, "3m": 0.02, "12m": 0.03, "10d": 0.01},
        {"1m": 0.01, "3m": 0.02, "12m": 0.03, "10d": 0.01},
        _settings(),
    )

    assert result.grade == "Action-Ready"
    assert result.action_label == "Increase"
    assert "alipay_trade_status" not in result.missing_fields
    assert "moomoo_trade_status" not in result.missing_fields


def test_limited_subscription_with_complete_fee_rules_is_not_missing_fee_manual_review():
    points = [
        PricePoint("FUNDX", date(2024, 1, 1) + timedelta(days=idx), 1.0 + idx * 0.01)
        for idx in range(760)
    ]
    result = score_candidate(
        _candidate(),
        _rule(subscription_status="limited", redemption_status="open"),
        calculate_metrics(points),
        {"1m": 0.01, "3m": 0.02, "12m": 0.03, "10d": 0.01},
        {"1m": 0.01, "3m": 0.02, "12m": 0.03, "10d": 0.01},
        _settings(),
    )

    assert result.manual_review_required is False
    assert result.grade == "Watch"
    assert result.action_label == "Pause New"
    assert result.executable_score == 7.0
    assert "subscription_status" not in result.missing_fields
    assert "redemption_status" not in result.missing_fields
    assert "subscription_fee_schedule" not in result.missing_fields
    assert "fee/redemption/subscription status missing or closed" not in result.trigger_reason


def test_closed_subscription_still_requires_manual_review():
    points = [
        PricePoint("FUNDX", date(2024, 1, 1) + timedelta(days=idx), 1.0 + idx * 0.01)
        for idx in range(760)
    ]
    result = score_candidate(
        _candidate(),
        _rule(subscription_status="closed", redemption_status="open"),
        calculate_metrics(points),
        {"1m": 0.01, "3m": 0.02, "12m": 0.03, "10d": 0.01},
        {"1m": 0.01, "3m": 0.02, "12m": 0.03, "10d": 0.01},
        _settings(),
    )

    assert result.manual_review_required is True
    assert result.action_label == "Pause New"
    assert result.executable_score == 0.0
    assert "关闭/未知" in result.trigger_reason


def test_missing_24_month_nav_history_prevents_action_ready():
    points = [
        PricePoint("FUNDX", date(2026, 1, 1) + timedelta(days=idx), 1.0 + idx * 0.01)
        for idx in range(120)
    ]
    result = score_candidate(
        _candidate(),
        _rule(),
        calculate_metrics(points),
        {"1m": 0.01, "3m": 0.02, "12m": 0.03, "10d": 0.01},
        {"1m": 0.01, "3m": 0.02, "12m": 0.03, "10d": 0.01},
        _settings(),
    )

    assert result.grade == "Block"
    assert result.action_label == "Block"
    assert "nav_history_24m" in result.missing_fields
    assert "24 months" in result.trigger_reason
