import unittest

from KMFA.tools.check_v014_s15_p2_performance_review_list import (
    validate_v014_s15_p2_performance_review_list,
)
from KMFA.tools.v014_s15_p2_performance_review_list import (
    REQUIRED_MANUAL_REVIEW_FIELDS,
    REQUIRED_PERFORMANCE_REVIEW_FIELDS,
    generate,
)


class V014S15P2PerformanceReviewListTests(unittest.TestCase):
    def test_outputs_public_safe_fact_table_and_review_items_without_payroll_or_upload(self) -> None:
        manifest = generate()
        validated = validate_v014_s15_p2_performance_review_list()

        self.assertEqual(manifest, validated)
        self.assertEqual(validated["project_id"], "KMFA")
        self.assertEqual(validated["version"], "0.1.4")
        self.assertEqual(validated["stage_id"], "S15")
        self.assertEqual(validated["phase_id"], "S15-P2")
        self.assertEqual(validated["phase_scope"], "v014_s15_p2_performance_review_list_only")
        self.assertEqual(validated["task_id"], "KMFA-V014-S15-P2-PERFORMANCE-REVIEW-LIST-20260705")
        self.assertEqual(validated["completed_task_ids"], ["S15P2T01", "S15P2T02", "S15P2T03"])
        self.assertEqual(validated["acceptance_ids"], ["ACC-V014-S15-P2-PERFORMANCE-REVIEW-LIST"])

        progress = validated["stage15_phase_progress"]
        self.assertEqual(progress["completed_phase_count"], 2)
        self.assertEqual(progress["total_phase_count"], 3)
        self.assertEqual(progress["derived_percent_label"], "66.67%")
        self.assertTrue(progress["s15_p1_performed"])
        self.assertTrue(progress["s15_p2_performed"])
        self.assertFalse(progress["s15_p3_performed"])
        self.assertFalse(progress["stage15_review_performed"])

        summary = validated["performance_review_summary"]
        self.assertEqual(summary["required_review_fields"], list(REQUIRED_PERFORMANCE_REVIEW_FIELDS))
        self.assertEqual(summary["required_manual_review_fields"], list(REQUIRED_MANUAL_REVIEW_FIELDS))
        self.assertEqual(summary["performance_fact_row_count"], 4)
        self.assertEqual(summary["abnormal_review_item_count"], 16)
        self.assertEqual(summary["manual_review_field_count"], 4)
        self.assertEqual(summary["salary_calculation_count"], 0)
        self.assertEqual(summary["wage_calculation_count"], 0)
        self.assertEqual(summary["bonus_approval_count"], 0)
        self.assertEqual(summary["payroll_export_count"], 0)
        self.assertEqual(summary["final_compensation_decision_count"], 0)
        self.assertEqual(summary["report_grade_visible"], "D")

        quality = validated["quality_gate"]
        self.assertTrue(quality["performance_fact_table_output_allowed"])
        self.assertTrue(quality["abnormal_project_review_list_allowed"])
        self.assertTrue(quality["review_item_output_allowed"])
        self.assertFalse(quality["salary_calculation_allowed"])
        self.assertFalse(quality["wage_calculation_allowed"])
        self.assertFalse(quality["bonus_approval_allowed"])
        self.assertFalse(quality["payroll_export_allowed"])
        self.assertFalse(quality["final_compensation_decision_allowed"])
        self.assertFalse(quality["payment_execution_allowed"])
        self.assertFalse(quality["s15_p3_allowed"])
        self.assertFalse(quality["stage15_review_allowed"])
        self.assertFalse(quality["github_upload_allowed"])

        raw_boundary = validated["raw_data_boundary"]
        self.assertFalse(raw_boundary["raw_inbox_read_by_this_phase"])
        self.assertFalse(raw_boundary["raw_inbox_listed_by_this_phase"])
        self.assertFalse(raw_boundary["raw_inbox_mutated_by_this_phase"])

        upload = validated["github_upload"]
        self.assertFalse(upload["github_upload_performed"])
        self.assertFalse(upload["github_upload_ready_next_gate"])
        self.assertTrue(upload["github_upload_deferred_until_v014_stage1_18_complete"])


if __name__ == "__main__":
    unittest.main()
