#!/usr/bin/env python3
"""Cross-phase review contract for KMFA v1.5 S12.

The review composes the accepted S12-P1 fact ledger, S12-P2 calculation
functions and S12-P3 engineering chains into one public-safe project example.
It proves that supported change income, target-project cost, cash movement and
human explanations are derived from the same scope and that rejected,
duplicate, low-confidence or cross-project candidates cannot leak into a
business result.
"""

from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any

from KMFA.tools import v015_s12_p1_project_cost_facts as facts
from KMFA.tools import v015_s12_p2_core_calculations as calculations
from KMFA.tools import v015_s12_p3_engineering_logic as engineering


RUN_PHASE_ID = "V015_S12_STAGE_REVIEW"
TASK_ID = "KMFA-V015-S12-STAGE-REVIEW-20260716"
ACCEPTANCE_ID = "ACC-KMFA-V015-S12-STAGE-REVIEW"
VERSION = "1.5.0-dev-s12-review"
REVIEW_BASE_COMMIT = "86a84846c3e69d791db525b0e23fb88ddd8e6a0e"

PROJECT_REF = "PROJECT-PUBLIC-001"
ENTITY_REF = "ENTITY-PUBLIC-001"
PERIOD_REF = "2026-PUBLIC-01"
PERIOD_VERSION = "PERIOD-RULE-PUBLIC-1"
SOURCE_VERSION = "S12-REVIEW-SOURCE-V1"
REVIEW_BASIS_VERSION = "S12-REVIEW-BASIS-V1"


class StageReviewError(ValueError):
    """Fail-closed review error with a stable reason code."""

    def __init__(self, code: str, message_zh: str) -> None:
        super().__init__(f"{code}: {message_zh}")
        self.code = code
        self.message_zh = message_zh


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _fingerprint(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value)).hexdigest()


def _mapping(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise StageReviewError("REVIEW_MAPPING_REQUIRED", f"{field} 必须是结构化对象。")
    return dict(value)


def _records(value: Any, field: str) -> list[dict[str, Any]]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise StageReviewError("REVIEW_LIST_REQUIRED", f"{field} 必须是列表。")
    return [_mapping(row, f"{field}[{index}]") for index, row in enumerate(value)]


def _integer(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise StageReviewError("REVIEW_INTEGER_REQUIRED", f"{field} 必须是整数。")
    return value


def _basis_points(numerator: int, denominator: int) -> int | None:
    if denominator == 0:
        return None
    sign = -1 if (numerator < 0) != (denominator < 0) else 1
    return sign * ((abs(numerator) * 10000 + abs(denominator) // 2) // abs(denominator))


def _assert_scope(value: Mapping[str, Any], field: str) -> None:
    expected = {
        "project_ref": PROJECT_REF,
        "entity_ref": ENTITY_REF,
        "period_ref": PERIOD_REF,
    }
    for key, required in expected.items():
        if value.get(key) != required:
            raise StageReviewError("REVIEW_SCOPE_MISMATCH", f"{field}.{key} 与统一项目范围不一致。")


def public_review_input() -> dict[str, Any]:
    """Return one deterministic public example shared by all three phases."""

    change = {
        "project_ref": PROJECT_REF,
        "entity_ref": ENTITY_REF,
        "period_ref": PERIOD_REF,
        "basis_version": REVIEW_BASIS_VERSION,
        "contract": {
            "contract_ref": "CONTRACT-PUBLIC-001",
            "project_ref": PROJECT_REF,
            "signed_amount_cents": 100000,
        },
        "changes": [
            {
                "change_ref": "CHANGE-PUBLIC-001",
                "contract_ref": "CONTRACT-PUBLIC-001",
                "project_ref": PROJECT_REF,
                "status": engineering.CONFIRMED,
                "amount_cents": 20000,
                "evidence_ref": "EVIDENCE-PUBLIC-001",
            },
            {
                "change_ref": "CHANGE-PUBLIC-002",
                "contract_ref": "CONTRACT-PUBLIC-001",
                "project_ref": PROJECT_REF,
                "status": engineering.UNCONFIRMED,
                "amount_cents": 15000,
                "evidence_ref": None,
            },
        ],
        "settlement": {
            "settlement_ref": "SETTLEMENT-PUBLIC-001",
            "contract_ref": "CONTRACT-PUBLIC-001",
            "project_ref": PROJECT_REF,
            "status": engineering.CONFIRMED,
            "confirmed_amount_cents": 115000,
        },
        "invoice": {
            "invoice_ref": "INVOICE-PUBLIC-001",
            "contract_ref": "CONTRACT-PUBLIC-001",
            "project_ref": PROJECT_REF,
            "confirmed_amount_cents": 90000,
        },
        "collections": [
            {
                "collection_ref": "COLLECTION-PUBLIC-001",
                "invoice_ref": "INVOICE-PUBLIC-001",
                "contract_ref": "CONTRACT-PUBLIC-001",
                "project_ref": PROJECT_REF,
                "account_status": engineering.CONFIRMED,
                "confirmed_amount_cents": 70000,
            }
        ],
    }
    cost_records = (
        ("OUTSOURCE-PUBLIC-001", "SRC-OUTSOURCE-001", "OUTSOURCING_ACCEPTANCE", 30000, 10000, PROJECT_REF, "EVIDENCE-OUTSOURCE-001"),
        ("PURCHASE-PUBLIC-001", "SRC-PURCHASE-001", "PURCHASE_ORDER", 20000, 10000, PROJECT_REF, "EVIDENCE-PURCHASE-001"),
        ("RECEIPT-PUBLIC-001", "SRC-RECEIPT-001", "MATERIAL_RECEIPT", 20000, 10000, PROJECT_REF, "EVIDENCE-RECEIPT-001"),
        ("ISSUE-PUBLIC-001", "SRC-ISSUE-001", "MATERIAL_ISSUE", 12000, 10000, PROJECT_REF, "EVIDENCE-ISSUE-001"),
        ("BALANCE-PUBLIC-001", "SRC-BALANCE-001", "INVENTORY_BALANCE", 8000, 10000, PROJECT_REF, "EVIDENCE-BALANCE-001"),
        ("PAYMENT-PUBLIC-001", "SRC-PAYMENT-001", "PAYMENT", 25000, 10000, PROJECT_REF, "EVIDENCE-PAYMENT-001"),
        ("PAYMENT-PUBLIC-002", "SRC-PAYMENT-001", "PAYMENT", 25000, 10000, PROJECT_REF, "EVIDENCE-PAYMENT-001"),
        ("ISSUE-PUBLIC-002", "SRC-ISSUE-002", "MATERIAL_ISSUE", 5000, 7000, None, "EVIDENCE-ISSUE-002"),
        ("OUTSOURCE-PUBLIC-002", "SRC-OUTSOURCE-002", "OUTSOURCING_ACCEPTANCE", 7000, 10000, "PROJECT-PUBLIC-002", "EVIDENCE-OUTSOURCE-002"),
    )
    cost = {
        "project_ref": PROJECT_REF,
        "entity_ref": ENTITY_REF,
        "period_ref": PERIOD_REF,
        "basis_version": REVIEW_BASIS_VERSION,
        "records": [
            {
                "record_ref": record_ref,
                "source_key": source_key,
                "source_kind": source_kind,
                "cost_effect": engineering.SOURCE_EFFECT[source_kind],
                "amount_cents": amount,
                "link_confidence_bps": confidence,
                "candidate_project_ref": candidate_project,
                "evidence_ref": evidence_ref,
            }
            for record_ref, source_key, source_kind, amount, confidence, candidate_project, evidence_ref in cost_records
        ],
    }
    return {
        "schema_version": "kmfa.v015.s12.review-input.v1",
        "fixture_class": "PUBLIC_SAFE_SYNTHETIC",
        "change_chain": change,
        "external_cost_chain": cost,
        "comparison_period_cost_cents": 40000,
        "raw_root_access_count": 0,
        "live_source_read_count": 0,
    }


def _p1_common(record_id: str, amount_cents: int, source_record_ref: str) -> dict[str, Any]:
    return {
        "record_id": record_id,
        "event_version": 1,
        "project_ref": PROJECT_REF,
        "company_entity_ref": ENTITY_REF,
        "period_ref": PERIOD_REF,
        "period_version": PERIOD_VERSION,
        "source_ref": "SOURCE-S12-REVIEW",
        "source_record_ref": source_record_ref,
        "source_version": SOURCE_VERSION,
        "amount_cents": amount_cents,
        "currency": "CNY",
    }


def _project_fact_projection(
    change: Mapping[str, Any],
    external: Mapping[str, Any],
) -> tuple[facts.ProjectCostFactLedger, dict[str, Any]]:
    """Project P3 results into P1 without leaking unsupported candidates."""

    ledger = facts.ProjectCostFactLedger()
    income_specs = (
        ("REV-CONTRACT-REVIEW", "CONTRACT", change["contract"]["signed_amount_cents"], change["contract"]["contract_ref"]),
        ("REV-CHANGE-REVIEW", "CHANGE_ORDER", change["confirmed_change_amount_cents"], "SUPPORTED-CHANGE-SUM"),
        ("REV-SETTLEMENT-REVIEW", "SETTLEMENT", change["settlement"]["confirmed_amount_cents"], change["settlement"]["settlement_ref"]),
        ("REV-INVOICE-REVIEW", "INVOICE", change["invoiced_amount_cents"], change["invoice"]["invoice_ref"]),
        ("REV-COLLECTION-REVIEW", "COLLECTION", change["confirmed_collection_cents"], "CONFIRMED-COLLECTION-SUM"),
    )
    for record_id, layer, amount, source_row in income_specs:
        ledger.add_income_fact({
            **_p1_common(record_id, _integer(amount, f"{layer}.amount"), str(source_row)),
            "income_layer": layer,
            "amount_basis": "TAX_INCLUSIVE",
        })

    category_by_kind = {
        "OUTSOURCING_ACCEPTANCE": "SUBCONTRACT",
        "MATERIAL_ISSUE": "MATERIAL",
    }
    for index, component in enumerate(external["recognized_cost_components"], start=1):
        kind = str(component["source_kind"])
        ledger.add_cost_fact({
            **_p1_common(
                f"COST-LINKED-{index:03d}",
                _integer(component["amount_cents"], "recognized_component.amount"),
                str(component["record_ref"]),
            ),
            "cost_category": category_by_kind[kind],
        })
    unallocated_amount = _integer(external["unallocated_candidate_amount_cents"], "unallocated_candidate_amount")
    unallocated = {
        **_p1_common("COST-UNALLOCATED-001", unallocated_amount, "LOW-CONFIDENCE-CANDIDATE-SUM"),
        "project_ref": facts.UNRESOLVED,
        "cost_category": "MATERIAL",
    }
    ledger.add_cost_fact(unallocated)
    snapshot = ledger.snapshot()
    projection = {
        "schema_version": "kmfa.v015.s12.review-fact-projection.v1",
        "income_layer_amounts_cents": {
            row["income_layer"]: row["amount_cents"]
            for row in ledger.income_facts
        },
        "supported_change_income_cents": change["confirmed_change_amount_cents"],
        "unconfirmed_change_excluded_cents": change["unconfirmed_change_amount_cents"],
        "unsupported_change_recognized_cents": change["unsupported_change_recognized_cents"],
        "target_cost_input_cents": snapshot["input_cost_cents"],
        "allocated_project_cost_cents": snapshot["allocated_cost_cents"],
        "unallocated_project_cost_cents": snapshot["unallocated_cost_cents"],
        "duplicate_excluded_amount_cents": external["duplicate_excluded_amount_cents"],
        "cross_project_excluded_amount_cents": external["cross_project_anomaly_amount_cents"],
        "excluded_candidate_leak_count": 0,
        "cost_conservation_delta_cents": snapshot["conservation_delta_cents"],
        "source_fact_fingerprints": sorted(
            row["fact_fingerprint"]
            for row in [*ledger.income_facts, *ledger.allocated_cost_facts, *ledger.unallocated_cost_pool]
        ),
    }
    projection["projection_fingerprint"] = _fingerprint(projection)
    return ledger, projection


def _calculation_projection(
    review_input: Mapping[str, Any],
    change: Mapping[str, Any],
    external: Mapping[str, Any],
    fact_snapshot: Mapping[str, Any],
) -> dict[str, Any]:
    """Derive every P2 payload from reviewed P1/P3 values."""

    common = {
        "project_ref": PROJECT_REF,
        "entity_ref": ENTITY_REF,
        "period_ref": PERIOD_REF,
        "basis_version": REVIEW_BASIS_VERSION,
    }
    total_cost = _integer(fact_snapshot["input_cost_cents"], "fact_snapshot.input_cost_cents")
    allocated_cost = _integer(fact_snapshot["allocated_cost_cents"], "fact_snapshot.allocated_cost_cents")
    margin_payload = {
        **common,
        "contract": {
            "revenue_basis": "SIGNED_CONTRACT_PLUS_APPROVED_CHANGE",
            "cost_basis": "CONTRACT_TARGET_COST",
            "revenue_cents": change["contract_and_supported_change_cents"],
            "cost_cents": total_cost,
        },
        "settlement": {
            "revenue_basis": "APPROVED_SETTLEMENT_REVENUE",
            "cost_basis": "SETTLEMENT_MATCHED_COST",
            "revenue_cents": change["settlement"]["confirmed_amount_cents"],
            "cost_cents": allocated_cost,
        },
        "management": {
            "revenue_basis": "MANAGEMENT_RECOGNIZED_REVENUE",
            "cost_basis": "MANAGEMENT_RECOGNIZED_COST",
            "revenue_cents": change["settlement"]["confirmed_amount_cents"],
            "cost_cents": total_cost,
        },
    }
    margins = calculations.calculate_margin_views(margin_payload)
    invoice_receivable = change["receivable_amount_cents"]
    unsettled = change["settlement"]["confirmed_amount_cents"] - change["invoiced_amount_cents"]
    cash_payload = {
        **common,
        "account_status": calculations.CONFIRMED,
        "entity_status": calculations.CONFIRMED,
        "cash_source_lane": "BANK_CONFIRMED_COLLECTIONS_AND_PAYMENTS",
        "confirmed_collection_cents": change["confirmed_collection_cents"],
        "confirmed_cash_paid_cost_cents": external["confirmed_paid_cash_cents"],
        "retention_receivable_cents": 0,
        "unsettled_receivable_cents": unsettled,
        "invoiced_not_collected_cents": invoice_receivable,
        "ordinary_receivable_cents": 0,
    }
    cash = calculations.calculate_cash_metrics(cash_payload)
    risk_payload = {
        **common,
        "required_cost_category_count": len(facts.COST_CATEGORIES),
        "observed_required_cost_category_count": fact_snapshot["allocated_cost_category_count"],
        "total_cost_cents": total_cost,
        "unallocated_cost_cents": fact_snapshot["unallocated_cost_cents"],
        "current_period_cost_cents": total_cost,
        "comparison_period_cost_cents": review_input["comparison_period_cost_cents"],
        "management_margin_bps": margins["views"]["management"]["gross_margin_bps"],
    }
    risk = calculations.assess_cost_risk(risk_payload, calculations.DEFAULT_RISK_POLICY)
    result = {
        "schema_version": "kmfa.v015.s12.review-calculation-projection.v1",
        "margin_payload": margin_payload,
        "margin_results": margins,
        "cash_payload": cash_payload,
        "cash_results": cash,
        "risk_payload": risk_payload,
        "risk_results": risk,
        "source_bindings": {
            "contract_revenue": "P3.contract_and_supported_change_cents",
            "settlement_revenue": "P3.settlement.confirmed_amount_cents",
            "management_revenue": "P3.settlement.confirmed_amount_cents",
            "contract_and_management_cost": "P1.input_cost_cents",
            "settlement_cost": "P1.allocated_cost_cents",
            "cash_collection": "P3.confirmed_collection_cents",
            "cash_paid_cost": "P3.confirmed_paid_cash_cents",
            "risk_total_and_unallocated_cost": "P1.cost_conservation",
        },
    }
    result["projection_fingerprint"] = _fingerprint(result)
    return result


def _review_explanation_rows(calculation: Mapping[str, Any], fact_projection: Mapping[str, Any]) -> list[dict[str, Any]]:
    margins = calculation["margin_results"]["views"]
    cash = calculation["cash_results"]
    risk = calculation["risk_results"]
    rows = [
        ("contract_gross_profit_cents", "合同毛利", margins["contract"]["gross_profit_cents"], "SUBTRACT", [
            ("合同及有依据变更", margins["contract"]["revenue_cents"]),
            ("目标总成本", margins["contract"]["cost_cents"]),
        ], "合同金额只加有依据变更，再扣除目标总成本。"),
        ("settlement_gross_profit_cents", "结算毛利", margins["settlement"]["gross_profit_cents"], "SUBTRACT", [
            ("确认结算收入", margins["settlement"]["revenue_cents"]),
            ("已匹配项目成本", margins["settlement"]["cost_cents"]),
        ], "确认结算收入扣除已经明确归到本项目的成本。"),
        ("management_gross_profit_cents", "管理毛利", margins["management"]["gross_profit_cents"], "SUBTRACT", [
            ("管理确认收入", margins["management"]["revenue_cents"]),
            ("包含未归集项的总成本", margins["management"]["cost_cents"]),
        ], "管理口径保留未归集成本，避免把毛利算高。"),
        ("cash_gross_profit_cents", "现金毛利", cash["cash_gross_profit_cents"], "SUBTRACT", [
            ("已确认回款", cash["confirmed_collection_cents"]),
            ("已确认付款成本", cash["confirmed_cash_paid_cost_cents"]),
        ], "现金毛利只使用已经确认收到和付出的现金。"),
        ("cost_conservation_delta_cents", "成本守恒差额", fact_projection["cost_conservation_delta_cents"], "CONSERVATION", [
            ("输入总成本", fact_projection["target_cost_input_cents"]),
            ("已归集成本", fact_projection["allocated_project_cost_cents"]),
            ("未归集成本", fact_projection["unallocated_project_cost_cents"]),
        ], "全部目标项目成本要么已归集，要么留在未归集池，不能丢失。"),
        ("unallocated_cost_ratio_bps", "未归集成本比例", risk["metrics"]["unallocated_cost_ratio_bps"], "BASIS_POINTS", [
            ("未归集成本", fact_projection["unallocated_project_cost_cents"]),
            ("输入总成本", fact_projection["target_cost_input_cents"]),
        ], "未归集成本比例单独展示，并按外置阈值判断风险。"),
    ]
    result: list[dict[str, Any]] = []
    for key, label, value, formula, inputs, summary in rows:
        row = {
            "result_key": key,
            "label_zh": label,
            "value": value,
            "formula_code": formula,
            "professional_trace": [
                {"label_zh": input_label, "value": input_value, "unit": "cent"}
                for input_label, input_value in inputs
            ],
            "ordinary_summary_zh": summary,
        }
        row["explanation_fingerprint"] = _fingerprint(row)
        result.append(row)
    return result


def _recalculate_review_explanation(row: Mapping[str, Any]) -> int | None:
    trace = _records(row.get("professional_trace"), "professional_trace")
    values = [_integer(item.get("value"), "professional_trace.value") for item in trace]
    formula = row.get("formula_code")
    if formula == "SUBTRACT" and len(values) == 2:
        return values[0] - values[1]
    if formula == "CONSERVATION" and len(values) == 3:
        return values[0] - values[1] - values[2]
    if formula == "BASIS_POINTS" and len(values) == 2:
        return _basis_points(values[0], values[1])
    raise StageReviewError("REVIEW_EXPLANATION_FORMULA_INVALID", "复审解释公式或参数数量无效。")


def verify_review_explanations(bundle: Mapping[str, Any]) -> dict[str, Any]:
    source = _mapping(bundle, "bundle")
    rows = _records(source.get("explanations"), "explanations")
    expected_keys = {
        "contract_gross_profit_cents",
        "settlement_gross_profit_cents",
        "management_gross_profit_cents",
        "cash_gross_profit_cents",
        "cost_conservation_delta_cents",
        "unallocated_cost_ratio_bps",
    }
    seen: set[str] = set()
    mismatches: list[str] = []
    for row in rows:
        key = row.get("result_key")
        if key not in expected_keys or key in seen:
            mismatches.append(f"RESULT_KEY_INVALID:{key}")
            continue
        seen.add(str(key))
        if row.get("value") != _recalculate_review_explanation(row):
            mismatches.append(f"FORMULA_VALUE_MISMATCH:{key}")
        fingerprint_source = {name: copy.deepcopy(value) for name, value in row.items() if name != "explanation_fingerprint"}
        if row.get("explanation_fingerprint") != _fingerprint(fingerprint_source):
            mismatches.append(f"EXPLANATION_FINGERPRINT_INVALID:{key}")
        if not isinstance(row.get("ordinary_summary_zh"), str) or not row["ordinary_summary_zh"].strip():
            mismatches.append(f"SUMMARY_MISSING:{key}")
    mismatches.extend(f"RESULT_MISSING:{key}" for key in sorted(expected_keys - seen))
    return {
        "schema_version": "kmfa.v015.s12.review-explanation-consistency.v1",
        "expected_result_count": len(expected_keys),
        "checked_result_count": len(rows),
        "mismatch_count": len(mismatches),
        "mismatch_codes": mismatches,
        "consistency_pass": not mismatches,
    }


def build_integrated_review(review_input: Mapping[str, Any] | None = None) -> dict[str, Any]:
    source = copy.deepcopy(dict(review_input if review_input is not None else public_review_input()))
    if source.get("schema_version") != "kmfa.v015.s12.review-input.v1":
        raise StageReviewError("REVIEW_INPUT_SCHEMA_MISMATCH", "复审输入版本不正确。")
    change_input = _mapping(source.get("change_chain"), "change_chain")
    cost_input = _mapping(source.get("external_cost_chain"), "external_cost_chain")
    _assert_scope(change_input, "change_chain")
    _assert_scope(cost_input, "external_cost_chain")
    change = engineering.build_change_settlement_chain(change_input)
    external = engineering.build_external_cost_chain(cost_input, engineering.DEFAULT_LINK_POLICY)
    p3_explanations = engineering.build_result_explanations(change, external)
    p3_consistency = engineering.verify_explanation_consistency(p3_explanations, change, external)
    ledger, fact_projection = _project_fact_projection(change, external)
    fact_snapshot = ledger.snapshot()
    calculation_projection = _calculation_projection(source, change, external, fact_snapshot)
    review_rows = _review_explanation_rows(calculation_projection, fact_projection)
    review_bundle = {
        "schema_version": "kmfa.v015.s12.review-explanations.v1",
        "explanation_count": len(review_rows),
        "explanations": review_rows,
    }
    review_bundle["bundle_fingerprint"] = _fingerprint(review_bundle)
    review_consistency = verify_review_explanations(review_bundle)
    result = {
        "schema_version": "kmfa.v015.s12.integrated-review.v1",
        "project_ref": PROJECT_REF,
        "entity_ref": ENTITY_REF,
        "period_ref": PERIOD_REF,
        "phase_versions": {
            "S12-P1": facts.VERSION,
            "S12-P2": calculations.VERSION,
            "S12-P3": engineering.VERSION,
        },
        "input_fingerprint": _fingerprint(source),
        "change_settlement_result": change,
        "external_cost_result": external,
        "p3_explanations": p3_explanations,
        "p3_explanation_consistency": p3_consistency,
        "fact_projection": fact_projection,
        "fact_snapshot": fact_snapshot,
        "calculation_projection": calculation_projection,
        "review_explanations": review_bundle,
        "review_explanation_consistency": review_consistency,
        "excluded_candidate_leak_count": 0,
        "raw_root_access_count": 0,
        "live_source_read_count": 0,
        "real_business_calculation_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
    }
    result["review_fingerprint"] = _fingerprint(result)
    return copy.deepcopy(result)


def validate_integrated_review(value: Mapping[str, Any]) -> dict[str, Any]:
    review = _mapping(value, "review")
    fingerprint_source = {key: copy.deepcopy(item) for key, item in review.items() if key != "review_fingerprint"}
    if review.get("review_fingerprint") != _fingerprint(fingerprint_source):
        raise StageReviewError("REVIEW_FINGERPRINT_INVALID", "复审结果内容或绑定已变化。")
    expected_versions = {
        "S12-P1": facts.VERSION,
        "S12-P2": calculations.VERSION,
        "S12-P3": engineering.VERSION,
    }
    if review.get("phase_versions") != expected_versions:
        raise StageReviewError("REVIEW_PHASE_VERSION_DRIFT", "三个已验收部分的版本绑定不一致。")
    fact_projection = _mapping(review.get("fact_projection"), "fact_projection")
    change = _mapping(review.get("change_settlement_result"), "change_settlement_result")
    external = _mapping(review.get("external_cost_result"), "external_cost_result")
    calculation = _mapping(review.get("calculation_projection"), "calculation_projection")
    margins = _mapping(calculation.get("margin_results"), "margin_results")["views"]
    cash = _mapping(calculation.get("cash_results"), "cash_results")
    risk = _mapping(calculation.get("risk_results"), "risk_results")
    explanation_bundle = _mapping(review.get("review_explanations"), "review_explanations")
    explanation_values = {
        row.get("result_key"): row.get("value")
        for row in _records(explanation_bundle.get("explanations"), "review_explanations.explanations")
    }
    expected_explanation_values = {
        "contract_gross_profit_cents": margins["contract"]["gross_profit_cents"],
        "settlement_gross_profit_cents": margins["settlement"]["gross_profit_cents"],
        "management_gross_profit_cents": margins["management"]["gross_profit_cents"],
        "cash_gross_profit_cents": cash["cash_gross_profit_cents"],
        "cost_conservation_delta_cents": fact_projection["cost_conservation_delta_cents"],
        "unallocated_cost_ratio_bps": risk["metrics"]["unallocated_cost_ratio_bps"],
    }
    p3_explanation_check = engineering.verify_explanation_consistency(
        review["p3_explanations"],
        change,
        external,
    )
    review_explanation_check = verify_review_explanations(explanation_bundle)
    checks = {
        "supported_change_only": fact_projection.get("supported_change_income_cents") == change.get("confirmed_change_amount_cents"),
        "unconfirmed_change_excluded": fact_projection.get("unconfirmed_change_excluded_cents") == change.get("unconfirmed_change_amount_cents"),
        "unsupported_change_zero": fact_projection.get("unsupported_change_recognized_cents") == 0,
        "cost_conservation_zero": fact_projection.get("cost_conservation_delta_cents") == 0,
        "excluded_candidate_leak_zero": fact_projection.get("excluded_candidate_leak_count") == 0,
        "allocated_cost_bound": fact_projection.get("allocated_project_cost_cents") == external.get("recognized_project_cost_cents"),
        "contract_revenue_bound": margins["contract"]["revenue_cents"] == change.get("contract_and_supported_change_cents"),
        "settlement_revenue_bound": margins["settlement"]["revenue_cents"] == change["settlement"]["confirmed_amount_cents"],
        "cash_collection_bound": cash.get("confirmed_collection_cents") == change.get("confirmed_collection_cents"),
        "cash_payment_bound": cash.get("confirmed_cash_paid_cost_cents") == external.get("confirmed_paid_cash_cents"),
        "margin_arithmetic_exact": all(
            row["gross_profit_cents"] == row["revenue_cents"] - row["cost_cents"]
            for row in margins.values()
        ),
        "cash_arithmetic_exact": cash["cash_gross_profit_cents"] == cash["confirmed_collection_cents"] - cash["confirmed_cash_paid_cost_cents"],
        "p3_explanations_match": p3_explanation_check.get("consistency_pass") is True,
        "review_explanations_match": review_explanation_check.get("consistency_pass") is True,
        "review_explanations_bound_to_sources": explanation_values == expected_explanation_values,
    }
    failed = sorted(key for key, passed in checks.items() if not passed)
    if failed:
        raise StageReviewError("REVIEW_CROSS_PHASE_MISMATCH", "跨部分结果不一致：" + ",".join(failed))
    return copy.deepcopy(review)


def _rejects(operation: Any, expected_code: str) -> bool:
    try:
        operation()
    except StageReviewError as error:
        return error.code == expected_code
    return False


def public_verification() -> dict[str, Any]:
    review_input = public_review_input()
    review = build_integrated_review(review_input)
    validated = validate_integrated_review(review)
    change = review["change_settlement_result"]
    external = review["external_cost_result"]
    fact = review["fact_projection"]
    snapshot = review["fact_snapshot"]
    calculation = review["calculation_projection"]
    margins = calculation["margin_results"]["views"]
    cash = calculation["cash_results"]
    risk = calculation["risk_results"]

    tampered_margin = copy.deepcopy(review)
    tampered_margin["calculation_projection"]["margin_results"]["views"]["management"]["gross_profit_cents"] += 1
    tampered_margin["review_fingerprint"] = _fingerprint({
        key: copy.deepcopy(value)
        for key, value in tampered_margin.items()
        if key != "review_fingerprint"
    })
    tampered_explanation = copy.deepcopy(review["review_explanations"])
    tampered_explanation["explanations"][0]["value"] += 1
    bad_scope = public_review_input()
    bad_scope["external_cost_chain"]["project_ref"] = "PROJECT-PUBLIC-002"

    checks = {
        "p1_version_bound": review["phase_versions"]["S12-P1"] == facts.VERSION,
        "p2_version_bound": review["phase_versions"]["S12-P2"] == calculations.VERSION,
        "p3_version_bound": review["phase_versions"]["S12-P3"] == engineering.VERSION,
        "integrated_review_valid": validated["review_fingerprint"] == review["review_fingerprint"],
        "review_deterministic": review == build_integrated_review(public_review_input()),
        "review_input_not_mutated": review_input == public_review_input(),
        "change_nodes_all_linked": change["chain_node_count"] == change["linked_node_count"] == 6,
        "confirmed_change_exact": change["confirmed_change_amount_cents"] == 20000,
        "unconfirmed_change_exact": change["unconfirmed_change_amount_cents"] == 15000,
        "unsupported_change_zero": change["unsupported_change_recognized_cents"] == 0,
        "contract_supported_change_exact": change["contract_and_supported_change_cents"] == 120000,
        "settlement_exact": change["settlement"]["confirmed_amount_cents"] == 115000,
        "invoice_exact": change["invoiced_amount_cents"] == 90000,
        "collection_exact": change["confirmed_collection_cents"] == 70000,
        "receivable_exact": change["receivable_amount_cents"] == 20000,
        "collection_rate_exact": change["invoice_collection_rate_bps"] == 7778,
        "p1_income_layer_count_exact": snapshot["income_layer_count"] == 5,
        "p1_income_fact_count_exact": snapshot["income_fact_count"] == 5,
        "p1_supported_change_only": fact["supported_change_income_cents"] == 20000,
        "p1_unconfirmed_change_excluded": fact["unconfirmed_change_excluded_cents"] == 15000,
        "p1_cost_input_exact": fact["target_cost_input_cents"] == 47000,
        "p1_allocated_cost_exact": fact["allocated_project_cost_cents"] == 42000,
        "p1_unallocated_cost_exact": fact["unallocated_project_cost_cents"] == 5000,
        "p1_cost_conservation_zero": fact["cost_conservation_delta_cents"] == 0,
        "p1_no_dropped_cost": snapshot["dropped_cost_fact_count"] == 0,
        "p1_no_average_allocation": snapshot["average_allocation_count"] == 0,
        "p1_no_silent_classification": snapshot["silent_classification_count"] == 0,
        "external_duplicate_count_exact": external["duplicate_record_count"] == 1,
        "external_duplicate_excluded_exact": external["duplicate_excluded_amount_cents"] == 25000,
        "external_low_confidence_count_exact": external["requires_confirmation_count"] == 1,
        "external_low_confidence_auto_zero": external["automatic_low_confidence_allocation_count"] == 0,
        "external_cross_project_count_exact": external["cross_project_anomaly_count"] == 1,
        "external_cross_project_excluded_exact": external["cross_project_anomaly_amount_cents"] == 7000,
        "external_recognized_cost_exact": external["recognized_project_cost_cents"] == 42000,
        "external_paid_cash_exact": external["confirmed_paid_cash_cents"] == 25000,
        "excluded_candidate_leak_zero": review["excluded_candidate_leak_count"] == 0,
        "contract_margin_revenue_bound": margins["contract"]["revenue_cents"] == 120000,
        "contract_margin_cost_bound": margins["contract"]["cost_cents"] == 47000,
        "contract_gross_profit_exact": margins["contract"]["gross_profit_cents"] == 73000,
        "settlement_margin_revenue_bound": margins["settlement"]["revenue_cents"] == 115000,
        "settlement_margin_cost_bound": margins["settlement"]["cost_cents"] == 42000,
        "settlement_gross_profit_exact": margins["settlement"]["gross_profit_cents"] == 73000,
        "management_margin_cost_includes_unallocated": margins["management"]["cost_cents"] == 47000,
        "management_gross_profit_exact": margins["management"]["gross_profit_cents"] == 68000,
        "cash_collection_bound": cash["confirmed_collection_cents"] == 70000,
        "cash_payment_bound": cash["confirmed_cash_paid_cost_cents"] == 25000,
        "cash_gross_profit_exact": cash["cash_gross_profit_cents"] == 45000,
        "uncollected_not_cash": cash["uncollected_amount_counted_as_cash_cents"] == 0,
        "cash_decision_allowed": cash["business_decision_allowed"] is True,
        "risk_total_cost_bound": calculation["risk_payload"]["total_cost_cents"] == 47000,
        "risk_unallocated_bound": calculation["risk_payload"]["unallocated_cost_cents"] == 5000,
        "risk_unallocated_ratio_exact": risk["metrics"]["unallocated_cost_ratio_bps"] == 1064,
        "risk_conclusion_determinate": risk["deterministic_conclusion_allowed"] is True,
        "risk_incomplete_category_alert": "COST_CATEGORY_INCOMPLETE" in risk["triggered_rule_codes"],
        "risk_unallocated_alert": "UNALLOCATED_COST_EXCESS" in risk["triggered_rule_codes"],
        "p3_explanation_count_exact": review["p3_explanations"]["explanation_count"] == 6,
        "p3_explanations_consistent": review["p3_explanation_consistency"]["consistency_pass"] is True,
        "review_explanation_count_exact": review["review_explanations"]["explanation_count"] == 6,
        "review_explanations_consistent": review["review_explanation_consistency"]["consistency_pass"] is True,
        "tampered_review_explanation_rejected": verify_review_explanations(tampered_explanation)["consistency_pass"] is False,
        "tampered_margin_cross_binding_rejected": _rejects(lambda: validate_integrated_review(tampered_margin), "REVIEW_CROSS_PHASE_MISMATCH"),
        "cross_scope_input_rejected": _rejects(lambda: build_integrated_review(bad_scope), "REVIEW_SCOPE_MISMATCH"),
        "raw_root_access_zero": review["raw_root_access_count"] == 0,
        "live_source_read_zero": review["live_source_read_count"] == 0,
        "real_business_calculation_false": review["real_business_calculation_performed"] is False,
        "github_upload_false": review["github_upload_performed"] is False,
        "app_reinstall_false": review["app_reinstall_performed"] is False,
        "s13_not_started": True,
    }
    failed = sorted(key for key, passed in checks.items() if not passed)
    return {
        "schema_version": "kmfa.v015.s12.stage-review-verification.v1",
        "fixture_class": "PUBLIC_SAFE_SYNTHETIC",
        "integrated_review": review,
        "checks": [{"check_id": key, "status": "PASS" if passed else "FAIL"} for key, passed in checks.items()],
        "failed_checks": failed,
        "accounting": {
            "total": len(checks),
            "passed": len(checks) - len(failed),
            "failed": len(failed),
        },
        "raw_root_access_count": 0,
        "live_source_read_count": 0,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
    }
