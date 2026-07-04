#!/usr/bin/env python3
"""Validate KMFA v0.1.4 S13-P3 cross-table review evidence."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from KMFA.tools.cross_table_review import (
    REQUIRED_REVIEW_DIMENSIONS,
    validate_cross_table_review_artifacts,
)
from KMFA.tools.v014_s13_p3_cross_table_review import (
    ACCEPTANCE_ID,
    CHECKS_PATH,
    DIFFERENCE_QUEUE_PATH,
    HTML_QUALITY_PATH,
    MANIFEST_PATH,
    NEXT_REQUIRED_STEP,
    PHASE_SCOPE,
    QUALITY_REPORT_PATH,
    REPORT_PATH,
    RISK_REGISTER_PATH,
    ROLLBACK_PATH,
    SCHEMA_VERSION,
    TASK_ID,
    TEST_RESULTS_PATH,
    _phase_boundaries,
    _public_repo_safety,
    _quality_gate,
    _raw_boundary,
    load_v14_html_uiux_baseline,
    validate_legacy_s13_p3_artifacts,
    validate_s13_p2_dependency,
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
    "difference_auto_resolution_blocked",
    "difference_closure_blocked",
    "legal_collection_decision_blocked",
    "payment_or_bank_operation_blocked",
    "invoice_operation_blocked",
    "tax_filing_blocked",
    "stage13_review_not_performed",
    "s14_not_performed",
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
    "tax_filing_material",
    "tax_filing_record",
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
    return {"cross_table_quality_report": HTML_QUALITY_PATH.read_text(encoding="utf-8")}


def validate_v014_s13_p3_cross_table_review(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []
    manifest = read_json(manifest_path)
    review_checks = read_jsonl(CHECKS_PATH)
    difference_queue = read_jsonl(DIFFERENCE_QUEUE_PATH)
    quality_report = read_json(QUALITY_REPORT_PATH)
    html_outputs = _html_outputs()
    s13_p2 = validate_s13_p2_dependency()
    legacy_manifest, legacy_checks, legacy_queue, legacy_quality_report, legacy_html = validate_legacy_s13_p3_artifacts()
    baseline = load_v14_html_uiux_baseline()

    validate_cross_table_review_artifacts(
        legacy_manifest, review_checks, difference_queue, quality_report, html_outputs
    )
    validate_cross_table_review_artifacts(
        legacy_manifest, legacy_checks, legacy_queue, legacy_quality_report, legacy_html
    )

    require(manifest.get("schema_version") == SCHEMA_VERSION, "manifest schema mismatch", errors)
    require(manifest.get("project_id") == "KMFA", "project_id mismatch", errors)
    require(manifest.get("version") == "0.1.4", "version mismatch", errors)
    require(manifest.get("stage_id") == "S13", "stage_id must be S13", errors)
    require(manifest.get("phase_id") == "S13-P3", "phase_id must be S13-P3", errors)
    require(manifest.get("phase_scope") == PHASE_SCOPE, "phase scope mismatch", errors)
    require(manifest.get("task_id") == TASK_ID, "task_id mismatch", errors)
    require(manifest.get("acceptance_ids") == [ACCEPTANCE_ID], "acceptance id mismatch", errors)
    require(manifest.get("completed_task_ids") == ["S13P3T01", "S13P3T02", "S13P3T03"], "tasks mismatch", errors)
    require(
        manifest.get("status") == "completed_validated_local_only_no_go_upload_deferred_cross_table_review_locked",
        "status mismatch",
        errors,
    )
    require(manifest.get("s13_p2_dependency_validated") is True, "S13-P2 dependency flag mismatch", errors)
    require(s13_p2.get("next_phase") == "S13-P3", "S13-P2 did not route to S13-P3", errors)
    require(manifest.get("legacy_s13_p3_dependency_validated") is True, "legacy S13-P3 flag mismatch", errors)
    require(manifest.get("v14_html_uiux_dependency_validated") is True, "v1.4 HTML/UIUX flag mismatch", errors)

    progress = manifest.get("stage13_phase_progress", {})
    require(progress.get("completed_phase_count") == 3, "completed phase count mismatch", errors)
    require(progress.get("total_phase_count") == 3, "total phase count mismatch", errors)
    require(progress.get("derived_percent_bps") == 10000, "derived percent bps mismatch", errors)
    require(progress.get("derived_percent_label") == "100.00%", "derived percent label mismatch", errors)
    require(progress.get("s13_p1_performed") is True, "S13-P1 must be performed", errors)
    require(progress.get("s13_p2_performed") is True, "S13-P2 must be performed", errors)
    require(progress.get("s13_p3_performed") is True, "S13-P3 must be performed", errors)
    require(progress.get("stage13_review_performed") is False, "Stage 13 review must be false", errors)

    summary = manifest.get("cross_table_review_summary", {})
    expected_summary = {
        "review_dimension_count": 4,
        "difference_queue_count": 4,
        "quality_report_count": 1,
        "html_draft_count": 1,
        "pending_reconciliation_count": 12,
        "report_grade_visible": "D",
        "formal_report_count": 0,
        "business_decision_basis_count": 0,
        "difference_auto_resolution_count": 0,
        "difference_closure_count": 0,
        "payment_or_bank_operation_count": 0,
        "legal_collection_decision_count": 0,
    }
    for key, expected in expected_summary.items():
        require(summary.get(key) == expected, f"summary {key} mismatch", errors)
    require(
        summary.get("required_review_dimensions") == list(REQUIRED_REVIEW_DIMENSIONS),
        "required review dimensions mismatch",
        errors,
    )

    manifest_baseline = manifest.get("v14_html_uiux_baseline", {})
    for key in ("audit_file_count", "audit_control_row_count", "audit_pass_count", "audit_warn_count", "audit_fail_count"):
        require(manifest_baseline.get(key) == baseline.get(key), f"baseline {key} mismatch", errors)
    require(
        manifest_baseline.get("implementation_reflects_cross_table_review") is True,
        "cross-table baseline flag mismatch",
        errors,
    )
    require(
        manifest_baseline.get("implementation_reflects_difference_queue") is True,
        "difference queue baseline flag mismatch",
        errors,
    )
    require(
        manifest_baseline.get("implementation_reflects_no_external_action_limits") is True,
        "external action limits baseline flag mismatch",
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
    require(manifest.get("next_phase") == "S13_STAGE_REVIEW", "next phase mismatch", errors)
    require(manifest.get("next_required_step") == NEXT_REQUIRED_STEP, "next required step mismatch", errors)
    for block in REQUIRED_HARD_BLOCKS:
        require(block in manifest.get("hard_blocks", []), f"missing hard block {block}", errors)

    require(len(review_checks) == 4, "review check row count mismatch", errors)
    require(len(difference_queue) == 4, "difference queue row count mismatch", errors)
    for check in review_checks:
        require(str(check.get("html_quality_ref", "")) == HTML_QUALITY_PATH.as_posix(), "quality html ref mismatch", errors)
        require(check.get("difference_auto_resolution_allowed") is False, "check auto resolution must be false", errors)
    for item in difference_queue:
        require(item.get("resolution_status") == "pending_owner_or_authorized_review", "queue status mismatch", errors)
        require(item.get("auto_resolution_allowed") is False, "queue auto resolution must be false", errors)
        require(item.get("auto_source_selection_allowed") is False, "queue auto source selection must be false", errors)
    require(quality_report.get("html_quality_ref") == HTML_QUALITY_PATH.as_posix(), "quality report html ref mismatch", errors)

    for path in (
        REPORT_PATH,
        TEST_RESULTS_PATH,
        RISK_REGISTER_PATH,
        ROLLBACK_PATH,
        MANIFEST_PATH,
        CHECKS_PATH,
        DIFFERENCE_QUEUE_PATH,
        QUALITY_REPORT_PATH,
        HTML_QUALITY_PATH,
    ):
        check_public_evidence_text(path, errors)
    for html_text in html_outputs.values():
        lower = html_text.lower()
        for forbidden in FORBIDDEN_PUBLIC_TEXT:
            require(forbidden.lower() not in lower, f"forbidden text in HTML: {forbidden}", errors)
        for required in ("跨表复核", "项目一致性", "客户一致性", "金额一致性", "时间一致性", "不可作为正式经营报告或经营决策依据"):
            require(required in html_text, f"HTML missing required visible text: {required}", errors)

    if errors:
        raise ValidationError("KMFA v0.1.4 S13-P3 validation failed:\n- " + "\n- ".join(errors))

    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.4 S13-P3 cross-table review evidence.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args(argv)
    manifest = validate_v014_s13_p3_cross_table_review(args.manifest)
    summary = manifest["cross_table_review_summary"]
    print(
        "PASS: KMFA v0.1.4 S13-P3 cross-table review validated "
        f"(review_dimensions={summary['review_dimension_count']}, "
        f"difference_queue={summary['difference_queue_count']}, "
        f"quality_report={summary['quality_report_count']}, "
        f"pending_reconciliation={summary['pending_reconciliation_count']}, "
        "report_grade=D, formal_report=false, difference_auto_resolution=false, "
        "stage13_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
