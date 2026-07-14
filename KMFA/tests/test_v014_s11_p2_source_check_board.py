import unittest

from KMFA.tools.check_v014_s11_p2_source_check_board import (
    validate_v014_s11_p2_source_check_board,
)
from KMFA.tools.source_check_board_runtime import ALLOWED_BOARD_STATUSES, REQUIRED_BOARD_COLUMNS
from KMFA.tools.v014_s11_p2_source_check_board import generate


class V014S11P2SourceCheckBoardTests(unittest.TestCase):
    def test_locks_source_check_board_with_v14_human_flow_baseline(self) -> None:
        manifest = generate()
        validated = validate_v014_s11_p2_source_check_board()

        self.assertEqual(manifest, validated)
        self.assertEqual(validated["project_id"], "KMFA")
        self.assertEqual(validated["version"], "0.1.4")
        self.assertEqual(validated["stage_id"], "S11")
        self.assertEqual(validated["phase_id"], "S11-P2")
        self.assertEqual(validated["phase_scope"], "v014_s11_p2_source_check_board_only")
        self.assertEqual(validated["task_id"], "KMFA-V014-S11-P2-SOURCE-CHECK-BOARD-20260704")
        self.assertEqual(validated["completed_task_ids"], ["S11P2T01", "S11P2T02", "S11P2T03"])
        self.assertEqual(validated["acceptance_ids"], ["ACC-V014-S11-P2-SOURCE-CHECK-BOARD"])

        progress = validated["stage11_phase_progress"]
        self.assertEqual(progress["completed_phase_count"], 2)
        self.assertEqual(progress["total_phase_count"], 3)
        self.assertEqual(progress["derived_percent_label"], "66.67%")
        self.assertTrue(progress["s11_p1_performed"])
        self.assertTrue(progress["s11_p2_performed"])
        self.assertFalse(progress["s11_p3_performed"])
        self.assertFalse(progress["stage11_review_performed"])

        summary = validated["source_check_board_summary"]
        self.assertEqual(summary["matrix_row_count"], 13)
        self.assertEqual(summary["required_columns"], list(REQUIRED_BOARD_COLUMNS))
        self.assertEqual(summary["required_column_count"], 11)
        self.assertEqual(summary["allowed_statuses"], list(ALLOWED_BOARD_STATUSES))
        self.assertEqual(summary["allowed_status_count"], 5)
        self.assertEqual(set(summary["status_counts"]), set(ALLOWED_BOARD_STATUSES))
        self.assertEqual(summary["html_export_count"], 1)
        self.assertTrue(summary["status_click_detail_enabled"])
        self.assertTrue(summary["blue_gray_surface_dominant"])
        self.assertTrue(summary["status_badges_only"])
        self.assertEqual(summary["large_yellow_surface_count"], 0)
        self.assertEqual(summary["formal_report_count"], 0)
        self.assertEqual(summary["business_decision_basis_count"], 0)
        self.assertEqual(summary["raw_business_value_count"], 0)
        self.assertEqual(summary["private_file_reference_count"], 0)

        baseline = validated["v14_html_uiux_baseline"]
        self.assertTrue(baseline["taskpack_html_requirement_read"])
        self.assertTrue(baseline["human_flow_entry_exists"])
        self.assertTrue(baseline["human_flow_audit_script_exists"])
        self.assertTrue(baseline["human_flow_audit_report_exists"])
        self.assertEqual(baseline["audit_file_count"], 6)
        self.assertEqual(baseline["audit_control_row_count"], 54)
        self.assertEqual(baseline["audit_pass_count"], 54)
        self.assertEqual(baseline["audit_warn_count"], 0)
        self.assertEqual(baseline["audit_fail_count"], 0)
        self.assertTrue(baseline["implementation_reflects_search_feedback"])
        self.assertTrue(baseline["implementation_reflects_status_change_feedback"])
        self.assertTrue(baseline["implementation_reflects_status_detail_preview"])

        upload = validated["github_upload"]
        self.assertFalse(upload["github_upload_performed"])
        self.assertFalse(upload["github_upload_ready_next_gate"])
        self.assertTrue(upload["github_upload_deferred_until_v014_stage1_18_complete"])

        raw_boundary = validated["raw_data_boundary"]
        self.assertFalse(raw_boundary["raw_inbox_read_by_this_phase"])
        self.assertFalse(raw_boundary["raw_inbox_listed_by_this_phase"])
        self.assertFalse(raw_boundary["raw_inbox_mutated_by_this_phase"])

        self.assertFalse(validated["quality_gate"]["formal_report_allowed"])
        self.assertFalse(validated["quality_gate"]["business_decision_basis_allowed"])
        self.assertFalse(validated["quality_gate"]["business_execution_allowed"])
        self.assertFalse(validated["quality_gate"]["stage11_review_allowed"])
        self.assertFalse(validated["quality_gate"]["github_upload_allowed"])


if __name__ == "__main__":
    unittest.main()
