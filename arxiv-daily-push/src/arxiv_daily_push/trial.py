"""Phase 11 operational trial evidence validator."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date
from typing import Any

from .config import DEFAULT_RECIPIENT, DEFAULT_TIMEZONE


TRIAL_EVIDENCE_VALIDATOR_ID = "adp-trial-evidence-v1"
TRIAL_DAYS_REQUIRED = 30
TARGET_LOCAL_TIME = "05:00"
HEALTH_CHECK_TIME = "04:45"
PASSING_RUN_STATUSES = {"succeeded", "degraded"}


def evaluate_trial_evidence(evidence: Mapping[str, Any], *, generated_at: str) -> dict[str, Any]:
    """Evaluate 30 unique-date operational evidence coverage without side effects."""

    trial_id = str(evidence.get("trial_id") or "trial:unknown")
    period = evidence.get("period") if isinstance(evidence.get("period"), Mapping) else {}
    expected_days = _positive_int(period.get("expected_days"), TRIAL_DAYS_REQUIRED)
    daily = _evaluate_daily_runs(evidence.get("daily_runs"), expected_days=expected_days)

    weekly_monthly = _evaluate_weekly_monthly(evidence.get("weekly_monthly"))
    recovery = _evaluate_recovery(evidence.get("recovery"))
    scheduler = _evaluate_scheduler(evidence.get("scheduler"), daily_passed=daily["passed"])
    text_artifacts = _evaluate_text_artifacts(evidence.get("text_artifacts"), daily_runs=daily["valid_runs"])
    email = _evaluate_email(evidence.get("email"), daily_runs=daily["valid_runs"])
    resource = _evaluate_resource(evidence.get("resource_pressure"), daily_runs=daily["valid_runs"])

    thirty_day_reasons = []
    for gate in (daily, weekly_monthly, recovery):
        thirty_day_reasons.extend(gate["blocking_reasons"])
    thirty_day_passed = not thirty_day_reasons
    trial_ref = _ref(evidence.get("trial_ref"))
    if not trial_ref:
        thirty_day_passed = False
        thirty_day_reasons.append("trial_ref is required")

    gates = [
        _gate("thirty_day_trial_passed", "30 unique-date operational coverage with traceability, weekly/monthly replay, and recovery drill evidence", thirty_day_passed, trial_ref, thirty_day_reasons),
        _gate("scheduler_operational", "05:00 scheduler, 04:45 health check, and manual rerun evidence", scheduler["passed"], scheduler["evidence_ref"], scheduler["blocking_reasons"]),
        _gate("text_artifacts_verified", "Stage 1 text delivery artifact evidence", text_artifacts["passed"], text_artifacts["evidence_ref"], text_artifacts["blocking_reasons"]),
        _gate("real_smtp_verified", "real SMTP delivery evidence to the configured recipient", email["passed"], email["evidence_ref"], email["blocking_reasons"]),
        _gate("resource_pressure_ok", "disk, memory, cache, Git artifact, and secret hygiene evidence", resource["passed"], resource["evidence_ref"], resource["blocking_reasons"]),
    ]
    production_ready = all(gate["passed"] for gate in gates)
    return {
        "trial_evidence_id": f"trial-evidence:{trial_id}",
        "validator_id": TRIAL_EVIDENCE_VALIDATOR_ID,
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "trial_id": trial_id,
        "timezone": str(evidence.get("timezone") or DEFAULT_TIMEZONE),
        "expected_days": expected_days,
        "observed_day_count": daily["observed_day_count"],
        "production_evidence_status": "pass" if production_ready else "blocked",
        "accepted_for_production": production_ready,
        "gates": gates,
        "blocking_reasons": [
            reason
            for gate in gates
            for reason in gate["blocking_reasons"]
            if not gate["passed"]
        ],
        "daily_summary": daily["summary"],
        "operational_evidence": _operational_evidence(gates, trial_id),
    }


def validate_trial_evidence_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("validator_id") != TRIAL_EVIDENCE_VALIDATOR_ID:
        errors.append("trial report validator_id is not adp-trial-evidence-v1")
    gates = report.get("gates")
    if not isinstance(gates, list) or not gates:
        errors.append("trial report gates must be a non-empty list")
        return errors
    accepted = bool(report.get("accepted_for_production"))
    failed = [
        str(gate.get("gate_id"))
        for gate in gates
        if isinstance(gate, Mapping) and gate.get("passed") is not True
    ]
    if accepted and failed:
        errors.append("accepted_for_production cannot be true with failed gates: " + ", ".join(failed))
    if accepted and report.get("blocking_reasons"):
        errors.append("accepted_for_production cannot be true with blocking_reasons")
    if not accepted and not report.get("blocking_reasons"):
        errors.append("blocked trial evidence must include blocking_reasons")
    operational = report.get("operational_evidence")
    if not isinstance(operational, Mapping) or operational.get("_validated_by") != TRIAL_EVIDENCE_VALIDATOR_ID:
        errors.append("trial report operational_evidence must include _validated_by")
    return errors


def _evaluate_daily_runs(value: Any, *, expected_days: int) -> dict[str, Any]:
    reasons: list[str] = []
    valid_runs: list[Mapping[str, Any]] = []
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return _check(False, "daily_runs must be a list", observed_day_count=0, valid_runs=[], summary={})

    dates_seen: set[str] = set()
    sources_seen: set[str] = set()
    publications_seen: set[str] = set()
    for index, run in enumerate(value):
        prefix = f"daily_runs[{index}]"
        if not isinstance(run, Mapping):
            reasons.append(f"{prefix} must be an object")
            continue
        valid_runs.append(run)
        run_date = str(run.get("date") or "")
        if not _valid_date(run_date):
            reasons.append(f"{prefix}.date must be ISO YYYY-MM-DD")
        elif run_date in dates_seen:
            reasons.append(f"{prefix}.date duplicates {run_date}")
        dates_seen.add(run_date)
        source_id = str(run.get("source_id") or "")
        publication_id = str(run.get("publication_id") or "")
        if not source_id:
            reasons.append(f"{prefix}.source_id is required")
        elif source_id in sources_seen:
            reasons.append(f"{prefix}.source_id duplicates {source_id}")
        sources_seen.add(source_id)
        if not publication_id:
            reasons.append(f"{prefix}.publication_id is required")
        elif publication_id in publications_seen:
            reasons.append(f"{prefix}.publication_id duplicates {publication_id}")
        publications_seen.add(publication_id)
        if run.get("status") not in PASSING_RUN_STATUSES:
            reasons.append(f"{prefix}.status must be succeeded or degraded")
        if run.get("scheduled_local_time") != TARGET_LOCAL_TIME:
            reasons.append(f"{prefix}.scheduled_local_time must be {TARGET_LOCAL_TIME}")
        for key in (
            "p0_claims_traceable",
            "text_degradation_path_verified",
        ):
            if run.get(key) is not True:
                reasons.append(f"{prefix}.{key} must be true")
        for key in ("duplicate_publication", "unsupported_claims_published", "failure_generated_misleading_content"):
            if run.get(key) is not False:
                reasons.append(f"{prefix}.{key} must be false")
        for key in ("run_record_ref", "text_artifact_ref", "email_ref", "resource_gate_ref"):
            if not _ref(run.get(key)):
                reasons.append(f"{prefix}.{key} is required")

    if len(dates_seen) < expected_days:
        reasons.append(f"observed unique trial days {len(dates_seen)} is below required {expected_days}")

    summary = {
        "unique_days": len(dates_seen),
        "unique_source_ids": len(sources_seen),
        "unique_publication_ids": len(publications_seen),
        "required_days": expected_days,
    }
    return _check(not reasons, *reasons, observed_day_count=len(dates_seen), valid_runs=valid_runs, summary=summary)


def _evaluate_weekly_monthly(value: Any) -> dict[str, Any]:
    data = value if isinstance(value, Mapping) else {}
    reasons = []
    if data.get("weekly_replay_verified") is not True:
        reasons.append("weekly_monthly.weekly_replay_verified must be true")
    if data.get("monthly_replay_verified") is not True:
        reasons.append("weekly_monthly.monthly_replay_verified must be true")
    if not _ref(data.get("ref")):
        reasons.append("weekly_monthly.ref is required")
    return _check(not reasons, *reasons)


def _evaluate_recovery(value: Any) -> dict[str, Any]:
    data = value if isinstance(value, Mapping) else {}
    reasons = []
    if data.get("failure_recovery_drill_verified") is not True:
        reasons.append("recovery.failure_recovery_drill_verified must be true")
    if not _ref(data.get("ref")):
        reasons.append("recovery.ref is required")
    return _check(not reasons, *reasons)


def _evaluate_scheduler(value: Any, *, daily_passed: bool) -> dict[str, Any]:
    data = value if isinstance(value, Mapping) else {}
    reasons = []
    if data.get("enabled") is not True:
        reasons.append("scheduler.enabled must be true")
    if data.get("target_local_time") != TARGET_LOCAL_TIME:
        reasons.append(f"scheduler.target_local_time must be {TARGET_LOCAL_TIME}")
    if data.get("health_check_time") != HEALTH_CHECK_TIME:
        reasons.append(f"scheduler.health_check_time must be {HEALTH_CHECK_TIME}")
    if data.get("manual_rerun_verified") is not True:
        reasons.append("scheduler.manual_rerun_verified must be true")
    if not daily_passed:
        reasons.append("scheduler evidence requires passing daily run evidence")
    ref = _ref(data.get("ref"))
    if not ref:
        reasons.append("scheduler.ref is required")
    return _check(not reasons, *reasons, evidence_ref=ref)


def _evaluate_text_artifacts(value: Any, *, daily_runs: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    data = value if isinstance(value, Mapping) else {}
    reasons = []
    if data.get("b1_text_artifacts_verified") is not True:
        reasons.append("text_artifacts.b1_text_artifacts_verified must be true")
    if any(not _ref(run.get("text_artifact_ref")) for run in daily_runs):
        reasons.append("every daily run must include text_artifact_ref")
    ref = _ref(data.get("ref"))
    if not ref:
        reasons.append("text_artifacts.ref is required")
    return _check(not reasons, *reasons, evidence_ref=ref)


def _evaluate_email(value: Any, *, daily_runs: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    data = value if isinstance(value, Mapping) else {}
    reasons = []
    if data.get("real_smtp_verified") is not True:
        reasons.append("email.real_smtp_verified must be true")
    if data.get("recipient") != DEFAULT_RECIPIENT:
        reasons.append(f"email.recipient must be {DEFAULT_RECIPIENT}")
    if any(not _ref(run.get("email_ref")) for run in daily_runs):
        reasons.append("every daily run must include email_ref")
    ref = _ref(data.get("ref"))
    if not ref:
        reasons.append("email.ref is required")
    return _check(not reasons, *reasons, evidence_ref=ref)


def _evaluate_resource(value: Any, *, daily_runs: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    data = value if isinstance(value, Mapping) else {}
    reasons = []
    for key in ("disk_ok", "memory_ok", "cache_ok", "secrets_ok", "git_large_artifacts_ok"):
        if data.get(key) is not True:
            reasons.append(f"resource_pressure.{key} must be true")
    if any(not _ref(run.get("resource_gate_ref")) for run in daily_runs):
        reasons.append("every daily run must include resource_gate_ref")
    ref = _ref(data.get("ref"))
    if not ref:
        reasons.append("resource_pressure.ref is required")
    return _check(not reasons, *reasons, evidence_ref=ref)


def _operational_evidence(gates: Sequence[Mapping[str, Any]], trial_id: str) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "_validated_by": TRIAL_EVIDENCE_VALIDATOR_ID,
        "_trial_evidence_id": f"trial-evidence:{trial_id}",
    }
    for gate in gates:
        key = str(gate["gate_id"])
        passed = gate.get("passed") is True
        payload[key] = passed
        payload[f"{key}_ref"] = str(gate.get("evidence_ref") or "") if passed else ""
    return payload


def _gate(gate_id: str, description: str, passed: bool, evidence_ref: str, blocking_reasons: Sequence[str]) -> dict[str, Any]:
    return {
        "gate_id": gate_id,
        "description": description,
        "passed": passed,
        "evidence_ref": evidence_ref if passed else "",
        "blocking_reasons": list(blocking_reasons) if not passed else [],
    }


def _check(passed: bool, *reasons: str, **extra: Any) -> dict[str, Any]:
    payload = {"passed": passed, "blocking_reasons": [reason for reason in reasons if reason]}
    payload.update(extra)
    return payload


def _positive_int(value: Any, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _valid_date(value: str) -> bool:
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def _ref(value: Any) -> str:
    return str(value or "").strip()
