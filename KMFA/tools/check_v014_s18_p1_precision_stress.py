#!/usr/bin/env python3
"""Validate KMFA v0.1.4 S18-P1 precision and stress evidence."""

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

from KMFA.tools.v014_s18_p1_precision_stress import (  # noqa: E402
    ACCEPTANCE_ID,
    ERROR_REPORT_LOCK_PATH,
    HTML_READING_RECORD_PATH,
    IMPORT_RUN_LOCK_PATH,
    MANIFEST_PATH,
    METADATA_ERROR_REPORTS_PATH,
    METADATA_IMPORT_RUNS_PATH,
    METADATA_MANIFEST_PATH,
    METADATA_SCENARIOS_PATH,
    NEXT_PHASE,
    NEXT_REQUIRED_STEP,
    PHASE_SCOPE,
    REPORT_PATH,
    REQUIRED_V014_SCENARIO_TYPES,
    RISK_REGISTER_PATH,
    ROLLBACK_PATH,
    SCENARIO_LOCK_PATH,
    SCHEMA_VERSION,
    TASK_ID,
    TEST_RESULTS_PATH,
    _phase_boundaries,
    _public_repo_safety,
    _quality_gate,
    _raw_boundary,
    load_v14_taskpack_baseline,
    validate_historical_s18_p1_public_safe_baseline,
    validate_s17_stage_review_dependency,
)


PUBLIC_SAFETY_FALSE_KEYS = tuple(key for key, value in _public_repo_safety().items() if value is False)
RAW_BOUNDARY_FALSE_KEYS = tuple(key for key, value in _raw_boundary().items() if value is False)
QUALITY_TRUE_KEYS = tuple(key for key, value in _quality_gate().items() if value is True)
QUALITY_FALSE_KEYS = tuple(key for key, value in _quality_gate().items() if value is False)
PHASE_TRUE_KEYS = tuple(key for key, value in _phase_boundaries().items() if value is True)
PHASE_FALSE_KEYS = tuple(key for key, value in _phase_boundaries().items() if value is False)

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
    "credential_material",
    "report_attachment_path",
    "production_restore_material",
    "external_service_material",
    "live_connector_material",
    "app_reinstall_material",
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


def _require_false_keys(record: dict[str, Any], keys: tuple[str, ...], label: str, errors: list[str]) -> None:
    for key in keys:
        require(record.get(key) is False, f"{label}.{key} must be false", errors)


def _require_true_keys(record: dict[str, Any], keys: tuple[str, ...], label: str, errors: list[str]) -> None:
    for key in keys:
        require(record.get(key) is True, f"{label}.{key} must be true", errors)


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


def validate_v014_s18_p1_precision_stress(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []
    manifest = read_json(manifest_path)
    metadata_manifest = read_json(METADATA_MANIFEST_PATH)
    scenarios = read_jsonl(SCENARIO_LOCK_PATH)
    metadata_scenarios = read_jsonl(METADATA_SCENARIOS_PATH)
    import_runs = read_jsonl(IMPORT_RUN_LOCK_PATH)
    metadata_import_runs = read_jsonl(METADATA_IMPORT_RUNS_PATH)
    error_reports = read_jsonl(ERROR_REPORT_LOCK_PATH)
    metadata_error_reports = read_jsonl(METADATA_ERROR_REPORTS_PATH)
    s17_review = validate_s17_stage_review_dependency()
    legacy_manifest, legacy_scenarios, legacy_import_runs, legacy_errors = (
        validate_historical_s18_p1_public_safe_baseline()
    )
    baseline = load_v14_taskpack_baseline()

    require(metadata_manifest == manifest, "metadata manifest copy must match machine manifest", errors)
    require(metadata_scenarios == scenarios, "metadata scenario copy must match machine scenario lock", errors)
    require(metadata_import_runs == import_runs, "metadata import run copy must match machine import run lock", errors)
    require(metadata_error_reports == error_reports, "metadata error report copy must match machine error lock", errors)
    require(manifest.get("schema_version") == SCHEMA_VERSION, "manifest schema mismatch", errors)
    require(manifest.get("project_id") == "KMFA", "project_id mismatch", errors)
    require(manifest.get("version") == "0.1.4", "version mismatch", errors)
    require(manifest.get("stage_id") == "S18", "stage_id must be S18", errors)
    require(manifest.get("phase_id") == "S18-P1", "phase_id mismatch", errors)
    require(manifest.get("phase_scope") == PHASE_SCOPE, "phase_scope mismatch", errors)
    require(manifest.get("task_id") == TASK_ID, "task_id mismatch", errors)
    require(manifest.get("acceptance_ids") == [ACCEPTANCE_ID], "acceptance id mismatch", errors)
    require(manifest.get("completed_task_ids") == ["S18P1T01", "S18P1T02", "S18P1T03"], "task ids mismatch", errors)
    require(manifest.get("next_phase") == NEXT_PHASE, "next phase mismatch", errors)
    require(manifest.get("next_required_step") == NEXT_REQUIRED_STEP, "next required step mismatch", errors)
    require(manifest.get("branch") == git_output(["branch", "--show-current"]), "manifest branch mismatch", errors)
    require(manifest.get("s17_stage_review_dependency_validated") is True, "S17 review dependency flag missing", errors)
    require(s17_review.get("next_phase") == "S18-P1", "S17 review must route to S18-P1", errors)
    require(
        manifest.get("historical_s18_p1_public_safe_baseline_validated") is True,
        "legacy S18-P1 baseline validation flag missing",
        errors,
    )
    require(
        manifest.get("required_scenario_types") == list(REQUIRED_V014_SCENARIO_TYPES),
        "required scenario types mismatch",
        errors,
    )

    require(len(legacy_scenarios) == 5, "legacy scenario count mismatch", errors)
    require(len(legacy_import_runs) == 3, "legacy import run count mismatch", errors)
    require(len(legacy_errors) == 2, "legacy error report count mismatch", errors)
    require(legacy_manifest.get("stage_phase") == "S18-P1", "legacy manifest stage phase mismatch", errors)

    summary = manifest.get("precision_stress_summary", {})
    require(summary.get("scenario_count") == 5, "scenario count must be 5", errors)
    require(summary.get("scenario_type_count") == 5, "scenario type count must be 5", errors)
    require(summary.get("consecutive_import_run_count") == 3, "three import runs required", errors)
    require(summary.get("unique_import_result_hash_count") == 1, "import result hash must be identical", errors)
    require(summary.get("large_batch_file_count") == 1200, "large batch file count mismatch", errors)
    require(summary.get("large_batch_elapsed_ms") == 348, "large batch elapsed mismatch", errors)
    require(summary.get("large_batch_performance_budget_ms") == 500, "large batch budget mismatch", errors)
    require(summary.get("error_report_count") == 2, "error report count mismatch", errors)
    require(summary.get("html_baseline_ref_count") == 3, "HTML baseline ref count mismatch", errors)
    require(summary.get("minimum_fail_difference_cents") == 1, "minimum fail difference must be 1 cent", errors)
    require(summary.get("report_grade_visible") == "D", "report grade must remain D", errors)

    progress = manifest.get("stage18_phase_progress", {})
    require(progress.get("completed_phase_count") == 1, "completed phase count mismatch", errors)
    require(progress.get("total_phase_count") == 3, "total phase count mismatch", errors)
    require(progress.get("derived_percent_bps") == 3333, "progress bps mismatch", errors)
    require(progress.get("derived_percent_label") == "33.33%", "progress label mismatch", errors)
    require(progress.get("s18_p1_performed") is True, "S18-P1 must be performed", errors)
    require(progress.get("s18_p2_performed") is False, "S18-P2 must not be performed", errors)
    require(progress.get("s18_p3_performed") is False, "S18-P3 must not be performed", errors)
    require(progress.get("stage18_review_performed") is False, "Stage 18 review must not be performed", errors)

    quality = manifest.get("quality_gate", {})
    _require_true_keys(quality, QUALITY_TRUE_KEYS, "quality_gate", errors)
    _require_false_keys(quality, QUALITY_FALSE_KEYS, "quality_gate", errors)
    raw_boundary = manifest.get("raw_data_boundary", {})
    _require_false_keys(raw_boundary, RAW_BOUNDARY_FALSE_KEYS, "raw_data_boundary", errors)
    phase_boundaries = manifest.get("phase_boundaries", {})
    _require_true_keys(phase_boundaries, PHASE_TRUE_KEYS, "phase_boundaries", errors)
    _require_false_keys(phase_boundaries, PHASE_FALSE_KEYS, "phase_boundaries", errors)
    safety = manifest.get("public_repo_safety", {})
    _require_false_keys(safety, PUBLIC_SAFETY_FALSE_KEYS, "public_repo_safety", errors)

    scenario_types = {str(row.get("scenario_type")) for row in scenarios}
    require(scenario_types == set(REQUIRED_V014_SCENARIO_TYPES), "scenario type set mismatch", errors)
    require({row.get("record_type") for row in scenarios} == {"v014_s18_p1_precision_stress_scenario_lock"}, "scenario record type mismatch", errors)
    for row in scenarios:
        require(row.get("project_id") == "KMFA", "scenario project mismatch", errors)
        require(row.get("stage_id") == "S18", "scenario stage mismatch", errors)
        require(row.get("phase_id") == "S18-P1", "scenario phase mismatch", errors)
        require(row.get("task_id") == "S18P1T01", "scenario task mismatch", errors)
        require(row.get("fixture_mode") == "public_safe_synthetic", "scenario fixture mode mismatch", errors)
        require(row.get("raw_business_data_used") is False, "scenario raw use must be false", errors)
        require(row.get("true_money_used") is False, "scenario true money must be false", errors)
        require(row.get("raw_file_committed") is False, "scenario raw file commit must be false", errors)
        require(row.get("github_upload_allowed") is False, "scenario upload allowed must be false", errors)

    amount_precision = next(row for row in scenarios if row.get("scenario_type") == "amount_precision")
    require(amount_precision.get("minimum_fail_difference_cents") == 1, "amount precision 1 cent gate missing", errors)
    require(amount_precision.get("float_money_allowed") is False, "float money must be false", errors)
    require(amount_precision.get("blank_dash_hash_defaults_to_zero") is False, "blank/dash/hash default must be false", errors)
    zero_delta = next(row for row in scenarios if row.get("scenario_type") == "zero_delta")
    require(zero_delta.get("zero_delta_result") == "passed", "zero delta scenario must pass", errors)
    duplicate = next(row for row in scenarios if row.get("scenario_type") == "duplicate_import")
    require(duplicate.get("idempotency_result") == "passed", "duplicate import idempotency must pass", errors)
    bad_file = next(row for row in scenarios if row.get("scenario_type") == "bad_file")
    missing_field = next(row for row in scenarios if row.get("scenario_type") == "missing_field")
    require(bad_file.get("error_report_required") is True, "bad file error report required", errors)
    require(missing_field.get("error_report_required") is True, "missing field error report required", errors)

    require([row.get("run_sequence") for row in import_runs] == [1, 2, 3], "import run sequence mismatch", errors)
    require(len({row.get("result_hash") for row in import_runs}) == 1, "import result hashes must match", errors)
    require(len({row.get("scenario_set_hash") for row in import_runs}) == 1, "scenario set hashes must match", errors)
    for row in import_runs:
        require(row.get("record_type") == "v014_s18_p1_import_consistency_run_lock", "import run record type mismatch", errors)
        require(row.get("input_mode") == "public_safe_synthetic_metadata_only", "import run input mode mismatch", errors)
        require(row.get("status") == "passed", "import run must pass", errors)
        require(row.get("raw_file_committed") is False, "import run raw file commit must be false", errors)
        require(row.get("raw_inbox_accessed") is False, "import run raw inbox access must be false", errors)

    require({row.get("error_type") for row in error_reports} == {"bad_file", "missing_field"}, "error type set mismatch", errors)
    for row in error_reports:
        require(row.get("record_type") == "v014_s18_p1_precision_stress_error_report_lock", "error report record type mismatch", errors)
        require(row.get("severity") == "blocking", "error report must be blocking", errors)
        require(row.get("raw_excerpt_committed") is False, "raw excerpt must be false", errors)
        require(row.get("private_file_path_committed") is False, "private file path must be false", errors)
        require(row.get("business_execution_allowed") is False, "business execution must be false", errors)

    baseline_refs = manifest.get("v14_taskpack_baseline", {})
    require(baseline_refs == baseline, "v1.4 taskpack baseline mismatch", errors)
    github = manifest.get("github_upload", {})
    require(github.get("github_upload_performed") is False, "GitHub upload must be false", errors)
    require(
        github.get("github_upload_status") == "not_uploaded_deferred_until_v014_stage1_18_complete",
        "GitHub upload status mismatch",
        errors,
    )
    require(github.get("github_upload_deferred_until_v014_stage1_18_complete") is True, "upload defer flag missing", errors)
    for path in (
        REPORT_PATH,
        HTML_READING_RECORD_PATH,
        TEST_RESULTS_PATH,
        RISK_REGISTER_PATH,
        ROLLBACK_PATH,
        MANIFEST_PATH,
        SCENARIO_LOCK_PATH,
        IMPORT_RUN_LOCK_PATH,
        ERROR_REPORT_LOCK_PATH,
    ):
        check_public_evidence_text(path, errors)

    if errors:
        raise ValidationError("\n".join(errors))
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.4 S18-P1 precision stress evidence.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args(argv)
    manifest = validate_v014_s18_p1_precision_stress(args.manifest)
    summary = manifest["precision_stress_summary"]
    print(
        "PASS: KMFA v0.1.4 S18-P1 precision stress validated "
        f"(scenarios={summary['scenario_count']}, "
        f"runs={summary['consecutive_import_run_count']}, "
        f"large_batch_files={summary['large_batch_file_count']}, "
        f"elapsed_ms={summary['large_batch_elapsed_ms']}, "
        f"errors={summary['error_report_count']}, "
        "s18_p2=False, s18_p3=False, stage18_review=False, github_upload=False)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
