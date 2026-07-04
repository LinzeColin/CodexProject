#!/usr/bin/env python3
"""Validate KMFA v0.1.4 Stage 10 review evidence."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from KMFA.tools.check_s10_stage_review import validate_stage_review as validate_legacy_stage10_review
from KMFA.tools.check_v013_s10_stage_review import validate_v013_s10_stage_review
from KMFA.tools.check_v014_s10_p1_report_templates import validate_v014_s10_p1_report_templates
from KMFA.tools.check_v014_s10_p2_report_trust_grade import validate_v014_s10_p2_report_trust_grade
from KMFA.tools.check_v014_s10_p3_report_export import validate_v014_s10_p3_report_export
from KMFA.tools.v014_s10_stage_review import (
    ACCEPTANCE_ID,
    LEGACY_STAGE10_REVIEW_MANIFEST_PATH,
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
    V013_STAGE10_REVIEW_MANIFEST,
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
    "s10_p1_raw_inbox_all_false",
    "s10_p2_raw_inbox_all_false",
    "s10_p3_raw_inbox_all_false",
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
    "s10_p1_validator",
    "s10_p2_validator",
    "s10_p3_validator",
    "legacy_s10_p1_validator",
    "legacy_s10_p1_unit",
    "legacy_s10_p2_validator",
    "legacy_s10_p2_unit",
    "legacy_s10_p3_validator",
    "legacy_s10_p3_unit",
    "legacy_stage10_review_validator",
    "v013_stage10_review_validator",
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
    "public_stage10_semantic_scan",
    "diff_check",
)
REQUIRED_HARD_BLOCKS = (
    "report_grade_d_only",
    "zero_delta_failed",
    "unresolved_critical_difference",
    "missing_required_lineage",
    "missing_human_confirmation_for_A",
    "pending_reconciliation_blocks_formal_report",
    "raw_data_mutation_forbidden",
    "raw_value_publication_forbidden",
    "field_header_plaintext_publication_forbidden",
    "formal_report_release_blocked",
    "business_decision_basis_blocked",
    "s11_p1_not_performed",
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
    "KMFA" "_MetaData",
    "/Users/linzezhang/Downloads",
)
STRICT_SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(?i)(password|passwd|secret|api_key|token)\s*=\s*[^\s,;]{8,}"),
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


def validate_v014_s10_stage_review(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []
    manifest = read_json(manifest_path)
    p1 = validate_v014_s10_p1_report_templates()
    p2 = validate_v014_s10_p2_report_trust_grade()
    p3 = validate_v014_s10_p3_report_export()
    v013 = validate_v013_s10_stage_review()
    legacy_counts = validate_legacy_stage10_review()

    require(manifest.get("schema_version") == SCHEMA_VERSION, "schema mismatch", errors)
    require(manifest.get("project_id") == "KMFA", "project_id mismatch", errors)
    require(manifest.get("version") == "0.1.4", "version mismatch", errors)
    require(manifest.get("stage_id") == "S10", "stage_id must be S10", errors)
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
    require(manifest.get("s11_p1_performed") is False, "S11-P1 must not be performed", errors)
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
    require(manifest.get("legacy_stage10_upload_artifacts_current_gate") is False, "legacy upload gate mismatch", errors)
    require(manifest.get("phase_count") == 3, "phase count mismatch", errors)
    require(manifest.get("phase_results") == {"S10-P1": "PASS", "S10-P2": "PASS", "S10-P3": "PASS"}, "phase results mismatch", errors)
    require(manifest.get("s10_p1_dependency_validated") is True, "S10-P1 dependency flag mismatch", errors)
    require(manifest.get("s10_p2_dependency_validated") is True, "S10-P2 dependency flag mismatch", errors)
    require(manifest.get("s10_p3_dependency_validated") is True, "S10-P3 dependency flag mismatch", errors)
    require(p1.get("phase_id") == "S10-P1", "S10-P1 validator did not return S10-P1", errors)
    require(p2.get("phase_id") == "S10-P2", "S10-P2 validator did not return S10-P2", errors)
    require(p3.get("phase_id") == "S10-P3", "S10-P3 validator did not return S10-P3", errors)
    require(p1.get("stage10_review_performed") is False, "S10-P1 must not include review", errors)
    require(p2.get("stage10_review_performed") is False, "S10-P2 must not include review", errors)
    require(p3.get("stage10_phase_progress", {}).get("stage10_review_performed") is False, "S10-P3 must not include review", errors)
    require(v013.get("stage_id") == "S10", "v0.1.3 Stage 10 review did not validate", errors)
    require(manifest.get("v013_stage10_review_validated") is True, "v013 Stage 10 review flag mismatch", errors)
    require(manifest.get("v013_stage10_review_manifest") == V013_STAGE10_REVIEW_MANIFEST, "v013 Stage 10 manifest mismatch", errors)
    require(manifest.get("legacy_stage10_review_validated") is True, "legacy Stage 10 review flag mismatch", errors)
    require(manifest.get("legacy_stage10_review_manifest") == str(LEGACY_STAGE10_REVIEW_MANIFEST_PATH), "legacy Stage 10 manifest mismatch", errors)
    require(manifest.get("legacy_stage10_review_counts") == legacy_counts, "legacy Stage 10 counts mismatch", errors)

    reviewed_phase_manifests = manifest.get("reviewed_phase_manifests", {})
    expected_phase_manifests = {
        **PHASE_MANIFESTS,
        "v013_S10_review": V013_STAGE10_REVIEW_MANIFEST,
        "legacy_S10_review": str(LEGACY_STAGE10_REVIEW_MANIFEST_PATH),
    }
    require(reviewed_phase_manifests == expected_phase_manifests, "reviewed phase manifests mismatch", errors)
    for key, path in expected_phase_manifests.items():
        require(Path(path).exists(), f"missing reviewed manifest for {key}: {path}", errors)

    p1_manifest = read_json(Path(PHASE_MANIFESTS["S10-P1"]))
    p3_summary = p3["report_export_summary"]
    gate = manifest.get("stage_gate", {})
    expected_gate = {
        "report_template_count": p1["template_count"],
        "report_template_section_count": p1["section_count"],
        "project_cost_section_count": p1["project_cost_section_count"],
        "business_overview_section_count": p1["business_overview_section_count"],
        "html_uiux_baseline_file_count": p1_manifest["v14_html_uiux_baseline"]["html_file_count"],
        "html_uiux_control_row_count": p1_manifest["v14_html_uiux_baseline"]["control_row_count"],
        "report_grade_record_count": p2["report_grade_record_count"],
        "grade_distribution": {"D": 2},
        "pending_reconciliation_count": p3_summary["pending_reconciliation_count"],
        "confirmed_resolution_count": p2["confirmed_resolution_count"],
        "source_quality_grade": "Q4",
        "zero_delta_passed": False,
        "full_trusted_report_allowed_count": 0,
        "complete_trusted_report_display_allowed_count": 0,
        "report_export_record_count": p3_summary["report_export_record_count"],
        "html_export_count": p3_summary["html_export_count"],
        "csv_appendix_count": p3_summary["csv_appendix_count"],
        "excel_compatible_download_count": p3_summary["excel_compatible_download_count"],
        "pdf_export_enabled_after_template_stable": True,
        "committed_pdf_file_count": 0,
        "committed_excel_file_count": 0,
        "formal_report_count": 0,
        "business_decision_basis_count": 0,
        "q5_calculation_baseline_allowed_count": 0,
        "formal_report_allowed_count": 0,
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "release_permission": "blocked",
    }
    for key, expected in expected_gate.items():
        require(gate.get(key) == expected, f"stage_gate.{key} mismatch", errors)

    release_state = manifest.get("release_state", {})
    for key in RELEASE_FALSE_KEYS:
        require(release_state.get(key) is False, f"release_state.{key} must be false", errors)
    require(release_state.get("current_go_no_go") == "NO_GO", "go/no-go mismatch", errors)
    require(release_state.get("current_report_grade") == "D", "release report grade mismatch", errors)

    export_policy = manifest.get("report_export_policy", {})
    require(export_policy.get("record_version_binding_count") == 2, "record version binding count mismatch", errors)
    require(export_policy.get("html_export_allowed") is True, "HTML export allowed mismatch", errors)
    require(export_policy.get("csv_excel_export_allowed") is True, "CSV export allowed mismatch", errors)
    require(export_policy.get("pdf_export_policy_enabled") is True, "PDF policy enabled mismatch", errors)
    require(export_policy.get("pdf_private_runtime_only") is True, "PDF private runtime mismatch", errors)
    require(export_policy.get("formal_report_allowed") is False, "export policy formal report mismatch", errors)
    require(export_policy.get("business_decision_basis_allowed") is False, "export policy business basis mismatch", errors)

    raw = manifest.get("raw_data_boundary", {})
    for key in RAW_REVIEW_FALSE_KEYS:
        require(raw.get(key) is False, f"raw_data_boundary.{key} must be false", errors)
    for key in RAW_REVIEW_TRUE_KEYS:
        require(raw.get(key) is True, f"raw_data_boundary.{key} must be true", errors)

    safety = manifest.get("public_repo_safety", {})
    for key in PUBLIC_SAFETY_FALSE_KEYS:
        require(safety.get(key) is False, f"public_repo_safety.{key} must be false", errors)
    require(safety.get("public_safe_csv_export_committed") is True, "CSV export flag mismatch", errors)
    require(safety.get("html_report_export_committed") is True, "HTML export flag mismatch", errors)

    findings = manifest.get("review_findings", [])
    finding_summary = manifest.get("review_findings_summary", {})
    require(isinstance(findings, list), "review_findings must be a list", errors)
    require(finding_summary.get("open_finding_count") == 0, "open finding count must be 0", errors)
    require(finding_summary.get("fixed_finding_count") >= 1, "fixed finding count must be at least 1", errors)
    require(
        any(finding.get("finding_id") == "KMFA-V014-S10-REV-F01" and finding.get("status") == "fixed" for finding in findings),
        "missing fixed legacy upload boundary finding",
        errors,
    )
    require(
        any(finding.get("finding_id") == "KMFA-V014-S10-REV-F02" and finding.get("status") == "fixed" for finding in findings),
        "missing fixed S10-P3 test evidence finding",
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
        "s10_p1_manifest",
        "s10_p2_manifest",
        "s10_p3_manifest",
        "v013_stage10_review_manifest",
        "legacy_stage10_review_manifest",
    ):
        path = Path(artifact_refs.get(key, ""))
        require(path.exists(), f"missing artifact ref: {key} -> {path}", errors)
    for ref in manifest.get("evidence_refs", []):
        require(Path(ref).exists(), f"missing evidence ref: {ref}", errors)

    for evidence in (MANIFEST_PATH, REPORT_PATH, TEST_RESULTS_PATH, RISK_REGISTER_PATH, ROLLBACK_PATH):
        check_public_evidence_text(evidence, errors)
    test_text = TEST_RESULTS_PATH.read_text(encoding="utf-8", errors="ignore")
    require("pending_final_validation" not in test_text, "test results must not remain pending", errors)
    require("check_v014_s10_stage_review.py" in test_text, "Stage 10 validator evidence missing", errors)
    require("test_v014_s10_stage_review" in test_text, "Stage 10 unit test evidence missing", errors)
    require("Stage 11 and GitHub upload were intentionally not performed" in test_text, "phase boundary evidence missing", errors)

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
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.4 Stage 10 review evidence.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args(argv)
    try:
        manifest = validate_v014_s10_stage_review(args.manifest)
    except ValidationError as exc:
        print(f"FAIL: {exc}")
        return 1
    gate = manifest["stage_gate"]
    print(
        "PASS: KMFA v0.1.4 Stage 10 review validated "
        f"(phase_results={manifest['phase_results']}, "
        f"open_findings={manifest['review_findings_summary']['open_finding_count']}, "
        f"fixed_findings={manifest['review_findings_summary']['fixed_finding_count']}, "
        f"report_templates={gate['report_template_count']}, "
        f"report_grades={gate['report_grade_record_count']}, "
        f"report_exports={gate['report_export_record_count']}, "
        f"stage11={str(manifest['s11_p1_performed']).lower()}, "
        f"github_upload={str(manifest['github_upload_performed']).lower()})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
