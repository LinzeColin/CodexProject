#!/usr/bin/env python3
"""Validate KMFA v0.1.4 outside-scope raw candidate alignment artifacts."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PHASE_ID = "V014_OUTSIDE_SCOPE_RAW_CANDIDATE_ALIGNMENT_AFTER_FULL_PRECHECK"
TASK_ID = "KMFA-V014-OUTSIDE-SCOPE-RAW-CANDIDATE-ALIGNMENT-AFTER-FULL-PRECHECK-20260707"
ACCEPTANCE_ID = "ACC-V014-OUTSIDE-SCOPE-RAW-CANDIDATE-ALIGNMENT-AFTER-FULL-PRECHECK"
VERSION = "0.1.4-outside-scope-raw-candidate-alignment-after-full-precheck"
STATUS = "completed_validated_local_only_outside_scope_raw_candidate_alignment_blocked_no_go"
DECISION = "NO_GO"
NEXT_REQUIRED_INPUT = "owner_or_authorized_delegate_reviews_private_outside_scope_candidate_alignment_before_full_comparison"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "outside_scope_raw_candidate_alignment_after_full_precheck_summary.json"
MANIFEST_PATH = MACHINE_DIR / "outside_scope_raw_candidate_alignment_after_full_precheck_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "outside_scope_raw_candidate_alignment_after_full_precheck_go_no_go_report.json"
MATRIX_PATH = MACHINE_DIR / "outside_scope_raw_candidate_alignment_after_full_precheck_matrix_public_safe.json"
REPORT_PATH = HUMAN_DIR / "outside_scope_raw_candidate_alignment_after_full_precheck_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_outside_scope_raw_candidate_alignment_after_full_precheck_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_outside_scope_raw_candidate_alignment_after_full_precheck_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_outside_scope_raw_candidate_alignment_after_full_precheck_go_no_go_report.json"
METADATA_MATRIX_PATH = PROJECT_ROOT / "metadata/quality/v014_outside_scope_raw_candidate_alignment_after_full_precheck_matrix_public_safe.json"

PRIVATE_OUTPUT_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_outside_scope_raw_candidate_alignment_after_full_precheck"
PRIVATE_ALIGNMENT_PATH = PRIVATE_OUTPUT_DIR / "private_outside_scope_raw_candidate_alignment.json"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_outside_scope_raw_candidate_alignment_diagnostic.json"
PRIVATE_ALIGNMENT_ITEMS_PATH = PRIVATE_OUTPUT_DIR / "private_outside_scope_raw_candidate_alignment_items.jsonl"
PRIVATE_QUESTION_LIST_PATH = PRIVATE_OUTPUT_DIR / "outside_scope_raw_candidate_alignment_questions_zh.md"

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

EXPECTED_CANDIDATE_STATUS_COUNTS = {
    "auto_ambiguous_multiple_candidates_requires_owner_review": 24,
    "auto_unmatched_requires_owner_review": 40,
    "requires_non_numeric_owner_mapping": 8,
}
EXPECTED_ALIGNMENT_STATUS_COUNTS = {
    "ambiguous_raw_candidates_require_owner_review": 24,
    "no_context_raw_candidate_requires_source_mapping_review": 40,
    "non_numeric_or_calculation_context_requires_manual_authority": 8,
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
        "user_authorized_raw_data_read_for_this_phase",
        "raw_data_root_readonly_policy_active",
        "raw_inbox_read_performed_by_this_phase",
        "raw_inbox_list_performed_by_this_phase",
        "raw_inbox_stat_performed_by_this_phase",
        "raw_inbox_hash_or_value_fingerprint_performed_by_this_phase",
        "raw_inbox_parse_performed_by_this_phase",
        "raw_inbox_field_or_header_read_performed_by_this_phase",
        "raw_inbox_value_extraction_performed_by_this_phase",
        "raw_root_stat_unchanged_after_phase",
    ):
        _require_true(f"raw_boundary.{key}", raw_boundary.get(key))
    for key in (
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
    _require_equal("summary.source_precheck_missing_candidate_count", summary.get("source_precheck_missing_candidate_count"), 72)
    _require_equal("summary.outside_scope_blocker_count", summary.get("outside_scope_blocker_count"), 72)
    _require_equal("summary.outside_scope_materialized_record_count", summary.get("outside_scope_materialized_record_count"), 72)
    _require_equal("summary.processed_staging_slot_count", summary.get("processed_staging_slot_count"), 149)
    _require_equal("summary.raw_root_file_count", summary.get("raw_root_file_count"), 5)
    _require_equal("summary.raw_archive_member_count", summary.get("raw_archive_member_count"), 18)
    _require_equal("summary.raw_archive_workbook_member_count", summary.get("raw_archive_workbook_member_count"), 5)
    _require_equal("summary.raw_archive_pdf_member_count", summary.get("raw_archive_pdf_member_count"), 7)
    _require_equal("summary.raw_openable_workbook_count", summary.get("raw_openable_workbook_count"), 1)
    _require_equal("summary.raw_openable_pdf_count", summary.get("raw_openable_pdf_count"), 7)
    _require_equal("summary.raw_workbook_parse_error_count", summary.get("raw_workbook_parse_error_count"), 3)
    _require_equal("summary.raw_pdf_parse_error_count", summary.get("raw_pdf_parse_error_count"), 0)
    _require_equal("summary.raw_numeric_candidate_count", summary.get("raw_numeric_candidate_count"), 351453)
    _require_equal("summary.raw_unique_numeric_fingerprint_count", summary.get("raw_unique_numeric_fingerprint_count"), 22453)
    _require_true("summary.raw_value_fingerprints_generated", summary.get("raw_value_fingerprints_generated"))
    _require_true("summary.raw_root_stat_unchanged_after_phase", summary.get("raw_root_stat_unchanged_after_phase"))
    _require_equal("summary.outside_scope_context_group_count", summary.get("outside_scope_context_group_count"), 10)
    _require_equal("summary.candidate_status_counts", summary.get("candidate_status_counts"), EXPECTED_CANDIDATE_STATUS_COUNTS)
    _require_equal("summary.alignment_status_counts", summary.get("alignment_status_counts"), EXPECTED_ALIGNMENT_STATUS_COUNTS)
    _require_equal("summary.direct_source_record_ref_match_count", summary.get("direct_source_record_ref_match_count"), 0)
    _require_equal("summary.direct_processed_fingerprint_match_count", summary.get("direct_processed_fingerprint_match_count"), 0)
    _require_equal(
        "summary.processed_replay_fingerprint_matches_private_processed_ref_hash_count",
        summary.get("processed_replay_fingerprint_matches_private_processed_ref_hash_count"),
        72,
    )
    _require_equal("summary.auto_unique_candidate_item_count", summary.get("auto_unique_candidate_item_count"), 0)
    _require_equal("summary.auto_ambiguous_candidate_item_count", summary.get("auto_ambiguous_candidate_item_count"), 24)
    _require_equal("summary.auto_unmatched_item_count", summary.get("auto_unmatched_item_count"), 40)
    _require_equal("summary.non_numeric_or_calculation_context_item_count", summary.get("non_numeric_or_calculation_context_item_count"), 8)
    _require_equal("summary.owner_review_required_item_count", summary.get("owner_review_required_item_count"), 72)
    _require_equal("summary.alignment_ready_count", summary.get("alignment_ready_count"), 0)
    for key in (
        "private_alignment_written",
        "private_alignment_gitignored",
        "private_alignment_items_written",
        "private_alignment_items_gitignored",
        "private_diagnostic_written",
        "private_diagnostic_gitignored",
        "private_question_list_written",
        "private_question_list_gitignored",
    ):
        _require_true(f"summary.{key}", summary.get(key))
    for key in (
        "source_map_correction_ready",
        "full_raw_to_processed_value_comparison_ready",
        "raw_to_processed_value_comparison_performed_by_this_phase",
        "full_raw_to_processed_value_comparison_complete",
        "business_value_consistency_verified",
    ):
        _require_false(f"summary.{key}", summary.get(key))
    _require_equal("summary.next_required_input", summary.get("next_required_input"), NEXT_REQUIRED_INPUT)
    _check_raw_boundary(summary.get("raw_boundary", {}))
    _check_public_safety(summary.get("public_safety", {}))

    _require_equal("matrix.phase_id", matrix.get("phase_id"), PHASE_ID)
    _require_equal("matrix.check_count", matrix.get("check_count"), 8)
    _require_equal("matrix.pass_count", matrix.get("pass_count"), 6)
    _require_equal("matrix.fail_count", matrix.get("fail_count"), 2)
    _require_equal("matrix.direct_source_record_ref_match_count", matrix.get("direct_source_record_ref_match_count"), 0)
    _require_equal("matrix.direct_processed_fingerprint_match_count", matrix.get("direct_processed_fingerprint_match_count"), 0)
    _require_equal("matrix.owner_review_required_item_count", matrix.get("owner_review_required_item_count"), 72)
    for key in (
        "full_raw_to_processed_value_comparison_ready",
        "full_raw_to_processed_value_comparison_complete",
        "business_value_consistency_verified",
    ):
        _require_false(f"matrix.{key}", matrix.get(key))
    check_statuses = {row.get("check_code"): row.get("status") for row in matrix.get("checks", []) if isinstance(row, dict)}
    _require_equal("matrix.direct_source_ref_coverage", check_statuses.get("direct_source_ref_coverage"), "FAIL")
    _require_equal("matrix.direct_processed_fingerprint_coverage", check_statuses.get("direct_processed_fingerprint_coverage"), "FAIL")

    _require_equal("go_no_go.phase_id", go_no_go.get("phase_id"), PHASE_ID)
    _require_equal("go_no_go.decision", go_no_go.get("decision"), DECISION)
    _require_equal("go_no_go.outside_scope_blocker_count", go_no_go.get("outside_scope_blocker_count"), 72)
    _require_equal("go_no_go.owner_review_required_item_count", go_no_go.get("owner_review_required_item_count"), 72)
    _require_false("go_no_go.full_raw_to_processed_value_comparison_ready", go_no_go.get("full_raw_to_processed_value_comparison_ready"))
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


def _check_private_alignment(summary: dict[str, Any]) -> None:
    for path in (PRIVATE_ALIGNMENT_PATH, PRIVATE_DIAGNOSTIC_PATH, PRIVATE_ALIGNMENT_ITEMS_PATH, PRIVATE_QUESTION_LIST_PATH):
        if not path.exists():
            raise ValidationError(f"missing private alignment artifact: {path}")
        _require_true(f"{path}.gitignored", _git_check_ignored(path))
        tracked = _git_output(["ls-files", "--", path.as_posix()])
        _require_equal(f"{path}.tracked", tracked, "")

    alignment = _read_json(PRIVATE_ALIGNMENT_PATH)
    diagnostic = _read_json(PRIVATE_DIAGNOSTIC_PATH)
    items = _read_jsonl(PRIVATE_ALIGNMENT_ITEMS_PATH)
    question_text = PRIVATE_QUESTION_LIST_PATH.read_text(encoding="utf-8")
    _require_equal("private.alignment.phase_id", alignment.get("phase_id"), PHASE_ID)
    _require_equal("private.diagnostic.phase_id", diagnostic.get("phase_id"), PHASE_ID)
    _require_equal("private.items length", len(items), 72)
    _require_equal("private.summary.outside_scope_blocker_count", alignment.get("summary_private", {}).get("outside_scope_blocker_count"), 72)
    _require_equal("private.summary.raw_numeric_candidate_count", alignment.get("summary_private", {}).get("raw_numeric_candidate_count"), 351453)
    _require_equal("private.summary.candidate_status_counts", alignment.get("summary_private", {}).get("candidate_status_counts"), EXPECTED_CANDIDATE_STATUS_COUNTS)
    _require_equal("private.summary.alignment_status_counts", alignment.get("summary_private", {}).get("alignment_status_counts"), EXPECTED_ALIGNMENT_STATUS_COUNTS)
    _require_equal("private.summary mirrors public owner count", alignment.get("summary_private", {}).get("owner_review_required_item_count"), summary.get("owner_review_required_item_count"))
    _require_equal("private.diagnostic.item count", len(diagnostic.get("alignment_items_requiring_owner_review", [])), 72)
    _check_raw_boundary(alignment.get("raw_boundary", {}))

    status_counts: dict[str, int] = {}
    for item in items:
        status = item.get("alignment_status")
        status_counts[status] = status_counts.get(status, 0) + 1
        _require_true("private item.owner_review_required", item.get("owner_review_required"))
        _require_false("private item.source_map_correction_ready", item.get("source_map_correction_ready"))
        _require_false("private item.full_comparison_allowed_by_this_phase", item.get("full_comparison_allowed_by_this_phase"))
    _require_equal("private alignment_status_counts", status_counts, EXPECTED_ALIGNMENT_STATUS_COUNTS)
    if "raw_file_name" not in question_text or "请确认" not in question_text:
        raise ValidationError("private question list does not contain expected private review prompts")


def validate(*, require_private_alignment: bool = False) -> dict[str, Any]:
    _check_public_artifacts()
    _check_no_raw_private_files_tracked()
    summary = _read_json(SUMMARY_PATH)
    manifest = _read_json(MANIFEST_PATH)
    go_no_go = _read_json(GO_NO_GO_PATH)
    matrix = _read_json(MATRIX_PATH)
    _check_summary(summary, matrix, go_no_go, manifest)
    _check_metadata_copies(summary, manifest, go_no_go, matrix)
    if require_private_alignment:
        _check_private_alignment(summary)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-private-alignment", action="store_true")
    args = parser.parse_args()
    try:
        manifest = validate(require_private_alignment=args.require_private_alignment)
    except ValidationError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    summary = manifest["summary"]
    print(
        "PASS: KMFA v0.1.4 outside-scope raw candidate alignment artifacts validated "
        f"(decision={summary['decision']}, blockers={summary['outside_scope_blocker_count']}, "
        f"owner_review_required={summary['owner_review_required_item_count']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
