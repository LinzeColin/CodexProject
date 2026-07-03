import unittest

from KMFA.tools.check_v014_s05_p2_field_golden_baseline import (
    validate_v014_s05_p2_field_golden_baseline,
)


class TestV014S05P2FieldGoldenBaseline(unittest.TestCase):
    def test_field_golden_baseline_public_safe_counts_and_boundaries(self) -> None:
        manifest = validate_v014_s05_p2_field_golden_baseline()
        summary = manifest["field_candidate_summary"]
        owner = manifest["owner_decision_summary"]
        scope = manifest["phase_scope_controls"]

        self.assertEqual(manifest["stage_id"], "S05")
        self.assertEqual(manifest["phase_id"], "S05-P2")
        self.assertEqual(manifest["phase_scope"], "v014_s05_p2_field_golden_baseline_only")
        self.assertTrue(manifest["s05_p1_dependency_validated"])
        self.assertEqual(summary["a0_project_candidate_count"], 9)
        self.assertEqual(summary["required_field_contract_count"], 5)
        self.assertEqual(summary["field_candidate_count"], 45)
        self.assertEqual(summary["pdf_field_candidate_count"], 40)
        self.assertEqual(summary["excel_field_candidate_count"], 5)
        self.assertEqual(summary["source_anchor_recorded_private_only_count"], 40)
        self.assertEqual(summary["source_anchor_pending_or_downgraded_count"], 5)
        self.assertEqual(summary["private_value_hash_recorded_count"], 40)
        self.assertEqual(summary["private_value_hash_pending_or_downgraded_count"], 5)
        self.assertEqual(summary["q3_field_candidate_count"], 45)
        self.assertEqual(summary["q4_human_confirmed_count"], 0)
        self.assertEqual(summary["q5_calculation_baseline_allowed_count"], 0)
        self.assertEqual(summary["owner_downgraded_excel_candidate_count"], 1)
        self.assertEqual(summary["owner_downgraded_excel_field_count"], 5)
        self.assertEqual(summary["public_source_or_normalized_value_committed_count"], 0)
        self.assertEqual(summary["public_source_header_plaintext_committed_count"], 0)
        self.assertEqual(owner["active_decision_code"], "downgrade_to_cross_source_support")
        self.assertTrue(manifest["completion_gate"]["ready"])
        self.assertEqual(manifest["completion_gate"]["mode"], "owner_downgrade_to_cross_source_support")
        self.assertTrue(scope["field_level_golden_baseline_performed"])
        self.assertTrue(scope["s05_p2_performed"])
        self.assertFalse(scope["raw_inbox_read_by_this_phase"])
        self.assertFalse(scope["raw_inbox_mutated_by_this_phase"])
        self.assertFalse(scope["business_field_parsing_from_raw_performed"])
        self.assertFalse(scope["source_value_matching_performed"])
        self.assertFalse(scope["s05_p3_performed"])
        self.assertFalse(scope["stage5_review_performed"])
        self.assertFalse(scope["github_upload_performed"])
        self.assertFalse(manifest["github_upload_performed"])
        self.assertEqual(manifest["github_upload_status"], "not_uploaded_deferred_until_v014_stage1_18_complete")
        self.assertEqual(manifest["release_state"]["current_data_quality_grade"], "Q3")
        self.assertEqual(manifest["release_state"]["current_report_grade"], "D")
        self.assertEqual(manifest["release_state"]["current_go_no_go"], "NO_GO")
        self.assertFalse(manifest["release_state"]["delivery_allowed"])
        self.assertFalse(manifest["release_state"]["formal_report_allowed"])
        self.assertEqual(manifest["next_recommended_phase"], "S05-P3")
        self.assertIn("Stage 1-18", manifest["next_phase_instruction"])
        self.assertIn("Stage 5 review", manifest["next_phase_instruction"])


if __name__ == "__main__":
    unittest.main()
