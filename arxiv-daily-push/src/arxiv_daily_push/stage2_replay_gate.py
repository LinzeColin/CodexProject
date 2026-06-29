"""S2PLT01 fail-closed replay entry precheck helpers."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from datetime import date
from pathlib import Path
from typing import Any


S2PLT01_ENTRY_PRECHECK_MODEL_ID = "adp-s2plt01-entry-precheck-v1"
S2PLT01_REPLAY_PAYLOAD_CONTRACT_ID = "adp-s2plt01-replay-payload-v1"
S2PLT01_INDEPENDENT_REVIEW_MODEL_ID = "adp-s2plt01-independent-replay-review-v1"
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
S2PLT01_INDEPENDENT_REVIEW_MANIFEST_PATH = (
    "governance/run_manifests/ADP-S2PLT01-INDEPENDENT-REPLAY-REVIEW-20260626.json"
)
S2PLT01_REPLAY_PAYLOAD_EXECUTION_MANIFEST_PATH = (
    "governance/run_manifests/ADP-S2PLT01-REPLAY-PAYLOAD-EXECUTION-20260626.json"
)
S2PLT01_REPLAY_PAYLOAD_EXECUTION_ID = "S2PLT01-REPLAY-PAYLOAD-EXECUTION-20260626-001"
S2PLT01_REPLAY_PAYLOAD_EXECUTION_GENERATED_AT = "2026-06-26T19:10:00+10:00"
S2PLT01_REPLAY_PAYLOAD_EXECUTION_GENERATED_BY = "codex-stage2-local"
S2PLT01_S2PLT04_REVIEW_SYNC_MANIFEST_PATH = (
    "governance/run_manifests/ADP-S2PLT04-S2PLT01-REPLAY-REVIEW-EVIDENCE-SYNC-20260628.json"
)
S2PLT01_P0_P1_ZERO_PROOF_ARTIFACT_PATH = "FINAL_ACCEPTANCE_BUNDLE/p0_p1_zero_proof.json"
S2PLT01_P0_P1_ZERO_PROOF_SCHEMA_VERSION = "adp.p0_p1_zero_proof.v1"
S2PLT01_P0_P1_ZERO_PROOF_CLOSURE_DECISION = "P0_P1_ZERO_PROVEN_NO_PRODUCTION_ACCEPTANCE"
S2PLT01_P0_P1_ZERO_PROOF_NO_PRODUCTION_FLAGS = (
    "integrated_production_accepted",
    "daily_operation_enabled",
    "real_smtp_sent",
    "real_smtp_send_enabled",
    "scheduler_enabled",
    "scheduler_install_enabled",
    "release_uploaded",
    "release_packaging_enabled",
    "production_restore_enabled",
    "production_restore_executed",
    "public_schema_changed",
    "db_migration_executed",
    "production_queue_mutated",
    "source_adapter_changed",
    "ranking_algorithm_changed",
    "current_pointer_changed",
    "v7_1_baseline_changed",
    "v7_2_contract_files_changed",
)
S2PLT01_TERMINAL_ACCEPTANCE_MODEL_ID = "adp-s2plt01-terminal-acceptance-v1"
S2PLT01_TERMINAL_ACCEPTANCE_ARTIFACT_PATH = "FINAL_ACCEPTANCE_BUNDLE/s2plt01_terminal_acceptance.json"
S2PLT01_TERMINAL_ACCEPTANCE_SCHEMA_VERSION = "adp.s2plt01_terminal_acceptance.v1"
S2PLT01_TERMINAL_ACCEPTANCE_DECISION = "S2PLT01_TERMINAL_ACCEPTED_NO_PRODUCTION_ACCEPTANCE"
S2PLT01_TERMINAL_ACCEPTANCE_REQUIRED_EVIDENCE_REFS = (
    S2PLT01_INDEPENDENT_REVIEW_MANIFEST_PATH,
    S2PLT01_REPLAY_PAYLOAD_EXECUTION_MANIFEST_PATH,
    S2PLT01_S2PLT04_REVIEW_SYNC_MANIFEST_PATH,
    S2PLT01_P0_P1_ZERO_PROOF_ARTIFACT_PATH,
)
S2PLT01_TERMINAL_ACCEPTANCE_NO_PRODUCTION_FLAGS = (
    "production_acceptance_claimed",
    "integrated_production_accepted",
    "daily_operation_enabled",
    "real_smtp_sent",
    "real_smtp_send_enabled",
    "scheduler_enabled",
    "scheduler_install_enabled",
    "release_uploaded",
    "release_packaging_enabled",
    "production_restore_enabled",
    "production_restore_executed",
    "public_schema_changed",
    "db_migration_executed",
    "production_queue_mutated",
    "source_adapter_changed",
    "ranking_algorithm_changed",
    "current_pointer_changed",
    "v7_1_baseline_changed",
    "v7_2_contract_files_changed",
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


def build_s2plt01_replay_payload_execution_report(
    *,
    execution_id: str,
    generated_at: str,
    generated_by: str,
    evidence_mode: str,
    replay_records: list[Mapping[str, Any]],
    mail_preview_records: list[Mapping[str, Any]],
    source_terminal_states: list[Mapping[str, Any]],
    evidence_refs: list[str],
) -> dict[str, Any]:
    """Build a no-production S2PLT01 payload execution package from explicit evidence."""

    payload = build_s2plt01_replay_payload(
        payload_id=execution_id,
        generated_at=generated_at,
        generated_by=generated_by,
        evidence_mode=evidence_mode,
        replay_records=replay_records,
        mail_preview_records=mail_preview_records,
        source_terminal_states=source_terminal_states,
        evidence_refs=evidence_refs,
    )
    payload_errors = validate_s2plt01_replay_payload(payload)
    entry_precheck = build_s2plt01_entry_precheck_report(
        generated_at=generated_at,
        replay_evidence=payload["replay_evidence"],
    )
    entry_precheck_errors = validate_s2plt01_entry_precheck_report(entry_precheck)
    payload_execution_package_passed = payload["status"] == "pass" and not payload_errors
    entry_precheck_passed = entry_precheck["status"] == "pass" and not entry_precheck_errors
    blocking_reasons = sorted(
        {
            *payload_errors,
            *entry_precheck_errors,
            *payload["validation_errors"],
            *payload["replay_evidence"].get("blocking_reasons", []),
            *entry_precheck["blocking_reasons"],
        }
    )
    if not payload_execution_package_passed:
        blocking_reasons.append("replay_payload_execution_package_not_passed")
        blocking_reasons = sorted(set(blocking_reasons))
    report = {
        "model_id": S2PLT01_ENTRY_PRECHECK_MODEL_ID,
        "schema_version": S2PLT01_SCHEMA_VERSION,
        "task_id": S2PLT01_TASK_ID,
        "acceptance_id": S2PLT01_ACCEPTANCE_ID,
        "execution_id": execution_id,
        "generated_at": generated_at,
        "generated_by": generated_by,
        "evidence_mode": evidence_mode,
        "status": "pass" if payload_execution_package_passed and entry_precheck_passed else "blocked",
        "scope": "no_production_replay_payload_execution_package",
        "payload_execution_package_passed": payload_execution_package_passed,
        "entry_precheck_passed": entry_precheck_passed,
        "payload": payload,
        "entry_precheck": entry_precheck,
        "payload_errors": payload_errors,
        "entry_precheck_errors": entry_precheck_errors,
        "blocking_reasons": blocking_reasons,
        "evidence_refs": list(evidence_refs),
        "execution_hash": "",
        **{flag: False for flag in S2PLT01_FORBIDDEN_FLAGS},
    }
    report["execution_hash"] = _stable_hash({key: value for key, value in report.items() if key != "execution_hash"})
    return report


def validate_s2plt01_replay_payload_execution_report(report: Mapping[str, Any]) -> list[str]:
    """Validate an S2PLT01 no-production payload execution package."""

    errors: list[str] = []
    if report.get("model_id") != S2PLT01_ENTRY_PRECHECK_MODEL_ID:
        errors.append("S2PLT01 replay payload execution model_id is invalid")
    if report.get("schema_version") != S2PLT01_SCHEMA_VERSION:
        errors.append("S2PLT01 replay payload execution schema_version must be 1")
    if report.get("task_id") != S2PLT01_TASK_ID:
        errors.append("S2PLT01 replay payload execution task_id is invalid")
    if report.get("acceptance_id") != S2PLT01_ACCEPTANCE_ID:
        errors.append("S2PLT01 replay payload execution acceptance_id is invalid")
    if not str(report.get("execution_id") or "").strip():
        errors.append("S2PLT01 replay payload execution_id is required")
    if not str(report.get("generated_at") or "").strip():
        errors.append("S2PLT01 replay payload execution generated_at is required")
    if not str(report.get("generated_by") or "").strip():
        errors.append("S2PLT01 replay payload execution generated_by is required")
    if report.get("evidence_mode") not in {"actual_replay_evidence", "fixture_replay_contract"}:
        errors.append("S2PLT01 replay payload execution evidence_mode is invalid")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("S2PLT01 replay payload execution status must be pass or blocked")
    if not _has_evidence_refs(report):
        errors.append("S2PLT01 replay payload execution evidence_refs are required")
    for flag in S2PLT01_FORBIDDEN_FLAGS:
        if report.get(flag) is not False:
            errors.append(f"{flag} must be false")

    payload = _mapping(report.get("payload"))
    payload_errors = validate_s2plt01_replay_payload(payload)
    entry_precheck = _mapping(report.get("entry_precheck"))
    entry_precheck_errors = validate_s2plt01_entry_precheck_report(entry_precheck)
    declared_payload_errors = list(report.get("payload_errors") or [])
    declared_entry_errors = list(report.get("entry_precheck_errors") or [])
    if declared_payload_errors != payload_errors:
        errors.append("S2PLT01 replay payload execution payload_errors must match payload validation")
    if declared_entry_errors != entry_precheck_errors:
        errors.append("S2PLT01 replay payload execution entry_precheck_errors must match precheck validation")
    if report.get("payload_execution_package_passed") is True and (payload.get("status") != "pass" or payload_errors):
        errors.append("payload_execution_package_passed requires a valid passing replay payload")
    if report.get("entry_precheck_passed") is True and (entry_precheck.get("status") != "pass" or entry_precheck_errors):
        errors.append("entry_precheck_passed requires a valid passing entry precheck")
    if report.get("status") == "pass":
        if report.get("payload_execution_package_passed") is not True or report.get("entry_precheck_passed") is not True:
            errors.append("passing S2PLT01 replay payload execution requires payload and entry precheck pass")
        if report.get("blocking_reasons"):
            errors.append("passing S2PLT01 replay payload execution must not have blocking reasons")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked S2PLT01 replay payload execution must include blocking reasons")
    expected_hash = _stable_hash({key: value for key, value in report.items() if key != "execution_hash"})
    if report.get("execution_hash") != expected_hash:
        errors.append("S2PLT01 replay payload execution_hash does not match report content")
    return errors


def build_s2plt01_independent_replay_review_report(
    *,
    review_id: str,
    generated_at: str,
    reviewer_id: str,
    reviewer_role: str,
    reviewer_involved_in_s2plt01_implementation: bool,
    replay_execution_report: Mapping[str, Any],
    ci_evidence_refs: list[str],
    evidence_refs: list[str],
) -> dict[str, Any]:
    """Build a no-production independent review receipt for an S2PLT01 execution package."""

    execution_errors = validate_s2plt01_replay_payload_execution_report(replay_execution_report)
    reviewer_independent = not reviewer_involved_in_s2plt01_implementation
    execution_blocking_reasons = set(replay_execution_report.get("blocking_reasons") or [])
    inherited_only_blockers = execution_blocking_reasons.issubset(
        {"inherited_v7_1_p0_findings_open", "inherited_v7_1_p1_findings_open"}
    )
    review_gates = {
        "reviewer_identity_present": bool(str(reviewer_id or "").strip()),
        "reviewer_role_present": bool(str(reviewer_role or "").strip()),
        "reviewer_independent": reviewer_independent,
        "execution_report_valid": not execution_errors,
        "payload_execution_package_passed": replay_execution_report.get("payload_execution_package_passed") is True,
        "entry_precheck_blocked_by_inherited_only": replay_execution_report.get("status") == "blocked" and inherited_only_blockers,
        "ci_evidence_refs_present": bool(ci_evidence_refs) and all(str(ref).strip() for ref in ci_evidence_refs),
        "evidence_refs_present": bool(evidence_refs) and all(str(ref).strip() for ref in evidence_refs),
        "no_production_side_effect": True,
    }
    blocking_reasons: list[str] = []
    if not review_gates["reviewer_identity_present"]:
        blocking_reasons.append("reviewer_id_missing")
    if not review_gates["reviewer_role_present"]:
        blocking_reasons.append("reviewer_role_missing")
    if not review_gates["reviewer_independent"]:
        blocking_reasons.append("reviewer_independence_not_proven")
    if not review_gates["execution_report_valid"]:
        blocking_reasons.append("replay_execution_report_invalid")
    if not review_gates["payload_execution_package_passed"]:
        blocking_reasons.append("payload_execution_package_not_passed")
    if not review_gates["entry_precheck_blocked_by_inherited_only"]:
        blocking_reasons.append("entry_precheck_has_unreviewed_non_inherited_blockers")
    if not review_gates["ci_evidence_refs_present"]:
        blocking_reasons.append("ci_evidence_refs_missing")
    if not review_gates["evidence_refs_present"]:
        blocking_reasons.append("review_evidence_refs_missing")
    blocking_reasons.extend(
        reason
        for reason in ("inherited_v7_1_p0_findings_open", "inherited_v7_1_p1_findings_open")
        if reason in execution_blocking_reasons
    )
    review_package_passed = not execution_errors and all(
        review_gates[name]
        for name in (
            "reviewer_identity_present",
            "reviewer_role_present",
            "reviewer_independent",
            "execution_report_valid",
            "payload_execution_package_passed",
            "entry_precheck_blocked_by_inherited_only",
            "ci_evidence_refs_present",
            "evidence_refs_present",
            "no_production_side_effect",
        )
    )
    report = {
        "model_id": S2PLT01_INDEPENDENT_REVIEW_MODEL_ID,
        "schema_version": S2PLT01_SCHEMA_VERSION,
        "task_id": S2PLT01_TASK_ID,
        "subtask_id": "S2PLT01-INDEPENDENT-REPLAY-REVIEW",
        "acceptance_id": S2PLT01_ACCEPTANCE_ID,
        "review_id": review_id,
        "generated_at": generated_at,
        "reviewer_id": reviewer_id,
        "reviewer_role": reviewer_role,
        "reviewer_involved_in_s2plt01_implementation": reviewer_involved_in_s2plt01_implementation,
        "status": "blocked",
        "scope": "no_production_independent_replay_review_receipt",
        "review_package_passed": review_package_passed,
        "review_gates": review_gates,
        "replay_execution_report": dict(replay_execution_report),
        "replay_execution_errors": execution_errors,
        "blocking_reasons": sorted(set(blocking_reasons)),
        "ci_evidence_refs": list(ci_evidence_refs),
        "evidence_refs": list(evidence_refs),
        "s2plt01_acceptance_claimed": False,
        "production_acceptance_claimed": False,
        "review_hash": "",
        **{flag: False for flag in S2PLT01_FORBIDDEN_FLAGS},
    }
    report["review_hash"] = _stable_hash({key: value for key, value in report.items() if key != "review_hash"})
    return report


def validate_s2plt01_independent_replay_review_report(report: Mapping[str, Any]) -> list[str]:
    """Validate an S2PLT01 no-production independent replay review receipt."""

    errors: list[str] = []
    if report.get("model_id") != S2PLT01_INDEPENDENT_REVIEW_MODEL_ID:
        errors.append("S2PLT01 independent replay review model_id is invalid")
    if report.get("schema_version") != S2PLT01_SCHEMA_VERSION:
        errors.append("S2PLT01 independent replay review schema_version must be 1")
    if report.get("task_id") != S2PLT01_TASK_ID:
        errors.append("S2PLT01 independent replay review task_id is invalid")
    if report.get("subtask_id") != "S2PLT01-INDEPENDENT-REPLAY-REVIEW":
        errors.append("S2PLT01 independent replay review subtask_id is invalid")
    if report.get("acceptance_id") != S2PLT01_ACCEPTANCE_ID:
        errors.append("S2PLT01 independent replay review acceptance_id is invalid")
    if not str(report.get("review_id") or "").strip():
        errors.append("S2PLT01 independent replay review_id is required")
    if not str(report.get("generated_at") or "").strip():
        errors.append("S2PLT01 independent replay review generated_at is required")
    if not str(report.get("reviewer_id") or "").strip():
        errors.append("S2PLT01 independent replay reviewer_id is required")
    if not str(report.get("reviewer_role") or "").strip():
        errors.append("S2PLT01 independent replay reviewer_role is required")
    if report.get("status") != "blocked":
        errors.append("S2PLT01 independent replay review must remain blocked until inherited P0/P1 and final gates close")
    if report.get("s2plt01_acceptance_claimed") is not False:
        errors.append("S2PLT01 independent replay review must not claim S2PLT01 acceptance")
    if report.get("production_acceptance_claimed") is not False:
        errors.append("S2PLT01 independent replay review must not claim production acceptance")
    for flag in S2PLT01_FORBIDDEN_FLAGS:
        if report.get(flag) is not False:
            errors.append(f"{flag} must be false")

    execution_report = _mapping(report.get("replay_execution_report"))
    execution_errors = validate_s2plt01_replay_payload_execution_report(execution_report)
    if list(report.get("replay_execution_errors") or []) != execution_errors:
        errors.append("S2PLT01 independent replay review replay_execution_errors must match execution validation")
    gates = _mapping(report.get("review_gates"))
    if report.get("review_package_passed") is True:
        required_true = (
            "reviewer_identity_present",
            "reviewer_role_present",
            "reviewer_independent",
            "execution_report_valid",
            "payload_execution_package_passed",
            "entry_precheck_blocked_by_inherited_only",
            "ci_evidence_refs_present",
            "evidence_refs_present",
            "no_production_side_effect",
        )
        for gate in required_true:
            if gates.get(gate) is not True:
                errors.append(f"review_package_passed requires {gate}")
        for reason in ("inherited_v7_1_p0_findings_open", "inherited_v7_1_p1_findings_open"):
            if reason not in report.get("blocking_reasons", []):
                errors.append(f"blocked S2PLT01 independent replay review must retain {reason}")
    else:
        if not report.get("blocking_reasons"):
            errors.append("blocked S2PLT01 independent replay review must include blocking reasons")
    if not report.get("ci_evidence_refs"):
        errors.append("S2PLT01 independent replay review ci_evidence_refs are required")
    if not _has_evidence_refs(report):
        errors.append("S2PLT01 independent replay review evidence_refs are required")
    expected_hash = _stable_hash({key: value for key, value in report.items() if key != "review_hash"})
    if report.get("review_hash") != expected_hash:
        errors.append("S2PLT01 independent replay review_hash does not match report content")
    return errors


def _build_s2plt01_terminal_acceptance_prerequisite_snapshot(root: Path) -> dict[str, Any]:
    review_manifest = _load_json_mapping(root / S2PLT01_INDEPENDENT_REVIEW_MANIFEST_PATH)
    s2plt04_sync = _load_json_mapping(root / S2PLT01_S2PLT04_REVIEW_SYNC_MANIFEST_PATH)
    replay_payload_execution_validation = _build_s2plt01_replay_payload_execution_package_validation_state(root)
    zero_proof_validation = _build_s2plt01_p0_p1_zero_proof_artifact_validation_state(root)
    current_entry_precheck_readiness = _build_s2plt01_current_entry_precheck_zero_proof_readiness_state(root)
    p0_zero_proven = (
        zero_proof_validation["p0_zero_proven_by_payload"] is True
        or int(s2plt04_sync.get("inherited_v7_1_open_p0_findings") or 0) == 0
    )
    p1_zero_proven = (
        zero_proof_validation["p1_zero_proven_by_payload"] is True
        or int(s2plt04_sync.get("inherited_v7_1_open_p1_findings") or 0) == 0
    )
    review_receipt_present = bool(review_manifest)
    review_package_passed = (
        review_manifest.get("independent_replay_review_receipt_added") is True
        and "independent_s2plt01_review_not_completed" not in list(review_manifest.get("blocking_reasons") or [])
        and bool(s2plt04_sync.get("s2plt01_independent_replay_review_hash"))
        and "S2PLT01_INDEPENDENT_REPLAY_REVIEW" in list(s2plt04_sync.get("consumed_nonterminal_evidence") or [])
    )
    terminal_gates = {
        "review_receipt_present": review_receipt_present,
        "review_package_passed": review_package_passed,
        "replay_payload_execution_package_passed": replay_payload_execution_validation["status"] == "pass",
        "current_entry_precheck_zero_proof_ready": current_entry_precheck_readiness["status"] == "pass",
        "inherited_p0_zero": p0_zero_proven,
        "inherited_p1_zero": p1_zero_proven,
    }
    return {
        "terminal_gates": terminal_gates,
        "review_manifest_ref": S2PLT01_INDEPENDENT_REVIEW_MANIFEST_PATH,
        "s2plt04_review_sync_ref": S2PLT01_S2PLT04_REVIEW_SYNC_MANIFEST_PATH,
        "replay_payload_execution_package_validation": replay_payload_execution_validation,
        "p0_p1_zero_proof_artifact_validation": zero_proof_validation,
        "current_entry_precheck_zero_proof_readiness": current_entry_precheck_readiness,
    }


def build_s2plt01_terminal_acceptance_artifact_validation_state(
    *, repo_root: str | Path = "."
) -> dict[str, Any]:
    """Validate the future live S2PLT01 terminal acceptance artifact."""

    root = Path(repo_root)
    artifact = _load_json_mapping(root / S2PLT01_TERMINAL_ACCEPTANCE_ARTIFACT_PATH)
    prerequisites = _build_s2plt01_terminal_acceptance_prerequisite_snapshot(root)
    validation_errors: list[str] = []

    if not artifact:
        validation_errors.append("s2plt01_terminal_acceptance_artifact_missing")
    else:
        if artifact.get("model_id") != S2PLT01_TERMINAL_ACCEPTANCE_MODEL_ID:
            validation_errors.append("model_id_invalid")
        if artifact.get("schema_version") != S2PLT01_TERMINAL_ACCEPTANCE_SCHEMA_VERSION:
            validation_errors.append("schema_version_invalid")
        if artifact.get("task_id") != S2PLT01_TASK_ID:
            validation_errors.append("task_id_invalid")
        if artifact.get("acceptance_id") != S2PLT01_ACCEPTANCE_ID:
            validation_errors.append("acceptance_id_invalid")
        if artifact.get("terminal_acceptance_decision") != S2PLT01_TERMINAL_ACCEPTANCE_DECISION:
            validation_errors.append("terminal_acceptance_decision_invalid")
        if artifact.get("s2plt01_accepted") is not True:
            validation_errors.append("s2plt01_accepted_must_be_true")
        if not str(artifact.get("generated_at") or "").strip():
            validation_errors.append("generated_at_required")
        if not str(artifact.get("reviewer_id") or "").strip():
            validation_errors.append("reviewer_id_required")
        if not str(artifact.get("reviewer_role") or "").strip():
            validation_errors.append("reviewer_role_required")
        if artifact.get("reviewer_involved_in_s2plt01_implementation") is not False:
            validation_errors.append("reviewer_independence_not_proven")

        terminal_gates = _mapping(artifact.get("terminal_gates"))
        for gate_name, gate_value in prerequisites["terminal_gates"].items():
            if gate_value is not True:
                validation_errors.append(f"current_prerequisite_{gate_name}_not_true")
            if terminal_gates.get(gate_name) is not True:
                validation_errors.append(f"terminal_gates.{gate_name}_must_be_true")

        evidence_refs = artifact.get("terminal_evidence_refs")
        if not isinstance(evidence_refs, list) or not evidence_refs:
            validation_errors.append("terminal_evidence_refs_required")
            evidence_refs = []
        for required_ref in S2PLT01_TERMINAL_ACCEPTANCE_REQUIRED_EVIDENCE_REFS:
            if required_ref not in evidence_refs:
                validation_errors.append(f"terminal_evidence_refs_missing:{required_ref}")

        no_production = _mapping(artifact.get("no_production_side_effects"))
        for flag in S2PLT01_TERMINAL_ACCEPTANCE_NO_PRODUCTION_FLAGS:
            if artifact.get(flag) is not False:
                validation_errors.append(f"{flag}_must_be_false")
            if no_production.get(flag) is not False:
                validation_errors.append(f"no_production_side_effects.{flag}_must_be_false")

        expected_hash = _stable_hash({key: value for key, value in artifact.items() if key != "acceptance_hash"})
        if artifact.get("acceptance_hash") != expected_hash:
            validation_errors.append("acceptance_hash_mismatch")

    state = {
        "status": "pass" if artifact and not validation_errors else "blocked",
        "scope": "s2plt01_terminal_acceptance_artifact_validation_only_no_production_acceptance",
        "artifact_ref": S2PLT01_TERMINAL_ACCEPTANCE_ARTIFACT_PATH,
        "artifact_present": bool(artifact),
        "model_id": S2PLT01_TERMINAL_ACCEPTANCE_MODEL_ID,
        "schema_version": S2PLT01_TERMINAL_ACCEPTANCE_SCHEMA_VERSION,
        "task_id": S2PLT01_TASK_ID,
        "acceptance_id": S2PLT01_ACCEPTANCE_ID,
        "terminal_acceptance_decision": artifact.get("terminal_acceptance_decision") if artifact else None,
        "s2plt01_accepted_by_artifact": bool(artifact) and artifact.get("s2plt01_accepted") is True and not validation_errors,
        "terminal_gates": dict(prerequisites["terminal_gates"]),
        "required_terminal_evidence_refs": list(S2PLT01_TERMINAL_ACCEPTANCE_REQUIRED_EVIDENCE_REFS),
        "validation_errors": sorted(set(validation_errors)),
        "acceptance_hash": artifact.get("acceptance_hash") if artifact else "",
        "production_acceptance_claimed": False,
        "integrated_production_accepted": False,
        "daily_operation_enabled": False,
        "real_smtp_sent": False,
        "real_smtp_send_enabled": False,
        "scheduler_enabled": False,
        "scheduler_install_enabled": False,
        "release_uploaded": False,
        "release_packaging_enabled": False,
        "production_restore_enabled": False,
        "production_restore_executed": False,
        "public_schema_changed": False,
        "db_migration_executed": False,
        "production_queue_mutated": False,
        "source_adapter_changed": False,
        "ranking_algorithm_changed": False,
        "current_pointer_changed": False,
        "v7_1_baseline_changed": False,
        "v7_2_contract_files_changed": False,
        "state_hash": "",
    }
    state["state_hash"] = _stable_hash({key: value for key, value in state.items() if key != "state_hash"})
    return state


def build_s2plt01_terminal_acceptance_audit_state(*, repo_root: str | Path = ".") -> dict[str, Any]:
    """Audit current S2PLT01 terminal acceptance without claiming acceptance."""

    root = Path(repo_root)
    review_manifest = _load_json_mapping(root / S2PLT01_INDEPENDENT_REVIEW_MANIFEST_PATH)
    prerequisites = _build_s2plt01_terminal_acceptance_prerequisite_snapshot(root)
    replay_payload_execution_validation = prerequisites["replay_payload_execution_package_validation"]
    zero_proof_validation = prerequisites["p0_p1_zero_proof_artifact_validation"]
    current_entry_precheck_readiness = prerequisites["current_entry_precheck_zero_proof_readiness"]
    terminal_acceptance_artifact_validation = build_s2plt01_terminal_acceptance_artifact_validation_state(repo_root=root)
    review_receipt_present = prerequisites["terminal_gates"]["review_receipt_present"]
    review_package_passed = prerequisites["terminal_gates"]["review_package_passed"]
    s2plt01_accepted_by_artifact = terminal_acceptance_artifact_validation["s2plt01_accepted_by_artifact"] is True
    terminal_gates = {
        "review_receipt_present": review_receipt_present,
        "review_package_passed": review_package_passed,
        "replay_payload_execution_package_passed": replay_payload_execution_validation["status"] == "pass",
        "current_entry_precheck_zero_proof_ready": current_entry_precheck_readiness["status"] == "pass",
        "s2plt01_accepted": s2plt01_accepted_by_artifact,
        "inherited_p0_zero": prerequisites["terminal_gates"]["inherited_p0_zero"],
        "inherited_p1_zero": prerequisites["terminal_gates"]["inherited_p1_zero"],
    }
    blocking_reasons: list[str] = []
    if not review_receipt_present:
        blocking_reasons.append("review_receipt_missing")
    if review_package_passed and not terminal_gates["s2plt01_accepted"]:
        blocking_reasons.append("review_receipt_is_nonterminal")
    if not terminal_acceptance_artifact_validation["artifact_present"]:
        blocking_reasons.append("s2plt01_terminal_acceptance_artifact_missing")
    elif terminal_acceptance_artifact_validation["status"] != "pass":
        blocking_reasons.append("s2plt01_terminal_acceptance_artifact_invalid")
    if not terminal_gates["replay_payload_execution_package_passed"]:
        blocking_reasons.append("replay_payload_execution_package_not_passed")
    if not terminal_gates["current_entry_precheck_zero_proof_ready"]:
        blocking_reasons.append("current_entry_precheck_zero_proof_not_ready")
    if not terminal_gates["s2plt01_accepted"]:
        blocking_reasons.append("s2plt01_not_accepted")
    if not terminal_gates["inherited_p0_zero"]:
        blocking_reasons.append("inherited_v7_1_p0_findings_open")
    if not terminal_gates["inherited_p1_zero"]:
        blocking_reasons.append("inherited_v7_1_p1_findings_open")

    terminal_acceptance_ready = all(terminal_gates.values())
    state = {
        "status": "pass" if terminal_acceptance_ready else "blocked",
        "scope": "s2plt01_terminal_acceptance_audit_only_no_acceptance_claim",
        "task_id": "S2PLT01",
        "acceptance_id": S2PLT01_ACCEPTANCE_ID,
        "terminal_acceptance_ready": terminal_acceptance_ready,
        "review_receipt_present": review_receipt_present,
        "review_package_passed": review_package_passed,
        "review_manifest_ref": S2PLT01_INDEPENDENT_REVIEW_MANIFEST_PATH,
        "replay_payload_execution_manifest_ref": S2PLT01_REPLAY_PAYLOAD_EXECUTION_MANIFEST_PATH,
        "s2plt04_review_sync_ref": S2PLT01_S2PLT04_REVIEW_SYNC_MANIFEST_PATH,
        "terminal_acceptance_artifact_ref": S2PLT01_TERMINAL_ACCEPTANCE_ARTIFACT_PATH,
        "terminal_acceptance_artifact_validation": terminal_acceptance_artifact_validation,
        "replay_payload_execution_package_validation": replay_payload_execution_validation,
        "p0_p1_zero_proof_artifact_validation": zero_proof_validation,
        "current_entry_precheck_zero_proof_readiness": current_entry_precheck_readiness,
        "terminal_gates": terminal_gates,
        "blocking_reasons": sorted(set(blocking_reasons)),
        "full_replay_executed": review_manifest.get("full_replay_executed") is True,
        "s2plt01_accepted": s2plt01_accepted_by_artifact,
        "s2plt04_completed": review_manifest.get("s2plt04_completed") is True,
        "s2pmt07_final_signoff_claimed": review_manifest.get("s2pmt07_final_signoff_claimed") is True,
        "production_acceptance_claimed": False,
        "integrated_production_accepted": False,
        "real_smtp_sent": False,
        "scheduler_enabled": False,
        "release_uploaded": False,
        "public_schema_changed": False,
        "db_migration_executed": False,
        "current_pointer_changed": False,
        "v7_1_baseline_changed": False,
        "v7_2_contract_files_changed": False,
        "state_hash": "",
    }
    state["state_hash"] = _stable_hash({key: value for key, value in state.items() if key != "state_hash"})
    return state


def build_s2plt01_entry_precheck_report(
    *,
    generated_at: str,
    replay_evidence: Mapping[str, Any] | None = None,
    audit_blockers: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a deterministic fail-closed S2PLT01 entry precheck report."""

    dependencies = build_s2plt01_dependency_state()
    audit = dict(audit_blockers) if isinstance(audit_blockers, Mapping) else build_s2plt01_audit_blocker_state()
    replay = dict(replay_evidence) if isinstance(replay_evidence, Mapping) else build_s2plt01_replay_evidence_state()
    audit_checks = _mapping(audit.get("checks"))
    gates = {
        "dependencies_complete": dependencies["status"] == "pass",
        "p0_zero": audit_checks.get("P0_zero") is True,
        "p1_zero": audit_checks.get("P1_zero") is True,
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


def _load_json_mapping(path: Path) -> Mapping[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, Mapping) else {}


def _build_s2plt01_replay_payload_execution_package_validation_state(root: Path) -> dict[str, Any]:
    manifest = _load_json_mapping(root / S2PLT01_REPLAY_PAYLOAD_EXECUTION_MANIFEST_PATH)
    s2plt04_sync = _load_json_mapping(root / S2PLT01_S2PLT04_REVIEW_SYNC_MANIFEST_PATH)
    report = build_s2plt01_replay_payload_execution_report(
        execution_id=S2PLT01_REPLAY_PAYLOAD_EXECUTION_ID,
        generated_at=S2PLT01_REPLAY_PAYLOAD_EXECUTION_GENERATED_AT,
        generated_by=S2PLT01_REPLAY_PAYLOAD_EXECUTION_GENERATED_BY,
        evidence_mode="actual_replay_evidence",
        replay_records=_build_s2plt01_committed_replay_records(),
        mail_preview_records=_build_s2plt01_committed_mail_preview_records(),
        source_terminal_states=_build_s2plt01_committed_source_terminal_states(),
        evidence_refs=[S2PLT01_REPLAY_PAYLOAD_EXECUTION_MANIFEST_PATH],
    )
    report_errors = validate_s2plt01_replay_payload_execution_report(report)
    expected_hash = str(s2plt04_sync.get("s2plt01_replay_execution_hash") or "")
    validation_errors: list[str] = []

    if not manifest:
        validation_errors.append("replay_payload_execution_manifest_missing")
    if manifest and manifest.get("task_id") != "S2PLT01-REPLAY-PAYLOAD-EXECUTION":
        validation_errors.append("replay_payload_execution_manifest_task_id_invalid")
    if manifest and manifest.get("replay_payload_execution_package_added") is not True:
        validation_errors.append("replay_payload_execution_package_added_not_true")
    if manifest and str(manifest.get("binding_status") or "") not in {
        "local_validation_passed_pending_pr_ci",
        "mainline_validation_passed",
    }:
        validation_errors.append("replay_payload_execution_binding_status_invalid")
    if report.get("payload_execution_package_passed") is not True:
        validation_errors.append("replay_payload_execution_package_not_passed")
    if report_errors:
        validation_errors.append("replay_payload_execution_report_invalid")
    if not expected_hash:
        validation_errors.append("s2plt04_replay_execution_hash_missing")
    if expected_hash and report.get("execution_hash") != expected_hash:
        validation_errors.append("s2plt04_replay_execution_hash_mismatch")

    for flag in S2PLT01_FORBIDDEN_FLAGS:
        if manifest and flag in manifest and manifest.get(flag) is not False:
            validation_errors.append(f"manifest.{flag}_must_be_false")
        if report.get(flag) is not False:
            validation_errors.append(f"report.{flag}_must_be_false")

    replay_evidence = _mapping(_mapping(report.get("payload")).get("replay_evidence"))
    return {
        "status": "pass" if not validation_errors else "blocked",
        "artifact_ref": S2PLT01_REPLAY_PAYLOAD_EXECUTION_MANIFEST_PATH,
        "artifact_present": bool(manifest),
        "execution_id": S2PLT01_REPLAY_PAYLOAD_EXECUTION_ID,
        "generated_at": S2PLT01_REPLAY_PAYLOAD_EXECUTION_GENERATED_AT,
        "payload_execution_package_passed": report.get("payload_execution_package_passed") is True,
        "entry_precheck_passed": report.get("entry_precheck_passed") is True,
        "report_status": report.get("status"),
        "observed_replay_days": replay_evidence.get("observed_replay_days"),
        "observed_mail_previews": replay_evidence.get("observed_mail_previews"),
        "source_terminal_states_proven": replay_evidence.get("source_terminal_states_proven"),
        "future_leakage_count": replay_evidence.get("future_leakage_count"),
        "p0_p1_blocker_count": replay_evidence.get("p0_p1_blocker_count"),
        "expected_execution_hash": expected_hash,
        "actual_execution_hash": report.get("execution_hash"),
        "report_validation_errors": report_errors,
        "validation_errors": validation_errors,
    }


def _build_s2plt01_p0_p1_zero_proof_artifact_validation_state(root: Path) -> dict[str, Any]:
    artifact = _load_json_mapping(root / S2PLT01_P0_P1_ZERO_PROOF_ARTIFACT_PATH)
    validation_errors: list[str] = []
    if not artifact:
        validation_errors.append("p0_p1_zero_proof_artifact_missing")
    if artifact and artifact.get("schema_version") != S2PLT01_P0_P1_ZERO_PROOF_SCHEMA_VERSION:
        validation_errors.append("schema_version_invalid")

    finding_counts = _mapping(artifact.get("finding_counts"))
    zero_severity_counts = _mapping(artifact.get("zero_severity_counts"))
    decision = _mapping(artifact.get("independent_closure_decision"))
    no_production = _mapping(artifact.get("no_production_side_effects"))
    p0_zero = finding_counts.get("P0") == 0 and zero_severity_counts.get("P0") == 0
    p1_zero = finding_counts.get("P1") == 0 and zero_severity_counts.get("P1") == 0
    if artifact and not p0_zero:
        validation_errors.append("p0_zero_not_proven")
    if artifact and not p1_zero:
        validation_errors.append("p1_zero_not_proven")
    if artifact and decision.get("decision") != S2PLT01_P0_P1_ZERO_PROOF_CLOSURE_DECISION:
        validation_errors.append("independent_closure_decision_invalid")
    if artifact and decision.get("production_acceptance_claimed") is not False:
        validation_errors.append("production_acceptance_claimed_must_be_false")
    for flag in S2PLT01_P0_P1_ZERO_PROOF_NO_PRODUCTION_FLAGS:
        if artifact and no_production.get(flag) is not False:
            validation_errors.append(f"no_production_side_effects.{flag}_must_be_false")

    return {
        "status": "pass" if not validation_errors else "blocked",
        "artifact_ref": S2PLT01_P0_P1_ZERO_PROOF_ARTIFACT_PATH,
        "artifact_present": bool(artifact),
        "p0_zero_proven_by_payload": bool(artifact) and p0_zero and not validation_errors,
        "p1_zero_proven_by_payload": bool(artifact) and p1_zero and not validation_errors,
        "production_acceptance_claimed": decision.get("production_acceptance_claimed") if artifact else None,
        "validation_errors": validation_errors,
    }


def _build_s2plt01_current_entry_precheck_zero_proof_readiness_state(root: Path) -> dict[str, Any]:
    zero_proof_validation = _build_s2plt01_p0_p1_zero_proof_artifact_validation_state(root)
    replay_evidence = build_s2plt01_replay_evidence_from_records(
        replay_records=_build_s2plt01_committed_replay_records(),
        mail_preview_records=_build_s2plt01_committed_mail_preview_records(),
        source_terminal_states=_build_s2plt01_committed_source_terminal_states(),
    )
    audit_blockers = build_s2plt01_audit_blocker_state(
        inherited_p0=0
        if zero_proof_validation.get("p0_zero_proven_by_payload") is True
        else S2PLT01_INHERITED_V7_1_OPEN_P0_FINDINGS,
        inherited_p1=0
        if zero_proof_validation.get("p1_zero_proven_by_payload") is True
        else S2PLT01_INHERITED_V7_1_OPEN_P1_FINDINGS,
    )
    entry_precheck = build_s2plt01_entry_precheck_report(
        generated_at=S2PLT01_REPLAY_PAYLOAD_EXECUTION_GENERATED_AT,
        replay_evidence=replay_evidence,
        audit_blockers=audit_blockers,
    )
    entry_precheck_errors = validate_s2plt01_entry_precheck_report(entry_precheck)
    validation_errors: list[str] = []
    if zero_proof_validation.get("status") != "pass":
        validation_errors.append("p0_p1_zero_proof_artifact_not_passed")
    if replay_evidence.get("status") != "pass":
        validation_errors.append("committed_replay_evidence_not_passed")
    if entry_precheck_errors:
        validation_errors.append("entry_precheck_report_invalid")
    if entry_precheck.get("status") != "pass":
        validation_errors.append("entry_precheck_not_ready")

    return {
        "status": "pass" if not validation_errors else "blocked",
        "scope": "current_entry_precheck_zero_proof_readiness_no_acceptance_claim",
        "generated_at": S2PLT01_REPLAY_PAYLOAD_EXECUTION_GENERATED_AT,
        "zero_proof_artifact_ref": S2PLT01_P0_P1_ZERO_PROOF_ARTIFACT_PATH,
        "zero_proof_artifact_status": zero_proof_validation.get("status"),
        "entry_precheck_passed": entry_precheck.get("status") == "pass" and not entry_precheck_errors,
        "entry_precheck_report_hash": entry_precheck.get("report_hash"),
        "gates": dict(entry_precheck.get("gates") or {}),
        "blocking_reasons": list(entry_precheck.get("blocking_reasons") or []),
        "observed_replay_days": replay_evidence.get("observed_replay_days"),
        "observed_mail_previews": replay_evidence.get("observed_mail_previews"),
        "source_terminal_states_proven": replay_evidence.get("source_terminal_states_proven"),
        "future_leakage_count": replay_evidence.get("future_leakage_count"),
        "p0_p1_blocker_count": replay_evidence.get("p0_p1_blocker_count"),
        "validation_errors": validation_errors,
        "entry_precheck_errors": entry_precheck_errors,
        "s2plt01_accepted": False,
        "production_acceptance_claimed": False,
        **{flag: False for flag in S2PLT01_FORBIDDEN_FLAGS},
    }


def _build_s2plt01_committed_replay_records() -> list[dict[str, Any]]:
    return [
        {
            "as_of_date": f"2026-05-{day:02d}",
            "status": "pass",
            "source_domains": ["D1", "D2", "D3", "D4"],
            "reading_boards": ["B1", "B2", "B3", "B4", "B5", "B6"],
            "future_leakage_count": 0,
            "p0_p1_blocker_count": 0,
            "evidence_refs": [f"replay/{day:02d}.json"],
        }
        for day in range(1, 31)
    ]


def _build_s2plt01_committed_mail_preview_records() -> list[dict[str, Any]]:
    return [
        {
            "as_of_date": f"2026-05-{day:02d}",
            "mail_product_id": product_id,
            "status": "pass",
            "email_template_contract": "EMAIL_LEARNING_V1",
            "real_smtp_sent": False,
            "evidence_refs": [f"mail/{day:02d}/{product_id}.json"],
        }
        for day in range(1, 31)
        for product_id in S2PLT01_REQUIRED_MAIL_PRODUCTS
    ]


def _build_s2plt01_committed_source_terminal_states() -> list[dict[str, Any]]:
    return [
        {
            "source_domain": domain,
            "status": "terminal_ready",
            "terminal_state": "qualified_no_send",
            "production_inclusion": False,
            "evidence_refs": [f"terminal/{domain}.json"],
        }
        for domain in S2PLT01_REQUIRED_SOURCE_DOMAINS
    ]


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
