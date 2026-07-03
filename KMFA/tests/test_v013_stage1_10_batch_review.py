import unittest

from KMFA.tools.check_v013_stage1_10_batch_review import validate_v013_stage1_10_batch_review


class TestV013Stage110BatchReview(unittest.TestCase):
    def test_batch_review_closes_stages_1_10_without_upload_or_raw_read(self) -> None:
        result = validate_v013_stage1_10_batch_review()

        self.assertEqual(result["review_scope"], "v013_stage1_10_batch_overall_review_only")
        self.assertTrue(result["stage1_10_batch_overall_review_performed"])
        self.assertEqual(result["stage_count"], 10)
        self.assertEqual(result["validated_stage_ids"], [f"S{idx:02d}" for idx in range(1, 11)])
        self.assertEqual(set(result["stage_results"].values()), {"PASS"})
        self.assertTrue(result["all_stage_reviews_validated"])
        self.assertEqual(result["open_batch_finding_count"], 0)
        self.assertGreaterEqual(result["fixed_batch_finding_count"], 1)
        self.assertFalse(result["legacy_individual_stage_upload_artifacts_current_gate"])
        self.assertFalse(result["github_upload_performed"])
        self.assertTrue(result["github_upload_ready_next_gate"])
        self.assertEqual(result["github_upload_status"], "not_uploaded_ready_for_separate_stage1_10_github_upload_gate")
        self.assertFalse(result["raw_dir_read_performed_by_batch_review"])
        self.assertFalse(result["raw_dir_read_performed_by_stage_validators"])
        self.assertFalse(result["raw_dir_mutation_performed"])
        self.assertFalse(result["raw_value_matching_performed"])
        self.assertFalse(result["lineage_full_check_completed"])
        self.assertFalse(result["formal_report_allowed"])
        self.assertFalse(result["business_decision_basis_allowed"])
        self.assertFalse(result["business_execution_allowed"])
        self.assertFalse(result["delivery_allowed"])
        self.assertEqual(result["current_report_grade"], "D")
        self.assertEqual(result["current_data_quality_grade"], "Q4")
        self.assertEqual(result["release_permission"], "blocked")
        self.assertEqual(result["pending_reconciliation_count"], 12)
        self.assertEqual(result["confirmed_resolution_count"], 0)
        self.assertIn("GitHub upload gate", result["next_required_step"])
        self.assertIn("separate run", result["next_required_step"])


if __name__ == "__main__":
    unittest.main()
