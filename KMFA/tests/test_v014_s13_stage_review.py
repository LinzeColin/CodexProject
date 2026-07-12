import unittest

from KMFA.tools.check_v014_s13_stage_review import validate_v014_s13_stage_review


class TestV014S13StageReview(unittest.TestCase):
    def test_stage13_review_closes_reporting_stage_without_upload_or_business_action(self) -> None:
        manifest = validate_v014_s13_stage_review()

        self.assertEqual(manifest["stage_id"], "S13")
        self.assertEqual(manifest["status"], "review_passed_local_only_no_go_upload_deferred_until_v014_stage1_18_complete")
        self.assertTrue(manifest["stage_review_performed"])
        self.assertEqual(
            manifest["phase_results"],
            {"S13-P1": "PASS", "S13-P2": "PASS", "S13-P3": "PASS"},
        )
        self.assertEqual(manifest["review_findings_summary"]["open_finding_count"], 0)
        self.assertGreaterEqual(manifest["review_findings_summary"]["fixed_finding_count"], 1)

        gate = manifest["stage_gate"]
        self.assertEqual(gate["financial_operating_source_lane_count"], 4)
        self.assertEqual(gate["financial_operating_draft_count"], 2)
        self.assertEqual(gate["financial_operating_html_draft_count"], 2)
        self.assertEqual(gate["collection_receivable_source_lane_count"], 5)
        self.assertEqual(gate["collection_receivable_priority_item_count"], 4)
        self.assertEqual(gate["collection_receivable_responsibility_item_count"], 4)
        self.assertEqual(gate["cross_table_review_dimension_count"], 4)
        self.assertEqual(gate["cross_table_difference_queue_count"], 4)
        self.assertEqual(gate["operating_quality_report_count"], 1)
        self.assertEqual(gate["html_export_count"], 4)
        self.assertEqual(gate["pending_reconciliation_count"], 12)
        self.assertEqual(gate["formal_report_count"], 0)
        self.assertEqual(gate["business_decision_basis_count"], 0)
        self.assertEqual(gate["difference_auto_resolution_count"], 0)
        self.assertEqual(gate["difference_closure_count"], 0)
        self.assertEqual(gate["legal_collection_decision_count"], 0)
        self.assertEqual(gate["payment_or_bank_operation_count"], 0)
        self.assertEqual(gate["current_report_grade"], "D")
        self.assertEqual(gate["release_permission"], "blocked")

        self.assertFalse(manifest["s14_p1_performed"])
        self.assertFalse(manifest["github_upload_performed"])
        self.assertEqual(manifest["github_upload_status"], "not_uploaded_deferred_until_v014_stage1_18_complete")
        self.assertTrue(manifest["raw_data_boundary"]["s13_p1_raw_inbox_all_false"])
        self.assertTrue(manifest["raw_data_boundary"]["s13_p2_raw_inbox_all_false"])
        self.assertTrue(manifest["raw_data_boundary"]["s13_p3_raw_inbox_all_false"])


if __name__ == "__main__":
    unittest.main()
