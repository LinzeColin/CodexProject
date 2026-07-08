#!/usr/bin/env python3
"""Validate the external-action requirement gate before processed-data reconciliation."""

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
    v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_external_action_required_before_raw_to_processed_value_comparison
    as source_comparison,
)
from KMFA.tools.v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_external_action_required_before_processed_data_reconciliation import (  # noqa: E402
    ACCEPTANCE_ID,
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
    PRIVATE_PROCESSED_DATA_RECONCILIATION_REQUIREMENT_DIAGNOSTIC_PATH,
    PRIVATE_PROCESSED_DATA_RECONCILIATION_REQUIREMENT_QUEUE_PATH,
    PRIVATE_PROCESSED_DATA_RECONCILIATION_REQUIREMENT_REPORT_PATH,
    PROJECT_ROOT,
    REPORT_PATH,
    REQUIREMENT_CONCLUSION,
    RISK_REGISTER_PATH,
    ROLLBACK_PATH,
    SOURCE_PRIVATE_RAW_TO_PROCESSED_VALUE_COMPARISON_REQUIREMENT_DIAGNOSTIC_PATH,
    SOURCE_PRIVATE_RAW_TO_PROCESSED_VALUE_COMPARISON_REQUIREMENT_QUEUE_PATH,
    SOURCE_PRIVATE_RAW_TO_PROCESSED_VALUE_COMPARISON_REQUIREMENT_REPORT_PATH,
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
        "source_raw_comparison_public_artifacts_read_by_this_phase",
        "source_private_raw_comparison_requirement_queue_read_by_this_phase",
        "private_processed_data_reconciliation_requirement_diagnostic_written_by_this_phase",
        "private_processed_data_reconciliation_requirement_queue_written_by_this_phase",
        "private_processed_data_reconciliation_requirement_report_written_by_this_phase",
    )
    false_keys = (
        "source_private_raw_comparison_requirement_diagnostic_mutated_by_this_phase",
        "source_private_raw_comparison_requirement_queue_mutated_by_this_phase",
        "source_private_raw_comparison_requirement_report_mutated_by_this_phase",
        "owner_or_agent_external_action_completed_by_this_phase",
        "authoritative_binding_applied_by_this_phase",
        "raw_candidate_fingerprint_bound_by_this_phase",
        "processed_data_reconciliation_ready_by_this_phase",
        "processed_data_reconciliation_performed_by_this_phase",
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
    _require_equal("summary.requirement", summary.get("requirement_conclusion"), REQUIREMENT_CONCLUSION)
    _require_equal("summary.source phase", summary.get("source_phase_id"), source_comparison.PHASE_ID)
    _require_equal("summary.source manifest", summary.get("source_manifest_phase_id"), source_comparison.PHASE_ID)
    _require_equal("summary.source decision", summary.get("source_go_no_go_decision"), "NO_GO")
    _require_equal("summary.source matrix", summary.get("source_matrix_check_fail_count"), 0)
    _require_equal(
        "summary.source raw comparison ready",
        summary.get("source_raw_to_processed_value_comparison_requirement_ready_count"),
        0,
    )
    _require_equal(
        "summary.source raw comparison blockers",
        summary.get("source_raw_to_processed_value_comparison_requirement_blocker_count"),
        48,
    )
    _require_equal(
        "summary.source raw comparison required",
        summary.get("source_raw_to_processed_value_comparison_requirement_required_count"),
        48,
    )
    _require_equal(
        "summary.source private raw comparison rows",
        summary.get("source_private_raw_to_processed_value_comparison_requirement_queue_item_count"),
        48,
    )
    _require_equal("summary.source goal", summary.get("source_goal_status_recommendation"), "blocked")
    _require_equal("summary.goal", summary.get("goal_status_recommendation"), "blocked")
    _require_equal(
        "summary.processed reconciliation req ready",
        summary.get("processed_data_reconciliation_requirement_ready_count"),
        0,
    )
    _require_equal(
        "summary.processed reconciliation req blockers",
        summary.get("processed_data_reconciliation_requirement_blocker_count"),
        48,
    )
    _require_equal(
        "summary.processed reconciliation req required",
        summary.get("processed_data_reconciliation_requirement_required_count"),
        48,
    )
    _require_equal("summary.actionable owner resolution", summary.get("actionable_owner_resolution_count"), 0)
    _require_equal(
        "summary.source ref reconciliation requirement",
        summary.get("source_reference_or_owner_exclusion_reconciliation_requirement_count"),
        40,
    )
    _require_equal(
        "summary.formula reconciliation requirement",
        summary.get("formula_or_non_numeric_mapping_reconciliation_requirement_count"),
        8,
    )
    _require_equal("summary.binding application ready count", summary.get("authoritative_binding_application_ready_count"), 0)
    _require_equal("summary.raw comparison ready count", summary.get("raw_to_processed_value_comparison_ready_count"), 0)
    _require_equal("summary.processed reconciliation ready count", summary.get("processed_data_reconciliation_ready_count"), 0)
    _require_equal("summary.unresolved differences", summary.get("unresolved_difference_count"), 72)
    for key in (
        "private_processed_data_reconciliation_requirement_diagnostic_written",
        "private_processed_data_reconciliation_requirement_queue_written",
        "private_processed_data_reconciliation_requirement_report_written",
        "private_processed_data_reconciliation_requirement_diagnostic_gitignored",
        "private_processed_data_reconciliation_requirement_queue_gitignored",
        "private_processed_data_reconciliation_requirement_report_gitignored",
        "source_private_raw_to_processed_value_comparison_requirement_diagnostic_gitignored",
        "source_private_raw_to_processed_value_comparison_requirement_queue_gitignored",
        "source_private_raw_to_processed_value_comparison_requirement_report_gitignored",
        "external_action_requirement_checked_by_this_phase",
    ):
        _require_true(f"summary.{key}", summary.get(key))
    for key in (
        "owner_or_agent_external_action_completed_by_this_phase",
        "authoritative_binding_application_ready",
        "authoritative_binding_applied_by_this_phase",
        "raw_candidate_fingerprint_bound_by_this_phase",
        "raw_to_processed_value_comparison_ready",
        "raw_to_processed_value_comparison_performed_by_this_phase",
        "full_raw_to_processed_value_comparison_complete",
        "processed_data_reconciliation_ready",
        "processed_data_reconciliation_performed_by_this_phase",
        "full_processed_data_reconciliation_complete",
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
    _require_equal("matrix.check_count", matrix.get("check_count"), 12)
    _require_equal("matrix.check_pass_count", matrix.get("check_pass_count"), 12)
    _require_equal("matrix.check_fail_count", matrix.get("check_fail_count"), 0)
    checks = {row.get("check_code"): row.get("status") for row in matrix.get("checks", []) if isinstance(row, dict)}
    for code in (
        "source_raw_comparison_phase_loaded",
        "source_go_no_go_preserved",
        "source_matrix_clean",
        "source_raw_comparison_blockers_complete",
        "source_private_raw_comparison_requirement_queue_read",
        "processed_reconciliation_requirement_queue_complete",
        "processed_reconciliation_requirement_blockers_locked",
        "diagnostic_kind_reconciliation_requirement_counts_locked",
        "blocked_goal_preserved",
        "raw_inbox_untouched",
        "downstream_gates_closed",
        "public_safety_locked",
    ):
        _require_equal(f"matrix.{code}", checks.get(code), "PASS")

    _require_equal("go_no_go.phase_id", go_no_go.get("phase_id"), PHASE_ID)
    _require_equal("go_no_go.decision", go_no_go.get("decision"), DECISION)
    _require_equal("go_no_go.requirement", go_no_go.get("requirement_conclusion"), REQUIREMENT_CONCLUSION)
    _require_equal("go_no_go.processed reconciliation req ready", go_no_go.get("processed_data_reconciliation_requirement_ready_count"), 0)
    _require_equal("go_no_go.processed reconciliation req blocker", go_no_go.get("processed_data_reconciliation_requirement_blocker_count"), 48)
    _require_equal("go_no_go.processed reconciliation req required", go_no_go.get("processed_data_reconciliation_requirement_required_count"), 48)
    _require_equal("go_no_go.goal", go_no_go.get("goal_status_recommendation"), "blocked")
    _require_false("go_no_go.binding ready", go_no_go.get("authoritative_binding_application_ready"))
    _require_false("go_no_go.raw comparison allowed", go_no_go.get("raw_to_processed_value_comparison_allowed"))
    _require_false(
        "go_no_go.raw comparison",
        go_no_go.get("raw_to_processed_value_comparison_performed_by_this_phase"),
    )
    _require_false("go_no_go.processed reconciliation allowed", go_no_go.get("processed_data_reconciliation_allowed"))
    _require_false("go_no_go.processed reconciliation", go_no_go.get("processed_data_reconciliation_performed_by_this_phase"))
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
        PRIVATE_PROCESSED_DATA_RECONCILIATION_REQUIREMENT_DIAGNOSTIC_PATH,
        PRIVATE_PROCESSED_DATA_RECONCILIATION_REQUIREMENT_QUEUE_PATH,
        PRIVATE_PROCESSED_DATA_RECONCILIATION_REQUIREMENT_REPORT_PATH,
        SOURCE_PRIVATE_RAW_TO_PROCESSED_VALUE_COMPARISON_REQUIREMENT_DIAGNOSTIC_PATH,
        SOURCE_PRIVATE_RAW_TO_PROCESSED_VALUE_COMPARISON_REQUIREMENT_QUEUE_PATH,
        SOURCE_PRIVATE_RAW_TO_PROCESSED_VALUE_COMPARISON_REQUIREMENT_REPORT_PATH,
    )
    for path in private_paths:
        if not path.exists():
            raise ValidationError(f"missing private artifact: {path}")
        if not _git_check_ignored(path):
            raise ValidationError(f"private artifact is not git-ignored: {path}")
        if _git_is_tracked(path):
            raise ValidationError(f"private artifact is tracked: {path}")
    diagnostic = _read_json(PRIVATE_PROCESSED_DATA_RECONCILIATION_REQUIREMENT_DIAGNOSTIC_PATH)
    requirement_rows = _read_jsonl(PRIVATE_PROCESSED_DATA_RECONCILIATION_REQUIREMENT_QUEUE_PATH)
    report = PRIVATE_PROCESSED_DATA_RECONCILIATION_REQUIREMENT_REPORT_PATH.read_text(encoding="utf-8")
    _require_equal("private diagnostic phase", diagnostic.get("phase_id"), PHASE_ID)
    _require_equal(
        "private diagnostic rows",
        len(diagnostic.get("processed_data_reconciliation_requirement_rows") or []),
        48,
    )
    _require_equal("private processed reconciliation requirement row count", len(requirement_rows), 48)
    if "owner/授权代理 external action required before processed-data reconciliation 队列" not in report:
        raise ValidationError("private processed reconciliation requirement report missing Chinese heading")
    counts = Counter(row.get("diagnostic_kind") for row in requirement_rows)
    _require_equal(
        f"private diagnostic kind {SOURCE_REFERENCE_DIAGNOSTIC_KIND}",
        counts[SOURCE_REFERENCE_DIAGNOSTIC_KIND],
        40,
    )
    _require_equal(f"private diagnostic kind {FORMULA_MAPPING_DIAGNOSTIC_KIND}", counts[FORMULA_MAPPING_DIAGNOSTIC_KIND], 8)
    for row in requirement_rows:
        _require_equal(
            "private processed reconciliation requirement status",
            row.get("processed_data_reconciliation_requirement_status"),
            REQUIREMENT_CONCLUSION,
        )
        _require_true(
            "private processed reconciliation requirement required",
            row.get("processed_data_reconciliation_requirement_required"),
        )
        _require_false(
            "private processed reconciliation requirement ready",
            row.get("processed_data_reconciliation_requirement_ready"),
        )
        _require_true(
            "private processed reconciliation requirement blocker",
            row.get("processed_data_reconciliation_requirement_blocker"),
        )
        _require_false("private actionable owner resolution", row.get("actionable_owner_resolution_ready"))
        _require_false("private authoritative binding ready", row.get("authoritative_binding_application_ready"))
        _require_false("private authoritative binding applied", row.get("authoritative_binding_applied_by_this_phase"))
        _require_false("private processed reconciliation ready", row.get("processed_data_reconciliation_ready"))
        _require_false("private processed reconciliation performed", row.get("processed_data_reconciliation_performed_by_this_phase"))
        _require_false("private public commit", row.get("public_commit_allowed"))


def validate(*, require_private_processed_data_reconciliation_requirement: bool = False) -> dict[str, Any]:
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
    if require_private_processed_data_reconciliation_requirement:
        _check_private_artifacts()
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-private-processed-data-reconciliation-requirement", action="store_true")
    args = parser.parse_args(argv)
    try:
        manifest = validate(
            require_private_processed_data_reconciliation_requirement=(
                args.require_private_processed_data_reconciliation_requirement
            )
        )
    except ValidationError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    summary = manifest["summary"]
    print(
        "PASS: validated V014 owner/authorized-agent external action required before processed reconciliation "
        f"(ready={summary['processed_data_reconciliation_requirement_ready_count']}, "
        f"blockers={summary['processed_data_reconciliation_requirement_blocker_count']}, "
        f"goal={summary['goal_status_recommendation']}, "
        f"decision={summary['decision']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
