import importlib
import unittest

from KMFA.tools.project_cost_page_runtime import (
    REQUIRED_COST_CATEGORIES,
    REQUIRED_PROJECT_TABLE_COLUMNS,
)


class TestV014S11P3PostRemediationProjectCostPage(unittest.TestCase):
    def _validate(self):
        try:
            module = importlib.import_module(
                "KMFA.tools.check_v014_s11_p3_post_remediation_project_cost_page"
            )
        except ModuleNotFoundError as exc:
            self.fail(f"missing S11-P3 post-remediation implementation: {exc}")
        return module.validate_v014_s11_p3_post_remediation_project_cost_page(
            require_private_evidence=True,
            require_browser_evidence=True,
        )

    def test_current_state_replaces_stale_pending_twelve(self) -> None:
        manifest = self._validate()
        summary = manifest["summary"]

        self.assertEqual(summary["stage_id"], "S11")
        self.assertEqual(summary["roadmap_phase_id"], "S11-P3")
        self.assertEqual(summary["current_data_quality_grade"], "Q4")
        self.assertEqual(summary["current_report_grade"], "D")
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertEqual(summary["open_final_difference_accepted_count"], 3)
        self.assertEqual(summary["nonzero_delta_reconciliation_count"], 9)
        self.assertEqual(summary["zero_delta_reconciliation_count"], 2)
        self.assertEqual(summary["incomplete_reconciliation_count"], 1)
        self.assertTrue(summary["historical_pending_twelve_recomputed"])
        self.assertFalse(summary["contains_stale_pending_twelve"])
        self.assertFalse(summary["contains_b_grade"])
        self.assertNotIn("pending_reconciliation_count", summary)

    def test_project_slots_cover_required_dimensions_without_false_attribution(self) -> None:
        manifest = self._validate()
        summary = manifest["summary"]
        projects = manifest["project_rows"]

        self.assertEqual(summary["project_row_count"], 4)
        self.assertEqual(summary["project_list_columns"], list(REQUIRED_PROJECT_TABLE_COLUMNS))
        self.assertEqual(summary["project_list_column_count"], 7)
        self.assertEqual(summary["cost_categories"], list(REQUIRED_COST_CATEGORIES))
        self.assertEqual(summary["cost_category_count"], 9)
        self.assertEqual(summary["margin_record_count"], 4)
        self.assertEqual(summary["cost_component_materialization_count"], 8)
        self.assertTrue(all(row["project_specific_allocation_status"] == "not_publicly_attributed" for row in projects))
        self.assertTrue(all(row["project_specific_difference_count"] is None for row in projects))
        self.assertTrue(all(row["contains_raw_business_values"] is False for row in projects))
        self.assertTrue(all(row["formal_report_allowed"] is False for row in projects))

    def test_project_details_show_current_evidence_and_pending_items(self) -> None:
        manifest = self._validate()
        interaction = manifest["interaction_contract"]

        self.assertTrue(interaction["project_search_enabled"])
        self.assertTrue(interaction["project_detail_click_enabled"])
        self.assertEqual(interaction["project_detail_button_count"], 4)
        self.assertEqual(interaction["detail_panel_fields"], ["来源证据", "待处理事项", "报告预览"])
        self.assertGreaterEqual(interaction["current_evidence_label_count"], 5)
        self.assertTrue(interaction["global_pending_items_visible"])
        self.assertTrue(interaction["project_level_false_attribution_blocked"])
        self.assertFalse(interaction["persistent_business_write_allowed"])
        self.assertFalse(interaction["raw_layer_write_allowed"])

    def test_restricted_report_preview_keeps_quality_gate_visible(self) -> None:
        manifest = self._validate()
        summary = manifest["summary"]
        quality = manifest["quality_gate"]

        self.assertTrue(summary["report_preview_direct_view_allowed"])
        self.assertEqual(summary["report_section_count"], 4)
        self.assertEqual(summary["restricted_report_link_count"], 1)
        self.assertEqual(summary["public_appendix_link_count"], 1)
        self.assertEqual(quality["current_report_grade"], "D")
        self.assertEqual(quality["decision"], "NO_GO")
        self.assertTrue(quality["restricted_internal_preview_allowed"])
        self.assertFalse(quality["quality_grade_bypass_allowed"])
        self.assertFalse(quality["complete_trusted_report_display_allowed"])
        self.assertFalse(quality["formal_report_allowed"])
        self.assertFalse(quality["business_decision_basis_allowed"])

    def test_browser_evidence_covers_project_and_report_flow(self) -> None:
        browser = self._validate()["browser_review"]

        self.assertEqual(browser["baseline_file_count"], 6)
        self.assertEqual(browser["baseline_control_row_count"], 54)
        self.assertEqual(browser["baseline_fail_count"], 0)
        self.assertEqual(browser["current_html_file_count"], 1)
        self.assertEqual(browser["current_html_fail_count"], 0)
        self.assertGreaterEqual(browser["current_html_control_row_count"], 18)
        self.assertEqual(browser["viewport_check_count"], 2)
        self.assertEqual(browser["search_interaction_count"], 4)
        self.assertEqual(browser["project_detail_interaction_count"], 8)
        self.assertEqual(browser["report_section_interaction_count"], 8)
        self.assertEqual(browser["report_preview_open_count"], 2)
        self.assertEqual(browser["report_preview_close_count"], 2)
        self.assertEqual(browser["keyboard_interaction_count"], 2)
        self.assertEqual(browser["linked_artifact_http_check_count"], 4)
        self.assertEqual(browser["console_error_count"], 0)
        self.assertEqual(browser["horizontal_overflow_count"], 0)

    def test_raw_and_downstream_boundaries_remain_closed(self) -> None:
        manifest = self._validate()
        summary = manifest["summary"]
        boundaries = manifest["phase_boundaries"]

        self.assertEqual(summary["raw_source_file_count"], 5)
        self.assertTrue(summary["raw_snapshot_exact_match"])
        self.assertTrue(summary["raw_cross_phase_snapshot_exact_match"])
        self.assertTrue(boundaries["s11_p1_dependency_validated"])
        self.assertTrue(boundaries["s11_p2_dependency_validated"])
        self.assertTrue(boundaries["s11_p3_performed"])
        for key in (
            "stage11_review_performed",
            "s12_p1_performed",
            "github_upload_performed",
            "app_reinstall_performed",
            "formal_report_release_performed",
            "business_execution_performed",
            "persistent_business_write_performed",
        ):
            self.assertFalse(boundaries[key])

    def test_frozen_phase_validator_survives_later_global_phase(self) -> None:
        module = importlib.import_module(
            "KMFA.tools.check_v014_s11_p3_post_remediation_project_cost_page"
        )

        self.assertTrue(
            module._phase_is_current(
                'current_phase: "V014_S11_P3_POST_REMEDIATION_PROJECT_COST_PAGE"'
            )
        )
        self.assertFalse(
            module._phase_is_current(
                'current_phase: "V014_S11_POST_REMEDIATION_STAGE_REVIEW"'
            )
        )


if __name__ == "__main__":
    unittest.main()
