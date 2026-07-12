import unittest

from KMFA.tools.check_v014_s04_stage_review import validate_v014_s04_stage_review


class TestV014S04StageReview(unittest.TestCase):
    def test_stage_review_closes_stage4_without_upload_or_s05(self) -> None:
        result = validate_v014_s04_stage_review()

        self.assertEqual(result["stage_id"], "S04")
        self.assertEqual(result["review_scope"], "v014_s04_stage_review_only")
        self.assertEqual(result["phase_count"], 3)
        self.assertEqual(result["phase_results"], {"S04-P1": "PASS", "S04-P2": "PASS", "S04-P3": "PASS"})
        self.assertTrue(result["stage_review_performed"])
        self.assertFalse(result["github_upload_performed"])
        self.assertFalse(result["s05_p1_started"])
        self.assertFalse(result["raw_value_matching_performed"])
        self.assertFalse(result["field_mapping_beyond_s04_performed"])
        self.assertFalse(result["lineage_full_check_performed"])
        self.assertFalse(result["formal_report_performed"])
        self.assertEqual(result["open_review_finding_count"], 0)
        self.assertEqual(result["fixed_review_finding_count"], 0)
        self.assertEqual(result["stage_gate"]["amount_case_count"], 9)
        self.assertEqual(result["stage_gate"]["amount_rejection_count"], 9)
        self.assertTrue(result["stage_gate"]["repository_no_float_scan_passed"])
        self.assertEqual(result["stage_gate"]["canonical_field_count"], 6)
        self.assertEqual(result["stage_gate"]["alias_dictionary_row_count"], 32)
        self.assertEqual(result["stage_gate"]["field_quality_status_count"], 5)
        self.assertEqual(result["stage_gate"]["synthetic_boundary_case_total"], 22)
        self.assertEqual(result["stage_gate"]["synthetic_boundary_case_passed"], 22)
        self.assertEqual(result["stage_gate"]["synthetic_boundary_case_failed"], 0)
        self.assertEqual(result["stage_gate"]["amount_boundary_case_count"], 11)
        self.assertEqual(result["stage_gate"]["date_period_boundary_case_count"], 11)
        self.assertTrue(result["stage_gate"]["json_report_generated"])
        self.assertTrue(result["stage_gate"]["markdown_report_generated"])
        self.assertEqual(result["release_state"]["current_data_quality_grade"], "Q2")
        self.assertEqual(result["release_state"]["current_report_grade"], "D")
        self.assertEqual(result["release_state"]["current_go_no_go"], "NO_GO")
        self.assertFalse(result["release_state"]["delivery_allowed"])
        self.assertFalse(result["release_state"]["github_main_upload_allowed"])
        self.assertFalse(result["raw_data_boundary"]["raw_inbox_read_by_this_review"])
        self.assertFalse(result["raw_data_boundary"]["raw_inbox_listed_by_this_review"])
        self.assertFalse(result["raw_data_boundary"]["raw_inbox_hashed_by_this_review"])
        self.assertFalse(result["raw_data_boundary"]["raw_inbox_mutated_by_stage4"])
        self.assertEqual(result["next_recommended_phase"], "S05-P1")
        self.assertIn("Stage 1-18", result["next_phase_instruction"])


if __name__ == "__main__":
    unittest.main()
