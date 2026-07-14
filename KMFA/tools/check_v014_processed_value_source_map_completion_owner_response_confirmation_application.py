from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PHASE_ID = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_RESPONSE_CONFIRMATION_APPLICATION"
TASK_ID = "KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-OWNER-RESPONSE-CONFIRMATION-APPLICATION-20260706"
VERSION = "0.1.4-processed-value-source-map-completion-owner-response-confirmation-application"
PRIMARY_CONFIRMATION_CODE = "KMFA_ORR_OPTION_REQUEST_MORE_DIAGNOSTICS_ALL"
FOLLOW_UP_CONFIRMATION_CODE = "KMFA_ORR_OPTION_REVIEW_GROUPS"
DIAGNOSTIC_CONCLUSION = "owner_confirmed_request_more_diagnostics_then_review_groups"
NEXT_REQUIRED_INPUT = "run_owner_review_groups_phase_after_private_supplemental_diagnostics"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
QUALITY_DIR = PROJECT_ROOT / "metadata" / "quality"
PRIVATE_DECISION_OPTIONS_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_processed_value_source_map_completion_owner_response_decision_options"
PRIVATE_CONFIRMATION_RECORD_PATH = PRIVATE_DECISION_OPTIONS_DIR / "private_owner_response_confirmation_record.json"
PRIVATE_OUTPUT_DIR = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_owner_response_confirmation_application"
)
PRIVATE_SUPPLEMENTAL_DIAGNOSTIC_REQUEST_PATH = PRIVATE_OUTPUT_DIR / "private_supplemental_diagnostic_request_all_rows.json"
PRIVATE_REVIEW_GROUPS_NEXT_STEP_PATH = PRIVATE_OUTPUT_DIR / "private_review_groups_next_step_queue.json"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_owner_response_confirmation_application_diagnostic.json"

SUMMARY_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_response_confirmation_application_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_response_confirmation_application_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_response_confirmation_application_go_no_go_report.json"

PUBLIC_ARTIFACTS = [
    SUMMARY_PATH,
    MANIFEST_PATH,
    GO_NO_GO_PATH,
    HUMAN_DIR / "processed_value_source_map_completion_owner_response_confirmation_application_report.md",
    HUMAN_DIR / "go_no_go_record.md",
    HUMAN_DIR / "test_results.md",
    HUMAN_DIR / "risk_register.md",
    HUMAN_DIR / "rollback_plan.md",
    QUALITY_DIR / "v014_processed_value_source_map_completion_owner_response_confirmation_application_summary.json",
    QUALITY_DIR / "v014_processed_value_source_map_completion_owner_response_confirmation_application_manifest.json",
    QUALITY_DIR / "v014_processed_value_source_map_completion_owner_response_confirmation_application_go_no_go_report.json",
]

FORBIDDEN_PUBLIC_PATTERNS = [
    re.compile(r"/Users/linzezhang/Downloads"),
    re.compile(r"KMFA_MetaData"),
    re.compile(r"\.(xlsx|xlsm|xls|zip|pdf)\b", re.IGNORECASE),
    re.compile(
        r'"(raw_file_name|archive_member_name|sheet_name|cell_address|raw_value|normalized_decimal|context_text)"',
        re.IGNORECASE,
    ),
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
        "private_confirmation_record_committed",
        "private_supplemental_diagnostic_request_committed",
        "private_review_group_queue_committed",
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


def _check_private_confirmation() -> None:
    confirmation = _read_json(PRIVATE_CONFIRMATION_RECORD_PATH)
    supplemental = _read_json(PRIVATE_SUPPLEMENTAL_DIAGNOSTIC_REQUEST_PATH)
    next_step = _read_json(PRIVATE_REVIEW_GROUPS_NEXT_STEP_PATH)
    diagnostic = _read_json(PRIVATE_DIAGNOSTIC_PATH)
    for name, payload in (
        ("confirmation", confirmation),
        ("supplemental", supplemental),
        ("next_step", next_step),
        ("diagnostic", diagnostic),
    ):
        _require_equal(f"{name}.phase_id", payload.get("phase_id"), PHASE_ID)
        _require_equal(f"{name}.task_id", payload.get("task_id"), TASK_ID)
    _require_equal("confirmation.primary", confirmation.get("primary_confirmation_code"), PRIMARY_CONFIRMATION_CODE)
    _require_equal("confirmation.follow_up", confirmation.get("follow_up_confirmation_code"), FOLLOW_UP_CONFIRMATION_CODE)
    _require_equal("confirmation.source_response_row_count", confirmation.get("source_response_row_count"), 113)
    _require_equal("confirmation.diagnostic_request_row_count", confirmation.get("diagnostic_request_row_count"), 113)
    _require_true("confirmation.review_group_follow_up_ready", confirmation.get("review_group_follow_up_ready"))
    _require_false("confirmation.active_ready", confirmation.get("active_owner_authorized_fill_record_ready"))
    _require_equal("supplemental.row_count", supplemental.get("diagnostic_request_row_count"), 113)
    _require_true("next_step.ready", next_step.get("review_group_follow_up_ready"))
    _require_equal("next_step.row_count", next_step.get("queued_row_count"), 113)
    _require_equal("diagnostic.primary", diagnostic.get("primary_confirmation_code"), PRIMARY_CONFIRMATION_CODE)
    _check_raw_boundary(diagnostic.get("raw_boundary", {}))
    for path in (
        PRIVATE_CONFIRMATION_RECORD_PATH,
        PRIVATE_SUPPLEMENTAL_DIAGNOSTIC_REQUEST_PATH,
        PRIVATE_REVIEW_GROUPS_NEXT_STEP_PATH,
        PRIVATE_DIAGNOSTIC_PATH,
    ):
        result = subprocess.run(["git", "check-ignore", "-q", path.as_posix()], cwd=PROJECT_ROOT.parent, check=False)
        _require_equal(f"{path}.gitignored", result.returncode, 0)
        _require_equal(f"{path}.tracked", _git_output(["ls-files", path.as_posix()]), "")


def validate(*, require_private_confirmation: bool = False) -> dict[str, Any]:
    summary = _read_json(SUMMARY_PATH)
    manifest = _read_json(MANIFEST_PATH)
    go_no_go = _read_json(GO_NO_GO_PATH)
    metadata_summary = _read_json(
        QUALITY_DIR / "v014_processed_value_source_map_completion_owner_response_confirmation_application_summary.json"
    )
    metadata_manifest = _read_json(
        QUALITY_DIR / "v014_processed_value_source_map_completion_owner_response_confirmation_application_manifest.json"
    )
    metadata_go_no_go = _read_json(
        QUALITY_DIR / "v014_processed_value_source_map_completion_owner_response_confirmation_application_go_no_go_report.json"
    )

    _require_equal("metadata summary copy", metadata_summary, summary)
    _require_equal("metadata manifest copy", metadata_manifest, manifest)
    _require_equal("metadata go/no-go copy", metadata_go_no_go, go_no_go)
    _require_equal("summary.phase_id", summary.get("phase_id"), PHASE_ID)
    _require_equal("summary.task_id", summary.get("task_id"), TASK_ID)
    _require_equal("summary.version", summary.get("version"), VERSION)
    _require_equal("summary.decision", summary.get("decision"), "NO_GO")
    _require_equal("summary.diagnostic_conclusion", summary.get("diagnostic_conclusion"), DIAGNOSTIC_CONCLUSION)
    _require_equal("summary.primary_confirmation_code", summary.get("primary_confirmation_code"), PRIMARY_CONFIRMATION_CODE)
    _require_equal("summary.follow_up_confirmation_code", summary.get("follow_up_confirmation_code"), FOLLOW_UP_CONFIRMATION_CODE)
    _require_equal("summary.source_response_row_count", summary.get("source_response_row_count"), 113)
    _require_equal("summary.source_pending_owner_decision_count", summary.get("source_pending_owner_decision_count"), 113)
    _require_equal("summary.decision_option_count", summary.get("decision_option_count"), 3)
    _require_true("summary.confirmation_record_written", summary.get("confirmation_record_written"))
    _require_true("summary.confirmation_record_gitignored", summary.get("confirmation_record_gitignored"))
    _require_true("summary.supplemental_diagnostic_request_written", summary.get("supplemental_diagnostic_request_written"))
    _require_true("summary.supplemental_diagnostic_request_gitignored", summary.get("supplemental_diagnostic_request_gitignored"))
    _require_equal("summary.supplemental_diagnostic_request_row_count", summary.get("supplemental_diagnostic_request_row_count"), 113)
    _require_true("summary.review_group_follow_up_ready", summary.get("review_group_follow_up_ready"))
    _require_equal("summary.review_group_follow_up_row_count", summary.get("review_group_follow_up_row_count"), 113)
    for key in (
        "active_owner_authorized_fill_record_ready",
        "active_owner_authorized_fill_record_written",
        "owner_response_template_modified",
        "completion_template_overwritten",
        "authorized_completion_record_supplied",
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
    _require_equal("summary.source_map_records_applied_count", summary.get("source_map_records_applied_count"), 0)
    _require_equal("summary.next_required_input", summary.get("next_required_input"), NEXT_REQUIRED_INPUT)
    _check_raw_boundary(summary.get("raw_boundary", {}))
    _check_public_safety(summary.get("public_safety", {}))

    _require_equal("go_no_go.decision", go_no_go.get("decision"), "NO_GO")
    _require_equal("go_no_go.primary_confirmation_code", go_no_go.get("primary_confirmation_code"), PRIMARY_CONFIRMATION_CODE)
    _require_equal("go_no_go.follow_up_confirmation_code", go_no_go.get("follow_up_confirmation_code"), FOLLOW_UP_CONFIRMATION_CODE)
    _require_equal("go_no_go.supplemental_diagnostic_request_row_count", go_no_go.get("supplemental_diagnostic_request_row_count"), 113)
    _require_true("go_no_go.review_group_follow_up_ready", go_no_go.get("review_group_follow_up_ready"))
    _require_false("go_no_go.active_owner_authorized_fill_record_ready", go_no_go.get("active_owner_authorized_fill_record_ready"))
    _require_false("go_no_go.source_map_completion_reapplication_ready", go_no_go.get("source_map_completion_reapplication_ready"))
    _require_false("go_no_go.raw_to_processed_value_comparison_performed", go_no_go.get("raw_to_processed_value_comparison_performed"))
    _require_false("go_no_go.business_value_consistency_verified", go_no_go.get("business_value_consistency_verified"))
    _require_false("go_no_go.github_upload_performed", go_no_go.get("github_upload_performed"))
    _require_equal("go_no_go.blocked_until", go_no_go.get("blocked_until"), NEXT_REQUIRED_INPUT)
    _require_equal("manifest.summary", manifest.get("summary"), summary)
    _require_equal("manifest.go_no_go", manifest.get("go_no_go"), go_no_go)

    _check_public_artifacts()
    _check_no_raw_private_files_tracked()
    if require_private_confirmation:
        _check_private_confirmation()
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-private-confirmation", action="store_true")
    args = parser.parse_args()
    manifest = validate(require_private_confirmation=args.require_private_confirmation)
    print(
        "PASS: KMFA v0.1.4 owner response confirmation application validated "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"primary={manifest['summary']['primary_confirmation_code']}, "
        f"follow_up={manifest['summary']['follow_up_confirmation_code']}, "
        f"rows={manifest['summary']['supplemental_diagnostic_request_row_count']})"
    )


if __name__ == "__main__":
    main()
