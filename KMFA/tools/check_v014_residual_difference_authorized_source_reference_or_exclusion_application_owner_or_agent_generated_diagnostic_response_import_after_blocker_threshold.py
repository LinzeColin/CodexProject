#!/usr/bin/env python3
"""Validate generated owner/agent diagnostic response import after blocker threshold."""

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

from KMFA.tools.v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_import_after_blocker_threshold import (  # noqa: E402
    ACCEPTANCE_ID,
    AUTHORIZATION_SOURCE,
    DECISION,
    FORMULA_MAPPING_DIAGNOSTIC_KIND,
    GO_NO_GO_PATH,
    GO_NO_GO_RECORD_PATH,
    IMPORT_CONCLUSION,
    MANIFEST_PATH,
    MATRIX_PATH,
    METADATA_GO_NO_GO_PATH,
    METADATA_MANIFEST_PATH,
    METADATA_MATRIX_PATH,
    METADATA_SUMMARY_PATH,
    NEXT_RECOMMENDED_PHASE,
    NEXT_REQUIRED_INPUT,
    PHASE_ID,
    PRIVATE_GENERATED_RESPONSE_ITEMS_PATH,
    PRIVATE_GENERATED_RESPONSE_RECORD_PATH,
    PRIVATE_GENERATED_RESPONSE_REPORT_PATH,
    PRIVATE_NON_ACTIONABLE_QUEUE_PATH,
    REPORT_PATH,
    RISK_REGISTER_PATH,
    ROLLBACK_PATH,
    SOURCE_PRIVATE_TEMPLATE_PATH,
    SOURCE_PRIVATE_THRESHOLD_RECORDS_PATH,
    SOURCE_PRIVATE_THRESHOLD_REPORT_PATH,
    SOURCE_REFERENCE_DIAGNOSTIC_KIND,
    STATUS,
    SUMMARY_PATH,
    TASK_ID,
    TEST_RESULTS_PATH,
    VERSION,
    source_threshold,
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
    re.compile(r"\.(xlsx|xlsm|xls|zip|pdf|sqlite|sqlite3|db)\b", re.IGNORECASE),
    re.compile(r"sha256:[0-9a-f]{64}"),
    re.compile(r'"[0-9a-f]{64}"'),
    re.compile(
        r'"(?:target_slot_id|raw_file_name|archive_member_name|sheet_name|cell_address|raw_value|'
        r"normalized_decimal|context_text|numeric_value_fingerprint|processed_value_fingerprint|"
        r"raw_candidate_fingerprint|value_fingerprint|raw_candidate_record_ref_hash|source_record_ref_hash)'",
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
        "source_public_threshold_summary_read_by_this_phase",
        "source_public_threshold_manifest_read_by_this_phase",
        "source_public_threshold_go_no_go_read_by_this_phase",
        "source_public_threshold_matrix_read_by_this_phase",
        "source_private_template_read_by_this_phase",
        "source_private_threshold_records_read_by_this_phase",
        "source_private_threshold_report_existence_checked_by_this_phase",
        "private_generated_response_record_written_by_this_phase",
        "private_generated_response_items_written_by_this_phase",
        "private_non_actionable_queue_written_by_this_phase",
        "private_generated_response_report_written_by_this_phase",
        "owner_or_agent_valid_response_supplied_by_this_phase",
        "authorized_delegate_generated_response_by_this_phase",
    ):
        _require_true(f"raw_boundary.{key}", raw_boundary.get(key))
    for key, value in raw_boundary.items():
        if key.startswith("raw_inbox_") or key.endswith("_mutated_by_this_phase"):
            _require_false(f"raw_boundary.{key}", value)
    for key in (
        "source_private_template_mutated_by_this_phase",
        "source_private_threshold_records_mutated_by_this_phase",
        "source_private_threshold_report_mutated_by_this_phase",
        "authoritative_binding_applied_by_this_phase",
        "raw_candidate_fingerprint_bound_by_this_phase",
        "raw_to_processed_value_comparison_performed_by_this_phase",
    ):
        _require_false(f"raw_boundary.{key}", raw_boundary.get(key))


def _check_public_safety(public_safety: dict[str, Any]) -> None:
    _require_true("public_safety.public_safe_aggregate_only", public_safety.get("public_safe_aggregate_only"))
    for key, value in public_safety.items():
        if key != "public_safe_aggregate_only":
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
    _require_equal("summary.import_conclusion", summary.get("import_conclusion"), IMPORT_CONCLUSION)
    _require_equal("summary.authorization_source", summary.get("authorization_source"), AUTHORIZATION_SOURCE)
    _require_true("summary.generated_by_authorized_delegate", summary.get("generated_by_authorized_delegate"))
    _require_equal("summary.source_phase_id", summary.get("source_phase_id"), source_threshold.PHASE_ID)
    _require_equal("summary.source_manifest_phase_id", summary.get("source_manifest_phase_id"), source_threshold.PHASE_ID)
    _require_equal("summary.source_go_no_go_decision", summary.get("source_go_no_go_decision"), "NO_GO")
    _require_equal("summary.source_matrix_check_fail_count", summary.get("source_matrix_check_fail_count"), 0)
    _require_equal("summary.source observation", summary.get("source_diagnostic_blocker_observation_count"), 3)
    _require_true("summary.source threshold", summary.get("source_diagnostic_blocked_audit_threshold_met"))
    _require_equal("summary.source blockers", summary.get("source_diagnostic_response_blocker_count"), 48)
    _require_equal("summary.source pending", summary.get("source_pending_diagnostic_response_count"), 48)
    _require_equal("summary.source valid", summary.get("source_valid_diagnostic_response_count"), 0)
    _require_equal("summary.source actionable", summary.get("source_actionable_resolution_count"), 0)
    _require_equal("summary.template", summary.get("source_template_item_count"), 48)
    _require_equal("summary.threshold", summary.get("source_threshold_record_count"), 48)
    _require_equal("summary.target match", summary.get("target_slot_match_count"), 48)
    _require_equal("summary.generated", summary.get("generated_diagnostic_response_count"), 48)
    _require_equal("summary.valid", summary.get("valid_diagnostic_response_count"), 48)
    _require_equal("summary.pending", summary.get("pending_diagnostic_response_count"), 0)
    _require_equal("summary.blocker", summary.get("diagnostic_response_blocker_count"), 0)
    _require_equal("summary.invalid", summary.get("invalid_diagnostic_response_count"), 0)
    _require_equal("summary.non actionable", summary.get("non_actionable_diagnostic_response_count"), 48)
    _require_equal("summary.actionable", summary.get("actionable_resolution_count"), 0)
    _require_equal("summary.source ref responses", summary.get("source_reference_or_owner_exclusion_response_count"), 40)
    _require_equal("summary.formula responses", summary.get("formula_or_non_numeric_mapping_response_count"), 8)
    _require_equal("summary.binding ready", summary.get("binding_ready_after_generated_response_import_count"), 0)
    _require_equal("summary.retry ready", summary.get("comparison_retry_ready_after_generated_response_import_count"), 0)
    _require_equal("summary.unresolved differences", summary.get("unresolved_difference_count"), 72)
    for key in (
        "owner_or_agent_valid_response_supplied",
        "owner_or_agent_valid_response_supplied_by_this_phase",
        "private_generated_response_record_written",
        "private_generated_response_items_written",
        "private_non_actionable_queue_written",
        "private_generated_response_report_written",
        "private_generated_response_record_gitignored",
        "private_generated_response_items_gitignored",
        "private_non_actionable_queue_gitignored",
        "private_generated_response_report_gitignored",
        "source_private_template_gitignored",
        "source_private_threshold_records_gitignored",
        "source_private_threshold_report_gitignored",
    ):
        _require_true(f"summary.{key}", summary.get(key))
    for key in (
        "authoritative_binding_application_ready",
        "authoritative_binding_applied_by_this_phase",
        "raw_candidate_fingerprint_bound_by_this_phase",
        "raw_to_processed_value_comparison_ready",
        "raw_to_processed_value_comparison_performed_by_this_phase",
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
    _require_equal("matrix.check_count", matrix.get("check_count"), 13)
    _require_equal("matrix.check_pass_count", matrix.get("check_pass_count"), 13)
    _require_equal("matrix.check_fail_count", matrix.get("check_fail_count"), 0)
    checks = {row.get("check_code"): row.get("status") for row in matrix.get("checks", []) if isinstance(row, dict)}
    for code in (
        "source_threshold_phase_loaded",
        "source_go_no_go_preserved",
        "source_matrix_clean",
        "source_threshold_was_met",
        "source_template_complete",
        "source_threshold_records_complete",
        "target_sets_match",
        "valid_generated_responses_imported",
        "missing_response_blocker_cleared",
        "all_generated_responses_non_actionable",
        "diagnostic_kind_counts_locked",
        "raw_inbox_untouched",
        "downstream_gates_closed",
    ):
        _require_equal(f"matrix.{code}", checks.get(code), "PASS")

    _require_equal("go_no_go.phase_id", go_no_go.get("phase_id"), PHASE_ID)
    _require_equal("go_no_go.decision", go_no_go.get("decision"), DECISION)
    _require_equal("go_no_go.import_conclusion", go_no_go.get("import_conclusion"), IMPORT_CONCLUSION)
    _require_equal("go_no_go.authorization_source", go_no_go.get("authorization_source"), AUTHORIZATION_SOURCE)
    _require_equal("go_no_go.generated", go_no_go.get("generated_diagnostic_response_count"), 48)
    _require_equal("go_no_go.valid", go_no_go.get("valid_diagnostic_response_count"), 48)
    _require_equal("go_no_go.pending", go_no_go.get("pending_diagnostic_response_count"), 0)
    _require_equal("go_no_go.blocker", go_no_go.get("diagnostic_response_blocker_count"), 0)
    _require_equal("go_no_go.non actionable", go_no_go.get("non_actionable_diagnostic_response_count"), 48)
    _require_equal("go_no_go.actionable", go_no_go.get("actionable_resolution_count"), 0)
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
        SOURCE_PRIVATE_TEMPLATE_PATH,
        SOURCE_PRIVATE_THRESHOLD_RECORDS_PATH,
        SOURCE_PRIVATE_THRESHOLD_REPORT_PATH,
        PRIVATE_GENERATED_RESPONSE_RECORD_PATH,
        PRIVATE_GENERATED_RESPONSE_ITEMS_PATH,
        PRIVATE_NON_ACTIONABLE_QUEUE_PATH,
        PRIVATE_GENERATED_RESPONSE_REPORT_PATH,
    )
    for path in private_paths:
        if not path.exists():
            raise ValidationError(f"missing private artifact: {path}")
        if not _git_check_ignored(path):
            raise ValidationError(f"private artifact is not git-ignored: {path}")
    source_template = _read_jsonl(SOURCE_PRIVATE_TEMPLATE_PATH)
    source_threshold_rows = _read_jsonl(SOURCE_PRIVATE_THRESHOLD_RECORDS_PATH)
    response_record = _read_json(PRIVATE_GENERATED_RESPONSE_RECORD_PATH)
    response_items = _read_jsonl(PRIVATE_GENERATED_RESPONSE_ITEMS_PATH)
    non_actionable = _read_jsonl(PRIVATE_NON_ACTIONABLE_QUEUE_PATH)
    _require_equal("source template rows", len(source_template), 48)
    _require_equal("source threshold rows", len(source_threshold_rows), 48)
    _require_equal("response record rows", len(response_record.get("response_items", [])), 48)
    _require_equal("response item rows", len(response_items), 48)
    _require_equal("non actionable rows", len(non_actionable), 48)
    template_packets = {row.get("source_diagnostic_packet_item_id") for row in source_template}
    threshold_packets = {row.get("source_diagnostic_packet_item_id") for row in source_threshold_rows}
    response_packets = {row.get("source_diagnostic_packet_item_id") for row in response_items}
    _require_equal("template/threshold packet sets", template_packets, threshold_packets)
    _require_equal("template/response packet sets", template_packets, response_packets)
    diagnostic_counts = Counter(row.get("diagnostic_kind") for row in response_items)
    _require_equal(f"private diagnostic kind {SOURCE_REFERENCE_DIAGNOSTIC_KIND}", diagnostic_counts[SOURCE_REFERENCE_DIAGNOSTIC_KIND], 40)
    _require_equal(f"private diagnostic kind {FORMULA_MAPPING_DIAGNOSTIC_KIND}", diagnostic_counts[FORMULA_MAPPING_DIAGNOSTIC_KIND], 8)
    for row in response_items:
        _require_equal("response actor", row.get("response_actor_role"), "authorized_delegate_codex")
        _require_equal("authorization source", row.get("authorization_source"), AUTHORIZATION_SOURCE)
        _require_equal("response status", row.get("response_status"), "valid_diagnostic_response_generated")
        _require_true("valid response", row.get("valid_diagnostic_response"))
        _require_true("generated by authorized delegate", row.get("generated_by_authorized_delegate"))
        _require_false("actionable", row.get("actionable_resolution_ready"))
        _require_false("binding", row.get("binding_ready_after_response"))
        _require_false("comparison", row.get("comparison_retry_ready_after_response"))
        _require_false("raw comparison", row.get("raw_to_processed_value_comparison_performed_by_this_phase"))
        _require_false("business consistency", row.get("business_value_consistency_verified"))
        _require_false("public commit", row.get("public_commit_allowed"))
    for row in non_actionable:
        _require_true("non actionable valid", row.get("valid_diagnostic_response"))
        _require_false("non actionable actionable", row.get("actionable_resolution_ready"))
        _require_false("non actionable binding", row.get("binding_ready_after_response"))
        _require_false("non actionable retry", row.get("comparison_retry_ready_after_response"))
        _require_false("non actionable public", row.get("public_commit_allowed"))
    tracked = set(_git_output(["ls-files", "KMFA"]).splitlines())
    for path in private_paths:
        if path.as_posix() in tracked:
            raise ValidationError(f"private artifact is tracked: {path}")


def validate(*, require_private_generated_response: bool = False) -> dict[str, Any]:
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
    _check_public_artifacts()
    _check_no_raw_private_files_tracked()
    if require_private_generated_response:
        _check_private_artifacts()
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-private-generated-response", action="store_true")
    args = parser.parse_args(argv)
    try:
        validate(require_private_generated_response=args.require_private_generated_response)
    except ValidationError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print("PASS: validated V014 generated owner/agent diagnostic response import after blocker threshold")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
