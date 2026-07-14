#!/usr/bin/env python3
"""Validate owner/agent diagnostic readiness recheck after intake."""

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

from KMFA.tools.v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_diagnostic_readiness_recheck_after_intake import (  # noqa: E402
    ACCEPTANCE_ID,
    DECISION,
    EXPECTED_READINESS_BLOCKER_COUNTS,
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
    PRIVATE_BLOCKER_QUEUE_PATH,
    PRIVATE_READINESS_DIAGNOSTIC_PATH,
    PRIVATE_READINESS_REPORT_PATH,
    READINESS_CONCLUSION,
    REPORT_PATH,
    RISK_REGISTER_PATH,
    ROLLBACK_PATH,
    SOURCE_PRIVATE_DIAGNOSTIC_PATH,
    SOURCE_PRIVATE_PENDING_QUEUE_PATH,
    SOURCE_PRIVATE_REPORT_PATH,
    SOURCE_PRIVATE_RESPONSE_TEMPLATE_PATH,
    SOURCE_REFERENCE_DIAGNOSTIC_KIND,
    STATUS,
    SUMMARY_PATH,
    TASK_ID,
    TEST_RESULTS_PATH,
    VERSION,
    source_intake,
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
        r"raw_candidate_fingerprint|value_fingerprint|raw_candidate_record_ref_hash|source_record_ref_hash|"
        + source_intake.source_packet.PRIVATE_SLOT_KEY
        + r')"',
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
        "source_public_intake_summary_read_by_this_phase",
        "source_public_intake_manifest_read_by_this_phase",
        "source_public_intake_go_no_go_read_by_this_phase",
        "source_public_intake_matrix_read_by_this_phase",
        "source_private_response_template_read_by_this_phase",
        "source_private_pending_queue_read_by_this_phase",
        "source_private_diagnostic_read_by_this_phase",
        "source_private_report_existence_checked_by_this_phase",
        "private_readiness_diagnostic_written_by_this_phase",
        "private_readiness_blocker_queue_written_by_this_phase",
        "private_readiness_report_written_by_this_phase",
    ):
        _require_true(f"raw_boundary.{key}", raw_boundary.get(key))
    for key, value in raw_boundary.items():
        if key.startswith("raw_inbox_") or key.endswith("_mutated_by_this_phase"):
            _require_false(f"raw_boundary.{key}", value)
    for key in (
        "source_private_response_template_mutated_by_this_phase",
        "source_private_pending_queue_mutated_by_this_phase",
        "source_private_diagnostic_mutated_by_this_phase",
        "source_private_report_mutated_by_this_phase",
        "owner_or_agent_response_supplied_by_this_phase",
        "valid_diagnostic_response_supplied_by_this_phase",
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
    _require_equal("summary.readiness_conclusion", summary.get("readiness_conclusion"), READINESS_CONCLUSION)
    _require_equal("summary.source_phase_id", summary.get("source_phase_id"), source_intake.PHASE_ID)
    _require_equal("summary.source_manifest_phase_id", summary.get("source_manifest_phase_id"), source_intake.PHASE_ID)
    _require_equal("summary.source_go_no_go_decision", summary.get("source_go_no_go_decision"), "NO_GO")
    _require_equal("summary.source_matrix_check_fail_count", summary.get("source_matrix_check_fail_count"), 0)
    _require_equal("summary.source template", summary.get("source_private_response_template_item_count"), 48)
    _require_equal("summary.source pending", summary.get("source_private_pending_queue_item_count"), 48)
    _require_equal("summary.source pending responses", summary.get("source_pending_diagnostic_response_count"), 48)
    _require_equal("summary.source valid", summary.get("source_valid_diagnostic_response_count"), 0)
    _require_equal("summary.source actionable", summary.get("source_actionable_resolution_count"), 0)
    _require_equal("summary.source binding ready", summary.get("source_binding_ready_after_intake_count"), 0)
    _require_equal("summary.source retry ready", summary.get("source_comparison_retry_ready_after_intake_count"), 0)
    _require_true("summary.readiness performed", summary.get("diagnostic_readiness_recheck_performed"))
    _require_equal("summary.ready count", summary.get("diagnostic_response_ready_count"), 0)
    _require_equal("summary.blocker count", summary.get("diagnostic_response_blocker_count"), 48)
    _require_equal("summary.blocker queue", summary.get("private_readiness_blocker_queue_item_count"), 48)
    _require_equal("summary.pending count", summary.get("pending_diagnostic_response_count"), 48)
    _require_equal("summary.valid count", summary.get("valid_diagnostic_response_count"), 0)
    _require_equal("summary.invalid count", summary.get("invalid_diagnostic_response_count"), 0)
    _require_equal("summary.actionable", summary.get("actionable_resolution_count"), 0)
    _require_equal("summary.source ref blockers", summary.get("source_reference_or_owner_exclusion_readiness_blocker_count"), 40)
    _require_equal("summary.formula blockers", summary.get("formula_or_non_numeric_mapping_readiness_blocker_count"), 8)
    _require_equal("summary.binding ready", summary.get("binding_ready_after_readiness_recheck_count"), 0)
    _require_equal("summary.retry ready", summary.get("comparison_retry_ready_after_readiness_recheck_count"), 0)
    _require_equal("summary.unresolved differences", summary.get("unresolved_difference_count"), 72)
    for key in (
        "private_readiness_diagnostic_written",
        "private_readiness_blocker_queue_written",
        "private_readiness_report_written",
        "private_readiness_diagnostic_gitignored",
        "private_readiness_blocker_queue_gitignored",
        "private_readiness_report_gitignored",
        "source_private_response_template_gitignored",
        "source_private_pending_queue_gitignored",
        "source_private_diagnostic_gitignored",
        "source_private_report_gitignored",
    ):
        _require_true(f"summary.{key}", summary.get(key))
    for key in (
        "owner_or_agent_valid_response_supplied",
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
    _require_equal("matrix.check_count", matrix.get("check_count"), 15)
    _require_equal("matrix.check_pass_count", matrix.get("check_pass_count"), 15)
    _require_equal("matrix.check_fail_count", matrix.get("check_fail_count"), 0)
    checks = {row.get("check_code"): row.get("status") for row in matrix.get("checks", []) if isinstance(row, dict)}
    for code in (
        "source_intake_loaded",
        "source_go_no_go_preserved",
        "source_matrix_clean",
        "source_template_loaded",
        "source_pending_queue_loaded",
        "readiness_recheck_performed",
        "no_ready_diagnostic_response",
        "all_diagnostic_responses_blocked",
        "no_valid_diagnostic_response",
        "no_actionable_resolution",
        "diagnostic_kind_counts_locked",
        "no_binding_or_retry_ready_after_recheck",
        "private_readiness_outputs_ignored",
        "raw_inbox_untouched",
        "downstream_gates_closed",
    ):
        _require_equal(f"matrix.{code}", checks.get(code), "PASS")

    _require_equal("go_no_go.phase_id", go_no_go.get("phase_id"), PHASE_ID)
    _require_equal("go_no_go.decision", go_no_go.get("decision"), DECISION)
    _require_equal("go_no_go.diagnostic_response_ready_count", go_no_go.get("diagnostic_response_ready_count"), 0)
    _require_equal("go_no_go.diagnostic_response_blocker_count", go_no_go.get("diagnostic_response_blocker_count"), 48)
    _require_equal("go_no_go.pending_diagnostic_response_count", go_no_go.get("pending_diagnostic_response_count"), 48)
    _require_equal("go_no_go.valid_diagnostic_response_count", go_no_go.get("valid_diagnostic_response_count"), 0)
    _require_equal("go_no_go.actionable_resolution_count", go_no_go.get("actionable_resolution_count"), 0)
    _require_equal("go_no_go.binding_ready_after_readiness_recheck_count", go_no_go.get("binding_ready_after_readiness_recheck_count"), 0)
    _require_equal("go_no_go.comparison_retry_ready_after_readiness_recheck_count", go_no_go.get("comparison_retry_ready_after_readiness_recheck_count"), 0)
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
    for path in (
        SOURCE_PRIVATE_RESPONSE_TEMPLATE_PATH,
        SOURCE_PRIVATE_PENDING_QUEUE_PATH,
        SOURCE_PRIVATE_DIAGNOSTIC_PATH,
        SOURCE_PRIVATE_REPORT_PATH,
        PRIVATE_READINESS_DIAGNOSTIC_PATH,
        PRIVATE_BLOCKER_QUEUE_PATH,
        PRIVATE_READINESS_REPORT_PATH,
    ):
        if not path.exists():
            raise ValidationError(f"missing private artifact: {path}")
        if not _git_check_ignored(path):
            raise ValidationError(f"private artifact is not git-ignored: {path}")
    source_template_rows = _read_jsonl(SOURCE_PRIVATE_RESPONSE_TEMPLATE_PATH)
    source_pending_rows = _read_jsonl(SOURCE_PRIVATE_PENDING_QUEUE_PATH)
    blocker_rows = _read_jsonl(PRIVATE_BLOCKER_QUEUE_PATH)
    _require_equal("source private template rows", len(source_template_rows), 48)
    _require_equal("source private pending rows", len(source_pending_rows), 48)
    _require_equal("private readiness blocker rows", len(blocker_rows), 48)
    diagnostic_counts = Counter(row.get("diagnostic_kind") for row in blocker_rows)
    _require_equal(
        f"private diagnostic kind {SOURCE_REFERENCE_DIAGNOSTIC_KIND}",
        diagnostic_counts.get(SOURCE_REFERENCE_DIAGNOSTIC_KIND),
        EXPECTED_READINESS_BLOCKER_COUNTS[SOURCE_REFERENCE_DIAGNOSTIC_KIND],
    )
    _require_equal(
        f"private diagnostic kind {FORMULA_MAPPING_DIAGNOSTIC_KIND}",
        diagnostic_counts.get(FORMULA_MAPPING_DIAGNOSTIC_KIND),
        EXPECTED_READINESS_BLOCKER_COUNTS[FORMULA_MAPPING_DIAGNOSTIC_KIND],
    )
    for item in blocker_rows:
        _require_equal("blocker code", item.get("blocker_code"), "missing_valid_owner_or_agent_diagnostic_response")
        _require_equal("blocker response status", item.get("response_status"), "pending_owner_or_external_agent")
        _require_false("blocker valid diagnostic response", item.get("valid_diagnostic_response"))
        _require_false("blocker actionable resolution", item.get("actionable_resolution_ready"))
        _require_false("blocker binding ready", item.get("binding_ready_after_response"))
        _require_false("blocker retry ready", item.get("comparison_retry_ready_after_response"))
        _require_false("blocker public commit allowed", item.get("public_commit_allowed"))


def validate(*, require_private_readiness: bool = False) -> dict[str, Any]:
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
    if require_private_readiness:
        _check_private_artifacts()
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-private-readiness", action="store_true")
    args = parser.parse_args()
    try:
        validate(require_private_readiness=args.require_private_readiness)
    except ValidationError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(
        "PASS: validated V014 authorized source reference or exclusion application "
        "owner/agent diagnostic readiness recheck after intake"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
