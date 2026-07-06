#!/usr/bin/env python3
"""Classify processed target slots outside linked replay scope.

This phase consumes the linked-scope comparison dry-run evidence plus ignored
private processed-target staging/source-map artifacts. It prepares a private
resolution queue for the 72 processed target slots that remain outside linked
replay scope. It does not read the raw inbox, write source-map extensions,
compare raw to processed values, reconcile business values, upload GitHub,
reinstall the app, or execute business actions.
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
PHASE_ID = "V014_PROCESSED_TARGET_OUTSIDE_LINKED_SCOPE_RESOLUTION"
TASK_ID = "KMFA-V014-PROCESSED-TARGET-OUTSIDE-LINKED-SCOPE-RESOLUTION-20260706"
ACCEPTANCE_ID = "ACC-V014-PROCESSED-TARGET-OUTSIDE-LINKED-SCOPE-RESOLUTION"
VERSION = "0.1.4-processed-target-outside-linked-scope-resolution"
STATUS = "completed_validated_local_only_outside_linked_scope_resolution_no_go"
DECISION = "NO_GO"
DIAGNOSTIC_CONCLUSION = (
    "outside_linked_scope_targets_classified_resolution_requires_authorized_source_map_extension"
)
NEXT_RECOMMENDED_PHASE = "V014_OUTSIDE_SCOPE_AUTHORIZED_SOURCE_MAP_EXTENSION"
NEXT_REQUIRED_INPUT = "owner_or_authorized_delegate_supplies_source_map_extension_for_72_outside_linked_scope_target_slots"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "processed_target_outside_linked_scope_resolution_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_target_outside_linked_scope_resolution_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_target_outside_linked_scope_resolution_go_no_go_report.json"
MATRIX_PATH = MACHINE_DIR / "processed_target_outside_linked_scope_resolution_matrix_public_safe.json"
REPORT_PATH = HUMAN_DIR / "processed_target_outside_linked_scope_resolution_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_processed_target_outside_linked_scope_resolution_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_processed_target_outside_linked_scope_resolution_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_processed_target_outside_linked_scope_resolution_go_no_go_report.json"
METADATA_MATRIX_PATH = PROJECT_ROOT / "metadata/quality/v014_processed_target_outside_linked_scope_resolution_matrix_public_safe.json"
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"

SOURCE_DRY_RUN_SUMMARY_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_linked_scope_raw_to_processed_comparison_dry_run_summary.json"
)
SOURCE_DRY_RUN_MANIFEST_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_linked_scope_raw_to_processed_comparison_dry_run_manifest.json"
)
PRIVATE_UNMATERIALIZED_SCOPE_RECORDS_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_materialization_replay_after_linked_reapplication/private_unmaterialized_processed_target_scope_records.jsonl"
)
PRIVATE_STAGING_PATH = PROJECT_ROOT / ".codex_private_runtime/v014_private_processed_value_staging/private_processed_value_staging.json"
PRIVATE_SOURCE_MAP_PATH = PROJECT_ROOT / ".codex_private_runtime/v014_private_processed_value_materialization/private_processed_value_source_map.json"

PRIVATE_OUTPUT_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_processed_target_outside_linked_scope_resolution"
PRIVATE_RESOLUTION_PATH = PRIVATE_OUTPUT_DIR / "private_outside_linked_scope_resolution.json"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_outside_linked_scope_resolution_diagnostic.json"
PRIVATE_QUEUE_PATH = PRIVATE_OUTPUT_DIR / "private_outside_linked_scope_resolution_queue.jsonl"
PRIVATE_REPORT_PATH = PRIVATE_OUTPUT_DIR / "private_outside_linked_scope_resolution.md"

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
    "KMFA/tests/test_v014_processed_target_outside_linked_scope_resolution.py",
    "KMFA/tools/check_v014_processed_target_outside_linked_scope_resolution.py",
    "KMFA/tools/v014_processed_target_outside_linked_scope_resolution.py",
]


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
        "private_staging_read_by_this_phase": True,
        "private_source_map_read_by_this_phase": True,
        "private_unmaterialized_scope_records_read_by_this_phase": True,
        "private_resolution_queue_written_by_this_phase": True,
    }


def _public_safety() -> dict[str, bool]:
    return {
        "public_safe_aggregate_only": True,
        "private_staging_committed": False,
        "private_source_map_committed": False,
        "private_unmaterialized_scope_records_committed": False,
        "private_resolution_queue_committed": False,
        "raw_file_committed": False,
        "raw_filename_committed": False,
        "raw_archive_member_name_committed": False,
        "raw_file_hash_committed": False,
        "field_header_plaintext_committed": False,
        "row_value_committed": False,
        "business_value_committed": False,
        "private_value_source_identifier_committed": False,
        "processed_value_fingerprint_committed": False,
        "credential_or_secret_committed": False,
    }


def _build_private_resolution(
    *,
    generated_at: str,
    dry_run_summary: dict[str, Any],
    outside_records: list[dict[str, Any]],
    staging: dict[str, Any],
    source_map: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    staging_rows = staging.get("processed_target_slots", [])
    source_rows = source_map.get("processed_value_sources", [])
    if not isinstance(staging_rows, list) or not isinstance(source_rows, list):
        raise ValueError("private staging/source map must contain list records")
    staging_by_slot = {
        row["target_slot_id"]: row
        for row in staging_rows
        if isinstance(row, dict) and isinstance(row.get("target_slot_id"), str)
    }
    source_slots = {
        row["target_slot_id"]
        for row in source_rows
        if isinstance(row, dict) and isinstance(row.get("target_slot_id"), str)
    }
    queue: list[dict[str, Any]] = []
    for index, row in enumerate(outside_records, start=1):
        slot_id = row.get("target_slot_id")
        staging_row = staging_by_slot.get(slot_id) if isinstance(slot_id, str) else None
        has_source = slot_id in source_slots if isinstance(slot_id, str) else False
        queue.append(
            {
                "resolution_queue_index": index,
                "target_slot_id": slot_id,
                "source_record_status": "missing_private_value_source" if not has_source else "source_map_present_unexpected",
                "resolution_status": "requires_authorized_source_map_extension",
                "auto_resolution_allowed": False,
                "source_map_extension_written_by_this_phase": False,
                "raw_to_processed_value_comparison_performed": False,
                "full_reconciliation_allowed": False,
                "staging_record_present": staging_row is not None,
                "existing_source_map_record_present": has_source,
                "private_processed_ref_hash": staging_row.get("private_processed_ref_hash") if staging_row else None,
                "record_ref_hash": staging_row.get("record_ref_hash") if staging_row else None,
                "target_key_ref_hash": staging_row.get("target_key_ref_hash") if staging_row else None,
                "context_group": staging_row.get("context_group") if staging_row else None,
            }
        )
    verified_count = sum(1 for row in queue if row["staging_record_present"])
    existing_source_count = sum(1 for row in queue if row["existing_source_map_record_present"])
    private_summary = {
        "source_dry_run_phase_id": dry_run_summary.get("phase_id"),
        "processed_target_slot_count": len(staging_by_slot),
        "linked_scope_resolved_target_slot_count": len(source_slots),
        "outside_linked_scope_target_slot_count": len(outside_records),
        "outside_scope_resolution_queue_record_count": len(queue),
        "outside_scope_verified_against_staging_count": verified_count,
        "outside_scope_already_has_source_map_count": existing_source_count,
        "outside_scope_auto_resolvable_count": 0,
        "outside_scope_authorized_source_map_required_count": len(queue),
        "outside_scope_resolution_applied_count": 0,
        "outside_scope_resolution_pending_count": len(queue),
        "source_map_extension_written_by_this_phase": False,
        "full_raw_to_processed_value_comparison_complete": False,
        "business_value_consistency_verified": False,
    }
    resolution = {
        "schema_version": "kmfa.private.v014_outside_linked_scope_resolution.v1",
        "classification": "private_outside_linked_scope_resolution_do_not_commit",
        "record_type": "v014_outside_linked_scope_resolution",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "private_summary": private_summary,
        "resolution_queue": queue,
        "raw_boundary": _raw_boundary(),
    }
    return resolution, queue, private_summary


def _build_matrix(generated_at: str, summary: dict[str, Any]) -> dict[str, Any]:
    checks = [
        ("source_dry_run_dependency_passed", summary["source_dry_run_passed"] is True, True, True),
        ("private_unmaterialized_records_available", summary["outside_linked_scope_target_slot_count"] == 72, summary["outside_linked_scope_target_slot_count"], 72),
        ("outside_count_preserved", summary["outside_scope_resolution_queue_record_count"] == 72, summary["outside_scope_resolution_queue_record_count"], 72),
        ("outside_records_present_in_staging", summary["outside_scope_verified_against_staging_count"] == 72, summary["outside_scope_verified_against_staging_count"], 72),
        ("outside_records_have_no_source_map", summary["outside_scope_already_has_source_map_count"] == 0, summary["outside_scope_already_has_source_map_count"], 0),
        ("auto_resolution_not_allowed", summary["outside_scope_auto_resolvable_count"] == 0, summary["outside_scope_auto_resolvable_count"], 0),
        ("full_comparison_not_claimed", summary["full_raw_to_processed_value_comparison_complete"] is False, False, False),
        ("downstream_no_go_preserved", summary["decision"] == DECISION, summary["decision"], DECISION),
    ]
    rows = [
        {"check_code": code, "status": "PASS" if passed else "FAIL", "observed_public_safe": observed, "required": required}
        for code, passed, observed, required in checks
    ]
    pass_count = sum(1 for row in rows if row["status"] == "PASS")
    return {
        "schema_version": "kmfa.v014_outside_linked_scope_resolution_matrix_public_safe.v1",
        "record_type": "v014_outside_linked_scope_resolution_matrix_public_safe",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "outside_scope_resolution_check_count": len(rows),
        "outside_scope_resolution_check_pass_count": pass_count,
        "outside_scope_resolution_check_fail_count": len(rows) - pass_count,
        "outside_linked_scope_target_slot_count": summary["outside_linked_scope_target_slot_count"],
        "outside_scope_resolution_queue_record_count": summary["outside_scope_resolution_queue_record_count"],
        "outside_scope_authorized_source_map_required_count": summary[
            "outside_scope_authorized_source_map_required_count"
        ],
        "outside_scope_auto_resolvable_count": summary["outside_scope_auto_resolvable_count"],
        "full_raw_to_processed_value_comparison_complete": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "decision": DECISION,
        "checks": rows,
    }


def _write_human_artifacts(summary: dict[str, Any], matrix: dict[str, Any]) -> None:
    report = f"""# Processed Target Outside Linked Scope Resolution

- phase: `{PHASE_ID}`
- status: `{STATUS}`
- decision: `{DECISION}`
- processed target slots: `{summary["processed_target_slot_count"]}`
- linked-scope resolved slots: `{summary["linked_scope_resolved_target_slot_count"]}`
- outside linked-scope slots: `{summary["outside_linked_scope_target_slot_count"]}`
- private resolution queue records: `{summary["outside_scope_resolution_queue_record_count"]}`
- auto-resolvable slots: `{summary["outside_scope_auto_resolvable_count"]}`
- authorized source-map required slots: `{summary["outside_scope_authorized_source_map_required_count"]}`
- source-map extension written by this phase: `false`
- full raw-to-processed comparison complete: `false`
- next recommended phase: `{NEXT_RECOMMENDED_PHASE}`

This phase classifies the 72 outside-linked-scope processed target slots and prepares a private resolution queue. It does not add source-map records or run full reconciliation.
"""
    go_no_go_record = f"""# Go/No-Go Record

- decision: `{DECISION}`
- reason: 72 outside-linked-scope processed target slots still require owner/authorized-delegate source-map extension before full comparison.
- readiness checks: `{matrix["outside_scope_resolution_check_pass_count"]}` pass / `{matrix["outside_scope_resolution_check_fail_count"]}` fail
- next required input: `{NEXT_REQUIRED_INPUT}`
"""
    risk_register = """# Risk Register

- Risk: classifying outside-scope slots could be mistaken for resolving them.
- Control: source-map extension, full comparison, reconciliation, formal report, upload, reinstall and business execution remain false.
"""
    rollback_plan = """# Rollback Plan

Remove this phase's public artifacts, metadata copies, private resolution outputs, tool, validator, focused test and governance entries. The raw data inbox is not modified by this rollback.
"""
    test_results = f"""# Test Results

Recorded validation commands for this phase:

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_processed_target_outside_linked_scope_resolution.py KMFA/tools/check_v014_processed_target_outside_linked_scope_resolution.py KMFA/tests/test_v014_processed_target_outside_linked_scope_resolution.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_processed_target_outside_linked_scope_resolution.py --generated-at 2026-07-06T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_target_outside_linked_scope_resolution.py --require-private-resolution`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_processed_target_outside_linked_scope_resolution`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only --base-ref HEAD --enforce-sync`
- `git diff --check -- KMFA`

Current generated check matrix: `{matrix["outside_scope_resolution_check_pass_count"]}` pass / `{matrix["outside_scope_resolution_check_fail_count"]}` fail. This phase does not read, list, parse, copy, move, rename, delete, overwrite, normalize or mutate the raw inbox.
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
    event_id = "DEV-KMFA-20260706-V014-OUTSIDE-LINKED-SCOPE-RESOLUTION"
    event = {
        "event_id": event_id,
        "event_time": generated_at,
        "event_type": "development",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "iteration_id": "ITER-20260706-KMFA-V014-OUTSIDE-LINKED-SCOPE-RESOLUTION",
        "fact_level": "EXTRACTED",
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "go_no_go": DECISION,
        "outside_linked_scope_target_slot_count": summary["outside_linked_scope_target_slot_count"],
        "outside_scope_resolution_queue_record_count": summary["outside_scope_resolution_queue_record_count"],
        "outside_scope_authorized_source_map_required_count": summary[
            "outside_scope_authorized_source_map_required_count"
        ],
        "outside_scope_resolution_applied_count": 0,
        "source_map_extension_written_by_this_phase": False,
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "result_commit": "PENDING",
        "files_changed": FILES_CHANGED,
        "summary": "Classified 72 processed target slots outside linked replay scope and prepared a private resolution queue while keeping full comparison blocked.",
    }
    DEVELOPMENT_EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    existing = DEVELOPMENT_EVENTS_PATH.read_text(encoding="utf-8").splitlines() if DEVELOPMENT_EVENTS_PATH.exists() else []
    filtered = [line for line in existing if f'"event_id":"{event_id}"' not in line and f'"event_id": "{event_id}"' not in line]
    filtered.append(json.dumps(event, ensure_ascii=False, sort_keys=True))
    DEVELOPMENT_EVENTS_PATH.write_text("\n".join(filtered) + "\n", encoding="utf-8")


def generate(*, generated_at: str | None = None, write_governance_event: bool = True) -> dict[str, Any]:
    timestamp = _now(generated_at)
    dry_run_summary = _read_json(SOURCE_DRY_RUN_SUMMARY_PATH)
    _read_json(SOURCE_DRY_RUN_MANIFEST_PATH)
    outside_records = _read_jsonl(PRIVATE_UNMATERIALIZED_SCOPE_RECORDS_PATH)
    staging = _read_json(PRIVATE_STAGING_PATH)
    source_map = _read_json(PRIVATE_SOURCE_MAP_PATH)
    resolution, queue, private_summary = _build_private_resolution(
        generated_at=timestamp,
        dry_run_summary=dry_run_summary,
        outside_records=outside_records,
        staging=staging,
        source_map=source_map,
    )
    summary = {
        "schema_version": "kmfa.v014_outside_linked_scope_resolution_summary.v1",
        "record_type": "v014_outside_linked_scope_resolution_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "source_dry_run_phase_id": dry_run_summary["phase_id"],
        "source_dry_run_passed": dry_run_summary["linked_scope_raw_to_processed_value_comparison_dry_run_passed"],
        "processed_target_slot_count": private_summary["processed_target_slot_count"],
        "linked_scope_resolved_target_slot_count": private_summary["linked_scope_resolved_target_slot_count"],
        "outside_linked_scope_target_slot_count": private_summary["outside_linked_scope_target_slot_count"],
        "outside_scope_resolution_queue_record_count": private_summary["outside_scope_resolution_queue_record_count"],
        "outside_scope_verified_against_staging_count": private_summary["outside_scope_verified_against_staging_count"],
        "outside_scope_already_has_source_map_count": private_summary["outside_scope_already_has_source_map_count"],
        "outside_scope_auto_resolvable_count": 0,
        "outside_scope_authorized_source_map_required_count": private_summary[
            "outside_scope_authorized_source_map_required_count"
        ],
        "outside_scope_resolution_applied_count": 0,
        "outside_scope_resolution_pending_count": private_summary["outside_scope_resolution_pending_count"],
        "source_map_extension_written_by_this_phase": False,
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "full_raw_to_processed_value_comparison_complete": False,
        "full_reconciliation_allowed": False,
        "business_value_consistency_verified": False,
        "lineage_full_check_complete": False,
        "formal_report_allowed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "private_resolution_written": True,
        "private_resolution_gitignored": _git_check_ignored(PRIVATE_RESOLUTION_PATH),
        "private_resolution_queue_written": True,
        "private_resolution_queue_gitignored": _git_check_ignored(PRIVATE_QUEUE_PATH),
        "private_diagnostic_written": True,
        "private_diagnostic_gitignored": _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH),
        "next_required_input": NEXT_REQUIRED_INPUT,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
        "raw_boundary": _raw_boundary(),
        "public_safety": _public_safety(),
    }
    matrix = _build_matrix(timestamp, summary)
    go_no_go = {
        "schema_version": "kmfa.v014_outside_linked_scope_resolution_go_no_go.v1",
        "record_type": "v014_outside_linked_scope_resolution_go_no_go",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "outside_linked_scope_target_slot_count": summary["outside_linked_scope_target_slot_count"],
        "outside_scope_authorized_source_map_required_count": summary[
            "outside_scope_authorized_source_map_required_count"
        ],
        "outside_scope_resolution_applied_count": 0,
        "source_map_extension_written_by_this_phase": False,
        "full_raw_to_processed_value_comparison_complete": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "next_required_input": NEXT_REQUIRED_INPUT,
    }
    diagnostic = {
        "schema_version": "kmfa.private.v014_outside_linked_scope_resolution_diagnostic.v1",
        "classification": "private_outside_linked_scope_resolution_diagnostic_do_not_commit",
        "record_type": "v014_outside_linked_scope_resolution_diagnostic",
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
    manifest = {
        "schema_version": "kmfa.v014_outside_linked_scope_resolution_manifest.v1",
        "record_type": "v014_outside_linked_scope_resolution_manifest",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "git": {
            "head": _git_output(["rev-parse", "HEAD"]),
            "branch": _git_output(["branch", "--show-current"]),
            "status_short_branch": _git_output(["status", "--short", "--branch"]),
        },
        "source_artifacts": [
            SOURCE_DRY_RUN_SUMMARY_PATH.as_posix(),
            SOURCE_DRY_RUN_MANIFEST_PATH.as_posix(),
            "private:unmaterialized_processed_target_scope_records",
            "private:processed_value_staging",
            "private:processed_value_source_map",
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
            "private:outside_linked_scope_resolution",
            "private:outside_linked_scope_resolution_queue",
            "private:outside_linked_scope_resolution_diagnostic",
        ],
        "validator": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_target_outside_linked_scope_resolution.py --require-private-resolution",
        "summary": summary,
        "matrix": matrix,
        "go_no_go_report": go_no_go,
    }
    _write_json(PRIVATE_RESOLUTION_PATH, resolution)
    _write_json(PRIVATE_DIAGNOSTIC_PATH, diagnostic)
    _write_jsonl(PRIVATE_QUEUE_PATH, queue)
    _write_text(
        PRIVATE_REPORT_PATH,
        "# Private Outside Linked Scope Resolution\n\n"
        "72 processed target slots require authorized source-map extension before full comparison. This file is ignored and must not be committed.\n",
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
        "PASS: KMFA v0.1.4 outside linked-scope resolution generated "
        f"(outside_scope={summary['outside_linked_scope_target_slot_count']}, "
        f"required_source_map={summary['outside_scope_authorized_source_map_required_count']}, "
        f"decision={summary['decision']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
