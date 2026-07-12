from __future__ import annotations

import unittest

from KMFA.tools import v014_s15_p2_post_remediation_performance_review_list as phase
from KMFA.tools.check_v014_s15_p2_post_remediation_performance_review_list import (
    validate_v014_s15_p2_post_remediation_performance_review_list,
)


class V014S15P2PostRemediationPerformanceReviewListTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = validate_v014_s15_p2_post_remediation_performance_review_list(
            require_private_evidence=True,
            require_browser_evidence=True,
            require_final_evidence=True,
        )
        cls.summary = cls.manifest["summary"]

    def test_identity_and_current_s15_p1_dependency_are_locked(self) -> None:
        self.assertEqual(self.manifest["phase_id"], phase.PHASE_ID)
        self.assertEqual(self.manifest["roadmap_phase_id"], "S15-P2")
        self.assertEqual(self.manifest["task_id"], phase.TASK_ID)
        self.assertEqual(self.manifest["acceptance_id"], phase.ACCEPTANCE_ID)
        self.assertEqual(self.manifest["version"], phase.VERSION)
        self.assertTrue(self.manifest["s15_p1_post_remediation_dependency_validated"])
        self.assertTrue(self.manifest["historical_s15_p2_fixture_validated"])
        self.assertFalse(self.manifest["historical_s15_p2_dynamic_rows_are_authoritative"])
        self.assertTrue(self.manifest["historical_four_fact_rows_quarantined"])
        self.assertTrue(self.manifest["historical_sixteen_review_items_quarantined"])

    def test_public_safe_fact_table_has_schema_without_invented_rows(self) -> None:
        self.assertEqual(self.summary["performance_fact_table_schema_count"], 1)
        self.assertEqual(self.summary["performance_fact_table_column_count"], 6)
        self.assertEqual(self.summary["performance_fact_row_count"], 0)
        self.assertEqual(self.summary["authoritative_project_row_count"], 0)
        self.assertEqual(self.summary["authoritative_value_binding_count"], 0)
        self.assertEqual(self.summary["synthetic_project_row_count"], 0)
        self.assertEqual(self.summary["public_business_value_count"], 0)
        table = self.manifest["performance_fact_table"]
        self.assertEqual(table["rows"], [])
        self.assertFalse(table["row_materialization_allowed"])
        self.assertEqual(
            [column["field_key"] for column in table["columns"]],
            list(phase.FIELD_KEYS),
        )

    def test_abnormal_project_method_and_six_field_review_items_are_emitted(self) -> None:
        self.assertEqual(self.summary["abnormal_project_method_count"], 1)
        self.assertEqual(self.summary["abnormal_project_rule_count"], 6)
        self.assertEqual(self.summary["actual_abnormal_project_count"], 0)
        self.assertEqual(self.summary["field_review_item_count"], 6)
        self.assertEqual(self.summary["manual_review_required_item_count"], 6)
        self.assertEqual(self.summary["project_specific_review_item_count"], 0)
        self.assertEqual(
            self.manifest["abnormal_project_method"]["current_output_status"],
            "blocked_no_authoritative_project_rows",
        )
        for row in self.manifest["review_items"]:
            self.assertEqual(row["scope_type"], "field_level_authoritative_binding_review")
            self.assertTrue(row["manual_review_required"])
            self.assertEqual(row["current_status"], "pending_authoritative_binding")
            self.assertNotIn("project_ref", row)
            self.assertFalse(row["abnormal_project_claimed"])
            self.assertFalse(row["salary_or_bonus_action_allowed"])

    def test_current_source_and_raw_snapshots_remain_exact(self) -> None:
        self.assertEqual(self.summary["required_field_count"], 6)
        self.assertEqual(self.summary["s15_p1_manual_review_required_field_count"], 6)
        self.assertEqual(self.summary["s15_p1_materialized_performance_fact_count"], 0)
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
        self.assertEqual(self.summary["review_item_interaction_check_count"], 12)
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
        for key in (
            "s15_p3_performed",
            "stage15_review_performed",
            "salary_calculation_performed",
            "bonus_approval_performed",
            "payroll_export_performed",
            "github_upload_performed",
            "app_reinstall_performed",
            "formal_report_release_performed",
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

    def test_governance_is_registered_once(self) -> None:
        self.assertEqual(self.manifest["formula_id"], phase.FORMULA_ID)
        self.assertEqual(self.manifest["parameter_ids"], list(phase.PARAMETER_IDS))
        self.assertEqual(self.manifest["model_registry_key"], phase.MODEL_REGISTRY_KEY)
        self.assertEqual(self.manifest["next_phase"], "S15-P3")


if __name__ == "__main__":
    unittest.main()
