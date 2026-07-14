#!/usr/bin/env python3
"""Validate KMFA v0.1.4 S17-P2 notification policy evidence."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.v014_s17_p2_notification_policy import (  # noqa: E402
    ACCEPTANCE_ID,
    DISPATCH_LOG_PATH,
    EVENT_LOG_PATH,
    MANIFEST_PATH,
    METADATA_DISPATCH_LOG_PATH,
    METADATA_EVENTS_PATH,
    METADATA_MANIFEST_PATH,
    METADATA_RULES_PATH,
    NEXT_PHASE,
    NEXT_REQUIRED_STEP,
    PHASE_SCOPE,
    REPORT_PATH,
    REQUIRED_V014_NOTIFICATION_TRIGGERS,
    RISK_REGISTER_PATH,
    ROLLBACK_PATH,
    RULE_LOCK_PATH,
    SCHEMA_VERSION,
    TASK_ID,
    TEST_RESULTS_PATH,
    _phase_boundaries,
    _public_repo_safety,
    _quality_gate,
    _raw_boundary,
    load_v14_taskpack_baseline,
    validate_legacy_s17_p2_artifacts,
    validate_s17_p1_dependency,
)


PUBLIC_SAFETY_FALSE_KEYS = tuple(key for key, value in _public_repo_safety().items() if value is False)
RAW_BOUNDARY_FALSE_KEYS = tuple(key for key, value in _raw_boundary().items() if value is False)
QUALITY_FALSE_KEYS = tuple(key for key, value in _quality_gate().items() if value is False)
QUALITY_TRUE_KEYS = tuple(key for key, value in _quality_gate().items() if value is True)
PHASE_FALSE_KEYS = tuple(key for key, value in _phase_boundaries().items() if value is False)
PHASE_TRUE_KEYS = tuple(key for key, value in _phase_boundaries().items() if value is True)

FORBIDDEN_PUBLIC_TEXT = (
    "raw_value:",
    "normalized_value:",
    "source_header_text:",
    "original_filename",
    "member_sha256:",
    "actual_package_sha256",
    "authoritative_value_cents",
    "system_value_cents",
    "amount_cents:",
    "amount_yuan:",
    "sheet_name:",
    "row_value:",
    "cell_value:",
    "business_data:",
    "bank_statement_payload",
    "contract_full_text",
    "salary_detail",
    "tax_filing_material",
    "connector_" + "token:",
    "connector_" + "pass" + "word:",
    "api" + "_key:",
    "private" + "_key:",
    "credential_payload",
    "report_attachment_path",
    "-----" "BEGIN",
    "project_name_plaintext",
    "customer_name_plaintext",
    "counterparty_plaintext",
    "company_entity_plaintext",
    "supplier_name_plaintext",
    "payment_account",
    "account_number:",
    "invoice_number:",
    "tax_identifier:",
    "private_ref://",
    "recipient_" + "email",
    "smtp",
    "KMFA" "_MetaData",
    "/Users/linzezhang/Downloads",
    ".xlsx",
    ".xls",
    ".zip",
    ".pdf",
    ".sqlite",
    ".db",
)
STRICT_SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(?i)(password|passwd|secret|api" + r"_key|token)\s*=\s*[^\s,;]{8,}"),
)


class ValidationError(Exception):
    pass


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ValidationError(f"missing JSON file: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValidationError(f"{path} must contain a JSON object")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise ValidationError(f"missing JSONL file: {path}")
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValidationError(f"{path} contains a non-object JSONL row")
        rows.append(value)
    return rows


def git_output(args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise ValidationError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def check_public_evidence_text(path: Path, errors: list[str]) -> None:
    require(path.exists(), f"missing public evidence: {path}", errors)
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8", errors="ignore")
    lower = text.lower()
    for forbidden in FORBIDDEN_PUBLIC_TEXT:
        require(forbidden.lower() not in lower, f"forbidden public evidence text {forbidden!r} in {path}", errors)
    for pattern in STRICT_SECRET_PATTERNS:
        require(pattern.search(text) is None, f"secret-like token found in {path}: {pattern.pattern}", errors)


def _require_false_keys(record: dict[str, Any], keys: tuple[str, ...], label: str, errors: list[str]) -> None:
    for key in keys:
        require(record.get(key) is False, f"{label}.{key} must be false", errors)


def _check_jsonl_equal(left: list[dict[str, Any]], right: list[dict[str, Any]], label: str, errors: list[str]) -> None:
    require(left == right, f"{label} metadata copy must match machine evidence", errors)


def _check_rule_locks(rows: list[dict[str, Any]], errors: list[str]) -> None:
    required = set(REQUIRED_V014_NOTIFICATION_TRIGGERS)
    require(len(rows) == 3, "notification rule count must be 3", errors)
    require({str(row.get("trigger_type")) for row in rows} == required, "notification rule triggers mismatch", errors)
    for row in rows:
        trigger_type = str(row.get("trigger_type"))
        require(
            row.get("record_type") == "v014_s17_p2_notification_rule_lock",
            "rule record type mismatch",
            errors,
        )
        require(row.get("project_id") == "KMFA", "rule project_id mismatch", errors)
        require(row.get("stage_id") == "S17", "rule stage_id mismatch", errors)
        require(row.get("phase_id") == "S17-P2", "rule phase_id mismatch", errors)
        require(row.get("channel") == "email_reminder", "rule channel mismatch", errors)
        require(row.get("recipient_role") in {"management", "finance", "reviewer"}, "rule role mismatch", errors)
        require(trigger_type in str(row.get("rule_id")), "rule id must include trigger type", errors)
        require(row.get("metadata_log_required") is True, "rule metadata log required must be true", errors)
        require(row.get("public_safe_template_only") is True, "rule public-safe template flag must be true", errors)
        require(row.get("metadata_target") == METADATA_RULES_PATH.as_posix(), "rule metadata target mismatch", errors)
        require(row.get("evidence_ref") == RULE_LOCK_PATH.as_posix(), "rule evidence ref mismatch", errors)
        _require_false_keys(
            row,
            (
                "full_report_body_allowed",
                "report_attachment_allowed",
                "raw_payload_allowed",
                "recipient_address_plaintext_allowed",
                "external_connector_required",
                "real_delivery_allowed",
            ),
            "rule_lock",
            errors,
        )


def _check_event_logs(rows: list[dict[str, Any]], errors: list[str]) -> None:
    required = set(REQUIRED_V014_NOTIFICATION_TRIGGERS)
    require(len(rows) == 3, "notification event count must be 3", errors)
    require({str(row.get("trigger_type")) for row in rows} == required, "notification event triggers mismatch", errors)
    for row in rows:
        require(
            row.get("record_type") == "v014_s17_p2_notification_event_log",
            "event record type mismatch",
            errors,
        )
        require(row.get("project_id") == "KMFA", "event project_id mismatch", errors)
        require(row.get("stage_id") == "S17", "event stage_id mismatch", errors)
        require(row.get("phase_id") == "S17-P2", "event phase_id mismatch", errors)
        require(row.get("channel") == "email_reminder", "event channel mismatch", errors)
        require(row.get("append_only") is True, "event append_only must be true", errors)
        require(row.get("metadata_target") == METADATA_EVENTS_PATH.as_posix(), "event metadata target mismatch", errors)
        require(row.get("evidence_ref") == EVENT_LOG_PATH.as_posix(), "event evidence ref mismatch", errors)
        require(row.get("result_status") == "metadata_event_logged_only", "event result status mismatch", errors)
        _require_false_keys(
            row,
            (
                "raw_business_data_included",
                "full_report_body_included",
                "report_attachment_included",
                "recipient_address_plaintext_included",
                "real_notification_delivery_performed",
                "external_connector_invoked",
            ),
            "event_log",
            errors,
        )


def _check_dispatch_logs(rows: list[dict[str, Any]], event_rows: list[dict[str, Any]], errors: list[str]) -> None:
    required = set(REQUIRED_V014_NOTIFICATION_TRIGGERS)
    event_ids = {row.get("event_id") for row in event_rows}
    require(len(rows) == 3, "notification dispatch log count must be 3", errors)
    require({str(row.get("trigger_type")) for row in rows} == required, "dispatch triggers mismatch", errors)
    for row in rows:
        encoded = json.dumps(row, ensure_ascii=False, sort_keys=True)
        require("@" not in encoded, "dispatch log must not contain address plaintext", errors)
        require(
            row.get("record_type") == "v014_s17_p2_notification_dispatch_log",
            "dispatch record type mismatch",
            errors,
        )
        require(row.get("project_id") == "KMFA", "dispatch project_id mismatch", errors)
        require(row.get("stage_id") == "S17", "dispatch stage_id mismatch", errors)
        require(row.get("phase_id") == "S17-P2", "dispatch phase_id mismatch", errors)
        require(row.get("event_id") in event_ids, "dispatch event id must map to event log", errors)
        require(row.get("recipient_address_ref") == "role_ref_only", "dispatch address ref mismatch", errors)
        require(row.get("channel") == "email_reminder", "dispatch channel mismatch", errors)
        require(row.get("delivery_mode") == "metadata_outbox_only", "dispatch delivery mode mismatch", errors)
        require(row.get("delivery_status") == "metadata_logged_only", "dispatch delivery status mismatch", errors)
        require(row.get("result_status") == "metadata_logged_only", "dispatch result status mismatch", errors)
        require(row.get("append_only") is True, "dispatch append_only must be true", errors)
        require(row.get("metadata_target") == METADATA_DISPATCH_LOG_PATH.as_posix(), "dispatch metadata target mismatch", errors)
        require(row.get("evidence_ref") == DISPATCH_LOG_PATH.as_posix(), "dispatch evidence ref mismatch", errors)
        require(0 < len(str(row.get("body_summary", ""))) <= 120, "dispatch body summary length mismatch", errors)
        _require_false_keys(
            row,
            (
                "full_report_body_included",
                "report_attachment_included",
                "raw_payload_included",
                "recipient_address_plaintext_included",
                "external_connector_invoked",
                "real_notification_delivery_performed",
            ),
            "dispatch_log",
            errors,
        )


def validate_v014_s17_p2_notification_policy(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []
    manifest = read_json(manifest_path)
    rule_locks = read_jsonl(RULE_LOCK_PATH)
    event_logs = read_jsonl(EVENT_LOG_PATH)
    dispatch_logs = read_jsonl(DISPATCH_LOG_PATH)
    metadata_manifest = read_json(METADATA_MANIFEST_PATH)
    metadata_rules = read_jsonl(METADATA_RULES_PATH)
    metadata_events = read_jsonl(METADATA_EVENTS_PATH)
    metadata_dispatch_logs = read_jsonl(METADATA_DISPATCH_LOG_PATH)

    s17_p1 = validate_s17_p1_dependency()
    legacy_manifest, legacy_rules, legacy_events, legacy_logs = validate_legacy_s17_p2_artifacts()
    baseline = load_v14_taskpack_baseline()

    require(manifest.get("schema_version") == SCHEMA_VERSION, "manifest schema mismatch", errors)
    require(manifest.get("project_id") == "KMFA", "project_id mismatch", errors)
    require(manifest.get("version") == "0.1.4", "version mismatch", errors)
    require(manifest.get("stage_id") == "S17", "stage_id must be S17", errors)
    require(manifest.get("phase_id") == "S17-P2", "phase_id must be S17-P2", errors)
    require(manifest.get("phase_scope") == PHASE_SCOPE, "phase scope mismatch", errors)
    require(manifest.get("task_id") == TASK_ID, "task id mismatch", errors)
    require(manifest.get("acceptance_ids") == [ACCEPTANCE_ID], "acceptance id mismatch", errors)
    require(manifest.get("completed_task_ids") == ["S17P2T01", "S17P2T02", "S17P2T03"], "tasks mismatch", errors)
    require(
        manifest.get("status") == "completed_validated_local_only_no_go_upload_deferred_notification_policy_locked",
        "status mismatch",
        errors,
    )
    require(manifest.get("s17_p1_dependency_validated") is True, "S17-P1 dependency flag mismatch", errors)
    require(
        manifest.get("s17_p1_dependency_task_id") == s17_p1["task_id"],
        "S17-P1 dependency task id mismatch",
        errors,
    )
    require(
        manifest.get("historical_s17_p2_public_safe_baseline_validated") is True,
        "historical S17-P2 baseline flag mismatch",
        errors,
    )
    require(
        manifest.get("historical_s17_p2_policy_version") == legacy_manifest["policy_version"],
        "historical S17-P2 policy version mismatch",
        errors,
    )
    require(tuple(manifest.get("required_notification_triggers", [])) == REQUIRED_V014_NOTIFICATION_TRIGGERS, "required triggers mismatch", errors)
    require(len(legacy_rules) == 3, "legacy rule count mismatch", errors)
    require(len(legacy_events) == 3, "legacy event count mismatch", errors)
    require(len(legacy_logs) == 3, "legacy dispatch log count mismatch", errors)
    require(baseline.get("roadmap_includes_s17_p2_requirements") is True, "v1.4 roadmap baseline mismatch", errors)
    require(
        baseline.get("taskpack_includes_notification_safety_boundary") is True,
        "v1.4 taskpack baseline mismatch",
        errors,
    )

    progress = manifest.get("stage17_phase_progress", {})
    require(progress.get("completed_phase_count") == 2, "completed phase count mismatch", errors)
    require(progress.get("total_phase_count") == 3, "total phase count mismatch", errors)
    require(progress.get("derived_percent_bps") == 6667, "derived percent bps mismatch", errors)
    require(progress.get("derived_percent_label") == "66.67%", "derived percent label mismatch", errors)
    require(progress.get("s17_p1_performed") is True, "S17-P1 must be true", errors)
    require(progress.get("s17_p2_performed") is True, "S17-P2 must be true", errors)
    require(progress.get("s17_p3_performed") is False, "S17-P3 must be false", errors)
    require(progress.get("stage17_review_performed") is False, "Stage 17 review must be false", errors)

    summary = manifest.get("notification_policy_summary", {})
    expected_summary = {
        "notification_rule_count": 3,
        "notification_event_count": 3,
        "notification_dispatch_log_count": 3,
        "trigger_type_count": 3,
        "required_trigger_count": 3,
        "metadata_outbox_log_count": 3,
        "real_notification_delivery_count": 0,
        "full_report_email_body_count": 0,
        "report_attachment_count": 0,
        "recipient_address_plaintext_count": 0,
        "external_connector_count": 0,
        "formal_report_count": 0,
        "business_decision_basis_count": 0,
        "business_execution_count": 0,
        "raw_inbox_access_count": 0,
        "report_grade_visible": "D",
    }
    for key, expected in expected_summary.items():
        require(summary.get(key) == expected, f"summary {key} must be {expected!r}", errors)

    quality = manifest.get("quality_gate", {})
    for key in QUALITY_TRUE_KEYS:
        require(quality.get(key) is True, f"quality_gate {key} must be true", errors)
    for key in QUALITY_FALSE_KEYS:
        require(quality.get(key) is False, f"quality_gate {key} must be false", errors)
    require(quality.get("current_report_grade") == "D", "current report grade mismatch", errors)
    require(quality.get("release_permission") == "blocked", "release permission mismatch", errors)

    boundaries = manifest.get("phase_boundaries", {})
    for key in PHASE_TRUE_KEYS:
        require(boundaries.get(key) is True, f"phase_boundaries {key} must be true", errors)
    for key in PHASE_FALSE_KEYS:
        require(boundaries.get(key) is False, f"phase_boundaries {key} must be false", errors)

    raw = manifest.get("raw_data_boundary", {})
    for key in RAW_BOUNDARY_FALSE_KEYS:
        require(raw.get(key) is False, f"raw boundary {key} must be false", errors)

    safety = manifest.get("public_repo_safety", {})
    for key in PUBLIC_SAFETY_FALSE_KEYS:
        require(safety.get(key) is False, f"public safety {key} must be false", errors)

    upload = manifest.get("github_upload", {})
    require(upload.get("github_upload_performed") is False, "GitHub upload must be false", errors)
    require(upload.get("github_upload_ready_next_gate") is False, "GitHub upload ready gate must be false", errors)
    require(
        upload.get("github_upload_deferred_until_v014_stage1_18_complete") is True,
        "GitHub upload deferral flag must be true",
        errors,
    )
    require(upload.get("github_upload_status") == "not_uploaded_deferred_until_v014_stage1_18_complete", "upload status mismatch", errors)
    require(manifest.get("next_phase") == NEXT_PHASE, "next phase mismatch", errors)
    require(manifest.get("next_required_step") == NEXT_REQUIRED_STEP, "next required step mismatch", errors)
    require(re.match(r"^[0-9a-f]{40}$", str(manifest.get("git_head"))), "git head must be a full SHA", errors)
    require(manifest.get("branch") == git_output(["branch", "--show-current"]), "branch mismatch", errors)

    require(metadata_manifest == manifest, "metadata manifest must match machine manifest", errors)
    _check_jsonl_equal(rule_locks, metadata_rules, "notification rules", errors)
    _check_jsonl_equal(event_logs, metadata_events, "notification events", errors)
    _check_jsonl_equal(dispatch_logs, metadata_dispatch_logs, "notification dispatch logs", errors)
    _check_rule_locks(rule_locks, errors)
    _check_event_logs(event_logs, errors)
    _check_dispatch_logs(dispatch_logs, event_logs, errors)

    for path in (
        MANIFEST_PATH,
        RULE_LOCK_PATH,
        EVENT_LOG_PATH,
        DISPATCH_LOG_PATH,
        METADATA_MANIFEST_PATH,
        METADATA_RULES_PATH,
        METADATA_EVENTS_PATH,
        METADATA_DISPATCH_LOG_PATH,
        REPORT_PATH,
        TEST_RESULTS_PATH,
        RISK_REGISTER_PATH,
        ROLLBACK_PATH,
    ):
        check_public_evidence_text(path, errors)

    if errors:
        raise ValidationError("; ".join(errors))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args()
    manifest = validate_v014_s17_p2_notification_policy(args.manifest)
    summary = manifest["notification_policy_summary"]
    print(
        "PASS: KMFA v0.1.4 S17-P2 notification policy validated "
        f"(rules={summary['notification_rule_count']}, events={summary['notification_event_count']}, "
        f"dispatch_logs={summary['notification_dispatch_log_count']}, "
        f"delivery={summary['real_notification_delivery_count']}, "
        f"full_report_email_body={summary['full_report_email_body_count']}, "
        f"attachments={summary['report_attachment_count']}, "
        f"external_connector={summary['external_connector_count']}, "
        f"s17_p3={manifest['stage17_phase_progress']['s17_p3_performed']}, "
        f"github_upload={manifest['github_upload']['github_upload_performed']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
