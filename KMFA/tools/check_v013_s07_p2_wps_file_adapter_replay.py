#!/usr/bin/env python3
"""Validate KMFA v0.1.3 S07-P2 WPS file adapter replay evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from KMFA.tools.v013_s05_p1_a0_file_registration import RAW_DIR
from KMFA.tools.v013_s07_p2_wps_file_adapter_replay import (
    ACTIVE_MAPPING_RULE_VERSION,
    MANIFEST_PATH,
    NEXT_REQUIRED_STEP,
    PHASE_SCOPE,
    REPORT_PATH,
    REQUIRED_WPS_EXPORT_TYPES,
    SCHEMA_VERSION,
    TASK_ID,
    TEST_RESULTS_PATH,
    validate_legacy_s07_p2,
)


BOOLEAN_FALSE_KEYS = (
    "raw_dir_read_required",
    "raw_dir_read_performed",
    "raw_dir_mutation_performed",
    "raw_layer_write_allowed",
    "raw_source_mutation_allowed",
    "raw_value_matching_performed",
    "business_field_parsing_performed",
    "source_header_plaintext_publication_allowed",
    "field_plaintext_publication_allowed",
    "raw_filename_publication_allowed",
    "raw_file_hash_publication_allowed",
    "tab_label_publication_allowed",
    "zip_member_name_publication_allowed",
    "record_value_publication_allowed",
    "business_value_publication_allowed",
    "s07_p1_performed",
    "s07_p3_performed",
    "stage7_review_performed",
    "github_upload_performed",
    "delivery_allowed",
    "formal_report_allowed",
    "business_decision_basis_allowed",
    "business_execution_allowed",
)
PUBLIC_SAFETY_FALSE_KEYS = (
    "protected_finance_inputs_committed",
    "zip_committed",
    "excel_workbook_committed",
    "wps_native_file_committed",
    "csv_committed",
    "pdf_committed",
    "private_csv_committed",
    "sqlite_or_db_committed",
    "credentials_committed",
    "field_plaintext_committed",
    "source_header_plaintext_committed",
    "raw_file_names_committed",
    "raw_file_hashes_committed",
    "tab_labels_committed",
    "zip_member_names_committed",
    "protected_finance_values_committed",
    "normalized_protected_values_committed",
)
FORBIDDEN_EVIDENCE_TEXT = (
    "raw_value:",
    "normalized_value:",
    "source_header_text:",
    "original_filename",
    "member_sha256:",
    "actual_package_sha256",
    "bank_statement",
    "contract_full_text",
    "salary_detail",
    "tax_filing",
    "sheet_name",
    "row_value",
    "business_data",
    "authoritative_value_cents",
    "system_value_cents",
    "pdf_value_cents",
    "excel_value_cents",
    "S07P2_",
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


def validate_v013_s07_p2_wps_file_adapter_replay(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    manifest = read_json(manifest_path)
    legacy = validate_legacy_s07_p2()
    summary = manifest.get("wps_adapter_summary", {})

    require(manifest.get("schema_version") == SCHEMA_VERSION, "manifest schema mismatch")
    require(manifest.get("project_id") == "KMFA", "project_id mismatch")
    require(manifest.get("version") == "0.1.3", "version mismatch")
    require(manifest.get("stage_id") == "S07", "stage_id must be S07")
    require(manifest.get("phase_id") == "S07-P2", "phase_id must be S07-P2")
    require(manifest.get("phase_scope") == PHASE_SCOPE, "phase scope mismatch")
    require(manifest.get("task_id") == TASK_ID, "task_id mismatch")
    require(
        manifest.get("status") == "completed_validated_local_only_no_go_upload_deferred_wps_file_adapter_replayed",
        "status mismatch",
    )
    require(manifest.get("completed_task_ids") == ["S7PBT01", "S7PBT02", "S7PBT03"], "task ids mismatch")
    require(
        manifest.get("acceptance_ids") == ["ACC-V013-S07-P2-WPS-FILE-ADAPTER-REPLAY"],
        "acceptance ids mismatch",
    )
    require(manifest.get("next_required_step") == NEXT_REQUIRED_STEP, "next_required_step mismatch")
    require(manifest.get("s06_stage_review_dependency_validated") is True, "S06 dependency flag must be true")
    require(manifest.get("s07_p1_dependency_validated") is True, "S07-P1 dependency flag must be true")
    require(manifest.get("legacy_s07_p2_dependency_validated") is True, "legacy S07-P2 dependency flag must be true")

    expected_summary = {
        "source_export_type_count": 4,
        "source_registry_count": 4,
        "field_mapping_count": 20,
        "hash_only_field_mapping_count": 20,
        "field_report_count": 4,
        "conversion_guidance_count": 4,
        "mapping_rule_version_count": 1,
        "source_header_hash_count": 20,
        "field_report_readonly_count": 4,
        "field_report_raw_layer_write_allowed_count": 0,
        "native_conversion_required_count": 4,
        "q4_human_confirmed_count": 0,
        "q5_calculation_baseline_allowed_count": 0,
        "formal_report_allowed_count": 0,
        "quality_counts": {"Q2_structure_candidate": 20},
        "converted_format_counts": {"xlsx": 4},
        "active_mapping_rule_version": ACTIVE_MAPPING_RULE_VERSION,
    }
    require(set(summary.get("wps_export_types", [])) == set(REQUIRED_WPS_EXPORT_TYPES), "WPS export type set mismatch")
    for key, expected in expected_summary.items():
        require(summary.get(key) == expected, f"WPS adapter summary {key} mismatch")
        require(legacy.get(key) == expected, f"legacy WPS adapter summary {key} mismatch")

    stage_scope = manifest.get("stage_scope", {})
    require(stage_scope.get("wps_file_adapter_replay") is True, "WPS replay scope must be true")
    require(stage_scope.get("wps_file_adapter") is True, "WPS adapter scope must be true")
    for key in (
        "finance_scope_included",
        "redcircle_scope_included",
        "stage7_review_included",
        "external_connector_included",
        "facts_layer_write_included",
        "lineage_full_check_included",
        "formal_report_generation_included",
        "github_upload_included",
    ):
        require(stage_scope.get(key) is False, f"stage_scope.{key} must be false")

    quality_gate = manifest.get("quality_gate", {})
    require(quality_gate.get("candidate_quality_grade") == "Q2_structure_candidate", "candidate quality mismatch")
    require(quality_gate.get("requires_stage7_review_before_downstream_use") is True, "Stage 7 review gate mismatch")
    require(quality_gate.get("current_data_quality_grade") == "Q4", "current data quality mismatch")
    require(quality_gate.get("current_report_grade") == "D", "current report grade mismatch")
    require(quality_gate.get("release_permission") == "blocked", "release permission mismatch")
    require(quality_gate.get("formal_report_allowed") is False, "formal report allowed must be false")

    raw_boundary = manifest.get("raw_data_boundary", {})
    require(raw_boundary.get("local_raw_data_dir") == str(RAW_DIR), "raw directory mismatch")
    require(raw_boundary.get("local_raw_data_dir_role") == "protected_finance_input_inbox", "raw role mismatch")
    require(raw_boundary.get("codex_read_required_by_this_phase") is False, "raw read required must be false")
    require(raw_boundary.get("codex_read_performed_by_this_phase") is False, "raw read performed must be false")
    require(raw_boundary.get("codex_modify_allowed") is False, "raw modify must be false")
    require(raw_boundary.get("codex_delete_allowed") is False, "raw delete must be false")
    require(raw_boundary.get("codex_move_allowed") is False, "raw move must be false")
    require(raw_boundary.get("codex_rename_allowed") is False, "raw rename must be false")
    require(raw_boundary.get("codex_overwrite_allowed") is False, "raw overwrite must be false")
    require(raw_boundary.get("codex_generate_inside_allowed") is False, "raw generate-inside must be false")
    require(raw_boundary.get("codex_create_extra_files_inside_allowed") is False, "raw extra-file creation must be false")
    require(raw_boundary.get("github_commit_allowed") is False, "raw GitHub commit must be false")

    for key in BOOLEAN_FALSE_KEYS:
        require(manifest.get(key) is False, f"{key} must be false")
    require(manifest.get("s07_p2_performed") is True, "S07-P2 performed flag must be true")
    require(manifest.get("github_upload_status") == "not_uploaded_deferred_until_stage10_batch", "upload status mismatch")
    require(manifest.get("github_upload_deferred_until_stage10_batch") is True, "upload deferral flag must be true")
    require(manifest.get("current_data_quality_grade") == "Q4", "manifest quality mismatch")
    require(manifest.get("current_report_grade") == "D", "manifest report grade mismatch")
    require(manifest.get("release_permission") == "blocked", "manifest release permission mismatch")

    safety = manifest.get("public_repo_safety", {})
    for key in PUBLIC_SAFETY_FALSE_KEYS:
        require(safety.get(key) is False, f"public_repo_safety.{key} must be false")

    for ref in manifest.get("legacy_s07_p2_refs", []):
        require(Path(ref).exists(), f"missing legacy S07-P2 ref: {ref}")
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

    if errors:
        raise ValidationError("; ".join(errors))

    return {
        "project_id": manifest["project_id"],
        "version": manifest["version"],
        "stage_id": manifest["stage_id"],
        "phase_id": manifest["phase_id"],
        "phase_scope": manifest["phase_scope"],
        "status": manifest["status"],
        "s06_stage_review_dependency_validated": manifest["s06_stage_review_dependency_validated"],
        "s07_p1_dependency_validated": manifest["s07_p1_dependency_validated"],
        "legacy_s07_p2_dependency_validated": manifest["legacy_s07_p2_dependency_validated"],
        "source_export_type_count": summary["source_export_type_count"],
        "field_mapping_count": summary["field_mapping_count"],
        "hash_only_field_mapping_count": summary["hash_only_field_mapping_count"],
        "field_report_count": summary["field_report_count"],
        "conversion_guidance_count": summary["conversion_guidance_count"],
        "mapping_rule_version_count": summary["mapping_rule_version_count"],
        "source_header_hash_count": summary["source_header_hash_count"],
        "native_conversion_required_count": summary["native_conversion_required_count"],
        "active_mapping_rule_version": summary["active_mapping_rule_version"],
        "q4_human_confirmed_count": summary["q4_human_confirmed_count"],
        "q5_calculation_baseline_allowed_count": summary["q5_calculation_baseline_allowed_count"],
        "formal_report_allowed_count": summary["formal_report_allowed_count"],
        "raw_dir_read_performed": manifest["raw_dir_read_performed"],
        "raw_dir_mutation_performed": manifest["raw_dir_mutation_performed"],
        "s07_p1_performed": manifest["s07_p1_performed"],
        "s07_p2_performed": manifest["s07_p2_performed"],
        "s07_p3_performed": manifest["s07_p3_performed"],
        "stage7_review_performed": manifest["stage7_review_performed"],
        "github_upload_performed": manifest["github_upload_performed"],
        "github_upload_deferred_until_stage10_batch": manifest["github_upload_deferred_until_stage10_batch"],
        "delivery_allowed": manifest["delivery_allowed"],
        "formal_report_allowed": manifest["formal_report_allowed"],
        "current_data_quality_grade": manifest["current_data_quality_grade"],
        "current_report_grade": manifest["current_report_grade"],
        "release_permission": manifest["release_permission"],
        "next_required_step": manifest["next_required_step"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.3 S07-P2 WPS file adapter replay evidence.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args(argv)

    result = validate_v013_s07_p2_wps_file_adapter_replay(args.manifest)
    print(
        "PASS: KMFA v0.1.3 S07-P2 WPS file adapter replay validated "
        f"(exports={result['source_export_type_count']}, "
        f"field_mappings={result['field_mapping_count']}, "
        f"conversion_guidance={result['conversion_guidance_count']}, "
        f"q5_allowed={result['q5_calculation_baseline_allowed_count']}, "
        "stage7_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
