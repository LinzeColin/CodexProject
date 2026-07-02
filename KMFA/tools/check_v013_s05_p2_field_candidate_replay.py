#!/usr/bin/env python3
"""Validate KMFA v0.1.3 S05-P2 field candidate replay evidence."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from KMFA.tools.check_v013_s05_p1_a0_file_registration import validate_v013_s05_p1_a0_file_registration
from KMFA.tools.v013_s05_p1_a0_file_registration import RAW_DIR
from KMFA.tools.v013_s05_p2_field_candidate_replay import (
    MANIFEST_PATH,
    REPORT_PATH,
    SCHEMA_VERSION,
    TASK_ID,
    TEST_RESULTS_PATH,
    validate_legacy_s05_p2,
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
    "s05_p3_performed",
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
    "sk-",
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


def validate_v013_s05_p2_field_candidate_replay(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    manifest = read_json(manifest_path)
    s05_p1 = validate_v013_s05_p1_a0_file_registration()
    legacy = validate_legacy_s05_p2()
    legacy_summary = legacy["fixture_summary"]
    summary = manifest.get("field_candidate_summary", {})
    owner = manifest.get("owner_decision_summary", {})
    gate = manifest.get("completion_gate", {})

    require(manifest.get("schema_version") == SCHEMA_VERSION, "manifest schema mismatch")
    require(manifest.get("project_id") == "KMFA", "project_id mismatch")
    require(manifest.get("version") == "0.1.3", "version mismatch")
    require(manifest.get("stage_id") == "S05", "stage_id must be S05")
    require(manifest.get("phase_id") == "S05-P2", "phase_id must be S05-P2")
    require(
        manifest.get("phase_scope") == "v013_s05_p2_field_candidate_replay_only",
        "phase scope mismatch",
    )
    require(manifest.get("task_id") == TASK_ID, "task_id mismatch")
    require(
        manifest.get("status") == "completed_validated_local_only_no_go_upload_deferred_owner_downgrade_replayed",
        "status mismatch",
    )
    require(manifest.get("completed_task_ids") == ["S5PBT01", "S5PBT02", "S5PBT03"], "task ids mismatch")

    require(s05_p1.get("phase_id") == "S05-P1", "S05-P1 dependency phase mismatch")
    require(s05_p1.get("github_upload_performed") is False, "S05-P1 upload boundary mismatch")
    require(
        s05_p1.get("github_upload_deferred_until_stage10_batch") is True,
        "S05-P1 upload deferral boundary mismatch",
    )
    require(manifest.get("s05_p1_dependency_validated") is True, "S05-P1 dependency flag must be true")
    require(manifest.get("legacy_s05_p2_dependency_validated") is True, "legacy S05-P2 dependency flag must be true")

    expected_summary = {
        "a0_project_candidates": 9,
        "required_fields_per_candidate": 5,
        "fixture_candidate_count": 45,
        "private_value_hash_recorded_count": 40,
        "private_value_pending_count": 5,
        "source_anchor_recorded_count": 40,
        "source_anchor_pending_count": 5,
        "source_format_counts": {"pdf": 40, "xlsx": 5},
        "q3_field_candidate_count": 45,
        "q4_human_confirmed_count": 0,
        "q5_calculation_baseline_allowed_count": 0,
        "pending_source_candidate_count": 1,
    }
    for key, expected in expected_summary.items():
        require(summary.get(key) == expected, f"field summary {key} mismatch")
        require(legacy_summary.get(key) == expected, f"legacy summary {key} mismatch")

    require(owner.get("owner_packet_status") == "awaiting_owner_or_authorized_decision", "owner packet status mismatch")
    require(owner.get("owner_allowed_decision_count") == 3, "owner allowed decision count mismatch")
    require(owner.get("owner_template_count") == 3, "owner template count mismatch")
    require(owner.get("active_decision_present") is True, "active decision must be present")
    require(owner.get("active_actor_role_validated") is True, "active actor role must be validated")
    require(owner.get("active_decision_code") == "downgrade_to_cross_source_support", "active decision mismatch")
    require(owner.get("active_decision_public_safe") is True, "active decision public safety mismatch")
    require(
        owner.get("active_decision_raw_or_plaintext_values_included") is False,
        "active decision must not include raw/plaintext values",
    )
    require(owner.get("active_preview_status") == "ready", "active preview status mismatch")
    require(owner.get("active_preview_candidate_role") == "cross_source_support_only", "active preview role mismatch")
    require(owner.get("active_preview_q5_exclusion_confirmed") is True, "active preview q5 exclusion mismatch")

    require(gate.get("ready") is True, "completion gate must be ready with active downgrade")
    require(gate.get("mode") == "owner_downgrade_to_cross_source_support", "completion gate mode mismatch")
    require(gate.get("reason") == "active_owner_or_authorized_decision_resolves_excel_candidate", "completion reason mismatch")
    require(gate.get("pending_fields") == 5, "completion pending fields mismatch")
    require(gate.get("q4_confirmation_claimed") is False, "Q4 must not be claimed")
    require(gate.get("q5_baseline_claimed") is False, "Q5 must not be claimed")
    require(gate.get("stage5_review_claimed") is False, "Stage 5 review must not be claimed")

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
    require(manifest.get("github_upload_deferred_until_stage10_batch") is True, "upload deferral flag must be true")
    safety = manifest.get("public_repo_safety", {})
    for key in PUBLIC_SAFETY_FALSE_KEYS:
        require(safety.get(key) is False, f"public_repo_safety.{key} must be false")

    require(manifest.get("current_data_quality_grade") == "Q2", "quality grade mismatch")
    require(manifest.get("current_report_grade") == "D", "report grade mismatch")
    require(manifest.get("release_permission") == "blocked", "release permission mismatch")
    next_step = manifest.get("next_required_step", "")
    require("S05-P3" in next_step, "next step must point to S05-P3")
    require("separate run" in next_step, "next step must preserve one-run boundary")
    require("Stage 5 review" in next_step, "next step must block Stage 5 review in this phase")
    require("Stage 1-10" in next_step, "next step must preserve batch upload boundary")

    for ref in manifest.get("legacy_s05_p2_refs", []):
        require(Path(ref).exists(), f"missing legacy S05-P2 ref: {ref}")
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
        "s05_p1_dependency_validated": manifest["s05_p1_dependency_validated"],
        "legacy_s05_p2_dependency_validated": manifest["legacy_s05_p2_dependency_validated"],
        "fixture_candidate_count": summary["fixture_candidate_count"],
        "required_fields_per_candidate": summary["required_fields_per_candidate"],
        "private_value_hash_recorded_count": summary["private_value_hash_recorded_count"],
        "private_value_pending_count": summary["private_value_pending_count"],
        "source_anchor_recorded_count": summary["source_anchor_recorded_count"],
        "source_anchor_pending_count": summary["source_anchor_pending_count"],
        "pending_source_candidate_count": summary["pending_source_candidate_count"],
        "q4_human_confirmed_count": summary["q4_human_confirmed_count"],
        "q5_calculation_baseline_allowed_count": summary["q5_calculation_baseline_allowed_count"],
        "active_decision_code": owner["active_decision_code"],
        "completion_gate_ready": gate["ready"],
        "completion_gate_mode": gate["mode"],
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
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.3 S05-P2 field candidate replay evidence.")
    parser.add_argument("--manifest", default=str(MANIFEST_PATH))
    args = parser.parse_args(argv)
    result = validate_v013_s05_p2_field_candidate_replay(Path(args.manifest))
    print(
        "PASS: KMFA v0.1.3 S05-P2 field candidate replay validator passed "
        f"(fixture_candidates={result['fixture_candidate_count']}, "
        f"hash_recorded={result['private_value_hash_recorded_count']}, "
        f"pending={result['private_value_pending_count']}, "
        f"owner_decision={result['active_decision_code']}, "
        f"github_upload={str(result['github_upload_performed']).lower()})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
