import unittest

from KMFA.tools.check_v013_s07_p3_redcircle_postponement_replay import (
    validate_v013_s07_p3_redcircle_postponement_replay,
)


class TestV013S07P3RedcirclePostponementReplay(unittest.TestCase):
    def test_redcircle_postponement_replay_stays_public_safe_and_local_only(self) -> None:
        result = validate_v013_s07_p3_redcircle_postponement_replay()

        self.assertEqual(result["stage_id"], "S07")
        self.assertEqual(result["phase_id"], "S07-P3")
        self.assertEqual(result["phase_scope"], "v013_s07_p3_redcircle_postponement_replay_only")
        self.assertTrue(result["s06_stage_review_dependency_validated"])
        self.assertTrue(result["s07_p1_dependency_validated"])
        self.assertTrue(result["s07_p2_dependency_validated"])
        self.assertTrue(result["legacy_s07_p3_dependency_validated"])
        self.assertEqual(result["reserved_template_count"], 4)
        self.assertEqual(result["connector_policy_count"], 1)
        self.assertEqual(result["rollback_plan_count"], 4)
        self.assertEqual(result["automatic_connector_allowed_count"], 0)
        self.assertEqual(result["registry_source_count"], 4)
        self.assertEqual(result["template_contract_hash_count"], 4)
        self.assertEqual(result["source_private_ref_count"], 4)
        self.assertEqual(result["manual_export_file_allowed_count"], 4)
        self.assertEqual(result["q4_human_confirmed_count"], 0)
        self.assertEqual(result["q5_calculation_baseline_allowed_count"], 0)
        self.assertEqual(result["formal_report_allowed_count"], 0)
        self.assertFalse(result["d15_file_mvp_automatic_connector_allowed"])
        self.assertFalse(result["external_connector_included"])
        self.assertTrue(result["read_only_required"])
        self.assertTrue(result["hash_retention_required"])
        self.assertTrue(result["rollback_plan_required"])
        self.assertTrue(result["manual_approval_required"])
        self.assertFalse(result["raw_dir_read_performed"])
        self.assertFalse(result["raw_dir_mutation_performed"])
        self.assertFalse(result["s07_p1_performed"])
        self.assertFalse(result["s07_p2_performed"])
        self.assertTrue(result["s07_p3_performed"])
        self.assertFalse(result["stage7_review_performed"])
        self.assertFalse(result["github_upload_performed"])
        self.assertTrue(result["github_upload_deferred_until_stage10_batch"])
        self.assertFalse(result["delivery_allowed"])
        self.assertFalse(result["formal_report_allowed"])
        self.assertEqual(result["current_data_quality_grade"], "Q4")
        self.assertEqual(result["current_report_grade"], "D")
        self.assertEqual(result["release_permission"], "blocked")
        self.assertIn("Stage 7 review", result["next_required_step"])
        self.assertIn("separate run", result["next_required_step"])
        self.assertIn("Stage 1-10", result["next_required_step"])


if __name__ == "__main__":
    unittest.main()
