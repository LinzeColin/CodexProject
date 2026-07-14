#!/usr/bin/env python3
"""Validate KMFA v0.1.3 S03-P3 source priority evidence."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from KMFA.tools.check_v013_s03_p2_source_check_matrix import validate_v013_s03_p2_source_check_matrix
from KMFA.tools.source_priority import SOURCE_PRIORITY_ORDER
from KMFA.tools.v013_s03_p1_file_import_register import RAW_DIR
from KMFA.tools.v013_s03_p3_source_priority import (
    MANIFEST_PATH,
    REPORT_PATH,
    SCHEMA_VERSION,
    TASK_ID,
    TEST_RESULTS_PATH,
    replay_source_priority_capability,
)


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
    "sheet_names_committed",
    "zip_member_names_committed",
    "raw_business_values_committed",
    "source_priority_event_rows_committed",
    "source_difference_queue_rows_committed",
)
BOOLEAN_FALSE_KEYS = (
    "raw_dir_read_performed",
    "raw_dir_mutation_performed",
    "raw_layer_write_allowed",
    "raw_source_mutation_allowed",
    "raw_file_bytes_committed",
    "raw_filename_publication_allowed",
    "raw_file_hash_publication_allowed",
    "source_package_hash_publication_allowed",
    "source_package_storage_ref_publication_allowed",
    "field_plaintext_publication_allowed",
    "sheet_name_publication_allowed",
    "zip_member_name_publication_allowed",
    "row_value_publication_allowed",
    "business_value_publication_allowed",
    "business_field_parsing_performed",
    "raw_value_matching_performed",
    "stage3_review_performed",
    "github_upload_performed",
    "delivery_allowed",
    "formal_report_allowed",
    "business_decision_basis_allowed",
    "business_execution_allowed",
    "auto_selection_allowed",
    "auto_correction_allowed",
    "published_synthetic_priority_event",
    "published_synthetic_difference_queue",
)
FORBIDDEN_EVIDENCE_TEXT = (
    "raw_value:",
    "normalized_value:",
    "source_header_text:",
    "bank_statement",
    "contract_full_text",
    "salary_detail",
    "tax_filing",
    "-----" "BEGIN",
    "sk-",
    "private-ref:primary",
    "private-ref:conflicting",
)
FORBIDDEN_PUBLIC_SUFFIXES = (".zip", ".xlsx", ".xls", ".pdf", ".sqlite", ".db")


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


def validate_v013_s03_p3_source_priority(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    manifest = read_json(manifest_path)
    s03_p2 = validate_v013_s03_p2_source_check_matrix()
    capability = replay_source_priority_capability()

    require(manifest.get("schema_version") == SCHEMA_VERSION, "manifest schema mismatch")
    require(manifest.get("project_id") == "KMFA", "project_id mismatch")
    require(manifest.get("version") == "0.1.3", "version mismatch")
    require(manifest.get("stage_id") == "S03", "stage_id must be S03")
    require(manifest.get("phase_id") == "S03-P3", "phase_id must be S03-P3")
    require(manifest.get("phase_scope") == "v013_s03_p3_source_priority_only", "phase scope mismatch")
    require(manifest.get("task_id") == TASK_ID, "task_id mismatch")
    require(manifest.get("status") == "completed_validated_local_only_no_go_upload_deferred", "status mismatch")
    require(manifest.get("completed_task_ids") == ["S3PCT01", "S3PCT02", "S3PCT03"], "completed task ids mismatch")

    require(manifest.get("s03_p2_dependency_validated") is True, "S03-P2 dependency flag must be true")
    require(s03_p2.get("stage_id") == "S03", "S03-P2 validator did not return Stage 3")
    require(s03_p2.get("phase_id") == "S03-P2", "S03-P2 dependency phase mismatch")
    require(s03_p2.get("github_upload_performed") is False, "S03-P2 upload boundary mismatch")
    require(s03_p2.get("raw_dir_read_performed") is False, "S03-P2 raw read boundary mismatch")

    require(manifest.get("source_priority_dependency_validated") is True, "source priority dependency must be true")
    require(manifest.get("source_priority_order") == list(SOURCE_PRIORITY_ORDER), "source priority order mismatch")
    require(manifest.get("source_priority_order") == capability["source_priority_order"], "replayed priority order mismatch")
    require(manifest.get("source_priority_order_count") == len(SOURCE_PRIORITY_ORDER) == 9, "source priority count mismatch")
    require(
        manifest.get("same_source_inconsistency_actions") == capability["same_source_inconsistency_actions"],
        "same-source actions mismatch",
    )
    require(
        manifest.get("same_source_inconsistency_actions") == ["invalidate_derived_cache", "request_rerun"],
        "same-source actions must invalidate cache and request rerun",
    )
    require(
        manifest.get("same_source_invalidation_event_validated") is True
        and capability["same_source_invalidation_event_validated"] is True,
        "same-source invalidation event not validated",
    )
    require(
        manifest.get("same_source_rerun_requested") is True and capability["same_source_rerun_requested"] is True,
        "same-source rerun request not validated",
    )
    require(
        manifest.get("cross_source_difference_queue_validated") is True
        and capability["cross_source_difference_queue_validated"] is True,
        "cross-source difference queue not validated",
    )
    require(
        manifest.get("cross_source_resolution_policy") == capability["cross_source_resolution_policy"] == "manual_review_required",
        "cross-source resolution policy mismatch",
    )
    require(manifest.get("difference_queue_entry_count") == capability["difference_queue_entry_count"] == 1, "queue count mismatch")
    require(manifest.get("manual_review_required") is True, "manual review must be required")
    require(manifest.get("auto_selection_allowed") is False, "auto selection must be false")
    require(manifest.get("auto_correction_allowed") is False, "auto correction must be false")
    policy = manifest.get("cross_source_conflict_policy", {})
    require(policy.get("difference_queue") is True, "conflict policy must enable difference queue")
    require(policy.get("manual_review_required") is True, "conflict policy must require manual review")
    require(policy.get("auto_selection_allowed") is False, "conflict policy auto selection must be false")
    require(policy.get("auto_correction_allowed") is False, "conflict policy auto correction must be false")
    require(manifest.get("event_private_temp_write_only") is True, "event replay must be temp-only")

    raw_boundary = manifest.get("raw_data_boundary", {})
    require(raw_boundary.get("local_raw_data_dir") == RAW_DIR, "raw directory mismatch")
    require(raw_boundary.get("codex_read_allowed_only_when_phase_requires") is True, "raw read policy mismatch")
    require(raw_boundary.get("codex_read_performed_by_this_phase") is False, "raw read performed flag must be false")
    require(raw_boundary.get("codex_modify_allowed") is False, "raw modify allowed must be false")
    require(raw_boundary.get("codex_delete_allowed") is False, "raw delete allowed must be false")
    require(raw_boundary.get("codex_move_allowed") is False, "raw move allowed must be false")
    require(raw_boundary.get("codex_rename_allowed") is False, "raw rename allowed must be false")
    require(raw_boundary.get("codex_overwrite_allowed") is False, "raw overwrite allowed must be false")
    require(raw_boundary.get("codex_generate_inside_allowed") is False, "raw generate-inside allowed must be false")
    require(raw_boundary.get("github_commit_allowed") is False, "raw GitHub commit allowed must be false")

    for key in BOOLEAN_FALSE_KEYS:
        require(manifest.get(key) is False, f"{key} must be false")
    safety = manifest.get("public_repo_safety", {})
    for key in PUBLIC_SAFETY_FALSE_KEYS:
        require(safety.get(key) is False, f"public_repo_safety.{key} must be false")

    require(manifest.get("current_data_quality_grade") == "Q2", "quality grade mismatch")
    require(manifest.get("current_report_grade") == "D", "report grade mismatch")
    require(manifest.get("release_permission") == "blocked", "release permission mismatch")
    require("Stage 3 review" in manifest.get("next_required_step", ""), "next step must point to Stage 3 review")
    require("GitHub upload" in manifest.get("next_required_step", ""), "next step must preserve upload boundary")

    for ref in manifest.get("source_priority_refs", []):
        require(Path(ref).exists(), f"missing source priority dependency ref: {ref}")
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
        "status": manifest["status"],
        "s03_p2_dependency_validated": manifest["s03_p2_dependency_validated"],
        "source_priority_dependency_validated": manifest["source_priority_dependency_validated"],
        "source_priority_order": manifest["source_priority_order"],
        "source_priority_order_count": manifest["source_priority_order_count"],
        "same_source_inconsistency_actions": manifest["same_source_inconsistency_actions"],
        "same_source_invalidation_event_validated": manifest["same_source_invalidation_event_validated"],
        "same_source_rerun_requested": manifest["same_source_rerun_requested"],
        "cross_source_difference_queue_validated": manifest["cross_source_difference_queue_validated"],
        "cross_source_resolution_policy": manifest["cross_source_resolution_policy"],
        "manual_review_required": manifest["manual_review_required"],
        "auto_selection_allowed": manifest["auto_selection_allowed"],
        "auto_correction_allowed": manifest["auto_correction_allowed"],
        "raw_dir_read_performed": manifest["raw_dir_read_performed"],
        "raw_dir_mutation_performed": manifest["raw_dir_mutation_performed"],
        "raw_layer_write_allowed": manifest["raw_layer_write_allowed"],
        "raw_source_mutation_allowed": manifest["raw_source_mutation_allowed"],
        "raw_filename_publication_allowed": manifest["raw_filename_publication_allowed"],
        "raw_file_hash_publication_allowed": manifest["raw_file_hash_publication_allowed"],
        "business_field_parsing_performed": manifest["business_field_parsing_performed"],
        "raw_value_matching_performed": manifest["raw_value_matching_performed"],
        "stage3_review_performed": manifest["stage3_review_performed"],
        "github_upload_performed": manifest["github_upload_performed"],
        "delivery_allowed": manifest["delivery_allowed"],
        "current_data_quality_grade": manifest["current_data_quality_grade"],
        "current_report_grade": manifest["current_report_grade"],
        "release_permission": manifest["release_permission"],
        "next_required_step": manifest["next_required_step"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.3 S03-P3 source priority evidence.")
    parser.add_argument("--manifest", default=str(MANIFEST_PATH))
    args = parser.parse_args(argv)
    result = validate_v013_s03_p3_source_priority(Path(args.manifest))
    print(
        "PASS: KMFA v0.1.3 S03-P3 source priority validator passed "
        f"(priority_count={result['source_priority_order_count']}, "
        f"same_source_event={str(result['same_source_invalidation_event_validated']).lower()}, "
        f"difference_queue={str(result['cross_source_difference_queue_validated']).lower()}, "
        f"raw_read={str(result['raw_dir_read_performed']).lower()}, "
        f"github_upload={str(result['github_upload_performed']).lower()})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
