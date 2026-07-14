#!/usr/bin/env python3
"""Validate KMFA v0.1.4 S18-P2 full-regression acceptance evidence."""

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

from KMFA.tools.v014_s18_p2_full_regression_acceptance import (  # noqa: E402
    ACCEPTANCE_ID,
    CHECK_RESULTS_PATH,
    GO_NO_GO_PATH,
    GO_NO_GO_RECORD_PATH,
    HTML_AUDIT_CSV_PATH,
    HTML_AUDIT_RECORD_PATH,
    HTML_AUDIT_SUMMARY_PATH,
    MACHINE_DIR,
    MANIFEST_PATH,
    METADATA_CHECK_RESULTS_PATH,
    METADATA_GO_NO_GO_PATH,
    METADATA_HTML_AUDIT_SUMMARY_PATH,
    METADATA_MANIFEST_PATH,
    METADATA_STAGE_EVIDENCE_PATH,
    NEXT_PHASE,
    NEXT_REQUIRED_STEP,
    PHASE_SCOPE,
    REPORT_PATH,
    REQUIRED_HTML_BASELINE_FILES,
    REQUIRED_V014_CHECK_CATEGORIES,
    REQUIRED_V014_STAGE_IDS,
    RISK_REGISTER_PATH,
    ROLLBACK_PATH,
    SCHEMA_VERSION,
    STAGE_EVIDENCE_PATH,
    TASK_ID,
    TEST_RESULTS_PATH,
    V14_HTML_DIR,
    _phase_boundaries,
    _public_repo_safety,
    _quality_gate,
    _raw_boundary,
    load_v14_taskpack_baseline,
    validate_historical_s18_p2_public_safe_baseline,
    validate_s18_p1_dependency,
)


PUBLIC_SAFETY_FALSE_KEYS = tuple(key for key, value in _public_repo_safety().items() if value is False)
RAW_BOUNDARY_FALSE_KEYS = tuple(key for key, value in _raw_boundary().items() if value is False)
QUALITY_TRUE_KEYS = tuple(key for key, value in _quality_gate().items() if value is True)
QUALITY_FALSE_KEYS = tuple(key for key, value in _quality_gate().items() if value is False)
PHASE_TRUE_KEYS = tuple(key for key, value in _phase_boundaries().items() if value is True)
PHASE_FALSE_KEYS = tuple(key for key, value in _phase_boundaries().items() if value is False)

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
    "bank_statement_payload",
    "contract_full_text",
    "salary_detail",
    "tax_filing_material",
    "connector_" + "token:",
    "connector_" + "pass" + "word:",
    "api" + "_key:",
    "private" + "_key:",
    "credential_material",
    "report_attachment_path",
    "production_restore_material",
    "external_service_material",
    "live_connector_material",
    "app_reinstall_material",
    "-----" "BEGIN",
    "s" "k-",
    "project_name_plaintext",
    "customer_name_plaintext",
    "counterparty_plaintext",
    "company_entity_plaintext",
    "supplier_name_plaintext",
    "payment_account",
    "account_number:",
    "invoice_number:",
    "tax_identifier:",
    "private_ref://",
    "recipient_" + "email",
    "smtp",
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


def _require_false_keys(record: dict[str, Any], keys: tuple[str, ...], label: str, errors: list[str]) -> None:
    for key in keys:
        require(record.get(key) is False, f"{label}.{key} must be false", errors)


def _require_true_keys(record: dict[str, Any], keys: tuple[str, ...], label: str, errors: list[str]) -> None:
    for key in keys:
        require(record.get(key) is True, f"{label}.{key} must be true", errors)


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


def validate_v014_s18_p2_full_regression_acceptance(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []
    manifest = read_json(manifest_path)
    metadata_manifest = read_json(METADATA_MANIFEST_PATH)
    check_results = read_jsonl(CHECK_RESULTS_PATH)
    metadata_check_results = read_jsonl(METADATA_CHECK_RESULTS_PATH)
    stage_evidence = read_jsonl(STAGE_EVIDENCE_PATH)
    metadata_stage_evidence = read_jsonl(METADATA_STAGE_EVIDENCE_PATH)
    go_no_go = read_json(GO_NO_GO_PATH)
    metadata_go_no_go = read_json(METADATA_GO_NO_GO_PATH)
    html_audit_summary = read_json(HTML_AUDIT_SUMMARY_PATH)
    metadata_html_audit_summary = read_json(METADATA_HTML_AUDIT_SUMMARY_PATH)
    s18_p1 = validate_s18_p1_dependency()
    legacy_manifest, legacy_checks, legacy_stage_rows, legacy_go_no_go = (
        validate_historical_s18_p2_public_safe_baseline()
    )
    baseline = load_v14_taskpack_baseline()

    require(metadata_manifest == manifest, "metadata manifest copy must match machine manifest", errors)
    require(metadata_check_results == check_results, "metadata check result copy must match machine checks", errors)
    require(metadata_stage_evidence == stage_evidence, "metadata stage evidence copy must match machine evidence", errors)
    require(metadata_go_no_go == go_no_go, "metadata Go/No-Go copy must match machine Go/No-Go", errors)
    require(metadata_html_audit_summary == html_audit_summary, "metadata HTML audit copy must match machine summary", errors)
    require(manifest.get("schema_version") == SCHEMA_VERSION, "manifest schema mismatch", errors)
    require(manifest.get("project_id") == "KMFA", "project_id mismatch", errors)
    require(manifest.get("version") == "0.1.4", "version mismatch", errors)
    require(manifest.get("stage_id") == "S18", "stage_id must be S18", errors)
    require(manifest.get("phase_id") == "S18-P2", "phase_id mismatch", errors)
    require(manifest.get("phase_scope") == PHASE_SCOPE, "phase_scope mismatch", errors)
    require(manifest.get("task_id") == TASK_ID, "task_id mismatch", errors)
    require(manifest.get("acceptance_ids") == [ACCEPTANCE_ID], "acceptance id mismatch", errors)
    require(manifest.get("completed_task_ids") == ["S18P2T01", "S18P2T02", "S18P2T03"], "task ids mismatch", errors)
    require(manifest.get("next_phase") == NEXT_PHASE, "next phase mismatch", errors)
    require(manifest.get("next_required_step") == NEXT_REQUIRED_STEP, "next required step mismatch", errors)
    require(manifest.get("branch") == git_output(["branch", "--show-current"]), "manifest branch mismatch", errors)
    require(manifest.get("s18_p1_dependency_validated") is True, "S18-P1 dependency flag missing", errors)
    require(s18_p1.get("next_phase") == "S18-P2", "S18-P1 dependency must route to S18-P2", errors)
    require(
        manifest.get("historical_s18_p2_public_safe_baseline_validated") is True,
        "legacy S18-P2 baseline validation flag missing",
        errors,
    )
    require(
        manifest.get("required_check_categories") == list(REQUIRED_V014_CHECK_CATEGORIES),
        "required check categories mismatch",
        errors,
    )
    require(manifest.get("required_stage_ids") == list(REQUIRED_V014_STAGE_IDS), "required stage ids mismatch", errors)

    require(legacy_manifest.get("stage_phase") == "S18-P2", "legacy manifest stage phase mismatch", errors)
    require(len(legacy_checks) == 5, "legacy check count mismatch", errors)
    require(len(legacy_stage_rows) == 18, "legacy stage evidence count mismatch", errors)
    require(legacy_go_no_go.get("decision") == "NO_GO", "legacy Go/No-Go mismatch", errors)

    summary = manifest.get("full_regression_summary", {})
    require(summary.get("check_category_count") == 5, "check category count mismatch", errors)
    require(summary.get("stage_evidence_count") == 18, "stage evidence count mismatch", errors)
    require(summary.get("html_audit_file_count") == 6, "HTML audit file count mismatch", errors)
    require(summary.get("html_audit_row_count") == 54, "HTML audit row count mismatch", errors)
    require(summary.get("html_audit_pass_count") == 54, "HTML audit pass count mismatch", errors)
    require(summary.get("html_audit_warn_count") == 0, "HTML audit warn count mismatch", errors)
    require(summary.get("html_audit_fail_count") == 0, "HTML audit fail count mismatch", errors)
    require(summary.get("go_no_go_decision") == "NO_GO", "Go/No-Go decision mismatch", errors)
    require(summary.get("maximum_report_grade") == "D", "maximum report grade mismatch", errors)
    require(summary.get("next_required_phase") == NEXT_PHASE, "next required phase mismatch", errors)

    progress = manifest.get("stage18_phase_progress", {})
    require(progress.get("completed_phase_count") == 2, "completed phase count mismatch", errors)
    require(progress.get("total_phase_count") == 3, "total phase count mismatch", errors)
    require(progress.get("derived_percent_bps") == 6667, "progress bps mismatch", errors)
    require(progress.get("derived_percent_label") == "66.67%", "progress label mismatch", errors)
    require(progress.get("s18_p1_performed") is True, "S18-P1 must be performed", errors)
    require(progress.get("s18_p2_performed") is True, "S18-P2 must be performed", errors)
    require(progress.get("s18_p3_performed") is False, "S18-P3 must not be performed", errors)
    require(progress.get("stage18_review_performed") is False, "Stage 18 review must not be performed", errors)

    quality = manifest.get("quality_gate", {})
    _require_true_keys(quality, QUALITY_TRUE_KEYS, "quality_gate", errors)
    _require_false_keys(quality, QUALITY_FALSE_KEYS, "quality_gate", errors)
    raw_boundary = manifest.get("raw_data_boundary", {})
    _require_false_keys(raw_boundary, RAW_BOUNDARY_FALSE_KEYS, "raw_data_boundary", errors)
    phase_boundaries = manifest.get("phase_boundaries", {})
    _require_true_keys(phase_boundaries, PHASE_TRUE_KEYS, "phase_boundaries", errors)
    _require_false_keys(phase_boundaries, PHASE_FALSE_KEYS, "phase_boundaries", errors)
    safety = manifest.get("public_repo_safety", {})
    _require_false_keys(safety, PUBLIC_SAFETY_FALSE_KEYS, "public_repo_safety", errors)

    categories = {str(row.get("check_category")) for row in check_results}
    require(categories == set(REQUIRED_V014_CHECK_CATEGORIES), "check category set mismatch", errors)
    require({row.get("record_type") for row in check_results} == {"v014_s18_p2_regression_check_result"}, "check record type mismatch", errors)
    for row in check_results:
        require(row.get("project_id") == "KMFA", "check project mismatch", errors)
        require(row.get("stage_id") == "S18", "check stage mismatch", errors)
        require(row.get("phase_id") == "S18-P2", "check phase mismatch", errors)
        require(row.get("task_id") == "S18P2T01", "check task mismatch", errors)
        require(row.get("execution_mode") == "public_safe_local_validation", "check execution mode mismatch", errors)
        require(row.get("raw_business_data_used") is False, "check raw use must be false", errors)
        require(row.get("raw_inbox_accessed") is False, "check raw inbox access must be false", errors)
        require(row.get("external_service_called") is False, "check external service must be false", errors)
        require(row.get("github_upload_performed") is False, "check GitHub upload must be false", errors)
        require(row.get("phase_completion_upload_allowed") is False, "check phase upload allowed must be false", errors)
    ui_check = next(row for row in check_results if row.get("check_category") == "ui")
    require(ui_check.get("result") == "passed", "UI check must pass", errors)

    stage_ids = [str(row.get("stage_id")) for row in stage_evidence]
    require(tuple(stage_ids) == REQUIRED_V014_STAGE_IDS, "stage id ordering mismatch", errors)
    require(
        {row.get("record_type") for row in stage_evidence} == {"v014_s18_p2_stage_acceptance_evidence"},
        "stage evidence record type mismatch",
        errors,
    )
    for row in stage_evidence:
        require(row.get("project_id") == "KMFA", "stage evidence project mismatch", errors)
        require(row.get("phase_id") == "S18-P2", "stage evidence phase mismatch", errors)
        require(row.get("task_id") == "S18P2T02", "stage evidence task mismatch", errors)
        require(row.get("acceptance_confirmed") is True, "stage acceptance must be confirmed", errors)
        require(row.get("raw_business_data_committed") is False, "stage raw data committed must be false", errors)
        require(row.get("github_upload_performed_in_s18_p2") is False, "stage upload during S18-P2 must be false", errors)
    s18_row = stage_evidence[-1]
    require(s18_row.get("stage_id") == "S18", "last stage evidence must be S18", errors)
    require("S18-P1" in s18_row.get("completed_phase_ids", []), "S18-P1 completion missing", errors)
    require("S18-P2" in s18_row.get("completed_phase_ids", []), "S18-P2 completion missing", errors)
    require("S18-P3" not in s18_row.get("completed_phase_ids", []), "S18-P3 must not be completed", errors)
    require(s18_row.get("pending_phase_ids") == ["S18-P3"], "S18 pending phase mismatch", errors)

    require(go_no_go == manifest.get("go_no_go"), "manifest Go/No-Go must match file", errors)
    require(go_no_go.get("decision") == "NO_GO", "Go/No-Go must be NO_GO", errors)
    require(go_no_go.get("delivery_allowed") is False, "delivery must be false", errors)
    require(go_no_go.get("business_decision_basis_allowed") is False, "business basis must be false", errors)
    require(go_no_go.get("github_upload_allowed") is False, "github upload allowed must be false", errors)
    for blocker in ("LINEAGE_FULL_CHECK_NOT_COMPLETE", "OFFICIAL_REPORT_RELEASE_NOT_ALLOWED", "S18_P3_PENDING"):
        require(blocker in go_no_go.get("blocker_ids", []), f"missing blocker {blocker}", errors)

    require(html_audit_summary == manifest.get("html_human_flow_audit"), "manifest HTML audit must match file", errors)
    require(html_audit_summary.get("audit_executed") is True, "HTML audit must execute", errors)
    require(html_audit_summary.get("file_count") == 6, "HTML audit file count must be 6", errors)
    require(html_audit_summary.get("row_count") == 54, "HTML audit rows must be 54", errors)
    require(html_audit_summary.get("pass_count") == 54, "HTML audit pass count must be 54", errors)
    require(html_audit_summary.get("warn_count") == 0, "HTML audit warn count must be 0", errors)
    require(html_audit_summary.get("fail_count") == 0, "HTML audit fail count must be 0", errors)
    require(HTML_AUDIT_CSV_PATH.exists(), "HTML audit CSV missing", errors)
    for file_name in REQUIRED_HTML_BASELINE_FILES:
        require((V14_HTML_DIR / file_name).exists(), f"missing v1.4 HTML baseline {file_name}", errors)
    require(baseline == manifest.get("v14_taskpack_baseline"), "v1.4 taskpack baseline mismatch", errors)

    github = manifest.get("github_upload", {})
    require(github.get("github_upload_performed") is False, "GitHub upload must be false", errors)
    require(
        github.get("github_upload_status") == "not_uploaded_deferred_until_v014_stage1_18_complete",
        "GitHub upload status mismatch",
        errors,
    )
    require(github.get("github_upload_deferred_until_v014_stage1_18_complete") is True, "upload defer flag missing", errors)

    for path in (
        REPORT_PATH,
        HTML_AUDIT_RECORD_PATH,
        GO_NO_GO_RECORD_PATH,
        TEST_RESULTS_PATH,
        RISK_REGISTER_PATH,
        ROLLBACK_PATH,
        MANIFEST_PATH,
        CHECK_RESULTS_PATH,
        STAGE_EVIDENCE_PATH,
        GO_NO_GO_PATH,
        HTML_AUDIT_SUMMARY_PATH,
        HTML_AUDIT_CSV_PATH,
    ):
        check_public_evidence_text(path, errors)

    require(MACHINE_DIR.exists(), "machine evidence dir missing", errors)

    if errors:
        raise ValidationError("\n".join(errors))
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.4 S18-P2 full-regression acceptance evidence.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args(argv)
    manifest = validate_v014_s18_p2_full_regression_acceptance(args.manifest)
    summary = manifest["full_regression_summary"]
    print(
        "PASS: KMFA v0.1.4 S18-P2 full regression acceptance validated "
        f"(checks={summary['check_category_count']}, "
        f"stages={summary['stage_evidence_count']}, "
        f"html_files={summary['html_audit_file_count']}, "
        f"html_rows={summary['html_audit_row_count']}, "
        f"html_fail={summary['html_audit_fail_count']}, "
        f"decision={summary['go_no_go_decision']}, "
        "s18_p3=False, stage18_review=False, github_upload=False)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
