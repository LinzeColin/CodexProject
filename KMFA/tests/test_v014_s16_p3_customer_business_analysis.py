import unittest

from KMFA.tools.check_v014_s16_p3_customer_business_analysis import (
    validate_v014_s16_p3_customer_business_analysis,
)
from KMFA.tools.v014_s16_p3_customer_business_analysis import generate


class V014S16P3CustomerBusinessAnalysisTests(unittest.TestCase):
    def test_locks_customer_business_analysis_without_collection_legal_or_upload(self) -> None:
        manifest = generate()
        validated = validate_v014_s16_p3_customer_business_analysis()

        self.assertEqual(manifest, validated)
        self.assertEqual(validated["project_id"], "KMFA")
        self.assertEqual(validated["version"], "0.1.4")
        self.assertEqual(validated["stage_id"], "S16")
        self.assertEqual(validated["phase_id"], "S16-P3")
        self.assertEqual(validated["phase_scope"], "v014_s16_p3_customer_business_analysis_only")
        self.assertEqual(validated["task_id"], "KMFA-V014-S16-P3-CUSTOMER-BUSINESS-ANALYSIS-20260705")
        self.assertEqual(validated["acceptance_ids"], ["ACC-V014-S16-P3-CUSTOMER-BUSINESS-ANALYSIS"])
        self.assertEqual(validated["completed_task_ids"], ["S16P3T01", "S16P3T02", "S16P3T03"])
        self.assertTrue(validated["s16_p2_dependency_validated"])
        self.assertTrue(validated["v14_taskpack_customer_line_validated"])
        self.assertTrue(validated["upstream_public_safe_fact_dependencies_validated"])

        progress = validated["stage16_phase_progress"]
        self.assertEqual(progress["completed_phase_count"], 3)
        self.assertEqual(progress["total_phase_count"], 3)
        self.assertEqual(progress["derived_percent_label"], "100.00%")
        self.assertTrue(progress["s16_p1_performed"])
        self.assertTrue(progress["s16_p2_performed"])
        self.assertTrue(progress["s16_p3_performed"])
        self.assertFalse(progress["stage16_review_performed"])

        summary = validated["customer_business_analysis_summary"]
        self.assertEqual(summary["source_lane_count"], 7)
        self.assertEqual(summary["customer_value_dimension_count"], 4)
        self.assertEqual(summary["customer_value_signal_count"], 4)
        self.assertEqual(summary["customer_risk_signal_count"], 4)
        self.assertEqual(summary["customer_summary_count"], 4)
        self.assertEqual(summary["handoff_guard_count"], 4)
        self.assertEqual(summary["pending_reconciliation_count"], 12)
        self.assertEqual(summary["report_grade_visible"], "D")
        self.assertEqual(summary["formal_report_count"], 0)
        self.assertEqual(summary["business_decision_basis_count"], 0)
        self.assertEqual(summary["customer_contact_action_count"], 0)
        self.assertEqual(summary["collection_action_count"], 0)
        self.assertEqual(summary["legal_collection_decision_count"], 0)
        self.assertEqual(summary["payment_execution_count"], 0)
        self.assertEqual(summary["bank_operation_count"], 0)

        quality = validated["quality_gate"]
        self.assertTrue(quality["customer_business_analysis_signal_allowed"])
        self.assertTrue(quality["owner_or_authorized_delegate_review_required"])
        self.assertFalse(quality["formal_report_allowed"])
        self.assertFalse(quality["business_decision_basis_allowed"])
        self.assertFalse(quality["automatic_customer_ranking_allowed"])
        self.assertFalse(quality["customer_contact_action_allowed"])
        self.assertFalse(quality["collection_action_allowed"])
        self.assertFalse(quality["legal_collection_decision_allowed"])
        self.assertFalse(quality["payment_execution_allowed"])
        self.assertFalse(quality["bank_operation_allowed"])
        self.assertFalse(quality["stage16_review_allowed"])
        self.assertFalse(quality["github_upload_allowed"])

        boundaries = validated["phase_boundaries"]
        self.assertTrue(boundaries["s16_p1_dependency_reused"])
        self.assertTrue(boundaries["s16_p2_dependency_reused"])
        self.assertTrue(boundaries["s16_p3_customer_analysis_scope_included"])
        self.assertFalse(boundaries["stage16_review_scope_included"])
        self.assertFalse(boundaries["github_upload_scope_included"])
        self.assertFalse(boundaries["formal_report_scope_included"])
        self.assertFalse(boundaries["collection_execution_scope_included"])
        self.assertFalse(boundaries["legal_execution_scope_included"])
        self.assertFalse(boundaries["business_execution_scope_included"])

        raw_alignment = validated["raw_private_alignment"]
        self.assertTrue(raw_alignment["raw_private_alignment_attempted_by_this_phase"])
        self.assertTrue(raw_alignment["raw_inbox_readonly_contract_preserved"])
        self.assertFalse(raw_alignment["raw_business_values_committed"])
        self.assertFalse(raw_alignment["raw_file_names_committed"])
        self.assertFalse(raw_alignment["raw_hashes_committed"])
        self.assertFalse(raw_alignment["field_header_plaintext_committed"])
        self.assertFalse(raw_alignment["raw_inbox_mutated_by_this_phase"])

        upload = validated["github_upload"]
        self.assertFalse(upload["github_upload_performed"])
        self.assertFalse(upload["github_upload_ready_next_gate"])
        self.assertTrue(upload["github_upload_deferred_until_v014_stage1_18_complete"])
        self.assertEqual(validated["next_phase"], "S16_STAGE_REVIEW")


if __name__ == "__main__":
    unittest.main()
