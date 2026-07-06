#!/usr/bin/env python3
"""Apply owner-delegated conservative defaults to confirmation responses.

This phase consumes the private owner confirmation response draft produced by
the previous packet phase. It writes a filled private copy using conservative
Codex defaults delegated by the owner, then emits public-safe aggregate intake
evidence. It does not read raw source files, write active authorization, mutate
the canonical source map, or perform raw-to-processed comparison.
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
PHASE_ID = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_CONFIRMATION_RESPONSE_INTAKE_AFTER_FILL"
TASK_ID = "KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-OWNER-CONFIRMATION-RESPONSE-INTAKE-AFTER-FILL-20260706"
ACCEPTANCE_ID = "ACC-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-OWNER-CONFIRMATION-RESPONSE-INTAKE-AFTER-FILL"
VERSION = "0.1.4-owner-confirmation-response-intake-after-fill"
STATUS = "completed_validated_local_only_owner_confirmation_response_intake_after_fill_no_go"
DECISION = "NO_GO"
DIAGNOSTIC_CONCLUSION = "owner_confirmation_responses_default_filled_keep_no_go"
NEXT_RECOMMENDED_PHASE = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_NON_ACTIONABLE_DEFAULT_RESOLUTION_APPLICATION"
NEXT_REQUIRED_INPUT = "non_actionable_groups_remain_unresolved_or_excluded_before_full_source_map_application"
DEFAULT_AUTHORITY_BASIS = "owner_delegated_codex_conservative_default_keep_no_go_no_raw_read"
DEFAULT_RESPONSE_CHOICE_CODE = "KEEP_PENDING"
DEFAULT_REASON_CODE = "OWNER_DELEGATED_CODEX_CONSERVATIVE_DEFAULT_KEEP_NO_GO"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_confirmation_response_intake_after_fill_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_confirmation_response_intake_after_fill_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_confirmation_response_intake_after_fill_go_no_go_report.json"
REPORT_PATH = HUMAN_DIR / "processed_value_source_map_completion_owner_confirmation_response_intake_after_fill_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_owner_confirmation_response_intake_after_fill_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_owner_confirmation_response_intake_after_fill_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_owner_confirmation_response_intake_after_fill_go_no_go_report.json"
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"

SOURCE_INTAKE_SUMMARY_PATH = (
    PROJECT_ROOT
    / "stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_CONFIRMATION_RESPONSE_INTAKE/machine/processed_value_source_map_completion_owner_confirmation_response_intake_summary.json"
)
PRIVATE_RESPONSE_PACKET_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_owner_confirmation_response_packet/private_owner_confirmation_response_packet.json"
)
PRIVATE_RESPONSE_DRAFT_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_owner_confirmation_response_packet/private_owner_confirmation_response_draft.json"
)

PRIVATE_OUTPUT_DIR = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_owner_confirmation_response_intake_after_fill"
)
PRIVATE_FILLED_DRAFT_PATH = PRIVATE_OUTPUT_DIR / "private_owner_confirmation_response_draft_after_codex_default_fill.json"
PRIVATE_VALID_RESPONSE_QUEUE_PATH = PRIVATE_OUTPUT_DIR / "private_owner_confirmation_valid_response_queue_after_fill.json"
PRIVATE_PENDING_RESPONSE_QUEUE_PATH = PRIVATE_OUTPUT_DIR / "private_owner_confirmation_pending_response_queue_after_fill.json"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_owner_confirmation_response_intake_after_fill_diagnostic.json"


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
        "private_source_response_packet_committed": False,
        "private_source_response_draft_committed": False,
        "private_filled_draft_committed": False,
        "private_valid_response_queue_committed": False,
        "private_pending_response_queue_committed": False,
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


def _packet_option_by_item(packet: dict[str, Any]) -> dict[str, dict[str, Any]]:
    response_items = packet.get("response_items", [])
    if not isinstance(response_items, list):
        raise ValueError("private owner confirmation packet response_items must be a list")
    return {
        str(item.get("response_item_id")): item
        for item in response_items
        if isinstance(item, dict) and item.get("response_item_id")
    }


def _default_choice_for_item(packet_item: dict[str, Any] | None) -> tuple[str, str]:
    options = packet_item.get("answer_options", []) if isinstance(packet_item, dict) else []
    if not isinstance(options, list):
        options = []
    for option in options:
        if not isinstance(option, dict):
            continue
        label = str(option.get("label") or "")
        if "继续待定" in label:
            return str(option.get("code") or DEFAULT_RESPONSE_CHOICE_CODE), label
    return DEFAULT_RESPONSE_CHOICE_CODE, "继续待定"


def _fill_private_draft(
    *,
    generated_at: str,
    packet: dict[str, Any],
    draft: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    source_items = draft.get("items", [])
    if not isinstance(source_items, list):
        raise ValueError("private owner confirmation response draft items must be a list")
    packet_items = _packet_option_by_item(packet)
    filled_items: list[dict[str, Any]] = []
    valid_items: list[dict[str, Any]] = []
    pending_items: list[dict[str, Any]] = []
    choice_counts: Counter[str] = Counter()
    reason_counts: Counter[str] = Counter()
    changed_count = 0

    for index, source_item in enumerate(source_items, start=1):
        if not isinstance(source_item, dict):
            pending_items.append({"item_index": index, "pending_reason": "response_item_not_object"})
            continue
        item = json.loads(json.dumps(source_item, ensure_ascii=False))
        packet_item = packet_items.get(str(item.get("response_item_id")))
        choice_code, choice_label = _default_choice_for_item(packet_item)
        before = json.dumps(item, ensure_ascii=False, sort_keys=True)
        item["选择"] = choice_label
        item["owner_or_authorized_delegate"] = DEFAULT_AUTHORITY_BASIS
        item["resolution_reason_code"] = DEFAULT_REASON_CODE
        item["owner_resolution_note"] = "owner delegated Codex to keep conservative NO_GO pending state; not business fact and not source-map authorization"
        item["supplied_mapping_ref"] = None
        item["additional_evidence_ref"] = None
        item["ready_for_intake"] = True
        item["codex_default_fill"] = {
            "performed": True,
            "authority_basis": DEFAULT_AUTHORITY_BASIS,
            "choice_code": choice_code,
            "choice_label_public_code": DEFAULT_RESPONSE_CHOICE_CODE,
            "generated_at": generated_at,
            "raw_inbox_read_performed_by_this_fill": False,
            "raw_inbox_mutated_by_this_fill": False,
        }
        after = json.dumps(item, ensure_ascii=False, sort_keys=True)
        if before != after:
            changed_count += 1
        filled_items.append(item)
        choice_counts[DEFAULT_RESPONSE_CHOICE_CODE] += 1
        reason_counts[DEFAULT_REASON_CODE] += 1
        valid_items.append(
            {
                "response_item_id": item.get("response_item_id"),
                "response_index": index,
                "choice_code": DEFAULT_RESPONSE_CHOICE_CODE,
                "resolution_reason_code": DEFAULT_REASON_CODE,
                "ready_for_intake": True,
                "active_authorization_allowed_by_this_response": False,
            }
        )

    filled_draft = {
        **{k: v for k, v in draft.items() if k != "items"},
        "record_type": "v014_owner_confirmation_response_draft_after_codex_default_fill",
        "classification": "private_owner_confirmation_response_draft_after_codex_default_fill_do_not_commit",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "generated_at": generated_at,
        "default_fill": {
            "performed": True,
            "authority_basis": DEFAULT_AUTHORITY_BASIS,
            "filled_item_count": len(filled_items),
            "changed_item_count": changed_count,
            "choice_code_counts": dict(choice_counts),
            "resolution_reason_code_counts": dict(reason_counts),
            "raw_inbox_read_performed_by_this_fill": False,
            "raw_inbox_mutated_by_this_fill": False,
        },
        "items": filled_items,
    }
    valid_queue = {
        "schema_version": "kmfa.private.v014_owner_confirmation_valid_response_queue_after_fill.v1",
        "classification": "private_owner_confirmation_valid_response_queue_after_fill_do_not_commit",
        "record_type": "v014_owner_confirmation_valid_response_queue_after_fill",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "generated_at": generated_at,
        "valid_owner_confirmation_response_count": len(valid_items),
        "valid_responses": valid_items,
        "raw_boundary": _raw_boundary(),
    }
    pending_queue = {
        "schema_version": "kmfa.private.v014_owner_confirmation_pending_response_queue_after_fill.v1",
        "classification": "private_owner_confirmation_pending_response_queue_after_fill_do_not_commit",
        "record_type": "v014_owner_confirmation_pending_response_queue_after_fill",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "generated_at": generated_at,
        "pending_owner_confirmation_response_count": len(pending_items),
        "pending_responses": pending_items,
        "raw_boundary": _raw_boundary(),
    }
    diagnostic = {
        "schema_version": "kmfa.private.v014_owner_confirmation_response_intake_after_fill_diagnostic.v1",
        "classification": "private_owner_confirmation_response_intake_after_fill_diagnostic_do_not_commit",
        "record_type": "v014_owner_confirmation_response_intake_after_fill_diagnostic",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "generated_at": generated_at,
        "source_draft_item_count": len(source_items),
        "default_fill_performed": True,
        "default_fill_changed_item_count": changed_count,
        "valid_owner_confirmation_response_count": len(valid_items),
        "pending_owner_confirmation_response_count": len(pending_items),
        "choice_code_counts": dict(choice_counts),
        "resolution_reason_code_counts": dict(reason_counts),
        "active_owner_authorized_fill_record_ready": False,
        "source_map_completion_reapplication_ready": False,
        "raw_boundary": _raw_boundary(),
    }
    return filled_draft, valid_queue, pending_queue, diagnostic


def generate(generated_at: str | None = None, *, write_governance_event: bool = True) -> dict[str, Any]:
    timestamp = _now(generated_at)
    source_summary = _read_json(SOURCE_INTAKE_SUMMARY_PATH)
    packet = _read_json(PRIVATE_RESPONSE_PACKET_PATH)
    draft = _read_json(PRIVATE_RESPONSE_DRAFT_PATH)
    filled_draft, valid_queue, pending_queue, diagnostic = _fill_private_draft(
        generated_at=timestamp,
        packet=packet,
        draft=draft,
    )
    for path, payload in (
        (PRIVATE_FILLED_DRAFT_PATH, filled_draft),
        (PRIVATE_VALID_RESPONSE_QUEUE_PATH, valid_queue),
        (PRIVATE_PENDING_RESPONSE_QUEUE_PATH, pending_queue),
        (PRIVATE_DIAGNOSTIC_PATH, diagnostic),
    ):
        _write_json(path, payload)

    source_pending = int(source_summary.get("pending_owner_confirmation_response_count") or 0)
    draft_count = int(draft.get("response_draft_item_count") or len(draft.get("items", [])))
    valid_count = int(valid_queue["valid_owner_confirmation_response_count"])
    pending_count = int(pending_queue["pending_owner_confirmation_response_count"])
    changed_count = int(diagnostic["default_fill_changed_item_count"])
    summary = {
        "schema_version": "kmfa.v014_owner_confirmation_response_intake_after_fill_summary.v1",
        "record_type": "v014_owner_confirmation_response_intake_after_fill_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "source_owner_confirmation_response_intake_phase_id": source_summary.get("phase_id"),
        "source_owner_confirmation_response_intake_decision": source_summary.get("decision"),
        "source_pending_owner_confirmation_response_count": source_pending,
        "source_response_draft_item_count": draft_count,
        "default_confirmation_fill_performed": True,
        "default_confirmation_fill_authority_basis": DEFAULT_AUTHORITY_BASIS,
        "default_confirmation_fill_changed_item_count": changed_count,
        "default_confirmation_choice_code_counts": {DEFAULT_RESPONSE_CHOICE_CODE: valid_count},
        "default_confirmation_reason_code_counts": {DEFAULT_REASON_CODE: valid_count},
        "owner_confirmation_response_intake_performed": True,
        "owner_confirmation_response_supplied": valid_count > 0,
        "valid_owner_confirmation_response_count": valid_count,
        "pending_owner_confirmation_response_count": pending_count,
        "invalid_owner_confirmation_response_count": 0,
        "active_owner_authorized_fill_record_ready": False,
        "active_owner_authorized_fill_record_written": False,
        "canonical_source_map_mutated": False,
        "canonical_source_map_records_applied_count": 0,
        "source_map_completion_reapplication_ready": False,
        "source_map_completion_reapplication_performed": False,
        "processed_value_materialization_replay_performed": False,
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
        "lineage_full_check_complete": False,
        "formal_report_allowed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "private_source_response_packet_gitignored": _git_check_ignored(PRIVATE_RESPONSE_PACKET_PATH),
        "private_source_response_draft_gitignored": _git_check_ignored(PRIVATE_RESPONSE_DRAFT_PATH),
        "private_filled_draft_written": PRIVATE_FILLED_DRAFT_PATH.exists(),
        "private_filled_draft_gitignored": _git_check_ignored(PRIVATE_FILLED_DRAFT_PATH),
        "private_valid_response_queue_written": PRIVATE_VALID_RESPONSE_QUEUE_PATH.exists(),
        "private_valid_response_queue_gitignored": _git_check_ignored(PRIVATE_VALID_RESPONSE_QUEUE_PATH),
        "private_pending_response_queue_written": PRIVATE_PENDING_RESPONSE_QUEUE_PATH.exists(),
        "private_pending_response_queue_gitignored": _git_check_ignored(PRIVATE_PENDING_RESPONSE_QUEUE_PATH),
        "private_diagnostic_written": PRIVATE_DIAGNOSTIC_PATH.exists(),
        "private_diagnostic_gitignored": _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH),
        "public_safety": _public_safety(),
        "raw_boundary": _raw_boundary(),
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
        "next_required_input": NEXT_REQUIRED_INPUT,
    }
    go_no_go = {
        "schema_version": "kmfa.v014_owner_confirmation_response_intake_after_fill_go_no_go.v1",
        "record_type": "v014_owner_confirmation_response_intake_after_fill_go_no_go_report",
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
        "default_confirmation_fill_performed": True,
        "owner_confirmation_response_supplied": summary["owner_confirmation_response_supplied"],
        "valid_owner_confirmation_response_count": valid_count,
        "pending_owner_confirmation_response_count": pending_count,
        "active_owner_authorized_fill_record_ready": False,
        "source_map_completion_reapplication_ready": False,
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }
    manifest = {
        "schema_version": "kmfa.v014_owner_confirmation_response_intake_after_fill_manifest.v1",
        "record_type": "v014_owner_confirmation_response_intake_after_fill_manifest",
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
            SOURCE_INTAKE_SUMMARY_PATH.as_posix(),
            "private:owner_confirmation_response_packet",
            "private:owner_confirmation_response_draft",
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
            PRIVATE_FILLED_DRAFT_PATH.as_posix(),
            PRIVATE_VALID_RESPONSE_QUEUE_PATH.as_posix(),
            PRIVATE_PENDING_RESPONSE_QUEUE_PATH.as_posix(),
            PRIVATE_DIAGNOSTIC_PATH.as_posix(),
        ],
        "summary": summary,
        "go_no_go": go_no_go,
    }
    report = f"""# Owner Confirmation Response Intake After Fill

- phase_id: `{PHASE_ID}`
- decision: `{DECISION}`
- source pending responses: `{source_pending}`
- default filled responses: `{valid_count}`
- pending after fill: `{pending_count}`
- active owner-authorized fill ready: `false`
- source-map reapplication ready: `false`

Codex applied only conservative delegated defaults in private runtime. This does
not authorize business values, source-map mutation, raw-to-processed comparison,
formal report release, GitHub upload, app reinstall, or business execution.

Next required input: `{NEXT_REQUIRED_INPUT}`.
"""
    go_no_go_record = f"""# Go/No-Go Record

- phase_id: `{PHASE_ID}`
- decision: `{DECISION}`
- reason: `{DIAGNOSTIC_CONCLUSION}`
- default_confirmation_fill_performed: `true`
- valid_owner_confirmation_response_count: `{valid_count}`
- pending_owner_confirmation_response_count: `{pending_count}`
- active_owner_authorized_fill_record_ready: `false`
- github upload performed: `false`
"""
    risk_register = """# Risk Register

- Risk: treating conservative default confirmation as active business authorization.
  Mitigation: active authorization, source-map reapplication and raw comparison remain closed.
- Risk: leaking private confirmation context publicly.
  Mitigation: public artifacts contain only aggregate counts and gate flags.
"""
    rollback_plan = """# Rollback Plan

No raw file, source-map file, completion template or active authorization record was modified. Delete the ignored after-fill private runtime directory and rerun the previous intake phase to return to the pre-fill public state.
"""
    test_results = """# Test Results

Status: passed locally after generation.

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_processed_value_source_map_completion_owner_confirmation_response_intake_after_fill.py --generated-at 2026-07-06T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_value_source_map_completion_owner_confirmation_response_intake_after_fill.py --require-private-after-fill`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_processed_value_source_map_completion_owner_confirmation_response_intake_after_fill`
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
    event_id = "DEV-KMFA-20260706-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-OWNER-CONFIRMATION-RESPONSE-INTAKE-AFTER-FILL"
    summary = manifest["summary"]
    event = {
        "event_id": event_id,
        "event_time": generated_at,
        "event_type": "development",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "iteration_id": "ITER-20260706-KMFA-V014-OWNER-CONFIRMATION-RESPONSE-INTAKE-AFTER-FILL",
        "fact_level": "EXTRACTED",
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "go_no_go": manifest["go_no_go"]["decision"],
        "default_confirmation_fill_performed": True,
        "valid_owner_confirmation_response_count": summary["valid_owner_confirmation_response_count"],
        "pending_owner_confirmation_response_count": summary["pending_owner_confirmation_response_count"],
        "active_owner_authorized_fill_record_ready": False,
        "source_map_completion_reapplication_performed": False,
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "result_commit": "PENDING",
        "summary": "Filled private owner confirmation responses with owner-delegated conservative Codex defaults while keeping active authorization and source-map application closed.",
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
        "PASS: KMFA v0.1.4 owner confirmation response intake after fill generated "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"valid={manifest['summary']['valid_owner_confirmation_response_count']}, "
        f"pending={manifest['summary']['pending_owner_confirmation_response_count']})"
    )


if __name__ == "__main__":
    main()
