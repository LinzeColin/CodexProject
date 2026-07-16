from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from typing import Any


TARGET_VERSION = "v0.2.5"
STAGE_ID = "Stage 6"
PHASE_ID = "6.1"
PHASE_NAME = "导航与 alias"
CONTRACT_ID = "PFI-V025-STAGE6-PHASE61-NAVIGATION-ALIAS"
ACCEPTANCE_ID = "ACC-PFI-V025-S6-P61-NAVIGATION-ALIAS"
TASK_IDS = ["S6-P1-T1", "S6-P1-T2", "S6-P1-T3", "S6-P1-T4"]
CANONICAL_STRATEGY_LAB_ROUTE = "/market-research/strategy-lab"

OFFICIAL_PRIMARY_NAV: list[dict[str, object]] = [
    {"index": 1, "label": "首页总览", "workspace": "home", "routeAlias": "/overview", "icon": "⌂"},
    {"index": 2, "label": "账户与资产", "workspace": "accounts", "routeAlias": "/accounts", "icon": "◫"},
    {"index": 3, "label": "账本流水", "workspace": "ledger", "routeAlias": "/ledger", "icon": "≋"},
    {"index": 4, "label": "投资管理", "workspace": "investment", "routeAlias": "/investment", "icon": "↗"},
    {"index": 5, "label": "消费管理", "workspace": "consumption", "routeAlias": "/consumption", "icon": "◌"},
    {"index": 6, "label": "数据源与上传", "workspace": "sync", "routeAlias": "/data", "icon": "⇄"},
    {"index": 7, "label": "建议与复盘", "workspace": "recommendations", "routeAlias": "/review", "icon": "✦"},
    {"index": 8, "label": "报告与洞察", "workspace": "insights", "routeAlias": "/reports", "icon": "▣"},
    {"index": 9, "label": "市场与研究", "workspace": "market_research", "routeAlias": "/market-research", "icon": "⌁"},
    {"index": 10, "label": "设置", "workspace": "settings", "routeAlias": "/settings", "icon": "⚙"},
]

ALIAS_MATRIX: list[dict[str, object]] = [
    {
        "label": "首页",
        "routeAlias": "/home",
        "resolvedRouteAlias": "/overview",
        "targetWorkspace": "home",
        "aliasClass": "command_or_compatibility_alias",
        "primaryEntryAllowed": False,
    },
    {
        "label": "市场",
        "routeAlias": "/market",
        "resolvedRouteAlias": "/market-research/market",
        "targetWorkspace": "market_research",
        "aliasClass": "command_or_compatibility_alias",
        "primaryEntryAllowed": False,
    },
    {
        "label": "研究",
        "routeAlias": "/research",
        "resolvedRouteAlias": "/market-research/research",
        "targetWorkspace": "market_research",
        "aliasClass": "command_or_compatibility_alias",
        "primaryEntryAllowed": False,
    },
    {
        "label": "持仓",
        "routeAlias": "/holdings",
        "resolvedRouteAlias": "/investment/holdings",
        "targetWorkspace": "investment",
        "aliasClass": "command_or_compatibility_alias",
        "primaryEntryAllowed": False,
    },
    {
        "label": "策略实验室",
        "routeAlias": "/strategy-lab",
        "resolvedRouteAlias": CANONICAL_STRATEGY_LAB_ROUTE,
        "targetWorkspace": "market_research",
        "aliasClass": "command_or_compatibility_alias",
        "primaryEntryAllowed": False,
    },
    {
        "label": "策略实验室",
        "routeAlias": "/investment/strategy-lab",
        "resolvedRouteAlias": CANONICAL_STRATEGY_LAB_ROUTE,
        "targetWorkspace": "market_research",
        "aliasClass": "command_or_compatibility_alias",
        "primaryEntryAllowed": False,
    },
    {
        "label": "数据与系统",
        "routeAlias": "/data-system",
        "resolvedRouteAlias": "/settings/data-system",
        "targetWorkspace": "settings",
        "aliasClass": "command_or_compatibility_alias",
        "primaryEntryAllowed": False,
    },
]

ALIAS_ROUTE_TARGETS = {str(item["routeAlias"]): str(item["resolvedRouteAlias"]) for item in ALIAS_MATRIX}


class _NavigationDOMParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.primary_nodes: list[dict[str, str]] = []
        self.mobile_only_nodes: list[dict[str, str]] = []
        self.nojs_routes: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = {key: value or "" for key, value in attrs}
        is_primary = attributes.get("data-primary-entry") == "true"
        is_mobile_primary = attributes.get("data-mobile-primary-entry") == "true"
        if is_primary:
            self.primary_nodes.append(attributes)
        if is_mobile_primary and not is_primary:
            self.mobile_only_nodes.append(attributes)
        if tag == "a" and "data-no-js-route" in attributes:
            self.nojs_routes.append(attributes["data-no-js-route"])


def audit_v025_stage6_phase61_index(index_path: Path | str) -> dict[str, Any]:
    path = Path(index_path)
    parser = _NavigationDOMParser()
    parser.feed(path.read_text(encoding="utf-8"))

    expected_routes = [str(item["routeAlias"]) for item in OFFICIAL_PRIMARY_NAV]
    primary_routes = [item.get("data-route-alias", "") for item in parser.primary_nodes]
    mobile_routes = [
        item.get("data-route-alias", "")
        for item in parser.primary_nodes
        if item.get("data-mobile-primary-entry") == "true"
        and item.get("data-mobile-workspace") == item.get("data-workspace")
    ]
    alias_inputs = set(ALIAS_ROUTE_TARGETS)
    alias_primary_routes = [route for route in primary_routes if route in alias_inputs]
    checks = {
        "unique_primary_node_count": len(parser.primary_nodes) == 10,
        "primary_route_order": primary_routes == expected_routes,
        "desktop_primary_count": len(parser.primary_nodes) == 10,
        "mobile_primary_count": len(mobile_routes) == 10 and mobile_routes == expected_routes,
        "nojs_primary_count": len(parser.nojs_routes) == 10 and parser.nojs_routes == expected_routes,
        "duplicate_responsive_primary_node_count": len(parser.mobile_only_nodes) == 0,
        "alias_primary_node_count": len(alias_primary_routes) == 0,
    }
    return {
        "schema": "PFIV025Stage6Phase61DOMAuditV1",
        "contract_id": CONTRACT_ID,
        "status": "pass" if all(checks.values()) else "fail",
        "unique_primary_node_count": len(parser.primary_nodes),
        "desktop_primary_count": len(parser.primary_nodes),
        "mobile_primary_count": len(mobile_routes),
        "nojs_primary_count": len(parser.nojs_routes),
        "duplicate_responsive_primary_node_count": len(parser.mobile_only_nodes),
        "alias_primary_node_count": len(alias_primary_routes),
        "primary_routes": primary_routes,
        "nojs_routes": parser.nojs_routes,
        "checks": checks,
    }


def build_v025_stage6_phase61_contract(project_root: Path | str) -> dict[str, Any]:
    root = Path(project_root)
    index_path = root / "web" / "index.html"
    dom_audit = audit_v025_stage6_phase61_index(index_path)
    if dom_audit["status"] != "pass":
        raise ValueError("v0.2.5 Stage 6 Phase 6.1 DOM audit failed")
    return {
        "schema": "PFIV025Stage6Phase61ContractV1",
        "version": TARGET_VERSION,
        "stage": STAGE_ID,
        "phase": PHASE_ID,
        "phase_name": PHASE_NAME,
        "contract_id": CONTRACT_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "acceptance_id_origin": "project_governance_assigned_not_source_roadmap",
        "task_ids": TASK_IDS,
        "official_primary_entries": OFFICIAL_PRIMARY_NAV,
        "alias_matrix": ALIAS_MATRIX,
        "alias_route_targets": ALIAS_ROUTE_TARGETS,
        "canonical_strategy_lab_route": CANONICAL_STRATEGY_LAB_ROUTE,
        "dom_audit": dom_audit,
        "phase_6_1_status": "candidate_pass",
        "phase_6_2_status": "not_started",
        "phase_6_3_status": "not_started",
        "stage_6_status": "in_progress",
        "stage_6_whole_stage_review_status": "not_started",
        "stage_7_status": "not_started",
        "finder_used": False,
        "external_network_performed": False,
        "push_performed": False,
        "app_install_performed": False,
        "database_changed": False,
        "financial_data_read": False,
        "financial_data_mutated": False,
    }
