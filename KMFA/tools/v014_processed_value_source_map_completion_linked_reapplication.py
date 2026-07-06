#!/usr/bin/env python3
"""Apply linked source-map reapplication records in ignored private runtime.

This phase consumes the prior post-resolution linked candidate queue and the
existing private partial value-source fill. It writes the 77 linked source-map
records to ignored private runtime and stages the private materialization
source-map input. It does not read the raw inbox, materialize processed values,
compare raw and processed values, reconcile business values, upload GitHub,
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
PHASE_ID = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_LINKED_REAPPLICATION"
TASK_ID = "KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-LINKED-REAPPLICATION-20260706"
ACCEPTANCE_ID = "ACC-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-LINKED-REAPPLICATION"
VERSION = "0.1.4-linked-source-map-reapplication"
STATUS = "completed_validated_local_only_linked_source_map_reapplied_no_go"
DECISION = "NO_GO"
DIAGNOSTIC_CONCLUSION = "linked_source_map_records_reapplied_materialization_replay_required"
NEXT_RECOMMENDED_PHASE = "V014_PROCESSED_VALUE_MATERIALIZATION_REPLAY_AFTER_LINKED_REAPPLICATION"
NEXT_REQUIRED_INPUT = "run_processed_value_materialization_replay_phase"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "processed_value_source_map_completion_linked_reapplication_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_value_source_map_completion_linked_reapplication_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_value_source_map_completion_linked_reapplication_go_no_go_report.json"
MATRIX_PATH = MACHINE_DIR / "processed_value_source_map_completion_linked_reapplication_matrix_public_safe.json"
REPORT_PATH = HUMAN_DIR / "processed_value_source_map_completion_linked_reapplication_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_linked_source_map_reapplication_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_linked_source_map_reapplication_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_linked_source_map_reapplication_go_no_go_report.json"
METADATA_MATRIX_PATH = PROJECT_ROOT / "metadata/quality/v014_linked_source_map_reapplication_matrix_public_safe.json"
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"

SOURCE_POST_RESOLUTION_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_post_resolution_readiness_recheck_summary.json"
SOURCE_POST_RESOLUTION_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_post_resolution_readiness_recheck_manifest.json"
PRIVATE_POST_RESOLUTION_CANDIDATE_QUEUE_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_post_resolution_readiness_recheck/private_post_resolution_reapplication_candidate_queue.jsonl"
)
PRIVATE_PARTIAL_VALUE_SOURCE_FILL_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_partial_value_source_fill/private_partial_value_source_fill.json"
)

PRIVATE_OUTPUT_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_processed_value_source_map_completion_linked_reapplication"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_linked_source_map_reapplication_diagnostic.json"
PRIVATE_RESULT_PATH = PRIVATE_OUTPUT_DIR / "private_linked_source_map_reapplication_result.json"
PRIVATE_APPLIED_RECORDS_PATH = PRIVATE_OUTPUT_DIR / "private_linked_source_map_reapplication_applied_records.jsonl"
PRIVATE_SOURCE_MAP_PATH = PRIVATE_OUTPUT_DIR / "private_processed_value_source_map.json"
PRIVATE_REPORT_PATH = PRIVATE_OUTPUT_DIR / "private_linked_source_map_reapplication.md"
PRIVATE_MATERIALIZATION_SOURCE_MAP_PATH = (
    PROJECT_ROOT / ".codex_private_runtime/v014_private_processed_value_materialization/private_processed_value_source_map.json"
)

FILES_CHANGED = [
    "KMFA/CHANGELOG.md",
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
    "KMFA/tests/test_v014_processed_value_source_map_completion_linked_reapplication.py",
    "KMFA/tools/check_v014_processed_value_source_map_completion_linked_reapplication.py",
    "KMFA/tools/v014_processed_value_source_map_completion_linked_reapplication.py",
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
        "private_post_resolution_candidate_queue_read_by_this_phase": True,
        "private_partial_value_source_fill_read_by_this_phase": True,
        "private_linked_reapplication_result_written_by_this_phase": True,
        "private_linked_reapplication_records_written_by_this_phase": True,
        "private_linked_reapplication_source_map_written_by_this_phase": True,
        "private_materialization_source_map_staged_by_this_phase": True,
    }


def _public_safety() -> dict[str, bool]:
    return {
        "public_safe_aggregate_only": True,
        "private_post_resolution_candidate_queue_committed": False,
        "private_partial_value_source_fill_committed": False,
        "private_linked_reapplication_diagnostic_committed": False,
        "private_linked_reapplication_result_committed": False,
        "private_linked_reapplication_records_committed": False,
        "private_linked_reapplication_source_map_committed": False,
        "private_materialization_source_map_committed": False,
        "raw_file_committed": False,
        "raw_filename_committed": False,
        "raw_archive_member_name_committed": False,
        "raw_file_hash_committed": False,
        "field_header_plaintext_committed": False,
        "row_value_committed": False,
        "business_value_committed": False,
        "processed_value_private_fingerprint_committed": False,
        "credential_or_secret_committed": False,
    }


def _candidate_group_ids(candidate_rows: list[dict[str, Any]]) -> set[str]:
    group_ids: set[str] = set()
    for row in candidate_rows:
        group_id = row.get("review_group_id")
        if not isinstance(group_id, str) or not group_id:
            raise ValueError("candidate queue contains a missing review group id")
        group_ids.add(group_id)
    return group_ids


def _build_linked_records(
    *,
    candidate_rows: list[dict[str, Any]],
    private_fill: dict[str, Any],
    generated_at: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    candidate_groups = _candidate_group_ids(candidate_rows)
    expected_count = sum(int(row.get("linked_application_blocker_count", 0)) for row in candidate_rows)
    processed_value_sources = private_fill.get("processed_value_sources", [])
    if not isinstance(processed_value_sources, list):
        raise ValueError("processed_value_sources must be a list")

    linked_records: list[dict[str, Any]] = []
    for row in processed_value_sources:
        if not isinstance(row, dict):
            continue
        if row.get("review_group_id") not in candidate_groups:
            continue
        record = dict(row)
        record.update(
            {
                "application_index": len(linked_records) + 1,
                "version": VERSION,
                "phase_id": PHASE_ID,
                "task_id": TASK_ID,
                "generated_at": generated_at,
                "source_map_reapplication_status": "applied_linked_source_map_record",
                "source_map_record_applied": True,
                "materialization_ready": True,
                "raw_to_processed_value_comparison_performed": False,
                "full_reconciliation_allowed": False,
            }
        )
        linked_records.append(record)

    linked_groups = {row.get("review_group_id") for row in linked_records}
    missing_groups = candidate_groups - linked_groups
    duplicate_slot_count = len(linked_records) - len({row.get("target_slot_id") for row in linked_records})
    blocked_count = expected_count - len(linked_records)
    diagnostics = {
        "expected_linked_candidate_group_count": len(candidate_groups),
        "expected_linked_candidate_record_count": expected_count,
        "linked_reapplication_applied_group_count": len(linked_groups),
        "linked_reapplication_applied_record_count": len(linked_records),
        "linked_reapplication_blocked_record_count": blocked_count,
        "missing_candidate_group_count": len(missing_groups),
        "duplicate_target_slot_count": duplicate_slot_count,
        "unique_private_fingerprint_count": len({row.get("processed_value_fingerprint") for row in linked_records}),
    }
    if diagnostics["linked_reapplication_applied_group_count"] != 15 or len(linked_records) != 77:
        raise ValueError(f"expected 15 linked groups and 77 records, got {diagnostics}")
    if blocked_count != 0 or missing_groups or duplicate_slot_count != 0:
        raise ValueError(f"linked reapplication is incomplete: {diagnostics}")
    return linked_records, diagnostics


def _build_private_source_map(*, generated_at: str, linked_records: list[dict[str, Any]]) -> dict[str, Any]:
    source_records = []
    for record in linked_records:
        source_records.append(
            {
                "target_slot_id": record.get("target_slot_id"),
                "review_group_id": record.get("review_group_id"),
                "processed_value_fingerprint": record.get("processed_value_fingerprint"),
                "fill_status": "linked_source_map_reapplication_applied",
                "source_map_reapplication_status": record.get("source_map_reapplication_status"),
                "source_candidate_rank": record.get("source_candidate_rank"),
                "source_record_ref_hash": record.get("source_record_ref_hash"),
                "source_ref_hash": record.get("source_ref_hash"),
                "source_cell_ref_hash": record.get("source_cell_ref_hash"),
                "source_sheet_ref_hash": record.get("source_sheet_ref_hash"),
                "source_record_kind": record.get("source_record_kind"),
                "source_kind": record.get("source_kind"),
            }
        )
    return {
        "schema_version": "kmfa.private.v014_linked_source_map_reapplication_source_map.v1",
        "classification": "private_processed_value_source_map_do_not_commit",
        "record_type": "v014_linked_source_map_reapplication_private_processed_value_source_map",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "source_map_scope": "linked_post_resolution_candidates_only",
        "source_map_records_written_count": len(source_records),
        "source_map_reapplication_complete": True,
        "public_commit_policy": "do_not_commit_private_source_map_or_values",
        "processed_value_sources": source_records,
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
    }


def _build_matrix(generated_at: str, *, summary: dict[str, Any]) -> dict[str, Any]:
    checks = [
        ("post_resolution_candidate_queue_available", summary["post_resolution_reapplication_candidate_count"] == 77, summary["post_resolution_reapplication_candidate_count"], 77),
        ("linked_groups_matched", summary["linked_reapplication_applied_group_count"] == 15, summary["linked_reapplication_applied_group_count"], 15),
        ("linked_records_applied", summary["linked_reapplication_applied_record_count"] == 77, summary["linked_reapplication_applied_record_count"], 77),
        ("linked_records_unblocked", summary["linked_reapplication_blocked_record_count"] == 0, summary["linked_reapplication_blocked_record_count"], 0),
        ("private_source_map_written", summary["private_processed_value_source_map_written"], True, True),
        ("private_materialization_input_staged", summary["private_materialization_source_map_staged"], True, True),
        ("materialization_not_performed", not summary["processed_value_materialization_replay_performed"], False, False),
        ("raw_comparison_not_performed", not summary["raw_to_processed_value_comparison_performed_by_this_phase"], False, False),
        ("downstream_no_go_preserved", summary["decision"] == DECISION, summary["decision"], DECISION),
    ]
    rows = [
        {"check_code": code, "status": "PASS" if passed else "FAIL", "observed_public_safe": observed, "required": required}
        for code, passed, observed, required in checks
    ]
    pass_count = sum(1 for row in rows if row["status"] == "PASS")
    return {
        "schema_version": "kmfa.v014_linked_source_map_reapplication_matrix_public_safe.v1",
        "record_type": "v014_linked_source_map_reapplication_matrix_public_safe",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "linked_reapplication_check_count": len(rows),
        "linked_reapplication_pass_count": pass_count,
        "linked_reapplication_fail_count": len(rows) - pass_count,
        "linked_reapplication_candidate_group_count": summary["linked_reapplication_candidate_group_count"],
        "linked_reapplication_candidate_record_count": summary["linked_reapplication_candidate_record_count"],
        "linked_reapplication_applied_group_count": summary["linked_reapplication_applied_group_count"],
        "linked_reapplication_applied_record_count": summary["linked_reapplication_applied_record_count"],
        "linked_reapplication_blocked_record_count": summary["linked_reapplication_blocked_record_count"],
        "source_map_records_applied_count": summary["source_map_records_applied_count"],
        "private_materialization_source_map_record_count": summary["private_materialization_source_map_record_count"],
        "processed_value_materialization_replay_ready": summary["processed_value_materialization_replay_ready"],
        "processed_value_materialization_replay_performed": False,
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "full_reconciliation_allowed": False,
        "github_upload_performed": False,
        "decision": DECISION,
        "checks": rows,
    }


def _write_human_artifacts(summary: dict[str, Any], matrix: dict[str, Any]) -> None:
    report = f"""# Linked Source-Map Reapplication

- phase: `{PHASE_ID}`
- status: `{STATUS}`
- decision: `{DECISION}`
- linked candidate groups: `{summary["linked_reapplication_candidate_group_count"]}`
- linked candidate records: `{summary["linked_reapplication_candidate_record_count"]}`
- linked source-map records applied: `{summary["linked_reapplication_applied_record_count"]}`
- blocked linked records: `{summary["linked_reapplication_blocked_record_count"]}`
- private materialization source-map records staged: `{summary["private_materialization_source_map_record_count"]}`
- materialization replay performed: `false`
- raw-to-processed comparison performed: `false`
- next recommended phase: `{NEXT_RECOMMENDED_PHASE}`

This phase applies linked source-map records only in ignored private runtime. Public evidence is aggregate-only and remains `NO_GO` until materialization replay and raw-to-processed comparison are separately completed and validated.
"""
    go_no_go_record = f"""# Go/No-Go Record

- decision: `{DECISION}`
- reason: linked source-map records were applied privately, but processed value materialization replay and raw-to-processed comparison were not performed in this phase.
- readiness checks: `{matrix["linked_reapplication_pass_count"]}` pass / `{matrix["linked_reapplication_fail_count"]}` fail
- next required input: `{NEXT_REQUIRED_INPUT}`
"""
    risk_register = """# Risk Register

- Risk: private source-map reapplication could be mistaken for verified business value consistency.
- Control: public evidence keeps materialization replay, raw-to-processed comparison, reconciliation, formal report, upload and business execution closed.
"""
    rollback_plan = """# Rollback Plan

Remove this phase's public artifacts, metadata copies, private linked reapplication outputs, tool, validator, focused test and governance entries. The raw data inbox is not modified by this rollback.
"""
    test_results = """# Test Results

Recorded validation commands for this phase:

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_processed_value_source_map_completion_linked_reapplication.py KMFA/tools/check_v014_processed_value_source_map_completion_linked_reapplication.py KMFA/tests/test_v014_processed_value_source_map_completion_linked_reapplication.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_processed_value_source_map_completion_linked_reapplication.py --generated-at 2026-07-06T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_value_source_map_completion_linked_reapplication.py --require-private-reapplication`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_processed_value_source_map_completion_linked_reapplication`
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
    event_id = "DEV-KMFA-20260706-V014-LINKED-SOURCE-MAP-REAPPLICATION"
    event = {
        "event_id": event_id,
        "event_time": generated_at,
        "event_type": "development",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "iteration_id": "ITER-20260706-KMFA-V014-LINKED-SOURCE-MAP-REAPPLICATION",
        "fact_level": "EXTRACTED",
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "go_no_go": DECISION,
        "linked_reapplication_candidate_group_count": summary["linked_reapplication_candidate_group_count"],
        "linked_reapplication_candidate_record_count": summary["linked_reapplication_candidate_record_count"],
        "linked_reapplication_applied_group_count": summary["linked_reapplication_applied_group_count"],
        "linked_reapplication_applied_record_count": summary["linked_reapplication_applied_record_count"],
        "source_map_records_applied_count": summary["source_map_records_applied_count"],
        "private_materialization_source_map_record_count": summary["private_materialization_source_map_record_count"],
        "processed_value_materialization_replay_ready": True,
        "processed_value_materialization_replay_performed": False,
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "result_commit": "PENDING",
        "files_changed": FILES_CHANGED,
        "summary": "Applied 77 linked source-map records in ignored private runtime and staged private materialization input while keeping downstream gates closed.",
    }
    DEVELOPMENT_EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    existing = DEVELOPMENT_EVENTS_PATH.read_text(encoding="utf-8").splitlines() if DEVELOPMENT_EVENTS_PATH.exists() else []
    filtered = [line for line in existing if f'"event_id":"{event_id}"' not in line and f'"event_id": "{event_id}"' not in line]
    filtered.append(json.dumps(event, ensure_ascii=False, sort_keys=True))
    DEVELOPMENT_EVENTS_PATH.write_text("\n".join(filtered) + "\n", encoding="utf-8")


def generate(*, generated_at: str | None = None, write_governance_event: bool = True) -> dict[str, Any]:
    timestamp = _now(generated_at)
    post_resolution_summary = _read_json(SOURCE_POST_RESOLUTION_SUMMARY_PATH)
    _read_json(SOURCE_POST_RESOLUTION_MANIFEST_PATH)
    candidate_rows = _read_jsonl(PRIVATE_POST_RESOLUTION_CANDIDATE_QUEUE_PATH)
    private_fill = _read_json(PRIVATE_PARTIAL_VALUE_SOURCE_FILL_PATH)
    linked_records, linked_diagnostics = _build_linked_records(
        candidate_rows=candidate_rows,
        private_fill=private_fill,
        generated_at=timestamp,
    )
    private_source_map = _build_private_source_map(generated_at=timestamp, linked_records=linked_records)

    private_diagnostic = {
        "schema_version": "kmfa.private.v014_linked_source_map_reapplication_diagnostic.v1",
        "classification": "private_linked_source_map_reapplication_diagnostic_do_not_commit",
        "record_type": "v014_linked_source_map_reapplication_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "source_post_resolution_readiness_phase_id": post_resolution_summary.get("phase_id"),
        "linked_diagnostics": linked_diagnostics,
        "raw_inbox_accessed": False,
        "raw_boundary": _raw_boundary(),
    }
    private_result = {
        "schema_version": "kmfa.private.v014_linked_source_map_reapplication_result.v1",
        "classification": "private_linked_source_map_reapplication_result_do_not_commit",
        "record_type": "v014_linked_source_map_reapplication_result",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "decision": DECISION,
        "linked_diagnostics": linked_diagnostics,
        "source_map_records_applied_count": len(linked_records),
        "processed_value_materialization_replay_ready": True,
        "processed_value_materialization_replay_performed": False,
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
    }
    _write_json(PRIVATE_DIAGNOSTIC_PATH, private_diagnostic)
    _write_json(PRIVATE_RESULT_PATH, private_result)
    _write_jsonl(PRIVATE_APPLIED_RECORDS_PATH, linked_records)
    _write_json(PRIVATE_SOURCE_MAP_PATH, private_source_map)
    _write_json(PRIVATE_MATERIALIZATION_SOURCE_MAP_PATH, private_source_map)
    _write_text(
        PRIVATE_REPORT_PATH,
        "# Private Linked Source-Map Reapplication\n\n"
        "77 linked source-map records were applied to private runtime only. This file is ignored and must not be committed.\n",
    )

    summary = {
        "schema_version": "kmfa.v014_linked_source_map_reapplication_summary.v1",
        "record_type": "v014_linked_source_map_reapplication_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "source_post_resolution_readiness_phase_id": post_resolution_summary["phase_id"],
        "source_post_resolution_readiness_decision": post_resolution_summary["decision"],
        "owner_exclusion_resolution_applied_count": post_resolution_summary["owner_exclusion_resolution_applied_count"],
        "source_linked_application_blocker_count": post_resolution_summary["source_linked_application_blocker_count"],
        "post_resolution_reapplication_candidate_group_count": post_resolution_summary[
            "post_resolution_reapplication_candidate_group_count"
        ],
        "post_resolution_reapplication_candidate_count": post_resolution_summary[
            "post_resolution_reapplication_candidate_count"
        ],
        "post_resolution_blocker_group_count": post_resolution_summary["post_resolution_blocker_group_count"],
        "post_resolution_open_unlinked_blocker_count": post_resolution_summary[
            "post_resolution_open_unlinked_blocker_count"
        ],
        "linked_reapplication_candidate_group_count": linked_diagnostics["expected_linked_candidate_group_count"],
        "linked_reapplication_candidate_record_count": linked_diagnostics["expected_linked_candidate_record_count"],
        "linked_reapplication_applied_group_count": linked_diagnostics["linked_reapplication_applied_group_count"],
        "linked_reapplication_applied_record_count": linked_diagnostics["linked_reapplication_applied_record_count"],
        "linked_reapplication_blocked_record_count": linked_diagnostics["linked_reapplication_blocked_record_count"],
        "source_map_completion_reapplication_ready": True,
        "source_map_completion_reapplication_performed_by_this_phase": True,
        "source_map_mutation_performed_by_this_phase": True,
        "source_map_records_applied_count": len(linked_records),
        "private_processed_value_source_map_written": True,
        "private_processed_value_source_map_gitignored": _git_check_ignored(PRIVATE_SOURCE_MAP_PATH),
        "private_materialization_source_map_staged": True,
        "private_materialization_source_map_gitignored": _git_check_ignored(PRIVATE_MATERIALIZATION_SOURCE_MAP_PATH),
        "private_materialization_source_map_record_count": len(private_source_map["processed_value_sources"]),
        "private_linked_reapplication_diagnostic_written": True,
        "private_linked_reapplication_diagnostic_gitignored": _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH),
        "private_linked_reapplication_result_written": True,
        "private_linked_reapplication_result_gitignored": _git_check_ignored(PRIVATE_RESULT_PATH),
        "private_linked_reapplication_records_written": True,
        "private_linked_reapplication_records_gitignored": _git_check_ignored(PRIVATE_APPLIED_RECORDS_PATH),
        "processed_value_materialization_replay_ready": True,
        "processed_value_materialization_replay_performed": False,
        "raw_to_processed_value_comparison_ready": False,
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "full_reconciliation_allowed": False,
        "business_value_consistency_verified": False,
        "lineage_full_check_complete": False,
        "formal_report_allowed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "next_required_input": NEXT_REQUIRED_INPUT,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
        "raw_boundary": _raw_boundary(),
        "public_safety": _public_safety(),
    }
    matrix = _build_matrix(timestamp, summary=summary)
    go_no_go = {
        "schema_version": "kmfa.v014_linked_source_map_reapplication_go_no_go.v1",
        "record_type": "v014_linked_source_map_reapplication_go_no_go",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "reason": "linked_source_map_records_applied_privately_but_materialization_and_raw_comparison_not_performed",
        "linked_reapplication_candidate_record_count": summary["linked_reapplication_candidate_record_count"],
        "linked_reapplication_applied_record_count": summary["linked_reapplication_applied_record_count"],
        "source_map_records_applied_count": summary["source_map_records_applied_count"],
        "processed_value_materialization_replay_ready": True,
        "processed_value_materialization_replay_performed": False,
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "next_required_input": NEXT_REQUIRED_INPUT,
    }
    manifest = {
        "schema_version": "kmfa.v014_linked_source_map_reapplication_manifest.v1",
        "record_type": "v014_linked_source_map_reapplication_manifest",
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
            SOURCE_POST_RESOLUTION_SUMMARY_PATH.as_posix(),
            SOURCE_POST_RESOLUTION_MANIFEST_PATH.as_posix(),
            "private:post_resolution_reapplication_candidate_queue",
            "private:partial_value_source_fill",
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
            "private:linked_source_map_reapplication_diagnostic",
            "private:linked_source_map_reapplication_result",
            "private:linked_source_map_reapplication_applied_records",
            "private:linked_reapplication_processed_value_source_map",
            "private:materialization_processed_value_source_map_input",
        ],
        "validator": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_value_source_map_completion_linked_reapplication.py --require-private-reapplication",
        "summary": summary,
        "matrix": matrix,
        "go_no_go_report": go_no_go,
    }
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
        "PASS: KMFA v0.1.4 linked source-map reapplication generated "
        f"(decision={summary['decision']}, source_map_records={summary['source_map_records_applied_count']}, "
        f"materialization_input={summary['private_materialization_source_map_record_count']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
