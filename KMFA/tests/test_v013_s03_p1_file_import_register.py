import unittest

from KMFA.tools.check_v013_s03_p1_file_import_register import (
    validate_v013_s03_p1_file_import_register,
)


class TestV013S03P1FileImportRegister(unittest.TestCase):
    def test_file_import_register_locks_public_safe_phase_boundary(self) -> None:
        result = validate_v013_s03_p1_file_import_register()

        self.assertEqual(result["stage_id"], "S03")
        self.assertEqual(result["phase_id"], "S03-P1")
        self.assertEqual(result["phase_scope"], "v013_s03_p1_file_import_register_only")
        self.assertTrue(result["s02_stage_review_dependency_validated"])
        self.assertTrue(result["file_import_register_dependency_validated"])
        self.assertEqual(result["core_supported_file_type_count"], 5)
        self.assertIn(".zip", result["supported_registration_extensions"])
        self.assertIn(".xlsx", result["supported_registration_extensions"])
        self.assertIn(".xls", result["supported_registration_extensions"])
        self.assertIn(".csv", result["supported_registration_extensions"])
        self.assertIn(".pdf", result["supported_registration_extensions"])
        self.assertTrue(result["safe_zip_extraction_validated"])
        self.assertTrue(result["zip_traversal_blocked"])
        self.assertTrue(result["metadata_required_fields_validated"])
        self.assertTrue(result["wps_ole_guidance_validated"])
        self.assertFalse(result["raw_dir_read_performed"])
        self.assertFalse(result["raw_dir_mutation_performed"])
        self.assertFalse(result["raw_file_bytes_committed"])
        self.assertFalse(result["raw_filename_publication_allowed"])
        self.assertFalse(result["raw_file_hash_publication_allowed"])
        self.assertFalse(result["business_field_parsing_performed"])
        self.assertFalse(result["raw_value_matching_performed"])
        self.assertFalse(result["github_upload_performed"])
        self.assertFalse(result["delivery_allowed"])
        self.assertIn("S03-P2", result["next_required_step"])


if __name__ == "__main__":
    unittest.main()
