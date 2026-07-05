#!/usr/bin/env python3
"""Generate KMFA v0.1.4 S16-P2 project status lifecycle evidence.

This phase locks the public-safe production/project lifecycle baseline for
v0.1.4. It may create a local ignored private diagnostic for read-only raw
alignment, but it does not commit raw filenames, headers, values, hashes, or
files. It does not enter S16-P3, perform Stage 16 review, release a formal
report, replace site/safety/technical signatures, execute invoices or
collections, operate bank accounts, execute business actions, or upload to
GitHub.
"""

from __future__ import annotations

import json
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.check_v014_s16_p1_subcontract_procurement import (  # noqa: E402
    validate_v014_s16_p1_subcontract_procurement,
)
from KMFA.tools.project_status_lifecycle import (  # noqa: E402
    REQUIRED_EXCEPTION_TYPES,
    REQUIRED_HANDOFF_GUARDS,
    REQUIRED_LIFECYCLE_STATES,
    REQUIRED_SOURCE_LANES,
    build_default_project_status_lifecycle,
    validate_project_status_lifecycle_artifacts,
)


TASK_ID = "KMFA-V014-S16-P2-PROJECT-STATUS-LIFECYCLE-20260705"
ACCEPTANCE_ID = "ACC-V014-S16-P2-PROJECT-STATUS-LIFECYCLE"
SCHEMA_VERSION = "kmfa.v014_s16_p2_project_status_lifecycle.v1"
PHASE_SCOPE = "v014_s16_p2_project_status_lifecycle_only"
BASELINE_LOCK_VERSION = "LOCK-KMFA-V014-S16P2-PROJECT-STATUS-LIFECYCLE-PUBLIC-SAFE-001"
FORMULA_ID = "FORM-KMFA-V014-S16P2-PROJECT-STATUS-LIFECYCLE-001"
MAPPING_VERSION = "MAP-KMFA-V014-S16P2-PROJECT-STATUS-LIFECYCLE-v1"

OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_S16_P2_PROJECT_STATUS_LIFECYCLE")
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
MANIFEST_PATH = MACHINE_DIR / "project_status_lifecycle_manifest.json"
SOURCE_LANE_LOCK_PATH = MACHINE_DIR / "source_lane_lock.jsonl"
LIFECYCLE_LOCK_PATH = MACHINE_DIR / "lifecycle_record_lock.jsonl"
EXCEPTION_LOCK_PATH = MACHINE_DIR / "exception_item_lock.jsonl"
HANDOFF_GUARD_LOCK_PATH = MACHINE_DIR / "handoff_guard_lock.jsonl"
REPORT_PATH = HUMAN_DIR / "project_status_lifecycle_report.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

V14_TASKPACK_PATH = Path("KMFA/taskpack/v1_4/taskpack/01_KMFA_Codex_TaskPack_v1_4_public_safe.md")
V14_ROADMAP_PATH = Path("KMFA/taskpack/v1_4/roadmap/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_4.md")
PRIVATE_RUNTIME_REPORT_REF = (
    "KMFA/.codex_private_runtime/v014_s16_p2_project_status_lifecycle/raw_alignment_report.json"
)
PRIVATE_RUNTIME_REPORT_PATH = Path(PRIVATE_RUNTIME_REPORT_REF)
NEXT_PHASE = "S16-P3"
NEXT_REQUIRED_STEP = (
    "Proceed to v0.1.4 S16-P3 customer business analysis as a separate run only after user instruction. "
    "Do not perform Stage 16 overall review, GitHub upload, formal report release, site construction, safety "
    "signature, technical signature, invoice issuance, collection action, payment execution, bank operation, "
    "legal action, or business execution in the S16-P2 run."
)
RAW_ACTION_KEYS = (
    "raw_inbox_modified_by_this_phase",
    "raw_inbox_deleted_by_this_phase",
    "raw_inbox_moved_by_this_phase",
    "raw_inbox_renamed_by_this_phase",
    "raw_inbox_overwritten_by_this_phase",
    "raw_inbox_written_by_this_phase",
    "raw_inbox_mutated_by_this_phase",
    "raw_business_values_committed",
    "raw_file_names_committed",
    "raw_hashes_committed",
    "field_header_plaintext_committed",
)


def git_output(args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def validate_s16_p1_dependency() -> dict[str, Any]:
    result = validate_v014_s16_p1_subcontract_procurement()
    if result.get("stage_id") != "S16" or result.get("phase_id") != "S16-P1":
        raise RuntimeError("S16-P2 requires validated v0.1.4 S16-P1 evidence")
    if result.get("next_phase") != "S16-P2":
        raise RuntimeError("S16-P1 must route to S16-P2")
    if result.get("stage16_phase_progress", {}).get("s16_p2_performed") is not False:
        raise RuntimeError("S16-P1 dependency must not already include S16-P2")
    if result.get("github_upload", {}).get("github_upload_performed") is not False:
        raise RuntimeError("v1.4 GitHub upload must remain deferred")
    return result


def validate_legacy_s16_p2_artifacts() -> tuple[
    dict[str, Any],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    artifacts = build_default_project_status_lifecycle(generated_at="2026-07-05T12:20:00+10:00")
    validate_project_status_lifecycle_artifacts(*artifacts)
    return artifacts


def load_v14_taskpack_baseline() -> dict[str, Any]:
    taskpack_text = V14_TASKPACK_PATH.read_text(encoding="utf-8")
    roadmap_text = V14_ROADMAP_PATH.read_text(encoding="utf-8")

    for token in (
        "项目状态生命周期",
        "接入生产项目状态、开工、完工、结算、开票、回款",
        "生成项目生命周期与异常事项",
        "不替代现场施工、安全、技术签字",
    ):
        if token not in roadmap_text:
            raise RuntimeError(f"v1.4 roadmap missing S16-P2 required marker {token}")
    for token in ("项目交付/生产状态线", "生命周期状态", "完工未结算", "结算未开票", "开票未回款"):
        if token not in taskpack_text:
            raise RuntimeError(f"v1.4 taskpack missing S16-P2 required marker {token}")

    return {
        "taskpack_read": True,
        "roadmap_read": True,
        "roadmap_includes_s16_p2_requirements": True,
        "taskpack_includes_project_delivery_status_line": True,
        "source_refs": {
            "taskpack": V14_TASKPACK_PATH.as_posix(),
            "roadmap": V14_ROADMAP_PATH.as_posix(),
        },
    }


def _raw_root() -> Path:
    return Path.home() / "Downloads" / "KMFA_MetaData"


def _xlsx_private_probe(path: Path) -> dict[str, Any]:
    try:
        with zipfile.ZipFile(path) as workbook:
            names = workbook.namelist()
    except (OSError, zipfile.BadZipFile) as exc:
        return {"read_status": "unreadable_private_workbook", "error": str(exc)}
    worksheet_count = len([name for name in names if name.startswith("xl/worksheets/") and name.endswith(".xml")])
    return {
        "read_status": "private_workbook_container_readonly_probe_ok",
        "suffix": path.suffix.lower(),
        "size_bytes": path.stat().st_size,
        "worksheet_xml_count": worksheet_count,
        "zip_member_count": len(names),
        "note": "Private diagnostic only; do not copy this payload into public evidence.",
    }


def create_raw_private_alignment_report(generated_at: str) -> dict[str, Any]:
    raw_root = _raw_root()
    files: list[Path] = []
    if raw_root.exists():
        files = sorted(path for path in raw_root.iterdir() if path.is_file())
    candidates = [
        path
        for path in files
        if path.suffix.lower() in {".xlsx", ".xlsm"}
        and "项目" in path.name
        and "状态" in path.name
    ]
    private_report = {
        "schema_version": "kmfa.private.v014_s16_p2_raw_alignment_report.v1",
        "generated_at": generated_at,
        "raw_root_exists": raw_root.exists(),
        "raw_file_count": len(files),
        "production_status_candidate_count": len(candidates),
        "candidate_private_diagnostics": [
            {
                "filename": path.name,
                "private_path": str(path),
                "probe": _xlsx_private_probe(path),
            }
            for path in candidates[:3]
        ],
        "mutation_performed": False,
        "public_commit_allowed": False,
        "public_copy_instruction": "Do not commit this file or copy raw filenames, headers, values, or raw hashes into public evidence.",
    }
    write_json(PRIVATE_RUNTIME_REPORT_PATH, private_report)

    result: dict[str, Any] = {
        "raw_private_alignment_attempted_by_this_phase": True,
        "raw_inbox_exists_observed": raw_root.exists(),
        "raw_inbox_file_count_observed": len(files),
        "production_status_private_candidate_count": len(candidates),
        "private_runtime_report_ref": PRIVATE_RUNTIME_REPORT_REF,
        "raw_inbox_readonly_contract_preserved": True,
        "private_runtime_report_committed": False,
        "alignment_status": "private_candidate_observed" if candidates else "no_private_candidate_observed_or_raw_inbox_unavailable",
    }
    result.update({key: False for key in RAW_ACTION_KEYS})
    return result


def _public_repo_safety() -> dict[str, bool]:
    return {
        "protected_source_payload_committed": False,
        "compressed_raw_package_committed": False,
        "excel_workbook_committed": False,
        "wps_native_file_committed": False,
        "raw_or_private_csv_committed": False,
        "pdf_document_committed": False,
        "private_csv_committed": False,
        "local_database_committed": False,
        "auth_material_committed": False,
        "connector_auth_material_committed": False,
        "field_plaintext_committed": False,
        "source_header_plaintext_committed": False,
        "raw_file_names_committed": False,
        "raw_file_hashes_committed": False,
        "tab_labels_committed": False,
        "source_record_payload_committed": False,
        "normalized_source_values_committed": False,
        "business_amount_values_committed": False,
        "public_numeric_values_committed": False,
        "project_or_customer_plaintext_committed": False,
        "business_decision_basis_committed": False,
        "site_construction_payload_committed": False,
        "safety_signature_payload_committed": False,
        "technical_signature_payload_committed": False,
    }


def _quality_gate() -> dict[str, Any]:
    return {
        "project_status_lifecycle_signal_allowed": True,
        "owner_or_authorized_delegate_review_required": True,
        "lifecycle_exception_review_required": True,
        "handoff_guard_review_required": True,
        "formal_report_allowed": False,
        "complete_trusted_report_display_allowed": False,
        "business_decision_basis_allowed": False,
        "report_grade_bypass_allowed": False,
        "quality_grade_bypass_allowed": False,
        "raw_layer_write_allowed": False,
        "site_construction_instruction_allowed": False,
        "site_operation_allowed": False,
        "safety_signature_allowed": False,
        "technical_acceptance_signature_allowed": False,
        "technical_signature_allowed": False,
        "settlement_confirmation_allowed": False,
        "invoice_issuance_allowed": False,
        "collection_action_allowed": False,
        "payment_execution_allowed": False,
        "bank_operation_allowed": False,
        "s16_p3_allowed": False,
        "stage16_review_allowed": False,
        "github_upload_allowed": False,
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "release_permission": "blocked",
        "release_block_reason": "s16_p2_project_status_lifecycle_review_queue_only_pending_manual_reconciliation",
    }


def _phase_boundaries() -> dict[str, bool]:
    return {
        "s16_p1_dependency_reused": True,
        "legacy_s16_p2_public_safe_baseline_reused": True,
        "s16_p1_subcontract_procurement_scope_included": False,
        "s16_p2_project_status_scope_included": True,
        "s16_p2_scope_included": True,
        "s16_p3_customer_analysis_scope_included": False,
        "s16_p3_scope_included": False,
        "stage16_review_scope_included": False,
        "github_upload_scope_included": False,
        "lineage_full_check_scope_included": False,
        "protected_source_matching_scope_included": False,
        "formal_report_runtime_scope_included": False,
        "live_ui_runtime_scope_included": False,
        "external_connector_scope_included": False,
        "app_reinstall_scope_included": False,
        "site_construction_scope_included": False,
        "site_operation_scope_included": False,
        "safety_signature_scope_included": False,
        "technical_signature_scope_included": False,
        "invoice_issuance_scope_included": False,
        "collection_action_scope_included": False,
        "payment_execution_scope_included": False,
        "bank_operation_scope_included": False,
        "legal_action_scope_included": False,
        "business_execution_scope_included": False,
    }


def _source_lane_lock_rows(source_lanes: list[dict[str, Any]], generated_at: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, lane in enumerate(source_lanes, start=1):
        rows.append(
            {
                "schema_version": "kmfa.v014_s16_p2.source_lane_lock.v1",
                "record_type": "v014_s16_p2_source_lane_lock",
                "project_id": "KMFA",
                "stage_id": "S16",
                "phase_id": "S16-P2",
                "lock_row_id": f"V014-S16P2-LANE-{index:03d}",
                "generated_at": generated_at,
                "baseline_lock_version": BASELINE_LOCK_VERSION,
                "legacy_lane_id": str(lane["lane_id"]),
                "legacy_stage_phase": str(lane["stage_phase"]),
                "source_count": int(lane["source_count"]),
                "field_mapping_count": int(lane["field_mapping_count"]),
                "all_sources_readonly": lane.get("all_sources_readonly") is True,
                "data_status": "structure_available_values_hidden",
                "manual_review_required": True,
                "raw_business_values_allowed": False,
                "public_numeric_values_allowed": False,
                "field_plaintext_allowed": False,
                "formal_report_allowed": False,
                "business_decision_basis_allowed": False,
                "site_operation_allowed": False,
                "signature_authority_allowed": False,
                "invoice_issuance_allowed": False,
                "collection_action_allowed": False,
            }
        )
    return rows


def _lifecycle_lock_rows(lifecycle_records: list[dict[str, Any]], generated_at: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, record in enumerate(lifecycle_records, start=1):
        rows.append(
            {
                "schema_version": "kmfa.v014_s16_p2.lifecycle_record_lock.v1",
                "record_type": "v014_s16_p2_lifecycle_record_lock",
                "project_id": "KMFA",
                "stage_id": "S16",
                "phase_id": "S16-P2",
                "lock_row_id": f"V014-S16P2-LIFE-{index:03d}",
                "generated_at": generated_at,
                "legacy_lifecycle_record_ref": str(record["lifecycle_record_id"]),
                "lifecycle_state": str(record["lifecycle_state"]),
                "manual_review_required": record.get("manual_review_required") is True,
                "raw_business_values_allowed": False,
                "public_numeric_values_allowed": False,
                "field_plaintext_allowed": False,
                "formal_report_allowed": False,
                "business_decision_basis_allowed": False,
                "site_construction_instruction_allowed": False,
                "safety_signature_allowed": False,
                "technical_acceptance_signature_allowed": False,
                "invoice_issuance_allowed": False,
                "collection_action_allowed": False,
            }
        )
    return rows


def _exception_lock_rows(exception_items: list[dict[str, Any]], generated_at: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, item in enumerate(exception_items, start=1):
        rows.append(
            {
                "schema_version": "kmfa.v014_s16_p2.exception_item_lock.v1",
                "record_type": "v014_s16_p2_exception_item_lock",
                "project_id": "KMFA",
                "stage_id": "S16",
                "phase_id": "S16-P2",
                "lock_row_id": f"V014-S16P2-EXC-{index:03d}",
                "generated_at": generated_at,
                "legacy_exception_item_ref": str(item["exception_item_id"]),
                "exception_type": str(item["exception_type"]),
                "candidate_status": str(item["candidate_status"]),
                "manual_review_required": item.get("manual_review_required") is True,
                "auto_close_allowed": False,
                "raw_business_values_allowed": False,
                "public_numeric_values_allowed": False,
                "field_plaintext_allowed": False,
                "formal_report_allowed": False,
                "business_decision_basis_allowed": False,
                "site_operation_allowed": False,
                "invoice_issuance_allowed": False,
                "collection_action_allowed": False,
            }
        )
    return rows


def _handoff_guard_lock_rows(handoff_guards: list[dict[str, Any]], generated_at: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, guard in enumerate(handoff_guards, start=1):
        rows.append(
            {
                "schema_version": "kmfa.v014_s16_p2.handoff_guard_lock.v1",
                "record_type": "v014_s16_p2_handoff_guard_lock",
                "project_id": "KMFA",
                "stage_id": "S16",
                "phase_id": "S16-P2",
                "lock_row_id": f"V014-S16P2-GUARD-{index:03d}",
                "generated_at": generated_at,
                "legacy_guard_ref": str(guard["guard_id"]),
                "blocked_capability": str(guard["blocked_capability"]),
                "required_actor": str(guard["required_actor"]),
                "delegated_to_system": False,
                "signature_authority_allowed": False,
                "operation_execution_allowed": False,
                "site_operation_allowed": False,
                "formal_report_allowed": False,
                "business_decision_basis_allowed": False,
                "raw_business_values_allowed": False,
            }
        )
    return rows


def build_artifacts(
    generated_at: str | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    generated_at = generated_at or datetime.now().isoformat(timespec="seconds")
    s16_p1 = validate_s16_p1_dependency()
    legacy_manifest, source_lanes, lifecycle_records, exception_items, handoff_guards = validate_legacy_s16_p2_artifacts()
    baseline = load_v14_taskpack_baseline()
    raw_alignment = create_raw_private_alignment_report(generated_at)
    legacy_summary = dict(legacy_manifest["summary"])

    summary = {
        "source_lane_count": legacy_summary["source_lane_count"],
        "lifecycle_record_count": legacy_summary["lifecycle_record_count"],
        "exception_item_count": legacy_summary["exception_item_count"],
        "handoff_guard_count": legacy_summary["handoff_guard_count"],
        "completed_not_settled_count": legacy_summary["completed_not_settled_count"],
        "settled_not_invoiced_count": legacy_summary["settled_not_invoiced_count"],
        "invoiced_not_collected_count": legacy_summary["invoiced_not_collected_count"],
        "pending_reconciliation_count": legacy_summary["pending_reconciliation_count"],
        "report_grade_visible": legacy_summary["report_grade_visible"],
        "site_operation_count": 0,
        "signature_operation_count": 0,
        "invoice_issuance_count": 0,
        "collection_action_count": 0,
        "formal_report_count": 0,
        "business_decision_basis_count": 0,
    }
    manifest: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "v014_s16_p2_project_status_lifecycle_manifest",
        "project_id": "KMFA",
        "version": "0.1.4",
        "stage_id": "S16",
        "phase_id": "S16-P2",
        "phase_scope": PHASE_SCOPE,
        "task_id": TASK_ID,
        "acceptance_ids": [ACCEPTANCE_ID],
        "completed_task_ids": ["S16P2T01", "S16P2T02", "S16P2T03"],
        "status": "completed_validated_local_only_no_go_upload_deferred_project_status_lifecycle_locked",
        "generated_at": generated_at,
        "branch": git_output(["branch", "--show-current"]),
        "git_head": git_output(["rev-parse", "HEAD"]),
        "baseline_lock_version": BASELINE_LOCK_VERSION,
        "formula_id": FORMULA_ID,
        "mapping_version": MAPPING_VERSION,
        "s16_p1_dependency_validated": True,
        "historical_s16_p2_public_safe_baseline_validated": True,
        "v14_taskpack_baseline": baseline,
        "required_source_lanes": list(REQUIRED_SOURCE_LANES),
        "required_lifecycle_states": list(REQUIRED_LIFECYCLE_STATES),
        "required_exception_types": list(REQUIRED_EXCEPTION_TYPES),
        "required_handoff_guards": list(REQUIRED_HANDOFF_GUARDS),
        "upstream_refs": {
            "v014_s16_p1_manifest": (
                "KMFA/stage_artifacts/V014_S16_P1_SUBCONTRACT_PROCUREMENT/machine/subcontract_procurement_manifest.json"
            ),
            "legacy_s16_p2_manifest": "KMFA/metadata/reports/project_status_lifecycle_manifest.json",
            "legacy_s16_p2_stage_manifest": "KMFA/stage_artifacts/S16_P2_project_status_lifecycle/machine/s16_p2_manifest.json",
        },
        "legacy_baseline_summary": {
            "stage_phase": legacy_manifest.get("stage_phase"),
            "lifecycle_version": legacy_manifest.get("lifecycle_version"),
            "formula_version": legacy_manifest.get("formula_version"),
            "mapping_version": legacy_manifest.get("mapping_version"),
            "source_lane_count": legacy_summary["source_lane_count"],
            "lifecycle_record_count": legacy_summary["lifecycle_record_count"],
            "exception_item_count": legacy_summary["exception_item_count"],
            "handoff_guard_count": legacy_summary["handoff_guard_count"],
            "pending_reconciliation_count": legacy_summary["pending_reconciliation_count"],
            "report_grade_visible": legacy_summary["report_grade_visible"],
            "formal_report_allowed": legacy_manifest.get("quality_gate", {}).get("formal_report_allowed"),
            "site_operation_allowed": legacy_manifest.get("quality_gate", {}).get("site_operation_allowed"),
            "technical_signature_allowed": legacy_manifest.get("quality_gate", {}).get("technical_signature_allowed"),
            "collection_action_allowed": legacy_manifest.get("quality_gate", {}).get("collection_action_allowed"),
        },
        "stage16_phase_progress": {
            "completed_phase_count": 2,
            "total_phase_count": 3,
            "derived_percent_bps": 6667,
            "derived_percent_label": "66.67%",
            "s16_p1_performed": True,
            "s16_p2_performed": True,
            "s16_p3_performed": False,
            "stage16_review_performed": False,
        },
        "project_status_lifecycle_summary": summary,
        "artifact_refs": {
            "manifest": MANIFEST_PATH.as_posix(),
            "source_lane_lock": SOURCE_LANE_LOCK_PATH.as_posix(),
            "lifecycle_record_lock": LIFECYCLE_LOCK_PATH.as_posix(),
            "exception_item_lock": EXCEPTION_LOCK_PATH.as_posix(),
            "handoff_guard_lock": HANDOFF_GUARD_LOCK_PATH.as_posix(),
            "report": REPORT_PATH.as_posix(),
            "test_results": TEST_RESULTS_PATH.as_posix(),
            "risk_register": RISK_REGISTER_PATH.as_posix(),
            "rollback_plan": ROLLBACK_PATH.as_posix(),
        },
        "quality_gate": _quality_gate(),
        "phase_boundaries": _phase_boundaries(),
        "raw_private_alignment": raw_alignment,
        "public_repo_safety": _public_repo_safety(),
        "github_upload": {
            "github_upload_performed": False,
            "github_upload_ready_next_gate": False,
            "github_upload_deferred_until_v014_stage1_18_complete": True,
            "github_upload_status": "not_uploaded_deferred_until_v014_stage1_18_complete",
        },
        "hard_blocks": [
            "formal_report_release_blocked",
            "business_decision_basis_blocked",
            "site_construction_blocked",
            "safety_signature_blocked",
            "technical_signature_blocked",
            "invoice_issuance_blocked",
            "collection_action_blocked",
            "payment_execution_blocked",
            "bank_operation_blocked",
            "s16_p3_not_performed",
            "stage16_review_not_performed",
            "github_upload_deferred_until_v014_stage1_18_complete",
            "business_execution_blocked",
        ],
        "s16_p1_dependency_status": {
            "task_id": s16_p1.get("task_id"),
            "status": s16_p1.get("status"),
            "next_phase": s16_p1.get("next_phase"),
            "github_upload_status": s16_p1.get("github_upload", {}).get("github_upload_status"),
        },
        "next_phase": NEXT_PHASE,
        "next_required_step": NEXT_REQUIRED_STEP,
    }
    return (
        manifest,
        _source_lane_lock_rows(source_lanes, generated_at),
        _lifecycle_lock_rows(lifecycle_records, generated_at),
        _exception_lock_rows(exception_items, generated_at),
        _handoff_guard_lock_rows(handoff_guards, generated_at),
    )


def _report_text(manifest: dict[str, Any]) -> str:
    summary = manifest["project_status_lifecycle_summary"]
    return (
        "# KMFA v0.1.4 S16-P2 project status lifecycle lock\n\n"
        f"- Task: {manifest['task_id']}\n"
        "- Status: completed, validated locally, upload deferred.\n"
        f"- Source lanes locked: {summary['source_lane_count']}\n"
        f"- Lifecycle records locked: {summary['lifecycle_record_count']}\n"
        f"- Exception items locked: {summary['exception_item_count']}\n"
        f"- Handoff guards locked: {summary['handoff_guard_count']}\n"
        f"- Pending reconciliation count: {summary['pending_reconciliation_count']}\n"
        "- Report grade remains D; output is review queue evidence only.\n"
        "- Site construction, safety signature, technical signature, invoice issuance, collection action, "
        "business execution, S16-P3, Stage 16 review, and GitHub upload are blocked in this phase.\n"
    )


def _test_results_text(manifest: dict[str, Any]) -> str:
    return (
        "# KMFA v0.1.4 S16-P2 test results\n\n"
        f"- Generated task: {manifest['task_id']}\n"
        "- Required checks: generator, validator, legacy S16-P2 validator, S16-P1 dependency validator, unit test, "
        "governance validator, public evidence scan, raw/private suffix scan, and local commit.\n"
        "- Final command evidence is recorded by the S16-P2 run after verification.\n"
    )


def _risk_register_text() -> str:
    return (
        "# KMFA v0.1.4 S16-P2 risk register\n\n"
        "- R1: Lifecycle states can be mistaken for site execution or signature authority. Mitigation: all site, "
        "safety and technical execution gates remain false and validator enforces the block.\n"
        "- R2: Exception items require owner or authorized delegate review. Mitigation: report grade D and "
        "business decision basis remain blocked.\n"
        "- R3: Raw production-status diagnostics are local/private only. Mitigation: public evidence stores only "
        "aggregate counts and an ignored private-runtime report reference.\n"
        "- R4: Historical Stage 16 artifacts can imply later-phase completion. Mitigation: this v0.1.4 manifest "
        "records only S16-P2 and explicitly blocks S16-P3, Stage 16 review, and upload.\n"
    )


def _rollback_text() -> str:
    return (
        "# KMFA v0.1.4 S16-P2 rollback plan\n\n"
        "Rollback is local-only: remove the V014_S16_P2_PROJECT_STATUS_LIFECYCLE artifact directory, remove the "
        "v014 S16-P2 tool, validator, and test file, then revert governance entries from this phase before any "
        "future upload gate. The ignored private runtime report can be deleted locally if desired; no raw/private "
        "inbox file is modified by this phase.\n"
    )


def generate(generated_at: str | None = None) -> dict[str, Any]:
    manifest, source_lane_locks, lifecycle_locks, exception_locks, handoff_guard_locks = build_artifacts(generated_at)
    write_json(MANIFEST_PATH, manifest)
    write_jsonl(SOURCE_LANE_LOCK_PATH, source_lane_locks)
    write_jsonl(LIFECYCLE_LOCK_PATH, lifecycle_locks)
    write_jsonl(EXCEPTION_LOCK_PATH, exception_locks)
    write_jsonl(HANDOFF_GUARD_LOCK_PATH, handoff_guard_locks)
    write_text(REPORT_PATH, _report_text(manifest))
    write_text(TEST_RESULTS_PATH, _test_results_text(manifest))
    write_text(RISK_REGISTER_PATH, _risk_register_text())
    write_text(ROLLBACK_PATH, _rollback_text())
    return manifest


def main() -> int:
    manifest = generate()
    summary = manifest["project_status_lifecycle_summary"]
    print(
        "PASS: KMFA v0.1.4 S16-P2 project status lifecycle generated "
        f"(source_lanes={summary['source_lane_count']}, lifecycle_records={summary['lifecycle_record_count']}, "
        f"exception_items={summary['exception_item_count']}, handoff_guards={summary['handoff_guard_count']}, "
        f"report_grade={summary['report_grade_visible']}, site_operation={summary['site_operation_count']}, "
        f"signature_operation={summary['signature_operation_count']}, next_phase={manifest['next_phase']}, "
        f"github_upload={manifest['github_upload']['github_upload_performed']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
