#!/usr/bin/env python3
"""Validate KMFA v0.1.4 Stage 6 review evidence."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from KMFA.tools.check_v014_s06_p1_zero_delta_validator import validate_v014_s06_p1_zero_delta_validator
from KMFA.tools.check_v014_s06_p2_difference_queue import validate_v014_s06_p2_difference_queue
from KMFA.tools.check_v014_s06_p3_validation_evidence import validate_v014_s06_p3_validation_evidence
from KMFA.tools.v014_s06_stage_review import (
    MANIFEST_PATH,
    NEXT_INSTRUCTION,
    NEXT_PHASE,
    PHASE_MANIFESTS,
    REPORT_PATH,
    RISK_REGISTER_PATH,
    ROLLBACK_PATH,
    SCHEMA_VERSION,
    TASK_ID,
    TEST_RESULTS_PATH,
)


FORBIDDEN_EXTENSIONS = {".zip", ".xlsx", ".xls", ".xlsm", ".pdf", ".sqlite", ".sqlite3", ".db"}
FORBIDDEN_TEXT = (
    "actual_package_" + "sha256",
    "member_" + "sha256:",
    "member_" + "name:",
    "member_" + "path:",
    "package_" + "name:",
    "candidate_" + "label:",
    "candidate_" + "label_hash:",
    "sheet_" + "name:",
    "raw_" + "value:",
    "normalized_" + "value:",
    "source_" + "header_text:",
    "cell_" + "value:",
    "row_" + "value:",
    "business_" + "value:",
    "bank_" + "statement:",
    "contract_" + "full_text:",
    "salary_" + "detail:",
    "tax_" + "filing:",
    "connector_" + "token:",
    "connector_" + "password:",
    "api_" + "key:",
    "private_" + "key:",
    "10000",
    "9999",
    "-----" "BEGIN",
    "s" "k-",
)
STRICT_SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(?i)(password|passwd|secret|api_key|token)\s*=\s*[^\s,;]{8,}"),
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
    "s06_p1_raw_inbox_read_by_phase",
    "s06_p1_raw_inbox_listed_by_phase",
    "s06_p1_raw_inbox_stat_by_phase",
    "s06_p1_raw_inbox_hashed_by_phase",
    "s06_p1_raw_inbox_mutated_by_phase",
    "s06_p2_raw_inbox_read_by_phase",
    "s06_p2_raw_inbox_listed_by_phase",
    "s06_p2_raw_inbox_stat_by_phase",
    "s06_p2_raw_inbox_hashed_by_phase",
    "s06_p2_raw_inbox_mutated_by_phase",
    "s06_p3_raw_inbox_read_by_phase",
    "s06_p3_raw_inbox_listed_by_phase",
    "s06_p3_raw_inbox_stat_by_phase",
    "s06_p3_raw_inbox_hashed_by_phase",
    "s06_p3_raw_inbox_mutated_by_phase",
)
PUBLIC_SAFETY_FALSE_KEYS = (
    "raw_business_data_committed",
    "raw_archive_or_workbook_committed",
    "raw_document_committed",
    "private_table_or_database_committed",
    "credentials_committed",
    "private_schema_text_committed",
    "raw_file_identifiers_committed",
    "raw_content_identifiers_committed",
    "private_record_content_committed",
    "business_content_committed",
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
    "s06_p1_validator",
    "s06_p2_validator",
    "s06_p3_validator",
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
    "public_stage6_semantic_scan",
    "diff_check",
)
FORBIDDEN_PUBLIC_KEYS = {
    "actual_package_" + "sha256",
    "member_" + "sha256",
    "member_" + "name",
    "member_" + "path",
    "package_" + "name",
    "candidate_" + "label",
    "candidate_" + "label_hash",
    "sheet_" + "name",
    "raw_" + "value",
    "normalized_" + "value",
    "source_" + "header_text",
    "cell_" + "value",
    "row_" + "value",
    "business_" + "value",
}


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


def walk_public(value: Any, errors: list[str], path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_PUBLIC_KEYS:
                errors.append(f"forbidden public key {key!r} at {path}")
            walk_public(child, errors, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            walk_public(child, errors, f"{path}[{index}]")


def check_public_safe_file(path: Path, errors: list[str]) -> None:
    require(path.exists(), f"missing evidence file: {path}", errors)
    if not path.exists():
        return
    require(path.suffix.lower() not in FORBIDDEN_EXTENSIONS, f"forbidden evidence extension: {path}", errors)
    if path.suffix.lower() not in {".md", ".json", ".jsonl", ".csv", ".yaml", ".yml"}:
        return
    text = path.read_text(encoding="utf-8", errors="ignore")
    lower = text.lower()
    for forbidden in FORBIDDEN_TEXT:
        require(forbidden.lower() not in lower, f"forbidden evidence text {forbidden!r} in {path}", errors)
    for pattern in STRICT_SECRET_PATTERNS:
        require(pattern.search(text) is None, f"secret-like pattern {pattern.pattern!r} in {path}", errors)


def validate_v014_s06_stage_review(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []
    manifest = read_json(manifest_path)
    p1 = validate_v014_s06_p1_zero_delta_validator()
    p2 = validate_v014_s06_p2_difference_queue()
    p3 = validate_v014_s06_p3_validation_evidence()
    p3_manifest = read_json(Path(PHASE_MANIFESTS["S06-P3"]))

    walk_public(manifest, errors)
    require(manifest.get("schema_version") == SCHEMA_VERSION, "schema mismatch", errors)
    require(manifest.get("project_id") == "KMFA", "project_id mismatch", errors)
    require(manifest.get("version") == "0.1.4", "version mismatch", errors)
    require(manifest.get("stage_id") == "S06", "stage_id must be S06", errors)
    require(manifest.get("review_id") == TASK_ID, "review_id mismatch", errors)
    require(manifest.get("task_id") == TASK_ID, "task_id mismatch", errors)
    require(manifest.get("acceptance_id") == "ACC-V014-S06-STAGE-REVIEW", "acceptance id mismatch", errors)
    require(manifest.get("review_scope") == "v014_s06_stage_review_only", "review scope mismatch", errors)
    require(
        manifest.get("status") == "review_passed_local_only_no_go_upload_deferred_until_v014_stage1_18_complete",
        "status mismatch",
        errors,
    )
    require(manifest.get("stage_review_performed") is True, "stage_review_performed must be true", errors)
    require(manifest.get("github_upload_performed") is False, "GitHub upload must not be performed", errors)
    require(
        manifest.get("github_upload_status") == "not_uploaded_deferred_until_v014_stage1_18_complete",
        "GitHub upload status mismatch",
        errors,
    )
    require(manifest.get("s07_p1_started") is False, "S07-P1 must not be started", errors)
    require(manifest.get("raw_content_matching_performed") is False, "raw content matching must not be performed", errors)
    require(manifest.get("lineage_full_check_performed") is False, "lineage full check must not be performed", errors)
    require(manifest.get("formal_report_performed") is False, "formal report must not be performed", errors)
    require(manifest.get("live_connector_called") is False, "live connector must not be called", errors)
    require(manifest.get("opme_deep_coupling_performed") is False, "OpMe deep coupling must not be performed", errors)
    require(manifest.get("business_execution_performed") is False, "business execution must not be performed", errors)
    require(manifest.get("phase_count") == 3, "phase_count must be 3", errors)
    require(
        manifest.get("phase_results") == {"S06-P1": "PASS", "S06-P2": "PASS", "S06-P3": "PASS"},
        "phase_results mismatch",
        errors,
    )
    require(p1.get("phase_id") == "S06-P1", "S06-P1 validator did not return S06-P1", errors)
    require(p2.get("phase_id") == "S06-P2", "S06-P2 validator did not return S06-P2", errors)
    require(p3.get("phase_id") == "S06-P3", "S06-P3 validator did not return S06-P3", errors)
    require(manifest.get("open_review_finding_count") == 0, "open findings must be 0", errors)
    require(manifest.get("fixed_review_finding_count") == 1, "fixed findings must be 1", errors)
    findings = manifest.get("review_findings", [])
    require(isinstance(findings, list) and len(findings) == 1, "review findings must contain one fixed finding", errors)
    if isinstance(findings, list) and findings:
        finding = findings[0]
        require(finding.get("finding_id") == "KMFA-V014-S06-STAGE-REVIEW-FIX-001", "finding id mismatch", errors)
        require(finding.get("status") == "fixed", "finding status must be fixed", errors)

    reviewed = manifest.get("reviewed_phase_manifests", {})
    for phase, path in PHASE_MANIFESTS.items():
        require(reviewed.get(phase) == str(path), f"{phase} manifest ref mismatch", errors)
        require(Path(path).exists(), f"missing phase manifest: {path}", errors)

    gate = manifest.get("stage_gate", {})
    require(gate.get("pass_fixture_field_comparison_count") == p1.get("pass_fixture_field_comparison_count") == 8, "field comparison count mismatch", errors)
    require(gate.get("pass_fixture_mismatch_count") == p1.get("pass_fixture_mismatch_count") == 0, "pass mismatch count mismatch", errors)
    require(gate.get("one_cent_mismatch_detected") is True, "one-cent mismatch must be detected", errors)
    require(gate.get("minimum_fail_difference_cents") == p1.get("minimum_fail_difference_cents") == 1, "minimum fail difference mismatch", errors)
    require(gate.get("mismatch_report_generated") is True, "mismatch report must be generated", errors)
    require(gate.get("queue_item_count") == p2.get("queue_item_count") == 1, "queue item count mismatch", errors)
    require(gate.get("minimum_queue_difference_cents") == p2.get("minimum_queue_difference_cents") == 1, "minimum queue difference mismatch", errors)
    require(gate.get("difference_closed") is False, "difference must remain open", errors)
    require(gate.get("manual_review_required") is True, "manual review must be required", errors)
    for key in ("auto_correction_allowed", "averaging_allowed", "rounding_mask_allowed", "auto_selection_allowed"):
        require(gate.get(key) is False, f"stage_gate.{key} must be false", errors)
    require(gate.get("metadata_quality_written") is True, "metadata quality must be written by S06-P3", errors)
    require(gate.get("metadata_zero_delta_records_written") == p3.get("metadata_zero_delta_records_written") == 1, "zero-delta metadata count mismatch", errors)
    require(gate.get("metadata_data_quality_records_written") == p3.get("metadata_data_quality_records_written") == 2, "data quality metadata count mismatch", errors)
    require(gate.get("metadata_source_difference_records_written") == p3.get("metadata_source_difference_records_written") == 1, "source difference metadata count mismatch", errors)
    require(gate.get("metadata_mismatch_rows_written") == p3.get("metadata_mismatch_rows_written") == 1, "metadata mismatch row count mismatch", errors)
    require(gate.get("project_status_count") == p3.get("project_status_count") == 2, "project status count mismatch", errors)
    require(gate.get("blocked_project_status_count") == p3.get("blocked_project_status_count") == 2, "blocked status count mismatch", errors)
    require(gate.get("mismatch_count") == p3_manifest.get("mismatch_count") == 1, "mismatch count mismatch", errors)
    require(gate.get("q5_allowed_count") == p3.get("q5_allowed_count") == 0, "Q5 allowed count must be 0", errors)
    require(gate.get("report_grade_a_allowed_count") == p3.get("report_grade_a_allowed_count") == 0, "report grade A allowed count must be 0", errors)
    require(gate.get("zero_delta_passed") is p3_manifest.get("zero_delta_passed") is False, "zero delta must remain failed", errors)
    require(set(gate.get("hard_blocks", [])) == {"zero_delta_failed", "unresolved_critical_difference"}, "hard blocks mismatch", errors)
    require(gate.get("current_data_quality_grade") == "Q4", "stage gate data quality mismatch", errors)
    require(gate.get("current_report_grade") == "D", "stage gate report grade mismatch", errors)
    require(gate.get("release_permission") == "blocked", "stage gate release permission mismatch", errors)

    release = manifest.get("release_state", {})
    for key in RELEASE_FALSE_KEYS:
        require(release.get(key) is False, f"release_state.{key} must be false", errors)
    require(release.get("current_go_no_go") == "NO_GO", "current Go/No-Go must be NO_GO", errors)
    require(release.get("current_data_quality_grade") == "Q4", "current data quality grade must be Q4", errors)
    require(release.get("current_report_grade") == "D", "current report grade must be D", errors)
    require(release.get("release_permission") == "blocked", "release permission must be blocked", errors)

    raw = manifest.get("raw_data_boundary", {})
    require(raw.get("raw_inbox_ref") == "operator-designated local raw/private inbox outside repository", "raw inbox ref mismatch", errors)
    require(raw.get("private_runtime_output_dir") == "KMFA/.codex_private_runtime/", "private runtime ref mismatch", errors)
    for key in RAW_REVIEW_FALSE_KEYS:
        require(raw.get(key) is False, f"raw_data_boundary.{key} must be false", errors)
    for key in PUBLIC_SAFETY_FALSE_KEYS:
        require(raw.get(key) is False, f"raw_data_boundary.{key} must be false", errors)

    safety = manifest.get("public_repo_safety", {})
    for key in PUBLIC_SAFETY_FALSE_KEYS:
        require(safety.get(key) is False, f"public_repo_safety.{key} must be false", errors)

    validation = manifest.get("validation_summary", {})
    for key in VALIDATION_KEYS:
        require(validation.get(key) == "PASS", f"validation_summary.{key} must be PASS", errors)

    require(manifest.get("next_recommended_phase") == NEXT_PHASE, "next recommended phase mismatch", errors)
    require(manifest.get("next_phase_instruction") == NEXT_INSTRUCTION, "next phase instruction mismatch", errors)

    for ref in manifest.get("evidence_refs", []):
        check_public_safe_file(Path(ref), errors)
    for path in (REPORT_PATH, TEST_RESULTS_PATH, RISK_REGISTER_PATH, ROLLBACK_PATH, MANIFEST_PATH):
        check_public_safe_file(path, errors)

    tracked_files = git_output(["ls-files", "KMFA"]).splitlines()
    forbidden_tracked = [
        path for path in tracked_files if path.lower().endswith(tuple(FORBIDDEN_EXTENSIONS)) or ".codex_private_runtime/" in path
    ]
    require(not forbidden_tracked, f"forbidden public/private tracked files: {forbidden_tracked}", errors)
    require("codex/kmfa" in git_output(["status", "--short", "--branch"]), "git status must be on codex/kmfa", errors)

    if errors:
        raise ValidationError("\n".join(errors))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.4 Stage 6 review evidence.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args()
    try:
        manifest = validate_v014_s06_stage_review(args.manifest)
    except ValidationError as exc:
        print("FAIL: KMFA v0.1.4 Stage 6 review validation failed")
        print(exc)
        return 1
    gate = manifest["stage_gate"]
    print(
        "PASS: KMFA v0.1.4 Stage 6 review validated "
        f"(phases={manifest['phase_count']}, findings_open={manifest['open_review_finding_count']}, "
        f"queue_items={gate['queue_item_count']}, blocked_statuses={gate['blocked_project_status_count']}, "
        f"q5_allowed={gate['q5_allowed_count']}, report_grade_a_allowed={gate['report_grade_a_allowed_count']}, "
        f"github_upload={str(manifest['github_upload_performed']).lower()}, "
        f"next={manifest['next_recommended_phase']}, go_no_go={manifest['release_state']['current_go_no_go']})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
