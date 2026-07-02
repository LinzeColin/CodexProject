#!/usr/bin/env python3
"""Validate KMFA v0.1.3 Stage 6 review evidence."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from KMFA.tools.check_v013_s06_p1_zero_delta_replay import validate_v013_s06_p1_zero_delta_replay
from KMFA.tools.check_v013_s06_p2_difference_queue_replay import (
    validate_v013_s06_p2_difference_queue_replay,
)
from KMFA.tools.check_v013_s06_p3_validation_evidence_replay import (
    validate_v013_s06_p3_validation_evidence_replay,
)
from KMFA.tools.v013_s06_stage_review import (
    MANIFEST_PATH,
    NEXT_REQUIRED_STEP,
    RAW_DIR,
    REPORT_PATH,
    REVIEW_SCOPE,
    SCHEMA_VERSION,
    TASK_ID,
    TEST_RESULTS_PATH,
)


PHASE_MANIFESTS = {
    "S06-P1": Path("KMFA/stage_artifacts/V013_S06_P1_ZERO_DELTA_REPLAY/machine/zero_delta_replay_manifest.json"),
    "S06-P2": Path(
        "KMFA/stage_artifacts/V013_S06_P2_DIFFERENCE_QUEUE_REPLAY/machine/difference_queue_replay_manifest.json"
    ),
    "S06-P3": Path(
        "KMFA/stage_artifacts/V013_S06_P3_VALIDATION_EVIDENCE_REPLAY/machine/validation_evidence_replay_manifest.json"
    ),
}
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
    "authority_system_amount_values_committed",
    "pdf_excel_amount_values_committed",
    "stage_review_raw_rows_committed",
)
REQUIRED_HARD_BLOCKS = (
    "raw_data_mutation_forbidden",
    "raw_value_publication_forbidden",
    "field_header_plaintext_publication_forbidden",
    "zero_delta_failed_for_one_cent_mismatch_fixture",
    "unresolved_critical_difference",
    "q5_forbidden_until_zero_delta_and_difference_closure",
    "report_grade_a_blocked_until_difference_closure",
    "raw_value_matching_not_performed",
    "lineage_full_check_not_performed",
    "formal_report_release_blocked",
    "github_upload_deferred_until_stage10_batch",
    "business_execution_blocked",
)
FORBIDDEN_EVIDENCE_TEXT = (
    "raw_value:",
    "normalized_value:",
    "source_header_text:",
    "authoritative_value_cents",
    "system_value_cents",
    "pdf_value_cents",
    "excel_value_cents",
    "contract_amount_cents",
    "bank_statement",
    "contract_full_text",
    "salary_detail",
    "tax_filing",
    "-----" "BEGIN",
    "s" "k-",
)
FORBIDDEN_PUBLIC_SUFFIXES = (".zip", ".xlsx", ".xls", ".xlsm", ".pdf", ".sqlite", ".db")


class ValidationError(Exception):
    pass


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ValidationError(f"missing JSON file: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValidationError(f"{path} must contain a JSON object")
    return value


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


def validate_v013_s06_stage_review(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    manifest = read_json(manifest_path)
    p1_result = validate_v013_s06_p1_zero_delta_replay()
    p2_result = validate_v013_s06_p2_difference_queue_replay()
    p3_result = validate_v013_s06_p3_validation_evidence_replay()

    require(manifest.get("schema_version") == SCHEMA_VERSION, "manifest schema mismatch")
    require(manifest.get("project_id") == "KMFA", "project_id mismatch")
    require(manifest.get("version") == "0.1.3", "version mismatch")
    require(manifest.get("stage_id") == "S06", "stage_id must be S06")
    require(manifest.get("review_id") == TASK_ID, "review_id mismatch")
    require(manifest.get("task_id") == TASK_ID, "task_id mismatch")
    require(manifest.get("review_scope") == REVIEW_SCOPE, "review scope mismatch")
    require(manifest.get("status") == "passed_local_stage_review_upload_deferred", "status mismatch")
    require(manifest.get("stage_review_performed") is True, "stage review must be performed")
    require(manifest.get("github_upload_ready_next_gate") is False, "GitHub upload ready must stay false")
    require(
        manifest.get("github_upload_deferred_until_stage10_batch") is True,
        "GitHub upload must be deferred until Stage 1-10 batch",
    )
    require(manifest.get("github_upload_performed") is False, "GitHub upload must not be performed")
    require(
        manifest.get("github_upload_status") == "not_uploaded_deferred_until_stage10_batch",
        "GitHub upload status mismatch",
    )
    require(manifest.get("legacy_stage6_upload_artifacts_current_gate") is False, "legacy upload must not be current")
    require(manifest.get("delivery_allowed") is False, "delivery_allowed must remain false")
    require(manifest.get("formal_report_allowed") is False, "formal_report_allowed must remain false")
    require(manifest.get("business_decision_basis_allowed") is False, "business basis must remain false")
    require(manifest.get("business_execution_allowed") is False, "business execution must remain false")
    require(manifest.get("lineage_full_check_completed") is False, "lineage full check must not be completed")
    require(manifest.get("raw_value_matching_performed") is False, "raw value matching must not be performed")
    require(manifest.get("raw_dir_read_performed_by_stage_review") is False, "stage review raw read must be false")
    require(
        manifest.get("raw_dir_read_performed_by_dependency_validators") is False,
        "dependency validators must not read raw inbox in this review",
    )
    require(manifest.get("raw_dir_mutation_performed") is False, "raw directory mutation must not be performed")
    require(manifest.get("phase_count") == 3, "phase_count must be 3")
    require(manifest.get("open_review_finding_count") == 0, "open review findings must be 0")
    require(manifest.get("fixed_review_finding_count") == 0, "fixed review findings must be 0")
    require(manifest.get("review_findings") == [], "review findings must be empty")
    require(manifest.get("next_required_step") == NEXT_REQUIRED_STEP, "next_required_step mismatch")

    phase_results = manifest.get("phase_results", {})
    require(phase_results == {"S06-P1": "PASS", "S06-P2": "PASS", "S06-P3": "PASS"}, "phase_results mismatch")
    require(manifest.get("s06_p1_dependency_validated") is True, "S06-P1 dependency flag mismatch")
    require(manifest.get("s06_p2_dependency_validated") is True, "S06-P2 dependency flag mismatch")
    require(manifest.get("s06_p3_dependency_validated") is True, "S06-P3 dependency flag mismatch")
    require(p1_result.get("phase_id") == "S06-P1", "S06-P1 validator did not return S06-P1")
    require(p2_result.get("phase_id") == "S06-P2", "S06-P2 validator did not return S06-P2")
    require(p3_result.get("phase_id") == "S06-P3", "S06-P3 validator did not return S06-P3")
    require(p1_result.get("stage6_review_performed") is False, "S06-P1 phase scope must not include review")
    require(p2_result.get("stage6_review_performed") is False, "S06-P2 phase scope must not include review")
    require(p3_result.get("stage6_review_performed") is False, "S06-P3 phase scope must not include review")
    require(p1_result.get("github_upload_performed") is False, "S06-P1 upload boundary mismatch")
    require(p2_result.get("github_upload_performed") is False, "S06-P2 upload boundary mismatch")
    require(p3_result.get("github_upload_performed") is False, "S06-P3 upload boundary mismatch")
    require(p1_result.get("raw_dir_read_performed") is False, "S06-P1 raw read boundary mismatch")
    require(p2_result.get("raw_dir_read_performed") is False, "S06-P2 raw read boundary mismatch")
    require(p3_result.get("raw_dir_read_performed") is False, "S06-P3 raw read boundary mismatch")
    require(p1_result.get("raw_dir_mutation_performed") is False, "S06-P1 raw mutation boundary mismatch")
    require(p2_result.get("raw_dir_mutation_performed") is False, "S06-P2 raw mutation boundary mismatch")
    require(p3_result.get("raw_dir_mutation_performed") is False, "S06-P3 raw mutation boundary mismatch")

    phase_summary = manifest.get("phase_summary", {})
    p1_summary = phase_summary.get("S06-P1", {})
    require(p1_summary.get("pass_fixture_field_comparison_count") == 8, "S06-P1 comparison count mismatch")
    require(p1_summary.get("zero_delta_passed_for_public_safe_fixture") is True, "S06-P1 zero-delta pass mismatch")
    require(p1_summary.get("pass_fixture_mismatch_count") == 0, "S06-P1 pass mismatch count mismatch")
    require(p1_summary.get("one_cent_mismatch_detected") is True, "S06-P1 one-cent mismatch mismatch")
    require(p1_summary.get("minimum_fail_difference_cents") == 1, "S06-P1 minimum fail cents mismatch")
    require(p1_summary.get("mismatch_fixture_mismatch_count") == 1, "S06-P1 mismatch fixture count mismatch")
    require(p1_summary.get("mismatch_report_generated") is True, "S06-P1 mismatch report mismatch")
    require(p1_summary.get("metadata_quality_written") is False, "S06-P1 must not write metadata quality")
    require(p1_summary.get("difference_queue_created") is False, "S06-P1 must not create queue")

    p2_summary = phase_summary.get("S06-P2", {})
    require(p2_summary.get("queue_item_count") == 1, "S06-P2 queue item count mismatch")
    require(p2_summary.get("pdf_excel_conflict_detected") is True, "S06-P2 conflict detection mismatch")
    require(p2_summary.get("difference_cents") == 1, "S06-P2 difference cents mismatch")
    require(p2_summary.get("auto_correction_allowed") is False, "S06-P2 auto correction must be false")
    require(p2_summary.get("averaging_allowed") is False, "S06-P2 averaging must be false")
    require(p2_summary.get("rounding_mask_allowed") is False, "S06-P2 rounding mask must be false")
    require(p2_summary.get("auto_selection_allowed") is False, "S06-P2 auto selection must be false")
    require(p2_summary.get("report_grade_a_allowed") is False, "S06-P2 report grade A must be false")
    require(p2_summary.get("maximum_report_grade") == "B", "S06-P2 maximum report grade mismatch")
    require(p2_summary.get("hard_block_reason") == "unresolved_critical_difference", "S06-P2 hard block mismatch")
    require(p2_summary.get("metadata_quality_written") is False, "S06-P2 must not write metadata quality")

    p3_summary = phase_summary.get("S06-P3", {})
    require(p3_summary.get("metadata_quality_written") is True, "S06-P3 metadata quality mismatch")
    require(p3_summary.get("metadata_zero_delta_records_written") == 1, "S06-P3 zero-delta record count mismatch")
    require(p3_summary.get("metadata_data_quality_records_written") == 2, "S06-P3 data-quality count mismatch")
    require(p3_summary.get("metadata_source_difference_records_written") == 1, "S06-P3 source difference count mismatch")
    require(p3_summary.get("metadata_mismatch_rows_written") == 1, "S06-P3 mismatch rows mismatch")
    require(p3_summary.get("project_status_count") == 2, "S06-P3 project status count mismatch")
    require(p3_summary.get("blocked_project_status_count") == 2, "S06-P3 blocked status count mismatch")
    require(p3_summary.get("q5_allowed_count") == 0, "S06-P3 Q5 allowed mismatch")
    require(p3_summary.get("report_grade_a_allowed_count") == 0, "S06-P3 report grade A count mismatch")

    gate = manifest.get("stage_gate", {})
    require(gate.get("current_data_quality_grade") == "Q4", "stage gate quality mismatch")
    require(gate.get("current_report_grade") == "D", "stage gate report grade mismatch")
    require(gate.get("release_permission") == "blocked", "stage gate release mismatch")
    require(manifest.get("current_data_quality_grade") == "Q4", "quality grade mismatch")
    require(manifest.get("current_report_grade") == "D", "report grade mismatch")
    require(manifest.get("release_permission") == "blocked", "release permission mismatch")

    hard_blocks = manifest.get("hard_blocks", [])
    require(isinstance(hard_blocks, list), "hard_blocks must be a list")
    for block in REQUIRED_HARD_BLOCKS:
        require(block in hard_blocks, f"missing hard block: {block}")
    require(manifest.get("hard_block_count") == len(REQUIRED_HARD_BLOCKS), "hard block count mismatch")

    raw_boundary = manifest.get("raw_data_boundary", {})
    require(raw_boundary.get("local_raw_data_dir") == RAW_DIR, "raw directory mismatch")
    require(
        raw_boundary.get("local_raw_data_dir_role") == "user_finance_raw_business_data_inbox",
        "raw directory role mismatch",
    )
    require(raw_boundary.get("codex_read_allowed_only_when_phase_requires") is True, "raw read policy mismatch")
    require(raw_boundary.get("codex_read_required_by_this_stage_review") is False, "review raw read required mismatch")
    require(raw_boundary.get("codex_read_performed_by_this_stage_review") is False, "review raw read performed mismatch")
    require(raw_boundary.get("codex_modify_allowed") is False, "raw modify must be false")
    require(raw_boundary.get("codex_delete_allowed") is False, "raw delete must be false")
    require(raw_boundary.get("codex_move_allowed") is False, "raw move must be false")
    require(raw_boundary.get("codex_rename_allowed") is False, "raw rename must be false")
    require(raw_boundary.get("codex_overwrite_allowed") is False, "raw overwrite must be false")
    require(raw_boundary.get("codex_generate_inside_allowed") is False, "raw generate-inside must be false")
    require(raw_boundary.get("codex_create_extra_files_inside_allowed") is False, "raw extra create must be false")
    require(raw_boundary.get("github_commit_allowed") is False, "raw GitHub commit must be false")
    require(
        raw_boundary.get("private_runtime_output_dir") == "KMFA/.codex_private_runtime/",
        "private runtime output dir mismatch",
    )

    safety = manifest.get("public_repo_safety", {})
    for key in PUBLIC_SAFETY_FALSE_KEYS:
        require(safety.get(key) is False, f"public_repo_safety.{key} must be false")

    reviewed_phase_manifests = manifest.get("reviewed_phase_manifests", {})
    for phase, path in PHASE_MANIFESTS.items():
        require(reviewed_phase_manifests.get(phase) == str(path), f"{phase} manifest ref mismatch")
        require(path.exists(), f"missing phase manifest: {path}")
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
        "review_scope": manifest["review_scope"],
        "phase_count": manifest["phase_count"],
        "phase_results": phase_results,
        "s06_p1_dependency_validated": manifest["s06_p1_dependency_validated"],
        "s06_p2_dependency_validated": manifest["s06_p2_dependency_validated"],
        "s06_p3_dependency_validated": manifest["s06_p3_dependency_validated"],
        "stage_review_performed": manifest["stage_review_performed"],
        "open_review_finding_count": manifest["open_review_finding_count"],
        "fixed_review_finding_count": manifest["fixed_review_finding_count"],
        "github_upload_ready_next_gate": manifest["github_upload_ready_next_gate"],
        "github_upload_deferred_until_stage10_batch": manifest["github_upload_deferred_until_stage10_batch"],
        "github_upload_performed": manifest["github_upload_performed"],
        "delivery_allowed": manifest["delivery_allowed"],
        "formal_report_allowed": manifest["formal_report_allowed"],
        "business_decision_basis_allowed": manifest["business_decision_basis_allowed"],
        "business_execution_allowed": manifest["business_execution_allowed"],
        "raw_value_matching_performed": manifest["raw_value_matching_performed"],
        "raw_dir_read_performed_by_stage_review": manifest["raw_dir_read_performed_by_stage_review"],
        "raw_dir_read_performed_by_dependency_validators": manifest[
            "raw_dir_read_performed_by_dependency_validators"
        ],
        "raw_dir_mutation_performed": manifest["raw_dir_mutation_performed"],
        "current_data_quality_grade": manifest["current_data_quality_grade"],
        "current_report_grade": manifest["current_report_grade"],
        "release_permission": manifest["release_permission"],
        "project_status_count": p3_summary["project_status_count"],
        "blocked_project_status_count": p3_summary["blocked_project_status_count"],
        "q5_allowed_count": p3_summary["q5_allowed_count"],
        "report_grade_a_allowed_count": p3_summary["report_grade_a_allowed_count"],
        "hard_blocks": hard_blocks,
        "next_required_step": manifest["next_required_step"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.3 Stage 6 review evidence.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args()
    try:
        result = validate_v013_s06_stage_review(args.manifest)
    except ValidationError as exc:
        print("FAIL: KMFA v0.1.3 Stage 6 review validation failed")
        print(exc)
        return 1
    print(
        "PASS: KMFA v0.1.3 Stage 6 review validated "
        f"(phases={result['phase_count']}, findings_open={result['open_review_finding_count']}, "
        f"project_statuses={result['project_status_count']}, q5_allowed={result['q5_allowed_count']}, "
        f"quality={result['current_data_quality_grade']}, report={result['current_report_grade']}, "
        f"release={result['release_permission']}, upload_ready={str(result['github_upload_ready_next_gate']).lower()}, "
        f"github_upload={str(result['github_upload_performed']).lower()})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
