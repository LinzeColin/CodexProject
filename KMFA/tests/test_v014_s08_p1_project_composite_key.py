import unittest

from KMFA.tools.check_v014_s08_p1_project_composite_key import (
    validate_v014_s08_p1_project_composite_key,
)
from KMFA.tools.v014_s08_p1_project_composite_key import generate


class TestV014S08P1ProjectCompositeKey(unittest.TestCase):
    def test_project_composite_key_stays_hash_only_without_s08p2_or_upload(self) -> None:
        generate()
        result = validate_v014_s08_p1_project_composite_key()

        self.assertEqual(result["stage_id"], "S08")
        self.assertEqual(result["phase_id"], "S08-P1")
        self.assertEqual(result["phase_scope"], "v014_s08_p1_project_composite_key_only")
        self.assertEqual(result["project_composite_key_summary"]["required_component_count"], 8)
        self.assertEqual(result["project_composite_key_summary"]["profile_count"], 4)
        self.assertEqual(result["project_composite_key_summary"]["match_result_count"], 3)
        self.assertEqual(result["project_composite_key_summary"]["manual_review_queue_count"], 2)
        self.assertEqual(result["project_composite_key_summary"]["strong_auto_match_count"], 1)
        self.assertEqual(result["project_composite_key_summary"]["human_review_required_count"], 2)
        self.assertEqual(result["matching_policy"]["matching_weights_sum_bps"], 10000)
        self.assertEqual(result["matching_policy"]["strong_threshold_bps"], 8500)
        self.assertEqual(result["matching_policy"]["human_review_threshold_bps"], 7000)
        self.assertFalse(result["matching_policy"]["missing_single_component_blocks_all_matching"])
        self.assertTrue(result["matching_policy"]["below_strong_threshold_enters_manual_review"])
        self.assertEqual(result["matching_policy"]["auto_merge_allowed_for_review_queue_count"], 0)
        self.assertTrue(result["stage8_phase_progress"]["s08_p1_performed"])
        self.assertFalse(result["stage8_phase_progress"]["s08_p2_performed"])
        self.assertFalse(result["stage8_phase_progress"]["s08_p3_performed"])
        self.assertFalse(result["stage8_phase_progress"]["stage8_review_performed"])
        self.assertFalse(result["github_upload"]["github_upload_performed"])
        self.assertTrue(result["github_upload"]["github_upload_deferred_until_v014_stage1_18_complete"])
        self.assertFalse(result["raw_data_boundary"]["raw_inbox_read_by_this_phase"])
        self.assertFalse(result["raw_data_boundary"]["raw_inbox_mutated_by_this_phase"])
        self.assertEqual(result["next_recommended_phase"], "S08-P2")
        self.assertIn("Stage 1-18", result["next_phase_instruction"])


if __name__ == "__main__":
    unittest.main()
