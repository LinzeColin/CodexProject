#!/usr/bin/env python3
"""Validate KMFA v0.1.4 final NO-GO governance lock."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PHASE_ID = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_FINAL_NO_GO_GOVERNANCE_LOCK"
VERSION = "0.1.4-final-no-go-governance-lock"
DIAGNOSTIC_CONCLUSION = "final_no_go_governance_locked_full_reconciliation_blocked"
NEXT_REQUIRED_INPUT = "explicit_business_resolution_for_non_actionable_groups_before_full_reconciliation"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
QUALITY_DIR = PROJECT_ROOT / "metadata" / "quality"
PRIVATE_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_processed_value_source_map_completion_final_no_go_governance_lock"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_DIR / "private_final_no_go_governance_lock_diagnostic.json"

SUMMARY_PATH = MACHINE_DIR / "processed_value_source_map_completion_final_no_go_governance_lock_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_value_source_map_completion_final_no_go_governance_lock_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_value_source_map_completion_final_no_go_governance_lock_go_no_go_report.json"

PUBLIC_ARTIFACTS = [
    SUMMARY_PATH,
    MANIFEST_PATH,
    GO_NO_GO_PATH,
    HUMAN_DIR / "processed_value_source_map_completion_final_no_go_governance_lock_report.md",
    HUMAN_DIR / "go_no_go_record.md",
    HUMAN_DIR / "test_results.md",
    HUMAN_DIR / "risk_register.md",
    HUMAN_DIR / "rollback_plan.md",
    QUALITY_DIR / "v014_final_no_go_governance_lock_summary.json",
    QUALITY_DIR / "v014_final_no_go_governance_lock_manifest.json",
    QUALITY_DIR / "v014_final_no_go_governance_lock_go_no_go_report.json",
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
    forbidden = re.compile(r"\.codex_private_runtime|/Users/linzezhang/Downloads|KMFA_MetaData|\.(zip|xlsx|xlsm|xls|pdf|sqlite|sqlite3|db|key|pem|p12|pfx)$", re.IGNORECASE)
    matches = [path for path in tracked if forbidden.search(path)]
    if matches:
        raise ValidationError("tracked raw/private files detected: " + ", ".join(matches[:10]))


def _check_private_diagnostic() -> None:
    diagnostic = _read_json(PRIVATE_DIAGNOSTIC_PATH)
    _require_equal("diagnostic.phase_id", diagnostic.get("phase_id"), PHASE_ID)
    _require_true("diagnostic.lock_active", diagnostic.get("lock_active"))
    _require_true("diagnostic.partial_ready", diagnostic.get("partial_evidence_chain_ready"))
    _require_equal("diagnostic.blocker_count", diagnostic.get("blocker_count"), 4)
    _require_equal("diagnostic.non_actionable_groups", diagnostic.get("non_actionable_group_count"), 3)
    _require_equal("diagnostic.non_actionable_slots", diagnostic.get("non_actionable_target_slot_count"), 12)
    locked = diagnostic.get("locked_gates", {})
    for key in (
        "delivery_allowed",
        "formal_report_allowed",
        "github_upload_allowed",
        "app_reinstall_allowed",
        "business_execution_allowed",
        "full_source_map_completion_reapplication_allowed",
        "full_raw_to_processed_value_comparison_allowed",
        "business_value_consistency_claim_allowed",
    ):
        _require_false(f"diagnostic.locked_gates.{key}", locked.get(key))
    _check_raw_boundary(diagnostic.get("raw_boundary", {}))
    if not _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH):
        raise ValidationError(f"private diagnostic is not gitignored: {PRIVATE_DIAGNOSTIC_PATH}")
    _require_equal("private diagnostic tracked", _git_output(["ls-files", PRIVATE_DIAGNOSTIC_PATH.as_posix()]), "")


def validate(*, require_private_diagnostic: bool = False) -> dict[str, Any]:
    summary = _read_json(SUMMARY_PATH)
    manifest = _read_json(MANIFEST_PATH)
    go_no_go = _read_json(GO_NO_GO_PATH)
    metadata_summary = _read_json(QUALITY_DIR / "v014_final_no_go_governance_lock_summary.json")
    metadata_manifest = _read_json(QUALITY_DIR / "v014_final_no_go_governance_lock_manifest.json")
    metadata_go_no_go = _read_json(QUALITY_DIR / "v014_final_no_go_governance_lock_go_no_go_report.json")
    _require_equal("metadata summary", metadata_summary, summary)
    _require_equal("metadata manifest", metadata_manifest, manifest)
    _require_equal("metadata go/no-go", metadata_go_no_go, go_no_go)
    _require_equal("summary.phase_id", summary.get("phase_id"), PHASE_ID)
    _require_equal("summary.version", summary.get("version"), VERSION)
    _require_equal("summary.decision", summary.get("decision"), "NO_GO")
    _require_equal("summary.diagnostic_conclusion", summary.get("diagnostic_conclusion"), DIAGNOSTIC_CONCLUSION)
    _require_true("summary.lock_active", summary.get("final_no_go_governance_lock_active"))
    _require_true("summary.partial_ready", summary.get("partial_evidence_chain_ready"))
    _require_equal("summary.blocker_count", summary.get("blocker_count"), 4)
    _require_equal("summary.blocking_count", summary.get("blocking_severity_count"), 4)
    _require_equal("summary.non_actionable_groups", summary.get("non_actionable_group_count"), 3)
    _require_equal("summary.non_actionable_slots", summary.get("non_actionable_target_slot_count"), 12)
    _require_equal("summary.keep_no_go", summary.get("keep_no_go_resolution_count"), 3)
    _require_equal("summary.unlock_input", summary.get("unlock_required_input"), NEXT_REQUIRED_INPUT)
    for key in (
        "delivery_allowed",
        "formal_report_allowed",
        "github_upload_performed",
        "github_upload_allowed",
        "app_reinstall_performed",
        "app_reinstall_allowed",
        "business_execution_performed",
        "business_execution_allowed",
        "full_source_map_completion_reapplication_ready",
        "full_source_map_completion_reapplication_performed",
        "full_raw_to_processed_value_comparison_ready",
        "full_raw_to_processed_value_comparison_performed",
        "business_value_consistency_verified",
        "lineage_full_check_complete",
        "canonical_source_map_mutated",
        "raw_to_processed_value_comparison_performed_by_this_phase",
    ):
        _require_false(f"summary.{key}", summary.get(key))
    _require_equal("summary.canonical_records_applied", summary.get("canonical_source_map_records_applied_count"), 0)
    _require_true("summary.private_diagnostic_written", summary.get("private_diagnostic_written"))
    _require_true("summary.private_diagnostic_gitignored", summary.get("private_diagnostic_gitignored"))
    _check_public_safety(summary.get("public_safety", {}))
    _check_raw_boundary(summary.get("raw_boundary", {}))
    _require_equal("go_no_go.decision", go_no_go.get("decision"), "NO_GO")
    _require_equal("go_no_go.blocked_until", go_no_go.get("blocked_until"), NEXT_REQUIRED_INPUT)
    _require_true("go_no_go.lock_active", go_no_go.get("final_no_go_governance_lock_active"))
    _require_true("go_no_go.partial_ready", go_no_go.get("partial_evidence_chain_ready"))
    _require_equal("go_no_go.blocker_count", go_no_go.get("blocker_count"), 4)
    for key in (
        "delivery_allowed",
        "github_upload_allowed",
        "app_reinstall_allowed",
        "business_execution_allowed",
        "full_source_map_completion_reapplication_ready",
        "full_raw_to_processed_value_comparison_ready",
        "business_value_consistency_verified",
    ):
        _require_false(f"go_no_go.{key}", go_no_go.get(key))
    _require_equal("manifest.summary", manifest.get("summary"), summary)
    _require_equal("manifest.go_no_go", manifest.get("go_no_go"), go_no_go)
    _check_public_artifacts()
    _check_no_raw_private_files_tracked()
    if require_private_diagnostic:
        _check_private_diagnostic()
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-private-diagnostic", action="store_true")
    args = parser.parse_args()
    manifest = validate(require_private_diagnostic=args.require_private_diagnostic)
    print(
        "PASS: KMFA v0.1.4 final NO-GO governance lock validated "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"lock={manifest['summary']['final_no_go_governance_lock_active']}, "
        f"blockers={manifest['summary']['blocker_count']})"
    )


if __name__ == "__main__":
    main()
