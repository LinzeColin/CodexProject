#!/usr/bin/env python3
"""Validate external-action final-threshold recheck after reminder."""

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

from KMFA.tools import (  # noqa: E402
    v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_external_action_blocked_handoff_after_external_action_readiness
    as source_handoff,
)
from KMFA.tools.v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_external_action_blocked_handoff_final_threshold_recheck_after_reminder import (  # noqa: E402
    ACCEPTANCE_ID,
    DECISION,
    FINAL_THRESHOLD_CONCLUSION,
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
    PRIVATE_EXTERNAL_ACTION_FINAL_THRESHOLD_DIAGNOSTIC_PATH,
    PRIVATE_EXTERNAL_ACTION_FINAL_THRESHOLD_RECORDS_PATH,
    PRIVATE_EXTERNAL_ACTION_FINAL_THRESHOLD_REPORT_PATH,
    PROJECT_ROOT,
    REPORT_PATH,
    RISK_REGISTER_PATH,
    ROLLBACK_PATH,
    SOURCE_PRIVATE_EXTERNAL_ACTION_BLOCKED_HANDOFF_DIAGNOSTIC_PATH,
    SOURCE_PRIVATE_EXTERNAL_ACTION_BLOCKED_HANDOFF_RECORDS_PATH,
    SOURCE_PRIVATE_OWNER_ACTION_REMINDER_QUEUE_PATH,
    SOURCE_PRIVATE_OWNER_ACTION_REMINDER_REPORT_PATH,
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
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
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


def _git_output(args: list[str], *, check: bool = True) -> str:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        cwd=PROJECT_ROOT.parent,
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout.strip()


def _git_check_ignored(path: Path) -> bool:
    return subprocess.run(["git", "check-ignore", "-q", path.as_posix()], cwd=PROJECT_ROOT.parent).returncode == 0


def _git_is_tracked(path: Path) -> bool:
    return (
        subprocess.run(
            ["git", "ls-files", "--error-unmatch", path.as_posix()],
            cwd=PROJECT_ROOT.parent,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        ).returncode
        == 0
    )


def _check_public_artifacts() -> None:
    for path in PUBLIC_PATHS:
        if not path.exists():
            raise ValidationError(f"missing public artifact: {path}")
        text = path.read_text(encoding="utf-8")
        for pattern in PRIVATE_MARKERS:
            if pattern.search(text):
                raise ValidationError(f"public artifact contains private marker {pattern.pattern}: {path}")


def _check_no_raw_private_files_tracked() -> None:
    tracked = _git_output(["ls-files", "KMFA"], check=True).splitlines()
    raw_private_pattern = re.compile(
        r"\.codex_private_runtime|"
        r"KMFA" + r"_MetaData|"
        r"/Downloads/|"
        r"\.(zip|xlsx|xlsm|xls|pdf|sqlite|sqlite3|db|key|pem|p12|pfx)$",
        re.IGNORECASE,
    )
    hits = [path for path in tracked if raw_private_pattern.search(path)]
    if hits:
        raise ValidationError("tracked raw/private files detected: " + ", ".join(hits[:20]))


def _check_raw_boundary(raw_boundary: dict[str, Any]) -> None:
    true_keys = (
        "user_declared_raw_data_immutable",
        "raw_data_root_readonly_policy_active",
        "source_external_action_blocked_handoff_public_artifacts_read_by_this_phase",
        "source_external_action_blocked_handoff_manifest_read_by_this_phase",
        "source_external_action_blocked_handoff_go_no_go_read_by_this_phase",
        "source_external_action_blocked_handoff_matrix_read_by_this_phase",
        "source_private_external_action_blocked_handoff_diagnostic_read_by_this_phase",
        "source_private_external_action_blocked_handoff_records_read_by_this_phase",
        "source_private_owner_action_reminder_queue_read_by_this_phase",
        "source_private_owner_action_reminder_report_existence_checked_by_this_phase",
        "private_external_action_final_threshold_diagnostic_written_by_this_phase",
        "private_external_action_final_threshold_records_written_by_this_phase",
        "private_external_action_final_threshold_report_written_by_this_phase",
    )
    false_keys = (
        "source_private_external_action_blocked_handoff_diagnostic_mutated_by_this_phase",
        "source_private_external_action_blocked_handoff_records_mutated_by_this_phase",
        "source_private_owner_action_reminder_queue_mutated_by_this_phase",
        "source_private_owner_action_reminder_report_mutated_by_this_phase",
        "owner_or_agent_external_action_completed_by_this_phase",
        "authoritative_binding_applied_by_this_phase",
        "raw_candidate_fingerprint_bound_by_this_phase",
        "raw_to_processed_value_comparison_performed_by_this_phase",
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
    )
    for key in true_keys:
        _require_true(f"raw_boundary.{key}", raw_boundary.get(key))
    for key in false_keys:
        _require_false(f"raw_boundary.{key}", raw_boundary.get(key))


def _check_public_safety(public_safety: dict[str, Any]) -> None:
    _require_true("public_safety.public_safe_aggregate_only", public_safety.get("public_safe_aggregate_only"))
    for key, value in public_safety.items():
        if key == "public_safe_aggregate_only":
            continue
        _require_false(f"public_safety.{key}", value)


def _check_summary(
    summary: dict[str, Any],
    matrix: dict[str, Any],
    go_no_go: dict[str, Any],
    manifest: dict[str, Any],
) -> None:
    _require_equal("summary.version", summary.get("version"), VERSION)
    _require_equal("summary.phase_id", summary.get("phase_id"), PHASE_ID)
    _require_equal("summary.task_id", summary.get("task_id"), TASK_ID)
    _require_equal("summary.acceptance_id", summary.get("acceptance_id"), ACCEPTANCE_ID)
    _require_equal("summary.status", summary.get("status"), STATUS)
    _require_equal("summary.decision", summary.get("decision"), DECISION)
    _require_equal("summary.threshold", summary.get("threshold_conclusion"), FINAL_THRESHOLD_CONCLUSION)
    _require_equal("summary.source phase", summary.get("source_phase_id"), source_handoff.PHASE_ID)
    _require_equal("summary.source manifest", summary.get("source_manifest_phase_id"), source_handoff.PHASE_ID)
    _require_equal("summary.source decision", summary.get("source_go_no_go_decision"), "NO_GO")
    _require_equal("summary.source matrix", summary.get("source_matrix_check_fail_count"), 0)
    _require_equal(
        "summary.source handoff count",
        summary.get("source_external_action_blocked_handoff_item_count"),
        48,
    )
    _require_equal("summary.source reminder count", summary.get("source_owner_action_reminder_item_count"), 48)
    _require_equal(
        "summary.source private handoff rows",
        summary.get("source_private_external_action_blocked_handoff_records_item_count"),
        48,
    )
    _require_equal(
        "summary.source private reminder rows",
        summary.get("source_private_owner_action_reminder_queue_item_count"),
        48,
    )
    _require_equal("summary.prior observation", summary.get("prior_external_action_blocker_observation_count"), 2)
    _require_equal("summary.observation", summary.get("external_action_blocker_observation_count"), 3)
    _require_true("summary.threshold met", summary.get("external_action_blocked_audit_threshold_met"))
    _require_equal("summary.goal", summary.get("goal_status_recommendation"), "blocked")
    _require_equal("summary.ready count", summary.get("external_owner_action_ready_count"), 0)
    _require_equal("summary.blocker count", summary.get("external_owner_action_blocker_count"), 48)
    _require_equal("summary.private final threshold rows", summary.get("private_final_threshold_records_item_count"), 48)
    _require_equal("summary.actionable owner resolution", summary.get("actionable_owner_resolution_count"), 0)
    _require_equal(
        "summary.source reference blocker count",
        summary.get("source_reference_or_owner_exclusion_final_threshold_blocker_count"),
        40,
    )
    _require_equal(
        "summary.formula blocker count",
        summary.get("formula_or_non_numeric_mapping_final_threshold_blocker_count"),
        8,
    )
    _require_equal(
        "summary.binding ready count",
        summary.get("binding_ready_after_external_action_final_threshold_recheck_count"),
        0,
    )
    _require_equal(
        "summary.comparison ready count",
        summary.get("comparison_retry_ready_after_external_action_final_threshold_recheck_count"),
        0,
    )
    _require_equal("summary.unresolved", summary.get("unresolved_difference_count"), 72)
    for key in (
        "authoritative_binding_application_ready",
        "authoritative_binding_applied_by_this_phase",
        "raw_candidate_fingerprint_bound_by_this_phase",
        "raw_to_processed_value_comparison_ready",
        "raw_to_processed_value_comparison_performed_by_this_phase",
        "full_raw_to_processed_value_comparison_complete",
        "processed_consistency_verified",
        "business_value_consistency_verified",
        "github_upload_performed",
        "app_reinstall_performed",
        "business_execution_performed",
    ):
        _require_false(f"summary.{key}", summary.get(key))
    _require_equal("matrix.check_count", matrix.get("check_count"), 12)
    _require_equal("matrix.check_fail_count", matrix.get("check_fail_count"), 0)
    _require_equal("go_no_go.decision", go_no_go.get("decision"), DECISION)
    _require_equal("go_no_go.next_required_input", go_no_go.get("next_required_input"), NEXT_REQUIRED_INPUT)
    _require_equal("go_no_go.next_recommended_phase", go_no_go.get("next_recommended_phase"), NEXT_RECOMMENDED_PHASE)
    _require_equal("manifest.summary", manifest.get("summary"), summary)
    _check_raw_boundary(summary.get("raw_boundary", {}))
    _check_public_safety(summary.get("public_safety", {}))


def _check_private_outputs(require_private_final_threshold: bool) -> None:
    private_paths = (
        PRIVATE_EXTERNAL_ACTION_FINAL_THRESHOLD_DIAGNOSTIC_PATH,
        PRIVATE_EXTERNAL_ACTION_FINAL_THRESHOLD_RECORDS_PATH,
        PRIVATE_EXTERNAL_ACTION_FINAL_THRESHOLD_REPORT_PATH,
        SOURCE_PRIVATE_EXTERNAL_ACTION_BLOCKED_HANDOFF_DIAGNOSTIC_PATH,
        SOURCE_PRIVATE_EXTERNAL_ACTION_BLOCKED_HANDOFF_RECORDS_PATH,
        SOURCE_PRIVATE_OWNER_ACTION_REMINDER_QUEUE_PATH,
        SOURCE_PRIVATE_OWNER_ACTION_REMINDER_REPORT_PATH,
    )
    for path in private_paths:
        if not path.exists():
            raise ValidationError(f"missing private artifact: {path}")
        if not _git_check_ignored(path):
            raise ValidationError(f"private artifact is not gitignored: {path}")
        if _git_is_tracked(path):
            raise ValidationError(f"private artifact is tracked: {path}")
    if not require_private_final_threshold:
        return
    diagnostic = _read_json(PRIVATE_EXTERNAL_ACTION_FINAL_THRESHOLD_DIAGNOSTIC_PATH)
    rows = _read_jsonl(PRIVATE_EXTERNAL_ACTION_FINAL_THRESHOLD_RECORDS_PATH)
    if len(rows) != 48:
        raise ValidationError("private final threshold records must contain 48 rows")
    if diagnostic.get("threshold_records") != rows:
        raise ValidationError("diagnostic threshold records do not match JSONL rows")
    for row in rows:
        _require_equal("row.phase_id", row.get("phase_id"), PHASE_ID)
        _require_equal("row.task_id", row.get("task_id"), TASK_ID)
        _require_equal("row.status", row.get("external_action_final_threshold_status"), FINAL_THRESHOLD_CONCLUSION)
        _require_false("row.ready", row.get("external_action_final_threshold_ready"))
        _require_true("row.blocker", row.get("external_action_final_threshold_blocker"))
        _require_equal("row.prior", row.get("prior_external_action_blocker_observation_count"), 2)
        _require_equal("row.observation", row.get("external_action_blocker_observation_count"), 3)
        _require_true("row.threshold", row.get("external_action_blocked_audit_threshold_met"))
        _require_equal("row.goal", row.get("goal_status_recommendation"), "blocked")
        _require_false("row.public_commit_allowed", row.get("public_commit_allowed"))
    counts = {kind: sum(1 for row in rows if row.get("diagnostic_kind") == kind) for kind in (
        SOURCE_REFERENCE_DIAGNOSTIC_KIND,
        FORMULA_MAPPING_DIAGNOSTIC_KIND,
    )}
    _require_equal("private source reference blockers", counts[SOURCE_REFERENCE_DIAGNOSTIC_KIND], 40)
    _require_equal("private formula blockers", counts[FORMULA_MAPPING_DIAGNOSTIC_KIND], 8)


def validate(*, require_private_final_threshold: bool = False) -> dict[str, Any]:
    _check_public_artifacts()
    _check_no_raw_private_files_tracked()
    summary = _read_json(SUMMARY_PATH)
    manifest = _read_json(MANIFEST_PATH)
    go_no_go = _read_json(GO_NO_GO_PATH)
    matrix = _read_json(MATRIX_PATH)
    for path, expected in (
        (METADATA_SUMMARY_PATH, summary),
        (METADATA_MANIFEST_PATH, manifest),
        (METADATA_GO_NO_GO_PATH, go_no_go),
        (METADATA_MATRIX_PATH, matrix),
    ):
        _require_equal(f"metadata copy {path}", _read_json(path), expected)
    _check_summary(summary, matrix, go_no_go, manifest)
    _check_private_outputs(require_private_final_threshold)
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-private-final-threshold", action="store_true")
    args = parser.parse_args(argv)
    try:
        manifest = validate(require_private_final_threshold=args.require_private_final_threshold)
    except ValidationError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    summary = manifest["summary"]
    print(
        "PASS: validated V014 owner/authorized-agent external action final threshold recheck after reminder "
        f"(observations={summary['external_action_blocker_observation_count']}, "
        f"threshold={summary['external_action_blocked_audit_threshold_met']}, "
        f"blockers={summary['external_owner_action_blocker_count']}, "
        f"goal={summary['goal_status_recommendation']}, decision={summary['decision']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
