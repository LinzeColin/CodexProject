#!/usr/bin/env python3
"""Validate KMFA v0.1.3 S08-P1 project composite key replay evidence."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from KMFA.tools.v013_s08_p1_project_composite_key_replay import (
    MANIFEST_PATH,
    NEXT_REQUIRED_STEP,
    PHASE_SCOPE,
    RAW_DIR,
    REPORT_PATH,
    SCHEMA_VERSION,
    TASK_ID,
    TEST_RESULTS_PATH,
    validate_legacy_s08_p1_artifacts,
    validate_stage7_dependency,
)


PUBLIC_SAFETY_FALSE_KEYS = (
    "protected_source_payload_committed",
    "zip_committed",
    "excel_workbook_committed",
    "wps_native_file_committed",
    "redcircle_native_file_committed",
    "csv_committed",
    "pdf_committed",
    "private_csv_committed",
    "sqlite_or_db_committed",
    "credentials_committed",
    "connector_secret_committed",
    "field_plaintext_committed",
    "source_header_plaintext_committed",
    "raw_file_names_committed",
    "raw_file_hashes_committed",
    "tab_labels_committed",
    "zip_member_names_committed",
    "source_record_payload_committed",
    "normalized_source_values_committed",
    "project_identity_plaintext_committed",
)
REQUIRED_HARD_BLOCKS = (
    "raw_data_mutation_forbidden",
    "raw_value_publication_forbidden",
    "field_header_plaintext_publication_forbidden",
    "project_identity_values_remain_hash_only",
    "manual_review_queue_auto_merge_forbidden",
    "q5_forbidden_until_downstream_stage8_and_quality_evidence",
    "formal_report_release_blocked",
    "lineage_full_check_not_performed",
    "raw_value_matching_not_performed",
    "github_upload_deferred_until_stage10_batch",
    "business_execution_blocked",
)
FORBIDDEN_EVIDENCE_TEXT = (
    "raw_value:",
    "normalized_value:",
    "source_header_text:",
    "original_filename",
    "member_sha256:",
    "actual_package_sha256",
    "authoritative_value_cents",
    "system_value_cents",
    "pdf_value_cents",
    "excel_value_cents",
    "sheet_name",
    "row_value",
    "cell_value",
    "business_data",
    "bank_statement",
    "contract_full_text",
    "salary_detail",
    "tax_filing",
    "connector_token",
    "connector_password",
    "api_key",
    "private_key",
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


def validate_v013_s08_p1_project_composite_key_replay(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    manifest = read_json(manifest_path)
    s07 = validate_stage7_dependency()
    legacy = validate_legacy_s08_p1_artifacts()

    require(manifest.get("schema_version") == SCHEMA_VERSION, "manifest schema mismatch")
    require(manifest.get("project_id") == "KMFA", "project_id mismatch")
    require(manifest.get("version") == "0.1.3", "version mismatch")
    require(manifest.get("stage_id") == "S08", "stage_id must be S08")
    require(manifest.get("phase_id") == "S08-P1", "phase_id must be S08-P1")
    require(manifest.get("task_id") == TASK_ID, "task_id mismatch")
    require(manifest.get("phase_scope") == PHASE_SCOPE, "phase scope mismatch")
    require(
        manifest.get("status")
        == "completed_validated_local_only_no_go_upload_deferred_project_composite_key_replayed",
        "status mismatch",
    )
    require(manifest.get("completed_task_ids") == ["S8PAT01", "S8PAT02", "S8PAT03"], "completed tasks mismatch")
    require(
        manifest.get("acceptance_ids") == ["ACC-V013-S08-P1-PROJECT-COMPOSITE-KEY-REPLAY"],
        "acceptance ids mismatch",
    )
    require(manifest.get("s07_stage_review_dependency_validated") is True, "Stage 7 dependency flag mismatch")
    require(s07.get("stage_id") == "S07", "Stage 7 dependency did not validate")
    require(manifest.get("legacy_s08_p1_dependency_validated") is True, "legacy S08-P1 dependency flag mismatch")

    progress = manifest.get("stage8_phase_progress", {})
    require(progress.get("completed_phase_count") == 1, "completed phase count mismatch")
    require(progress.get("total_phase_count") == 3, "total phase count mismatch")
    require(progress.get("derived_percent_bps") == 3333, "derived percent bps mismatch")
    require(progress.get("derived_percent_label") == "33.33%", "derived percent label mismatch")
    require(progress.get("s08_p1_performed") is True, "S08-P1 must be performed")
    require(progress.get("s08_p2_performed") is False, "S08-P2 must not be performed")
    require(progress.get("s08_p3_performed") is False, "S08-P3 must not be performed")
    require(progress.get("stage8_review_performed") is False, "Stage 8 review must not be performed")

    summary = manifest.get("legacy_s08_p1_summary", {})
    require(summary.get("required_component_count") == 8, "component count mismatch")
    require(summary.get("profile_count") == 4, "profile count mismatch")
    require(summary.get("match_result_count") == 3, "match result count mismatch")
    require(summary.get("manual_review_queue_count") == 2, "review queue count mismatch")
    require(summary.get("strong_auto_match_count") == 1, "strong auto match count mismatch")
    require(summary.get("human_review_required_count") == 2, "human review count mismatch")
    require(summary.get("hash_only_profile_count") == 4, "hash-only profile count mismatch")
    require(summary.get("component_private_ref_count") == 32, "component private ref count mismatch")
    require(summary.get("match_decision_counts", {}).get("strong_auto_match") == 1, "decision count mismatch")
    require(summary.get("match_decision_counts", {}).get("human_review_required") == 2, "decision count mismatch")
    for key in (
        "required_component_count",
        "profile_count",
        "match_result_count",
        "manual_review_queue_count",
        "strong_auto_match_count",
        "human_review_required_count",
        "hash_only_profile_count",
        "component_private_ref_count",
    ):
        require(summary.get(key) == legacy.get(key), f"legacy summary mismatch for {key}")

    policy = manifest.get("matching_policy", {})
    require(policy.get("matching_weights_sum_bps") == 10000, "matching weights must sum to 10000 bps")
    require(policy.get("strong_threshold_bps") == 8500, "strong threshold mismatch")
    require(policy.get("human_review_threshold_bps") == 7000, "human review threshold mismatch")
    require(policy.get("weak_candidate_threshold_bps") == 5000, "weak candidate threshold mismatch")
    require(policy.get("missing_single_component_blocks_all_matching") is False, "missing single component policy mismatch")
    require(policy.get("below_strong_threshold_enters_manual_review") is True, "manual review policy mismatch")
    require(policy.get("auto_merge_allowed_for_review_queue_count") == 0, "review queue auto merge mismatch")
    require(policy.get("blocked_by_missing_single_field_count") == 0, "missing field total block mismatch")
    require(policy.get("below_strong_threshold_manual_review_count") == 2, "below strong review count mismatch")

    phase_boundaries = manifest.get("phase_boundaries", {})
    for key in (
        "s08_p2_entity_model_scope_included",
        "s08_p3_matching_quality_scope_included",
        "stage8_review_scope_included",
        "fact_layer_scope_included",
        "lineage_full_check_scope_included",
        "report_scope_included",
        "ui_scope_included",
        "external_connector_scope_included",
        "github_upload_scope_included",
    ):
        require(phase_boundaries.get(key) is False, f"phase_boundaries.{key} must be false")
    require(phase_boundaries.get("s08_p1_scope_included") is True, "S08-P1 scope flag mismatch")

    quality = manifest.get("quality_gate", {})
    require(quality.get("current_data_quality_grade") == "Q4", "quality grade mismatch")
    require(quality.get("current_report_grade") == "D", "report grade mismatch")
    require(quality.get("release_permission") == "blocked", "release permission mismatch")
    for key in (
        "q5_calculation_baseline_allowed",
        "formal_report_allowed",
        "business_decision_basis_allowed",
        "business_execution_allowed",
        "delivery_allowed",
    ):
        require(quality.get(key) is False, f"quality_gate.{key} must be false")
    require(quality.get("q5_calculation_baseline_allowed_count") == 0, "Q5 allowed count mismatch")
    require(quality.get("formal_report_allowed_count") == 0, "formal report allowed count mismatch")

    upload = manifest.get("github_upload", {})
    require(upload.get("github_upload_ready_next_gate") is False, "upload ready must stay false")
    require(upload.get("github_upload_deferred_until_stage10_batch") is True, "upload must be deferred")
    require(upload.get("github_upload_performed") is False, "upload performed must be false")
    require(
        upload.get("github_upload_status") == "not_uploaded_deferred_until_stage10_batch",
        "upload status mismatch",
    )

    raw_boundary = manifest.get("raw_data_boundary", {})
    require(raw_boundary.get("local_raw_data_dir") == RAW_DIR, "raw directory mismatch")
    require(
        raw_boundary.get("local_raw_data_dir_role") == "user_finance_raw_private_inbox",
        "raw directory role mismatch",
    )
    require(raw_boundary.get("codex_read_allowed_only_when_phase_requires") is True, "raw read policy mismatch")
    for key in (
        "codex_read_required_by_this_phase",
        "codex_read_performed_by_this_phase",
        "codex_list_performed_by_this_phase",
        "codex_modify_allowed",
        "codex_delete_allowed",
        "codex_move_allowed",
        "codex_rename_allowed",
        "codex_overwrite_allowed",
        "codex_generate_inside_allowed",
        "codex_create_extra_files_inside_allowed",
        "github_commit_allowed",
    ):
        require(raw_boundary.get(key) is False, f"raw_data_boundary.{key} must be false")
    require(
        raw_boundary.get("private_runtime_output_dir") == "KMFA/.codex_private_runtime/",
        "private runtime output dir mismatch",
    )

    safety = manifest.get("public_repo_safety", {})
    for key in PUBLIC_SAFETY_FALSE_KEYS:
        require(safety.get(key) is False, f"public_repo_safety.{key} must be false")

    hard_blocks = manifest.get("hard_blocks", [])
    require(isinstance(hard_blocks, list), "hard_blocks must be a list")
    for block in REQUIRED_HARD_BLOCKS:
        require(block in hard_blocks, f"missing hard block: {block}")
    require(manifest.get("hard_block_count") == len(REQUIRED_HARD_BLOCKS), "hard block count mismatch")
    require(manifest.get("next_required_step") == NEXT_REQUIRED_STEP, "next_required_step mismatch")

    artifact_refs = manifest.get("artifact_refs", {})
    for key in (
        "legacy_manifest",
        "legacy_profiles",
        "legacy_match_results",
        "legacy_manual_review_queue",
        "legacy_stage_manifest",
        "manifest",
        "report",
        "test_results",
        "generator",
        "validator",
        "unit_test",
    ):
        path = Path(artifact_refs.get(key, ""))
        require(path.exists(), f"missing artifact ref: {key} -> {path}")

    for ref in manifest.get("evidence_refs", []):
        require(Path(ref).exists(), f"missing evidence ref: {ref}")
    for evidence in (MANIFEST_PATH, REPORT_PATH, TEST_RESULTS_PATH):
        require(evidence.exists(), f"missing public evidence: {evidence}")
        if evidence.exists():
            text = evidence.read_text(encoding="utf-8")
            for forbidden in FORBIDDEN_EVIDENCE_TEXT:
                require(forbidden not in text, f"forbidden public evidence text {forbidden!r} in {evidence}")

    reviewed_head = str(manifest.get("reviewed_head", ""))
    require(
        len(reviewed_head) == 40 and all(character in "0123456789abcdef" for character in reviewed_head),
        "reviewed_head must be a lowercase 40-character git SHA",
    )
    require(manifest.get("branch") == git_output(["branch", "--show-current"]), "branch mismatch")
    require(manifest.get("remote") == git_output(["remote", "get-url", "origin"]), "remote mismatch")

    if errors:
        raise ValidationError("; ".join(errors))

    return {
        "project_id": manifest["project_id"],
        "version": manifest["version"],
        "stage_id": manifest["stage_id"],
        "phase_id": manifest["phase_id"],
        "phase_scope": manifest["phase_scope"],
        "status": manifest["status"],
        "required_component_count": summary["required_component_count"],
        "profile_count": summary["profile_count"],
        "match_result_count": summary["match_result_count"],
        "manual_review_queue_count": summary["manual_review_queue_count"],
        "strong_auto_match_count": summary["strong_auto_match_count"],
        "human_review_required_count": summary["human_review_required_count"],
        "matching_weights_sum_bps": policy["matching_weights_sum_bps"],
        "strong_threshold_bps": policy["strong_threshold_bps"],
        "human_review_threshold_bps": policy["human_review_threshold_bps"],
        "missing_single_component_blocks_all_matching": policy["missing_single_component_blocks_all_matching"],
        "below_strong_threshold_enters_manual_review": policy["below_strong_threshold_enters_manual_review"],
        "q5_calculation_baseline_allowed_count": quality["q5_calculation_baseline_allowed_count"],
        "formal_report_allowed_count": quality["formal_report_allowed_count"],
        "s08_p2_performed": progress["s08_p2_performed"],
        "s08_p3_performed": progress["s08_p3_performed"],
        "stage8_review_performed": progress["stage8_review_performed"],
        "github_upload_performed": upload["github_upload_performed"],
        "github_upload_deferred_until_stage10_batch": upload["github_upload_deferred_until_stage10_batch"],
        "raw_dir_read_performed": raw_boundary["codex_read_performed_by_this_phase"],
        "raw_dir_mutation_performed": raw_boundary["codex_modify_allowed"],
        "next_required_step": manifest["next_required_step"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.3 S08-P1 project composite key replay.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args(argv)

    result = validate_v013_s08_p1_project_composite_key_replay(args.manifest)
    print(
        "PASS: KMFA v0.1.3 S08-P1 project composite key replay validated "
        f"(components={result['required_component_count']}, profiles={result['profile_count']}, "
        f"matches={result['match_result_count']}, review_queue={result['manual_review_queue_count']}, "
        "s08p2=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
