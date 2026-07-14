import unittest

from KMFA.tools.check_v014_s07_p3_redcircle_postponement import (
    validate_v014_s07_p3_redcircle_postponement,
)


class TestV014S07P3RedcirclePostponement(unittest.TestCase):
    def test_redcircle_postponement_is_public_safe_versioned_and_local_only(self) -> None:
        result = validate_v014_s07_p3_redcircle_postponement()

        self.assertEqual(result["stage_id"], "S07")
        self.assertEqual(result["phase_id"], "S07-P3")
        self.assertEqual(result["phase_scope"], "v014_s07_p3_redcircle_postponement_only")
        self.assertTrue(result["s06_stage_review_dependency_validated"])
        self.assertTrue(result["s07_p1_dependency_validated"])
        self.assertTrue(result["s07_p2_dependency_validated"])
        self.assertTrue(result["legacy_redcircle_postponement_validated"])
        self.assertEqual(result["redcircle_export_type_count"], 4)
        self.assertEqual(result["reserved_template_count"], 4)
        self.assertEqual(result["registry_source_count"], 4)
        self.assertEqual(result["template_contract_hash_count"], 4)
        self.assertEqual(result["source_private_ref_count"], 4)
        self.assertEqual(result["connector_policy_count"], 1)
        self.assertEqual(result["rollback_plan_count"], 4)
        self.assertEqual(result["automatic_connector_allowed_count"], 0)
        self.assertFalse(result["d15_automatic_connector_allowed"])
        self.assertEqual(result["read_only_required_count"], 4)
        self.assertEqual(result["hash_retention_required_count"], 4)
        self.assertEqual(result["rollback_plan_required_count"], 4)
        self.assertEqual(result["manual_approval_required_count"], 4)
        self.assertEqual(result["q4_human_confirmed_count"], 0)
        self.assertEqual(result["q5_calculation_baseline_allowed_count"], 0)
        self.assertEqual(result["formal_report_allowed_count"], 0)
        self.assertFalse(result["raw_inbox_read_performed"])
        self.assertFalse(result["raw_inbox_list_performed"])
        self.assertFalse(result["raw_inbox_stat_performed"])
        self.assertFalse(result["raw_inbox_hash_performed"])
        self.assertFalse(result["raw_inbox_mutation_performed"])
        self.assertFalse(result["business_field_value_parsing_performed"])
        self.assertFalse(result["source_header_plaintext_committed"])
        self.assertFalse(result["field_plaintext_committed"])
        self.assertTrue(result["s07_p3_performed"])
        self.assertFalse(result["s07_p1_performed"])
        self.assertFalse(result["s07_p2_performed"])
        self.assertFalse(result["stage7_review_performed"])
        self.assertFalse(result["s08_p1_performed"])
        self.assertFalse(result["github_upload_performed"])
        self.assertFalse(result["delivery_allowed"])
        self.assertFalse(result["formal_report_allowed"])
        self.assertEqual(result["current_data_quality_grade"], "Q4")
        self.assertEqual(result["current_report_grade"], "D")
        self.assertEqual(result["release_permission"], "blocked")
        self.assertEqual(result["next_recommended_phase"], "S07_STAGE_REVIEW")
        self.assertIn("Stage 7 review", result["next_phase_instruction"])
        self.assertIn("Stage 1-18", result["next_phase_instruction"])


if __name__ == "__main__":
    unittest.main()
