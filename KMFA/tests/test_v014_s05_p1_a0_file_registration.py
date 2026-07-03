import unittest

from KMFA.tools.check_v014_s05_p1_a0_file_registration import validate_v014_s05_p1_a0_file_registration


class TestV014S05P1A0FileRegistration(unittest.TestCase):
    def test_a0_file_registration_locks_public_safe_q3_candidates(self) -> None:
        result = validate_v014_s05_p1_a0_file_registration()

        self.assertEqual(result["stage_id"], "S05")
        self.assertEqual(result["phase_id"], "S05-P1")
        self.assertEqual(result["phase_scope"], "v014_s05_p1_a0_file_registration_only")
        self.assertTrue(result["stage4_review_dependency_validated"])
        self.assertEqual(result["a0_file_summary"]["total_files"], 9)
        self.assertEqual(result["a0_file_summary"]["pdf_files"], 8)
        self.assertEqual(result["a0_file_summary"]["excel_files"], 1)
        self.assertEqual(result["a0_file_summary"]["private_business_member_hash_record_count"], 9)
        self.assertEqual(result["a0_file_summary"]["public_actual_raw_package_hash_committed_count"], 0)
        self.assertEqual(result["a0_file_summary"]["public_actual_raw_member_hash_committed_count"], 0)
        self.assertEqual(result["a0_candidate_summary"]["candidate_count"], 9)
        self.assertEqual(result["a0_candidate_summary"]["q3_machine_candidate_count"], 9)
        self.assertEqual(result["a0_candidate_summary"]["q4_human_locked_count"], 0)
        self.assertEqual(result["a0_candidate_summary"]["q5_calculation_baseline_allowed_count"], 0)

        raw = result["raw_alignment"]
        self.assertTrue(raw["raw_data_inbox_read_required"])
        self.assertTrue(raw["raw_data_inbox_read_performed"])
        self.assertTrue(raw["raw_data_inbox_list_performed"])
        self.assertTrue(raw["raw_data_inbox_stat_performed"])
        self.assertTrue(raw["raw_data_inbox_hash_performed"])
        self.assertFalse(raw["raw_data_inbox_mutation_performed"])
        self.assertTrue(raw["local_raw_zip_present"])
        self.assertTrue(raw["local_raw_zip_openable"])
        self.assertEqual(raw["local_raw_business_member_count"], 9)
        self.assertEqual(raw["local_raw_pdf_member_count"], 8)
        self.assertEqual(raw["local_raw_excel_member_count"], 1)
        self.assertTrue(raw["private_package_hash_recorded"])
        self.assertEqual(raw["private_business_member_hash_record_count"], 9)
        self.assertFalse(raw["public_actual_raw_package_hash_committed"])
        self.assertFalse(raw["public_actual_raw_member_hashes_committed"])
        self.assertFalse(raw["public_raw_member_names_committed"])
        self.assertTrue(raw["private_diagnostic_written"])

        scope = result["phase_scope_controls"]
        self.assertFalse(scope["s05_p2_performed"])
        self.assertFalse(scope["s05_p3_performed"])
        self.assertFalse(scope["stage5_review_performed"])
        self.assertFalse(scope["github_upload_performed"])
        self.assertFalse(scope["raw_value_matching_performed"])
        self.assertFalse(scope["lineage_full_check_performed"])
        self.assertFalse(scope["formal_report_performed"])
        self.assertFalse(scope["business_execution_performed"])
        self.assertEqual(result["release_state"]["current_data_quality_grade"], "Q3")
        self.assertEqual(result["release_state"]["current_report_grade"], "D")
        self.assertEqual(result["release_state"]["current_go_no_go"], "NO_GO")
        self.assertFalse(result["release_state"]["github_main_upload_allowed"])
        self.assertEqual(result["next_recommended_phase"], "S05-P2")
        self.assertIn("Stage 1-18", result["next_phase_instruction"])


if __name__ == "__main__":
    unittest.main()
