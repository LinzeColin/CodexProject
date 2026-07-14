#!/usr/bin/env python3
"""Record delegated conservative decisions for outside-scope KMFA source-map extension.

This phase consumes ignored private runtime evidence only. It records that the
owner delegated Codex to decide, but because exact hash/ref candidate evidence
is not sufficient for authoritative source-map extension, all 72 outside-scope
items are conservatively kept pending. It does not mutate the original private
template, read the raw inbox, apply source-map records, compare values,
reconcile values, upload, reinstall, or execute business steps.
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
PHASE_ID = "V014_OUTSIDE_SCOPE_AUTHORIZED_SOURCE_MAP_EXTENSION_DELEGATED_KEEP_PENDING_DECISION"
TASK_ID = (
    "KMFA-V014-OUTSIDE-SCOPE-AUTHORIZED-SOURCE-MAP-EXTENSION-"
    "DELEGATED-KEEP-PENDING-DECISION-20260706"
)
ACCEPTANCE_ID = "ACC-V014-OUTSIDE-SCOPE-AUTHORIZED-SOURCE-MAP-EXTENSION-DELEGATED-KEEP-PENDING-DECISION"
VERSION = "0.1.4-outside-scope-authorized-source-map-extension-delegated-keep-pending-decision"
STATUS = "completed_validated_local_only_outside_scope_authorized_extension_delegated_keep_pending_no_go"
DECISION = "NO_GO"
DIAGNOSTIC_CONCLUSION = "delegated_codex_keep_pending_decision_recorded_no_source_map_authorization"
AUTHORITY_BASIS = "owner_delegated_codex_conservative_default_decision_current_thread"
NEXT_REQUIRED_INPUT = "strong_authorized_source_map_extension_evidence_before_source_map_application_or_keep_no_go"
NEXT_RECOMMENDED_PHASE = "V014_OUTSIDE_SCOPE_AUTHORIZED_SOURCE_MAP_EXTENSION_DELEGATED_DECISION_READINESS_RECHECK"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "outside_scope_authorized_source_map_extension_delegated_keep_pending_decision_summary.json"
MANIFEST_PATH = MACHINE_DIR / "outside_scope_authorized_source_map_extension_delegated_keep_pending_decision_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "outside_scope_authorized_source_map_extension_delegated_keep_pending_decision_go_no_go_report.json"
MATRIX_PATH = MACHINE_DIR / "outside_scope_authorized_source_map_extension_delegated_keep_pending_decision_matrix_public_safe.json"
REPORT_PATH = HUMAN_DIR / "outside_scope_authorized_source_map_extension_delegated_keep_pending_decision_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_outside_scope_authorized_source_map_extension_delegated_keep_pending_decision_summary.json"
)
METADATA_MANIFEST_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_outside_scope_authorized_source_map_extension_delegated_keep_pending_decision_manifest.json"
)
METADATA_GO_NO_GO_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_outside_scope_authorized_source_map_extension_delegated_keep_pending_decision_go_no_go_report.json"
)
METADATA_MATRIX_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_outside_scope_authorized_source_map_extension_delegated_keep_pending_decision_matrix_public_safe.json"
)
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"

SOURCE_TEMPLATE_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_outside_scope_authorized_source_map_extension/private_authorized_source_map_extension_template.json"
)
SOURCE_OUTSIDE_SCOPE_PRIVATE_RESULT_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_target_outside_linked_scope_resolution/private_outside_linked_scope_resolution.json"
)
SOURCE_CANDIDATE_CATALOG_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_owner_review_intake_prep/private_candidate_catalog.json"
)

PRIVATE_OUTPUT_DIR = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_outside_scope_authorized_source_map_extension_delegated_keep_pending_decision"
)
PRIVATE_DECISION_RECORD_PATH = PRIVATE_OUTPUT_DIR / "private_delegated_keep_pending_decision_record.json"
PRIVATE_DECISION_QUEUE_PATH = PRIVATE_OUTPUT_DIR / "private_delegated_keep_pending_decision_queue.jsonl"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_delegated_keep_pending_decision_diagnostic.json"

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
        "private_authorized_extension_template_read_by_this_phase": True,
        "private_outside_scope_resolution_read_by_this_phase": True,
        "private_candidate_catalog_read_by_this_phase": True,
        "private_delegated_decision_record_written_by_this_phase": True,
        "private_delegated_decision_queue_written_by_this_phase": True,
        "private_delegated_diagnostic_written_by_this_phase": True,
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
        "private_outside_scope_resolution_committed": False,
        "private_candidate_catalog_committed": False,
        "private_delegated_decision_record_committed": False,
        "private_delegated_decision_queue_committed": False,
        "private_delegated_diagnostic_committed": False,
        "private_source_map_committed": False,
        "raw_file_committed": False,
        "raw_filename_committed": False,
        "raw_file_hash_committed": False,
        "source_archive_member_label_committed": False,
        "source_schema_label_committed": False,
        "target_slot_detail_committed": False,
        "row_value_committed": False,
        "sensitive_business_content_committed": False,
        "private_fingerprint_committed": False,
        "credential_or_secret_committed": False,
    }


def _build_private_decision(
    *,
    generated_at: str,
    template: dict[str, Any],
    outside_scope_result: dict[str, Any],
    candidate_catalog: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    extension_rows = template.get("extension_rows")
    resolution_queue = outside_scope_result.get("resolution_queue")
    candidate_rows = candidate_catalog.get("candidate_catalog_records")
    if not isinstance(extension_rows, list):
        raise ValueError("private template extension_rows must be a list")
    if not isinstance(resolution_queue, list):
        raise ValueError("private outside-scope resolution_queue must be a list")
    if not isinstance(candidate_rows, list):
        raise ValueError("private candidate catalog records must be a list")

    candidate_record_refs = {row.get("record_ref_hash") for row in candidate_rows if isinstance(row, dict)}
    candidate_numeric_refs = {row.get("numeric_value_fingerprint") for row in candidate_rows if isinstance(row, dict)}
    candidate_contexts = {row.get("context_group") for row in candidate_rows if isinstance(row, dict)}
    row_contexts = {row.get("context_group") for row in extension_rows if isinstance(row, dict)}

    exact_record_ref_match_count = sum(
        1 for row in extension_rows if isinstance(row, dict) and row.get("record_ref_hash") in candidate_record_refs
    )
    exact_processed_ref_match_count = sum(
        1
        for row in extension_rows
        if isinstance(row, dict) and row.get("private_processed_ref_hash") in candidate_numeric_refs
    )
    context_overlap_row_count = sum(
        1 for row in extension_rows if isinstance(row, dict) and row.get("context_group") in candidate_contexts
    )

    decision_rows: list[dict[str, Any]] = []
    for index, row in enumerate(extension_rows, start=1):
        if not isinstance(row, dict):
            continue
        decision_rows.append(
            {
                "decision_queue_index": index,
                "source_extension_queue_index": row.get("extension_queue_index"),
                "source_resolution_queue_index": row.get("source_resolution_queue_index"),
                "owner_decision_code": "KEEP_PENDING",
                "delegated_by": "codex",
                "authority_basis": AUTHORITY_BASIS,
                "decision_basis_code": "NO_EXACT_HASH_REF_CANDIDATE_MATCH",
                "source_map_extension_application_allowed": False,
                "source_map_extension_written_by_this_phase": False,
                "raw_to_processed_value_comparison_allowed": False,
                "full_reconciliation_allowed": False,
                "owner_note": "Conservative delegated default: keep pending until stronger source-map extension evidence exists.",
            }
        )

    private_summary = {
        "private_authorized_extension_template_item_count": len(extension_rows),
        "outside_scope_resolution_queue_record_count": len(resolution_queue),
        "candidate_catalog_record_count": len(candidate_rows),
        "candidate_catalog_context_count": len(candidate_contexts),
        "extension_context_count": len(row_contexts),
        "context_overlap_row_count": context_overlap_row_count,
        "context_overlap_unique_count": len(row_contexts & candidate_contexts),
        "exact_source_record_ref_match_count": exact_record_ref_match_count,
        "exact_processed_ref_match_count": exact_processed_ref_match_count,
        "delegated_decision_record_count": len(decision_rows),
        "delegated_keep_pending_decision_count": len(decision_rows),
        "delegated_authorize_source_map_extension_count": 0,
        "delegated_owner_exclusion_count": 0,
        "valid_authorized_extension_record_count": 0,
        "source_map_extension_ready_count": 0,
        "source_map_extension_blocker_count": len(decision_rows),
        "source_map_extension_application_ready": False,
        "source_map_extension_written_by_this_phase": False,
        "full_raw_to_processed_value_comparison_complete": False,
        "processed_consistency_verified": False,
    }
    record = {
        "schema_version": "kmfa.private.v014_outside_scope_delegated_keep_pending_decision.v1",
        "classification": "private_delegated_keep_pending_decision_do_not_commit",
        "record_type": "v014_outside_scope_authorized_source_map_extension_delegated_keep_pending_decision",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "authority_basis": AUTHORITY_BASIS,
        "delegated_default_decision_applied_by_this_phase": True,
        "private_summary": private_summary,
        "decision_rows": decision_rows,
    }
    diagnostic = {
        "schema_version": "kmfa.private.v014_outside_scope_delegated_keep_pending_diagnostic.v1",
        "classification": "private_delegated_keep_pending_diagnostic_do_not_commit",
        "record_type": "v014_outside_scope_authorized_source_map_extension_delegated_keep_pending_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "authority_basis": AUTHORITY_BASIS,
        "private_summary": private_summary,
        "raw_boundary": _raw_boundary(),
    }
    return record, decision_rows, diagnostic


def _build_matrix(summary: dict[str, Any]) -> dict[str, Any]:
    checks = [
        ("template_row_count_preserved", summary["private_authorized_extension_template_item_count"] == 72, 72),
        ("delegated_decision_count_complete", summary["delegated_decision_record_count"] == 72, 72),
        ("all_delegated_decisions_keep_pending", summary["delegated_keep_pending_decision_count"] == 72, 72),
        ("exact_source_record_ref_match_absent", summary["exact_source_record_ref_match_count"] == 0, 0),
        ("exact_processed_ref_match_absent", summary["exact_processed_ref_match_count"] == 0, 0),
        ("source_map_application_not_ready", summary["source_map_extension_application_ready"] is False, False),
        ("raw_inbox_untouched", summary["raw_boundary"]["raw_inbox_mutated_by_this_phase"] is False, False),
        ("downstream_gates_closed", summary["business_execution_performed"] is False, False),
    ]
    rows = [
        {"check_code": code, "status": "PASS" if ok else "FAIL", "observed_public_safe": summary.get(code), "required": required}
        for code, ok, required in checks
    ]
    pass_count = sum(1 for row in rows if row["status"] == "PASS")
    return {
        "schema_version": "kmfa.v014_outside_scope_delegated_keep_pending_matrix_public_safe.v1",
        "record_type": "v014_outside_scope_authorized_source_map_extension_delegated_keep_pending_matrix_public_safe",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": summary["generated_at"],
        "delegated_keep_pending_decision_check_count": len(rows),
        "delegated_keep_pending_decision_check_pass_count": pass_count,
        "delegated_keep_pending_decision_check_fail_count": len(rows) - pass_count,
        "decision": DECISION,
        "checks": rows,
    }


def _write_human_artifacts(summary: dict[str, Any], matrix: dict[str, Any]) -> None:
    report = f"""# V014 Outside-Scope Delegated Keep-Pending Decision

- phase: `{PHASE_ID}`
- status: `{STATUS}`
- decision: `{DECISION}`
- delegated decision records: `{summary["delegated_decision_record_count"]}`
- delegated keep-pending decisions: `{summary["delegated_keep_pending_decision_count"]}`
- exact source-record ref matches: `{summary["exact_source_record_ref_match_count"]}`
- exact processed-ref matches: `{summary["exact_processed_ref_match_count"]}`
- source-map application ready: `false`
- source-map extension written by this phase: `false`

Codex recorded a conservative delegated decision because the available private evidence did not prove exact authorized source-map extension. This phase records a private response only; it does not mutate the original template or apply source-map records.
"""
    go_no_go_record = f"""# Go / No-Go

- decision: `{DECISION}`
- reason: delegated conservative decisions keep all outside-scope items pending because exact authoritative source-map evidence is not proven.
- next required input: `{NEXT_REQUIRED_INPUT}`
- source-map application ready: `false`
- full comparison complete: `false`
- GitHub upload performed: `false`
- app reinstall performed: `false`
"""
    risk_register = """# Risk Register

- R1: Delegated keep-pending decisions could be mistaken for source-map authorization.
- R2: Context overlap is not exact source-map evidence and cannot unlock full comparison.
- R3: Downstream release, upload, reinstall and business execution remain blocked.
"""
    rollback_plan = """# Rollback Plan

No raw inbox, original private template, source-map, materialization, reconciliation or active authorization file was mutated. To roll back, remove this phase's public artifacts, metadata copies, private response output directory, tool, validator, focused test and governance entries.
"""
    test_results = f"""# Test Results

Recorded validation commands for this phase:

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_outside_scope_authorized_source_map_extension_delegated_keep_pending_decision.py KMFA/tools/check_v014_outside_scope_authorized_source_map_extension_delegated_keep_pending_decision.py KMFA/tests/test_v014_outside_scope_authorized_source_map_extension_delegated_keep_pending_decision.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_outside_scope_authorized_source_map_extension_delegated_keep_pending_decision.py --generated-at 2026-07-06T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_outside_scope_authorized_source_map_extension_delegated_keep_pending_decision.py --require-private-decision`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_outside_scope_authorized_source_map_extension_delegated_keep_pending_decision`

Current generated check matrix: `{matrix["delegated_keep_pending_decision_check_pass_count"]}` pass / `{matrix["delegated_keep_pending_decision_check_fail_count"]}` fail. This phase does not read, list, parse, copy, move, rename, delete, overwrite, normalize or mutate the raw inbox.
"""
    for path, text in (
        (REPORT_PATH, report),
        (GO_NO_GO_RECORD_PATH, go_no_go_record),
        (RISK_REGISTER_PATH, risk_register),
        (ROLLBACK_PATH, rollback_plan),
        (TEST_RESULTS_PATH, test_results),
    ):
        _write_text(path, text)


def _append_development_event(manifest: dict[str, Any]) -> None:
    event_id = "DEV-KMFA-20260706-V014-OUTSIDE-SCOPE-DELEGATED-KEEP-PENDING-DECISION"
    summary = manifest["summary"]
    event = {
        "event_id": event_id,
        "event_time": manifest["generated_at"],
        "event_type": "development",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "iteration_id": "ITER-20260706-KMFA-V014-OUTSIDE-SCOPE-DELEGATED-KEEP-PENDING-DECISION",
        "fact_level": "EXTRACTED",
        "status": STATUS,
        "go_no_go": DECISION,
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "delegated_decision_record_count": summary["delegated_decision_record_count"],
        "delegated_keep_pending_decision_count": summary["delegated_keep_pending_decision_count"],
        "exact_source_record_ref_match_count": summary["exact_source_record_ref_match_count"],
        "exact_processed_ref_match_count": summary["exact_processed_ref_match_count"],
        "source_map_extension_application_ready": False,
        "source_map_extension_written_by_this_phase": False,
        "raw_to_processed_value_comparison_performed": False,
        "processed_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "summary": "Recorded delegated conservative keep-pending decisions for 72 outside-scope source-map extension items.",
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
            "KMFA/tests/test_v014_outside_scope_authorized_source_map_extension_delegated_keep_pending_decision.py",
            "KMFA/tools/check_v014_outside_scope_authorized_source_map_extension_delegated_keep_pending_decision.py",
            "KMFA/tools/v014_outside_scope_authorized_source_map_extension_delegated_keep_pending_decision.py",
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
    template = _read_json(SOURCE_TEMPLATE_PATH)
    outside_scope_result = _read_json(SOURCE_OUTSIDE_SCOPE_PRIVATE_RESULT_PATH)
    candidate_catalog = _read_json(SOURCE_CANDIDATE_CATALOG_PATH)
    private_record, decision_rows, diagnostic = _build_private_decision(
        generated_at=timestamp,
        template=template,
        outside_scope_result=outside_scope_result,
        candidate_catalog=candidate_catalog,
    )

    private_summary = diagnostic["private_summary"]
    summary = {
        "schema_version": "kmfa.v014_outside_scope_delegated_keep_pending_decision_summary.v1",
        "record_type": "v014_outside_scope_authorized_source_map_extension_delegated_keep_pending_decision_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "authority_basis": AUTHORITY_BASIS,
        "delegated_default_decision_applied_by_this_phase": True,
        **private_summary,
        "owner_delegated_decision_input_present": True,
        "private_decision_record_written": True,
        "private_decision_record_gitignored": _git_check_ignored(PRIVATE_DECISION_RECORD_PATH),
        "private_decision_queue_written": True,
        "private_decision_queue_gitignored": _git_check_ignored(PRIVATE_DECISION_QUEUE_PATH),
        "private_diagnostic_written": True,
        "private_diagnostic_gitignored": _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH),
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "full_reconciliation_allowed": False,
        "lineage_full_check_complete": False,
        "formal_report_allowed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "next_required_input": NEXT_REQUIRED_INPUT,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
        "raw_boundary": _raw_boundary(),
        "public_safety": _public_safety(),
    }
    matrix = _build_matrix(summary)
    go_no_go = {
        "schema_version": "kmfa.v014_outside_scope_delegated_keep_pending_decision_go_no_go.v1",
        "record_type": "v014_outside_scope_authorized_source_map_extension_delegated_keep_pending_decision_go_no_go",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "authority_basis": AUTHORITY_BASIS,
        "delegated_decision_record_count": summary["delegated_decision_record_count"],
        "delegated_keep_pending_decision_count": summary["delegated_keep_pending_decision_count"],
        "valid_authorized_extension_record_count": summary["valid_authorized_extension_record_count"],
        "source_map_extension_application_ready": False,
        "source_map_extension_written_by_this_phase": False,
        "full_raw_to_processed_value_comparison_complete": False,
        "processed_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "next_required_input": NEXT_REQUIRED_INPUT,
    }
    manifest = {
        "schema_version": "kmfa.v014_outside_scope_delegated_keep_pending_decision_manifest.v1",
        "record_type": "v014_outside_scope_authorized_source_map_extension_delegated_keep_pending_decision_manifest",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "source_artifacts": [
            "private:outside_scope_authorized_extension_template",
            "private:outside_scope_resolution_result",
            "private:candidate_catalog",
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
            "private:delegated_keep_pending_decision_record",
            "private:delegated_keep_pending_decision_queue",
            "private:delegated_keep_pending_decision_diagnostic",
        ],
        "validator": (
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 "
            "KMFA/tools/check_v014_outside_scope_authorized_source_map_extension_delegated_keep_pending_decision.py "
            "--require-private-decision"
        ),
        "summary": summary,
        "go_no_go_report": go_no_go,
        "matrix": matrix,
        "git": {
            "head": _git_output(["rev-parse", "HEAD"]),
            "branch": _git_output(["branch", "--show-current"]),
            "status_short_branch": _git_output(["status", "--short", "--branch"]),
        },
    }

    _write_json(PRIVATE_DECISION_RECORD_PATH, private_record)
    _write_jsonl(PRIVATE_DECISION_QUEUE_PATH, decision_rows)
    _write_json(PRIVATE_DIAGNOSTIC_PATH, diagnostic)
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
    _write_human_artifacts(summary, matrix)
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
        "PASS: KMFA v0.1.4 outside-scope delegated keep-pending decision recorded "
        f"(decision_records={summary['delegated_decision_record_count']}, "
        f"keep_pending={summary['delegated_keep_pending_decision_count']}, "
        f"decision={summary['decision']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
