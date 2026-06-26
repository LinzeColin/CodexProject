"""S2PLT01 fail-closed replay entry precheck helpers."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any


S2PLT01_ENTRY_PRECHECK_MODEL_ID = "adp-s2plt01-entry-precheck-v1"
S2PLT01_ACCEPTANCE_ID = "ACC-S2PLT01-30D"
S2PLT01_TASK_ID = "S2PLT01"
S2PLT01_SCHEMA_VERSION = 1
S2PLT01_INHERITED_V7_1_OPEN_P0_FINDINGS = 8
S2PLT01_INHERITED_V7_1_OPEN_P1_FINDINGS = 37
S2PLT01_REQUIRED_DEPENDENCIES = (
    "S2PBT05",
    "S2PCT07",
    "S2PDT04",
    "S2PET04",
    "S2PFT05",
    "S2PKT05",
)
S2PLT01_COMPLETED_DEPENDENCIES = (
    "S2PCT07",
    "S2PDT04",
    "S2PET04",
    "S2PFT05",
    "S2PKT05",
)
S2PLT01_REQUIRED_REPLAY_DAYS = 30
S2PLT01_REQUIRED_MAIL_PREVIEWS = 120
S2PLT01_REQUIRED_SOURCE_DOMAINS = ("D1", "D2", "D3", "D4")
S2PLT01_REQUIRED_READING_BOARDS = ("B1", "B2", "B3", "B4", "B5", "B6")
S2PLT01_REQUIRED_OUTPUTS = (
    "daily_replay_reports",
    "mail_previews",
    "source_terminal_states",
    "ledger",
    "future_leakage_check",
    "p0_p1_zero_evidence",
)
S2PLT01_FORBIDDEN_FLAGS = (
    "full_replay_executed",
    "s2plt01_accepted",
    "s2plt04_completed",
    "integrated_production_accepted",
    "daily_operation_enabled",
    "real_smtp_sent",
    "scheduler_enabled",
    "release_uploaded",
    "production_queue_mutated",
    "public_schema_changed",
    "db_migration_executed",
    "current_pointer_changed",
    "v7_1_baseline_changed",
    "v7_2_contract_files_changed",
)
S2PLT01_BLOCKING_REASONS = (
    "s2pbt05_missing",
    "inherited_v7_1_p0_findings_open",
    "inherited_v7_1_p1_findings_open",
    "full_30_day_replay_not_executed",
    "mail_preview_count_not_proven",
    "source_terminal_states_not_proven",
)


def build_s2plt01_dependency_state() -> dict[str, Any]:
    """Build current S2PLT01 dependency state from governance-level facts."""

    completed = {task_id: "completed_governance_evidence" for task_id in S2PLT01_COMPLETED_DEPENDENCIES}
    missing = [task_id for task_id in S2PLT01_REQUIRED_DEPENDENCIES if task_id not in completed]
    return {
        "status": "pass" if not missing else "blocked",
        "required_dependencies": list(S2PLT01_REQUIRED_DEPENDENCIES),
        "completed_dependencies": completed,
        "missing_dependencies": missing,
    }


def build_s2plt01_audit_blocker_state(
    *,
    inherited_p0: int = S2PLT01_INHERITED_V7_1_OPEN_P0_FINDINGS,
    inherited_p1: int = S2PLT01_INHERITED_V7_1_OPEN_P1_FINDINGS,
) -> dict[str, Any]:
    """Build inherited V7.1 blocker state for S2PLT01 replay entry."""

    checks = {
        "P0_zero": inherited_p0 == 0,
        "P1_zero": inherited_p1 == 0,
    }
    return {
        "status": "pass" if all(checks.values()) else "blocked",
        "inherited_v7_1_open_p0_findings": inherited_p0,
        "inherited_v7_1_open_p1_findings": inherited_p1,
        "checks": checks,
    }


def build_s2plt01_replay_evidence_state() -> dict[str, Any]:
    """Build the required full-system replay evidence state without executing replay."""

    available_outputs = {name: False for name in S2PLT01_REQUIRED_OUTPUTS}
    return {
        "status": "blocked",
        "required_replay_days": S2PLT01_REQUIRED_REPLAY_DAYS,
        "observed_replay_days": 0,
        "required_mail_previews": S2PLT01_REQUIRED_MAIL_PREVIEWS,
        "observed_mail_previews": 0,
        "required_source_domains": list(S2PLT01_REQUIRED_SOURCE_DOMAINS),
        "required_reading_boards": list(S2PLT01_REQUIRED_READING_BOARDS),
        "required_outputs": list(S2PLT01_REQUIRED_OUTPUTS),
        "available_outputs": available_outputs,
        "future_leakage_count": None,
        "source_terminal_states_proven": False,
    }


def build_s2plt01_entry_precheck_report(*, generated_at: str) -> dict[str, Any]:
    """Build a deterministic fail-closed S2PLT01 entry precheck report."""

    dependencies = build_s2plt01_dependency_state()
    audit = build_s2plt01_audit_blocker_state()
    replay = build_s2plt01_replay_evidence_state()
    gates = {
        "dependencies_complete": dependencies["status"] == "pass",
        "p0_zero": audit["checks"]["P0_zero"],
        "p1_zero": audit["checks"]["P1_zero"],
        "thirty_independent_days_proven": replay["observed_replay_days"] >= S2PLT01_REQUIRED_REPLAY_DAYS,
        "mail_previews_proven": replay["observed_mail_previews"] >= S2PLT01_REQUIRED_MAIL_PREVIEWS,
        "source_terminal_states_proven": replay["source_terminal_states_proven"],
        "future_leakage_zero": replay["future_leakage_count"] == 0,
        "no_production_side_effect": True,
    }
    blocking_reasons: list[str] = []
    if "S2PBT05" in dependencies["missing_dependencies"]:
        blocking_reasons.append("s2pbt05_missing")
    if not gates["p0_zero"]:
        blocking_reasons.append("inherited_v7_1_p0_findings_open")
    if not gates["p1_zero"]:
        blocking_reasons.append("inherited_v7_1_p1_findings_open")
    if not gates["thirty_independent_days_proven"]:
        blocking_reasons.append("full_30_day_replay_not_executed")
    if not gates["mail_previews_proven"]:
        blocking_reasons.append("mail_preview_count_not_proven")
    if not gates["source_terminal_states_proven"]:
        blocking_reasons.append("source_terminal_states_not_proven")

    report = {
        "model_id": S2PLT01_ENTRY_PRECHECK_MODEL_ID,
        "schema_version": S2PLT01_SCHEMA_VERSION,
        "task_id": S2PLT01_TASK_ID,
        "acceptance_id": S2PLT01_ACCEPTANCE_ID,
        "generated_at": generated_at,
        "status": "pass" if not blocking_reasons and all(gates.values()) else "blocked",
        "scope": "fail_closed_entry_precheck_only",
        "blocking_reasons": blocking_reasons,
        "gates": gates,
        "dependencies": dependencies,
        "audit_blockers": audit,
        "replay_evidence": replay,
        "production_acceptance_claimed": False,
        "report_hash": "",
        **{flag: False for flag in S2PLT01_FORBIDDEN_FLAGS},
    }
    report["report_hash"] = _stable_hash({key: value for key, value in report.items() if key != "report_hash"})
    return report


def validate_s2plt01_entry_precheck_report(report: Mapping[str, Any]) -> list[str]:
    """Validate S2PLT01 fail-closed entry precheck reports."""

    errors: list[str] = []
    if report.get("model_id") != S2PLT01_ENTRY_PRECHECK_MODEL_ID:
        errors.append("S2PLT01 report model_id is invalid")
    if report.get("schema_version") != S2PLT01_SCHEMA_VERSION:
        errors.append("S2PLT01 report schema_version must be 1")
    if report.get("task_id") != S2PLT01_TASK_ID:
        errors.append("S2PLT01 report task_id is invalid")
    if report.get("acceptance_id") != S2PLT01_ACCEPTANCE_ID:
        errors.append("S2PLT01 report acceptance_id is invalid")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("S2PLT01 report status must be pass or blocked")
    if report.get("production_acceptance_claimed") is not False:
        errors.append("S2PLT01 precheck must not claim production acceptance")
    for flag in S2PLT01_FORBIDDEN_FLAGS:
        if report.get(flag) is not False:
            errors.append(f"{flag} must be false")
    dependencies = _mapping(report.get("dependencies"))
    for task_id in S2PLT01_REQUIRED_DEPENDENCIES:
        if task_id not in dependencies.get("required_dependencies", []):
            errors.append(f"dependencies.required_dependencies must include {task_id}")
    replay = _mapping(report.get("replay_evidence"))
    if replay.get("required_replay_days") != S2PLT01_REQUIRED_REPLAY_DAYS:
        errors.append("replay_evidence.required_replay_days must be 30")
    if replay.get("required_mail_previews") != S2PLT01_REQUIRED_MAIL_PREVIEWS:
        errors.append("replay_evidence.required_mail_previews must be 120")
    if report.get("status") == "pass":
        gates = _mapping(report.get("gates"))
        if not all(gates.values()):
            errors.append("passing S2PLT01 precheck requires every gate true")
        if report.get("blocking_reasons"):
            errors.append("passing S2PLT01 precheck must not have blocking reasons")
    else:
        for reason in S2PLT01_BLOCKING_REASONS:
            if reason not in report.get("blocking_reasons", []):
                errors.append(f"blocked S2PLT01 precheck must include {reason}")
    return errors


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _stable_hash(value: Mapping[str, Any]) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
