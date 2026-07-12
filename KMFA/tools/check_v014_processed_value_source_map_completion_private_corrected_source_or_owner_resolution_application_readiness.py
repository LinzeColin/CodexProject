#!/usr/bin/env python3
"""Validate KMFA v0.1.4 owner-resolution application-readiness artifacts."""

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

from KMFA.tools.v014_processed_value_source_map_completion_private_corrected_source_or_owner_resolution_application_readiness import (  # noqa: E402
    DECISION,
    DIAGNOSTIC_CONCLUSION,
    GO_NO_GO_PATH,
    GO_NO_GO_RECORD_PATH,
    MANIFEST_PATH,
    METADATA_GO_NO_GO_PATH,
    METADATA_MANIFEST_PATH,
    METADATA_READINESS_MATRIX_PATH,
    METADATA_SUMMARY_PATH,
    NEXT_REQUIRED_INPUT,
    PHASE_ID,
    PRIVATE_BLOCKER_QUEUE_PATH,
    PRIVATE_DIAGNOSTIC_PATH,
    PRIVATE_REPORT_PATH,
    READINESS_MATRIX_PATH,
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
    READINESS_MATRIX_PATH,
    REPORT_PATH,
    GO_NO_GO_RECORD_PATH,
    TEST_RESULTS_PATH,
    RISK_REGISTER_PATH,
    ROLLBACK_PATH,
    METADATA_SUMMARY_PATH,
    METADATA_MANIFEST_PATH,
    METADATA_GO_NO_GO_PATH,
    METADATA_READINESS_MATRIX_PATH,
]
FORBIDDEN_PUBLIC_PATTERNS = [
    re.compile(re.escape(RAW_DOWNLOADS_MARKER)),
    re.compile(re.escape(RAW_INBOX_MARKER)),
    re.compile(r"\.(xlsx|xlsm|xls|zip|pdf)\b", re.IGNORECASE),
    re.compile(
        r'"(raw_file_name|archive_member_name|sheet_name|cell_address|raw_value|normalized_decimal|context_text|numeric_value_fingerprint|processed_value_fingerprint|value_fingerprint|sha256_private|target_slot_id|review_group_id)"',
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
    _require_true("raw_boundary.raw_data_root_readonly_policy_active", raw_boundary.get("raw_data_root_readonly_policy_active"))
    _require_true("raw_boundary.private_intake_summary_read_by_this_phase", raw_boundary.get("private_intake_summary_read_by_this_phase"))
    _require_true("raw_boundary.private_intake_template_read_by_this_phase", raw_boundary.get("private_intake_template_read_by_this_phase"))
    _require_true("raw_boundary.private_pending_queue_read_by_this_phase", raw_boundary.get("private_pending_queue_read_by_this_phase"))
    _require_true(
        "raw_boundary.private_application_readiness_diagnostic_written_by_this_phase",
        raw_boundary.get("private_application_readiness_diagnostic_written_by_this_phase"),
    )
    for key in (
        "raw_inbox_read_performed_by_this_phase",
        "raw_inbox_list_performed_by_this_phase",
        "raw_inbox_stat_performed_by_this_phase",
        "raw_inbox_hash_or_value_fingerprint_performed_by_this_phase",
        "raw_inbox_file_content_hash_performed_by_this_phase",
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


def _check_private_diagnostic(summary: dict[str, Any]) -> None:
    diagnostic = _read_json(PRIVATE_DIAGNOSTIC_PATH)
    blocker_queue = _read_jsonl(PRIVATE_BLOCKER_QUEUE_PATH)
    private_report = PRIVATE_REPORT_PATH.read_text(encoding="utf-8") if PRIVATE_REPORT_PATH.exists() else ""
    _require_equal("private diagnostic.phase_id", diagnostic.get("phase_id"), PHASE_ID)
    _require_equal("private diagnostic.task_id", diagnostic.get("task_id"), TASK_ID)
    _require_equal("private diagnostic.decision", diagnostic.get("decision"), DECISION)
    _require_equal("private diagnostic.private_pending_queue_count", diagnostic.get("private_pending_queue_count"), 113)
    _require_equal("private diagnostic.blocker count", diagnostic.get("application_blocker_queue_count"), 113)
    _require_equal("private blocker queue length", len(blocker_queue), 113)
    _require_equal("summary.blocker queue count", summary.get("application_blocker_queue_count"), len(blocker_queue))
    _require_false("private diagnostic.application ready", diagnostic.get("resolution_application_ready"))
    _require_false("private diagnostic.application allowed", diagnostic.get("resolution_application_allowed"))
    _require_false("private diagnostic.raw inbox accessed", diagnostic.get("raw_inbox_accessed"))
    if RAW_DOWNLOADS_MARKER in private_report or RAW_INBOX_MARKER in private_report:
        raise ValidationError("private report unexpectedly contains raw inbox markers")
    for path in (PRIVATE_DIAGNOSTIC_PATH, PRIVATE_BLOCKER_QUEUE_PATH, PRIVATE_REPORT_PATH):
        if not path.exists():
            raise ValidationError(f"missing private artifact: {path}")
        _require_true(f"{path}.gitignored", _git_check_ignored(path))
        _require_equal(f"{path}.tracked", _git_output(["ls-files", path.as_posix()]), "")


def validate(*, require_private_diagnostic: bool = False) -> dict[str, Any]:
    summary = _read_json(SUMMARY_PATH)
    manifest = _read_json(MANIFEST_PATH)
    go_no_go = _read_json(GO_NO_GO_PATH)
    matrix = _read_json(READINESS_MATRIX_PATH)
    metadata_summary = _read_json(METADATA_SUMMARY_PATH)
    metadata_manifest = _read_json(METADATA_MANIFEST_PATH)
    metadata_go_no_go = _read_json(METADATA_GO_NO_GO_PATH)
    metadata_matrix = _read_json(METADATA_READINESS_MATRIX_PATH)

    _require_equal("summary.phase_id", summary.get("phase_id"), PHASE_ID)
    _require_equal("summary.task_id", summary.get("task_id"), TASK_ID)
    _require_equal("summary.version", summary.get("version"), VERSION)
    _require_equal("summary.status", summary.get("status"), STATUS)
    _require_equal("summary.decision", summary.get("decision"), DECISION)
    _require_equal("summary.diagnostic_conclusion", summary.get("diagnostic_conclusion"), DIAGNOSTIC_CONCLUSION)
    _require_equal("summary.source_decision", summary.get("source_decision"), DECISION)
    _require_false("summary.source owner input", summary.get("source_owner_approved_resolution_input_present"))
    _require_false("summary.source corrected package", summary.get("source_corrected_private_source_package_present"))
    _require_false("summary.source application allowed", summary.get("source_resolution_application_allowed"))
    _require_false("summary.previous_required_input_resolved_by_this_phase", summary.get("previous_required_input_resolved_by_this_phase"))
    _require_false("summary.owner_approved_resolution_input_present", summary.get("owner_approved_resolution_input_present"))
    _require_false("summary.corrected_private_source_package_present", summary.get("corrected_private_source_package_present"))
    _require_equal("summary.template_track_count", summary.get("template_track_count"), 5)
    _require_equal("summary.private_pending_queue_count", summary.get("private_pending_queue_count"), 113)
    _require_equal("summary.missing_owner_input_count", summary.get("missing_owner_input_count"), 113)
    _require_equal("summary.valid_owner_input_count", summary.get("valid_owner_input_count"), 0)
    _require_equal("summary.resolution_application_allowed_row_count", summary.get("resolution_application_allowed_row_count"), 0)
    _require_equal("summary.full_reconciliation_allowed_row_count", summary.get("full_reconciliation_allowed_row_count"), 0)
    _require_equal("summary.application_blocker_queue_count", summary.get("application_blocker_queue_count"), 113)
    _require_false("summary.resolution_application_ready", summary.get("resolution_application_ready"))
    _require_false("summary.resolution_application_allowed", summary.get("resolution_application_allowed"))
    _require_false("summary.resolution_application_performed_by_this_phase", summary.get("resolution_application_performed_by_this_phase"))
    _require_false("summary.source_map_mutation_performed_by_this_phase", summary.get("source_map_mutation_performed_by_this_phase"))
    _require_equal("summary.source_map_records_applied_count", summary.get("source_map_records_applied_count"), 0)
    _require_false("summary.full_reconciliation_allowed", summary.get("full_reconciliation_allowed"))
    _require_false("summary.business_value_consistency_verified", summary.get("business_value_consistency_verified"))
    _require_false("summary.github_upload_performed", summary.get("github_upload_performed"))
    _require_false("summary.app_reinstall_performed", summary.get("app_reinstall_performed"))
    _require_false("summary.business_execution_performed", summary.get("business_execution_performed"))
    _require_equal("summary.next_required_input", summary.get("next_required_input"), NEXT_REQUIRED_INPUT)
    _require_true("summary.private_diagnostic_written", summary.get("private_diagnostic_written"))
    _require_true("summary.private_application_blocker_queue_written", summary.get("private_application_blocker_queue_written"))
    _require_true("summary.private_diagnostic_gitignored", summary.get("private_diagnostic_gitignored"))
    _require_true("summary.private_application_blocker_queue_gitignored", summary.get("private_application_blocker_queue_gitignored"))

    _require_equal("matrix.phase_id", matrix.get("phase_id"), PHASE_ID)
    _require_equal("matrix.application_readiness_check_count", matrix.get("application_readiness_check_count"), 7)
    _require_equal("matrix.application_readiness_pass_count", matrix.get("application_readiness_pass_count"), 1)
    _require_equal("matrix.application_readiness_fail_count", matrix.get("application_readiness_fail_count"), 6)
    _require_false("matrix.resolution_application_ready", matrix.get("resolution_application_ready"))
    _require_false("matrix.resolution_application_allowed", matrix.get("resolution_application_allowed"))
    _require_false("matrix.full_reconciliation_allowed_after_application", matrix.get("full_reconciliation_allowed_after_application"))
    _require_equal("matrix.decision", matrix.get("decision"), DECISION)

    _require_equal("go_no_go.decision", go_no_go.get("decision"), DECISION)
    _require_equal("go_no_go.blocked_until", go_no_go.get("blocked_until"), NEXT_REQUIRED_INPUT)
    _require_equal("go_no_go.missing_owner_input_count", go_no_go.get("missing_owner_input_count"), 113)
    _require_false("go_no_go.resolution_application_ready", go_no_go.get("resolution_application_ready"))
    _require_false("go_no_go.resolution_application_performed", go_no_go.get("resolution_application_performed"))
    _require_false("go_no_go.full_reconciliation_allowed", go_no_go.get("full_reconciliation_allowed"))
    _require_false("go_no_go.business_value_consistency_verified", go_no_go.get("business_value_consistency_verified"))
    _require_false("go_no_go.github_upload_performed", go_no_go.get("github_upload_performed"))

    _require_equal("manifest.summary", manifest.get("summary"), summary)
    _require_equal("manifest.go_no_go", manifest.get("go_no_go"), go_no_go)
    _require_equal("manifest.readiness_matrix", manifest.get("readiness_matrix"), matrix)
    _require_equal("metadata_summary", metadata_summary, summary)
    _require_equal("metadata_manifest", metadata_manifest, manifest)
    _require_equal("metadata_go_no_go", metadata_go_no_go, go_no_go)
    _require_equal("metadata_matrix", metadata_matrix, matrix)

    _check_raw_boundary(summary.get("raw_boundary", {}))
    _check_public_safety(summary.get("public_safety", {}))
    _check_public_artifacts()
    _check_no_raw_private_files_tracked()
    if require_private_diagnostic:
        _check_private_diagnostic(summary)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-private-diagnostic", action="store_true")
    args = parser.parse_args()
    manifest = validate(require_private_diagnostic=args.require_private_diagnostic)
    print(
        "PASS: KMFA v0.1.4 private corrected-source owner-resolution application readiness artifacts validated "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"missing_owner_input={manifest['summary']['missing_owner_input_count']}, "
        f"ready={manifest['summary']['resolution_application_ready']})"
    )


if __name__ == "__main__":
    main()
