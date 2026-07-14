#!/usr/bin/env python3
"""Validate KMFA v0.1.4 delegated decision readiness recheck artifacts."""

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

from KMFA.tools.v014_outside_scope_authorized_source_map_extension_delegated_decision_readiness_recheck import (  # noqa: E402
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
    PRIOR_PRIVATE_DECISION_QUEUE_PATH,
    PRIOR_PRIVATE_DECISION_RECORD_PATH,
    PRIVATE_DIAGNOSTIC_PATH,
    REPORT_PATH,
    RISK_REGISTER_PATH,
    ROLLBACK_PATH,
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
    re.compile(
        r'"(target_slot_id|private_processed_ref_hash|record_ref_hash|target_key_ref_hash|processed_value_fingerprint|raw_file_name|archive_member_name|sheet_name|cell_address|raw_value|normalized_decimal|context_text|business_value|field_header)"',
        re.IGNORECASE,
    ),
    re.compile(r"sha256:[0-9a-f]{64}"),
    re.compile(r'"[0-9a-f]{64}"'),
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
        "raw_data_root_readonly_policy_active",
        "prior_private_delegated_decision_record_read_by_this_phase",
        "prior_private_delegated_decision_queue_read_by_this_phase",
        "prior_public_summary_read_by_this_phase",
        "private_readiness_diagnostic_written_by_this_phase",
    ):
        _require_true(f"raw_boundary.{key}", raw_boundary.get(key))
    for key, value in raw_boundary.items():
        if key.startswith("raw_inbox_") or key.endswith("_mutated_by_this_phase") or key == "source_map_extension_written_by_this_phase":
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
    _require_equal("summary.status", summary.get("status"), STATUS)
    _require_equal("summary.decision", summary.get("decision"), DECISION)
    _require_equal("summary.diagnostic", summary.get("diagnostic_conclusion"), DIAGNOSTIC_CONCLUSION)
    _require_equal("summary.prior phase", summary.get("prior_phase_id"), "V014_OUTSIDE_SCOPE_AUTHORIZED_SOURCE_MAP_EXTENSION_DELEGATED_KEEP_PENDING_DECISION")
    _require_true("summary.prior delegated default", summary.get("prior_delegated_default_decision_applied"))
    _require_true("summary.private record count match", summary.get("private_record_summary_count_match"))
    _require_equal("summary.prior exact source", summary.get("prior_exact_source_record_ref_match_count"), 0)
    _require_equal("summary.prior exact processed", summary.get("prior_exact_processed_ref_match_count"), 0)
    _require_equal("summary.prior valid", summary.get("prior_valid_authorized_extension_record_count"), 0)
    _require_equal("summary.blocker observation", summary.get("post_delegation_blocker_observation_count"), 1)
    _require_false("summary.blocked threshold", summary.get("post_delegation_blocked_audit_threshold_met"))
    _require_equal("summary.goal status", summary.get("goal_status_recommendation"), "continue_waiting_for_strong_authorized_evidence")
    _require_equal("summary.delegated decisions", summary.get("delegated_decision_record_count"), 72)
    _require_equal("summary.keep pending", summary.get("delegated_keep_pending_decision_count"), 72)
    _require_equal("summary.authorize count", summary.get("delegated_authorize_source_map_extension_count"), 0)
    _require_equal("summary.application allowed", summary.get("delegated_application_allowed_count"), 0)
    _require_equal("summary.valid", summary.get("valid_authorized_extension_record_count"), 0)
    _require_equal("summary.ready count", summary.get("source_map_extension_ready_count"), 0)
    _require_equal("summary.blocker count", summary.get("source_map_extension_blocker_count"), 72)
    for key in (
        "source_map_extension_application_ready",
        "source_map_extension_application_feasible_after_delegated_decision",
        "source_map_extension_written_by_this_phase",
        "raw_to_processed_value_comparison_performed_by_this_phase",
        "full_raw_to_processed_value_comparison_complete",
        "full_reconciliation_allowed",
        "processed_consistency_verified",
        "lineage_full_check_complete",
        "formal_report_allowed",
        "github_upload_performed",
        "app_reinstall_performed",
        "business_execution_performed",
    ):
        _require_false(f"summary.{key}", summary.get(key))
    _require_equal("summary.next_required_input", summary.get("next_required_input"), NEXT_REQUIRED_INPUT)
    _check_raw_boundary(summary["raw_boundary"])
    _check_public_safety(summary["public_safety"])
    _require_equal("matrix.phase_id", matrix.get("phase_id"), PHASE_ID)
    _require_equal("matrix.count", matrix.get("readiness_recheck_count"), 9)
    _require_equal("matrix.pass", matrix.get("readiness_recheck_pass_count"), 9)
    _require_equal("matrix.fail", matrix.get("readiness_recheck_fail_count"), 0)
    _require_equal("go_no_go.next_required_input", go_no_go.get("next_required_input"), NEXT_REQUIRED_INPUT)
    _require_false("go_no_go.application ready", go_no_go.get("source_map_extension_application_ready"))
    _require_equal("manifest.summary", manifest.get("summary"), summary)
    _require_equal("manifest.matrix", manifest.get("matrix"), matrix)
    _require_equal("manifest.go_no_go", manifest.get("go_no_go_report"), go_no_go)


def _check_private_diagnostic() -> None:
    for path in (PRIOR_PRIVATE_DECISION_RECORD_PATH, PRIOR_PRIVATE_DECISION_QUEUE_PATH, PRIVATE_DIAGNOSTIC_PATH):
        if not path.exists():
            raise ValidationError(f"missing private artifact: {path}")
        if not _git_check_ignored(path):
            raise ValidationError(f"private artifact is not gitignored: {path}")
    tracked = set(_git_output(["ls-files", "KMFA"]).splitlines())
    for path in (PRIOR_PRIVATE_DECISION_RECORD_PATH, PRIOR_PRIVATE_DECISION_QUEUE_PATH, PRIVATE_DIAGNOSTIC_PATH):
        if path.as_posix() in tracked:
            raise ValidationError(f"private artifact is tracked: {path}")
    queue = _read_jsonl(PRIOR_PRIVATE_DECISION_QUEUE_PATH)
    diagnostic = _read_json(PRIVATE_DIAGNOSTIC_PATH)
    _require_equal("private queue rows", len(queue), 72)
    _require_equal("private diagnostic phase", diagnostic.get("phase_id"), PHASE_ID)
    _require_equal("private diagnostic delegated count", diagnostic.get("private_input_counts", {}).get("delegated_decision_record_count"), 72)
    for row in queue:
        _require_equal("private queue decision", row.get("owner_decision_code"), "KEEP_PENDING")
        _require_false("private queue application", row.get("source_map_extension_application_allowed"))


def validate(*, require_private_diagnostic: bool = False) -> dict[str, Any]:
    _check_public_artifacts()
    _check_no_raw_private_files_tracked()
    summary = _read_json(SUMMARY_PATH)
    manifest = _read_json(MANIFEST_PATH)
    go_no_go = _read_json(GO_NO_GO_PATH)
    matrix = _read_json(MATRIX_PATH)
    _check_summary(summary, matrix, go_no_go, manifest)
    for metadata_path, expected in (
        (METADATA_SUMMARY_PATH, summary),
        (METADATA_MANIFEST_PATH, manifest),
        (METADATA_GO_NO_GO_PATH, go_no_go),
        (METADATA_MATRIX_PATH, matrix),
    ):
        _require_equal(metadata_path.as_posix(), _read_json(metadata_path), expected)
    if require_private_diagnostic:
        _check_private_diagnostic()
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-private-diagnostic", action="store_true")
    args = parser.parse_args()
    manifest = validate(require_private_diagnostic=args.require_private_diagnostic)
    summary = manifest["summary"]
    print(
        "PASS: KMFA v0.1.4 outside-scope delegated decision readiness recheck artifacts validated "
        f"(decision_records={summary['delegated_decision_record_count']}, "
        f"keep_pending={summary['delegated_keep_pending_decision_count']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
