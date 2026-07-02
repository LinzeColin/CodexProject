import unittest

from KMFA.tools.check_v013_s06_stage_review import validate_v013_s06_stage_review


class TestV013S06StageReview(unittest.TestCase):
    def test_stage_review_closes_s06_without_upload_or_raw_mutation(self) -> None:
        result = validate_v013_s06_stage_review()

        self.assertEqual(result["stage_id"], "S06")
        self.assertEqual(result["review_scope"], "v013_s06_stage_review_only")
        self.assertEqual(result["phase_count"], 3)
        self.assertEqual(result["phase_results"]["S06-P1"], "PASS")
        self.assertEqual(result["phase_results"]["S06-P2"], "PASS")
        self.assertEqual(result["phase_results"]["S06-P3"], "PASS")
        self.assertTrue(result["s06_p1_dependency_validated"])
        self.assertTrue(result["s06_p2_dependency_validated"])
        self.assertTrue(result["s06_p3_dependency_validated"])
        self.assertTrue(result["stage_review_performed"])
        self.assertEqual(result["open_review_finding_count"], 0)
        self.assertEqual(result["fixed_review_finding_count"], 0)
        self.assertFalse(result["github_upload_ready_next_gate"])
        self.assertTrue(result["github_upload_deferred_until_stage10_batch"])
        self.assertFalse(result["github_upload_performed"])
        self.assertFalse(result["delivery_allowed"])
        self.assertFalse(result["formal_report_allowed"])
        self.assertFalse(result["business_decision_basis_allowed"])
        self.assertFalse(result["business_execution_allowed"])
        self.assertFalse(result["raw_value_matching_performed"])
        self.assertFalse(result["raw_dir_read_performed_by_stage_review"])
        self.assertFalse(result["raw_dir_read_performed_by_dependency_validators"])
        self.assertFalse(result["raw_dir_mutation_performed"])
        self.assertEqual(result["project_status_count"], 2)
        self.assertEqual(result["blocked_project_status_count"], 2)
        self.assertEqual(result["q5_allowed_count"], 0)
        self.assertEqual(result["report_grade_a_allowed_count"], 0)
        self.assertEqual(result["current_data_quality_grade"], "Q4")
        self.assertEqual(result["current_report_grade"], "D")
        self.assertEqual(result["release_permission"], "blocked")
        self.assertIn("S07-P1", result["next_required_step"])
        self.assertIn("Stages 1-10", result["next_required_step"])
        self.assertIn("separate run", result["next_required_step"])


if __name__ == "__main__":
    unittest.main()
