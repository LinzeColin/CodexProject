#!/usr/bin/env python3
"""Validate blocked handoff after resolution-intake blocker final recheck."""

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
    v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_resolution_intake_blocker_final_recheck_after_final_check_closure
    as source_final_recheck,
)
from KMFA.tools.v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_resolution_intake_blocker_blocked_handoff_after_final_recheck import (  # noqa: E402
    ACCEPTANCE_ID,
    DECISION,
    FORMULA_MAPPING_DIAGNOSTIC_KIND,
    GO_NO_GO_PATH,
    GO_NO_GO_RECORD_PATH,
    HANDOFF_CONCLUSION,
    MANIFEST_PATH,
    MATRIX_PATH,
    METADATA_GO_NO_GO_PATH,
    METADATA_MANIFEST_PATH,
    METADATA_MATRIX_PATH,
    METADATA_SUMMARY_PATH,
    NEXT_RECOMMENDED_PHASE,
    NEXT_REQUIRED_INPUT,
    PHASE_ID,
    PRIVATE_RESOLUTION_INTAKE_BLOCKER_BLOCKED_HANDOFF_DIAGNOSTIC_PATH,
    PRIVATE_RESOLUTION_INTAKE_BLOCKER_BLOCKED_HANDOFF_RECORDS_PATH,
    PRIVATE_RESOLUTION_INTAKE_BLOCKER_BLOCKED_HANDOFF_REPORT_PATH,
    PRIVATE_RESOLUTION_INTAKE_BLOCKER_OWNER_RESOLUTION_QUEUE_PATH,
    PROJECT_ROOT,
    REPORT_PATH,
    RISK_REGISTER_PATH,
    ROLLBACK_PATH,
    SOURCE_PRIVATE_RESOLUTION_INTAKE_BLOCKER_FINAL_RECHECK_DIAGNOSTIC_PATH,
    SOURCE_PRIVATE_RESOLUTION_INTAKE_BLOCKER_FINAL_RECHECK_QUEUE_PATH,
    SOURCE_PRIVATE_RESOLUTION_INTAKE_BLOCKER_FINAL_RECHECK_REPORT_PATH,
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
    return (
        subprocess.run(["git", "check-ignore", "-q", path.as_posix()], cwd=PROJECT_ROOT.parent, check=False).returncode
        == 0
    )


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
        "source_final_recheck_public_artifacts_read_by_this_phase",
        "source_final_recheck_manifest_read_by_this_phase",
        "source_final_recheck_go_no_go_read_by_this_phase",
        "source_final_recheck_matrix_read_by_this_phase",
        "source_private_resolution_intake_blocker_final_recheck_diagnostic_read_by_this_phase",
        "source_private_resolution_intake_blocker_final_recheck_queue_read_by_this_phase",
        "source_private_resolution_intake_blocker_final_recheck_report_existence_checked_by_this_phase",
        "private_resolution_intake_blocker_blocked_handoff_diagnostic_written_by_this_phase",
        "private_resolution_intake_blocker_blocked_handoff_records_written_by_this_phase",
        "private_resolution_intake_blocker_owner_resolution_queue_written_by_this_phase",
        "private_resolution_intake_blocker_blocked_handoff_report_written_by_this_phase",
    )
    false_keys = (
        "source_private_resolution_intake_blocker_final_recheck_diagnostic_mutated_by_this_phase",
        "source_private_resolution_intake_blocker_final_recheck_queue_mutated_by_this_phase",
        "source_private_resolution_intake_blocker_final_recheck_report_mutated_by_this_phase",
        "owner_or_authorized_agent_resolution_completed_by_this_phase",
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
    _require_equal("summary.handoff_conclusion", summary.get("handoff_conclusion"), HANDOFF_CONCLUSION)
    _require_equal("summary.source phase", summary.get("source_phase_id"), source_final_recheck.PHASE_ID)
    _require_equal("summary.source manifest", summary.get("source_manifest_phase_id"), source_final_recheck.PHASE_ID)
    _require_equal("summary.source decision", summary.get("source_go_no_go_decision"), "NO_GO")
    _require_equal("summary.source matrix", summary.get("source_matrix_check_fail_count"), 0)
    _require_equal(
        "summary.source final recheck",
        summary.get("source_resolution_intake_blocker_final_recheck_item_count"),
        48,
    )
    _require_equal(
        "summary.source blockers",
        summary.get("source_resolution_intake_blocker_final_recheck_blocker_count"),
        48,
    )
    _require_equal(
        "summary.source ready",
        summary.get("source_resolution_intake_blocker_final_recheck_ready_count"),
        0,
    )
    _require_equal(
        "summary.source private final recheck queue",
        summary.get("source_private_resolution_intake_blocker_final_recheck_queue_item_count"),
        48,
    )
    _require_equal("summary.blocked handoff", summary.get("blocked_handoff_item_count"), 48)
    _require_equal("summary.owner resolution", summary.get("owner_resolution_item_count"), 48)
    _require_equal("summary.goal", summary.get("goal_status_recommendation"), "blocked")
    _require_equal("summary.observation", summary.get("resolution_intake_blocker_observation_count"), 3)
    _require_true("summary.threshold", summary.get("resolution_intake_blocker_audit_threshold_met"))
    _require_equal("summary.ready", summary.get("owner_resolution_intake_ready_count"), 0)
    _require_equal("summary.blocker", summary.get("owner_resolution_intake_blocker_count"), 48)
    _require_equal("summary.valid", summary.get("valid_owner_resolution_intake_blocker_count"), 48)
    _require_equal("summary.actionable", summary.get("actionable_owner_resolution_count"), 0)
    _require_equal(
        "summary.source ref owner resolutions",
        summary.get("source_reference_or_owner_exclusion_owner_resolution_count"),
        40,
    )
    _require_equal(
        "summary.formula owner resolutions",
        summary.get("formula_or_non_numeric_mapping_owner_resolution_count"),
        8,
    )
    _require_equal("summary.binding ready", summary.get("binding_ready_after_blocked_handoff_count"), 0)
    _require_equal("summary.retry ready", summary.get("comparison_retry_ready_after_blocked_handoff_count"), 0)
    _require_equal("summary.unresolved differences", summary.get("unresolved_difference_count"), 72)
    for key in (
        "private_resolution_intake_blocker_blocked_handoff_diagnostic_written",
        "private_resolution_intake_blocker_blocked_handoff_records_written",
        "private_resolution_intake_blocker_owner_resolution_queue_written",
        "private_resolution_intake_blocker_blocked_handoff_report_written",
        "private_resolution_intake_blocker_blocked_handoff_diagnostic_gitignored",
        "private_resolution_intake_blocker_blocked_handoff_records_gitignored",
        "private_resolution_intake_blocker_owner_resolution_queue_gitignored",
        "private_resolution_intake_blocker_blocked_handoff_report_gitignored",
        "source_private_resolution_intake_blocker_final_recheck_diagnostic_gitignored",
        "source_private_resolution_intake_blocker_final_recheck_queue_gitignored",
        "source_private_resolution_intake_blocker_final_recheck_report_gitignored",
        "blocked_handoff_prepared_by_this_phase",
        "owner_resolution_queue_prepared_by_this_phase",
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
        "processed_consistency_verified",
        "business_value_consistency_ready",
        "business_value_consistency_verified",
        "business_value_consistency_verified_by_this_phase",
        "full_reconciliation_allowed",
        "lineage_full_check_ready",
        "lineage_full_check_complete",
        "lineage_full_check_performed_by_this_phase",
        "formal_report_allowed",
        "github_upload_ready",
        "github_upload_allowed",
        "github_upload_performed_by_this_phase",
        "github_upload_performed",
        "app_reinstall_ready",
        "app_reinstall_allowed",
        "app_reinstall_performed_by_this_phase",
        "app_reinstall_performed",
        "business_execution_ready",
        "business_execution_allowed",
        "business_execution_performed_by_this_phase",
        "business_execution_performed",
    ):
        _require_false(f"summary.{key}", summary.get(key))
    _require_equal("summary.next_required_input", summary.get("next_required_input"), NEXT_REQUIRED_INPUT)
    _require_equal("summary.next_recommended_phase", summary.get("next_recommended_phase"), NEXT_RECOMMENDED_PHASE)
    _check_raw_boundary(summary.get("raw_boundary") or {})
    _check_public_safety(summary.get("public_safety") or {})

    _require_equal("matrix.phase_id", matrix.get("phase_id"), PHASE_ID)
    _require_equal("matrix.check_count", matrix.get("check_count"), 12)
    _require_equal("matrix.check_pass_count", matrix.get("check_pass_count"), 12)
    _require_equal("matrix.check_fail_count", matrix.get("check_fail_count"), 0)
    checks = {row.get("check_code"): row.get("status") for row in matrix.get("checks", []) if isinstance(row, dict)}
    for code in (
        "source_final_recheck_phase_loaded",
        "source_go_no_go_preserved",
        "source_matrix_clean",
        "source_final_recheck_complete",
        "source_blockers_complete",
        "source_private_final_recheck_queue_complete",
        "blocked_handoff_complete",
        "owner_resolution_queue_complete",
        "blocked_goal_preserved",
        "diagnostic_kind_owner_resolution_counts_locked",
        "raw_inbox_untouched",
        "downstream_gates_closed",
    ):
        _require_equal(f"matrix.{code}", checks.get(code), "PASS")

    _require_equal("go_no_go.phase_id", go_no_go.get("phase_id"), PHASE_ID)
    _require_equal("go_no_go.decision", go_no_go.get("decision"), DECISION)
    _require_equal("go_no_go.handoff_conclusion", go_no_go.get("handoff_conclusion"), HANDOFF_CONCLUSION)
    _require_equal("go_no_go.blocked handoff", go_no_go.get("blocked_handoff_item_count"), 48)
    _require_equal("go_no_go.owner resolution", go_no_go.get("owner_resolution_item_count"), 48)
    _require_equal("go_no_go.goal", go_no_go.get("goal_status_recommendation"), "blocked")
    _require_true("go_no_go.threshold", go_no_go.get("resolution_intake_blocker_audit_threshold_met"))
    _require_equal("go_no_go.ready", go_no_go.get("owner_resolution_intake_ready_count"), 0)
    _require_equal("go_no_go.blocker", go_no_go.get("owner_resolution_intake_blocker_count"), 48)
    _require_equal("go_no_go.actionable", go_no_go.get("actionable_owner_resolution_count"), 0)
    _require_false("go_no_go.binding ready", go_no_go.get("authoritative_binding_application_ready"))
    _require_false("go_no_go.raw comparison allowed", go_no_go.get("raw_to_processed_value_comparison_allowed"))
    _require_false("go_no_go.raw comparison", go_no_go.get("raw_to_processed_value_comparison_performed_by_this_phase"))
    _require_false("go_no_go.business consistency", go_no_go.get("business_value_consistency_verified"))
    _require_false("go_no_go.github upload", go_no_go.get("github_upload_allowed"))
    _require_false("go_no_go.app reinstall", go_no_go.get("app_reinstall_allowed"))
    _require_false("go_no_go.business execution", go_no_go.get("business_execution_allowed"))
    _require_equal("go_no_go.next_required_input", go_no_go.get("next_required_input"), NEXT_REQUIRED_INPUT)
    _require_equal("go_no_go.next_recommended_phase", go_no_go.get("next_recommended_phase"), NEXT_RECOMMENDED_PHASE)
    _require_equal("manifest.summary", manifest.get("summary"), summary)
    _require_equal("manifest.matrix", manifest.get("matrix"), matrix)
    _require_equal("manifest.go_no_go", manifest.get("go_no_go_report"), go_no_go)


def _check_private_artifacts() -> None:
    private_paths = (
        PRIVATE_RESOLUTION_INTAKE_BLOCKER_BLOCKED_HANDOFF_DIAGNOSTIC_PATH,
        PRIVATE_RESOLUTION_INTAKE_BLOCKER_BLOCKED_HANDOFF_RECORDS_PATH,
        PRIVATE_RESOLUTION_INTAKE_BLOCKER_OWNER_RESOLUTION_QUEUE_PATH,
        PRIVATE_RESOLUTION_INTAKE_BLOCKER_BLOCKED_HANDOFF_REPORT_PATH,
        SOURCE_PRIVATE_RESOLUTION_INTAKE_BLOCKER_FINAL_RECHECK_DIAGNOSTIC_PATH,
        SOURCE_PRIVATE_RESOLUTION_INTAKE_BLOCKER_FINAL_RECHECK_QUEUE_PATH,
        SOURCE_PRIVATE_RESOLUTION_INTAKE_BLOCKER_FINAL_RECHECK_REPORT_PATH,
    )
    for path in private_paths:
        if not path.exists():
            raise ValidationError(f"missing private artifact: {path}")
        if not _git_check_ignored(path):
            raise ValidationError(f"private artifact is not git-ignored: {path}")
        if _git_is_tracked(path):
            raise ValidationError(f"private artifact is tracked: {path}")
    diagnostic = _read_json(PRIVATE_RESOLUTION_INTAKE_BLOCKER_BLOCKED_HANDOFF_DIAGNOSTIC_PATH)
    handoff_rows = _read_jsonl(PRIVATE_RESOLUTION_INTAKE_BLOCKER_BLOCKED_HANDOFF_RECORDS_PATH)
    owner_resolution_rows = _read_jsonl(PRIVATE_RESOLUTION_INTAKE_BLOCKER_OWNER_RESOLUTION_QUEUE_PATH)
    _require_equal("private diagnostic phase", diagnostic.get("phase_id"), PHASE_ID)
    _require_equal("private diagnostic handoff rows", len(diagnostic.get("blocked_handoff_rows") or []), 48)
    _require_equal(
        "private diagnostic owner resolution rows",
        len(diagnostic.get("owner_resolution_queue_rows") or []),
        48,
    )
    _require_equal("private handoff row count", len(handoff_rows), 48)
    _require_equal("private owner resolution row count", len(owner_resolution_rows), 48)
    handoff_counts = Counter(row.get("diagnostic_kind") for row in handoff_rows)
    _require_equal(f"private diagnostic kind {SOURCE_REFERENCE_DIAGNOSTIC_KIND}", handoff_counts[SOURCE_REFERENCE_DIAGNOSTIC_KIND], 40)
    _require_equal(f"private diagnostic kind {FORMULA_MAPPING_DIAGNOSTIC_KIND}", handoff_counts[FORMULA_MAPPING_DIAGNOSTIC_KIND], 8)
    for row in handoff_rows:
        _require_equal("private handoff status", row.get("blocked_handoff_status"), HANDOFF_CONCLUSION)
        _require_true("private owner resolution required", row.get("owner_resolution_required"))
        _require_equal(
            "private owner resolution status",
            row.get("owner_resolution_status"),
            "required_before_binding_or_value_comparison",
        )
        _require_true("private threshold met", row.get("resolution_intake_blocker_audit_threshold_met"))
        _require_equal("private goal", row.get("goal_status_recommendation"), "blocked")
        _require_false("private actionable", row.get("actionable_owner_resolution_ready"))
        _require_false("private binding", row.get("binding_ready_after_blocked_handoff"))
        _require_false("private retry", row.get("comparison_retry_ready_after_blocked_handoff"))
        _require_false("private public commit", row.get("public_commit_allowed"))
    for row in owner_resolution_rows:
        _require_equal(
            "owner resolution status",
            row.get("owner_resolution_status"),
            "required_before_binding_or_value_comparison",
        )
        _require_true("owner agent required", row.get("owner_or_authorized_agent_required"))
        _require_true("actionable resolution required", row.get("actionable_owner_resolution_required"))
        _require_false("owner binding ready", row.get("authoritative_binding_application_ready"))
        _require_false("owner comparison ready", row.get("raw_to_processed_value_comparison_ready"))
        _require_false("owner public commit", row.get("public_commit_allowed"))


def validate(*, require_private_blocked_handoff: bool = False) -> dict[str, Any]:
    summary = _read_json(SUMMARY_PATH)
    manifest = _read_json(MANIFEST_PATH)
    go_no_go = _read_json(GO_NO_GO_PATH)
    matrix = _read_json(MATRIX_PATH)
    for path, payload in (
        (METADATA_SUMMARY_PATH, summary),
        (METADATA_MANIFEST_PATH, manifest),
        (METADATA_GO_NO_GO_PATH, go_no_go),
        (METADATA_MATRIX_PATH, matrix),
    ):
        _require_equal(f"metadata copy {path}", _read_json(path), payload)
    _check_summary(summary, matrix, go_no_go, manifest)
    _check_public_artifacts()
    _check_no_raw_private_files_tracked()
    if require_private_blocked_handoff:
        _check_private_artifacts()
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-private-blocked-handoff", action="store_true")
    args = parser.parse_args(argv)
    try:
        manifest = validate(require_private_blocked_handoff=args.require_private_blocked_handoff)
    except ValidationError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    summary = manifest["summary"]
    print(
        "PASS: validated V014 owner/agent resolution-intake blocker blocked handoff after final recheck "
        f"(handoff={summary['blocked_handoff_item_count']}, "
        f"owner_resolutions={summary['owner_resolution_item_count']}, "
        f"goal={summary['goal_status_recommendation']}, "
        f"decision={summary['decision']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
