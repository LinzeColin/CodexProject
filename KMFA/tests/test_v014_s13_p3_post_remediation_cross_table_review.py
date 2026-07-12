import importlib
import unittest


class TestV014S13P3PostRemediationCrossTableReview(unittest.TestCase):
    def _module(self):
        try:
            return importlib.import_module(
                "KMFA.tools.check_v014_s13_p3_post_remediation_cross_table_review"
            )
        except ModuleNotFoundError as exc:
            self.fail(f"missing current S13-P3 implementation: {exc}")

    def _validate(self):
        return self._module().validate_v014_s13_p3_post_remediation_cross_table_review(
            require_private_evidence=True,
            require_browser_evidence=True,
            require_final_evidence=True,
        )

    def test_current_s13_p2_is_the_only_dynamic_dependency(self) -> None:
        manifest = self._validate()
        summary = manifest["summary"]

        self.assertEqual(summary["stage_id"], "S13")
        self.assertEqual(summary["roadmap_phase_id"], "S13-P3")
        self.assertTrue(manifest["s13_p2_dependency_validated"])
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

    def test_four_dimensions_are_not_comparable_without_row_binding(self) -> None:
        manifest = self._validate()
        summary = manifest["summary"]
        checks = manifest["review_checks"]

        self.assertEqual(summary["review_dimension_count"], 4)
        self.assertEqual(summary["comparable_dimension_count"], 0)
        self.assertEqual(summary["exact_comparison_performed_count"], 0)
        self.assertEqual(summary["proven_match_dimension_count"], 0)
        self.assertEqual(summary["proven_mismatch_dimension_count"], 0)
        self.assertEqual(summary["not_comparable_dimension_count"], 4)
        self.assertEqual(
            {row["review_dimension"] for row in checks},
            {
                "project_consistency",
                "customer_consistency",
                "amount_consistency",
                "time_consistency",
            },
        )
        for check in checks:
            self.assertTrue(check["public_structure_evidence_present"])
            self.assertFalse(check["shared_row_binding_proven"])
            self.assertFalse(check["exact_comparison_performed"])
            self.assertEqual(check["review_result"], "NOT_COMPARABLE")
            self.assertTrue(check["difference_queue_required"])
            self.assertFalse(check["business_conclusion_allowed"])
        amount_check = next(row for row in checks if row["review_dimension"] == "amount_consistency")
        self.assertEqual(amount_check["money_tolerance_minor_units"], 0)
        self.assertFalse(amount_check["one_cent_difference_ignored"])

    def test_public_safe_queue_has_required_contract_with_null_amounts(self) -> None:
        manifest = self._validate()
        summary = manifest["summary"]
        queue = manifest["difference_queue"]
        required_keys = {
            "difference_id",
            "source_a",
            "source_b",
            "field_name",
            "amount_a_cents",
            "amount_b_cents",
            "delta_cents",
            "reason_candidate",
            "impact_scope",
            "resolution_status",
            "reviewer",
            "created_at",
            "closed_at",
        }

        self.assertEqual(summary["difference_queue_count"], 4)
        self.assertTrue(summary["difference_queue_is_non_additive"])
        for row in queue:
            self.assertTrue(required_keys.issubset(row))
            self.assertIsNone(row["amount_a_cents"])
            self.assertIsNone(row["amount_b_cents"])
            self.assertIsNone(row["delta_cents"])
            self.assertEqual(row["resolution_status"], "pending_evidence_not_comparable")
            self.assertFalse(row["queue_item_is_additive_to_global_difference_counts"])
            self.assertFalse(row["auto_resolution_allowed"])
            self.assertFalse(row["contains_source_identity"])
            self.assertFalse(row["contains_field_plaintext"])
            self.assertFalse(row["contains_business_amounts"])

    def test_quality_report_preserves_d_no_go_and_no_business_conclusion(self) -> None:
        manifest = self._validate()
        summary = manifest["summary"]
        quality = manifest["quality_report"]

        self.assertEqual(summary["quality_report_count"], 1)
        self.assertEqual(summary["quality_html_count"], 1)
        self.assertEqual(quality["cross_table_review_status"], "insufficient_row_level_evidence")
        self.assertEqual(quality["current_report_grade"], "D")
        self.assertEqual(quality["decision"], "NO_GO")
        self.assertEqual(quality["comparison_completion_ratio_bps"], 0)
        self.assertFalse(quality["formal_report_allowed"])
        self.assertFalse(quality["business_decision_basis_allowed"])
        self.assertFalse(quality["difference_closure_allowed"])
        self.assertFalse(quality["business_execution_allowed"])

    def test_private_diagnostic_and_raw_snapshots_are_locked(self) -> None:
        manifest = self._validate()
        summary = manifest["summary"]
        raw = manifest["raw_boundary"]

        self.assertEqual(summary["raw_source_file_count"], 5)
        self.assertEqual(summary["private_dimension_diagnostic_count"], 4)
        self.assertTrue(summary["raw_snapshot_exact_match"])
        self.assertTrue(summary["raw_cross_phase_snapshot_exact_match"])
        self.assertTrue(raw["raw_read_authorized"])
        self.assertTrue(raw["private_cross_table_diagnostic_generated"])
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

        self.assertTrue(manifest["historical_s13_p3_policy_fixture_validated"])
        self.assertFalse(manifest["historical_s13_p3_dynamic_state_is_authoritative"])
        self.assertTrue(manifest["historical_pending_twelve_quarantined"])
        self.assertTrue(manifest["historical_completed_review_claim_quarantined"])

    def test_browser_review_covers_quality_workbench_and_dependencies(self) -> None:
        browser = self._validate()["browser_review"]

        self.assertEqual(browser["baseline_pass_count"], 54)
        self.assertEqual(browser["baseline_warn_count"], 0)
        self.assertEqual(browser["baseline_fail_count"], 0)
        self.assertEqual(browser["current_page_count"], 1)
        self.assertEqual(browser["viewport_check_count"], 2)
        self.assertEqual(browser["dimension_interaction_check_count"], 4)
        self.assertEqual(browser["dependency_link_http_check_count"], 3)
        self.assertEqual(browser["dependency_navigation_check_count"], 3)
        self.assertEqual(browser["console_error_count"], 0)
        self.assertEqual(browser["horizontal_overflow_count"], 0)

    def test_stage_review_release_and_business_boundaries_remain_closed(self) -> None:
        manifest = self._validate()
        boundaries = manifest["phase_boundaries"]
        quality = manifest["quality_gate"]

        self.assertTrue(boundaries["s13_p1_performed"])
        self.assertTrue(boundaries["s13_p2_performed"])
        self.assertTrue(boundaries["s13_p3_performed"])
        for key in (
            "stage13_review_performed",
            "s14_p1_performed",
            "github_upload_performed",
            "app_reinstall_performed",
            "formal_report_release_performed",
            "business_execution_performed",
            "persistent_business_write_performed",
        ):
            self.assertFalse(boundaries[key])
        self.assertTrue(quality["cross_table_review_evidence_allowed"])
        self.assertTrue(quality["difference_queue_output_allowed"])
        self.assertTrue(quality["operating_report_quality_report_allowed"])
        self.assertFalse(quality["formal_report_allowed"])
        self.assertFalse(quality["business_decision_basis_allowed"])
        self.assertFalse(quality["difference_auto_resolution_allowed"])
        self.assertFalse(quality["stage13_review_allowed"])

    def test_validator_survives_later_global_phase(self) -> None:
        module = self._module()

        self.assertTrue(
            module._phase_is_current(
                'current_phase: "V014_S13_P3_POST_REMEDIATION_CROSS_TABLE_REVIEW"'
            )
        )
        self.assertFalse(
            module._phase_is_current('current_phase: "V014_S13_POST_REMEDIATION_STAGE_REVIEW"')
        )


if __name__ == "__main__":
    unittest.main()
