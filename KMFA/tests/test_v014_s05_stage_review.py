import unittest

from KMFA.tools.check_v014_s05_stage_review import validate_v014_s05_stage_review


class TestV014S05StageReview(unittest.TestCase):
    def test_stage_review_closes_stage5_without_upload_or_s06(self) -> None:
        result = validate_v014_s05_stage_review()

        self.assertEqual(result["stage_id"], "S05")
        self.assertEqual(result["review_scope"], "v014_s05_stage_review_only")
        self.assertEqual(result["phase_count"], 3)
        self.assertEqual(result["phase_results"], {"S05-P1": "PASS", "S05-P2": "PASS", "S05-P3": "PASS"})
        self.assertTrue(result["stage_review_performed"])
        self.assertFalse(result["github_upload_performed"])
        self.assertFalse(result["s06_p1_started"])
        self.assertFalse(result["raw_value_matching_performed"])
        self.assertFalse(result["zero_delta_validation_performed"])
        self.assertFalse(result["lineage_full_check_performed"])
        self.assertFalse(result["formal_report_performed"])
        self.assertEqual(result["open_review_finding_count"], 0)
        self.assertEqual(result["fixed_review_finding_count"], 0)
        self.assertEqual(result["stage_gate"]["a0_total_files"], 9)
        self.assertEqual(result["stage_gate"]["a0_pdf_files"], 8)
        self.assertEqual(result["stage_gate"]["a0_excel_files"], 1)
        self.assertEqual(result["stage_gate"]["field_contract_count"], 5)
        self.assertEqual(result["stage_gate"]["field_candidate_count"], 45)
        self.assertEqual(result["stage_gate"]["pdf_field_candidate_count"], 40)
        self.assertEqual(result["stage_gate"]["excel_field_candidate_count"], 5)
        self.assertEqual(result["stage_gate"]["q5_calculation_baseline_locked_count"], 40)
        self.assertEqual(result["stage_gate"]["excluded_cross_source_support_only_count"], 5)
        self.assertEqual(result["stage_gate"]["q4_human_confirmed_count"], 40)
        self.assertEqual(result["stage_gate"]["q5_full_quality_grade_allowed_count"], 0)
        self.assertEqual(result["stage_gate"]["zero_delta_validated_count"], 0)
        self.assertEqual(result["stage_gate"]["lineage_full_check_completed_count"], 0)
        self.assertEqual(result["stage_gate"]["formal_report_allowed_count"], 0)
        self.assertEqual(result["release_state"]["current_data_quality_grade"], "Q4")
        self.assertEqual(result["release_state"]["current_report_grade"], "D")
        self.assertEqual(result["release_state"]["current_go_no_go"], "NO_GO")
        self.assertFalse(result["release_state"]["delivery_allowed"])
        self.assertFalse(result["release_state"]["github_main_upload_allowed"])
        self.assertFalse(result["raw_data_boundary"]["raw_inbox_read_by_this_review"])
        self.assertFalse(result["raw_data_boundary"]["raw_inbox_listed_by_this_review"])
        self.assertFalse(result["raw_data_boundary"]["raw_inbox_hashed_by_this_review"])
        self.assertFalse(result["raw_data_boundary"]["raw_inbox_mutated_by_stage5"])
        self.assertTrue(result["raw_data_boundary"]["s05_p1_raw_read_list_stat_hash_authorized"])
        self.assertEqual(result["next_recommended_phase"], "S06-P1")
        self.assertIn("Stage 1-18", result["next_phase_instruction"])


if __name__ == "__main__":
    unittest.main()
