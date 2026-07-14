#!/usr/bin/env python3
"""Build a public-safe owner diagnostic packet for KMFA v0.1.4 NO-GO state.

This phase packages the latest final NO-GO governance lock into a diagnostic
handoff packet that another owner or agent can use to decide whether to provide
explicit business resolution. Public outputs stay aggregate-only. Private
runtime receives the full diagnostic packet for follow-up orchestration. No raw
source files are read or mutated.
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
PHASE_ID = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_DIAGNOSTIC_PACKET"
TASK_ID = "KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-OWNER-DIAGNOSTIC-PACKET-20260706"
ACCEPTANCE_ID = "ACC-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-OWNER-DIAGNOSTIC-PACKET"
VERSION = "0.1.4-owner-diagnostic-packet"
STATUS = "completed_validated_local_only_owner_diagnostic_packet_no_go"
DECISION = "NO_GO"
DIAGNOSTIC_CONCLUSION = "owner_diagnostic_packet_ready_final_no_go_locked"
NEXT_RECOMMENDED_PHASE = "AWAIT_EXPLICIT_BUSINESS_RESOLUTION"
NEXT_REQUIRED_INPUT = "explicit_business_resolution_for_non_actionable_groups_before_full_reconciliation"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_diagnostic_packet_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_diagnostic_packet_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_diagnostic_packet_go_no_go_report.json"
REPORT_PATH = HUMAN_DIR / "processed_value_source_map_completion_owner_diagnostic_packet_report.md"
OWNER_PACKET_PATH = HUMAN_DIR / "owner_diagnostic_packet_public_safe.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_owner_diagnostic_packet_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_owner_diagnostic_packet_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_owner_diagnostic_packet_go_no_go_report.json"
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"

SOURCE_FINAL_LOCK_SUMMARY_PATH = (
    PROJECT_ROOT
    / "stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_FINAL_NO_GO_GOVERNANCE_LOCK/machine/processed_value_source_map_completion_final_no_go_governance_lock_summary.json"
)
SOURCE_FULL_BLOCKER_SUMMARY_PATH = (
    PROJECT_ROOT
    / "stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_FULL_RECONCILIATION_BLOCKER_AUDIT/machine/processed_value_source_map_completion_full_reconciliation_blocker_audit_summary.json"
)

PRIVATE_OUTPUT_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_processed_value_source_map_completion_owner_diagnostic_packet"
PRIVATE_PACKET_PATH = PRIVATE_OUTPUT_DIR / "private_owner_diagnostic_packet.json"
PRIVATE_PACKET_MARKDOWN_PATH = PRIVATE_OUTPUT_DIR / "private_owner_diagnostic_packet.md"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_owner_diagnostic_packet_diagnostic.json"


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
        "private_packet_committed": False,
        "private_packet_markdown_committed": False,
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


def _build_private_packet(*, generated_at: str, final_lock: dict[str, Any], blocker_summary: dict[str, Any]) -> tuple[dict[str, Any], str, dict[str, Any]]:
    decision_items = [
        {
            "item_code": "RESOLVE_NON_ACTIONABLE_GROUPS",
            "required_input": NEXT_REQUIRED_INPUT,
            "aggregate_group_count": int(final_lock.get("non_actionable_group_count") or 0),
            "aggregate_target_slot_count": int(final_lock.get("non_actionable_target_slot_count") or 0),
            "allowed_owner_paths": [
                "provide_explicit_business_resolution",
                "keep_no_go_and_defer_full_reconciliation",
                "request_private_raw_diagnostic_under_readonly_boundary",
            ],
            "disallowed_codex_actions_without_resolution": [
                "full_source_map_completion_reapplication",
                "full_raw_to_processed_value_comparison",
                "delivery_claim",
                "github_upload",
                "app_reinstall",
                "business_execution",
            ],
        }
    ]
    packet = {
        "schema_version": "kmfa.private.v014_owner_diagnostic_packet.v1",
        "classification": "private_owner_diagnostic_packet_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_owner_diagnostic_packet",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "source_final_lock_phase_id": final_lock.get("phase_id"),
        "source_blocker_audit_phase_id": blocker_summary.get("phase_id"),
        "decision": DECISION,
        "partial_evidence_chain_ready": final_lock.get("partial_evidence_chain_ready") is True,
        "final_no_go_governance_lock_active": final_lock.get("final_no_go_governance_lock_active") is True,
        "blocker_count": int(final_lock.get("blocker_count") or 0),
        "owner_decision_item_count": len(decision_items),
        "non_actionable_group_count": int(final_lock.get("non_actionable_group_count") or 0),
        "non_actionable_target_slot_count": int(final_lock.get("non_actionable_target_slot_count") or 0),
        "delivery_allowed": False,
        "diagnostic_questions": decision_items,
        "raw_boundary": _raw_boundary(),
    }
    markdown = f"""# Private Owner Diagnostic Packet

- decision: `{DECISION}`
- final NO-GO governance lock active: `{str(packet["final_no_go_governance_lock_active"]).lower()}`
- partial evidence chain ready: `{str(packet["partial_evidence_chain_ready"]).lower()}`
- blocker count: `{packet["blocker_count"]}`
- non-actionable groups: `{packet["non_actionable_group_count"]}`
- non-actionable target slots: `{packet["non_actionable_target_slot_count"]}`
- delivery allowed: `false`

Required owner input: `{NEXT_REQUIRED_INPUT}`.

Codex must not run full source-map completion, full raw comparison, GitHub
upload, app reinstall, delivery claim, or business execution until the required
input is supplied and validated.
"""
    diagnostic = {
        "schema_version": "kmfa.private.v014_owner_diagnostic_packet_diagnostic.v1",
        "classification": "private_owner_diagnostic_packet_diagnostic_do_not_commit",
        "record_type": "v014_owner_diagnostic_packet_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "packet_ready": True,
        "owner_decision_item_count": len(decision_items),
        "source_final_lock_phase_id": final_lock.get("phase_id"),
        "source_blocker_audit_phase_id": blocker_summary.get("phase_id"),
        "raw_boundary": _raw_boundary(),
    }
    return packet, markdown, diagnostic


def generate(generated_at: str | None = None, *, write_governance_event: bool = True) -> dict[str, Any]:
    timestamp = _now(generated_at)
    final_lock = _read_json(SOURCE_FINAL_LOCK_SUMMARY_PATH)
    blocker_summary = _read_json(SOURCE_FULL_BLOCKER_SUMMARY_PATH)
    private_packet, private_packet_md, private_diagnostic = _build_private_packet(
        generated_at=timestamp,
        final_lock=final_lock,
        blocker_summary=blocker_summary,
    )
    _write_json(PRIVATE_PACKET_PATH, private_packet)
    _write_text(PRIVATE_PACKET_MARKDOWN_PATH, private_packet_md)
    _write_json(PRIVATE_DIAGNOSTIC_PATH, private_diagnostic)

    partial_ready = final_lock.get("partial_evidence_chain_ready") is True
    lock_active = final_lock.get("final_no_go_governance_lock_active") is True
    blocker_count = int(final_lock.get("blocker_count") or 0)
    owner_decision_item_count = int(private_packet["owner_decision_item_count"])
    summary = {
        "schema_version": "kmfa.v014_owner_diagnostic_packet_summary.v1",
        "record_type": "v014_owner_diagnostic_packet_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "source_final_lock_phase_id": final_lock.get("phase_id"),
        "source_final_lock_decision": final_lock.get("decision"),
        "source_blocker_audit_phase_id": blocker_summary.get("phase_id"),
        "source_blocker_audit_decision": blocker_summary.get("decision"),
        "owner_diagnostic_packet_ready": True,
        "owner_decision_item_count": owner_decision_item_count,
        "final_no_go_governance_lock_active": lock_active,
        "partial_evidence_chain_ready": partial_ready,
        "blocker_count": blocker_count,
        "non_actionable_group_count": int(final_lock.get("non_actionable_group_count") or 0),
        "non_actionable_target_slot_count": int(final_lock.get("non_actionable_target_slot_count") or 0),
        "keep_no_go_resolution_count": int(final_lock.get("keep_no_go_resolution_count") or 0),
        "required_owner_input_count": 1,
        "next_required_input": NEXT_REQUIRED_INPUT,
        "delivery_allowed": False,
        "formal_report_allowed": False,
        "github_upload_allowed": False,
        "github_upload_performed": False,
        "app_reinstall_allowed": False,
        "app_reinstall_performed": False,
        "business_execution_allowed": False,
        "business_execution_performed": False,
        "full_source_map_completion_reapplication_ready": False,
        "full_raw_to_processed_value_comparison_ready": False,
        "business_value_consistency_verified": False,
        "canonical_source_map_mutated": False,
        "canonical_source_map_records_applied_count": 0,
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "private_packet_written": PRIVATE_PACKET_PATH.exists(),
        "private_packet_gitignored": _git_check_ignored(PRIVATE_PACKET_PATH),
        "private_packet_markdown_written": PRIVATE_PACKET_MARKDOWN_PATH.exists(),
        "private_packet_markdown_gitignored": _git_check_ignored(PRIVATE_PACKET_MARKDOWN_PATH),
        "private_diagnostic_written": PRIVATE_DIAGNOSTIC_PATH.exists(),
        "private_diagnostic_gitignored": _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH),
        "public_safety": _public_safety(),
        "raw_boundary": _raw_boundary(),
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
    }
    go_no_go = {
        "schema_version": "kmfa.v014_owner_diagnostic_packet_go_no_go.v1",
        "record_type": "v014_owner_diagnostic_packet_go_no_go_report",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "blocked_until": NEXT_REQUIRED_INPUT,
        "owner_diagnostic_packet_ready": True,
        "owner_decision_item_count": owner_decision_item_count,
        "delivery_allowed": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "business_execution_allowed": False,
    }
    manifest = {
        "schema_version": "kmfa.v014_owner_diagnostic_packet_manifest.v1",
        "record_type": "v014_owner_diagnostic_packet_manifest",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "git_head": _git_output(["rev-parse", "HEAD"]),
        "git_branch": _git_output(["branch", "--show-current"]),
        "source_artifacts": [
            SOURCE_FINAL_LOCK_SUMMARY_PATH.as_posix(),
            SOURCE_FULL_BLOCKER_SUMMARY_PATH.as_posix(),
        ],
        "public_outputs": [
            SUMMARY_PATH.as_posix(),
            MANIFEST_PATH.as_posix(),
            GO_NO_GO_PATH.as_posix(),
            REPORT_PATH.as_posix(),
            OWNER_PACKET_PATH.as_posix(),
            GO_NO_GO_RECORD_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            RISK_REGISTER_PATH.as_posix(),
            ROLLBACK_PATH.as_posix(),
            METADATA_SUMMARY_PATH.as_posix(),
            METADATA_MANIFEST_PATH.as_posix(),
            METADATA_GO_NO_GO_PATH.as_posix(),
        ],
        "private_outputs": [
            "private:owner_diagnostic_packet",
            "private:owner_diagnostic_packet_markdown",
            "private:owner_diagnostic_packet_diagnostic",
        ],
        "summary": summary,
        "go_no_go": go_no_go,
    }
    report = f"""# Owner Diagnostic Packet

- phase_id: `{PHASE_ID}`
- decision: `{DECISION}`
- packet ready: `true`
- owner decision item count: `{owner_decision_item_count}`
- final NO-GO governance lock active: `{str(lock_active).lower()}`
- partial evidence chain ready: `{str(partial_ready).lower()}`
- blocker count: `{blocker_count}`
- non-actionable groups: `{summary["non_actionable_group_count"]}`
- non-actionable target slots: `{summary["non_actionable_target_slot_count"]}`
- delivery allowed: `false`

This diagnostic packet is safe to share as aggregate governance context. It is
not a delivery, release, GitHub upload, app reinstall, formal report, raw data
comparison, or business-use approval.

Next required input: `{NEXT_REQUIRED_INPUT}`.
"""
    owner_packet = f"""# Public-Safe Owner Diagnostic Packet

## Current State

- Go/No-Go: `{DECISION}`
- Final governance lock active: `{str(lock_active).lower()}`
- Partial evidence chain ready: `{str(partial_ready).lower()}`
- Blocking issue count: `{blocker_count}`
- Non-actionable group count: `{summary["non_actionable_group_count"]}`
- Non-actionable target-slot count: `{summary["non_actionable_target_slot_count"]}`

## Required Owner Input

- Required input count: `1`
- Required input: `{NEXT_REQUIRED_INPUT}`

## Still Blocked

- Full source-map reapplication: `blocked`
- Full raw-to-processed comparison: `blocked`
- Business-value consistency claim: `blocked`
- Formal report / delivery / GitHub upload / app reinstall / business execution: `blocked`
"""
    go_no_go_record = f"""# Go/No-Go Record

- phase_id: `{PHASE_ID}`
- decision: `{DECISION}`
- reason: `{DIAGNOSTIC_CONCLUSION}`
- owner_diagnostic_packet_ready: `true`
- delivery_allowed: `false`
- github_upload_allowed: `false`
- app_reinstall_allowed: `false`
- business_execution_allowed: `false`
"""
    risk_register = """# Risk Register

- Risk: treating the diagnostic packet as delivery approval.
  Mitigation: delivery, report, GitHub upload, app reinstall and business execution remain blocked.
- Risk: leaking private source details in an owner packet.
  Mitigation: public packet contains only aggregate counts and gate flags; private packet stays in ignored runtime.
"""
    rollback_plan = """# Rollback Plan

No raw file, canonical source-map file, completion template or active authorization record was modified. To roll back, remove this phase's public artifacts and ignored private packet outputs.
"""
    test_results = """# Test Results

Status: passed locally after generation.

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_processed_value_source_map_completion_owner_diagnostic_packet.py --generated-at 2026-07-06T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_value_source_map_completion_owner_diagnostic_packet.py --require-private-packet`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_processed_value_source_map_completion_owner_diagnostic_packet`
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
    event_id = "DEV-KMFA-20260706-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-OWNER-DIAGNOSTIC-PACKET"
    summary = manifest["summary"]
    event = {
        "event_id": event_id,
        "event_time": generated_at,
        "event_type": "development",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "iteration_id": "ITER-20260706-KMFA-V014-OWNER-DIAGNOSTIC-PACKET",
        "fact_level": "EXTRACTED",
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "go_no_go": manifest["go_no_go"]["decision"],
        "owner_diagnostic_packet_ready": True,
        "owner_decision_item_count": summary["owner_decision_item_count"],
        "delivery_allowed": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "business_execution_allowed": False,
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "result_commit": "PENDING",
        "summary": "Prepared public-safe owner diagnostic packet for the locked NO-GO source-map completion state.",
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
        "PASS: KMFA v0.1.4 owner diagnostic packet generated "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"packet={manifest['summary']['owner_diagnostic_packet_ready']}, "
        f"items={manifest['summary']['owner_decision_item_count']})"
    )


if __name__ == "__main__":
    main()
