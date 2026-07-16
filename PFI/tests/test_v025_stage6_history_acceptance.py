from __future__ import annotations

from html.parser import HTMLParser
import json
from pathlib import Path
import shutil
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]
ROUTES_PATH = ROOT / "web/app/routes.js"
SHELL_PATH = ROOT / "web/app/shell.js"
INDEX_PATH = ROOT / "web/index.html"
BROWSER_PATH = ROOT / "web/tests/v025/stage6_history_acceptance_browser.py"
CDP_PATH = ROOT / "web/tests/v025/stage6_history_acceptance_cdp.mjs"


class _PrimaryAndInvalidRouteParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.primary_nodes: list[dict[str, str]] = []
        self.invalid_route_nodes: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = {key: value or "" for key, value in attrs}
        if attributes.get("data-primary-entry") == "true":
            self.primary_nodes.append(attributes)
        if "data-stage6-invalid-route" in attributes:
            self.invalid_route_nodes.append(attributes)


def _load_routes() -> dict[str, object]:
    node = shutil.which("node")
    if not node:
        pytest.skip("node is required for the Stage 6 route runtime contract")
    completed = subprocess.run(
        [node, "-e", "console.log(JSON.stringify(require(process.argv[1])))", str(ROUTES_PATH)],
        cwd=ROOT.parent,
        check=True,
        text=True,
        capture_output=True,
    )
    return json.loads(completed.stdout)


def test_phase63_route_runtime_contract_is_explicit_and_candidate_only() -> None:
    routes = _load_routes()
    contract = routes["phase63HistoryContract"]
    assert contract["schema"] == "PFIV025Stage6Phase63HistoryContractV1"
    assert contract["acceptanceId"] == "ACC-PFI-V025-S6-P63-HISTORY-ACCEPTANCE"
    assert contract["taskIds"] == ["S6-P3-T1", "S6-P3-T2", "S6-P3-T3", "S6-P3-T4"]
    assert contract["canonicalRouteCount"] == 55
    assert contract["historyMode"] == "canonical_path_with_hash_compatibility_fallback"
    assert contract["historyEvents"] == ["pushState", "replaceState", "popstate"]
    assert contract["invalidRouteStatus"] == "actionable_not_found"
    assert contract["invalidRouteRecovery"] == "/overview"
    assert contract["phase63CandidateComplete"] is True
    assert contract["stage6WholeReviewComplete"] is False
    assert routes["phase63CandidateComplete"] is True
    assert routes["stage6Complete"] is False


def test_phase63_shell_declares_state_url_focus_scroll_and_invalid_route_runtime() -> None:
    shell = SHELL_PATH.read_text(encoding="utf-8")
    required_runtime_symbols = (
        "PFI_V025_STAGE6_PHASE63_HISTORY",
        "stage6HistoryMode",
        "stage6CanonicalUrlForRoute",
        "replaceCurrentStage6HistoryState",
        "renderInvalidRouteState",
        "applyStage6HistoryNavigation",
        'window.history.scrollRestoration = "manual"',
        'source: "popstate"',
        'data-stage6-route-state',
        'data-stage6-invalid-route-requested',
    )
    for symbol in required_runtime_symbols:
        assert symbol in shell

    parser = _PrimaryAndInvalidRouteParser()
    parser.feed(INDEX_PATH.read_text(encoding="utf-8"))
    assert len(parser.primary_nodes) == 10
    assert len(parser.invalid_route_nodes) == 1
    invalid = parser.invalid_route_nodes[0]
    assert invalid["role"] == "alert"
    assert invalid["aria-live"] == "assertive"


def test_phase63_browser_acceptance_uses_real_history_reload_keyboard_and_ax_tree() -> None:
    browser = BROWSER_PATH.read_text(encoding="utf-8")
    cdp = CDP_PATH.read_text(encoding="utf-8")
    for marker in (
        "history.back()",
        "history.forward()",
        "Page.reload",
        "repeated_click_history_delta",
        "invalid_route_actionable",
        "keyboard_primary_navigation",
        "Accessibility.getFullAXTree",
    ):
        assert marker in browser or marker in cdp
    assert "external_network_performed" in browser
    assert "finder_used" in browser
    assert "stage_6_whole_stage_review_started" in browser


def test_phase63_legacy_hash_routes_remain_compatibility_inputs_not_canonical_urls() -> None:
    routes = _load_routes()
    inputs = ["#/accounts/reconcile", "/home?tab=status", "/not-a-real-route"]
    node = shutil.which("node")
    assert node
    script = """
const routes = require(process.argv[1]);
const inputs = JSON.parse(process.argv[2]);
console.log(JSON.stringify(inputs.map((value) => routes.resolveRouteAlias(value))));
"""
    completed = subprocess.run(
        [node, "-e", script, str(ROUTES_PATH), json.dumps(inputs)],
        cwd=ROOT.parent,
        check=True,
        text=True,
        capture_output=True,
    )
    resolved = json.loads(completed.stdout)
    assert resolved[0]["routeAlias"] == "/accounts/reconcile"
    assert resolved[0]["routeType"] == "legacy_redirect"
    assert resolved[1]["routeAlias"] == "/overview/status"
    assert resolved[1]["routeType"] == "legacy_redirect"
    assert resolved[2] == {
        "status": "unmatched",
        "inputRouteAlias": "/not-a-real-route",
        "routeType": "invalid",
        "reason": "route_not_registered",
        "recoveryRouteAlias": "/overview",
    }
