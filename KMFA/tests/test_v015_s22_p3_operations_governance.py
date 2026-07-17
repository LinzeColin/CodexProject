from __future__ import annotations

import hashlib
import json
import os
import stat
import tempfile
import unittest
from pathlib import Path

from KMFA.tools import v015_s22_p2_security_audit as security
from KMFA.tools import v015_s22_p3_operations_governance as operations


class OperationsGovernanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.auth_value = hashlib.sha256(b"s22p3-unit-auth").hexdigest()
        self.signing_value = hashlib.sha256(b"s22p3-unit-signing").hexdigest()
        self.security = security.SecurityWorkbench(
            self.root / "security.jsonl",
            secret_values={
                "KMFA_LOCAL_AUTH_KEY": self.auth_value,
                "KMFA_SESSION_SIGNING_KEY": self.signing_value,
            },
        )
        self.owner = self.security.sessions.authenticate(
            "owner.local", self.auth_value, session_id="A1" * 12
        )
        self.workbench = operations.OperationsWorkbench(
            self.root / "operations", self.security, occurred_at="2026-07-17T00:00:00+00:00"
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_journal_is_append_only_hash_linked_and_tamper_evident(self) -> None:
        journal = operations.OperationsJournal(self.root / "journal.jsonl")
        journal.append("TEST_EVENT", subject_ref="TEST::ONE", result="PASS")
        journal.append("TEST_EVENT", subject_ref="TEST::TWO", result="PASS")
        self.assertEqual(journal.snapshot()["event_count"], 2)
        self.assertTrue(journal.snapshot()["chain_valid"])
        rows = journal.events()
        rows[0]["details"]["tampered"] = True
        journal.path.write_text(
            "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(operations.OperationsError, "OPERATIONS_JOURNAL_TAMPERED"):
            journal.snapshot()

    def test_six_services_are_monitored_and_ui_snapshot_is_minimal(self) -> None:
        value = self.workbench.overview()
        self.assertEqual(
            (
                value["health"]["service_count"],
                value["health"]["monitored_service_count"],
                value["health"]["unmonitored_service_count"],
            ),
            (6, 6, 0),
        )
        self.assertTrue(value["health"]["production_ready"])
        self.assertTrue(value["necessary_status_only"])
        self.assertEqual(
            (value["internal_path_count"], value["stack_trace_count"], value["credential_field_count"]),
            (0, 0, 0),
        )
        for row in value["health"]["services"]:
            self.assertNotIn("latency_ms", row)
            self.assertNotIn("debug", row)
            self.assertTrue(row["label_zh"] and row["updated_at"])

    def test_missing_monitor_blocks_production(self) -> None:
        registry = operations.HealthRegistry(operations.OperationsJournal(self.root / "empty.jsonl"))
        with self.assertRaisesRegex(operations.OperationsError, "CRITICAL_MONITORING_REQUIRED"):
            registry.require_production_ready()

    def test_failure_drill_detects_blocks_and_recovers(self) -> None:
        value = self.workbench.failure_probe(self.owner["session_token"], "COMPUTATION")
        self.assertTrue(value["failure_detected"])
        self.assertTrue(value["critical_operation_blocked"])
        self.assertTrue(value["recovered"])
        self.assertEqual(value["final_status"], "HEALTHY")
        self.assertTrue(self.workbench.health.snapshot()["production_ready"])

    def test_degraded_service_is_visible_without_exposing_internal_details(self) -> None:
        value = self.workbench.health.record_probe("REPORT", available=True, latency_ms=5000)
        self.assertEqual(value["status"], "DEGRADED")
        row = next(
            item for item in self.workbench.health.snapshot()["services"] if item["service_id"] == "REPORT"
        )
        self.assertEqual(row["status"], "DEGRADED")
        self.assertNotIn("latency_ms", row)

    def test_unknown_service_and_unsafe_message_fail_closed(self) -> None:
        with self.assertRaisesRegex(operations.OperationsError, "SERVICE_UNKNOWN"):
            self.workbench.health.record_probe("UNKNOWN", available=True, latency_ms=1)
        with self.assertRaisesRegex(operations.OperationsError, "HEALTH_MESSAGE_UNSAFE"):
            self.workbench.health.record_probe(
                "IMPORT", available=False, latency_ms=1, message_zh="Traceback /private/path"
            )

    def test_backup_requires_all_datasets_and_current_permissions(self) -> None:
        state = operations.default_state()
        del state["datasets"]["AUDIT_EVENTS"]
        with self.assertRaisesRegex(operations.OperationsError, "BACKUP_SCOPE_INCOMPLETE"):
            self.workbench.backups.create(state)
        state = operations.default_state()
        state["permissions"]["OWNER"] = []
        with self.assertRaisesRegex(operations.OperationsError, "BACKUP_PERMISSION_INVALID"):
            self.workbench.backups.create(state)

    def test_unverified_backup_is_not_usable_or_restorable(self) -> None:
        value = self.workbench.create_backup(self.owner["session_token"])
        self.assertFalse(value["verified"])
        self.assertFalse(value["usable"])
        with self.assertRaisesRegex(operations.OperationsError, "BACKUP_NOT_VERIFIED"):
            self.workbench.restore_drill(self.owner["session_token"], value["backup_id"])

    def test_verified_backup_restores_with_zero_data_and_permission_difference(self) -> None:
        created = self.workbench.create_backup(self.owner["session_token"])
        verified = self.workbench.verify_backup(self.owner["session_token"], created["backup_id"])
        self.assertTrue(verified["verified"])
        self.assertFalse(verified["usable"])
        restored = self.workbench.restore_drill(self.owner["session_token"], created["backup_id"])
        self.assertEqual(
            (restored["difference_count"], restored["permission_difference_count"]),
            (0, 0),
        )
        self.assertTrue(restored["usable"])
        backup_path = self.workbench.backups._path(created["backup_id"])
        self.assertEqual(stat.S_IMODE(backup_path.stat().st_mode), 0o600)

    def test_backup_is_content_addressed_idempotent_and_tamper_evident(self) -> None:
        first = self.workbench.create_backup(self.owner["session_token"])
        second = self.workbench.create_backup(self.owner["session_token"])
        self.assertEqual(first["backup_id"], second["backup_id"])
        self.assertFalse(second["created"])
        self.assertEqual(self.workbench.backups.tamper_probe(first["backup_id"])["tamper_accept_count"], 0)
        path = self.workbench.backups._path(first["backup_id"])
        value = json.loads(path.read_text(encoding="utf-8"))
        value["payload"]["datasets"]["CONFIGURATION"]["tampered"] = True
        path.write_text(json.dumps(value), encoding="utf-8")
        os.chmod(path, 0o600)
        with self.assertRaisesRegex(operations.OperationsError, "BACKUP_INTEGRITY_FAILED"):
            self.workbench.backups.verify(first["backup_id"])

    def test_migration_updates_four_surfaces_and_second_run_is_noop(self) -> None:
        value = self.workbench.migrate(self.owner["session_token"])
        self.assertEqual((value["status"], value["change_count"]), ("APPLIED", 4))
        self.assertEqual(value["permission_difference_count"], 0)
        second = self.workbench.migrate(self.owner["session_token"])
        self.assertEqual((second["status"], second["change_count"]), ("NOOP", 0))
        self.assertTrue(second["idempotent"])
        self.assertTrue(self.workbench.migrations.summary()["at_target"])

    def test_migration_failure_is_atomic_and_rollback_restores_exact_state(self) -> None:
        before = operations._fingerprint(self.workbench.migrations.state())
        drill = self.workbench.migration_failure_probe(self.owner["session_token"], "FORMULA")
        self.assertTrue(drill["failure_detected"])
        self.assertTrue(drill["state_unchanged"])
        self.assertEqual(drill["rollback_difference_count"], 0)
        self.assertEqual(operations._fingerprint(self.workbench.migrations.state()), before)
        applied = self.workbench.migrate(self.owner["session_token"])
        rolled_back = self.workbench.rollback(self.owner["session_token"], applied["migration_id"])
        self.assertEqual(
            (rolled_back["difference_count"], rolled_back["permission_difference_count"]),
            (0, 0),
        )
        self.assertEqual(operations._fingerprint(self.workbench.migrations.state()), before)

    def test_irreversible_migration_requires_explicit_approval(self) -> None:
        with self.assertRaisesRegex(operations.OperationsError, "IRREVERSIBLE_APPROVAL_REQUIRED"):
            self.workbench.migrations.apply(irreversible=True)
        value = self.workbench.migrations.apply(
            irreversible=True, approval_ref="APPROVAL::OWNER-S22P3"
        )
        self.assertEqual(value["status"], "APPLIED")

    def test_only_owner_can_backup_restore_or_migrate(self) -> None:
        finance = self.security.sessions.authenticate(
            "finance.local", self.auth_value, session_id="B2" * 12
        )
        for action in (
            lambda: self.workbench.create_backup(finance["session_token"]),
            lambda: self.workbench.migrate(finance["session_token"]),
            lambda: self.workbench.failure_probe(finance["session_token"], "STORAGE"),
        ):
            with self.assertRaisesRegex(operations.OperationsError, "OWNER_PERMISSION_REQUIRED"):
                action()

    def test_public_verification_passes_every_check(self) -> None:
        value = operations.public_verification()
        self.assertEqual(
            (value["status"], value["public_check_count"], value["public_check_pass_count"]),
            ("PASS", 62, 62),
        )
        self.assertEqual(
            (
                value["restore_difference_count"],
                value["migration_rollback_difference_count"],
                value["irreversible_without_approval_accept_count"],
                value["raw_external_release_count"],
            ),
            (0, 0, 0, 0),
        )


if __name__ == "__main__":
    unittest.main()
