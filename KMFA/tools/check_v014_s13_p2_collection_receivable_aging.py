#!/usr/bin/env python3
"""Validate KMFA v0.1.4 S13-P2 collection receivable aging evidence."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from KMFA.tools.collection_receivable_aging import (
    REQUIRED_ISSUE_TYPES,
    REQUIRED_SOURCE_LANES,
    validate_collection_receivable_aging_artifacts,
)
from KMFA.tools.v014_s13_p2_collection_receivable_aging import (
    ACCEPTANCE_ID,
    HTML_PRIORITY_PATH,
    LANES_PATH,
    MANIFEST_PATH,
    NEXT_REQUIRED_STEP,
    PHASE_SCOPE,
    PRIORITY_PATH,
    REPORT_PATH,
    RESPONSIBILITY_PATH,
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
    validate_legacy_s13_p2_artifacts,
    validate_s13_p1_dependency,
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
    "legal_collection_decision_blocked",
    "payment_or_bank_operation_blocked",
    "invoice_operation_blocked",
    "tax_filing_blocked",
    "s13_p3_not_performed",
    "stage13_review_not_performed",
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
    return {"collection_receivable_aging_priority": HTML_PRIORITY_PATH.read_text(encoding="utf-8")}


def validate_v014_s13_p2_collection_receivable_aging(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []
    manifest = read_json(manifest_path)
    source_lanes = read_jsonl(LANES_PATH)
    priority_items = read_jsonl(PRIORITY_PATH)
    responsibility_items = read_jsonl(RESPONSIBILITY_PATH)
    html_outputs = _html_outputs()
    s13_p1 = validate_s13_p1_dependency()
    legacy_manifest, legacy_lanes, legacy_priority_items, legacy_responsibility_items, legacy_html = (
        validate_legacy_s13_p2_artifacts()
    )
    baseline = load_v14_html_uiux_baseline()

    validate_collection_receivable_aging_artifacts(
        legacy_manifest, source_lanes, priority_items, responsibility_items, html_outputs
    )
    validate_collection_receivable_aging_artifacts(
        legacy_manifest, legacy_lanes, legacy_priority_items, legacy_responsibility_items, legacy_html
    )

    require(manifest.get("schema_version") == SCHEMA_VERSION, "manifest schema mismatch", errors)
    require(manifest.get("project_id") == "KMFA", "project_id mismatch", errors)
    require(manifest.get("version") == "0.1.4", "version mismatch", errors)
    require(manifest.get("stage_id") == "S13", "stage_id must be S13", errors)
    require(manifest.get("phase_id") == "S13-P2", "phase_id must be S13-P2", errors)
    require(manifest.get("phase_scope") == PHASE_SCOPE, "phase scope mismatch", errors)
    require(manifest.get("task_id") == TASK_ID, "task_id mismatch", errors)
    require(manifest.get("acceptance_ids") == [ACCEPTANCE_ID], "acceptance id mismatch", errors)
    require(manifest.get("completed_task_ids") == ["S13P2T01", "S13P2T02", "S13P2T03"], "tasks mismatch", errors)
    require(
        manifest.get("status") == "completed_validated_local_only_no_go_upload_deferred_collection_receivable_aging_locked",
        "status mismatch",
        errors,
    )
    require(manifest.get("s13_p1_dependency_validated") is True, "S13-P1 dependency flag mismatch", errors)
    require(s13_p1.get("next_phase") == "S13-P2", "S13-P1 did not route to S13-P2", errors)
    require(manifest.get("legacy_s13_p2_dependency_validated") is True, "legacy S13-P2 flag mismatch", errors)
    require(manifest.get("v14_html_uiux_dependency_validated") is True, "v1.4 HTML/UIUX flag mismatch", errors)

    progress = manifest.get("stage13_phase_progress", {})
    require(progress.get("completed_phase_count") == 2, "completed phase count mismatch", errors)
    require(progress.get("total_phase_count") == 3, "total phase count mismatch", errors)
    require(progress.get("derived_percent_bps") == 6667, "derived percent bps mismatch", errors)
    require(progress.get("derived_percent_label") == "66.67%", "derived percent label mismatch", errors)
    require(progress.get("s13_p1_performed") is True, "S13-P1 must be performed", errors)
    require(progress.get("s13_p2_performed") is True, "S13-P2 must be performed", errors)
    require(progress.get("s13_p3_performed") is False, "S13-P3 must be false", errors)
    require(progress.get("stage13_review_performed") is False, "Stage 13 review must be false", errors)

    summary = manifest.get("collection_receivable_summary", {})
    expected_summary = {
        "source_lane_count": 5,
        "source_count": 5,
        "field_mapping_count": 25,
        "required_issue_type_count": 4,
        "priority_item_count": 4,
        "responsibility_item_count": 4,
        "html_draft_count": 1,
        "pending_reconciliation_count": 12,
        "report_grade_visible": "D",
        "formal_report_count": 0,
        "business_decision_basis_count": 0,
        "collection_action_count": 0,
        "legal_collection_decision_count": 0,
        "payment_or_bank_operation_count": 0,
    }
    for key, expected in expected_summary.items():
        require(summary.get(key) == expected, f"summary {key} mismatch", errors)
    require(summary.get("required_source_lanes") == list(REQUIRED_SOURCE_LANES), "required lanes mismatch", errors)
    require(summary.get("required_issue_types") == list(REQUIRED_ISSUE_TYPES), "required issue types mismatch", errors)

    manifest_baseline = manifest.get("v14_html_uiux_baseline", {})
    for key in ("audit_file_count", "audit_control_row_count", "audit_pass_count", "audit_warn_count", "audit_fail_count"):
        require(manifest_baseline.get(key) == baseline.get(key), f"baseline {key} mismatch", errors)
    require(
        manifest_baseline.get("implementation_reflects_collection_receivable_aging") is True,
        "collection receivable baseline flag mismatch",
        errors,
    )
    require(
        manifest_baseline.get("implementation_reflects_priority_and_responsibility") is True,
        "priority/responsibility baseline flag mismatch",
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
    require(manifest.get("next_phase") == "S13-P3", "next phase mismatch", errors)
    require(manifest.get("next_required_step") == NEXT_REQUIRED_STEP, "next required step mismatch", errors)
    for block in REQUIRED_HARD_BLOCKS:
        require(block in manifest.get("hard_blocks", []), f"missing hard block {block}", errors)

    require(len(source_lanes) == 5, "source lane row count mismatch", errors)
    require(len(priority_items) == 4, "priority item row count mismatch", errors)
    require(len(responsibility_items) == 4, "responsibility item row count mismatch", errors)
    for item in priority_items:
        require(str(item.get("html_draft_ref", "")) == HTML_PRIORITY_PATH.as_posix(), "priority html ref mismatch", errors)
    for path in (
        REPORT_PATH,
        TEST_RESULTS_PATH,
        RISK_REGISTER_PATH,
        ROLLBACK_PATH,
        MANIFEST_PATH,
        LANES_PATH,
        PRIORITY_PATH,
        RESPONSIBILITY_PATH,
        HTML_PRIORITY_PATH,
    ):
        check_public_evidence_text(path, errors)
    for html_text in html_outputs.values():
        lower = html_text.lower()
        for forbidden in FORBIDDEN_PUBLIC_TEXT:
            require(forbidden.lower() not in lower, f"forbidden text in HTML: {forbidden}", errors)
        for required in ("回款应收账龄", "已开票未回款", "责任事项", "不可作为催收、付款、法务或经营决策依据"):
            require(required in html_text, f"HTML missing required visible text: {required}", errors)

    if errors:
        raise ValidationError("KMFA v0.1.4 S13-P2 validation failed:\n- " + "\n- ".join(errors))

    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.4 S13-P2 collection receivable aging evidence.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args(argv)
    manifest = validate_v014_s13_p2_collection_receivable_aging(args.manifest)
    summary = manifest["collection_receivable_summary"]
    print(
        "PASS: KMFA v0.1.4 S13-P2 collection receivable aging validated "
        f"(source_lanes={summary['source_lane_count']}, sources={summary['source_count']}, "
        f"priority_items={summary['priority_item_count']}, responsibility_items={summary['responsibility_item_count']}, "
        f"field_mappings={summary['field_mapping_count']}, pending_reconciliation={summary['pending_reconciliation_count']}, "
        "report_grade=D, formal_report=false, legal_collection=false, payment_or_bank=false, "
        "s13_p3=false, stage13_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
