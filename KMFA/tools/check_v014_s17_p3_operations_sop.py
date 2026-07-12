#!/usr/bin/env python3
"""Validate KMFA v0.1.4 S17-P3 operations SOP evidence."""

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

from KMFA.tools.v014_s17_p3_operations_sop import (  # noqa: E402
    ACCEPTANCE_ID,
    DRILL_LOG_PATH,
    KNOWLEDGE_INDEX_PATH,
    MANIFEST_PATH,
    METADATA_DRILL_LOG_PATH,
    METADATA_KNOWLEDGE_INDEX_PATH,
    METADATA_MANIFEST_PATH,
    METADATA_RUNBOOKS_PATH,
    NEXT_PHASE,
    NEXT_REQUIRED_STEP,
    PHASE_SCOPE,
    REPORT_PATH,
    REQUIRED_V014_DRILL_TYPES,
    REQUIRED_V014_KNOWLEDGE_ITEM_TYPES,
    REQUIRED_V014_RUNBOOK_TYPES,
    RISK_REGISTER_PATH,
    ROLLBACK_PATH,
    RUNBOOK_LOCK_PATH,
    SCHEMA_VERSION,
    TASK_ID,
    TEST_RESULTS_PATH,
    _phase_boundaries,
    _public_repo_safety,
    _quality_gate,
    _raw_boundary,
    load_v14_taskpack_baseline,
    validate_legacy_s17_p3_artifacts,
    validate_s17_p2_dependency,
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


def _check_runbooks(rows: list[dict[str, Any]], errors: list[str]) -> None:
    required = set(REQUIRED_V014_RUNBOOK_TYPES)
    require(len(rows) == 4, "operation runbook count must be 4", errors)
    require({str(row.get("runbook_type")) for row in rows} == required, "runbook types mismatch", errors)
    for row in rows:
        runbook_type = str(row.get("runbook_type"))
        require(row.get("record_type") == "v014_s17_p3_operation_runbook_lock", "runbook record type mismatch", errors)
        require(row.get("project_id") == "KMFA", "runbook project_id mismatch", errors)
        require(row.get("stage_id") == "S17", "runbook stage_id mismatch", errors)
        require(row.get("phase_id") == "S17-P3", "runbook phase_id mismatch", errors)
        require(row.get("task_id") == "S17P3T01", "runbook task id mismatch", errors)
        require(row.get("execution_mode") == "manual_sop_only", "runbook execution mode mismatch", errors)
        require(row.get("metadata_target") == METADATA_RUNBOOKS_PATH.as_posix(), "runbook metadata target mismatch", errors)
        require(row.get("evidence_ref") == RUNBOOK_LOCK_PATH.as_posix(), "runbook evidence ref mismatch", errors)
        require(row.get("append_only") is True, "runbook append_only must be true", errors)
        require(row.get("precheck_required") is True, "runbook precheck must be true", errors)
        require(runbook_type in str(row.get("runbook_id")), "runbook id must include type", errors)
        for key in ("precheck_ref", "primary_step_ref", "rollback_step_ref", "source_baseline_ref"):
            require(bool(row.get(key)), f"runbook {key} required", errors)
        _require_false_keys(
            row,
            (
                "raw_business_data_required",
                "private_document_required",
                "live_connector_required",
                "external_service_required",
                "production_restore_allowed",
                "business_execution_allowed",
                "formal_report_release_allowed",
                "stage_review_allowed",
                "github_upload_allowed",
            ),
            "runbook",
            errors,
        )


def _check_knowledge_items(rows: list[dict[str, Any]], errors: list[str]) -> None:
    required = set(REQUIRED_V014_KNOWLEDGE_ITEM_TYPES)
    require(len(rows) == 2, "knowledge item count must be 2", errors)
    require({str(row.get("item_type")) for row in rows} == required, "knowledge item types mismatch", errors)
    for row in rows:
        item_type = str(row.get("item_type"))
        require(
            row.get("record_type") == "v014_s17_p3_operations_knowledge_index_lock",
            "knowledge record type mismatch",
            errors,
        )
        require(row.get("project_id") == "KMFA", "knowledge project_id mismatch", errors)
        require(row.get("stage_id") == "S17", "knowledge stage_id mismatch", errors)
        require(row.get("phase_id") == "S17-P3", "knowledge phase_id mismatch", errors)
        require(row.get("task_id") == "S17P3T02", "knowledge task id mismatch", errors)
        require(row.get("storage_mode") == "public_safe_index_only", "knowledge storage mode mismatch", errors)
        require(row.get("metadata_target") == METADATA_KNOWLEDGE_INDEX_PATH.as_posix(), "knowledge metadata target mismatch", errors)
        require(row.get("evidence_ref") == KNOWLEDGE_INDEX_PATH.as_posix(), "knowledge evidence ref mismatch", errors)
        require(row.get("append_only") is True, "knowledge append_only must be true", errors)
        require(item_type in str(row.get("knowledge_item_id")), "knowledge id must include type", errors)
        require(bool(row.get("owner_role")), "knowledge owner role required", errors)
        require(bool(row.get("knowledge_ref")), "knowledge ref required", errors)
        _require_false_keys(
            row,
            (
                "private_document_committed",
                "raw_business_data_committed",
                "credential_material_committed",
                "business_decision_basis_allowed",
                "external_service_required",
                "production_restore_allowed",
                "github_upload_allowed",
            ),
            "knowledge",
            errors,
        )


def _check_drill_logs(rows: list[dict[str, Any]], errors: list[str]) -> None:
    required = set(REQUIRED_V014_DRILL_TYPES)
    require(len(rows) == 2, "drill log count must be 2", errors)
    require({str(row.get("drill_type")) for row in rows} == required, "drill types mismatch", errors)
    for row in rows:
        drill_type = str(row.get("drill_type"))
        require(row.get("record_type") == "v014_s17_p3_operations_drill_log", "drill record type mismatch", errors)
        require(row.get("project_id") == "KMFA", "drill project_id mismatch", errors)
        require(row.get("stage_id") == "S17", "drill stage_id mismatch", errors)
        require(row.get("phase_id") == "S17-P3", "drill phase_id mismatch", errors)
        require(row.get("task_id") == "S17P3T03", "drill task id mismatch", errors)
        require(row.get("execution_mode") == "metadata_drill_only", "drill execution mode mismatch", errors)
        require(row.get("result_status") == "simulated_passed", "drill result status mismatch", errors)
        require(row.get("metadata_target") == METADATA_DRILL_LOG_PATH.as_posix(), "drill metadata target mismatch", errors)
        require(row.get("evidence_ref") == DRILL_LOG_PATH.as_posix(), "drill evidence ref mismatch", errors)
        require(row.get("append_only") is True, "drill append_only must be true", errors)
        require(drill_type in str(row.get("drill_id")), "drill id must include type", errors)
        require(bool(row.get("scenario_ref")), "drill scenario ref required", errors)
        require(bool(row.get("recovery_evidence_ref")), "drill recovery evidence ref required", errors)
        _require_false_keys(
            row,
            (
                "production_restore_executed",
                "raw_business_data_required",
                "private_document_required",
                "external_service_called",
                "live_connector_called",
                "business_execution_allowed",
                "github_upload_allowed",
            ),
            "drill",
            errors,
        )


def validate_v014_s17_p3_operations_sop(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []
    manifest = read_json(manifest_path)
    runbooks = read_jsonl(RUNBOOK_LOCK_PATH)
    knowledge_items = read_jsonl(KNOWLEDGE_INDEX_PATH)
    drill_logs = read_jsonl(DRILL_LOG_PATH)
    metadata_manifest = read_json(METADATA_MANIFEST_PATH)
    metadata_runbooks = read_jsonl(METADATA_RUNBOOKS_PATH)
    metadata_knowledge = read_jsonl(METADATA_KNOWLEDGE_INDEX_PATH)
    metadata_drills = read_jsonl(METADATA_DRILL_LOG_PATH)

    s17_p2 = validate_s17_p2_dependency()
    legacy_manifest, legacy_runbooks, legacy_items, legacy_drills = validate_legacy_s17_p3_artifacts()
    baseline = load_v14_taskpack_baseline()

    require(manifest.get("schema_version") == SCHEMA_VERSION, "manifest schema mismatch", errors)
    require(manifest.get("project_id") == "KMFA", "project_id mismatch", errors)
    require(manifest.get("version") == "0.1.4", "version mismatch", errors)
    require(manifest.get("stage_id") == "S17", "stage_id must be S17", errors)
    require(manifest.get("phase_id") == "S17-P3", "phase_id must be S17-P3", errors)
    require(manifest.get("phase_scope") == PHASE_SCOPE, "phase scope mismatch", errors)
    require(manifest.get("task_id") == TASK_ID, "task id mismatch", errors)
    require(manifest.get("acceptance_ids") == [ACCEPTANCE_ID], "acceptance id mismatch", errors)
    require(manifest.get("completed_task_ids") == ["S17P3T01", "S17P3T02", "S17P3T03"], "tasks mismatch", errors)
    require(
        manifest.get("status") == "completed_validated_local_only_no_go_upload_deferred_operations_sop_locked",
        "status mismatch",
        errors,
    )
    require(manifest.get("s17_p2_dependency_validated") is True, "S17-P2 dependency flag mismatch", errors)
    require(manifest.get("s17_p2_dependency_task_id") == s17_p2["task_id"], "S17-P2 dependency task id mismatch", errors)
    require(
        manifest.get("historical_s17_p3_public_safe_baseline_validated") is True,
        "historical S17-P3 baseline flag mismatch",
        errors,
    )
    require(
        manifest.get("historical_s17_p3_policy_version") == legacy_manifest["policy_version"],
        "historical S17-P3 policy version mismatch",
        errors,
    )
    require(tuple(manifest.get("required_runbook_types", [])) == REQUIRED_V014_RUNBOOK_TYPES, "required runbooks mismatch", errors)
    require(
        tuple(manifest.get("required_knowledge_item_types", [])) == REQUIRED_V014_KNOWLEDGE_ITEM_TYPES,
        "required knowledge items mismatch",
        errors,
    )
    require(tuple(manifest.get("required_drill_types", [])) == REQUIRED_V014_DRILL_TYPES, "required drill types mismatch", errors)
    require(len(legacy_runbooks) == 4, "legacy runbook count mismatch", errors)
    require(len(legacy_items) == 2, "legacy knowledge count mismatch", errors)
    require(len(legacy_drills) == 2, "legacy drill count mismatch", errors)
    require(baseline.get("roadmap_includes_s17_p3_requirements") is True, "v1.4 roadmap baseline mismatch", errors)
    require(
        baseline.get("taskpack_includes_operations_safety_boundary") is True,
        "v1.4 taskpack baseline mismatch",
        errors,
    )

    progress = manifest.get("stage17_phase_progress", {})
    require(progress.get("completed_phase_count") == 3, "completed phase count mismatch", errors)
    require(progress.get("total_phase_count") == 3, "total phase count mismatch", errors)
    require(progress.get("derived_percent_bps") == 10000, "derived percent bps mismatch", errors)
    require(progress.get("derived_percent_label") == "100.00%", "derived percent label mismatch", errors)
    require(progress.get("s17_p1_performed") is True, "S17-P1 must be true", errors)
    require(progress.get("s17_p2_performed") is True, "S17-P2 must be true", errors)
    require(progress.get("s17_p3_performed") is True, "S17-P3 must be true", errors)
    require(progress.get("stage17_review_performed") is False, "Stage 17 review must be false", errors)

    summary = manifest.get("operations_sop_summary", {})
    expected_summary = {
        "operation_runbook_count": 4,
        "knowledge_item_count": 2,
        "drill_log_count": 2,
        "runbook_type_count": 4,
        "knowledge_item_type_count": 2,
        "drill_type_count": 2,
        "production_restore_count": 0,
        "external_service_call_count": 0,
        "live_connector_call_count": 0,
        "business_execution_count": 0,
        "raw_inbox_access_count": 0,
        "formal_report_count": 0,
        "app_reinstall_count": 0,
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
    _check_jsonl_equal(runbooks, metadata_runbooks, "operation runbooks", errors)
    _check_jsonl_equal(knowledge_items, metadata_knowledge, "knowledge index", errors)
    _check_jsonl_equal(drill_logs, metadata_drills, "drill logs", errors)
    _check_runbooks(runbooks, errors)
    _check_knowledge_items(knowledge_items, errors)
    _check_drill_logs(drill_logs, errors)

    for path in (
        MANIFEST_PATH,
        RUNBOOK_LOCK_PATH,
        KNOWLEDGE_INDEX_PATH,
        DRILL_LOG_PATH,
        METADATA_MANIFEST_PATH,
        METADATA_RUNBOOKS_PATH,
        METADATA_KNOWLEDGE_INDEX_PATH,
        METADATA_DRILL_LOG_PATH,
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
    manifest = validate_v014_s17_p3_operations_sop(args.manifest)
    summary = manifest["operations_sop_summary"]
    print(
        "PASS: KMFA v0.1.4 S17-P3 operations SOP validated "
        f"(runbooks={summary['operation_runbook_count']}, knowledge={summary['knowledge_item_count']}, "
        f"drills={summary['drill_log_count']}, production_restore={summary['production_restore_count']}, "
        f"external_service={summary['external_service_call_count']}, business_execution={summary['business_execution_count']}, "
        f"raw_inbox_access={summary['raw_inbox_access_count']}, "
        f"stage17_review={manifest['stage17_phase_progress']['stage17_review_performed']}, "
        f"github_upload={manifest['github_upload']['github_upload_performed']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
