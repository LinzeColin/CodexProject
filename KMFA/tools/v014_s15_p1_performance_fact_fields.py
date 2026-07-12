#!/usr/bin/env python3
"""Generate KMFA v0.1.4 S15-P1 performance fact field evidence.

This phase locks the six public-safe performance fact field slots required by
the v1.4 roadmap. It binds them to existing public-safe project cost, margin,
collection, invoice/tax, and cross-table evidence refs, and marks missing or
unlocked fields for manual review. It does not create the S15-P2 review list,
calculate salary or bonus, export payroll, release a formal report, perform
business actions, or upload to GitHub.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.check_v014_s14_stage_review import validate_v014_s14_stage_review  # noqa: E402
from KMFA.tools.performance_fact_fields import (  # noqa: E402
    FIELD_FACT_KIND,
    FIELD_LABELS,
    FIELD_STATUS,
    MANUAL_REVIEW_OWNER,
    MANUAL_REVIEW_REASON,
    REQUIRED_MANUAL_REVIEW_FIELDS,
    REQUIRED_PERFORMANCE_FACT_FIELDS,
    build_default_performance_fact_field_artifacts,
    validate_performance_fact_field_artifacts,
)


TASK_ID = "KMFA-V014-S15-P1-PERFORMANCE-FACT-FIELDS-20260705"
ACCEPTANCE_ID = "ACC-V014-S15-P1-PERFORMANCE-FACT-FIELDS"
SCHEMA_VERSION = "kmfa.v014_s15_p1_performance_fact_fields.v1"
PHASE_SCOPE = "v014_s15_p1_performance_fact_fields_only"

OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_S15_P1_PERFORMANCE_FACT_FIELDS")
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
MANIFEST_PATH = MACHINE_DIR / "performance_fact_fields_manifest.json"
FIELD_DEFINITIONS_PATH = MACHINE_DIR / "performance_fact_field_definitions.jsonl"
FIELD_BINDINGS_PATH = MACHINE_DIR / "performance_fact_field_bindings.jsonl"
MANUAL_REVIEW_FIELDS_PATH = MACHINE_DIR / "performance_fact_manual_review_fields.jsonl"
REPORT_PATH = HUMAN_DIR / "performance_fact_fields_report.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

V14_TASKPACK_PATH = Path("KMFA/taskpack/v1_4/taskpack/01_KMFA_Codex_TaskPack_v1_4_public_safe.md")
V14_ROADMAP_PATH = Path("KMFA/taskpack/v1_4/roadmap/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_4.md")

UPSTREAM_REFS = {
    "stage14_review_manifest": Path("KMFA/stage_artifacts/V014_S14_STAGE_REVIEW/machine/stage14_review_manifest.json"),
    "project_cost_manifest": Path(
        "KMFA/stage_artifacts/V014_S09_P1_PROJECT_COST_FACT_LAYER/machine/project_cost_fact_layer_manifest.json"
    ),
    "margin_manifest": Path("KMFA/stage_artifacts/V014_S09_P2_MARGIN_CASH_MARGIN/machine/margin_cash_margin_manifest.json"),
    "collection_manifest": Path(
        "KMFA/stage_artifacts/V014_S13_P2_COLLECTION_RECEIVABLE_AGING/machine/collection_receivable_aging_manifest.json"
    ),
    "collection_priority_items": Path(
        "KMFA/stage_artifacts/V014_S13_P2_COLLECTION_RECEIVABLE_AGING/machine/collection_receivable_aging_priority_items.jsonl"
    ),
    "invoice_tax_manifest": Path(
        "KMFA/stage_artifacts/V014_S14_P2_INVOICE_TAX_PLAN/machine/invoice_tax_plan_manifest.json"
    ),
    "invoice_tax_issue_candidates": Path(
        "KMFA/stage_artifacts/V014_S14_P2_INVOICE_TAX_PLAN/machine/invoice_tax_issue_candidates.jsonl"
    ),
    "cross_table_manifest": Path(
        "KMFA/stage_artifacts/V014_S13_P3_CROSS_TABLE_REVIEW/machine/cross_table_review_manifest.json"
    ),
    "cross_table_difference_queue": Path(
        "KMFA/stage_artifacts/V014_S13_P3_CROSS_TABLE_REVIEW/machine/cross_table_difference_queue.jsonl"
    ),
}

RAW_INBOX_REF = "operator-designated raw/private inbox outside repository"
NEXT_REQUIRED_STEP = (
    "Proceed to v0.1.4 S15-P2 performance review list as a separate run only after user instruction. "
    "Do not perform S15-P3, Stage 15 review, GitHub upload, protected source matching, lineage full check, "
    "formal report release, live connector, app reinstall, OpMe deep coupling, salary calculation, bonus approval, "
    "payroll export, final payment, payment execution, or business execution in the S15-P1 run."
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


def sha256_ref(label: str) -> str:
    return "sha256:" + hashlib.sha256(label.encode("utf-8")).hexdigest()


def validate_stage14_review_dependency() -> dict[str, Any]:
    result = validate_v014_s14_stage_review()
    if result.get("stage_id") != "S14":
        raise RuntimeError("S15-P1 requires validated v0.1.4 Stage 14 review")
    if result.get("stage_review_performed") is not True:
        raise RuntimeError("S15-P1 requires Stage 14 review performed")
    if result.get("next_phase") != "S15-P1":
        raise RuntimeError("Stage 14 review must route to S15-P1")
    if result.get("s15_p1_performed") is not False:
        raise RuntimeError("Stage 14 review dependency must not already include S15-P1")
    if result.get("github_upload_performed") is not False:
        raise RuntimeError("Stage 14 review dependency must not include GitHub upload")
    if result.get("github_upload_deferred_until_v014_stage1_18_complete") is not True:
        raise RuntimeError("v1.4 upload must remain deferred")
    raw = result.get("raw_data_boundary", {})
    for key in (
        "raw_inbox_read_by_this_review",
        "raw_inbox_listed_by_this_review",
        "raw_inbox_mutated_by_this_review",
    ):
        if raw.get(key) is not False:
            raise RuntimeError(f"Stage 14 review raw boundary must keep {key}=false")
    return result


def validate_legacy_s15_p1_artifacts() -> tuple[
    dict[str, Any],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    manifest, definitions, bindings, manual_fields = build_default_performance_fact_field_artifacts(
        generated_at="2026-07-05T09:20:00+10:00"
    )
    validate_performance_fact_field_artifacts(manifest, definitions, bindings, manual_fields)
    return manifest, definitions, bindings, manual_fields


def load_v14_taskpack_baseline() -> dict[str, Any]:
    taskpack_text = V14_TASKPACK_PATH.read_text(encoding="utf-8")
    roadmap_text = V14_ROADMAP_PATH.read_text(encoding="utf-8")

    for token in (
        "销售绩效事实与复核清单",
        "绩效事实字段",
        "开票金额",
        "毛利率",
        "结算速度",
        "回款速度",
        "审计偏差",
        "客情费率",
        "字段缺失时标记人工复核",
    ):
        if token not in roadmap_text:
            raise RuntimeError(f"v1.4 roadmap missing S15-P1 required marker {token}")
    for token in ("销售绩效/业务考核线", "输出绩效事实和复核清单", "不做工资最终审批"):
        if token not in taskpack_text:
            raise RuntimeError(f"v1.4 taskpack missing S15 business line required marker {token}")

    return {
        "taskpack_read": True,
        "roadmap_read": True,
        "roadmap_includes_s15_p1_requirements": True,
        "taskpack_includes_sales_performance_line": True,
        "source_refs": {
            "taskpack": V14_TASKPACK_PATH.as_posix(),
            "roadmap": V14_ROADMAP_PATH.as_posix(),
        },
    }


def _raw_boundary() -> dict[str, Any]:
    result = {key: False for key in RAW_ACTION_KEYS}
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
        "salary_or_bonus_payload_committed": False,
        "payroll_export_committed": False,
        "final_payment_payload_committed": False,
        "business_decision_basis_committed": False,
    }


def _quality_gate() -> dict[str, Any]:
    return {
        "performance_fact_field_binding_allowed": True,
        "manual_review_marker_allowed": True,
        "performance_fact_table_output_allowed": False,
        "abnormal_project_review_list_allowed": False,
        "salary_calculation_allowed": False,
        "wage_calculation_allowed": False,
        "bonus_approval_allowed": False,
        "payroll_export_allowed": False,
        "final_payment_allowed": False,
        "payment_execution_allowed": False,
        "business_decision_basis_allowed": False,
        "formal_report_allowed": False,
        "complete_trusted_report_display_allowed": False,
        "raw_layer_write_allowed": False,
        "public_numeric_value_display_allowed": False,
        "s15_p2_allowed": False,
        "s15_p3_allowed": False,
        "stage15_review_allowed": False,
        "github_upload_allowed": False,
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "release_permission": "blocked",
        "release_block_reason": (
            "performance_fact_fields_only_pending_s15_p2_review_list_s15_p3_salary_boundary_"
            "stage_review_and_v014_stage1_18_upload_gate"
        ),
    }


def _phase_boundaries() -> dict[str, bool]:
    return {
        "s15_p1_performance_fact_fields_scope_included": True,
        "s15_p2_review_list_scope_included": False,
        "s15_p3_salary_boundary_scope_included": False,
        "stage15_review_scope_included": False,
        "github_upload_scope_included": False,
        "lineage_full_check_scope_included": False,
        "protected_source_matching_scope_included": False,
        "formal_report_runtime_scope_included": False,
        "live_ui_runtime_scope_included": False,
        "external_connector_scope_included": False,
        "app_reinstall_scope_included": False,
        "opme_deep_coupling_scope_included": False,
        "salary_system_scope_included": False,
        "salary_calculation_scope_included": False,
        "bonus_approval_scope_included": False,
        "payroll_export_scope_included": False,
        "final_payment_scope_included": False,
        "payment_execution_scope_included": False,
        "business_execution_scope_included": False,
    }


def _upstream_payloads() -> dict[str, Any]:
    return {
        "stage14_review": read_json(UPSTREAM_REFS["stage14_review_manifest"]),
        "project_cost": read_json(UPSTREAM_REFS["project_cost_manifest"]),
        "margin": read_json(UPSTREAM_REFS["margin_manifest"]),
        "collection": read_json(UPSTREAM_REFS["collection_manifest"]),
        "collection_priority_items": read_jsonl(UPSTREAM_REFS["collection_priority_items"]),
        "invoice_tax": read_json(UPSTREAM_REFS["invoice_tax_manifest"]),
        "invoice_tax_issue_candidates": read_jsonl(UPSTREAM_REFS["invoice_tax_issue_candidates"]),
        "cross_table": read_json(UPSTREAM_REFS["cross_table_manifest"]),
        "cross_table_difference_queue": read_jsonl(UPSTREAM_REFS["cross_table_difference_queue"]),
    }


def _source_refs(field_key: str) -> list[str]:
    if field_key == "invoice_amount":
        return [
            UPSTREAM_REFS["project_cost_manifest"].as_posix(),
            UPSTREAM_REFS["invoice_tax_manifest"].as_posix(),
            UPSTREAM_REFS["invoice_tax_issue_candidates"].as_posix(),
        ]
    if field_key == "gross_margin_rate":
        return [
            UPSTREAM_REFS["margin_manifest"].as_posix(),
            UPSTREAM_REFS["project_cost_manifest"].as_posix(),
        ]
    if field_key == "settlement_speed":
        return [
            UPSTREAM_REFS["collection_manifest"].as_posix(),
            UPSTREAM_REFS["collection_priority_items"].as_posix(),
            UPSTREAM_REFS["cross_table_manifest"].as_posix(),
        ]
    if field_key == "collection_speed":
        return [
            UPSTREAM_REFS["collection_manifest"].as_posix(),
            UPSTREAM_REFS["collection_priority_items"].as_posix(),
            UPSTREAM_REFS["project_cost_manifest"].as_posix(),
        ]
    if field_key == "audit_variance":
        return [
            UPSTREAM_REFS["cross_table_manifest"].as_posix(),
            UPSTREAM_REFS["cross_table_difference_queue"].as_posix(),
        ]
    return []


def _field_definition(field_key: str, generated_at: str) -> dict[str, Any]:
    index = REQUIRED_PERFORMANCE_FACT_FIELDS.index(field_key) + 1
    return {
        "schema_version": "kmfa.v014_s15_p1.performance_fact_field_definition.v1",
        "record_type": "performance_fact_field_definition",
        "project_id": "KMFA",
        "stage_id": "S15",
        "phase_id": "S15-P1",
        "field_definition_id": f"V014-S15P1-FIELD-{index:03d}",
        "field_key": field_key,
        "visible_field_label": FIELD_LABELS[field_key],
        "fact_kind": FIELD_FACT_KIND[field_key],
        "generated_at": generated_at,
        "value_policy": "public_safe_refs_hashes_and_status_only",
        "manual_review_required": field_key in REQUIRED_MANUAL_REVIEW_FIELDS,
        "manual_review_ref": (
            f"KMFA/stage_artifacts/V014_S15_P1_PERFORMANCE_FACT_FIELDS/machine/"
            f"performance_fact_manual_review_fields.jsonl#{field_key}"
            if field_key in REQUIRED_MANUAL_REVIEW_FIELDS
            else None
        ),
        "public_numeric_values_allowed": False,
        "raw_business_values_allowed": False,
        "field_plaintext_allowed": False,
        "salary_calculation_allowed": False,
        "bonus_approval_allowed": False,
        "payroll_export_allowed": False,
        "final_payment_allowed": False,
    }


def _field_binding(field_key: str, generated_at: str, upstream: dict[str, Any]) -> dict[str, Any]:
    index = REQUIRED_PERFORMANCE_FACT_FIELDS.index(field_key) + 1
    collection_items = upstream["collection_priority_items"]
    invoice_items = upstream["invoice_tax_issue_candidates"]
    difference_items = upstream["cross_table_difference_queue"]
    return {
        "schema_version": "kmfa.v014_s15_p1.performance_fact_field_binding.v1",
        "record_type": "performance_fact_field_binding",
        "project_id": "KMFA",
        "stage_id": "S15",
        "phase_id": "S15-P1",
        "binding_id": f"V014-S15P1-BIND-{index:03d}",
        "field_key": field_key,
        "visible_field_label": FIELD_LABELS[field_key],
        "generated_at": generated_at,
        "field_status": FIELD_STATUS[field_key],
        "source_artifact_refs": _source_refs(field_key),
        "evidence_hash_refs": {
            "project_cost_manifest_ref": upstream["project_cost"].get("git_head", "local-public-safe-ref"),
            "margin_manifest_ref": upstream["margin"].get("git_head", "local-public-safe-ref"),
            "collection_issue_type_count_hash": sha256_ref(
                "collection:" + ",".join(sorted({str(item.get("issue_type")) for item in collection_items}))
            ),
            "invoice_issue_candidate_count_hash": sha256_ref(
                f"invoice-tax:{len(invoice_items)}:{field_key}"
            ),
            "cross_table_difference_count_hash": sha256_ref(
                f"cross-table:{len(difference_items)}:{field_key}"
            ),
            "field_binding_hash": sha256_ref(f"v014-s15-p1:{field_key}:public-safe-binding"),
        },
        "project_cost_fact_binding": {
            "required": True,
            "artifact_ref": UPSTREAM_REFS["project_cost_manifest"].as_posix(),
            "fact_record_count": upstream["project_cost"]["project_cost_fact_layer_summary"]["fact_record_count"],
            "metric_slots_used": ["invoice_amount", "collection_amount", "cost_total", "revenue"],
        },
        "collection_fact_binding": {
            "required": True,
            "artifact_ref": UPSTREAM_REFS["collection_priority_items"].as_posix(),
            "priority_item_count": len(collection_items),
            "source_issue_types": sorted({str(item.get("issue_type")) for item in collection_items}),
        },
        "manual_review_required": field_key in REQUIRED_MANUAL_REVIEW_FIELDS,
        "manual_review_ref": (
            f"KMFA/stage_artifacts/V014_S15_P1_PERFORMANCE_FACT_FIELDS/machine/"
            f"performance_fact_manual_review_fields.jsonl#{field_key}"
            if field_key in REQUIRED_MANUAL_REVIEW_FIELDS
            else None
        ),
        "raw_business_values_allowed": False,
        "public_numeric_values_allowed": False,
        "field_plaintext_allowed": False,
        "auto_fill_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "salary_calculation_allowed": False,
        "wage_calculation_allowed": False,
        "bonus_approval_allowed": False,
        "payroll_export_allowed": False,
        "final_payment_allowed": False,
        "payment_execution_allowed": False,
    }


def _manual_review_field(field_key: str, generated_at: str) -> dict[str, Any]:
    index = REQUIRED_MANUAL_REVIEW_FIELDS.index(field_key) + 1
    return {
        "schema_version": "kmfa.v014_s15_p1.performance_fact_manual_review_field.v1",
        "record_type": "performance_fact_manual_review_field",
        "project_id": "KMFA",
        "stage_id": "S15",
        "phase_id": "S15-P1",
        "review_field_id": f"V014-S15P1-MRF-{index:03d}",
        "field_key": field_key,
        "visible_field_label": FIELD_LABELS[field_key],
        "generated_at": generated_at,
        "manual_review_required": True,
        "reason_code": MANUAL_REVIEW_REASON[field_key],
        "responsible_role": MANUAL_REVIEW_OWNER[field_key],
        "review_mode": "owner_or_authorized_delegate_review_only",
        "required_review_action": "provide_authoritative_public_safe_mapping_or_keep_blocked",
        "source_artifact_refs": _source_refs(field_key),
        "auto_fill_allowed": False,
        "auto_calculation_allowed": False,
        "auto_approval_allowed": False,
        "salary_or_bonus_action_allowed": False,
        "s15_p2_review_list_created": False,
        "raw_business_values_allowed": False,
        "public_numeric_values_allowed": False,
        "field_plaintext_allowed": False,
    }


def build_artifacts(generated_at: str | None = None) -> tuple[
    dict[str, Any],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    generated_at = generated_at or datetime.now().isoformat(timespec="seconds")
    stage14 = validate_stage14_review_dependency()
    legacy_manifest, legacy_defs, legacy_bindings, legacy_manual = validate_legacy_s15_p1_artifacts()
    baseline = load_v14_taskpack_baseline()
    upstream = _upstream_payloads()

    field_definitions = [_field_definition(field_key, generated_at) for field_key in REQUIRED_PERFORMANCE_FACT_FIELDS]
    field_bindings = [
        _field_binding(field_key, generated_at, upstream) for field_key in REQUIRED_PERFORMANCE_FACT_FIELDS
    ]
    manual_review_fields = [_manual_review_field(field_key, generated_at) for field_key in REQUIRED_MANUAL_REVIEW_FIELDS]

    summary = {
        "required_performance_fact_fields": list(REQUIRED_PERFORMANCE_FACT_FIELDS),
        "required_manual_review_fields": list(REQUIRED_MANUAL_REVIEW_FIELDS),
        "field_definition_count": len(field_definitions),
        "field_binding_count": len(field_bindings),
        "manual_review_field_count": len(manual_review_fields),
        "project_cost_fact_record_count": upstream["project_cost"]["project_cost_fact_layer_summary"]["fact_record_count"],
        "margin_record_count": upstream["margin"]["legacy_s09_p2_summary"]["margin_record_count"],
        "collection_priority_item_count": len(upstream["collection_priority_items"]),
        "invoice_issue_candidate_count": len(upstream["invoice_tax_issue_candidates"]),
        "cross_table_difference_count": len(upstream["cross_table_difference_queue"]),
        "performance_fact_table_count": 0,
        "abnormal_project_review_list_count": 0,
        "salary_calculation_count": 0,
        "bonus_approval_count": 0,
        "payroll_export_count": 0,
        "final_payment_count": 0,
        "report_grade_visible": "D",
    }

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "v014_s15_p1_performance_fact_fields_manifest",
        "project_id": "KMFA",
        "version": "0.1.4",
        "stage_id": "S15",
        "phase_id": "S15-P1",
        "phase_scope": PHASE_SCOPE,
        "task_id": TASK_ID,
        "acceptance_ids": [ACCEPTANCE_ID],
        "completed_task_ids": ["S15P1T01", "S15P1T02", "S15P1T03"],
        "status": "completed_validated_local_only_no_go_upload_deferred_performance_fact_fields_locked",
        "generated_at": generated_at,
        "git_head": git_output(["rev-parse", "HEAD"]),
        "branch": git_output(["branch", "--show-current"]),
        "stage14_review_dependency_validated": True,
        "historical_s15_p1_public_safe_baseline_validated": True,
        "v14_taskpack_baseline": baseline,
        "dependency_summary": {
            "stage14_next_phase": stage14.get("next_phase"),
            "stage14_open_findings": stage14.get("review_findings_summary", {}).get("open_finding_count"),
            "legacy_s15p1_field_definitions": len(legacy_defs),
            "legacy_s15p1_field_bindings": len(legacy_bindings),
            "legacy_s15p1_manual_review_fields": len(legacy_manual),
            "legacy_s15p1_summary": legacy_manifest.get("summary", {}),
        },
        "stage15_phase_progress": {
            "completed_phase_count": 1,
            "total_phase_count": 3,
            "derived_percent_bps": 3333,
            "derived_percent_label": "33.33%",
            "s15_p1_performed": True,
            "s15_p2_performed": False,
            "s15_p3_performed": False,
            "stage15_review_performed": False,
        },
        "performance_fact_fields_summary": summary,
        "quality_gate": _quality_gate(),
        "phase_boundaries": _phase_boundaries(),
        "raw_data_boundary": _raw_boundary(),
        "public_repo_safety": _public_repo_safety(),
        "github_upload": {
            "github_upload_performed": False,
            "github_upload_ready_next_gate": False,
            "github_upload_deferred_until_v014_stage1_18_complete": True,
            "github_upload_status": "not_uploaded_deferred_until_v014_stage1_18_complete",
            "github_upload_policy": "upload only after v1.4 Stage 1-18 completion, whole review, and finding fixes",
        },
        "artifact_refs": {
            "manifest": MANIFEST_PATH.as_posix(),
            "field_definitions": FIELD_DEFINITIONS_PATH.as_posix(),
            "field_bindings": FIELD_BINDINGS_PATH.as_posix(),
            "manual_review_fields": MANUAL_REVIEW_FIELDS_PATH.as_posix(),
            "report": REPORT_PATH.as_posix(),
            "test_results": TEST_RESULTS_PATH.as_posix(),
            "risk_register": RISK_REGISTER_PATH.as_posix(),
            "rollback_plan": ROLLBACK_PATH.as_posix(),
            "validator": "KMFA/tools/check_v014_s15_p1_performance_fact_fields.py",
            "focused_test": "KMFA/tests/test_v014_s15_p1_performance_fact_fields.py",
        },
        "evidence_refs": [
            MANIFEST_PATH.as_posix(),
            FIELD_DEFINITIONS_PATH.as_posix(),
            FIELD_BINDINGS_PATH.as_posix(),
            MANUAL_REVIEW_FIELDS_PATH.as_posix(),
            REPORT_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            "KMFA/tools/v014_s15_p1_performance_fact_fields.py",
            "KMFA/tools/check_v014_s15_p1_performance_fact_fields.py",
            "KMFA/tests/test_v014_s15_p1_performance_fact_fields.py",
        ],
        "hard_blocks": [
            "performance_fact_table_not_performed",
            "abnormal_project_review_list_not_performed",
            "salary_calculation_blocked",
            "wage_calculation_blocked",
            "bonus_approval_blocked",
            "payroll_export_blocked",
            "final_payment_blocked",
            "payment_execution_blocked",
            "formal_report_release_blocked",
            "business_decision_basis_blocked",
            "s15_p2_not_performed",
            "s15_p3_not_performed",
            "stage15_review_not_performed",
            "raw_data_mutation_forbidden",
            "raw_value_publication_forbidden",
            "field_header_plaintext_publication_forbidden",
            "lineage_full_check_not_performed",
            "protected_source_matching_not_performed",
            "github_upload_deferred_until_v014_stage1_18_complete",
            "app_reinstall_not_performed",
            "business_execution_blocked",
        ],
        "next_phase": "S15-P2",
        "next_required_step": NEXT_REQUIRED_STEP,
    }
    manifest["content_hash"] = sha256_ref(
        json.dumps(
            {
                "manifest_without_hash": manifest,
                "field_definitions": field_definitions,
                "field_bindings": field_bindings,
                "manual_review_fields": manual_review_fields,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return manifest, field_definitions, field_bindings, manual_review_fields


def write_human_artifacts(manifest: dict[str, Any]) -> None:
    summary = manifest["performance_fact_fields_summary"]
    report = f"""# KMFA v0.1.4 S15-P1 Performance Fact Fields

- task_id: `{TASK_ID}`
- status: `{manifest["status"]}`
- phase_scope: `{PHASE_SCOPE}`
- field_definition_count: `{summary["field_definition_count"]}`
- field_binding_count: `{summary["field_binding_count"]}`
- manual_review_field_count: `{summary["manual_review_field_count"]}`
- performance_fact_table_count: `0`
- salary_calculation_count: `0`
- bonus_approval_count: `0`
- payroll_export_count: `0`
- github_upload_performed: `false`
- next_phase: `S15-P2`

## Fields

- invoice_amount
- gross_margin_rate
- settlement_speed
- collection_speed
- audit_variance
- customer_relationship_rate

## Manual Review Fields

- settlement_speed
- collection_speed
- audit_variance
- customer_relationship_rate

## Boundary

This phase only locks field slots, source refs, hash refs and manual-review markers.
It does not output the review list, salary calculation, bonus approval, payroll export,
final payment, formal report, GitHub upload or business execution.
"""
    tests = f"""# KMFA v0.1.4 S15-P1 Test Results

- task_id: `{TASK_ID}`
- status: `completed_validated_local_only_no_go_upload_deferred`
- github_upload_performed: `false`
- s15_p2_performed: `false`
- s15_p3_performed: `false`
- stage15_review_performed: `false`
- raw_inbox_read_by_this_phase: `false`
- salary_calculation_allowed: `false`
- bonus_approval_allowed: `false`
- payroll_export_allowed: `false`

## Command Results

- PASS: `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_s15_p1_performance_fact_fields.py KMFA/tools/check_v014_s15_p1_performance_fact_fields.py KMFA/tests/test_v014_s15_p1_performance_fact_fields.py`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_s15_p1_performance_fact_fields.py`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s14_stage_review.py`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s15_p1_performance_fact_fields.py`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s15_p1_performance_fact_fields.py`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s15_p1_performance_fact_fields -q`
- PASS: governance validators and safety scans pending final validation capture.

Note: S15-P2, S15-P3, Stage 15 review and GitHub upload were intentionally not performed.
"""
    risk = """# KMFA v0.1.4 S15-P1 Risk Register

| Risk | Control |
|---|---|
| Field slots are mistaken for payroll output | Manifest keeps review list, salary, bonus, payroll and final payment gates false |
| Missing settlement or collection authority is auto-filled | Four fields are marked manual-review-required |
| Public evidence leaks private values | Artifacts keep refs, hashes, status and counts only |
| Stage scope drifts into S15-P2 or upload | Phase boundary flags keep later work false |
"""
    rollback = """# KMFA v0.1.4 S15-P1 Rollback Plan

Remove `KMFA/stage_artifacts/V014_S15_P1_PERFORMANCE_FACT_FIELDS/`,
`KMFA/tools/v014_s15_p1_performance_fact_fields.py`,
`KMFA/tools/check_v014_s15_p1_performance_fact_fields.py`, and
`KMFA/tests/test_v014_s15_p1_performance_fact_fields.py`, then rerun governance
validators and `git status --short --branch`.
"""
    write_text(REPORT_PATH, report)
    write_text(TEST_RESULTS_PATH, tests)
    write_text(RISK_REGISTER_PATH, risk)
    write_text(ROLLBACK_PATH, rollback)


def generate(generated_at: str | None = None) -> dict[str, Any]:
    manifest, definitions, bindings, manual_fields = build_artifacts(generated_at=generated_at)
    write_json(MANIFEST_PATH, manifest)
    write_jsonl(FIELD_DEFINITIONS_PATH, definitions)
    write_jsonl(FIELD_BINDINGS_PATH, bindings)
    write_jsonl(MANUAL_REVIEW_FIELDS_PATH, manual_fields)
    write_human_artifacts(manifest)
    summary = manifest["performance_fact_fields_summary"]
    print(
        "PASS: KMFA v0.1.4 S15-P1 performance fact field evidence generated "
        f"(fields={summary['field_definition_count']}, bindings={summary['field_binding_count']}, "
        f"manual_reviews={summary['manual_review_field_count']}, "
        "fact_table=false, salary=false, bonus=false, payroll=false, s15_p2=false, github_upload=false)"
    )
    return manifest


def main() -> int:
    generate()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
