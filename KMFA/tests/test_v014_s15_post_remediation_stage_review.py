from __future__ import annotations

import unittest
from pathlib import Path


MODULE_PATH = Path("KMFA/tools/v014_s15_post_remediation_stage_review.py")
CHECKER_PATH = Path("KMFA/tools/check_v014_s15_post_remediation_stage_review.py")


class V014S15PostRemediationStageReviewTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not MODULE_PATH.is_file() or not CHECKER_PATH.is_file():
            return
        from KMFA.tools import v014_s15_post_remediation_stage_review as phase
        from KMFA.tools.check_v014_s15_post_remediation_stage_review import (
            validate_v014_s15_post_remediation_stage_review,
        )

        cls.phase = phase
        cls.manifest = validate_v014_s15_post_remediation_stage_review(
            require_private_evidence=True,
            require_browser_evidence=True,
            require_final_evidence=True,
        )
        cls.summary = cls.manifest["summary"]

    def _require_implementation(self) -> None:
        if not hasattr(self, "manifest"):
            self.skipTest("Stage 15 post-remediation review implementation is not present yet")

    def test_review_implementation_exists(self) -> None:
        self.assertTrue(MODULE_PATH.is_file(), "Stage 15 review generator is missing")
        self.assertTrue(CHECKER_PATH.is_file(), "Stage 15 review validator is missing")

    def test_identity_current_chain_and_legacy_quarantine(self) -> None:
        self._require_implementation()
        self.assertEqual(self.manifest["phase_id"], self.phase.PHASE_ID)
        self.assertEqual(self.manifest["roadmap_phase_id"], "STAGE-REVIEW")
        self.assertEqual(self.manifest["task_id"], self.phase.TASK_ID)
        self.assertEqual(self.manifest["acceptance_id"], self.phase.ACCEPTANCE_ID)
        self.assertEqual(self.manifest["version"], self.phase.VERSION)
        self.assertTrue(self.manifest["current_s15_chain_validated"])
        self.assertTrue(self.manifest["historical_s15_review_validated"])
        self.assertFalse(self.manifest["historical_s15_review_dynamic_state_is_authoritative"])
        self.assertTrue(self.manifest["historical_four_fact_rows_quarantined"])
        self.assertTrue(self.manifest["historical_four_readiness_rows_quarantined"])
        self.assertTrue(self.manifest["historical_sixteen_review_items_quarantined"])

    def test_current_phase_replay_is_complete(self) -> None:
        self._require_implementation()
        self.assertEqual(self.summary["phase_results"], {"S15-P1": "PASS", "S15-P2": "PASS", "S15-P3": "PASS"})
        self.assertEqual(self.summary["phase_focused_test_count"], 24)
        self.assertEqual(self.summary["phase_focused_test_pass_count"], 24)
        self.assertEqual(self.summary["phase_strict_validator_count"], 3)
        self.assertEqual(self.summary["phase_strict_validator_pass_count"], 3)

    def test_current_business_state_remains_public_safe_and_zero_record(self) -> None:
        self._require_implementation()
        self.assertEqual(self.summary["required_field_count"], 6)
        self.assertEqual(self.summary["manual_review_required_field_count"], 6)
        self.assertEqual(self.summary["authoritative_value_binding_count"], 0)
        self.assertEqual(self.summary["performance_fact_row_count"], 0)
        self.assertEqual(self.summary["actual_abnormal_project_count"], 0)
        self.assertEqual(self.summary["field_review_item_count"], 6)
        self.assertEqual(self.summary["interface_payload_record_count"], 0)
        self.assertEqual(self.summary["future_salary_readiness_record_count"], 0)
        self.assertEqual(self.summary["human_boundary_checkpoint_count"], 4)
        self.assertEqual(self.summary["human_approval_completed_count"], 0)
        self.assertEqual(self.summary["salary_numeric_value_count"], 0)

    def test_all_review_findings_are_fixed(self) -> None:
        self._require_implementation()
        self.assertEqual(self.summary["review_finding_count"], 10)
        self.assertEqual(self.summary["fixed_review_finding_count"], 10)
        self.assertEqual(self.summary["open_review_finding_count"], 0)
        self.assertEqual(len(self.manifest["review_findings"]), 10)
        self.assertTrue(all(row["status"] == "fixed" for row in self.manifest["review_findings"]))

    def test_three_page_human_flow_is_strongly_connected_and_mobile_safe(self) -> None:
        self._require_implementation()
        self.assertEqual(self.summary["current_stage_page_count"], 3)
        self.assertEqual(self.summary["cross_page_link_count"], 6)
        self.assertEqual(self.summary["broken_cross_page_link_count"], 0)
        self.assertTrue(self.summary["cross_page_navigation_strongly_connected"])
        self.assertEqual(self.summary["baseline_html_pass_count"], 54)
        self.assertEqual(self.summary["current_html_control_row_count"], 45)
        self.assertEqual(self.summary["current_html_pass_count"], 45)
        self.assertEqual(self.summary["browser_viewport_check_count"], 6)
        self.assertEqual(self.summary["representative_interaction_check_count"], 6)
        self.assertEqual(self.summary["cross_page_link_http_check_count"], 6)
        self.assertEqual(self.summary["cross_page_navigation_check_count"], 6)
        self.assertEqual(self.summary["console_error_count"], 0)
        self.assertEqual(self.summary["horizontal_overflow_count"], 0)

    def test_raw_snapshots_remain_exact(self) -> None:
        self._require_implementation()
        self.assertEqual(self.summary["raw_source_file_count"], 5)
        self.assertTrue(self.summary["raw_snapshot_exact_match"])
        self.assertTrue(self.summary["raw_cross_phase_snapshot_exact_match"])

    def test_quality_and_all_downstream_actions_remain_closed(self) -> None:
        self._require_implementation()
        self.assertEqual(self.summary["current_data_quality_grade"], "Q4")
        self.assertEqual(self.summary["current_report_grade"], "D")
        self.assertEqual(self.summary["decision"], "NO_GO")
        self.assertEqual(self.summary["open_final_difference_accepted_count"], 3)
        self.assertEqual(self.summary["nonzero_delta_reconciliation_count"], 9)
        self.assertEqual(self.summary["zero_delta_reconciliation_count"], 2)
        self.assertEqual(self.summary["incomplete_reconciliation_count"], 1)
        self.assertTrue(self.summary["stage15_review_performed"])
        for key in (
            "s16_p1_performed",
            "salary_calculation_performed",
            "bonus_approval_performed",
            "payroll_export_performed",
            "final_compensation_decision_performed",
            "final_payment_performed",
            "payment_execution_performed",
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
        self.assertEqual(self.manifest["review_boundaries"], self.phase._review_boundaries())
        self.assertEqual(self.manifest["acceptance_matrix"]["check_fail_count"], 0)
        self.assertEqual(self.manifest["next_phase"], "S16-P1")
        self.assertFalse(self.manifest["go_no_go"]["s16_p1_allowed_in_this_run"])
        self.assertFalse(self.manifest["go_no_go"]["github_upload_allowed"])


if __name__ == "__main__":
    unittest.main()
