import unittest

from KMFA.tools.check_v014_s09_stage_review import validate_v014_s09_stage_review


class TestV014S09StageReview(unittest.TestCase):
    def test_stage_review_closes_s09_without_upload_raw_matching_or_s10(self) -> None:
        result = validate_v014_s09_stage_review()

        self.assertEqual(result["stage_id"], "S09")
        self.assertEqual(result["review_scope"], "v014_s09_stage_review_only")
        self.assertEqual(result["phase_count"], 3)
        self.assertEqual(result["phase_results"], {"S09-P1": "PASS", "S09-P2": "PASS", "S09-P3": "PASS"})
        self.assertTrue(result["s09_p1_dependency_validated"])
        self.assertTrue(result["s09_p2_dependency_validated"])
        self.assertTrue(result["s09_p3_dependency_validated"])
        self.assertTrue(result["stage_review_performed"])
        self.assertFalse(result["s10_p1_performed"])
        self.assertFalse(result["github_upload_performed"])
        self.assertFalse(result["github_upload_ready_next_gate"])
        self.assertTrue(result["github_upload_deferred_until_v014_stage1_18_complete"])
        self.assertFalse(result["legacy_stage9_upload_artifacts_current_gate"])
        self.assertFalse(result["app_reinstall_performed"])
        self.assertFalse(result["raw_value_matching_performed"])
        self.assertFalse(result["lineage_full_check_completed"])
        self.assertFalse(result["formal_report_performed"])
        self.assertEqual(result["open_review_finding_count"], 0)
        self.assertEqual(result["fixed_review_finding_count"], 1)
        self.assertEqual(result["review_findings"][0]["status"], "fixed")

        gate = result["stage_gate"]
        self.assertEqual(gate["project_cost_required_metric_count"], 6)
        self.assertEqual(gate["project_cost_category_count"], 9)
        self.assertEqual(gate["project_cost_fact_record_count"], 4)
        self.assertEqual(gate["project_cost_unallocated_pool_count"], 9)
        self.assertEqual(gate["project_cost_authority_locked_field_count"], 40)
        self.assertEqual(gate["project_cost_authority_excluded_field_count"], 5)
        self.assertEqual(gate["margin_required_metric_count"], 4)
        self.assertEqual(gate["margin_record_count"], 4)
        self.assertEqual(gate["margin_difference_summary_count"], 12)
        self.assertEqual(gate["margin_authority_field_group_count"], 8)
        self.assertEqual(gate["margin_authority_system_overwrite_allowed_count"], 0)
        self.assertEqual(gate["margin_public_amount_values_committed_count"], 0)
        self.assertEqual(gate["reconciliation_record_count"], 12)
        self.assertEqual(gate["reconciliation_domain_control_count"], 6)
        self.assertEqual(gate["reconciliation_confirmed_resolution_count"], 0)
        self.assertEqual(gate["reconciliation_pending_resolution_count"], 12)
        self.assertEqual(gate["reconciliation_derived_metric_rerun_allowed_count"], 0)
        self.assertEqual(gate["formal_report_allowed_count"], 0)

        self.assertEqual(result["release_state"]["current_data_quality_grade"], "Q4")
        self.assertEqual(result["release_state"]["current_report_grade"], "D")
        self.assertEqual(result["release_state"]["current_go_no_go"], "NO_GO")
        self.assertFalse(result["release_state"]["delivery_allowed"])
        self.assertFalse(result["release_state"]["github_main_upload_allowed"])
        self.assertFalse(result["raw_data_boundary"]["raw_inbox_read_by_this_review"])
        self.assertFalse(result["raw_data_boundary"]["raw_inbox_listed_by_this_review"])
        self.assertFalse(result["raw_data_boundary"]["raw_inbox_hashed_by_this_review"])
        self.assertFalse(result["raw_data_boundary"]["raw_inbox_mutated_by_this_review"])
        self.assertTrue(result["raw_data_boundary"]["s09_p1_raw_inbox_all_false"])
        self.assertTrue(result["raw_data_boundary"]["s09_p2_raw_inbox_all_false"])
        self.assertTrue(result["raw_data_boundary"]["s09_p3_raw_inbox_all_false"])
        self.assertEqual(result["next_recommended_phase"], "S10-P1")
        self.assertIn("Stage 1-18", result["next_phase_instruction"])
        self.assertIn("separate run", result["next_phase_instruction"])


if __name__ == "__main__":
    unittest.main()
