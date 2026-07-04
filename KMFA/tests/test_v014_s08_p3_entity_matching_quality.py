import unittest

from KMFA.tools.check_v014_s08_p3_entity_matching_quality import (
    validate_v014_s08_p3_entity_matching_quality,
)
from KMFA.tools.v014_s08_p3_entity_matching_quality import generate


class TestV014S08P3EntityMatchingQuality(unittest.TestCase):
    def test_entity_matching_quality_locks_review_queue_without_stage_review_or_upload(self) -> None:
        generate()
        result = validate_v014_s08_p3_entity_matching_quality()

        self.assertEqual(result["stage_id"], "S08")
        self.assertEqual(result["phase_id"], "S08-P3")
        self.assertEqual(result["phase_scope"], "v014_s08_p3_entity_matching_quality_only")
        self.assertTrue(result["s08_p2_dependency_validated"])
        self.assertTrue(result["legacy_s08_p3_dependency_validated"])
        self.assertEqual(result["entity_matching_quality_summary"]["scenario_count"], 4)
        self.assertEqual(result["entity_matching_quality_summary"]["quality_case_count"], 4)
        self.assertEqual(result["entity_matching_quality_summary"]["manual_review_queue_count"], 3)
        self.assertEqual(result["entity_matching_quality_summary"]["manual_review_case_count"], 3)
        self.assertEqual(result["entity_matching_quality_summary"]["risk_summary"], {"high": 2, "medium": 1, "low": 1})
        self.assertEqual(result["entity_matching_quality_summary"]["auto_merge_allowed_for_review_queue_count"], 0)
        self.assertTrue(result["entity_matching_quality_policy"]["medium_high_risk_requires_manual_review"])
        self.assertFalse(result["entity_matching_quality_policy"]["manual_review_queue_auto_merge_allowed"])
        self.assertTrue(result["entity_matching_quality_policy"]["entity_matching_values_hash_ref_only"])
        self.assertFalse(result["entity_matching_quality_policy"]["quality_report_is_formal_report"])
        self.assertTrue(result["stage8_phase_progress"]["s08_p1_performed"])
        self.assertTrue(result["stage8_phase_progress"]["s08_p2_performed"])
        self.assertTrue(result["stage8_phase_progress"]["s08_p3_performed"])
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
        self.assertEqual(result["next_recommended_phase"], "Stage 8 review")
        self.assertIn("Stage 1-18", result["next_phase_instruction"])
        self.assertIn("separate run", result["next_phase_instruction"])


if __name__ == "__main__":
    unittest.main()
