import unittest

from KMFA.tools.check_v014_s05_p3_authority_baseline_lock import (
    validate_v014_s05_p3_authority_baseline_lock,
)


class TestV014S05P3AuthorityBaselineLock(unittest.TestCase):
    def test_authority_baseline_lock_public_safe_counts_and_boundaries(self) -> None:
        manifest = validate_v014_s05_p3_authority_baseline_lock()
        summary = manifest["authority_baseline_summary"]
        scope = manifest["phase_scope_controls"]
        release = manifest["release_state"]

        self.assertEqual(manifest["stage_id"], "S05")
        self.assertEqual(manifest["phase_id"], "S05-P3")
        self.assertEqual(manifest["phase_scope"], "v014_s05_p3_authority_baseline_lock_only")
        self.assertTrue(manifest["s05_p2_dependency_validated"])
        self.assertEqual(summary["authority_record_count"], 45)
        self.assertEqual(summary["field_candidate_count"], 45)
        self.assertEqual(summary["q5_calculation_baseline_locked_count"], 40)
        self.assertEqual(summary["excluded_cross_source_support_only_count"], 5)
        self.assertEqual(summary["q4_human_confirmed_count"], 40)
        self.assertEqual(summary["q5_calculation_baseline_allowed_count"], 40)
        self.assertEqual(summary["q5_full_quality_grade_allowed_count"], 0)
        self.assertEqual(summary["zero_delta_validated_count"], 0)
        self.assertEqual(summary["lineage_full_check_completed_count"], 0)
        self.assertEqual(summary["formal_report_allowed_count"], 0)
        self.assertEqual(summary["pdf_locked_field_count"], 40)
        self.assertEqual(summary["excel_excluded_field_count"], 5)
        self.assertTrue(scope["authority_baseline_lock_performed"])
        self.assertTrue(scope["s05_p3_performed"])
        self.assertFalse(scope["raw_inbox_read_by_this_phase"])
        self.assertFalse(scope["raw_inbox_mutated_by_this_phase"])
        self.assertFalse(scope["source_value_matching_performed"])
        self.assertFalse(scope["stage5_review_performed"])
        self.assertFalse(scope["github_upload_performed"])
        self.assertFalse(scope["zero_delta_validation_performed"])
        self.assertFalse(scope["lineage_full_check_performed"])
        self.assertFalse(scope["formal_report_performed"])
        self.assertFalse(manifest["github_upload_performed"])
        self.assertEqual(manifest["github_upload_status"], "not_uploaded_deferred_until_v014_stage1_18_complete")
        self.assertEqual(release["current_data_quality_grade"], "Q4")
        self.assertEqual(
            release["field_level_calculation_baseline_status"],
            "q5_calculation_baseline_locked_for_40_fields_not_full_q5_quality",
        )
        self.assertEqual(release["current_report_grade"], "D")
        self.assertEqual(release["current_go_no_go"], "NO_GO")
        self.assertFalse(release["delivery_allowed"])
        self.assertFalse(release["formal_report_allowed"])
        self.assertEqual(manifest["next_recommended_phase"], "S05-STAGE-REVIEW")
        self.assertIn("Stage 5 whole review", manifest["next_phase_instruction"])
        self.assertIn("Stage 1-18", manifest["next_phase_instruction"])


if __name__ == "__main__":
    unittest.main()
