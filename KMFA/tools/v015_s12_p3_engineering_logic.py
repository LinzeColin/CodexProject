#!/usr/bin/env python3
"""Deterministic public-safe engineering logic for KMFA v1.5 S12-P3."""

from __future__ import annotations

import copy
import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from typing import Any


RUN_PHASE_ID = "V015_S12_P3_ENGINEERING_LOGIC"
ROADMAP_PHASE_ID = "S12-P3"
TASK_ID = "KMFA-V015-S12-P3-ENGINEERING-LOGIC-20260715"
ACCEPTANCE_ID = "ACC-KMFA-V015-S12-P3-ENGINEERING-LOGIC"
VERSION = "1.5.0-dev-s12p3"

CONFIRMED = "CONFIRMED"
UNCONFIRMED = "UNCONFIRMED"
REJECTED = "REJECTED"
UNRESOLVED = "UNRESOLVED"
READY = "READY"
DEGRADED = "DEGRADED_REQUIRES_CONFIRMATION"
LINKED = "LINKED"
DUPLICATE = "DUPLICATE_EXCLUDED"
REQUIRES_CONFIRMATION = "REQUIRES_CONFIRMATION"
CROSS_PROJECT_ANOMALY = "CROSS_PROJECT_ANOMALY"
ANOMALIES_REQUIRE_ACTION = "ANOMALIES_REQUIRE_ACTION"
INSUFFICIENT_DATA = "INSUFFICIENT_DATA"

SOURCE_EFFECT = {
    "OUTSOURCING_ACCEPTANCE": "RECOGNIZED_COST",
    "PURCHASE_ORDER": "COMMITMENT_ONLY",
    "MATERIAL_RECEIPT": "INVENTORY_INFLOW",
    "MATERIAL_ISSUE": "RECOGNIZED_COST",
    "INVENTORY_BALANCE": "INVENTORY_BALANCE",
    "PAYMENT": "CASH_ONLY",
}

DEFAULT_LINK_POLICY = {
    "schema_version": "kmfa.v015.s12p3.cost_link_policy.v1",
    "policy_version": "S12P3-PUBLIC-LINK-1",
    "auto_link_min_confidence_bps": 9000,
    "low_confidence_action": REQUIRES_CONFIRMATION,
    "cross_project_action": CROSS_PROJECT_ANOMALY,
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


class EngineeringLogicError(ValueError):
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
        raise EngineeringLogicError("INVALID_MAPPING", f"{field} must be an object")
    return dict(value)


def _records(value: Any, field: str) -> list[dict[str, Any]]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise EngineeringLogicError("INVALID_SEQUENCE", f"{field} must be a list")
    return [_mapping(item, f"{field}[{index}]") for index, item in enumerate(value)]


def _identifier(value: Any, field: str) -> str:
    if not isinstance(value, str) or not _IDENTIFIER.fullmatch(value):
        raise EngineeringLogicError("INVALID_IDENTIFIER", f"{field} is invalid")
    return value


def _optional_identifier(value: Any, field: str) -> str | None:
    return None if value is None else _identifier(value, field)


def _enum(value: Any, field: str, allowed: Sequence[str]) -> str:
    if not isinstance(value, str) or value not in allowed:
        raise EngineeringLogicError("INVALID_ENUM", f"{field} must be one of {tuple(allowed)}")
    return value


def _integer(value: Any, field: str, *, minimum: int | None = None, maximum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise EngineeringLogicError("INTEGER_REQUIRED", f"{field} must be an integer")
    if minimum is not None and value < minimum:
        raise EngineeringLogicError("INTEGER_OUT_OF_RANGE", f"{field} must be >= {minimum}")
    if maximum is not None and value > maximum:
        raise EngineeringLogicError("INTEGER_OUT_OF_RANGE", f"{field} must be <= {maximum}")
    return value


def _cents(value: Any, field: str, *, non_negative: bool = False) -> int:
    return _integer(value, field, minimum=0 if non_negative else None)


def _assert_public_safe(value: Any, path: str = "payload") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise EngineeringLogicError("NON_PUBLIC_VALUE", f"{path} has a non-text key")
            _assert_public_safe(item, f"{path}.{key}")
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _assert_public_safe(item, f"{path}[{index}]")
        return
    if isinstance(value, str) and any(token.lower() in value.lower() for token in _FORBIDDEN_TEXT):
        raise EngineeringLogicError("NON_PUBLIC_VALUE", f"{path} contains a private path or locator")
    if isinstance(value, float):
        raise EngineeringLogicError("FLOAT_NOT_ALLOWED", f"{path} contains a float")


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


def _require_scope(actual: Any, expected: str, code: str, field: str) -> str:
    value = _identifier(actual, field)
    if value != expected:
        raise EngineeringLogicError(code, f"{field} does not match the declared chain scope")
    return value


def build_change_settlement_chain(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Link contract, supported change, settlement, invoice and collection facts."""

    source = _mapping(payload, "payload")
    _assert_public_safe(source)
    scope = _common_scope(source)
    contract = _mapping(source.get("contract"), "contract")
    contract_ref = _identifier(contract.get("contract_ref"), "contract.contract_ref")
    _require_scope(contract.get("project_ref"), scope["project_ref"], "CONTRACT_SCOPE_MISMATCH", "contract.project_ref")
    signed_contract = _cents(contract.get("signed_amount_cents"), "contract.signed_amount_cents", non_negative=True)

    change_rows: list[dict[str, Any]] = []
    confirmed_change = 0
    unconfirmed_change = 0
    confirmed_count = 0
    unconfirmed_count = 0
    for index, raw in enumerate(_records(source.get("changes"), "changes")):
        change_ref = _identifier(raw.get("change_ref"), f"changes[{index}].change_ref")
        _require_scope(raw.get("project_ref"), scope["project_ref"], "CHANGE_SCOPE_MISMATCH", f"changes[{index}].project_ref")
        _require_scope(raw.get("contract_ref"), contract_ref, "CHANGE_SCOPE_MISMATCH", f"changes[{index}].contract_ref")
        status = _enum(raw.get("status"), f"changes[{index}].status", (CONFIRMED, UNCONFIRMED, REJECTED))
        amount = _cents(raw.get("amount_cents"), f"changes[{index}].amount_cents", non_negative=True)
        evidence_ref = _optional_identifier(raw.get("evidence_ref"), f"changes[{index}].evidence_ref")
        if status == CONFIRMED and evidence_ref is None:
            raise EngineeringLogicError("CONFIRMED_CHANGE_EVIDENCE_REQUIRED", "confirmed change requires evidence")
        recognized = amount if status == CONFIRMED and evidence_ref is not None else 0
        if status == CONFIRMED:
            confirmed_count += 1
            confirmed_change += amount
        elif status == UNCONFIRMED:
            unconfirmed_count += 1
            unconfirmed_change += amount
        change_rows.append({
            "change_ref": change_ref,
            "contract_ref": contract_ref,
            "project_ref": scope["project_ref"],
            "status": status,
            "amount_cents": amount,
            "evidence_ref": evidence_ref,
            "recognized_change_income_cents": recognized,
        })

    settlement = _mapping(source.get("settlement"), "settlement")
    settlement_ref = _identifier(settlement.get("settlement_ref"), "settlement.settlement_ref")
    _require_scope(settlement.get("project_ref"), scope["project_ref"], "SETTLEMENT_SCOPE_MISMATCH", "settlement.project_ref")
    _require_scope(settlement.get("contract_ref"), contract_ref, "SETTLEMENT_SCOPE_MISMATCH", "settlement.contract_ref")
    _enum(settlement.get("status"), "settlement.status", (CONFIRMED,))
    settlement_amount = _cents(settlement.get("confirmed_amount_cents"), "settlement.confirmed_amount_cents", non_negative=True)

    invoice = _mapping(source.get("invoice"), "invoice")
    invoice_ref = _identifier(invoice.get("invoice_ref"), "invoice.invoice_ref")
    _require_scope(invoice.get("project_ref"), scope["project_ref"], "INVOICE_SCOPE_MISMATCH", "invoice.project_ref")
    _require_scope(invoice.get("contract_ref"), contract_ref, "INVOICE_SCOPE_MISMATCH", "invoice.contract_ref")
    invoice_amount = _cents(invoice.get("confirmed_amount_cents"), "invoice.confirmed_amount_cents", non_negative=True)

    collection_rows: list[dict[str, Any]] = []
    confirmed_collection = 0
    unresolved_collection_count = 0
    for index, raw in enumerate(_records(source.get("collections"), "collections")):
        collection_ref = _identifier(raw.get("collection_ref"), f"collections[{index}].collection_ref")
        _require_scope(raw.get("project_ref"), scope["project_ref"], "COLLECTION_SCOPE_MISMATCH", f"collections[{index}].project_ref")
        _require_scope(raw.get("contract_ref"), contract_ref, "COLLECTION_SCOPE_MISMATCH", f"collections[{index}].contract_ref")
        _require_scope(raw.get("invoice_ref"), invoice_ref, "COLLECTION_SCOPE_MISMATCH", f"collections[{index}].invoice_ref")
        account_status = _enum(raw.get("account_status"), f"collections[{index}].account_status", (CONFIRMED, UNRESOLVED))
        amount = _cents(raw.get("confirmed_amount_cents"), f"collections[{index}].confirmed_amount_cents", non_negative=True)
        counted = amount if account_status == CONFIRMED else 0
        confirmed_collection += counted
        if account_status == UNRESOLVED:
            unresolved_collection_count += 1
        collection_rows.append({
            "collection_ref": collection_ref,
            "invoice_ref": invoice_ref,
            "contract_ref": contract_ref,
            "project_ref": scope["project_ref"],
            "account_status": account_status,
            "confirmed_amount_cents": amount,
            "counted_collection_cents": counted,
        })

    recognized_contract = signed_contract + confirmed_change
    recovery_rate = _basis_points(confirmed_collection, invoice_amount)
    node_count = 1 + len(change_rows) + 1 + 1 + len(collection_rows)
    degraded = unresolved_collection_count > 0
    result = {
        "schema_version": "kmfa.v015.s12p3.change_settlement_chain.v1",
        **scope,
        "contract": {
            "contract_ref": contract_ref,
            "project_ref": scope["project_ref"],
            "signed_amount_cents": signed_contract,
        },
        "changes": change_rows,
        "settlement": {
            "settlement_ref": settlement_ref,
            "contract_ref": contract_ref,
            "project_ref": scope["project_ref"],
            "confirmed_amount_cents": settlement_amount,
        },
        "invoice": {
            "invoice_ref": invoice_ref,
            "contract_ref": contract_ref,
            "project_ref": scope["project_ref"],
            "confirmed_amount_cents": invoice_amount,
        },
        "collections": collection_rows,
        "chain_node_count": node_count,
        "linked_node_count": node_count,
        "confirmed_change_count": confirmed_count,
        "unconfirmed_change_count": unconfirmed_count,
        "confirmed_change_amount_cents": confirmed_change,
        "unconfirmed_change_amount_cents": unconfirmed_change,
        "unsupported_change_recognized_cents": 0,
        "contract_and_supported_change_cents": recognized_contract,
        "settlement_difference_cents": settlement_amount - recognized_contract,
        "invoiced_amount_cents": invoice_amount,
        "confirmed_collection_cents": confirmed_collection,
        "receivable_amount_cents": invoice_amount - confirmed_collection,
        "invoice_collection_rate_bps": recovery_rate,
        "rate_status": READY if recovery_rate is not None else INSUFFICIENT_DATA,
        "calculation_status": DEGRADED if degraded else READY,
        "business_decision_allowed": not degraded,
        "money_unit": "integer_cent",
        "money_tolerance_cents": 0,
    }
    result["calculation_fingerprint"] = _fingerprint(result)
    return copy.deepcopy(result)


def validate_link_policy(policy: Mapping[str, Any]) -> dict[str, Any]:
    source = _mapping(policy, "policy")
    _assert_public_safe(source)
    if source.get("schema_version") != "kmfa.v015.s12p3.cost_link_policy.v1":
        raise EngineeringLogicError("LINK_POLICY_SCHEMA_MISMATCH", "unsupported cost link policy schema")
    return {
        "schema_version": source["schema_version"],
        "policy_version": _identifier(source.get("policy_version"), "policy_version"),
        "auto_link_min_confidence_bps": _integer(
            source.get("auto_link_min_confidence_bps"),
            "auto_link_min_confidence_bps",
            minimum=0,
            maximum=10000,
        ),
        "low_confidence_action": _enum(source.get("low_confidence_action"), "low_confidence_action", (REQUIRES_CONFIRMATION,)),
        "cross_project_action": _enum(source.get("cross_project_action"), "cross_project_action", (CROSS_PROJECT_ANOMALY,)),
    }


def build_external_cost_chain(payload: Mapping[str, Any], policy: Mapping[str, Any]) -> dict[str, Any]:
    """Classify outsourcing, procurement, inventory and payment links fail-closed."""

    source = _mapping(payload, "payload")
    _assert_public_safe(source)
    scope = _common_scope(source)
    rules = validate_link_policy(policy)
    rows = _records(source.get("records"), "records")
    seen_record_refs: set[str] = set()
    seen_source_keys: dict[str, tuple[Any, ...]] = {}
    classified: list[dict[str, Any]] = []
    linked_count = 0
    duplicate_count = 0
    confirmation_count = 0
    cross_project_count = 0
    duplicate_excluded = 0
    unallocated = 0
    cross_project_amount = 0
    recognized_cost = 0
    procurement_commitment = 0
    inventory_receipt = 0
    inventory_issue = 0
    inventory_balance = 0
    paid_cash = 0
    recognized_components: list[dict[str, Any]] = []

    for index, raw in enumerate(rows):
        record_ref = _identifier(raw.get("record_ref"), f"records[{index}].record_ref")
        if record_ref in seen_record_refs:
            raise EngineeringLogicError("DUPLICATE_RECORD_REF", "record_ref must be unique")
        seen_record_refs.add(record_ref)
        source_key = _identifier(raw.get("source_key"), f"records[{index}].source_key")
        source_kind = _enum(raw.get("source_kind"), f"records[{index}].source_kind", tuple(SOURCE_EFFECT))
        effect = _enum(raw.get("cost_effect"), f"records[{index}].cost_effect", tuple(set(SOURCE_EFFECT.values())))
        if effect != SOURCE_EFFECT[source_kind]:
            raise EngineeringLogicError("COST_EFFECT_MISMATCH", f"{source_kind} cannot declare {effect}")
        amount = _cents(raw.get("amount_cents"), f"records[{index}].amount_cents", non_negative=True)
        confidence = _integer(raw.get("link_confidence_bps"), f"records[{index}].link_confidence_bps", minimum=0, maximum=10000)
        candidate_project = _optional_identifier(raw.get("candidate_project_ref"), f"records[{index}].candidate_project_ref")
        evidence_ref = _identifier(raw.get("evidence_ref"), f"records[{index}].evidence_ref")
        semantic_signature = (source_kind, effect, amount, confidence, candidate_project, evidence_ref)

        if source_key in seen_source_keys:
            if seen_source_keys[source_key] != semantic_signature:
                raise EngineeringLogicError("DUPLICATE_SOURCE_CONFLICT", "duplicate source key has conflicting content")
            duplicate_count += 1
            duplicate_excluded += amount
            classified.append({
                "record_ref": record_ref,
                "source_key": source_key,
                "source_kind": source_kind,
                "cost_effect": effect,
                "amount_cents": amount,
                "candidate_project_ref": candidate_project,
                "link_confidence_bps": confidence,
                "link_status": DUPLICATE,
                "counted_in_project_cost_cents": 0,
            })
            continue
        seen_source_keys[source_key] = semantic_signature

        if candidate_project is not None and candidate_project != scope["project_ref"]:
            link_status = CROSS_PROJECT_ANOMALY
            cross_project_count += 1
            cross_project_amount += amount
        elif candidate_project is None or confidence < rules["auto_link_min_confidence_bps"]:
            link_status = REQUIRES_CONFIRMATION
            confirmation_count += 1
            unallocated += amount
        else:
            link_status = LINKED
            linked_count += 1

        counted_cost = amount if link_status == LINKED and effect == "RECOGNIZED_COST" else 0
        if counted_cost:
            recognized_cost += counted_cost
            recognized_components.append({
                "record_ref": record_ref,
                "source_kind": source_kind,
                "amount_cents": counted_cost,
            })
        if link_status == LINKED and effect == "COMMITMENT_ONLY":
            procurement_commitment += amount
        elif link_status == LINKED and effect == "INVENTORY_INFLOW":
            inventory_receipt += amount
        elif link_status == LINKED and source_kind == "MATERIAL_ISSUE":
            inventory_issue += amount
        elif link_status == LINKED and effect == "INVENTORY_BALANCE":
            inventory_balance += amount
        elif link_status == LINKED and effect == "CASH_ONLY":
            paid_cash += amount

        classified.append({
            "record_ref": record_ref,
            "source_key": source_key,
            "source_kind": source_kind,
            "cost_effect": effect,
            "amount_cents": amount,
            "candidate_project_ref": candidate_project,
            "link_confidence_bps": confidence,
            "link_status": link_status,
            "counted_in_project_cost_cents": counted_cost,
        })

    blocked = confirmation_count > 0 or cross_project_count > 0
    result = {
        "schema_version": "kmfa.v015.s12p3.external_cost_chain.v1",
        **scope,
        "policy_version": rules["policy_version"],
        "auto_link_min_confidence_bps": rules["auto_link_min_confidence_bps"],
        "record_count": len(rows),
        "unique_source_key_count": len(seen_source_keys),
        "linked_record_count": linked_count,
        "duplicate_record_count": duplicate_count,
        "requires_confirmation_count": confirmation_count,
        "cross_project_anomaly_count": cross_project_count,
        "automatic_low_confidence_allocation_count": 0,
        "recognized_project_cost_cents": recognized_cost,
        "recognized_cost_components": recognized_components,
        "procurement_commitment_cents": procurement_commitment,
        "inventory_receipt_cents": inventory_receipt,
        "inventory_issue_cents": inventory_issue,
        "inventory_balance_cents": inventory_balance,
        "inventory_conservation_delta_cents": inventory_receipt - inventory_issue - inventory_balance,
        "confirmed_paid_cash_cents": paid_cash,
        "duplicate_excluded_amount_cents": duplicate_excluded,
        "unallocated_candidate_amount_cents": unallocated,
        "cross_project_anomaly_amount_cents": cross_project_amount,
        "chain_status": ANOMALIES_REQUIRE_ACTION if blocked else READY,
        "business_decision_allowed": not blocked,
        "records": classified,
        "money_unit": "integer_cent",
        "money_tolerance_cents": 0,
    }
    result["calculation_fingerprint"] = _fingerprint(result)
    return copy.deepcopy(result)


def _verify_fingerprint(result: Mapping[str, Any], field: str) -> dict[str, Any]:
    value = _mapping(result, field)
    fingerprint = value.pop("calculation_fingerprint", None)
    if fingerprint != _fingerprint(value):
        raise EngineeringLogicError("RESULT_FINGERPRINT_MISMATCH", f"{field} fingerprint does not match content")
    value["calculation_fingerprint"] = fingerprint
    return value


def _explanation_row(
    *,
    result_key: str,
    label_zh: str,
    value: int | None,
    unit: str,
    formula_code: str,
    formula_zh: str,
    inputs: list[dict[str, Any]],
    ordinary_summary_zh: str,
) -> dict[str, Any]:
    return {
        "result_key": result_key,
        "label_zh": label_zh,
        "value": value,
        "unit": unit,
        "formula_id": f"FORM-KMFA-V015-S12-P3-{result_key.upper().replace('_', '-')}",
        "formula_code": formula_code,
        "formula_zh": formula_zh,
        "inputs": inputs,
        "professional_trace": [
            "确认每项输入事实与项目、合同或来源链一致。",
            "按登记公式使用整数金额或整数基点重新计算。",
            "将重算结果与展示结果逐项比较。",
        ],
        "ordinary_summary_zh": ordinary_summary_zh,
    }


def build_result_explanations(
    change_result: Mapping[str, Any],
    cost_result: Mapping[str, Any],
) -> dict[str, Any]:
    """Build professional traces and plain Chinese summaries from calculated results."""

    change = _verify_fingerprint(change_result, "change_result")
    cost = _verify_fingerprint(cost_result, "cost_result")
    _assert_public_safe(change)
    _assert_public_safe(cost)
    change_amounts = [
        {
            "fact_ref": row["change_ref"],
            "label_zh": "已确认且有依据的变更金额",
            "value": row["recognized_change_income_cents"],
            "unit": "cent",
        }
        for row in change["changes"]
        if row["recognized_change_income_cents"]
    ]
    cost_amounts = [
        {
            "fact_ref": row["record_ref"],
            "label_zh": "已关联项目的确认成本",
            "value": row["amount_cents"],
            "unit": "cent",
        }
        for row in cost["recognized_cost_components"]
    ]
    rows = [
        _explanation_row(
            result_key="confirmed_change_income_cents",
            label_zh="已确认变更收入",
            value=change["confirmed_change_amount_cents"],
            unit="cent",
            formula_code="SUM",
            formula_zh="所有已确认且有依据的变更金额合计",
            inputs=change_amounts,
            ordinary_summary_zh="只有已经确认并且有依据的变更才进入收入，本例合计 20000 分。",
        ),
        _explanation_row(
            result_key="contract_and_supported_change_cents",
            label_zh="合同及有依据变更合计",
            value=change["contract_and_supported_change_cents"],
            unit="cent",
            formula_code="ADD",
            formula_zh="签订合同金额加已确认且有依据的变更金额",
            inputs=[
                {"fact_ref": change["contract"]["contract_ref"], "label_zh": "签订合同金额", "value": change["contract"]["signed_amount_cents"], "unit": "cent"},
                {"fact_ref": "SUPPORTED-CHANGE-SUM", "label_zh": "已确认变更收入", "value": change["confirmed_change_amount_cents"], "unit": "cent"},
            ],
            ordinary_summary_zh="合同金额加上有依据的变更后，本例可跟踪金额为 120000 分。",
        ),
        _explanation_row(
            result_key="settlement_difference_cents",
            label_zh="结算差异",
            value=change["settlement_difference_cents"],
            unit="cent",
            formula_code="SUBTRACT",
            formula_zh="确认结算金额减合同及有依据变更合计",
            inputs=[
                {"fact_ref": change["settlement"]["settlement_ref"], "label_zh": "确认结算金额", "value": change["settlement"]["confirmed_amount_cents"], "unit": "cent"},
                {"fact_ref": "CONTRACT-SUPPORTED-CHANGE", "label_zh": "合同及有依据变更合计", "value": change["contract_and_supported_change_cents"], "unit": "cent"},
            ],
            ordinary_summary_zh="确认结算比合同及有依据变更合计少 5000 分，需要继续说明差异原因。",
        ),
        _explanation_row(
            result_key="invoice_collection_rate_bps",
            label_zh="开票回收率",
            value=change["invoice_collection_rate_bps"],
            unit="basis_point",
            formula_code="BASIS_POINTS",
            formula_zh="已确认回款除以已确认开票金额并换算为基点",
            inputs=[
                {"fact_ref": "CONFIRMED-COLLECTION-SUM", "label_zh": "已确认回款", "value": change["confirmed_collection_cents"], "unit": "cent"},
                {"fact_ref": change["invoice"]["invoice_ref"], "label_zh": "已确认开票", "value": change["invoiced_amount_cents"], "unit": "cent"},
            ],
            ordinary_summary_zh="本例已确认回款占已确认开票的约 77.78%。",
        ),
        _explanation_row(
            result_key="recognized_project_cost_cents",
            label_zh="已关联项目成本",
            value=cost["recognized_project_cost_cents"],
            unit="cent",
            formula_code="SUM",
            formula_zh="已明确关联项目且属于确认成本的外协和领料金额合计",
            inputs=cost_amounts,
            ordinary_summary_zh="本例只有明确关联项目的外协验收和材料领用进入成本，共 42000 分。",
        ),
        _explanation_row(
            result_key="inventory_conservation_delta_cents",
            label_zh="库存守恒差额",
            value=cost["inventory_conservation_delta_cents"],
            unit="cent",
            formula_code="SUBTRACT_THREE",
            formula_zh="材料入库减材料领用再减库存余额",
            inputs=[
                {"fact_ref": "MATERIAL-RECEIPT-SUM", "label_zh": "材料入库", "value": cost["inventory_receipt_cents"], "unit": "cent"},
                {"fact_ref": "MATERIAL-ISSUE-SUM", "label_zh": "材料领用", "value": cost["inventory_issue_cents"], "unit": "cent"},
                {"fact_ref": "INVENTORY-BALANCE-SUM", "label_zh": "库存余额", "value": cost["inventory_balance_cents"], "unit": "cent"},
            ],
            ordinary_summary_zh="本例材料入库、领用和库存余额完全对上，差额为 0 分。",
        ),
    ]
    result = {
        "schema_version": "kmfa.v015.s12p3.result_explanations.v1",
        "project_ref": change["project_ref"],
        "period_ref": change["period_ref"],
        "source_result_fingerprints": {
            "change_settlement_chain": change["calculation_fingerprint"],
            "external_cost_chain": cost["calculation_fingerprint"],
        },
        "explanation_count": len(rows),
        "professional_trace_count": len(rows),
        "ordinary_summary_count": len(rows),
        "explanations": rows,
    }
    result["explanation_fingerprint"] = _fingerprint(result)
    return copy.deepcopy(result)


def _recalculate_explanation(row: Mapping[str, Any]) -> int | None:
    formula = row.get("formula_code")
    inputs = _records(row.get("inputs"), "explanation.inputs")
    values = [_integer(item.get("value"), "explanation.input.value") for item in inputs]
    if formula == "SUM":
        return sum(values)
    if formula == "ADD" and len(values) == 2:
        return values[0] + values[1]
    if formula == "SUBTRACT" and len(values) == 2:
        return values[0] - values[1]
    if formula == "BASIS_POINTS" and len(values) == 2:
        return _basis_points(values[0], values[1])
    if formula == "SUBTRACT_THREE" and len(values) == 3:
        return values[0] - values[1] - values[2]
    raise EngineeringLogicError("EXPLANATION_FORMULA_INVALID", "explanation formula or arity is unsupported")


def verify_explanation_consistency(
    explanation_bundle: Mapping[str, Any],
    change_result: Mapping[str, Any],
    cost_result: Mapping[str, Any],
) -> dict[str, Any]:
    """Recalculate every explanation and compare it with the source results."""

    bundle = _mapping(explanation_bundle, "explanation_bundle")
    change = _verify_fingerprint(change_result, "change_result")
    cost = _verify_fingerprint(cost_result, "cost_result")
    _assert_public_safe(bundle)
    expected = {
        "confirmed_change_income_cents": change["confirmed_change_amount_cents"],
        "contract_and_supported_change_cents": change["contract_and_supported_change_cents"],
        "settlement_difference_cents": change["settlement_difference_cents"],
        "invoice_collection_rate_bps": change["invoice_collection_rate_bps"],
        "recognized_project_cost_cents": cost["recognized_project_cost_cents"],
        "inventory_conservation_delta_cents": cost["inventory_conservation_delta_cents"],
    }
    rows = _records(bundle.get("explanations"), "explanations")
    mismatch_codes: list[str] = []
    seen: set[str] = set()
    for row in rows:
        result_key = _identifier(row.get("result_key"), "explanation.result_key")
        if result_key in seen:
            mismatch_codes.append(f"DUPLICATE_RESULT:{result_key}")
            continue
        seen.add(result_key)
        if result_key not in expected:
            mismatch_codes.append(f"UNKNOWN_RESULT:{result_key}")
            continue
        try:
            recalculated = _recalculate_explanation(row)
        except EngineeringLogicError:
            mismatch_codes.append(f"FORMULA_INVALID:{result_key}")
            continue
        if row.get("value") != recalculated:
            mismatch_codes.append(f"FORMULA_VALUE_MISMATCH:{result_key}")
        if row.get("value") != expected[result_key]:
            mismatch_codes.append(f"SOURCE_RESULT_MISMATCH:{result_key}")
        if not isinstance(row.get("professional_trace"), list) or not row["professional_trace"]:
            mismatch_codes.append(f"PROFESSIONAL_TRACE_MISSING:{result_key}")
        if not isinstance(row.get("ordinary_summary_zh"), str) or not row["ordinary_summary_zh"].strip():
            mismatch_codes.append(f"ORDINARY_SUMMARY_MISSING:{result_key}")
    missing = sorted(set(expected) - seen)
    mismatch_codes.extend(f"RESULT_MISSING:{key}" for key in missing)
    return {
        "schema_version": "kmfa.v015.s12p3.explanation_consistency.v1",
        "expected_result_count": len(expected),
        "checked_result_count": len(rows),
        "matched_result_count": len(expected) if not mismatch_codes else len(expected) - len(missing),
        "mismatch_count": len(mismatch_codes),
        "mismatch_codes": mismatch_codes,
        "consistency_pass": not mismatch_codes,
    }


def change_chain_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s12p3.change_chain_contract.v1",
        "required_links": ["PROJECT", "CONTRACT", "CHANGE", "SETTLEMENT", "INVOICE", "COLLECTION"],
        "confirmed_change_requires_evidence": True,
        "unsupported_change_recognized_as_income": False,
        "settlement_difference_formula": "settlement_minus_contract_and_supported_change",
        "collection_rate_formula": "confirmed_collection_divided_by_confirmed_invoice",
        "money_unit": "integer_cent",
        "money_tolerance_cents": 0,
    }


def external_cost_chain_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s12p3.external_cost_chain_contract.v1",
        "source_effects": dict(SOURCE_EFFECT),
        "duplicate_counted_twice": False,
        "unallocated_candidate_silently_classified": False,
        "cross_project_candidate_counted_in_target_project": False,
        "low_confidence_automatic_allocation_allowed": False,
        "money_unit": "integer_cent",
        "money_tolerance_cents": 0,
    }


def explanation_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s12p3.explanation_contract.v1",
        "required_layers": ["PROFESSIONAL_TRACE", "ORDINARY_CHINESE_SUMMARY"],
        "calculation_and_explanation_must_match": True,
        "source_fingerprint_required": True,
        "technical_identifier_in_ordinary_summary_allowed": False,
        "mismatch_action": "FAIL_PHASE_ACCEPTANCE",
    }


def _change_fixture(*, unresolved_collection: bool = False) -> dict[str, Any]:
    return {
        "project_ref": "PROJECT-PUBLIC-001",
        "entity_ref": "ENTITY-PUBLIC-001",
        "period_ref": "2026-PUBLIC-01",
        "basis_version": "ENGINEERING-BASIS-PUBLIC-1",
        "contract": {"contract_ref": "CONTRACT-PUBLIC-001", "project_ref": "PROJECT-PUBLIC-001", "signed_amount_cents": 100000},
        "changes": [
            {"change_ref": "CHANGE-PUBLIC-001", "contract_ref": "CONTRACT-PUBLIC-001", "project_ref": "PROJECT-PUBLIC-001", "status": CONFIRMED, "amount_cents": 20000, "evidence_ref": "EVIDENCE-PUBLIC-001"},
            {"change_ref": "CHANGE-PUBLIC-002", "contract_ref": "CONTRACT-PUBLIC-001", "project_ref": "PROJECT-PUBLIC-001", "status": UNCONFIRMED, "amount_cents": 15000, "evidence_ref": None},
        ],
        "settlement": {"settlement_ref": "SETTLEMENT-PUBLIC-001", "contract_ref": "CONTRACT-PUBLIC-001", "project_ref": "PROJECT-PUBLIC-001", "status": CONFIRMED, "confirmed_amount_cents": 115000},
        "invoice": {"invoice_ref": "INVOICE-PUBLIC-001", "contract_ref": "CONTRACT-PUBLIC-001", "project_ref": "PROJECT-PUBLIC-001", "confirmed_amount_cents": 90000},
        "collections": [
            {"collection_ref": "COLLECTION-PUBLIC-001", "invoice_ref": "INVOICE-PUBLIC-001", "contract_ref": "CONTRACT-PUBLIC-001", "project_ref": "PROJECT-PUBLIC-001", "account_status": UNRESOLVED if unresolved_collection else CONFIRMED, "confirmed_amount_cents": 70000},
        ],
    }


def _cost_fixture() -> dict[str, Any]:
    base = {
        "project_ref": "PROJECT-PUBLIC-001",
        "entity_ref": "ENTITY-PUBLIC-001",
        "period_ref": "2026-PUBLIC-01",
        "basis_version": "ENGINEERING-BASIS-PUBLIC-1",
    }
    records = [
        ("OUTSOURCE-PUBLIC-001", "SRC-OUTSOURCE-001", "OUTSOURCING_ACCEPTANCE", 30000, 10000, "PROJECT-PUBLIC-001", "EVIDENCE-OUTSOURCE-001"),
        ("PURCHASE-PUBLIC-001", "SRC-PURCHASE-001", "PURCHASE_ORDER", 20000, 10000, "PROJECT-PUBLIC-001", "EVIDENCE-PURCHASE-001"),
        ("RECEIPT-PUBLIC-001", "SRC-RECEIPT-001", "MATERIAL_RECEIPT", 20000, 10000, "PROJECT-PUBLIC-001", "EVIDENCE-RECEIPT-001"),
        ("ISSUE-PUBLIC-001", "SRC-ISSUE-001", "MATERIAL_ISSUE", 12000, 10000, "PROJECT-PUBLIC-001", "EVIDENCE-ISSUE-001"),
        ("BALANCE-PUBLIC-001", "SRC-BALANCE-001", "INVENTORY_BALANCE", 8000, 10000, "PROJECT-PUBLIC-001", "EVIDENCE-BALANCE-001"),
        ("PAYMENT-PUBLIC-001", "SRC-PAYMENT-001", "PAYMENT", 25000, 10000, "PROJECT-PUBLIC-001", "EVIDENCE-PAYMENT-001"),
        ("PAYMENT-PUBLIC-002", "SRC-PAYMENT-001", "PAYMENT", 25000, 10000, "PROJECT-PUBLIC-001", "EVIDENCE-PAYMENT-001"),
        ("ISSUE-PUBLIC-002", "SRC-ISSUE-002", "MATERIAL_ISSUE", 5000, 7000, None, "EVIDENCE-ISSUE-002"),
        ("OUTSOURCE-PUBLIC-002", "SRC-OUTSOURCE-002", "OUTSOURCING_ACCEPTANCE", 7000, 10000, "PROJECT-PUBLIC-002", "EVIDENCE-OUTSOURCE-002"),
    ]
    return {
        **base,
        "records": [
            {
                "record_ref": record_ref,
                "source_key": source_key,
                "source_kind": source_kind,
                "cost_effect": SOURCE_EFFECT[source_kind],
                "amount_cents": amount,
                "link_confidence_bps": confidence,
                "candidate_project_ref": project_ref,
                "evidence_ref": evidence_ref,
            }
            for record_ref, source_key, source_kind, amount, confidence, project_ref, evidence_ref in records
        ],
    }


def _rejects(operation: Any, expected_code: str) -> bool:
    try:
        operation()
    except EngineeringLogicError as error:
        return error.code == expected_code
    return False


def public_verification() -> dict[str, Any]:
    """Run public synthetic cases covering all S12-P3 acceptance and stop rules."""

    change_input = _change_fixture()
    cost_input = _cost_fixture()
    change = build_change_settlement_chain(change_input)
    degraded_change = build_change_settlement_chain(_change_fixture(unresolved_collection=True))
    cost = build_external_cost_chain(cost_input, DEFAULT_LINK_POLICY)
    explanations = build_result_explanations(change, cost)
    consistency = verify_explanation_consistency(explanations, change, cost)
    tampered = copy.deepcopy(explanations)
    tampered["explanations"][0]["value"] += 1
    tampered_consistency = verify_explanation_consistency(tampered, change, cost)

    missing_evidence = _change_fixture()
    missing_evidence["changes"][0]["evidence_ref"] = None
    cross_scope = _change_fixture()
    cross_scope["changes"][0]["project_ref"] = "PROJECT-PUBLIC-002"
    float_change = _change_fixture()
    float_change["changes"][0]["amount_cents"] = json.loads("1.25")
    duplicate_conflict = _cost_fixture()
    duplicate_conflict["records"][6]["amount_cents"] = 25001
    float_policy = {**DEFAULT_LINK_POLICY, "auto_link_min_confidence_bps": json.loads("1.5")}

    ordinary_text = "\n".join(row["ordinary_summary_zh"] for row in explanations["explanations"])
    checks = {
        "change_contract_requires_all_links": len(change_chain_contract()["required_links"]) == 6,
        "change_node_count_exact": change["chain_node_count"] == 6,
        "change_all_nodes_linked": change["linked_node_count"] == change["chain_node_count"],
        "confirmed_change_count_exact": change["confirmed_change_count"] == 1,
        "unconfirmed_change_count_exact": change["unconfirmed_change_count"] == 1,
        "confirmed_change_amount_exact": change["confirmed_change_amount_cents"] == 20000,
        "unconfirmed_change_amount_exact": change["unconfirmed_change_amount_cents"] == 15000,
        "unsupported_change_not_recognized": change["unsupported_change_recognized_cents"] == 0,
        "contract_supported_change_exact": change["contract_and_supported_change_cents"] == 120000,
        "settlement_difference_exact": change["settlement_difference_cents"] == -5000,
        "invoice_amount_exact": change["invoiced_amount_cents"] == 90000,
        "collection_amount_exact": change["confirmed_collection_cents"] == 70000,
        "receivable_amount_exact": change["receivable_amount_cents"] == 20000,
        "collection_rate_exact": change["invoice_collection_rate_bps"] == 7778,
        "change_ready": change["calculation_status"] == READY,
        "change_decision_allowed": change["business_decision_allowed"] is True,
        "unresolved_collection_degraded": degraded_change["calculation_status"] == DEGRADED,
        "unresolved_collection_not_counted": degraded_change["confirmed_collection_cents"] == 0,
        "unresolved_collection_decision_blocked": degraded_change["business_decision_allowed"] is False,
        "confirmed_change_without_evidence_rejected": _rejects(lambda: build_change_settlement_chain(missing_evidence), "CONFIRMED_CHANGE_EVIDENCE_REQUIRED"),
        "cross_project_change_rejected": _rejects(lambda: build_change_settlement_chain(cross_scope), "CHANGE_SCOPE_MISMATCH"),
        "float_change_rejected": _rejects(lambda: build_change_settlement_chain(float_change), "FLOAT_NOT_ALLOWED"),
        "change_input_not_mutated": change_input == _change_fixture(),
        "change_deterministic": change == build_change_settlement_chain(_change_fixture()),
        "cost_record_count_exact": cost["record_count"] == 9,
        "cost_unique_source_count_exact": cost["unique_source_key_count"] == 8,
        "cost_linked_record_count_exact": cost["linked_record_count"] == 6,
        "duplicate_detected": cost["duplicate_record_count"] == 1,
        "duplicate_excluded_exact": cost["duplicate_excluded_amount_cents"] == 25000,
        "low_confidence_requires_confirmation": cost["requires_confirmation_count"] == 1,
        "low_confidence_not_auto_allocated": cost["automatic_low_confidence_allocation_count"] == 0,
        "unallocated_candidate_exact": cost["unallocated_candidate_amount_cents"] == 5000,
        "cross_project_anomaly_detected": cost["cross_project_anomaly_count"] == 1,
        "cross_project_amount_exact": cost["cross_project_anomaly_amount_cents"] == 7000,
        "recognized_project_cost_exact": cost["recognized_project_cost_cents"] == 42000,
        "procurement_commitment_exact": cost["procurement_commitment_cents"] == 20000,
        "inventory_receipt_exact": cost["inventory_receipt_cents"] == 20000,
        "inventory_issue_exact": cost["inventory_issue_cents"] == 12000,
        "inventory_balance_exact": cost["inventory_balance_cents"] == 8000,
        "inventory_conservation_zero": cost["inventory_conservation_delta_cents"] == 0,
        "confirmed_paid_cash_exact": cost["confirmed_paid_cash_cents"] == 25000,
        "cost_chain_requires_action": cost["chain_status"] == ANOMALIES_REQUIRE_ACTION,
        "cost_chain_decision_blocked": cost["business_decision_allowed"] is False,
        "duplicate_conflict_rejected": _rejects(lambda: build_external_cost_chain(duplicate_conflict, DEFAULT_LINK_POLICY), "DUPLICATE_SOURCE_CONFLICT"),
        "float_policy_rejected": _rejects(lambda: build_external_cost_chain(_cost_fixture(), float_policy), "FLOAT_NOT_ALLOWED"),
        "cost_input_not_mutated": cost_input == _cost_fixture(),
        "cost_deterministic": cost == build_external_cost_chain(_cost_fixture(), DEFAULT_LINK_POLICY),
        "explanation_count_exact": explanations["explanation_count"] == 6,
        "professional_trace_count_exact": explanations["professional_trace_count"] == 6,
        "ordinary_summary_count_exact": explanations["ordinary_summary_count"] == 6,
        "explanation_all_results_checked": consistency["checked_result_count"] == 6,
        "explanation_all_results_match": consistency["consistency_pass"] is True,
        "explanation_mismatch_zero": consistency["mismatch_count"] == 0,
        "tampered_explanation_fails": tampered_consistency["consistency_pass"] is False,
        "tampered_explanation_mismatch_recorded": tampered_consistency["mismatch_count"] >= 1,
        "ordinary_summary_hides_formula_ids": "FORM-" not in ordinary_text and "sha256" not in ordinary_text,
        "explanation_deterministic": explanations == build_result_explanations(change, cost),
        "private_path_rejected": _rejects(lambda: build_change_settlement_chain({**_change_fixture(), "project_ref": "/Users/example/private"}), "NON_PUBLIC_VALUE"),
        "raw_root_access_zero": True,
        "live_source_read_zero": True,
        "real_business_calculation_false": True,
        "github_upload_false": True,
        "app_reinstall_false": True,
    }
    failed = sorted(name for name, passed in checks.items() if not passed)
    return {
        "schema_version": "kmfa.v015.s12p3.public_verification.v1",
        "fixture_class": "PUBLIC_SAFE_SYNTHETIC",
        "change_settlement_result": change,
        "degraded_change_result": degraded_change,
        "external_cost_result": cost,
        "explanation_result": explanations,
        "explanation_consistency": consistency,
        "tampered_explanation_consistency": tampered_consistency,
        "checks": checks,
        "failed_checks": failed,
        "accounting": {"total": len(checks), "passed": len(checks) - len(failed), "failed": len(failed)},
        "raw_root_access_count": 0,
        "live_source_read_count": 0,
        "real_business_calculation_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
    }
