import unittest

from KMFA.tools.check_v014_s13_p1_financial_operating_report import (
    validate_v014_s13_p1_financial_operating_report,
)
from KMFA.tools.v014_s13_p1_financial_operating_report import generate


class V014S13P1FinancialOperatingReportTests(unittest.TestCase):
    def test_locks_financial_operating_report_without_later_scope_or_upload(self) -> None:
        manifest = generate()
        validated = validate_v014_s13_p1_financial_operating_report()

        self.assertEqual(manifest, validated)
        self.assertEqual(validated["project_id"], "KMFA")
        self.assertEqual(validated["version"], "0.1.4")
        self.assertEqual(validated["stage_id"], "S13")
        self.assertEqual(validated["phase_id"], "S13-P1")
        self.assertEqual(validated["phase_scope"], "v014_s13_p1_financial_operating_report_only")
        self.assertEqual(validated["task_id"], "KMFA-V014-S13-P1-FINANCIAL-OPERATING-REPORT-20260705")
        self.assertEqual(validated["completed_task_ids"], ["S13P1T01", "S13P1T02", "S13P1T03"])
        self.assertEqual(validated["acceptance_ids"], ["ACC-V014-S13-P1-FINANCIAL-OPERATING-REPORT"])

        progress = validated["stage13_phase_progress"]
        self.assertEqual(progress["completed_phase_count"], 1)
        self.assertEqual(progress["total_phase_count"], 3)
        self.assertEqual(progress["derived_percent_label"], "33.33%")
        self.assertTrue(progress["s13_p1_performed"])
        self.assertFalse(progress["s13_p2_performed"])
        self.assertFalse(progress["s13_p3_performed"])
        self.assertFalse(progress["stage13_review_performed"])

        summary = validated["financial_operating_summary"]
        self.assertEqual(summary["source_lane_count"], 4)
        self.assertEqual(summary["source_count"], 8)
        self.assertEqual(summary["field_mapping_count"], 39)
        self.assertEqual(summary["draft_report_count"], 2)
        self.assertEqual(summary["html_draft_count"], 2)
        self.assertEqual(summary["pending_reconciliation_count"], 12)
        self.assertEqual(summary["report_grade_visible"], "D")
        self.assertEqual(summary["formal_report_count"], 0)
        self.assertEqual(summary["business_decision_basis_count"], 0)

        baseline = validated["v14_html_uiux_baseline"]
        self.assertTrue(baseline["taskpack_html_requirement_read"])
        self.assertEqual(baseline["audit_file_count"], 6)
        self.assertEqual(baseline["audit_control_row_count"], 54)
        self.assertEqual(baseline["audit_pass_count"], 54)
        self.assertEqual(baseline["audit_warn_count"], 0)
        self.assertEqual(baseline["audit_fail_count"], 0)
        self.assertTrue(baseline["implementation_reflects_weekly_monthly_drafts"])
        self.assertTrue(baseline["implementation_reflects_data_status_and_limits"])

        upload = validated["github_upload"]
        self.assertFalse(upload["github_upload_performed"])
        self.assertFalse(upload["github_upload_ready_next_gate"])
        self.assertTrue(upload["github_upload_deferred_until_v014_stage1_18_complete"])

        raw_boundary = validated["raw_data_boundary"]
        self.assertFalse(raw_boundary["raw_inbox_read_by_this_phase"])
        self.assertFalse(raw_boundary["raw_inbox_listed_by_this_phase"])
        self.assertFalse(raw_boundary["raw_inbox_mutated_by_this_phase"])

        quality = validated["quality_gate"]
        self.assertTrue(quality["draft_report_allowed"])
        self.assertFalse(quality["formal_report_allowed"])
        self.assertFalse(quality["business_decision_basis_allowed"])
        self.assertFalse(quality["business_execution_allowed"])
        self.assertFalse(quality["s13_p2_allowed"])
        self.assertFalse(quality["s13_p3_allowed"])
        self.assertFalse(quality["stage13_review_allowed"])
        self.assertFalse(quality["github_upload_allowed"])


if __name__ == "__main__":
    unittest.main()
