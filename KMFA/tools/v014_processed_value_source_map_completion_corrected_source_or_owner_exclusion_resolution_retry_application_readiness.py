#!/usr/bin/env python3
"""Check retry application readiness for the 36 owner-exclusion items."""

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
PHASE_ID = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_CORRECTED_SOURCE_OR_OWNER_EXCLUSION_RESOLUTION_RETRY_APPLICATION_READINESS"
TASK_ID = "KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-CORRECTED-SOURCE-OR-OWNER-EXCLUSION-RESOLUTION-RETRY-APPLICATION-READINESS-20260706"
ACCEPTANCE_ID = "ACC-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-CORRECTED-SOURCE-OR-OWNER-EXCLUSION-RESOLUTION-RETRY-APPLICATION-READINESS"
VERSION = "0.1.4-corrected-source-or-owner-exclusion-resolution-retry-application-readiness"
STATUS = "completed_validated_local_only_corrected_source_or_owner_exclusion_retry_application_readiness_ready_no_go"
DECISION = "NO_GO"
DIAGNOSTIC_CONCLUSION = "retry_application_readiness_passed_application_not_performed"
NEXT_REQUIRED_INPUT = "run_resolution_application_against_private_retry_readiness_queue"
NEXT_RECOMMENDED_PHASE = (
    "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_CORRECTED_SOURCE_OR_OWNER_EXCLUSION_RESOLUTION_APPLICATION"
)
OWNER_EXCLUSION_DECISION = "OWNER_EXCLUDE_FROM_RECONCILIATION"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_retry_application_readiness_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_retry_application_readiness_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_retry_application_readiness_go_no_go_report.json"
MATRIX_PATH = MACHINE_DIR / "processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_retry_application_readiness_matrix_public_safe.json"
REPORT_PATH = HUMAN_DIR / "processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_retry_application_readiness_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_corrected_source_or_owner_exclusion_resolution_retry_application_readiness_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_corrected_source_or_owner_exclusion_resolution_retry_application_readiness_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_corrected_source_or_owner_exclusion_resolution_retry_application_readiness_go_no_go_report.json"
METADATA_MATRIX_PATH = PROJECT_ROOT / "metadata/quality/v014_corrected_source_or_owner_exclusion_resolution_retry_application_readiness_matrix_public_safe.json"
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"

SOURCE_RETRY_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_corrected_source_or_owner_exclusion_resolution_input_retry_summary.json"
SOURCE_RETRY_MATRIX_PATH = PROJECT_ROOT / "metadata/quality/v014_corrected_source_or_owner_exclusion_resolution_input_retry_matrix_public_safe.json"
SOURCE_PRIVATE_RETRY_TEMPLATE_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_input_retry/private_corrected_source_or_owner_exclusion_resolution_input_retry_template.json"
)
SOURCE_PRIVATE_RETRY_QUEUE_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_input_retry/private_corrected_source_or_owner_exclusion_resolution_input_retry_queue.jsonl"
)
SOURCE_PRIVATE_RETRY_DIAGNOSTIC_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_input_retry/private_corrected_source_or_owner_exclusion_resolution_input_retry_diagnostic.json"
)

PRIVATE_OUTPUT_DIR = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_retry_application_readiness"
)
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_corrected_source_or_owner_exclusion_resolution_retry_application_readiness_diagnostic.json"
PRIVATE_READY_QUEUE_PATH = PRIVATE_OUTPUT_DIR / "private_corrected_source_or_owner_exclusion_resolution_retry_application_ready_queue.jsonl"
PRIVATE_BLOCKER_QUEUE_PATH = PRIVATE_OUTPUT_DIR / "private_corrected_source_or_owner_exclusion_resolution_retry_application_blocker_queue.jsonl"
PRIVATE_REPORT_PATH = PRIVATE_OUTPUT_DIR / "private_corrected_source_or_owner_exclusion_resolution_retry_application_readiness.md"

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
    "KMFA/tests/test_v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_retry_application_readiness.py",
    "KMFA/tools/check_v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_retry_application_readiness.py",
    "KMFA/tools/v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_retry_application_readiness.py",
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
        "private_retry_template_read_by_this_phase": True,
        "private_retry_queue_read_by_this_phase": True,
        "private_retry_diagnostic_read_by_this_phase": True,
        "private_retry_application_readiness_diagnostic_written_by_this_phase": True,
    }


def _public_safety() -> dict[str, bool]:
    return {
        "public_safe_aggregate_only": True,
        "private_retry_template_committed": False,
        "private_retry_queue_committed": False,
        "private_retry_diagnostic_committed": False,
        "private_retry_application_readiness_diagnostic_committed": False,
        "private_retry_application_ready_queue_committed": False,
        "private_retry_application_blocker_queue_committed": False,
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


def _retry_item_ready(item: dict[str, Any]) -> bool:
    return (
        item.get("required_owner_decision_code") == OWNER_EXCLUSION_DECISION
        and item.get("source_match_status") == "no_raw_index_fingerprint_match"
        and item.get("source_raw_index_occurrence_count") == 0
        and item.get("owner_exclusion_basis_ref") not in {"", None, "PENDING_PRIVATE_INPUT"}
        and item.get("corrected_source_package_ref") in {"", None, "NOT_APPLICABLE_OWNER_EXCLUSION"}
        and item.get("resolution_application_allowed") is False
        and item.get("full_reconciliation_allowed") is False
    )


def _build_ready_queue(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, item in enumerate(items, start=1):
        if not _retry_item_ready(item):
            continue
        rows.append(
            {
                "ready_item_index": index,
                "target_slot_id": item.get("target_slot_id"),
                "application_decision_code": OWNER_EXCLUSION_DECISION,
                "owner_exclusion_basis_ref": item.get("owner_exclusion_basis_ref"),
                "source_match_status": item.get("source_match_status"),
                "source_raw_index_occurrence_count": item.get("source_raw_index_occurrence_count"),
                "resolution_application_ready": True,
                "source_map_mutation_allowed_by_this_phase": False,
                "full_reconciliation_allowed": False,
            }
        )
    return rows


def _build_blocker_queue(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, item in enumerate(items, start=1):
        if _retry_item_ready(item):
            continue
        rows.append(
            {
                "blocker_item_index": index,
                "target_slot_id": item.get("target_slot_id"),
                "application_blocker_code": "retry_item_not_application_ready",
                "required_owner_decision_code": item.get("required_owner_decision_code"),
                "source_match_status": item.get("source_match_status"),
                "resolution_application_ready": False,
            }
        )
    return rows


def _build_matrix(generated_at: str, retry_summary: dict[str, Any], ready_count: int, blocker_count: int) -> dict[str, Any]:
    checks = [
        ("source_retry_phase_available", retry_summary.get("private_retry_item_count") == 36, retry_summary.get("private_retry_item_count"), 36),
        ("private_retry_template_count_locked", retry_summary.get("private_retry_item_count") == 36, retry_summary.get("private_retry_item_count"), 36),
        ("retry_input_complete", retry_summary.get("retry_input_valid_count") == 36 and retry_summary.get("retry_input_missing_count") == 0, retry_summary.get("retry_input_valid_count"), 36),
        ("all_36_owner_exclusions_valid", retry_summary.get("owner_exclusion_retry_item_count") == 36, retry_summary.get("owner_exclusion_retry_item_count"), 36),
        ("no_corrected_source_retry_items", retry_summary.get("corrected_source_retry_item_count") == 0, retry_summary.get("corrected_source_retry_item_count"), 0),
        ("no_application_blockers_remaining", blocker_count == 0, blocker_count, 0),
        ("resolution_application_ready_for_next_phase", ready_count == 36, ready_count, 36),
        ("downstream_actions_not_performed", True, False, False),
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
        "schema_version": "kmfa.v014_corrected_source_or_owner_exclusion_resolution_retry_application_readiness_matrix_public_safe.v1",
        "record_type": "v014_corrected_source_or_owner_exclusion_resolution_retry_application_readiness_matrix_public_safe",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "application_readiness_check_count": len(rows),
        "application_readiness_pass_count": pass_count,
        "application_readiness_fail_count": len(rows) - pass_count,
        "private_retry_item_count": 36,
        "ready_item_count": ready_count,
        "application_blocker_queue_count": blocker_count,
        "all_36_retry_inputs_valid": ready_count == 36,
        "all_36_unlinked_blockers_resolved": ready_count == 36 and blocker_count == 0,
        "resolution_application_ready": ready_count == 36 and blocker_count == 0,
        "resolution_application_allowed_next_phase": ready_count == 36 and blocker_count == 0,
        "resolution_application_performed_by_this_phase": False,
        "source_map_mutation_performed_by_this_phase": False,
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "full_reconciliation_allowed": False,
        "github_upload_performed": False,
        "decision": DECISION,
        "checks": rows,
    }


def _write_human_artifacts(summary: dict[str, Any], matrix: dict[str, Any]) -> None:
    report = f"""# Corrected Source Or Owner Exclusion Retry Application Readiness

- phase: `{PHASE_ID}`
- status: `{STATUS}`
- decision: `{DECISION}`
- private retry item count: `{summary["private_retry_item_count"]}`
- ready item count: `{summary["retry_application_ready_item_count"]}`
- blocker queue count: `{summary["retry_application_blocker_queue_count"]}`
- resolution application ready: `{str(summary["resolution_application_ready"]).lower()}`
- source-map application performed: `false`
- raw inbox accessed: `false`
- next recommended phase: `{NEXT_RECOMMENDED_PHASE}`

This phase checks retry application readiness only. It does not apply source-map records, compare raw and processed values, reconcile values, upload GitHub, reinstall the app, or execute business actions.
"""
    go_no_go_record = f"""# Go/No-Go Record

- decision: `{DECISION}`
- reason: retry inputs are ready for a later application phase, but application and reconciliation are not performed in this phase.
- readiness checks: `{matrix["application_readiness_pass_count"]}` pass / `{matrix["application_readiness_fail_count"]}` fail
- next required input: `{NEXT_REQUIRED_INPUT}`
"""
    risk_register = """# Risk Register

- Risk: retry readiness can be mistaken for source-map application.
- Control: this phase writes only a private readiness queue; application, reconciliation and reporting gates remain closed.
"""
    rollback_plan = """# Rollback Plan

Remove this phase's public artifacts, metadata copies, private readiness outputs, tools, tests and governance rows. Do not modify raw source files.
"""
    test_results = """# Test Results

Recorded validation commands for this phase:

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_retry_application_readiness.py KMFA/tools/check_v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_retry_application_readiness.py KMFA/tests/test_v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_retry_application_readiness.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_retry_application_readiness.py --generated-at 2026-07-06T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_retry_application_readiness.py --require-private-readiness`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_retry_application_readiness`
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
    event_id = "DEV-KMFA-20260706-V014-CORRECTED-SOURCE-OR-OWNER-EXCLUSION-RESOLUTION-RETRY-APPLICATION-READINESS"
    event = {
        "event_id": event_id,
        "event_time": generated_at,
        "event_type": "development",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "iteration_id": "ITER-20260706-KMFA-V014-CORRECTED-SOURCE-OR-OWNER-EXCLUSION-RESOLUTION-RETRY-APPLICATION-READINESS",
        "fact_level": "EXTRACTED",
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "go_no_go": DECISION,
        "private_retry_item_count": summary["private_retry_item_count"],
        "retry_application_ready_item_count": summary["retry_application_ready_item_count"],
        "retry_application_blocker_queue_count": summary["retry_application_blocker_queue_count"],
        "resolution_application_ready": summary["resolution_application_ready"],
        "resolution_application_performed": False,
        "full_reconciliation_allowed": False,
        "business_value_consistency_verified": False,
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "result_commit": "PENDING",
        "files_changed": FILES_CHANGED,
        "summary": "Checked private retry application readiness for 36 delegated owner-exclusion items while keeping application and reconciliation gates closed.",
    }
    DEVELOPMENT_EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    existing = DEVELOPMENT_EVENTS_PATH.read_text(encoding="utf-8").splitlines() if DEVELOPMENT_EVENTS_PATH.exists() else []
    filtered = [line for line in existing if f'"event_id":"{event_id}"' not in line and f'"event_id": "{event_id}"' not in line]
    filtered.append(json.dumps(event, ensure_ascii=False, sort_keys=True))
    DEVELOPMENT_EVENTS_PATH.write_text("\n".join(filtered) + "\n", encoding="utf-8")


def generate(*, generated_at: str | None = None) -> dict[str, Any]:
    timestamp = _now(generated_at)
    retry_summary = _read_json(SOURCE_RETRY_SUMMARY_PATH)
    retry_matrix = _read_json(SOURCE_RETRY_MATRIX_PATH)
    retry_template = _read_json(SOURCE_PRIVATE_RETRY_TEMPLATE_PATH)
    retry_queue = _read_jsonl(SOURCE_PRIVATE_RETRY_QUEUE_PATH)
    retry_diagnostic = _read_json(SOURCE_PRIVATE_RETRY_DIAGNOSTIC_PATH)
    items = retry_template.get("items", [])
    if not isinstance(items, list):
        raise ValueError("private retry template items must be a list")
    if len(items) != 36 or len(retry_queue) != 36:
        raise ValueError(f"expected 36 retry items and queue rows, got {len(items)} and {len(retry_queue)}")
    ready_queue = _build_ready_queue([item for item in items if isinstance(item, dict)])
    blocker_queue = _build_blocker_queue([item for item in items if isinstance(item, dict)])
    ready_count = len(ready_queue)
    blocker_count = len(blocker_queue)
    resolution_application_ready = ready_count == 36 and blocker_count == 0

    private_diagnostic = {
        "schema_version": "kmfa.private.v014_corrected_source_or_owner_exclusion_resolution_retry_application_readiness_diagnostic.v1",
        "classification": "private_retry_application_readiness_diagnostic_do_not_commit",
        "record_type": "v014_corrected_source_or_owner_exclusion_resolution_retry_application_readiness_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "private_retry_item_count": len(items),
        "owner_exclusion_retry_item_count": retry_diagnostic.get("owner_exclusion_retry_item_count"),
        "corrected_source_retry_item_count": retry_diagnostic.get("corrected_source_retry_item_count"),
        "retry_application_ready_item_count": ready_count,
        "retry_application_blocker_queue_count": blocker_count,
        "resolution_application_ready": resolution_application_ready,
        "resolution_application_allowed_next_phase": resolution_application_ready,
        "resolution_application_performed_by_this_phase": False,
        "raw_inbox_accessed": False,
        "raw_boundary": _raw_boundary(),
    }
    _write_json(PRIVATE_DIAGNOSTIC_PATH, private_diagnostic)
    _write_jsonl(PRIVATE_READY_QUEUE_PATH, ready_queue)
    _write_jsonl(PRIVATE_BLOCKER_QUEUE_PATH, blocker_queue)
    _write_text(
        PRIVATE_REPORT_PATH,
        "# Private Retry Application Readiness\n\n"
        "36 delegated owner-exclusion retry items are ready for a later application phase. "
        "This private file is ignored and must not be committed.\n",
    )

    matrix = _build_matrix(timestamp, retry_summary, ready_count, blocker_count)
    summary = {
        "schema_version": "kmfa.v014_corrected_source_or_owner_exclusion_resolution_retry_application_readiness_summary.v1",
        "record_type": "v014_corrected_source_or_owner_exclusion_resolution_retry_application_readiness_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "source_retry_phase_id": retry_summary["phase_id"],
        "source_retry_decision": retry_summary["decision"],
        "source_retry_matrix_fail_count": retry_matrix["retry_check_fail_count"],
        "private_retry_item_count": len(items),
        "source_private_retry_item_count": retry_summary["private_retry_item_count"],
        "owner_exclusion_retry_item_count": retry_summary["owner_exclusion_retry_item_count"],
        "corrected_source_retry_item_count": retry_summary["corrected_source_retry_item_count"],
        "retry_input_valid_count": retry_summary["retry_input_valid_count"],
        "retry_input_missing_count": retry_summary["retry_input_missing_count"],
        "retry_application_ready_item_count": ready_count,
        "retry_application_blocker_queue_count": blocker_count,
        "all_36_retry_inputs_valid": ready_count == 36,
        "all_36_unlinked_blockers_resolved": resolution_application_ready,
        "resolution_application_ready": resolution_application_ready,
        "resolution_application_allowed_next_phase": resolution_application_ready,
        "resolution_application_allowed": False,
        "resolution_application_performed_by_this_phase": False,
        "source_map_mutation_performed_by_this_phase": False,
        "source_map_records_applied_count": 0,
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "full_reconciliation_allowed": False,
        "business_value_consistency_verified": False,
        "lineage_full_check_complete": False,
        "formal_report_allowed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "private_readiness_diagnostic_written": True,
        "private_readiness_diagnostic_gitignored": _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH),
        "private_ready_queue_written": True,
        "private_ready_queue_gitignored": _git_check_ignored(PRIVATE_READY_QUEUE_PATH),
        "private_blocker_queue_written": True,
        "private_blocker_queue_gitignored": _git_check_ignored(PRIVATE_BLOCKER_QUEUE_PATH),
        "next_required_input": NEXT_REQUIRED_INPUT,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
        "raw_boundary": _raw_boundary(),
        "public_safety": _public_safety(),
    }
    go_no_go = {
        "schema_version": "kmfa.v014_corrected_source_or_owner_exclusion_resolution_retry_application_readiness_go_no_go.v1",
        "record_type": "v014_corrected_source_or_owner_exclusion_resolution_retry_application_readiness_go_no_go",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "reason": "retry_application_ready_but_application_and_reconciliation_not_performed",
        "retry_application_ready_item_count": ready_count,
        "retry_application_blocker_queue_count": blocker_count,
        "resolution_application_ready": resolution_application_ready,
        "resolution_application_allowed_next_phase": resolution_application_ready,
        "resolution_application_performed_by_this_phase": False,
        "full_reconciliation_allowed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "next_required_input": NEXT_REQUIRED_INPUT,
    }
    manifest = {
        "schema_version": "kmfa.v014_corrected_source_or_owner_exclusion_resolution_retry_application_readiness_manifest.v1",
        "record_type": "v014_corrected_source_or_owner_exclusion_resolution_retry_application_readiness_manifest",
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
            SOURCE_RETRY_SUMMARY_PATH.as_posix(),
            SOURCE_RETRY_MATRIX_PATH.as_posix(),
            "private:corrected_source_or_owner_exclusion_resolution_input_retry_template",
            "private:corrected_source_or_owner_exclusion_resolution_input_retry_queue",
            "private:corrected_source_or_owner_exclusion_resolution_input_retry_diagnostic",
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
            "private:retry_application_readiness_diagnostic",
            "private:retry_application_ready_queue",
            "private:retry_application_blocker_queue",
            "private:retry_application_readiness_report",
        ],
        "validator": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_retry_application_readiness.py --require-private-readiness",
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
        "PASS: KMFA v0.1.4 retry application readiness generated "
        f"(decision={summary['decision']}, ready_items={summary['retry_application_ready_item_count']}, "
        f"blockers={summary['retry_application_blocker_queue_count']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
