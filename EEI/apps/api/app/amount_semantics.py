from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

AMOUNT_SEMANTICS_VERSION = "event-amount-semantics-v1"
NON_AGGREGATABLE_AMOUNT_KINDS = frozenset(
    {"unknown", "unreported", "undisclosed", "not_disclosed"}
)
NON_AGGREGATABLE_CURRENCIES = frozenset({"XXX"})


class AmountSemanticError(ValueError):
    pass


def _decimal(value: Decimal | int | float | str) -> Decimal:
    try:
        amount = value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise AmountSemanticError("amount must be a finite numeric value") from exc
    if not amount.is_finite():
        raise AmountSemanticError("amount must be a finite numeric value")
    return amount


def _period_value(value: date | datetime | str | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    normalized = value.strip()
    if not normalized:
        return None
    try:
        return date.fromisoformat(normalized).isoformat()
    except ValueError as exc:
        raise AmountSemanticError("amount period must use ISO date format") from exc


def event_amount_semantics(
    *,
    amount: Decimal | int | float | str | None,
    currency: str | None,
    amount_kind: str | None,
    period_start: date | datetime | str | None,
    period_end: date | datetime | str | None,
) -> dict[str, Any]:
    normalized_currency = currency.strip().upper() if currency else None
    normalized_kind = amount_kind.strip().lower() if amount_kind else None
    normalized_period_start = _period_value(period_start)
    normalized_period_end = _period_value(period_end)
    if (
        normalized_period_start is not None
        and normalized_period_end is not None
        and normalized_period_start > normalized_period_end
    ):
        raise AmountSemanticError("amount period_start must be <= period_end")

    if amount is None:
        return {
            "schema_version": AMOUNT_SEMANTICS_VERSION,
            "state": "unreported",
            "amount": None,
            "display_amount": None,
            "currency": normalized_currency,
            "amount_kind": normalized_kind,
            "period_start": normalized_period_start,
            "period_end": normalized_period_end,
            "visual_weight": None,
            "width_eligible": False,
            "aggregate_eligible": False,
            "aggregation_key": None,
            "non_aggregation_reason": "amount_unreported",
        }

    numeric_amount = _decimal(amount)
    if not normalized_currency or len(normalized_currency) != 3:
        raise AmountSemanticError("reported amount requires a three-letter currency")
    if not normalized_kind:
        raise AmountSemanticError("reported amount requires amount_kind")

    classified = (
        normalized_kind not in NON_AGGREGATABLE_AMOUNT_KINDS
        and normalized_currency not in NON_AGGREGATABLE_CURRENCIES
    )
    aggregation_key = (
        {
            "currency": normalized_currency,
            "amount_kind": normalized_kind,
            "period_start": normalized_period_start,
            "period_end": normalized_period_end,
        }
        if classified
        else None
    )
    return {
        "schema_version": AMOUNT_SEMANTICS_VERSION,
        "state": "reported" if classified else "reported_unclassified",
        "amount": numeric_amount,
        "display_amount": numeric_amount,
        "currency": normalized_currency,
        "amount_kind": normalized_kind,
        "period_start": normalized_period_start,
        "period_end": normalized_period_end,
        "visual_weight": numeric_amount if classified else None,
        "width_eligible": classified,
        "aggregate_eligible": classified,
        "aggregation_key": aggregation_key,
        "non_aggregation_reason": None if classified else "amount_semantics_unclassified",
    }


def aggregate_event_amounts(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    buckets: dict[tuple[str, str, str | None, str | None], dict[str, Any]] = {}
    unreported_event_ids: list[str] = []
    unclassified_event_ids: list[str] = []
    event_count = 0
    reported_event_count = 0

    for row in rows:
        event_count += 1
        event_id = str(row["id"])
        semantics = event_amount_semantics(
            amount=row.get("amount"),
            currency=row.get("currency"),
            amount_kind=row.get("amount_kind"),
            period_start=row.get("period_start"),
            period_end=row.get("period_end"),
        )
        if semantics["state"] == "unreported":
            unreported_event_ids.append(event_id)
            continue
        reported_event_count += 1
        if not semantics["aggregate_eligible"]:
            unclassified_event_ids.append(event_id)
            continue

        key_payload = semantics["aggregation_key"]
        key = (
            key_payload["currency"],
            key_payload["amount_kind"],
            key_payload["period_start"],
            key_payload["period_end"],
        )
        bucket = buckets.setdefault(
            key,
            {
                **key_payload,
                "total_amount": Decimal("0"),
                "visual_weight_total": Decimal("0"),
                "event_count": 0,
                "event_ids": [],
            },
        )
        bucket["total_amount"] += semantics["amount"]
        bucket["visual_weight_total"] += semantics["visual_weight"]
        bucket["event_count"] += 1
        bucket["event_ids"].append(event_id)

    ordered_buckets = sorted(
        buckets.values(),
        key=lambda item: (
            item["currency"],
            item["amount_kind"],
            item["period_start"] or "",
            item["period_end"] or "",
        ),
    )
    dimensions: list[str] = []
    if len({bucket["currency"] for bucket in ordered_buckets}) > 1:
        dimensions.append("currency")
    if len({bucket["amount_kind"] for bucket in ordered_buckets}) > 1:
        dimensions.append("amount_kind")
    if len(
        {(bucket["period_start"], bucket["period_end"]) for bucket in ordered_buckets}
    ) > 1:
        dimensions.append("period")

    one_comparable_bucket = len(ordered_buckets) == 1 and not unclassified_event_ids
    comparable_reported_total = (
        ordered_buckets[0]["total_amount"] if one_comparable_bucket else None
    )
    return {
        "schema_version": AMOUNT_SEMANTICS_VERSION,
        "event_count": event_count,
        "reported_event_count": reported_event_count,
        "unreported_event_count": len(unreported_event_ids),
        "unclassified_event_count": len(unclassified_event_ids),
        "bucket_count": len(ordered_buckets),
        "buckets": ordered_buckets,
        "unreported_event_ids": sorted(unreported_event_ids),
        "unclassified_event_ids": sorted(unclassified_event_ids),
        "incomparable_dimensions": dimensions,
        "cross_bucket_summation_performed": False,
        "comparable_reported_total_available": one_comparable_bucket,
        "comparable_reported_total": comparable_reported_total,
        "comparable_reported_total_complete": bool(
            one_comparable_bucket and not unreported_event_ids
        ),
        "semantics": {
            "unknown_amount_is_zero": False,
            "unknown_amount_has_visual_weight": False,
            "aggregation_key": ["currency", "amount_kind", "period_start", "period_end"],
            "incomparable_buckets_are_summed": False,
        },
    }
