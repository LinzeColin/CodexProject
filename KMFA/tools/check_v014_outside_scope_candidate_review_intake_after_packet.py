#!/usr/bin/env python3
"""Validate KMFA v0.1.4 outside-scope candidate review intake artifacts."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PHASE_ID = "V014_OUTSIDE_SCOPE_CANDIDATE_REVIEW_INTAKE_AFTER_PACKET"
TASK_ID = "KMFA-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-INTAKE-AFTER-PACKET-20260707"
ACCEPTANCE_ID = "ACC-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-INTAKE-AFTER-PACKET"
VERSION = "0.1.4-outside-scope-candidate-review-intake-after-packet"
STATUS = "completed_validated_local_only_outside_scope_candidate_review_intake_keep_pending_no_go"
DECISION = "NO_GO"
AUTHORITY_BASIS = "owner_delegated_codex_conservative_default_decision_current_thread"
DIAGNOSTIC_CONCLUSION = "delegated_keep_pending_review_response_intaken_no_source_map_correction"
NEXT_REQUIRED_INPUT = "strong_owner_or_authorized_delegate_candidate_selection_or_source_map_reference_before_correction"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "outside_scope_candidate_review_intake_after_packet_summary.json"
MANIFEST_PATH = MACHINE_DIR / "outside_scope_candidate_review_intake_after_packet_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "outside_scope_candidate_review_intake_after_packet_go_no_go_report.json"
MATRIX_PATH = MACHINE_DIR / "outside_scope_candidate_review_intake_after_packet_matrix_public_safe.json"
REPORT_PATH = HUMAN_DIR / "outside_scope_candidate_review_intake_after_packet_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_outside_scope_candidate_review_intake_after_packet_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_outside_scope_candidate_review_intake_after_packet_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_outside_scope_candidate_review_intake_after_packet_go_no_go_report.json"
METADATA_MATRIX_PATH = PROJECT_ROOT / "metadata/quality/v014_outside_scope_candidate_review_intake_after_packet_matrix_public_safe.json"

PRIVATE_OUTPUT_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_outside_scope_candidate_review_intake_after_packet"
PRIVATE_RESPONSE_RECORD_PATH = PRIVATE_OUTPUT_DIR / "private_delegated_review_response_record.json"
PRIVATE_RESPONSE_ITEMS_PATH = PRIVATE_OUTPUT_DIR / "private_delegated_review_response_items.jsonl"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_delegated_review_response_diagnostic.json"

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
FORBIDDEN_PUBLIC_PATTERNS = [
    re.compile(re.escape(RAW_DOWNLOADS_MARKER)),
    re.compile(re.escape(RAW_INBOX_MARKER)),
    re.compile(re.escape(".codex_private_runtime")),
    re.compile(r"\.(xlsx|xlsm|xls|zip|pdf)\b", re.IGNORECASE),
    re.compile(r"sha256:[0-9a-f]{64}"),
    re.compile(r'"[0-9a-f]{64}"'),
    re.compile(
        r'"(raw_file_name|archive_member_name|sheet_name|cell_address|raw_value|normalized_decimal|context_text|numeric_value_fingerprint|processed_value_fingerprint|value_fingerprint|target_slot_id|review_group_id|source_ref_hash|source_cell_ref_hash|source_record_ref_hash|private_processed_ref_hash)"',
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
        "user_declared_raw_data_immutable",
        "raw_data_root_readonly_policy_active",
        "source_private_review_packet_read_performed_by_this_phase",
        "private_delegated_review_response_record_written_by_this_phase",
        "private_delegated_review_response_items_written_by_this_phase",
        "private_delegated_review_diagnostic_written_by_this_phase",
    ):
        _require_true(f"raw_boundary.{key}", raw_boundary.get(key))
    for key in (
        "source_private_review_packet_mutated_by_this_phase",
        "raw_inbox_read_performed_by_this_phase",
        "raw_inbox_list_performed_by_this_phase",
        "raw_inbox_stat_performed_by_this_phase",
        "raw_inbox_hash_or_value_fingerprint_performed_by_this_phase",
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


def _check_summary(summary: dict[str, Any], matrix: dict[str, Any], go_no_go: dict[str, Any], manifest: dict[str, Any]) -> None:
    _require_equal("summary.phase_id", summary.get("phase_id"), PHASE_ID)
    _require_equal("summary.task_id", summary.get("task_id"), TASK_ID)
    _require_equal("summary.acceptance_id", summary.get("acceptance_id"), ACCEPTANCE_ID)
    _require_equal("summary.version", summary.get("version"), VERSION)
    _require_equal("summary.status", summary.get("status"), STATUS)
    _require_equal("summary.decision", summary.get("decision"), DECISION)
    _require_equal("summary.authority_basis", summary.get("authority_basis"), AUTHORITY_BASIS)
    _require_equal("summary.diagnostic_conclusion", summary.get("diagnostic_conclusion"), DIAGNOSTIC_CONCLUSION)
    _require_equal("summary.source_review_packet_phase_id", summary.get("source_review_packet_phase_id"), "V014_OUTSIDE_SCOPE_CANDIDATE_REVIEW_PACKET_AFTER_ALIGNMENT")
    _require_equal("summary.source_review_packet_item_count", summary.get("source_review_packet_item_count"), 72)
    _require_equal("summary.source_review_group_count", summary.get("source_review_group_count"), 10)
    _require_equal("summary.source_owner_review_required_item_count", summary.get("source_owner_review_required_item_count"), 72)
    _require_false("summary.source_owner_review_response_supplied", summary.get("source_owner_review_response_supplied"))
    _require_equal("summary.intake_response_item_count", summary.get("intake_response_item_count"), 72)
    _require_true("summary.authorized_delegate_response_supplied", summary.get("authorized_delegate_response_supplied_by_this_phase"))
    _require_false("summary.owner_direct_response_supplied", summary.get("owner_direct_response_supplied_by_this_phase"))
    _require_equal("summary.delegated_decision_record_count", summary.get("delegated_decision_record_count"), 72)
    _require_equal("summary.delegated_keep_pending_response_count", summary.get("delegated_keep_pending_response_count"), 72)
    _require_equal("summary.selected_private_candidate_count", summary.get("selected_private_candidate_count"), 0)
    _require_equal("summary.corrected_source_map_reference_count", summary.get("corrected_source_map_reference_count"), 0)
    _require_equal(
        "summary.authoritative_non_numeric_or_calculation_mapping_count",
        summary.get("authoritative_non_numeric_or_calculation_mapping_count"),
        0,
    )
    _require_equal("summary.source_map_actionable_response_count", summary.get("source_map_actionable_response_count"), 0)
    for key in (
        "source_map_correction_ready",
        "raw_to_processed_value_comparison_performed_by_this_phase",
        "full_raw_to_processed_value_comparison_ready",
        "full_raw_to_processed_value_comparison_complete",
        "business_value_consistency_verified",
        "github_upload_performed",
        "app_reinstall_performed",
        "business_execution_performed",
    ):
        _require_false(f"summary.{key}", summary.get(key))
    for key in (
        "private_delegated_review_response_record_written",
        "private_delegated_review_response_record_gitignored",
        "private_delegated_review_response_items_written",
        "private_delegated_review_response_items_gitignored",
        "private_delegated_review_diagnostic_written",
        "private_delegated_review_diagnostic_gitignored",
    ):
        _require_true(f"summary.{key}", summary.get(key))
    _require_equal("summary.next_required_input", summary.get("next_required_input"), NEXT_REQUIRED_INPUT)
    _check_raw_boundary(summary.get("raw_boundary", {}))
    _check_public_safety(summary.get("public_safety", {}))

    _require_equal("matrix.phase_id", matrix.get("phase_id"), PHASE_ID)
    _require_equal("matrix.check_count", matrix.get("check_count"), 8)
    _require_equal("matrix.pass_count", matrix.get("pass_count"), 6)
    _require_equal("matrix.fail_count", matrix.get("fail_count"), 2)
    checks = {row.get("check_code"): row.get("status") for row in matrix.get("checks", []) if isinstance(row, dict)}
    _require_equal("matrix.actionable_source_map_response_present", checks.get("actionable_source_map_response_present"), "FAIL")
    _require_equal("matrix.candidate_selection_present", checks.get("candidate_selection_present"), "FAIL")
    _require_false("matrix.source_map_correction_ready", matrix.get("source_map_correction_ready"))
    _require_false("matrix.full_raw_to_processed_value_comparison_complete", matrix.get("full_raw_to_processed_value_comparison_complete"))

    _require_equal("go_no_go.phase_id", go_no_go.get("phase_id"), PHASE_ID)
    _require_equal("go_no_go.decision", go_no_go.get("decision"), DECISION)
    _require_equal("go_no_go.delegated_keep_pending_response_count", go_no_go.get("delegated_keep_pending_response_count"), 72)
    _require_equal("go_no_go.source_map_actionable_response_count", go_no_go.get("source_map_actionable_response_count"), 0)
    _require_false("go_no_go.source_map_correction_ready", go_no_go.get("source_map_correction_ready"))
    _require_false("go_no_go.raw_to_processed_value_comparison_performed", go_no_go.get("raw_to_processed_value_comparison_performed"))
    _require_false("go_no_go.full_raw_to_processed_value_comparison_complete", go_no_go.get("full_raw_to_processed_value_comparison_complete"))
    _require_false("go_no_go.business_value_consistency_verified", go_no_go.get("business_value_consistency_verified"))
    _require_false("go_no_go.github_upload_performed", go_no_go.get("github_upload_performed"))
    _require_false("go_no_go.app_reinstall_performed", go_no_go.get("app_reinstall_performed"))
    _require_false("go_no_go.business_execution_performed", go_no_go.get("business_execution_performed"))

    _require_equal("manifest.phase_id", manifest.get("phase_id"), PHASE_ID)
    _require_equal("manifest.task_id", manifest.get("task_id"), TASK_ID)
    _require_equal("manifest.acceptance_id", manifest.get("acceptance_id"), ACCEPTANCE_ID)
    _require_equal("manifest.decision", manifest.get("decision"), DECISION)
    _require_equal("manifest.summary", manifest.get("summary"), summary)
    _require_equal("manifest.go_no_go_report", manifest.get("go_no_go_report"), go_no_go)
    _require_equal("manifest.matrix", manifest.get("matrix"), matrix)
    _check_raw_boundary(manifest.get("raw_boundary", {}))
    _check_public_safety(manifest.get("public_safety", {}))


def _check_metadata_copies(summary: dict[str, Any], manifest: dict[str, Any], go_no_go: dict[str, Any], matrix: dict[str, Any]) -> None:
    _require_equal("metadata summary copy", _read_json(METADATA_SUMMARY_PATH), summary)
    _require_equal("metadata manifest copy", _read_json(METADATA_MANIFEST_PATH), manifest)
    _require_equal("metadata go/no-go copy", _read_json(METADATA_GO_NO_GO_PATH), go_no_go)
    _require_equal("metadata matrix copy", _read_json(METADATA_MATRIX_PATH), matrix)


def _check_private_response(summary: dict[str, Any]) -> None:
    for path in (PRIVATE_RESPONSE_RECORD_PATH, PRIVATE_RESPONSE_ITEMS_PATH, PRIVATE_DIAGNOSTIC_PATH):
        if not path.exists():
            raise ValidationError(f"missing private response artifact: {path}")
        _require_true(f"{path}.gitignored", _git_check_ignored(path))
        _require_equal(f"{path}.tracked", _git_output(["ls-files", "--", path.as_posix()]), "")
    record = _read_json(PRIVATE_RESPONSE_RECORD_PATH)
    diagnostic = _read_json(PRIVATE_DIAGNOSTIC_PATH)
    items = _read_jsonl(PRIVATE_RESPONSE_ITEMS_PATH)
    _require_equal("private.record.phase_id", record.get("phase_id"), PHASE_ID)
    _require_equal("private.diagnostic.phase_id", diagnostic.get("phase_id"), PHASE_ID)
    _require_equal("private.summary.intake count", record.get("summary_private", {}).get("intake_response_item_count"), 72)
    _require_equal("private.items length", len(items), 72)
    _require_equal("private.summary.keep_pending", record.get("summary_private", {}).get("delegated_keep_pending_response_count"), 72)
    _require_equal("private.summary.actionable", record.get("summary_private", {}).get("source_map_actionable_response_count"), 0)
    _check_raw_boundary(record.get("raw_boundary", {}))
    for item in items:
        _require_equal("private item selected decision", item.get("selected_review_decision_code"), "keep_pending")
        _require_equal("private item selected option", item.get("selected_private_candidate_option_index"), None)
        _require_equal("private item corrected ref", item.get("corrected_source_map_reference"), None)
        _require_false("private item.source_map_correction_ready", item.get("source_map_correction_ready"))
        _require_false("private item.candidate_selection", item.get("candidate_selection_performed_by_this_phase"))
        _require_false("private item.full_comparison_allowed", item.get("full_comparison_allowed_by_this_phase"))
    _require_equal("summary/private count", summary.get("intake_response_item_count"), len(items))


def validate(*, require_private_response: bool = False) -> dict[str, Any]:
    _check_public_artifacts()
    _check_no_raw_private_files_tracked()
    summary = _read_json(SUMMARY_PATH)
    manifest = _read_json(MANIFEST_PATH)
    go_no_go = _read_json(GO_NO_GO_PATH)
    matrix = _read_json(MATRIX_PATH)
    _check_summary(summary, matrix, go_no_go, manifest)
    _check_metadata_copies(summary, manifest, go_no_go, matrix)
    if require_private_response:
        _check_private_response(summary)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-private-response", action="store_true")
    args = parser.parse_args()
    try:
        manifest = validate(require_private_response=args.require_private_response)
    except ValidationError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    summary = manifest["summary"]
    print(
        "PASS: KMFA v0.1.4 outside-scope candidate review intake artifacts validated "
        f"(decision={summary['decision']}, keep_pending={summary['delegated_keep_pending_response_count']}, "
        f"source_map_actionable={summary['source_map_actionable_response_count']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
