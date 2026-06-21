"""Resource pressure evidence for Phase 11 trial runs."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .production_preflight import validate_production_preflight
from .trial import TRIAL_DAYS_REQUIRED


TRIAL_RESOURCE_MODEL_ID = "adp-trial-resource-v1"
REQUIRED_PREFLIGHT_GATES = (
    "disk_pressure",
    "memory_pressure",
    "git_artifact_hygiene",
    "local_artifact_cache",
    "secret_environment",
)


def build_trial_resource_evidence(
    trial_evidence: Mapping[str, Any],
    preflight_reports: Sequence[Mapping[str, Any]],
    *,
    generated_at: str,
    resource_ref: str = "",
) -> dict[str, Any]:
    """Build a fail-closed resource telemetry evidence report.

    The report validates that daily trial entries are backed by passing
    production preflight resource refs. It does not mutate the trial ledger or
    claim production acceptance.
    """

    evidence = dict(trial_evidence or {})
    trial_id = str(evidence.get("trial_id") or "adp-trial-current")
    period = evidence.get("period") if isinstance(evidence.get("period"), Mapping) else {}
    expected_days = max(_positive_int(period.get("expected_days"), TRIAL_DAYS_REQUIRED), TRIAL_DAYS_REQUIRED)
    base = _base_report(
        generated_at=generated_at,
        trial_id=trial_id,
        expected_days=expected_days,
        resource_ref=resource_ref,
    )
    daily_runs, daily_reasons = _daily_resource_refs(evidence.get("daily_runs"))
    preflights, preflight_reasons = _preflight_resource_refs(preflight_reports)
    base["observed_day_count"] = len({item["date"] for item in daily_runs if item.get("date")})
    base["daily_resource_refs"] = daily_runs
    base["preflight_resource_refs"] = preflights
    base["coverage"] = _coverage(daily_runs, preflights, expected_days=expected_days)

    reasons = daily_reasons + preflight_reasons
    if not _ref(resource_ref):
        reasons.append("resource_ref is required before resource evidence can be verified")
    if base["coverage"]["unique_daily_resource_refs"] < expected_days:
        reasons.append(f"resource evidence requires at least {expected_days} unique daily resource refs")
    if base["coverage"]["matched_daily_resource_refs"] < expected_days:
        reasons.append(f"resource evidence requires at least {expected_days} daily refs matched by preflight reports")
    missing_refs = sorted(base["coverage"]["unmatched_daily_resource_refs"])
    if missing_refs:
        reasons.append("daily resource refs missing matching preflight reports: " + ", ".join(missing_refs[:5]))

    if reasons:
        base["blocking_reasons"] = reasons
        return _with_validation(base)

    base.update(
        {
            "status": "pass",
            "resource_pressure_verified": True,
            "annotation_hint": {
                "resource_pressure_ok": True,
                "resource_ref": resource_ref,
            },
        }
    )
    return _with_validation(base)


def validate_trial_resource_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != TRIAL_RESOURCE_MODEL_ID:
        errors.append("trial resource model_id must be adp-trial-resource-v1")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("trial resource status must be pass or blocked")
    if report.get("resource_pressure_verified") not in {True, False}:
        errors.append("trial resource report requires resource_pressure_verified boolean")
    if int(report.get("observed_day_count", -1)) < 0:
        errors.append("trial resource observed_day_count must be non-negative")
    if not isinstance(report.get("daily_resource_refs"), list):
        errors.append("trial resource report requires daily_resource_refs list")
    if not isinstance(report.get("preflight_resource_refs"), list):
        errors.append("trial resource report requires preflight_resource_refs list")
    if not isinstance(report.get("coverage"), Mapping):
        errors.append("trial resource report requires coverage")
    if report.get("status") == "pass":
        if report.get("resource_pressure_verified") is not True:
            errors.append("passing trial resource report requires resource_pressure_verified true")
        if report.get("blocking_reasons"):
            errors.append("passing trial resource report cannot include blocking_reasons")
        if not _ref(report.get("resource_evidence_ref")):
            errors.append("passing trial resource report requires resource_evidence_ref")
        hint = report.get("annotation_hint")
        if not isinstance(hint, Mapping):
            errors.append("passing trial resource report requires annotation_hint")
        elif hint.get("resource_ref") != report.get("resource_evidence_ref"):
            errors.append("annotation_hint resource_ref must match resource_evidence_ref")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked trial resource report requires blocking_reasons")
    return errors


def _daily_resource_refs(value: Any) -> tuple[list[dict[str, str]], list[str]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return [], ["daily_runs must be a list"]
    refs: list[dict[str, str]] = []
    reasons: list[str] = []
    dates_seen: set[str] = set()
    resource_refs_seen: set[str] = set()
    for index, run in enumerate(value):
        prefix = f"daily_runs[{index}]"
        if not isinstance(run, Mapping):
            reasons.append(f"{prefix} must be an object")
            continue
        run_date = str(run.get("date") or "")
        resource_ref = _ref(run.get("resource_gate_ref"))
        if not run_date:
            reasons.append(f"{prefix}.date is required")
        elif run_date in dates_seen:
            reasons.append(f"{prefix}.date duplicates {run_date}")
        dates_seen.add(run_date)
        if not resource_ref:
            reasons.append(f"{prefix}.resource_gate_ref is required")
        elif resource_ref in resource_refs_seen:
            reasons.append(f"{prefix}.resource_gate_ref duplicates {resource_ref}")
        resource_refs_seen.add(resource_ref)
        refs.append(
            {
                "date": run_date,
                "run_id": str(run.get("run_id") or ""),
                "resource_gate_ref": resource_ref,
            }
        )
    return refs, reasons


def _preflight_resource_refs(reports: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    reasons: list[str] = []
    refs: list[dict[str, Any]] = []
    if not isinstance(reports, Sequence) or isinstance(reports, (str, bytes)):
        return [], ["preflight_reports must be a list"]
    for index, report in enumerate(reports):
        prefix = f"preflight_reports[{index}]"
        if not isinstance(report, Mapping):
            reasons.append(f"{prefix} must be an object")
            continue
        errors = validate_production_preflight(report)
        if errors:
            reasons.append(f"{prefix} invalid: {errors[0]}")
        if report.get("status") != "pass" or report.get("production_run_allowed") is not True:
            reasons.append(f"{prefix} must be a passing production preflight report")
        gates = report.get("gates") if isinstance(report.get("gates"), list) else []
        gate_map = {str(gate.get("gate_id")): gate for gate in gates if isinstance(gate, Mapping)}
        for gate_id in REQUIRED_PREFLIGHT_GATES:
            gate = gate_map.get(gate_id)
            if not isinstance(gate, Mapping) or gate.get("passed") is not True:
                reasons.append(f"{prefix}.{gate_id} must pass")
        resource = report.get("resource_evidence") if isinstance(report.get("resource_evidence"), Mapping) else {}
        resource_ref = _ref(resource.get("resource_pressure_ok_ref"))
        if resource.get("resource_pressure_ok") is not True:
            reasons.append(f"{prefix}.resource_evidence.resource_pressure_ok must be true")
        if not resource_ref:
            reasons.append(f"{prefix}.resource_evidence.resource_pressure_ok_ref is required")
        refs.append(
            {
                "preflight_id": str(report.get("preflight_id") or ""),
                "generated_at": str(report.get("generated_at") or ""),
                "resource_pressure_ok_ref": resource_ref,
                "passed_gates": sorted(gate_id for gate_id, gate in gate_map.items() if gate.get("passed") is True),
            }
        )
    return refs, reasons


def _coverage(
    daily_refs: Sequence[Mapping[str, str]],
    preflight_refs: Sequence[Mapping[str, Any]],
    *,
    expected_days: int,
) -> dict[str, Any]:
    daily_resource_refs = {str(item.get("resource_gate_ref") or "") for item in daily_refs if item.get("resource_gate_ref")}
    preflight_resource_refs = {
        str(item.get("resource_pressure_ok_ref") or "") for item in preflight_refs if item.get("resource_pressure_ok_ref")
    }
    matched = daily_resource_refs & preflight_resource_refs
    return {
        "required_days": expected_days,
        "unique_daily_resource_refs": len(daily_resource_refs),
        "unique_preflight_resource_refs": len(preflight_resource_refs),
        "matched_daily_resource_refs": len(matched),
        "unmatched_daily_resource_refs": sorted(daily_resource_refs - preflight_resource_refs),
    }


def _base_report(*, generated_at: str, trial_id: str, expected_days: int, resource_ref: str) -> dict[str, Any]:
    return {
        "resource_report_id": f"trial-resource:{trial_id}:{generated_at}",
        "model_id": TRIAL_RESOURCE_MODEL_ID,
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "status": "blocked",
        "trial_id": trial_id,
        "expected_days": expected_days,
        "resource_pressure_verified": False,
        "resource_evidence_ref": resource_ref,
        "observed_day_count": 0,
        "daily_resource_refs": [],
        "preflight_resource_refs": [],
        "coverage": {},
        "annotation_hint": {},
        "blocking_reasons": [],
    }


def _with_validation(report: Mapping[str, Any]) -> dict[str, Any]:
    normalized = dict(report)
    normalized["validation_errors"] = validate_trial_resource_report(normalized)
    return normalized


def _positive_int(value: Any, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _ref(value: Any) -> str:
    text = str(value or "").strip()
    return text if "://" in text else ""
