import unittest

from KMFA.tools.check_v013_s04_p1_amount_precision import (
    validate_v013_s04_p1_amount_precision,
)


class TestV013S04P1AmountPrecision(unittest.TestCase):
    def test_amount_precision_replay_locks_no_float_and_public_safe_boundaries(self) -> None:
        result = validate_v013_s04_p1_amount_precision()

        self.assertEqual(result["stage_id"], "S04")
        self.assertEqual(result["phase_id"], "S04-P1")
        self.assertEqual(result["phase_scope"], "v013_s04_p1_amount_precision_only")
        self.assertTrue(result["s03_stage_review_dependency_validated"])
        self.assertTrue(result["amount_tools_dependency_validated"])
        self.assertTrue(result["no_float_dependency_validated"])
        self.assertEqual(result["amount_case_count"], 9)
        self.assertEqual(result["amount_rejection_count"], 9)
        self.assertEqual(result["scan_fixture_forbidden_float_findings"], 3)
        self.assertTrue(result["repository_no_float_scan_passed"])
        self.assertFalse(result["raw_dir_read_performed"])
        self.assertFalse(result["raw_dir_mutation_performed"])
        self.assertFalse(result["raw_layer_write_allowed"])
        self.assertFalse(result["raw_source_mutation_allowed"])
        self.assertFalse(result["raw_value_matching_performed"])
        self.assertFalse(result["stage4_review_performed"])
        self.assertFalse(result["github_upload_performed"])
        self.assertFalse(result["delivery_allowed"])
        self.assertEqual(result["current_data_quality_grade"], "Q2")
        self.assertEqual(result["current_report_grade"], "D")
        self.assertEqual(result["release_permission"], "blocked")
        self.assertIn("S04-P2", result["next_required_step"])


if __name__ == "__main__":
    unittest.main()
