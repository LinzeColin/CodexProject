from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent
INDEX_PATH = ROOT / "web" / "index.html"
SHELL_PATH = ROOT / "web" / "app" / "shell.js"
FEEDBACK_PATH = ROOT / "web" / "app" / "feedback.js"
SETTINGS_PATH = ROOT / "web" / "app" / "pages" / "settings.js"
PHASE_DIR = ROOT / "reports" / "pfi_v024" / "stage_6" / "phase_6_3"


def node_executable() -> str | None:
    candidates = [
        os.environ.get("PFI_NODE"),
        shutil.which("node"),
        "/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    return None


def node_json(script: str) -> dict[str, object]:
    node = node_executable()
    if not node:
        raise AssertionError("Node runtime is required for Stage 6 Phase 6.3 contract tests")
    completed = subprocess.run(
        [node, "-e", script],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    return json.loads(completed.stdout)


class TestV024Stage6Phase63HapticsSettings(unittest.TestCase):
    def setUp(self) -> None:
        self.index = INDEX_PATH.read_text(encoding="utf-8")
        self.shell = SHELL_PATH.read_text(encoding="utf-8")
        self.feedback = FEEDBACK_PATH.read_text(encoding="utf-8")
        self.settings = SETTINGS_PATH.read_text(encoding="utf-8")

    def test_phase63_feedback_contract_is_v024_and_phase_limited(self) -> None:
        script = """
const feedback = require('./PFI/web/app/feedback.js');
console.log(JSON.stringify(feedback.buildStage6Phase63HapticsContract()));
"""
        contract = node_json(script)

        self.assertEqual(contract["schema"], "PFIV024Stage6Phase63HapticsContractV1")
        self.assertEqual(contract["target_version"], "v0.2.4")
        self.assertEqual(contract["stage"], "Stage 6")
        self.assertEqual(contract["phase_id"], "6.3")
        self.assertEqual(contract["phase_name"], "触感与设置隔离")
        self.assertTrue(contract["current_phase_only"])
        self.assertEqual(contract["task_ids"], ["T6.3.1", "T6.3.2", "T6.3.3"])
        self.assertTrue(contract["stage_contract"]["phase_6_1_complete"])
        self.assertTrue(contract["stage_contract"]["phase_6_2_complete"])
        self.assertTrue(contract["stage_contract"]["phase_6_3_complete"])
        self.assertFalse(contract["stage_contract"]["stage_6_whole_review_complete"])
        self.assertFalse(contract["stage_contract"]["github_main_uploaded"])
        self.assertIn("Stage 6 whole-stage review", contract["explicitly_not_done"])
        self.assertIn("GitHub main upload", contract["explicitly_not_done"])

    def test_haptic_model_detects_vibrate_and_silently_degrades_when_unsupported(self) -> None:
        script = """
const feedback = require('./PFI/web/app/feedback.js');
const capable = feedback.buildStage6Phase63HapticsModel({ navigator: { vibrate: function () { return true; } } });
const unavailable = feedback.buildStage6Phase63HapticsModel({ navigator: {} });
const nonFunction = feedback.buildStage6Phase63HapticsModel({ navigator: { vibrate: true } });
console.log(JSON.stringify({ capable, unavailable, nonFunction }));
"""
        result = node_json(script)
        capable = result["capable"]
        unavailable = result["unavailable"]
        non_function = result["nonFunction"]

        self.assertEqual(capable["schema"], "PFIV024Stage6Phase63HapticsModelV1")
        self.assertEqual(capable["phase_id"], "6.3")
        self.assertTrue(capable["capability"]["can_vibrate"])
        self.assertEqual(capable["capability"]["source"], "navigator.vibrate")
        self.assertTrue(capable["supported_device_only"])
        self.assertTrue(capable["preferences"]["can_disable"])
        self.assertEqual(capable["preferences"]["setting_route"], "/settings?tab=feedback")
        levels = {item["level_id"]: item for item in capable["levels"]}
        self.assertEqual(set(levels), {"select", "confirm", "warning", "blocked"})
        for level_id, item in levels.items():
            self.assertLessEqual(max(item["pattern_ms"]), 80, level_id)
            self.assertRegex(item["label_zh"], r"[\u4e00-\u9fff]")

        for model in (unavailable, non_function):
            self.assertFalse(model["capability"]["can_vibrate"])
            self.assertTrue(model["silent_degradation"]["enabled"])
            self.assertEqual(model["silent_degradation"]["degrade_to"], "visual_feedback")
            self.assertRegex(model["silent_degradation"]["reason_zh"], r"[\u4e00-\u9fff]")

    def test_settings_page_model_hosts_feedback_toggles_only_in_settings(self) -> None:
        script = """
const settings = require('./PFI/web/app/pages/settings.js');
console.log(JSON.stringify(settings.buildStage6Phase63FeedbackSettingsViewModel()));
"""
        model = node_json(script)

        self.assertEqual(model["schema"], "PFIV024Stage6Phase63FeedbackSettingsViewModelV1")
        self.assertEqual(model["target_version"], "v0.2.4")
        self.assertEqual(model["stage"], "Stage 6")
        self.assertEqual(model["phase_id"], "6.3")
        self.assertEqual(model["page"], "settings")
        self.assertEqual(model["route_alias"], "/settings?tab=feedback")
        self.assertEqual(model["visible_on_workspaces"], ["settings"])
        self.assertFalse(model["business_pages_show_feedback_console"])
        self.assertEqual(set(model["toggle_ids"]), {"haptic", "sound", "motion"})
        self.assertTrue(model["toggles"]["haptic"]["default_enabled"])
        self.assertTrue(model["toggles"]["haptic"]["can_disable"])
        self.assertEqual(model["toggles"]["haptic"]["unsupported_behavior"], "silent_visual_degradation")
        self.assertTrue(model["isolation_policy"]["hidden_outside_settings"])

    def test_runtime_marks_phase63_and_keeps_feedback_console_out_of_business_pages(self) -> None:
        self.assertIn('data-pfi-phase="6.3"', self.index)
        self.assertIn('data-v024-stage6-haptics-settings="phase_6_3"', self.index)
        self.assertIn("data-settings-feedback-console hidden", self.index)
        self.assertIn('data-feedback-toggle="haptic"', self.index)
        self.assertIn('data-feedback-toggle="motion"', self.index)
        self.assertIn('settingsConsole.hidden = workspaceId !== "settings"', self.shell)
        self.assertIn('main.dataset.settingsSurface = workspaceId === "settings" ? "primary_workspace" : "none"', self.shell)
        self.assertNotIn("data-settings-feedback-console", self.settings)

        business_workspaces = [
            "home",
            "accounts",
            "ledger",
            "investment",
            "consumption",
            "sync",
            "recommendations",
            "insights",
            "market_research",
        ]
        model_text = json.dumps(node_json("""
const settings = require('./PFI/web/app/pages/settings.js');
console.log(JSON.stringify(settings.buildStage6Phase63FeedbackSettingsViewModel()));
"""), ensure_ascii=False)
        for workspace in business_workspaces:
            self.assertNotIn(f'"{workspace}"', model_text)

    def test_shell_haptics_runtime_uses_function_detection_and_silent_degradation(self) -> None:
        required = [
            "PFI_V024_STAGE6_HAPTICS_CONTRACT",
            "detectV024HapticRuntimeCapability",
            'document.body.dataset.v024HapticCapability = canVibrate ? "supported" : "unsupported"',
            'typeof navigator.vibrate !== "function"',
            'document.body.dataset.v024HapticDegraded = "visual_feedback"',
            'feedbackRuntimeState.haptic = Boolean(toggle.checked)',
            'toggle.dataset.v024FeedbackSetting = "phase_6_3"',
        ]
        for snippet in required:
            self.assertIn(snippet, self.shell)

    def test_phase63_evidence_and_non_goals_are_machine_readable(self) -> None:
        evidence_path = PHASE_DIR / "evidence.json"
        audit_path = PHASE_DIR / "haptic_settings_validation.json"
        terminal_path = PHASE_DIR / "terminal.log"
        changed_files_path = PHASE_DIR / "changed_files.txt"
        risk_path = PHASE_DIR / "risk_and_rollback.md"

        for path in (evidence_path, audit_path, terminal_path, changed_files_path, risk_path):
            self.assertTrue(path.exists(), str(path))

        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        audit = json.loads(audit_path.read_text(encoding="utf-8"))

        self.assertEqual(evidence["schema"], "PFIV024Stage6Phase63EvidenceV1")
        self.assertEqual(evidence["target_version"], "v0.2.4")
        self.assertEqual(evidence["stage"], "Stage 6")
        self.assertEqual(evidence["phase_id"], "6.3")
        self.assertEqual(evidence["phase_name"], "触感与设置隔离")
        self.assertEqual(evidence["task_ids"], ["T6.3.1", "T6.3.2", "T6.3.3"])
        self.assertTrue(evidence["phase_6_1_complete"])
        self.assertTrue(evidence["phase_6_2_complete"])
        self.assertTrue(evidence["phase_6_3_complete"])
        self.assertFalse(evidence["stage_6_whole_review_complete"])
        self.assertFalse(evidence["github_main_uploaded"])
        self.assertFalse(evidence["app_bundle_reinstall_executed"])
        self.assertFalse(evidence["data_logic_changes_made"])
        self.assertIn("Stage 6 whole-stage review", evidence["explicitly_not_done"])

        self.assertEqual(audit["schema"], "PFIV024Stage6Phase63HapticSettingsValidationV1")
        self.assertEqual(audit["status"], "pass")
        self.assertTrue(audit["capability_detection"]["uses_navigator_vibrate_function_check"])
        self.assertTrue(audit["settings_isolation"]["visible_only_in_settings"])
        self.assertFalse(audit["settings_isolation"]["business_pages_show_feedback_console"])
        self.assertTrue(audit["unsupported_degradation"]["silent_visual_degradation"])


if __name__ == "__main__":
    unittest.main()
