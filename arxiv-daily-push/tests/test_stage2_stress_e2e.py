from __future__ import annotations

import unittest

from arxiv_daily_push.stage2_stress_e2e import (
    S2PMT05_BACKPRESSURE_HIGH_PRIORITY_SLO_SECONDS,
    S2PMT05_BACKPRESSURE_PEAK_MULTIPLIERS,
    S2PMT05_CAPACITY_BASELINE_MAX_QUEUE_AGE_SECONDS,
    S2PMT05_CAPACITY_BASELINE_MULTIPLIERS,
    S2PMT05_CATCHUP_MAX_RUNS_PER_CYCLE,
    S2PMT05_CLOCK_SKEW_TOLERANCE_SECONDS,
    S2PMT05_MISFIRE_GRACE_SECONDS,
    S2PMT05_REPLAY_DAYS_REQUIRED,
    S2PMT05_REQUIRED_FAULTS,
    S2PMT05_REQUIRED_FAULT_RECOVERY_STATES,
    S2PMT05_REQUIRED_FINDINGS,
    S2PMT05_REQUIRED_MAIL_PRODUCTS,
    S2PMT05_REQUIRED_PRODUCTION_FALSE_FLAGS,
    S2PMT05_REQUIRED_TIME_POLICY_CASES,
    S2PMT05_SCHEDULE_LOCAL_TIME,
    S2PMT05_SOAK_HOURS_REQUIRED,
    S2PMT05_SLEEP_MISFIRE_HOURS,
    build_35_day_e2e_fixture,
    build_capacity_baseline_model,
    build_fault_injection_matrix,
    build_result_validity_fixture,
    build_s2pmt05_report,
    build_time_policy_cases,
    build_time_schedule_policy,
    build_workload_profile,
    evaluate_backpressure_policy,
    evaluate_capacity_baseline_model,
    evaluate_dst_clock_policy,
    evaluate_fault_injection_matrix,
    evaluate_load_stress_spike_soak,
    evaluate_result_validity,
    evaluate_time_policy_cases,
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

    def test_capacity_baseline_model_covers_formal_load_stress_spike_and_soak_metrics(self) -> None:
        baseline = build_capacity_baseline_model(generated_at="2026-07-04T06:00:00+10:00")

        self.assertEqual(baseline["status"], "pass")
        self.assertFalse(baseline["real_24h_wall_clock_run"])
        self.assertEqual(set(baseline["required_multipliers"]), set(S2PMT05_CAPACITY_BASELINE_MULTIPLIERS))
        self.assertEqual(baseline["max_queue_age_seconds"], S2PMT05_CAPACITY_BASELINE_MAX_QUEUE_AGE_SECONDS)
        self.assertTrue(baseline["checks"]["load_stress_spike_soak_rows_present"])
        self.assertTrue(baseline["checks"]["throughput_latency_queue_metrics_present"])
        self.assertTrue(baseline["checks"]["queue_age_bounded_and_recoverable"])
        self.assertTrue(baseline["checks"]["memory_disk_metrics_present"])
        self.assertTrue(baseline["checks"]["error_rate_within_budget"])
        rows = {row["phase"]: row for row in baseline["rows"]}
        self.assertEqual(rows["soak"]["duration_hours"], S2PMT05_SOAK_HOURS_REQUIRED)
        self.assertGreater(rows["spike"]["shed_rebuildable_items"], 0)
        self.assertFalse(rows["spike"]["durable_evidence_dropped"])

    def test_capacity_baseline_model_blocks_missing_peak_and_unbounded_queue(self) -> None:
        baseline = build_capacity_baseline_model(generated_at="2026-07-04T06:00:00+10:00")
        rows = [dict(row) for row in baseline["rows"] if not (row["phase"] == "spike" and row["multiplier"] == 5)]
        rows[1]["max_queue_age_seconds"] = S2PMT05_CAPACITY_BASELINE_MAX_QUEUE_AGE_SECONDS + 1
        rows[1]["min_free_disk_mb"] = 0

        evaluation = evaluate_capacity_baseline_model(rows=rows)

        self.assertEqual(evaluation["status"], "blocked")
        self.assertFalse(evaluation["checks"]["required_multipliers_present"])
        self.assertFalse(evaluation["checks"]["queue_age_bounded_and_recoverable"])
        self.assertFalse(evaluation["checks"]["memory_disk_metrics_present"])

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
        recovery_states = {row["resulting_state"] for row in matrix["scenarios"]}

        self.assertEqual(matrix["status"], "pass")
        self.assertEqual(faults, set(S2PMT05_REQUIRED_FAULTS))
        self.assertEqual(recovery_states, set(S2PMT05_REQUIRED_FAULT_RECOVERY_STATES))
        self.assertGreaterEqual(matrix["sqlite_busy_timeout_ms"], 5000)
        self.assertTrue(matrix["checks"]["required_faults_present"])
        self.assertTrue(matrix["checks"]["required_recovery_states_present"])
        self.assertTrue(matrix["checks"]["no_partial_artifact_commit"])
        self.assertTrue(matrix["checks"]["corrupt_pdf_rebuilds_from_source"])
        self.assertTrue(matrix["checks"]["backup_faults_block_restore_or_publish"])
        self.assertTrue(all(row["fail_closed"] for row in matrix["scenarios"]))
        self.assertTrue(all(not row["production_mutation_applied"] for row in matrix["scenarios"]))

    def test_fault_injection_matrix_blocks_missing_pdf_backup_and_partial_commit(self) -> None:
        matrix = build_fault_injection_matrix(generated_at="2026-07-04T06:00:00+10:00")
        scenarios = [
            dict(row)
            for row in matrix["scenarios"]
            if row["fault"] not in {"CORRUPT_PDF_ARTIFACT", "BACKUP_PATH_COLLISION"}
        ]
        scenarios[0]["partial_artifact_committed"] = True
        scenarios[1]["production_mutation_applied"] = True

        evaluation = evaluate_fault_injection_matrix(scenarios=scenarios)

        self.assertEqual(evaluation["status"], "blocked")
        self.assertFalse(evaluation["checks"]["required_faults_present"])
        self.assertFalse(evaluation["checks"]["required_recovery_states_present"])
        self.assertFalse(evaluation["checks"]["no_partial_artifact_commit"])
        self.assertFalse(evaluation["checks"]["no_production_mutation_applied"])
        self.assertFalse(evaluation["checks"]["corrupt_pdf_rebuilds_from_source"])
        self.assertFalse(evaluation["checks"]["backup_faults_block_restore_or_publish"])

    def test_dst_and_clock_skew_policy_blocks_future_heartbeat_and_handles_folds(self) -> None:
        policy = evaluate_dst_clock_policy()
        cases = {row["case_id"]: row for row in policy["cases"]}

        self.assertEqual(policy["status"], "pass")
        self.assertEqual(policy["timezone"], "Australia/Sydney")
        self.assertEqual(policy["clock_skew_tolerance_seconds"], S2PMT05_CLOCK_SKEW_TOLERANCE_SECONDS)
        self.assertEqual(policy["future_heartbeat_seconds"], S2PMT05_CLOCK_SKEW_TOLERANCE_SECONDS + 1)
        self.assertEqual(policy["future_heartbeat_action"], "block_until_owner_review")
        self.assertEqual(policy["schedule_policy"]["local_time"], S2PMT05_SCHEDULE_LOCAL_TIME)
        self.assertEqual(policy["schedule_policy"]["misfire_grace_seconds"], S2PMT05_MISFIRE_GRACE_SECONDS)
        self.assertEqual(policy["schedule_policy"]["sleep_misfire_hours"], S2PMT05_SLEEP_MISFIRE_HOURS)
        self.assertEqual(policy["schedule_policy"]["catch_up_max_runs_per_cycle"], S2PMT05_CATCHUP_MAX_RUNS_PER_CYCLE)
        self.assertEqual(set(policy["required_time_policy_cases"]), set(S2PMT05_REQUIRED_TIME_POLICY_CASES))
        self.assertEqual(set(cases), set(S2PMT05_REQUIRED_TIME_POLICY_CASES))
        self.assertEqual(cases["MISFIRE_WITHIN_GRACE"]["misfire_lag_seconds"], 1800)
        self.assertEqual(cases["MISFIRE_WITHIN_GRACE"]["catchup_run_count"], S2PMT05_CATCHUP_MAX_RUNS_PER_CYCLE)
        self.assertEqual(cases["SLEEP_MISSED_8H"]["missed_run_hours"], S2PMT05_SLEEP_MISFIRE_HOURS)
        self.assertEqual(cases["SLEEP_MISSED_8H"]["duplicate_m4_count"], 0)
        self.assertEqual(cases["NTP_BACKWARD_WITHIN_TOLERANCE"]["action"], "ALLOW_MONOTONIC_LEASE_KEEP_UTC_AUDIT")
        self.assertEqual(cases["NTP_FORWARD_GT_TOLERANCE"]["action"], "CLOCK_TIMEZONE_FAIL")
        self.assertTrue(policy["checks"]["dst_fold_records_offset"])
        self.assertTrue(policy["checks"]["dst_gap_runs_after_gap"])
        self.assertTrue(policy["checks"]["misfire_within_grace_runs_once"])
        self.assertTrue(policy["checks"]["sleep_8h_catchup_bounded"])
        self.assertTrue(policy["checks"]["ntp_backward_within_tolerance_allows"])
        self.assertTrue(policy["checks"]["ntp_forward_over_tolerance_blocks"])
        self.assertTrue(policy["checks"]["catchup_is_bounded"])
        self.assertTrue(policy["checks"]["no_duplicate_m4_watermark"])
        self.assertTrue(policy["checks"]["scheduler_side_effects_disabled"])

    def test_time_policy_blocks_missing_sleep_ntp_and_unbounded_catchup(self) -> None:
        schedule_policy = build_time_schedule_policy()
        cases = [
            dict(row)
            for row in build_time_policy_cases()
            if row["case_id"] not in {"SLEEP_MISSED_8H", "NTP_FORWARD_GT_TOLERANCE"}
        ]
        for row in cases:
            if row["case_id"] == "MISFIRE_WITHIN_GRACE":
                row["catchup_run_count"] = S2PMT05_CATCHUP_MAX_RUNS_PER_CYCLE + 1

        evaluation = evaluate_time_policy_cases(cases=cases, schedule_policy=schedule_policy)

        self.assertEqual(evaluation["status"], "blocked")
        self.assertFalse(evaluation["checks"]["required_time_policy_cases_present"])
        self.assertFalse(evaluation["checks"]["ntp_forward_over_tolerance_blocks"])
        self.assertFalse(evaluation["checks"]["misfire_within_grace_runs_once"])
        self.assertFalse(evaluation["checks"]["sleep_8h_catchup_bounded"])
        self.assertFalse(evaluation["checks"]["catchup_is_bounded"])

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
        self.assertEqual(set(policy["required_peak_multipliers"]), set(S2PMT05_BACKPRESSURE_PEAK_MULTIPLIERS))
        self.assertEqual(policy["high_priority_slo_seconds"], S2PMT05_BACKPRESSURE_HIGH_PRIORITY_SLO_SECONDS)
        self.assertTrue(policy["checks"]["covers_2x_and_5x_peak_profiles"])
        self.assertTrue(policy["checks"]["high_priority_slo_met"])
        self.assertTrue(policy["checks"]["low_priority_delay_or_drop_has_reasons"])
        self.assertTrue(policy["checks"]["keeps_durable_evidence"])
        self.assertTrue(policy["checks"]["opens_circuit_breaker_on_repeated_faults"])
        self.assertTrue(policy["checks"]["deadline_aware_degradation"])
        high_priority = [row for row in policy["peak_profiles"] if row["priority"] == "high"]
        low_priority = [row for row in policy["peak_profiles"] if row["priority"] == "low"]
        self.assertEqual({row["peak_multiplier"] for row in high_priority}, {2, 5})
        self.assertTrue(all(row["p95_latency_seconds"] <= S2PMT05_BACKPRESSURE_HIGH_PRIORITY_SLO_SECONDS for row in high_priority))
        self.assertEqual({row["reason_code"] for row in low_priority}, {"LOW_PRIORITY_DELAYED", "REBUILDABLE_CACHE_SHED"})

    def test_backpressure_policy_blocks_missing_reasons_and_high_priority_slo_breach(self) -> None:
        policy = evaluate_backpressure_policy(queue_depth=15000, capacity=10000)
        peak_profiles = [dict(row) for row in policy["peak_profiles"]]
        peak_profiles[0]["p95_latency_seconds"] = S2PMT05_BACKPRESSURE_HIGH_PRIORITY_SLO_SECONDS + 1
        for row in peak_profiles:
            if row["priority"] == "low":
                row["reason_code"] = ""

        evaluation = evaluate_backpressure_policy(queue_depth=15000, capacity=10000, peak_profiles=peak_profiles)

        self.assertEqual(evaluation["status"], "blocked")
        self.assertTrue(evaluation["checks"]["covers_2x_and_5x_peak_profiles"])
        self.assertFalse(evaluation["checks"]["high_priority_slo_met"])
        self.assertFalse(evaluation["checks"]["low_priority_delay_or_drop_has_reasons"])

    def test_backpressure_policy_blocks_missing_low_priority_peak_profile(self) -> None:
        policy = evaluate_backpressure_policy(queue_depth=15000, capacity=10000)
        peak_profiles = [
            dict(row)
            for row in policy["peak_profiles"]
            if not (row["priority"] == "low" and row["peak_multiplier"] == 5)
        ]

        evaluation = evaluate_backpressure_policy(queue_depth=15000, capacity=10000, peak_profiles=peak_profiles)

        self.assertEqual(evaluation["status"], "blocked")
        self.assertFalse(evaluation["checks"]["covers_2x_and_5x_peak_profiles"])

    def test_full_s2pmt05_report_validates_without_production_side_effects(self) -> None:
        report = build_s2pmt05_report(generated_at="2026-07-04T06:00:00+10:00")

        self.assertEqual(report["status"], "pass")
        self.assertFalse(report["production_acceptance_claimed"])
        self.assertFalse(report["inherited_p0_p1_closed"])
        self.assertEqual(set(report["findings_covered"]), set(S2PMT05_REQUIRED_FINDINGS))
        self.assertTrue(report["gates"]["capacity_baseline_model"])
        self.assertEqual(report["findings_covered"]["B-006"], ["capacity_baseline_model", "load_stress_spike_soak"])
        self.assertTrue(report["gates"]["fault_injection"])
        self.assertEqual(report["findings_covered"]["B-009"], ["fault_injection"])
        self.assertTrue(report["fault_injection"]["checks"]["corrupt_pdf_rebuilds_from_source"])
        self.assertTrue(report["fault_injection"]["checks"]["backup_faults_block_restore_or_publish"])
        self.assertTrue(report["gates"]["dst_clock_policy"])
        self.assertEqual(report["findings_covered"]["B-010"], ["dst_clock_policy"])
        self.assertTrue(report["dst_clock_policy"]["checks"]["misfire_within_grace_runs_once"])
        self.assertTrue(report["dst_clock_policy"]["checks"]["sleep_8h_catchup_bounded"])
        self.assertTrue(report["dst_clock_policy"]["checks"]["ntp_forward_over_tolerance_blocks"])
        self.assertTrue(report["gates"]["result_validity_semantic_evidence"])
        self.assertEqual(report["findings_covered"]["B-013"], ["result_validity_semantic_evidence"])
        self.assertTrue(report["backpressure_degradation"]["checks"]["covers_2x_and_5x_peak_profiles"])
        self.assertTrue(report["backpressure_degradation"]["checks"]["high_priority_slo_met"])
        self.assertTrue(report["backpressure_degradation"]["checks"]["low_priority_delay_or_drop_has_reasons"])
        for flag in S2PMT05_REQUIRED_PRODUCTION_FALSE_FLAGS:
            self.assertFalse(report[flag])
        self.assertEqual(validate_s2pmt05_report(report), [])

        tampered = dict(report)
        tampered["scheduler_enabled"] = True
        self.assertIn("scheduler_enabled must be false", validate_s2pmt05_report(tampered))


if __name__ == "__main__":
    unittest.main()
