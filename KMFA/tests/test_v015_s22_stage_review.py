from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from KMFA.tools import run_v015_s22_p3_operations_governance as runtime


class Stage22ReviewRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.auth_value = hashlib.sha256((self.temporary.name + "auth").encode()).hexdigest()
        self.signing_value = hashlib.sha256((self.temporary.name + "sign").encode()).hexdigest()
        self.server, self.thread, self.base_url = runtime.start_server(
            event_path=root / "base.jsonl",
            data_root=root / "data",
            confirmation_event_path=root / "confirmation.jsonl",
            publication_event_path=root / "publication.jsonl",
            report_model_event_path=root / "models.jsonl",
            export_event_path=root / "exports.jsonl",
            export_bundle_root=root / "bundles",
            workflow_event_path=root / "workflows.jsonl",
            notification_event_path=root / "notifications.jsonl",
            audit_event_path=root / "audit.jsonl",
            operations_root=root / "operations",
            secret_values={
                "KMFA_LOCAL_AUTH_KEY": self.auth_value,
                "KMFA_SESSION_SIGNING_KEY": self.signing_value,
            },
        )

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)
        self.temporary.cleanup()

    def request(
        self,
        path: str,
        body: dict | None = None,
        *,
        headers: dict[str, str] | None = None,
    ):
        data = None if body is None else json.dumps(body).encode("utf-8")
        request_headers = dict(headers or {})
        if data:
            request_headers["Content-Type"] = "application/json"
        request = urllib.request.Request(
            self.base_url + path, data=data, headers=request_headers
        )
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                return response.status, json.load(response)
        except urllib.error.HTTPError as error:
            return error.code, json.load(error)

    def login(self, username: str) -> dict:
        status, value = self.request(
            "/api/security-audit/login",
            {"username": username, "credential": self.auth_value},
        )
        self.assertEqual(status, 201)
        return value

    @staticmethod
    def report_body(token: str | None = None) -> dict:
        value = {
            "report_version_id": "REPORT-S22REV-RUNTIME-001",
            "report_type": "MONTHLY",
            "period_label": "2026-07",
            "report_status": "APPROVED",
            "idempotency_key": "s22-review-runtime-report-001",
        }
        if token:
            value["session_token"] = token
        return value

    def test_notification_mutation_requires_session_and_is_audited(self) -> None:
        denied_status, denied = self.request(
            "/api/notification-delivery/report", self.report_body()
        )
        finance = self.login("finance.local")
        allowed_status, allowed = self.request(
            "/api/notification-delivery/report",
            self.report_body(finance["session_token"]),
        )
        _, audit = self.request(
            "/api/security-audit?action_type=PROCESSING",
            headers={"X-KMFA-Session": finance["session_token"]},
        )
        self.assertEqual((denied_status, denied["code"]), (401, "SESSION_INVALID"))
        self.assertEqual((allowed_status, allowed["status"]), (201, "SENT_SANDBOX"))
        self.assertTrue(
            any(
                row["subject_ref"] == "NOTIFICATION::REPORT"
                for row in audit["query"]["events"]
            )
        )

    def test_readonly_cannot_mutate_notification(self) -> None:
        readonly = self.login("readonly.local")
        status, value = self.request(
            "/api/notification-delivery/report",
            self.report_body(readonly["session_token"]),
        )
        self.assertEqual((status, value["code"]), (403, "PERMISSION_DENIED"))

    def test_audit_details_are_hidden_until_authorized(self) -> None:
        owner = self.login("owner.local")
        _, hidden = self.request("/api/security-audit")
        _, visible = self.request(
            "/api/security-audit",
            headers={"X-KMFA-Session": owner["session_token"]},
        )
        self.assertTrue(hidden["authentication_required"])
        self.assertEqual(hidden["audit"]["events"], [])
        self.assertEqual(hidden["query"]["events"], [])
        self.assertFalse(visible["authentication_required"])
        self.assertGreaterEqual(visible["query"]["query_result_count"], 1)

    def test_live_backup_contains_current_notification_and_audit(self) -> None:
        owner = self.login("owner.local")
        self.request(
            "/api/notification-delivery/report",
            self.report_body(owner["session_token"]),
        )
        created_status, created = self.request(
            "/api/operations/backups",
            {"session_token": owner["session_token"]},
        )
        envelope = self.server.operations_workbench.backups._read(created["backup_id"])
        datasets = envelope["payload"]["datasets"]
        self.assertEqual(created_status, 201)
        self.assertEqual(datasets["PRIVATE_DERIVED"]["source"], "LIVE_RUNTIME")
        self.assertEqual(
            datasets["PRIVATE_DERIVED"]["notification_event_count"], 1
        )
        self.assertGreaterEqual(datasets["AUDIT_EVENTS"]["security_event_count"], 3)
        encoded = json.dumps(envelope, ensure_ascii=False)
        self.assertNotIn(self.auth_value, encoded)
        self.assertNotIn(self.signing_value, encoded)

    def test_all_critical_operations_enter_security_audit(self) -> None:
        owner = self.login("owner.local")
        token = owner["session_token"]
        self.request(
            "/api/operations/health-drill",
            {"session_token": token, "service_id": "STORAGE"},
        )
        _, created = self.request(
            "/api/operations/backups", {"session_token": token}
        )
        self.request(
            "/api/operations/backups/verify",
            {"session_token": token, "backup_id": created["backup_id"]},
        )
        self.request(
            "/api/operations/backups/restore-drill",
            {"session_token": token, "backup_id": created["backup_id"]},
        )
        _, migrated = self.request(
            "/api/operations/migrations", {"session_token": token}
        )
        self.request(
            "/api/operations/migrations/rollback",
            {"session_token": token, "migration_id": migrated["migration_id"]},
        )
        self.request(
            "/api/operations/migrations/failure-drill",
            {"session_token": token, "surface": "FORMULA"},
        )
        _, audit = self.request(
            "/api/security-audit?limit=200",
            headers={"X-KMFA-Session": token},
        )
        subjects = {row["subject_ref"] for row in audit["query"]["events"]}
        self.assertTrue(
            {
                "SERVICE::HEALTH-DRILL-S22P3",
                "BACKUP::S22P3",
                "BACKUP::VERIFY-S22P3",
                "BACKUP::RESTORE-S22P3",
                "MIGRATION::S22P3",
                "MIGRATION::ROLLBACK-S22P3",
                "MIGRATION::FAILURE-DRILL-S22P3",
            }
            <= subjects
        )

    def test_three_pages_have_navigation_and_short_session_contract(self) -> None:
        html = runtime.render_html()
        self.assertEqual(html.count('aria-label="长期运行三步流程"'), 3)
        self.assertIn("kmfa_s22_session_token", html)
        self.assertIn("X-KMFA-Session", html)
        for path, current in (
            ("/notification-delivery", "安全通知"),
            ("/security-audit", "登录与审计"),
            ("/operations", "运维与恢复"),
        ):
            page = urllib.request.urlopen(self.base_url + path).read().decode("utf-8")
            self.assertIn(current, page)


if __name__ == "__main__":
    unittest.main()
