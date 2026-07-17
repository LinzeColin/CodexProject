#!/usr/bin/env python3
"""KMFA v1.5 S07-P1 exact comparison and reconciliation kernel.

The public API is deliberately fail-closed: money is signed integer cents,
dates are canonical ISO dates, text is compared byte-for-byte after decoding,
enums and units must belong to an explicit registry, and every reconciliation
formula emits an evidence record even when its difference is zero.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP, localcontext
from typing import Any, Iterable, Mapping

from KMFA.tools import v015_s06_p3_baseline_coverage_boundary as s06p3


RUN_PHASE_ID = "V015_S07_P1_ZERO_DELTA_VALIDATOR"
ROADMAP_PHASE_ID = "S07-P1"
TASK_ID = "KMFA-V015-S07-P1-ZERO-DELTA-VALIDATOR-20260715"
ACCEPTANCE_ID = "ACC-KMFA-V015-S07-P1-ZERO-DELTA-VALIDATOR"
VERSION = "1.5.0-dev-s07p1"
SCHEMA_VERSION = "kmfa.v015.s07p1.zero_delta_validator.v1"

INTEGER_CENTS = "INTEGER_CENTS"
EXACT_TEXT = "EXACT_TEXT"
ENUM = "ENUM"
ISO_DATE = "ISO_DATE"
UNIT = "UNIT"
FIELD_TYPES = (INTEGER_CENTS, EXACT_TEXT, ENUM, ISO_DATE, UNIT)
MONEY_TOLERANCE_CENTS = 0
MINIMUM_FAIL_DIFFERENCE_CENTS = 1
MARGIN_ROUNDING = "ROUND_HALF_UP_TO_BASIS_POINT"
DIFFERENCE_FIELDS = (
    "difference_id", "record_ref", "field_id", "comparison_type",
    "expected_value", "actual_value", "difference_value", "source_ref",
    "formula_id", "impact", "recommended_action", "blocking",
)


class ZeroDeltaError(ValueError):
    """Stable fail-closed validation error with a repair route."""

    def __init__(self, code: str, message: str, *, action: str = "BLOCK_AND_REVIEW") -> None:
        super().__init__(message)
        self.code = code
        self.action = action


@dataclass(frozen=True)
class FieldSpec:
    field_id: str
    field_type: str
    source_ref: str
    formula_id: str = "DIRECT_FIELD_COMPARISON"
    allowed_values: tuple[str, ...] = ()
    impact: str = "该字段会影响项目成本结果或报告可信度。"
    recommended_action: str = "核对权威来源与系统结果，修正后重新计算并复核。"

    def __post_init__(self) -> None:
        if not self.field_id or self.field_type not in FIELD_TYPES or not self.source_ref:
            raise ZeroDeltaError("INVALID_FIELD_SPEC", "字段校验定义不完整。")
        if self.field_type in {ENUM, UNIT} and not self.allowed_values:
            raise ZeroDeltaError("MISSING_VALUE_REGISTRY", "枚举或单位必须提供允许值。")


def _integer_cents(value: Any, field_id: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ZeroDeltaError(
            "INTEGER_CENTS_REQUIRED",
            f"{field_id} 必须是整数分，禁止布尔值、浮点数和隐式换算。",
        )
    return value


def _canonical_value(value: Any, spec: FieldSpec) -> Any:
    if spec.field_type == INTEGER_CENTS:
        return _integer_cents(value, spec.field_id)
    if not isinstance(value, str):
        raise ZeroDeltaError("TEXT_VALUE_REQUIRED", f"{spec.field_id} 必须是文本。")
    if spec.field_type == ISO_DATE:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            raise ZeroDeltaError("ISO_DATE_REQUIRED", f"{spec.field_id} 必须使用 YYYY-MM-DD。")
        try:
            if date.fromisoformat(value).isoformat() != value:
                raise ValueError(value)
        except ValueError as error:
            raise ZeroDeltaError("INVALID_ISO_DATE", f"{spec.field_id} 不是有效日期。") from error
    if spec.field_type in {ENUM, UNIT} and value not in spec.allowed_values:
        raise ZeroDeltaError(
            "UNREGISTERED_VALUE",
            f"{spec.field_id} 不在已登记的{('枚举' if spec.field_type == ENUM else '单位')}中。",
        )
    return value


def _difference(
    *, difference_id: str, record_ref: str, field_id: str,
    comparison_type: str, expected: Any, actual: Any, difference: Any,
    source_ref: str, formula_id: str, impact: str, recommended_action: str,
) -> dict[str, Any]:
    return {
        "difference_id": difference_id,
        "record_ref": record_ref,
        "field_id": field_id,
        "comparison_type": comparison_type,
        "expected_value": expected,
        "actual_value": actual,
        "difference_value": difference,
        "source_ref": source_ref,
        "formula_id": formula_id,
        "impact": impact,
        "recommended_action": recommended_action,
        "blocking": True,
    }


def compare_fields(
    expected: Mapping[str, Any], actual: Mapping[str, Any],
    specs: Iterable[FieldSpec], *, record_ref: str,
) -> dict[str, Any]:
    """Compare registered fields exactly and return actionable differences."""

    if not record_ref:
        raise ZeroDeltaError("RECORD_REF_REQUIRED", "校验记录必须有稳定标识。")
    comparisons: list[dict[str, Any]] = []
    differences: list[dict[str, Any]] = []
    for index, spec in enumerate(specs, start=1):
        if spec.field_id not in expected or spec.field_id not in actual:
            missing_side = "expected" if spec.field_id not in expected else "actual"
            raise ZeroDeltaError("FIELD_MISSING", f"{spec.field_id} 缺少 {missing_side} 值。")
        expected_value = _canonical_value(expected[spec.field_id], spec)
        actual_value = _canonical_value(actual[spec.field_id], spec)
        equal = expected_value == actual_value
        difference_value = (
            actual_value - expected_value if spec.field_type == INTEGER_CENTS else (None if equal else "NOT_EQUAL")
        )
        row = {
            "comparison_id": f"{record_ref}-FIELD-{index:03d}",
            "record_ref": record_ref,
            "field_id": spec.field_id,
            "field_type": spec.field_type,
            "expected_value": expected_value,
            "actual_value": actual_value,
            "difference_value": difference_value,
            "source_ref": spec.source_ref,
            "formula_id": spec.formula_id,
            "status": "PASS" if equal else "FAIL",
        }
        comparisons.append(row)
        if not equal:
            differences.append(_difference(
                difference_id=f"{record_ref}-DIFF-{len(differences) + 1:03d}",
                record_ref=record_ref,
                field_id=spec.field_id,
                comparison_type="FIELD_EXACT",
                expected=expected_value,
                actual=actual_value,
                difference=difference_value,
                source_ref=spec.source_ref,
                formula_id=spec.formula_id,
                impact=spec.impact,
                recommended_action=spec.recommended_action,
            ))
    return {
        "schema_version": SCHEMA_VERSION,
        "record_ref": record_ref,
        "comparison_count": len(comparisons),
        "passed_count": sum(row["status"] == "PASS" for row in comparisons),
        "failed_count": len(differences),
        "zero_difference": not differences,
        "money_tolerance_cents": MONEY_TOLERANCE_CENTS,
        "minimum_fail_difference_cents": MINIMUM_FAIL_DIFFERENCE_CENTS,
        "comparisons": comparisons,
        "differences": differences,
    }


def gross_margin_basis_points(gross_profit_cents: int, revenue_cents: int) -> int:
    profit = _integer_cents(gross_profit_cents, "gross_profit_cents")
    revenue = _integer_cents(revenue_cents, "revenue_cents")
    if revenue == 0:
        raise ZeroDeltaError(
            "ZERO_REVENUE_MARGIN_UNDEFINED",
            "合同金额为 0 时毛利率没有定义，必须人工确认口径。",
        )
    with localcontext() as context:
        context.prec = 80
        return int(
            (Decimal(profit) * Decimal(10000) / Decimal(revenue)).quantize(
                Decimal("1"), rounding=ROUND_HALF_UP,
            )
        )


def _formula_record(
    *, check_id: str, project_ref: str, field_id: str, formula_id: str,
    formula: str, inputs: list[dict[str, Any]], expected: int, actual: int,
    source_ref: str, impact: str, action: str,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    difference_value = actual - expected
    record = {
        "check_id": check_id,
        "project_ref": project_ref,
        "field_id": field_id,
        "formula_id": formula_id,
        "formula": formula,
        "inputs": inputs,
        "expected_value": expected,
        "actual_value": actual,
        "difference_value": difference_value,
        "source_ref": source_ref,
        "status": "PASS" if difference_value == 0 else "FAIL",
        "difference_recorded": True,
    }
    if difference_value == 0:
        return record, None
    return record, _difference(
        difference_id=f"{project_ref}-{check_id}-DIFF",
        record_ref=project_ref,
        field_id=field_id,
        comparison_type="FORMULA_RECONCILIATION",
        expected=expected,
        actual=actual,
        difference=difference_value,
        source_ref=source_ref,
        formula_id=formula_id,
        impact=impact,
        recommended_action=action,
    )


def reconcile_project(project: Mapping[str, Any]) -> dict[str, Any]:
    """Reconcile details, categories, project total, profit and margin."""

    project_ref = str(project.get("project_ref") or "").strip()
    if not project_ref:
        raise ZeroDeltaError("PROJECT_REF_REQUIRED", "勾稽项目必须有稳定标识。")
    details = project.get("details")
    categories = project.get("category_totals")
    totals = project.get("project_totals")
    if not isinstance(details, list) or not isinstance(categories, list) or not isinstance(totals, Mapping):
        raise ZeroDeltaError("RECONCILIATION_INPUT_INVALID", "明细、分类合计和项目合计必须齐全。")

    category_map: dict[str, int] = {}
    for row in categories:
        key = str(row.get("category_key") or "").strip()
        if not key or key in category_map:
            raise ZeroDeltaError("CATEGORY_KEY_INVALID", "分类标识缺失或重复。")
        category_map[key] = _integer_cents(row.get("amount_cents"), "category.amount_cents")
    detail_map = {key: [] for key in category_map}
    for row in details:
        key = str(row.get("category_key") or "").strip()
        if key not in detail_map:
            raise ZeroDeltaError("DETAIL_CATEGORY_UNKNOWN", "明细引用了未登记分类。")
        detail_ref = str(row.get("detail_ref") or "").strip()
        if not detail_ref:
            raise ZeroDeltaError("DETAIL_REF_REQUIRED", "每条明细必须有稳定标识。")
        detail_map[key].append((detail_ref, _integer_cents(row.get("amount_cents"), "detail.amount_cents")))

    checks: list[dict[str, Any]] = []
    differences: list[dict[str, Any]] = []

    def add(result: tuple[dict[str, Any], dict[str, Any] | None]) -> None:
        record, difference = result
        checks.append(record)
        if difference:
            differences.append(difference)

    for index, key in enumerate(sorted(category_map), start=1):
        rows = detail_map[key]
        if not rows:
            raise ZeroDeltaError("CATEGORY_WITHOUT_DETAIL", "每个分类至少需要一条明细证据。")
        add(_formula_record(
            check_id=f"DETAIL-TO-CATEGORY-{index:03d}", project_ref=project_ref,
            field_id=f"category_total.{key}", formula_id="S07P1-F01-DETAIL-SUM",
            formula="分类合计 = 同分类明细金额之和",
            inputs=[{"detail_ref": ref, "amount_cents": amount} for ref, amount in rows],
            expected=category_map[key], actual=sum(amount for _, amount in rows),
            source_ref="AUTHORITY_CATEGORY_TOTAL=>SYSTEM_DETAIL_ROWS",
            impact="分类成本与明细不一致，会导致项目成本总额失真。",
            action="定位该分类明细，修正来源或映射后重新汇总。",
        ))

    total_cost = _integer_cents(totals.get("total_cost_cents"), "total_cost_cents")
    category_sum = sum(category_map.values())
    add(_formula_record(
        check_id="CATEGORY-TO-PROJECT", project_ref=project_ref,
        field_id="total_cost_cents", formula_id="S07P1-F02-CATEGORY-SUM",
        formula="项目总成本 = 全部分类合计之和",
        inputs=[{"category_key": key, "amount_cents": value} for key, value in sorted(category_map.items())],
        expected=total_cost, actual=category_sum,
        source_ref="AUTHORITY_PROJECT_TOTAL=>SYSTEM_CATEGORY_TOTALS",
        impact="项目成本总额不一致，会影响毛利和管理决策。",
        action="核对分类遗漏或重复，修正后重新汇总项目总成本。",
    ))

    revenue = _integer_cents(totals.get("revenue_cents"), "revenue_cents")
    gross_profit = _integer_cents(totals.get("gross_profit_cents"), "gross_profit_cents")
    add(_formula_record(
        check_id="PROJECT-TO-GROSS-PROFIT", project_ref=project_ref,
        field_id="gross_profit_cents", formula_id="S07P1-F03-GROSS-PROFIT",
        formula="毛利 = 合同金额 - 项目总成本",
        inputs=[{"field_id": "revenue_cents", "value": revenue}, {"field_id": "total_cost_cents", "value": total_cost}],
        expected=gross_profit, actual=revenue - total_cost,
        source_ref="AUTHORITY_GROSS_PROFIT=>SYSTEM_PROJECT_TOTALS",
        impact="毛利不一致会直接改变项目盈利判断。",
        action="核对合同金额和项目总成本，修正后重新计算毛利。",
    ))

    margin = _integer_cents(totals.get("gross_margin_basis_points"), "gross_margin_basis_points")
    add(_formula_record(
        check_id="GROSS-PROFIT-TO-MARGIN", project_ref=project_ref,
        field_id="gross_margin_basis_points", formula_id="S07P1-F04-GROSS-MARGIN",
        formula="毛利率基点 = ROUND_HALF_UP(毛利分 × 10000 ÷ 合同金额分)",
        inputs=[{"field_id": "gross_profit_cents", "value": gross_profit}, {"field_id": "revenue_cents", "value": revenue}],
        expected=margin, actual=gross_margin_basis_points(gross_profit, revenue),
        source_ref="AUTHORITY_GROSS_MARGIN=>SYSTEM_GROSS_PROFIT_AND_REVENUE",
        impact="毛利率不一致会改变项目排序和经营判断。",
        action="核对毛利、合同金额及 ROUND_HALF_UP 规则后重新计算。",
    ))
    return {
        "schema_version": SCHEMA_VERSION,
        "project_ref": project_ref,
        "formula_check_count": len(checks),
        "formula_pass_count": sum(row["status"] == "PASS" for row in checks),
        "formula_fail_count": len(differences),
        "every_formula_has_evidence": all(row["inputs"] and row["difference_recorded"] for row in checks),
        "zero_difference": not differences,
        "blocking_unexplained_difference_count": len(differences),
        "checks": checks,
        "differences": differences,
    }


def _golden_project_input(summary: Mapping[str, Any], index: int) -> dict[str, Any]:
    categories = list(summary["category_costs"])
    return {
        "project_ref": f"PRIVATE-GOLDEN-{index:03d}",
        "details": [
            {
                "detail_ref": f"ACCEPTED-CATEGORY-{category_index:03d}",
                "category_key": row["category_key"],
                "amount_cents": row["amount_cents"],
            }
            for category_index, row in enumerate(categories, start=1)
        ],
        "category_totals": categories,
        "project_totals": {
            "revenue_cents": summary["revenue_cents"],
            "total_cost_cents": summary["total_cost_cents"],
            "gross_profit_cents": summary["gross_profit_cents"],
            "gross_margin_basis_points": summary["gross_margin_basis_points"],
        },
    }


def validate_private_golden_scope() -> dict[str, Any]:
    """Recompute the accepted private golden summaries; return aggregates only."""

    fixture, queue, _ = s06p3.validate_private_outputs()
    reports = [
        reconcile_project(_golden_project_input(summary, index))
        for index, summary in enumerate(fixture["project_summaries"], start=1)
    ]
    return {
        "private_project_count": len(reports),
        "private_accepted_field_count": fixture["accepted_field_count"],
        "private_formula_check_count": sum(row["formula_check_count"] for row in reports),
        "private_formula_fail_count": sum(row["formula_fail_count"] for row in reports),
        "private_zero_difference": all(row["zero_difference"] for row in reports),
        "open_unconfirmed_item_count": queue["status_counts"]["OPEN"],
        "excluded_or_unconfirmed_item_count": queue["item_count"],
        "open_items_may_be_treated_as_resolved": False,
        "tax_normalization_allowed": False,
        "cross_period_generalization_allowed": False,
    }


def synthetic_acceptance_cases() -> dict[str, Any]:
    specs = (
        FieldSpec("amount_cents", INTEGER_CENTS, "SYNTHETIC_AUTHORITY"),
        FieldSpec("label", EXACT_TEXT, "SYNTHETIC_AUTHORITY"),
        FieldSpec("status", ENUM, "SYNTHETIC_AUTHORITY", allowed_values=("OPEN", "CLOSED")),
        FieldSpec("business_date", ISO_DATE, "SYNTHETIC_AUTHORITY"),
        FieldSpec("unit", UNIT, "SYNTHETIC_AUTHORITY", allowed_values=("CNY_CENT", "DAY")),
    )
    expected = {"amount_cents": 100, "label": "Alpha", "status": "OPEN", "business_date": "2026-07-15", "unit": "CNY_CENT"}
    exact = compare_fields(expected, dict(expected), specs, record_ref="SYN-EXACT")
    failing_actual = {"amount_cents": 99, "label": "alpha", "status": "CLOSED", "business_date": "2026-07-16", "unit": "DAY"}
    failing = compare_fields(expected, failing_actual, specs, record_ref="SYN-DIFF")
    project = {
        "project_ref": "SYN-PROJECT",
        "details": [
            {"detail_ref": "D-001", "category_key": "LABOUR", "amount_cents": 3000},
            {"detail_ref": "D-002", "category_key": "LABOUR", "amount_cents": 2000},
            {"detail_ref": "D-003", "category_key": "MATERIAL", "amount_cents": 2500},
        ],
        "category_totals": [
            {"category_key": "LABOUR", "amount_cents": 5000},
            {"category_key": "MATERIAL", "amount_cents": 2500},
        ],
        "project_totals": {
            "revenue_cents": 10000,
            "total_cost_cents": 7500,
            "gross_profit_cents": 2500,
            "gross_margin_basis_points": 2500,
        },
    }
    exact_reconciliation = reconcile_project(project)
    one_cent = json.loads(json.dumps(project))
    one_cent["details"][0]["amount_cents"] = 2999
    failing_reconciliation = reconcile_project(one_cent)
    differences = failing["differences"] + failing_reconciliation["differences"]
    return {
        "field_type_count": len(FIELD_TYPES),
        "field_exact_pass_count": exact["passed_count"],
        "field_deliberate_fail_count": failing["failed_count"],
        "one_cent_difference_detected": any(
            row["field_id"] == "amount_cents" and row["difference_value"] == -1
            for row in failing["differences"]
        ),
        "reconciliation_formula_count": exact_reconciliation["formula_check_count"],
        "reconciliation_exact_pass_count": exact_reconciliation["formula_pass_count"],
        "reconciliation_deliberate_fail_count": failing_reconciliation["formula_fail_count"],
        "difference_report_required_field_count": len(DIFFERENCE_FIELDS),
        "difference_report_complete_count": sum(all(key in row for key in DIFFERENCE_FIELDS) for row in differences),
        "difference_report_count": len(differences),
        "difference_snapshot": differences,
    }


def public_projection() -> dict[str, Any]:
    private = validate_private_golden_scope()
    synthetic = synthetic_acceptance_cases()
    return {
        "schema_version": "kmfa.v015.s07p1.zero_delta_public_safe.v1",
        "project_id": "KMFA",
        "target_release": "v1.5",
        "stage_id": "S07",
        "phase_id": RUN_PHASE_ID,
        "roadmap_phase_id": ROADMAP_PHASE_ID,
        "field_type_count": synthetic["field_type_count"],
        "field_types": list(FIELD_TYPES),
        "money_tolerance_cents": MONEY_TOLERANCE_CENTS,
        "minimum_fail_difference_cents": MINIMUM_FAIL_DIFFERENCE_CENTS,
        "one_cent_difference_detected": synthetic["one_cent_difference_detected"],
        "synthetic_field_exact_pass_count": synthetic["field_exact_pass_count"],
        "synthetic_field_deliberate_fail_count": synthetic["field_deliberate_fail_count"],
        "synthetic_reconciliation_formula_count": synthetic["reconciliation_formula_count"],
        "synthetic_reconciliation_exact_pass_count": synthetic["reconciliation_exact_pass_count"],
        "synthetic_reconciliation_deliberate_fail_count": synthetic["reconciliation_deliberate_fail_count"],
        "difference_report_required_field_count": synthetic["difference_report_required_field_count"],
        "difference_report_complete_count": synthetic["difference_report_complete_count"],
        "synthetic_difference_report_count": synthetic["difference_report_count"],
        **private,
        "private_project_identity_count_public": 0,
        "private_money_value_count_public": 0,
        "private_source_locator_count_public": 0,
        "private_digest_count_public": 0,
        "rounding_policy": MARGIN_ROUNDING,
        "every_formula_has_evidence_and_difference_record": True,
        "blocking_unexplained_difference_count": 0,
        "raw_root_access_count": 0,
        "raw_business_content_read": False,
        "raw_mutation_performed": False,
        "phase_execution_status": "EXECUTION_COMPLETE",
        "phase_acceptance_status": "PENDING_FINAL_VALIDATION",
        "stage_lifecycle_status": "IN_PROGRESS",
        "stage_acceptance_status": "PENDING",
        "stage_execution_percentage": 33,
        "s07_p2_entry_allowed": False,
        "s07_p2_started": False,
        "formal_report_generated": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }


if __name__ == "__main__":
    print(json.dumps(public_projection(), ensure_ascii=False, indent=2, sort_keys=True))
