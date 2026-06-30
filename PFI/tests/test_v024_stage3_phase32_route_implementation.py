from __future__ import annotations

import json
from pathlib import Path
import subprocess
import unittest

import pfi_v02.stage_v024_stage3_navigation as navigation


ROOT = Path(__file__).resolve().parents[1]
NODE = "/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node"
EVIDENCE_DIR = ROOT / "reports" / "pfi_v024" / "stage_3" / "phase_3_2"

PRIMARY_ROUTE_CASES = [
    ("/home", "home"),
    ("/accounts", "accounts"),
    ("/ledger", "ledger"),
    ("/investment", "investment"),
    ("/consumption", "consumption"),
    ("/sources-upload", "sync"),
    ("/review", "recommendations"),
    ("/reports", "insights"),
    ("/market-research", "market_research"),
    ("/settings", "settings"),
]

SECONDARY_ROUTE_CASES = [
    ("/home?tab=status", "home", "/home", "status"),
    ("/accounts?tab=trend", "accounts", "/accounts", "trend"),
    ("/ledger?tab=review", "ledger", "/ledger", "review"),
    ("/investment?tab=holdings", "investment", "/investment", "holdings"),
    ("/consumption?tab=budget", "consumption", "/consumption", "budget"),
    ("/sources-upload?tab=import", "sync", "/sources-upload", "import"),
    ("/review?tab=decision", "recommendations", "/review", "decision"),
    ("/reports?tab=export", "insights", "/reports", "export"),
    ("/market-research?tab=research", "market_research", "/market-research", "research"),
    ("/market-research/strategy-lab", "market_research", "/market-research", "strategy_lab"),
    ("/settings?tab=data-system", "settings", "/settings", "data-system"),
]

LEGACY_REDIRECT_CASES = [
    ("/home/today", "/home", "home"),
    ("/market/watch", "/market-research?tab=market", "market_research"),
    ("/market/research", "/market-research?tab=research", "market_research"),
    ("/investment/holdings", "/investment?tab=holdings", "investment"),
    ("/market/lab", "/market-research/strategy-lab", "market_research"),
    ("/settings/data", "/settings?tab=data-system", "settings"),
]


def load_routes_js_payload() -> dict[str, object]:
    cases = {
        "primary": [route for route, _workspace in PRIMARY_ROUTE_CASES],
        "secondary": [route for route, _workspace, _primary, _tab in SECONDARY_ROUTE_CASES],
        "legacy": [route for route, _target, _workspace in LEGACY_REDIRECT_CASES],
    }
    script = f"""
const routes = require('./PFI/web/app/routes.js');
const cases = {json.dumps(cases, ensure_ascii=False)};
const resolveAll = (items) => Object.fromEntries(items.map((routeAlias) => [routeAlias, routes.resolveRouteAlias(routeAlias)]));
console.log(JSON.stringify({{
  phase32: routes.v024Phase32RouteContract,
  primary: resolveAll(cases.primary),
  secondary: resolveAll(cases.secondary),
  legacy: resolveAll(cases.legacy),
  hashLegacy: routes.resolveRouteAlias('#/market/watch'),
  unknown: routes.resolveRouteAlias('/not-a-real-route'),
}}));
"""
    completed = subprocess.run(
        [NODE, "-e", script],
        cwd=ROOT.parent,
        check=True,
        text=True,
        capture_output=True,
    )
    return json.loads(completed.stdout)


class TestV024Stage3Phase32RouteImplementation(unittest.TestCase):
    def test_phase32_python_contract_declares_route_implementation_scope(self) -> None:
        self.assertTrue(hasattr(navigation, "build_v024_stage3_phase32_contract"))

        contract = navigation.build_v024_stage3_phase32_contract().to_dict()

        self.assertEqual(contract["target_version"], "v0.2.4")
        self.assertEqual(contract["source_package_version"], "v0.2.3-repair")
        self.assertEqual(contract["stage_id"], "Stage 3")
        self.assertEqual(contract["phase_id"], "3.2")
        self.assertEqual(contract["phase_name"], "路由实现")
        self.assertEqual(contract["task_ids"], ["T3.2.1", "T3.2.2", "T3.2.3", "T3.2.4"])
        self.assertTrue(contract["phase_3_1_complete"])
        self.assertTrue(contract["phase_3_2_complete"])
        self.assertFalse(contract["phase_3_3_complete"])
        self.assertFalse(contract["stage_3_candidate_complete"])
        self.assertFalse(contract["stage_3_complete"])
        self.assertFalse(contract["browser_history_validation_done"])
        self.assertFalse(contract["github_main_upload_allowed"])
        self.assertEqual(contract["max_phases_per_run"], 1)
        self.assertEqual(len(contract["primary_routes"]), 10)
        self.assertEqual(len(contract["legacy_redirect_routes"]), 6)
        self.assertGreaterEqual(len(contract["secondary_routes"]), 30)
        self.assertTrue(contract["history_runtime_contract"]["push_state_declared"])
        self.assertTrue(contract["history_runtime_contract"]["popstate_listener_declared"])

    def test_phase32_routes_js_resolves_primary_and_secondary_routes(self) -> None:
        payload = load_routes_js_payload()
        phase32 = payload["phase32"]

        self.assertEqual(phase32["version"], "v0.2.4")
        self.assertEqual(phase32["phaseId"], "3.2")
        self.assertEqual(phase32["phaseName"], "路由实现")
        self.assertEqual(phase32["taskIds"], ["T3.2.1", "T3.2.2", "T3.2.3", "T3.2.4"])
        self.assertEqual(len(phase32["primaryRoutes"]), 10)
        self.assertGreaterEqual(len(phase32["secondaryRoutes"]), 30)

        for route_alias, workspace in PRIMARY_ROUTE_CASES:
            with self.subTest(route_alias=route_alias):
                resolved = payload["primary"][route_alias]
                self.assertEqual(resolved["status"], "resolved")
                self.assertEqual(resolved["routeType"], "primary")
                self.assertEqual(resolved["routeAlias"], route_alias)
                self.assertEqual(resolved["workspace"], workspace)
                self.assertEqual(resolved["primaryRouteAlias"], route_alias)

        for route_alias, workspace, primary_route, tab in SECONDARY_ROUTE_CASES:
            with self.subTest(route_alias=route_alias):
                resolved = payload["secondary"][route_alias]
                self.assertEqual(resolved["status"], "resolved")
                self.assertEqual(resolved["routeType"], "secondary")
                self.assertEqual(resolved["routeAlias"], route_alias)
                self.assertEqual(resolved["workspace"], workspace)
                self.assertEqual(resolved["primaryRouteAlias"], primary_route)
                self.assertEqual(resolved["tab"], tab)

    def test_phase32_routes_js_redirects_v01_aliases_to_owned_routes(self) -> None:
        payload = load_routes_js_payload()

        for route_alias, target_route, workspace in LEGACY_REDIRECT_CASES:
            with self.subTest(route_alias=route_alias):
                resolved = payload["legacy"][route_alias]
                self.assertEqual(resolved["status"], "resolved")
                self.assertEqual(resolved["routeType"], "legacy_redirect")
                self.assertEqual(resolved["inputRouteAlias"], route_alias)
                self.assertEqual(resolved["routeAlias"], target_route)
                self.assertEqual(resolved["redirectedFrom"], route_alias)
                self.assertEqual(resolved["workspace"], workspace)

        self.assertEqual(payload["hashLegacy"]["routeAlias"], "/market-research?tab=market")
        self.assertEqual(payload["hashLegacy"]["redirectedFrom"], "/market/watch")
        self.assertEqual(payload["unknown"], {"status": "unmatched", "inputRouteAlias": "/not-a-real-route"})

    def test_phase32_shell_runtime_uses_route_table_and_history_events(self) -> None:
        shell_text = (ROOT / "web" / "app" / "shell.js").read_text(encoding="utf-8")

        self.assertIn("PFI_V024_STAGE3_ROUTES", shell_text)
        self.assertIn("STAGE3_ROUTES.resolveRouteAlias", shell_text)
        self.assertIn("function routeAliasFromLocation", shell_text)
        self.assertIn("function syncBrowserRoute", shell_text)
        self.assertIn("pushState", shell_text)
        self.assertIn("replaceState", shell_text)
        self.assertIn('window.addEventListener("hashchange"', shell_text)
        self.assertIn('window.addEventListener("popstate"', shell_text)
        self.assertIn("skipRouteSync", shell_text)

    def test_phase32_evidence_pack_records_boundaries(self) -> None:
        evidence_path = EVIDENCE_DIR / "evidence.json"
        changed_files_path = EVIDENCE_DIR / "changed_files.txt"
        terminal_path = EVIDENCE_DIR / "terminal.log"
        risk_path = EVIDENCE_DIR / "risk_and_rollback.md"
        doc_path = ROOT / "docs" / "pfi_v024" / "STAGE3_NAVIGATION_ROUTING.md"

        for path in (evidence_path, changed_files_path, terminal_path, risk_path, doc_path):
            self.assertTrue(path.exists(), str(path))

        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        changed_files = [line.strip() for line in changed_files_path.read_text(encoding="utf-8").splitlines() if line.strip()]

        self.assertEqual(evidence["schema"], "PFIV024Stage3Phase32RouteEvidenceV1")
        self.assertEqual(evidence["target_version"], "v0.2.4")
        self.assertEqual(evidence["stage"], "Stage 3")
        self.assertEqual(evidence["phase_id"], "3.2")
        self.assertEqual(evidence["phase_name"], "路由实现")
        self.assertEqual(evidence["status"], "candidate_pass")
        self.assertTrue(evidence["current_phase_only"])
        self.assertTrue(evidence["max_one_phase_per_run"])
        self.assertEqual(evidence["changed_files"], changed_files)
        self.assertTrue(evidence["acceptance_checks"]["primary_routes_resolve"])
        self.assertTrue(evidence["acceptance_checks"]["secondary_routes_resolve"])
        self.assertTrue(evidence["acceptance_checks"]["v01_aliases_redirect"])
        self.assertTrue(evidence["acceptance_checks"]["history_popstate_runtime_declared"])
        self.assertFalse(evidence["phase_3_3_complete"])
        self.assertFalse(evidence["stage_3_complete"])
        self.assertFalse(evidence["github_main_uploaded"])
        self.assertIn("Stage 3 Phase 3.3 browser history validation", evidence["explicitly_not_done"])
        self.assertIn("Stage 3 whole-stage review", evidence["explicitly_not_done"])
        self.assertIn("GitHub main upload", evidence["explicitly_not_done"])


if __name__ == "__main__":
    unittest.main()
