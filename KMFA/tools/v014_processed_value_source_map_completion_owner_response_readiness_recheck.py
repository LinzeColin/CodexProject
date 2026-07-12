#!/usr/bin/env python3
"""Recheck owner response readiness for KMFA v0.1.4 source-map completion.

This phase consumes the ignored private owner-review response template and
records whether it can be safely converted into an active authorization record.
It does not read the raw inbox, does not fill owner decisions, does not
overwrite the completion template, and does not apply source-map changes.
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
PHASE_ID = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_RESPONSE_READINESS_RECHECK"
TASK_ID = "KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-OWNER-RESPONSE-READINESS-RECHECK-20260706"
ACCEPTANCE_ID = "ACC-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-OWNER-RESPONSE-READINESS-RECHECK"
VERSION = "0.1.4-processed-value-source-map-completion-owner-response-readiness-recheck"
STATUS = "completed_validated_local_only_no_go_owner_response_template_still_pending"
NEXT_REQUIRED_INPUT = "owner_or_authorized_delegate_fills_private_owner_review_response_template"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_response_readiness_recheck_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_response_readiness_recheck_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_response_readiness_recheck_go_no_go_report.json"
REPORT_PATH = HUMAN_DIR / "processed_value_source_map_completion_owner_response_readiness_recheck_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_processed_value_source_map_completion_owner_response_readiness_recheck_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_processed_value_source_map_completion_owner_response_readiness_recheck_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_processed_value_source_map_completion_owner_response_readiness_recheck_go_no_go_report.json"
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"

SOURCE_RESPONSE_TEMPLATE_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_owner_review_intake_prep/private_owner_review_response_template.json"
)
PRIVATE_OUTPUT_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_processed_value_source_map_completion_owner_response_readiness_recheck"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_owner_response_readiness_diagnostic.json"

PENDING_VALUE = "PENDING_OWNER_OR_AUTHORIZED_DELEGATE_REVIEW"
VALID_DECISION_CODES = {
    "confirm_group_candidate_rank",
    "choose_candidate_record_ref",
    "keep_pending",
    "mark_not_applicable",
    "request_more_diagnostics",
}
DECISIONS_REQUIRING_SELECTION = {"confirm_group_candidate_rank", "choose_candidate_record_ref"}


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
    if result.returncode != 0:
        return "UNKNOWN"
    return result.stdout.strip()


def _git_check_ignored(path: Path) -> bool:
    return subprocess.run(["git", "check-ignore", "-q", path.as_posix()], check=False).returncode == 0


def _field_filled(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip()) and value != PENDING_VALUE


def _classify_response_rows(template: dict[str, Any]) -> tuple[dict[str, int], list[dict[str, Any]]]:
    rows = template.get("response_rows", [])
    if not isinstance(rows, list):
        raise ValueError("response_rows must be a list")
    counts = {
        "response_row_count": len(rows),
        "pending_owner_decision_count": 0,
        "valid_owner_decision_count": 0,
        "invalid_owner_decision_count": 0,
        "explicit_keep_pending_count": 0,
        "mark_not_applicable_count": 0,
        "request_more_diagnostics_count": 0,
        "confirm_group_candidate_rank_count": 0,
        "choose_candidate_record_ref_count": 0,
    }
    item_statuses: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("response row must be an object")
        target_slot_id = row.get("target_slot_id")
        decision = row.get("owner_decision_code")
        status = "pending_owner_or_authorized_delegate_review"
        if decision == PENDING_VALUE:
            counts["pending_owner_decision_count"] += 1
        elif decision not in VALID_DECISION_CODES:
            counts["invalid_owner_decision_count"] += 1
            status = "invalid_unknown_owner_decision_code"
        else:
            missing_fields: list[str] = []
            if decision in DECISIONS_REQUIRING_SELECTION:
                if not _field_filled(row.get("selected_candidate_record_ref_hash")):
                    missing_fields.append("selected_candidate_record_ref_hash")
                if not _field_filled(row.get("selected_processed_value_fingerprint")):
                    missing_fields.append("selected_processed_value_fingerprint")
            if not _field_filled(row.get("owner_or_authorized_delegate_role")):
                missing_fields.append("owner_or_authorized_delegate_role")
            if not _field_filled(row.get("authorization_timestamp")):
                missing_fields.append("authorization_timestamp")
            if missing_fields:
                counts["invalid_owner_decision_count"] += 1
                status = "invalid_owner_decision_missing_required_fields"
            else:
                counts["valid_owner_decision_count"] += 1
                status = f"valid_{decision}"
                if decision == "keep_pending":
                    counts["explicit_keep_pending_count"] += 1
                elif decision == "mark_not_applicable":
                    counts["mark_not_applicable_count"] += 1
                elif decision == "request_more_diagnostics":
                    counts["request_more_diagnostics_count"] += 1
                elif decision == "confirm_group_candidate_rank":
                    counts["confirm_group_candidate_rank_count"] += 1
                elif decision == "choose_candidate_record_ref":
                    counts["choose_candidate_record_ref_count"] += 1
        item_statuses.append(
            {
                "target_slot_id": target_slot_id,
                "context_group": row.get("context_group"),
                "review_group_id": row.get("review_group_id"),
                "owner_decision_code": decision,
                "readiness_status": status,
            }
        )
    return counts, item_statuses


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
    response_template = _read_json(SOURCE_RESPONSE_TEMPLATE_PATH)
    counts, item_statuses = _classify_response_rows(response_template)
    private_diagnostic = {
        "schema_version": "kmfa.private.v014_processed_value_source_map_completion_owner_response_readiness_recheck.v1",
        "classification": "private_owner_response_readiness_diagnostic_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_owner_response_readiness_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "source_response_template_ref": "private_runtime_only",
        "counts": counts,
        "item_statuses": item_statuses,
        "raw_boundary": _raw_boundary(),
    }
    _write_json(PRIVATE_DIAGNOSTIC_PATH, private_diagnostic)

    active_record_ready = (
        counts["response_row_count"] > 0
        and counts["pending_owner_decision_count"] == 0
        and counts["invalid_owner_decision_count"] == 0
        and counts["valid_owner_decision_count"] == counts["response_row_count"]
    )
    decision = "GO" if active_record_ready else "NO_GO"
    diagnostic_conclusion = (
        "private_owner_response_template_complete_ready_for_separate_activation"
        if active_record_ready
        else "private_owner_response_template_still_pending_owner_review"
    )
    status = "ready_for_separate_owner_response_activation_phase" if active_record_ready else STATUS
    summary = {
        "schema_version": "kmfa.v014_processed_value_source_map_completion_owner_response_readiness_recheck_summary.v1",
        "record_type": "v014_processed_value_source_map_completion_owner_response_readiness_recheck_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "status": status,
        "generated_at": timestamp,
        "response_template_gitignored": _git_check_ignored(SOURCE_RESPONSE_TEMPLATE_PATH),
        "private_diagnostic_written": True,
        "private_diagnostic_gitignored": _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH),
        "response_row_count": counts["response_row_count"],
        "pending_owner_decision_count": counts["pending_owner_decision_count"],
        "valid_owner_decision_count": counts["valid_owner_decision_count"],
        "invalid_owner_decision_count": counts["invalid_owner_decision_count"],
        "explicit_keep_pending_count": counts["explicit_keep_pending_count"],
        "mark_not_applicable_count": counts["mark_not_applicable_count"],
        "request_more_diagnostics_count": counts["request_more_diagnostics_count"],
        "confirm_group_candidate_rank_count": counts["confirm_group_candidate_rank_count"],
        "choose_candidate_record_ref_count": counts["choose_candidate_record_ref_count"],
        "active_owner_authorized_fill_record_ready": active_record_ready,
        "active_owner_authorized_fill_record_written": False,
        "completion_template_overwritten": False,
        "authorized_completion_record_supplied": active_record_ready,
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
        "decision": decision,
        "diagnostic_conclusion": diagnostic_conclusion,
        "next_required_input": NEXT_REQUIRED_INPUT if not active_record_ready else "separate_owner_response_activation_phase",
        "raw_boundary": _raw_boundary(),
        "public_safety": _public_safety(),
    }
    go_no_go = {
        "schema_version": "kmfa.v014_processed_value_source_map_completion_owner_response_readiness_recheck_go_no_go.v1",
        "record_type": "v014_processed_value_source_map_completion_owner_response_readiness_recheck_go_no_go_report",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "decision": decision,
        "status": status,
        "diagnostic_conclusion": diagnostic_conclusion,
        "response_row_count": counts["response_row_count"],
        "pending_owner_decision_count": counts["pending_owner_decision_count"],
        "valid_owner_decision_count": counts["valid_owner_decision_count"],
        "active_owner_authorized_fill_record_ready": active_record_ready,
        "source_map_completion_reapplication_ready": False,
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "blocked_until": summary["next_required_input"],
    }
    manifest = {
        "schema_version": "kmfa.v014_processed_value_source_map_completion_owner_response_readiness_recheck_manifest.v1",
        "record_type": "v014_processed_value_source_map_completion_owner_response_readiness_recheck_manifest",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_ids": [ACCEPTANCE_ID],
        "generated_at": timestamp,
        "status": status,
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
            "python3 KMFA/tools/check_v014_processed_value_source_map_completion_owner_response_readiness_recheck.py "
            "--require-private-diagnostic"
        ),
        "git": {
            "branch": _git_output(["branch", "--show-current"]),
            "head": _git_output(["rev-parse", "HEAD"]),
            "status_short": _git_output(["status", "--short", "--branch"]),
        },
    }
    report = f"""# V014 Processed Value Source-map Completion Owner Response Readiness Recheck

Decision: {decision}

This phase rechecked the private owner-review response template. It did not read the raw inbox, fill owner decisions, activate an authorization record, or apply source-map changes.

## Public-safe aggregate result

- Response rows: {summary["response_row_count"]}
- Pending owner decisions: {summary["pending_owner_decision_count"]}
- Valid owner decisions: {summary["valid_owner_decision_count"]}
- Invalid owner decisions: {summary["invalid_owner_decision_count"]}
- Active authorization record ready: {str(active_record_ready).lower()}

Next required input: `{summary["next_required_input"]}`.
"""
    go_no_go_record = f"""# Go/No-Go Record

- phase_id: `{PHASE_ID}`
- decision: `{decision}`
- reason: owner response template is still pending and cannot be activated.
- active owner-authorized fill record ready: `{str(active_record_ready).lower()}`
- github upload performed: `false`
"""
    risk_register = """# Risk Register

- Risk: proceeding without owner response would fabricate authorization.
  Mitigation: this gate keeps active authorization, source-map application and reconciliation closed.
- Risk: private response details leaking publicly.
  Mitigation: public artifacts contain only aggregate counts and gate flags; private item statuses stay ignored.
"""
    rollback_plan = """# Rollback Plan

No raw file, completion template, active authorization record or source-map file was modified. To roll back, remove this phase's public artifacts and metadata copies, then remove the ignored private diagnostic if not needed.
"""
    test_results = """# Test Results

Pending until validator and focused tests are run after artifact generation.

Expected validator:
`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_value_source_map_completion_owner_response_readiness_recheck.py --require-private-diagnostic`
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
    event_id = "DEV-KMFA-20260706-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-OWNER-RESPONSE-READINESS-RECHECK"
    event = {
        "event_id": event_id,
        "event_time": generated_at,
        "event_type": "development",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "iteration_id": "ITER-20260706-KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-OWNER-RESPONSE-READINESS-RECHECK",
        "fact_level": "EXTRACTED",
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "go_no_go": manifest["go_no_go"]["decision"],
        "response_row_count": manifest["summary"]["response_row_count"],
        "pending_owner_decision_count": manifest["summary"]["pending_owner_decision_count"],
        "valid_owner_decision_count": manifest["summary"]["valid_owner_decision_count"],
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "result_commit": "PENDING",
        "summary": (
            "Rechecked the private owner-review response template and confirmed that all response rows remain pending. "
            "Public evidence is aggregate-only and downstream authorization, source-map application and reconciliation remain blocked."
        ),
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
        "PASS: KMFA v0.1.4 owner response readiness recheck generated "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"pending={manifest['summary']['pending_owner_decision_count']}, "
        f"valid={manifest['summary']['valid_owner_decision_count']})"
    )


if __name__ == "__main__":
    main()
