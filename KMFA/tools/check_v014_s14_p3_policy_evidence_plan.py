#!/usr/bin/env python3
"""Validate KMFA v0.1.4 S14-P3 policy evidence planning evidence."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from KMFA.tools.policy_evidence_plan import (
    REQUIRED_EVIDENCE_DIRECTORIES,
    REQUIRED_POLICY_PROGRAMS,
    validate_policy_evidence_artifacts,
)
from KMFA.tools.v014_s14_p3_policy_evidence_plan import (
    ACCEPTANCE_ID,
    DIRECTORIES_PATH,
    GAPS_PATH,
    HTML_OVERVIEW_PATH,
    MANIFEST_PATH,
    NEXT_REQUIRED_STEP,
    PHASE_SCOPE,
    REPORT_PATH,
    RISK_REGISTER_PATH,
    RISK_TIPS_PATH,
    ROLLBACK_PATH,
    SCHEMA_VERSION,
    TASK_ID,
    TEST_RESULTS_PATH,
    _phase_boundaries,
    _public_repo_safety,
    _quality_gate,
    _raw_boundary,
    load_v14_taskpack_baseline,
    validate_legacy_s14_p3_artifacts,
    validate_s14_p2_dependency,
)


PUBLIC_SAFETY_FALSE_KEYS = tuple(key for key, value in _public_repo_safety().items() if value is False)
RAW_BOUNDARY_FALSE_KEYS = tuple(key for key, value in _raw_boundary().items() if value is False)
QUALITY_FALSE_KEYS = tuple(key for key, value in _quality_gate().items() if value is False)
QUALITY_TRUE_KEYS = tuple(key for key, value in _quality_gate().items() if value is True)
PHASE_FALSE_KEYS = tuple(key for key, value in _phase_boundaries().items() if value is False)
PHASE_TRUE_KEYS = tuple(key for key, value in _phase_boundaries().items() if value is True)
REQUIRED_HARD_BLOCKS = (
    "report_grade_d_only",
    "pending_reconciliation_blocks_formal_report",
    "raw_data_mutation_forbidden",
    "raw_value_publication_forbidden",
    "field_header_plaintext_publication_forbidden",
    "formal_report_release_blocked",
    "business_decision_basis_blocked",
    "policy_qualification_conclusion_blocked",
    "policy_application_submission_blocked",
    "subsidy_application_blocked",
    "tax_filing_blocked",
    "invoice_issuance_blocked",
    "payment_approval_blocked",
    "payment_execution_blocked",
    "bank_operation_blocked",
    "loan_management_action_blocked",
    "stage14_review_not_performed",
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
    "tax_identifier:",
    "tax_rate_value:",
    "invoice_number:",
    "tax_declaration_number:",
    "sheet_name:",
    "row_value:",
    "cell_value:",
    "business_data:",
    "bank_statement",
    "contract_full_text",
    "salary_detail",
    "policy_filing_material",
    "subsidy_application_file",
    "tax_filing_material",
    "tax_filing_record",
    "connector_" + "token:",
    "connector_" + "password:",
    "api" + "_key:",
    "private" + "_key:",
    "-----" "BEGIN",
    "project_name_plaintext",
    "customer_name_plaintext",
    "counterparty_plaintext",
    "company_entity_plaintext",
    "account_number:",
    "private_ref://",
    "KMFA" "_MetaData",
    "/Users/linzezhang/Downloads",
    ".xlsx",
    ".xls",
    ".zip",
    ".pdf",
    ".sqlite",
    ".db",
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


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise ValidationError(f"missing JSONL file: {path}")
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValidationError(f"{path} contains a non-object JSONL row")
        rows.append(value)
    return rows


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


def _html_outputs() -> dict[str, str]:
    return {"policy_evidence_overview": HTML_OVERVIEW_PATH.read_text(encoding="utf-8")}


def validate_v014_s14_p3_policy_evidence_plan(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []
    manifest = read_json(manifest_path)
    directories = read_jsonl(DIRECTORIES_PATH)
    gaps = read_jsonl(GAPS_PATH)
    risk_tips = read_jsonl(RISK_TIPS_PATH)
    html_outputs = _html_outputs()
    s14_p2 = validate_s14_p2_dependency()
    legacy_manifest, legacy_directories, legacy_gaps, legacy_risk_tips, legacy_html = validate_legacy_s14_p3_artifacts()
    baseline = load_v14_taskpack_baseline()

    validate_policy_evidence_artifacts(legacy_manifest, directories, gaps, risk_tips, html_outputs)
    validate_policy_evidence_artifacts(
        legacy_manifest,
        legacy_directories,
        legacy_gaps,
        legacy_risk_tips,
        legacy_html,
    )

    require(manifest.get("schema_version") == SCHEMA_VERSION, "manifest schema mismatch", errors)
    require(manifest.get("project_id") == "KMFA", "project_id mismatch", errors)
    require(manifest.get("version") == "0.1.4", "version mismatch", errors)
    require(manifest.get("stage_id") == "S14", "stage_id must be S14", errors)
    require(manifest.get("phase_id") == "S14-P3", "phase_id must be S14-P3", errors)
    require(manifest.get("phase_scope") == PHASE_SCOPE, "phase scope mismatch", errors)
    require(manifest.get("task_id") == TASK_ID, "task_id mismatch", errors)
    require(manifest.get("acceptance_ids") == [ACCEPTANCE_ID], "acceptance id mismatch", errors)
    require(manifest.get("completed_task_ids") == ["S14P3T01", "S14P3T02", "S14P3T03"], "tasks mismatch", errors)
    require(
        manifest.get("status") == "completed_validated_local_only_no_go_upload_deferred_policy_evidence_plan_locked",
        "status mismatch",
        errors,
    )
    require(manifest.get("s14_p2_dependency_validated") is True, "S14-P2 dependency flag mismatch", errors)
    require(s14_p2.get("next_phase") == "S14-P3", "S14-P2 did not route to S14-P3", errors)
    require(manifest.get("legacy_s14_p3_dependency_validated") is True, "legacy S14-P3 flag mismatch", errors)
    require(manifest.get("v14_taskpack_dependency_validated") is True, "v1.4 taskpack flag mismatch", errors)

    progress = manifest.get("stage14_phase_progress", {})
    require(progress.get("completed_phase_count") == 3, "completed phase count mismatch", errors)
    require(progress.get("total_phase_count") == 3, "total phase count mismatch", errors)
    require(progress.get("derived_percent_bps") == 10000, "derived percent bps mismatch", errors)
    require(progress.get("derived_percent_label") == "100.00%", "derived percent label mismatch", errors)
    require(progress.get("s14_p1_performed") is True, "S14-P1 must be performed", errors)
    require(progress.get("s14_p2_performed") is True, "S14-P2 must be performed", errors)
    require(progress.get("s14_p3_performed") is True, "S14-P3 must be performed", errors)
    require(progress.get("stage14_review_performed") is False, "Stage 14 review must be false", errors)

    summary = manifest.get("policy_evidence_summary", {})
    expected_summary = {
        "policy_program_count": 5,
        "evidence_directory_count": 5,
        "evidence_gap_count": 5,
        "risk_tip_count": 5,
        "html_output_count": 1,
        "pending_reconciliation_count": 12,
        "report_grade_visible": "D",
        "formal_report_count": 0,
        "formal_policy_conclusion_count": 0,
        "policy_application_submission_count": 0,
        "subsidy_application_count": 0,
        "business_decision_basis_count": 0,
        "external_connector_action_count": 0,
        "tax_filing_count": 0,
        "invoice_issuance_count": 0,
        "payment_or_bank_operation_count": 0,
    }
    for key, expected in expected_summary.items():
        require(summary.get(key) == expected, f"summary {key} mismatch", errors)
    require(summary.get("required_policy_programs") == list(REQUIRED_POLICY_PROGRAMS), "required programs mismatch", errors)
    require(
        summary.get("required_evidence_directories") == list(REQUIRED_EVIDENCE_DIRECTORIES),
        "required evidence directories mismatch",
        errors,
    )

    manifest_baseline = manifest.get("v14_taskpack_baseline", {})
    for key in ("audit_file_count", "audit_control_row_count", "audit_pass_count", "audit_warn_count", "audit_fail_count"):
        require(manifest_baseline.get(key) == baseline.get(key), f"baseline {key} mismatch", errors)
    require(
        manifest_baseline.get("implementation_reflects_policy_evidence_directories") is True,
        "policy evidence directory baseline flag mismatch",
        errors,
    )
    require(
        manifest_baseline.get("implementation_reflects_no_policy_conclusion_or_submission") is True,
        "policy conclusion/submission boundary baseline flag mismatch",
        errors,
    )

    for key in QUALITY_FALSE_KEYS:
        require(manifest.get("quality_gate", {}).get(key) is False, f"quality_gate {key} must be false", errors)
    for key in QUALITY_TRUE_KEYS:
        require(manifest.get("quality_gate", {}).get(key) is True, f"quality_gate {key} must be true", errors)
    for key in PHASE_FALSE_KEYS:
        require(manifest.get("phase_boundaries", {}).get(key) is False, f"phase_boundaries {key} must be false", errors)
    for key in PHASE_TRUE_KEYS:
        require(manifest.get("phase_boundaries", {}).get(key) is True, f"phase_boundaries {key} must be true", errors)
    for key in RAW_BOUNDARY_FALSE_KEYS:
        require(manifest.get("raw_data_boundary", {}).get(key) is False, f"raw_data_boundary {key} must be false", errors)
    for key in PUBLIC_SAFETY_FALSE_KEYS:
        require(manifest.get("public_repo_safety", {}).get(key) is False, f"public_repo_safety {key} must be false", errors)

    upload = manifest.get("github_upload", {})
    require(upload.get("github_upload_performed") is False, "github upload must be false", errors)
    require(upload.get("github_upload_ready_next_gate") is False, "github upload ready gate must be false", errors)
    require(upload.get("github_upload_deferred_until_v014_stage1_18_complete") is True, "github upload deferral mismatch", errors)
    require(manifest.get("next_phase") == "S14_STAGE_REVIEW", "next phase mismatch", errors)
    require(manifest.get("next_required_step") == NEXT_REQUIRED_STEP, "next required step mismatch", errors)
    for block in REQUIRED_HARD_BLOCKS:
        require(block in manifest.get("hard_blocks", []), f"missing hard block {block}", errors)

    require(len(directories) == 5, "directory row count mismatch", errors)
    require(len(gaps) == 5, "gap row count mismatch", errors)
    require(len(risk_tips) == 5, "risk tip row count mismatch", errors)
    for row in [*directories, *gaps, *risk_tips]:
        require(row.get("formal_report_allowed") is False, "formal report must be false in output rows", errors)
        require(row.get("business_decision_basis_allowed") is False, "business basis must be false in output rows", errors)
        require(row.get("policy_application_submission_allowed") is False, "policy submission must be false in output rows", errors)
        require(row.get("raw_business_values_allowed", False) is False, "raw business values must be false in output rows", errors)
    for row in directories:
        require(row.get("formal_policy_conclusion_allowed") is False, "directory policy conclusion must be false", errors)
        require(row.get("field_plaintext_allowed") is False, "directory field plaintext must be false", errors)
    for row in gaps:
        require(row.get("eligibility_conclusion_allowed") is False, "gap eligibility conclusion must be false", errors)
        require(row.get("policy_score_allowed") is False, "gap policy score must be false", errors)
    for row in risk_tips:
        require(row.get("formal_policy_conclusion_allowed") is False, "risk policy conclusion must be false", errors)
        require(row.get("external_connector_action_allowed") is False, "risk connector action must be false", errors)

    for path in (
        REPORT_PATH,
        TEST_RESULTS_PATH,
        RISK_REGISTER_PATH,
        ROLLBACK_PATH,
        MANIFEST_PATH,
        DIRECTORIES_PATH,
        GAPS_PATH,
        RISK_TIPS_PATH,
    ):
        check_public_evidence_text(path, errors)
    html_text = HTML_OVERVIEW_PATH.read_text(encoding="utf-8", errors="ignore")
    lower = html_text.lower()
    for forbidden in FORBIDDEN_PUBLIC_TEXT:
        require(forbidden.lower() not in lower, f"forbidden text in HTML: {forbidden}", errors)

    if errors:
        raise ValidationError("KMFA v0.1.4 S14-P3 validation failed:\n- " + "\n- ".join(errors))

    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.4 S14-P3 policy evidence plan evidence.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args(argv)
    manifest = validate_v014_s14_p3_policy_evidence_plan(args.manifest)
    summary = manifest["policy_evidence_summary"]
    print(
        "PASS: KMFA v0.1.4 S14-P3 policy evidence plan validated "
        f"(policy_programs={summary['policy_program_count']}, directories={summary['evidence_directory_count']}, "
        f"gaps={summary['evidence_gap_count']}, risk_tips={summary['risk_tip_count']}, "
        f"pending_reconciliation={summary['pending_reconciliation_count']}, report_grade=D, "
        "policy_conclusion=false, policy_submission=false, stage14_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
