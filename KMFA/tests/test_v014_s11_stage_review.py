import unittest

from KMFA.tools.check_v014_s11_stage_review import validate_v014_s11_stage_review


class TestV014S11StageReview(unittest.TestCase):
    def test_stage11_review_closes_human_flow_without_upload_or_release(self) -> None:
        manifest = validate_v014_s11_stage_review()

        self.assertEqual(manifest["stage_id"], "S11")
        self.assertEqual(manifest["status"], "review_passed_local_only_no_go_upload_deferred_until_v014_stage1_18_complete")
        self.assertTrue(manifest["stage_review_performed"])
        self.assertEqual(
            manifest["phase_results"],
            {"S11-P1": "PASS", "S11-P2": "PASS", "S11-P3": "PASS"},
        )
        self.assertEqual(manifest["review_findings_summary"]["open_finding_count"], 0)
        self.assertGreaterEqual(manifest["review_findings_summary"]["fixed_finding_count"], 1)
        self.assertEqual(manifest["stage_gate"]["navigation_module_count"], 8)
        self.assertEqual(manifest["stage_gate"]["nav_button_count"], 8)
        self.assertEqual(manifest["stage_gate"]["module_action_button_count"], 8)
        self.assertEqual(manifest["stage_gate"]["source_check_matrix_row_count"], 13)
        self.assertEqual(manifest["stage_gate"]["source_check_required_column_count"], 11)
        self.assertEqual(manifest["stage_gate"]["project_cost_page_row_count"], 4)
        self.assertEqual(manifest["stage_gate"]["project_cost_page_column_count"], 7)
        self.assertEqual(manifest["stage_gate"]["cost_category_count"], 9)
        self.assertEqual(manifest["stage_gate"]["margin_record_count"], 4)
        self.assertEqual(manifest["stage_gate"]["pending_reconciliation_count"], 12)
        self.assertEqual(manifest["stage_gate"]["html_export_count"], 3)
        self.assertEqual(manifest["stage_gate"]["formal_report_count"], 0)
        self.assertEqual(manifest["stage_gate"]["business_decision_basis_count"], 0)
        self.assertEqual(manifest["stage_gate"]["current_report_grade"], "D")
        self.assertEqual(manifest["stage_gate"]["release_permission"], "blocked")
        self.assertFalse(manifest["s12_p1_performed"])
        self.assertFalse(manifest["github_upload_performed"])
        self.assertEqual(manifest["github_upload_status"], "not_uploaded_deferred_until_v014_stage1_18_complete")
        self.assertTrue(manifest["raw_data_boundary"]["s11_p1_raw_inbox_all_false"])
        self.assertTrue(manifest["raw_data_boundary"]["s11_p2_raw_inbox_all_false"])
        self.assertTrue(manifest["raw_data_boundary"]["s11_p3_raw_inbox_all_false"])


if __name__ == "__main__":
    unittest.main()
