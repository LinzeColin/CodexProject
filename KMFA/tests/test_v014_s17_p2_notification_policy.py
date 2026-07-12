import json
import unittest

from KMFA.tools.check_v014_s17_p2_notification_policy import (
    validate_v014_s17_p2_notification_policy,
)
from KMFA.tools.v014_s17_p2_notification_policy import (
    REQUIRED_V014_NOTIFICATION_TRIGGERS,
    generate,
)


class V014S17P2NotificationPolicyTests(unittest.TestCase):
    def test_v014_s17_p2_locks_public_safe_notification_policy_only(self) -> None:
        manifest = generate(generated_at="2026-07-05T14:30:00+10:00")
        validated = validate_v014_s17_p2_notification_policy()

        self.assertEqual(validated["schema_version"], "kmfa.v014_s17_p2_notification_policy.v1")
        self.assertEqual(validated["project_id"], "KMFA")
        self.assertEqual(validated["version"], "0.1.4")
        self.assertEqual(validated["stage_id"], "S17")
        self.assertEqual(validated["phase_id"], "S17-P2")
        self.assertEqual(validated["phase_scope"], "v014_s17_p2_notification_policy_only")
        self.assertEqual(
            validated["task_id"],
            "KMFA-V014-S17-P2-NOTIFICATION-POLICY-20260705",
        )
        self.assertEqual(validated["acceptance_ids"], ["ACC-V014-S17-P2-NOTIFICATION-POLICY"])
        self.assertEqual(validated["completed_task_ids"], ["S17P2T01", "S17P2T02", "S17P2T03"])
        self.assertEqual(tuple(validated["required_notification_triggers"]), REQUIRED_V014_NOTIFICATION_TRIGGERS)

        self.assertTrue(validated["s17_p1_dependency_validated"])
        self.assertTrue(validated["historical_s17_p2_public_safe_baseline_validated"])
        self.assertEqual(validated["historical_s17_p2_policy_version"], "KMFA-S17P2-NOTIFICATION-REMINDER-PUBLIC-SAFE-001")

        progress = validated["stage17_phase_progress"]
        self.assertEqual(progress["completed_phase_count"], 2)
        self.assertEqual(progress["total_phase_count"], 3)
        self.assertEqual(progress["derived_percent_bps"], 6667)
        self.assertEqual(progress["derived_percent_label"], "66.67%")
        self.assertTrue(progress["s17_p1_performed"])
        self.assertTrue(progress["s17_p2_performed"])
        self.assertFalse(progress["s17_p3_performed"])
        self.assertFalse(progress["stage17_review_performed"])

        summary = validated["notification_policy_summary"]
        self.assertEqual(summary["notification_rule_count"], 3)
        self.assertEqual(summary["notification_event_count"], 3)
        self.assertEqual(summary["notification_dispatch_log_count"], 3)
        self.assertEqual(summary["trigger_type_count"], 3)
        self.assertEqual(summary["real_notification_delivery_count"], 0)
        self.assertEqual(summary["full_report_email_body_count"], 0)
        self.assertEqual(summary["report_attachment_count"], 0)
        self.assertEqual(summary["recipient_address_plaintext_count"], 0)
        self.assertEqual(summary["external_connector_count"], 0)
        self.assertEqual(summary["raw_inbox_access_count"], 0)
        self.assertEqual(summary["report_grade_visible"], "D")

        quality = validated["quality_gate"]
        self.assertTrue(quality["notification_rules_complete"])
        self.assertTrue(quality["notification_events_generated"])
        self.assertTrue(quality["notification_logs_written_to_metadata"])
        self.assertTrue(quality["email_reminder_only"])
        for key in (
            "email_full_report_body_allowed",
            "email_attachment_allowed",
            "recipient_address_plaintext_allowed",
            "raw_payload_allowed",
            "external_email_connector_allowed",
            "real_notification_delivery_allowed",
            "formal_report_allowed",
            "business_decision_basis_allowed",
            "business_execution_allowed",
            "s17_p3_scope_allowed",
            "stage17_review_allowed",
            "github_upload_allowed",
        ):
            self.assertFalse(quality[key], key)

        boundaries = validated["phase_boundaries"]
        self.assertTrue(boundaries["s17_p1_dependency_reused"])
        self.assertTrue(boundaries["legacy_s17_p2_public_safe_baseline_reused"])
        self.assertTrue(boundaries["s17_p2_notification_scope_included"])
        for key in (
            "s17_p3_scope_included",
            "stage17_review_scope_included",
            "github_upload_scope_included",
            "real_notification_delivery_scope_included",
            "external_connector_scope_included",
            "full_report_email_body_scope_included",
            "formal_report_runtime_scope_included",
            "business_execution_scope_included",
            "raw_inbox_access_scope_included",
        ):
            self.assertFalse(boundaries[key], key)

        payload = json.dumps(manifest, ensure_ascii=False, sort_keys=True)
        for forbidden in (
            "original_filename",
            "source_header_text",
            "private_ref://",
            "actual_package_sha256",
            "report_attachment_path",
            "credential_payload",
            "business_amount_value",
        ):
            self.assertNotIn(forbidden, payload)

        self.assertFalse(validated["github_upload"]["github_upload_performed"])
        self.assertTrue(validated["github_upload"]["github_upload_deferred_until_v014_stage1_18_complete"])
        self.assertEqual(validated["next_phase"], "S17-P3")


if __name__ == "__main__":
    unittest.main()
