#!/usr/bin/env python3
"""Validate KMFA v0.1.4 Stage 11 review evidence."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from KMFA.tools.check_s11_stage_review import validate_stage_review as validate_legacy_stage11_review
from KMFA.tools.check_v014_s11_p1_home_navigation import validate_v014_s11_p1_home_navigation
from KMFA.tools.check_v014_s11_p2_source_check_board import validate_v014_s11_p2_source_check_board
from KMFA.tools.check_v014_s11_p3_project_cost_page import validate_v014_s11_p3_project_cost_page
from KMFA.tools.v014_s11_stage_review import (
    ACCEPTANCE_ID,
    LEGACY_STAGE11_REVIEW_MANIFEST_PATH,
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


PUBLIC_SAFETY_FALSE_KEYS = (
    "protected_source_payload_committed",
    "zip_committed",
    "excel_workbook_committed",
    "wps_native_file_committed",
    "redcircle_native_file_committed",
    "raw_or_private_csv_committed",
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
    "business_amount_values_committed",
    "project_or_customer_plaintext_committed",
    "formal_report_committed",
    "spreadsheet_workbook_committed",
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
)
RAW_REVIEW_TRUE_KEYS = (
    "s11_p1_raw_inbox_all_false",
    "s11_p2_raw_inbox_all_false",
    "s11_p3_raw_inbox_all_false",
)
RELEASE_FALSE_KEYS = (
    "delivery_allowed",
    "formal_report_allowed",
    "business_decision_basis_allowed",
    "business_execution_allowed",
    "github_main_upload_allowed",
)
VALIDATION_KEYS = (
    "py_compile",
    "s11_p1_validator",
    "s11_p2_validator",
    "s11_p3_validator",
    "legacy_s11_stage_review_validator",
    "stage_review_validator",
    "focused_unit_test",
    "no_omission_check",
    "no_float_money_check",
    "governance_validator",
    "lean_governance_validator",
    "governance_sync_validator",
    "structured_parse",
    "ruby_yaml_parse",
    "raw_private_suffix_scan",
    "strict_secret_token_scan",
    "public_stage11_semantic_scan",
    "diff_check",
)
REQUIRED_HARD_BLOCKS = (
    "report_grade_d_only",
    "pending_reconciliation_blocks_formal_report",
    "quality_grade_bypass_forbidden",
    "raw_data_mutation_forbidden",
    "raw_value_publication_forbidden",
    "field_header_plaintext_publication_forbidden",
    "formal_report_release_blocked",
    "business_decision_basis_blocked",
    "s12_p1_not_performed",
    "lineage_full_check_not_performed",
    "raw_value_matching_not_performed",
    "github_upload_deferred_until_v014_stage1_18_complete",
    "app_reinstall_not_performed",
    "business_execution_blocked",
)
FORBIDDEN_PUBLIC_TEXT = (
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
    "amount_cents:",
    "amount_yuan:",
    "sheet_name:",
    "row_value:",
    "cell_value:",
    "business_data:",
    "bank_statement",
    "contract_full_text",
    "salary_detail",
    "tax_filing",
    "connector_" + "token:",
    "connector_" + "password:",
    "api" + "_key:",
    "private" + "_key:",
    "-----" "BEGIN",
    "s" "k-",
    "project_name_plaintext",
    "customer_name_plaintext",
    "counterparty_plaintext",
    "company_entity_plaintext",
    "account_number:",
    "KMFA" "_MetaData",
    "/Users/linzezhang/Downloads",
)
STRICT_SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(?i)(password|passwd|secret|api" + r"_key|token)\s*=\s*[^\s,;]{8,}"),
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


def check_public_evidence_text(path: Path, errors: list[str]) -> None:
    require(path.exists(), f"missing public evidence: {path}", errors)
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8", errors="ignore")
    lower = text.lower()
    for forbidden in FORBIDDEN_PUBLIC_TEXT:
        require(forbidden.lower() not in lower, f"forbidden public evidence text {forbidden!r} in {path}", errors)
    for pattern in STRICT_SECRET_PATTERNS:
        require(pattern.search(text) is None, f"secret-like token found in {path}: {pattern.pattern}", errors)


def validate_v014_s11_stage_review(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []
    manifest = read_json(manifest_path)
    p1 = validate_v014_s11_p1_home_navigation()
    p2 = validate_v014_s11_p2_source_check_board()
    p3 = validate_v014_s11_p3_project_cost_page()
    legacy_counts = validate_legacy_stage11_review()
    legacy_manifest = read_json(LEGACY_STAGE11_REVIEW_MANIFEST_PATH)

    require(manifest.get("schema_version") == SCHEMA_VERSION, "schema mismatch", errors)
    require(manifest.get("project_id") == "KMFA", "project_id mismatch", errors)
    require(manifest.get("version") == "0.1.4", "version mismatch", errors)
    require(manifest.get("stage_id") == "S11", "stage_id must be S11", errors)
    require(manifest.get("review_id") == TASK_ID, "review_id mismatch", errors)
    require(manifest.get("task_id") == TASK_ID, "task_id mismatch", errors)
    require(manifest.get("acceptance_id") == ACCEPTANCE_ID, "acceptance id mismatch", errors)
    require(manifest.get("review_scope") == REVIEW_SCOPE, "review scope mismatch", errors)
    require(
        manifest.get("status") == "review_passed_local_only_no_go_upload_deferred_until_v014_stage1_18_complete",
        "status mismatch",
        errors,
    )
    require(manifest.get("stage_review_performed") is True, "stage review must be performed", errors)
    require(manifest.get("s12_p1_performed") is False, "S12-P1 must not be performed", errors)
    require(manifest.get("github_upload_ready_next_gate") is False, "upload ready must stay false", errors)
    require(
        manifest.get("github_upload_deferred_until_v014_stage1_18_complete") is True,
        "upload defer flag mismatch",
        errors,
    )
    require(manifest.get("github_upload_performed") is False, "GitHub upload must not be performed", errors)
    require(
        manifest.get("github_upload_status") == "not_uploaded_deferred_until_v014_stage1_18_complete",
        "GitHub upload status mismatch",
        errors,
    )
    require(manifest.get("legacy_stage11_review_validated") is True, "legacy Stage 11 review flag mismatch", errors)
    require(manifest.get("legacy_stage11_review_manifest") == str(LEGACY_STAGE11_REVIEW_MANIFEST_PATH), "legacy manifest mismatch", errors)
    require(manifest.get("legacy_stage11_review_status") == "pass_upload_ready_local_only", "legacy status mismatch", errors)
    require(manifest.get("legacy_stage11_review_status") == legacy_manifest.get("status"), "legacy status does not match manifest", errors)
    require(manifest.get("legacy_stage11_review_counts") == legacy_counts, "legacy Stage 11 counts mismatch", errors)
    require(manifest.get("legacy_stage11_upload_artifacts_current_gate") is False, "legacy upload gate mismatch", errors)
    require(manifest.get("s11_p3_reviewed_head_policy") == "valid_git_sha_not_current_head_equality", "reviewed_head policy mismatch", errors)
    require(manifest.get("phase_count") == 3, "phase count mismatch", errors)
    require(manifest.get("phase_results") == {"S11-P1": "PASS", "S11-P2": "PASS", "S11-P3": "PASS"}, "phase results mismatch", errors)
    require(manifest.get("s11_p1_dependency_validated") is True, "S11-P1 dependency flag mismatch", errors)
    require(manifest.get("s11_p2_dependency_validated") is True, "S11-P2 dependency flag mismatch", errors)
    require(manifest.get("s11_p3_dependency_validated") is True, "S11-P3 dependency flag mismatch", errors)
    require(p1.get("phase_id") == "S11-P1", "S11-P1 validator did not return S11-P1", errors)
    require(p2.get("phase_id") == "S11-P2", "S11-P2 validator did not return S11-P2", errors)
    require(p3.get("phase_id") == "S11-P3", "S11-P3 validator did not return S11-P3", errors)
    require(p1.get("stage11_phase_progress", {}).get("stage11_review_performed") is False, "S11-P1 must not include review", errors)
    require(p2.get("stage11_phase_progress", {}).get("stage11_review_performed") is False, "S11-P2 must not include review", errors)
    require(p3.get("stage11_phase_progress", {}).get("stage11_review_performed") is False, "S11-P3 must not include review", errors)

    expected_phase_manifests = {
        **PHASE_MANIFESTS,
        "legacy_S11_review": str(LEGACY_STAGE11_REVIEW_MANIFEST_PATH),
    }
    require(manifest.get("reviewed_phase_manifests") == expected_phase_manifests, "reviewed phase manifests mismatch", errors)
    for key, path in expected_phase_manifests.items():
        require(Path(path).exists(), f"missing reviewed manifest for {key}: {path}", errors)

    p1_summary = p1["home_navigation_summary"]
    p2_summary = p2["source_check_board_summary"]
    p3_summary = p3["project_cost_page_summary"]
    v14_baseline = p3["v14_html_uiux_baseline"]
    gate = manifest.get("stage_gate", {})
    expected_gate = {
        "navigation_module_count": 8,
        "nav_button_count": 8,
        "module_action_button_count": 8,
        "source_check_matrix_row_count": 13,
        "source_check_required_column_count": 11,
        "source_check_allowed_status_count": 5,
        "project_cost_page_row_count": 4,
        "project_cost_page_column_count": 7,
        "cost_category_count": 9,
        "margin_record_count": 4,
        "pending_reconciliation_count": 12,
        "html_export_count": 3,
        "v14_html_uiux_audit_file_count": 6,
        "v14_html_uiux_control_row_count": 54,
        "v14_html_uiux_audit_pass_count": 54,
        "v14_html_uiux_audit_warn_count": 0,
        "v14_html_uiux_audit_fail_count": 0,
        "large_yellow_surface_count": 0,
        "quality_bypass_allowed_count": 0,
        "formal_report_count": 0,
        "business_decision_basis_count": 0,
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "release_permission": "blocked",
    }
    derived_gate = {
        "navigation_module_count": p1_summary["navigation_module_count"],
        "nav_button_count": p1_summary["nav_button_count"],
        "module_action_button_count": p1_summary["module_action_button_count"],
        "source_check_matrix_row_count": p2_summary["matrix_row_count"],
        "source_check_required_column_count": p2_summary["required_column_count"],
        "source_check_allowed_status_count": p2_summary["allowed_status_count"],
        "project_cost_page_row_count": p3_summary["project_row_count"],
        "project_cost_page_column_count": p3_summary["project_list_column_count"],
        "cost_category_count": p3_summary["cost_category_count"],
        "margin_record_count": p3_summary["margin_record_count"],
        "pending_reconciliation_count": p3_summary["pending_reconciliation_count"],
        "html_export_count": p1_summary["html_export_count"] + p2_summary["html_export_count"] + p3_summary["html_export_count"],
        "v14_html_uiux_audit_file_count": v14_baseline["audit_file_count"],
        "v14_html_uiux_control_row_count": v14_baseline["audit_control_row_count"],
        "v14_html_uiux_audit_pass_count": v14_baseline["audit_pass_count"],
        "v14_html_uiux_audit_warn_count": v14_baseline["audit_warn_count"],
        "v14_html_uiux_audit_fail_count": v14_baseline["audit_fail_count"],
        "large_yellow_surface_count": 0,
        "quality_bypass_allowed_count": 0,
        "formal_report_count": 0,
        "business_decision_basis_count": 0,
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "release_permission": "blocked",
    }
    for key, expected in expected_gate.items():
        require(gate.get(key) == expected, f"stage_gate.{key} mismatch", errors)
        require(gate.get(key) == derived_gate[key], f"stage_gate.{key} does not match phase evidence", errors)

    release_state = manifest.get("release_state", {})
    for key in RELEASE_FALSE_KEYS:
        require(release_state.get(key) is False, f"release_state.{key} must be false", errors)
    require(release_state.get("current_go_no_go") == "NO_GO", "go/no-go mismatch", errors)
    require(release_state.get("current_report_grade") == "D", "release report grade mismatch", errors)

    raw = manifest.get("raw_data_boundary", {})
    for key in RAW_REVIEW_FALSE_KEYS:
        require(raw.get(key) is False, f"raw_data_boundary.{key} must be false", errors)
    for key in RAW_REVIEW_TRUE_KEYS:
        require(raw.get(key) is True, f"raw_data_boundary.{key} must be true", errors)

    safety = manifest.get("public_repo_safety", {})
    for key in PUBLIC_SAFETY_FALSE_KEYS:
        require(safety.get(key) is False, f"public_repo_safety.{key} must be false", errors)
    require(safety.get("html_ui_export_committed") is True, "HTML UI export flag mismatch", errors)

    findings = manifest.get("review_findings", [])
    finding_summary = manifest.get("review_findings_summary", {})
    require(isinstance(findings, list), "review_findings must be a list", errors)
    require(finding_summary.get("open_finding_count") == 0, "open finding count must be 0", errors)
    require(finding_summary.get("fixed_finding_count") >= 2, "fixed finding count must be at least 2", errors)
    require(
        any(finding.get("finding_id") == "KMFA-V014-S11-REV-F01" and finding.get("status") == "fixed" for finding in findings),
        "missing fixed legacy upload boundary finding",
        errors,
    )
    require(
        any(finding.get("finding_id") == "KMFA-V014-S11-REV-F02" and finding.get("status") == "fixed" for finding in findings),
        "missing fixed reviewed_head durability finding",
        errors,
    )

    validation = manifest.get("validation_summary", {})
    for key in VALIDATION_KEYS:
        require(validation.get(key) == "PASS", f"validation_summary.{key} must be PASS", errors)
    hard_blocks = manifest.get("hard_blocks", [])
    require(isinstance(hard_blocks, list), "hard_blocks must be a list", errors)
    for block in REQUIRED_HARD_BLOCKS:
        require(block in hard_blocks, f"missing hard block: {block}", errors)
    require(manifest.get("hard_block_count") == len(REQUIRED_HARD_BLOCKS), "hard block count mismatch", errors)
    require(manifest.get("next_phase") == NEXT_PHASE, "next phase mismatch", errors)
    require(manifest.get("next_required_step") == NEXT_INSTRUCTION, "next instruction mismatch", errors)

    artifact_refs = manifest.get("artifact_refs", {})
    for key in (
        "manifest",
        "report",
        "test_results",
        "risk_register",
        "rollback_plan",
        "generator",
        "validator",
        "unit_test",
        "s11_p1_manifest",
        "s11_p2_manifest",
        "s11_p3_manifest",
        "legacy_stage11_review_manifest",
    ):
        path = Path(artifact_refs.get(key, ""))
        require(path.exists(), f"missing artifact ref: {key} -> {path}", errors)
    for ref in manifest.get("evidence_refs", []):
        require(Path(ref).exists(), f"missing evidence ref: {ref}", errors)

    for evidence in (MANIFEST_PATH, REPORT_PATH, TEST_RESULTS_PATH, RISK_REGISTER_PATH, ROLLBACK_PATH):
        check_public_evidence_text(evidence, errors)
    test_text = TEST_RESULTS_PATH.read_text(encoding="utf-8", errors="ignore")
    require("PENDING" not in test_text, "test results must not contain pending marker", errors)
    require("check_v014_s11_stage_review.py" in test_text, "Stage 11 validator evidence missing", errors)
    require("test_v014_s11_stage_review" in test_text, "Stage 11 unit test evidence missing", errors)
    require("Stage 12 and GitHub upload were intentionally not performed" in test_text, "phase boundary evidence missing", errors)

    reviewed_head = str(manifest.get("reviewed_head", ""))
    require(
        len(reviewed_head) == 40 and all(character in "0123456789abcdef" for character in reviewed_head),
        "reviewed_head must be a lowercase 40-character git SHA",
        errors,
    )
    require(manifest.get("branch") == git_output(["branch", "--show-current"]), "branch mismatch", errors)
    require(manifest.get("remote") == git_output(["remote", "get-url", "origin"]), "remote mismatch", errors)

    if errors:
        raise ValidationError("; ".join(errors))
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.4 Stage 11 review evidence.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args(argv)
    try:
        manifest = validate_v014_s11_stage_review(args.manifest)
    except ValidationError as exc:
        print(f"FAIL: {exc}")
        return 1
    gate = manifest["stage_gate"]
    print(
        "PASS: KMFA v0.1.4 Stage 11 review validated "
        f"(phase_results={manifest['phase_results']}, "
        f"open_findings={manifest['review_findings_summary']['open_finding_count']}, "
        f"fixed_findings={manifest['review_findings_summary']['fixed_finding_count']}, "
        f"navigation_modules={gate['navigation_module_count']}, "
        f"source_rows={gate['source_check_matrix_row_count']}, "
        f"project_rows={gate['project_cost_page_row_count']}, "
        f"s12={str(manifest['s12_p1_performed']).lower()}, "
        f"github_upload={str(manifest['github_upload_performed']).lower()})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
