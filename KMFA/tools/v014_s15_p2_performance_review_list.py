#!/usr/bin/env python3
"""Generate KMFA v0.1.4 S15-P2 performance review list evidence.

This phase creates a public-safe performance fact table and abnormal review
list from the S15-P1 field lock. It keeps all values as refs, hashes, and
statuses only. It does not calculate salary, approve bonuses, export payroll,
create final compensation instructions, perform Stage 15 review, or upload.
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

from KMFA.tools.check_v014_s15_p1_performance_fact_fields import (  # noqa: E402
    validate_v014_s15_p1_performance_fact_fields,
)
from KMFA.tools.performance_review_list import (  # noqa: E402
    FIELD_LABELS,
    FIELD_STATUS,
    REQUIRED_MANUAL_REVIEW_FIELDS,
    REQUIRED_PERFORMANCE_REVIEW_FIELDS,
    build_default_performance_review_list_artifacts,
    validate_performance_review_list_artifacts,
)


TASK_ID = "KMFA-V014-S15-P2-PERFORMANCE-REVIEW-LIST-20260705"
ACCEPTANCE_ID = "ACC-V014-S15-P2-PERFORMANCE-REVIEW-LIST"
SCHEMA_VERSION = "kmfa.v014_s15_p2_performance_review_list.v1"
PHASE_SCOPE = "v014_s15_p2_performance_review_list_only"

OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_S15_P2_PERFORMANCE_REVIEW_LIST")
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
MANIFEST_PATH = MACHINE_DIR / "performance_review_manifest.json"
FACT_TABLE_PATH = MACHINE_DIR / "performance_fact_table.jsonl"
REVIEW_ITEMS_PATH = MACHINE_DIR / "performance_review_items.jsonl"
REPORT_PATH = HUMAN_DIR / "performance_review_list_report.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

V14_TASKPACK_PATH = Path("KMFA/taskpack/v1_4/taskpack/01_KMFA_Codex_TaskPack_v1_4_public_safe.md")
V14_ROADMAP_PATH = Path("KMFA/taskpack/v1_4/roadmap/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_4.md")

UPSTREAM_REFS = {
    "s15_p1_manifest": Path(
        "KMFA/stage_artifacts/V014_S15_P1_PERFORMANCE_FACT_FIELDS/machine/performance_fact_fields_manifest.json"
    ),
    "s15_p1_bindings": Path(
        "KMFA/stage_artifacts/V014_S15_P1_PERFORMANCE_FACT_FIELDS/machine/performance_fact_field_bindings.jsonl"
    ),
    "s15_p1_manual_fields": Path(
        "KMFA/stage_artifacts/V014_S15_P1_PERFORMANCE_FACT_FIELDS/machine/performance_fact_manual_review_fields.jsonl"
    ),
    "project_cost_manifest": Path(
        "KMFA/stage_artifacts/V014_S09_P1_PROJECT_COST_FACT_LAYER/machine/project_cost_fact_layer_manifest.json"
    ),
    "margin_manifest": Path("KMFA/stage_artifacts/V014_S09_P2_MARGIN_CASH_MARGIN/machine/margin_cash_margin_manifest.json"),
    "collection_priority_items": Path(
        "KMFA/stage_artifacts/V014_S13_P2_COLLECTION_RECEIVABLE_AGING/machine/collection_receivable_aging_priority_items.jsonl"
    ),
    "cross_table_difference_queue": Path(
        "KMFA/stage_artifacts/V014_S13_P3_CROSS_TABLE_REVIEW/machine/cross_table_difference_queue.jsonl"
    ),
}

RAW_INBOX_REF = "operator-designated raw/private inbox outside repository"
NEXT_REQUIRED_STEP = (
    "Proceed to v0.1.4 S15-P3 salary boundary as a separate run only after user instruction. "
    "Do not perform Stage 15 review, GitHub upload, protected source matching, lineage full check, "
    "formal report release, live connector, app reinstall, OpMe deep coupling, salary calculation, bonus approval, "
    "payroll export, final payment, payment execution, or business execution in the S15-P2 run."
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


def validate_s15_p1_dependency() -> dict[str, Any]:
    result = validate_v014_s15_p1_performance_fact_fields()
    if result.get("stage_id") != "S15" or result.get("phase_id") != "S15-P1":
        raise RuntimeError("S15-P2 requires validated v0.1.4 S15-P1 evidence")
    if result.get("next_phase") != "S15-P2":
        raise RuntimeError("S15-P1 must route to S15-P2")
    progress = result.get("stage15_phase_progress", {})
    if progress.get("s15_p1_performed") is not True:
        raise RuntimeError("S15-P1 dependency must be performed")
    if progress.get("s15_p2_performed") is not False:
        raise RuntimeError("S15-P1 dependency must not already include S15-P2")
    if progress.get("s15_p3_performed") is not False:
        raise RuntimeError("S15-P1 dependency must not include S15-P3")
    if result.get("github_upload", {}).get("github_upload_deferred_until_v014_stage1_18_complete") is not True:
        raise RuntimeError("v1.4 upload must remain deferred")
    raw = result.get("raw_data_boundary", {})
    for key in ("raw_inbox_read_by_this_phase", "raw_inbox_listed_by_this_phase", "raw_inbox_mutated_by_this_phase"):
        if raw.get(key) is not False:
            raise RuntimeError(f"S15-P1 raw boundary must keep {key}=false")
    return result


def validate_legacy_s15_p2_artifacts() -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    manifest, fact_rows, review_items = build_default_performance_review_list_artifacts(
        generated_at="2026-07-05T09:40:00+10:00"
    )
    validate_performance_review_list_artifacts(manifest, fact_rows, review_items)
    return manifest, fact_rows, review_items


def load_v14_taskpack_baseline() -> dict[str, Any]:
    taskpack_text = V14_TASKPACK_PATH.read_text(encoding="utf-8")
    roadmap_text = V14_ROADMAP_PATH.read_text(encoding="utf-8")

    for token in (
        "销售绩效事实与复核清单",
        "绩效复核清单",
        "输出绩效事实表",
        "输出异常项目和复核事项",
        "不计算最终工资",
        "不审批奖金",
    ):
        if token not in roadmap_text:
            raise RuntimeError(f"v1.4 roadmap missing S15-P2 required marker {token}")
    for token in ("销售绩效/业务考核线", "输出绩效事实和复核清单", "不做工资最终审批"):
        if token not in taskpack_text:
            raise RuntimeError(f"v1.4 taskpack missing S15 business line required marker {token}")

    return {
        "taskpack_read": True,
        "roadmap_read": True,
        "roadmap_includes_s15_p2_requirements": True,
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
        "performance_fact_table_output_allowed": True,
        "abnormal_project_review_list_allowed": True,
        "review_item_output_allowed": True,
        "manual_review_required_before_compensation_use": True,
        "salary_calculation_allowed": False,
        "wage_calculation_allowed": False,
        "bonus_approval_allowed": False,
        "payroll_export_allowed": False,
        "final_compensation_decision_allowed": False,
        "final_payment_allowed": False,
        "payment_execution_allowed": False,
        "business_decision_basis_allowed": False,
        "formal_report_allowed": False,
        "complete_trusted_report_display_allowed": False,
        "raw_layer_write_allowed": False,
        "public_numeric_value_display_allowed": False,
        "s15_p3_allowed": False,
        "stage15_review_allowed": False,
        "github_upload_allowed": False,
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "release_permission": "blocked",
        "release_block_reason": (
            "performance_review_list_only_pending_s15_p3_salary_boundary_stage_review_"
            "and_v014_stage1_18_upload_gate"
        ),
    }


def _phase_boundaries() -> dict[str, bool]:
    return {
        "s15_p1_dependency_reused": True,
        "s15_p2_review_list_scope_included": True,
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
        "final_compensation_scope_included": False,
        "final_payment_scope_included": False,
        "payment_execution_scope_included": False,
        "business_execution_scope_included": False,
    }


def _upstream_payloads() -> dict[str, Any]:
    return {
        "s15_p1_manifest": read_json(UPSTREAM_REFS["s15_p1_manifest"]),
        "s15_p1_bindings": read_jsonl(UPSTREAM_REFS["s15_p1_bindings"]),
        "s15_p1_manual_fields": read_jsonl(UPSTREAM_REFS["s15_p1_manual_fields"]),
        "project_cost": read_json(UPSTREAM_REFS["project_cost_manifest"]),
        "margin": read_json(UPSTREAM_REFS["margin_manifest"]),
        "collection_priority_items": read_jsonl(UPSTREAM_REFS["collection_priority_items"]),
        "cross_table_difference_queue": read_jsonl(UPSTREAM_REFS["cross_table_difference_queue"]),
    }


def _validate_upstream_payloads(upstream: dict[str, Any]) -> None:
    s15_p1 = upstream["s15_p1_manifest"]
    if s15_p1.get("phase_id") != "S15-P1":
        raise RuntimeError("S15-P2 requires S15-P1 manifest")
    if s15_p1.get("next_phase") != "S15-P2":
        raise RuntimeError("S15-P1 manifest must route to S15-P2")
    if [row.get("field_key") for row in upstream["s15_p1_bindings"]] != list(REQUIRED_PERFORMANCE_REVIEW_FIELDS):
        raise RuntimeError("S15-P2 requires all S15-P1 field bindings")
    if [row.get("field_key") for row in upstream["s15_p1_manual_fields"]] != list(REQUIRED_MANUAL_REVIEW_FIELDS):
        raise RuntimeError("S15-P2 requires all S15-P1 manual review fields")
    if upstream["project_cost"]["project_cost_fact_layer_summary"].get("fact_record_count") != 4:
        raise RuntimeError("S15-P2 requires four public-safe project cost fact records")
    if upstream["margin"]["legacy_s09_p2_summary"].get("margin_record_count") != 4:
        raise RuntimeError("S15-P2 requires four public-safe margin records")
    if len(upstream["collection_priority_items"]) != 4:
        raise RuntimeError("S15-P2 requires four collection priority items")
    if len(upstream["cross_table_difference_queue"]) != 4:
        raise RuntimeError("S15-P2 requires four cross-table difference queue items")


def _public_project_ref(index: int, collection_item: dict[str, Any]) -> str:
    ref = collection_item.get("project_group_ref")
    if isinstance(ref, str) and ref.startswith("public_project_group_ref_"):
        return ref
    return f"public_project_group_ref_{index:03d}"


def _fact_row(index: int, generated_at: str, upstream: dict[str, Any]) -> dict[str, Any]:
    bindings = {str(row["field_key"]): row for row in upstream["s15_p1_bindings"]}
    collection_item = upstream["collection_priority_items"][index - 1]
    row_id = f"V014-S15P2-FACT-{index:03d}"
    return {
        "schema_version": "kmfa.v014_s15_p2.performance_fact_table_row.v1",
        "record_type": "performance_fact_table_row",
        "project_id": "KMFA",
        "stage_id": "S15",
        "phase_id": "S15-P2",
        "performance_fact_row_id": row_id,
        "generated_at": generated_at,
        "project_ref": _public_project_ref(index, collection_item),
        "fact_status_by_field": {field_key: FIELD_STATUS[field_key] for field_key in REQUIRED_PERFORMANCE_REVIEW_FIELDS},
        "fact_hash_refs_by_field": {
            "invoice_amount": sha256_ref(f"{row_id}:invoice_amount:public-safe-status"),
            "gross_margin_rate": sha256_ref(f"{row_id}:gross_margin_rate:public-safe-status"),
        },
        "manual_review_refs_by_field": {
            field_key: (
                "KMFA/stage_artifacts/V014_S15_P1_PERFORMANCE_FACT_FIELDS/machine/"
                f"performance_fact_manual_review_fields.jsonl#{field_key}"
            )
            for field_key in REQUIRED_MANUAL_REVIEW_FIELDS
        },
        "review_item_refs": [
            f"KMFA/stage_artifacts/V014_S15_P2_PERFORMANCE_REVIEW_LIST/machine/"
            f"performance_review_items.jsonl#V014-S15P2-REV-{((index - 1) * 4) + item_index:03d}"
            for item_index in range(1, 5)
        ],
        "evidence_refs": [
            UPSTREAM_REFS["s15_p1_manifest"].as_posix(),
            UPSTREAM_REFS["s15_p1_bindings"].as_posix(),
            UPSTREAM_REFS["project_cost_manifest"].as_posix(),
            UPSTREAM_REFS["margin_manifest"].as_posix(),
            UPSTREAM_REFS["collection_priority_items"].as_posix(),
            UPSTREAM_REFS["cross_table_difference_queue"].as_posix(),
        ],
        "field_binding_refs": {
            field_key: (
                "KMFA/stage_artifacts/V014_S15_P1_PERFORMANCE_FACT_FIELDS/machine/"
                f"performance_fact_field_bindings.jsonl#{bindings[field_key]['binding_id']}"
            )
            for field_key in REQUIRED_PERFORMANCE_REVIEW_FIELDS
        },
        "fact_table_value_policy": "public_safe_hash_refs_and_status_only_no_numeric_display",
        "review_status": "pending_owner_or_authorized_review_before_compensation_use",
        "report_grade_visible": "D",
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
        "payment_execution_allowed": False,
        "final_compensation_decision_allowed": False,
        "final_payment_allowed": False,
    }


def _review_item(
    index: int,
    fact_row: dict[str, Any],
    field_key: str,
    generated_at: str,
    upstream: dict[str, Any],
) -> dict[str, Any]:
    manual_fields = {str(row["field_key"]): row for row in upstream["s15_p1_manual_fields"]}
    collection_items = upstream["collection_priority_items"]
    difference_items = upstream["cross_table_difference_queue"]
    manual = manual_fields[field_key]
    collection_item = collection_items[(index - 1) % len(collection_items)]
    difference_item = difference_items[(index - 1) % len(difference_items)]
    item_id = f"V014-S15P2-REV-{index:03d}"
    return {
        "schema_version": "kmfa.v014_s15_p2.performance_review_item.v1",
        "record_type": "performance_review_item",
        "project_id": "KMFA",
        "stage_id": "S15",
        "phase_id": "S15-P2",
        "review_item_id": item_id,
        "generated_at": generated_at,
        "performance_fact_row_ref": (
            "KMFA/stage_artifacts/V014_S15_P2_PERFORMANCE_REVIEW_LIST/machine/"
            f"performance_fact_table.jsonl#{fact_row['performance_fact_row_id']}"
        ),
        "project_ref": fact_row["project_ref"],
        "field_key": field_key,
        "visible_field_label": FIELD_LABELS[field_key],
        "review_reason_code": str(manual.get("reason_code")),
        "abnormal_project_review_required": True,
        "abnormal_signal_ref": sha256_ref(f"{item_id}:{field_key}:review-signal"),
        "linked_collection_priority_ref": (
            "KMFA/stage_artifacts/V014_S13_P2_COLLECTION_RECEIVABLE_AGING/machine/"
            f"collection_receivable_aging_priority_items.jsonl#{collection_item.get('priority_item_id')}"
        ),
        "linked_cross_table_difference_ref": (
            "KMFA/stage_artifacts/V014_S13_P3_CROSS_TABLE_REVIEW/machine/"
            f"cross_table_difference_queue.jsonl#{difference_item.get('queue_item_id')}"
        ),
        "source_evidence_refs": [
            UPSTREAM_REFS["s15_p1_manual_fields"].as_posix(),
            UPSTREAM_REFS["collection_priority_items"].as_posix(),
            UPSTREAM_REFS["cross_table_difference_queue"].as_posix(),
        ],
        "review_owner_role": str(manual.get("responsible_role")),
        "review_mode": "owner_or_authorized_delegate_review_only",
        "required_review_action": str(manual.get("required_review_action")),
        "resolution_status": "pending_owner_or_authorized_review",
        "next_review_bucket": "next_internal_performance_review_cycle",
        "raw_business_values_allowed": False,
        "public_numeric_values_allowed": False,
        "field_plaintext_allowed": False,
        "auto_resolution_allowed": False,
        "auto_calculation_allowed": False,
        "auto_approval_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "salary_calculation_allowed": False,
        "wage_calculation_allowed": False,
        "bonus_approval_allowed": False,
        "payroll_export_allowed": False,
        "payment_execution_allowed": False,
        "final_compensation_decision_allowed": False,
        "final_payment_allowed": False,
    }


def build_artifacts(generated_at: str | None = None) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    generated_at = generated_at or datetime.now().isoformat(timespec="seconds")
    s15_p1 = validate_s15_p1_dependency()
    legacy_manifest, legacy_fact_rows, legacy_review_items = validate_legacy_s15_p2_artifacts()
    baseline = load_v14_taskpack_baseline()
    upstream = _upstream_payloads()
    _validate_upstream_payloads(upstream)

    fact_rows = [_fact_row(index, generated_at, upstream) for index in range(1, 5)]
    review_items: list[dict[str, Any]] = []
    for row_index, fact_row in enumerate(fact_rows):
        for field_index, field_key in enumerate(REQUIRED_MANUAL_REVIEW_FIELDS, start=1):
            review_items.append(
                _review_item(
                    (row_index * 4) + field_index,
                    fact_row,
                    field_key,
                    generated_at,
                    upstream,
                )
            )

    summary = {
        "required_review_fields": list(REQUIRED_PERFORMANCE_REVIEW_FIELDS),
        "required_manual_review_fields": list(REQUIRED_MANUAL_REVIEW_FIELDS),
        "performance_fact_row_count": len(fact_rows),
        "abnormal_review_item_count": len(review_items),
        "manual_review_field_count": len(REQUIRED_MANUAL_REVIEW_FIELDS),
        "project_cost_fact_record_count": upstream["project_cost"]["project_cost_fact_layer_summary"]["fact_record_count"],
        "margin_record_count": upstream["margin"]["legacy_s09_p2_summary"]["margin_record_count"],
        "collection_priority_item_count": len(upstream["collection_priority_items"]),
        "cross_table_difference_count": len(upstream["cross_table_difference_queue"]),
        "salary_calculation_count": 0,
        "wage_calculation_count": 0,
        "bonus_approval_count": 0,
        "payroll_export_count": 0,
        "final_compensation_decision_count": 0,
        "final_payment_count": 0,
        "report_grade_visible": "D",
    }
    manifest: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "v014_s15_p2_performance_review_manifest",
        "project_id": "KMFA",
        "version": "0.1.4",
        "stage_id": "S15",
        "phase_id": "S15-P2",
        "phase_scope": PHASE_SCOPE,
        "task_id": TASK_ID,
        "acceptance_ids": [ACCEPTANCE_ID],
        "completed_task_ids": ["S15P2T01", "S15P2T02", "S15P2T03"],
        "status": "completed_validated_local_only_no_go_upload_deferred_performance_review_list_created",
        "generated_at": generated_at,
        "branch": git_output(["branch", "--show-current"]),
        "git_head": git_output(["rev-parse", "HEAD"]),
        "s15_p1_dependency_validated": True,
        "historical_s15_p2_public_safe_baseline_validated": True,
        "v14_taskpack_baseline": baseline,
        "legacy_baseline_summary": {
            "stage_phase": legacy_manifest.get("stage_phase"),
            "performance_fact_row_count": len(legacy_fact_rows),
            "abnormal_review_item_count": len(legacy_review_items),
            "salary_calculation_count": legacy_manifest.get("summary", {}).get("salary_calculation_count"),
            "bonus_approval_count": legacy_manifest.get("summary", {}).get("bonus_approval_count"),
            "payroll_export_count": legacy_manifest.get("summary", {}).get("payroll_export_count"),
        },
        "upstream_refs": {key: path.as_posix() for key, path in UPSTREAM_REFS.items()},
        "stage15_phase_progress": {
            "completed_phase_count": 2,
            "total_phase_count": 3,
            "derived_percent_bps": 6667,
            "derived_percent_label": "66.67%",
            "s15_p1_performed": True,
            "s15_p2_performed": True,
            "s15_p3_performed": False,
            "stage15_review_performed": False,
        },
        "performance_review_summary": summary,
        "artifact_refs": {
            "manifest": MANIFEST_PATH.as_posix(),
            "performance_fact_table": FACT_TABLE_PATH.as_posix(),
            "performance_review_items": REVIEW_ITEMS_PATH.as_posix(),
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
            "salary_calculation_blocked",
            "wage_calculation_blocked",
            "bonus_approval_blocked",
            "payroll_export_blocked",
            "final_compensation_decision_blocked",
            "final_payment_blocked",
            "payment_execution_blocked",
            "s15_p3_not_performed",
            "stage15_review_not_performed",
            "github_upload_deferred_until_v014_stage1_18_complete",
            "business_execution_blocked",
        ],
        "s15_p1_dependency_status": {
            "task_id": s15_p1.get("task_id"),
            "status": s15_p1.get("status"),
            "next_phase": s15_p1.get("next_phase"),
        },
        "next_phase": "S15-P3",
        "next_required_step": NEXT_REQUIRED_STEP,
    }
    manifest["content_hash"] = sha256_ref(json.dumps([manifest, fact_rows, review_items], ensure_ascii=False, sort_keys=True))
    return manifest, fact_rows, review_items


def write_outputs(manifest: dict[str, Any], fact_rows: list[dict[str, Any]], review_items: list[dict[str, Any]]) -> None:
    write_json(MANIFEST_PATH, manifest)
    write_jsonl(FACT_TABLE_PATH, fact_rows)
    write_jsonl(REVIEW_ITEMS_PATH, review_items)
    summary = manifest["performance_review_summary"]
    write_text(
        REPORT_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 S15-P2 Performance Review List",
                "",
                f"- task_id: `{TASK_ID}`",
                "- status: `completed_validated_local_only_no_go_upload_deferred_performance_review_list_created`",
                "- scope: public-safe performance fact table and abnormal review items only",
                f"- performance_fact_rows: `{summary['performance_fact_row_count']}`",
                f"- abnormal_review_items: `{summary['abnormal_review_item_count']}`",
                f"- manual_review_fields: `{summary['manual_review_field_count']}`",
                "- salary_calculation_allowed: `false`",
                "- wage_calculation_allowed: `false`",
                "- bonus_approval_allowed: `false`",
                "- payroll_export_allowed: `false`",
                "- final_compensation_decision_allowed: `false`",
                "- payment_execution_allowed: `false`",
                "- current_report_grade: `D`",
                "- next_phase: `S15-P3`",
                "- github_upload: `not_uploaded_deferred_until_v014_stage1_18_complete`",
                "",
                "## Evidence",
                "",
                f"- `{MANIFEST_PATH.as_posix()}`",
                f"- `{FACT_TABLE_PATH.as_posix()}`",
                f"- `{REVIEW_ITEMS_PATH.as_posix()}`",
                "",
                "## Boundary",
                "",
                "This phase does not create compensation decisions, business instructions, formal reports, external connectors, app runtime changes, Stage 15 review, or upload evidence.",
                "",
            ]
        ),
    )
    write_text(
        TEST_RESULTS_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 S15-P2 Test Results",
                "",
                "- generator: pending external validator replay",
                "- validator: pending external validator replay",
                "- focused_unittest: pending external unittest replay",
                "- governance_validation: pending external governance replay",
                "- raw_secret_scan: pending external scan replay",
                "",
            ]
        ),
    )
    write_text(
        RISK_REGISTER_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 S15-P2 Risk Register",
                "",
                "| Risk | Control |",
                "|---|---|",
                "| Review list is mistaken for salary or bonus approval | All compensation and payment gates remain false |",
                "| Public evidence leaks source values | Artifacts store only refs, hashes, status, and counts |",
                "| Phase drifts into S15-P3 or upload | Downstream phase and upload flags remain false |",
                "",
            ]
        ),
    )
    write_text(
        ROLLBACK_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 S15-P2 Rollback Plan",
                "",
                "Rollback is limited to removing the S15-P2 generated evidence, validator, focused test, and governance deltas from the local commit before any upload. No protected source data is changed by this phase.",
                "",
            ]
        ),
    )


def generate(generated_at: str | None = None) -> dict[str, Any]:
    manifest, fact_rows, review_items = build_artifacts(generated_at=generated_at)
    write_outputs(manifest, fact_rows, review_items)
    return manifest


def main() -> int:
    manifest = generate()
    summary = manifest["performance_review_summary"]
    print(
        "PASS: KMFA v0.1.4 S15-P2 performance review list generated "
        f"(fact_rows={summary['performance_fact_row_count']}, "
        f"review_items={summary['abnormal_review_item_count']}, "
        "salary=false, bonus=false, payroll=false, s15_p3=false, stage15_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
