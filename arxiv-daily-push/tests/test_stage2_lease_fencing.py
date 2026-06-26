from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import threading
import unittest

from arxiv_daily_push.stage2_lease_fencing import (
    LocalLeaseClaimRepository,
    apply_fenced_state_transition,
    build_lease_fencing_report,
    build_m4_cycle_watermark,
    build_outbox_message,
    claim_leased_item,
    claim_outbox_message,
    reconcile_smtp_accept_crash,
    validate_lease_fencing_report,
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

    def test_lease_fencing_report_passes_without_production_side_effects(self) -> None:
        report = build_lease_fencing_report(generated_at="2026-07-02T06:00:00+10:00")

        self.assertEqual(report["status"], "pass")
        self.assertFalse(report["exactly_once_claimed"])
        self.assertFalse(report["real_smtp_sent"])
        self.assertFalse(report["queue_mutation_allowed"])
        self.assertEqual(validate_lease_fencing_report(report), [])


if __name__ == "__main__":
    unittest.main()
