import unittest

from KMFA.tools.check_v013_s06_p1_zero_delta_replay import validate_v013_s06_p1_zero_delta_replay


class V013S06P1ZeroDeltaReplayTests(unittest.TestCase):
    def test_v013_s06_p1_zero_delta_replay_gate(self) -> None:
        result = validate_v013_s06_p1_zero_delta_replay()

        self.assertEqual(result["phase_id"], "S06-P1")
        self.assertEqual(result["phase_scope"], "v013_s06_p1_zero_delta_replay_only")
        self.assertTrue(result["s05_stage_review_dependency_validated"])
        self.assertEqual(result["pass_fixture_field_comparison_count"], 8)
        self.assertTrue(result["zero_delta_passed_for_public_safe_fixture"])
        self.assertEqual(result["pass_fixture_mismatch_count"], 0)
        self.assertTrue(result["one_cent_mismatch_detected"])
        self.assertEqual(result["minimum_fail_difference_cents"], 1)
        self.assertEqual(result["mismatch_fixture_mismatch_count"], 1)
        self.assertTrue(result["mismatch_report_generated"])
        self.assertFalse(result["metadata_quality_written"])
        self.assertFalse(result["difference_queue_created"])
        self.assertFalse(result["stage6_review_performed"])
        self.assertFalse(result["github_upload_performed"])
        self.assertFalse(result["raw_dir_read_performed"])
        self.assertFalse(result["raw_dir_mutation_performed"])
        self.assertFalse(result["formal_report_allowed"])
        self.assertFalse(result["business_execution_allowed"])


if __name__ == "__main__":
    unittest.main()
