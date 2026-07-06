#!/usr/bin/env python3
"""Validate KMFA v0.1.4 owner 22-group decision response intake artifacts."""

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

from KMFA.tools.v014_processed_value_source_map_completion_owner_22_group_decision_response_intake import (  # noqa: E402
    AUTHORITY_BASIS,
    DECISION,
    DIAGNOSTIC_CONCLUSION,
    EXPECTED_DECISION_CODE_COUNTS,
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
    PRIVATE_FOLLOWUP_QUEUE_PATH,
    PRIVATE_RESPONSE_PATH,
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
    re.compile(r"\.(xlsx|xlsm|xls|zip|pdf)\b", re.IGNORECASE),
    re.compile(
        r'"(raw_file_name|archive_member_name|sheet_name|cell_address|raw_value|normalized_decimal|context_text|numeric_value_fingerprint|processed_value_fingerprint|value_fingerprint|sha256_private|target_slot_id|review_group_id|context_group)"',
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
    _require_true("raw_boundary.private_22_group_checklist_read_by_this_phase", raw_boundary.get("private_22_group_checklist_read_by_this_phase"))
    _require_true(
        "raw_boundary.private_22_group_response_template_read_by_this_phase",
        raw_boundary.get("private_22_group_response_template_read_by_this_phase"),
    )
    _require_true(
        "raw_boundary.private_22_group_decision_response_written_by_this_phase",
        raw_boundary.get("private_22_group_decision_response_written_by_this_phase"),
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


def _check_private_response(summary: dict[str, Any]) -> None:
    response = _read_json(PRIVATE_RESPONSE_PATH)
    diagnostic = _read_json(PRIVATE_DIAGNOSTIC_PATH)
    followup = _read_json(PRIVATE_FOLLOWUP_QUEUE_PATH)
    for label, payload in (("response", response), ("diagnostic", diagnostic), ("followup", followup)):
        _require_equal(f"{label}.phase_id", payload.get("phase_id"), PHASE_ID)
        _require_equal(f"{label}.task_id", payload.get("task_id"), TASK_ID)
        _require_equal(f"{label}.version", payload.get("version"), VERSION)

    _require_equal("response.group_count", response.get("group_count"), 22)
    _require_equal("response.response_row_count", response.get("response_row_count"), 113)
    _require_equal("response.application_blocker_queue_count", response.get("application_blocker_queue_count"), 113)
    _require_equal("response.linked_application_blocker_count", response.get("linked_application_blocker_count"), 77)
    _require_equal("response.unlinked_application_blocker_count", response.get("unlinked_application_blocker_count"), 36)
    _require_equal("response.decision_code_counts", response.get("decision_code_counts"), EXPECTED_DECISION_CODE_COUNTS)
    _require_equal("response.actionable_group_decision_count", response.get("actionable_group_decision_count"), 19)
    _require_equal("response.non_actionable_group_decision_count", response.get("non_actionable_group_decision_count"), 3)
    _require_equal("response.actionable_linked_application_blocker_count", response.get("actionable_linked_application_blocker_count"), 77)
    _require_equal("response.non_actionable_linked_application_blocker_count", response.get("non_actionable_linked_application_blocker_count"), 0)
    _require_true("response.owner_response_complete", response.get("owner_response_complete"))
    _require_true("response.all_group_decisions_valid", response.get("all_group_decisions_valid"))
    _require_false("response.resolution_application_allowed", response.get("resolution_application_allowed"))
    _require_false("response.full_reconciliation_allowed", response.get("full_reconciliation_allowed"))
    _require_equal("diagnostic.decision", diagnostic.get("decision"), DECISION)
    _require_equal("diagnostic.authority_basis", diagnostic.get("authority_basis"), AUTHORITY_BASIS)
    _check_raw_boundary(diagnostic.get("raw_boundary", {}))
    _require_equal("followup.non_actionable_group_decision_count", followup.get("non_actionable_group_decision_count"), 3)
    _require_equal("followup.unlinked_application_blocker_count", followup.get("unlinked_application_blocker_count"), 36)
    _require_true("followup.followup_required", followup.get("followup_required"))
    _require_equal("summary.private response count", summary.get("owner_22_group_count"), response.get("group_count"))
    for path in (PRIVATE_RESPONSE_PATH, PRIVATE_DIAGNOSTIC_PATH, PRIVATE_FOLLOWUP_QUEUE_PATH):
        if not path.exists():
            raise ValidationError(f"missing private artifact: {path}")
        _require_true(f"{path}.gitignored", _git_check_ignored(path))
        _require_equal(f"{path}.tracked", _git_output(["ls-files", path.as_posix()]), "")


def validate(*, require_private_response: bool = False) -> dict[str, Any]:
    summary = _read_json(SUMMARY_PATH)
    manifest = _read_json(MANIFEST_PATH)
    go_no_go = _read_json(GO_NO_GO_PATH)
    matrix = _read_json(MATRIX_PATH)
    metadata_summary = _read_json(METADATA_SUMMARY_PATH)
    metadata_manifest = _read_json(METADATA_MANIFEST_PATH)
    metadata_go_no_go = _read_json(METADATA_GO_NO_GO_PATH)
    metadata_matrix = _read_json(METADATA_MATRIX_PATH)

    _require_equal("summary.phase_id", summary.get("phase_id"), PHASE_ID)
    _require_equal("summary.task_id", summary.get("task_id"), TASK_ID)
    _require_equal("summary.version", summary.get("version"), VERSION)
    _require_equal("summary.status", summary.get("status"), STATUS)
    _require_equal("summary.decision", summary.get("decision"), DECISION)
    _require_equal("summary.diagnostic_conclusion", summary.get("diagnostic_conclusion"), DIAGNOSTIC_CONCLUSION)
    _require_equal("summary.authority_basis", summary.get("authority_basis"), AUTHORITY_BASIS)
    _require_equal("summary.source_22_group_checklist_decision", summary.get("source_22_group_checklist_decision"), "NO_GO")
    _require_true("summary.delegated_default_decision_applied_by_this_phase", summary.get("delegated_default_decision_applied_by_this_phase"))
    _require_true("summary.owner_22_group_response_intaken", summary.get("owner_22_group_response_intaken"))
    _require_equal("summary.owner_22_group_count", summary.get("owner_22_group_count"), 22)
    _require_equal("summary.owner_22_group_response_row_count", summary.get("owner_22_group_response_row_count"), 113)
    _require_equal("summary.application_blocker_queue_count", summary.get("application_blocker_queue_count"), 113)
    _require_equal("summary.linked_application_blocker_count", summary.get("linked_application_blocker_count"), 77)
    _require_equal("summary.unlinked_application_blocker_count", summary.get("unlinked_application_blocker_count"), 36)
    _require_equal("summary.actionable_linked_application_blocker_count", summary.get("actionable_linked_application_blocker_count"), 77)
    _require_equal("summary.non_actionable_linked_application_blocker_count", summary.get("non_actionable_linked_application_blocker_count"), 0)
    _require_equal("summary.decision_code_counts", summary.get("decision_code_counts"), EXPECTED_DECISION_CODE_COUNTS)
    _require_equal("summary.actionable_group_decision_count", summary.get("actionable_group_decision_count"), 19)
    _require_equal("summary.non_actionable_group_decision_count", summary.get("non_actionable_group_decision_count"), 3)
    _require_true("summary.owner_response_complete", summary.get("owner_response_complete"))
    _require_true("summary.all_group_decisions_valid", summary.get("all_group_decisions_valid"))
    for key in (
        "private_response_written",
        "private_response_gitignored",
        "private_diagnostic_written",
        "private_diagnostic_gitignored",
        "private_followup_queue_written",
        "private_followup_queue_gitignored",
    ):
        _require_true(f"summary.{key}", summary.get(key))
    for key in (
        "owner_group_decision_applied",
        "owner_22_group_partial_authorization_record_ready",
        "owner_22_group_partial_authorization_record_written",
        "resolution_application_allowed",
        "resolution_application_performed_by_this_phase",
        "source_map_mutation_performed_by_this_phase",
        "raw_to_processed_value_comparison_performed_by_this_phase",
        "full_reconciliation_allowed",
        "business_value_consistency_verified",
        "lineage_full_check_complete",
        "formal_report_allowed",
        "github_upload_performed",
        "app_reinstall_performed",
        "business_execution_performed",
    ):
        _require_false(f"summary.{key}", summary.get(key))
    _require_equal("summary.source_map_records_applied_count", summary.get("source_map_records_applied_count"), 0)
    _require_equal("summary.next_required_input", summary.get("next_required_input"), NEXT_REQUIRED_INPUT)

    _require_equal("matrix.phase_id", matrix.get("phase_id"), PHASE_ID)
    _require_equal("matrix.decision_check_count", matrix.get("decision_check_count"), 8)
    _require_equal("matrix.decision_pass_count", matrix.get("decision_pass_count"), 4)
    _require_equal("matrix.decision_fail_count", matrix.get("decision_fail_count"), 4)
    _require_true("matrix.owner_response_complete", matrix.get("owner_response_complete"))
    _require_true("matrix.all_group_decisions_valid", matrix.get("all_group_decisions_valid"))
    _require_false("matrix.resolution_application_allowed", matrix.get("resolution_application_allowed"))
    _require_false("matrix.full_reconciliation_allowed", matrix.get("full_reconciliation_allowed"))
    _require_equal("matrix.decision", matrix.get("decision"), DECISION)

    _require_equal("go_no_go.decision", go_no_go.get("decision"), DECISION)
    _require_equal("go_no_go.blocked_until", go_no_go.get("blocked_until"), NEXT_REQUIRED_INPUT)
    _require_equal("go_no_go.owner_22_group_count", go_no_go.get("owner_22_group_count"), 22)
    _require_equal("go_no_go.owner_22_group_response_row_count", go_no_go.get("owner_22_group_response_row_count"), 113)
    _require_equal("go_no_go.actionable_group_decision_count", go_no_go.get("actionable_group_decision_count"), 19)
    _require_equal("go_no_go.non_actionable_group_decision_count", go_no_go.get("non_actionable_group_decision_count"), 3)
    _require_equal("go_no_go.unlinked_application_blocker_count", go_no_go.get("unlinked_application_blocker_count"), 36)
    _require_true("go_no_go.owner_22_group_response_intaken", go_no_go.get("owner_22_group_response_intaken"))
    _require_false("go_no_go.resolution_application_allowed", go_no_go.get("resolution_application_allowed"))
    _require_false("go_no_go.full_reconciliation_allowed", go_no_go.get("full_reconciliation_allowed"))
    _require_false("go_no_go.business_value_consistency_verified", go_no_go.get("business_value_consistency_verified"))
    _require_false("go_no_go.github_upload_performed", go_no_go.get("github_upload_performed"))

    _require_equal("manifest.summary", manifest.get("summary"), summary)
    _require_equal("manifest.go_no_go", manifest.get("go_no_go"), go_no_go)
    _require_equal("manifest.decision_matrix", manifest.get("decision_matrix"), matrix)
    _require_equal("metadata_summary", metadata_summary, summary)
    _require_equal("metadata_manifest", metadata_manifest, manifest)
    _require_equal("metadata_go_no_go", metadata_go_no_go, go_no_go)
    _require_equal("metadata_matrix", metadata_matrix, matrix)

    _check_raw_boundary(summary.get("raw_boundary", {}))
    _check_public_safety(summary.get("public_safety", {}))
    _check_public_artifacts()
    _check_no_raw_private_files_tracked()
    if require_private_response:
        _check_private_response(summary)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-private-response", action="store_true")
    args = parser.parse_args()
    manifest = validate(require_private_response=args.require_private_response)
    print(
        "PASS: KMFA v0.1.4 owner 22-group decision response intake artifacts validated "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"groups={manifest['summary']['owner_22_group_count']}, "
        f"actionable={manifest['summary']['actionable_group_decision_count']}, "
        f"remaining_unlinked={manifest['summary']['unlinked_application_blocker_count']})"
    )


if __name__ == "__main__":
    main()
