from __future__ import annotations

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent
NODE_CANDIDATE = "/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node"
STAGE6_DIR = ROOT / "reports" / "pfi_v024" / "stage_6"
REVIEW_DIR = STAGE6_DIR / "whole_stage_review"
SCREENSHOT_DIR = REVIEW_DIR / "screenshots"
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


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def node_executable() -> str:
    candidates = [os.environ.get("PFI_NODE"), shutil.which("node"), NODE_CANDIDATE]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    raise AssertionError("Node runtime is required for Stage 6 whole-stage review tests")


def node_json(script: str) -> dict[str, object]:
    completed = subprocess.run(
        [node_executable(), "-e", script],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    return json.loads(completed.stdout)


def css_ms_values(css: str) -> list[int]:
    return [int(value) for value in re.findall(r"(\d+)ms", css)]


class TestV024Stage6WholeReviewContract(unittest.TestCase):
    def test_whole_stage_review_artifacts_exist_and_scope_is_bounded(self) -> None:
        expected_files = [
            ROOT / "docs" / "pfi_v024" / "STAGE6_WHOLE_STAGE_REVIEW.md",
            ROOT / "scripts" / "validate_v024_stage6_whole_review_browser.js",
            REVIEW_DIR / "evidence.json",
            REVIEW_DIR / "browser_validation.json",
            REVIEW_DIR / "terminal.log",
            REVIEW_DIR / "changed_files.txt",
            REVIEW_DIR / "risk_and_rollback.md",
            SCREENSHOT_DIR / "desktop_light_home.png",
            SCREENSHOT_DIR / "mobile_responsive.png",
        ]
        for path in expected_files:
            self.assertTrue(path.exists(), str(path))

        evidence = read_json(REVIEW_DIR / "evidence.json")
        self.assertEqual(evidence["schema"], "PFIV024Stage6WholeReviewEvidenceV1")
        self.assertEqual(evidence["target_version"], "v0.2.4")
        self.assertEqual(evidence["source_package_version"], "v0.2.3-repair")
        self.assertEqual(evidence["stage"], "Stage 6")
        self.assertEqual(evidence["review_id"], "stage_6_whole_review")
        self.assertEqual(evidence["current_run_unit"], "Stage 6 whole-stage review")
        self.assertTrue(evidence["current_run_only"])
        self.assertEqual(evidence["status"], "pass")
        self.assertTrue(evidence["stage_6_candidate_complete"])
        self.assertTrue(evidence["stage_6_whole_review_complete"])
        self.assertFalse(evidence["stage_7_started"])
        self.assertFalse(evidence["github_main_uploaded"])
        self.assertIn("Stage 7", evidence["explicitly_not_done"])
        self.assertIn("GitHub main upload", evidence["explicitly_not_done"])

    def test_phase_evidence_and_runtime_contracts_prove_stage6_acceptance(self) -> None:
        phase61 = read_json(STAGE6_DIR / "phase_6_1" / "evidence.json")
        phase62 = read_json(STAGE6_DIR / "phase_6_2" / "evidence.json")
        phase63 = read_json(STAGE6_DIR / "phase_6_3" / "evidence.json")
        token_validation = read_json(STAGE6_DIR / "phase_6_1" / "design_token_validation.json")
        motion_validation = read_json(STAGE6_DIR / "phase_6_2" / "motion_feedback_validation.json")
        haptic_validation = read_json(STAGE6_DIR / "phase_6_3" / "haptic_settings_validation.json")
        evidence = read_json(REVIEW_DIR / "evidence.json")

        self.assertEqual(evidence["reviewed_phase_ids"], ["6.1", "6.2", "6.3"])
        self.assertEqual(evidence["phase_statuses"], {
            "phase_6_1": "candidate_pass",
            "phase_6_2": "candidate_pass",
            "phase_6_3": "candidate_pass",
        })
        self.assertEqual([phase61["status"], phase62["status"], phase63["status"]], ["pass", "pass", "pass"])
        self.assertTrue(phase61["phase_6_1_complete"])
        self.assertTrue(phase62["phase_6_2_complete"])
        self.assertTrue(phase63["phase_6_3_complete"])
        self.assertEqual(token_validation["status"], "pass")
        self.assertEqual(motion_validation["status"], "pass")
        self.assertEqual(haptic_validation["status"], "pass")

        runtime = node_json("""
const feedback = require('./PFI/web/app/feedback.js');
const settings = require('./PFI/web/app/pages/settings.js');
console.log(JSON.stringify({
  motion: feedback.buildStage6Phase62MotionFeedbackModel(),
  haptics: feedback.buildStage6Phase63HapticsModel({ navigator: {} }),
  settings: settings.buildStage6Phase63FeedbackSettingsViewModel()
}));
""")
        self.assertLessEqual(runtime["motion"]["page_transition"]["max_duration_ms"], 220)
        self.assertTrue(runtime["motion"]["reduced_motion"]["supported"])
        self.assertTrue(runtime["haptics"]["supported_device_only"])
        self.assertTrue(runtime["haptics"]["preferences"]["can_disable"])
        self.assertTrue(runtime["haptics"]["silent_degradation"]["enabled"])
        self.assertEqual(runtime["settings"]["visible_on_workspaces"], ["settings"])
        self.assertFalse(runtime["settings"]["business_pages_show_feedback_console"])

    def test_browser_validation_covers_stage6_visual_and_settings_pass_gate(self) -> None:
        browser = read_json(REVIEW_DIR / "browser_validation.json")

        self.assertEqual(browser["schema"], "PFIV024Stage6WholeReviewBrowserValidationV1")
        self.assertEqual(browser["status"], "pass")
        self.assertEqual(browser["target_version"], "v0.2.4")
        self.assertEqual(browser["stage"], "Stage 6")
        self.assertEqual(browser["primary_entry_count"], 10)
        self.assertEqual(tuple(browser["primary_workspaces"]), PRIMARY_WORKSPACES)
        self.assertTrue(browser["default_light_ui"])
        self.assertGreaterEqual(browser["body_background_luminance"], 210)
        self.assertTrue(browser["desktop_light_home_screenshot"])
        self.assertTrue(browser["mobile_responsive_screenshot"])
        self.assertFalse(browser["desktop_phone_preview_frame_visible"])
        self.assertTrue(browser["settings_feedback_console_hidden_on_home"])
        self.assertTrue(browser["settings_feedback_console_visible_on_settings"])
        self.assertTrue(browser["haptic_capability_detected"])
        self.assertIn(browser["haptic_capability"], {"supported", "unsupported"})
        self.assertTrue(browser["haptic_degrades_visually_when_unsupported"])
        self.assertEqual(browser["console_errors"], [])
        self.assertEqual(browser["page_errors"], [])
        self.assertEqual(browser["http_errors"], [])

        screenshots = {item["file"]: item for item in browser["screenshots"]}
        for filename in ("desktop_light_home.png", "mobile_responsive.png"):
            self.assertIn(filename, screenshots)
            path = SCREENSHOT_DIR / filename
            self.assertTrue(path.exists(), str(path))
            self.assertGreater(path.stat().st_size, 20_000, str(path))

    def test_stop_conditions_are_recorded_as_absent(self) -> None:
        evidence = read_json(REVIEW_DIR / "evidence.json")
        browser = read_json(REVIEW_DIR / "browser_validation.json")
        css = (ROOT / "web" / "styles.css").read_text(encoding="utf-8")
        html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        shell = (ROOT / "web" / "app" / "shell.js").read_text(encoding="utf-8")

        stop_conditions = evidence["stop_condition_audit"]
        self.assertEqual(stop_conditions["dark_ai_console_style"], "absent")
        self.assertEqual(stop_conditions["decorative_or_interfering_motion"], "absent")
        self.assertEqual(stop_conditions["haptics_cannot_be_disabled"], "absent")
        self.assertEqual(stop_conditions["feedback_console_on_business_pages"], "absent")

        self.assertGreaterEqual(browser["body_background_luminance"], 210)
        self.assertFalse(browser["desktop_phone_preview_frame_visible"])
        self.assertTrue(browser["settings_feedback_console_hidden_on_home"])
        self.assertTrue(browser["settings_feedback_console_visible_on_settings"])
        self.assertLessEqual(max(css_ms_values(css)), 3000)
        self.assertIn("@media (prefers-reduced-motion: reduce)", css)
        self.assertIn('typeof navigator.vibrate !== "function"', shell)
        self.assertIn('feedbackRuntimeState.haptic = Boolean(toggle.checked)', shell)
        self.assertNotIn("phone-preview", html + css)
        self.assertNotIn("mobile-preview-frame", html + css)

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
        self.assertEqual(command_status["node stage6 whole review browser validation"], "pass")
        self.assertEqual(command_status["pytest stage6 whole review contract"], "pass")
        self.assertEqual(command_status["pytest stage6 phase regression"], "pass")
        self.assertEqual(command_status["pytest stage5 adjacent regression"], "pass")
        self.assertEqual(command_status["node syntax checks"], "pass")
        self.assertEqual(command_status["json evidence checks"], "pass")
        self.assertEqual(command_status["git diff --check -- PFI"], "pass")

        self.assertFalse(evidence["github_main_uploaded"])
        self.assertIn("GitHub main upload", evidence["remaining_gates"])


if __name__ == "__main__":
    unittest.main()
