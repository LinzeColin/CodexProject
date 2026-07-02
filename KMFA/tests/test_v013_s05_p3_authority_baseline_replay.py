import unittest

from KMFA.tools.check_v013_s05_p3_authority_baseline_replay import (
    validate_v013_s05_p3_authority_baseline_replay,
)


class TestV013S05P3AuthorityBaselineReplay(unittest.TestCase):
    def test_authority_baseline_replay_locks_public_safe_q5_baseline(self) -> None:
        result = validate_v013_s05_p3_authority_baseline_replay()

        self.assertEqual(result["stage_id"], "S05")
        self.assertEqual(result["phase_id"], "S05-P3")
        self.assertEqual(result["phase_scope"], "v013_s05_p3_authority_baseline_replay_only")
        self.assertTrue(result["s05_p2_dependency_validated"])
        self.assertTrue(result["legacy_s05_p3_dependency_validated"])
        self.assertEqual(result["baseline_version"], "KMFA-A0-Q5-20260630-S05P3-PUBLIC-SAFE-HASH-LOCK")
        self.assertEqual(
            result["baseline_content_hash"],
            "sha256:dbb55ffb4e3608e49dbcf91e97fc0f19395a8269ff7c8f4d5c3f8ca398c03670",
        )
        self.assertEqual(result["authority_records"], 45)
        self.assertEqual(result["q5_locked_field_count"], 40)
        self.assertEqual(result["excluded_field_count"], 5)
        self.assertFalse(result["formal_report_allowed"])
        self.assertFalse(result["raw_dir_read_required"])
        self.assertFalse(result["raw_dir_read_performed"])
        self.assertFalse(result["raw_dir_mutation_performed"])
        self.assertFalse(result["field_plaintext_publication_allowed"])
        self.assertTrue(result["s05_p3_performed"])
        self.assertFalse(result["stage5_review_performed"])
        self.assertFalse(result["github_upload_performed"])
        self.assertTrue(result["github_upload_deferred_until_stage10_batch"])
        self.assertFalse(result["delivery_allowed"])
        self.assertEqual(result["current_data_quality_grade"], "Q2")
        self.assertEqual(result["current_report_grade"], "D")
        self.assertEqual(result["release_permission"], "blocked")
        self.assertIn("Stage 5 whole review", result["next_required_step"])
        self.assertIn("separate run", result["next_required_step"])
        self.assertIn("Stage 1-10", result["next_required_step"])


if __name__ == "__main__":
    unittest.main()
