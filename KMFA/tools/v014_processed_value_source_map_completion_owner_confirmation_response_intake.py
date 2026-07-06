#!/usr/bin/env python3
"""Intake the private owner confirmation response draft for KMFA v0.1.4.

This phase reads the private response draft produced by the owner confirmation
response packet phase. It validates whether owner or authorized-delegate
responses are complete. It does not fill responses, write active authorization,
apply source-map records, or read raw source files.
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
PHASE_ID = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_CONFIRMATION_RESPONSE_INTAKE"
TASK_ID = "KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-OWNER-CONFIRMATION-RESPONSE-INTAKE-20260706"
ACCEPTANCE_ID = "ACC-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-OWNER-CONFIRMATION-RESPONSE-INTAKE"
VERSION = "0.1.4-owner-confirmation-response-intake"
STATUS = "completed_validated_local_only_owner_confirmation_response_intake_no_go"
DECISION = "NO_GO"
DIAGNOSTIC_CONCLUSION = "owner_confirmation_response_intake_has_no_complete_owner_responses"
NEXT_RECOMMENDED_PHASE = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_CONFIRMATION_RESPONSE_INTAKE_AFTER_FILL"
NEXT_REQUIRED_INPUT = "owner_or_authorized_delegate_completes_private_confirmation_response_draft"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_confirmation_response_intake_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_confirmation_response_intake_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_confirmation_response_intake_go_no_go_report.json"
REPORT_PATH = HUMAN_DIR / "processed_value_source_map_completion_owner_confirmation_response_intake_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_owner_confirmation_response_intake_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_owner_confirmation_response_intake_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_owner_confirmation_response_intake_go_no_go_report.json"
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"

SOURCE_RESPONSE_PACKET_SUMMARY_PATH = (
    PROJECT_ROOT
    / "stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_CONFIRMATION_RESPONSE_PACKET/machine/processed_value_source_map_completion_owner_confirmation_response_packet_summary.json"
)
PRIVATE_RESPONSE_DRAFT_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_owner_confirmation_response_packet/private_owner_confirmation_response_draft.json"
)

PRIVATE_OUTPUT_DIR = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_owner_confirmation_response_intake"
)
PRIVATE_INTAKE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_owner_confirmation_response_intake_diagnostic.json"
PRIVATE_VALID_RESPONSE_QUEUE_PATH = PRIVATE_OUTPUT_DIR / "private_owner_confirmation_valid_response_queue.json"
PRIVATE_PENDING_RESPONSE_QUEUE_PATH = PRIVATE_OUTPUT_DIR / "private_owner_confirmation_pending_response_queue.json"


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
        "private_response_draft_committed": False,
        "private_intake_diagnostic_committed": False,
        "private_valid_response_queue_committed": False,
        "private_pending_response_queue_committed": False,
        "raw_file_committed": False,
        "raw_filename_committed": False,
        "raw_archive_member_name_committed": False,
        "field_header_plaintext_committed": False,
        "row_value_committed": False,
        "business_value_committed": False,
        "processed_value_fingerprint_committed": False,
        "credential_or_secret_committed": False,
    }


def _missing_response_fields(item: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    for key in ("选择", "owner_or_authorized_delegate", "resolution_reason_code"):
        if item.get(key) in {None, ""}:
            missing.append(key)
    if item.get("ready_for_intake") is not True:
        missing.append("ready_for_intake")
    choice = str(item.get("选择") or "")
    if "提供非数值映射" in choice and item.get("supplied_mapping_ref") in {None, ""}:
        missing.append("supplied_mapping_ref")
    if "补充来源证据" in choice and item.get("additional_evidence_ref") in {None, ""}:
        missing.append("additional_evidence_ref")
    return sorted(set(missing))


def _build_private_intake(
    *,
    generated_at: str,
    source_summary: dict[str, Any],
    response_draft: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    items = response_draft.get("items", [])
    if not isinstance(items, list):
        raise ValueError("response draft items must be a list")

    valid_responses: list[dict[str, Any]] = []
    pending_responses: list[dict[str, Any]] = []
    invalid_responses: list[dict[str, Any]] = []
    missing_counts: Counter[str] = Counter()
    filled_counts: Counter[str] = Counter()
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            invalid_responses.append({"item_index": index, "invalid_reason": "response_draft_item_not_object"})
            continue
        missing = _missing_response_fields(item)
        for field in missing:
            missing_counts[field] += 1
        if item.get("选择") not in {None, ""}:
            filled_counts["选择"] += 1
        if item.get("owner_or_authorized_delegate") not in {None, ""}:
            filled_counts["owner_or_authorized_delegate"] += 1
        if item.get("resolution_reason_code") not in {None, ""}:
            filled_counts["resolution_reason_code"] += 1
        if item.get("ready_for_intake") is True:
            filled_counts["ready_for_intake"] += 1
        row = {
            "response_item_id": item.get("response_item_id"),
            "确认项编号": item.get("确认项编号"),
            "choice_supplied": item.get("选择") not in {None, ""},
            "owner_or_authorized_delegate_supplied": item.get("owner_or_authorized_delegate") not in {None, ""},
            "resolution_reason_code_supplied": item.get("resolution_reason_code") not in {None, ""},
            "ready_for_intake": item.get("ready_for_intake") is True,
            "missing_required_fields": missing,
        }
        if not missing:
            valid_responses.append(
                {
                    **row,
                    "intake_status": "valid_owner_confirmation_response",
                    "active_authorization_written_by_this_phase": False,
                }
            )
        else:
            pending_responses.append({**row, "intake_status": "pending_owner_confirmation_response"})

    intake_summary = {
        "source_owner_confirmation_response_packet_phase_id": source_summary.get("phase_id"),
        "source_owner_confirmation_response_packet_decision": source_summary.get("decision"),
        "source_response_packet_item_count": int(source_summary.get("response_packet_item_count") or 0),
        "source_response_packet_target_slot_count": int(source_summary.get("response_packet_target_slot_count") or 0),
        "response_draft_item_count": len(items),
        "valid_owner_confirmation_response_count": len(valid_responses),
        "pending_owner_confirmation_response_count": len(pending_responses),
        "invalid_owner_confirmation_response_count": len(invalid_responses),
        "filled_field_counts": dict(filled_counts),
        "missing_required_field_counts": dict(missing_counts),
        "owner_confirmation_response_intake_performed": True,
        "owner_confirmation_response_supplied": len(valid_responses) > 0,
        "active_owner_authorized_fill_record_ready": False,
        "active_owner_authorized_fill_record_written": False,
        "source_map_completion_reapplication_ready": False,
        "source_map_completion_reapplication_performed": False,
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
    }
    diagnostic = {
        "schema_version": "kmfa.private.v014_owner_confirmation_response_intake_diagnostic.v1",
        "classification": "private_owner_confirmation_response_intake_diagnostic_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_owner_confirmation_response_intake_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "intake_summary": intake_summary,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "raw_boundary": _raw_boundary(),
    }
    valid_queue = {
        "schema_version": "kmfa.private.v014_owner_confirmation_valid_response_queue.v1",
        "classification": "private_owner_confirmation_valid_response_queue_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_owner_confirmation_valid_response_queue",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "valid_owner_confirmation_response_count": len(valid_responses),
        "valid_responses": valid_responses,
        "raw_boundary": _raw_boundary(),
    }
    pending_queue = {
        "schema_version": "kmfa.private.v014_owner_confirmation_pending_response_queue.v1",
        "classification": "private_owner_confirmation_pending_response_queue_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_owner_confirmation_pending_response_queue",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "pending_owner_confirmation_response_count": len(pending_responses),
        "invalid_owner_confirmation_response_count": len(invalid_responses),
        "pending_responses": pending_responses,
        "invalid_responses": invalid_responses,
        "raw_boundary": _raw_boundary(),
    }
    return diagnostic, valid_queue, pending_queue


def generate(*, generated_at: str | None = None, write_governance_event: bool = True) -> dict[str, Any]:
    timestamp = _now(generated_at)
    source_summary = _read_json(SOURCE_RESPONSE_PACKET_SUMMARY_PATH)
    response_draft = _read_json(PRIVATE_RESPONSE_DRAFT_PATH)
    private_diagnostic, private_valid_queue, private_pending_queue = _build_private_intake(
        generated_at=timestamp,
        source_summary=source_summary,
        response_draft=response_draft,
    )
    intake_summary = private_diagnostic["intake_summary"]
    _write_json(PRIVATE_INTAKE_DIAGNOSTIC_PATH, private_diagnostic)
    _write_json(PRIVATE_VALID_RESPONSE_QUEUE_PATH, private_valid_queue)
    _write_json(PRIVATE_PENDING_RESPONSE_QUEUE_PATH, private_pending_queue)

    summary = {
        "schema_version": "kmfa.v014_owner_confirmation_response_intake_summary.v1",
        "record_type": "v014_processed_value_source_map_completion_owner_confirmation_response_intake_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "status": STATUS,
        "generated_at": timestamp,
        **intake_summary,
        "private_response_draft_gitignored": _git_check_ignored(PRIVATE_RESPONSE_DRAFT_PATH),
        "private_intake_diagnostic_written": True,
        "private_intake_diagnostic_gitignored": _git_check_ignored(PRIVATE_INTAKE_DIAGNOSTIC_PATH),
        "private_valid_response_queue_written": True,
        "private_valid_response_queue_gitignored": _git_check_ignored(PRIVATE_VALID_RESPONSE_QUEUE_PATH),
        "private_pending_response_queue_written": True,
        "private_pending_response_queue_gitignored": _git_check_ignored(PRIVATE_PENDING_RESPONSE_QUEUE_PATH),
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
        "schema_version": "kmfa.v014_owner_confirmation_response_intake_go_no_go.v1",
        "record_type": "v014_processed_value_source_map_completion_owner_confirmation_response_intake_go_no_go_report",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "decision": DECISION,
        "status": STATUS,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "response_draft_item_count": summary["response_draft_item_count"],
        "valid_owner_confirmation_response_count": summary["valid_owner_confirmation_response_count"],
        "pending_owner_confirmation_response_count": summary["pending_owner_confirmation_response_count"],
        "owner_confirmation_response_supplied": False,
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
        "schema_version": "kmfa.v014_owner_confirmation_response_intake_manifest.v1",
        "record_type": "v014_processed_value_source_map_completion_owner_confirmation_response_intake_manifest",
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
            "private_response_draft": "private_runtime_only",
            "private_intake_diagnostic": "private_runtime_only",
            "private_valid_response_queue": "private_runtime_only",
            "private_pending_response_queue": "private_runtime_only",
        },
        "validator": (
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. "
            "python3 KMFA/tools/check_v014_processed_value_source_map_completion_owner_confirmation_response_intake.py "
            "--require-private-owner-confirmation-intake"
        ),
        "git": {
            "branch": _git_output(["branch", "--show-current"]),
            "head": _git_output(["rev-parse", "HEAD"]),
            "status_short": _git_output(["status", "--short", "--branch"]),
        },
    }
    report = f"""# V014 Owner 确认响应 Intake

Decision: {DECISION}

本 phase 读取 private owner confirmation response draft 并执行 intake。当前没有完整填写的 owner/授权人响应，因此 0 条有效响应、3 条继续 pending。

## 公开安全聚合结果

- Response draft items: {summary["response_draft_item_count"]}
- Valid owner confirmation responses: {summary["valid_owner_confirmation_response_count"]}
- Pending owner confirmation responses: {summary["pending_owner_confirmation_response_count"]}
- Invalid owner confirmation responses: {summary["invalid_owner_confirmation_response_count"]}
- Active authorization ready: `false`
- Full source-map reapplication ready: `false`

Next recommended phase: `{NEXT_RECOMMENDED_PHASE}`.
"""
    go_no_go_record = f"""# Go/No-Go Record

- phase_id: `{PHASE_ID}`
- decision: `{DECISION}`
- reason: `{DIAGNOSTIC_CONCLUSION}`
- valid_owner_confirmation_response_count: `{summary["valid_owner_confirmation_response_count"]}`
- pending_owner_confirmation_response_count: `{summary["pending_owner_confirmation_response_count"]}`
- active_owner_authorized_fill_record_ready: `false`
- github upload performed: `false`
"""
    risk_register = """# Risk Register

- Risk: treating an empty response draft as owner approval.
  Mitigation: intake requires choice, owner/delegate, reason, and ready flag; current valid count is zero.
- Risk: leaking private response details publicly.
  Mitigation: public artifacts contain only aggregate counts and gate flags; private queues stay in ignored runtime.
"""
    rollback_plan = """# Rollback Plan

No raw file, response draft, source map, completion template, active authorization record or GitHub remote was modified. To roll back, remove this phase's public artifacts and metadata copies, then remove the ignored private intake files if not needed.
"""
    test_results = """# Test Results

Status: passed locally after generation.

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_processed_value_source_map_completion_owner_confirmation_response_intake.py --generated-at 2026-07-06T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_value_source_map_completion_owner_confirmation_response_intake.py --require-private-owner-confirmation-intake`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_processed_value_source_map_completion_owner_confirmation_response_intake`
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
    event_id = "DEV-KMFA-20260706-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-OWNER-CONFIRMATION-RESPONSE-INTAKE"
    summary = manifest["summary"]
    event = {
        "event_id": event_id,
        "event_time": generated_at,
        "event_type": "development",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "iteration_id": "ITER-20260706-KMFA-V014-OWNER-CONFIRMATION-RESPONSE-INTAKE",
        "fact_level": "EXTRACTED",
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "go_no_go": manifest["go_no_go"]["decision"],
        "response_draft_item_count": summary["response_draft_item_count"],
        "valid_owner_confirmation_response_count": summary["valid_owner_confirmation_response_count"],
        "pending_owner_confirmation_response_count": summary["pending_owner_confirmation_response_count"],
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
        "summary": "Intaken private owner confirmation response draft and kept full source-map application blocked because no complete owner/delegate responses were supplied.",
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
        "PASS: KMFA v0.1.4 owner confirmation response intake generated "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"valid={manifest['summary']['valid_owner_confirmation_response_count']}, "
        f"pending={manifest['summary']['pending_owner_confirmation_response_count']})"
    )


if __name__ == "__main__":
    main()
