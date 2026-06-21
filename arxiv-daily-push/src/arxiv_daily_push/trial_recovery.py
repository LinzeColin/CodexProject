"""Recovery drill evidence for Phase 11 trial runs."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .scheduled_execution import SCHEDULED_EXECUTION_MODEL_ID, validate_scheduled_execution_report


TRIAL_RECOVERY_MODEL_ID = "adp-trial-recovery-v1"
FAILURE_STATUSES = {"blocked", "failed", "degraded"}
REQUIRED_RECOVERY_REFS = ("daily_run_ref", "release_ref", "email_ref", "resource_gate_ref")


def build_trial_recovery_evidence(
    failure_execution_report: Mapping[str, Any],
    recovery_execution_report: Mapping[str, Any],
    *,
    generated_at: str,
    failure_ref: str = "",
    recovery_ref: str = "",
) -> dict[str, Any]:
    """Build a fail-closed recovery drill evidence report.

    The report proves only that a failed/degraded scheduled daily run and a
    later production-ready daily rerun are both backed by durable evidence refs.
    It does not mutate the trial ledger or claim the 30-day trial has passed.
    """

    failure = dict(failure_execution_report or {})
    recovery = dict(recovery_execution_report or {})
    base = _base_report(generated_at=generated_at, failure_ref=failure_ref, recovery_ref=recovery_ref)
    base["failure_summary"] = _execution_summary(failure)
    base["recovery_summary"] = _execution_summary(recovery)
    base["evidence_refs"] = _recovery_refs(recovery)

    reasons: list[str] = []
    failure_errors = validate_scheduled_execution_report(failure)
    recovery_errors = validate_scheduled_execution_report(recovery)
    if failure_errors:
        reasons.append(f"failure scheduled execution report invalid: {failure_errors[0]}")
    if recovery_errors:
        reasons.append(f"recovery scheduled execution report invalid: {recovery_errors[0]}")

    _validate_failure_execution(failure, reasons)
    _validate_recovery_execution(recovery, reasons)
    _validate_dates(failure, recovery, reasons)
    if not _ref(failure_ref):
        reasons.append("failure_ref is required before recovery drill evidence can be verified")
    if not _ref(recovery_ref):
        reasons.append("recovery_ref is required before recovery drill evidence can be verified")

    if reasons:
        base["blocking_reasons"] = reasons
        return _with_validation(base)

    base.update(
        {
            "status": "pass",
            "recovery_drill_verified": True,
            "annotation_hint": {
                "recovery_drill_verified": True,
                "recovery_ref": recovery_ref,
            },
        }
    )
    return _with_validation(base)


def validate_trial_recovery_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != TRIAL_RECOVERY_MODEL_ID:
        errors.append("trial recovery model_id must be adp-trial-recovery-v1")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("trial recovery status must be pass or blocked")
    if report.get("recovery_drill_verified") not in {True, False}:
        errors.append("trial recovery report requires recovery_drill_verified boolean")
    if not isinstance(report.get("failure_summary"), Mapping):
        errors.append("trial recovery report requires failure_summary")
    if not isinstance(report.get("recovery_summary"), Mapping):
        errors.append("trial recovery report requires recovery_summary")
    if not isinstance(report.get("evidence_refs"), Mapping):
        errors.append("trial recovery report requires evidence_refs")
    if report.get("status") == "pass":
        if report.get("recovery_drill_verified") is not True:
            errors.append("passing trial recovery report requires recovery_drill_verified true")
        if report.get("blocking_reasons"):
            errors.append("passing trial recovery report cannot include blocking_reasons")
        if not _ref(report.get("failure_ref")):
            errors.append("passing trial recovery report requires failure_ref")
        if not _ref(report.get("recovery_ref")):
            errors.append("passing trial recovery report requires recovery_ref")
        refs = report.get("evidence_refs")
        if isinstance(refs, Mapping):
            for key in REQUIRED_RECOVERY_REFS:
                if not str(refs.get(key) or "").strip():
                    errors.append(f"passing trial recovery report requires evidence_refs.{key}")
        hint = report.get("annotation_hint")
        if not isinstance(hint, Mapping):
            errors.append("passing trial recovery report requires annotation_hint")
        elif hint.get("recovery_ref") != report.get("recovery_ref"):
            errors.append("annotation_hint recovery_ref must match recovery_ref")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked trial recovery report requires blocking_reasons")
    return errors


def _validate_failure_execution(report: Mapping[str, Any], reasons: list[str]) -> None:
    if report.get("validator_id") != SCHEDULED_EXECUTION_MODEL_ID:
        reasons.append("failure report must be an adp-scheduled-execution-v1 report")
    if report.get("mode") != "daily-run":
        reasons.append("failure report mode must be daily-run")
    if report.get("status") not in FAILURE_STATUSES:
        reasons.append("failure report status must be blocked, failed, or degraded")
    if report.get("exit_code") != 2:
        reasons.append("failure report exit_code must be 2")
    if report.get("production_evidence_ready") is True:
        reasons.append("failure report cannot be production_evidence_ready")
    if not report.get("blocking_reasons"):
        reasons.append("failure report requires blocking_reasons")
    _require_sent_notification(report, "failure", reasons)
    daily = report.get("daily_run_report")
    if isinstance(daily, Mapping):
        if daily.get("failure_generated_misleading_content") is not False:
            reasons.append("failure daily_run_report must not generate misleading content")
        if daily.get("unsupported_claims_published") is not False:
            reasons.append("failure daily_run_report must not publish unsupported claims")


def _validate_recovery_execution(report: Mapping[str, Any], reasons: list[str]) -> None:
    if report.get("validator_id") != SCHEDULED_EXECUTION_MODEL_ID:
        reasons.append("recovery report must be an adp-scheduled-execution-v1 report")
    if report.get("mode") != "daily-run":
        reasons.append("recovery report mode must be daily-run")
    if report.get("status") != "succeeded":
        reasons.append("recovery report status must be succeeded")
    if report.get("exit_code") != 0:
        reasons.append("recovery report exit_code must be 0")
    if report.get("production_evidence_ready") is not True:
        reasons.append("recovery report must be production_evidence_ready")
    refs = report.get("evidence_refs")
    if not isinstance(refs, Mapping):
        reasons.append("recovery report requires evidence_refs")
    else:
        for key in REQUIRED_RECOVERY_REFS:
            if not str(refs.get(key) or "").strip():
                reasons.append(f"recovery report evidence_refs.{key} is required")
    _require_sent_notification(report, "recovery", reasons)
    daily = report.get("daily_run_report")
    if not isinstance(daily, Mapping):
        reasons.append("recovery report requires daily_run_report")
    else:
        if daily.get("scheduled_local_time") != "05:00":
            reasons.append("recovery daily_run_report scheduled_local_time must be 05:00")
        if daily.get("p0_claims_traceable") is not True:
            reasons.append("recovery daily_run_report requires p0_claims_traceable true")
        if daily.get("failure_generated_misleading_content") is not False:
            reasons.append("recovery daily_run_report must not generate misleading content")
        if daily.get("unsupported_claims_published") is not False:
            reasons.append("recovery daily_run_report must not publish unsupported claims")


def _require_sent_notification(report: Mapping[str, Any], label: str, reasons: list[str]) -> None:
    notification = report.get("notification_report")
    if not isinstance(notification, Mapping):
        reasons.append(f"{label} report requires notification_report")
        return
    if notification.get("status") != "sent":
        reasons.append(f"{label} notification_report status must be sent")
    if not _ref(notification.get("delivery_ref")):
        reasons.append(f"{label} notification_report requires delivery_ref")


def _validate_dates(failure: Mapping[str, Any], recovery: Mapping[str, Any], reasons: list[str]) -> None:
    failure_daily = failure.get("daily_run_report")
    recovery_daily = recovery.get("daily_run_report")
    if not isinstance(failure_daily, Mapping) or not isinstance(recovery_daily, Mapping):
        return
    failure_date = str(failure_daily.get("date") or "")
    recovery_date = str(recovery_daily.get("date") or "")
    if failure_date and recovery_date and failure_date != recovery_date:
        reasons.append("failure and recovery daily_run_report dates must match")


def _execution_summary(report: Mapping[str, Any]) -> dict[str, Any]:
    notification = report.get("notification_report") if isinstance(report.get("notification_report"), Mapping) else {}
    daily = report.get("daily_run_report") if isinstance(report.get("daily_run_report"), Mapping) else {}
    return {
        "execution_id": str(report.get("execution_id") or ""),
        "validator_id": str(report.get("validator_id") or ""),
        "mode": str(report.get("mode") or ""),
        "status": str(report.get("status") or ""),
        "exit_code": report.get("exit_code"),
        "production_evidence_ready": bool(report.get("production_evidence_ready")),
        "blocking_reasons": list(report.get("blocking_reasons") or []),
        "notification_status": str(notification.get("status") or ""),
        "notification_ref": str(notification.get("delivery_ref") or ""),
        "daily_run_id": str(daily.get("run_id") or ""),
        "date": str(daily.get("date") or ""),
        "source_id": str(daily.get("source_id") or ""),
        "publication_id": str(daily.get("publication_id") or ""),
    }


def _recovery_refs(report: Mapping[str, Any]) -> dict[str, str]:
    refs = report.get("evidence_refs") if isinstance(report.get("evidence_refs"), Mapping) else {}
    return {key: str(refs.get(key) or "") for key in REQUIRED_RECOVERY_REFS}


def _base_report(*, generated_at: str, failure_ref: str, recovery_ref: str) -> dict[str, Any]:
    return {
        "recovery_report_id": f"trial-recovery:{generated_at}",
        "model_id": TRIAL_RECOVERY_MODEL_ID,
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "status": "blocked",
        "recovery_drill_verified": False,
        "failure_ref": failure_ref,
        "recovery_ref": recovery_ref,
        "failure_summary": {},
        "recovery_summary": {},
        "evidence_refs": {},
        "annotation_hint": {},
        "blocking_reasons": [],
    }


def _with_validation(report: Mapping[str, Any]) -> dict[str, Any]:
    normalized = dict(report)
    normalized["validation_errors"] = validate_trial_recovery_report(normalized)
    return normalized


def _ref(value: Any) -> str:
    text = str(value or "").strip()
    return text if "://" in text else ""
