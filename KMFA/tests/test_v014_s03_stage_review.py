import unittest

from KMFA.tools.check_v014_s03_stage_review import validate_v014_s03_stage_review


class TestV014S03StageReview(unittest.TestCase):
    def test_stage_review_closes_stage3_without_upload_or_s04(self) -> None:
        result = validate_v014_s03_stage_review()

        self.assertEqual(result["stage_id"], "S03")
        self.assertEqual(result["review_scope"], "v014_s03_stage_review_only")
        self.assertEqual(result["phase_count"], 3)
        self.assertEqual(result["phase_results"], {"S03-P1": "PASS", "S03-P2": "PASS", "S03-P3": "PASS"})
        self.assertTrue(result["stage_review_performed"])
        self.assertFalse(result["github_upload_performed"])
        self.assertFalse(result["s04_p1_started"])
        self.assertFalse(result["raw_value_matching_performed"])
        self.assertFalse(result["field_mapping_performed"])
        self.assertFalse(result["lineage_full_check_performed"])
        self.assertFalse(result["formal_report_performed"])
        self.assertEqual(result["open_review_finding_count"], 0)
        self.assertEqual(result["fixed_review_finding_count"], 0)
        self.assertEqual(result["stage_gate"]["public_raw_file_count"], 5)
        self.assertEqual(result["stage_gate"]["matrix_row_count"], 5)
        self.assertEqual(result["stage_gate"]["status_event_count"], 5)
        self.assertEqual(result["stage_gate"]["source_priority_record_count"], 5)
        self.assertEqual(result["stage_gate"]["source_priority_order_count"], 9)
        self.assertEqual(result["stage_gate"]["same_source_policy_event_count"], 1)
        self.assertEqual(result["stage_gate"]["cross_source_difference_queue_item_count"], 1)
        self.assertFalse(result["stage_gate"]["auto_selection_allowed"])
        self.assertEqual(result["release_state"]["current_data_quality_grade"], "Q2")
        self.assertEqual(result["release_state"]["current_report_grade"], "D")
        self.assertEqual(result["release_state"]["current_go_no_go"], "NO_GO")
        self.assertFalse(result["release_state"]["delivery_allowed"])
        self.assertFalse(result["release_state"]["github_main_upload_allowed"])
        self.assertFalse(result["raw_data_boundary"]["raw_inbox_read_by_this_review"])
        self.assertTrue(result["raw_data_boundary"]["s03_p1_authorized_read_only_inventory_performed"])
        self.assertFalse(result["raw_data_boundary"]["s03_p2_raw_read_performed"])
        self.assertFalse(result["raw_data_boundary"]["s03_p3_raw_read_performed"])
        self.assertEqual(result["next_recommended_phase"], "S04-P1")


if __name__ == "__main__":
    unittest.main()
