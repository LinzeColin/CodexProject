import unittest

from KMFA.tools.check_v014_s16_p2_project_status_lifecycle import (
    validate_v014_s16_p2_project_status_lifecycle,
)
from KMFA.tools.v014_s16_p2_project_status_lifecycle import generate


class V014S16P2ProjectStatusLifecycleTests(unittest.TestCase):
    def test_locks_project_status_lifecycle_without_site_signature_or_upload(self) -> None:
        manifest = generate()
        validated = validate_v014_s16_p2_project_status_lifecycle()

        self.assertEqual(manifest, validated)
        self.assertEqual(validated["project_id"], "KMFA")
        self.assertEqual(validated["version"], "0.1.4")
        self.assertEqual(validated["stage_id"], "S16")
        self.assertEqual(validated["phase_id"], "S16-P2")
        self.assertEqual(validated["phase_scope"], "v014_s16_p2_project_status_lifecycle_only")
        self.assertEqual(validated["task_id"], "KMFA-V014-S16-P2-PROJECT-STATUS-LIFECYCLE-20260705")
        self.assertEqual(validated["acceptance_ids"], ["ACC-V014-S16-P2-PROJECT-STATUS-LIFECYCLE"])
        self.assertEqual(validated["completed_task_ids"], ["S16P2T01", "S16P2T02", "S16P2T03"])
        self.assertTrue(validated["s16_p1_dependency_validated"])
        self.assertTrue(validated["historical_s16_p2_public_safe_baseline_validated"])

        progress = validated["stage16_phase_progress"]
        self.assertEqual(progress["completed_phase_count"], 2)
        self.assertEqual(progress["total_phase_count"], 3)
        self.assertEqual(progress["derived_percent_label"], "66.67%")
        self.assertTrue(progress["s16_p1_performed"])
        self.assertTrue(progress["s16_p2_performed"])
        self.assertFalse(progress["s16_p3_performed"])
        self.assertFalse(progress["stage16_review_performed"])

        summary = validated["project_status_lifecycle_summary"]
        self.assertEqual(summary["source_lane_count"], 6)
        self.assertEqual(summary["lifecycle_record_count"], 4)
        self.assertEqual(summary["exception_item_count"], 3)
        self.assertEqual(summary["handoff_guard_count"], 3)
        self.assertEqual(summary["completed_not_settled_count"], 1)
        self.assertEqual(summary["settled_not_invoiced_count"], 1)
        self.assertEqual(summary["invoiced_not_collected_count"], 1)
        self.assertEqual(summary["pending_reconciliation_count"], 12)
        self.assertEqual(summary["report_grade_visible"], "D")
        self.assertEqual(summary["site_operation_count"], 0)
        self.assertEqual(summary["signature_operation_count"], 0)
        self.assertEqual(summary["invoice_issuance_count"], 0)
        self.assertEqual(summary["collection_action_count"], 0)
        self.assertEqual(summary["business_decision_basis_count"], 0)

        quality = validated["quality_gate"]
        self.assertTrue(quality["project_status_lifecycle_signal_allowed"])
        self.assertTrue(quality["owner_or_authorized_delegate_review_required"])
        self.assertFalse(quality["formal_report_allowed"])
        self.assertFalse(quality["business_decision_basis_allowed"])
        self.assertFalse(quality["site_construction_instruction_allowed"])
        self.assertFalse(quality["site_operation_allowed"])
        self.assertFalse(quality["safety_signature_allowed"])
        self.assertFalse(quality["technical_acceptance_signature_allowed"])
        self.assertFalse(quality["settlement_confirmation_allowed"])
        self.assertFalse(quality["invoice_issuance_allowed"])
        self.assertFalse(quality["collection_action_allowed"])
        self.assertFalse(quality["payment_execution_allowed"])
        self.assertFalse(quality["bank_operation_allowed"])
        self.assertFalse(quality["s16_p3_allowed"])
        self.assertFalse(quality["stage16_review_allowed"])
        self.assertFalse(quality["github_upload_allowed"])

        boundaries = validated["phase_boundaries"]
        self.assertTrue(boundaries["s16_p1_dependency_reused"])
        self.assertTrue(boundaries["s16_p2_project_status_scope_included"])
        self.assertFalse(boundaries["s16_p3_customer_analysis_scope_included"])
        self.assertFalse(boundaries["stage16_review_scope_included"])
        self.assertFalse(boundaries["github_upload_scope_included"])
        self.assertFalse(boundaries["site_construction_scope_included"])
        self.assertFalse(boundaries["safety_signature_scope_included"])
        self.assertFalse(boundaries["technical_signature_scope_included"])
        self.assertFalse(boundaries["business_execution_scope_included"])

        raw_alignment = validated["raw_private_alignment"]
        self.assertTrue(raw_alignment["raw_private_alignment_attempted_by_this_phase"])
        self.assertTrue(raw_alignment["raw_inbox_readonly_contract_preserved"])
        self.assertFalse(raw_alignment["raw_business_values_committed"])
        self.assertFalse(raw_alignment["raw_file_names_committed"])
        self.assertFalse(raw_alignment["raw_hashes_committed"])
        self.assertFalse(raw_alignment["field_header_plaintext_committed"])
        self.assertFalse(raw_alignment["raw_inbox_mutated_by_this_phase"])
        self.assertEqual(
            raw_alignment["private_runtime_report_ref"],
            "KMFA/.codex_private_runtime/v014_s16_p2_project_status_lifecycle/raw_alignment_report.json",
        )

        upload = validated["github_upload"]
        self.assertFalse(upload["github_upload_performed"])
        self.assertFalse(upload["github_upload_ready_next_gate"])
        self.assertTrue(upload["github_upload_deferred_until_v014_stage1_18_complete"])
        self.assertEqual(validated["next_phase"], "S16-P3")


if __name__ == "__main__":
    unittest.main()
