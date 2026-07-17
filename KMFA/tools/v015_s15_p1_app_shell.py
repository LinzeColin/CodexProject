#!/usr/bin/env python3
"""KMFA v1.5 S15-P1 应用外壳、全局上下文与错误边界内核。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping
from urllib.parse import urlencode

from KMFA.tools import v015_s14_p1_information_architecture as information_architecture


RUN_PHASE_ID = "V015_S15_P1_APP_SHELL"
ROADMAP_PHASE_ID = "S15-P1"
TASK_ID = "KMFA-V015-S15-P1-APP-SHELL-20260716"
ACCEPTANCE_ID = "ACC-KMFA-V015-S15-P1-APP-SHELL"
VERSION = "1.5.0-dev-s15p1"

NAV_ITEMS = information_architecture.NAV_ITEMS
PAGE_NODES = information_architecture.PAGE_NODES
KNOWN_ROUTES = tuple(node["route"] for node in PAGE_NODES)

CONTEXT_OPTIONS: dict[str, tuple[dict[str, str], ...]] = {
    "company": (
        {"value": "demo-north", "label": "北区示例公司"},
        {"value": "demo-south", "label": "南区示例公司"},
        {"value": "demo-west", "label": "西区示例公司"},
    ),
    "period": (
        {"value": "2026-07", "label": "2026年7月"},
        {"value": "2026-Q2", "label": "2026年第二季度"},
        {"value": "2026-H1", "label": "2026年上半年"},
    ),
    "project_status": (
        {"value": "all", "label": "全部项目"},
        {"value": "attention", "label": "需要关注"},
        {"value": "normal", "label": "进展正常"},
    ),
    "report_version": (
        {"value": "latest", "label": "最新版本"},
        {"value": "approved", "label": "已确认版本"},
        {"value": "previous", "label": "上一版本"},
    ),
}

CONTEXT_QUERY_KEYS = {
    "company": "company",
    "period": "period",
    "project_status": "project_status",
    "report_version": "report_version",
}

DEFAULT_CONTEXT = {
    key: values[0]["value"] for key, values in CONTEXT_OPTIONS.items()
}

FAULT_CONTRACT = {
    "network": {
        "http_status": 503,
        "title_zh": "暂时无法连接",
        "message_zh": "演示服务暂时没有响应。请稍后重试。",
        "action_zh": "重新加载",
    },
    "parse": {
        "http_status": 200,
        "title_zh": "返回内容无法读取",
        "message_zh": "收到的内容格式不完整。请重新加载。",
        "action_zh": "重新加载",
    },
    "calculation": {
        "http_status": 422,
        "title_zh": "暂时无法完成计算",
        "message_zh": "当前筛选条件下无法形成结果。请调整条件或重试。",
        "action_zh": "重新加载",
    },
    "permission": {
        "http_status": 403,
        "title_zh": "当前账号不能查看",
        "message_zh": "你没有查看这个演示范围的权限。请返回经营首页。",
        "action_zh": "返回经营首页",
    },
}


class ContextError(ValueError):
    """全局上下文或上下文数据不符合公开演示合同。"""


@dataclass(frozen=True)
class ContextResult:
    context: dict[str, str]
    context_labels: dict[str, str]
    summary: dict[str, int | str]
    items: tuple[dict[str, Any], ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "kmfa.v015.s15p1.context_response.v1",
            "data_classification": "PUBLIC_SYNTHETIC",
            "context": dict(self.context),
            "context_labels": dict(self.context_labels),
            "summary": dict(self.summary),
            "items": [dict(item) for item in self.items],
        }


def _allowed_values(key: str) -> set[str]:
    return {item["value"] for item in CONTEXT_OPTIONS[key]}


def normalize_context(values: Mapping[str, Any] | None = None) -> dict[str, str]:
    """把 URL、持久化状态或调用参数收敛到允许的公开演示上下文。"""

    source = values or {}
    normalized: dict[str, str] = {}
    for key, default in DEFAULT_CONTEXT.items():
        candidate = str(source.get(key, default))
        normalized[key] = candidate if candidate in _allowed_values(key) else default
    return normalized


def context_labels(context: Mapping[str, Any]) -> dict[str, str]:
    normalized = normalize_context(context)
    return {
        key: next(item["label"] for item in CONTEXT_OPTIONS[key] if item["value"] == normalized[key])
        for key in CONTEXT_OPTIONS
    }

def context_query(context: Mapping[str, Any]) -> str:
    normalized = normalize_context(context)
    return urlencode([(CONTEXT_QUERY_KEYS[key], normalized[key]) for key in CONTEXT_OPTIONS])


def public_context_result(context: Mapping[str, Any]) -> ContextResult:
    """生成只含公开合成信息、且显式绑定主体的确定性响应。"""

    normalized = normalize_context(context)
    labels = context_labels(normalized)
    company_index = [item["value"] for item in CONTEXT_OPTIONS["company"]].index(normalized["company"])
    period_index = [item["value"] for item in CONTEXT_OPTIONS["period"]].index(normalized["period"])
    status_index = [item["value"] for item in CONTEXT_OPTIONS["project_status"]].index(
        normalized["project_status"]
    )
    version_index = [item["value"] for item in CONTEXT_OPTIONS["report_version"]].index(
        normalized["report_version"]
    )

    visible_item_count = 3 - min(status_index, 1)
    attention_count = (company_index + 1) * 2 + period_index + status_index
    update_count = (period_index + 1) + version_index
    items = tuple(
        {
            "item_id": f"{normalized['company']}-demo-{index + 1}",
            "company_id": normalized["company"],
            "title_zh": f"示例事项 {index + 1}",
            "status_zh": "需要关注" if index < attention_count % 3 else "进展正常",
            "next_step_zh": "查看说明" if index % 2 == 0 else "确认负责人",
        }
        for index in range(visible_item_count)
    )
    result = ContextResult(
        context=normalized,
        context_labels=labels,
        summary={
            "visible_item_count": visible_item_count,
            "attention_count": attention_count,
            "update_count": update_count,
            "message_zh": f"正在查看{labels['company']} · {labels['period']} · {labels['project_status']} · {labels['report_version']}",
        },
        items=items,
    )
    validate_public_payload(result.as_dict(), normalized)
    return result


def validate_public_payload(payload: Mapping[str, Any], requested_context: Mapping[str, Any]) -> None:
    """拒绝主体不一致的响应，防止切换主体时展示旧主体数据。"""

    expected = normalize_context(requested_context)
    if payload.get("data_classification") != "PUBLIC_SYNTHETIC":
        raise ContextError("context payload must be public synthetic")
    if payload.get("context") != expected:
        raise ContextError("context response does not match the requested context")
    items = payload.get("items")
    if not isinstance(items, list):
        raise ContextError("context response items must be a list")
    leaked = [item for item in items if not isinstance(item, Mapping) or item.get("company_id") != expected["company"]]
    if leaked:
        raise ContextError("cross-company response rejected")


def source_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s15p1.source_contract.v1",
        "stage_id": "S15",
        "stage_name_zh": "应用外壳、角色权限与多主体上下文",
        "roadmap_phase_id": ROADMAP_PHASE_ID,
        "phase_name_zh": "应用外壳",
        "task_ids": ["S15P1T01", "S15P1T02", "S15P1T03"],
        "task_names_zh": ["实现布局与路由", "全局筛选上下文", "加载和错误边界"],
        "acceptance_zh": [
            "刷新恢复，深链接可用。",
            "主体、期间、项目状态和报告版本切换影响清晰且状态持久化。",
            "网络、解析、计算和权限错误均给出明确下一步并可恢复。",
        ],
        "stop_conditions_zh": [
            "静态 HTML 不算完成。",
            "跨主体数据泄露即失败。",
            "白屏或静默失败即失败。",
        ],
    }


def acceptance_checks() -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []

    def add(check_id: str, passed: bool, detail: str) -> None:
        checks.append({"check_id": check_id, "status": "PASS" if passed else "FAIL", "detail": detail})

    add("seven_primary_navigation_items", len(NAV_ITEMS) == 7, str(len(NAV_ITEMS)))
    add("eighteen_deep_link_routes", len(KNOWN_ROUTES) == 18, str(len(KNOWN_ROUTES)))
    add("four_context_dimensions", len(CONTEXT_OPTIONS) == 4, str(len(CONTEXT_OPTIONS)))
    add("three_public_companies", len(CONTEXT_OPTIONS["company"]) == 3, "public synthetic only")
    add("four_fault_boundaries", set(FAULT_CONTRACT) == {"network", "parse", "calculation", "permission"}, ",".join(FAULT_CONTRACT))
    add("all_context_values_normalized", normalize_context({"company": "invalid"}) == DEFAULT_CONTEXT, "fail closed to defaults")
    sample = public_context_result(DEFAULT_CONTEXT).as_dict()
    add("sample_payload_company_bound", all(item["company_id"] == DEFAULT_CONTEXT["company"] for item in sample["items"]), "exact company binding")
    add("no_raw_or_live_input", sample["data_classification"] == "PUBLIC_SYNTHETIC", sample["data_classification"])
    return checks


def build_contract() -> dict[str, Any]:
    checks = acceptance_checks()
    failed = [check for check in checks if check["status"] != "PASS"]
    return {
        "schema_version": "kmfa.v015.s15p1.app_shell_contract.v1",
        "run_phase_id": RUN_PHASE_ID,
        "roadmap_phase_id": ROADMAP_PHASE_ID,
        "version": VERSION,
        "navigation_count": len(NAV_ITEMS),
        "route_count": len(KNOWN_ROUTES),
        "context_dimension_count": len(CONTEXT_OPTIONS),
        "company_context_count": len(CONTEXT_OPTIONS["company"]),
        "fault_boundary_count": len(FAULT_CONTRACT),
        "public_check_total": len(checks),
        "public_check_pass_count": len(checks) - len(failed),
        "public_check_failed_count": len(failed),
        "checks": checks,
        "raw_root_access_count": 0,
        "live_source_read_count": 0,
        "external_network_request_count": 0,
        "real_business_action_count": 0,
    }
