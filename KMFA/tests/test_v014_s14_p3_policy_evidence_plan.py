import unittest

from KMFA.tools.check_v014_s14_p3_policy_evidence_plan import (
    validate_v014_s14_p3_policy_evidence_plan,
)
from KMFA.tools.v014_s14_p3_policy_evidence_plan import generate


class V014S14P3PolicyEvidencePlanTests(unittest.TestCase):
    def test_locks_policy_evidence_plan_without_conclusion_submission_review_or_upload(self) -> None:
        manifest = generate()
        validated = validate_v014_s14_p3_policy_evidence_plan()

        self.assertEqual(manifest, validated)
        self.assertEqual(validated["project_id"], "KMFA")
        self.assertEqual(validated["version"], "0.1.4")
        self.assertEqual(validated["stage_id"], "S14")
        self.assertEqual(validated["phase_id"], "S14-P3")
        self.assertEqual(validated["phase_scope"], "v014_s14_p3_policy_evidence_plan_only")
        self.assertEqual(validated["task_id"], "KMFA-V014-S14-P3-POLICY-EVIDENCE-PLAN-20260705")
        self.assertEqual(validated["completed_task_ids"], ["S14P3T01", "S14P3T02", "S14P3T03"])
        self.assertEqual(validated["acceptance_ids"], ["ACC-V014-S14-P3-POLICY-EVIDENCE-PLAN"])

        progress = validated["stage14_phase_progress"]
        self.assertEqual(progress["completed_phase_count"], 3)
        self.assertEqual(progress["total_phase_count"], 3)
        self.assertEqual(progress["derived_percent_label"], "100.00%")
        self.assertTrue(progress["s14_p1_performed"])
        self.assertTrue(progress["s14_p2_performed"])
        self.assertTrue(progress["s14_p3_performed"])
        self.assertFalse(progress["stage14_review_performed"])

        summary = validated["policy_evidence_summary"]
        self.assertEqual(summary["policy_program_count"], 5)
        self.assertEqual(summary["evidence_directory_count"], 5)
        self.assertEqual(summary["evidence_gap_count"], 5)
        self.assertEqual(summary["risk_tip_count"], 5)
        self.assertEqual(summary["html_output_count"], 1)
        self.assertEqual(summary["pending_reconciliation_count"], 12)
        self.assertEqual(summary["report_grade_visible"], "D")
        self.assertEqual(summary["formal_policy_conclusion_count"], 0)
        self.assertEqual(summary["policy_application_submission_count"], 0)
        self.assertEqual(summary["subsidy_application_count"], 0)
        self.assertEqual(summary["external_connector_action_count"], 0)

        upload = validated["github_upload"]
        self.assertFalse(upload["github_upload_performed"])
        self.assertFalse(upload["github_upload_ready_next_gate"])
        self.assertTrue(upload["github_upload_deferred_until_v014_stage1_18_complete"])

        raw_boundary = validated["raw_data_boundary"]
        self.assertFalse(raw_boundary["raw_inbox_read_by_this_phase"])
        self.assertFalse(raw_boundary["raw_inbox_listed_by_this_phase"])
        self.assertFalse(raw_boundary["raw_inbox_mutated_by_this_phase"])

        quality = validated["quality_gate"]
        self.assertTrue(quality["policy_evidence_directory_registration_allowed"])
        self.assertTrue(quality["evidence_gap_signal_allowed"])
        self.assertTrue(quality["risk_tip_allowed"])
        self.assertFalse(quality["formal_report_allowed"])
        self.assertFalse(quality["business_decision_basis_allowed"])
        self.assertFalse(quality["policy_qualification_conclusion_allowed"])
        self.assertFalse(quality["policy_application_submission_allowed"])
        self.assertFalse(quality["subsidy_application_allowed"])
        self.assertFalse(quality["tax_filing_allowed"])
        self.assertFalse(quality["invoice_issuance_allowed"])
        self.assertFalse(quality["payment_approval_allowed"])
        self.assertFalse(quality["bank_operation_allowed"])
        self.assertFalse(quality["loan_management_action_allowed"])
        self.assertFalse(quality["stage14_review_allowed"])
        self.assertFalse(quality["github_upload_allowed"])


if __name__ == "__main__":
    unittest.main()
