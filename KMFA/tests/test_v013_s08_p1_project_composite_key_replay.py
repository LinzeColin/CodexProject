import unittest

from KMFA.tools.check_v013_s08_p1_project_composite_key_replay import (
    validate_v013_s08_p1_project_composite_key_replay,
)
from KMFA.tools.v013_s08_p1_project_composite_key_replay import generate


class TestV013S08P1ProjectCompositeKeyReplay(unittest.TestCase):
    def test_replay_locks_project_composite_key_without_stage8_review_or_upload(self) -> None:
        generate()
        result = validate_v013_s08_p1_project_composite_key_replay()

        self.assertEqual(result["stage_id"], "S08")
        self.assertEqual(result["phase_id"], "S08-P1")
        self.assertEqual(result["phase_scope"], "v013_s08_p1_project_composite_key_replay_only")
        self.assertEqual(result["required_component_count"], 8)
        self.assertEqual(result["profile_count"], 4)
        self.assertEqual(result["match_result_count"], 3)
        self.assertEqual(result["manual_review_queue_count"], 2)
        self.assertEqual(result["strong_auto_match_count"], 1)
        self.assertEqual(result["human_review_required_count"], 2)
        self.assertEqual(result["matching_weights_sum_bps"], 10000)
        self.assertEqual(result["strong_threshold_bps"], 8500)
        self.assertEqual(result["human_review_threshold_bps"], 7000)
        self.assertFalse(result["missing_single_component_blocks_all_matching"])
        self.assertTrue(result["below_strong_threshold_enters_manual_review"])
        self.assertEqual(result["q5_calculation_baseline_allowed_count"], 0)
        self.assertEqual(result["formal_report_allowed_count"], 0)
        self.assertFalse(result["s08_p2_performed"])
        self.assertFalse(result["s08_p3_performed"])
        self.assertFalse(result["stage8_review_performed"])
        self.assertFalse(result["github_upload_performed"])
        self.assertTrue(result["github_upload_deferred_until_stage10_batch"])
        self.assertFalse(result["raw_dir_read_performed"])
        self.assertFalse(result["raw_dir_mutation_performed"])
        self.assertIn("S08-P2", result["next_required_step"])
        self.assertIn("Stages 1-10", result["next_required_step"])
        self.assertIn("separate run", result["next_required_step"])


if __name__ == "__main__":
    unittest.main()
