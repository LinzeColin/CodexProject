#!/usr/bin/env python3
"""Validate KMFA v0.1.4 value-consistency scope gate evidence."""

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

from KMFA.tools.v014_value_consistency_scope_gate import (  # noqa: E402
    ACCEPTANCE_ID,
    DIFFERENCE_REPORT_CONTRACT_PATH,
    GO_NO_GO_PATH,
    GO_NO_GO_RECORD_PATH,
    MANIFEST_PATH,
    METADATA_DIFFERENCE_CONTRACT_PATH,
    METADATA_GO_NO_GO_PATH,
    METADATA_MANIFEST_PATH,
    METADATA_SCOPE_MATRIX_PATH,
    PHASE_ID,
    PRIVATE_DIAGNOSTIC_PATH,
    PRIVATE_SCHEMA_VERSION,
    REPORT_PATH,
    RISK_REGISTER_PATH,
    ROLLBACK_PATH,
    SCHEMA_VERSION,
    SCOPE_MATRIX_PATH,
    STATUS,
    TASK_ID,
    TEST_RESULTS_PATH,
)


FORBIDDEN_PUBLIC_TEXT = (
    "raw_path",
    "raw_root_path",
    "sheet_name:",
    "raw_value:",
    "normalized_value:",
    "processed_value:",
    "source_header_text:",
    "cell_value:",
    "row_value:",
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
    require(".codex_private_runtime/" in PRIVATE_DIAGNOSTIC_PATH.as_posix(), "private diagnostic path mismatch", errors)
    require(not git_output(["ls-files", str(PRIVATE_DIAGNOSTIC_PATH)]), "private diagnostic must not be tracked", errors)
    if not require_private_diagnostic:
        return
    require(PRIVATE_DIAGNOSTIC_PATH.exists(), "private diagnostic must exist for local acceptance", errors)
    if not PRIVATE_DIAGNOSTIC_PATH.exists():
        return
    diagnostic = read_json(PRIVATE_DIAGNOSTIC_PATH)
    require(diagnostic.get("schema_version") == PRIVATE_SCHEMA_VERSION, "private diagnostic schema mismatch", errors)
    require(
        diagnostic.get("classification") == "private_raw_readonly_stat_guard_do_not_commit",
        "private diagnostic classification mismatch",
        errors,
    )
    require(diagnostic.get("raw_root_before") == diagnostic.get("raw_root_after"), "raw root stat changed", errors)
    require(diagnostic.get("raw_root_stat_unchanged_after_scope_guard") is True, "private raw stat guard mismatch", errors)
    require(diagnostic.get("raw_value_matching_performed") is False, "private diagnostic value matching flag mismatch", errors)
    require(diagnostic.get("raw_business_value_extraction_performed") is False, "private diagnostic extraction flag mismatch", errors)
    require(diagnostic.get("raw_inbox_mutation_detected") is False, "private diagnostic mutation flag mismatch", errors)


def validate_v014_value_consistency_scope_gate(
    manifest_path: Path = MANIFEST_PATH,
    *,
    require_private_diagnostic: bool = False,
) -> dict[str, Any]:
    errors: list[str] = []
    manifest = read_json(manifest_path)
    go_no_go = read_json(GO_NO_GO_PATH)
    scope_matrix = read_json(SCOPE_MATRIX_PATH)
    difference_contract = read_json(DIFFERENCE_REPORT_CONTRACT_PATH)
    metadata_manifest = read_json(METADATA_MANIFEST_PATH)
    metadata_go_no_go = read_json(METADATA_GO_NO_GO_PATH)
    metadata_scope_matrix = read_json(METADATA_SCOPE_MATRIX_PATH)
    metadata_difference_contract = read_json(METADATA_DIFFERENCE_CONTRACT_PATH)

    require(metadata_manifest == manifest, "metadata manifest copy mismatch", errors)
    require(metadata_go_no_go == go_no_go, "metadata go/no-go copy mismatch", errors)
    require(metadata_scope_matrix == scope_matrix, "metadata scope matrix copy mismatch", errors)
    require(metadata_difference_contract == difference_contract, "metadata difference contract copy mismatch", errors)
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
        "value_consistency_scope_gate_only",
        "authoritative_raw_baseline_dependency_consumed",
        "raw_inbox_stat_guard_only",
    ):
        require(scope.get(key) is True, f"phase_scope_controls.{key} must be true", errors)
    for key in (
        "raw_business_value_extraction_performed",
        "raw_value_matching_performed",
        "processed_data_reconciliation_performed",
        "lineage_full_check_performed",
        "formal_report_performed",
        "github_upload_performed",
        "app_reinstall_performed",
        "business_execution_performed",
        "next_phase_started",
    ):
        require(scope.get(key) is False, f"phase_scope_controls.{key} must be false", errors)

    summary = manifest.get("value_consistency_summary", {})
    for key in (
        "authoritative_raw_baseline_locked",
        "source_container_consistency_verified",
        "value_consistency_scope_locked",
        "raw_inbox_mutation_guard_locked",
        "difference_report_required_on_repeated_mismatch",
        "difference_report_obligation_locked",
        "private_value_diagnostic_next_phase_required",
    ):
        require(summary.get(key) is True, f"value_consistency_summary.{key} must be true", errors)
    for key in (
        "raw_inbox_mutation_detected",
        "raw_value_matching_performed",
        "raw_business_value_extraction_performed",
        "processed_data_reconciliation_performed",
        "processed_data_consistency_verified",
        "business_value_consistency_verified",
        "lineage_full_check_complete",
        "formal_report_allowed",
        "difference_report_triggered_this_phase",
        "public_value_disclosure_allowed",
    ):
        require(summary.get(key) is False, f"value_consistency_summary.{key} must be false", errors)

    boundary = manifest.get("raw_boundary", {})
    require(boundary.get("raw_inbox_stat_guard_performed_by_this_phase") is True, "stat guard must run", errors)
    require(boundary.get("raw_root_stat_unchanged_after_scope_guard") is True, "raw root stat must be unchanged", errors)
    for key in (
        "raw_inbox_read_performed_by_this_phase",
        "raw_inbox_list_performed_by_this_phase",
        "raw_inbox_hash_performed_by_this_phase",
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
        require(boundary.get(key) is False, f"raw_boundary.{key} must be false", errors)

    require(scope_matrix.get("phase_id") == PHASE_ID, "scope matrix phase mismatch", errors)
    lanes = scope_matrix.get("lanes", [])
    require(isinstance(lanes, list) and len(lanes) == 6, "scope matrix must contain six lanes", errors)
    if isinstance(lanes, list):
        lane_ids = {lane.get("lane_id") for lane in lanes if isinstance(lane, dict)}
        require(lane_ids == {"VC-L01", "VC-L02", "VC-L03", "VC-L04", "VC-L05", "VC-L06"}, "lane ids mismatch", errors)
        require(
            all(lane.get("required_before_business_value_go") is True for lane in lanes if isinstance(lane, dict)),
            "all lanes must be required before business value go",
            errors,
        )
    for key in (
        "all_lanes_public_safe",
        "raw_business_values_in_public_scope_matrix",
        "raw_filenames_in_public_scope_matrix",
        "field_header_plaintext_in_public_scope_matrix",
    ):
        expected = key == "all_lanes_public_safe"
        require(scope_matrix.get(key) is expected, f"scope_matrix.{key} mismatch", errors)

    require(difference_contract.get("enabled") is True, "difference contract must be enabled", errors)
    require(
        difference_contract.get("final_goal_closeout_must_include_difference_report_if_triggered") is True,
        "goal closeout report obligation mismatch",
        errors,
    )
    require(
        difference_contract.get("multi_pass_cross_validation_required_before_consistency_claim") is True,
        "multi-pass requirement mismatch",
        errors,
    )
    require(difference_contract.get("minimum_independent_validation_passes") == 3, "minimum pass count mismatch", errors)
    require(difference_contract.get("raw_inbox_mutation_allowed") is False, "raw mutation must be disallowed", errors)
    require(difference_contract.get("blocked_release_until_resolved") is True, "blocked release flag mismatch", errors)
    for key in (
        "public_difference_report_contains_raw_values",
        "public_difference_report_contains_raw_filenames",
        "public_difference_report_contains_field_header_plaintext",
    ):
        require(difference_contract.get(key) is False, f"difference_contract.{key} must be false", errors)

    public_safety = manifest.get("public_repo_safety", {})
    for key, value in public_safety.items():
        if key == "public_safe_aggregate_only":
            require(value is True, f"public_repo_safety.{key} must be true", errors)
        else:
            require(value is False, f"public_repo_safety.{key} must be false", errors)

    require(manifest.get("go_no_go") == go_no_go, "embedded go/no-go mismatch", errors)
    require(go_no_go.get("schema_version") == "kmfa.v014_value_consistency_scope_go_no_go.v1", "go/no-go schema mismatch", errors)
    require(go_no_go.get("decision") == "NO_GO", "go/no-go decision mismatch", errors)
    for key in (
        "authoritative_raw_baseline_locked",
        "value_consistency_scope_locked",
        "raw_inbox_mutation_guard_locked",
        "difference_report_required_on_repeated_mismatch",
    ):
        require(go_no_go.get(key) is True, f"go_no_go.{key} must be true", errors)
    for key in (
        "raw_value_matching_performed",
        "processed_data_reconciliation_performed",
        "business_value_consistency_verified",
        "lineage_full_check_complete",
        "formal_report_allowed",
        "github_upload_allowed",
        "app_reinstall_allowed",
        "business_execution_allowed",
    ):
        require(go_no_go.get(key) is False, f"go_no_go.{key} must be false", errors)
    require("RAW_VALUE_MATCHING_NOT_PERFORMED" in go_no_go.get("blocker_ids", []), "missing raw value blocker", errors)
    require(
        "DIFFERENCE_REPORT_OBLIGATION_LOCKED" in go_no_go.get("resolved_blocker_ids", []),
        "missing difference report resolved blocker",
        errors,
    )
    require(manifest.get("github_upload_performed") is False, "GitHub upload must not be performed", errors)
    require(manifest.get("app_reinstall_performed") is False, "app reinstall must not be performed", errors)
    require(manifest.get("formal_report_performed") is False, "formal report must not be performed", errors)
    require(manifest.get("business_execution_performed") is False, "business execution must not be performed", errors)

    check_private_diagnostic(require_private_diagnostic, errors)
    for ref in manifest.get("evidence_refs", []):
        check_public_evidence_text(Path(ref), errors)
    for path in (
        MANIFEST_PATH,
        GO_NO_GO_PATH,
        SCOPE_MATRIX_PATH,
        DIFFERENCE_REPORT_CONTRACT_PATH,
        METADATA_MANIFEST_PATH,
        METADATA_GO_NO_GO_PATH,
        METADATA_SCOPE_MATRIX_PATH,
        METADATA_DIFFERENCE_CONTRACT_PATH,
        REPORT_PATH,
        GO_NO_GO_RECORD_PATH,
        TEST_RESULTS_PATH,
        RISK_REGISTER_PATH,
        ROLLBACK_PATH,
    ):
        check_public_evidence_text(path, errors)

    tracked_files = git_output(["ls-files", "KMFA"]).splitlines()
    forbidden = [
        path for path in tracked_files if path.lower().endswith(FORBIDDEN_TRACKED_SUFFIXES) or ".codex_private_runtime/" in path
    ]
    require(not forbidden, "forbidden raw/private tracked artifacts: " + ", ".join(forbidden[:20]), errors)
    require("codex/kmfa" in git_output(["status", "--short", "--branch"]), "git status must be on codex/kmfa", errors)

    if errors:
        raise ValidationError("\n".join(f"- {error}" for error in errors))
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.4 value-consistency scope gate.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--require-private-diagnostic", action="store_true")
    args = parser.parse_args(argv)
    try:
        manifest = validate_v014_value_consistency_scope_gate(
            args.manifest,
            require_private_diagnostic=args.require_private_diagnostic,
        )
    except ValidationError as exc:
        print("FAIL: KMFA v0.1.4 value consistency scope validation failed")
        print(exc)
        return 1
    summary = manifest["value_consistency_summary"]
    print(
        "PASS: KMFA v0.1.4 value consistency scope validated "
        f"(scope_locked={str(summary['value_consistency_scope_locked']).lower()}, "
        f"raw_value_matching={str(summary['raw_value_matching_performed']).lower()}, "
        f"business_value_consistency={str(summary['business_value_consistency_verified']).lower()}, "
        f"github_upload={str(manifest['github_upload_performed']).lower()})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
