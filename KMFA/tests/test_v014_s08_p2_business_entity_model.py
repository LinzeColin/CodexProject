import unittest

from KMFA.tools.check_v014_s08_p2_business_entity_model import (
    validate_v014_s08_p2_business_entity_model,
)
from KMFA.tools.v014_s08_p2_business_entity_model import generate


class TestV014S08P2BusinessEntityModel(unittest.TestCase):
    def test_business_entity_model_locks_schema_only_boundaries(self) -> None:
        generate()
        result = validate_v014_s08_p2_business_entity_model()

        self.assertEqual(result["stage_id"], "S08")
        self.assertEqual(result["phase_id"], "S08-P2")
        self.assertEqual(result["phase_scope"], "v014_s08_p2_business_entity_model_only")
        self.assertTrue(result["s08_p1_dependency_validated"])
        self.assertTrue(result["legacy_s08_p2_dependency_validated"])
        self.assertEqual(result["business_entity_summary"]["required_entity_type_count"], 8)
        self.assertEqual(result["business_entity_summary"]["relationship_count"], 14)
        self.assertEqual(result["business_entity_summary"]["lifecycle_status_count"], 32)
        self.assertEqual(result["business_entity_summary"]["lifecycle_status_per_entity_count"], 4)
        self.assertTrue(result["business_entity_summary"]["relationship_graph_required_links_present"])
        self.assertTrue(result["entity_model_policy"]["entity_values_hash_ref_only"])
        self.assertTrue(result["entity_model_policy"]["relationship_values_schema_only"])
        self.assertTrue(result["entity_model_policy"]["lifecycle_values_status_only"])
        self.assertTrue(result["stage8_phase_progress"]["s08_p1_performed"])
        self.assertTrue(result["stage8_phase_progress"]["s08_p2_performed"])
        self.assertFalse(result["stage8_phase_progress"]["s08_p3_performed"])
        self.assertFalse(result["stage8_phase_progress"]["stage8_review_performed"])
        self.assertFalse(result["phase_boundaries"]["fact_layer_scope_included"])
        self.assertFalse(result["phase_boundaries"]["lineage_full_check_scope_included"])
        self.assertFalse(result["phase_boundaries"]["report_scope_included"])
        self.assertFalse(result["phase_boundaries"]["ui_scope_included"])
        self.assertEqual(result["release_state"]["current_go_no_go"], "NO_GO")
        self.assertFalse(result["release_state"]["formal_report_allowed"])
        self.assertFalse(result["release_state"]["business_execution_allowed"])
        self.assertFalse(result["github_upload"]["github_upload_performed"])
        self.assertTrue(result["github_upload"]["github_upload_deferred_until_v014_stage1_18_complete"])
        self.assertFalse(result["raw_data_boundary"]["raw_inbox_read_by_this_phase"])
        self.assertFalse(result["raw_data_boundary"]["raw_inbox_mutated_by_this_phase"])
        self.assertEqual(result["next_recommended_phase"], "S08-P3")
        self.assertIn("Stage 1-18", result["next_phase_instruction"])
        self.assertIn("separate run", result["next_phase_instruction"])


if __name__ == "__main__":
    unittest.main()
