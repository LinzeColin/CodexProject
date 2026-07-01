import unittest

from KMFA.tools.check_whole_project_final_review import validate_whole_project_final_review


class WholeProjectFinalReviewTests(unittest.TestCase):
    def test_whole_project_review_passes_local_gate_but_blocks_delivery(self) -> None:
        counts = validate_whole_project_final_review()

        self.assertEqual(counts["part_count"], 6)
        self.assertEqual(counts["stage_count"], 18)
        self.assertEqual(counts["full_kmfa_unit_tests"], 276)
        self.assertEqual(counts["open_launch_blocker_count"], 3)
        self.assertEqual(counts["delivery_allowed_count"], 0)


if __name__ == "__main__":
    unittest.main()
