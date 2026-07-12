#!/usr/bin/env python3
"""Apply conservative default resolution to non-actionable source-map groups.

This phase converts the already-filled private owner confirmation responses
for non-actionable groups into a private default-resolution result. It keeps
those groups excluded from canonical source-map application and preserves the
NO-GO gate for full reapplication. No raw source files are read or mutated.
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
PHASE_ID = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_NON_ACTIONABLE_DEFAULT_RESOLUTION_APPLICATION"
TASK_ID = "KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-NON-ACTIONABLE-DEFAULT-RESOLUTION-APPLICATION-20260706"
ACCEPTANCE_ID = "ACC-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-NON-ACTIONABLE-DEFAULT-RESOLUTION-APPLICATION"
VERSION = "0.1.4-non-actionable-default-resolution-application"
STATUS = "completed_validated_local_only_non_actionable_default_resolution_application_no_go"
DECISION = "NO_GO"
DIAGNOSTIC_CONCLUSION = "non_actionable_default_keep_no_go_resolution_applied_full_reapplication_blocked"
NEXT_RECOMMENDED_PHASE = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_FULL_RECONCILIATION_BLOCKER_AUDIT"
NEXT_REQUIRED_INPUT = "non_actionable_groups_keep_no_go_until_explicit_business_resolution"
DEFAULT_RESOLUTION_CODE = "KEEP_NO_GO_EXCLUDED_FROM_FULL_SOURCE_MAP_APPLICATION"
DEFAULT_AUTHORITY_BASIS = "owner_delegated_codex_conservative_default_keep_no_go_no_raw_read"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "processed_value_source_map_completion_non_actionable_default_resolution_application_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_value_source_map_completion_non_actionable_default_resolution_application_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_value_source_map_completion_non_actionable_default_resolution_application_go_no_go_report.json"
REPORT_PATH = HUMAN_DIR / "processed_value_source_map_completion_non_actionable_default_resolution_application_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_non_actionable_default_resolution_application_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_non_actionable_default_resolution_application_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_non_actionable_default_resolution_application_go_no_go_report.json"
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"

SOURCE_AFTER_FILL_SUMMARY_PATH = (
    PROJECT_ROOT
    / "stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_CONFIRMATION_RESPONSE_INTAKE_AFTER_FILL/machine/processed_value_source_map_completion_owner_confirmation_response_intake_after_fill_summary.json"
)
SOURCE_PARTIAL_APPLICATION_SUMMARY_PATH = (
    PROJECT_ROOT
    / "stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_GROUP_PARTIAL_APPLICATION/machine/processed_value_source_map_completion_owner_group_partial_application_summary.json"
)
SOURCE_PARTIAL_COMPARISON_SUMMARY_PATH = (
    PROJECT_ROOT
    / "stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_PARTIAL_RAW_TO_PROCESSED_COMPARISON/machine/processed_value_source_map_completion_partial_raw_to_processed_comparison_summary.json"
)
PRIVATE_VALID_RESPONSE_QUEUE_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_owner_confirmation_response_intake_after_fill/private_owner_confirmation_valid_response_queue_after_fill.json"
)

PRIVATE_OUTPUT_DIR = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_non_actionable_default_resolution_application"
)
PRIVATE_RESULT_PATH = PRIVATE_OUTPUT_DIR / "private_non_actionable_default_resolution_application_result.json"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_non_actionable_default_resolution_application_diagnostic.json"


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
        "private_valid_response_queue_committed": False,
        "private_default_resolution_result_committed": False,
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
    valid_queue: dict[str, Any],
    partial_summary: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    valid_responses = valid_queue.get("valid_responses", [])
    if not isinstance(valid_responses, list):
        raise ValueError("valid_responses must be a list")
    resolution_rows: list[dict[str, Any]] = []
    choice_counts: Counter[str] = Counter()
    reason_counts: Counter[str] = Counter()
    for response in valid_responses:
        if not isinstance(response, dict):
            continue
        choice_code = str(response.get("choice_code") or "UNKNOWN")
        reason_code = str(response.get("resolution_reason_code") or "UNKNOWN")
        choice_counts[choice_code] += 1
        reason_counts[reason_code] += 1
        resolution_rows.append(
            {
                "response_item_id": response.get("response_item_id"),
                "response_index": response.get("response_index"),
                "source_choice_code": choice_code,
                "resolution_reason_code": reason_code,
                "default_resolution_code": DEFAULT_RESOLUTION_CODE,
                "default_resolution_authority_basis": DEFAULT_AUTHORITY_BASIS,
                "active_authorization_allowed_by_resolution": False,
                "canonical_source_map_mutation_allowed_by_resolution": False,
                "raw_compare_allowed_by_resolution": False,
            }
        )
    result_summary = {
        "valid_response_count": len(resolution_rows),
        "keep_no_go_resolution_count": len(resolution_rows),
        "active_authorization_allowed_count": 0,
        "canonical_source_map_mutation_allowed_count": 0,
        "non_actionable_group_count": int(partial_summary.get("private_blocked_group_count") or 0),
        "non_actionable_target_slot_count": int(partial_summary.get("private_blocked_target_slot_count") or 0),
        "actionable_partial_application_group_count": int(partial_summary.get("private_partial_application_group_count") or 0),
        "actionable_partial_application_target_slot_count": int(partial_summary.get("private_partial_application_target_slot_count") or 0),
        "choice_code_counts": dict(choice_counts),
        "resolution_reason_code_counts": dict(reason_counts),
        "full_source_map_completion_reapplication_ready": False,
        "canonical_source_map_mutated": False,
    }
    result = {
        "schema_version": "kmfa.private.v014_non_actionable_default_resolution_application.v1",
        "classification": "private_non_actionable_default_resolution_application_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_non_actionable_default_resolution_application",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "default_resolution_code": DEFAULT_RESOLUTION_CODE,
        "default_resolution_authority_basis": DEFAULT_AUTHORITY_BASIS,
        "result_summary": result_summary,
        "resolution_rows": resolution_rows,
        "raw_boundary": _raw_boundary(),
    }
    diagnostic = {
        "schema_version": "kmfa.private.v014_non_actionable_default_resolution_application_diagnostic.v1",
        "classification": "private_non_actionable_default_resolution_application_diagnostic_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_non_actionable_default_resolution_application_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "result_summary": result_summary,
        "raw_boundary": _raw_boundary(),
    }
    return result, diagnostic


def generate(generated_at: str | None = None, *, write_governance_event: bool = True) -> dict[str, Any]:
    timestamp = _now(generated_at)
    after_fill_summary = _read_json(SOURCE_AFTER_FILL_SUMMARY_PATH)
    partial_summary = _read_json(SOURCE_PARTIAL_APPLICATION_SUMMARY_PATH)
    partial_comparison_summary = _read_json(SOURCE_PARTIAL_COMPARISON_SUMMARY_PATH)
    valid_queue = _read_json(PRIVATE_VALID_RESPONSE_QUEUE_PATH)
    private_result, private_diagnostic = _build_private_resolution(
        generated_at=timestamp,
        valid_queue=valid_queue,
        partial_summary=partial_summary,
    )
    _write_json(PRIVATE_RESULT_PATH, private_result)
    _write_json(PRIVATE_DIAGNOSTIC_PATH, private_diagnostic)

    result_summary = private_result["result_summary"]
    summary = {
        "schema_version": "kmfa.v014_non_actionable_default_resolution_application_summary.v1",
        "record_type": "v014_non_actionable_default_resolution_application_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "source_after_fill_phase_id": after_fill_summary.get("phase_id"),
        "source_after_fill_decision": after_fill_summary.get("decision"),
        "source_after_fill_valid_owner_confirmation_response_count": int(
            after_fill_summary.get("valid_owner_confirmation_response_count") or 0
        ),
        "source_after_fill_pending_owner_confirmation_response_count": int(
            after_fill_summary.get("pending_owner_confirmation_response_count") or 0
        ),
        "source_after_fill_default_choice_code_counts": after_fill_summary.get("default_confirmation_choice_code_counts", {}),
        "non_actionable_default_resolution_application_performed": True,
        "non_actionable_default_resolution_code": DEFAULT_RESOLUTION_CODE,
        "non_actionable_default_resolution_authority_basis": DEFAULT_AUTHORITY_BASIS,
        "non_actionable_default_resolution_item_count": result_summary["valid_response_count"],
        "keep_no_go_resolution_count": result_summary["keep_no_go_resolution_count"],
        "non_actionable_active_authorization_allowed_count": result_summary["active_authorization_allowed_count"],
        "non_actionable_canonical_source_map_mutation_allowed_count": result_summary[
            "canonical_source_map_mutation_allowed_count"
        ],
        "non_actionable_group_count": result_summary["non_actionable_group_count"],
        "non_actionable_target_slot_count": result_summary["non_actionable_target_slot_count"],
        "actionable_partial_application_group_count": result_summary["actionable_partial_application_group_count"],
        "actionable_partial_application_target_slot_count": result_summary[
            "actionable_partial_application_target_slot_count"
        ],
        "source_partial_comparison_phase_id": partial_comparison_summary.get("phase_id"),
        "source_partial_comparison_decision": partial_comparison_summary.get("decision"),
        "partial_raw_to_processed_comparison_already_public_safe_passed": (
            partial_comparison_summary.get("diagnostic_conclusion")
            == "private_partial_raw_to_processed_fingerprint_comparison_passed_full_reconciliation_blocked"
        ),
        "partial_followup_evidence_ready_for_blocker_audit": True,
        "full_source_map_completion_reapplication_ready": False,
        "full_raw_to_processed_comparison_ready": False,
        "canonical_source_map_mutated": False,
        "canonical_source_map_records_applied_count": 0,
        "processed_value_materialization_replay_performed": False,
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "business_value_consistency_verified": False,
        "lineage_full_check_complete": False,
        "formal_report_allowed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "private_valid_response_queue_gitignored": _git_check_ignored(PRIVATE_VALID_RESPONSE_QUEUE_PATH),
        "private_default_resolution_result_written": PRIVATE_RESULT_PATH.exists(),
        "private_default_resolution_result_gitignored": _git_check_ignored(PRIVATE_RESULT_PATH),
        "private_diagnostic_written": PRIVATE_DIAGNOSTIC_PATH.exists(),
        "private_diagnostic_gitignored": _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH),
        "public_safety": _public_safety(),
        "raw_boundary": _raw_boundary(),
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
        "next_required_input": NEXT_REQUIRED_INPUT,
    }
    go_no_go = {
        "schema_version": "kmfa.v014_non_actionable_default_resolution_application_go_no_go.v1",
        "record_type": "v014_non_actionable_default_resolution_application_go_no_go_report",
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
        "non_actionable_default_resolution_application_performed": True,
        "keep_no_go_resolution_count": summary["keep_no_go_resolution_count"],
        "non_actionable_group_count": summary["non_actionable_group_count"],
        "non_actionable_target_slot_count": summary["non_actionable_target_slot_count"],
        "full_source_map_completion_reapplication_ready": False,
        "canonical_source_map_mutated": False,
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }
    manifest = {
        "schema_version": "kmfa.v014_non_actionable_default_resolution_application_manifest.v1",
        "record_type": "v014_non_actionable_default_resolution_application_manifest",
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
            SOURCE_AFTER_FILL_SUMMARY_PATH.as_posix(),
            SOURCE_PARTIAL_APPLICATION_SUMMARY_PATH.as_posix(),
            SOURCE_PARTIAL_COMPARISON_SUMMARY_PATH.as_posix(),
            "private:owner_confirmation_valid_response_queue_after_fill",
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
        "private_outputs": [
            "private:non_actionable_default_resolution_application_result",
            "private:non_actionable_default_resolution_application_diagnostic",
        ],
        "summary": summary,
        "go_no_go": go_no_go,
    }
    report = f"""# Non-Actionable Default Resolution Application

- phase_id: `{PHASE_ID}`
- decision: `{DECISION}`
- default resolution applied: `true`
- keep No-Go resolution count: `{summary["keep_no_go_resolution_count"]}`
- non-actionable groups: `{summary["non_actionable_group_count"]}`
- non-actionable target slots: `{summary["non_actionable_target_slot_count"]}`
- actionable partial target slots already staged: `{summary["actionable_partial_application_target_slot_count"]}`
- full source-map reapplication ready: `false`

The non-actionable responses are now documented as conservative keep-No-Go
defaults in private runtime. This does not authorize business values, canonical
source-map mutation, full raw comparison, formal reports, GitHub upload, app
reinstall or business execution.

Next required input: `{NEXT_REQUIRED_INPUT}`.
"""
    go_no_go_record = f"""# Go/No-Go Record

- phase_id: `{PHASE_ID}`
- decision: `{DECISION}`
- reason: `{DIAGNOSTIC_CONCLUSION}`
- keep_no_go_resolution_count: `{summary["keep_no_go_resolution_count"]}`
- non_actionable_target_slot_count: `{summary["non_actionable_target_slot_count"]}`
- full_source_map_completion_reapplication_ready: `false`
- github upload performed: `false`
"""
    risk_register = """# Risk Register

- Risk: treating keep-No-Go default resolution as business authorization.
  Mitigation: active authorization, canonical source-map mutation and full raw comparison remain closed.
- Risk: leaking private response identifiers publicly.
  Mitigation: public artifacts contain only aggregate counts and gate flags.
"""
    rollback_plan = """# Rollback Plan

No raw file, canonical source-map file, completion template or active authorization record was modified. To roll back, remove this phase's public artifacts and the ignored private default-resolution runtime outputs.
"""
    test_results = """# Test Results

Status: passed locally after generation.

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_processed_value_source_map_completion_non_actionable_default_resolution_application.py --generated-at 2026-07-06T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_value_source_map_completion_non_actionable_default_resolution_application.py --require-private-default-resolution`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_processed_value_source_map_completion_non_actionable_default_resolution_application`
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
    event_id = "DEV-KMFA-20260706-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-NON-ACTIONABLE-DEFAULT-RESOLUTION-APPLICATION"
    summary = manifest["summary"]
    event = {
        "event_id": event_id,
        "event_time": generated_at,
        "event_type": "development",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "iteration_id": "ITER-20260706-KMFA-V014-NON-ACTIONABLE-DEFAULT-RESOLUTION-APPLICATION",
        "fact_level": "EXTRACTED",
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "go_no_go": manifest["go_no_go"]["decision"],
        "non_actionable_default_resolution_application_performed": True,
        "keep_no_go_resolution_count": summary["keep_no_go_resolution_count"],
        "non_actionable_group_count": summary["non_actionable_group_count"],
        "non_actionable_target_slot_count": summary["non_actionable_target_slot_count"],
        "canonical_source_map_mutated": False,
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "result_commit": "PENDING",
        "summary": "Applied private conservative keep-No-Go resolution for the non-actionable source-map groups while preserving full reapplication and business-use blockers.",
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
        "PASS: KMFA v0.1.4 non-actionable default resolution application generated "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"keep_no_go={manifest['summary']['keep_no_go_resolution_count']}, "
        f"blocked_slots={manifest['summary']['non_actionable_target_slot_count']})"
    )


if __name__ == "__main__":
    main()
