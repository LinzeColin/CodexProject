from __future__ import annotations

import json
import shutil
import subprocess
from html.parser import HTMLParser
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
NAVIGATION_PATH = ROOT / "web/app/navigation.js"
ROUTES_PATH = ROOT / "web/app/routes.js"
SHELL_PATH = ROOT / "web/app/shell.js"
INDEX_PATH = ROOT / "web/index.html"

EXPECTED_WORKSPACE_COUNTS = {
    "home": 4,
    "accounts": 4,
    "ledger": 4,
    "investment": 4,
    "consumption": 5,
    "sync": 5,
    "recommendations": 4,
    "insights": 5,
    "market_research": 5,
    "settings": 5,
}


class _NoJsPageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.pages: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = {key: value or "" for key, value in attrs}
        if tag == "article" and "data-no-js-page-route" in attributes:
            self.pages.append(attributes)


def _load_js(path: Path) -> dict[str, object]:
    node = shutil.which("node")
    if not node:
        pytest.skip("node is required for the Stage 6 page-contract test")
    result = subprocess.run(
        [node, "-e", "console.log(JSON.stringify(require(process.argv[1])))", str(path)],
        cwd=ROOT.parent,
        check=True,
        text=True,
        capture_output=True,
    )
    return json.loads(result.stdout)


def test_phase62_declares_all_canonical_secondary_page_contracts() -> None:
    contract = _load_js(NAVIGATION_PATH)["v025PageContracts"]
    assert contract["schema"] == "PFIV025Stage6Phase62PageContractsV1"
    assert contract["acceptanceId"] == "ACC-PFI-V025-S6-P62-PAGE-CONTRACTS"
    assert contract["taskIds"] == ["S6-P2-T1", "S6-P2-T2", "S6-P2-T3", "S6-P2-T4"]
    assert contract["phase62CandidateComplete"] is True
    assert contract["phase63Complete"] is False

    pages = contract["pages"]
    assert len(pages) == 45
    assert len({page["routeAlias"] for page in pages}) == 45
    assert len({page["stateKey"] for page in pages}) == 45
    assert len({page["layoutKind"] for page in pages}) == 45
    assert len({page["primaryAction"] for page in pages}) == 45
    assert len({page["dataObject"] for page in pages}) == 45
    assert all("?" not in page["routeAlias"] for page in pages)
    assert all(page["routeAlias"].startswith(page["primaryRouteAlias"] + "/") for page in pages)
    assert all(len(page["breadcrumb"]) == 2 for page in pages)
    assert all(page["jobToBeDone"] for page in pages)
    assert all(page["states"][kind] for page in pages for kind in ("loading", "empty", "error"))
    assert all(page["focusTarget"] == "page_heading" for page in pages)
    assert all(page["scrollPolicy"] == "restore_per_canonical_route" for page in pages)

    counts = {
        workspace: sum(page["workspace"] == workspace for page in pages)
        for workspace in EXPECTED_WORKSPACE_COUNTS
    }
    assert counts == EXPECTED_WORKSPACE_COUNTS
    assert [page["routeAlias"] for page in pages if page["pageLabel"] == "策略实验室"] == [
        "/market-research/strategy-lab"
    ]


def test_phase62_route_registry_resolves_canonical_and_historical_secondary_routes() -> None:
    routes = _load_js(ROUTES_PATH)
    registry = routes["phase62RouteRegistry"]
    assert registry["schema"] == "PFIV025Stage6Phase62RouteRegistryV1"
    assert len(registry["canonicalSecondaryRoutes"]) == 45
    assert registry["phase62CandidateComplete"] is True
    assert registry["phase63Complete"] is False

    node = shutil.which("node")
    assert node
    script = """
const routes = require(process.argv[1]);
const inputs = JSON.parse(process.argv[2]);
console.log(JSON.stringify(inputs.map((input) => routes.resolveRouteAlias(input))));
"""
    inputs = [
        "/overview/status",
        "/accounts/reconcile",
        "/data/history",
        "/market-research/strategy-lab",
        "/home?tab=status",
        "/sources-upload?tab=history",
        "/settings?tab=privacy",
    ]
    result = subprocess.run(
        [node, "-e", script, str(ROUTES_PATH), json.dumps(inputs)],
        cwd=ROOT.parent,
        check=True,
        text=True,
        capture_output=True,
    )
    resolved = json.loads(result.stdout)
    assert [item["routeAlias"] for item in resolved] == [
        "/overview/status",
        "/accounts/reconcile",
        "/data/history",
        "/market-research/strategy-lab",
        "/overview/status",
        "/data/history",
        "/settings/privacy",
    ]
    assert all(item["status"] == "resolved" for item in resolved)


def test_phase62_shell_uses_current_page_contract_and_recoverable_navigation() -> None:
    shell = SHELL_PATH.read_text(encoding="utf-8")
    assert "PFI_V025_STAGE6_PAGE_CONTRACTS" in shell
    assert 'data-stage6-page-contract' in shell
    assert 'data-stage6-job-to-be-done' in shell
    assert 'data-stage6-loading-state' in shell
    assert 'data-stage6-empty-state' in shell
    assert 'data-stage6-error-state' in shell
    assert "saveStage6RouteScroll" in shell
    assert "restoreStage6RouteScroll" in shell
    assert "document.title" in shell
    assert 'heading.focus({ preventScroll: true })' in shell


def test_phase62_nojs_fallback_has_a_nonblank_unique_page_for_every_contract() -> None:
    contract = _load_js(NAVIGATION_PATH)["v025PageContracts"]
    parser = _NoJsPageParser()
    parser.feed(INDEX_PATH.read_text(encoding="utf-8"))
    assert len(parser.pages) == 45
    assert {page["data-no-js-page-route"] for page in parser.pages} == {
        page["routeAlias"] for page in contract["pages"]
    }
    assert all(page["data-no-js-page-title"] for page in parser.pages)
    assert all(page["data-no-js-page-task"] for page in parser.pages)
