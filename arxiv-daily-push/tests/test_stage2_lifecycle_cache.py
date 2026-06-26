from __future__ import annotations

import plistlib
import tempfile
import unittest
from pathlib import Path

from arxiv_daily_push.stage2_lifecycle_cache import (
    S2PMT04_DEFAULT_CACHE_TTL_SECONDS,
    build_cache_low_disk_degradation_receipt,
    build_cache_cleanup_plan,
    build_launchd_plist_payload,
    build_lifecycle_cache_report,
    build_lifecycle_transition_plan,
    build_shutdown_receipt,
    build_startup_convergence_receipt,
    build_startup_reconciliation,
    build_transaction_completion_receipt,
    validate_launchd_plist_payload,
    validate_cache_low_disk_degradation_receipt,
    validate_lifecycle_cache_report,
    validate_lifecycle_transition,
    validate_startup_convergence_receipt,
    validate_transaction_completion_receipt,
)


class Stage2LifecycleCacheTests(unittest.TestCase):
    def test_lifecycle_chain_allows_drain_and_blocks_direct_stop(self) -> None:
        plan = build_lifecycle_transition_plan(cycle_id="2026-07-03", generated_at="2026-07-03T06:00:00+10:00")

        self.assertTrue(plan["transition_chain_valid"])
        self.assertTrue(plan["claim_new_work_disabled_during_draining"])
        self.assertFalse(plan["direct_stop_without_drain_allowed"])
        self.assertEqual(validate_lifecycle_transition("RUNNING", "DRAINING"), [])
        self.assertIn("transition RUNNING->STOPPED is not allowed", validate_lifecycle_transition("RUNNING", "STOPPED"))

    def test_startup_reconciliation_covers_temp_inflight_outbox_and_stale_locks(self) -> None:
        receipt = build_startup_reconciliation(
            temp_items=[{"item_id": "tmp-1"}],
            inflight_items=[{"work_id": "work-1", "state": "RUNNING"}],
            outbox_items=[{"mail_key": "cycle|M1|owner", "status": "ACCEPTED_PENDING_COMMIT"}],
            stale_locks=[{"lock_id": "lock-1", "lease_owner": "worker-old"}],
            generated_at="2026-07-03T06:00:00+10:00",
        )

        self.assertTrue(receipt["reconciliation_ready"])
        self.assertFalse(receipt["new_work_claim_allowed"])
        self.assertFalse(receipt["queue_mutation_applied"])
        self.assertEqual(receipt["temp_actions"][0]["action"], "cleanup_temp_after_whitelist_check")
        self.assertFalse(receipt["outbox_actions"][0]["resend_allowed_without_provider_ref"])

    def test_startup_convergence_receipt_conserves_counts_after_restart(self) -> None:
        startup = build_startup_reconciliation(
            temp_items=[{"item_id": "tmp-1"}, {"item_id": "tmp-2"}],
            inflight_items=[{"work_id": "work-1", "state": "RUNNING"}],
            outbox_items=[{"mail_key": "cycle|M1|owner", "status": "ACCEPTED_PENDING_COMMIT"}],
            stale_locks=[{"lock_id": "lock-1", "lease_owner": "worker-old"}],
            generated_at="2026-07-03T06:00:00+10:00",
        )
        receipt = build_startup_convergence_receipt(
            startup_reconciliation=startup,
            expected_counts={"temp_items": 2, "inflight_items": 1, "outbox_items": 1, "stale_locks": 1},
            generated_at="2026-07-03T06:00:01+10:00",
        )

        self.assertEqual(receipt["status"], "pass")
        self.assertTrue(receipt["count_conservation"])
        self.assertTrue(receipt["terminal_convergence"])
        self.assertFalse(receipt["new_work_claim_allowed"])
        self.assertFalse(receipt["queue_mutation_applied"])
        self.assertEqual(receipt["total_expected_count"], 5)
        self.assertEqual(receipt["total_accounted_count"], 5)
        self.assertEqual(validate_startup_convergence_receipt(receipt), [])

    def test_startup_convergence_receipt_blocks_missing_persistent_state_action(self) -> None:
        startup = build_startup_reconciliation(
            temp_items=[{"item_id": "tmp-1"}],
            inflight_items=[{"work_id": "work-1", "state": "RUNNING"}],
            outbox_items=[{"mail_key": "cycle|M1|owner", "status": "ACCEPTED_PENDING_COMMIT"}],
            stale_locks=[],
            generated_at="2026-07-03T06:00:00+10:00",
        )
        startup["outbox_actions"] = []
        receipt = build_startup_convergence_receipt(
            startup_reconciliation=startup,
            expected_counts={"temp_items": 1, "inflight_items": 1, "outbox_items": 1, "stale_locks": 0},
            generated_at="2026-07-03T06:00:01+10:00",
        )

        self.assertEqual(receipt["status"], "blocked")
        self.assertFalse(receipt["count_conservation"])
        self.assertIn("outbox_items expected 1 but accounted 0", receipt["blocking_reasons"])
        self.assertIn("outbox_items expected/accounted count mismatch", validate_startup_convergence_receipt(receipt))

    def test_shutdown_receipt_requires_checkpoint_backup_and_lease_release(self) -> None:
        ok = build_shutdown_receipt(
            cycle_id="2026-07-03",
            inflight_count=0,
            outbox_pending_count=1,
            checkpoint_ref="checkpoint://local/ok",
            cleanup_ref="cleanup://local/ok",
            backup_ref="backup://local/ok",
            lease_released=True,
            graceful_elapsed_seconds=120,
            generated_at="2026-07-03T06:00:00+10:00",
        )
        blocked = build_shutdown_receipt(
            cycle_id="2026-07-03",
            inflight_count=1,
            outbox_pending_count=1,
            checkpoint_ref="",
            cleanup_ref="cleanup://local/blocked",
            backup_ref="",
            lease_released=False,
            graceful_elapsed_seconds=301,
            generated_at="2026-07-03T06:00:00+10:00",
        )

        self.assertEqual(ok["status"], "pass")
        self.assertEqual(ok["exit_code"], 0)
        self.assertEqual(blocked["status"], "blocked")
        self.assertEqual(blocked["exit_code"], 2)
        self.assertIn("checkpoint must be written", blocked["blocking_reasons"])
        self.assertIn("lease release must be recorded", blocked["blocking_reasons"])

    def test_transaction_completion_receipt_allows_precise_restart_after_kill(self) -> None:
        receipt = build_transaction_completion_receipt(
            cycle_id="2026-07-03",
            generated_at="2026-07-03T06:00:00+10:00",
            interrupted_after_step="cleanup",
            steps=[
                {"step_id": "inflight", "committed": True, "durable_ref": "receipt://inflight"},
                {"step_id": "outbox", "committed": True, "durable_ref": "receipt://outbox"},
                {"step_id": "checkpoint", "committed": True, "durable_ref": "receipt://checkpoint"},
                {"step_id": "cleanup", "committed": True, "durable_ref": "receipt://cleanup"},
                {"step_id": "backup", "committed": False, "rollback_ref": "rollback://backup"},
                {"step_id": "lease_release", "committed": False, "rollback_ref": "rollback://lease_release"},
            ],
        )

        self.assertEqual(receipt["status"], "pass")
        self.assertFalse(receipt["completed"])
        self.assertTrue(receipt["interrupted_recoverable"])
        self.assertFalse(receipt["new_work_claim_allowed"])
        self.assertTrue(receipt["completion_signal_observable"])
        self.assertEqual([action["step_id"] for action in receipt["recovery_actions"]], ["backup", "lease_release"])
        self.assertEqual(validate_transaction_completion_receipt(receipt), [])

    def test_transaction_completion_receipt_blocks_invisible_or_post_kill_commit(self) -> None:
        blocked = build_transaction_completion_receipt(
            cycle_id="2026-07-03",
            generated_at="2026-07-03T06:00:00+10:00",
            interrupted_after_step="checkpoint",
            steps=[
                {"step_id": "inflight", "committed": True, "durable_ref": "receipt://inflight"},
                {"step_id": "outbox", "committed": True, "durable_ref": "receipt://outbox"},
                {"step_id": "checkpoint", "committed": True, "durable_ref": "receipt://checkpoint"},
                {"step_id": "cleanup", "committed": True, "durable_ref": "receipt://cleanup"},
                {"step_id": "backup", "committed": False},
                {"step_id": "lease_release", "committed": False, "rollback_ref": "rollback://lease_release"},
            ],
        )

        self.assertEqual(blocked["status"], "blocked")
        self.assertIn("transaction step cleanup committed after interruption point", blocked["blocking_reasons"])
        self.assertIn("transaction step backup lacks rollback_ref for recovery", blocked["blocking_reasons"])
        self.assertIn("transaction completion signal must be observable", validate_transaction_completion_receipt(blocked))

    def test_cache_cleanup_keeps_durable_evidence_and_blocks_unsafe_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            symlink = root / "rebuildable" / "link"
            symlink.parent.mkdir()
            symlink.symlink_to(root / "target")
            outside = root.parent / "outside-cache.txt"
            plan = build_cache_cleanup_plan(
                cache_entries=[
                    {
                        "path": str(root / "raw" / "evidence.json"),
                        "cache_class": "durable_evidence",
                        "size_bytes": 100,
                        "age_seconds": S2PMT04_DEFAULT_CACHE_TTL_SECONDS * 2,
                    },
                    {
                        "path": str(root / "fulltext" / "old.txt"),
                        "cache_class": "rebuildable_cache",
                        "size_bytes": 200,
                        "age_seconds": S2PMT04_DEFAULT_CACHE_TTL_SECONDS + 1,
                    },
                    {"path": str(root / "tmp" / "scratch.json"), "cache_class": "temp", "size_bytes": 50, "age_seconds": 1},
                    {
                        "path": str(symlink),
                        "cache_class": "rebuildable_cache",
                        "size_bytes": 10,
                        "age_seconds": S2PMT04_DEFAULT_CACHE_TTL_SECONDS + 1,
                    },
                    {
                        "path": str(outside),
                        "cache_class": "rebuildable_cache",
                        "size_bytes": 10,
                        "age_seconds": S2PMT04_DEFAULT_CACHE_TTL_SECONDS + 1,
                    },
                ],
                whitelist_roots=[root],
                dry_run=True,
            )

        self.assertFalse(plan["durable_evidence_delete_allowed"])
        self.assertEqual(plan["candidate_count"], 2)
        self.assertEqual(plan["blocked_count"], 2)
        self.assertEqual(plan["retained"][0]["action"], "retain_durable_evidence")
        self.assertIn("symbolic links are not cleanup candidates", plan["blocked"][0]["blocking_reasons"])
        self.assertIn("path is outside cache cleanup whitelist", plan["blocked"][1]["blocking_reasons"])

    def test_cache_low_disk_degradation_blocks_new_downloads_and_keeps_durable_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = build_cache_cleanup_plan(
                cache_entries=[
                    {
                        "path": str(root / "raw" / "evidence.json"),
                        "cache_class": "durable_evidence",
                        "size_bytes": 100,
                        "age_seconds": S2PMT04_DEFAULT_CACHE_TTL_SECONDS * 2,
                    },
                    {
                        "path": str(root / "fulltext" / "old.txt"),
                        "cache_class": "rebuildable_cache",
                        "size_bytes": 200,
                        "age_seconds": S2PMT04_DEFAULT_CACHE_TTL_SECONDS + 1,
                    },
                ],
                whitelist_roots=[root],
                dry_run=True,
            )
            receipt = build_cache_low_disk_degradation_receipt(
                cleanup_plan=plan,
                free_disk_bytes=128 * 1024 * 1024,
                low_disk_threshold_bytes=512 * 1024 * 1024,
                generated_at="2026-07-03T06:00:00+10:00",
            )

        self.assertEqual(receipt["status"], "pass")
        self.assertTrue(receipt["low_disk_pressure"])
        self.assertFalse(receipt["new_downloads_allowed"])
        self.assertFalse(receipt["rebuildable_cache_writes_allowed"])
        self.assertFalse(receipt["durable_evidence_delete_allowed"])
        self.assertFalse(receipt["delete_apply_allowed"])
        self.assertFalse(receipt["queue_mutation_allowed"])
        self.assertIn("block_new_downloads", receipt["degradation_actions"])
        self.assertEqual(validate_cache_low_disk_degradation_receipt(receipt), [])

    def test_cache_low_disk_degradation_blocks_unsafe_degrade_receipt(self) -> None:
        receipt = build_cache_low_disk_degradation_receipt(
            cleanup_plan={"dry_run": True, "candidate_count": 1, "delete_bytes_dry_run": 200},
            free_disk_bytes=128,
            low_disk_threshold_bytes=512,
            generated_at="2026-07-03T06:00:00+10:00",
        )
        receipt["new_downloads_allowed"] = True
        receipt["durable_evidence_delete_allowed"] = True
        receipt["delete_apply_allowed"] = True

        errors = validate_cache_low_disk_degradation_receipt(receipt)

        self.assertIn("low disk pressure must block new downloads", errors)
        self.assertIn("durable evidence must never be deleted under low disk pressure", errors)
        self.assertIn("low disk degradation evidence must not apply deletes", errors)

    def test_launchd_plist_payload_is_parseable_disabled_and_escaped(self) -> None:
        payload = build_launchd_plist_payload(
            label="com.linze.adp.local.daily",
            program_arguments=("/bin/zsh", "-lc", "echo 'A&B' && python3 -m arxiv_daily_push local-runner daily"),
        )
        parsed = plistlib.loads(payload)

        self.assertEqual(validate_launchd_plist_payload(payload), [])
        self.assertTrue(parsed["Disabled"])
        self.assertFalse(parsed["RunAtLoad"])
        self.assertEqual(parsed["ProgramArguments"][0], "/bin/zsh")
        self.assertIn("A&B", parsed["ProgramArguments"][2])
        self.assertNotIn("EnvironmentVariables", parsed)

    def test_lifecycle_cache_report_passes_without_production_side_effects(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_lifecycle_cache_report(generated_at="2026-07-03T06:00:00+10:00", cache_root=tmp)

        self.assertEqual(report["status"], "pass")
        self.assertFalse(report["real_smtp_sent"])
        self.assertFalse(report["scheduler_installed"])
        self.assertFalse(report["queue_mutation_allowed"])
        self.assertTrue(report["gates"]["startup_convergence_count_conservation"])
        self.assertTrue(report["startup_convergence_receipt"]["count_conservation"])
        self.assertTrue(report["gates"]["transaction_completion_signal"])
        self.assertTrue(report["transaction_completion_receipt"]["interrupted_recoverable"])
        self.assertTrue(report["gates"]["cache_low_disk_degradation"])
        self.assertTrue(report["cache_low_disk_degradation_receipt"]["low_disk_pressure"])
        self.assertFalse(report["cache_low_disk_degradation_receipt"]["new_downloads_allowed"])
        self.assertTrue(report["gates"]["cache_cleanup_safety"])
        self.assertEqual(validate_lifecycle_cache_report(report), [])


if __name__ == "__main__":
    unittest.main()
