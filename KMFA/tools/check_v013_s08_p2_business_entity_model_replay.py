#!/usr/bin/env python3
"""Validate KMFA v0.1.3 S08-P2 business entity model replay evidence."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from KMFA.tools.v013_s08_p2_business_entity_model_replay import (
    MANIFEST_PATH,
    NEXT_REQUIRED_STEP,
    PHASE_SCOPE,
    RAW_DIR,
    REPORT_PATH,
    SCHEMA_VERSION,
    TASK_ID,
    TEST_RESULTS_PATH,
    validate_legacy_s08_p2_artifacts,
    validate_s08_p1_dependency,
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
    "business_entity_plaintext_committed",
    "business_relationship_values_committed",
    "business_lifecycle_values_committed",
)
REQUIRED_HARD_BLOCKS = (
    "raw_data_mutation_forbidden",
    "raw_value_publication_forbidden",
    "field_header_plaintext_publication_forbidden",
    "business_entity_values_remain_hash_ref_only",
    "business_entity_relationships_remain_schema_only",
    "business_entity_lifecycle_values_remain_status_only",
    "s08_p3_matching_quality_not_performed",
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


def validate_v013_s08_p2_business_entity_model_replay(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    manifest = read_json(manifest_path)
    s08_p1 = validate_s08_p1_dependency()
    legacy = validate_legacy_s08_p2_artifacts()

    require(manifest.get("schema_version") == SCHEMA_VERSION, "manifest schema mismatch")
    require(manifest.get("project_id") == "KMFA", "project_id mismatch")
    require(manifest.get("version") == "0.1.3", "version mismatch")
    require(manifest.get("stage_id") == "S08", "stage_id must be S08")
    require(manifest.get("phase_id") == "S08-P2", "phase_id must be S08-P2")
    require(manifest.get("task_id") == TASK_ID, "task_id mismatch")
    require(manifest.get("phase_scope") == PHASE_SCOPE, "phase scope mismatch")
    require(
        manifest.get("status")
        == "completed_validated_local_only_no_go_upload_deferred_business_entity_model_replayed",
        "status mismatch",
    )
    require(manifest.get("completed_task_ids") == ["S8PBT01", "S8PBT02", "S8PBT03"], "completed tasks mismatch")
    require(
        manifest.get("acceptance_ids") == ["ACC-V013-S08-P2-BUSINESS-ENTITY-MODEL-REPLAY"],
        "acceptance ids mismatch",
    )
    require(manifest.get("s08_p1_dependency_validated") is True, "S08-P1 dependency flag mismatch")
    require(s08_p1.get("phase_id") == "S08-P1", "S08-P1 dependency did not validate")
    require(manifest.get("legacy_s08_p2_dependency_validated") is True, "legacy S08-P2 dependency flag mismatch")

    progress = manifest.get("stage8_phase_progress", {})
    require(progress.get("completed_phase_count") == 2, "completed phase count mismatch")
    require(progress.get("total_phase_count") == 3, "total phase count mismatch")
    require(progress.get("derived_percent_bps") == 6667, "derived percent bps mismatch")
    require(progress.get("derived_percent_label") == "66.67%", "derived percent label mismatch")
    require(progress.get("s08_p1_performed") is True, "S08-P1 must be performed")
    require(progress.get("s08_p2_performed") is True, "S08-P2 must be performed")
    require(progress.get("s08_p3_performed") is False, "S08-P3 must not be performed")
    require(progress.get("stage8_review_performed") is False, "Stage 8 review must not be performed")

    summary = manifest.get("legacy_s08_p2_summary", {})
    require(summary.get("required_entity_type_count") == 8, "entity type count mismatch")
    require(summary.get("required_entity_types") == legacy["required_entity_types"], "entity types mismatch")
    require(summary.get("relationship_count") == 14, "relationship count mismatch")
    require(summary.get("lifecycle_status_count") == 32, "lifecycle status count mismatch")
    require(summary.get("lifecycle_status_per_entity_count") == 4, "lifecycle status per entity mismatch")
    require(summary.get("schema_entity_definition_count") == 8, "schema entity definition count mismatch")
    require(summary.get("relationship_graph_required_links_present") is True, "relationship graph incomplete")
    for entity_type in legacy["required_entity_types"]:
        require(
            summary.get("lifecycle_counts_by_entity", {}).get(entity_type) == 4,
            f"lifecycle count mismatch for {entity_type}",
        )
    for key in (
        "required_entity_type_count",
        "relationship_count",
        "lifecycle_status_count",
        "lifecycle_status_per_entity_count",
        "schema_entity_definition_count",
        "relationship_graph_required_link_count",
    ):
        require(summary.get(key) == legacy.get(key), f"legacy summary mismatch for {key}")

    policy = manifest.get("entity_model_policy", {})
    require(policy.get("private_ref_required") is True, "private ref policy mismatch")
    require(policy.get("entity_values_hash_ref_only") is True, "entity hash/ref policy mismatch")
    require(policy.get("relationship_values_schema_only") is True, "relationship schema-only policy mismatch")
    require(policy.get("lifecycle_values_status_only") is True, "lifecycle status-only policy mismatch")
    require(policy.get("relationship_graph_required_links_present") is True, "relationship graph policy mismatch")
    require(policy.get("quality_gate_false_count") == legacy["quality_gate_false_count"], "quality false count mismatch")
    require(
        policy.get("public_safety_false_count") == legacy["public_safety_false_count"],
        "public safety false count mismatch",
    )

    phase_boundaries = manifest.get("phase_boundaries", {})
    require(phase_boundaries.get("s08_p1_dependency_validated") is True, "S08-P1 dependency boundary mismatch")
    require(phase_boundaries.get("s08_p2_scope_included") is True, "S08-P2 scope flag mismatch")
    for key in (
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
        "raw_layer_write_allowed",
        "automatic_external_action_allowed",
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
        "legacy_schema",
        "legacy_relationships",
        "legacy_lifecycle_statuses",
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
        "s08_p1_dependency_validated": manifest["s08_p1_dependency_validated"],
        "legacy_s08_p2_dependency_validated": manifest["legacy_s08_p2_dependency_validated"],
        "required_entity_type_count": summary["required_entity_type_count"],
        "required_entity_types": summary["required_entity_types"],
        "relationship_count": summary["relationship_count"],
        "lifecycle_status_count": summary["lifecycle_status_count"],
        "lifecycle_status_per_entity_count": summary["lifecycle_status_per_entity_count"],
        "relationship_graph_required_links_present": summary["relationship_graph_required_links_present"],
        "q5_calculation_baseline_allowed_count": quality["q5_calculation_baseline_allowed_count"],
        "formal_report_allowed_count": quality["formal_report_allowed_count"],
        "s08_p1_performed": progress["s08_p1_performed"],
        "s08_p2_performed": progress["s08_p2_performed"],
        "s08_p3_performed": progress["s08_p3_performed"],
        "stage8_review_performed": progress["stage8_review_performed"],
        "fact_layer_scope_included": phase_boundaries["fact_layer_scope_included"],
        "lineage_full_check_scope_included": phase_boundaries["lineage_full_check_scope_included"],
        "report_scope_included": phase_boundaries["report_scope_included"],
        "ui_scope_included": phase_boundaries["ui_scope_included"],
        "external_connector_scope_included": phase_boundaries["external_connector_scope_included"],
        "github_upload_performed": upload["github_upload_performed"],
        "github_upload_deferred_until_stage10_batch": upload["github_upload_deferred_until_stage10_batch"],
        "raw_dir_read_performed": raw_boundary["codex_read_performed_by_this_phase"],
        "raw_dir_mutation_performed": raw_boundary["codex_modify_allowed"],
        "next_required_step": manifest["next_required_step"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.3 S08-P2 business entity model replay.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args(argv)

    result = validate_v013_s08_p2_business_entity_model_replay(args.manifest)
    print(
        "PASS: KMFA v0.1.3 S08-P2 business entity model replay validated "
        f"(entities={result['required_entity_type_count']}, relationships={result['relationship_count']}, "
        f"lifecycle_statuses={result['lifecycle_status_count']}, s08p3=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
