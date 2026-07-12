import unittest

from KMFA.tools.check_v014_s02_stage_review import validate_v014_s02_stage_review


class TestV014S02StageReview(unittest.TestCase):
    def test_stage_review_closes_stage2_without_upload_or_s03(self) -> None:
        result = validate_v014_s02_stage_review()

        self.assertEqual(result["stage_id"], "S02")
        self.assertEqual(result["review_scope"], "v014_s02_stage_review_only")
        self.assertEqual(result["phase_count"], 3)
        self.assertEqual(result["phase_results"], {"S02-P1": "PASS", "S02-P2": "PASS", "S02-P3": "PASS"})
        self.assertTrue(result["stage_review_performed"])
        self.assertFalse(result["github_upload_performed"])
        self.assertFalse(result["s03_p1_started"])
        self.assertFalse(result["raw_inventory_performed"])
        self.assertFalse(result["raw_value_matching_performed"])
        self.assertFalse(result["lineage_full_check_performed"])
        self.assertFalse(result["formal_report_performed"])
        self.assertEqual(result["open_review_finding_count"], 0)
        self.assertEqual(result["fixed_review_finding_count"], 0)
        self.assertEqual(result["stage_gate"]["metadata_directory_count"], 7)
        self.assertEqual(result["stage_gate"]["metadata_identifier_count"], 5)
        self.assertEqual(result["stage_gate"]["raw_manifest_immutable_field_count"], 5)
        self.assertEqual(result["stage_gate"]["derived_allowed_action_count"], 4)
        self.assertEqual(result["stage_gate"]["control_event_type_count"], 6)
        self.assertEqual(result["stage_gate"]["quality_grade_count"], 6)
        self.assertEqual(result["stage_gate"]["report_grade_count"], 4)
        self.assertEqual(result["stage_gate"]["quality_to_report_gate_count"], 6)
        self.assertEqual(result["release_state"]["current_data_quality_grade"], "Q0")
        self.assertEqual(result["release_state"]["current_report_grade"], "D")
        self.assertEqual(result["release_state"]["current_go_no_go"], "NO_GO")
        self.assertFalse(result["release_state"]["delivery_allowed"])
        self.assertFalse(result["release_state"]["github_main_upload_allowed"])
        self.assertFalse(result["raw_data_boundary"]["raw_inbox_read_by_this_review"])
        self.assertFalse(result["raw_data_boundary"]["raw_inbox_listed_by_this_review"])
        self.assertFalse(result["raw_data_boundary"]["raw_inbox_inventory_by_this_review"])
        self.assertEqual(result["next_recommended_phase"], "S03-P1")


if __name__ == "__main__":
    unittest.main()
