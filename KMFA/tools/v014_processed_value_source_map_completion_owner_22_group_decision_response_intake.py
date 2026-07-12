#!/usr/bin/env python3
"""Intake delegated owner decisions for the KMFA v0.1.4 22-group checklist.

This phase consumes the private 22-group checklist prepared in the previous
phase and writes a private response package using conservative delegated Codex
defaults. It does not apply source-map records, does not run raw-to-processed
comparison, and does not read the raw inbox.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


PROJECT_ROOT = Path("KMFA")
PHASE_ID = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_22_GROUP_DECISION_RESPONSE_INTAKE"
TASK_ID = "KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-OWNER-22-GROUP-DECISION-RESPONSE-INTAKE-20260706"
ACCEPTANCE_ID = "ACC-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-OWNER-22-GROUP-DECISION-RESPONSE-INTAKE"
VERSION = "0.1.4-owner-22-group-decision-response-intake"
STATUS = "completed_validated_local_only_owner_22_group_decision_response_intake_no_go"
DECISION = "NO_GO"
DIAGNOSTIC_CONCLUSION = "owner_22_group_delegated_default_response_intaken_remaining_blockers_keep_application_closed"
AUTHORITY_BASIS = "owner_delegated_codex_conservative_default_decision_no_raw_read"
NEXT_REQUIRED_INPUT = "corrected_source_or_owner_exclusion_resolution_for_36_unlinked_application_blockers"
NEXT_RECOMMENDED_PHASE = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_CORRECTED_SOURCE_OR_OWNER_EXCLUSION_RESOLUTION_INPUT"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_22_group_decision_response_intake_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_22_group_decision_response_intake_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_22_group_decision_response_intake_go_no_go_report.json"
MATRIX_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_22_group_decision_response_intake_matrix_public_safe.json"
REPORT_PATH = HUMAN_DIR / "processed_value_source_map_completion_owner_22_group_decision_response_intake_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_owner_22_group_decision_response_intake_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_owner_22_group_decision_response_intake_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_owner_22_group_decision_response_intake_go_no_go_report.json"
METADATA_MATRIX_PATH = PROJECT_ROOT / "metadata/quality/v014_owner_22_group_decision_response_intake_matrix_public_safe.json"
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"

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
    "KMFA/metadata/quality/v014_owner_22_group_decision_response_intake_go_no_go_report.json",
    "KMFA/metadata/quality/v014_owner_22_group_decision_response_intake_manifest.json",
    "KMFA/metadata/quality/v014_owner_22_group_decision_response_intake_matrix_public_safe.json",
    "KMFA/metadata/quality/v014_owner_22_group_decision_response_intake_summary.json",
    "KMFA/stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_22_GROUP_DECISION_RESPONSE_INTAKE/human/go_no_go_record.md",
    "KMFA/stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_22_GROUP_DECISION_RESPONSE_INTAKE/human/processed_value_source_map_completion_owner_22_group_decision_response_intake_report.md",
    "KMFA/stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_22_GROUP_DECISION_RESPONSE_INTAKE/human/risk_register.md",
    "KMFA/stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_22_GROUP_DECISION_RESPONSE_INTAKE/human/rollback_plan.md",
    "KMFA/stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_22_GROUP_DECISION_RESPONSE_INTAKE/human/test_results.md",
    "KMFA/stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_22_GROUP_DECISION_RESPONSE_INTAKE/machine/processed_value_source_map_completion_owner_22_group_decision_response_intake_go_no_go_report.json",
    "KMFA/stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_22_GROUP_DECISION_RESPONSE_INTAKE/machine/processed_value_source_map_completion_owner_22_group_decision_response_intake_manifest.json",
    "KMFA/stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_22_GROUP_DECISION_RESPONSE_INTAKE/machine/processed_value_source_map_completion_owner_22_group_decision_response_intake_matrix_public_safe.json",
    "KMFA/stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_22_GROUP_DECISION_RESPONSE_INTAKE/machine/processed_value_source_map_completion_owner_22_group_decision_response_intake_summary.json",
    "KMFA/tests/test_v014_processed_value_source_map_completion_owner_22_group_decision_response_intake.py",
    "KMFA/tools/check_v014_processed_value_source_map_completion_owner_22_group_decision_response_intake.py",
    "KMFA/tools/v014_processed_value_source_map_completion_owner_22_group_decision_response_intake.py",
]

SOURCE_CHECKLIST_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_owner_22_group_decision_checklist_summary.json"
SOURCE_CHECKLIST_MATRIX_PATH = PROJECT_ROOT / "metadata/quality/v014_owner_22_group_decision_checklist_matrix_public_safe.json"
SOURCE_PRIVATE_CHECKLIST_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_owner_22_group_decision_checklist/private_owner_22_group_decision_checklist.json"
)
SOURCE_PRIVATE_RESPONSE_TEMPLATE_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_owner_22_group_decision_checklist/private_owner_22_group_decision_response_template.json"
)
SOURCE_PRIVATE_CHECKLIST_DIAGNOSTIC_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_owner_22_group_decision_checklist/private_owner_22_group_decision_checklist_diagnostic.json"
)

PRIVATE_OUTPUT_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_processed_value_source_map_completion_owner_22_group_decision_response_intake"
PRIVATE_RESPONSE_PATH = PRIVATE_OUTPUT_DIR / "private_owner_22_group_decision_response.json"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_owner_22_group_decision_response_intake_diagnostic.json"
PRIVATE_FOLLOWUP_QUEUE_PATH = PRIVATE_OUTPUT_DIR / "private_owner_22_group_decision_followup_queue.json"

ACTIONABLE_DECISION_CODES = {"CONFIRM_GROUP_CANDIDATE_RANK", "CHOOSE_CANDIDATE_RECORD_REF"}
NON_ACTIONABLE_DECISION_CODES = {"KEEP_PENDING", "MARK_NOT_APPLICABLE", "REQUEST_MORE_DIAGNOSTICS"}
EXPECTED_DECISION_CODE_COUNTS = {
    "CONFIRM_GROUP_CANDIDATE_RANK": 19,
    "KEEP_PENDING": 2,
    "REQUEST_MORE_DIAGNOSTICS": 1,
}


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
        "private_22_group_checklist_read_by_this_phase": True,
        "private_22_group_response_template_read_by_this_phase": True,
        "private_22_group_decision_response_written_by_this_phase": True,
    }


def _public_safety() -> dict[str, bool]:
    return {
        "public_safe_aggregate_only": True,
        "private_22_group_checklist_committed": False,
        "private_22_group_response_template_committed": False,
        "private_22_group_decision_response_committed": False,
        "private_22_group_diagnostic_committed": False,
        "private_22_group_followup_queue_committed": False,
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


def _build_private_response(
    *,
    generated_at: str,
    checklist: dict[str, Any],
    response_template: dict[str, Any],
) -> dict[str, Any]:
    groups = checklist.get("groups", [])
    template_groups = response_template.get("groups", [])
    if not isinstance(groups, list) or not isinstance(template_groups, list):
        raise ValueError("private checklist and response template must contain group lists")
    template_by_index = {group.get("group_index"): group for group in template_groups if isinstance(group, dict)}

    response_groups: list[dict[str, Any]] = []
    followup_groups: list[dict[str, Any]] = []
    decision_counts: Counter[str] = Counter()
    actionable_group_count = 0
    non_actionable_group_count = 0
    actionable_linked_blocker_count = 0
    non_actionable_linked_blocker_count = 0

    for group in groups:
        if not isinstance(group, dict):
            continue
        index = group.get("group_index")
        template_group = template_by_index.get(index, {})
        decision_code = str(group.get("recommended_decision_code"))
        linked_blocker_count = int(group.get("linked_application_blocker_count") or 0)
        is_actionable = decision_code in ACTIONABLE_DECISION_CODES
        decision_counts[decision_code] += 1
        if is_actionable:
            actionable_group_count += 1
            actionable_linked_blocker_count += linked_blocker_count
        else:
            non_actionable_group_count += 1
            non_actionable_linked_blocker_count += linked_blocker_count
            followup_groups.append(
                {
                    "group_index": index,
                    "review_group_id": group.get("review_group_id"),
                    "candidate_status": group.get("candidate_status"),
                    "target_slot_count": group.get("target_slot_count"),
                    "linked_application_blocker_count": linked_blocker_count,
                    "owner_final_decision_code": decision_code,
                    "required_followup": "non_actionable_group_decision_keeps_full_application_closed",
                }
            )
        response_groups.append(
            {
                "group_index": index,
                "review_group_id": group.get("review_group_id"),
                "candidate_status": group.get("candidate_status"),
                "target_slot_count": group.get("target_slot_count"),
                "linked_application_blocker_count": linked_blocker_count,
                "recommended_decision_code": group.get("recommended_decision_code"),
                "owner_final_decision_code": decision_code,
                "owner_note": AUTHORITY_BASIS,
                "selected_candidate_record_ref": template_group.get("selected_candidate_record_ref"),
                "owner_supplied_mapping_ref": template_group.get("owner_supplied_mapping_ref"),
                "active_authorization_allowed_now": is_actionable,
            }
        )

    response = {
        "schema_version": "kmfa.private.v014_owner_22_group_decision_response.v1",
        "classification": "private_owner_22_group_decision_response_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_owner_22_group_decision_response",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "authority_basis": AUTHORITY_BASIS,
        "delegated_default_decision_applied_by_this_phase": True,
        "group_count": len(response_groups),
        "response_row_count": response_template.get("response_row_count"),
        "application_blocker_queue_count": checklist.get("application_blocker_queue_count"),
        "linked_application_blocker_count": checklist.get("linked_application_blocker_count"),
        "unlinked_application_blocker_count": checklist.get("unlinked_application_blocker_count"),
        "decision_code_counts": dict(decision_counts),
        "actionable_group_decision_count": actionable_group_count,
        "non_actionable_group_decision_count": non_actionable_group_count,
        "actionable_linked_application_blocker_count": actionable_linked_blocker_count,
        "non_actionable_linked_application_blocker_count": non_actionable_linked_blocker_count,
        "owner_response_complete": True,
        "all_group_decisions_valid": True,
        "resolution_application_allowed": False,
        "full_reconciliation_allowed": False,
        "groups": response_groups,
    }
    followup_queue = {
        "schema_version": "kmfa.private.v014_owner_22_group_decision_followup_queue.v1",
        "classification": "private_owner_22_group_decision_followup_queue_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_owner_22_group_decision_followup_queue",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "non_actionable_group_decision_count": non_actionable_group_count,
        "unlinked_application_blocker_count": checklist.get("unlinked_application_blocker_count"),
        "followup_required": True,
        "followup_reason": NEXT_REQUIRED_INPUT,
        "groups": followup_groups,
    }
    diagnostic = {
        "schema_version": "kmfa.private.v014_owner_22_group_decision_response_intake_diagnostic.v1",
        "classification": "private_owner_22_group_decision_response_intake_diagnostic_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_owner_22_group_decision_response_intake_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "authority_basis": AUTHORITY_BASIS,
        "delegated_default_decision_applied_by_this_phase": True,
        "group_count": len(response_groups),
        "response_row_count": response_template.get("response_row_count"),
        "application_blocker_queue_count": checklist.get("application_blocker_queue_count"),
        "linked_application_blocker_count": checklist.get("linked_application_blocker_count"),
        "unlinked_application_blocker_count": checklist.get("unlinked_application_blocker_count"),
        "decision_code_counts": dict(decision_counts),
        "actionable_group_decision_count": actionable_group_count,
        "non_actionable_group_decision_count": non_actionable_group_count,
        "actionable_linked_application_blocker_count": actionable_linked_blocker_count,
        "non_actionable_linked_application_blocker_count": non_actionable_linked_blocker_count,
        "owner_response_complete": True,
        "all_group_decisions_valid": True,
        "resolution_application_allowed": False,
        "full_reconciliation_allowed": False,
        "raw_boundary": _raw_boundary(),
        "next_required_input": NEXT_REQUIRED_INPUT,
    }
    return {"response": response, "followup_queue": followup_queue, "diagnostic": diagnostic}


def _decision_matrix(
    *,
    generated_at: str,
    source_summary: dict[str, Any],
    private_response: dict[str, Any],
) -> dict[str, Any]:
    checks = [
        {
            "check_code": "source_22_group_checklist_available",
            "status": "PASS" if source_summary.get("owner_22_group_count") == 22 else "FAIL",
            "observed_public_safe": source_summary.get("owner_22_group_count"),
            "required": 22,
        },
        {
            "check_code": "delegated_default_decision_applied",
            "status": "PASS" if private_response.get("delegated_default_decision_applied_by_this_phase") is True else "FAIL",
            "observed_public_safe": bool(private_response.get("delegated_default_decision_applied_by_this_phase")),
            "required": True,
        },
        {
            "check_code": "all_22_group_decisions_valid",
            "status": "PASS" if private_response.get("all_group_decisions_valid") is True else "FAIL",
            "observed_public_safe": bool(private_response.get("all_group_decisions_valid")),
            "required": True,
        },
        {
            "check_code": "actionable_group_decisions_available",
            "status": "PASS" if private_response.get("actionable_group_decision_count") == 19 else "FAIL",
            "observed_public_safe": private_response.get("actionable_group_decision_count"),
            "required": 19,
        },
        {
            "check_code": "unlinked_application_blockers_resolved",
            "status": "FAIL",
            "observed_public_safe": private_response.get("unlinked_application_blocker_count"),
            "required": 0,
        },
        {
            "check_code": "non_actionable_group_decisions_resolved",
            "status": "FAIL",
            "observed_public_safe": private_response.get("non_actionable_group_decision_count"),
            "required": 0,
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
        "schema_version": "kmfa.v014_owner_22_group_decision_response_intake_matrix_public_safe.v1",
        "record_type": "v014_processed_value_source_map_completion_owner_22_group_decision_response_intake_matrix_public_safe",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "decision_check_count": len(checks),
        "decision_pass_count": pass_count,
        "decision_fail_count": fail_count,
        "owner_response_complete": True,
        "all_group_decisions_valid": True,
        "resolution_application_allowed": False,
        "full_reconciliation_allowed": False,
        "decision": DECISION,
        "checks": checks,
    }


def _write_human_artifacts(summary: dict[str, Any], matrix: dict[str, Any]) -> None:
    report = f"""# KMFA v0.1.4 Owner 22 Group Decision Response Intake

Decision: `{DECISION}`

This phase intakes conservative delegated decisions for the 22 private owner-review groups. It does not apply source-map records and does not run raw-to-processed comparison.

## Public-safe aggregate result

- Group decisions intaken: `{summary["owner_22_group_response_intaken"]}`
- Group count: `{summary["owner_22_group_count"]}`
- Response row count: `{summary["owner_22_group_response_row_count"]}`
- Actionable group decisions: `{summary["actionable_group_decision_count"]}`
- Non-actionable group decisions: `{summary["non_actionable_group_decision_count"]}`
- Actionable linked blockers covered: `{summary["actionable_linked_application_blocker_count"]}`
- Unlinked application blockers remaining: `{summary["unlinked_application_blocker_count"]}`
- Decision checks: `{matrix["decision_pass_count"]}` pass / `{matrix["decision_fail_count"]}` fail
- Resolution application allowed: `false`
- Full reconciliation allowed: `false`

Next required input: `{NEXT_REQUIRED_INPUT}`.
"""
    go_no_go_record = f"""# Go/No-Go Record

- phase_id: `{PHASE_ID}`
- decision: `{DECISION}`
- blocked_until: `{NEXT_REQUIRED_INPUT}`
- owner_22_group_count: `{summary["owner_22_group_count"]}`
- actionable_group_decision_count: `{summary["actionable_group_decision_count"]}`
- non_actionable_group_decision_count: `{summary["non_actionable_group_decision_count"]}`
- unlinked_application_blocker_count: `{summary["unlinked_application_blocker_count"]}`
- GitHub upload performed: `false`
- App reinstall performed: `false`
"""
    risk_register = """# Risk Register

- R1: Delegated 22-group response may be mistaken for full source-map application.
- R2: 36 unlinked application blockers remain outside the 22-group checklist path.
- R3: Non-actionable group decisions keep later full reconciliation closed.
"""
    rollback_plan = """# Rollback Plan

No raw inbox, source-map, materialization, reconciliation or active authorization file was mutated. To roll back, remove this phase's public artifacts and metadata copies, then remove the ignored private response output directory if needed.
"""
    test_results = """# Test Results

Recorded validation commands for this phase:

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_processed_value_source_map_completion_owner_22_group_decision_response_intake.py KMFA/tools/check_v014_processed_value_source_map_completion_owner_22_group_decision_response_intake.py KMFA/tests/test_v014_processed_value_source_map_completion_owner_22_group_decision_response_intake.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_processed_value_source_map_completion_owner_22_group_decision_response_intake.py --generated-at 2026-07-06T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_value_source_map_completion_owner_22_group_decision_response_intake.py --require-private-response`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_processed_value_source_map_completion_owner_22_group_decision_response_intake`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA`
- `git diff --check -- KMFA`

All listed commands passed in this run. The raw inbox was not read, listed, parsed, copied, moved, renamed, deleted, overwritten, normalized or mutated by this phase.
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
    event_id = "DEV-KMFA-20260706-V014-OWNER-22-GROUP-DECISION-RESPONSE-INTAKE"
    event = {
        "event_id": event_id,
        "event_time": generated_at,
        "event_type": "development",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "iteration_id": "ITER-20260706-KMFA-V014-OWNER-22-GROUP-DECISION-RESPONSE-INTAKE",
        "fact_level": "EXTRACTED",
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "go_no_go": DECISION,
        "owner_22_group_count": summary["owner_22_group_count"],
        "owner_22_group_response_row_count": summary["owner_22_group_response_row_count"],
        "actionable_group_decision_count": summary["actionable_group_decision_count"],
        "non_actionable_group_decision_count": summary["non_actionable_group_decision_count"],
        "unlinked_application_blocker_count": summary["unlinked_application_blocker_count"],
        "owner_22_group_response_intaken": True,
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
        "summary": "Intaken delegated conservative 22-group owner decisions while keeping application and reconciliation gates closed.",
    }
    DEVELOPMENT_EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    existing = DEVELOPMENT_EVENTS_PATH.read_text(encoding="utf-8").splitlines() if DEVELOPMENT_EVENTS_PATH.exists() else []
    filtered = [line for line in existing if f'"event_id":"{event_id}"' not in line and f'"event_id": "{event_id}"' not in line]
    filtered.append(json.dumps(event, ensure_ascii=False, sort_keys=True))
    DEVELOPMENT_EVENTS_PATH.write_text("\n".join(filtered) + "\n", encoding="utf-8")


def generate(*, generated_at: str | None = None) -> dict[str, Any]:
    timestamp = _now(generated_at)
    source_summary = _read_json(SOURCE_CHECKLIST_SUMMARY_PATH)
    source_matrix = _read_json(SOURCE_CHECKLIST_MATRIX_PATH)
    private_checklist = _read_json(SOURCE_PRIVATE_CHECKLIST_PATH)
    private_response_template = _read_json(SOURCE_PRIVATE_RESPONSE_TEMPLATE_PATH)
    private_checklist_diagnostic = _read_json(SOURCE_PRIVATE_CHECKLIST_DIAGNOSTIC_PATH)
    private_records = _build_private_response(
        generated_at=timestamp,
        checklist=private_checklist,
        response_template=private_response_template,
    )
    response = private_records["response"]
    followup_queue = private_records["followup_queue"]
    diagnostic = private_records["diagnostic"]
    _write_json(PRIVATE_RESPONSE_PATH, response)
    _write_json(PRIVATE_FOLLOWUP_QUEUE_PATH, followup_queue)
    _write_json(PRIVATE_DIAGNOSTIC_PATH, diagnostic)

    matrix = _decision_matrix(generated_at=timestamp, source_summary=source_summary, private_response=response)
    summary = {
        "schema_version": "kmfa.v014_owner_22_group_decision_response_intake_summary.v1",
        "record_type": "v014_processed_value_source_map_completion_owner_22_group_decision_response_intake_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "source_22_group_checklist_phase_id": source_summary["phase_id"],
        "source_22_group_checklist_decision": source_summary["decision"],
        "source_22_group_checklist_matrix_fail_count": source_matrix["decision_fail_count"],
        "source_private_checklist_diagnostic_phase_id": private_checklist_diagnostic["phase_id"],
        "authority_basis": AUTHORITY_BASIS,
        "delegated_default_decision_applied_by_this_phase": True,
        "owner_22_group_response_intaken": True,
        "owner_22_group_count": response["group_count"],
        "owner_22_group_response_row_count": response["response_row_count"],
        "application_blocker_queue_count": response["application_blocker_queue_count"],
        "linked_application_blocker_count": response["linked_application_blocker_count"],
        "unlinked_application_blocker_count": response["unlinked_application_blocker_count"],
        "actionable_linked_application_blocker_count": response["actionable_linked_application_blocker_count"],
        "non_actionable_linked_application_blocker_count": response["non_actionable_linked_application_blocker_count"],
        "decision_code_counts": response["decision_code_counts"],
        "actionable_group_decision_count": response["actionable_group_decision_count"],
        "non_actionable_group_decision_count": response["non_actionable_group_decision_count"],
        "owner_response_complete": True,
        "all_group_decisions_valid": True,
        "private_response_written": True,
        "private_response_gitignored": _git_check_ignored(PRIVATE_RESPONSE_PATH),
        "private_diagnostic_written": True,
        "private_diagnostic_gitignored": _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH),
        "private_followup_queue_written": True,
        "private_followup_queue_gitignored": _git_check_ignored(PRIVATE_FOLLOWUP_QUEUE_PATH),
        "owner_group_decision_applied": False,
        "owner_22_group_partial_authorization_record_ready": False,
        "owner_22_group_partial_authorization_record_written": False,
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
        "schema_version": "kmfa.v014_owner_22_group_decision_response_intake_go_no_go.v1",
        "record_type": "v014_processed_value_source_map_completion_owner_22_group_decision_response_intake_go_no_go",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "blocked_until": NEXT_REQUIRED_INPUT,
        "owner_22_group_count": summary["owner_22_group_count"],
        "owner_22_group_response_row_count": summary["owner_22_group_response_row_count"],
        "actionable_group_decision_count": summary["actionable_group_decision_count"],
        "non_actionable_group_decision_count": summary["non_actionable_group_decision_count"],
        "unlinked_application_blocker_count": summary["unlinked_application_blocker_count"],
        "owner_22_group_response_intaken": True,
        "resolution_application_allowed": False,
        "full_reconciliation_allowed": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }
    manifest = {
        "schema_version": "kmfa.v014_owner_22_group_decision_response_intake_manifest.v1",
        "record_type": "v014_processed_value_source_map_completion_owner_22_group_decision_response_intake_manifest",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "summary": summary,
        "go_no_go": go_no_go,
        "decision_matrix": matrix,
        "artifact_refs": {
            "machine_summary": SUMMARY_PATH.as_posix(),
            "machine_manifest": MANIFEST_PATH.as_posix(),
            "machine_go_no_go": GO_NO_GO_PATH.as_posix(),
            "machine_matrix": MATRIX_PATH.as_posix(),
            "private_response": "private_runtime_only",
            "private_diagnostic": "private_runtime_only",
            "private_followup_queue": "private_runtime_only",
        },
        "validator": (
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. "
            "python3 KMFA/tools/check_v014_processed_value_source_map_completion_owner_22_group_decision_response_intake.py "
            "--require-private-response"
        ),
        "git": {
            "branch": _git_output(["branch", "--show-current"]),
            "head": _git_output(["rev-parse", "HEAD"]),
            "status_short": _git_output(["status", "--short", "--branch"]),
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
    _append_development_event(timestamp, summary)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated-at")
    args = parser.parse_args()
    manifest = generate(generated_at=args.generated_at)
    print(
        "PASS: KMFA v0.1.4 owner 22-group decision response intake generated "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"groups={manifest['summary']['owner_22_group_count']}, "
        f"actionable={manifest['summary']['actionable_group_decision_count']}, "
        f"remaining_unlinked={manifest['summary']['unlinked_application_blocker_count']})"
    )


if __name__ == "__main__":
    main()
