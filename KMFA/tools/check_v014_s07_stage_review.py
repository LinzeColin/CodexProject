#!/usr/bin/env python3
"""Validate KMFA v0.1.4 Stage 7 review evidence."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from KMFA.tools.check_v014_s07_p1_finance_file_adapter import validate_v014_s07_p1_finance_file_adapter
from KMFA.tools.check_v014_s07_p2_wps_file_adapter import validate_v014_s07_p2_wps_file_adapter
from KMFA.tools.check_v014_s07_p3_redcircle_postponement import validate_v014_s07_p3_redcircle_postponement
from KMFA.tools.v014_s07_stage_review import (
    ACCEPTANCE_ID,
    MANIFEST_PATH,
    NEXT_INSTRUCTION,
    NEXT_PHASE,
    PHASE_MANIFESTS,
    REPORT_PATH,
    REVIEW_SCOPE,
    RISK_REGISTER_PATH,
    ROLLBACK_PATH,
    SCHEMA_VERSION,
    TASK_ID,
    TEST_RESULTS_PATH,
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
    "canonical_field_keys",
}
FORBIDDEN_TEXT = (
    "raw_value:",
    "normalized_value:",
    "source_header_text:",
    "field_key:",
    "field_label:",
    "file_hash:",
    "sheet_name:",
    "member_name:",
    "member_path:",
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
RELEASE_FALSE_KEYS = (
    "delivery_allowed",
    "formal_report_allowed",
    "business_decision_basis_allowed",
    "business_execution_allowed",
    "github_main_upload_allowed",
)
PUBLIC_SAFETY_FALSE_KEYS = (
    "raw_business_data_committed",
    "raw_archive_or_workbook_committed",
    "raw_document_committed",
    "private_table_or_database_committed",
    "credentials_committed",
    "connector_secret_committed",
    "private_schema_text_committed",
    "field_plaintext_committed",
    "source_header_plaintext_committed",
    "raw_file_identifiers_committed",
    "raw_content_identifiers_committed",
    "private_record_content_committed",
    "business_content_committed",
)
RAW_REVIEW_FALSE_KEYS = (
    "raw_inbox_read_by_this_review",
    "raw_inbox_listed_by_this_review",
    "raw_inbox_inventory_by_this_review",
    "raw_inbox_stat_by_this_review",
    "raw_inbox_hashed_by_this_review",
    "raw_inbox_modified_by_this_review",
    "raw_inbox_deleted_by_this_review",
    "raw_inbox_moved_by_this_review",
    "raw_inbox_renamed_by_this_review",
    "raw_inbox_overwritten_by_this_review",
    "raw_inbox_written_by_this_review",
    "raw_inbox_mutated_by_this_review",
    "s07_p1_raw_inbox_read_by_phase",
    "s07_p1_raw_inbox_mutated_by_phase",
    "s07_p2_raw_inbox_read_by_phase",
    "s07_p2_raw_inbox_mutated_by_phase",
    "s07_p3_raw_inbox_read_by_phase",
    "s07_p3_raw_inbox_listed_by_phase",
    "s07_p3_raw_inbox_stat_by_phase",
    "s07_p3_raw_inbox_hashed_by_phase",
    "s07_p3_raw_inbox_mutated_by_phase",
)
VALIDATION_KEYS = (
    "py_compile",
    "s07_p1_validator",
    "s07_p2_validator",
    "s07_p3_validator",
    "legacy_s07_p1_validator",
    "legacy_s07_p1_unit",
    "legacy_s07_p2_validator",
    "legacy_s07_p2_unit",
    "legacy_s07_p3_validator",
    "legacy_s07_p3_unit",
    "stage_review_validator",
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
    "public_stage7_semantic_scan",
    "diff_check",
)
REQUIRED_HARD_BLOCKS = (
    "raw_data_mutation_forbidden",
    "raw_value_publication_forbidden",
    "field_header_plaintext_publication_forbidden",
    "adapter_candidates_remain_structural_or_reserved",
    "q5_forbidden_until_downstream_value_reconciliation",
    "formal_report_release_blocked",
    "lineage_full_check_not_performed",
    "raw_value_matching_not_performed",
    "redcircle_automatic_connector_blocked",
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


def validate_v014_s07_stage_review(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []
    manifest = read_json(manifest_path)
    p1 = validate_v014_s07_p1_finance_file_adapter()
    p2 = validate_v014_s07_p2_wps_file_adapter()
    p3 = validate_v014_s07_p3_redcircle_postponement()
    walk_forbidden_keys(manifest, errors)

    require(manifest.get("schema_version") == SCHEMA_VERSION, "schema mismatch", errors)
    require(manifest.get("project_id") == "KMFA", "project_id mismatch", errors)
    require(manifest.get("version") == "0.1.4", "version mismatch", errors)
    require(manifest.get("stage_id") == "S07", "stage_id must be S07", errors)
    require(manifest.get("review_id") == TASK_ID, "review id mismatch", errors)
    require(manifest.get("task_id") == TASK_ID, "task id mismatch", errors)
    require(manifest.get("acceptance_id") == ACCEPTANCE_ID, "acceptance id mismatch", errors)
    require(manifest.get("review_scope") == REVIEW_SCOPE, "review scope mismatch", errors)
    require(
        manifest.get("status") == "review_passed_local_only_no_go_upload_deferred_until_v014_stage1_18_complete",
        "status mismatch",
        errors,
    )
    require(manifest.get("stage_review_performed") is True, "stage review must be true", errors)
    require(manifest.get("s08_p1_performed") is False, "S08-P1 must not be performed", errors)
    require(manifest.get("github_upload_performed") is False, "GitHub upload must not be performed", errors)
    require(
        manifest.get("github_upload_status") == "not_uploaded_deferred_until_v014_stage1_18_complete",
        "GitHub upload status mismatch",
        errors,
    )
    for key in (
        "app_reinstall_performed",
        "raw_content_matching_performed",
        "lineage_full_check_performed",
        "formal_report_performed",
        "live_connector_called",
        "opme_deep_coupling_performed",
        "business_execution_performed",
    ):
        require(manifest.get(key) is False, f"{key} must be false", errors)

    require(manifest.get("phase_count") == 3, "phase count mismatch", errors)
    require(
        manifest.get("phase_results") == {"S07-P1": "PASS", "S07-P2": "PASS", "S07-P3": "PASS"},
        "phase results mismatch",
        errors,
    )
    require(p1.get("phase_id") == "S07-P1", "S07-P1 validator did not return S07-P1", errors)
    require(p2.get("phase_id") == "S07-P2", "S07-P2 validator did not return S07-P2", errors)
    require(p3.get("phase_id") == "S07-P3", "S07-P3 validator did not return S07-P3", errors)
    for key in ("s07_p1_dependency_validated", "s07_p2_dependency_validated", "s07_p3_dependency_validated"):
        require(manifest.get(key) is True, f"{key} must be true", errors)

    reviewed = manifest.get("reviewed_phase_manifests", {})
    for phase, ref in PHASE_MANIFESTS.items():
        require(reviewed.get(phase) == ref, f"{phase} manifest ref mismatch", errors)
        require(Path(ref).exists(), f"missing phase manifest: {ref}", errors)

    require(manifest.get("open_review_finding_count") == 0, "open findings must be 0", errors)
    require(manifest.get("fixed_review_finding_count") == 1, "fixed findings must be 1", errors)
    findings = manifest.get("review_findings", [])
    require(isinstance(findings, list) and len(findings) == 1, "review findings must contain one fixed finding", errors)
    if isinstance(findings, list) and findings:
        require(findings[0].get("finding_id") == "KMFA-V014-S07-STAGE-REVIEW-FIX-001", "finding id mismatch", errors)
        require(findings[0].get("status") == "fixed", "finding must be fixed", errors)

    gate = manifest.get("stage_gate", {})
    expected_gate = {
        "finance_source_category_count": 9,
        "finance_field_candidate_count": 45,
        "finance_hash_only_field_candidate_count": 45,
        "finance_field_report_count": 9,
        "finance_source_header_fingerprint_count": 45,
        "wps_source_export_type_count": 4,
        "wps_field_mapping_count": 20,
        "wps_hash_only_field_mapping_count": 20,
        "wps_field_report_count": 4,
        "wps_conversion_guidance_count": 4,
        "wps_mapping_rule_version_count": 1,
        "wps_source_header_fingerprint_count": 20,
        "wps_native_conversion_required_count": 4,
        "redcircle_export_type_count": 4,
        "redcircle_reserved_template_count": 4,
        "redcircle_registry_source_count": 4,
        "redcircle_template_contract_hash_count": 4,
        "redcircle_source_private_ref_count": 4,
        "redcircle_connector_policy_count": 1,
        "redcircle_rollback_plan_count": 4,
        "redcircle_automatic_connector_allowed_count": 0,
        "redcircle_d15_automatic_connector_allowed": False,
        "redcircle_read_only_required_count": 4,
        "redcircle_hash_retention_required_count": 4,
        "redcircle_rollback_plan_required_count": 4,
        "redcircle_manual_approval_required_count": 4,
        "total_public_safe_source_registry_count": 17,
        "total_structural_mapping_count": 65,
        "q4_human_confirmed_count": 0,
        "q5_calculation_baseline_allowed_count": 0,
        "formal_report_allowed_count": 0,
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "release_permission": "blocked",
    }
    for key, value in expected_gate.items():
        require(gate.get(key) == value, f"stage_gate.{key} mismatch", errors)
    require(gate.get("finance_field_candidate_count") == p1.get("field_candidate_count"), "P1 field count mismatch", errors)
    require(gate.get("wps_field_mapping_count") == p2.get("field_mapping_count"), "P2 mapping count mismatch", errors)
    require(gate.get("redcircle_reserved_template_count") == p3.get("reserved_template_count"), "P3 template count mismatch", errors)

    phase_summary = manifest.get("phase_summary", {})
    for phase, validator_result in (("S07-P1", p1), ("S07-P2", p2), ("S07-P3", p3)):
        summary = phase_summary.get(phase, {})
        require(summary.get("github_upload_performed") is False, f"{phase} upload flag mismatch", errors)
        require(summary.get("raw_inbox_read_performed") is False, f"{phase} raw read flag mismatch", errors)
        require(summary.get("stage7_review_performed") is False, f"{phase} phase review flag mismatch", errors)
        require(validator_result.get("github_upload_performed") is False, f"{phase} validator upload flag mismatch", errors)

    raw = manifest.get("raw_data_boundary", {})
    require(raw.get("raw_inbox_ref") == "operator-designated local raw/private inbox outside repository", "raw inbox ref mismatch", errors)
    for key in RAW_REVIEW_FALSE_KEYS:
        require(raw.get(key) is False, f"raw_data_boundary.{key} must be false", errors)

    safety = manifest.get("public_repo_safety", {})
    for key in PUBLIC_SAFETY_FALSE_KEYS:
        require(safety.get(key) is False, f"public_repo_safety.{key} must be false", errors)

    release = manifest.get("release_state", {})
    for key in RELEASE_FALSE_KEYS:
        require(release.get(key) is False, f"release_state.{key} must be false", errors)
    require(release.get("current_go_no_go") == "NO_GO", "Go/No-Go mismatch", errors)
    require(release.get("current_data_quality_grade") == "Q4", "data quality mismatch", errors)
    require(release.get("current_report_grade") == "D", "report grade mismatch", errors)
    require(release.get("release_permission") == "blocked", "release permission mismatch", errors)

    hard_blocks = manifest.get("hard_blocks", [])
    require(isinstance(hard_blocks, list), "hard_blocks must be a list", errors)
    for block in REQUIRED_HARD_BLOCKS:
        require(block in hard_blocks, f"missing hard block: {block}", errors)
    require(manifest.get("hard_block_count") == len(REQUIRED_HARD_BLOCKS), "hard block count mismatch", errors)

    validation = manifest.get("validation_summary", {})
    for key in VALIDATION_KEYS:
        require(validation.get(key) == "PASS", f"validation_summary.{key} must be PASS", errors)

    for ref in manifest.get("evidence_refs", []):
        check_public_safe_file(Path(ref), errors)
    for path in (MANIFEST_PATH, REPORT_PATH, TEST_RESULTS_PATH, RISK_REGISTER_PATH, ROLLBACK_PATH):
        check_public_safe_file(path, errors)

    reviewed_head = str(manifest.get("reviewed_head", ""))
    require(len(reviewed_head) == 40 and all(char in "0123456789abcdef" for char in reviewed_head), "reviewed_head mismatch", errors)
    require("codex/kmfa" in git_output(["status", "--short", "--branch"]), "branch must be codex/kmfa", errors)
    require(manifest.get("next_recommended_phase") == NEXT_PHASE, "next phase mismatch", errors)
    require(manifest.get("next_phase_instruction") == NEXT_INSTRUCTION, "next instruction mismatch", errors)

    if errors:
        raise ValidationError("\n".join(errors))
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.4 Stage 7 review evidence.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args(argv)
    try:
        result = validate_v014_s07_stage_review(args.manifest)
    except ValidationError as exc:
        print("FAIL: KMFA v0.1.4 Stage 7 review validation failed")
        print(exc)
        return 1
    gate = result["stage_gate"]
    print(
        "PASS: KMFA v0.1.4 Stage 7 review validated "
        f"(finance_candidates={gate['finance_field_candidate_count']}, "
        f"wps_mappings={gate['wps_field_mapping_count']}, "
        f"redcircle_templates={gate['redcircle_reserved_template_count']}, "
        f"q5_allowed={gate['q5_calculation_baseline_allowed_count']}, "
        "s08_p1=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
