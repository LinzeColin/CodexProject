#!/usr/bin/env python3
"""Validate KMFA v0.1.4 S05-P2 field-level golden baseline evidence."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from KMFA.tools.check_v014_s05_p1_a0_file_registration import validate_v014_s05_p1_a0_file_registration
from KMFA.tools.v014_s05_p2_field_golden_baseline import (
    ACCEPTANCE_ID,
    FIELD_CONTRACT_ROLES,
    MANIFEST_PATH,
    PUBLIC_FIELD_CANDIDATES_PATH,
    PUBLIC_FIELD_CONTRACTS_PATH,
    RAW_INBOX,
    REPORT_PATH,
    RISK_REGISTER_PATH,
    ROLLBACK_PATH,
    SCHEMA_VERSION,
    TASK_ID,
    TEST_RESULTS_PATH,
    validate_owner_decision,
)


PUBLIC_FALSE_KEYS = (
    "raw_business_data_committed",
    "zip_committed",
    "excel_workbook_committed",
    "pdf_committed",
    "private_csv_committed",
    "sqlite_or_db_committed",
    "credentials_committed",
    "raw_filenames_committed",
    "raw_hashes_committed",
    "directory_tree_plaintext_committed",
    "zip_member_names_committed",
    "sheet_names_committed",
    "source_header_plaintext_committed",
    "source_or_normalized_values_committed",
    "row_or_cell_values_committed",
    "business_values_committed",
)
BOUNDARY_FALSE_KEYS = (
    "raw_inbox_read_by_this_phase",
    "raw_inbox_listed_by_this_phase",
    "raw_inbox_stat_by_this_phase",
    "raw_inbox_hashed_by_this_phase",
    "raw_inbox_modified_by_this_phase",
    "raw_inbox_deleted_by_this_phase",
    "raw_inbox_moved_by_this_phase",
    "raw_inbox_renamed_by_this_phase",
    "raw_inbox_overwritten_by_this_phase",
    "raw_inbox_written_by_this_phase",
    "raw_inbox_generate_inside_by_this_phase",
    "raw_inbox_create_extra_files_inside_by_this_phase",
    "raw_inbox_mutated_by_this_phase",
    "raw_filenames_committed",
    "raw_hashes_committed",
    "directory_tree_plaintext_committed",
    "zip_member_names_committed",
    "sheet_names_committed",
    "source_header_plaintext_committed",
    "row_or_cell_values_committed",
    "source_or_normalized_values_committed",
    "business_values_committed",
)
PHASE_SCOPE_FALSE_KEYS = (
    "raw_inbox_read_required_by_this_phase",
    "raw_inbox_read_by_this_phase",
    "raw_inbox_listed_by_this_phase",
    "raw_inbox_stat_by_this_phase",
    "raw_inbox_hashed_by_this_phase",
    "raw_inbox_mutated_by_this_phase",
    "private_runtime_written_by_this_phase",
    "business_field_parsing_from_raw_performed",
    "source_value_matching_performed",
    "s05_p3_performed",
    "stage5_review_performed",
    "github_upload_performed",
    "lineage_full_check_performed",
    "formal_report_performed",
    "live_connector_called",
    "opme_deep_coupling_performed",
    "business_execution_performed",
    "next_phase_started",
)
FORBIDDEN_PUBLIC_KEYS = {
    "actual_package_sha256",
    "expected_package_sha256",
    "member_sha256",
    "member_name",
    "member_path",
    "package_name",
    "candidate_label",
    "candidate_label_hash",
    "sheet_name",
    "raw_value",
    "normalized_value",
    "source_header_text",
    "cell_value",
    "row_value",
    "business_value",
}
FORBIDDEN_PUBLIC_TEXT = (
    "actual_package_sha256",
    "expected_package_sha256",
    "member_sha256:",
    "member_name:",
    "member_path:",
    "package_name:",
    "candidate_label:",
    "candidate_label_hash:",
    "sheet_name:",
    "raw_value:",
    "normalized_value:",
    "source_header_text:",
    "cell_value:",
    "row_value:",
    "business_value:",
    "bank_statement:",
    "contract_full_text:",
    "salary_detail:",
    "tax_filing:",
    "connector_token:",
    "connector_password:",
    "api_key:",
    "private_key:",
    "-----" "BEGIN",
    "s" "k-",
)
FORBIDDEN_TRACKED_SUFFIXES = (".zip", ".xlsx", ".xls", ".xlsm", ".pdf", ".sqlite", ".sqlite3", ".db")


class ValidationError(Exception):
    pass


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ValidationError(f"missing JSON file: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValidationError(f"{path} must contain a JSON object")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise ValidationError(f"missing JSONL file: {path}")
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValidationError(f"{path} contains non-object JSONL row")
        records.append(value)
    return records


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


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def walk_public(value: Any, errors: list[str], path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_PUBLIC_KEYS:
                errors.append(f"forbidden public key {key!r} at {path}")
            walk_public(child, errors, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            walk_public(child, errors, f"{path}[{index}]")


def check_public_safe_file(path: Path, errors: list[str]) -> None:
    require(path.exists(), f"missing evidence file: {path}", errors)
    if not path.exists():
        return
    require(path.suffix.lower() not in FORBIDDEN_TRACKED_SUFFIXES, f"forbidden evidence extension: {path}", errors)
    if path.suffix.lower() in {".md", ".json", ".jsonl", ".csv", ".yaml", ".yml"}:
        text = path.read_text(encoding="utf-8", errors="ignore")
        lower = text.lower()
        for forbidden in FORBIDDEN_PUBLIC_TEXT:
            require(forbidden.lower() not in lower, f"forbidden public text {forbidden!r} in {path}", errors)


def validate_v014_s05_p2_field_golden_baseline(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []
    manifest = read_json(manifest_path)
    contracts_payload = read_json(PUBLIC_FIELD_CONTRACTS_PATH)
    candidates = read_jsonl(PUBLIC_FIELD_CANDIDATES_PATH)
    s05_p1 = validate_v014_s05_p1_a0_file_registration()
    owner = validate_owner_decision()

    for public_value in (manifest, contracts_payload, candidates):
        walk_public(public_value, errors)

    require(manifest.get("schema_version") == SCHEMA_VERSION, "schema mismatch", errors)
    require(manifest.get("project_id") == "KMFA", "project_id mismatch", errors)
    require(manifest.get("version") == "0.1.4", "version mismatch", errors)
    require(manifest.get("stage_id") == "S05", "stage_id must be S05", errors)
    require(manifest.get("phase_id") == "S05-P2", "phase_id must be S05-P2", errors)
    require(
        manifest.get("phase_scope") == "v014_s05_p2_field_golden_baseline_only",
        "phase scope mismatch",
        errors,
    )
    require(manifest.get("task_id") == TASK_ID, "task id mismatch", errors)
    require(manifest.get("acceptance_id") == ACCEPTANCE_ID, "acceptance id mismatch", errors)
    require(
        manifest.get("status") == "completed_validated_local_only_no_go_upload_deferred_field_candidates_public_safe",
        "status mismatch",
        errors,
    )
    require(manifest.get("completed_task_ids") == ["S05P2T01", "S05P2T02", "S05P2T03"], "task ids mismatch", errors)

    require(s05_p1.get("phase_id") == "S05-P1", "S05-P1 dependency phase mismatch", errors)
    require(s05_p1.get("github_upload_performed") is False, "S05-P1 upload boundary mismatch", errors)
    require(s05_p1.get("next_recommended_phase") == "S05-P2", "S05-P1 next phase mismatch", errors)
    require(manifest.get("s05_p1_dependency_validated") is True, "S05-P1 dependency flag must be true", errors)

    require(contracts_payload.get("schema_version") == "kmfa.v014_s05_p2_field_contracts.v1", "contract schema mismatch", errors)
    require(contracts_payload.get("contract_count") == 5, "contract count mismatch", errors)
    contracts = contracts_payload.get("contracts")
    require(isinstance(contracts, list) and len(contracts) == 5, "contracts must contain five rows", errors)
    if isinstance(contracts, list):
        roles = [contract.get("field_role") for contract in contracts]
        require(tuple(roles) == FIELD_CONTRACT_ROLES, "field contract roles mismatch", errors)
        for index, contract in enumerate(contracts, start=1):
            require(
                contract.get("field_contract_ref") == f"V014-S05P2-FIELD-CONTRACT-{index:03d}",
                "field contract ref order mismatch",
                errors,
            )
            require(contract.get("source_header_plaintext_committed") is False, "contract plaintext leak flag mismatch", errors)
            require(contract.get("source_locator_publication_allowed") is False, "contract locator flag mismatch", errors)
            require(contract.get("source_value_publication_allowed") is False, "contract source value flag mismatch", errors)
            require(
                contract.get("normalized_value_publication_allowed") is False,
                "contract normalized value flag mismatch",
                errors,
            )
            require(contract.get("q5_allowed_in_s05p2") is False, "contract Q5 flag mismatch", errors)

    summary = manifest.get("field_candidate_summary", {})
    expected_summary = {
        "a0_project_candidate_count": 9,
        "required_field_contract_count": 5,
        "field_candidate_count": 45,
        "pdf_field_candidate_count": 40,
        "excel_field_candidate_count": 5,
        "source_anchor_recorded_private_only_count": 40,
        "source_anchor_pending_or_downgraded_count": 5,
        "private_value_hash_recorded_count": 40,
        "private_value_hash_pending_or_downgraded_count": 5,
        "q3_field_candidate_count": 45,
        "q4_human_confirmed_count": 0,
        "q5_calculation_baseline_allowed_count": 0,
        "q5_formal_report_allowed_count": 0,
        "owner_downgraded_excel_candidate_count": 1,
        "owner_downgraded_excel_field_count": 5,
        "public_source_or_normalized_value_committed_count": 0,
        "public_source_header_plaintext_committed_count": 0,
        "public_sheet_name_committed_count": 0,
        "public_row_or_cell_value_committed_count": 0,
        "source_format_counts": {"pdf": 40, "xlsx": 5},
    }
    for key, expected in expected_summary.items():
        require(summary.get(key) == expected, f"field summary {key} mismatch", errors)

    require(len(candidates) == 45, "public field candidates must contain 45 rows", errors)
    candidate_refs = {record.get("candidate_public_ref") for record in candidates}
    require(candidate_refs == {f"V014-A0-CAND-{index:03d}" for index in range(1, 10)}, "candidate refs mismatch", errors)
    field_refs = {record.get("field_contract_ref") for record in candidates}
    require(field_refs == {f"V014-S05P2-FIELD-CONTRACT-{index:03d}" for index in range(1, 6)}, "field refs mismatch", errors)
    pdf_rows = [record for record in candidates if record.get("source_file_format") == "pdf"]
    excel_rows = [record for record in candidates if record.get("source_file_format") == "xlsx"]
    require(len(pdf_rows) == 40, "PDF field candidate count mismatch", errors)
    require(len(excel_rows) == 5, "Excel field candidate count mismatch", errors)
    for index, record in enumerate(candidates, start=1):
        require(
            record.get("field_candidate_public_ref") == f"V014-S05P2-FIELD-CAND-{index:03d}",
            "field candidate ref order mismatch",
            errors,
        )
        require(record.get("field_role") in FIELD_CONTRACT_ROLES, "field role mismatch", errors)
        require(
            record.get("field_role_status") == "canonical_contract_role_not_raw_header_text",
            "field role status mismatch",
            errors,
        )
        require(record.get("source_locator_status") == "private_only_not_committed", "locator status mismatch", errors)
        require(
            record.get("page_sheet_cell_status") == "private_only_not_committed",
            "page sheet cell status mismatch",
            errors,
        )
        require(record.get("source_value_status") == "private_only_not_committed", "source value status mismatch", errors)
        require(
            record.get("normalized_value_status") == "private_only_not_committed",
            "normalized value status mismatch",
            errors,
        )
        require(record.get("machine_candidate_quality_grade") == "Q3", "candidate quality mismatch", errors)
        for key in (
            "q4_human_confirmed",
            "q5_calculation_baseline_allowed",
            "q5_formal_report_allowed",
            "raw_file_committed",
            "raw_filename_committed",
            "raw_hash_committed",
            "source_header_plaintext_committed",
            "sheet_name_committed",
            "zip_member_name_committed",
            "row_or_cell_value_committed",
            "source_or_normalized_values_committed",
            "business_value_committed",
        ):
            require(record.get(key) is False, f"candidate {key} must be false", errors)
    for record in pdf_rows:
        require(record.get("source_anchor_status") == "recorded_private_only", "PDF source anchor mismatch", errors)
        require(record.get("private_value_hash_status") == "recorded_private_only", "PDF private hash mismatch", errors)
        require(record.get("excel_owner_downgrade_applied") is False, "PDF downgrade flag mismatch", errors)
        require(record.get("cross_source_support_only") is False, "PDF support role mismatch", errors)
    for record in excel_rows:
        require(record.get("source_public_file_ref") == "V014-A0-FILE-008", "Excel public file ref mismatch", errors)
        require(record.get("source_anchor_status") == "pending_downgraded", "Excel source anchor mismatch", errors)
        require(record.get("private_value_hash_status") == "pending_downgraded", "Excel private hash mismatch", errors)
        require(record.get("excel_owner_downgrade_applied") is True, "Excel downgrade flag mismatch", errors)
        require(record.get("cross_source_support_only") is True, "Excel support role mismatch", errors)

    owner_summary = manifest.get("owner_decision_summary", {})
    require(owner_summary.get("owner_packet_status") == owner["owner_packet_status"], "owner packet status mismatch", errors)
    require(owner_summary.get("owner_allowed_decision_count") == 3, "owner allowed decision count mismatch", errors)
    require(owner_summary.get("owner_template_count") == 3, "owner template count mismatch", errors)
    require(owner_summary.get("active_decision_present") is True, "active decision must be present", errors)
    require(owner_summary.get("active_actor_role_validated") is True, "active actor role must be validated", errors)
    require(owner_summary.get("active_decision_code") == "downgrade_to_cross_source_support", "active decision mismatch", errors)
    require(owner_summary.get("active_decision_public_safe") is True, "active decision public-safe mismatch", errors)
    require(
        owner_summary.get("active_decision_raw_or_plaintext_values_included") is False,
        "active decision raw/plaintext flag mismatch",
        errors,
    )
    require(owner_summary.get("active_preview_status") == "ready", "active preview status mismatch", errors)
    require(owner_summary.get("active_preview_candidate_role") == "cross_source_support_only", "active preview role mismatch", errors)
    require(owner_summary.get("active_preview_q5_exclusion_confirmed") is True, "active preview q5 mismatch", errors)

    gate = manifest.get("completion_gate", {})
    require(gate.get("ready") is True, "completion gate must be ready", errors)
    require(gate.get("mode") == "owner_downgrade_to_cross_source_support", "completion gate mode mismatch", errors)
    require(gate.get("reason") == "active_owner_or_authorized_decision_resolves_excel_candidate", "completion reason mismatch", errors)
    require(gate.get("pending_fields") == 5, "completion pending fields mismatch", errors)
    require(gate.get("q4_confirmation_claimed") is False, "Q4 must not be claimed", errors)
    require(gate.get("q5_baseline_claimed") is False, "Q5 must not be claimed", errors)
    require(gate.get("stage5_review_claimed") is False, "Stage 5 review must not be claimed", errors)

    scope = manifest.get("phase_scope_controls", {})
    require(scope.get("current_phase_only") is True, "current_phase_only must be true", errors)
    require(scope.get("field_level_golden_baseline_performed") is True, "field baseline flag must be true", errors)
    require(scope.get("s05_p2_performed") is True, "S05-P2 flag must be true", errors)
    for key in PHASE_SCOPE_FALSE_KEYS:
        require(scope.get(key) is False, f"phase_scope_controls.{key} must be false", errors)

    boundary = manifest.get("raw_data_boundary", {})
    require(boundary.get("raw_inbox_path") == str(RAW_INBOX), "raw inbox path mismatch", errors)
    for key in BOUNDARY_FALSE_KEYS:
        require(boundary.get(key) is False, f"raw_data_boundary.{key} must be false", errors)

    for safety in (manifest.get("public_repo_safety", {}), contracts_payload.get("public_repo_safety", {})):
        for key in PUBLIC_FALSE_KEYS:
            require(safety.get(key) is False, f"public_repo_safety.{key} must be false", errors)

    release = manifest.get("release_state", {})
    require(release.get("current_data_quality_grade") == "Q3", "data quality grade must be Q3", errors)
    require(release.get("current_report_grade") == "D", "report grade must be D", errors)
    require(release.get("current_go_no_go") == "NO_GO", "Go/No-Go must be NO_GO", errors)
    for key in (
        "delivery_allowed",
        "formal_report_allowed",
        "business_decision_basis_allowed",
        "business_execution_allowed",
        "github_main_upload_allowed",
    ):
        require(release.get(key) is False, f"release_state.{key} must be false", errors)
    require(manifest.get("github_upload_performed") is False, "GitHub upload must be false", errors)
    require(
        manifest.get("github_upload_status") == "not_uploaded_deferred_until_v014_stage1_18_complete",
        "GitHub upload status mismatch",
        errors,
    )
    require(manifest.get("next_recommended_phase") == "S05-P3", "next phase mismatch", errors)
    require("Stage 1-18" in manifest.get("next_phase_instruction", ""), "next instruction must preserve upload deferral", errors)
    require("Stage 5 review" in manifest.get("next_phase_instruction", ""), "next instruction must block stage review", errors)

    for ref in manifest.get("s05_p1_dependency_refs", []):
        check_public_safe_file(Path(ref), errors)
    for ref in manifest.get("evidence_refs", []):
        check_public_safe_file(Path(ref), errors)
    for path in (
        REPORT_PATH,
        TEST_RESULTS_PATH,
        RISK_REGISTER_PATH,
        ROLLBACK_PATH,
        MANIFEST_PATH,
        PUBLIC_FIELD_CONTRACTS_PATH,
        PUBLIC_FIELD_CANDIDATES_PATH,
    ):
        check_public_safe_file(path, errors)

    tracked_files = git_output(["ls-files", "KMFA"]).splitlines()
    forbidden_tracked = [
        path for path in tracked_files if path.lower().endswith(FORBIDDEN_TRACKED_SUFFIXES) or ".codex_private_runtime/" in path
    ]
    require(not forbidden_tracked, f"forbidden tracked raw/private artifacts: {forbidden_tracked}", errors)
    require("codex/kmfa" in git_output(["status", "--short", "--branch"]), "git status must be on codex/kmfa", errors)

    if errors:
        raise ValidationError("\n".join(f"- {error}" for error in errors))
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.4 S05-P2 field golden baseline evidence.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args(argv)
    try:
        manifest = validate_v014_s05_p2_field_golden_baseline(args.manifest)
    except ValidationError as exc:
        print("FAIL: KMFA v0.1.4 S05-P2 field golden baseline validation failed")
        print(exc)
        return 1
    summary = manifest["field_candidate_summary"]
    print(
        "PASS: KMFA v0.1.4 S05-P2 field golden baseline validated "
        f"(field_candidates={summary['field_candidate_count']}, "
        f"anchor_recorded={summary['source_anchor_recorded_private_only_count']}, "
        f"downgraded={summary['owner_downgraded_excel_field_count']}, "
        f"q4={summary['q4_human_confirmed_count']}, "
        f"q5={summary['q5_calculation_baseline_allowed_count']}, "
        f"github_upload={str(manifest['github_upload_performed']).lower()})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
