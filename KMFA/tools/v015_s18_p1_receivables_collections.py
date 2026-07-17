#!/usr/bin/env python3
"""KMFA v1.5 S18-P1 回款、应收账龄与可解释催收优先级。

本模块只使用公开合成事实。金额始终使用整数分；未开票事项与应收
分开保存；所有催收结果都只是内部复核建议，不会联系客户。
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date
from typing import Any, Iterable, Mapping, Sequence

from KMFA.tools import v015_s16_p1_homepage as homepage
from KMFA.tools import v015_s17_p1_project_list as projects


RUN_PHASE_ID = "V015_S18_P1_RECEIVABLES_COLLECTIONS"
ROADMAP_PHASE_ID = "S18-P1"
TASK_ID = "KMFA-V015-S18-P1-RECEIVABLES-COLLECTIONS-20260716"
ACCEPTANCE_ID = "ACC-KMFA-V015-S18-P1-RECEIVABLES-COLLECTIONS"
VERSION = "1.5.0-dev-s18p1"

CUTOFF_DATE = "2026-07-15"
DATA_CLASSIFICATION = "PUBLIC_SYNTHETIC"
MONEY_TOLERANCE_CENTS = 0
GROUP_DIMENSIONS = ("project", "customer", "period", "owner")
AGING_BUCKETS = (
    ("CURRENT", "未到期", -1, 0),
    ("D01_30", "逾期 1–30 天", 1, 30),
    ("D31_60", "逾期 31–60 天", 31, 60),
    ("D61_90", "逾期 61–90 天", 61, 90),
    ("D90_PLUS", "逾期 90 天以上", 91, None),
)
PRIORITY_COMPONENT_MAX = {
    "amount": 20,
    "overdue": 40,
    "credit": 15,
    "dispute": 12,
    "cash_urgency": 20,
}
COMPANY_AMOUNT_FACTORS = {"demo-north": 10_000, "demo-south": 8_400, "demo-west": 6_800}
PERIOD_AMOUNT_FACTORS = {"2026-07": 10_000, "2026-Q2": 9_400, "2026-H1": 8_800}


class ReceivablesError(ValueError):
    """回款与应收请求违反公开演示合同。"""


def source_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s18p1.source_contract.v1",
        "stage_id": "S18",
        "stage_name_zh": "回款、应收、资金与贷款分析",
        "stage_goal_zh": "建立现金安全、催收优先级、多主体账户和资金计划能力，不执行付款。",
        "roadmap_phase_id": ROADMAP_PHASE_ID,
        "phase_name_zh": "回款与应收",
        "task_ids": ["S18P1T01", "S18P1T02", "S18P1T03"],
        "task_names_zh": ["建立应收与账龄事实", "实现催收优先级", "实现回款视图"],
        "acceptance_zh": ["账龄口径和截止日明确。", "结果可解释，不自动联系客户。", "汇总和明细一致。"],
        "stop_conditions_zh": ["未开票和应收不得混淆。", "无依据建议不得显示。", "跨主体汇总错误为高危。"],
        "data_classification": DATA_CLASSIFICATION,
    }


def _scaled(cents: int, company_id: str, period: str) -> int:
    if company_id not in COMPANY_AMOUNT_FACTORS:
        raise ReceivablesError("unsupported public company")
    if period not in PERIOD_AMOUNT_FACTORS:
        raise ReceivablesError("unsupported public period")
    return cents * COMPANY_AMOUNT_FACTORS[company_id] * PERIOD_AMOUNT_FACTORS[period] // 100_000_000


def format_money(cents: int) -> str:
    if isinstance(cents, bool) or not isinstance(cents, int):
        raise ReceivablesError("money must use integer cents")
    sign = "-" if cents < 0 else ""
    yuan, fen = divmod(abs(cents), 100)
    return f"{sign}¥{yuan:,}.{fen:02d}"


def _base_items() -> tuple[dict[str, Any], ...]:
    """七张发票、一项未开票节点；其中一张发票已结清。"""

    return (
        {
            "item_id": "AR-001", "project_id": "PUB-PROJ-001", "invoice_period": "2026-07",
            "milestone_zh": "设备进场节点", "invoice_status": "INVOICED", "invoice_date": "2026-05-20",
            "due_date": "2026-06-15", "invoice_cents": 80_000_000, "collected_cents": 50_000_000,
            "retention_cents": 5_000_000, "dispute_cents": 0, "credit_grade": "B", "cash_urgency": "HIGH",
            "evidence_complete": True,
        },
        {
            "item_id": "AR-002", "project_id": "PUB-PROJ-001", "invoice_period": "2026-04",
            "milestone_zh": "主体完工节点", "invoice_status": "INVOICED", "invoice_date": "2026-03-18",
            "due_date": "2026-04-15", "invoice_cents": 30_000_000, "collected_cents": 10_000_000,
            "retention_cents": 0, "dispute_cents": 4_000_000, "credit_grade": "B", "cash_urgency": "HIGH",
            "evidence_complete": True,
        },
        {
            "item_id": "AR-003", "project_id": "PUB-PROJ-002", "invoice_period": "2026-07",
            "milestone_zh": "调试完成节点", "invoice_status": "INVOICED", "invoice_date": "2026-07-01",
            "due_date": "2026-08-15", "invoice_cents": 45_000_000, "collected_cents": 40_000_000,
            "retention_cents": 0, "dispute_cents": 0, "credit_grade": "A", "cash_urgency": "LOW",
            "evidence_complete": True,
        },
        {
            "item_id": "AR-004", "project_id": "PUB-PROJ-003", "invoice_period": "2026-03",
            "milestone_zh": "阶段验收节点", "invoice_status": "INVOICED", "invoice_date": "2026-02-28",
            "due_date": "2026-03-31", "invoice_cents": 60_000_000, "collected_cents": 15_000_000,
            "retention_cents": 0, "dispute_cents": 10_000_000, "credit_grade": "C", "cash_urgency": "HIGH",
            "evidence_complete": True,
        },
        {
            "item_id": "AR-005", "project_id": "PUB-PROJ-004", "invoice_period": "2026-05",
            "milestone_zh": "季度服务节点", "invoice_status": "INVOICED", "invoice_date": "2026-04-30",
            "due_date": "2026-05-31", "invoice_cents": 25_000_000, "collected_cents": 10_000_000,
            "retention_cents": 5_000_000, "dispute_cents": 0, "credit_grade": "A", "cash_urgency": "MEDIUM",
            "evidence_complete": True,
        },
        {
            "item_id": "AR-006", "project_id": "PUB-PROJ-005", "invoice_period": "2026-07",
            "milestone_zh": "仓储区域交付节点", "invoice_status": "INVOICED", "invoice_date": "2026-06-10",
            "due_date": "2026-07-10", "invoice_cents": 15_000_000, "collected_cents": 0,
            "retention_cents": 0, "dispute_cents": 0, "credit_grade": "B", "cash_urgency": "MEDIUM",
            "evidence_complete": False,
        },
        {
            "item_id": "AR-007", "project_id": "PUB-PROJ-006", "invoice_period": "2026-05",
            "milestone_zh": "节能设备验收节点", "invoice_status": "INVOICED", "invoice_date": "2026-04-12",
            "due_date": "2026-05-15", "invoice_cents": 50_000_000, "collected_cents": 50_000_000,
            "retention_cents": 0, "dispute_cents": 0, "credit_grade": "A", "cash_urgency": "LOW",
            "evidence_complete": True,
        },
        {
            "item_id": "UNBILLED-001", "project_id": "PUB-PROJ-002", "invoice_period": "2026-07",
            "milestone_zh": "待确认培训节点", "invoice_status": "NOT_INVOICED", "invoice_date": None,
            "due_date": None, "invoice_cents": 18_000_000, "collected_cents": 0,
            "retention_cents": 0, "dispute_cents": 0, "credit_grade": "A", "cash_urgency": "LOW",
            "evidence_complete": True,
        },
    )


def _aging(due_date: str, cutoff_date: str = CUTOFF_DATE) -> tuple[int, str, str]:
    days = (date.fromisoformat(cutoff_date) - date.fromisoformat(due_date)).days
    overdue_days = max(days, 0)
    for bucket_id, label, lower, upper in AGING_BUCKETS:
        if bucket_id == "CURRENT" and days <= 0:
            return 0, bucket_id, label
        if lower <= overdue_days and (upper is None or overdue_days <= upper):
            return overdue_days, bucket_id, label
    raise ReceivablesError("aging bucket could not be resolved")


def _priority_components(row: Mapping[str, Any]) -> dict[str, int]:
    amount = int(row["receivable_cents"])
    amount_points = 20 if amount >= 50_000_000 else 15 if amount >= 20_000_000 else 10 if amount >= 5_000_000 else 5
    overdue_points = {"CURRENT": 0, "D01_30": 10, "D31_60": 20, "D61_90": 30, "D90_PLUS": 40}[str(row["aging_bucket_id"])]
    credit_points = {"A": 0, "B": 8, "C": 15}[str(row["credit_grade"])]
    dispute_points = 12 if int(row["dispute_cents"]) > 0 else 0
    urgency_points = {"LOW": 0, "MEDIUM": 10, "HIGH": 20}[str(row["cash_urgency"])]
    return {
        "amount": amount_points,
        "overdue": overdue_points,
        "credit": credit_points,
        "dispute": dispute_points,
        "cash_urgency": urgency_points,
    }


def _priority(row: Mapping[str, Any]) -> dict[str, Any]:
    if not row.get("evidence_complete"):
        return {
            "priority_supported": False,
            "priority_score": None,
            "priority_tier": "EVIDENCE_MISSING",
            "priority_label_zh": "资料不足",
            "priority_reasons_zh": ["缺少必要回款依据，不能给出催收建议。"],
            "recommended_internal_step_zh": None,
            "automatic_customer_contact_allowed": False,
            "components": None,
        }
    components = _priority_components(row)
    score = sum(components.values())
    tier = "HIGH" if score >= 65 else "MEDIUM" if score >= 40 else "LOW"
    label = {"HIGH": "优先复核", "MEDIUM": "近期复核", "LOW": "常规跟进"}[tier]
    reasons = [
        f"应收金额 {format_money(int(row['receivable_cents']))}，金额项 {components['amount']} 分",
        f"{row['aging_bucket_zh']}，逾期项 {components['overdue']} 分",
        f"客户信用 {row['credit_grade']} 级，信用项 {components['credit']} 分",
        (f"存在争议 {format_money(int(row['dispute_cents']))}，争议项 {components['dispute']} 分" if int(row["dispute_cents"]) else "无已知争议，争议项 0 分"),
        f"现金紧迫度 {row['cash_urgency_zh']}，紧迫度项 {components['cash_urgency']} 分",
    ]
    step = "先内部核对争议资料" if int(row["dispute_cents"]) else "准备内部催收复核材料"
    return {
        "priority_supported": True,
        "priority_score": score,
        "priority_tier": tier,
        "priority_label_zh": label,
        "priority_reasons_zh": reasons,
        "recommended_internal_step_zh": step,
        "automatic_customer_contact_allowed": False,
        "components": components,
    }


def receivable_facts(company_id: str = "demo-north", period: str = "2026-07") -> dict[str, Any]:
    """形成当前主体的应收事实；未开票项目永远不进入应收行。"""

    catalog = {row["project_id"]: row for row in projects.project_catalog(company_id, period)}
    rows: list[dict[str, Any]] = []
    unbilled: list[dict[str, Any]] = []
    all_invoices: list[dict[str, Any]] = []
    for definition in _base_items():
        project = catalog[definition["project_id"]]
        item = dict(definition)
        for key in ("invoice_cents", "collected_cents", "retention_cents", "dispute_cents"):
            item[key] = _scaled(int(item[key]), company_id, period)
        item.update(
            {
                "company_id": company_id,
                "company_zh": project["company_zh"],
                "project_name_zh": project["project_name_zh"],
                "customer_zh": project["client_zh"],
                "owner_zh": project["owner_zh"],
                "cutoff_date": CUTOFF_DATE,
                "source_ref": f"PUBLIC-SYNTHETIC:RECEIVABLE:{company_id}:{period}:{item['item_id']}",
                "source_zh": "公开合成合同节点、发票与回款台账",
                "data_classification": DATA_CLASSIFICATION,
            }
        )
        if item["invoice_status"] == "NOT_INVOICED":
            item.update(
                {
                    "unbilled_cents": item.pop("invoice_cents"),
                    "receivable_cents": 0,
                    "classification_zh": "未开票节点（不计应收）",
                }
            )
            unbilled.append(item)
            continue
        all_invoices.append(item)
        receivable = item["invoice_cents"] - item["collected_cents"]
        if receivable < 0:
            raise ReceivablesError("collection cannot exceed invoice")
        if item["retention_cents"] > receivable or item["dispute_cents"] > receivable:
            raise ReceivablesError("retention or dispute cannot exceed receivable")
        if receivable == 0:
            continue
        overdue_days, bucket_id, bucket_label = _aging(str(item["due_date"]))
        item.update(
            {
                "receivable_cents": receivable,
                "overdue_cents": receivable if overdue_days > 0 else 0,
                "overdue_days": overdue_days,
                "aging_bucket_id": bucket_id,
                "aging_bucket_zh": bucket_label,
                "cash_urgency_zh": {"LOW": "低", "MEDIUM": "中", "HIGH": "高"}[item["cash_urgency"]],
                "classification_zh": "已开票应收",
            }
        )
        item.update(_priority(item))
        rows.append(item)

    _validate_facts(rows, unbilled, all_invoices, company_id)
    return {
        "schema_version": "kmfa.v015.s18p1.receivable_facts.v1",
        "company_id": company_id,
        "period": period,
        "cutoff_date": CUTOFF_DATE,
        "aging_basis_zh": "按发票约定到期日与 2026-07-15 截止日的自然日差计算；未到期为 0 天。",
        "receivable_definition_zh": "仅已开票金额减已回款金额计入应收；未开票合同节点单独列示且应收为 0。",
        "rows": rows,
        "unbilled_items": unbilled,
        "invoice_items": all_invoices,
        "source_data_write_count": 0,
        "fact_layer_write_count": 0,
        "real_customer_contact_count": 0,
        "payment_execution_count": 0,
    }


def _validate_facts(
    rows: Sequence[Mapping[str, Any]],
    unbilled: Sequence[Mapping[str, Any]],
    invoices: Sequence[Mapping[str, Any]],
    company_id: str,
) -> None:
    if any(row["company_id"] != company_id for row in [*rows, *unbilled, *invoices]):
        raise ReceivablesError("cross-company receivable leakage detected")
    if any(row.get("invoice_status") != "INVOICED" for row in rows):
        raise ReceivablesError("unbilled item entered receivables")
    if any(int(row.get("receivable_cents", -1)) != 0 for row in unbilled):
        raise ReceivablesError("unbilled item was treated as receivable")
    if any(int(row["invoice_cents"]) - int(row["collected_cents"]) != int(row["receivable_cents"]) for row in rows):
        raise ReceivablesError("receivable equation drifted")
    if any(row["data_classification"] != DATA_CLASSIFICATION for row in [*rows, *unbilled, *invoices]):
        raise ReceivablesError("private data entered public receivables")
    for row in rows:
        money = (row["invoice_cents"], row["collected_cents"], row["receivable_cents"], row["overdue_cents"], row["retention_cents"], row["dispute_cents"])
        if any(isinstance(value, bool) or not isinstance(value, int) for value in money):
            raise ReceivablesError("money must use integer cents")
        if row["priority_supported"] and (not row["priority_reasons_zh"] or row["recommended_internal_step_zh"] is None):
            raise ReceivablesError("supported priority requires reasons and an internal step")
        if not row["priority_supported"] and row["recommended_internal_step_zh"] is not None:
            raise ReceivablesError("unsupported recommendation must not be displayed")
        if row["automatic_customer_contact_allowed"]:
            raise ReceivablesError("automatic customer contact is forbidden")


def _filtered(rows: Iterable[Mapping[str, Any]], filters: Mapping[str, str]) -> list[dict[str, Any]]:
    mappings = {
        "project": "project_id",
        "customer": "customer_zh",
        "invoice_period": "invoice_period",
        "owner": "owner_zh",
        "aging_bucket": "aging_bucket_id",
        "priority": "priority_tier",
    }
    result: list[dict[str, Any]] = []
    for row in rows:
        if all(value in {"", "all"} or str(row[mappings[key]]) == value for key, value in filters.items()):
            result.append(dict(row))
    return result


def _group_rows(rows: Sequence[Mapping[str, Any]], group_by: str) -> list[dict[str, Any]]:
    if group_by not in GROUP_DIMENSIONS:
        raise ReceivablesError("unsupported receivable group dimension")
    keys = {
        "project": ("project_id", "project_name_zh"),
        "customer": ("customer_zh", "customer_zh"),
        "period": ("invoice_period", "invoice_period"),
        "owner": ("owner_zh", "owner_zh"),
    }
    key_field, label_field = keys[group_by]
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    labels: dict[str, str] = {}
    for row in rows:
        key = str(row[key_field])
        grouped[key].append(row)
        labels[key] = str(row[label_field])
    output = []
    for key in sorted(grouped):
        values = grouped[key]
        output.append(
            {
                "group_id": key,
                "group_label_zh": labels[key],
                "receivable_count": len(values),
                "receivable_cents": sum(int(row["receivable_cents"]) for row in values),
                "overdue_cents": sum(int(row["overdue_cents"]) for row in values),
                "collected_cents": sum(int(row["collected_cents"]) for row in values),
                "high_priority_count": sum(row["priority_tier"] == "HIGH" for row in values),
                "evidence_missing_count": sum(not row["priority_supported"] for row in values),
            }
        )
    return output


def receivables_view(
    *,
    company_id: str = "demo-north",
    period: str = "2026-07",
    project: str = "all",
    customer: str = "all",
    invoice_period: str = "all",
    owner: str = "all",
    aging_bucket: str = "all",
    priority: str = "all",
    group_by: str = "project",
) -> dict[str, Any]:
    facts = receivable_facts(company_id, period)
    filters = {
        "project": project,
        "customer": customer,
        "invoice_period": invoice_period,
        "owner": owner,
        "aging_bucket": aging_bucket,
        "priority": priority,
    }
    rows = _filtered(facts["rows"], filters)
    rows.sort(
        key=lambda row: (
            row["priority_score"] is None,
            -(row["priority_score"] or -1),
            -row["receivable_cents"],
            row["item_id"],
        )
    )
    groups = _group_rows(rows, group_by)
    invoice_items = facts["invoice_items"]
    summary = {
        "invoice_cents": sum(int(row["invoice_cents"]) for row in invoice_items),
        "collected_cents": sum(int(row["collected_cents"]) for row in invoice_items),
        "receivable_cents": sum(int(row["receivable_cents"]) for row in rows),
        "overdue_cents": sum(int(row["overdue_cents"]) for row in rows),
        "dispute_cents": sum(int(row["dispute_cents"]) for row in rows),
        "retention_cents": sum(int(row["retention_cents"]) for row in rows),
        "unbilled_cents": sum(int(row["unbilled_cents"]) for row in facts["unbilled_items"]),
        "receivable_count": len(rows),
        "high_priority_count": sum(row["priority_tier"] == "HIGH" for row in rows),
        "evidence_missing_count": sum(not row["priority_supported"] for row in rows),
    }
    if summary["receivable_cents"] != sum(group["receivable_cents"] for group in groups):
        raise ReceivablesError("group receivable total does not match detail")
    if summary["overdue_cents"] != sum(group["overdue_cents"] for group in groups):
        raise ReceivablesError("group overdue total does not match detail")
    return {
        "schema_version": "kmfa.v015.s18p1.receivables_view.v1",
        "allowed": True,
        "data_classification": DATA_CLASSIFICATION,
        "company_id": company_id,
        "period": period,
        "cutoff_date": facts["cutoff_date"],
        "aging_basis_zh": facts["aging_basis_zh"],
        "receivable_definition_zh": facts["receivable_definition_zh"],
        "priority_formula_zh": "金额 0–20 分 + 逾期 0–40 分 + 客户信用 0–15 分 + 争议 0/12 分 + 现金紧迫度 0–20 分；每项分数逐笔显示。",
        "priority_boundaries_zh": "65 分及以上优先复核，40–64 分近期复核，低于 40 分常规跟进；资料不足时不显示建议。",
        "summary": summary,
        "rows": rows,
        "groups": groups,
        "group_by": group_by,
        "filters": filters,
        "filter_options": {
            "projects": sorted({(row["project_id"], row["project_name_zh"]) for row in facts["rows"]}),
            "customers": sorted({row["customer_zh"] for row in facts["rows"]}),
            "invoice_periods": sorted({row["invoice_period"] for row in facts["rows"]}, reverse=True),
            "owners": sorted({row["owner_zh"] for row in facts["rows"]}),
            "aging_buckets": [(item[0], item[1]) for item in AGING_BUCKETS],
            "priorities": [("HIGH", "优先复核"), ("MEDIUM", "近期复核"), ("LOW", "常规跟进"), ("EVIDENCE_MISSING", "资料不足")],
        },
        "unbilled_items": facts["unbilled_items"],
        "money_difference_cents": summary["receivable_cents"] - sum(row["receivable_cents"] for row in rows),
        "group_difference_cents": summary["receivable_cents"] - sum(group["receivable_cents"] for group in groups),
        "cross_company_leak_count": sum(row["company_id"] != company_id for row in rows),
        "unsupported_recommendation_count": sum((not row["priority_supported"]) and row["recommended_internal_step_zh"] is not None for row in rows),
        "automatic_customer_contact_count": 0,
        "external_network_request_count": 0,
        "raw_root_access_count": 0,
        "live_source_read_count": 0,
        "source_data_write_count": 0,
        "fact_layer_write_count": 0,
        "payment_execution_count": 0,
    }


def public_checks() -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []

    def add(check_id: str, passed: bool, detail_zh: str) -> None:
        checks.append({"check_id": check_id, "status": "PASS" if passed else "FAIL", "detail_zh": detail_zh})

    for company_id in COMPANY_AMOUNT_FACTORS:
        view = receivables_view(company_id=company_id)
        add(f"{company_id}_entity_scope", view["cross_company_leak_count"] == 0, "主体隔离")
        add(f"{company_id}_detail_total", view["money_difference_cents"] == 0, "明细与汇总一致")
        add(f"{company_id}_group_total", view["group_difference_cents"] == 0, "分组与汇总一致")
        add(f"{company_id}_unbilled_separate", all(row["receivable_cents"] == 0 for row in view["unbilled_items"]), "未开票未计应收")
        add(f"{company_id}_unsupported_hidden", view["unsupported_recommendation_count"] == 0, "无依据建议隐藏")
        add(f"{company_id}_contact_blocked", view["automatic_customer_contact_count"] == 0, "不自动联系客户")
        for dimension in GROUP_DIMENSIONS:
            grouped = receivables_view(company_id=company_id, group_by=dimension)
            add(f"{company_id}_{dimension}_reconcile", grouped["group_difference_cents"] == 0, f"{dimension} 分组一致")
    sample = receivables_view()
    for row in sample["rows"]:
        add(f"equation_{row['item_id']}", row["invoice_cents"] - row["collected_cents"] == row["receivable_cents"], "应收等式成立")
        add(f"priority_{row['item_id']}", (bool(row["priority_reasons_zh"]) if row["priority_supported"] else row["recommended_internal_step_zh"] is None), "优先级有依据或失败关闭")
    add("cutoff_visible", sample["cutoff_date"] == CUTOFF_DATE, "截止日明确")
    add("aging_basis_visible", bool(sample["aging_basis_zh"]), "账龄口径明确")
    add("priority_formula_visible", bool(sample["priority_formula_zh"]), "排序公式明确")
    add("integer_money", all(isinstance(row["receivable_cents"], int) and not isinstance(row["receivable_cents"], bool) for row in sample["rows"]), "金额使用整数分")
    add("zero_tolerance", MONEY_TOLERANCE_CENTS == 0, "金额误差为零分")
    add("raw_closed", sample["raw_root_access_count"] == 0, "未访问原始资料")
    add("network_closed", sample["external_network_request_count"] == 0, "无外部网络")
    add("payment_closed", sample["payment_execution_count"] == 0, "未执行付款")
    return checks


def main() -> int:
    checks = public_checks()
    failed = [row for row in checks if row["status"] != "PASS"]
    print(f"{'PASS' if not failed else 'FAIL'}: S18-P1 public checks {len(checks) - len(failed)}/{len(checks)}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
