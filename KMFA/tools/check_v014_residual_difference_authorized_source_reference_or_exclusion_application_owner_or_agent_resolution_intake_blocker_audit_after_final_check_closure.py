#!/usr/bin/env python3
"""Validate owner/authorized-agent resolution-intake blocker audit after final-check closure."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools import (  # noqa: E402
    v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_resolution_intake_after_final_check_closure
    as source_intake,
)
from KMFA.tools.v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_resolution_intake_blocker_audit_after_final_check_closure import (  # noqa: E402
    ACCEPTANCE_ID,
    AUDIT_CONCLUSION,
    DECISION,
    FORMULA_MAPPING_DIAGNOSTIC_KIND,
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
    PRIVATE_RESOLUTION_INTAKE_BLOCKER_AUDIT_DIAGNOSTIC_PATH,
    PRIVATE_RESOLUTION_INTAKE_BLOCKER_AUDIT_QUEUE_PATH,
    PRIVATE_RESOLUTION_INTAKE_BLOCKER_AUDIT_REPORT_PATH,
    REPORT_PATH,
    RISK_REGISTER_PATH,
    ROLLBACK_PATH,
    SOURCE_PRIVATE_RESOLUTION_INTAKE_DIAGNOSTIC_PATH,
    SOURCE_PRIVATE_RESOLUTION_INTAKE_QUEUE_PATH,
    SOURCE_PRIVATE_RESOLUTION_INTAKE_REPORT_PATH,
    SOURCE_REFERENCE_DIAGNOSTIC_KIND,
    STATUS,
    SUMMARY_PATH,
    TASK_ID,
    TEST_RESULTS_PATH,
    VERSION,
)


class ValidationError(RuntimeError):
    pass


PUBLIC_PATHS = (
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
)
PRIVATE_MARKERS = (
    re.compile(re.escape(".codex_private_runtime")),
    re.compile(re.escape("/Users/linzezhang/" + "Downloads")),
    re.compile(re.escape("KMFA" + "_MetaData")),
    re.compile(r"\.(xlsx|xlsm|xls|zip|pdf|sqlite|sqlite3|db)\b", re.IGNORECASE),
    re.compile(r"sha256:[0-9a-f]{64}"),
    re.compile(r'"[0-9a-f]{64}"'),
    re.compile(
        r'"(?:target_slot_id|raw_file_name|archive_member_name|sheet_name|cell_address|raw_value|'
        r"normalized_decimal|context_text|numeric_value_fingerprint|processed_value_fingerprint|"
        r'raw_candidate_fingerprint|value_fingerprint|raw_candidate_record_ref_hash|source_record_ref_hash)"',
        re.IGNORECASE,
    ),
    re.compile("s" + "k-" + r"[A-Za-z0-9_-]{20,}"),
    re.compile("A" + "KIA" + r"[0-9A-Z]{16}"),
    re.compile("BEGIN [A-Z ]*" + "PRIVATE" + " KEY"),
)


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValidationError(f"missing JSON artifact: {path}") from exc
    if not isinstance(value, dict):
        raise ValidationError(f"{path} must contain a JSON object")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    try:
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    except FileNotFoundError as exc:
        raise ValidationError(f"missing JSONL artifact: {path}") from exc
    if not all(isinstance(row, dict) for row in rows):
        raise ValidationError(f"{path} must contain JSON objects")
    return rows


def _require_equal(label: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        raise ValidationError(f"{label}: expected {expected!r}, got {actual!r}")


def _require_true(label: str, actual: Any) -> None:
    if actual is not True:
        raise ValidationError(f"{label}: expected True, got {actual!r}")


def _require_false(label: str, actual: Any) -> None:
    if actual is not False:
        raise ValidationError(f"{label}: expected False, got {actual!r}")


def _git_check_ignored(path: Path) -> bool:
    result = subprocess.run(["git", "check-ignore", "-q", path.as_posix()], check=False)
    return result.returncode == 0


def _git_is_tracked(path: Path) -> bool:
    result = subprocess.run(["git", "ls-files", "--error-unmatch", path.as_posix()], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result.returncode == 0


def _check_public_safety() -> None:
    for path in PUBLIC_PATHS:
        try:
            text = path.read_text(encoding="utf-8")
        except FileNotFoundError as exc:
            raise ValidationError(f"missing public artifact: {path}") from exc
        for pattern in PRIVATE_MARKERS:
            if pattern.search(text):
                raise ValidationError(f"public artifact contains private marker {pattern.pattern!r}: {path}")


def _validate_summary(summary: dict[str, Any]) -> None:
    _require_equal("summary.version", summary.get("version"), VERSION)
    _require_equal("summary.phase", summary.get("phase_id"), PHASE_ID)
    _require_equal("summary.task", summary.get("task_id"), TASK_ID)
    _require_equal("summary.acceptance", summary.get("acceptance_id"), ACCEPTANCE_ID)
    _require_equal("summary.status", summary.get("status"), STATUS)
    _require_equal("summary.decision", summary.get("decision"), DECISION)
    _require_equal("summary.audit", summary.get("audit_conclusion"), AUDIT_CONCLUSION)
    _require_equal("summary.source phase", summary.get("source_phase_id"), source_intake.PHASE_ID)
    _require_equal("summary.source manifest", summary.get("source_manifest_phase_id"), source_intake.PHASE_ID)
    _require_equal("summary.source decision", summary.get("source_go_no_go_decision"), "NO_GO")
    _require_equal("summary.source matrix", summary.get("source_matrix_check_fail_count"), 0)
    _require_equal("summary.source ready", summary.get("source_resolution_intake_ready_count"), 0)
    _require_equal("summary.source blocker", summary.get("source_resolution_intake_blocker_count"), 48)
    _require_equal("summary.source items", summary.get("source_resolution_intake_item_count"), 48)
    _require_equal("summary.source required", summary.get("source_resolution_intake_required_count"), 48)
    _require_equal("summary.source private queue", summary.get("source_private_resolution_intake_queue_item_count"), 48)
    _require_equal("summary.goal", summary.get("goal_status_recommendation"), "blocked")
    _require_equal("summary.prior observation", summary.get("prior_resolution_intake_blocker_observation_count"), 0)
    _require_equal("summary.observation", summary.get("resolution_intake_blocker_observation_count"), 1)
    _require_false("summary.threshold", summary.get("resolution_intake_blocker_audit_threshold_met"))
    _require_equal("summary.audit ready", summary.get("resolution_intake_blocker_audit_ready_count"), 0)
    _require_equal("summary.audit blocker", summary.get("resolution_intake_blocker_audit_blocker_count"), 48)
    _require_equal("summary.audit items", summary.get("resolution_intake_blocker_audit_item_count"), 48)
    _require_equal("summary.private audit queue", summary.get("private_audit_queue_item_count"), 48)
    _require_equal("summary.actionable owner resolution", summary.get("actionable_owner_resolution_count"), 0)
    _require_equal("summary.owner resolution", summary.get("owner_or_authorized_agent_resolution_count"), 0)
    _require_equal("summary.source ref audit", summary.get("source_reference_or_owner_exclusion_audit_blocker_count"), 40)
    _require_equal("summary.formula audit", summary.get("formula_or_non_numeric_mapping_audit_blocker_count"), 8)
    _require_equal("summary.binding ready count", summary.get("authoritative_binding_application_ready_count"), 0)
    _require_equal("summary.comparison ready count", summary.get("raw_to_processed_value_comparison_ready_count"), 0)
    _require_equal("summary.reconciliation ready count", summary.get("processed_data_reconciliation_ready_count"), 0)
    _require_equal("summary.business value ready count", summary.get("business_value_consistency_ready_count"), 0)
    _require_equal("summary.lineage ready count", summary.get("lineage_full_check_ready_count"), 0)
    _require_equal("summary.business execution ready count", summary.get("business_execution_ready_count"), 0)
    _require_equal("summary.unresolved", summary.get("unresolved_difference_count"), 72)
    _require_equal("summary.next required", summary.get("next_required_input"), NEXT_REQUIRED_INPUT)
    _require_equal("summary.next phase", summary.get("next_recommended_phase"), NEXT_RECOMMENDED_PHASE)
    for key in (
        "private_resolution_intake_blocker_audit_diagnostic_written",
        "private_resolution_intake_blocker_audit_queue_written",
        "private_resolution_intake_blocker_audit_report_written",
        "private_resolution_intake_blocker_audit_diagnostic_gitignored",
        "private_resolution_intake_blocker_audit_queue_gitignored",
        "private_resolution_intake_blocker_audit_report_gitignored",
        "source_private_resolution_intake_queue_gitignored",
        "resolution_intake_blocker_audit_checked_by_this_phase",
    ):
        _require_true(f"summary.{key}", summary.get(key))
    for key in (
        "owner_or_authorized_agent_resolution_completed_by_this_phase",
        "authoritative_binding_application_ready",
        "authoritative_binding_applied_by_this_phase",
        "raw_candidate_fingerprint_bound_by_this_phase",
        "raw_to_processed_value_comparison_ready",
        "raw_to_processed_value_comparison_performed_by_this_phase",
        "full_raw_to_processed_value_comparison_complete",
        "processed_data_reconciliation_ready",
        "processed_data_reconciliation_performed_by_this_phase",
        "business_value_consistency_ready",
        "business_value_consistency_verified",
        "lineage_full_check_ready",
        "lineage_full_check_complete",
        "github_upload_ready",
        "github_upload_allowed",
        "github_upload_performed",
        "app_reinstall_ready",
        "app_reinstall_allowed",
        "app_reinstall_performed",
        "business_execution_ready",
        "business_execution_allowed",
        "business_execution_performed",
    ):
        _require_false(f"summary.{key}", summary.get(key))
    boundary = summary.get("raw_boundary")
    if not isinstance(boundary, dict):
        raise ValidationError("summary.raw_boundary must be object")
    for key in (
        "source_resolution_intake_public_artifacts_read_by_this_phase",
        "source_private_resolution_intake_queue_read_by_this_phase",
        "private_resolution_intake_blocker_audit_queue_written_by_this_phase",
    ):
        _require_true(f"raw_boundary.{key}", boundary.get(key))
    for key in (
        "owner_or_authorized_agent_resolution_completed_by_this_phase",
        "business_execution_performed_by_this_phase",
        "raw_inbox_read_performed_by_this_phase",
        "raw_inbox_list_performed_by_this_phase",
        "raw_inbox_parse_performed_by_this_phase",
        "raw_inbox_mutated_by_this_phase",
    ):
        _require_false(f"raw_boundary.{key}", boundary.get(key))
    public_safety = summary.get("public_safety")
    if not isinstance(public_safety, dict):
        raise ValidationError("summary.public_safety must be object")
    _require_true("public_safety.public_safe_aggregate_only", public_safety.get("public_safe_aggregate_only"))


def _validate_matrix(matrix: dict[str, Any]) -> None:
    _require_equal("matrix.phase", matrix.get("phase_id"), PHASE_ID)
    _require_equal("matrix.decision", matrix.get("decision"), DECISION)
    _require_equal("matrix.check_count", matrix.get("check_count"), 12)
    _require_equal("matrix.check_fail_count", matrix.get("check_fail_count"), 0)
    checks = matrix.get("checks")
    if not isinstance(checks, list) or len(checks) != 12:
        raise ValidationError("matrix.checks must contain 12 rows")
    for row in checks:
        if row.get("status") != "PASS":
            raise ValidationError(f"matrix check did not pass: {row}")


def _validate_go_no_go(go_no_go: dict[str, Any]) -> None:
    _require_equal("go_no_go.phase", go_no_go.get("phase_id"), PHASE_ID)
    _require_equal("go_no_go.decision", go_no_go.get("decision"), DECISION)
    _require_equal("go_no_go.audit", go_no_go.get("audit_conclusion"), AUDIT_CONCLUSION)
    _require_equal("go_no_go.source blocker", go_no_go.get("source_resolution_intake_blocker_count"), 48)
    _require_equal("go_no_go.audit blocker", go_no_go.get("resolution_intake_blocker_audit_blocker_count"), 48)
    _require_equal("go_no_go.owner resolution", go_no_go.get("owner_or_authorized_agent_resolution_count"), 0)
    _require_false("go_no_go.github upload", go_no_go.get("github_upload_performed"))
    _require_false("go_no_go.app reinstall", go_no_go.get("app_reinstall_performed"))
    _require_false("go_no_go.business execution", go_no_go.get("business_execution_performed"))
    _require_equal("go_no_go.next", go_no_go.get("next_recommended_phase"), NEXT_RECOMMENDED_PHASE)


def _check_private_artifacts() -> None:
    private_paths = (
        PRIVATE_RESOLUTION_INTAKE_BLOCKER_AUDIT_DIAGNOSTIC_PATH,
        PRIVATE_RESOLUTION_INTAKE_BLOCKER_AUDIT_QUEUE_PATH,
        PRIVATE_RESOLUTION_INTAKE_BLOCKER_AUDIT_REPORT_PATH,
        SOURCE_PRIVATE_RESOLUTION_INTAKE_DIAGNOSTIC_PATH,
        SOURCE_PRIVATE_RESOLUTION_INTAKE_QUEUE_PATH,
        SOURCE_PRIVATE_RESOLUTION_INTAKE_REPORT_PATH,
    )
    for path in private_paths:
        if not path.exists():
            raise ValidationError(f"missing private artifact: {path}")
        if not _git_check_ignored(path):
            raise ValidationError(f"private artifact is not git-ignored: {path}")
        if _git_is_tracked(path):
            raise ValidationError(f"private artifact is tracked: {path}")
    diagnostic = _read_json(PRIVATE_RESOLUTION_INTAKE_BLOCKER_AUDIT_DIAGNOSTIC_PATH)
    audit_rows = _read_jsonl(PRIVATE_RESOLUTION_INTAKE_BLOCKER_AUDIT_QUEUE_PATH)
    report = PRIVATE_RESOLUTION_INTAKE_BLOCKER_AUDIT_REPORT_PATH.read_text(encoding="utf-8")
    _require_equal("private diagnostic phase", diagnostic.get("phase_id"), PHASE_ID)
    _require_equal("private rows", len(diagnostic.get("audit_queue") or []), 48)
    _require_equal("private row count", len(audit_rows), 48)
    if "owner/授权代理 resolution intake blocker audit 私有报告" not in report:
        raise ValidationError("private report missing Chinese heading")
    counts = Counter(row.get("diagnostic_kind") for row in audit_rows)
    _require_equal(f"private diagnostic kind {SOURCE_REFERENCE_DIAGNOSTIC_KIND}", counts[SOURCE_REFERENCE_DIAGNOSTIC_KIND], 40)
    _require_equal(f"private diagnostic kind {FORMULA_MAPPING_DIAGNOSTIC_KIND}", counts[FORMULA_MAPPING_DIAGNOSTIC_KIND], 8)
    for row in audit_rows:
        _require_equal("private audit status", row.get("resolution_intake_blocker_audit_status"), AUDIT_CONCLUSION)
        _require_false("private audit ready", row.get("resolution_intake_blocker_audit_ready"))
        _require_true("private audit blocker", row.get("resolution_intake_blocker_audit_blocker"))
        _require_equal("private observation", row.get("resolution_intake_blocker_observation_count"), 1)
        _require_false("private threshold", row.get("resolution_intake_blocker_audit_threshold_met"))
        _require_false(
            "private owner resolution completed",
            row.get("owner_or_authorized_agent_resolution_completed_by_this_phase"),
        )
        _require_false("private authoritative binding ready", row.get("authoritative_binding_application_ready"))
        _require_false("private comparison ready", row.get("raw_to_processed_value_comparison_ready"))
        _require_false("private reconciliation ready", row.get("processed_data_reconciliation_ready"))
        _require_false("private business value ready", row.get("business_value_consistency_ready"))
        _require_false("private lineage ready", row.get("lineage_full_check_ready"))
        _require_false("private github upload allowed", row.get("github_upload_allowed"))
        _require_false("private app reinstall allowed", row.get("app_reinstall_allowed"))
        _require_false("private business execution ready", row.get("business_execution_ready"))
        _require_false("private business execution allowed", row.get("business_execution_allowed"))
        _require_false("private business execution performed", row.get("business_execution_performed_by_this_phase"))
        _require_false("private public commit allowed", row.get("public_commit_allowed"))


def validate(*, require_private_audit: bool = False) -> dict[str, Any]:
    summary = _read_json(SUMMARY_PATH)
    manifest = _read_json(MANIFEST_PATH)
    go_no_go = _read_json(GO_NO_GO_PATH)
    matrix = _read_json(MATRIX_PATH)
    metadata_summary = _read_json(METADATA_SUMMARY_PATH)
    metadata_manifest = _read_json(METADATA_MANIFEST_PATH)
    metadata_go_no_go = _read_json(METADATA_GO_NO_GO_PATH)
    metadata_matrix = _read_json(METADATA_MATRIX_PATH)
    _require_equal("metadata summary", metadata_summary, summary)
    _require_equal("metadata manifest", metadata_manifest, manifest)
    _require_equal("metadata go_no_go", metadata_go_no_go, go_no_go)
    _require_equal("metadata matrix", metadata_matrix, matrix)
    _validate_summary(summary)
    _validate_matrix(matrix)
    _validate_go_no_go(go_no_go)
    _require_equal("manifest.phase", manifest.get("phase_id"), PHASE_ID)
    _require_equal("manifest.summary", manifest.get("summary"), summary)
    _require_equal("manifest.matrix", manifest.get("matrix"), matrix)
    _require_equal("manifest.go_no_go", manifest.get("go_no_go_report"), go_no_go)
    _check_public_safety()
    if require_private_audit:
        _check_private_artifacts()
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-private-audit", action="store_true", dest="require_private_audit")
    args = parser.parse_args(argv)
    manifest = validate(require_private_audit=args.require_private_audit)
    summary = manifest["summary"]
    print(
        "PASS: validated V014 owner/authorized-agent resolution-intake blocker audit after final-check closure "
        f"(observation={summary['resolution_intake_blocker_observation_count']}, "
        f"blockers={summary['resolution_intake_blocker_audit_blocker_count']}, "
        f"goal={summary['goal_status_recommendation']}, decision={summary['decision']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
