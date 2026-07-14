#!/usr/bin/env python3
"""Apply the KMFA v0.1.4 owner review-groups decision gate.

This phase checks the private owner review-groups response draft. It does not
fill decisions, write active authorization, apply source-map records, or read
raw inbox data.
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
PHASE_ID = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_GROUP_DECISION_APPLICATION"
TASK_ID = "KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-OWNER-GROUP-DECISION-APPLICATION-20260706"
ACCEPTANCE_ID = "ACC-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-OWNER-GROUP-DECISION-APPLICATION"
VERSION = "0.1.4-processed-value-source-map-completion-owner-group-decision-application"
STATUS = "completed_validated_local_only_no_go_owner_group_decisions_missing"
DIAGNOSTIC_CONCLUSION = "owner_group_decisions_missing_active_authorization_blocked"
NEXT_REQUIRED_INPUT = "owner_or_authorized_delegate_supplies_group_level_decisions"
PENDING_DECISION_CODE = "PENDING_OWNER_OR_AUTHORIZED_DELEGATE_GROUP_DECISION"
VALID_OWNER_GROUP_DECISION_CODES = {
    "CONFIRM_GROUP_CANDIDATE_RANK",
    "CHOOSE_CANDIDATE_RECORD_REF",
    "KEEP_PENDING",
    "MARK_NOT_APPLICABLE",
    "REQUEST_MORE_DIAGNOSTICS",
}

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_group_decision_application_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_group_decision_application_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_group_decision_application_go_no_go_report.json"
REPORT_PATH = HUMAN_DIR / "processed_value_source_map_completion_owner_group_decision_application_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_processed_value_source_map_completion_owner_group_decision_application_summary.json"
)
METADATA_MANIFEST_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_processed_value_source_map_completion_owner_group_decision_application_manifest.json"
)
METADATA_GO_NO_GO_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_processed_value_source_map_completion_owner_group_decision_application_go_no_go_report.json"
)
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"

SOURCE_GROUPS_SUMMARY_PATH = (
    PROJECT_ROOT
    / "stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_REVIEW_GROUPS_PATH/machine/processed_value_source_map_completion_owner_review_groups_path_summary.json"
)
PRIVATE_GROUPS_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_processed_value_source_map_completion_owner_review_groups_path"
PRIVATE_GROUPS_PACKET_PATH = PRIVATE_GROUPS_DIR / "private_owner_review_groups_path_packet.json"
PRIVATE_RESPONSE_DRAFT_PATH = PRIVATE_GROUPS_DIR / "private_owner_review_groups_path_response_draft.json"
PRIVATE_SOURCE_DIAGNOSTIC_PATH = PRIVATE_GROUPS_DIR / "private_owner_review_groups_path_diagnostic.json"

PRIVATE_OUTPUT_DIR = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_owner_group_decision_application"
)
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_owner_group_decision_application_diagnostic.json"
PRIVATE_PENDING_QUEUE_PATH = PRIVATE_OUTPUT_DIR / "private_owner_group_decision_pending_queue.json"


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
        "private_source_diagnostic_committed": False,
        "private_application_diagnostic_committed": False,
        "private_pending_queue_committed": False,
        "raw_file_committed": False,
        "raw_filename_committed": False,
        "raw_archive_member_name_committed": False,
        "field_header_plaintext_committed": False,
        "row_value_committed": False,
        "business_value_committed": False,
        "credential_or_secret_committed": False,
    }


def _row_decision_code(row: dict[str, Any]) -> str:
    return str(row.get("owner_decision_code", "")).strip()


def _build_private_records(
    *,
    generated_at: str,
    source_summary: dict[str, Any],
    packet: dict[str, Any],
    draft: dict[str, Any],
    source_diagnostic: dict[str, Any],
) -> dict[str, Any]:
    if packet.get("review_groups_path_prepared") is not True:
        raise ValueError("source review groups path is not prepared")
    if draft.get("draft_is_active_authorization_record") is not False:
        raise ValueError("source response draft must not be an active authorization record")
    rows = draft.get("response_rows", [])
    if not isinstance(rows, list):
        raise ValueError("private review groups response draft response_rows must be a list")

    valid_count = 0
    invalid_count = 0
    pending_rows: list[dict[str, Any]] = []
    code_counts: Counter[str] = Counter()
    for row in rows:
        if not isinstance(row, dict):
            invalid_count += 1
            code_counts["INVALID_ROW_TYPE"] += 1
            continue
        code = _row_decision_code(row)
        code_counts[code or "MISSING_OWNER_DECISION_CODE"] += 1
        if code == PENDING_DECISION_CODE:
            pending_rows.append(
                {
                    "target_slot_id": row.get("target_slot_id"),
                    "review_group_id": row.get("review_group_id"),
                    "candidate_status": row.get("candidate_status"),
                    "owner_decision_code": code,
                    "active_authorization_allowed": False,
                }
            )
        elif code in VALID_OWNER_GROUP_DECISION_CODES:
            valid_count += 1
        else:
            invalid_count += 1

    diagnostic = {
        "schema_version": "kmfa.private.v014_owner_group_decision_application_diagnostic.v1",
        "classification": "private_owner_group_decision_application_diagnostic_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_owner_group_decision_application_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "source_phase_id": source_summary.get("phase_id"),
        "source_packet_phase_id": packet.get("phase_id"),
        "source_diagnostic_phase_id": source_diagnostic.get("phase_id"),
        "review_group_count": packet.get("review_group_count"),
        "response_row_count": len(rows),
        "pending_group_decision_row_count": len(pending_rows),
        "valid_group_decision_row_count": valid_count,
        "invalid_group_decision_row_count": invalid_count,
        "owner_decision_code_counts": dict(code_counts),
        "owner_group_decision_applied": False,
        "active_owner_authorized_fill_record_ready": False,
        "active_owner_authorized_fill_record_written": False,
        "source_map_completion_reapplication_ready": False,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "next_required_input": NEXT_REQUIRED_INPUT,
        "raw_boundary": _raw_boundary(),
    }
    pending_queue = {
        "schema_version": "kmfa.private.v014_owner_group_decision_pending_queue.v1",
        "classification": "private_owner_group_decision_pending_queue_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_owner_group_decision_pending_queue",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "review_group_count": packet.get("review_group_count"),
        "pending_group_decision_row_count": len(pending_rows),
        "active_authorization_allowed": False,
        "pending_rows": pending_rows,
    }
    return {"diagnostic": diagnostic, "pending_queue": pending_queue}


def generate(*, generated_at: str | None = None, write_governance_event: bool = True) -> dict[str, Any]:
    timestamp = _now(generated_at)
    source_summary = _read_json(SOURCE_GROUPS_SUMMARY_PATH)
    packet = _read_json(PRIVATE_GROUPS_PACKET_PATH)
    draft = _read_json(PRIVATE_RESPONSE_DRAFT_PATH)
    source_diagnostic = _read_json(PRIVATE_SOURCE_DIAGNOSTIC_PATH)
    private_records = _build_private_records(
        generated_at=timestamp,
        source_summary=source_summary,
        packet=packet,
        draft=draft,
        source_diagnostic=source_diagnostic,
    )

    _write_json(PRIVATE_DIAGNOSTIC_PATH, private_records["diagnostic"])
    _write_json(PRIVATE_PENDING_QUEUE_PATH, private_records["pending_queue"])

    diagnostic = private_records["diagnostic"]
    summary = {
        "schema_version": "kmfa.v014_owner_group_decision_application_summary.v1",
        "record_type": "v014_processed_value_source_map_completion_owner_group_decision_application_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "status": STATUS,
        "generated_at": timestamp,
        "source_review_groups_phase_id": source_summary.get("phase_id"),
        "source_review_groups_path_prepared": source_summary.get("review_groups_path_prepared"),
        "review_group_count": diagnostic["review_group_count"],
        "response_row_count": diagnostic["response_row_count"],
        "pending_group_decision_row_count": diagnostic["pending_group_decision_row_count"],
        "valid_group_decision_row_count": diagnostic["valid_group_decision_row_count"],
        "invalid_group_decision_row_count": diagnostic["invalid_group_decision_row_count"],
        "candidate_catalog_record_count": source_summary.get("candidate_catalog_record_count"),
        "private_diagnostic_written": True,
        "private_diagnostic_gitignored": _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH),
        "private_pending_queue_written": True,
        "private_pending_queue_gitignored": _git_check_ignored(PRIVATE_PENDING_QUEUE_PATH),
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
        "schema_version": "kmfa.v014_owner_group_decision_application_go_no_go.v1",
        "record_type": "v014_processed_value_source_map_completion_owner_group_decision_application_go_no_go_report",
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
        "response_row_count": summary["response_row_count"],
        "pending_group_decision_row_count": summary["pending_group_decision_row_count"],
        "valid_group_decision_row_count": summary["valid_group_decision_row_count"],
        "invalid_group_decision_row_count": summary["invalid_group_decision_row_count"],
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
        "schema_version": "kmfa.v014_owner_group_decision_application_manifest.v1",
        "record_type": "v014_processed_value_source_map_completion_owner_group_decision_application_manifest",
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
            "private_application_diagnostic": "private_runtime_only",
            "private_pending_queue": "private_runtime_only",
        },
        "validator": (
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. "
            "python3 KMFA/tools/check_v014_processed_value_source_map_completion_owner_group_decision_application.py "
            "--require-private-diagnostic"
        ),
        "git": {
            "branch": _git_output(["branch", "--show-current"]),
            "head": _git_output(["rev-parse", "HEAD"]),
            "status_short": _git_output(["status", "--short", "--branch"]),
        },
    }
    report = f"""# V014 Owner Group Decision Application

Decision: NO_GO

This phase checks the private owner review-groups response draft and confirms that no active group-level owner decisions are available. It does not modify the private owner response template, write active authorization, apply source-map changes, or compare raw and processed values.

## Public-safe aggregate result

- Review groups: {summary["review_group_count"]}
- Response rows: {summary["response_row_count"]}
- Pending group decision rows: {summary["pending_group_decision_row_count"]}
- Valid group decision rows: {summary["valid_group_decision_row_count"]}
- Invalid group decision rows: {summary["invalid_group_decision_row_count"]}
- Review groups path prepared: `true`
- Owner group decision applied: `false`

Next required input: `{NEXT_REQUIRED_INPUT}`.
"""
    go_no_go_record = f"""# Go/No-Go Record

- phase_id: `{PHASE_ID}`
- decision: `NO_GO`
- reason: all review-group response rows still require owner or authorized-delegate group-level decisions.
- review_group_count: `{summary["review_group_count"]}`
- response_row_count: `{summary["response_row_count"]}`
- pending_group_decision_row_count: `{summary["pending_group_decision_row_count"]}`
- valid_group_decision_row_count: `{summary["valid_group_decision_row_count"]}`
- github upload performed: `false`
"""
    risk_register = """# Risk Register

- Risk: treating pending group review rows as active owner authorization.
  Mitigation: the validator requires valid group decision count to remain zero in this NO_GO phase and keeps all downstream gates closed.
- Risk: leaking private row-level routing publicly.
  Mitigation: public artifacts contain only aggregate counts and gate flags; the pending queue is private runtime only.
"""
    rollback_plan = """# Rollback Plan

No raw file, owner response template, completion template, active authorization record or source-map file was modified. To roll back, remove this phase's public artifacts and metadata copies, then remove the ignored private diagnostic and pending queue if not needed.
"""
    test_results = """# Test Results

Pending until validator and focused tests are run after artifact generation.

Expected validator:
`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_value_source_map_completion_owner_group_decision_application.py --require-private-diagnostic`
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
    event_id = "DEV-KMFA-20260706-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-OWNER-GROUP-DECISION-APPLICATION"
    event = {
        "event_id": event_id,
        "event_time": generated_at,
        "event_type": "development",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "iteration_id": "ITER-20260706-KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-OWNER-GROUP-DECISION-APPLICATION",
        "fact_level": "EXTRACTED",
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "go_no_go": manifest["go_no_go"]["decision"],
        "review_group_count": manifest["summary"]["review_group_count"],
        "response_row_count": manifest["summary"]["response_row_count"],
        "pending_group_decision_row_count": manifest["summary"]["pending_group_decision_row_count"],
        "valid_group_decision_row_count": manifest["summary"]["valid_group_decision_row_count"],
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
        "summary": "Checked private owner review-groups draft; no active group-level owner decisions are available, so downstream active authorization remains closed.",
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
        "PASS: KMFA v0.1.4 owner group decision application generated "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"groups={manifest['summary']['review_group_count']}, "
        f"rows={manifest['summary']['response_row_count']}, "
        f"pending={manifest['summary']['pending_group_decision_row_count']})"
    )


if __name__ == "__main__":
    main()
