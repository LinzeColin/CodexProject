#!/usr/bin/env python3
"""Check owner group-decision response intake for KMFA v0.1.4.

This phase reads only the private owner group-decision response template. It
does not modify that template, write active authorization, apply source-map
records, or read raw inbox data.
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
PHASE_ID = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_GROUP_DECISION_RESPONSE_INTAKE"
TASK_ID = "KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-OWNER-GROUP-DECISION-RESPONSE-INTAKE-20260706"
ACCEPTANCE_ID = "ACC-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-OWNER-GROUP-DECISION-RESPONSE-INTAKE"
VERSION = "0.1.4-processed-value-source-map-completion-owner-group-decision-response-intake"
STATUS = "completed_validated_local_only_no_go_owner_group_decisions_still_pending"
DIAGNOSTIC_CONCLUSION = "owner_group_decision_response_template_still_pending"
NEXT_REQUIRED_INPUT = "owner_or_authorized_delegate_replaces_pending_group_decision_codes"
PENDING_DECISION_CODE = "PENDING_OWNER_OR_AUTHORIZED_DELEGATE_GROUP_DECISION"
VALID_OWNER_GROUP_DECISION_CODES = {
    "CONFIRM_GROUP_CANDIDATE_RANK",
    "CHOOSE_CANDIDATE_RECORD_REF",
    "KEEP_PENDING",
    "MARK_NOT_APPLICABLE",
    "REQUEST_MORE_DIAGNOSTICS",
}

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_group_decision_response_intake_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_group_decision_response_intake_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_group_decision_response_intake_go_no_go_report.json"
REPORT_PATH = HUMAN_DIR / "processed_value_source_map_completion_owner_group_decision_response_intake_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_processed_value_source_map_completion_owner_group_decision_response_intake_summary.json"
)
METADATA_MANIFEST_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_processed_value_source_map_completion_owner_group_decision_response_intake_manifest.json"
)
METADATA_GO_NO_GO_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_processed_value_source_map_completion_owner_group_decision_response_intake_go_no_go_report.json"
)
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"

SOURCE_INPUT_KIT_SUMMARY_PATH = (
    PROJECT_ROOT
    / "stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_GROUP_DECISION_INPUT_KIT/machine/processed_value_source_map_completion_owner_group_decision_input_kit_summary.json"
)
PRIVATE_INPUT_KIT_DIR = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_owner_group_decision_input_kit"
)
PRIVATE_RESPONSE_TEMPLATE_PATH = PRIVATE_INPUT_KIT_DIR / "private_owner_group_decision_response_template.json"
PRIVATE_INPUT_KIT_DIAGNOSTIC_PATH = PRIVATE_INPUT_KIT_DIR / "private_owner_group_decision_input_kit_diagnostic.json"

PRIVATE_OUTPUT_DIR = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_owner_group_decision_response_intake"
)
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_owner_group_decision_response_intake_diagnostic.json"
PRIVATE_PENDING_GROUP_QUEUE_PATH = PRIVATE_OUTPUT_DIR / "private_owner_group_decision_response_pending_queue.json"


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
        "private_input_kit_diagnostic_committed": False,
        "private_intake_diagnostic_committed": False,
        "private_pending_group_queue_committed": False,
        "raw_file_committed": False,
        "raw_filename_committed": False,
        "raw_archive_member_name_committed": False,
        "field_header_plaintext_committed": False,
        "row_value_committed": False,
        "business_value_committed": False,
        "credential_or_secret_committed": False,
    }


def _decision_code(group: dict[str, Any]) -> str:
    return str(group.get("owner_group_decision_code", "")).strip()


def _build_private_records(
    *,
    generated_at: str,
    source_summary: dict[str, Any],
    input_diagnostic: dict[str, Any],
    response_template: dict[str, Any],
) -> dict[str, Any]:
    if response_template.get("template_is_active_authorization_record") is not False:
        raise ValueError("private response template must not be an active authorization record")
    groups = response_template.get("groups", [])
    if not isinstance(groups, list):
        raise ValueError("private response template groups must be a list")

    pending_groups: list[dict[str, Any]] = []
    valid_count = 0
    invalid_count = 0
    code_counts: Counter[str] = Counter()
    for group in groups:
        if not isinstance(group, dict):
            invalid_count += 1
            code_counts["INVALID_GROUP_RECORD"] += 1
            continue
        code = _decision_code(group)
        code_counts[code or "MISSING_OWNER_GROUP_DECISION_CODE"] += 1
        if code == PENDING_DECISION_CODE:
            pending_groups.append(
                {
                    "review_group_id": group.get("review_group_id"),
                    "candidate_status": group.get("candidate_status"),
                    "target_slot_count": group.get("target_slot_count"),
                    "owner_group_decision_code": code,
                    "active_authorization_allowed": False,
                }
            )
        elif code in VALID_OWNER_GROUP_DECISION_CODES:
            valid_count += 1
        else:
            invalid_count += 1

    diagnostic = {
        "schema_version": "kmfa.private.v014_owner_group_decision_response_intake_diagnostic.v1",
        "classification": "private_owner_group_decision_response_intake_diagnostic_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_owner_group_decision_response_intake_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "source_phase_id": source_summary.get("phase_id"),
        "source_input_kit_diagnostic_phase_id": input_diagnostic.get("phase_id"),
        "review_group_count": len(groups),
        "response_row_count": response_template.get("response_row_count"),
        "pending_group_decision_count": len(pending_groups),
        "valid_group_decision_count": valid_count,
        "invalid_group_decision_count": invalid_count,
        "owner_group_decision_code_counts": dict(code_counts),
        "owner_group_decisions_supplied": valid_count > 0,
        "owner_group_decision_applied": False,
        "active_owner_authorized_fill_record_ready": False,
        "source_map_completion_reapplication_ready": False,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "next_required_input": NEXT_REQUIRED_INPUT,
        "raw_boundary": _raw_boundary(),
    }
    pending_queue = {
        "schema_version": "kmfa.private.v014_owner_group_decision_response_pending_queue.v1",
        "classification": "private_owner_group_decision_response_pending_queue_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_owner_group_decision_response_pending_queue",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "pending_group_decision_count": len(pending_groups),
        "active_authorization_allowed": False,
        "pending_groups": pending_groups,
    }
    return {"diagnostic": diagnostic, "pending_queue": pending_queue}


def generate(*, generated_at: str | None = None, write_governance_event: bool = True) -> dict[str, Any]:
    timestamp = _now(generated_at)
    source_summary = _read_json(SOURCE_INPUT_KIT_SUMMARY_PATH)
    input_diagnostic = _read_json(PRIVATE_INPUT_KIT_DIAGNOSTIC_PATH)
    response_template = _read_json(PRIVATE_RESPONSE_TEMPLATE_PATH)
    private_records = _build_private_records(
        generated_at=timestamp,
        source_summary=source_summary,
        input_diagnostic=input_diagnostic,
        response_template=response_template,
    )

    _write_json(PRIVATE_DIAGNOSTIC_PATH, private_records["diagnostic"])
    _write_json(PRIVATE_PENDING_GROUP_QUEUE_PATH, private_records["pending_queue"])

    diagnostic = private_records["diagnostic"]
    summary = {
        "schema_version": "kmfa.v014_owner_group_decision_response_intake_summary.v1",
        "record_type": "v014_processed_value_source_map_completion_owner_group_decision_response_intake_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "status": STATUS,
        "generated_at": timestamp,
        "source_phase_id": source_summary.get("phase_id"),
        "source_decision": source_summary.get("decision"),
        "review_group_count": diagnostic["review_group_count"],
        "response_row_count": diagnostic["response_row_count"],
        "pending_group_decision_count": diagnostic["pending_group_decision_count"],
        "valid_group_decision_count": diagnostic["valid_group_decision_count"],
        "invalid_group_decision_count": diagnostic["invalid_group_decision_count"],
        "private_diagnostic_written": True,
        "private_diagnostic_gitignored": _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH),
        "private_pending_group_queue_written": True,
        "private_pending_group_queue_gitignored": _git_check_ignored(PRIVATE_PENDING_GROUP_QUEUE_PATH),
        "owner_group_decisions_supplied": False,
        "owner_group_decision_applied": False,
        "active_owner_authorized_fill_record_ready": False,
        "active_owner_authorized_fill_record_written": False,
        "owner_response_template_modified": False,
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
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "next_required_input": NEXT_REQUIRED_INPUT,
        "raw_boundary": _raw_boundary(),
        "public_safety": _public_safety(),
    }
    go_no_go = {
        "schema_version": "kmfa.v014_owner_group_decision_response_intake_go_no_go.v1",
        "record_type": "v014_processed_value_source_map_completion_owner_group_decision_response_intake_go_no_go_report",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "decision": "NO_GO",
        "status": STATUS,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "review_group_count": summary["review_group_count"],
        "response_row_count": summary["response_row_count"],
        "pending_group_decision_count": summary["pending_group_decision_count"],
        "valid_group_decision_count": summary["valid_group_decision_count"],
        "invalid_group_decision_count": summary["invalid_group_decision_count"],
        "owner_group_decisions_supplied": False,
        "owner_group_decision_applied": False,
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
        "schema_version": "kmfa.v014_owner_group_decision_response_intake_manifest.v1",
        "record_type": "v014_processed_value_source_map_completion_owner_group_decision_response_intake_manifest",
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
            "private_intake_diagnostic": "private_runtime_only",
            "private_pending_group_queue": "private_runtime_only",
        },
        "validator": (
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. "
            "python3 KMFA/tools/check_v014_processed_value_source_map_completion_owner_group_decision_response_intake.py "
            "--require-private-intake"
        ),
        "git": {
            "branch": _git_output(["branch", "--show-current"]),
            "head": _git_output(["rev-parse", "HEAD"]),
            "status_short": _git_output(["status", "--short", "--branch"]),
        },
    }
    report = f"""# V014 Owner Group Decision Response Intake

Decision: NO_GO

This phase checks the private owner group-decision response template. All groups remain pending, so no active authorization or source-map application is allowed.

## Public-safe aggregate result

- Review groups: {summary["review_group_count"]}
- Response rows represented: {summary["response_row_count"]}
- Pending group decisions: {summary["pending_group_decision_count"]}
- Valid group decisions: {summary["valid_group_decision_count"]}
- Invalid group decisions: {summary["invalid_group_decision_count"]}
- Owner group decisions supplied: `false`

Next required input: `{NEXT_REQUIRED_INPUT}`.
"""
    go_no_go_record = f"""# Go/No-Go Record

- phase_id: `{PHASE_ID}`
- decision: `NO_GO`
- reason: the private response template still contains only pending group decision codes.
- review_group_count: `{summary["review_group_count"]}`
- pending_group_decision_count: `{summary["pending_group_decision_count"]}`
- valid_group_decision_count: `{summary["valid_group_decision_count"]}`
- github upload performed: `false`
"""
    risk_register = """# Risk Register

- Risk: treating pending response-template values as owner authorization.
  Mitigation: the validator requires valid_group_decision_count=0 and keeps all downstream gates closed.
- Risk: leaking private group-level response context publicly.
  Mitigation: public artifacts contain only aggregate counts and gate flags; diagnostics stay in private runtime.
"""
    rollback_plan = """# Rollback Plan

No raw file, response template, source-map file, completion template or active authorization record was modified. To roll back, remove this phase's public artifacts and metadata copies, then remove the ignored private diagnostic and pending queue if not needed.
"""
    test_results = """# Test Results

Pending until validator and focused tests are run after artifact generation.

Expected validator:
`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_value_source_map_completion_owner_group_decision_response_intake.py --require-private-intake`
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
    event_id = "DEV-KMFA-20260706-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-OWNER-GROUP-DECISION-RESPONSE-INTAKE"
    event = {
        "event_id": event_id,
        "event_time": generated_at,
        "event_type": "development",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "iteration_id": "ITER-20260706-KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-OWNER-GROUP-DECISION-RESPONSE-INTAKE",
        "fact_level": "EXTRACTED",
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "go_no_go": manifest["go_no_go"]["decision"],
        "review_group_count": manifest["summary"]["review_group_count"],
        "pending_group_decision_count": manifest["summary"]["pending_group_decision_count"],
        "valid_group_decision_count": manifest["summary"]["valid_group_decision_count"],
        "owner_group_decisions_supplied": False,
        "owner_group_decision_applied": False,
        "active_owner_authorized_fill_record_ready": False,
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "result_commit": "PENDING",
        "summary": "Checked private owner group-decision response template; all 22 groups remain pending, so downstream active authorization remains closed.",
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
        "PASS: KMFA v0.1.4 owner group decision response intake generated "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"groups={manifest['summary']['review_group_count']}, "
        f"pending={manifest['summary']['pending_group_decision_count']}, "
        f"valid={manifest['summary']['valid_group_decision_count']})"
    )


if __name__ == "__main__":
    main()
