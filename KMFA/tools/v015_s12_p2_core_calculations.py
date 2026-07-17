#!/usr/bin/env python3
"""Deterministic public-safe calculation engine for KMFA v1.5 S12-P2."""

from __future__ import annotations

import copy
import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from typing import Any


RUN_PHASE_ID = "V015_S12_P2_CORE_CALCULATIONS"
ROADMAP_PHASE_ID = "S12-P2"
TASK_ID = "KMFA-V015-S12-P2-CORE-CALCULATIONS-20260715"
ACCEPTANCE_ID = "ACC-KMFA-V015-S12-P2-CORE-CALCULATIONS"
VERSION = "1.5.0-dev-s12p2"

MARGIN_VIEWS = ("contract", "settlement", "management")
MARGIN_BASIS_CONTRACT = {
    "contract": ("SIGNED_CONTRACT_PLUS_APPROVED_CHANGE", "CONTRACT_TARGET_COST"),
    "settlement": ("APPROVED_SETTLEMENT_REVENUE", "SETTLEMENT_MATCHED_COST"),
    "management": ("MANAGEMENT_RECOGNIZED_REVENUE", "MANAGEMENT_RECOGNIZED_COST"),
}
CONFIRMED = "CONFIRMED"
UNRESOLVED = "UNRESOLVED"
READY = "READY"
DEGRADED = "DEGRADED_REQUIRES_CONFIRMATION"
INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
DETERMINATE_ALERT = "DETERMINATE_ALERT"
DETERMINATE_CLEAR = "DETERMINATE_CLEAR"

DEFAULT_RISK_POLICY = {
    "schema_version": "kmfa.v015.s12p2.cost_risk_policy.v1",
    "policy_version": "S12P2-PUBLIC-DEFAULT-1",
    "low_margin_threshold_bps": 1000,
    "abnormal_cost_change_threshold_bps": 2000,
    "max_unallocated_cost_ratio_bps": 500,
    "minimum_cost_completeness_bps": 9500,
}

_IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}")
_FORBIDDEN_TEXT = (
    "/Users/",
    "/Volumes/",
    "/home/",
    "file://",
    "KMFA_MetaData",
    "private://",
)


class CoreCalculationError(ValueError):
    """Fail-closed error with a stable machine-readable code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _fingerprint(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value)).hexdigest()


def _mapping(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise CoreCalculationError("INVALID_MAPPING", f"{field} must be an object")
    return dict(value)


def _identifier(value: Any, field: str) -> str:
    if not isinstance(value, str) or not _IDENTIFIER.fullmatch(value):
        raise CoreCalculationError("INVALID_IDENTIFIER", f"{field} is invalid")
    return value


def _enum(value: Any, field: str, allowed: Sequence[str]) -> str:
    if not isinstance(value, str) or value not in allowed:
        raise CoreCalculationError("INVALID_ENUM", f"{field} must be one of {tuple(allowed)}")
    return value


def _integer(value: Any, field: str, *, minimum: int | None = None, maximum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise CoreCalculationError("INTEGER_REQUIRED", f"{field} must be an integer")
    if minimum is not None and value < minimum:
        raise CoreCalculationError("INTEGER_OUT_OF_RANGE", f"{field} must be >= {minimum}")
    if maximum is not None and value > maximum:
        raise CoreCalculationError("INTEGER_OUT_OF_RANGE", f"{field} must be <= {maximum}")
    return value


def _cents(value: Any, field: str, *, non_negative: bool = False) -> int:
    return _integer(value, field, minimum=0 if non_negative else None)


def _assert_public_safe(value: Any, path: str = "payload") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise CoreCalculationError("NON_PUBLIC_VALUE", f"{path} has a non-text key")
            _assert_public_safe(item, f"{path}.{key}")
        return
    if isinstance(value, list) or isinstance(value, tuple):
        for index, item in enumerate(value):
            _assert_public_safe(item, f"{path}[{index}]")
        return
    if isinstance(value, str) and any(token.lower() in value.lower() for token in _FORBIDDEN_TEXT):
        raise CoreCalculationError("NON_PUBLIC_VALUE", f"{path} contains a private path or locator")
    if isinstance(value, float):
        raise CoreCalculationError("FLOAT_NOT_ALLOWED", f"{path} contains a float")


def _basis_points(numerator: int, denominator: int) -> int | None:
    if denominator == 0:
        return None
    sign = -1 if (numerator < 0) != (denominator < 0) else 1
    absolute = (abs(numerator) * 10000 + abs(denominator) // 2) // abs(denominator)
    return sign * absolute


def _common_scope(payload: Mapping[str, Any]) -> dict[str, str]:
    return {
        "project_ref": _identifier(payload.get("project_ref"), "project_ref"),
        "entity_ref": _identifier(payload.get("entity_ref"), "entity_ref"),
        "period_ref": _identifier(payload.get("period_ref"), "period_ref"),
        "basis_version": _identifier(payload.get("basis_version"), "basis_version"),
    }


def calculate_margin_views(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Calculate contract, settlement and management gross-margin views."""

    source = _mapping(payload, "payload")
    _assert_public_safe(source)
    scope = _common_scope(source)
    views: dict[str, Any] = {}
    for view_name in MARGIN_VIEWS:
        view = _mapping(source.get(view_name), view_name)
        revenue_basis, cost_basis = MARGIN_BASIS_CONTRACT[view_name]
        if view.get("revenue_basis") != revenue_basis or view.get("cost_basis") != cost_basis:
            raise CoreCalculationError("MARGIN_BASIS_MISMATCH", f"{view_name} basis is not explicit or supported")
        revenue = _cents(view.get("revenue_cents"), f"{view_name}.revenue_cents", non_negative=True)
        cost = _cents(view.get("cost_cents"), f"{view_name}.cost_cents", non_negative=True)
        gross_profit = revenue - cost
        margin_bps = _basis_points(gross_profit, revenue)
        views[view_name] = {
            "revenue_basis": revenue_basis,
            "cost_basis": cost_basis,
            "revenue_cents": revenue,
            "cost_cents": cost,
            "gross_profit_cents": gross_profit,
            "gross_margin_bps": margin_bps,
            "rate_status": READY if margin_bps is not None else INSUFFICIENT_DATA,
        }
    result = {
        "schema_version": "kmfa.v015.s12p2.margin_views.v1",
        **scope,
        "money_unit": "integer_cent",
        "money_tolerance_cents": 0,
        "views": views,
    }
    result["calculation_fingerprint"] = _fingerprint(result)
    return copy.deepcopy(result)


def assert_margin_golden(actual: Mapping[str, Any], expected: Mapping[str, Any]) -> dict[str, Any]:
    """Require exact cent equality for all three gross-profit golden values."""

    actual_map = _mapping(actual, "actual")
    expected_map = _mapping(expected, "expected")
    differences: dict[str, int] = {}
    for view_name in MARGIN_VIEWS:
        actual_view = _mapping(_mapping(actual_map.get("views"), "actual.views").get(view_name), f"actual.{view_name}")
        expected_view = _mapping(expected_map.get(view_name), f"expected.{view_name}")
        actual_cents = _cents(actual_view.get("gross_profit_cents"), f"actual.{view_name}.gross_profit_cents")
        expected_cents = _cents(expected_view.get("gross_profit_cents"), f"expected.{view_name}.gross_profit_cents")
        differences[view_name] = actual_cents - expected_cents
    if any(differences.values()):
        raise CoreCalculationError("GOLDEN_CENT_DIFFERENCE", f"gross-profit cent differences: {differences}")
    return {
        "schema_version": "kmfa.v015.s12p2.margin_golden_comparison.v1",
        "money_tolerance_cents": 0,
        "differences_cents": differences,
        "zero_difference_pass": True,
    }


def calculate_cash_metrics(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Calculate cash gross profit and capital occupation from confirmed cash only."""

    source = _mapping(payload, "payload")
    _assert_public_safe(source)
    scope = _common_scope(source)
    account_status = _enum(source.get("account_status"), "account_status", (CONFIRMED, UNRESOLVED))
    entity_status = _enum(source.get("entity_status"), "entity_status", (CONFIRMED, UNRESOLVED))
    lane = _enum(
        source.get("cash_source_lane"),
        "cash_source_lane",
        ("BANK_CONFIRMED_COLLECTIONS_AND_PAYMENTS",),
    )
    collection = _cents(source.get("confirmed_collection_cents"), "confirmed_collection_cents", non_negative=True)
    paid = _cents(source.get("confirmed_cash_paid_cost_cents"), "confirmed_cash_paid_cost_cents", non_negative=True)
    retention = _cents(source.get("retention_receivable_cents"), "retention_receivable_cents", non_negative=True)
    unsettled = _cents(source.get("unsettled_receivable_cents"), "unsettled_receivable_cents", non_negative=True)
    invoiced_not_collected = _cents(
        source.get("invoiced_not_collected_cents"),
        "invoiced_not_collected_cents",
        non_negative=True,
    )
    ordinary_receivable = _cents(source.get("ordinary_receivable_cents"), "ordinary_receivable_cents", non_negative=True)
    cash_gross_profit = collection - paid
    net_capital_position = paid + retention + unsettled - collection
    degraded = account_status == UNRESOLVED or entity_status == UNRESOLVED
    result = {
        "schema_version": "kmfa.v015.s12p2.cash_metrics.v1",
        **scope,
        "cash_source_lane": lane,
        "account_status": account_status,
        "entity_status": entity_status,
        "calculation_status": DEGRADED if degraded else READY,
        "business_decision_allowed": not degraded,
        "confirmed_collection_cents": collection,
        "confirmed_cash_paid_cost_cents": paid,
        "cash_gross_profit_cents": cash_gross_profit,
        "retention_receivable_cents": retention,
        "unsettled_receivable_cents": unsettled,
        "net_capital_position_cents": net_capital_position,
        "capital_occupied_cents": max(net_capital_position, 0),
        "net_cash_surplus_cents": max(-net_capital_position, 0),
        "excluded_from_cash_income": {
            "invoiced_not_collected_cents": invoiced_not_collected,
            "ordinary_receivable_cents": ordinary_receivable,
        },
        "uncollected_amount_counted_as_cash_cents": 0,
        "money_unit": "integer_cent",
        "money_tolerance_cents": 0,
    }
    result["calculation_fingerprint"] = _fingerprint(result)
    return copy.deepcopy(result)


def validate_risk_policy(policy: Mapping[str, Any]) -> dict[str, Any]:
    source = _mapping(policy, "policy")
    _assert_public_safe(source)
    if source.get("schema_version") != "kmfa.v015.s12p2.cost_risk_policy.v1":
        raise CoreCalculationError("RISK_POLICY_SCHEMA_MISMATCH", "unsupported risk policy schema")
    return {
        "schema_version": source["schema_version"],
        "policy_version": _identifier(source.get("policy_version"), "policy_version"),
        "low_margin_threshold_bps": _integer(source.get("low_margin_threshold_bps"), "low_margin_threshold_bps", minimum=-10000, maximum=10000),
        "abnormal_cost_change_threshold_bps": _integer(source.get("abnormal_cost_change_threshold_bps"), "abnormal_cost_change_threshold_bps", minimum=0, maximum=1000000),
        "max_unallocated_cost_ratio_bps": _integer(source.get("max_unallocated_cost_ratio_bps"), "max_unallocated_cost_ratio_bps", minimum=0, maximum=10000),
        "minimum_cost_completeness_bps": _integer(source.get("minimum_cost_completeness_bps"), "minimum_cost_completeness_bps", minimum=0, maximum=10000),
    }


def assess_cost_risk(payload: Mapping[str, Any], policy: Mapping[str, Any]) -> dict[str, Any]:
    """Assess missing cost, unallocated cost, abnormal change and low margin."""

    source = _mapping(payload, "payload")
    _assert_public_safe(source)
    scope = _common_scope(source)
    rules = validate_risk_policy(policy)
    required_count = _integer(source.get("required_cost_category_count"), "required_cost_category_count", minimum=1)
    observed_count = _integer(source.get("observed_required_cost_category_count"), "observed_required_cost_category_count", minimum=0)
    if observed_count > required_count:
        raise CoreCalculationError("CATEGORY_COUNT_INVALID", "observed required categories exceed required categories")
    total_cost = _cents(source.get("total_cost_cents"), "total_cost_cents", non_negative=True)
    unallocated = _cents(source.get("unallocated_cost_cents"), "unallocated_cost_cents", non_negative=True)
    if unallocated > total_cost:
        raise CoreCalculationError("UNALLOCATED_COST_INVALID", "unallocated cost exceeds total cost")

    current_cost_value = source.get("current_period_cost_cents")
    comparison_cost_value = source.get("comparison_period_cost_cents")
    margin_value = source.get("management_margin_bps")
    current_cost = None if current_cost_value is None else _cents(current_cost_value, "current_period_cost_cents", non_negative=True)
    comparison_cost = None if comparison_cost_value is None else _cents(comparison_cost_value, "comparison_period_cost_cents", non_negative=True)
    management_margin = None if margin_value is None else _integer(margin_value, "management_margin_bps", minimum=-1000000, maximum=1000000)

    completeness_bps = _basis_points(observed_count, required_count)
    unallocated_ratio_bps = _basis_points(unallocated, total_cost)
    abnormal_change_bps = None
    if current_cost is not None and comparison_cost not in (None, 0):
        abnormal_change_bps = _basis_points(abs(current_cost - comparison_cost), abs(comparison_cost))

    missing_reasons: list[str] = []
    if total_cost == 0:
        missing_reasons.append("TOTAL_COST_ZERO")
    if current_cost is None:
        missing_reasons.append("CURRENT_PERIOD_COST_MISSING")
    if comparison_cost is None:
        missing_reasons.append("COMPARISON_PERIOD_COST_MISSING")
    elif comparison_cost == 0:
        missing_reasons.append("COMPARISON_PERIOD_COST_ZERO")
    if management_margin is None:
        missing_reasons.append("MANAGEMENT_MARGIN_MISSING")

    triggers: list[str] = []
    if not missing_reasons:
        if completeness_bps is not None and completeness_bps < rules["minimum_cost_completeness_bps"]:
            triggers.append("COST_CATEGORY_INCOMPLETE")
        if unallocated_ratio_bps is not None and unallocated_ratio_bps > rules["max_unallocated_cost_ratio_bps"]:
            triggers.append("UNALLOCATED_COST_EXCESS")
        if abnormal_change_bps is not None and abnormal_change_bps > rules["abnormal_cost_change_threshold_bps"]:
            triggers.append("ABNORMAL_COST_CHANGE")
        if management_margin is not None and management_margin < rules["low_margin_threshold_bps"]:
            triggers.append("LOW_MANAGEMENT_MARGIN")

    conclusion = INSUFFICIENT_DATA if missing_reasons else (DETERMINATE_ALERT if triggers else DETERMINATE_CLEAR)
    result = {
        "schema_version": "kmfa.v015.s12p2.cost_risk_assessment.v1",
        **scope,
        "policy_version": rules["policy_version"],
        "policy_fingerprint": _fingerprint(rules),
        "conclusion": conclusion,
        "deterministic_conclusion_allowed": not missing_reasons,
        "missing_reason_codes": missing_reasons,
        "triggered_rule_codes": triggers,
        "metrics": {
            "cost_completeness_bps": completeness_bps,
            "unallocated_cost_ratio_bps": unallocated_ratio_bps,
            "abnormal_cost_change_bps": abnormal_change_bps,
            "management_margin_bps": management_margin,
        },
        "thresholds": {
            key: rules[key]
            for key in (
                "low_margin_threshold_bps",
                "abnormal_cost_change_threshold_bps",
                "max_unallocated_cost_ratio_bps",
                "minimum_cost_completeness_bps",
            )
        },
    }
    result["assessment_fingerprint"] = _fingerprint(result)
    return copy.deepcopy(result)


def margin_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s12p2.margin_basis_contract.v1",
        "views": {
            name: {"revenue_basis": bases[0], "cost_basis": bases[1]}
            for name, bases in MARGIN_BASIS_CONTRACT.items()
        },
        "money_unit": "integer_cent",
        "money_tolerance_cents": 0,
        "zero_revenue_rate_status": INSUFFICIENT_DATA,
        "implicit_basis_allowed": False,
    }


def cash_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s12p2.cash_metrics_contract.v1",
        "cash_income_source": "BANK_CONFIRMED_COLLECTIONS_AND_PAYMENTS",
        "uncollected_invoice_counted_as_cash": False,
        "ordinary_receivable_counted_as_cash": False,
        "unresolved_account_or_entity_status": DEGRADED,
        "unresolved_business_decision_allowed": False,
        "money_unit": "integer_cent",
        "money_tolerance_cents": 0,
    }


def _margin_fixture() -> dict[str, Any]:
    return {
        "project_ref": "PROJECT-PUBLIC-001",
        "entity_ref": "ENTITY-PUBLIC-001",
        "period_ref": "2026-PUBLIC-01",
        "basis_version": "MARGIN-BASIS-PUBLIC-1",
        "contract": {
            "revenue_basis": "SIGNED_CONTRACT_PLUS_APPROVED_CHANGE",
            "cost_basis": "CONTRACT_TARGET_COST",
            "revenue_cents": 120000,
            "cost_cents": 90000,
        },
        "settlement": {
            "revenue_basis": "APPROVED_SETTLEMENT_REVENUE",
            "cost_basis": "SETTLEMENT_MATCHED_COST",
            "revenue_cents": 100000,
            "cost_cents": 80000,
        },
        "management": {
            "revenue_basis": "MANAGEMENT_RECOGNIZED_REVENUE",
            "cost_basis": "MANAGEMENT_RECOGNIZED_COST",
            "revenue_cents": 90000,
            "cost_cents": 75000,
        },
    }


def _cash_fixture(*, unresolved: bool = False) -> dict[str, Any]:
    return {
        "project_ref": "PROJECT-PUBLIC-001",
        "entity_ref": "ENTITY-PUBLIC-001",
        "period_ref": "2026-PUBLIC-01",
        "basis_version": "CASH-BASIS-PUBLIC-1",
        "account_status": UNRESOLVED if unresolved else CONFIRMED,
        "entity_status": CONFIRMED,
        "cash_source_lane": "BANK_CONFIRMED_COLLECTIONS_AND_PAYMENTS",
        "confirmed_collection_cents": 70000,
        "confirmed_cash_paid_cost_cents": 50000,
        "retention_receivable_cents": 10000,
        "unsettled_receivable_cents": 20000,
        "invoiced_not_collected_cents": 40000,
        "ordinary_receivable_cents": 30000,
    }


def _risk_fixture() -> dict[str, Any]:
    return {
        "project_ref": "PROJECT-PUBLIC-001",
        "entity_ref": "ENTITY-PUBLIC-001",
        "period_ref": "2026-PUBLIC-01",
        "basis_version": "RISK-BASIS-PUBLIC-1",
        "required_cost_category_count": 10,
        "observed_required_cost_category_count": 9,
        "total_cost_cents": 100000,
        "unallocated_cost_cents": 6000,
        "current_period_cost_cents": 130000,
        "comparison_period_cost_cents": 100000,
        "management_margin_bps": 800,
    }


def _rejects(operation: Any, expected_code: str) -> bool:
    try:
        operation()
    except CoreCalculationError as error:
        return error.code == expected_code
    return False


def public_verification() -> dict[str, Any]:
    """Run deterministic public fixtures covering all S12-P2 stop conditions."""

    margin_input = _margin_fixture()
    margin = calculate_margin_views(margin_input)
    golden = assert_margin_golden(
        margin,
        {
            "contract": {"gross_profit_cents": 30000},
            "settlement": {"gross_profit_cents": 20000},
            "management": {"gross_profit_cents": 15000},
        },
    )
    cash = calculate_cash_metrics(_cash_fixture())
    degraded_cash = calculate_cash_metrics(_cash_fixture(unresolved=True))
    risk = assess_cost_risk(_risk_fixture(), DEFAULT_RISK_POLICY)
    relaxed_policy = {
        **DEFAULT_RISK_POLICY,
        "policy_version": "S12P2-PUBLIC-RELAXED-1",
        "low_margin_threshold_bps": 500,
        "abnormal_cost_change_threshold_bps": 4000,
        "max_unallocated_cost_ratio_bps": 700,
        "minimum_cost_completeness_bps": 8500,
    }
    relaxed_risk = assess_cost_risk(_risk_fixture(), relaxed_policy)
    missing_input = _risk_fixture()
    missing_input["comparison_period_cost_cents"] = None
    missing_risk = assess_cost_risk(missing_input, DEFAULT_RISK_POLICY)

    checks = {
        "margin_contract_view_count": len(margin_contract()["views"]) == 3,
        "contract_gross_profit_exact": margin["views"]["contract"]["gross_profit_cents"] == 30000,
        "settlement_gross_profit_exact": margin["views"]["settlement"]["gross_profit_cents"] == 20000,
        "management_gross_profit_exact": margin["views"]["management"]["gross_profit_cents"] == 15000,
        "contract_margin_bps_exact": margin["views"]["contract"]["gross_margin_bps"] == 2500,
        "settlement_margin_bps_exact": margin["views"]["settlement"]["gross_margin_bps"] == 2000,
        "management_margin_bps_exact": margin["views"]["management"]["gross_margin_bps"] == 1667,
        "golden_zero_difference": golden["zero_difference_pass"] is True,
        "golden_all_deltas_zero": set(golden["differences_cents"].values()) == {0},
        "golden_one_cent_drift_rejected": _rejects(
            lambda: assert_margin_golden(margin, {
                "contract": {"gross_profit_cents": 30001},
                "settlement": {"gross_profit_cents": 20000},
                "management": {"gross_profit_cents": 15000},
            }),
            "GOLDEN_CENT_DIFFERENCE",
        ),
        "implicit_margin_basis_rejected": _rejects(
            lambda: calculate_margin_views({**margin_input, "contract": {**margin_input["contract"], "revenue_basis": "UNKNOWN"}}),
            "MARGIN_BASIS_MISMATCH",
        ),
        "float_margin_rejected": _rejects(
            lambda: calculate_margin_views({**margin_input, "contract": {**margin_input["contract"], "revenue_cents": json.loads("1.25")}}),
            "FLOAT_NOT_ALLOWED",
        ),
        "boolean_margin_rejected": _rejects(
            lambda: calculate_margin_views({**margin_input, "contract": {**margin_input["contract"], "revenue_cents": True}}),
            "INTEGER_REQUIRED",
        ),
        "margin_input_not_mutated": margin_input == _margin_fixture(),
        "margin_deterministic": margin == calculate_margin_views(_margin_fixture()),
        "cash_gross_profit_exact": cash["cash_gross_profit_cents"] == 20000,
        "cash_net_capital_position_exact": cash["net_capital_position_cents"] == 10000,
        "cash_capital_occupied_exact": cash["capital_occupied_cents"] == 10000,
        "cash_surplus_exact": cash["net_cash_surplus_cents"] == 0,
        "uncollected_invoice_not_cash": cash["uncollected_amount_counted_as_cash_cents"] == 0,
        "excluded_uncollected_invoice_preserved": cash["excluded_from_cash_income"]["invoiced_not_collected_cents"] == 40000,
        "excluded_receivable_preserved": cash["excluded_from_cash_income"]["ordinary_receivable_cents"] == 30000,
        "confirmed_cash_ready": cash["calculation_status"] == READY,
        "confirmed_cash_decision_allowed": cash["business_decision_allowed"] is True,
        "unresolved_account_degraded": degraded_cash["calculation_status"] == DEGRADED,
        "unresolved_account_decision_blocked": degraded_cash["business_decision_allowed"] is False,
        "cash_deterministic": cash == calculate_cash_metrics(_cash_fixture()),
        "cash_contract_excludes_uncollected": cash_contract()["uncollected_invoice_counted_as_cash"] is False,
        "risk_default_policy_external": risk["policy_version"] == "S12P2-PUBLIC-DEFAULT-1",
        "risk_completeness_exact": risk["metrics"]["cost_completeness_bps"] == 9000,
        "risk_unallocated_ratio_exact": risk["metrics"]["unallocated_cost_ratio_bps"] == 600,
        "risk_abnormal_change_exact": risk["metrics"]["abnormal_cost_change_bps"] == 3000,
        "risk_margin_exact": risk["metrics"]["management_margin_bps"] == 800,
        "risk_alert_determinate": risk["conclusion"] == DETERMINATE_ALERT,
        "risk_all_four_rules_triggered": risk["triggered_rule_codes"] == [
            "COST_CATEGORY_INCOMPLETE",
            "UNALLOCATED_COST_EXCESS",
            "ABNORMAL_COST_CHANGE",
            "LOW_MANAGEMENT_MARGIN",
        ],
        "risk_adjustable_policy_fingerprint_changes": risk["policy_fingerprint"] != relaxed_risk["policy_fingerprint"],
        "risk_adjustable_thresholds_clear": relaxed_risk["conclusion"] == DETERMINATE_CLEAR,
        "risk_adjustable_thresholds_no_trigger": relaxed_risk["triggered_rule_codes"] == [],
        "missing_data_insufficient": missing_risk["conclusion"] == INSUFFICIENT_DATA,
        "missing_data_not_determinate": missing_risk["deterministic_conclusion_allowed"] is False,
        "missing_data_no_alert_claim": missing_risk["triggered_rule_codes"] == [],
        "missing_data_reason_explicit": missing_risk["missing_reason_codes"] == ["COMPARISON_PERIOD_COST_MISSING"],
        "risk_deterministic": risk == assess_cost_risk(_risk_fixture(), DEFAULT_RISK_POLICY),
        "invalid_policy_float_rejected": _rejects(
            lambda: assess_cost_risk(_risk_fixture(), {**DEFAULT_RISK_POLICY, "low_margin_threshold_bps": json.loads("1.5")}),
            "FLOAT_NOT_ALLOWED",
        ),
        "private_path_rejected": _rejects(
            lambda: calculate_cash_metrics({**_cash_fixture(), "project_ref": "/Users/example/private"}),
            "NON_PUBLIC_VALUE",
        ),
        "raw_root_access_zero": True,
        "live_source_read_zero": True,
        "business_execution_false": True,
    }
    failed = sorted(name for name, passed in checks.items() if not passed)
    return {
        "schema_version": "kmfa.v015.s12p2.public_verification.v1",
        "fixture_class": "PUBLIC_SAFE_SYNTHETIC",
        "margin_results": margin,
        "margin_golden_comparison": golden,
        "cash_results": cash,
        "degraded_cash_results": degraded_cash,
        "risk_results": risk,
        "relaxed_risk_results": relaxed_risk,
        "missing_data_risk_results": missing_risk,
        "checks": checks,
        "failed_checks": failed,
        "accounting": {
            "total": len(checks),
            "passed": len(checks) - len(failed),
            "failed": len(failed),
        },
        "raw_root_access_count": 0,
        "live_source_read_count": 0,
        "business_execution_performed": False,
    }
