import importlib
import unittest


class TestV014S13PostRemediationStageReview(unittest.TestCase):
    def _module(self):
        try:
            return importlib.import_module(
                "KMFA.tools.check_v014_s13_post_remediation_stage_review"
            )
        except ModuleNotFoundError as exc:
            self.fail(f"missing current Stage 13 review implementation: {exc}")

    def _validate(self):
        return self._module().validate_v014_s13_post_remediation_stage_review(
            require_private_evidence=True,
            require_browser_evidence=True,
            require_final_evidence=True,
        )

    def test_review_uses_current_three_phase_chain(self) -> None:
        summary = self._validate()["summary"]

        self.assertEqual(summary["stage_id"], "S13")
        self.assertEqual(summary["roadmap_phase_id"], "STAGE-REVIEW")
        self.assertEqual(
            summary["phase_results"],
            {"S13-P1": "PASS", "S13-P2": "PASS", "S13-P3": "PASS"},
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

    def test_current_reporting_collection_and_cross_table_contract_is_preserved(self) -> None:
        summary = self._validate()["summary"]

        self.assertEqual(
            (
                summary["financial_source_lane_count"],
                summary["financial_structure_connected_lane_count"],
                summary["financial_raw_value_bound_lane_count"],
                summary["financial_draft_report_count"],
            ),
            (4, 4, 0, 2),
        )
        self.assertEqual(
            (
                summary["receivable_source_lane_count"],
                summary["receivable_private_parseable_lane_count"],
                summary["receivable_row_binding_proven_lane_count"],
                summary["receivable_issue_definition_count"],
                summary["receivable_identified_business_item_count"],
            ),
            (5, 3, 0, 4, 0),
        )
        self.assertEqual(
            (
                summary["cross_table_review_dimension_count"],
                summary["cross_table_comparable_dimension_count"],
                summary["cross_table_exact_comparison_count"],
                summary["cross_table_not_comparable_dimension_count"],
                summary["cross_table_difference_queue_count"],
                summary["cross_table_quality_report_count"],
            ),
            (4, 0, 0, 4, 4, 1),
        )
        self.assertTrue(summary["cross_table_difference_queue_is_non_additive"])

    def test_four_page_navigation_and_review_findings_are_closed(self) -> None:
        manifest = self._validate()
        summary = manifest["summary"]

        self.assertEqual(summary["current_stage_page_count"], 4)
        self.assertEqual(summary["cross_page_link_count"], 12)
        self.assertEqual(summary["broken_cross_page_link_count"], 0)
        self.assertTrue(summary["cross_page_navigation_strongly_connected"])
        self.assertEqual(summary["fixed_review_finding_count"], 9)
        self.assertEqual(summary["open_review_finding_count"], 0)
        self.assertTrue(all(row["status"] == "fixed" for row in manifest["review_findings"]))

    def test_browser_review_covers_four_pages_desktop_and_mobile(self) -> None:
        browser = self._validate()["browser_review"]

        self.assertEqual(browser["baseline_pass_count"], 54)
        self.assertEqual(browser["baseline_warn_count"], 0)
        self.assertEqual(browser["baseline_fail_count"], 0)
        self.assertEqual(browser["current_page_count"], 4)
        self.assertEqual(browser["viewport_check_count"], 8)
        self.assertEqual(browser["representative_interaction_check_count"], 8)
        self.assertEqual(browser["cross_page_link_http_check_count"], 12)
        self.assertEqual(browser["cross_page_navigation_check_count"], 12)
        self.assertEqual(browser["console_error_count"], 0)
        self.assertEqual(browser["horizontal_overflow_count"], 0)

    def test_historical_dynamic_state_is_quarantined(self) -> None:
        manifest = self._validate()

        self.assertTrue(manifest["historical_review_dependency_validated"])
        self.assertFalse(manifest["historical_review_dynamic_state_is_authoritative"])
        self.assertTrue(manifest["historical_pending_twelve_quarantined"])
        self.assertTrue(manifest["historical_static_business_items_quarantined"])
        self.assertTrue(manifest["historical_cross_table_semantics_quarantined"])
        self.assertTrue(manifest["historical_upload_ready_semantics_quarantined"])

    def test_quality_and_business_boundaries_remain_closed(self) -> None:
        manifest = self._validate()
        quality = manifest["quality_gate"]

        self.assertTrue(quality["current_public_safe_pages_allowed"])
        self.assertTrue(quality["restricted_internal_preview_allowed"])
        self.assertFalse(quality["quality_grade_bypass_allowed"])
        self.assertFalse(quality["formal_report_allowed"])
        self.assertFalse(quality["business_decision_basis_allowed"])
        self.assertFalse(quality["difference_closure_allowed"])
        self.assertFalse(quality["business_execution_allowed"])

    def test_raw_and_downstream_boundaries_remain_closed(self) -> None:
        manifest = self._validate()
        summary = manifest["summary"]
        boundaries = manifest["review_boundaries"]

        self.assertEqual(summary["raw_source_file_count"], 5)
        self.assertTrue(summary["raw_snapshot_exact_match"])
        self.assertTrue(summary["raw_cross_phase_snapshot_exact_match"])
        self.assertTrue(boundaries["stage13_review_performed"])
        for key in (
            "s14_p1_performed",
            "github_upload_performed",
            "app_reinstall_performed",
            "formal_report_release_performed",
            "difference_closure_performed",
            "business_execution_performed",
            "persistent_business_write_performed",
        ):
            self.assertFalse(boundaries[key])

    def test_review_validator_survives_later_global_phase(self) -> None:
        module = self._module()

        self.assertTrue(
            module._phase_is_current(
                'current_phase: "V014_S13_POST_REMEDIATION_STAGE_REVIEW"'
            )
        )
        self.assertFalse(
            module._phase_is_current('current_phase: "V014_S14_P1_FUND_CASH_LOAN_PLAN"')
        )


if __name__ == "__main__":
    unittest.main()
