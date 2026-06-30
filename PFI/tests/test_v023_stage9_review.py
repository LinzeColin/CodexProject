from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TestV023Stage9WholeStageReview(unittest.TestCase):
    def test_stage9_review_evidence_covers_all_three_phases_before_stage10(self) -> None:
        review_dir = ROOT / "reports" / "pfi_v023" / "stage_9" / "stage9_review"
        evidence_path = review_dir / "evidence.json"
        audit_path = review_dir / "review_audit.json"
        scan_path = review_dir / "no_source_term_scan.json"
        changed_files_path = review_dir / "changed_files.txt"
        terminal_log_path = review_dir / "terminal.log"

        for path in (evidence_path, audit_path, scan_path, changed_files_path, terminal_log_path):
            self.assertTrue(path.exists(), str(path))

        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
        scan = json.loads(scan_path.read_text(encoding="utf-8"))
        changed_files = [line.strip() for line in changed_files_path.read_text(encoding="utf-8").splitlines() if line.strip()]

        self.assertEqual(evidence["schema"], "PFIV023Stage9WholeStageReviewEvidenceV1")
        self.assertEqual(evidence["version"], "v0.2.3")
        self.assertEqual(evidence["stage"], "Stage 9")
        self.assertEqual(evidence["review_id"], "V023-S9-REVIEW")
        self.assertEqual(evidence["status"], "candidate_pass")
        self.assertTrue(evidence["stage9_whole_stage_review"])
        self.assertTrue(evidence["findings_fixed"])
        self.assertFalse(evidence["stage10_started"])
        self.assertFalse(evidence["github_main_uploaded_before_review"])
        self.assertEqual(evidence["changed_files"], changed_files)

        self.assertEqual(
            set(evidence["phase_evidence"]),
            {"phase_9_1", "phase_9_2", "phase_9_3"},
        )
        for rel_path in evidence["phase_evidence"].values():
            phase = json.loads((ROOT / rel_path.removeprefix("PFI/")).read_text(encoding="utf-8"))
            self.assertEqual(phase["status"], "candidate_pass")
            self.assertTrue(phase["current_phase_only"])
            self.assertTrue(phase["max_one_phase_per_run"])
            self.assertFalse(phase["stage_contract"]["stage_9_whole_review_done"])
            self.assertFalse(phase["stage_contract"]["github_main_upload_done"])

        self.assertEqual(audit["schema"], "PFIV023Stage9WholeStageReviewAuditV1")
        self.assertEqual(audit["review_id"], "V023-S9-REVIEW")
        self.assertEqual(
            audit["phase_status"],
            {
                "phase_9_1": "candidate_pass",
                "phase_9_2": "candidate_pass",
                "phase_9_3": "candidate_pass",
            },
        )
        self.assertEqual(audit["review_findings"], [])
        self.assertFalse(audit["stage10_started"])
        self.assertFalse(audit["github_main_uploaded_before_review"])
        self.assertEqual(scan["violations"], [])

    def test_stage9_review_acceptance_and_stop_conditions_are_explicit(self) -> None:
        evidence = json.loads(
            (ROOT / "reports" / "pfi_v023" / "stage_9" / "stage9_review" / "evidence.json").read_text(
                encoding="utf-8"
            )
        )
        audit = json.loads(
            (ROOT / "reports" / "pfi_v023" / "stage_9" / "stage9_review" / "review_audit.json").read_text(
                encoding="utf-8"
            )
        )

        for key in (
            "light_design_system_default",
            "design_tokens_present",
            "motion_feedback_for_transition_loading_success_error_blocked",
            "haptics_can_disable_and_degrade",
            "settings_page_manages_feedback_preferences",
            "business_pages_without_feedback_console",
            "desktop_mobile_screenshots_exist",
            "no_forbidden_financial_data_terms",
        ):
            self.assertTrue(evidence["acceptance_checks"][key], key)
            self.assertTrue(audit["acceptance_checks"][key], key)

        for key in (
            "not_dark_ai_console",
            "feedback_settings_not_polluting_home",
            "motion_has_business_state_meaning",
            "success_error_blocked_feedback_are_distinct",
        ):
            self.assertTrue(evidence["stop_condition_checks"][key], key)
            self.assertTrue(audit["stop_condition_checks"][key], key)

    def test_stage9_doc_records_whole_stage_review_without_stage10_or_upload_claim(self) -> None:
        doc = (ROOT / "docs" / "pfi_v023" / "STAGE9_VISUAL_FEEDBACK.md").read_text(encoding="utf-8")

        self.assertIn("Stage 9 Whole-Stage Review", doc)
        self.assertIn("V023-S9-REVIEW", doc)
        self.assertIn("Phase 9.1", doc)
        self.assertIn("Phase 9.2", doc)
        self.assertIn("Phase 9.3", doc)
        self.assertIn("GitHub main upload proof", doc)
        self.assertIn("not embedded in commit", doc)
        self.assertIn("Stage 10 未执行", doc)

    def test_stage9_review_files_do_not_contain_blocked_placeholder_terms(self) -> None:
        terms = ["mo" + "ck", "sam" + "ple", "synthe" + "tic", "fix" + "ture", "de" + "mo", "fa" + "ke"]
        paths = [
            ROOT / "web" / "styles.css",
            ROOT / "web" / "app" / "feedback.js",
            ROOT / "web" / "app" / "pages" / "settings.js",
            ROOT / "tests" / "test_v023_stage9_visual_feedback.py",
            ROOT / "tests" / "test_v023_stage9_review.py",
            ROOT / "docs" / "pfi_v023" / "STAGE9_VISUAL_FEEDBACK.md",
        ]
        for path in paths:
            text = path.read_text(encoding="utf-8").lower().replace("sample_size", "")
            for term in terms:
                self.assertIsNone(re.search(term, text), f"{path} contains blocked placeholder term {term}")


if __name__ == "__main__":
    unittest.main()
