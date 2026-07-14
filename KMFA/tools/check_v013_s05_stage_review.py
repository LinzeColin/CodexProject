#!/usr/bin/env python3
"""Validate KMFA v0.1.3 Stage 5 review evidence."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from KMFA.tools.check_v013_s05_p1_a0_file_registration import validate_v013_s05_p1_a0_file_registration
from KMFA.tools.check_v013_s05_p2_field_candidate_replay import validate_v013_s05_p2_field_candidate_replay
from KMFA.tools.check_v013_s05_p3_authority_baseline_replay import validate_v013_s05_p3_authority_baseline_replay
from KMFA.tools.v013_s05_stage_review import (
    MANIFEST_PATH,
    NEXT_REQUIRED_STEP,
    REPORT_PATH,
    REVIEW_SCOPE,
    SCHEMA_VERSION,
    TASK_ID,
    TEST_RESULTS_PATH,
)


PHASE_MANIFESTS = {
    "S05-P1": Path(
        "KMFA/stage_artifacts/V013_S05_P1_A0_FILE_REGISTRATION/machine/a0_file_registration_replay_manifest.json"
    ),
    "S05-P2": Path(
        "KMFA/stage_artifacts/V013_S05_P2_FIELD_CANDIDATE_REPLAY/machine/field_candidate_replay_manifest.json"
    ),
    "S05-P3": Path(
        "KMFA/stage_artifacts/V013_S05_P3_AUTHORITY_BASELINE_REPLAY/machine/authority_baseline_replay_manifest.json"
    ),
}
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
    "authority_baseline_raw_values_committed",
    "stage_review_raw_rows_committed",
)
REQUIRED_HARD_BLOCKS = (
    "raw_data_mutation_forbidden",
    "raw_value_publication_forbidden",
    "field_header_plaintext_publication_forbidden",
    "a0_private_source_package_mismatch_not_backfilled",
    "excel_candidate_excluded_as_cross_source_support_only",
    "lineage_full_check_not_performed",
    "formal_report_release_blocked",
    "github_upload_deferred_until_stage10_batch",
    "business_execution_blocked",
)
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


def validate_v013_s05_stage_review(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    manifest = read_json(manifest_path)
    p1_result = validate_v013_s05_p1_a0_file_registration()
    p2_result = validate_v013_s05_p2_field_candidate_replay()
    p3_result = validate_v013_s05_p3_authority_baseline_replay()

    require(manifest.get("schema_version") == SCHEMA_VERSION, "manifest schema mismatch")
    require(manifest.get("project_id") == "KMFA", "project_id mismatch")
    require(manifest.get("version") == "0.1.3", "version mismatch")
    require(manifest.get("stage_id") == "S05", "stage_id must be S05")
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
    require(manifest.get("legacy_stage5_upload_artifacts_current_gate") is False, "legacy upload must not be current gate")
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
    require(manifest.get("s05_p1_prior_raw_read_recorded") is True, "S05-P1 prior read record must remain true")
    require(manifest.get("s05_p1_prior_raw_read_required") is True, "S05-P1 prior read-required record must remain true")
    require(manifest.get("raw_dir_mutation_performed") is False, "raw directory mutation must not be performed")
    require(manifest.get("phase_count") == 3, "phase_count must be 3")
    require(manifest.get("open_review_finding_count") == 0, "open review findings must be 0")
    require(manifest.get("fixed_review_finding_count") == 0, "fixed review findings must be 0")
    require(manifest.get("review_findings") == [], "review findings must be empty")
    require(manifest.get("next_required_step") == NEXT_REQUIRED_STEP, "next_required_step mismatch")

    phase_results = manifest.get("phase_results", {})
    require(phase_results == {"S05-P1": "PASS", "S05-P2": "PASS", "S05-P3": "PASS"}, "phase_results mismatch")
    require(manifest.get("s05_p1_dependency_validated") is True, "S05-P1 dependency flag mismatch")
    require(manifest.get("s05_p2_dependency_validated") is True, "S05-P2 dependency flag mismatch")
    require(manifest.get("s05_p3_dependency_validated") is True, "S05-P3 dependency flag mismatch")
    require(p1_result.get("phase_id") == "S05-P1", "S05-P1 validator did not return S05-P1")
    require(p2_result.get("phase_id") == "S05-P2", "S05-P2 validator did not return S05-P2")
    require(p3_result.get("phase_id") == "S05-P3", "S05-P3 validator did not return S05-P3")
    require(p1_result.get("github_upload_performed") is False, "S05-P1 upload boundary mismatch")
    require(p2_result.get("github_upload_performed") is False, "S05-P2 upload boundary mismatch")
    require(p3_result.get("github_upload_performed") is False, "S05-P3 upload boundary mismatch")
    require(p1_result.get("raw_dir_mutation_performed") is False, "S05-P1 raw mutation boundary mismatch")
    require(p2_result.get("raw_dir_read_performed") is False, "S05-P2 raw read boundary mismatch")
    require(p2_result.get("raw_dir_mutation_performed") is False, "S05-P2 raw mutation boundary mismatch")
    require(p3_result.get("raw_dir_read_performed") is False, "S05-P3 raw read boundary mismatch")
    require(p3_result.get("raw_dir_mutation_performed") is False, "S05-P3 raw mutation boundary mismatch")

    phase_summary = manifest.get("phase_summary", {})
    p1_summary = phase_summary.get("S05-P1", {})
    require(p1_summary.get("a0_file_count") == 9, "S05-P1 file count mismatch")
    require(p1_summary.get("a0_pdf_file_count") == 8, "S05-P1 PDF count mismatch")
    require(p1_summary.get("a0_excel_file_count") == 1, "S05-P1 Excel count mismatch")
    require(p1_summary.get("a0_candidate_count") == 9, "S05-P1 candidate count mismatch")
    require(p1_summary.get("q4_human_locked_count") == 0, "S05-P1 Q4 count mismatch")
    require(p1_summary.get("q5_formal_report_allowed_count") == 0, "S05-P1 Q5 count mismatch")
    require(p1_summary.get("member_sha256_recorded_count") == 0, "S05-P1 member SHA256 recorded mismatch")
    require(p1_summary.get("member_sha256_pending_count") == 9, "S05-P1 member SHA256 pending mismatch")
    require(p1_summary.get("local_raw_zip_openable") is True, "S05-P1 local raw zip openable mismatch")
    require(
        p1_summary.get("local_raw_package_hash_matches_registered") is False,
        "S05-P1 package hash must remain mismatched",
    )
    require(
        p1_summary.get("local_raw_package_size_matches_registered") is False,
        "S05-P1 package size must remain mismatched",
    )
    require(p1_summary.get("member_sha256_public_backfill_performed") is False, "S05-P1 backfill must be false")
    require(p1_summary.get("raw_dir_mutation_performed") is False, "S05-P1 raw mutation summary mismatch")

    p2_summary = phase_summary.get("S05-P2", {})
    require(p2_summary.get("fixture_candidate_count") == 45, "S05-P2 fixture count mismatch")
    require(p2_summary.get("required_fields_per_candidate") == 5, "S05-P2 fields-per-candidate mismatch")
    require(p2_summary.get("private_value_hash_recorded_count") == 40, "S05-P2 hash recorded mismatch")
    require(p2_summary.get("private_value_pending_count") == 5, "S05-P2 pending count mismatch")
    require(p2_summary.get("source_anchor_recorded_count") == 40, "S05-P2 source anchor recorded mismatch")
    require(p2_summary.get("source_anchor_pending_count") == 5, "S05-P2 source anchor pending mismatch")
    require(
        p2_summary.get("active_decision_code") == "downgrade_to_cross_source_support",
        "S05-P2 owner decision mismatch",
    )
    require(p2_summary.get("completion_gate_ready") is True, "S05-P2 completion gate mismatch")
    require(
        p2_summary.get("completion_gate_mode") == "owner_downgrade_to_cross_source_support",
        "S05-P2 completion gate mode mismatch",
    )
    require(p2_summary.get("q4_human_confirmed_count") == 0, "S05-P2 Q4 count mismatch")
    require(p2_summary.get("q5_calculation_baseline_allowed_count") == 0, "S05-P2 Q5 count mismatch")
    require(p2_summary.get("raw_dir_read_performed") is False, "S05-P2 raw read summary mismatch")
    require(p2_summary.get("raw_dir_mutation_performed") is False, "S05-P2 raw mutation summary mismatch")

    p3_summary = phase_summary.get("S05-P3", {})
    require(
        p3_summary.get("baseline_version") == "KMFA-A0-Q5-20260630-S05P3-PUBLIC-SAFE-HASH-LOCK",
        "S05-P3 baseline version mismatch",
    )
    require(
        p3_summary.get("baseline_content_hash")
        == "sha256:dbb55ffb4e3608e49dbcf91e97fc0f19395a8269ff7c8f4d5c3f8ca398c03670",
        "S05-P3 baseline content hash mismatch",
    )
    require(p3_summary.get("authority_records") == 45, "S05-P3 authority record mismatch")
    require(p3_summary.get("q5_locked_field_count") == 40, "S05-P3 q5 locked count mismatch")
    require(p3_summary.get("excluded_field_count") == 5, "S05-P3 excluded count mismatch")
    require(p3_summary.get("formal_report_allowed") is False, "S05-P3 formal report boundary mismatch")
    require(p3_summary.get("raw_dir_read_performed") is False, "S05-P3 raw read summary mismatch")
    require(p3_summary.get("raw_dir_mutation_performed") is False, "S05-P3 raw mutation summary mismatch")

    gate = manifest.get("stage_gate", {})
    require(gate.get("current_data_quality_grade") == "Q2", "stage gate quality mismatch")
    require(gate.get("current_report_grade") == "D", "stage gate report grade mismatch")
    require(gate.get("release_permission") == "blocked", "stage gate release mismatch")
    require(manifest.get("current_data_quality_grade") == "Q2", "quality grade mismatch")
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
        "s05_p1_dependency_validated": manifest["s05_p1_dependency_validated"],
        "s05_p2_dependency_validated": manifest["s05_p2_dependency_validated"],
        "s05_p3_dependency_validated": manifest["s05_p3_dependency_validated"],
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
        "s05_p1_prior_raw_read_recorded": manifest["s05_p1_prior_raw_read_recorded"],
        "raw_dir_mutation_performed": manifest["raw_dir_mutation_performed"],
        "current_data_quality_grade": manifest["current_data_quality_grade"],
        "current_report_grade": manifest["current_report_grade"],
        "release_permission": manifest["release_permission"],
        "q5_locked_field_count": p3_summary["q5_locked_field_count"],
        "excluded_field_count": p3_summary["excluded_field_count"],
        "hard_blocks": hard_blocks,
        "next_required_step": manifest["next_required_step"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.3 Stage 5 review evidence.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args()
    try:
        result = validate_v013_s05_stage_review(args.manifest)
    except ValidationError as exc:
        print("FAIL: KMFA v0.1.3 Stage 5 review validation failed")
        print(exc)
        return 1
    print(
        "PASS: KMFA v0.1.3 Stage 5 review validated "
        f"(phases={result['phase_count']}, findings_open={result['open_review_finding_count']}, "
        f"q5_locked={result['q5_locked_field_count']}, excluded={result['excluded_field_count']}, "
        f"quality={result['current_data_quality_grade']}, report={result['current_report_grade']}, "
        f"release={result['release_permission']}, upload_ready={str(result['github_upload_ready_next_gate']).lower()}, "
        f"github_upload={str(result['github_upload_performed']).lower()})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
