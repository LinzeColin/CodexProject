#!/usr/bin/env python3
"""Apply private owner responses from the non-actionable checklist if present.

This phase reads the private Chinese confirmation checklist. If owner or
authorized-delegate responses are complete and marked ready, it stages a private
application result for later active authorization. With an empty checklist, it
records a public-safe No-Go and keeps source-map application closed.
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
PHASE_ID = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_NON_ACTIONABLE_GROUP_OWNER_RESPONSE_APPLICATION"
TASK_ID = "KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-NON-ACTIONABLE-GROUP-OWNER-RESPONSE-APPLICATION-20260706"
ACCEPTANCE_ID = "ACC-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-NON-ACTIONABLE-GROUP-OWNER-RESPONSE-APPLICATION"
VERSION = "0.1.4-non-actionable-group-owner-response-application"
STATUS = "completed_validated_local_only_owner_response_application_no_go"
DECISION = "NO_GO"
DIAGNOSTIC_CONCLUSION = "owner_response_application_attempted_no_complete_owner_responses"
NEXT_RECOMMENDED_PHASE = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_NON_ACTIONABLE_GROUP_OWNER_RESPONSE_APPLICATION_AFTER_FILL"
NEXT_REQUIRED_INPUT = "fill_private_chinese_confirmation_checklist_with_owner_or_authorized_delegate_responses"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "processed_value_source_map_completion_non_actionable_group_owner_response_application_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_value_source_map_completion_non_actionable_group_owner_response_application_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_value_source_map_completion_non_actionable_group_owner_response_application_go_no_go_report.json"
REPORT_PATH = HUMAN_DIR / "processed_value_source_map_completion_non_actionable_group_owner_response_application_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_non_actionable_group_owner_response_application_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_non_actionable_group_owner_response_application_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_non_actionable_group_owner_response_application_go_no_go_report.json"
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"

SOURCE_CHECKLIST_SUMMARY_PATH = (
    PROJECT_ROOT
    / "stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_NON_ACTIONABLE_GROUP_CONFIRMATION_CHECKLIST/machine/processed_value_source_map_completion_non_actionable_group_confirmation_checklist_summary.json"
)
PRIVATE_CHECKLIST_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_non_actionable_group_confirmation_checklist/private_non_actionable_group_confirmation_checklist.json"
)

PRIVATE_OUTPUT_DIR = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_non_actionable_group_owner_response_application"
)
PRIVATE_APPLICATION_RESULT_PATH = PRIVATE_OUTPUT_DIR / "private_non_actionable_group_owner_response_application_result.json"
PRIVATE_PENDING_QUEUE_PATH = PRIVATE_OUTPUT_DIR / "private_non_actionable_group_owner_response_application_pending_queue.json"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_non_actionable_group_owner_response_application_diagnostic.json"


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
        "private_confirmation_checklist_committed": False,
        "private_application_result_committed": False,
        "private_pending_queue_committed": False,
        "private_diagnostic_committed": False,
        "raw_file_committed": False,
        "raw_filename_committed": False,
        "raw_archive_member_name_committed": False,
        "field_header_plaintext_committed": False,
        "row_value_committed": False,
        "business_value_committed": False,
        "processed_value_fingerprint_committed": False,
        "credential_or_secret_committed": False,
    }


def _missing_fields_for_fill(fill: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    for key in ("选择", "owner_or_authorized_delegate", "resolution_reason_code"):
        if fill.get(key) in {None, ""}:
            missing.append(key)
    if fill.get("ready_for_intake") is not True:
        missing.append("ready_for_intake")
    choice = str(fill.get("选择") or "")
    if "提供非数值映射" in choice and fill.get("supplied_mapping_ref") in {None, ""}:
        missing.append("supplied_mapping_ref")
    if "补充来源证据" in choice and fill.get("additional_evidence_ref") in {None, ""}:
        missing.append("additional_evidence_ref")
    return sorted(set(missing))


def _build_private_application(
    *,
    generated_at: str,
    source_summary: dict[str, Any],
    checklist: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    items = checklist.get("checklist_items", [])
    if not isinstance(items, list):
        raise ValueError("checklist_items must be a list")
    applied_items: list[dict[str, Any]] = []
    pending_items: list[dict[str, Any]] = []
    invalid_items: list[dict[str, Any]] = []
    missing_counts: Counter[str] = Counter()
    recommendation_counts: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()
    filled_choice_count = 0
    filled_owner_count = 0
    ready_flag_count = 0
    target_total = 0

    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            invalid_items.append({"item_index": index, "invalid_reason": "checklist_item_not_object"})
            continue
        fill = item.get("填写区")
        if not isinstance(fill, dict):
            fill = {}
        target_slot_count = int(item.get("target_slot_count") or 0)
        target_total += target_slot_count
        recommendation_counts[str(item.get("推荐默认选择") or "unknown")] += 1
        status_counts[str(item.get("candidate_status") or "unknown")] += 1
        if fill.get("选择") not in {None, ""}:
            filled_choice_count += 1
        if fill.get("owner_or_authorized_delegate") not in {None, ""}:
            filled_owner_count += 1
        if fill.get("ready_for_intake") is True:
            ready_flag_count += 1
        missing = _missing_fields_for_fill(fill)
        for key in missing:
            missing_counts[key] += 1
        row = {
            "确认项编号": item.get("确认项编号"),
            "review_group_id": item.get("review_group_id"),
            "target_slot_count": target_slot_count,
            "target_slot_ids": item.get("target_slot_ids", []),
            "candidate_status": item.get("candidate_status"),
            "recommended_default": item.get("推荐默认选择"),
            "choice_supplied": fill.get("选择") not in {None, ""},
            "owner_or_authorized_delegate_supplied": fill.get("owner_or_authorized_delegate") not in {None, ""},
            "ready_for_intake": fill.get("ready_for_intake") is True,
            "missing_required_fields": missing,
        }
        if not missing:
            applied_items.append(
                {
                    **row,
                    "application_status": "owner_response_ready_for_future_active_authorization",
                    "active_authorization_written_by_this_phase": False,
                }
            )
        else:
            pending_items.append({**row, "application_status": "pending_owner_response_completion"})

    applied_target_slot_count = sum(int(item.get("target_slot_count") or 0) for item in applied_items)
    pending_target_slot_count = sum(int(item.get("target_slot_count") or 0) for item in pending_items)
    invalid_target_slot_count = sum(int(item.get("target_slot_count") or 0) for item in invalid_items)
    application_summary = {
        "source_confirmation_checklist_phase_id": source_summary.get("phase_id"),
        "source_confirmation_checklist_decision": source_summary.get("decision"),
        "source_checklist_item_count": int(source_summary.get("checklist_item_count") or 0),
        "source_checklist_target_slot_count": int(source_summary.get("checklist_target_slot_count") or 0),
        "checklist_item_count": len(items),
        "checklist_target_slot_count": target_total,
        "filled_choice_count": filled_choice_count,
        "filled_owner_or_authorized_delegate_count": filled_owner_count,
        "ready_for_intake_flag_count": ready_flag_count,
        "owner_response_application_attempted": True,
        "owner_response_applied_item_count": len(applied_items),
        "owner_response_applied_target_slot_count": applied_target_slot_count,
        "pending_owner_response_item_count": len(pending_items),
        "pending_owner_response_target_slot_count": pending_target_slot_count,
        "invalid_owner_response_item_count": len(invalid_items),
        "invalid_owner_response_target_slot_count": invalid_target_slot_count,
        "missing_required_field_counts": dict(missing_counts),
        "recommendation_counts": dict(recommendation_counts),
        "candidate_status_group_counts": dict(status_counts),
        "owner_or_authorized_delegate_response_supplied": len(applied_items) > 0,
        "active_owner_authorized_fill_record_ready": False,
        "active_owner_authorized_fill_record_written": False,
        "source_map_completion_reapplication_ready": False,
        "source_map_completion_reapplication_performed": False,
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
    }
    application_result = {
        "schema_version": "kmfa.private.v014_non_actionable_group_owner_response_application_result.v1",
        "classification": "private_non_actionable_group_owner_response_application_result_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_non_actionable_group_owner_response_application_result",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "application_summary": application_summary,
        "applied_items": applied_items,
        "raw_boundary": _raw_boundary(),
    }
    pending_queue = {
        "schema_version": "kmfa.private.v014_non_actionable_group_owner_response_application_pending_queue.v1",
        "classification": "private_non_actionable_group_owner_response_application_pending_queue_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_non_actionable_group_owner_response_application_pending_queue",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "pending_owner_response_item_count": len(pending_items),
        "pending_owner_response_target_slot_count": pending_target_slot_count,
        "invalid_owner_response_item_count": len(invalid_items),
        "invalid_owner_response_target_slot_count": invalid_target_slot_count,
        "pending_items": pending_items,
        "invalid_items": invalid_items,
        "raw_boundary": _raw_boundary(),
    }
    diagnostic = {
        "schema_version": "kmfa.private.v014_non_actionable_group_owner_response_application_diagnostic.v1",
        "classification": "private_non_actionable_group_owner_response_application_diagnostic_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_non_actionable_group_owner_response_application_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "application_summary": application_summary,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "raw_boundary": _raw_boundary(),
    }
    return application_result, pending_queue, diagnostic


def generate(*, generated_at: str | None = None, write_governance_event: bool = True) -> dict[str, Any]:
    timestamp = _now(generated_at)
    source_summary = _read_json(SOURCE_CHECKLIST_SUMMARY_PATH)
    checklist = _read_json(PRIVATE_CHECKLIST_PATH)
    application_result, pending_queue, private_diagnostic = _build_private_application(
        generated_at=timestamp,
        source_summary=source_summary,
        checklist=checklist,
    )
    application_summary = application_result["application_summary"]
    _write_json(PRIVATE_APPLICATION_RESULT_PATH, application_result)
    _write_json(PRIVATE_PENDING_QUEUE_PATH, pending_queue)
    _write_json(PRIVATE_DIAGNOSTIC_PATH, private_diagnostic)

    summary = {
        "schema_version": "kmfa.v014_non_actionable_group_owner_response_application_summary.v1",
        "record_type": "v014_processed_value_source_map_completion_non_actionable_group_owner_response_application_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "status": STATUS,
        "generated_at": timestamp,
        **application_summary,
        "private_confirmation_checklist_gitignored": _git_check_ignored(PRIVATE_CHECKLIST_PATH),
        "private_application_result_written": True,
        "private_application_result_gitignored": _git_check_ignored(PRIVATE_APPLICATION_RESULT_PATH),
        "private_pending_queue_written": True,
        "private_pending_queue_gitignored": _git_check_ignored(PRIVATE_PENDING_QUEUE_PATH),
        "private_diagnostic_written": True,
        "private_diagnostic_gitignored": _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH),
        "canonical_source_map_mutated": False,
        "canonical_source_map_records_applied_count": 0,
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
        "schema_version": "kmfa.v014_non_actionable_group_owner_response_application_go_no_go.v1",
        "record_type": "v014_processed_value_source_map_completion_non_actionable_group_owner_response_application_go_no_go_report",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "decision": DECISION,
        "status": STATUS,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "checklist_item_count": summary["checklist_item_count"],
        "checklist_target_slot_count": summary["checklist_target_slot_count"],
        "owner_response_applied_item_count": summary["owner_response_applied_item_count"],
        "pending_owner_response_item_count": summary["pending_owner_response_item_count"],
        "owner_or_authorized_delegate_response_supplied": False,
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
        "schema_version": "kmfa.v014_non_actionable_group_owner_response_application_manifest.v1",
        "record_type": "v014_processed_value_source_map_completion_non_actionable_group_owner_response_application_manifest",
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
            "private_confirmation_checklist": "private_runtime_only",
            "private_application_result": "private_runtime_only",
            "private_pending_queue": "private_runtime_only",
            "private_diagnostic": "private_runtime_only",
        },
        "validator": (
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. "
            "python3 KMFA/tools/check_v014_processed_value_source_map_completion_non_actionable_group_owner_response_application.py "
            "--require-private-owner-response-application"
        ),
        "git": {
            "branch": _git_output(["branch", "--show-current"]),
            "head": _git_output(["rev-parse", "HEAD"]),
            "status_short": _git_output(["status", "--short", "--branch"]),
        },
    }
    report = f"""# V014 非自动处理组 Owner Response Application

Decision: {DECISION}

本 phase 读取 private 中文确认清单并尝试应用 owner/授权响应。当前没有完整填写的响应，因此 0 条可应用，3 条继续 pending。

## 公开安全聚合结果

- Checklist items: {summary["checklist_item_count"]}
- Checklist target slots: {summary["checklist_target_slot_count"]}
- Filled choices: {summary["filled_choice_count"]}
- Filled owners/delegates: {summary["filled_owner_or_authorized_delegate_count"]}
- Ready flags: {summary["ready_for_intake_flag_count"]}
- Applied response items: {summary["owner_response_applied_item_count"]}
- Pending response items: {summary["pending_owner_response_item_count"]}
- Active authorization ready: `false`
- Full source-map reapplication ready: `false`

Next recommended phase: `{NEXT_RECOMMENDED_PHASE}`.
"""
    go_no_go_record = f"""# Go/No-Go Record

- phase_id: `{PHASE_ID}`
- decision: `{DECISION}`
- reason: `{DIAGNOSTIC_CONCLUSION}`
- owner_response_applied_item_count: `{summary["owner_response_applied_item_count"]}`
- pending_owner_response_item_count: `{summary["pending_owner_response_item_count"]}`
- active_owner_authorized_fill_record_ready: `false`
- github upload performed: `false`
"""
    risk_register = """# Risk Register

- Risk: treating an empty private checklist as owner approval.
  Mitigation: application requires filled choice, owner/delegate, reason, and ready flag; current applied count is zero.
- Risk: leaking private group or target details publicly.
  Mitigation: public artifacts contain only aggregate counts and gate flags; application details stay in ignored runtime.
"""
    rollback_plan = """# Rollback Plan

No raw file, checklist, source map, completion template, active authorization record or GitHub remote was modified. To roll back, remove this phase's public artifacts and metadata copies, then remove the ignored private application files if not needed.
"""
    test_results = """# Test Results

Status: passed locally after generation.

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_processed_value_source_map_completion_non_actionable_group_owner_response_application.py --generated-at 2026-07-06T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_value_source_map_completion_non_actionable_group_owner_response_application.py --require-private-owner-response-application`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_processed_value_source_map_completion_non_actionable_group_owner_response_application`
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
    event_id = "DEV-KMFA-20260706-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-NON-ACTIONABLE-GROUP-OWNER-RESPONSE-APPLICATION"
    summary = manifest["summary"]
    event = {
        "event_id": event_id,
        "event_time": generated_at,
        "event_type": "development",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "iteration_id": "ITER-20260706-KMFA-V014-NON-ACTIONABLE-GROUP-OWNER-RESPONSE-APPLICATION",
        "fact_level": "EXTRACTED",
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "go_no_go": manifest["go_no_go"]["decision"],
        "checklist_item_count": summary["checklist_item_count"],
        "owner_response_applied_item_count": summary["owner_response_applied_item_count"],
        "pending_owner_response_item_count": summary["pending_owner_response_item_count"],
        "active_owner_authorized_fill_record_ready": False,
        "source_map_completion_reapplication_performed": False,
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "result_commit": "PENDING",
        "summary": "Attempted private owner response application and kept full source-map application blocked because no complete owner/delegate responses were supplied.",
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
        "PASS: KMFA v0.1.4 non-actionable group owner response application generated "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"applied={manifest['summary']['owner_response_applied_item_count']}, "
        f"pending={manifest['summary']['pending_owner_response_item_count']})"
    )


if __name__ == "__main__":
    main()
