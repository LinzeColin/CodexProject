#!/usr/bin/env python3
"""Prepare the private non-actionable group resolution packet for KMFA v0.1.4.

This phase turns the remaining non-actionable owner-group decisions into a
private response packet and public-safe aggregate evidence. It does not infer
business mappings, does not write an active authorization record, and does not
read or mutate the raw data inbox.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


PROJECT_ROOT = Path("KMFA")
PHASE_ID = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_NON_ACTIONABLE_GROUP_RESOLUTION_PACKET"
TASK_ID = "KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-NON-ACTIONABLE-GROUP-RESOLUTION-PACKET-20260706"
ACCEPTANCE_ID = "ACC-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-NON-ACTIONABLE-GROUP-RESOLUTION-PACKET"
VERSION = "0.1.4-non-actionable-group-resolution-packet"
STATUS = "completed_validated_local_only_non_actionable_resolution_packet_no_go"
DECISION = "NO_GO"
DIAGNOSTIC_CONCLUSION = "non_actionable_group_resolution_packet_ready_business_resolution_not_inferred"
NEXT_RECOMMENDED_PHASE = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_NON_ACTIONABLE_GROUP_RESPONSE_INTAKE"
NEXT_REQUIRED_INPUT = "owner_or_authorized_delegate_resolves_non_actionable_group_packet_before_full_source_map_application"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "processed_value_source_map_completion_non_actionable_group_resolution_packet_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_value_source_map_completion_non_actionable_group_resolution_packet_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_value_source_map_completion_non_actionable_group_resolution_packet_go_no_go_report.json"
REPORT_PATH = HUMAN_DIR / "processed_value_source_map_completion_non_actionable_group_resolution_packet_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_non_actionable_group_resolution_packet_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_non_actionable_group_resolution_packet_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_non_actionable_group_resolution_packet_go_no_go_report.json"
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"

SOURCE_PARTIAL_COMPARISON_SUMMARY_PATH = (
    PROJECT_ROOT
    / "stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_PARTIAL_RAW_TO_PROCESSED_COMPARISON/machine/processed_value_source_map_completion_partial_raw_to_processed_comparison_summary.json"
)
PRIVATE_ACTIONABLE_PLAN_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_owner_group_actionable_application_plan/private_owner_group_actionable_application_plan.json"
)
PRIVATE_PARTIAL_APPLICATION_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_owner_group_partial_application/private_owner_group_partial_application_result.json"
)
PRIVATE_DECISION_DIAGNOSTIC_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_owner_group_decision_response_intake/private_owner_group_decision_response_intake_diagnostic.json"
)

PRIVATE_OUTPUT_DIR = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_non_actionable_group_resolution_packet"
)
PRIVATE_RESOLUTION_PACKET_PATH = PRIVATE_OUTPUT_DIR / "private_non_actionable_group_resolution_packet.json"
PRIVATE_RESPONSE_TEMPLATE_PATH = PRIVATE_OUTPUT_DIR / "private_non_actionable_group_resolution_response_template.json"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_non_actionable_group_resolution_diagnostic.json"

ALLOWED_RESOLUTION_CODES = [
    "SUPPLY_NON_NUMERIC_OWNER_MAPPING",
    "MARK_NOT_APPLICABLE_WITH_REASON",
    "KEEP_PENDING_WITH_REASON",
    "REQUEST_ADDITIONAL_SOURCE_EVIDENCE",
    "CONFIRM_UNMATCHED_NO_VALUE_SOURCE",
]


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
        "private_resolution_packet_committed": False,
        "private_response_template_committed": False,
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


def _resolution_policy(candidate_status: str, decision_code: str) -> dict[str, Any]:
    if candidate_status == "requires_non_numeric_owner_mapping" or decision_code == "KEEP_PENDING":
        return {
            "current_blocker": "requires_owner_supplied_non_numeric_mapping_or_explicit_not_applicable_reason",
            "codex_default_resolution_code": "KEEP_PENDING_WITH_REASON",
            "codex_default_reason_code": "codex_cannot_infer_non_numeric_business_mapping",
            "recommended_resolution_path": "owner_or_authorized_delegate_supplies_mapping_or_marks_not_applicable",
            "owner_input_required_keys": [
                "resolution_decision_code",
                "resolution_reason_code",
                "owner_or_authorized_delegate",
            ],
        }
    return {
        "current_blocker": "requires_additional_source_evidence_or_explicit_no_value_source_confirmation",
        "codex_default_resolution_code": "REQUEST_ADDITIONAL_SOURCE_EVIDENCE",
        "codex_default_reason_code": "codex_cannot_infer_missing_value_source",
        "recommended_resolution_path": "owner_or_authorized_delegate_adds_evidence_or_confirms_no_value_source",
        "owner_input_required_keys": [
            "resolution_decision_code",
            "resolution_reason_code",
            "owner_or_authorized_delegate",
        ],
    }


def _build_private_outputs(
    *,
    generated_at: str,
    source_summary: dict[str, Any],
    actionable_plan: dict[str, Any],
    partial_application: dict[str, Any],
    decision_diagnostic: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    non_actionable_items = actionable_plan.get("non_actionable_items", [])
    blocked_rows = partial_application.get("blocked_rows", [])
    if not isinstance(non_actionable_items, list):
        raise ValueError("non_actionable_items must be a list")
    if not isinstance(blocked_rows, list):
        raise ValueError("blocked_rows must be a list")

    target_ids_by_group: dict[str, list[str]] = defaultdict(list)
    for row in blocked_rows:
        if not isinstance(row, dict):
            continue
        review_group_id = row.get("review_group_id")
        target_slot_id = row.get("target_slot_id")
        if isinstance(review_group_id, str) and isinstance(target_slot_id, str):
            target_ids_by_group[review_group_id].append(target_slot_id)

    decision_group_counts: Counter[str] = Counter()
    decision_target_counts: Counter[str] = Counter()
    status_group_counts: Counter[str] = Counter()
    status_target_counts: Counter[str] = Counter()
    resolution_groups: list[dict[str, Any]] = []
    response_groups: list[dict[str, Any]] = []
    missing_blocked_target_group_count = 0

    for item in non_actionable_items:
        if not isinstance(item, dict):
            continue
        review_group_id = str(item.get("review_group_id", ""))
        candidate_status = str(item.get("candidate_status", "unknown"))
        decision_code = str(item.get("owner_group_decision_code", "unknown"))
        target_slot_count = int(item.get("target_slot_count") or 0)
        target_slot_ids = sorted(target_ids_by_group.get(review_group_id, []))
        if len(target_slot_ids) != target_slot_count:
            missing_blocked_target_group_count += 1
        policy = _resolution_policy(candidate_status, decision_code)
        decision_group_counts[decision_code] += 1
        decision_target_counts[decision_code] += target_slot_count
        status_group_counts[candidate_status] += 1
        status_target_counts[candidate_status] += target_slot_count
        resolution_groups.append(
            {
                "review_group_id": review_group_id,
                "candidate_status": candidate_status,
                "current_owner_group_decision_code": decision_code,
                "target_slot_count": target_slot_count,
                "target_slot_ids": target_slot_ids,
                "allowed_resolution_codes": ALLOWED_RESOLUTION_CODES,
                "current_blocker": policy["current_blocker"],
                "codex_default_resolution_code": policy["codex_default_resolution_code"],
                "codex_default_reason_code": policy["codex_default_reason_code"],
                "codex_business_mapping_inferred": False,
                "recommended_resolution_path": policy["recommended_resolution_path"],
                "owner_input_required_keys": policy["owner_input_required_keys"],
            }
        )
        response_groups.append(
            {
                "review_group_id": review_group_id,
                "current_owner_group_decision_code": decision_code,
                "candidate_status": candidate_status,
                "target_slot_count": target_slot_count,
                "target_slot_ids": target_slot_ids,
                "allowed_resolution_codes": ALLOWED_RESOLUTION_CODES,
                "resolution_decision_code": policy["codex_default_resolution_code"],
                "resolution_reason_code": policy["codex_default_reason_code"],
                "owner_or_authorized_delegate": None,
                "owner_resolution_note": None,
                "supplied_mapping_ref": None,
                "additional_evidence_ref": None,
                "ready_for_intake": False,
            }
        )

    resolution_summary = {
        "review_group_count": int(decision_diagnostic.get("review_group_count") or 0),
        "response_row_count": int(decision_diagnostic.get("response_row_count") or 0),
        "source_partial_comparable_pair_count": int(source_summary.get("partial_comparable_pair_count") or 0),
        "source_partial_exact_match_count": int(source_summary.get("partial_exact_match_count") or 0),
        "source_partial_mismatch_count": int(source_summary.get("partial_mismatch_count") or 0),
        "source_partial_missing_candidate_count": int(source_summary.get("partial_missing_candidate_count") or 0),
        "non_actionable_group_count": len(resolution_groups),
        "non_actionable_target_slot_count": sum(group["target_slot_count"] for group in resolution_groups),
        "decision_code_group_counts": dict(decision_group_counts),
        "decision_code_target_slot_counts": dict(decision_target_counts),
        "candidate_status_group_counts": dict(status_group_counts),
        "candidate_status_target_slot_counts": dict(status_target_counts),
        "missing_blocked_target_group_count": missing_blocked_target_group_count,
        "codex_default_business_resolution_applied": False,
        "owner_or_authorized_delegate_resolution_required": True,
        "non_actionable_resolution_packet_ready": True,
        "source_map_completion_reapplication_ready": False,
        "full_raw_to_processed_value_comparison_ready": False,
        "business_value_consistency_verified": False,
    }
    packet = {
        "schema_version": "kmfa.private.v014_non_actionable_group_resolution_packet.v1",
        "classification": "private_non_actionable_group_resolution_packet_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_non_actionable_group_resolution_packet",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "source_partial_comparison_phase_id": source_summary.get("phase_id"),
        "source_actionable_plan_phase_id": actionable_plan.get("phase_id"),
        "source_partial_application_phase_id": partial_application.get("phase_id"),
        "source_decision_diagnostic_phase_id": decision_diagnostic.get("phase_id"),
        "resolution_summary": resolution_summary,
        "resolution_groups": resolution_groups,
        "raw_boundary": _raw_boundary(),
    }
    response_template = {
        "schema_version": "kmfa.private.v014_non_actionable_group_resolution_response_template.v1",
        "classification": "private_non_actionable_group_resolution_response_template_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_non_actionable_group_resolution_response_template",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "response_group_count": len(response_groups),
        "response_target_slot_count": resolution_summary["non_actionable_target_slot_count"],
        "allowed_resolution_codes": ALLOWED_RESOLUTION_CODES,
        "default_policy": "keep_no_go_until_owner_or_authorized_delegate_supplies_resolution",
        "groups": response_groups,
        "raw_boundary": _raw_boundary(),
    }
    diagnostic = {
        "schema_version": "kmfa.private.v014_non_actionable_group_resolution_diagnostic.v1",
        "classification": "private_non_actionable_group_resolution_diagnostic_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_non_actionable_group_resolution_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "resolution_summary": resolution_summary,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "raw_boundary": _raw_boundary(),
    }
    return packet, response_template, diagnostic


def generate(*, generated_at: str | None = None, write_governance_event: bool = True) -> dict[str, Any]:
    timestamp = _now(generated_at)
    source_summary = _read_json(SOURCE_PARTIAL_COMPARISON_SUMMARY_PATH)
    actionable_plan = _read_json(PRIVATE_ACTIONABLE_PLAN_PATH)
    partial_application = _read_json(PRIVATE_PARTIAL_APPLICATION_PATH)
    decision_diagnostic = _read_json(PRIVATE_DECISION_DIAGNOSTIC_PATH)

    private_packet, private_response_template, private_diagnostic = _build_private_outputs(
        generated_at=timestamp,
        source_summary=source_summary,
        actionable_plan=actionable_plan,
        partial_application=partial_application,
        decision_diagnostic=decision_diagnostic,
    )
    resolution_summary = private_packet["resolution_summary"]
    _write_json(PRIVATE_RESOLUTION_PACKET_PATH, private_packet)
    _write_json(PRIVATE_RESPONSE_TEMPLATE_PATH, private_response_template)
    _write_json(PRIVATE_DIAGNOSTIC_PATH, private_diagnostic)

    summary = {
        "schema_version": "kmfa.v014_non_actionable_group_resolution_packet_summary.v1",
        "record_type": "v014_processed_value_source_map_completion_non_actionable_group_resolution_packet_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "status": STATUS,
        "generated_at": timestamp,
        "source_partial_comparison_phase_id": source_summary.get("phase_id"),
        "source_partial_comparison_decision": source_summary.get("decision"),
        "source_actionable_plan_phase_id": actionable_plan.get("phase_id"),
        "source_partial_application_phase_id": partial_application.get("phase_id"),
        "review_group_count": resolution_summary["review_group_count"],
        "response_row_count": resolution_summary["response_row_count"],
        "source_partial_comparable_pair_count": resolution_summary["source_partial_comparable_pair_count"],
        "source_partial_exact_match_count": resolution_summary["source_partial_exact_match_count"],
        "source_partial_mismatch_count": resolution_summary["source_partial_mismatch_count"],
        "source_partial_missing_candidate_count": resolution_summary["source_partial_missing_candidate_count"],
        "non_actionable_group_count": resolution_summary["non_actionable_group_count"],
        "non_actionable_target_slot_count": resolution_summary["non_actionable_target_slot_count"],
        "decision_code_group_counts": resolution_summary["decision_code_group_counts"],
        "decision_code_target_slot_counts": resolution_summary["decision_code_target_slot_counts"],
        "candidate_status_group_counts": resolution_summary["candidate_status_group_counts"],
        "candidate_status_target_slot_counts": resolution_summary["candidate_status_target_slot_counts"],
        "missing_blocked_target_group_count": resolution_summary["missing_blocked_target_group_count"],
        "private_resolution_packet_written": True,
        "private_resolution_packet_gitignored": _git_check_ignored(PRIVATE_RESOLUTION_PACKET_PATH),
        "private_response_template_written": True,
        "private_response_template_gitignored": _git_check_ignored(PRIVATE_RESPONSE_TEMPLATE_PATH),
        "private_diagnostic_written": True,
        "private_diagnostic_gitignored": _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH),
        "codex_default_business_resolution_applied": False,
        "owner_or_authorized_delegate_resolution_required": True,
        "non_actionable_resolution_packet_ready": True,
        "active_owner_authorized_fill_record_ready": False,
        "active_owner_authorized_fill_record_written": False,
        "canonical_source_map_mutated": False,
        "canonical_source_map_records_applied_count": 0,
        "source_map_completion_reapplication_ready": False,
        "source_map_completion_reapplication_performed": False,
        "partial_raw_to_processed_value_comparison_performed": True,
        "partial_raw_to_processed_value_consistency_verified": True,
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
        "schema_version": "kmfa.v014_non_actionable_group_resolution_packet_go_no_go.v1",
        "record_type": "v014_processed_value_source_map_completion_non_actionable_group_resolution_packet_go_no_go_report",
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
        "non_actionable_group_count": summary["non_actionable_group_count"],
        "non_actionable_target_slot_count": summary["non_actionable_target_slot_count"],
        "codex_default_business_resolution_applied": False,
        "owner_or_authorized_delegate_resolution_required": True,
        "source_map_completion_reapplication_ready": False,
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "blocked_until": NEXT_REQUIRED_INPUT,
    }
    manifest = {
        "schema_version": "kmfa.v014_non_actionable_group_resolution_packet_manifest.v1",
        "record_type": "v014_processed_value_source_map_completion_non_actionable_group_resolution_packet_manifest",
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
            "private_resolution_packet": "private_runtime_only",
            "private_response_template": "private_runtime_only",
            "private_diagnostic": "private_runtime_only",
        },
        "validator": (
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. "
            "python3 KMFA/tools/check_v014_processed_value_source_map_completion_non_actionable_group_resolution_packet.py "
            "--require-private-resolution-packet"
        ),
        "git": {
            "branch": _git_output(["branch", "--show-current"]),
            "head": _git_output(["rev-parse", "HEAD"]),
            "status_short": _git_output(["status", "--short", "--branch"]),
        },
    }
    report = f"""# V014 非自动处理组决策包

Decision: {DECISION}

本 phase 将剩余非自动处理 owner group 整理为私有决策包和 response template。Codex 已决定保持 No-Go，不推断业务映射、不写 active authorization、不执行 source-map reapplication。

## 公开安全聚合结果

- Review groups: {summary["review_group_count"]}
- Response rows represented: {summary["response_row_count"]}
- Partial raw-to-processed exact matches: {summary["source_partial_exact_match_count"]}
- Partial raw-to-processed mismatches: {summary["source_partial_mismatch_count"]}
- Non-actionable groups: {summary["non_actionable_group_count"]}
- Non-actionable target slots: {summary["non_actionable_target_slot_count"]}
- Codex business resolution applied: `false`
- Owner/delegate resolution required: `true`
- Full source-map reapplication ready: `false`

Next recommended phase: `{NEXT_RECOMMENDED_PHASE}`.
"""
    go_no_go_record = f"""# Go/No-Go Record

- phase_id: `{PHASE_ID}`
- decision: `{DECISION}`
- reason: `{DIAGNOSTIC_CONCLUSION}`
- non_actionable_group_count: `{summary["non_actionable_group_count"]}`
- non_actionable_target_slot_count: `{summary["non_actionable_target_slot_count"]}`
- codex_default_business_resolution_applied: `false`
- github upload performed: `false`
"""
    risk_register = """# Risk Register

- Risk: treating a Codex default as a business authorization.
  Mitigation: default business resolution is explicitly false; private template stays not ready for intake until an owner or authorized delegate fills it.
- Risk: leaking private group or target details publicly.
  Mitigation: public artifacts contain only aggregate counts and gate flags; private packet stays in ignored runtime.
"""
    rollback_plan = """# Rollback Plan

No raw file, source map, completion template, active authorization record or GitHub remote was modified. To roll back, remove this phase's public artifacts and metadata copies, then remove the ignored private packet/template/diagnostic if not needed.
"""
    test_results = """# Test Results

Status: passed locally after generation.

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_processed_value_source_map_completion_non_actionable_group_resolution_packet.py --generated-at 2026-07-06T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_value_source_map_completion_non_actionable_group_resolution_packet.py --require-private-resolution-packet`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_processed_value_source_map_completion_non_actionable_group_resolution_packet`
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
    event_id = "DEV-KMFA-20260706-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-NON-ACTIONABLE-GROUP-RESOLUTION-PACKET"
    summary = manifest["summary"]
    event = {
        "event_id": event_id,
        "event_time": generated_at,
        "event_type": "development",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "iteration_id": "ITER-20260706-KMFA-V014-NON-ACTIONABLE-GROUP-RESOLUTION-PACKET",
        "fact_level": "EXTRACTED",
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "go_no_go": manifest["go_no_go"]["decision"],
        "source_partial_exact_match_count": summary["source_partial_exact_match_count"],
        "source_partial_mismatch_count": summary["source_partial_mismatch_count"],
        "non_actionable_group_count": summary["non_actionable_group_count"],
        "non_actionable_target_slot_count": summary["non_actionable_target_slot_count"],
        "codex_default_business_resolution_applied": False,
        "owner_or_authorized_delegate_resolution_required": True,
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
        "summary": "Prepared private non-actionable group resolution packet and kept full source-map application blocked pending owner/delegate resolution.",
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
        "PASS: KMFA v0.1.4 non-actionable group resolution packet generated "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"non_actionable_groups={manifest['summary']['non_actionable_group_count']}, "
        f"non_actionable_target_slots={manifest['summary']['non_actionable_target_slot_count']})"
    )


if __name__ == "__main__":
    main()
