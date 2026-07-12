from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PHASE_ID = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_GROUP_PARTIAL_APPLICATION"
TASK_ID = "KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-OWNER-GROUP-PARTIAL-APPLICATION-20260706"
VERSION = "0.1.4-owner-group-partial-application"
DIAGNOSTIC_CONCLUSION = "private_partial_owner_group_application_staged_full_reapplication_blocked"
NEXT_REQUIRED_INPUT = "resolve_non_actionable_group_decisions_before_full_source_map_reapplication"
EXPECTED_ROW_DECISION_COUNTS = {
    "CONFIRM_GROUP_CANDIDATE_RANK": 101,
    "KEEP_PENDING": 8,
    "REQUEST_MORE_DIAGNOSTICS": 4,
}

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
QUALITY_DIR = PROJECT_ROOT / "metadata" / "quality"
PRIVATE_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_processed_value_source_map_completion_owner_group_partial_application"
PRIVATE_RESULT_PATH = PRIVATE_DIR / "private_owner_group_partial_application_result.json"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_DIR / "private_owner_group_partial_application_diagnostic.json"

SUMMARY_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_group_partial_application_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_group_partial_application_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_group_partial_application_go_no_go_report.json"

PUBLIC_ARTIFACTS = [
    SUMMARY_PATH,
    MANIFEST_PATH,
    GO_NO_GO_PATH,
    HUMAN_DIR / "processed_value_source_map_completion_owner_group_partial_application_report.md",
    HUMAN_DIR / "go_no_go_record.md",
    HUMAN_DIR / "test_results.md",
    HUMAN_DIR / "risk_register.md",
    HUMAN_DIR / "rollback_plan.md",
    QUALITY_DIR / "v014_owner_group_partial_application_summary.json",
    QUALITY_DIR / "v014_owner_group_partial_application_manifest.json",
    QUALITY_DIR / "v014_owner_group_partial_application_go_no_go_report.json",
]

FORBIDDEN_PUBLIC_PATTERNS = [
    re.compile(r"/Users/linzezhang/Downloads"),
    re.compile(r"KMFA_MetaData"),
    re.compile(r"\.(xlsx|xlsm|xls|zip|pdf)\b", re.IGNORECASE),
    re.compile(r'"(target_slot_id|review_group_id|context_group|raw_file_name|archive_member_name|sheet_name|cell_address|raw_value|normalized_decimal|context_text)"', re.IGNORECASE),
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


def _require_equal(name: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        raise ValidationError(f"{name}: expected {expected!r}, got {actual!r}")


def _require_true(name: str, value: Any) -> None:
    if value is not True:
        raise ValidationError(f"{name}: expected True, got {value!r}")


def _require_false(name: str, value: Any) -> None:
    if value is not False:
        raise ValidationError(f"{name}: expected False, got {value!r}")


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
    forbidden_suffix = re.compile(r"\.(zip|xlsx|xlsm|xls|pdf|sqlite|sqlite3|db|key|pem|p12|pfx)$", re.IGNORECASE)
    hits = [path for path in tracked if forbidden_suffix.search(path) or ".codex_private_runtime" in path]
    if hits:
        raise ValidationError("forbidden tracked raw/private files: " + ", ".join(hits[:20]))


def _check_raw_boundary(boundary: dict[str, Any]) -> None:
    _require_true("raw_boundary.raw_data_root_readonly_policy_active", boundary.get("raw_data_root_readonly_policy_active"))
    for key in (
        "raw_inbox_read_performed_by_this_phase",
        "raw_inbox_list_performed_by_this_phase",
        "raw_inbox_stat_performed_by_this_phase",
        "raw_inbox_hash_or_value_fingerprint_performed_by_this_phase",
        "raw_inbox_write_performed_by_this_phase",
        "raw_inbox_delete_performed_by_this_phase",
        "raw_inbox_move_performed_by_this_phase",
        "raw_inbox_rename_performed_by_this_phase",
        "raw_inbox_overwrite_performed_by_this_phase",
        "raw_inbox_copy_performed_by_this_phase",
        "raw_inbox_normalize_performed_by_this_phase",
        "raw_inbox_mutated_by_this_phase",
    ):
        _require_false(f"raw_boundary.{key}", boundary.get(key))


def _check_public_safety(safety: dict[str, Any]) -> None:
    _require_true("public_safety.public_safe_aggregate_only", safety.get("public_safe_aggregate_only"))
    for key in (
        "private_actionable_plan_committed",
        "private_response_draft_committed",
        "private_partial_application_result_committed",
        "private_diagnostic_committed",
        "raw_file_committed",
        "raw_filename_committed",
        "raw_archive_member_name_committed",
        "field_header_plaintext_committed",
        "row_value_committed",
        "business_value_committed",
        "credential_or_secret_committed",
    ):
        _require_false(f"public_safety.{key}", safety.get(key))


def _check_private_application() -> None:
    result = _read_json(PRIVATE_RESULT_PATH)
    diagnostic = _read_json(PRIVATE_DIAGNOSTIC_PATH)
    _require_equal("result.phase_id", result.get("phase_id"), PHASE_ID)
    _require_equal("result.task_id", result.get("task_id"), TASK_ID)
    _require_equal("result.version", result.get("version"), VERSION)
    _require_equal("diagnostic.phase_id", diagnostic.get("phase_id"), PHASE_ID)
    app_summary = result.get("partial_application_summary", {})
    _require_equal("private.source_response_row_count", app_summary.get("source_response_row_count"), 113)
    _require_equal("private.partial_application_group_count", app_summary.get("private_partial_application_group_count"), 19)
    _require_equal("private.partial_application_target_slot_count", app_summary.get("private_partial_application_target_slot_count"), 101)
    _require_equal("private.blocked_group_count", app_summary.get("private_blocked_group_count"), 3)
    _require_equal("private.blocked_target_slot_count", app_summary.get("private_blocked_target_slot_count"), 12)
    _require_equal("private.row_decision_code_counts", app_summary.get("row_decision_code_counts"), EXPECTED_ROW_DECISION_COUNTS)
    _require_equal("private.missing_group_decision_row_count", app_summary.get("missing_group_decision_row_count"), 0)
    _require_true("private.partial_application_staged", app_summary.get("private_partial_application_staged"))
    _require_false("private.canonical_source_map_mutated", app_summary.get("canonical_source_map_mutated"))
    _require_false("private.full_source_map_completion_reapplication_ready", app_summary.get("full_source_map_completion_reapplication_ready"))
    applied_rows = result.get("applied_rows", [])
    blocked_rows = result.get("blocked_rows", [])
    if not isinstance(applied_rows, list) or not isinstance(blocked_rows, list):
        raise ValidationError("private result row lists must be lists")
    _require_equal("private.applied_rows length", len(applied_rows), 101)
    _require_equal("private.blocked_rows length", len(blocked_rows), 12)
    _check_raw_boundary(result.get("raw_boundary", {}))
    for path in (PRIVATE_RESULT_PATH, PRIVATE_DIAGNOSTIC_PATH):
        ignore = subprocess.run(["git", "check-ignore", "-q", path.as_posix()], cwd=PROJECT_ROOT.parent, check=False)
        _require_equal(f"{path}.gitignored", ignore.returncode, 0)
        _require_equal(f"{path}.tracked", _git_output(["ls-files", path.as_posix()]), "")


def validate(*, require_private_application: bool = False) -> dict[str, Any]:
    summary = _read_json(SUMMARY_PATH)
    manifest = _read_json(MANIFEST_PATH)
    go_no_go = _read_json(GO_NO_GO_PATH)
    metadata_summary = _read_json(QUALITY_DIR / "v014_owner_group_partial_application_summary.json")
    metadata_manifest = _read_json(QUALITY_DIR / "v014_owner_group_partial_application_manifest.json")
    metadata_go_no_go = _read_json(QUALITY_DIR / "v014_owner_group_partial_application_go_no_go_report.json")

    _require_equal("metadata summary copy", metadata_summary, summary)
    _require_equal("metadata manifest copy", metadata_manifest, manifest)
    _require_equal("metadata go/no-go copy", metadata_go_no_go, go_no_go)
    _require_equal("summary.phase_id", summary.get("phase_id"), PHASE_ID)
    _require_equal("summary.task_id", summary.get("task_id"), TASK_ID)
    _require_equal("summary.version", summary.get("version"), VERSION)
    _require_equal("summary.decision", summary.get("decision"), "NO_GO")
    _require_equal("summary.diagnostic_conclusion", summary.get("diagnostic_conclusion"), DIAGNOSTIC_CONCLUSION)
    _require_equal("summary.next_required_input", summary.get("next_required_input"), NEXT_REQUIRED_INPUT)
    _require_equal("summary.source_actionable_plan_decision", summary.get("source_actionable_plan_decision"), "NO_GO")
    _require_equal("summary.source_response_row_count", summary.get("source_response_row_count"), 113)
    _require_equal("summary.private_partial_application_group_count", summary.get("private_partial_application_group_count"), 19)
    _require_equal("summary.private_partial_application_target_slot_count", summary.get("private_partial_application_target_slot_count"), 101)
    _require_equal("summary.private_blocked_group_count", summary.get("private_blocked_group_count"), 3)
    _require_equal("summary.private_blocked_target_slot_count", summary.get("private_blocked_target_slot_count"), 12)
    _require_equal("summary.row_decision_code_counts", summary.get("row_decision_code_counts"), EXPECTED_ROW_DECISION_COUNTS)
    _require_equal("summary.missing_group_decision_row_count", summary.get("missing_group_decision_row_count"), 0)
    for key in (
        "private_partial_application_staged",
        "private_partial_application_result_written",
        "private_partial_application_result_gitignored",
        "private_diagnostic_written",
        "private_diagnostic_gitignored",
        "processed_value_materialization_replay_ready",
    ):
        _require_true(f"summary.{key}", summary.get(key))
    for key in (
        "canonical_source_map_mutated",
        "active_owner_authorized_fill_record_written",
        "source_map_completion_reapplication_ready",
        "source_map_completion_reapplication_performed",
        "processed_value_materialization_replay_performed",
        "raw_to_processed_value_comparison_performed",
        "business_value_consistency_verified",
        "lineage_full_check_complete",
        "formal_report_allowed",
        "github_upload_performed",
        "app_reinstall_performed",
        "business_execution_performed",
    ):
        _require_false(f"summary.{key}", summary.get(key))
    _require_equal("summary.canonical_source_map_records_applied_count", summary.get("canonical_source_map_records_applied_count"), 0)
    _check_raw_boundary(summary.get("raw_boundary", {}))
    _check_public_safety(summary.get("public_safety", {}))
    _require_equal("go_no_go.decision", go_no_go.get("decision"), "NO_GO")
    _require_equal("go_no_go.private_partial_application_target_slot_count", go_no_go.get("private_partial_application_target_slot_count"), 101)
    _require_equal("go_no_go.private_blocked_target_slot_count", go_no_go.get("private_blocked_target_slot_count"), 12)
    _require_true("go_no_go.private_partial_application_staged", go_no_go.get("private_partial_application_staged"))
    _require_false("go_no_go.canonical_source_map_mutated", go_no_go.get("canonical_source_map_mutated"))
    _require_false("go_no_go.reapplication_ready", go_no_go.get("source_map_completion_reapplication_ready"))
    _require_true("go_no_go.materialization_precheck_ready", go_no_go.get("processed_value_materialization_replay_ready"))
    _require_false("go_no_go.raw_compare", go_no_go.get("raw_to_processed_value_comparison_performed"))
    _require_false("go_no_go.business_consistency", go_no_go.get("business_value_consistency_verified"))
    _require_false("go_no_go.github_upload", go_no_go.get("github_upload_performed"))
    _require_false("go_no_go.app_reinstall", go_no_go.get("app_reinstall_performed"))
    _require_false("go_no_go.business_execution", go_no_go.get("business_execution_performed"))
    _require_equal("go_no_go.blocked_until", go_no_go.get("blocked_until"), NEXT_REQUIRED_INPUT)
    _require_equal("manifest.summary", manifest.get("summary"), summary)
    _require_equal("manifest.go_no_go", manifest.get("go_no_go"), go_no_go)
    _check_public_artifacts()
    _check_no_raw_private_files_tracked()
    if require_private_application:
        _check_private_application()
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-private-application", action="store_true")
    args = parser.parse_args()
    manifest = validate(require_private_application=args.require_private_application)
    print(
        "PASS: KMFA v0.1.4 owner group partial application validated "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"partial_slots={manifest['summary']['private_partial_application_target_slot_count']}, "
        f"blocked_slots={manifest['summary']['private_blocked_target_slot_count']})"
    )


if __name__ == "__main__":
    main()
