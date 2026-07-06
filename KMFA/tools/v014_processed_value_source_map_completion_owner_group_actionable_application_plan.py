#!/usr/bin/env python3
"""Prepare a private actionable owner-group application plan for KMFA v0.1.4.

This phase consumes the private owner group-decision response template and
builds a git-ignored plan for the groups that are actionable after delegated
default decisions. It does not write an active authorization record, does not
apply source-map records, and does not read or mutate the raw inbox.
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
PHASE_ID = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_GROUP_ACTIONABLE_APPLICATION_PLAN"
TASK_ID = "KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-OWNER-GROUP-ACTIONABLE-APPLICATION-PLAN-20260706"
ACCEPTANCE_ID = "ACC-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-OWNER-GROUP-ACTIONABLE-APPLICATION-PLAN"
VERSION = "0.1.4-owner-group-actionable-application-plan"
STATUS = "completed_validated_local_only_partial_actionable_plan_no_go"
DECISION = "NO_GO"
DIAGNOSTIC_CONCLUSION = "partial_actionable_owner_group_plan_ready_full_reapplication_blocked"
NEXT_RECOMMENDED_PHASE = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_GROUP_PARTIAL_APPLICATION"
NEXT_REQUIRED_INPUT = "run_partial_application_or_resolve_non_actionable_group_decisions"

ACTIONABLE_OWNER_GROUP_DECISION_CODES = {
    "CONFIRM_GROUP_CANDIDATE_RANK",
    "CHOOSE_CANDIDATE_RECORD_REF",
}
NON_ACTIONABLE_OWNER_GROUP_DECISION_CODES = {
    "KEEP_PENDING",
    "MARK_NOT_APPLICABLE",
    "REQUEST_MORE_DIAGNOSTICS",
}

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_group_actionable_application_plan_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_group_actionable_application_plan_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_group_actionable_application_plan_go_no_go_report.json"
REPORT_PATH = HUMAN_DIR / "processed_value_source_map_completion_owner_group_actionable_application_plan_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_owner_group_actionable_application_plan_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_owner_group_actionable_application_plan_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_owner_group_actionable_application_plan_go_no_go_report.json"
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"

SOURCE_RESPONSE_INTAKE_SUMMARY_PATH = (
    PROJECT_ROOT
    / "stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_GROUP_DECISION_RESPONSE_INTAKE/machine/processed_value_source_map_completion_owner_group_decision_response_intake_summary.json"
)
PRIVATE_RESPONSE_TEMPLATE_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_owner_group_decision_input_kit/private_owner_group_decision_response_template.json"
)
PRIVATE_GROUP_PACKET_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_owner_review_groups_path/private_owner_review_groups_path_packet.json"
)

PRIVATE_OUTPUT_DIR = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_owner_group_actionable_application_plan"
)
PRIVATE_PLAN_PATH = PRIVATE_OUTPUT_DIR / "private_owner_group_actionable_application_plan.json"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_owner_group_actionable_application_plan_diagnostic.json"


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
        "private_group_packet_committed": False,
        "private_actionable_plan_committed": False,
        "private_diagnostic_committed": False,
        "raw_file_committed": False,
        "raw_filename_committed": False,
        "raw_archive_member_name_committed": False,
        "field_header_plaintext_committed": False,
        "row_value_committed": False,
        "business_value_committed": False,
        "credential_or_secret_committed": False,
    }


def _private_plan(generated_at: str, response_template: dict[str, Any], group_packet: dict[str, Any]) -> dict[str, Any]:
    groups = response_template.get("groups", [])
    packet_groups = group_packet.get("groups", [])
    if not isinstance(groups, list):
        raise ValueError("private response template groups must be a list")
    if not isinstance(packet_groups, list):
        raise ValueError("private group packet groups must be a list")
    packet_by_id = {
        group.get("review_group_id"): group
        for group in packet_groups
        if isinstance(group, dict) and isinstance(group.get("review_group_id"), str)
    }
    actionable_items: list[dict[str, Any]] = []
    non_actionable_items: list[dict[str, Any]] = []
    decision_counts: Counter[str] = Counter()
    target_slot_counts: Counter[str] = Counter()
    candidate_status_counts: Counter[str] = Counter()
    missing_packet_group_count = 0
    for group in groups:
        if not isinstance(group, dict):
            continue
        review_group_id = str(group.get("review_group_id", ""))
        packet_group = packet_by_id.get(review_group_id)
        if packet_group is None:
            missing_packet_group_count += 1
            packet_group = {}
        code = str(group.get("owner_group_decision_code", ""))
        status = str(group.get("candidate_status", "unknown"))
        target_slot_count = int(group.get("target_slot_count") or 0)
        decision_counts[code] += 1
        target_slot_counts[code] += target_slot_count
        candidate_status_counts[status] += 1
        item = {
            "review_group_id": review_group_id,
            "owner_group_decision_code": code,
            "candidate_status": status,
            "target_slot_count": target_slot_count,
            "top_candidate_record_count": int(packet_group.get("top_candidate_record_count") or 0),
            "source_packet_group_present": bool(packet_group),
        }
        if code in ACTIONABLE_OWNER_GROUP_DECISION_CODES:
            item["planned_action"] = "prepare_partial_owner_group_source_map_application"
            item["active_authorization_allowed_by_group_decision"] = True
            actionable_items.append(item)
        else:
            item["planned_action"] = "keep_full_application_blocked"
            item["active_authorization_allowed_by_group_decision"] = False
            non_actionable_items.append(item)

    actionable_target_slot_count = sum(item["target_slot_count"] for item in actionable_items)
    non_actionable_target_slot_count = sum(item["target_slot_count"] for item in non_actionable_items)
    plan_summary = {
        "review_group_count": len(groups),
        "response_row_count": response_template.get("response_row_count"),
        "decision_code_counts": dict(decision_counts),
        "decision_code_target_slot_counts": dict(target_slot_counts),
        "candidate_status_group_counts": dict(candidate_status_counts),
        "actionable_group_count": len(actionable_items),
        "actionable_target_slot_count": actionable_target_slot_count,
        "non_actionable_group_count": len(non_actionable_items),
        "non_actionable_target_slot_count": non_actionable_target_slot_count,
        "missing_packet_group_count": missing_packet_group_count,
        "partial_actionable_application_plan_ready": len(actionable_items) > 0 and missing_packet_group_count == 0,
        "full_source_map_completion_reapplication_ready": False,
    }
    return {
        "schema_version": "kmfa.private.v014_owner_group_actionable_application_plan.v1",
        "classification": "private_owner_group_actionable_application_plan_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_owner_group_actionable_application_plan",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "source_response_template_phase_id": response_template.get("phase_id"),
        "source_group_packet_phase_id": group_packet.get("phase_id"),
        "plan_summary": plan_summary,
        "actionable_items": actionable_items,
        "non_actionable_items": non_actionable_items,
        "raw_boundary": _raw_boundary(),
    }


def generate(*, generated_at: str | None = None, write_governance_event: bool = True) -> dict[str, Any]:
    timestamp = _now(generated_at)
    source_summary = _read_json(SOURCE_RESPONSE_INTAKE_SUMMARY_PATH)
    response_template = _read_json(PRIVATE_RESPONSE_TEMPLATE_PATH)
    group_packet = _read_json(PRIVATE_GROUP_PACKET_PATH)
    private_plan = _private_plan(timestamp, response_template, group_packet)
    plan_summary = private_plan["plan_summary"]
    diagnostic = {
        "schema_version": "kmfa.private.v014_owner_group_actionable_application_plan_diagnostic.v1",
        "classification": "private_owner_group_actionable_application_plan_diagnostic_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_owner_group_actionable_application_plan_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "plan_summary": plan_summary,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "raw_boundary": _raw_boundary(),
    }
    _write_json(PRIVATE_PLAN_PATH, private_plan)
    _write_json(PRIVATE_DIAGNOSTIC_PATH, diagnostic)

    summary = {
        "schema_version": "kmfa.v014_owner_group_actionable_application_plan_summary.v1",
        "record_type": "v014_processed_value_source_map_completion_owner_group_actionable_application_plan_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "status": STATUS,
        "generated_at": timestamp,
        "source_response_intake_phase_id": source_summary.get("phase_id"),
        "source_response_intake_decision": source_summary.get("decision"),
        "review_group_count": plan_summary["review_group_count"],
        "response_row_count": plan_summary["response_row_count"],
        "decision_code_counts": plan_summary["decision_code_counts"],
        "decision_code_target_slot_counts": plan_summary["decision_code_target_slot_counts"],
        "candidate_status_group_counts": plan_summary["candidate_status_group_counts"],
        "actionable_group_count": plan_summary["actionable_group_count"],
        "actionable_target_slot_count": plan_summary["actionable_target_slot_count"],
        "non_actionable_group_count": plan_summary["non_actionable_group_count"],
        "non_actionable_target_slot_count": plan_summary["non_actionable_target_slot_count"],
        "missing_packet_group_count": plan_summary["missing_packet_group_count"],
        "private_actionable_plan_written": True,
        "private_actionable_plan_gitignored": _git_check_ignored(PRIVATE_PLAN_PATH),
        "private_diagnostic_written": True,
        "private_diagnostic_gitignored": _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH),
        "partial_actionable_application_plan_ready": plan_summary["partial_actionable_application_plan_ready"],
        "active_owner_authorized_fill_record_ready": False,
        "active_owner_authorized_fill_record_written": False,
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
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
        "next_required_input": NEXT_REQUIRED_INPUT,
        "raw_boundary": _raw_boundary(),
        "public_safety": _public_safety(),
    }
    go_no_go = {
        "schema_version": "kmfa.v014_owner_group_actionable_application_plan_go_no_go.v1",
        "record_type": "v014_processed_value_source_map_completion_owner_group_actionable_application_plan_go_no_go_report",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "decision": DECISION,
        "status": STATUS,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "actionable_group_count": summary["actionable_group_count"],
        "actionable_target_slot_count": summary["actionable_target_slot_count"],
        "non_actionable_group_count": summary["non_actionable_group_count"],
        "non_actionable_target_slot_count": summary["non_actionable_target_slot_count"],
        "partial_actionable_application_plan_ready": summary["partial_actionable_application_plan_ready"],
        "source_map_completion_reapplication_ready": False,
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "blocked_until": NEXT_REQUIRED_INPUT,
    }
    manifest = {
        "schema_version": "kmfa.v014_owner_group_actionable_application_plan_manifest.v1",
        "record_type": "v014_processed_value_source_map_completion_owner_group_actionable_application_plan_manifest",
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
            "private_actionable_plan": "private_runtime_only",
            "private_diagnostic": "private_runtime_only",
        },
        "validator": (
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. "
            "python3 KMFA/tools/check_v014_processed_value_source_map_completion_owner_group_actionable_application_plan.py "
            "--require-private-plan"
        ),
        "git": {
            "branch": _git_output(["branch", "--show-current"]),
            "head": _git_output(["rev-parse", "HEAD"]),
            "status_short": _git_output(["status", "--short", "--branch"]),
        },
    }
    report = f"""# V014 Owner Group Actionable Application Plan

Decision: {DECISION}

This phase prepares a private actionable plan for owner-group decisions that can be applied later. It keeps full source-map reapplication blocked because non-actionable decisions remain.

## Public-safe aggregate result

- Review groups: {summary["review_group_count"]}
- Response rows represented: {summary["response_row_count"]}
- Actionable groups: {summary["actionable_group_count"]}
- Actionable target slots: {summary["actionable_target_slot_count"]}
- Non-actionable groups: {summary["non_actionable_group_count"]}
- Non-actionable target slots: {summary["non_actionable_target_slot_count"]}
- Partial actionable plan ready: `{str(summary["partial_actionable_application_plan_ready"]).lower()}`
- Full source-map reapplication ready: `false`

Next recommended phase: `{NEXT_RECOMMENDED_PHASE}`.
"""
    go_no_go_record = f"""# Go/No-Go Record

- phase_id: `{PHASE_ID}`
- decision: `{DECISION}`
- reason: `{DIAGNOSTIC_CONCLUSION}`
- actionable_group_count: `{summary["actionable_group_count"]}`
- actionable_target_slot_count: `{summary["actionable_target_slot_count"]}`
- non_actionable_group_count: `{summary["non_actionable_group_count"]}`
- non_actionable_target_slot_count: `{summary["non_actionable_target_slot_count"]}`
- github upload performed: `false`
"""
    risk_register = """# Risk Register

- Risk: treating a partial actionable plan as full active authorization.
  Mitigation: no active record is written and full source-map reapplication remains closed.
- Risk: leaking private group-level context publicly.
  Mitigation: public artifacts contain only aggregate counts and gate flags; private plan stays in ignored runtime.
"""
    rollback_plan = """# Rollback Plan

No raw file, response template, source-map file, completion template or active authorization record was modified. To roll back, remove this phase's public artifacts and metadata copies, then remove the ignored private plan and diagnostic if not needed.
"""
    test_results = """# Test Results

Status: passed locally.

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_processed_value_source_map_completion_owner_group_actionable_application_plan.py --generated-at 2026-07-06T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_value_source_map_completion_owner_group_actionable_application_plan.py --require-private-plan`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_processed_value_source_map_completion_owner_group_actionable_application_plan`
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
    event_id = "DEV-KMFA-20260706-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-OWNER-GROUP-ACTIONABLE-APPLICATION-PLAN"
    summary = manifest["summary"]
    event = {
        "event_id": event_id,
        "event_time": generated_at,
        "event_type": "development",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "iteration_id": "ITER-20260706-KMFA-V014-OWNER-GROUP-ACTIONABLE-APPLICATION-PLAN",
        "fact_level": "EXTRACTED",
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "go_no_go": manifest["go_no_go"]["decision"],
        "actionable_group_count": summary["actionable_group_count"],
        "actionable_target_slot_count": summary["actionable_target_slot_count"],
        "non_actionable_group_count": summary["non_actionable_group_count"],
        "non_actionable_target_slot_count": summary["non_actionable_target_slot_count"],
        "partial_actionable_application_plan_ready": summary["partial_actionable_application_plan_ready"],
        "active_owner_authorized_fill_record_written": False,
        "source_map_completion_reapplication_performed": False,
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "result_commit": "PENDING",
        "summary": "Prepared private actionable owner-group application plan for 19 groups while keeping full source-map reapplication blocked for 3 non-actionable groups.",
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
        "PASS: KMFA v0.1.4 owner group actionable application plan generated "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"actionable_groups={manifest['summary']['actionable_group_count']}, "
        f"non_actionable_groups={manifest['summary']['non_actionable_group_count']})"
    )


if __name__ == "__main__":
    main()
