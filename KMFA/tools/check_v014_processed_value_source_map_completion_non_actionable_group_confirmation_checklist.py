from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PHASE_ID = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_NON_ACTIONABLE_GROUP_CONFIRMATION_CHECKLIST"
TASK_ID = "KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-NON-ACTIONABLE-GROUP-CONFIRMATION-CHECKLIST-20260706"
VERSION = "0.1.4-non-actionable-group-confirmation-checklist"
DIAGNOSTIC_CONCLUSION = "private_chinese_confirmation_checklist_ready_owner_response_still_required"
NEXT_REQUIRED_INPUT = "owner_or_authorized_delegate_answers_private_chinese_confirmation_checklist_before_application"
EXPECTED_MISSING_KEY_COUNTS = {
    "additional_evidence_ref": 1,
    "owner_or_authorized_delegate": 3,
}
EXPECTED_RESOLUTION_CODE_COUNTS = {
    "KEEP_PENDING_WITH_REASON": 2,
    "REQUEST_ADDITIONAL_SOURCE_EVIDENCE": 1,
}
EXPECTED_STATUS_GROUP_COUNTS = {
    "auto_unmatched_requires_owner_review": 1,
    "requires_non_numeric_owner_mapping": 2,
}

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
QUALITY_DIR = PROJECT_ROOT / "metadata" / "quality"
PRIVATE_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_processed_value_source_map_completion_non_actionable_group_confirmation_checklist"
PRIVATE_CHECKLIST_JSON_PATH = PRIVATE_DIR / "private_non_actionable_group_confirmation_checklist.json"
PRIVATE_CHECKLIST_MD_PATH = PRIVATE_DIR / "private_non_actionable_group_confirmation_checklist.md"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_DIR / "private_non_actionable_group_confirmation_checklist_diagnostic.json"

SUMMARY_PATH = MACHINE_DIR / "processed_value_source_map_completion_non_actionable_group_confirmation_checklist_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_value_source_map_completion_non_actionable_group_confirmation_checklist_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_value_source_map_completion_non_actionable_group_confirmation_checklist_go_no_go_report.json"

PUBLIC_ARTIFACTS = [
    SUMMARY_PATH,
    MANIFEST_PATH,
    GO_NO_GO_PATH,
    HUMAN_DIR / "processed_value_source_map_completion_non_actionable_group_confirmation_checklist_report.md",
    HUMAN_DIR / "go_no_go_record.md",
    HUMAN_DIR / "test_results.md",
    HUMAN_DIR / "risk_register.md",
    HUMAN_DIR / "rollback_plan.md",
    QUALITY_DIR / "v014_non_actionable_group_confirmation_checklist_summary.json",
    QUALITY_DIR / "v014_non_actionable_group_confirmation_checklist_manifest.json",
    QUALITY_DIR / "v014_non_actionable_group_confirmation_checklist_go_no_go_report.json",
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
        "private_confirmation_checklist_committed",
        "private_confirmation_markdown_committed",
        "private_diagnostic_committed",
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


def _check_private_confirmation_checklist() -> None:
    checklist = _read_json(PRIVATE_CHECKLIST_JSON_PATH)
    diagnostic = _read_json(PRIVATE_DIAGNOSTIC_PATH)
    markdown = PRIVATE_CHECKLIST_MD_PATH.read_text(encoding="utf-8")
    for name, payload in (("checklist", checklist), ("diagnostic", diagnostic)):
        _require_equal(f"{name}.phase_id", payload.get("phase_id"), PHASE_ID)
        _require_equal(f"{name}.task_id", payload.get("task_id"), TASK_ID)
        _require_equal(f"{name}.version", payload.get("version"), VERSION)
        _check_forbidden_private_keys(payload, name)
        _check_raw_boundary(payload.get("raw_boundary", {}))
    checklist_summary = checklist.get("checklist_summary", {})
    _require_equal("private.source_response_group_count", checklist_summary.get("source_response_group_count"), 3)
    _require_equal("private.source_response_target_slot_count", checklist_summary.get("source_response_target_slot_count"), 12)
    _require_equal("private.source_ready_for_intake_group_count", checklist_summary.get("source_ready_for_intake_group_count"), 0)
    _require_equal("private.source_pending_response_group_count", checklist_summary.get("source_pending_response_group_count"), 3)
    _require_equal("private.source_invalid_response_group_count", checklist_summary.get("source_invalid_response_group_count"), 0)
    _require_equal("private.checklist_item_count", checklist_summary.get("checklist_item_count"), 3)
    _require_equal("private.checklist_target_slot_count", checklist_summary.get("checklist_target_slot_count"), 12)
    _require_equal("private.missing_required_key_counts", checklist_summary.get("missing_required_key_counts"), EXPECTED_MISSING_KEY_COUNTS)
    _require_equal("private.resolution_decision_code_counts", checklist_summary.get("resolution_decision_code_counts"), EXPECTED_RESOLUTION_CODE_COUNTS)
    _require_equal("private.candidate_status_group_counts", checklist_summary.get("candidate_status_group_counts"), EXPECTED_STATUS_GROUP_COUNTS)
    _require_true("private.private_chinese_checklist_ready", checklist_summary.get("private_chinese_checklist_ready"))
    _require_true("private.owner_response_required", checklist_summary.get("owner_or_authorized_delegate_response_required"))
    _require_false("private.codex_default_business_resolution_applied", checklist_summary.get("codex_default_business_resolution_applied"))
    _require_false("private.active_ready", checklist_summary.get("active_owner_authorized_fill_record_ready"))
    _require_false("private.reapplication_ready", checklist_summary.get("source_map_completion_reapplication_ready"))
    _require_false("private.business_consistency", checklist_summary.get("business_value_consistency_verified"))
    items = checklist.get("checklist_items", [])
    if not isinstance(items, list):
        raise ValidationError("private checklist_items must be a list")
    _require_equal("private.checklist_items length", len(items), 3)
    target_total = sum(int(item.get("target_slot_count") or 0) for item in items if isinstance(item, dict))
    _require_equal("private.checklist target total", target_total, 12)
    if "中文问题" not in markdown or "确认项数量: 3" not in markdown:
        raise ValidationError("private markdown checklist does not contain expected Chinese checklist markers")
    for path in (PRIVATE_CHECKLIST_JSON_PATH, PRIVATE_CHECKLIST_MD_PATH, PRIVATE_DIAGNOSTIC_PATH):
        _check_private_file_ignored_and_untracked(path)


def validate(*, require_private_confirmation_checklist: bool = False) -> dict[str, Any]:
    summary = _read_json(SUMMARY_PATH)
    manifest = _read_json(MANIFEST_PATH)
    go_no_go = _read_json(GO_NO_GO_PATH)
    metadata_summary = _read_json(QUALITY_DIR / "v014_non_actionable_group_confirmation_checklist_summary.json")
    metadata_manifest = _read_json(QUALITY_DIR / "v014_non_actionable_group_confirmation_checklist_manifest.json")
    metadata_go_no_go = _read_json(QUALITY_DIR / "v014_non_actionable_group_confirmation_checklist_go_no_go_report.json")

    _require_equal("metadata summary copy", metadata_summary, summary)
    _require_equal("metadata manifest copy", metadata_manifest, manifest)
    _require_equal("metadata go/no-go copy", metadata_go_no_go, go_no_go)
    _require_equal("summary.phase_id", summary.get("phase_id"), PHASE_ID)
    _require_equal("summary.task_id", summary.get("task_id"), TASK_ID)
    _require_equal("summary.version", summary.get("version"), VERSION)
    _require_equal("summary.decision", summary.get("decision"), "NO_GO")
    _require_equal("summary.diagnostic_conclusion", summary.get("diagnostic_conclusion"), DIAGNOSTIC_CONCLUSION)
    _require_equal("summary.next_required_input", summary.get("next_required_input"), NEXT_REQUIRED_INPUT)
    _require_equal("summary.source_response_intake_decision", summary.get("source_response_intake_decision"), "NO_GO")
    _require_equal("summary.source_response_group_count", summary.get("source_response_group_count"), 3)
    _require_equal("summary.source_response_target_slot_count", summary.get("source_response_target_slot_count"), 12)
    _require_equal("summary.source_ready_for_intake_group_count", summary.get("source_ready_for_intake_group_count"), 0)
    _require_equal("summary.source_pending_response_group_count", summary.get("source_pending_response_group_count"), 3)
    _require_equal("summary.source_invalid_response_group_count", summary.get("source_invalid_response_group_count"), 0)
    _require_equal("summary.checklist_item_count", summary.get("checklist_item_count"), 3)
    _require_equal("summary.checklist_target_slot_count", summary.get("checklist_target_slot_count"), 12)
    _require_equal("summary.missing_required_key_counts", summary.get("missing_required_key_counts"), EXPECTED_MISSING_KEY_COUNTS)
    _require_equal("summary.resolution_decision_code_counts", summary.get("resolution_decision_code_counts"), EXPECTED_RESOLUTION_CODE_COUNTS)
    _require_equal("summary.candidate_status_group_counts", summary.get("candidate_status_group_counts"), EXPECTED_STATUS_GROUP_COUNTS)
    for key in (
        "private_chinese_checklist_ready",
        "owner_or_authorized_delegate_response_required",
        "private_confirmation_checklist_written",
        "private_confirmation_checklist_gitignored",
        "private_confirmation_markdown_written",
        "private_confirmation_markdown_gitignored",
        "private_diagnostic_written",
        "private_diagnostic_gitignored",
    ):
        _require_true(f"summary.{key}", summary.get(key))
    for key in (
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
    _require_equal("go_no_go.checklist_item_count", go_no_go.get("checklist_item_count"), 3)
    _require_equal("go_no_go.checklist_target_slot_count", go_no_go.get("checklist_target_slot_count"), 12)
    _require_true("go_no_go.owner_response_required", go_no_go.get("owner_or_authorized_delegate_response_required"))
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
    if require_private_confirmation_checklist:
        _check_private_confirmation_checklist()
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-private-confirmation-checklist", action="store_true")
    args = parser.parse_args()
    manifest = validate(require_private_confirmation_checklist=args.require_private_confirmation_checklist)
    print(
        "PASS: KMFA v0.1.4 non-actionable group confirmation checklist validated "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"items={manifest['summary']['checklist_item_count']}, "
        f"target_slots={manifest['summary']['checklist_target_slot_count']})"
    )


if __name__ == "__main__":
    main()
