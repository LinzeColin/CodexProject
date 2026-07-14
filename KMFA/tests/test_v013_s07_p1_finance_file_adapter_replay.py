import unittest

from KMFA.tools.check_v013_s07_p1_finance_file_adapter_replay import (
    validate_v013_s07_p1_finance_file_adapter_replay,
)


class TestV013S07P1FinanceFileAdapterReplay(unittest.TestCase):
    def test_finance_file_adapter_replay_stays_public_safe_and_local_only(self) -> None:
        result = validate_v013_s07_p1_finance_file_adapter_replay()

        self.assertEqual(result["stage_id"], "S07")
        self.assertEqual(result["phase_id"], "S07-P1")
        self.assertEqual(result["phase_scope"], "v013_s07_p1_finance_file_adapter_replay_only")
        self.assertTrue(result["s06_stage_review_dependency_validated"])
        self.assertTrue(result["legacy_s07_p1_dependency_validated"])
        self.assertEqual(result["source_category_count"], 9)
        self.assertEqual(result["field_candidate_count"], 45)
        self.assertEqual(result["hash_only_field_candidate_count"], 45)
        self.assertEqual(result["field_report_count"], 9)
        self.assertEqual(result["source_header_hash_count"], 45)
        self.assertEqual(result["q4_human_confirmed_count"], 0)
        self.assertEqual(result["q5_calculation_baseline_allowed_count"], 0)
        self.assertEqual(result["formal_report_allowed_count"], 0)
        self.assertFalse(result["raw_dir_read_performed"])
        self.assertFalse(result["raw_dir_mutation_performed"])
        self.assertTrue(result["s07_p1_performed"])
        self.assertFalse(result["s07_p2_performed"])
        self.assertFalse(result["s07_p3_performed"])
        self.assertFalse(result["stage7_review_performed"])
        self.assertFalse(result["github_upload_performed"])
        self.assertTrue(result["github_upload_deferred_until_stage10_batch"])
        self.assertFalse(result["delivery_allowed"])
        self.assertFalse(result["formal_report_allowed"])
        self.assertEqual(result["current_data_quality_grade"], "Q4")
        self.assertEqual(result["current_report_grade"], "D")
        self.assertEqual(result["release_permission"], "blocked")
        self.assertIn("S07-P2", result["next_required_step"])
        self.assertIn("separate run", result["next_required_step"])
        self.assertIn("Stage 1-10", result["next_required_step"])


if __name__ == "__main__":
    unittest.main()
