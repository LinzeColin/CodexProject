#!/usr/bin/env python3
"""Validate KMFA v0.1.4 S13-P1 financial operating report evidence."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from KMFA.tools.financial_operating_report import (
    REQUIRED_DRAFT_IDS,
    REQUIRED_SOURCE_LANES,
    validate_financial_operating_report_artifacts,
)
from KMFA.tools.v014_s13_p1_financial_operating_report import (
    ACCEPTANCE_ID,
    DRAFTS_PATH,
    EXPORT_HTML_DIR,
    LANES_PATH,
    MANIFEST_PATH,
    NEXT_REQUIRED_STEP,
    PHASE_SCOPE,
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
    validate_legacy_s13_p1_artifacts,
    validate_stage12_review_dependency,
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
    "s13_p2_not_performed",
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
    return {
        draft_id: (EXPORT_HTML_DIR / f"{draft_id}.html").read_text(encoding="utf-8")
        for draft_id in REQUIRED_DRAFT_IDS
    }


def validate_v014_s13_p1_financial_operating_report(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []
    manifest = read_json(manifest_path)
    source_lanes = read_jsonl(LANES_PATH)
    drafts = read_jsonl(DRAFTS_PATH)
    html_outputs = _html_outputs()
    stage12 = validate_stage12_review_dependency()
    legacy_manifest, legacy_lanes, legacy_drafts, legacy_html = validate_legacy_s13_p1_artifacts()
    baseline = load_v14_html_uiux_baseline()

    validate_financial_operating_report_artifacts(legacy_manifest, source_lanes, drafts, html_outputs)
    validate_financial_operating_report_artifacts(legacy_manifest, legacy_lanes, legacy_drafts, legacy_html)

    require(manifest.get("schema_version") == SCHEMA_VERSION, "manifest schema mismatch", errors)
    require(manifest.get("project_id") == "KMFA", "project_id mismatch", errors)
    require(manifest.get("version") == "0.1.4", "version mismatch", errors)
    require(manifest.get("stage_id") == "S13", "stage_id must be S13", errors)
    require(manifest.get("phase_id") == "S13-P1", "phase_id must be S13-P1", errors)
    require(manifest.get("phase_scope") == PHASE_SCOPE, "phase scope mismatch", errors)
    require(manifest.get("task_id") == TASK_ID, "task_id mismatch", errors)
    require(manifest.get("acceptance_ids") == [ACCEPTANCE_ID], "acceptance id mismatch", errors)
    require(manifest.get("completed_task_ids") == ["S13P1T01", "S13P1T02", "S13P1T03"], "tasks mismatch", errors)
    require(
        manifest.get("status") == "completed_validated_local_only_no_go_upload_deferred_financial_operating_report_locked",
        "status mismatch",
        errors,
    )
    require(manifest.get("s12_stage_review_dependency_validated") is True, "Stage 12 dependency flag mismatch", errors)
    require(stage12.get("next_phase") == "S13-P1", "Stage 12 review did not route to S13-P1", errors)
    require(manifest.get("legacy_s13_p1_dependency_validated") is True, "legacy S13-P1 flag mismatch", errors)
    require(manifest.get("v14_html_uiux_dependency_validated") is True, "v1.4 HTML/UIUX flag mismatch", errors)

    progress = manifest.get("stage13_phase_progress", {})
    require(progress.get("completed_phase_count") == 1, "completed phase count mismatch", errors)
    require(progress.get("total_phase_count") == 3, "total phase count mismatch", errors)
    require(progress.get("derived_percent_bps") == 3333, "derived percent bps mismatch", errors)
    require(progress.get("derived_percent_label") == "33.33%", "derived percent label mismatch", errors)
    require(progress.get("s13_p1_performed") is True, "S13-P1 must be performed", errors)
    require(progress.get("s13_p2_performed") is False, "S13-P2 must be false", errors)
    require(progress.get("s13_p3_performed") is False, "S13-P3 must be false", errors)
    require(progress.get("stage13_review_performed") is False, "Stage 13 review must be false", errors)

    summary = manifest.get("financial_operating_summary", {})
    expected_summary = {
        "source_lane_count": 4,
        "source_count": 8,
        "field_mapping_count": 39,
        "draft_report_count": 2,
        "html_draft_count": 2,
        "pending_reconciliation_count": 12,
        "report_grade_visible": "D",
        "formal_report_count": 0,
        "business_decision_basis_count": 0,
    }
    for key, expected in expected_summary.items():
        require(summary.get(key) == expected, f"summary {key} mismatch", errors)
    require(summary.get("required_source_lanes") == list(REQUIRED_SOURCE_LANES), "required lanes mismatch", errors)
    require(summary.get("required_draft_ids") == list(REQUIRED_DRAFT_IDS), "required drafts mismatch", errors)

    manifest_baseline = manifest.get("v14_html_uiux_baseline", {})
    for key in ("audit_file_count", "audit_control_row_count", "audit_pass_count", "audit_warn_count", "audit_fail_count"):
        require(manifest_baseline.get(key) == baseline.get(key), f"baseline {key} mismatch", errors)
    require(manifest_baseline.get("implementation_reflects_weekly_monthly_drafts") is True, "weekly/monthly baseline flag mismatch", errors)
    require(manifest_baseline.get("implementation_reflects_data_status_and_limits") is True, "data status baseline flag mismatch", errors)

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
    require(manifest.get("next_phase") == "S13-P2", "next phase mismatch", errors)
    require(manifest.get("next_required_step") == NEXT_REQUIRED_STEP, "next required step mismatch", errors)
    for block in REQUIRED_HARD_BLOCKS:
        require(block in manifest.get("hard_blocks", []), f"missing hard block {block}", errors)

    require(len(source_lanes) == 4, "source lane row count mismatch", errors)
    require(len(drafts) == 2, "draft row count mismatch", errors)
    for draft in drafts:
        require(
            str(draft.get("html_draft_ref", "")).startswith(
                "KMFA/stage_artifacts/V014_S13_P1_FINANCIAL_OPERATING_REPORT/exports/html/"
            ),
            "draft html ref must point to v014 evidence",
            errors,
        )
    for path in (REPORT_PATH, TEST_RESULTS_PATH, RISK_REGISTER_PATH, ROLLBACK_PATH, MANIFEST_PATH, LANES_PATH, DRAFTS_PATH):
        check_public_evidence_text(path, errors)
    for html_text in html_outputs.values():
        lower = html_text.lower()
        for forbidden in FORBIDDEN_PUBLIC_TEXT:
            require(forbidden.lower() not in lower, f"forbidden text in HTML: {forbidden}", errors)

    if errors:
        raise ValidationError("KMFA v0.1.4 S13-P1 validation failed:\n- " + "\n- ".join(errors))

    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.4 S13-P1 financial operating report evidence.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args(argv)
    manifest = validate_v014_s13_p1_financial_operating_report(args.manifest)
    summary = manifest["financial_operating_summary"]
    print(
        "PASS: KMFA v0.1.4 S13-P1 financial operating report validated "
        f"(source_lanes={summary['source_lane_count']}, drafts={summary['draft_report_count']}, "
        f"html={summary['html_draft_count']}, field_mappings={summary['field_mapping_count']}, "
        f"pending_reconciliation={summary['pending_reconciliation_count']}, report_grade=D, "
        "formal_report=false, s13_p2=false, s13_p3=false, stage13_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
