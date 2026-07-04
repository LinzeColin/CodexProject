import unittest

from KMFA.tools.check_v014_s10_p3_report_export import (
    validate_v014_s10_p3_report_export,
)
from KMFA.tools.v014_s10_p3_report_export import generate


class V014S10P3ReportExportTests(unittest.TestCase):
    def test_locks_public_safe_report_exports_without_review_upload_or_raw_access(self) -> None:
        manifest = generate()
        validated = validate_v014_s10_p3_report_export()

        self.assertEqual(manifest, validated)
        self.assertEqual(validated["project_id"], "KMFA")
        self.assertEqual(validated["version"], "0.1.4")
        self.assertEqual(validated["stage_id"], "S10")
        self.assertEqual(validated["phase_id"], "S10-P3")
        self.assertEqual(validated["phase_scope"], "v014_s10_p3_report_export_only")
        self.assertEqual(validated["task_id"], "KMFA-V014-S10-P3-REPORT-EXPORT-20260704")
        self.assertEqual(validated["completed_task_ids"], ["S10P3T01", "S10P3T02", "S10P3T03"])
        self.assertEqual(validated["acceptance_ids"], ["ACC-V014-S10-P3-REPORT-EXPORT"])

        progress = validated["stage10_phase_progress"]
        self.assertEqual(progress["completed_phase_count"], 3)
        self.assertEqual(progress["total_phase_count"], 3)
        self.assertEqual(progress["derived_percent_label"], "100.00%")
        self.assertTrue(progress["s10_p1_performed"])
        self.assertTrue(progress["s10_p2_performed"])
        self.assertTrue(progress["s10_p3_performed"])
        self.assertFalse(progress["stage10_review_performed"])

        summary = validated["report_export_summary"]
        self.assertEqual(summary["template_count"], 2)
        self.assertEqual(summary["report_export_record_count"], 2)
        self.assertEqual(summary["grade_distribution"], {"D": 2})
        self.assertEqual(summary["html_export_count"], 2)
        self.assertEqual(summary["csv_appendix_count"], 2)
        self.assertEqual(summary["excel_compatible_download_count"], 2)
        self.assertTrue(summary["pdf_export_enabled_after_template_stable"])
        self.assertEqual(summary["committed_pdf_file_count"], 0)
        self.assertEqual(summary["committed_excel_file_count"], 0)
        self.assertEqual(summary["formal_report_count"], 0)
        self.assertEqual(summary["business_decision_basis_count"], 0)
        self.assertEqual(summary["pending_reconciliation_count"], 12)

        policy = validated["report_export_policy"]
        self.assertTrue(policy["html_export_allowed"])
        self.assertTrue(policy["csv_excel_export_allowed"])
        self.assertEqual(policy["excel_download_mode"], "excel_compatible_csv_no_workbook_committed")
        self.assertTrue(policy["pdf_export_policy_enabled"])
        self.assertTrue(policy["pdf_private_runtime_only"])
        self.assertFalse(policy["pdf_file_committed"])
        self.assertFalse(policy["excel_workbook_committed"])
        self.assertFalse(policy["formal_report_allowed"])
        self.assertFalse(policy["business_decision_basis_allowed"])
        self.assertEqual(policy["record_version_binding_count"], 2)

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
        self.assertFalse(validated["quality_gate"]["stage10_review_allowed"])
        self.assertFalse(validated["quality_gate"]["github_upload_allowed"])


if __name__ == "__main__":
    unittest.main()
