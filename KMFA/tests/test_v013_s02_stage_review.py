import unittest

from KMFA.tools.check_v013_s02_stage_review import validate_v013_s02_stage_review


class TestV013S02StageReview(unittest.TestCase):
    def test_stage_review_closes_s02_without_upload_or_release(self) -> None:
        result = validate_v013_s02_stage_review()

        self.assertEqual(result["stage_id"], "S02")
        self.assertEqual(result["review_scope"], "v013_s02_stage_review_only")
        self.assertEqual(result["phase_count"], 3)
        self.assertEqual(result["open_review_finding_count"], 0)
        self.assertEqual(result["fixed_review_finding_count"], 0)
        self.assertTrue(result["stage_review_performed"])
        self.assertFalse(result["github_upload_performed"])
        self.assertFalse(result["delivery_allowed"])
        self.assertFalse(result["formal_report_allowed"])
        self.assertFalse(result["business_decision_basis_allowed"])
        self.assertFalse(result["business_execution_allowed"])
        self.assertFalse(result["raw_value_matching_performed"])
        self.assertFalse(result["raw_dir_read_performed_by_stage_review"])
        self.assertFalse(result["raw_dir_mutation_performed"])
        self.assertEqual(result["phase_results"]["S02-P1"], "PASS")
        self.assertEqual(result["phase_results"]["S02-P2"], "PASS")
        self.assertEqual(result["phase_results"]["S02-P3"], "PASS")
        self.assertEqual(result["current_data_quality_grade"], "Q2")
        self.assertEqual(result["current_report_grade"], "D")
        self.assertEqual(result["release_permission"], "blocked")
        self.assertIn("S03-P1", result["next_required_step"])
        self.assertIn("overall completion upload gate", result["next_required_step"])


if __name__ == "__main__":
    unittest.main()
