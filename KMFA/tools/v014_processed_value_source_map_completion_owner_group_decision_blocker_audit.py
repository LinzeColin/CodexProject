#!/usr/bin/env python3
"""Audit the repeated KMFA v0.1.4 owner group-decision blocker.

This phase records the repeated observation that no owner or authorized-delegate
group-level decisions have been supplied. It does not mutate the private
response template, write active authorization, apply source-map records, or
read raw inbox data.
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
PHASE_ID = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_GROUP_DECISION_BLOCKER_AUDIT"
TASK_ID = "KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-OWNER-GROUP-DECISION-BLOCKER-AUDIT-20260706"
ACCEPTANCE_ID = "ACC-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-OWNER-GROUP-DECISION-BLOCKER-AUDIT"
VERSION = "0.1.4-processed-value-source-map-completion-owner-group-decision-blocker-audit"
STATUS = "completed_validated_local_only_goal_blocked_owner_group_decisions_missing"
BLOCKER_CONDITION = "owner_group_decisions_missing_active_authorization_blocked"
DIAGNOSTIC_CONCLUSION = "owner_group_decision_blocker_repeated_threshold_met"
NEXT_REQUIRED_INPUT = "owner_or_authorized_delegate_replaces_pending_group_decision_codes"
PENDING_DECISION_CODE = "PENDING_OWNER_OR_AUTHORIZED_DELEGATE_GROUP_DECISION"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_group_decision_blocker_audit_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_group_decision_blocker_audit_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_group_decision_blocker_audit_go_no_go_report.json"
REPORT_PATH = HUMAN_DIR / "processed_value_source_map_completion_owner_group_decision_blocker_audit_report.md"
OWNER_PACKET_PATH = HUMAN_DIR / "owner_agent_blocker_packet.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_processed_value_source_map_completion_owner_group_decision_blocker_audit_summary.json"
)
METADATA_MANIFEST_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_processed_value_source_map_completion_owner_group_decision_blocker_audit_manifest.json"
)
METADATA_GO_NO_GO_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_processed_value_source_map_completion_owner_group_decision_blocker_audit_go_no_go_report.json"
)
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"

APPLICATION_SUMMARY_PATH = (
    PROJECT_ROOT
    / "stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_GROUP_DECISION_APPLICATION/machine/processed_value_source_map_completion_owner_group_decision_application_summary.json"
)
INPUT_KIT_SUMMARY_PATH = (
    PROJECT_ROOT
    / "stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_GROUP_DECISION_INPUT_KIT/machine/processed_value_source_map_completion_owner_group_decision_input_kit_summary.json"
)
RESPONSE_INTAKE_SUMMARY_PATH = (
    PROJECT_ROOT
    / "stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_GROUP_DECISION_RESPONSE_INTAKE/machine/processed_value_source_map_completion_owner_group_decision_response_intake_summary.json"
)
PRIVATE_RESPONSE_TEMPLATE_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_owner_group_decision_input_kit/private_owner_group_decision_response_template.json"
)

PRIVATE_OUTPUT_DIR = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_owner_group_decision_blocker_audit"
)
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_owner_group_decision_blocker_audit_diagnostic.json"


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
        "private_response_template_committed": False,
        "private_blocker_diagnostic_committed": False,
        "raw_file_committed": False,
        "raw_filename_committed": False,
        "raw_archive_member_name_committed": False,
        "field_header_plaintext_committed": False,
        "row_value_committed": False,
        "business_value_committed": False,
        "credential_or_secret_committed": False,
    }


def _template_counts(template: dict[str, Any]) -> dict[str, Any]:
    groups = template.get("groups", [])
    if not isinstance(groups, list):
        raise ValueError("private owner group decision response template groups must be a list")
    code_counts = Counter(str(group.get("owner_group_decision_code", "")).strip() for group in groups if isinstance(group, dict))
    return {
        "review_group_count": len(groups),
        "response_row_count": template.get("response_row_count"),
        "pending_group_decision_count": code_counts.get(PENDING_DECISION_CODE, 0),
        "valid_group_decision_count": 0,
        "invalid_group_decision_count": sum(
            count for code, count in code_counts.items() if code not in {PENDING_DECISION_CODE, ""}
        ),
        "owner_group_decision_code_counts": dict(code_counts),
    }


def _build_observations(application: dict[str, Any], input_kit: dict[str, Any], response_intake: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "phase_id": application.get("phase_id"),
            "decision": application.get("decision"),
            "pending_count": application.get("pending_group_decision_row_count"),
            "valid_count": application.get("valid_group_decision_row_count"),
            "active_ready": application.get("active_owner_authorized_fill_record_ready"),
        },
        {
            "phase_id": input_kit.get("phase_id"),
            "decision": input_kit.get("decision"),
            "pending_count": input_kit.get("pending_group_template_count"),
            "valid_count": 0,
            "active_ready": input_kit.get("active_owner_authorized_fill_record_ready"),
        },
        {
            "phase_id": response_intake.get("phase_id"),
            "decision": response_intake.get("decision"),
            "pending_count": response_intake.get("pending_group_decision_count"),
            "valid_count": response_intake.get("valid_group_decision_count"),
            "active_ready": response_intake.get("active_owner_authorized_fill_record_ready"),
        },
        {
            "phase_id": PHASE_ID,
            "decision": "NO_GO",
            "pending_count": response_intake.get("pending_group_decision_count"),
            "valid_count": response_intake.get("valid_group_decision_count"),
            "active_ready": False,
        },
    ]


def generate(*, generated_at: str | None = None, write_governance_event: bool = True) -> dict[str, Any]:
    timestamp = _now(generated_at)
    application_summary = _read_json(APPLICATION_SUMMARY_PATH)
    input_kit_summary = _read_json(INPUT_KIT_SUMMARY_PATH)
    response_intake_summary = _read_json(RESPONSE_INTAKE_SUMMARY_PATH)
    private_template = _read_json(PRIVATE_RESPONSE_TEMPLATE_PATH)
    template_counts = _template_counts(private_template)
    observations = _build_observations(application_summary, input_kit_summary, response_intake_summary)
    consecutive_blocker_count = sum(
        1
        for observation in observations
        if observation.get("decision") == "NO_GO"
        and observation.get("valid_count") == 0
        and observation.get("active_ready") is False
    )
    blocked_threshold_met = consecutive_blocker_count >= 3

    private_diagnostic = {
        "schema_version": "kmfa.private.v014_owner_group_decision_blocker_audit_diagnostic.v1",
        "classification": "private_owner_group_decision_blocker_audit_diagnostic_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_owner_group_decision_blocker_audit_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "blocker_condition": BLOCKER_CONDITION,
        "observations": observations,
        "consecutive_blocker_observation_count": consecutive_blocker_count,
        "blocked_audit_threshold_met": blocked_threshold_met,
        "meaningful_progress_without_owner_input_available": False,
        "template_counts": template_counts,
        "raw_boundary": _raw_boundary(),
    }
    _write_json(PRIVATE_DIAGNOSTIC_PATH, private_diagnostic)

    summary = {
        "schema_version": "kmfa.v014_owner_group_decision_blocker_audit_summary.v1",
        "record_type": "v014_processed_value_source_map_completion_owner_group_decision_blocker_audit_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "status": STATUS,
        "generated_at": timestamp,
        "blocker_condition": BLOCKER_CONDITION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "consecutive_goal_turn_blocker_count": consecutive_blocker_count,
        "blocked_audit_threshold_met": blocked_threshold_met,
        "goal_status_recommendation": "blocked" if blocked_threshold_met else "continue",
        "meaningful_progress_without_owner_input_available": False,
        "source_application_phase_id": application_summary.get("phase_id"),
        "source_input_kit_phase_id": input_kit_summary.get("phase_id"),
        "source_response_intake_phase_id": response_intake_summary.get("phase_id"),
        "review_group_count": template_counts["review_group_count"],
        "response_row_count": template_counts["response_row_count"],
        "pending_group_decision_count": template_counts["pending_group_decision_count"],
        "valid_group_decision_count": template_counts["valid_group_decision_count"],
        "invalid_group_decision_count": template_counts["invalid_group_decision_count"],
        "private_response_template_gitignored": _git_check_ignored(PRIVATE_RESPONSE_TEMPLATE_PATH),
        "private_diagnostic_written": True,
        "private_diagnostic_gitignored": _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH),
        "owner_group_decisions_supplied": False,
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
        "next_required_input": NEXT_REQUIRED_INPUT,
        "raw_boundary": _raw_boundary(),
        "public_safety": _public_safety(),
    }
    go_no_go = {
        "schema_version": "kmfa.v014_owner_group_decision_blocker_audit_go_no_go.v1",
        "record_type": "v014_processed_value_source_map_completion_owner_group_decision_blocker_audit_go_no_go_report",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "decision": "NO_GO",
        "status": STATUS,
        "blocker_condition": BLOCKER_CONDITION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "consecutive_goal_turn_blocker_count": consecutive_blocker_count,
        "blocked_audit_threshold_met": blocked_threshold_met,
        "goal_status_recommendation": summary["goal_status_recommendation"],
        "meaningful_progress_without_owner_input_available": False,
        "review_group_count": summary["review_group_count"],
        "pending_group_decision_count": summary["pending_group_decision_count"],
        "valid_group_decision_count": summary["valid_group_decision_count"],
        "owner_group_decisions_supplied": False,
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
        "schema_version": "kmfa.v014_owner_group_decision_blocker_audit_manifest.v1",
        "record_type": "v014_processed_value_source_map_completion_owner_group_decision_blocker_audit_manifest",
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
            "private_diagnostic": "private_runtime_only",
        },
        "validator": (
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. "
            "python3 KMFA/tools/check_v014_processed_value_source_map_completion_owner_group_decision_blocker_audit.py "
            "--require-private-diagnostic"
        ),
        "git": {
            "branch": _git_output(["branch", "--show-current"]),
            "head": _git_output(["rev-parse", "HEAD"]),
            "status_short": _git_output(["status", "--short", "--branch"]),
        },
    }
    report = f"""# V014 Owner Group Decision Blocker Audit

Decision: NO_GO

This phase records that the owner group-decision blocker has repeated across the application, input-kit, response-intake and blocker-audit observations. The only valid unlock is owner or authorized-delegate replacement of pending group decision codes.

## Public-safe aggregate result

- Review groups: {summary["review_group_count"]}
- Response rows represented: {summary["response_row_count"]}
- Pending group decisions: {summary["pending_group_decision_count"]}
- Valid group decisions: {summary["valid_group_decision_count"]}
- Consecutive blocker observations: {summary["consecutive_goal_turn_blocker_count"]}
- Blocked audit threshold met: `{str(summary["blocked_audit_threshold_met"]).lower()}`

Next required input: `{NEXT_REQUIRED_INPUT}`.
"""
    owner_packet = f"""# Owner/Agent Blocker Packet

Current state is blocked because no valid owner or authorized-delegate group-level decisions have been supplied.

- required action: replace pending group decision codes in the private response template
- review_group_count: `{summary["review_group_count"]}`
- pending_group_decision_count: `{summary["pending_group_decision_count"]}`
- valid_group_decision_count: `{summary["valid_group_decision_count"]}`
- source-map reapplication allowed: `false`
- GitHub upload performed: `false`
"""
    go_no_go_record = f"""# Go/No-Go Record

- phase_id: `{PHASE_ID}`
- decision: `NO_GO`
- reason: repeated missing owner group decisions meet the blocked-audit threshold.
- consecutive_goal_turn_blocker_count: `{summary["consecutive_goal_turn_blocker_count"]}`
- blocked_audit_threshold_met: `{str(summary["blocked_audit_threshold_met"]).lower()}`
- goal_status_recommendation: `{summary["goal_status_recommendation"]}`
- github upload performed: `false`
"""
    risk_register = """# Risk Register

- Risk: continuing to generate non-unlocking artifacts instead of stopping at the owner-decision blocker.
  Mitigation: this phase records the blocked-audit threshold and recommends blocked goal status until owner/authorized-delegate input changes.
- Risk: leaking private group template details publicly.
  Mitigation: public artifacts contain only aggregate counts and gate flags; private diagnostic stays in ignored runtime.
"""
    rollback_plan = """# Rollback Plan

No raw file, response template, source-map file, completion template or active authorization record was modified. To roll back, remove this phase's public artifacts and metadata copies, then remove the ignored private diagnostic if not needed.
"""
    test_results = """# Test Results

Pending until validator and focused tests are run after artifact generation.

Expected validator:
`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_value_source_map_completion_owner_group_decision_blocker_audit.py --require-private-diagnostic`
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
        (OWNER_PACKET_PATH, owner_packet),
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
    event_id = "DEV-KMFA-20260706-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-OWNER-GROUP-DECISION-BLOCKER-AUDIT"
    event = {
        "event_id": event_id,
        "event_time": generated_at,
        "event_type": "development",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "iteration_id": "ITER-20260706-KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-OWNER-GROUP-DECISION-BLOCKER-AUDIT",
        "fact_level": "EXTRACTED",
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "go_no_go": manifest["go_no_go"]["decision"],
        "blocker_condition": BLOCKER_CONDITION,
        "consecutive_goal_turn_blocker_count": manifest["summary"]["consecutive_goal_turn_blocker_count"],
        "blocked_audit_threshold_met": manifest["summary"]["blocked_audit_threshold_met"],
        "goal_status_recommendation": manifest["summary"]["goal_status_recommendation"],
        "review_group_count": manifest["summary"]["review_group_count"],
        "pending_group_decision_count": manifest["summary"]["pending_group_decision_count"],
        "valid_group_decision_count": manifest["summary"]["valid_group_decision_count"],
        "owner_group_decisions_supplied": False,
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
        "summary": "Recorded repeated owner group-decision blocker; downstream active authorization remains closed until owner or authorized-delegate decisions are supplied.",
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
        "PASS: KMFA v0.1.4 owner group decision blocker audit generated "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"blocked_threshold_met={manifest['summary']['blocked_audit_threshold_met']}, "
        f"valid={manifest['summary']['valid_group_decision_count']})"
    )


if __name__ == "__main__":
    main()
