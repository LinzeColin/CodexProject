#!/usr/bin/env python3
"""Validate KMFA v0.1.4 residual gap report prep."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PHASE_ID = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_RESIDUAL_GAP_REPORT_PREP"
VERSION = "0.1.4-residual-gap-report-prep"
DIAGNOSTIC_CONCLUSION = "residual_gap_report_prepared_delivery_still_blocked"
PREVIOUS_REQUIRED_INPUT = "private_residual_gap_report_or_corrected_source_package_before_any_delivery_claim"
NEXT_REQUIRED_INPUT = "corrected_source_package_or_owner_authorized_private_raw_comparison_scope"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
QUALITY_DIR = PROJECT_ROOT / "metadata" / "quality"
PRIVATE_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_processed_value_source_map_completion_residual_gap_report_prep"
PRIVATE_GAP_REPORT_PATH = PRIVATE_DIR / "private_residual_gap_report.json"
PRIVATE_GAP_REPORT_MARKDOWN_PATH = PRIVATE_DIR / "private_residual_gap_report.md"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_DIR / "private_residual_gap_report_diagnostic.json"

SUMMARY_PATH = MACHINE_DIR / "processed_value_source_map_completion_residual_gap_report_prep_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_value_source_map_completion_residual_gap_report_prep_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_value_source_map_completion_residual_gap_report_prep_go_no_go_report.json"
PUBLIC_GAP_MATRIX_PATH = MACHINE_DIR / "processed_value_source_map_completion_residual_gap_matrix_public_safe.json"

PUBLIC_ARTIFACTS = [
    SUMMARY_PATH,
    MANIFEST_PATH,
    GO_NO_GO_PATH,
    PUBLIC_GAP_MATRIX_PATH,
    HUMAN_DIR / "processed_value_source_map_completion_residual_gap_report_prep_report.md",
    HUMAN_DIR / "residual_gap_report_public_safe.md",
    HUMAN_DIR / "go_no_go_record.md",
    HUMAN_DIR / "test_results.md",
    HUMAN_DIR / "risk_register.md",
    HUMAN_DIR / "rollback_plan.md",
    QUALITY_DIR / "v014_residual_gap_report_prep_summary.json",
    QUALITY_DIR / "v014_residual_gap_report_prep_manifest.json",
    QUALITY_DIR / "v014_residual_gap_report_prep_go_no_go_report.json",
    QUALITY_DIR / "v014_residual_gap_matrix_public_safe.json",
]

FORBIDDEN_PUBLIC_PATTERNS = [
    re.compile(r"/Users/linzezhang/Downloads"),
    re.compile(r"KMFA_MetaData"),
    re.compile(r"\.(xlsx|xlsm|xls|zip|pdf)\b", re.IGNORECASE),
    re.compile(
        r'"(target_slot_id|target_slot_ids|review_group_id|response_item_id|raw_file_name|archive_member_name|sheet_name|cell_address|raw_value|normalized_decimal|context_text)"',
        re.IGNORECASE,
    ),
    re.compile(r"sha256:[0-9a-f]{64}"),
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
]


class ValidationError(Exception):
    pass


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ValidationError(f"missing JSON artifact: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValidationError(f"{path} must contain a JSON object")
    return value


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


def _check_raw_boundary(raw_boundary: dict[str, Any]) -> None:
    _require_true("raw_boundary.raw_data_root_readonly_policy_active", raw_boundary.get("raw_data_root_readonly_policy_active"))
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
        _require_false(f"raw_boundary.{key}", raw_boundary.get(key))


def _check_public_safety(public_safety: dict[str, Any]) -> None:
    _require_true("public_safety.public_safe_aggregate_only", public_safety.get("public_safe_aggregate_only"))
    for key, value in public_safety.items():
        if key == "public_safe_aggregate_only":
            continue
        _require_false(f"public_safety.{key}", value)


def _check_public_artifacts() -> None:
    for path in PUBLIC_ARTIFACTS:
        if not path.exists():
            raise ValidationError(f"missing public artifact: {path}")
        text = path.read_text(encoding="utf-8")
        for pattern in FORBIDDEN_PUBLIC_PATTERNS:
            if pattern.search(text):
                raise ValidationError(f"forbidden public pattern {pattern.pattern!r} in {path}")


def _check_no_raw_private_files_tracked() -> None:
    tracked = _git_output(["ls-files", "KMFA"]).splitlines()
    forbidden = re.compile(
        r"\.codex_private_runtime|/Users/linzezhang/Downloads|KMFA_MetaData|\.(zip|xlsx|xlsm|xls|pdf|sqlite|sqlite3|db|key|pem|p12|pfx)$",
        re.IGNORECASE,
    )
    matches = [path for path in tracked if forbidden.search(path)]
    if matches:
        raise ValidationError("tracked raw/private files detected: " + ", ".join(matches[:10]))


def _check_gap_matrix(matrix: dict[str, Any]) -> None:
    _require_equal("gap_matrix.phase_id", matrix.get("phase_id"), PHASE_ID)
    _require_equal("gap_matrix.decision", matrix.get("decision"), "NO_GO")
    _require_equal("gap_matrix.category_count", matrix.get("gap_category_count"), 4)
    _require_equal("gap_matrix.blocker_count", matrix.get("aggregate_blocker_count"), 4)
    _require_equal("gap_matrix.non_actionable_groups", matrix.get("non_actionable_group_count"), 3)
    _require_equal("gap_matrix.non_actionable_slots", matrix.get("non_actionable_target_slot_count"), 12)
    categories = matrix.get("categories", [])
    if not isinstance(categories, list):
        raise ValidationError("gap matrix categories must be a list")
    _require_equal("gap_matrix.categories length", len(categories), 4)
    codes = {item.get("gap_code") for item in categories if isinstance(item, dict)}
    _require_equal(
        "gap_matrix.codes",
        codes,
        {
            "NON_ACTIONABLE_GROUPS",
            "FULL_RECONCILIATION_BLOCKED",
            "FORMAL_REPORT_BLOCKED",
            "UPLOAD_AND_APP_BLOCKED",
        },
    )
    if not all(item.get("blocks_delivery") is True for item in categories if isinstance(item, dict)):
        raise ValidationError("all gap categories must block delivery")


def _check_private_gap_report() -> None:
    report = _read_json(PRIVATE_GAP_REPORT_PATH)
    diagnostic = _read_json(PRIVATE_DIAGNOSTIC_PATH)
    markdown = PRIVATE_GAP_REPORT_MARKDOWN_PATH.read_text(encoding="utf-8") if PRIVATE_GAP_REPORT_MARKDOWN_PATH.exists() else ""
    _require_equal("report.phase_id", report.get("phase_id"), PHASE_ID)
    _require_equal("diagnostic.phase_id", diagnostic.get("phase_id"), PHASE_ID)
    _require_true("report.ready", report.get("residual_gap_report_ready"))
    _require_true("report.previous_input_resolved", report.get("previous_required_input_resolved_by_this_phase"))
    _require_equal("report.gap_category_count", report.get("gap_category_count"), 4)
    _require_equal("report.aggregate_blocker_count", report.get("aggregate_blocker_count"), 4)
    _require_equal("report.non_actionable_groups", report.get("non_actionable_group_count"), 3)
    _require_equal("report.non_actionable_slots", report.get("non_actionable_target_slot_count"), 12)
    _check_gap_matrix(report.get("public_gap_matrix", {}))
    _require_true("diagnostic.ready", diagnostic.get("residual_gap_report_ready"))
    _require_equal("diagnostic.gap_category_count", diagnostic.get("gap_category_count"), 4)
    _require_false("diagnostic.full_comparison_allowed", diagnostic.get("full_comparison_allowed_by_this_phase"))
    _require_false("diagnostic.delivery_allowed", diagnostic.get("delivery_allowed"))
    _check_raw_boundary(report.get("raw_boundary", {}))
    _check_raw_boundary(diagnostic.get("raw_boundary", {}))
    if "Private Residual Gap Report" not in markdown:
        raise ValidationError("private residual gap markdown missing title")
    for path in (PRIVATE_GAP_REPORT_PATH, PRIVATE_GAP_REPORT_MARKDOWN_PATH, PRIVATE_DIAGNOSTIC_PATH):
        if not path.exists():
            raise ValidationError(f"missing private artifact: {path}")
        if not _git_check_ignored(path):
            raise ValidationError(f"private artifact is not gitignored: {path}")
        _require_equal(f"{path}.tracked", _git_output(["ls-files", path.as_posix()]), "")


def validate(*, require_private_gap_report: bool = False) -> dict[str, Any]:
    summary = _read_json(SUMMARY_PATH)
    manifest = _read_json(MANIFEST_PATH)
    go_no_go = _read_json(GO_NO_GO_PATH)
    gap_matrix = _read_json(PUBLIC_GAP_MATRIX_PATH)
    metadata_summary = _read_json(QUALITY_DIR / "v014_residual_gap_report_prep_summary.json")
    metadata_manifest = _read_json(QUALITY_DIR / "v014_residual_gap_report_prep_manifest.json")
    metadata_go_no_go = _read_json(QUALITY_DIR / "v014_residual_gap_report_prep_go_no_go_report.json")
    metadata_gap_matrix = _read_json(QUALITY_DIR / "v014_residual_gap_matrix_public_safe.json")
    _require_equal("metadata summary", metadata_summary, summary)
    _require_equal("metadata manifest", metadata_manifest, manifest)
    _require_equal("metadata go/no-go", metadata_go_no_go, go_no_go)
    _require_equal("metadata gap matrix", metadata_gap_matrix, gap_matrix)
    _require_equal("summary.phase_id", summary.get("phase_id"), PHASE_ID)
    _require_equal("summary.version", summary.get("version"), VERSION)
    _require_equal("summary.decision", summary.get("decision"), "NO_GO")
    _require_equal("summary.diagnostic_conclusion", summary.get("diagnostic_conclusion"), DIAGNOSTIC_CONCLUSION)
    _require_true("summary.private_source_read", summary.get("source_private_resolution_read_performed_by_this_phase"))
    _require_equal("summary.previous_required_input", summary.get("previous_required_input"), PREVIOUS_REQUIRED_INPUT)
    _require_true("summary.previous_input_resolved", summary.get("previous_required_input_resolved_by_this_phase"))
    _require_true("summary.residual_gap_ready", summary.get("residual_gap_report_ready"))
    _require_true("summary.public_matrix_ready", summary.get("public_gap_matrix_ready"))
    _require_equal("summary.gap_category_count", summary.get("gap_category_count"), 4)
    _require_true("summary.lock_active", summary.get("final_no_go_governance_lock_active"))
    _require_true("summary.partial_ready", summary.get("partial_evidence_chain_ready"))
    _require_equal("summary.blocker_count", summary.get("blocker_count"), 4)
    _require_equal("summary.non_actionable_groups", summary.get("non_actionable_group_count"), 3)
    _require_equal("summary.non_actionable_slots", summary.get("non_actionable_target_slot_count"), 12)
    _require_false("summary.non_actionable_delivery_use", summary.get("non_actionable_groups_delivery_use_allowed"))
    _require_false("summary.non_actionable_report_use", summary.get("non_actionable_groups_formal_report_use_allowed"))
    _require_false("summary.non_actionable_business_use", summary.get("non_actionable_groups_business_execution_use_allowed"))
    _require_true("summary.next_input_required", summary.get("corrected_source_package_required_or_raw_scope_required"))
    for key in (
        "delivery_allowed",
        "formal_report_allowed",
        "github_upload_allowed",
        "github_upload_performed",
        "app_reinstall_allowed",
        "app_reinstall_performed",
        "business_execution_allowed",
        "business_execution_performed",
        "full_source_map_completion_reapplication_ready",
        "full_raw_to_processed_value_comparison_ready",
        "business_value_consistency_verified",
        "canonical_source_map_mutated",
        "raw_to_processed_value_comparison_performed_by_this_phase",
    ):
        _require_false(f"summary.{key}", summary.get(key))
    _require_equal("summary.canonical_records_applied", summary.get("canonical_source_map_records_applied_count"), 0)
    for key in (
        "private_gap_report_written",
        "private_gap_report_gitignored",
        "private_gap_report_markdown_written",
        "private_gap_report_markdown_gitignored",
        "private_diagnostic_written",
        "private_diagnostic_gitignored",
    ):
        _require_true(f"summary.{key}", summary.get(key))
    _check_public_safety(summary.get("public_safety", {}))
    _check_raw_boundary(summary.get("raw_boundary", {}))
    _require_equal("summary.next_required_input", summary.get("next_required_input"), NEXT_REQUIRED_INPUT)
    _require_equal("go_no_go.decision", go_no_go.get("decision"), "NO_GO")
    _require_equal("go_no_go.blocked_until", go_no_go.get("blocked_until"), NEXT_REQUIRED_INPUT)
    _require_true("go_no_go.residual_gap_ready", go_no_go.get("residual_gap_report_ready"))
    _require_true("go_no_go.previous_input_resolved", go_no_go.get("previous_required_input_resolved_by_this_phase"))
    _require_equal("go_no_go.gap_category_count", go_no_go.get("gap_category_count"), 4)
    for key in (
        "delivery_allowed",
        "github_upload_allowed",
        "app_reinstall_allowed",
        "business_execution_allowed",
    ):
        _require_false(f"go_no_go.{key}", go_no_go.get(key))
    _require_equal("manifest.summary", manifest.get("summary"), summary)
    _require_equal("manifest.go_no_go", manifest.get("go_no_go"), go_no_go)
    _require_equal("manifest.public_gap_matrix", manifest.get("public_gap_matrix"), gap_matrix)
    _check_gap_matrix(gap_matrix)
    _check_public_artifacts()
    _check_no_raw_private_files_tracked()
    if require_private_gap_report:
        _check_private_gap_report()
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-private-gap-report", action="store_true")
    args = parser.parse_args()
    manifest = validate(require_private_gap_report=args.require_private_gap_report)
    print(
        "PASS: KMFA v0.1.4 residual gap report prep validated "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"report={manifest['summary']['residual_gap_report_ready']}, "
        f"gap_categories={manifest['summary']['gap_category_count']})"
    )


if __name__ == "__main__":
    main()
