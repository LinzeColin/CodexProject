from __future__ import annotations

import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
STYLE_PATH = ROOT / "web" / "styles.css"
INDEX_PATH = ROOT / "web" / "index.html"
PHASE_DIR = ROOT / "reports" / "pfi_v024" / "stage_6" / "phase_6_1"


class TestV024Stage6Phase61DesignSystem(unittest.TestCase):
    def setUp(self) -> None:
        self.css = STYLE_PATH.read_text(encoding="utf-8")
        self.index = INDEX_PATH.read_text(encoding="utf-8")

    def test_phase61_locks_default_light_design_tokens(self) -> None:
        self.assertIn('<meta name="color-scheme" content="light" />', self.index)
        self.assertIn('data-v024-stage6-design-system="phase_6_1"', self.index)
        self.assertIn("body[data-pfi-target-version=\"v0.2.4\"]", self.css)
        self.assertIn("color-scheme: light;", self.css)

        required_tokens = [
            "--pfi-v024-light-bg",
            "--pfi-v024-surface",
            "--pfi-v024-surface-raised",
            "--pfi-v024-text",
            "--pfi-v024-muted",
            "--pfi-v024-border",
            "--pfi-v024-space-2",
            "--pfi-v024-space-3",
            "--pfi-v024-space-4",
            "--pfi-v024-radius-card",
            "--pfi-v024-radius-control",
            "--pfi-v024-shadow-card",
            "--pfi-v024-font",
        ]
        for token in required_tokens:
            self.assertIn(token, self.css)

        dark_ai_colors = ("#0f172a", "#111827", "#121416", "#17202a")
        scoped_block = self.css.split("/* PFI v0.2.4 Stage 6 Phase 6.1 design system */", 1)[-1]
        for color in dark_ai_colors:
            self.assertNotIn(color, scoped_block)

    def test_status_color_system_covers_all_required_states(self) -> None:
        required_status_tokens = [
            "--pfi-v024-status-ready",
            "--pfi-v024-status-success",
            "--pfi-v024-status-warning",
            "--pfi-v024-status-danger",
            "--pfi-v024-status-blocked",
            "--pfi-v024-status-loading",
            "--pfi-v024-status-empty",
        ]
        for token in required_status_tokens:
            self.assertRegex(self.css, rf"{re.escape(token)}:\s*#[0-9a-fA-F]{{6}};")

        for selector in (
            ".status-ready",
            ".status-review",
            ".status-watch",
            ".stage5-ux-state-loading",
            ".stage5-ux-state-success",
            ".stage5-ux-state-error",
            ".stage5-ux-state-empty",
        ):
            self.assertIn(f'body[data-pfi-target-version="v0.2.4"] {selector}', self.css)

    def test_cards_tables_and_chart_slots_share_design_system(self) -> None:
        scoped_selectors = [
            ".metric-tile",
            ".home-question-card",
            ".workflow-card",
            ".stage4-section",
            ".stage5-ux-state",
            ".compact-table",
            ".chart-strip",
            ".trend-empty",
        ]
        for selector in scoped_selectors:
            self.assertIn(f'body[data-pfi-target-version="v0.2.4"] {selector}', self.css)

        self.assertIn("border-radius: var(--pfi-v024-radius-card);", self.css)
        self.assertIn("box-shadow: var(--pfi-v024-shadow-card);", self.css)
        self.assertIn("background: var(--pfi-v024-chart-slot-bg);", self.css)
        self.assertIn("border: 1px solid var(--pfi-v024-table-border);", self.css)

    def test_responsive_layout_is_defined_for_mobile_without_preview_frame(self) -> None:
        self.assertIn("@media (max-width: 780px)", self.css)
        self.assertIn('body[data-pfi-target-version="v0.2.4"] .app-shell', self.css)
        self.assertIn('body[data-pfi-target-version="v0.2.4"] .top-bar', self.css)
        self.assertIn('body[data-pfi-target-version="v0.2.4"] .metric-grid', self.css)
        self.assertIn('body[data-pfi-target-version="v0.2.4"] .home-question-grid', self.css)
        self.assertIn("grid-template-columns: 1fr;", self.css)
        self.assertNotIn("phone-preview", self.index + self.css)
        self.assertNotIn("mobile-preview-frame", self.index + self.css)

    def test_phase61_evidence_and_non_goals_are_machine_readable(self) -> None:
        evidence_path = PHASE_DIR / "evidence.json"
        token_validation_path = PHASE_DIR / "design_token_validation.json"
        terminal_path = PHASE_DIR / "terminal.log"
        changed_files_path = PHASE_DIR / "changed_files.txt"
        risk_path = PHASE_DIR / "risk_and_rollback.md"

        for path in (evidence_path, token_validation_path, terminal_path, changed_files_path, risk_path):
            self.assertTrue(path.exists(), str(path))

        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        token_validation = json.loads(token_validation_path.read_text(encoding="utf-8"))

        self.assertEqual(evidence["schema"], "PFIV024Stage6Phase61EvidenceV1")
        self.assertEqual(evidence["target_version"], "v0.2.4")
        self.assertEqual(evidence["stage"], "Stage 6")
        self.assertEqual(evidence["phase_id"], "6.1")
        self.assertEqual(evidence["phase_name"], "设计系统")
        self.assertEqual(evidence["task_ids"], ["T6.1.1", "T6.1.2", "T6.1.3", "T6.1.4"])
        self.assertTrue(evidence["phase_6_1_complete"])
        self.assertFalse(evidence["phase_6_2_started"])
        self.assertFalse(evidence["phase_6_3_started"])
        self.assertFalse(evidence["stage_6_whole_review_complete"])
        self.assertFalse(evidence["github_main_uploaded"])
        self.assertFalse(evidence["app_bundle_reinstall_executed"])
        self.assertFalse(evidence["data_logic_changes_made"])
        self.assertIn("Phase 6.2 motion feedback", evidence["explicitly_not_done"])
        self.assertIn("Phase 6.3 haptics and settings isolation", evidence["explicitly_not_done"])

        self.assertEqual(token_validation["status"], "pass")
        self.assertGreaterEqual(token_validation["light_token_count"], 20)
        self.assertGreaterEqual(token_validation["status_token_count"], 7)
        self.assertTrue(token_validation["mobile_layout_contract"])


if __name__ == "__main__":
    unittest.main()
