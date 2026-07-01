import copy
import json
import unittest

from KMFA.tools.notification_reminders import (
    REQUIRED_NOTIFICATION_TRIGGERS,
    NotificationReminderError,
    build_default_notification_reminders,
    validate_notification_reminder_artifacts,
)


class NotificationReminderTests(unittest.TestCase):
    def test_default_runtime_covers_s17_p2_required_scope(self) -> None:
        manifest, rules, events, dispatch_logs = build_default_notification_reminders(
            generated_at="2026-07-01T23:59:00+10:00"
        )
        validate_notification_reminder_artifacts(
            manifest,
            rules,
            events,
            dispatch_logs,
        )

        self.assertEqual(manifest["stage_phase"], "S17-P2")
        self.assertEqual(tuple(manifest["required_notification_triggers"]), REQUIRED_NOTIFICATION_TRIGGERS)
        self.assertEqual(manifest["summary"]["notification_rule_count"], 3)
        self.assertEqual(manifest["summary"]["notification_event_count"], 3)
        self.assertEqual(manifest["summary"]["notification_dispatch_log_count"], 3)
        self.assertTrue(manifest["quality_gate"]["notification_rules_complete"])
        self.assertTrue(manifest["quality_gate"]["notification_logs_written_to_metadata"])
        self.assertTrue(manifest["quality_gate"]["email_reminder_only"])
        self.assertFalse(manifest["quality_gate"]["email_full_report_body_allowed"])
        self.assertFalse(manifest["quality_gate"]["email_attachment_allowed"])
        self.assertFalse(manifest["quality_gate"]["s17_p3_scope_allowed"])
        self.assertFalse(manifest["quality_gate"]["stage17_review_allowed"])
        self.assertFalse(manifest["quality_gate"]["github_upload_allowed"])

    def test_notification_rules_cover_report_completion_major_risk_and_missing_source(self) -> None:
        manifest, rules, events, dispatch_logs = build_default_notification_reminders(
            generated_at="2026-07-01T23:59:00+10:00"
        )
        validate_notification_reminder_artifacts(manifest, rules, events, dispatch_logs)

        rules_by_trigger = {row["trigger_type"]: row for row in rules}
        self.assertEqual(set(rules_by_trigger), set(REQUIRED_NOTIFICATION_TRIGGERS))
        for trigger_type, row in rules_by_trigger.items():
            self.assertEqual(row["record_type"], "notification_rule")
            self.assertEqual(row["channel"], "email_reminder")
            self.assertIn(row["recipient_role"], {"management", "finance", "reviewer"})
            self.assertFalse(row["full_report_body_allowed"])
            self.assertFalse(row["report_attachment_allowed"])
            self.assertFalse(row["raw_payload_allowed"])
            self.assertTrue(row["metadata_log_required"])
            self.assertTrue(row["public_safe_template_only"])
            self.assertIn(trigger_type, row["rule_id"])

    def test_email_reminders_do_not_include_full_report_body_attachments_or_addresses(self) -> None:
        manifest, rules, events, dispatch_logs = build_default_notification_reminders(
            generated_at="2026-07-01T23:59:00+10:00"
        )
        validate_notification_reminder_artifacts(manifest, rules, events, dispatch_logs)

        for log in dispatch_logs:
            self.assertEqual(log["record_type"], "notification_dispatch_log")
            self.assertEqual(log["channel"], "email_reminder")
            self.assertEqual(log["delivery_mode"], "metadata_outbox_only")
            self.assertEqual(log["delivery_status"], "metadata_logged")
            self.assertFalse(log["full_report_body_included"])
            self.assertFalse(log["report_attachment_included"])
            self.assertEqual(log["recipient_address_ref"], "role_ref_only")
            self.assertNotIn("@", json.dumps(log, ensure_ascii=False, sort_keys=True))
            self.assertLessEqual(len(log["body_summary"]), 120)

    def test_notification_logs_are_append_only_metadata_records(self) -> None:
        manifest, rules, events, dispatch_logs = build_default_notification_reminders(
            generated_at="2026-07-01T23:59:00+10:00"
        )
        validate_notification_reminder_artifacts(manifest, rules, events, dispatch_logs)

        event_ids = {row["event_id"] for row in events}
        for row in events:
            self.assertEqual(row["record_type"], "notification_event")
            self.assertTrue(row["append_only"])
            self.assertEqual(row["metadata_target"], "KMFA/metadata/notifications/notification_events.jsonl")
            self.assertIn(row["trigger_type"], REQUIRED_NOTIFICATION_TRIGGERS)
            self.assertFalse(row["raw_business_data_included"])
            self.assertFalse(row["full_report_body_included"])
            self.assertTrue(row["evidence_ref"])

        for row in dispatch_logs:
            self.assertIn(row["event_id"], event_ids)
            self.assertTrue(row["append_only"])
            self.assertEqual(row["metadata_target"], "KMFA/metadata/notifications/notification_dispatch_log.jsonl")
            self.assertEqual(row["result_status"], "metadata_logged")

    def test_public_payload_has_no_raw_values_private_refs_full_report_or_live_secrets(self) -> None:
        manifest, rules, events, dispatch_logs = build_default_notification_reminders(
            generated_at="2026-07-01T23:59:00+10:00"
        )
        payload = json.dumps([manifest, rules, events, dispatch_logs], ensure_ascii=False, sort_keys=True)

        for forbidden_text in (
            "raw_value",
            "normalized_value",
            "plaintext_value",
            "source_header_text",
            "original_filename",
            "private://",
            "private_ref://",
            "full_report_body_text",
            "complete_report_body_text",
            "report_attachment_path",
            "recipient_email",
            "smtp",
            "sk-",
            "-----BEGIN",
        ):
            self.assertNotIn(forbidden_text, payload)

    def test_validator_rejects_missing_trigger_full_body_attachment_or_scope_escape(self) -> None:
        manifest, rules, events, dispatch_logs = build_default_notification_reminders(
            generated_at="2026-07-01T23:59:00+10:00"
        )

        broken_rules = [row for row in rules if row["trigger_type"] != "data_source_missing"]
        with self.assertRaises(NotificationReminderError):
            validate_notification_reminder_artifacts(manifest, broken_rules, events, dispatch_logs)

        broken_logs = copy.deepcopy(dispatch_logs)
        broken_logs[0]["full_report_body_included"] = True
        with self.assertRaises(NotificationReminderError):
            validate_notification_reminder_artifacts(manifest, rules, events, broken_logs)

        broken_logs = copy.deepcopy(dispatch_logs)
        broken_logs[0]["report_attachment_included"] = True
        with self.assertRaises(NotificationReminderError):
            validate_notification_reminder_artifacts(manifest, rules, events, broken_logs)

        broken_manifest = copy.deepcopy(manifest)
        broken_manifest["quality_gate"]["stage17_review_allowed"] = True
        with self.assertRaises(NotificationReminderError):
            validate_notification_reminder_artifacts(broken_manifest, rules, events, dispatch_logs)

        broken_events = copy.deepcopy(events)
        broken_events[0]["metadata_target"] = "KMFA/metadata/security/audit_events.jsonl"
        with self.assertRaises(NotificationReminderError):
            validate_notification_reminder_artifacts(manifest, rules, broken_events, dispatch_logs)


if __name__ == "__main__":
    unittest.main()
