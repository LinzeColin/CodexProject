import unittest

from KMFA.tools.check_v014_s15_p3_salary_boundary import (
    validate_v014_s15_p3_salary_boundary,
)
from KMFA.tools.v014_s15_p3_salary_boundary import generate


class V014S15P3SalaryBoundaryTests(unittest.TestCase):
    def test_outputs_contract_and_readiness_draft_without_compensation_actions_or_upload(self) -> None:
        manifest = generate()
        validated = validate_v014_s15_p3_salary_boundary()

        self.assertEqual(manifest, validated)
        self.assertEqual(validated["project_id"], "KMFA")
        self.assertEqual(validated["version"], "0.1.4")
        self.assertEqual(validated["stage_id"], "S15")
        self.assertEqual(validated["phase_id"], "S15-P3")
        self.assertEqual(validated["phase_scope"], "v014_s15_p3_salary_boundary_only")
        self.assertEqual(validated["task_id"], "KMFA-V014-S15-P3-SALARY-BOUNDARY-20260705")
        self.assertEqual(validated["acceptance_ids"], ["ACC-V014-S15-P3-SALARY-BOUNDARY"])
        self.assertEqual(validated["completed_task_ids"], ["S15P3T01", "S15P3T02", "S15P3T03"])

        progress = validated["stage15_phase_progress"]
        self.assertEqual(progress["completed_phase_count"], 3)
        self.assertEqual(progress["total_phase_count"], 3)
        self.assertEqual(progress["derived_percent_label"], "100.00%")
        self.assertTrue(progress["s15_p1_performed"])
        self.assertTrue(progress["s15_p2_performed"])
        self.assertTrue(progress["s15_p3_performed"])
        self.assertFalse(progress["stage15_review_performed"])

        summary = validated["salary_boundary_summary"]
        self.assertEqual(summary["fact_output_interface_contract_count"], 1)
        self.assertEqual(summary["future_salary_system_readiness_row_count"], 4)
        self.assertEqual(summary["human_approval_boundary_count"], 4)
        self.assertEqual(summary["pending_review_item_count"], 16)
        self.assertEqual(summary["salary_calculation_count"], 0)
        self.assertEqual(summary["wage_calculation_count"], 0)
        self.assertEqual(summary["bonus_approval_count"], 0)
        self.assertEqual(summary["payroll_export_count"], 0)
        self.assertEqual(summary["final_compensation_decision_count"], 0)
        self.assertEqual(summary["final_payment_count"], 0)
        self.assertEqual(summary["payment_execution_count"], 0)
        self.assertEqual(summary["report_grade_visible"], "D")

        quality = validated["quality_gate"]
        self.assertTrue(quality["fact_output_interface_reserved"])
        self.assertTrue(quality["future_salary_system_readiness_draft_allowed"])
        self.assertTrue(quality["final_approval_must_be_human"])
        self.assertTrue(quality["payment_release_must_be_human"])
        self.assertFalse(quality["live_salary_system_integration_allowed"])
        self.assertFalse(quality["api_endpoint_allowed"])
        self.assertFalse(quality["connector_allowed"])
        self.assertFalse(quality["file_export_allowed"])
        self.assertFalse(quality["salary_calculation_allowed"])
        self.assertFalse(quality["wage_calculation_allowed"])
        self.assertFalse(quality["bonus_approval_allowed"])
        self.assertFalse(quality["payroll_export_allowed"])
        self.assertFalse(quality["final_compensation_decision_allowed"])
        self.assertFalse(quality["final_payment_allowed"])
        self.assertFalse(quality["payment_execution_allowed"])
        self.assertFalse(quality["stage15_review_allowed"])
        self.assertFalse(quality["github_upload_allowed"])

        raw_boundary = validated["raw_data_boundary"]
        self.assertFalse(raw_boundary["raw_inbox_read_by_this_phase"])
        self.assertFalse(raw_boundary["raw_inbox_listed_by_this_phase"])
        self.assertFalse(raw_boundary["raw_inbox_mutated_by_this_phase"])

        upload = validated["github_upload"]
        self.assertFalse(upload["github_upload_performed"])
        self.assertFalse(upload["github_upload_ready_next_gate"])
        self.assertTrue(upload["github_upload_deferred_until_v014_stage1_18_complete"])


if __name__ == "__main__":
    unittest.main()
