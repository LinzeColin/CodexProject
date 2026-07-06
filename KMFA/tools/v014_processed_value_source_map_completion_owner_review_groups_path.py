#!/usr/bin/env python3
"""Prepare the owner review-groups path for KMFA v0.1.4 source-map completion."""

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
PHASE_ID = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_REVIEW_GROUPS_PATH"
TASK_ID = "KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-OWNER-REVIEW-GROUPS-PATH-20260706"
ACCEPTANCE_ID = "ACC-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-OWNER-REVIEW-GROUPS-PATH"
VERSION = "0.1.4-processed-value-source-map-completion-owner-review-groups-path"
STATUS = "completed_validated_local_only_no_go_review_groups_path_prepared"
PRIMARY_CONFIRMATION_CODE = "KMFA_ORR_OPTION_REQUEST_MORE_DIAGNOSTICS_ALL"
FOLLOW_UP_CONFIRMATION_CODE = "KMFA_ORR_OPTION_REVIEW_GROUPS"
DIAGNOSTIC_CONCLUSION = "owner_review_groups_path_prepared_owner_group_decisions_required"
NEXT_REQUIRED_INPUT = "owner_or_authorized_delegate_applies_group_level_decisions_to_private_response_template"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_review_groups_path_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_review_groups_path_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_review_groups_path_go_no_go_report.json"
REPORT_PATH = HUMAN_DIR / "processed_value_source_map_completion_owner_review_groups_path_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_processed_value_source_map_completion_owner_review_groups_path_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_processed_value_source_map_completion_owner_review_groups_path_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_processed_value_source_map_completion_owner_review_groups_path_go_no_go_report.json"
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"

PRIVATE_CONFIRMATION_RECORD_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_owner_response_decision_options/private_owner_response_confirmation_record.json"
)
PRIVATE_SUPPLEMENTAL_DIAGNOSTIC_REQUEST_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_owner_response_confirmation_application/private_supplemental_diagnostic_request_all_rows.json"
)
PRIVATE_REVIEW_GROUPS_NEXT_STEP_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_owner_response_confirmation_application/private_review_groups_next_step_queue.json"
)
PRIVATE_GROUPED_REVIEW_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_owner_review_intake_prep/private_grouped_owner_review_intake.json"
)
PRIVATE_RESPONSE_TEMPLATE_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_owner_review_intake_prep/private_owner_review_response_template.json"
)
PRIVATE_CANDIDATE_CATALOG_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_owner_review_intake_prep/private_candidate_catalog.json"
)
PRIVATE_OUTPUT_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_processed_value_source_map_completion_owner_review_groups_path"
PRIVATE_GROUPS_PACKET_PATH = PRIVATE_OUTPUT_DIR / "private_owner_review_groups_path_packet.json"
PRIVATE_RESPONSE_DRAFT_PATH = PRIVATE_OUTPUT_DIR / "private_owner_review_groups_path_response_draft.json"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_owner_review_groups_path_diagnostic.json"


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
        "private_groups_packet_committed": False,
        "private_response_draft_committed": False,
        "private_diagnostic_committed": False,
        "private_confirmation_record_committed": False,
        "raw_file_committed": False,
        "raw_filename_committed": False,
        "raw_archive_member_name_committed": False,
        "field_header_plaintext_committed": False,
        "row_value_committed": False,
        "business_value_committed": False,
        "credential_or_secret_committed": False,
    }


def _recommended_group_action(candidate_status: str) -> str:
    if candidate_status == "auto_ambiguous_multiple_candidates_requires_owner_review":
        return "owner_review_group_candidates"
    if candidate_status == "requires_non_numeric_owner_mapping":
        return "owner_supplies_non_numeric_mapping_or_marks_not_applicable"
    if candidate_status == "auto_unmatched_requires_owner_review":
        return "owner_requests_more_diagnostics_or_keeps_pending"
    return "owner_review_required"


def _build_private_records(*, generated_at: str, confirmation: dict[str, Any], grouped: dict[str, Any]) -> dict[str, Any]:
    if confirmation.get("follow_up_confirmation_code") != FOLLOW_UP_CONFIRMATION_CODE:
        raise ValueError("private confirmation record does not authorize the review groups path")
    review_groups = grouped.get("review_groups", [])
    if not isinstance(review_groups, list):
        raise ValueError("private grouped review file has invalid review_groups")
    group_records = []
    response_rows = []
    status_counts: Counter[str] = Counter()
    target_slot_counts: Counter[str] = Counter()
    candidate_catalog_count = 0
    for group in review_groups:
        if not isinstance(group, dict):
            continue
        status = str(group.get("candidate_status", "unknown"))
        slot_ids = group.get("target_slot_ids", [])
        if not isinstance(slot_ids, list):
            slot_ids = []
        top_records = group.get("top_candidate_records", [])
        if not isinstance(top_records, list):
            top_records = []
        status_counts[status] += 1
        target_slot_counts[status] += len(slot_ids)
        candidate_catalog_count += len(top_records)
        action = _recommended_group_action(status)
        group_records.append(
            {
                "review_group_id": group.get("review_group_id"),
                "context_group": group.get("context_group"),
                "candidate_status": status,
                "target_slot_count": len(slot_ids),
                "top_candidate_record_count": len(top_records),
                "recommended_group_review_action": action,
                "active_authorization_allowed": False,
            }
        )
        for slot_id in slot_ids:
            response_rows.append(
                {
                    "target_slot_id": slot_id,
                    "review_group_id": group.get("review_group_id"),
                    "candidate_status": status,
                    "recommended_group_review_action": action,
                    "owner_decision_code": "PENDING_OWNER_OR_AUTHORIZED_DELEGATE_GROUP_DECISION",
                    "active_authorization_allowed": False,
                }
            )
    packet = {
        "schema_version": "kmfa.private.v014_owner_review_groups_path_packet.v1",
        "classification": "private_owner_review_groups_path_packet_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_owner_review_groups_path_packet",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "primary_confirmation_code": confirmation.get("primary_confirmation_code"),
        "follow_up_confirmation_code": confirmation.get("follow_up_confirmation_code"),
        "review_group_count": len(group_records),
        "response_row_count": len(response_rows),
        "candidate_status_group_counts": dict(status_counts),
        "candidate_status_target_slot_counts": dict(target_slot_counts),
        "candidate_catalog_record_count": candidate_catalog_count,
        "review_groups_path_prepared": True,
        "owner_group_decision_applied": False,
        "active_owner_authorized_fill_record_ready": False,
        "groups": group_records,
    }
    response_draft = {
        "schema_version": "kmfa.private.v014_owner_review_groups_path_response_draft.v1",
        "classification": "private_owner_review_groups_path_response_draft_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_owner_review_groups_path_response_draft",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "draft_is_active_authorization_record": False,
        "owner_group_decision_applied": False,
        "response_row_count": len(response_rows),
        "response_rows": response_rows,
    }
    diagnostic = {
        "schema_version": "kmfa.private.v014_owner_review_groups_path_diagnostic.v1",
        "classification": "private_owner_review_groups_path_diagnostic_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_owner_review_groups_path_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "review_group_count": len(group_records),
        "response_row_count": len(response_rows),
        "candidate_status_group_counts": dict(status_counts),
        "candidate_status_target_slot_counts": dict(target_slot_counts),
        "candidate_catalog_record_count": candidate_catalog_count,
        "raw_boundary": _raw_boundary(),
    }
    return {"packet": packet, "response_draft": response_draft, "diagnostic": diagnostic}


def generate(*, generated_at: str | None = None, write_governance_event: bool = True) -> dict[str, Any]:
    timestamp = _now(generated_at)
    confirmation = _read_json(PRIVATE_CONFIRMATION_RECORD_PATH)
    supplemental = _read_json(PRIVATE_SUPPLEMENTAL_DIAGNOSTIC_REQUEST_PATH)
    next_step = _read_json(PRIVATE_REVIEW_GROUPS_NEXT_STEP_PATH)
    grouped = _read_json(PRIVATE_GROUPED_REVIEW_PATH)
    response_template = _read_json(PRIVATE_RESPONSE_TEMPLATE_PATH)
    catalog = _read_json(PRIVATE_CANDIDATE_CATALOG_PATH)
    private_records = _build_private_records(generated_at=timestamp, confirmation=confirmation, grouped=grouped)

    _write_json(PRIVATE_GROUPS_PACKET_PATH, private_records["packet"])
    _write_json(PRIVATE_RESPONSE_DRAFT_PATH, private_records["response_draft"])
    _write_json(PRIVATE_DIAGNOSTIC_PATH, private_records["diagnostic"])

    group_counts = private_records["packet"]["candidate_status_group_counts"]
    slot_counts = private_records["packet"]["candidate_status_target_slot_counts"]
    summary = {
        "schema_version": "kmfa.v014_owner_review_groups_path_summary.v1",
        "record_type": "v014_processed_value_source_map_completion_owner_review_groups_path_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "status": STATUS,
        "generated_at": timestamp,
        "primary_confirmation_code": PRIMARY_CONFIRMATION_CODE,
        "follow_up_confirmation_code": FOLLOW_UP_CONFIRMATION_CODE,
        "source_response_row_count": response_template.get("response_row_count"),
        "source_pending_owner_decision_count": confirmation.get("source_pending_owner_decision_count"),
        "source_supplemental_diagnostic_request_row_count": supplemental.get("diagnostic_request_row_count"),
        "source_review_group_follow_up_ready": next_step.get("review_group_follow_up_ready"),
        "review_group_count": private_records["packet"]["review_group_count"],
        "review_group_response_row_count": private_records["packet"]["response_row_count"],
        "candidate_catalog_record_count": catalog.get("candidate_catalog_record_count"),
        "candidate_status_group_counts": group_counts,
        "candidate_status_target_slot_counts": slot_counts,
        "ambiguous_review_group_count": group_counts.get("auto_ambiguous_multiple_candidates_requires_owner_review", 0),
        "non_numeric_review_group_count": group_counts.get("requires_non_numeric_owner_mapping", 0),
        "unmatched_review_group_count": group_counts.get("auto_unmatched_requires_owner_review", 0),
        "ambiguous_target_slot_count": slot_counts.get("auto_ambiguous_multiple_candidates_requires_owner_review", 0),
        "non_numeric_target_slot_count": slot_counts.get("requires_non_numeric_owner_mapping", 0),
        "unmatched_target_slot_count": slot_counts.get("auto_unmatched_requires_owner_review", 0),
        "private_groups_packet_written": True,
        "private_groups_packet_gitignored": _git_check_ignored(PRIVATE_GROUPS_PACKET_PATH),
        "private_response_draft_written": True,
        "private_response_draft_gitignored": _git_check_ignored(PRIVATE_RESPONSE_DRAFT_PATH),
        "private_diagnostic_written": True,
        "private_diagnostic_gitignored": _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH),
        "review_groups_path_prepared": True,
        "owner_group_decision_applied": False,
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
        "schema_version": "kmfa.v014_owner_review_groups_path_go_no_go.v1",
        "record_type": "v014_processed_value_source_map_completion_owner_review_groups_path_go_no_go_report",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "decision": "NO_GO",
        "status": STATUS,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "review_group_count": summary["review_group_count"],
        "review_group_response_row_count": summary["review_group_response_row_count"],
        "review_groups_path_prepared": True,
        "owner_group_decision_applied": False,
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
        "schema_version": "kmfa.v014_owner_review_groups_path_manifest.v1",
        "record_type": "v014_processed_value_source_map_completion_owner_review_groups_path_manifest",
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
            "private_groups_packet": "private_runtime_only",
            "private_response_draft": "private_runtime_only",
            "private_diagnostic": "private_runtime_only",
        },
        "validator": (
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. "
            "python3 KMFA/tools/check_v014_processed_value_source_map_completion_owner_review_groups_path.py "
            "--require-private-groups"
        ),
        "git": {
            "branch": _git_output(["branch", "--show-current"]),
            "head": _git_output(["rev-parse", "HEAD"]),
            "status_short": _git_output(["status", "--short", "--branch"]),
        },
    }
    report = f"""# V014 Owner Review Groups Path

Decision: NO_GO

This phase prepares the private owner review-groups path for the 113 pending rows across 22 groups. It does not modify the private owner response template, create active authorization, or apply source-map changes.

## Public-safe aggregate result

- Review groups: {summary["review_group_count"]}
- Response rows: {summary["review_group_response_row_count"]}
- Ambiguous groups / rows: {summary["ambiguous_review_group_count"]} / {summary["ambiguous_target_slot_count"]}
- Non-numeric groups / rows: {summary["non_numeric_review_group_count"]} / {summary["non_numeric_target_slot_count"]}
- Unmatched groups / rows: {summary["unmatched_review_group_count"]} / {summary["unmatched_target_slot_count"]}
- Candidate catalog records: {summary["candidate_catalog_record_count"]}
- Review groups path prepared: `true`

Next required input: `{NEXT_REQUIRED_INPUT}`.
"""
    go_no_go_record = f"""# Go/No-Go Record

- phase_id: `{PHASE_ID}`
- decision: `NO_GO`
- reason: review groups path is prepared, but owner group decisions are not yet applied.
- review_group_count: `{summary["review_group_count"]}`
- review_group_response_row_count: `{summary["review_group_response_row_count"]}`
- github upload performed: `false`
"""
    risk_register = """# Risk Register

- Risk: treating grouped routing as owner approval.
  Mitigation: this phase prepares private group review drafts only and keeps active authorization closed.
- Risk: leaking row-level private group routing publicly.
  Mitigation: public artifacts contain only aggregate counts and gate flags.
"""
    rollback_plan = """# Rollback Plan

No raw file, owner response template, completion template, active authorization record or source-map file was modified. To roll back, remove this phase's public artifacts and metadata copies, then remove the ignored private groups packet, response draft and diagnostic if not needed.
"""
    test_results = """# Test Results

Pending until validator and focused tests are run after artifact generation.

Expected validator:
`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_value_source_map_completion_owner_review_groups_path.py --require-private-groups`
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
    event_id = "DEV-KMFA-20260706-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-OWNER-REVIEW-GROUPS-PATH"
    event = {
        "event_id": event_id,
        "event_time": generated_at,
        "event_type": "development",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "iteration_id": "ITER-20260706-KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-OWNER-REVIEW-GROUPS-PATH",
        "fact_level": "EXTRACTED",
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "go_no_go": manifest["go_no_go"]["decision"],
        "review_group_count": manifest["summary"]["review_group_count"],
        "review_group_response_row_count": manifest["summary"]["review_group_response_row_count"],
        "owner_group_decision_applied": False,
        "active_owner_authorized_fill_record_ready": False,
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "result_commit": "PENDING",
        "summary": "Prepared the option 1 owner review-groups path; downstream active authorization remains closed.",
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
        "PASS: KMFA v0.1.4 owner review groups path generated "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"groups={manifest['summary']['review_group_count']}, "
        f"rows={manifest['summary']['review_group_response_row_count']})"
    )


if __name__ == "__main__":
    main()
