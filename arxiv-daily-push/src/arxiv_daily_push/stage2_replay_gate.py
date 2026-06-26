"""S2PLT01 fail-closed replay entry precheck helpers."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from datetime import date
from typing import Any


S2PLT01_ENTRY_PRECHECK_MODEL_ID = "adp-s2plt01-entry-precheck-v1"
S2PLT01_REPLAY_PAYLOAD_CONTRACT_ID = "adp-s2plt01-replay-payload-v1"
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
    "S2PBT05",
    "S2PCT07",
    "S2PDT04",
    "S2PET04",
    "S2PFT05",
    "S2PKT05",
)
S2PLT01_REQUIRED_REPLAY_DAYS = 30
S2PLT01_REQUIRED_MAIL_PREVIEWS = 120
S2PLT01_REQUIRED_MAIL_PRODUCTS = ("M1", "M2", "M3", "M4")
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


def build_s2plt01_replay_evidence_from_records(
    *,
    replay_records: list[Mapping[str, Any]],
    mail_preview_records: list[Mapping[str, Any]],
    source_terminal_states: list[Mapping[str, Any]],
) -> dict[str, Any]:
    """Validate provided full-system replay evidence without creating production side effects."""

    replay_dates = sorted(
        {
            str(record.get("as_of_date") or "")
            for record in replay_records
            if _replay_record_passes(record)
        }
    )
    replay_domains = sorted(
        {
            str(domain)
            for record in replay_records
            if _replay_record_passes(record)
            for domain in record.get("source_domains", [])
        }
    )
    replay_boards = sorted(
        {
            str(board)
            for record in replay_records
            if _replay_record_passes(record)
            for board in record.get("reading_boards", [])
        }
    )
    mail_preview_keys = {
        (str(record.get("as_of_date") or ""), str(record.get("mail_product_id") or ""))
        for record in mail_preview_records
        if _mail_preview_record_passes(record)
    }
    terminal_domains = {
        str(record.get("source_domain") or "")
        for record in source_terminal_states
        if _terminal_source_record_passes(record)
    }
    future_leakage_count = sum(int(record.get("future_leakage_count") or 0) for record in replay_records if isinstance(record, Mapping))
    p0_p1_blocker_count = sum(int(record.get("p0_p1_blocker_count") or 0) for record in replay_records if isinstance(record, Mapping))
    missing_mail_keys = [
        f"{date}:{product_id}"
        for date in replay_dates
        for product_id in S2PLT01_REQUIRED_MAIL_PRODUCTS
        if (date, product_id) not in mail_preview_keys
    ]
    missing_domains = [domain for domain in S2PLT01_REQUIRED_SOURCE_DOMAINS if domain not in terminal_domains]
    blocking_reasons: list[str] = []
    if len(replay_dates) < S2PLT01_REQUIRED_REPLAY_DAYS:
        blocking_reasons.append("full_30_day_replay_not_executed")
    if not set(S2PLT01_REQUIRED_SOURCE_DOMAINS).issubset(replay_domains):
        blocking_reasons.append("source_domain_coverage_not_proven")
    if not set(S2PLT01_REQUIRED_READING_BOARDS).issubset(replay_boards):
        blocking_reasons.append("reading_board_coverage_not_proven")
    if len(mail_preview_keys) < S2PLT01_REQUIRED_MAIL_PREVIEWS or missing_mail_keys:
        blocking_reasons.append("mail_preview_count_not_proven")
    if missing_domains:
        blocking_reasons.append("source_terminal_states_not_proven")
    if future_leakage_count != 0:
        blocking_reasons.append("future_leakage_not_zero")
    if p0_p1_blocker_count != 0:
        blocking_reasons.append("replay_p0_p1_blockers_not_zero")
    available_outputs = {
        "daily_replay_reports": len(replay_dates) >= S2PLT01_REQUIRED_REPLAY_DAYS,
        "mail_previews": len(mail_preview_keys) >= S2PLT01_REQUIRED_MAIL_PREVIEWS and not missing_mail_keys,
        "source_terminal_states": not missing_domains,
        "ledger": all(_has_evidence_refs(record) for record in replay_records),
        "future_leakage_check": future_leakage_count == 0,
        "p0_p1_zero_evidence": p0_p1_blocker_count == 0,
    }
    return {
        "status": "pass" if not blocking_reasons and all(available_outputs.values()) else "blocked",
        "required_replay_days": S2PLT01_REQUIRED_REPLAY_DAYS,
        "observed_replay_days": len(replay_dates),
        "replay_dates_observed": replay_dates,
        "required_mail_previews": S2PLT01_REQUIRED_MAIL_PREVIEWS,
        "observed_mail_previews": len(mail_preview_keys),
        "required_mail_products": list(S2PLT01_REQUIRED_MAIL_PRODUCTS),
        "missing_mail_preview_keys": missing_mail_keys,
        "required_source_domains": list(S2PLT01_REQUIRED_SOURCE_DOMAINS),
        "source_domains_observed": replay_domains,
        "required_reading_boards": list(S2PLT01_REQUIRED_READING_BOARDS),
        "reading_boards_observed": replay_boards,
        "required_outputs": list(S2PLT01_REQUIRED_OUTPUTS),
        "available_outputs": available_outputs,
        "future_leakage_count": future_leakage_count,
        "p0_p1_blocker_count": p0_p1_blocker_count,
        "source_terminal_states_proven": not missing_domains,
        "missing_source_domains": missing_domains,
        "blocking_reasons": blocking_reasons,
    }


def build_s2plt01_replay_payload(
    *,
    payload_id: str,
    generated_at: str,
    generated_by: str,
    evidence_mode: str,
    replay_records: list[Mapping[str, Any]],
    mail_preview_records: list[Mapping[str, Any]],
    source_terminal_states: list[Mapping[str, Any]],
    evidence_refs: list[str],
) -> dict[str, Any]:
    """Build a no-production S2PLT01 replay payload envelope from explicit evidence records."""

    validation_errors = _validate_s2plt01_replay_payload_inputs(
        payload_id=payload_id,
        generated_at=generated_at,
        generated_by=generated_by,
        evidence_mode=evidence_mode,
        replay_records=replay_records,
        mail_preview_records=mail_preview_records,
        source_terminal_states=source_terminal_states,
        evidence_refs=evidence_refs,
    )
    replay_evidence = build_s2plt01_replay_evidence_from_records(
        replay_records=replay_records,
        mail_preview_records=mail_preview_records,
        source_terminal_states=source_terminal_states,
    )
    status = "pass" if not validation_errors and replay_evidence["status"] == "pass" else "blocked"
    payload = {
        "contract_id": S2PLT01_REPLAY_PAYLOAD_CONTRACT_ID,
        "schema_version": S2PLT01_SCHEMA_VERSION,
        "task_id": S2PLT01_TASK_ID,
        "acceptance_id": S2PLT01_ACCEPTANCE_ID,
        "payload_id": payload_id,
        "generated_at": generated_at,
        "generated_by": generated_by,
        "evidence_mode": evidence_mode,
        "status": status,
        "scope": "no_production_replay_payload_contract",
        "validation_errors": validation_errors,
        "replay_evidence": replay_evidence,
        "evidence_refs": list(evidence_refs),
        "payload_hash": "",
        **{flag: False for flag in S2PLT01_FORBIDDEN_FLAGS},
    }
    payload["payload_hash"] = _stable_hash({key: value for key, value in payload.items() if key != "payload_hash"})
    return payload


def validate_s2plt01_replay_payload(payload: Mapping[str, Any]) -> list[str]:
    """Validate an S2PLT01 no-production replay payload envelope."""

    errors: list[str] = []
    if payload.get("contract_id") != S2PLT01_REPLAY_PAYLOAD_CONTRACT_ID:
        errors.append("S2PLT01 replay payload contract_id is invalid")
    if payload.get("schema_version") != S2PLT01_SCHEMA_VERSION:
        errors.append("S2PLT01 replay payload schema_version must be 1")
    if payload.get("task_id") != S2PLT01_TASK_ID:
        errors.append("S2PLT01 replay payload task_id is invalid")
    if payload.get("acceptance_id") != S2PLT01_ACCEPTANCE_ID:
        errors.append("S2PLT01 replay payload acceptance_id is invalid")
    if not str(payload.get("payload_id") or "").strip():
        errors.append("S2PLT01 replay payload_id is required")
    if not str(payload.get("generated_at") or "").strip():
        errors.append("S2PLT01 replay payload generated_at is required")
    if not str(payload.get("generated_by") or "").strip():
        errors.append("S2PLT01 replay payload generated_by is required")
    if payload.get("evidence_mode") not in {"actual_replay_evidence", "fixture_replay_contract"}:
        errors.append("S2PLT01 replay payload evidence_mode is invalid")
    if payload.get("status") not in {"pass", "blocked"}:
        errors.append("S2PLT01 replay payload status must be pass or blocked")
    if not _has_evidence_refs(payload):
        errors.append("S2PLT01 replay payload evidence_refs are required")
    for flag in S2PLT01_FORBIDDEN_FLAGS:
        if payload.get(flag) is not False:
            errors.append(f"{flag} must be false")
    replay = _mapping(payload.get("replay_evidence"))
    if replay.get("required_replay_days") != S2PLT01_REQUIRED_REPLAY_DAYS:
        errors.append("S2PLT01 replay payload must require 30 replay days")
    if replay.get("required_mail_previews") != S2PLT01_REQUIRED_MAIL_PREVIEWS:
        errors.append("S2PLT01 replay payload must require 120 mail previews")
    expected_hash = _stable_hash({key: value for key, value in payload.items() if key != "payload_hash"})
    if payload.get("payload_hash") != expected_hash:
        errors.append("S2PLT01 replay payload_hash does not match payload content")
    if payload.get("status") == "pass" and replay.get("status") != "pass":
        errors.append("passing S2PLT01 replay payload requires passing replay evidence")
    if payload.get("status") == "blocked" and not (payload.get("validation_errors") or replay.get("blocking_reasons")):
        errors.append("blocked S2PLT01 replay payload must include validation errors or replay blocking reasons")
    return errors


def build_s2plt01_entry_precheck_report(
    *,
    generated_at: str,
    replay_evidence: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a deterministic fail-closed S2PLT01 entry precheck report."""

    dependencies = build_s2plt01_dependency_state()
    audit = build_s2plt01_audit_blocker_state()
    replay = dict(replay_evidence) if isinstance(replay_evidence, Mapping) else build_s2plt01_replay_evidence_state()
    gates = {
        "dependencies_complete": dependencies["status"] == "pass",
        "p0_zero": audit["checks"]["P0_zero"],
        "p1_zero": audit["checks"]["P1_zero"],
        "replay_evidence_passed": replay["status"] == "pass",
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
    if (
        not gates["replay_evidence_passed"]
        and "full_30_day_replay_not_executed" not in blocking_reasons
        and "mail_preview_count_not_proven" not in blocking_reasons
        and "source_terminal_states_not_proven" not in blocking_reasons
    ):
        blocking_reasons.append("full_30_day_replay_not_executed")

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
        gates = _mapping(report.get("gates"))
        blocking_reasons = report.get("blocking_reasons", [])
        if not blocking_reasons:
            errors.append("blocked S2PLT01 precheck must include at least one blocking reason")
        gate_reason_pairs = (
            ("p0_zero", "inherited_v7_1_p0_findings_open"),
            ("p1_zero", "inherited_v7_1_p1_findings_open"),
            ("thirty_independent_days_proven", "full_30_day_replay_not_executed"),
            ("mail_previews_proven", "mail_preview_count_not_proven"),
            ("source_terminal_states_proven", "source_terminal_states_not_proven"),
        )
        for gate_name, reason in gate_reason_pairs:
            if gates.get(gate_name) is False and reason not in blocking_reasons:
                errors.append(f"blocked S2PLT01 precheck with {gate_name}=false must include {reason}")
    return errors


def _validate_s2plt01_replay_payload_inputs(
    *,
    payload_id: str,
    generated_at: str,
    generated_by: str,
    evidence_mode: str,
    replay_records: list[Mapping[str, Any]],
    mail_preview_records: list[Mapping[str, Any]],
    source_terminal_states: list[Mapping[str, Any]],
    evidence_refs: list[str],
) -> list[str]:
    errors: list[str] = []
    if not str(payload_id or "").strip():
        errors.append("payload_id_required")
    if not str(generated_at or "").strip():
        errors.append("generated_at_required")
    if not str(generated_by or "").strip():
        errors.append("generated_by_required")
    if evidence_mode not in {"actual_replay_evidence", "fixture_replay_contract"}:
        errors.append("invalid_evidence_mode")
    if not replay_records:
        errors.append("replay_records_required")
    if not mail_preview_records:
        errors.append("mail_preview_records_required")
    if not source_terminal_states:
        errors.append("source_terminal_states_required")
    if not evidence_refs or not all(str(ref).strip() for ref in evidence_refs):
        errors.append("evidence_refs_required")
    return errors


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _replay_record_passes(record: Mapping[str, Any]) -> bool:
    return (
        isinstance(record, Mapping)
        and record.get("status") == "pass"
        and _is_date(str(record.get("as_of_date") or ""))
        and int(record.get("future_leakage_count") or 0) == 0
        and int(record.get("p0_p1_blocker_count") or 0) == 0
        and _has_evidence_refs(record)
    )


def _mail_preview_record_passes(record: Mapping[str, Any]) -> bool:
    return (
        isinstance(record, Mapping)
        and record.get("status") == "pass"
        and _is_date(str(record.get("as_of_date") or ""))
        and record.get("mail_product_id") in S2PLT01_REQUIRED_MAIL_PRODUCTS
        and record.get("email_template_contract") == "EMAIL_LEARNING_V1"
        and record.get("real_smtp_sent") is False
        and _has_evidence_refs(record)
    )


def _terminal_source_record_passes(record: Mapping[str, Any]) -> bool:
    return (
        isinstance(record, Mapping)
        and record.get("source_domain") in S2PLT01_REQUIRED_SOURCE_DOMAINS
        and record.get("status") == "terminal_ready"
        and str(record.get("terminal_state") or "")
        and record.get("production_inclusion") is False
        and _has_evidence_refs(record)
    )


def _has_evidence_refs(record: Mapping[str, Any]) -> bool:
    refs = record.get("evidence_refs")
    return isinstance(refs, list) and bool(refs) and all(str(ref).strip() for ref in refs)


def _is_date(value: str) -> bool:
    try:
        return date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def _stable_hash(value: Mapping[str, Any]) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
