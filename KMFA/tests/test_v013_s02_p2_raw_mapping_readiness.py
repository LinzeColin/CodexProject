import unittest

from KMFA.tools.check_v013_s02_p2_raw_mapping_readiness import (
    validate_v013_s02_p2_raw_mapping_readiness,
)


class TestV013S02P2RawMappingReadiness(unittest.TestCase):
    def test_private_schema_readiness_is_public_safe_and_upload_deferred(self) -> None:
        result = validate_v013_s02_p2_raw_mapping_readiness()

        self.assertEqual(result["stage_id"], "S02")
        self.assertEqual(result["phase_id"], "S02-P2")
        self.assertEqual(result["task_id"], "KMFA-V013-S02-P2-RAW-MAPPING-READINESS-20260702")
        self.assertTrue(result["s02_p1_dependency_validated"])
        self.assertEqual(result["raw_dir"], "/Users/linzezhang/Downloads/KMFA_MetaData")
        self.assertTrue(result["raw_dir_exists"])
        self.assertTrue(result["raw_dir_readable"])
        self.assertGreater(result["raw_file_count"], 0)
        self.assertGreaterEqual(result["zip_files_seen"], 1)
        self.assertGreaterEqual(result["xlsx_files_seen"], 1)
        self.assertGreaterEqual(result["zip_files_openable"], 1)
        self.assertGreaterEqual(result["workbooks_parseable"], 1)
        self.assertTrue(result["private_schema_inventory_written"])
        self.assertTrue(result["private_mapping_diagnostic_written"])
        self.assertTrue(result["private_outputs_git_ignored"])
        self.assertFalse(result["raw_dir_mutation_performed"])
        self.assertFalse(result["public_manifest_contains_raw_filenames"])
        self.assertFalse(result["public_manifest_contains_field_plaintext"])
        self.assertFalse(result["public_manifest_contains_raw_values"])
        self.assertEqual(result["raw_value_matching_readiness_status"], "blocked_authorized_mapping_required")
        self.assertFalse(result["raw_value_matching_performed"])
        self.assertFalse(result["github_upload_performed"])
        self.assertFalse(result["delivery_allowed"])
        self.assertIn("S02-P3", result["next_required_step"])


if __name__ == "__main__":
    unittest.main()
