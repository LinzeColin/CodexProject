from __future__ import annotations

import hashlib
import unittest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from KMFA.tools import v015_s10_p3_automatic_ingestion_reserve as reserve


class AutomaticIngestionReserveTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tz = ZoneInfo(reserve.DEFAULT_TIMEZONE)
        self.now = datetime(2026, 7, 15, 10, 0, tzinfo=self.tz)

    def session(self) -> reserve.ConnectorSession:
        return reserve.authorize(
            "REDCIRCLE",
            authorization_id="AUTH-TEST-0001",
            vault_reference="vaultref://kmfa/test/redcircle",
            official_authorization=True,
            read_only_scope=True,
        )

    def test_public_verification_has_48_passing_checks(self) -> None:
        result = reserve.public_verification()
        self.assertEqual(result["accounting"], {"total": 48, "passed": 48, "failed": 0})
        self.assertEqual({row["check_id"] for row in result["checks"]}, set(reserve.CHECK_IDS))
        self.assertEqual(result["automatic_connector_enabled_count"], 0)

    def test_exact_future_sources_and_operations_are_registered(self) -> None:
        contract = reserve.connector_contract_public_safe()
        self.assertEqual(set(reserve.SOURCE_LABELS_ZH), {"REDCIRCLE", "KINGDEE", "WPS", "BANK", "TAX"})
        self.assertEqual(tuple(contract["operations"]), reserve.CONNECTOR_OPERATIONS)
        self.assertEqual(contract["contract_ledger_mode"], "FILE_ONLY_NOT_CONNECTOR_CANDIDATE")

    def test_official_read_only_authorization_is_mandatory(self) -> None:
        for official, read_only, code in (
            (False, True, "OFFICIAL_AUTHORIZATION_REQUIRED"),
            (True, False, "READ_ONLY_SCOPE_REQUIRED"),
        ):
            with self.subTest(code=code), self.assertRaisesRegex(reserve.ConnectorContractError, code):
                reserve.authorize(
                    "REDCIRCLE",
                    authorization_id="AUTH-TEST-0001",
                    vault_reference="vaultref://kmfa/test/redcircle",
                    official_authorization=official,
                    read_only_scope=read_only,
                )

    def test_plaintext_credentials_are_rejected(self) -> None:
        for field in ("password", "access_token", "api_key", "cookie"):
            with self.subTest(field=field), self.assertRaisesRegex(
                reserve.ConnectorContractError, "PLAINTEXT_CREDENTIAL_FIELD_FORBIDDEN"
            ):
                reserve.authorize(
                    "REDCIRCLE",
                    authorization_id="AUTH-TEST-0001",
                    vault_reference="vaultref://kmfa/test/redcircle",
                    official_authorization=True,
                    read_only_scope=True,
                    **{field: "forbidden"},
                )

    def test_pull_plan_is_offline_and_revoke_is_fail_closed(self) -> None:
        plan = reserve.pull_manifest_plan(self.session(), requested_at=self.now)
        self.assertEqual(plan["mode"], "OFFLINE_CONTRACT_SIMULATION")
        self.assertFalse(plan["network_call_performed"])
        self.assertFalse(plan["source_mutation_performed"])
        with self.assertRaisesRegex(reserve.ConnectorContractError, "AUTHORIZATION_REVOKED"):
            reserve.pull_manifest_plan(reserve.revoke(self.session()), requested_at=self.now)

    def test_hash_increment_and_idempotency_are_fail_closed(self) -> None:
        payload = b"test"
        declared = "sha256:" + hashlib.sha256(payload).hexdigest()
        self.assertTrue(reserve.verify_hash(payload, declared))
        with self.assertRaisesRegex(reserve.ConnectorContractError, "PAYLOAD_HASH_MISMATCH"):
            reserve.verify_hash(payload, "sha256:" + "0" * 64)
        updated, status = reserve.apply_increment(
            self.session(), cursor=1, idempotency_key="ONE", verified_hash=True
        )
        replay, replay_status = reserve.apply_increment(
            updated, cursor=1, idempotency_key="ONE", verified_hash=True
        )
        self.assertEqual((status, replay_status), ("APPLIED", "ALREADY_APPLIED"))
        self.assertEqual(updated, replay)
        with self.assertRaisesRegex(reserve.ConnectorContractError, "CURSOR_NOT_MONOTONIC"):
            reserve.apply_increment(updated, cursor=1, idempotency_key="TWO", verified_hash=True)

    def test_daily_weekly_monthly_schedules_are_timezone_aware(self) -> None:
        policy = reserve.schedule_policy_public_safe()
        self.assertEqual(set(policy["frequency_types"]), {"DAILY", "WEEKLY", "MONTHLY"})
        for source_id in reserve.SOURCE_LABELS_ZH:
            with self.subTest(source=source_id):
                due = reserve.next_due(source_id, after=self.now)
                self.assertGreater(due, self.now)
                self.assertIsNotNone(due.tzinfo)
        with self.assertRaisesRegex(reserve.ConnectorContractError, "TIMEZONE_REQUIRED"):
            reserve.next_due("REDCIRCLE", after=datetime(2026, 7, 15))

    def test_freshness_states_are_deterministic(self) -> None:
        due = reserve.next_due("REDCIRCLE", after=self.now)
        self.assertEqual(reserve.freshness("REDCIRCLE", checked_at=None, now=self.now), "NEVER_CHECKED")
        self.assertEqual(reserve.freshness("REDCIRCLE", checked_at=self.now, now=self.now), "FRESH")
        self.assertEqual(reserve.freshness("REDCIRCLE", checked_at=self.now, now=due), "DUE")
        self.assertEqual(reserve.freshness("REDCIRCLE", checked_at=self.now, now=self.now + timedelta(days=3)), "STALE")

    def test_retry_is_bounded_and_no_data_never_loops(self) -> None:
        no_data = reserve.retry_decision(attempt=1, outcome="NO_DATA")
        self.assertEqual(no_data, {"status": "CHECK_COMPLETED_NO_DATA", "retry": False, "delay_minutes": 0})
        delays = [
            reserve.retry_decision(attempt=attempt, outcome="TRANSIENT_FAILURE")["delay_minutes"]
            for attempt in (1, 2, 3)
        ]
        self.assertEqual(delays, [15, 60, 240])
        exhausted = reserve.retry_decision(attempt=4, outcome="TRANSIENT_FAILURE")
        self.assertFalse(exhausted["retry"])
        self.assertEqual(exhausted["status"], "RETRY_BUDGET_EXHAUSTED")

    def test_activation_gates_are_independent_and_default_closed(self) -> None:
        matrix = reserve.activation_matrix_public_safe()
        self.assertEqual(matrix["source_gate_count"], 5)
        self.assertEqual(matrix["automatic_connector_enabled_count"], 0)
        self.assertTrue(all(row["activation_status"] == "BLOCKED" for row in matrix["gates"]))
        evidence = {criterion: True for criterion in reserve.ACTIVATION_CRITERIA}
        one = reserve.activation_gate("BANK", evidence)
        self.assertTrue(one["ready_for_separate_acceptance"])
        self.assertFalse(one["enabled"])
        self.assertTrue(all(not row["ready_for_separate_acceptance"] for row in matrix["gates"]))

    def test_file_import_remains_available_when_schedule_fails(self) -> None:
        policy = reserve.schedule_policy_public_safe()
        matrix = reserve.activation_matrix_public_safe()
        self.assertTrue(policy["manual_import_available"])
        self.assertFalse(policy["scheduled_failure_blocks_manual_import"])
        self.assertTrue(matrix["file_mvp_available"])

    def test_module_performs_no_external_or_business_action(self) -> None:
        result = reserve.public_verification()
        self.assertEqual(result["raw_root_access_count"], 0)
        self.assertFalse(result["raw_business_content_read"])
        self.assertFalse(result["source_mutation_performed"])
        self.assertEqual(result["live_connector_call_count"], 0)
        self.assertEqual(result["credential_read_count"], 0)
        self.assertFalse(result["business_execution_performed"])


if __name__ == "__main__":
    unittest.main()
