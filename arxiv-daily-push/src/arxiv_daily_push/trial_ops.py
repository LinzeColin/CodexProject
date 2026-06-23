"""Operational trial evidence annotations for Phase 11."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .config import DEFAULT_RECIPIENT, DEFAULT_TIMEZONE
from .trial import TARGET_LOCAL_TIME, TRIAL_DAYS_REQUIRED, evaluate_trial_evidence, validate_trial_evidence_report


TRIAL_OPS_MODEL_ID = "adp-trial-ops-evidence-v1"


def annotate_trial_operational_evidence(
    existing_evidence: Mapping[str, Any],
    *,
    generated_at: str,
    trial_id: str = "adp-trial-current",
    trial_ref: str = "",
    expected_days: int = TRIAL_DAYS_REQUIRED,
    scheduler_enabled: bool = False,
    manual_rerun_verified: bool = False,
    scheduler_ref: str = "",
    text_artifacts_verified: bool = False,
    text_artifact_ref: str = "",
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
    """Merge explicit operational evidence refs into an existing trial package."""

    evidence = _base_evidence(existing_evidence, trial_id=trial_id, trial_ref=trial_ref, expected_days=expected_days)
    updated = False
    reasons: list[str] = []

    updated |= _merge_scheduler(
        evidence,
        scheduler_enabled=scheduler_enabled,
        manual_rerun_verified=manual_rerun_verified,
        scheduler_ref=scheduler_ref,
        reasons=reasons,
    )
    updated |= _merge_text_artifacts(evidence, text_artifacts_verified=text_artifacts_verified, text_artifact_ref=text_artifact_ref, reasons=reasons)
    updated |= _merge_release(evidence, private_release_verified=private_release_verified, release_ref=release_ref, reasons=reasons)
    updated |= _merge_email(evidence, real_smtp_verified=real_smtp_verified, email_ref=email_ref, reasons=reasons)
    updated |= _merge_resource(evidence, resource_pressure_ok=resource_pressure_ok, resource_ref=resource_ref, reasons=reasons)
    updated |= _merge_weekly_monthly(
        evidence,
        weekly_replay_verified=weekly_replay_verified,
        monthly_replay_verified=monthly_replay_verified,
        weekly_monthly_ref=weekly_monthly_ref,
        reasons=reasons,
    )
    updated |= _merge_recovery(
        evidence,
        recovery_drill_verified=recovery_drill_verified,
        recovery_ref=recovery_ref,
        reasons=reasons,
    )

    if not updated and not reasons:
        reasons.append("no operational evidence annotation requested")
    if reasons:
        report = _base_ops_report(generated_at=generated_at, trial_evidence=evidence)
        report["blocking_reasons"] = reasons
        return _with_validation(report)

    trial_report = evaluate_trial_evidence(evidence, generated_at=generated_at)
    report = _base_ops_report(generated_at=generated_at, trial_evidence=evidence, trial_report=trial_report)
    report.update(
        {
            "status": "pass",
            "trial_evidence_updated": True,
            "accepted_for_production": trial_report["accepted_for_production"],
            "observed_day_count": trial_report["observed_day_count"],
        }
    )
    return _with_validation(report)


def validate_trial_ops_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != TRIAL_OPS_MODEL_ID:
        errors.append("trial ops model_id must be adp-trial-ops-evidence-v1")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("trial ops status must be pass or blocked")
    if report.get("trial_evidence_updated") not in {True, False}:
        errors.append("trial ops report requires trial_evidence_updated boolean")
    trial_evidence = report.get("trial_evidence")
    if not isinstance(trial_evidence, Mapping):
        errors.append("trial ops report requires trial_evidence object")
    trial_report = report.get("trial_evidence_report")
    if isinstance(trial_report, Mapping) and trial_report:
        errors.extend(validate_trial_evidence_report(trial_report))
    elif report.get("status") == "pass":
        errors.append("passing trial ops report requires trial_evidence_report")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked trial ops report requires blocking_reasons")
    return errors


def _base_evidence(existing: Mapping[str, Any], *, trial_id: str, trial_ref: str, expected_days: int) -> dict[str, Any]:
    evidence = dict(existing or {})
    evidence["trial_id"] = str(evidence.get("trial_id") or trial_id or "adp-trial-current")
    evidence["timezone"] = str(evidence.get("timezone") or DEFAULT_TIMEZONE)
    if trial_ref:
        evidence["trial_ref"] = trial_ref
    else:
        evidence.setdefault("trial_ref", "")
    period = dict(evidence.get("period") or {})
    period["expected_days"] = int(period.get("expected_days") or expected_days or TRIAL_DAYS_REQUIRED)
    evidence["period"] = period
    evidence["daily_runs"] = [dict(run) for run in evidence.get("daily_runs") or [] if isinstance(run, Mapping)]
    _section(
        evidence,
        "scheduler",
        {"enabled": False, "target_local_time": TARGET_LOCAL_TIME, "health_check_time": "04:45", "manual_rerun_verified": False, "ref": ""},
    )
    _section(evidence, "text_artifacts", {"b1_text_artifacts_verified": False, "ref": ""})
    _section(evidence, "release", {"private_release_verified": False, "ref": ""})
    _section(evidence, "email", {"real_smtp_verified": False, "recipient": DEFAULT_RECIPIENT, "ref": ""})
    _section(
        evidence,
        "resource_pressure",
        {"disk_ok": False, "memory_ok": False, "cache_ok": False, "secrets_ok": False, "git_large_artifacts_ok": False, "ref": ""},
    )
    _section(evidence, "weekly_monthly", {"weekly_replay_verified": False, "monthly_replay_verified": False, "ref": ""})
    _section(evidence, "recovery", {"failure_recovery_drill_verified": False, "ref": ""})
    return evidence


def _section(evidence: dict[str, Any], key: str, defaults: Mapping[str, Any]) -> dict[str, Any]:
    current = dict(defaults)
    existing = evidence.get(key)
    if isinstance(existing, Mapping):
        for item_key, value in existing.items():
            if value not in (None, ""):
                if isinstance(current.get(item_key), bool):
                    if isinstance(value, bool):
                        current[item_key] = value
                else:
                    current[item_key] = value
    evidence[key] = current
    return current


def _merge_scheduler(
    evidence: dict[str, Any],
    *,
    scheduler_enabled: bool,
    manual_rerun_verified: bool,
    scheduler_ref: str,
    reasons: list[str],
) -> bool:
    requested = scheduler_enabled or manual_rerun_verified or bool(scheduler_ref)
    if not requested:
        return False
    section = _section(
        evidence,
        "scheduler",
        {"enabled": False, "target_local_time": TARGET_LOCAL_TIME, "health_check_time": "04:45", "manual_rerun_verified": False, "ref": ""},
    )
    section["enabled"] = _is_true(section.get("enabled")) or scheduler_enabled
    section["manual_rerun_verified"] = _is_true(section.get("manual_rerun_verified")) or manual_rerun_verified
    if scheduler_ref:
        section["ref"] = scheduler_ref
    if (scheduler_enabled or manual_rerun_verified) and not str(section.get("ref") or "").strip():
        reasons.append("scheduler evidence ref is required when scheduler evidence is verified")
    return True


def _merge_release(evidence: dict[str, Any], *, private_release_verified: bool, release_ref: str, reasons: list[str]) -> bool:
    requested = private_release_verified or bool(release_ref)
    if not requested:
        return False
    section = _section(evidence, "release", {"private_release_verified": False, "ref": ""})
    section["private_release_verified"] = _is_true(section.get("private_release_verified")) or private_release_verified
    if release_ref:
        section["ref"] = release_ref
    if private_release_verified and not str(section.get("ref") or "").strip():
        reasons.append("release ref is required when private Release evidence is verified")
    return True


def _merge_text_artifacts(evidence: dict[str, Any], *, text_artifacts_verified: bool, text_artifact_ref: str, reasons: list[str]) -> bool:
    requested = text_artifacts_verified or bool(text_artifact_ref)
    if not requested:
        return False
    section = _section(evidence, "text_artifacts", {"b1_text_artifacts_verified": False, "ref": ""})
    section["b1_text_artifacts_verified"] = _is_true(section.get("b1_text_artifacts_verified")) or text_artifacts_verified
    if text_artifact_ref:
        section["ref"] = text_artifact_ref
    if text_artifacts_verified and not str(section.get("ref") or "").strip():
        reasons.append("text artifact ref is required when Stage 1 text artifacts are verified")
    return True


def _merge_email(evidence: dict[str, Any], *, real_smtp_verified: bool, email_ref: str, reasons: list[str]) -> bool:
    requested = real_smtp_verified or bool(email_ref)
    if not requested:
        return False
    section = _section(evidence, "email", {"real_smtp_verified": False, "recipient": DEFAULT_RECIPIENT, "ref": ""})
    section["real_smtp_verified"] = _is_true(section.get("real_smtp_verified")) or real_smtp_verified
    section["recipient"] = DEFAULT_RECIPIENT
    if email_ref:
        section["ref"] = email_ref
    if real_smtp_verified and not str(section.get("ref") or "").strip():
        reasons.append("email ref is required when real SMTP evidence is verified")
    return True


def _merge_resource(evidence: dict[str, Any], *, resource_pressure_ok: bool, resource_ref: str, reasons: list[str]) -> bool:
    requested = resource_pressure_ok or bool(resource_ref)
    if not requested:
        return False
    section = _section(
        evidence,
        "resource_pressure",
        {"disk_ok": False, "memory_ok": False, "cache_ok": False, "secrets_ok": False, "git_large_artifacts_ok": False, "ref": ""},
    )
    if resource_pressure_ok:
        for key in ("disk_ok", "memory_ok", "cache_ok", "secrets_ok", "git_large_artifacts_ok"):
            section[key] = True
    if resource_ref:
        section["ref"] = resource_ref
    if resource_pressure_ok and not str(section.get("ref") or "").strip():
        reasons.append("resource ref is required when resource pressure evidence is verified")
    return True


def _merge_weekly_monthly(
    evidence: dict[str, Any],
    *,
    weekly_replay_verified: bool,
    monthly_replay_verified: bool,
    weekly_monthly_ref: str,
    reasons: list[str],
) -> bool:
    requested = weekly_replay_verified or monthly_replay_verified or bool(weekly_monthly_ref)
    if not requested:
        return False
    section = _section(evidence, "weekly_monthly", {"weekly_replay_verified": False, "monthly_replay_verified": False, "ref": ""})
    section["weekly_replay_verified"] = _is_true(section.get("weekly_replay_verified")) or weekly_replay_verified
    section["monthly_replay_verified"] = _is_true(section.get("monthly_replay_verified")) or monthly_replay_verified
    if weekly_monthly_ref:
        section["ref"] = weekly_monthly_ref
    if (weekly_replay_verified or monthly_replay_verified) and not str(section.get("ref") or "").strip():
        reasons.append("weekly/monthly replay ref is required when replay evidence is verified")
    if weekly_monthly_ref and not (section["weekly_replay_verified"] or section["monthly_replay_verified"]):
        reasons.append("weekly/monthly replay verification flag is required when replay ref is supplied")
    return True


def _merge_recovery(evidence: dict[str, Any], *, recovery_drill_verified: bool, recovery_ref: str, reasons: list[str]) -> bool:
    requested = recovery_drill_verified or bool(recovery_ref)
    if not requested:
        return False
    section = _section(evidence, "recovery", {"failure_recovery_drill_verified": False, "ref": ""})
    section["failure_recovery_drill_verified"] = _is_true(section.get("failure_recovery_drill_verified")) or recovery_drill_verified
    if recovery_ref:
        section["ref"] = recovery_ref
    if recovery_drill_verified and not str(section.get("ref") or "").strip():
        reasons.append("recovery ref is required when recovery drill evidence is verified")
    if recovery_ref and not section["failure_recovery_drill_verified"]:
        reasons.append("recovery drill verification flag is required when recovery ref is supplied")
    return True


def _base_ops_report(
    *,
    generated_at: str,
    trial_evidence: Mapping[str, Any],
    trial_report: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "ops_update_id": f"trial-ops:{trial_evidence.get('trial_id', 'adp-trial-current')}:{generated_at}",
        "model_id": TRIAL_OPS_MODEL_ID,
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "status": "blocked",
        "trial_evidence_updated": False,
        "trial_evidence": dict(trial_evidence),
        "trial_evidence_report": dict(trial_report or {}),
        "observed_day_count": len(trial_evidence.get("daily_runs") or []),
        "accepted_for_production": False,
        "blocking_reasons": [],
    }


def _with_validation(report: Mapping[str, Any]) -> dict[str, Any]:
    normalized = dict(report)
    normalized["validation_errors"] = validate_trial_ops_report(normalized)
    return normalized


def _is_true(value: Any) -> bool:
    return value is True
