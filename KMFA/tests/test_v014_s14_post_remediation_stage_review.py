import importlib
import unittest


class TestV014S14PostRemediationStageReview(unittest.TestCase):
    def _module(self):
        try:
            return importlib.import_module(
                "KMFA.tools.check_v014_s14_post_remediation_stage_review"
            )
        except ModuleNotFoundError as exc:
            self.fail(f"missing current Stage 14 review implementation: {exc}")

    def _validate(self):
        return self._module().validate_v014_s14_post_remediation_stage_review(
            require_private_evidence=True,
            require_browser_evidence=True,
            require_final_evidence=True,
        )

    def test_review_uses_current_three_phase_chain(self) -> None:
        summary = self._validate()["summary"]

        self.assertEqual(summary["stage_id"], "S14")
        self.assertEqual(summary["roadmap_phase_id"], "STAGE-REVIEW")
        self.assertEqual(
            summary["phase_results"],
            {"S14-P1": "PASS", "S14-P2": "PASS", "S14-P3": "PASS"},
        )
        self.assertEqual(summary["current_data_quality_grade"], "Q4")
        self.assertEqual(summary["current_report_grade"], "D")
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertEqual(
            (
                summary["open_final_difference_accepted_count"],
                summary["nonzero_delta_reconciliation_count"],
                summary["zero_delta_reconciliation_count"],
                summary["incomplete_reconciliation_count"],
            ),
            (3, 9, 2, 1),
        )

    def test_current_fund_cash_loan_contract_is_preserved(self) -> None:
        summary = self._validate()["summary"]

        self.assertEqual(
            (
                summary["fund_source_lane_count"],
                summary["fund_private_parseable_lane_count"],
                summary["fund_row_binding_proven_lane_count"],
                summary["fund_value_binding_proven_lane_count"],
                summary["fund_planning_method_definition_count"],
                summary["fund_identified_business_item_count"],
            ),
            (4, 4, 0, 0, 3, 0),
        )
        self.assertEqual(summary["fund_private_unique_candidate_sheet_count"], 180)

    def test_current_invoice_tax_contract_is_preserved(self) -> None:
        summary = self._validate()["summary"]

        self.assertEqual(
            (
                summary["invoice_tax_source_lane_count"],
                summary["invoice_tax_private_parseable_direct_lane_count"],
                summary["invoice_tax_row_binding_proven_lane_count"],
                summary["invoice_tax_value_binding_proven_lane_count"],
                summary["invoice_tax_issue_method_definition_count"],
                summary["invoice_tax_cash_method_definition_count"],
                summary["invoice_tax_identified_issue_candidate_count"],
                summary["invoice_tax_materialized_cash_summary_count"],
            ),
            (3, 2, 0, 0, 3, 3, 0, 0),
        )
        self.assertEqual(summary["invoice_tax_private_unique_candidate_sheet_count"], 612)

    def test_current_policy_evidence_contract_is_preserved(self) -> None:
        summary = self._validate()["summary"]

        self.assertEqual(
            (
                summary["policy_program_count"],
                summary["policy_directory_definition_count"],
                summary["policy_required_evidence_category_count"],
                summary["policy_authoritative_evidence_bound_program_count"],
                summary["policy_evidence_complete_program_count"],
                summary["policy_evidence_gap_count"],
                summary["policy_risk_tip_count"],
                summary["policy_formal_qualification_conclusion_count"],
            ),
            (5, 5, 23, 0, 0, 5, 5, 0),
        )
        self.assertEqual(summary["policy_private_unique_lexical_candidate_sheet_count"], 3830)

    def test_three_page_navigation_and_review_findings_are_closed(self) -> None:
        manifest = self._validate()
        summary = manifest["summary"]

        self.assertEqual(summary["current_stage_page_count"], 3)
        self.assertEqual(summary["cross_page_link_count"], 6)
        self.assertEqual(summary["broken_cross_page_link_count"], 0)
        self.assertTrue(summary["cross_page_navigation_strongly_connected"])
        self.assertEqual(summary["fixed_review_finding_count"], 11)
        self.assertEqual(summary["open_review_finding_count"], 0)
        self.assertTrue(all(row["status"] == "fixed" for row in manifest["review_findings"]))

    def test_browser_review_covers_three_pages_desktop_and_mobile(self) -> None:
        browser = self._validate()["browser_review"]

        self.assertEqual(browser["baseline_pass_count"], 54)
        self.assertEqual(browser["baseline_warn_count"], 0)
        self.assertEqual(browser["baseline_fail_count"], 0)
        self.assertEqual(browser["current_page_count"], 3)
        self.assertEqual(browser["current_page_audits"]["p1"]["pass_count"], 13)
        self.assertEqual(browser["current_page_audits"]["p2"]["pass_count"], 12)
        self.assertEqual(browser["current_page_audits"]["p3"]["pass_count"], 13)
        self.assertEqual(browser["viewport_check_count"], 6)
        self.assertEqual(browser["representative_interaction_check_count"], 6)
        self.assertEqual(browser["cross_page_link_http_check_count"], 6)
        self.assertEqual(browser["cross_page_navigation_check_count"], 6)
        self.assertEqual(browser["console_error_count"], 0)
        self.assertEqual(browser["horizontal_overflow_count"], 0)

    def test_historical_stage14_state_is_quarantined(self) -> None:
        manifest = self._validate()

        self.assertTrue(manifest["historical_review_dependency_validated"])
        self.assertFalse(manifest["historical_review_dynamic_state_is_authoritative"])
        self.assertTrue(manifest["historical_pending_twelve_quarantined"])
        self.assertTrue(manifest["historical_static_business_items_quarantined"])
        self.assertTrue(manifest["historical_policy_mapping_semantics_quarantined"])
        self.assertTrue(manifest["historical_upload_ready_semantics_quarantined"])

    def test_review_stops_before_s15_release_and_business_actions(self) -> None:
        manifest = self._validate()
        boundaries = manifest["review_boundaries"]

        for key in (
            "s14_p1_validated",
            "s14_p2_validated",
            "s14_p3_validated",
            "stage14_review_performed",
        ):
            self.assertTrue(boundaries[key], key)
        for key in (
            "s15_p1_performed",
            "formal_policy_qualification_conclusion_performed",
            "policy_application_submission_performed",
            "subsidy_application_performed",
            "invoice_issuance_performed",
            "tax_filing_performed",
            "payment_or_bank_operation_performed",
            "github_upload_performed",
            "app_reinstall_performed",
            "formal_report_release_performed",
            "difference_closure_performed",
            "persistent_business_write_performed",
            "business_execution_performed",
        ):
            self.assertFalse(boundaries[key], key)
        self.assertEqual(manifest["next_phase"], "S15-P1")


if __name__ == "__main__":
    unittest.main()
