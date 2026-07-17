from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from KMFA.tools import v015_s22_p1_notifications as notifications


class NotificationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.path = Path(self.temporary.name) / "notifications.jsonl"
        self.journal = notifications.NotificationJournal(self.path)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def report(self, key="unit-report-001", ref="REPORT-UNIT-001", time="2026-07-17T00:00:00+00:00"):
        return self.journal.dispatch_report(
            report_version_id=ref, report_type="MONTHLY", period_label="2026年7月",
            report_status="PUBLISHED_INTERNAL", idempotency_key=key, occurred_at=time,
        )

    def alert(self, rule, ref, key, minute, *, failure=False):
        return self.journal.dispatch_alert(
            rule_id=rule, alert_ref=ref, period_label="2026年7月", alert_status="需要查看",
            idempotency_key=key, occurred_at=f"2026-07-17T00:{minute:02d}:00+00:00",
            simulate_failure=failure,
        )

    def test_report_message_has_only_four_safe_fields(self) -> None:
        value = self.report()
        self.assertEqual(value["status"], "SENT_SANDBOX")
        self.assertEqual({row["field"] for row in value["message"]["body_fields"]}, {"kind", "period", "status", "safe_entry"})
        self.assertEqual((value["message"]["amount_detail_count"], value["message"]["attachment_count"]), (0, 0))
        self.assertEqual(value["message"]["external_network_request_count"], 0)

    def test_all_five_confirmed_alert_categories_dispatch_to_sandbox(self) -> None:
        rules = [row for row in notifications.RULE_CATALOG if row["enabled"] and row["category"] != "REPORT"]
        values = [self.alert(row["rule_id"], f"ALERT-{index:03d}", f"unit-alert-{index:03d}", index) for index, row in enumerate(rules, 1)]
        self.assertEqual({row["category"] for row in values}, {"CASH", "RECEIVABLE", "TAX", "DATA_STALE", "IMPORT_FAILED"})
        self.assertTrue(all(row["status"] == "SENT_SANDBOX" for row in values))

    def test_duplicate_and_silenced_notifications_are_suppressed(self) -> None:
        self.report()
        duplicate = self.report("unit-report-002", time="2026-07-17T00:01:00+00:00")
        self.assertEqual((duplicate["status"], duplicate["suppression_reason"]), ("SUPPRESSED", "DUPLICATE_WINDOW"))
        self.journal.set_rule_silenced("RULE-CASH-MAJOR-RISK", True, idempotency_key="unit-silence-001")
        quiet = self.alert("RULE-CASH-MAJOR-RISK", "ALERT-CASH-001", "unit-cash-quiet-001", 2)
        self.assertEqual((quiet["status"], quiet["suppression_reason"]), ("SUPPRESSED", "RULE_SILENCED"))

    def test_frequency_limit_keeps_fourth_same_category_quiet(self) -> None:
        values = [self.alert("RULE-TAX-MAJOR-RISK", f"ALERT-TAX-{i}", f"unit-tax-{i:03d}", i) for i in range(1, 5)]
        self.assertTrue(all(row["status"] == "SENT_SANDBOX" for row in values[:3]))
        self.assertEqual((values[3]["status"], values[3]["suppression_reason"]), ("SUPPRESSED", "FREQUENCY_LIMIT"))

    def test_retry_is_idempotent_and_keeps_same_safe_body(self) -> None:
        failed = self.alert("RULE-IMPORT-FAILED", "IMPORT-JOB-001", "unit-failure-001", 1, failure=True)
        retried = self.journal.retry(failed["notification_id"], idempotency_key="unit-retry-001", occurred_at="2026-07-17T00:02:00+00:00")
        replay = self.journal.retry(failed["notification_id"], idempotency_key="unit-retry-001", occurred_at="2026-07-17T00:02:00+00:00")
        self.assertEqual((failed["status"], retried["status"], retried["retry_count"]), ("FAILED_RETRYABLE", "RETRY_SUCCEEDED_SANDBOX", 1))
        self.assertEqual(failed["message"]["body_fingerprint"], retried["message"]["body_fingerprint"])
        self.assertTrue(replay["idempotent_replay"])

    def test_unconfirmed_rule_and_sensitive_body_fail_closed(self) -> None:
        with self.assertRaisesRegex(notifications.NotificationError, "未确认"):
            self.alert("RULE-DRAFT-FORECAST-VARIANCE", "DRAFT-001", "unit-draft-001", 1)
        with self.assertRaisesRegex(notifications.NotificationError, "敏感"):
            self.journal.dispatch_alert(
                rule_id="RULE-CASH-MAJOR-RISK", alert_ref="ALERT-SENSITIVE-001", period_label="2026年7月",
                alert_status="金额需要查看", idempotency_key="unit-sensitive-001",
            )

    def test_annual_period_and_idempotency_conflict(self) -> None:
        annual = self.journal.dispatch_report(
            report_version_id="REPORT-ANNUAL-2026", report_type="ANNUAL", period_label="2026年",
            report_status="GENERATED", idempotency_key="unit-annual-001",
        )
        self.assertEqual(annual["message"]["body_fields"][1]["value"], "2026年")
        with self.assertRaisesRegex(notifications.NotificationError, "同一请求编号"):
            self.journal.dispatch_report(
                report_version_id="REPORT-ANNUAL-2025", report_type="ANNUAL", period_label="2025年",
                report_status="GENERATED", idempotency_key="unit-annual-001",
            )

    def test_hash_chain_detects_tampering(self) -> None:
        self.report()
        rows = self.path.read_text(encoding="utf-8").splitlines()
        value = json.loads(rows[0]); value["status"] = "FAKE"; rows[0] = json.dumps(value, ensure_ascii=False, sort_keys=True)
        self.path.write_text("\n".join(rows) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(notifications.NotificationError, "完整性"):
            self.journal.read()

    def test_options_and_public_verification_close_external_boundaries(self) -> None:
        options = notifications.options_contract()
        result = notifications.public_verification()
        self.assertEqual((options["rule_catalog_count"], options["enabled_confirmed_rule_count"]), (7, 6))
        self.assertFalse(options["external_network_allowed"] or options["github_upload_in_scope"] or options["app_reinstall_in_scope"] or options["s22_p2_in_scope"])
        self.assertEqual((result["public_check_count"], result["public_check_pass_count"], result["public_check_failed_count"]), (65, 65, 0))


if __name__ == "__main__":
    unittest.main()
