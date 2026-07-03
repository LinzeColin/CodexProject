import unittest

from KMFA.tools.check_v013_s08_p3_entity_matching_quality_replay import (
    validate_v013_s08_p3_entity_matching_quality_replay,
)
from KMFA.tools.v013_s08_p3_entity_matching_quality_replay import generate


class TestV013S08P3EntityMatchingQualityReplay(unittest.TestCase):
    def test_replay_locks_entity_matching_quality_without_stage8_review_or_upload(self) -> None:
        generate()
        result = validate_v013_s08_p3_entity_matching_quality_replay()

        self.assertEqual(result["stage_id"], "S08")
        self.assertEqual(result["phase_id"], "S08-P3")
        self.assertEqual(result["phase_scope"], "v013_s08_p3_entity_matching_quality_replay_only")
        self.assertTrue(result["s08_p2_dependency_validated"])
        self.assertTrue(result["legacy_s08_p3_dependency_validated"])
        self.assertEqual(result["scenario_count"], 4)
        self.assertEqual(result["quality_case_count"], 4)
        self.assertEqual(result["manual_review_queue_count"], 3)
        self.assertEqual(result["entity_matching_report_count"], 1)
        self.assertEqual(
            set(result["quality_scenarios"]),
            {
                "same_project_name",
                "multiple_company_entities",
                "multiple_accounts",
                "multiple_periods",
            },
        )
        self.assertEqual(result["risk_summary"]["high"], 2)
        self.assertEqual(result["risk_summary"]["medium"], 1)
        self.assertEqual(result["risk_summary"]["low"], 1)
        self.assertEqual(result["auto_merge_allowed_for_review_queue_count"], 0)
        self.assertTrue(result["s08_p1_performed"])
        self.assertTrue(result["s08_p2_performed"])
        self.assertTrue(result["s08_p3_performed"])
        self.assertFalse(result["stage8_review_performed"])
        self.assertFalse(result["fact_layer_scope_included"])
        self.assertFalse(result["lineage_full_check_scope_included"])
        self.assertFalse(result["report_scope_included"])
        self.assertFalse(result["ui_scope_included"])
        self.assertFalse(result["external_connector_scope_included"])
        self.assertEqual(result["q5_calculation_baseline_allowed_count"], 0)
        self.assertEqual(result["formal_report_allowed_count"], 0)
        self.assertFalse(result["github_upload_performed"])
        self.assertTrue(result["github_upload_deferred_until_stage10_batch"])
        self.assertFalse(result["raw_dir_read_performed"])
        self.assertFalse(result["raw_dir_mutation_performed"])
        self.assertIn("Stage 8 review", result["next_required_step"])
        self.assertIn("Stages 1-10", result["next_required_step"])
        self.assertIn("separate run", result["next_required_step"])


if __name__ == "__main__":
    unittest.main()
