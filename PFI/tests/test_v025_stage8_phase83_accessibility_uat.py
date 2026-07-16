from __future__ import annotations

import json
from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent
INDEX_PATH = ROOT / "web" / "index.html"
TOKENS_PATH = ROOT / "web" / "styles" / "tokens.css"
ACCESSIBILITY_PATH = ROOT / "web" / "app" / "accessibility.js"
HARNESS_PATH = ROOT / "web" / "tests" / "v025" / "stage8_phase83_cdp.mjs"
PHASE_DIR = ROOT / "reports" / "pfi_v025" / "stage_8" / "phase_8_3"
TASK_IDS = ["S8-P3-T1", "S8-P3-T2", "S8-P3-T3", "S8-P3-T4"]


def load_json(name: str) -> dict:
    return json.loads((PHASE_DIR / name).read_text(encoding="utf-8"))


class TestV025Stage8Phase83AccessibilityUAT(unittest.TestCase):
    def test_formal_shell_mounts_phase83_accessibility_runtime_only(self) -> None:
        index = INDEX_PATH.read_text(encoding="utf-8")
        self.assertTrue(ACCESSIBILITY_PATH.is_file())
        self.assertIn('data-v025-stage8-accessibility="phase_8_3"', index)
        self.assertIn('<script src="./app/accessibility.js"></script>', index)
        self.assertNotIn('data-v025-stage8-whole-review="pass"', index)
        self.assertNotIn('data-v025-stage9=', index)

    def test_runtime_contract_covers_keyboard_focus_status_and_error_prevention(self) -> None:
        source = ACCESSIBILITY_PATH.read_text(encoding="utf-8")
        required = (
            "PFIV025Stage8Phase83AccessibilityContractV1",
            'standard: "WCAG 2.2 AA"',
            "lastInputModality",
            "routeAnnouncer",
            "focusMainForKeyboardRoute",
            "aria-live",
            "financial_data_error_prevention",
            "MutationObserver",
            "PFI_V025_STAGE8_ACCESSIBILITY",
        )
        for token in required:
            self.assertIn(token, source)
        self.assertNotIn('tabindex="1"', source)
        self.assertNotIn("outline = 'none'", source)

    def test_phase83_css_has_visible_focus_target_and_forced_color_contracts(self) -> None:
        css = TOKENS_PATH.read_text(encoding="utf-8")
        start = css.index("/* v0.2.5 Stage 8 Phase 8.3")
        phase83 = css[start:]
        for token in (
            ":focus-visible",
            "outline: 3px solid",
            "outline-offset: 3px",
            "scroll-margin",
            "min-width: 44px",
            "min-height: 44px",
            "@media (forced-colors: active)",
        ):
            self.assertIn(token, phase83)
        self.assertNotIn("outline: none", phase83)
        self.assertNotIn("outline: 0", phase83)

    def test_browser_harness_runs_real_contrast_ax_keyboard_and_pixel_regression(self) -> None:
        source = HARNESS_PATH.read_text(encoding="utf-8")
        for token in (
            "chromium.launch",
            "Accessibility.getFullAXTree",
            "contrastRatio",
            "pixelmatch",
            "PRIMARY_ROUTES",
            "SECONDARY_ROUTES",
            "keyboardFlow",
            "390",
            "1440",
        ):
            self.assertIn(token, source)
        self.assertIn("PRIMARY_ROUTES.length !== 10", source)
        self.assertNotIn("axe_core_passed: true", source)

    def test_wcag_keyboard_and_ax_evidence_has_zero_blocking_findings(self) -> None:
        wcag = load_json("wcag_audit.json")
        keyboard = load_json("keyboard_flow.json")
        ax_tree = load_json("accessibility_tree.json")
        self.assertEqual(wcag["standard"], "WCAG 2.2 AA")
        self.assertEqual(wcag["audited_primary_page_count"], 10)
        self.assertGreaterEqual(wcag["audited_secondary_page_count"], 8)
        self.assertEqual(wcag["blocking_violation_count"], 0)
        self.assertEqual(wcag["contrast_failure_count"], 0)
        self.assertEqual(wcag["target_size_failure_count"], 0)
        self.assertTrue(wcag["financial_data_error_prevention_passed"])
        self.assertTrue(keyboard["skip_link_to_main_passed"])
        self.assertTrue(keyboard["primary_navigation_passed"])
        self.assertTrue(keyboard["secondary_navigation_passed"])
        self.assertTrue(keyboard["focus_not_obscured_passed"])
        self.assertTrue(keyboard["no_keyboard_trap"])
        self.assertEqual(ax_tree["unnamed_interactive_node_count"], 0)
        self.assertEqual(ax_tree["duplicate_id_count"], 0)
        self.assertEqual(ax_tree["primary_navigation_entry_count"], 10)

    def test_visual_regression_covers_ten_pages_at_desktop_and_mobile(self) -> None:
        visual = load_json("visual_regression.json")
        screenshots = list((PHASE_DIR / "desktop_pages").glob("*.png")) + list(
            (PHASE_DIR / "mobile_pages").glob("*.png")
        )
        self.assertEqual(visual["primary_page_count"], 10)
        self.assertEqual(visual["viewport_count"], 2)
        self.assertEqual(visual["screenshot_count"], 20)
        self.assertEqual(len(screenshots), 20)
        self.assertEqual(visual["decode_failure_count"], 0)
        self.assertEqual(visual["dimension_mismatch_count"], 0)
        self.assertEqual(visual["regression_failure_count"], 0)
        self.assertLessEqual(visual["maximum_diff_ratio"], visual["allowed_diff_ratio"])

    def test_phase_evidence_is_complete_but_does_not_claim_stage_acceptance(self) -> None:
        required = (
            "evidence.json",
            "phase_contract.json",
            "browser_validation.json",
            "wcag_audit.json",
            "keyboard_flow.json",
            "accessibility_tree.json",
            "visual_regression.json",
            "error_prevention_audit.json",
            "human_acceptance_request.json",
            "defects.md",
            "terminal.log",
            "changed_files.txt",
            "risk_and_rollback.md",
            "browser_trace.zip",
            "artifact_hashes.json",
        )
        for name in required:
            self.assertTrue((PHASE_DIR / name).is_file(), name)
        evidence = load_json("evidence.json")
        request = load_json("human_acceptance_request.json")
        self.assertEqual(evidence["schema"], "PFIV025Stage8Phase83EvidenceV1")
        self.assertEqual(evidence["status"], "candidate_pass")
        self.assertEqual(evidence["task_ids"], TASK_IDS)
        self.assertTrue(evidence["phase_8_3_complete"])
        self.assertFalse(evidence["stage_8_whole_review_complete"])
        self.assertFalse(evidence["stage_8_user_acceptance_complete"])
        self.assertFalse(evidence["stage_9_started"])
        self.assertFalse(evidence["github_main_uploaded"])
        self.assertFalse(evidence["app_bundle_reinstall_executed"])
        self.assertFalse(evidence["finder_used"])
        self.assertEqual(request["status"], "pending_whole_stage_review_and_user_confirmation")
        self.assertFalse(request["accepted"])
        self.assertIsNone(request["user_confirmation_reference"])

    def test_release_identity_matches_evidence_without_model_formula_parameter_change(self) -> None:
        evidence = load_json("evidence.json")
        binding = load_json("release_identity_binding.json")
        phase_commit = subprocess.run(
            ["git", "log", "-1", "--format=%H", "--", "PFI/reports/pfi_v025/stage_8/phase_8_3/evidence.json"],
            cwd=REPO_ROOT,
            check=True,
            text=True,
            capture_output=True,
        ).stdout.strip()
        historical_manifest = json.loads(subprocess.run(
            ["git", "show", f"{phase_commit}:PFI/config/release_manifest.json"],
            cwd=REPO_ROOT,
            check=True,
            text=True,
            capture_output=True,
        ).stdout)
        self.assertEqual(binding["frontend_bundle_hash"], historical_manifest["frontend_bundle_hash"])
        self.assertEqual(binding["backend_build_hash"], historical_manifest["backend_build_hash"])
        self.assertTrue(binding["frontend_hash_recomputed"])
        self.assertTrue(binding["backend_hash_recomputed"])
        self.assertEqual(evidence["model_ids_changed"], [])
        self.assertEqual(evidence["formula_ids_changed"], [])
        self.assertEqual(evidence["parameter_ids_changed"], [])
        self.assertFalse(evidence["financial_data_loaded"])
        self.assertFalse(evidence["database_changed"])


if __name__ == "__main__":
    unittest.main()
