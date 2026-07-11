import unittest

from openpyxl.worksheet.formula import ArrayFormula

from KMFA.tools.check_v014_s14_p1_post_remediation_fund_cash_loan_plan import (
    validate_v014_s14_p1_post_remediation_fund_cash_loan_plan,
)
from KMFA.tools.v014_s14_p1_post_remediation_fund_cash_loan_plan import _normalize_cell, generate


class TestPrivateCellNormalization(unittest.TestCase):
    def test_array_formula_normalization_is_content_stable(self) -> None:
        first = ArrayFormula(ref="A1:A2", text="=SUM(B1:B2)")
        second = ArrayFormula(ref="A1:A2", text="=SUM(B1:B2)")
        expected = {
            "formula_type": "ArrayFormula",
            "ref": "A1:A2",
            "text": "=SUM(B1:B2)",
        }
        self.assertEqual(_normalize_cell(first), expected)
        self.assertEqual(_normalize_cell(second), expected)


class TestV014S14P1PostRemediationFundCashLoanPlan(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.generated = generate(final_validation=False, write_governance=False)
        cls.validated = validate_v014_s14_p1_post_remediation_fund_cash_loan_plan(
            require_private_evidence=True,
            require_browser_evidence=True,
        )

    def test_identity_and_current_dependency(self) -> None:
        self.assertEqual(self.generated, self.validated)
        self.assertEqual(self.validated["project_id"], "KMFA")
        self.assertEqual(self.validated["stage_id"], "S14")
        self.assertEqual(
            self.validated["phase_id"],
            "V014_S14_P1_POST_REMEDIATION_FUND_CASH_LOAN_PLAN",
        )
        self.assertEqual(self.validated["roadmap_phase_id"], "S14-P1")
        self.assertEqual(
            self.validated["task_id"],
            "KMFA-V014-S14-P1-POST-REMEDIATION-FUND-CASH-LOAN-PLAN-20260711",
        )
        self.assertTrue(self.validated["stage13_post_remediation_review_dependency_validated"])
        self.assertFalse(self.validated["historical_s14_p1_dynamic_state_is_authoritative"])

    def test_connects_four_structures_without_claiming_value_bindings(self) -> None:
        summary = self.validated["summary"]
        self.assertEqual(summary["source_lane_count"], 4)
        self.assertEqual(summary["structure_connected_lane_count"], 4)
        self.assertEqual(summary["unique_public_source_ref_count"], 4)
        self.assertEqual(summary["lane_source_binding_count"], 5)
        self.assertEqual(summary["unique_structure_candidate_count"], 20)
        self.assertEqual(summary["lane_structure_candidate_association_count"], 25)
        self.assertEqual(summary["private_parseable_lane_count"], 4)
        self.assertEqual(summary["row_level_binding_proven_lane_count"], 0)
        self.assertEqual(summary["value_binding_proven_lane_count"], 0)

    def test_read_only_raw_probe_is_exact_and_private(self) -> None:
        summary = self.validated["summary"]
        self.assertEqual(summary["raw_source_file_count"], 5)
        self.assertEqual(summary["private_xlsx_container_count"], 48)
        self.assertEqual(summary["private_parseable_xlsx_count"], 25)
        self.assertEqual(summary["private_unparseable_xlsx_count"], 23)
        self.assertEqual(summary["private_unique_candidate_sheet_count"], 180)
        self.assertEqual(
            summary["private_candidate_sheet_count_by_lane"],
            {
                "account_list": 12,
                "monthly_cash": 23,
                "fund_plan": 4,
                "loan_detail": 154,
            },
        )
        self.assertEqual(summary["private_probe_roundtrip_mismatch_count"], 0)
        self.assertTrue(summary["raw_snapshot_exact_match"])
        self.assertTrue(summary["raw_cross_phase_snapshot_exact_match"])

    def test_defines_outputs_but_keeps_business_items_zero(self) -> None:
        summary = self.validated["summary"]
        self.assertEqual(summary["planning_method_definition_count"], 3)
        self.assertEqual(summary["identified_cash_pressure_item_count"], 0)
        self.assertEqual(summary["identified_loan_due_item_count"], 0)
        self.assertEqual(summary["identified_account_balance_item_count"], 0)
        self.assertEqual(summary["identified_business_item_count"], 0)
        self.assertEqual(summary["public_business_amount_count"], 0)
        self.assertEqual(summary["payment_approval_count"], 0)
        self.assertEqual(summary["bank_operation_count"], 0)
        self.assertEqual(summary["loan_management_action_count"], 0)

    def test_preserves_current_quality_and_non_additive_difference_state(self) -> None:
        summary = self.validated["summary"]
        self.assertEqual(summary["open_final_difference_accepted_count"], 3)
        self.assertEqual(summary["nonzero_delta_reconciliation_count"], 9)
        self.assertEqual(summary["zero_delta_reconciliation_count"], 2)
        self.assertEqual(summary["incomplete_reconciliation_count"], 1)
        self.assertEqual(summary["current_data_quality_grade"], "Q4")
        self.assertEqual(summary["current_report_grade"], "D")
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertFalse(self.validated["quality_gate"]["cash_forecast_decision_allowed"])
        self.assertFalse(self.validated["quality_gate"]["formal_report_allowed"])

    def test_browser_flow_and_stage13_navigation(self) -> None:
        browser = self.validated["browser_review"]
        self.assertEqual(browser["baseline_pass_count"], 54)
        self.assertEqual(browser["baseline_warn_count"], 0)
        self.assertEqual(browser["baseline_fail_count"], 0)
        self.assertEqual(browser["current_page_count"], 1)
        self.assertEqual(browser["current_pass_count"], browser["current_control_row_count"])
        self.assertGreaterEqual(browser["current_pass_count"], 8)
        self.assertEqual(browser["viewport_check_count"], 2)
        self.assertEqual(browser["method_interaction_check_count"], 6)
        self.assertEqual(browser["dependency_link_http_check_count"], 4)
        self.assertEqual(browser["dependency_navigation_check_count"], 4)
        self.assertEqual(browser["console_error_count"], 0)
        self.assertEqual(browser["horizontal_overflow_count"], 0)

    def test_quarantines_legacy_static_signals(self) -> None:
        quarantine = self.validated["historical_quarantine"]
        self.assertTrue(quarantine["legacy_pending_twelve_quarantined"])
        self.assertTrue(quarantine["legacy_cash_pressure_records_quarantined"])
        self.assertTrue(quarantine["legacy_loan_due_alerts_quarantined"])
        self.assertTrue(quarantine["legacy_account_balance_summaries_quarantined"])
        self.assertEqual(quarantine["current_identified_business_item_count"], 0)

    def test_stops_before_later_scope_release_and_execution(self) -> None:
        boundaries = self.validated["phase_boundaries"]
        self.assertTrue(boundaries["s14_p1_performed"])
        for key in (
            "s14_p2_performed",
            "s14_p3_performed",
            "stage14_review_performed",
            "github_upload_performed",
            "app_reinstall_performed",
            "formal_report_release_performed",
            "difference_closure_performed",
            "persistent_business_write_performed",
            "business_execution_performed",
        ):
            self.assertFalse(boundaries[key], key)


if __name__ == "__main__":
    unittest.main()
