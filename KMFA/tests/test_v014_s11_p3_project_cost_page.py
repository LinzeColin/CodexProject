import unittest

from KMFA.tools.check_v014_s11_p3_project_cost_page import validate_v014_s11_p3_project_cost_page
from KMFA.tools.project_cost_page_runtime import REQUIRED_COST_CATEGORIES, REQUIRED_PROJECT_TABLE_COLUMNS
from KMFA.tools.v014_s11_p3_project_cost_page import generate


class V014S11P3ProjectCostPageTests(unittest.TestCase):
    def test_locks_project_cost_page_with_v14_human_flow_baseline(self) -> None:
        manifest = generate()
        validated = validate_v014_s11_p3_project_cost_page()

        self.assertEqual(manifest, validated)
        self.assertEqual(validated["project_id"], "KMFA")
        self.assertEqual(validated["version"], "0.1.4")
        self.assertEqual(validated["stage_id"], "S11")
        self.assertEqual(validated["phase_id"], "S11-P3")
        self.assertEqual(validated["phase_scope"], "v014_s11_p3_project_cost_page_only")
        self.assertEqual(validated["task_id"], "KMFA-V014-S11-P3-PROJECT-COST-PAGE-20260704")
        self.assertEqual(validated["completed_task_ids"], ["S11P3T01", "S11P3T02", "S11P3T03"])
        self.assertEqual(validated["acceptance_ids"], ["ACC-V014-S11-P3-PROJECT-COST-PAGE"])

        progress = validated["stage11_phase_progress"]
        self.assertEqual(progress["completed_phase_count"], 3)
        self.assertEqual(progress["total_phase_count"], 3)
        self.assertEqual(progress["derived_percent_label"], "100.00%")
        self.assertTrue(progress["s11_p1_performed"])
        self.assertTrue(progress["s11_p2_performed"])
        self.assertTrue(progress["s11_p3_performed"])
        self.assertFalse(progress["stage11_review_performed"])

        summary = validated["project_cost_page_summary"]
        self.assertEqual(summary["project_row_count"], 4)
        self.assertEqual(summary["project_list_columns"], list(REQUIRED_PROJECT_TABLE_COLUMNS))
        self.assertEqual(summary["project_list_column_count"], 7)
        self.assertEqual(summary["cost_categories"], list(REQUIRED_COST_CATEGORIES))
        self.assertEqual(summary["cost_category_count"], 9)
        self.assertEqual(summary["margin_record_count"], 4)
        self.assertEqual(summary["pending_reconciliation_count"], 12)
        self.assertEqual(summary["pending_action_total"], 12)
        self.assertEqual(summary["html_export_count"], 1)
        self.assertTrue(summary["project_detail_click_enabled"])
        self.assertTrue(summary["source_evidence_panel_enabled"])
        self.assertTrue(summary["pending_action_panel_enabled"])
        self.assertTrue(summary["report_preview_direct_view_allowed"])
        self.assertEqual(summary["report_grade_visible"], "D")
        self.assertFalse(summary["quality_grade_bypass_allowed"])
        self.assertEqual(summary["formal_report_count"], 0)
        self.assertEqual(summary["business_decision_basis_count"], 0)
        self.assertEqual(summary["raw_business_value_count"], 0)
        self.assertEqual(summary["private_file_reference_count"], 0)

        baseline = validated["v14_html_uiux_baseline"]
        self.assertTrue(baseline["taskpack_html_requirement_read"])
        self.assertEqual(baseline["audit_file_count"], 6)
        self.assertEqual(baseline["audit_control_row_count"], 54)
        self.assertEqual(baseline["audit_pass_count"], 54)
        self.assertEqual(baseline["audit_warn_count"], 0)
        self.assertEqual(baseline["audit_fail_count"], 0)
        self.assertTrue(baseline["implementation_reflects_project_detail_click"])
        self.assertTrue(baseline["implementation_reflects_report_section_switch"])
        self.assertTrue(baseline["implementation_reflects_appendix_export_feedback"])
        self.assertTrue(baseline["implementation_reflects_print_save_feedback"])
        self.assertTrue(baseline["implementation_reflects_quality_gate_block"])

        upload = validated["github_upload"]
        self.assertFalse(upload["github_upload_performed"])
        self.assertFalse(upload["github_upload_ready_next_gate"])
        self.assertTrue(upload["github_upload_deferred_until_v014_stage1_18_complete"])

        raw_boundary = validated["raw_data_boundary"]
        self.assertFalse(raw_boundary["raw_inbox_read_by_this_phase"])
        self.assertFalse(raw_boundary["raw_inbox_listed_by_this_phase"])
        self.assertFalse(raw_boundary["raw_inbox_mutated_by_this_phase"])

        self.assertFalse(validated["quality_gate"]["formal_report_allowed"])
        self.assertFalse(validated["quality_gate"]["complete_trusted_report_display_allowed"])
        self.assertFalse(validated["quality_gate"]["business_decision_basis_allowed"])
        self.assertFalse(validated["quality_gate"]["stage11_review_allowed"])
        self.assertFalse(validated["quality_gate"]["github_upload_allowed"])


if __name__ == "__main__":
    unittest.main()
