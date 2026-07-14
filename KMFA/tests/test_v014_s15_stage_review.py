import unittest

from KMFA.tools.check_v014_s15_stage_review import validate_v014_s15_stage_review
from KMFA.tools.v014_s15_stage_review import generate


class V014S15StageReviewTests(unittest.TestCase):
    def test_reviews_all_s15_phases_without_upload_s16_or_compensation_actions(self) -> None:
        manifest = generate()
        validated = validate_v014_s15_stage_review()

        self.assertEqual(manifest, validated)
        self.assertEqual(validated["project_id"], "KMFA")
        self.assertEqual(validated["version"], "0.1.4")
        self.assertEqual(validated["stage_id"], "S15")
        self.assertEqual(validated["phase_id"], "S15_STAGE_REVIEW")
        self.assertEqual(validated["review_scope"], "v014_s15_stage_review_only")
        self.assertEqual(validated["task_id"], "KMFA-V014-S15-STAGE-REVIEW-20260705")
        self.assertEqual(validated["acceptance_ids"], ["ACC-V014-S15-STAGE-REVIEW"])

        self.assertTrue(validated["stage_review_performed"])
        self.assertEqual(validated["phase_results"], {"S15-P1": "PASS", "S15-P2": "PASS", "S15-P3": "PASS"})
        self.assertEqual(validated["review_findings_summary"]["open_finding_count"], 0)
        self.assertGreaterEqual(validated["review_findings_summary"]["fixed_finding_count"], 1)

        progress = validated["stage15_phase_progress"]
        self.assertEqual(progress["completed_phase_count"], 3)
        self.assertEqual(progress["total_phase_count"], 3)
        self.assertEqual(progress["derived_percent_label"], "100.00%")
        self.assertTrue(progress["s15_p1_performed"])
        self.assertTrue(progress["s15_p2_performed"])
        self.assertTrue(progress["s15_p3_performed"])
        self.assertTrue(progress["stage15_review_performed"])

        gate = validated["stage_gate"]
        self.assertEqual(gate["field_definition_count"], 6)
        self.assertEqual(gate["field_binding_count"], 6)
        self.assertEqual(gate["manual_review_field_count"], 4)
        self.assertEqual(gate["performance_fact_row_count"], 4)
        self.assertEqual(gate["abnormal_review_item_count"], 16)
        self.assertEqual(gate["fact_output_interface_contract_count"], 1)
        self.assertEqual(gate["future_salary_system_readiness_row_count"], 4)
        self.assertEqual(gate["human_approval_boundary_count"], 4)
        self.assertEqual(gate["pending_review_item_count"], 16)
        self.assertEqual(gate["salary_calculation_count"], 0)
        self.assertEqual(gate["wage_calculation_count"], 0)
        self.assertEqual(gate["bonus_approval_count"], 0)
        self.assertEqual(gate["payroll_export_count"], 0)
        self.assertEqual(gate["final_compensation_decision_count"], 0)
        self.assertEqual(gate["final_payment_count"], 0)
        self.assertEqual(gate["payment_execution_count"], 0)
        self.assertEqual(gate["current_report_grade"], "D")
        self.assertEqual(gate["release_permission"], "blocked")

        release = validated["release_state"]
        self.assertFalse(release["delivery_allowed"])
        self.assertFalse(release["formal_report_allowed"])
        self.assertFalse(release["business_decision_basis_allowed"])
        self.assertFalse(release["salary_calculation_allowed"])
        self.assertFalse(release["bonus_approval_allowed"])
        self.assertFalse(release["payroll_export_allowed"])
        self.assertFalse(release["final_payment_allowed"])

        raw_boundary = validated["raw_data_boundary"]
        self.assertFalse(raw_boundary["raw_inbox_read_by_this_review"])
        self.assertFalse(raw_boundary["raw_inbox_listed_by_this_review"])
        self.assertFalse(raw_boundary["raw_inbox_mutated_by_this_review"])
        self.assertTrue(raw_boundary["s15_p1_raw_inbox_all_false"])
        self.assertTrue(raw_boundary["s15_p2_raw_inbox_all_false"])
        self.assertTrue(raw_boundary["s15_p3_raw_inbox_all_false"])

        self.assertFalse(validated["s16_p1_performed"])
        self.assertFalse(validated["github_upload_performed"])
        self.assertEqual(validated["github_upload_status"], "not_uploaded_deferred_until_v014_stage1_18_complete")
        self.assertTrue(validated["github_upload_deferred_until_v014_stage1_18_complete"])
        self.assertEqual(validated["next_phase"], "S16-P1")


if __name__ == "__main__":
    unittest.main()
