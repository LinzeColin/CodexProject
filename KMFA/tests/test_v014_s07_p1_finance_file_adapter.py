import unittest

from KMFA.tools.check_v014_s07_p1_finance_file_adapter import (
    validate_v014_s07_p1_finance_file_adapter,
)


class TestV014S07P1FinanceFileAdapter(unittest.TestCase):
    def test_finance_file_adapter_is_public_safe_and_local_only(self) -> None:
        result = validate_v014_s07_p1_finance_file_adapter()

        self.assertEqual(result["stage_id"], "S07")
        self.assertEqual(result["phase_id"], "S07-P1")
        self.assertEqual(result["phase_scope"], "v014_s07_p1_finance_file_adapter_only")
        self.assertTrue(result["s06_stage_review_dependency_validated"])
        self.assertTrue(result["legacy_finance_adapter_validated"])
        self.assertEqual(result["source_category_count"], 9)
        self.assertEqual(result["source_registry_count"], 9)
        self.assertEqual(result["field_candidate_count"], 45)
        self.assertEqual(result["hash_only_field_candidate_count"], 45)
        self.assertEqual(result["field_report_count"], 9)
        self.assertEqual(result["source_header_fingerprint_count"], 45)
        self.assertEqual(result["q4_human_confirmed_count"], 0)
        self.assertEqual(result["q5_calculation_baseline_allowed_count"], 0)
        self.assertEqual(result["formal_report_allowed_count"], 0)
        self.assertTrue(result["s07_p1_performed"])
        self.assertFalse(result["s07_p2_performed"])
        self.assertFalse(result["s07_p3_performed"])
        self.assertFalse(result["stage7_review_performed"])
        self.assertFalse(result["github_upload_performed"])
        self.assertFalse(result["raw_inbox_read_performed"])
        self.assertFalse(result["raw_inbox_mutation_performed"])
        self.assertFalse(result["business_field_value_parsing_performed"])
        self.assertFalse(result["source_header_plaintext_committed"])
        self.assertFalse(result["field_plaintext_committed"])
        self.assertFalse(result["delivery_allowed"])
        self.assertFalse(result["formal_report_allowed"])
        self.assertEqual(result["current_data_quality_grade"], "Q4")
        self.assertEqual(result["current_report_grade"], "D")
        self.assertEqual(result["release_permission"], "blocked")
        self.assertEqual(result["next_recommended_phase"], "S07-P2")
        self.assertIn("Stage 1-18", result["next_phase_instruction"])


if __name__ == "__main__":
    unittest.main()
