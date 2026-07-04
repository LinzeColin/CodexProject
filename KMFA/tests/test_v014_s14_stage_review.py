import unittest

from KMFA.tools.check_v014_s14_stage_review import validate_v014_s14_stage_review


class TestV014S14StageReview(unittest.TestCase):
    def test_stage14_review_closes_fund_tax_policy_stage_without_upload_or_actions(self) -> None:
        manifest = validate_v014_s14_stage_review()

        self.assertEqual(manifest["stage_id"], "S14")
        self.assertEqual(manifest["status"], "review_passed_local_only_no_go_upload_deferred_until_v014_stage1_18_complete")
        self.assertTrue(manifest["stage_review_performed"])
        self.assertEqual(
            manifest["phase_results"],
            {"S14-P1": "PASS", "S14-P2": "PASS", "S14-P3": "PASS"},
        )
        self.assertEqual(manifest["review_findings_summary"]["open_finding_count"], 0)
        self.assertGreaterEqual(manifest["review_findings_summary"]["fixed_finding_count"], 1)

        gate = manifest["stage_gate"]
        self.assertEqual(gate["fund_cash_loan_source_lane_count"], 4)
        self.assertEqual(gate["cash_pressure_record_count"], 4)
        self.assertEqual(gate["loan_due_alert_count"], 3)
        self.assertEqual(gate["account_balance_summary_count"], 3)
        self.assertEqual(gate["invoice_tax_source_lane_count"], 3)
        self.assertEqual(gate["invoice_tax_issue_candidate_count"], 3)
        self.assertEqual(gate["invoice_tax_cash_summary_count"], 3)
        self.assertEqual(gate["policy_evidence_directory_count"], 5)
        self.assertEqual(gate["policy_evidence_gap_count"], 5)
        self.assertEqual(gate["policy_risk_tip_count"], 5)
        self.assertEqual(gate["html_export_count"], 3)
        self.assertEqual(gate["pending_reconciliation_count"], 12)
        self.assertEqual(gate["formal_report_count"], 0)
        self.assertEqual(gate["business_decision_basis_count"], 0)
        self.assertEqual(gate["payment_or_bank_operation_count"], 0)
        self.assertEqual(gate["loan_management_action_count"], 0)
        self.assertEqual(gate["tax_filing_count"], 0)
        self.assertEqual(gate["invoice_issuance_count"], 0)
        self.assertEqual(gate["formal_policy_conclusion_count"], 0)
        self.assertEqual(gate["policy_application_submission_count"], 0)
        self.assertEqual(gate["subsidy_application_count"], 0)
        self.assertEqual(gate["current_report_grade"], "D")
        self.assertEqual(gate["release_permission"], "blocked")

        self.assertFalse(manifest["s15_p1_performed"])
        self.assertFalse(manifest["github_upload_performed"])
        self.assertEqual(manifest["github_upload_status"], "not_uploaded_deferred_until_v014_stage1_18_complete")
        self.assertTrue(manifest["raw_data_boundary"]["s14_p1_raw_inbox_all_false"])
        self.assertTrue(manifest["raw_data_boundary"]["s14_p2_raw_inbox_all_false"])
        self.assertTrue(manifest["raw_data_boundary"]["s14_p3_raw_inbox_all_false"])


if __name__ == "__main__":
    unittest.main()
