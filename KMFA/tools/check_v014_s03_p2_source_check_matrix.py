#!/usr/bin/env python3
"""Validate KMFA v1.4 S03-P2 source check matrix evidence."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from KMFA.tools.check_v014_s03_p1_file_registration import validate_v014_s03_p1_file_registration
from KMFA.tools.source_check_matrix import ALLOWED_STATUSES, REQUIRED_DIMENSIONS
from KMFA.tools.v014_s03_p2_source_check_matrix import (
    ACCEPTANCE_ID,
    MANIFEST_PATH,
    MATRIX_PATH,
    PROTOCOL_PATH,
    PUBLIC_REGISTER_PATH,
    REPORT_PATH,
    RISK_REGISTER_PATH,
    ROLLBACK_PLAN_PATH,
    STATUS_EVENTS_PATH,
    TASK_ID,
    TEST_RESULTS_PATH,
)


FORBIDDEN_EXTENSIONS = {".zip", ".xlsx", ".xls", ".xlsm", ".pdf", ".sqlite", ".sqlite3", ".db"}
PUBLIC_FORBIDDEN_TEXT = (
    "original_filename",
    "relative_path",
    "content_sha256",
    "member_path",
    "sheet_name",
    "source_header_text",
    "raw_value:",
    "normalized_value:",
    "cell_value:",
    "row_value:",
    "bank_statement:",
    "contract_full_text:",
    "salary_detail:",
    "tax_filing:",
    "connector_token:",
    "connector_password:",
    "api_key:",
    "private_key:",
    "-----" "BEGIN",
    "s" "k-",
)
PUBLIC_SAFETY_FALSE_KEYS = (
    "raw_business_data_committed",
    "raw_filenames_committed",
    "raw_hashes_committed",
    "directory_tree_plaintext_committed",
    "zip_member_names_committed",
    "field_or_header_plaintext_committed",
    "raw_or_normalized_values_committed",
    "zip_committed",
    "excel_workbook_committed",
    "pdf_committed",
    "private_csv_committed",
    "sqlite_or_db_committed",
    "credentials_committed",
)
PHASE_SCOPE_FALSE_KEYS = (
    "raw_root_read_performed_by_this_phase",
    "raw_root_list_performed_by_this_phase",
    "raw_root_hash_performed_by_this_phase",
    "raw_root_mutation_performed",
    "s03_p3_started",
    "stage3_review_performed",
    "github_upload_performed",
    "raw_value_matching_performed",
    "field_mapping_performed",
    "formal_report_performed",
    "business_execution_performed",
    "next_phase_started",
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
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValidationError(f"{path}:{line_number} must contain a JSON object")
        records.append(value)
    return records


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


def check_public_safe_file(path: Path, errors: list[str]) -> None:
    require(path.exists(), f"missing evidence file: {path}", errors)
    if not path.exists():
        return
    require(path.suffix.lower() not in FORBIDDEN_EXTENSIONS, f"forbidden evidence extension: {path}", errors)
    if path.suffix.lower() in {".md", ".json", ".jsonl", ".csv", ".yaml", ".yml", ".py"}:
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        for forbidden in PUBLIC_FORBIDDEN_TEXT:
            require(forbidden.lower() not in text, f"forbidden public text {forbidden!r} in {path}", errors)


def validate_v014_s03_p2_source_check_matrix(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []
    manifest = read_json(manifest_path)
    matrix_rows = read_jsonl(MATRIX_PATH)
    status_events = read_jsonl(STATUS_EVENTS_PATH)
    protocol = read_json(PROTOCOL_PATH)
    public_register = read_json(PUBLIC_REGISTER_PATH)
    dependency = validate_v014_s03_p1_file_registration()

    require(manifest.get("schema_version") == "kmfa.v014_s03_p2_source_check_matrix.v1", "schema mismatch", errors)
    require(manifest.get("project_id") == "KMFA", "project_id mismatch", errors)
    require(manifest.get("version") == "0.1.4", "version mismatch", errors)
    require(manifest.get("stage_id") == "S03", "stage_id must be S03", errors)
    require(manifest.get("phase_id") == "S03-P2", "phase_id must be S03-P2", errors)
    require(manifest.get("task_id") == TASK_ID, "task_id mismatch", errors)
    require(manifest.get("acceptance_id") == ACCEPTANCE_ID, "acceptance_id mismatch", errors)
    require(manifest.get("status") == "completed_validated_local_only_no_go_upload_deferred", "status mismatch", errors)
    require(dependency.get("phase_id") == "S03-P1", "S03-P1 dependency phase mismatch", errors)
    require(dependency.get("status") == "completed_validated_local_only_no_go_upload_deferred", "S03-P1 dependency status mismatch", errors)

    phase_scope = manifest.get("phase_scope", {})
    require(phase_scope.get("current_phase_only") is True, "current_phase_only must be true", errors)
    require(phase_scope.get("source_check_matrix_only") is True, "source_check_matrix_only must be true", errors)
    require(phase_scope.get("uses_s03_p1_public_register_only") is True, "S03-P1 public register dependency missing", errors)
    require(phase_scope.get("next_phase") == "S03-P3", "next phase mismatch", errors)
    for key in PHASE_SCOPE_FALSE_KEYS:
        require(phase_scope.get(key) is False, f"phase_scope.{key} must be false", errors)

    summary = manifest.get("source_check_matrix_summary", {})
    public_file_records = public_register.get("public_file_records", [])
    public_file_ids = {str(record.get("public_file_id")) for record in public_file_records if isinstance(record, dict)}
    require(summary.get("matrix_row_count") == len(matrix_rows) == len(public_file_ids), "matrix row count mismatch", errors)
    require(summary.get("status_event_count") == len(status_events) == len(public_file_ids), "status event count mismatch", errors)
    require(summary.get("public_file_count_from_s03_p1") == public_register.get("scan_summary", {}).get("file_count"), "S03-P1 public file count mismatch", errors)
    require(summary.get("required_dimensions") == list(REQUIRED_DIMENSIONS), "required dimensions mismatch", errors)
    require(summary.get("required_dimension_count") == len(REQUIRED_DIMENSIONS) == 6, "required dimension count mismatch", errors)
    require(summary.get("allowed_statuses") == list(ALLOWED_STATUSES), "allowed statuses mismatch", errors)
    require(summary.get("allowed_status_count") == len(ALLOWED_STATUSES) == 5, "allowed status count mismatch", errors)
    require(summary.get("status_counts", {}).get("人工复核") == len(public_file_ids), "manual review count mismatch", errors)
    require(summary.get("event_target_layer_counts", {}).get("metadata") == len(public_file_ids), "event target count mismatch", errors)

    seen_matrix_ids: set[str] = set()
    event_ids_by_row: dict[str, dict[str, Any]] = {}
    for event in status_events:
        require(event.get("record_type") == "source_status_event", "status event record_type mismatch", errors)
        require(event.get("schema_version") == "kmfa.v014_s03_p2.source_status_event.v1", "status event schema mismatch", errors)
        require(event.get("event_type") == "initial_status_assignment", "event type mismatch", errors)
        require(re.fullmatch(r"SSE-V014-S03P2-[0-9]{6}", str(event.get("event_id"))) is not None, "event id mismatch", errors)
        require(event.get("previous_status") is None, "initial event previous_status must be null", errors)
        require(event.get("new_status") in ALLOWED_STATUSES, "event new_status not allowed", errors)
        require(event.get("target_layer") == "metadata", "event target layer must be metadata", errors)
        require(event.get("append_only") is True, "event must be append-only", errors)
        require(event.get("raw_layer_write_allowed") is False, "event raw layer write must be false", errors)
        require(event.get("raw_source_mutation_allowed") is False, "event raw source mutation must be false", errors)
        event_ids_by_row[str(event.get("matrix_id"))] = event

    for row in matrix_rows:
        require(row.get("record_type") == "source_check_matrix_row", "matrix row record_type mismatch", errors)
        require(row.get("schema_version") == "kmfa.v014_s03_p2.source_check_matrix_row.v1", "matrix row schema mismatch", errors)
        require(row.get("stage_phase") == "S03-P2", "matrix row phase mismatch", errors)
        matrix_id = str(row.get("matrix_id"))
        require(re.fullmatch(r"SCM-V014-S03P2-[a-f0-9]{16}", matrix_id) is not None, "matrix id mismatch", errors)
        require(matrix_id not in seen_matrix_ids, "duplicate matrix id", errors)
        seen_matrix_ids.add(matrix_id)
        require(str(row.get("public_file_id")) in public_file_ids, "row public file id not in S03-P1 register", errors)
        for dimension in REQUIRED_DIMENSIONS:
            require(dimension in row, f"missing required dimension {dimension}", errors)
        require(row.get("status") in ALLOWED_STATUSES, "row status not allowed", errors)
        require(row.get("allowed_statuses") == list(ALLOWED_STATUSES), "row allowed statuses mismatch", errors)
        require(row.get("raw_layer_write_allowed") is False, "row raw layer write must be false", errors)
        require(row.get("raw_source_mutation_allowed") is False, "row raw source mutation must be false", errors)
        require(row.get("raw_filename_committed") is False, "row raw filename committed must be false", errors)
        require(row.get("raw_hash_committed") is False, "row raw hash committed must be false", errors)
        require(row.get("field_or_header_plaintext_committed") is False, "row field/header plaintext must be false", errors)
        require(row.get("raw_or_normalized_value_committed") is False, "row raw value must be false", errors)
        source_package_ref = row.get("source_package_ref", {})
        require(isinstance(source_package_ref, dict), "source_package_ref must be object", errors)
        require(source_package_ref.get("content_hash_status") == "computed_private_only", "content hash status mismatch", errors)
        require(source_package_ref.get("path_status") == "private_only", "path status mismatch", errors)
        event = event_ids_by_row.get(matrix_id)
        require(event is not None, "missing status event for matrix row", errors)
        if event:
            require(event.get("event_id") == row.get("status_event_ref"), "status event ref mismatch", errors)
            require(event.get("public_file_id") == row.get("public_file_id"), "event public file id mismatch", errors)
            require(event.get("new_status") == row.get("status"), "event status mismatch", errors)

    for safety in (manifest.get("public_repo_safety", {}), protocol.get("public_repo_safety", {})):
        for key in PUBLIC_SAFETY_FALSE_KEYS:
            require(safety.get(key) is False, f"public_repo_safety.{key} must be false", errors)
    protocol_non_scope = protocol.get("non_scope", {})
    for key in (
        "s03_p3_source_priority_started",
        "stage3_review_performed",
        "github_upload_performed",
        "raw_value_matching_performed",
        "field_mapping_performed",
        "formal_report_performed",
        "business_execution_performed",
    ):
        require(protocol_non_scope.get(key) is False, f"protocol.non_scope.{key} must be false", errors)

    release = manifest.get("release_state", {})
    require(release.get("current_data_quality_grade") == "Q2", "quality grade must be Q2", errors)
    require(release.get("current_report_grade") == "D", "report grade must be D", errors)
    require(release.get("current_go_no_go") == "NO_GO", "Go/No-Go must be NO_GO", errors)
    require(release.get("release_permission") == "blocked", "release permission must be blocked", errors)
    for key in (
        "delivery_allowed",
        "formal_report_allowed",
        "business_decision_basis_allowed",
        "business_execution_allowed",
        "github_main_upload_allowed",
    ):
        require(release.get(key) is False, f"release_state.{key} must be false", errors)

    require(protocol.get("schema_version") == "kmfa.source_check_matrix.v1_4.s03_p2", "protocol schema mismatch", errors)
    require(protocol.get("matrix_file") == MATRIX_PATH.as_posix(), "protocol matrix ref mismatch", errors)
    require(protocol.get("status_event_file") == STATUS_EVENTS_PATH.as_posix(), "protocol status event ref mismatch", errors)
    require(protocol.get("status_changes_append_only") is True, "protocol append-only mismatch", errors)
    require(protocol.get("status_changes_target_layer") == "metadata", "protocol target layer mismatch", errors)
    require(protocol.get("raw_root_read_performed_by_this_phase") is False, "protocol raw read must be false", errors)
    require(protocol.get("raw_root_mutation_performed") is False, "protocol raw mutation must be false", errors)

    for path in (
        MANIFEST_PATH,
        MATRIX_PATH,
        STATUS_EVENTS_PATH,
        PROTOCOL_PATH,
        REPORT_PATH,
        TEST_RESULTS_PATH,
        RISK_REGISTER_PATH,
        ROLLBACK_PLAN_PATH,
    ):
        check_public_safe_file(path, errors)

    tracked_files = git_output(["ls-files", "KMFA"]).splitlines()
    forbidden_tracked = [
        path for path in tracked_files if path.lower().endswith(tuple(FORBIDDEN_EXTENSIONS)) or ".codex_private_runtime/" in path
    ]
    require(not forbidden_tracked, f"forbidden tracked raw/private files: {forbidden_tracked}", errors)
    require("codex/kmfa" in git_output(["status", "--short", "--branch"]), "git status must be on codex/kmfa", errors)

    validation = manifest.get("validation_summary", {})
    for key in (
        "s03_p1_dependency",
        "v014_s03_p2_validator",
        "focused_unit_test",
        "governance_validator",
        "raw_private_scan",
        "public_raw_leak_scan",
        "secret_scan",
        "diff_check",
    ):
        require(validation.get(key) in {"PENDING", "PASS"}, f"validation_summary.{key} must be PENDING or PASS", errors)

    if errors:
        raise ValidationError("\n".join(errors))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA v1.4 S03-P2 source check matrix evidence.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args()
    try:
        manifest = validate_v014_s03_p2_source_check_matrix(args.manifest)
    except ValidationError as exc:
        print("FAIL: KMFA v1.4 S03-P2 validation failed")
        print(exc)
        return 1
    summary = manifest["source_check_matrix_summary"]
    print(
        "PASS: KMFA v1.4 S03-P2 source check matrix validated "
        f"(rows={summary['matrix_row_count']}, events={summary['status_event_count']}, "
        f"statuses={summary['allowed_status_count']}, raw_read=false, github_upload=false, "
        f"next={manifest['next_recommended_phase']})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
