import importlib
import unittest


class TestV014S12P1PostRemediationPendingActions(unittest.TestCase):
    def _module(self):
        try:
            return importlib.import_module(
                "KMFA.tools.check_v014_s12_p1_post_remediation_pending_actions"
            )
        except ModuleNotFoundError as exc:
            self.fail(f"missing S12-P1 post-remediation implementation: {exc}")

    def _validate(self):
        return self._module().validate_v014_s12_p1_post_remediation_pending_actions(
            require_private_evidence=True,
            require_browser_evidence=True,
        )

    def test_current_stage11_state_replaces_stale_pending_twelve(self) -> None:
        manifest = self._validate()
        summary = manifest["summary"]

        self.assertEqual(summary["stage_id"], "S12")
        self.assertEqual(summary["roadmap_phase_id"], "S12-P1")
        self.assertEqual(summary["current_data_quality_grade"], "Q4")
        self.assertEqual(summary["current_report_grade"], "D")
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertEqual(summary["open_final_difference_accepted_count"], 3)
        self.assertEqual(summary["nonzero_delta_reconciliation_count"], 9)
        self.assertEqual(summary["zero_delta_reconciliation_count"], 2)
        self.assertEqual(summary["incomplete_reconciliation_count"], 1)
        self.assertEqual(summary["project_specific_unknown_allocation_count"], 4)
        self.assertEqual(summary["source_check_matrix_row_count"], 13)
        self.assertEqual(summary["hard_block_count"], 12)
        self.assertNotIn("pending_reconciliation_count", summary)
        self.assertTrue(manifest["stage11_post_remediation_review_dependency_validated"])

    def test_pending_groups_are_public_safe_and_do_not_invent_attribution(self) -> None:
        manifest = self._validate()
        summary = manifest["summary"]
        groups = manifest["pending_action_groups"]

        self.assertEqual(summary["pending_action_group_count"], 6)
        self.assertEqual(len(groups), 6)
        self.assertEqual(len({group["group_id"] for group in groups}), 6)
        self.assertEqual(
            {group["manual_action_kind"] for group in groups},
            {"field_mapping", "project_matching", "difference_handling", "note"},
        )
        self.assertTrue(all(group["session_candidate_only"] for group in groups))
        self.assertTrue(all(group["project_attribution"] == "unknown_or_not_applicable" for group in groups))
        self.assertTrue(all(group["public_amount_values_committed"] is False for group in groups))
        self.assertTrue(all(group["persistent_business_write_allowed"] is False for group in groups))
        self.assertTrue(all(group["responsible_role"] for group in groups))
        self.assertTrue(all(group["status"] for group in groups))
        self.assertTrue(all(group["impact_summary"] for group in groups))
        self.assertTrue(all(group["next_step"] for group in groups))

    def test_event_templates_cover_roadmap_contract_and_append_only_reversal(self) -> None:
        manifest = self._validate()
        summary = manifest["summary"]
        templates = manifest["manual_event_templates"]
        fixture = manifest["approved_event_reversal_policy_fixture"]

        self.assertEqual(summary["manual_event_template_count"], 4)
        self.assertEqual(summary["manual_action_kind_count"], 4)
        self.assertEqual(summary["current_approved_business_event_count"], 0)
        self.assertEqual(len(templates), 4)
        self.assertEqual(
            {template["manual_action_kind"] for template in templates},
            {"field_mapping", "project_matching", "difference_handling", "note"},
        )
        required = {
            "event_id",
            "manual_action_kind",
            "actor_ref",
            "event_time_policy",
            "reason_code",
            "impact_scope",
            "event_version",
        }
        self.assertTrue(all(required <= set(template) for template in templates))
        self.assertTrue(all(template["append_only"] for template in templates))
        self.assertTrue(all(template["session_candidate_only"] for template in templates))
        self.assertTrue(all(template["approval_state"] == "draft" for template in templates))
        self.assertTrue(all(template["silent_update_allowed"] is False for template in templates))
        self.assertEqual(fixture["historical_approved_event_count"], 1)
        self.assertEqual(fixture["historical_reverse_event_count"], 1)
        self.assertTrue(fixture["reverse_chain_validated"])
        self.assertFalse(fixture["current_business_resolution_applied"])

    def test_workbench_is_searchable_filterable_and_session_only(self) -> None:
        module = importlib.import_module(
            "KMFA.tools.v014_s12_p1_post_remediation_pending_actions"
        )
        html = module.HTML_PATH.read_text(encoding="utf-8")

        for token in (
            "待处理事项",
            "处理人",
            "状态",
            "影响",
            "下一步",
            "字段映射",
            "项目匹配",
            "差异处理",
            "备注",
            "生成候选事件",
            "追加反向事件候选",
            'data-pending-search',
            'data-kind-filter',
            'data-status-filter',
            'aria-live="polite"',
        ):
            self.assertIn(token, html)
        for forbidden in (
            "localStorage",
            "sessionStorage",
            "indexedDB",
            "XMLHttpRequest",
            "fetch(",
            "data-impact",
            "data-rerun",
        ):
            self.assertNotIn(forbidden, html)

    def test_browser_evidence_covers_desktop_mobile_and_session_reset(self) -> None:
        browser = self._validate()["browser_review"]

        self.assertEqual(browser["baseline_file_count"], 6)
        self.assertEqual(browser["baseline_control_row_count"], 54)
        self.assertEqual(browser["baseline_fail_count"], 0)
        self.assertEqual(browser["current_html_file_count"], 1)
        self.assertEqual(browser["current_html_fail_count"], 0)
        self.assertEqual(browser["viewport_check_count"], 2)
        self.assertEqual(browser["search_check_count"], 2)
        self.assertEqual(browser["kind_filter_check_count"], 2)
        self.assertEqual(browser["status_filter_check_count"], 2)
        self.assertEqual(browser["row_selection_check_count"], 2)
        self.assertEqual(browser["candidate_event_check_count"], 2)
        self.assertEqual(browser["reverse_event_check_count"], 2)
        self.assertEqual(browser["reload_reset_check_count"], 2)
        self.assertEqual(browser["return_link_http_check_count"], 5)
        self.assertEqual(browser["actual_navigation_check_count"], 5)
        self.assertEqual(browser["console_error_count"], 0)
        self.assertEqual(browser["horizontal_overflow_count"], 0)

    def test_raw_and_downstream_boundaries_remain_closed(self) -> None:
        manifest = self._validate()
        summary = manifest["summary"]
        boundaries = manifest["phase_boundaries"]
        quality = manifest["quality_gate"]

        self.assertEqual(summary["raw_source_file_count"], 5)
        self.assertTrue(summary["raw_snapshot_exact_match"])
        self.assertTrue(summary["raw_cross_phase_snapshot_exact_match"])
        self.assertTrue(boundaries["s12_p1_performed"])
        for key in (
            "s12_p2_performed",
            "s12_p3_performed",
            "stage12_review_performed",
            "github_upload_performed",
            "app_reinstall_performed",
            "formal_report_release_performed",
            "persistent_business_write_performed",
            "business_execution_performed",
            "raw_write_performed",
            "raw_delete_performed",
            "raw_move_performed",
            "raw_rename_performed",
            "raw_overwrite_performed",
        ):
            self.assertFalse(boundaries[key])
        self.assertFalse(quality["impact_preview_publish_allowed"])
        self.assertFalse(quality["derived_rerun_allowed"])
        self.assertFalse(quality["formal_report_allowed"])
        self.assertFalse(quality["business_decision_basis_allowed"])

    def test_frozen_phase_validator_survives_later_global_phase(self) -> None:
        module = self._module()

        self.assertTrue(
            module._phase_is_current(
                'current_phase: "V014_S12_P1_POST_REMEDIATION_PENDING_ACTIONS"'
            )
        )
        self.assertFalse(
            module._phase_is_current(
                'current_phase: "V014_S12_P2_POST_REMEDIATION_IMPACT_PREVIEW"'
            )
        )


if __name__ == "__main__":
    unittest.main()
