from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent


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


def node_json(script: str, *args: str) -> dict[str, object]:
    node = node_executable()
    if not node:
        raise AssertionError("Node runtime is required for Stage 9 visual feedback contract tests")
    completed = subprocess.run(
        [node, "-e", script, *args],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    return json.loads(completed.stdout)


class TestV023Stage9VisualFeedback(unittest.TestCase):
    def setUp(self) -> None:
        self.html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        self.styles = (ROOT / "web" / "styles.css").read_text(encoding="utf-8")
        self.tokens = (ROOT / "web" / "styles" / "tokens.css").read_text(encoding="utf-8")
        feedback_path = ROOT / "web" / "app" / "feedback.js"
        self.feedback_js = feedback_path.read_text(encoding="utf-8") if feedback_path.exists() else ""
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

        self.assertNotIn("navigator.vibrate", self.styles)

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

        terminal_log = terminal_log_path.read_text(encoding="utf-8")
        self.assertIn("PFI/tests/test_v023_stage9_visual_feedback.py -q", terminal_log)

    def test_phase92_contract_is_limited_to_motion_feedback(self) -> None:
        script = """
const feedback = require('./PFI/web/app/feedback.js');
console.log(JSON.stringify(feedback.buildStage9Phase92Contract()));
"""
        contract = node_json(script)

        self.assertEqual(contract["version"], "v0.2.3")
        self.assertEqual(contract["stage"], "Stage 9")
        self.assertEqual(contract["phase_id"], "V023-S9-P9.2")
        self.assertEqual(contract["phase_name"], "动效反馈")
        self.assertTrue(contract["current_phase_only"])
        self.assertTrue(contract["max_one_phase_per_run"])
        self.assertEqual(contract["task_ids"], ["T9.2.1", "T9.2.2", "T9.2.3", "T9.2.4"])
        self.assertIn("PFI/web/styles.css", contract["allowed_files"])
        self.assertIn("PFI/web/app/feedback.js", contract["allowed_files"])
        self.assertNotIn("PFI/web/index.html", contract["changed_in_this_phase"])
        self.assertNotIn("PFI/web/app/shell.js", contract["changed_in_this_phase"])
        self.assertIn("Phase 9.3 触感与设置隔离", contract["explicitly_not_done"])
        self.assertIn("Stage 9 whole-stage review", contract["explicitly_not_done"])
        self.assertIn("GitHub main upload for intermediate phase", contract["explicitly_not_done"])

    def test_phase92_feedback_model_covers_transitions_states_report_progress_and_reduced_motion(self) -> None:
        script = """
const feedback = require('./PFI/web/app/feedback.js');
console.log(JSON.stringify(feedback.buildStage9Phase92FeedbackModel()));
"""
        model = node_json(script)

        self.assertEqual(model["schema"], "PFIV023Stage9Phase92FeedbackModelV1")
        self.assertEqual(model["phase_id"], "V023-S9-P9.2")
        self.assertLessEqual(model["page_transition"]["duration_ms"], 220)
        self.assertEqual(model["page_transition"]["route_state_attribute"], "data-route-transition")
        states = {item["state"]: item for item in model["feedback_states"]}
        self.assertEqual(set(states), {"loading", "success", "error", "blocked"})
        for state, item in states.items():
            self.assertRegex(item["label_zh"], r"[\u4e00-\u9fff]")
            self.assertRegex(item["action_zh"], r"[\u4e00-\u9fff]")
            self.assertIn("aria_live", item)
        self.assertEqual(model["report_generation_progress"]["schema"], "PFIV023ReportProgressV1")
        self.assertGreaterEqual(len(model["report_generation_progress"]["steps"]), 4)
        self.assertIn("检查真实数据状态", json.dumps(model["report_generation_progress"], ensure_ascii=False))
        self.assertTrue(model["reduced_motion"]["prefers_reduced_motion_supported"])
        self.assertIn("body.reduce-motion", model["reduced_motion"]["selectors"])
        self.assertFalse(model["phase_9_3_haptics_settings_started"])
        self.assertNotIn("navigator.vibrate", json.dumps(model))

    def test_phase92_css_defines_motion_feedback_components(self) -> None:
        for required in (
            "PFI v0.2.3 Stage 9 Phase 9.2 motion feedback",
            'body[data-pfi-version="v0.2.3"] .workspace[data-route-transition="enter"]',
            'body[data-pfi-version="v0.2.3"] .action-feedback[data-feedback-state="loading"]',
            'body[data-pfi-version="v0.2.3"] .action-feedback[data-feedback-state="success"]',
            'body[data-pfi-version="v0.2.3"] .action-feedback[data-feedback-state="error"]',
            'body[data-pfi-version="v0.2.3"] .action-feedback[data-feedback-state="blocked"]',
            'body[data-pfi-version="v0.2.3"] .report-progress',
            'body[data-pfi-version="v0.2.3"] .report-progress-step',
            "@media (prefers-reduced-motion: reduce)",
            "body.reduce-motion",
        ):
            self.assertIn(required, self.styles)
        for required in (
            "pfi-v023-page-enter",
            "pfi-v023-skeleton-sheen",
            "transition-duration: 1ms !important",
            "animation-duration: 1ms !important",
        ):
            self.assertIn(required, self.styles)

    def test_phase92_doc_and_evidence_exist_before_candidate_pass(self) -> None:
        phase_dir = ROOT / "reports" / "pfi_v023" / "stage_9" / "phase_9_2"
        evidence_path = phase_dir / "evidence.json"
        feedback_audit_path = phase_dir / "feedback_audit.json"
        scan_path = phase_dir / "no_source_term_scan.json"
        changed_files_path = phase_dir / "changed_files.txt"
        terminal_log_path = phase_dir / "terminal.log"
        doc_path = ROOT / "docs" / "pfi_v023" / "STAGE9_VISUAL_FEEDBACK.md"

        for path in (evidence_path, feedback_audit_path, scan_path, changed_files_path, terminal_log_path, doc_path):
            self.assertTrue(path.exists(), str(path))

        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        audit = json.loads(feedback_audit_path.read_text(encoding="utf-8"))
        scan = json.loads(scan_path.read_text(encoding="utf-8"))
        changed_files = [line.strip() for line in changed_files_path.read_text(encoding="utf-8").splitlines() if line.strip()]

        self.assertEqual(evidence["version"], "v0.2.3")
        self.assertEqual(evidence["stage"], "Stage 9")
        self.assertEqual(evidence["phase_id"], "V023-S9-P9.2")
        self.assertEqual(evidence["phase_name"], "动效反馈")
        self.assertEqual(evidence["status"], "candidate_pass")
        self.assertTrue(evidence["current_phase_only"])
        self.assertTrue(evidence["max_one_phase_per_run"])
        self.assertTrue(evidence["stage_contract"]["phase_9_1_design_system_done"])
        self.assertTrue(evidence["stage_contract"]["phase_9_2_motion_feedback_done"])
        self.assertFalse(evidence["stage_contract"]["phase_9_3_haptics_settings_done"])
        self.assertFalse(evidence["stage_contract"]["stage_9_whole_review_done"])
        self.assertFalse(evidence["stage_contract"]["github_main_upload_done"])
        self.assertEqual(evidence["changed_files"], changed_files)
        for key in (
            "page_transition",
            "feedback_state_components",
            "report_generation_progress",
            "reduced_motion",
            "no_forbidden_financial_data_terms",
        ):
            self.assertTrue(evidence["acceptance_checks"][key], key)

        self.assertEqual(audit["schema"], "PFIV023Stage9Phase92FeedbackAuditV1")
        self.assertEqual(audit["phase_id"], "V023-S9-P9.2")
        self.assertEqual(set(audit["feedback_states"]), {"loading", "success", "error", "blocked"})
        self.assertEqual(audit["page_transition"]["duration_ms"], 180)
        self.assertEqual(audit["report_generation_progress"]["step_count"], 4)
        self.assertTrue(audit["reduced_motion"]["supported"])
        self.assertFalse(audit["phase_9_3_haptics_settings_started"])
        self.assertEqual(scan["violations"], [])

        doc_text = doc_path.read_text(encoding="utf-8")
        self.assertIn("Stage 9 Phase 9.2", doc_text)
        self.assertIn("页面转场", doc_text)
        self.assertIn("loading/success/error/blocked", doc_text)
        self.assertIn("报告生成进度", doc_text)
        self.assertIn("减少动画模式", doc_text)
        self.assertIn("Phase 9.3 未执行", doc_text)

        terminal_log = terminal_log_path.read_text(encoding="utf-8")
        self.assertIn("PFI/tests/test_v023_stage9_visual_feedback.py -q", terminal_log)

    def test_phase91_files_do_not_contain_blocked_placeholder_terms(self) -> None:
        terms = ["mo" + "ck", "sam" + "ple", "synthe" + "tic", "fix" + "ture", "de" + "mo", "fa" + "ke"]
        paths = [
            ROOT / "web" / "styles.css",
            ROOT / "web" / "app" / "feedback.js",
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
