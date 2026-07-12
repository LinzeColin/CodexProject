import unittest

from KMFA.tools.check_v014_s04_p2_field_standardization import (
    validate_v014_s04_p2_field_standardization,
)


class TestV014S04P2FieldStandardization(unittest.TestCase):
    def test_field_standardization_locks_public_safe_boundaries(self) -> None:
        result = validate_v014_s04_p2_field_standardization()

        self.assertEqual(result["stage_id"], "S04")
        self.assertEqual(result["phase_id"], "S04-P2")
        self.assertEqual(result["phase_scope"], "v014_s04_p2_field_standardization_only")
        self.assertTrue(result["s04_p1_dependency_validated"])
        self.assertTrue(result["field_standardization_dependency_validated"])
        self.assertEqual(result["canonical_field_count"], 6)
        self.assertGreaterEqual(result["alias_dictionary_row_count"], 30)
        self.assertEqual(result["mapping_record_count"], 6)
        self.assertEqual(result["standardization_case_count"], 6)
        self.assertEqual(result["standardization_case_passed_count"], 6)
        self.assertEqual(result["quality_status_count"], 5)
        self.assertTrue(result["field_standardization_performed"])
        self.assertTrue(result["field_alias_mapping_performed"])
        self.assertFalse(result["raw_field_mapping_performed"])
        self.assertFalse(result["raw_dir_read_performed"])
        self.assertFalse(result["raw_dir_list_performed"])
        self.assertFalse(result["raw_dir_hash_performed"])
        self.assertFalse(result["raw_dir_mutation_performed"])
        self.assertFalse(result["raw_filename_publication_allowed"])
        self.assertFalse(result["field_plaintext_publication_allowed"])
        self.assertFalse(result["row_value_publication_allowed"])
        self.assertFalse(result["business_value_publication_allowed"])
        self.assertFalse(result["s04_p3_started"])
        self.assertFalse(result["stage4_review_performed"])
        self.assertFalse(result["github_upload_performed"])
        self.assertFalse(result["delivery_allowed"])
        self.assertEqual(result["current_data_quality_grade"], "Q2")
        self.assertEqual(result["current_report_grade"], "D")
        self.assertEqual(result["release_permission"], "blocked")
        self.assertEqual(result["current_go_no_go"], "NO_GO")
        self.assertIn("S04-P3", result["next_required_step"])


if __name__ == "__main__":
    unittest.main()
