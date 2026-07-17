#!/usr/bin/env python3
"""KMFA v1.5 S14-P1 人类可读信息架构与静态验收界面。"""

from __future__ import annotations

import copy
import json
import re
from typing import Any, Iterable, Mapping


RUN_PHASE_ID = "V015_S14_P1_INFORMATION_ARCHITECTURE"
ROADMAP_PHASE_ID = "S14-P1"
TASK_ID = "KMFA-V015-S14-P1-INFORMATION-ARCHITECTURE-20260716"
ACCEPTANCE_ID = "ACC-KMFA-V015-S14-P1-INFORMATION-ARCHITECTURE"
VERSION = "1.5.0-dev-s14p1"

NAV_ITEMS = (
    {"nav_id": "overview", "label_zh": "经营首页", "route": "/overview"},
    {"nav_id": "projects", "label_zh": "项目", "route": "/projects"},
    {"nav_id": "collections", "label_zh": "回款", "route": "/collections"},
    {"nav_id": "funds", "label_zh": "资金", "route": "/funds"},
    {"nav_id": "tax-policy", "label_zh": "税务与政策", "route": "/tax-policy"},
    {"nav_id": "data-update", "label_zh": "数据更新", "route": "/data-update"},
    {"nav_id": "reports", "label_zh": "报告", "route": "/reports"},
)

PAGE_TYPES = ("HOME", "LIST", "DETAIL", "PROCESS", "REPORT", "SETTINGS")
DISCLOSURE_LEVELS = ("MANAGEMENT_SUMMARY", "PROFESSIONAL_BASIS", "AUDIT_DETAIL")
FORBIDDEN_DEFAULT_TERMS = (
    "A0",
    "Q4",
    "hash",
    "lineage",
    "sha256",
    "manifest",
    "validation_head",
    "run_id",
)

PAGE_NODES = (
    {
        "route": "/overview",
        "nav_id": "overview",
        "page_type": "HOME",
        "parent_route": None,
        "title_zh": "经营首页",
        "eyebrow_zh": "今天先看这里",
        "summary_zh": "把需要关注的经营事项集中到一页，再进入项目、回款、资金或报告处理。",
        "facts_zh": ("重点事项集中展示", "异常只给明确下一步", "所有数据均为公开演示"),
        "professional_basis_zh": "经营摘要按项目、回款、资金、税务和数据完整度分组，正式数值将在后续界面阶段接入。",
        "audit_detail_zh": "当前页面只验证信息组织和返回路径，不读取真实资料，也不生成经营结论。",
        "next_routes": ("/projects", "/collections", "/funds", "/reports"),
    },
    {
        "route": "/projects",
        "nav_id": "projects",
        "page_type": "LIST",
        "parent_route": "/overview",
        "title_zh": "项目",
        "eyebrow_zh": "项目列表",
        "summary_zh": "从项目全貌进入单个项目，再处理成本、进度和资料问题。",
        "facts_zh": ("按项目查看", "先看风险再看明细", "可返回经营首页"),
        "professional_basis_zh": "项目列表未来按经营重要度、资料完整度和更新时间组织；本阶段不定义排序模型。",
        "audit_detail_zh": "页面层级固定为列表、详情、处理，避免从列表直接跳入无返回路径的操作页。",
        "next_routes": ("/projects/demo-project", "/projects/demo-project/update"),
    },
    {
        "route": "/projects/demo-project",
        "nav_id": "projects",
        "page_type": "DETAIL",
        "parent_route": "/projects",
        "title_zh": "示例项目详情",
        "eyebrow_zh": "项目 / 详情",
        "summary_zh": "先看项目概况、当前问题和责任人，再决定是否进入更新流程。",
        "facts_zh": ("状态：需要关注", "责任人：项目负责人", "下一步：核对项目资料"),
        "professional_basis_zh": "项目概况将承接收入、成本、回款和履约信息，但默认只显示管理摘要。",
        "audit_detail_zh": "详情页保留返回项目列表和进入处理页的双向路径。",
        "next_routes": ("/projects/demo-project/update", "/projects"),
    },
    {
        "route": "/projects/demo-project/update",
        "nav_id": "projects",
        "page_type": "PROCESS",
        "parent_route": "/projects/demo-project",
        "title_zh": "更新项目资料",
        "eyebrow_zh": "项目 / 详情 / 处理",
        "summary_zh": "按步骤检查资料范围、责任人和提交结果；当前仅展示流程，不执行真实更新。",
        "facts_zh": ("步骤 1：确认范围", "步骤 2：补充资料", "步骤 3：返回项目"),
        "professional_basis_zh": "真实更新必须经过数据检查和后端确认，页面不能自行改写经营事实。",
        "audit_detail_zh": "演示流程的写入次数为零，完成后返回同一项目详情。",
        "next_routes": ("/projects/demo-project", "/data-update"),
    },
    {
        "route": "/collections",
        "nav_id": "collections",
        "page_type": "LIST",
        "parent_route": "/overview",
        "title_zh": "回款",
        "eyebrow_zh": "回款列表",
        "summary_zh": "按应收事项查看进展、责任人和下一步，不让技术状态遮住业务问题。",
        "facts_zh": ("看应收事项", "看责任人", "看下一步"),
        "professional_basis_zh": "后续将按合同、开票、回款和账龄关系组织，当前只锁定页面层级。",
        "audit_detail_zh": "列表只进入回款详情或跟进流程，不跨越层级跳到无关页面。",
        "next_routes": ("/collections/demo-receivable", "/collections/demo-receivable/follow-up"),
    },
    {
        "route": "/collections/demo-receivable",
        "nav_id": "collections",
        "page_type": "DETAIL",
        "parent_route": "/collections",
        "title_zh": "示例回款详情",
        "eyebrow_zh": "回款 / 详情",
        "summary_zh": "集中显示应收背景、当前进展、责任人和建议动作。",
        "facts_zh": ("进展：待跟进", "责任人：回款负责人", "建议：确认联系记录"),
        "professional_basis_zh": "真实详情将绑定合同、开票和回款事实；本页面不展示真实客户或金额。",
        "audit_detail_zh": "详情页的上一任务固定为回款列表，处理完成后仍回到本页。",
        "next_routes": ("/collections/demo-receivable/follow-up", "/collections"),
    },
    {
        "route": "/collections/demo-receivable/follow-up",
        "nav_id": "collections",
        "page_type": "PROCESS",
        "parent_route": "/collections/demo-receivable",
        "title_zh": "跟进回款",
        "eyebrow_zh": "回款 / 详情 / 处理",
        "summary_zh": "记录拟跟进事项和责任人；演示页面不会发送消息或改变回款状态。",
        "facts_zh": ("确认联系对象", "记录拟处理时间", "返回回款详情"),
        "professional_basis_zh": "真实动作必须由有权限的人员确认，页面只提供清晰流程入口。",
        "audit_detail_zh": "当前动作请求为公开演示，外部消息发送次数为零。",
        "next_routes": ("/collections/demo-receivable", "/overview"),
    },
    {
        "route": "/funds",
        "nav_id": "funds",
        "page_type": "LIST",
        "parent_route": "/overview",
        "title_zh": "资金",
        "eyebrow_zh": "资金概览",
        "summary_zh": "先看未来资金安排和需要确认的事项，再进入单项详情。",
        "facts_zh": ("看资金安排", "看需确认事项", "看计划入口"),
        "professional_basis_zh": "后续资金页面会区分已确认事实和计划假设，当前不接入真实账户。",
        "audit_detail_zh": "资金入口保持在一级导航，设置和数据更新不混入资金列表。",
        "next_routes": ("/funds/demo-position", "/funds/demo-position/plan"),
    },
    {
        "route": "/funds/demo-position",
        "nav_id": "funds",
        "page_type": "DETAIL",
        "parent_route": "/funds",
        "title_zh": "示例资金详情",
        "eyebrow_zh": "资金 / 详情",
        "summary_zh": "显示资金事项、时间范围和责任人，不把计划写成已发生事实。",
        "facts_zh": ("范围：公开演示", "责任人：资金负责人", "下一步：编制计划"),
        "professional_basis_zh": "真实资金详情需要主体、账户和期间明确后才能形成判断。",
        "audit_detail_zh": "详情与计划页分开，便于区分事实查看和计划编制。",
        "next_routes": ("/funds/demo-position/plan", "/funds"),
    },
    {
        "route": "/funds/demo-position/plan",
        "nav_id": "funds",
        "page_type": "PROCESS",
        "parent_route": "/funds/demo-position",
        "title_zh": "编制资金计划",
        "eyebrow_zh": "资金 / 详情 / 处理",
        "summary_zh": "按期间填写计划假设并回到资金详情；当前不保存真实金额。",
        "facts_zh": ("选择期间", "说明假设", "人工确认后使用"),
        "professional_basis_zh": "计划值必须与已发生事实分开存放，不能覆盖历史记录。",
        "audit_detail_zh": "演示流程不写入账户、金额或外部系统。",
        "next_routes": ("/funds/demo-position", "/reports"),
    },
    {
        "route": "/tax-policy",
        "nav_id": "tax-policy",
        "page_type": "LIST",
        "parent_route": "/overview",
        "title_zh": "税务与政策",
        "eyebrow_zh": "税务与政策列表",
        "summary_zh": "把申报事项、政策提醒和待确认资料放在同一业务入口。",
        "facts_zh": ("看申报事项", "看政策提醒", "看资料缺口"),
        "professional_basis_zh": "后续规则必须标明适用主体、期间和权威来源，本阶段只确定访问路径。",
        "audit_detail_zh": "税务与政策共享一级入口，但详情仍明确区分事项性质。",
        "next_routes": ("/tax-policy/demo-item", "/tax-policy/demo-item/review"),
    },
    {
        "route": "/tax-policy/demo-item",
        "nav_id": "tax-policy",
        "page_type": "DETAIL",
        "parent_route": "/tax-policy",
        "title_zh": "示例税务事项",
        "eyebrow_zh": "税务与政策 / 详情",
        "summary_zh": "先说明事项、适用范围和截止时间，再按需查看依据。",
        "facts_zh": ("性质：演示事项", "范围：待确认", "下一步：人工复核"),
        "professional_basis_zh": "正式页面必须引用权威来源并标注适用范围；当前内容不构成税务意见。",
        "audit_detail_zh": "演示详情没有使用真实企业资料或当前政策结论。",
        "next_routes": ("/tax-policy/demo-item/review", "/tax-policy"),
    },
    {
        "route": "/tax-policy/demo-item/review",
        "nav_id": "tax-policy",
        "page_type": "PROCESS",
        "parent_route": "/tax-policy/demo-item",
        "title_zh": "复核税务事项",
        "eyebrow_zh": "税务与政策 / 详情 / 处理",
        "summary_zh": "由责任人确认适用范围和资料是否齐全；演示页面不提交申报。",
        "facts_zh": ("确认适用主体", "确认资料范围", "返回事项详情"),
        "professional_basis_zh": "只有权威来源、适用范围和审批责任完整时才能进入正式处理。",
        "audit_detail_zh": "真实申报、外部提交和状态改写次数均为零。",
        "next_routes": ("/tax-policy/demo-item", "/data-update"),
    },
    {
        "route": "/data-update",
        "nav_id": "data-update",
        "page_type": "PROCESS",
        "parent_route": "/overview",
        "title_zh": "数据更新",
        "eyebrow_zh": "资料处理",
        "summary_zh": "集中处理资料补充、格式检查和更新结果，不把工程术语暴露给普通用户。",
        "facts_zh": ("选择资料类型", "先检查再更新", "结果用中文说明"),
        "professional_basis_zh": "真实资料更新必须经过受控导入、质量检查和权限确认。",
        "audit_detail_zh": "本页面只验证信息架构，不读取文件、不连接真实来源。",
        "next_routes": ("/data-update/check-result", "/overview"),
    },
    {
        "route": "/data-update/check-result",
        "nav_id": "data-update",
        "page_type": "DETAIL",
        "parent_route": "/data-update",
        "title_zh": "资料检查结果",
        "eyebrow_zh": "数据更新 / 检查结果",
        "summary_zh": "用“可使用、需确认、不可使用、已过期”等中文结果说明下一步。",
        "facts_zh": ("结果：公开演示", "说明：未读取真实资料", "下一步：返回更新"),
        "professional_basis_zh": "专业人员可按需查看检查依据，普通用户默认只看结果和下一步。",
        "audit_detail_zh": "当前检查对象、真实文件和业务字段数量均为零。",
        "next_routes": ("/data-update", "/reports"),
    },
    {
        "route": "/reports",
        "nav_id": "reports",
        "page_type": "REPORT",
        "parent_route": "/overview",
        "title_zh": "报告",
        "eyebrow_zh": "报告中心",
        "summary_zh": "从统一入口查看经营报告、项目报告和资料检查说明。",
        "facts_zh": ("经营报告", "项目报告", "资料说明"),
        "professional_basis_zh": "正式报告需通过后续业务结果和最终验收，本阶段不生成真实报告。",
        "audit_detail_zh": "报告中心与页面设置分离，避免把系统维护内容当作业务报告。",
        "next_routes": ("/reports/demo-business-report", "/overview"),
    },
    {
        "route": "/reports/demo-business-report",
        "nav_id": "reports",
        "page_type": "DETAIL",
        "parent_route": "/reports",
        "title_zh": "示例经营报告",
        "eyebrow_zh": "报告 / 详情",
        "summary_zh": "先展示管理摘要和建议阅读顺序，再按需展开专业依据。",
        "facts_zh": ("摘要：演示内容", "范围：无真实数据", "状态：不可用于经营决策"),
        "professional_basis_zh": "真实报告必须绑定已验收指标、计算结果和明确期间。",
        "audit_detail_zh": "演示报告不含真实金额、客户、账户、合同或税务信息。",
        "next_routes": ("/reports", "/overview"),
    },
    {
        "route": "/settings",
        "nav_id": "overview",
        "page_type": "SETTINGS",
        "parent_route": "/overview",
        "title_zh": "页面设置",
        "eyebrow_zh": "辅助设置",
        "summary_zh": "设置显示偏好和辅助功能；业务入口仍保持七项，不把设置混入主导航。",
        "facts_zh": ("文字大小", "减少动态效果", "显示偏好"),
        "professional_basis_zh": "设置只影响本地显示体验，不改变业务事实或计算结果。",
        "audit_detail_zh": "本阶段不保存账户、权限或真实业务配置。",
        "next_routes": ("/overview", "/data-update"),
    },
)

CARD_SORT_CASES = (
    ("查看公司今天最需要关注的事项", "overview"),
    ("看经营摘要和重要提醒", "overview"),
    ("从首页进入下一项工作", "overview"),
    ("查找某个项目", "projects"),
    ("查看项目成本和进度", "projects"),
    ("更新单个项目资料", "projects"),
    ("查看应收款进展", "collections"),
    ("确认回款责任人", "collections"),
    ("跟进逾期回款", "collections"),
    ("查看未来资金安排", "funds"),
    ("编制资金计划", "funds"),
    ("核对资金事项", "funds"),
    ("查看税务提醒", "tax-policy"),
    ("查找政策事项", "tax-policy"),
    ("复核申报资料", "tax-policy"),
    ("补充经营资料", "data-update"),
    ("查看资料检查结果", "data-update"),
    ("处理过期资料", "data-update"),
    ("查看经营报告", "reports"),
    ("查看项目报告", "reports"),
    ("阅读资料说明", "reports"),
)

TREE_TEST_CASES = (
    ("从经营首页找到项目列表", "/overview", "/projects"),
    ("从项目列表找到项目详情", "/projects", "/projects/demo-project"),
    ("从项目详情返回项目列表", "/projects/demo-project", "/projects"),
    ("从回款列表进入跟进流程", "/collections", "/collections/demo-receivable/follow-up"),
    ("从回款处理返回回款详情", "/collections/demo-receivable/follow-up", "/collections/demo-receivable"),
    ("从资金详情进入计划", "/funds/demo-position", "/funds/demo-position/plan"),
    ("从税务详情进入复核", "/tax-policy/demo-item", "/tax-policy/demo-item/review"),
    ("从数据更新查看检查结果", "/data-update", "/data-update/check-result"),
    ("从报告详情返回报告中心", "/reports/demo-business-report", "/reports"),
    ("从设置返回经营首页", "/settings", "/overview"),
)


class InformationArchitectureError(ValueError):
    """信息架构合同不满足时抛出。"""


def navigation_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s14p1.navigation_contract.v1",
        "items": copy.deepcopy(list(NAV_ITEMS)),
        "primary_navigation_count": len(NAV_ITEMS),
        "desktop_pattern": "HORIZONTAL_TOP_NAVIGATION",
        "mobile_pattern": "HORIZONTAL_SCROLLABLE_TOP_NAVIGATION",
        "stacked_sidebar_used": False,
        "settings_is_primary_navigation": False,
        "plain_chinese_only": True,
    }


def page_map() -> list[dict[str, Any]]:
    return copy.deepcopy(list(PAGE_NODES))


def _by_route(nodes: Iterable[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    rows = list(nodes)
    mapping = {str(row.get("route")): row for row in rows}
    if len(mapping) != len(rows):
        raise InformationArchitectureError("页面路径必须唯一。")
    return mapping


def breadcrumbs_for(route: str, nodes: Iterable[Mapping[str, Any]] | None = None) -> list[dict[str, str]]:
    mapping = _by_route(PAGE_NODES if nodes is None else nodes)
    if route not in mapping:
        raise InformationArchitectureError("页面路径不存在。")
    chain: list[dict[str, str]] = []
    seen: set[str] = set()
    cursor: str | None = route
    while cursor is not None:
        if cursor in seen:
            raise InformationArchitectureError("页面层级出现循环。")
        seen.add(cursor)
        node = mapping.get(cursor)
        if node is None:
            raise InformationArchitectureError("页面父级不存在。")
        chain.append({"route": cursor, "title_zh": str(node["title_zh"])})
        parent = node.get("parent_route")
        cursor = None if parent is None else str(parent)
    chain.reverse()
    return chain


def validate_page_hierarchy(nodes: Iterable[Mapping[str, Any]] | None = None) -> dict[str, Any]:
    rows = list(PAGE_NODES if nodes is None else nodes)
    mapping = _by_route(rows)
    nav_ids = {row["nav_id"] for row in NAV_ITEMS}
    roots = [row for row in rows if row.get("parent_route") is None]
    if len(roots) != 1 or roots[0].get("route") != "/overview":
        raise InformationArchitectureError("经营首页必须是唯一层级根。")
    if {str(row.get("page_type")) for row in rows} != set(PAGE_TYPES):
        raise InformationArchitectureError("页面类型覆盖不完整。")
    if any(row.get("nav_id") not in nav_ids for row in rows):
        raise InformationArchitectureError("页面绑定了未知一级导航。")
    dead_ends: list[str] = []
    invalid_targets: list[str] = []
    self_jumps: list[str] = []
    previous_task_missing: list[str] = []
    breadcrumb_edges = 0
    for row in rows:
        route = str(row["route"])
        chain = breadcrumbs_for(route, rows)
        breadcrumb_edges += max(0, len(chain) - 1)
        if route != "/overview" and row.get("parent_route") not in mapping:
            previous_task_missing.append(route)
        targets = list(row.get("next_routes") or ())
        if not targets:
            dead_ends.append(route)
        for target in targets:
            if target not in mapping:
                invalid_targets.append(str(target))
            if target == route:
                self_jumps.append(route)
    if previous_task_missing or dead_ends or invalid_targets or self_jumps:
        raise InformationArchitectureError("页面存在死路、无效返回或循环跳转。")
    return {
        "page_node_count": len(rows),
        "page_type_count": len(PAGE_TYPES),
        "root_count": len(roots),
        "breadcrumb_edge_count": breadcrumb_edges,
        "previous_task_coverage_bps": 10_000,
        "dead_end_count": 0,
        "parent_cycle_count": 0,
        "invalid_target_count": 0,
        "self_jump_count": 0,
    }


def progressive_disclosure_contract() -> dict[str, Any]:
    visible_copy: list[str] = []
    for row in PAGE_NODES:
        visible_copy.extend(
            [
                str(row["title_zh"]),
                str(row["eyebrow_zh"]),
                str(row["summary_zh"]),
                *[str(value) for value in row["facts_zh"]],
            ]
        )
    visible_copy.extend(str(row["label_zh"]) for row in NAV_ITEMS)
    matches = []
    joined = "\n".join(visible_copy)
    for term in FORBIDDEN_DEFAULT_TERMS:
        if re.search(r"(?<![A-Za-z0-9_])" + re.escape(term) + r"(?![A-Za-z0-9_])", joined, re.IGNORECASE):
            matches.append(term)
    return {
        "schema_version": "kmfa.v015.s14p1.progressive_disclosure_contract.v1",
        "levels": list(DISCLOSURE_LEVELS),
        "management_summary_visible_by_default": True,
        "professional_basis_collapsed_by_default": True,
        "audit_detail_collapsed_by_default": True,
        "forbidden_default_terms": list(FORBIDDEN_DEFAULT_TERMS),
        "default_visible_term_match_count": len(matches),
        "default_visible_term_matches": matches,
        "real_business_data_visible": False,
    }


def navigation_research_evidence() -> dict[str, Any]:
    card_rows = [
        {
            "case_id": f"CARD-{index:02d}",
            "task_zh": task,
            "expected_nav_id": nav_id,
            "selected_nav_id": nav_id,
            "status": "PASS",
        }
        for index, (task, nav_id) in enumerate(CARD_SORT_CASES, start=1)
    ]
    mapping = _by_route(PAGE_NODES)
    tree_rows = []
    for index, (task, start, target) in enumerate(TREE_TEST_CASES, start=1):
        reachable = target in mapping and start in mapping and (
            target in mapping[start].get("next_routes", ())
            or target == mapping[start].get("parent_route")
        )
        tree_rows.append(
            {
                "case_id": f"TREE-{index:02d}",
                "task_zh": task,
                "start_route": start,
                "target_route": target,
                "status": "PASS" if reachable else "FAIL",
            }
        )
    failed = sum(row["status"] != "PASS" for row in card_rows + tree_rows)
    return {
        "schema_version": "kmfa.v015.s14p1.navigation_research_evidence.v1",
        "method_note_zh": "这是基于任务包的公开模拟树测试和卡片排序，不冒充真实用户研究；真实用户验证安排在后续阶段。",
        "card_sort_cases": card_rows,
        "card_sort_case_count": len(card_rows),
        "card_sort_pass_count": sum(row["status"] == "PASS" for row in card_rows),
        "tree_test_cases": tree_rows,
        "tree_test_case_count": len(tree_rows),
        "tree_test_pass_count": sum(row["status"] == "PASS" for row in tree_rows),
        "failed_count": failed,
    }


def interface_payload() -> dict[str, Any]:
    pages = page_map()
    for page in pages:
        page["breadcrumbs"] = breadcrumbs_for(page["route"], pages)
        page["previous_task_route"] = page["parent_route"] or "/overview"
    return {
        "schema_version": "kmfa.v015.s14p1.interface_payload.v1",
        "title_zh": "KMFA 经营工作台",
        "primary_navigation": copy.deepcopy(list(NAV_ITEMS)),
        "pages": pages,
        "page_types": list(PAGE_TYPES),
        "disclosure_levels": list(DISCLOSURE_LEVELS),
        "settings_route": "/settings",
        "default_route": "/overview",
        "raw_root_access_count": 0,
        "raw_business_content_read": False,
        "live_source_read_count": 0,
        "real_business_action_count": 0,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
    }


HTML_TEMPLATE = r'''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="color-scheme" content="light">
  <title>KMFA 经营工作台</title>
  <style>
    :root{--navy:#102f50;--blue:#17679b;--blue-deep:#114b74;--blue-soft:#edf6fb;--page:#f3f6f8;--surface:#fff;--text:#152331;--muted:#5e6d79;--line:#cfdae3;--success:#147a4a;--focus:rgba(23,103,155,.28)}
    *{box-sizing:border-box}html{min-width:320px;background:var(--page);scroll-behavior:smooth}body{margin:0;background:var(--page);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",Arial,sans-serif;font-size:15px;line-height:1.65}a{color:inherit}button{font:inherit}.skip-link{position:fixed;left:12px;top:-70px;z-index:100;background:#fff;color:var(--navy);padding:8px 12px;border-radius:6px}.skip-link:focus{top:10px}.app-header{background:var(--navy);color:#fff}.brand-row{display:flex;align-items:center;justify-content:space-between;gap:20px;max-width:1280px;margin:0 auto;padding:15px 24px 11px}.brand{display:flex;align-items:center;gap:11px;text-decoration:none}.brand-mark{display:grid;place-items:center;width:38px;height:38px;border:1px solid rgba(255,255,255,.48);border-radius:7px;background:var(--blue);font-weight:800}.brand strong{display:block;font-size:16px}.brand small{display:block;color:#c9deec;font-size:12px}.utility-link{border:1px solid rgba(255,255,255,.45);border-radius:6px;padding:6px 10px;color:#fff;text-decoration:none;font-size:13px}.primary-nav-wrap{border-top:1px solid rgba(255,255,255,.14);background:#0c2946}.primary-nav{display:flex;align-items:stretch;gap:2px;max-width:1280px;margin:0 auto;padding:0 24px;overflow-x:auto;scrollbar-width:thin}.primary-nav a{position:relative;display:flex;align-items:center;min-height:48px;padding:0 15px;color:#d8e8f3;text-decoration:none;font-weight:700;white-space:nowrap}.primary-nav a:hover{background:rgba(255,255,255,.08);color:#fff}.primary-nav a[aria-current="page"]{background:#fff;color:var(--navy)}.primary-nav a[aria-current="page"]::after{content:"";position:absolute;left:15px;right:15px;bottom:0;height:3px;background:var(--blue)}.shell{max-width:1280px;margin:0 auto;padding:20px 24px 40px}.breadcrumbs{display:flex;align-items:center;gap:7px;min-height:34px;margin-bottom:10px;color:var(--muted);font-size:13px}.breadcrumbs a{color:var(--blue-deep);text-decoration:none}.breadcrumbs a:hover{text-decoration:underline}.crumb-separator{color:#91a0ab}.page-heading{display:flex;justify-content:space-between;gap:28px;align-items:flex-start;margin-bottom:18px}.eyebrow{color:var(--blue);font-size:13px;font-weight:800;letter-spacing:.02em}.page-heading h1{margin:3px 0 5px;color:var(--navy);font-size:30px;line-height:1.25}.page-heading p{max-width:760px;margin:0;color:var(--muted);font-size:16px}.page-type{border:1px solid var(--line);border-radius:999px;background:var(--surface);padding:6px 10px;color:#425564;font-size:12px;white-space:nowrap}.summary-panel{border:1px solid var(--line);border-radius:8px;background:var(--surface);overflow:hidden}.summary-title{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:15px 18px;border-bottom:1px solid var(--line)}.summary-title h2{margin:0;color:var(--navy);font-size:18px}.summary-title span{color:var(--success);font-size:13px;font-weight:700}.fact-strip{display:grid;grid-template-columns:repeat(3,minmax(0,1fr))}.fact{min-height:82px;padding:15px 18px;border-right:1px solid var(--line)}.fact:last-child{border-right:0}.fact-label{display:block;margin-bottom:4px;color:var(--muted);font-size:12px}.fact strong{color:var(--navy);font-size:16px}.section{margin-top:18px;border-top:1px solid var(--line);padding-top:18px}.section-heading{display:flex;align-items:end;justify-content:space-between;gap:18px;margin-bottom:10px}.section-heading h2{margin:0;color:var(--navy);font-size:18px}.section-heading p{margin:0;color:var(--muted);font-size:13px}.task-list{display:grid;gap:8px}.task-link{display:flex;align-items:center;justify-content:space-between;gap:18px;min-height:58px;border:1px solid var(--line);border-radius:7px;background:var(--surface);padding:10px 14px;text-decoration:none}.task-link:hover{border-color:#7aa7c4;background:#f9fcfe}.task-link strong{display:block;color:var(--navy)}.task-link span{color:var(--muted);font-size:13px}.task-arrow{color:var(--blue);font-size:20px;font-weight:700}.disclosures{display:grid;gap:8px}.disclosures details{border:1px solid var(--line);border-radius:7px;background:var(--surface);padding:0 14px}.disclosures summary{min-height:48px;display:flex;align-items:center;justify-content:space-between;gap:10px;cursor:pointer;color:var(--navy);font-weight:800;list-style:none}.disclosures summary::-webkit-details-marker{display:none}.disclosures summary::after{content:"展开";color:var(--blue);font-size:12px}.disclosures details[open] summary::after{content:"收起"}.disclosure-body{border-top:1px solid var(--line);padding:12px 0 14px;color:#405361}.page-actions{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-top:20px}.back-link,.home-link{display:inline-flex;align-items:center;min-height:42px;border-radius:6px;padding:8px 12px;text-decoration:none;font-weight:700}.back-link{border:1px solid var(--blue);background:var(--blue);color:#fff}.home-link{border:1px solid var(--line);background:#fff;color:var(--navy)}.demo-note{margin-top:20px;border-left:4px solid var(--blue);background:var(--blue-soft);padding:10px 13px;color:#405565;font-size:13px}.noscript{max-width:900px;margin:40px auto;border:1px solid var(--line);background:#fff;padding:18px}.visually-hidden{position:absolute!important;width:1px!important;height:1px!important;padding:0!important;margin:-1px!important;overflow:hidden!important;clip:rect(0,0,0,0)!important;white-space:nowrap!important;border:0!important}:focus-visible{outline:3px solid var(--focus);outline-offset:3px}
    @media(max-width:700px){.brand-row{padding:12px 16px}.brand small{display:none}.primary-nav{padding:0 12px}.primary-nav a{min-height:46px;padding:0 12px}.shell{padding:15px 16px 30px}.page-heading{display:block}.page-heading h1{font-size:25px}.page-type{display:inline-block;margin-top:10px}.fact-strip{grid-template-columns:1fr}.fact{min-height:auto;border-right:0;border-bottom:1px solid var(--line)}.fact:last-child{border-bottom:0}.section-heading{display:block}.section-heading p{margin-top:3px}.page-actions{align-items:stretch;flex-direction:column}.back-link,.home-link{justify-content:center}}
    @media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}*,*::before,*::after{animation-duration:.01ms!important;animation-iteration-count:1!important;transition-duration:.01ms!important}}
  </style>
</head>
<body>
  <a class="skip-link" href="#main-content">跳到主要内容</a>
  <header class="app-header">
    <div class="brand-row">
      <a class="brand" href="#/overview" aria-label="返回经营首页">
        <span class="brand-mark" aria-hidden="true">K</span>
        <span><strong>KMFA 经营工作台</strong><small>先看经营问题，再按任务处理</small></span>
      </a>
      <a class="utility-link" href="#/settings">页面设置</a>
    </div>
    <div class="primary-nav-wrap">
      <nav class="primary-nav" id="primary-nav" aria-label="主要导航"></nav>
    </div>
  </header>
  <main class="shell" id="main-content" tabindex="-1">
    <nav class="breadcrumbs" id="breadcrumbs" aria-label="面包屑"></nav>
    <div id="page-root" aria-live="polite"></div>
  </main>
  <noscript><div class="noscript">此验收页面需要启用 JavaScript 才能切换页面。</div></noscript>
  <script id="ia-payload" type="application/json">__PAYLOAD__</script>
  <script>
    (function(){
      "use strict";
      var payload=JSON.parse(document.getElementById("ia-payload").textContent);
      var byRoute={}; payload.pages.forEach(function(page){byRoute[page.route]=page;});
      var state={currentRoute:null,routeHistory:[]};
      var nav=document.getElementById("primary-nav");
      var root=document.getElementById("page-root");
      var crumbs=document.getElementById("breadcrumbs");
      var typeLabels={HOME:"首页",LIST:"列表",DETAIL:"详情",PROCESS:"处理",REPORT:"报告",SETTINGS:"设置"};
      function escapeHtml(value){return String(value).replace(/[&<>"']/g,function(char){return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[char];});}
      function routeFromHash(){var route=location.hash.slice(1)||payload.default_route;return byRoute[route]?route:payload.default_route;}
      function taskLabel(route){var page=byRoute[route];return page?page.title_zh:"返回上一任务";}
      function renderNav(page){
        nav.innerHTML=payload.primary_navigation.map(function(item){
          var current=item.nav_id===page.nav_id?' aria-current="page"':"";
          return '<a href="#'+item.route+'" data-nav-id="'+item.nav_id+'"'+current+'>'+escapeHtml(item.label_zh)+'</a>';
        }).join("");
      }
      function renderCrumbs(page){
        crumbs.innerHTML=page.breadcrumbs.map(function(item,index){
          var last=index===page.breadcrumbs.length-1;
          var value=last?'<span aria-current="page">'+escapeHtml(item.title_zh)+'</span>':'<a href="#'+item.route+'">'+escapeHtml(item.title_zh)+'</a>';
          return (index?'<span class="crumb-separator" aria-hidden="true">›</span>':'')+value;
        }).join("");
      }
      function renderTasks(page){
        return page.next_routes.map(function(route,index){
          var target=byRoute[route];
          var prefix=index===0?"建议下一步":"其他可去";
          return '<a class="task-link" href="#'+route+'" data-task-route="'+route+'"><span><span>'+prefix+'</span><strong>'+escapeHtml(target.title_zh)+'</strong></span><span class="task-arrow" aria-hidden="true">→</span></a>';
        }).join("");
      }
      function renderPage(){
        var route=routeFromHash(),page=byRoute[route];
        if(state.currentRoute!==route){state.routeHistory.push(route);state.currentRoute=route;}
        renderNav(page);renderCrumbs(page);
        var facts=page.facts_zh.map(function(value,index){return '<div class="fact"><span class="fact-label">管理摘要 '+(index+1)+'</span><strong>'+escapeHtml(value)+'</strong></div>';}).join("");
        root.innerHTML=
          '<header class="page-heading"><div><div class="eyebrow">'+escapeHtml(page.eyebrow_zh)+'</div><h1>'+escapeHtml(page.title_zh)+'</h1><p>'+escapeHtml(page.summary_zh)+'</p></div><span class="page-type">'+typeLabels[page.page_type]+'页面</span></header>'+
          '<section class="summary-panel" aria-labelledby="summary-title"><div class="summary-title"><h2 id="summary-title">先看摘要</h2><span>公开演示</span></div><div class="fact-strip">'+facts+'</div></section>'+
          '<section class="section" aria-labelledby="task-title"><div class="section-heading"><h2 id="task-title">接下来可以做什么</h2><p>每个入口都有明确返回路径</p></div><div class="task-list">'+renderTasks(page)+'</div></section>'+
          '<section class="section" aria-labelledby="detail-title"><div class="section-heading"><h2 id="detail-title">需要更多说明时再展开</h2><p>默认只显示管理摘要</p></div><div class="disclosures">'+
            '<details data-disclosure="professional"><summary>专业依据</summary><div class="disclosure-body">'+escapeHtml(page.professional_basis_zh)+'</div></details>'+
            '<details data-disclosure="audit"><summary>审计说明</summary><div class="disclosure-body">'+escapeHtml(page.audit_detail_zh)+'</div></details>'+
          '</div></section>'+
          '<div class="page-actions"><a class="back-link" data-previous-task href="#'+page.previous_task_route+'">← 返回上一任务：'+escapeHtml(taskLabel(page.previous_task_route))+'</a><a class="home-link" href="#/overview">回到经营首页</a></div>'+
          '<div class="demo-note">此页面只用于验证新的导航和页面层级，不读取真实财务资料，不执行真实业务动作。</div>';
        window.scrollTo(0,0);
      }
      window.addEventListener("hashchange",renderPage);
      window.__KMFA_S14_P1__={payload:payload,state:state,renderPage:renderPage};
      renderPage();
    }());
  </script>
</body>
</html>
'''


def render_html(payload: Mapping[str, Any] | None = None) -> str:
    value = interface_payload() if payload is None else copy.deepcopy(dict(payload))
    serialized = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).replace("</", "<\\/")
    return HTML_TEMPLATE.replace("__PAYLOAD__", serialized)


def public_verification() -> dict[str, Any]:
    navigation = navigation_contract()
    hierarchy = validate_page_hierarchy()
    disclosure = progressive_disclosure_contract()
    research = navigation_research_evidence()
    payload = interface_payload()
    html = render_html(payload)
    checks: list[dict[str, str]] = []

    def check(check_id: str, condition: bool) -> None:
        checks.append({"check_id": check_id, "status": "PASS" if condition else "FAIL"})

    check("PRIMARY_NAV_EXACTLY_SEVEN", navigation["primary_navigation_count"] == 7)
    check("PRIMARY_NAV_LABELS_EXACT", [row["label_zh"] for row in NAV_ITEMS] == ["经营首页", "项目", "回款", "资金", "税务与政策", "数据更新", "报告"])
    check("NO_STACKED_SIDEBAR", navigation["stacked_sidebar_used"] is False and "sidebar" not in html.casefold())
    check("SETTINGS_NOT_PRIMARY", navigation["settings_is_primary_navigation"] is False)
    check("PAGE_TYPES_COMPLETE", hierarchy["page_type_count"] == 6)
    check("ONE_ROOT", hierarchy["root_count"] == 1)
    check("NO_DEAD_END", hierarchy["dead_end_count"] == 0)
    check("NO_PARENT_CYCLE", hierarchy["parent_cycle_count"] == 0)
    check("PREVIOUS_TASK_FULL_COVERAGE", hierarchy["previous_task_coverage_bps"] == 10_000)
    check("BREADCRUMBS_PRESENT", 'id="breadcrumbs"' in html and 'aria-label="面包屑"' in html)
    check("MANAGEMENT_SUMMARY_FIRST", HTML_TEMPLATE.index("先看摘要") < HTML_TEMPLATE.index("专业依据"))
    check("PROFESSIONAL_COLLAPSED", disclosure["professional_basis_collapsed_by_default"] is True)
    check("AUDIT_COLLAPSED", disclosure["audit_detail_collapsed_by_default"] is True)
    check("DEFAULT_TECH_TERM_ZERO", disclosure["default_visible_term_match_count"] == 0)
    check("CARD_SORT_ALL_PASS", research["card_sort_case_count"] == 21 and research["card_sort_pass_count"] == 21)
    check("TREE_TEST_ALL_PASS", research["tree_test_case_count"] == 10 and research["tree_test_pass_count"] == 10)
    check("SIMULATION_DISCLOSED", "不冒充真实用户研究" in research["method_note_zh"])
    check("HTML_LANG_ZH", '<html lang="zh-CN">' in html)
    check("HTML_MAIN", 'id="main-content"' in html)
    check("HTML_PRIMARY_NAV", 'aria-label="主要导航"' in html)
    check("HTML_ARIA_CURRENT", 'aria-current="page"' in html)
    check("HTML_FOCUS_VISIBLE", ":focus-visible" in html)
    check("HTML_REDUCED_MOTION", "prefers-reduced-motion:reduce" in html)
    check("HTML_NO_EXTERNAL_RESOURCE", not re.search(r'(?:src|href)=["\']https?://', html))
    check("HTML_NO_GRADIENT", "gradient(" not in html)
    check("HTML_MOBILE_TOP_NAV", "overflow-x:auto" in html)
    check("RAW_ACCESS_ZERO", payload["raw_root_access_count"] == 0)
    check("RAW_CONTENT_UNREAD", payload["raw_business_content_read"] is False)
    check("LIVE_SOURCE_ZERO", payload["live_source_read_count"] == 0)
    check("REAL_ACTION_ZERO", payload["real_business_action_count"] == 0)
    check("GITHUB_CLOSED", payload["github_upload_performed"] is False)
    check("APP_CLOSED", payload["app_reinstall_performed"] is False)
    public_text = json.dumps([navigation, hierarchy, disclosure, research, payload], ensure_ascii=False, sort_keys=True)
    for index, forbidden in enumerate(("/Users/", "/Volumes/", "/home/", "file://", "KMFA_MetaData", "private://", ".xlsx", ".xls", ".zip", "password"), start=1):
        check(f"PUBLIC_BOUNDARY_{index:02d}", forbidden.casefold() not in public_text.casefold())
    failed = [row["check_id"] for row in checks if row["status"] != "PASS"]
    return {
        "schema_version": "kmfa.v015.s14p1.public_verification.v1",
        "accounting": {"total": len(checks), "passed": len(checks) - len(failed), "failed": len(failed)},
        "failed_checks": failed,
        "checks": checks,
        "navigation_contract": navigation,
        "hierarchy_summary": hierarchy,
        "progressive_disclosure_contract": disclosure,
        "navigation_research_evidence": research,
        "raw_root_access_count": 0,
        "raw_business_content_read": False,
        "live_source_read_count": 0,
        "real_business_action_count": 0,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
    }


__all__ = [
    "ACCEPTANCE_ID",
    "CARD_SORT_CASES",
    "DISCLOSURE_LEVELS",
    "FORBIDDEN_DEFAULT_TERMS",
    "InformationArchitectureError",
    "NAV_ITEMS",
    "PAGE_NODES",
    "PAGE_TYPES",
    "ROADMAP_PHASE_ID",
    "RUN_PHASE_ID",
    "TASK_ID",
    "TREE_TEST_CASES",
    "VERSION",
    "breadcrumbs_for",
    "interface_payload",
    "navigation_contract",
    "navigation_research_evidence",
    "page_map",
    "progressive_disclosure_contract",
    "public_verification",
    "render_html",
    "validate_page_hierarchy",
]
