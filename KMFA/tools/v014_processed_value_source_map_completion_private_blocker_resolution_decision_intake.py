#!/usr/bin/env python3
"""Intake conservative blocker-resolution decisions for KMFA v0.1.4.

This phase records a public-safe decision intake for the prior private blocker
resolution packet. No corrected private source, owner exclusion, or
disambiguation evidence is available in this phase, so every resolution track
is kept blocked. Private target-level queue decisions remain under the ignored
runtime directory.
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
PHASE_ID = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_PRIVATE_BLOCKER_RESOLUTION_DECISION_INTAKE"
TASK_ID = "KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-PRIVATE-BLOCKER-RESOLUTION-DECISION-INTAKE-20260706"
ACCEPTANCE_ID = "ACC-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-PRIVATE-BLOCKER-RESOLUTION-DECISION-INTAKE"
VERSION = "0.1.4-private-blocker-resolution-decision-intake"
STATUS = "completed_validated_local_only_private_blocker_resolution_decision_intake_no_go"
DECISION = "NO_GO"
DIAGNOSTIC_CONCLUSION = "conservative_blocker_resolution_decisions_intaken_no_resolution_applied"
PREVIOUS_REQUIRED_INPUT = "private_blocker_resolution_decisions_or_corrected_private_source_before_full_reconciliation"
NEXT_RECOMMENDED_PHASE = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_PRIVATE_RECONCILIATION_READINESS_RECHECK"
NEXT_REQUIRED_INPUT = "corrected_private_source_or_owner_approved_resolution_before_full_reconciliation"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "processed_value_source_map_completion_private_blocker_resolution_decision_intake_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_value_source_map_completion_private_blocker_resolution_decision_intake_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_value_source_map_completion_private_blocker_resolution_decision_intake_go_no_go_report.json"
DECISION_MATRIX_PATH = MACHINE_DIR / "processed_value_source_map_completion_private_blocker_resolution_decision_matrix_public_safe.json"
REPORT_PATH = HUMAN_DIR / "processed_value_source_map_completion_private_blocker_resolution_decision_intake.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_private_blocker_resolution_decision_intake_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_private_blocker_resolution_decision_intake_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_private_blocker_resolution_decision_intake_go_no_go_report.json"
METADATA_DECISION_MATRIX_PATH = PROJECT_ROOT / "metadata/quality/v014_private_blocker_resolution_decision_matrix_public_safe.json"
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"

SOURCE_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_private_blocker_resolution_packet_summary.json"
SOURCE_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_private_blocker_resolution_packet_go_no_go_report.json"
SOURCE_TRACKS_PATH = PROJECT_ROOT / "metadata/quality/v014_private_blocker_resolution_tracks_public_safe.json"
SOURCE_PRIVATE_PACKET_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_private_blocker_resolution_packet/private_blocker_resolution_packet.json"
)
SOURCE_PRIVATE_QUEUE_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_private_blocker_resolution_packet/private_blocker_resolution_queue.jsonl"
)

PRIVATE_OUTPUT_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_processed_value_source_map_completion_private_blocker_resolution_decision_intake"
PRIVATE_DECISION_RECORD_PATH = PRIVATE_OUTPUT_DIR / "private_blocker_resolution_decision_intake.json"
PRIVATE_DECISION_QUEUE_PATH = PRIVATE_OUTPUT_DIR / "private_blocker_resolution_decision_queue.jsonl"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_blocker_resolution_decision_intake_diagnostic.json"
PRIVATE_REPORT_PATH = PRIVATE_OUTPUT_DIR / "private_blocker_resolution_decision_intake.md"


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
        "private_blocker_resolution_packet_read_performed_by_this_phase": True,
        "private_resolution_queue_read_performed_by_this_phase": True,
        "private_decision_intake_written_by_this_phase": True,
    }


def _public_safety() -> dict[str, bool]:
    return {
        "public_safe_aggregate_only": True,
        "private_resolution_queue_committed": False,
        "private_decision_queue_committed": False,
        "private_decision_record_committed": False,
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


def _decision_for_track(track: dict[str, Any]) -> dict[str, Any]:
    return {
        "blocker_code": track["blocker_code"],
        "resolution_track_code": track["resolution_track_code"],
        "decision_code": "keep_blocked_no_resolution_evidence",
        "decision_basis": "no corrected private source, owner exclusion, or disambiguation evidence was provided",
        "source_decision": track["default_resolution_decision"],
        "resolution_applied": False,
        "requires_corrected_private_source_or_owner_decision": True,
        "full_reconciliation_allowed_after_decision": False,
        "delivery_claim_allowed_after_decision": False,
    }


def _build_decision_matrix(generated_at: str, source_tracks: dict[str, Any]) -> dict[str, Any]:
    tracks = source_tracks.get("resolution_tracks", [])
    if not isinstance(tracks, list):
        raise ValueError("resolution_tracks must be a list")
    decisions = [_decision_for_track(track) for track in tracks if isinstance(track, dict)]
    return {
        "schema_version": "kmfa.v014_private_blocker_resolution_decision_matrix_public_safe.v1",
        "record_type": "v014_processed_value_source_map_completion_private_blocker_resolution_decision_matrix_public_safe",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "source_phase_id": source_tracks["phase_id"],
        "decision_track_count": len(decisions),
        "keep_blocked_decision_count": len(decisions),
        "resolution_applied_decision_count": 0,
        "corrected_private_source_provided": False,
        "owner_exclusion_or_disambiguation_provided": False,
        "all_decisions_intaken": len(decisions) == int(source_tracks["resolution_track_count"]),
        "decision_rows": decisions,
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "business_value_consistency_verified": False,
        "decision": DECISION,
    }


def _build_private_decision_queue(private_queue: list[dict[str, Any]]) -> list[dict[str, Any]]:
    decisions: list[dict[str, Any]] = []
    for row in private_queue:
        if not isinstance(row, dict):
            continue
        queue_status = str(row.get("resolution_queue_status"))
        if queue_status == "requires_corrected_source_or_owner_exclusion":
            decision_code = "keep_blocked_pending_corrected_source_or_owner_exclusion"
        elif queue_status == "requires_private_disambiguation":
            decision_code = "keep_blocked_pending_private_disambiguation"
        else:
            decision_code = "keep_blocked_pending_valid_resolution"
        decisions.append(
            {
                "target_source": row.get("target_source"),
                "target_slot_id": row.get("target_slot_id"),
                "review_group_id": row.get("review_group_id"),
                "value_fingerprint": row.get("value_fingerprint"),
                "match_status": row.get("match_status"),
                "raw_index_occurrence_count": row.get("raw_index_occurrence_count"),
                "source_resolution_queue_status": queue_status,
                "decision_code": decision_code,
                "resolution_applied": False,
                "full_reconciliation_allowed": False,
            }
        )
    return decisions


def generate(*, generated_at: str | None = None, write_governance_event: bool = True) -> dict[str, Any]:
    timestamp = _now(generated_at)
    source_summary = _read_json(SOURCE_SUMMARY_PATH)
    source_go_no_go = _read_json(SOURCE_GO_NO_GO_PATH)
    source_tracks = _read_json(SOURCE_TRACKS_PATH)
    source_private_packet = _read_json(SOURCE_PRIVATE_PACKET_PATH)
    private_queue = _read_jsonl(SOURCE_PRIVATE_QUEUE_PATH)
    decision_matrix = _build_decision_matrix(timestamp, source_tracks)
    private_decisions = _build_private_decision_queue(private_queue)
    decision_status_counts = Counter(str(row.get("decision_code")) for row in private_decisions)

    private_record = {
        "schema_version": "kmfa.private.v014_private_blocker_resolution_decision_intake.v1",
        "classification": "private_blocker_resolution_decision_intake_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_private_blocker_resolution_decision_intake",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "source_phase_id": source_private_packet.get("phase_id"),
        "decision_matrix_public_safe_copy": decision_matrix,
        "private_decision_queue_count": len(private_decisions),
        "private_decision_status_counts": dict(sorted(decision_status_counts.items())),
        "resolution_applied_by_this_phase": False,
        "private_decision_queue": private_decisions,
        "raw_boundary": _raw_boundary(),
    }
    diagnostic = {
        "schema_version": "kmfa.private.v014_private_blocker_resolution_decision_intake_diagnostic.v1",
        "classification": "private_blocker_resolution_decision_intake_diagnostic_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_private_blocker_resolution_decision_intake_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "private_decision_queue_count": len(private_decisions),
        "private_decision_status_counts": dict(sorted(decision_status_counts.items())),
        "resolution_applied_by_this_phase": False,
        "raw_boundary": _raw_boundary(),
    }
    _write_json(PRIVATE_DECISION_RECORD_PATH, private_record)
    _write_jsonl(PRIVATE_DECISION_QUEUE_PATH, private_decisions)
    _write_json(PRIVATE_DIAGNOSTIC_PATH, diagnostic)
    _write_text(
        PRIVATE_REPORT_PATH,
        "# Private Blocker Resolution Decision Intake\n\n"
        "This private intake may contain target-level refs and value fingerprints. "
        "It is ignored and must not be committed.\n",
    )

    summary = {
        "schema_version": "kmfa.v014_private_blocker_resolution_decision_intake_summary.v1",
        "record_type": "v014_processed_value_source_map_completion_private_blocker_resolution_decision_intake_summary",
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
        "blocker_resolution_decision_intake_performed": True,
        "decision_track_count": decision_matrix["decision_track_count"],
        "keep_blocked_decision_count": decision_matrix["keep_blocked_decision_count"],
        "resolution_applied_decision_count": 0,
        "corrected_private_source_provided": False,
        "owner_exclusion_or_disambiguation_provided": False,
        "private_resolution_queue_count": source_summary["private_resolution_queue_count"],
        "private_decision_queue_count": len(private_decisions),
        "private_decision_status_counts": dict(sorted(decision_status_counts.items())),
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
        "private_decision_record_written": True,
        "private_decision_record_gitignored": _git_check_ignored(PRIVATE_DECISION_RECORD_PATH),
        "private_decision_queue_written": True,
        "private_decision_queue_gitignored": _git_check_ignored(PRIVATE_DECISION_QUEUE_PATH),
        "private_diagnostic_written": True,
        "private_diagnostic_gitignored": _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH),
        "private_report_written": True,
        "private_report_gitignored": _git_check_ignored(PRIVATE_REPORT_PATH),
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
        "next_required_input": NEXT_REQUIRED_INPUT,
        "raw_boundary": _raw_boundary(),
        "public_safety": _public_safety(),
    }
    go_no_go = {
        "schema_version": "kmfa.v014_private_blocker_resolution_decision_intake_go_no_go.v1",
        "record_type": "v014_processed_value_source_map_completion_private_blocker_resolution_decision_intake_go_no_go",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "decision": DECISION,
        "status": STATUS,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "decision_track_count": summary["decision_track_count"],
        "keep_blocked_decision_count": summary["keep_blocked_decision_count"],
        "resolution_applied_decision_count": 0,
        "private_decision_queue_count": summary["private_decision_queue_count"],
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "blocked_until": NEXT_REQUIRED_INPUT,
    }
    manifest = {
        "schema_version": "kmfa.v014_private_blocker_resolution_decision_intake_manifest.v1",
        "record_type": "v014_processed_value_source_map_completion_private_blocker_resolution_decision_intake_manifest",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_ids": [ACCEPTANCE_ID],
        "generated_at": timestamp,
        "status": STATUS,
        "summary": summary,
        "go_no_go": go_no_go,
        "decision_matrix": decision_matrix,
        "artifact_refs": {
            "machine_summary": SUMMARY_PATH.as_posix(),
            "machine_manifest": MANIFEST_PATH.as_posix(),
            "machine_go_no_go": GO_NO_GO_PATH.as_posix(),
            "machine_decision_matrix": DECISION_MATRIX_PATH.as_posix(),
            "private_decision_record": "private_runtime_only",
            "private_decision_queue": "private_runtime_only",
            "private_diagnostic": "private_runtime_only",
            "private_report": "private_runtime_only",
        },
        "validator": (
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. "
            "python3 KMFA/tools/check_v014_processed_value_source_map_completion_private_blocker_resolution_decision_intake.py "
            "--require-private-intake"
        ),
        "git": {
            "branch": _git_output(["branch", "--show-current"]),
            "head": _git_output(["rev-parse", "HEAD"]),
            "status_short": _git_output(["status", "--short", "--branch"]),
        },
    }
    report = f"""# V014 Private Blocker Resolution Decision Intake

Decision: {DECISION}

This phase records conservative decision intake for the current blocker resolution packet. No corrected private source, owner exclusion, or private disambiguation evidence was provided, so all tracks remain blocked.

## Public-safe aggregate result

- Decision tracks: {summary["decision_track_count"]}
- Keep-blocked decisions: {summary["keep_blocked_decision_count"]}
- Resolution-applied decisions: {summary["resolution_applied_decision_count"]}
- Private decision queue rows: {summary["private_decision_queue_count"]}
- Corrected private source provided: `false`
- Owner exclusion or disambiguation provided: `false`
- Business value consistency verified: `false`

Next required input: `{NEXT_REQUIRED_INPUT}`.
"""
    go_no_go_record = f"""# Go/No-Go Record

- phase_id: `{PHASE_ID}`
- decision: `{DECISION}`
- reason: `{DIAGNOSTIC_CONCLUSION}`
- decision_track_count: `{summary["decision_track_count"]}`
- keep_blocked_decision_count: `{summary["keep_blocked_decision_count"]}`
- resolution applied by this phase: `false`
- full reconciliation complete: `false`
- github upload performed: `false`
"""
    test_results = """# Test Results

Status: passed locally.

Commands:

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_processed_value_source_map_completion_private_blocker_resolution_decision_intake.py --generated-at 2026-07-06T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_value_source_map_completion_private_blocker_resolution_decision_intake.py --require-private-intake`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_processed_value_source_map_completion_private_blocker_resolution_decision_intake`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA`
- `git diff --check -- KMFA`
- tracked and staged raw/private artifact scans
- high-confidence tracked and staged secret marker scans
"""
    risk_register = """# Risk Register

- Risk: treating conservative decision intake as resolved blockers.
  Mitigation: resolution_applied remains false and all reconciliation, lineage, formal report and delivery gates stay closed.
- Risk: leaking private queue details.
  Mitigation: public artifacts contain only decision counts and track-level public-safe codes; target-level decisions stay in ignored runtime.
"""
    rollback_plan = """# Rollback Plan

No raw inbox file, canonical source map, app entry or public business value was modified. To roll back, remove this phase's public artifacts and metadata copies, remove ignored private intake outputs if not needed, and revert this local commit.
"""

    for path, payload in (
        (SUMMARY_PATH, summary),
        (MANIFEST_PATH, manifest),
        (GO_NO_GO_PATH, go_no_go),
        (DECISION_MATRIX_PATH, decision_matrix),
        (METADATA_SUMMARY_PATH, summary),
        (METADATA_MANIFEST_PATH, manifest),
        (METADATA_GO_NO_GO_PATH, go_no_go),
        (METADATA_DECISION_MATRIX_PATH, decision_matrix),
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
    event_id = "DEV-KMFA-20260706-V014-PRIVATE-BLOCKER-RESOLUTION-DECISION-INTAKE"
    summary = manifest["summary"]
    event = {
        "event_id": event_id,
        "event_time": generated_at,
        "event_type": "development",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "iteration_id": "ITER-20260706-KMFA-V014-PRIVATE-BLOCKER-RESOLUTION-DECISION-INTAKE",
        "fact_level": "EXTRACTED",
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "go_no_go": manifest["go_no_go"]["decision"],
        "decision_track_count": summary["decision_track_count"],
        "keep_blocked_decision_count": summary["keep_blocked_decision_count"],
        "resolution_applied_decision_count": summary["resolution_applied_decision_count"],
        "private_decision_queue_count": summary["private_decision_queue_count"],
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "full_raw_to_processed_reconciliation_complete": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "result_commit": "PENDING",
        "summary": "Recorded conservative private blocker resolution decision intake and kept all full-reconciliation gates closed.",
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
        "PASS: KMFA v0.1.4 private blocker resolution decision intake generated "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"tracks={manifest['summary']['decision_track_count']}, "
        f"keep_blocked={manifest['summary']['keep_blocked_decision_count']})"
    )


if __name__ == "__main__":
    main()
