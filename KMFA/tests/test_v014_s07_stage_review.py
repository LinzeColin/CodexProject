import unittest

from KMFA.tools.check_v014_s07_stage_review import validate_v014_s07_stage_review


class TestV014S07StageReview(unittest.TestCase):
    def test_stage_review_closes_stage7_without_upload_or_s08(self) -> None:
        result = validate_v014_s07_stage_review()

        self.assertEqual(result["stage_id"], "S07")
        self.assertEqual(result["review_scope"], "v014_s07_stage_review_only")
        self.assertEqual(result["phase_count"], 3)
        self.assertEqual(result["phase_results"], {"S07-P1": "PASS", "S07-P2": "PASS", "S07-P3": "PASS"})
        self.assertTrue(result["stage_review_performed"])
        self.assertFalse(result["s08_p1_performed"])
        self.assertFalse(result["github_upload_performed"])
        self.assertFalse(result["app_reinstall_performed"])
        self.assertFalse(result["raw_content_matching_performed"])
        self.assertFalse(result["lineage_full_check_performed"])
        self.assertFalse(result["formal_report_performed"])
        self.assertEqual(result["open_review_finding_count"], 0)
        self.assertEqual(result["fixed_review_finding_count"], 1)
        self.assertEqual(result["review_findings"][0]["status"], "fixed")
        self.assertEqual(result["stage_gate"]["finance_field_candidate_count"], 45)
        self.assertEqual(result["stage_gate"]["wps_field_mapping_count"], 20)
        self.assertEqual(result["stage_gate"]["redcircle_reserved_template_count"], 4)
        self.assertEqual(result["stage_gate"]["redcircle_rollback_plan_count"], 4)
        self.assertEqual(result["stage_gate"]["redcircle_automatic_connector_allowed_count"], 0)
        self.assertFalse(result["stage_gate"]["redcircle_d15_automatic_connector_allowed"])
        self.assertEqual(result["stage_gate"]["total_public_safe_source_registry_count"], 17)
        self.assertEqual(result["stage_gate"]["total_structural_mapping_count"], 65)
        self.assertEqual(result["stage_gate"]["q4_human_confirmed_count"], 0)
        self.assertEqual(result["stage_gate"]["q5_calculation_baseline_allowed_count"], 0)
        self.assertEqual(result["stage_gate"]["formal_report_allowed_count"], 0)
        self.assertEqual(result["release_state"]["current_data_quality_grade"], "Q4")
        self.assertEqual(result["release_state"]["current_report_grade"], "D")
        self.assertEqual(result["release_state"]["current_go_no_go"], "NO_GO")
        self.assertFalse(result["release_state"]["delivery_allowed"])
        self.assertFalse(result["release_state"]["github_main_upload_allowed"])
        self.assertFalse(result["raw_data_boundary"]["raw_inbox_read_by_this_review"])
        self.assertFalse(result["raw_data_boundary"]["raw_inbox_listed_by_this_review"])
        self.assertFalse(result["raw_data_boundary"]["raw_inbox_hashed_by_this_review"])
        self.assertFalse(result["raw_data_boundary"]["raw_inbox_mutated_by_this_review"])
        self.assertEqual(result["next_recommended_phase"], "S08-P1")
        self.assertIn("Stage 1-18", result["next_phase_instruction"])


if __name__ == "__main__":
    unittest.main()
