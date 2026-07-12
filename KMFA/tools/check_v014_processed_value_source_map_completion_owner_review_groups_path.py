from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PHASE_ID = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_REVIEW_GROUPS_PATH"
TASK_ID = "KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-OWNER-REVIEW-GROUPS-PATH-20260706"
VERSION = "0.1.4-processed-value-source-map-completion-owner-review-groups-path"
PRIMARY_CONFIRMATION_CODE = "KMFA_ORR_OPTION_REQUEST_MORE_DIAGNOSTICS_ALL"
FOLLOW_UP_CONFIRMATION_CODE = "KMFA_ORR_OPTION_REVIEW_GROUPS"
DIAGNOSTIC_CONCLUSION = "owner_review_groups_path_prepared_owner_group_decisions_required"
NEXT_REQUIRED_INPUT = "owner_or_authorized_delegate_applies_group_level_decisions_to_private_response_template"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
QUALITY_DIR = PROJECT_ROOT / "metadata" / "quality"
PRIVATE_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_processed_value_source_map_completion_owner_review_groups_path"
PRIVATE_GROUPS_PACKET_PATH = PRIVATE_DIR / "private_owner_review_groups_path_packet.json"
PRIVATE_RESPONSE_DRAFT_PATH = PRIVATE_DIR / "private_owner_review_groups_path_response_draft.json"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_DIR / "private_owner_review_groups_path_diagnostic.json"

SUMMARY_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_review_groups_path_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_review_groups_path_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_review_groups_path_go_no_go_report.json"

PUBLIC_ARTIFACTS = [
    SUMMARY_PATH,
    MANIFEST_PATH,
    GO_NO_GO_PATH,
    HUMAN_DIR / "processed_value_source_map_completion_owner_review_groups_path_report.md",
    HUMAN_DIR / "go_no_go_record.md",
    HUMAN_DIR / "test_results.md",
    HUMAN_DIR / "risk_register.md",
    HUMAN_DIR / "rollback_plan.md",
    QUALITY_DIR / "v014_processed_value_source_map_completion_owner_review_groups_path_summary.json",
    QUALITY_DIR / "v014_processed_value_source_map_completion_owner_review_groups_path_manifest.json",
    QUALITY_DIR / "v014_processed_value_source_map_completion_owner_review_groups_path_go_no_go_report.json",
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
        "private_groups_packet_committed",
        "private_response_draft_committed",
        "private_diagnostic_committed",
        "private_confirmation_record_committed",
        "raw_file_committed",
        "raw_filename_committed",
        "raw_archive_member_name_committed",
        "field_header_plaintext_committed",
        "row_value_committed",
        "business_value_committed",
        "credential_or_secret_committed",
    ):
        _require_false(f"public_safety.{key}", safety.get(key))


def _check_private_groups() -> None:
    packet = _read_json(PRIVATE_GROUPS_PACKET_PATH)
    draft = _read_json(PRIVATE_RESPONSE_DRAFT_PATH)
    diagnostic = _read_json(PRIVATE_DIAGNOSTIC_PATH)
    for name, payload in (("packet", packet), ("draft", draft), ("diagnostic", diagnostic)):
        _require_equal(f"{name}.phase_id", payload.get("phase_id"), PHASE_ID)
        _require_equal(f"{name}.task_id", payload.get("task_id"), TASK_ID)
    _require_equal("packet.primary", packet.get("primary_confirmation_code"), PRIMARY_CONFIRMATION_CODE)
    _require_equal("packet.follow_up", packet.get("follow_up_confirmation_code"), FOLLOW_UP_CONFIRMATION_CODE)
    _require_equal("packet.review_group_count", packet.get("review_group_count"), 22)
    _require_equal("packet.response_row_count", packet.get("response_row_count"), 113)
    _require_equal("packet.candidate_catalog_record_count", packet.get("candidate_catalog_record_count"), 366)
    _require_true("packet.review_groups_path_prepared", packet.get("review_groups_path_prepared"))
    _require_false("packet.owner_group_decision_applied", packet.get("owner_group_decision_applied"))
    _require_false("packet.active_ready", packet.get("active_owner_authorized_fill_record_ready"))
    _require_equal("draft.response_row_count", draft.get("response_row_count"), 113)
    _require_false("draft.active", draft.get("draft_is_active_authorization_record"))
    _require_false("draft.owner_group_decision_applied", draft.get("owner_group_decision_applied"))
    _require_equal("diagnostic.review_group_count", diagnostic.get("review_group_count"), 22)
    _require_equal("diagnostic.response_row_count", diagnostic.get("response_row_count"), 113)
    _check_raw_boundary(diagnostic.get("raw_boundary", {}))
    for path in (PRIVATE_GROUPS_PACKET_PATH, PRIVATE_RESPONSE_DRAFT_PATH, PRIVATE_DIAGNOSTIC_PATH):
        result = subprocess.run(["git", "check-ignore", "-q", path.as_posix()], cwd=PROJECT_ROOT.parent, check=False)
        _require_equal(f"{path}.gitignored", result.returncode, 0)
        _require_equal(f"{path}.tracked", _git_output(["ls-files", path.as_posix()]), "")


def validate(*, require_private_groups: bool = False) -> dict[str, Any]:
    summary = _read_json(SUMMARY_PATH)
    manifest = _read_json(MANIFEST_PATH)
    go_no_go = _read_json(GO_NO_GO_PATH)
    metadata_summary = _read_json(QUALITY_DIR / "v014_processed_value_source_map_completion_owner_review_groups_path_summary.json")
    metadata_manifest = _read_json(QUALITY_DIR / "v014_processed_value_source_map_completion_owner_review_groups_path_manifest.json")
    metadata_go_no_go = _read_json(
        QUALITY_DIR / "v014_processed_value_source_map_completion_owner_review_groups_path_go_no_go_report.json"
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
    _require_equal("summary.source_supplemental_diagnostic_request_row_count", summary.get("source_supplemental_diagnostic_request_row_count"), 113)
    _require_true("summary.source_review_group_follow_up_ready", summary.get("source_review_group_follow_up_ready"))
    _require_equal("summary.review_group_count", summary.get("review_group_count"), 22)
    _require_equal("summary.review_group_response_row_count", summary.get("review_group_response_row_count"), 113)
    _require_equal("summary.candidate_catalog_record_count", summary.get("candidate_catalog_record_count"), 366)
    _require_equal("summary.ambiguous_review_group_count", summary.get("ambiguous_review_group_count"), 19)
    _require_equal("summary.non_numeric_review_group_count", summary.get("non_numeric_review_group_count"), 2)
    _require_equal("summary.unmatched_review_group_count", summary.get("unmatched_review_group_count"), 1)
    _require_equal("summary.ambiguous_target_slot_count", summary.get("ambiguous_target_slot_count"), 101)
    _require_equal("summary.non_numeric_target_slot_count", summary.get("non_numeric_target_slot_count"), 8)
    _require_equal("summary.unmatched_target_slot_count", summary.get("unmatched_target_slot_count"), 4)
    for key in (
        "private_groups_packet_written",
        "private_groups_packet_gitignored",
        "private_response_draft_written",
        "private_response_draft_gitignored",
        "private_diagnostic_written",
        "private_diagnostic_gitignored",
        "review_groups_path_prepared",
    ):
        _require_true(f"summary.{key}", summary.get(key))
    for key in (
        "owner_group_decision_applied",
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
    _require_equal("go_no_go.review_group_count", go_no_go.get("review_group_count"), 22)
    _require_equal("go_no_go.review_group_response_row_count", go_no_go.get("review_group_response_row_count"), 113)
    _require_true("go_no_go.review_groups_path_prepared", go_no_go.get("review_groups_path_prepared"))
    _require_false("go_no_go.owner_group_decision_applied", go_no_go.get("owner_group_decision_applied"))
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
    if require_private_groups:
        _check_private_groups()
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-private-groups", action="store_true")
    args = parser.parse_args()
    manifest = validate(require_private_groups=args.require_private_groups)
    print(
        "PASS: KMFA v0.1.4 owner review groups path validated "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"groups={manifest['summary']['review_group_count']}, "
        f"rows={manifest['summary']['review_group_response_row_count']})"
    )


if __name__ == "__main__":
    main()
