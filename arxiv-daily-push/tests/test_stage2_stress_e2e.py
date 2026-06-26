from __future__ import annotations

import unittest

from arxiv_daily_push.stage2_stress_e2e import (
    S2PMT05_CLOCK_SKEW_TOLERANCE_SECONDS,
    S2PMT05_REPLAY_DAYS_REQUIRED,
    S2PMT05_REQUIRED_FINDINGS,
    S2PMT05_REQUIRED_MAIL_PRODUCTS,
    S2PMT05_REQUIRED_PRODUCTION_FALSE_FLAGS,
    S2PMT05_SOAK_HOURS_REQUIRED,
    build_35_day_e2e_fixture,
    build_fault_injection_matrix,
    build_result_validity_fixture,
    build_s2pmt05_report,
    build_workload_profile,
    evaluate_backpressure_policy,
    evaluate_dst_clock_policy,
    evaluate_load_stress_spike_soak,
    evaluate_result_validity,
    simulate_dual_scheduler_race,
    simulate_smtp_crash_window,
    validate_s2pmt05_report,
)


class Stage2StressE2ETests(unittest.TestCase):
    def test_load_stress_spike_soak_profile_passes_with_accelerated_local_soak(self) -> None:
        profile = build_workload_profile(generated_at="2026-07-04T06:00:00+10:00")
        evaluation = evaluate_load_stress_spike_soak(profile)

        self.assertEqual(evaluation["status"], "pass")
        self.assertTrue(profile["accelerated_simulation"])
        self.assertFalse(profile["real_24h_wall_clock_run"])
        self.assertGreaterEqual(profile["soak"]["duration_hours"], S2PMT05_SOAK_HOURS_REQUIRED)
        self.assertEqual(profile["load"]["duplicate_active_messages"], 0)
        self.assertGreater(profile["spike"]["shed_messages"], 0)
        self.assertFalse(profile["spike"]["durable_evidence_dropped"])
        self.assertTrue(evaluation["checks"]["sqlite_busy_policy_present"])

    def test_dual_scheduler_race_keeps_one_active_revision_per_mail_product(self) -> None:
        race = simulate_dual_scheduler_race(cycle_id="2026-07-04", trigger_count=100)

        self.assertEqual(race["status"], "pass")
        self.assertFalse(race["scheduler_installed"])
        self.assertFalse(race["scheduler_enabled"])
        self.assertEqual(race["attempted_revisions"], 400)
        self.assertEqual(race["blocked_race_attempts"], 396)
        self.assertEqual(race["duplicate_active_revisions"], 0)
        self.assertEqual([row["product_id"] for row in race["active_revisions"]], list(S2PMT05_REQUIRED_MAIL_PRODUCTS))

    def test_smtp_crash_window_blocks_resend_without_provider_reference(self) -> None:
        crash = simulate_smtp_crash_window(generated_at="2026-07-04T06:00:00+10:00")

        self.assertEqual(crash["status"], "pass")
        self.assertFalse(crash["real_smtp_sent"])
        self.assertFalse(crash["resend_without_provider_ref_allowed"])
        self.assertEqual(crash["accepted_without_commit"]["status"], "blocked")
        self.assertIn("provider_accept_ref is required", crash["accepted_without_commit"]["blocking_reasons"][0])
        self.assertEqual(crash["accepted_with_provider_ref"]["message"]["status"], "SENT")

    def test_fault_injection_matrix_covers_storage_sqlite_and_corrupt_artifacts(self) -> None:
        matrix = build_fault_injection_matrix(generated_at="2026-07-04T06:00:00+10:00")
        faults = {row["fault"] for row in matrix["scenarios"]}

        self.assertEqual(matrix["status"], "pass")
        self.assertEqual(
            faults,
            {"ENOSPC", "EACCES_READ_ONLY_DIR", "SQLITE_BUSY", "CORRUPT_CACHE_JSON", "CORRUPT_BACKUP_MANIFEST"},
        )
        self.assertGreaterEqual(matrix["sqlite_busy_timeout_ms"], 5000)
        self.assertTrue(all(row["fail_closed"] for row in matrix["scenarios"]))
        self.assertTrue(all(not row["production_mutation_applied"] for row in matrix["scenarios"]))

    def test_dst_and_clock_skew_policy_blocks_future_heartbeat_and_handles_folds(self) -> None:
        policy = evaluate_dst_clock_policy()

        self.assertEqual(policy["status"], "pass")
        self.assertEqual(policy["timezone"], "Australia/Sydney")
        self.assertEqual(policy["clock_skew_tolerance_seconds"], S2PMT05_CLOCK_SKEW_TOLERANCE_SECONDS)
        self.assertEqual(policy["future_heartbeat_seconds"], S2PMT05_CLOCK_SKEW_TOLERANCE_SECONDS + 1)
        self.assertEqual(policy["future_heartbeat_action"], "block_until_owner_review")
        self.assertTrue(policy["checks"]["dst_fold_records_offset"])
        self.assertTrue(policy["checks"]["catchup_is_bounded"])

    def test_35_day_e2e_fixture_covers_daily_weekly_monthly_review_action_roi(self) -> None:
        fixture = build_35_day_e2e_fixture()
        sections = fixture["sections"]

        self.assertEqual(fixture["status"], "pass")
        self.assertEqual(fixture["days"], S2PMT05_REPLAY_DAYS_REQUIRED)
        self.assertEqual(sections["daily_3_plus_1"]["mail_count"], 140)
        self.assertEqual(sections["weekly_report"]["report_count"], 5)
        self.assertGreaterEqual(sections["monthly_report"]["report_count"], 1)
        self.assertEqual(sections["review"]["records"], sections["action"]["linked_review_records"])
        self.assertEqual(sections["action"]["records"], sections["roi"]["linked_action_records"])

    def test_result_validity_gate_requires_semantic_evidence_and_non_template_output(self) -> None:
        fixture = build_result_validity_fixture(generated_at="2026-07-04T06:00:00+10:00")

        self.assertEqual(fixture["status"], "pass")
        self.assertEqual(len(fixture["publish_records"]), 3)
        self.assertTrue(fixture["checks"]["semantic_alignment_threshold"])
        self.assertTrue(fixture["checks"]["claim_ledger_refs_present"])
        self.assertTrue(fixture["checks"]["evidence_refs_present"])
        self.assertTrue(fixture["checks"]["mechanism_and_action_specific"])
        self.assertTrue(fixture["checks"]["non_template_variance"])
        self.assertTrue(fixture["checks"]["unsupported_claims_blocked"])

    def test_result_validity_gate_blocks_missing_evidence_and_template_reuse(self) -> None:
        fixture = build_result_validity_fixture(generated_at="2026-07-04T06:00:00+10:00")
        publish_records = [dict(row) for row in fixture["publish_records"]]
        publish_records[0]["evidence_refs"] = []
        for row in publish_records:
            row["template_signature"] = "same-template"

        evaluation = evaluate_result_validity(
            publish_records=publish_records,
            negative_controls=fixture["negative_controls"],
        )

        self.assertEqual(evaluation["status"], "blocked")
        self.assertIn("evidence_refs_present", evaluation["blocking_reasons"])
        self.assertIn("non_template_variance", evaluation["blocking_reasons"])

    def test_backpressure_policy_sheds_without_dropping_durable_evidence(self) -> None:
        policy = evaluate_backpressure_policy(queue_depth=15000, capacity=10000)

        self.assertEqual(policy["status"], "pass")
        self.assertEqual(policy["shed_count"], 5000)
        self.assertTrue(policy["checks"]["keeps_durable_evidence"])
        self.assertTrue(policy["checks"]["opens_circuit_breaker_on_repeated_faults"])
        self.assertTrue(policy["checks"]["deadline_aware_degradation"])

    def test_full_s2pmt05_report_validates_without_production_side_effects(self) -> None:
        report = build_s2pmt05_report(generated_at="2026-07-04T06:00:00+10:00")

        self.assertEqual(report["status"], "pass")
        self.assertFalse(report["production_acceptance_claimed"])
        self.assertFalse(report["inherited_p0_p1_closed"])
        self.assertEqual(set(report["findings_covered"]), set(S2PMT05_REQUIRED_FINDINGS))
        self.assertTrue(report["gates"]["result_validity_semantic_evidence"])
        self.assertEqual(report["findings_covered"]["B-013"], ["result_validity_semantic_evidence"])
        for flag in S2PMT05_REQUIRED_PRODUCTION_FALSE_FLAGS:
            self.assertFalse(report[flag])
        self.assertEqual(validate_s2pmt05_report(report), [])

        tampered = dict(report)
        tampered["scheduler_enabled"] = True
        self.assertIn("scheduler_enabled must be false", validate_s2pmt05_report(tampered))


if __name__ == "__main__":
    unittest.main()
