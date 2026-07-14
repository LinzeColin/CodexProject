import unittest

from KMFA.tools.check_v014_s01_stage_review import validate_v014_s01_stage_review


class TestV014S01StageReview(unittest.TestCase):
    def test_stage_review_closes_stage1_without_upload_or_s02(self) -> None:
        result = validate_v014_s01_stage_review()

        self.assertEqual(result["stage_id"], "S01")
        self.assertEqual(result["review_scope"], "v014_s01_stage_review_only")
        self.assertEqual(result["phase_count"], 3)
        self.assertEqual(result["phase_results"], {"S01-P1": "PASS", "S01-P2": "PASS", "S01-P3": "PASS"})
        self.assertTrue(result["stage_review_performed"])
        self.assertFalse(result["github_upload_performed"])
        self.assertFalse(result["s02_started"])
        self.assertFalse(result["raw_inventory_performed"])
        self.assertEqual(result["open_review_finding_count"], 0)
        self.assertEqual(result["fixed_review_finding_count"], 0)
        self.assertEqual(result["release_state"]["current_go_no_go"], "NO_GO")
        self.assertFalse(result["release_state"]["delivery_allowed"])
        self.assertFalse(result["release_state"]["github_main_upload_allowed"])
        self.assertEqual(result["no_omission_baseline"]["v14_stages"], 18)
        self.assertEqual(result["no_omission_baseline"]["v14_phases"], 54)
        self.assertEqual(result["no_omission_baseline"]["v14_tasks"], 162)
        self.assertEqual(result["next_recommended_phase"], "S02-P1")


if __name__ == "__main__":
    unittest.main()
