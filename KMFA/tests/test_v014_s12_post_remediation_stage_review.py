import importlib
import unittest


class TestV014S12PostRemediationStageReview(unittest.TestCase):
    def _validate(self):
        try:
            module = importlib.import_module(
                "KMFA.tools.check_v014_s12_post_remediation_stage_review"
            )
        except ModuleNotFoundError as exc:
            self.fail(f"missing Stage 12 post-remediation review implementation: {exc}")
        return module.validate_v014_s12_post_remediation_stage_review(
            require_private_evidence=True,
            require_browser_evidence=True,
            require_final_evidence=True,
        )

    def test_review_uses_current_three_phase_chain(self) -> None:
        summary = self._validate()["summary"]

        self.assertEqual(summary["stage_id"], "S12")
        self.assertEqual(summary["roadmap_phase_id"], "STAGE-REVIEW")
        self.assertEqual(
            summary["phase_results"],
            {"S12-P1": "PASS", "S12-P2": "PASS", "S12-P3": "PASS"},
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

    def test_control_preview_and_rerun_contract_is_complete(self) -> None:
        summary = self._validate()["summary"]

        self.assertEqual(summary["pending_action_group_count"], 6)
        self.assertEqual(summary["manual_event_template_count"], 4)
        self.assertEqual(summary["impact_preview_definition_count"], 6)
        self.assertEqual(summary["high_risk_preview_count"], 5)
        self.assertEqual(summary["second_confirmation_required_count"], 5)
        self.assertEqual(summary["rerun_plan_definition_count"], 6)
        self.assertEqual(summary["required_rerun_chain_layer_count"], 4)
        self.assertEqual(summary["planned_rerun_step_count"], 24)
        self.assertEqual(summary["current_approved_business_event_count"], 0)
        self.assertEqual(summary["current_published_business_event_count"], 0)
        self.assertEqual(summary["current_persistent_cache_invalidation_count"], 0)
        self.assertEqual(summary["current_persistent_rerun_step_count"], 0)
        self.assertEqual(summary["current_persistent_consistency_check_count"], 0)

    def test_cross_page_navigation_and_review_findings_are_closed(self) -> None:
        manifest = self._validate()
        summary = manifest["summary"]

        self.assertEqual(summary["current_stage_page_count"], 3)
        self.assertEqual(summary["cross_page_link_count"], 6)
        self.assertEqual(summary["broken_cross_page_link_count"], 0)
        self.assertTrue(summary["cross_page_navigation_strongly_connected"])
        self.assertGreaterEqual(summary["fixed_review_finding_count"], 6)
        self.assertEqual(summary["open_review_finding_count"], 0)
        self.assertTrue(all(row["status"] == "fixed" for row in manifest["review_findings"]))

    def test_browser_review_covers_three_pages_desktop_and_mobile(self) -> None:
        browser = self._validate()["browser_review"]

        self.assertEqual(browser["viewport_check_count"], 6)
        self.assertEqual(browser["representative_interaction_check_count"], 6)
        self.assertEqual(browser["cross_page_link_http_check_count"], 6)
        self.assertEqual(browser["cross_page_navigation_check_count"], 6)
        self.assertEqual(browser["console_error_count"], 0)
        self.assertEqual(browser["horizontal_overflow_count"], 0)

    def test_historical_dynamic_state_is_quarantined(self) -> None:
        manifest = self._validate()

        self.assertTrue(manifest["historical_review_dependency_validated"])
        self.assertFalse(manifest["historical_review_dynamic_state_is_authoritative"])
        self.assertTrue(manifest["historical_five_events_quarantined"])
        self.assertTrue(manifest["historical_two_eligible_events_quarantined"])
        self.assertTrue(manifest["historical_eight_rerun_steps_quarantined"])

    def test_raw_and_downstream_boundaries_remain_closed(self) -> None:
        manifest = self._validate()
        summary = manifest["summary"]
        boundaries = manifest["review_boundaries"]

        self.assertEqual(summary["raw_source_file_count"], 5)
        self.assertTrue(summary["raw_snapshot_exact_match"])
        self.assertTrue(summary["raw_cross_phase_snapshot_exact_match"])
        self.assertTrue(boundaries["stage12_review_performed"])
        for key in (
            "s13_p1_performed",
            "github_upload_performed",
            "app_reinstall_performed",
            "formal_report_release_performed",
            "business_execution_performed",
            "persistent_business_write_performed",
        ):
            self.assertFalse(boundaries[key])

    def test_review_validator_survives_later_global_phase(self) -> None:
        try:
            module = importlib.import_module(
                "KMFA.tools.check_v014_s12_post_remediation_stage_review"
            )
        except ModuleNotFoundError as exc:
            self.fail(f"missing Stage 12 post-remediation review implementation: {exc}")

        self.assertTrue(
            module._phase_is_current(
                'current_phase: "V014_S12_POST_REMEDIATION_STAGE_REVIEW"'
            )
        )
        self.assertFalse(
            module._phase_is_current('current_phase: "V014_S13_P1_REPORT_SHELL"')
        )


if __name__ == "__main__":
    unittest.main()
