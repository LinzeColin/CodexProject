from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TestV023Stage9VisualFeedback(unittest.TestCase):
    def setUp(self) -> None:
        self.html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        self.styles = (ROOT / "web" / "styles.css").read_text(encoding="utf-8")
        self.tokens = (ROOT / "web" / "styles" / "tokens.css").read_text(encoding="utf-8")
        self.css = "\n".join((self.tokens, self.styles))

    def test_phase91_scope_is_limited_to_design_system_css(self) -> None:
        self.assertIn('<link rel="stylesheet" href="./styles/tokens.css" />', self.html)
        self.assertIn('<link rel="stylesheet" href="./styles.css" />', self.html)
        self.assertLess(
            self.html.index("./styles/tokens.css"),
            self.html.index("./styles.css"),
        )

        for required in (
            "PFI v0.2.3 Stage 9 Phase 9.1 design system",
            "--pfi-v023-bg: #f7fafc",
            "--pfi-v023-surface: #ffffff",
            "--pfi-v023-surface-soft: #eef6ff",
            "--pfi-v023-accent-blue: #2563eb",
            "--pfi-v023-accent-teal: #0f766e",
            "--pfi-v023-accent-gold: #b7791f",
            "--pfi-v023-radius-card: 8px",
            "color-scheme: light;",
        ):
            self.assertIn(required, self.styles)

        self.assertNotIn("PFI/web/app/feedback.js", self.styles)
        self.assertNotIn("navigator.vibrate", self.styles)
        self.assertNotIn("report-progress", self.styles)

    def test_phase91_components_cover_cards_tables_buttons_and_chart_empty_states(self) -> None:
        for selector in (
            'body[data-pfi-version="v0.2.3"] .metric-tile',
            'body[data-pfi-version="v0.2.3"] .workflow-card',
            'body[data-pfi-version="v0.2.3"] .stage4-section',
            'body[data-pfi-version="v0.2.3"] .compact-table',
            'body[data-pfi-version="v0.2.3"] .primary-action',
            'body[data-pfi-version="v0.2.3"] .secondary-action',
            'body[data-pfi-version="v0.2.3"] .trend-empty',
            'body[data-pfi-version="v0.2.3"] .v023-chart-empty',
        ):
            self.assertIn(selector, self.styles)

        for required in (
            "box-shadow: var(--pfi-v023-shadow-card)",
            "border-radius: var(--pfi-v023-radius-card)",
            "background: var(--pfi-v023-surface)",
            "min-height: 44px",
            "border-collapse: separate",
            "暂无真实图表数据",
            "数据源与上传",
        ):
            self.assertIn(required, self.styles)

    def test_phase91_mobile_rules_keep_layout_usable_without_text_overlap(self) -> None:
        mobile_match = re.search(r"@media \(max-width: 780px\) \{(?P<body>.*)\n\}", self.styles, flags=re.S)
        self.assertIsNotNone(mobile_match)
        mobile_css = mobile_match.group("body")

        for required in (
            "body[data-pfi-version=\"v0.2.3\"] .app-shell",
            "grid-template-columns: 1fr",
            "padding-bottom: 86px",
            "overflow-x: auto",
            "scroll-snap-type: x proximity",
            "min-width: 96px",
            "white-space: normal",
            "word-break: break-word",
        ):
            self.assertIn(required, mobile_css)

    def test_phase91_doc_and_evidence_exist_before_candidate_pass(self) -> None:
        phase_dir = ROOT / "reports" / "pfi_v023" / "stage_9" / "phase_9_1"
        evidence_path = phase_dir / "evidence.json"
        css_audit_path = phase_dir / "design_system_audit.json"
        scan_path = phase_dir / "no_source_term_scan.json"
        changed_files_path = phase_dir / "changed_files.txt"
        terminal_log_path = phase_dir / "terminal.log"
        doc_path = ROOT / "docs" / "pfi_v023" / "STAGE9_VISUAL_FEEDBACK.md"

        for path in (evidence_path, css_audit_path, scan_path, changed_files_path, terminal_log_path, doc_path):
            self.assertTrue(path.exists(), str(path))

        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        audit = json.loads(css_audit_path.read_text(encoding="utf-8"))
        scan = json.loads(scan_path.read_text(encoding="utf-8"))
        changed_files = [line.strip() for line in changed_files_path.read_text(encoding="utf-8").splitlines() if line.strip()]

        self.assertEqual(evidence["version"], "v0.2.3")
        self.assertEqual(evidence["stage"], "Stage 9")
        self.assertEqual(evidence["phase_id"], "V023-S9-P9.1")
        self.assertEqual(evidence["phase_name"], "设计系统")
        self.assertEqual(evidence["status"], "candidate_pass")
        self.assertTrue(evidence["current_phase_only"])
        self.assertTrue(evidence["max_one_phase_per_run"])
        self.assertTrue(evidence["stage_contract"]["phase_9_1_design_system_done"])
        self.assertFalse(evidence["stage_contract"]["phase_9_2_motion_feedback_done"])
        self.assertFalse(evidence["stage_contract"]["phase_9_3_haptics_settings_done"])
        self.assertFalse(evidence["stage_contract"]["stage_9_whole_review_done"])
        self.assertFalse(evidence["stage_contract"]["github_main_upload_done"])
        self.assertEqual(evidence["changed_files"], changed_files)
        for key in (
            "light_tokens",
            "cards_tables_buttons",
            "chart_empty_states",
            "mobile_adaptation",
            "no_forbidden_financial_data_terms",
        ):
            self.assertTrue(evidence["acceptance_checks"][key], key)

        self.assertEqual(audit["schema"], "PFIV023Stage9Phase91DesignSystemAuditV1")
        self.assertEqual(audit["phase_id"], "V023-S9-P9.1")
        self.assertEqual(audit["token_surface"]["color_scheme"], "light")
        self.assertEqual(set(audit["component_rules"]), {"cards", "tables", "buttons", "chart_empty_states", "mobile"})
        self.assertFalse(audit["phase_9_2_motion_feedback_started"])
        self.assertFalse(audit["phase_9_3_haptics_settings_started"])
        self.assertEqual(scan["violations"], [])

        doc_text = doc_path.read_text(encoding="utf-8")
        self.assertIn("Stage 9 Phase 9.1", doc_text)
        self.assertIn("亮色 token", doc_text)
        self.assertIn("卡片/表格/按钮规范", doc_text)
        self.assertIn("图表空状态规范", doc_text)
        self.assertIn("移动端适配", doc_text)
        self.assertIn("Phase 9.2 未执行", doc_text)
        self.assertIn("Phase 9.3 未执行", doc_text)

        terminal_log = terminal_log_path.read_text(encoding="utf-8")
        self.assertIn("PFI/tests/test_v023_stage9_visual_feedback.py -q", terminal_log)

    def test_phase91_files_do_not_contain_blocked_placeholder_terms(self) -> None:
        terms = ["mo" + "ck", "sam" + "ple", "synthe" + "tic", "fix" + "ture", "de" + "mo", "fa" + "ke"]
        paths = [
            ROOT / "web" / "styles.css",
            ROOT / "tests" / "test_v023_stage9_visual_feedback.py",
            ROOT / "docs" / "pfi_v023" / "STAGE9_VISUAL_FEEDBACK.md",
        ]
        for path in paths:
            if not path.exists():
                continue
            text = path.read_text(encoding="utf-8").lower().replace("sample_size", "")
            for term in terms:
                self.assertIsNone(re.search(term, text), f"{path} contains blocked placeholder term {term}")


if __name__ == "__main__":
    unittest.main()
