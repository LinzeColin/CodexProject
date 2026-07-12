from __future__ import annotations

import unittest

from KMFA.tools import v014_s15_p1_post_remediation_performance_fact_fields as phase
from KMFA.tools.check_v014_s15_p1_post_remediation_performance_fact_fields import (
    validate_v014_s15_p1_post_remediation_performance_fact_fields,
)


class V014S15P1PostRemediationPerformanceFactFieldsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = validate_v014_s15_p1_post_remediation_performance_fact_fields(
            require_private_evidence=True,
            require_browser_evidence=True,
            require_final_evidence=True,
        )
        cls.summary = cls.manifest["summary"]

    def test_identity_and_current_dependency_are_locked(self) -> None:
        self.assertEqual(self.manifest["phase_id"], phase.PHASE_ID)
        self.assertEqual(self.manifest["roadmap_phase_id"], "S15-P1")
        self.assertEqual(self.manifest["task_id"], phase.TASK_ID)
        self.assertEqual(self.manifest["acceptance_id"], phase.ACCEPTANCE_ID)
        self.assertEqual(self.manifest["version"], phase.VERSION)
        self.assertTrue(self.manifest["stage14_post_remediation_review_dependency_validated"])
        self.assertTrue(self.manifest["historical_s15_p1_fixture_validated"])
        self.assertFalse(self.manifest["historical_s15_p1_dynamic_binding_state_is_authoritative"])
        self.assertTrue(self.manifest["historical_two_non_manual_fields_quarantined"])

    def test_six_required_fields_are_defined_and_all_require_review(self) -> None:
        self.assertEqual(self.summary["required_field_count"], 6)
        self.assertEqual(self.summary["field_definition_count"], 6)
        self.assertEqual(self.summary["field_binding_status_count"], 6)
        self.assertEqual(self.summary["manual_review_required_field_count"], 6)
        self.assertEqual(self.summary["candidate_covered_field_count"], 6)
        self.assertEqual(
            self.summary["private_candidate_sheet_count_by_field"],
            {
                "invoice_amount": 9,
                "gross_margin_rate": 1,
                "settlement_speed": 2,
                "collection_speed": 4,
                "audit_variance": 2,
                "customer_relationship_rate": 2,
            },
        )

    def test_structure_references_do_not_claim_authoritative_fact_binding(self) -> None:
        self.assertEqual(self.summary["project_cost_structure_reference_connected_field_count"], 6)
        self.assertEqual(self.summary["collection_structure_reference_connected_field_count"], 6)
        self.assertEqual(self.summary["authoritative_row_binding_proven_field_count"], 0)
        self.assertEqual(self.summary["authoritative_value_binding_proven_field_count"], 0)
        self.assertEqual(self.summary["materialized_performance_fact_count"], 0)
        self.assertEqual(self.summary["public_business_value_count"], 0)
        for row in self.manifest["field_binding_statuses"]:
            self.assertTrue(row["project_cost_structure_reference_connected"])
            self.assertTrue(row["collection_structure_reference_connected"])
            self.assertFalse(row["authoritative_row_binding_proven"])
            self.assertFalse(row["authoritative_value_binding_proven"])
            self.assertFalse(row["performance_fact_materialized"])
            self.assertTrue(row["manual_review_required"])

    def test_private_probe_and_raw_snapshots_are_deterministic(self) -> None:
        self.assertEqual(self.summary["raw_source_file_count"], 5)
        self.assertEqual(self.summary["private_xlsx_container_count"], 48)
        self.assertEqual(self.summary["private_parseable_xlsx_count"], 25)
        self.assertEqual(self.summary["private_unparseable_xlsx_count"], 23)
        self.assertEqual(self.summary["private_parseable_sheet_count"], 4198)
        self.assertEqual(self.summary["private_unique_candidate_sheet_count"], 13)
        self.assertEqual(self.summary["private_multi_field_candidate_sheet_count"], 3)
        self.assertEqual(self.summary["private_probe_roundtrip_mismatch_count"], 0)
        self.assertTrue(self.summary["raw_snapshot_exact_match"])
        self.assertTrue(self.summary["raw_cross_phase_snapshot_exact_match"])

    def test_html_human_flow_is_current_and_mobile_safe(self) -> None:
        self.assertEqual(self.summary["workbench_html_count"], 1)
        self.assertEqual(self.summary["browser_status"], "PASS")
        self.assertEqual(self.summary["browser_viewport_check_count"], 2)
        self.assertEqual(self.summary["field_interaction_check_count"], 12)
        self.assertEqual(self.summary["dependency_link_http_check_count"], 4)
        self.assertEqual(self.summary["dependency_navigation_check_count"], 4)
        self.assertEqual(self.summary["console_error_count"], 0)
        self.assertEqual(self.summary["horizontal_overflow_count"], 0)
        self.assertGreater(self.summary["current_html_control_row_count"], 0)
        self.assertEqual(
            self.summary["current_html_control_row_count"],
            self.summary["current_html_pass_count"],
        )

    def test_quality_and_downstream_boundaries_remain_closed(self) -> None:
        self.assertEqual(self.summary["current_data_quality_grade"], "Q4")
        self.assertEqual(self.summary["current_report_grade"], "D")
        self.assertEqual(self.summary["decision"], "NO_GO")
        self.assertEqual(self.summary["open_final_difference_accepted_count"], 3)
        self.assertEqual(self.summary["nonzero_delta_reconciliation_count"], 9)
        self.assertEqual(self.summary["zero_delta_reconciliation_count"], 2)
        self.assertEqual(self.summary["incomplete_reconciliation_count"], 1)
        self.assertTrue(self.summary["s15_p1_performed"])
        for key in (
            "s15_p2_performed",
            "s15_p3_performed",
            "stage15_review_performed",
            "salary_calculation_performed",
            "bonus_approval_performed",
            "payroll_export_performed",
            "github_upload_performed",
            "app_reinstall_performed",
            "business_execution_performed",
        ):
            self.assertFalse(self.summary[key])

    def test_public_and_private_evidence_contracts_are_enforced(self) -> None:
        self.assertEqual(self.manifest["public_repo_safety"], phase._public_safety())
        self.assertEqual(self.manifest["raw_boundary"], phase._raw_boundary())
        self.assertEqual(self.manifest["phase_boundaries"], phase._phase_boundaries())
        self.assertEqual(self.manifest["quality_gate"], phase._quality_gate())
        self.assertEqual(self.manifest["acceptance_matrix"]["check_fail_count"], 0)
        self.assertFalse(self.manifest["go_no_go"]["performance_fact_release_allowed"])
        self.assertFalse(self.manifest["go_no_go"]["salary_or_bonus_action_allowed"])

    def test_final_validation_and_next_phase_routing_are_explicit(self) -> None:
        validation = self.manifest["validation_summary"]
        self.assertTrue(validation["final_validation_recorded"])
        for key in (
            "focused_test",
            "strict_validator",
            "browser_desktop_mobile",
            "raw_alignment",
            "governance_and_safety_scans",
        ):
            self.assertEqual(validation[key], "PASS")
        self.assertEqual(self.manifest["next_phase"], "S15-P2")
        self.assertIn("S15-P2", self.manifest["next_required_step"])
        self.assertIn("separate run", self.manifest["next_required_step"])


if __name__ == "__main__":
    unittest.main()
