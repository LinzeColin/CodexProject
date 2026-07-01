import unittest

from KMFA.tools.check_s14_stage_review import (
    DEFAULT_REVIEW_MANIFEST,
    validate_stage_review,
)


class S14StageReviewTests(unittest.TestCase):
    def test_stage14_review_manifest_matches_phase_evidence(self) -> None:
        counts = validate_stage_review(DEFAULT_REVIEW_MANIFEST)

        self.assertEqual(counts["fund_cash_loan_source_lane_count"], 4)
        self.assertEqual(counts["cash_pressure_record_count"], 4)
        self.assertEqual(counts["loan_due_alert_count"], 3)
        self.assertEqual(counts["account_balance_summary_count"], 3)
        self.assertEqual(counts["invoice_tax_source_lane_count"], 3)
        self.assertEqual(counts["invoice_tax_issue_candidate_count"], 3)
        self.assertEqual(counts["invoice_tax_cash_summary_count"], 3)
        self.assertEqual(counts["policy_evidence_directory_count"], 5)
        self.assertEqual(counts["policy_evidence_gap_count"], 5)
        self.assertEqual(counts["policy_risk_tip_count"], 5)
        self.assertEqual(counts["pending_reconciliation_count"], 12)
        self.assertEqual(counts["html_export_count"], 3)
        self.assertEqual(counts["full_kmfa_unit_tests"], 191)


if __name__ == "__main__":
    unittest.main()
