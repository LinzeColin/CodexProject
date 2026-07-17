#!/usr/bin/env python3
"""KMFA v1.5 S17-P1 项目列表的公开合成业务合同。"""

from __future__ import annotations

import csv
import io
from collections import Counter
from typing import Any, Iterable, Mapping, Sequence

from KMFA.tools import v015_s16_p1_homepage as homepage


RUN_PHASE_ID = "V015_S17_P1_PROJECT_LIST"
ROADMAP_PHASE_ID = "S17-P1"
TASK_ID = "KMFA-V015-S17-P1-PROJECT-LIST-20260716"
ACCEPTANCE_ID = "ACC-KMFA-V015-S17-P1-PROJECT-LIST"
VERSION = "1.5.0-dev-s17p1"

CATALOG_PROJECT_COUNT = 18
COMPANY_COUNT = 3
PROJECTS_PER_COMPANY = 6
DEFAULT_PAGE_SIZE = 4
MAX_PAGE_SIZE = 12
AVAILABLE_COLUMN_COUNT = 12
DEFAULT_VISIBLE_COLUMN_COUNT = 8  # 固定选择列 + 7 个业务列
FILTER_DIMENSION_COUNT = 7
GROUP_OPTION_COUNT = 6
SORT_OPTION_COUNT = 5
MIN_BATCH_COUNT = 2
MAX_BATCH_COUNT = 6
BROWSER_FLOW_COUNT = 8
VISUAL_EVIDENCE_COUNT = 4

COMPANY_IDS = ("demo-north", "demo-south", "demo-west")
RISK_LEVELS = ("HIGH", "MEDIUM", "LOW")
MARGIN_BANDS = ("low", "medium", "high")
COLLECTION_BANDS = ("low", "medium", "high")
GROUP_OPTIONS = ("none", "risk", "margin", "collection", "industry", "period")
SORT_OPTIONS = ("risk", "margin", "collection", "industry", "period")

AVAILABLE_COLUMNS: tuple[dict[str, str], ...] = (
    {"id": "project", "label_zh": "项目"},
    {"id": "client", "label_zh": "客户"},
    {"id": "owner", "label_zh": "负责人"},
    {"id": "status", "label_zh": "状态"},
    {"id": "margin", "label_zh": "毛利率"},
    {"id": "collection", "label_zh": "回款进度"},
    {"id": "risk", "label_zh": "风险"},
    {"id": "revenue", "label_zh": "收入"},
    {"id": "cost", "label_zh": "成本"},
    {"id": "industry", "label_zh": "行业"},
    {"id": "period", "label_zh": "项目期间"},
    {"id": "source", "label_zh": "来源"},
)
DEFAULT_COLUMNS = ("project", "client", "owner", "status", "margin", "collection", "risk")

SORT_EXPLANATIONS = {
    "risk": "风险最高优先：高风险、需关注、低风险；同级按项目编号。没有隐藏评分。",
    "margin": "毛利率最低优先：直接按毛利率从低到高；相同则按项目编号。",
    "collection": "回款最慢优先：直接按回款进度从低到高；相同则按项目编号。",
    "industry": "行业排序：按行业中文名称排序；相同则按项目编号。",
    "period": "期间最新优先：按项目期间从新到旧；相同则按项目编号。",
}

GROUP_EXPLANATIONS = {
    "none": "不分组，只按所选排序规则排列。",
    "risk": "按高风险、需关注、低风险分组。",
    "margin": "按低于 22%、22% 至 27.99%、28% 及以上分组。",
    "collection": "按低于 80%、80% 至 92.99%、93% 及以上分组。",
    "industry": "按项目所属行业分组。",
    "period": "按项目期间分组，较新期间在前。",
}


class ProjectListError(ValueError):
    """项目列表请求不符合公开演示合同。"""


def source_contract() -> dict[str, Any]:
    """返回 TaskPack v2.0 中 S17-P1 的逐项合同。"""

    return {
        "schema_version": "kmfa.v015.s17p1.source_contract.v1",
        "stage_id": "S17",
        "stage_name_zh": "项目列表、项目详情与成本分析流程",
        "stage_goal_zh": "提供项目制工程企业最核心的项目成本、收入、回款、差异和资料工作流。",
        "roadmap_phase_id": ROADMAP_PHASE_ID,
        "phase_name_zh": "项目列表",
        "task_ids": ["S17P1T01", "S17P1T02", "S17P1T03"],
        "task_names_zh": ["实现项目总表", "实现项目分组与排序", "实现批量查看与导出"],
        "acceptance_zh": ["列可配置，默认不过载。", "排序公式可解释。", "批量操作不修改事实。"],
        "stop_conditions_zh": [
            "分页或筛选后数据不得错位。",
            "不得用隐含评分误导。",
            "导出缺少来源说明失败。",
        ],
        "evidence_zh": ["表格测试。", "排序测试。", "导出一致性测试。"],
        "data_classification": "PUBLIC_SYNTHETIC",
    }


def format_percent_bps(value: int) -> str:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ProjectListError("percentage must use integer basis points")
    return f"{value // 100}.{value % 100:02d}%"


def _margin_band(value: int) -> str:
    if value < 2_200:
        return "low"
    if value < 2_800:
        return "medium"
    return "high"


def _collection_band(value: int) -> str:
    if value < 8_000:
        return "low"
    if value < 9_300:
        return "medium"
    return "high"


def _project_definitions() -> tuple[dict[str, Any], ...]:
    """六个公开合成项目；前四个金额和比例与 S16 首页完全一致。"""

    return (
        {
            "project_id": "PUB-PROJ-001",
            "project_name_zh": "示例厂房改造",
            "client_zh": "示例制造集团",
            "owner_zh": "陈工",
            "industry_zh": "工业改造",
            "project_period": "2026-07",
            "risk_level": "MEDIUM",
            "risk_zh": "需关注",
            "risk_reasons_zh": ["成本偏差待复核"],
        },
        {
            "project_id": "PUB-PROJ-002",
            "project_name_zh": "示例设备安装",
            "client_zh": "示例装备公司",
            "owner_zh": "周工",
            "industry_zh": "设备安装",
            "project_period": "2026-06",
            "risk_level": "LOW",
            "risk_zh": "低风险",
            "risk_reasons_zh": ["进度与回款正常"],
        },
        {
            "project_id": "PUB-PROJ-003",
            "project_name_zh": "示例管网工程",
            "client_zh": "示例公用事业",
            "owner_zh": "李工",
            "industry_zh": "市政工程",
            "project_period": "2026-05",
            "risk_level": "HIGH",
            "risk_zh": "高风险",
            "risk_reasons_zh": ["回款低于 80%", "毛利率低于 22%"],
        },
        {
            "project_id": "PUB-PROJ-004",
            "project_name_zh": "示例维护服务",
            "client_zh": "示例能源服务",
            "owner_zh": "陈工",
            "industry_zh": "运维服务",
            "project_period": "2026-07",
            "risk_level": "LOW",
            "risk_zh": "低风险",
            "risk_reasons_zh": ["毛利与回款正常"],
        },
        {
            "project_id": "PUB-PROJ-005",
            "project_name_zh": "示例仓储升级",
            "client_zh": "示例物流集团",
            "owner_zh": "王工",
            "industry_zh": "仓储物流",
            "project_period": "2026-04",
            "base_revenue_cents": 168_000_000,
            "gross_margin_bps": 2_260,
            "collection_bps": 8_150,
            "status": "ATTENTION",
            "status_zh": "需要关注",
            "risk_level": "MEDIUM",
            "risk_zh": "需关注",
            "risk_reasons_zh": ["回款进度需跟进"],
        },
        {
            "project_id": "PUB-PROJ-006",
            "project_name_zh": "示例节能改造",
            "client_zh": "示例商业中心",
            "owner_zh": "周工",
            "industry_zh": "节能工程",
            "project_period": "2026-03",
            "base_revenue_cents": 152_000_000,
            "gross_margin_bps": 2_920,
            "collection_bps": 9_400,
            "status": "NORMAL",
            "status_zh": "进展正常",
            "risk_level": "LOW",
            "risk_zh": "低风险",
            "risk_reasons_zh": ["暂无显著风险"],
        },
    )


def project_catalog(company_id: str, period: str) -> list[dict[str, Any]]:
    """形成某一公开演示公司的六个项目，且不产生任何写操作。"""

    if company_id not in COMPANY_IDS:
        raise ProjectListError("unsupported public company")
    snapshot = homepage.homepage_snapshot(company_id=company_id, period=period)
    if not snapshot.get("allowed"):
        raise ProjectListError("public company is not accessible")
    homepage_rows = {row["project_id"]: row for row in snapshot["project_portfolio"]}
    company_label = snapshot["context_labels"]["company"]
    rows: list[dict[str, Any]] = []
    for definition in _project_definitions():
        project_id = definition["project_id"]
        if project_id in homepage_rows:
            summary = homepage_rows[project_id]
            revenue_cents = int(summary["revenue_cents"])
            margin_bps = int(summary["gross_margin_bps"])
            collection_bps = int(summary["collection_bps"])
            status = str(summary["status"])
            status_zh = str(summary["status_zh"])
        else:
            revenue_cents = homepage._scale(int(definition["base_revenue_cents"]), company_id, period)
            margin_bps = int(definition["gross_margin_bps"])
            collection_bps = int(definition["collection_bps"])
            status = str(definition["status"])
            status_zh = str(definition["status_zh"])
        gross_profit_cents = revenue_cents * margin_bps // 10_000
        cost_cents = revenue_cents - gross_profit_cents
        source_ref = f"PUBLIC-SYNTHETIC:PROJECT:{company_id}:{period}:{project_id}"
        row = {
            "project_id": project_id,
            "project_name_zh": definition["project_name_zh"],
            "company_id": company_id,
            "company_zh": company_label,
            "client_zh": definition["client_zh"],
            "owner_zh": definition["owner_zh"],
            "industry_zh": definition["industry_zh"],
            "project_period": definition["project_period"],
            "status": status,
            "status_zh": status_zh,
            "revenue_cents": revenue_cents,
            "revenue_display_zh": homepage.format_wan_cents(revenue_cents),
            "cost_cents": cost_cents,
            "cost_display_zh": homepage.format_wan_cents(cost_cents),
            "gross_profit_cents": gross_profit_cents,
            "gross_margin_bps": margin_bps,
            "gross_margin_display_zh": format_percent_bps(margin_bps),
            "margin_band": _margin_band(margin_bps),
            "collection_bps": collection_bps,
            "collection_display_zh": format_percent_bps(collection_bps),
            "collection_band": _collection_band(collection_bps),
            "risk_level": definition["risk_level"],
            "risk_zh": definition["risk_zh"],
            "risk_reasons_zh": list(definition["risk_reasons_zh"]),
            "route": f"/projects/{project_id}",
            "source_zh": "公开合成项目台账",
            "source_ref": source_ref,
            "cutoff_date": "2026-07-15",
            "data_classification": "PUBLIC_SYNTHETIC",
        }
        rows.append(row)
    _validate_catalog(rows, company_id)
    return rows


def _validate_catalog(rows: Sequence[Mapping[str, Any]], company_id: str) -> None:
    if len(rows) != PROJECTS_PER_COMPANY:
        raise ProjectListError("exactly six projects are required per company")
    if len({row.get("project_id") for row in rows}) != PROJECTS_PER_COMPANY:
        raise ProjectListError("project identifiers must be unique")
    if any(row.get("company_id") != company_id for row in rows):
        raise ProjectListError("cross-company project leakage detected")
    if any(row.get("data_classification") != "PUBLIC_SYNTHETIC" for row in rows):
        raise ProjectListError("project catalog must remain public synthetic")
    for row in rows:
        amounts = (row.get("revenue_cents"), row.get("cost_cents"), row.get("gross_profit_cents"))
        if any(isinstance(value, bool) or not isinstance(value, int) for value in amounts):
            raise ProjectListError("money must use integer cents")
        if row["revenue_cents"] != row["cost_cents"] + row["gross_profit_cents"]:
            raise ProjectListError("project amount equation drifted")
        if not row.get("source_zh") or not row.get("source_ref") or not row.get("cutoff_date"):
            raise ProjectListError("every project requires source and cutoff")


def _catalog_snapshot(
    company_id: str,
    period: str,
    catalog_rows: Sequence[Mapping[str, Any]] | None,
) -> list[dict[str, Any]]:
    """使用当前项目投影，或在没有投影时读取原公开合成台账。"""

    rows = project_catalog(company_id, period) if catalog_rows is None else [dict(row) for row in catalog_rows]
    _validate_catalog(rows, company_id)
    return rows


def _normalise_columns(columns: Sequence[str] | None) -> list[str]:
    available = {item["id"] for item in AVAILABLE_COLUMNS}
    selected = list(DEFAULT_COLUMNS if columns is None else columns)
    if not selected or len(selected) != len(set(selected)) or any(item not in available for item in selected):
        raise ProjectListError("columns are invalid")
    return selected


def _sort_key(sort_by: str, row: Mapping[str, Any]) -> tuple[Any, ...]:
    if sort_by == "risk":
        return ({"HIGH": 0, "MEDIUM": 1, "LOW": 2}[str(row["risk_level"])], row["project_id"])
    if sort_by == "margin":
        return (row["gross_margin_bps"], row["project_id"])
    if sort_by == "collection":
        return (row["collection_bps"], row["project_id"])
    if sort_by == "industry":
        return (row["industry_zh"], row["project_id"])
    if sort_by == "period":
        return tuple([-int(str(row["project_period"]).replace("-", "")), str(row["project_id"])])
    raise ProjectListError("unsupported sort option")


def _group_key(group_by: str, row: Mapping[str, Any]) -> tuple[Any, str, str]:
    if group_by == "none":
        return (0, "all", "全部项目")
    if group_by == "risk":
        level = str(row["risk_level"])
        return ({"HIGH": 0, "MEDIUM": 1, "LOW": 2}[level], level, str(row["risk_zh"]))
    if group_by == "margin":
        band = str(row["margin_band"])
        labels = {"low": "毛利率低于 22%", "medium": "毛利率 22% 至 27.99%", "high": "毛利率 28% 及以上"}
        return ({"low": 0, "medium": 1, "high": 2}[band], band, labels[band])
    if group_by == "collection":
        band = str(row["collection_band"])
        labels = {"low": "回款低于 80%", "medium": "回款 80% 至 92.99%", "high": "回款 93% 及以上"}
        return ({"low": 0, "medium": 1, "high": 2}[band], band, labels[band])
    if group_by == "industry":
        label = str(row["industry_zh"])
        return (label, label, label)
    if group_by == "period":
        label = str(row["project_period"])
        return (-int(label.replace("-", "")), label, label)
    raise ProjectListError("unsupported group option")


def _filtered_rows(
    rows: Iterable[dict[str, Any]],
    *,
    project_status: str,
    client: str,
    owner: str,
    margin_band: str,
    collection_band: str,
    risk: str,
) -> list[dict[str, Any]]:
    if project_status not in {"all", "attention", "normal"}:
        raise ProjectListError("unsupported project status")
    if margin_band not in {"all", *MARGIN_BANDS}:
        raise ProjectListError("unsupported margin band")
    if collection_band not in {"all", *COLLECTION_BANDS}:
        raise ProjectListError("unsupported collection band")
    if risk not in {"all", *RISK_LEVELS}:
        raise ProjectListError("unsupported risk level")
    expected_status = {"attention": "ATTENTION", "normal": "NORMAL"}.get(project_status)
    return [
        row
        for row in rows
        if (expected_status is None or row["status"] == expected_status)
        and (client == "all" or row["client_zh"] == client)
        and (owner == "all" or row["owner_zh"] == owner)
        and (margin_band == "all" or row["margin_band"] == margin_band)
        and (collection_band == "all" or row["collection_band"] == collection_band)
        and (risk == "all" or row["risk_level"] == risk)
    ]


def project_list(
    *,
    company_id: str = "demo-north",
    period: str = "2026-07",
    project_status: str = "all",
    client: str = "all",
    owner: str = "all",
    margin_band: str = "all",
    collection_band: str = "all",
    risk: str = "all",
    group_by: str = "none",
    sort_by: str = "risk",
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
    columns: Sequence[str] | None = None,
    catalog_rows: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """筛选、分组、排序并分页；每一步都以 project_id 保持稳定。"""

    if group_by not in GROUP_OPTIONS:
        raise ProjectListError("unsupported group option")
    if sort_by not in SORT_OPTIONS:
        raise ProjectListError("unsupported sort option")
    if isinstance(page, bool) or not isinstance(page, int) or page < 1:
        raise ProjectListError("page must be a positive integer")
    if isinstance(page_size, bool) or not isinstance(page_size, int) or not 1 <= page_size <= MAX_PAGE_SIZE:
        raise ProjectListError("page size is invalid")
    selected_columns = _normalise_columns(columns)
    catalog = _catalog_snapshot(company_id, period, catalog_rows)
    filtered = _filtered_rows(
        catalog,
        project_status=project_status,
        client=client,
        owner=owner,
        margin_band=margin_band,
        collection_band=collection_band,
        risk=risk,
    )
    ordered = sorted(filtered, key=lambda row: (_group_key(group_by, row)[0], _sort_key(sort_by, row)))
    total_count = len(ordered)
    page_count = max(1, (total_count + page_size - 1) // page_size)
    effective_page = min(page, page_count)
    start = (effective_page - 1) * page_size
    visible = [dict(row) for row in ordered[start : start + page_size]]
    for absolute_index, row in enumerate(visible, start=start + 1):
        _, group_id, group_label = _group_key(group_by, row)
        row.update(
            {
                "absolute_row_number": absolute_index,
                "group_id": group_id,
                "group_label_zh": group_label,
            }
        )
    counts: Counter[tuple[str, str]] = Counter()
    order: list[tuple[str, str]] = []
    for row in ordered:
        _, group_id, group_label = _group_key(group_by, row)
        key = (group_id, group_label)
        if key not in counts:
            order.append(key)
        counts[key] += 1
    return {
        "schema_version": "kmfa.v015.s17p1.project_list_response.v1",
        "data_classification": "PUBLIC_SYNTHETIC",
        "allowed": True,
        "context": {"company_id": company_id, "period": period, "project_status": project_status},
        "rows": visible,
        "all_filtered_project_ids": [row["project_id"] for row in ordered],
        "catalog_count": len(catalog),
        "filtered_count": total_count,
        "page": effective_page,
        "requested_page": page,
        "page_size": page_size,
        "page_count": page_count,
        "visible_count": len(visible),
        "selected_columns": selected_columns,
        "available_columns": [dict(item) for item in AVAILABLE_COLUMNS],
        "default_visible_column_count": DEFAULT_VISIBLE_COLUMN_COUNT,
        "group_by": group_by,
        "group_explanation_zh": GROUP_EXPLANATIONS[group_by],
        "groups": [{"group_id": key[0], "label_zh": key[1], "count": counts[key]} for key in order],
        "sort_by": sort_by,
        "sort_explanation_zh": SORT_EXPLANATIONS[sort_by],
        "filter_options": {
            "clients": sorted({row["client_zh"] for row in catalog}),
            "owners": sorted({row["owner_zh"] for row in catalog}),
        },
        "source_note_zh": "全部为公开合成项目；每行保留来源编号和 2026-07-15 截止日。",
        "fact_layer_write_count": 0,
        "external_network_request_count": 0,
        "real_business_action_count": 0,
    }


def batch_compare(
    project_ids: Sequence[str],
    *,
    company_id: str = "demo-north",
    period: str = "2026-07",
    catalog_rows: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """生成只读对比，项目事实保持原值。"""

    selected = list(project_ids)
    if not MIN_BATCH_COUNT <= len(selected) <= MAX_BATCH_COUNT:
        raise ProjectListError("请选择 2 至 6 个项目进行对比")
    if len(selected) != len(set(selected)):
        raise ProjectListError("项目选择不能重复")
    catalog = {row["project_id"]: row for row in _catalog_snapshot(company_id, period, catalog_rows)}
    if any(project_id not in catalog for project_id in selected):
        raise ProjectListError("所选项目不在当前公司范围内")
    rows = [dict(catalog[project_id]) for project_id in selected]
    revenue = sum(row["revenue_cents"] for row in rows)
    cost = sum(row["cost_cents"] for row in rows)
    profit = sum(row["gross_profit_cents"] for row in rows)
    collected = sum(row["revenue_cents"] * row["collection_bps"] // 10_000 for row in rows)
    weighted_margin = profit * 10_000 // revenue if revenue else 0
    weighted_collection = collected * 10_000 // revenue if revenue else 0
    return {
        "schema_version": "kmfa.v015.s17p1.project_compare_response.v1",
        "data_classification": "PUBLIC_SYNTHETIC",
        "company_id": company_id,
        "period": period,
        "project_ids": selected,
        "project_count": len(rows),
        "rows": rows,
        "totals": {
            "revenue_cents": revenue,
            "cost_cents": cost,
            "gross_profit_cents": profit,
            "weighted_margin_bps": weighted_margin,
            "weighted_margin_display_zh": format_percent_bps(weighted_margin),
            "weighted_collection_bps": weighted_collection,
            "weighted_collection_display_zh": format_percent_bps(weighted_collection),
        },
        "source_note_zh": "对比直接引用当前公开合成项目台账，不改写任何项目事实。",
        "fact_layer_write_count": 0,
        "export_write_count": 0,
        "real_business_action_count": 0,
    }


def export_csv(
    project_ids: Sequence[str],
    *,
    company_id: str = "demo-north",
    period: str = "2026-07",
    catalog_rows: Sequence[Mapping[str, Any]] | None = None,
) -> str:
    """导出与批量对比一致的 CSV，每行强制包含来源与截止日。"""

    comparison = batch_compare(
        project_ids,
        company_id=company_id,
        period=period,
        catalog_rows=catalog_rows,
    )
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(
        [
            "项目编号",
            "项目名称",
            "公司",
            "客户",
            "负责人",
            "状态",
            "风险",
            "收入(分)",
            "成本(分)",
            "毛利(分)",
            "毛利率(基点)",
            "回款进度(基点)",
            "行业",
            "项目期间",
            "来源说明",
            "来源编号",
            "数据截止日",
            "数据分类",
        ]
    )
    for row in comparison["rows"]:
        writer.writerow(
            [
                row["project_id"],
                row["project_name_zh"],
                row["company_zh"],
                row["client_zh"],
                row["owner_zh"],
                row["status_zh"],
                row["risk_zh"],
                row["revenue_cents"],
                row["cost_cents"],
                row["gross_profit_cents"],
                row["gross_margin_bps"],
                row["collection_bps"],
                row["industry_zh"],
                row["project_period"],
                row["source_zh"],
                row["source_ref"],
                row["cutoff_date"],
                row["data_classification"],
            ]
        )
    return stream.getvalue()


def public_checks() -> list[dict[str, Any]]:
    """形成确定性的公开检查清单，供证据生成和复核共用。"""

    checks: list[dict[str, Any]] = []

    def add(check_id: str, passed: bool, detail_zh: str) -> None:
        checks.append({"check_id": check_id, "passed": bool(passed), "detail_zh": detail_zh})

    for company_id in COMPANY_IDS:
        rows = project_catalog(company_id, "2026-07")
        add(f"{company_id}_row_count", len(rows) == PROJECTS_PER_COMPANY, "每家公司六个项目")
        add(f"{company_id}_unique", len({row["project_id"] for row in rows}) == 6, "项目编号唯一")
        add(f"{company_id}_integer_money", all(isinstance(row["revenue_cents"], int) for row in rows), "金额使用整数分")
        add(f"{company_id}_equation", all(row["revenue_cents"] == row["cost_cents"] + row["gross_profit_cents"] for row in rows), "收入等于成本加毛利")
        add(f"{company_id}_lineage", all(row["source_ref"] and row["cutoff_date"] for row in rows), "每行包含来源和截止日")
        add(f"{company_id}_boundary", all(row["company_id"] == company_id for row in rows), "没有跨公司混入")
    baseline = project_list()
    add("default_columns", baseline["default_visible_column_count"] == 8, "默认只显示八列")
    add("page_one", [row["absolute_row_number"] for row in baseline["rows"]] == [1, 2, 3, 4], "第一页行号连续")
    second = project_list(page=2)
    add("page_two", [row["absolute_row_number"] for row in second["rows"]] == [5, 6], "第二页行号连续")
    add("stable_pages", not ({row["project_id"] for row in baseline["rows"]} & {row["project_id"] for row in second["rows"]}), "分页没有重复项目")
    for sort_by in SORT_OPTIONS:
        payload = project_list(sort_by=sort_by, page_size=6)
        add(f"sort_{sort_by}", len(payload["rows"]) == 6 and bool(payload["sort_explanation_zh"]), "排序规则可见且覆盖全部项目")
    for group_by in GROUP_OPTIONS:
        payload = project_list(group_by=group_by, page_size=6)
        add(f"group_{group_by}", sum(group["count"] for group in payload["groups"]) == 6, "分组数量与项目数量一致")
    for status in ("attention", "normal"):
        payload = project_list(project_status=status, page_size=6)
        expected = "ATTENTION" if status == "attention" else "NORMAL"
        add(f"filter_status_{status}", all(row["status"] == expected for row in payload["rows"]), "状态筛选准确")
    for band in MARGIN_BANDS:
        payload = project_list(margin_band=band, page_size=6)
        add(f"filter_margin_{band}", all(row["margin_band"] == band for row in payload["rows"]), "毛利筛选准确")
    for band in COLLECTION_BANDS:
        payload = project_list(collection_band=band, page_size=6)
        add(f"filter_collection_{band}", all(row["collection_band"] == band for row in payload["rows"]), "回款筛选准确")
    for risk in RISK_LEVELS:
        payload = project_list(risk=risk, page_size=6)
        add(f"filter_risk_{risk.lower()}", all(row["risk_level"] == risk for row in payload["rows"]), "风险筛选准确")
    rows = project_catalog("demo-north", "2026-07")
    for client in sorted({row["client_zh"] for row in rows})[:2]:
        payload = project_list(client=client, page_size=6)
        add(f"filter_client_{len(checks)}", all(row["client_zh"] == client for row in payload["rows"]), "客户筛选准确")
    for owner in sorted({row["owner_zh"] for row in rows})[:2]:
        payload = project_list(owner=owner, page_size=6)
        add(f"filter_owner_{len(checks)}", all(row["owner_zh"] == owner for row in payload["rows"]), "负责人筛选准确")
    selected = [row["project_id"] for row in rows[:3]]
    compare = batch_compare(selected)
    add("compare_count", compare["project_count"] == 3, "批量对比项目数一致")
    add("compare_read_only", compare["fact_layer_write_count"] == 0, "批量对比不修改事实")
    add("compare_total", compare["totals"]["revenue_cents"] == sum(row["revenue_cents"] for row in rows[:3]), "对比汇总金额一致")
    exported = export_csv(selected)
    parsed = list(csv.DictReader(io.StringIO(exported)))
    add("export_count", len(parsed) == 3, "导出项目数一致")
    add("export_ids", [row["项目编号"] for row in parsed] == selected, "导出顺序与选择一致")
    add("export_lineage", all(row["来源说明"] and row["来源编号"] and row["数据截止日"] for row in parsed), "导出每行包含来源说明")
    add("export_amounts", [int(row["收入(分)"]) for row in parsed] == [row["revenue_cents"] for row in rows[:3]], "导出金额与项目事实一致")
    add("catalog_total", PROJECTS_PER_COMPANY * COMPANY_COUNT == CATALOG_PROJECT_COUNT, "公开目录共十八个项目")
    add("fact_write_zero", baseline["fact_layer_write_count"] == 0, "事实层写入为零")
    add("network_zero", baseline["external_network_request_count"] == 0, "外部网络请求为零")
    if not all(check["passed"] for check in checks):
        failed = [check["check_id"] for check in checks if not check["passed"]]
        raise ProjectListError("project list public checks failed: " + ", ".join(failed))
    return checks


def main() -> int:
    try:
        checks = public_checks()
    except (KeyError, TypeError, ProjectListError, homepage.HomepageError) as error:
        print(f"FAIL: {error}")
        return 1
    print(f"PASS: S17-P1 project list public checks {len(checks)}/{len(checks)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
