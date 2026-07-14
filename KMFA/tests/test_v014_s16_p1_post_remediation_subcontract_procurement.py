from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path("KMFA/tools/v014_s16_p1_post_remediation_subcontract_procurement.py")
CHECKER_PATH = Path("KMFA/tools/check_v014_s16_p1_post_remediation_subcontract_procurement.py")


class V014S16P1PostRemediationSubcontractProcurementTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not MODULE_PATH.is_file() or not CHECKER_PATH.is_file():
            return
        from KMFA.tools import v014_s16_p1_post_remediation_subcontract_procurement as phase
        from KMFA.tools.check_v014_s16_p1_post_remediation_subcontract_procurement import (
            validate_v014_s16_p1_post_remediation_subcontract_procurement,
        )

        cls.phase = phase
        cls.manifest = validate_v014_s16_p1_post_remediation_subcontract_procurement(
            require_private_evidence=True,
            require_browser_evidence=True,
            require_final_evidence=True,
        )
        cls.summary = cls.manifest["summary"]

    def _require_implementation(self) -> None:
        if not hasattr(self, "manifest"):
            self.skipTest("S16-P1 post-remediation implementation is not present yet")

    def test_implementation_exists(self) -> None:
        self.assertTrue(MODULE_PATH.is_file(), "S16-P1 generator is missing")
        self.assertTrue(CHECKER_PATH.is_file(), "S16-P1 validator is missing")

    def test_identity_dependency_and_legacy_quarantine(self) -> None:
        self._require_implementation()
        self.assertEqual(self.manifest["phase_id"], self.phase.PHASE_ID)
        self.assertEqual(self.manifest["roadmap_phase_id"], "S16-P1")
        self.assertEqual(self.manifest["task_id"], self.phase.TASK_ID)
        self.assertEqual(self.manifest["acceptance_id"], self.phase.ACCEPTANCE_ID)
        self.assertEqual(self.manifest["version"], self.phase.VERSION)
        self.assertTrue(self.manifest["stage15_post_remediation_review_dependency_validated"])
        self.assertTrue(self.manifest["historical_s16_p1_fixture_validated"])
        self.assertFalse(self.manifest["historical_s16_p1_dynamic_state_is_authoritative"])
        self.assertTrue(self.manifest["historical_five_project_matches_quarantined"])
        self.assertTrue(self.manifest["historical_two_unallocated_items_quarantined"])
        self.assertTrue(self.manifest["historical_four_anomaly_candidates_quarantined"])

    def test_private_probe_and_public_structure_are_exactly_aligned(self) -> None:
        self._require_implementation()
        self.assertEqual(self.summary["raw_source_file_count"], 5)
        self.assertEqual(self.summary["private_xlsx_container_count"], 48)
        self.assertEqual(self.summary["private_parseable_xlsx_count"], 25)
        self.assertEqual(self.summary["private_unparseable_xlsx_count"], 23)
        self.assertEqual(self.summary["private_parseable_sheet_count"], 4198)
        self.assertEqual(self.summary["private_candidate_covered_lane_count"], 5)
        self.assertEqual(self.summary["private_unique_candidate_sheet_count"], 1335)
        self.assertEqual(self.summary["private_candidate_lane_association_count"], 1647)
        self.assertEqual(self.summary["private_multi_lane_candidate_sheet_count"], 274)
        self.assertEqual(self.summary["private_probe_roundtrip_mismatch_count"], 0)
        self.assertEqual(self.summary["processed_candidate_sheet_count"], 1335)
        self.assertEqual(self.summary["processed_candidate_lane_association_count"], 1647)
        self.assertTrue(self.summary["processed_private_structure_alignment_exact"])
        self.assertEqual(
            self.summary["private_candidate_sheet_count_by_lane"],
            {
                "invoice": 672,
                "payment_application": 391,
                "procurement_order": 296,
                "project_attribution": 5,
                "subcontract_contract": 283,
            },
        )

    def test_spreadsheet_parser_runtime_is_available_and_probe_fails_closed(self) -> None:
        self._require_implementation()
        runtime = self.phase._spreadsheet_python()
        self.assertTrue(self.phase._python_has_module(runtime, "openpyxl"))
        with patch.object(self.phase, "_python_has_module", return_value=False):
            with self.assertRaisesRegex(RuntimeError, "openpyxl parser runtime is required"):
                self.phase._raw_candidate_probe(Path("."))

    def test_source_lanes_and_detection_rules_cover_the_roadmap(self) -> None:
        self._require_implementation()
        self.assertEqual(self.summary["source_lane_count"], 5)
        self.assertEqual(
            {row["lane_id"] for row in self.manifest["source_lanes"]},
            {
                "subcontract_contract",
                "procurement_order",
                "payment_application",
                "invoice",
                "project_attribution",
            },
        )
        self.assertEqual(self.summary["detection_rule_count"], 4)
        self.assertEqual(
            {row["rule_id"] for row in self.manifest["detection_rules"]},
            {
                "unallocated_cost",
                "duplicate_payment",
                "payment_without_contract",
                "cross_project_cost",
            },
        )
        self.assertTrue(all(row["manual_review_required"] for row in self.manifest["source_lanes"]))
        self.assertTrue(all(row["manual_review_required"] for row in self.manifest["detection_rules"]))

    def test_no_transaction_or_anomaly_is_invented_without_row_binding(self) -> None:
        self._require_implementation()
        self.assertEqual(self.summary["project_matching_contract_count"], 1)
        self.assertEqual(self.summary["project_matching_component_count"], 6)
        self.assertEqual(self.summary["authoritative_row_binding_count"], 0)
        self.assertEqual(self.summary["authoritative_value_binding_count"], 0)
        self.assertEqual(self.summary["materialized_transaction_record_count"], 0)
        self.assertEqual(self.summary["project_match_record_count"], 0)
        self.assertEqual(self.summary["unallocated_cost_pool_item_count"], 0)
        self.assertEqual(self.summary["anomaly_candidate_count"], 0)
        self.assertEqual(self.summary["duplicate_payment_candidate_count"], 0)
        self.assertEqual(self.summary["payment_without_contract_candidate_count"], 0)
        self.assertEqual(self.summary["cross_project_cost_candidate_count"], 0)
        self.assertEqual(self.summary["public_business_value_count"], 0)
        self.assertFalse(self.manifest["project_matching_contract"]["candidate_materialization_allowed"])

    def test_workbench_is_mobile_safe_and_interactive(self) -> None:
        self._require_implementation()
        self.assertEqual(self.summary["workbench_html_count"], 1)
        self.assertEqual(self.summary["baseline_html_pass_count"], 54)
        self.assertEqual(
            self.summary["current_html_pass_count"],
            self.summary["current_html_control_row_count"],
        )
        self.assertGreater(self.summary["current_html_control_row_count"], 0)
        self.assertEqual(self.summary["browser_viewport_check_count"], 2)
        self.assertEqual(self.summary["lane_interaction_check_count"], 10)
        self.assertEqual(self.summary["rule_interaction_check_count"], 8)
        self.assertEqual(self.summary["dependency_link_http_check_count"], 4)
        self.assertEqual(self.summary["dependency_navigation_check_count"], 4)
        self.assertEqual(self.summary["console_error_count"], 0)
        self.assertEqual(self.summary["horizontal_overflow_count"], 0)

    def test_raw_snapshots_remain_exact(self) -> None:
        self._require_implementation()
        self.assertTrue(self.summary["raw_snapshot_exact_match"])
        self.assertTrue(self.summary["raw_cross_phase_snapshot_exact_match"])

    def test_quality_and_downstream_actions_remain_closed(self) -> None:
        self._require_implementation()
        self.assertEqual(self.summary["current_data_quality_grade"], "Q4")
        self.assertEqual(self.summary["current_report_grade"], "D")
        self.assertEqual(self.summary["decision"], "NO_GO")
        self.assertEqual(self.summary["open_final_difference_accepted_count"], 3)
        self.assertEqual(self.summary["nonzero_delta_reconciliation_count"], 9)
        self.assertEqual(self.summary["zero_delta_reconciliation_count"], 2)
        self.assertEqual(self.summary["incomplete_reconciliation_count"], 1)
        self.assertTrue(self.summary["s16_p1_performed"])
        for key in (
            "s16_p2_performed",
            "s16_p3_performed",
            "stage16_review_performed",
            "procurement_execution_performed",
            "payment_approval_performed",
            "payment_execution_performed",
            "bank_operation_performed",
            "github_upload_performed",
            "app_reinstall_performed",
            "formal_report_release_performed",
            "difference_closure_performed",
            "business_execution_performed",
        ):
            self.assertFalse(self.summary[key])

    def test_governance_and_next_run_boundary_are_locked(self) -> None:
        self._require_implementation()
        self.assertEqual(self.manifest["formula_id"], self.phase.FORMULA_ID)
        self.assertEqual(self.manifest["parameter_ids"], list(self.phase.PARAMETER_IDS))
        self.assertEqual(self.manifest["model_registry_key"], self.phase.MODEL_REGISTRY_KEY)
        self.assertEqual(self.manifest["public_repo_safety"], self.phase._public_safety())
        self.assertEqual(self.manifest["phase_boundaries"], self.phase._phase_boundaries())
        self.assertEqual(self.manifest["acceptance_matrix"]["check_fail_count"], 0)
        self.assertEqual(self.manifest["next_phase"], "S16-P2")
        self.assertFalse(self.manifest["go_no_go"]["s16_p2_allowed_in_this_run"])
        self.assertFalse(self.manifest["go_no_go"]["github_upload_allowed"])


if __name__ == "__main__":
    unittest.main()
