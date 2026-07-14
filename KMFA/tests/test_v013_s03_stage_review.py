import unittest

from KMFA.tools.check_v013_s03_stage_review import validate_v013_s03_stage_review


class TestV013S03StageReview(unittest.TestCase):
    def test_stage_review_closes_s03_without_upload_or_raw_access(self) -> None:
        result = validate_v013_s03_stage_review()

        self.assertEqual(result["stage_id"], "S03")
        self.assertEqual(result["review_scope"], "v013_s03_stage_review_only")
        self.assertEqual(result["phase_count"], 3)
        self.assertEqual(result["phase_results"]["S03-P1"], "PASS")
        self.assertEqual(result["phase_results"]["S03-P2"], "PASS")
        self.assertEqual(result["phase_results"]["S03-P3"], "PASS")
        self.assertTrue(result["s03_p1_dependency_validated"])
        self.assertTrue(result["s03_p2_dependency_validated"])
        self.assertTrue(result["s03_p3_dependency_validated"])
        self.assertTrue(result["stage_review_performed"])
        self.assertEqual(result["open_review_finding_count"], 0)
        self.assertEqual(result["fixed_review_finding_count"], 0)
        self.assertTrue(result["github_upload_ready_next_gate"])
        self.assertFalse(result["github_upload_performed"])
        self.assertFalse(result["delivery_allowed"])
        self.assertFalse(result["formal_report_allowed"])
        self.assertFalse(result["business_decision_basis_allowed"])
        self.assertFalse(result["business_execution_allowed"])
        self.assertFalse(result["raw_value_matching_performed"])
        self.assertFalse(result["raw_dir_read_performed_by_stage_review"])
        self.assertTrue(result["raw_dir_read_performed_by_dependency_validators"])
        self.assertFalse(result["raw_dir_mutation_performed"])
        self.assertEqual(result["current_data_quality_grade"], "Q2")
        self.assertEqual(result["current_report_grade"], "D")
        self.assertEqual(result["release_permission"], "blocked")
        self.assertIn("Stage 3 GitHub upload", result["next_required_step"])
        self.assertIn("separate run", result["next_required_step"])


if __name__ == "__main__":
    unittest.main()
