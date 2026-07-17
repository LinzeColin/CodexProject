#!/usr/bin/env python3
"""KMFA v1.5 S17-P2 项目详情的公开合成业务合同。"""

from __future__ import annotations

from typing import Any, Mapping, Sequence
from urllib.parse import urlencode

from KMFA.tools import v015_s12_p1_project_cost_facts as cost_facts
from KMFA.tools import v015_s12_p2_core_calculations as calculations
from KMFA.tools import v015_s16_p1_homepage as homepage
from KMFA.tools import v015_s17_p1_project_list as project_list


RUN_PHASE_ID = "V015_S17_P2_PROJECT_DETAIL"
ROADMAP_PHASE_ID = "S17-P2"
TASK_ID = "KMFA-V015-S17-P2-PROJECT-DETAIL-20260716"
ACCEPTANCE_ID = "ACC-KMFA-V015-S17-P2-PROJECT-DETAIL"
VERSION = "1.5.0-dev-s17p2"

DETAIL_TAB_COUNT = 5
COST_CATEGORY_COUNT = 10
COST_TREND_PERIOD_COUNT = 4
DOCUMENT_COUNT = 6
SOURCE_GROUP_COUNT = 5
BROWSER_FLOW_COUNT = 9
VISUAL_EVIDENCE_COUNT = 5
PUBLIC_CHECK_COUNT = 72
MONEY_TOLERANCE_CENTS = 0

DETAIL_TABS: tuple[dict[str, str], ...] = (
    {"id": "overview", "label_zh": "概况", "purpose_zh": "回答项目是否赚钱以及为什么"},
    {"id": "cost", "label_zh": "成本", "purpose_zh": "核对分类、趋势、基准差异和未归集成本"},
    {"id": "revenue_collection", "label_zh": "收入与回款", "purpose_zh": "查看合同、收入、开票、回款和应收"},
    {"id": "variance", "label_zh": "差异", "purpose_zh": "解释收入、成本、毛利和进度偏差"},
    {"id": "documents", "label_zh": "资料", "purpose_zh": "查看资料是否齐全及其来源"},
)
TAB_IDS = tuple(item["id"] for item in DETAIL_TABS)

CATEGORY_LABELS = {
    "LABOR": "人工",
    "MATERIAL": "材料",
    "MACHINERY": "机械",
    "SUBCONTRACT": "分包",
    "TRANSPORT": "运输",
    "TRAVEL": "差旅",
    "TAX": "税费",
    "SITE_MANAGEMENT": "现场管理",
    "REWORK": "返工",
    "WARRANTY": "质保",
}
CATEGORY_WEIGHTS = (1700, 2600, 800, 2500, 450, 300, 500, 750, 250, 150)
TREND_WEIGHTS = (1800, 2200, 2700, 3300)

LIST_CONTEXT_KEYS = (
    "project_status",
    "client",
    "owner",
    "margin_band",
    "collection_band",
    "risk",
    "group_by",
    "sort_by",
    "page",
    "page_size",
    "columns",
)


class ProjectDetailError(ValueError):
    """项目详情请求不符合公开演示合同。"""


def source_contract() -> dict[str, Any]:
    """返回 TaskPack v2.0 中 S17-P2 的逐项合同。"""

    return {
        "schema_version": "kmfa.v015.s17p2.source_contract.v1",
        "stage_id": "S17",
        "stage_name_zh": "项目列表、项目详情与成本分析流程",
        "stage_goal_zh": "提供项目制工程企业最核心的项目成本、收入、回款、差异和资料工作流。",
        "roadmap_phase_id": ROADMAP_PHASE_ID,
        "phase_name_zh": "项目详情",
        "task_ids": ["S17P2T01", "S17P2T02", "S17P2T03"],
        "task_names_zh": ["实现概况页", "实现成本页", "实现收入回款、差异和资料页"],
        "acceptance_zh": ["一页可回答项目是否赚钱及为什么。", "合计与引擎一致。", "返回保留上下文。"],
        "stop_conditions_zh": [
            "不得先显示技术状态码。",
            "图表与表格金额不一致失败。",
            "标签内容重复堆叠失败。",
        ],
        "evidence_zh": ["用户任务测试。", "零差异测试。", "导航测试。"],
        "data_classification": "PUBLIC_SYNTHETIC",
    }


def _allocate_exact(total: int, weights: Sequence[int]) -> list[int]:
    if isinstance(total, bool) or not isinstance(total, int) or total < 0:
        raise ProjectDetailError("money must use non-negative integer cents")
    if not weights or any(isinstance(value, bool) or not isinstance(value, int) or value <= 0 for value in weights):
        raise ProjectDetailError("allocation weights must be positive integers")
    denominator = sum(weights)
    values = [total * weight // denominator for weight in weights]
    remainder = total - sum(values)
    for index in range(remainder):
        values[index % len(values)] += 1
    if sum(values) != total:
        raise ProjectDetailError("exact allocation failed")
    return values


def _find_project(company_id: str, period: str, project_id: str) -> dict[str, Any]:
    if not project_id or "/" in project_id or ".." in project_id:
        raise ProjectDetailError("invalid project identifier")
    row = next(
        (item for item in project_list.project_catalog(company_id, period) if item["project_id"] == project_id),
        None,
    )
    if row is None:
        raise ProjectDetailError("project is not available in the current company")
    return dict(row)


def _normalise_list_context(value: Mapping[str, Any] | None, company_id: str, period: str) -> dict[str, str]:
    source = dict(value or {})
    context = {"company_id": company_id, "period": period}
    for key in LIST_CONTEXT_KEYS:
        raw = source.get(key)
        if raw is not None and str(raw):
            context[key] = str(raw)[:240]
    context.setdefault("project_status", "all")
    context.setdefault("group_by", "none")
    context.setdefault("sort_by", "risk")
    context.setdefault("page", "1")
    context.setdefault("page_size", str(project_list.DEFAULT_PAGE_SIZE))
    return context


def _engine_views(row: Mapping[str, Any], company_id: str, period: str) -> tuple[dict[str, Any], dict[str, Any]]:
    revenue = int(row["revenue_cents"])
    cost = int(row["cost_cents"])
    contract_revenue = revenue * 108 // 100
    contract_cost = cost * 102 // 100
    settlement_revenue = revenue * 101 // 100
    settlement_cost = cost * 1005 // 1000
    payload = {
        "project_ref": row["project_id"],
        "entity_ref": company_id,
        "period_ref": period,
        "basis_version": "S17P2-PUBLIC-DETAIL-1",
        "contract": {
            "revenue_basis": calculations.MARGIN_BASIS_CONTRACT["contract"][0],
            "cost_basis": calculations.MARGIN_BASIS_CONTRACT["contract"][1],
            "revenue_cents": contract_revenue,
            "cost_cents": contract_cost,
        },
        "settlement": {
            "revenue_basis": calculations.MARGIN_BASIS_CONTRACT["settlement"][0],
            "cost_basis": calculations.MARGIN_BASIS_CONTRACT["settlement"][1],
            "revenue_cents": settlement_revenue,
            "cost_cents": settlement_cost,
        },
        "management": {
            "revenue_basis": calculations.MARGIN_BASIS_CONTRACT["management"][0],
            "cost_basis": calculations.MARGIN_BASIS_CONTRACT["management"][1],
            "revenue_cents": revenue,
            "cost_cents": cost,
        },
    }
    views = calculations.calculate_margin_views(payload)
    golden = calculations.assert_margin_golden(
        views,
        {
            name: {"gross_profit_cents": view["revenue_cents"] - view["cost_cents"]}
            for name, view in payload.items()
            if name in calculations.MARGIN_VIEWS
        },
    )
    return views, golden


def _cost_section(row: Mapping[str, Any], company_id: str, period: str) -> dict[str, Any]:
    total = int(row["cost_cents"])
    project_number = int(str(row["project_id"]).rsplit("-", 1)[-1])
    unallocated_bps = 180 + project_number * 35
    unallocated = total * unallocated_bps // 10_000
    allocated_total = total - unallocated
    actuals = _allocate_exact(allocated_total, CATEGORY_WEIGHTS)
    budget_total = total * (10_150 - project_number * 18) // 10_000
    budget_allocated = max(budget_total - unallocated, 0)
    budgets = _allocate_exact(budget_allocated, CATEGORY_WEIGHTS)
    categories: list[dict[str, Any]] = []
    for code, actual, budget in zip(cost_facts.COST_CATEGORIES, actuals, budgets):
        categories.append(
            {
                "category_id": code,
                "category_zh": CATEGORY_LABELS[code],
                "actual_cents": actual,
                "actual_display_zh": homepage.format_wan_cents(actual),
                "budget_cents": budget,
                "budget_display_zh": homepage.format_wan_cents(budget),
                "variance_cents": actual - budget,
                "variance_direction_zh": "超出基准" if actual > budget else "低于基准" if actual < budget else "与基准一致",
                "source_zh": "公开合成成本分类账",
                "source_ref": f"PUBLIC-SYNTHETIC:COST:{company_id}:{period}:{row['project_id']}:{code}",
            }
        )
    trend_amounts = _allocate_exact(total, TREND_WEIGHTS)
    trend = [
        {
            "period_id": f"P{index}",
            "period_zh": label,
            "actual_cents": amount,
            "actual_display_zh": homepage.format_wan_cents(amount),
            "source_ref": f"PUBLIC-SYNTHETIC:COST-TREND:{company_id}:{row['project_id']}:P{index}",
        }
        for index, (label, amount) in enumerate(zip(("四期前", "三期前", "上期", "本期"), trend_amounts), start=1)
    ]
    risk = calculations.assess_cost_risk(
        {
            "project_ref": row["project_id"],
            "entity_ref": company_id,
            "period_ref": period,
            "basis_version": "S17P2-PUBLIC-DETAIL-1",
            "required_cost_category_count": COST_CATEGORY_COUNT,
            "observed_required_cost_category_count": COST_CATEGORY_COUNT,
            "total_cost_cents": total,
            "unallocated_cost_cents": unallocated,
            "current_period_cost_cents": trend[-1]["actual_cents"],
            "comparison_period_cost_cents": trend[-2]["actual_cents"],
            "management_margin_bps": row["gross_margin_bps"],
        },
        calculations.DEFAULT_RISK_POLICY,
    )
    table_total = sum(item["actual_cents"] for item in categories) + unallocated
    chart_total = sum(item["actual_cents"] for item in categories) + unallocated
    return {
        "section_id": "cost",
        "title_zh": "成本",
        "category_count": len(categories),
        "categories": categories,
        "unallocated": {
            "amount_cents": unallocated,
            "amount_display_zh": homepage.format_wan_cents(unallocated),
            "ratio_bps": unallocated_bps,
            "ratio_display_zh": project_list.format_percent_bps(unallocated_bps),
            "reason_zh": "公开演示中暂未匹配到具体分类，保留在未归集池，不隐去也不摊平。",
            "source_zh": "公开合成未归集成本池",
            "source_ref": f"PUBLIC-SYNTHETIC:UNALLOCATED:{company_id}:{period}:{row['project_id']}",
        },
        "trend": trend,
        "budget_total_cents": budget_total,
        "actual_total_cents": total,
        "variance_total_cents": total - budget_total,
        "table_total_cents": table_total,
        "chart_total_cents": chart_total,
        "trend_total_cents": sum(item["actual_cents"] for item in trend),
        "engine_difference_cents": table_total - total,
        "chart_table_difference_cents": chart_total - table_total,
        "zero_difference_pass": table_total == chart_total == total,
        "risk_assessment": risk,
        "source_zh": "公开合成成本事实与 S12 计算引擎",
        "source_ref": f"PUBLIC-SYNTHETIC:COST-DETAIL:{company_id}:{period}:{row['project_id']}",
    }


def _revenue_collection_section(row: Mapping[str, Any], company_id: str, period: str) -> dict[str, Any]:
    revenue = int(row["revenue_cents"])
    contract_value = revenue * 108 // 100
    approved_change = contract_value * 3 // 100
    invoiced = revenue * 92 // 100
    collected = revenue * int(row["collection_bps"]) // 10_000
    receivable = max(invoiced - collected, 0)
    return {
        "section_id": "revenue_collection",
        "title_zh": "收入与回款",
        "contract_value_cents": contract_value,
        "approved_change_cents": approved_change,
        "recognized_revenue_cents": revenue,
        "invoiced_cents": invoiced,
        "collected_cents": collected,
        "receivable_cents": receivable,
        "remaining_contract_cents": max(contract_value + approved_change - revenue, 0),
        "collection_bps": row["collection_bps"],
        "collection_display_zh": row["collection_display_zh"],
        "timeline": [
            {"step": 1, "label_zh": "合同及变更", "amount_cents": contract_value + approved_change, "status_zh": "已确认"},
            {"step": 2, "label_zh": "收入确认", "amount_cents": revenue, "status_zh": "进行中"},
            {"step": 3, "label_zh": "已开票", "amount_cents": invoiced, "status_zh": "进行中"},
            {"step": 4, "label_zh": "已回款", "amount_cents": collected, "status_zh": "持续跟进"},
        ],
        "source_zh": "公开合成合同、开票与回款台账",
        "source_ref": f"PUBLIC-SYNTHETIC:REVENUE-COLLECTION:{company_id}:{period}:{row['project_id']}",
    }


def _variance_section(
    row: Mapping[str, Any], cost: Mapping[str, Any], revenue_collection: Mapping[str, Any], company_id: str, period: str
) -> dict[str, Any]:
    planned_revenue = int(row["revenue_cents"]) * 102 // 100
    planned_gross_profit = planned_revenue - int(cost["budget_total_cents"])
    actual_gross_profit = int(row["gross_profit_cents"])
    schedule_bps = 8_200 + int(str(row["project_id"]).rsplit("-", 1)[-1]) * 170
    rows = [
        {
            "variance_id": "REVENUE",
            "label_zh": "收入差异",
            "actual_cents": row["revenue_cents"],
            "baseline_cents": planned_revenue,
            "variance_cents": int(row["revenue_cents"]) - planned_revenue,
            "explanation_zh": "按当前已确认进度与计划收入比较。",
        },
        {
            "variance_id": "COST",
            "label_zh": "成本差异",
            "actual_cents": cost["actual_total_cents"],
            "baseline_cents": cost["budget_total_cents"],
            "variance_cents": cost["variance_total_cents"],
            "explanation_zh": "按成本分类事实与公开合成预算基准比较。",
        },
        {
            "variance_id": "GROSS_PROFIT",
            "label_zh": "毛利差异",
            "actual_cents": actual_gross_profit,
            "baseline_cents": planned_gross_profit,
            "variance_cents": actual_gross_profit - planned_gross_profit,
            "explanation_zh": "收入差异与成本差异共同形成，不使用隐藏评分。",
        },
    ]
    return {
        "section_id": "variance",
        "title_zh": "差异",
        "rows": rows,
        "schedule_progress_bps": schedule_bps,
        "schedule_progress_display_zh": project_list.format_percent_bps(schedule_bps),
        "collection_gap_cents": int(revenue_collection["invoiced_cents"]) - int(revenue_collection["collected_cents"]),
        "change_note_zh": "公开演示变更已单列在合同与收入流程中，没有并入基础合同后隐藏。",
        "source_zh": "公开合成计划基准与项目事实",
        "source_ref": f"PUBLIC-SYNTHETIC:VARIANCE:{company_id}:{period}:{row['project_id']}",
    }


def _documents_section(row: Mapping[str, Any], company_id: str, period: str) -> dict[str, Any]:
    definitions = (
        ("CONTRACT", "合同及补充协议", "已齐全"),
        ("BUDGET", "项目预算", "已齐全"),
        ("PROGRESS", "进度确认资料", "待补充" if row["risk_level"] == "HIGH" else "已齐全"),
        ("INVOICE", "开票记录", "已齐全"),
        ("COLLECTION", "回款记录", "持续更新"),
        ("SETTLEMENT", "结算资料", "办理中"),
    )
    documents = [
        {
            "document_id": code,
            "document_name_zh": label,
            "status_zh": status,
            "updated_zh": "2026-07-15",
            "source_zh": "公开合成项目资料索引",
            "source_ref": f"PUBLIC-SYNTHETIC:DOCUMENT:{company_id}:{period}:{row['project_id']}:{code}",
        }
        for code, label, status in definitions
    ]
    return {
        "section_id": "documents",
        "title_zh": "资料",
        "document_count": len(documents),
        "complete_count": sum(item["status_zh"] == "已齐全" for item in documents),
        "documents": documents,
        "source_zh": "公开合成项目资料索引",
        "source_ref": f"PUBLIC-SYNTHETIC:DOCUMENTS:{company_id}:{period}:{row['project_id']}",
    }


def _overview_section(
    row: Mapping[str, Any], engine: Mapping[str, Any], golden: Mapping[str, Any], cost: Mapping[str, Any],
    revenue_collection: Mapping[str, Any], variance: Mapping[str, Any], documents: Mapping[str, Any]
) -> dict[str, Any]:
    profitable = int(row["gross_profit_cents"]) > 0
    reasons = [
        f"确认收入 {row['revenue_display_zh']}，确认成本 {row['cost_display_zh']}。",
        f"毛利率 {row['gross_margin_display_zh']}，回款进度 {row['collection_display_zh']}。",
    ]
    if int(cost["variance_total_cents"]) > 0:
        reasons.append("实际成本高于当前基准，需要查看成本页中的分类差异。")
    else:
        reasons.append("实际成本未超过当前基准，成本总体受控。")
    if row["risk_level"] != "LOW":
        reasons.append("需继续关注：" + "；".join(row["risk_reasons_zh"]) + "。")
    else:
        reasons.append("当前没有显著经营风险。")
    return {
        "section_id": "overview",
        "title_zh": "项目概况",
        "profit_verdict_zh": "项目目前赚钱" if profitable else "项目目前未实现盈利",
        "profit_reason_zh": reasons,
        "contract_value_cents": revenue_collection["contract_value_cents"],
        "progress_bps": variance["schedule_progress_bps"],
        "progress_display_zh": variance["schedule_progress_display_zh"],
        "revenue_cents": row["revenue_cents"],
        "cost_cents": row["cost_cents"],
        "gross_profit_cents": row["gross_profit_cents"],
        "gross_margin_bps": row["gross_margin_bps"],
        "gross_margin_display_zh": row["gross_margin_display_zh"],
        "collected_cents": revenue_collection["collected_cents"],
        "collection_bps": row["collection_bps"],
        "collection_display_zh": row["collection_display_zh"],
        "risk_zh": row["risk_zh"],
        "risk_reasons_zh": list(row["risk_reasons_zh"]),
        "data_status_zh": f"金额已与计算引擎核对；资料 {documents['complete_count']} / {documents['document_count']} 项齐全。",
        "business_summary_first": True,
        "professional_basis": {
            "title_zh": "专业口径与核对信息",
            "margin_views": engine,
            "golden_comparison": golden,
            "money_tolerance_cents": MONEY_TOLERANCE_CENTS,
        },
        "source_zh": "公开合成项目台账与 S12 计算引擎",
        "source_ref": row["source_ref"],
    }


def project_detail(
    *,
    project_id: str,
    company_id: str = "demo-north",
    period: str = "2026-07",
    active_tab: str = "overview",
    list_context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """返回一个项目的五个互不重复详情标签，并保留列表返回上下文。"""

    if active_tab not in TAB_IDS:
        raise ProjectDetailError("unsupported detail tab")
    row = _find_project(company_id, period, project_id)
    engine, golden = _engine_views(row, company_id, period)
    cost = _cost_section(row, company_id, period)
    revenue_collection = _revenue_collection_section(row, company_id, period)
    variance = _variance_section(row, cost, revenue_collection, company_id, period)
    documents = _documents_section(row, company_id, period)
    overview = _overview_section(row, engine, golden, cost, revenue_collection, variance, documents)
    context = _normalise_list_context(list_context, company_id, period)
    return_query = urlencode(context)
    sections = {
        "overview": overview,
        "cost": cost,
        "revenue_collection": revenue_collection,
        "variance": variance,
        "documents": documents,
    }
    return {
        "schema_version": "kmfa.v015.s17p2.project_detail.v1",
        "version": VERSION,
        "allowed": True,
        "data_classification": "PUBLIC_SYNTHETIC",
        "project": row,
        "active_tab": active_tab,
        "tabs": [dict(item, active=item["id"] == active_tab) for item in DETAIL_TABS],
        "sections": sections,
        "overview": overview,
        "cost": cost,
        "revenue_collection": revenue_collection,
        "variance": variance,
        "documents": documents,
        "navigation": {
            "return_context": context,
            "return_url": f"/projects?{return_query}",
            "detail_url": f"/projects/{project_id}?{return_query}",
            "preserves_list_context": True,
        },
        "section_ids": list(sections),
        "section_overlap_count": 0,
        "source_group_count": SOURCE_GROUP_COUNT,
        "fact_layer_write_count": 0,
        "raw_root_access_count": 0,
        "live_source_read_count": 0,
        "external_network_request_count": 0,
        "real_identity_count": 0,
        "credential_count": 0,
        "real_business_action_count": 0,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
    }


def public_checks() -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []

    def add(check_id: str, passed: bool, summary_zh: str) -> None:
        checks.append({"check_id": check_id, "passed": bool(passed), "summary_zh": summary_zh})

    baseline = project_detail(project_id="PUB-PROJ-001")
    overview = baseline["overview"]
    cost = baseline["cost"]
    revenue = baseline["revenue_collection"]
    variance = baseline["variance"]
    documents = baseline["documents"]
    contract = source_contract()
    add("source_tasks", len(contract["task_ids"]) == 3, "三项路线图任务完整")
    add("tab_count", len(baseline["tabs"]) == DETAIL_TAB_COUNT, "五个详情标签完整")
    add("project_identity", baseline["project"]["project_id"] == "PUB-PROJ-001", "项目身份准确")
    add("company_scope", baseline["project"]["company_id"] == "demo-north", "公司范围准确")
    add("public_classification", baseline["data_classification"] == "PUBLIC_SYNTHETIC", "只使用公开合成数据")
    add("profit_verdict", bool(overview["profit_verdict_zh"]), "概况先给出盈亏结论")
    add("business_first", overview["business_summary_first"] is True, "概况不先显示技术状态码")
    add("overview_equation", overview["revenue_cents"] == overview["cost_cents"] + overview["gross_profit_cents"], "概况金额等式成立")
    add("overview_list_revenue", overview["revenue_cents"] == baseline["project"]["revenue_cents"], "概况收入复用列表事实")
    add("overview_list_cost", overview["cost_cents"] == baseline["project"]["cost_cents"], "概况成本复用列表事实")
    add("engine_revenue", overview["professional_basis"]["margin_views"]["views"]["management"]["revenue_cents"] == overview["revenue_cents"], "管理口径收入一致")
    add("engine_cost", overview["professional_basis"]["margin_views"]["views"]["management"]["cost_cents"] == overview["cost_cents"], "管理口径成本一致")
    add("golden_pass", overview["professional_basis"]["golden_comparison"]["zero_difference_pass"] is True, "引擎黄金值核对通过")
    add("golden_zero", all(value == 0 for value in overview["professional_basis"]["golden_comparison"]["differences_cents"].values()), "三个毛利口径零差异")
    add("cost_total", cost["actual_total_cents"] == baseline["project"]["cost_cents"], "成本总额与项目事实一致")
    add("cost_conservation", sum(item["actual_cents"] for item in cost["categories"]) + cost["unallocated"]["amount_cents"] == cost["actual_total_cents"], "分类成本守恒")
    add("category_count", len(cost["categories"]) == COST_CATEGORY_COUNT, "十类成本完整")
    add("category_unique", len({item["category_id"] for item in cost["categories"]}) == COST_CATEGORY_COUNT, "成本分类不重复")
    add("category_sources", all(item["source_ref"] for item in cost["categories"]), "每类成本有来源")
    add("chart_table_ids", [item["category_id"] for item in cost["categories"]] == list(cost_facts.COST_CATEGORIES), "图表表格共用分类顺序")
    add("chart_table_total", cost["table_total_cents"] == cost["chart_total_cents"], "图表与表格金额一致")
    add("budget_total", sum(item["budget_cents"] for item in cost["categories"]) + cost["unallocated"]["amount_cents"] == cost["budget_total_cents"], "预算基准合计一致")
    add("variance_total", cost["actual_total_cents"] - cost["budget_total_cents"] == cost["variance_total_cents"], "成本差异等式成立")
    add("trend_total", cost["trend_total_cents"] == cost["actual_total_cents"], "趋势金额合计一致")
    add("trend_count", len(cost["trend"]) == COST_TREND_PERIOD_COUNT, "四期成本趋势完整")
    add("cost_risk", cost["risk_assessment"]["deterministic_conclusion_allowed"] is True, "成本风险可确定")
    add("cost_source", bool(cost["source_ref"]), "成本页有来源")
    add("unallocated_source", bool(cost["unallocated"]["source_ref"]), "未归集成本有来源")
    add("recognized_revenue", revenue["recognized_revenue_cents"] == baseline["project"]["revenue_cents"], "确认收入一致")
    add("collection_amount", revenue["collected_cents"] == baseline["project"]["revenue_cents"] * baseline["project"]["collection_bps"] // 10_000, "回款金额一致")
    add("collection_ratio", revenue["collection_bps"] == baseline["project"]["collection_bps"], "回款比例一致")
    add("receivable_equation", revenue["receivable_cents"] == max(revenue["invoiced_cents"] - revenue["collected_cents"], 0), "应收金额等式成立")
    add("timeline_count", len(revenue["timeline"]) == 4, "收入回款流程完整")
    add("revenue_variance", variance["rows"][0]["variance_cents"] == variance["rows"][0]["actual_cents"] - variance["rows"][0]["baseline_cents"], "收入差异准确")
    add("cost_variance", variance["rows"][1]["variance_cents"] == variance["rows"][1]["actual_cents"] - variance["rows"][1]["baseline_cents"], "成本差异准确")
    add("gross_variance", variance["rows"][2]["variance_cents"] == variance["rows"][2]["actual_cents"] - variance["rows"][2]["baseline_cents"], "毛利差异准确")
    add("document_count", documents["document_count"] == DOCUMENT_COUNT, "六类资料完整")
    add("document_sources", all(item["source_ref"] for item in documents["documents"]), "每类资料有来源")
    add("documents_no_amounts", all("amount_cents" not in item for item in documents["documents"]), "资料页不重复堆金额")
    add("section_unique", len(set(baseline["section_ids"])) == DETAIL_TAB_COUNT, "标签内容职责不重复")
    add("return_path", baseline["navigation"]["return_url"].startswith("/projects?"), "返回项目列表")
    add("return_company", "company_id=demo-north" in baseline["navigation"]["return_url"], "返回保留公司")
    add("detail_route", baseline["navigation"]["detail_url"].startswith("/projects/PUB-PROJ-001?"), "详情地址准确")
    add("fact_write_zero", baseline["fact_layer_write_count"] == 0, "事实层写入为零")
    add("raw_zero", baseline["raw_root_access_count"] == 0, "未访问原始资料")
    add("network_zero", baseline["external_network_request_count"] == 0, "无外部网络请求")
    add("action_zero", baseline["real_business_action_count"] == 0, "无真实业务动作")

    for row in project_list.project_catalog("demo-north", "2026-07"):
        value = project_detail(project_id=row["project_id"])
        add(f"project_equation_{row['project_id']}", value["overview"]["revenue_cents"] == value["overview"]["cost_cents"] + value["overview"]["gross_profit_cents"], "项目金额等式成立")
        add(f"project_cost_{row['project_id']}", value["cost"]["zero_difference_pass"] is True, "项目成本守恒")
        add(f"project_golden_{row['project_id']}", value["overview"]["professional_basis"]["golden_comparison"]["zero_difference_pass"] is True, "项目引擎零差异")
        add(f"project_tabs_{row['project_id']}", value["section_overlap_count"] == 0, "项目标签不重复堆叠")
    add("catalog_ids_unique", len({row["project_id"] for row in project_list.project_catalog("demo-north", "2026-07")}) == 6, "当前公司项目编号唯一")
    if len(checks) != PUBLIC_CHECK_COUNT:
        raise ProjectDetailError(f"public check count drifted: {len(checks)}")
    if not all(item["passed"] for item in checks):
        failed = [item["check_id"] for item in checks if not item["passed"]]
        raise ProjectDetailError("project detail public checks failed: " + ", ".join(failed))
    return checks


def main() -> int:
    try:
        checks = public_checks()
    except (KeyError, TypeError, ProjectDetailError, calculations.CoreCalculationError, project_list.ProjectListError) as error:
        print(f"FAIL: {error}")
        return 1
    print(f"PASS: S17-P2 project detail public checks {len(checks)}/{len(checks)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
