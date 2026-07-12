import importlib
import unittest


class TestV014S11PostRemediationStageReview(unittest.TestCase):
    def _validate(self):
        try:
            module = importlib.import_module(
                "KMFA.tools.check_v014_s11_post_remediation_stage_review"
            )
        except ModuleNotFoundError as exc:
            self.fail(f"missing Stage 11 post-remediation review implementation: {exc}")
        return module.validate_v014_s11_post_remediation_stage_review(
            require_private_evidence=True,
            require_browser_evidence=True,
        )

    def test_review_uses_current_three_phase_chain(self) -> None:
        manifest = self._validate()
        summary = manifest["summary"]

        self.assertEqual(summary["stage_id"], "S11")
        self.assertEqual(summary["roadmap_phase_id"], "STAGE-REVIEW")
        self.assertEqual(
            summary["phase_results"],
            {"S11-P1": "PASS", "S11-P2": "PASS", "S11-P3": "PASS"},
        )
        self.assertEqual(summary["open_final_difference_accepted_count"], 3)
        self.assertEqual(summary["nonzero_delta_reconciliation_count"], 9)
        self.assertEqual(summary["zero_delta_reconciliation_count"], 2)
        self.assertEqual(summary["incomplete_reconciliation_count"], 1)
        self.assertEqual(summary["current_data_quality_grade"], "Q4")
        self.assertEqual(summary["current_report_grade"], "D")
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertNotIn("pending_reconciliation_count", summary)

    def test_stage_contract_and_cross_page_navigation_are_complete(self) -> None:
        summary = self._validate()["summary"]

        self.assertEqual(summary["navigation_module_count"], 8)
        self.assertEqual(summary["source_check_matrix_row_count"], 13)
        self.assertEqual(summary["source_check_required_column_count"], 11)
        self.assertEqual(summary["project_cost_page_row_count"], 4)
        self.assertEqual(summary["project_cost_page_column_count"], 7)
        self.assertEqual(summary["current_stage_page_count"], 3)
        self.assertEqual(summary["cross_page_link_count"], 6)
        self.assertEqual(summary["broken_cross_page_link_count"], 0)
        self.assertTrue(summary["cross_page_navigation_strongly_connected"])

    def test_d_no_go_and_unknown_project_attribution_are_preserved(self) -> None:
        manifest = self._validate()
        summary = manifest["summary"]
        quality = manifest["quality_gate"]

        self.assertEqual(summary["project_specific_attributed_difference_count"], 0)
        self.assertEqual(summary["project_specific_unknown_allocation_count"], 4)
        self.assertEqual(summary["formal_report_count"], 0)
        self.assertEqual(summary["business_decision_basis_allowed_count"], 0)
        self.assertFalse(quality["quality_grade_bypass_allowed"])
        self.assertFalse(quality["formal_report_allowed"])
        self.assertFalse(quality["business_decision_basis_allowed"])
        self.assertFalse(quality["business_execution_allowed"])

    def test_findings_and_browser_review_are_closed(self) -> None:
        manifest = self._validate()
        summary = manifest["summary"]
        browser = manifest["browser_review"]

        self.assertGreaterEqual(summary["fixed_review_finding_count"], 4)
        self.assertEqual(summary["open_review_finding_count"], 0)
        self.assertTrue(all(item["status"] == "fixed" for item in manifest["review_findings"]))
        self.assertEqual(browser["viewport_check_count"], 6)
        self.assertEqual(browser["cross_page_link_http_check_count"], 6)
        self.assertEqual(browser["cross_page_navigation_check_count"], 6)
        self.assertEqual(browser["console_error_count"], 0)
        self.assertEqual(browser["horizontal_overflow_count"], 0)

    def test_raw_and_downstream_boundaries_remain_closed(self) -> None:
        manifest = self._validate()
        summary = manifest["summary"]
        boundaries = manifest["review_boundaries"]

        self.assertEqual(summary["raw_source_file_count"], 5)
        self.assertTrue(summary["raw_snapshot_exact_match"])
        self.assertTrue(summary["raw_cross_phase_snapshot_exact_match"])
        self.assertTrue(boundaries["stage11_review_performed"])
        for key in (
            "s12_p1_performed",
            "github_upload_performed",
            "app_reinstall_performed",
            "formal_report_release_performed",
            "business_execution_performed",
            "persistent_business_write_performed",
        ):
            self.assertFalse(boundaries[key])

    def test_review_validator_survives_later_global_phase(self) -> None:
        module = importlib.import_module(
            "KMFA.tools.check_v014_s11_post_remediation_stage_review"
        )

        self.assertTrue(
            module._phase_is_current(
                'current_phase: "V014_S11_POST_REMEDIATION_STAGE_REVIEW"'
            )
        )
        self.assertFalse(
            module._phase_is_current('current_phase: "V014_S12_P1_PENDING_WORKBENCH"')
        )


if __name__ == "__main__":
    unittest.main()
