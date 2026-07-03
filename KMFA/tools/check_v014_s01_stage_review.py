#!/usr/bin/env python3
"""Validate KMFA v1.4 Stage 1 overall review evidence."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from KMFA.tools.check_v014_s01_p1_read_only_scope_lock import validate_v014_s01_p1_read_only_scope_lock
from KMFA.tools.check_v014_s01_p2_public_baseline_sync import validate_v014_s01_p2_public_baseline_sync
from KMFA.tools.check_v014_s01_p3_no_omission_baseline import validate_v014_s01_p3_no_omission_baseline


MANIFEST_PATH = Path("KMFA/stage_artifacts/V014_S01_STAGE_REVIEW/machine/stage1_review_manifest.json")
REPORT_PATH = Path("KMFA/stage_artifacts/V014_S01_STAGE_REVIEW/human/stage1_review_report.md")
TEST_RESULTS_PATH = Path("KMFA/stage_artifacts/V014_S01_STAGE_REVIEW/human/test_results.md")
RISK_REGISTER_PATH = Path("KMFA/stage_artifacts/V014_S01_STAGE_REVIEW/human/risk_register.md")
ROLLBACK_PATH = Path("KMFA/stage_artifacts/V014_S01_STAGE_REVIEW/human/rollback_plan.md")
PHASE_MANIFESTS = {
    "S01-P1": Path(
        "KMFA/stage_artifacts/V014_S01_P1_READ_ONLY_SCOPE_LOCK/machine/"
        "s01_p1_read_only_scope_lock_manifest.json"
    ),
    "S01-P2": Path(
        "KMFA/stage_artifacts/V014_S01_P2_PUBLIC_BASELINE_SYNC/machine/"
        "s01_p2_public_baseline_sync_manifest.json"
    ),
    "S01-P3": Path(
        "KMFA/stage_artifacts/V014_S01_P3_NO_OMISSION_BASELINE/machine/"
        "s01_p3_no_omission_baseline_manifest.json"
    ),
}
FORBIDDEN_EXTENSIONS = {".zip", ".xlsx", ".xls", ".xlsm", ".pdf", ".sqlite", ".sqlite3", ".db"}
FORBIDDEN_TEXT = (
    "raw_value:",
    "normalized_value:",
    "source_header_text:",
    "original_filename",
    "member_path",
    "member_name",
    "sheet_name:",
    "row_value:",
    "cell_value:",
    "bank_statement:",
    "contract_full_text:",
    "salary_detail:",
    "tax_filing:",
    "connector_token:",
    "connector_password:",
    "api_key:",
    "private_key:",
    "-----" "BEGIN",
    "s" "k-",
)
FALSE_BOUNDARY_KEYS = (
    "raw_inbox_read_by_this_review",
    "raw_inbox_listed_by_this_review",
    "raw_inbox_modified_by_this_review",
    "raw_inbox_deleted_by_this_review",
    "raw_inbox_moved_by_this_review",
    "raw_inbox_renamed_by_this_review",
    "raw_inbox_overwritten_by_this_review",
    "raw_inbox_written_by_this_review",
    "raw_payload_extracted_from_delivery_zip",
    "raw_filenames_committed",
    "raw_hashes_committed",
    "field_or_header_plaintext_committed",
    "business_values_committed",
    "zip_committed",
    "excel_workbook_committed",
    "pdf_committed",
    "private_csv_committed",
    "sqlite_or_db_committed",
    "credentials_committed",
)
PUBLIC_SAFETY_FALSE_KEYS = (
    "raw_business_data_committed",
    "zip_committed",
    "excel_workbook_committed",
    "pdf_committed",
    "private_csv_committed",
    "sqlite_or_db_committed",
    "credentials_committed",
    "raw_filenames_committed",
    "raw_hashes_committed",
    "field_plaintext_committed",
    "normalized_business_values_committed",
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


def check_public_safe_file(path: Path, errors: list[str]) -> None:
    require(path.exists(), f"missing evidence file: {path}", errors)
    if not path.exists():
        return
    require(path.suffix.lower() not in FORBIDDEN_EXTENSIONS, f"forbidden evidence extension: {path}", errors)
    if path.suffix.lower() in {".md", ".json", ".jsonl", ".csv", ".yaml", ".yml"}:
        text = path.read_text(encoding="utf-8").lower()
        for forbidden in FORBIDDEN_TEXT:
            require(forbidden.lower() not in text, f"forbidden evidence text {forbidden!r} in {path}", errors)


def validate_v014_s01_stage_review(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []
    manifest = read_json(manifest_path)
    p1_result = validate_v014_s01_p1_read_only_scope_lock()
    p2_result = validate_v014_s01_p2_public_baseline_sync()
    p3_result = validate_v014_s01_p3_no_omission_baseline()

    require(manifest.get("schema_version") == "kmfa.v014_s01_stage_review.v1", "schema mismatch", errors)
    require(manifest.get("project_id") == "KMFA", "project_id mismatch", errors)
    require(manifest.get("version") == "0.1.4", "version mismatch", errors)
    require(manifest.get("stage_id") == "S01", "stage_id must be S01", errors)
    require(manifest.get("review_id") == "KMFA-V014-S01-STAGE-REVIEW-20260703", "review_id mismatch", errors)
    require(manifest.get("task_id") == "KMFA-V014-S01-STAGE-REVIEW-20260703", "task_id mismatch", errors)
    require(manifest.get("review_scope") == "v014_s01_stage_review_only", "review scope mismatch", errors)
    require(
        manifest.get("status") == "review_passed_local_only_no_go_upload_deferred_until_v014_stage1_18_complete",
        "status mismatch",
        errors,
    )
    require(manifest.get("stage_review_performed") is True, "stage_review_performed must be true", errors)
    require(manifest.get("github_upload_performed") is False, "GitHub upload must not be performed", errors)
    require(manifest.get("s02_started") is False, "S02 must not be started", errors)
    require(manifest.get("raw_inventory_performed") is False, "raw inventory must not be performed", errors)
    require(manifest.get("raw_value_matching_performed") is False, "raw value matching must not be performed", errors)
    require(manifest.get("formal_report_performed") is False, "formal report must not be performed", errors)
    require(manifest.get("business_execution_performed") is False, "business execution must not be performed", errors)
    require(manifest.get("lineage_full_check_performed") is False, "lineage full check must not be performed", errors)
    require(manifest.get("phase_count") == 3, "phase_count must be 3", errors)
    require(
        manifest.get("phase_results") == {"S01-P1": "PASS", "S01-P2": "PASS", "S01-P3": "PASS"},
        "phase_results mismatch",
        errors,
    )
    require(p1_result.get("stage_phase") == "S01-P1", "S01-P1 validator did not return S01-P1", errors)
    require(p2_result.get("stage_phase") == "S01-P2", "S01-P2 validator did not return S01-P2", errors)
    require(p3_result.get("stage_phase") == "S01-P3", "S01-P3 validator did not return S01-P3", errors)
    require(manifest.get("open_review_finding_count") == 0, "open findings must be 0", errors)
    require(manifest.get("fixed_review_finding_count") == 0, "fixed findings must be 0", errors)
    require(manifest.get("review_findings") == [], "review findings must be empty", errors)

    reviewed = manifest.get("reviewed_phase_manifests", {})
    for phase, path in PHASE_MANIFESTS.items():
        require(reviewed.get(phase) == str(path), f"{phase} manifest ref mismatch", errors)
        require(path.exists(), f"missing phase manifest: {path}", errors)

    release = manifest.get("release_state", {})
    for key in (
        "delivery_allowed",
        "formal_report_allowed",
        "business_decision_basis_allowed",
        "business_execution_allowed",
        "github_main_upload_allowed",
    ):
        require(release.get(key) is False, f"release_state.{key} must be false", errors)
    require(release.get("current_go_no_go") == "NO_GO", "current Go/No-Go must be NO_GO", errors)
    require(release.get("current_report_grade") == "D", "current report grade must be D", errors)
    require(release.get("release_permission") == "blocked", "release permission must be blocked", errors)

    raw_boundary = manifest.get("raw_data_boundary", {})
    require(raw_boundary.get("raw_inbox_path") == "/Users/linzezhang/Downloads/KMFA_MetaData", "raw inbox path mismatch", errors)
    for key in FALSE_BOUNDARY_KEYS:
        require(raw_boundary.get(key) is False, f"raw_data_boundary.{key} must be false", errors)

    safety = manifest.get("public_repo_safety", {})
    for key in PUBLIC_SAFETY_FALSE_KEYS:
        require(safety.get(key) is False, f"public_repo_safety.{key} must be false", errors)

    source = manifest.get("v14_source_baseline", {})
    require(source.get("public_source_count") == 9, "public source count must be 9", errors)
    require(len(str(source.get("source_package_sha256", ""))) == 64, "source package hash must be full SHA256", errors)
    html = source.get("html_human_flow_gate", {})
    require(html.get("pass") == 54 and html.get("warn") == 0 and html.get("fail") == 0, "HTML gate must be 54/0/0", errors)

    counts = manifest.get("no_omission_baseline", {})
    require(counts.get("legacy_requirements") == p3_result.get("legacy_requirements") == 20, "legacy requirement count mismatch", errors)
    require(counts.get("legacy_p0") == p3_result.get("legacy_p0") == 9, "legacy P0 count mismatch", errors)
    require(counts.get("legacy_p1") == p3_result.get("legacy_p1") == 8, "legacy P1 count mismatch", errors)
    require(counts.get("v14_overlay_requirements") == p3_result.get("v14_overlay_requirements") == 5, "v1.4 overlay count mismatch", errors)
    require(counts.get("v14_stages") == p3_result.get("v14_stages") == 18, "v1.4 stage count mismatch", errors)
    require(counts.get("v14_phases") == p3_result.get("v14_phases") == 54, "v1.4 phase count mismatch", errors)
    require(counts.get("v14_tasks") == p3_result.get("v14_tasks") == 162, "v1.4 task count mismatch", errors)
    require(counts.get("v14_stage_phase_task_status_records") == p3_result.get("v14_stage_status_records") == 234, "v1.4 status record count mismatch", errors)

    for ref in manifest.get("evidence_refs", []):
        check_public_safe_file(Path(ref), errors)
    for path in (REPORT_PATH, TEST_RESULTS_PATH, RISK_REGISTER_PATH, ROLLBACK_PATH, MANIFEST_PATH):
        check_public_safe_file(path, errors)

    status = git_output(["status", "--short", "--branch"])
    require("codex/kmfa" in status, "git status must be on codex/kmfa", errors)

    if errors:
        raise ValidationError("\n".join(errors))

    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA v1.4 Stage 1 overall review evidence.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args()
    try:
        manifest = validate_v014_s01_stage_review(args.manifest)
    except ValidationError as exc:
        print("FAIL: KMFA v1.4 Stage 1 review validation failed")
        print(exc)
        return 1
    counts = manifest["no_omission_baseline"]
    html = manifest["v14_source_baseline"]["html_human_flow_gate"]
    print(
        "PASS: KMFA v1.4 Stage 1 review validated "
        f"(phases={manifest['phase_count']}, findings_open={manifest['open_review_finding_count']}, "
        f"legacy_requirements={counts['legacy_requirements']}, v14_overlay={counts['v14_overlay_requirements']}, "
        f"roadmap={counts['v14_stages']}/{counts['v14_phases']}/{counts['v14_tasks']}, "
        f"html={html['pass']}/{html['warn']}/{html['fail']}, "
        f"github_upload={str(manifest['github_upload_performed']).lower()}, "
        f"s02_started={str(manifest['s02_started']).lower()}, "
        f"go_no_go={manifest['release_state']['current_go_no_go']})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
