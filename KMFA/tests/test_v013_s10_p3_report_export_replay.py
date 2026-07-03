import unittest

from KMFA.tools.check_v013_s10_p3_report_export_replay import (
    validate_v013_s10_p3_report_export_replay,
)
from KMFA.tools.v013_s10_p3_report_export_replay import generate


class V013S10P3ReportExportReplayTests(unittest.TestCase):
    def test_replays_public_safe_report_exports_without_review_or_upload(self) -> None:
        manifest = generate()
        validated = validate_v013_s10_p3_report_export_replay()

        self.assertEqual(manifest, validated)
        self.assertEqual(validated["stage_id"], "S10")
        self.assertEqual(validated["phase_id"], "S10-P3")
        self.assertEqual(validated["phase_scope"], "v013_s10_p3_report_export_replay_only")
        self.assertEqual(validated["completed_task_ids"], ["S10PCT01", "S10PCT02", "S10PCT03"])
        self.assertEqual(validated["stage10_phase_progress"]["completed_phase_count"], 3)
        self.assertEqual(validated["stage10_phase_progress"]["derived_percent_label"], "100.00%")
        self.assertTrue(validated["stage10_phase_progress"]["s10_p1_performed"])
        self.assertTrue(validated["stage10_phase_progress"]["s10_p2_performed"])
        self.assertTrue(validated["stage10_phase_progress"]["s10_p3_performed"])
        self.assertFalse(validated["stage10_phase_progress"]["stage10_review_performed"])

        summary = validated["legacy_s10_p3_summary"]
        self.assertEqual(summary["report_export_record_count"], 2)
        self.assertEqual(summary["html_export_count"], 2)
        self.assertEqual(summary["csv_appendix_count"], 2)
        self.assertEqual(summary["excel_compatible_download_count"], 2)
        self.assertEqual(summary["committed_pdf_file_count"], 0)
        self.assertEqual(summary["committed_excel_file_count"], 0)
        self.assertEqual(summary["formal_report_count"], 0)
        self.assertEqual(summary["business_decision_basis_count"], 0)
        self.assertEqual(summary["pending_reconciliation_count"], 12)
        self.assertEqual(summary["grade_distribution"], {"D": 2})

        export_policy = validated["report_export_policy"]
        self.assertTrue(export_policy["html_export_allowed"])
        self.assertTrue(export_policy["csv_excel_export_allowed"])
        self.assertEqual(export_policy["excel_download_mode"], "excel_compatible_csv_no_workbook_committed")
        self.assertTrue(export_policy["pdf_export_policy_enabled"])
        self.assertTrue(export_policy["pdf_private_runtime_only"])
        self.assertFalse(export_policy["pdf_file_committed"])
        self.assertFalse(export_policy["excel_workbook_committed"])
        self.assertFalse(export_policy["formal_report_allowed"])
        self.assertFalse(export_policy["business_decision_basis_allowed"])

        upload = validated["github_upload"]
        self.assertFalse(upload["github_upload_performed"])
        self.assertFalse(upload["github_upload_ready_next_gate"])
        self.assertTrue(upload["github_upload_deferred_until_stage10_batch"])

        raw_boundary = validated["raw_data_boundary"]
        self.assertFalse(raw_boundary["codex_read_performed_by_this_phase"])
        self.assertFalse(raw_boundary["codex_list_performed_by_this_phase"])
        self.assertFalse(raw_boundary["codex_generate_inside_allowed"])
        self.assertFalse(raw_boundary["github_commit_allowed"])


if __name__ == "__main__":
    unittest.main()
