import unittest

from KMFA.tools.check_v014_s06_stage_review import validate_v014_s06_stage_review


class TestV014S06StageReview(unittest.TestCase):
    def test_stage_review_closes_stage6_without_upload_or_s07(self) -> None:
        result = validate_v014_s06_stage_review()

        self.assertEqual(result["stage_id"], "S06")
        self.assertEqual(result["review_scope"], "v014_s06_stage_review_only")
        self.assertEqual(result["phase_count"], 3)
        self.assertEqual(result["phase_results"], {"S06-P1": "PASS", "S06-P2": "PASS", "S06-P3": "PASS"})
        self.assertTrue(result["stage_review_performed"])
        self.assertFalse(result["github_upload_performed"])
        self.assertFalse(result["s07_p1_started"])
        self.assertFalse(result["raw_content_matching_performed"])
        self.assertFalse(result["lineage_full_check_performed"])
        self.assertFalse(result["formal_report_performed"])
        self.assertEqual(result["open_review_finding_count"], 0)
        self.assertEqual(result["fixed_review_finding_count"], 1)
        self.assertEqual(result["review_findings"][0]["status"], "fixed")
        self.assertEqual(result["stage_gate"]["pass_fixture_field_comparison_count"], 8)
        self.assertTrue(result["stage_gate"]["one_cent_mismatch_detected"])
        self.assertEqual(result["stage_gate"]["queue_item_count"], 1)
        self.assertEqual(result["stage_gate"]["minimum_queue_difference_cents"], 1)
        self.assertFalse(result["stage_gate"]["difference_closed"])
        self.assertTrue(result["stage_gate"]["metadata_quality_written"])
        self.assertEqual(result["stage_gate"]["metadata_zero_delta_records_written"], 1)
        self.assertEqual(result["stage_gate"]["metadata_data_quality_records_written"], 2)
        self.assertEqual(result["stage_gate"]["metadata_source_difference_records_written"], 1)
        self.assertEqual(result["stage_gate"]["metadata_mismatch_rows_written"], 1)
        self.assertEqual(result["stage_gate"]["project_status_count"], 2)
        self.assertEqual(result["stage_gate"]["blocked_project_status_count"], 2)
        self.assertEqual(result["stage_gate"]["q5_allowed_count"], 0)
        self.assertEqual(result["stage_gate"]["report_grade_a_allowed_count"], 0)
        self.assertFalse(result["stage_gate"]["zero_delta_passed"])
        self.assertIn("zero_delta_failed", result["stage_gate"]["hard_blocks"])
        self.assertIn("unresolved_critical_difference", result["stage_gate"]["hard_blocks"])
        self.assertEqual(result["release_state"]["current_data_quality_grade"], "Q4")
        self.assertEqual(result["release_state"]["current_report_grade"], "D")
        self.assertEqual(result["release_state"]["current_go_no_go"], "NO_GO")
        self.assertFalse(result["release_state"]["delivery_allowed"])
        self.assertFalse(result["release_state"]["github_main_upload_allowed"])
        self.assertFalse(result["raw_data_boundary"]["raw_inbox_read_by_this_review"])
        self.assertFalse(result["raw_data_boundary"]["raw_inbox_listed_by_this_review"])
        self.assertFalse(result["raw_data_boundary"]["raw_inbox_hashed_by_this_review"])
        self.assertFalse(result["raw_data_boundary"]["raw_inbox_mutated_by_this_review"])
        self.assertEqual(result["next_recommended_phase"], "S07-P1")
        self.assertIn("Stage 1-18", result["next_phase_instruction"])


if __name__ == "__main__":
    unittest.main()
