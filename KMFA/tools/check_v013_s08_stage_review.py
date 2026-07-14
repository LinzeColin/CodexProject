#!/usr/bin/env python3
"""Validate KMFA v0.1.3 Stage 8 review evidence."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from KMFA.tools.check_v013_s08_p1_project_composite_key_replay import (
    validate_v013_s08_p1_project_composite_key_replay,
)
from KMFA.tools.check_v013_s08_p2_business_entity_model_replay import (
    validate_v013_s08_p2_business_entity_model_replay,
)
from KMFA.tools.check_v013_s08_p3_entity_matching_quality_replay import (
    validate_v013_s08_p3_entity_matching_quality_replay,
)
from KMFA.tools.v013_s08_stage_review import (
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
    "S08-P1": Path(
        "KMFA/stage_artifacts/V013_S08_P1_PROJECT_COMPOSITE_KEY_REPLAY/machine/"
        "project_composite_key_replay_manifest.json"
    ),
    "S08-P2": Path(
        "KMFA/stage_artifacts/V013_S08_P2_BUSINESS_ENTITY_MODEL_REPLAY/machine/"
        "business_entity_model_replay_manifest.json"
    ),
    "S08-P3": Path(
        "KMFA/stage_artifacts/V013_S08_P3_ENTITY_MATCHING_QUALITY_REPLAY/machine/"
        "entity_matching_quality_replay_manifest.json"
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
    "source_record_payload_committed",
    "normalized_source_values_committed",
    "project_identity_plaintext_committed",
    "business_entity_plaintext_committed",
    "business_relationship_values_committed",
    "business_lifecycle_values_committed",
    "entity_matching_plaintext_committed",
    "entity_matching_business_values_committed",
    "entity_matching_report_formal_report_committed",
)
REQUIRED_HARD_BLOCKS = (
    "raw_data_mutation_forbidden",
    "raw_value_publication_forbidden",
    "field_header_plaintext_publication_forbidden",
    "project_identity_values_remain_hash_ref_or_status_only",
    "medium_high_risk_auto_merge_forbidden",
    "manual_review_queue_auto_merge_forbidden",
    "q5_forbidden_until_stage9_reconciliation_and_quality_evidence",
    "formal_report_release_blocked",
    "lineage_full_check_not_performed",
    "raw_value_matching_not_performed",
    "github_upload_deferred_until_stage10_batch",
    "s09_p1_not_performed",
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
    "project_name_plaintext",
    "customer_name_plaintext",
    "counterparty_plaintext",
    "company_entity_plaintext",
    "account_number",
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


def validate_v013_s08_stage_review(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    manifest = read_json(manifest_path)
    p1 = validate_v013_s08_p1_project_composite_key_replay()
    p2 = validate_v013_s08_p2_business_entity_model_replay()
    p3 = validate_v013_s08_p3_entity_matching_quality_replay()

    require(manifest.get("schema_version") == SCHEMA_VERSION, "manifest schema mismatch")
    require(manifest.get("project_id") == "KMFA", "project_id mismatch")
    require(manifest.get("version") == "0.1.3", "version mismatch")
    require(manifest.get("stage_id") == "S08", "stage_id must be S08")
    require(manifest.get("review_id") == TASK_ID, "review_id mismatch")
    require(manifest.get("task_id") == TASK_ID, "task_id mismatch")
    require(manifest.get("review_scope") == REVIEW_SCOPE, "review scope mismatch")
    require(manifest.get("status") == "review_passed_upload_deferred_until_stage10_batch_no_go", "status mismatch")
    require(manifest.get("stage_review_performed") is True, "stage review must be performed")
    require(manifest.get("s09_p1_performed") is False, "S09-P1 must not be performed")
    require(manifest.get("github_upload_ready_next_gate") is False, "upload ready must stay false")
    require(
        manifest.get("github_upload_deferred_until_stage10_batch") is True,
        "upload must stay deferred until Stage 1-10 batch",
    )
    require(manifest.get("github_upload_performed") is False, "GitHub upload must not be performed")
    require(
        manifest.get("github_upload_status") == "not_uploaded_deferred_until_stage10_batch",
        "GitHub upload status mismatch",
    )
    require(manifest.get("legacy_stage8_upload_artifacts_current_gate") is False, "legacy upload must not be current")
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
    require(manifest.get("fixed_review_finding_count") == 1, "fixed review findings must be 1")
    require(manifest.get("next_required_step") == NEXT_REQUIRED_STEP, "next_required_step mismatch")

    findings = manifest.get("review_findings")
    require(isinstance(findings, list), "review_findings must be a list")
    require(
        any(finding.get("finding_id") == "KMFA-V013-S08-REV-F01" and finding.get("status") == "fixed"
            for finding in findings or []),
        "missing fixed legacy upload finding",
    )

    phase_results = manifest.get("phase_results", {})
    require(phase_results == {"S08-P1": "PASS", "S08-P2": "PASS", "S08-P3": "PASS"}, "phase_results mismatch")
    require(manifest.get("s08_p1_dependency_validated") is True, "S08-P1 dependency flag mismatch")
    require(manifest.get("s08_p2_dependency_validated") is True, "S08-P2 dependency flag mismatch")
    require(manifest.get("s08_p3_dependency_validated") is True, "S08-P3 dependency flag mismatch")
    require(p1.get("phase_id") == "S08-P1", "S08-P1 validator did not return S08-P1")
    require(p2.get("phase_id") == "S08-P2", "S08-P2 validator did not return S08-P2")
    require(p3.get("phase_id") == "S08-P3", "S08-P3 validator did not return S08-P3")
    for result, label in ((p1, "S08-P1"), (p2, "S08-P2"), (p3, "S08-P3")):
        require(result.get("stage8_review_performed") is False, f"{label} phase scope must not include review")
        require(result.get("github_upload_performed") is False, f"{label} upload boundary mismatch")
        require(result.get("raw_dir_read_performed") is False, f"{label} raw read boundary mismatch")
        require(result.get("raw_dir_mutation_performed") is False, f"{label} raw mutation boundary mismatch")

    reviewed_phase_manifests = manifest.get("reviewed_phase_manifests", {})
    require(reviewed_phase_manifests == {key: path.as_posix() for key, path in PHASE_MANIFESTS.items()}, "phase manifests mismatch")
    for phase, path in PHASE_MANIFESTS.items():
        require(path.exists(), f"missing reviewed phase manifest for {phase}: {path}")

    phase_summary = manifest.get("phase_summary", {})
    p1_summary = phase_summary.get("S08-P1", {})
    require(p1_summary.get("required_component_count") == 8, "S08-P1 component count mismatch")
    require(p1_summary.get("profile_count") == 4, "S08-P1 profile count mismatch")
    require(p1_summary.get("match_result_count") == 3, "S08-P1 match result count mismatch")
    require(p1_summary.get("manual_review_queue_count") == 2, "S08-P1 review queue count mismatch")
    require(p1_summary.get("strong_auto_match_count") == 1, "S08-P1 strong auto match count mismatch")
    require(p1_summary.get("human_review_required_count") == 2, "S08-P1 human review count mismatch")
    require(p1_summary.get("matching_weights_sum_bps") == 10000, "S08-P1 weights mismatch")
    require(p1_summary.get("strong_threshold_bps") == 8500, "S08-P1 strong threshold mismatch")
    require(p1_summary.get("human_review_threshold_bps") == 7000, "S08-P1 review threshold mismatch")
    require(p1_summary.get("missing_single_component_blocks_all_matching") is False, "S08-P1 missing component policy mismatch")
    require(p1_summary.get("below_strong_threshold_enters_manual_review") is True, "S08-P1 manual review policy mismatch")

    p2_summary = phase_summary.get("S08-P2", {})
    require(p2_summary.get("required_entity_type_count") == 8, "S08-P2 entity type count mismatch")
    require(p2_summary.get("relationship_count") == 14, "S08-P2 relationship count mismatch")
    require(p2_summary.get("lifecycle_status_count") == 32, "S08-P2 lifecycle status count mismatch")
    require(p2_summary.get("lifecycle_status_per_entity_count") == 4, "S08-P2 lifecycle per entity mismatch")
    require(p2_summary.get("relationship_graph_required_links_present") is True, "S08-P2 relationship graph mismatch")

    p3_summary = phase_summary.get("S08-P3", {})
    require(p3_summary.get("scenario_count") == 4, "S08-P3 scenario count mismatch")
    require(p3_summary.get("quality_case_count") == 4, "S08-P3 quality case count mismatch")
    require(p3_summary.get("manual_review_queue_count") == 3, "S08-P3 review queue count mismatch")
    require(p3_summary.get("manual_review_case_count") == 3, "S08-P3 review case count mismatch")
    require(p3_summary.get("entity_matching_report_count") == 1, "S08-P3 report count mismatch")
    require(p3_summary.get("risk_summary", {}).get("high") == 2, "S08-P3 high risk count mismatch")
    require(p3_summary.get("risk_summary", {}).get("medium") == 1, "S08-P3 medium risk count mismatch")
    require(p3_summary.get("risk_summary", {}).get("low") == 1, "S08-P3 low risk count mismatch")
    require(
        p3_summary.get("auto_merge_allowed_for_review_queue_count") == 0,
        "S08-P3 review queue auto merge count mismatch",
    )

    for summary, label in (
        (p1_summary, "S08-P1"),
        (p2_summary, "S08-P2"),
        (p3_summary, "S08-P3"),
    ):
        require(summary.get("q5_calculation_baseline_allowed_count") == 0, f"{label} Q5 count mismatch")
        require(summary.get("formal_report_allowed_count") == 0, f"{label} formal report count mismatch")
        require(summary.get("raw_dir_read_performed") is False, f"{label} raw read summary mismatch")
        require(summary.get("raw_dir_mutation_performed") is False, f"{label} raw mutation summary mismatch")
        require(summary.get("github_upload_performed") is False, f"{label} upload summary mismatch")

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
    for key in (
        "codex_read_required_by_this_stage_review",
        "codex_read_performed_by_this_stage_review",
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
        "s08_p1_dependency_validated": manifest["s08_p1_dependency_validated"],
        "s08_p2_dependency_validated": manifest["s08_p2_dependency_validated"],
        "s08_p3_dependency_validated": manifest["s08_p3_dependency_validated"],
        "stage_review_performed": manifest["stage_review_performed"],
        "s09_p1_performed": manifest["s09_p1_performed"],
        "open_review_finding_count": manifest["open_review_finding_count"],
        "fixed_review_finding_count": manifest["fixed_review_finding_count"],
        "q5_allowed_count": manifest["q5_allowed_count"],
        "formal_report_allowed_count": manifest["formal_report_allowed_count"],
        "current_data_quality_grade": manifest["current_data_quality_grade"],
        "current_report_grade": manifest["current_report_grade"],
        "release_permission": manifest["release_permission"],
        "raw_dir_read_performed_by_stage_review": manifest["raw_dir_read_performed_by_stage_review"],
        "raw_dir_read_performed_by_dependency_validators": manifest[
            "raw_dir_read_performed_by_dependency_validators"
        ],
        "raw_dir_mutation_performed": manifest["raw_dir_mutation_performed"],
        "github_upload_performed": manifest["github_upload_performed"],
        "github_upload_deferred_until_stage10_batch": manifest[
            "github_upload_deferred_until_stage10_batch"
        ],
        "legacy_stage8_upload_artifacts_current_gate": manifest["legacy_stage8_upload_artifacts_current_gate"],
        "delivery_allowed": manifest["delivery_allowed"],
        "formal_report_allowed": manifest["formal_report_allowed"],
        "business_execution_allowed": manifest["business_execution_allowed"],
        "next_required_step": manifest["next_required_step"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.3 Stage 8 review evidence.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args(argv)

    try:
        result = validate_v013_s08_stage_review(args.manifest)
    except (OSError, json.JSONDecodeError, ValidationError) as exc:
        print(f"FAIL: KMFA v0.1.3 Stage 8 review validation failed ({exc})")
        return 1

    print(
        "PASS: KMFA v0.1.3 Stage 8 review validated "
        f"(phase_results={result['phase_results']}, "
        f"open_findings={result['open_review_finding_count']}, "
        f"fixed_findings={result['fixed_review_finding_count']}, "
        f"s09_p1={str(result['s09_p1_performed']).lower()}, "
        f"github_upload={str(result['github_upload_performed']).lower()})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
