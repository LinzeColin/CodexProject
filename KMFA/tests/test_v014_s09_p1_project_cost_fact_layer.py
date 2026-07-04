import unittest

from KMFA.tools.check_v014_s09_p1_project_cost_fact_layer import (
    validate_v014_s09_p1_project_cost_fact_layer,
)
from KMFA.tools.v014_s09_p1_project_cost_fact_layer import generate


class TestV014S09P1ProjectCostFactLayer(unittest.TestCase):
    def test_project_cost_fact_layer_stays_public_safe_without_later_phase_or_upload(self) -> None:
        generate()
        result = validate_v014_s09_p1_project_cost_fact_layer()

        summary = result["project_cost_fact_layer_summary"]
        policy = result["fact_layer_policy"]
        progress = result["stage9_phase_progress"]

        self.assertEqual(result["stage_id"], "S09")
        self.assertEqual(result["phase_id"], "S09-P1")
        self.assertEqual(result["phase_scope"], "v014_s09_p1_project_cost_fact_layer_only")
        self.assertEqual(summary["required_metric_count"], 6)
        self.assertEqual(
            summary["required_metrics"],
            ["revenue", "contract_amount", "invoice_amount", "collection_amount", "cost_total", "cost_category"],
        )
        self.assertEqual(summary["cost_category_count"], 9)
        self.assertEqual(
            summary["required_cost_categories"],
            ["labor", "material", "machinery", "subcontract", "transport", "travel", "tax", "management_fee", "interest"],
        )
        self.assertEqual(summary["fact_record_count"], 4)
        self.assertEqual(summary["unallocated_pool_count"], 9)
        self.assertEqual(summary["authority_locked_field_count"], 40)
        self.assertEqual(summary["authority_excluded_field_count"], 5)
        self.assertEqual(summary["business_entity_type_count"], 8)
        self.assertEqual(summary["project_identity_profile_count"], 4)
        self.assertEqual(summary["manual_review_queue_count"], 3)
        self.assertEqual(summary["unresolved_difference_count"], 1)
        self.assertEqual(summary["zero_delta_fail_count"], 1)
        self.assertEqual(summary["blocked_quality_result_count"], 2)
        self.assertTrue(summary["formal_calculation_blocked"])
        self.assertFalse(policy["formal_calculation_allowed"])
        self.assertEqual(policy["metric_hash_ref_count"], 24)
        self.assertEqual(policy["metric_private_ref_count"], 24)
        self.assertEqual(policy["cost_category_hash_ref_count"], 36)
        self.assertEqual(policy["cost_category_private_ref_count"], 36)
        self.assertEqual(policy["pending_pool_assignment_count"], 9)
        self.assertTrue(progress["s09_p1_performed"])
        self.assertFalse(progress["s09_p2_performed"])
        self.assertFalse(progress["s09_p3_performed"])
        self.assertFalse(progress["stage9_review_performed"])
        self.assertFalse(result["github_upload"]["github_upload_performed"])
        self.assertTrue(result["github_upload"]["github_upload_deferred_until_v014_stage1_18_complete"])
        self.assertFalse(result["raw_data_boundary"]["raw_inbox_read_by_this_phase"])
        self.assertFalse(result["raw_data_boundary"]["raw_inbox_mutated_by_this_phase"])
        self.assertEqual(result["next_recommended_phase"], "S09-P2")
        self.assertIn("Stage 1-18", result["next_phase_instruction"])


if __name__ == "__main__":
    unittest.main()
