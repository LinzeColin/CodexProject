#!/usr/bin/env python3
"""Validate KMFA v0.1.4 corrected-source/owner-exclusion retry input artifacts."""

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

from KMFA.tools.v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_input_retry import (  # noqa: E402
    DECISION,
    GO_NO_GO_PATH,
    GO_NO_GO_RECORD_PATH,
    MANIFEST_PATH,
    MATRIX_PATH,
    METADATA_GO_NO_GO_PATH,
    METADATA_MANIFEST_PATH,
    METADATA_MATRIX_PATH,
    METADATA_SUMMARY_PATH,
    NEXT_RECOMMENDED_PHASE,
    OWNER_EXCLUSION_DECISION,
    PHASE_ID,
    PRIVATE_RETRY_DIAGNOSTIC_PATH,
    PRIVATE_RETRY_QUEUE_PATH,
    PRIVATE_RETRY_REPORT_PATH,
    PRIVATE_RETRY_TEMPLATE_PATH,
    REPORT_PATH,
    RISK_REGISTER_PATH,
    ROLLBACK_PATH,
    STATUS,
    SUMMARY_PATH,
    TASK_ID,
    TEST_RESULTS_PATH,
    VERSION,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DOWNLOADS_MARKER = "/Users/" + "linzezhang/Downloads"
RAW_INBOX_MARKER = "KMFA" + "_MetaData"
PUBLIC_ARTIFACTS = [
    SUMMARY_PATH,
    MANIFEST_PATH,
    GO_NO_GO_PATH,
    MATRIX_PATH,
    REPORT_PATH,
    GO_NO_GO_RECORD_PATH,
    TEST_RESULTS_PATH,
    RISK_REGISTER_PATH,
    ROLLBACK_PATH,
    METADATA_SUMMARY_PATH,
    METADATA_MANIFEST_PATH,
    METADATA_GO_NO_GO_PATH,
    METADATA_MATRIX_PATH,
]
FORBIDDEN_PUBLIC_PATTERNS = [
    re.compile(re.escape(RAW_DOWNLOADS_MARKER)),
    re.compile(re.escape(RAW_INBOX_MARKER)),
    re.compile(re.escape(".codex_private_runtime")),
    re.compile(r"\.(xlsx|xlsm|xls|zip|pdf)\b", re.IGNORECASE),
    re.compile(
        r'"(raw_file_name|archive_member_name|sheet_name|cell_address|raw_value|normalized_decimal|context_text|numeric_value_fingerprint|processed_value_fingerprint|value_fingerprint|sha256_private|target_slot_id|review_group_id|context_group)"',
        re.IGNORECASE,
    ),
    re.compile(r"sha256:[0-9a-f]{64}"),
    re.compile(r'"[0-9a-f]{64}"'),
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
]


class ValidationError(Exception):
    pass


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ValidationError(f"missing artifact: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValidationError(f"{path} must contain a JSON object")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise ValidationError(f"missing JSONL artifact: {path}")
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValidationError(f"{path} must contain JSON objects")
        rows.append(value)
    return rows


def _require_equal(label: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        raise ValidationError(f"{label}: expected {expected!r}, got {actual!r}")


def _require_true(label: str, value: Any) -> None:
    if value is not True:
        raise ValidationError(f"{label}: expected true, got {value!r}")


def _require_false(label: str, value: Any) -> None:
    if value is not False:
        raise ValidationError(f"{label}: expected false, got {value!r}")


def _git_output(args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        cwd=PROJECT_ROOT.parent,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise ValidationError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def _git_check_ignored(path: Path) -> bool:
    return subprocess.run(["git", "check-ignore", "-q", path.as_posix()], cwd=PROJECT_ROOT.parent, check=False).returncode == 0


def _check_public_artifacts() -> None:
    for path in PUBLIC_ARTIFACTS:
        if not path.exists():
            raise ValidationError(f"missing public artifact: {path}")
        text = path.read_text(encoding="utf-8")
        for pattern in FORBIDDEN_PUBLIC_PATTERNS:
            if pattern.search(text):
                raise ValidationError(f"forbidden public marker {pattern.pattern!r} in {path}")


def _check_no_raw_private_files_tracked() -> None:
    tracked = _git_output(["ls-files", "KMFA"]).splitlines()
    forbidden = re.compile(
        r"\.codex_private_runtime|"
        + re.escape(RAW_DOWNLOADS_MARKER)
        + "|"
        + re.escape(RAW_INBOX_MARKER)
        + r"|\.(zip|xlsx|xlsm|xls|pdf|sqlite|sqlite3|db|key|pem|p12|pfx)$",
        re.IGNORECASE,
    )
    hits = [path for path in tracked if forbidden.search(path)]
    if hits:
        raise ValidationError("tracked raw/private files detected: " + ", ".join(hits[:20]))


def _check_raw_boundary(raw_boundary: dict[str, Any]) -> None:
    _require_true("raw_boundary.raw_data_root_readonly_policy_active", raw_boundary.get("raw_data_root_readonly_policy_active"))
    _require_true("raw_boundary.private_prior_template_read_by_this_phase", raw_boundary.get("private_prior_template_read_by_this_phase"))
    _require_true(
        "raw_boundary.private_prior_application_blocker_queue_read_by_this_phase",
        raw_boundary.get("private_prior_application_blocker_queue_read_by_this_phase"),
    )
    _require_true(
        "raw_boundary.private_prior_raw_matching_dry_run_read_by_this_phase",
        raw_boundary.get("private_prior_raw_matching_dry_run_read_by_this_phase"),
    )
    _require_true("raw_boundary.private_retry_input_written_by_this_phase", raw_boundary.get("private_retry_input_written_by_this_phase"))
    for key in (
        "raw_inbox_read_performed_by_this_phase",
        "raw_inbox_list_performed_by_this_phase",
        "raw_inbox_stat_performed_by_this_phase",
        "raw_inbox_hash_or_value_fingerprint_performed_by_this_phase",
        "raw_inbox_file_content_hash_performed_by_this_phase",
        "raw_inbox_parse_performed_by_this_phase",
        "raw_inbox_field_or_header_read_performed_by_this_phase",
        "raw_inbox_value_extraction_performed_by_this_phase",
        "raw_inbox_write_performed_by_this_phase",
        "raw_inbox_delete_performed_by_this_phase",
        "raw_inbox_move_performed_by_this_phase",
        "raw_inbox_rename_performed_by_this_phase",
        "raw_inbox_overwrite_performed_by_this_phase",
        "raw_inbox_copy_performed_by_this_phase",
        "raw_inbox_normalize_performed_by_this_phase",
        "raw_inbox_mutated_by_this_phase",
    ):
        _require_false(f"raw_boundary.{key}", raw_boundary.get(key))


def _check_public_safety(public_safety: dict[str, Any]) -> None:
    _require_true("public_safety.public_safe_aggregate_only", public_safety.get("public_safe_aggregate_only"))
    for key, value in public_safety.items():
        if key == "public_safe_aggregate_only":
            continue
        _require_false(f"public_safety.{key}", value)


def _check_private_retry(summary: dict[str, Any]) -> None:
    template = _read_json(PRIVATE_RETRY_TEMPLATE_PATH)
    diagnostic = _read_json(PRIVATE_RETRY_DIAGNOSTIC_PATH)
    queue = _read_jsonl(PRIVATE_RETRY_QUEUE_PATH)
    if not PRIVATE_RETRY_REPORT_PATH.exists():
        raise ValidationError(f"missing private retry report: {PRIVATE_RETRY_REPORT_PATH}")
    for path in (PRIVATE_RETRY_TEMPLATE_PATH, PRIVATE_RETRY_DIAGNOSTIC_PATH, PRIVATE_RETRY_QUEUE_PATH, PRIVATE_RETRY_REPORT_PATH):
        if not _git_check_ignored(path):
            raise ValidationError(f"private artifact is not gitignored: {path}")
        tracked = _git_output(["ls-files", "--", path.as_posix()])
        if tracked:
            raise ValidationError(f"private artifact is tracked: {path}")
    items = template.get("items")
    if not isinstance(items, list):
        raise ValidationError("private retry template items must be a list")
    _require_equal("private retry item count", len(items), 36)
    _require_equal("private retry queue count", len(queue), 36)
    _require_equal("diagnostic.private_retry_item_count", diagnostic.get("private_retry_item_count"), 36)
    _require_equal("diagnostic.owner_exclusion_retry_item_count", diagnostic.get("owner_exclusion_retry_item_count"), 36)
    _require_equal("diagnostic.corrected_source_retry_item_count", diagnostic.get("corrected_source_retry_item_count"), 0)
    _require_equal("diagnostic.no_raw_index_fingerprint_match_count", diagnostic.get("no_raw_index_fingerprint_match_count"), 36)
    _require_equal("diagnostic.zero_raw_index_occurrence_count", diagnostic.get("zero_raw_index_occurrence_count"), 36)
    for item in items:
        _require_equal("retry item decision", item.get("required_owner_decision_code"), OWNER_EXCLUSION_DECISION)
        _require_equal("retry item source match", item.get("source_match_status"), "no_raw_index_fingerprint_match")
        _require_equal("retry item raw occurrence count", item.get("source_raw_index_occurrence_count"), 0)
        _require_false("retry item resolution application allowed", item.get("resolution_application_allowed"))
    _require_equal("summary.private_retry_item_count", summary.get("private_retry_item_count"), len(items))


def _check_summary(summary: dict[str, Any], matrix: dict[str, Any], go_no_go: dict[str, Any], manifest: dict[str, Any]) -> None:
    _require_equal("summary.phase_id", summary.get("phase_id"), PHASE_ID)
    _require_equal("summary.task_id", summary.get("task_id"), TASK_ID)
    _require_equal("summary.version", summary.get("version"), VERSION)
    _require_equal("summary.status", summary.get("status"), STATUS)
    _require_equal("summary.decision", summary.get("decision"), DECISION)
    _require_true("summary.delegated_default_decision_applied", summary.get("delegated_default_decision_applied"))
    _require_equal("summary.private_retry_item_count", summary.get("private_retry_item_count"), 36)
    _require_equal("summary.owner_exclusion_retry_item_count", summary.get("owner_exclusion_retry_item_count"), 36)
    _require_equal("summary.corrected_source_retry_item_count", summary.get("corrected_source_retry_item_count"), 0)
    _require_equal("summary.retry_input_valid_count", summary.get("retry_input_valid_count"), 36)
    _require_equal("summary.retry_input_missing_count", summary.get("retry_input_missing_count"), 0)
    _require_true(
        "summary.resolution_application_readiness_allowed_next_phase",
        summary.get("resolution_application_readiness_allowed_next_phase"),
    )
    for key in (
        "resolution_application_allowed",
        "resolution_application_performed_by_this_phase",
        "source_map_mutation_performed_by_this_phase",
        "raw_to_processed_value_comparison_performed_by_this_phase",
        "full_reconciliation_allowed",
        "business_value_consistency_verified",
        "lineage_full_check_complete",
        "formal_report_allowed",
        "github_upload_performed",
        "app_reinstall_performed",
        "business_execution_performed",
    ):
        _require_false(f"summary.{key}", summary.get(key))
    _require_equal("summary.next_recommended_phase", summary.get("next_recommended_phase"), NEXT_RECOMMENDED_PHASE)
    _check_raw_boundary(summary["raw_boundary"])
    _check_public_safety(summary["public_safety"])
    _require_equal("matrix.phase_id", matrix.get("phase_id"), PHASE_ID)
    _require_equal("matrix.retry_check_count", matrix.get("retry_check_count"), 6)
    _require_equal("matrix.retry_check_pass_count", matrix.get("retry_check_pass_count"), 6)
    _require_true("matrix.all_retry_inputs_valid", matrix.get("all_retry_inputs_valid"))
    _require_equal("go_no_go.decision", go_no_go.get("decision"), DECISION)
    _require_true(
        "go_no_go.resolution_application_readiness_allowed_next_phase",
        go_no_go.get("resolution_application_readiness_allowed_next_phase"),
    )
    _require_false("go_no_go.resolution_application_performed_by_this_phase", go_no_go.get("resolution_application_performed_by_this_phase"))
    _require_equal("manifest.phase_id", manifest.get("phase_id"), PHASE_ID)
    _require_true("manifest.private_artifacts_gitignored", manifest.get("private_artifacts_gitignored"))


def validate(*, require_private_retry: bool = False) -> dict[str, Any]:
    summary = _read_json(SUMMARY_PATH)
    manifest = _read_json(MANIFEST_PATH)
    go_no_go = _read_json(GO_NO_GO_PATH)
    matrix = _read_json(MATRIX_PATH)
    metadata_summary = _read_json(METADATA_SUMMARY_PATH)
    metadata_manifest = _read_json(METADATA_MANIFEST_PATH)
    metadata_go_no_go = _read_json(METADATA_GO_NO_GO_PATH)
    metadata_matrix = _read_json(METADATA_MATRIX_PATH)
    _require_equal("metadata summary", metadata_summary, summary)
    _require_equal("metadata manifest", metadata_manifest, manifest)
    _require_equal("metadata go_no_go", metadata_go_no_go, go_no_go)
    _require_equal("metadata matrix", metadata_matrix, matrix)
    _check_summary(summary, matrix, go_no_go, manifest)
    _check_public_artifacts()
    _check_no_raw_private_files_tracked()
    if require_private_retry:
        _check_private_retry(summary)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-private-retry", action="store_true")
    args = parser.parse_args()
    manifest = validate(require_private_retry=args.require_private_retry)
    summary = manifest["summary"]
    print(
        "PASS: KMFA v0.1.4 corrected-source or owner-exclusion retry input artifacts validated "
        f"(decision={summary['decision']}, retry_items={summary['private_retry_item_count']})"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValidationError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
