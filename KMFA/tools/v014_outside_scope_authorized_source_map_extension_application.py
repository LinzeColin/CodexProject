#!/usr/bin/env python3
"""Apply owner-authorized outside-scope source-map extensions in private runtime.

This phase consumes the ignored private application-ready queue produced by the
previous phase and writes 72 outside-scope source-map extension records to a new
ignored private runtime area. It also prepares a full 149-record private
materialization source-map input for a later phase. It does not materialize
processed values, compare raw to processed values, reconcile values, upload
GitHub, reinstall the app, or execute business steps.
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
PHASE_ID = "V014_OUTSIDE_SCOPE_AUTHORIZED_SOURCE_MAP_EXTENSION_APPLICATION"
TASK_ID = "KMFA-V014-OUTSIDE-SCOPE-AUTHORIZED-SOURCE-MAP-EXTENSION-APPLICATION-20260707"
ACCEPTANCE_ID = "ACC-V014-OUTSIDE-SCOPE-AUTHORIZED-SOURCE-MAP-EXTENSION-APPLICATION"
VERSION = "0.1.4-outside-scope-authorized-source-map-extension-application"
STATUS = "completed_validated_local_only_outside_scope_authorized_extension_application_applied_no_go"
DECISION = "NO_GO"
DIAGNOSTIC_CONCLUSION = "outside_scope_source_map_extension_applied_materialization_replay_required"
NEXT_RECOMMENDED_PHASE = "V014_FULL_PROCESSED_VALUE_MATERIALIZATION_REPLAY_AFTER_OUTSIDE_SCOPE_APPLICATION"
NEXT_REQUIRED_INPUT = "run_full_processed_value_materialization_replay_before_full_raw_to_processed_comparison"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "outside_scope_authorized_source_map_extension_application_summary.json"
MANIFEST_PATH = MACHINE_DIR / "outside_scope_authorized_source_map_extension_application_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "outside_scope_authorized_source_map_extension_application_go_no_go_report.json"
MATRIX_PATH = MACHINE_DIR / "outside_scope_authorized_source_map_extension_application_matrix_public_safe.json"
REPORT_PATH = HUMAN_DIR / "outside_scope_authorized_source_map_extension_application_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_outside_scope_authorized_source_map_extension_application_summary.json"
)
METADATA_MANIFEST_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_outside_scope_authorized_source_map_extension_application_manifest.json"
)
METADATA_GO_NO_GO_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_outside_scope_authorized_source_map_extension_application_go_no_go_report.json"
)
METADATA_MATRIX_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_outside_scope_authorized_source_map_extension_application_matrix_public_safe.json"
)
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"
STAGE_STATUS_PATH = PROJECT_ROOT / "metadata/stage_status.jsonl"
TASK_STATUS_PATH = PROJECT_ROOT / "metadata/traceability/v1_4_stage_phase_task_status.jsonl"

SOURCE_READINESS_SUMMARY_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_outside_scope_authorized_source_map_extension_application_readiness_summary.json"
)
SOURCE_READINESS_GO_NO_GO_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_outside_scope_authorized_source_map_extension_application_readiness_go_no_go_report.json"
)
SOURCE_PRIVATE_READY_QUEUE_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_outside_scope_authorized_source_map_extension_application_readiness/private_outside_scope_source_map_extension_application_ready_queue.jsonl"
)
SOURCE_PRIVATE_READINESS_DIAGNOSTIC_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_outside_scope_authorized_source_map_extension_application_readiness/private_outside_scope_source_map_extension_application_readiness_diagnostic.json"
)
SOURCE_LINKED_PRIVATE_SOURCE_MAP_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_linked_reapplication/private_processed_value_source_map.json"
)

PRIVATE_OUTPUT_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_outside_scope_authorized_source_map_extension_application"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_outside_scope_source_map_extension_application_diagnostic.json"
PRIVATE_RESULT_PATH = PRIVATE_OUTPUT_DIR / "private_outside_scope_source_map_extension_application_result.json"
PRIVATE_APPLIED_RECORDS_PATH = PRIVATE_OUTPUT_DIR / "private_outside_scope_source_map_extension_applied_records.jsonl"
PRIVATE_EXTENSION_SOURCE_MAP_PATH = PRIVATE_OUTPUT_DIR / "private_outside_scope_source_map_extension_source_map.json"
PRIVATE_FULL_MATERIALIZATION_SOURCE_MAP_PATH = (
    PRIVATE_OUTPUT_DIR / "private_full_processed_value_source_map_after_outside_scope_extension.json"
)
PRIVATE_REPORT_PATH = PRIVATE_OUTPUT_DIR / "private_outside_scope_source_map_extension_application.md"

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
    "KMFA/tests/test_v014_outside_scope_authorized_source_map_extension_application.py",
    "KMFA/tools/check_v014_outside_scope_authorized_source_map_extension_application.py",
    "KMFA/tools/v014_outside_scope_authorized_source_map_extension_application.py",
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
        "source_private_ready_queue_read_by_this_phase": True,
        "source_private_readiness_diagnostic_read_by_this_phase": True,
        "source_linked_private_source_map_read_by_this_phase": True,
        "private_outside_scope_application_diagnostic_written_by_this_phase": True,
        "private_outside_scope_application_result_written_by_this_phase": True,
        "private_outside_scope_applied_records_written_by_this_phase": True,
        "private_outside_scope_extension_source_map_written_by_this_phase": True,
        "private_full_materialization_source_map_prepared_by_this_phase": True,
        "source_private_ready_queue_mutated_by_this_phase": False,
        "source_linked_private_source_map_mutated_by_this_phase": False,
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
        "private_ready_queue_committed": False,
        "private_readiness_diagnostic_committed": False,
        "private_linked_source_map_committed": False,
        "private_outside_scope_application_diagnostic_committed": False,
        "private_outside_scope_application_result_committed": False,
        "private_outside_scope_applied_records_committed": False,
        "private_outside_scope_extension_source_map_committed": False,
        "private_full_materialization_source_map_committed": False,
        "raw_file_committed": False,
        "raw_filename_committed": False,
        "raw_archive_member_name_committed": False,
        "raw_file_hash_committed": False,
        "field_header_plaintext_committed": False,
        "row_value_committed": False,
        "business_value_committed": False,
        "private_value_fingerprint_committed": False,
        "private_source_map_committed": False,
        "credential_or_secret_committed": False,
    }


def _source_records(source_map: dict[str, Any]) -> list[dict[str, Any]]:
    rows = source_map.get("processed_value_sources", [])
    if not isinstance(rows, list):
        raise ValueError("processed_value_sources must be a list")
    return [row for row in rows if isinstance(row, dict)]


def _build_extension_records(*, ready_rows: list[dict[str, Any]], generated_at: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    extension_records: list[dict[str, Any]] = []
    blockers: list[dict[str, Any]] = []
    for row in ready_rows:
        slot_id = row.get("target_slot_id")
        fingerprint = row.get("authorized_processed_value_fingerprint")
        source_record = row.get("authorized_source_record_ref_hash")
        if not isinstance(slot_id, str) or not slot_id:
            blockers.append({"application_ready_queue_index": row.get("application_ready_queue_index"), "blocker": "missing_target_slot"})
            continue
        if not isinstance(fingerprint, str) or not fingerprint.startswith("sha256:"):
            blockers.append({"target_slot_id": slot_id, "blocker": "invalid_authorized_processed_value_fingerprint"})
            continue
        if not isinstance(source_record, str) or not source_record.startswith("sha256:"):
            blockers.append({"target_slot_id": slot_id, "blocker": "invalid_authorized_source_record_ref_hash"})
            continue
        extension_records.append(
            {
                "application_index": len(extension_records) + 1,
                "version": VERSION,
                "phase_id": PHASE_ID,
                "task_id": TASK_ID,
                "generated_at": generated_at,
                "target_slot_id": slot_id,
                "context_group": row.get("context_group"),
                "target_key_ref_hash": row.get("target_key_ref_hash"),
                "private_processed_ref_hash": row.get("private_processed_ref_hash"),
                "record_ref_hash": row.get("record_ref_hash"),
                "processed_value_fingerprint": fingerprint,
                "source_record_ref_hash": source_record,
                "source_kind": "outside_scope_owner_authorized_extension",
                "source_record_kind": "owner_authorized_outside_scope_source_record",
                "source_candidate_rank": 1,
                "fill_status": "outside_scope_source_map_extension_applied",
                "source_map_extension_application_status": "applied_outside_scope_source_map_extension",
                "source_map_record_applied": True,
                "materialization_ready": True,
                "raw_to_processed_value_comparison_performed": False,
                "full_reconciliation_allowed": False,
                "source_resolution_queue_index": row.get("source_resolution_queue_index"),
                "source_extension_queue_index": row.get("source_extension_queue_index"),
                "authorization_queue_index": row.get("authorization_queue_index"),
                "application_ready_queue_index": row.get("application_ready_queue_index"),
            }
        )

    duplicate_target_slot_count = len(extension_records) - len({row["target_slot_id"] for row in extension_records})
    diagnostics = {
        "source_ready_queue_record_count": len(ready_rows),
        "outside_scope_extension_candidate_count": len(ready_rows),
        "outside_scope_extension_applied_record_count": len(extension_records),
        "outside_scope_extension_blocker_count": len(blockers),
        "outside_scope_extension_duplicate_target_slot_count": duplicate_target_slot_count,
    }
    if len(ready_rows) != 72 or len(extension_records) != 72 or blockers or duplicate_target_slot_count:
        raise ValueError(f"outside-scope source-map extension application is incomplete: {diagnostics}")
    return extension_records, diagnostics


def _build_extension_source_map(*, generated_at: str, extension_records: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.private.v014_outside_scope_source_map_extension_source_map.v1",
        "classification": "private_outside_scope_source_map_extension_do_not_commit",
        "record_type": "v014_outside_scope_source_map_extension_private_source_map",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "source_map_scope": "outside_scope_owner_authorized_extensions_only",
        "source_map_records_written_count": len(extension_records),
        "source_map_extension_application_complete": True,
        "public_commit_policy": "do_not_commit_private_source_map_or_values",
        "processed_value_sources": extension_records,
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
    }


def _build_full_materialization_source_map(
    *, generated_at: str, linked_records: list[dict[str, Any]], extension_records: list[dict[str, Any]]
) -> dict[str, Any]:
    combined = list(linked_records) + list(extension_records)
    duplicate_target_slot_count = len(combined) - len({row.get("target_slot_id") for row in combined})
    if len(linked_records) != 77 or len(extension_records) != 72 or len(combined) != 149 or duplicate_target_slot_count:
        raise ValueError(
            "full materialization source-map input must contain 77 linked records and 72 outside-scope extension records"
        )
    return {
        "schema_version": "kmfa.private.v014_full_processed_value_source_map_after_outside_scope_extension.v1",
        "classification": "private_full_processed_value_source_map_do_not_commit",
        "record_type": "v014_full_processed_value_source_map_after_outside_scope_extension",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "source_map_scope": "linked_records_plus_outside_scope_owner_authorized_extensions",
        "linked_source_map_record_count": len(linked_records),
        "outside_scope_extension_source_map_record_count": len(extension_records),
        "source_map_records_written_count": len(combined),
        "duplicate_target_slot_count": duplicate_target_slot_count,
        "full_processed_value_materialization_ready": True,
        "public_commit_policy": "do_not_commit_private_source_map_or_values",
        "processed_value_sources": combined,
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
    }


def _build_matrix(generated_at: str, *, summary: dict[str, Any]) -> dict[str, Any]:
    checks = [
        ("readiness_gate_ready", summary["source_map_extension_application_ready"], True, True),
        ("ready_queue_count", summary["source_ready_queue_record_count"] == 72, summary["source_ready_queue_record_count"], 72),
        ("outside_scope_records_applied", summary["outside_scope_source_map_extension_applied_record_count"] == 72, summary["outside_scope_source_map_extension_applied_record_count"], 72),
        ("outside_scope_blockers_clear", summary["outside_scope_source_map_extension_blocker_count"] == 0, summary["outside_scope_source_map_extension_blocker_count"], 0),
        ("linked_records_preserved", summary["existing_linked_source_map_record_count"] == 77, summary["existing_linked_source_map_record_count"], 77),
        ("full_source_map_input_ready", summary["private_full_materialization_source_map_record_count"] == 149, summary["private_full_materialization_source_map_record_count"], 149),
        ("full_materialization_not_performed", not summary["full_processed_value_materialization_performed_by_this_phase"], False, False),
        ("raw_comparison_not_performed", not summary["raw_to_processed_value_comparison_performed_by_this_phase"], False, False),
        ("downstream_no_go_preserved", summary["decision"] == DECISION, summary["decision"], DECISION),
    ]
    rows = [
        {"check_code": code, "status": "PASS" if passed else "FAIL", "observed_public_safe": observed, "required": required}
        for code, passed, observed, required in checks
    ]
    pass_count = sum(1 for row in rows if row["status"] == "PASS")
    return {
        "schema_version": "kmfa.v014_outside_scope_source_map_extension_application_matrix_public_safe.v1",
        "record_type": "v014_outside_scope_source_map_extension_application_matrix_public_safe",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "application_check_count": len(rows),
        "application_pass_count": pass_count,
        "application_fail_count": len(rows) - pass_count,
        "source_ready_queue_record_count": summary["source_ready_queue_record_count"],
        "outside_scope_source_map_extension_applied_record_count": summary[
            "outside_scope_source_map_extension_applied_record_count"
        ],
        "outside_scope_source_map_extension_blocker_count": summary["outside_scope_source_map_extension_blocker_count"],
        "existing_linked_source_map_record_count": summary["existing_linked_source_map_record_count"],
        "private_full_materialization_source_map_record_count": summary[
            "private_full_materialization_source_map_record_count"
        ],
        "full_processed_value_materialization_ready": True,
        "full_processed_value_materialization_performed_by_this_phase": False,
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "full_reconciliation_allowed": False,
        "github_upload_performed": False,
        "decision": DECISION,
        "checks": rows,
    }


def _write_human_artifacts(summary: dict[str, Any], matrix: dict[str, Any]) -> None:
    report = f"""# Outside-Scope Source-Map Extension Application

- phase: `{PHASE_ID}`
- status: `{STATUS}`
- decision: `{DECISION}`
- application-ready records: `{summary["source_ready_queue_record_count"]}`
- outside-scope source-map records applied: `{summary["outside_scope_source_map_extension_applied_record_count"]}`
- blocked outside-scope records: `{summary["outside_scope_source_map_extension_blocker_count"]}`
- linked source-map records preserved: `{summary["existing_linked_source_map_record_count"]}`
- full private materialization source-map records prepared: `{summary["private_full_materialization_source_map_record_count"]}`
- full processed-value materialization performed: `false`
- raw-to-processed comparison performed: `false`
- next recommended phase: `{NEXT_RECOMMENDED_PHASE}`

This phase applies owner-authorized outside-scope source-map extensions only in ignored private runtime. Public evidence is aggregate-only and remains `NO_GO` until a later materialization replay and full raw-to-processed comparison are separately completed and validated.
"""
    go_no_go_record = f"""# Go/No-Go Record

- decision: `{DECISION}`
- reason: outside-scope source-map extension records were applied privately, but materialization replay and raw-to-processed comparison were not performed in this phase.
- readiness checks: `{matrix["application_pass_count"]}` pass / `{matrix["application_fail_count"]}` fail
- next required input: `{NEXT_REQUIRED_INPUT}`
"""
    risk_register = """# Risk Register

- Risk: private source-map application could be mistaken for verified business value consistency.
- Control: public evidence keeps materialization replay, raw-to-processed comparison, reconciliation, formal report, upload, app reinstall and business execution closed.
"""
    rollback_plan = """# Rollback Plan

Remove this phase's public artifacts, metadata copies, private outside-scope application outputs, tool, validator, focused test and governance entries. The raw data inbox is not modified by this rollback.
"""
    test_results = """# Test Results

Recorded validation commands for this phase:

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_outside_scope_authorized_source_map_extension_application.py KMFA/tools/check_v014_outside_scope_authorized_source_map_extension_application.py KMFA/tests/test_v014_outside_scope_authorized_source_map_extension_application.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_outside_scope_authorized_source_map_extension_application.py --generated-at 2026-07-07T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_outside_scope_authorized_source_map_extension_application.py --require-private-application`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_outside_scope_authorized_source_map_extension_application`
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
    event_id = "DEV-KMFA-20260707-V014-OUTSIDE-SCOPE-APPLICATION"
    event = {
        "event_id": event_id,
        "event_time": generated_at,
        "event_type": "development",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "iteration_id": "ITER-20260707-KMFA-V014-OUTSIDE-SCOPE-APPLICATION",
        "fact_level": "EXTRACTED",
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "go_no_go": DECISION,
        "source_ready_queue_record_count": summary["source_ready_queue_record_count"],
        "outside_scope_source_map_extension_applied_record_count": summary[
            "outside_scope_source_map_extension_applied_record_count"
        ],
        "private_full_materialization_source_map_record_count": summary[
            "private_full_materialization_source_map_record_count"
        ],
        "full_processed_value_materialization_ready": True,
        "full_processed_value_materialization_performed": False,
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "result_commit": "PENDING",
        "files_changed": FILES_CHANGED,
        "summary": "Applied 72 owner-authorized outside-scope source-map extension records in ignored private runtime and prepared a 149-record private materialization input while keeping downstream gates closed.",
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
    readiness_summary = _read_json(SOURCE_READINESS_SUMMARY_PATH)
    readiness_go_no_go = _read_json(SOURCE_READINESS_GO_NO_GO_PATH)
    readiness_diagnostic = _read_json(SOURCE_PRIVATE_READINESS_DIAGNOSTIC_PATH)
    ready_rows = _read_jsonl(SOURCE_PRIVATE_READY_QUEUE_PATH)
    linked_source_map = _read_json(SOURCE_LINKED_PRIVATE_SOURCE_MAP_PATH)
    linked_records = _source_records(linked_source_map)
    extension_records, extension_diagnostics = _build_extension_records(ready_rows=ready_rows, generated_at=timestamp)
    extension_source_map = _build_extension_source_map(generated_at=timestamp, extension_records=extension_records)
    full_source_map = _build_full_materialization_source_map(
        generated_at=timestamp,
        linked_records=linked_records,
        extension_records=extension_records,
    )

    private_diagnostic = {
        "schema_version": "kmfa.private.v014_outside_scope_source_map_extension_application_diagnostic.v1",
        "classification": "private_outside_scope_source_map_extension_application_diagnostic_do_not_commit",
        "record_type": "v014_outside_scope_source_map_extension_application_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "source_readiness_phase_id": readiness_summary.get("phase_id"),
        "source_readiness_decision": readiness_go_no_go.get("decision"),
        "source_readiness_diagnostic_phase_id": readiness_diagnostic.get("phase_id"),
        "extension_diagnostics": extension_diagnostics,
        "linked_source_map_record_count": len(linked_records),
        "full_materialization_source_map_record_count": len(full_source_map["processed_value_sources"]),
        "raw_inbox_accessed": False,
        "raw_boundary": _raw_boundary(),
    }
    private_result = {
        "schema_version": "kmfa.private.v014_outside_scope_source_map_extension_application_result.v1",
        "classification": "private_outside_scope_source_map_extension_application_result_do_not_commit",
        "record_type": "v014_outside_scope_source_map_extension_application_result",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "decision": DECISION,
        "extension_diagnostics": extension_diagnostics,
        "source_map_records_applied_count": len(extension_records),
        "full_processed_value_materialization_ready": True,
        "full_processed_value_materialization_performed": False,
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
    }
    _write_json(PRIVATE_DIAGNOSTIC_PATH, private_diagnostic)
    _write_json(PRIVATE_RESULT_PATH, private_result)
    _write_jsonl(PRIVATE_APPLIED_RECORDS_PATH, extension_records)
    _write_json(PRIVATE_EXTENSION_SOURCE_MAP_PATH, extension_source_map)
    _write_json(PRIVATE_FULL_MATERIALIZATION_SOURCE_MAP_PATH, full_source_map)
    _write_text(
        PRIVATE_REPORT_PATH,
        "# Private Outside-Scope Source-Map Extension Application\n\n"
        "72 outside-scope source-map extension records were applied to private runtime only. This file is ignored and must not be committed.\n",
    )

    summary = {
        "schema_version": "kmfa.v014_outside_scope_source_map_extension_application_summary.v1",
        "record_type": "v014_outside_scope_source_map_extension_application_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "source_readiness_phase_id": readiness_summary["phase_id"],
        "source_readiness_decision": readiness_summary["decision"],
        "source_map_extension_application_ready": readiness_summary["source_map_extension_application_ready"],
        "source_valid_authorized_extension_record_count": readiness_summary[
            "source_valid_authorized_extension_record_count"
        ],
        "source_ready_queue_record_count": extension_diagnostics["source_ready_queue_record_count"],
        "outside_scope_extension_candidate_count": extension_diagnostics["outside_scope_extension_candidate_count"],
        "outside_scope_source_map_extension_applied_record_count": extension_diagnostics[
            "outside_scope_extension_applied_record_count"
        ],
        "outside_scope_source_map_extension_blocker_count": extension_diagnostics[
            "outside_scope_extension_blocker_count"
        ],
        "outside_scope_source_map_extension_duplicate_target_slot_count": extension_diagnostics[
            "outside_scope_extension_duplicate_target_slot_count"
        ],
        "existing_linked_source_map_record_count": len(linked_records),
        "linked_source_map_preserved_by_this_phase": True,
        "source_map_extension_application_performed_by_this_phase": True,
        "source_map_extension_written_by_this_phase": True,
        "source_map_records_applied_count": len(extension_records),
        "private_outside_scope_application_diagnostic_written": True,
        "private_outside_scope_application_diagnostic_gitignored": _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH),
        "private_outside_scope_application_result_written": True,
        "private_outside_scope_application_result_gitignored": _git_check_ignored(PRIVATE_RESULT_PATH),
        "private_outside_scope_applied_records_written": True,
        "private_outside_scope_applied_records_gitignored": _git_check_ignored(PRIVATE_APPLIED_RECORDS_PATH),
        "private_outside_scope_extension_source_map_written": True,
        "private_outside_scope_extension_source_map_gitignored": _git_check_ignored(PRIVATE_EXTENSION_SOURCE_MAP_PATH),
        "private_full_materialization_source_map_prepared": True,
        "private_full_materialization_source_map_gitignored": _git_check_ignored(
            PRIVATE_FULL_MATERIALIZATION_SOURCE_MAP_PATH
        ),
        "private_full_materialization_source_map_record_count": len(full_source_map["processed_value_sources"]),
        "full_processed_value_materialization_ready": True,
        "full_processed_value_materialization_performed_by_this_phase": False,
        "raw_to_processed_value_comparison_ready": False,
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "full_raw_to_processed_value_comparison_complete": False,
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
        "schema_version": "kmfa.v014_outside_scope_source_map_extension_application_go_no_go.v1",
        "record_type": "v014_outside_scope_source_map_extension_application_go_no_go",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "reason": "outside_scope_source_map_extension_applied_privately_but_materialization_and_raw_comparison_not_performed",
        "outside_scope_source_map_extension_applied_record_count": summary[
            "outside_scope_source_map_extension_applied_record_count"
        ],
        "private_full_materialization_source_map_record_count": summary[
            "private_full_materialization_source_map_record_count"
        ],
        "full_processed_value_materialization_ready": True,
        "full_processed_value_materialization_performed_by_this_phase": False,
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "next_required_input": NEXT_REQUIRED_INPUT,
    }
    manifest = {
        "schema_version": "kmfa.v014_outside_scope_source_map_extension_application_manifest.v1",
        "record_type": "v014_outside_scope_source_map_extension_application_manifest",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "summary": summary,
        "matrix": matrix,
        "go_no_go_report": go_no_go,
        "private_artifact_refs": [
            "private:outside_scope_source_map_extension_application_diagnostic",
            "private:outside_scope_source_map_extension_application_result",
            "private:outside_scope_source_map_extension_applied_records",
            "private:outside_scope_source_map_extension_source_map",
            "private:full_processed_value_source_map_after_outside_scope_extension",
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
        ],
        "metadata_copies": [
            METADATA_SUMMARY_PATH.as_posix(),
            METADATA_MANIFEST_PATH.as_posix(),
            METADATA_GO_NO_GO_PATH.as_posix(),
            METADATA_MATRIX_PATH.as_posix(),
        ],
        "validator": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_outside_scope_authorized_source_map_extension_application.py --require-private-application",
        "git": {
            "branch": _git_output(["branch", "--show-current"]),
            "head_short": _git_output(["rev-parse", "--short=12", "HEAD"]),
            "status_short_branch": _git_output(["status", "--short", "--branch"]),
        },
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
        _append_governance_events(timestamp, summary)
    return {"summary": summary, "manifest": manifest, "go_no_go": go_no_go, "matrix": matrix}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generated-at")
    args = parser.parse_args()
    result = generate(generated_at=args.generated_at)
    summary = result["summary"]
    print(
        "PASS: KMFA v0.1.4 outside-scope source-map extension application generated "
        f"(applied_records={summary['outside_scope_source_map_extension_applied_record_count']}, "
        f"full_source_map={summary['private_full_materialization_source_map_record_count']}, "
        f"decision={summary['decision']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
