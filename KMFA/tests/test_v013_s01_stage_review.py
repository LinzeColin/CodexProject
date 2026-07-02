import unittest

from KMFA.tools.check_v013_s01_stage_review import validate_v013_s01_stage_review


class TestV013S01StageReview(unittest.TestCase):
    def test_stage_review_closes_s01_without_upload_or_release(self) -> None:
        result = validate_v013_s01_stage_review()

        self.assertEqual(result["stage_id"], "S01")
        self.assertEqual(result["review_scope"], "v013_s01_stage_review_only")
        self.assertEqual(result["phase_count"], 3)
        self.assertEqual(result["open_review_finding_count"], 0)
        self.assertEqual(result["fixed_review_finding_count"], 0)
        self.assertTrue(result["stage_review_performed"])
        self.assertFalse(result["github_upload_performed"])
        self.assertFalse(result["delivery_allowed"])
        self.assertFalse(result["formal_report_allowed"])
        self.assertFalse(result["business_execution_allowed"])
        self.assertEqual(result["phase_results"]["S01-P1"], "PASS")
        self.assertEqual(result["phase_results"]["S01-P2"], "PASS")
        self.assertEqual(result["phase_results"]["S01-P3"], "PASS")
        self.assertEqual(result["next_required_step"], "Stage 1 GitHub upload gate after rebase and review evidence binding.")


if __name__ == "__main__":
    unittest.main()
