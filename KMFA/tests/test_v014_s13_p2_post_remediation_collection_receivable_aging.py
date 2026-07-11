import importlib
import unittest


class TestV014S13P2PostRemediationCollectionReceivableAging(unittest.TestCase):
    def _module(self):
        try:
            return importlib.import_module(
                "KMFA.tools.check_v014_s13_p2_post_remediation_collection_receivable_aging"
            )
        except ModuleNotFoundError as exc:
            self.fail(f"missing current S13-P2 implementation: {exc}")

    def _validate(self):
        return self._module().validate_v014_s13_p2_post_remediation_collection_receivable_aging(
            require_private_evidence=True,
            require_browser_evidence=True,
            require_final_evidence=True,
        )

    def test_current_s13_p1_is_the_only_dynamic_dependency(self) -> None:
        manifest = self._validate()
        summary = manifest["summary"]

        self.assertEqual(summary["stage_id"], "S13")
        self.assertEqual(summary["roadmap_phase_id"], "S13-P2")
        self.assertTrue(manifest["s13_p1_dependency_validated"])
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

    def test_five_required_lanes_distinguish_structure_parseability_and_binding(self) -> None:
        manifest = self._validate()
        summary = manifest["summary"]
        lanes = manifest["source_lane_status"]

        self.assertEqual(summary["source_lane_count"], 5)
        self.assertEqual(summary["structure_connected_lane_count"], 5)
        self.assertEqual(summary["row_level_binding_proven_lane_count"], 0)
        self.assertEqual(summary["private_raw_parseable_lane_count"], sum(row["private_raw_parseable"] for row in lanes))
        self.assertGreater(summary["private_raw_parseable_lane_count"], 0)
        self.assertLess(summary["private_raw_parseable_lane_count"], 5)
        self.assertEqual(
            {row["lane_id"] for row in lanes},
            {"collection_table", "receivable_aging", "customer_aging", "journal", "invoice_plan"},
        )
        for lane in lanes:
            self.assertTrue(lane["structure_connected"])
            self.assertFalse(lane["row_level_binding_proven"])
            self.assertFalse(lane["contains_source_identity"])
            self.assertFalse(lane["contains_field_plaintext"])
            self.assertFalse(lane["contains_business_amounts"])

    def test_four_issue_definitions_do_not_claim_business_items(self) -> None:
        manifest = self._validate()
        summary = manifest["summary"]
        issues = manifest["issue_definitions"]

        self.assertEqual(summary["required_issue_type_count"], 4)
        self.assertEqual(summary["issue_definition_count"], 4)
        self.assertEqual(summary["identified_business_item_count"], 0)
        self.assertEqual(summary["actionable_collection_priority_item_count"], 0)
        self.assertEqual(summary["assigned_responsibility_item_count"], 0)
        self.assertEqual(
            {row["issue_type"] for row in issues},
            {
                "invoiced_not_collected",
                "completed_not_settled",
                "settled_not_invoiced",
                "overdue_receivable",
            },
        )
        for issue in issues:
            self.assertEqual(issue["identification_status"], "definition_locked_row_level_evidence_unproven")
            self.assertEqual(issue["identified_item_count"], 0)
            self.assertEqual(issue["priority_status"], "method_only_not_business_priority")
            self.assertEqual(issue["responsibility_status"], "role_definition_only_unassigned")
            self.assertFalse(issue["business_priority_allowed"])
            self.assertFalse(issue["responsibility_assignment_allowed"])
            self.assertFalse(issue["contains_business_amounts"])

    def test_private_raw_constraints_and_difference_evidence_are_locked(self) -> None:
        manifest = self._validate()
        summary = manifest["summary"]
        raw = manifest["raw_boundary"]

        self.assertEqual(summary["raw_source_file_count"], 5)
        self.assertEqual(summary["wps_private_container_count"], 2)
        self.assertTrue(summary["raw_snapshot_exact_match"])
        self.assertTrue(summary["raw_cross_phase_snapshot_exact_match"])
        self.assertGreaterEqual(summary["private_difference_item_count"], 2)
        self.assertTrue(summary["private_workbook_structure_profile_performed"])
        self.assertTrue(raw["raw_read_authorized"])
        self.assertTrue(raw["private_workbook_structure_profile_performed"])
        self.assertTrue(raw["private_difference_report_generated"])
        for key in (
            "raw_write_performed",
            "raw_delete_performed",
            "raw_move_performed",
            "raw_rename_performed",
            "raw_overwrite_performed",
            "raw_mutation_performed",
        ):
            self.assertFalse(raw[key])

    def test_historical_static_state_is_quarantined(self) -> None:
        manifest = self._validate()

        self.assertTrue(manifest["historical_s13_p2_policy_fixture_validated"])
        self.assertFalse(manifest["historical_s13_p2_dynamic_state_is_authoritative"])
        self.assertTrue(manifest["historical_pending_twelve_quarantined"])
        self.assertTrue(manifest["historical_static_priority_and_responsibility_quarantined"])

    def test_browser_review_covers_workbench_and_four_issue_interactions(self) -> None:
        browser = self._validate()["browser_review"]

        self.assertEqual(browser["baseline_pass_count"], 54)
        self.assertEqual(browser["baseline_warn_count"], 0)
        self.assertEqual(browser["baseline_fail_count"], 0)
        self.assertEqual(browser["current_page_count"], 1)
        self.assertEqual(browser["viewport_check_count"], 2)
        self.assertEqual(browser["issue_interaction_check_count"], 4)
        self.assertEqual(browser["dependency_link_http_check_count"], 2)
        self.assertEqual(browser["dependency_navigation_check_count"], 2)
        self.assertEqual(browser["console_error_count"], 0)
        self.assertEqual(browser["horizontal_overflow_count"], 0)

    def test_downstream_release_and_business_boundaries_remain_closed(self) -> None:
        manifest = self._validate()
        boundaries = manifest["phase_boundaries"]
        quality = manifest["quality_gate"]

        self.assertTrue(boundaries["s13_p1_performed"])
        self.assertTrue(boundaries["s13_p2_performed"])
        for key in (
            "s13_p3_performed",
            "stage13_review_performed",
            "github_upload_performed",
            "app_reinstall_performed",
            "formal_report_release_performed",
            "business_execution_performed",
            "persistent_business_write_performed",
        ):
            self.assertFalse(boundaries[key])
        self.assertTrue(quality["method_definition_allowed"])
        self.assertFalse(quality["business_priority_allowed"])
        self.assertFalse(quality["responsibility_assignment_allowed"])
        self.assertFalse(quality["collection_action_allowed"])
        self.assertFalse(quality["business_decision_basis_allowed"])

    def test_validator_survives_later_global_phase(self) -> None:
        module = self._module()

        self.assertTrue(
            module._phase_is_current(
                'current_phase: "V014_S13_P2_POST_REMEDIATION_COLLECTION_RECEIVABLE_AGING"'
            )
        )
        self.assertFalse(
            module._phase_is_current('current_phase: "V014_S13_P3_FINANCIAL_ANALYSIS_PANEL"')
        )


if __name__ == "__main__":
    unittest.main()
