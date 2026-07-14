#!/usr/bin/env python3
"""Validate KMFA v0.1.4 private processed value source-map capture evidence."""

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

from KMFA.tools.v014_private_processed_value_source_map_capture import (  # noqa: E402
    ACCEPTANCE_ID,
    GO_NO_GO_PATH,
    GO_NO_GO_RECORD_PATH,
    GO_NO_GO_SCHEMA_VERSION,
    MANIFEST_PATH,
    METADATA_GO_NO_GO_PATH,
    METADATA_MANIFEST_PATH,
    METADATA_SUMMARY_PATH,
    NEXT_RECOMMENDED_PHASE,
    PHASE_ID,
    PRIVATE_CAPTURE_PATH,
    PRIVATE_FILL_REQUEST_PATH,
    PRIVATE_FILL_REQUEST_SCHEMA_VERSION,
    PRIVATE_SCHEMA_VERSION,
    REPORT_PATH,
    RISK_REGISTER_PATH,
    ROLLBACK_PATH,
    SCHEMA_VERSION,
    SOURCE_MAP_CANDIDATES,
    STATUS,
    SUMMARY_PATH,
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
    "private://",
    "private_ref://",
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


def check_private_capture(
    *,
    require_private_capture: bool,
    expected_slot_count: int,
    expected_fill_count: int,
    errors: list[str],
) -> None:
    for path in (PRIVATE_CAPTURE_PATH, PRIVATE_FILL_REQUEST_PATH):
        require(".codex_private_runtime/" in path.as_posix(), f"private path mismatch: {path}", errors)
        require(not git_output(["ls-files", str(path)]), f"private artifact must not be tracked: {path}", errors)
    for path in SOURCE_MAP_CANDIDATES:
        require(not git_output(["ls-files", str(path)]), f"private source map must not be tracked: {path}", errors)
    if not require_private_capture:
        return
    require(PRIVATE_CAPTURE_PATH.exists(), "private capture diagnostic must exist for local acceptance", errors)
    require(PRIVATE_FILL_REQUEST_PATH.exists(), "private fill request must exist for local acceptance", errors)
    if not PRIVATE_CAPTURE_PATH.exists() or not PRIVATE_FILL_REQUEST_PATH.exists():
        return
    capture = read_json(PRIVATE_CAPTURE_PATH)
    fill_request = read_json(PRIVATE_FILL_REQUEST_PATH)
    require(capture.get("schema_version") == PRIVATE_SCHEMA_VERSION, "private capture schema mismatch", errors)
    require(
        capture.get("classification") == "private_processed_value_source_map_capture_do_not_commit",
        "private capture classification mismatch",
        errors,
    )
    require(fill_request.get("schema_version") == PRIVATE_FILL_REQUEST_SCHEMA_VERSION, "fill request schema mismatch", errors)
    require(
        fill_request.get("classification") == "private_processed_value_source_map_fill_request_do_not_commit",
        "fill request classification mismatch",
        errors,
    )
    require(capture.get("raw_to_processed_value_comparison_performed") is False, "private comparison flag must be false", errors)
    require(capture.get("business_value_consistency_verified") is False, "private consistency flag must be false", errors)
    slots = capture.get("source_map_capture_slots", [])
    require(isinstance(slots, list), "source_map_capture_slots must be list", errors)
    require(len(slots) == expected_slot_count, "private capture slot count mismatch", errors)
    fill_items = fill_request.get("fill_request_items", [])
    require(isinstance(fill_items, list), "fill_request_items must be list", errors)
    require(len(fill_items) == expected_fill_count, "private fill request count mismatch", errors)
    for slot in slots:
        if not isinstance(slot, dict):
            continue
        require("target_slot_id" in slot, "capture slot target id missing", errors)
        require("private_processed_ref" in slot, "private capture slot ref missing", errors)
        require(slot.get("processed_value_fingerprint_present") is False, "unexpected processed fingerprint present", errors)
        for forbidden_key in ("processed_value", "value", "raw_value", "normalized_value"):
            require(forbidden_key not in slot, f"value-bearing key must not be in capture slot: {forbidden_key}", errors)
    for item in fill_items:
        if not isinstance(item, dict):
            continue
        require(item.get("required_field") == "processed_value_fingerprint", "fill request required field mismatch", errors)
        require(item.get("fill_status") == "authorized_private_value_source_required", "fill status mismatch", errors)
        for forbidden_key in ("processed_value", "value", "raw_value", "normalized_value"):
            require(forbidden_key not in item, f"value-bearing key must not be in fill request: {forbidden_key}", errors)


def validate_v014_private_processed_value_source_map_capture(
    manifest_path: Path = MANIFEST_PATH,
    *,
    require_private_capture: bool = False,
) -> dict[str, Any]:
    errors: list[str] = []
    manifest = read_json(manifest_path)
    go_no_go = read_json(GO_NO_GO_PATH)
    summary = read_json(SUMMARY_PATH)
    metadata_manifest = read_json(METADATA_MANIFEST_PATH)
    metadata_go_no_go = read_json(METADATA_GO_NO_GO_PATH)
    metadata_summary = read_json(METADATA_SUMMARY_PATH)

    require(metadata_manifest == manifest, "metadata manifest copy mismatch", errors)
    require(metadata_go_no_go == go_no_go, "metadata go/no-go copy mismatch", errors)
    require(metadata_summary == summary, "metadata summary copy mismatch", errors)
    require(manifest.get("schema_version") == SCHEMA_VERSION, "schema mismatch", errors)
    require(manifest.get("project_id") == "KMFA", "project_id mismatch", errors)
    require(manifest.get("version") == "0.1.4", "version mismatch", errors)
    require(manifest.get("phase_id") == PHASE_ID, "phase_id mismatch", errors)
    require(manifest.get("task_id") == TASK_ID, "task_id mismatch", errors)
    require(manifest.get("acceptance_ids") == [ACCEPTANCE_ID], "acceptance ids mismatch", errors)
    require(manifest.get("status") == STATUS, "status mismatch", errors)
    require(manifest.get("next_recommended_phase") == NEXT_RECOMMENDED_PHASE, "next phase mismatch", errors)

    require(go_no_go.get("schema_version") == GO_NO_GO_SCHEMA_VERSION, "go/no-go schema mismatch", errors)
    require(go_no_go.get("decision") == "NO_GO", "go/no-go decision mismatch", errors)
    require(go_no_go.get("next_recommended_phase") == NEXT_RECOMMENDED_PHASE, "go/no-go next phase mismatch", errors)
    require(manifest.get("go_no_go") == go_no_go, "manifest go/no-go mismatch", errors)

    scope = manifest.get("phase_scope_controls", {})
    for key in (
        "current_phase_only",
        "private_processed_value_source_map_capture_only",
        "previous_staging_private_runtime_consumed",
        "previous_source_resolution_evidence_consumed",
        "private_capture_request_written",
    ):
        require(scope.get(key) is True, f"phase_scope_controls.{key} must be true", errors)
    for key in (
        "private_source_map_write_performed",
        "processed_value_materialization_performed",
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

    raw_boundary = manifest.get("raw_readonly_boundary", {})
    for key, value in raw_boundary.items():
        require(value is False, f"raw_readonly_boundary.{key} must be false", errors)

    capture_summary = manifest.get("source_map_capture_summary", {})
    require(capture_summary == summary, "manifest summary mismatch", errors)
    require(summary.get("processed_target_slot_count") == 149, "processed target slot count mismatch", errors)
    require(summary.get("path_only_private_ref_slot_count") == 149, "path-only slot count mismatch", errors)
    require(summary.get("direct_processed_value_literal_count") == 0, "direct value literal count must be zero", errors)
    require(summary.get("existing_processed_value_fingerprint_count") == 0, "existing fingerprint count must be zero", errors)
    require(summary.get("captured_processed_value_fingerprint_count") == 0, "captured fingerprint count must be zero", errors)
    require(
        summary.get("usable_private_processed_value_source_map_record_count") == 0,
        "usable source map record count must be zero",
        errors,
    )
    require(summary.get("private_source_map_write_performed") is False, "private source map write must be false", errors)
    require(summary.get("authorized_fill_required_slot_count") == 149, "authorized fill count mismatch", errors)
    require(summary.get("source_map_capture_complete") is False, "source map capture must remain incomplete", errors)
    require(summary.get("raw_to_processed_value_comparison_performed") is False, "comparison must be false", errors)
    require(summary.get("comparable_value_pair_count") == 0, "comparable pair count must be zero", errors)
    require(summary.get("business_value_consistency_verified") is False, "business consistency must be false", errors)

    readiness = manifest.get("value_matching_readiness", {})
    require(readiness.get("processed_target_slot_count") == summary.get("processed_target_slot_count"), "readiness slot mismatch", errors)
    require(readiness.get("processed_source_map_capture_complete") is False, "readiness capture complete must be false", errors)
    require(readiness.get("private_processed_value_fingerprint_count") == 0, "readiness fingerprint count mismatch", errors)
    require(readiness.get("authorized_fill_required_slot_count") == 149, "readiness fill count mismatch", errors)
    require(readiness.get("raw_to_processed_value_comparison_performed") is False, "readiness comparison must be false", errors)
    require(readiness.get("comparable_value_pair_count") == 0, "readiness comparable pair count must be zero", errors)
    require(readiness.get("business_value_consistency_verified") is False, "readiness business consistency must be false", errors)
    require(
        readiness.get("final_goal_closeout_difference_report_required_if_repeated") is True,
        "difference report obligation must remain true",
        errors,
    )

    for key in (
        "lineage_full_check_complete",
        "formal_report_allowed",
        "github_upload_allowed",
        "app_reinstall_allowed",
        "business_execution_allowed",
    ):
        require(go_no_go.get(key) is False, f"go_no_go.{key} must be false", errors)

    safety = manifest.get("public_repo_safety", {})
    require(safety.get("public_safe_aggregate_only") is True, "public safety aggregate flag mismatch", errors)
    for key, value in safety.items():
        if key == "public_safe_aggregate_only":
            continue
        require(value is False, f"public_repo_safety.{key} must be false", errors)

    for path in (
        MANIFEST_PATH,
        GO_NO_GO_PATH,
        SUMMARY_PATH,
        REPORT_PATH,
        GO_NO_GO_RECORD_PATH,
        TEST_RESULTS_PATH,
        RISK_REGISTER_PATH,
        ROLLBACK_PATH,
        METADATA_MANIFEST_PATH,
        METADATA_GO_NO_GO_PATH,
        METADATA_SUMMARY_PATH,
    ):
        check_public_evidence_text(path, errors)

    tracked = git_output(["ls-files", "KMFA"])
    for line in tracked.splitlines():
        lower = line.lower()
        require(".codex_private_runtime/" not in line, f"private runtime file is tracked: {line}", errors)
        require(not lower.endswith(FORBIDDEN_TRACKED_SUFFIXES), f"forbidden tracked raw/private artifact: {line}", errors)

    check_private_capture(
        require_private_capture=require_private_capture,
        expected_slot_count=int(summary.get("processed_target_slot_count", 0)),
        expected_fill_count=int(summary.get("authorized_fill_required_slot_count", 0)),
        errors=errors,
    )

    if errors:
        raise ValidationError("\n".join(errors))
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-private-capture", action="store_true")
    args = parser.parse_args(argv)
    manifest = validate_v014_private_processed_value_source_map_capture(
        require_private_capture=args.require_private_capture
    )
    summary = manifest["source_map_capture_summary"]
    print(
        "PASS: KMFA v0.1.4 private processed value source-map capture validated "
        f"(target_slots={summary['processed_target_slot_count']}, "
        f"captured_fingerprints={summary['captured_processed_value_fingerprint_count']}, "
        f"authorized_fill_required={summary['authorized_fill_required_slot_count']}, "
        "business_consistency=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
