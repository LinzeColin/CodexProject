import importlib
import unittest


class TestV014S10PostRemediationStageReview(unittest.TestCase):
    def test_browser_console_filter_ignores_only_automatic_favicon_404(self) -> None:
        module = importlib.import_module(
            "KMFA.tools.v014_s10_post_remediation_stage_review"
        )
        self.assertTrue(
            hasattr(module, "_is_actionable_console_error"),
            "missing actionable console error filter",
        )

        self.assertFalse(
            module._is_actionable_console_error(
                "Failed to load resource: 404 http://127.0.0.1/favicon.ico"
            )
        )
        self.assertTrue(module._is_actionable_console_error("ReferenceError: reportState is undefined"))

    def _validate(self):
        try:
            module = importlib.import_module(
                "KMFA.tools.check_v014_s10_post_remediation_stage_review"
            )
        except ModuleNotFoundError as exc:
            self.fail(f"missing Stage 10 post-remediation review implementation: {exc}")
        return module.validate_v014_s10_post_remediation_stage_review(
            require_private_evidence=True,
            require_browser_evidence=True,
        )

    def test_review_uses_current_post_remediation_chain(self) -> None:
        manifest = self._validate()
        summary = manifest["summary"]

        self.assertEqual(summary["stage_id"], "S10")
        self.assertEqual(
            summary["review_scope"],
            "v014_s10_post_remediation_stage_review_only",
        )
        self.assertEqual(
            summary["phase_results"],
            {"S10-P1": "PASS", "S10-P2": "PASS", "S10-P3": "PASS"},
        )
        self.assertEqual(summary["open_final_difference_accepted_count"], 3)
        self.assertEqual(summary["nonzero_delta_reconciliation_count"], 9)
        self.assertEqual(summary["zero_delta_reconciliation_count"], 2)
        self.assertEqual(summary["incomplete_reconciliation_count"], 1)
        self.assertNotIn("pending_reconciliation_count", summary)

    def test_stage_contract_and_restricted_exports_are_complete(self) -> None:
        summary = self._validate()["summary"]

        self.assertEqual(summary["report_template_count"], 2)
        self.assertEqual(summary["management_section_count"], 11)
        self.assertEqual(summary["report_grade_record_count"], 2)
        self.assertEqual(summary["report_export_record_count"], 2)
        self.assertEqual(summary["html_restricted_preview_count"], 2)
        self.assertEqual(summary["csv_restricted_appendix_count"], 2)
        self.assertEqual(summary["excel_compatible_csv_download_count"], 2)
        self.assertEqual(summary["browser_viewport_check_count"], 4)
        self.assertEqual(summary["byte_exact_download_count"], 2)
        self.assertEqual(summary["committed_pdf_file_count"], 0)
        self.assertEqual(summary["committed_excel_workbook_count"], 0)
        self.assertEqual(summary["formal_report_count"], 0)
        self.assertEqual(summary["business_decision_basis_allowed_count"], 0)

    def test_d_no_go_limits_propagate_without_stale_state(self) -> None:
        manifest = self._validate()
        summary = manifest["summary"]

        self.assertEqual(summary["current_data_quality_grade"], "Q4")
        self.assertEqual(summary["current_report_grade"], "D")
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertEqual(summary["hard_block_count"], 12)
        self.assertTrue(manifest["cross_format_restriction_propagation_verified"])
        self.assertFalse(manifest["stale_b_grade_or_pending_twelve_detected"])
        self.assertFalse(manifest["restricted_preview_mislabeled_as_formal_report"])

    def test_findings_are_fixed_and_old_review_is_historical_only(self) -> None:
        manifest = self._validate()
        findings = manifest["review_findings"]

        self.assertGreaterEqual(len(findings), 5)
        self.assertTrue(all(item["status"] == "fixed" for item in findings))
        self.assertEqual(manifest["summary"]["open_review_finding_count"], 0)
        self.assertEqual(
            manifest["summary"]["fixed_review_finding_count"], len(findings)
        )
        self.assertTrue(manifest["historical_review_dependency_validated"])
        self.assertFalse(manifest["historical_review_dynamic_state_is_authoritative"])
        self.assertTrue(manifest["frozen_phase_semantics_validated"])

    def test_raw_and_release_boundaries_remain_closed(self) -> None:
        manifest = self._validate()
        summary = manifest["summary"]
        boundaries = manifest["review_boundaries"]

        self.assertTrue(summary["raw_snapshot_exact_match"])
        self.assertTrue(summary["raw_cross_phase_snapshot_exact_match"])
        self.assertEqual(summary["raw_source_file_count"], 5)
        self.assertTrue(boundaries["stage10_review_performed"])
        for key in (
            "s11_p1_performed",
            "github_upload_performed",
            "app_reinstall_performed",
            "formal_report_release_performed",
            "business_execution_performed",
        ):
            self.assertFalse(boundaries[key])


if __name__ == "__main__":
    unittest.main()
