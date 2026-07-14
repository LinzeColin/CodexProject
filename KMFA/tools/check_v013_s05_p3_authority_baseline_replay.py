#!/usr/bin/env python3
"""Validate KMFA v0.1.3 S05-P3 authority baseline replay evidence."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from KMFA.tools.check_v013_s05_p2_field_candidate_replay import validate_v013_s05_p2_field_candidate_replay
from KMFA.tools.v013_s05_p1_a0_file_registration import RAW_DIR
from KMFA.tools.v013_s05_p3_authority_baseline_replay import (
    EXPECTED_BASELINE_CONTENT_HASH,
    EXPECTED_BASELINE_VERSION,
    MANIFEST_PATH,
    REPORT_PATH,
    SCHEMA_VERSION,
    TASK_ID,
    TEST_RESULTS_PATH,
    validate_legacy_s05_p3,
)


BOOLEAN_FALSE_KEYS = (
    "raw_dir_read_required",
    "raw_dir_read_performed",
    "raw_dir_mutation_performed",
    "raw_layer_write_allowed",
    "raw_source_mutation_allowed",
    "raw_file_bytes_committed",
    "raw_filename_publication_allowed",
    "raw_file_hash_publication_allowed",
    "field_plaintext_publication_allowed",
    "sheet_name_publication_allowed",
    "zip_member_name_publication_allowed",
    "row_value_publication_allowed",
    "business_value_publication_allowed",
    "business_field_parsing_performed",
    "raw_value_matching_performed",
    "stage5_review_performed",
    "github_upload_performed",
    "delivery_allowed",
    "formal_report_allowed",
    "business_decision_basis_allowed",
    "business_execution_allowed",
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
    "normalized_business_values_committed",
)
FORBIDDEN_EVIDENCE_TEXT = (
    "raw_value:",
    "normalized_value:",
    "source_header_text:",
    "member_sha256:",
    "actual_package_sha256",
    "合同额",
    "支出合计",
    "毛利率",
    "成本分类",
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


def validate_v013_s05_p3_authority_baseline_replay(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    manifest = read_json(manifest_path)
    s05_p2 = validate_v013_s05_p2_field_candidate_replay()
    legacy = validate_legacy_s05_p3()
    summary = manifest.get("authority_baseline_summary", {})
    lock = manifest.get("baseline_lock", {})

    require(manifest.get("schema_version") == SCHEMA_VERSION, "manifest schema mismatch")
    require(manifest.get("project_id") == "KMFA", "project_id mismatch")
    require(manifest.get("version") == "0.1.3", "version mismatch")
    require(manifest.get("stage_id") == "S05", "stage_id must be S05")
    require(manifest.get("phase_id") == "S05-P3", "phase_id must be S05-P3")
    require(
        manifest.get("phase_scope") == "v013_s05_p3_authority_baseline_replay_only",
        "phase scope mismatch",
    )
    require(manifest.get("task_id") == TASK_ID, "task_id mismatch")
    require(
        manifest.get("status") == "completed_validated_local_only_no_go_upload_deferred_authority_baseline_replayed",
        "status mismatch",
    )
    require(manifest.get("completed_task_ids") == ["S5PCT01", "S5PCT02", "S5PCT03"], "task ids mismatch")

    require(s05_p2.get("phase_id") == "S05-P2", "S05-P2 dependency phase mismatch")
    require(s05_p2.get("github_upload_performed") is False, "S05-P2 upload boundary mismatch")
    require(
        s05_p2.get("github_upload_deferred_until_stage10_batch") is True,
        "S05-P2 upload deferral boundary mismatch",
    )
    require(manifest.get("s05_p2_dependency_validated") is True, "S05-P2 dependency flag must be true")
    require(manifest.get("legacy_s05_p3_dependency_validated") is True, "legacy S05-P3 dependency flag must be true")

    expected_summary = {
        "baseline_version": EXPECTED_BASELINE_VERSION,
        "baseline_content_hash": EXPECTED_BASELINE_CONTENT_HASH,
        "authority_records": 45,
        "total_fixture_fields": 45,
        "q5_locked_field_count": 40,
        "excluded_field_count": 5,
        "q4_human_confirmed_count": 40,
        "q5_calculation_baseline_allowed_count": 40,
        "formal_report_allowed": False,
        "stage5_review_completed": False,
        "github_upload_allowed": False,
        "lock_status_counts": {
            "excluded_cross_source_support_only": 5,
            "q5_locked_public_safe_hash_baseline": 40,
        },
        "locked_source_format_counts": {"pdf": 40},
        "raw_business_values_committed": False,
        "normalized_business_values_committed": False,
        "raw_file_bytes_committed": False,
        "private_csv_committed": False,
    }
    for key, expected in expected_summary.items():
        require(summary.get(key) == expected, f"authority summary {key} mismatch")
        require(legacy.get(key) == expected, f"legacy authority summary {key} mismatch")

    require(lock.get("authority_baseline_lock_performed") is True, "baseline lock must be performed")
    require(lock.get("public_safe_hash_lock_only") is True, "baseline lock must be public-safe hash only")
    require(
        lock.get("raw_or_normalized_value_publication_performed") is False,
        "raw/normalized value publication must be false",
    )
    require(
        lock.get("raw_file_or_business_document_publication_performed") is False,
        "raw file or business document publication must be false",
    )
    require(
        lock.get("field_or_header_plaintext_publication_performed") is False,
        "field/header plaintext publication must be false",
    )
    require(lock.get("formal_report_release_performed") is False, "formal report release must be false")

    raw_boundary = manifest.get("raw_data_boundary", {})
    require(raw_boundary.get("local_raw_data_dir") == str(RAW_DIR), "raw directory mismatch")
    require(
        raw_boundary.get("local_raw_data_dir_role") == "user_finance_raw_business_data_inbox",
        "raw directory role mismatch",
    )
    require(raw_boundary.get("codex_read_required_by_this_phase") is False, "raw read required flag must be false")
    require(raw_boundary.get("codex_read_performed_by_this_phase") is False, "raw read performed flag must be false")
    require(raw_boundary.get("codex_modify_allowed") is False, "raw modify allowed must be false")
    require(raw_boundary.get("codex_delete_allowed") is False, "raw delete allowed must be false")
    require(raw_boundary.get("codex_move_allowed") is False, "raw move allowed must be false")
    require(raw_boundary.get("codex_rename_allowed") is False, "raw rename allowed must be false")
    require(raw_boundary.get("codex_overwrite_allowed") is False, "raw overwrite allowed must be false")
    require(raw_boundary.get("codex_generate_inside_allowed") is False, "raw generate-inside allowed must be false")
    require(
        raw_boundary.get("codex_create_extra_files_inside_allowed") is False,
        "raw create-extra-files-inside allowed must be false",
    )
    require(raw_boundary.get("github_commit_allowed") is False, "raw GitHub commit allowed must be false")
    require(
        raw_boundary.get("private_runtime_output_dir") == "KMFA/.codex_private_runtime/",
        "private runtime output dir mismatch",
    )

    for key in BOOLEAN_FALSE_KEYS:
        require(manifest.get(key) is False, f"{key} must be false")
    require(manifest.get("s05_p3_performed") is True, "S05-P3 performed flag must be true")
    require(manifest.get("github_upload_deferred_until_stage10_batch") is True, "upload deferral flag must be true")
    safety = manifest.get("public_repo_safety", {})
    for key in PUBLIC_SAFETY_FALSE_KEYS:
        require(safety.get(key) is False, f"public_repo_safety.{key} must be false")

    require(manifest.get("current_data_quality_grade") == "Q2", "quality grade mismatch")
    require(manifest.get("current_report_grade") == "D", "report grade mismatch")
    require(manifest.get("release_permission") == "blocked", "release permission mismatch")
    next_step = manifest.get("next_required_step", "")
    require("Stage 5 whole review" in next_step, "next step must point to Stage 5 whole review")
    require("separate run" in next_step, "next step must preserve one-run boundary")
    require("Stage 1-10" in next_step, "next step must preserve batch upload boundary")
    require("GitHub upload" in next_step, "next step must preserve upload prohibition")

    for ref in manifest.get("legacy_s05_p3_refs", []):
        require(Path(ref).exists(), f"missing legacy S05-P3 ref: {ref}")
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
        "s05_p2_dependency_validated": manifest["s05_p2_dependency_validated"],
        "legacy_s05_p3_dependency_validated": manifest["legacy_s05_p3_dependency_validated"],
        "baseline_version": summary["baseline_version"],
        "baseline_content_hash": summary["baseline_content_hash"],
        "authority_records": summary["authority_records"],
        "q5_locked_field_count": summary["q5_locked_field_count"],
        "excluded_field_count": summary["excluded_field_count"],
        "formal_report_allowed": summary["formal_report_allowed"],
        "raw_dir_read_required": manifest["raw_dir_read_required"],
        "raw_dir_read_performed": manifest["raw_dir_read_performed"],
        "raw_dir_mutation_performed": manifest["raw_dir_mutation_performed"],
        "field_plaintext_publication_allowed": manifest["field_plaintext_publication_allowed"],
        "s05_p3_performed": manifest["s05_p3_performed"],
        "stage5_review_performed": manifest["stage5_review_performed"],
        "github_upload_performed": manifest["github_upload_performed"],
        "github_upload_deferred_until_stage10_batch": manifest["github_upload_deferred_until_stage10_batch"],
        "delivery_allowed": manifest["delivery_allowed"],
        "current_data_quality_grade": manifest["current_data_quality_grade"],
        "current_report_grade": manifest["current_report_grade"],
        "release_permission": manifest["release_permission"],
        "next_required_step": manifest["next_required_step"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.3 S05-P3 authority baseline replay evidence.")
    parser.add_argument("--manifest", default=str(MANIFEST_PATH))
    args = parser.parse_args(argv)
    result = validate_v013_s05_p3_authority_baseline_replay(Path(args.manifest))
    print(
        "PASS: KMFA v0.1.3 S05-P3 authority baseline replay validator passed "
        f"(authority_records={result['authority_records']}, "
        f"q5_locked={result['q5_locked_field_count']}, "
        f"excluded={result['excluded_field_count']}, "
        f"formal_report_allowed={str(result['formal_report_allowed']).lower()}, "
        f"github_upload={str(result['github_upload_performed']).lower()})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
