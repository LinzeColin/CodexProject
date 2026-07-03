import unittest

from KMFA.tools.check_v014_s02_p3_quality_gate import validate_v014_s02_p3_quality_gate


class TestV014S02P3QualityGate(unittest.TestCase):
    def test_quality_gate_phase_is_closed_without_raw_read_or_upload(self) -> None:
        result = validate_v014_s02_p3_quality_gate()

        self.assertEqual(result["stage_id"], "S02")
        self.assertEqual(result["phase_id"], "S02-P3")
        self.assertTrue(result["phase_scope"]["quality_gate_policy_only"])
        self.assertFalse(result["phase_scope"]["stage2_review_performed"])
        self.assertFalse(result["phase_scope"]["github_upload_performed"])
        self.assertFalse(result["phase_scope"]["raw_inventory_performed"])
        self.assertFalse(result["phase_scope"]["raw_value_matching_performed"])
        self.assertEqual(result["quality_gate"]["allowed_quality_grade_count"], 6)
        self.assertEqual(result["quality_gate"]["allowed_report_grade_count"], 4)
        self.assertEqual(result["quality_gate"]["quality_to_report_gate_count"], 6)
        self.assertEqual(result["quality_gate"]["minimum_formal_internal_report_quality_grade"], "Q5")
        self.assertTrue(result["quality_gate"]["grade_a_zero_delta_required"])
        self.assertTrue(result["quality_gate"]["grade_a_critical_differences_closed_required"])
        self.assertTrue(result["quality_gate"]["grade_a_human_confirmation_required"])
        self.assertEqual(result["quality_gate"]["missing_gate_evidence_policy"], "block_release")
        self.assertFalse(result["quality_gate"]["runtime_quality_result_generated_by_this_phase"])
        self.assertFalse(result["quality_gate"]["runtime_report_generated_by_this_phase"])
        self.assertFalse(result["raw_data_boundary"]["raw_inbox_read_by_this_phase"])
        self.assertFalse(result["raw_data_boundary"]["raw_inbox_listed_by_this_phase"])
        self.assertFalse(result["raw_data_boundary"]["raw_inbox_inventory_by_this_phase"])
        self.assertFalse(result["release_state"]["delivery_allowed"])
        self.assertFalse(result["release_state"]["formal_report_allowed"])
        self.assertFalse(result["release_state"]["github_main_upload_allowed"])
        self.assertEqual(result["release_state"]["current_data_quality_grade"], "Q0")
        self.assertEqual(result["release_state"]["current_report_grade"], "D")
        self.assertEqual(result["release_state"]["current_go_no_go"], "NO_GO")
        self.assertEqual(result["next_recommended_phase"], "S02-STAGE-REVIEW")


if __name__ == "__main__":
    unittest.main()
