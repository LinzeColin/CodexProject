from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PHASE_ID = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_GROUP_DECISION_INPUT_KIT"
TASK_ID = "KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-OWNER-GROUP-DECISION-INPUT-KIT-20260706"
VERSION = "0.1.4-processed-value-source-map-completion-owner-group-decision-input-kit"
DIAGNOSTIC_CONCLUSION = "owner_group_decision_input_kit_ready_decisions_not_supplied"
NEXT_REQUIRED_INPUT = "owner_or_authorized_delegate_fills_private_group_decision_response_template"
PENDING_DECISION_CODE = "PENDING_OWNER_OR_AUTHORIZED_DELEGATE_GROUP_DECISION"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
QUALITY_DIR = PROJECT_ROOT / "metadata" / "quality"
PRIVATE_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_processed_value_source_map_completion_owner_group_decision_input_kit"
PRIVATE_RESPONSE_TEMPLATE_PATH = PRIVATE_DIR / "private_owner_group_decision_response_template.json"
PRIVATE_CODEBOOK_PATH = PRIVATE_DIR / "private_owner_group_decision_codes_zh.md"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_DIR / "private_owner_group_decision_input_kit_diagnostic.json"

SUMMARY_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_group_decision_input_kit_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_group_decision_input_kit_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_group_decision_input_kit_go_no_go_report.json"

PUBLIC_ARTIFACTS = [
    SUMMARY_PATH,
    MANIFEST_PATH,
    GO_NO_GO_PATH,
    HUMAN_DIR / "processed_value_source_map_completion_owner_group_decision_input_kit_report.md",
    HUMAN_DIR / "go_no_go_record.md",
    HUMAN_DIR / "test_results.md",
    HUMAN_DIR / "risk_register.md",
    HUMAN_DIR / "rollback_plan.md",
    QUALITY_DIR / "v014_processed_value_source_map_completion_owner_group_decision_input_kit_summary.json",
    QUALITY_DIR / "v014_processed_value_source_map_completion_owner_group_decision_input_kit_manifest.json",
    QUALITY_DIR / "v014_processed_value_source_map_completion_owner_group_decision_input_kit_go_no_go_report.json",
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
        "private_source_pending_queue_committed",
        "private_source_diagnostic_committed",
        "private_response_template_committed",
        "private_codebook_committed",
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


def _check_private_kit() -> None:
    template = _read_json(PRIVATE_RESPONSE_TEMPLATE_PATH)
    diagnostic = _read_json(PRIVATE_DIAGNOSTIC_PATH)
    for name, payload in (("template", template), ("diagnostic", diagnostic)):
        _require_equal(f"{name}.phase_id", payload.get("phase_id"), PHASE_ID)
        _require_equal(f"{name}.task_id", payload.get("task_id"), TASK_ID)
        _require_equal(f"{name}.version", payload.get("version"), VERSION)
        _require_equal(f"{name}.review_group_count", payload.get("review_group_count"), 22)
        _require_equal(f"{name}.response_row_count", payload.get("response_row_count"), 113)
    _require_equal("template.pending_group_template_count", template.get("pending_group_template_count"), 22)
    _require_false("template.active", template.get("template_is_active_authorization_record"))
    _require_false("template.decisions_supplied", template.get("owner_group_decisions_supplied"))
    _require_false("template.active_ready", template.get("active_owner_authorized_fill_record_ready"))
    groups = template.get("groups", [])
    if not isinstance(groups, list):
        raise ValidationError("template.groups must be a list")
    _require_equal("template.groups length", len(groups), 22)
    for group in groups:
        if not isinstance(group, dict):
            raise ValidationError("template group must be an object")
        _require_equal("group.owner_group_decision_code", group.get("owner_group_decision_code"), PENDING_DECISION_CODE)
        _require_false("group.active_authorization_allowed", group.get("active_authorization_allowed"))
    _require_equal("diagnostic.pending_group_template_count", diagnostic.get("pending_group_template_count"), 22)
    _require_equal("diagnostic.allowed code count", diagnostic.get("allowed_owner_group_decision_code_count"), 5)
    _require_false("diagnostic.decisions_supplied", diagnostic.get("owner_group_decisions_supplied"))
    _require_false("diagnostic.decision_applied", diagnostic.get("owner_group_decision_applied"))
    _require_false("diagnostic.active_ready", diagnostic.get("active_owner_authorized_fill_record_ready"))
    _require_false(
        "diagnostic.source_map_completion_reapplication_ready",
        diagnostic.get("source_map_completion_reapplication_ready"),
    )
    _require_equal("diagnostic.conclusion", diagnostic.get("diagnostic_conclusion"), DIAGNOSTIC_CONCLUSION)
    _require_equal("diagnostic.next_required_input", diagnostic.get("next_required_input"), NEXT_REQUIRED_INPUT)
    _check_raw_boundary(diagnostic.get("raw_boundary", {}))
    if not PRIVATE_CODEBOOK_PATH.exists():
        raise ValidationError(f"missing private codebook: {PRIVATE_CODEBOOK_PATH}")
    for path in (PRIVATE_RESPONSE_TEMPLATE_PATH, PRIVATE_CODEBOOK_PATH, PRIVATE_DIAGNOSTIC_PATH):
        result = subprocess.run(["git", "check-ignore", "-q", path.as_posix()], cwd=PROJECT_ROOT.parent, check=False)
        _require_equal(f"{path}.gitignored", result.returncode, 0)
        _require_equal(f"{path}.tracked", _git_output(["ls-files", path.as_posix()]), "")


def validate(*, require_private_kit: bool = False) -> dict[str, Any]:
    summary = _read_json(SUMMARY_PATH)
    manifest = _read_json(MANIFEST_PATH)
    go_no_go = _read_json(GO_NO_GO_PATH)
    metadata_summary = _read_json(
        QUALITY_DIR / "v014_processed_value_source_map_completion_owner_group_decision_input_kit_summary.json"
    )
    metadata_manifest = _read_json(
        QUALITY_DIR / "v014_processed_value_source_map_completion_owner_group_decision_input_kit_manifest.json"
    )
    metadata_go_no_go = _read_json(
        QUALITY_DIR / "v014_processed_value_source_map_completion_owner_group_decision_input_kit_go_no_go_report.json"
    )

    _require_equal("metadata summary copy", metadata_summary, summary)
    _require_equal("metadata manifest copy", metadata_manifest, manifest)
    _require_equal("metadata go/no-go copy", metadata_go_no_go, go_no_go)
    _require_equal("summary.phase_id", summary.get("phase_id"), PHASE_ID)
    _require_equal("summary.task_id", summary.get("task_id"), TASK_ID)
    _require_equal("summary.version", summary.get("version"), VERSION)
    _require_equal("summary.decision", summary.get("decision"), "NO_GO")
    _require_equal("summary.diagnostic_conclusion", summary.get("diagnostic_conclusion"), DIAGNOSTIC_CONCLUSION)
    _require_equal("summary.next_required_input", summary.get("next_required_input"), NEXT_REQUIRED_INPUT)
    _require_equal("summary.source_decision", summary.get("source_decision"), "NO_GO")
    _require_equal("summary.review_group_count", summary.get("review_group_count"), 22)
    _require_equal("summary.response_row_count", summary.get("response_row_count"), 113)
    _require_equal("summary.pending_group_template_count", summary.get("pending_group_template_count"), 22)
    _require_equal("summary.allowed_owner_group_decision_code_count", summary.get("allowed_owner_group_decision_code_count"), 5)
    _require_equal(
        "summary.ambiguous group count",
        summary.get("candidate_status_group_counts", {}).get("auto_ambiguous_multiple_candidates_requires_owner_review"),
        19,
    )
    _require_equal(
        "summary.nonnumeric group count",
        summary.get("candidate_status_group_counts", {}).get("requires_non_numeric_owner_mapping"),
        2,
    )
    _require_equal(
        "summary.unmatched group count",
        summary.get("candidate_status_group_counts", {}).get("auto_unmatched_requires_owner_review"),
        1,
    )
    _require_equal(
        "summary.ambiguous row count",
        summary.get("candidate_status_response_row_counts", {}).get("auto_ambiguous_multiple_candidates_requires_owner_review"),
        101,
    )
    _require_equal(
        "summary.nonnumeric row count",
        summary.get("candidate_status_response_row_counts", {}).get("requires_non_numeric_owner_mapping"),
        8,
    )
    _require_equal(
        "summary.unmatched row count",
        summary.get("candidate_status_response_row_counts", {}).get("auto_unmatched_requires_owner_review"),
        4,
    )
    for key in (
        "private_response_template_written",
        "private_response_template_gitignored",
        "private_codebook_written",
        "private_codebook_gitignored",
        "private_diagnostic_written",
        "private_diagnostic_gitignored",
    ):
        _require_true(f"summary.{key}", summary.get(key))
    for key in (
        "owner_group_decisions_supplied",
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
    _check_raw_boundary(summary.get("raw_boundary", {}))
    _check_public_safety(summary.get("public_safety", {}))
    _require_equal("go_no_go.decision", go_no_go.get("decision"), "NO_GO")
    _require_equal("go_no_go.review_group_count", go_no_go.get("review_group_count"), 22)
    _require_equal("go_no_go.response_row_count", go_no_go.get("response_row_count"), 113)
    _require_equal("go_no_go.pending_group_template_count", go_no_go.get("pending_group_template_count"), 22)
    _require_false("go_no_go.decisions_supplied", go_no_go.get("owner_group_decisions_supplied"))
    _require_false("go_no_go.decision_applied", go_no_go.get("owner_group_decision_applied"))
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
    if require_private_kit:
        _check_private_kit()
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-private-kit", action="store_true")
    args = parser.parse_args()
    manifest = validate(require_private_kit=args.require_private_kit)
    print(
        "PASS: KMFA v0.1.4 owner group decision input kit validated "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"groups={manifest['summary']['review_group_count']}, "
        f"rows={manifest['summary']['response_row_count']}, "
        f"templates={manifest['summary']['pending_group_template_count']})"
    )


if __name__ == "__main__":
    main()
