#!/usr/bin/env python3
"""Validate KMFA v0.1.4 S15-P3 salary boundary evidence."""

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

from KMFA.tools.v014_s15_p3_salary_boundary import (  # noqa: E402
    ACCEPTANCE_ID,
    INTERFACE_CONTRACT_PATH,
    MANIFEST_PATH,
    NEXT_REQUIRED_STEP,
    PHASE_SCOPE,
    READINESS_DRAFT_PATH,
    REPORT_PATH,
    REQUIRED_PERFORMANCE_REVIEW_FIELDS,
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
    validate_legacy_s15_p3_artifacts,
    validate_s15_p2_dependency,
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
    "employee_name",
    "employee_id",
    "staff_name",
    "staff_id",
    "salary_amount",
    "wage_amount",
    "bonus_amount",
    "payroll_amount",
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


def validate_v014_s15_p3_salary_boundary(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []
    manifest = read_json(manifest_path)
    interface_contract = read_json(INTERFACE_CONTRACT_PATH)
    readiness_rows = read_jsonl(READINESS_DRAFT_PATH)
    s15_p2 = validate_s15_p2_dependency()
    legacy_manifest, legacy_interface, legacy_readiness_rows = validate_legacy_s15_p3_artifacts()
    baseline = load_v14_taskpack_baseline()

    require(manifest.get("schema_version") == SCHEMA_VERSION, "manifest schema mismatch", errors)
    require(manifest.get("project_id") == "KMFA", "project_id mismatch", errors)
    require(manifest.get("version") == "0.1.4", "version mismatch", errors)
    require(manifest.get("stage_id") == "S15", "stage_id must be S15", errors)
    require(manifest.get("phase_id") == "S15-P3", "phase_id must be S15-P3", errors)
    require(manifest.get("phase_scope") == PHASE_SCOPE, "phase scope mismatch", errors)
    require(manifest.get("task_id") == TASK_ID, "task_id mismatch", errors)
    require(manifest.get("acceptance_ids") == [ACCEPTANCE_ID], "acceptance id mismatch", errors)
    require(manifest.get("completed_task_ids") == ["S15P3T01", "S15P3T02", "S15P3T03"], "tasks mismatch", errors)
    require(
        manifest.get("status") == "completed_validated_local_only_no_go_upload_deferred_salary_boundary_locked",
        "status mismatch",
        errors,
    )
    require(manifest.get("s15_p2_dependency_validated") is True, "S15-P2 dependency flag mismatch", errors)
    require(s15_p2.get("next_phase") == "S15-P3", "S15-P2 did not route to S15-P3", errors)
    require(
        manifest.get("historical_s15_p3_public_safe_baseline_validated") is True,
        "historical S15-P3 baseline flag mismatch",
        errors,
    )
    require(legacy_manifest.get("summary", {}).get("fact_interface_contract_count") == 1, "legacy interface count mismatch", errors)
    require(len(legacy_readiness_rows) == 4, "legacy readiness row count mismatch", errors)
    require(legacy_interface.get("interface_status") == "reserved_contract_only", "legacy interface status mismatch", errors)
    require(legacy_manifest.get("summary", {}).get("salary_calculation_count") == 0, "legacy salary count mismatch", errors)
    require(baseline.get("roadmap_includes_s15_p3_requirements") is True, "v1.4 roadmap baseline mismatch", errors)

    progress = manifest.get("stage15_phase_progress", {})
    require(progress.get("completed_phase_count") == 3, "completed phase count mismatch", errors)
    require(progress.get("total_phase_count") == 3, "total phase count mismatch", errors)
    require(progress.get("derived_percent_bps") == 10000, "derived percent bps mismatch", errors)
    require(progress.get("derived_percent_label") == "100.00%", "derived percent label mismatch", errors)
    require(progress.get("s15_p1_performed") is True, "S15-P1 must be true", errors)
    require(progress.get("s15_p2_performed") is True, "S15-P2 must be true", errors)
    require(progress.get("s15_p3_performed") is True, "S15-P3 must be true", errors)
    require(progress.get("stage15_review_performed") is False, "Stage 15 review must be false", errors)

    summary = manifest.get("salary_boundary_summary", {})
    expected_summary = {
        "fact_output_interface_contract_count": 1,
        "future_salary_system_readiness_row_count": 4,
        "human_approval_boundary_count": 4,
        "pending_review_item_count": 16,
        "salary_calculation_count": 0,
        "wage_calculation_count": 0,
        "bonus_approval_count": 0,
        "payroll_export_count": 0,
        "final_compensation_decision_count": 0,
        "final_payment_count": 0,
        "payment_execution_count": 0,
        "report_grade_visible": "D",
    }
    for key, expected in expected_summary.items():
        require(summary.get(key) == expected, f"summary {key} must be {expected}", errors)

    require(
        interface_contract.get("schema_version") == "kmfa.v014_s15_p3.fact_output_interface_contract.v1",
        "interface schema mismatch",
        errors,
    )
    require(interface_contract.get("record_type") == "fact_output_interface_contract", "interface record type mismatch", errors)
    require(interface_contract.get("stage_id") == "S15" and interface_contract.get("phase_id") == "S15-P3", "interface phase mismatch", errors)
    require(interface_contract.get("interface_status") == "reserved_contract_only", "interface status mismatch", errors)
    require(interface_contract.get("fact_interface_fields") == list(REQUIRED_PERFORMANCE_REVIEW_FIELDS), "interface fields mismatch", errors)
    require(
        interface_contract.get("source_fact_table_ref")
        == "KMFA/stage_artifacts/V014_S15_P2_PERFORMANCE_REVIEW_LIST/machine/performance_fact_table.jsonl",
        "interface fact table ref mismatch",
        errors,
    )
    for false_key in (
        "api_endpoint_created",
        "file_export_created",
        "connector_enabled",
        "live_read_enabled",
        "scheduled_sync_enabled",
        "external_write_enabled",
        "raw_layer_write_allowed",
        "public_numeric_values_allowed",
        "automatic_compensation_decision_allowed",
        "automatic_payment_allowed",
    ):
        require(interface_contract.get(false_key) is False, f"interface {false_key} must be false", errors)
    for true_key in ("final_approval_must_be_human", "payment_release_must_be_human"):
        require(interface_contract.get(true_key) is True, f"interface {true_key} must be true", errors)

    require(len(readiness_rows) == 4, "readiness draft row count must be 4", errors)
    expected_ids = [f"V014-S15P3-READ-{index:03d}" for index in range(1, 5)]
    require([row.get("readiness_row_id") for row in readiness_rows] == expected_ids, "readiness row ids mismatch", errors)
    for row in readiness_rows:
        row_id = str(row.get("readiness_row_id"))
        require(
            row.get("schema_version") == "kmfa.v014_s15_p3.future_salary_system_readiness_draft.v1",
            f"{row_id} schema mismatch",
            errors,
        )
        require(row.get("record_type") == "future_salary_system_readiness_draft", f"{row_id} record type mismatch", errors)
        require(row.get("stage_id") == "S15" and row.get("phase_id") == "S15-P3", f"{row_id} phase mismatch", errors)
        require(
            str(row.get("performance_fact_row_ref", "")).startswith(
                "KMFA/stage_artifacts/V014_S15_P2_PERFORMANCE_REVIEW_LIST/machine/performance_fact_table.jsonl#V014-S15P2-FACT-"
            ),
            f"{row_id} fact row ref mismatch",
            errors,
        )
        require(str(row.get("project_ref", "")).startswith("public_project_group_ref_"), f"{row_id} project ref mismatch", errors)
        require(row.get("interface_contract_ref") == INTERFACE_CONTRACT_PATH.as_posix(), f"{row_id} interface ref mismatch", errors)
        require(set(row.get("available_fact_fields", [])) == set(REQUIRED_PERFORMANCE_REVIEW_FIELDS), f"{row_id} field coverage mismatch", errors)
        require(len(row.get("source_review_item_refs", [])) == 4, f"{row_id} must reference four review items", errors)
        require(
            row.get("future_read_status") == "draft_only_blocked_until_manual_review_and_human_approval",
            f"{row_id} future read status mismatch",
            errors,
        )
        for true_key in ("final_approval_must_be_human", "payment_release_must_be_human"):
            require(row.get(true_key) is True, f"{row_id}.{true_key} must be true", errors)
        for false_key in (
            "raw_business_values_allowed",
            "public_numeric_values_allowed",
            "field_plaintext_allowed",
            "api_endpoint_created",
            "connector_enabled",
            "live_read_enabled",
            "file_export_created",
            "salary_calculation_allowed",
            "wage_calculation_allowed",
            "bonus_approval_allowed",
            "payroll_export_allowed",
            "automatic_compensation_decision_allowed",
            "automatic_payment_allowed",
            "payment_execution_allowed",
            "final_compensation_decision_allowed",
            "final_payment_allowed",
            "business_execution_allowed",
        ):
            require(row.get(false_key) is False, f"{row_id}.{false_key} must be false", errors)

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
        "salary_calculation_blocked",
        "wage_calculation_blocked",
        "bonus_approval_blocked",
        "payroll_export_blocked",
        "final_compensation_decision_blocked",
        "final_payment_blocked",
        "payment_execution_blocked",
        "stage15_review_not_performed",
        "github_upload_deferred_until_v014_stage1_18_complete",
        "business_execution_blocked",
    ):
        require(block in manifest.get("hard_blocks", []), f"missing hard block {block}", errors)
    require(manifest.get("next_phase") == "S15_STAGE_REVIEW", "next phase mismatch", errors)
    require(manifest.get("next_required_step") == NEXT_REQUIRED_STEP, "next instruction mismatch", errors)
    require(manifest.get("branch") == git_output(["branch", "--show-current"]), "branch mismatch", errors)
    require(re.fullmatch(r"[0-9a-f]{40}", str(manifest.get("git_head", ""))) is not None, "git head shape mismatch", errors)

    for path in (
        MANIFEST_PATH,
        INTERFACE_CONTRACT_PATH,
        READINESS_DRAFT_PATH,
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
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.4 S15-P3 salary boundary evidence.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args(argv)
    manifest = validate_v014_s15_p3_salary_boundary(args.manifest)
    summary = manifest["salary_boundary_summary"]
    print(
        "PASS: KMFA v0.1.4 S15-P3 salary boundary validated "
        f"(interface_contracts={summary['fact_output_interface_contract_count']}, "
        f"readiness_rows={summary['future_salary_system_readiness_row_count']}, "
        "future_read_draft=true, live_integration=false, "
        "salary=false, bonus=false, payroll=false, final_payment=false, "
        "stage15_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
