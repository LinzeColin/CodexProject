from __future__ import annotations

import unittest

from KMFA.tools import v014_s15_p3_post_remediation_salary_boundary as phase
from KMFA.tools.check_v014_s15_p3_post_remediation_salary_boundary import (
    validate_v014_s15_p3_post_remediation_salary_boundary,
)


class V014S15P3PostRemediationSalaryBoundaryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = validate_v014_s15_p3_post_remediation_salary_boundary(
            require_private_evidence=True,
            require_browser_evidence=True,
            require_final_evidence=True,
        )
        cls.summary = cls.manifest["summary"]

    def test_identity_and_current_s15_p2_dependency_are_locked(self) -> None:
        self.assertEqual(self.manifest["phase_id"], phase.PHASE_ID)
        self.assertEqual(self.manifest["roadmap_phase_id"], "S15-P3")
        self.assertEqual(self.manifest["task_id"], phase.TASK_ID)
        self.assertEqual(self.manifest["acceptance_id"], phase.ACCEPTANCE_ID)
        self.assertEqual(self.manifest["version"], phase.VERSION)
        self.assertTrue(self.manifest["s15_p2_post_remediation_dependency_validated"])
        self.assertTrue(self.manifest["historical_s15_p3_fixture_validated"])
        self.assertFalse(self.manifest["historical_s15_p3_dynamic_rows_are_authoritative"])
        self.assertTrue(self.manifest["historical_four_readiness_rows_quarantined"])
        self.assertTrue(self.manifest["historical_sixteen_review_refs_quarantined"])

    def test_fact_output_interface_is_schema_only_and_has_no_records(self) -> None:
        self.assertEqual(self.summary["fact_output_interface_contract_count"], 1)
        self.assertEqual(self.summary["fact_output_interface_field_count"], 6)
        self.assertEqual(self.summary["source_performance_fact_row_count"], 0)
        self.assertEqual(self.summary["interface_payload_record_count"], 0)
        self.assertEqual(self.summary["project_reference_count"], 0)
        self.assertEqual(self.summary["employee_reference_count"], 0)
        interface = self.manifest["fact_output_interface_contract"]
        self.assertEqual(interface["payload_records"], [])
        self.assertEqual(interface["interface_mode"], "schema_only_no_records")
        self.assertFalse(interface["live_read_enabled"])
        self.assertFalse(interface["api_endpoint_created"])
        self.assertFalse(interface["connector_enabled"])
        self.assertFalse(interface["file_export_created"])
        self.assertFalse(interface["scheduled_sync_enabled"])
        self.assertFalse(interface["external_write_enabled"])

    def test_future_salary_read_draft_is_zero_record_and_blocked(self) -> None:
        self.assertEqual(self.summary["future_salary_read_draft_count"], 1)
        self.assertEqual(self.summary["future_salary_field_mapping_count"], 6)
        self.assertEqual(self.summary["future_salary_readiness_record_count"], 0)
        self.assertEqual(self.summary["salary_numeric_value_count"], 0)
        draft = self.manifest["future_salary_read_draft"]
        self.assertEqual(draft["readiness_records"], [])
        self.assertEqual(draft["current_status"], "draft_blocked_no_authoritative_fact_rows")
        self.assertFalse(draft["future_read_enabled"])
        self.assertFalse(draft["salary_calculation_allowed"])
        self.assertFalse(draft["bonus_approval_allowed"])
        self.assertFalse(draft["payroll_export_allowed"])

    def test_four_human_boundaries_remain_manual(self) -> None:
        self.assertEqual(self.summary["human_boundary_checkpoint_count"], 4)
        self.assertEqual(self.summary["human_approval_completed_count"], 0)
        self.assertEqual(self.summary["automatic_approval_count"], 0)
        self.assertEqual(self.summary["payment_release_count"], 0)
        self.assertEqual(self.summary["payment_execution_count"], 0)
        self.assertEqual(
            [row["checkpoint_key"] for row in self.manifest["human_boundaries"]],
            list(phase.HUMAN_CHECKPOINT_KEYS),
        )
        for row in self.manifest["human_boundaries"]:
            self.assertTrue(row["human_action_required"])
            self.assertEqual(row["current_status"], "not_performed")
            self.assertFalse(row["automatic_execution_allowed"])

    def test_current_source_and_raw_snapshots_remain_exact(self) -> None:
        self.assertEqual(self.summary["required_field_count"], 6)
        self.assertEqual(self.summary["s15_p2_field_review_item_count"], 6)
        self.assertEqual(self.summary["s15_p2_performance_fact_row_count"], 0)
        self.assertEqual(self.summary["raw_source_file_count"], 5)
        self.assertEqual(self.summary["private_xlsx_container_count"], 48)
        self.assertEqual(self.summary["private_parseable_xlsx_count"], 25)
        self.assertEqual(self.summary["private_unparseable_xlsx_count"], 23)
        self.assertEqual(self.summary["private_parseable_sheet_count"], 4198)
        self.assertEqual(self.summary["private_unique_candidate_sheet_count"], 13)
        self.assertEqual(self.summary["private_probe_roundtrip_mismatch_count"], 0)
        self.assertTrue(self.summary["raw_snapshot_exact_match"])
        self.assertTrue(self.summary["raw_cross_phase_snapshot_exact_match"])

    def test_html_human_flow_is_current_and_mobile_safe(self) -> None:
        self.assertEqual(self.summary["workbench_html_count"], 1)
        self.assertEqual(self.summary["browser_status"], "PASS")
        self.assertEqual(self.summary["baseline_html_control_row_count"], 54)
        self.assertEqual(
            self.summary["current_html_control_row_count"],
            self.summary["current_html_pass_count"],
        )
        self.assertEqual(self.summary["browser_viewport_check_count"], 2)
        self.assertEqual(self.summary["interface_field_interaction_check_count"], 12)
        self.assertEqual(self.summary["dependency_link_http_check_count"], 4)
        self.assertEqual(self.summary["dependency_navigation_check_count"], 4)
        self.assertEqual(self.summary["console_error_count"], 0)
        self.assertEqual(self.summary["horizontal_overflow_count"], 0)

    def test_quality_and_downstream_boundaries_remain_closed(self) -> None:
        self.assertEqual(self.summary["current_data_quality_grade"], "Q4")
        self.assertEqual(self.summary["current_report_grade"], "D")
        self.assertEqual(self.summary["decision"], "NO_GO")
        self.assertEqual(self.summary["open_final_difference_accepted_count"], 3)
        self.assertEqual(self.summary["nonzero_delta_reconciliation_count"], 9)
        self.assertEqual(self.summary["zero_delta_reconciliation_count"], 2)
        self.assertEqual(self.summary["incomplete_reconciliation_count"], 1)
        self.assertTrue(self.summary["s15_p1_performed"])
        self.assertTrue(self.summary["s15_p2_performed"])
        self.assertTrue(self.summary["s15_p3_performed"])
        for key in (
            "stage15_review_performed",
            "salary_calculation_performed",
            "bonus_approval_performed",
            "payroll_export_performed",
            "final_compensation_decision_performed",
            "final_payment_performed",
            "github_upload_performed",
            "app_reinstall_performed",
            "formal_report_release_performed",
            "business_execution_performed",
        ):
            self.assertFalse(self.summary[key])

    def test_public_private_and_governance_contracts_are_enforced(self) -> None:
        self.assertEqual(self.manifest["public_repo_safety"], phase._public_safety())
        self.assertEqual(self.manifest["raw_boundary"], phase._raw_boundary())
        self.assertEqual(self.manifest["phase_boundaries"], phase._phase_boundaries())
        self.assertEqual(self.manifest["quality_gate"], phase._quality_gate())
        self.assertEqual(self.manifest["acceptance_matrix"]["check_fail_count"], 0)
        self.assertFalse(self.manifest["go_no_go"]["live_salary_integration_allowed"])
        self.assertEqual(self.manifest["formula_id"], phase.FORMULA_ID)
        self.assertEqual(self.manifest["parameter_ids"], list(phase.PARAMETER_IDS))
        self.assertEqual(self.manifest["model_registry_key"], phase.MODEL_REGISTRY_KEY)
        self.assertEqual(self.manifest["next_phase"], "S15_STAGE_REVIEW")


if __name__ == "__main__":
    unittest.main()
