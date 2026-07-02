import unittest

from KMFA.tools.check_v013_s02_p3_data_quality_error_gate import (
    validate_v013_s02_p3_data_quality_error_gate,
)


class TestV013S02P3DataQualityErrorGate(unittest.TestCase):
    def test_quality_and_report_gate_blocks_release_until_matching_and_lineage(self) -> None:
        result = validate_v013_s02_p3_data_quality_error_gate()

        self.assertEqual(result["stage_id"], "S02")
        self.assertEqual(result["phase_id"], "S02-P3")
        self.assertEqual(result["task_id"], "KMFA-V013-S02-P3-DATA-QUALITY-ERROR-GATE-20260702")
        self.assertTrue(result["s02_p1_dependency_validated"])
        self.assertTrue(result["s02_p2_dependency_validated"])
        self.assertEqual(result["quality_grades"], ["Q0", "Q1", "Q2", "Q3", "Q4", "Q5"])
        self.assertEqual(result["report_grades"], ["A", "B", "C", "D"])
        self.assertEqual(result["quality_to_report_gate"]["Q2"]["maximum_report_grade"], "D")
        self.assertEqual(result["quality_to_report_gate"]["Q2"]["release_permission"], "blocked")
        self.assertEqual(result["current_data_quality_grade"], "Q2")
        self.assertEqual(result["current_report_grade"], "D")
        self.assertEqual(result["release_permission"], "blocked")
        self.assertFalse(result["formal_report_allowed"])
        self.assertFalse(result["business_decision_basis_allowed"])
        self.assertFalse(result["data_matches_raw_claim_allowed"])
        self.assertFalse(result["raw_value_matching_performed"])
        self.assertFalse(result["raw_business_value_extraction_performed"])
        self.assertFalse(result["raw_dir_mutation_performed"])
        self.assertIn("raw_value_matching_blocked_authorized_mapping_required", result["hard_blocks"])
        self.assertIn("owner_authorized_semantic_mapping_missing", result["hard_blocks"])
        self.assertIn("zero_delta_not_performed", result["hard_blocks"])
        self.assertIn("lineage_full_check_not_performed", result["hard_blocks"])
        self.assertFalse(result["stage_review_performed"])
        self.assertFalse(result["github_upload_performed"])
        self.assertFalse(result["delivery_allowed"])
        self.assertIn("Stage 2 review", result["next_required_step"])


if __name__ == "__main__":
    unittest.main()
