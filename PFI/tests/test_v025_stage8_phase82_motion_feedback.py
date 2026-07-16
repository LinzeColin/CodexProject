from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = ROOT / "web" / "index.html"
SHELL_PATH = ROOT / "web" / "app" / "shell.js"
MOTION_PATH = ROOT / "web" / "app" / "motion.js"
HAPTICS_PATH = ROOT / "web" / "app" / "haptics.js"
JOB_TIMELINE_PATH = ROOT / "web" / "app" / "components" / "jobTimeline.js"
TOKENS_PATH = ROOT / "web" / "styles" / "tokens.css"
PHASE_DIR = ROOT / "reports" / "pfi_v025" / "stage_8" / "phase_8_2"


class TestV025Stage8Phase82MotionFeedback(unittest.TestCase):
    def setUp(self) -> None:
        self.index = INDEX_PATH.read_text(encoding="utf-8")
        self.shell = SHELL_PATH.read_text(encoding="utf-8")
        self.css = TOKENS_PATH.read_text(encoding="utf-8")
        self.motion = MOTION_PATH.read_text(encoding="utf-8") if MOTION_PATH.exists() else ""
        self.haptics = HAPTICS_PATH.read_text(encoding="utf-8") if HAPTICS_PATH.exists() else ""
        self.jobs = JOB_TIMELINE_PATH.read_text(encoding="utf-8") if JOB_TIMELINE_PATH.exists() else ""

    def test_phase82_contracts_remain_mounted_after_phase83_without_claiming_stage_acceptance(self) -> None:
        self.assertIn('data-v025-stage8-motion-feedback="phase_8_2"', self.index)
        for script in (
            '<script src="./app/motion.js"></script>',
            '<script src="./app/haptics.js"></script>',
            '<script src="./app/components/jobTimeline.js"></script>',
        ):
            self.assertIn(script, self.index)
        self.assertIn('data-v025-stage8-accessibility="phase_8_3"', self.index)
        self.assertIn('<script src="./app/accessibility.js"></script>', self.index)
        self.assertNotIn('data-v025-stage8-whole-review="pass"', self.index)
        self.assertNotIn('data-v025-stage9=', self.index)
        self.assertIn("PFI_V025_STAGE8_MOTION", self.motion)
        self.assertIn("PFI_V025_STAGE8_HAPTICS", self.haptics)
        self.assertIn("PFI_V025_STAGE8_JOB_TIMELINE", self.jobs)

    def test_motion_budget_is_bounded_progressive_and_reduced_motion_safe(self) -> None:
        for name, value in (("instant", 100), ("cached", 300), ("staged", 1000), ("durable", 10000)):
            self.assertIn(f"{name}: {value}", self.motion)
        self.assertIn('matchMedia("(prefers-reduced-motion: reduce)")', self.motion)
        self.assertIn("document.startViewTransition", self.motion)
        self.assertIn("progressive_enhancement", self.motion)
        self.assertIn("maxMotionMs: 220", self.motion)
        self.assertIn("reducedMotionActive() ? 0", self.motion)
        for forbidden in ("left:", "top:", "width:", "height:"):
            self.assertNotIn(forbidden, self.motion)
        self.assertNotIn("setInterval", self.motion)

    def test_feedback_budget_never_turns_elapsed_time_into_fake_percent(self) -> None:
        self.assertNotIn('state === "progress" ? "64%"', self.shell)
        self.assertIn("completedUnits", self.jobs)
        self.assertIn("totalUnits", self.jobs)
        self.assertIn("actualProgress", self.jobs)
        self.assertIn('progress.removeAttribute("value")', self.jobs)
        self.assertNotIn("syntheticProgress", self.jobs)
        self.assertNotIn("setInterval", self.jobs)
        self.assertIn('data-stage8-feedback-budget="phase_8_2"', self.index)

    def test_haptics_and_sound_are_explicit_opt_in_with_silent_degradation(self) -> None:
        self.assertIn("haptic: false", self.haptics)
        self.assertIn("sound: false", self.haptics)
        self.assertIn("navigator.vibrate", self.haptics)
        self.assertIn("navigator.userActivation", self.haptics)
        self.assertIn("navigator.userActivation?.isActive === true", self.haptics)
        self.assertIn("visual_only", self.haptics)
        self.assertIn("AudioContext", self.haptics)
        self.assertIn("feedbackHaptic: false", self.shell)
        self.assertIn("feedback_haptic: false", self.shell)
        self.assertNotIn('data-feedback-toggle="haptic" checked', self.index)

    def test_long_job_timeline_is_durable_across_routes_and_uses_real_states(self) -> None:
        for state in ("queued", "running", "blocked", "succeeded", "failed", "cancelled"):
            self.assertIn(f'"{state}"', self.jobs)
        self.assertIn("sessionStorage", self.jobs)
        self.assertIn("durableMs: 10000", self.jobs)
        self.assertIn("stageMs: 1000", self.jobs)
        self.assertIn("MutationObserver", self.jobs)
        self.assertIn('data-stage8-job-timeline', self.jobs)
        self.assertIn("leave_page_safe", self.jobs)
        self.assertIn("PFI_V025_STAGE8_JOB_TIMELINE", self.shell)
        self.assertIn('value === null || value === undefined || value === ""', self.jobs)

    def test_scoped_motion_styles_use_state_not_decoration(self) -> None:
        self.assertIn('body[data-v025-stage8-motion-feedback="phase_8_2"]', self.css)
        self.assertIn("@media (prefers-reduced-motion: reduce)", self.css)
        self.assertIn("data-stage8-job-state", self.css)
        phase82_start = self.css.index("/* v0.2.5 Stage 8 Phase 8.2")
        phase82_end = self.css.index('body[data-v025-stage8-design-system="phase_8_1"]', phase82_start)
        phase82_css = self.css[phase82_start:phase82_end]
        self.assertNotIn("repeating-linear-gradient", phase82_css)
        self.assertNotIn("animation-iteration-count: infinite", phase82_css)
        self.assertIn("transition-property: transform, opacity;", phase82_css)
        self.assertNotIn("transition-property: transform, opacity, border-color", phase82_css)
        self.assertIn("animation-duration: 0ms !important;", phase82_css)

    def test_phase_evidence_is_complete_and_stays_below_whole_stage_acceptance(self) -> None:
        required = (
            "evidence.json",
            "phase_contract.json",
            "feedback_budget.json",
            "motion_validation.json",
            "haptics_capability.json",
            "job_timeline_validation.json",
            "browser_validation.json",
            "terminal.log",
            "changed_files.txt",
            "risk_and_rollback.md",
            "browser_trace.zip",
        )
        for name in required:
            self.assertTrue((PHASE_DIR / name).is_file(), name)
        evidence = json.loads((PHASE_DIR / "evidence.json").read_text(encoding="utf-8"))
        self.assertEqual(evidence["schema"], "PFIV025Stage8Phase82EvidenceV1")
        self.assertEqual(evidence["task_ids"], ["S8-P2-T1", "S8-P2-T2", "S8-P2-T3", "S8-P2-T4"])
        self.assertEqual(evidence["acceptance_id"], "ACC-PFI-V025-STAGE8-WHOLE-REVIEW")
        self.assertTrue(evidence["phase_8_2_complete"])
        self.assertFalse(evidence["phase_8_3_started"])
        self.assertFalse(evidence["stage_8_whole_review_complete"])
        self.assertFalse(evidence["github_main_uploaded"])
        self.assertFalse(evidence["app_bundle_reinstall_executed"])
        self.assertFalse(evidence["finder_used"])


if __name__ == "__main__":
    unittest.main()
