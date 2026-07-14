#!/usr/bin/env python3
"""Validate KMFA v0.1.4 S06-P2 cross-source difference queue evidence."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from KMFA.tools.check_v014_s06_p1_zero_delta_validator import validate_v014_s06_p1_zero_delta_validator
from KMFA.tools.cross_source_difference_queue import (
    build_queue_from_fixture,
    evaluate_report_grade_gate,
    validate_queue_item,
)
from KMFA.tools.v014_s06_p2_difference_queue import (
    ACCEPTANCE_ID,
    FIXTURE_PATH,
    GATE_PATH,
    MANIFEST_PATH,
    NEXT_INSTRUCTION,
    NEXT_PHASE,
    PHASE_SCOPE,
    QUEUE_PATH,
    REPORT_PATH,
    RISK_REGISTER_PATH,
    ROLLBACK_PATH,
    SCHEMA_VERSION,
    TASK_ID,
    TEST_RESULTS_PATH,
)


RAW_INBOX_REF = "operator-designated local raw/private inbox outside repository"
FORBIDDEN_TRACKED_SUFFIXES = (".zip", ".xlsx", ".xls", ".xlsm", ".pdf", ".sqlite", ".sqlite3", ".db")
PUBLIC_FALSE_KEYS = (
    "raw_business_data_committed",
    "zip_committed",
    "excel_workbook_committed",
    "pdf_committed",
    "private_csv_committed",
    "sqlite_or_db_committed",
    "credentials_committed",
    "raw_filenames_committed",
    "raw_hashes_committed",
    "directory_tree_plaintext_committed",
    "zip_member_names_committed",
    "sheet_names_committed",
    "source_header_plaintext_committed",
    "row_or_cell_values_committed",
    "source_or_normalized_values_committed",
    "business_values_committed",
)
BOUNDARY_FALSE_KEYS = (
    "raw_inbox_read_required_by_this_phase",
    "raw_inbox_read_by_this_phase",
    "raw_inbox_listed_by_this_phase",
    "raw_inbox_stat_by_this_phase",
    "raw_inbox_hashed_by_this_phase",
    "raw_inbox_modified_by_this_phase",
    "raw_inbox_deleted_by_this_phase",
    "raw_inbox_moved_by_this_phase",
    "raw_inbox_renamed_by_this_phase",
    "raw_inbox_overwritten_by_this_phase",
    "raw_inbox_written_by_this_phase",
    "raw_inbox_mutated_by_this_phase",
    "private_runtime_written_by_this_phase",
    "github_commit_allowed_for_raw",
)
FORBIDDEN_PUBLIC_KEYS = {
    "actual_package_sha256",
    "expected_package_sha256",
    "member_sha256",
    "member_name",
    "member_path",
    "package_name",
    "candidate_label",
    "candidate_label_hash",
    "sheet_name",
    "raw_value",
    "normalized_value",
    "source_header_text",
    "cell_value",
    "row_value",
    "business_value",
    "bank_account_number",
    "identity_document_number",
    "connector_token",
    "connector_password",
    "api_key",
    "private_key",
}
FORBIDDEN_PUBLIC_TEXT = (
    "actual_package_sha256",
    "expected_package_sha256",
    "member_sha256:",
    "member_name:",
    "member_path:",
    "package_name:",
    "candidate_label:",
    "candidate_label_hash:",
    "sheet_name:",
    "raw_value:",
    "normalized_value:",
    "source_header_text:",
    "cell_value:",
    "row_value:",
    "business_value:",
    "bank_statement:",
    "contract_full_text:",
    "salary_detail:",
    "tax_filing:",
    "connector_token:",
    "connector_password:",
    "api_key:",
    "private_key:",
    "-----" "BEGIN",
)
STRICT_SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(?i)(password|passwd|secret|api_key|token)\s*=\s*[^\s,;]{8,}"),
)
RAW_INBOX_DIRECTORY_TOKEN = "KMFA" + "_MetaData"
LOCAL_DOWNLOADS_RAW_PATH_PATTERN = re.compile(r"/Users/[^\s\"'`]+/Downloads/[^\s\"'`]+")


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


def walk_public(value: Any, errors: list[str], path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_PUBLIC_KEYS:
                errors.append(f"forbidden public key {key!r} at {path}")
            walk_public(child, errors, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            walk_public(child, errors, f"{path}[{index}]")


def check_public_safe_file(path: Path, errors: list[str]) -> None:
    require(path.exists(), f"missing evidence file: {path}", errors)
    if not path.exists():
        return
    require(path.suffix.lower() not in FORBIDDEN_TRACKED_SUFFIXES, f"forbidden evidence extension: {path}", errors)
    if path.suffix.lower() in {".md", ".json", ".jsonl", ".csv", ".yaml", ".yml"}:
        text = path.read_text(encoding="utf-8", errors="ignore")
        lower = text.lower()
        for forbidden in FORBIDDEN_PUBLIC_TEXT:
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


def validate_v014_s06_p2_difference_queue(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []
    manifest = read_json(manifest_path)
    fixture = read_json(FIXTURE_PATH)
    queue_items = read_jsonl(QUEUE_PATH)
    gate = read_json(GATE_PATH)
    recomputed_queue_items = build_queue_from_fixture(FIXTURE_PATH)
    recomputed_gate = evaluate_report_grade_gate(recomputed_queue_items)
    s06_p1 = validate_v014_s06_p1_zero_delta_validator()

    for public_value in (manifest, fixture, queue_items, gate):
        walk_public(public_value, errors)

    require(manifest.get("schema_version") == SCHEMA_VERSION, "schema mismatch", errors)
    require(manifest.get("project_id") == "KMFA", "project_id mismatch", errors)
    require(manifest.get("version") == "0.1.4", "version mismatch", errors)
    require(manifest.get("stage_id") == "S06", "stage_id must be S06", errors)
    require(manifest.get("phase_id") == "S06-P2", "phase_id must be S06-P2", errors)
    require(manifest.get("phase_scope") == PHASE_SCOPE, "phase scope mismatch", errors)
    require(manifest.get("task_id") == TASK_ID, "task id mismatch", errors)
    require(manifest.get("acceptance_id") == ACCEPTANCE_ID, "acceptance id mismatch", errors)
    require(
        manifest.get("status") == "completed_validated_local_only_no_go_upload_deferred_difference_queue",
        "status mismatch",
        errors,
    )
    require(manifest.get("completed_task_ids") == ["S06P2T01", "S06P2T02", "S06P2T03"], "task ids mismatch", errors)

    require(manifest.get("s06_p1_dependency_validated") is True, "S06-P1 dependency flag mismatch", errors)
    require(s06_p1.get("phase_id") == "S06-P1", "S06-P1 dependency phase mismatch", errors)
    require(s06_p1.get("one_cent_mismatch_detected") is True, "S06-P1 one-cent dependency mismatch", errors)
    require(s06_p1.get("minimum_fail_difference_cents") == 1, "S06-P1 minimum fail mismatch", errors)
    require(s06_p1.get("metadata_quality_written") is False, "S06-P1 metadata quality must be false", errors)
    require(s06_p1.get("difference_queue_created") is False, "S06-P1 difference queue must be false", errors)
    require(s06_p1.get("github_upload_performed") is False, "S06-P1 upload must be false", errors)
    s06_p1_summary = manifest.get("s06_p1_dependency_summary", {})
    require(s06_p1_summary.get("phase_id") == "S06-P1", "manifest S06-P1 summary phase mismatch", errors)
    require(s06_p1_summary.get("one_cent_mismatch_detected") is True, "manifest S06-P1 summary one-cent mismatch", errors)
    require(s06_p1_summary.get("minimum_fail_difference_cents") == 1, "manifest S06-P1 summary minimum mismatch", errors)
    require(s06_p1_summary.get("metadata_quality_written") is False, "manifest S06-P1 metadata summary mismatch", errors)
    require(s06_p1_summary.get("difference_queue_created") is False, "manifest S06-P1 queue summary mismatch", errors)
    require(s06_p1_summary.get("github_upload_performed") is False, "manifest S06-P1 upload summary mismatch", errors)
    require(s06_p1_summary.get("next_recommended_phase") == "S06-P2", "manifest S06-P1 next phase mismatch", errors)

    require(fixture.get("schema_version") == "kmfa.v014_s06_p2.pdf_excel_conflict_fixture.v1", "fixture schema mismatch", errors)
    require(fixture.get("public_safe_fixture_only") is True, "fixture must be public-safe", errors)
    require(fixture.get("raw_business_data_used") is False, "fixture raw flag mismatch", errors)
    require(fixture.get("pdf_value_cents") == 10000, "fixture pdf cents mismatch", errors)
    require(fixture.get("excel_value_cents") == 9999, "fixture excel cents mismatch", errors)
    require(fixture.get("pdf_source_ref", {}).get("source_type") == "pdf", "fixture PDF source mismatch", errors)
    require(fixture.get("excel_source_ref", {}).get("source_type") == "excel", "fixture Excel source mismatch", errors)

    require(queue_items == recomputed_queue_items, "queue evidence must match recomputed queue output", errors)
    require(gate == recomputed_gate, "gate evidence must match recomputed gate output", errors)
    require(len(queue_items) == 1, "queue must contain one public-safe conflict", errors)
    queue_item = queue_items[0]
    try:
        validate_queue_item(queue_item)
    except Exception as exc:  # pragma: no cover - surfaced in the collected error list.
        errors.append(str(exc))
    require(len(queue_item.get("source_refs", [])) == 2, "queue item must contain exactly two source refs", errors)
    require({ref.get("source_type") for ref in queue_item["source_refs"]} == {"pdf", "excel"}, "source types mismatch", errors)
    require(queue_item.get("status") == "queued_for_manual_review", "queue status mismatch", errors)
    require(queue_item.get("difference_cents") == 1, "difference cents must be 1", errors)
    require(queue_item.get("public_safe_fixture_only") is True, "queue item public-safe flag mismatch", errors)
    require(queue_item.get("raw_business_data_used") is False, "queue item raw flag mismatch", errors)
    require(queue_item.get("raw_layer_write_allowed") is False, "raw layer write must be false", errors)
    require(queue_item.get("raw_source_mutation_allowed") is False, "raw source mutation must be false", errors)
    for flag in ("auto_correction_allowed", "averaging_allowed", "rounding_mask_allowed", "auto_selection_allowed"):
        require(queue_item.get(flag) is False, f"{flag} must be false", errors)
        require(manifest.get(flag) is False, f"manifest {flag} must be false", errors)
    require(queue_item.get("auto_selected_source_id") is None, "auto selected source must be null", errors)
    require(queue_item.get("resolved_value_cents") is None, "resolved value must be null", errors)
    require(queue_item.get("resolution_policy") == "manual_review_required", "resolution policy mismatch", errors)

    require(gate.get("status") == "blocked", "gate status must be blocked", errors)
    require(gate.get("report_grade_a_allowed") is False, "report grade A must be blocked", errors)
    require(gate.get("maximum_report_grade") == "B", "maximum report grade must be B while unresolved", errors)
    require(gate.get("hard_block_reason") == "unresolved_critical_difference", "hard block reason mismatch", errors)
    require(gate.get("blocking_queue_ids") == [queue_item["queue_id"]], "blocking queue ids mismatch", errors)
    require(gate.get("public_safe_fixture_only") is True, "gate public-safe flag mismatch", errors)
    require(gate.get("raw_business_data_used") is False, "gate raw flag mismatch", errors)

    require(manifest.get("queue_item_count") == 1, "manifest queue count mismatch", errors)
    require(manifest.get("queue_ids") == [queue_item["queue_id"]], "manifest queue ids mismatch", errors)
    require(manifest.get("queue_statuses") == ["queued_for_manual_review"], "manifest queue statuses mismatch", errors)
    require(manifest.get("pdf_excel_conflict_detected") is True, "PDF/Excel conflict flag mismatch", errors)
    require(manifest.get("source_types") == ["excel", "pdf"], "manifest source types mismatch", errors)
    require(manifest.get("difference_cents") == 1, "manifest difference mismatch", errors)
    require(manifest.get("absolute_difference_cents") == 1, "manifest absolute difference mismatch", errors)
    require(manifest.get("minimum_queue_difference_cents") == 1, "minimum queue difference mismatch", errors)
    require(manifest.get("report_grade_a_allowed") is False, "manifest report grade A mismatch", errors)
    require(manifest.get("maximum_report_grade") == "B", "manifest maximum report grade mismatch", errors)
    require(manifest.get("hard_block_reason") == "unresolved_critical_difference", "manifest hard block mismatch", errors)
    require(manifest.get("blocking_queue_ids") == [queue_item["queue_id"]], "manifest blocking ids mismatch", errors)
    require(manifest.get("manual_review_required") is True, "manual review required mismatch", errors)
    require(manifest.get("difference_closed") is False, "difference must remain unclosed", errors)
    require(manifest.get("integer_cent_comparison_only") is True, "integer-cent flag mismatch", errors)
    require(manifest.get("float_money_allowed") is False, "float money must be disallowed", errors)

    require(manifest.get("raw_business_data_used") is False, "raw business data must not be used", errors)
    require(manifest.get("actual_business_difference_validated") is False, "actual business validation belongs to later gated work", errors)
    require(manifest.get("metadata_quality_written") is False, "metadata quality write belongs to S06-P3", errors)
    require(
        manifest.get("source_difference_queue_metadata_written") is False,
        "metadata source difference queue write belongs to S06-P3",
        errors,
    )
    for key in (
        "s06_p3_started",
        "stage6_review_performed",
        "github_upload_performed",
        "raw_value_matching_performed",
        "lineage_full_check_performed",
        "formal_report_performed",
        "live_connector_called",
        "opme_deep_coupling_performed",
        "business_execution_performed",
    ):
        require(manifest.get(key) is False, f"{key} must be false", errors)
    require(
        manifest.get("github_upload_status") == "not_uploaded_deferred_until_v014_stage1_18_complete",
        "github upload status mismatch",
        errors,
    )

    boundary = manifest.get("raw_data_boundary", {})
    require(boundary.get("raw_inbox_ref") == RAW_INBOX_REF, "raw inbox ref mismatch", errors)
    require("raw_inbox_path" not in boundary, "raw inbox absolute path must not be public evidence", errors)
    for key in BOUNDARY_FALSE_KEYS:
        require(boundary.get(key) is False, f"raw_data_boundary.{key} must be false", errors)

    safety = manifest.get("public_repo_safety", {})
    for key in PUBLIC_FALSE_KEYS:
        require(safety.get(key) is False, f"public_repo_safety.{key} must be false", errors)

    release = manifest.get("release_state", {})
    require(release.get("current_data_quality_grade") == "Q4", "data quality grade mismatch", errors)
    require(release.get("current_report_grade") == "D", "report grade mismatch", errors)
    require(release.get("current_go_no_go") == "NO_GO", "Go/No-Go mismatch", errors)
    require(release.get("release_permission") == "blocked", "release permission mismatch", errors)
    for key in (
        "delivery_allowed",
        "formal_report_allowed",
        "business_decision_basis_allowed",
        "business_execution_allowed",
        "github_main_upload_allowed",
    ):
        require(release.get(key) is False, f"release_state.{key} must be false", errors)

    require(manifest.get("next_recommended_phase") == NEXT_PHASE, "next phase mismatch", errors)
    require(manifest.get("next_phase_instruction") == NEXT_INSTRUCTION, "next instruction mismatch", errors)

    for ref in manifest.get("evidence_refs", []):
        check_public_safe_file(Path(ref), errors)
    for path in (
        REPORT_PATH,
        TEST_RESULTS_PATH,
        RISK_REGISTER_PATH,
        ROLLBACK_PATH,
        MANIFEST_PATH,
        FIXTURE_PATH,
        QUEUE_PATH,
        GATE_PATH,
    ):
        check_public_safe_file(path, errors)

    tracked_files = git_output(["ls-files", "KMFA"]).splitlines()
    forbidden_tracked = [
        path for path in tracked_files if path.lower().endswith(FORBIDDEN_TRACKED_SUFFIXES) or ".codex_private_runtime/" in path
    ]
    require(not forbidden_tracked, f"forbidden tracked raw/private artifacts: {forbidden_tracked}", errors)
    require("codex/kmfa" in git_output(["status", "--short", "--branch"]), "git status must be on codex/kmfa", errors)

    if errors:
        raise ValidationError("\n".join(f"- {error}" for error in errors))
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.4 S06-P2 difference queue evidence.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args(argv)
    try:
        manifest = validate_v014_s06_p2_difference_queue(args.manifest)
    except ValidationError as exc:
        print("FAIL: KMFA v0.1.4 S06-P2 difference queue validation failed")
        print(exc)
        return 1
    print(
        "PASS: KMFA v0.1.4 S06-P2 difference queue validated "
        f"(queue_items={manifest['queue_item_count']}, "
        f"difference_cents={manifest['difference_cents']}, "
        f"report_grade_a_allowed={str(manifest['report_grade_a_allowed']).lower()}, "
        f"metadata_quality_written={str(manifest['metadata_quality_written']).lower()}, "
        f"github_upload={str(manifest['github_upload_performed']).lower()})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
