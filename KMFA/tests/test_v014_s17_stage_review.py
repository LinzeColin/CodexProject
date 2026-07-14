import unittest

from KMFA.tools.check_v014_s17_stage_review import validate_v014_s17_stage_review
from KMFA.tools.v014_s17_stage_review import generate


class V014S17StageReviewTests(unittest.TestCase):
    def test_reviews_all_s17_phases_without_s18_upload_or_operations(self) -> None:
        manifest = generate(generated_at="2026-07-05T15:40:00+10:00")
        validated = validate_v014_s17_stage_review()

        self.assertEqual(manifest, validated)
        self.assertEqual(validated["schema_version"], "kmfa.v014_s17_stage_review.v1")
        self.assertEqual(validated["project_id"], "KMFA")
        self.assertEqual(validated["version"], "0.1.4")
        self.assertEqual(validated["stage_id"], "S17")
        self.assertEqual(validated["phase_id"], "S17_STAGE_REVIEW")
        self.assertEqual(validated["review_scope"], "v014_s17_stage_review_only")
        self.assertEqual(validated["task_id"], "KMFA-V014-S17-STAGE-REVIEW-20260705")
        self.assertEqual(validated["acceptance_ids"], ["ACC-V014-S17-STAGE-REVIEW"])
        self.assertEqual(validated["completed_task_ids"], ["S17REVT01", "S17REVT02", "S17REVT03"])

        self.assertTrue(validated["stage_review_performed"])
        self.assertEqual(validated["phase_results"], {"S17-P1": "PASS", "S17-P2": "PASS", "S17-P3": "PASS"})
        self.assertEqual(validated["review_findings_summary"]["open_finding_count"], 0)
        self.assertGreaterEqual(validated["review_findings_summary"]["fixed_finding_count"], 1)

        progress = validated["stage17_phase_progress"]
        self.assertEqual(progress["completed_phase_count"], 3)
        self.assertEqual(progress["total_phase_count"], 3)
        self.assertEqual(progress["derived_percent_bps"], 10000)
        self.assertEqual(progress["derived_percent_label"], "100.00%")
        self.assertTrue(progress["s17_p1_performed"])
        self.assertTrue(progress["s17_p2_performed"])
        self.assertTrue(progress["s17_p3_performed"])
        self.assertTrue(progress["stage17_review_performed"])

        gate = validated["stage_gate"]
        self.assertEqual(gate["role_count"], 4)
        self.assertEqual(gate["sensitive_policy_category_count"], 15)
        self.assertEqual(gate["audit_action_type_count"], 5)
        self.assertEqual(gate["notification_rule_count"], 3)
        self.assertEqual(gate["notification_event_count"], 3)
        self.assertEqual(gate["notification_dispatch_log_count"], 3)
        self.assertEqual(gate["trigger_type_count"], 3)
        self.assertEqual(gate["operation_runbook_count"], 4)
        self.assertEqual(gate["knowledge_item_count"], 2)
        self.assertEqual(gate["drill_log_count"], 2)
        self.assertEqual(gate["production_restore_count"], 0)
        self.assertEqual(gate["external_service_call_count"], 0)
        self.assertEqual(gate["live_connector_call_count"], 0)
        self.assertEqual(gate["app_reinstall_count"], 0)
        self.assertEqual(gate["real_notification_delivery_count"], 0)
        self.assertEqual(gate["full_report_email_body_count"], 0)
        self.assertEqual(gate["report_attachment_count"], 0)
        self.assertEqual(gate["recipient_address_plaintext_count"], 0)
        self.assertEqual(gate["formal_report_count"], 0)
        self.assertEqual(gate["business_decision_basis_count"], 0)
        self.assertEqual(gate["business_execution_count"], 0)
        self.assertEqual(gate["raw_inbox_access_count"], 0)
        self.assertEqual(gate["current_report_grade"], "D")
        self.assertEqual(gate["release_permission"], "blocked")

        release = validated["release_state"]
        for key in (
            "delivery_allowed",
            "formal_report_allowed",
            "business_decision_basis_allowed",
            "notification_delivery_allowed",
            "full_report_email_allowed",
            "report_attachment_allowed",
            "recipient_address_plaintext_allowed",
            "external_connector_allowed",
            "production_restore_allowed",
            "live_connector_allowed",
            "app_reinstall_allowed",
            "business_execution_allowed",
            "github_main_upload_allowed",
        ):
            self.assertFalse(release[key], key)

        raw_boundary = validated["raw_data_boundary"]
        self.assertFalse(raw_boundary["raw_inbox_read_by_this_review"])
        self.assertFalse(raw_boundary["raw_inbox_listed_by_this_review"])
        self.assertFalse(raw_boundary["raw_inbox_stat_by_this_review"])
        self.assertFalse(raw_boundary["raw_inbox_hashed_by_this_review"])
        self.assertFalse(raw_boundary["raw_inbox_mutated_by_this_review"])
        self.assertTrue(raw_boundary["s17_p1_raw_inbox_all_false"])
        self.assertTrue(raw_boundary["s17_p2_raw_inbox_all_false"])
        self.assertTrue(raw_boundary["s17_p3_raw_inbox_all_false"])

        self.assertFalse(validated["s18_p1_performed"])
        self.assertFalse(validated["github_upload_performed"])
        self.assertEqual(validated["github_upload_status"], "not_uploaded_deferred_until_v014_stage1_18_complete")
        self.assertTrue(validated["github_upload_deferred_until_v014_stage1_18_complete"])
        self.assertEqual(validated["next_phase"], "S18-P1")


if __name__ == "__main__":
    unittest.main()
