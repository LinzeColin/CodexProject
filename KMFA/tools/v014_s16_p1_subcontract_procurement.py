#!/usr/bin/env python3
"""Generate KMFA v0.1.4 S16-P1 subcontract procurement evidence.

This phase locks the public-safe subcontract, procurement, and payment
aggregation baseline for v0.1.4. It does not read raw/private finance data,
enter S16-P2 or S16-P3, perform Stage 16 review, release a formal report,
approve or execute payments, operate bank accounts, execute business actions,
or upload to GitHub.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.check_v014_s15_stage_review import validate_v014_s15_stage_review  # noqa: E402
from KMFA.tools.subcontract_procurement_aggregation import (  # noqa: E402
    REQUIRED_OUTPUT_RECORD_TYPES,
    REQUIRED_SOURCE_LANES,
    build_default_subcontract_procurement_aggregation,
    validate_subcontract_procurement_artifacts,
)


TASK_ID = "KMFA-V014-S16-P1-SUBCONTRACT-PROCUREMENT-20260705"
ACCEPTANCE_ID = "ACC-V014-S16-P1-SUBCONTRACT-PROCUREMENT"
SCHEMA_VERSION = "kmfa.v014_s16_p1_subcontract_procurement.v1"
PHASE_SCOPE = "v014_s16_p1_subcontract_procurement_only"
BASELINE_LOCK_VERSION = "LOCK-KMFA-V014-S16P1-SUBCONTRACT-PROCUREMENT-PUBLIC-SAFE-001"
FORMULA_ID = "FORM-KMFA-V014-S16P1-SUBCONTRACT-PROCUREMENT-001"
MAPPING_VERSION = "MAP-KMFA-V014-S16P1-SUBCONTRACT-PROCUREMENT-v1"

OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_S16_P1_SUBCONTRACT_PROCUREMENT")
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
MANIFEST_PATH = MACHINE_DIR / "subcontract_procurement_manifest.json"
SOURCE_LANE_LOCK_PATH = MACHINE_DIR / "source_lane_lock.jsonl"
PROJECT_MATCH_LOCK_PATH = MACHINE_DIR / "project_match_lock.jsonl"
UNALLOCATED_POOL_LOCK_PATH = MACHINE_DIR / "unallocated_cost_pool_lock.jsonl"
ANOMALY_CANDIDATE_LOCK_PATH = MACHINE_DIR / "anomaly_candidate_lock.jsonl"
REPORT_PATH = HUMAN_DIR / "subcontract_procurement_report.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

V14_TASKPACK_PATH = Path("KMFA/taskpack/v1_4/taskpack/01_KMFA_Codex_TaskPack_v1_4_public_safe.md")
V14_ROADMAP_PATH = Path("KMFA/taskpack/v1_4/roadmap/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_4.md")
RAW_INBOX_REF = "operator-designated raw/private inbox outside repository"
NEXT_PHASE = "S16-P2"
NEXT_REQUIRED_STEP = (
    "Proceed to v0.1.4 S16-P2 project status lifecycle as a separate run only after user instruction. "
    "Do not perform S16-P3, Stage 16 overall review, GitHub upload, formal report release, procurement "
    "execution, payment approval, payment execution, bank operation, collection action, legal action, or "
    "business execution in the S16-P1 run."
)
RAW_ACTION_KEYS = (
    "raw_inbox_read_by_this_phase",
    "raw_inbox_listed_by_this_phase",
    "raw_inbox_inventory_by_this_phase",
    "raw_inbox_stat_by_this_phase",
    "raw_inbox_hashed_by_this_phase",
    "raw_inbox_modified_by_this_phase",
    "raw_inbox_deleted_by_this_phase",
    "raw_inbox_moved_by_this_phase",
    "raw_inbox_renamed_by_this_phase",
    "raw_inbox_overwritten_by_this_phase",
    "raw_inbox_written_by_this_phase",
    "raw_inbox_mutated_by_this_phase",
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


def validate_s15_stage_review_dependency() -> dict[str, Any]:
    result = validate_v014_s15_stage_review()
    if result.get("stage_id") != "S15" or result.get("phase_id") != "S15_STAGE_REVIEW":
        raise RuntimeError("S16-P1 requires validated v0.1.4 Stage 15 review evidence")
    if result.get("next_phase") != "S16-P1":
        raise RuntimeError("Stage 15 review must route to S16-P1")
    if result.get("s16_p1_performed") is not False:
        raise RuntimeError("Stage 15 review dependency must not already include S16-P1")
    if result.get("github_upload_performed") is not False:
        raise RuntimeError("v1.4 upload must remain deferred")
    if result.get("github_upload_deferred_until_v014_stage1_18_complete") is not True:
        raise RuntimeError("v1.4 GitHub upload deferral flag is required")
    return result


def validate_legacy_s16_p1_artifacts() -> tuple[
    dict[str, Any],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    artifacts = build_default_subcontract_procurement_aggregation(generated_at="2026-07-05T10:40:00+10:00")
    validate_subcontract_procurement_artifacts(*artifacts)
    return artifacts


def load_v14_taskpack_baseline() -> dict[str, Any]:
    taskpack_text = V14_TASKPACK_PATH.read_text(encoding="utf-8")
    roadmap_text = V14_ROADMAP_PATH.read_text(encoding="utf-8")

    for token in (
        "外协采购归集",
        "外协费用、采购、付款按项目匹配",
        "未匹配进入未归集成本池",
        "识别重复付款和跨项目费用候选",
    ):
        if token not in roadmap_text:
            raise RuntimeError(f"v1.4 roadmap missing S16-P1 required marker {token}")
    for token in ("外协/采购/付款归集线", "外协费用归集", "未归集成本池", "重复付款候选"):
        if token not in taskpack_text:
            raise RuntimeError(f"v1.4 taskpack missing S16-P1 required marker {token}")

    return {
        "taskpack_read": True,
        "roadmap_read": True,
        "roadmap_includes_s16_p1_requirements": True,
        "taskpack_includes_subcontract_procurement_payment_line": True,
        "source_refs": {
            "taskpack": V14_TASKPACK_PATH.as_posix(),
            "roadmap": V14_ROADMAP_PATH.as_posix(),
        },
    }


def _raw_boundary() -> dict[str, Any]:
    result: dict[str, Any] = {key: False for key in RAW_ACTION_KEYS}
    result.update(
        {
            "raw_inbox_read_required_by_this_phase": False,
            "raw_inbox_ref": RAW_INBOX_REF,
            "private_runtime_output_dir": "KMFA/.codex_private_runtime/",
        }
    )
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
        "supplier_plaintext_committed": False,
        "bank_payload_committed": False,
        "supplier_settlement_payload_committed": False,
        "procurement_order_payload_committed": False,
        "final_payment_payload_committed": False,
        "business_decision_basis_committed": False,
    }


def _quality_gate() -> dict[str, Any]:
    return {
        "subcontract_aggregation_signal_allowed": True,
        "unallocated_cost_pool_review_required": True,
        "duplicate_payment_candidates_review_required": True,
        "cross_project_candidates_review_required": True,
        "owner_or_authorized_delegate_review_required": True,
        "formal_report_allowed": False,
        "complete_trusted_report_display_allowed": False,
        "business_decision_basis_allowed": False,
        "report_grade_bypass_allowed": False,
        "quality_grade_bypass_allowed": False,
        "raw_layer_write_allowed": False,
        "derived_amount_calculation_allowed": False,
        "procurement_execution_allowed": False,
        "payment_approval_allowed": False,
        "payment_execution_allowed": False,
        "bank_operation_allowed": False,
        "supplier_settlement_action_allowed": False,
        "s16_p2_allowed": False,
        "s16_p3_allowed": False,
        "stage16_review_allowed": False,
        "github_upload_allowed": False,
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "release_permission": "blocked",
        "release_block_reason": "s16_p1_public_safe_review_queue_only_pending_manual_reconciliation",
    }


def _phase_boundaries() -> dict[str, bool]:
    return {
        "s15_stage_review_dependency_reused": True,
        "legacy_s16_p1_public_safe_baseline_reused": True,
        "s16_p1_subcontract_procurement_scope_included": True,
        "s16_p2_project_status_scope_included": False,
        "s16_p2_scope_included": False,
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
        "procurement_execution_scope_included": False,
        "payment_approval_scope_included": False,
        "payment_execution_scope_included": False,
        "bank_operation_scope_included": False,
        "collection_action_scope_included": False,
        "legal_action_scope_included": False,
        "business_execution_scope_included": False,
    }


def _source_lane_lock_rows(source_lanes: list[dict[str, Any]], generated_at: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, lane in enumerate(source_lanes, start=1):
        rows.append(
            {
                "schema_version": "kmfa.v014_s16_p1.source_lane_lock.v1",
                "record_type": "v014_s16_p1_source_lane_lock",
                "project_id": "KMFA",
                "stage_id": "S16",
                "phase_id": "S16-P1",
                "lock_row_id": f"V014-S16P1-LANE-{index:03d}",
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
                "procurement_execution_allowed": False,
                "payment_execution_allowed": False,
                "bank_operation_allowed": False,
            }
        )
    return rows


def _project_match_lock_rows(project_matches: list[dict[str, Any]], generated_at: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, match in enumerate(project_matches, start=1):
        rows.append(
            {
                "schema_version": "kmfa.v014_s16_p1.project_match_lock.v1",
                "record_type": "v014_s16_p1_project_match_lock",
                "project_id": "KMFA",
                "stage_id": "S16",
                "phase_id": "S16-P1",
                "lock_row_id": f"V014-S16P1-MATCH-{index:03d}",
                "generated_at": generated_at,
                "legacy_match_record_ref": str(match["match_record_id"]),
                "matching_status": str(match["matching_status"]),
                "manual_review_required": match.get("manual_review_required") is True,
                "cross_project_candidate": match.get("cross_project_candidate") is True,
                "unallocated_cost_pool_required": match.get("unallocated_cost_pool_required") is True,
                "raw_business_values_allowed": False,
                "public_numeric_values_allowed": False,
                "field_plaintext_allowed": False,
                "formal_report_allowed": False,
                "business_decision_basis_allowed": False,
                "procurement_execution_allowed": False,
                "payment_execution_allowed": False,
                "bank_operation_allowed": False,
            }
        )
    return rows


def _unallocated_pool_lock_rows(unallocated_pool: list[dict[str, Any]], generated_at: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, pool_item in enumerate(unallocated_pool, start=1):
        rows.append(
            {
                "schema_version": "kmfa.v014_s16_p1.unallocated_pool_lock.v1",
                "record_type": "v014_s16_p1_unallocated_pool_lock",
                "project_id": "KMFA",
                "stage_id": "S16",
                "phase_id": "S16-P1",
                "lock_row_id": f"V014-S16P1-POOL-{index:03d}",
                "generated_at": generated_at,
                "legacy_pool_item_ref": str(pool_item["pool_item_id"]),
                "legacy_match_record_ref": str(pool_item["match_record_ref"]),
                "assignment_status": str(pool_item["assignment_status"]),
                "manual_review_required": pool_item.get("manual_review_required") is True,
                "raw_business_values_allowed": False,
                "public_numeric_values_allowed": False,
                "field_plaintext_allowed": False,
                "formal_report_allowed": False,
                "business_decision_basis_allowed": False,
                "procurement_execution_allowed": False,
                "payment_execution_allowed": False,
                "bank_operation_allowed": False,
            }
        )
    return rows


def _anomaly_candidate_lock_rows(anomaly_candidates: list[dict[str, Any]], generated_at: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, candidate in enumerate(anomaly_candidates, start=1):
        rows.append(
            {
                "schema_version": "kmfa.v014_s16_p1.anomaly_candidate_lock.v1",
                "record_type": "v014_s16_p1_anomaly_candidate_lock",
                "project_id": "KMFA",
                "stage_id": "S16",
                "phase_id": "S16-P1",
                "lock_row_id": f"V014-S16P1-ANOMALY-{index:03d}",
                "generated_at": generated_at,
                "legacy_candidate_ref": str(candidate["candidate_id"]),
                "candidate_type": str(candidate["candidate_type"]),
                "candidate_status": str(candidate["candidate_status"]),
                "manual_review_required": candidate.get("manual_review_required") is True,
                "action_execution_allowed": False,
                "raw_business_values_allowed": False,
                "public_numeric_values_allowed": False,
                "field_plaintext_allowed": False,
                "formal_report_allowed": False,
                "business_decision_basis_allowed": False,
                "procurement_execution_allowed": False,
                "payment_execution_allowed": False,
                "bank_operation_allowed": False,
            }
        )
    return rows


def build_artifacts(
    generated_at: str | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    generated_at = generated_at or datetime.now().isoformat(timespec="seconds")
    s15_review = validate_s15_stage_review_dependency()
    legacy_manifest, source_lanes, project_matches, unallocated_pool, anomaly_candidates = validate_legacy_s16_p1_artifacts()
    baseline = load_v14_taskpack_baseline()
    legacy_summary = dict(legacy_manifest["summary"])

    source_lane_locks = _source_lane_lock_rows(source_lanes, generated_at)
    project_match_locks = _project_match_lock_rows(project_matches, generated_at)
    unallocated_pool_locks = _unallocated_pool_lock_rows(unallocated_pool, generated_at)
    anomaly_candidate_locks = _anomaly_candidate_lock_rows(anomaly_candidates, generated_at)

    summary = {
        "source_lane_count": legacy_summary["source_lane_count"],
        "project_match_count": legacy_summary["project_match_count"],
        "matched_to_project_count": legacy_summary["matched_to_project_count"],
        "cross_project_match_count": legacy_summary["cross_project_match_count"],
        "unmatched_project_count": legacy_summary["unmatched_project_count"],
        "unallocated_cost_pool_count": legacy_summary["unallocated_cost_pool_count"],
        "anomaly_candidate_count": legacy_summary["anomaly_candidate_count"],
        "duplicate_payment_candidate_count": legacy_summary["duplicate_payment_candidate_count"],
        "cross_project_cost_candidate_count": legacy_summary["cross_project_cost_candidate_count"],
        "pending_reconciliation_count": legacy_summary["pending_reconciliation_count"],
        "report_grade_visible": legacy_summary["report_grade_visible"],
        "procurement_execution_count": 0,
        "payment_approval_count": 0,
        "payment_execution_count": 0,
        "bank_operation_count": 0,
        "formal_report_count": 0,
        "business_decision_basis_count": 0,
    }
    manifest: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "v014_s16_p1_subcontract_procurement_manifest",
        "project_id": "KMFA",
        "version": "0.1.4",
        "stage_id": "S16",
        "phase_id": "S16-P1",
        "phase_scope": PHASE_SCOPE,
        "task_id": TASK_ID,
        "acceptance_ids": [ACCEPTANCE_ID],
        "completed_task_ids": ["S16P1T01", "S16P1T02", "S16P1T03"],
        "status": "completed_validated_local_only_no_go_upload_deferred_subcontract_procurement_locked",
        "generated_at": generated_at,
        "branch": git_output(["branch", "--show-current"]),
        "git_head": git_output(["rev-parse", "HEAD"]),
        "baseline_lock_version": BASELINE_LOCK_VERSION,
        "formula_id": FORMULA_ID,
        "mapping_version": MAPPING_VERSION,
        "s15_stage_review_dependency_validated": True,
        "historical_s16_p1_public_safe_baseline_validated": True,
        "v14_taskpack_baseline": baseline,
        "required_source_lanes": list(REQUIRED_SOURCE_LANES),
        "required_output_record_types": list(REQUIRED_OUTPUT_RECORD_TYPES),
        "upstream_refs": {
            "s15_stage_review_manifest": "KMFA/stage_artifacts/V014_S15_STAGE_REVIEW/machine/stage15_review_manifest.json",
            "legacy_s16_p1_manifest": "KMFA/metadata/reports/subcontract_procurement_aggregation_manifest.json",
            "legacy_s16_p1_stage_manifest": (
                "KMFA/stage_artifacts/S16_P1_subcontract_procurement_aggregation/machine/s16_p1_manifest.json"
            ),
        },
        "legacy_baseline_summary": {
            "stage_phase": legacy_manifest.get("stage_phase"),
            "aggregation_version": legacy_manifest.get("aggregation_version"),
            "matching_version": legacy_manifest.get("matching_version"),
            "anomaly_version": legacy_manifest.get("anomaly_version"),
            "source_lane_count": legacy_summary["source_lane_count"],
            "project_match_count": legacy_summary["project_match_count"],
            "unallocated_cost_pool_count": legacy_summary["unallocated_cost_pool_count"],
            "anomaly_candidate_count": legacy_summary["anomaly_candidate_count"],
            "duplicate_payment_candidate_count": legacy_summary["duplicate_payment_candidate_count"],
            "cross_project_cost_candidate_count": legacy_summary["cross_project_cost_candidate_count"],
            "pending_reconciliation_count": legacy_summary["pending_reconciliation_count"],
            "report_grade_visible": legacy_summary["report_grade_visible"],
            "formal_report_allowed": legacy_manifest.get("quality_gate", {}).get("formal_report_allowed"),
            "payment_execution_allowed": legacy_manifest.get("quality_gate", {}).get("payment_execution_allowed"),
            "bank_operation_allowed": legacy_manifest.get("quality_gate", {}).get("bank_operation_allowed"),
        },
        "stage16_phase_progress": {
            "completed_phase_count": 1,
            "total_phase_count": 3,
            "derived_percent_bps": 3333,
            "derived_percent_label": "33.33%",
            "s16_p1_performed": True,
            "s16_p2_performed": False,
            "s16_p3_performed": False,
            "stage16_review_performed": False,
        },
        "subcontract_procurement_summary": summary,
        "artifact_refs": {
            "manifest": MANIFEST_PATH.as_posix(),
            "source_lane_lock": SOURCE_LANE_LOCK_PATH.as_posix(),
            "project_match_lock": PROJECT_MATCH_LOCK_PATH.as_posix(),
            "unallocated_cost_pool_lock": UNALLOCATED_POOL_LOCK_PATH.as_posix(),
            "anomaly_candidate_lock": ANOMALY_CANDIDATE_LOCK_PATH.as_posix(),
            "report": REPORT_PATH.as_posix(),
            "test_results": TEST_RESULTS_PATH.as_posix(),
            "risk_register": RISK_REGISTER_PATH.as_posix(),
            "rollback_plan": ROLLBACK_PATH.as_posix(),
        },
        "quality_gate": _quality_gate(),
        "phase_boundaries": _phase_boundaries(),
        "raw_data_boundary": _raw_boundary(),
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
            "procurement_execution_blocked",
            "payment_approval_blocked",
            "payment_execution_blocked",
            "bank_operation_blocked",
            "s16_p2_not_performed",
            "s16_p3_not_performed",
            "stage16_review_not_performed",
            "github_upload_deferred_until_v014_stage1_18_complete",
            "business_execution_blocked",
        ],
        "s15_stage_review_dependency_status": {
            "task_id": s15_review.get("task_id"),
            "status": s15_review.get("status"),
            "next_phase": s15_review.get("next_phase"),
            "github_upload_status": s15_review.get("github_upload_status"),
        },
        "next_phase": NEXT_PHASE,
        "next_required_step": NEXT_REQUIRED_STEP,
    }
    return manifest, source_lane_locks, project_match_locks, unallocated_pool_locks, anomaly_candidate_locks


def _report_text(manifest: dict[str, Any]) -> str:
    summary = manifest["subcontract_procurement_summary"]
    return (
        "# KMFA v0.1.4 S16-P1 subcontract procurement lock\n\n"
        f"- Task: {manifest['task_id']}\n"
        "- Status: completed, validated locally, upload deferred.\n"
        f"- Source lanes locked: {summary['source_lane_count']}\n"
        f"- Project match records locked: {summary['project_match_count']}\n"
        f"- Unallocated cost pool items: {summary['unallocated_cost_pool_count']}\n"
        f"- Duplicate payment candidates: {summary['duplicate_payment_candidate_count']}\n"
        f"- Cross-project cost candidates: {summary['cross_project_cost_candidate_count']}\n"
        f"- Pending reconciliation count: {summary['pending_reconciliation_count']}\n"
        "- Report grade remains D; output is review queue evidence only.\n"
        "- Procurement execution, payment approval, payment execution, bank operation, business execution, "
        "S16-P2, S16-P3, Stage 16 review, and GitHub upload are blocked in this phase.\n"
    )


def _test_results_text(manifest: dict[str, Any]) -> str:
    return (
        "# KMFA v0.1.4 S16-P1 test results\n\n"
        f"- Generated task: {manifest['task_id']}\n"
        "- Required checks: generator, validator, legacy S16-P1 validator, Stage 15 review validator, unit test, "
        "governance validator, public evidence scan, raw/private suffix scan, and local commit.\n"
        "- Final command evidence is recorded by the S16-P1 run after verification.\n"
    )


def _risk_register_text() -> str:
    return (
        "# KMFA v0.1.4 S16-P1 risk register\n\n"
        "- R1: Public-safe structural matches can be mistaken for approved procurement or payment actions. "
        "Mitigation: all execution gates remain false and validator enforces the block.\n"
        "- R2: Unallocated cost pool and anomaly candidates require owner or authorized delegate review. "
        "Mitigation: report grade D and business decision basis remain blocked.\n"
        "- R3: Legacy Stage 16 historical artifacts can imply later-phase completion. Mitigation: this v0.1.4 "
        "manifest records only S16-P1 and explicitly blocks S16-P2, S16-P3, Stage 16 review, and upload.\n"
    )


def _rollback_text() -> str:
    return (
        "# KMFA v0.1.4 S16-P1 rollback plan\n\n"
        "Rollback is local-only: remove the V014_S16_P1_SUBCONTRACT_PROCUREMENT artifact directory, remove the "
        "v014 S16-P1 tool, validator, and test file, then revert governance entries from this phase before any "
        "future upload gate. No raw/private inbox file is modified by this phase.\n"
    )


def generate(generated_at: str | None = None) -> dict[str, Any]:
    manifest, source_lane_locks, project_match_locks, unallocated_pool_locks, anomaly_candidate_locks = build_artifacts(
        generated_at
    )
    write_json(MANIFEST_PATH, manifest)
    write_jsonl(SOURCE_LANE_LOCK_PATH, source_lane_locks)
    write_jsonl(PROJECT_MATCH_LOCK_PATH, project_match_locks)
    write_jsonl(UNALLOCATED_POOL_LOCK_PATH, unallocated_pool_locks)
    write_jsonl(ANOMALY_CANDIDATE_LOCK_PATH, anomaly_candidate_locks)
    write_text(REPORT_PATH, _report_text(manifest))
    write_text(TEST_RESULTS_PATH, _test_results_text(manifest))
    write_text(RISK_REGISTER_PATH, _risk_register_text())
    write_text(ROLLBACK_PATH, _rollback_text())
    return manifest


def main() -> int:
    manifest = generate()
    summary = manifest["subcontract_procurement_summary"]
    print(
        "PASS: KMFA v0.1.4 S16-P1 subcontract procurement generated "
        f"(source_lanes={summary['source_lane_count']}, project_matches={summary['project_match_count']}, "
        f"unallocated_pool={summary['unallocated_cost_pool_count']}, "
        f"duplicate_payment_candidates={summary['duplicate_payment_candidate_count']}, "
        f"cross_project_candidates={summary['cross_project_cost_candidate_count']}, "
        f"report_grade={summary['report_grade_visible']}, payment_execution={summary['payment_execution_count']}, "
        f"bank_operation={summary['bank_operation_count']}, next_phase={manifest['next_phase']}, "
        f"github_upload={manifest['github_upload']['github_upload_performed']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
