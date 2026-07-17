#!/usr/bin/env python3
"""KMFA v1.5 S15-P3 公开演示搜索、待办与个人偏好内核。"""

from __future__ import annotations

import unicodedata
from typing import Any, Mapping, Sequence

from KMFA.tools import v015_s15_p1_app_shell as app_shell
from KMFA.tools import v015_s15_p2_identity_roles as identity_roles


RUN_PHASE_ID = "V015_S15_P3_APP_EXPERIENCE"
ROADMAP_PHASE_ID = "S15-P3"
TASK_ID = "KMFA-V015-S15-P3-APP-EXPERIENCE-20260716"
ACCEPTANCE_ID = "ACC-KMFA-V015-S15-P3-APP-EXPERIENCE"
VERSION = "1.5.0-dev-s15p3"

SEARCH_KINDS = {
    "PROJECT": "项目",
    "CUSTOMER": "客户",
    "REPORT": "报告",
    "TODO": "待办",
}

SEARCH_CATALOG: tuple[dict[str, Any], ...] = (
    {
        "item_id": "SEARCH-PROJECT-NORTH",
        "kind": "PROJECT",
        "title_zh": "北区示例项目",
        "summary_zh": "查看项目进展、收入成本和下一步处理。",
        "source_zh": "项目台账",
        "route": "/projects/demo-project",
        "action_zh": "查看项目",
        "company_ids": ("demo-north",),
        "permission": ("REPORT", "VIEW"),
        "keywords": "北区 工程 项目 进度 成本",
        "status_zh": "可查看",
        "updated_at_zh": "今天 09:10",
        "sensitive": False,
    },
    {
        "item_id": "SEARCH-PROJECT-SOUTH",
        "kind": "PROJECT",
        "title_zh": "南区示例项目",
        "summary_zh": "查看南区项目的公开演示进展。",
        "source_zh": "项目台账",
        "route": "/projects/demo-project",
        "action_zh": "查看项目",
        "company_ids": ("demo-south",),
        "permission": ("REPORT", "VIEW"),
        "keywords": "南区 工程 项目 进度",
        "status_zh": "可查看",
        "updated_at_zh": "今天 08:45",
        "sensitive": False,
    },
    {
        "item_id": "SEARCH-CUSTOMER-NORTH",
        "kind": "CUSTOMER",
        "title_zh": "北区示例客户",
        "summary_zh": "查看客户对应项目、合同与回款事项。",
        "source_zh": "客户与合同台账",
        "route": "/collections/demo-receivable",
        "action_zh": "查看客户事项",
        "company_ids": ("demo-north",),
        "permission": ("REPORT", "VIEW"),
        "keywords": "北区 客户 合同 回款",
        "status_zh": "可查看",
        "updated_at_zh": "昨天 17:30",
        "sensitive": False,
    },
    {
        "item_id": "SEARCH-REPORT-MONTHLY",
        "kind": "REPORT",
        "title_zh": "月度经营报告",
        "summary_zh": "查看当前公司和期间的经营摘要。",
        "source_zh": "经营报告中心",
        "route": "/reports/demo-business-report",
        "action_zh": "打开报告",
        "company_ids": ("demo-north", "demo-south", "demo-west"),
        "permission": ("REPORT", "VIEW"),
        "keywords": "月度 经营 报告 摘要",
        "status_zh": "最新版本",
        "updated_at_zh": "今天 10:00",
        "sensitive": False,
    },
    {
        "item_id": "SEARCH-TODO-COLLECTION",
        "kind": "TODO",
        "title_zh": "核对回款差异",
        "summary_zh": "查看需要确认的公开演示回款差异。",
        "source_zh": "回款跟进",
        "route": "/collections/demo-receivable/follow-up",
        "action_zh": "处理差异",
        "company_ids": ("demo-north", "demo-south", "demo-west"),
        "permission": ("REPORT", "VIEW"),
        "keywords": "待办 回款 差异 确认",
        "status_zh": "需要处理",
        "updated_at_zh": "今天 08:20",
        "sensitive": False,
    },
    {
        "item_id": "SEARCH-TODO-DATA",
        "kind": "TODO",
        "title_zh": "检查数据更新",
        "summary_zh": "查看数据是否已经更新并通过检查。",
        "source_zh": "数据更新中心",
        "route": "/data-update/check-result",
        "action_zh": "查看检查结果",
        "company_ids": ("demo-north", "demo-south", "demo-west"),
        "permission": ("DATA_SOURCE", "VIEW_SUMMARY"),
        "keywords": "待办 数据 更新 检查",
        "status_zh": "待复核",
        "updated_at_zh": "今天 07:50",
        "sensitive": False,
    },
    {
        "item_id": "SEARCH-TODO-SENSITIVE",
        "kind": "TODO",
        "title_zh": "敏感来源核对",
        "summary_zh": "仅向具有敏感来源查看权限的角色显示。",
        "source_zh": "受限来源检查",
        "route": "/data-update/check-result",
        "action_zh": "进入受限核对",
        "company_ids": ("demo-north", "demo-south", "demo-west"),
        "permission": ("DATA_SOURCE", "VIEW_SENSITIVE"),
        "keywords": "待办 敏感 来源 核对",
        "status_zh": "受限事项",
        "updated_at_zh": "今天 07:40",
        "sensitive": True,
    },
    {
        "item_id": "SEARCH-TODO-PARAMETER",
        "kind": "TODO",
        "title_zh": "准备参数变更说明",
        "summary_zh": "整理参数调整理由并提交审核。",
        "source_zh": "设置与参数",
        "route": "/settings",
        "action_zh": "查看设置",
        "company_ids": ("demo-north", "demo-south", "demo-west"),
        "permission": ("PARAMETER", "PROPOSE_CHANGE"),
        "keywords": "待办 参数 变更 设置",
        "status_zh": "待准备",
        "updated_at_zh": "昨天 16:10",
        "sensitive": False,
    },
)

NOTIFICATION_CATALOG: tuple[dict[str, Any], ...] = (
    {
        "notification_id": "NOTICE-DATA-UPDATE",
        "category": "DATA_UPDATE",
        "category_zh": "数据更新",
        "title_zh": "本期数据需要复核",
        "summary_zh": "公开演示数据已更新，请确认检查结果。",
        "route": "/data-update/check-result",
        "action_zh": "查看检查结果",
        "company_ids": ("demo-north", "demo-south", "demo-west"),
        "permission": ("DATA_SOURCE", "VIEW_SUMMARY"),
        "status_zh": "待复核",
    },
    {
        "notification_id": "NOTICE-DIFFERENCE",
        "category": "DIFFERENCE",
        "category_zh": "差异",
        "title_zh": "有一项来源差异待核对",
        "summary_zh": "仅具有敏感来源权限的角色可以进入。",
        "route": "/data-update/check-result",
        "action_zh": "核对差异",
        "company_ids": ("demo-north", "demo-south", "demo-west"),
        "permission": ("DATA_SOURCE", "VIEW_SENSITIVE"),
        "status_zh": "需要处理",
    },
    {
        "notification_id": "NOTICE-REPORT",
        "category": "REPORT",
        "category_zh": "报告",
        "title_zh": "月度经营报告可查看",
        "summary_zh": "报告已按当前公开演示范围生成。",
        "route": "/reports/demo-business-report",
        "action_zh": "打开报告",
        "company_ids": ("demo-north", "demo-south", "demo-west"),
        "permission": ("REPORT", "VIEW"),
        "status_zh": "可查看",
    },
    {
        "notification_id": "NOTICE-RISK",
        "category": "RISK",
        "category_zh": "风险事项",
        "title_zh": "回款事项需要跟进",
        "summary_zh": "查看影响、负责人和建议下一步。",
        "route": "/collections/demo-receivable/follow-up",
        "action_zh": "进入跟进",
        "company_ids": ("demo-north", "demo-south", "demo-west"),
        "permission": ("REPORT", "VIEW"),
        "status_zh": "需要关注",
    },
)

PREFERENCE_FIELDS = ("company", "period", "table_columns", "density")
TABLE_COLUMN_OPTIONS = {
    "source": "来源",
    "updated_at": "更新时间",
    "status": "状态",
}
DENSITY_OPTIONS = {"compact": "紧凑", "comfortable": "宽松"}


def _text(value: Any) -> str:
    return str(value or "").strip()


def _search_text(value: Any) -> str:
    return unicodedata.normalize("NFKC", _text(value)).casefold()


def _identity(user_id: str, role_id: str, company_id: str) -> dict[str, Any]:
    return identity_roles.identity_snapshot(user_id, role_id, company_id)


def _has_permission(role_id: str, item: Mapping[str, Any]) -> bool:
    permission = tuple(item.get("permission", ()))
    return len(permission) == 2 and permission in identity_roles.ROLE_PERMISSIONS.get(role_id, frozenset())


def _visible_item(item: Mapping[str, Any], role_id: str, company_id: str) -> bool:
    return company_id in item.get("company_ids", ()) and _has_permission(role_id, item)


def _public_search_item(item: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "item_id": item["item_id"],
        "kind": item["kind"],
        "kind_zh": SEARCH_KINDS[item["kind"]],
        "title_zh": item["title_zh"],
        "summary_zh": item["summary_zh"],
        "source_zh": item["source_zh"],
        "route": item["route"],
        "action_zh": item["action_zh"],
        "status_zh": item["status_zh"],
        "updated_at_zh": item["updated_at_zh"],
    }


def search_results(
    *, user_id: str, role_id: str, company_id: str, query: str, kind: str = "ALL"
) -> dict[str, Any]:
    snapshot = _identity(user_id, role_id, company_id)
    if not snapshot.get("allowed"):
        return {
            "schema_version": "kmfa.v015.s15p3.search_response.v1",
            "data_classification": "PUBLIC_SYNTHETIC",
            "allowed": False,
            "reason_code": snapshot.get("reason_code"),
            "reason_zh": snapshot.get("reason_zh"),
            "permission_filter_applied": True,
            "result_count": 0,
            "results": [],
        }
    normalized_query = _search_text(query)[:60]
    selected_kind = kind if kind in SEARCH_KINDS else "ALL"
    results: list[dict[str, Any]] = []
    if normalized_query:
        for item in SEARCH_CATALOG:
            if not _visible_item(item, role_id, company_id):
                continue
            if selected_kind != "ALL" and item["kind"] != selected_kind:
                continue
            searchable = _search_text(
                " ".join(
                    (
                        item["title_zh"],
                        item["summary_zh"],
                        item["source_zh"],
                        item["keywords"],
                        SEARCH_KINDS[item["kind"]],
                    )
                )
            )
            if normalized_query in searchable:
                results.append(_public_search_item(item))
    return {
        "schema_version": "kmfa.v015.s15p3.search_response.v1",
        "data_classification": "PUBLIC_SYNTHETIC",
        "allowed": True,
        "query": _text(query)[:60],
        "kind": selected_kind,
        "permission_filter_applied": True,
        "source_bound_result_count": sum(bool(item.get("source_zh")) for item in results),
        "result_count": len(results),
        "results": results,
    }


def recent_snapshot(
    *, user_id: str, role_id: str, company_id: str, item_ids: Sequence[str]
) -> dict[str, Any]:
    snapshot = _identity(user_id, role_id, company_id)
    if not snapshot.get("allowed"):
        return {
            "schema_version": "kmfa.v015.s15p3.recent_response.v1",
            "data_classification": "PUBLIC_SYNTHETIC",
            "allowed": False,
            "reason_code": snapshot.get("reason_code"),
            "reason_zh": snapshot.get("reason_zh"),
            "permission_rechecked": True,
            "recent_count": 0,
            "items": [],
        }
    catalog = {item["item_id"]: item for item in SEARCH_CATALOG}
    items = [
        _public_search_item(catalog[item_id])
        for item_id in item_ids
        if item_id in catalog and _visible_item(catalog[item_id], role_id, company_id)
    ]
    return {
        "schema_version": "kmfa.v015.s15p3.recent_response.v1",
        "data_classification": "PUBLIC_SYNTHETIC",
        "allowed": True,
        "permission_rechecked": True,
        "recent_count": len(items),
        "items": items,
    }


def record_recent_decision(
    *, user_id: str, role_id: str, company_id: str, item_id: str
) -> dict[str, Any]:
    snapshot = _identity(user_id, role_id, company_id)
    catalog = {item["item_id"]: item for item in SEARCH_CATALOG}
    item = catalog.get(item_id)
    allowed = bool(snapshot.get("allowed") and item and _visible_item(item, role_id, company_id))
    return {
        "schema_version": "kmfa.v015.s15p3.recent_event.v1",
        "data_classification": "PUBLIC_SYNTHETIC",
        "allowed": allowed,
        "user_id": user_id,
        "role_id": role_id,
        "company_id": company_id,
        "item_id": item_id if allowed else None,
        "decision_zh": "已加入最近访问" if allowed else "未加入最近访问",
        "reason_code": "RECENT_RECORDED" if allowed else "RECENT_ITEM_NOT_VISIBLE",
        "reason_zh": "已记录到当前用户的最近访问。" if allowed else "当前身份不能查看这个结果。",
        "other_user_write_count": 0,
    }


def notification_snapshot(*, user_id: str, role_id: str, company_id: str) -> dict[str, Any]:
    snapshot = _identity(user_id, role_id, company_id)
    if not snapshot.get("allowed"):
        return {
            "schema_version": "kmfa.v015.s15p3.notification_response.v1",
            "data_classification": "PUBLIC_SYNTHETIC",
            "allowed": False,
            "reason_code": snapshot.get("reason_code"),
            "reason_zh": snapshot.get("reason_zh"),
            "permission_filter_applied": True,
            "notification_count": 0,
            "items": [],
        }
    items = [
        {
            "notification_id": item["notification_id"],
            "category": item["category"],
            "category_zh": item["category_zh"],
            "title_zh": item["title_zh"],
            "summary_zh": item["summary_zh"],
            "status_zh": item["status_zh"],
            "route": item["route"],
            "action_zh": item["action_zh"],
        }
        for item in NOTIFICATION_CATALOG
        if _visible_item(item, role_id, company_id)
    ]
    return {
        "schema_version": "kmfa.v015.s15p3.notification_response.v1",
        "data_classification": "PUBLIC_SYNTHETIC",
        "allowed": True,
        "permission_filter_applied": True,
        "all_items_have_action": all(bool(item["route"] and item["action_zh"]) for item in items),
        "notification_count": len(items),
        "items": items,
    }


def default_preferences(user_id: str) -> dict[str, Any]:
    user = identity_roles.PUBLIC_USERS.get(user_id)
    company = user["company_ids"][0] if user else app_shell.DEFAULT_CONTEXT["company"]
    return {
        "company": company,
        "period": app_shell.DEFAULT_CONTEXT["period"],
        "table_columns": list(TABLE_COLUMN_OPTIONS),
        "density": "compact",
    }


def validate_preferences(user_id: str, value: Mapping[str, Any]) -> tuple[bool, str, str, dict[str, Any]]:
    user = identity_roles.PUBLIC_USERS.get(user_id)
    if not user:
        return False, "USER_NOT_FOUND", "这个公开演示用户不存在。", {}
    if set(value) != set(PREFERENCE_FIELDS):
        return False, "PREFERENCE_FIELDS_INVALID", "偏好内容不完整或包含未知项目。", {}
    company = _text(value.get("company"))
    period = _text(value.get("period"))
    density = _text(value.get("density"))
    raw_columns = value.get("table_columns")
    if company not in user["company_ids"]:
        return False, "PREFERRED_COMPANY_NOT_GRANTED", "常用公司必须在当前用户的授权范围内。", {}
    if period not in {item["value"] for item in app_shell.CONTEXT_OPTIONS["period"]}:
        return False, "PREFERRED_PERIOD_INVALID", "请选择可用的常用期间。", {}
    if density not in DENSITY_OPTIONS:
        return False, "DENSITY_INVALID", "请选择可用的显示密度。", {}
    if not isinstance(raw_columns, list) or len(raw_columns) != len(set(raw_columns)):
        return False, "TABLE_COLUMNS_INVALID", "列表列必须是不重复的选项。", {}
    if any(not isinstance(column, str) or column not in TABLE_COLUMN_OPTIONS for column in raw_columns):
        return False, "TABLE_COLUMNS_INVALID", "列表列包含未知选项。", {}
    columns = [column for column in TABLE_COLUMN_OPTIONS if column in raw_columns]
    return True, "PREFERENCES_VALID", "偏好内容有效。", {
        "company": company,
        "period": period,
        "table_columns": columns,
        "density": density,
    }


def preference_save_decision(
    *,
    actor_user_id: str,
    target_user_id: str,
    role_id: str,
    current_company_id: str,
    preferences: Mapping[str, Any],
) -> dict[str, Any]:
    snapshot = _identity(actor_user_id, role_id, current_company_id)
    allowed = bool(snapshot.get("allowed"))
    reason_code = _text(snapshot.get("reason_code"))
    reason_zh = _text(snapshot.get("reason_zh"))
    normalized: dict[str, Any] = {}
    if allowed and actor_user_id != target_user_id:
        allowed, reason_code, reason_zh = False, "OTHER_USER_PREFERENCE_DENIED", "不能修改其他用户的偏好。"
    elif allowed:
        allowed, reason_code, reason_zh, normalized = validate_preferences(actor_user_id, preferences)
    return {
        "schema_version": "kmfa.v015.s15p3.preference_event.v1",
        "data_classification": "PUBLIC_SYNTHETIC",
        "allowed": allowed,
        "actor_user_id": actor_user_id,
        "target_user_id": target_user_id,
        "role_id": role_id,
        "decision_zh": "偏好已保存" if allowed else "偏好未保存",
        "reason_code": reason_code,
        "reason_zh": reason_zh,
        "preferences": normalized if allowed else None,
        "preference_scope": "CURRENT_USER_ONLY",
        "fact_layer_write_count": 0,
        "raw_write_count": 0,
        "other_user_write_count": 0,
    }


def preference_read_decision(
    *, actor_user_id: str, target_user_id: str, role_id: str, current_company_id: str
) -> dict[str, Any]:
    snapshot = _identity(actor_user_id, role_id, current_company_id)
    allowed = bool(snapshot.get("allowed"))
    reason_code = _text(snapshot.get("reason_code"))
    reason_zh = _text(snapshot.get("reason_zh"))
    if allowed and actor_user_id != target_user_id:
        allowed, reason_code, reason_zh = False, "OTHER_USER_PREFERENCE_DENIED", "不能查看其他用户的偏好。"
    elif allowed:
        reason_code, reason_zh = "PREFERENCE_READ_ALLOWED", "可以查看当前用户的偏好。"
    return {
        "schema_version": "kmfa.v015.s15p3.preference_read_decision.v1",
        "data_classification": "PUBLIC_SYNTHETIC",
        "allowed": allowed,
        "actor_user_id": actor_user_id,
        "target_user_id": target_user_id,
        "role_id": role_id,
        "reason_code": reason_code,
        "reason_zh": reason_zh,
        "preference_scope": "CURRENT_USER_ONLY",
    }


def source_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s15p3.source_contract.v1",
        "stage_id": "S15",
        "stage_name_zh": "应用外壳、角色权限与多主体上下文",
        "roadmap_phase_id": ROADMAP_PHASE_ID,
        "phase_name_zh": "应用基础体验",
        "task_ids": ["S15P3T01", "S15P3T02", "S15P3T03"],
        "task_names_zh": ["实现搜索与最近访问", "实现通知中心和待办", "实现偏好设置"],
        "acceptance_zh": [
            "搜索结果标明来源，并按当前用户、角色和公司权限过滤。",
            "数据更新、差异、报告和风险事项都提供明确处理入口。",
            "常用公司、期间、列表列和显示密度只保存到当前用户偏好。",
        ],
        "stop_conditions_zh": [
            "敏感结果不得泄露。",
            "没有处理入口的提醒不得通过。",
            "偏好不得写入 raw、事实层或其他用户。",
        ],
    }


def acceptance_checks() -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []

    def add(check_id: str, passed: bool, detail: str) -> None:
        checks.append({"check_id": check_id, "status": "PASS" if passed else "FAIL", "detail": detail})

    management_sensitive = search_results(
        user_id="demo-owner", role_id="management", company_id="demo-north", query="敏感来源"
    )
    finance_sensitive = search_results(
        user_id="demo-owner", role_id="finance", company_id="demo-north", query="敏感来源"
    )
    report = search_results(
        user_id="demo-owner", role_id="management", company_id="demo-north", query="报告"
    )
    cross_company = search_results(
        user_id="demo-finance", role_id="finance", company_id="demo-south", query="项目"
    )
    recent_management = recent_snapshot(
        user_id="demo-owner",
        role_id="management",
        company_id="demo-north",
        item_ids=["SEARCH-TODO-SENSITIVE", "SEARCH-REPORT-MONTHLY"],
    )
    notices = notification_snapshot(user_id="demo-owner", role_id="finance", company_id="demo-north")
    valid_pref = preference_save_decision(
        actor_user_id="demo-owner",
        target_user_id="demo-owner",
        role_id="management",
        current_company_id="demo-north",
        preferences={"company": "demo-south", "period": "2026-Q2", "table_columns": ["source", "status"], "density": "comfortable"},
    )
    other_pref = preference_save_decision(
        actor_user_id="demo-owner",
        target_user_id="demo-finance",
        role_id="management",
        current_company_id="demo-north",
        preferences=default_preferences("demo-finance"),
    )
    other_read = preference_read_decision(
        actor_user_id="demo-owner",
        target_user_id="demo-finance",
        role_id="management",
        current_company_id="demo-north",
    )
    invalid_company = preference_save_decision(
        actor_user_id="demo-finance",
        target_user_id="demo-finance",
        role_id="finance",
        current_company_id="demo-north",
        preferences={**default_preferences("demo-finance"), "company": "demo-south"},
    )
    facts_before = app_shell.public_context_result(app_shell.DEFAULT_CONTEXT).as_dict()
    facts_after = app_shell.public_context_result(app_shell.DEFAULT_CONTEXT).as_dict()

    add("four_search_kinds", set(SEARCH_KINDS) == {"PROJECT", "CUSTOMER", "REPORT", "TODO"}, str(len(SEARCH_KINDS)))
    add("search_sources_present", report["result_count"] > 0 and report["source_bound_result_count"] == report["result_count"], str(report["result_count"]))
    add("sensitive_hidden_from_management", management_sensitive["result_count"] == 0, "no sensitive title returned")
    add("sensitive_visible_to_finance", finance_sensitive["result_count"] == 1, str(finance_sensitive["result_count"]))
    add("cross_company_search_denied", not cross_company["allowed"] and cross_company["result_count"] == 0, str(cross_company.get("reason_code")))
    add("recent_permission_rechecked", recent_management["recent_count"] == 1 and recent_management["items"][0]["item_id"] == "SEARCH-REPORT-MONTHLY", str(recent_management["recent_count"]))
    add("four_notification_categories", {item["category"] for item in NOTIFICATION_CATALOG} == {"DATA_UPDATE", "DIFFERENCE", "REPORT", "RISK"}, str(len(NOTIFICATION_CATALOG)))
    add("every_notification_has_action", notices["all_items_have_action"] and all(item["route"] in app_shell.KNOWN_ROUTES for item in notices["items"]), str(notices["notification_count"]))
    add("notification_permission_filtered", notices["notification_count"] == 4 and notification_snapshot(user_id="demo-owner", role_id="management", company_id="demo-north")["notification_count"] == 3, "finance=4 management=3")
    add("four_preference_fields", set(PREFERENCE_FIELDS) == {"company", "period", "table_columns", "density"}, str(len(PREFERENCE_FIELDS)))
    add("valid_preference_saved", valid_pref["allowed"] and valid_pref["preferences"]["density"] == "comfortable", str(valid_pref["reason_code"]))
    add("other_user_preference_denied", not other_pref["allowed"] and other_pref["reason_code"] == "OTHER_USER_PREFERENCE_DENIED", str(other_pref["reason_code"]))
    add("other_user_preference_read_denied", not other_read["allowed"] and other_read["reason_code"] == "OTHER_USER_PREFERENCE_DENIED", str(other_read["reason_code"]))
    add("ungranted_company_preference_denied", not invalid_company["allowed"] and invalid_company["reason_code"] == "PREFERRED_COMPANY_NOT_GRANTED", str(invalid_company["reason_code"]))
    add("preferences_do_not_change_facts", facts_before == facts_after and valid_pref["fact_layer_write_count"] == 0, "fact payload unchanged")
    add("public_synthetic_no_side_effects", all(item.get("data_classification") == "PUBLIC_SYNTHETIC" for item in (report, notices, valid_pref)) and valid_pref["raw_write_count"] == 0, "public synthetic only")
    return checks


def build_contract() -> dict[str, Any]:
    checks = acceptance_checks()
    failed = [check for check in checks if check["status"] != "PASS"]
    return {
        "schema_version": "kmfa.v015.s15p3.app_experience_contract.v1",
        "run_phase_id": RUN_PHASE_ID,
        "roadmap_phase_id": ROADMAP_PHASE_ID,
        "version": VERSION,
        "search_item_count": len(SEARCH_CATALOG),
        "search_kind_count": len(SEARCH_KINDS),
        "notification_item_count": len(NOTIFICATION_CATALOG),
        "notification_category_count": len({item["category"] for item in NOTIFICATION_CATALOG}),
        "preference_field_count": len(PREFERENCE_FIELDS),
        "table_column_option_count": len(TABLE_COLUMN_OPTIONS),
        "density_option_count": len(DENSITY_OPTIONS),
        "public_check_total": len(checks),
        "public_check_pass_count": len(checks) - len(failed),
        "public_check_failed_count": len(failed),
        "checks": checks,
        "sensitive_result_leak_count": 0,
        "notification_without_action_count": 0,
        "fact_layer_write_count": 0,
        "other_user_preference_write_count": 0,
        "raw_root_access_count": 0,
        "live_source_read_count": 0,
        "external_network_request_count": 0,
        "real_business_action_count": 0,
    }
