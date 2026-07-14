import importlib
import unittest
from pathlib import Path

from KMFA.tools.source_check_board_runtime import ALLOWED_BOARD_STATUSES, REQUIRED_BOARD_COLUMNS


class TestV014S11P2PostRemediationSourceCheckBoard(unittest.TestCase):
    def _validate(self):
        try:
            module = importlib.import_module(
                "KMFA.tools.check_v014_s11_p2_post_remediation_source_check_board"
            )
        except ModuleNotFoundError as exc:
            self.fail(f"missing S11-P2 post-remediation implementation: {exc}")
        return module.validate_v014_s11_p2_post_remediation_source_check_board(
            require_private_evidence=True,
            require_browser_evidence=True,
        )

    def test_current_quality_state_replaces_stale_pending_state(self) -> None:
        summary = self._validate()["summary"]

        self.assertEqual(summary["stage_id"], "S11")
        self.assertEqual(summary["roadmap_phase_id"], "S11-P2")
        self.assertEqual(summary["current_data_quality_grade"], "Q4")
        self.assertEqual(summary["current_report_grade"], "D")
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertEqual(summary["open_final_difference_accepted_count"], 3)
        self.assertEqual(summary["nonzero_delta_reconciliation_count"], 9)
        self.assertEqual(summary["zero_delta_reconciliation_count"], 2)
        self.assertEqual(summary["incomplete_reconciliation_count"], 1)
        self.assertFalse(summary["contains_stale_pending_twelve"])
        self.assertFalse(summary["contains_b_grade"])
        self.assertNotIn("pending_reconciliation_count", summary)

    def test_matrix_covers_required_dimensions_with_current_status_overlay(self) -> None:
        manifest = self._validate()
        summary = manifest["summary"]
        rows = manifest["source_rows"]

        self.assertEqual(summary["matrix_row_count"], 13)
        self.assertEqual(summary["required_columns"], list(REQUIRED_BOARD_COLUMNS))
        self.assertEqual(summary["required_column_count"], 11)
        self.assertEqual(summary["allowed_statuses"], list(ALLOWED_BOARD_STATUSES))
        self.assertEqual(
            summary["status_counts"],
            {"已就绪": 0, "部分/阻塞": 6, "失败/不适用": 1, "已过期": 2, "人工复核": 4},
        )
        self.assertEqual(summary["historical_ready_status_recomputed_count"], 4)
        self.assertEqual(summary["current_ready_row_count"], 0)
        self.assertEqual([row["status"] for row in rows[:4]], ["部分/阻塞", "部分/阻塞", "人工复核", "部分/阻塞"])
        self.assertTrue(all(row["status"] in ALLOWED_BOARD_STATUSES for row in rows))
        self.assertTrue(all(row["status_basis"] == "current_public_safe_evidence_overlay" for row in rows))
        self.assertTrue(all(row["contains_raw_business_values"] is False for row in rows))

    def test_status_detail_and_preview_actions_are_visible_but_session_only(self) -> None:
        manifest = self._validate()
        interaction = manifest["interaction_contract"]
        quality = manifest["quality_gate"]

        self.assertTrue(interaction["search_feedback_enabled"])
        self.assertTrue(interaction["status_filter_enabled"])
        self.assertTrue(interaction["status_click_detail_enabled"])
        self.assertEqual(interaction["detail_panel_fields"], ["影响报告", "处理规则", "下一步"])
        self.assertEqual(interaction["session_status_preview_action_count"], 5)
        self.assertTrue(interaction["session_only_control_events"])
        self.assertFalse(interaction["persistent_status_write_allowed"])
        self.assertFalse(interaction["raw_layer_write_allowed"])
        self.assertFalse(quality["complete_trusted_report_display_allowed"])
        self.assertFalse(quality["formal_report_allowed"])
        self.assertFalse(quality["business_decision_basis_allowed"])
        self.assertFalse(quality["business_execution_allowed"])

    def test_public_html_preserves_brand_language_and_release_boundary(self) -> None:
        manifest = self._validate()
        summary = manifest["summary"]

        self.assertTrue(summary["km_brand_mark_present"])
        self.assertFalse(summary["single_k_brand_mark_present"])
        self.assertTrue(summary["blue_gray_surface_dominant"])
        self.assertTrue(summary["status_badges_only"])
        self.assertEqual(summary["large_yellow_surface_count"], 0)
        self.assertTrue(summary["all_chinese_visible_copy"])
        self.assertEqual(summary["home_navigation_link_count"], 1)
        self.assertEqual(summary["project_cost_page_link_count"], 1)
        self.assertEqual(summary["current_stage_page_target_count"], 2)
        self.assertEqual(summary["visible_feedback_panel_count"], 3)
        self.assertEqual(summary["formal_report_count"], 0)
        self.assertEqual(summary["business_decision_basis_allowed_count"], 0)

    def test_browser_evidence_covers_search_filters_details_and_preview_actions(self) -> None:
        browser = self._validate()["browser_review"]

        self.assertEqual(browser["baseline_file_count"], 6)
        self.assertEqual(browser["baseline_control_row_count"], 54)
        self.assertEqual(browser["baseline_fail_count"], 0)
        self.assertEqual(browser["current_html_file_count"], 1)
        self.assertEqual(browser["current_html_fail_count"], 0)
        self.assertGreaterEqual(browser["current_html_control_row_count"], 21)
        self.assertEqual(browser["viewport_check_count"], 2)
        self.assertEqual(browser["search_interaction_count"], 4)
        self.assertEqual(browser["status_filter_interaction_count"], 10)
        self.assertEqual(browser["status_detail_interaction_count"], 26)
        self.assertEqual(browser["status_preview_interaction_count"], 10)
        self.assertEqual(browser["keyboard_interaction_count"], 2)
        self.assertEqual(browser["home_link_http_check_count"], 1)
        self.assertEqual(browser["project_cost_link_http_check_count"], 1)
        self.assertEqual(browser["console_error_count"], 0)
        self.assertEqual(browser["horizontal_overflow_count"], 0)

    def test_frozen_phase_validator_survives_later_global_phase(self) -> None:
        module = importlib.import_module(
            "KMFA.tools.check_v014_s11_p2_post_remediation_source_check_board"
        )

        self.assertTrue(
            module._phase_is_current(
                'current_phase: "V014_S11_P2_POST_REMEDIATION_SOURCE_CHECK_BOARD"'
            )
        )
        self.assertFalse(
            module._phase_is_current(
                'current_phase: "V014_S11_POST_REMEDIATION_STAGE_REVIEW"'
            )
        )

    def test_mobile_icon_links_keep_chinese_accessible_names(self) -> None:
        text = Path(
            "KMFA/stage_artifacts/V014_S11_P2_POST_REMEDIATION_SOURCE_CHECK_BOARD/"
            "exports/html/kmfa_source_check_board.html"
        ).read_text(encoding="utf-8")

        self.assertIn('data-home-link aria-label="返回经营首页" title="返回经营首页"', text)
        self.assertIn(
            'data-project-cost-link aria-label="查看项目成本页面" title="查看项目成本页面"',
            text,
        )

    def test_raw_and_downstream_phase_boundaries_remain_closed(self) -> None:
        manifest = self._validate()
        summary = manifest["summary"]
        boundaries = manifest["phase_boundaries"]

        self.assertEqual(summary["raw_source_file_count"], 5)
        self.assertTrue(summary["raw_snapshot_exact_match"])
        self.assertTrue(summary["raw_cross_phase_snapshot_exact_match"])
        self.assertTrue(boundaries["s11_p1_dependency_validated"])
        self.assertTrue(boundaries["s11_p2_performed"])
        for key in (
            "s11_p3_performed",
            "stage11_review_performed",
            "github_upload_performed",
            "app_reinstall_performed",
            "formal_report_release_performed",
            "business_execution_performed",
            "persistent_status_write_performed",
        ):
            self.assertFalse(boundaries[key])


if __name__ == "__main__":
    unittest.main()
