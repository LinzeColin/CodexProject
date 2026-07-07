#!/usr/bin/env python3
"""Apply residual-difference source-map correction records in private runtime.

This phase consumes the ignored private application-ready queue produced by the
previous phase and writes private resolution/source-map application records. It
does not read the raw inbox, materialize processed values, compare raw to
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
PHASE_ID = "V014_OUTSIDE_SCOPE_CANDIDATE_REVIEW_RESIDUAL_DIFFERENCE_SOURCE_MAP_CORRECTION_APPLICATION"
TASK_ID = (
    "KMFA-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-RESIDUAL-DIFFERENCE-"
    "SOURCE-MAP-CORRECTION-APPLICATION-20260707"
)
ACCEPTANCE_ID = (
    "ACC-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-RESIDUAL-DIFFERENCE-"
    "SOURCE-MAP-CORRECTION-APPLICATION"
)
VERSION = "0.1.4-outside-scope-candidate-review-residual-difference-source-map-correction-application"
STATUS = "completed_validated_local_only_residual_difference_source_map_correction_application_applied_no_go"
DECISION = "NO_GO"
DIAGNOSTIC_CONCLUSION = "private_resolution_application_applied_materialization_replay_required"
NEXT_RECOMMENDED_PHASE = (
    "V014_RESIDUAL_DIFFERENCE_PRIVATE_RESOLUTION_MATERIALIZATION_REPLAY"
)
NEXT_REQUIRED_INPUT = (
    "run_private_resolution_materialization_replay_before_full_raw_to_processed_comparison"
)

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "outside_scope_candidate_review_residual_difference_source_map_correction_application_summary.json"
MANIFEST_PATH = MACHINE_DIR / "outside_scope_candidate_review_residual_difference_source_map_correction_application_manifest.json"
GO_NO_GO_PATH = (
    MACHINE_DIR / "outside_scope_candidate_review_residual_difference_source_map_correction_application_go_no_go_report.json"
)
MATRIX_PATH = (
    MACHINE_DIR / "outside_scope_candidate_review_residual_difference_source_map_correction_application_matrix_public_safe.json"
)
REPORT_PATH = HUMAN_DIR / "outside_scope_candidate_review_residual_difference_source_map_correction_application.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_outside_scope_candidate_review_residual_difference_source_map_correction_application_summary.json"
)
METADATA_MANIFEST_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_outside_scope_candidate_review_residual_difference_source_map_correction_application_manifest.json"
)
METADATA_GO_NO_GO_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_outside_scope_candidate_review_residual_difference_source_map_correction_application_go_no_go_report.json"
)
METADATA_MATRIX_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_outside_scope_candidate_review_residual_difference_source_map_correction_application_matrix_public_safe.json"
)

SOURCE_READINESS_SUMMARY_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_outside_scope_candidate_review_residual_difference_source_map_correction_application_readiness_summary.json"
)
SOURCE_READINESS_GO_NO_GO_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_outside_scope_candidate_review_residual_difference_source_map_correction_application_readiness_go_no_go_report.json"
)
SOURCE_READINESS_MATRIX_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_outside_scope_candidate_review_residual_difference_source_map_correction_application_readiness_matrix_public_safe.json"
)
SOURCE_PRIVATE_READINESS_DIAGNOSTIC_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_outside_scope_candidate_review_residual_difference_source_map_correction_application_readiness/private_source_map_correction_application_readiness_diagnostic.json"
)
SOURCE_PRIVATE_READY_QUEUE_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_outside_scope_candidate_review_residual_difference_source_map_correction_application_readiness/private_source_map_correction_application_ready_queue.jsonl"
)
SOURCE_PRIVATE_BLOCKER_QUEUE_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_outside_scope_candidate_review_residual_difference_source_map_correction_application_readiness/private_source_map_correction_application_blocker_queue.jsonl"
)

PRIVATE_OUTPUT_DIR = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_outside_scope_candidate_review_residual_difference_source_map_correction_application"
)
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_source_map_correction_application_diagnostic.json"
PRIVATE_RESULT_PATH = PRIVATE_OUTPUT_DIR / "private_source_map_correction_application_result.json"
PRIVATE_APPLIED_RECORDS_PATH = PRIVATE_OUTPUT_DIR / "private_source_map_correction_applied_records.jsonl"
PRIVATE_RESOLUTION_OVERLAY_PATH = PRIVATE_OUTPUT_DIR / "private_source_map_correction_resolution_overlay.json"
PRIVATE_MATERIALIZATION_INPUT_PATH = PRIVATE_OUTPUT_DIR / "private_residual_difference_materialization_input_after_application.json"
PRIVATE_REPORT_PATH = PRIVATE_OUTPUT_DIR / "private_source_map_correction_application.md"

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
        "source_public_readiness_summary_read_by_this_phase": True,
        "source_public_readiness_go_no_go_read_by_this_phase": True,
        "source_public_readiness_matrix_read_by_this_phase": True,
        "source_private_readiness_diagnostic_read_by_this_phase": True,
        "source_private_ready_queue_read_by_this_phase": True,
        "source_private_blocker_queue_read_by_this_phase": True,
        "private_application_diagnostic_written_by_this_phase": True,
        "private_application_result_written_by_this_phase": True,
        "private_application_records_written_by_this_phase": True,
        "private_resolution_overlay_written_by_this_phase": True,
        "private_materialization_input_written_by_this_phase": True,
        "source_private_ready_queue_mutated_by_this_phase": False,
        "source_private_blocker_queue_mutated_by_this_phase": False,
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
        "private_readiness_diagnostic_committed": False,
        "private_ready_queue_committed": False,
        "private_blocker_queue_committed": False,
        "private_application_diagnostic_committed": False,
        "private_application_result_committed": False,
        "private_application_records_committed": False,
        "private_resolution_overlay_committed": False,
        "private_materialization_input_committed": False,
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


def _resolution_action(track: str) -> str:
    return {
        "owner_select_one_authoritative_candidate": "apply_owner_selected_authoritative_candidate_resolution",
        "provide_authoritative_source_reference_or_owner_exclusion": "apply_authoritative_source_reference_or_owner_exclusion_resolution",
        "provide_formula_or_non_numeric_mapping": "apply_formula_or_non_numeric_mapping_resolution",
    }.get(track, "apply_unknown_private_resolution")


def _build_application_records(rows: list[dict[str, Any]], generated_at: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    applied: list[dict[str, Any]] = []
    blockers: list[dict[str, Any]] = []
    seen_slots: set[str] = set()
    for index, row in enumerate(rows, start=1):
        slot_id = row.get("target_slot_id")
        track = row.get("diagnostic_track")
        if not isinstance(slot_id, str) or not slot_id:
            blockers.append({"application_queue_index": index, "blocker_code": "missing_target_slot"})
            continue
        if slot_id in seen_slots:
            blockers.append({"application_queue_index": index, "blocker_code": "duplicate_target_slot"})
            continue
        if track not in EXPECTED_TRACK_COUNTS:
            blockers.append({"application_queue_index": index, "blocker_code": "unknown_resolution_track"})
            continue
        if row.get("source_map_correction_application_ready") is not True:
            blockers.append({"application_queue_index": index, "blocker_code": "source_map_correction_not_ready"})
            continue
        if row.get("authoritative_value_resolution_application_ready") is not True:
            blockers.append({"application_queue_index": index, "blocker_code": "authoritative_resolution_not_ready"})
            continue
        seen_slots.add(slot_id)
        applied.append(
            {
                "application_index": len(applied) + 1,
                "version": VERSION,
                "phase_id": PHASE_ID,
                "task_id": TASK_ID,
                "generated_at": generated_at,
                "target_slot_id": slot_id,
                "authorization_item_id": row.get("authorization_item_id"),
                "source_final_threshold_item_id": row.get("source_final_threshold_item_id"),
                "diagnostic_track": track,
                "response_decision_code": row.get("response_decision_code"),
                "resolution_application_action": _resolution_action(track),
                "private_resolution_application_status": "applied_private_resolution_record",
                "source_map_correction_application_status": "applied_private_source_map_correction_record",
                "authoritative_value_resolution_application_status": "applied_private_authoritative_value_resolution_record",
                "source_map_correction_record_applied": True,
                "authoritative_value_resolution_record_applied": True,
                "materialization_replay_required": True,
                "raw_to_processed_value_comparison_performed": False,
                "full_reconciliation_allowed": False,
                "public_commit_allowed": False,
                "application_ready_queue_index": row.get("application_ready_queue_index"),
            }
        )
    return applied, blockers


def _build_matrix(summary: dict[str, Any], generated_at: str) -> dict[str, Any]:
    checks = [
        ("source_readiness_ready", summary["source_private_resolution_application_ready"] is True, summary["source_private_resolution_application_ready"], True),
        ("source_ready_queue_count", summary["source_ready_queue_record_count"] == 72, summary["source_ready_queue_record_count"], 72),
        ("source_blocker_queue_clear", summary["source_blocker_queue_record_count"] == 0, summary["source_blocker_queue_record_count"], 0),
        ("application_applied_count", summary["private_resolution_application_applied_record_count"] == 72, summary["private_resolution_application_applied_record_count"], 72),
        ("application_blocker_count_zero", summary["private_resolution_application_blocker_count"] == 0, summary["private_resolution_application_blocker_count"], 0),
        ("track_counts_match_expected", summary["diagnostic_track_counts"] == EXPECTED_TRACK_COUNTS, summary["diagnostic_track_counts"], EXPECTED_TRACK_COUNTS),
        ("materialization_input_prepared", summary["private_materialization_input_record_count"] == 72, summary["private_materialization_input_record_count"], 72),
        ("raw_comparison_not_performed", not summary["raw_to_processed_value_comparison_performed_by_this_phase"], False, False),
        ("full_reconciliation_not_allowed", not summary["full_reconciliation_allowed"], False, False),
        ("project_no_go_preserved", summary["decision"] == DECISION, summary["decision"], DECISION),
    ]
    rows = [
        {"check_code": code, "status": "PASS" if ok else "FAIL", "observed_public_safe": observed, "required": required}
        for code, ok, observed, required in checks
    ]
    pass_count = sum(1 for row in rows if row["status"] == "PASS")
    return {
        "schema_version": "kmfa.v014_residual_difference_source_map_correction_application_matrix_public_safe.v1",
        "record_type": "v014_residual_difference_source_map_correction_application_matrix_public_safe",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "check_count": len(rows),
        "check_pass_count": pass_count,
        "check_fail_count": len(rows) - pass_count,
        "private_resolution_application_performed": True,
        "private_resolution_application_applied_record_count": summary["private_resolution_application_applied_record_count"],
        "private_resolution_application_blocker_count": summary["private_resolution_application_blocker_count"],
        "private_materialization_input_record_count": summary["private_materialization_input_record_count"],
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "full_reconciliation_allowed": False,
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
    event_id = "DEV-KMFA-20260707-V014-RESIDUAL-DIFFERENCE-SOURCE-MAP-CORRECTION-APPLICATION"
    event = {
        "event_id": event_id,
        "event_time": manifest["generated_at"],
        "event_type": "development",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "iteration_id": "ITER-20260707-KMFA-V014-RESIDUAL-DIFFERENCE-SOURCE-MAP-CORRECTION-APPLICATION",
        "fact_level": "EXTRACTED",
        "status": STATUS,
        "go_no_go": DECISION,
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "private_resolution_application_applied_record_count": summary["private_resolution_application_applied_record_count"],
        "private_resolution_application_blocker_count": summary["private_resolution_application_blocker_count"],
        "private_materialization_input_record_count": summary["private_materialization_input_record_count"],
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "summary": "Applied 72 residual-difference private source-map correction records in ignored runtime while keeping materialization and raw comparison as later gates.",
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
            "name": "v0.1.4 residual difference source-map correction application",
            "phase_id": PHASE_ID,
            "record_type": "v014_phase",
            "roadmap_phase_id": "OUTSIDE_SCOPE_CANDIDATE_REVIEW_RESIDUAL_DIFFERENCE_SOURCE_MAP_CORRECTION_APPLICATION",
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
            "name": "72 private residual-difference resolution records applied",
            "phase_id": PHASE_ID,
            "record_type": "v014_task",
            "roadmap_phase_id": "OUTSIDE_SCOPE_CANDIDATE_REVIEW_RESIDUAL_DIFFERENCE_SOURCE_MAP_CORRECTION_APPLICATION",
            "roadmap_stage_id": "VALUE-CONSISTENCY",
            "status": "completed_validated_local_only_no_go_upload_deferred",
            "task_id": "RDSMCA01",
            "updated_at": "2026-07-07",
        },
        {
            "acceptance_id": ACCEPTANCE_ID,
            "evidence_ref": GO_NO_GO_PATH.as_posix(),
            "fact_level": "EXTRACTED",
            "governance_stage_id": "VALUE-CONSISTENCY",
            "name": "materialization replay and raw comparison remain closed after private application",
            "phase_id": PHASE_ID,
            "record_type": "v014_task",
            "roadmap_phase_id": "OUTSIDE_SCOPE_CANDIDATE_REVIEW_RESIDUAL_DIFFERENCE_SOURCE_MAP_CORRECTION_APPLICATION",
            "roadmap_stage_id": "VALUE-CONSISTENCY",
            "status": "completed_validated_local_only_no_go_upload_deferred",
            "task_id": "RDSMCA02",
            "updated_at": "2026-07-07",
        },
        {
            "acceptance_id": ACCEPTANCE_ID,
            "evidence_ref": MANIFEST_PATH.as_posix(),
            "fact_level": "EXTRACTED",
            "governance_stage_id": "VALUE-CONSISTENCY",
            "name": "raw inbox untouched and private application outputs remain ignored",
            "phase_id": PHASE_ID,
            "record_type": "v014_task",
            "roadmap_phase_id": "OUTSIDE_SCOPE_CANDIDATE_REVIEW_RESIDUAL_DIFFERENCE_SOURCE_MAP_CORRECTION_APPLICATION",
            "roadmap_stage_id": "VALUE-CONSISTENCY",
            "status": "completed_validated_local_only_no_go_upload_deferred",
            "task_id": "RDSMCA03",
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
                "Private application result manifest summary Go No-Go public-safe matrix private ignored application "
                "records validator focused test and governance records"
            )
            task_row["phase_goal"] = (
                "apply residual-difference private source-map correction records without materialization or raw comparison"
            )
        else:
            task_row["task_label"] = row["task_id"][-2:]
            task_row["task_text"] = row["name"]
        task_rows.append(task_row)
    _dedupe_append_jsonl(TASK_STATUS_PATH, task_rows, lambda existing: existing.get("phase_id") != PHASE_ID)


def _write_human_artifacts(summary: dict[str, Any], matrix: dict[str, Any]) -> None:
    report = f"""# Residual Difference Source-Map Correction Application

- phase: `{PHASE_ID}`
- status: `{STATUS}`
- decision: `{DECISION}`
- source ready queue records: `{summary["source_ready_queue_record_count"]}`
- private resolution application records applied: `{summary["private_resolution_application_applied_record_count"]}`
- private application blockers: `{summary["private_resolution_application_blocker_count"]}`
- private materialization input records prepared: `{summary["private_materialization_input_record_count"]}`
- raw-to-processed comparison performed: `false`
- next required input: `{NEXT_REQUIRED_INPUT}`

This phase applies residual-difference source-map correction / authoritative value resolution records only in ignored private runtime. Public evidence is aggregate-only and remains `NO_GO` until later materialization replay and full raw-to-processed comparison are separately completed and validated.
"""
    go_no_go_record = f"""# Go/No-Go Record

- decision: `{DECISION}`
- reason: private residual-difference correction records were applied, but materialization replay and raw-to-processed comparison were not performed in this phase.
- checks: `{matrix["check_pass_count"]}` pass / `{matrix["check_fail_count"]}` fail
- next required input: `{NEXT_REQUIRED_INPUT}`
"""
    risk_register = """# Risk Register

- Risk: private application could be mistaken for verified raw-to-processed consistency.
- Control: materialization replay, raw comparison, full reconciliation, formal report, upload, app reinstall and business execution remain closed.
"""
    rollback_plan = """# Rollback Plan

Remove this phase's public artifacts, metadata copies, private application outputs, tool, validator, focused test and governance entries. The raw data inbox is not modified by this rollback.
"""
    test_results = """# Test Results

Recorded validation commands for this phase:

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_outside_scope_candidate_review_residual_difference_source_map_correction_application.py KMFA/tools/check_v014_outside_scope_candidate_review_residual_difference_source_map_correction_application.py KMFA/tests/test_v014_outside_scope_candidate_review_residual_difference_source_map_correction_application.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_outside_scope_candidate_review_residual_difference_source_map_correction_application.py --generated-at 2026-07-07T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_outside_scope_candidate_review_residual_difference_source_map_correction_application.py --require-private-application`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_outside_scope_candidate_review_residual_difference_source_map_correction_application`
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
    source_summary = _read_json(SOURCE_READINESS_SUMMARY_PATH)
    source_go_no_go = _read_json(SOURCE_READINESS_GO_NO_GO_PATH)
    source_matrix = _read_json(SOURCE_READINESS_MATRIX_PATH)
    source_diagnostic = _read_json(SOURCE_PRIVATE_READINESS_DIAGNOSTIC_PATH)
    ready_rows = _read_jsonl(SOURCE_PRIVATE_READY_QUEUE_PATH)
    blocker_rows = _read_jsonl(SOURCE_PRIVATE_BLOCKER_QUEUE_PATH)

    if len(ready_rows) != 72 or blocker_rows:
        raise ValueError("source application readiness must provide 72 ready rows and 0 blocker rows")
    applied_records, application_blockers = _build_application_records(ready_rows, timestamp)
    track_counts = dict(Counter(row.get("diagnostic_track") for row in applied_records))
    application_complete = len(applied_records) == 72 and not application_blockers and track_counts == EXPECTED_TRACK_COUNTS
    if not application_complete:
        raise ValueError("private residual difference correction application is incomplete")

    raw_boundary = _raw_boundary()
    public_safety = _public_safety()
    private_materialization_input = {
        "schema_version": "kmfa.private.v014_residual_difference_materialization_input_after_application.v1",
        "classification": "private_residual_difference_materialization_input_do_not_commit",
        "record_type": "v014_residual_difference_materialization_input_after_application",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "private_resolution_application_applied_record_count": len(applied_records),
        "materialization_replay_ready": True,
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
        "resolution_records": applied_records,
    }
    private_resolution_overlay = {
        "schema_version": "kmfa.private.v014_residual_difference_source_map_correction_resolution_overlay.v1",
        "classification": "private_residual_difference_resolution_overlay_do_not_commit",
        "record_type": "v014_residual_difference_source_map_correction_resolution_overlay",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "track_counts": track_counts,
        "private_resolution_application_applied_record_count": len(applied_records),
        "private_resolution_application_blocker_count": len(application_blockers),
        "public_commit_policy": "do_not_commit_private_resolution_records_or_values",
        "applied_records": applied_records,
    }
    private_result = {
        "schema_version": "kmfa.private.v014_residual_difference_source_map_correction_application_result.v1",
        "classification": "private_source_map_correction_application_result_do_not_commit",
        "record_type": "v014_residual_difference_source_map_correction_application_result",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "private_resolution_application_applied_record_count": len(applied_records),
        "private_resolution_application_blocker_count": len(application_blockers),
        "materialization_replay_ready": True,
        "materialization_replay_performed": False,
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
    }
    private_diagnostic = {
        "schema_version": "kmfa.private.v014_residual_difference_source_map_correction_application_diagnostic.v1",
        "record_type": "private_residual_difference_source_map_correction_application_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "source_readiness_phase_id": source_summary.get("phase_id"),
        "source_readiness_decision": source_go_no_go.get("decision"),
        "source_readiness_check_fail_count": source_matrix.get("check_fail_count"),
        "source_private_diagnostic_phase_id": source_diagnostic.get("phase_id"),
        "private_resolution_application_applied_record_count": len(applied_records),
        "private_resolution_application_blocker_count": len(application_blockers),
        "diagnostic_track_counts": track_counts,
        "raw_inbox_accessed": False,
        "raw_inbox_mutated": False,
    }

    _write_json(PRIVATE_DIAGNOSTIC_PATH, private_diagnostic)
    _write_json(PRIVATE_RESULT_PATH, private_result)
    _write_jsonl(PRIVATE_APPLIED_RECORDS_PATH, applied_records)
    _write_json(PRIVATE_RESOLUTION_OVERLAY_PATH, private_resolution_overlay)
    _write_json(PRIVATE_MATERIALIZATION_INPUT_PATH, private_materialization_input)
    _write_text(
        PRIVATE_REPORT_PATH,
        "\n".join(
            [
                "# Private residual difference source-map correction application",
                "",
                f"- phase_id: `{PHASE_ID}`",
                f"- private_resolution_application_applied_record_count: `{len(applied_records)}`",
                f"- private_resolution_application_blocker_count: `{len(application_blockers)}`",
                "- materialization replay was not performed.",
                "- raw inbox access and mutation were not performed.",
            ]
        )
        + "\n",
    )

    summary = {
        "schema_version": "kmfa.v014_residual_difference_source_map_correction_application_summary.v1",
        "record_type": "v014_residual_difference_source_map_correction_application_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "source_readiness_phase_id": source_summary.get("phase_id"),
        "source_readiness_decision": source_summary.get("decision"),
        "source_private_resolution_application_ready": source_summary.get("private_resolution_application_ready"),
        "source_ready_queue_record_count": len(ready_rows),
        "source_blocker_queue_record_count": len(blocker_rows),
        "private_resolution_application_performed_by_this_phase": True,
        "source_map_correction_application_performed_by_this_phase": True,
        "authoritative_value_resolution_application_performed_by_this_phase": True,
        "private_resolution_application_applied_record_count": len(applied_records),
        "private_resolution_application_blocker_count": len(application_blockers),
        "source_map_correction_applied_record_count": len(applied_records),
        "authoritative_value_resolution_applied_record_count": len(applied_records),
        "private_materialization_input_record_count": len(applied_records),
        "materialization_replay_ready": True,
        "materialization_replay_performed_by_this_phase": False,
        "diagnostic_track_counts": track_counts,
        "owner_select_one_authoritative_candidate_count": track_counts.get("owner_select_one_authoritative_candidate", 0),
        "provide_authoritative_source_reference_or_owner_exclusion_count": track_counts.get(
            "provide_authoritative_source_reference_or_owner_exclusion", 0
        ),
        "provide_formula_or_non_numeric_mapping_count": track_counts.get("provide_formula_or_non_numeric_mapping", 0),
        "closed_discrepancy_count": 0,
        "open_residual_difference_count": source_summary.get("open_residual_difference_count"),
        "raw_to_processed_value_comparison_ready": False,
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
        "private_application_diagnostic_written": True,
        "private_application_diagnostic_gitignored": _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH),
        "private_application_result_written": True,
        "private_application_result_gitignored": _git_check_ignored(PRIVATE_RESULT_PATH),
        "private_application_records_written": True,
        "private_application_records_gitignored": _git_check_ignored(PRIVATE_APPLIED_RECORDS_PATH),
        "private_resolution_overlay_written": True,
        "private_resolution_overlay_gitignored": _git_check_ignored(PRIVATE_RESOLUTION_OVERLAY_PATH),
        "private_materialization_input_written": True,
        "private_materialization_input_gitignored": _git_check_ignored(PRIVATE_MATERIALIZATION_INPUT_PATH),
        "private_application_report_gitignored": _git_check_ignored(PRIVATE_REPORT_PATH),
        "raw_boundary": raw_boundary,
        "public_safety": public_safety,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
        "next_required_input": NEXT_REQUIRED_INPUT,
    }
    matrix = _build_matrix(summary, timestamp)
    go_no_go = {
        "schema_version": "kmfa.v014_residual_difference_source_map_correction_application_go_no_go.v1",
        "record_type": "v014_residual_difference_source_map_correction_application_go_no_go",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "private_resolution_application_applied_record_count": summary[
            "private_resolution_application_applied_record_count"
        ],
        "private_resolution_application_blocker_count": summary["private_resolution_application_blocker_count"],
        "materialization_replay_ready": True,
        "materialization_replay_performed_by_this_phase": False,
        "raw_to_processed_value_comparison_allowed": False,
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
        "schema_version": "kmfa.v014_residual_difference_source_map_correction_application_manifest.v1",
        "record_type": "v014_residual_difference_source_map_correction_application_manifest",
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
            SOURCE_READINESS_SUMMARY_PATH.as_posix(),
            SOURCE_READINESS_GO_NO_GO_PATH.as_posix(),
            SOURCE_READINESS_MATRIX_PATH.as_posix(),
            "private:source_map_correction_application_readiness_diagnostic",
            "private:source_map_correction_application_ready_queue",
            "private:source_map_correction_application_blocker_queue",
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
            "private:source_map_correction_application_diagnostic",
            "private:source_map_correction_application_result",
            "private:source_map_correction_applied_records",
            "private:source_map_correction_resolution_overlay",
            "private:residual_difference_materialization_input_after_application",
            "private:source_map_correction_application_report",
        ],
        "test_commands": [
            "PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_outside_scope_candidate_review_residual_difference_source_map_correction_application.py KMFA/tools/check_v014_outside_scope_candidate_review_residual_difference_source_map_correction_application.py KMFA/tests/test_v014_outside_scope_candidate_review_residual_difference_source_map_correction_application.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_outside_scope_candidate_review_residual_difference_source_map_correction_application.py --generated-at 2026-07-07T00:00:00+10:00",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_outside_scope_candidate_review_residual_difference_source_map_correction_application.py --require-private-application",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_outside_scope_candidate_review_residual_difference_source_map_correction_application",
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
        "PASS: generated V014 residual-difference source-map correction application "
        f"decision={summary['decision']} applied={summary['private_resolution_application_applied_record_count']} "
        f"blockers={summary['private_resolution_application_blocker_count']} next={summary['next_recommended_phase']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
