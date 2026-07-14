import unittest

from KMFA.tools.check_v014_s06_p1_zero_delta_validator import validate_v014_s06_p1_zero_delta_validator


class V014S06P1ZeroDeltaValidatorTests(unittest.TestCase):
    def test_v014_s06_p1_zero_delta_validator_gate(self) -> None:
        result = validate_v014_s06_p1_zero_delta_validator()

        self.assertEqual(result["phase_id"], "S06-P1")
        self.assertEqual(result["phase_scope"], "v014_s06_p1_zero_delta_validator_only")
        self.assertTrue(result["s05_stage_review_dependency_validated"])
        self.assertEqual(result["pass_fixture_field_comparison_count"], 8)
        self.assertTrue(result["zero_delta_passed_for_public_safe_fixture"])
        self.assertEqual(result["pass_fixture_mismatch_count"], 0)
        self.assertTrue(result["one_cent_mismatch_detected"])
        self.assertEqual(result["minimum_fail_difference_cents"], 1)
        self.assertEqual(result["mismatch_fixture_mismatch_count"], 1)
        self.assertTrue(result["mismatch_report_generated"])
        self.assertTrue(result["mismatch_report_contains_required_columns"])
        self.assertFalse(result["difference_queue_created"])
        self.assertFalse(result["metadata_quality_written"])
        self.assertFalse(result["s06_p2_started"])
        self.assertFalse(result["s06_p3_started"])
        self.assertFalse(result["stage6_review_performed"])
        self.assertFalse(result["github_upload_performed"])
        self.assertFalse(result["raw_data_boundary"]["raw_inbox_read_by_this_phase"])
        self.assertFalse(result["raw_data_boundary"]["raw_inbox_mutated_by_this_phase"])
        self.assertFalse(result["release_state"]["formal_report_allowed"])
        self.assertFalse(result["business_execution_performed"])
        self.assertFalse(result["release_state"]["business_execution_allowed"])


if __name__ == "__main__":
    unittest.main()
