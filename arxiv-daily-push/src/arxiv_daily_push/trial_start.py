"""Fail-closed start gate for the real Phase 11 production trial."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .config import DEFAULT_RECIPIENT
from .production_preflight import validate_production_preflight
from .production_scheduler import validate_production_scheduler_plan
from .release_delivery import validate_release_delivery_report
from .smtp_delivery import validate_smtp_delivery_report
from .source_ingest import validate_source_batch
from .trial_bootstrap import validate_trial_bootstrap_plan


TRIAL_START_MODEL_ID = "adp-trial-start-v1"
REQUIRED_START_REF_KEYS = (
    "default_branch_ref",
    "runner_ref",
    "preflight_ref",
    "source_ingest_ref",
    "smtp_ref",
    "release_ref",
    "scheduler_ref",
    "trial_state_ref",
    "trial_start_ref",
)


def build_trial_start_gate(
    *,
    generated_at: str,
    preflight_report: Mapping[str, Any],
    bootstrap_plan: Mapping[str, Any],
    scheduler_plan: Mapping[str, Any],
    source_batch: Mapping[str, Any],
    smtp_delivery_report: Mapping[str, Any],
    release_delivery_report: Mapping[str, Any],
    default_branch_ref: str = "",
    runner_ref: str = "",
    preflight_ref: str = "",
    source_ingest_ref: str = "",
    smtp_ref: str = "",
    release_ref: str = "",
    scheduler_ref: str = "",
    trial_state_ref: str = "",
    trial_start_ref: str = "",
    confirm_start: bool = False,
) -> dict[str, Any]:
    """Build a start-readiness report without performing side effects."""

    evidence_refs = {
        "default_branch_ref": _ref(default_branch_ref),
        "runner_ref": _ref(runner_ref),
        "preflight_ref": _ref(preflight_ref),
        "source_ingest_ref": _ref(source_ingest_ref),
        "smtp_ref": _ref(smtp_ref),
        "release_ref": _ref(release_ref),
        "scheduler_ref": _ref(scheduler_ref),
        "trial_state_ref": _ref(trial_state_ref),
        "trial_start_ref": _ref(trial_start_ref),
    }
    readiness_gates = [
        _simple_gate("start_confirmed", bool(confirm_start), "confirm_start must be true before the real trial can start"),
        _durable_ref_gate("default_branch_ref", evidence_refs["default_branch_ref"]),
        _durable_ref_gate("runner_ref", evidence_refs["runner_ref"]),
        _durable_ref_gate("preflight_ref", evidence_refs["preflight_ref"]),
        _durable_ref_gate("source_ingest_ref", evidence_refs["source_ingest_ref"]),
        _durable_ref_gate("smtp_ref", evidence_refs["smtp_ref"]),
        _durable_ref_gate("release_ref", evidence_refs["release_ref"]),
        _durable_ref_gate("scheduler_ref", evidence_refs["scheduler_ref"]),
        _durable_ref_gate("trial_state_ref", evidence_refs["trial_state_ref"]),
        _durable_ref_gate("trial_start_ref", evidence_refs["trial_start_ref"]),
        _preflight_gate(preflight_report),
        _bootstrap_gate(bootstrap_plan),
        _scheduler_gate(scheduler_plan),
        _source_ingest_gate(source_batch),
        _smtp_gate(smtp_delivery_report, evidence_refs["smtp_ref"]),
        _release_gate(release_delivery_report, evidence_refs["release_ref"]),
    ]
    blocking_reasons = [
        reason
        for gate in readiness_gates
        for reason in gate["blocking_reasons"]
        if gate.get("passed") is not True
    ]
    ready = not blocking_reasons
    report = {
        "trial_start_report_id": f"trial-start:arxiv-daily-push:{generated_at}",
        "model_id": TRIAL_START_MODEL_ID,
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "status": "pass" if ready else "blocked",
        "trial_start_ready": ready,
        "notification_recipient": DEFAULT_RECIPIENT,
        "start_confirmation_required": True,
        "start_confirmed": bool(confirm_start),
        "evidence_refs": evidence_refs,
        "readiness_gates": readiness_gates,
        "side_effects_performed": False,
        "production_acceptance_claimed": False,
        "blocking_reasons": blocking_reasons,
        "next_external_actions": [] if ready else _next_external_actions(readiness_gates),
    }
    return _with_validation(report)


def validate_trial_start_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != TRIAL_START_MODEL_ID:
        errors.append("trial start model_id must be adp-trial-start-v1")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("trial start status must be pass or blocked")
    if report.get("trial_start_ready") not in {True, False}:
        errors.append("trial start report requires trial_start_ready boolean")
    if report.get("notification_recipient") != DEFAULT_RECIPIENT:
        errors.append(f"trial start notification_recipient must be {DEFAULT_RECIPIENT}")
    if report.get("side_effects_performed") is not False:
        errors.append("trial start gate must not perform side effects")
    if report.get("production_acceptance_claimed") is not False:
        errors.append("trial start gate must not claim production acceptance")
    refs = report.get("evidence_refs")
    if not isinstance(refs, Mapping):
        errors.append("trial start report requires evidence_refs object")
    else:
        for key in REQUIRED_START_REF_KEYS:
            if key not in refs:
                errors.append(f"trial start evidence_refs missing {key}")
    gates = report.get("readiness_gates")
    if not isinstance(gates, list) or not gates:
        errors.append("trial start report requires readiness_gates list")
        return errors
    failed = [
        str(gate.get("gate_id"))
        for gate in gates
        if isinstance(gate, Mapping) and gate.get("passed") is not True
    ]
    if report.get("status") == "pass":
        if report.get("trial_start_ready") is not True:
            errors.append("passing trial start report requires trial_start_ready true")
        if failed:
            errors.append("passing trial start report cannot include failed gates: " + ", ".join(failed))
        if report.get("blocking_reasons"):
            errors.append("passing trial start report cannot include blocking_reasons")
        if isinstance(refs, Mapping):
            for key in REQUIRED_START_REF_KEYS:
                if not _ref(refs.get(key)):
                    errors.append(f"passing trial start report requires durable {key}")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked trial start report requires blocking_reasons")
    return errors


def _preflight_gate(report: Mapping[str, Any]) -> dict[str, Any]:
    reasons = [f"preflight invalid: {error}" for error in validate_production_preflight(report)]
    if report.get("status") != "pass" or report.get("production_run_allowed") is not True:
        reasons.append("production preflight must pass before trial start")
    resource = report.get("resource_evidence") if isinstance(report.get("resource_evidence"), Mapping) else {}
    if resource.get("resource_pressure_ok") is not True:
        reasons.append("production preflight resource evidence must be passing")
    return _gate("production_preflight_passed", not reasons, reasons)


def _bootstrap_gate(plan: Mapping[str, Any]) -> dict[str, Any]:
    reasons = [f"bootstrap plan invalid: {error}" for error in validate_trial_bootstrap_plan(plan)]
    if plan.get("trial_bootstrap_ready") is not True:
        reasons.append("trial bootstrap plan must be ready")
    return _gate("trial_bootstrap_ready", not reasons, reasons)


def _scheduler_gate(plan: Mapping[str, Any]) -> dict[str, Any]:
    reasons = [f"scheduler plan invalid: {error}" for error in validate_production_scheduler_plan(plan)]
    if plan.get("scheduler_contract_ready") is not True:
        reasons.append("production scheduler contract must be ready")
    return _gate("production_scheduler_ready", not reasons, reasons)


def _source_ingest_gate(batch: Mapping[str, Any]) -> dict[str, Any]:
    reasons = [f"source batch invalid: {error}" for error in validate_source_batch(batch)]
    if batch.get("status") != "pass":
        reasons.append("live arXiv source ingest must pass on the runner")
    policy = batch.get("source_policy") if isinstance(batch.get("source_policy"), Mapping) else {}
    if policy.get("pdf_download_enabled") is not False:
        reasons.append("source ingest must not download PDFs")
    if policy.get("bulk_harvest_enabled") is not False:
        reasons.append("source ingest must not perform bulk harvesting")
    if int(batch.get("new_item_count") or 0) < 1:
        reasons.append("source ingest must return at least one unseen item before trial start")
    return _gate("live_source_ingest_passed", not reasons, reasons)


def _smtp_gate(report: Mapping[str, Any], expected_ref: str) -> dict[str, Any]:
    reasons = [f"smtp delivery invalid: {error}" for error in validate_smtp_delivery_report(report)]
    if report.get("status") != "sent":
        reasons.append("SMTP delivery probe must be a real sent report")
    if report.get("real_smtp_send_enabled") is not True:
        reasons.append("SMTP delivery probe must have real_smtp_send_enabled true")
    if _ref(report.get("delivery_ref")) != expected_ref:
        reasons.append("smtp_ref must match the SMTP delivery report delivery_ref")
    return _gate("real_smtp_delivery_verified", not reasons, reasons)


def _release_gate(report: Mapping[str, Any], expected_ref: str) -> dict[str, Any]:
    reasons = [f"release delivery invalid: {error}" for error in validate_release_delivery_report(report)]
    if report.get("status") != "created":
        reasons.append("Release delivery probe must be a real created report")
    if report.get("release_upload_enabled") is not True:
        reasons.append("Release delivery probe must have release_upload_enabled true")
    if _ref(report.get("release_ref")) != expected_ref:
        reasons.append("release_ref must match the Release delivery report release_ref")
    return _gate("private_release_verified", not reasons, reasons)


def _durable_ref_gate(key: str, value: str) -> dict[str, Any]:
    return _simple_gate(key, bool(_ref(value)), f"{key} must be a durable ref containing ://")


def _simple_gate(gate_id: str, passed: bool, reason: str) -> dict[str, Any]:
    return _gate(gate_id, passed, [] if passed else [reason])


def _gate(gate_id: str, passed: bool, reasons: list[str]) -> dict[str, Any]:
    return {
        "gate_id": gate_id,
        "passed": bool(passed),
        "blocking_reasons": [] if passed else reasons,
    }


def _next_external_actions(gates: list[Mapping[str, Any]]) -> list[str]:
    return [
        f"resolve {gate['gate_id']}"
        for gate in gates
        if gate.get("passed") is not True
    ]


def _with_validation(report: Mapping[str, Any]) -> dict[str, Any]:
    normalized = dict(report)
    normalized["validation_errors"] = validate_trial_start_report(normalized)
    return normalized


def _ref(value: Any) -> str:
    text = str(value or "").strip()
    return text if "://" in text else ""
