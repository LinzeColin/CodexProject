from __future__ import annotations

import json
import tempfile
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from KMFA.tools import run_v015_s22_p1_notifications as runtime


class NotificationRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(); root = Path(self.temporary.name)
        self.server, self.thread, self.base_url = runtime.start_server(
            event_path=root / "base.jsonl", data_root=root / "data", confirmation_event_path=root / "confirmation.jsonl",
            publication_event_path=root / "publication.jsonl", report_model_event_path=root / "models.jsonl",
            export_event_path=root / "exports.jsonl", export_bundle_root=root / "bundles",
            workflow_event_path=root / "workflows.jsonl", notification_event_path=root / "notifications.jsonl",
        )

    def tearDown(self) -> None:
        self.server.shutdown(); self.server.server_close(); self.thread.join(timeout=3); self.temporary.cleanup()

    def request(self, path, body=None):
        data = None if body is None else json.dumps(body).encode("utf-8")
        headers = {"Content-Type": "application/json"} if data else {}
        request = urllib.request.Request(self.base_url + path, data=data, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                return response.status, json.load(response)
        except urllib.error.HTTPError as error:
            return error.code, json.load(error)

    def test_page_and_report_center_link_are_available(self) -> None:
        text = urllib.request.urlopen(self.base_url + "/notification-delivery").read().decode("utf-8")
        self.assertIn("通知只负责提醒", text)
        predecessor = urllib.request.urlopen(self.base_url + "/report-workflow").read().decode("utf-8")
        self.assertIn("notification-delivery", predecessor)

    def test_options_and_empty_snapshot_are_public_safe(self) -> None:
        status, options = self.request("/api/notification-delivery/options")
        _, snapshot = self.request("/api/notification-delivery")
        self.assertEqual((status, options["recipient_count"], options["enabled_confirmed_rule_count"]), (200, 1, 6))
        self.assertEqual((snapshot["event_count"], snapshot["external_network_request_count"], snapshot["raw_root_access_count"]), (0, 0, 0))

    def test_report_dispatch_returns_safe_sandbox_message(self) -> None:
        status, value = self.request("/api/notification-delivery/report", {
            "report_version_id": "REPORT-RUNTIME-001", "report_type": "MONTHLY", "period_label": "2026年7月",
            "report_status": "PUBLISHED_INTERNAL", "idempotency_key": "runtime-report-001",
        })
        self.assertEqual((status, value["status"], len(value["message"]["body_fields"])), (201, "SENT_SANDBOX", 4))
        self.assertEqual(value["message"]["external_network_request_count"], 0)

    def test_duplicate_and_unconfirmed_rules_are_blocked(self) -> None:
        body = {"report_version_id": "REPORT-RUNTIME-002", "report_type": "MONTHLY", "period_label": "2026年7月", "report_status": "GENERATED"}
        _, first = self.request("/api/notification-delivery/report", {**body, "idempotency_key": "runtime-duplicate-001", "occurred_at": "2026-07-17T00:00:00+00:00"})
        _, duplicate = self.request("/api/notification-delivery/report", {**body, "idempotency_key": "runtime-duplicate-002", "occurred_at": "2026-07-17T00:01:00+00:00"})
        status, error = self.request("/api/notification-delivery/alert", {"rule_id": "RULE-DRAFT-FORECAST-VARIANCE", "alert_ref": "DRAFT-001", "period_label": "2026年7月", "alert_status": "待确认", "idempotency_key": "runtime-draft-001"})
        self.assertEqual((first["status"], duplicate["suppression_reason"]), ("SENT_SANDBOX", "DUPLICATE_WINDOW"))
        self.assertEqual((status, error["code"]), (409, "RULE_NOT_CONFIRMED"))

    def test_silence_and_resume_rule(self) -> None:
        status, silenced = self.request("/api/notification-delivery/rules/RULE-CASH-MAJOR-RISK/silence", {"idempotency_key": "runtime-silence-001"})
        _, quiet = self.request("/api/notification-delivery/alert", {"rule_id": "RULE-CASH-MAJOR-RISK", "alert_ref": "ALERT-CASH-001", "period_label": "2026年7月", "alert_status": "需要查看", "idempotency_key": "runtime-cash-quiet-001"})
        _, resumed = self.request("/api/notification-delivery/rules/RULE-CASH-MAJOR-RISK/resume", {"idempotency_key": "runtime-resume-001"})
        self.assertEqual((status, silenced["status"], quiet["suppression_reason"], resumed["status"]), (200, "SILENCED", "RULE_SILENCED", "ACTIVE"))

    def test_failed_delivery_records_reason_and_retries_idempotently(self) -> None:
        _, failed = self.request("/api/notification-delivery/alert", {"rule_id": "RULE-IMPORT-FAILED", "alert_ref": "IMPORT-JOB-001", "period_label": "2026年7月", "alert_status": "导入失败", "simulate_failure": True, "idempotency_key": "runtime-failure-001"})
        path = f"/api/notification-delivery/{failed['notification_id']}/retry"
        status, retried = self.request(path, {"idempotency_key": "runtime-retry-001"})
        _, replay = self.request(path, {"idempotency_key": "runtime-retry-001"})
        self.assertEqual((failed["failure_code"], status, retried["status"]), ("SANDBOX_TRANSIENT_FAILURE", 200, "RETRY_SUCCEEDED_SANDBOX"))
        self.assertTrue(replay["idempotent_replay"])

    def test_invalid_period_and_unknown_route_return_stable_errors(self) -> None:
        status, error = self.request("/api/notification-delivery/report", {"report_version_id": "REPORT-BAD-001", "report_type": "MONTHLY", "period_label": "最近", "report_status": "GENERATED", "idempotency_key": "runtime-bad-period-001"})
        unknown_status, unknown = self.request("/api/notification-delivery/not-found")
        self.assertEqual((status, error["code"]), (400, "PERIOD_INVALID"))
        self.assertEqual((unknown_status, unknown["code"]), (404, "RESOURCE_NOT_FOUND"))

    def test_snapshot_persists_delivery_log(self) -> None:
        self.request("/api/notification-delivery/alert", {"rule_id": "RULE-DATA-STALE", "alert_ref": "STALE-001", "period_label": "2026年7月", "alert_status": "需要查看", "idempotency_key": "runtime-stale-001"})
        _, before = self.request("/api/notification-delivery")
        reloaded = runtime.kernel.NotificationJournal(self.server.notification_journal.path).snapshot()
        self.assertEqual((before["event_count"], reloaded["event_count"]), (1, 1))
        self.assertEqual(reloaded["notifications"][0]["category"], "DATA_STALE")


if __name__ == "__main__":
    unittest.main()
