#!/usr/bin/env python3
"""Replay full processed value materialization after outside-scope application.

This phase consumes only ignored private inputs produced by prior KMFA v0.1.4
phases: the full 149-record processed-value source map and private processed
target staging. It materializes all 149 processed target slots in ignored
private runtime. It does not read the raw inbox, compare raw and processed
values, reconcile business values, upload GitHub, reinstall the app, publish a
formal report, or execute business actions.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


PROJECT_ROOT = Path("KMFA")
PHASE_ID = "V014_FULL_PROCESSED_VALUE_MATERIALIZATION_REPLAY_AFTER_OUTSIDE_SCOPE_APPLICATION"
TASK_ID = "KMFA-V014-FULL-PROCESSED-VALUE-MATERIALIZATION-REPLAY-AFTER-OUTSIDE-SCOPE-APPLICATION-20260707"
ACCEPTANCE_ID = "ACC-V014-FULL-PROCESSED-VALUE-MATERIALIZATION-REPLAY-AFTER-OUTSIDE-SCOPE-APPLICATION"
VERSION = "0.1.4-full-materialization-replay-after-outside-scope-application"
STATUS = "completed_validated_local_only_full_materialization_replay_no_go"
DECISION = "NO_GO"
DIAGNOSTIC_CONCLUSION = "full_processed_value_materialized_raw_to_processed_comparison_required"
NEXT_RECOMMENDED_PHASE = "V014_FULL_RAW_TO_PROCESSED_COMPARISON_PRECHECK_AFTER_FULL_MATERIALIZATION"
NEXT_REQUIRED_INPUT = "run_full_raw_to_processed_comparison_precheck_after_full_materialization"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "full_processed_value_materialization_replay_after_outside_scope_application_summary.json"
MANIFEST_PATH = MACHINE_DIR / "full_processed_value_materialization_replay_after_outside_scope_application_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "full_processed_value_materialization_replay_after_outside_scope_application_go_no_go_report.json"
MATRIX_PATH = MACHINE_DIR / "full_processed_value_materialization_replay_after_outside_scope_application_matrix_public_safe.json"
REPORT_PATH = HUMAN_DIR / "full_processed_value_materialization_replay_after_outside_scope_application_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_full_materialization_replay_after_outside_scope_application_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_full_materialization_replay_after_outside_scope_application_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_full_materialization_replay_after_outside_scope_application_go_no_go_report.json"
METADATA_MATRIX_PATH = PROJECT_ROOT / "metadata/quality/v014_full_materialization_replay_after_outside_scope_application_matrix_public_safe.json"
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"
STAGE_STATUS_PATH = PROJECT_ROOT / "metadata/stage_status.jsonl"
TASK_STATUS_PATH = PROJECT_ROOT / "metadata/traceability/v1_4_stage_phase_task_status.jsonl"

SOURCE_APPLICATION_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_outside_scope_authorized_source_map_extension_application_summary.json"
SOURCE_APPLICATION_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_outside_scope_authorized_source_map_extension_application_manifest.json"
SOURCE_FULL_SOURCE_MAP_PATH = PROJECT_ROOT / ".codex_private_runtime/v014_outside_scope_authorized_source_map_extension_application/private_full_processed_value_source_map_after_outside_scope_extension.json"
PRIVATE_STAGING_PATH = PROJECT_ROOT / ".codex_private_runtime/v014_private_processed_value_staging/private_processed_value_staging.json"

PRIVATE_OUTPUT_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_full_processed_value_materialization_replay_after_outside_scope_application"
PRIVATE_REPLAY_PATH = PRIVATE_OUTPUT_DIR / "private_full_materialization_replay.json"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_full_materialization_replay_diagnostic.json"
PRIVATE_MATERIALIZED_RECORDS_PATH = PRIVATE_OUTPUT_DIR / "private_full_materialized_records.jsonl"
PRIVATE_BLOCKED_RECORDS_PATH = PRIVATE_OUTPUT_DIR / "private_full_materialization_blocked_records.jsonl"
PRIVATE_REPORT_PATH = PRIVATE_OUTPUT_DIR / "private_full_materialization_replay.md"

FILES_CHANGED = [
    "KMFA/CHANGELOG.md",
    "KMFA/HANDOFF.md",
    "KMFA/VERSION",
    "KMFA/docs/governance/ASSURANCE_STATUS.yaml",
    "KMFA/docs/governance/DEVELOPMENT_LEDGER.md",
    "KMFA/docs/governance/MODEL_SPEC.md",
    "KMFA/docs/governance/OWNER_STATUS.md",
    "KMFA/docs/governance/STATUS.md",
    "KMFA/docs/governance/TRACEABILITY_MATRIX.csv",
    "KMFA/docs/governance/VERSION_MATRIX.yaml",
    "KMFA/docs/governance/delivery_tasks.yaml",
    "KMFA/docs/governance/development_events.jsonl",
    "KMFA/docs/governance/formula_registry.yaml",
    "KMFA/docs/governance/model_registry.yaml",
    "KMFA/docs/governance/parameter_registry.csv",
    "KMFA/metadata/stage_status.jsonl",
    "KMFA/metadata/traceability/v1_4_stage_phase_task_status.jsonl",
    "KMFA/功能清单.md",
    "KMFA/开发记录.md",
    "KMFA/模型参数文件.md",
    METADATA_SUMMARY_PATH.as_posix(),
    METADATA_MANIFEST_PATH.as_posix(),
    METADATA_GO_NO_GO_PATH.as_posix(),
    METADATA_MATRIX_PATH.as_posix(),
    SUMMARY_PATH.as_posix(),
    MANIFEST_PATH.as_posix(),
    GO_NO_GO_PATH.as_posix(),
    MATRIX_PATH.as_posix(),
    REPORT_PATH.as_posix(),
    GO_NO_GO_RECORD_PATH.as_posix(),
    TEST_RESULTS_PATH.as_posix(),
    RISK_REGISTER_PATH.as_posix(),
    ROLLBACK_PATH.as_posix(),
    "KMFA/tests/test_v014_full_processed_value_materialization_replay_after_outside_scope_application.py",
    "KMFA/tools/check_v014_full_processed_value_materialization_replay_after_outside_scope_application.py",
    "KMFA/tools/v014_full_processed_value_materialization_replay_after_outside_scope_application.py",
]


def _now(generated_at: str | None = None) -> str:
    return generated_at or datetime.now().astimezone().isoformat(timespec="seconds")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


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
        "private_full_source_map_read_by_this_phase": True,
        "private_processed_target_staging_read_by_this_phase": True,
        "private_full_materialization_replay_written_by_this_phase": True,
        "private_full_materialized_records_written_by_this_phase": True,
        "source_private_full_source_map_mutated_by_this_phase": False,
        "source_private_processed_target_staging_mutated_by_this_phase": False,
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
    }


def _public_safety() -> dict[str, bool]:
    return {
        "public_safe_aggregate_only": True,
        "private_full_source_map_committed": False,
        "private_processed_target_staging_committed": False,
        "private_full_materialization_replay_committed": False,
        "private_full_materialized_records_committed": False,
        "private_blocked_records_committed": False,
        "raw_file_committed": False,
        "raw_filename_committed": False,
        "raw_archive_member_name_committed": False,
        "raw_file_hash_committed": False,
        "field_header_plaintext_committed": False,
        "row_value_committed": False,
        "business_value_committed": False,
        "private_value_source_identifier_committed": False,
        "credential_or_secret_committed": False,
    }


def _source_records(private_source_map: dict[str, Any]) -> list[dict[str, Any]]:
    records = private_source_map.get("processed_value_sources", [])
    if not isinstance(records, list):
        raise ValueError("processed_value_sources must be a list")
    return [row for row in records if isinstance(row, dict)]


def _staging_by_slot(private_staging: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = private_staging.get("processed_target_slots", [])
    if not isinstance(rows, list):
        raise ValueError("processed_target_slots must be a list")
    slots: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        slot_id = row.get("target_slot_id")
        if isinstance(slot_id, str) and slot_id:
            slots[slot_id] = row
    return slots


def _scope_for(record: dict[str, Any]) -> str:
    if record.get("fill_status") == "linked_source_map_reapplication_applied":
        return "linked"
    if record.get("source_map_reapplication_status") == "applied_linked_source_map_record":
        return "linked"
    if record.get("fill_status") == "outside_scope_source_map_extension_applied":
        return "outside_scope_extension"
    if record.get("source_kind") == "outside_scope_owner_authorized_extension":
        return "outside_scope_extension"
    return "unknown"


def _build_private_replay(
    *,
    generated_at: str,
    application_summary: dict[str, Any],
    private_source_map: dict[str, Any],
    private_staging: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    records = _source_records(private_source_map)
    slots = _staging_by_slot(private_staging)
    materialized: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []
    seen_slots: set[str] = set()

    for index, record in enumerate(records, start=1):
        slot_id = record.get("target_slot_id")
        fingerprint = record.get("processed_value_fingerprint")
        source_scope = _scope_for(record)
        if not isinstance(slot_id, str) or not isinstance(fingerprint, str) or not fingerprint.startswith("sha256:"):
            blocked.append(
                {
                    "full_materialization_replay_index": index,
                    "target_slot_id": slot_id,
                    "source_scope": source_scope,
                    "materialization_status": "blocked_invalid_private_source_record",
                }
            )
            continue
        if slot_id in seen_slots:
            blocked.append(
                {
                    "full_materialization_replay_index": index,
                    "target_slot_id": slot_id,
                    "source_scope": source_scope,
                    "materialization_status": "blocked_duplicate_private_source_record",
                }
            )
            continue
        staging_row = slots.get(slot_id)
        if staging_row is None:
            blocked.append(
                {
                    "full_materialization_replay_index": index,
                    "target_slot_id": slot_id,
                    "source_scope": source_scope,
                    "materialization_status": "blocked_missing_processed_target_slot",
                }
            )
            continue
        seen_slots.add(slot_id)
        materialized.append(
            {
                "full_materialization_replay_index": index,
                "phase_id": PHASE_ID,
                "task_id": TASK_ID,
                "generated_at": generated_at,
                "target_slot_id": slot_id,
                "source_scope": source_scope,
                "review_group_id": record.get("review_group_id"),
                "processed_value_fingerprint": fingerprint,
                "source_candidate_rank": record.get("source_candidate_rank"),
                "source_kind": record.get("source_kind"),
                "source_record_kind": record.get("source_record_kind"),
                "source_record_ref_hash": record.get("source_record_ref_hash"),
                "source_ref_hash": record.get("source_ref_hash"),
                "source_cell_ref_hash": record.get("source_cell_ref_hash"),
                "source_sheet_ref_hash": record.get("source_sheet_ref_hash"),
                "source_map_reapplication_status": record.get("source_map_reapplication_status"),
                "source_map_extension_application_status": record.get("source_map_extension_application_status"),
                "fill_status": record.get("fill_status"),
                "source_artifact_ref_hash": staging_row.get("source_artifact_ref_hash"),
                "source_root_id": staging_row.get("source_root_id"),
                "record_ref_hash": staging_row.get("record_ref_hash"),
                "target_key_ref_hash": staging_row.get("target_key_ref_hash"),
                "context_group": staging_row.get("context_group"),
                "private_processed_ref_hash": staging_row.get("private_processed_ref_hash"),
                "value_materialized": True,
                "materialization_status": "materialized_full_processed_value",
                "raw_to_processed_value_comparison_performed": False,
                "business_value_consistency_verified": False,
            }
        )

    linked_count = sum(1 for row in materialized if row["source_scope"] == "linked")
    outside_count = sum(1 for row in materialized if row["source_scope"] == "outside_scope_extension")
    unknown_count = sum(1 for row in materialized if row["source_scope"] == "unknown")
    private_summary = {
        "source_application_phase_id": application_summary.get("phase_id"),
        "processed_target_slot_count": len(slots),
        "full_materialization_source_map_record_count": len(records),
        "full_materialized_record_count": len(materialized),
        "full_materialization_blocked_record_count": len(blocked),
        "linked_materialized_record_count": linked_count,
        "outside_scope_materialized_record_count": outside_count,
        "unknown_scope_materialized_record_count": unknown_count,
        "full_unique_private_value_source_count": len({row.get("processed_value_fingerprint") for row in materialized}),
        "full_processed_value_materialization_complete": len(slots) == 149 and len(records) == 149 and len(materialized) == 149 and not blocked,
        "full_raw_to_processed_value_comparison_ready": len(materialized) == 149 and not blocked,
        "raw_to_processed_value_comparison_performed": False,
        "full_reconciliation_allowed": False,
        "business_value_consistency_verified": False,
    }
    replay = {
        "schema_version": "kmfa.private.v014_full_materialization_replay.v1",
        "classification": "private_full_materialization_replay_do_not_commit",
        "record_type": "v014_full_materialization_replay",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "source_application_phase_id": application_summary.get("phase_id"),
        "private_summary": private_summary,
        "materialized_records": materialized,
        "blocked_records": blocked,
        "raw_boundary": _raw_boundary(),
    }
    return replay, materialized, blocked, private_summary


def _build_matrix(generated_at: str, *, summary: dict[str, Any]) -> dict[str, Any]:
    checks = [
        ("full_source_map_input_available", summary["full_materialization_source_map_record_count"] == 149, summary["full_materialization_source_map_record_count"], 149),
        ("processed_target_slots_available", summary["processed_target_slot_count"] == 149, summary["processed_target_slot_count"], 149),
        ("full_records_materialized", summary["full_materialized_record_count"] == 149, summary["full_materialized_record_count"], 149),
        ("linked_records_preserved", summary["linked_materialized_record_count"] == 77, summary["linked_materialized_record_count"], 77),
        ("outside_scope_records_materialized", summary["outside_scope_materialized_record_count"] == 72, summary["outside_scope_materialized_record_count"], 72),
        ("full_materialization_unblocked", summary["full_materialization_blocked_record_count"] == 0, summary["full_materialization_blocked_record_count"], 0),
        ("raw_comparison_not_performed", summary["raw_to_processed_value_comparison_performed_by_this_phase"] is False, False, False),
        ("downstream_no_go_preserved", summary["decision"] == DECISION, summary["decision"], DECISION),
    ]
    rows = [
        {"check_code": code, "status": "PASS" if passed else "FAIL", "observed_public_safe": observed, "required": required}
        for code, passed, observed, required in checks
    ]
    pass_count = sum(1 for row in rows if row["status"] == "PASS")
    return {
        "schema_version": "kmfa.v014_full_materialization_replay_matrix_public_safe.v1",
        "record_type": "v014_full_materialization_replay_matrix_public_safe",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "full_materialization_check_count": len(rows),
        "full_materialization_pass_count": pass_count,
        "full_materialization_fail_count": len(rows) - pass_count,
        "processed_target_slot_count": summary["processed_target_slot_count"],
        "full_materialization_source_map_record_count": summary["full_materialization_source_map_record_count"],
        "full_materialized_record_count": summary["full_materialized_record_count"],
        "linked_materialized_record_count": summary["linked_materialized_record_count"],
        "outside_scope_materialized_record_count": summary["outside_scope_materialized_record_count"],
        "full_processed_value_materialization_complete": summary["full_processed_value_materialization_complete"],
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "decision": DECISION,
        "checks": rows,
    }


def _write_human_artifacts(summary: dict[str, Any], matrix: dict[str, Any]) -> None:
    report = f"""# Full Processed Value Materialization Replay

- phase: `{PHASE_ID}`
- status: `{STATUS}`
- decision: `{DECISION}`
- processed target slots: `{summary["processed_target_slot_count"]}`
- full materialization input records: `{summary["full_materialization_source_map_record_count"]}`
- full materialized records: `{summary["full_materialized_record_count"]}`
- linked materialized records: `{summary["linked_materialized_record_count"]}`
- outside-scope materialized records: `{summary["outside_scope_materialized_record_count"]}`
- blocked records: `{summary["full_materialization_blocked_record_count"]}`
- raw-to-processed comparison ready: `{str(summary["raw_to_processed_value_comparison_ready"]).lower()}`
- raw-to-processed comparison performed: `false`
- next recommended phase: `{NEXT_RECOMMENDED_PHASE}`

This phase materializes the complete private processed-value source map into private runtime only. Raw-to-processed comparison, reconciliation, lineage full check, formal report, upload, app reinstall and business execution remain separate closed gates.
"""
    go_no_go_record = f"""# Go/No-Go Record

- decision: `{DECISION}`
- reason: full processed-value materialization is complete, but raw-to-processed comparison and business consistency verification are not complete.
- readiness checks: `{matrix["full_materialization_pass_count"]}` pass / `{matrix["full_materialization_fail_count"]}` fail
- next required input: `{NEXT_REQUIRED_INPUT}`
"""
    risk_register = """# Risk Register

- Risk: full private materialization could be mistaken for verified business consistency.
- Control: public evidence keeps raw comparison, reconciliation, lineage full check, formal report, upload, app reinstall and business execution closed.
"""
    rollback_plan = """# Rollback Plan

Remove this phase's public artifacts, metadata copies, private full materialization replay outputs, tool, validator, focused test and governance entries. The raw data inbox is not modified by this rollback.
"""
    test_results = """# Test Results

Recorded validation commands for this phase:

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_full_processed_value_materialization_replay_after_outside_scope_application.py KMFA/tools/check_v014_full_processed_value_materialization_replay_after_outside_scope_application.py KMFA/tests/test_v014_full_processed_value_materialization_replay_after_outside_scope_application.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_full_processed_value_materialization_replay_after_outside_scope_application.py --generated-at 2026-07-07T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_full_processed_value_materialization_replay_after_outside_scope_application.py --require-private-replay`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_full_processed_value_materialization_replay_after_outside_scope_application`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_project_governance.py --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/lean_governance.py validate --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_governance_sync.py --changed-only --base-ref HEAD --enforce-sync`
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


def _append_jsonl_event(path: Path, event_id: str, event: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    filtered = [line for line in existing if f'"event_id":"{event_id}"' not in line and f'"event_id": "{event_id}"' not in line]
    filtered.append(json.dumps(event, ensure_ascii=False, sort_keys=True))
    path.write_text("\n".join(filtered) + "\n", encoding="utf-8")


def _append_governance_events(generated_at: str, summary: dict[str, Any]) -> None:
    event_id = "DEV-KMFA-20260707-V014-FULL-MATERIALIZATION-REPLAY"
    event = {
        "event_id": event_id,
        "event_time": generated_at,
        "event_type": "development",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "iteration_id": "ITER-20260707-KMFA-V014-FULL-MATERIALIZATION-REPLAY",
        "fact_level": "EXTRACTED",
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "go_no_go": DECISION,
        "processed_target_slot_count": summary["processed_target_slot_count"],
        "full_materialization_source_map_record_count": summary["full_materialization_source_map_record_count"],
        "full_materialized_record_count": summary["full_materialized_record_count"],
        "linked_materialized_record_count": summary["linked_materialized_record_count"],
        "outside_scope_materialized_record_count": summary["outside_scope_materialized_record_count"],
        "full_processed_value_materialization_complete": summary["full_processed_value_materialization_complete"],
        "raw_to_processed_value_comparison_ready": summary["raw_to_processed_value_comparison_ready"],
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "result_commit": "PENDING",
        "files_changed": FILES_CHANGED,
        "summary": "Materialized all 149 processed-value source-map records in ignored private runtime while keeping raw comparison and downstream gates closed.",
    }
    _append_jsonl_event(DEVELOPMENT_EVENTS_PATH, event_id, event)
    _append_jsonl_event(
        STAGE_STATUS_PATH,
        event_id,
        {
            "event_id": event_id,
            "event_time": generated_at,
            "project_id": "KMFA",
            "stage_id": "value-consistency",
            "phase_id": PHASE_ID,
            "status": STATUS,
            "decision": DECISION,
            "next_required_input": NEXT_REQUIRED_INPUT,
            "evidence_ref": MANIFEST_PATH.as_posix(),
        },
    )
    _append_jsonl_event(
        TASK_STATUS_PATH,
        event_id,
        {
            "event_id": event_id,
            "event_time": generated_at,
            "task_id": TASK_ID,
            "phase_id": PHASE_ID,
            "acceptance_id": ACCEPTANCE_ID,
            "status": STATUS,
            "decision": DECISION,
            "evidence_ref": MANIFEST_PATH.as_posix(),
        },
    )


def generate(*, generated_at: str | None = None, write_governance_event: bool = True) -> dict[str, Any]:
    timestamp = _now(generated_at)
    application_summary = _read_json(SOURCE_APPLICATION_SUMMARY_PATH)
    _read_json(SOURCE_APPLICATION_MANIFEST_PATH)
    private_source_map = _read_json(SOURCE_FULL_SOURCE_MAP_PATH)
    private_staging = _read_json(PRIVATE_STAGING_PATH)
    replay, materialized, blocked, private_summary = _build_private_replay(
        generated_at=timestamp,
        application_summary=application_summary,
        private_source_map=private_source_map,
        private_staging=private_staging,
    )
    summary = {
        "schema_version": "kmfa.v014_full_materialization_replay_summary.v1",
        "record_type": "v014_full_materialization_replay_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "source_application_phase_id": application_summary["phase_id"],
        "source_application_decision": application_summary["decision"],
        "processed_target_slot_count": private_summary["processed_target_slot_count"],
        "full_materialization_source_map_record_count": private_summary["full_materialization_source_map_record_count"],
        "full_materialized_record_count": private_summary["full_materialized_record_count"],
        "full_materialization_blocked_record_count": private_summary["full_materialization_blocked_record_count"],
        "linked_materialized_record_count": private_summary["linked_materialized_record_count"],
        "outside_scope_materialized_record_count": private_summary["outside_scope_materialized_record_count"],
        "unknown_scope_materialized_record_count": private_summary["unknown_scope_materialized_record_count"],
        "full_unique_private_value_source_count": private_summary["full_unique_private_value_source_count"],
        "full_processed_value_materialization_replay_performed_by_this_phase": True,
        "full_processed_value_materialization_complete": private_summary["full_processed_value_materialization_complete"],
        "raw_to_processed_value_comparison_ready": private_summary["full_raw_to_processed_value_comparison_ready"],
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "full_raw_to_processed_value_comparison_complete": False,
        "full_reconciliation_allowed": False,
        "business_value_consistency_verified": False,
        "lineage_full_check_complete": False,
        "formal_report_allowed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "private_full_materialization_replay_written": True,
        "private_full_materialization_replay_gitignored": _git_check_ignored(PRIVATE_REPLAY_PATH),
        "private_full_materialized_records_written": True,
        "private_full_materialized_records_gitignored": _git_check_ignored(PRIVATE_MATERIALIZED_RECORDS_PATH),
        "private_blocked_records_written": True,
        "private_blocked_records_gitignored": _git_check_ignored(PRIVATE_BLOCKED_RECORDS_PATH),
        "private_diagnostic_written": True,
        "private_diagnostic_gitignored": _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH),
        "next_required_input": NEXT_REQUIRED_INPUT,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
        "raw_boundary": _raw_boundary(),
        "public_safety": _public_safety(),
    }
    diagnostic = {
        "schema_version": "kmfa.private.v014_full_materialization_replay_diagnostic.v1",
        "classification": "private_full_materialization_replay_diagnostic_do_not_commit",
        "record_type": "v014_full_materialization_replay_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "private_summary": private_summary,
        "raw_boundary": _raw_boundary(),
    }
    go_no_go = {
        "schema_version": "kmfa.v014_full_materialization_replay_go_no_go.v1",
        "record_type": "v014_full_materialization_replay_go_no_go",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "reason": "full_processed_value_materialized_but_raw_to_processed_comparison_not_complete",
        "processed_target_slot_count": summary["processed_target_slot_count"],
        "full_materialized_record_count": summary["full_materialized_record_count"],
        "linked_materialized_record_count": summary["linked_materialized_record_count"],
        "outside_scope_materialized_record_count": summary["outside_scope_materialized_record_count"],
        "raw_to_processed_value_comparison_ready": summary["raw_to_processed_value_comparison_ready"],
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "next_required_input": NEXT_REQUIRED_INPUT,
    }
    matrix = _build_matrix(timestamp, summary=summary)
    manifest = {
        "schema_version": "kmfa.v014_full_materialization_replay_manifest.v1",
        "record_type": "v014_full_materialization_replay_manifest",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "git_head_at_generation": _git_output(["rev-parse", "HEAD"]),
        "source_artifacts": [
            SOURCE_APPLICATION_SUMMARY_PATH.as_posix(),
            SOURCE_APPLICATION_MANIFEST_PATH.as_posix(),
            "private:full_processed_value_source_map_after_outside_scope_extension",
            "private:processed_target_staging",
        ],
        "public_artifacts": [
            SUMMARY_PATH.as_posix(),
            MANIFEST_PATH.as_posix(),
            GO_NO_GO_PATH.as_posix(),
            MATRIX_PATH.as_posix(),
            REPORT_PATH.as_posix(),
            GO_NO_GO_RECORD_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            RISK_REGISTER_PATH.as_posix(),
            ROLLBACK_PATH.as_posix(),
            METADATA_SUMMARY_PATH.as_posix(),
            METADATA_MANIFEST_PATH.as_posix(),
            METADATA_GO_NO_GO_PATH.as_posix(),
            METADATA_MATRIX_PATH.as_posix(),
        ],
        "private_artifact_refs": [
            "private:full_materialization_replay",
            "private:full_materialized_records",
            "private:full_materialization_blocked_records",
            "private:full_materialization_diagnostic",
        ],
        "validator": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_full_processed_value_materialization_replay_after_outside_scope_application.py --require-private-replay",
        "summary": summary,
        "matrix": matrix,
        "go_no_go_report": go_no_go,
    }
    _write_json(PRIVATE_REPLAY_PATH, replay)
    _write_json(PRIVATE_DIAGNOSTIC_PATH, diagnostic)
    _write_jsonl(PRIVATE_MATERIALIZED_RECORDS_PATH, materialized)
    _write_jsonl(PRIVATE_BLOCKED_RECORDS_PATH, blocked)
    _write_text(
        PRIVATE_REPORT_PATH,
        "# Private Full Materialization Replay\n\n"
        "149 processed-value records were materialized in private runtime only. This file is ignored and must not be committed.\n",
    )
    for path, payload in (
        (SUMMARY_PATH, summary),
        (MANIFEST_PATH, manifest),
        (GO_NO_GO_PATH, go_no_go),
        (MATRIX_PATH, matrix),
        (METADATA_SUMMARY_PATH, summary),
        (METADATA_MANIFEST_PATH, manifest),
        (METADATA_GO_NO_GO_PATH, go_no_go),
        (METADATA_MATRIX_PATH, matrix),
    ):
        _write_json(path, payload)
    _write_human_artifacts(summary, matrix)
    if write_governance_event:
        _append_governance_events(timestamp, summary)
    return {"summary": summary, "manifest": manifest, "matrix": matrix, "go_no_go": go_no_go}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generated-at", default=None)
    args = parser.parse_args()
    result = generate(generated_at=args.generated_at)
    summary = result["summary"]
    print(
        "PASS: KMFA v0.1.4 full materialization replay generated "
        f"(decision={summary['decision']}, materialized={summary['full_materialized_record_count']}, "
        f"comparison_ready={str(summary['raw_to_processed_value_comparison_ready']).lower()})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
