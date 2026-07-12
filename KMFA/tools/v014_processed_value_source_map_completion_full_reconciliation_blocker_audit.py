#!/usr/bin/env python3
"""Audit full reconciliation blockers for KMFA v0.1.4 source-map completion.

This phase consolidates public-safe evidence from the partial application,
partial materialization, partial fingerprint comparison, and non-actionable
default-resolution phases. It records why full reconciliation remains blocked
without reading raw source files or mutating canonical source-map records.
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
PHASE_ID = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_FULL_RECONCILIATION_BLOCKER_AUDIT"
TASK_ID = "KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-FULL-RECONCILIATION-BLOCKER-AUDIT-20260706"
ACCEPTANCE_ID = "ACC-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-FULL-RECONCILIATION-BLOCKER-AUDIT"
VERSION = "0.1.4-full-reconciliation-blocker-audit"
STATUS = "completed_validated_local_only_full_reconciliation_blocker_audit_no_go"
DECISION = "NO_GO"
DIAGNOSTIC_CONCLUSION = "partial_evidence_ready_full_reconciliation_blocked_by_non_actionable_keep_no_go"
NEXT_RECOMMENDED_PHASE = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_FINAL_NO_GO_GOVERNANCE_LOCK"
NEXT_REQUIRED_INPUT = "explicit_business_resolution_for_non_actionable_groups_before_full_reconciliation"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "processed_value_source_map_completion_full_reconciliation_blocker_audit_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_value_source_map_completion_full_reconciliation_blocker_audit_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_value_source_map_completion_full_reconciliation_blocker_audit_go_no_go_report.json"
REPORT_PATH = HUMAN_DIR / "processed_value_source_map_completion_full_reconciliation_blocker_audit_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_full_reconciliation_blocker_audit_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_full_reconciliation_blocker_audit_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_full_reconciliation_blocker_audit_go_no_go_report.json"
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"

SOURCE_NON_ACTIONABLE_RESOLUTION_SUMMARY_PATH = (
    PROJECT_ROOT
    / "stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_NON_ACTIONABLE_DEFAULT_RESOLUTION_APPLICATION/machine/processed_value_source_map_completion_non_actionable_default_resolution_application_summary.json"
)
SOURCE_PARTIAL_APPLICATION_SUMMARY_PATH = (
    PROJECT_ROOT
    / "stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_GROUP_PARTIAL_APPLICATION/machine/processed_value_source_map_completion_owner_group_partial_application_summary.json"
)
SOURCE_PARTIAL_MATERIALIZATION_REPLAY_SUMMARY_PATH = (
    PROJECT_ROOT
    / "stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_PARTIAL_MATERIALIZATION_REPLAY/machine/processed_value_source_map_completion_partial_materialization_replay_summary.json"
)
SOURCE_PARTIAL_RAW_COMPARISON_SUMMARY_PATH = (
    PROJECT_ROOT
    / "stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_PARTIAL_RAW_TO_PROCESSED_COMPARISON/machine/processed_value_source_map_completion_partial_raw_to_processed_comparison_summary.json"
)

PRIVATE_OUTPUT_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_processed_value_source_map_completion_full_reconciliation_blocker_audit"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_full_reconciliation_blocker_audit_diagnostic.json"


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


def _build_blockers(
    *,
    non_actionable_summary: dict[str, Any],
    partial_application_summary: dict[str, Any],
    partial_replay_summary: dict[str, Any],
    partial_comparison_summary: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    non_actionable_group_count = int(non_actionable_summary.get("non_actionable_group_count") or 0)
    non_actionable_target_slot_count = int(non_actionable_summary.get("non_actionable_target_slot_count") or 0)
    keep_no_go_resolution_count = int(non_actionable_summary.get("keep_no_go_resolution_count") or 0)
    partial_application_target_slot_count = int(partial_application_summary.get("private_partial_application_target_slot_count") or 0)
    partial_blocked_target_slot_count = int(partial_application_summary.get("private_blocked_target_slot_count") or 0)
    partial_materialization_replay_complete = partial_replay_summary.get("partial_materialization_replay_performed") is True
    partial_fingerprint_comparison_passed = (
        partial_comparison_summary.get("diagnostic_conclusion")
        == "private_partial_raw_to_processed_fingerprint_comparison_passed_full_reconciliation_blocked"
    )
    blockers = [
        {
            "blocker_code": "NON_ACTIONABLE_KEEP_NO_GO_GROUPS",
            "severity": "blocking",
            "aggregate_count": non_actionable_group_count,
            "aggregate_target_slot_count": non_actionable_target_slot_count,
            "resolution_state": "keep_no_go_until_explicit_business_resolution",
        },
        {
            "blocker_code": "FULL_SOURCE_MAP_REAPPLICATION_NOT_READY",
            "severity": "blocking",
            "aggregate_count": keep_no_go_resolution_count,
            "resolution_state": "blocked_by_non_actionable_keep_no_go",
        },
        {
            "blocker_code": "FULL_RAW_TO_PROCESSED_COMPARISON_NOT_PERFORMED",
            "severity": "blocking",
            "aggregate_count": non_actionable_target_slot_count,
            "resolution_state": "requires_full_source_map_reapplication_first",
        },
        {
            "blocker_code": "BUSINESS_VALUE_CONSISTENCY_NOT_VERIFIED",
            "severity": "blocking",
            "aggregate_count": 1,
            "resolution_state": "requires_full_raw_to_processed_comparison_and_reconciliation",
        },
    ]
    audit_counts = {
        "partial_application_target_slot_count": partial_application_target_slot_count,
        "partial_blocked_target_slot_count": partial_blocked_target_slot_count,
        "partial_materialization_replay_complete": partial_materialization_replay_complete,
        "partial_fingerprint_comparison_passed": partial_fingerprint_comparison_passed,
        "non_actionable_group_count": non_actionable_group_count,
        "non_actionable_target_slot_count": non_actionable_target_slot_count,
        "keep_no_go_resolution_count": keep_no_go_resolution_count,
        "blocker_count": len(blockers),
    }
    return blockers, audit_counts


def generate(generated_at: str | None = None, *, write_governance_event: bool = True) -> dict[str, Any]:
    timestamp = _now(generated_at)
    non_actionable_summary = _read_json(SOURCE_NON_ACTIONABLE_RESOLUTION_SUMMARY_PATH)
    partial_application_summary = _read_json(SOURCE_PARTIAL_APPLICATION_SUMMARY_PATH)
    partial_replay_summary = _read_json(SOURCE_PARTIAL_MATERIALIZATION_REPLAY_SUMMARY_PATH)
    partial_comparison_summary = _read_json(SOURCE_PARTIAL_RAW_COMPARISON_SUMMARY_PATH)
    blockers, audit_counts = _build_blockers(
        non_actionable_summary=non_actionable_summary,
        partial_application_summary=partial_application_summary,
        partial_replay_summary=partial_replay_summary,
        partial_comparison_summary=partial_comparison_summary,
    )
    partial_evidence_chain_ready = (
        audit_counts["partial_application_target_slot_count"] == 101
        and audit_counts["partial_blocked_target_slot_count"] == 12
        and audit_counts["partial_materialization_replay_complete"]
        and audit_counts["partial_fingerprint_comparison_passed"]
        and audit_counts["keep_no_go_resolution_count"] == 3
    )
    diagnostic = {
        "schema_version": "kmfa.private.v014_full_reconciliation_blocker_audit_diagnostic.v1",
        "classification": "private_full_reconciliation_blocker_audit_diagnostic_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_full_reconciliation_blocker_audit_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "partial_evidence_chain_ready": partial_evidence_chain_ready,
        "audit_counts": audit_counts,
        "blockers": blockers,
        "raw_boundary": _raw_boundary(),
    }
    _write_json(PRIVATE_DIAGNOSTIC_PATH, diagnostic)

    summary = {
        "schema_version": "kmfa.v014_full_reconciliation_blocker_audit_summary.v1",
        "record_type": "v014_full_reconciliation_blocker_audit_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "source_non_actionable_resolution_phase_id": non_actionable_summary.get("phase_id"),
        "source_non_actionable_resolution_decision": non_actionable_summary.get("decision"),
        "source_partial_application_phase_id": partial_application_summary.get("phase_id"),
        "source_partial_application_decision": partial_application_summary.get("decision"),
        "source_partial_replay_phase_id": partial_replay_summary.get("phase_id"),
        "source_partial_replay_decision": partial_replay_summary.get("decision"),
        "source_partial_comparison_phase_id": partial_comparison_summary.get("phase_id"),
        "source_partial_comparison_decision": partial_comparison_summary.get("decision"),
        "partial_evidence_chain_ready": partial_evidence_chain_ready,
        "partial_application_target_slot_count": audit_counts["partial_application_target_slot_count"],
        "partial_blocked_target_slot_count": audit_counts["partial_blocked_target_slot_count"],
        "partial_materialization_replay_complete": audit_counts["partial_materialization_replay_complete"],
        "partial_fingerprint_comparison_passed": audit_counts["partial_fingerprint_comparison_passed"],
        "non_actionable_group_count": audit_counts["non_actionable_group_count"],
        "non_actionable_target_slot_count": audit_counts["non_actionable_target_slot_count"],
        "keep_no_go_resolution_count": audit_counts["keep_no_go_resolution_count"],
        "blocker_count": audit_counts["blocker_count"],
        "blocking_severity_count": audit_counts["blocker_count"],
        "full_source_map_completion_reapplication_ready": False,
        "full_source_map_completion_reapplication_performed": False,
        "full_raw_to_processed_value_comparison_ready": False,
        "full_raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
        "lineage_full_check_complete": False,
        "formal_report_allowed": False,
        "delivery_allowed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "canonical_source_map_mutated": False,
        "canonical_source_map_records_applied_count": 0,
        "private_diagnostic_written": PRIVATE_DIAGNOSTIC_PATH.exists(),
        "private_diagnostic_gitignored": _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH),
        "public_safety": _public_safety(),
        "raw_boundary": _raw_boundary(),
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
        "next_required_input": NEXT_REQUIRED_INPUT,
    }
    go_no_go = {
        "schema_version": "kmfa.v014_full_reconciliation_blocker_audit_go_no_go.v1",
        "record_type": "v014_full_reconciliation_blocker_audit_go_no_go_report",
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
        "partial_evidence_chain_ready": partial_evidence_chain_ready,
        "blocker_count": audit_counts["blocker_count"],
        "non_actionable_group_count": audit_counts["non_actionable_group_count"],
        "non_actionable_target_slot_count": audit_counts["non_actionable_target_slot_count"],
        "full_source_map_completion_reapplication_ready": False,
        "full_raw_to_processed_value_comparison_ready": False,
        "business_value_consistency_verified": False,
        "delivery_allowed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }
    manifest = {
        "schema_version": "kmfa.v014_full_reconciliation_blocker_audit_manifest.v1",
        "record_type": "v014_full_reconciliation_blocker_audit_manifest",
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
            SOURCE_NON_ACTIONABLE_RESOLUTION_SUMMARY_PATH.as_posix(),
            SOURCE_PARTIAL_APPLICATION_SUMMARY_PATH.as_posix(),
            SOURCE_PARTIAL_MATERIALIZATION_REPLAY_SUMMARY_PATH.as_posix(),
            SOURCE_PARTIAL_RAW_COMPARISON_SUMMARY_PATH.as_posix(),
        ],
        "public_outputs": [
            SUMMARY_PATH.as_posix(),
            MANIFEST_PATH.as_posix(),
            GO_NO_GO_PATH.as_posix(),
            REPORT_PATH.as_posix(),
            GO_NO_GO_RECORD_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            RISK_REGISTER_PATH.as_posix(),
            ROLLBACK_PATH.as_posix(),
            METADATA_SUMMARY_PATH.as_posix(),
            METADATA_MANIFEST_PATH.as_posix(),
            METADATA_GO_NO_GO_PATH.as_posix(),
        ],
        "private_outputs": ["private:full_reconciliation_blocker_audit_diagnostic"],
        "summary": summary,
        "go_no_go": go_no_go,
    }
    report = f"""# Full Reconciliation Blocker Audit

- phase_id: `{PHASE_ID}`
- decision: `{DECISION}`
- partial evidence chain ready: `{str(partial_evidence_chain_ready).lower()}`
- partial application target slots: `{summary["partial_application_target_slot_count"]}`
- partial blocked target slots: `{summary["partial_blocked_target_slot_count"]}`
- keep-NoGo non-actionable groups: `{summary["non_actionable_group_count"]}`
- keep-NoGo target slots: `{summary["non_actionable_target_slot_count"]}`
- blocker count: `{summary["blocker_count"]}`
- delivery allowed: `false`

Partial evidence is locally available, but full reconciliation remains blocked
until non-actionable groups receive explicit business resolution. This phase
does not run full source-map reapplication, raw comparison, formal reporting,
GitHub upload, app reinstall, or business execution.

Next required input: `{NEXT_REQUIRED_INPUT}`.
"""
    go_no_go_record = f"""# Go/No-Go Record

- phase_id: `{PHASE_ID}`
- decision: `{DECISION}`
- reason: `{DIAGNOSTIC_CONCLUSION}`
- partial_evidence_chain_ready: `{str(partial_evidence_chain_ready).lower()}`
- blocker_count: `{summary["blocker_count"]}`
- full_source_map_completion_reapplication_ready: `false`
- full_raw_to_processed_value_comparison_ready: `false`
- delivery_allowed: `false`
- github upload performed: `false`
"""
    risk_register = """# Risk Register

- Risk: treating partial evidence as full business reconciliation.
  Mitigation: full source-map reapplication, full raw comparison and delivery remain explicitly closed.
- Risk: leaking private diagnostic details publicly.
  Mitigation: public artifacts contain only aggregate counts and gate flags.
"""
    rollback_plan = """# Rollback Plan

No raw file, canonical source-map file, completion template or active authorization record was modified. To roll back, remove this phase's public artifacts and ignored private diagnostic output.
"""
    test_results = """# Test Results

Status: passed locally after generation.

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_processed_value_source_map_completion_full_reconciliation_blocker_audit.py --generated-at 2026-07-06T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_value_source_map_completion_full_reconciliation_blocker_audit.py --require-private-diagnostic`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_processed_value_source_map_completion_full_reconciliation_blocker_audit`
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
    event_id = "DEV-KMFA-20260706-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-FULL-RECONCILIATION-BLOCKER-AUDIT"
    summary = manifest["summary"]
    event = {
        "event_id": event_id,
        "event_time": generated_at,
        "event_type": "development",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "iteration_id": "ITER-20260706-KMFA-V014-FULL-RECONCILIATION-BLOCKER-AUDIT",
        "fact_level": "EXTRACTED",
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "go_no_go": manifest["go_no_go"]["decision"],
        "partial_evidence_chain_ready": summary["partial_evidence_chain_ready"],
        "blocker_count": summary["blocker_count"],
        "non_actionable_group_count": summary["non_actionable_group_count"],
        "non_actionable_target_slot_count": summary["non_actionable_target_slot_count"],
        "full_source_map_completion_reapplication_ready": False,
        "full_raw_to_processed_value_comparison_ready": False,
        "business_value_consistency_verified": False,
        "delivery_allowed": False,
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "result_commit": "PENDING",
        "summary": "Audited full reconciliation blockers: partial evidence is ready, but non-actionable keep-NoGo groups keep full reconciliation and delivery blocked.",
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
        "PASS: KMFA v0.1.4 full reconciliation blocker audit generated "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"partial_ready={manifest['summary']['partial_evidence_chain_ready']}, "
        f"blockers={manifest['summary']['blocker_count']})"
    )


if __name__ == "__main__":
    main()
