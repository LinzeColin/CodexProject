import unittest

from KMFA.tools.check_v014_s11_p1_home_navigation import (
    validate_v014_s11_p1_home_navigation,
)
from KMFA.tools.home_navigation_runtime import REQUIRED_NAVIGATION_LABELS
from KMFA.tools.v014_s11_p1_home_navigation import generate


class V014S11P1HomeNavigationTests(unittest.TestCase):
    def test_locks_home_navigation_with_v14_human_flow_baseline(self) -> None:
        manifest = generate()
        validated = validate_v014_s11_p1_home_navigation()

        self.assertEqual(manifest, validated)
        self.assertEqual(validated["project_id"], "KMFA")
        self.assertEqual(validated["version"], "0.1.4")
        self.assertEqual(validated["stage_id"], "S11")
        self.assertEqual(validated["phase_id"], "S11-P1")
        self.assertEqual(validated["phase_scope"], "v014_s11_p1_home_navigation_only")
        self.assertEqual(validated["task_id"], "KMFA-V014-S11-P1-HOME-NAVIGATION-20260704")
        self.assertEqual(validated["completed_task_ids"], ["S11P1T01", "S11P1T02", "S11P1T03"])
        self.assertEqual(validated["acceptance_ids"], ["ACC-V014-S11-P1-HOME-NAVIGATION"])

        progress = validated["stage11_phase_progress"]
        self.assertEqual(progress["completed_phase_count"], 1)
        self.assertEqual(progress["total_phase_count"], 3)
        self.assertEqual(progress["derived_percent_label"], "33.33%")
        self.assertTrue(progress["s11_p1_performed"])
        self.assertFalse(progress["s11_p2_performed"])
        self.assertFalse(progress["s11_p3_performed"])
        self.assertFalse(progress["stage11_review_performed"])

        summary = validated["home_navigation_summary"]
        self.assertEqual(summary["navigation_module_count"], 8)
        self.assertEqual(summary["required_navigation_labels"], list(REQUIRED_NAVIGATION_LABELS))
        self.assertEqual(summary["html_export_count"], 1)
        self.assertEqual(summary["nav_button_count"], 8)
        self.assertEqual(summary["module_action_button_count"], 8)
        self.assertEqual(summary["visible_feedback_panel_count"], 1)
        self.assertTrue(summary["km_brand_mark_present"])
        self.assertFalse(summary["single_k_brand_mark_present"])
        self.assertTrue(summary["blue_business_style"])
        self.assertTrue(summary["all_chinese_visible_copy"])
        self.assertEqual(summary["formal_report_count"], 0)
        self.assertEqual(summary["business_decision_basis_count"], 0)

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
        self.assertTrue(baseline["implementation_reflects_clickable_navigation"])
        self.assertTrue(baseline["implementation_reflects_visible_feedback"])
        self.assertTrue(baseline["implementation_reflects_report_center_entry"])

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
