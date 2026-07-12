import unittest

from KMFA.tools.check_v014_s16_p1_subcontract_procurement import (
    validate_v014_s16_p1_subcontract_procurement,
)
from KMFA.tools.v014_s16_p1_subcontract_procurement import generate


class V014S16P1SubcontractProcurementTests(unittest.TestCase):
    def test_locks_subcontract_procurement_baseline_without_execution_or_upload(self) -> None:
        manifest = generate()
        validated = validate_v014_s16_p1_subcontract_procurement()

        self.assertEqual(manifest, validated)
        self.assertEqual(validated["project_id"], "KMFA")
        self.assertEqual(validated["version"], "0.1.4")
        self.assertEqual(validated["stage_id"], "S16")
        self.assertEqual(validated["phase_id"], "S16-P1")
        self.assertEqual(validated["phase_scope"], "v014_s16_p1_subcontract_procurement_only")
        self.assertEqual(validated["task_id"], "KMFA-V014-S16-P1-SUBCONTRACT-PROCUREMENT-20260705")
        self.assertEqual(validated["acceptance_ids"], ["ACC-V014-S16-P1-SUBCONTRACT-PROCUREMENT"])
        self.assertEqual(validated["completed_task_ids"], ["S16P1T01", "S16P1T02", "S16P1T03"])
        self.assertTrue(validated["s15_stage_review_dependency_validated"])
        self.assertTrue(validated["historical_s16_p1_public_safe_baseline_validated"])

        progress = validated["stage16_phase_progress"]
        self.assertEqual(progress["completed_phase_count"], 1)
        self.assertEqual(progress["total_phase_count"], 3)
        self.assertEqual(progress["derived_percent_label"], "33.33%")
        self.assertTrue(progress["s16_p1_performed"])
        self.assertFalse(progress["s16_p2_performed"])
        self.assertFalse(progress["s16_p3_performed"])
        self.assertFalse(progress["stage16_review_performed"])

        summary = validated["subcontract_procurement_summary"]
        self.assertEqual(summary["source_lane_count"], 4)
        self.assertEqual(summary["project_match_count"], 5)
        self.assertEqual(summary["unallocated_cost_pool_count"], 2)
        self.assertEqual(summary["anomaly_candidate_count"], 4)
        self.assertEqual(summary["duplicate_payment_candidate_count"], 2)
        self.assertEqual(summary["cross_project_cost_candidate_count"], 2)
        self.assertEqual(summary["pending_reconciliation_count"], 12)
        self.assertEqual(summary["report_grade_visible"], "D")
        self.assertEqual(summary["procurement_execution_count"], 0)
        self.assertEqual(summary["payment_execution_count"], 0)
        self.assertEqual(summary["bank_operation_count"], 0)

        quality = validated["quality_gate"]
        self.assertTrue(quality["subcontract_aggregation_signal_allowed"])
        self.assertTrue(quality["unallocated_cost_pool_review_required"])
        self.assertTrue(quality["duplicate_payment_candidates_review_required"])
        self.assertTrue(quality["cross_project_candidates_review_required"])
        self.assertFalse(quality["formal_report_allowed"])
        self.assertFalse(quality["business_decision_basis_allowed"])
        self.assertFalse(quality["procurement_execution_allowed"])
        self.assertFalse(quality["payment_approval_allowed"])
        self.assertFalse(quality["payment_execution_allowed"])
        self.assertFalse(quality["bank_operation_allowed"])
        self.assertFalse(quality["s16_p2_allowed"])
        self.assertFalse(quality["s16_p3_allowed"])
        self.assertFalse(quality["stage16_review_allowed"])
        self.assertFalse(quality["github_upload_allowed"])

        boundaries = validated["phase_boundaries"]
        self.assertTrue(boundaries["s16_p1_subcontract_procurement_scope_included"])
        self.assertFalse(boundaries["s16_p2_project_status_scope_included"])
        self.assertFalse(boundaries["s16_p3_customer_analysis_scope_included"])
        self.assertFalse(boundaries["stage16_review_scope_included"])
        self.assertFalse(boundaries["github_upload_scope_included"])
        self.assertFalse(boundaries["payment_execution_scope_included"])
        self.assertFalse(boundaries["business_execution_scope_included"])

        raw_boundary = validated["raw_data_boundary"]
        self.assertFalse(raw_boundary["raw_inbox_read_by_this_phase"])
        self.assertFalse(raw_boundary["raw_inbox_listed_by_this_phase"])
        self.assertFalse(raw_boundary["raw_inbox_mutated_by_this_phase"])

        upload = validated["github_upload"]
        self.assertFalse(upload["github_upload_performed"])
        self.assertFalse(upload["github_upload_ready_next_gate"])
        self.assertTrue(upload["github_upload_deferred_until_v014_stage1_18_complete"])
        self.assertEqual(validated["next_phase"], "S16-P2")


if __name__ == "__main__":
    unittest.main()
