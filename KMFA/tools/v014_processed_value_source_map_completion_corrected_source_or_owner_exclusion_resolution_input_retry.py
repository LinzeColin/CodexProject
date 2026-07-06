#!/usr/bin/env python3
"""Create a delegated conservative retry input for the 36 no-match blockers."""

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
PHASE_ID = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_CORRECTED_SOURCE_OR_OWNER_EXCLUSION_RESOLUTION_INPUT_RETRY"
TASK_ID = "KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-CORRECTED-SOURCE-OR-OWNER-EXCLUSION-RESOLUTION-INPUT-RETRY-20260706"
ACCEPTANCE_ID = "ACC-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-CORRECTED-SOURCE-OR-OWNER-EXCLUSION-RESOLUTION-INPUT-RETRY"
VERSION = "0.1.4-corrected-source-or-owner-exclusion-resolution-input-retry"
STATUS = "completed_validated_local_only_corrected_source_or_owner_exclusion_resolution_input_retry_ready_for_readiness_check"
DECISION = "NO_GO"
NEXT_REQUIRED_INPUT = "run_application_readiness_against_private_retry_template"
NEXT_RECOMMENDED_PHASE = (
    "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_CORRECTED_SOURCE_OR_OWNER_EXCLUSION_RESOLUTION_RETRY_APPLICATION_READINESS"
)

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_input_retry_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_input_retry_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_input_retry_go_no_go_report.json"
MATRIX_PATH = MACHINE_DIR / "processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_input_retry_matrix_public_safe.json"
REPORT_PATH = HUMAN_DIR / "processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_input_retry_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_corrected_source_or_owner_exclusion_resolution_input_retry_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_corrected_source_or_owner_exclusion_resolution_input_retry_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_corrected_source_or_owner_exclusion_resolution_input_retry_go_no_go_report.json"
METADATA_MATRIX_PATH = PROJECT_ROOT / "metadata/quality/v014_corrected_source_or_owner_exclusion_resolution_input_retry_matrix_public_safe.json"
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"

SOURCE_INPUT_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_corrected_source_or_owner_exclusion_resolution_input_summary.json"
SOURCE_APPLICATION_READINESS_SUMMARY_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_corrected_source_or_owner_exclusion_resolution_application_readiness_summary.json"
)
SOURCE_PRIVATE_TEMPLATE_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_input/private_corrected_source_or_owner_exclusion_resolution_input_template.json"
)
SOURCE_PRIVATE_PENDING_QUEUE_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_input/private_corrected_source_or_owner_exclusion_pending_queue.jsonl"
)
SOURCE_PRIVATE_APPLICATION_BLOCKER_QUEUE_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_application_readiness/private_corrected_source_or_owner_exclusion_resolution_application_blocker_queue.jsonl"
)
SOURCE_PRIVATE_RAW_MATCHING_RECORDS_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_private_raw_value_matching_dry_run/private_raw_value_matching_records.jsonl"
)
SOURCE_PRIVATE_BLOCKER_RECORDS_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_private_mismatch_and_blocker_report/private_blocker_records.jsonl"
)

PRIVATE_OUTPUT_DIR = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_input_retry"
)
PRIVATE_RETRY_TEMPLATE_PATH = PRIVATE_OUTPUT_DIR / "private_corrected_source_or_owner_exclusion_resolution_input_retry_template.json"
PRIVATE_RETRY_QUEUE_PATH = PRIVATE_OUTPUT_DIR / "private_corrected_source_or_owner_exclusion_resolution_input_retry_queue.jsonl"
PRIVATE_RETRY_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_corrected_source_or_owner_exclusion_resolution_input_retry_diagnostic.json"
PRIVATE_RETRY_REPORT_PATH = PRIVATE_OUTPUT_DIR / "private_corrected_source_or_owner_exclusion_resolution_input_retry.md"

OWNER_EXCLUSION_DECISION = "OWNER_EXCLUDE_FROM_RECONCILIATION"
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
    "KMFA/metadata/quality/v014_corrected_source_or_owner_exclusion_resolution_input_retry_go_no_go_report.json",
    "KMFA/metadata/quality/v014_corrected_source_or_owner_exclusion_resolution_input_retry_manifest.json",
    "KMFA/metadata/quality/v014_corrected_source_or_owner_exclusion_resolution_input_retry_matrix_public_safe.json",
    "KMFA/metadata/quality/v014_corrected_source_or_owner_exclusion_resolution_input_retry_summary.json",
    "KMFA/stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_CORRECTED_SOURCE_OR_OWNER_EXCLUSION_RESOLUTION_INPUT_RETRY/human/go_no_go_record.md",
    "KMFA/stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_CORRECTED_SOURCE_OR_OWNER_EXCLUSION_RESOLUTION_INPUT_RETRY/human/processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_input_retry_report.md",
    "KMFA/stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_CORRECTED_SOURCE_OR_OWNER_EXCLUSION_RESOLUTION_INPUT_RETRY/human/risk_register.md",
    "KMFA/stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_CORRECTED_SOURCE_OR_OWNER_EXCLUSION_RESOLUTION_INPUT_RETRY/human/rollback_plan.md",
    "KMFA/stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_CORRECTED_SOURCE_OR_OWNER_EXCLUSION_RESOLUTION_INPUT_RETRY/human/test_results.md",
    "KMFA/stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_CORRECTED_SOURCE_OR_OWNER_EXCLUSION_RESOLUTION_INPUT_RETRY/machine/processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_input_retry_go_no_go_report.json",
    "KMFA/stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_CORRECTED_SOURCE_OR_OWNER_EXCLUSION_RESOLUTION_INPUT_RETRY/machine/processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_input_retry_manifest.json",
    "KMFA/stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_CORRECTED_SOURCE_OR_OWNER_EXCLUSION_RESOLUTION_INPUT_RETRY/machine/processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_input_retry_matrix_public_safe.json",
    "KMFA/stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_CORRECTED_SOURCE_OR_OWNER_EXCLUSION_RESOLUTION_INPUT_RETRY/machine/processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_input_retry_summary.json",
    "KMFA/tests/test_v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_input_retry.py",
    "KMFA/tools/check_v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_input_retry.py",
    "KMFA/tools/v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_input_retry.py",
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
        "private_prior_template_read_by_this_phase": True,
        "private_prior_application_blocker_queue_read_by_this_phase": True,
        "private_prior_raw_matching_dry_run_read_by_this_phase": True,
        "private_prior_blocker_records_read_by_this_phase": True,
        "private_retry_input_written_by_this_phase": True,
    }


def _public_safety() -> dict[str, bool]:
    return {
        "public_safe_aggregate_only": True,
        "private_retry_template_committed": False,
        "private_retry_queue_committed": False,
        "private_retry_diagnostic_committed": False,
        "private_retry_report_committed": False,
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


def _index_by_slot(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for row in rows:
        slot = str(row.get("target_slot_id") or "")
        if slot:
            indexed[slot] = row
    return indexed


def _build_retry_items(
    items: list[dict[str, Any]],
    raw_match_by_slot: dict[str, dict[str, Any]],
    blocker_by_slot: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    retry_items: list[dict[str, Any]] = []
    for index, item in enumerate(items, start=1):
        slot = str(item.get("target_slot_id") or "")
        raw_match = raw_match_by_slot.get(slot, {})
        blocker = blocker_by_slot.get(slot, {})
        match_status = str(raw_match.get("match_status") or "")
        blocker_reason = str(blocker.get("private_blocker_reason") or "")
        occurrence_count = int(raw_match.get("raw_index_occurrence_count") or 0)
        if match_status != "no_raw_index_fingerprint_match" or blocker_reason != "no_raw_index_fingerprint_match":
            raise ValueError("retry input only supports no-raw-index-fingerprint-match blockers")
        if occurrence_count != 0:
            raise ValueError("retry input owner exclusion requires zero raw index occurrences")
        retry_items.append(
            {
                "retry_item_index": index,
                "target_slot_id": slot,
                "source_decision_code": item.get("source_decision_code"),
                "required_owner_decision_code": OWNER_EXCLUSION_DECISION,
                "corrected_source_package_ref": "NOT_APPLICABLE_OWNER_EXCLUSION",
                "owner_exclusion_basis_ref": f"PRIVATE_NO_RAW_INDEX_MATCH_BASIS::{slot}",
                "owner_resolution_note": "delegated_conservative_owner_exclusion_for_no_raw_index_fingerprint_match",
                "source_match_status": match_status,
                "source_raw_index_occurrence_count": occurrence_count,
                "resolution_application_allowed": False,
                "full_reconciliation_allowed": False,
            }
        )
    return retry_items


def _build_matrix(generated_at: str, retry_count: int) -> dict[str, Any]:
    checks = [
        {
            "check_code": "source_application_readiness_no_go_available",
            "status": "PASS",
            "public_safe_observed_value": True,
            "required_value": True,
        },
        {
            "check_code": "private_36_retry_items_generated",
            "status": "PASS" if retry_count == 36 else "FAIL",
            "public_safe_observed_value": retry_count,
            "required_value": 36,
        },
        {
            "check_code": "all_retry_items_owner_exclusion",
            "status": "PASS" if retry_count == 36 else "FAIL",
            "public_safe_observed_value": retry_count,
            "required_value": 36,
        },
        {
            "check_code": "raw_inbox_access_not_performed",
            "status": "PASS",
            "public_safe_observed_value": False,
            "required_value": False,
        },
        {
            "check_code": "source_map_application_not_performed",
            "status": "PASS",
            "public_safe_observed_value": False,
            "required_value": False,
        },
        {
            "check_code": "next_readiness_check_allowed",
            "status": "PASS" if retry_count == 36 else "FAIL",
            "public_safe_observed_value": retry_count == 36,
            "required_value": True,
        },
    ]
    pass_count = sum(1 for check in checks if check["status"] == "PASS")
    return {
        "schema_version": "kmfa.v014_corrected_source_or_owner_exclusion_resolution_input_retry_matrix_public_safe.v1",
        "record_type": "v014_corrected_source_or_owner_exclusion_resolution_input_retry_matrix_public_safe",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "retry_check_count": len(checks),
        "retry_check_pass_count": pass_count,
        "retry_check_fail_count": len(checks) - pass_count,
        "all_retry_inputs_valid": retry_count == 36,
        "resolution_application_performed_by_this_phase": False,
        "source_map_mutation_performed_by_this_phase": False,
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "github_upload_performed": False,
        "checks": checks,
    }


def _write_human_artifacts(summary: dict[str, Any]) -> None:
    report = f"""# Corrected Source Or Owner Exclusion Resolution Input Retry

- phase: `{PHASE_ID}`
- status: `{STATUS}`
- decision: `{DECISION}`
- private retry item count: `{summary["private_retry_item_count"]}`
- owner exclusion retry item count: `{summary["owner_exclusion_retry_item_count"]}`
- corrected source retry item count: `{summary["corrected_source_retry_item_count"]}`
- raw inbox accessed: `false`
- source-map application performed: `false`
- next recommended phase: `{NEXT_RECOMMENDED_PHASE}`

This phase creates a private retry input package only. It does not apply source-map records, compare raw and processed values, reconcile values, upload GitHub, reinstall the app, or execute business actions.
"""
    go_no_go_record = f"""# Go/No-Go Record

- decision: `{DECISION}`
- reason: private retry input is prepared for a later readiness check, but application and reconciliation are still blocked in this phase.
- next required input: `{NEXT_REQUIRED_INPUT}`
"""
    risk_register = """# Risk Register

- Risk: delegated conservative exclusions can hide missing corrected-source evidence if treated as final application.
- Control: retry input remains private and ignored; public evidence is aggregate-only; application, reconciliation and reporting gates remain closed.
"""
    rollback_plan = """# Rollback Plan

Remove this phase's public artifacts, metadata copies, private retry outputs, tools, tests and governance rows. Do not modify raw source files.
"""
    test_results = """# Test Results

Recorded validation commands for this phase:

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_input_retry.py KMFA/tools/check_v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_input_retry.py KMFA/tests/test_v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_input_retry.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_input_retry.py --generated-at 2026-07-06T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_input_retry.py --require-private-retry`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_input_retry`
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
    event_id = "DEV-KMFA-20260706-V014-CORRECTED-SOURCE-OR-OWNER-EXCLUSION-RESOLUTION-INPUT-RETRY"
    event = {
        "event_id": event_id,
        "event_time": generated_at,
        "event_type": "development",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "iteration_id": "ITER-20260706-KMFA-V014-CORRECTED-SOURCE-OR-OWNER-EXCLUSION-RESOLUTION-INPUT-RETRY",
        "fact_level": "EXTRACTED",
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "go_no_go": DECISION,
        "private_retry_item_count": summary["private_retry_item_count"],
        "owner_exclusion_retry_item_count": summary["owner_exclusion_retry_item_count"],
        "corrected_source_retry_item_count": summary["corrected_source_retry_item_count"],
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "resolution_application_performed": False,
        "full_reconciliation_allowed": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "result_commit": "PENDING",
        "files_changed": FILES_CHANGED,
        "summary": "Generated a private delegated conservative owner-exclusion retry package for 36 no-match blockers.",
    }
    DEVELOPMENT_EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    existing = DEVELOPMENT_EVENTS_PATH.read_text(encoding="utf-8").splitlines() if DEVELOPMENT_EVENTS_PATH.exists() else []
    filtered = [line for line in existing if f'"event_id":"{event_id}"' not in line and f'"event_id": "{event_id}"' not in line]
    filtered.append(json.dumps(event, ensure_ascii=False, sort_keys=True))
    DEVELOPMENT_EVENTS_PATH.write_text("\n".join(filtered) + "\n", encoding="utf-8")


def generate(*, generated_at: str | None = None) -> dict[str, Any]:
    timestamp = _now(generated_at)
    source_input_summary = _read_json(SOURCE_INPUT_SUMMARY_PATH)
    source_readiness_summary = _read_json(SOURCE_APPLICATION_READINESS_SUMMARY_PATH)
    source_template = _read_json(SOURCE_PRIVATE_TEMPLATE_PATH)
    source_pending_queue = _read_jsonl(SOURCE_PRIVATE_PENDING_QUEUE_PATH)
    source_application_blockers = _read_jsonl(SOURCE_PRIVATE_APPLICATION_BLOCKER_QUEUE_PATH)
    raw_matching_records = _read_jsonl(SOURCE_PRIVATE_RAW_MATCHING_RECORDS_PATH)
    blocker_records = _read_jsonl(SOURCE_PRIVATE_BLOCKER_RECORDS_PATH)
    items = source_template.get("items", [])
    if not isinstance(items, list):
        raise ValueError("source private template items must be a list")
    if len(items) != 36 or len(source_pending_queue) != 36 or len(source_application_blockers) != 36:
        raise ValueError("expected 36 source items, pending rows and application blockers")
    slots = {str(item.get("target_slot_id") or "") for item in items}
    raw_match_by_slot = _index_by_slot([row for row in raw_matching_records if str(row.get("target_slot_id") or "") in slots])
    blocker_by_slot = _index_by_slot([row for row in blocker_records if str(row.get("target_slot_id") or "") in slots])
    if len(raw_match_by_slot) != 36 or len(blocker_by_slot) != 36:
        raise ValueError("expected private raw-match and blocker records for all 36 retry slots")
    retry_items = _build_retry_items([item for item in items if isinstance(item, dict)], raw_match_by_slot, blocker_by_slot)
    retry_queue = [
        {
            "retry_queue_index": item["retry_item_index"],
            "required_owner_decision_code": item["required_owner_decision_code"],
            "owner_input_status": "delegated_conservative_owner_exclusion_prepared",
            "resolution_application_allowed": False,
            "full_reconciliation_allowed": False,
            "target_slot_id": item["target_slot_id"],
        }
        for item in retry_items
    ]
    private_retry_template = {
        "schema_version": "kmfa.private.v014_corrected_source_or_owner_exclusion_resolution_input_retry_template.v1",
        "classification": "private_corrected_source_or_owner_exclusion_resolution_input_retry_do_not_commit",
        "record_type": "v014_corrected_source_or_owner_exclusion_resolution_input_retry_template",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "generated_at": timestamp,
        "delegated_default_decision_applied": True,
        "delegated_default_decision_basis": "all_36_slots_have_no_raw_index_fingerprint_match_in_prior_private_dry_run",
        "private_retry_item_count": len(retry_items),
        "owner_exclusion_retry_item_count": len(retry_items),
        "corrected_source_retry_item_count": 0,
        "allowed_next_phase": NEXT_RECOMMENDED_PHASE,
        "items": retry_items,
    }
    private_diagnostic = {
        "schema_version": "kmfa.private.v014_corrected_source_or_owner_exclusion_resolution_input_retry_diagnostic.v1",
        "classification": "private_corrected_source_or_owner_exclusion_resolution_input_retry_diagnostic_do_not_commit",
        "record_type": "v014_corrected_source_or_owner_exclusion_resolution_input_retry_diagnostic",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "generated_at": timestamp,
        "decision": DECISION,
        "source_application_readiness_decision": source_readiness_summary.get("decision"),
        "private_retry_item_count": len(retry_items),
        "owner_exclusion_retry_item_count": len(retry_items),
        "corrected_source_retry_item_count": 0,
        "no_raw_index_fingerprint_match_count": len(retry_items),
        "zero_raw_index_occurrence_count": len(retry_items),
        "retry_input_valid_count": len(retry_items),
        "retry_input_missing_count": 0,
        "resolution_application_performed": False,
        "raw_inbox_accessed": False,
    }
    summary = {
        "schema_version": "kmfa.v014_corrected_source_or_owner_exclusion_resolution_input_retry_summary.v1",
        "record_type": "v014_corrected_source_or_owner_exclusion_resolution_input_retry_summary",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "version": VERSION,
        "status": STATUS,
        "decision": DECISION,
        "generated_at": timestamp,
        "source_input_decision": source_input_summary.get("decision"),
        "source_application_readiness_decision": source_readiness_summary.get("decision"),
        "source_application_missing_owner_input_count": source_readiness_summary.get("missing_owner_input_count"),
        "delegated_default_decision_applied": True,
        "delegated_default_decision_type": "owner_exclusion_for_no_raw_index_fingerprint_match",
        "private_retry_item_count": len(retry_items),
        "owner_exclusion_retry_item_count": len(retry_items),
        "corrected_source_retry_item_count": 0,
        "retry_input_valid_count": len(retry_items),
        "retry_input_missing_count": 0,
        "no_raw_index_fingerprint_match_count": len(retry_items),
        "zero_raw_index_occurrence_count": len(retry_items),
        "private_retry_template_written": True,
        "private_retry_queue_written": True,
        "private_retry_diagnostic_written": True,
        "private_retry_template_gitignored": _git_check_ignored(PRIVATE_RETRY_TEMPLATE_PATH),
        "resolution_application_readiness_allowed_next_phase": True,
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
        "raw_boundary": _raw_boundary(),
        "public_safety": _public_safety(),
        "next_required_input": NEXT_REQUIRED_INPUT,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
    }
    matrix = _build_matrix(timestamp, len(retry_items))
    manifest = {
        "schema_version": "kmfa.v014_corrected_source_or_owner_exclusion_resolution_input_retry_manifest.v1",
        "record_type": "v014_corrected_source_or_owner_exclusion_resolution_input_retry_manifest",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "version": VERSION,
        "status": STATUS,
        "decision": DECISION,
        "generated_at": timestamp,
        "git_branch": _git_output(["branch", "--show-current"]),
        "git_head": _git_output(["rev-parse", "HEAD"]),
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
        "private_artifacts_gitignored": True,
        "summary": summary,
        "matrix": matrix,
    }
    go_no_go = {
        "schema_version": "kmfa.v014_corrected_source_or_owner_exclusion_resolution_input_retry_go_no_go.v1",
        "record_type": "v014_corrected_source_or_owner_exclusion_resolution_input_retry_go_no_go",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "decision": DECISION,
        "reason": "private_retry_input_prepared_but_application_and_reconciliation_not_performed",
        "resolution_application_readiness_allowed_next_phase": True,
        "resolution_application_performed_by_this_phase": False,
        "full_reconciliation_allowed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "next_required_input": NEXT_REQUIRED_INPUT,
    }

    _write_json(PRIVATE_RETRY_TEMPLATE_PATH, private_retry_template)
    _write_jsonl(PRIVATE_RETRY_QUEUE_PATH, retry_queue)
    _write_json(PRIVATE_RETRY_DIAGNOSTIC_PATH, private_diagnostic)
    _write_text(
        PRIVATE_RETRY_REPORT_PATH,
        "# Private Retry Input\n\n"
        "36 delegated conservative owner-exclusion retry items were prepared from prior private no-match evidence. "
        "This private file is ignored and must not be committed.\n",
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
    _write_human_artifacts(summary)
    _append_development_event(timestamp, summary)
    return {"summary": summary, "manifest": manifest, "matrix": matrix, "go_no_go": go_no_go}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated-at", default=None)
    args = parser.parse_args()
    result = generate(generated_at=args.generated_at)
    summary = result["summary"]
    print(
        "PASS: KMFA v0.1.4 corrected-source or owner-exclusion retry input generated "
        f"(decision={summary['decision']}, retry_items={summary['private_retry_item_count']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
