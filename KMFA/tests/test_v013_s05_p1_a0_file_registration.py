import unittest

from KMFA.tools.check_v013_s05_p1_a0_file_registration import (
    validate_v013_s05_p1_a0_file_registration,
)


class TestV013S05P1A0FileRegistration(unittest.TestCase):
    def test_a0_file_registration_replay_locks_public_safe_raw_alignment(self) -> None:
        result = validate_v013_s05_p1_a0_file_registration()

        self.assertEqual(result["stage_id"], "S05")
        self.assertEqual(result["phase_id"], "S05-P1")
        self.assertEqual(result["phase_scope"], "v013_s05_p1_a0_file_registration_replay_only")
        self.assertTrue(result["stage4_review_dependency_validated"])
        self.assertTrue(result["legacy_s05_p1_dependency_validated"])
        self.assertEqual(result["a0_file_summary"]["total_files"], 9)
        self.assertEqual(result["a0_file_summary"]["pdf_files"], 8)
        self.assertEqual(result["a0_file_summary"]["excel_files"], 1)
        self.assertEqual(result["a0_file_summary"]["member_sha256_recorded_count"], 0)
        self.assertEqual(result["a0_file_summary"]["member_sha256_pending_count"], 9)
        self.assertEqual(result["a0_candidate_summary"]["candidate_count"], 9)
        self.assertEqual(result["a0_candidate_summary"]["q3_machine_candidate_count"], 9)
        self.assertEqual(result["a0_candidate_summary"]["q4_human_locked_count"], 0)
        self.assertEqual(result["a0_candidate_summary"]["q5_formal_report_allowed_count"], 0)

        raw_alignment = result["raw_alignment"]
        self.assertTrue(raw_alignment["raw_data_inbox_read_required"])
        self.assertTrue(raw_alignment["raw_data_inbox_read_performed"])
        self.assertFalse(raw_alignment["raw_data_inbox_mutation_performed"])
        self.assertTrue(raw_alignment["local_raw_zip_present"])
        self.assertTrue(raw_alignment["local_raw_zip_openable"])
        self.assertFalse(raw_alignment["local_raw_package_hash_matches_registered"])
        self.assertFalse(raw_alignment["local_raw_package_size_matches_registered"])
        self.assertEqual(raw_alignment["local_raw_business_member_count"], 9)
        self.assertEqual(raw_alignment["local_raw_pdf_member_count"], 8)
        self.assertEqual(raw_alignment["local_raw_excel_member_count"], 1)
        self.assertFalse(raw_alignment["member_sha256_public_backfill_performed"])
        self.assertEqual(
            raw_alignment["member_sha256_public_backfill_blocked_reason"],
            "local_raw_package_hash_or_size_mismatch",
        )

        self.assertFalse(result["raw_dir_mutation_performed"])
        self.assertFalse(result["raw_filename_publication_allowed"])
        self.assertFalse(result["raw_file_hash_publication_allowed"])
        self.assertFalse(result["field_plaintext_publication_allowed"])
        self.assertFalse(result["sheet_name_publication_allowed"])
        self.assertFalse(result["zip_member_name_publication_allowed"])
        self.assertFalse(result["row_value_publication_allowed"])
        self.assertFalse(result["business_value_publication_allowed"])
        self.assertFalse(result["s05_p2_performed"])
        self.assertFalse(result["stage5_review_performed"])
        self.assertFalse(result["github_upload_performed"])
        self.assertTrue(result["github_upload_deferred_until_stage10_batch"])
        self.assertFalse(result["delivery_allowed"])
        self.assertEqual(result["current_data_quality_grade"], "Q2")
        self.assertEqual(result["current_report_grade"], "D")
        self.assertEqual(result["release_permission"], "blocked")
        self.assertIn("S05-P2", result["next_required_step"])
        self.assertIn("separate run", result["next_required_step"])


if __name__ == "__main__":
    unittest.main()
