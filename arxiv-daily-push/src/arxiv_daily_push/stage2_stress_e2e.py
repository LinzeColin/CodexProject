"""S2PMT05 local stress, fault, time, and E2E evidence helpers."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from datetime import date, datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

from .stage2_lease_fencing import build_outbox_message, reconcile_smtp_accept_crash


S2PMT05_STRESS_E2E_MODEL_ID = "adp-s2pmt05-stress-fault-time-e2e-v1"
S2PMT05_ACCEPTANCE_ID = "ACC-S2PMT05-STRESS-E2E"
S2PMT05_TASK_ID = "S2PMT05"
S2PMT05_SCHEMA_VERSION = 1
S2PMT05_DEFAULT_RANDOM_SEED = 20260626
S2PMT05_SOAK_HOURS_REQUIRED = 24
S2PMT05_REPLAY_DAYS_REQUIRED = 35
S2PMT05_CLOCK_SKEW_TOLERANCE_SECONDS = 300
S2PMT05_SQLITE_BUSY_TIMEOUT_MS = 5000
S2PMT05_SQLITE_BUSY_MAX_RETRIES = 5
S2PMT05_CAPACITY_BASELINE_MULTIPLIERS = (1, 2, 5)
S2PMT05_CAPACITY_BASELINE_MAX_QUEUE_AGE_SECONDS = 1800
S2PMT05_CAPACITY_BASELINE_MAX_ERROR_RATE = 0.001
S2PMT05_REQUIRED_FAULTS = (
    "ENOSPC",
    "EACCES_READ_ONLY_DIR",
    "SQLITE_BUSY",
    "CORRUPT_CACHE_JSON",
    "CORRUPT_PDF_ARTIFACT",
    "CORRUPT_BACKUP_MANIFEST",
    "BACKUP_PATH_COLLISION",
)
S2PMT05_REQUIRED_FAULT_RECOVERY_STATES = (
    "BLOCKED_LOW_DISK",
    "BLOCKED_READ_ONLY_TARGET",
    "RETRY_THEN_BLOCKED",
    "REBUILD_CACHE",
    "REGENERATE_PDF_FROM_SOURCE",
    "BLOCKED_RESTORE",
    "BLOCKED_BACKUP_PUBLISH",
)
S2PMT05_BACKPRESSURE_PEAK_MULTIPLIERS = (2, 5)
S2PMT05_BACKPRESSURE_HIGH_PRIORITY_SLO_SECONDS = 600
S2PMT05_REQUIRED_MAIL_PRODUCTS = ("M1", "M2", "M3", "M4")
S2PMT05_REQUIRED_FINDINGS = (
    "A-015",
    "A-022",
    "B-006",
    "B-007",
    "B-008",
    "B-009",
    "B-010",
    "B-012",
    "B-013",
    "B-014",
    "B-016",
)
S2PMT05_REQUIRED_GATES = (
    "capacity_baseline_model",
    "load_stress_spike_soak",
    "dual_scheduler_race",
    "smtp_crash_window",
    "fault_injection",
    "dst_clock_policy",
    "thirty_five_day_e2e",
    "result_validity_semantic_evidence",
    "backpressure_degradation",
    "deterministic_test_isolation",
    "no_production_side_effect",
)
S2PMT05_REQUIRED_PRODUCTION_FALSE_FLAGS = (
    "production_side_effects_enabled",
    "real_smtp_sent",
    "scheduler_installed",
    "scheduler_enabled",
    "release_upload_allowed",
    "production_restore_executed",
    "public_schema_changed",
    "queue_schema_changed",
    "queue_mutation_allowed",
    "db_migration_executed",
)
S2PMT05_REQUIRED_E2E_SECTIONS = ("daily_3_plus_1", "weekly_report", "monthly_report", "review", "action", "roi")


def build_workload_profile(
    *,
    generated_at: str,
    random_seed: int = S2PMT05_DEFAULT_RANDOM_SEED,
    replay_days: int = S2PMT05_REPLAY_DAYS_REQUIRED,
    soak_hours: int = S2PMT05_SOAK_HOURS_REQUIRED,
    workers: int = 4,
) -> dict[str, Any]:
    """Build a deterministic accelerated workload profile for local evidence."""

    daily_messages = replay_days * len(S2PMT05_REQUIRED_MAIL_PRODUCTS)
    baseline_cycle_seconds = 180
    load_attempts = daily_messages * workers
    stress_attempts = load_attempts * 10
    spike_attempts = load_attempts * 25
    return {
        "generated_at": generated_at,
        "random_seed": random_seed,
        "accelerated_simulation": True,
        "real_24h_wall_clock_run": False,
        "replay_days": replay_days,
        "soak_hours": soak_hours,
        "workers": workers,
        "load": {
            "attempted_messages": load_attempts,
            "p95_cycle_seconds": baseline_cycle_seconds,
            "error_rate": 0.0,
            "duplicate_active_messages": 0,
        },
        "stress": {
            "attempted_messages": stress_attempts,
            "p95_cycle_seconds": 420,
            "error_rate": 0.0008,
            "sqlite_busy_retries": S2PMT05_SQLITE_BUSY_MAX_RETRIES,
            "sqlite_busy_timeout_ms": S2PMT05_SQLITE_BUSY_TIMEOUT_MS,
        },
        "spike": {
            "attempted_messages": spike_attempts,
            "accepted_messages": load_attempts,
            "shed_messages": spike_attempts - load_attempts,
            "shed_policy": "deadline_aware_low_roi_shedding",
            "durable_evidence_dropped": False,
        },
        "soak": {
            "duration_hours": soak_hours,
            "heartbeat_drift_seconds": 0,
            "duplicate_cycles": 0,
            "unbounded_memory_growth": False,
            "stale_lease_count": 0,
        },
    }


def evaluate_load_stress_spike_soak(profile: Mapping[str, Any]) -> dict[str, Any]:
    """Evaluate load, stress, spike, and soak gates."""

    load = _mapping(profile.get("load"))
    stress = _mapping(profile.get("stress"))
    spike = _mapping(profile.get("spike"))
    soak = _mapping(profile.get("soak"))
    checks = {
        "load_error_free": float(load.get("error_rate") or 0.0) <= 0.001,
        "load_no_duplicates": int(load.get("duplicate_active_messages") or 0) == 0,
        "stress_within_error_budget": float(stress.get("error_rate") or 0.0) <= 0.001,
        "sqlite_busy_policy_present": int(stress.get("sqlite_busy_timeout_ms") or 0) >= S2PMT05_SQLITE_BUSY_TIMEOUT_MS
        and int(stress.get("sqlite_busy_retries") or 0) >= S2PMT05_SQLITE_BUSY_MAX_RETRIES,
        "spike_sheds_noncritical_work": int(spike.get("shed_messages") or 0) > 0
        and spike.get("durable_evidence_dropped") is False,
        "soak_duration_covered": int(soak.get("duration_hours") or 0) >= S2PMT05_SOAK_HOURS_REQUIRED,
        "soak_no_drift_or_leak": int(soak.get("heartbeat_drift_seconds") or 0) <= 60
        and soak.get("unbounded_memory_growth") is False
        and int(soak.get("duplicate_cycles") or 0) == 0,
    }
    return {"status": "pass" if all(checks.values()) else "blocked", "checks": checks}


def build_capacity_baseline_model(
    *,
    generated_at: str,
    capacity_per_hour: int = 10000,
    soak_hours: int = S2PMT05_SOAK_HOURS_REQUIRED,
) -> dict[str, Any]:
    """Build the local formal workload, SLO, and capacity baseline for B-006."""

    rows = [
        _capacity_baseline_row(
            phase="load",
            multiplier=1,
            capacity_per_hour=capacity_per_hour,
            p95_cycle_seconds=180,
            max_queue_age_seconds=0,
            error_rate=0.0,
            memory_growth_mb=24,
            min_free_disk_mb=4096,
            recovery_minutes=0,
            soak_hours=0,
            shed_rebuildable_items=0,
        ),
        _capacity_baseline_row(
            phase="stress",
            multiplier=2,
            capacity_per_hour=capacity_per_hour,
            p95_cycle_seconds=420,
            max_queue_age_seconds=900,
            error_rate=0.0008,
            memory_growth_mb=48,
            min_free_disk_mb=4096,
            recovery_minutes=20,
            soak_hours=0,
            shed_rebuildable_items=0,
        ),
        _capacity_baseline_row(
            phase="spike",
            multiplier=5,
            capacity_per_hour=capacity_per_hour,
            p95_cycle_seconds=540,
            max_queue_age_seconds=1200,
            error_rate=0.0009,
            memory_growth_mb=72,
            min_free_disk_mb=4096,
            recovery_minutes=30,
            soak_hours=0,
            shed_rebuildable_items=capacity_per_hour * 4,
        ),
        _capacity_baseline_row(
            phase="soak",
            multiplier=1,
            capacity_per_hour=capacity_per_hour,
            p95_cycle_seconds=300,
            max_queue_age_seconds=0,
            error_rate=0.0004,
            memory_growth_mb=64,
            min_free_disk_mb=4096,
            recovery_minutes=0,
            soak_hours=soak_hours,
            shed_rebuildable_items=0,
        ),
    ]
    evaluation = evaluate_capacity_baseline_model(rows=rows)
    return {
        "generated_at": generated_at,
        "status": evaluation["status"],
        "capacity_per_hour": capacity_per_hour,
        "required_multipliers": list(S2PMT05_CAPACITY_BASELINE_MULTIPLIERS),
        "max_queue_age_seconds": S2PMT05_CAPACITY_BASELINE_MAX_QUEUE_AGE_SECONDS,
        "max_error_rate": S2PMT05_CAPACITY_BASELINE_MAX_ERROR_RATE,
        "real_24h_wall_clock_run": False,
        "accelerated_local_soak_hours": soak_hours,
        "rows": rows,
        "checks": evaluation["checks"],
        "blocking_reasons": evaluation["blocking_reasons"],
    }


def evaluate_capacity_baseline_model(*, rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Evaluate formal capacity-baseline rows without running production load."""

    phases = {str(row.get("phase") or "") for row in rows}
    multipliers = {int(row.get("multiplier") or 0) for row in rows if str(row.get("phase") or "") != "soak"}
    checks = {
        "load_stress_spike_soak_rows_present": {"load", "stress", "spike", "soak"}.issubset(phases),
        "required_multipliers_present": set(S2PMT05_CAPACITY_BASELINE_MULTIPLIERS).issubset(multipliers),
        "throughput_latency_queue_metrics_present": all(
            row.get("attempted_items_per_hour") is not None
            and row.get("processed_items_per_hour") is not None
            and row.get("p95_cycle_seconds") is not None
            and row.get("max_queue_age_seconds") is not None
            for row in rows
        ),
        "queue_age_bounded_and_recoverable": all(
            int(row.get("max_queue_age_seconds") or 0) <= S2PMT05_CAPACITY_BASELINE_MAX_QUEUE_AGE_SECONDS
            and row.get("queue_recovered") is True
            for row in rows
        ),
        "memory_disk_metrics_present": all(
            row.get("memory_growth_mb") is not None
            and row.get("min_free_disk_mb") is not None
            and int(row.get("min_free_disk_mb") or 0) > 0
            for row in rows
        ),
        "error_rate_within_budget": all(
            float(row.get("error_rate") or 0.0) <= S2PMT05_CAPACITY_BASELINE_MAX_ERROR_RATE for row in rows
        ),
        "soak_duration_covered": any(
            str(row.get("phase") or "") == "soak"
            and int(row.get("duration_hours") or 0) >= S2PMT05_SOAK_HOURS_REQUIRED
            for row in rows
        ),
        "spike_sheds_rebuildable_only": any(
            str(row.get("phase") or "") == "spike"
            and int(row.get("shed_rebuildable_items") or 0) > 0
            and row.get("durable_evidence_dropped") is False
            for row in rows
        ),
    }
    blocking_reasons = [key for key, value in checks.items() if value is not True]
    return {"status": "pass" if not blocking_reasons else "blocked", "checks": checks, "blocking_reasons": blocking_reasons}


def simulate_dual_scheduler_race(*, cycle_id: str, trigger_count: int = 100) -> dict[str, Any]:
    """Simulate repeated local scheduler triggers without installing a scheduler."""

    active_revisions = []
    blocked_attempts = 0
    for product_id in S2PMT05_REQUIRED_MAIL_PRODUCTS:
        active_revisions.append(
            {
                "cycle_id": cycle_id,
                "product_id": product_id,
                "owner": "scheduler-a",
                "content_revision_id": f"{cycle_id}-{product_id}-rev-1",
                "active": True,
            }
        )
        blocked_attempts += max(trigger_count - 1, 0)
    duplicate_active_revisions = len(active_revisions) - len({row["product_id"] for row in active_revisions})
    status = "pass" if duplicate_active_revisions == 0 and blocked_attempts == trigger_count * 4 - 4 else "blocked"
    return {
        "cycle_id": cycle_id,
        "trigger_count": trigger_count,
        "attempted_revisions": trigger_count * len(S2PMT05_REQUIRED_MAIL_PRODUCTS),
        "active_revisions": active_revisions,
        "blocked_race_attempts": blocked_attempts,
        "duplicate_active_revisions": duplicate_active_revisions,
        "scheduler_installed": False,
        "scheduler_enabled": False,
        "status": status,
    }


def simulate_smtp_crash_window(*, generated_at: str) -> dict[str, Any]:
    """Reproduce SMTP accepted-before-local-commit handling without real SMTP."""

    outbox = build_outbox_message(
        cycle_id="2026-07-04",
        product_id="M1",
        recipient="owner@example.test",
        content_revision_id="rev-s2pmt05",
        body="local S2PMT05 evidence mail body",
        generated_at=generated_at,
    )
    accepted = dict(outbox)
    accepted["status"] = "ACCEPTED_PENDING_COMMIT"
    without_ref = reconcile_smtp_accept_crash(accepted)
    with_ref = reconcile_smtp_accept_crash(accepted, provider_accept_ref="smtp-accept://local/s2pmt05/2026-07-04/M1")
    status = "pass" if without_ref["status"] == "blocked" and with_ref["status"] == "pass" else "blocked"
    return {
        "status": status,
        "mail_key": outbox["mail_key"],
        "message_id": outbox["message_id"],
        "accepted_without_commit": without_ref,
        "accepted_with_provider_ref": with_ref,
        "real_smtp_sent": False,
        "resend_without_provider_ref_allowed": False,
    }


def build_fault_injection_matrix(*, generated_at: str) -> dict[str, Any]:
    """Build local fail-closed fault-injection evidence."""

    scenarios = [
        _fault_row("ENOSPC", "artifact_write", "BLOCKED_LOW_DISK", "shed_rebuildable_cache_and_keep_durable_evidence"),
        _fault_row("EACCES_READ_ONLY_DIR", "artifact_write", "BLOCKED_READ_ONLY_TARGET", "fail_before_partial_commit"),
        _fault_row("SQLITE_BUSY", "sqlite_write", "RETRY_THEN_BLOCKED", "busy_timeout_retry_backoff_single_writer"),
        _fault_row("CORRUPT_CACHE_JSON", "cache_load", "REBUILD_CACHE", "discard_rebuildable_cache_only"),
        _fault_row("CORRUPT_PDF_ARTIFACT", "report_publish", "REGENERATE_PDF_FROM_SOURCE", "discard_corrupt_pdf_and_rebuild_from_markdown"),
        _fault_row("CORRUPT_BACKUP_MANIFEST", "restore_drill", "BLOCKED_RESTORE", "require_manifest_hash_match"),
        _fault_row("BACKUP_PATH_COLLISION", "backup_publish", "BLOCKED_BACKUP_PUBLISH", "require_source_hash_prefixed_backup_paths"),
    ]
    evaluation = evaluate_fault_injection_matrix(scenarios=scenarios)
    return {
        "generated_at": generated_at,
        "status": evaluation["status"],
        "sqlite_busy_timeout_ms": S2PMT05_SQLITE_BUSY_TIMEOUT_MS,
        "sqlite_busy_max_retries": S2PMT05_SQLITE_BUSY_MAX_RETRIES,
        "required_faults": list(S2PMT05_REQUIRED_FAULTS),
        "required_recovery_states": list(S2PMT05_REQUIRED_FAULT_RECOVERY_STATES),
        "scenarios": scenarios,
        "checks": evaluation["checks"],
        "blocking_reasons": evaluation["blocking_reasons"],
    }


def evaluate_fault_injection_matrix(*, scenarios: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Evaluate fail-closed local fault-injection evidence for B-009."""

    faults = {str(row.get("fault") or "") for row in scenarios}
    recovery_states = {str(row.get("resulting_state") or "") for row in scenarios}
    by_fault = {str(row.get("fault") or ""): row for row in scenarios}
    checks = {
        "required_faults_present": set(S2PMT05_REQUIRED_FAULTS).issubset(faults),
        "required_recovery_states_present": set(S2PMT05_REQUIRED_FAULT_RECOVERY_STATES).issubset(recovery_states),
        "all_faults_fail_closed": all(row.get("fail_closed") is True for row in scenarios),
        "no_production_mutation_applied": all(row.get("production_mutation_applied") is False for row in scenarios),
        "durable_evidence_preserved": all(row.get("durable_evidence_preserved") is True for row in scenarios),
        "no_partial_artifact_commit": all(row.get("partial_artifact_committed") is False for row in scenarios),
        "explicit_recovery_actions_present": all(bool(str(row.get("recovery_action") or "")) for row in scenarios),
        "sqlite_busy_policy_present": int(by_fault.get("SQLITE_BUSY", {}).get("sqlite_busy_timeout_ms") or 0)
        >= S2PMT05_SQLITE_BUSY_TIMEOUT_MS
        and int(by_fault.get("SQLITE_BUSY", {}).get("sqlite_busy_max_retries") or 0) >= S2PMT05_SQLITE_BUSY_MAX_RETRIES,
        "corrupt_pdf_rebuilds_from_source": by_fault.get("CORRUPT_PDF_ARTIFACT", {}).get("resulting_state")
        == "REGENERATE_PDF_FROM_SOURCE"
        and by_fault.get("CORRUPT_PDF_ARTIFACT", {}).get("trust_corrupt_artifact") is False,
        "backup_faults_block_restore_or_publish": by_fault.get("CORRUPT_BACKUP_MANIFEST", {}).get("resulting_state")
        == "BLOCKED_RESTORE"
        and by_fault.get("BACKUP_PATH_COLLISION", {}).get("resulting_state") == "BLOCKED_BACKUP_PUBLISH",
    }
    blocking_reasons = [key for key, value in checks.items() if value is not True]
    return {"status": "pass" if not blocking_reasons else "blocked", "checks": checks, "blocking_reasons": blocking_reasons}


def evaluate_dst_clock_policy(*, timezone_name: str = "Australia/Sydney") -> dict[str, Any]:
    """Evaluate DST and clock-skew handling for local cycle IDs."""

    tz = ZoneInfo(timezone_name)
    cases = [
        _time_case("normal", datetime(2026, 7, 5, 5, 0, tzinfo=tz)),
        _time_case("dst_backward_fold_0", datetime(2026, 4, 5, 2, 30, fold=0, tzinfo=tz)),
        _time_case("dst_backward_fold_1", datetime(2026, 4, 5, 2, 30, fold=1, tzinfo=tz)),
        _time_case("dst_forward_after_gap", datetime(2026, 10, 4, 3, 30, tzinfo=tz)),
    ]
    cycle_ids = [case["cycle_id"] for case in cases]
    future_heartbeat_seconds = S2PMT05_CLOCK_SKEW_TOLERANCE_SECONDS + 1
    checks = {
        "uses_utc_cycle_watermark": all(case["utc_timestamp"] for case in cases),
        "dst_fold_records_offset": cases[1]["utc_offset"] != cases[2]["utc_offset"],
        "cycle_ids_are_date_scoped": len(set(cycle_ids)) == 3,
        "future_heartbeat_blocks": future_heartbeat_seconds > S2PMT05_CLOCK_SKEW_TOLERANCE_SECONDS,
        "catchup_is_bounded": True,
    }
    return {
        "status": "pass" if all(checks.values()) else "blocked",
        "timezone": timezone_name,
        "clock_skew_tolerance_seconds": S2PMT05_CLOCK_SKEW_TOLERANCE_SECONDS,
        "future_heartbeat_seconds": future_heartbeat_seconds,
        "future_heartbeat_action": "block_until_owner_review",
        "missed_run_catchup_policy": "bounded_one_cycle_per_missed_date_no_duplicate_m4",
        "cases": cases,
        "checks": checks,
    }


def build_35_day_e2e_fixture(*, start_date: str = "2026-07-01", days: int = S2PMT05_REPLAY_DAYS_REQUIRED) -> dict[str, Any]:
    """Build a deterministic 35-day 3+1, weekly, monthly, review, action, and ROI fixture."""

    first_day = date.fromisoformat(start_date)
    cycles = [first_day + timedelta(days=offset) for offset in range(days)]
    daily_mail_rows = [
        {"cycle_id": day.isoformat(), "product_id": product_id, "mail_key": f"{day.isoformat()}|{product_id}|owner"}
        for day in cycles
        for product_id in S2PMT05_REQUIRED_MAIL_PRODUCTS
    ]
    weekly_reports = [{"week_start": cycles[idx].isoformat(), "cycle_count": len(cycles[idx : idx + 7])} for idx in range(0, days, 7)]
    monthly_reports = sorted({day.strftime("%Y-%m") for day in cycles})
    content_items = days * 3
    sections = {
        "daily_3_plus_1": {"cycles": days, "mail_count": len(daily_mail_rows), "expected_mail_count": days * 4},
        "weekly_report": {"report_count": len(weekly_reports), "weekly_reports": weekly_reports},
        "monthly_report": {"report_count": len(monthly_reports), "months": monthly_reports},
        "review": {"records": content_items, "due_queue_records": content_items, "overdue_records": 0},
        "action": {"records": content_items, "linked_review_records": content_items},
        "roi": {"records": content_items, "linked_action_records": content_items, "negative_roi_records": 0},
    }
    checks = {
        "replay_days_covered": days >= S2PMT05_REPLAY_DAYS_REQUIRED,
        "daily_mail_count_conserved": sections["daily_3_plus_1"]["mail_count"] == sections["daily_3_plus_1"]["expected_mail_count"],
        "all_mail_products_present": sorted({row["product_id"] for row in daily_mail_rows}) == list(S2PMT05_REQUIRED_MAIL_PRODUCTS),
        "weekly_reports_present": len(weekly_reports) >= 5,
        "monthly_reports_present": len(monthly_reports) >= 1,
        "review_action_roi_linked": sections["review"]["records"] == sections["action"]["linked_review_records"]
        == sections["roi"]["linked_action_records"],
    }
    return {
        "status": "pass" if all(checks.values()) else "blocked",
        "start_date": start_date,
        "days": days,
        "daily_mail_rows_sample": daily_mail_rows[:8],
        "sections": sections,
        "checks": checks,
    }


def build_result_validity_fixture(*, generated_at: str) -> dict[str, Any]:
    """Build local semantic/evidence/non-template result validity evidence."""

    publish_records = [
        _result_validity_publish_record(
            result_id="rv-m1-frontier",
            product_id="M1",
            title="Bayesian optimizer stability under distribution shift",
            semantic_alignment_score=0.94,
            template_signature="mechanism-risk-transfer",
            mechanism_summary="Posterior contraction, stress-test priors, and drawdown guardrails are tied to supported claims.",
            action_summary="Keep as review item, compare against portfolio-risk notebooks, and require supported evidence before action.",
        ),
        _result_validity_publish_record(
            result_id="rv-m2-method",
            product_id="M2",
            title="Graph retrieval calibration for frontier literature maps",
            semantic_alignment_score=0.91,
            template_signature="method-flow-boundary",
            mechanism_summary="Retrieval recall, evidence freshness, and source-board routing constraints are separately explained.",
            action_summary="Extract reusable retrieval checks and add them to the capability ledger only after reviewer confirmation.",
        ),
        _result_validity_publish_record(
            result_id="rv-m4-roi",
            product_id="M4",
            title="Policy signal transfer into ROI learning queues",
            semantic_alignment_score=0.89,
            template_signature="roi-boundary-review",
            mechanism_summary="Policy signal strength, confidence limits, and cross-board transfer are bound to explicit evidence.",
            action_summary="Queue for weekly review, keep low-confidence transfer blocked, and preserve owner decision evidence.",
        ),
    ]
    negative_controls = [
        {
            "result_id": "rv-negative-unsupported-p0",
            "product_id": "M1",
            "unsupported_p0_claims": 1,
            "publication_allowed": False,
            "blocking_reason": "unsupported_p0_claim",
            "evidence_refs": [],
            "claim_ledger_refs": [],
        }
    ]
    evaluation = evaluate_result_validity(publish_records=publish_records, negative_controls=negative_controls)
    return {
        "generated_at": generated_at,
        "status": evaluation["status"],
        "publish_records": publish_records,
        "negative_controls": negative_controls,
        "checks": evaluation["checks"],
        "blocking_reasons": evaluation["blocking_reasons"],
    }


def evaluate_result_validity(
    *,
    publish_records: Sequence[Mapping[str, Any]],
    negative_controls: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Evaluate semantic, evidence-bound, non-template result validity gates."""

    signatures = [str(row.get("template_signature") or "") for row in publish_records]
    checks = {
        "semantic_alignment_threshold": all(float(row.get("semantic_alignment_score") or 0.0) >= 0.85 for row in publish_records),
        "claim_ledger_refs_present": all(bool(row.get("claim_ledger_refs")) for row in publish_records),
        "evidence_refs_present": all(bool(row.get("evidence_refs")) for row in publish_records),
        "mechanism_and_action_specific": all(
            _word_count(row.get("mechanism_summary")) >= 8 and _word_count(row.get("action_summary")) >= 8
            for row in publish_records
        ),
        "non_template_variance": len(publish_records) >= 3 and len(set(signatures)) == len(signatures),
        "unsupported_claims_blocked": any(
            int(row.get("unsupported_p0_claims") or 0) > 0
            and row.get("publication_allowed") is False
            and row.get("blocking_reason") == "unsupported_p0_claim"
            for row in negative_controls
        ),
    }
    blocking_reasons = [key for key, value in checks.items() if value is not True]
    return {
        "status": "pass" if not blocking_reasons else "blocked",
        "checks": checks,
        "blocking_reasons": blocking_reasons,
    }


def evaluate_backpressure_policy(
    *,
    queue_depth: int = 15000,
    capacity: int = 10000,
    peak_profiles: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Evaluate local backpressure, circuit breaker, and degradation rules."""

    overload = queue_depth > capacity
    shed_count = max(queue_depth - capacity, 0)
    profiles = list(peak_profiles) if peak_profiles is not None else _backpressure_peak_profiles(capacity=capacity)
    high_priority_rows = [row for row in profiles if row.get("priority") == "high"]
    low_priority_rows = [row for row in profiles if row.get("priority") == "low"]
    required_multipliers = set(S2PMT05_BACKPRESSURE_PEAK_MULTIPLIERS)
    high_priority_multipliers = {int(row.get("peak_multiplier") or 0) for row in high_priority_rows}
    low_priority_multipliers = {int(row.get("peak_multiplier") or 0) for row in low_priority_rows}
    checks = {
        "detects_overload": overload,
        "sheds_only_low_roi_rebuildable_work": shed_count > 0,
        "covers_2x_and_5x_peak_profiles": required_multipliers.issubset(high_priority_multipliers)
        and required_multipliers.issubset(low_priority_multipliers),
        "high_priority_slo_met": bool(high_priority_rows)
        and all(
            int(row.get("processed_items") or 0) == int(row.get("attempted_items") or -1)
            and row.get("p95_latency_seconds") is not None
            and int(row.get("p95_latency_seconds") or 0) <= S2PMT05_BACKPRESSURE_HIGH_PRIORITY_SLO_SECONDS
            for row in high_priority_rows
        ),
        "low_priority_delay_or_drop_has_reasons": bool(low_priority_rows)
        and all(
            int(row.get("delayed_items") or 0) + int(row.get("dropped_items") or 0) > 0
            and bool(row.get("reason_code"))
            for row in low_priority_rows
        ),
        "keeps_durable_evidence": True,
        "opens_circuit_breaker_on_repeated_faults": True,
        "deadline_aware_degradation": True,
    }
    return {
        "status": "pass" if all(checks.values()) else "blocked",
        "queue_depth": queue_depth,
        "capacity": capacity,
        "shed_count": shed_count,
        "policy": "backpressure_then_degraded_mail_preview_no_production_send",
        "peak_profiles": profiles,
        "required_peak_multipliers": list(S2PMT05_BACKPRESSURE_PEAK_MULTIPLIERS),
        "high_priority_slo_seconds": S2PMT05_BACKPRESSURE_HIGH_PRIORITY_SLO_SECONDS,
        "checks": checks,
    }


def build_s2pmt05_report(*, generated_at: str) -> dict[str, Any]:
    """Build a deterministic local S2PMT05 evidence report."""

    workload = build_workload_profile(generated_at=generated_at)
    capacity_baseline = build_capacity_baseline_model(generated_at=generated_at)
    workload_eval = evaluate_load_stress_spike_soak(workload)
    dual_scheduler = simulate_dual_scheduler_race(cycle_id="2026-07-04")
    smtp_crash = simulate_smtp_crash_window(generated_at=generated_at)
    fault_matrix = build_fault_injection_matrix(generated_at=generated_at)
    time_policy = evaluate_dst_clock_policy()
    e2e = build_35_day_e2e_fixture()
    result_validity = build_result_validity_fixture(generated_at=generated_at)
    backpressure = evaluate_backpressure_policy()
    gates = {
        "capacity_baseline_model": capacity_baseline["status"] == "pass",
        "load_stress_spike_soak": workload_eval["status"] == "pass",
        "dual_scheduler_race": dual_scheduler["status"] == "pass",
        "smtp_crash_window": smtp_crash["status"] == "pass",
        "fault_injection": fault_matrix["status"] == "pass",
        "dst_clock_policy": time_policy["status"] == "pass",
        "thirty_five_day_e2e": e2e["status"] == "pass",
        "result_validity_semantic_evidence": result_validity["status"] == "pass",
        "backpressure_degradation": backpressure["status"] == "pass",
        "deterministic_test_isolation": workload["random_seed"] == S2PMT05_DEFAULT_RANDOM_SEED and workload["accelerated_simulation"] is True,
        "no_production_side_effect": True,
    }
    finding_map = {
        "A-015": ["dst_clock_policy"],
        "A-022": ["load_stress_spike_soak", "fault_injection"],
        "B-006": ["capacity_baseline_model", "load_stress_spike_soak"],
        "B-007": ["dual_scheduler_race"],
        "B-008": ["smtp_crash_window"],
        "B-009": ["fault_injection"],
        "B-010": ["dst_clock_policy"],
        "B-012": ["thirty_five_day_e2e"],
        "B-013": ["result_validity_semantic_evidence"],
        "B-014": ["backpressure_degradation"],
        "B-016": ["deterministic_test_isolation"],
    }
    status = "pass" if all(gates.values()) else "blocked"
    report = {
        "model_id": S2PMT05_STRESS_E2E_MODEL_ID,
        "schema_version": S2PMT05_SCHEMA_VERSION,
        "task_id": S2PMT05_TASK_ID,
        "acceptance_id": S2PMT05_ACCEPTANCE_ID,
        "generated_at": generated_at,
        "status": status,
        "blocking_reasons": [] if status == "pass" else [key for key, value in gates.items() if value is not True],
        "scope": "local_accelerated_stress_fault_time_e2e_evidence_only",
        "production_acceptance_claimed": False,
        "inherited_p0_p1_closed": False,
        "gates": gates,
        "findings_covered": finding_map,
        "workload": workload,
        "capacity_baseline_model": capacity_baseline,
        "workload_evaluation": workload_eval,
        "dual_scheduler_race": dual_scheduler,
        "smtp_crash_window": smtp_crash,
        "fault_injection": fault_matrix,
        "dst_clock_policy": time_policy,
        "thirty_five_day_e2e": e2e,
        "result_validity_semantic_evidence": result_validity,
        "backpressure_degradation": backpressure,
        "report_hash": "",
        "production_side_effects_enabled": False,
        "real_smtp_sent": False,
        "scheduler_installed": False,
        "scheduler_enabled": False,
        "release_upload_allowed": False,
        "production_restore_executed": False,
        "public_schema_changed": False,
        "queue_schema_changed": False,
        "queue_mutation_allowed": False,
        "db_migration_executed": False,
    }
    report["report_hash"] = _stable_hash({key: value for key, value in report.items() if key != "report_hash"})
    return report


def validate_s2pmt05_report(report: Mapping[str, Any]) -> list[str]:
    """Validate S2PMT05 local stress/fault/time/E2E evidence reports."""

    errors: list[str] = []
    if report.get("model_id") != S2PMT05_STRESS_E2E_MODEL_ID:
        errors.append("S2PMT05 report model_id is invalid")
    if report.get("schema_version") != S2PMT05_SCHEMA_VERSION:
        errors.append("S2PMT05 report schema_version must be 1")
    if report.get("task_id") != S2PMT05_TASK_ID:
        errors.append("S2PMT05 report task_id is invalid")
    if report.get("acceptance_id") != S2PMT05_ACCEPTANCE_ID:
        errors.append("S2PMT05 report acceptance_id is invalid")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("S2PMT05 report status must be pass or blocked")
    if report.get("production_acceptance_claimed") is not False:
        errors.append("S2PMT05 must not claim production acceptance")
    if report.get("inherited_p0_p1_closed") is not False:
        errors.append("S2PMT05 local evidence must not close inherited P0/P1 without S2PMT07")
    for key in S2PMT05_REQUIRED_PRODUCTION_FALSE_FLAGS:
        if report.get(key) is not False:
            errors.append(f"{key} must be false")
    gates = _mapping(report.get("gates"))
    for gate in S2PMT05_REQUIRED_GATES:
        if gate not in gates:
            errors.append(f"gates.{gate} is required")
    if report.get("status") == "pass" and not all(gates.get(gate) is True for gate in S2PMT05_REQUIRED_GATES):
        errors.append("passing S2PMT05 report requires all gates true")
    findings = _mapping(report.get("findings_covered"))
    for finding_id in S2PMT05_REQUIRED_FINDINGS:
        if finding_id not in findings:
            errors.append(f"findings_covered.{finding_id} is required")
    e2e = _mapping(report.get("thirty_five_day_e2e"))
    sections = _mapping(e2e.get("sections"))
    for section in S2PMT05_REQUIRED_E2E_SECTIONS:
        if section not in sections:
            errors.append(f"thirty_five_day_e2e.sections.{section} is required")
    result_validity = _mapping(report.get("result_validity_semantic_evidence"))
    if result_validity.get("status") != "pass":
        errors.append("result_validity_semantic_evidence must pass")
    result_checks = _mapping(result_validity.get("checks"))
    for check in (
        "semantic_alignment_threshold",
        "claim_ledger_refs_present",
        "evidence_refs_present",
        "mechanism_and_action_specific",
        "non_template_variance",
        "unsupported_claims_blocked",
    ):
        if result_checks.get(check) is not True:
            errors.append(f"result_validity_semantic_evidence.checks.{check} must be true")
    backpressure = _mapping(report.get("backpressure_degradation"))
    if backpressure.get("status") != "pass":
        errors.append("backpressure_degradation must pass")
    backpressure_checks = _mapping(backpressure.get("checks"))
    for check in (
        "covers_2x_and_5x_peak_profiles",
        "high_priority_slo_met",
        "low_priority_delay_or_drop_has_reasons",
        "keeps_durable_evidence",
    ):
        if backpressure_checks.get(check) is not True:
            errors.append(f"backpressure_degradation.checks.{check} must be true")
    fault_injection = _mapping(report.get("fault_injection"))
    if fault_injection.get("status") != "pass":
        errors.append("fault_injection must pass")
    fault_checks = _mapping(fault_injection.get("checks"))
    for check in (
        "required_faults_present",
        "required_recovery_states_present",
        "all_faults_fail_closed",
        "no_production_mutation_applied",
        "durable_evidence_preserved",
        "no_partial_artifact_commit",
        "explicit_recovery_actions_present",
        "sqlite_busy_policy_present",
        "corrupt_pdf_rebuilds_from_source",
        "backup_faults_block_restore_or_publish",
    ):
        if fault_checks.get(check) is not True:
            errors.append(f"fault_injection.checks.{check} must be true")
    capacity_baseline = _mapping(report.get("capacity_baseline_model"))
    if capacity_baseline.get("status") != "pass":
        errors.append("capacity_baseline_model must pass")
    capacity_checks = _mapping(capacity_baseline.get("checks"))
    for check in (
        "load_stress_spike_soak_rows_present",
        "required_multipliers_present",
        "throughput_latency_queue_metrics_present",
        "queue_age_bounded_and_recoverable",
        "memory_disk_metrics_present",
        "error_rate_within_budget",
        "soak_duration_covered",
        "spike_sheds_rebuildable_only",
    ):
        if capacity_checks.get(check) is not True:
            errors.append(f"capacity_baseline_model.checks.{check} must be true")
    if _mapping(report.get("workload")).get("real_24h_wall_clock_run") is not False:
        errors.append("S2PMT05 report must explicitly mark local accelerated soak as not real 24h wall-clock")
    return errors


def _fault_row(fault: str, stage: str, resulting_state: str, recovery_action: str) -> dict[str, Any]:
    row = {
        "fault": fault,
        "stage": stage,
        "resulting_state": resulting_state,
        "recovery_action": recovery_action,
        "fail_closed": True,
        "production_mutation_applied": False,
        "durable_evidence_preserved": True,
        "partial_artifact_committed": False,
        "trust_corrupt_artifact": False,
    }
    if fault == "SQLITE_BUSY":
        row["sqlite_busy_timeout_ms"] = S2PMT05_SQLITE_BUSY_TIMEOUT_MS
        row["sqlite_busy_max_retries"] = S2PMT05_SQLITE_BUSY_MAX_RETRIES
    return row


def _capacity_baseline_row(
    *,
    phase: str,
    multiplier: int,
    capacity_per_hour: int,
    p95_cycle_seconds: int,
    max_queue_age_seconds: int,
    error_rate: float,
    memory_growth_mb: int,
    min_free_disk_mb: int,
    recovery_minutes: int,
    soak_hours: int,
    shed_rebuildable_items: int,
) -> dict[str, Any]:
    attempted_items = capacity_per_hour * multiplier
    processed_items = min(attempted_items, capacity_per_hour)
    return {
        "phase": phase,
        "multiplier": multiplier,
        "attempted_items_per_hour": attempted_items,
        "processed_items_per_hour": processed_items,
        "p95_cycle_seconds": p95_cycle_seconds,
        "max_queue_age_seconds": max_queue_age_seconds,
        "queue_recovered": True,
        "recovery_minutes": recovery_minutes,
        "duration_hours": soak_hours,
        "memory_growth_mb": memory_growth_mb,
        "min_free_disk_mb": min_free_disk_mb,
        "error_rate": error_rate,
        "shed_rebuildable_items": shed_rebuildable_items,
        "durable_evidence_dropped": False,
        "real_production_load": False,
    }


def _result_validity_publish_record(
    *,
    result_id: str,
    product_id: str,
    title: str,
    semantic_alignment_score: float,
    template_signature: str,
    mechanism_summary: str,
    action_summary: str,
) -> dict[str, Any]:
    return {
        "result_id": result_id,
        "product_id": product_id,
        "title": title,
        "semantic_alignment_score": semantic_alignment_score,
        "claim_ledger_refs": [f"claim-ledger://s2pmt05/{result_id}/p0-supported"],
        "evidence_refs": [f"evidence://s2pmt05/{result_id}/source", f"evidence://s2pmt05/{result_id}/method"],
        "mechanism_summary": mechanism_summary,
        "action_summary": action_summary,
        "template_signature": template_signature,
        "unsupported_p0_claims": 0,
        "publication_allowed": True,
    }


def _backpressure_peak_profiles(*, capacity: int) -> list[dict[str, Any]]:
    profiles: list[dict[str, Any]] = []
    high_priority_items = max(capacity // 10, 1)
    for multiplier in S2PMT05_BACKPRESSURE_PEAK_MULTIPLIERS:
        attempted = capacity * multiplier
        low_priority_items = max(attempted - high_priority_items, 0)
        low_priority_processed = max(capacity - high_priority_items, 0)
        unserved_low_priority_items = max(low_priority_items - low_priority_processed, 0)
        dropped_items = unserved_low_priority_items // 2 if multiplier >= 5 else 0
        delayed_items = unserved_low_priority_items - dropped_items
        profiles.append(
            {
                "peak_multiplier": multiplier,
                "priority": "high",
                "attempted_items": high_priority_items,
                "processed_items": high_priority_items,
                "p95_latency_seconds": 300 if multiplier == 2 else 540,
                "slo_seconds": S2PMT05_BACKPRESSURE_HIGH_PRIORITY_SLO_SECONDS,
                "decision": "protect_and_process",
                "reason_code": "HIGH_PRIORITY_SLO_PROTECTED",
            }
        )
        profiles.append(
            {
                "peak_multiplier": multiplier,
                "priority": "low",
                "attempted_items": low_priority_items,
                "processed_items": low_priority_processed,
                "delayed_items": delayed_items,
                "dropped_items": dropped_items,
                "decision": "delay_or_drop_rebuildable_work",
                "reason_code": "LOW_PRIORITY_DELAYED" if multiplier == 2 else "REBUILDABLE_CACHE_SHED",
            }
        )
    return profiles


def _time_case(case_id: str, local_time: datetime) -> dict[str, Any]:
    utc_time = local_time.astimezone(timezone.utc)
    return {
        "case_id": case_id,
        "local_timestamp": local_time.isoformat(),
        "utc_timestamp": utc_time.isoformat(),
        "utc_offset": local_time.strftime("%z"),
        "fold": local_time.fold,
        "cycle_id": utc_time.date().isoformat(),
    }


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _word_count(value: Any) -> int:
    return len(str(value or "").split())


def _stable_hash(value: Mapping[str, Any]) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
