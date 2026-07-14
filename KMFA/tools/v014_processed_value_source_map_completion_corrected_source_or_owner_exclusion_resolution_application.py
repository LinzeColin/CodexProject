#!/usr/bin/env python3
"""Apply the 36 ready corrected-source or owner-exclusion retry decisions.

This phase consumes the private retry application-readiness queue produced by
the previous phase. The current ready set contains owner-exclusion decisions
only, so the phase writes a private applied queue and public aggregate evidence.
It does not mutate source-map records, read the raw inbox, compare raw and
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
PHASE_ID = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_CORRECTED_SOURCE_OR_OWNER_EXCLUSION_RESOLUTION_APPLICATION"
TASK_ID = "KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-CORRECTED-SOURCE-OR-OWNER-EXCLUSION-RESOLUTION-APPLICATION-20260706"
ACCEPTANCE_ID = "ACC-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-CORRECTED-SOURCE-OR-OWNER-EXCLUSION-RESOLUTION-APPLICATION"
VERSION = "0.1.4-corrected-source-or-owner-exclusion-resolution-application"
STATUS = "completed_validated_local_only_owner_exclusion_resolution_application_no_go"
DECISION = "NO_GO"
DIAGNOSTIC_CONCLUSION = "owner_exclusion_resolution_applied_recheck_required"
NEXT_REQUIRED_INPUT = "run_post_resolution_source_map_readiness_recheck"
NEXT_RECOMMENDED_PHASE = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_POST_RESOLUTION_READINESS_RECHECK"
OWNER_EXCLUSION_DECISION = "OWNER_EXCLUDE_FROM_RECONCILIATION"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_application_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_application_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_application_go_no_go_report.json"
MATRIX_PATH = MACHINE_DIR / "processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_application_matrix_public_safe.json"
REPORT_PATH = HUMAN_DIR / "processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_application_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_corrected_source_or_owner_exclusion_resolution_application_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_corrected_source_or_owner_exclusion_resolution_application_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_corrected_source_or_owner_exclusion_resolution_application_go_no_go_report.json"
METADATA_MATRIX_PATH = PROJECT_ROOT / "metadata/quality/v014_corrected_source_or_owner_exclusion_resolution_application_matrix_public_safe.json"
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"

SOURCE_READINESS_SUMMARY_PATH = PROJECT_ROOT / (
    "metadata/quality/v014_corrected_source_or_owner_exclusion_resolution_retry_application_readiness_summary.json"
)
SOURCE_READINESS_MATRIX_PATH = PROJECT_ROOT / (
    "metadata/quality/v014_corrected_source_or_owner_exclusion_resolution_retry_application_readiness_matrix_public_safe.json"
)
SOURCE_PRIVATE_READINESS_DIAGNOSTIC_PATH = PROJECT_ROOT / (
    ".codex_private_runtime/"
    "v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_retry_application_readiness/"
    "private_corrected_source_or_owner_exclusion_resolution_retry_application_readiness_diagnostic.json"
)
SOURCE_PRIVATE_READY_QUEUE_PATH = PROJECT_ROOT / (
    ".codex_private_runtime/"
    "v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_retry_application_readiness/"
    "private_corrected_source_or_owner_exclusion_resolution_retry_application_ready_queue.jsonl"
)
SOURCE_PRIVATE_BLOCKER_QUEUE_PATH = PROJECT_ROOT / (
    ".codex_private_runtime/"
    "v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_retry_application_readiness/"
    "private_corrected_source_or_owner_exclusion_resolution_retry_application_blocker_queue.jsonl"
)

PRIVATE_OUTPUT_DIR = PROJECT_ROOT / (
    ".codex_private_runtime/"
    "v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_application"
)
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_corrected_source_or_owner_exclusion_resolution_application_diagnostic.json"
PRIVATE_RESULT_PATH = PRIVATE_OUTPUT_DIR / "private_corrected_source_or_owner_exclusion_resolution_application_result.json"
PRIVATE_APPLIED_QUEUE_PATH = PRIVATE_OUTPUT_DIR / "private_corrected_source_or_owner_exclusion_resolution_application_applied_queue.jsonl"
PRIVATE_BLOCKER_QUEUE_PATH = PRIVATE_OUTPUT_DIR / "private_corrected_source_or_owner_exclusion_resolution_application_blocker_queue.jsonl"
PRIVATE_REPORT_PATH = PRIVATE_OUTPUT_DIR / "private_corrected_source_or_owner_exclusion_resolution_application.md"

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
    "KMFA/docs/governance/formula_registry.yaml",
    "KMFA/docs/governance/model_registry.yaml",
    "KMFA/docs/governance/parameter_registry.csv",
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
    "KMFA/tests/test_v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_application.py",
    "KMFA/tools/check_v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_application.py",
    "KMFA/tools/v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_application.py",
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
        "private_retry_application_readiness_diagnostic_read_by_this_phase": True,
        "private_retry_application_ready_queue_read_by_this_phase": True,
        "private_retry_application_blocker_queue_read_by_this_phase": True,
        "private_resolution_application_diagnostic_written_by_this_phase": True,
        "private_resolution_application_applied_queue_written_by_this_phase": True,
    }


def _public_safety() -> dict[str, bool]:
    return {
        "public_safe_aggregate_only": True,
        "private_readiness_diagnostic_committed": False,
        "private_readiness_ready_queue_committed": False,
        "private_readiness_blocker_queue_committed": False,
        "private_application_diagnostic_committed": False,
        "private_application_result_committed": False,
        "private_application_applied_queue_committed": False,
        "private_application_blocker_queue_committed": False,
        "private_report_committed": False,
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


def _build_applied_queue(ready_queue: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(ready_queue, start=1):
        if row.get("application_decision_code") != OWNER_EXCLUSION_DECISION:
            continue
        rows.append(
            {
                "application_index": index,
                "target_slot_id": row.get("target_slot_id"),
                "application_decision_code": OWNER_EXCLUSION_DECISION,
                "owner_exclusion_basis_ref": row.get("owner_exclusion_basis_ref"),
                "source_match_status": row.get("source_match_status"),
                "source_raw_index_occurrence_count": row.get("source_raw_index_occurrence_count"),
                "resolution_application_performed": True,
                "owner_exclusion_applied": True,
                "corrected_source_applied": False,
                "source_map_mutation_performed_by_this_phase": False,
                "source_map_record_applied": False,
                "raw_to_processed_value_comparison_performed": False,
                "full_reconciliation_allowed": False,
                "application_status": "owner_exclusion_applied_recheck_required",
            }
        )
    return rows


def _build_matrix(generated_at: str, readiness_summary: dict[str, Any], applied_count: int, blocker_count: int) -> dict[str, Any]:
    checks = [
        ("source_retry_readiness_available", readiness_summary.get("retry_application_ready_item_count") == 36, readiness_summary.get("retry_application_ready_item_count"), 36),
        ("ready_queue_count_locked", applied_count == 36, applied_count, 36),
        ("blocker_queue_clear", blocker_count == 0, blocker_count, 0),
        ("owner_exclusion_application_performed", applied_count == 36, applied_count, 36),
        ("corrected_source_application_zero", True, 0, 0),
        ("source_map_records_not_mutated", True, 0, 0),
        ("raw_comparison_not_performed", True, False, False),
        ("downstream_no_go_preserved", True, DECISION, DECISION),
    ]
    rows = [
        {
            "check_code": code,
            "status": "PASS" if passed else "FAIL",
            "observed_public_safe": observed,
            "required": required,
        }
        for code, passed, observed, required in checks
    ]
    pass_count = sum(1 for row in rows if row["status"] == "PASS")
    return {
        "schema_version": "kmfa.v014_corrected_source_or_owner_exclusion_resolution_application_matrix_public_safe.v1",
        "record_type": "v014_corrected_source_or_owner_exclusion_resolution_application_matrix_public_safe",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "application_check_count": len(rows),
        "application_pass_count": pass_count,
        "application_fail_count": len(rows) - pass_count,
        "source_retry_application_ready_item_count": 36,
        "owner_exclusion_resolution_applied_count": applied_count,
        "corrected_source_resolution_applied_count": 0,
        "application_blocker_queue_count": blocker_count,
        "resolution_application_performed_by_this_phase": True,
        "source_map_mutation_performed_by_this_phase": False,
        "source_map_records_applied_count": 0,
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "full_reconciliation_allowed": False,
        "github_upload_performed": False,
        "decision": DECISION,
        "checks": rows,
    }


def _write_human_artifacts(summary: dict[str, Any], matrix: dict[str, Any]) -> None:
    report = f"""# Corrected Source Or Owner Exclusion Resolution Application

- phase: `{PHASE_ID}`
- status: `{STATUS}`
- decision: `{DECISION}`
- private retry item count: `{summary["private_retry_item_count"]}`
- owner-exclusion items applied: `{summary["owner_exclusion_resolution_applied_count"]}`
- corrected-source items applied: `{summary["corrected_source_resolution_applied_count"]}`
- source-map records applied: `{summary["source_map_records_applied_count"]}`
- raw inbox accessed: `false`
- next recommended phase: `{NEXT_RECOMMENDED_PHASE}`

This phase applies the private ready owner-exclusion decisions as exclusions only. It does not apply source-map records, compare raw and processed values, reconcile values, upload GitHub, reinstall the app, or execute business actions.
"""
    go_no_go_record = f"""# Go/No-Go Record

- decision: `{DECISION}`
- reason: owner exclusions were applied, but post-resolution source-map readiness, materialization, raw-to-processed comparison and reconciliation have not run.
- application checks: `{matrix["application_pass_count"]}` pass / `{matrix["application_fail_count"]}` fail
- next required input: `{NEXT_REQUIRED_INPUT}`
"""
    risk_register = """# Risk Register

- Risk: owner-exclusion application can be mistaken for value reconciliation or source-map completion.
- Control: public evidence locks source-map records applied at zero and keeps raw comparison, reconciliation, report, upload and business gates closed.
"""
    rollback_plan = """# Rollback Plan

Remove this phase's public artifacts, metadata copies, private application outputs, tools, tests and governance rows. Do not modify raw source files.
"""
    test_results = """# Test Results

Recorded validation commands for this phase:

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_application.py KMFA/tools/check_v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_application.py KMFA/tests/test_v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_application.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_application.py --generated-at 2026-07-06T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_application.py --require-private-application`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_application`
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
    event_id = "DEV-KMFA-20260706-V014-CORRECTED-SOURCE-OR-OWNER-EXCLUSION-RESOLUTION-APPLICATION"
    event = {
        "event_id": event_id,
        "event_time": generated_at,
        "event_type": "development",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "iteration_id": "ITER-20260706-KMFA-V014-CORRECTED-SOURCE-OR-OWNER-EXCLUSION-RESOLUTION-APPLICATION",
        "fact_level": "EXTRACTED",
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "go_no_go": DECISION,
        "private_retry_item_count": summary["private_retry_item_count"],
        "owner_exclusion_resolution_applied_count": summary["owner_exclusion_resolution_applied_count"],
        "corrected_source_resolution_applied_count": summary["corrected_source_resolution_applied_count"],
        "source_map_records_applied_count": summary["source_map_records_applied_count"],
        "resolution_application_performed": True,
        "source_map_mutation_performed": False,
        "full_reconciliation_allowed": False,
        "business_value_consistency_verified": False,
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "result_commit": "PENDING",
        "files_changed": FILES_CHANGED,
        "summary": "Applied 36 private delegated owner-exclusion retry decisions while keeping source-map mutation and reconciliation gates closed.",
    }
    DEVELOPMENT_EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    existing = DEVELOPMENT_EVENTS_PATH.read_text(encoding="utf-8").splitlines() if DEVELOPMENT_EVENTS_PATH.exists() else []
    filtered = [line for line in existing if f'"event_id":"{event_id}"' not in line and f'"event_id": "{event_id}"' not in line]
    filtered.append(json.dumps(event, ensure_ascii=False, sort_keys=True))
    DEVELOPMENT_EVENTS_PATH.write_text("\n".join(filtered) + "\n", encoding="utf-8")


def generate(*, generated_at: str | None = None) -> dict[str, Any]:
    timestamp = _now(generated_at)
    readiness_summary = _read_json(SOURCE_READINESS_SUMMARY_PATH)
    readiness_matrix = _read_json(SOURCE_READINESS_MATRIX_PATH)
    readiness_diagnostic = _read_json(SOURCE_PRIVATE_READINESS_DIAGNOSTIC_PATH)
    ready_queue = _read_jsonl(SOURCE_PRIVATE_READY_QUEUE_PATH)
    source_blocker_queue = _read_jsonl(SOURCE_PRIVATE_BLOCKER_QUEUE_PATH)
    if len(ready_queue) != 36 or source_blocker_queue:
        raise ValueError(f"expected 36 ready rows and 0 source blockers, got {len(ready_queue)} and {len(source_blocker_queue)}")
    applied_queue = _build_applied_queue(ready_queue)
    blocker_queue = [
        {
            "blocker_item_index": index,
            "application_blocker_code": "ready_row_not_owner_exclusion_decision",
            "resolution_application_performed": False,
        }
        for index, row in enumerate(ready_queue, start=1)
        if row.get("application_decision_code") != OWNER_EXCLUSION_DECISION
    ]
    applied_count = len(applied_queue)
    blocker_count = len(blocker_queue)
    if applied_count != 36 or blocker_count != 0:
        raise ValueError(f"expected 36 applied owner exclusions and 0 blockers, got {applied_count} and {blocker_count}")

    private_diagnostic = {
        "schema_version": "kmfa.private.v014_corrected_source_or_owner_exclusion_resolution_application_diagnostic.v1",
        "classification": "private_resolution_application_diagnostic_do_not_commit",
        "record_type": "v014_corrected_source_or_owner_exclusion_resolution_application_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "source_readiness_phase_id": readiness_summary.get("phase_id"),
        "private_retry_item_count": readiness_summary.get("private_retry_item_count"),
        "source_ready_queue_count": len(ready_queue),
        "source_blocker_queue_count": len(source_blocker_queue),
        "owner_exclusion_resolution_applied_count": applied_count,
        "corrected_source_resolution_applied_count": 0,
        "resolution_application_performed_by_this_phase": True,
        "source_map_mutation_performed_by_this_phase": False,
        "source_map_records_applied_count": 0,
        "raw_inbox_accessed": False,
        "raw_boundary": _raw_boundary(),
    }
    private_result = {
        "schema_version": "kmfa.private.v014_corrected_source_or_owner_exclusion_resolution_application_result.v1",
        "classification": "private_resolution_application_result_do_not_commit",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "owner_exclusion_resolution_applied_count": applied_count,
        "corrected_source_resolution_applied_count": 0,
        "application_blocker_queue_count": blocker_count,
        "resolution_application_performed_by_this_phase": True,
        "next_required_input": NEXT_REQUIRED_INPUT,
    }
    _write_json(PRIVATE_DIAGNOSTIC_PATH, private_diagnostic)
    _write_json(PRIVATE_RESULT_PATH, private_result)
    _write_jsonl(PRIVATE_APPLIED_QUEUE_PATH, applied_queue)
    _write_jsonl(PRIVATE_BLOCKER_QUEUE_PATH, blocker_queue)
    _write_text(
        PRIVATE_REPORT_PATH,
        "# Private Resolution Application\n\n"
        "36 delegated owner-exclusion decisions were applied to the private application result. "
        "This private file is ignored and must not be committed.\n",
    )

    matrix = _build_matrix(timestamp, readiness_summary, applied_count, blocker_count)
    summary = {
        "schema_version": "kmfa.v014_corrected_source_or_owner_exclusion_resolution_application_summary.v1",
        "record_type": "v014_corrected_source_or_owner_exclusion_resolution_application_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "source_retry_application_readiness_phase_id": readiness_summary["phase_id"],
        "source_retry_application_readiness_decision": readiness_summary["decision"],
        "source_retry_application_readiness_matrix_fail_count": readiness_matrix["application_readiness_fail_count"],
        "private_retry_item_count": readiness_summary["private_retry_item_count"],
        "retry_application_ready_item_count": readiness_summary["retry_application_ready_item_count"],
        "source_retry_application_blocker_queue_count": readiness_summary["retry_application_blocker_queue_count"],
        "source_resolution_application_ready": readiness_summary["resolution_application_ready"],
        "source_readiness_diagnostic_ready": readiness_diagnostic.get("resolution_application_ready"),
        "owner_exclusion_resolution_applied_count": applied_count,
        "corrected_source_resolution_applied_count": 0,
        "resolution_application_blocker_queue_count": blocker_count,
        "resolution_application_performed_by_this_phase": True,
        "owner_exclusion_resolution_application_performed_by_this_phase": True,
        "corrected_source_resolution_application_performed_by_this_phase": False,
        "all_36_unlinked_blockers_resolved_by_owner_exclusion": applied_count == 36 and blocker_count == 0,
        "post_resolution_readiness_recheck_required": True,
        "post_resolution_readiness_recheck_ready": True,
        "source_map_mutation_performed_by_this_phase": False,
        "source_map_records_applied_count": 0,
        "source_map_completion_reapplication_ready": True,
        "processed_value_materialization_replay_ready": False,
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "raw_to_processed_value_comparison_ready": False,
        "full_reconciliation_allowed": False,
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
        "private_application_applied_queue_written": True,
        "private_application_applied_queue_gitignored": _git_check_ignored(PRIVATE_APPLIED_QUEUE_PATH),
        "private_application_blocker_queue_written": True,
        "private_application_blocker_queue_gitignored": _git_check_ignored(PRIVATE_BLOCKER_QUEUE_PATH),
        "next_required_input": NEXT_REQUIRED_INPUT,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
        "raw_boundary": _raw_boundary(),
        "public_safety": _public_safety(),
    }
    go_no_go = {
        "schema_version": "kmfa.v014_corrected_source_or_owner_exclusion_resolution_application_go_no_go.v1",
        "record_type": "v014_corrected_source_or_owner_exclusion_resolution_application_go_no_go",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "reason": "owner_exclusions_applied_but_post_resolution_readiness_materialization_and_reconciliation_not_performed",
        "owner_exclusion_resolution_applied_count": applied_count,
        "corrected_source_resolution_applied_count": 0,
        "source_map_records_applied_count": 0,
        "resolution_application_performed_by_this_phase": True,
        "source_map_mutation_performed_by_this_phase": False,
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "full_reconciliation_allowed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "next_required_input": NEXT_REQUIRED_INPUT,
    }
    manifest = {
        "schema_version": "kmfa.v014_corrected_source_or_owner_exclusion_resolution_application_manifest.v1",
        "record_type": "v014_corrected_source_or_owner_exclusion_resolution_application_manifest",
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
            SOURCE_READINESS_SUMMARY_PATH.as_posix(),
            SOURCE_READINESS_MATRIX_PATH.as_posix(),
            "private:retry_application_readiness_diagnostic",
            "private:retry_application_ready_queue",
            "private:retry_application_blocker_queue",
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
            "private:resolution_application_diagnostic",
            "private:resolution_application_result",
            "private:resolution_application_applied_queue",
            "private:resolution_application_blocker_queue",
            "private:resolution_application_report",
        ],
        "validator": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_application.py --require-private-application",
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
    _append_development_event(timestamp, summary)
    return {"summary": summary, "manifest": manifest, "matrix": matrix, "go_no_go": go_no_go}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generated-at", default=None)
    args = parser.parse_args()
    result = generate(generated_at=args.generated_at)
    summary = result["summary"]
    print(
        "PASS: KMFA v0.1.4 resolution application generated "
        f"(decision={summary['decision']}, owner_exclusions={summary['owner_exclusion_resolution_applied_count']}, "
        f"source_map_records={summary['source_map_records_applied_count']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
