from __future__ import annotations

import unittest

from KMFA.tools import v015_s07_p3_release_gate as kernel


class S07P3ReleaseGateTests(unittest.TestCase):
    def test_three_human_statuses_have_no_technical_grade_abbreviations(self) -> None:
        cases = kernel.synthetic_acceptance_cases()["status_cases"]
        self.assertEqual([row["display_label_zh"] for row in cases], list(kernel.HUMAN_STATUS_LABELS))
        self.assertEqual(sum(row["ui_technical_abbreviation_count"] for row in cases), 0)
        for row in cases:
            text = str(row["ui_payload"])
            for token in kernel.TECHNICAL_ABBREVIATIONS:
                self.assertNotIn(token, text)

    def test_critical_difference_conflict_or_failed_recheck_blocks_release(self) -> None:
        inputs = (
            kernel.ReportGateInput(1, 0, 0, 0, 0, True, True, True),
            kernel.ReportGateInput(0, 1, 0, 0, 0, True, True, True),
            kernel.ReportGateInput(0, 0, 1, 0, 0, True, True, True),
            kernel.ReportGateInput(0, 0, 0, 0, 0, False, True, True),
            kernel.ReportGateInput(0, 0, 0, 0, 0, True, False, True),
            kernel.ReportGateInput(0, 0, 0, 0, 0, True, True, False),
        )
        for value in inputs:
            result = kernel.determine_report_status(value)
            self.assertEqual(result["display_label_zh"], kernel.UNAVAILABLE_LABEL)
            self.assertFalse(result["internal_use_allowed"])
            self.assertFalse(result["formal_report_release_allowed"])
            self.assertGreater(result["blocking_reason_count"], 0)

    def test_noncritical_or_undetermined_items_require_confirmation(self) -> None:
        result = kernel.determine_report_status(
            kernel.ReportGateInput(0, 0, 0, 1, 2, True, True, True)
        )
        self.assertEqual(result["display_label_zh"], kernel.CONFIRMATION_REQUIRED_LABEL)
        self.assertFalse(result["formal_report_release_allowed"])

    def test_clear_recalculated_reviewed_and_regressed_case_is_internal_use(self) -> None:
        result = kernel.determine_report_status(
            kernel.ReportGateInput(0, 0, 0, 0, 0, True, True, True)
        )
        self.assertEqual(result["display_label_zh"], kernel.INTERNAL_USE_LABEL)
        self.assertTrue(result["internal_use_allowed"])
        self.assertTrue(result["release_candidate_allowed"])

    def test_all_four_closure_paths_require_recalculation_and_review(self) -> None:
        cases = kernel.synthetic_acceptance_cases()["closure_cases"]
        self.assertEqual({row["closure_kind"] for row in cases}, set(kernel.CLOSURE_KINDS))
        self.assertEqual(len(cases), 4)
        for row in cases:
            self.assertEqual(row["status"], "CLOSED")
            self.assertTrue(row["recalculation_performed"])
            self.assertTrue(row["review_performed"])
            self.assertEqual(row["post_recalculation_difference_count"], 0)
            self.assertFalse(row["status_only_closure"])

    def test_status_only_or_missing_recalculation_cannot_close_difference(self) -> None:
        cases = kernel.synthetic_acceptance_cases()
        self.assertTrue(cases["status_only_closure_rejected"])
        self.assertTrue(cases["missing_recalculation_rejected"])
        with self.assertRaisesRegex(kernel.ReleaseGateError, "重算后"):
            closure = kernel._closure_fixture(kernel.RULE_CORRECTION)
            closure["post_recalculation_difference_count"] = 1
            kernel.close_difference({"difference_id": "D-1", "status": "OPEN"}, closure)

    def test_every_previously_passed_project_must_rerun(self) -> None:
        with self.assertRaisesRegex(kernel.ReleaseGateError, "全部历史"):
            kernel.evaluate_regression_gate(
                change_ref="CHANGE-1",
                previously_passed_project_refs=("P-1", "P-2", "P-3"),
                rerun_results={"P-1": True, "P-2": True},
            )

    def test_any_regression_failure_blocks_merge(self) -> None:
        result = kernel.evaluate_regression_gate(
            change_ref="CHANGE-2",
            previously_passed_project_refs=("P-1", "P-2", "P-3"),
            rerun_results={"P-1": True, "P-2": False, "P-3": True},
        )
        self.assertEqual(result["regression_pass_rate_bps"], 6666)
        self.assertEqual(result["regression_fail_count"], 1)
        self.assertFalse(result["historical_projects_100_percent_passed"])
        self.assertFalse(result["merge_allowed"])

    def test_private_historical_projects_rerun_at_100_percent(self) -> None:
        result = kernel.validate_private_regression_gate()
        self.assertEqual(result["private_historical_project_count"], 8)
        self.assertEqual(result["private_selected_for_rerun_count"], 8)
        self.assertEqual(result["private_regression_pass_count"], 8)
        self.assertEqual(result["private_regression_fail_count"], 0)
        self.assertEqual(result["private_regression_pass_rate_bps"], 10000)
        self.assertTrue(result["private_historical_projects_100_percent_passed"])
        self.assertTrue(result["private_merge_allowed"])
        self.assertEqual(result["private_open_unconfirmed_item_count"], 128)

    def test_current_private_status_stays_unavailable_and_does_not_publish(self) -> None:
        result = kernel.current_private_release_status()
        self.assertEqual(result["current_report_display_label_zh"], kernel.UNAVAILABLE_LABEL)
        self.assertFalse(result["current_formal_report_release_allowed"])
        self.assertFalse(result["current_internal_use_allowed"])
        self.assertEqual(result["current_private_open_unconfirmed_item_count"], 128)
        self.assertEqual(result["current_private_conflict_candidate_count"], 6)
        self.assertEqual(result["current_private_conflict_auto_selected_count"], 0)

    def test_public_projection_keeps_later_work_closed(self) -> None:
        result = kernel.public_projection()
        self.assertEqual(result["status_label_count"], 3)
        self.assertEqual(result["ui_technical_abbreviation_count"], 0)
        self.assertEqual(result["closure_kind_count"], 4)
        self.assertEqual(result["closure_success_count"], 4)
        self.assertEqual(result["private_regression_pass_rate_bps"], 10000)
        self.assertFalse(result["synthetic_regression_failure_merge_allowed"])
        self.assertEqual(result["stage_execution_percentage"], 100)
        self.assertFalse(result["s07_stage_review_started"])
        self.assertFalse(result["s08_p1_entry_allowed"])
        self.assertFalse(result["formal_report_generated"])
        self.assertFalse(result["github_upload_performed"])
        self.assertFalse(result["app_reinstall_performed"])


if __name__ == "__main__":
    unittest.main()
