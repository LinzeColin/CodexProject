from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PHASE_ID = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_NON_ACTIONABLE_GROUP_RESPONSE_INTAKE"
TASK_ID = "KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-NON-ACTIONABLE-GROUP-RESPONSE-INTAKE-20260706"
VERSION = "0.1.4-non-actionable-group-response-intake"
DIAGNOSTIC_CONCLUSION = "non_actionable_group_response_intake_has_no_owner_authorized_ready_rows"
NEXT_REQUIRED_INPUT = "owner_or_authorized_delegate_updates_non_actionable_group_response_template_before_full_source_map_application"
EXPECTED_RESOLUTION_CODE_COUNTS = {
    "KEEP_PENDING_WITH_REASON": 2,
    "REQUEST_ADDITIONAL_SOURCE_EVIDENCE": 1,
}
EXPECTED_REASON_CODE_COUNTS = {
    "codex_cannot_infer_missing_value_source": 1,
    "codex_cannot_infer_non_numeric_business_mapping": 2,
}
EXPECTED_STATUS_GROUP_COUNTS = {
    "auto_unmatched_requires_owner_review": 1,
    "requires_non_numeric_owner_mapping": 2,
}

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
QUALITY_DIR = PROJECT_ROOT / "metadata" / "quality"
PRIVATE_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_processed_value_source_map_completion_non_actionable_group_response_intake"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_DIR / "private_non_actionable_group_response_intake_diagnostic.json"
PRIVATE_PENDING_QUEUE_PATH = PRIVATE_DIR / "private_non_actionable_group_response_pending_queue.json"

SUMMARY_PATH = MACHINE_DIR / "processed_value_source_map_completion_non_actionable_group_response_intake_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_value_source_map_completion_non_actionable_group_response_intake_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_value_source_map_completion_non_actionable_group_response_intake_go_no_go_report.json"

PUBLIC_ARTIFACTS = [
    SUMMARY_PATH,
    MANIFEST_PATH,
    GO_NO_GO_PATH,
    HUMAN_DIR / "processed_value_source_map_completion_non_actionable_group_response_intake_report.md",
    HUMAN_DIR / "go_no_go_record.md",
    HUMAN_DIR / "test_results.md",
    HUMAN_DIR / "risk_register.md",
    HUMAN_DIR / "rollback_plan.md",
    QUALITY_DIR / "v014_non_actionable_group_response_intake_summary.json",
    QUALITY_DIR / "v014_non_actionable_group_response_intake_manifest.json",
    QUALITY_DIR / "v014_non_actionable_group_response_intake_go_no_go_report.json",
]

FORBIDDEN_PUBLIC_PATTERNS = [
    re.compile(r"/Users/linzezhang/Downloads"),
    re.compile(r"KMFA_MetaData"),
    re.compile(r"\.(xlsx|xlsm|xls|zip|pdf)\b", re.IGNORECASE),
    re.compile(
        r'"(target_slot_id|target_slot_ids|review_group_id|raw_file_name|archive_member_name|sheet_name|cell_address|raw_value|normalized_decimal|context_text)"',
        re.IGNORECASE,
    ),
    re.compile(r"sha256:[0-9a-f]{64}"),
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
]
FORBIDDEN_PRIVATE_KEYS = {
    "raw_file_name",
    "archive_member_name",
    "sheet_name",
    "cell_address",
    "raw_value",
    "normalized_decimal",
    "context_text",
}


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
        "private_response_template_committed",
        "private_intake_diagnostic_committed",
        "private_pending_queue_committed",
        "raw_file_committed",
        "raw_filename_committed",
        "raw_archive_member_name_committed",
        "field_header_plaintext_committed",
        "row_value_committed",
        "business_value_committed",
        "processed_value_fingerprint_committed",
        "credential_or_secret_committed",
    ):
        _require_false(f"public_safety.{key}", safety.get(key))


def _check_forbidden_private_keys(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        forbidden = FORBIDDEN_PRIVATE_KEYS.intersection(value)
        if forbidden:
            raise ValidationError(f"{path} contains forbidden copied raw keys: {sorted(forbidden)}")
        for key, child in value.items():
            _check_forbidden_private_keys(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _check_forbidden_private_keys(child, f"{path}[{index}]")


def _check_private_file_ignored_and_untracked(path: Path) -> None:
    result = subprocess.run(["git", "check-ignore", "-q", path.as_posix()], cwd=PROJECT_ROOT.parent, check=False)
    _require_equal(f"{path}.gitignored", result.returncode, 0)
    _require_equal(f"{path}.tracked", _git_output(["ls-files", path.as_posix()]), "")


def _check_private_response_intake() -> None:
    diagnostic = _read_json(PRIVATE_DIAGNOSTIC_PATH)
    pending_queue = _read_json(PRIVATE_PENDING_QUEUE_PATH)
    for name, payload in (("diagnostic", diagnostic), ("pending_queue", pending_queue)):
        _require_equal(f"{name}.phase_id", payload.get("phase_id"), PHASE_ID)
        _require_equal(f"{name}.task_id", payload.get("task_id"), TASK_ID)
        _require_equal(f"{name}.version", payload.get("version"), VERSION)
        _check_forbidden_private_keys(payload, name)
        _check_raw_boundary(payload.get("raw_boundary", {}))
    intake_summary = diagnostic.get("intake_summary", {})
    _require_equal("private.source_partial_exact_match_count", intake_summary.get("source_partial_exact_match_count"), 101)
    _require_equal("private.source_partial_mismatch_count", intake_summary.get("source_partial_mismatch_count"), 0)
    _require_equal("private.source_non_actionable_group_count", intake_summary.get("source_non_actionable_group_count"), 3)
    _require_equal("private.source_non_actionable_target_slot_count", intake_summary.get("source_non_actionable_target_slot_count"), 12)
    _require_equal("private.response_group_count", intake_summary.get("response_group_count"), 3)
    _require_equal("private.response_target_slot_count", intake_summary.get("response_target_slot_count"), 12)
    _require_equal("private.ready_for_intake_group_count", intake_summary.get("ready_for_intake_group_count"), 0)
    _require_equal("private.ready_for_intake_target_slot_count", intake_summary.get("ready_for_intake_target_slot_count"), 0)
    _require_equal("private.pending_response_group_count", intake_summary.get("pending_response_group_count"), 3)
    _require_equal("private.pending_response_target_slot_count", intake_summary.get("pending_response_target_slot_count"), 12)
    _require_equal("private.invalid_response_group_count", intake_summary.get("invalid_response_group_count"), 0)
    _require_equal("private.invalid_response_target_slot_count", intake_summary.get("invalid_response_target_slot_count"), 0)
    _require_equal("private.resolution_decision_code_counts", intake_summary.get("resolution_decision_code_counts"), EXPECTED_RESOLUTION_CODE_COUNTS)
    _require_equal("private.resolution_reason_code_counts", intake_summary.get("resolution_reason_code_counts"), EXPECTED_REASON_CODE_COUNTS)
    _require_equal("private.candidate_status_group_counts", intake_summary.get("candidate_status_group_counts"), EXPECTED_STATUS_GROUP_COUNTS)
    _require_false("private.owner_resolution_supplied", intake_summary.get("owner_or_authorized_delegate_resolution_supplied"))
    _require_true("private.owner_resolution_required", intake_summary.get("owner_or_authorized_delegate_resolution_required"))
    _require_true("private.intake_performed", intake_summary.get("non_actionable_group_response_intake_performed"))
    _require_false("private.codex_default_business_resolution_applied", intake_summary.get("codex_default_business_resolution_applied"))
    _require_false("private.active_ready", intake_summary.get("active_owner_authorized_fill_record_ready"))
    _require_false("private.reapplication_ready", intake_summary.get("source_map_completion_reapplication_ready"))
    _require_false("private.full_raw_compare_ready", intake_summary.get("full_raw_to_processed_value_comparison_ready"))
    _require_false("private.business_consistency", intake_summary.get("business_value_consistency_verified"))
    _require_equal("private.ready queue count", pending_queue.get("ready_for_intake_group_count"), 0)
    _require_equal("private.pending queue count", pending_queue.get("pending_response_group_count"), 3)
    _require_equal("private.invalid queue count", pending_queue.get("invalid_response_group_count"), 0)
    ready = pending_queue.get("ready_groups", [])
    pending = pending_queue.get("pending_groups", [])
    invalid = pending_queue.get("invalid_groups", [])
    if not isinstance(ready, list) or not isinstance(pending, list) or not isinstance(invalid, list):
        raise ValidationError("private queue groups must be lists")
    _require_equal("private.ready_groups length", len(ready), 0)
    _require_equal("private.pending_groups length", len(pending), 3)
    _require_equal("private.invalid_groups length", len(invalid), 0)
    target_total = sum(int(group.get("target_slot_count") or 0) for group in pending if isinstance(group, dict))
    _require_equal("private.pending_groups target total", target_total, 12)
    for path in (PRIVATE_DIAGNOSTIC_PATH, PRIVATE_PENDING_QUEUE_PATH):
        _check_private_file_ignored_and_untracked(path)


def validate(*, require_private_response_intake: bool = False) -> dict[str, Any]:
    summary = _read_json(SUMMARY_PATH)
    manifest = _read_json(MANIFEST_PATH)
    go_no_go = _read_json(GO_NO_GO_PATH)
    metadata_summary = _read_json(QUALITY_DIR / "v014_non_actionable_group_response_intake_summary.json")
    metadata_manifest = _read_json(QUALITY_DIR / "v014_non_actionable_group_response_intake_manifest.json")
    metadata_go_no_go = _read_json(QUALITY_DIR / "v014_non_actionable_group_response_intake_go_no_go_report.json")

    _require_equal("metadata summary copy", metadata_summary, summary)
    _require_equal("metadata manifest copy", metadata_manifest, manifest)
    _require_equal("metadata go/no-go copy", metadata_go_no_go, go_no_go)
    _require_equal("summary.phase_id", summary.get("phase_id"), PHASE_ID)
    _require_equal("summary.task_id", summary.get("task_id"), TASK_ID)
    _require_equal("summary.version", summary.get("version"), VERSION)
    _require_equal("summary.decision", summary.get("decision"), "NO_GO")
    _require_equal("summary.diagnostic_conclusion", summary.get("diagnostic_conclusion"), DIAGNOSTIC_CONCLUSION)
    _require_equal("summary.next_required_input", summary.get("next_required_input"), NEXT_REQUIRED_INPUT)
    _require_equal("summary.source_resolution_packet_decision", summary.get("source_resolution_packet_decision"), "NO_GO")
    _require_equal("summary.source_partial_exact_match_count", summary.get("source_partial_exact_match_count"), 101)
    _require_equal("summary.source_partial_mismatch_count", summary.get("source_partial_mismatch_count"), 0)
    _require_equal("summary.source_non_actionable_group_count", summary.get("source_non_actionable_group_count"), 3)
    _require_equal("summary.source_non_actionable_target_slot_count", summary.get("source_non_actionable_target_slot_count"), 12)
    _require_equal("summary.response_group_count", summary.get("response_group_count"), 3)
    _require_equal("summary.response_target_slot_count", summary.get("response_target_slot_count"), 12)
    _require_equal("summary.ready_for_intake_group_count", summary.get("ready_for_intake_group_count"), 0)
    _require_equal("summary.ready_for_intake_target_slot_count", summary.get("ready_for_intake_target_slot_count"), 0)
    _require_equal("summary.pending_response_group_count", summary.get("pending_response_group_count"), 3)
    _require_equal("summary.pending_response_target_slot_count", summary.get("pending_response_target_slot_count"), 12)
    _require_equal("summary.invalid_response_group_count", summary.get("invalid_response_group_count"), 0)
    _require_equal("summary.invalid_response_target_slot_count", summary.get("invalid_response_target_slot_count"), 0)
    _require_equal("summary.resolution_decision_code_counts", summary.get("resolution_decision_code_counts"), EXPECTED_RESOLUTION_CODE_COUNTS)
    _require_equal("summary.resolution_reason_code_counts", summary.get("resolution_reason_code_counts"), EXPECTED_REASON_CODE_COUNTS)
    _require_equal("summary.candidate_status_group_counts", summary.get("candidate_status_group_counts"), EXPECTED_STATUS_GROUP_COUNTS)
    for key in (
        "private_response_template_gitignored",
        "private_diagnostic_written",
        "private_diagnostic_gitignored",
        "private_pending_queue_written",
        "private_pending_queue_gitignored",
        "owner_or_authorized_delegate_resolution_required",
        "non_actionable_group_response_intake_performed",
        "partial_raw_to_processed_value_comparison_performed",
        "partial_raw_to_processed_value_consistency_verified",
    ):
        _require_true(f"summary.{key}", summary.get(key))
    for key in (
        "owner_or_authorized_delegate_resolution_supplied",
        "codex_default_business_resolution_applied",
        "active_owner_authorized_fill_record_ready",
        "active_owner_authorized_fill_record_written",
        "canonical_source_map_mutated",
        "source_map_completion_reapplication_ready",
        "source_map_completion_reapplication_performed",
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
    _require_equal("go_no_go.source_partial_exact_match_count", go_no_go.get("source_partial_exact_match_count"), 101)
    _require_equal("go_no_go.source_partial_mismatch_count", go_no_go.get("source_partial_mismatch_count"), 0)
    _require_equal("go_no_go.response_group_count", go_no_go.get("response_group_count"), 3)
    _require_equal("go_no_go.response_target_slot_count", go_no_go.get("response_target_slot_count"), 12)
    _require_equal("go_no_go.ready_for_intake_group_count", go_no_go.get("ready_for_intake_group_count"), 0)
    _require_equal("go_no_go.pending_response_group_count", go_no_go.get("pending_response_group_count"), 3)
    _require_equal("go_no_go.invalid_response_group_count", go_no_go.get("invalid_response_group_count"), 0)
    _require_false("go_no_go.owner_resolution_supplied", go_no_go.get("owner_or_authorized_delegate_resolution_supplied"))
    _require_true("go_no_go.owner_resolution_required", go_no_go.get("owner_or_authorized_delegate_resolution_required"))
    _require_false("go_no_go.codex_default_business_resolution_applied", go_no_go.get("codex_default_business_resolution_applied"))
    _require_false("go_no_go.reapplication_ready", go_no_go.get("source_map_completion_reapplication_ready"))
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
    if require_private_response_intake:
        _check_private_response_intake()
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-private-response-intake", action="store_true")
    args = parser.parse_args()
    manifest = validate(require_private_response_intake=args.require_private_response_intake)
    print(
        "PASS: KMFA v0.1.4 non-actionable group response intake validated "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"ready={manifest['summary']['ready_for_intake_group_count']}, "
        f"pending={manifest['summary']['pending_response_group_count']})"
    )


if __name__ == "__main__":
    main()
