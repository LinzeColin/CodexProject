#!/usr/bin/env python3
"""Validate KMFA v0.1.4 post-resolution readiness recheck artifacts."""

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

from KMFA.tools.v014_processed_value_source_map_completion_post_resolution_readiness_recheck import (  # noqa: E402
    DECISION,
    GO_NO_GO_PATH,
    GO_NO_GO_RECORD_PATH,
    MANIFEST_PATH,
    MATRIX_PATH,
    METADATA_GO_NO_GO_PATH,
    METADATA_MANIFEST_PATH,
    METADATA_MATRIX_PATH,
    METADATA_SUMMARY_PATH,
    NEXT_REQUIRED_INPUT,
    PHASE_ID,
    PRIVATE_BLOCKER_QUEUE_PATH,
    PRIVATE_DIAGNOSTIC_PATH,
    PRIVATE_REAPPLICATION_CANDIDATE_QUEUE_PATH,
    PRIVATE_REPORT_PATH,
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
PRIVATE_ARTIFACTS = [
    PRIVATE_DIAGNOSTIC_PATH,
    PRIVATE_REAPPLICATION_CANDIDATE_QUEUE_PATH,
    PRIVATE_BLOCKER_QUEUE_PATH,
    PRIVATE_REPORT_PATH,
]
FORBIDDEN_PUBLIC_PATTERNS = [
    re.compile(re.escape(RAW_DOWNLOADS_MARKER)),
    re.compile(re.escape(RAW_INBOX_MARKER)),
    re.compile(re.escape(".codex_private_runtime")),
    re.compile(r"\.(xlsx|xlsm|xls|zip|pdf)\b", re.IGNORECASE),
    re.compile(
        r'"(raw_file_name|archive_member_name|sheet_name|cell_address|raw_value|normalized_decimal|context_text|numeric_value_fingerprint|processed_value_fingerprint|value_fingerprint|sha256_private|target_slot_id|review_group_id|selected_candidate_record_ref|owner_supplied_mapping_ref)"',
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
    for key in (
        "raw_data_root_readonly_policy_active",
        "private_owner_22_group_response_read_by_this_phase",
        "private_resolution_application_diagnostic_read_by_this_phase",
        "private_resolution_application_result_read_by_this_phase",
        "private_resolution_application_applied_queue_read_by_this_phase",
        "private_post_resolution_readiness_diagnostic_written_by_this_phase",
        "private_post_resolution_reapplication_candidate_queue_written_by_this_phase",
    ):
        _require_true(f"raw_boundary.{key}", raw_boundary.get(key))
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


def _check_private_readiness(summary: dict[str, Any]) -> None:
    for path in PRIVATE_ARTIFACTS:
        if not path.exists():
            raise ValidationError(f"missing private artifact: {path}")
        if not _git_check_ignored(path):
            raise ValidationError(f"private artifact is not gitignored: {path}")
        tracked = _git_output(["ls-files", "--", path.as_posix()])
        if tracked:
            raise ValidationError(f"private artifact is tracked: {path}")
    diagnostic = _read_json(PRIVATE_DIAGNOSTIC_PATH)
    candidate_rows = _read_jsonl(PRIVATE_REAPPLICATION_CANDIDATE_QUEUE_PATH)
    blocker_rows = _read_jsonl(PRIVATE_BLOCKER_QUEUE_PATH)
    _require_equal("diagnostic.phase_id", diagnostic.get("phase_id"), PHASE_ID)
    _require_equal("diagnostic.task_id", diagnostic.get("task_id"), TASK_ID)
    _require_equal("diagnostic.decision", diagnostic.get("decision"), DECISION)
    _require_equal("diagnostic.owner_exclusion_resolution_applied_count", diagnostic.get("owner_exclusion_resolution_applied_count"), 36)
    _require_equal("diagnostic.corrected_source_resolution_applied_count", diagnostic.get("corrected_source_resolution_applied_count"), 0)
    _require_equal("diagnostic.post_resolution_actionable_group_decision_count", diagnostic.get("post_resolution_actionable_group_decision_count"), 19)
    _require_equal("diagnostic.post_resolution_reapplication_candidate_group_count", diagnostic.get("post_resolution_reapplication_candidate_group_count"), 15)
    _require_equal("diagnostic.post_resolution_reapplication_candidate_count", diagnostic.get("post_resolution_reapplication_candidate_count"), 77)
    _require_equal("diagnostic.post_resolution_blocker_group_count", diagnostic.get("post_resolution_blocker_group_count"), 3)
    _require_true("diagnostic.source_map_completion_reapplication_ready", diagnostic.get("source_map_completion_reapplication_ready"))
    _require_false("diagnostic.source_map_completion_reapplication_performed", diagnostic.get("source_map_completion_reapplication_performed_by_this_phase"))
    _require_equal("diagnostic.source_map_records_applied_count", diagnostic.get("source_map_records_applied_count"), 0)
    _require_false("diagnostic.raw_inbox_accessed", diagnostic.get("raw_inbox_accessed"))
    _require_equal("private candidate queue length", len(candidate_rows), 15)
    _require_equal("private candidate count sum", sum(int(row.get("linked_application_blocker_count", 0)) for row in candidate_rows), 77)
    _require_equal("private blocker queue length", len(blocker_rows), 3)
    for row in candidate_rows:
        _require_true("candidate readiness", row.get("source_map_reapplication_ready"))
        _require_false("candidate reapplication performed", row.get("source_map_reapplication_performed_by_this_phase"))
        _require_false("candidate raw comparison", row.get("raw_to_processed_value_comparison_performed"))
        _require_false("candidate full reconciliation", row.get("full_reconciliation_allowed"))
    _require_equal("summary candidate group count", summary.get("post_resolution_reapplication_candidate_group_count"), len(candidate_rows))
    _require_equal("summary candidate count", summary.get("post_resolution_reapplication_candidate_count"), 77)
    _require_equal("summary blocker group count", summary.get("post_resolution_blocker_group_count"), len(blocker_rows))


def _check_summary(summary: dict[str, Any], matrix: dict[str, Any], go_no_go: dict[str, Any], manifest: dict[str, Any]) -> None:
    _require_equal("summary.phase_id", summary.get("phase_id"), PHASE_ID)
    _require_equal("summary.task_id", summary.get("task_id"), TASK_ID)
    _require_equal("summary.version", summary.get("version"), VERSION)
    _require_equal("summary.status", summary.get("status"), STATUS)
    _require_equal("summary.decision", summary.get("decision"), DECISION)
    _require_equal("summary.original_application_blocker_queue_count", summary.get("original_application_blocker_queue_count"), 113)
    _require_equal("summary.source_linked_application_blocker_count", summary.get("source_linked_application_blocker_count"), 77)
    _require_equal("summary.source_unlinked_application_blocker_count", summary.get("source_unlinked_application_blocker_count"), 36)
    _require_equal("summary.owner_exclusion_resolution_applied_count", summary.get("owner_exclusion_resolution_applied_count"), 36)
    _require_equal("summary.corrected_source_resolution_applied_count", summary.get("corrected_source_resolution_applied_count"), 0)
    _require_equal("summary.post_resolution_actionable_group_decision_count", summary.get("post_resolution_actionable_group_decision_count"), 19)
    _require_equal("summary.post_resolution_reapplication_candidate_group_count", summary.get("post_resolution_reapplication_candidate_group_count"), 15)
    _require_equal("summary.post_resolution_reapplication_candidate_count", summary.get("post_resolution_reapplication_candidate_count"), 77)
    _require_equal("summary.post_resolution_blocker_group_count", summary.get("post_resolution_blocker_group_count"), 3)
    _require_equal("summary.post_resolution_open_unlinked_blocker_count", summary.get("post_resolution_open_unlinked_blocker_count"), 0)
    for key in (
        "post_resolution_readiness_recheck_performed_by_this_phase",
        "source_map_completion_reapplication_ready",
        "private_post_resolution_diagnostic_written",
        "private_post_resolution_diagnostic_gitignored",
        "private_post_resolution_candidate_queue_written",
        "private_post_resolution_candidate_queue_gitignored",
        "private_post_resolution_blocker_queue_written",
        "private_post_resolution_blocker_queue_gitignored",
    ):
        _require_true(f"summary.{key}", summary.get(key))
    for key in (
        "source_map_completion_reapplication_performed_by_this_phase",
        "source_map_mutation_performed_by_this_phase",
        "processed_value_materialization_replay_ready",
        "raw_to_processed_value_comparison_ready",
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
    _require_equal("summary.source_map_records_applied_count", summary.get("source_map_records_applied_count"), 0)
    _require_equal("summary.next_required_input", summary.get("next_required_input"), NEXT_REQUIRED_INPUT)
    _check_raw_boundary(summary["raw_boundary"])
    _check_public_safety(summary["public_safety"])
    _require_equal("matrix.phase_id", matrix.get("phase_id"), PHASE_ID)
    _require_equal("matrix.post_resolution_check_count", matrix.get("post_resolution_check_count"), 8)
    _require_equal("matrix.post_resolution_pass_count", matrix.get("post_resolution_pass_count"), 8)
    _require_equal("matrix.post_resolution_fail_count", matrix.get("post_resolution_fail_count"), 0)
    _require_equal("matrix.post_resolution_reapplication_candidate_count", matrix.get("post_resolution_reapplication_candidate_count"), 77)
    _require_equal("matrix.post_resolution_actionable_group_decision_count", matrix.get("post_resolution_actionable_group_decision_count"), 19)
    _require_equal("matrix.post_resolution_candidate_group_count", matrix.get("post_resolution_candidate_group_count"), 15)
    _require_equal("matrix.post_resolution_blocker_group_count", matrix.get("post_resolution_blocker_group_count"), 3)
    _require_true("matrix.source_map_completion_reapplication_ready", matrix.get("source_map_completion_reapplication_ready"))
    _require_false("matrix.source_map_completion_reapplication_performed", matrix.get("source_map_completion_reapplication_performed_by_this_phase"))
    _require_equal("matrix.source_map_records_applied_count", matrix.get("source_map_records_applied_count"), 0)
    _require_false("matrix.raw comparison", matrix.get("raw_to_processed_value_comparison_performed_by_this_phase"))
    _require_false("matrix.full reconciliation", matrix.get("full_reconciliation_allowed"))
    _require_equal("go_no_go.next_required_input", go_no_go.get("next_required_input"), NEXT_REQUIRED_INPUT)
    _require_equal("go_no_go.post_resolution_reapplication_candidate_count", go_no_go.get("post_resolution_reapplication_candidate_count"), 77)
    _require_true("go_no_go.source_map_completion_reapplication_ready", go_no_go.get("source_map_completion_reapplication_ready"))
    _require_false("go_no_go.source_map_completion_reapplication_performed", go_no_go.get("source_map_completion_reapplication_performed_by_this_phase"))
    _require_equal("go_no_go.source_map_records_applied_count", go_no_go.get("source_map_records_applied_count"), 0)
    _require_false("go_no_go.raw comparison", go_no_go.get("raw_to_processed_value_comparison_performed_by_this_phase"))
    _require_equal("manifest.phase_id", manifest.get("phase_id"), PHASE_ID)
    _require_equal("manifest.summary", manifest.get("summary"), summary)
    _require_equal("manifest.matrix", manifest.get("matrix"), matrix)
    _require_equal("manifest.go_no_go_report", manifest.get("go_no_go_report"), go_no_go)


def validate(*, require_private_readiness: bool = False) -> dict[str, Any]:
    _check_public_artifacts()
    _check_no_raw_private_files_tracked()
    summary = _read_json(SUMMARY_PATH)
    manifest = _read_json(MANIFEST_PATH)
    go_no_go = _read_json(GO_NO_GO_PATH)
    matrix = _read_json(MATRIX_PATH)
    _require_equal("metadata summary", _read_json(METADATA_SUMMARY_PATH), summary)
    _require_equal("metadata manifest", _read_json(METADATA_MANIFEST_PATH), manifest)
    _require_equal("metadata go/no-go", _read_json(METADATA_GO_NO_GO_PATH), go_no_go)
    _require_equal("metadata matrix", _read_json(METADATA_MATRIX_PATH), matrix)
    _check_summary(summary, matrix, go_no_go, manifest)
    if require_private_readiness:
        _check_private_readiness(summary)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-private-readiness", action="store_true")
    args = parser.parse_args()
    try:
        manifest = validate(require_private_readiness=args.require_private_readiness)
    except ValidationError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    summary = manifest["summary"]
    print(
        "PASS: KMFA v0.1.4 post-resolution readiness recheck artifacts validated "
        f"(decision={summary['decision']}, candidates={summary['post_resolution_reapplication_candidate_count']}, "
        f"source_map_records={summary['source_map_records_applied_count']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
