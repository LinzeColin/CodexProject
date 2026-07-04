import unittest

from KMFA.tools.check_v014_s14_p1_fund_cash_loan_plan import (
    validate_v014_s14_p1_fund_cash_loan_plan,
)
from KMFA.tools.v014_s14_p1_fund_cash_loan_plan import generate


class V014S14P1FundCashLoanPlanTests(unittest.TestCase):
    def test_locks_fund_cash_loan_plan_without_operations_later_scope_or_upload(self) -> None:
        manifest = generate()
        validated = validate_v014_s14_p1_fund_cash_loan_plan()

        self.assertEqual(manifest, validated)
        self.assertEqual(validated["project_id"], "KMFA")
        self.assertEqual(validated["version"], "0.1.4")
        self.assertEqual(validated["stage_id"], "S14")
        self.assertEqual(validated["phase_id"], "S14-P1")
        self.assertEqual(validated["phase_scope"], "v014_s14_p1_fund_cash_loan_plan_only")
        self.assertEqual(validated["task_id"], "KMFA-V014-S14-P1-FUND-CASH-LOAN-PLAN-20260705")
        self.assertEqual(validated["completed_task_ids"], ["S14P1T01", "S14P1T02", "S14P1T03"])
        self.assertEqual(validated["acceptance_ids"], ["ACC-V014-S14-P1-FUND-CASH-LOAN-PLAN"])

        progress = validated["stage14_phase_progress"]
        self.assertEqual(progress["completed_phase_count"], 1)
        self.assertEqual(progress["total_phase_count"], 3)
        self.assertEqual(progress["derived_percent_label"], "33.33%")
        self.assertTrue(progress["s14_p1_performed"])
        self.assertFalse(progress["s14_p2_performed"])
        self.assertFalse(progress["s14_p3_performed"])
        self.assertFalse(progress["stage14_review_performed"])

        summary = validated["fund_cash_loan_summary"]
        self.assertEqual(summary["source_lane_count"], 4)
        self.assertEqual(summary["source_count"], 5)
        self.assertEqual(summary["field_mapping_count"], 25)
        self.assertEqual(summary["cash_pressure_record_count"], 4)
        self.assertEqual(summary["loan_due_alert_count"], 3)
        self.assertEqual(summary["account_balance_summary_count"], 3)
        self.assertEqual(summary["html_output_count"], 1)
        self.assertEqual(summary["pending_reconciliation_count"], 12)
        self.assertEqual(summary["report_grade_visible"], "D")
        self.assertEqual(summary["payment_operation_count"], 0)
        self.assertEqual(summary["bank_operation_count"], 0)
        self.assertEqual(summary["loan_management_action_count"], 0)

        upload = validated["github_upload"]
        self.assertFalse(upload["github_upload_performed"])
        self.assertFalse(upload["github_upload_ready_next_gate"])
        self.assertTrue(upload["github_upload_deferred_until_v014_stage1_18_complete"])

        raw_boundary = validated["raw_data_boundary"]
        self.assertFalse(raw_boundary["raw_inbox_read_by_this_phase"])
        self.assertFalse(raw_boundary["raw_inbox_listed_by_this_phase"])
        self.assertFalse(raw_boundary["raw_inbox_mutated_by_this_phase"])

        quality = validated["quality_gate"]
        self.assertTrue(quality["planning_signal_allowed"])
        self.assertFalse(quality["formal_report_allowed"])
        self.assertFalse(quality["business_decision_basis_allowed"])
        self.assertFalse(quality["payment_approval_allowed"])
        self.assertFalse(quality["bank_operation_allowed"])
        self.assertFalse(quality["loan_management_action_allowed"])
        self.assertFalse(quality["tax_filing_allowed"])
        self.assertFalse(quality["invoice_issuance_allowed"])
        self.assertFalse(quality["s14_p2_allowed"])
        self.assertFalse(quality["s14_p3_allowed"])
        self.assertFalse(quality["stage14_review_allowed"])
        self.assertFalse(quality["github_upload_allowed"])


if __name__ == "__main__":
    unittest.main()
