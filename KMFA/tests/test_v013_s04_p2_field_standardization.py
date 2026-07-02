import unittest

from KMFA.tools.check_v013_s04_p2_field_standardization import (
    validate_v013_s04_p2_field_standardization,
)


class TestV013S04P2FieldStandardization(unittest.TestCase):
    def test_field_standardization_replay_locks_public_safe_boundaries(self) -> None:
        result = validate_v013_s04_p2_field_standardization()

        self.assertEqual(result["stage_id"], "S04")
        self.assertEqual(result["phase_id"], "S04-P2")
        self.assertEqual(result["phase_scope"], "v013_s04_p2_field_standardization_replay_only")
        self.assertTrue(result["s04_p1_dependency_validated"])
        self.assertTrue(result["field_standardization_dependency_validated"])
        self.assertEqual(result["canonical_field_count"], 6)
        self.assertGreaterEqual(result["alias_dictionary_row_count"], 30)
        self.assertEqual(result["standardization_case_count"], 6)
        self.assertEqual(result["standardization_case_passed_count"], 6)
        self.assertEqual(result["quality_status_count"], 5)
        self.assertFalse(result["raw_dir_mutation_performed"])
        self.assertTrue(result["raw_dir_accidental_listing_performed"])
        self.assertTrue(result["raw_dir_accidental_listing_temp_files_removed"])
        self.assertFalse(result["raw_filename_publication_allowed"])
        self.assertFalse(result["field_plaintext_publication_allowed"])
        self.assertFalse(result["row_value_publication_allowed"])
        self.assertFalse(result["business_value_publication_allowed"])
        self.assertFalse(result["stage4_review_performed"])
        self.assertFalse(result["github_upload_performed"])
        self.assertFalse(result["delivery_allowed"])
        self.assertEqual(result["current_data_quality_grade"], "Q2")
        self.assertEqual(result["current_report_grade"], "D")
        self.assertEqual(result["release_permission"], "blocked")
        self.assertIn("S04-P3", result["next_required_step"])


if __name__ == "__main__":
    unittest.main()
