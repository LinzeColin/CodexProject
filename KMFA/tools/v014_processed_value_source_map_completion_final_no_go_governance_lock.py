#!/usr/bin/env python3
"""Lock final NO-GO governance for KMFA v0.1.4 source-map completion.

This phase converts the current full-reconciliation blocker audit into a
public-safe governance lock. It does not claim delivery, run raw comparison,
mutate source maps, upload to GitHub, reinstall the app, or execute business
actions.
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
PHASE_ID = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_FINAL_NO_GO_GOVERNANCE_LOCK"
TASK_ID = "KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-FINAL-NO-GO-GOVERNANCE-LOCK-20260706"
ACCEPTANCE_ID = "ACC-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-FINAL-NO-GO-GOVERNANCE-LOCK"
VERSION = "0.1.4-final-no-go-governance-lock"
STATUS = "completed_validated_local_only_final_no_go_governance_lock"
DECISION = "NO_GO"
DIAGNOSTIC_CONCLUSION = "final_no_go_governance_locked_full_reconciliation_blocked"
NEXT_RECOMMENDED_PHASE = "AWAIT_EXPLICIT_BUSINESS_RESOLUTION_OR_PREPARE_OWNER_DIAGNOSTIC_PACKET"
NEXT_REQUIRED_INPUT = "explicit_business_resolution_for_non_actionable_groups_before_full_reconciliation"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "processed_value_source_map_completion_final_no_go_governance_lock_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_value_source_map_completion_final_no_go_governance_lock_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_value_source_map_completion_final_no_go_governance_lock_go_no_go_report.json"
REPORT_PATH = HUMAN_DIR / "processed_value_source_map_completion_final_no_go_governance_lock_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_final_no_go_governance_lock_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_final_no_go_governance_lock_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_final_no_go_governance_lock_go_no_go_report.json"
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"

SOURCE_BLOCKER_AUDIT_SUMMARY_PATH = (
    PROJECT_ROOT
    / "stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_FULL_RECONCILIATION_BLOCKER_AUDIT/machine/processed_value_source_map_completion_full_reconciliation_blocker_audit_summary.json"
)
SOURCE_BLOCKER_AUDIT_GO_NO_GO_PATH = (
    PROJECT_ROOT
    / "stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_FULL_RECONCILIATION_BLOCKER_AUDIT/machine/processed_value_source_map_completion_full_reconciliation_blocker_audit_go_no_go_report.json"
)

PRIVATE_OUTPUT_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_processed_value_source_map_completion_final_no_go_governance_lock"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_final_no_go_governance_lock_diagnostic.json"


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


def generate(generated_at: str | None = None, *, write_governance_event: bool = True) -> dict[str, Any]:
    timestamp = _now(generated_at)
    blocker_summary = _read_json(SOURCE_BLOCKER_AUDIT_SUMMARY_PATH)
    blocker_go_no_go = _read_json(SOURCE_BLOCKER_AUDIT_GO_NO_GO_PATH)
    partial_ready = blocker_summary.get("partial_evidence_chain_ready") is True
    blocker_count = int(blocker_summary.get("blocker_count") or 0)
    non_actionable_group_count = int(blocker_summary.get("non_actionable_group_count") or 0)
    non_actionable_target_slot_count = int(blocker_summary.get("non_actionable_target_slot_count") or 0)
    lock_active = (
        blocker_summary.get("decision") == "NO_GO"
        and blocker_go_no_go.get("decision") == "NO_GO"
        and partial_ready
        and blocker_count == 4
        and non_actionable_group_count == 3
        and non_actionable_target_slot_count == 12
    )
    locked_gates = {
        "delivery_allowed": False,
        "formal_report_allowed": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "business_execution_allowed": False,
        "full_source_map_completion_reapplication_allowed": False,
        "full_raw_to_processed_value_comparison_allowed": False,
        "business_value_consistency_claim_allowed": False,
    }
    diagnostic = {
        "schema_version": "kmfa.private.v014_final_no_go_governance_lock_diagnostic.v1",
        "classification": "private_final_no_go_governance_lock_diagnostic_do_not_commit",
        "record_type": "v014_final_no_go_governance_lock_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "lock_active": lock_active,
        "source_blocker_audit_phase_id": blocker_summary.get("phase_id"),
        "source_blocker_audit_decision": blocker_summary.get("decision"),
        "partial_evidence_chain_ready": partial_ready,
        "blocker_count": blocker_count,
        "non_actionable_group_count": non_actionable_group_count,
        "non_actionable_target_slot_count": non_actionable_target_slot_count,
        "locked_gates": locked_gates,
        "unlock_required_input": NEXT_REQUIRED_INPUT,
        "raw_boundary": _raw_boundary(),
    }
    _write_json(PRIVATE_DIAGNOSTIC_PATH, diagnostic)

    summary = {
        "schema_version": "kmfa.v014_final_no_go_governance_lock_summary.v1",
        "record_type": "v014_final_no_go_governance_lock_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "final_no_go_governance_lock_active": lock_active,
        "source_blocker_audit_phase_id": blocker_summary.get("phase_id"),
        "source_blocker_audit_decision": blocker_summary.get("decision"),
        "source_blocker_audit_go_no_go_decision": blocker_go_no_go.get("decision"),
        "partial_evidence_chain_ready": partial_ready,
        "partial_application_target_slot_count": int(blocker_summary.get("partial_application_target_slot_count") or 0),
        "partial_blocked_target_slot_count": int(blocker_summary.get("partial_blocked_target_slot_count") or 0),
        "partial_materialization_replay_complete": blocker_summary.get("partial_materialization_replay_complete") is True,
        "partial_fingerprint_comparison_passed": blocker_summary.get("partial_fingerprint_comparison_passed") is True,
        "blocker_count": blocker_count,
        "blocking_severity_count": int(blocker_summary.get("blocking_severity_count") or 0),
        "non_actionable_group_count": non_actionable_group_count,
        "non_actionable_target_slot_count": non_actionable_target_slot_count,
        "keep_no_go_resolution_count": int(blocker_summary.get("keep_no_go_resolution_count") or 0),
        "unlock_required_input": NEXT_REQUIRED_INPUT,
        "delivery_allowed": False,
        "formal_report_allowed": False,
        "github_upload_performed": False,
        "github_upload_allowed": False,
        "app_reinstall_performed": False,
        "app_reinstall_allowed": False,
        "business_execution_performed": False,
        "business_execution_allowed": False,
        "full_source_map_completion_reapplication_ready": False,
        "full_source_map_completion_reapplication_performed": False,
        "full_raw_to_processed_value_comparison_ready": False,
        "full_raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
        "lineage_full_check_complete": False,
        "canonical_source_map_mutated": False,
        "canonical_source_map_records_applied_count": 0,
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "private_diagnostic_written": PRIVATE_DIAGNOSTIC_PATH.exists(),
        "private_diagnostic_gitignored": _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH),
        "public_safety": _public_safety(),
        "raw_boundary": _raw_boundary(),
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
        "next_required_input": NEXT_REQUIRED_INPUT,
    }
    go_no_go = {
        "schema_version": "kmfa.v014_final_no_go_governance_lock_go_no_go.v1",
        "record_type": "v014_final_no_go_governance_lock_go_no_go_report",
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
        "final_no_go_governance_lock_active": lock_active,
        "partial_evidence_chain_ready": partial_ready,
        "blocker_count": blocker_count,
        "non_actionable_group_count": non_actionable_group_count,
        "non_actionable_target_slot_count": non_actionable_target_slot_count,
        "delivery_allowed": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "business_execution_allowed": False,
        "full_source_map_completion_reapplication_ready": False,
        "full_raw_to_processed_value_comparison_ready": False,
        "business_value_consistency_verified": False,
    }
    manifest = {
        "schema_version": "kmfa.v014_final_no_go_governance_lock_manifest.v1",
        "record_type": "v014_final_no_go_governance_lock_manifest",
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
            SOURCE_BLOCKER_AUDIT_SUMMARY_PATH.as_posix(),
            SOURCE_BLOCKER_AUDIT_GO_NO_GO_PATH.as_posix(),
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
        "private_outputs": ["private:final_no_go_governance_lock_diagnostic"],
        "summary": summary,
        "go_no_go": go_no_go,
    }
    report = f"""# Final NO-GO Governance Lock

- phase_id: `{PHASE_ID}`
- decision: `{DECISION}`
- lock active: `{str(lock_active).lower()}`
- partial evidence chain ready: `{str(partial_ready).lower()}`
- blocker count: `{blocker_count}`
- non-actionable groups: `{non_actionable_group_count}`
- non-actionable target slots: `{non_actionable_target_slot_count}`
- delivery allowed: `false`

This phase locks the current state as NO-GO governance evidence. It is not a
delivery, release, GitHub upload, app reinstall, formal report, or business-use
approval. Full reconciliation can only reopen after explicit business
resolution for the non-actionable groups.

Next required input: `{NEXT_REQUIRED_INPUT}`.
"""
    go_no_go_record = f"""# Go/No-Go Record

- phase_id: `{PHASE_ID}`
- decision: `{DECISION}`
- reason: `{DIAGNOSTIC_CONCLUSION}`
- final_no_go_governance_lock_active: `{str(lock_active).lower()}`
- delivery_allowed: `false`
- github_upload_allowed: `false`
- app_reinstall_allowed: `false`
- business_execution_allowed: `false`
"""
    risk_register = """# Risk Register

- Risk: treating the NO-GO lock as final delivery.
  Mitigation: delivery, formal report, GitHub upload, app reinstall and business execution remain explicitly blocked.
- Risk: weakening raw/private boundary while preserving evidence.
  Mitigation: this phase reads only public-safe summaries and writes private diagnostics to ignored runtime.
"""
    rollback_plan = """# Rollback Plan

No raw file, canonical source-map file, completion template or active authorization record was modified. To roll back, remove this phase's public artifacts and ignored private diagnostic output.
"""
    test_results = """# Test Results

Status: passed locally after generation.

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_processed_value_source_map_completion_final_no_go_governance_lock.py --generated-at 2026-07-06T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_value_source_map_completion_final_no_go_governance_lock.py --require-private-diagnostic`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_processed_value_source_map_completion_final_no_go_governance_lock`
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
    event_id = "DEV-KMFA-20260706-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-FINAL-NO-GO-GOVERNANCE-LOCK"
    summary = manifest["summary"]
    event = {
        "event_id": event_id,
        "event_time": generated_at,
        "event_type": "development",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "iteration_id": "ITER-20260706-KMFA-V014-FINAL-NO-GO-GOVERNANCE-LOCK",
        "fact_level": "EXTRACTED",
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "go_no_go": manifest["go_no_go"]["decision"],
        "final_no_go_governance_lock_active": summary["final_no_go_governance_lock_active"],
        "partial_evidence_chain_ready": summary["partial_evidence_chain_ready"],
        "blocker_count": summary["blocker_count"],
        "delivery_allowed": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "business_execution_allowed": False,
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "result_commit": "PENDING",
        "summary": "Locked final NO-GO governance for current source-map completion state; delivery and execution remain blocked until explicit business resolution.",
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
        "PASS: KMFA v0.1.4 final NO-GO governance lock generated "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"lock={manifest['summary']['final_no_go_governance_lock_active']}, "
        f"blockers={manifest['summary']['blocker_count']})"
    )


if __name__ == "__main__":
    main()
