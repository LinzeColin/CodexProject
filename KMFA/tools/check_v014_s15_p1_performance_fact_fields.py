#!/usr/bin/env python3
"""Validate KMFA v0.1.4 S15-P1 performance fact field evidence."""

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

from KMFA.tools.v014_s15_p1_performance_fact_fields import (  # noqa: E402
    ACCEPTANCE_ID,
    FIELD_BINDINGS_PATH,
    FIELD_DEFINITIONS_PATH,
    MANIFEST_PATH,
    MANUAL_REVIEW_FIELDS_PATH,
    NEXT_REQUIRED_STEP,
    PHASE_SCOPE,
    REPORT_PATH,
    REQUIRED_MANUAL_REVIEW_FIELDS,
    REQUIRED_PERFORMANCE_FACT_FIELDS,
    RISK_REGISTER_PATH,
    ROLLBACK_PATH,
    SCHEMA_VERSION,
    TASK_ID,
    TEST_RESULTS_PATH,
    _phase_boundaries,
    _public_repo_safety,
    _quality_gate,
    _raw_boundary,
    load_v14_taskpack_baseline,
    validate_legacy_s15_p1_artifacts,
    validate_stage14_review_dependency,
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
    "bank_statement",
    "contract_full_text",
    "salary_detail",
    "tax_filing_material",
    "tax_filing_record",
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


def validate_v014_s15_p1_performance_fact_fields(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []
    manifest = read_json(manifest_path)
    definitions = read_jsonl(FIELD_DEFINITIONS_PATH)
    bindings = read_jsonl(FIELD_BINDINGS_PATH)
    manual_fields = read_jsonl(MANUAL_REVIEW_FIELDS_PATH)
    stage14 = validate_stage14_review_dependency()
    legacy_manifest, legacy_defs, legacy_bindings, legacy_manual = validate_legacy_s15_p1_artifacts()
    baseline = load_v14_taskpack_baseline()

    require(manifest.get("schema_version") == SCHEMA_VERSION, "manifest schema mismatch", errors)
    require(manifest.get("project_id") == "KMFA", "project_id mismatch", errors)
    require(manifest.get("version") == "0.1.4", "version mismatch", errors)
    require(manifest.get("stage_id") == "S15", "stage_id must be S15", errors)
    require(manifest.get("phase_id") == "S15-P1", "phase_id must be S15-P1", errors)
    require(manifest.get("phase_scope") == PHASE_SCOPE, "phase scope mismatch", errors)
    require(manifest.get("task_id") == TASK_ID, "task_id mismatch", errors)
    require(manifest.get("acceptance_ids") == [ACCEPTANCE_ID], "acceptance id mismatch", errors)
    require(manifest.get("completed_task_ids") == ["S15P1T01", "S15P1T02", "S15P1T03"], "tasks mismatch", errors)
    require(
        manifest.get("status") == "completed_validated_local_only_no_go_upload_deferred_performance_fact_fields_locked",
        "status mismatch",
        errors,
    )
    require(manifest.get("stage14_review_dependency_validated") is True, "Stage 14 dependency flag mismatch", errors)
    require(stage14.get("next_phase") == "S15-P1", "Stage 14 review did not route to S15-P1", errors)
    require(
        manifest.get("historical_s15_p1_public_safe_baseline_validated") is True,
        "historical S15-P1 baseline flag mismatch",
        errors,
    )
    require(len(legacy_defs) == 6, "legacy definitions count mismatch", errors)
    require(len(legacy_bindings) == 6, "legacy bindings count mismatch", errors)
    require(len(legacy_manual) == 4, "legacy manual review count mismatch", errors)
    require(legacy_manifest.get("summary", {}).get("field_definition_count") == 6, "legacy summary mismatch", errors)
    require(baseline.get("roadmap_includes_s15_p1_requirements") is True, "v1.4 roadmap baseline mismatch", errors)

    progress = manifest.get("stage15_phase_progress", {})
    require(progress.get("completed_phase_count") == 1, "completed phase count mismatch", errors)
    require(progress.get("total_phase_count") == 3, "total phase count mismatch", errors)
    require(progress.get("derived_percent_bps") == 3333, "derived percent bps mismatch", errors)
    require(progress.get("derived_percent_label") == "33.33%", "derived percent label mismatch", errors)
    require(progress.get("s15_p1_performed") is True, "S15-P1 must be performed", errors)
    require(progress.get("s15_p2_performed") is False, "S15-P2 must be false", errors)
    require(progress.get("s15_p3_performed") is False, "S15-P3 must be false", errors)
    require(progress.get("stage15_review_performed") is False, "Stage 15 review must be false", errors)

    summary = manifest.get("performance_fact_fields_summary", {})
    require(summary.get("required_performance_fact_fields") == list(REQUIRED_PERFORMANCE_FACT_FIELDS), "field list mismatch", errors)
    require(summary.get("required_manual_review_fields") == list(REQUIRED_MANUAL_REVIEW_FIELDS), "manual field list mismatch", errors)
    expected_summary = {
        "field_definition_count": 6,
        "field_binding_count": 6,
        "manual_review_field_count": 4,
        "project_cost_fact_record_count": 4,
        "margin_record_count": 4,
        "collection_priority_item_count": 4,
        "invoice_issue_candidate_count": 3,
        "cross_table_difference_count": 4,
        "performance_fact_table_count": 0,
        "abnormal_project_review_list_count": 0,
        "salary_calculation_count": 0,
        "bonus_approval_count": 0,
        "payroll_export_count": 0,
        "final_payment_count": 0,
        "report_grade_visible": "D",
    }
    for key, expected in expected_summary.items():
        require(summary.get(key) == expected, f"summary {key} must be {expected}", errors)

    require([row.get("field_key") for row in definitions] == list(REQUIRED_PERFORMANCE_FACT_FIELDS), "definition order mismatch", errors)
    require([row.get("field_key") for row in bindings] == list(REQUIRED_PERFORMANCE_FACT_FIELDS), "binding order mismatch", errors)
    require([row.get("field_key") for row in manual_fields] == list(REQUIRED_MANUAL_REVIEW_FIELDS), "manual review order mismatch", errors)

    for row in definitions:
        field_key = row.get("field_key")
        require(row.get("phase_id") == "S15-P1", f"{field_key} definition phase mismatch", errors)
        require(row.get("manual_review_required") is (field_key in REQUIRED_MANUAL_REVIEW_FIELDS), f"{field_key} manual flag mismatch", errors)
        for false_key in (
            "public_numeric_values_allowed",
            "raw_business_values_allowed",
            "field_plaintext_allowed",
            "salary_calculation_allowed",
            "bonus_approval_allowed",
            "payroll_export_allowed",
            "final_payment_allowed",
        ):
            require(row.get(false_key) is False, f"{field_key} definition {false_key} must be false", errors)

    for row in bindings:
        field_key = row.get("field_key")
        require(row.get("phase_id") == "S15-P1", f"{field_key} binding phase mismatch", errors)
        require(row.get("project_cost_fact_binding", {}).get("required") is True, f"{field_key} project cost binding missing", errors)
        require(row.get("collection_fact_binding", {}).get("required") is True, f"{field_key} collection binding missing", errors)
        require(row.get("manual_review_required") is (field_key in REQUIRED_MANUAL_REVIEW_FIELDS), f"{field_key} binding manual flag mismatch", errors)
        if field_key in REQUIRED_MANUAL_REVIEW_FIELDS:
            require(str(row.get("manual_review_ref", "")).endswith(f"#{field_key}"), f"{field_key} manual ref mismatch", errors)
        else:
            require(row.get("manual_review_ref") is None, f"{field_key} manual ref must be null", errors)
        for false_key in (
            "raw_business_values_allowed",
            "public_numeric_values_allowed",
            "field_plaintext_allowed",
            "auto_fill_allowed",
            "formal_report_allowed",
            "business_decision_basis_allowed",
            "salary_calculation_allowed",
            "wage_calculation_allowed",
            "bonus_approval_allowed",
            "payroll_export_allowed",
            "final_payment_allowed",
            "payment_execution_allowed",
        ):
            require(row.get(false_key) is False, f"{field_key} binding {false_key} must be false", errors)

    for row in manual_fields:
        field_key = row.get("field_key")
        require(row.get("phase_id") == "S15-P1", f"{field_key} manual review phase mismatch", errors)
        require(row.get("manual_review_required") is True, f"{field_key} manual review required mismatch", errors)
        require(row.get("review_mode") == "owner_or_authorized_delegate_review_only", f"{field_key} review mode mismatch", errors)
        for false_key in (
            "auto_fill_allowed",
            "auto_calculation_allowed",
            "auto_approval_allowed",
            "salary_or_bonus_action_allowed",
            "s15_p2_review_list_created",
            "raw_business_values_allowed",
            "public_numeric_values_allowed",
            "field_plaintext_allowed",
        ):
            require(row.get(false_key) is False, f"{field_key} manual review {false_key} must be false", errors)

    for key in QUALITY_TRUE_KEYS:
        require(manifest.get("quality_gate", {}).get(key) is True, f"quality_gate.{key} must be true", errors)
    for key in QUALITY_FALSE_KEYS:
        require(manifest.get("quality_gate", {}).get(key) is False, f"quality_gate.{key} must be false", errors)
    require(manifest.get("quality_gate", {}).get("current_report_grade") == "D", "report grade mismatch", errors)
    require(manifest.get("quality_gate", {}).get("current_data_quality_grade") == "Q4", "data quality mismatch", errors)

    for key in PHASE_TRUE_KEYS:
        require(manifest.get("phase_boundaries", {}).get(key) is True, f"phase_boundaries.{key} must be true", errors)
    for key in PHASE_FALSE_KEYS:
        require(manifest.get("phase_boundaries", {}).get(key) is False, f"phase_boundaries.{key} must be false", errors)
    for key in RAW_BOUNDARY_FALSE_KEYS:
        require(manifest.get("raw_data_boundary", {}).get(key) is False, f"raw_data_boundary.{key} must be false", errors)
    for key in PUBLIC_SAFETY_FALSE_KEYS:
        require(manifest.get("public_repo_safety", {}).get(key) is False, f"public_repo_safety.{key} must be false", errors)

    upload = manifest.get("github_upload", {})
    require(upload.get("github_upload_performed") is False, "github upload must be false", errors)
    require(upload.get("github_upload_ready_next_gate") is False, "github ready gate must be false", errors)
    require(upload.get("github_upload_deferred_until_v014_stage1_18_complete") is True, "github deferred flag must be true", errors)

    for block in (
        "performance_fact_table_not_performed",
        "abnormal_project_review_list_not_performed",
        "salary_calculation_blocked",
        "bonus_approval_blocked",
        "payroll_export_blocked",
        "final_payment_blocked",
        "s15_p2_not_performed",
        "s15_p3_not_performed",
        "stage15_review_not_performed",
        "github_upload_deferred_until_v014_stage1_18_complete",
        "business_execution_blocked",
    ):
        require(block in manifest.get("hard_blocks", []), f"missing hard block {block}", errors)
    require(manifest.get("next_phase") == "S15-P2", "next phase mismatch", errors)
    require(manifest.get("next_required_step") == NEXT_REQUIRED_STEP, "next instruction mismatch", errors)
    require(manifest.get("branch") == git_output(["branch", "--show-current"]), "branch mismatch", errors)
    require(re.fullmatch(r"[0-9a-f]{40}", str(manifest.get("git_head", ""))) is not None, "git head shape mismatch", errors)

    for path in (
        MANIFEST_PATH,
        FIELD_DEFINITIONS_PATH,
        FIELD_BINDINGS_PATH,
        MANUAL_REVIEW_FIELDS_PATH,
        REPORT_PATH,
        TEST_RESULTS_PATH,
        RISK_REGISTER_PATH,
        ROLLBACK_PATH,
    ):
        check_public_evidence_text(path, errors)

    if errors:
        raise ValidationError("; ".join(errors))
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.4 S15-P1 performance fact field evidence.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args(argv)
    manifest = validate_v014_s15_p1_performance_fact_fields(args.manifest)
    summary = manifest["performance_fact_fields_summary"]
    print(
        "PASS: KMFA v0.1.4 S15-P1 performance fact fields validated "
        f"(fields={summary['field_definition_count']}, bindings={summary['field_binding_count']}, "
        f"manual_reviews={summary['manual_review_field_count']}, "
        "fact_table=false, salary=false, bonus=false, payroll=false, s15_p2=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
