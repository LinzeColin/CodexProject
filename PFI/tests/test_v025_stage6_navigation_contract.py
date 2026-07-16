from __future__ import annotations

import json
import shutil
import subprocess
from html.parser import HTMLParser
from pathlib import Path

import pytest

from pfi_v02.stage_v025_navigation import (
    ALIAS_ROUTE_TARGETS,
    CANONICAL_STRATEGY_LAB_ROUTE,
    OFFICIAL_PRIMARY_NAV,
    audit_v025_stage6_phase61_index,
    build_v025_stage6_phase61_contract,
)


ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = ROOT / "web" / "index.html"
ROUTES_PATH = ROOT / "web" / "app" / "routes.js"

EXPECTED_LABELS = [
    "首页总览",
    "账户与资产",
    "账本流水",
    "投资管理",
    "消费管理",
    "数据源与上传",
    "建议与复盘",
    "报告与洞察",
    "市场与研究",
    "设置",
]
EXPECTED_PRIMARY_ROUTES = [
    "/overview",
    "/accounts",
    "/ledger",
    "/investment",
    "/consumption",
    "/data",
    "/review",
    "/reports",
    "/market-research",
    "/settings",
]
EXPECTED_ALIASES = {
    "/home": "/overview",
    "/market": "/market-research/market",
    "/research": "/market-research/research",
    "/holdings": "/investment/holdings",
    "/strategy-lab": "/market-research/strategy-lab",
    "/investment/strategy-lab": "/market-research/strategy-lab",
    "/data-system": "/settings/data-system",
}


class _PrimaryNodeParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.primary_nodes: list[dict[str, str]] = []
        self.nojs_nodes: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = {key: value or "" for key, value in attrs}
        if attributes.get("data-primary-entry") == "true":
            self.primary_nodes.append(attributes)
        if tag == "a" and "data-no-js-route" in attributes:
            self.nojs_nodes.append(attributes)


def _load_javascript_contract() -> dict[str, object]:
    node = shutil.which("node")
    if not node:
        pytest.skip("node is required for the route-registry contract")
    completed = subprocess.run(
        [node, "-e", "console.log(JSON.stringify(require(process.argv[1])))", str(ROUTES_PATH)],
        cwd=ROOT.parent,
        check=True,
        text=True,
        capture_output=True,
    )
    return json.loads(completed.stdout)


def test_phase61_primary_navigation_is_exactly_the_roadmap_appendix_contract() -> None:
    assert [entry["label"] for entry in OFFICIAL_PRIMARY_NAV] == EXPECTED_LABELS
    assert [entry["routeAlias"] for entry in OFFICIAL_PRIMARY_NAV] == EXPECTED_PRIMARY_ROUTES
    assert [entry["index"] for entry in OFFICIAL_PRIMARY_NAV] == list(range(1, 11))
    assert len({entry["workspace"] for entry in OFFICIAL_PRIMARY_NAV}) == 10


def test_phase61_alias_matrix_is_non_primary_and_resolves_to_canonical_routes() -> None:
    assert ALIAS_ROUTE_TARGETS == EXPECTED_ALIASES
    assert not (set(ALIAS_ROUTE_TARGETS) & set(EXPECTED_PRIMARY_ROUTES))
    assert CANONICAL_STRATEGY_LAB_ROUTE == "/market-research/strategy-lab"
    assert set(ALIAS_ROUTE_TARGETS.values()).issubset(
        set(EXPECTED_PRIMARY_ROUTES)
        | {
            "/market-research/market",
            "/market-research/research",
            "/investment/holdings",
            CANONICAL_STRATEGY_LAB_ROUTE,
            "/settings/data-system",
        }
    )


def test_phase61_static_dom_has_one_shared_ten_entry_tree_and_no_alias_pollution() -> None:
    audit = audit_v025_stage6_phase61_index(INDEX_PATH)
    assert audit["status"] == "pass"
    assert audit["unique_primary_node_count"] == 10
    assert audit["desktop_primary_count"] == 10
    assert audit["mobile_primary_count"] == 10
    assert audit["nojs_primary_count"] == 10
    assert audit["duplicate_responsive_primary_node_count"] == 0
    assert audit["alias_primary_node_count"] == 0

    parser = _PrimaryNodeParser()
    parser.feed(INDEX_PATH.read_text(encoding="utf-8"))
    assert [node["data-route-alias"] for node in parser.primary_nodes] == EXPECTED_PRIMARY_ROUTES
    assert [node["data-no-js-route"] for node in parser.nojs_nodes] == EXPECTED_PRIMARY_ROUTES


def test_phase61_javascript_registry_matches_python_and_resolves_every_alias() -> None:
    payload = _load_javascript_contract()
    assert payload["schema"] == "PFIV025Stage6Phase61NavigationContractV1"
    assert payload["navigationContractVersion"] == "PFI-V025-STAGE6-PHASE61-NAVIGATION-ALIAS"
    assert payload["taskIds"] == ["S6-P1-T1", "S6-P1-T2", "S6-P1-T3", "S6-P1-T4"]
    assert payload["officialPrimaryEntries"] == OFFICIAL_PRIMARY_NAV
    assert payload["aliasRouteTargets"] == ALIAS_ROUTE_TARGETS
    assert payload["canonicalStrategyLabRoute"] == CANONICAL_STRATEGY_LAB_ROUTE

    node = shutil.which("node")
    assert node
    script = """
const routes = require(process.argv[1]);
const inputs = JSON.parse(process.argv[2]);
console.log(JSON.stringify(inputs.map((input) => routes.resolveRouteAlias(input))));
"""
    completed = subprocess.run(
        [node, "-e", script, str(ROUTES_PATH), json.dumps(list(EXPECTED_ALIASES))],
        cwd=ROOT.parent,
        check=True,
        text=True,
        capture_output=True,
    )
    resolved = json.loads(completed.stdout)
    assert [item["routeAlias"] for item in resolved] == list(EXPECTED_ALIASES.values())
    assert all(item["status"] == "resolved" for item in resolved)
    assert all(item["routeType"] == "legacy_redirect" for item in resolved)


def test_phase61_contract_is_candidate_only_and_stops_before_phase62() -> None:
    payload = build_v025_stage6_phase61_contract(ROOT)
    assert payload["acceptance_id"] == "ACC-PFI-V025-S6-P61-NAVIGATION-ALIAS"
    assert payload["phase_6_1_status"] == "candidate_pass"
    assert payload["phase_6_2_status"] == "not_started"
    assert payload["phase_6_3_status"] == "not_started"
    assert payload["stage_6_status"] == "in_progress"
    assert payload["stage_6_whole_stage_review_status"] == "not_started"
    assert payload["stage_7_status"] == "not_started"
    assert payload["push_performed"] is False
    assert payload["app_install_performed"] is False
    assert payload["finder_used"] is False
