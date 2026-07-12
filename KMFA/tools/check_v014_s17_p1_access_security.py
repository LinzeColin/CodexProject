#!/usr/bin/env python3
"""Validate KMFA v0.1.4 S17-P1 access and security evidence."""

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

from KMFA.tools.v014_s17_p1_access_security import (  # noqa: E402
    ACCEPTANCE_ID,
    AUDIT_POLICY_LOCK_PATH,
    MANIFEST_PATH,
    NEXT_PHASE,
    NEXT_REQUIRED_STEP,
    PHASE_SCOPE,
    REPORT_PATH,
    RISK_REGISTER_PATH,
    ROLE_PERMISSION_LOCK_PATH,
    ROLLBACK_PATH,
    SCHEMA_VERSION,
    SENSITIVE_POLICY_LOCK_PATH,
    TASK_ID,
    TEST_RESULTS_PATH,
    _phase_boundaries,
    _public_repo_safety,
    _quality_gate,
    _raw_boundary,
    load_v14_taskpack_baseline,
    validate_legacy_s17_p1_artifacts,
    validate_s16_stage_review_dependency,
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
    "-----" "BEGIN",
    "s" "k-",
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


def _check_role_locks(rows: list[dict[str, Any]], errors: list[str]) -> None:
    require(len(rows) == 4, "role lock count must be 4", errors)
    expected_roles = {"management", "finance", "reviewer", "readonly"}
    require({str(row.get("role_id")) for row in rows} == expected_roles, "role ids mismatch", errors)
    for row in rows:
        role = str(row.get("role_id"))
        require(row.get("record_type") == "v014_s17_p1_role_permission_lock", "role record type mismatch", errors)
        require(row.get("project_id") == "KMFA", "role project_id mismatch", errors)
        require(row.get("stage_id") == "S17", "role stage_id mismatch", errors)
        require(row.get("phase_id") == "S17-P1", "role phase_id mismatch", errors)
        require(int(row.get("allowed_public_safe_action_count", 0)) >= 2, "role allowed action count mismatch", errors)
        require(row.get("audit_required") is True, "role audit_required must be true", errors)
        require(row.get("least_privilege_applied") is True, "role least privilege must be true", errors)
        if role == "readonly":
            require(row.get("max_write_scope") == "none", "readonly max_write_scope mismatch", errors)
        else:
            require(row.get("max_write_scope") == "metadata_only", f"{role} max_write_scope mismatch", errors)
        _require_false_keys(
            row,
            (
                "raw_business_data_access_in_public_repo",
                "sensitive_file_public_commit_allowed",
                "credential_access_allowed",
                "business_execution_allowed",
                "bypass_quality_gate_allowed",
                "notification_body_report_allowed",
            ),
            "role_lock",
            errors,
        )


def _check_sensitive_locks(rows: list[dict[str, Any]], errors: list[str]) -> None:
    require(len(rows) == 15, "sensitive policy lock count must be 15", errors)
    for row in rows:
        require(
            row.get("record_type") == "v014_s17_p1_sensitive_policy_lock",
            "sensitive policy record type mismatch",
            errors,
        )
        require(row.get("project_id") == "KMFA", "sensitive policy project_id mismatch", errors)
        require(row.get("stage_id") == "S17", "sensitive policy stage_id mismatch", errors)
        require(row.get("phase_id") == "S17-P1", "sensitive policy phase_id mismatch", errors)
        _require_false_keys(
            row,
            ("public_repo_allowed", "git_upload_allowed", "value_plaintext_allowed"),
            "sensitive_policy_lock",
            errors,
        )
        require(
            row.get("metadata_hash_or_ref_only_allowed") is True,
            "sensitive policy hash/ref flag must be true",
            errors,
        )
        require(
            row.get("handling") == "private_storage_or_hash_only_metadata",
            "sensitive policy handling mismatch",
            errors,
        )
        require(int(row.get("enforcement_control_count", 0)) >= 3, "enforcement control count mismatch", errors)


def _check_audit_locks(rows: list[dict[str, Any]], errors: list[str]) -> None:
    require(len(rows) == 5, "audit policy lock count must be 5", errors)
    expected_actions = {"import", "processing", "report", "export", "notification"}
    require({str(row.get("action_type")) for row in rows} == expected_actions, "audit action types mismatch", errors)
    for row in rows:
        action = str(row.get("action_type"))
        require(row.get("record_type") == "v014_s17_p1_audit_policy_lock", "audit record type mismatch", errors)
        require(row.get("project_id") == "KMFA", "audit project_id mismatch", errors)
        require(row.get("stage_id") == "S17", "audit stage_id mismatch", errors)
        require(row.get("phase_id") == "S17-P1", "audit phase_id mismatch", errors)
        for key in ("append_only", "requires_actor_role", "requires_event_time", "requires_evidence_ref"):
            require(row.get(key) is True, f"audit {key} must be true", errors)
        _require_false_keys(
            row,
            ("raw_payload_allowed", "private_document_allowed", "business_value_plaintext_allowed", "sends_full_report_body"),
            "audit_policy_lock",
            errors,
        )
        if action == "notification":
            require(
                row.get("delivery_scope") == "log_policy_only_s17_p2_not_implemented",
                "notification delivery scope mismatch",
                errors,
            )


def validate_v014_s17_p1_access_security(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []
    manifest = read_json(manifest_path)
    role_locks = read_jsonl(ROLE_PERMISSION_LOCK_PATH)
    sensitive_locks = read_jsonl(SENSITIVE_POLICY_LOCK_PATH)
    audit_locks = read_jsonl(AUDIT_POLICY_LOCK_PATH)

    s16_review = validate_s16_stage_review_dependency()
    legacy_manifest, legacy_roles, legacy_sensitive, legacy_audit = validate_legacy_s17_p1_artifacts()
    baseline = load_v14_taskpack_baseline()

    require(manifest.get("schema_version") == SCHEMA_VERSION, "manifest schema mismatch", errors)
    require(manifest.get("project_id") == "KMFA", "project_id mismatch", errors)
    require(manifest.get("version") == "0.1.4", "version mismatch", errors)
    require(manifest.get("stage_id") == "S17", "stage_id must be S17", errors)
    require(manifest.get("phase_id") == "S17-P1", "phase_id must be S17-P1", errors)
    require(manifest.get("phase_scope") == PHASE_SCOPE, "phase scope mismatch", errors)
    require(manifest.get("task_id") == TASK_ID, "task id mismatch", errors)
    require(manifest.get("acceptance_ids") == [ACCEPTANCE_ID], "acceptance id mismatch", errors)
    require(manifest.get("completed_task_ids") == ["S17P1T01", "S17P1T02", "S17P1T03"], "tasks mismatch", errors)
    require(
        manifest.get("status") == "completed_validated_local_only_no_go_upload_deferred_access_security_locked",
        "status mismatch",
        errors,
    )
    require(manifest.get("s16_stage_review_dependency_validated") is True, "S16 review dependency flag mismatch", errors)
    require(
        manifest.get("historical_s17_p1_public_safe_baseline_validated") is True,
        "historical S17-P1 baseline flag mismatch",
        errors,
    )
    require(s16_review.get("next_phase") == "S17-P1", "Stage 16 review did not route to S17-P1", errors)
    require(legacy_manifest.get("stage_phase") == "S17-P1", "legacy S17-P1 manifest mismatch", errors)
    require(len(legacy_roles) == 4, "legacy role count mismatch", errors)
    require(len(legacy_sensitive) == 15, "legacy sensitive policy count mismatch", errors)
    require(len(legacy_audit) == 5, "legacy audit policy count mismatch", errors)
    require(baseline.get("roadmap_includes_s17_p1_requirements") is True, "v1.4 roadmap baseline mismatch", errors)
    require(
        baseline.get("taskpack_includes_access_security_audit_boundary") is True,
        "v1.4 taskpack baseline mismatch",
        errors,
    )

    progress = manifest.get("stage17_phase_progress", {})
    require(progress.get("completed_phase_count") == 1, "completed phase count mismatch", errors)
    require(progress.get("total_phase_count") == 3, "total phase count mismatch", errors)
    require(progress.get("derived_percent_bps") == 3333, "derived percent bps mismatch", errors)
    require(progress.get("derived_percent_label") == "33.33%", "derived percent label mismatch", errors)
    require(progress.get("s17_p1_performed") is True, "S17-P1 must be true", errors)
    require(progress.get("s17_p2_performed") is False, "S17-P2 must be false", errors)
    require(progress.get("s17_p3_performed") is False, "S17-P3 must be false", errors)
    require(progress.get("stage17_review_performed") is False, "Stage 17 review must be false", errors)

    summary = manifest.get("access_security_summary", {})
    expected_summary = {
        "role_count": 4,
        "sensitive_policy_category_count": 15,
        "audit_action_type_count": 5,
        "notification_delivery_count": 0,
        "full_report_email_body_count": 0,
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

    _check_role_locks(role_locks, errors)
    _check_sensitive_locks(sensitive_locks, errors)
    _check_audit_locks(audit_locks, errors)

    for path in (
        MANIFEST_PATH,
        ROLE_PERMISSION_LOCK_PATH,
        SENSITIVE_POLICY_LOCK_PATH,
        AUDIT_POLICY_LOCK_PATH,
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
    manifest = validate_v014_s17_p1_access_security(args.manifest)
    summary = manifest["access_security_summary"]
    print(
        "PASS: KMFA v0.1.4 S17-P1 access/security validated "
        f"(roles={summary['role_count']}, sensitive_categories={summary['sensitive_policy_category_count']}, "
        f"audit_actions={summary['audit_action_type_count']}, notification_delivery={summary['notification_delivery_count']}, "
        f"external_connector={summary['external_connector_count']}, business_execution={summary['business_execution_count']}, "
        f"s17_p2={manifest['stage17_phase_progress']['s17_p2_performed']}, "
        f"github_upload={manifest['github_upload']['github_upload_performed']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
