#!/usr/bin/env python3
"""Prepare private corrected-source or owner-exclusion input for KMFA v0.1.4.

This phase narrows the prior blocker queue to the 36 unlinked application
blockers that remain after the delegated 22-group owner response intake. It
writes a private input template and public-safe aggregate evidence only. It
does not read the raw inbox, apply source-map records, reconcile values, or
clear any business gate.
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
PHASE_ID = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_CORRECTED_SOURCE_OR_OWNER_EXCLUSION_RESOLUTION_INPUT"
TASK_ID = "KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-CORRECTED-SOURCE-OR-OWNER-EXCLUSION-RESOLUTION-INPUT-20260706"
ACCEPTANCE_ID = "ACC-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-CORRECTED-SOURCE-OR-OWNER-EXCLUSION-RESOLUTION-INPUT"
VERSION = "0.1.4-corrected-source-or-owner-exclusion-resolution-input"
STATUS = "completed_validated_local_only_corrected_source_or_owner_exclusion_resolution_input_no_go"
DECISION = "NO_GO"
DIAGNOSTIC_CONCLUSION = "private_36_unlinked_blocker_resolution_input_template_prepared_no_owner_resolution_supplied"
NEXT_REQUIRED_INPUT = "owner_or_authorized_delegate_supplies_36_corrected_source_or_exclusion_resolution_items"
NEXT_RECOMMENDED_PHASE = (
    "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_CORRECTED_SOURCE_OR_OWNER_EXCLUSION_RESOLUTION_APPLICATION_READINESS"
)

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_input_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_input_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_input_go_no_go_report.json"
MATRIX_PATH = MACHINE_DIR / "processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_input_matrix_public_safe.json"
REPORT_PATH = HUMAN_DIR / "processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_input_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_corrected_source_or_owner_exclusion_resolution_input_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_corrected_source_or_owner_exclusion_resolution_input_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_corrected_source_or_owner_exclusion_resolution_input_go_no_go_report.json"
METADATA_MATRIX_PATH = PROJECT_ROOT / "metadata/quality/v014_corrected_source_or_owner_exclusion_resolution_input_matrix_public_safe.json"
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"

SOURCE_OWNER_RESPONSE_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_owner_22_group_decision_response_intake_summary.json"
SOURCE_OWNER_RESPONSE_MATRIX_PATH = PROJECT_ROOT / "metadata/quality/v014_owner_22_group_decision_response_intake_matrix_public_safe.json"
SOURCE_PRIVATE_FOLLOWUP_QUEUE_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_owner_22_group_decision_response_intake/private_owner_22_group_decision_followup_queue.json"
)
SOURCE_PRIVATE_DECISION_QUEUE_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_private_blocker_resolution_decision_intake/private_blocker_resolution_decision_queue.jsonl"
)

PRIVATE_OUTPUT_DIR = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_input"
)
PRIVATE_TEMPLATE_PATH = PRIVATE_OUTPUT_DIR / "private_corrected_source_or_owner_exclusion_resolution_input_template.json"
PRIVATE_PENDING_QUEUE_PATH = PRIVATE_OUTPUT_DIR / "private_corrected_source_or_owner_exclusion_pending_queue.jsonl"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_corrected_source_or_owner_exclusion_resolution_input_diagnostic.json"
PRIVATE_REPORT_PATH = PRIVATE_OUTPUT_DIR / "private_corrected_source_or_owner_exclusion_resolution_input.md"

CORRECTED_OR_EXCLUSION_CODE = "keep_blocked_pending_corrected_source_or_owner_exclusion"
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
    "KMFA/metadata/quality/v014_corrected_source_or_owner_exclusion_resolution_input_go_no_go_report.json",
    "KMFA/metadata/quality/v014_corrected_source_or_owner_exclusion_resolution_input_manifest.json",
    "KMFA/metadata/quality/v014_corrected_source_or_owner_exclusion_resolution_input_matrix_public_safe.json",
    "KMFA/metadata/quality/v014_corrected_source_or_owner_exclusion_resolution_input_summary.json",
    "KMFA/stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_CORRECTED_SOURCE_OR_OWNER_EXCLUSION_RESOLUTION_INPUT/human/go_no_go_record.md",
    "KMFA/stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_CORRECTED_SOURCE_OR_OWNER_EXCLUSION_RESOLUTION_INPUT/human/processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_input_report.md",
    "KMFA/stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_CORRECTED_SOURCE_OR_OWNER_EXCLUSION_RESOLUTION_INPUT/human/risk_register.md",
    "KMFA/stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_CORRECTED_SOURCE_OR_OWNER_EXCLUSION_RESOLUTION_INPUT/human/rollback_plan.md",
    "KMFA/stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_CORRECTED_SOURCE_OR_OWNER_EXCLUSION_RESOLUTION_INPUT/human/test_results.md",
    "KMFA/stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_CORRECTED_SOURCE_OR_OWNER_EXCLUSION_RESOLUTION_INPUT/machine/processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_input_go_no_go_report.json",
    "KMFA/stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_CORRECTED_SOURCE_OR_OWNER_EXCLUSION_RESOLUTION_INPUT/machine/processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_input_manifest.json",
    "KMFA/stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_CORRECTED_SOURCE_OR_OWNER_EXCLUSION_RESOLUTION_INPUT/machine/processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_input_matrix_public_safe.json",
    "KMFA/stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_CORRECTED_SOURCE_OR_OWNER_EXCLUSION_RESOLUTION_INPUT/machine/processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_input_summary.json",
    "KMFA/tests/test_v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_input.py",
    "KMFA/tools/check_v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_input.py",
    "KMFA/tools/v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_input.py",
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
        "private_owner_22_group_followup_queue_read_by_this_phase": True,
        "private_blocker_resolution_decision_queue_read_by_this_phase": True,
        "private_corrected_or_exclusion_template_written_by_this_phase": True,
    }


def _public_safety() -> dict[str, bool]:
    return {
        "public_safe_aggregate_only": True,
        "private_template_committed": False,
        "private_pending_queue_committed": False,
        "private_diagnostic_committed": False,
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


def _extract_resolution_items(private_decision_queue: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for row in private_decision_queue:
        if row.get("decision_code") != CORRECTED_OR_EXCLUSION_CODE:
            continue
        items.append(
            {
                "target_slot_id": row.get("target_slot_id"),
                "source_decision_code": row.get("decision_code"),
                "required_owner_decision_code": "PENDING_CORRECTED_SOURCE_OR_OWNER_EXCLUSION",
                "corrected_source_package_ref": "PENDING_PRIVATE_INPUT",
                "owner_exclusion_basis_ref": "PENDING_PRIVATE_INPUT",
                "owner_resolution_note": "PENDING_PRIVATE_INPUT",
                "resolution_application_allowed": False,
                "full_reconciliation_allowed": False,
            }
        )
    return items


def _build_private_artifacts(generated_at: str, items: list[dict[str, Any]], followup_queue: dict[str, Any]) -> dict[str, Any]:
    template = {
        "schema_version": "kmfa.private.v014_corrected_source_or_owner_exclusion_resolution_input_template.v1",
        "classification": "private_corrected_source_or_owner_exclusion_resolution_input_do_not_commit",
        "record_type": "v014_corrected_source_or_owner_exclusion_resolution_input_template",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "private_resolution_item_count": len(items),
        "source_followup_group_count": followup_queue.get("non_actionable_group_decision_count"),
        "source_unlinked_application_blocker_count": followup_queue.get("unlinked_application_blocker_count"),
        "allowed_owner_decision_codes": [
            "REGISTER_CORRECTED_SOURCE_REF",
            "OWNER_EXCLUDE_FROM_RECONCILIATION",
            "KEEP_BLOCKED_REQUEST_MORE_DIAGNOSTICS",
        ],
        "items": items,
    }
    pending_queue = [
        {
            "queue_index": index + 1,
            "target_slot_id": item.get("target_slot_id"),
            "required_owner_decision_code": item["required_owner_decision_code"],
            "owner_input_status": "missing",
            "resolution_application_allowed": False,
            "full_reconciliation_allowed": False,
        }
        for index, item in enumerate(items)
    ]
    diagnostic = {
        "schema_version": "kmfa.private.v014_corrected_source_or_owner_exclusion_resolution_input_diagnostic.v1",
        "classification": "private_corrected_source_or_owner_exclusion_resolution_input_diagnostic_do_not_commit",
        "record_type": "v014_corrected_source_or_owner_exclusion_resolution_input_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "private_resolution_item_count": len(items),
        "owner_resolution_input_present": False,
        "all_36_unlinked_blockers_resolved": False,
        "resolution_application_allowed": False,
        "full_reconciliation_allowed": False,
        "next_required_input": NEXT_REQUIRED_INPUT,
        "raw_boundary": _raw_boundary(),
    }
    private_report = f"""# Private corrected-source or owner-exclusion input

- phase_id: `{PHASE_ID}`
- private_resolution_item_count: `{len(items)}`
- owner_resolution_input_present: `false`
- resolution_application_allowed: `false`
- full_reconciliation_allowed: `false`

Fill this private template only with owner-approved corrected source references or explicit owner exclusion basis. Do not commit this file.
"""
    return {
        "template": template,
        "pending_queue": pending_queue,
        "diagnostic": diagnostic,
        "private_report": private_report,
    }


def _build_matrix(generated_at: str, owner_summary: dict[str, Any], private_item_count: int) -> dict[str, Any]:
    checks = [
        {
            "check_code": "owner_22_group_response_intaken",
            "status": "PASS" if owner_summary.get("owner_22_group_response_intaken") is True else "FAIL",
            "observed_public_safe": bool(owner_summary.get("owner_22_group_response_intaken")),
            "required": True,
        },
        {
            "check_code": "unlinked_blocker_count_locked",
            "status": "PASS" if owner_summary.get("unlinked_application_blocker_count") == 36 else "FAIL",
            "observed_public_safe": owner_summary.get("unlinked_application_blocker_count"),
            "required": 36,
        },
        {
            "check_code": "private_resolution_input_template_prepared",
            "status": "PASS" if private_item_count == 36 else "FAIL",
            "observed_public_safe": private_item_count,
            "required": 36,
        },
        {
            "check_code": "owner_resolution_input_present",
            "status": "FAIL",
            "observed_public_safe": False,
            "required": True,
        },
        {
            "check_code": "all_36_unlinked_blockers_resolved",
            "status": "FAIL",
            "observed_public_safe": False,
            "required": True,
        },
        {
            "check_code": "resolution_application_allowed",
            "status": "FAIL",
            "observed_public_safe": False,
            "required": True,
        },
        {
            "check_code": "full_reconciliation_allowed",
            "status": "FAIL",
            "observed_public_safe": False,
            "required": True,
        },
    ]
    pass_count = sum(1 for row in checks if row["status"] == "PASS")
    fail_count = sum(1 for row in checks if row["status"] == "FAIL")
    return {
        "schema_version": "kmfa.v014_corrected_source_or_owner_exclusion_resolution_input_matrix_public_safe.v1",
        "record_type": "v014_corrected_source_or_owner_exclusion_resolution_input_matrix_public_safe",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "decision_check_count": len(checks),
        "decision_pass_count": pass_count,
        "decision_fail_count": fail_count,
        "owner_resolution_input_present": False,
        "all_36_unlinked_blockers_resolved": False,
        "resolution_application_allowed": False,
        "full_reconciliation_allowed": False,
        "decision": DECISION,
        "checks": checks,
    }


def _write_human_artifacts(summary: dict[str, Any], matrix: dict[str, Any]) -> None:
    report = f"""# KMFA v0.1.4 Corrected Source Or Owner Exclusion Resolution Input

Decision: `{DECISION}`

This phase prepares a private input kit for the 36 unlinked application blockers that remain after the delegated 22-group owner response intake. It does not apply source-map records and does not run raw-to-processed comparison.

## Public-safe aggregate result

- Unlinked blockers requiring corrected source or owner exclusion: `{summary["unlinked_application_blocker_count"]}`
- Private resolution input item count: `{summary["private_resolution_item_count"]}`
- Source non-actionable group decisions: `{summary["source_non_actionable_group_decision_count"]}`
- Decision checks: `{matrix["decision_pass_count"]}` pass / `{matrix["decision_fail_count"]}` fail
- Owner resolution input present: `false`
- Resolution application allowed: `false`
- Full reconciliation allowed: `false`

Next required input: `{NEXT_REQUIRED_INPUT}`.
"""
    go_no_go_record = f"""# Go/No-Go Record

- phase_id: `{PHASE_ID}`
- decision: `{DECISION}`
- blocked_until: `{NEXT_REQUIRED_INPUT}`
- private_resolution_item_count: `{summary["private_resolution_item_count"]}`
- owner_resolution_input_present: `false`
- GitHub upload performed: `false`
- App reinstall performed: `false`
"""
    risk_register = """# Risk Register

- R1: Private resolution input can be mistaken for source-map application.
- R2: Owner corrected-source or exclusion decisions remain absent.
- R3: Raw-to-processed consistency is still unverified until a later explicit comparison phase.
"""
    rollback_plan = """# Rollback Plan

No raw inbox, source-map, materialization, reconciliation or active authorization file was mutated. To roll back, remove this phase's public artifacts and metadata copies, then remove the ignored private output directory if needed.
"""
    test_results = """# Test Results

Recorded validation commands for this phase:

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_input.py KMFA/tools/check_v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_input.py KMFA/tests/test_v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_input.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_input.py --generated-at 2026-07-06T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_input.py --require-private-template`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_input`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA`
- `git diff --check -- KMFA`

All listed commands must pass before local commit. The raw inbox is not read, listed, parsed, copied, moved, renamed, deleted, overwritten, normalized or mutated by this phase.
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
    event_id = "DEV-KMFA-20260706-V014-CORRECTED-SOURCE-OR-OWNER-EXCLUSION-RESOLUTION-INPUT"
    event = {
        "event_id": event_id,
        "event_time": generated_at,
        "event_type": "development",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "iteration_id": "ITER-20260706-KMFA-V014-CORRECTED-SOURCE-OR-OWNER-EXCLUSION-RESOLUTION-INPUT",
        "fact_level": "EXTRACTED",
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "go_no_go": DECISION,
        "private_resolution_item_count": summary["private_resolution_item_count"],
        "unlinked_application_blocker_count": summary["unlinked_application_blocker_count"],
        "owner_resolution_input_present": False,
        "resolution_application_allowed": False,
        "full_reconciliation_allowed": False,
        "business_value_consistency_verified": False,
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "result_commit": "PENDING",
        "files_changed": FILES_CHANGED,
        "summary": "Prepared private input template for 36 unlinked corrected-source or owner-exclusion blockers while keeping application and reconciliation gates closed.",
    }
    DEVELOPMENT_EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    existing = DEVELOPMENT_EVENTS_PATH.read_text(encoding="utf-8").splitlines() if DEVELOPMENT_EVENTS_PATH.exists() else []
    filtered = [line for line in existing if f'"event_id":"{event_id}"' not in line and f'"event_id": "{event_id}"' not in line]
    filtered.append(json.dumps(event, ensure_ascii=False, sort_keys=True))
    DEVELOPMENT_EVENTS_PATH.write_text("\n".join(filtered) + "\n", encoding="utf-8")


def generate(*, generated_at: str | None = None) -> dict[str, Any]:
    timestamp = _now(generated_at)
    owner_summary = _read_json(SOURCE_OWNER_RESPONSE_SUMMARY_PATH)
    owner_matrix = _read_json(SOURCE_OWNER_RESPONSE_MATRIX_PATH)
    followup_queue = _read_json(SOURCE_PRIVATE_FOLLOWUP_QUEUE_PATH)
    private_decision_queue = _read_jsonl(SOURCE_PRIVATE_DECISION_QUEUE_PATH)
    resolution_items = _extract_resolution_items(private_decision_queue)
    if len(resolution_items) != 36:
        raise ValueError(f"expected 36 corrected-source or owner-exclusion items, got {len(resolution_items)}")
    private_artifacts = _build_private_artifacts(timestamp, resolution_items, followup_queue)

    _write_json(PRIVATE_TEMPLATE_PATH, private_artifacts["template"])
    _write_jsonl(PRIVATE_PENDING_QUEUE_PATH, private_artifacts["pending_queue"])
    _write_json(PRIVATE_DIAGNOSTIC_PATH, private_artifacts["diagnostic"])
    _write_text(PRIVATE_REPORT_PATH, private_artifacts["private_report"])

    matrix = _build_matrix(timestamp, owner_summary, len(resolution_items))
    summary = {
        "schema_version": "kmfa.v014_corrected_source_or_owner_exclusion_resolution_input_summary.v1",
        "record_type": "v014_corrected_source_or_owner_exclusion_resolution_input_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "source_owner_response_phase_id": owner_summary["phase_id"],
        "source_owner_response_decision": owner_summary["decision"],
        "source_owner_response_matrix_fail_count": owner_matrix["decision_fail_count"],
        "source_non_actionable_group_decision_count": followup_queue["non_actionable_group_decision_count"],
        "source_unlinked_application_blocker_count": owner_summary["unlinked_application_blocker_count"],
        "unlinked_application_blocker_count": 36,
        "private_resolution_item_count": len(resolution_items),
        "private_pending_queue_count": len(private_artifacts["pending_queue"]),
        "private_template_written": True,
        "private_template_gitignored": _git_check_ignored(PRIVATE_TEMPLATE_PATH),
        "private_pending_queue_written": True,
        "private_pending_queue_gitignored": _git_check_ignored(PRIVATE_PENDING_QUEUE_PATH),
        "private_diagnostic_written": True,
        "private_diagnostic_gitignored": _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH),
        "private_report_written": True,
        "private_report_gitignored": _git_check_ignored(PRIVATE_REPORT_PATH),
        "owner_resolution_input_present": False,
        "corrected_source_package_ref_present": False,
        "owner_exclusion_basis_present": False,
        "all_36_unlinked_blockers_resolved": False,
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
        "next_required_input": NEXT_REQUIRED_INPUT,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
        "raw_boundary": _raw_boundary(),
        "public_safety": _public_safety(),
    }
    go_no_go = {
        "schema_version": "kmfa.v014_corrected_source_or_owner_exclusion_resolution_input_go_no_go.v1",
        "record_type": "v014_corrected_source_or_owner_exclusion_resolution_input_go_no_go",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "blocked_until": NEXT_REQUIRED_INPUT,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "private_resolution_item_count": len(resolution_items),
        "owner_resolution_input_present": False,
        "resolution_application_allowed": False,
        "full_reconciliation_allowed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }
    manifest = {
        "schema_version": "kmfa.v014_corrected_source_or_owner_exclusion_resolution_input_manifest.v1",
        "record_type": "v014_corrected_source_or_owner_exclusion_resolution_input_manifest",
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
            SOURCE_OWNER_RESPONSE_SUMMARY_PATH.as_posix(),
            SOURCE_OWNER_RESPONSE_MATRIX_PATH.as_posix(),
            "private:owner_22_group_followup_queue",
            "private:blocker_resolution_decision_queue",
        ],
        "public_artifacts": [path.as_posix() for path in (
            SUMMARY_PATH,
            MANIFEST_PATH,
            GO_NO_GO_PATH,
            MATRIX_PATH,
            REPORT_PATH,
            GO_NO_GO_RECORD_PATH,
            TEST_RESULTS_PATH,
            RISK_REGISTER_PATH,
            ROLLBACK_PATH,
            METADATA_SUMMARY_PATH,
            METADATA_MANIFEST_PATH,
            METADATA_GO_NO_GO_PATH,
            METADATA_MATRIX_PATH,
        )],
        "private_artifact_refs": [
            "private:corrected_source_or_owner_exclusion_resolution_input_template",
            "private:corrected_source_or_owner_exclusion_pending_queue",
            "private:corrected_source_or_owner_exclusion_resolution_input_diagnostic",
            "private:corrected_source_or_owner_exclusion_resolution_input_report",
        ],
        "validator": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_input.py --require-private-template",
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
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generated-at", default=None)
    args = parser.parse_args()
    manifest = generate(generated_at=args.generated_at)
    summary = manifest["summary"]
    print(
        "PASS: KMFA v0.1.4 corrected-source or owner-exclusion resolution input generated "
        f"(decision={summary['decision']}, private_items={summary['private_resolution_item_count']}, "
        f"owner_input_present={summary['owner_resolution_input_present']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
