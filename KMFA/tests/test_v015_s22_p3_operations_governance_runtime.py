from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from KMFA.tools import run_v015_s22_p3_operations_governance as runtime


class OperationsGovernanceRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.auth_value = hashlib.sha256((self.temporary.name + "auth").encode()).hexdigest()
        self.signing_value = hashlib.sha256((self.temporary.name + "sign").encode()).hexdigest()
        self.operations_root = root / "operations"
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
            operations_root=self.operations_root,
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

    def request(self, path: str, body: dict | None = None):
        data = None if body is None else json.dumps(body).encode("utf-8")
        headers = {"Content-Type": "application/json"} if data else {}
        request = urllib.request.Request(self.base_url + path, data=data, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                return response.status, json.load(response)
        except urllib.error.HTTPError as error:
            return error.code, json.load(error)

    def login(self, username: str = "owner.local") -> dict:
        status, value = self.request(
            "/api/security-audit/login",
            {"username": username, "credential": self.auth_value},
        )
        self.assertEqual(status, 201)
        return value

    def test_page_and_predecessor_entry_are_available(self) -> None:
        text = urllib.request.urlopen(self.base_url + "/operations").read().decode("utf-8")
        predecessor = urllib.request.urlopen(
            self.base_url + "/security-audit"
        ).read().decode("utf-8")
        self.assertIn("运维、恢复与升级控制", text)
        self.assertIn("S22-P3 正式验收后立即停止", text)
        self.assertIn("/operations", predecessor)
        self.assertIn("window.KMFA_OPERATIONS_TEST", text)

    def test_options_and_overview_show_only_necessary_status(self) -> None:
        status, options = self.request("/api/operations/options")
        overview_status, overview = self.request("/api/operations")
        self.assertEqual(
            (
                status,
                overview_status,
                len(options["services"]),
                len(options["backup_datasets"]),
                len(options["migration_surfaces"]),
            ),
            (200, 200, 6, 3, 4),
        )
        self.assertEqual(
            (
                overview["health"]["service_count"],
                overview["health"]["monitored_service_count"],
                overview["health"]["unmonitored_service_count"],
            ),
            (6, 6, 0),
        )
        encoded = json.dumps(overview, ensure_ascii=False)
        self.assertNotIn(self.auth_value, encoded)
        self.assertNotIn(self.signing_value, encoded)
        self.assertNotIn("latency_ms", encoded)
        self.assertNotIn("Traceback", encoded)
        self.assertEqual(
            (
                overview["raw_root_access_count"],
                overview["external_network_request_count"],
                overview["internal_path_count"],
            ),
            (0, 0, 0),
        )

    def test_only_owner_can_run_operations(self) -> None:
        finance = self.login("finance.local")
        status, value = self.request(
            "/api/operations/backups",
            {"session_token": finance["session_token"]},
        )
        self.assertEqual((status, value["code"]), (403, "OWNER_PERMISSION_REQUIRED"))

    def test_health_failure_is_detected_blocked_and_recovered(self) -> None:
        owner = self.login()
        status, value = self.request(
            "/api/operations/health-drill",
            {"session_token": owner["session_token"], "service_id": "STORAGE"},
        )
        _, overview = self.request("/api/operations")
        self.assertEqual(status, 200)
        self.assertTrue(value["failure_detected"])
        self.assertTrue(value["critical_operation_blocked"])
        self.assertTrue(value["recovered"])
        self.assertTrue(overview["health"]["production_ready"])

    def test_unverified_backup_is_blocked_then_zero_difference_restore_passes(self) -> None:
        owner = self.login()
        created_status, created = self.request(
            "/api/operations/backups",
            {"session_token": owner["session_token"]},
        )
        blocked_status, blocked = self.request(
            "/api/operations/backups/restore-drill",
            {
                "session_token": owner["session_token"],
                "backup_id": created["backup_id"],
            },
        )
        verify_status, verified = self.request(
            "/api/operations/backups/verify",
            {
                "session_token": owner["session_token"],
                "backup_id": created["backup_id"],
            },
        )
        restore_status, restored = self.request(
            "/api/operations/backups/restore-drill",
            {
                "session_token": owner["session_token"],
                "backup_id": created["backup_id"],
            },
        )
        _, overview = self.request("/api/operations")
        self.assertEqual(
            (
                created_status,
                blocked_status,
                blocked["code"],
                verify_status,
                restore_status,
            ),
            (201, 400, "BACKUP_NOT_VERIFIED", 200, 200),
        )
        self.assertTrue(verified["verified"])
        self.assertEqual(
            (restored["difference_count"], restored["permission_difference_count"]),
            (0, 0),
        )
        self.assertEqual(overview["backup"]["usable_backup_count"], 1)

    def test_migration_is_idempotent_and_exactly_rollbackable(self) -> None:
        owner = self.login()
        status, first = self.request(
            "/api/operations/migrations",
            {"session_token": owner["session_token"]},
        )
        second_status, second = self.request(
            "/api/operations/migrations",
            {"session_token": owner["session_token"]},
        )
        rollback_status, rolled_back = self.request(
            "/api/operations/migrations/rollback",
            {
                "session_token": owner["session_token"],
                "migration_id": first["migration_id"],
            },
        )
        self.assertEqual(
            (status, first["status"], first["change_count"], second_status, second["status"]),
            (200, "APPLIED", 4, 200, "NOOP"),
        )
        self.assertEqual(
            (
                rollback_status,
                rolled_back["difference_count"],
                rolled_back["permission_difference_count"],
            ),
            (200, 0, 0),
        )

    def test_migration_failure_drill_keeps_state_unchanged(self) -> None:
        owner = self.login()
        status, value = self.request(
            "/api/operations/migrations/failure-drill",
            {"session_token": owner["session_token"], "surface": "FORMULA"},
        )
        self.assertEqual(status, 200)
        self.assertTrue(value["failure_detected"])
        self.assertTrue(value["state_unchanged"])
        self.assertEqual(value["rollback_difference_count"], 0)

    def test_unknown_operation_routes_fail_closed(self) -> None:
        status, value = self.request("/api/operations/unknown")
        post_status, post_value = self.request("/api/operations/unknown", {})
        self.assertEqual((status, value["code"]), (404, "RESOURCE_NOT_FOUND"))
        self.assertEqual((post_status, post_value["code"]), (404, "RESOURCE_NOT_FOUND"))

    def test_operations_state_survives_workbench_reload(self) -> None:
        owner = self.login()
        _, created = self.request(
            "/api/operations/backups",
            {"session_token": owner["session_token"]},
        )
        self.request(
            "/api/operations/backups/verify",
            {"session_token": owner["session_token"], "backup_id": created["backup_id"]},
        )
        self.request(
            "/api/operations/backups/restore-drill",
            {"session_token": owner["session_token"], "backup_id": created["backup_id"]},
        )
        reloaded = runtime.kernel.OperationsWorkbench(
            self.operations_root,
            self.server.security_workbench,
            seed_health=False,
        )
        self.assertEqual(reloaded.backups.summary()["usable_backup_count"], 1)
        self.assertEqual(reloaded.health.snapshot()["monitored_service_count"], 6)
        self.assertTrue(reloaded.journal.snapshot()["chain_valid"])


if __name__ == "__main__":
    unittest.main()
