#!/usr/bin/env python3
"""Validate KMFA v0.1.4 Stage 14 review evidence."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.check_s14_stage_review import validate_stage_review as validate_legacy_stage14_review  # noqa: E402
from KMFA.tools.v014_s14_stage_review import (  # noqa: E402
    ACCEPTANCE_ID,
    LEGACY_STAGE14_REVIEW_MANIFEST_PATH,
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
    "compressed_raw_package_committed",
    "excel_workbook_committed",
    "wps_native_file_committed",
    "raw_or_private_csv_committed",
    "pdf_document_committed",
    "private_csv_committed",
    "local_database_committed",
    "auth_material_committed",
    "connector_auth_material_committed",
    "field_plaintext_committed",
    "source_header_plaintext_committed",
    "raw_file_names_committed",
    "raw_file_hashes_committed",
    "tab_labels_committed",
    "source_record_payload_committed",
    "normalized_source_values_committed",
    "business_amount_values_committed",
    "project_or_customer_plaintext_committed",
    "account_number_committed",
    "invoice_number_committed",
    "tax_identifier_committed",
    "formal_report_committed",
    "business_decision_basis_committed",
    "payment_or_bank_operation_committed",
    "loan_management_action_committed",
    "tax_or_invoice_operation_committed",
    "formal_policy_conclusion_committed",
    "policy_application_file_committed",
    "policy_or_subsidy_filing_committed",
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
    "s14_p1_raw_inbox_all_false",
    "s14_p2_raw_inbox_all_false",
    "s14_p3_raw_inbox_all_false",
)
RELEASE_FALSE_KEYS = (
    "delivery_allowed",
    "formal_report_allowed",
    "business_decision_basis_allowed",
    "business_execution_allowed",
    "payment_or_bank_operation_allowed",
    "loan_management_action_allowed",
    "invoice_issuance_allowed",
    "tax_filing_allowed",
    "formal_policy_conclusion_allowed",
    "policy_application_submission_allowed",
    "subsidy_application_allowed",
    "github_main_upload_allowed",
)
VALIDATION_KEYS = (
    "py_compile",
    "s14_p1_validator",
    "s14_p2_validator",
    "s14_p3_validator",
    "legacy_s14_stage_review_validator",
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
    "high_signal_secret_scan",
    "public_stage14_semantic_scan",
    "diff_check",
)
REQUIRED_HARD_BLOCKS = (
    "report_grade_d_only",
    "pending_reconciliation_blocks_formal_report",
    "quality_grade_bypass_forbidden",
    "raw_data_mutation_forbidden",
    "protected_source_publication_forbidden",
    "field_header_plaintext_publication_forbidden",
    "formal_report_release_blocked",
    "business_decision_basis_blocked",
    "payment_or_bank_operation_blocked",
    "loan_management_action_blocked",
    "invoice_issuance_blocked",
    "tax_filing_blocked",
    "formal_policy_conclusion_blocked",
    "policy_application_submission_blocked",
    "subsidy_application_blocked",
    "s15_p1_not_performed",
    "lineage_full_check_not_performed",
    "protected_source_matching_not_performed",
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
    "amount_cents:",
    "amount_yuan:",
    "sheet_name:",
    "row_value:",
    "cell_value:",
    "business_data:",
    "bank_statement",
    "contract_full_text",
    "salary_detail",
    "connector_" + "token:",
    "connector_" + "pass" + "word:",
    "api" + "_key:",
    "private" + "_key:",
    "-----" "BEGIN",
    "s" "k-",
    "project_name_plaintext",
    "customer_name_plaintext",
    "counterparty_plaintext",
    "company_entity_plaintext",
    "account_number:",
    "invoice_number:",
    "tax_identifier:",
    "KMFA" "_MetaData",
    "/Users/linzezhang/Downloads",
    "." + "xlsx",
    "." + "xls",
    "." + "zip",
    "." + "pdf",
    "." + "sqlite",
    "." + "db",
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


def _expected_stage_gate(p1: dict[str, Any], p2: dict[str, Any], p3: dict[str, Any]) -> dict[str, Any]:
    p1_summary = p1["fund_cash_loan_summary"]
    p2_summary = p2["invoice_tax_summary"]
    p3_summary = p3["policy_evidence_summary"]
    v14_baseline = p3["v14_taskpack_baseline"]
    return {
        "fund_cash_loan_source_lane_count": p1_summary["source_lane_count"],
        "fund_cash_loan_source_count": p1_summary["source_count"],
        "fund_cash_loan_field_mapping_count": p1_summary["field_mapping_count"],
        "cash_pressure_record_count": p1_summary["cash_pressure_record_count"],
        "loan_due_alert_count": p1_summary["loan_due_alert_count"],
        "account_balance_summary_count": p1_summary["account_balance_summary_count"],
        "invoice_tax_source_lane_count": p2_summary["source_lane_count"],
        "invoice_tax_source_count": p2_summary["source_count"],
        "invoice_tax_field_mapping_count": p2_summary["field_mapping_count"],
        "invoice_tax_issue_candidate_count": p2_summary["issue_candidate_count"],
        "invoice_tax_cash_summary_count": p2_summary["cash_summary_count"],
        "policy_evidence_source_count": p3_summary["source_count"],
        "policy_evidence_field_mapping_count": p3_summary["field_mapping_count"],
        "policy_program_count": p3_summary["policy_program_count"],
        "policy_evidence_directory_count": p3_summary["evidence_directory_count"],
        "policy_evidence_gap_count": p3_summary["evidence_gap_count"],
        "policy_risk_tip_count": p3_summary["risk_tip_count"],
        "html_export_count": p1_summary["html_output_count"] + p2_summary["html_output_count"] + p3_summary["html_output_count"],
        "pending_reconciliation_count": p3_summary["pending_reconciliation_count"],
        "formal_report_count": 0,
        "business_decision_basis_count": 0,
        "payment_or_bank_operation_count": 0,
        "loan_management_action_count": 0,
        "tax_filing_count": 0,
        "invoice_issuance_count": 0,
        "formal_policy_conclusion_count": 0,
        "policy_application_submission_count": 0,
        "subsidy_application_count": 0,
        "v14_html_uiux_audit_file_count": v14_baseline["audit_file_count"],
        "v14_html_uiux_control_row_count": v14_baseline["audit_control_row_count"],
        "v14_html_uiux_audit_pass_count": v14_baseline["audit_pass_count"],
        "v14_html_uiux_audit_warn_count": v14_baseline["audit_warn_count"],
        "v14_html_uiux_audit_fail_count": v14_baseline["audit_fail_count"],
        "quality_bypass_allowed_count": 0,
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "release_permission": "blocked",
    }


def validate_v014_s14_stage_review(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []
    manifest = read_json(manifest_path)
    p1 = read_json(Path(PHASE_MANIFESTS["S14-P1"]))
    p2 = read_json(Path(PHASE_MANIFESTS["S14-P2"]))
    p3 = read_json(Path(PHASE_MANIFESTS["S14-P3"]))
    legacy_counts = validate_legacy_stage14_review()
    legacy_manifest = read_json(LEGACY_STAGE14_REVIEW_MANIFEST_PATH)

    require(manifest.get("schema_version") == SCHEMA_VERSION, "schema mismatch", errors)
    require(manifest.get("project_id") == "KMFA", "project_id mismatch", errors)
    require(manifest.get("version") == "0.1.4", "version mismatch", errors)
    require(manifest.get("stage_id") == "S14", "stage_id must be S14", errors)
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
    require(manifest.get("s15_p1_performed") is False, "S15-P1 must not be performed", errors)
    require(manifest.get("github_upload_ready_next_gate") is False, "upload ready must stay false", errors)
    require(manifest.get("github_upload_deferred_until_v014_stage1_18_complete") is True, "upload defer flag mismatch", errors)
    require(manifest.get("github_upload_performed") is False, "GitHub upload must not be performed", errors)
    require(
        manifest.get("github_upload_status") == "not_uploaded_deferred_until_v014_stage1_18_complete",
        "GitHub upload status mismatch",
        errors,
    )
    require(manifest.get("legacy_stage14_review_validated") is True, "legacy Stage 14 review flag mismatch", errors)
    require(manifest.get("legacy_stage14_review_manifest") == str(LEGACY_STAGE14_REVIEW_MANIFEST_PATH), "legacy manifest mismatch", errors)
    require(
        manifest.get("legacy_stage14_review_status") == legacy_manifest.get("status") == "review_passed_upload_ready_local_only",
        "legacy status mismatch",
        errors,
    )
    require(manifest.get("legacy_stage14_review_counts") == legacy_counts, "legacy Stage 14 counts mismatch", errors)
    require(manifest.get("legacy_stage14_upload_artifacts_current_gate") is False, "legacy upload gate mismatch", errors)
    require(manifest.get("phase_count") == 3, "phase count mismatch", errors)
    require(manifest.get("phase_results") == {"S14-P1": "PASS", "S14-P2": "PASS", "S14-P3": "PASS"}, "phase results mismatch", errors)
    require(manifest.get("s14_p1_dependency_validated") is True, "S14-P1 dependency flag mismatch", errors)
    require(manifest.get("s14_p2_dependency_validated") is True, "S14-P2 dependency flag mismatch", errors)
    require(manifest.get("s14_p3_dependency_validated") is True, "S14-P3 dependency flag mismatch", errors)
    require(p1.get("phase_id") == "S14-P1", "S14-P1 validator did not return S14-P1", errors)
    require(p2.get("phase_id") == "S14-P2", "S14-P2 validator did not return S14-P2", errors)
    require(p3.get("phase_id") == "S14-P3", "S14-P3 validator did not return S14-P3", errors)
    require(p1.get("stage14_phase_progress", {}).get("stage14_review_performed") is False, "S14-P1 must not include review", errors)
    require(p2.get("stage14_phase_progress", {}).get("stage14_review_performed") is False, "S14-P2 must not include review", errors)
    require(p3.get("stage14_phase_progress", {}).get("stage14_review_performed") is False, "S14-P3 must not include review", errors)

    expected_phase_manifests = {
        **PHASE_MANIFESTS,
        "legacy_S14_review": str(LEGACY_STAGE14_REVIEW_MANIFEST_PATH),
    }
    require(manifest.get("reviewed_phase_manifests") == expected_phase_manifests, "reviewed phase manifests mismatch", errors)
    for key, path in expected_phase_manifests.items():
        require(Path(path).exists(), f"missing reviewed manifest for {key}: {path}", errors)

    expected_gate = {
        "fund_cash_loan_source_lane_count": 4,
        "fund_cash_loan_source_count": 5,
        "fund_cash_loan_field_mapping_count": 25,
        "cash_pressure_record_count": 4,
        "loan_due_alert_count": 3,
        "account_balance_summary_count": 3,
        "invoice_tax_source_lane_count": 3,
        "invoice_tax_source_count": 6,
        "invoice_tax_field_mapping_count": 30,
        "invoice_tax_issue_candidate_count": 3,
        "invoice_tax_cash_summary_count": 3,
        "policy_evidence_source_count": 4,
        "policy_evidence_field_mapping_count": 19,
        "policy_program_count": 5,
        "policy_evidence_directory_count": 5,
        "policy_evidence_gap_count": 5,
        "policy_risk_tip_count": 5,
        "html_export_count": 3,
        "pending_reconciliation_count": 12,
        "formal_report_count": 0,
        "business_decision_basis_count": 0,
        "payment_or_bank_operation_count": 0,
        "loan_management_action_count": 0,
        "tax_filing_count": 0,
        "invoice_issuance_count": 0,
        "formal_policy_conclusion_count": 0,
        "policy_application_submission_count": 0,
        "subsidy_application_count": 0,
        "v14_html_uiux_audit_file_count": 6,
        "v14_html_uiux_control_row_count": 54,
        "v14_html_uiux_audit_pass_count": 54,
        "v14_html_uiux_audit_warn_count": 0,
        "v14_html_uiux_audit_fail_count": 0,
        "quality_bypass_allowed_count": 0,
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "release_permission": "blocked",
    }
    derived_gate = _expected_stage_gate(p1, p2, p3)
    gate = manifest.get("stage_gate", {})
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
    require(finding_summary.get("fixed_finding_count") >= 1, "fixed finding count must be at least 1", errors)
    require(
        any(finding.get("finding_id") == "KMFA-V014-S14-REV-F01" and finding.get("status") == "fixed" for finding in findings),
        "missing fixed legacy upload boundary finding",
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
        "s14_p1_manifest",
        "s14_p2_manifest",
        "s14_p3_manifest",
        "legacy_stage14_review_manifest",
    ):
        path = Path(artifact_refs.get(key, ""))
        require(path.exists(), f"missing artifact ref: {key} -> {path}", errors)
    for ref in manifest.get("evidence_refs", []):
        require(Path(ref).exists(), f"missing evidence ref: {ref}", errors)

    for evidence in (MANIFEST_PATH, REPORT_PATH, TEST_RESULTS_PATH, RISK_REGISTER_PATH, ROLLBACK_PATH):
        check_public_evidence_text(evidence, errors)
    test_text = TEST_RESULTS_PATH.read_text(encoding="utf-8", errors="ignore")
    require("PENDING" not in test_text, "test results must not contain pending marker", errors)
    require("check_v014_s14_stage_review.py" in test_text, "Stage 14 validator evidence missing", errors)
    require("test_v014_s14_stage_review" in test_text, "Stage 14 unit test evidence missing", errors)
    require("S15 and GitHub upload were intentionally not performed" in test_text, "phase boundary evidence missing", errors)

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
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.4 Stage 14 review evidence.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args(argv)
    try:
        manifest = validate_v014_s14_stage_review(args.manifest)
    except ValidationError as exc:
        print(f"FAIL: {exc}")
        return 1
    gate = manifest["stage_gate"]
    print(
        "PASS: KMFA v0.1.4 Stage 14 review validated "
        f"(phase_results={manifest['phase_results']}, "
        f"open_findings={manifest['review_findings_summary']['open_finding_count']}, "
        f"fixed_findings={manifest['review_findings_summary']['fixed_finding_count']}, "
        f"fund_lanes={gate['fund_cash_loan_source_lane_count']}, "
        f"invoice_tax_lanes={gate['invoice_tax_source_lane_count']}, "
        f"policy_dirs={gate['policy_evidence_directory_count']}, "
        f"pending_reconciliation={gate['pending_reconciliation_count']}, "
        f"s15={str(manifest['s15_p1_performed']).lower()}, "
        f"github_upload={str(manifest['github_upload_performed']).lower()})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
