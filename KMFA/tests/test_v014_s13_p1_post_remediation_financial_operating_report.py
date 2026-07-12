import importlib
import unittest


class TestV014S13P1PostRemediationFinancialOperatingReport(unittest.TestCase):
    def _module(self):
        try:
            return importlib.import_module(
                "KMFA.tools.check_v014_s13_p1_post_remediation_financial_operating_report"
            )
        except ModuleNotFoundError as exc:
            self.fail(f"missing current S13-P1 implementation: {exc}")

    def _validate(self):
        return self._module().validate_v014_s13_p1_post_remediation_financial_operating_report(
            require_private_evidence=True,
            require_browser_evidence=True,
            require_final_evidence=True,
        )

    def test_current_stage12_review_is_the_only_dynamic_dependency(self) -> None:
        manifest = self._validate()
        summary = manifest["summary"]

        self.assertEqual(summary["stage_id"], "S13")
        self.assertEqual(summary["roadmap_phase_id"], "S13-P1")
        self.assertTrue(manifest["stage12_post_remediation_review_dependency_validated"])
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
        self.assertNotIn("pending_reconciliation_count", summary)

    def test_four_financial_lanes_are_structure_connected_without_value_claims(self) -> None:
        manifest = self._validate()
        summary = manifest["summary"]

        self.assertEqual(summary["source_lane_count"], 4)
        self.assertEqual(summary["unique_source_count"], 7)
        self.assertEqual(summary["lane_source_binding_count"], 8)
        self.assertEqual(summary["unique_structure_candidate_count"], 35)
        self.assertEqual(summary["lane_structure_candidate_association_count"], 40)
        self.assertEqual(summary["structure_connected_lane_count"], 4)
        self.assertEqual(summary["raw_value_bound_lane_count"], 0)
        self.assertEqual(len(manifest["source_lane_status"]), 4)
        for lane in manifest["source_lane_status"]:
            self.assertTrue(lane["structure_connected"])
            self.assertFalse(lane["current_raw_value_binding_proven"])
            self.assertEqual(lane["data_status"], "structure_connected_values_unproven")

    def test_weekly_and_monthly_drafts_show_status_and_limits(self) -> None:
        manifest = self._validate()
        summary = manifest["summary"]

        self.assertEqual(summary["draft_report_count"], 2)
        self.assertEqual(summary["html_draft_count"], 2)
        self.assertEqual(summary["required_section_count"], 7)
        self.assertEqual(
            {row["draft_id"] for row in manifest["draft_definitions"]},
            {"financial_operating_weekly_draft", "financial_operating_monthly_draft"},
        )
        for draft in manifest["draft_definitions"]:
            self.assertEqual(draft["report_grade_visible"], "D")
            self.assertTrue(draft["draft_report_allowed"])
            self.assertFalse(draft["formal_report_allowed"])
            self.assertFalse(draft["contains_business_amounts"])
            self.assertTrue(draft["data_status_and_limitations_visible"])

    def test_historical_report_state_is_quarantined(self) -> None:
        manifest = self._validate()

        self.assertTrue(manifest["historical_s13_p1_policy_fixture_validated"])
        self.assertFalse(manifest["historical_s13_p1_dynamic_state_is_authoritative"])
        self.assertTrue(manifest["historical_pending_twelve_quarantined"])
        self.assertTrue(manifest["historical_b_grade_sample_quarantined"])

    def test_browser_review_covers_both_drafts_and_interactions(self) -> None:
        browser = self._validate()["browser_review"]

        self.assertEqual(browser["baseline_pass_count"], 54)
        self.assertEqual(browser["baseline_warn_count"], 0)
        self.assertEqual(browser["baseline_fail_count"], 0)
        self.assertEqual(browser["current_page_count"], 2)
        self.assertEqual(browser["current_control_row_count"], 20)
        self.assertEqual(browser["current_pass_count"], 20)
        self.assertEqual(browser["viewport_check_count"], 4)
        self.assertEqual(browser["section_interaction_check_count"], 28)
        self.assertEqual(browser["cross_draft_link_http_check_count"], 2)
        self.assertEqual(browser["cross_draft_navigation_check_count"], 2)
        self.assertEqual(browser["console_error_count"], 0)
        self.assertEqual(browser["horizontal_overflow_count"], 0)

    def test_raw_alignment_is_exact_and_private(self) -> None:
        manifest = self._validate()
        summary = manifest["summary"]
        raw = manifest["raw_boundary"]

        self.assertEqual(summary["raw_source_file_count"], 5)
        self.assertTrue(summary["raw_snapshot_exact_match"])
        self.assertTrue(summary["raw_cross_phase_snapshot_exact_match"])
        self.assertTrue(raw["raw_read_authorized"])
        self.assertTrue(raw["raw_snapshot_validation_performed"])
        for key in (
            "raw_write_performed",
            "raw_delete_performed",
            "raw_move_performed",
            "raw_rename_performed",
            "raw_overwrite_performed",
            "raw_mutation_performed",
        ):
            self.assertFalse(raw[key])

    def test_downstream_and_release_boundaries_remain_closed(self) -> None:
        manifest = self._validate()
        boundaries = manifest["phase_boundaries"]
        quality = manifest["quality_gate"]

        self.assertTrue(boundaries["s13_p1_performed"])
        for key in (
            "s13_p2_performed",
            "s13_p3_performed",
            "stage13_review_performed",
            "github_upload_performed",
            "app_reinstall_performed",
            "formal_report_release_performed",
            "business_execution_performed",
            "persistent_business_write_performed",
        ):
            self.assertFalse(boundaries[key])
        self.assertTrue(quality["draft_report_allowed"])
        self.assertFalse(quality["formal_report_allowed"])
        self.assertFalse(quality["business_decision_basis_allowed"])
        self.assertFalse(quality["business_execution_allowed"])

    def test_validator_survives_later_global_phase(self) -> None:
        module = self._module()

        self.assertTrue(
            module._phase_is_current(
                'current_phase: "V014_S13_P1_POST_REMEDIATION_FINANCIAL_OPERATING_REPORT"'
            )
        )
        self.assertFalse(
            module._phase_is_current('current_phase: "V014_S13_P2_COLLECTION_RECEIVABLE_AGING"')
        )


if __name__ == "__main__":
    unittest.main()
