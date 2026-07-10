import importlib
import unittest

from KMFA.tools.home_navigation_runtime import REQUIRED_NAVIGATION_LABELS


class TestV014S11P1PostRemediationHomeNavigation(unittest.TestCase):
    def _validate(self):
        try:
            module = importlib.import_module(
                "KMFA.tools.check_v014_s11_p1_post_remediation_home_navigation"
            )
        except ModuleNotFoundError as exc:
            self.fail(f"missing S11-P1 post-remediation implementation: {exc}")
        return module.validate_v014_s11_p1_post_remediation_home_navigation(
            require_private_evidence=True,
            require_browser_evidence=True,
        )

    def test_current_stage10_state_replaces_stale_home_state(self) -> None:
        summary = self._validate()["summary"]

        self.assertEqual(summary["stage_id"], "S11")
        self.assertEqual(summary["roadmap_phase_id"], "S11-P1")
        self.assertEqual(summary["current_data_quality_grade"], "Q4")
        self.assertEqual(summary["current_report_grade"], "D")
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertEqual(summary["open_final_difference_accepted_count"], 3)
        self.assertEqual(summary["nonzero_delta_reconciliation_count"], 9)
        self.assertEqual(summary["zero_delta_reconciliation_count"], 2)
        self.assertEqual(summary["incomplete_reconciliation_count"], 1)
        self.assertNotIn("pending_reconciliation_count", summary)

    def test_all_eight_required_modules_have_real_single_page_navigation(self) -> None:
        manifest = self._validate()
        summary = manifest["summary"]
        records = manifest["navigation_modules"]

        self.assertEqual(summary["required_navigation_labels"], list(REQUIRED_NAVIGATION_LABELS))
        self.assertEqual(summary["navigation_module_count"], 8)
        self.assertEqual(summary["navigation_view_count"], 8)
        self.assertEqual(summary["nav_button_count"], 8)
        self.assertEqual(summary["module_action_button_count"], 8)
        self.assertEqual(len(records), 8)
        self.assertEqual([record["visible_label"] for record in records], list(REQUIRED_NAVIGATION_LABELS))
        self.assertEqual(len({record["route_hash"] for record in records}), 8)
        self.assertTrue(all(record["visible_feedback_required"] for record in records))

    def test_current_report_links_are_safe_and_future_historical_links_are_removed(self) -> None:
        summary = self._validate()["summary"]

        self.assertEqual(summary["report_link_count"], 4)
        self.assertEqual(summary["unique_report_target_count"], 2)
        self.assertEqual(summary["current_stage_page_link_count"], 2)
        self.assertEqual(summary["current_stage_page_target_count"], 2)
        self.assertEqual(summary["unavailable_future_target_link_count"], 0)
        self.assertTrue(summary["restricted_report_links_preserve_s10_grade"])
        self.assertFalse(summary["contains_stale_pending_twelve"])
        self.assertFalse(summary["contains_b_grade"])

    def test_brand_language_and_release_boundary_are_visible(self) -> None:
        manifest = self._validate()
        summary = manifest["summary"]
        quality = manifest["quality_gate"]

        self.assertTrue(summary["km_brand_mark_present"])
        self.assertFalse(summary["single_k_brand_mark_present"])
        self.assertTrue(summary["blue_business_style"])
        self.assertTrue(summary["all_chinese_visible_copy"])
        self.assertEqual(summary["visible_feedback_panel_count"], 1)
        self.assertFalse(quality["complete_trusted_report_display_allowed"])
        self.assertFalse(quality["formal_report_allowed"])
        self.assertFalse(quality["business_decision_basis_allowed"])
        self.assertFalse(quality["business_execution_allowed"])

    def test_browser_evidence_covers_every_navigation_and_action(self) -> None:
        browser = self._validate()["browser_review"]

        self.assertEqual(browser["baseline_file_count"], 6)
        self.assertEqual(browser["baseline_control_row_count"], 54)
        self.assertEqual(browser["baseline_fail_count"], 0)
        self.assertEqual(browser["current_html_file_count"], 1)
        self.assertEqual(browser["current_html_fail_count"], 0)
        self.assertGreaterEqual(browser["current_html_control_row_count"], 13)
        self.assertEqual(browser["viewport_check_count"], 2)
        self.assertEqual(browser["navigation_interaction_count"], 16)
        self.assertEqual(browser["module_action_interaction_count"], 16)
        self.assertEqual(browser["keyboard_navigation_check_count"], 4)
        self.assertEqual(browser["report_link_http_check_count"], 4)
        self.assertEqual(browser["current_stage_page_link_http_check_count"], 2)
        self.assertEqual(browser["visible_no_go_viewport_count"], 2)
        self.assertEqual(browser["console_error_count"], 0)
        self.assertEqual(browser["horizontal_overflow_count"], 0)

    def test_frozen_phase_validator_survives_later_global_phase(self) -> None:
        module = importlib.import_module(
            "KMFA.tools.check_v014_s11_p1_post_remediation_home_navigation"
        )

        self.assertTrue(
            module._phase_is_current(
                'current_phase: "V014_S11_P1_POST_REMEDIATION_HOME_NAVIGATION"'
            )
        )
        self.assertFalse(
            module._phase_is_current(
                'current_phase: "V014_S11_POST_REMEDIATION_STAGE_REVIEW"'
            )
        )

    def test_raw_and_phase_boundaries_remain_closed(self) -> None:
        manifest = self._validate()
        summary = manifest["summary"]
        boundaries = manifest["phase_boundaries"]

        self.assertEqual(summary["raw_source_file_count"], 5)
        self.assertTrue(summary["raw_snapshot_exact_match"])
        self.assertTrue(summary["raw_cross_phase_snapshot_exact_match"])
        self.assertTrue(boundaries["s11_p1_performed"])
        for key in (
            "s11_p2_performed",
            "s11_p3_performed",
            "stage11_review_performed",
            "github_upload_performed",
            "app_reinstall_performed",
            "formal_report_release_performed",
            "business_execution_performed",
        ):
            self.assertFalse(boundaries[key])


if __name__ == "__main__":
    unittest.main()
