#!/usr/bin/env python3
"""Validate KMFA v0.1.3 S06-P3 validation evidence replay outputs."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from KMFA.tools.check_v013_s06_p1_zero_delta_replay import validate_v013_s06_p1_zero_delta_replay
from KMFA.tools.check_v013_s06_p2_difference_queue_replay import validate_v013_s06_p2_difference_queue_replay
from KMFA.tools.v013_s06_p3_validation_evidence_replay import (
    MANIFEST_PATH,
    MISMATCH_OUTPUT_PATH,
    NEXT_REQUIRED_STEP,
    PHASE_SCOPE,
    PROJECT_STATUS_OUTPUT_PATH,
    REPORT_PATH,
    SCHEMA_VERSION,
    TASK_ID,
    TEST_RESULTS_PATH,
    ZERO_DELTA_OUTPUT_PATH,
)


RAW_DIR = "/Users/linzezhang/Downloads/KMFA_MetaData"
METADATA_QUALITY_DIR = Path("KMFA/metadata/quality")
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
FORBIDDEN_PUBLIC_SUFFIXES = (".zip", ".xlsx", ".xls", ".xlsm", ".pdf", ".sqlite", ".db")
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
    "authoritative_value_cents",
    "system_value_cents",
    "pdf_value_cents",
    "excel_value_cents",
    "contract_amount_cents",
    "10000",
    "9999",
    "-----" "BEGIN",
    "s" "k-",
)
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


def _require_public_safe_text(paths: list[Path], errors: list[str]) -> None:
    for path in paths:
        if not path.exists():
            errors.append(f"missing public-safe scan path: {path}")
            continue
        text = path.read_text(encoding="utf-8")
        for forbidden in FORBIDDEN_TEXT:
            if forbidden in text:
                errors.append(f"forbidden public evidence text {forbidden!r} in {path}")


def _metadata_records_by_id(path: Path, identity_field: str) -> dict[str, dict[str, Any]]:
    return {str(record.get(identity_field)): record for record in read_jsonl(path) if record.get(identity_field)}


def validate_v013_s06_p3_validation_evidence_replay(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    manifest = read_json(manifest_path)
    s06_p1 = validate_v013_s06_p1_zero_delta_replay()
    s06_p2 = validate_v013_s06_p2_difference_queue_replay()
    zero_delta_output = read_json(ZERO_DELTA_OUTPUT_PATH)
    project_statuses = read_jsonl(PROJECT_STATUS_OUTPUT_PATH)
    mismatch_rows = read_csv(MISMATCH_OUTPUT_PATH)

    require(manifest.get("schema_version") == SCHEMA_VERSION, "manifest schema mismatch")
    require(manifest.get("project_id") == "KMFA", "project_id mismatch")
    require(manifest.get("version") == "0.1.3", "version mismatch")
    require(manifest.get("stage_id") == "S06", "stage_id must be S06")
    require(manifest.get("phase_id") == "S06-P3", "phase_id must be S06-P3")
    require(manifest.get("phase_scope") == PHASE_SCOPE, "phase scope mismatch")
    require(manifest.get("task_id") == TASK_ID, "task_id mismatch")
    require(
        manifest.get("status") == "completed_validated_local_only_upload_deferred_validation_evidence_replay",
        "status mismatch",
    )
    require(manifest.get("completed_task_ids") == ["S6PCT01", "S6PCT02", "S6PCT03"], "task ids mismatch")
    require(
        manifest.get("acceptance_ids") == ["ACC-V013-S06-P3-VALIDATION-EVIDENCE-REPLAY"],
        "acceptance ids mismatch",
    )
    require(manifest.get("next_required_step") == NEXT_REQUIRED_STEP, "next_required_step mismatch")

    require(manifest.get("s06_p1_dependency_validated") is True, "S06-P1 dependency flag mismatch")
    require(manifest.get("s06_p2_dependency_validated") is True, "S06-P2 dependency flag mismatch")
    require(s06_p1.get("phase_id") == "S06-P1", "S06-P1 dependency phase mismatch")
    require(s06_p2.get("phase_id") == "S06-P2", "S06-P2 dependency phase mismatch")
    require(s06_p1.get("metadata_quality_written") is False, "S06-P1 must not write metadata quality")
    require(s06_p2.get("metadata_quality_written") is False, "S06-P2 must not write metadata quality")
    require(s06_p2.get("source_difference_queue_metadata_written") is False, "S06-P2 metadata queue write must be false")
    require(s06_p2.get("report_grade_a_allowed") is False, "S06-P2 unresolved difference must block grade A")

    require(zero_delta_output.get("record_type") == "s06_p3_zero_delta_result", "zero delta output record type mismatch")
    require(zero_delta_output.get("stage_phase") == "S06-P3", "zero delta output stage phase mismatch")
    require(zero_delta_output.get("zero_delta_passed") is False, "zero delta output must remain failed")
    require(zero_delta_output.get("mismatch_count") == 1, "zero delta output mismatch count mismatch")
    require(zero_delta_output.get("project_status_count") == 2, "zero delta output project count mismatch")
    require("mismatches" not in zero_delta_output, "zero delta output must not inline mismatch rows")
    require(zero_delta_output.get("raw_business_data_used") is False, "zero delta output raw flag mismatch")
    require(zero_delta_output.get("public_safe_fixture_only") is True, "zero delta output public-safe flag mismatch")
    require(zero_delta_output.get("forbidden_plaintext") is True, "zero delta output forbidden plaintext flag mismatch")

    require(len(project_statuses) == 2, "project status count must be 2")
    status_by_project = {status.get("project_ref"): status for status in project_statuses}
    require("V013-SYN-ZERO-DELTA-001" in status_by_project, "missing zero-delta project status")
    require("V013-SYN-PROJECT-S06P2-001" in status_by_project, "missing difference queue project status")
    for status in project_statuses:
        require(status.get("record_type") == "project_validation_status", "project status record type mismatch")
        require(status.get("stage_phase") == "S06-P3", "project status phase mismatch")
        require(status.get("validation_status") == "blocked", "project status must remain blocked")
        require(status.get("quality_grade") == "Q4", "blocked project quality grade must be Q4")
        require(status.get("q5_allowed") is False, "q5_allowed must be false")
        require(status.get("report_grade_a_allowed") is False, "grade A must be false")
        require(status.get("maximum_report_grade") == "B", "maximum report grade must be B")
        require(status.get("raw_business_data_used") is False, "project status raw flag mismatch")
        require(status.get("public_safe_fixture_only") is True, "project status public-safe flag mismatch")
        require(status.get("forbidden_plaintext") is True, "project status forbidden plaintext flag mismatch")
    if "V013-SYN-ZERO-DELTA-001" in status_by_project:
        require(
            status_by_project["V013-SYN-ZERO-DELTA-001"].get("hard_blocks") == ["zero_delta_failed"],
            "zero-delta project hard blocks mismatch",
        )
    if "V013-SYN-PROJECT-S06P2-001" in status_by_project:
        require(
            status_by_project["V013-SYN-PROJECT-S06P2-001"].get("hard_blocks") == ["unresolved_critical_difference"],
            "difference project hard blocks mismatch",
        )

    require(len(mismatch_rows) == 1, "sanitized mismatch report must contain one row")
    if mismatch_rows:
        row = mismatch_rows[0]
        require(tuple(row.keys()) == SANITIZED_MISMATCH_COLUMNS, "sanitized mismatch columns mismatch")
        require(str(row.get("field_path", "")).startswith("field_ref:sha256:"), "field_path must be hash/ref")
        require(str(row.get("file_hash", "")).startswith("sha256:"), "file_hash must be hash")
        require(row.get("status") == "zero_delta_failed", "mismatch status mismatch")

    require(manifest.get("metadata_quality_written") is True, "metadata_quality_written must be true")
    require(manifest.get("zero_delta_result_output_written") is True, "zero delta output written flag mismatch")
    require(manifest.get("mismatch_report_output_written") is True, "mismatch output written flag mismatch")
    require(manifest.get("project_validation_status_output_written") is True, "project status written flag mismatch")
    require(manifest.get("metadata_zero_delta_records_written") == 1, "metadata zero delta count mismatch")
    require(manifest.get("metadata_data_quality_records_written") == 2, "metadata data quality count mismatch")
    require(manifest.get("metadata_source_difference_records_written") == 1, "metadata source queue count mismatch")
    require(manifest.get("metadata_mismatch_rows_written") == 1, "metadata mismatch row count mismatch")
    require(manifest.get("q5_allowed_count") == 0, "q5 count must be 0")
    require(manifest.get("report_grade_a_allowed_count") == 0, "grade A count must be 0")
    require(manifest.get("hard_blocks") == ["unresolved_critical_difference", "zero_delta_failed"], "hard blocks mismatch")

    zero_delta_metadata = _metadata_records_by_id(
        METADATA_QUALITY_DIR / "zero_delta_results.jsonl",
        "result_id",
    )
    require(manifest.get("zero_delta_result_id") in zero_delta_metadata, "metadata zero-delta record missing")
    metadata_record = zero_delta_metadata.get(str(manifest.get("zero_delta_result_id")), {})
    require(metadata_record.get("result_ref") == ZERO_DELTA_OUTPUT_PATH.as_posix(), "metadata result_ref mismatch")
    require(metadata_record.get("mismatch_report_ref") == MISMATCH_OUTPUT_PATH.as_posix(), "metadata mismatch ref mismatch")

    data_quality_ids = set()
    for record in read_jsonl(METADATA_QUALITY_DIR / "data_quality_results.jsonl"):
        if record.get("stage_phase") == "S06-P3" and record.get("zero_delta_result_id") == manifest.get("zero_delta_result_id"):
            data_quality_ids.add(record.get("quality_result_id"))
            require(record.get("q5_allowed") is False, "metadata data quality q5 must be false")
            require(record.get("report_grade_a_allowed") is False, "metadata data quality grade A must be false")
            require(record.get("raw_business_data_used") is False, "metadata data quality raw flag mismatch")
            require(record.get("public_safe_fixture_only") is True, "metadata data quality public-safe flag mismatch")
    require(len(data_quality_ids) == 2, "metadata data quality records for result id mismatch")

    metadata_queue_records = _metadata_records_by_id(
        METADATA_QUALITY_DIR / "source_difference_queue.jsonl",
        "queue_id",
    )
    require("CDQ-20260703-062000-404ffdcfce59" in metadata_queue_records, "metadata source difference queue record missing")
    queue_record = metadata_queue_records.get("CDQ-20260703-062000-404ffdcfce59", {})
    require(queue_record.get("stage_phase") == "S06-P3", "metadata queue stage phase mismatch")
    require(str(queue_record.get("field_path", "")).startswith("field_ref:sha256:"), "metadata queue field path mismatch")
    require(queue_record.get("auto_correction_allowed") is False, "metadata queue auto correction mismatch")
    require(queue_record.get("auto_selection_allowed") is False, "metadata queue auto selection mismatch")
    require(queue_record.get("report_grade_a_allowed") is False, "metadata queue report grade mismatch")
    require(queue_record.get("raw_business_data_used") is False, "metadata queue raw flag mismatch")
    require(queue_record.get("public_safe_fixture_only") is True, "metadata queue public-safe flag mismatch")

    metadata_mismatch_rows = read_csv(METADATA_QUALITY_DIR / "mismatch_report.csv")
    require(
        any(row.get("mismatch_id") == mismatch_rows[0].get("mismatch_id") for row in metadata_mismatch_rows),
        "metadata mismatch row missing",
    )

    require(manifest.get("field_plaintext_committed") is False, "field plaintext flag mismatch")
    require(manifest.get("raw_business_values_committed") is False, "raw business value flag mismatch")
    require(manifest.get("source_amount_literals_committed") is False, "source amount literal flag mismatch")
    require(manifest.get("raw_business_data_used") is False, "raw business data must not be used")
    require(manifest.get("raw_dir_read_performed") is False, "raw dir read must be false")
    require(manifest.get("raw_dir_mutation_performed") is False, "raw dir mutation must be false")
    require(manifest.get("raw_value_matching_performed") is False, "raw value matching must be false")
    require(manifest.get("difference_closed") is False, "difference must remain unclosed")
    require(manifest.get("stage6_review_performed") is False, "Stage 6 review must not be performed")
    require(manifest.get("github_upload_performed") is False, "GitHub upload must not be performed")
    require(
        manifest.get("github_upload_deferred_until_stage10_batch") is True,
        "GitHub upload must remain deferred",
    )
    require(manifest.get("formal_report_allowed") is False, "formal report must remain blocked")
    require(manifest.get("business_decision_basis_allowed") is False, "business basis must be false")
    require(manifest.get("business_execution_allowed") is False, "business execution must be false")
    require(manifest.get("current_data_quality_grade") == "Q4", "data quality summary mismatch")
    require(manifest.get("current_report_grade") == "D", "report grade summary mismatch")
    require(manifest.get("release_permission") == "blocked", "release permission mismatch")

    raw_boundary = manifest.get("raw_data_boundary", {})
    require(raw_boundary.get("local_raw_data_dir") == RAW_DIR, "raw directory mismatch")
    require(raw_boundary.get("codex_read_allowed_only_when_phase_requires") is True, "raw read policy mismatch")
    require(raw_boundary.get("codex_read_required_by_this_phase") is False, "raw read required mismatch")
    require(raw_boundary.get("codex_read_performed_by_this_phase") is False, "raw read performed mismatch")
    require(raw_boundary.get("codex_modify_allowed") is False, "raw modify must be false")
    require(raw_boundary.get("codex_delete_allowed") is False, "raw delete must be false")
    require(raw_boundary.get("codex_move_allowed") is False, "raw move must be false")
    require(raw_boundary.get("codex_rename_allowed") is False, "raw rename must be false")
    require(raw_boundary.get("codex_overwrite_allowed") is False, "raw overwrite must be false")
    require(raw_boundary.get("codex_generate_inside_allowed") is False, "raw generate-inside must be false")
    require(raw_boundary.get("github_commit_allowed") is False, "raw GitHub commit must be false")

    safety = manifest.get("public_repo_safety", {})
    for key in PUBLIC_SAFETY_FALSE_KEYS:
        require(safety.get(key) is False, f"public_repo_safety.{key} must be false")

    for ref in manifest.get("evidence_refs", []):
        require(Path(ref).exists(), f"missing evidence ref: {ref}")
    _require_public_safe_text(
        [
            ZERO_DELTA_OUTPUT_PATH,
            MISMATCH_OUTPUT_PATH,
            PROJECT_STATUS_OUTPUT_PATH,
            REPORT_PATH,
            TEST_RESULTS_PATH,
        ],
        errors,
    )

    tracked_files = git_output(["ls-files", "KMFA"]).splitlines()
    forbidden_tracked = [
        path
        for path in tracked_files
        if path.lower().endswith(FORBIDDEN_PUBLIC_SUFFIXES) or ".codex_private_runtime/" in path
    ]
    require(not forbidden_tracked, f"forbidden public/private tracked files: {forbidden_tracked}")
    require("codex/kmfa" in git_output(["status", "--short", "--branch"]), "git status must be on codex/kmfa")

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
        "raw_dir_read_performed": manifest["raw_dir_read_performed"],
        "raw_dir_mutation_performed": manifest["raw_dir_mutation_performed"],
        "formal_report_allowed": manifest["formal_report_allowed"],
        "business_execution_allowed": manifest["business_execution_allowed"],
        "next_required_step": manifest["next_required_step"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.3 S06-P3 validation evidence replay.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args()
    try:
        result = validate_v013_s06_p3_validation_evidence_replay(args.manifest)
    except ValidationError as exc:
        print("FAIL: KMFA v0.1.3 S06-P3 validation evidence replay validation failed")
        print(exc)
        return 1
    print(
        "PASS: KMFA v0.1.3 S06-P3 validation evidence replay validated "
        f"(metadata_quality_written={str(result['metadata_quality_written']).lower()}, "
        f"project_statuses={result['project_status_count']}, "
        f"q5_allowed={result['q5_allowed_count']}, "
        f"stage6_review={str(result['stage6_review_performed']).lower()}, "
        f"github_upload={str(result['github_upload_performed']).lower()})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
