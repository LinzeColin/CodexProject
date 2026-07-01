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
STYLE_PATH = ROOT / "web" / "styles.css"
INDEX_PATH = ROOT / "web" / "index.html"
SHELL_PATH = ROOT / "web" / "app" / "shell.js"
FEEDBACK_PATH = ROOT / "web" / "app" / "feedback.js"
PHASE_DIR = ROOT / "reports" / "pfi_v024" / "stage_6" / "phase_6_2"


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
        raise AssertionError("Node runtime is required for Stage 6 Phase 6.2 contract tests")
    completed = subprocess.run(
        [node, "-e", script],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    return json.loads(completed.stdout)


class TestV024Stage6Phase62MotionFeedback(unittest.TestCase):
    def setUp(self) -> None:
        self.css = STYLE_PATH.read_text(encoding="utf-8")
        self.index = INDEX_PATH.read_text(encoding="utf-8")
        self.shell = SHELL_PATH.read_text(encoding="utf-8")
        self.feedback = FEEDBACK_PATH.read_text(encoding="utf-8")

    def test_phase62_feedback_contract_is_v024_and_phase_limited(self) -> None:
        script = """
const feedback = require('./PFI/web/app/feedback.js');
console.log(JSON.stringify(feedback.buildStage6Phase62MotionContract()));
"""
        contract = node_json(script)

        self.assertEqual(contract["schema"], "PFIV024Stage6Phase62MotionContractV1")
        self.assertEqual(contract["target_version"], "v0.2.4")
        self.assertEqual(contract["stage"], "Stage 6")
        self.assertEqual(contract["phase_id"], "6.2")
        self.assertEqual(contract["phase_name"], "动效反馈")
        self.assertTrue(contract["current_phase_only"])
        self.assertEqual(contract["task_ids"], ["T6.2.1", "T6.2.2", "T6.2.3", "T6.2.4"])
        self.assertTrue(contract["stage_contract"]["phase_6_1_complete"])
        self.assertTrue(contract["stage_contract"]["phase_6_2_complete"])
        self.assertFalse(contract["stage_contract"]["phase_6_3_started"])
        self.assertFalse(contract["stage_contract"]["stage_6_whole_review_complete"])
        self.assertFalse(contract["stage_contract"]["github_main_uploaded"])
        self.assertIn("Phase 6.3 haptics and settings isolation", contract["explicitly_not_done"])
        self.assertIn("Stage 6 whole-stage review", contract["explicitly_not_done"])
        self.assertIn("GitHub main upload", contract["explicitly_not_done"])

    def test_phase62_motion_model_covers_transition_skeleton_feedback_and_report_progress(self) -> None:
        script = """
const feedback = require('./PFI/web/app/feedback.js');
console.log(JSON.stringify(feedback.buildStage6Phase62MotionFeedbackModel()));
"""
        model = node_json(script)

        self.assertEqual(model["schema"], "PFIV024Stage6Phase62MotionFeedbackModelV1")
        self.assertEqual(model["target_version"], "v0.2.4")
        self.assertLessEqual(model["page_transition"]["duration_ms"], 220)
        self.assertEqual(model["page_transition"]["route_state_attribute"], "data-v024-route-transition")
        self.assertEqual(model["loading_skeleton"]["css_selector"], ".v024-skeleton-row")
        states = {item["state"]: item for item in model["feedback_states"]}
        self.assertEqual(set(states), {"loading", "success", "error", "blocked", "progress"})
        for state, item in states.items():
            self.assertRegex(item["label_zh"], r"[\u4e00-\u9fff]", state)
            self.assertIn(item["aria_live"], {"polite", "assertive"})
            self.assertLessEqual(item["max_motion_ms"], 240)
        self.assertEqual(model["report_generation_progress"]["schema"], "PFIV024Stage6Phase62ReportProgressV1")
        self.assertGreaterEqual(len(model["report_generation_progress"]["steps"]), 4)
        self.assertIn("检查真实数据状态", json.dumps(model["report_generation_progress"], ensure_ascii=False))
        self.assertTrue(model["reduced_motion"]["supported"])
        self.assertIn("body.reduce-motion", model["reduced_motion"]["selectors"])
        self.assertFalse(model["phase_6_3_haptics_settings_started"])
        self.assertNotIn("navigator.vibrate", json.dumps(model))

    def test_shell_marks_v024_route_transition_and_motion_feedback_states(self) -> None:
        required_shell_snippets = [
            "PFI_V024_STAGE6_MOTION_CONTRACT",
            "applyV024Stage6RouteTransition",
            'main.dataset.v024RouteTransition = "enter"',
            "delete main.dataset.v024RouteTransition",
            'feedback.dataset.v024MotionState = normalizedState',
            'feedback.dataset.v024FeedbackPhase = "6.2"',
            'skeleton.classList.add("v024-skeleton-row")',
            'skeleton.dataset.v024SkeletonState = "loading"',
            'jobLabel.dataset.v024ReportProgress = "phase_6_2"',
        ]
        for snippet in required_shell_snippets:
            self.assertIn(snippet, self.shell)

        self.assertIn('data-pfi-phase="6.2"', self.index)
        self.assertIn('data-v024-stage6-motion-feedback="phase_6_2"', self.index)

    def test_css_defines_v024_motion_feedback_without_excessive_or_dark_console_motion(self) -> None:
        self.assertIn("/* PFI v0.2.4 Stage 6 Phase 6.2 motion feedback */", self.css)
        required_css = [
            'body[data-pfi-target-version="v0.2.4"] .workspace[data-v024-route-transition="enter"]',
            'body[data-pfi-target-version="v0.2.4"] .workspace[data-v024-route-transition="exit"]',
            'body[data-pfi-target-version="v0.2.4"] .v024-skeleton-row span::after',
            'body[data-pfi-target-version="v0.2.4"] .action-feedback[data-v024-motion-state="progress"]',
            'body[data-pfi-target-version="v0.2.4"] .action-feedback[data-v024-motion-state="success"]',
            'body[data-pfi-target-version="v0.2.4"] .action-feedback[data-v024-motion-state="failure"]',
            'body[data-pfi-target-version="v0.2.4"] .action-feedback[data-v024-motion-state="blocked"]',
            'body[data-pfi-target-version="v0.2.4"] .report-progress[data-v024-report-progress="phase_6_2"]',
            'body[data-pfi-target-version="v0.2.4"] .report-progress-step[data-progress-state="loading"]',
            "@keyframes pfi-v024-page-enter",
            "@keyframes pfi-v024-skeleton-sheen",
            "@keyframes pfi-v024-progress-step",
            "@media (prefers-reduced-motion: reduce)",
            "body.reduce-motion",
        ]
        for snippet in required_css:
            self.assertIn(snippet, self.css)

        durations = [int(value) for value in re.findall(r"(\d+)ms", self.css)]
        self.assertTrue(any(value <= 220 for value in durations))
        scoped_block = self.css.split("/* PFI v0.2.4 Stage 6 Phase 6.2 motion feedback */", 1)[-1]
        for color in ("#0f172a", "#111827", "#121416", "#17202a"):
            self.assertNotIn(color, scoped_block)

    def test_phase62_evidence_and_non_goals_are_machine_readable(self) -> None:
        evidence_path = PHASE_DIR / "evidence.json"
        audit_path = PHASE_DIR / "motion_feedback_validation.json"
        terminal_path = PHASE_DIR / "terminal.log"
        changed_files_path = PHASE_DIR / "changed_files.txt"
        risk_path = PHASE_DIR / "risk_and_rollback.md"

        for path in (evidence_path, audit_path, terminal_path, changed_files_path, risk_path):
            self.assertTrue(path.exists(), str(path))

        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        audit = json.loads(audit_path.read_text(encoding="utf-8"))

        self.assertEqual(evidence["schema"], "PFIV024Stage6Phase62EvidenceV1")
        self.assertEqual(evidence["target_version"], "v0.2.4")
        self.assertEqual(evidence["stage"], "Stage 6")
        self.assertEqual(evidence["phase_id"], "6.2")
        self.assertEqual(evidence["phase_name"], "动效反馈")
        self.assertEqual(evidence["task_ids"], ["T6.2.1", "T6.2.2", "T6.2.3", "T6.2.4"])
        self.assertTrue(evidence["phase_6_1_complete"])
        self.assertTrue(evidence["phase_6_2_complete"])
        self.assertFalse(evidence["phase_6_3_started"])
        self.assertFalse(evidence["stage_6_whole_review_complete"])
        self.assertFalse(evidence["github_main_uploaded"])
        self.assertFalse(evidence["app_bundle_reinstall_executed"])
        self.assertFalse(evidence["data_logic_changes_made"])
        self.assertIn("Phase 6.3 haptics and settings isolation", evidence["explicitly_not_done"])

        self.assertEqual(audit["schema"], "PFIV024Stage6Phase62MotionValidationV1")
        self.assertEqual(audit["status"], "pass")
        self.assertEqual(audit["page_transition"]["duration_ms"], 180)
        self.assertEqual(audit["feedback_state_count"], 5)
        self.assertEqual(audit["report_generation_progress"]["step_count"], 4)
        self.assertTrue(audit["reduced_motion"]["supported"])
        self.assertFalse(audit["phase_6_3_haptics_settings_started"])


if __name__ == "__main__":
    unittest.main()
