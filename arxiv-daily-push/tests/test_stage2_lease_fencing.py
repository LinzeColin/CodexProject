from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import threading
import unittest

from arxiv_daily_push.stage2_lease_fencing import (
    LocalLeaseClaimRepository,
    LocalOutboxClaimRepository,
    apply_fenced_state_transition,
    build_lease_fencing_report,
    build_m4_cycle_watermark,
    build_outbox_delivery_a003_report,
    build_outbox_message,
    claim_leased_item,
    claim_outbox_message,
    decide_watchdog_stale_lock_recovery,
    reconcile_smtp_accept_crash,
    simulate_fake_smtp_accept_after_kill,
    validate_lease_fencing_report,
    validate_outbox_delivery_a003_report,
)


class Stage2LeaseFencingTests(unittest.TestCase):
    def test_lease_claim_blocks_unexpired_foreign_owner_and_allows_expired_takeover(self) -> None:
        item = {"work_id": "cycle-1", "row_version": 0, "lease_owner": "worker-a", "lease_until_ms": 2000, "fencing_token": 1}

        blocked = claim_leased_item(item, owner_id="worker-b", now_ms=1000)
        takeover = claim_leased_item(item, owner_id="worker-b", now_ms=3000)

        self.assertEqual(blocked["status"], "blocked")
        self.assertIn("unexpired foreign lease blocks claim", blocked["blocking_reasons"])
        self.assertEqual(takeover["status"], "pass")
        self.assertEqual(takeover["item"]["lease_owner"], "worker-b")
        self.assertEqual(takeover["item"]["row_version"], 1)
        self.assertEqual(takeover["item"]["fencing_token"], 2)

    def test_atomic_claim_allows_only_one_of_100_concurrent_claimants(self) -> None:
        claimant_count = 100
        repo = LocalLeaseClaimRepository({"work_id": "cycle-1", "row_version": 0, "fencing_token": 0})
        barrier = threading.Barrier(claimant_count + 1)

        def claim(index: int) -> dict[str, object]:
            barrier.wait(timeout=5)
            return repo.claim(owner_id=f"worker-{index:03d}", expected_row_version=0, now_ms=1000)

        with ThreadPoolExecutor(max_workers=claimant_count) as executor:
            futures = [executor.submit(claim, index) for index in range(claimant_count)]
            barrier.wait(timeout=5)
            results = [future.result(timeout=5) for future in futures]

        passed = [result for result in results if result["status"] == "pass"]
        blocked = [result for result in results if result["status"] == "blocked"]

        self.assertEqual(len(passed), 1)
        self.assertEqual(len(blocked), claimant_count - 1)
        self.assertEqual(passed[0]["affected_rows"], 1)
        self.assertEqual(repo.snapshot()["row_version"], 1)
        self.assertEqual(repo.snapshot()["fencing_token"], 1)
        self.assertEqual(len(repo.events()), claimant_count)
        self.assertEqual(sum(1 for event in repo.events() if event["affected_rows"] == 1), 1)
        self.assertTrue(all(result["affected_rows"] == 0 for result in blocked))
        self.assertTrue(all("row_version compare-and-swap failed" in result["blocking_reasons"] for result in blocked))

    def test_fenced_transition_blocks_stale_row_version_and_token(self) -> None:
        record = {
            "current_state": "created",
            "row_version": 2,
            "fencing_token": 7,
            "state_history": [{"from_state": "", "to_state": "created"}],
        }

        stale = apply_fenced_state_transition(
            record,
            next_state="health_checked",
            expected_row_version=1,
            fencing_token=6,
            reason="stale",
            at="2026-07-02T06:00:00+10:00",
        )
        valid = apply_fenced_state_transition(
            record,
            next_state="health_checked",
            expected_row_version=2,
            fencing_token=7,
            reason="ok",
            at="2026-07-02T06:00:00+10:00",
        )

        self.assertEqual(stale["status"], "blocked")
        self.assertIn("row_version compare-and-swap failed", stale["blocking_reasons"])
        self.assertIn("fencing_token is stale", stale["blocking_reasons"])
        self.assertEqual(stale["affected_rows"], 0)
        self.assertEqual(valid["status"], "pass")
        self.assertEqual(valid["record"]["row_version"], 3)
        self.assertEqual(valid["affected_rows"], 1)
        self.assertEqual(valid["record"]["state_history"][-1]["from_state"], "created")

    def test_outbox_identity_is_idempotent_per_revision_and_claimed_once(self) -> None:
        first = build_outbox_message(
            cycle_id="2026-07-02",
            product_id="M1",
            recipient="linzezhang35@gmail.com",
            content_revision_id="rev-1",
            body="body",
            generated_at="2026-07-02T06:00:00+10:00",
        )
        retry = build_outbox_message(
            cycle_id="2026-07-02",
            product_id="M1",
            recipient="linzezhang35@gmail.com",
            content_revision_id="rev-1",
            body="body",
            generated_at="2026-07-02T06:00:00+10:00",
        )
        revised = build_outbox_message(
            cycle_id="2026-07-02",
            product_id="M1",
            recipient="linzezhang35@gmail.com",
            content_revision_id="rev-2",
            body="body changed",
            generated_at="2026-07-02T06:00:00+10:00",
        )

        claimed = claim_outbox_message(first, owner_id="sender-a", now_ms=1000)
        blocked_second_sender = claim_outbox_message(claimed["message"], owner_id="sender-b", now_ms=1001)

        self.assertEqual(first["message_id"], retry["message_id"])
        self.assertNotEqual(first["message_id"], revised["message_id"])
        self.assertEqual(claimed["status"], "pass")
        self.assertEqual(claimed["message"]["status"], "CLAIMED")
        self.assertEqual(blocked_second_sender["status"], "blocked")

    def test_outbox_claim_allows_only_one_of_100_concurrent_senders(self) -> None:
        claimant_count = 100
        message = build_outbox_message(
            cycle_id="2026-07-02",
            product_id="M1",
            recipient="linzezhang35@gmail.com",
            content_revision_id="rev-1",
            body="body",
            generated_at="2026-07-02T06:00:00+10:00",
        )
        repo = LocalOutboxClaimRepository(message)
        barrier = threading.Barrier(claimant_count + 1)

        def claim(index: int) -> dict[str, object]:
            barrier.wait(timeout=5)
            return repo.claim(owner_id=f"sender-{index:03d}", expected_row_version=0, now_ms=1000 + index)

        with ThreadPoolExecutor(max_workers=claimant_count) as executor:
            futures = [executor.submit(claim, index) for index in range(claimant_count)]
            barrier.wait(timeout=5)
            results = [future.result(timeout=5) for future in futures]

        passed = [result for result in results if result["status"] == "pass"]
        blocked = [result for result in results if result["status"] == "blocked"]

        self.assertEqual(len(passed), 1)
        self.assertEqual(len(blocked), claimant_count - 1)
        self.assertEqual(passed[0]["affected_rows"], 1)
        self.assertEqual(repo.snapshot()["status"], "CLAIMED")
        self.assertEqual(repo.snapshot()["row_version"], 1)
        self.assertEqual(repo.snapshot()["send_attempts"], 1)
        self.assertEqual(len(repo.events()), claimant_count)
        self.assertEqual(sum(1 for event in repo.events() if event["affected_rows"] == 1), 1)
        self.assertTrue(all(result["affected_rows"] == 0 for result in blocked))
        self.assertTrue(all("row_version compare-and-swap failed" in result["blocking_reasons"] for result in blocked))

    def test_smtp_accept_crash_window_requires_provider_ref_before_resolution(self) -> None:
        message = build_outbox_message(
            cycle_id="2026-07-02",
            product_id="M1",
            recipient="linzezhang35@gmail.com",
            content_revision_id="rev-1",
            body="body",
            generated_at="2026-07-02T06:00:00+10:00",
        )
        message["status"] = "ACCEPTED_PENDING_COMMIT"

        blocked = reconcile_smtp_accept_crash(message)
        resolved = reconcile_smtp_accept_crash(message, provider_accept_ref="smtp://provider/message-1")

        self.assertEqual(blocked["status"], "blocked")
        self.assertFalse(blocked["message"]["retry_safe"])
        self.assertEqual(resolved["status"], "pass")
        self.assertEqual(resolved["message"]["status"], "SENT")
        self.assertFalse(resolved["message"]["real_smtp_sent"])

    def test_outbox_reclaim_blocks_not_retry_safe_or_terminal_rows_after_lease_expiry(self) -> None:
        message = build_outbox_message(
            cycle_id="2026-07-02",
            product_id="M1",
            recipient="linzezhang35@gmail.com",
            content_revision_id="rev-1",
            body="body",
            generated_at="2026-07-02T06:00:00+10:00",
        )
        claimed = claim_outbox_message(message, owner_id="sender-a", now_ms=1000)
        accepted = dict(claimed["message"])
        accepted["status"] = "ACCEPTED_PENDING_COMMIT"

        pending_commit_claim = claim_outbox_message(accepted, owner_id="sender-b", now_ms=999999)
        fail_closed = reconcile_smtp_accept_crash(accepted)
        finalized = reconcile_smtp_accept_crash(accepted, provider_accept_ref="smtp://provider/message-1")

        blocked_repo = LocalOutboxClaimRepository(fail_closed["message"])
        blocked_reclaim = blocked_repo.claim(
            owner_id="sender-b",
            expected_row_version=fail_closed["message"]["row_version"],
            now_ms=999999,
        )
        sent_repo = LocalOutboxClaimRepository(finalized["message"])
        sent_reclaim = sent_repo.claim(
            owner_id="sender-b",
            expected_row_version=finalized["message"]["row_version"],
            now_ms=999999,
        )

        self.assertEqual(pending_commit_claim["status"], "blocked")
        self.assertIn(
            "outbox status requires provider accept reconciliation before claim",
            pending_commit_claim["blocking_reasons"],
        )
        self.assertEqual(blocked_reclaim["status"], "blocked")
        self.assertEqual(blocked_reclaim["affected_rows"], 0)
        self.assertIn("outbox row is marked not retry safe", blocked_reclaim["blocking_reasons"])
        self.assertEqual(blocked_repo.snapshot()["status"], "BLOCKED")
        self.assertEqual(blocked_repo.snapshot()["send_attempts"], 1)
        self.assertEqual(sent_reclaim["status"], "blocked")
        self.assertEqual(sent_reclaim["affected_rows"], 0)
        self.assertIn("outbox row is marked not retry safe", sent_reclaim["blocking_reasons"])
        self.assertEqual(sent_repo.snapshot()["status"], "SENT")
        self.assertEqual(sent_repo.snapshot()["send_attempts"], 1)

    def test_fake_smtp_accept_after_kill_blocks_restart_without_provider_ref(self) -> None:
        harness = simulate_fake_smtp_accept_after_kill(
            cycle_id="2026-07-02",
            product_id="M1",
            recipient="linzezhang35@gmail.com",
            content_revision_id="rev-1",
            body="body",
            generated_at="2026-07-02T06:00:00+10:00",
        )

        self.assertEqual(harness["status"], "blocked")
        self.assertFalse(harness["real_smtp_sent"])
        self.assertFalse(harness["duplicate_resend_allowed"])
        self.assertFalse(harness["crash_marker"]["provider_accept_ref_recorded"])
        self.assertTrue(harness["crash_marker"]["runner_killed"])
        self.assertTrue(harness["message_id_stable"])
        self.assertTrue(harness["mail_key_stable"])
        self.assertIn("provider_accept_ref is required", harness["blocking_reasons"][0])

    def test_fake_smtp_accept_after_kill_reconciles_with_provider_ref_without_retry(self) -> None:
        harness = simulate_fake_smtp_accept_after_kill(
            cycle_id="2026-07-02",
            product_id="M1",
            recipient="linzezhang35@gmail.com",
            content_revision_id="rev-1",
            body="body",
            generated_at="2026-07-02T06:00:00+10:00",
            provider_accept_ref="smtp-accept://fake-provider/message-1",
        )

        self.assertEqual(harness["status"], "pass")
        self.assertFalse(harness["real_smtp_sent"])
        self.assertFalse(harness["duplicate_resend_allowed"])
        self.assertFalse(harness["retry_safe"])
        self.assertTrue(harness["crash_marker"]["provider_accept_ref_recorded"])
        self.assertTrue(harness["message_id_stable"])
        self.assertEqual(harness["restart_reconciliation"]["message"]["status"], "SENT")
        self.assertEqual(
            harness["restart_reconciliation"]["message"]["provider_accept_ref"],
            "smtp-accept://fake-provider/message-1",
        )

    def test_watchdog_recovery_blocks_live_owner_and_recovers_dead_stale_lock(self) -> None:
        stale_lock = {
            "work_id": "cycle-20260702-M2",
            "row_version": 4,
            "lease_owner": "slow-worker",
            "lease_until_ms": 1000,
            "fencing_token": 9,
        }
        live_owner = decide_watchdog_stale_lock_recovery(
            stale_lock,
            recovery_owner_id="watchdog",
            now_ms=2000,
            live_owner_ids={"slow-worker"},
        )
        dead_owner = decide_watchdog_stale_lock_recovery(
            {**stale_lock, "lease_owner": "dead-worker"},
            recovery_owner_id="watchdog",
            now_ms=2000,
            live_owner_ids=set(),
        )

        self.assertEqual(live_owner["status"], "blocked")
        self.assertFalse(live_owner["safe_takeover"])
        self.assertIn("lease owner is still live; watchdog recovery is forbidden", live_owner["blocking_reasons"])
        self.assertEqual(dead_owner["status"], "pass")
        self.assertTrue(dead_owner["safe_takeover"])
        self.assertEqual(dead_owner["lock"]["lease_owner"], "watchdog")
        self.assertEqual(dead_owner["lock"]["row_version"], 5)
        self.assertEqual(dead_owner["lock"]["fencing_token"], 10)

    def test_watchdog_recovery_blocks_unexpired_dead_owner_lock(self) -> None:
        active_lease = decide_watchdog_stale_lock_recovery(
            {
                "work_id": "cycle-20260702-M3",
                "row_version": 0,
                "lease_owner": "dead-worker",
                "lease_until_ms": 3000,
                "fencing_token": 1,
            },
            recovery_owner_id="watchdog",
            now_ms=2000,
            live_owner_ids=set(),
        )

        self.assertEqual(active_lease["status"], "blocked")
        self.assertEqual(active_lease["affected_rows"], 0)
        self.assertIn("lease has not expired", active_lease["blocking_reasons"])


    def test_m4_watermark_is_cycle_scoped_and_degrades_after_deadline(self) -> None:
        ready = build_m4_cycle_watermark(
            cycle_id="2026-07-02",
            generated_at="2026-07-02T22:00:00+10:00",
            terminal_mails=[
                {"cycle_id": "2026-07-02", "product_id": "M1", "status": "SENT"},
                {"cycle_id": "2026-07-02", "product_id": "M2", "status": "SENT"},
                {"cycle_id": "2026-07-02", "product_id": "M3", "status": "DEGRADED"},
            ],
            deadline_passed=True,
        )
        wrong_cycle = build_m4_cycle_watermark(
            cycle_id="2026-07-02",
            generated_at="2026-07-02T22:00:00+10:00",
            terminal_mails=[
                {"cycle_id": "2026-07-02", "product_id": "M1", "status": "SENT"},
                {"cycle_id": "2026-07-03", "product_id": "M2", "status": "SENT"},
                {"cycle_id": "2026-07-02", "product_id": "M3", "status": "SENT"},
            ],
            deadline_passed=True,
        )

        self.assertEqual(ready["status"], "ready")
        self.assertTrue(ready["m4_ready"])
        self.assertEqual(wrong_cycle["status"], "degraded")
        self.assertIn("M2 cycle_id does not match", wrong_cycle["blocking_reasons"])

    def test_m4_watermark_degrades_m2_failed_and_m3_timeout_after_deadline(self) -> None:
        watermark = build_m4_cycle_watermark(
            cycle_id="2026-07-02",
            generated_at="2026-07-02T22:30:00+10:00",
            terminal_mails=[
                {"cycle_id": "2026-07-02", "product_id": "M1", "status": "SENT"},
                {"cycle_id": "2026-07-02", "product_id": "M2", "status": "FAILED"},
                {"cycle_id": "2026-07-02", "product_id": "M3", "status": "TIMEOUT"},
            ],
            deadline_passed=True,
        )

        self.assertEqual(watermark["status"], "degraded")
        self.assertFalse(watermark["m4_ready"])
        self.assertTrue(watermark["m4_cycle_watermark"])
        self.assertIn("M2 terminal status failed", watermark["blocking_reasons"])
        self.assertIn("M3 terminal status timed out", watermark["blocking_reasons"])
        self.assertFalse(watermark["retry_safe"])
        self.assertEqual(watermark["watermark_finalized_at"], "2026-07-02T22:30:00+10:00")

    def test_m4_watermark_waits_before_deadline_and_is_idempotent_on_rerun(self) -> None:
        kwargs = {
            "cycle_id": "2026-07-02",
            "generated_at": "2026-07-02T20:00:00+10:00",
            "terminal_mails": [
                {"cycle_id": "2026-07-02", "product_id": "M1", "status": "SENT"},
                {"cycle_id": "2026-07-02", "product_id": "M2", "status": "SENT"},
            ],
            "deadline_passed": False,
        }

        first = build_m4_cycle_watermark(**kwargs)
        rerun = build_m4_cycle_watermark(**kwargs)

        self.assertEqual(first, rerun)
        self.assertEqual(first["status"], "waiting")
        self.assertTrue(first["retry_safe"])
        self.assertFalse(first["m4_cycle_watermark"])
        self.assertIn("M3 terminal mail is missing", first["blocking_reasons"])

    def test_m4_watermark_ignores_late_terminal_after_finalized_degradation(self) -> None:
        degraded = build_m4_cycle_watermark(
            cycle_id="2026-07-02",
            generated_at="2026-07-02T22:00:00+10:00",
            terminal_mails=[
                {"cycle_id": "2026-07-02", "product_id": "M1", "status": "SENT", "observed_at": "2026-07-02T21:00:00+10:00"},
                {"cycle_id": "2026-07-02", "product_id": "M2", "status": "SENT", "observed_at": "2026-07-02T21:01:00+10:00"},
            ],
            deadline_passed=True,
        )
        late = build_m4_cycle_watermark(
            cycle_id="2026-07-02",
            generated_at="2026-07-02T22:05:00+10:00",
            terminal_mails=[
                {"cycle_id": "2026-07-02", "product_id": "M1", "status": "SENT", "observed_at": "2026-07-02T21:00:00+10:00"},
                {"cycle_id": "2026-07-02", "product_id": "M2", "status": "SENT", "observed_at": "2026-07-02T21:01:00+10:00"},
                {"cycle_id": "2026-07-02", "product_id": "M3", "status": "SENT", "observed_at": "2026-07-02T22:03:00+10:00"},
            ],
            deadline_passed=True,
            previous_watermark=degraded,
        )

        self.assertEqual(degraded["status"], "degraded")
        self.assertEqual(late["status"], "degraded")
        self.assertTrue(late["late_data_ignored"])
        self.assertEqual(late["ignored_late_terminal_mails"][0]["product_id"], "M3")
        self.assertIn("M3 terminal mail is missing after deadline", late["blocking_reasons"])

    def test_lease_fencing_report_passes_without_production_side_effects(self) -> None:
        report = build_lease_fencing_report(generated_at="2026-07-02T06:00:00+10:00")

        self.assertEqual(report["status"], "pass")
        self.assertFalse(report["exactly_once_claimed"])
        self.assertFalse(report["real_smtp_sent"])
        self.assertFalse(report["queue_mutation_allowed"])
        self.assertTrue(report["gates"]["watchdog_stale_lock_recovery"])
        self.assertEqual(validate_lease_fencing_report(report), [])

    def test_outbox_delivery_a003_report_passes_without_exactly_once_or_smtp(self) -> None:
        report = build_outbox_delivery_a003_report(generated_at="2026-07-02T06:00:00+10:00")

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["finding_id"], "A-003")
        self.assertEqual(report["delivery_semantics"], "at_least_once_with_idempotent_message_id")
        self.assertFalse(report["exactly_once_claimed"])
        self.assertFalse(report["real_smtp_sent"])
        self.assertFalse(report["scheduler_enabled"])
        self.assertFalse(report["source_adapter_changed"])
        self.assertEqual(report["claim_contention"]["claim_attempts"], 100)
        self.assertEqual(report["claim_contention"]["passed_claims"], 1)
        self.assertEqual(report["claim_contention"]["blocked_claims"], 99)
        self.assertTrue(report["probes"]["message_identity_same_revision"])
        self.assertTrue(report["probes"]["message_identity_revision_change"])
        self.assertTrue(report["gates"]["provider_accept_finalizes_without_resend"])
        self.assertTrue(report["gates"]["fail_closed_not_retry_safe_not_reclaimed"])
        self.assertTrue(report["gates"]["provider_finalized_not_reclaimed"])
        self.assertEqual(report["smtp_accept_pending_commit_reclaim"]["status"], "blocked")
        self.assertEqual(report["provider_accept_finalization_reclaim"]["status"], "blocked")
        self.assertEqual(validate_outbox_delivery_a003_report(report), [])

    def test_outbox_delivery_a003_report_blocks_exactly_once_or_missing_gate(self) -> None:
        report = build_outbox_delivery_a003_report(generated_at="2026-07-02T06:00:00+10:00")
        report["exactly_once_claimed"] = True
        report["gates"]["single_outbox_claim_under_contention"] = False

        errors = validate_outbox_delivery_a003_report(report)

        self.assertIn("S2PMT03 A-003 report must not claim exactly-once delivery", errors)
        self.assertIn("passing S2PMT03 A-003 report requires all gates true", errors)


if __name__ == "__main__":
    unittest.main()
