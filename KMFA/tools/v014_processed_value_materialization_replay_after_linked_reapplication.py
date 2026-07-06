#!/usr/bin/env python3
"""Replay processed value materialization after linked source-map reapplication.

This phase consumes the linked source-map reapplication summary, the ignored
private materialization source-map input, and the ignored private processed
target staging output. It materializes only the 77 linked-scope records in
ignored private runtime. It does not read the raw inbox, compare raw and
processed values, reconcile business values, upload GitHub, reinstall the app,
or execute business actions.
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
PHASE_ID = "V014_PROCESSED_VALUE_MATERIALIZATION_REPLAY_AFTER_LINKED_REAPPLICATION"
TASK_ID = "KMFA-V014-PROCESSED-VALUE-MATERIALIZATION-REPLAY-AFTER-LINKED-REAPPLICATION-20260706"
ACCEPTANCE_ID = "ACC-V014-PROCESSED-VALUE-MATERIALIZATION-REPLAY-AFTER-LINKED-REAPPLICATION"
VERSION = "0.1.4-linked-materialization-replay"
STATUS = "completed_validated_local_only_linked_materialization_replay_no_go"
DECISION = "NO_GO"
DIAGNOSTIC_CONCLUSION = "linked_scope_materialized_full_materialization_and_raw_comparison_not_complete"
NEXT_RECOMMENDED_PHASE = "V014_LINKED_SCOPE_RAW_TO_PROCESSED_COMPARISON_PRECHECK"
NEXT_REQUIRED_INPUT = "run_linked_scope_raw_to_processed_comparison_precheck_phase"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "processed_value_materialization_replay_after_linked_reapplication_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_value_materialization_replay_after_linked_reapplication_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_value_materialization_replay_after_linked_reapplication_go_no_go_report.json"
MATRIX_PATH = MACHINE_DIR / "processed_value_materialization_replay_after_linked_reapplication_matrix_public_safe.json"
REPORT_PATH = HUMAN_DIR / "processed_value_materialization_replay_after_linked_reapplication_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_linked_materialization_replay_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_linked_materialization_replay_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_linked_materialization_replay_go_no_go_report.json"
METADATA_MATRIX_PATH = PROJECT_ROOT / "metadata/quality/v014_linked_materialization_replay_matrix_public_safe.json"
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"

SOURCE_LINKED_REAPPLICATION_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_linked_source_map_reapplication_summary.json"
SOURCE_LINKED_REAPPLICATION_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_linked_source_map_reapplication_manifest.json"
PRIVATE_LINKED_SOURCE_MAP_PATH = (
    PROJECT_ROOT / ".codex_private_runtime/v014_private_processed_value_materialization/private_processed_value_source_map.json"
)
PRIVATE_STAGING_PATH = PROJECT_ROOT / ".codex_private_runtime/v014_private_processed_value_staging/private_processed_value_staging.json"

PRIVATE_OUTPUT_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_processed_value_materialization_replay_after_linked_reapplication"
PRIVATE_REPLAY_PATH = PRIVATE_OUTPUT_DIR / "private_linked_materialization_replay.json"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_linked_materialization_replay_diagnostic.json"
PRIVATE_MATERIALIZED_RECORDS_PATH = PRIVATE_OUTPUT_DIR / "private_linked_materialized_records.jsonl"
PRIVATE_UNMATERIALIZED_SCOPE_RECORDS_PATH = PRIVATE_OUTPUT_DIR / "private_unmaterialized_processed_target_scope_records.jsonl"
PRIVATE_REPORT_PATH = PRIVATE_OUTPUT_DIR / "private_linked_materialization_replay.md"

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
    "KMFA/docs/governance/events.jsonl",
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
    "KMFA/tests/test_v014_processed_value_materialization_replay_after_linked_reapplication.py",
    "KMFA/tools/check_v014_processed_value_materialization_replay_after_linked_reapplication.py",
    "KMFA/tools/v014_processed_value_materialization_replay_after_linked_reapplication.py",
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
        "private_linked_source_map_read_by_this_phase": True,
        "private_processed_target_staging_read_by_this_phase": True,
        "private_linked_materialization_replay_written_by_this_phase": True,
    }


def _public_safety() -> dict[str, bool]:
    return {
        "public_safe_aggregate_only": True,
        "private_linked_source_map_committed": False,
        "private_processed_target_staging_committed": False,
        "private_linked_materialization_replay_committed": False,
        "private_linked_materialized_records_committed": False,
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


def _load_slots(private_staging: dict[str, Any]) -> dict[str, dict[str, Any]]:
    slots = private_staging.get("processed_target_slots", [])
    if not isinstance(slots, list):
        raise ValueError("processed_target_slots must be a list")
    by_slot: dict[str, dict[str, Any]] = {}
    for row in slots:
        if not isinstance(row, dict):
            continue
        slot_id = row.get("target_slot_id")
        if isinstance(slot_id, str) and slot_id:
            by_slot[slot_id] = row
    return by_slot


def _load_source_records(private_source_map: dict[str, Any]) -> list[dict[str, Any]]:
    records = private_source_map.get("processed_value_sources", [])
    if not isinstance(records, list):
        raise ValueError("processed_value_sources must be a list")
    return [row for row in records if isinstance(row, dict)]


def _build_private_replay(
    *,
    generated_at: str,
    linked_summary: dict[str, Any],
    private_source_map: dict[str, Any],
    private_staging: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    source_records = _load_source_records(private_source_map)
    staging_by_slot = _load_slots(private_staging)
    materialized: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []
    for record in source_records:
        slot_id = record.get("target_slot_id")
        fingerprint = record.get("processed_value_fingerprint")
        if not isinstance(slot_id, str) or not isinstance(fingerprint, str) or not fingerprint.startswith("sha256:"):
            blocked.append(
                {
                    "target_slot_id": slot_id,
                    "review_group_id": record.get("review_group_id"),
                    "linked_materialization_status": "blocked_invalid_private_source_record",
                }
            )
            continue
        staging_row = staging_by_slot.get(slot_id)
        if staging_row is None:
            blocked.append(
                {
                    "target_slot_id": slot_id,
                    "review_group_id": record.get("review_group_id"),
                    "linked_materialization_status": "blocked_missing_processed_target_slot",
                }
            )
            continue
        materialized.append(
            {
                "target_slot_id": slot_id,
                "review_group_id": record.get("review_group_id"),
                "processed_value_fingerprint": fingerprint,
                "source_candidate_rank": record.get("source_candidate_rank"),
                "source_record_ref_hash": record.get("source_record_ref_hash"),
                "source_ref_hash": record.get("source_ref_hash"),
                "source_cell_ref_hash": record.get("source_cell_ref_hash"),
                "source_sheet_ref_hash": record.get("source_sheet_ref_hash"),
                "source_record_kind": record.get("source_record_kind"),
                "source_kind": record.get("source_kind"),
                "source_map_reapplication_status": record.get("source_map_reapplication_status"),
                "source_artifact_ref_hash": staging_row.get("source_artifact_ref_hash"),
                "source_root_id": staging_row.get("source_root_id"),
                "record_ref_hash": staging_row.get("record_ref_hash"),
                "target_key_ref_hash": staging_row.get("target_key_ref_hash"),
                "context_group": staging_row.get("context_group"),
                "private_processed_ref_hash": staging_row.get("private_processed_ref_hash"),
                "value_materialized": True,
                "linked_materialization_status": "materialized_linked_scope_private_value_source",
                "raw_to_processed_value_comparison_performed": False,
            }
        )
    materialized_slot_ids = {row["target_slot_id"] for row in materialized}
    outside_scope = [
        {
            "target_slot_id": slot_id,
            "linked_materialization_status": "outside_linked_replay_scope_missing_private_value_source",
            "value_materialized": False,
        }
        for slot_id in sorted(set(staging_by_slot) - materialized_slot_ids)
    ]
    private_summary = {
        "linked_reapplication_phase_id": linked_summary.get("phase_id"),
        "processed_target_slot_count": len(staging_by_slot),
        "linked_materialization_source_map_record_count": len(source_records),
        "linked_materialized_record_count": len(materialized),
        "linked_materialization_blocked_record_count": len(blocked),
        "linked_unique_private_value_source_count": len({row.get("processed_value_fingerprint") for row in materialized}),
        "processed_target_slot_outside_linked_replay_scope_count": len(outside_scope),
        "linked_scope_materialization_replay_complete": len(source_records) == 77 and len(materialized) == 77 and not blocked,
        "full_processed_value_materialization_complete": len(staging_by_slot) == len(materialized) and not blocked,
        "linked_scope_raw_to_processed_value_comparison_ready": len(materialized) == 77 and not blocked,
        "raw_to_processed_value_comparison_ready": False,
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
    }
    replay = {
        "schema_version": "kmfa.private.v014_linked_materialization_replay.v1",
        "classification": "private_linked_materialization_replay_do_not_commit",
        "record_type": "v014_linked_materialization_replay",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "source_linked_reapplication_phase_id": linked_summary.get("phase_id"),
        "private_summary": private_summary,
        "materialized_linked_records": materialized,
        "blocked_linked_records": blocked,
        "unmaterialized_processed_target_scope_records": outside_scope,
        "raw_boundary": _raw_boundary(),
    }
    return replay, materialized, outside_scope, private_summary


def _build_matrix(generated_at: str, *, summary: dict[str, Any]) -> dict[str, Any]:
    checks = [
        ("linked_source_map_input_available", summary["linked_materialization_source_map_record_count"] == 77, summary["linked_materialization_source_map_record_count"], 77),
        ("linked_records_materialized", summary["linked_materialized_record_count"] == 77, summary["linked_materialized_record_count"], 77),
        ("linked_materialization_unblocked", summary["linked_materialization_blocked_record_count"] == 0, summary["linked_materialization_blocked_record_count"], 0),
        ("full_materialization_not_claimed", summary["full_processed_value_materialization_complete"] is False, False, False),
        ("raw_comparison_not_performed", summary["raw_to_processed_value_comparison_performed_by_this_phase"] is False, False, False),
        ("downstream_no_go_preserved", summary["decision"] == DECISION, summary["decision"], DECISION),
    ]
    rows = [
        {"check_code": code, "status": "PASS" if passed else "FAIL", "observed_public_safe": observed, "required": required}
        for code, passed, observed, required in checks
    ]
    pass_count = sum(1 for row in rows if row["status"] == "PASS")
    return {
        "schema_version": "kmfa.v014_linked_materialization_replay_matrix_public_safe.v1",
        "record_type": "v014_linked_materialization_replay_matrix_public_safe",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "linked_materialization_check_count": len(rows),
        "linked_materialization_pass_count": pass_count,
        "linked_materialization_fail_count": len(rows) - pass_count,
        "processed_target_slot_count": summary["processed_target_slot_count"],
        "linked_materialization_source_map_record_count": summary["linked_materialization_source_map_record_count"],
        "linked_materialized_record_count": summary["linked_materialized_record_count"],
        "processed_target_slot_outside_linked_replay_scope_count": summary[
            "processed_target_slot_outside_linked_replay_scope_count"
        ],
        "full_processed_value_materialization_complete": False,
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "decision": DECISION,
        "checks": rows,
    }


def _write_human_artifacts(summary: dict[str, Any], matrix: dict[str, Any]) -> None:
    report = f"""# Linked Materialization Replay

- phase: `{PHASE_ID}`
- status: `{STATUS}`
- decision: `{DECISION}`
- processed target slots: `{summary["processed_target_slot_count"]}`
- linked materialization input records: `{summary["linked_materialization_source_map_record_count"]}`
- linked materialized records: `{summary["linked_materialized_record_count"]}`
- linked blocked records: `{summary["linked_materialization_blocked_record_count"]}`
- processed target slots outside linked replay scope: `{summary["processed_target_slot_outside_linked_replay_scope_count"]}`
- linked-scope comparison precheck ready: `{str(summary["linked_scope_raw_to_processed_value_comparison_ready"]).lower()}`
- raw-to-processed comparison performed: `false`
- next recommended phase: `{NEXT_RECOMMENDED_PHASE}`

This phase materializes linked-scope private value sources only. Full materialization and raw-to-processed comparison remain separate gates.
"""
    go_no_go_record = f"""# Go/No-Go Record

- decision: `{DECISION}`
- reason: linked scope materialized, but full materialization and raw-to-processed comparison are not complete.
- readiness checks: `{matrix["linked_materialization_pass_count"]}` pass / `{matrix["linked_materialization_fail_count"]}` fail
- next required input: `{NEXT_REQUIRED_INPUT}`
"""
    risk_register = """# Risk Register

- Risk: linked-scope materialization could be mistaken for full processed-data reconciliation.
- Control: public evidence keeps full materialization, raw comparison, reconciliation, formal report, upload and business execution closed.
"""
    rollback_plan = """# Rollback Plan

Remove this phase's public artifacts, metadata copies, private linked materialization replay outputs, tool, validator, focused test and governance entries. The raw data inbox is not modified by this rollback.
"""
    test_results = """# Test Results

Recorded validation commands for this phase:

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_processed_value_materialization_replay_after_linked_reapplication.py KMFA/tools/check_v014_processed_value_materialization_replay_after_linked_reapplication.py KMFA/tests/test_v014_processed_value_materialization_replay_after_linked_reapplication.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_processed_value_materialization_replay_after_linked_reapplication.py --generated-at 2026-07-06T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_value_materialization_replay_after_linked_reapplication.py --require-private-replay`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_processed_value_materialization_replay_after_linked_reapplication`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only --base-ref HEAD --enforce-sync`
- `git diff --check -- KMFA`

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


def _append_development_event(generated_at: str, summary: dict[str, Any]) -> None:
    event_id = "DEV-KMFA-20260706-V014-LINKED-MATERIALIZATION-REPLAY"
    event = {
        "event_id": event_id,
        "event_time": generated_at,
        "event_type": "development",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "iteration_id": "ITER-20260706-KMFA-V014-LINKED-MATERIALIZATION-REPLAY",
        "fact_level": "EXTRACTED",
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "go_no_go": DECISION,
        "processed_target_slot_count": summary["processed_target_slot_count"],
        "linked_materialization_source_map_record_count": summary["linked_materialization_source_map_record_count"],
        "linked_materialized_record_count": summary["linked_materialized_record_count"],
        "processed_target_slot_outside_linked_replay_scope_count": summary[
            "processed_target_slot_outside_linked_replay_scope_count"
        ],
        "linked_scope_raw_to_processed_value_comparison_ready": summary[
            "linked_scope_raw_to_processed_value_comparison_ready"
        ],
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "result_commit": "PENDING",
        "files_changed": FILES_CHANGED,
        "summary": "Replayed linked-scope processed value materialization for 77 private records while keeping raw comparison and full reconciliation gates closed.",
    }
    DEVELOPMENT_EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    existing = DEVELOPMENT_EVENTS_PATH.read_text(encoding="utf-8").splitlines() if DEVELOPMENT_EVENTS_PATH.exists() else []
    filtered = [line for line in existing if f'"event_id":"{event_id}"' not in line and f'"event_id": "{event_id}"' not in line]
    filtered.append(json.dumps(event, ensure_ascii=False, sort_keys=True))
    DEVELOPMENT_EVENTS_PATH.write_text("\n".join(filtered) + "\n", encoding="utf-8")


def generate(*, generated_at: str | None = None, write_governance_event: bool = True) -> dict[str, Any]:
    timestamp = _now(generated_at)
    linked_summary = _read_json(SOURCE_LINKED_REAPPLICATION_SUMMARY_PATH)
    _read_json(SOURCE_LINKED_REAPPLICATION_MANIFEST_PATH)
    private_source_map = _read_json(PRIVATE_LINKED_SOURCE_MAP_PATH)
    private_staging = _read_json(PRIVATE_STAGING_PATH)
    replay, materialized, outside_scope, private_summary = _build_private_replay(
        generated_at=timestamp,
        linked_summary=linked_summary,
        private_source_map=private_source_map,
        private_staging=private_staging,
    )
    summary = {
        "schema_version": "kmfa.v014_linked_materialization_replay_summary.v1",
        "record_type": "v014_linked_materialization_replay_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "source_linked_reapplication_phase_id": linked_summary["phase_id"],
        "source_linked_reapplication_decision": linked_summary["decision"],
        "processed_target_slot_count": private_summary["processed_target_slot_count"],
        "linked_materialization_source_map_record_count": private_summary[
            "linked_materialization_source_map_record_count"
        ],
        "linked_materialized_record_count": private_summary["linked_materialized_record_count"],
        "linked_materialization_blocked_record_count": private_summary["linked_materialization_blocked_record_count"],
        "linked_unique_private_value_source_count": private_summary["linked_unique_private_value_source_count"],
        "processed_target_slot_outside_linked_replay_scope_count": private_summary[
            "processed_target_slot_outside_linked_replay_scope_count"
        ],
        "linked_scope_materialization_replay_performed_by_this_phase": True,
        "linked_scope_materialization_replay_complete": private_summary["linked_scope_materialization_replay_complete"],
        "full_processed_value_materialization_complete": False,
        "linked_scope_raw_to_processed_value_comparison_ready": private_summary[
            "linked_scope_raw_to_processed_value_comparison_ready"
        ],
        "raw_to_processed_value_comparison_ready": False,
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "full_reconciliation_allowed": False,
        "business_value_consistency_verified": False,
        "lineage_full_check_complete": False,
        "formal_report_allowed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "private_linked_materialization_replay_written": True,
        "private_linked_materialization_replay_gitignored": _git_check_ignored(PRIVATE_REPLAY_PATH),
        "private_linked_materialized_records_written": True,
        "private_linked_materialized_records_gitignored": _git_check_ignored(PRIVATE_MATERIALIZED_RECORDS_PATH),
        "private_unmaterialized_scope_records_written": True,
        "private_unmaterialized_scope_records_gitignored": _git_check_ignored(PRIVATE_UNMATERIALIZED_SCOPE_RECORDS_PATH),
        "private_diagnostic_written": True,
        "private_diagnostic_gitignored": _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH),
        "next_required_input": NEXT_REQUIRED_INPUT,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
        "raw_boundary": _raw_boundary(),
        "public_safety": _public_safety(),
    }
    diagnostic = {
        "schema_version": "kmfa.private.v014_linked_materialization_replay_diagnostic.v1",
        "classification": "private_linked_materialization_replay_diagnostic_do_not_commit",
        "record_type": "v014_linked_materialization_replay_diagnostic",
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
        "schema_version": "kmfa.v014_linked_materialization_replay_go_no_go.v1",
        "record_type": "v014_linked_materialization_replay_go_no_go",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "reason": "linked_scope_materialized_but_full_materialization_and_raw_comparison_not_complete",
        "linked_materialized_record_count": summary["linked_materialized_record_count"],
        "processed_target_slot_outside_linked_replay_scope_count": summary[
            "processed_target_slot_outside_linked_replay_scope_count"
        ],
        "linked_scope_raw_to_processed_value_comparison_ready": summary[
            "linked_scope_raw_to_processed_value_comparison_ready"
        ],
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "next_required_input": NEXT_REQUIRED_INPUT,
    }
    matrix = _build_matrix(timestamp, summary=summary)
    manifest = {
        "schema_version": "kmfa.v014_linked_materialization_replay_manifest.v1",
        "record_type": "v014_linked_materialization_replay_manifest",
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
            SOURCE_LINKED_REAPPLICATION_SUMMARY_PATH.as_posix(),
            SOURCE_LINKED_REAPPLICATION_MANIFEST_PATH.as_posix(),
            "private:linked_materialization_source_map_input",
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
            "private:linked_materialization_replay",
            "private:linked_materialized_records",
            "private:unmaterialized_processed_target_scope_records",
            "private:linked_materialization_diagnostic",
        ],
        "validator": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_value_materialization_replay_after_linked_reapplication.py --require-private-replay",
        "summary": summary,
        "matrix": matrix,
        "go_no_go_report": go_no_go,
    }
    _write_json(PRIVATE_REPLAY_PATH, replay)
    _write_json(PRIVATE_DIAGNOSTIC_PATH, diagnostic)
    _write_jsonl(PRIVATE_MATERIALIZED_RECORDS_PATH, materialized)
    _write_jsonl(PRIVATE_UNMATERIALIZED_SCOPE_RECORDS_PATH, outside_scope)
    _write_text(
        PRIVATE_REPORT_PATH,
        "# Private Linked Materialization Replay\n\n"
        "77 linked-scope records were materialized in private runtime only. This file is ignored and must not be committed.\n",
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
        _append_development_event(timestamp, summary)
    return {"summary": summary, "manifest": manifest, "matrix": matrix, "go_no_go": go_no_go}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generated-at", default=None)
    args = parser.parse_args()
    result = generate(generated_at=args.generated_at)
    summary = result["summary"]
    print(
        "PASS: KMFA v0.1.4 linked materialization replay generated "
        f"(decision={summary['decision']}, materialized={summary['linked_materialized_record_count']}, "
        f"outside_scope={summary['processed_target_slot_outside_linked_replay_scope_count']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
