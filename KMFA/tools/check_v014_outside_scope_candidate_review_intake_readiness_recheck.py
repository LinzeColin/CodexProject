#!/usr/bin/env python3
"""Validate KMFA v0.1.4 candidate review intake readiness recheck artifacts."""

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

from KMFA.tools.v014_outside_scope_candidate_review_intake_readiness_recheck import (  # noqa: E402
    ACCEPTANCE_ID,
    DECISION,
    DIAGNOSTIC_CONCLUSION,
    GO_NO_GO_PATH,
    GO_NO_GO_RECORD_PATH,
    MANIFEST_PATH,
    MATRIX_PATH,
    METADATA_GO_NO_GO_PATH,
    METADATA_MANIFEST_PATH,
    METADATA_MATRIX_PATH,
    METADATA_SUMMARY_PATH,
    NEXT_REQUIRED_INPUT,
    PHASE_ID,
    PRIVATE_DIAGNOSTIC_PATH,
    REPORT_PATH,
    RISK_REGISTER_PATH,
    ROLLBACK_PATH,
    SOURCE_PRIVATE_DIAGNOSTIC_PATH,
    SOURCE_PRIVATE_RESPONSE_ITEMS_PATH,
    SOURCE_PRIVATE_RESPONSE_RECORD_PATH,
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
        "source_public_intake_summary_read_by_this_phase",
        "source_private_delegated_response_record_read_by_this_phase",
        "source_private_delegated_response_items_read_by_this_phase",
        "source_private_delegated_response_diagnostic_read_by_this_phase",
        "private_readiness_diagnostic_written_by_this_phase",
    ):
        _require_true(f"raw_boundary.{key}", raw_boundary.get(key))
    for key, value in raw_boundary.items():
        if key.startswith("raw_inbox_") or key.endswith("_mutated_by_this_phase") or key == "source_map_correction_written_by_this_phase":
            _require_false(f"raw_boundary.{key}", value)


def _check_public_safety(public_safety: dict[str, Any]) -> None:
    _require_true("public_safety.public_safe_aggregate_only", public_safety.get("public_safe_aggregate_only"))
    for key, value in public_safety.items():
        if key != "public_safe_aggregate_only":
            _require_false(f"public_safety.{key}", value)


def _check_summary(summary: dict[str, Any], matrix: dict[str, Any], go_no_go: dict[str, Any], manifest: dict[str, Any]) -> None:
    _require_equal("summary.version", summary.get("version"), VERSION)
    _require_equal("summary.phase_id", summary.get("phase_id"), PHASE_ID)
    _require_equal("summary.task_id", summary.get("task_id"), TASK_ID)
    _require_equal("summary.acceptance_id", summary.get("acceptance_id"), ACCEPTANCE_ID)
    _require_equal("summary.status", summary.get("status"), STATUS)
    _require_equal("summary.decision", summary.get("decision"), DECISION)
    _require_equal("summary.diagnostic", summary.get("diagnostic_conclusion"), DIAGNOSTIC_CONCLUSION)
    _require_equal("summary.source_phase_id", summary.get("source_phase_id"), "V014_OUTSIDE_SCOPE_CANDIDATE_REVIEW_INTAKE_AFTER_PACKET")
    _require_equal("summary.source_intake_response_item_count", summary.get("source_intake_response_item_count"), 72)
    _require_equal("summary.source_delegated_decision_record_count", summary.get("source_delegated_decision_record_count"), 72)
    _require_equal("summary.source_delegated_keep_pending_response_count", summary.get("source_delegated_keep_pending_response_count"), 72)
    _require_equal("summary.delegated decisions", summary.get("delegated_decision_record_count"), 72)
    _require_equal("summary.keep pending", summary.get("delegated_keep_pending_response_count"), 72)
    _require_equal("summary.selected candidate", summary.get("selected_private_candidate_count"), 0)
    _require_equal("summary.corrected source map", summary.get("corrected_source_map_reference_count"), 0)
    _require_equal("summary.non numeric mapping", summary.get("authoritative_non_numeric_or_calculation_mapping_count"), 0)
    _require_equal("summary.actionable", summary.get("source_map_actionable_response_count"), 0)
    _require_true("summary.private count match", summary.get("private_record_summary_count_match"))
    _require_equal("summary.blocker observation", summary.get("review_intake_blocker_observation_count"), 1)
    _require_false("summary.blocked threshold", summary.get("review_intake_blocked_audit_threshold_met"))
    _require_equal("summary.goal status", summary.get("goal_status_recommendation"), "continue_waiting_for_actionable_source_map_response")
    for key in (
        "source_map_correction_ready",
        "source_map_correction_feasible_after_intake",
        "raw_to_processed_value_comparison_performed_by_this_phase",
        "full_raw_to_processed_value_comparison_ready",
        "full_raw_to_processed_value_comparison_complete",
        "full_reconciliation_allowed",
        "processed_consistency_verified",
        "business_value_consistency_verified",
        "lineage_full_check_complete",
        "formal_report_allowed",
        "github_upload_performed",
        "app_reinstall_performed",
        "business_execution_performed",
    ):
        _require_false(f"summary.{key}", summary.get(key))
    _require_true("summary.private diagnostic written", summary.get("private_readiness_diagnostic_written"))
    _require_true("summary.private diagnostic ignored", summary.get("private_readiness_diagnostic_gitignored"))
    _require_equal("summary.next_required_input", summary.get("next_required_input"), NEXT_REQUIRED_INPUT)
    _check_raw_boundary(summary.get("raw_boundary", {}))
    _check_public_safety(summary.get("public_safety", {}))

    _require_equal("matrix.phase_id", matrix.get("phase_id"), PHASE_ID)
    _require_equal("matrix.count", matrix.get("readiness_recheck_count"), 9)
    _require_equal("matrix.pass", matrix.get("readiness_recheck_pass_count"), 9)
    _require_equal("matrix.fail", matrix.get("readiness_recheck_fail_count"), 0)
    checks = {row.get("check_code"): row.get("status") for row in matrix.get("checks", []) if isinstance(row, dict)}
    for code in (
        "prior_phase_is_candidate_review_intake",
        "delegated_response_count_complete",
        "all_delegated_responses_keep_pending",
        "no_candidate_selection",
        "no_corrected_source_map_reference",
        "source_map_correction_not_ready",
        "review_intake_threshold_not_met",
        "raw_inbox_untouched",
        "downstream_gates_closed",
    ):
        _require_equal(f"matrix.{code}", checks.get(code), "PASS")

    _require_equal("go_no_go.phase_id", go_no_go.get("phase_id"), PHASE_ID)
    _require_equal("go_no_go.decision", go_no_go.get("decision"), DECISION)
    _require_equal("go_no_go.keep pending", go_no_go.get("delegated_keep_pending_response_count"), 72)
    _require_equal("go_no_go.actionable", go_no_go.get("source_map_actionable_response_count"), 0)
    _require_false("go_no_go.source map ready", go_no_go.get("source_map_correction_ready"))
    _require_false("go_no_go.raw comparison", go_no_go.get("raw_to_processed_value_comparison_allowed"))
    _require_false("go_no_go.business consistency", go_no_go.get("business_value_consistency_verified"))
    _require_false("go_no_go.github upload", go_no_go.get("github_upload_allowed"))
    _require_false("go_no_go.app reinstall", go_no_go.get("app_reinstall_allowed"))
    _require_false("go_no_go.business execution", go_no_go.get("business_execution_allowed"))

    _require_equal("manifest.summary", manifest.get("summary"), summary)
    _require_equal("manifest.matrix", manifest.get("matrix"), matrix)
    _require_equal("manifest.go_no_go", manifest.get("go_no_go_report"), go_no_go)
    _check_raw_boundary(manifest.get("raw_boundary", {}))
    _check_public_safety(manifest.get("public_safety", {}))


def _check_metadata_copies(summary: dict[str, Any], manifest: dict[str, Any], go_no_go: dict[str, Any], matrix: dict[str, Any]) -> None:
    _require_equal("metadata summary copy", _read_json(METADATA_SUMMARY_PATH), summary)
    _require_equal("metadata manifest copy", _read_json(METADATA_MANIFEST_PATH), manifest)
    _require_equal("metadata go/no-go copy", _read_json(METADATA_GO_NO_GO_PATH), go_no_go)
    _require_equal("metadata matrix copy", _read_json(METADATA_MATRIX_PATH), matrix)


def _check_private_diagnostic() -> None:
    for path in (
        SOURCE_PRIVATE_RESPONSE_RECORD_PATH,
        SOURCE_PRIVATE_RESPONSE_ITEMS_PATH,
        SOURCE_PRIVATE_DIAGNOSTIC_PATH,
        PRIVATE_DIAGNOSTIC_PATH,
    ):
        if not path.exists():
            raise ValidationError(f"missing private artifact: {path}")
        if not _git_check_ignored(path):
            raise ValidationError(f"private artifact is not gitignored: {path}")
        _require_equal(f"{path}.tracked", _git_output(["ls-files", "--", path.as_posix()]), "")
    items = _read_jsonl(SOURCE_PRIVATE_RESPONSE_ITEMS_PATH)
    diagnostic = _read_json(PRIVATE_DIAGNOSTIC_PATH)
    _require_equal("private items length", len(items), 72)
    _require_equal("private diagnostic phase", diagnostic.get("phase_id"), PHASE_ID)
    _require_equal("private diagnostic count", diagnostic.get("private_input_counts", {}).get("delegated_decision_record_count"), 72)
    _require_equal("private diagnostic keep pending", diagnostic.get("private_input_counts", {}).get("delegated_keep_pending_response_count"), 72)
    _require_equal("private diagnostic actionable", diagnostic.get("private_input_counts", {}).get("source_map_actionable_response_count"), 0)
    _require_false("private diagnostic ready", diagnostic.get("source_map_correction_ready"))
    for item in items:
        _require_equal("private item decision", item.get("selected_review_decision_code"), "keep_pending")
        _require_equal("private item selected option", item.get("selected_private_candidate_option_index"), None)
        _require_equal("private item corrected ref", item.get("corrected_source_map_reference"), None)
        _require_false("private item source map ready", item.get("source_map_correction_ready"))


def validate(*, require_private_diagnostic: bool = False) -> dict[str, Any]:
    _check_public_artifacts()
    _check_no_raw_private_files_tracked()
    summary = _read_json(SUMMARY_PATH)
    manifest = _read_json(MANIFEST_PATH)
    go_no_go = _read_json(GO_NO_GO_PATH)
    matrix = _read_json(MATRIX_PATH)
    _check_summary(summary, matrix, go_no_go, manifest)
    _check_metadata_copies(summary, manifest, go_no_go, matrix)
    if require_private_diagnostic:
        _check_private_diagnostic()
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-private-diagnostic", action="store_true")
    args = parser.parse_args()
    try:
        manifest = validate(require_private_diagnostic=args.require_private_diagnostic)
    except ValidationError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    summary = manifest["summary"]
    print(
        "PASS: KMFA v0.1.4 outside-scope candidate review intake readiness recheck artifacts validated "
        f"(decision={summary['decision']}, keep_pending={summary['delegated_keep_pending_response_count']}, "
        f"source_map_ready={summary['source_map_correction_ready']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
