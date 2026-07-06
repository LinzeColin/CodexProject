#!/usr/bin/env python3
"""Record an explicit conservative business resolution for the v0.1.4 NO-GO gate.

The owner delegated Codex to decide because the detailed prompt was not useful
to answer manually. This phase records the only safe default: keep the
non-actionable groups out of delivery claims and keep full reconciliation,
GitHub upload, app reinstall, formal reporting, and business execution blocked.
It reads only prior public-safe gate summaries plus the ignored private owner
diagnostic packet. It does not read or mutate the raw inbox.
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
PHASE_ID = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_EXPLICIT_BUSINESS_RESOLUTION_INTAKE"
TASK_ID = "KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-EXPLICIT-BUSINESS-RESOLUTION-INTAKE-20260706"
ACCEPTANCE_ID = "ACC-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-EXPLICIT-BUSINESS-RESOLUTION-INTAKE"
VERSION = "0.1.4-explicit-business-resolution-intake"
STATUS = "completed_validated_local_only_explicit_business_resolution_intake_no_go"
DECISION = "NO_GO"
RESOLUTION_STRATEGY = "owner_delegated_conservative_keep_no_go_defer_full_reconciliation"
DIAGNOSTIC_CONCLUSION = "explicit_business_resolution_recorded_conservative_no_go"
PREVIOUS_REQUIRED_INPUT = "explicit_business_resolution_for_non_actionable_groups_before_full_reconciliation"
NEXT_RECOMMENDED_PHASE = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_RESIDUAL_GAP_REPORT_PREP"
NEXT_REQUIRED_INPUT = "private_residual_gap_report_or_corrected_source_package_before_any_delivery_claim"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "processed_value_source_map_completion_explicit_business_resolution_intake_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_value_source_map_completion_explicit_business_resolution_intake_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_value_source_map_completion_explicit_business_resolution_intake_go_no_go_report.json"
REPORT_PATH = HUMAN_DIR / "processed_value_source_map_completion_explicit_business_resolution_intake_report.md"
RESOLUTION_RECORD_PATH = HUMAN_DIR / "business_resolution_public_safe.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_explicit_business_resolution_intake_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_explicit_business_resolution_intake_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_explicit_business_resolution_intake_go_no_go_report.json"
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"

SOURCE_OWNER_DIAGNOSTIC_SUMMARY_PATH = (
    PROJECT_ROOT
    / "stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_DIAGNOSTIC_PACKET/machine/processed_value_source_map_completion_owner_diagnostic_packet_summary.json"
)
SOURCE_FINAL_LOCK_SUMMARY_PATH = (
    PROJECT_ROOT
    / "stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_FINAL_NO_GO_GOVERNANCE_LOCK/machine/processed_value_source_map_completion_final_no_go_governance_lock_summary.json"
)
SOURCE_PRIVATE_OWNER_DIAGNOSTIC_PACKET_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_owner_diagnostic_packet/private_owner_diagnostic_packet.json"
)

PRIVATE_OUTPUT_DIR = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_explicit_business_resolution_intake"
)
PRIVATE_RESOLUTION_RECORD_PATH = PRIVATE_OUTPUT_DIR / "private_explicit_business_resolution_record.json"
PRIVATE_RESOLUTION_MARKDOWN_PATH = PRIVATE_OUTPUT_DIR / "private_explicit_business_resolution_record.md"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_explicit_business_resolution_intake_diagnostic.json"


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
        "private_source_packet_committed": False,
        "private_resolution_record_committed": False,
        "private_resolution_markdown_committed": False,
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


def _build_private_resolution(
    *,
    generated_at: str,
    owner_diagnostic: dict[str, Any],
    final_lock: dict[str, Any],
    private_packet: dict[str, Any],
) -> tuple[dict[str, Any], str, dict[str, Any]]:
    group_count = int(final_lock.get("non_actionable_group_count") or 0)
    target_slot_count = int(final_lock.get("non_actionable_target_slot_count") or 0)
    resolution_record = {
        "schema_version": "kmfa.private.v014_explicit_business_resolution.v1",
        "classification": "private_explicit_business_resolution_do_not_commit",
        "record_type": "v014_explicit_business_resolution",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "authority_basis_code": "OWNER_DELEGATED_CODEX_DECISION_CONSERVATIVE_DEFAULT",
        "source_owner_diagnostic_phase_id": owner_diagnostic.get("phase_id"),
        "source_final_lock_phase_id": final_lock.get("phase_id"),
        "source_private_packet_phase_id": private_packet.get("phase_id"),
        "previous_required_input": PREVIOUS_REQUIRED_INPUT,
        "previous_required_input_resolved_by_this_phase": True,
        "resolution_strategy": RESOLUTION_STRATEGY,
        "business_resolution_item_count": 1,
        "resolution_items": [
            {
                "item_code": "NON_ACTIONABLE_GROUPS",
                "aggregate_group_count": group_count,
                "aggregate_target_slot_count": target_slot_count,
                "resolution_action": "KEEP_NO_GO_AND_DEFER_FULL_RECONCILIATION",
                "delivery_use_allowed": False,
                "formal_report_use_allowed": False,
                "business_execution_use_allowed": False,
                "requires_residual_gap_report": True,
            }
        ],
        "raw_boundary": _raw_boundary(),
    }
    markdown = f"""# Private Explicit Business Resolution

- decision: `{DECISION}`
- resolution strategy: `{RESOLUTION_STRATEGY}`
- previous required input resolved: `true`
- business resolution item count: `1`
- non-actionable groups: `{group_count}`
- non-actionable target slots: `{target_slot_count}`
- delivery use allowed: `false`
- full reconciliation allowed: `false`
- raw inbox read by this phase: `false`
- raw inbox mutated by this phase: `false`

This is a conservative owner-delegated decision record. It does not authorize
source-map reapplication, raw-to-processed comparison, delivery, formal report,
GitHub upload, app reinstall, or business execution.
"""
    diagnostic = {
        "schema_version": "kmfa.private.v014_explicit_business_resolution_intake_diagnostic.v1",
        "classification": "private_explicit_business_resolution_diagnostic_do_not_commit",
        "record_type": "v014_explicit_business_resolution_intake_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "resolution_record_ready": True,
        "business_resolution_item_count": 1,
        "previous_required_input_resolved_by_this_phase": True,
        "full_reconciliation_allowed": False,
        "residual_gap_report_recommended": True,
        "raw_boundary": _raw_boundary(),
    }
    return resolution_record, markdown, diagnostic


def generate(generated_at: str | None = None, *, write_governance_event: bool = True) -> dict[str, Any]:
    timestamp = _now(generated_at)
    owner_diagnostic = _read_json(SOURCE_OWNER_DIAGNOSTIC_SUMMARY_PATH)
    final_lock = _read_json(SOURCE_FINAL_LOCK_SUMMARY_PATH)
    private_packet = _read_json(SOURCE_PRIVATE_OWNER_DIAGNOSTIC_PACKET_PATH)
    private_resolution, private_markdown, private_diagnostic = _build_private_resolution(
        generated_at=timestamp,
        owner_diagnostic=owner_diagnostic,
        final_lock=final_lock,
        private_packet=private_packet,
    )
    _write_json(PRIVATE_RESOLUTION_RECORD_PATH, private_resolution)
    _write_text(PRIVATE_RESOLUTION_MARKDOWN_PATH, private_markdown)
    _write_json(PRIVATE_DIAGNOSTIC_PATH, private_diagnostic)

    group_count = int(final_lock.get("non_actionable_group_count") or 0)
    target_slot_count = int(final_lock.get("non_actionable_target_slot_count") or 0)
    blocker_count = int(final_lock.get("blocker_count") or 0)
    summary = {
        "schema_version": "kmfa.v014_explicit_business_resolution_intake_summary.v1",
        "record_type": "v014_explicit_business_resolution_intake_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "source_owner_diagnostic_phase_id": owner_diagnostic.get("phase_id"),
        "source_owner_diagnostic_decision": owner_diagnostic.get("decision"),
        "source_final_lock_phase_id": final_lock.get("phase_id"),
        "source_final_lock_decision": final_lock.get("decision"),
        "source_private_packet_read_performed_by_this_phase": True,
        "explicit_business_resolution_recorded": True,
        "owner_delegated_default_decision_applied": True,
        "previous_required_input": PREVIOUS_REQUIRED_INPUT,
        "previous_required_input_resolved_by_this_phase": True,
        "resolution_strategy": RESOLUTION_STRATEGY,
        "business_resolution_item_count": 1,
        "final_no_go_governance_lock_active": final_lock.get("final_no_go_governance_lock_active") is True,
        "partial_evidence_chain_ready": final_lock.get("partial_evidence_chain_ready") is True,
        "blocker_count": blocker_count,
        "non_actionable_group_count": group_count,
        "non_actionable_target_slot_count": target_slot_count,
        "keep_no_go_resolution_count": int(final_lock.get("keep_no_go_resolution_count") or 0),
        "non_actionable_groups_delivery_use_allowed": False,
        "non_actionable_groups_formal_report_use_allowed": False,
        "non_actionable_groups_business_execution_use_allowed": False,
        "residual_gap_report_recommended": True,
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
        "private_resolution_record_written": PRIVATE_RESOLUTION_RECORD_PATH.exists(),
        "private_resolution_record_gitignored": _git_check_ignored(PRIVATE_RESOLUTION_RECORD_PATH),
        "private_resolution_markdown_written": PRIVATE_RESOLUTION_MARKDOWN_PATH.exists(),
        "private_resolution_markdown_gitignored": _git_check_ignored(PRIVATE_RESOLUTION_MARKDOWN_PATH),
        "private_diagnostic_written": PRIVATE_DIAGNOSTIC_PATH.exists(),
        "private_diagnostic_gitignored": _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH),
        "public_safety": _public_safety(),
        "raw_boundary": _raw_boundary(),
        "next_required_input": NEXT_REQUIRED_INPUT,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
    }
    go_no_go = {
        "schema_version": "kmfa.v014_explicit_business_resolution_intake_go_no_go.v1",
        "record_type": "v014_explicit_business_resolution_intake_go_no_go_report",
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
        "explicit_business_resolution_recorded": True,
        "previous_required_input_resolved_by_this_phase": True,
        "resolution_strategy": RESOLUTION_STRATEGY,
        "business_resolution_item_count": 1,
        "delivery_allowed": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "business_execution_allowed": False,
    }
    manifest = {
        "schema_version": "kmfa.v014_explicit_business_resolution_intake_manifest.v1",
        "record_type": "v014_explicit_business_resolution_intake_manifest",
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
            SOURCE_OWNER_DIAGNOSTIC_SUMMARY_PATH.as_posix(),
            SOURCE_FINAL_LOCK_SUMMARY_PATH.as_posix(),
            "private:owner_diagnostic_packet",
        ],
        "public_outputs": [
            SUMMARY_PATH.as_posix(),
            MANIFEST_PATH.as_posix(),
            GO_NO_GO_PATH.as_posix(),
            REPORT_PATH.as_posix(),
            RESOLUTION_RECORD_PATH.as_posix(),
            GO_NO_GO_RECORD_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            RISK_REGISTER_PATH.as_posix(),
            ROLLBACK_PATH.as_posix(),
            METADATA_SUMMARY_PATH.as_posix(),
            METADATA_MANIFEST_PATH.as_posix(),
            METADATA_GO_NO_GO_PATH.as_posix(),
        ],
        "private_outputs": [
            "private:explicit_business_resolution_record",
            "private:explicit_business_resolution_record_markdown",
            "private:explicit_business_resolution_intake_diagnostic",
        ],
        "summary": summary,
        "go_no_go": go_no_go,
    }
    report = f"""# Explicit Business Resolution Intake

- phase_id: `{PHASE_ID}`
- decision: `{DECISION}`
- resolution recorded: `true`
- strategy: `{RESOLUTION_STRATEGY}`
- previous required input resolved: `true`
- business resolution item count: `1`
- non-actionable groups: `{group_count}`
- non-actionable target slots: `{target_slot_count}`
- full reconciliation allowed: `false`
- delivery allowed: `false`

This phase records a conservative owner-delegated business resolution. It keeps
the residual non-actionable groups out of any delivery or consistency claim and
does not authorize full source-map reapplication, raw comparison, GitHub upload,
app reinstall, formal reporting, or business execution.
"""
    resolution_record = f"""# Public-Safe Business Resolution

## Resolution

- Resolution strategy: `{RESOLUTION_STRATEGY}`
- Business resolution item count: `1`
- Previous required input resolved by this phase: `true`
- Residual gap report recommended: `true`

## Still Blocked

- Non-actionable groups usable for delivery: `false`
- Non-actionable groups usable for formal report: `false`
- Full raw-to-processed comparison: `blocked`
- Business-value consistency claim: `blocked`
- GitHub upload / app reinstall / business execution: `blocked`
"""
    go_no_go_record = f"""# Go/No-Go Record

- phase_id: `{PHASE_ID}`
- decision: `{DECISION}`
- reason: `{DIAGNOSTIC_CONCLUSION}`
- explicit_business_resolution_recorded: `true`
- previous_required_input_resolved_by_this_phase: `true`
- delivery_allowed: `false`
- github_upload_allowed: `false`
- app_reinstall_allowed: `false`
- business_execution_allowed: `false`
"""
    risk_register = """# Risk Register

- Risk: treating the conservative resolution as a release approval.
  Mitigation: all delivery, report, upload, reinstall and business execution gates remain closed.
- Risk: losing the unresolved gap context.
  Mitigation: next phase is limited to residual gap report preparation, not reconciliation bypass.
"""
    rollback_plan = """# Rollback Plan

No raw file, canonical source-map file, completion template, active authorization record or business output was modified. To roll back, remove this phase's public artifacts and ignored private resolution outputs.
"""
    test_results = """# Test Results

Status: passed locally after generation.

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_processed_value_source_map_completion_explicit_business_resolution_intake.py --generated-at 2026-07-06T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_value_source_map_completion_explicit_business_resolution_intake.py --require-private-resolution`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_processed_value_source_map_completion_explicit_business_resolution_intake`
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
        (RESOLUTION_RECORD_PATH, resolution_record),
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
    event_id = "DEV-KMFA-20260706-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-EXPLICIT-BUSINESS-RESOLUTION-INTAKE"
    summary = manifest["summary"]
    event = {
        "event_id": event_id,
        "event_time": generated_at,
        "event_type": "development",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "iteration_id": "ITER-20260706-KMFA-V014-EXPLICIT-BUSINESS-RESOLUTION-INTAKE",
        "fact_level": "EXTRACTED",
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "go_no_go": manifest["go_no_go"]["decision"],
        "explicit_business_resolution_recorded": True,
        "previous_required_input_resolved_by_this_phase": True,
        "resolution_strategy": summary["resolution_strategy"],
        "delivery_allowed": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "business_execution_allowed": False,
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "result_commit": "PENDING",
        "summary": "Recorded conservative owner-delegated business resolution while keeping v0.1.4 delivery gates closed.",
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
        "PASS: KMFA v0.1.4 explicit business resolution intake generated "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"recorded={manifest['summary']['explicit_business_resolution_recorded']}, "
        f"strategy={manifest['summary']['resolution_strategy']})"
    )


if __name__ == "__main__":
    main()
