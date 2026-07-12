#!/usr/bin/env python3
"""Audit missing owner confirmation for KMFA v0.1.4 source-map completion."""

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
PHASE_ID = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_CONFIRMATION_BLOCKER_AUDIT"
TASK_ID = "KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-OWNER-CONFIRMATION-BLOCKER-AUDIT-20260706"
ACCEPTANCE_ID = "ACC-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-OWNER-CONFIRMATION-BLOCKER-AUDIT"
VERSION = "0.1.4-processed-value-source-map-completion-owner-confirmation-blocker-audit"
STATUS = "completed_validated_local_only_no_go_owner_confirmation_missing"
BLOCKER = "owner_or_authorized_delegate_confirmation_code_not_supplied"
NEXT_REQUIRED_INPUT = "owner_or_authorized_delegate_confirms_private_decision_option_or_fills_response_template"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_confirmation_blocker_audit_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_confirmation_blocker_audit_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_confirmation_blocker_audit_go_no_go_report.json"
REPORT_PATH = HUMAN_DIR / "processed_value_source_map_completion_owner_confirmation_blocker_audit_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_processed_value_source_map_completion_owner_confirmation_blocker_audit_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_processed_value_source_map_completion_owner_confirmation_blocker_audit_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_processed_value_source_map_completion_owner_confirmation_blocker_audit_go_no_go_report.json"
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"

DECISION_OPTIONS_SUMMARY_PATH = (
    PROJECT_ROOT
    / "stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_RESPONSE_DECISION_OPTIONS/machine/processed_value_source_map_completion_owner_response_decision_options_summary.json"
)
PRIVATE_DECISION_OPTIONS_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_processed_value_source_map_completion_owner_response_decision_options"
PRIVATE_CONFIRMATION_RECORD_PATH = PRIVATE_DECISION_OPTIONS_DIR / "private_owner_response_confirmation_record.json"
PRIVATE_OUTPUT_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_processed_value_source_map_completion_owner_confirmation_blocker_audit"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_owner_confirmation_blocker_diagnostic.json"


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
        "private_confirmation_record_committed": False,
        "private_diagnostic_committed": False,
        "raw_file_committed": False,
        "raw_filename_committed": False,
        "raw_archive_member_name_committed": False,
        "field_header_plaintext_committed": False,
        "row_value_committed": False,
        "business_value_committed": False,
        "credential_or_secret_committed": False,
    }


def generate(*, generated_at: str | None = None, write_governance_event: bool = True) -> dict[str, Any]:
    timestamp = _now(generated_at)
    source_summary = _read_json(DECISION_OPTIONS_SUMMARY_PATH)
    confirmation_record_found = PRIVATE_CONFIRMATION_RECORD_PATH.exists()

    private_diagnostic = {
        "schema_version": "kmfa.private.v014_owner_confirmation_blocker_audit.v1",
        "classification": "private_owner_confirmation_blocker_diagnostic_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_owner_confirmation_blocker_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "source_decision_options_ref": "private_runtime_only",
        "confirmation_record_found": confirmation_record_found,
        "source_response_row_count": source_summary.get("source_response_row_count"),
        "source_pending_owner_decision_count": source_summary.get("source_pending_owner_decision_count"),
        "decision_option_count": source_summary.get("decision_option_count"),
        "raw_boundary": _raw_boundary(),
    }
    _write_json(PRIVATE_DIAGNOSTIC_PATH, private_diagnostic)

    summary = {
        "schema_version": "kmfa.v014_owner_confirmation_blocker_audit_summary.v1",
        "record_type": "v014_processed_value_source_map_completion_owner_confirmation_blocker_audit_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "status": STATUS,
        "generated_at": timestamp,
        "blocker_condition": BLOCKER,
        "source_decision_options_phase_id": source_summary.get("phase_id"),
        "source_response_row_count": source_summary.get("source_response_row_count"),
        "source_pending_owner_decision_count": source_summary.get("source_pending_owner_decision_count"),
        "decision_option_count": source_summary.get("decision_option_count"),
        "confirmation_record_found": confirmation_record_found,
        "private_diagnostic_written": True,
        "private_diagnostic_gitignored": _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH),
        "owner_confirmation_supplied": False,
        "active_owner_authorized_fill_record_ready": False,
        "active_owner_authorized_fill_record_written": False,
        "completion_template_overwritten": False,
        "authorized_completion_record_supplied": False,
        "source_map_completion_reapplication_ready": False,
        "source_map_completion_reapplication_performed": False,
        "source_map_records_applied_count": 0,
        "processed_value_materialization_replay_performed": False,
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
        "lineage_full_check_complete": False,
        "formal_report_allowed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "decision": "NO_GO",
        "diagnostic_conclusion": BLOCKER,
        "next_required_input": NEXT_REQUIRED_INPUT,
        "raw_boundary": _raw_boundary(),
        "public_safety": _public_safety(),
    }
    go_no_go = {
        "schema_version": "kmfa.v014_owner_confirmation_blocker_audit_go_no_go.v1",
        "record_type": "v014_processed_value_source_map_completion_owner_confirmation_blocker_audit_go_no_go_report",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "decision": "NO_GO",
        "status": STATUS,
        "diagnostic_conclusion": BLOCKER,
        "confirmation_record_found": confirmation_record_found,
        "owner_confirmation_supplied": False,
        "source_pending_owner_decision_count": summary["source_pending_owner_decision_count"],
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
        "schema_version": "kmfa.v014_owner_confirmation_blocker_audit_manifest.v1",
        "record_type": "v014_processed_value_source_map_completion_owner_confirmation_blocker_audit_manifest",
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
            "private_diagnostic": "private_runtime_only",
        },
        "validator": (
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. "
            "python3 KMFA/tools/check_v014_processed_value_source_map_completion_owner_confirmation_blocker_audit.py "
            "--require-private-diagnostic"
        ),
        "git": {
            "branch": _git_output(["branch", "--show-current"]),
            "head": _git_output(["rev-parse", "HEAD"]),
            "status_short": _git_output(["status", "--short", "--branch"]),
        },
    }
    report = f"""# V014 Processed Value Source-map Completion Owner Confirmation Blocker Audit

Decision: NO_GO

This phase records that no owner or authorized-delegate confirmation code has been supplied. It does not read raw data, create an active authorization record, overwrite the completion template, or apply source-map changes.

## Public-safe aggregate result

- Source response rows: {summary["source_response_row_count"]}
- Source pending owner decisions: {summary["source_pending_owner_decision_count"]}
- Decision options available: {summary["decision_option_count"]}
- Confirmation record found: {str(confirmation_record_found).lower()}

Next required input: `{NEXT_REQUIRED_INPUT}`.
"""
    go_no_go_record = f"""# Go/No-Go Record

- phase_id: `{PHASE_ID}`
- decision: `NO_GO`
- reason: owner or authorized-delegate confirmation code has not been supplied.
- active owner-authorized fill record ready: `false`
- github upload performed: `false`
"""
    risk_register = """# Risk Register

- Risk: proceeding without confirmation would fabricate owner authorization.
  Mitigation: this audit keeps active authorization, source-map application and reconciliation closed.
- Risk: private option details leaking publicly.
  Mitigation: public artifacts contain only aggregate counts and gate flags.
"""
    rollback_plan = """# Rollback Plan

No raw file, response template, completion template, active authorization record or source-map file was modified. To roll back, remove this phase's public artifacts and metadata copies, then remove the ignored private diagnostic if not needed.
"""
    test_results = """# Test Results

Pending until validator and focused tests are run after artifact generation.

Expected validator:
`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_value_source_map_completion_owner_confirmation_blocker_audit.py --require-private-diagnostic`
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
    event_id = "DEV-KMFA-20260706-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-OWNER-CONFIRMATION-BLOCKER-AUDIT"
    event = {
        "event_id": event_id,
        "event_time": generated_at,
        "event_type": "development",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "iteration_id": "ITER-20260706-KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-OWNER-CONFIRMATION-BLOCKER-AUDIT",
        "fact_level": "EXTRACTED",
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "go_no_go": manifest["go_no_go"]["decision"],
        "confirmation_record_found": manifest["summary"]["confirmation_record_found"],
        "source_pending_owner_decision_count": manifest["summary"]["source_pending_owner_decision_count"],
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "result_commit": "PENDING",
        "summary": "Recorded the missing owner confirmation blocker; downstream authorization, source-map application and reconciliation remain blocked.",
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
        "PASS: KMFA v0.1.4 owner confirmation blocker audit generated "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"confirmation_found={manifest['summary']['confirmation_record_found']}, "
        f"pending={manifest['summary']['source_pending_owner_decision_count']})"
    )


if __name__ == "__main__":
    main()
