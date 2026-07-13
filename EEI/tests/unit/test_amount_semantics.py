from __future__ import annotations

from decimal import Decimal

import pytest

from apps.api.app.amount_semantics import (
    AmountSemanticError,
    aggregate_event_amounts,
    event_amount_semantics,
)


def test_unreported_amount_is_null_and_has_no_visual_or_aggregation_weight() -> None:
    semantics = event_amount_semantics(
        amount=None,
        currency=None,
        amount_kind=None,
        period_start=None,
        period_end=None,
    )

    assert semantics["state"] == "unreported"
    assert semantics["amount"] is None
    assert semantics["display_amount"] is None
    assert semantics["visual_weight"] is None
    assert semantics["width_eligible"] is False
    assert semantics["aggregate_eligible"] is False
    assert semantics["aggregation_key"] is None
    assert semantics["non_aggregation_reason"] == "amount_unreported"


def test_reported_amount_requires_currency_and_amount_kind() -> None:
    with pytest.raises(AmountSemanticError, match="currency"):
        event_amount_semantics(
            amount=100,
            currency=None,
            amount_kind="transaction_value",
            period_start=None,
            period_end=None,
        )
    with pytest.raises(AmountSemanticError, match="amount_kind"):
        event_amount_semantics(
            amount=100,
            currency="USD",
            amount_kind=None,
            period_start=None,
            period_end=None,
        )


def test_unclassified_numeric_amount_is_visible_but_not_used_for_width_or_sum() -> None:
    semantics = event_amount_semantics(
        amount=100,
        currency="USD",
        amount_kind="unknown",
        period_start=None,
        period_end=None,
    )

    assert semantics["state"] == "reported_unclassified"
    assert semantics["display_amount"] == Decimal("100")
    assert semantics["visual_weight"] is None
    assert semantics["width_eligible"] is False
    assert semantics["aggregate_eligible"] is False


def test_same_currency_kind_and_period_aggregate_into_one_bucket() -> None:
    summary = aggregate_event_amounts(
        [
            {
                "id": "event-1",
                "amount": 100,
                "currency": "USD",
                "amount_kind": "period_capex",
                "period_start": "2026-01-01",
                "period_end": "2026-12-31",
            },
            {
                "id": "event-2",
                "amount": 250,
                "currency": "usd",
                "amount_kind": "period_capex",
                "period_start": "2026-01-01",
                "period_end": "2026-12-31",
            },
        ]
    )

    assert summary["bucket_count"] == 1
    assert summary["buckets"][0]["total_amount"] == Decimal("350")
    assert summary["buckets"][0]["event_count"] == 2
    assert summary["comparable_reported_total_available"] is True
    assert summary["comparable_reported_total"] == Decimal("350")
    assert summary["comparable_reported_total_complete"] is True


def test_incomparable_kinds_and_periods_are_separate_without_cross_bucket_total() -> None:
    summary = aggregate_event_amounts(
        [
            {
                "id": "capex",
                "amount": 100,
                "currency": "USD",
                "amount_kind": "period_capex",
                "period_start": "2026-01-01",
                "period_end": "2026-12-31",
            },
            {
                "id": "ceiling",
                "amount": 500,
                "currency": "USD",
                "amount_kind": "award_ceiling",
                "period_start": None,
                "period_end": None,
            },
        ]
    )

    assert summary["bucket_count"] == 2
    assert {bucket["amount_kind"] for bucket in summary["buckets"]} == {
        "period_capex",
        "award_ceiling",
    }
    assert summary["incomparable_dimensions"] == ["amount_kind", "period"]
    assert summary["cross_bucket_summation_performed"] is False
    assert summary["comparable_reported_total_available"] is False
    assert summary["comparable_reported_total"] is None


def test_unreported_event_is_coverage_not_zero_in_reported_total() -> None:
    summary = aggregate_event_amounts(
        [
            {
                "id": "reported",
                "amount": 100,
                "currency": "USD",
                "amount_kind": "transaction_value",
                "period_start": None,
                "period_end": None,
            },
            {
                "id": "unreported",
                "amount": None,
                "currency": None,
                "amount_kind": None,
                "period_start": None,
                "period_end": None,
            },
        ]
    )

    assert summary["event_count"] == 2
    assert summary["reported_event_count"] == 1
    assert summary["unreported_event_count"] == 1
    assert summary["unreported_event_ids"] == ["unreported"]
    assert summary["comparable_reported_total"] == Decimal("100")
    assert summary["comparable_reported_total_complete"] is False
    assert summary["semantics"]["unknown_amount_is_zero"] is False
    assert summary["semantics"]["unknown_amount_has_visual_weight"] is False
