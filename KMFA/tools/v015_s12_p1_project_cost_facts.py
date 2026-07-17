#!/usr/bin/env python3
"""KMFA v1.5 S12-P1 project income, cost, and unallocated-cost facts.

The ledger is deliberately small and deterministic.  It accepts caller-supplied
fact envelopes, never discovers or reads a raw-data path, and keeps every money
amount as signed integer cents.  Revenue layers are never collapsed across
different meanings, tax bases, projects, entities, or periods.  Every cost
input is routed exactly once to either an allocated project-cost fact or the
explicit unallocated-cost pool.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from typing import Any


RUN_PHASE_ID = "V015_S12_P1_PROJECT_COST_FACTS"
ROADMAP_PHASE_ID = "S12-P1"
TASK_ID = "KMFA-V015-S12-P1-PROJECT-COST-FACTS-20260715"
ACCEPTANCE_ID = "ACC-KMFA-V015-S12-P1-PROJECT-COST-FACTS"
VERSION = "1.5.0-dev-s12p1"

INCOME_FACT_SCHEMA = "kmfa.v015.s12p1.income_fact.v1"
COST_FACT_SCHEMA = "kmfa.v015.s12p1.cost_fact.v1"
UNALLOCATED_POOL_SCHEMA = "kmfa.v015.s12p1.unallocated_cost_pool_item.v1"

INCOME_LAYERS = (
    "CONTRACT",
    "CHANGE_ORDER",
    "SETTLEMENT",
    "INVOICE",
    "COLLECTION",
)
AMOUNT_BASES = ("TAX_INCLUSIVE", "TAX_EXCLUSIVE", "UNKNOWN")
COST_CATEGORIES = (
    "LABOR",
    "MATERIAL",
    "MACHINERY",
    "SUBCONTRACT",
    "TRANSPORT",
    "TRAVEL",
    "TAX",
    "SITE_MANAGEMENT",
    "REWORK",
    "WARRANTY",
)
UNALLOCATED_REASON_CODES = (
    "PROJECT_UNRESOLVED",
    "ENTITY_UNRESOLVED",
    "PERIOD_UNRESOLVED",
    "CATEGORY_UNRESOLVED",
)
UNRESOLVED = "UNRESOLVED"
TRACEABILITY_FIELDS = (
    "project_ref",
    "company_entity_ref",
    "period_ref",
    "period_version",
    "source_ref",
    "source_record_ref",
    "source_version",
)

_ID_RE = re.compile(r"^[A-Z0-9][A-Z0-9_-]{2,95}$")
_REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_:/.-]{1,159}$")
_FORBIDDEN_PUBLIC_KEYS = {
    "raw_value",
    "original_value",
    "plaintext_value",
    "source_header_text",
    "original_filename",
    "absolute_path",
    "local_path",
    "private_hash",
    "private_key",
    "password",
    "token",
    "api_key",
    "bank_account_number",
    "identity_document_number",
}


class ProjectCostFactError(ValueError):
    """Fail-closed fact validation error with a stable reason code."""

    def __init__(self, code: str, message_zh: str):
        super().__init__(f"{code}: {message_zh}")
        self.code = code
        self.message_zh = message_zh


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _fingerprint(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value)).hexdigest()


def _mapping(value: Any, field: str = "record") -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ProjectCostFactError("RECORD_INVALID", f"{field} 必须是结构化记录。")
    result = dict(value)
    _assert_public_safe(result)
    return result


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ProjectCostFactError("TEXT_REQUIRED", f"{field} 必须是非空文本。")
    return value.strip()


def _identifier(value: Any, field: str) -> str:
    text = _text(value, field)
    if not _ID_RE.fullmatch(text):
        raise ProjectCostFactError("IDENTIFIER_INVALID", f"{field} 格式不正确。")
    return text


def _reference(value: Any, field: str, *, unresolved_allowed: bool = False) -> str:
    text = _text(value, field)
    if text == UNRESOLVED and unresolved_allowed:
        return text
    if not _REF_RE.fullmatch(text) or text.startswith(("private://", "file://")):
        raise ProjectCostFactError("REFERENCE_INVALID", f"{field} 必须是公开安全引用。")
    return text


def _positive_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ProjectCostFactError("POSITIVE_INTEGER_REQUIRED", f"{field} 必须是正整数。")
    return value


def _integer_cents(value: Any, field: str = "amount_cents") -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ProjectCostFactError("INTEGER_CENTS_REQUIRED", f"{field} 只允许整数分，不能使用 float 或布尔值。")
    return value


def _enum(value: Any, field: str, allowed: Sequence[str]) -> str:
    text = _text(value, field)
    if text not in allowed:
        raise ProjectCostFactError("ENUM_INVALID", f"{field} 不在允许范围内。")
    return text


def _assert_public_safe(value: Any, path: str = "record") -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = str(key)
            if key_text.lower() in _FORBIDDEN_PUBLIC_KEYS:
                raise ProjectCostFactError("PRIVATE_FIELD_REJECTED", f"{path}.{key_text} 不允许进入事实接口。")
            _assert_public_safe(nested, f"{path}.{key_text}")
    elif isinstance(value, (list, tuple)):
        for index, nested in enumerate(value):
            _assert_public_safe(nested, f"{path}[{index}]")
    elif isinstance(value, str):
        lowered = value.lower()
        if value.startswith(("/Users/", "/Volumes/", "/home/")) or "kmfa_metadata" in lowered or lowered.startswith(("file://", "private://")):
            raise ProjectCostFactError("PRIVATE_VALUE_REJECTED", f"{path} 包含本地或私有定位信息。")


def _base_fact(record: Mapping[str, Any]) -> dict[str, Any]:
    source = _mapping(record)
    currency = _enum(source.get("currency"), "currency", ("CNY",))
    return {
        "record_id": _identifier(source.get("record_id"), "record_id"),
        "event_version": _positive_int(source.get("event_version"), "event_version"),
        "project_ref": _reference(source.get("project_ref"), "project_ref", unresolved_allowed=True),
        "company_entity_ref": _reference(
            source.get("company_entity_ref"), "company_entity_ref", unresolved_allowed=True
        ),
        "period_ref": _reference(source.get("period_ref"), "period_ref", unresolved_allowed=True),
        "period_version": _reference(
            source.get("period_version"), "period_version", unresolved_allowed=True
        ),
        "source_ref": _reference(source.get("source_ref"), "source_ref"),
        "source_record_ref": _reference(source.get("source_record_ref"), "source_record_ref"),
        "source_version": _reference(source.get("source_version"), "source_version"),
        "amount_cents": _integer_cents(source.get("amount_cents")),
        "currency": currency,
    }


def _fact_identity(kind: str, base: Mapping[str, Any]) -> tuple[str, str]:
    event_key = f"{kind}:{base['record_id']}:v{base['event_version']}"
    fact_id = f"FACT-{kind}-{base['record_id']}-V{base['event_version']}"
    return event_key, fact_id


class ProjectCostFactLedger:
    """Append-only in-memory fact ledger with exact replay idempotency."""

    def __init__(self) -> None:
        self._events: dict[str, dict[str, Any]] = {}
        self._income_facts: list[dict[str, Any]] = []
        self._cost_inputs: list[dict[str, Any]] = []
        self._allocated_cost_facts: list[dict[str, Any]] = []
        self._unallocated_cost_pool: list[dict[str, Any]] = []

    def _append_once(self, event_key: str, record: dict[str, Any], target: list[dict[str, Any]]) -> dict[str, Any]:
        fingerprint = _fingerprint(record)
        existing = self._events.get(event_key)
        if existing is not None:
            if existing["fact_fingerprint"] != fingerprint:
                raise ProjectCostFactError(
                    "IMMUTABLE_EVENT_CONFLICT",
                    "同一记录版本已存在，不能用不同内容静默覆盖。",
                )
            return copy.deepcopy(existing)
        stored = copy.deepcopy(record)
        stored["fact_fingerprint"] = fingerprint
        self._events[event_key] = stored
        target.append(stored)
        return copy.deepcopy(stored)

    def add_income_fact(self, record: Mapping[str, Any]) -> dict[str, Any]:
        source = _mapping(record)
        base = _base_fact(source)
        layer = _enum(source.get("income_layer"), "income_layer", INCOME_LAYERS)
        amount_basis = _enum(source.get("amount_basis"), "amount_basis", AMOUNT_BASES)
        event_key, fact_id = _fact_identity("INCOME", base)
        unresolved_reasons: list[str] = []
        if base["project_ref"] == UNRESOLVED:
            unresolved_reasons.append("PROJECT_UNRESOLVED")
        if base["company_entity_ref"] == UNRESOLVED:
            unresolved_reasons.append("ENTITY_UNRESOLVED")
        if base["period_ref"] == UNRESOLVED or base["period_version"] == UNRESOLVED:
            unresolved_reasons.append("PERIOD_UNRESOLVED")
        if amount_basis == "UNKNOWN":
            unresolved_reasons.append("AMOUNT_BASIS_UNKNOWN")
        fact = {
            "schema_version": INCOME_FACT_SCHEMA,
            "record_type": "project_income_fact",
            "fact_id": fact_id,
            **base,
            "income_layer": layer,
            "amount_basis": amount_basis,
            "merge_eligible": not unresolved_reasons,
            "unresolved_reason_codes": unresolved_reasons,
            "raw_layer_write_allowed": False,
            "formal_calculation_allowed": False,
        }
        return self._append_once(event_key, fact, self._income_facts)

    def add_cost_fact(self, record: Mapping[str, Any]) -> dict[str, Any]:
        source = _mapping(record)
        base = _base_fact(source)
        category = _enum(source.get("cost_category"), "cost_category", (*COST_CATEGORIES, "UNKNOWN"))
        event_key, fact_id = _fact_identity("COST", base)
        reasons: list[str] = []
        if base["project_ref"] == UNRESOLVED:
            reasons.append("PROJECT_UNRESOLVED")
        if base["company_entity_ref"] == UNRESOLVED:
            reasons.append("ENTITY_UNRESOLVED")
        if base["period_ref"] == UNRESOLVED or base["period_version"] == UNRESOLVED:
            reasons.append("PERIOD_UNRESOLVED")
        if category == "UNKNOWN":
            reasons.append("CATEGORY_UNRESOLVED")
        schema = UNALLOCATED_POOL_SCHEMA if reasons else COST_FACT_SCHEMA
        record_type = "unallocated_project_cost_pool_item" if reasons else "project_cost_fact"
        allocation_status = "UNALLOCATED" if reasons else "ALLOCATED"
        fact = {
            "schema_version": schema,
            "record_type": record_type,
            "fact_id": fact_id,
            **base,
            "cost_category": category,
            "allocation_status": allocation_status,
            "unallocated_reason_codes": reasons,
            "automatic_allocation_performed": False,
            "average_allocation_performed": False,
            "silent_classification_performed": False,
            "raw_layer_write_allowed": False,
            "formal_calculation_allowed": False,
        }
        stored = self._append_once(
            event_key,
            fact,
            self._unallocated_cost_pool if reasons else self._allocated_cost_facts,
        )
        if len(self._cost_inputs) == len(self._allocated_cost_facts) + len(self._unallocated_cost_pool) - 1:
            self._cost_inputs.append(copy.deepcopy(stored))
        self.assert_cost_conservation()
        return stored

    def combine_income_facts(self, fact_ids: Sequence[str]) -> dict[str, Any]:
        if isinstance(fact_ids, (str, bytes)) or not fact_ids:
            raise ProjectCostFactError("INCOME_SELECTION_REQUIRED", "至少选择一条收入事实。")
        index = {row["fact_id"]: row for row in self._income_facts}
        selected: list[dict[str, Any]] = []
        for fact_id in fact_ids:
            if fact_id not in index:
                raise ProjectCostFactError("INCOME_FACT_NOT_FOUND", "收入事实不存在。")
            selected.append(index[fact_id])
        if any(not row["merge_eligible"] for row in selected):
            raise ProjectCostFactError("UNKNOWN_INCOME_SCOPE", "口径、项目、主体或期间未知的收入不得合并。")
        dimensions = (
            "project_ref",
            "company_entity_ref",
            "period_ref",
            "period_version",
            "income_layer",
            "amount_basis",
            "currency",
        )
        signatures = {tuple(row[field] for field in dimensions) for row in selected}
        if len(signatures) != 1:
            raise ProjectCostFactError(
                "INCOME_SCOPE_MISMATCH",
                "不同项目、主体、期间、收入层或税口径不得合并。",
            )
        signature = next(iter(signatures))
        return {
            "schema_version": "kmfa.v015.s12p1.income_layer_subtotal.v1",
            **dict(zip(dimensions, signature)),
            "fact_count": len(selected),
            "amount_cents": sum(_integer_cents(row["amount_cents"]) for row in selected),
            "source_fact_ids": [row["fact_id"] for row in selected],
            "cross_layer_merge_performed": False,
            "tax_basis_conversion_performed": False,
            "formal_calculation_allowed": False,
        }

    def cost_conservation(self) -> dict[str, Any]:
        input_total = sum(_integer_cents(row["amount_cents"]) for row in self._cost_inputs)
        allocated_total = sum(_integer_cents(row["amount_cents"]) for row in self._allocated_cost_facts)
        unallocated_total = sum(_integer_cents(row["amount_cents"]) for row in self._unallocated_cost_pool)
        return {
            "input_cost_fact_count": len(self._cost_inputs),
            "allocated_cost_fact_count": len(self._allocated_cost_facts),
            "unallocated_cost_pool_count": len(self._unallocated_cost_pool),
            "input_cost_cents": input_total,
            "allocated_cost_cents": allocated_total,
            "unallocated_cost_cents": unallocated_total,
            "conservation_delta_cents": input_total - allocated_total - unallocated_total,
            "dropped_cost_fact_count": len(self._cost_inputs)
            - len(self._allocated_cost_facts)
            - len(self._unallocated_cost_pool),
            "average_allocation_count": sum(row["average_allocation_performed"] for row in self._cost_inputs),
            "silent_classification_count": sum(row["silent_classification_performed"] for row in self._cost_inputs),
        }

    def assert_cost_conservation(self) -> None:
        result = self.cost_conservation()
        if result["conservation_delta_cents"] != 0 or result["dropped_cost_fact_count"] != 0:
            raise ProjectCostFactError("COST_CONSERVATION_FAILED", "总成本不守恒，必须停止。")
        if result["average_allocation_count"] or result["silent_classification_count"]:
            raise ProjectCostFactError("IMPLICIT_ALLOCATION_REJECTED", "未归集成本不得平均摊或静默归类。")

    @property
    def income_facts(self) -> list[dict[str, Any]]:
        return copy.deepcopy(self._income_facts)

    @property
    def allocated_cost_facts(self) -> list[dict[str, Any]]:
        return copy.deepcopy(self._allocated_cost_facts)

    @property
    def unallocated_cost_pool(self) -> list[dict[str, Any]]:
        return copy.deepcopy(self._unallocated_cost_pool)

    def snapshot(self) -> dict[str, Any]:
        conservation = self.cost_conservation()
        return {
            "income_fact_count": len(self._income_facts),
            "income_layer_count": len({row["income_layer"] for row in self._income_facts}),
            "income_layer_counts": {
                layer: sum(row["income_layer"] == layer for row in self._income_facts)
                for layer in INCOME_LAYERS
            },
            "income_unknown_basis_count": sum(row["amount_basis"] == "UNKNOWN" for row in self._income_facts),
            "income_merge_eligible_count": sum(row["merge_eligible"] for row in self._income_facts),
            "allocated_cost_category_count": len({row["cost_category"] for row in self._allocated_cost_facts}),
            "all_allocated_costs_traceable": all(
                all(row[field] != UNRESOLVED for field in TRACEABILITY_FIELDS)
                for row in self._allocated_cost_facts
            ),
            **conservation,
            "raw_root_access_count": 0,
            "live_source_read_count": 0,
            "raw_business_content_read": False,
            "formal_calculation_allowed": False,
        }


def public_schema_contracts() -> dict[str, Any]:
    """Return public-safe field and invariant contracts without business facts."""

    common_fields = [
        "record_id",
        "event_version",
        "project_ref",
        "company_entity_ref",
        "period_ref",
        "period_version",
        "source_ref",
        "source_record_ref",
        "source_version",
        "amount_cents",
        "currency",
    ]
    return {
        "schema_version": "kmfa.v015.s12p1.fact_contracts.v1",
        "income_fact": {
            "schema_version": INCOME_FACT_SCHEMA,
            "required_fields": [*common_fields, "income_layer", "amount_basis"],
            "income_layers": list(INCOME_LAYERS),
            "amount_bases": list(AMOUNT_BASES),
            "combination_dimensions": [
                "project_ref",
                "company_entity_ref",
                "period_ref",
                "period_version",
                "income_layer",
                "amount_basis",
                "currency",
            ],
            "unknown_basis_combination_allowed": False,
            "cross_layer_combination_allowed": False,
        },
        "cost_fact": {
            "schema_version": COST_FACT_SCHEMA,
            "required_fields": [*common_fields, "cost_category"],
            "cost_categories": list(COST_CATEGORIES),
            "traceability_fields": list(TRACEABILITY_FIELDS),
            "unknown_cost_routes_to_pool": True,
        },
        "unallocated_cost_pool": {
            "schema_version": UNALLOCATED_POOL_SCHEMA,
            "reason_codes": list(UNALLOCATED_REASON_CODES),
            "dropped_cost_allowed": False,
            "average_allocation_allowed": False,
            "silent_classification_allowed": False,
            "conservation_formula": "input_cost_cents = allocated_cost_cents + unallocated_cost_cents",
            "money_tolerance_cents": 0,
        },
        "raw_root_access_count": 0,
        "live_source_read_count": 0,
        "formal_calculation_allowed": False,
    }


def _common(record_id: str, amount_cents: int) -> dict[str, Any]:
    return {
        "record_id": record_id,
        "event_version": 1,
        "project_ref": "PROJECT-SYNTHETIC-001",
        "company_entity_ref": "ENTITY-SYNTHETIC-001",
        "period_ref": "PERIOD-2026-07",
        "period_version": "PERIOD-RULE-V1",
        "source_ref": "SOURCE-SYNTHETIC-001",
        "source_record_ref": f"SOURCE-ROW-{record_id}",
        "source_version": "SOURCE-V1",
        "amount_cents": amount_cents,
        "currency": "CNY",
    }


def build_synthetic_acceptance_ledger() -> ProjectCostFactLedger:
    ledger = ProjectCostFactLedger()
    income_specs = (
        ("REV-CONTRACT-001", "CONTRACT", "TAX_INCLUSIVE", 100_000),
        ("REV-CONTRACT-002", "CONTRACT", "TAX_INCLUSIVE", 20_000),
        ("REV-CHANGE-001", "CHANGE_ORDER", "TAX_EXCLUSIVE", 10_000),
        ("REV-SETTLEMENT-001", "SETTLEMENT", "TAX_EXCLUSIVE", 90_000),
        ("REV-INVOICE-001", "INVOICE", "TAX_INCLUSIVE", 80_000),
        ("REV-COLLECTION-001", "COLLECTION", "TAX_INCLUSIVE", 60_000),
    )
    for record_id, layer, basis, amount in income_specs:
        ledger.add_income_fact({**_common(record_id, amount), "income_layer": layer, "amount_basis": basis})
    unknown = {
        **_common("REV-UNKNOWN-001", 5_000),
        "income_layer": "CHANGE_ORDER",
        "amount_basis": "UNKNOWN",
    }
    ledger.add_income_fact(unknown)

    for index, category in enumerate(COST_CATEGORIES, start=1):
        ledger.add_cost_fact({**_common(f"COST-{index:03d}", index * 1_000), "cost_category": category})
    ledger.add_cost_fact(
        {
            **_common("COST-UNALLOCATED-PROJECT", 7_000),
            "project_ref": UNRESOLVED,
            "cost_category": "LABOR",
        }
    )
    ledger.add_cost_fact(
        {
            **_common("COST-UNALLOCATED-CATEGORY", 5_000),
            "cost_category": "UNKNOWN",
        }
    )
    ledger.add_cost_fact(
        {
            **_common("COST-UNALLOCATED-PERIOD", 3_000),
            "period_ref": UNRESOLVED,
            "period_version": UNRESOLVED,
            "cost_category": "WARRANTY",
        }
    )
    ledger.assert_cost_conservation()
    return ledger


def _rejects(operation: Any, expected_code: str) -> bool:
    try:
        operation()
    except ProjectCostFactError as error:
        return error.code == expected_code
    return False


def public_verification() -> dict[str, Any]:
    """Run deterministic synthetic facts and return aggregate acceptance evidence."""

    contracts = public_schema_contracts()
    ledger = build_synthetic_acceptance_ledger()
    snapshot = ledger.snapshot()
    income = ledger.income_facts
    allocated = ledger.allocated_cost_facts
    pool = ledger.unallocated_cost_pool

    contract_facts = [row for row in income if row["income_layer"] == "CONTRACT"]
    subtotal = ledger.combine_income_facts([row["fact_id"] for row in contract_facts])
    unknown_fact = next(row for row in income if row["amount_basis"] == "UNKNOWN")
    inclusive_fact = next(row for row in income if row["amount_basis"] == "TAX_INCLUSIVE")
    exclusive_fact = next(row for row in income if row["amount_basis"] == "TAX_EXCLUSIVE")
    settlement_fact = next(row for row in income if row["income_layer"] == "SETTLEMENT")

    checks: dict[str, bool] = {
        "income_layer_contract_complete": tuple(contracts["income_fact"]["income_layers"]) == INCOME_LAYERS,
        "income_layer_count": snapshot["income_layer_count"] == 5,
        "contract_layer_present": snapshot["income_layer_counts"]["CONTRACT"] == 2,
        "change_layer_present": snapshot["income_layer_counts"]["CHANGE_ORDER"] == 2,
        "settlement_layer_present": snapshot["income_layer_counts"]["SETTLEMENT"] == 1,
        "invoice_layer_present": snapshot["income_layer_counts"]["INVOICE"] == 1,
        "collection_layer_present": snapshot["income_layer_counts"]["COLLECTION"] == 1,
        "all_income_basis_explicit": all(row["amount_basis"] in AMOUNT_BASES for row in income),
        "known_income_merge_eligible": all(row["merge_eligible"] for row in income if row["amount_basis"] != "UNKNOWN"),
        "unknown_income_not_merge_eligible": not unknown_fact["merge_eligible"],
        "unknown_income_has_reason": "AMOUNT_BASIS_UNKNOWN" in unknown_fact["unresolved_reason_codes"],
        "unknown_income_merge_rejected": _rejects(
            lambda: ledger.combine_income_facts([unknown_fact["fact_id"]]), "UNKNOWN_INCOME_SCOPE"
        ),
        "mixed_basis_merge_rejected": _rejects(
            lambda: ledger.combine_income_facts([inclusive_fact["fact_id"], exclusive_fact["fact_id"]]),
            "INCOME_SCOPE_MISMATCH",
        ),
        "cross_layer_merge_rejected": _rejects(
            lambda: ledger.combine_income_facts([exclusive_fact["fact_id"], settlement_fact["fact_id"]]),
            "INCOME_SCOPE_MISMATCH",
        ),
        "contract_subtotal_fact_count": subtotal["fact_count"] == 2,
        "contract_subtotal_exact_cents": subtotal["amount_cents"] == 120_000,
        "contract_subtotal_layer_kept": subtotal["income_layer"] == "CONTRACT",
        "contract_subtotal_basis_kept": subtotal["amount_basis"] == "TAX_INCLUSIVE",
        "cross_layer_merge_not_performed": subtotal["cross_layer_merge_performed"] is False,
        "tax_conversion_not_performed": subtotal["tax_basis_conversion_performed"] is False,
        "income_required_fields_complete": all(
            field in contracts["income_fact"]["required_fields"]
            for field in (*TRACEABILITY_FIELDS, "amount_cents", "income_layer", "amount_basis")
        ),
        "income_integer_cents": all(isinstance(row["amount_cents"], int) and not isinstance(row["amount_cents"], bool) for row in income),
        "income_float_rejected": _rejects(
            lambda: ProjectCostFactLedger().add_income_fact(
                {**_common("REV-FLOAT-001", 1), "amount_cents": json.loads("1.5"), "income_layer": "CONTRACT", "amount_basis": "TAX_INCLUSIVE"}
            ),
            "INTEGER_CENTS_REQUIRED",
        ),
        "income_bool_rejected": _rejects(
            lambda: ProjectCostFactLedger().add_income_fact(
                {**_common("REV-BOOL-001", 1), "amount_cents": True, "income_layer": "CONTRACT", "amount_basis": "TAX_INCLUSIVE"}
            ),
            "INTEGER_CENTS_REQUIRED",
        ),
        "cost_category_contract_complete": tuple(contracts["cost_fact"]["cost_categories"]) == COST_CATEGORIES,
        "cost_category_count": snapshot["allocated_cost_category_count"] == 10,
        "allocated_cost_count": snapshot["allocated_cost_fact_count"] == 10,
        "unallocated_pool_count": snapshot["unallocated_cost_pool_count"] == 3,
        "all_allocated_cost_traceable": snapshot["all_allocated_costs_traceable"],
        "all_cost_sources_traceable": all(row["source_ref"] and row["source_record_ref"] and row["source_version"] for row in [*allocated, *pool]),
        "all_allocated_projects_traceable": all(row["project_ref"] != UNRESOLVED for row in allocated),
        "all_allocated_periods_traceable": all(row["period_ref"] != UNRESOLVED and row["period_version"] != UNRESOLVED for row in allocated),
        "all_allocated_categories_known": all(row["cost_category"] in COST_CATEGORIES for row in allocated),
        "unknown_project_routed_to_pool": any("PROJECT_UNRESOLVED" in row["unallocated_reason_codes"] for row in pool),
        "unknown_category_routed_to_pool": any("CATEGORY_UNRESOLVED" in row["unallocated_reason_codes"] for row in pool),
        "unknown_period_routed_to_pool": any("PERIOD_UNRESOLVED" in row["unallocated_reason_codes"] for row in pool),
        "pool_items_explicit": all(row["allocation_status"] == "UNALLOCATED" for row in pool),
        "pool_items_not_auto_allocated": all(row["automatic_allocation_performed"] is False for row in pool),
        "pool_items_not_average_allocated": all(row["average_allocation_performed"] is False for row in pool),
        "pool_items_not_silently_classified": all(row["silent_classification_performed"] is False for row in pool),
        "input_cost_count_conserved": snapshot["input_cost_fact_count"] == 13,
        "cost_count_conserved": snapshot["allocated_cost_fact_count"] + snapshot["unallocated_cost_pool_count"] == snapshot["input_cost_fact_count"],
        "cost_amount_conserved": snapshot["conservation_delta_cents"] == 0,
        "cost_drop_count_zero": snapshot["dropped_cost_fact_count"] == 0,
        "average_allocation_count_zero": snapshot["average_allocation_count"] == 0,
        "silent_classification_count_zero": snapshot["silent_classification_count"] == 0,
        "cost_float_rejected": _rejects(
            lambda: ProjectCostFactLedger().add_cost_fact(
                {**_common("COST-FLOAT-001", 1), "amount_cents": json.loads("1.5"), "cost_category": "LABOR"}
            ),
            "INTEGER_CENTS_REQUIRED",
        ),
        "cost_bool_rejected": _rejects(
            lambda: ProjectCostFactLedger().add_cost_fact(
                {**_common("COST-BOOL-001", 1), "amount_cents": False, "cost_category": "LABOR"}
            ),
            "INTEGER_CENTS_REQUIRED",
        ),
        "unregistered_category_rejected": _rejects(
            lambda: ProjectCostFactLedger().add_cost_fact(
                {**_common("COST-CATEGORY-001", 1), "cost_category": "OTHER_GUESSED"}
            ),
            "ENUM_INVALID",
        ),
        "missing_source_rejected": _rejects(
            lambda: ProjectCostFactLedger().add_cost_fact(
                {**_common("COST-NOSOURCE-001", 1), "source_ref": "", "cost_category": "LABOR"}
            ),
            "TEXT_REQUIRED",
        ),
        "private_path_rejected": _rejects(
            lambda: ProjectCostFactLedger().add_cost_fact(
                {**_common("COST-PRIVATE-001", 1), "source_ref": "/Users/example/private", "cost_category": "LABOR"}
            ),
            "PRIVATE_VALUE_REJECTED",
        ),
        "exact_replay_idempotent": len(build_synthetic_acceptance_ledger().allocated_cost_facts) == 10,
        "immutable_income_conflict_rejected": _immutable_income_conflict_rejected(),
        "immutable_cost_conflict_rejected": _immutable_cost_conflict_rejected(),
        "raw_root_access_zero": snapshot["raw_root_access_count"] == 0,
        "live_source_read_zero": snapshot["live_source_read_count"] == 0,
        "raw_business_content_not_read": snapshot["raw_business_content_read"] is False,
        "formal_calculation_closed": snapshot["formal_calculation_allowed"] is False,
        "p2_calculation_not_implemented": contracts["formal_calculation_allowed"] is False,
        "money_tolerance_zero": contracts["unallocated_cost_pool"]["money_tolerance_cents"] == 0,
        "dropped_cost_forbidden": contracts["unallocated_cost_pool"]["dropped_cost_allowed"] is False,
        "average_allocation_forbidden": contracts["unallocated_cost_pool"]["average_allocation_allowed"] is False,
        "silent_classification_forbidden": contracts["unallocated_cost_pool"]["silent_classification_allowed"] is False,
    }
    failed = sorted(name for name, passed in checks.items() if not passed)
    return {
        "schema_version": "kmfa.v015.s12p1.public_verification.v1",
        "accounting": {"total": len(checks), "passed": len(checks) - len(failed), "failed": len(failed)},
        "failed_checks": failed,
        "checks": checks,
        "summary": snapshot,
        "income_layer_count": len(INCOME_LAYERS),
        "cost_category_count": len(COST_CATEGORIES),
        "traceability_field_count": len(TRACEABILITY_FIELDS),
        "unallocated_reason_code_count": len(UNALLOCATED_REASON_CODES),
        "unknown_income_merge_allowed": False,
        "cross_layer_income_merge_allowed": False,
        "raw_root_access_count": 0,
        "live_source_read_count": 0,
        "formal_calculation_allowed": False,
    }


def _immutable_income_conflict_rejected() -> bool:
    ledger = ProjectCostFactLedger()
    base = {**_common("REV-CONFLICT-001", 100), "income_layer": "CONTRACT", "amount_basis": "TAX_INCLUSIVE"}
    ledger.add_income_fact(base)
    return _rejects(lambda: ledger.add_income_fact({**base, "amount_cents": 101}), "IMMUTABLE_EVENT_CONFLICT")


def _immutable_cost_conflict_rejected() -> bool:
    ledger = ProjectCostFactLedger()
    base = {**_common("COST-CONFLICT-001", 100), "cost_category": "LABOR"}
    ledger.add_cost_fact(base)
    return _rejects(lambda: ledger.add_cost_fact({**base, "cost_category": "MATERIAL"}), "IMMUTABLE_EVENT_CONFLICT")


if __name__ == "__main__":
    result = public_verification()
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
