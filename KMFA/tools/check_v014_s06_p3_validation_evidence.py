#!/usr/bin/env python3
"""Validate KMFA v0.1.4 S06-P3 public-safe validation evidence outputs."""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from KMFA.tools.check_v014_s06_p1_zero_delta_validator import validate_v014_s06_p1_zero_delta_validator
from KMFA.tools.check_v014_s06_p2_difference_queue import validate_v014_s06_p2_difference_queue
from KMFA.tools.v014_s06_p3_validation_evidence import (
    ACCEPTANCE_ID,
    MANIFEST_PATH,
    MISMATCH_OUTPUT_PATH,
    NEXT_INSTRUCTION,
    NEXT_PHASE,
    PHASE_SCOPE,
    PROJECT_STATUS_OUTPUT_PATH,
    REPORT_PATH,
    RISK_REGISTER_PATH,
    ROLLBACK_PATH,
    SCHEMA_VERSION,
    TASK_ID,
    TEST_RESULTS_PATH,
    ZERO_DELTA_OUTPUT_PATH,
)


METADATA_QUALITY_DIR = Path("KMFA/metadata/quality")
FORBIDDEN_PUBLIC_SUFFIXES = (".zip", ".xlsx", ".xls", ".xlsm", ".pdf", ".sqlite", ".sqlite3", ".db")
PUBLIC_SAFETY_FALSE_KEYS = (
    "raw_business_data_committed",
    "zip_committed",
    "excel_workbook_committed",
    "pdf_committed",
    "private_csv_committed",
    "sqlite_or_db_committed",
    "credentials_committed",
    "field_plaintext_committed",
    "raw_file_names_committed",
    "raw_file_hashes_committed",
    "raw_business_values_committed",
    "sheet_names_committed",
    "zip_member_names_committed",
)


def forbidden_key(*parts: str) -> str:
    return "_".join(parts)


FORBIDDEN_PUBLIC_KEYS = {
    "field",
    forbidden_key("authoritative", "value", "cents"),
    forbidden_key("system", "value", "cents"),
    forbidden_key("pdf", "value", "cents"),
    forbidden_key("excel", "value", "cents"),
    "raw_value",
    "original_value",
    "plaintext_content",
    "full_file_text",
}
FORBIDDEN_TEXT = (
    "raw_value:",
    "normalized_value:",
    "source_header_text:",
    "actual_package_sha256",
    "member_sha256:",
    "bank_statement",
    "contract_full_text",
    "salary_detail",
    "tax_filing",
    forbidden_key("authoritative", "value", "cents"),
    forbidden_key("system", "value", "cents"),
    forbidden_key("pdf", "value", "cents"),
    forbidden_key("excel", "value", "cents"),
    forbidden_key("contract", "amount", "cents"),
    "10000",
    "9999",
    "-----" "BEGIN",
    "s" "k-",
)
STRICT_SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(?i)(password|passwd|secret|api_key|token)\s*=\s*[^\s,;]{8,}"),
)
RAW_INBOX_DIRECTORY_TOKEN = "KMFA" + "_MetaData"
LOCAL_DOWNLOADS_RAW_PATH_PATTERN = re.compile(r"/Users/[^\s\"'`]+/Downloads/[^\s\"'`]+")
SANITIZED_MISMATCH_COLUMNS = (
    "mismatch_id",
    "source_id",
    "file_hash",
    "field_path",
    "mapping_version",
    "formula_version",
    "status",
    "evidence_ref",
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
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not rows:
        raise ValidationError(f"{path} must contain at least one row")
    if not all(isinstance(row, dict) for row in rows):
        raise ValidationError(f"{path} must contain JSON objects")
    return rows


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise ValidationError(f"missing CSV file: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


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


def walk_forbidden_keys(value: Any, errors: list[str], path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_PUBLIC_KEYS:
                errors.append(f"forbidden public output key {key!r} at {path}")
            walk_forbidden_keys(child, errors, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            walk_forbidden_keys(child, errors, f"{path}[{index}]")


def check_public_safe_file(path: Path, errors: list[str]) -> None:
    require(path.exists(), f"missing public-safe file: {path}", errors)
    if not path.exists():
        return
    require(path.suffix.lower() not in FORBIDDEN_PUBLIC_SUFFIXES, f"forbidden evidence extension: {path}", errors)
    if path.suffix.lower() not in {".md", ".json", ".jsonl", ".csv", ".yaml", ".yml"}:
        return
    text = path.read_text(encoding="utf-8", errors="ignore")
    lower = text.lower()
    for forbidden in FORBIDDEN_TEXT:
        require(forbidden.lower() not in lower, f"forbidden public text {forbidden!r} in {path}", errors)
    require(
        RAW_INBOX_DIRECTORY_TOKEN.lower() not in lower,
        f"forbidden raw inbox directory token in {path}",
        errors,
    )
    require(
        LOCAL_DOWNLOADS_RAW_PATH_PATTERN.search(text) is None,
        f"forbidden local Downloads raw path in {path}",
        errors,
    )
    for pattern in STRICT_SECRET_PATTERNS:
        require(pattern.search(text) is None, f"high-signal secret pattern in {path}: {pattern.pattern}", errors)


def metadata_records_by_id(path: Path, identity_field: str) -> dict[str, dict[str, Any]]:
    return {str(record.get(identity_field)): record for record in read_jsonl(path) if record.get(identity_field)}


def validate_v014_s06_p3_validation_evidence(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []
    manifest = read_json(manifest_path)
    s06_p1 = validate_v014_s06_p1_zero_delta_validator()
    s06_p2 = validate_v014_s06_p2_difference_queue()
    zero_delta_output = read_json(ZERO_DELTA_OUTPUT_PATH)
    project_statuses = read_jsonl(PROJECT_STATUS_OUTPUT_PATH)
    mismatch_rows = read_csv(MISMATCH_OUTPUT_PATH)

    for value in (manifest, zero_delta_output, project_statuses):
        walk_forbidden_keys(value, errors)

    require(manifest.get("schema_version") == SCHEMA_VERSION, "manifest schema mismatch", errors)
    require(manifest.get("project_id") == "KMFA", "project_id mismatch", errors)
    require(manifest.get("version") == "0.1.4", "version mismatch", errors)
    require(manifest.get("stage_id") == "S06", "stage_id must be S06", errors)
    require(manifest.get("phase_id") == "S06-P3", "phase_id must be S06-P3", errors)
    require(manifest.get("phase_scope") == PHASE_SCOPE, "phase scope mismatch", errors)
    require(manifest.get("task_id") == TASK_ID, "task id mismatch", errors)
    require(manifest.get("acceptance_id") == ACCEPTANCE_ID, "acceptance id mismatch", errors)
    require(
        manifest.get("status") == "completed_validated_local_only_no_go_upload_deferred_validation_evidence",
        "status mismatch",
        errors,
    )
    require(manifest.get("completed_task_ids") == ["S06P3T01", "S06P3T02", "S06P3T03"], "task ids mismatch", errors)
    require(manifest.get("next_recommended_phase") == NEXT_PHASE, "next phase mismatch", errors)
    require(manifest.get("next_phase_instruction") == NEXT_INSTRUCTION, "next instruction mismatch", errors)

    require(manifest.get("s06_p1_dependency_validated") is True, "S06-P1 dependency flag mismatch", errors)
    require(manifest.get("s06_p2_dependency_validated") is True, "S06-P2 dependency flag mismatch", errors)
    require(s06_p1.get("phase_id") == "S06-P1", "S06-P1 dependency phase mismatch", errors)
    require(s06_p2.get("phase_id") == "S06-P2", "S06-P2 dependency phase mismatch", errors)
    require(s06_p1.get("metadata_quality_written") is False, "S06-P1 must not write metadata quality", errors)
    require(s06_p2.get("metadata_quality_written") is False, "S06-P2 must not write metadata quality", errors)
    require(s06_p2.get("source_difference_queue_metadata_written") is False, "S06-P2 queue metadata flag mismatch", errors)
    require(s06_p2.get("report_grade_a_allowed") is False, "S06-P2 unresolved difference must block grade A", errors)

    require(zero_delta_output.get("record_type") == "s06_p3_zero_delta_result", "zero delta record type mismatch", errors)
    require(zero_delta_output.get("stage_phase") == "S06-P3", "zero delta phase mismatch", errors)
    require(zero_delta_output.get("zero_delta_passed") is False, "zero delta must remain failed", errors)
    require(zero_delta_output.get("mismatch_count") == 1, "zero delta mismatch count mismatch", errors)
    require(zero_delta_output.get("project_status_count") == 2, "project status count mismatch", errors)
    require("mismatches" not in zero_delta_output, "zero delta output must not inline mismatch rows", errors)
    require(zero_delta_output.get("raw_business_data_used") is False, "zero delta raw flag mismatch", errors)
    require(zero_delta_output.get("public_safe_fixture_only") is True, "zero delta public-safe flag mismatch", errors)
    require(zero_delta_output.get("forbidden_plaintext") is True, "zero delta forbidden plaintext flag mismatch", errors)

    require(len(project_statuses) == 2, "project status count must be 2", errors)
    status_by_project = {status.get("project_ref"): status for status in project_statuses}
    require("V014-SYN-ZERO-DELTA-001" in status_by_project, "missing zero-delta project status", errors)
    require("V014-SYN-PROJECT-S06P2-001" in status_by_project, "missing difference project status", errors)
    expected_blocks = {
        "V014-SYN-ZERO-DELTA-001": ["zero_delta_failed"],
        "V014-SYN-PROJECT-S06P2-001": ["unresolved_critical_difference"],
    }
    for status in project_statuses:
        require(status.get("record_type") == "project_validation_status", "project status record type mismatch", errors)
        require(status.get("stage_phase") == "S06-P3", "project status phase mismatch", errors)
        require(status.get("validation_status") == "blocked", "project status must remain blocked", errors)
        require(status.get("quality_grade") == "Q4", "blocked quality grade must be Q4", errors)
        require(status.get("q5_allowed") is False, "q5_allowed must be false", errors)
        require(status.get("report_grade_a_allowed") is False, "grade A must be false", errors)
        require(status.get("maximum_report_grade") == "B", "maximum report grade must be B", errors)
        require(status.get("raw_business_data_used") is False, "project status raw flag mismatch", errors)
        require(status.get("public_safe_fixture_only") is True, "project status public-safe flag mismatch", errors)
        require(status.get("forbidden_plaintext") is True, "project status forbidden plaintext flag mismatch", errors)
        require(status.get("hard_blocks") == expected_blocks.get(str(status.get("project_ref"))), "hard blocks mismatch", errors)

    require(len(mismatch_rows) == 1, "sanitized mismatch report must contain one row", errors)
    if mismatch_rows:
        row = mismatch_rows[0]
        require(tuple(row.keys()) == SANITIZED_MISMATCH_COLUMNS, "sanitized mismatch columns mismatch", errors)
        require(str(row.get("field_path", "")).startswith("field_ref:sha256:"), "field_path must be hash/ref", errors)
        require(str(row.get("file_hash", "")).startswith("sha256:"), "file_hash must be hash", errors)
        require(row.get("status") == "zero_delta_failed", "mismatch status mismatch", errors)

    require(manifest.get("metadata_quality_written") is True, "metadata quality flag mismatch", errors)
    require(manifest.get("zero_delta_result_output_written") is True, "zero delta output flag mismatch", errors)
    require(manifest.get("mismatch_report_output_written") is True, "mismatch output flag mismatch", errors)
    require(manifest.get("project_validation_status_output_written") is True, "status output flag mismatch", errors)
    require(manifest.get("metadata_zero_delta_records_written") == 1, "metadata zero delta count mismatch", errors)
    require(manifest.get("metadata_data_quality_records_written") == 2, "metadata data quality count mismatch", errors)
    require(manifest.get("metadata_source_difference_records_written") == 1, "metadata source queue count mismatch", errors)
    require(manifest.get("metadata_mismatch_rows_written") == 1, "metadata mismatch row count mismatch", errors)
    require(manifest.get("q5_allowed_count") == 0, "q5 count must be zero", errors)
    require(manifest.get("report_grade_a_allowed_count") == 0, "grade A count must be zero", errors)
    require(manifest.get("hard_blocks") == ["unresolved_critical_difference", "zero_delta_failed"], "hard blocks summary mismatch", errors)

    zero_delta_metadata = metadata_records_by_id(METADATA_QUALITY_DIR / "zero_delta_results.jsonl", "result_id")
    require(manifest.get("zero_delta_result_id") in zero_delta_metadata, "metadata zero delta record missing", errors)
    metadata_record = zero_delta_metadata.get(str(manifest.get("zero_delta_result_id")), {})
    require(metadata_record.get("result_ref") == ZERO_DELTA_OUTPUT_PATH.as_posix(), "metadata result_ref mismatch", errors)
    require(metadata_record.get("mismatch_report_ref") == MISMATCH_OUTPUT_PATH.as_posix(), "metadata mismatch ref mismatch", errors)

    data_quality_records = [
        record
        for record in read_jsonl(METADATA_QUALITY_DIR / "data_quality_results.jsonl")
        if record.get("stage_phase") == "S06-P3" and record.get("zero_delta_result_id") == manifest.get("zero_delta_result_id")
    ]
    require(len(data_quality_records) == 2, "metadata data quality records for result id mismatch", errors)
    for record in data_quality_records:
        require(record.get("q5_allowed") is False, "metadata data quality q5 must be false", errors)
        require(record.get("report_grade_a_allowed") is False, "metadata data quality grade A must be false", errors)
        require(record.get("raw_business_data_used") is False, "metadata data quality raw flag mismatch", errors)
        require(record.get("public_safe_fixture_only") is True, "metadata data quality public-safe flag mismatch", errors)

    queue_records = metadata_records_by_id(METADATA_QUALITY_DIR / "source_difference_queue.jsonl", "queue_id")
    require("CDQ-20260704-114000-e7b8be95d2e7" in queue_records, "metadata source difference queue record missing", errors)
    queue_record = queue_records.get("CDQ-20260704-114000-e7b8be95d2e7", {})
    require(queue_record.get("stage_phase") == "S06-P3", "metadata queue phase mismatch", errors)
    require(str(queue_record.get("field_path", "")).startswith("field_ref:sha256:"), "metadata queue field path mismatch", errors)
    require(queue_record.get("auto_correction_allowed") is False, "metadata queue auto correction mismatch", errors)
    require(queue_record.get("auto_selection_allowed") is False, "metadata queue auto selection mismatch", errors)
    require(queue_record.get("report_grade_a_allowed") is False, "metadata queue report grade mismatch", errors)
    require(queue_record.get("raw_business_data_used") is False, "metadata queue raw flag mismatch", errors)
    require(queue_record.get("public_safe_fixture_only") is True, "metadata queue public-safe flag mismatch", errors)

    metadata_mismatch_rows = read_csv(METADATA_QUALITY_DIR / "mismatch_report.csv")
    require(
        any(row.get("mismatch_id") == mismatch_rows[0].get("mismatch_id") for row in metadata_mismatch_rows),
        "metadata mismatch row missing",
        errors,
    )

    for key in (
        "field_plaintext_committed",
        "raw_business_values_committed",
        "source_amount_literals_committed",
        "raw_business_data_used",
        "raw_inbox_read_performed",
        "raw_inbox_listed_performed",
        "raw_inbox_stat_performed",
        "raw_inbox_hash_performed",
        "raw_inbox_mutation_performed",
        "raw_value_matching_performed",
        "difference_closed",
        "auto_correction_allowed",
        "averaging_allowed",
        "rounding_mask_allowed",
        "auto_selection_allowed",
        "stage6_review_performed",
        "github_upload_performed",
        "formal_report_allowed",
        "business_decision_basis_allowed",
        "business_execution_allowed",
    ):
        require(manifest.get(key) is False, f"{key} must be false", errors)
    require(
        manifest.get("github_upload_status") == "not_uploaded_deferred_until_v014_stage1_18_complete",
        "github upload status mismatch",
        errors,
    )
    require(manifest.get("current_data_quality_grade") == "Q4", "data quality grade mismatch", errors)
    require(manifest.get("current_report_grade") == "D", "report grade mismatch", errors)
    require(manifest.get("release_permission") == "blocked", "release permission mismatch", errors)

    raw_boundary = manifest.get("raw_data_boundary", {})
    require(raw_boundary.get("raw_inbox_ref") == "operator-designated local raw/private inbox outside repository", "raw inbox ref mismatch", errors)
    require("raw_inbox_path" not in raw_boundary, "raw inbox absolute path must not be public evidence", errors)
    for key in (
        "codex_read_required_by_this_phase",
        "codex_read_performed_by_this_phase",
        "codex_list_performed_by_this_phase",
        "codex_stat_performed_by_this_phase",
        "codex_hash_performed_by_this_phase",
        "codex_modify_allowed",
        "codex_delete_allowed",
        "codex_move_allowed",
        "codex_rename_allowed",
        "codex_overwrite_allowed",
        "codex_generate_inside_allowed",
        "github_commit_allowed",
    ):
        require(raw_boundary.get(key) is False, f"raw_data_boundary.{key} must be false", errors)

    safety = manifest.get("public_repo_safety", {})
    for key in PUBLIC_SAFETY_FALSE_KEYS:
        require(safety.get(key) is False, f"public_repo_safety.{key} must be false", errors)

    for ref in manifest.get("evidence_refs", []):
        require(Path(ref).exists(), f"missing evidence ref: {ref}", errors)
    for path in [
        REPORT_PATH,
        TEST_RESULTS_PATH,
        RISK_REGISTER_PATH,
        ROLLBACK_PATH,
        MANIFEST_PATH,
        ZERO_DELTA_OUTPUT_PATH,
        MISMATCH_OUTPUT_PATH,
        PROJECT_STATUS_OUTPUT_PATH,
    ]:
        check_public_safe_file(path, errors)

    tracked_files = git_output(["ls-files", "KMFA"]).splitlines()
    forbidden_tracked = [
        path
        for path in tracked_files
        if path.lower().endswith(FORBIDDEN_PUBLIC_SUFFIXES) or ".codex_private_runtime/" in path
    ]
    require(not forbidden_tracked, f"forbidden public/private tracked files: {forbidden_tracked}", errors)
    require("codex/kmfa" in git_output(["status", "--short", "--branch"]), "git status must be on codex/kmfa", errors)

    if errors:
        raise ValidationError("\n".join(errors))

    return {
        "task_id": manifest["task_id"],
        "stage_id": manifest["stage_id"],
        "phase_id": manifest["phase_id"],
        "phase_scope": manifest["phase_scope"],
        "s06_p1_dependency_validated": manifest["s06_p1_dependency_validated"],
        "s06_p2_dependency_validated": manifest["s06_p2_dependency_validated"],
        "metadata_quality_written": manifest["metadata_quality_written"],
        "metadata_zero_delta_records_written": manifest["metadata_zero_delta_records_written"],
        "metadata_data_quality_records_written": manifest["metadata_data_quality_records_written"],
        "metadata_source_difference_records_written": manifest["metadata_source_difference_records_written"],
        "metadata_mismatch_rows_written": manifest["metadata_mismatch_rows_written"],
        "project_status_count": manifest["project_status_count"],
        "blocked_project_status_count": manifest["blocked_project_status_count"],
        "q5_allowed_count": manifest["q5_allowed_count"],
        "report_grade_a_allowed_count": manifest["report_grade_a_allowed_count"],
        "stage6_review_performed": manifest["stage6_review_performed"],
        "github_upload_performed": manifest["github_upload_performed"],
        "raw_inbox_read_performed": manifest["raw_inbox_read_performed"],
        "raw_inbox_mutation_performed": manifest["raw_inbox_mutation_performed"],
        "formal_report_allowed": manifest["formal_report_allowed"],
        "business_execution_allowed": manifest["business_execution_allowed"],
        "next_recommended_phase": manifest["next_recommended_phase"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.4 S06-P3 validation evidence.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args()
    try:
        result = validate_v014_s06_p3_validation_evidence(args.manifest)
    except ValidationError as exc:
        print("FAIL: KMFA v0.1.4 S06-P3 validation evidence validation failed")
        print(exc)
        return 1
    print(
        "PASS: KMFA v0.1.4 S06-P3 validation evidence validated "
        f"(metadata_quality_written={str(result['metadata_quality_written']).lower()}, "
        f"project_statuses={result['project_status_count']}, "
        f"blocked={result['blocked_project_status_count']}, "
        f"q5_allowed={result['q5_allowed_count']}, "
        f"stage6_review={str(result['stage6_review_performed']).lower()}, "
        f"github_upload={str(result['github_upload_performed']).lower()})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
