"""PFI v0.2.5 Stage 5.2 deterministic financial model capability contracts.

The functions in this module operate on explicit caller-provided values.  They
do not load private rows, infer missing balances or holdings, or claim that the
models have passed the real-data validation reserved for Phase 5.3.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, replace
from datetime import date, timedelta
from decimal import Decimal, localcontext
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from pfi_v02.stage_v022_interconnection import event_policy
from pfi_v02.stage_v022_ledger_taxonomy import (
    STAGE5_TAXONOMY_LIMITS,
    build_stage5_consumption_taxonomy,
    validate_stage5_taxonomy_constraints,
)
from pfi_v02.stage_v022_tags_views import (
    STAGE6_TAG_TABLES,
    build_stage6_default_tag_library,
)


PHASE_ID = "V025-S5-P5.2"
TASK_IDS = ("S5-P2-T1", "S5-P2-T2", "S5-P2-T3", "S5-P2-T4")
ACCEPTANCE_ID = "ACC-PFI-V025-S5-P52-FINANCIAL-MODELS"
MODEL_VERSION = "pfi-v0.2.5-financial-models-v1"
BASE_CURRENCY = "CNY"

TOTAL_CONSUMPTION_LABEL_ZH = "消费总流出金额（用户定义活动口径）"
LIVING_CONSUMPTION_LABEL_ZH = "生活消费金额"
INVESTMENT_FUNDING_LABEL_ZH = "投资资金流出金额"
INVESTMENT_ALLOCATION_LABEL_ZH = "投资域内配置金额"

GROSS_ACTIVITY_EVENT_TYPES = (
    "consumption",
    "investment_deposit",
    "fund_subscription",
    "bullion_purchase",
    "investment_buy",
    "fee",
)
LIVING_CONSUMPTION_EVENT_TYPES = ("consumption",)
INVESTMENT_FUNDING_EVENT_TYPES = ("investment_deposit",)
INVESTMENT_ALLOCATION_EVENT_TYPES = (
    "fund_subscription",
    "bullion_purchase",
    "investment_buy",
)
CASHFLOW_WINDOWS_DAYS = (7, 21, 30, 60, 90, 180, 360)
FORMULA_IDS = tuple(f"FORM-PFI-{number:03d}" for number in range(15, 21))
PARAMETER_IDS = tuple(f"PARAM-PFI-{number:03d}" for number in range(81, 93))
XIRR_POLICY = {
    "day_count_basis": 365,
    "npv_tolerance": "0.0000000001",
    "rate_quantum": "0.0000000001",
    "max_iterations": 256,
    "lower_bound": "-0.999999",
    "initial_upper_bound": "10",
    "maximum_upper_bound": "1000000",
    "multiple_sign_change_policy": "blocked_non_unique",
}
FINANCIAL_MODEL_CONFIG: dict[str, Any] = {
    "model_version": MODEL_VERSION,
    "base_currency": BASE_CURRENCY,
    "labels_zh": {
        "total_consumption_outflow": TOTAL_CONSUMPTION_LABEL_ZH,
        "living_consumption": LIVING_CONSUMPTION_LABEL_ZH,
        "investment_funding_outflow": INVESTMENT_FUNDING_LABEL_ZH,
        "investment_allocation_amount": INVESTMENT_ALLOCATION_LABEL_ZH,
    },
    "gross_activity_event_types": list(GROSS_ACTIVITY_EVENT_TYPES),
    "living_consumption_event_types": list(LIVING_CONSUMPTION_EVENT_TYPES),
    "investment_funding_event_types": list(INVESTMENT_FUNDING_EVENT_TYPES),
    "investment_allocation_event_types": list(INVESTMENT_ALLOCATION_EVENT_TYPES),
    "cashflow_windows_days": list(CASHFLOW_WINDOWS_DAYS),
    "taxonomy_limits": {
        "max_l1_categories": 12,
        "max_l2_per_l1": 5,
        "max_l2_total": 50,
        "primary_category_per_transaction": 1,
    },
    "tag_policy": {
        "tag_types": ["default", "custom"],
        "history_required": True,
        "view_filter_modes": ["all", "any"],
    },
    "xirr_policy": dict(XIRR_POLICY),
    "real_data_model_validation_status": "blocked_pending_phase_5_3",
}

PFI_ROOT = Path(__file__).resolve().parents[4]
FORMULA_REGISTRY_PATH = PFI_ROOT / "config" / "formulas" / "v025_formula_registry.json"
PARAMETER_CATALOG_PATH = PFI_ROOT / "config" / "pfi_parameters.yaml"
HUMAN_PARAMETER_PATH = PFI_ROOT / "模型参数文件.md"


def _canonical_hash(payload: object) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _decimal(name: str, value: object) -> Decimal:
    if isinstance(value, float):
        raise TypeError(f"{name} must be Decimal; float is forbidden")
    if not isinstance(value, Decimal) or not value.is_finite():
        raise TypeError(f"{name} must be a finite Decimal")
    return value


def _non_negative(name: str, value: object) -> Decimal:
    decimal_value = _decimal(name, value)
    if decimal_value < 0:
        raise ValueError(f"{name} must be non-negative")
    return decimal_value


def _money_text(value: Decimal) -> str:
    return format(value, "f")


def _canonical_event_type(event_type: str) -> str:
    normalized = event_policy(event_type).event_type
    return "consumption" if normalized == "ordinary_consumption" else normalized


@dataclass(frozen=True)
class FinancialEvent:
    source_record_id: str
    economic_event_id: str
    interconnection_group_id: str
    event_date: date
    event_type: str
    amount_cny: Decimal
    direction: str
    offset_economic_event_id: str | None = None

    def __post_init__(self) -> None:
        for name in ("source_record_id", "economic_event_id", "interconnection_group_id"):
            if not str(getattr(self, name)).strip():
                raise ValueError(f"{name} is required")
        if not isinstance(self.event_date, date):
            raise TypeError("event_date must be date")
        amount = _decimal("amount_cny", self.amount_cny)
        if amount <= 0:
            raise ValueError("amount_cny must be positive")
        policy = event_policy(self.event_type)
        expected_direction = policy.cashflow_direction
        allowed_direction = {
            "outflow": "outflow",
            "inflow": "inflow",
            "internal": "internal",
            "none": self.direction,
        }[expected_direction]
        if self.direction != allowed_direction:
            raise ValueError(
                f"{self.event_type} requires {allowed_direction} direction, got {self.direction}"
            )


@dataclass(frozen=True)
class CoreFinancialSnapshot:
    cash_cny: Decimal
    investment_market_value_cny: Decimal
    other_assets_cny: Decimal
    liabilities_cny: Decimal
    reported_net_worth_cny: Decimal

    def __post_init__(self) -> None:
        _decimal("cash_cny", self.cash_cny)
        _non_negative("investment_market_value_cny", self.investment_market_value_cny)
        _non_negative("other_assets_cny", self.other_assets_cny)
        _non_negative("liabilities_cny", self.liabilities_cny)
        _decimal("reported_net_worth_cny", self.reported_net_worth_cny)


@dataclass(frozen=True)
class CashRollforward:
    opening_cash_cny: Decimal
    external_inflows_cny: Decimal
    external_outflows_cny: Decimal
    adjustments_cny: Decimal
    closing_cash_cny: Decimal

    def __post_init__(self) -> None:
        _decimal("opening_cash_cny", self.opening_cash_cny)
        _non_negative("external_inflows_cny", self.external_inflows_cny)
        _non_negative("external_outflows_cny", self.external_outflows_cny)
        _decimal("adjustments_cny", self.adjustments_cny)
        _decimal("closing_cash_cny", self.closing_cash_cny)


@dataclass(frozen=True)
class InvestmentReallocation:
    life_cash_before_cny: Decimal
    investment_assets_before_cny: Decimal
    life_cash_after_cny: Decimal
    investment_assets_after_cny: Decimal
    explicit_fee_cny: Decimal

    def __post_init__(self) -> None:
        for name in (
            "life_cash_before_cny",
            "investment_assets_before_cny",
            "life_cash_after_cny",
            "investment_assets_after_cny",
            "explicit_fee_cny",
        ):
            _non_negative(name, getattr(self, name))


@dataclass(frozen=True)
class XirrCashFlow:
    cashflow_date: date
    amount_cny: Decimal
    flow_type: str

    def __post_init__(self) -> None:
        if not isinstance(self.cashflow_date, date):
            raise TypeError("cashflow_date must be date")
        amount = _decimal("amount_cny", self.amount_cny)
        if amount == 0:
            raise ValueError("XIRR cash flow amount must be non-zero")
        if self.flow_type not in {
            "investment_funding",
            "investment_return",
            "dividend",
            "interest",
            "terminal_value",
            "fee",
            "tax",
        }:
            raise ValueError(f"unsupported XIRR flow_type: {self.flow_type}")


def build_phase52_contract() -> dict[str, Any]:
    return {
        "version": "v0.2.5",
        "stage": 5,
        "phase": "5.2",
        "phase_id": PHASE_ID,
        "task_ids": list(TASK_IDS),
        "acceptance_id": ACCEPTANCE_ID,
        "acceptance_id_origin": "project_governance_assigned_not_source_roadmap",
        "current_phase_only": True,
        "real_data_model_validation_completed": False,
        "phase_5_3_started": False,
        "stage_5_whole_stage_review_started": False,
        "financial_fixture_acceptance_allowed": False,
        "real_financial_data_read": False,
        "real_financial_data_mutated": False,
        "database_changed": False,
        "finder_used": False,
        "network_performed": False,
        "push_performed": False,
        "app_install_performed": False,
    }


def _event_payload(event: FinancialEvent) -> tuple[object, ...]:
    return (
        event.economic_event_id,
        event.interconnection_group_id,
        event.event_date,
        _canonical_event_type(event.event_type),
        event.amount_cny,
        event.direction,
        event.offset_economic_event_id,
    )


def _deduplicate_events(
    events: Iterable[FinancialEvent],
) -> tuple[tuple[FinancialEvent, ...], int, int]:
    source_rows = tuple(events)
    by_source: dict[str, FinancialEvent] = {}
    for event in source_rows:
        current = by_source.get(event.source_record_id)
        if current is not None and _event_payload(current) != _event_payload(event):
            raise ValueError(f"conflicting source_record_id: {event.source_record_id}")
        by_source[event.source_record_id] = event

    by_event_type: dict[tuple[str, str], FinancialEvent] = {}
    for event in by_source.values():
        canonical_type = _canonical_event_type(event.event_type)
        normalized = replace(event, event_type=canonical_type)
        key = (normalized.economic_event_id, canonical_type)
        current = by_event_type.get(key)
        if current is not None and _event_payload(current) != _event_payload(normalized):
            raise ValueError(
                "conflicting duplicate economic_event_id/event_type: "
                f"{normalized.economic_event_id}/{canonical_type}"
            )
        if current is None or normalized.source_record_id < current.source_record_id:
            by_event_type[key] = normalized

    deduped = tuple(
        sorted(
            by_event_type.values(),
            key=lambda event: (
                event.event_date,
                event.economic_event_id,
                event.event_type,
                event.source_record_id,
            ),
        )
    )
    return deduped, len(source_rows), len(by_source)


def calculate_dual_consumption(events: Iterable[FinancialEvent]) -> dict[str, Any]:
    deduped, source_record_count, unique_source_record_count = _deduplicate_events(events)
    non_refunds = tuple(event for event in deduped if event.event_type != "refund")
    target_by_id: dict[str, list[FinancialEvent]] = defaultdict(list)
    for event in non_refunds:
        target_by_id[event.economic_event_id].append(event)

    component_bases = {
        "living": sum(
            (event.amount_cny for event in non_refunds if event.event_type in LIVING_CONSUMPTION_EVENT_TYPES),
            Decimal("0.00"),
        ),
        "funding": sum(
            (event.amount_cny for event in non_refunds if event.event_type in INVESTMENT_FUNDING_EVENT_TYPES),
            Decimal("0.00"),
        ),
        "allocation": sum(
            (event.amount_cny for event in non_refunds if event.event_type in INVESTMENT_ALLOCATION_EVENT_TYPES),
            Decimal("0.00"),
        ),
        "fee": sum(
            (event.amount_cny for event in non_refunds if event.event_type == "fee"),
            Decimal("0.00"),
        ),
    }
    refund_by_component = {key: Decimal("0.00") for key in component_bases}
    gross_refund = Decimal("0.00")
    refunded_by_target: dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))
    for refund in (event for event in deduped if event.event_type == "refund"):
        if not refund.offset_economic_event_id:
            raise ValueError("refund requires offset_economic_event_id")
        targets = target_by_id.get(refund.offset_economic_event_id, [])
        if len(targets) != 1:
            raise ValueError("refund offset_economic_event_id must resolve to one event")
        target = targets[0]
        refunded_by_target[target.economic_event_id] += refund.amount_cny
        if refunded_by_target[target.economic_event_id] > target.amount_cny:
            raise ValueError("refund total exceeds the linked original event")
        if target.event_type in GROSS_ACTIVITY_EVENT_TYPES:
            gross_refund += refund.amount_cny
        if target.event_type in LIVING_CONSUMPTION_EVENT_TYPES:
            refund_by_component["living"] += refund.amount_cny
        elif target.event_type in INVESTMENT_FUNDING_EVENT_TYPES:
            refund_by_component["funding"] += refund.amount_cny
        elif target.event_type in INVESTMENT_ALLOCATION_EVENT_TYPES:
            refund_by_component["allocation"] += refund.amount_cny
        elif target.event_type == "fee":
            refund_by_component["fee"] += refund.amount_cny

    components = {
        key: component_bases[key] - refund_by_component[key] for key in component_bases
    }
    if any(value < 0 for value in components.values()):
        raise ValueError("refund produced a negative component")
    gross_base = sum(
        (event.amount_cny for event in non_refunds if event.event_type in GROSS_ACTIVITY_EVENT_TYPES),
        Decimal("0.00"),
    )
    gross = gross_base - gross_refund
    component_total = sum(components.values(), Decimal("0.00"))

    event_types_by_group: dict[str, set[str]] = defaultdict(set)
    for event in non_refunds:
        event_types_by_group[event.interconnection_group_id].add(event.event_type)
    funding_and_allocation_group_count = sum(
        1
        for event_types in event_types_by_group.values()
        if set(INVESTMENT_FUNDING_EVENT_TYPES) & event_types
        and set(INVESTMENT_ALLOCATION_EVENT_TYPES) & event_types
    )
    return {
        "schema": "PFIV025Stage5Phase52DualConsumptionV1",
        "model_version": MODEL_VERSION,
        "currency": BASE_CURRENCY,
        "source_record_count": source_record_count,
        "unique_source_record_count": unique_source_record_count,
        "deduped_economic_event_type_count": len(deduped),
        "total_consumption_outflow_cny": gross,
        "living_consumption_cny": components["living"],
        "investment_funding_outflow_cny": components["funding"],
        "investment_allocation_amount_cny": components["allocation"],
        "financial_fee_outflow_cny": components["fee"],
        "refund_offset_cny": gross_refund,
        "component_reconciliation_difference_cny": gross - component_total,
        "funding_and_allocation_group_count": funding_and_allocation_group_count,
        "funding_allocation_explanation_zh": (
            "投资入金表示家庭可用现金进入投资域，投资域内配置表示基金、黄金或证券买入；"
            "两者是同一资金链的不同活动阶段，分别展示并按版本化广义活动口径计数，"
            "不得解释为两次净资产损失。"
        ),
        "investment_activity_is_net_worth_loss": False,
        "model_validation": "blocked_pending_phase_5_3_real_data",
        "calculation_context": "contract_test_only",
    }


def build_dual_metric_surface_contract(metrics: Mapping[str, Any]) -> dict[str, Any]:
    if metrics.get("component_reconciliation_difference_cny") != Decimal("0.00"):
        raise ValueError("dual metric components do not reconcile")
    payload = {
        TOTAL_CONSUMPTION_LABEL_ZH: _money_text(metrics["total_consumption_outflow_cny"]),
        LIVING_CONSUMPTION_LABEL_ZH: _money_text(metrics["living_consumption_cny"]),
        INVESTMENT_FUNDING_LABEL_ZH: _money_text(metrics["investment_funding_outflow_cny"]),
        INVESTMENT_ALLOCATION_LABEL_ZH: _money_text(metrics["investment_allocation_amount_cny"]),
        "currency": BASE_CURRENCY,
        "口径说明": metrics["funding_allocation_explanation_zh"],
        "不等于净资产损失": metrics["investment_activity_is_net_worth_loss"] is False,
        "model_validation": metrics["model_validation"],
    }
    payload_hash = _canonical_hash(payload)
    surfaces = ("homepage", "consumption_page", "report")
    return {
        "schema": "PFIV025Stage5Phase52DualMetricSurfaceContractV1",
        "surface_ids": list(surfaces),
        "surfaces": {surface: dict(payload) for surface in surfaces},
        "surface_hashes": {surface: payload_hash for surface in surfaces},
        "same_payload_hash": True,
        "real_ui_binding_completed": False,
    }


def build_cashflow_windows(
    events: Iterable[FinancialEvent],
    *,
    as_of: date,
) -> dict[str, Any]:
    if not isinstance(as_of, date):
        raise TypeError("as_of must be date")
    deduped, source_record_count, unique_source_record_count = _deduplicate_events(events)
    metrics: dict[int, dict[str, Any]] = {}
    for window_days in CASHFLOW_WINDOWS_DAYS:
        start = as_of - timedelta(days=window_days - 1)
        selected = tuple(event for event in deduped if start <= event.event_date <= as_of)
        if not selected:
            metrics[window_days] = {
                "status": "filtered_empty",
                "coverage_start": start.isoformat(),
                "coverage_end": as_of.isoformat(),
                "record_count": 0,
                "external_inflow_cny": None,
                "external_outflow_cny": None,
                "internal_transfer_cny": None,
                "net_cashflow_cny": None,
            }
            continue
        external_inflow = Decimal("0.00")
        external_outflow = Decimal("0.00")
        internal_transfer = Decimal("0.00")
        for event in selected:
            direction = event_policy(event.event_type).cashflow_direction
            if direction == "inflow":
                external_inflow += event.amount_cny
            elif direction == "outflow":
                external_outflow += event.amount_cny
            elif direction == "internal":
                internal_transfer += event.amount_cny
        metrics[window_days] = {
            "status": "ready",
            "coverage_start": start.isoformat(),
            "coverage_end": as_of.isoformat(),
            "record_count": len(selected),
            "external_inflow_cny": external_inflow,
            "external_outflow_cny": external_outflow,
            "internal_transfer_cny": internal_transfer,
            "net_cashflow_cny": external_inflow - external_outflow,
        }
    return {
        "schema": "PFIV025Stage5Phase52CashflowWindowsV1",
        "as_of": as_of.isoformat(),
        "currency": BASE_CURRENCY,
        "windows": list(CASHFLOW_WINDOWS_DAYS),
        "metrics": metrics,
        "source_record_count": source_record_count,
        "unique_source_record_count": unique_source_record_count,
        "deduped_economic_event_type_count": len(deduped),
        "internal_transfers_excluded_from_net_cashflow": True,
        "model_validation": "blocked_pending_phase_5_3_real_data",
    }


def build_taxonomy_tag_contract() -> dict[str, Any]:
    taxonomy = build_stage5_consumption_taxonomy()
    validation = validate_stage5_taxonomy_constraints(taxonomy)
    default_tags = build_stage6_default_tag_library()
    if validation["limits"]["max_l1_categories"] != STAGE5_TAXONOMY_LIMITS["max_l1_categories"]:
        raise ValueError("taxonomy limits conflict with preserved v0.2.2 policy")
    if "pfi_tag_history" not in STAGE6_TAG_TABLES:
        raise ValueError("tag history persistence contract is missing")
    return {
        "schema": "PFIV025Stage5Phase52TaxonomyTagContractV1",
        "taxonomy_validation": validation,
        "primary_category_per_transaction": 1,
        "default_tag_count": len(default_tags),
        "tag_types": ["default", "custom"],
        "tag_history_required": True,
        "view_filter_modes": ["all", "any"],
        "historical_inactive_tags_retained": True,
        "new_assignment_requires_enabled_tag": True,
        "model_validation": "blocked_pending_phase_5_3_real_data",
    }


def validate_primary_category_assignments(
    assignments: Sequence[Mapping[str, object]],
) -> dict[str, Any]:
    seen: set[str] = set()
    for assignment in assignments:
        source_record_id = str(assignment.get("source_record_id") or "").strip()
        category_id = str(assignment.get("primary_category_id") or "").strip()
        if not source_record_id or not category_id:
            raise ValueError("each record requires exactly one primary category")
        if source_record_id in seen:
            raise ValueError("each record requires exactly one primary category")
        seen.add(source_record_id)
        tag_ids = assignment.get("tag_ids", [])
        if not isinstance(tag_ids, list) or any(not str(tag_id).strip() for tag_id in tag_ids):
            raise ValueError("tag_ids must be a list of non-empty identifiers")
        if len(tag_ids) != len(set(str(tag_id) for tag_id in tag_ids)):
            raise ValueError("tag_ids must not contain duplicates")
    return {
        "schema": "PFIV025Stage5Phase52PrimaryCategoryValidationV1",
        "status": "pass",
        "record_count": len(assignments),
        "primary_category_per_transaction": 1,
    }


def calculate_net_worth(snapshot: CoreFinancialSnapshot) -> Decimal:
    return (
        snapshot.cash_cny
        + snapshot.investment_market_value_cny
        + snapshot.other_assets_cny
        - snapshot.liabilities_cny
    )


def evaluate_core_invariants(
    snapshot: CoreFinancialSnapshot,
    cash: CashRollforward,
    reallocation: InvestmentReallocation,
) -> dict[str, Any]:
    calculated_net_worth = calculate_net_worth(snapshot)
    net_worth_discrepancy = snapshot.reported_net_worth_cny - calculated_net_worth
    expected_closing_cash = (
        cash.opening_cash_cny
        + cash.external_inflows_cny
        - cash.external_outflows_cny
        + cash.adjustments_cny
    )
    cash_discrepancy = cash.closing_cash_cny - expected_closing_cash
    before_reallocation = reallocation.life_cash_before_cny + reallocation.investment_assets_before_cny
    expected_after_reallocation = before_reallocation - reallocation.explicit_fee_cny
    actual_after_reallocation = reallocation.life_cash_after_cny + reallocation.investment_assets_after_cny
    reallocation_discrepancy = actual_after_reallocation - expected_after_reallocation
    passed = (
        net_worth_discrepancy == 0
        and cash_discrepancy == 0
        and reallocation_discrepancy == 0
    )
    return {
        "schema": "PFIV025Stage5Phase52CoreInvariantResultV1",
        "status": "pass" if passed else "failed_closed",
        "ledger_conserved": passed,
        "net_worth_cny": calculated_net_worth if passed else None,
        "net_worth_discrepancy_cny": net_worth_discrepancy,
        "expected_closing_cash_cny": expected_closing_cash,
        "cash_rollforward_discrepancy_cny": cash_discrepancy,
        "investment_reallocation_discrepancy_cny": reallocation_discrepancy,
        "investment_reallocation_changes_net_worth_only_by_explicit_fee": True,
        "blocking_reason_zh": None
        if passed
        else "净资产、现金滚动或投资重配置不变量不守恒，禁止发布财务值。",
        "calculation_context": "contract_test_only",
        "model_validation": "blocked_pending_phase_5_3_real_data",
    }


def calculate_investment_metrics(
    *,
    market_value_cny: Decimal,
    remaining_cost_cny: Decimal,
    sell_proceeds_cny: Decimal,
    allocated_cost_cny: Decimal,
    transaction_fees_cny: Decimal,
    taxes_cny: Decimal,
    dividends_cny: Decimal,
    interest_cny: Decimal,
    holding_costs_cny: Decimal,
    gross_trade_value_cny: Decimal,
    original_currency_exposure: Decimal,
    current_fx_to_cny: Decimal,
    reference_fx_to_cny: Decimal,
    idle_cash_cny: Decimal,
    benchmark_return_rate: Decimal,
) -> dict[str, Any]:
    values = {
        name: _non_negative(name, value)
        for name, value in {
            "market_value_cny": market_value_cny,
            "remaining_cost_cny": remaining_cost_cny,
            "sell_proceeds_cny": sell_proceeds_cny,
            "allocated_cost_cny": allocated_cost_cny,
            "transaction_fees_cny": transaction_fees_cny,
            "taxes_cny": taxes_cny,
            "dividends_cny": dividends_cny,
            "interest_cny": interest_cny,
            "holding_costs_cny": holding_costs_cny,
            "gross_trade_value_cny": gross_trade_value_cny,
            "original_currency_exposure": original_currency_exposure,
            "idle_cash_cny": idle_cash_cny,
            "benchmark_return_rate": benchmark_return_rate,
        }.items()
    }
    current_fx = _decimal("current_fx_to_cny", current_fx_to_cny)
    reference_fx = _decimal("reference_fx_to_cny", reference_fx_to_cny)
    if current_fx <= 0 or reference_fx <= 0:
        raise ValueError("FX rates must be positive")
    unrealized = values["market_value_cny"] - values["remaining_cost_cny"]
    realized_before_costs = values["sell_proceeds_cny"] - values["allocated_cost_cny"]
    realized_net = realized_before_costs - values["transaction_fees_cny"] - values["taxes_cny"]
    total_return = (
        realized_net
        + unrealized
        + values["dividends_cny"]
        + values["interest_cny"]
        - values["holding_costs_cny"]
    )
    denominator = values["gross_trade_value_cny"]
    fee_drag_rate = (
        (values["transaction_fees_cny"] + values["holding_costs_cny"]) / denominator
        if denominator
        else None
    )
    tax_drag_rate = values["taxes_cny"] / denominator if denominator else None
    fx_effect = values["original_currency_exposure"] * (current_fx - reference_fx)
    fx_drag = max(-fx_effect, Decimal("0.00"))
    idle_cash_drag = values["idle_cash_cny"] * values["benchmark_return_rate"]
    return {
        "schema": "PFIV025Stage5Phase52InvestmentMetricsV1",
        "currency": BASE_CURRENCY,
        "market_value_cny": values["market_value_cny"],
        "remaining_cost_cny": values["remaining_cost_cny"],
        "unrealized_pnl_cny": unrealized,
        "realized_pnl_before_costs_cny": realized_before_costs,
        "realized_pnl_net_cny": realized_net,
        "total_return_net_cny": total_return,
        "fee_drag_rate": fee_drag_rate,
        "tax_drag_rate": tax_drag_rate,
        "fx_effect_cny": fx_effect,
        "fx_drag_cny": fx_drag,
        "idle_cash_drag_cny": idle_cash_drag,
        "fees_and_taxes_counted_once": True,
        "calculation_context": "contract_test_only",
        "model_validation": "blocked_pending_phase_5_3_real_data",
    }


def _aggregate_xirr_cashflows(flows: Sequence[XirrCashFlow]) -> tuple[tuple[date, Decimal], ...]:
    by_date: dict[date, Decimal] = defaultdict(lambda: Decimal("0"))
    for flow in flows:
        by_date[flow.cashflow_date] += flow.amount_cny
    return tuple(sorted((flow_date, amount) for flow_date, amount in by_date.items() if amount))


def _sign_change_count(values: Sequence[Decimal]) -> int:
    signs = [1 if value > 0 else -1 for value in values if value]
    return sum(1 for left, right in zip(signs, signs[1:]) if left != right)


def _xnpv(rate: Decimal, flows: Sequence[tuple[date, Decimal]]) -> Decimal:
    if rate <= -1:
        raise ValueError("XIRR rate must be greater than -1")
    first_date = flows[0][0]
    with localcontext() as context:
        context.prec = 50
        base = Decimal("1") + rate
        total = Decimal("0")
        for flow_date, amount in flows:
            year_fraction = Decimal((flow_date - first_date).days) / Decimal(
                XIRR_POLICY["day_count_basis"]
            )
            discount = (base.ln() * year_fraction).exp()
            total += amount / discount
        return +total


def calculate_xirr(flows: Sequence[XirrCashFlow]) -> dict[str, Any]:
    aggregated = _aggregate_xirr_cashflows(tuple(flows))
    if len(aggregated) < 2 or len({flow_date for flow_date, _ in aggregated}) < 2:
        raise ValueError("XIRR requires at least two distinct dated cash flows")
    amounts = [amount for _, amount in aggregated]
    if not any(amount < 0 for amount in amounts) or not any(amount > 0 for amount in amounts):
        raise ValueError("XIRR requires at least one negative and one positive cash flow")
    sign_changes = _sign_change_count(amounts)
    if sign_changes != 1:
        raise ValueError("XIRR sign pattern is non-unique; model is blocked")

    lower = Decimal(XIRR_POLICY["lower_bound"])
    upper = Decimal(XIRR_POLICY["initial_upper_bound"])
    max_upper = Decimal(XIRR_POLICY["maximum_upper_bound"])
    tolerance = Decimal(XIRR_POLICY["npv_tolerance"])
    low_npv = _xnpv(lower, aggregated)
    high_npv = _xnpv(upper, aggregated)
    while low_npv * high_npv > 0 and upper < max_upper:
        upper = min(upper * Decimal("2"), max_upper)
        high_npv = _xnpv(upper, aggregated)
    if low_npv * high_npv > 0:
        raise ValueError("XIRR root is not bracketed; model is blocked")

    midpoint = Decimal("0")
    midpoint_npv = Decimal("Infinity")
    iterations = 0
    for iterations in range(1, int(XIRR_POLICY["max_iterations"]) + 1):
        midpoint = (lower + upper) / Decimal("2")
        midpoint_npv = _xnpv(midpoint, aggregated)
        if abs(midpoint_npv) <= tolerance:
            break
        if low_npv * midpoint_npv <= 0:
            upper = midpoint
            high_npv = midpoint_npv
        else:
            lower = midpoint
            low_npv = midpoint_npv
    if abs(midpoint_npv) > tolerance:
        raise ValueError("XIRR did not converge within the configured tolerance")
    quantized_rate = midpoint.quantize(Decimal(XIRR_POLICY["rate_quantum"]))
    residual = abs(_xnpv(quantized_rate, aggregated))
    return {
        "schema": "PFIV025Stage5Phase52XirrResultV1",
        "xirr": quantized_rate,
        "unit": "annual_decimal_rate",
        "day_count_basis": XIRR_POLICY["day_count_basis"],
        "cashflow_count": len(aggregated),
        "sign_change_count": sign_changes,
        "iterations": iterations,
        "residual_abs": residual,
        "calculation_context": "contract_test_only",
        "model_validation": "blocked_pending_phase_5_3_real_data",
    }


def build_financial_model_ui_report_contract() -> dict[str, Any]:
    return {
        "schema": "PFIV025Stage5Phase52UIReportParameterContractV1",
        "model_version": MODEL_VERSION,
        "parameters": json.loads(json.dumps(FINANCIAL_MODEL_CONFIG, ensure_ascii=False)),
        "surface_ids": ["homepage", "consumption_page", "report"],
        "real_ui_binding_completed": False,
        "real_report_binding_completed": False,
    }


def _json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_financial_model_parameter_consistency_report() -> dict[str, Any]:
    conflicts: list[str] = []
    registry = _json_object(FORMULA_REGISTRY_PATH)
    formulas = registry.get("formulas", [])
    registry_formulas = {
        str(formula.get("formula_id")): formula
        for formula in formulas
        if isinstance(formula, Mapping) and str(formula.get("formula_id")) in FORMULA_IDS
    }
    if tuple(sorted(registry_formulas)) != FORMULA_IDS:
        conflicts.append("formula_registry_json.formula_ids")
    registry_parameter_ids = {
        parameter_id
        for formula in registry_formulas.values()
        for parameter_id in formula.get("parameters", [])
        if isinstance(parameter_id, str) and ".." not in parameter_id
    }
    if registry_parameter_ids != set(PARAMETER_IDS):
        conflicts.append("formula_registry_json.parameter_ids")

    catalog = _json_object(PARAMETER_CATALOG_PATH)
    yaml_config = catalog.get("financial_models_v025")
    if yaml_config != FINANCIAL_MODEL_CONFIG:
        conflicts.append("pfi_parameters_yaml")
    ui_config = build_financial_model_ui_report_contract()["parameters"]
    if ui_config != FINANCIAL_MODEL_CONFIG:
        conflicts.append("ui_report_contract")

    human_text = HUMAN_PARAMETER_PATH.read_text(encoding="utf-8")
    required_human_markers = (
        MODEL_VERSION,
        "7|21|30|60|90|180|360",
        "max_l1=12;max_l2_per_l1=5;max_l2_total=50;primary=1",
        "day_basis=365;tolerance=0.0000000001;max_iterations=256;multiple_sign_change=blocked_non_unique",
        TOTAL_CONSUMPTION_LABEL_ZH,
        INVESTMENT_ALLOCATION_LABEL_ZH,
    )
    missing_markers = [marker for marker in required_human_markers if marker not in human_text]
    if missing_markers:
        conflicts.append("模型参数文件.md:" + "|".join(missing_markers))
    return {
        "schema": "PFIV025Stage5Phase52ParameterConsistencyV1",
        "status": "pass" if not conflicts else "fail",
        "model_version": MODEL_VERSION,
        "formula_ids": list(FORMULA_IDS),
        "parameter_ids": list(PARAMETER_IDS),
        "carriers": [
            "formula_registry_json",
            "pfi_parameters_yaml",
            "python_runtime",
            "ui_report_contract",
            "模型参数文件.md",
        ],
        "conflict_count": len(conflicts),
        "conflicts": conflicts,
    }
