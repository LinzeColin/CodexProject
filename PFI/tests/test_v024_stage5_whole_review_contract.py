from __future__ import annotations

import json
from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
NODE = "/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node"
STAGE5_DIR = ROOT / "reports" / "pfi_v024" / "stage_5"
REVIEW_DIR = STAGE5_DIR / "whole_stage_review"
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
MECHANICAL_TERMS = ("功能面板", "PFI 功能入口", "功能已准备", "进入操作面板")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_stage5_runtime_contract() -> dict[str, object]:
    script = """
const home = require('./PFI/web/app/pages/home.js');
const pages = require('./PFI/web/app/pages/stage5Subpages.js');
const ux = require('./PFI/web/app/ux_state.js');
const routes = require('./PFI/web/app/routes.js');
const catalog = pages.buildV024Stage5Phase52Catalog();
const flatPages = pages.flattenV024Stage5Phase52Pages(catalog);
const uxCatalog = ux.buildV024Stage5UxStateCatalog(catalog);
console.log(JSON.stringify({
  homeContract: home.buildV024Stage5Phase51Contract(),
  pageContract: pages.buildV024Stage5Phase52Contract(),
  uxContract: ux.buildV024Stage5Phase53Contract(),
  routeValidation: pages.validateV024Stage5Phase52Catalog(catalog, routes.v024Phase32RouteContract.secondaryRoutes),
  uxValidation: ux.validateV024Stage5UxStateCatalog(uxCatalog),
  primaryWorkspaces: Object.keys(catalog),
  totalPages: flatPages.length,
  primaryActionMissing: flatPages.filter((page) => !page.primaryAction).map((page) => page.routeAlias),
  stateKinds: [...new Set(Object.values(uxCatalog).flatMap((items) => items.flatMap((page) => page.stateKinds)))],
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


class TestV024Stage5WholeReviewContract(unittest.TestCase):
    def test_whole_stage_review_artifacts_exist_and_scope_is_bounded(self) -> None:
        expected_files = [
            ROOT / "docs" / "pfi_v024" / "STAGE5_WHOLE_STAGE_REVIEW.md",
            ROOT / "scripts" / "validate_v024_stage5_whole_review_browser.js",
            REVIEW_DIR / "evidence.json",
            REVIEW_DIR / "browser_validation.json",
            REVIEW_DIR / "terminal.log",
            REVIEW_DIR / "changed_files.txt",
            REVIEW_DIR / "risk_and_rollback.md",
        ]
        for path in expected_files:
            self.assertTrue(path.exists(), str(path))

        evidence = read_json(REVIEW_DIR / "evidence.json")
        self.assertEqual(evidence["schema"], "PFIV024Stage5WholeReviewEvidenceV1")
        self.assertEqual(evidence["target_version"], "v0.2.4")
        self.assertEqual(evidence["source_package_version"], "v0.2.3-repair")
        self.assertEqual(evidence["stage"], "Stage 5")
        self.assertEqual(evidence["review_id"], "stage_5_whole_review")
        self.assertEqual(evidence["status"], "pass")
        self.assertEqual(evidence["current_run_unit"], "Stage 5 whole-stage review")
        self.assertTrue(evidence["current_run_only"])
        self.assertTrue(evidence["stage_5_candidate_complete"])
        self.assertTrue(evidence["stage_5_whole_review_complete"])
        self.assertFalse(evidence["stage_6_started"])
        self.assertFalse(evidence["github_main_uploaded"])
        self.assertIn("Stage 6", evidence["explicitly_not_done"])
        self.assertIn("GitHub main upload", evidence["explicitly_not_done"])

    def test_review_proves_stage5_acceptance_against_runtime_contracts(self) -> None:
        runtime = load_stage5_runtime_contract()
        evidence = read_json(REVIEW_DIR / "evidence.json")
        acceptance = evidence["acceptance_checks"]

        self.assertEqual(tuple(runtime["primaryWorkspaces"]), PRIMARY_WORKSPACES)
        self.assertEqual(runtime["totalPages"], 45)
        self.assertEqual(runtime["primaryActionMissing"], [])
        self.assertEqual(runtime["routeValidation"]["status"], "pass")
        self.assertEqual(runtime["uxValidation"]["status"], "pass")
        self.assertEqual(runtime["uxValidation"]["missing_state_pages"], [])
        self.assertEqual(runtime["uxValidation"]["non_actionable_empty_pages"], [])
        self.assertEqual(runtime["uxValidation"]["non_actionable_error_pages"], [])
        self.assertEqual(runtime["uxValidation"]["history_acceptance"]["status"], "pass")

        expected_acceptance = {
            "homepage_answers_six_questions",
            "mechanical_home_layer_removed",
            "ten_primary_entries_preserved",
            "each_primary_has_three_or_more_distinct_subpages",
            "secondary_pages_not_title_only_clones",
            "every_page_has_primary_action_and_four_states",
            "click_actions_are_real_routes_not_toast_only",
            "browser_screenshots_cover_primary_and_core_secondary_pages",
            "no_forbidden_financial_data_added",
        }
        self.assertEqual(set(acceptance), expected_acceptance)
        for check_id, item in acceptance.items():
            self.assertEqual(item["result"], "pass", check_id)
            self.assertTrue(item["evidence"], check_id)

    def test_phase_evidence_is_current_and_consistent(self) -> None:
        evidence = read_json(REVIEW_DIR / "evidence.json")
        phase51 = read_json(STAGE5_DIR / "phase_5_1" / "evidence.json")
        phase52 = read_json(STAGE5_DIR / "phase_5_2" / "evidence.json")
        phase53 = read_json(STAGE5_DIR / "phase_5_3" / "evidence.json")
        route_validation = read_json(STAGE5_DIR / "phase_5_2" / "route_validation.json")
        ux_validation = read_json(STAGE5_DIR / "phase_5_3" / "ux_state_validation.json")
        history_validation = read_json(STAGE5_DIR / "phase_5_3" / "history_validation.json")

        self.assertEqual(evidence["reviewed_phase_ids"], ["5.1", "5.2", "5.3"])
        self.assertEqual(evidence["phase_statuses"], {
            "phase_5_1": "candidate_pass",
            "phase_5_2": "candidate_pass",
            "phase_5_3": "candidate_pass",
        })
        self.assertEqual([phase51["status"], phase52["status"], phase53["status"]], ["candidate_pass", "candidate_pass", "candidate_pass"])
        self.assertTrue(phase51["phase_5_1_complete"])
        self.assertTrue(phase52["phase_5_2_complete"])
        self.assertTrue(phase53["phase_5_3_complete"])
        self.assertEqual(route_validation["status"], "pass")
        self.assertEqual(ux_validation["status"], "pass")
        self.assertEqual(history_validation["status"], "pass")
        self.assertEqual(evidence["validation_surface"]["total_subpage_count"], route_validation["total_subpage_count"])
        self.assertEqual(evidence["validation_surface"]["ux_state_page_count"], ux_validation["total_page_count"])
        self.assertEqual(evidence["validation_surface"]["history_route_count"], history_validation["total_route_aliases"])

    def test_browser_validation_covers_stage5_pass_gate(self) -> None:
        browser = read_json(REVIEW_DIR / "browser_validation.json")
        screenshot_dir = REVIEW_DIR / "screenshots"

        self.assertEqual(browser["schema"], "PFIV024Stage5WholeReviewBrowserValidationV1")
        self.assertEqual(browser["status"], "pass")
        self.assertEqual(browser["primary_entry_count"], 10)
        self.assertEqual(browser["primary_screenshot_count"], 10)
        self.assertGreaterEqual(browser["core_secondary_screenshot_count"], 10)
        self.assertEqual(browser["console_errors"], [])
        self.assertEqual(browser["page_errors"], [])
        self.assertEqual(set(browser["primary_workspaces"]), set(PRIMARY_WORKSPACES))
        self.assertTrue(browser["click_actions_route_not_toast_only"])
        self.assertTrue(browser["history_back_forward_passed"])
        self.assertTrue(browser["stage5_ux_state_visible"])
        self.assertEqual(browser["mechanical_terms_visible"], [])

        screenshots = browser["screenshots"]
        self.assertGreaterEqual(len(screenshots), 20)
        for item in screenshots:
            path = screenshot_dir / item["file"]
            self.assertTrue(path.exists(), str(path))
            self.assertGreater(path.stat().st_size, 20_000, str(path))

    def test_review_findings_are_recorded_and_fixed_before_upload(self) -> None:
        evidence = read_json(REVIEW_DIR / "evidence.json")
        findings = evidence["review_findings"]

        self.assertGreaterEqual(len(findings), 3)
        for finding in findings:
            self.assertIn(finding["severity"], {"P1", "P2", "P3"})
            self.assertEqual(finding["status"], "fixed")
            self.assertTrue(finding["fix"])
            self.assertTrue(finding["verification"])

        command_status = {item["cmd"]: item["status"] for item in evidence["commands"]}
        self.assertEqual(command_status["node stage5 whole review browser validation"], "pass")
        self.assertEqual(command_status["pytest stage5 whole review contract"], "pass")
        self.assertEqual(command_status["pytest stage5 phase regression"], "pass")
        self.assertEqual(command_status["pytest stage3/stage4 regression"], "pass")
        self.assertEqual(command_status["git diff --check -- PFI"], "pass")

        self.assertFalse(evidence["github_main_uploaded"])
        self.assertIn("GitHub main upload", evidence["remaining_gates"])

    def test_formal_ui_does_not_restore_mechanical_terms(self) -> None:
        html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        shell = (ROOT / "web" / "app" / "shell.js").read_text(encoding="utf-8")
        combined = f"{html}\n{shell}"

        for term in MECHANICAL_TERMS:
            with self.subTest(term=term):
                self.assertNotIn(term, combined)


if __name__ == "__main__":
    unittest.main()
