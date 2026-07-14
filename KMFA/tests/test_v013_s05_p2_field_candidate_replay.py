import unittest

from KMFA.tools.check_v013_s05_p2_field_candidate_replay import (
    validate_v013_s05_p2_field_candidate_replay,
)


class TestV013S05P2FieldCandidateReplay(unittest.TestCase):
    def test_field_candidate_replay_locks_public_safe_owner_downgrade(self) -> None:
        result = validate_v013_s05_p2_field_candidate_replay()

        self.assertEqual(result["stage_id"], "S05")
        self.assertEqual(result["phase_id"], "S05-P2")
        self.assertEqual(result["phase_scope"], "v013_s05_p2_field_candidate_replay_only")
        self.assertTrue(result["s05_p1_dependency_validated"])
        self.assertTrue(result["legacy_s05_p2_dependency_validated"])
        self.assertEqual(result["fixture_candidate_count"], 45)
        self.assertEqual(result["required_fields_per_candidate"], 5)
        self.assertEqual(result["private_value_hash_recorded_count"], 40)
        self.assertEqual(result["private_value_pending_count"], 5)
        self.assertEqual(result["source_anchor_recorded_count"], 40)
        self.assertEqual(result["source_anchor_pending_count"], 5)
        self.assertEqual(result["pending_source_candidate_count"], 1)
        self.assertEqual(result["q4_human_confirmed_count"], 0)
        self.assertEqual(result["q5_calculation_baseline_allowed_count"], 0)
        self.assertEqual(result["active_decision_code"], "downgrade_to_cross_source_support")
        self.assertTrue(result["completion_gate_ready"])
        self.assertEqual(result["completion_gate_mode"], "owner_downgrade_to_cross_source_support")
        self.assertFalse(result["raw_dir_read_required"])
        self.assertFalse(result["raw_dir_read_performed"])
        self.assertFalse(result["raw_dir_mutation_performed"])
        self.assertFalse(result["field_plaintext_publication_allowed"])
        self.assertFalse(result["s05_p3_performed"])
        self.assertFalse(result["stage5_review_performed"])
        self.assertFalse(result["github_upload_performed"])
        self.assertTrue(result["github_upload_deferred_until_stage10_batch"])
        self.assertFalse(result["delivery_allowed"])
        self.assertEqual(result["current_data_quality_grade"], "Q2")
        self.assertEqual(result["current_report_grade"], "D")
        self.assertEqual(result["release_permission"], "blocked")
        self.assertIn("S05-P3", result["next_required_step"])
        self.assertIn("separate run", result["next_required_step"])
        self.assertIn("Stage 1-10", result["next_required_step"])


if __name__ == "__main__":
    unittest.main()
