#!/usr/bin/env python3
"""Executable cross-Phase contract for the KMFA v1.5 S05 Stage Review.

The adapter makes the accepted S05-P1 amount, S05-P2 date, and S05-P3 field
contracts one fail-closed ingestion path.  It is public-safe and does not read
raw files or expose input values in its verification projection.
"""

from __future__ import annotations

import json
from typing import Any

from KMFA.tools import v015_s05_p1_amount_precision as amount
from KMFA.tools import v015_s05_p2_date_period as date_period
from KMFA.tools import v015_s05_p3_field_standardization as fields


RUN_PHASE_ID = "V015_S05_STAGE_REVIEW"
TASK_ID = "KMFA-V015-S05-STAGE-REVIEW-20260715"
ACCEPTANCE_ID = "ACC-KMFA-V015-S05-STAGE-REVIEW"
VERSION = "1.5.0-dev-s05-review"

# S05-P3's dictionary token is deliberately bound to the S05-P1 registered
# canonical cent unit.  Consumers cannot infer or substitute this mapping.
UNIT_BINDINGS = {"CNY_CENT": "fen"}

CHECK_IDS = (
    "AMOUNT_ALIAS_EXACT",
    "AMOUNT_UNIT_BINDING",
    "AMOUNT_INTEGER_CENTS",
    "OBSERVED_ZERO_PRESERVED",
    "FLOAT_AMOUNT_BLOCKED",
    "BLANK_AMOUNT_BLOCKED",
    "LOW_CONFIDENCE_ALIAS_BLOCKED",
    "AMBIGUOUS_ALIAS_BLOCKED",
    "DATE_NORMALIZATION_PRECEDES_STORAGE",
    "DATE_SOURCE_POLICY_REQUIRED",
)


class StageReviewContractError(ValueError):
    """Stable fail-closed Stage-level error."""

    def __init__(self, code: str, message: str, *, action: str = "BLOCK_DERIVATION") -> None:
        super().__init__(message)
        self.code = code
        self.action = action


def _resolve_auto(
    alias: Any,
    *,
    template_class: str | None,
    version: str,
) -> tuple[fields.MappingDecision, fields.FieldDefinition]:
    decision = fields.AliasRegistry().resolve(
        alias,
        template_class=template_class,
        version=version,
    )
    if decision.status != "AUTO_MAPPED" or decision.canonical_field_id is None:
        raise StageReviewContractError(
            "ALIAS_NOT_AUTO_MAPPABLE",
            f"alias decision requires controlled routing: {decision.status}",
            action=decision.action,
        )
    definition = fields.FIELD_BY_ID[decision.canonical_field_id]
    return decision, definition


def _mapping_projection(decision: fields.MappingDecision) -> dict[str, Any]:
    return {
        "field_id": decision.canonical_field_id,
        "mapping_rule_id": decision.rule_id,
        "mapping_version": decision.version,
        "mapping_confidence_bps": decision.confidence_bps,
    }


def standardize_amount_field(
    alias: Any,
    value: Any,
    *,
    template_class: str | None = None,
    mapping_version: str = fields.MAPPING_VERSION,
) -> dict[str, Any]:
    """Resolve, classify, and convert one amount to canonical signed cents."""

    decision, definition = _resolve_auto(
        alias,
        template_class=template_class,
        version=mapping_version,
    )
    if (
        definition.data_type != "INTEGER_CENTS"
        or definition.unit not in UNIT_BINDINGS
        or definition.storage_format != "SIGNED_INTEGER_CENTS"
    ):
        raise StageReviewContractError("AMOUNT_FIELD_CONTRACT_MISMATCH", "field is not a registered cents field")

    classified = fields.classify_value(definition.field_id, value)
    if not classified.derivation_allowed or classified.semantic not in {
        fields.ValueSemantic.PRESENT,
        fields.ValueSemantic.ZERO,
    }:
        raise StageReviewContractError(
            "AMOUNT_VALUE_NOT_DERIVABLE",
            f"amount semantic blocks derivation: {classified.semantic.value}",
            action=classified.action,
        )

    p1_unit = UNIT_BINDINGS[definition.unit]
    money = amount.Money.from_value(classified.normalized_value, unit=p1_unit)
    if money.cents != classified.normalized_value:
        raise StageReviewContractError("AMOUNT_CENT_BINDING_DRIFT", "P1/P3 cents binding changed the value")
    return {
        "schema_version": "kmfa.v015.s05_stage_review.amount.v1",
        **_mapping_projection(decision),
        "semantic": classified.semantic.value,
        "amount_cents": money.cents,
        "currency": money.currency,
        "dictionary_unit": definition.unit,
        "amount_unit_id": p1_unit,
        "storage_format": definition.storage_format,
        "public_safe": True,
    }


def standardize_date_field(
    alias: Any,
    value: Any,
    *,
    source_kind: str,
    business_timezone: str,
    source_timezone: str | None = None,
    template_class: str | None = None,
    mapping_version: str = fields.MAPPING_VERSION,
) -> dict[str, Any]:
    """Resolve and normalize a date before P3 ISO-date storage classification."""

    decision, definition = _resolve_auto(
        alias,
        template_class=template_class,
        version=mapping_version,
    )
    if (
        definition.data_type != "ISO_DATE"
        or definition.unit != "DAY"
        or definition.storage_format != "YYYY-MM-DD"
    ):
        raise StageReviewContractError("DATE_FIELD_CONTRACT_MISMATCH", "field is not a registered business-date field")

    normalized = date_period.normalize_business_date(
        value,
        source_kind=source_kind,
        business_timezone=business_timezone,
        source_timezone=source_timezone,
    )
    classified = fields.classify_value(definition.field_id, normalized.canonical_date.isoformat())
    if not classified.derivation_allowed or classified.semantic is not fields.ValueSemantic.PRESENT:
        raise StageReviewContractError("DATE_STORAGE_CLASSIFICATION_FAILED", "normalized date cannot enter P3 storage")
    return {
        "schema_version": "kmfa.v015.s05_stage_review.date.v1",
        **_mapping_projection(decision),
        "semantic": classified.semantic.value,
        "business_date": classified.normalized_value,
        "business_timezone": normalized.business_timezone,
        "source_kind": normalized.source_kind,
        "instant_utc": normalized.to_public_dict()["instant_utc"],
        "dictionary_unit": definition.unit,
        "storage_format": definition.storage_format,
        "normalization_order": ["ALIAS_RESOLUTION", "S05_P2_DATE_NORMALIZATION", "S05_P3_STORAGE_CLASSIFICATION"],
        "public_safe": True,
    }


def public_verification() -> dict[str, Any]:
    """Exercise positive and negative joins without returning source values."""

    checks: list[dict[str, str]] = []

    exact = standardize_amount_field("合同金额分", 12345)
    checks.append({"check_id": CHECK_IDS[0], "status": "PASS" if exact["field_id"] == "contract_amount_cents" else "FAIL"})
    checks.append({"check_id": CHECK_IDS[1], "status": "PASS" if exact["dictionary_unit"] == "CNY_CENT" and exact["amount_unit_id"] == "fen" else "FAIL"})
    checks.append({"check_id": CHECK_IDS[2], "status": "PASS" if exact["amount_cents"] == 12345 else "FAIL"})
    zero = standardize_amount_field("发票金额分", 0)
    checks.append({"check_id": CHECK_IDS[3], "status": "PASS" if zero["semantic"] == "ZERO" and zero["amount_cents"] == 0 else "FAIL"})

    negative_cases = (
        (CHECK_IDS[4], lambda: standardize_amount_field("合同金额分", json.loads("1.0"))),
        (CHECK_IDS[5], lambda: standardize_amount_field("合同金额分", "")),
        (CHECK_IDS[6], lambda: standardize_amount_field("含税金额", 1, template_class="CONTRACT_REGISTER")),
        (CHECK_IDS[7], lambda: standardize_amount_field("金额", 1)),
    )
    for check_id, operation in negative_cases:
        blocked = False
        try:
            operation()
        except StageReviewContractError:
            blocked = True
        checks.append({"check_id": check_id, "status": "PASS" if blocked else "FAIL"})

    normalized = standardize_date_field(
        "开票日期",
        "2026-07-15T23:30:00+00:00",
        source_kind="DATETIME",
        business_timezone="Australia/Sydney",
    )
    date_order_ok = (
        normalized["business_date"] == "2026-07-16"
        and normalized["normalization_order"][1] == "S05_P2_DATE_NORMALIZATION"
    )
    checks.append({"check_id": CHECK_IDS[8], "status": "PASS" if date_order_ok else "FAIL"})
    blocked = False
    try:
        standardize_date_field("开票日期", "2026-07-15", source_kind="DATE", business_timezone="")
    except date_period.DatePeriodError:
        blocked = True
    checks.append({"check_id": CHECK_IDS[9], "status": "PASS" if blocked else "FAIL"})

    failed = sum(row["status"] != "PASS" for row in checks)
    return {
        "schema_version": "kmfa.v015.s05_stage_review.binding_verification.v1",
        "run_phase_id": RUN_PHASE_ID,
        "public_safe": True,
        "synthetic_fixture": True,
        "unit_bindings": UNIT_BINDINGS,
        "normalization_order_enforced": True,
        "checks": checks,
        "accounting": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
        "raw_root_access_count": 0,
        "raw_value_exposed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
    }
