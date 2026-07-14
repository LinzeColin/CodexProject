#!/usr/bin/env python3
"""Apply the owner response confirmation sequence for KMFA v0.1.4.

This phase records the user-authorized sequence "complete option 3, then follow
option 1" as a private confirmation record. It prepares private supplemental
diagnostic requests and keeps all downstream application gates closed.
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
PHASE_ID = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_RESPONSE_CONFIRMATION_APPLICATION"
TASK_ID = "KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-OWNER-RESPONSE-CONFIRMATION-APPLICATION-20260706"
ACCEPTANCE_ID = "ACC-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-OWNER-RESPONSE-CONFIRMATION-APPLICATION"
VERSION = "0.1.4-processed-value-source-map-completion-owner-response-confirmation-application"
STATUS = "completed_validated_local_only_no_go_diagnostics_then_review_groups_confirmed"
PRIMARY_CONFIRMATION_CODE = "KMFA_ORR_OPTION_REQUEST_MORE_DIAGNOSTICS_ALL"
FOLLOW_UP_CONFIRMATION_CODE = "KMFA_ORR_OPTION_REVIEW_GROUPS"
DIAGNOSTIC_CONCLUSION = "owner_confirmed_request_more_diagnostics_then_review_groups"
NEXT_REQUIRED_INPUT = "run_owner_review_groups_phase_after_private_supplemental_diagnostics"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_response_confirmation_application_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_response_confirmation_application_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_response_confirmation_application_go_no_go_report.json"
REPORT_PATH = HUMAN_DIR / "processed_value_source_map_completion_owner_response_confirmation_application_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_processed_value_source_map_completion_owner_response_confirmation_application_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_processed_value_source_map_completion_owner_response_confirmation_application_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_processed_value_source_map_completion_owner_response_confirmation_application_go_no_go_report.json"
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"

DECISION_OPTIONS_SUMMARY_PATH = (
    PROJECT_ROOT
    / "stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_RESPONSE_DECISION_OPTIONS/machine/processed_value_source_map_completion_owner_response_decision_options_summary.json"
)
PRIVATE_DECISION_OPTIONS_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_processed_value_source_map_completion_owner_response_decision_options"
PRIVATE_OPTIONS_PATH = PRIVATE_DECISION_OPTIONS_DIR / "private_owner_response_decision_options.json"
PRIVATE_NON_ACTIVE_DRAFT_PATH = PRIVATE_DECISION_OPTIONS_DIR / "private_owner_response_non_active_draft.json"
PRIVATE_CONFIRMATION_RECORD_PATH = PRIVATE_DECISION_OPTIONS_DIR / "private_owner_response_confirmation_record.json"
PRIVATE_OUTPUT_DIR = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_owner_response_confirmation_application"
)
PRIVATE_SUPPLEMENTAL_DIAGNOSTIC_REQUEST_PATH = PRIVATE_OUTPUT_DIR / "private_supplemental_diagnostic_request_all_rows.json"
PRIVATE_REVIEW_GROUPS_NEXT_STEP_PATH = PRIVATE_OUTPUT_DIR / "private_review_groups_next_step_queue.json"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_owner_response_confirmation_application_diagnostic.json"


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
        "private_confirmation_record_committed": False,
        "private_supplemental_diagnostic_request_committed": False,
        "private_review_group_queue_committed": False,
        "private_diagnostic_committed": False,
        "raw_file_committed": False,
        "raw_filename_committed": False,
        "raw_archive_member_name_committed": False,
        "field_header_plaintext_committed": False,
        "row_value_committed": False,
        "business_value_committed": False,
        "credential_or_secret_committed": False,
    }


def _build_private_records(*, generated_at: str, options: dict[str, Any], draft: dict[str, Any]) -> dict[str, Any]:
    option_codes = [
        option.get("confirmation_code")
        for option in options.get("decision_options", [])
        if isinstance(option, dict)
    ]
    if PRIMARY_CONFIRMATION_CODE not in option_codes or FOLLOW_UP_CONFIRMATION_CODE not in option_codes:
        raise ValueError("requested confirmation codes are not present in private decision options")
    rows = draft.get("response_rows", [])
    if not isinstance(rows, list):
        raise ValueError("private non-active draft response_rows must be a list")
    diagnostic_items = []
    review_queue = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        item = {
            "target_slot_id": row.get("target_slot_id"),
            "review_group_id": row.get("review_group_id"),
            "context_group": row.get("context_group"),
            "requested_primary_action": "request_more_diagnostics",
            "follow_up_action": "review_groups",
            "active_authorization_allowed": False,
        }
        diagnostic_items.append(item)
        review_queue.append(
            {
                "target_slot_id": row.get("target_slot_id"),
                "review_group_id": row.get("review_group_id"),
                "route_after_diagnostics": "owner_review_groups",
                "active_authorization_allowed": False,
            }
        )
    confirmation_record = {
        "schema_version": "kmfa.private.v014_owner_response_confirmation_record.v1",
        "classification": "private_owner_response_confirmation_record_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_owner_response_confirmation_record",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "instruction_source": "user_chat_zh_2026_07_06",
        "instruction_summary": "complete_option_3_then_follow_option_1",
        "primary_confirmation_code": PRIMARY_CONFIRMATION_CODE,
        "follow_up_confirmation_code": FOLLOW_UP_CONFIRMATION_CODE,
        "requested_sequence": [PRIMARY_CONFIRMATION_CODE, FOLLOW_UP_CONFIRMATION_CODE],
        "source_response_row_count": len(rows),
        "source_pending_owner_decision_count": options.get("source_pending_owner_decision_count"),
        "source_review_group_count": options.get("source_review_group_count"),
        "diagnostic_request_row_count": len(diagnostic_items),
        "review_group_follow_up_ready": True,
        "active_owner_authorized_fill_record_ready": False,
        "active_owner_authorized_fill_record_written": False,
        "owner_response_template_modified": False,
        "completion_template_overwritten": False,
        "source_map_completion_reapplication_ready": False,
    }
    supplemental_request = {
        "schema_version": "kmfa.private.v014_supplemental_diagnostic_request_all_rows.v1",
        "classification": "private_supplemental_diagnostic_request_all_rows_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_supplemental_diagnostic_request_all_rows",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "diagnostic_request_row_count": len(diagnostic_items),
        "diagnostic_items": diagnostic_items,
    }
    review_groups_next = {
        "schema_version": "kmfa.private.v014_review_groups_next_step_queue.v1",
        "classification": "private_review_groups_next_step_queue_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_review_groups_next_step_queue",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "review_group_follow_up_ready": True,
        "review_group_follow_up_code": FOLLOW_UP_CONFIRMATION_CODE,
        "queued_row_count": len(review_queue),
        "queued_rows": review_queue,
    }
    private_diagnostic = {
        "schema_version": "kmfa.private.v014_owner_response_confirmation_application_diagnostic.v1",
        "classification": "private_owner_response_confirmation_application_diagnostic_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_owner_response_confirmation_application_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "primary_confirmation_code": PRIMARY_CONFIRMATION_CODE,
        "follow_up_confirmation_code": FOLLOW_UP_CONFIRMATION_CODE,
        "source_response_row_count": len(rows),
        "diagnostic_request_row_count": len(diagnostic_items),
        "review_group_follow_up_ready": True,
        "raw_boundary": _raw_boundary(),
    }
    return {
        "confirmation_record": confirmation_record,
        "supplemental_request": supplemental_request,
        "review_groups_next": review_groups_next,
        "private_diagnostic": private_diagnostic,
    }


def generate(*, generated_at: str | None = None, write_governance_event: bool = True) -> dict[str, Any]:
    timestamp = _now(generated_at)
    source_summary = _read_json(DECISION_OPTIONS_SUMMARY_PATH)
    private_options = _read_json(PRIVATE_OPTIONS_PATH)
    private_draft = _read_json(PRIVATE_NON_ACTIVE_DRAFT_PATH)
    private_records = _build_private_records(generated_at=timestamp, options=private_options, draft=private_draft)

    _write_json(PRIVATE_CONFIRMATION_RECORD_PATH, private_records["confirmation_record"])
    _write_json(PRIVATE_SUPPLEMENTAL_DIAGNOSTIC_REQUEST_PATH, private_records["supplemental_request"])
    _write_json(PRIVATE_REVIEW_GROUPS_NEXT_STEP_PATH, private_records["review_groups_next"])
    _write_json(PRIVATE_DIAGNOSTIC_PATH, private_records["private_diagnostic"])

    summary = {
        "schema_version": "kmfa.v014_owner_response_confirmation_application_summary.v1",
        "record_type": "v014_processed_value_source_map_completion_owner_response_confirmation_application_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "status": STATUS,
        "generated_at": timestamp,
        "source_decision_options_phase_id": source_summary.get("phase_id"),
        "source_response_row_count": source_summary.get("source_response_row_count"),
        "source_pending_owner_decision_count": source_summary.get("source_pending_owner_decision_count"),
        "decision_option_count": source_summary.get("decision_option_count"),
        "primary_confirmation_code": PRIMARY_CONFIRMATION_CODE,
        "follow_up_confirmation_code": FOLLOW_UP_CONFIRMATION_CODE,
        "confirmation_record_written": True,
        "confirmation_record_gitignored": _git_check_ignored(PRIVATE_CONFIRMATION_RECORD_PATH),
        "supplemental_diagnostic_request_written": True,
        "supplemental_diagnostic_request_gitignored": _git_check_ignored(PRIVATE_SUPPLEMENTAL_DIAGNOSTIC_REQUEST_PATH),
        "supplemental_diagnostic_request_row_count": private_records["supplemental_request"]["diagnostic_request_row_count"],
        "review_group_follow_up_ready": True,
        "review_group_follow_up_row_count": private_records["review_groups_next"]["queued_row_count"],
        "active_owner_authorized_fill_record_ready": False,
        "active_owner_authorized_fill_record_written": False,
        "owner_response_template_modified": False,
        "completion_template_overwritten": False,
        "authorized_completion_record_supplied": False,
        "source_map_completion_reapplication_ready": False,
        "source_map_completion_reapplication_performed": False,
        "source_map_records_applied_count": 0,
        "processed_value_materialization_replay_performed": False,
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
        "lineage_full_check_complete": False,
        "formal_report_allowed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "decision": "NO_GO",
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "next_required_input": NEXT_REQUIRED_INPUT,
        "raw_boundary": _raw_boundary(),
        "public_safety": _public_safety(),
    }
    go_no_go = {
        "schema_version": "kmfa.v014_owner_response_confirmation_application_go_no_go.v1",
        "record_type": "v014_processed_value_source_map_completion_owner_response_confirmation_application_go_no_go_report",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "decision": "NO_GO",
        "status": STATUS,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "primary_confirmation_code": PRIMARY_CONFIRMATION_CODE,
        "follow_up_confirmation_code": FOLLOW_UP_CONFIRMATION_CODE,
        "supplemental_diagnostic_request_row_count": summary["supplemental_diagnostic_request_row_count"],
        "review_group_follow_up_ready": True,
        "active_owner_authorized_fill_record_ready": False,
        "source_map_completion_reapplication_ready": False,
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "blocked_until": NEXT_REQUIRED_INPUT,
    }
    manifest = {
        "schema_version": "kmfa.v014_owner_response_confirmation_application_manifest.v1",
        "record_type": "v014_processed_value_source_map_completion_owner_response_confirmation_application_manifest",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_ids": [ACCEPTANCE_ID],
        "generated_at": timestamp,
        "status": STATUS,
        "summary": summary,
        "go_no_go": go_no_go,
        "artifact_refs": {
            "machine_summary": SUMMARY_PATH.as_posix(),
            "machine_manifest": MANIFEST_PATH.as_posix(),
            "machine_go_no_go": GO_NO_GO_PATH.as_posix(),
            "private_confirmation_record": "private_runtime_only",
            "private_supplemental_diagnostic_request": "private_runtime_only",
            "private_review_groups_next_step_queue": "private_runtime_only",
            "private_diagnostic": "private_runtime_only",
        },
        "validator": (
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. "
            "python3 KMFA/tools/check_v014_processed_value_source_map_completion_owner_response_confirmation_application.py "
            "--require-private-confirmation"
        ),
        "git": {
            "branch": _git_output(["branch", "--show-current"]),
            "head": _git_output(["rev-parse", "HEAD"]),
            "status_short": _git_output(["status", "--short", "--branch"]),
        },
    }
    report = f"""# V014 Owner Response Confirmation Application

Decision: NO_GO

This phase records the owner instruction sequence: primary option 3 first, then option 1. It creates private-only confirmation and diagnostic request records, but it does not create active authorization or apply source-map changes.

## Public-safe aggregate result

- Source response rows: {summary["source_response_row_count"]}
- Source pending owner decisions: {summary["source_pending_owner_decision_count"]}
- Primary confirmation code: `{PRIMARY_CONFIRMATION_CODE}`
- Follow-up confirmation code: `{FOLLOW_UP_CONFIRMATION_CODE}`
- Supplemental diagnostic request rows: {summary["supplemental_diagnostic_request_row_count"]}
- Review group follow-up ready: `true`

Next required input: `{NEXT_REQUIRED_INPUT}`.
"""
    go_no_go_record = f"""# Go/No-Go Record

- phase_id: `{PHASE_ID}`
- decision: `NO_GO`
- reason: option 3 has been recorded first, and option 1 is queued next; active authorization is still closed.
- primary confirmation code: `{PRIMARY_CONFIRMATION_CODE}`
- follow-up confirmation code: `{FOLLOW_UP_CONFIRMATION_CODE}`
- github upload performed: `false`
"""
    risk_register = """# Risk Register

- Risk: treating a diagnostic request as active authorization.
  Mitigation: this phase records the confirmation sequence but keeps active authorization and source-map application closed.
- Risk: private row-level diagnostics leaking publicly.
  Mitigation: public artifacts contain only aggregate counts and gate flags.
"""
    rollback_plan = """# Rollback Plan

No raw file, response template, completion template, active authorization record or source-map file was modified. To roll back, remove this phase's public artifacts and metadata copies, then remove the ignored private confirmation and diagnostic records if needed.
"""
    test_results = """# Test Results

Pending until validator and focused tests are run after artifact generation.

Expected validator:
`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_value_source_map_completion_owner_response_confirmation_application.py --require-private-confirmation`
"""
    for path, payload in (
        (SUMMARY_PATH, summary),
        (MANIFEST_PATH, manifest),
        (GO_NO_GO_PATH, go_no_go),
        (METADATA_SUMMARY_PATH, summary),
        (METADATA_MANIFEST_PATH, manifest),
        (METADATA_GO_NO_GO_PATH, go_no_go),
    ):
        _write_json(path, payload)
    for path, text in (
        (REPORT_PATH, report),
        (GO_NO_GO_RECORD_PATH, go_no_go_record),
        (RISK_REGISTER_PATH, risk_register),
        (ROLLBACK_PATH, rollback_plan),
        (TEST_RESULTS_PATH, test_results),
    ):
        _write_text(path, text)
    if write_governance_event:
        _append_development_event(timestamp, manifest)
    return manifest


def _append_development_event(generated_at: str, manifest: dict[str, Any]) -> None:
    event_id = "DEV-KMFA-20260706-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-OWNER-RESPONSE-CONFIRMATION-APPLICATION"
    event = {
        "event_id": event_id,
        "event_time": generated_at,
        "event_type": "development",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "iteration_id": "ITER-20260706-KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-OWNER-RESPONSE-CONFIRMATION-APPLICATION",
        "fact_level": "EXTRACTED",
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "go_no_go": manifest["go_no_go"]["decision"],
        "primary_confirmation_code": PRIMARY_CONFIRMATION_CODE,
        "follow_up_confirmation_code": FOLLOW_UP_CONFIRMATION_CODE,
        "supplemental_diagnostic_request_row_count": manifest["summary"]["supplemental_diagnostic_request_row_count"],
        "active_owner_authorized_fill_record_ready": False,
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "result_commit": "PENDING",
        "summary": "Recorded user instruction to complete option 3 first and queue option 1 next; downstream active authorization remains closed.",
    }
    DEVELOPMENT_EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    existing = DEVELOPMENT_EVENTS_PATH.read_text(encoding="utf-8").splitlines() if DEVELOPMENT_EVENTS_PATH.exists() else []
    filtered = [line for line in existing if f'"event_id":"{event_id}"' not in line and f'"event_id": "{event_id}"' not in line]
    filtered.append(json.dumps(event, ensure_ascii=False, sort_keys=True))
    DEVELOPMENT_EVENTS_PATH.write_text("\n".join(filtered) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated-at")
    args = parser.parse_args()
    manifest = generate(generated_at=args.generated_at)
    print(
        "PASS: KMFA v0.1.4 owner response confirmation application generated "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"primary={manifest['summary']['primary_confirmation_code']}, "
        f"follow_up={manifest['summary']['follow_up_confirmation_code']}, "
        f"rows={manifest['summary']['supplemental_diagnostic_request_row_count']})"
    )


if __name__ == "__main__":
    main()
