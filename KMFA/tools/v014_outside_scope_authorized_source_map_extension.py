#!/usr/bin/env python3
"""Prepare authorized source-map extension intake for outside-scope KMFA slots.

This phase consumes the ignored private outside-linked-scope resolution queue
and prepares a private owner/authorized-delegate fill template. It does not read
the raw inbox, write source-map extension records, materialize values, compare
raw values, reconcile values, or unlock downstream gates.
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
PHASE_ID = "V014_OUTSIDE_SCOPE_AUTHORIZED_SOURCE_MAP_EXTENSION"
TASK_ID = "KMFA-V014-OUTSIDE-SCOPE-AUTHORIZED-SOURCE-MAP-EXTENSION-20260706"
ACCEPTANCE_ID = "ACC-V014-OUTSIDE-SCOPE-AUTHORIZED-SOURCE-MAP-EXTENSION"
VERSION = "0.1.4-outside-scope-authorized-source-map-extension"
STATUS = "completed_validated_local_only_outside_scope_authorized_source_map_extension_input_no_go"
DECISION = "NO_GO"
DIAGNOSTIC_CONCLUSION = "authorized_source_map_extension_input_template_prepared_no_authorized_extension_supplied"
NEXT_RECOMMENDED_PHASE = "V014_OUTSIDE_SCOPE_AUTHORIZED_SOURCE_MAP_EXTENSION_READINESS_RECHECK"
NEXT_REQUIRED_INPUT = "owner_or_authorized_delegate_fills_private_authorized_source_map_extension_template_for_72_slots"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "outside_scope_authorized_source_map_extension_summary.json"
MANIFEST_PATH = MACHINE_DIR / "outside_scope_authorized_source_map_extension_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "outside_scope_authorized_source_map_extension_go_no_go_report.json"
MATRIX_PATH = MACHINE_DIR / "outside_scope_authorized_source_map_extension_matrix_public_safe.json"
REPORT_PATH = HUMAN_DIR / "outside_scope_authorized_source_map_extension_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_outside_scope_authorized_source_map_extension_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_outside_scope_authorized_source_map_extension_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_outside_scope_authorized_source_map_extension_go_no_go_report.json"
METADATA_MATRIX_PATH = PROJECT_ROOT / "metadata/quality/v014_outside_scope_authorized_source_map_extension_matrix_public_safe.json"
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"

SOURCE_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_processed_target_outside_linked_scope_resolution_summary.json"
SOURCE_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_processed_target_outside_linked_scope_resolution_manifest.json"
SOURCE_PRIVATE_QUEUE_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_target_outside_linked_scope_resolution/private_outside_linked_scope_resolution_queue.jsonl"
)

PRIVATE_OUTPUT_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_outside_scope_authorized_source_map_extension"
PRIVATE_TEMPLATE_PATH = PRIVATE_OUTPUT_DIR / "private_authorized_source_map_extension_template.json"
PRIVATE_PENDING_QUEUE_PATH = PRIVATE_OUTPUT_DIR / "private_authorized_source_map_extension_pending_queue.jsonl"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_authorized_source_map_extension_diagnostic.json"
PRIVATE_REPORT_PATH = PRIVATE_OUTPUT_DIR / "private_authorized_source_map_extension.md"

GOVERNANCE_FILES_CHANGED = [
    "KMFA/CHANGELOG.md",
    "KMFA/HANDOFF.md",
    "KMFA/VERSION",
    "KMFA/docs/governance/ASSURANCE_STATUS.yaml",
    "KMFA/docs/governance/DEVELOPMENT_LEDGER.md",
    "KMFA/docs/governance/MODEL_SPEC.md",
    "KMFA/docs/governance/OWNER_STATUS.md",
    "KMFA/docs/governance/STATUS.md",
    "KMFA/docs/governance/TRACEABILITY_MATRIX.csv",
    "KMFA/docs/governance/VERSION_MATRIX.yaml",
    "KMFA/docs/governance/delivery_tasks.yaml",
    "KMFA/docs/governance/development_events.jsonl",
    "KMFA/docs/governance/events.jsonl",
    "KMFA/docs/governance/formula_registry.yaml",
    "KMFA/docs/governance/model_registry.yaml",
    "KMFA/docs/governance/parameter_registry.csv",
    "KMFA/metadata/stage_status.jsonl",
    "KMFA/metadata/traceability/v1_4_stage_phase_task_status.jsonl",
    "KMFA/功能清单.md",
    "KMFA/开发记录.md",
    "KMFA/模型参数文件.md",
]


def _now(generated_at: str | None = None) -> str:
    return generated_at or datetime.now().astimezone().isoformat(timespec="seconds")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path} must contain JSON objects")
        rows.append(value)
    return rows


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


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
        "private_outside_scope_resolution_queue_read_by_this_phase": True,
        "private_authorized_extension_template_written_by_this_phase": True,
        "private_authorized_extension_pending_queue_written_by_this_phase": True,
        "raw_inbox_read_performed_by_this_phase": False,
        "raw_inbox_list_performed_by_this_phase": False,
        "raw_inbox_stat_performed_by_this_phase": False,
        "raw_inbox_hash_or_value_fingerprint_performed_by_this_phase": False,
        "raw_inbox_file_content_hash_performed_by_this_phase": False,
        "raw_inbox_parse_performed_by_this_phase": False,
        "raw_inbox_field_or_header_read_performed_by_this_phase": False,
        "raw_inbox_value_extraction_performed_by_this_phase": False,
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
        "private_source_resolution_queue_committed": False,
        "private_extension_template_committed": False,
        "private_extension_pending_queue_committed": False,
        "private_extension_diagnostic_committed": False,
        "private_source_map_committed": False,
        "private_staging_committed": False,
        "raw_file_committed": False,
        "raw_filename_committed": False,
        "raw_file_hash_committed": False,
        "raw_archive_member_name_committed": False,
        "field_header_plaintext_committed": False,
        "target_slot_detail_committed": False,
        "row_value_committed": False,
        "business_value_committed": False,
        "processed_value_fingerprint_committed": False,
        "credential_or_secret_committed": False,
    }


def _build_private_template(
    *, generated_at: str, source_summary: dict[str, Any], source_queue: list[dict[str, Any]]
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    pending_rows: list[dict[str, Any]] = []
    for row in source_queue:
        if row.get("resolution_status") != "requires_authorized_source_map_extension":
            continue
        pending_rows.append(
            {
                "extension_queue_index": len(pending_rows) + 1,
                "source_resolution_queue_index": row.get("resolution_queue_index"),
                "target_slot_id": row.get("target_slot_id"),
                "target_key_ref_hash": row.get("target_key_ref_hash"),
                "record_ref_hash": row.get("record_ref_hash"),
                "private_processed_ref_hash": row.get("private_processed_ref_hash"),
                "context_group": row.get("context_group"),
                "current_resolution_status": row.get("resolution_status"),
                "required_action": "supply_authorized_source_map_extension",
                "owner_decision_code": "PENDING_AUTHORIZED_SOURCE_MAP_EXTENSION",
                "authorized_source_record_ref_hash": "PENDING_PRIVATE_INPUT",
                "authorized_processed_value_fingerprint": "PENDING_PRIVATE_INPUT",
                "authorized_source_basis": "PENDING_PRIVATE_INPUT",
                "authorized_by": "PENDING_PRIVATE_INPUT",
                "authorization_timestamp": "PENDING_PRIVATE_INPUT",
                "owner_note": "PENDING_PRIVATE_INPUT",
                "source_map_extension_written_by_this_phase": False,
            }
        )

    private_summary = {
        "source_outside_scope_resolution_queue_count": len(source_queue),
        "outside_scope_authorized_source_map_required_count": int(
            source_summary["outside_scope_authorized_source_map_required_count"]
        ),
        "private_authorized_extension_template_item_count": len(pending_rows),
        "private_authorized_extension_pending_queue_count": len(pending_rows),
        "owner_authorized_extension_input_present": False,
        "owner_authorized_extension_record_count": 0,
        "valid_authorized_extension_record_count": 0,
        "invalid_authorized_extension_record_count": 0,
        "missing_authorized_extension_record_count": len(pending_rows),
        "source_map_extension_applied_count": 0,
        "source_map_extension_pending_count": len(pending_rows),
        "source_map_extension_written_by_this_phase": False,
        "full_raw_to_processed_value_comparison_complete": False,
        "business_value_consistency_verified": False,
    }

    template = {
        "schema_version": "kmfa.private.v014_outside_scope_authorized_source_map_extension_template.v1",
        "classification": "private_authorized_source_map_extension_template_do_not_commit",
        "record_type": "v014_outside_scope_authorized_source_map_extension_template",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "source_phase_id": "V014_PROCESSED_TARGET_OUTSIDE_LINKED_SCOPE_RESOLUTION",
        "instructions_zh": [
            "仅由 owner 或授权代理在私有 runtime 中填写。",
            "不得复制 raw 文件名、字段明文、表头、金额明细或业务原值到公开仓库。",
            "填写后必须由后续 readiness/application phase 校验，不能手工绕过 full comparison gate。",
        ],
        "allowed_owner_decision_codes": [
            "AUTHORIZE_SOURCE_MAP_EXTENSION",
            "KEEP_PENDING",
            "EXCLUDE_FROM_FULL_COMPARISON_WITH_OWNER_REASON",
        ],
        "private_summary": private_summary,
        "extension_rows": pending_rows,
        "raw_boundary": _raw_boundary(),
    }
    return template, pending_rows, private_summary


def _build_matrix(summary: dict[str, Any], generated_at: str) -> dict[str, Any]:
    checks = [
        ("source_resolution_queue_available", summary["source_outside_scope_resolution_queue_count"] == 72, summary["source_outside_scope_resolution_queue_count"], 72),
        ("source_required_count_preserved", summary["outside_scope_authorized_source_map_required_count"] == 72, summary["outside_scope_authorized_source_map_required_count"], 72),
        ("private_template_prepared", summary["private_authorized_extension_template_item_count"] == 72, summary["private_authorized_extension_template_item_count"], 72),
        ("owner_input_absent_recorded", summary["owner_authorized_extension_input_present"] is False, summary["owner_authorized_extension_input_present"], False),
        ("valid_extension_zero", summary["valid_authorized_extension_record_count"] == 0, summary["valid_authorized_extension_record_count"], 0),
        ("missing_extension_count", summary["missing_authorized_extension_record_count"] == 72, summary["missing_authorized_extension_record_count"], 72),
        ("source_map_not_written", summary["source_map_extension_written_by_this_phase"] is False, summary["source_map_extension_written_by_this_phase"], False),
        ("downstream_no_go_preserved", summary["decision"] == DECISION, summary["decision"], DECISION),
    ]
    rows = [
        {"check_code": code, "status": "PASS" if ok else "FAIL", "observed_public_safe": observed, "required": required}
        for code, ok, observed, required in checks
    ]
    pass_count = sum(1 for row in rows if row["status"] == "PASS")
    return {
        "schema_version": "kmfa.v014_outside_scope_authorized_source_map_extension_matrix_public_safe.v1",
        "record_type": "v014_outside_scope_authorized_source_map_extension_matrix_public_safe",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "outside_scope_authorized_source_map_extension_check_count": len(rows),
        "outside_scope_authorized_source_map_extension_check_pass_count": pass_count,
        "outside_scope_authorized_source_map_extension_check_fail_count": len(rows) - pass_count,
        "decision": DECISION,
        "checks": rows,
    }


def _append_development_event(manifest: dict[str, Any]) -> None:
    event_id = "DEV-KMFA-20260706-V014-OUTSIDE-SCOPE-AUTHORIZED-SOURCE-MAP-EXTENSION"
    event = {
        "event_id": event_id,
        "event_time": manifest["generated_at"],
        "event_type": "development",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "iteration_id": "ITER-20260706-KMFA-V014-OUTSIDE-SCOPE-AUTHORIZED-SOURCE-MAP-EXTENSION",
        "fact_level": "EXTRACTED",
        "status": STATUS,
        "go_no_go": DECISION,
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "source_outside_scope_resolution_queue_count": manifest["summary"]["source_outside_scope_resolution_queue_count"],
        "private_authorized_extension_template_item_count": manifest["summary"][
            "private_authorized_extension_template_item_count"
        ],
        "valid_authorized_extension_record_count": manifest["summary"]["valid_authorized_extension_record_count"],
        "source_map_extension_applied_count": manifest["summary"]["source_map_extension_applied_count"],
        "source_map_extension_written_by_this_phase": False,
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "summary": "Prepared private authorized source-map extension template for 72 outside-scope target slots while keeping full comparison blocked.",
        "result_commit": "PENDING",
        "files_changed": GOVERNANCE_FILES_CHANGED
        + [
            METADATA_SUMMARY_PATH.as_posix(),
            METADATA_MANIFEST_PATH.as_posix(),
            METADATA_GO_NO_GO_PATH.as_posix(),
            METADATA_MATRIX_PATH.as_posix(),
            SUMMARY_PATH.as_posix(),
            MANIFEST_PATH.as_posix(),
            GO_NO_GO_PATH.as_posix(),
            MATRIX_PATH.as_posix(),
            REPORT_PATH.as_posix(),
            GO_NO_GO_RECORD_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            RISK_REGISTER_PATH.as_posix(),
            ROLLBACK_PATH.as_posix(),
            "KMFA/tests/test_v014_outside_scope_authorized_source_map_extension.py",
            "KMFA/tools/check_v014_outside_scope_authorized_source_map_extension.py",
            "KMFA/tools/v014_outside_scope_authorized_source_map_extension.py",
        ],
    }
    DEVELOPMENT_EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    retained_lines: list[str] = []
    if DEVELOPMENT_EVENTS_PATH.exists():
        for line in DEVELOPMENT_EVENTS_PATH.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                existing_event = json.loads(line)
            except json.JSONDecodeError:
                retained_lines.append(line)
                continue
            if not isinstance(existing_event, dict) or existing_event.get("event_id") != event_id:
                retained_lines.append(line)
    retained_lines.append(json.dumps(event, ensure_ascii=False, sort_keys=True))
    DEVELOPMENT_EVENTS_PATH.write_text("\n".join(retained_lines) + "\n", encoding="utf-8")


def generate(*, generated_at: str | None = None, write_governance_event: bool = True) -> dict[str, Any]:
    timestamp = _now(generated_at)
    source_summary = _read_json(SOURCE_SUMMARY_PATH)
    source_manifest = _read_json(SOURCE_MANIFEST_PATH)
    source_queue = _read_jsonl(SOURCE_PRIVATE_QUEUE_PATH)
    template, pending_rows, private_summary = _build_private_template(
        generated_at=timestamp,
        source_summary=source_summary,
        source_queue=source_queue,
    )

    raw_boundary = _raw_boundary()
    public_safety = _public_safety()
    summary = {
        "schema_version": "kmfa.v014_outside_scope_authorized_source_map_extension_summary.v1",
        "record_type": "v014_outside_scope_authorized_source_map_extension_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "source_phase_id": source_summary["phase_id"],
        "source_decision": source_summary["decision"],
        "source_outside_scope_resolution_queue_count": private_summary["source_outside_scope_resolution_queue_count"],
        "outside_scope_authorized_source_map_required_count": private_summary[
            "outside_scope_authorized_source_map_required_count"
        ],
        "private_authorized_extension_template_item_count": private_summary[
            "private_authorized_extension_template_item_count"
        ],
        "private_authorized_extension_pending_queue_count": private_summary[
            "private_authorized_extension_pending_queue_count"
        ],
        "owner_authorized_extension_input_present": False,
        "owner_authorized_extension_record_count": 0,
        "valid_authorized_extension_record_count": 0,
        "invalid_authorized_extension_record_count": 0,
        "missing_authorized_extension_record_count": private_summary["missing_authorized_extension_record_count"],
        "source_map_extension_applied_count": 0,
        "source_map_extension_pending_count": private_summary["source_map_extension_pending_count"],
        "source_map_extension_written_by_this_phase": False,
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "full_raw_to_processed_value_comparison_complete": False,
        "full_reconciliation_allowed": False,
        "business_value_consistency_verified": False,
        "lineage_full_check_complete": False,
        "formal_report_allowed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "private_template_written": True,
        "private_template_gitignored": _git_check_ignored(PRIVATE_TEMPLATE_PATH),
        "private_pending_queue_written": True,
        "private_pending_queue_gitignored": _git_check_ignored(PRIVATE_PENDING_QUEUE_PATH),
        "private_diagnostic_written": True,
        "private_diagnostic_gitignored": _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH),
        "raw_boundary": raw_boundary,
        "public_safety": public_safety,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
        "next_required_input": NEXT_REQUIRED_INPUT,
    }
    matrix = _build_matrix(summary, timestamp)
    go_no_go = {
        "schema_version": "kmfa.v014_outside_scope_authorized_source_map_extension_go_no_go.v1",
        "record_type": "v014_outside_scope_authorized_source_map_extension_go_no_go",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "private_authorized_extension_template_item_count": summary["private_authorized_extension_template_item_count"],
        "valid_authorized_extension_record_count": 0,
        "missing_authorized_extension_record_count": summary["missing_authorized_extension_record_count"],
        "source_map_extension_written_by_this_phase": False,
        "full_raw_to_processed_value_comparison_complete": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "next_required_input": NEXT_REQUIRED_INPUT,
    }
    diagnostic = {
        "schema_version": "kmfa.private.v014_outside_scope_authorized_source_map_extension_diagnostic.v1",
        "classification": "private_authorized_source_map_extension_diagnostic_do_not_commit",
        "record_type": "v014_outside_scope_authorized_source_map_extension_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "source_manifest_public_ref": source_manifest.get("record_type"),
        "private_summary": private_summary,
        "raw_boundary": raw_boundary,
    }
    manifest = {
        "schema_version": "kmfa.v014_outside_scope_authorized_source_map_extension_manifest.v1",
        "record_type": "v014_outside_scope_authorized_source_map_extension_manifest",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "source_artifacts": [
            SOURCE_SUMMARY_PATH.as_posix(),
            SOURCE_MANIFEST_PATH.as_posix(),
            "private:outside_linked_scope_resolution_queue",
        ],
        "public_artifact_refs": [
            SUMMARY_PATH.as_posix(),
            MANIFEST_PATH.as_posix(),
            GO_NO_GO_PATH.as_posix(),
            MATRIX_PATH.as_posix(),
            REPORT_PATH.as_posix(),
            GO_NO_GO_RECORD_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            RISK_REGISTER_PATH.as_posix(),
            ROLLBACK_PATH.as_posix(),
        ],
        "metadata_artifact_refs": [
            METADATA_SUMMARY_PATH.as_posix(),
            METADATA_MANIFEST_PATH.as_posix(),
            METADATA_GO_NO_GO_PATH.as_posix(),
            METADATA_MATRIX_PATH.as_posix(),
        ],
        "private_artifact_refs": [
            "private:authorized_source_map_extension_template",
            "private:authorized_source_map_extension_pending_queue",
            "private:authorized_source_map_extension_diagnostic",
        ],
        "validator": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_outside_scope_authorized_source_map_extension.py --require-private-template",
        "summary": summary,
        "go_no_go_report": go_no_go,
        "matrix": matrix,
        "git": {
            "head": _git_output(["rev-parse", "HEAD"]),
            "branch": _git_output(["branch", "--show-current"]),
            "status_short_branch": _git_output(["status", "--short", "--branch"]),
        },
    }

    _write_json(PRIVATE_TEMPLATE_PATH, template)
    _write_json(PRIVATE_DIAGNOSTIC_PATH, diagnostic)
    _write_jsonl(PRIVATE_PENDING_QUEUE_PATH, pending_rows)
    _write_text(
        PRIVATE_REPORT_PATH,
        "# Private Authorized Source-Map Extension Template\n\n"
        "72 outside-scope target slots need owner or authorized-delegate source-map extension before full comparison. "
        "This file is ignored and must not be committed.\n",
    )

    for path, payload in (
        (SUMMARY_PATH, summary),
        (MANIFEST_PATH, manifest),
        (GO_NO_GO_PATH, go_no_go),
        (MATRIX_PATH, matrix),
        (METADATA_SUMMARY_PATH, summary),
        (METADATA_MANIFEST_PATH, manifest),
        (METADATA_GO_NO_GO_PATH, go_no_go),
        (METADATA_MATRIX_PATH, matrix),
    ):
        _write_json(path, payload)

    _write_text(
        REPORT_PATH,
        f"""# V014 Outside-Scope Authorized Source-Map Extension

- phase: `{PHASE_ID}`
- status: `{STATUS}`
- decision: `{DECISION}`
- source outside-scope queue records: `{summary["source_outside_scope_resolution_queue_count"]}`
- private extension template items: `{summary["private_authorized_extension_template_item_count"]}`
- valid authorized extension records: `{summary["valid_authorized_extension_record_count"]}`
- missing authorized extension records: `{summary["missing_authorized_extension_record_count"]}`
- source-map extension written by this phase: `false`
- raw-to-processed comparison complete: `false`

This phase prepares a private owner/authorized-delegate extension template only. It does not write source-map extension records or run full reconciliation.
""",
    )
    _write_text(
        GO_NO_GO_RECORD_PATH,
        f"""# Go / No-Go

- decision: `{DECISION}`
- reason: no owner/authorized-delegate source-map extension input has been supplied for 72 outside-scope target slots.
- next required input: `{NEXT_REQUIRED_INPUT}`
- blocked: full comparison, reconciliation, business value consistency, lineage full check, formal report, GitHub upload, app reinstall and business execution.
""",
    )
    _write_text(
        RISK_REGISTER_PATH,
        "# Risk Register\n\n"
        "- Risk: a private fill template could be mistaken for an applied authorization.\n"
        "- Control: source-map extension, full comparison, reconciliation, formal report, upload, reinstall and business execution remain false.\n"
        "- Raw boundary: raw inbox read/list/stat/hash/parse/write/delete/move/rename/copy/normalize/mutation remain false.\n",
    )
    _write_text(
        ROLLBACK_PATH,
        "Remove this phase's public artifacts, metadata copies, private template outputs, tool, validator, focused test and governance entries. The raw data inbox is not modified by this rollback.\n",
    )
    _write_text(
        TEST_RESULTS_PATH,
        f"""# Test Results

Planned commands:

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_outside_scope_authorized_source_map_extension.py KMFA/tools/check_v014_outside_scope_authorized_source_map_extension.py KMFA/tests/test_v014_outside_scope_authorized_source_map_extension.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_outside_scope_authorized_source_map_extension.py --generated-at 2026-07-06T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_outside_scope_authorized_source_map_extension.py --require-private-template`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_outside_scope_authorized_source_map_extension`

Current generated check matrix: `{matrix["outside_scope_authorized_source_map_extension_check_pass_count"]}` pass / `{matrix["outside_scope_authorized_source_map_extension_check_fail_count"]}` fail. This phase does not read, list, parse, copy, move, rename, delete, overwrite, normalize or mutate the raw inbox.
""",
    )

    if write_governance_event:
        _append_development_event(manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generated-at")
    args = parser.parse_args()
    manifest = generate(generated_at=args.generated_at)
    summary = manifest["summary"]
    print(
        "PASS: KMFA v0.1.4 outside-scope authorized source-map extension input generated "
        f"(template_items={summary['private_authorized_extension_template_item_count']}, "
        f"valid_extensions={summary['valid_authorized_extension_record_count']}, "
        f"decision={summary['decision']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
