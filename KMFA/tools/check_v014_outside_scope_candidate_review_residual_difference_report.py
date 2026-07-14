#!/usr/bin/env python3
"""Validate KMFA residual difference report artifacts."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.v014_outside_scope_candidate_review_residual_difference_report import (  # noqa: E402
    ACCEPTANCE_ID,
    DECISION,
    GO_NO_GO_PATH,
    GO_NO_GO_RECORD_PATH,
    MANIFEST_PATH,
    MATRIX_PATH,
    METADATA_GO_NO_GO_PATH,
    METADATA_MANIFEST_PATH,
    METADATA_MATRIX_PATH,
    METADATA_SUMMARY_PATH,
    NEXT_RECOMMENDED_PHASE,
    NEXT_REQUIRED_INPUT,
    PHASE_ID,
    PRIVATE_DIAGNOSTIC_PATH,
    PRIVATE_RESIDUAL_DIFFERENCE_QUEUE_PATH,
    PRIVATE_RESIDUAL_DIFFERENCE_REPORT_PATH,
    REPORT_PATH,
    REPORT_CONCLUSION,
    RISK_REGISTER_PATH,
    ROLLBACK_PATH,
    SOURCE_PRIVATE_RESIDUAL_QUEUE_PATH,
    SOURCE_PRIVATE_RESIDUAL_REPORT_PATH,
    STATUS,
    SUMMARY_PATH,
    TASK_ID,
    TEST_RESULTS_PATH,
    VERSION,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
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
        "source_public_closure_summary_read_by_this_phase",
        "source_public_closure_manifest_read_by_this_phase",
        "source_private_closure_blocker_queue_read_by_this_phase",
        "source_private_closure_workpack_existence_checked_by_this_phase",
        "source_public_blocker_audit_summary_read_by_this_phase",
        "source_public_blocker_audit_manifest_read_by_this_phase",
        "source_private_residual_queue_read_by_this_phase",
        "source_private_residual_report_existence_checked_by_this_phase",
        "private_residual_report_diagnostic_written_by_this_phase",
        "private_residual_difference_queue_written_by_this_phase",
        "private_residual_difference_report_written_by_this_phase",
    ):
        if key in raw_boundary:
            _require_true(f"raw_boundary.{key}", raw_boundary.get(key))
    for key, value in raw_boundary.items():
        if (
            key.startswith("raw_inbox_")
            or key.endswith("_mutated_by_this_phase")
            or key.endswith("_written_by_this_phase") and key in {"discrepancy_closure_written_by_this_phase", "source_map_correction_written_by_this_phase"}
            or key == "protected_source_identifier_derivation_performed_by_this_phase"
        ):
            _require_false(f"raw_boundary.{key}", value)


def _check_public_safety(public_safety: dict[str, Any]) -> None:
    _require_true("public_safety.public_safe_aggregate_only", public_safety.get("public_safe_aggregate_only"))
    for key, value in public_safety.items():
        if key == "public_safe_aggregate_only":
            continue
        _require_false(f"public_safety.{key}", value)


def _check_summary(summary: dict[str, Any], matrix: dict[str, Any], go_no_go: dict[str, Any], manifest: dict[str, Any]) -> None:
    _require_equal("summary.version", summary.get("version"), VERSION)
    _require_equal("summary.phase_id", summary.get("phase_id"), PHASE_ID)
    _require_equal("summary.task_id", summary.get("task_id"), TASK_ID)
    _require_equal("summary.acceptance_id", summary.get("acceptance_id"), ACCEPTANCE_ID)
    _require_equal("summary.status", summary.get("status"), STATUS)
    _require_equal("summary.decision", summary.get("decision"), DECISION)
    _require_equal("summary.report_conclusion", summary.get("report_conclusion"), REPORT_CONCLUSION)
    _require_equal(
        "summary.source_phase_id",
        summary.get("source_phase_id"),
        "V014_OUTSIDE_SCOPE_CANDIDATE_REVIEW_DISCREPANCY_CLOSURE_BLOCKER_AUDIT",
    )
    _require_equal("summary.source_open_closure_blocker_count", summary.get("source_open_closure_blocker_count"), 72)
    _require_equal("summary.source_closed_discrepancy_count", summary.get("source_closed_discrepancy_count"), 0)
    _require_equal("summary.source_newly_actionable_closure_count", summary.get("source_newly_actionable_closure_count"), 0)
    _require_equal("summary.source_safe_auto_closure_count", summary.get("source_safe_auto_closure_count"), 0)
    _require_true("summary.source_private_residual_queue_written", summary.get("source_private_residual_queue_written"))
    _require_true("summary.source_private_residual_report_written", summary.get("source_private_residual_report_written"))
    _require_true("summary.residual_report_performed", summary.get("residual_report_performed"))
    _require_equal("summary.source_private_residual_queue_item_count", summary.get("source_private_residual_queue_item_count"), 72)
    _require_equal("summary.residual_difference_report_item_count", summary.get("residual_difference_report_item_count"), 72)
    _require_equal("summary.open_residual_difference_count", summary.get("open_residual_difference_count"), 72)
    _require_equal("summary.closed_discrepancy_count", summary.get("closed_discrepancy_count"), 0)
    _require_equal("summary.safe_auto_closure_count", summary.get("safe_auto_closure_count"), 0)
    _require_equal("summary.newly_actionable_closure_count", summary.get("newly_actionable_closure_count"), 0)
    _require_equal("summary.public_residual_difference_bucket_count", summary.get("public_residual_difference_bucket_count"), 3)
    _require_equal("summary.ambiguous_selection_required_count", summary.get("ambiguous_selection_required_count"), 24)
    _require_equal(
        "summary.authoritative_source_reference_required_count",
        summary.get("authoritative_source_reference_required_count"),
        40,
    )
    _require_equal(
        "summary.formula_or_non_numeric_mapping_required_count",
        summary.get("formula_or_non_numeric_mapping_required_count"),
        8,
    )
    _require_equal("summary.unsupported_manual_triage_required_count", summary.get("unsupported_manual_triage_required_count"), 0)
    _require_equal(
        "summary.mandatory_owner_or_authorized_delegate_resolution_count",
        summary.get("mandatory_owner_or_authorized_delegate_resolution_count"),
        72,
    )
    _require_true("summary.residual_difference_report_prepared", summary.get("residual_difference_report_prepared"))
    _require_true("summary.private_diagnostic_handoff_ready", summary.get("private_diagnostic_handoff_ready"))
    _require_equal(
        "summary.goal_status_recommendation",
        summary.get("goal_status_recommendation"),
        "continue_with_private_diagnostic_handoff_or_owner_resolution",
    )
    for key in (
        "private_residual_report_diagnostic_written",
        "private_residual_difference_queue_written",
        "private_residual_difference_report_written",
        "private_residual_report_diagnostic_gitignored",
        "private_residual_difference_queue_gitignored",
        "private_residual_difference_report_gitignored",
    ):
        _require_true(f"summary.{key}", summary.get(key))
    for key in (
        "discrepancy_closure_complete",
        "source_map_correction_ready",
        "source_map_correction_written_by_this_phase",
        "raw_to_processed_value_comparison_performed_by_this_phase",
        "full_raw_to_processed_value_comparison_ready",
        "full_raw_to_processed_value_comparison_complete",
        "processed_consistency_verified",
        "business_value_consistency_verified",
        "full_reconciliation_allowed",
        "lineage_full_check_complete",
        "formal_report_allowed",
        "github_upload_performed",
        "app_reinstall_performed",
        "business_execution_performed",
    ):
        _require_false(f"summary.{key}", summary.get(key))
    _require_equal("summary.next_required_input", summary.get("next_required_input"), NEXT_REQUIRED_INPUT)
    _require_equal("summary.next_recommended_phase", summary.get("next_recommended_phase"), NEXT_RECOMMENDED_PHASE)
    _check_raw_boundary(summary.get("raw_boundary") or {})
    _check_public_safety(summary.get("public_safety") or {})

    _require_equal("matrix.phase_id", matrix.get("phase_id"), PHASE_ID)
    _require_equal("matrix.check_count", matrix.get("check_count"), 10)
    _require_equal("matrix.check_pass_count", matrix.get("check_pass_count"), 10)
    _require_equal("matrix.check_fail_count", matrix.get("check_fail_count"), 0)
    checks = {row.get("check_code"): row.get("status") for row in matrix.get("checks", []) if isinstance(row, dict)}
    for code in (
        "source_blocker_audit_summary_loaded",
        "source_open_closure_blocker_count_locked",
        "source_private_residual_queue_loaded",
        "private_residual_difference_report_written",
        "residual_difference_report_items_locked",
        "no_discrepancy_closed",
        "no_newly_actionable_closure",
        "residual_bucket_counts_locked",
        "raw_inbox_untouched",
        "downstream_gates_closed",
    ):
        _require_equal(f"matrix.{code}", checks.get(code), "PASS")

    _require_equal("go_no_go.phase_id", go_no_go.get("phase_id"), PHASE_ID)
    _require_equal("go_no_go.decision", go_no_go.get("decision"), DECISION)
    _require_equal("go_no_go.open_residual_difference_count", go_no_go.get("open_residual_difference_count"), 72)
    _require_equal("go_no_go.closed_discrepancy_count", go_no_go.get("closed_discrepancy_count"), 0)
    _require_false("go_no_go.discrepancy_closure_complete", go_no_go.get("discrepancy_closure_complete"))
    _require_false("go_no_go.source_map_correction_ready", go_no_go.get("source_map_correction_ready"))
    _require_false("go_no_go.raw comparison", go_no_go.get("raw_to_processed_value_comparison_allowed"))
    _require_false("go_no_go.business consistency", go_no_go.get("business_value_consistency_verified"))
    _require_false("go_no_go.github upload", go_no_go.get("github_upload_allowed"))
    _require_false("go_no_go.app reinstall", go_no_go.get("app_reinstall_allowed"))
    _require_false("go_no_go.business execution", go_no_go.get("business_execution_allowed"))
    _require_equal("go_no_go.next_required_input", go_no_go.get("next_required_input"), NEXT_REQUIRED_INPUT)
    _require_equal("manifest.summary", manifest.get("summary"), summary)
    _require_equal("manifest.matrix", manifest.get("matrix"), matrix)
    _require_equal("manifest.go_no_go", manifest.get("go_no_go_report"), go_no_go)


def _check_private_artifacts() -> None:
    for path in (
        SOURCE_PRIVATE_RESIDUAL_QUEUE_PATH,
        SOURCE_PRIVATE_RESIDUAL_REPORT_PATH,
        PRIVATE_DIAGNOSTIC_PATH,
        PRIVATE_RESIDUAL_DIFFERENCE_QUEUE_PATH,
        PRIVATE_RESIDUAL_DIFFERENCE_REPORT_PATH,
    ):
        if not path.exists():
            raise ValidationError(f"missing private artifact: {path}")
        if not _git_check_ignored(path):
            raise ValidationError(f"private artifact is not git-ignored: {path}")
    source_rows = _read_jsonl(SOURCE_PRIVATE_RESIDUAL_QUEUE_PATH)
    residual_rows = _read_jsonl(PRIVATE_RESIDUAL_DIFFERENCE_QUEUE_PATH)
    _require_equal("source private residual rows", len(source_rows), 72)
    _require_equal("private residual difference rows", len(residual_rows), 72)
    for item in residual_rows:
        _require_equal("private residual difference status", item.get("difference_status"), "unresolved_requires_private_diagnostic_or_owner_resolution")
        _require_true("private residual report ready", item.get("private_report_ready"))
        _require_false("private residual discrepancy closed", item.get("discrepancy_closed_by_this_phase"))
        _require_false("private residual source map ready", item.get("source_map_correction_ready_after_report"))
        _require_false(
            "private residual raw comparison ready",
            item.get("raw_to_processed_comparison_ready_after_report"),
        )


def validate(*, require_private_report: bool = False) -> dict[str, Any]:
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
    if require_private_report:
        _check_private_artifacts()
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-private-report", action="store_true")
    args = parser.parse_args()
    try:
        validate(require_private_report=args.require_private_report)
    except ValidationError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print("PASS: KMFA v0.1.4 residual difference report artifacts validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
