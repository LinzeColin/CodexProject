import unittest

from KMFA.tools.check_v013_s09_p1_project_cost_fact_layer_replay import (
    validate_v013_s09_p1_project_cost_fact_layer_replay,
)
from KMFA.tools.v013_s09_p1_project_cost_fact_layer_replay import generate


class TestV013S09P1ProjectCostFactLayerReplay(unittest.TestCase):
    def test_replay_locks_project_cost_fact_layer_without_later_phase_or_upload(self) -> None:
        generate()
        result = validate_v013_s09_p1_project_cost_fact_layer_replay()

        self.assertEqual(result["stage_id"], "S09")
        self.assertEqual(result["phase_id"], "S09-P1")
        self.assertEqual(result["phase_scope"], "v013_s09_p1_project_cost_fact_layer_replay_only")
        self.assertEqual(result["required_metric_count"], 6)
        self.assertEqual(result["cost_category_count"], 9)
        self.assertEqual(result["fact_record_count"], 4)
        self.assertEqual(result["unallocated_pool_count"], 9)
        self.assertEqual(result["authority_locked_field_count"], 40)
        self.assertEqual(result["authority_excluded_field_count"], 5)
        self.assertEqual(result["business_entity_type_count"], 8)
        self.assertEqual(result["manual_review_queue_count"], 3)
        self.assertEqual(result["unresolved_difference_count"], 1)
        self.assertEqual(result["zero_delta_fail_count"], 1)
        self.assertEqual(result["blocked_quality_result_count"], 2)
        self.assertFalse(result["formal_calculation_allowed"])
        self.assertFalse(result["formal_report_allowed"])
        self.assertFalse(result["s09_p2_performed"])
        self.assertFalse(result["s09_p3_performed"])
        self.assertFalse(result["stage9_review_performed"])
        self.assertFalse(result["github_upload_performed"])
        self.assertTrue(result["github_upload_deferred_until_stage10_batch"])
        self.assertFalse(result["raw_dir_read_performed"])
        self.assertFalse(result["raw_dir_mutation_performed"])
        self.assertIn("S09-P2", result["next_required_step"])
        self.assertIn("Stages 1-10", result["next_required_step"])
        self.assertIn("separate run", result["next_required_step"])


if __name__ == "__main__":
    unittest.main()
