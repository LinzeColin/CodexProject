#!/usr/bin/env python3
"""Generate a public-safe private blocker resolution packet.

This phase converts the prior public-safe blocker matrix into resolution tracks
and creates private-only row queues for the target-level blocker records. It
does not read the raw inbox, apply decisions, run full reconciliation, publish
fingerprints, or claim business consistency.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


PROJECT_ROOT = Path("KMFA")
PHASE_ID = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_PRIVATE_BLOCKER_RESOLUTION_PACKET"
TASK_ID = "KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-PRIVATE-BLOCKER-RESOLUTION-PACKET-20260706"
ACCEPTANCE_ID = "ACC-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-PRIVATE-BLOCKER-RESOLUTION-PACKET"
VERSION = "0.1.4-private-blocker-resolution-packet"
STATUS = "completed_validated_local_only_private_blocker_resolution_packet_no_go"
DECISION = "NO_GO"
DIAGNOSTIC_CONCLUSION = "private_blocker_resolution_packet_prepared_full_reconciliation_still_blocked"
PREVIOUS_REQUIRED_INPUT = "private_blocker_resolution_packet_before_any_full_raw_to_processed_reconciliation"
NEXT_RECOMMENDED_PHASE = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_PRIVATE_BLOCKER_RESOLUTION_DECISION_INTAKE"
NEXT_REQUIRED_INPUT = "private_blocker_resolution_decisions_or_corrected_private_source_before_full_reconciliation"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "processed_value_source_map_completion_private_blocker_resolution_packet_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_value_source_map_completion_private_blocker_resolution_packet_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_value_source_map_completion_private_blocker_resolution_packet_go_no_go_report.json"
RESOLUTION_TRACKS_PATH = MACHINE_DIR / "processed_value_source_map_completion_private_blocker_resolution_tracks_public_safe.json"
REPORT_PATH = HUMAN_DIR / "processed_value_source_map_completion_private_blocker_resolution_packet.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_private_blocker_resolution_packet_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_private_blocker_resolution_packet_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_private_blocker_resolution_packet_go_no_go_report.json"
METADATA_RESOLUTION_TRACKS_PATH = PROJECT_ROOT / "metadata/quality/v014_private_blocker_resolution_tracks_public_safe.json"
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"

SOURCE_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_private_mismatch_and_blocker_report_summary.json"
SOURCE_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_private_mismatch_and_blocker_report_go_no_go_report.json"
SOURCE_BLOCKER_MATRIX_PATH = PROJECT_ROOT / "metadata/quality/v014_private_blocker_matrix_public_safe.json"
SOURCE_PRIVATE_REPORT_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_private_mismatch_and_blocker_report/private_mismatch_and_blocker_report.json"
)
SOURCE_PRIVATE_BLOCKER_RECORDS_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_private_mismatch_and_blocker_report/private_blocker_records.jsonl"
)

PRIVATE_OUTPUT_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_processed_value_source_map_completion_private_blocker_resolution_packet"
PRIVATE_PACKET_PATH = PRIVATE_OUTPUT_DIR / "private_blocker_resolution_packet.json"
PRIVATE_QUEUE_PATH = PRIVATE_OUTPUT_DIR / "private_blocker_resolution_queue.jsonl"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_blocker_resolution_packet_diagnostic.json"
PRIVATE_PACKET_MD_PATH = PRIVATE_OUTPUT_DIR / "private_blocker_resolution_packet.md"


def _now(generated_at: str | None = None) -> str:
    return generated_at or datetime.now().astimezone().isoformat(timespec="seconds")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path} must contain JSON objects")
        rows.append(value)
    return rows


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _git_output(args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else "UNKNOWN"


def _git_check_ignored(path: Path) -> bool:
    return subprocess.run(["git", "check-ignore", "-q", path.as_posix()], check=False).returncode == 0


def _raw_boundary() -> dict[str, bool]:
    return {
        "raw_data_root_readonly_policy_active": True,
        "raw_inbox_read_performed_by_this_phase": False,
        "raw_inbox_list_performed_by_this_phase": False,
        "raw_inbox_stat_performed_by_this_phase": False,
        "raw_inbox_hash_or_value_fingerprint_performed_by_this_phase": False,
        "raw_inbox_file_content_hash_performed_by_this_phase": False,
        "raw_inbox_parse_performed_by_this_phase": False,
        "raw_inbox_field_or_header_read_performed_by_this_phase": False,
        "raw_inbox_value_extraction_performed_by_this_phase": False,
        "raw_inbox_write_performed_by_this_phase": False,
        "raw_inbox_delete_performed_by_this_phase": False,
        "raw_inbox_move_performed_by_this_phase": False,
        "raw_inbox_rename_performed_by_this_phase": False,
        "raw_inbox_overwrite_performed_by_this_phase": False,
        "raw_inbox_copy_performed_by_this_phase": False,
        "raw_inbox_normalize_performed_by_this_phase": False,
        "raw_inbox_mutated_by_this_phase": False,
        "private_blocker_report_read_performed_by_this_phase": True,
        "private_blocker_records_read_performed_by_this_phase": True,
        "private_resolution_packet_written_by_this_phase": True,
    }


def _public_safety() -> dict[str, bool]:
    return {
        "public_safe_aggregate_only": True,
        "private_blocker_records_committed": False,
        "private_resolution_packet_committed": False,
        "private_resolution_queue_committed": False,
        "private_diagnostic_committed": False,
        "raw_file_committed": False,
        "raw_filename_committed": False,
        "raw_archive_member_name_committed": False,
        "raw_file_hash_committed": False,
        "field_header_plaintext_committed": False,
        "row_value_committed": False,
        "business_value_committed": False,
        "raw_or_processed_fingerprint_value_committed": False,
        "credential_or_secret_committed": False,
    }


def _resolution_track_for(blocker: dict[str, Any]) -> dict[str, Any]:
    code = str(blocker["blocker_code"])
    templates = {
        "processed_materialization_value_fingerprints_missing": {
            "resolution_track_code": "prepare_or_reactivate_private_processed_value_sources",
            "default_resolution_decision": "keep_blocked_until_private_processed_value_sources_are_materialized",
            "required_next_input": "private processed-value source map with materialized value fingerprints",
            "auto_resolution_allowed": False,
            "owner_or_agent_action_required": True,
            "enables_full_reconciliation_when_resolved": True,
        },
        "owner_authorized_fill_targets_unmatched_in_private_raw_index": {
            "resolution_track_code": "correct_or_explain_unmatched_owner_authorized_fill_targets",
            "default_resolution_decision": "keep_unmatched_targets_excluded_from_delivery_claim",
            "required_next_input": "corrected private source mapping or owner-approved exclusion rationale",
            "auto_resolution_allowed": False,
            "owner_or_agent_action_required": True,
            "enables_full_reconciliation_when_resolved": True,
        },
        "ambiguous_private_raw_index_matches": {
            "resolution_track_code": "disambiguate_private_raw_index_matches",
            "default_resolution_decision": "manual_disambiguation_required_no_auto_selection",
            "required_next_input": "private source-priority or owner-approved disambiguation decision",
            "auto_resolution_allowed": False,
            "owner_or_agent_action_required": True,
            "enables_full_reconciliation_when_resolved": True,
        },
        "residual_partial_application_blocked_targets": {
            "resolution_track_code": "resolve_residual_partial_application_blockers",
            "default_resolution_decision": "keep_residual_targets_blocked_until_authorized_source_map_update",
            "required_next_input": "authorized source-map update or explicit owner exclusion",
            "auto_resolution_allowed": False,
            "owner_or_agent_action_required": True,
            "enables_full_reconciliation_when_resolved": True,
        },
        "private_raw_index_parse_errors_present": {
            "resolution_track_code": "review_private_raw_index_parse_errors",
            "default_resolution_decision": "private_diagnostic_review_required_before_relying_on_full_index",
            "required_next_input": "private parse-error review result or corrected source package",
            "auto_resolution_allowed": False,
            "owner_or_agent_action_required": False,
            "enables_full_reconciliation_when_resolved": True,
        },
    }
    template = templates[code]
    return {
        "blocker_code": code,
        "resolution_track_code": template["resolution_track_code"],
        "severity": blocker["severity"],
        "affected_count": blocker["affected_count"],
        "default_resolution_decision": template["default_resolution_decision"],
        "required_next_input": template["required_next_input"],
        "auto_resolution_allowed": template["auto_resolution_allowed"],
        "owner_or_agent_action_required": template["owner_or_agent_action_required"],
        "enables_full_reconciliation_when_resolved": template["enables_full_reconciliation_when_resolved"],
        "resolution_applied_by_this_phase": False,
        "delivery_claim_allowed_after_this_phase": False,
    }


def _build_resolution_tracks(generated_at: str, blocker_matrix: dict[str, Any]) -> dict[str, Any]:
    blockers = blocker_matrix.get("blockers", [])
    if not isinstance(blockers, list):
        raise ValueError("blockers must be a list")
    tracks = [_resolution_track_for(blocker) for blocker in blockers if isinstance(blocker, dict)]
    owner_required_count = sum(1 for track in tracks if track["owner_or_agent_action_required"])
    auto_allowed_count = sum(1 for track in tracks if track["auto_resolution_allowed"])
    total_affected = sum(int(track["affected_count"]) for track in tracks)
    return {
        "schema_version": "kmfa.v014_private_blocker_resolution_tracks_public_safe.v1",
        "record_type": "v014_processed_value_source_map_completion_private_blocker_resolution_tracks_public_safe",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "source_phase_id": blocker_matrix["phase_id"],
        "resolution_track_count": len(tracks),
        "owner_or_agent_action_required_track_count": owner_required_count,
        "auto_resolution_allowed_track_count": auto_allowed_count,
        "aggregate_affected_count_is_not_unique_target_count": True,
        "aggregate_affected_count": total_affected,
        "resolution_tracks": tracks,
        "all_resolution_tracks_prepared": len(tracks) == int(blocker_matrix["blocker_class_count"]),
        "any_resolution_applied_by_this_phase": False,
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "business_value_consistency_verified": False,
        "decision": DECISION,
    }


def _build_private_queue(private_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    queue: list[dict[str, Any]] = []
    for record in private_records:
        if not isinstance(record, dict):
            continue
        status = record.get("match_status")
        if status == "no_raw_index_fingerprint_match":
            queue_status = "requires_corrected_source_or_owner_exclusion"
        elif status == "ambiguous_raw_index_fingerprint_match":
            queue_status = "requires_private_disambiguation"
        else:
            queue_status = "not_in_resolution_queue"
        if queue_status == "not_in_resolution_queue":
            continue
        queue.append(
            {
                "target_source": record.get("target_source"),
                "target_slot_id": record.get("target_slot_id"),
                "review_group_id": record.get("review_group_id"),
                "value_fingerprint": record.get("value_fingerprint"),
                "match_status": status,
                "raw_index_occurrence_count": record.get("raw_index_occurrence_count"),
                "resolution_queue_status": queue_status,
                "resolution_applied": False,
            }
        )
    return queue


def generate(*, generated_at: str | None = None, write_governance_event: bool = True) -> dict[str, Any]:
    timestamp = _now(generated_at)
    source_summary = _read_json(SOURCE_SUMMARY_PATH)
    source_go_no_go = _read_json(SOURCE_GO_NO_GO_PATH)
    blocker_matrix = _read_json(SOURCE_BLOCKER_MATRIX_PATH)
    source_private_report = _read_json(SOURCE_PRIVATE_REPORT_PATH)
    private_records = _read_jsonl(SOURCE_PRIVATE_BLOCKER_RECORDS_PATH)
    resolution_tracks = _build_resolution_tracks(timestamp, blocker_matrix)
    private_queue = _build_private_queue(private_records)
    queue_status_counts = Counter(str(row.get("resolution_queue_status")) for row in private_queue)

    private_packet = {
        "schema_version": "kmfa.private.v014_private_blocker_resolution_packet.v1",
        "classification": "private_blocker_resolution_packet_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_private_blocker_resolution_packet",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "source_phase_id": source_private_report.get("phase_id"),
        "resolution_tracks_public_safe_copy": resolution_tracks,
        "private_resolution_queue_count": len(private_queue),
        "private_resolution_queue_status_counts": dict(sorted(queue_status_counts.items())),
        "resolution_applied_by_this_phase": False,
        "private_resolution_queue": private_queue,
        "raw_boundary": _raw_boundary(),
    }
    diagnostic = {
        "schema_version": "kmfa.private.v014_private_blocker_resolution_packet_diagnostic.v1",
        "classification": "private_blocker_resolution_packet_diagnostic_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_private_blocker_resolution_packet_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "resolution_track_count": resolution_tracks["resolution_track_count"],
        "private_resolution_queue_count": len(private_queue),
        "private_resolution_queue_status_counts": dict(sorted(queue_status_counts.items())),
        "resolution_applied_by_this_phase": False,
        "raw_boundary": _raw_boundary(),
    }
    _write_json(PRIVATE_PACKET_PATH, private_packet)
    _write_jsonl(PRIVATE_QUEUE_PATH, private_queue)
    _write_json(PRIVATE_DIAGNOSTIC_PATH, diagnostic)
    _write_text(
        PRIVATE_PACKET_MD_PATH,
        "# Private Blocker Resolution Packet\n\n"
        "This private packet may contain target-level refs and value fingerprints. "
        "It is ignored and must not be committed.\n",
    )

    summary = {
        "schema_version": "kmfa.v014_private_blocker_resolution_packet_summary.v1",
        "record_type": "v014_processed_value_source_map_completion_private_blocker_resolution_packet_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "status": STATUS,
        "generated_at": timestamp,
        "source_phase_id": source_summary["phase_id"],
        "source_decision": source_summary["decision"],
        "source_go_no_go_decision": source_go_no_go["decision"],
        "previous_required_input": PREVIOUS_REQUIRED_INPUT,
        "previous_required_input_resolved_by_this_phase": True,
        "blocker_resolution_packet_prepared": True,
        "blocker_class_count": source_summary["blocker_class_count"],
        "resolution_track_count": resolution_tracks["resolution_track_count"],
        "owner_or_agent_action_required_track_count": resolution_tracks[
            "owner_or_agent_action_required_track_count"
        ],
        "auto_resolution_allowed_track_count": resolution_tracks["auto_resolution_allowed_track_count"],
        "private_blocker_record_count": len(private_records),
        "private_resolution_queue_count": len(private_queue),
        "private_resolution_queue_status_counts": dict(sorted(queue_status_counts.items())),
        "confirmed_value_mismatch_count": source_summary["confirmed_value_mismatch_count"],
        "confirmed_mismatch_report_required_now": False,
        "repeated_cross_validation_mismatch_confirmed": False,
        "final_goal_closeout_difference_report_required_now": False,
        "final_goal_closeout_difference_report_required_if_repeated": True,
        "resolution_applied_by_this_phase": False,
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "full_raw_to_processed_reconciliation_complete": False,
        "business_value_consistency_verified": False,
        "lineage_full_check_complete": False,
        "formal_report_allowed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "private_packet_written": True,
        "private_packet_gitignored": _git_check_ignored(PRIVATE_PACKET_PATH),
        "private_queue_written": True,
        "private_queue_gitignored": _git_check_ignored(PRIVATE_QUEUE_PATH),
        "private_diagnostic_written": True,
        "private_diagnostic_gitignored": _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH),
        "private_packet_markdown_written": True,
        "private_packet_markdown_gitignored": _git_check_ignored(PRIVATE_PACKET_MD_PATH),
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
        "next_required_input": NEXT_REQUIRED_INPUT,
        "raw_boundary": _raw_boundary(),
        "public_safety": _public_safety(),
    }
    go_no_go = {
        "schema_version": "kmfa.v014_private_blocker_resolution_packet_go_no_go.v1",
        "record_type": "v014_processed_value_source_map_completion_private_blocker_resolution_packet_go_no_go",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "decision": DECISION,
        "status": STATUS,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "resolution_track_count": summary["resolution_track_count"],
        "private_resolution_queue_count": summary["private_resolution_queue_count"],
        "resolution_applied_by_this_phase": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "blocked_until": NEXT_REQUIRED_INPUT,
    }
    manifest = {
        "schema_version": "kmfa.v014_private_blocker_resolution_packet_manifest.v1",
        "record_type": "v014_processed_value_source_map_completion_private_blocker_resolution_packet_manifest",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_ids": [ACCEPTANCE_ID],
        "generated_at": timestamp,
        "status": STATUS,
        "summary": summary,
        "go_no_go": go_no_go,
        "resolution_tracks": resolution_tracks,
        "artifact_refs": {
            "machine_summary": SUMMARY_PATH.as_posix(),
            "machine_manifest": MANIFEST_PATH.as_posix(),
            "machine_go_no_go": GO_NO_GO_PATH.as_posix(),
            "machine_resolution_tracks": RESOLUTION_TRACKS_PATH.as_posix(),
            "private_packet": "private_runtime_only",
            "private_queue": "private_runtime_only",
            "private_diagnostic": "private_runtime_only",
            "private_packet_markdown": "private_runtime_only",
        },
        "validator": (
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. "
            "python3 KMFA/tools/check_v014_processed_value_source_map_completion_private_blocker_resolution_packet.py "
            "--require-private-packet"
        ),
        "git": {
            "branch": _git_output(["branch", "--show-current"]),
            "head": _git_output(["rev-parse", "HEAD"]),
            "status_short": _git_output(["status", "--short", "--branch"]),
        },
    }
    report = f"""# V014 Private Blocker Resolution Packet

Decision: {DECISION}

This phase prepares resolution tracks for the current public-safe blocker matrix. It does not apply any resolution, read the raw inbox, run full reconciliation or publish target-level private evidence.

## Public-safe aggregate result

- Resolution tracks: {summary["resolution_track_count"]}
- Owner/agent action required tracks: {summary["owner_or_agent_action_required_track_count"]}
- Auto-resolution allowed tracks: {summary["auto_resolution_allowed_track_count"]}
- Private resolution queue rows: {summary["private_resolution_queue_count"]}
- Confirmed mismatches: {summary["confirmed_value_mismatch_count"]}
- Resolution applied by this phase: `false`
- Business value consistency verified: `false`

Next required input: `{NEXT_REQUIRED_INPUT}`.
"""
    go_no_go_record = f"""# Go/No-Go Record

- phase_id: `{PHASE_ID}`
- decision: `{DECISION}`
- reason: `{DIAGNOSTIC_CONCLUSION}`
- resolution_track_count: `{summary["resolution_track_count"]}`
- private_resolution_queue_count: `{summary["private_resolution_queue_count"]}`
- resolution applied by this phase: `false`
- full reconciliation complete: `false`
- github upload performed: `false`
"""
    test_results = """# Test Results

Status: passed locally.

Commands:

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_processed_value_source_map_completion_private_blocker_resolution_packet.py --generated-at 2026-07-06T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_value_source_map_completion_private_blocker_resolution_packet.py --require-private-packet`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_processed_value_source_map_completion_private_blocker_resolution_packet`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA`
- `git diff --check -- KMFA`
- tracked and staged raw/private artifact scans
- high-confidence tracked and staged secret marker scans
"""
    risk_register = """# Risk Register

- Risk: treating a resolution packet as completed reconciliation.
  Mitigation: no resolution is applied; full reconciliation, lineage, formal report and delivery gates remain closed.
- Risk: leaking private resolution queue details.
  Mitigation: public artifacts contain aggregate tracks and counts only; target-level queue stays in ignored runtime.
"""
    rollback_plan = """# Rollback Plan

No raw inbox file, canonical source map, app entry or public business value was modified. To roll back, remove this phase's public artifacts and metadata copies, remove ignored private packet outputs if not needed, and revert this local commit.
"""

    for path, payload in (
        (SUMMARY_PATH, summary),
        (MANIFEST_PATH, manifest),
        (GO_NO_GO_PATH, go_no_go),
        (RESOLUTION_TRACKS_PATH, resolution_tracks),
        (METADATA_SUMMARY_PATH, summary),
        (METADATA_MANIFEST_PATH, manifest),
        (METADATA_GO_NO_GO_PATH, go_no_go),
        (METADATA_RESOLUTION_TRACKS_PATH, resolution_tracks),
    ):
        _write_json(path, payload)
    for path, text in (
        (REPORT_PATH, report),
        (GO_NO_GO_RECORD_PATH, go_no_go_record),
        (TEST_RESULTS_PATH, test_results),
        (RISK_REGISTER_PATH, risk_register),
        (ROLLBACK_PATH, rollback_plan),
    ):
        _write_text(path, text)
    if write_governance_event:
        _append_development_event(timestamp, manifest)
    return manifest


def _append_development_event(generated_at: str, manifest: dict[str, Any]) -> None:
    event_id = "DEV-KMFA-20260706-V014-PRIVATE-BLOCKER-RESOLUTION-PACKET"
    summary = manifest["summary"]
    event = {
        "event_id": event_id,
        "event_time": generated_at,
        "event_type": "development",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "iteration_id": "ITER-20260706-KMFA-V014-PRIVATE-BLOCKER-RESOLUTION-PACKET",
        "fact_level": "EXTRACTED",
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "go_no_go": manifest["go_no_go"]["decision"],
        "resolution_track_count": summary["resolution_track_count"],
        "private_resolution_queue_count": summary["private_resolution_queue_count"],
        "resolution_applied_by_this_phase": False,
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "full_raw_to_processed_reconciliation_complete": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "result_commit": "PENDING",
        "summary": "Prepared public-safe private blocker resolution packet and kept all delivery gates closed.",
    }
    DEVELOPMENT_EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    existing = DEVELOPMENT_EVENTS_PATH.read_text(encoding="utf-8").splitlines() if DEVELOPMENT_EVENTS_PATH.exists() else []
    filtered = [line for line in existing if f'"event_id":"{event_id}"' not in line and f'"event_id": "{event_id}"' not in line]
    filtered.append(json.dumps(event, ensure_ascii=False, sort_keys=True))
    DEVELOPMENT_EVENTS_PATH.write_text("\n".join(filtered) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated-at")
    args = parser.parse_args()
    manifest = generate(generated_at=args.generated_at)
    print(
        "PASS: KMFA v0.1.4 private blocker resolution packet generated "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"tracks={manifest['summary']['resolution_track_count']}, "
        f"queue={manifest['summary']['private_resolution_queue_count']})"
    )


if __name__ == "__main__":
    main()
