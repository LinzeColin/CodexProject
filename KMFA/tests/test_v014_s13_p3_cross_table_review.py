import unittest

from KMFA.tools.check_v014_s13_p3_cross_table_review import (
    validate_v014_s13_p3_cross_table_review,
)
from KMFA.tools.v014_s13_p3_cross_table_review import generate


class V014S13P3CrossTableReviewTests(unittest.TestCase):
    def test_locks_cross_table_review_without_stage_review_or_upload(self) -> None:
        manifest = generate()
        validated = validate_v014_s13_p3_cross_table_review()

        self.assertEqual(manifest, validated)
        self.assertEqual(validated["project_id"], "KMFA")
        self.assertEqual(validated["version"], "0.1.4")
        self.assertEqual(validated["stage_id"], "S13")
        self.assertEqual(validated["phase_id"], "S13-P3")
        self.assertEqual(validated["phase_scope"], "v014_s13_p3_cross_table_review_only")
        self.assertEqual(validated["task_id"], "KMFA-V014-S13-P3-CROSS-TABLE-REVIEW-20260705")
        self.assertEqual(validated["completed_task_ids"], ["S13P3T01", "S13P3T02", "S13P3T03"])
        self.assertEqual(validated["acceptance_ids"], ["ACC-V014-S13-P3-CROSS-TABLE-REVIEW"])

        progress = validated["stage13_phase_progress"]
        self.assertEqual(progress["completed_phase_count"], 3)
        self.assertEqual(progress["total_phase_count"], 3)
        self.assertEqual(progress["derived_percent_label"], "100.00%")
        self.assertTrue(progress["s13_p1_performed"])
        self.assertTrue(progress["s13_p2_performed"])
        self.assertTrue(progress["s13_p3_performed"])
        self.assertFalse(progress["stage13_review_performed"])

        summary = validated["cross_table_review_summary"]
        self.assertEqual(summary["review_dimension_count"], 4)
        self.assertEqual(summary["difference_queue_count"], 4)
        self.assertEqual(summary["quality_report_count"], 1)
        self.assertEqual(summary["html_draft_count"], 1)
        self.assertEqual(summary["pending_reconciliation_count"], 12)
        self.assertEqual(summary["report_grade_visible"], "D")
        self.assertEqual(summary["formal_report_count"], 0)
        self.assertEqual(summary["business_decision_basis_count"], 0)
        self.assertEqual(summary["difference_auto_resolution_count"], 0)

        baseline = validated["v14_html_uiux_baseline"]
        self.assertTrue(baseline["taskpack_html_requirement_read"])
        self.assertEqual(baseline["audit_file_count"], 6)
        self.assertEqual(baseline["audit_control_row_count"], 54)
        self.assertEqual(baseline["audit_pass_count"], 54)
        self.assertEqual(baseline["audit_warn_count"], 0)
        self.assertEqual(baseline["audit_fail_count"], 0)
        self.assertTrue(baseline["implementation_reflects_cross_table_review"])
        self.assertTrue(baseline["implementation_reflects_difference_queue"])
        self.assertTrue(baseline["implementation_reflects_no_external_action_limits"])

        upload = validated["github_upload"]
        self.assertFalse(upload["github_upload_performed"])
        self.assertFalse(upload["github_upload_ready_next_gate"])
        self.assertTrue(upload["github_upload_deferred_until_v014_stage1_18_complete"])

        raw_boundary = validated["raw_data_boundary"]
        self.assertFalse(raw_boundary["raw_inbox_read_by_this_phase"])
        self.assertFalse(raw_boundary["raw_inbox_listed_by_this_phase"])
        self.assertFalse(raw_boundary["raw_inbox_mutated_by_this_phase"])

        quality = validated["quality_gate"]
        self.assertTrue(quality["cross_table_review_evidence_allowed"])
        self.assertTrue(quality["difference_queue_output_allowed"])
        self.assertTrue(quality["operating_report_quality_report_allowed"])
        self.assertFalse(quality["formal_report_allowed"])
        self.assertFalse(quality["business_decision_basis_allowed"])
        self.assertFalse(quality["difference_auto_resolution_allowed"])
        self.assertFalse(quality["stage13_review_allowed"])
        self.assertFalse(quality["github_upload_allowed"])


if __name__ == "__main__":
    unittest.main()
