from __future__ import annotations

import json
from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
NODE = "/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node"

PRIMARY_WORKSPACES = (
    "home",
    "accounts",
    "ledger",
    "investment",
    "consumption",
    "sync",
    "recommendations",
    "insights",
    "market_research",
    "settings",
)
DIFFERENTIATION_FIELDS = ("routeAlias", "stateKey", "title", "layoutKind", "primaryAction", "dataObject")


def load_phase52_payload() -> dict[str, object]:
    script = """
const routes = require('./PFI/web/app/routes.js');
const pages = require('./PFI/web/app/pages/stage5Subpages.js');
const catalog = pages.buildV024Stage5Phase52Catalog();
const flatPages = pages.flattenV024Stage5Phase52Pages(catalog);
console.log(JSON.stringify({
  contract: pages.buildV024Stage5Phase52Contract(),
  catalog,
  flatPages,
  validation: pages.validateV024Stage5Phase52Catalog(catalog, routes.v024Phase32RouteContract.secondaryRoutes),
}));
"""
    completed = subprocess.run(
        [NODE, "-e", script],
        cwd=ROOT.parent,
        check=True,
        text=True,
        capture_output=True,
    )
    return json.loads(completed.stdout)


class TestV024Stage5Phase52SubpageDifferentiation(unittest.TestCase):
    def test_phase52_contract_is_limited_to_subpage_differentiation(self) -> None:
        payload = load_phase52_payload()
        contract = payload["contract"]

        self.assertEqual(contract["schema"], "PFIV024Stage5Phase52ContractV1")
        self.assertEqual(contract["target_version"], "v0.2.4")
        self.assertEqual(contract["source_package_version"], "v0.2.3-repair")
        self.assertEqual(contract["stage"], "Stage 5")
        self.assertEqual(contract["phase_id"], "5.2")
        self.assertEqual(contract["phase_name"], "二级页面差异化")
        self.assertTrue(contract["current_phase_only"])
        self.assertTrue(contract["max_one_phase_per_run"])
        self.assertTrue(contract["phase_5_1_complete"])
        self.assertFalse(contract["phase_5_3_started"])
        self.assertEqual(contract["primary_entry_count"], 10)
        self.assertEqual(contract["min_subpages_per_primary"], 3)
        self.assertEqual(tuple(contract["differentiation_fields"]), DIFFERENTIATION_FIELDS)
        self.assertIn("T5.2.1 账户二级页面差异化", contract["tasks"])
        self.assertIn("T5.2.2 投资二级页面差异化", contract["tasks"])
        self.assertIn("T5.2.3 消费二级页面差异化", contract["tasks"])
        self.assertIn("T5.2.4 数据源/报告/市场差异化", contract["tasks"])
        self.assertIn("Phase 5.3 交互状态", contract["explicitly_not_done"])
        self.assertIn("Stage 5 whole-stage review", contract["explicitly_not_done"])
        self.assertIn("GitHub main upload", contract["explicitly_not_done"])

    def test_each_primary_entry_has_three_or_more_structurally_distinct_subpages(self) -> None:
        payload = load_phase52_payload()
        catalog = payload["catalog"]

        self.assertEqual(tuple(catalog), PRIMARY_WORKSPACES)
        for workspace in PRIMARY_WORKSPACES:
            pages = catalog[workspace]
            self.assertGreaterEqual(len(pages), 3, workspace)
            for field in DIFFERENTIATION_FIELDS:
                values = [page[field] for page in pages]
                self.assertEqual(len(set(values)), len(values), f"{workspace}:{field} is not differentiated")
            for page in pages:
                self.assertEqual(page["workspace"], workspace)
                self.assertTrue(page["routeAlias"].startswith("/"))
                self.assertIn(workspace, page["stateKey"])
                self.assertGreaterEqual(len(page["sections"]), 3)
                self.assertTrue(page["primaryObject"])
                self.assertTrue(page["primaryAction"])
                self.assertTrue(page["dataObject"])
                self.assertTrue(page["dataSource"])
                self.assertTrue(page["emptyState"])
                self.assertTrue(page["errorState"])

    def test_route_validation_matches_stage3_secondary_routes_without_orphans(self) -> None:
        payload = load_phase52_payload()
        validation = payload["validation"]

        self.assertEqual(validation["schema"], "PFIV024Stage5Phase52RouteValidationV1")
        self.assertEqual(validation["status"], "pass")
        self.assertEqual(validation["primary_entry_count"], 10)
        self.assertEqual(validation["workspace_count"], 10)
        self.assertEqual(validation["total_subpage_count"], 45)
        self.assertEqual(validation["min_subpages_per_primary"], 4)
        self.assertEqual(validation["missing_workspaces"], [])
        self.assertEqual(validation["workspaces_below_minimum"], [])
        self.assertEqual(validation["duplicate_route_aliases"], [])
        self.assertEqual(validation["duplicate_state_keys"], [])
        self.assertEqual(validation["missing_stage3_secondary_routes"], [])
        self.assertEqual(validation["orphan_stage5_routes"], [])
        self.assertEqual(validation["title_only_clone_groups"], [])

    def test_runtime_loads_v024_stage5_subpage_catalog_before_rendering(self) -> None:
        html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        shell = (ROOT / "web" / "app" / "shell.js").read_text(encoding="utf-8")
        streamlit = (ROOT / "src" / "pfi_os" / "app" / "streamlit_app.py").read_text(encoding="utf-8")

        self.assertLess(html.index("./app/pages/stage4Subpages.js"), html.index("./app/pages/stage5Subpages.js"))
        self.assertLess(html.index("./app/pages/stage5Subpages.js"), html.index("./app/shell.js"))
        self.assertIn("PFI_V024_STAGE5_PAGES", shell)
        self.assertIn("loadStage5SubpageCatalog", shell)
        self.assertIn("buildV024Stage5Phase52Catalog", shell)
        self.assertIn("data-stage5-state-key", shell)
        self.assertIn("data-stage5-data-object", shell)
        self.assertIn("stage5_pages_path", streamlit)
        self.assertIn("stage5_pages_js", streamlit)

    def test_phase52_evidence_pack_exists_before_candidate_pass(self) -> None:
        phase_dir = ROOT / "reports" / "pfi_v024" / "stage_5" / "phase_5_2"
        evidence_path = phase_dir / "evidence.json"
        route_validation_path = phase_dir / "route_validation.json"
        ux_diff_path = phase_dir / "ux_diff_report.md"
        changed_files_path = phase_dir / "changed_files.txt"
        terminal_log_path = phase_dir / "terminal.log"
        risk_path = phase_dir / "risk_and_rollback.md"
        doc_path = ROOT / "docs" / "pfi_v024" / "STAGE5_SUBPAGE_DIFFERENTIATION.md"

        for path in (evidence_path, route_validation_path, ux_diff_path, changed_files_path, terminal_log_path, risk_path, doc_path):
            with self.subTest(path=path.name):
                self.assertTrue(path.exists(), f"{path} is required")

        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        route_validation = json.loads(route_validation_path.read_text(encoding="utf-8"))
        self.assertEqual(evidence["schema"], "PFIV024Stage5Phase52EvidenceV1")
        self.assertEqual(evidence["target_version"], "v0.2.4")
        self.assertEqual(evidence["stage"], "Stage 5")
        self.assertEqual(evidence["phase_id"], "5.2")
        self.assertEqual(evidence["status"], "candidate_pass")
        self.assertTrue(evidence["current_phase_only"])
        self.assertTrue(evidence["phase_5_1_complete"])
        self.assertTrue(evidence["phase_5_2_complete"])
        self.assertFalse(evidence["phase_5_3_started"])
        self.assertFalse(evidence["stage_5_whole_review_complete"])
        self.assertFalse(evidence["github_main_uploaded"])
        self.assertTrue(evidence["no_forbidden_financial_data"])
        self.assertEqual(route_validation["status"], "pass")
        self.assertEqual(route_validation["total_subpage_count"], evidence["total_subpage_count"])


if __name__ == "__main__":
    unittest.main()
