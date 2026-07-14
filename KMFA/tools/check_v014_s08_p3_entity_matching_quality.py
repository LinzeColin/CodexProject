#!/usr/bin/env python3
"""Validate KMFA v0.1.4 S08-P3 entity matching quality evidence."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from KMFA.tools.v014_s08_p3_entity_matching_quality import (
    ACCEPTANCE_ID,
    MANIFEST_PATH,
    NEXT_INSTRUCTION,
    NEXT_PHASE,
    PHASE_SCOPE,
    REPORT_PATH,
    RISK_REGISTER_PATH,
    ROLLBACK_PATH,
    SCHEMA_VERSION,
    TASK_ID,
    TEST_RESULTS_PATH,
    validate_legacy_s08_p3_artifacts,
    validate_s08_p2_dependency,
)


FORBIDDEN_PUBLIC_SUFFIXES = (".zip", ".xlsx", ".xls", ".xlsm", ".pdf", ".sqlite", ".sqlite3", ".db")
RAW_INBOX_DIRECTORY_TOKEN = "KMFA" + "_MetaData"
LOCAL_DOWNLOADS_RAW_PATH_PATTERN = re.compile(r"/Users/[^\s\"'`]+/Downloads/[^\s\"'`]+")
STRICT_SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(?i)(password|passwd|secret|api_key|token)\s*=\s*[^\s,;]{8,}"),
)
FORBIDDEN_PUBLIC_KEYS = {
    "raw_value",
    "normalized_value",
    "original_value",
    "plaintext_value",
    "source_header_text",
    "field_key",
    "field_label",
    "file_hash",
    "sheet_name",
    "member_name",
    "member_path",
    "package_name",
    "business_value",
    "row_value",
    "cell_value",
    "plaintext_content",
    "full_file_text",
    "raw_file_bytes",
    "original_filename",
    "bank_account_number",
    "identity_document_number",
    "project_name_plaintext",
    "customer_name_plaintext",
    "counterparty_plaintext",
    "company_entity_plaintext",
}
FORBIDDEN_TEXT = (
    "raw_value:",
    "normalized_value:",
    "plaintext_value:",
    "source_header_text:",
    "field_key:",
    "field_label:",
    "file_hash:",
    "sheet_name:",
    "member_name:",
    "package_name:",
    "business_value:",
    "row_value:",
    "cell_value:",
    "bank_statement",
    "contract_full_text",
    "salary_detail",
    "tax_filing",
    "-----" "BEGIN",
    "s" "k-",
)
FALSE_BOUNDARY_KEYS = (
    "stage8_review_scope_included",
    "fact_layer_scope_included",
    "lineage_full_check_scope_included",
    "report_scope_included",
    "ui_scope_included",
    "external_connector_scope_included",
    "github_upload_scope_included",
    "app_reinstall_scope_included",
)
RELEASE_FALSE_KEYS = (
    "delivery_allowed",
    "formal_report_allowed",
    "business_decision_basis_allowed",
    "business_execution_allowed",
    "github_main_upload_allowed",
)
RAW_FALSE_KEYS = (
    "raw_inbox_read_by_this_phase",
    "raw_inbox_listed_by_this_phase",
    "raw_inbox_inventory_by_this_phase",
    "raw_inbox_stat_by_this_phase",
    "raw_inbox_hashed_by_this_phase",
    "raw_inbox_modified_by_this_phase",
    "raw_inbox_deleted_by_this_phase",
    "raw_inbox_moved_by_this_phase",
    "raw_inbox_renamed_by_this_phase",
    "raw_inbox_overwritten_by_this_phase",
    "raw_inbox_written_by_this_phase",
    "raw_inbox_mutated_by_this_phase",
)
PUBLIC_SAFETY_FALSE_KEYS = (
    "raw_business_data_committed",
    "raw_archive_or_workbook_committed",
    "raw_document_committed",
    "private_csv_committed",
    "private_table_or_database_committed",
    "credentials_committed",
    "connector_secret_committed",
    "field_plaintext_committed",
    "source_header_plaintext_committed",
    "raw_file_identifiers_committed",
    "raw_content_identifiers_committed",
    "private_record_content_committed",
    "business_content_committed",
    "entity_matching_plaintext_committed",
    "entity_matching_business_values_committed",
    "normalized_business_values_committed",
    "entity_matching_report_formal_report_committed",
)
VALIDATION_KEYS = (
    "py_compile",
    "s08_p2_dependency_validator",
    "legacy_s08_p3_generator",
    "legacy_s08_p3_validator",
    "legacy_s08_p3_unit",
    "v014_s08_p3_generator",
    "v014_s08_p3_validator",
    "focused_unit_test",
    "no_omission_check",
    "no_float_money_check",
    "governance_validator",
    "lean_governance_validator",
    "governance_sync_validator",
    "structured_parse",
    "ruby_yaml_parse",
    "raw_private_scan",
    "secret_scan",
    "public_s08_p3_semantic_scan",
    "diff_check",
)
REQUIRED_HARD_BLOCKS = (
    "raw_data_mutation_forbidden",
    "raw_value_publication_forbidden",
    "field_header_plaintext_publication_forbidden",
    "entity_matching_values_remain_hash_ref_only",
    "medium_high_risk_auto_merge_forbidden",
    "manual_review_queue_auto_merge_forbidden",
    "stage8_review_required_as_separate_run",
    "q5_forbidden_until_stage8_review_and_quality_evidence",
    "formal_report_release_blocked",
    "lineage_full_check_not_performed",
    "raw_value_matching_not_performed",
    "github_upload_deferred_until_v014_stage1_18_complete",
    "business_execution_blocked",
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


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def walk_forbidden_keys(value: Any, errors: list[str], path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_PUBLIC_KEYS:
                errors.append(f"forbidden public key {key!r} at {path}")
            walk_forbidden_keys(child, errors, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            walk_forbidden_keys(child, errors, f"{path}[{index}]")


def check_public_safe_file(path: Path, errors: list[str]) -> None:
    require(path.exists(), f"missing public-safe file: {path}", errors)
    if not path.exists():
        return
    require(path.suffix.lower() not in FORBIDDEN_PUBLIC_SUFFIXES, f"forbidden public extension: {path}", errors)
    if path.suffix.lower() not in {".md", ".json", ".jsonl", ".csv", ".yaml", ".yml"}:
        return
    text = path.read_text(encoding="utf-8", errors="ignore")
    lower = text.lower()
    for forbidden in FORBIDDEN_TEXT:
        require(forbidden.lower() not in lower, f"forbidden public text {forbidden!r} in {path}", errors)
    require(RAW_INBOX_DIRECTORY_TOKEN.lower() not in lower, f"forbidden raw inbox directory token in {path}", errors)
    require(LOCAL_DOWNLOADS_RAW_PATH_PATTERN.search(text) is None, f"forbidden local Downloads raw path in {path}", errors)
    for pattern in STRICT_SECRET_PATTERNS:
        require(pattern.search(text) is None, f"high-signal secret pattern in {path}: {pattern.pattern}", errors)


def validate_v014_s08_p3_entity_matching_quality(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []
    manifest = read_json(manifest_path)
    dependency = validate_s08_p2_dependency()
    legacy = validate_legacy_s08_p3_artifacts()
    walk_forbidden_keys(manifest, errors)

    require(manifest.get("schema_version") == SCHEMA_VERSION, "schema mismatch", errors)
    require(manifest.get("project_id") == "KMFA", "project_id mismatch", errors)
    require(manifest.get("version") == "0.1.4", "version mismatch", errors)
    require(manifest.get("stage_id") == "S08", "stage_id must be S08", errors)
    require(manifest.get("phase_id") == "S08-P3", "phase_id must be S08-P3", errors)
    require(manifest.get("task_id") == TASK_ID, "task id mismatch", errors)
    require(manifest.get("acceptance_id") == ACCEPTANCE_ID, "acceptance id mismatch", errors)
    require(manifest.get("phase_scope") == PHASE_SCOPE, "phase scope mismatch", errors)
    require(
        manifest.get("status") == "completed_validated_local_only_no_go_upload_deferred_entity_matching_quality",
        "status mismatch",
        errors,
    )
    require(dependency.get("phase_id") == "S08-P2", "S08-P2 dependency did not validate", errors)
    require(manifest.get("s08_p2_dependency_validated") is True, "S08-P2 dependency flag mismatch", errors)
    require(manifest.get("legacy_s08_p3_dependency_validated") is True, "legacy S08-P3 flag mismatch", errors)
    require(manifest.get("completed_task_ids") == ["S08P3T01", "S08P3T02", "S08P3T03"], "task ids mismatch", errors)

    progress = manifest.get("stage8_phase_progress", {})
    require(progress.get("completed_phase_count") == 3, "completed phase count mismatch", errors)
    require(progress.get("total_phase_count") == 3, "total phase count mismatch", errors)
    require(progress.get("derived_percent_bps") == 10000, "derived percent bps mismatch", errors)
    require(progress.get("derived_percent_label") == "100.00%", "derived percent label mismatch", errors)
    require(progress.get("s08_p1_performed") is True, "S08-P1 must be true", errors)
    require(progress.get("s08_p2_performed") is True, "S08-P2 must be true", errors)
    require(progress.get("s08_p3_performed") is True, "S08-P3 must be true", errors)
    require(progress.get("stage8_review_performed") is False, "Stage 8 review must be false", errors)

    summary = manifest.get("entity_matching_quality_summary", {})
    require(summary.get("scenario_count") == 4, "scenario count mismatch", errors)
    require(summary.get("quality_scenarios") == legacy["quality_scenarios"], "quality scenarios mismatch", errors)
    require(summary.get("quality_case_count") == 4, "quality case count mismatch", errors)
    require(summary.get("manual_review_queue_count") == 3, "manual review queue count mismatch", errors)
    require(summary.get("manual_review_case_count") == 3, "manual review case count mismatch", errors)
    require(summary.get("medium_high_risk_case_count") == 3, "medium/high risk count mismatch", errors)
    require(summary.get("low_risk_case_count") == 1, "low risk count mismatch", errors)
    require(summary.get("quality_control_passed_count") == 1, "quality pass count mismatch", errors)
    require(summary.get("entity_matching_report_count") == 1, "entity matching report count mismatch", errors)
    require(summary.get("risk_summary", {}).get("high") == 2, "high risk count mismatch", errors)
    require(summary.get("risk_summary", {}).get("medium") == 1, "medium risk count mismatch", errors)
    require(summary.get("risk_summary", {}).get("low") == 1, "low risk count mismatch", errors)
    require(summary.get("auto_merge_allowed_case_count") == 1, "auto merge case count mismatch", errors)
    require(
        summary.get("auto_merge_allowed_for_review_queue_count") == 0,
        "review queue auto merge count mismatch",
        errors,
    )
    for key in (
        "scenario_count",
        "quality_case_count",
        "manual_review_queue_count",
        "manual_review_case_count",
        "medium_high_risk_case_count",
        "low_risk_case_count",
        "quality_control_passed_count",
        "entity_matching_report_count",
        "risk_summary",
        "auto_merge_allowed_case_count",
        "auto_merge_allowed_for_review_queue_count",
    ):
        require(summary.get(key) == legacy.get(key), f"legacy summary mismatch for {key}", errors)

    policy = manifest.get("entity_matching_quality_policy", {})
    require(policy.get("scenario_coverage") == legacy["quality_scenarios"], "scenario coverage mismatch", errors)
    require(policy.get("medium_high_risk_requires_manual_review") is True, "manual review policy mismatch", errors)
    require(policy.get("manual_review_queue_auto_merge_allowed") is False, "queue auto merge policy mismatch", errors)
    require(policy.get("entity_matching_values_hash_ref_only") is True, "hash/ref-only policy mismatch", errors)
    require(policy.get("quality_report_is_formal_report") is False, "formal report policy mismatch", errors)
    require(policy.get("quality_gate_false_count") == legacy["quality_gate_false_count"], "quality false count mismatch", errors)
    require(policy.get("public_safety_false_count") == legacy["public_safety_false_count"], "public false count mismatch", errors)

    boundaries = manifest.get("phase_boundaries", {})
    require(boundaries.get("s08_p2_dependency_validated") is True, "S08-P2 boundary mismatch", errors)
    require(boundaries.get("s08_p3_scope_included") is True, "S08-P3 scope mismatch", errors)
    for key in FALSE_BOUNDARY_KEYS:
        require(boundaries.get(key) is False, f"phase_boundaries.{key} must be false", errors)

    release = manifest.get("release_state", {})
    require(release.get("current_go_no_go") == "NO_GO", "Go/No-Go mismatch", errors)
    require(release.get("current_data_quality_grade") == "Q4", "data quality mismatch", errors)
    require(release.get("current_report_grade") == "D", "report grade mismatch", errors)
    require(release.get("release_permission") == "blocked", "release permission mismatch", errors)
    for key in RELEASE_FALSE_KEYS:
        require(release.get(key) is False, f"release_state.{key} must be false", errors)

    upload = manifest.get("github_upload", {})
    require(upload.get("github_upload_ready_next_gate") is False, "upload next gate must be false", errors)
    require(upload.get("github_upload_performed") is False, "upload performed must be false", errors)
    require(upload.get("github_upload_deferred_until_v014_stage1_18_complete") is True, "upload deferral mismatch", errors)
    require(
        upload.get("github_upload_status") == "not_uploaded_deferred_until_v014_stage1_18_complete",
        "upload status mismatch",
        errors,
    )

    raw = manifest.get("raw_data_boundary", {})
    require(raw.get("raw_inbox_ref") == "operator-designated raw/private inbox outside repository", "raw ref mismatch", errors)
    for key in RAW_FALSE_KEYS:
        require(raw.get(key) is False, f"raw_data_boundary.{key} must be false", errors)

    safety = manifest.get("public_repo_safety", {})
    for key in PUBLIC_SAFETY_FALSE_KEYS:
        require(safety.get(key) is False, f"public_repo_safety.{key} must be false", errors)

    hard_blocks = manifest.get("hard_blocks", [])
    require(isinstance(hard_blocks, list), "hard_blocks must be list", errors)
    for block in REQUIRED_HARD_BLOCKS:
        require(block in hard_blocks, f"missing hard block: {block}", errors)
    require(manifest.get("hard_block_count") == len(REQUIRED_HARD_BLOCKS), "hard block count mismatch", errors)

    validation = manifest.get("validation_summary", {})
    for key in VALIDATION_KEYS:
        require(validation.get(key) == "PASS", f"validation_summary.{key} must be PASS", errors)

    artifact_refs = manifest.get("artifact_refs", {})
    for key in (
        "legacy_manifest",
        "legacy_cases",
        "legacy_review_queue",
        "legacy_report",
        "legacy_stage_manifest",
        "manifest",
        "report",
        "test_results",
        "risk_register",
        "rollback_plan",
        "generator",
        "validator",
        "unit_test",
    ):
        require(Path(artifact_refs.get(key, "")).exists(), f"missing artifact ref: {key}", errors)

    for ref in manifest.get("evidence_refs", []):
        check_public_safe_file(Path(ref), errors)
    for path in (MANIFEST_PATH, REPORT_PATH, TEST_RESULTS_PATH, RISK_REGISTER_PATH, ROLLBACK_PATH):
        check_public_safe_file(path, errors)

    reviewed_head = str(manifest.get("reviewed_head", ""))
    require(len(reviewed_head) == 40 and all(char in "0123456789abcdef" for char in reviewed_head), "reviewed_head mismatch", errors)
    require(manifest.get("branch") == git_output(["branch", "--show-current"]), "branch mismatch", errors)
    require(manifest.get("remote") == git_output(["remote", "get-url", "origin"]), "remote mismatch", errors)
    require(manifest.get("next_recommended_phase") == NEXT_PHASE, "next phase mismatch", errors)
    require(manifest.get("next_phase_instruction") == NEXT_INSTRUCTION, "next instruction mismatch", errors)

    if errors:
        raise ValidationError("\n".join(errors))
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.4 S08-P3 entity matching quality evidence.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args(argv)
    try:
        result = validate_v014_s08_p3_entity_matching_quality(args.manifest)
    except ValidationError as exc:
        print("FAIL: KMFA v0.1.4 S08-P3 entity matching quality validation failed")
        print(exc)
        return 1
    summary = result["entity_matching_quality_summary"]
    print(
        "PASS: KMFA v0.1.4 S08-P3 entity matching quality validated "
        f"(scenarios={summary['scenario_count']}, quality_cases={summary['quality_case_count']}, "
        f"manual_review_queue={summary['manual_review_queue_count']}, "
        "stage8_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
