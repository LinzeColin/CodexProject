#!/usr/bin/env python3
"""Recheck readiness of outside-scope authorized source-map extension input.

This phase reads the ignored private extension template produced by the prior
phase and records whether owner/authorized-delegate input is ready for a later
source-map extension application phase. It does not read the raw inbox, mutate
the template, write source-map records, compare values, reconcile values, or
unlock downstream gates.
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
PHASE_ID = "V014_OUTSIDE_SCOPE_AUTHORIZED_SOURCE_MAP_EXTENSION_READINESS_RECHECK"
TASK_ID = "KMFA-V014-OUTSIDE-SCOPE-AUTHORIZED-SOURCE-MAP-EXTENSION-READINESS-RECHECK-20260706"
ACCEPTANCE_ID = "ACC-V014-OUTSIDE-SCOPE-AUTHORIZED-SOURCE-MAP-EXTENSION-READINESS-RECHECK"
VERSION = "0.1.4-outside-scope-authorized-source-map-extension-readiness-recheck"
STATUS = "completed_validated_local_only_outside_scope_authorized_source_map_extension_readiness_no_go"
DECISION = "NO_GO"
DIAGNOSTIC_CONCLUSION = "authorized_source_map_extension_template_rechecked_all_items_still_pending"
NEXT_RECOMMENDED_PHASE = "V014_OUTSIDE_SCOPE_AUTHORIZED_SOURCE_MAP_EXTENSION_READINESS_RECHECK_AFTER_OWNER_INPUT"
NEXT_REQUIRED_INPUT = "owner_or_authorized_delegate_fills_private_authorized_source_map_extension_template_for_72_slots"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "outside_scope_authorized_source_map_extension_readiness_recheck_summary.json"
MANIFEST_PATH = MACHINE_DIR / "outside_scope_authorized_source_map_extension_readiness_recheck_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "outside_scope_authorized_source_map_extension_readiness_recheck_go_no_go_report.json"
MATRIX_PATH = MACHINE_DIR / "outside_scope_authorized_source_map_extension_readiness_recheck_matrix_public_safe.json"
REPORT_PATH = HUMAN_DIR / "outside_scope_authorized_source_map_extension_readiness_recheck_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_outside_scope_authorized_source_map_extension_readiness_recheck_summary.json"
)
METADATA_MANIFEST_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_outside_scope_authorized_source_map_extension_readiness_recheck_manifest.json"
)
METADATA_GO_NO_GO_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_outside_scope_authorized_source_map_extension_readiness_recheck_go_no_go_report.json"
)
METADATA_MATRIX_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_outside_scope_authorized_source_map_extension_readiness_recheck_matrix_public_safe.json"
)
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"

SOURCE_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_outside_scope_authorized_source_map_extension_summary.json"
SOURCE_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_outside_scope_authorized_source_map_extension_manifest.json"
SOURCE_TEMPLATE_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_outside_scope_authorized_source_map_extension/private_authorized_source_map_extension_template.json"
)
SOURCE_PENDING_QUEUE_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_outside_scope_authorized_source_map_extension/private_authorized_source_map_extension_pending_queue.jsonl"
)

PRIVATE_OUTPUT_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_outside_scope_authorized_source_map_extension_readiness_recheck"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_authorized_source_map_extension_readiness_diagnostic.json"
PRIVATE_BLOCKER_QUEUE_PATH = PRIVATE_OUTPUT_DIR / "private_authorized_source_map_extension_readiness_blocker_queue.jsonl"
PRIVATE_REPORT_PATH = PRIVATE_OUTPUT_DIR / "private_authorized_source_map_extension_readiness.md"

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

ALLOWED_DECISIONS = {
    "PENDING_AUTHORIZED_SOURCE_MAP_EXTENSION",
    "AUTHORIZE_SOURCE_MAP_EXTENSION",
    "KEEP_PENDING",
    "EXCLUDE_FROM_FULL_COMPARISON_WITH_OWNER_REASON",
}
PENDING_MARKERS = {"", "PENDING_PRIVATE_INPUT", None}
AUTHORIZATION_REQUIRED_FIELDS = [
    "authorized_source_record_ref_hash",
    "authorized_processed_value_fingerprint",
    "authorized_source_basis",
    "authorized_by",
    "authorization_timestamp",
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


def _raw_boundary() -> dict[str, bool]:
    return {
        "raw_data_root_readonly_policy_active": True,
        "private_authorized_extension_template_read_by_this_phase": True,
        "private_authorized_extension_pending_queue_read_by_this_phase": True,
        "private_readiness_diagnostic_written_by_this_phase": True,
        "private_readiness_blocker_queue_written_by_this_phase": True,
        "private_template_mutated_by_this_phase": False,
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
        "private_template_committed": False,
        "private_pending_queue_committed": False,
        "private_readiness_diagnostic_committed": False,
        "private_readiness_blocker_queue_committed": False,
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


def _decision_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts = {decision: 0 for decision in ALLOWED_DECISIONS}
    counts["invalid_decision_code"] = 0
    for row in rows:
        decision = row.get("owner_decision_code")
        if decision in counts:
            counts[decision] += 1
        else:
            counts["invalid_decision_code"] += 1
    return counts


def _is_valid_authorization(row: dict[str, Any]) -> bool:
    if row.get("owner_decision_code") != "AUTHORIZE_SOURCE_MAP_EXTENSION":
        return False
    return all(row.get(field) not in PENDING_MARKERS for field in AUTHORIZATION_REQUIRED_FIELDS)


def _build_readiness(
    *, generated_at: str, source_summary: dict[str, Any], template: dict[str, Any], pending_queue: list[dict[str, Any]]
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    extension_rows = template.get("extension_rows")
    if not isinstance(extension_rows, list):
        raise ValueError("private template extension_rows must be a list")

    counts = _decision_counts(extension_rows)
    valid_authorized = sum(1 for row in extension_rows if _is_valid_authorization(row))
    invalid_authorized = counts["AUTHORIZE_SOURCE_MAP_EXTENSION"] - valid_authorized
    keep_pending = counts["KEEP_PENDING"]
    owner_exclusions = counts["EXCLUDE_FROM_FULL_COMPARISON_WITH_OWNER_REASON"]
    pending = counts["PENDING_AUTHORIZED_SOURCE_MAP_EXTENSION"]
    invalid_decision = counts["invalid_decision_code"]
    owner_records = len(extension_rows) - pending - invalid_decision
    ready_count = valid_authorized
    blocker_count = len(extension_rows) - ready_count
    readiness_passed = blocker_count == 0 and ready_count == len(extension_rows) and len(extension_rows) > 0

    blocker_queue = [
        {
            "readiness_queue_index": index + 1,
            "source_extension_queue_index": row.get("extension_queue_index"),
            "owner_decision_code": row.get("owner_decision_code", "INVALID_OR_MISSING"),
            "readiness_status": "pending_owner_or_authorized_delegate_input"
            if row.get("owner_decision_code") == "PENDING_AUTHORIZED_SOURCE_MAP_EXTENSION"
            else "invalid_or_non_application_decision",
            "required_action": "fill_private_authorized_source_map_extension_template",
        }
        for index, row in enumerate(extension_rows)
        if not _is_valid_authorization(row)
    ]

    private_summary = {
        "source_outside_scope_resolution_queue_count": int(source_summary["source_outside_scope_resolution_queue_count"]),
        "outside_scope_authorized_source_map_required_count": int(
            source_summary["outside_scope_authorized_source_map_required_count"]
        ),
        "private_authorized_extension_template_item_count": len(extension_rows),
        "private_authorized_extension_pending_queue_count": len(pending_queue),
        "owner_authorized_extension_input_present": owner_records > 0,
        "owner_authorized_extension_record_count": owner_records,
        "valid_authorized_extension_record_count": valid_authorized,
        "invalid_authorized_extension_record_count": invalid_authorized + invalid_decision,
        "keep_pending_extension_record_count": keep_pending,
        "owner_exclusion_extension_record_count": owner_exclusions,
        "missing_authorized_extension_record_count": pending,
        "source_map_extension_ready_count": ready_count,
        "source_map_extension_blocker_count": blocker_count,
        "source_map_extension_application_ready": readiness_passed,
        "source_map_extension_applied_count": 0,
        "source_map_extension_pending_count": blocker_count,
        "source_map_extension_written_by_this_phase": False,
        "full_raw_to_processed_value_comparison_complete": False,
        "business_value_consistency_verified": False,
    }

    diagnostic = {
        "schema_version": "kmfa.private.v014_outside_scope_authorized_source_map_extension_readiness_diagnostic.v1",
        "classification": "private_authorized_source_map_extension_readiness_diagnostic_do_not_commit",
        "record_type": "v014_outside_scope_authorized_source_map_extension_readiness_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "private_summary": private_summary,
        "raw_boundary": _raw_boundary(),
    }
    return diagnostic, blocker_queue, private_summary


def _build_summary(generated_at: str, private_summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v014_outside_scope_authorized_source_map_extension_readiness_recheck_summary.v1",
        "record_type": "v014_outside_scope_authorized_source_map_extension_readiness_recheck_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": generated_at,
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
        "next_required_input": NEXT_REQUIRED_INPUT,
        **private_summary,
        "readiness_recheck_performed_by_this_phase": True,
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "full_reconciliation_allowed": False,
        "lineage_full_check_complete": False,
        "formal_report_allowed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "raw_boundary": _raw_boundary(),
        "public_safety": _public_safety(),
    }


def _build_go_no_go(summary: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "source_outside_scope_resolution_queue_count",
        "private_authorized_extension_template_item_count",
        "owner_authorized_extension_input_present",
        "valid_authorized_extension_record_count",
        "missing_authorized_extension_record_count",
        "source_map_extension_ready_count",
        "source_map_extension_blocker_count",
        "source_map_extension_application_ready",
        "source_map_extension_written_by_this_phase",
        "full_raw_to_processed_value_comparison_complete",
        "business_value_consistency_verified",
    ]
    return {
        "schema_version": "kmfa.v014_outside_scope_authorized_source_map_extension_readiness_go_no_go.v1",
        "record_type": "v014_outside_scope_authorized_source_map_extension_readiness_go_no_go_report",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": summary["generated_at"],
        "decision": DECISION,
        "status": STATUS,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "next_required_input": NEXT_REQUIRED_INPUT,
        **{key: summary[key] for key in keys},
        "blocked_next_steps": [
            "source_map_extension_application",
            "full_raw_to_processed_value_comparison",
            "processed_data_reconciliation",
            "business_value_consistency",
            "lineage_full_check",
            "formal_report",
            "github_upload",
            "app_reinstall",
            "business_execution",
        ],
    }


def _build_matrix(summary: dict[str, Any]) -> dict[str, Any]:
    checks = [
        ("source_summary_available", True, "available"),
        ("template_row_count_matches_expected", summary["private_authorized_extension_template_item_count"] == 72, "72"),
        ("pending_queue_count_matches_expected", summary["private_authorized_extension_pending_queue_count"] == 72, "72"),
        ("all_rows_still_pending", summary["missing_authorized_extension_record_count"] == 72, "72"),
        ("valid_authorization_absent", summary["valid_authorized_extension_record_count"] == 0, "0"),
        ("source_map_application_not_ready", summary["source_map_extension_application_ready"] is False, "false"),
        ("raw_inbox_untouched", summary["raw_boundary"]["raw_inbox_mutated_by_this_phase"] is False, "false"),
        ("downstream_gates_closed", summary["business_execution_performed"] is False, "false"),
    ]
    rows = [
        {
            "check_code": code,
            "status": "PASS" if ok else "FAIL",
            "observed": str(ok).lower(),
            "required": required,
        }
        for code, ok, required in checks
    ]
    pass_count = sum(1 for row in rows if row["status"] == "PASS")
    return {
        "schema_version": "kmfa.v014_outside_scope_authorized_source_map_extension_readiness_matrix_public_safe.v1",
        "record_type": "v014_outside_scope_authorized_source_map_extension_readiness_matrix_public_safe",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": summary["generated_at"],
        "readiness_recheck_count": len(rows),
        "readiness_recheck_pass_count": pass_count,
        "readiness_recheck_fail_count": len(rows) - pass_count,
        "decision": DECISION,
        "checks": rows,
    }


def _append_development_event(manifest: dict[str, Any]) -> None:
    event_id = "DEV-KMFA-20260706-V014-OUTSIDE-SCOPE-AUTHORIZED-SOURCE-MAP-EXTENSION-READINESS-RECHECK"
    summary = manifest["summary"]
    event = {
        "event_id": event_id,
        "event_time": manifest["generated_at"],
        "event_type": "development",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "iteration_id": "ITER-20260706-KMFA-V014-OUTSIDE-SCOPE-AUTHORIZED-SOURCE-MAP-EXTENSION-READINESS-RECHECK",
        "fact_level": "EXTRACTED",
        "status": STATUS,
        "go_no_go": DECISION,
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "private_authorized_extension_template_item_count": summary[
            "private_authorized_extension_template_item_count"
        ],
        "valid_authorized_extension_record_count": summary["valid_authorized_extension_record_count"],
        "missing_authorized_extension_record_count": summary["missing_authorized_extension_record_count"],
        "source_map_extension_application_ready": False,
        "source_map_extension_written_by_this_phase": False,
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "summary": "Rechecked private outside-scope source-map extension readiness and kept application blocked because all template rows remain pending.",
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
            "KMFA/tests/test_v014_outside_scope_authorized_source_map_extension_readiness_recheck.py",
            "KMFA/tools/check_v014_outside_scope_authorized_source_map_extension_readiness_recheck.py",
            "KMFA/tools/v014_outside_scope_authorized_source_map_extension_readiness_recheck.py",
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
    template = _read_json(SOURCE_TEMPLATE_PATH)
    pending_queue = _read_jsonl(SOURCE_PENDING_QUEUE_PATH)
    diagnostic, blocker_queue, private_summary = _build_readiness(
        generated_at=timestamp,
        source_summary=source_summary,
        template=template,
        pending_queue=pending_queue,
    )
    summary = _build_summary(timestamp, private_summary)
    go_no_go = _build_go_no_go(summary)
    matrix = _build_matrix(summary)
    manifest = {
        "schema_version": "kmfa.v014_outside_scope_authorized_source_map_extension_readiness_manifest.v1",
        "record_type": "v014_outside_scope_authorized_source_map_extension_readiness_recheck_manifest",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "source_phase_id": "V014_OUTSIDE_SCOPE_AUTHORIZED_SOURCE_MAP_EXTENSION",
        "source_manifest_version": source_manifest.get("version"),
        "summary": summary,
        "go_no_go_report": go_no_go,
        "matrix": matrix,
        "git": {
            "head": _git_output(["rev-parse", "HEAD"]),
            "branch": _git_output(["branch", "--show-current"]),
            "status_short": _git_output(["status", "--short", "--branch"]),
        },
    }

    for path, payload in (
        (SUMMARY_PATH, summary),
        (MANIFEST_PATH, manifest),
        (GO_NO_GO_PATH, go_no_go),
        (MATRIX_PATH, matrix),
        (METADATA_SUMMARY_PATH, summary),
        (METADATA_MANIFEST_PATH, manifest),
        (METADATA_GO_NO_GO_PATH, go_no_go),
        (METADATA_MATRIX_PATH, matrix),
        (PRIVATE_DIAGNOSTIC_PATH, diagnostic),
    ):
        _write_json(path, payload)
    _write_jsonl(PRIVATE_BLOCKER_QUEUE_PATH, blocker_queue)

    _write_text(
        PRIVATE_REPORT_PATH,
        "Private readiness recheck: all current extension rows remain pending; no source-map application is ready.\n",
    )
    _write_text(
        REPORT_PATH,
        f"""# V014 Outside-Scope Authorized Source-Map Extension Readiness Recheck

- phase: `{PHASE_ID}`
- status: `{STATUS}`
- decision: `{DECISION}`
- private extension template items: `{summary["private_authorized_extension_template_item_count"]}`
- valid authorized extension records: `{summary["valid_authorized_extension_record_count"]}`
- missing authorized extension records: `{summary["missing_authorized_extension_record_count"]}`
- source-map application ready: `false`
- source-map extension written by this phase: `false`
- raw-to-processed comparison complete: `false`

This phase rechecks readiness only. It does not write source-map extension records or run full reconciliation.
""",
    )
    _write_text(
        GO_NO_GO_RECORD_PATH,
        f"""# Go / No-Go

- decision: `{DECISION}`
- reason: no valid owner/authorized-delegate source-map extension records were found.
- next required input: `{NEXT_REQUIRED_INPUT}`
- blocked: source-map extension application, full comparison, reconciliation, business value consistency, lineage full check, formal report, GitHub upload, app reinstall and business execution.
""",
    )
    _write_text(
        RISK_REGISTER_PATH,
        "# Risk Register\n\n"
        "- Risk: readiness recheck could be mistaken for actual authorization.\n"
        "- Control: source-map extension application, full comparison, reconciliation, formal report, upload, reinstall and business execution remain false.\n"
        "- Raw boundary: raw inbox read/list/stat/hash/parse/write/delete/move/rename/copy/normalize/mutation remain false.\n",
    )
    _write_text(
        ROLLBACK_PATH,
        "Remove this phase's public artifacts, metadata copies, private readiness outputs, tool, validator, focused test and governance entries. The raw data inbox is not modified by this rollback.\n",
    )
    _write_text(
        TEST_RESULTS_PATH,
        f"""# Test Results

Planned commands:

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_outside_scope_authorized_source_map_extension_readiness_recheck.py KMFA/tools/check_v014_outside_scope_authorized_source_map_extension_readiness_recheck.py KMFA/tests/test_v014_outside_scope_authorized_source_map_extension_readiness_recheck.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_outside_scope_authorized_source_map_extension_readiness_recheck.py --generated-at 2026-07-06T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_outside_scope_authorized_source_map_extension_readiness_recheck.py --require-private-readiness`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_outside_scope_authorized_source_map_extension_readiness_recheck`

Current generated check matrix: `{matrix["readiness_recheck_pass_count"]}` pass / `{matrix["readiness_recheck_fail_count"]}` fail. This phase does not read, list, parse, copy, move, rename, delete, overwrite, normalize or mutate the raw inbox.
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
        "PASS: KMFA v0.1.4 outside-scope authorized source-map extension readiness rechecked "
        f"(template_items={summary['private_authorized_extension_template_item_count']}, "
        f"valid_extensions={summary['valid_authorized_extension_record_count']}, "
        f"decision={summary['decision']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
