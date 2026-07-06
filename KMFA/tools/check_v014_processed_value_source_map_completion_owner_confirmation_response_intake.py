from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PHASE_ID = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_CONFIRMATION_RESPONSE_INTAKE"
TASK_ID = "KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-OWNER-CONFIRMATION-RESPONSE-INTAKE-20260706"
VERSION = "0.1.4-owner-confirmation-response-intake"
DIAGNOSTIC_CONCLUSION = "owner_confirmation_response_intake_has_no_complete_owner_responses"
NEXT_REQUIRED_INPUT = "owner_or_authorized_delegate_completes_private_confirmation_response_draft"
EXPECTED_MISSING_FIELD_COUNTS = {
    "owner_or_authorized_delegate": 3,
    "ready_for_intake": 3,
    "resolution_reason_code": 3,
    "选择": 3,
}

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
QUALITY_DIR = PROJECT_ROOT / "metadata" / "quality"
PRIVATE_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_processed_value_source_map_completion_owner_confirmation_response_intake"
PRIVATE_INTAKE_DIAGNOSTIC_PATH = PRIVATE_DIR / "private_owner_confirmation_response_intake_diagnostic.json"
PRIVATE_VALID_RESPONSE_QUEUE_PATH = PRIVATE_DIR / "private_owner_confirmation_valid_response_queue.json"
PRIVATE_PENDING_RESPONSE_QUEUE_PATH = PRIVATE_DIR / "private_owner_confirmation_pending_response_queue.json"

SUMMARY_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_confirmation_response_intake_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_confirmation_response_intake_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_confirmation_response_intake_go_no_go_report.json"

PUBLIC_ARTIFACTS = [
    SUMMARY_PATH,
    MANIFEST_PATH,
    GO_NO_GO_PATH,
    HUMAN_DIR / "processed_value_source_map_completion_owner_confirmation_response_intake_report.md",
    HUMAN_DIR / "go_no_go_record.md",
    HUMAN_DIR / "test_results.md",
    HUMAN_DIR / "risk_register.md",
    HUMAN_DIR / "rollback_plan.md",
    QUALITY_DIR / "v014_owner_confirmation_response_intake_summary.json",
    QUALITY_DIR / "v014_owner_confirmation_response_intake_manifest.json",
    QUALITY_DIR / "v014_owner_confirmation_response_intake_go_no_go_report.json",
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
        "private_response_draft_committed",
        "private_intake_diagnostic_committed",
        "private_valid_response_queue_committed",
        "private_pending_response_queue_committed",
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


def _check_private_owner_confirmation_intake() -> None:
    diagnostic = _read_json(PRIVATE_INTAKE_DIAGNOSTIC_PATH)
    valid_queue = _read_json(PRIVATE_VALID_RESPONSE_QUEUE_PATH)
    pending_queue = _read_json(PRIVATE_PENDING_RESPONSE_QUEUE_PATH)
    for name, payload in (("diagnostic", diagnostic), ("valid_queue", valid_queue), ("pending_queue", pending_queue)):
        _require_equal(f"{name}.phase_id", payload.get("phase_id"), PHASE_ID)
        _require_equal(f"{name}.task_id", payload.get("task_id"), TASK_ID)
        _require_equal(f"{name}.version", payload.get("version"), VERSION)
        _check_forbidden_private_keys(payload, name)
        _check_raw_boundary(payload.get("raw_boundary", {}))
    intake_summary = diagnostic.get("intake_summary", {})
    _require_equal("private.source_response_packet_item_count", intake_summary.get("source_response_packet_item_count"), 3)
    _require_equal("private.source_response_packet_target_slot_count", intake_summary.get("source_response_packet_target_slot_count"), 12)
    _require_equal("private.response_draft_item_count", intake_summary.get("response_draft_item_count"), 3)
    _require_equal("private.valid_response_count", intake_summary.get("valid_owner_confirmation_response_count"), 0)
    _require_equal("private.pending_response_count", intake_summary.get("pending_owner_confirmation_response_count"), 3)
    _require_equal("private.invalid_response_count", intake_summary.get("invalid_owner_confirmation_response_count"), 0)
    _require_equal("private.filled_field_counts", intake_summary.get("filled_field_counts"), {})
    _require_equal("private.missing_required_field_counts", intake_summary.get("missing_required_field_counts"), EXPECTED_MISSING_FIELD_COUNTS)
    _require_true("private.intake_performed", intake_summary.get("owner_confirmation_response_intake_performed"))
    _require_false("private.response_supplied", intake_summary.get("owner_confirmation_response_supplied"))
    _require_false("private.active_ready", intake_summary.get("active_owner_authorized_fill_record_ready"))
    _require_false("private.active_written", intake_summary.get("active_owner_authorized_fill_record_written"))
    _require_false("private.reapplication_ready", intake_summary.get("source_map_completion_reapplication_ready"))
    _require_false("private.reapplication_performed", intake_summary.get("source_map_completion_reapplication_performed"))
    _require_false("private.raw_compare", intake_summary.get("raw_to_processed_value_comparison_performed"))
    _require_false("private.business_consistency", intake_summary.get("business_value_consistency_verified"))
    valid_responses = valid_queue.get("valid_responses", [])
    pending_responses = pending_queue.get("pending_responses", [])
    invalid_responses = pending_queue.get("invalid_responses", [])
    if not isinstance(valid_responses, list) or not isinstance(pending_responses, list) or not isinstance(invalid_responses, list):
        raise ValidationError("private intake response lists must be lists")
    _require_equal("private.valid_responses length", len(valid_responses), 0)
    _require_equal("private.pending_responses length", len(pending_responses), 3)
    _require_equal("private.invalid_responses length", len(invalid_responses), 0)
    for path in (PRIVATE_INTAKE_DIAGNOSTIC_PATH, PRIVATE_VALID_RESPONSE_QUEUE_PATH, PRIVATE_PENDING_RESPONSE_QUEUE_PATH):
        _check_private_file_ignored_and_untracked(path)


def validate(*, require_private_owner_confirmation_intake: bool = False) -> dict[str, Any]:
    summary = _read_json(SUMMARY_PATH)
    manifest = _read_json(MANIFEST_PATH)
    go_no_go = _read_json(GO_NO_GO_PATH)
    metadata_summary = _read_json(QUALITY_DIR / "v014_owner_confirmation_response_intake_summary.json")
    metadata_manifest = _read_json(QUALITY_DIR / "v014_owner_confirmation_response_intake_manifest.json")
    metadata_go_no_go = _read_json(QUALITY_DIR / "v014_owner_confirmation_response_intake_go_no_go_report.json")

    _require_equal("metadata summary copy", metadata_summary, summary)
    _require_equal("metadata manifest copy", metadata_manifest, manifest)
    _require_equal("metadata go/no-go copy", metadata_go_no_go, go_no_go)
    _require_equal("summary.phase_id", summary.get("phase_id"), PHASE_ID)
    _require_equal("summary.task_id", summary.get("task_id"), TASK_ID)
    _require_equal("summary.version", summary.get("version"), VERSION)
    _require_equal("summary.decision", summary.get("decision"), "NO_GO")
    _require_equal("summary.diagnostic_conclusion", summary.get("diagnostic_conclusion"), DIAGNOSTIC_CONCLUSION)
    _require_equal("summary.next_required_input", summary.get("next_required_input"), NEXT_REQUIRED_INPUT)
    _require_equal("summary.source_owner_confirmation_response_packet_decision", summary.get("source_owner_confirmation_response_packet_decision"), "NO_GO")
    _require_equal("summary.source_response_packet_item_count", summary.get("source_response_packet_item_count"), 3)
    _require_equal("summary.source_response_packet_target_slot_count", summary.get("source_response_packet_target_slot_count"), 12)
    _require_equal("summary.response_draft_item_count", summary.get("response_draft_item_count"), 3)
    _require_equal("summary.valid_response_count", summary.get("valid_owner_confirmation_response_count"), 0)
    _require_equal("summary.pending_response_count", summary.get("pending_owner_confirmation_response_count"), 3)
    _require_equal("summary.invalid_response_count", summary.get("invalid_owner_confirmation_response_count"), 0)
    _require_equal("summary.filled_field_counts", summary.get("filled_field_counts"), {})
    _require_equal("summary.missing_required_field_counts", summary.get("missing_required_field_counts"), EXPECTED_MISSING_FIELD_COUNTS)
    for key in (
        "owner_confirmation_response_intake_performed",
        "private_response_draft_gitignored",
        "private_intake_diagnostic_written",
        "private_intake_diagnostic_gitignored",
        "private_valid_response_queue_written",
        "private_valid_response_queue_gitignored",
        "private_pending_response_queue_written",
        "private_pending_response_queue_gitignored",
    ):
        _require_true(f"summary.{key}", summary.get(key))
    for key in (
        "owner_confirmation_response_supplied",
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
    _require_equal("go_no_go.valid_response_count", go_no_go.get("valid_owner_confirmation_response_count"), 0)
    _require_equal("go_no_go.pending_response_count", go_no_go.get("pending_owner_confirmation_response_count"), 3)
    _require_false("go_no_go.response_supplied", go_no_go.get("owner_confirmation_response_supplied"))
    _require_false("go_no_go.active_ready", go_no_go.get("active_owner_authorized_fill_record_ready"))
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
    if require_private_owner_confirmation_intake:
        _check_private_owner_confirmation_intake()
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-private-owner-confirmation-intake", action="store_true")
    args = parser.parse_args()
    manifest = validate(require_private_owner_confirmation_intake=args.require_private_owner_confirmation_intake)
    print(
        "PASS: KMFA v0.1.4 owner confirmation response intake validated "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"valid={manifest['summary']['valid_owner_confirmation_response_count']}, "
        f"pending={manifest['summary']['pending_owner_confirmation_response_count']})"
    )


if __name__ == "__main__":
    main()
