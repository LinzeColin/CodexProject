#!/usr/bin/env python3
"""Validate KMFA v0.1.4 raw value matching private dry-run evidence."""

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

from KMFA.tools.v014_raw_value_matching_private_dry_run import (  # noqa: E402
    ACCEPTANCE_ID,
    GAP_SUMMARY_PATH,
    GO_NO_GO_PATH,
    GO_NO_GO_RECORD_PATH,
    MANIFEST_PATH,
    METADATA_GAP_SUMMARY_PATH,
    METADATA_GO_NO_GO_PATH,
    METADATA_MANIFEST_PATH,
    PHASE_ID,
    PRIVATE_DIAGNOSTIC_PATH,
    PRIVATE_GAP_REPORT_PATH,
    PRIVATE_SCHEMA_VERSION,
    REPORT_PATH,
    RISK_REGISTER_PATH,
    ROLLBACK_PATH,
    SCHEMA_VERSION,
    STATUS,
    TASK_ID,
    TEST_RESULTS_PATH,
)


FORBIDDEN_PUBLIC_TEXT = (
    "raw_path",
    "raw_root_path",
    "sheet_name:",
    "worksheet_name",
    "member_name",
    "raw_value:",
    "normalized_value:",
    "processed_value:",
    "source_header_text:",
    "cell_value:",
    "row_value:",
    "pdf_text",
    "business_value:",
    "project_name_plaintext",
    "customer_name_plaintext",
    "counterparty_plaintext",
    "company_entity_plaintext",
    "supplier_name_plaintext",
    "account_number:",
    "invoice_number:",
    "tax_identifier:",
    "connector_" + "token:",
    "connector_" + "pass" + "word:",
    "api" + "_key:",
    "private" + "_key:",
    "-----" "BEGIN",
    "s" "k-",
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
FORBIDDEN_TRACKED_SUFFIXES = (
    ".zip",
    ".xlsx",
    ".xls",
    ".xlsm",
    ".pdf",
    ".sqlite",
    ".sqlite3",
    ".sqlite-shm",
    ".sqlite-wal",
    ".db",
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


def check_private_diagnostic(require_private_diagnostic: bool, errors: list[str]) -> None:
    for path in (PRIVATE_DIAGNOSTIC_PATH, PRIVATE_GAP_REPORT_PATH):
        require(".codex_private_runtime/" in path.as_posix(), f"private path mismatch: {path}", errors)
        require(not git_output(["ls-files", str(path)]), f"private artifact must not be tracked: {path}", errors)
    if not require_private_diagnostic:
        return
    require(PRIVATE_DIAGNOSTIC_PATH.exists(), "private diagnostic must exist for local acceptance", errors)
    require(PRIVATE_GAP_REPORT_PATH.exists(), "private gap report must exist for local acceptance", errors)
    if not PRIVATE_DIAGNOSTIC_PATH.exists():
        return
    diagnostic = read_json(PRIVATE_DIAGNOSTIC_PATH)
    require(diagnostic.get("schema_version") == PRIVATE_SCHEMA_VERSION, "private diagnostic schema mismatch", errors)
    require(
        diagnostic.get("classification") == "private_raw_value_matching_diagnostic_do_not_commit",
        "private diagnostic classification mismatch",
        errors,
    )
    require(diagnostic.get("raw_root_before") == diagnostic.get("raw_root_after"), "raw root stat changed", errors)
    require(diagnostic.get("raw_root_stat_unchanged_after_dry_run") is True, "raw root stat guard mismatch", errors)
    require(diagnostic.get("raw_inbox_mutation_detected") is False, "raw mutation flag mismatch", errors)
    raw_summary = diagnostic.get("raw_private_summary", {})
    require(raw_summary.get("raw_value_fingerprints_generated") is True, "private raw fingerprints missing", errors)
    require(int(raw_summary.get("raw_value_fingerprint_count", 0)) > 0, "private raw fingerprint count must be > 0", errors)
    processed_summary = diagnostic.get("processed_scan_summary", {})
    require(
        processed_summary.get("processed_value_targets_available") is False,
        "processed value target availability should remain false in this dry run",
        errors,
    )
    require(diagnostic.get("comparable_value_pair_count") == 0, "comparable pair count must be zero", errors)
    require(diagnostic.get("business_value_consistency_verified") is False, "consistency must not be verified", errors)


def validate_v014_raw_value_matching_private_dry_run(
    manifest_path: Path = MANIFEST_PATH,
    *,
    require_private_diagnostic: bool = False,
) -> dict[str, Any]:
    errors: list[str] = []
    manifest = read_json(manifest_path)
    go_no_go = read_json(GO_NO_GO_PATH)
    gap_summary = read_json(GAP_SUMMARY_PATH)
    metadata_manifest = read_json(METADATA_MANIFEST_PATH)
    metadata_go_no_go = read_json(METADATA_GO_NO_GO_PATH)
    metadata_gap_summary = read_json(METADATA_GAP_SUMMARY_PATH)

    require(metadata_manifest == manifest, "metadata manifest copy mismatch", errors)
    require(metadata_go_no_go == go_no_go, "metadata go/no-go copy mismatch", errors)
    require(metadata_gap_summary == gap_summary, "metadata gap summary copy mismatch", errors)
    require(manifest.get("schema_version") == SCHEMA_VERSION, "schema mismatch", errors)
    require(manifest.get("project_id") == "KMFA", "project_id mismatch", errors)
    require(manifest.get("version") == "0.1.4", "version mismatch", errors)
    require(manifest.get("phase_id") == PHASE_ID, "phase_id mismatch", errors)
    require(manifest.get("task_id") == TASK_ID, "task_id mismatch", errors)
    require(manifest.get("acceptance_ids") == [ACCEPTANCE_ID], "acceptance ids mismatch", errors)
    require(manifest.get("status") == STATUS, "status mismatch", errors)

    scope = manifest.get("phase_scope_controls", {})
    for key in (
        "current_phase_only",
        "private_raw_value_matching_dry_run_only",
        "authoritative_raw_baseline_dependency_consumed",
        "raw_value_fingerprint_extraction_performed",
        "processed_value_target_scan_performed",
    ):
        require(scope.get(key) is True, f"phase_scope_controls.{key} must be true", errors)
    for key in (
        "raw_to_processed_value_comparison_performed",
        "processed_data_reconciliation_performed",
        "lineage_full_check_performed",
        "formal_report_performed",
        "github_upload_performed",
        "app_reinstall_performed",
        "business_execution_performed",
        "next_phase_started",
    ):
        require(scope.get(key) is False, f"phase_scope_controls.{key} must be false", errors)

    boundary = manifest.get("raw_readonly_boundary", {})
    for key in (
        "raw_inbox_read_performed_by_this_phase",
        "raw_inbox_list_performed_by_this_phase",
        "raw_inbox_stat_performed_by_this_phase",
        "raw_inbox_hash_or_value_fingerprint_performed_by_this_phase",
        "raw_root_stat_unchanged_after_dry_run",
    ):
        require(boundary.get(key) is True, f"raw_readonly_boundary.{key} must be true", errors)
    for key in (
        "raw_inbox_write_performed_by_this_phase",
        "raw_inbox_delete_performed_by_this_phase",
        "raw_inbox_move_performed_by_this_phase",
        "raw_inbox_rename_performed_by_this_phase",
        "raw_inbox_overwrite_performed_by_this_phase",
        "raw_inbox_copy_performed_by_this_phase",
        "raw_inbox_create_extra_files_inside_by_this_phase",
        "raw_inbox_normalize_performed_by_this_phase",
        "raw_inbox_mutated_by_this_phase",
    ):
        require(boundary.get(key) is False, f"raw_readonly_boundary.{key} must be false", errors)

    raw_summary = manifest.get("raw_private_extraction_summary", {})
    require(raw_summary.get("source_container_openable") is True, "source container must be openable", errors)
    require(raw_summary.get("package_pdf_entry_count") == 8, "PDF entry count mismatch", errors)
    require(raw_summary.get("package_workbook_entry_count") == 1, "workbook entry count mismatch", errors)
    require(raw_summary.get("raw_value_fingerprints_generated") is True, "raw fingerprints must be generated", errors)
    require(int(raw_summary.get("raw_value_fingerprint_count", 0)) > 0, "raw fingerprint count must be > 0", errors)

    processed_summary = manifest.get("processed_target_summary", {})
    require(
        processed_summary.get("processed_value_targets_available") is False,
        "processed value targets should be missing in this dry run",
        errors,
    )
    require(
        processed_summary.get("processed_value_target_status") == "missing_private_processed_value_targets",
        "processed value target status mismatch",
        errors,
    )

    matching_summary = manifest.get("value_matching_summary", {})
    require(matching_summary.get("raw_value_fingerprints_generated") is True, "matching raw fingerprints missing", errors)
    require(matching_summary.get("approved_private_processed_value_target_count") == 0, "processed target count must be zero", errors)
    require(matching_summary.get("comparable_value_pair_count") == 0, "comparable pair count must be zero", errors)
    require(matching_summary.get("raw_to_processed_value_comparison_performed") is False, "comparison must not be performed", errors)
    require(matching_summary.get("processed_data_consistency_verified") is False, "processed consistency must be false", errors)
    require(matching_summary.get("business_value_consistency_verified") is False, "business consistency must be false", errors)
    require(matching_summary.get("dry_run_gap_report_generated") is True, "gap report flag missing", errors)
    require(matching_summary.get("repeated_cross_validation_mismatch_confirmed") is False, "repeated mismatch flag mismatch", errors)
    require(matching_summary.get("independent_validation_passes_completed_by_this_phase") == 1, "pass count mismatch", errors)
    require(matching_summary.get("minimum_independent_validation_passes_required") == 3, "minimum pass requirement mismatch", errors)

    require(go_no_go.get("decision") == "NO_GO", "go/no-go decision mismatch", errors)
    require(go_no_go.get("processed_value_targets_available") is False, "go/no-go processed target flag mismatch", errors)
    require(go_no_go.get("comparable_value_pair_count") == 0, "go/no-go comparable pair count mismatch", errors)
    require(go_no_go.get("business_value_consistency_verified") is False, "go/no-go consistency mismatch", errors)
    for key in (
        "lineage_full_check_complete",
        "formal_report_allowed",
        "github_upload_allowed",
        "app_reinstall_allowed",
        "business_execution_allowed",
    ):
        require(go_no_go.get(key) is False, f"go_no_go.{key} must be false", errors)

    require(gap_summary.get("gap_count") == 1, "gap count mismatch", errors)
    require(gap_summary.get("public_raw_or_processed_values_included") is False, "gap summary value leak flag mismatch", errors)
    require(
        gap_summary.get("final_goal_closeout_difference_report_required_if_repeated") is True,
        "final difference report obligation mismatch",
        errors,
    )

    safety = manifest.get("public_repo_safety", {})
    require(safety.get("public_safe_aggregate_only") is True, "public safety aggregate flag mismatch", errors)
    for key, value in safety.items():
        if key == "public_safe_aggregate_only":
            continue
        require(value is False, f"public_repo_safety.{key} must be false", errors)

    for path in (
        MANIFEST_PATH,
        GO_NO_GO_PATH,
        GAP_SUMMARY_PATH,
        REPORT_PATH,
        GO_NO_GO_RECORD_PATH,
        TEST_RESULTS_PATH,
        RISK_REGISTER_PATH,
        ROLLBACK_PATH,
        METADATA_MANIFEST_PATH,
        METADATA_GO_NO_GO_PATH,
        METADATA_GAP_SUMMARY_PATH,
    ):
        check_public_evidence_text(path, errors)

    tracked = git_output(["ls-files", "KMFA"])
    for line in tracked.splitlines():
        lower = line.lower()
        require(".codex_private_runtime/" not in line, f"private runtime file is tracked: {line}", errors)
        require(not lower.endswith(FORBIDDEN_TRACKED_SUFFIXES), f"forbidden tracked raw/private artifact: {line}", errors)

    check_private_diagnostic(require_private_diagnostic, errors)

    if errors:
        raise ValidationError("\n".join(errors))
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-private-diagnostic", action="store_true")
    args = parser.parse_args(argv)
    manifest = validate_v014_raw_value_matching_private_dry_run(
        require_private_diagnostic=args.require_private_diagnostic
    )
    summary = manifest["value_matching_summary"]
    print(
        "PASS: KMFA v0.1.4 raw value matching private dry run validated "
        f"(raw_fingerprints={summary['raw_value_fingerprint_count']}, "
        f"processed_targets={summary['approved_private_processed_value_target_count']}, "
        "business_consistency=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
