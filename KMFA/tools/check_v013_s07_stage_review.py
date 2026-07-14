#!/usr/bin/env python3
"""Validate KMFA v0.1.3 Stage 7 review evidence."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from KMFA.tools.check_v013_s07_p1_finance_file_adapter_replay import (
    validate_v013_s07_p1_finance_file_adapter_replay,
)
from KMFA.tools.check_v013_s07_p2_wps_file_adapter_replay import (
    validate_v013_s07_p2_wps_file_adapter_replay,
)
from KMFA.tools.check_v013_s07_p3_redcircle_postponement_replay import (
    validate_v013_s07_p3_redcircle_postponement_replay,
)
from KMFA.tools.v013_s07_stage_review import (
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
    "S07-P1": Path(
        "KMFA/stage_artifacts/V013_S07_P1_FINANCE_FILE_ADAPTER_REPLAY/machine/"
        "finance_file_adapter_replay_manifest.json"
    ),
    "S07-P2": Path(
        "KMFA/stage_artifacts/V013_S07_P2_WPS_FILE_ADAPTER_REPLAY/machine/"
        "wps_file_adapter_replay_manifest.json"
    ),
    "S07-P3": Path(
        "KMFA/stage_artifacts/V013_S07_P3_REDCIRCLE_POSTPONEMENT_REPLAY/machine/"
        "redcircle_postponement_replay_manifest.json"
    ),
}
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
    "raw_business_values_committed",
    "normalized_business_values_committed",
)
REQUIRED_HARD_BLOCKS = (
    "raw_data_mutation_forbidden",
    "raw_value_publication_forbidden",
    "field_header_plaintext_publication_forbidden",
    "adapter_candidates_remain_structural_or_reserved",
    "q5_forbidden_until_stage7_downstream_review_and_evidence_closure",
    "formal_report_release_blocked",
    "lineage_full_check_not_performed",
    "raw_value_matching_not_performed",
    "redcircle_automatic_connector_blocked",
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


def validate_v013_s07_stage_review(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    manifest = read_json(manifest_path)
    p1_result = validate_v013_s07_p1_finance_file_adapter_replay()
    p2_result = validate_v013_s07_p2_wps_file_adapter_replay()
    p3_result = validate_v013_s07_p3_redcircle_postponement_replay()

    require(manifest.get("schema_version") == SCHEMA_VERSION, "manifest schema mismatch")
    require(manifest.get("project_id") == "KMFA", "project_id mismatch")
    require(manifest.get("version") == "0.1.3", "version mismatch")
    require(manifest.get("stage_id") == "S07", "stage_id must be S07")
    require(manifest.get("review_id") == TASK_ID, "review_id mismatch")
    require(manifest.get("task_id") == TASK_ID, "task_id mismatch")
    require(manifest.get("review_scope") == REVIEW_SCOPE, "review scope mismatch")
    require(manifest.get("status") == "review_passed_upload_deferred_until_stage10_batch_no_go", "status mismatch")
    require(manifest.get("stage_review_performed") is True, "stage review must be performed")
    require(manifest.get("s08_p1_performed") is False, "S08-P1 must not be performed")
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
    require(manifest.get("legacy_stage7_upload_artifacts_current_gate") is False, "legacy upload must not be current")
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
    require(phase_results == {"S07-P1": "PASS", "S07-P2": "PASS", "S07-P3": "PASS"}, "phase_results mismatch")
    require(manifest.get("s07_p1_dependency_validated") is True, "S07-P1 dependency flag mismatch")
    require(manifest.get("s07_p2_dependency_validated") is True, "S07-P2 dependency flag mismatch")
    require(manifest.get("s07_p3_dependency_validated") is True, "S07-P3 dependency flag mismatch")
    require(p1_result.get("phase_id") == "S07-P1", "S07-P1 validator did not return S07-P1")
    require(p2_result.get("phase_id") == "S07-P2", "S07-P2 validator did not return S07-P2")
    require(p3_result.get("phase_id") == "S07-P3", "S07-P3 validator did not return S07-P3")
    require(p1_result.get("stage7_review_performed") is False, "S07-P1 phase scope must not include review")
    require(p2_result.get("stage7_review_performed") is False, "S07-P2 phase scope must not include review")
    require(p3_result.get("stage7_review_performed") is False, "S07-P3 phase scope must not include review")
    for result, label in ((p1_result, "S07-P1"), (p2_result, "S07-P2"), (p3_result, "S07-P3")):
        require(result.get("github_upload_performed") is False, f"{label} upload boundary mismatch")
        require(result.get("raw_dir_read_performed") is False, f"{label} raw read boundary mismatch")
        require(result.get("raw_dir_mutation_performed") is False, f"{label} raw mutation boundary mismatch")

    phase_summary = manifest.get("phase_summary", {})
    p1_summary = phase_summary.get("S07-P1", {})
    require(p1_summary.get("source_category_count") == 9, "S07-P1 source category count mismatch")
    require(p1_summary.get("field_candidate_count") == 45, "S07-P1 field candidate count mismatch")
    require(p1_summary.get("hash_only_field_candidate_count") == 45, "S07-P1 hash-only count mismatch")
    require(p1_summary.get("field_report_count") == 9, "S07-P1 field report count mismatch")
    require(p1_summary.get("source_header_hash_count") == 45, "S07-P1 source header hash count mismatch")
    require(p1_summary.get("q4_human_confirmed_count") == 0, "S07-P1 Q4 count mismatch")
    require(p1_summary.get("q5_calculation_baseline_allowed_count") == 0, "S07-P1 Q5 count mismatch")
    require(p1_summary.get("formal_report_allowed_count") == 0, "S07-P1 formal report count mismatch")

    p2_summary = phase_summary.get("S07-P2", {})
    require(p2_summary.get("source_export_type_count") == 4, "S07-P2 export type count mismatch")
    require(p2_summary.get("field_mapping_count") == 20, "S07-P2 field mapping count mismatch")
    require(p2_summary.get("hash_only_field_mapping_count") == 20, "S07-P2 hash-only count mismatch")
    require(p2_summary.get("field_report_count") == 4, "S07-P2 field report count mismatch")
    require(p2_summary.get("conversion_guidance_count") == 4, "S07-P2 conversion guidance count mismatch")
    require(p2_summary.get("mapping_rule_version_count") == 1, "S07-P2 mapping version count mismatch")
    require(p2_summary.get("source_header_hash_count") == 20, "S07-P2 source header hash count mismatch")
    require(p2_summary.get("native_conversion_required_count") == 4, "S07-P2 native conversion count mismatch")
    require(p2_summary.get("q4_human_confirmed_count") == 0, "S07-P2 Q4 count mismatch")
    require(p2_summary.get("q5_calculation_baseline_allowed_count") == 0, "S07-P2 Q5 count mismatch")
    require(p2_summary.get("formal_report_allowed_count") == 0, "S07-P2 formal report count mismatch")

    p3_summary = phase_summary.get("S07-P3", {})
    require(p3_summary.get("reserved_template_count") == 4, "S07-P3 template count mismatch")
    require(p3_summary.get("connector_policy_count") == 1, "S07-P3 connector policy count mismatch")
    require(p3_summary.get("rollback_plan_count") == 4, "S07-P3 rollback plan count mismatch")
    require(p3_summary.get("automatic_connector_allowed_count") == 0, "S07-P3 connector allowed count mismatch")
    require(p3_summary.get("registry_source_count") == 4, "S07-P3 registry source count mismatch")
    require(p3_summary.get("template_contract_hash_count") == 4, "S07-P3 template hash count mismatch")
    require(p3_summary.get("source_private_ref_count") == 4, "S07-P3 private ref count mismatch")
    require(p3_summary.get("manual_export_file_allowed_count") == 4, "S07-P3 manual export count mismatch")
    require(p3_summary.get("q4_human_confirmed_count") == 0, "S07-P3 Q4 count mismatch")
    require(p3_summary.get("q5_calculation_baseline_allowed_count") == 0, "S07-P3 Q5 count mismatch")
    require(p3_summary.get("formal_report_allowed_count") == 0, "S07-P3 formal report count mismatch")
    require(p3_summary.get("d15_file_mvp_automatic_connector_allowed") is False, "D15 connector must stay blocked")
    require(p3_summary.get("external_connector_included") is False, "external connector must stay false")
    require(p3_summary.get("read_only_required") is True, "read-only control mismatch")
    require(p3_summary.get("hash_retention_required") is True, "hash retention control mismatch")
    require(p3_summary.get("rollback_plan_required") is True, "rollback plan control mismatch")
    require(p3_summary.get("manual_approval_required") is True, "manual approval control mismatch")

    require(manifest.get("q5_allowed_count") == 0, "stage Q5 allowed count mismatch")
    require(manifest.get("formal_report_allowed_count") == 0, "stage formal report count mismatch")
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
        raw_boundary.get("local_raw_data_dir_role") == "user_finance_raw_private_inbox",
        "raw directory role mismatch",
    )
    require(raw_boundary.get("codex_read_allowed_only_when_phase_requires") is True, "raw read policy mismatch")
    require(raw_boundary.get("codex_read_required_by_this_stage_review") is False, "review raw read required mismatch")
    require(raw_boundary.get("codex_read_performed_by_this_stage_review") is False, "review raw read performed mismatch")
    for key in (
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

    reviewed_phase_manifests = manifest.get("reviewed_phase_manifests", {})
    for phase, path in PHASE_MANIFESTS.items():
        require(reviewed_phase_manifests.get(phase) == path.as_posix(), f"{phase} manifest ref mismatch")
        require(path.exists(), f"{phase} manifest missing")

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
        "review_scope": manifest["review_scope"],
        "status": manifest["status"],
        "phase_count": manifest["phase_count"],
        "phase_results": manifest["phase_results"],
        "s07_p1_dependency_validated": manifest["s07_p1_dependency_validated"],
        "s07_p2_dependency_validated": manifest["s07_p2_dependency_validated"],
        "s07_p3_dependency_validated": manifest["s07_p3_dependency_validated"],
        "stage_review_performed": manifest["stage_review_performed"],
        "s08_p1_performed": manifest["s08_p1_performed"],
        "open_review_finding_count": manifest["open_review_finding_count"],
        "fixed_review_finding_count": manifest["fixed_review_finding_count"],
        "q5_allowed_count": manifest["q5_allowed_count"],
        "formal_report_allowed_count": manifest["formal_report_allowed_count"],
        "current_data_quality_grade": manifest["current_data_quality_grade"],
        "current_report_grade": manifest["current_report_grade"],
        "release_permission": manifest["release_permission"],
        "raw_dir_read_performed_by_stage_review": manifest["raw_dir_read_performed_by_stage_review"],
        "raw_dir_read_performed_by_dependency_validators": manifest["raw_dir_read_performed_by_dependency_validators"],
        "raw_dir_mutation_performed": manifest["raw_dir_mutation_performed"],
        "github_upload_performed": manifest["github_upload_performed"],
        "github_upload_deferred_until_stage10_batch": manifest["github_upload_deferred_until_stage10_batch"],
        "delivery_allowed": manifest["delivery_allowed"],
        "formal_report_allowed": manifest["formal_report_allowed"],
        "business_execution_allowed": manifest["business_execution_allowed"],
        "next_required_step": manifest["next_required_step"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.3 Stage 7 review evidence.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args(argv)

    result = validate_v013_s07_stage_review(args.manifest)
    print(
        "PASS: KMFA v0.1.3 Stage 7 review validated "
        f"(phases={result['phase_count']}, "
        f"findings_open={result['open_review_finding_count']}, "
        f"q5_allowed={result['q5_allowed_count']}, "
        "stage8=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
