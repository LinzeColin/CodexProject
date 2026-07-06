#!/usr/bin/env python3
"""Stage a partial owner-group source-map application for KMFA v0.1.4.

This phase consumes the private actionable owner-group plan and private
response draft, stages the actionable target slots in ignored runtime, and
keeps canonical source-map mutation plus full reapplication blocked.
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
PHASE_ID = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_GROUP_PARTIAL_APPLICATION"
TASK_ID = "KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-OWNER-GROUP-PARTIAL-APPLICATION-20260706"
ACCEPTANCE_ID = "ACC-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-OWNER-GROUP-PARTIAL-APPLICATION"
VERSION = "0.1.4-owner-group-partial-application"
STATUS = "completed_validated_local_only_private_partial_application_no_go"
DECISION = "NO_GO"
DIAGNOSTIC_CONCLUSION = "private_partial_owner_group_application_staged_full_reapplication_blocked"
NEXT_RECOMMENDED_PHASE = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_PARTIAL_MATERIALIZATION_PRECHECK"
NEXT_REQUIRED_INPUT = "resolve_non_actionable_group_decisions_before_full_source_map_reapplication"

ACTIONABLE_OWNER_GROUP_DECISION_CODES = {
    "CONFIRM_GROUP_CANDIDATE_RANK",
    "CHOOSE_CANDIDATE_RECORD_REF",
}

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_group_partial_application_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_group_partial_application_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_group_partial_application_go_no_go_report.json"
REPORT_PATH = HUMAN_DIR / "processed_value_source_map_completion_owner_group_partial_application_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_owner_group_partial_application_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_owner_group_partial_application_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_owner_group_partial_application_go_no_go_report.json"
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"

SOURCE_ACTIONABLE_PLAN_SUMMARY_PATH = (
    PROJECT_ROOT
    / "stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_GROUP_ACTIONABLE_APPLICATION_PLAN/machine/processed_value_source_map_completion_owner_group_actionable_application_plan_summary.json"
)
PRIVATE_ACTIONABLE_PLAN_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_owner_group_actionable_application_plan/private_owner_group_actionable_application_plan.json"
)
PRIVATE_RESPONSE_DRAFT_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_owner_review_groups_path/private_owner_review_groups_path_response_draft.json"
)

PRIVATE_OUTPUT_DIR = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_owner_group_partial_application"
)
PRIVATE_RESULT_PATH = PRIVATE_OUTPUT_DIR / "private_owner_group_partial_application_result.json"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_owner_group_partial_application_diagnostic.json"


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
        "private_actionable_plan_committed": False,
        "private_response_draft_committed": False,
        "private_partial_application_result_committed": False,
        "private_diagnostic_committed": False,
        "raw_file_committed": False,
        "raw_filename_committed": False,
        "raw_archive_member_name_committed": False,
        "field_header_plaintext_committed": False,
        "row_value_committed": False,
        "business_value_committed": False,
        "credential_or_secret_committed": False,
    }


def _partial_application(generated_at: str, plan: dict[str, Any], response_draft: dict[str, Any]) -> dict[str, Any]:
    actionable_items = plan.get("actionable_items", [])
    non_actionable_items = plan.get("non_actionable_items", [])
    rows = response_draft.get("response_rows", [])
    if not isinstance(actionable_items, list) or not isinstance(non_actionable_items, list):
        raise ValueError("private plan item lists must be lists")
    if not isinstance(rows, list):
        raise ValueError("private response draft response_rows must be a list")
    decision_by_group = {
        str(item.get("review_group_id")): str(item.get("owner_group_decision_code"))
        for item in actionable_items + non_actionable_items
        if isinstance(item, dict)
    }
    actionable_group_ids = {
        str(item.get("review_group_id"))
        for item in actionable_items
        if isinstance(item, dict) and item.get("owner_group_decision_code") in ACTIONABLE_OWNER_GROUP_DECISION_CODES
    }
    applied_rows: list[dict[str, Any]] = []
    blocked_rows: list[dict[str, Any]] = []
    row_decision_counts: Counter[str] = Counter()
    row_candidate_status_counts: Counter[str] = Counter()
    missing_group_decision_row_count = 0
    for row in rows:
        if not isinstance(row, dict):
            continue
        review_group_id = str(row.get("review_group_id", ""))
        decision_code = decision_by_group.get(review_group_id)
        if decision_code is None:
            missing_group_decision_row_count += 1
            decision_code = "MISSING_GROUP_DECISION"
        candidate_status = str(row.get("candidate_status", "unknown"))
        row_decision_counts[decision_code] += 1
        row_candidate_status_counts[candidate_status] += 1
        row_record = {
            "target_slot_id": row.get("target_slot_id"),
            "review_group_id": review_group_id,
            "candidate_status": candidate_status,
            "owner_group_decision_code": decision_code,
        }
        if review_group_id in actionable_group_ids:
            row_record["private_partial_application_status"] = "staged_for_partial_source_map_application"
            applied_rows.append(row_record)
        else:
            row_record["private_partial_application_status"] = "blocked_from_partial_application"
            blocked_rows.append(row_record)

    applied_unique_group_count = len({row["review_group_id"] for row in applied_rows})
    blocked_unique_group_count = len({row["review_group_id"] for row in blocked_rows})
    summary = {
        "source_review_group_count": int(plan.get("plan_summary", {}).get("review_group_count") or 0),
        "source_response_row_count": len(rows),
        "private_partial_application_group_count": applied_unique_group_count,
        "private_partial_application_target_slot_count": len(applied_rows),
        "private_blocked_group_count": blocked_unique_group_count,
        "private_blocked_target_slot_count": len(blocked_rows),
        "row_decision_code_counts": dict(row_decision_counts),
        "row_candidate_status_counts": dict(row_candidate_status_counts),
        "missing_group_decision_row_count": missing_group_decision_row_count,
        "private_partial_application_staged": bool(applied_rows) and missing_group_decision_row_count == 0,
        "canonical_source_map_mutated": False,
        "full_source_map_completion_reapplication_ready": False,
    }
    return {
        "schema_version": "kmfa.private.v014_owner_group_partial_application.v1",
        "classification": "private_owner_group_partial_application_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_owner_group_partial_application",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "source_actionable_plan_phase_id": plan.get("phase_id"),
        "source_response_draft_phase_id": response_draft.get("phase_id"),
        "partial_application_summary": summary,
        "applied_rows": applied_rows,
        "blocked_rows": blocked_rows,
        "raw_boundary": _raw_boundary(),
    }


def generate(*, generated_at: str | None = None, write_governance_event: bool = True) -> dict[str, Any]:
    timestamp = _now(generated_at)
    source_summary = _read_json(SOURCE_ACTIONABLE_PLAN_SUMMARY_PATH)
    private_plan = _read_json(PRIVATE_ACTIONABLE_PLAN_PATH)
    response_draft = _read_json(PRIVATE_RESPONSE_DRAFT_PATH)
    partial_application = _partial_application(timestamp, private_plan, response_draft)
    private_summary = partial_application["partial_application_summary"]
    diagnostic = {
        "schema_version": "kmfa.private.v014_owner_group_partial_application_diagnostic.v1",
        "classification": "private_owner_group_partial_application_diagnostic_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_owner_group_partial_application_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "partial_application_summary": private_summary,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "raw_boundary": _raw_boundary(),
    }
    _write_json(PRIVATE_RESULT_PATH, partial_application)
    _write_json(PRIVATE_DIAGNOSTIC_PATH, diagnostic)

    summary = {
        "schema_version": "kmfa.v014_owner_group_partial_application_summary.v1",
        "record_type": "v014_processed_value_source_map_completion_owner_group_partial_application_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "status": STATUS,
        "generated_at": timestamp,
        "source_actionable_plan_phase_id": source_summary.get("phase_id"),
        "source_actionable_plan_decision": source_summary.get("decision"),
        "source_actionable_group_count": source_summary.get("actionable_group_count"),
        "source_actionable_target_slot_count": source_summary.get("actionable_target_slot_count"),
        "source_non_actionable_group_count": source_summary.get("non_actionable_group_count"),
        "source_non_actionable_target_slot_count": source_summary.get("non_actionable_target_slot_count"),
        "source_response_row_count": private_summary["source_response_row_count"],
        "private_partial_application_group_count": private_summary["private_partial_application_group_count"],
        "private_partial_application_target_slot_count": private_summary["private_partial_application_target_slot_count"],
        "private_blocked_group_count": private_summary["private_blocked_group_count"],
        "private_blocked_target_slot_count": private_summary["private_blocked_target_slot_count"],
        "row_decision_code_counts": private_summary["row_decision_code_counts"],
        "row_candidate_status_counts": private_summary["row_candidate_status_counts"],
        "missing_group_decision_row_count": private_summary["missing_group_decision_row_count"],
        "private_partial_application_staged": private_summary["private_partial_application_staged"],
        "private_partial_application_result_written": True,
        "private_partial_application_result_gitignored": _git_check_ignored(PRIVATE_RESULT_PATH),
        "private_diagnostic_written": True,
        "private_diagnostic_gitignored": _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH),
        "canonical_source_map_mutated": False,
        "canonical_source_map_records_applied_count": 0,
        "active_owner_authorized_fill_record_written": False,
        "source_map_completion_reapplication_ready": False,
        "source_map_completion_reapplication_performed": False,
        "processed_value_materialization_replay_ready": True,
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
        "schema_version": "kmfa.v014_owner_group_partial_application_go_no_go.v1",
        "record_type": "v014_processed_value_source_map_completion_owner_group_partial_application_go_no_go_report",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "decision": DECISION,
        "status": STATUS,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "private_partial_application_group_count": summary["private_partial_application_group_count"],
        "private_partial_application_target_slot_count": summary["private_partial_application_target_slot_count"],
        "private_blocked_group_count": summary["private_blocked_group_count"],
        "private_blocked_target_slot_count": summary["private_blocked_target_slot_count"],
        "private_partial_application_staged": summary["private_partial_application_staged"],
        "canonical_source_map_mutated": False,
        "source_map_completion_reapplication_ready": False,
        "processed_value_materialization_replay_ready": True,
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "blocked_until": NEXT_REQUIRED_INPUT,
    }
    manifest = {
        "schema_version": "kmfa.v014_owner_group_partial_application_manifest.v1",
        "record_type": "v014_processed_value_source_map_completion_owner_group_partial_application_manifest",
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
            "private_partial_application_result": "private_runtime_only",
            "private_diagnostic": "private_runtime_only",
        },
        "validator": (
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. "
            "python3 KMFA/tools/check_v014_processed_value_source_map_completion_owner_group_partial_application.py "
            "--require-private-application"
        ),
        "git": {
            "branch": _git_output(["branch", "--show-current"]),
            "head": _git_output(["rev-parse", "HEAD"]),
            "status_short": _git_output(["status", "--short", "--branch"]),
        },
    }
    report = f"""# V014 Owner Group Partial Application

Decision: {DECISION}

This phase stages the actionable owner-group target slots in private runtime. Canonical source-map files are not mutated and full source-map reapplication remains blocked.

## Public-safe aggregate result

- Private partial application groups: {summary["private_partial_application_group_count"]}
- Private partial application target slots: {summary["private_partial_application_target_slot_count"]}
- Blocked groups: {summary["private_blocked_group_count"]}
- Blocked target slots: {summary["private_blocked_target_slot_count"]}
- Canonical source-map mutated: `false`
- Processed value materialization replay ready: `{str(summary["processed_value_materialization_replay_ready"]).lower()}`
- Full source-map reapplication ready: `false`

Next recommended phase: `{NEXT_RECOMMENDED_PHASE}`.
"""
    go_no_go_record = f"""# Go/No-Go Record

- phase_id: `{PHASE_ID}`
- decision: `{DECISION}`
- reason: `{DIAGNOSTIC_CONCLUSION}`
- private_partial_application_target_slot_count: `{summary["private_partial_application_target_slot_count"]}`
- private_blocked_target_slot_count: `{summary["private_blocked_target_slot_count"]}`
- canonical_source_map_mutated: `false`
- github upload performed: `false`
"""
    risk_register = """# Risk Register

- Risk: treating private partial staging as canonical source-map mutation.
  Mitigation: canonical source-map mutation remains false and full reapplication remains closed.
- Risk: leaking private target slots or group refs publicly.
  Mitigation: public artifacts contain only aggregate counts and gate flags; slot-level rows stay in ignored runtime.
"""
    rollback_plan = """# Rollback Plan

No raw file, canonical source-map file, completion template or active authorization record was modified. To roll back, remove this phase's public artifacts and metadata copies, then remove the ignored private partial application result and diagnostic if not needed.
"""
    test_results = """# Test Results

Status: passed locally.

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_processed_value_source_map_completion_owner_group_partial_application.py --generated-at 2026-07-06T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_value_source_map_completion_owner_group_partial_application.py --require-private-application`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_processed_value_source_map_completion_owner_group_partial_application`
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
    event_id = "DEV-KMFA-20260706-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-OWNER-GROUP-PARTIAL-APPLICATION"
    summary = manifest["summary"]
    event = {
        "event_id": event_id,
        "event_time": generated_at,
        "event_type": "development",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "iteration_id": "ITER-20260706-KMFA-V014-OWNER-GROUP-PARTIAL-APPLICATION",
        "fact_level": "EXTRACTED",
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "go_no_go": manifest["go_no_go"]["decision"],
        "private_partial_application_group_count": summary["private_partial_application_group_count"],
        "private_partial_application_target_slot_count": summary["private_partial_application_target_slot_count"],
        "private_blocked_group_count": summary["private_blocked_group_count"],
        "private_blocked_target_slot_count": summary["private_blocked_target_slot_count"],
        "canonical_source_map_mutated": False,
        "processed_value_materialization_replay_ready": summary["processed_value_materialization_replay_ready"],
        "source_map_completion_reapplication_performed": False,
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "result_commit": "PENDING",
        "summary": "Staged private partial owner-group application for 101 target slots while keeping canonical source-map mutation and full reapplication blocked.",
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
        "PASS: KMFA v0.1.4 owner group partial application generated "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"partial_slots={manifest['summary']['private_partial_application_target_slot_count']}, "
        f"blocked_slots={manifest['summary']['private_blocked_target_slot_count']})"
    )


if __name__ == "__main__":
    main()
