"""Incremental Phase 11 trial evidence ledger updates."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .config import DEFAULT_RECIPIENT, DEFAULT_TIMEZONE
from .scheduled_execution import validate_scheduled_execution_report
from .trial import TARGET_LOCAL_TIME, TRIAL_DAYS_REQUIRED, evaluate_trial_evidence, validate_trial_evidence_report


TRIAL_LEDGER_MODEL_ID = "adp-trial-ledger-v1"
DEFAULT_TRIAL_ID = "adp-trial-current"


def update_trial_evidence_ledger(
    existing_evidence: Mapping[str, Any] | None,
    scheduled_execution_report: Mapping[str, Any],
    *,
    generated_at: str,
    trial_id: str = DEFAULT_TRIAL_ID,
    trial_ref: str = "",
    expected_days: int = TRIAL_DAYS_REQUIRED,
    text_degradation_path_verified: bool = False,
    video_degradation_path_verified: bool = False,
    text_artifacts_verified: bool = False,
    text_artifact_ref: str = "",
    scheduler_enabled: bool = False,
    manual_rerun_verified: bool = False,
    scheduler_ref: str = "",
    private_release_verified: bool = False,
    release_ref: str = "",
    real_smtp_verified: bool = False,
    email_ref: str = "",
    resource_pressure_ok: bool = False,
    resource_ref: str = "",
    weekly_replay_verified: bool = False,
    monthly_replay_verified: bool = False,
    weekly_monthly_ref: str = "",
    recovery_drill_verified: bool = False,
    recovery_ref: str = "",
) -> dict[str, Any]:
    """Append one production-ready scheduled daily run to a trial evidence package."""

    scheduled_refs = scheduled_execution_report.get("evidence_refs") if isinstance(scheduled_execution_report.get("evidence_refs"), Mapping) else {}
    scheduled_text_ref = str(scheduled_refs.get("text_artifact_ref") or "")
    if scheduled_execution_report.get("production_evidence_ready") is True and scheduled_text_ref:
        text_artifacts_verified = True
        text_artifact_ref = text_artifact_ref or scheduled_text_ref

    base_evidence = _base_trial_evidence(
        existing_evidence,
        trial_id=trial_id,
        trial_ref=trial_ref,
        expected_days=expected_days,
        scheduler_enabled=scheduler_enabled,
        manual_rerun_verified=manual_rerun_verified,
        scheduler_ref=scheduler_ref,
        text_artifacts_verified=text_artifacts_verified,
        text_artifact_ref=text_artifact_ref,
        private_release_verified=private_release_verified,
        release_ref=release_ref,
        real_smtp_verified=real_smtp_verified,
        email_ref=email_ref,
        resource_pressure_ok=resource_pressure_ok,
        resource_ref=resource_ref,
        weekly_replay_verified=weekly_replay_verified,
        monthly_replay_verified=monthly_replay_verified,
        weekly_monthly_ref=weekly_monthly_ref,
        recovery_drill_verified=recovery_drill_verified,
        recovery_ref=recovery_ref,
    )
    daily_entry, reasons = _daily_entry_from_scheduled_report(
        scheduled_execution_report,
        text_degradation_path_verified=text_degradation_path_verified,
    )
    if not reasons and daily_entry:
        reasons.extend(_duplicate_reasons(base_evidence.get("daily_runs"), daily_entry))
    if reasons:
        report = _base_update_report(generated_at=generated_at, trial_evidence=base_evidence)
        report["blocking_reasons"] = reasons
        return _with_validation(report)

    updated = dict(base_evidence)
    updated["daily_runs"] = [dict(run) for run in base_evidence.get("daily_runs") or []] + [daily_entry]
    if not ((updated.get("period") or {}).get("start_date")):
        updated["period"]["start_date"] = daily_entry["date"]
    updated["period"]["end_date"] = daily_entry["date"]
    trial_report = evaluate_trial_evidence(updated, generated_at=generated_at)

    report = _base_update_report(generated_at=generated_at, trial_evidence=updated, trial_report=trial_report)
    report.update(
        {
            "status": "pass",
            "ledger_updated": True,
            "daily_entry": daily_entry,
            "observed_day_count": trial_report["observed_day_count"],
            "accepted_for_production": trial_report["accepted_for_production"],
        }
    )
    return _with_validation(report)


def validate_trial_ledger_update_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != TRIAL_LEDGER_MODEL_ID:
        errors.append("trial ledger model_id must be adp-trial-ledger-v1")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("trial ledger status must be pass or blocked")
    if report.get("ledger_updated") not in {True, False}:
        errors.append("trial ledger report requires ledger_updated boolean")
    trial_evidence = report.get("trial_evidence")
    if not isinstance(trial_evidence, Mapping):
        errors.append("trial ledger report requires trial_evidence object")
    trial_report = report.get("trial_evidence_report")
    if isinstance(trial_report, Mapping) and trial_report:
        errors.extend(validate_trial_evidence_report(trial_report))
    elif report.get("status") == "pass":
        errors.append("passing trial ledger report requires trial_evidence_report")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked trial ledger report requires blocking_reasons")
    if report.get("status") == "pass" and not isinstance(report.get("daily_entry"), Mapping):
        errors.append("passing trial ledger report requires daily_entry")
    return errors


def _daily_entry_from_scheduled_report(
    report: Mapping[str, Any],
    *,
    text_degradation_path_verified: bool,
) -> tuple[dict[str, Any] | None, list[str]]:
    reasons = validate_scheduled_execution_report(report)
    if reasons:
        return None, [f"invalid scheduled execution report: {reasons[0]}"]
    if report.get("mode") != "daily-run":
        reasons.append("scheduled execution report mode must be daily-run")
    if report.get("production_evidence_ready") is not True:
        reasons.append("scheduled execution report must be production_evidence_ready")
    daily = report.get("daily_run_report")
    refs = report.get("evidence_refs")
    if not isinstance(daily, Mapping):
        reasons.append("scheduled execution report daily_run_report is required")
        daily = {}
    if not isinstance(refs, Mapping):
        reasons.append("scheduled execution report evidence_refs is required")
        refs = {}
    for key in ("date", "run_id", "source_id", "publication_id"):
        if not str(daily.get(key) or "").strip():
            reasons.append(f"daily_run_report.{key} is required")
    for key in ("daily_run_ref", "text_artifact_ref", "email_ref", "resource_gate_ref"):
        if not str(refs.get(key) or "").strip():
            reasons.append(f"evidence_refs.{key} is required")
    if daily.get("p0_claims_traceable") is not True:
        reasons.append("daily_run_report.p0_claims_traceable must be true")
    if daily.get("unsupported_claims_published") is not False:
        reasons.append("daily_run_report.unsupported_claims_published must be false")
    if daily.get("failure_generated_misleading_content") is not False:
        reasons.append("daily_run_report.failure_generated_misleading_content must be false")
    if reasons:
        return None, reasons
    return (
        {
            "date": str(daily["date"]),
            "run_id": str(daily["run_id"]),
            "source_id": str(daily["source_id"]),
            "publication_id": str(daily["publication_id"]),
            "status": str(daily.get("status") or "succeeded"),
            "scheduled_local_time": str(daily.get("scheduled_local_time") or TARGET_LOCAL_TIME),
            "p0_claims_traceable": True,
            "text_degradation_path_verified": bool(text_degradation_path_verified),
            "duplicate_publication": False,
            "unsupported_claims_published": False,
            "failure_generated_misleading_content": False,
            "run_record_ref": str(refs["daily_run_ref"]),
            "text_artifact_ref": str(refs["text_artifact_ref"]),
            "release_ref": str(refs.get("release_ref") or ""),
            "email_ref": str(refs["email_ref"]),
            "resource_gate_ref": str(refs["resource_gate_ref"]),
            "scheduled_execution_ref": str(report.get("execution_id") or ""),
        },
        [],
    )


def _base_trial_evidence(
    existing: Mapping[str, Any] | None,
    *,
    trial_id: str,
    trial_ref: str,
    expected_days: int,
    scheduler_enabled: bool,
    manual_rerun_verified: bool,
    scheduler_ref: str,
    text_artifacts_verified: bool,
    text_artifact_ref: str,
    private_release_verified: bool,
    release_ref: str,
    real_smtp_verified: bool,
    email_ref: str,
    resource_pressure_ok: bool,
    resource_ref: str,
    weekly_replay_verified: bool,
    monthly_replay_verified: bool,
    weekly_monthly_ref: str,
    recovery_drill_verified: bool,
    recovery_ref: str,
) -> dict[str, Any]:
    evidence = dict(existing or {})
    evidence["trial_id"] = str(evidence.get("trial_id") or trial_id or DEFAULT_TRIAL_ID)
    evidence["timezone"] = str(evidence.get("timezone") or DEFAULT_TIMEZONE)
    if trial_ref:
        evidence["trial_ref"] = trial_ref
    else:
        evidence.setdefault("trial_ref", "")
    period = dict(evidence.get("period") or {})
    period["expected_days"] = int(period.get("expected_days") or expected_days or TRIAL_DAYS_REQUIRED)
    evidence["period"] = period
    evidence["daily_runs"] = [dict(run) for run in evidence.get("daily_runs") or [] if isinstance(run, Mapping)]
    evidence["scheduler"] = _merge_section(
        evidence.get("scheduler"),
        {
            "enabled": bool(scheduler_enabled),
            "target_local_time": TARGET_LOCAL_TIME,
            "health_check_time": "04:45",
            "manual_rerun_verified": bool(manual_rerun_verified),
            "ref": scheduler_ref,
        },
    )
    evidence["text_artifacts"] = _merge_section(
        evidence.get("text_artifacts"),
        {"b1_text_artifacts_verified": bool(text_artifacts_verified), "ref": text_artifact_ref},
    )
    evidence["release"] = _merge_section(
        evidence.get("release"),
        {"private_release_verified": bool(private_release_verified), "ref": release_ref},
    )
    evidence["email"] = _merge_section(
        evidence.get("email"),
        {"real_smtp_verified": bool(real_smtp_verified), "recipient": DEFAULT_RECIPIENT, "ref": email_ref},
    )
    evidence["resource_pressure"] = _merge_section(
        evidence.get("resource_pressure"),
        {
            "disk_ok": bool(resource_pressure_ok),
            "memory_ok": bool(resource_pressure_ok),
            "cache_ok": bool(resource_pressure_ok),
            "secrets_ok": bool(resource_pressure_ok),
            "git_large_artifacts_ok": bool(resource_pressure_ok),
            "ref": resource_ref,
        },
    )
    evidence["weekly_monthly"] = _merge_section(
        evidence.get("weekly_monthly"),
        {
            "weekly_replay_verified": bool(weekly_replay_verified),
            "monthly_replay_verified": bool(monthly_replay_verified),
            "ref": weekly_monthly_ref,
        },
    )
    evidence["recovery"] = _merge_section(
        evidence.get("recovery"),
        {"failure_recovery_drill_verified": bool(recovery_drill_verified), "ref": recovery_ref},
    )
    return evidence


def _merge_section(existing: Any, defaults: Mapping[str, Any]) -> dict[str, Any]:
    section = dict(defaults)
    if isinstance(existing, Mapping):
        for key, value in existing.items():
            if value not in (None, ""):
                if isinstance(value, bool) and isinstance(section.get(key), bool):
                    section[key] = bool(value or section[key])
                else:
                    section[key] = value
    return section


def _duplicate_reasons(existing_runs: Any, daily_entry: Mapping[str, Any]) -> list[str]:
    reasons: list[str] = []
    runs = existing_runs if isinstance(existing_runs, list) else []
    for index, run in enumerate(runs):
        if not isinstance(run, Mapping):
            continue
        for key in ("date", "source_id", "publication_id"):
            if str(run.get(key) or "") == str(daily_entry.get(key) or ""):
                reasons.append(f"daily_runs[{index}].{key} duplicates new {key} {daily_entry.get(key)}")
    return reasons


def _base_update_report(
    *,
    generated_at: str,
    trial_evidence: Mapping[str, Any],
    trial_report: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "ledger_update_id": f"trial-ledger:{trial_evidence.get('trial_id', DEFAULT_TRIAL_ID)}:{generated_at}",
        "model_id": TRIAL_LEDGER_MODEL_ID,
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "status": "blocked",
        "ledger_updated": False,
        "trial_evidence": dict(trial_evidence),
        "trial_evidence_report": dict(trial_report or {}),
        "daily_entry": {},
        "observed_day_count": len(trial_evidence.get("daily_runs") or []),
        "accepted_for_production": False,
        "blocking_reasons": [],
    }


def _with_validation(report: Mapping[str, Any]) -> dict[str, Any]:
    normalized = dict(report)
    normalized["validation_errors"] = validate_trial_ledger_update_report(normalized)
    return normalized
