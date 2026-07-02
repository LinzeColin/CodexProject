import unittest

from KMFA.tools.check_v013_s02_p1_raw_readiness import validate_v013_s02_p1_raw_readiness


class TestV013S02P1RawReadiness(unittest.TestCase):
    def test_raw_readiness_inventory_is_public_safe_and_upload_deferred(self) -> None:
        result = validate_v013_s02_p1_raw_readiness()

        self.assertEqual(result["stage_id"], "S02")
        self.assertEqual(result["phase_id"], "S02-P1")
        self.assertEqual(result["task_id"], "KMFA-V013-S02-P1-RAW-READINESS-20260702")
        self.assertEqual(result["raw_dir"], "/Users/linzezhang/Downloads/KMFA_MetaData")
        self.assertTrue(result["raw_dir_exists"])
        self.assertTrue(result["raw_dir_readable"])
        self.assertGreater(result["file_count"], 0)
        self.assertTrue(result["private_inventory_written"])
        self.assertTrue(result["private_outputs_git_ignored"])
        self.assertFalse(result["raw_dir_mutation_performed"])
        self.assertFalse(result["raw_value_matching_performed"])
        self.assertFalse(result["github_upload_performed"])
        self.assertFalse(result["delivery_allowed"])
        self.assertFalse(result["public_manifest_contains_raw_filenames"])
        self.assertFalse(result["public_manifest_contains_raw_values"])
        self.assertIn("overall completion", result["next_required_step"])


if __name__ == "__main__":
    unittest.main()
