#!/usr/bin/env python3
"""Validate KMFA v0.1.3 S06-P2 difference queue replay evidence."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from KMFA.tools.check_v013_s06_p1_zero_delta_replay import validate_v013_s06_p1_zero_delta_replay
from KMFA.tools.cross_source_difference_queue import (
    build_queue_from_fixture,
    evaluate_report_grade_gate,
    validate_queue_item,
)
from KMFA.tools.v013_s06_p2_difference_queue_replay import (
    FIXTURE_PATH,
    GATE_PATH,
    MANIFEST_PATH,
    NEXT_REQUIRED_STEP,
    PHASE_SCOPE,
    QUEUE_PATH,
    REPORT_PATH,
    SCHEMA_VERSION,
    TASK_ID,
    TEST_RESULTS_PATH,
)


RAW_DIR = "/Users/linzezhang/Downloads/KMFA_MetaData"
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
FORBIDDEN_EVIDENCE_TEXT = (
    "raw_value:",
    "normalized_value:",
    "source_header_text:",
    "actual_package_sha256",
    "member_sha256:",
    "bank_statement",
    "contract_full_text",
    "salary_detail",
    "tax_filing",
    "-----" "BEGIN",
    "s" "k-",
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


def validate_v013_s06_p2_difference_queue_replay(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    manifest = read_json(manifest_path)
    fixture = read_json(FIXTURE_PATH)
    queue_items = read_jsonl(QUEUE_PATH)
    gate = read_json(GATE_PATH)
    recomputed_queue_items = build_queue_from_fixture(FIXTURE_PATH)
    recomputed_gate = evaluate_report_grade_gate(recomputed_queue_items)
    s06_p1 = validate_v013_s06_p1_zero_delta_replay()

    require(manifest.get("schema_version") == SCHEMA_VERSION, "manifest schema mismatch")
    require(manifest.get("project_id") == "KMFA", "project_id mismatch")
    require(manifest.get("version") == "0.1.3", "version mismatch")
    require(manifest.get("stage_id") == "S06", "stage_id must be S06")
    require(manifest.get("phase_id") == "S06-P2", "phase_id must be S06-P2")
    require(manifest.get("phase_scope") == PHASE_SCOPE, "phase scope mismatch")
    require(manifest.get("task_id") == TASK_ID, "task_id mismatch")
    require(
        manifest.get("status") == "completed_validated_local_only_upload_deferred_difference_queue_replay",
        "status mismatch",
    )
    require(manifest.get("completed_task_ids") == ["S6PBT01", "S6PBT02", "S6PBT03"], "task ids mismatch")
    require(
        manifest.get("acceptance_ids") == ["ACC-V013-S06-P2-DIFFERENCE-QUEUE-REPLAY"],
        "acceptance ids mismatch",
    )
    require(manifest.get("next_required_step") == NEXT_REQUIRED_STEP, "next_required_step mismatch")

    require(manifest.get("s06_p1_dependency_validated") is True, "S06-P1 dependency flag mismatch")
    require(s06_p1.get("phase_id") == "S06-P1", "S06-P1 dependency phase mismatch")
    require(s06_p1.get("one_cent_mismatch_detected") is True, "S06-P1 one-cent dependency mismatch")
    require(s06_p1.get("minimum_fail_difference_cents") == 1, "S06-P1 minimum fail mismatch")
    require(s06_p1.get("metadata_quality_written") is False, "S06-P1 metadata quality must be false")
    require(s06_p1.get("difference_queue_created") is False, "S06-P1 difference queue must be false")
    require(s06_p1.get("github_upload_performed") is False, "S06-P1 upload must be false")
    s06_p1_summary = manifest.get("s06_p1_dependency_summary", {})
    require(s06_p1_summary.get("phase_id") == "S06-P1", "manifest S06-P1 summary phase mismatch")
    require(s06_p1_summary.get("one_cent_mismatch_detected") is True, "manifest S06-P1 summary one-cent mismatch")
    require(s06_p1_summary.get("minimum_fail_difference_cents") == 1, "manifest S06-P1 summary minimum mismatch")
    require(s06_p1_summary.get("metadata_quality_written") is False, "manifest S06-P1 metadata summary mismatch")
    require(s06_p1_summary.get("difference_queue_created") is False, "manifest S06-P1 queue summary mismatch")
    require(s06_p1_summary.get("github_upload_performed") is False, "manifest S06-P1 upload summary mismatch")

    require(fixture.get("schema_version") == "kmfa.v013_s06_p2.pdf_excel_conflict_fixture.v1", "fixture schema mismatch")
    require(fixture.get("public_safe_fixture_only") is True, "fixture must be public-safe")
    require(fixture.get("raw_business_data_used") is False, "fixture raw flag mismatch")
    require(fixture.get("pdf_value_cents") == 10000, "fixture pdf cents mismatch")
    require(fixture.get("excel_value_cents") == 9999, "fixture excel cents mismatch")
    require(fixture.get("pdf_source_ref", {}).get("source_type") == "pdf", "fixture PDF source mismatch")
    require(fixture.get("excel_source_ref", {}).get("source_type") == "excel", "fixture Excel source mismatch")

    require(queue_items == recomputed_queue_items, "queue evidence must match recomputed queue output")
    require(gate == recomputed_gate, "gate evidence must match recomputed gate output")
    require(len(queue_items) == 1, "queue must contain one public-safe conflict")
    queue_item = queue_items[0]
    validate_queue_item(queue_item)
    require(len(queue_item.get("source_refs", [])) == 2, "queue item must contain exactly two source refs")
    require({ref.get("source_type") for ref in queue_item["source_refs"]} == {"pdf", "excel"}, "source types mismatch")
    require(queue_item.get("status") == "queued_for_manual_review", "queue status mismatch")
    require(queue_item.get("difference_cents") == 1, "difference cents must be 1")
    require(queue_item.get("public_safe_fixture_only") is True, "queue item public-safe flag mismatch")
    require(queue_item.get("raw_business_data_used") is False, "queue item raw flag mismatch")
    require(queue_item.get("raw_layer_write_allowed") is False, "raw layer write must be false")
    require(queue_item.get("raw_source_mutation_allowed") is False, "raw source mutation must be false")
    for flag in ("auto_correction_allowed", "averaging_allowed", "rounding_mask_allowed", "auto_selection_allowed"):
        require(queue_item.get(flag) is False, f"{flag} must be false")
        require(manifest.get(flag) is False, f"manifest {flag} must be false")
    require(queue_item.get("auto_selected_source_id") is None, "auto selected source must be null")
    require(queue_item.get("resolved_value_cents") is None, "resolved value must be null")
    require(queue_item.get("resolution_policy") == "manual_review_required", "resolution policy mismatch")

    require(gate.get("status") == "blocked", "gate status must be blocked")
    require(gate.get("report_grade_a_allowed") is False, "report grade A must be blocked")
    require(gate.get("maximum_report_grade") == "B", "maximum report grade must be B while unresolved")
    require(gate.get("hard_block_reason") == "unresolved_critical_difference", "hard block reason mismatch")
    require(gate.get("blocking_queue_ids") == [queue_item["queue_id"]], "blocking queue ids mismatch")
    require(gate.get("public_safe_fixture_only") is True, "gate public-safe flag mismatch")
    require(gate.get("raw_business_data_used") is False, "gate raw flag mismatch")

    require(manifest.get("queue_item_count") == 1, "manifest queue count mismatch")
    require(manifest.get("queue_ids") == [queue_item["queue_id"]], "manifest queue ids mismatch")
    require(manifest.get("queue_statuses") == ["queued_for_manual_review"], "manifest queue statuses mismatch")
    require(manifest.get("pdf_excel_conflict_detected") is True, "PDF/Excel conflict flag mismatch")
    require(manifest.get("source_types") == ["excel", "pdf"], "manifest source types mismatch")
    require(manifest.get("difference_cents") == 1, "manifest difference mismatch")
    require(manifest.get("absolute_difference_cents") == 1, "manifest absolute difference mismatch")
    require(manifest.get("minimum_queue_difference_cents") == 1, "minimum queue difference mismatch")
    require(manifest.get("report_grade_a_allowed") is False, "manifest report grade A mismatch")
    require(manifest.get("maximum_report_grade") == "B", "manifest maximum report grade mismatch")
    require(manifest.get("hard_block_reason") == "unresolved_critical_difference", "manifest hard block mismatch")
    require(manifest.get("blocking_queue_ids") == [queue_item["queue_id"]], "manifest blocking ids mismatch")
    require(manifest.get("manual_review_required") is True, "manual review required mismatch")
    require(manifest.get("difference_closed") is False, "difference must remain unclosed")
    require(manifest.get("integer_cent_comparison_only") is True, "integer-cent flag mismatch")
    require(manifest.get("float_money_allowed") is False, "float money must be disallowed")

    require(manifest.get("raw_business_data_used") is False, "raw business data must not be used")
    require(manifest.get("raw_dir_read_performed") is False, "raw dir read must be false")
    require(manifest.get("raw_dir_mutation_performed") is False, "raw dir mutation must be false")
    require(manifest.get("metadata_quality_written") is False, "metadata quality write belongs to S06-P3")
    require(
        manifest.get("source_difference_queue_metadata_written") is False,
        "metadata source difference queue write belongs to S06-P3",
    )
    require(manifest.get("stage6_review_performed") is False, "Stage 6 review must not be performed")
    require(manifest.get("s06_p3_performed") is False, "S06-P3 must not be performed")
    require(manifest.get("github_upload_performed") is False, "GitHub upload must not be performed")
    require(
        manifest.get("github_upload_deferred_until_stage10_batch") is True,
        "GitHub upload must be deferred until Stage 1-10 batch",
    )
    require(manifest.get("formal_report_allowed") is False, "formal report must remain blocked")
    require(manifest.get("business_decision_basis_allowed") is False, "business basis must remain false")
    require(manifest.get("business_execution_allowed") is False, "business execution must remain false")
    require(manifest.get("current_data_quality_grade") == "Q2", "data quality summary mismatch")
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
    for evidence in (REPORT_PATH, TEST_RESULTS_PATH):
        require(evidence.exists(), f"missing human evidence: {evidence}")
        if evidence.exists():
            text = evidence.read_text(encoding="utf-8")
            for forbidden in FORBIDDEN_EVIDENCE_TEXT:
                require(forbidden not in text, f"forbidden evidence text {forbidden!r} in {evidence}")

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
        "queue_item_count": manifest["queue_item_count"],
        "pdf_excel_conflict_detected": manifest["pdf_excel_conflict_detected"],
        "difference_cents": manifest["difference_cents"],
        "auto_correction_allowed": manifest["auto_correction_allowed"],
        "averaging_allowed": manifest["averaging_allowed"],
        "rounding_mask_allowed": manifest["rounding_mask_allowed"],
        "auto_selection_allowed": manifest["auto_selection_allowed"],
        "report_grade_a_allowed": manifest["report_grade_a_allowed"],
        "maximum_report_grade": manifest["maximum_report_grade"],
        "hard_block_reason": manifest["hard_block_reason"],
        "metadata_quality_written": manifest["metadata_quality_written"],
        "source_difference_queue_metadata_written": manifest["source_difference_queue_metadata_written"],
        "stage6_review_performed": manifest["stage6_review_performed"],
        "s06_p3_performed": manifest["s06_p3_performed"],
        "github_upload_performed": manifest["github_upload_performed"],
        "raw_dir_read_performed": manifest["raw_dir_read_performed"],
        "raw_dir_mutation_performed": manifest["raw_dir_mutation_performed"],
        "formal_report_allowed": manifest["formal_report_allowed"],
        "business_execution_allowed": manifest["business_execution_allowed"],
        "next_required_step": manifest["next_required_step"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.3 S06-P2 difference queue replay evidence.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args()
    try:
        result = validate_v013_s06_p2_difference_queue_replay(args.manifest)
    except ValidationError as exc:
        print("FAIL: KMFA v0.1.3 S06-P2 difference queue replay validation failed")
        print(exc)
        return 1
    print(
        "PASS: KMFA v0.1.3 S06-P2 difference queue replay validated "
        f"(queue_items={result['queue_item_count']}, "
        f"difference_cents={result['difference_cents']}, "
        f"report_grade_a_allowed={str(result['report_grade_a_allowed']).lower()}, "
        f"metadata_quality_written={str(result['metadata_quality_written']).lower()}, "
        f"github_upload={str(result['github_upload_performed']).lower()})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
