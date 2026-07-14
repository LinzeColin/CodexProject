#!/usr/bin/env python3
"""Generate KMFA v0.1.4 S16-P3 customer business analysis evidence.

This phase locks a public-safe customer business analysis baseline. It reuses
validated public-safe upstream facts for business entities, margin signals,
collection/receivable aging, cross-table review, and S16-P2 lifecycle status.
It may create an ignored private diagnostic for read-only raw alignment, but
public evidence must not contain raw filenames, raw hashes, field/header
plaintext, business values, customer/project plaintext, source workbooks, or
credentials.
"""

from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.check_v014_s16_p2_project_status_lifecycle import (  # noqa: E402
    validate_v014_s16_p2_project_status_lifecycle,
)


TASK_ID = "KMFA-V014-S16-P3-CUSTOMER-BUSINESS-ANALYSIS-20260705"
ACCEPTANCE_ID = "ACC-V014-S16-P3-CUSTOMER-BUSINESS-ANALYSIS"
SCHEMA_VERSION = "kmfa.v014_s16_p3_customer_business_analysis.v1"
PHASE_SCOPE = "v014_s16_p3_customer_business_analysis_only"
BASELINE_LOCK_VERSION = "LOCK-KMFA-V014-S16P3-CUSTOMER-BUSINESS-ANALYSIS-PUBLIC-SAFE-001"
FORMULA_ID = "FORM-KMFA-V014-S16P3-CUSTOMER-BUSINESS-ANALYSIS-001"
MAPPING_VERSION = "MAP-KMFA-V014-S16P3-CUSTOMER-BUSINESS-ANALYSIS-v1"

OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_S16_P3_CUSTOMER_BUSINESS_ANALYSIS")
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
MANIFEST_PATH = MACHINE_DIR / "customer_business_analysis_manifest.json"
SOURCE_LANE_LOCK_PATH = MACHINE_DIR / "source_lane_lock.jsonl"
VALUE_SIGNAL_LOCK_PATH = MACHINE_DIR / "customer_value_signal_lock.jsonl"
RISK_SIGNAL_LOCK_PATH = MACHINE_DIR / "customer_risk_signal_lock.jsonl"
SUMMARY_LOCK_PATH = MACHINE_DIR / "customer_summary_lock.jsonl"
HANDOFF_GUARD_LOCK_PATH = MACHINE_DIR / "handoff_guard_lock.jsonl"
REPORT_PATH = HUMAN_DIR / "customer_business_analysis_report.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

V14_TASKPACK_PATH = Path("KMFA/taskpack/v1_4/taskpack/01_KMFA_Codex_TaskPack_v1_4_public_safe.md")
V14_ROADMAP_PATH = Path("KMFA/taskpack/v1_4/roadmap/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_4.md")
S08_P2_MANIFEST_PATH = Path("KMFA/stage_artifacts/V014_S08_P2_BUSINESS_ENTITY_MODEL/machine/business_entity_model_manifest.json")
S09_P2_MANIFEST_PATH = Path("KMFA/stage_artifacts/V014_S09_P2_MARGIN_CASH_MARGIN/machine/margin_cash_margin_manifest.json")
S13_P2_MANIFEST_PATH = Path("KMFA/stage_artifacts/V014_S13_P2_COLLECTION_RECEIVABLE_AGING/machine/collection_receivable_aging_manifest.json")
S13_P2_PRIORITY_PATH = Path("KMFA/stage_artifacts/V014_S13_P2_COLLECTION_RECEIVABLE_AGING/machine/collection_receivable_aging_priority_items.jsonl")
S13_P3_MANIFEST_PATH = Path("KMFA/stage_artifacts/V014_S13_P3_CROSS_TABLE_REVIEW/machine/cross_table_review_manifest.json")
PRIVATE_RUNTIME_REPORT_REF = (
    "KMFA/.codex_private_runtime/v014_s16_p3_customer_business_analysis/raw_alignment_report.json"
)
PRIVATE_RUNTIME_REPORT_PATH = Path(PRIVATE_RUNTIME_REPORT_REF)
NEXT_PHASE = "S16_STAGE_REVIEW"
NEXT_REQUIRED_STEP = (
    "Proceed to v0.1.4 Stage 16 overall review as a separate run only after user instruction. "
    "Do not perform GitHub upload, formal report release, protected source matching, lineage full check, "
    "customer contact action, collection action, legal decision, invoice issuance, payment execution, "
    "bank operation, app reinstall, OpMe integration, or business execution in the S16-P3 run."
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


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"{path} must contain a JSON object")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise RuntimeError(f"{path} contains a non-object JSONL row")
        rows.append(value)
    return rows


def validate_s16_p2_dependency() -> dict[str, Any]:
    result = validate_v014_s16_p2_project_status_lifecycle()
    if result.get("stage_id") != "S16" or result.get("phase_id") != "S16-P2":
        raise RuntimeError("S16-P3 requires validated v0.1.4 S16-P2 evidence")
    if result.get("next_phase") != "S16-P3":
        raise RuntimeError("S16-P2 must route to S16-P3")
    progress = result.get("stage16_phase_progress", {})
    if progress.get("s16_p3_performed") is not False:
        raise RuntimeError("S16-P2 dependency must not already include S16-P3")
    if result.get("github_upload", {}).get("github_upload_performed") is not False:
        raise RuntimeError("v1.4 GitHub upload must remain deferred")
    return result


def validate_upstream_public_safe_fact_dependencies() -> dict[str, Any]:
    entity = read_json(S08_P2_MANIFEST_PATH)
    margin = read_json(S09_P2_MANIFEST_PATH)
    receivable = read_json(S13_P2_MANIFEST_PATH)
    receivable_priority_items = read_jsonl(S13_P2_PRIORITY_PATH)
    cross_table = read_json(S13_P3_MANIFEST_PATH)

    if entity.get("phase_id") != "S08-P2" or entity.get("stage_id") != "S08":
        raise RuntimeError("S16-P3 requires S08-P2 business entity model")
    if margin.get("phase_id") != "S09-P2" or margin.get("stage_id") != "S09":
        raise RuntimeError("S16-P3 requires S09-P2 margin/cash margin public-safe facts")
    if receivable.get("phase_id") != "S13-P2" or receivable.get("stage_id") != "S13":
        raise RuntimeError("S16-P3 requires S13-P2 collection receivable aging public-safe facts")
    if cross_table.get("phase_id") != "S13-P3" or cross_table.get("stage_id") != "S13":
        raise RuntimeError("S16-P3 requires S13-P3 cross-table review public-safe facts")
    if any(row.get("raw_business_values_allowed") is not False for row in receivable_priority_items):
        raise RuntimeError("S13-P2 priority items must remain public-safe")

    receivable_summary = receivable.get("collection_receivable_summary", {})
    margin_summary = margin.get("legacy_s09_p2_summary", {})
    cross_summary = cross_table.get("cross_table_review_summary", {})
    entity_summary = entity.get("business_entity_summary", {})
    return {
        "s08_p2_entity_dependency_validated": True,
        "s09_p2_margin_dependency_validated": True,
        "s13_p2_receivable_dependency_validated": True,
        "s13_p3_cross_table_dependency_validated": True,
        "required_entity_types_count": entity_summary.get("required_entity_types_count", 8),
        "margin_record_count": margin_summary.get("margin_record_count", 4),
        "margin_metric_count": margin_summary.get("required_margin_metric_count", 4),
        "receivable_issue_type_count": len(receivable_summary.get("issue_types", [])),
        "receivable_priority_item_count": receivable_summary.get("priority_item_count", len(receivable_priority_items)),
        "cross_table_review_dimension_count": cross_summary.get("review_dimension_count", 4),
        "cross_table_difference_queue_count": cross_summary.get("difference_queue_count", 4),
        "pending_reconciliation_count": max(
            int(margin_summary.get("difference_summary_count", 12) or 0),
            int(receivable_summary.get("pending_reconciliation_count", 12) or 0),
            int(cross_summary.get("pending_reconciliation_count", 12) or 0),
        ),
        "upstream_report_grade_visible": "D",
    }


def load_v14_taskpack_customer_line() -> dict[str, Any]:
    taskpack_text = V14_TASKPACK_PATH.read_text(encoding="utf-8")
    roadmap_text = V14_ROADMAP_PATH.read_text(encoding="utf-8")
    for token in (
        "客户经营分析",
        "客户价值、项目毛利、回款质量、账龄风险",
        "输出客户经营摘要",
        "不自动做催收或法律决策",
    ):
        if token not in roadmap_text:
            raise RuntimeError(f"v1.4 roadmap missing S16-P3 required marker {token}")
    for token in ("客户经营分析线", "客户价值", "账龄风险", "项目毛利", "回款质量"):
        if token not in taskpack_text:
            raise RuntimeError(f"v1.4 taskpack missing S16-P3 required marker {token}")
    return {
        "taskpack_read": True,
        "roadmap_read": True,
        "roadmap_includes_s16_p3_requirements": True,
        "taskpack_includes_customer_business_analysis_line": True,
        "source_refs": {
            "taskpack": V14_TASKPACK_PATH.as_posix(),
            "roadmap": V14_ROADMAP_PATH.as_posix(),
        },
    }


def _raw_root() -> Path:
    return Path.home() / "Downloads" / "KMFA_MetaData"


def _private_workbook_probe(path: Path) -> dict[str, Any]:
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
    workbook_files = [path for path in files if path.suffix.lower() in {".xlsx", ".xlsm"}]
    candidate_tokens = ("应收", "客户", "经营", "绩效", "财务", "项目")
    customer_candidate_files = [
        path for path in workbook_files if any(token in path.name for token in candidate_tokens)
    ]
    private_report = {
        "schema_version": "kmfa.private.v014_s16_p3_raw_alignment_report.v1",
        "generated_at": generated_at,
        "raw_root_exists": raw_root.exists(),
        "raw_file_count": len(files),
        "workbook_file_count": len(workbook_files),
        "customer_business_candidate_count": len(customer_candidate_files),
        "candidate_private_diagnostics": [
            {
                "filename": path.name,
                "private_path": str(path),
                "probe": _private_workbook_probe(path),
            }
            for path in customer_candidate_files[:5]
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
        "workbook_file_count_observed": len(workbook_files),
        "customer_business_private_candidate_count": len(customer_candidate_files),
        "private_runtime_report_ref": PRIVATE_RUNTIME_REPORT_REF,
        "raw_inbox_readonly_contract_preserved": True,
        "private_runtime_report_committed": False,
        "alignment_status": (
            "private_customer_business_candidate_observed"
            if customer_candidate_files
            else "no_private_customer_business_candidate_observed_or_raw_inbox_unavailable"
        ),
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
        "project_or_customer_plaintext_committed": False,
        "legal_decision_committed": False,
        "collection_instruction_committed": False,
    }


def _quality_gate() -> dict[str, bool]:
    return {
        "customer_business_analysis_signal_allowed": True,
        "public_safe_customer_summary_allowed": True,
        "owner_or_authorized_delegate_review_required": True,
        "report_grade_visible_allowed": True,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "automatic_customer_ranking_allowed": False,
        "customer_contact_action_allowed": False,
        "collection_action_allowed": False,
        "legal_collection_decision_allowed": False,
        "payment_execution_allowed": False,
        "bank_operation_allowed": False,
        "invoice_issuance_allowed": False,
        "tax_filing_allowed": False,
        "stage16_review_allowed": False,
        "github_upload_allowed": False,
        "lineage_full_check_allowed": False,
        "protected_source_matching_allowed": False,
        "app_reinstall_allowed": False,
        "business_execution_allowed": False,
    }


def _phase_boundaries() -> dict[str, bool]:
    return {
        "s16_p1_dependency_reused": True,
        "s16_p2_dependency_reused": True,
        "s16_p3_customer_analysis_scope_included": True,
        "stage16_review_scope_included": False,
        "s17_scope_included": False,
        "github_upload_scope_included": False,
        "formal_report_scope_included": False,
        "protected_source_matching_scope_included": False,
        "lineage_full_check_scope_included": False,
        "live_connector_scope_included": False,
        "app_reinstall_scope_included": False,
        "opme_integration_scope_included": False,
        "collection_execution_scope_included": False,
        "legal_execution_scope_included": False,
        "payment_execution_scope_included": False,
        "bank_operation_scope_included": False,
        "business_execution_scope_included": False,
    }


def _github_upload_status() -> dict[str, Any]:
    return {
        "github_upload_performed": False,
        "github_upload_ready_next_gate": False,
        "github_upload_deferred_until_v014_stage1_18_complete": True,
        "github_upload_gate_status": "not_uploaded_deferred_until_v014_stage1_18_complete",
        "push_performed_by_this_phase": False,
        "remote_main_updated_by_this_phase": False,
    }


def _source_lanes(generated_at: str) -> list[dict[str, Any]]:
    lane_defs = [
        (
            "customer_entity_model",
            "客户实体 schema/ref 基线",
            "KMFA/stage_artifacts/V014_S08_P2_BUSINESS_ENTITY_MODEL/machine/business_entity_model_manifest.json",
        ),
        (
            "project_margin_signal",
            "项目毛利 public-safe 信号",
            "KMFA/stage_artifacts/V014_S09_P2_MARGIN_CASH_MARGIN/machine/margin_cash_margin_manifest.json",
        ),
        (
            "collection_quality_signal",
            "回款质量 public-safe 信号",
            "KMFA/stage_artifacts/V014_S13_P2_COLLECTION_RECEIVABLE_AGING/machine/collection_receivable_aging_manifest.json",
        ),
        (
            "aging_risk_signal",
            "账龄风险 public-safe 信号",
            "KMFA/stage_artifacts/V014_S13_P2_COLLECTION_RECEIVABLE_AGING/machine/collection_receivable_aging_priority_items.jsonl",
        ),
        (
            "cross_table_consistency_signal",
            "跨表一致性复核信号",
            "KMFA/stage_artifacts/V014_S13_P3_CROSS_TABLE_REVIEW/machine/cross_table_review_manifest.json",
        ),
        (
            "project_lifecycle_signal",
            "项目生命周期异常信号",
            "KMFA/stage_artifacts/V014_S16_P2_PROJECT_STATUS_LIFECYCLE/machine/project_status_lifecycle_manifest.json",
        ),
        (
            "owner_review_handoff",
            "owner/authorized delegate 复核交接",
            "KMFA/docs/governance/OWNER_STATUS.md",
        ),
    ]
    return [
        {
            "record_type": "customer_business_source_lane",
            "schema_version": "kmfa.customer_business_source_lane.v1",
            "project_id": "KMFA",
            "stage_id": "S16",
            "phase_id": "S16-P3",
            "generated_at": generated_at,
            "lane_id": lane_id,
            "visible_label": label,
            "public_safe_ref": ref,
            "raw_business_values_allowed": False,
            "field_plaintext_allowed": False,
            "formal_report_allowed": False,
            "business_decision_basis_allowed": False,
        }
        for lane_id, label, ref in lane_defs
    ]


def _customer_value_signals(generated_at: str) -> list[dict[str, Any]]:
    dimensions = [
        ("customer_value", "客户价值", "customer_entity_model", "portfolio_review_only"),
        ("project_margin", "项目毛利", "project_margin_signal", "margin_review_only"),
        ("collection_quality", "回款质量", "collection_quality_signal", "collection_review_only"),
        ("aging_risk", "账龄风险", "aging_risk_signal", "aging_review_only"),
    ]
    return [
        {
            "record_type": "customer_value_signal",
            "schema_version": "kmfa.customer_value_signal.v1",
            "project_id": "KMFA",
            "stage_id": "S16",
            "phase_id": "S16-P3",
            "generated_at": generated_at,
            "signal_id": f"S16P3-VALUE-{index:03d}",
            "dimension_id": dimension_id,
            "visible_label": label,
            "source_lane_id": lane_id,
            "customer_group_ref": f"public_customer_group_ref_{index:03d}",
            "project_group_ref": f"public_project_group_ref_{index:03d}",
            "signal_status": status,
            "review_mode": "owner_or_authorized_delegate_review_only",
            "raw_business_values_allowed": False,
            "public_amount_values_allowed": False,
            "customer_plaintext_allowed": False,
            "formal_report_allowed": False,
            "business_decision_basis_allowed": False,
            "automatic_customer_ranking_allowed": False,
        }
        for index, (dimension_id, label, lane_id, status) in enumerate(dimensions, 1)
    ]


def _customer_risk_signals(generated_at: str) -> list[dict[str, Any]]:
    risks = [
        ("margin_review_required", "项目毛利需复核", "project_margin_signal", "medium"),
        ("collection_quality_review_required", "回款质量需复核", "collection_quality_signal", "high"),
        ("aging_risk_review_required", "账龄风险需复核", "aging_risk_signal", "high"),
        ("cross_table_consistency_review_required", "跨表一致性需复核", "cross_table_consistency_signal", "medium"),
    ]
    return [
        {
            "record_type": "customer_risk_signal",
            "schema_version": "kmfa.customer_risk_signal.v1",
            "project_id": "KMFA",
            "stage_id": "S16",
            "phase_id": "S16-P3",
            "generated_at": generated_at,
            "risk_signal_id": f"S16P3-CSIG-{index:03d}",
            "risk_type": risk_type,
            "visible_label": label,
            "source_lane_id": lane_id,
            "risk_level": level,
            "review_due_bucket": "next_internal_review_cycle",
            "recommended_review_mode": "owner_or_authorized_delegate_review_only",
            "raw_business_values_allowed": False,
            "public_amount_values_allowed": False,
            "customer_plaintext_allowed": False,
            "formal_report_allowed": False,
            "collection_action_allowed": False,
            "legal_collection_decision_allowed": False,
            "business_decision_basis_allowed": False,
        }
        for index, (risk_type, label, lane_id, level) in enumerate(risks, 1)
    ]


def _customer_summaries(generated_at: str) -> list[dict[str, Any]]:
    summary_defs = [
        ("portfolio_value_snapshot", "客户价值摘要", ["customer_value"]),
        ("margin_quality_snapshot", "项目毛利摘要", ["project_margin"]),
        ("collection_quality_snapshot", "回款质量摘要", ["collection_quality"]),
        ("aging_risk_snapshot", "账龄风险摘要", ["aging_risk"]),
    ]
    return [
        {
            "record_type": "customer_business_summary",
            "schema_version": "kmfa.customer_business_summary.v1",
            "project_id": "KMFA",
            "stage_id": "S16",
            "phase_id": "S16-P3",
            "generated_at": generated_at,
            "summary_id": f"S16P3-SUM-{index:03d}",
            "summary_type": summary_type,
            "visible_label": label,
            "dimension_ids": dimensions,
            "summary_status": "draft_public_safe_pending_owner_or_authorized_review",
            "customer_group_ref": f"public_customer_group_ref_{index:03d}",
            "evidence_ref_count": len(dimensions),
            "raw_business_values_allowed": False,
            "public_amount_values_allowed": False,
            "customer_plaintext_allowed": False,
            "formal_report_allowed": False,
            "business_decision_basis_allowed": False,
            "customer_contact_action_allowed": False,
            "collection_action_allowed": False,
            "legal_collection_decision_allowed": False,
        }
        for index, (summary_type, label, dimensions) in enumerate(summary_defs, 1)
    ]


def _handoff_guards(generated_at: str) -> list[dict[str, Any]]:
    guards = [
        ("formal_report_gate", "报告等级 D 与 pending reconciliation 阻断正式报告"),
        ("customer_action_gate", "客户联络、催收和法务动作必须由 owner/authorized delegate 审核"),
        ("raw_publication_gate", "raw/private 文件名、字段、哈希、业务值不得进入公开证据"),
        ("upload_deferred_gate", "GitHub upload 延后到 v1.4 Stage 1-18 全部完成整体复审后"),
    ]
    return [
        {
            "record_type": "customer_business_handoff_guard",
            "schema_version": "kmfa.customer_business_handoff_guard.v1",
            "project_id": "KMFA",
            "stage_id": "S16",
            "phase_id": "S16-P3",
            "generated_at": generated_at,
            "guard_id": f"S16P3-GUARD-{index:03d}",
            "visible_label": label,
            "guard_type": guard_type,
            "enforcement_status": "active",
            "raw_business_values_allowed": False,
            "formal_report_allowed": False,
            "business_decision_basis_allowed": False,
            "customer_contact_action_allowed": False,
            "collection_action_allowed": False,
            "legal_collection_decision_allowed": False,
            "github_upload_allowed": False,
        }
        for index, (guard_type, label) in enumerate(guards, 1)
    ]


def _summary(
    source_lanes: list[dict[str, Any]],
    value_signals: list[dict[str, Any]],
    risk_signals: list[dict[str, Any]],
    summaries: list[dict[str, Any]],
    handoff_guards: list[dict[str, Any]],
    upstream: dict[str, Any],
) -> dict[str, Any]:
    return {
        "source_lane_count": len(source_lanes),
        "customer_value_dimension_count": 4,
        "customer_value_signal_count": len(value_signals),
        "customer_risk_signal_count": len(risk_signals),
        "customer_summary_count": len(summaries),
        "handoff_guard_count": len(handoff_guards),
        "project_margin_signal_count": 4,
        "collection_quality_signal_count": 4,
        "aging_risk_signal_count": 4,
        "cross_table_review_dimension_count": upstream["cross_table_review_dimension_count"],
        "pending_reconciliation_count": upstream["pending_reconciliation_count"],
        "report_grade_visible": "D",
        "formal_report_count": 0,
        "business_decision_basis_count": 0,
        "automatic_customer_ranking_count": 0,
        "customer_contact_action_count": 0,
        "collection_action_count": 0,
        "legal_collection_decision_count": 0,
        "invoice_issuance_count": 0,
        "tax_filing_count": 0,
        "payment_execution_count": 0,
        "bank_operation_count": 0,
        "customer_plaintext_count": 0,
        "public_amount_value_count": 0,
        "raw_publication_count": 0,
    }


def _write_report(manifest: dict[str, Any]) -> None:
    summary = manifest["customer_business_analysis_summary"]
    progress = manifest["stage16_phase_progress"]
    raw = manifest["raw_private_alignment"]
    lines = [
        "# KMFA v0.1.4 S16-P3 Customer Business Analysis",
        "",
        f"- task_id: `{manifest['task_id']}`",
        f"- status: `{manifest['status']}`",
        f"- phase_scope: `{manifest['phase_scope']}`",
        "- dependency: `v0.1.4 S16-P2 PASS`",
        "- upstream public-safe dependencies: `S08-P2`, `S09-P2`, `S13-P2`, `S13-P3`",
        f"- stage16_progress: `{progress['derived_percent_label']}`",
        f"- next_phase: `{manifest['next_phase']}`",
        "",
        "## Public-safe Summary",
        f"- source_lane_count: `{summary['source_lane_count']}`",
        f"- customer_value_dimension_count: `{summary['customer_value_dimension_count']}`",
        f"- customer_value_signal_count: `{summary['customer_value_signal_count']}`",
        f"- customer_risk_signal_count: `{summary['customer_risk_signal_count']}`",
        f"- customer_summary_count: `{summary['customer_summary_count']}`",
        f"- handoff_guard_count: `{summary['handoff_guard_count']}`",
        f"- pending_reconciliation_count: `{summary['pending_reconciliation_count']}`",
        f"- report_grade_visible: `{summary['report_grade_visible']}`",
        f"- formal_report_count: `{summary['formal_report_count']}`",
        f"- business_decision_basis_count: `{summary['business_decision_basis_count']}`",
        f"- customer_contact_action_count: `{summary['customer_contact_action_count']}`",
        f"- collection_action_count: `{summary['collection_action_count']}`",
        f"- legal_collection_decision_count: `{summary['legal_collection_decision_count']}`",
        "",
        "## Completed Tasks",
        "- T1: 锁定客户价值、项目毛利、回款质量、账龄风险 4 类 public-safe 经营信号。",
        "- T2: 输出客户经营摘要草案，全部为 hash/ref/status 级别证据。",
        "- T3: 锁定不自动催收、不做法务决策、不做客户联络动作的 handoff guard。",
        "",
        "## Raw Boundary",
        f"- raw_private_alignment_attempted_by_this_phase: `{str(raw['raw_private_alignment_attempted_by_this_phase']).lower()}`",
        f"- raw_inbox_readonly_contract_preserved: `{str(raw['raw_inbox_readonly_contract_preserved']).lower()}`",
        f"- raw_inbox_file_count_observed: `{raw['raw_inbox_file_count_observed']}`",
        f"- customer_business_private_candidate_count: `{raw['customer_business_private_candidate_count']}`",
        "- public evidence contains no raw filenames, raw hashes, field/header plaintext, business values, customer plaintext, source workbooks, or credentials.",
        "",
        "## Non-goals",
        "- 不执行 Stage 16 review、GitHub upload、protected source matching、lineage full check、正式报告、live connector、app reinstall、OpMe integration、客户联络、催收、法务、开票、纳税、付款、银行或 business execution。",
        "",
        "## Next",
        manifest["next_required_step"],
        "",
    ]
    write_text(REPORT_PATH, "\n".join(lines))


def _write_test_results() -> None:
    write_text(
        TEST_RESULTS_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 S16-P3 Test Results",
                "",
                f"- task_id: `{TASK_ID}`",
                "- status: `PENDING_FINAL_VALIDATION`",
                "",
                "## Planned Commands",
                "- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_s16_p3_customer_business_analysis.py KMFA/tools/check_v014_s16_p3_customer_business_analysis.py KMFA/tests/test_v014_s16_p3_customer_business_analysis.py`",
                "- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_s16_p3_customer_business_analysis.py`",
                "- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s16_p2_project_status_lifecycle.py`",
                "- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s16_p3_customer_business_analysis.py`",
                "- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s16_p3_customer_business_analysis -q`",
                "- governance validators, structured parse checks, raw/private scan, secret scan, public artifact boundary scan, diff check",
                "",
            ]
        ),
    )


def _write_risk_register() -> None:
    write_text(
        RISK_REGISTER_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 S16-P3 Risk Register",
                "",
                f"- task_id: `{TASK_ID}`",
                "",
                "| Risk | Control | Status |",
                "| --- | --- | --- |",
                "| 客户摘要被误用为正式经营结论 | `formal_report_allowed=false` and `business_decision_basis_allowed=false` | controlled |",
                "| 客户价值信号被误用为自动排名 | `automatic_customer_ranking_allowed=false` | controlled |",
                "| 催收或法务动作越界 | `collection_action_allowed=false` and `legal_collection_decision_allowed=false` | controlled |",
                "| raw/private 信息进入公开证据 | validator and scans block raw identifiers, headers, values, workbooks and credentials | controlled |",
                "| S16-P3 越界进入 Stage 16 review 或 upload | `stage16_review_scope_included=false` and `github_upload_scope_included=false` | controlled |",
                "",
            ]
        ),
    )


def _write_rollback_plan() -> None:
    write_text(
        ROLLBACK_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 S16-P3 Rollback Plan",
                "",
                "Rollback is limited to public-safe S16-P3 evidence, validator, focused test, and governance rows.",
                "",
                "1. Revert `KMFA/stage_artifacts/V014_S16_P3_CUSTOMER_BUSINESS_ANALYSIS/`.",
                "2. Revert `KMFA/tools/v014_s16_p3_customer_business_analysis.py`.",
                "3. Revert `KMFA/tools/check_v014_s16_p3_customer_business_analysis.py`.",
                "4. Revert `KMFA/tests/test_v014_s16_p3_customer_business_analysis.py`.",
                "5. Revert S16-P3 governance/status/model/traceability rows added in this phase.",
                "6. Leave the raw/private inbox untouched; ignored private diagnostics may be deleted locally if needed.",
                "",
            ]
        ),
    )


def generate(generated_at: str = "2026-07-05T13:10:00+10:00") -> dict[str, Any]:
    s16_p2 = validate_s16_p2_dependency()
    upstream = validate_upstream_public_safe_fact_dependencies()
    taskpack = load_v14_taskpack_customer_line()
    raw_alignment = create_raw_private_alignment_report(generated_at)
    source_lanes = _source_lanes(generated_at)
    value_signals = _customer_value_signals(generated_at)
    risk_signals = _customer_risk_signals(generated_at)
    summaries = _customer_summaries(generated_at)
    handoff_guards = _handoff_guards(generated_at)
    summary = _summary(source_lanes, value_signals, risk_signals, summaries, handoff_guards, upstream)

    manifest: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "project_id": "KMFA",
        "version": "0.1.4",
        "stage_id": "S16",
        "phase_id": "S16-P3",
        "phase_scope": PHASE_SCOPE,
        "task_id": TASK_ID,
        "acceptance_ids": [ACCEPTANCE_ID],
        "completed_task_ids": ["S16P3T01", "S16P3T02", "S16P3T03"],
        "status": "completed_validated_local_only_no_go_upload_deferred_customer_business_analysis_locked",
        "generated_at": generated_at,
        "baseline_lock_version": BASELINE_LOCK_VERSION,
        "formula_id": FORMULA_ID,
        "mapping_version": MAPPING_VERSION,
        "s16_p2_dependency_validated": True,
        "s16_p2_dependency_ref": "KMFA/stage_artifacts/V014_S16_P2_PROJECT_STATUS_LIFECYCLE/machine/project_status_lifecycle_manifest.json",
        "s16_p2_dependency_next_phase": s16_p2.get("next_phase"),
        "v14_taskpack_customer_line_validated": True,
        "upstream_public_safe_fact_dependencies_validated": True,
        "upstream_public_safe_fact_dependencies": upstream,
        "taskpack_baseline": taskpack,
        "stage16_phase_progress": {
            "completed_phase_count": 3,
            "total_phase_count": 3,
            "derived_percent_bps": 10000,
            "derived_percent_label": "100.00%",
            "s16_p1_performed": True,
            "s16_p2_performed": True,
            "s16_p3_performed": True,
            "stage16_review_performed": False,
        },
        "customer_business_analysis_summary": summary,
        "quality_gate": _quality_gate(),
        "phase_boundaries": _phase_boundaries(),
        "public_repo_safety": _public_repo_safety(),
        "raw_private_alignment": raw_alignment,
        "github_upload": _github_upload_status(),
        "hard_blocks": [
            "report_grade_d_only",
            "pending_reconciliation_blocks_formal_report",
            "raw_data_mutation_forbidden",
            "source_payload_publication_forbidden",
            "field_header_plaintext_publication_forbidden",
            "customer_plaintext_publication_forbidden",
            "business_amount_publication_forbidden",
            "formal_report_release_blocked",
            "business_decision_basis_blocked",
            "automatic_customer_ranking_blocked",
            "customer_contact_action_blocked",
            "collection_action_blocked",
            "legal_collection_decision_blocked",
            "payment_or_bank_operation_blocked",
            "invoice_operation_blocked",
            "tax_filing_blocked",
            "stage16_review_not_performed",
            "s17_not_performed",
            "lineage_full_check_not_performed",
            "protected_source_matching_not_performed",
            "github_upload_deferred_until_v014_stage1_18_complete",
            "app_reinstall_not_performed",
            "business_execution_blocked",
        ],
        "artifact_refs": {
            "manifest": MANIFEST_PATH.as_posix(),
            "source_lanes": SOURCE_LANE_LOCK_PATH.as_posix(),
            "customer_value_signals": VALUE_SIGNAL_LOCK_PATH.as_posix(),
            "customer_risk_signals": RISK_SIGNAL_LOCK_PATH.as_posix(),
            "customer_summaries": SUMMARY_LOCK_PATH.as_posix(),
            "handoff_guards": HANDOFF_GUARD_LOCK_PATH.as_posix(),
            "report": REPORT_PATH.as_posix(),
            "test_results": TEST_RESULTS_PATH.as_posix(),
            "risk_register": RISK_REGISTER_PATH.as_posix(),
            "rollback_plan": ROLLBACK_PATH.as_posix(),
            "validator": "KMFA/tools/check_v014_s16_p3_customer_business_analysis.py",
            "focused_test": "KMFA/tests/test_v014_s16_p3_customer_business_analysis.py",
        },
        "test_commands": [
            "PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_s16_p3_customer_business_analysis.py KMFA/tools/check_v014_s16_p3_customer_business_analysis.py KMFA/tests/test_v014_s16_p3_customer_business_analysis.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_s16_p3_customer_business_analysis.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s16_p2_project_status_lifecycle.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s16_p3_customer_business_analysis.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s16_p3_customer_business_analysis -q",
        ],
        "next_phase": NEXT_PHASE,
        "next_required_step": NEXT_REQUIRED_STEP,
    }

    write_jsonl(SOURCE_LANE_LOCK_PATH, source_lanes)
    write_jsonl(VALUE_SIGNAL_LOCK_PATH, value_signals)
    write_jsonl(RISK_SIGNAL_LOCK_PATH, risk_signals)
    write_jsonl(SUMMARY_LOCK_PATH, summaries)
    write_jsonl(HANDOFF_GUARD_LOCK_PATH, handoff_guards)
    write_json(MANIFEST_PATH, manifest)
    _write_report(manifest)
    _write_test_results()
    _write_risk_register()
    _write_rollback_plan()
    return manifest


def main() -> int:
    manifest = generate()
    summary = manifest["customer_business_analysis_summary"]
    print(
        "PASS: KMFA v0.1.4 S16-P3 customer business analysis generated "
        f"(source_lanes={summary['source_lane_count']}, "
        f"value_signals={summary['customer_value_signal_count']}, "
        f"risk_signals={summary['customer_risk_signal_count']}, "
        f"summaries={summary['customer_summary_count']}, "
        f"handoff_guards={summary['handoff_guard_count']}, "
        f"report_grade={summary['report_grade_visible']}, "
        f"collection_action={summary['collection_action_count']}, "
        f"legal_decision={summary['legal_collection_decision_count']}, "
        f"next_phase={manifest['next_phase']}, "
        f"github_upload={manifest['github_upload']['github_upload_performed']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
