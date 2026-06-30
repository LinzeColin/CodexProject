from __future__ import annotations

from dataclasses import asdict, dataclass


TARGET_VERSION = "v0.2.4"
SOURCE_PACKAGE_VERSION = "v0.2.3-repair"
STAGE_ID = "Stage 3"
PHASE_3_1_ID = "3.1"
PHASE_3_1_NAME = "导航合同"
REPAIR_LABEL = "PFI v0.2.3 Repair"
NAVIGATION_CONTRACT_VERSION = "PFI-V024-STAGE3-PHASE31-NAVIGATION"

OFFICIAL_PRIMARY_NAV = [
    {"index": 1, "label": "首页总览", "workspace": "home", "routeAlias": "/home", "icon": "⌂"},
    {"index": 2, "label": "账户与资产", "workspace": "accounts", "routeAlias": "/accounts", "icon": "◫"},
    {"index": 3, "label": "账本流水", "workspace": "ledger", "routeAlias": "/ledger", "icon": "≋"},
    {"index": 4, "label": "投资管理", "workspace": "investment", "routeAlias": "/investment", "icon": "↗"},
    {"index": 5, "label": "消费管理", "workspace": "consumption", "routeAlias": "/consumption", "icon": "◌"},
    {"index": 6, "label": "数据源与上传", "workspace": "sync", "routeAlias": "/sources-upload", "icon": "⇄"},
    {"index": 7, "label": "建议与复盘", "workspace": "recommendations", "routeAlias": "/review", "icon": "✦"},
    {"index": 8, "label": "报告与洞察", "workspace": "insights", "routeAlias": "/reports", "icon": "▣"},
    {"index": 9, "label": "市场与研究", "workspace": "market_research", "routeAlias": "/market-research", "icon": "⌁"},
    {"index": 10, "label": "设置", "workspace": "settings", "routeAlias": "/settings", "icon": "⚙"},
]

LEGACY_ALIAS_ROUTES = [
    {
        "taskId": "T3.1.2",
        "label": "首页",
        "targetWorkspace": "home",
        "routeAlias": "/home/today",
        "resolvedRouteAlias": "/home",
        "aliasClass": "secondary_or_command_alias",
        "primaryEntryAllowed": False,
    },
    {
        "taskId": "T3.1.2",
        "label": "市场",
        "targetWorkspace": "market_research",
        "routeAlias": "/market/watch",
        "resolvedRouteAlias": "/market-research?tab=market",
        "aliasClass": "secondary_or_command_alias",
        "primaryEntryAllowed": False,
    },
    {
        "taskId": "T3.1.2",
        "label": "研究",
        "targetWorkspace": "market_research",
        "routeAlias": "/market/research",
        "resolvedRouteAlias": "/market-research?tab=research",
        "aliasClass": "secondary_or_command_alias",
        "primaryEntryAllowed": False,
    },
    {
        "taskId": "T3.1.2",
        "label": "持仓",
        "targetWorkspace": "investment",
        "routeAlias": "/investment/holdings",
        "resolvedRouteAlias": "/investment?tab=holdings",
        "aliasClass": "secondary_or_command_alias",
        "primaryEntryAllowed": False,
    },
    {
        "taskId": "T3.1.2",
        "label": "策略实验室",
        "targetWorkspace": "market_research",
        "routeAlias": "/market/lab",
        "resolvedRouteAlias": "/market-research/strategy-lab",
        "aliasClass": "secondary_or_command_alias",
        "primaryEntryAllowed": False,
    },
    {
        "taskId": "T3.1.2",
        "label": "数据与系统",
        "targetWorkspace": "settings",
        "routeAlias": "/settings/data",
        "resolvedRouteAlias": "/settings?tab=data-system",
        "aliasClass": "secondary_or_command_alias",
        "primaryEntryAllowed": False,
    },
]

ACTIVE_STATE_RULES = {
    "nav_index_sequence": list(range(1, 11)),
    "single_active_primary_entry": True,
    "desktop_and_mobile_active_state_share_workspace": True,
    "legacy_alias_primary_entry_allowed": False,
    "legacy_alias_resolves_before_active_workspace": True,
}

LEGACY_ROUTE_ALIAS_TARGETS = {item["routeAlias"]: item["resolvedRouteAlias"] for item in LEGACY_ALIAS_ROUTES}
PRIMARY_ROUTE_WORKSPACES = {item["routeAlias"]: item["workspace"] for item in OFFICIAL_PRIMARY_NAV}


def resolve_legacy_route_alias(route_alias: str) -> str:
    clean = str(route_alias or "").strip()
    return LEGACY_ROUTE_ALIAS_TARGETS.get(clean, clean)


def active_workspace_from_route(route_alias: str) -> str | None:
    resolved = resolve_legacy_route_alias(route_alias).split("?", 1)[0]
    return PRIMARY_ROUTE_WORKSPACES.get(resolved)


@dataclass(frozen=True)
class V024Stage3Phase31NavigationContract:
    target_version: str
    source_package_version: str
    repair_label: str
    stage_id: str
    phase_id: str
    phase_name: str
    task_ids: list[str]
    navigation_contract_version: str
    official_primary_entries: list[dict[str, object]]
    legacy_alias_entries: list[dict[str, object]]
    active_state_rules: dict[str, object]
    phase_3_1_complete: bool
    phase_3_2_complete: bool
    phase_3_3_complete: bool
    stage_3_candidate_complete: bool
    stage_3_complete: bool
    browser_history_validation_done: bool
    app_bundle_changes_allowed: bool
    data_logic_changes_allowed: bool
    formal_fake_financial_data_allowed: bool
    github_main_upload_allowed: bool
    max_phases_per_run: int
    explicitly_not_done: list[str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def build_v024_stage3_phase31_contract() -> V024Stage3Phase31NavigationContract:
    return V024Stage3Phase31NavigationContract(
        target_version=TARGET_VERSION,
        source_package_version=SOURCE_PACKAGE_VERSION,
        repair_label=REPAIR_LABEL,
        stage_id=STAGE_ID,
        phase_id=PHASE_3_1_ID,
        phase_name=PHASE_3_1_NAME,
        task_ids=["T3.1.1", "T3.1.2", "T3.1.3", "T3.1.4"],
        navigation_contract_version=NAVIGATION_CONTRACT_VERSION,
        official_primary_entries=OFFICIAL_PRIMARY_NAV,
        legacy_alias_entries=LEGACY_ALIAS_ROUTES,
        active_state_rules=ACTIVE_STATE_RULES,
        phase_3_1_complete=True,
        phase_3_2_complete=False,
        phase_3_3_complete=False,
        stage_3_candidate_complete=False,
        stage_3_complete=False,
        browser_history_validation_done=False,
        app_bundle_changes_allowed=False,
        data_logic_changes_allowed=False,
        formal_fake_financial_data_allowed=False,
        github_main_upload_allowed=False,
        max_phases_per_run=1,
        explicitly_not_done=[
            "Stage 3 Phase 3.2 route implementation",
            "Stage 3 Phase 3.3 browser history validation",
            "Stage 3 whole-stage review",
            "GitHub main upload",
        ],
    )
