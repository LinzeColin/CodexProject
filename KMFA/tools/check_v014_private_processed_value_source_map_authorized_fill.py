#!/usr/bin/env python3
"""Validate KMFA v0.1.4 authorized private processed source-map fill evidence."""

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

from KMFA.tools.v014_private_processed_value_source_map_authorized_fill import (  # noqa: E402
    ACCEPTANCE_ID,
    GO_NO_GO_PATH,
    GO_NO_GO_RECORD_PATH,
    GO_NO_GO_SCHEMA_VERSION,
    MANIFEST_PATH,
    MATERIALIZATION_SOURCE_MAP_PATH,
    METADATA_GO_NO_GO_PATH,
    METADATA_MANIFEST_PATH,
    METADATA_SUMMARY_PATH,
    NEXT_RECOMMENDED_PHASE,
    PHASE_ID,
    PRIVATE_AUTHORIZED_FILL_PATH,
    PRIVATE_SCHEMA_VERSION,
    PRIVATE_SOURCE_MAP_PATH,
    PRIVATE_SOURCE_MAP_SCHEMA_VERSION,
    REPORT_PATH,
    RISK_REGISTER_PATH,
    ROLLBACK_PATH,
    SCHEMA_VERSION,
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
VALUE_BEARING_KEYS = {
    "raw_value",
    "normalized_value",
    "processed_value",
    "business_value",
    "value",
    "amount",
}
SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


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


def git_check_ignore(path: Path) -> bool:
    result = subprocess.run(
        ["git", "check-ignore", "-q", str(path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return result.returncode == 0


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


def _contains_value_bearing_key(value: Any) -> bool:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in VALUE_BEARING_KEYS:
                return True
            if _contains_value_bearing_key(child):
                return True
    elif isinstance(value, list):
        return any(_contains_value_bearing_key(child) for child in value)
    return False


def check_private_authorized_fill(
    *,
    require_private_authorized_fill: bool,
    expected_filled_count: int,
    expected_unfilled_count: int,
    errors: list[str],
) -> None:
    for path in (PRIVATE_AUTHORIZED_FILL_PATH, PRIVATE_SOURCE_MAP_PATH, MATERIALIZATION_SOURCE_MAP_PATH):
        require(".codex_private_runtime/" in path.as_posix(), f"private path mismatch: {path}", errors)
        require(not git_output(["ls-files", str(path)]), f"private artifact must not be tracked: {path}", errors)
        require(git_check_ignore(path), f"private artifact must be git-ignored: {path}", errors)
    if not require_private_authorized_fill:
        return
    for path in (PRIVATE_AUTHORIZED_FILL_PATH, PRIVATE_SOURCE_MAP_PATH, MATERIALIZATION_SOURCE_MAP_PATH):
        require(path.exists(), f"private authorized fill artifact must exist: {path}", errors)
    if not PRIVATE_AUTHORIZED_FILL_PATH.exists() or not PRIVATE_SOURCE_MAP_PATH.exists():
        return

    private_fill = read_json(PRIVATE_AUTHORIZED_FILL_PATH)
    source_map = read_json(PRIVATE_SOURCE_MAP_PATH)
    staged_source_map = read_json(MATERIALIZATION_SOURCE_MAP_PATH)
    require(staged_source_map == source_map, "staged materialization source map copy mismatch", errors)
    require(private_fill.get("schema_version") == PRIVATE_SCHEMA_VERSION, "private authorized fill schema mismatch", errors)
    require(
        private_fill.get("classification") == "private_processed_value_source_map_authorized_fill_do_not_commit",
        "private authorized fill classification mismatch",
        errors,
    )
    require(source_map.get("schema_version") == PRIVATE_SOURCE_MAP_SCHEMA_VERSION, "private source map schema mismatch", errors)
    require(
        source_map.get("classification") == "private_processed_value_source_map_do_not_commit",
        "private source map classification mismatch",
        errors,
    )
    require(private_fill.get("raw_to_processed_value_comparison_performed") is False, "private comparison flag must be false", errors)
    require(private_fill.get("business_value_consistency_verified") is False, "private consistency flag must be false", errors)
    summary = private_fill.get("authorized_fill_summary", {})
    require(summary.get("authorized_filled_item_count") == expected_filled_count, "private filled count mismatch", errors)
    require(summary.get("authorized_unfilled_item_count") == expected_unfilled_count, "private unfilled count mismatch", errors)
    require(summary.get("source_map_authorized_fill_complete") is False, "private fill must remain incomplete", errors)

    records = source_map.get("processed_value_sources", [])
    require(isinstance(records, list), "processed_value_sources must be list", errors)
    require(len(records) == expected_filled_count, "private source map record count mismatch", errors)
    target_ids: set[str] = set()
    for record in records:
        require(isinstance(record, dict), "source map record must be object", errors)
        if not isinstance(record, dict):
            continue
        require(
            sorted(record) == ["fill_status", "processed_value_fingerprint", "target_slot_id"],
            "private source map record fields mismatch",
            errors,
        )
        target_id = record.get("target_slot_id")
        fingerprint = record.get("processed_value_fingerprint")
        require(isinstance(target_id, str) and target_id.startswith("PVSTG-"), "target slot id mismatch", errors)
        require(isinstance(fingerprint, str) and SHA256_RE.match(fingerprint) is not None, "fingerprint format mismatch", errors)
        require(record.get("fill_status") == "filled_from_existing_metadata_hash_sibling", "fill status mismatch", errors)
        if isinstance(target_id, str):
            require(target_id not in target_ids, f"duplicate target slot id: {target_id}", errors)
            target_ids.add(target_id)
        require(not _contains_value_bearing_key(record), "value-bearing key found in private source map record", errors)


def validate_v014_private_processed_value_source_map_authorized_fill(
    manifest_path: Path = MANIFEST_PATH,
    *,
    require_private_authorized_fill: bool = False,
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
        "authorized_private_processed_value_source_map_fill_only",
        "previous_fill_request_consumed",
        "previous_capture_diagnostic_consumed",
        "project_metadata_hash_sibling_scan_performed",
        "private_authorized_fill_diagnostic_written",
        "private_source_map_write_performed",
        "private_source_map_staged_for_future_materialization",
    ):
        require(scope.get(key) is True, f"phase_scope_controls.{key} must be true", errors)
    for key in (
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

    require(manifest.get("authorized_fill_summary") == summary, "manifest summary mismatch", errors)
    require(summary.get("fill_request_item_count") == 149, "fill request item count mismatch", errors)
    require(summary.get("unique_private_ref_count") == 137, "unique ref count mismatch", errors)
    require(summary.get("duplicate_private_ref_item_count") == 12, "duplicate ref count mismatch", errors)
    require(summary.get("authorized_filled_item_count") == 36, "authorized filled count mismatch", errors)
    require(summary.get("authorized_unfilled_item_count") == 113, "authorized unfilled count mismatch", errors)
    require(summary.get("authorized_filled_unique_ref_count") == 36, "filled unique ref count mismatch", errors)
    require(summary.get("authorized_unfilled_unique_ref_count") == 101, "unfilled unique ref count mismatch", errors)
    require(summary.get("metadata_hash_sibling_source_file_count") == 1, "metadata source file count mismatch", errors)
    require(summary.get("metadata_hash_sibling_record_count") == 36, "metadata sibling record count mismatch", errors)
    require(summary.get("source_map_records_written_count") == 36, "source map records written mismatch", errors)
    require(summary.get("source_map_authorized_fill_complete") is False, "authorized fill must remain incomplete", errors)
    require(summary.get("raw_to_processed_value_comparison_performed") is False, "comparison must be false", errors)
    require(summary.get("comparable_value_pair_count") == 0, "comparable pair count must be zero", errors)
    require(summary.get("business_value_consistency_verified") is False, "business consistency must be false", errors)

    readiness = manifest.get("value_matching_readiness", {})
    require(readiness.get("fill_request_item_count") == 149, "readiness fill request count mismatch", errors)
    require(readiness.get("private_processed_value_fingerprint_count") == 36, "readiness fingerprint count mismatch", errors)
    require(readiness.get("source_map_authorized_fill_complete") is False, "readiness fill complete must be false", errors)
    require(readiness.get("source_map_authorized_unfilled_count") == 113, "readiness unfilled count mismatch", errors)
    require(readiness.get("processed_value_materialization_replay_performed") is False, "readiness materialization must be false", errors)
    require(readiness.get("raw_to_processed_value_comparison_performed") is False, "readiness comparison must be false", errors)
    require(readiness.get("comparable_value_pair_count") == 0, "readiness comparable pair count must be zero", errors)
    require(readiness.get("business_value_consistency_verified") is False, "readiness business consistency must be false", errors)
    require(
        readiness.get("final_goal_closeout_difference_report_required_if_repeated") is True,
        "difference report obligation must remain true",
        errors,
    )

    for key in (
        "processed_value_materialization_replay_performed",
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

    check_private_authorized_fill(
        require_private_authorized_fill=require_private_authorized_fill,
        expected_filled_count=int(summary.get("authorized_filled_item_count", 0)),
        expected_unfilled_count=int(summary.get("authorized_unfilled_item_count", 0)),
        errors=errors,
    )

    if errors:
        raise ValidationError("\n".join(errors))
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-private-authorized-fill", action="store_true")
    args = parser.parse_args(argv)
    manifest = validate_v014_private_processed_value_source_map_authorized_fill(
        require_private_authorized_fill=args.require_private_authorized_fill
    )
    summary = manifest["authorized_fill_summary"]
    print(
        "PASS: KMFA v0.1.4 authorized private processed source-map fill validated "
        f"(filled={summary['authorized_filled_item_count']}, "
        f"unfilled={summary['authorized_unfilled_item_count']}, "
        "materialization=false, business_consistency=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
