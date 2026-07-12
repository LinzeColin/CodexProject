import unittest

from KMFA.tools.check_v014_s16_stage_review import validate_v014_s16_stage_review
from KMFA.tools.v014_s16_stage_review import generate


class V014S16StageReviewTests(unittest.TestCase):
    def test_reviews_all_s16_phases_without_upload_s17_or_business_actions(self) -> None:
        manifest = generate()
        validated = validate_v014_s16_stage_review()

        self.assertEqual(manifest, validated)
        self.assertEqual(validated["project_id"], "KMFA")
        self.assertEqual(validated["version"], "0.1.4")
        self.assertEqual(validated["stage_id"], "S16")
        self.assertEqual(validated["phase_id"], "S16_STAGE_REVIEW")
        self.assertEqual(validated["review_scope"], "v014_s16_stage_review_only")
        self.assertEqual(validated["task_id"], "KMFA-V014-S16-STAGE-REVIEW-20260705")
        self.assertEqual(validated["acceptance_ids"], ["ACC-V014-S16-STAGE-REVIEW"])

        self.assertTrue(validated["stage_review_performed"])
        self.assertEqual(validated["phase_results"], {"S16-P1": "PASS", "S16-P2": "PASS", "S16-P3": "PASS"})
        self.assertEqual(validated["review_findings_summary"]["open_finding_count"], 0)
        self.assertGreaterEqual(validated["review_findings_summary"]["fixed_finding_count"], 1)

        progress = validated["stage16_phase_progress"]
        self.assertEqual(progress["completed_phase_count"], 3)
        self.assertEqual(progress["total_phase_count"], 3)
        self.assertEqual(progress["derived_percent_bps"], 10000)
        self.assertEqual(progress["derived_percent_label"], "100.00%")
        self.assertTrue(progress["s16_p1_performed"])
        self.assertTrue(progress["s16_p2_performed"])
        self.assertTrue(progress["s16_p3_performed"])
        self.assertTrue(progress["stage16_review_performed"])

        gate = validated["stage_gate"]
        self.assertEqual(gate["source_lane_total_count"], 17)
        self.assertEqual(gate["subcontract_source_lane_count"], 4)
        self.assertEqual(gate["project_status_source_lane_count"], 6)
        self.assertEqual(gate["customer_business_source_lane_count"], 7)
        self.assertEqual(gate["project_match_count"], 5)
        self.assertEqual(gate["unallocated_cost_pool_count"], 2)
        self.assertEqual(gate["anomaly_candidate_count"], 4)
        self.assertEqual(gate["duplicate_payment_candidate_count"], 2)
        self.assertEqual(gate["cross_project_cost_candidate_count"], 2)
        self.assertEqual(gate["lifecycle_record_count"], 4)
        self.assertEqual(gate["exception_item_count"], 3)
        self.assertEqual(gate["lifecycle_handoff_guard_count"], 3)
        self.assertEqual(gate["customer_value_signal_count"], 4)
        self.assertEqual(gate["customer_risk_signal_count"], 4)
        self.assertEqual(gate["customer_summary_count"], 4)
        self.assertEqual(gate["customer_handoff_guard_count"], 4)
        self.assertEqual(gate["pending_reconciliation_count"], 12)
        self.assertEqual(gate["formal_report_count"], 0)
        self.assertEqual(gate["business_decision_basis_count"], 0)
        self.assertEqual(gate["procurement_execution_count"], 0)
        self.assertEqual(gate["payment_approval_count"], 0)
        self.assertEqual(gate["payment_execution_count"], 0)
        self.assertEqual(gate["bank_operation_count"], 0)
        self.assertEqual(gate["site_operation_count"], 0)
        self.assertEqual(gate["signature_operation_count"], 0)
        self.assertEqual(gate["invoice_issuance_count"], 0)
        self.assertEqual(gate["customer_contact_action_count"], 0)
        self.assertEqual(gate["collection_action_count"], 0)
        self.assertEqual(gate["legal_collection_decision_count"], 0)
        self.assertEqual(gate["current_report_grade"], "D")
        self.assertEqual(gate["release_permission"], "blocked")

        release = validated["release_state"]
        for key in (
            "delivery_allowed",
            "formal_report_allowed",
            "business_decision_basis_allowed",
            "procurement_execution_allowed",
            "payment_approval_allowed",
            "payment_execution_allowed",
            "bank_operation_allowed",
            "site_operation_allowed",
            "signature_operation_allowed",
            "invoice_issuance_allowed",
            "customer_contact_action_allowed",
            "collection_action_allowed",
            "legal_collection_decision_allowed",
        ):
            self.assertFalse(release[key], key)

        raw_boundary = validated["raw_data_boundary"]
        self.assertFalse(raw_boundary["raw_inbox_read_by_this_review"])
        self.assertFalse(raw_boundary["raw_inbox_listed_by_this_review"])
        self.assertFalse(raw_boundary["raw_inbox_mutated_by_this_review"])
        self.assertTrue(raw_boundary["s16_p1_raw_inbox_all_false"])
        self.assertTrue(raw_boundary["s16_p2_raw_private_alignment_readonly"])
        self.assertTrue(raw_boundary["s16_p3_raw_private_alignment_readonly"])

        self.assertFalse(validated["s17_p1_performed"])
        self.assertFalse(validated["github_upload_performed"])
        self.assertEqual(validated["github_upload_status"], "not_uploaded_deferred_until_v014_stage1_18_complete")
        self.assertTrue(validated["github_upload_deferred_until_v014_stage1_18_complete"])
        self.assertEqual(validated["next_phase"], "S17-P1")


if __name__ == "__main__":
    unittest.main()
