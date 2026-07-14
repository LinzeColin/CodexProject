#!/usr/bin/env python3
"""Validate KMFA v0.1.4 private blocker resolution packet evidence."""

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

from KMFA.tools.v014_processed_value_source_map_completion_private_blocker_resolution_packet import (  # noqa: E402
    ACCEPTANCE_ID,
    DECISION,
    DIAGNOSTIC_CONCLUSION,
    GO_NO_GO_PATH,
    GO_NO_GO_RECORD_PATH,
    MANIFEST_PATH,
    METADATA_GO_NO_GO_PATH,
    METADATA_MANIFEST_PATH,
    METADATA_RESOLUTION_TRACKS_PATH,
    METADATA_SUMMARY_PATH,
    NEXT_REQUIRED_INPUT,
    PHASE_ID,
    PRIVATE_DIAGNOSTIC_PATH,
    PRIVATE_PACKET_MD_PATH,
    PRIVATE_PACKET_PATH,
    PRIVATE_QUEUE_PATH,
    REPORT_PATH,
    RESOLUTION_TRACKS_PATH,
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
    RESOLUTION_TRACKS_PATH,
    REPORT_PATH,
    GO_NO_GO_RECORD_PATH,
    TEST_RESULTS_PATH,
    RISK_REGISTER_PATH,
    ROLLBACK_PATH,
    METADATA_SUMMARY_PATH,
    METADATA_MANIFEST_PATH,
    METADATA_GO_NO_GO_PATH,
    METADATA_RESOLUTION_TRACKS_PATH,
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
SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")


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
    _require_true(
        "raw_boundary.private_blocker_report_read_performed_by_this_phase",
        raw_boundary.get("private_blocker_report_read_performed_by_this_phase"),
    )
    _require_true(
        "raw_boundary.private_blocker_records_read_performed_by_this_phase",
        raw_boundary.get("private_blocker_records_read_performed_by_this_phase"),
    )
    _require_true(
        "raw_boundary.private_resolution_packet_written_by_this_phase",
        raw_boundary.get("private_resolution_packet_written_by_this_phase"),
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


def _check_private_packet(summary: dict[str, Any]) -> None:
    packet = _read_json(PRIVATE_PACKET_PATH)
    diagnostic = _read_json(PRIVATE_DIAGNOSTIC_PATH)
    queue = _read_jsonl(PRIVATE_QUEUE_PATH)
    markdown = PRIVATE_PACKET_MD_PATH.read_text(encoding="utf-8") if PRIVATE_PACKET_MD_PATH.exists() else ""
    _require_equal("private packet.phase_id", packet.get("phase_id"), PHASE_ID)
    _require_equal("private diagnostic.phase_id", diagnostic.get("phase_id"), PHASE_ID)
    _require_equal("private packet.queue_count", packet.get("private_resolution_queue_count"), 113)
    _require_equal("private diagnostic.queue_count", diagnostic.get("private_resolution_queue_count"), 113)
    _require_equal("private queue length", len(queue), 113)
    allowed_statuses = {
        "requires_corrected_source_or_owner_exclusion",
        "requires_private_disambiguation",
    }
    for index, row in enumerate(queue):
        if row.get("resolution_queue_status") not in allowed_statuses:
            raise ValidationError(f"private queue row {index} has invalid status")
        fingerprint = row.get("value_fingerprint")
        if not isinstance(fingerprint, str) or not SHA256.fullmatch(fingerprint):
            raise ValidationError(f"private queue row {index} has invalid fingerprint")
        _require_false(f"private queue row {index}.resolution_applied", row.get("resolution_applied"))
    if "Private Blocker Resolution Packet" not in markdown:
        raise ValidationError("private markdown packet missing title")
    _check_raw_boundary(packet.get("raw_boundary", {}))
    for path in (PRIVATE_PACKET_PATH, PRIVATE_QUEUE_PATH, PRIVATE_DIAGNOSTIC_PATH, PRIVATE_PACKET_MD_PATH):
        if not path.exists():
            raise ValidationError(f"missing private artifact: {path}")
        if not _git_check_ignored(path):
            raise ValidationError(f"private artifact is not gitignored: {path}")
        _require_equal(f"{path}.tracked", _git_output(["ls-files", path.as_posix()]), "")


def validate(*, require_private_packet: bool = False) -> dict[str, Any]:
    summary = _read_json(SUMMARY_PATH)
    manifest = _read_json(MANIFEST_PATH)
    go_no_go = _read_json(GO_NO_GO_PATH)
    tracks = _read_json(RESOLUTION_TRACKS_PATH)
    _require_equal("metadata summary", _read_json(METADATA_SUMMARY_PATH), summary)
    _require_equal("metadata manifest", _read_json(METADATA_MANIFEST_PATH), manifest)
    _require_equal("metadata go/no-go", _read_json(METADATA_GO_NO_GO_PATH), go_no_go)
    _require_equal("metadata resolution tracks", _read_json(METADATA_RESOLUTION_TRACKS_PATH), tracks)

    _require_equal("summary.phase_id", summary.get("phase_id"), PHASE_ID)
    _require_equal("summary.task_id", summary.get("task_id"), TASK_ID)
    _require_equal("summary.acceptance_id", summary.get("acceptance_id"), ACCEPTANCE_ID)
    _require_equal("summary.version", summary.get("version"), VERSION)
    _require_equal("summary.status", summary.get("status"), STATUS)
    _require_equal("summary.decision", summary.get("decision"), DECISION)
    _require_equal("summary.diagnostic_conclusion", summary.get("diagnostic_conclusion"), DIAGNOSTIC_CONCLUSION)
    _require_equal("summary.previous_required_input", summary.get("previous_required_input"), "private_blocker_resolution_packet_before_any_full_raw_to_processed_reconciliation")
    _require_true("summary.previous_required_input_resolved", summary.get("previous_required_input_resolved_by_this_phase"))
    _require_equal("summary.next_required_input", summary.get("next_required_input"), NEXT_REQUIRED_INPUT)
    _require_true("summary.blocker_resolution_packet_prepared", summary.get("blocker_resolution_packet_prepared"))
    _require_equal("summary.blocker_class_count", summary.get("blocker_class_count"), 5)
    _require_equal("summary.resolution_track_count", summary.get("resolution_track_count"), 5)
    _require_equal("summary.owner_or_agent_action_required_track_count", summary.get("owner_or_agent_action_required_track_count"), 4)
    _require_equal("summary.auto_resolution_allowed_track_count", summary.get("auto_resolution_allowed_track_count"), 0)
    _require_equal("summary.private_blocker_record_count", summary.get("private_blocker_record_count"), 113)
    _require_equal("summary.private_resolution_queue_count", summary.get("private_resolution_queue_count"), 113)
    _require_equal(
        "summary.requires_corrected_source_or_owner_exclusion",
        summary["private_resolution_queue_status_counts"].get("requires_corrected_source_or_owner_exclusion"),
        36,
    )
    _require_equal(
        "summary.requires_private_disambiguation",
        summary["private_resolution_queue_status_counts"].get("requires_private_disambiguation"),
        77,
    )
    _require_equal("summary.confirmed_value_mismatch_count", summary.get("confirmed_value_mismatch_count"), 0)
    _require_false("summary.confirmed_mismatch_report_required_now", summary.get("confirmed_mismatch_report_required_now"))
    _require_false("summary.repeated_cross_validation_mismatch_confirmed", summary.get("repeated_cross_validation_mismatch_confirmed"))
    _require_false("summary.final_goal_closeout_difference_report_required_now", summary.get("final_goal_closeout_difference_report_required_now"))
    _require_true(
        "summary.final_goal_closeout_difference_report_required_if_repeated",
        summary.get("final_goal_closeout_difference_report_required_if_repeated"),
    )
    for key in (
        "resolution_applied_by_this_phase",
        "raw_to_processed_value_comparison_performed_by_this_phase",
        "full_raw_to_processed_reconciliation_complete",
        "business_value_consistency_verified",
        "lineage_full_check_complete",
        "formal_report_allowed",
        "github_upload_performed",
        "app_reinstall_performed",
        "business_execution_performed",
    ):
        _require_false(f"summary.{key}", summary.get(key))
    for key in (
        "private_packet_written",
        "private_packet_gitignored",
        "private_queue_written",
        "private_queue_gitignored",
        "private_diagnostic_written",
        "private_diagnostic_gitignored",
        "private_packet_markdown_written",
        "private_packet_markdown_gitignored",
    ):
        _require_true(f"summary.{key}", summary.get(key))

    _require_equal("tracks.resolution_track_count", tracks.get("resolution_track_count"), 5)
    _require_equal("tracks.owner_or_agent_action_required_track_count", tracks.get("owner_or_agent_action_required_track_count"), 4)
    _require_equal("tracks.auto_resolution_allowed_track_count", tracks.get("auto_resolution_allowed_track_count"), 0)
    _require_true("tracks.all_resolution_tracks_prepared", tracks.get("all_resolution_tracks_prepared"))
    _require_false("tracks.any_resolution_applied_by_this_phase", tracks.get("any_resolution_applied_by_this_phase"))
    resolution_tracks = tracks.get("resolution_tracks")
    if not isinstance(resolution_tracks, list) or len(resolution_tracks) != 5:
        raise ValidationError("resolution tracks must contain five rows")
    for track in resolution_tracks:
        _require_false(f"{track.get('blocker_code')}.auto_resolution_allowed", track.get("auto_resolution_allowed"))
        _require_false(
            f"{track.get('blocker_code')}.resolution_applied_by_this_phase",
            track.get("resolution_applied_by_this_phase"),
        )
        _require_false(
            f"{track.get('blocker_code')}.delivery_claim_allowed_after_this_phase",
            track.get("delivery_claim_allowed_after_this_phase"),
        )
    _require_false("tracks.business_value_consistency_verified", tracks.get("business_value_consistency_verified"))
    _require_equal("go_no_go.decision", go_no_go.get("decision"), DECISION)
    _require_equal("go_no_go.blocked_until", go_no_go.get("blocked_until"), NEXT_REQUIRED_INPUT)
    _require_false("go_no_go.business_value_consistency_verified", go_no_go.get("business_value_consistency_verified"))
    _require_false("go_no_go.github_upload_performed", go_no_go.get("github_upload_performed"))
    _require_false("go_no_go.app_reinstall_performed", go_no_go.get("app_reinstall_performed"))
    _require_false("go_no_go.business_execution_performed", go_no_go.get("business_execution_performed"))
    _require_equal("manifest.summary", manifest.get("summary"), summary)
    _require_equal("manifest.go_no_go", manifest.get("go_no_go"), go_no_go)
    _require_equal("manifest.resolution_tracks", manifest.get("resolution_tracks"), tracks)
    _check_raw_boundary(summary.get("raw_boundary", {}))
    _check_public_safety(summary.get("public_safety", {}))
    _check_public_artifacts()
    _check_no_raw_private_files_tracked()
    if require_private_packet:
        _check_private_packet(summary)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-private-packet", action="store_true")
    args = parser.parse_args()
    manifest = validate(require_private_packet=args.require_private_packet)
    print(
        "PASS: KMFA v0.1.4 private blocker resolution packet artifacts validated "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"tracks={manifest['summary']['resolution_track_count']}, "
        f"queue={manifest['summary']['private_resolution_queue_count']})"
    )


if __name__ == "__main__":
    main()
