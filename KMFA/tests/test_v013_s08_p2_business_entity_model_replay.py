import unittest

from KMFA.tools.check_v013_s08_p2_business_entity_model_replay import (
    validate_v013_s08_p2_business_entity_model_replay,
)
from KMFA.tools.v013_s08_p2_business_entity_model_replay import generate


class TestV013S08P2BusinessEntityModelReplay(unittest.TestCase):
    def test_replay_locks_business_entity_model_without_stage8_review_or_upload(self) -> None:
        generate()
        result = validate_v013_s08_p2_business_entity_model_replay()

        self.assertEqual(result["stage_id"], "S08")
        self.assertEqual(result["phase_id"], "S08-P2")
        self.assertEqual(result["phase_scope"], "v013_s08_p2_business_entity_model_replay_only")
        self.assertTrue(result["s08_p1_dependency_validated"])
        self.assertTrue(result["legacy_s08_p2_dependency_validated"])
        self.assertEqual(result["required_entity_type_count"], 8)
        self.assertEqual(result["relationship_count"], 14)
        self.assertEqual(result["lifecycle_status_count"], 32)
        self.assertEqual(result["lifecycle_status_per_entity_count"], 4)
        self.assertEqual(
            set(result["required_entity_types"]),
            {
                "customer",
                "contract",
                "project",
                "cost_record",
                "invoice",
                "collection",
                "receivable",
                "tax_evidence",
            },
        )
        self.assertTrue(result["s08_p1_performed"])
        self.assertTrue(result["s08_p2_performed"])
        self.assertFalse(result["s08_p3_performed"])
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
        self.assertIn("S08-P3", result["next_required_step"])
        self.assertIn("Stages 1-10", result["next_required_step"])
        self.assertIn("separate run", result["next_required_step"])


if __name__ == "__main__":
    unittest.main()
