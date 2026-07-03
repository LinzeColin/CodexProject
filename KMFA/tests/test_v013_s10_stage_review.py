import unittest

from KMFA.tools.check_v013_s10_stage_review import validate_v013_s10_stage_review


class TestV013S10StageReview(unittest.TestCase):
    def test_stage_review_closes_s10_without_upload_raw_read_or_stage1_10_batch(self) -> None:
        result = validate_v013_s10_stage_review()

        self.assertEqual(result["stage_id"], "S10")
        self.assertEqual(result["review_scope"], "v013_s10_stage_review_only")
        self.assertEqual(result["phase_count"], 3)
        self.assertEqual(result["phase_results"], {"S10-P1": "PASS", "S10-P2": "PASS", "S10-P3": "PASS"})
        self.assertTrue(result["s10_p1_dependency_validated"])
        self.assertTrue(result["s10_p2_dependency_validated"])
        self.assertTrue(result["s10_p3_dependency_validated"])
        self.assertTrue(result["stage_review_performed"])
        self.assertFalse(result["stage1_10_batch_overall_review_performed"])
        self.assertEqual(result["open_review_finding_count"], 0)
        self.assertGreaterEqual(result["fixed_review_finding_count"], 1)
        self.assertEqual(result["current_data_quality_grade"], "Q4")
        self.assertEqual(result["current_report_grade"], "D")
        self.assertEqual(result["release_permission"], "blocked")
        self.assertEqual(result["report_template_count"], 2)
        self.assertEqual(result["report_template_section_count"], 11)
        self.assertEqual(result["report_grade_record_count"], 2)
        self.assertEqual(result["report_export_record_count"], 2)
        self.assertEqual(result["html_export_count"], 2)
        self.assertEqual(result["csv_appendix_count"], 2)
        self.assertEqual(result["excel_compatible_download_count"], 2)
        self.assertEqual(result["pending_reconciliation_count"], 12)
        self.assertEqual(result["confirmed_resolution_count"], 0)
        self.assertEqual(result["formal_report_count"], 0)
        self.assertEqual(result["business_decision_basis_count"], 0)
        self.assertFalse(result["raw_dir_read_performed_by_stage_review"])
        self.assertFalse(result["raw_dir_read_performed_by_dependency_validators"])
        self.assertFalse(result["raw_dir_mutation_performed"])
        self.assertFalse(result["github_upload_performed"])
        self.assertTrue(result["github_upload_deferred_until_stage1_10_batch"])
        self.assertEqual(result["github_upload_status"], "not_uploaded_deferred_until_stage1_10_batch")
        self.assertFalse(result["legacy_stage10_upload_artifacts_current_gate"])
        self.assertFalse(result["delivery_allowed"])
        self.assertFalse(result["formal_report_allowed"])
        self.assertFalse(result["business_execution_allowed"])
        self.assertIn("Stage 1-10 batch overall review", result["next_required_step"])
        self.assertIn("separate run", result["next_required_step"])


if __name__ == "__main__":
    unittest.main()
