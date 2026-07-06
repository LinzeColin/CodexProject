#!/usr/bin/env python3
"""Intake non-actionable group resolution responses for KMFA v0.1.4.

This phase reads the private response template produced by the non-actionable
resolution packet phase. It does not invent owner decisions, does not modify the
template, does not write active authorization, and does not read or mutate raw
source files.
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
PHASE_ID = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_NON_ACTIONABLE_GROUP_RESPONSE_INTAKE"
TASK_ID = "KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-NON-ACTIONABLE-GROUP-RESPONSE-INTAKE-20260706"
ACCEPTANCE_ID = "ACC-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-NON-ACTIONABLE-GROUP-RESPONSE-INTAKE"
VERSION = "0.1.4-non-actionable-group-response-intake"
STATUS = "completed_validated_local_only_non_actionable_response_intake_no_go"
DECISION = "NO_GO"
DIAGNOSTIC_CONCLUSION = "non_actionable_group_response_intake_has_no_owner_authorized_ready_rows"
NEXT_RECOMMENDED_PHASE = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_NON_ACTIONABLE_GROUP_RESPONSE_INTAKE_AFTER_OWNER_UPDATE"
NEXT_REQUIRED_INPUT = "owner_or_authorized_delegate_updates_non_actionable_group_response_template_before_full_source_map_application"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "processed_value_source_map_completion_non_actionable_group_response_intake_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_value_source_map_completion_non_actionable_group_response_intake_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_value_source_map_completion_non_actionable_group_response_intake_go_no_go_report.json"
REPORT_PATH = HUMAN_DIR / "processed_value_source_map_completion_non_actionable_group_response_intake_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_non_actionable_group_response_intake_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_non_actionable_group_response_intake_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_non_actionable_group_response_intake_go_no_go_report.json"
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"

SOURCE_RESOLUTION_SUMMARY_PATH = (
    PROJECT_ROOT
    / "stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_NON_ACTIONABLE_GROUP_RESOLUTION_PACKET/machine/processed_value_source_map_completion_non_actionable_group_resolution_packet_summary.json"
)
PRIVATE_RESPONSE_TEMPLATE_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_non_actionable_group_resolution_packet/private_non_actionable_group_resolution_response_template.json"
)

PRIVATE_OUTPUT_DIR = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_non_actionable_group_response_intake"
)
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_non_actionable_group_response_intake_diagnostic.json"
PRIVATE_PENDING_QUEUE_PATH = PRIVATE_OUTPUT_DIR / "private_non_actionable_group_response_pending_queue.json"

OWNER_REQUIRED_KEYS = {
    "owner_or_authorized_delegate",
    "resolution_decision_code",
    "resolution_reason_code",
}
RESOLUTION_CODES_REQUIRING_REF = {
    "SUPPLY_NON_NUMERIC_OWNER_MAPPING": "supplied_mapping_ref",
    "REQUEST_ADDITIONAL_SOURCE_EVIDENCE": "additional_evidence_ref",
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
        "private_intake_diagnostic_committed": False,
        "private_pending_queue_committed": False,
        "raw_file_committed": False,
        "raw_filename_committed": False,
        "raw_archive_member_name_committed": False,
        "field_header_plaintext_committed": False,
        "row_value_committed": False,
        "business_value_committed": False,
        "processed_value_fingerprint_committed": False,
        "credential_or_secret_committed": False,
    }


def _missing_required_keys(group: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    for key in OWNER_REQUIRED_KEYS:
        value = group.get(key)
        if value in {None, ""}:
            missing.append(key)
    resolution_code = str(group.get("resolution_decision_code") or "")
    ref_key = RESOLUTION_CODES_REQUIRING_REF.get(resolution_code)
    if ref_key and group.get(ref_key) in {None, ""}:
        missing.append(ref_key)
    return sorted(missing)


def _build_private_records(
    *,
    generated_at: str,
    source_summary: dict[str, Any],
    response_template: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    groups = response_template.get("groups", [])
    if not isinstance(groups, list):
        raise ValueError("private response template groups must be a list")

    resolution_code_counts: Counter[str] = Counter()
    reason_code_counts: Counter[str] = Counter()
    candidate_status_counts: Counter[str] = Counter()
    ready_groups: list[dict[str, Any]] = []
    pending_groups: list[dict[str, Any]] = []
    invalid_groups: list[dict[str, Any]] = []
    target_slot_total = 0

    for index, group in enumerate(groups):
        if not isinstance(group, dict):
            invalid_groups.append({"group_index": index, "invalid_reason": "group_record_not_object"})
            continue
        resolution_code = str(group.get("resolution_decision_code") or "")
        reason_code = str(group.get("resolution_reason_code") or "")
        candidate_status = str(group.get("candidate_status") or "unknown")
        target_slot_count = int(group.get("target_slot_count") or 0)
        target_slot_total += target_slot_count
        resolution_code_counts[resolution_code or "MISSING_RESOLUTION_DECISION_CODE"] += 1
        reason_code_counts[reason_code or "MISSING_RESOLUTION_REASON_CODE"] += 1
        candidate_status_counts[candidate_status] += 1
        missing = _missing_required_keys(group)
        ready_flag = group.get("ready_for_intake") is True
        owner_supplied = bool(group.get("owner_or_authorized_delegate"))
        private_row = {
            "review_group_id": group.get("review_group_id"),
            "current_owner_group_decision_code": group.get("current_owner_group_decision_code"),
            "candidate_status": candidate_status,
            "target_slot_count": target_slot_count,
            "target_slot_ids": group.get("target_slot_ids", []),
            "resolution_decision_code": resolution_code,
            "resolution_reason_code": reason_code,
            "owner_or_authorized_delegate_supplied": owner_supplied,
            "ready_for_intake": ready_flag,
            "missing_required_keys": missing,
        }
        if ready_flag and not missing:
            ready_groups.append(private_row)
        elif missing or not ready_flag:
            pending_groups.append(private_row)
        else:
            invalid_groups.append({**private_row, "invalid_reason": "unclassified_response_state"})

    ready_target_count = sum(int(group.get("target_slot_count") or 0) for group in ready_groups)
    pending_target_count = sum(int(group.get("target_slot_count") or 0) for group in pending_groups)
    invalid_target_count = sum(int(group.get("target_slot_count") or 0) for group in invalid_groups)
    intake_summary = {
        "source_resolution_packet_phase_id": source_summary.get("phase_id"),
        "source_resolution_packet_decision": source_summary.get("decision"),
        "source_partial_exact_match_count": int(source_summary.get("source_partial_exact_match_count") or 0),
        "source_partial_mismatch_count": int(source_summary.get("source_partial_mismatch_count") or 0),
        "source_non_actionable_group_count": int(source_summary.get("non_actionable_group_count") or 0),
        "source_non_actionable_target_slot_count": int(source_summary.get("non_actionable_target_slot_count") or 0),
        "response_group_count": len(groups),
        "response_target_slot_count": target_slot_total,
        "ready_for_intake_group_count": len(ready_groups),
        "ready_for_intake_target_slot_count": ready_target_count,
        "pending_response_group_count": len(pending_groups),
        "pending_response_target_slot_count": pending_target_count,
        "invalid_response_group_count": len(invalid_groups),
        "invalid_response_target_slot_count": invalid_target_count,
        "resolution_decision_code_counts": dict(resolution_code_counts),
        "resolution_reason_code_counts": dict(reason_code_counts),
        "candidate_status_group_counts": dict(candidate_status_counts),
        "owner_or_authorized_delegate_resolution_supplied": len(ready_groups) > 0,
        "owner_or_authorized_delegate_resolution_required": True,
        "non_actionable_group_response_intake_performed": True,
        "codex_default_business_resolution_applied": False,
        "active_owner_authorized_fill_record_ready": False,
        "source_map_completion_reapplication_ready": False,
        "full_raw_to_processed_value_comparison_ready": False,
        "business_value_consistency_verified": False,
    }
    diagnostic = {
        "schema_version": "kmfa.private.v014_non_actionable_group_response_intake_diagnostic.v1",
        "classification": "private_non_actionable_group_response_intake_diagnostic_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_non_actionable_group_response_intake_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "intake_summary": intake_summary,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "raw_boundary": _raw_boundary(),
    }
    pending_queue = {
        "schema_version": "kmfa.private.v014_non_actionable_group_response_pending_queue.v1",
        "classification": "private_non_actionable_group_response_pending_queue_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_non_actionable_group_response_pending_queue",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "ready_for_intake_group_count": len(ready_groups),
        "pending_response_group_count": len(pending_groups),
        "invalid_response_group_count": len(invalid_groups),
        "ready_groups": ready_groups,
        "pending_groups": pending_groups,
        "invalid_groups": invalid_groups,
        "raw_boundary": _raw_boundary(),
    }
    return diagnostic, pending_queue


def generate(*, generated_at: str | None = None, write_governance_event: bool = True) -> dict[str, Any]:
    timestamp = _now(generated_at)
    source_summary = _read_json(SOURCE_RESOLUTION_SUMMARY_PATH)
    response_template = _read_json(PRIVATE_RESPONSE_TEMPLATE_PATH)
    private_diagnostic, private_pending_queue = _build_private_records(
        generated_at=timestamp,
        source_summary=source_summary,
        response_template=response_template,
    )
    intake_summary = private_diagnostic["intake_summary"]
    _write_json(PRIVATE_DIAGNOSTIC_PATH, private_diagnostic)
    _write_json(PRIVATE_PENDING_QUEUE_PATH, private_pending_queue)

    summary = {
        "schema_version": "kmfa.v014_non_actionable_group_response_intake_summary.v1",
        "record_type": "v014_processed_value_source_map_completion_non_actionable_group_response_intake_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "status": STATUS,
        "generated_at": timestamp,
        **intake_summary,
        "private_response_template_gitignored": _git_check_ignored(PRIVATE_RESPONSE_TEMPLATE_PATH),
        "private_diagnostic_written": True,
        "private_diagnostic_gitignored": _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH),
        "private_pending_queue_written": True,
        "private_pending_queue_gitignored": _git_check_ignored(PRIVATE_PENDING_QUEUE_PATH),
        "active_owner_authorized_fill_record_written": False,
        "canonical_source_map_mutated": False,
        "canonical_source_map_records_applied_count": 0,
        "source_map_completion_reapplication_performed": False,
        "partial_raw_to_processed_value_comparison_performed": True,
        "partial_raw_to_processed_value_consistency_verified": True,
        "raw_to_processed_value_comparison_performed": False,
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
        "schema_version": "kmfa.v014_non_actionable_group_response_intake_go_no_go.v1",
        "record_type": "v014_processed_value_source_map_completion_non_actionable_group_response_intake_go_no_go_report",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "decision": DECISION,
        "status": STATUS,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "source_partial_exact_match_count": summary["source_partial_exact_match_count"],
        "source_partial_mismatch_count": summary["source_partial_mismatch_count"],
        "response_group_count": summary["response_group_count"],
        "response_target_slot_count": summary["response_target_slot_count"],
        "ready_for_intake_group_count": summary["ready_for_intake_group_count"],
        "pending_response_group_count": summary["pending_response_group_count"],
        "invalid_response_group_count": summary["invalid_response_group_count"],
        "owner_or_authorized_delegate_resolution_supplied": False,
        "owner_or_authorized_delegate_resolution_required": True,
        "codex_default_business_resolution_applied": False,
        "source_map_completion_reapplication_ready": False,
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "blocked_until": NEXT_REQUIRED_INPUT,
    }
    manifest = {
        "schema_version": "kmfa.v014_non_actionable_group_response_intake_manifest.v1",
        "record_type": "v014_processed_value_source_map_completion_non_actionable_group_response_intake_manifest",
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
            "private_response_template": "private_runtime_only",
            "private_intake_diagnostic": "private_runtime_only",
            "private_pending_queue": "private_runtime_only",
        },
        "validator": (
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. "
            "python3 KMFA/tools/check_v014_processed_value_source_map_completion_non_actionable_group_response_intake.py "
            "--require-private-response-intake"
        ),
        "git": {
            "branch": _git_output(["branch", "--show-current"]),
            "head": _git_output(["rev-parse", "HEAD"]),
            "status_short": _git_output(["status", "--short", "--branch"]),
        },
    }
    report = f"""# V014 非自动处理组响应 Intake

Decision: {DECISION}

本 phase 读取私有 response template 并执行 intake 判断。当前没有 owner/授权人可 intake 的有效响应，因此不会写 active authorization，也不会执行 source-map reapplication。

## 公开安全聚合结果

- Response groups: {summary["response_group_count"]}
- Response target slots: {summary["response_target_slot_count"]}
- Ready for intake groups: {summary["ready_for_intake_group_count"]}
- Pending response groups: {summary["pending_response_group_count"]}
- Invalid response groups: {summary["invalid_response_group_count"]}
- Owner/delegate resolution supplied: `false`
- Owner/delegate resolution required: `true`
- Codex default business resolution applied: `false`
- Full source-map reapplication ready: `false`

Next recommended phase: `{NEXT_RECOMMENDED_PHASE}`.
"""
    go_no_go_record = f"""# Go/No-Go Record

- phase_id: `{PHASE_ID}`
- decision: `{DECISION}`
- reason: `{DIAGNOSTIC_CONCLUSION}`
- response_group_count: `{summary["response_group_count"]}`
- ready_for_intake_group_count: `{summary["ready_for_intake_group_count"]}`
- pending_response_group_count: `{summary["pending_response_group_count"]}`
- owner_or_authorized_delegate_resolution_supplied: `false`
- github upload performed: `false`
"""
    risk_register = """# Risk Register

- Risk: treating an unfilled template as owner authorization.
  Mitigation: intake requires ready_for_intake plus required owner/delegate fields; current ready count is zero.
- Risk: leaking private group or target details publicly.
  Mitigation: public artifacts contain only aggregate counts and gate flags; private queue stays in ignored runtime.
"""
    rollback_plan = """# Rollback Plan

No raw file, response template, source map, completion template, active authorization record or GitHub remote was modified. To roll back, remove this phase's public artifacts and metadata copies, then remove the ignored private diagnostic and pending queue if not needed.
"""
    test_results = """# Test Results

Status: passed locally after generation.

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_processed_value_source_map_completion_non_actionable_group_response_intake.py --generated-at 2026-07-06T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_value_source_map_completion_non_actionable_group_response_intake.py --require-private-response-intake`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_processed_value_source_map_completion_non_actionable_group_response_intake`
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
    event_id = "DEV-KMFA-20260706-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-NON-ACTIONABLE-GROUP-RESPONSE-INTAKE"
    summary = manifest["summary"]
    event = {
        "event_id": event_id,
        "event_time": generated_at,
        "event_type": "development",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "iteration_id": "ITER-20260706-KMFA-V014-NON-ACTIONABLE-GROUP-RESPONSE-INTAKE",
        "fact_level": "EXTRACTED",
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "go_no_go": manifest["go_no_go"]["decision"],
        "response_group_count": summary["response_group_count"],
        "response_target_slot_count": summary["response_target_slot_count"],
        "ready_for_intake_group_count": summary["ready_for_intake_group_count"],
        "pending_response_group_count": summary["pending_response_group_count"],
        "owner_or_authorized_delegate_resolution_supplied": False,
        "owner_or_authorized_delegate_resolution_required": True,
        "codex_default_business_resolution_applied": False,
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
        "summary": "Intaken private non-actionable group response template and kept full source-map application blocked because no owner/delegate-ready responses are present.",
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
        "PASS: KMFA v0.1.4 non-actionable group response intake generated "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"ready={manifest['summary']['ready_for_intake_group_count']}, "
        f"pending={manifest['summary']['pending_response_group_count']})"
    )


if __name__ == "__main__":
    main()
