"""Weekly and monthly replay evidence for Phase 11 trial runs."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date
from typing import Any

from .config import DEFAULT_TIMEZONE
from .trial import PASSING_RUN_STATUSES, TARGET_LOCAL_TIME, TRIAL_DAYS_REQUIRED


TRIAL_REPLAY_MODEL_ID = "adp-trial-replay-v1"
WEEKLY_REPLAY_DAYS_REQUIRED = 7


def build_trial_replay_evidence(
    trial_evidence: Mapping[str, Any],
    *,
    generated_at: str,
    weekly_replay: bool = False,
    monthly_replay: bool = False,
    replay_ref: str = "",
) -> dict[str, Any]:
    """Build a fail-closed weekly/monthly replay evidence report.

    The report validates that replay evidence is derived from production-ready
    daily trial entries. It does not mutate the trial ledger or claim that
    replay output has been archived unless a durable replay_ref is supplied.
    """

    evidence = dict(trial_evidence or {})
    trial_id = str(evidence.get("trial_id") or "adp-trial-current")
    period = evidence.get("period") if isinstance(evidence.get("period"), Mapping) else {}
    expected_days = _positive_int(period.get("expected_days"), TRIAL_DAYS_REQUIRED)
    daily_runs = evidence.get("daily_runs")
    base = _base_report(
        generated_at=generated_at,
        trial_id=trial_id,
        timezone=str(evidence.get("timezone") or DEFAULT_TIMEZONE),
        expected_days=expected_days,
        weekly_replay=weekly_replay,
        monthly_replay=monthly_replay,
        replay_ref=replay_ref,
    )

    valid_runs, daily_reasons = _valid_daily_runs(daily_runs)
    monthly_days_required = max(expected_days, TRIAL_DAYS_REQUIRED)
    coverage = _coverage(valid_runs, monthly_days_required=monthly_days_required)
    base["observed_day_count"] = coverage["unique_days"]
    base["date_range"] = coverage["date_range"]
    base["coverage"] = coverage
    base["daily_entry_refs"] = _daily_entry_refs(valid_runs)

    reasons = list(daily_reasons)
    if not weekly_replay and not monthly_replay:
        reasons.append("at least one replay mode must be requested")
    if (weekly_replay or monthly_replay) and not _ref(replay_ref):
        reasons.append("replay_ref is required before replay evidence can be verified")
    if weekly_replay:
        if coverage["unique_days"] < WEEKLY_REPLAY_DAYS_REQUIRED:
            reasons.append(f"weekly replay requires at least {WEEKLY_REPLAY_DAYS_REQUIRED} unique daily entries")
        if coverage["longest_consecutive_days"] < WEEKLY_REPLAY_DAYS_REQUIRED:
            reasons.append(f"weekly replay requires {WEEKLY_REPLAY_DAYS_REQUIRED} consecutive daily entries")
    if monthly_replay:
        if coverage["unique_days"] < monthly_days_required:
            reasons.append(f"monthly replay requires at least {monthly_days_required} unique daily entries")
        if coverage["longest_consecutive_days"] < monthly_days_required:
            reasons.append(f"monthly replay requires {monthly_days_required} consecutive daily entries")

    if reasons:
        base["blocking_reasons"] = reasons
        return _with_validation(base)

    base.update(
        {
            "status": "pass",
            "replay_evidence_verified": True,
            "weekly_replay_verified": bool(weekly_replay),
            "monthly_replay_verified": bool(monthly_replay),
            "annotation_hint": {
                "weekly_replay_verified": bool(weekly_replay),
                "monthly_replay_verified": bool(monthly_replay),
                "weekly_monthly_ref": replay_ref,
            },
        }
    )
    return _with_validation(base)


def validate_trial_replay_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != TRIAL_REPLAY_MODEL_ID:
        errors.append("trial replay model_id must be adp-trial-replay-v1")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("trial replay status must be pass or blocked")
    if report.get("replay_evidence_verified") not in {True, False}:
        errors.append("trial replay report requires replay_evidence_verified boolean")
    if report.get("weekly_replay_verified") not in {True, False}:
        errors.append("trial replay report requires weekly_replay_verified boolean")
    if report.get("monthly_replay_verified") not in {True, False}:
        errors.append("trial replay report requires monthly_replay_verified boolean")
    if int(report.get("observed_day_count", -1)) < 0:
        errors.append("trial replay observed_day_count must be non-negative")
    if report.get("status") == "pass":
        if report.get("replay_evidence_verified") is not True:
            errors.append("passing trial replay report requires replay_evidence_verified true")
        if not (report.get("weekly_replay_verified") or report.get("monthly_replay_verified")):
            errors.append("passing trial replay report requires at least one verified replay mode")
        if not _ref(report.get("replay_evidence_ref")):
            errors.append("passing trial replay report requires replay_evidence_ref")
        if report.get("blocking_reasons"):
            errors.append("passing trial replay report cannot include blocking_reasons")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked trial replay report requires blocking_reasons")
    hint = report.get("annotation_hint")
    if report.get("status") == "pass":
        if not isinstance(hint, Mapping):
            errors.append("passing trial replay report requires annotation_hint")
        elif hint.get("weekly_monthly_ref") != report.get("replay_evidence_ref"):
            errors.append("annotation_hint weekly_monthly_ref must match replay_evidence_ref")
    return errors


def _valid_daily_runs(value: Any) -> tuple[list[Mapping[str, Any]], list[str]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return [], ["daily_runs must be a list"]
    reasons: list[str] = []
    valid_runs: list[Mapping[str, Any]] = []
    dates_seen: set[str] = set()
    source_ids_seen: set[str] = set()
    publication_ids_seen: set[str] = set()
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
        if not source_id:
            reasons.append(f"{prefix}.source_id is required")
        elif source_id in source_ids_seen:
            reasons.append(f"{prefix}.source_id duplicates {source_id}")
        source_ids_seen.add(source_id)
        publication_id = str(run.get("publication_id") or "")
        if not publication_id:
            reasons.append(f"{prefix}.publication_id is required")
        elif publication_id in publication_ids_seen:
            reasons.append(f"{prefix}.publication_id duplicates {publication_id}")
        publication_ids_seen.add(publication_id)
        if run.get("status") not in PASSING_RUN_STATUSES:
            reasons.append(f"{prefix}.status must be succeeded or degraded")
        if run.get("scheduled_local_time") != TARGET_LOCAL_TIME:
            reasons.append(f"{prefix}.scheduled_local_time must be {TARGET_LOCAL_TIME}")
        for key in ("p0_claims_traceable", "text_degradation_path_verified", "video_degradation_path_verified"):
            if run.get(key) is not True:
                reasons.append(f"{prefix}.{key} must be true")
        for key in ("duplicate_publication", "unsupported_claims_published", "failure_generated_misleading_content"):
            if run.get(key) is not False:
                reasons.append(f"{prefix}.{key} must be false")
        for key in ("run_record_ref", "release_ref", "email_ref", "resource_gate_ref"):
            if not _ref(run.get(key)):
                reasons.append(f"{prefix}.{key} is required")
    return valid_runs, reasons


def _coverage(runs: Sequence[Mapping[str, Any]], *, monthly_days_required: int) -> dict[str, Any]:
    parsed_dates = sorted({_parse_date(str(run.get("date") or "")) for run in runs if _valid_date(str(run.get("date") or ""))})
    parsed_dates = [item for item in parsed_dates if item is not None]
    unique_sources = {str(run.get("source_id") or "") for run in runs if str(run.get("source_id") or "")}
    unique_publications = {str(run.get("publication_id") or "") for run in runs if str(run.get("publication_id") or "")}
    date_range = {
        "start_date": parsed_dates[0].isoformat() if parsed_dates else "",
        "end_date": parsed_dates[-1].isoformat() if parsed_dates else "",
    }
    return {
        "unique_days": len(parsed_dates),
        "unique_source_ids": len(unique_sources),
        "unique_publication_ids": len(unique_publications),
        "required_weekly_days": WEEKLY_REPLAY_DAYS_REQUIRED,
        "required_monthly_days": monthly_days_required,
        "longest_consecutive_days": _longest_consecutive_days(parsed_dates),
        "date_range": date_range,
    }


def _daily_entry_refs(runs: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    refs: list[dict[str, str]] = []
    for run in runs:
        refs.append(
            {
                "date": str(run.get("date") or ""),
                "run_record_ref": str(run.get("run_record_ref") or ""),
                "release_ref": str(run.get("release_ref") or ""),
                "email_ref": str(run.get("email_ref") or ""),
                "resource_gate_ref": str(run.get("resource_gate_ref") or ""),
            }
        )
    return refs


def _longest_consecutive_days(dates: Sequence[date]) -> int:
    if not dates:
        return 0
    longest = 1
    current = 1
    for previous, item in zip(dates, dates[1:]):
        if (item - previous).days == 1:
            current += 1
        else:
            current = 1
        longest = max(longest, current)
    return longest


def _base_report(
    *,
    generated_at: str,
    trial_id: str,
    timezone: str,
    expected_days: int,
    weekly_replay: bool,
    monthly_replay: bool,
    replay_ref: str,
) -> dict[str, Any]:
    return {
        "replay_report_id": f"trial-replay:{trial_id}:{generated_at}",
        "model_id": TRIAL_REPLAY_MODEL_ID,
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "status": "blocked",
        "trial_id": trial_id,
        "timezone": timezone,
        "expected_days": expected_days,
        "requested_replay_modes": {
            "weekly": bool(weekly_replay),
            "monthly": bool(monthly_replay),
        },
        "replay_evidence_verified": False,
        "weekly_replay_verified": False,
        "monthly_replay_verified": False,
        "replay_evidence_ref": replay_ref,
        "observed_day_count": 0,
        "date_range": {"start_date": "", "end_date": ""},
        "coverage": {},
        "daily_entry_refs": [],
        "annotation_hint": {},
        "blocking_reasons": [],
    }


def _with_validation(report: Mapping[str, Any]) -> dict[str, Any]:
    normalized = dict(report)
    normalized["validation_errors"] = validate_trial_replay_report(normalized)
    return normalized


def _positive_int(value: Any, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _valid_date(value: str) -> bool:
    return _parse_date(value) is not None


def _parse_date(value: str) -> date | None:
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _ref(value: Any) -> str:
    text = str(value or "").strip()
    return text if "://" in text else ""
