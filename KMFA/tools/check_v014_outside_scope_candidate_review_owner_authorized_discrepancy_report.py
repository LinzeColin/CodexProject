#!/usr/bin/env python3
"""Validate KMFA owner-authorized discrepancy report artifacts."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PHASE_ID = "V014_OUTSIDE_SCOPE_CANDIDATE_REVIEW_OWNER_AUTHORIZED_DISCREPANCY_REPORT"
TASK_ID = "KMFA-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-OWNER-AUTHORIZED-DISCREPANCY-REPORT-20260707"
ACCEPTANCE_ID = "ACC-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-OWNER-AUTHORIZED-DISCREPANCY-REPORT"
VERSION = "0.1.4-outside-scope-candidate-review-owner-authorized-discrepancy-report"
STATUS = "completed_validated_local_only_owner_authorized_discrepancy_report_no_go"
DECISION = "NO_GO"
DIAGNOSTIC_CONCLUSION = "owner_authorized_auto_resolution_attempt_found_no_safe_exact_match_discrepancy_report_written"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "outside_scope_candidate_review_owner_authorized_discrepancy_report_summary.json"
MANIFEST_PATH = MACHINE_DIR / "outside_scope_candidate_review_owner_authorized_discrepancy_report_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "outside_scope_candidate_review_owner_authorized_discrepancy_report_go_no_go_report.json"
MATRIX_PATH = MACHINE_DIR / "outside_scope_candidate_review_owner_authorized_discrepancy_report_matrix_public_safe.json"
REPORT_PATH = HUMAN_DIR / "outside_scope_candidate_review_owner_authorized_discrepancy_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_outside_scope_candidate_review_owner_authorized_discrepancy_report_summary.json"
)
METADATA_MANIFEST_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_outside_scope_candidate_review_owner_authorized_discrepancy_report_manifest.json"
)
METADATA_GO_NO_GO_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_outside_scope_candidate_review_owner_authorized_discrepancy_report_go_no_go_report.json"
)
METADATA_MATRIX_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_outside_scope_candidate_review_owner_authorized_discrepancy_report_matrix_public_safe.json"
)

PRIVATE_OUTPUT_DIR = (
    PROJECT_ROOT / ".codex_private_runtime/v014_outside_scope_candidate_review_owner_authorized_discrepancy_report"
)
PRIVATE_RECORD_PATH = PRIVATE_OUTPUT_DIR / "private_owner_authorized_discrepancy_report_record.json"
PRIVATE_ITEMS_PATH = PRIVATE_OUTPUT_DIR / "private_owner_authorized_discrepancy_report_items.jsonl"
PRIVATE_QUEUE_PATH = PRIVATE_OUTPUT_DIR / "private_owner_authorized_discrepancy_queue.jsonl"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_owner_authorized_discrepancy_report_diagnostic.json"

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
    re.compile("-----BEGIN [A-Z ]*" + "PRIVATE" + " KEY-----"),
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
        "source_private_review_packet_read_by_this_phase",
        "source_private_alignment_diagnostic_read_by_this_phase",
        "private_discrepancy_report_written_by_this_phase",
        "private_discrepancy_queue_written_by_this_phase",
    ):
        _require_true(f"raw_boundary.{key}", raw_boundary.get(key))
    for key in (
        "source_private_review_packet_mutated_by_this_phase",
        "source_private_alignment_diagnostic_mutated_by_this_phase",
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
    _require_equal("summary.diagnostic_conclusion", summary.get("diagnostic_conclusion"), DIAGNOSTIC_CONCLUSION)
    _require_true(
        "summary.owner_latest_instruction_authorizes_auto_decision",
        summary.get("owner_latest_instruction_authorizes_auto_decision"),
    )
    _require_equal("summary.source_review_item_count", summary.get("source_review_item_count"), 72)
    _require_equal("summary.auto_ambiguous_item_count", summary.get("auto_ambiguous_item_count"), 24)
    _require_equal("summary.ambiguous_tied_candidate_item_count", summary.get("ambiguous_tied_candidate_item_count"), 24)
    _require_equal("summary.auto_unmatched_item_count", summary.get("auto_unmatched_item_count"), 40)
    _require_equal("summary.non_numeric_or_calculation_item_count", summary.get("non_numeric_or_calculation_item_count"), 8)
    _require_equal("summary.direct_exact_private_match_count", summary.get("direct_exact_private_match_count"), 0)
    _require_equal("summary.safe_auto_resolution_count", summary.get("safe_auto_resolution_count"), 0)
    _require_equal("summary.discrepancy_queue_item_count", summary.get("discrepancy_queue_item_count"), 72)
    _require_true("summary.discrepancy_report_written", summary.get("discrepancy_report_written"))
    _require_true("summary.all_review_items_classified", summary.get("all_review_items_classified"))
    for key in (
        "source_map_correction_ready",
        "raw_to_processed_value_comparison_performed_by_this_phase",
        "full_raw_to_processed_value_comparison_ready",
        "full_raw_to_processed_value_comparison_complete",
        "processed_consistency_verified",
        "business_value_consistency_verified",
        "github_upload_performed",
        "app_reinstall_performed",
        "business_execution_performed",
    ):
        _require_false(f"summary.{key}", summary.get(key))

    _check_raw_boundary(summary.get("raw_boundary") or {})
    _check_public_safety(summary.get("public_safety") or {})
    _require_equal("go_no_go.decision", go_no_go.get("decision"), DECISION)
    _require_false("go_no_go.raw_to_processed_value_comparison_allowed", go_no_go.get("raw_to_processed_value_comparison_allowed"))
    _require_equal("matrix.check_fail_count", matrix.get("check_fail_count"), 0)
    _require_equal("manifest.phase_id", manifest.get("phase_id"), PHASE_ID)
    _require_equal("manifest.summary.discrepancy_queue_item_count", manifest.get("summary", {}).get("discrepancy_queue_item_count"), 72)


def _check_private_artifacts() -> None:
    for path in (PRIVATE_RECORD_PATH, PRIVATE_ITEMS_PATH, PRIVATE_QUEUE_PATH, PRIVATE_DIAGNOSTIC_PATH):
        if not path.exists():
            raise ValidationError(f"missing private artifact: {path}")
        if not _git_check_ignored(path):
            raise ValidationError(f"private artifact is not git-ignored: {path}")
    items = _read_jsonl(PRIVATE_ITEMS_PATH)
    queue = _read_jsonl(PRIVATE_QUEUE_PATH)
    _require_equal("private items count", len(items), 72)
    _require_equal("private queue count", len(queue), 72)
    for item in items:
        _require_false("private item safe auto resolution", item.get("safe_auto_resolution_available"))
        _require_equal("private item selected option", item.get("selected_private_candidate_option_index"), None)
        _require_equal("private item corrected ref", item.get("corrected_source_map_reference"), None)
        _require_equal("private item source_map_correction_ready", item.get("source_map_correction_ready"), False)


def validate(*, require_private_discrepancy: bool = False) -> None:
    summary = _read_json(SUMMARY_PATH)
    manifest = _read_json(MANIFEST_PATH)
    go_no_go = _read_json(GO_NO_GO_PATH)
    matrix = _read_json(MATRIX_PATH)
    for metadata_path, source in (
        (METADATA_SUMMARY_PATH, summary),
        (METADATA_MANIFEST_PATH, manifest),
        (METADATA_GO_NO_GO_PATH, go_no_go),
        (METADATA_MATRIX_PATH, matrix),
    ):
        _require_equal(f"{metadata_path}.content", _read_json(metadata_path), source)
    _check_summary(summary, matrix, go_no_go, manifest)
    _check_public_artifacts()
    _check_no_raw_private_files_tracked()
    if require_private_discrepancy:
        _check_private_artifacts()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-private-discrepancy", action="store_true")
    args = parser.parse_args()
    try:
        validate(require_private_discrepancy=args.require_private_discrepancy)
    except ValidationError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print("PASS: KMFA v0.1.4 owner-authorized discrepancy report artifacts validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
