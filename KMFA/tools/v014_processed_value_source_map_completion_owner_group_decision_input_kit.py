#!/usr/bin/env python3
"""Prepare the KMFA v0.1.4 owner group-decision input kit.

The kit gives the owner or authorized delegate a private, machine-checkable
response template for group-level decisions. This phase does not decide on the
owner's behalf, write active authorization, apply source-map records, or read
raw inbox data.
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
PHASE_ID = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_GROUP_DECISION_INPUT_KIT"
TASK_ID = "KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-OWNER-GROUP-DECISION-INPUT-KIT-20260706"
ACCEPTANCE_ID = "ACC-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-OWNER-GROUP-DECISION-INPUT-KIT"
VERSION = "0.1.4-processed-value-source-map-completion-owner-group-decision-input-kit"
STATUS = "completed_validated_local_only_no_go_owner_group_decision_input_kit_ready"
DIAGNOSTIC_CONCLUSION = "owner_group_decision_input_kit_ready_decisions_not_supplied"
NEXT_REQUIRED_INPUT = "owner_or_authorized_delegate_fills_private_group_decision_response_template"
PENDING_DECISION_CODE = "PENDING_OWNER_OR_AUTHORIZED_DELEGATE_GROUP_DECISION"
ALLOWED_OWNER_GROUP_DECISION_CODES = [
    "CONFIRM_GROUP_CANDIDATE_RANK",
    "CHOOSE_CANDIDATE_RECORD_REF",
    "KEEP_PENDING",
    "MARK_NOT_APPLICABLE",
    "REQUEST_MORE_DIAGNOSTICS",
]

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_group_decision_input_kit_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_group_decision_input_kit_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_group_decision_input_kit_go_no_go_report.json"
REPORT_PATH = HUMAN_DIR / "processed_value_source_map_completion_owner_group_decision_input_kit_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_processed_value_source_map_completion_owner_group_decision_input_kit_summary.json"
)
METADATA_MANIFEST_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_processed_value_source_map_completion_owner_group_decision_input_kit_manifest.json"
)
METADATA_GO_NO_GO_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_processed_value_source_map_completion_owner_group_decision_input_kit_go_no_go_report.json"
)
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"

SOURCE_APPLICATION_SUMMARY_PATH = (
    PROJECT_ROOT
    / "stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_GROUP_DECISION_APPLICATION/machine/processed_value_source_map_completion_owner_group_decision_application_summary.json"
)
PRIVATE_SOURCE_DIR = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_owner_group_decision_application"
)
PRIVATE_SOURCE_DIAGNOSTIC_PATH = PRIVATE_SOURCE_DIR / "private_owner_group_decision_application_diagnostic.json"
PRIVATE_PENDING_QUEUE_PATH = PRIVATE_SOURCE_DIR / "private_owner_group_decision_pending_queue.json"
PRIVATE_GROUPS_PACKET_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_owner_review_groups_path/private_owner_review_groups_path_packet.json"
)

PRIVATE_OUTPUT_DIR = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_owner_group_decision_input_kit"
)
PRIVATE_RESPONSE_TEMPLATE_PATH = PRIVATE_OUTPUT_DIR / "private_owner_group_decision_response_template.json"
PRIVATE_CODEBOOK_PATH = PRIVATE_OUTPUT_DIR / "private_owner_group_decision_codes_zh.md"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_owner_group_decision_input_kit_diagnostic.json"


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
        "private_source_pending_queue_committed": False,
        "private_source_diagnostic_committed": False,
        "private_response_template_committed": False,
        "private_codebook_committed": False,
        "private_diagnostic_committed": False,
        "raw_file_committed": False,
        "raw_filename_committed": False,
        "raw_archive_member_name_committed": False,
        "field_header_plaintext_committed": False,
        "row_value_committed": False,
        "business_value_committed": False,
        "credential_or_secret_committed": False,
    }


def _build_private_records(
    *,
    generated_at: str,
    source_summary: dict[str, Any],
    source_diagnostic: dict[str, Any],
    pending_queue: dict[str, Any],
    groups_packet: dict[str, Any],
) -> dict[str, Any]:
    if source_summary.get("decision") != "NO_GO":
        raise ValueError("source owner group decision application must remain NO_GO")
    rows = pending_queue.get("pending_rows", [])
    groups = groups_packet.get("groups", [])
    if not isinstance(rows, list) or not isinstance(groups, list):
        raise ValueError("pending rows and groups must be lists")

    rows_by_group: dict[str, list[dict[str, Any]]] = defaultdict(list)
    status_by_group: dict[str, str] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        group_id = str(row.get("review_group_id"))
        rows_by_group[group_id].append(row)
        status_by_group[group_id] = str(row.get("candidate_status"))

    template_groups: list[dict[str, Any]] = []
    group_status_counts: Counter[str] = Counter()
    for group in groups:
        if not isinstance(group, dict):
            continue
        group_id = str(group.get("review_group_id"))
        status = str(group.get("candidate_status", status_by_group.get(group_id, "unknown")))
        target_slot_count = len(rows_by_group.get(group_id, []))
        group_status_counts[status] += 1
        template_groups.append(
            {
                "review_group_id": group.get("review_group_id"),
                "candidate_status": status,
                "target_slot_count": target_slot_count,
                "owner_group_decision_code": PENDING_DECISION_CODE,
                "allowed_owner_group_decision_codes": ALLOWED_OWNER_GROUP_DECISION_CODES,
                "selected_candidate_record_ref": None,
                "owner_supplied_mapping_ref": None,
                "owner_note": None,
                "authorization_actor_role_required": "owner_or_authorized_delegate",
                "active_authorization_allowed": False,
            }
        )

    status_row_counts = Counter(str(row.get("candidate_status")) for row in rows if isinstance(row, dict))
    response_template = {
        "schema_version": "kmfa.private.v014_owner_group_decision_response_template.v1",
        "classification": "private_owner_group_decision_response_template_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_owner_group_decision_response_template",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "source_phase_id": source_summary.get("phase_id"),
        "review_group_count": len(template_groups),
        "response_row_count": len(rows),
        "pending_group_template_count": len(template_groups),
        "allowed_owner_group_decision_codes": ALLOWED_OWNER_GROUP_DECISION_CODES,
        "template_is_active_authorization_record": False,
        "owner_group_decisions_supplied": False,
        "active_owner_authorized_fill_record_ready": False,
        "groups": template_groups,
    }
    diagnostic = {
        "schema_version": "kmfa.private.v014_owner_group_decision_input_kit_diagnostic.v1",
        "classification": "private_owner_group_decision_input_kit_diagnostic_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_owner_group_decision_input_kit_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "source_phase_id": source_summary.get("phase_id"),
        "source_diagnostic_phase_id": source_diagnostic.get("phase_id"),
        "review_group_count": len(template_groups),
        "response_row_count": len(rows),
        "pending_group_template_count": len(template_groups),
        "allowed_owner_group_decision_code_count": len(ALLOWED_OWNER_GROUP_DECISION_CODES),
        "candidate_status_group_counts": dict(group_status_counts),
        "candidate_status_response_row_counts": dict(status_row_counts),
        "owner_group_decisions_supplied": False,
        "owner_group_decision_applied": False,
        "active_owner_authorized_fill_record_ready": False,
        "source_map_completion_reapplication_ready": False,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "next_required_input": NEXT_REQUIRED_INPUT,
        "raw_boundary": _raw_boundary(),
    }
    codebook = f"""# KMFA owner group decision codes

This private-only codebook is for the owner or authorized delegate response template.

- `{PENDING_DECISION_CODE}`: 默认待处理，占位符，不是有效授权。
- `CONFIRM_GROUP_CANDIDATE_RANK`: 确认该组按候选排序选择。
- `CHOOSE_CANDIDATE_RECORD_REF`: 指定该组使用某个候选记录引用。
- `KEEP_PENDING`: 明确保持待处理，不进入 source-map application。
- `MARK_NOT_APPLICABLE`: 标记该组不适用。
- `REQUEST_MORE_DIAGNOSTICS`: 要求继续补充诊断。

Only an owner or authorized delegate may replace the pending value with a decision code. This file stays in private runtime and must not be committed.
"""
    return {"response_template": response_template, "diagnostic": diagnostic, "codebook": codebook}


def generate(*, generated_at: str | None = None, write_governance_event: bool = True) -> dict[str, Any]:
    timestamp = _now(generated_at)
    source_summary = _read_json(SOURCE_APPLICATION_SUMMARY_PATH)
    source_diagnostic = _read_json(PRIVATE_SOURCE_DIAGNOSTIC_PATH)
    pending_queue = _read_json(PRIVATE_PENDING_QUEUE_PATH)
    groups_packet = _read_json(PRIVATE_GROUPS_PACKET_PATH)
    private_records = _build_private_records(
        generated_at=timestamp,
        source_summary=source_summary,
        source_diagnostic=source_diagnostic,
        pending_queue=pending_queue,
        groups_packet=groups_packet,
    )

    _write_json(PRIVATE_RESPONSE_TEMPLATE_PATH, private_records["response_template"])
    _write_json(PRIVATE_DIAGNOSTIC_PATH, private_records["diagnostic"])
    _write_text(PRIVATE_CODEBOOK_PATH, private_records["codebook"])

    diagnostic = private_records["diagnostic"]
    summary = {
        "schema_version": "kmfa.v014_owner_group_decision_input_kit_summary.v1",
        "record_type": "v014_processed_value_source_map_completion_owner_group_decision_input_kit_summary",
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
        "pending_group_template_count": diagnostic["pending_group_template_count"],
        "allowed_owner_group_decision_code_count": diagnostic["allowed_owner_group_decision_code_count"],
        "candidate_status_group_counts": diagnostic["candidate_status_group_counts"],
        "candidate_status_response_row_counts": diagnostic["candidate_status_response_row_counts"],
        "private_response_template_written": True,
        "private_response_template_gitignored": _git_check_ignored(PRIVATE_RESPONSE_TEMPLATE_PATH),
        "private_codebook_written": True,
        "private_codebook_gitignored": _git_check_ignored(PRIVATE_CODEBOOK_PATH),
        "private_diagnostic_written": True,
        "private_diagnostic_gitignored": _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH),
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
        "schema_version": "kmfa.v014_owner_group_decision_input_kit_go_no_go.v1",
        "record_type": "v014_processed_value_source_map_completion_owner_group_decision_input_kit_go_no_go_report",
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
        "pending_group_template_count": summary["pending_group_template_count"],
        "allowed_owner_group_decision_code_count": summary["allowed_owner_group_decision_code_count"],
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
        "schema_version": "kmfa.v014_owner_group_decision_input_kit_manifest.v1",
        "record_type": "v014_processed_value_source_map_completion_owner_group_decision_input_kit_manifest",
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
            "private_codebook": "private_runtime_only",
            "private_diagnostic": "private_runtime_only",
        },
        "validator": (
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. "
            "python3 KMFA/tools/check_v014_processed_value_source_map_completion_owner_group_decision_input_kit.py "
            "--require-private-kit"
        ),
        "git": {
            "branch": _git_output(["branch", "--show-current"]),
            "head": _git_output(["rev-parse", "HEAD"]),
            "status_short": _git_output(["status", "--short", "--branch"]),
        },
    }
    report = f"""# V014 Owner Group Decision Input Kit

Decision: NO_GO

This phase prepares a private machine-checkable owner group-decision response template. It does not supply decisions, modify an owner response template, write active authorization, apply source-map records, or compare raw and processed values.

## Public-safe aggregate result

- Review groups: {summary["review_group_count"]}
- Response rows represented: {summary["response_row_count"]}
- Pending group templates: {summary["pending_group_template_count"]}
- Allowed decision code count: {summary["allowed_owner_group_decision_code_count"]}
- Owner group decisions supplied: `false`

Next required input: `{NEXT_REQUIRED_INPUT}`.
"""
    go_no_go_record = f"""# Go/No-Go Record

- phase_id: `{PHASE_ID}`
- decision: `NO_GO`
- reason: the private input kit is ready, but owner or authorized-delegate group-level decisions have not been supplied.
- review_group_count: `{summary["review_group_count"]}`
- response_row_count: `{summary["response_row_count"]}`
- pending_group_template_count: `{summary["pending_group_template_count"]}`
- github upload performed: `false`
"""
    risk_register = """# Risk Register

- Risk: treating a blank response template as owner authorization.
  Mitigation: the template is explicitly non-active and the validator requires owner_group_decisions_supplied=false.
- Risk: leaking private row/group context publicly.
  Mitigation: public artifacts contain only aggregate counts and gate flags; the response template and codebook remain private runtime only.
"""
    rollback_plan = """# Rollback Plan

No raw file, source-map file, completion template, active authorization record or business output was modified. To roll back, remove this phase's public artifacts and metadata copies, then remove the ignored private response template, codebook and diagnostic if not needed.
"""
    test_results = """# Test Results

Pending until validator and focused tests are run after artifact generation.

Expected validator:
`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_value_source_map_completion_owner_group_decision_input_kit.py --require-private-kit`
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
    event_id = "DEV-KMFA-20260706-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-OWNER-GROUP-DECISION-INPUT-KIT"
    event = {
        "event_id": event_id,
        "event_time": generated_at,
        "event_type": "development",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "iteration_id": "ITER-20260706-KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-OWNER-GROUP-DECISION-INPUT-KIT",
        "fact_level": "EXTRACTED",
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "go_no_go": manifest["go_no_go"]["decision"],
        "review_group_count": manifest["summary"]["review_group_count"],
        "response_row_count": manifest["summary"]["response_row_count"],
        "pending_group_template_count": manifest["summary"]["pending_group_template_count"],
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
        "summary": "Prepared a private owner group-decision input kit for 22 groups and 113 response rows; downstream active authorization remains closed until owner or authorized-delegate decisions are supplied.",
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
        "PASS: KMFA v0.1.4 owner group decision input kit generated "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"groups={manifest['summary']['review_group_count']}, "
        f"rows={manifest['summary']['response_row_count']}, "
        f"templates={manifest['summary']['pending_group_template_count']})"
    )


if __name__ == "__main__":
    main()
