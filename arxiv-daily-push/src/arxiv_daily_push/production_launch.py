"""Fail-closed production launch readiness gate."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .trial_start_workflow import build_trial_start_workflow_plan, validate_trial_start_workflow_plan


PRODUCTION_LAUNCH_MODEL_ID = "adp-production-launch-readiness-v1"
REQUIRED_LAUNCH_REF_KEYS = (
    "default_branch_ref",
    "runner_ref",
    "smtp_secret_ref",
    "release_target_ref",
    "workflow_vars_ref",
    "trial_start_workflow_ref",
)


def build_production_launch_readiness(
    path: Path | str | None = None,
    *,
    generated_at: str,
    pr_info: Mapping[str, Any],
    expected_head_sha: str = "",
    default_branch_ref: str = "",
    runner_ref: str = "",
    smtp_secret_ref: str = "",
    release_target_ref: str = "",
    workflow_vars_ref: str = "",
    trial_start_workflow_ref: str = "",
    confirm_launch: bool = False,
) -> dict[str, Any]:
    """Build a launch-readiness report without merging, dispatching, or reading secrets."""

    root = Path(path or ".").resolve()
    workflow_plan = build_trial_start_workflow_plan(root, generated_at=generated_at)
    evidence_refs = {
        "default_branch_ref": _ref(default_branch_ref),
        "runner_ref": _ref(runner_ref),
        "smtp_secret_ref": _ref(smtp_secret_ref),
        "release_target_ref": _ref(release_target_ref),
        "workflow_vars_ref": _ref(workflow_vars_ref),
        "trial_start_workflow_ref": _ref(trial_start_workflow_ref),
    }
    gates = [
        _simple_gate("launch_confirmed", bool(confirm_launch), "confirm_launch must be true before production launch"),
        _pr_metadata_gate(pr_info),
        _pr_not_draft_gate(pr_info),
        _pr_merged_gate(pr_info),
        _head_sha_gate(pr_info, expected_head_sha),
        _workflow_gate(workflow_plan),
        *[_durable_ref_gate(key, evidence_refs[key]) for key in REQUIRED_LAUNCH_REF_KEYS],
    ]
    blocking_reasons = [
        reason
        for gate in gates
        for reason in gate["blocking_reasons"]
        if gate.get("passed") is not True
    ]
    ready = not blocking_reasons
    report = {
        "launch_readiness_id": f"production-launch:arxiv-daily-push:{generated_at}",
        "model_id": PRODUCTION_LAUNCH_MODEL_ID,
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "status": "pass" if ready else "blocked",
        "production_launch_ready": ready,
        "launch_confirmation_required": True,
        "launch_confirmed": bool(confirm_launch),
        "expected_head_sha": str(expected_head_sha or ""),
        "pr_summary": _pr_summary(pr_info),
        "workflow_plan": {
            "validator_id": workflow_plan.get("validator_id"),
            "status": workflow_plan.get("status"),
            "trial_start_workflow_ready": workflow_plan.get("trial_start_workflow_ready"),
            "workflow_path": workflow_plan.get("workflow_path"),
        },
        "evidence_refs": evidence_refs,
        "readiness_gates": gates,
        "side_effects_performed": False,
        "secret_values_logged": False,
        "codex_auth_read": False,
        "production_acceptance_claimed": False,
        "blocking_reasons": blocking_reasons,
        "next_external_actions": [] if ready else _next_external_actions(gates),
    }
    return _with_validation(report)


def validate_production_launch_readiness(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != PRODUCTION_LAUNCH_MODEL_ID:
        errors.append("production launch model_id must be adp-production-launch-readiness-v1")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("production launch status must be pass or blocked")
    if report.get("production_launch_ready") not in {True, False}:
        errors.append("production launch report requires production_launch_ready boolean")
    for key in ("side_effects_performed", "secret_values_logged", "codex_auth_read", "production_acceptance_claimed"):
        if report.get(key) is not False:
            errors.append(f"production launch {key} must be false")
    refs = report.get("evidence_refs")
    if not isinstance(refs, Mapping):
        errors.append("production launch report requires evidence_refs object")
    else:
        for key in REQUIRED_LAUNCH_REF_KEYS:
            if key not in refs:
                errors.append(f"production launch evidence_refs missing {key}")
    gates = report.get("readiness_gates")
    if not isinstance(gates, list) or not gates:
        errors.append("production launch report requires readiness_gates list")
        return errors
    failed = [
        str(gate.get("gate_id"))
        for gate in gates
        if isinstance(gate, Mapping) and gate.get("passed") is not True
    ]
    if report.get("status") == "pass":
        if report.get("production_launch_ready") is not True:
            errors.append("passing production launch report requires production_launch_ready true")
        if failed:
            errors.append("passing production launch report cannot include failed gates: " + ", ".join(failed))
        if report.get("blocking_reasons"):
            errors.append("passing production launch report cannot include blocking_reasons")
        if isinstance(refs, Mapping):
            for key in REQUIRED_LAUNCH_REF_KEYS:
                if not _ref(refs.get(key)):
                    errors.append(f"passing production launch report requires durable {key}")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked production launch report requires blocking_reasons")
    return errors


def _pr_metadata_gate(pr_info: Mapping[str, Any]) -> dict[str, Any]:
    required = ("state", "merged", "draft", "base", "head_sha")
    missing = [key for key in required if key not in pr_info]
    return _gate(
        "pr_metadata_present",
        not missing,
        [f"PR metadata missing required keys: {', '.join(missing)}"] if missing else [],
    )


def _pr_not_draft_gate(pr_info: Mapping[str, Any]) -> dict[str, Any]:
    return _simple_gate("pr_not_draft", pr_info.get("draft") is False, "PR must not be draft before launch")


def _pr_merged_gate(pr_info: Mapping[str, Any]) -> dict[str, Any]:
    reasons: list[str] = []
    if pr_info.get("merged") is not True:
        reasons.append("PR must be merged before default-branch trial start workflow can run")
    if pr_info.get("base") != "main":
        reasons.append("PR base branch must be main")
    return _gate("pr_merged_to_main", not reasons, reasons)


def _head_sha_gate(pr_info: Mapping[str, Any], expected_head_sha: str) -> dict[str, Any]:
    expected = str(expected_head_sha or "").strip()
    if not expected:
        return _gate("expected_head_sha_recorded", False, ["expected_head_sha is required for launch audit"])
    observed = str(pr_info.get("head_sha") or "")
    return _simple_gate(
        "expected_head_sha_matches",
        observed == expected,
        f"PR head_sha {observed or '<missing>'} does not match expected {expected}",
    )


def _workflow_gate(workflow_plan: Mapping[str, Any]) -> dict[str, Any]:
    reasons = [f"trial start workflow plan invalid: {error}" for error in validate_trial_start_workflow_plan(workflow_plan)]
    if workflow_plan.get("trial_start_workflow_ready") is not True:
        reasons.append("trial start workflow contract must be ready before launch")
    return _gate("trial_start_workflow_ready", not reasons, reasons)


def _durable_ref_gate(key: str, value: str) -> dict[str, Any]:
    return _simple_gate(key, bool(_ref(value)), f"{key} must be a durable ref containing ://")


def _simple_gate(gate_id: str, passed: bool, reason: str) -> dict[str, Any]:
    return _gate(gate_id, passed, [] if passed else [reason])


def _gate(gate_id: str, passed: bool, reasons: list[str]) -> dict[str, Any]:
    return {"gate_id": gate_id, "passed": bool(passed), "blocking_reasons": [] if passed else reasons}


def _next_external_actions(gates: list[Mapping[str, Any]]) -> list[str]:
    action_map = {
        "launch_confirmed": "rerun with --confirm-launch only after external launch prerequisites are provisioned",
        "pr_metadata_present": "export current PR metadata from GitHub",
        "pr_not_draft": "mark PR ready for review before launch",
        "pr_merged_to_main": "merge PR to main before running the default-branch workflow",
        "expected_head_sha_recorded": "record the expected PR head SHA before launch",
        "expected_head_sha_matches": "refresh PR metadata and expected head SHA",
        "trial_start_workflow_ready": "fix the trial start workflow contract before launch",
        "default_branch_ref": "provide the merged default-branch commit ref",
        "runner_ref": "provide a durable GitHub-hosted runner readiness ref",
        "smtp_secret_ref": "provide a durable GitHub SMTP secrets readiness ref without secret values",
        "release_target_ref": "provide a durable Release target readiness ref",
        "workflow_vars_ref": "provide a durable GitHub variables readiness ref",
        "trial_start_workflow_ref": "provide a durable default-branch trial start workflow ref",
    }
    actions = []
    for gate in gates:
        if gate.get("passed") is True:
            continue
        actions.append(action_map.get(str(gate.get("gate_id")), f"resolve {gate.get('gate_id')}"))
    return actions


def _pr_summary(pr_info: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "state": pr_info.get("state"),
        "merged": pr_info.get("merged"),
        "draft": pr_info.get("draft"),
        "mergeable": pr_info.get("mergeable"),
        "base": pr_info.get("base"),
        "head": pr_info.get("head"),
        "head_sha": pr_info.get("head_sha"),
        "changed_files": pr_info.get("changed_files"),
    }


def _with_validation(report: Mapping[str, Any]) -> dict[str, Any]:
    normalized = dict(report)
    normalized["validation_errors"] = validate_production_launch_readiness(normalized)
    return normalized


def _ref(value: Any) -> str:
    text = str(value or "").strip()
    return text if "://" in text else ""
