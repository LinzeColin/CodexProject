#!/usr/bin/env python3
"""Validate diagnostic-packet evidence after blocked handoff."""

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

from KMFA.tools.v014_residual_difference_authorized_source_reference_or_exclusion_application_diagnostic_packet_after_blocked_handoff import (  # noqa: E402
    ACCEPTANCE_ID,
    DECISION,
    DIAGNOSTIC_CONCLUSION,
    EXPECTED_DIAGNOSTIC_TRACK_COUNTS,
    FORMULA_MAPPING_INTAKE_TRACK,
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
    PRIVATE_DIAGNOSTIC_PACKET_PATH,
    PRIVATE_DIAGNOSTIC_QUEUE_PATH,
    PRIVATE_DIAGNOSTIC_REPORT_PATH,
    PRIVATE_SLOT_KEY,
    REPORT_PATH,
    RISK_REGISTER_PATH,
    ROLLBACK_PATH,
    SOURCE_BLOCKED_HANDOFF_GO_NO_GO_PATH,
    SOURCE_BLOCKED_HANDOFF_MANIFEST_PATH,
    SOURCE_BLOCKED_HANDOFF_MATRIX_PATH,
    SOURCE_BLOCKED_HANDOFF_SUMMARY_PATH,
    SOURCE_PRIVATE_BLOCKED_HANDOFF_DIAGNOSTIC_PATH,
    SOURCE_PRIVATE_BLOCKED_HANDOFF_PACKET_PATH,
    SOURCE_PRIVATE_BLOCKED_HANDOFF_RECORDS_PATH,
    SOURCE_REFERENCE_INTAKE_TRACK,
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
    re.compile(r"\.(xlsx|xlsm|xls|zip|pdf|sqlite|sqlite3|db)\b", re.IGNORECASE),
    re.compile(r"sha256:[0-9a-f]{64}"),
    re.compile(r'"[0-9a-f]{64}"'),
    re.compile(
        r'"(?:target_slot_id|raw_file_name|archive_member_name|sheet_name|cell_address|raw_value|'
        r"normalized_decimal|context_text|numeric_value_fingerprint|processed_value_fingerprint|"
        r"raw_candidate_fingerprint|value_fingerprint|raw_candidate_record_ref_hash|source_record_ref_hash|"
        + PRIVATE_SLOT_KEY
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
        "source_blocked_handoff_public_artifacts_read_by_this_phase",
        "source_blocked_handoff_manifest_read_by_this_phase",
        "source_blocked_handoff_go_no_go_read_by_this_phase",
        "source_blocked_handoff_matrix_read_by_this_phase",
        "source_private_blocked_handoff_diagnostic_read_by_this_phase",
        "source_private_blocked_handoff_records_read_by_this_phase",
        "source_private_blocked_handoff_packet_read_by_this_phase",
        "private_diagnostic_packet_written_by_this_phase",
        "private_diagnostic_queue_written_by_this_phase",
        "private_diagnostic_report_written_by_this_phase",
    ):
        _require_true(f"raw_boundary.{key}", raw_boundary.get(key))
    for key, value in raw_boundary.items():
        if key.startswith("raw_inbox_") or key.endswith("_mutated_by_this_phase"):
            _require_false(f"raw_boundary.{key}", value)
    for key in (
        "authoritative_binding_applied_by_this_phase",
        "raw_candidate_fingerprint_bound_by_this_phase",
        "raw_to_processed_value_comparison_performed_by_this_phase",
        "source_private_blocked_handoff_diagnostic_mutated_by_this_phase",
        "source_private_blocked_handoff_records_mutated_by_this_phase",
        "source_private_blocked_handoff_packet_mutated_by_this_phase",
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
    _require_equal("summary.diagnostic_conclusion", summary.get("diagnostic_conclusion"), DIAGNOSTIC_CONCLUSION)
    _require_equal("summary.source go/no-go", summary.get("source_go_no_go_decision"), "NO_GO")
    _require_equal("summary.source matrix", summary.get("source_matrix_check_fail_count"), 0)
    _require_equal("summary.source private rows", summary.get("source_private_blocked_handoff_record_count"), 48)
    _require_equal("summary.source blocked handoff", summary.get("source_blocked_handoff_item_count"), 48)
    _require_equal("summary.source owner actions", summary.get("source_owner_action_item_count"), 48)
    _require_true("summary.source blockers remain", summary.get("source_authorized_resolution_blockers_remain"))
    _require_true("summary.packet prepared", summary.get("diagnostic_packet_prepared_by_this_phase"))
    _require_true("summary.external ready", summary.get("external_agent_private_packet_ready"))
    _require_equal("summary.diagnostic items", summary.get("diagnostic_packet_item_count"), 48)
    _require_equal("summary.external items", summary.get("external_agent_private_packet_item_count"), 48)
    _require_equal(
        "summary.source ref diagnostic items",
        summary.get("source_reference_or_owner_exclusion_diagnostic_item_count"),
        40,
    )
    _require_equal("summary.formula diagnostic items", summary.get("formula_or_non_numeric_mapping_diagnostic_item_count"), 8)
    _require_equal("summary.auto resolution", summary.get("safe_auto_resolution_available_count"), 0)
    _require_equal("summary.binding ready", summary.get("binding_ready_after_diagnostic_packet_count"), 0)
    _require_equal("summary.retry ready", summary.get("comparison_retry_ready_after_diagnostic_packet_count"), 0)
    _require_equal("summary.unresolved differences", summary.get("unresolved_difference_count"), 72)
    _require_true("summary.private queue ignored", summary.get("private_diagnostic_queue_gitignored"))
    _require_true("summary.source private records ignored", summary.get("source_private_blocked_handoff_records_gitignored"))
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
    _check_raw_boundary(summary.get("raw_boundary", {}))
    _check_public_safety(summary.get("public_safety", {}))
    _require_equal("matrix phase", matrix.get("phase_id"), PHASE_ID)
    _require_equal("matrix check count", matrix.get("check_count"), 15)
    _require_equal("matrix pass count", matrix.get("check_pass_count"), 15)
    _require_equal("matrix fail count", matrix.get("check_fail_count"), 0)
    _require_equal("go/no-go phase", go_no_go.get("phase_id"), PHASE_ID)
    _require_equal("go/no-go decision", go_no_go.get("decision"), DECISION)
    _require_equal("manifest phase", manifest.get("phase_id"), PHASE_ID)
    _require_equal("manifest summary", manifest.get("summary"), summary)
    _require_equal("manifest matrix", manifest.get("matrix"), matrix)
    _require_equal("manifest go/no-go", manifest.get("go_no_go_report"), go_no_go)


def _check_private_packet() -> None:
    for path in (
        PRIVATE_DIAGNOSTIC_PACKET_PATH,
        PRIVATE_DIAGNOSTIC_QUEUE_PATH,
        PRIVATE_DIAGNOSTIC_REPORT_PATH,
        SOURCE_PRIVATE_BLOCKED_HANDOFF_DIAGNOSTIC_PATH,
        SOURCE_PRIVATE_BLOCKED_HANDOFF_RECORDS_PATH,
        SOURCE_PRIVATE_BLOCKED_HANDOFF_PACKET_PATH,
    ):
        if not _git_check_ignored(path):
            raise ValidationError(f"private path is not git-ignored: {path}")
    packet = _read_json(PRIVATE_DIAGNOSTIC_PACKET_PATH)
    _require_equal("private packet phase", packet.get("phase_id"), PHASE_ID)
    _require_equal("private packet items", packet.get("diagnostic_packet_item_count"), 48)
    _require_equal("private external items", packet.get("external_agent_private_packet_item_count"), 48)
    _require_equal("private binding ready", packet.get("binding_ready_after_diagnostic_packet_count"), 0)
    _require_equal("private retry ready", packet.get("comparison_retry_ready_after_diagnostic_packet_count"), 0)
    records = _read_jsonl(PRIVATE_DIAGNOSTIC_QUEUE_PATH)
    _require_equal("private diagnostic record count", len(records), 48)
    track_counts = Counter(row.get("intake_track") for row in records)
    _require_equal("private diagnostic track counts", dict(track_counts), EXPECTED_DIAGNOSTIC_TRACK_COUNTS)
    for index, row in enumerate(records, start=1):
        _require_equal(f"record {index} phase", row.get("phase_id"), PHASE_ID)
        _require_equal(
            f"record {index} status",
            row.get("diagnostic_packet_status"),
            "waiting_for_authorized_resolution_input",
        )
        _require_true(f"record {index} action", row.get("owner_or_external_agent_action_required"))
        _require_false(f"record {index} auto", row.get("safe_auto_resolution_available"))
        _require_false(f"record {index} binding", row.get("binding_ready_after_diagnostic_packet"))
        _require_false(f"record {index} retry", row.get("comparison_retry_ready_after_diagnostic_packet"))
        _require_false(f"record {index} public", row.get("public_commit_allowed"))


def _check_source_artifacts() -> None:
    source_summary = _read_json(SOURCE_BLOCKED_HANDOFF_SUMMARY_PATH)
    source_go_no_go = _read_json(SOURCE_BLOCKED_HANDOFF_GO_NO_GO_PATH)
    source_matrix = _read_json(SOURCE_BLOCKED_HANDOFF_MATRIX_PATH)
    source_diagnostic = _read_json(SOURCE_PRIVATE_BLOCKED_HANDOFF_DIAGNOSTIC_PATH)
    source_rows = _read_jsonl(SOURCE_PRIVATE_BLOCKED_HANDOFF_RECORDS_PATH)
    _read_json(SOURCE_BLOCKED_HANDOFF_MANIFEST_PATH)
    _require_equal("source decision", source_go_no_go.get("decision"), "NO_GO")
    _require_equal("source matrix fail", source_matrix.get("check_fail_count"), 0)
    _require_equal("source blocked handoff", source_summary.get("blocked_handoff_item_count"), 48)
    _require_equal("source owner actions", source_summary.get("owner_action_item_count"), 48)
    _require_true("source blockers remain", source_summary.get("authorized_resolution_blockers_remain"))
    _require_equal("source private diagnostic items", source_diagnostic.get("blocked_handoff_item_count"), 48)
    _require_equal("source private rows", len(source_rows), 48)
    track_counts = Counter(row.get("intake_track") for row in source_rows)
    _require_equal("source track counts", dict(track_counts), EXPECTED_DIAGNOSTIC_TRACK_COUNTS)
    _require_equal("source ref track count", track_counts[SOURCE_REFERENCE_INTAKE_TRACK], 40)
    _require_equal("formula track count", track_counts[FORMULA_MAPPING_INTAKE_TRACK], 8)
    for index, row in enumerate(source_rows, start=1):
        _require_equal(
            f"source record {index} status",
            row.get("handoff_action_status"),
            "blocked_waiting_for_authorized_resolution_application",
        )
        _require_false(f"source record {index} public", row.get("public_commit_allowed"))


def validate(*, require_private_packet: bool = False) -> dict[str, Any]:
    summary = _read_json(SUMMARY_PATH)
    manifest = _read_json(MANIFEST_PATH)
    go_no_go = _read_json(GO_NO_GO_PATH)
    matrix = _read_json(MATRIX_PATH)
    for expected, metadata in (
        (summary, _read_json(METADATA_SUMMARY_PATH)),
        (manifest, _read_json(METADATA_MANIFEST_PATH)),
        (go_no_go, _read_json(METADATA_GO_NO_GO_PATH)),
        (matrix, _read_json(METADATA_MATRIX_PATH)),
    ):
        _require_equal(f"metadata copy {metadata.get('record_type')}", metadata, expected)
    _check_summary(summary, matrix, go_no_go, manifest)
    _check_source_artifacts()
    _check_public_artifacts()
    _check_no_raw_private_files_tracked()
    if require_private_packet:
        _check_private_packet()
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-private-packet", action="store_true")
    args = parser.parse_args()
    manifest = validate(require_private_packet=args.require_private_packet)
    summary = manifest["summary"]
    print(
        "PASS: validated V014 authorized source reference or exclusion application "
        "diagnostic packet after blocked handoff "
        f"decision={summary['decision']} packet={summary['diagnostic_packet_item_count']} "
        f"external_ready={summary['external_agent_private_packet_ready']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
