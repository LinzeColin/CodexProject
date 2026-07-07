#!/usr/bin/env python3
"""Materialize private residual-difference resolution records for later comparison.

This phase consumes the ignored private materialization input produced by the
previous application phase. It writes only ignored private materialized records
and aggregate public evidence. It does not read the raw inbox, compare raw to
processed values, reconcile values, upload GitHub, reinstall the app, or execute
business steps.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


PROJECT_ROOT = Path("KMFA")
PHASE_ID = "V014_RESIDUAL_DIFFERENCE_PRIVATE_RESOLUTION_MATERIALIZATION_REPLAY"
TASK_ID = "KMFA-V014-RESIDUAL-DIFFERENCE-PRIVATE-RESOLUTION-MATERIALIZATION-REPLAY-20260707"
ACCEPTANCE_ID = "ACC-V014-RESIDUAL-DIFFERENCE-PRIVATE-RESOLUTION-MATERIALIZATION-REPLAY"
VERSION = "0.1.4-residual-difference-private-resolution-materialization-replay"
STATUS = "completed_validated_local_only_residual_difference_private_resolution_materialization_replay_no_go"
DECISION = "NO_GO"
DIAGNOSTIC_CONCLUSION = "private_resolution_materialized_raw_comparison_required"
NEXT_RECOMMENDED_PHASE = "V014_RESIDUAL_DIFFERENCE_RAW_TO_PROCESSED_COMPARISON_PRECHECK"
NEXT_REQUIRED_INPUT = "run_residual_difference_raw_to_processed_comparison_precheck"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "residual_difference_private_resolution_materialization_replay_summary.json"
MANIFEST_PATH = MACHINE_DIR / "residual_difference_private_resolution_materialization_replay_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "residual_difference_private_resolution_materialization_replay_go_no_go_report.json"
MATRIX_PATH = MACHINE_DIR / "residual_difference_private_resolution_materialization_replay_matrix_public_safe.json"
REPORT_PATH = HUMAN_DIR / "residual_difference_private_resolution_materialization_replay.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_residual_difference_private_resolution_materialization_replay_summary.json"
)
METADATA_MANIFEST_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_residual_difference_private_resolution_materialization_replay_manifest.json"
)
METADATA_GO_NO_GO_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_residual_difference_private_resolution_materialization_replay_go_no_go_report.json"
)
METADATA_MATRIX_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_residual_difference_private_resolution_materialization_replay_matrix_public_safe.json"
)

SOURCE_APPLICATION_SUMMARY_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_outside_scope_candidate_review_residual_difference_source_map_correction_application_summary.json"
)
SOURCE_APPLICATION_GO_NO_GO_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_outside_scope_candidate_review_residual_difference_source_map_correction_application_go_no_go_report.json"
)
SOURCE_APPLICATION_MATRIX_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_outside_scope_candidate_review_residual_difference_source_map_correction_application_matrix_public_safe.json"
)
SOURCE_PRIVATE_DIR = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_outside_scope_candidate_review_residual_difference_source_map_correction_application"
)
SOURCE_PRIVATE_APPLICATION_DIAGNOSTIC_PATH = SOURCE_PRIVATE_DIR / "private_source_map_correction_application_diagnostic.json"
SOURCE_PRIVATE_APPLICATION_RESULT_PATH = SOURCE_PRIVATE_DIR / "private_source_map_correction_application_result.json"
SOURCE_PRIVATE_APPLIED_RECORDS_PATH = SOURCE_PRIVATE_DIR / "private_source_map_correction_applied_records.jsonl"
SOURCE_PRIVATE_RESOLUTION_OVERLAY_PATH = SOURCE_PRIVATE_DIR / "private_source_map_correction_resolution_overlay.json"
SOURCE_PRIVATE_MATERIALIZATION_INPUT_PATH = (
    SOURCE_PRIVATE_DIR / "private_residual_difference_materialization_input_after_application.json"
)

PRIVATE_OUTPUT_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_residual_difference_private_resolution_materialization_replay"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_residual_difference_materialization_replay_diagnostic.json"
PRIVATE_RESULT_PATH = PRIVATE_OUTPUT_DIR / "private_residual_difference_materialization_replay_result.json"
PRIVATE_MATERIALIZED_RECORDS_PATH = PRIVATE_OUTPUT_DIR / "private_residual_difference_materialized_records.jsonl"
PRIVATE_RAW_COMPARISON_INPUT_PATH = PRIVATE_OUTPUT_DIR / "private_residual_difference_raw_comparison_input.json"
PRIVATE_REPORT_PATH = PRIVATE_OUTPUT_DIR / "private_residual_difference_materialization_replay.md"

DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"
STAGE_STATUS_PATH = PROJECT_ROOT / "metadata/stage_status.jsonl"
TASK_STATUS_PATH = PROJECT_ROOT / "metadata/traceability/v1_4_stage_phase_task_status.jsonl"

EXPECTED_TRACK_COUNTS = {
    "owner_select_one_authoritative_candidate": 24,
    "provide_authoritative_source_reference_or_owner_exclusion": 40,
    "provide_formula_or_non_numeric_mapping": 8,
}


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


def _changed_kmfa_files() -> list[str]:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", "status", "--porcelain=v1", "--untracked-files=all", "--", "KMFA"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        return []
    files: set[str] = set()
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        if ".codex_private_runtime/" not in path:
            files.add(path)
    return sorted(files)


def _raw_boundary() -> dict[str, bool]:
    return {
        "user_declared_raw_data_immutable": True,
        "raw_data_root_readonly_policy_active": True,
        "source_public_application_summary_read_by_this_phase": True,
        "source_public_application_go_no_go_read_by_this_phase": True,
        "source_public_application_matrix_read_by_this_phase": True,
        "source_private_application_diagnostic_read_by_this_phase": True,
        "source_private_application_result_read_by_this_phase": True,
        "source_private_applied_records_read_by_this_phase": True,
        "source_private_resolution_overlay_read_by_this_phase": True,
        "source_private_materialization_input_read_by_this_phase": True,
        "private_materialization_diagnostic_written_by_this_phase": True,
        "private_materialization_result_written_by_this_phase": True,
        "private_materialized_records_written_by_this_phase": True,
        "private_raw_comparison_input_written_by_this_phase": True,
        "source_private_application_inputs_mutated_by_this_phase": False,
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "raw_inbox_read_performed_by_this_phase": False,
        "raw_inbox_list_performed_by_this_phase": False,
        "raw_inbox_stat_performed_by_this_phase": False,
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
    }


def _public_safety() -> dict[str, bool]:
    return {
        "public_safe_aggregate_only": True,
        "private_application_diagnostic_committed": False,
        "private_application_result_committed": False,
        "private_application_records_committed": False,
        "private_resolution_overlay_committed": False,
        "private_materialization_input_committed": False,
        "private_materialization_diagnostic_committed": False,
        "private_materialization_result_committed": False,
        "private_materialized_records_committed": False,
        "private_raw_comparison_input_committed": False,
        "private_report_committed": False,
        "raw_file_committed": False,
        "raw_filename_committed": False,
        "raw_file_hash_committed": False,
        "raw_archive_member_name_committed": False,
        "field_header_plaintext_committed": False,
        "target_slot_detail_committed": False,
        "row_value_committed": False,
        "business_value_committed": False,
        "private_ref_or_fingerprint_committed": False,
        "credential_or_secret_committed": False,
    }


def _build_materialized_records(rows: list[dict[str, Any]], generated_at: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    materialized: list[dict[str, Any]] = []
    blockers: list[dict[str, Any]] = []
    seen_slots: set[str] = set()
    for index, row in enumerate(rows, start=1):
        slot_id = row.get("target_slot_id")
        track = row.get("diagnostic_track")
        if not isinstance(slot_id, str) or not slot_id:
            blockers.append({"materialization_queue_index": index, "blocker_code": "missing_target_slot"})
            continue
        if slot_id in seen_slots:
            blockers.append({"materialization_queue_index": index, "blocker_code": "duplicate_target_slot"})
            continue
        if track not in EXPECTED_TRACK_COUNTS:
            blockers.append({"materialization_queue_index": index, "blocker_code": "unknown_resolution_track"})
            continue
        if row.get("materialization_replay_required") is not True:
            blockers.append({"materialization_queue_index": index, "blocker_code": "materialization_not_required"})
            continue
        if row.get("source_map_correction_record_applied") is not True:
            blockers.append({"materialization_queue_index": index, "blocker_code": "source_map_correction_not_applied"})
            continue
        if row.get("authoritative_value_resolution_record_applied") is not True:
            blockers.append({"materialization_queue_index": index, "blocker_code": "authoritative_resolution_not_applied"})
            continue
        seen_slots.add(slot_id)
        materialized.append(
            {
                "materialization_index": len(materialized) + 1,
                "version": VERSION,
                "phase_id": PHASE_ID,
                "task_id": TASK_ID,
                "generated_at": generated_at,
                "target_slot_id": slot_id,
                "authorization_item_id": row.get("authorization_item_id"),
                "source_final_threshold_item_id": row.get("source_final_threshold_item_id"),
                "source_application_index": row.get("application_index"),
                "diagnostic_track": track,
                "response_decision_code": row.get("response_decision_code"),
                "source_resolution_application_action": row.get("resolution_application_action"),
                "materialization_action": "materialize_private_resolution_to_comparison_ready_processed_record",
                "materialization_status": "materialized_from_private_resolution_application",
                "private_resolution_materialized": True,
                "source_map_correction_record_applied": True,
                "authoritative_value_resolution_record_applied": True,
                "raw_to_processed_value_comparison_ready": True,
                "raw_to_processed_value_comparison_performed": False,
                "full_reconciliation_allowed": False,
                "business_value_consistency_verified": False,
                "public_commit_allowed": False,
            }
        )
    return materialized, blockers


def _build_matrix(summary: dict[str, Any], generated_at: str) -> dict[str, Any]:
    checks = [
        ("source_application_applied_count", summary["source_application_applied_record_count"] == 72, summary["source_application_applied_record_count"], 72),
        ("source_application_blocker_count_zero", summary["source_application_blocker_count"] == 0, summary["source_application_blocker_count"], 0),
        ("source_materialization_input_count", summary["source_materialization_input_record_count"] == 72, summary["source_materialization_input_record_count"], 72),
        ("materialized_record_count", summary["private_materialized_record_count"] == 72, summary["private_materialized_record_count"], 72),
        ("materialization_blocker_count_zero", summary["private_materialization_blocker_count"] == 0, summary["private_materialization_blocker_count"], 0),
        ("track_counts_match_expected", summary["diagnostic_track_counts"] == EXPECTED_TRACK_COUNTS, summary["diagnostic_track_counts"], EXPECTED_TRACK_COUNTS),
        ("raw_comparison_ready", summary["raw_to_processed_value_comparison_ready"] is True, summary["raw_to_processed_value_comparison_ready"], True),
        ("raw_comparison_not_performed", not summary["raw_to_processed_value_comparison_performed_by_this_phase"], False, False),
        ("business_consistency_not_verified", not summary["business_value_consistency_verified"], False, False),
        ("project_no_go_preserved", summary["decision"] == DECISION, summary["decision"], DECISION),
    ]
    rows = [
        {"check_code": code, "status": "PASS" if ok else "FAIL", "observed_public_safe": observed, "required": required}
        for code, ok, observed, required in checks
    ]
    pass_count = sum(1 for row in rows if row["status"] == "PASS")
    return {
        "schema_version": "kmfa.v014_residual_difference_private_resolution_materialization_replay_matrix_public_safe.v1",
        "record_type": "v014_residual_difference_private_resolution_materialization_replay_matrix_public_safe",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "check_count": len(rows),
        "check_pass_count": pass_count,
        "check_fail_count": len(rows) - pass_count,
        "private_materialized_record_count": summary["private_materialized_record_count"],
        "private_materialization_blocker_count": summary["private_materialization_blocker_count"],
        "raw_to_processed_value_comparison_ready": True,
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "business_value_consistency_verified": False,
        "decision": DECISION,
        "checks": rows,
    }


def _dedupe_append_jsonl(path: Path, rows: list[dict[str, Any]], keep_existing: Callable[[dict[str, Any]], bool]) -> None:
    retained: list[str] = []
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                existing = json.loads(line)
            except json.JSONDecodeError:
                retained.append(line)
                continue
            if not isinstance(existing, dict) or keep_existing(existing):
                retained.append(line)
    retained.extend(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(retained) + "\n", encoding="utf-8")


def _append_governance_records(manifest: dict[str, Any]) -> None:
    summary = manifest["summary"]
    event_id = "DEV-KMFA-20260707-V014-RESIDUAL-DIFFERENCE-MATERIALIZATION-REPLAY"
    event = {
        "event_id": event_id,
        "event_time": manifest["generated_at"],
        "event_type": "development",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "iteration_id": "ITER-20260707-KMFA-V014-RESIDUAL-DIFFERENCE-MATERIALIZATION-REPLAY",
        "fact_level": "EXTRACTED",
        "status": STATUS,
        "go_no_go": DECISION,
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "private_materialized_record_count": summary["private_materialized_record_count"],
        "private_materialization_blocker_count": summary["private_materialization_blocker_count"],
        "raw_to_processed_value_comparison_ready": True,
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "summary": "Materialized 72 private residual-difference resolution records in ignored runtime while keeping raw comparison and business consistency verification as later gates.",
        "result_commit": "PENDING",
        "files_changed": _changed_kmfa_files(),
    }
    _dedupe_append_jsonl(DEVELOPMENT_EVENTS_PATH, [event], lambda existing: existing.get("event_id") != event_id)

    stage_rows = [
        {
            "acceptance_id": ACCEPTANCE_ID,
            "completed_task_units": 1,
            "derived_percent": 100.0,
            "estimated_task_units": 1,
            "evidence_ref": MANIFEST_PATH.as_posix(),
            "fact_level": "EXTRACTED",
            "governance_stage_id": "VALUE-CONSISTENCY",
            "name": "v0.1.4 residual difference private resolution materialization replay",
            "phase_id": PHASE_ID,
            "record_type": "v014_phase",
            "roadmap_phase_id": "RESIDUAL_DIFFERENCE_PRIVATE_RESOLUTION_MATERIALIZATION_REPLAY",
            "roadmap_stage_id": "VALUE-CONSISTENCY",
            "status": STATUS,
            "task_count": 3,
            "updated_at": "2026-07-07",
        },
        {
            "acceptance_id": ACCEPTANCE_ID,
            "evidence_ref": SUMMARY_PATH.as_posix(),
            "fact_level": "EXTRACTED",
            "governance_stage_id": "VALUE-CONSISTENCY",
            "name": "72 private residual-difference records materialized",
            "phase_id": PHASE_ID,
            "record_type": "v014_task",
            "roadmap_phase_id": "RESIDUAL_DIFFERENCE_PRIVATE_RESOLUTION_MATERIALIZATION_REPLAY",
            "roadmap_stage_id": "VALUE-CONSISTENCY",
            "status": "completed_validated_local_only_no_go_upload_deferred",
            "task_id": "RDMR01",
            "updated_at": "2026-07-07",
        },
        {
            "acceptance_id": ACCEPTANCE_ID,
            "evidence_ref": GO_NO_GO_PATH.as_posix(),
            "fact_level": "EXTRACTED",
            "governance_stage_id": "VALUE-CONSISTENCY",
            "name": "raw-to-processed comparison is ready but not performed",
            "phase_id": PHASE_ID,
            "record_type": "v014_task",
            "roadmap_phase_id": "RESIDUAL_DIFFERENCE_PRIVATE_RESOLUTION_MATERIALIZATION_REPLAY",
            "roadmap_stage_id": "VALUE-CONSISTENCY",
            "status": "completed_validated_local_only_no_go_upload_deferred",
            "task_id": "RDMR02",
            "updated_at": "2026-07-07",
        },
        {
            "acceptance_id": ACCEPTANCE_ID,
            "evidence_ref": MANIFEST_PATH.as_posix(),
            "fact_level": "EXTRACTED",
            "governance_stage_id": "VALUE-CONSISTENCY",
            "name": "raw inbox untouched and private materialization outputs remain ignored",
            "phase_id": PHASE_ID,
            "record_type": "v014_task",
            "roadmap_phase_id": "RESIDUAL_DIFFERENCE_PRIVATE_RESOLUTION_MATERIALIZATION_REPLAY",
            "roadmap_stage_id": "VALUE-CONSISTENCY",
            "status": "completed_validated_local_only_no_go_upload_deferred",
            "task_id": "RDMR03",
            "updated_at": "2026-07-07",
        },
    ]
    _dedupe_append_jsonl(STAGE_STATUS_PATH, stage_rows, lambda existing: existing.get("phase_id") != PHASE_ID)

    task_rows = []
    for row in stage_rows:
        task_row = {
            **row,
            "schema_version": "kmfa.v014_stage_phase_task_status.v1",
            "project_id": "KMFA",
            "version": VERSION,
            "stage_id": "VALUE-CONSISTENCY",
            "raw_data_committed": False,
        }
        if row["record_type"] == "v014_phase":
            task_row["acceptance_output"] = (
                "Private materialization replay manifest summary Go No-Go public-safe matrix ignored private "
                "materialized records validator focused test and governance records"
            )
            task_row["phase_goal"] = (
                "materialize private residual-difference resolution records without raw comparison or reconciliation"
            )
        else:
            task_row["task_label"] = row["task_id"][-2:]
            task_row["task_text"] = row["name"]
        task_rows.append(task_row)
    _dedupe_append_jsonl(TASK_STATUS_PATH, task_rows, lambda existing: existing.get("phase_id") != PHASE_ID)


def _write_human_artifacts(summary: dict[str, Any], matrix: dict[str, Any]) -> None:
    report = f"""# Residual Difference Private Resolution Materialization Replay

- phase: `{PHASE_ID}`
- status: `{STATUS}`
- decision: `{DECISION}`
- source application records: `{summary["source_application_applied_record_count"]}`
- private materialized records: `{summary["private_materialized_record_count"]}`
- private materialization blockers: `{summary["private_materialization_blocker_count"]}`
- raw-to-processed comparison ready: `true`
- raw-to-processed comparison performed: `false`
- next required input: `{NEXT_REQUIRED_INPUT}`

This phase materializes private residual-difference resolution records only in ignored runtime. Public evidence is aggregate-only and remains `NO_GO` until raw-to-processed comparison and full reconciliation are separately completed and validated.
"""
    go_no_go_record = f"""# Go/No-Go Record

- decision: `{DECISION}`
- reason: private records were materialized for the next comparison gate, but raw-to-processed comparison and business consistency verification were not performed in this phase.
- checks: `{matrix["check_pass_count"]}` pass / `{matrix["check_fail_count"]}` fail
- next required input: `{NEXT_REQUIRED_INPUT}`
"""
    risk_register = """# Risk Register

- Risk: private materialization could be mistaken for verified raw-to-processed consistency.
- Control: raw comparison, full reconciliation, formal report, upload, app reinstall and business execution remain closed.
"""
    rollback_plan = """# Rollback Plan

Remove this phase's public artifacts, metadata copies, private materialization outputs, tool, validator, focused test and governance entries. The raw data inbox is not modified by this rollback.
"""
    test_results = """# Test Results

Recorded validation commands for this phase:

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_residual_difference_private_resolution_materialization_replay.py KMFA/tools/check_v014_residual_difference_private_resolution_materialization_replay.py KMFA/tests/test_v014_residual_difference_private_resolution_materialization_replay.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_private_resolution_materialization_replay.py --generated-at 2026-07-07T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_private_resolution_materialization_replay.py --require-private-replay`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_residual_difference_private_resolution_materialization_replay`
- `python3 scripts/validate_governance_sync.py --changed-only --base-ref HEAD --enforce-sync`
- `python3 scripts/validate_project_governance.py --changed-only --base-ref HEAD --enforce-sync`
- `python3 scripts/lean_governance.py validate --changed-only --base-ref HEAD --enforce-sync`
- `git diff --check`

All listed commands must pass before local commit. This phase does not read, list, parse, copy, move, rename, delete, overwrite, normalize or mutate the raw inbox.
"""
    for path, text in (
        (REPORT_PATH, report),
        (GO_NO_GO_RECORD_PATH, go_no_go_record),
        (RISK_REGISTER_PATH, risk_register),
        (ROLLBACK_PATH, rollback_plan),
        (TEST_RESULTS_PATH, test_results),
    ):
        _write_text(path, text)


def generate(*, generated_at: str | None = None, write_governance_event: bool = True) -> dict[str, Any]:
    timestamp = _now(generated_at)
    source_summary = _read_json(SOURCE_APPLICATION_SUMMARY_PATH)
    source_go_no_go = _read_json(SOURCE_APPLICATION_GO_NO_GO_PATH)
    source_matrix = _read_json(SOURCE_APPLICATION_MATRIX_PATH)
    source_diagnostic = _read_json(SOURCE_PRIVATE_APPLICATION_DIAGNOSTIC_PATH)
    source_result = _read_json(SOURCE_PRIVATE_APPLICATION_RESULT_PATH)
    source_applied_rows = _read_jsonl(SOURCE_PRIVATE_APPLIED_RECORDS_PATH)
    source_overlay = _read_json(SOURCE_PRIVATE_RESOLUTION_OVERLAY_PATH)
    source_materialization_input = _read_json(SOURCE_PRIVATE_MATERIALIZATION_INPUT_PATH)
    resolution_rows = source_materialization_input.get("resolution_records", [])
    if not isinstance(resolution_rows, list):
        raise ValueError("source materialization input must contain resolution_records")
    if len(source_applied_rows) != 72 or len(resolution_rows) != 72:
        raise ValueError("source application must provide 72 applied rows and 72 materialization rows")
    if source_result.get("private_resolution_application_blocker_count") != 0:
        raise ValueError("source application blockers must be zero")

    materialized_records, materialization_blockers = _build_materialized_records(resolution_rows, timestamp)
    track_counts = dict(Counter(row.get("diagnostic_track") for row in materialized_records))
    materialization_complete = (
        len(materialized_records) == 72
        and not materialization_blockers
        and track_counts == EXPECTED_TRACK_COUNTS
    )
    if not materialization_complete:
        raise ValueError("private residual difference materialization replay is incomplete")

    raw_boundary = _raw_boundary()
    public_safety = _public_safety()
    private_raw_comparison_input = {
        "schema_version": "kmfa.private.v014_residual_difference_raw_comparison_input.v1",
        "classification": "private_residual_difference_raw_comparison_input_do_not_commit",
        "record_type": "v014_residual_difference_raw_comparison_input",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "private_materialized_record_count": len(materialized_records),
        "raw_to_processed_value_comparison_ready": True,
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
        "materialized_records": materialized_records,
    }
    private_result = {
        "schema_version": "kmfa.private.v014_residual_difference_materialization_replay_result.v1",
        "classification": "private_residual_difference_materialization_replay_result_do_not_commit",
        "record_type": "v014_residual_difference_materialization_replay_result",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "source_application_applied_record_count": len(source_applied_rows),
        "source_application_blocker_count": source_result.get("private_resolution_application_blocker_count"),
        "private_materialized_record_count": len(materialized_records),
        "private_materialization_blocker_count": len(materialization_blockers),
        "materialization_replay_performed": True,
        "raw_to_processed_value_comparison_ready": True,
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
    }
    private_diagnostic = {
        "schema_version": "kmfa.private.v014_residual_difference_materialization_replay_diagnostic.v1",
        "record_type": "private_residual_difference_materialization_replay_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "source_application_phase_id": source_summary.get("phase_id"),
        "source_application_decision": source_go_no_go.get("decision"),
        "source_application_check_fail_count": source_matrix.get("check_fail_count"),
        "source_private_diagnostic_phase_id": source_diagnostic.get("phase_id"),
        "source_private_overlay_phase_id": source_overlay.get("phase_id"),
        "source_application_applied_record_count": len(source_applied_rows),
        "source_materialization_input_record_count": len(resolution_rows),
        "private_materialized_record_count": len(materialized_records),
        "private_materialization_blocker_count": len(materialization_blockers),
        "diagnostic_track_counts": track_counts,
        "raw_inbox_accessed": False,
        "raw_inbox_mutated": False,
    }

    _write_json(PRIVATE_DIAGNOSTIC_PATH, private_diagnostic)
    _write_json(PRIVATE_RESULT_PATH, private_result)
    _write_jsonl(PRIVATE_MATERIALIZED_RECORDS_PATH, materialized_records)
    _write_json(PRIVATE_RAW_COMPARISON_INPUT_PATH, private_raw_comparison_input)
    _write_text(
        PRIVATE_REPORT_PATH,
        "\n".join(
            [
                "# Private residual difference materialization replay",
                "",
                f"- phase_id: `{PHASE_ID}`",
                f"- private_materialized_record_count: `{len(materialized_records)}`",
                f"- private_materialization_blocker_count: `{len(materialization_blockers)}`",
                "- raw-to-processed comparison was not performed.",
                "- raw inbox access and mutation were not performed.",
            ]
        )
        + "\n",
    )

    summary = {
        "schema_version": "kmfa.v014_residual_difference_private_resolution_materialization_replay_summary.v1",
        "record_type": "v014_residual_difference_private_resolution_materialization_replay_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "source_application_phase_id": source_summary.get("phase_id"),
        "source_application_decision": source_summary.get("decision"),
        "source_application_applied_record_count": len(source_applied_rows),
        "source_application_blocker_count": source_result.get("private_resolution_application_blocker_count"),
        "source_materialization_input_record_count": len(resolution_rows),
        "materialization_replay_performed_by_this_phase": True,
        "private_materialized_record_count": len(materialized_records),
        "private_materialization_blocker_count": len(materialization_blockers),
        "diagnostic_track_counts": track_counts,
        "owner_select_one_authoritative_candidate_count": track_counts.get("owner_select_one_authoritative_candidate", 0),
        "provide_authoritative_source_reference_or_owner_exclusion_count": track_counts.get(
            "provide_authoritative_source_reference_or_owner_exclusion", 0
        ),
        "provide_formula_or_non_numeric_mapping_count": track_counts.get("provide_formula_or_non_numeric_mapping", 0),
        "closed_discrepancy_count": 0,
        "open_residual_difference_count": source_summary.get("open_residual_difference_count"),
        "raw_to_processed_value_comparison_ready": True,
        "private_raw_comparison_input_prepared": True,
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "full_raw_to_processed_value_comparison_complete": False,
        "full_reconciliation_allowed": False,
        "processed_consistency_verified": False,
        "business_value_consistency_verified": False,
        "lineage_full_check_complete": False,
        "formal_report_allowed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "private_materialization_diagnostic_written": True,
        "private_materialization_diagnostic_gitignored": _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH),
        "private_materialization_result_written": True,
        "private_materialization_result_gitignored": _git_check_ignored(PRIVATE_RESULT_PATH),
        "private_materialized_records_written": True,
        "private_materialized_records_gitignored": _git_check_ignored(PRIVATE_MATERIALIZED_RECORDS_PATH),
        "private_raw_comparison_input_written": True,
        "private_raw_comparison_input_gitignored": _git_check_ignored(PRIVATE_RAW_COMPARISON_INPUT_PATH),
        "private_materialization_report_gitignored": _git_check_ignored(PRIVATE_REPORT_PATH),
        "raw_boundary": raw_boundary,
        "public_safety": public_safety,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
        "next_required_input": NEXT_REQUIRED_INPUT,
    }
    matrix = _build_matrix(summary, timestamp)
    go_no_go = {
        "schema_version": "kmfa.v014_residual_difference_private_resolution_materialization_replay_go_no_go.v1",
        "record_type": "v014_residual_difference_private_resolution_materialization_replay_go_no_go",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "private_materialized_record_count": summary["private_materialized_record_count"],
        "private_materialization_blocker_count": summary["private_materialization_blocker_count"],
        "raw_to_processed_value_comparison_ready": True,
        "raw_to_processed_value_comparison_allowed_next_phase": True,
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "full_raw_to_processed_value_comparison_complete": False,
        "business_value_consistency_verified": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "business_execution_allowed": False,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
        "next_required_input": NEXT_REQUIRED_INPUT,
    }
    manifest = {
        "schema_version": "kmfa.v014_residual_difference_private_resolution_materialization_replay_manifest.v1",
        "record_type": "v014_residual_difference_private_resolution_materialization_replay_manifest",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "source_artifacts": [
            SOURCE_APPLICATION_SUMMARY_PATH.as_posix(),
            SOURCE_APPLICATION_GO_NO_GO_PATH.as_posix(),
            SOURCE_APPLICATION_MATRIX_PATH.as_posix(),
            "private:source_map_correction_application_diagnostic",
            "private:source_map_correction_application_result",
            "private:source_map_correction_applied_records",
            "private:source_map_correction_resolution_overlay",
            "private:residual_difference_materialization_input_after_application",
        ],
        "public_artifact_refs": [
            SUMMARY_PATH.as_posix(),
            MANIFEST_PATH.as_posix(),
            GO_NO_GO_PATH.as_posix(),
            MATRIX_PATH.as_posix(),
            REPORT_PATH.as_posix(),
            GO_NO_GO_RECORD_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            RISK_REGISTER_PATH.as_posix(),
            ROLLBACK_PATH.as_posix(),
        ],
        "metadata_artifact_refs": [
            METADATA_SUMMARY_PATH.as_posix(),
            METADATA_MANIFEST_PATH.as_posix(),
            METADATA_GO_NO_GO_PATH.as_posix(),
            METADATA_MATRIX_PATH.as_posix(),
        ],
        "private_artifact_refs": [
            "private:residual_difference_materialization_replay_diagnostic",
            "private:residual_difference_materialization_replay_result",
            "private:residual_difference_materialized_records",
            "private:residual_difference_raw_comparison_input",
            "private:residual_difference_materialization_replay_report",
        ],
        "test_commands": [
            "PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_residual_difference_private_resolution_materialization_replay.py KMFA/tools/check_v014_residual_difference_private_resolution_materialization_replay.py KMFA/tests/test_v014_residual_difference_private_resolution_materialization_replay.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_private_resolution_materialization_replay.py --generated-at 2026-07-07T00:00:00+10:00",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_private_resolution_materialization_replay.py --require-private-replay",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_residual_difference_private_resolution_materialization_replay",
        ],
        "raw_boundary": raw_boundary,
        "public_safety": public_safety,
        "summary": summary,
        "matrix": matrix,
        "go_no_go_report": go_no_go,
        "git": {
            "branch": _git_output(["branch", "--show-current"]),
            "head": _git_output(["rev-parse", "HEAD"]),
            "status_short_branch": _git_output(["status", "--short", "--branch"]),
        },
    }

    _write_json(SUMMARY_PATH, summary)
    _write_json(MANIFEST_PATH, manifest)
    _write_json(GO_NO_GO_PATH, go_no_go)
    _write_json(MATRIX_PATH, matrix)
    _write_json(METADATA_SUMMARY_PATH, summary)
    _write_json(METADATA_MANIFEST_PATH, manifest)
    _write_json(METADATA_GO_NO_GO_PATH, go_no_go)
    _write_json(METADATA_MATRIX_PATH, matrix)
    _write_human_artifacts(summary, matrix)
    if write_governance_event:
        _append_governance_records(manifest)
    return {"summary": summary, "matrix": matrix, "go_no_go": go_no_go, "manifest": manifest}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generated-at")
    args = parser.parse_args()
    result = generate(generated_at=args.generated_at)
    summary = result["summary"]
    print(
        "PASS: generated V014 residual-difference private materialization replay "
        f"decision={summary['decision']} materialized={summary['private_materialized_record_count']} "
        f"blockers={summary['private_materialization_blocker_count']} next={summary['next_recommended_phase']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
