#!/usr/bin/env python3
"""Generate KMFA v0.1.4 S15-P3 salary boundary evidence.

This phase reserves a public-safe performance fact output interface and a
future read draft for a salary system. It does not create a live integration,
API endpoint, connector, file export, salary calculation, bonus approval,
payroll export, final compensation decision, final payment, Stage 15 review,
or GitHub upload.
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

from KMFA.tools.check_v014_s15_p2_performance_review_list import (  # noqa: E402
    validate_v014_s15_p2_performance_review_list,
)
from KMFA.tools.performance_salary_boundary import (  # noqa: E402
    REQUIRED_FACT_INTERFACE_FIELDS as LEGACY_REQUIRED_FACT_INTERFACE_FIELDS,
    build_default_performance_salary_boundary_artifacts,
    validate_performance_salary_boundary_artifacts,
)
from KMFA.tools.v014_s15_p2_performance_review_list import (  # noqa: E402
    FACT_TABLE_PATH as S15P2_FACT_TABLE_PATH,
    MANIFEST_PATH as S15P2_MANIFEST_PATH,
    REQUIRED_PERFORMANCE_REVIEW_FIELDS,
    REVIEW_ITEMS_PATH as S15P2_REVIEW_ITEMS_PATH,
)


TASK_ID = "KMFA-V014-S15-P3-SALARY-BOUNDARY-20260705"
ACCEPTANCE_ID = "ACC-V014-S15-P3-SALARY-BOUNDARY"
SCHEMA_VERSION = "kmfa.v014_s15_p3_salary_boundary.v1"
PHASE_SCOPE = "v014_s15_p3_salary_boundary_only"
BOUNDARY_VERSION = "BOUNDARY-KMFA-V014-S15P3-SALARY-FACT-INTERFACE-DRAFT-001"
FORMULA_ID = "FORM-KMFA-V014-S15P3-SALARY-BOUNDARY-001"
MAPPING_VERSION = "MAP-KMFA-V014-S15P3-SALARY-BOUNDARY-v1"

OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_S15_P3_SALARY_BOUNDARY")
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
MANIFEST_PATH = MACHINE_DIR / "salary_boundary_manifest.json"
INTERFACE_CONTRACT_PATH = MACHINE_DIR / "fact_output_interface_contract.json"
READINESS_DRAFT_PATH = MACHINE_DIR / "future_salary_system_readiness_draft.jsonl"
REPORT_PATH = HUMAN_DIR / "salary_boundary_report.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

V14_TASKPACK_PATH = Path("KMFA/taskpack/v1_4/taskpack/01_KMFA_Codex_TaskPack_v1_4_public_safe.md")
V14_ROADMAP_PATH = Path("KMFA/taskpack/v1_4/roadmap/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_4.md")

RAW_INBOX_REF = "operator-designated raw/private inbox outside repository"
NEXT_REQUIRED_STEP = (
    "Proceed to v0.1.4 Stage 15 overall review as a separate run only after user instruction. "
    "Do not perform GitHub upload, S16, protected source matching, lineage full check, formal report release, "
    "live connector, app reinstall, OpMe deep coupling, salary calculation, bonus approval, payroll export, "
    "final compensation decision, final payment, payment execution, or business execution in the S15-P3 run."
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


def validate_s15_p2_dependency() -> dict[str, Any]:
    result = validate_v014_s15_p2_performance_review_list()
    if result.get("stage_id") != "S15" or result.get("phase_id") != "S15-P2":
        raise RuntimeError("S15-P3 requires validated v0.1.4 S15-P2 evidence")
    if result.get("next_phase") != "S15-P3":
        raise RuntimeError("S15-P2 must route to S15-P3")
    progress = result.get("stage15_phase_progress", {})
    if progress.get("s15_p1_performed") is not True or progress.get("s15_p2_performed") is not True:
        raise RuntimeError("S15-P3 requires completed S15-P1 and S15-P2")
    if progress.get("s15_p3_performed") is not False:
        raise RuntimeError("S15-P2 dependency must not already include S15-P3")
    if result.get("github_upload", {}).get("github_upload_deferred_until_v014_stage1_18_complete") is not True:
        raise RuntimeError("v1.4 upload must remain deferred")
    raw = result.get("raw_data_boundary", {})
    for key in ("raw_inbox_read_by_this_phase", "raw_inbox_listed_by_this_phase", "raw_inbox_mutated_by_this_phase"):
        if raw.get(key) is not False:
            raise RuntimeError(f"S15-P2 raw boundary must keep {key}=false")
    return result


def validate_legacy_s15_p3_artifacts() -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    manifest, interface_contract, readiness_rows = build_default_performance_salary_boundary_artifacts(
        generated_at="2026-07-05T10:20:00+10:00"
    )
    validate_performance_salary_boundary_artifacts(manifest, interface_contract, readiness_rows)
    return manifest, interface_contract, readiness_rows


def load_v14_taskpack_baseline() -> dict[str, Any]:
    taskpack_text = V14_TASKPACK_PATH.read_text(encoding="utf-8")
    roadmap_text = V14_ROADMAP_PATH.read_text(encoding="utf-8")

    for token in (
        "与工资项目边界",
        "仅预留事实输出接口",
        "未来可供工资系统读取草案",
        "最终审批和发放必须人工处理",
    ):
        if token not in roadmap_text:
            raise RuntimeError(f"v1.4 roadmap missing S15-P3 required marker {token}")
    for token in ("销售绩效/业务考核线", "不做工资最终审批", "不自动发工资或奖金"):
        if token not in taskpack_text:
            raise RuntimeError(f"v1.4 taskpack missing S15 salary boundary required marker {token}")

    return {
        "taskpack_read": True,
        "roadmap_read": True,
        "roadmap_includes_s15_p3_requirements": True,
        "taskpack_includes_no_final_salary_approval": True,
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
        "employee_or_salary_payload_committed": False,
        "payroll_export_committed": False,
        "final_compensation_payload_committed": False,
        "final_payment_payload_committed": False,
        "business_decision_basis_committed": False,
    }


def _quality_gate() -> dict[str, Any]:
    return {
        "fact_output_interface_reserved": True,
        "future_salary_system_readiness_draft_allowed": True,
        "final_approval_must_be_human": True,
        "payment_release_must_be_human": True,
        "live_salary_system_integration_allowed": False,
        "api_endpoint_allowed": False,
        "connector_allowed": False,
        "file_export_allowed": False,
        "scheduled_sync_allowed": False,
        "external_system_write_allowed": False,
        "salary_calculation_allowed": False,
        "wage_calculation_allowed": False,
        "bonus_approval_allowed": False,
        "payroll_export_allowed": False,
        "final_compensation_decision_allowed": False,
        "automatic_compensation_decision_allowed": False,
        "final_payment_allowed": False,
        "automatic_payment_allowed": False,
        "payment_execution_allowed": False,
        "business_decision_basis_allowed": False,
        "formal_report_allowed": False,
        "complete_trusted_report_display_allowed": False,
        "raw_layer_write_allowed": False,
        "public_numeric_value_display_allowed": False,
        "stage15_review_allowed": False,
        "github_upload_allowed": False,
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "release_permission": "blocked",
        "release_block_reason": "salary_boundary_contract_only_pending_stage15_review_and_v014_stage1_18_upload_gate",
    }


def _phase_boundaries() -> dict[str, bool]:
    return {
        "s15_p1_dependency_reused": True,
        "s15_p2_dependency_reused": True,
        "s15_p3_salary_boundary_scope_included": True,
        "stage15_review_scope_included": False,
        "s16_scope_included": False,
        "github_upload_scope_included": False,
        "lineage_full_check_scope_included": False,
        "protected_source_matching_scope_included": False,
        "formal_report_runtime_scope_included": False,
        "live_ui_runtime_scope_included": False,
        "external_connector_scope_included": False,
        "app_reinstall_scope_included": False,
        "opme_deep_coupling_scope_included": False,
        "salary_system_live_scope_included": False,
        "salary_calculation_scope_included": False,
        "bonus_approval_scope_included": False,
        "payroll_export_scope_included": False,
        "final_compensation_scope_included": False,
        "final_payment_scope_included": False,
        "payment_execution_scope_included": False,
        "business_execution_scope_included": False,
    }


def _review_items_by_fact(review_items: list[dict[str, Any]]) -> dict[str, list[str]]:
    by_fact: dict[str, list[str]] = {}
    for item in review_items:
        fact_ref = str(item.get("performance_fact_row_ref"))
        by_fact.setdefault(fact_ref, []).append(str(item.get("review_item_id")))
    return by_fact


def _build_interface_contract(generated_at: str) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v014_s15_p3.fact_output_interface_contract.v1",
        "record_type": "fact_output_interface_contract",
        "project_id": "KMFA",
        "stage_id": "S15",
        "phase_id": "S15-P3",
        "generated_at": generated_at,
        "boundary_version": BOUNDARY_VERSION,
        "formula_id": FORMULA_ID,
        "mapping_version": MAPPING_VERSION,
        "interface_status": "reserved_contract_only",
        "source_manifest_ref": S15P2_MANIFEST_PATH.as_posix(),
        "source_fact_table_ref": S15P2_FACT_TABLE_PATH.as_posix(),
        "source_review_item_ref": S15P2_REVIEW_ITEMS_PATH.as_posix(),
        "fact_interface_fields": list(REQUIRED_PERFORMANCE_REVIEW_FIELDS),
        "allowed_payload_fields": [
            "performance_fact_row_ref",
            "project_ref",
            "available_fact_fields",
            "field_status_refs",
            "fact_hash_ref_fields",
            "review_item_refs",
            "evidence_refs",
            "boundary_flags",
        ],
        "value_policy": "hash_ref_status_and_evidence_only_no_numeric_compensation_payload",
        "read_model_status": "draft_schema_for_future_system_only",
        "api_endpoint_created": False,
        "file_export_created": False,
        "connector_enabled": False,
        "live_read_enabled": False,
        "scheduled_sync_enabled": False,
        "external_write_enabled": False,
        "raw_layer_write_allowed": False,
        "public_numeric_values_allowed": False,
        "automatic_compensation_decision_allowed": False,
        "automatic_payment_allowed": False,
        "final_approval_must_be_human": True,
        "payment_release_must_be_human": True,
    }


def _readiness_row(
    *,
    index: int,
    fact_row: dict[str, Any],
    review_item_ids: list[str],
    generated_at: str,
) -> dict[str, Any]:
    row_id = f"V014-S15P3-READ-{index:03d}"
    fact_row_id = str(fact_row["performance_fact_row_id"])
    return {
        "schema_version": "kmfa.v014_s15_p3.future_salary_system_readiness_draft.v1",
        "record_type": "future_salary_system_readiness_draft",
        "project_id": "KMFA",
        "stage_id": "S15",
        "phase_id": "S15-P3",
        "readiness_row_id": row_id,
        "generated_at": generated_at,
        "performance_fact_row_ref": f"{S15P2_FACT_TABLE_PATH.as_posix()}#{fact_row_id}",
        "project_ref": str(fact_row["project_ref"]),
        "interface_contract_ref": INTERFACE_CONTRACT_PATH.as_posix(),
        "source_review_item_refs": [
            f"{S15P2_REVIEW_ITEMS_PATH.as_posix()}#{item_id}" for item_id in sorted(review_item_ids)
        ],
        "available_fact_fields": list(REQUIRED_PERFORMANCE_REVIEW_FIELDS),
        "field_status_refs": dict(fact_row.get("fact_status_by_field", {})),
        "fact_hash_ref_fields": sorted(fact_row.get("fact_hash_refs_by_field", {}).keys()),
        "review_item_count": len(review_item_ids),
        "future_read_status": "draft_only_blocked_until_manual_review_and_human_approval",
        "value_policy": "no_numeric_compensation_or_payment_payload",
        "boundary_decision_policy": "facts_may_be_read_later_decisions_must_be_manual",
        "manual_approval_role": "owner_or_authorized_compensation_approver",
        "final_approval_must_be_human": True,
        "payment_release_must_be_human": True,
        "raw_business_values_allowed": False,
        "public_numeric_values_allowed": False,
        "field_plaintext_allowed": False,
        "api_endpoint_created": False,
        "connector_enabled": False,
        "live_read_enabled": False,
        "file_export_created": False,
        "salary_calculation_allowed": False,
        "wage_calculation_allowed": False,
        "bonus_approval_allowed": False,
        "payroll_export_allowed": False,
        "automatic_compensation_decision_allowed": False,
        "automatic_payment_allowed": False,
        "payment_execution_allowed": False,
        "final_compensation_decision_allowed": False,
        "final_payment_allowed": False,
        "business_execution_allowed": False,
    }


def build_artifacts(generated_at: str | None = None) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    generated_at = generated_at or datetime.now().isoformat(timespec="seconds")
    s15_p2 = validate_s15_p2_dependency()
    legacy_manifest, legacy_interface, legacy_readiness_rows = validate_legacy_s15_p3_artifacts()
    baseline = load_v14_taskpack_baseline()
    fact_rows = read_jsonl(S15P2_FACT_TABLE_PATH)
    review_items = read_jsonl(S15P2_REVIEW_ITEMS_PATH)

    if tuple(REQUIRED_PERFORMANCE_REVIEW_FIELDS) != tuple(LEGACY_REQUIRED_FACT_INTERFACE_FIELDS):
        raise RuntimeError("v0.1.4 S15-P3 fact fields must remain compatible with legacy S15-P3 baseline")
    if len(fact_rows) != 4:
        raise RuntimeError("S15-P3 requires four v0.1.4 S15-P2 performance fact rows")
    if len(review_items) != 16:
        raise RuntimeError("S15-P3 requires sixteen v0.1.4 S15-P2 review items")

    interface_contract = _build_interface_contract(generated_at)
    review_by_fact = _review_items_by_fact(review_items)
    readiness_rows: list[dict[str, Any]] = []
    for index, fact_row in enumerate(fact_rows, start=1):
        fact_ref = f"{S15P2_FACT_TABLE_PATH.as_posix()}#{fact_row['performance_fact_row_id']}"
        review_ids = review_by_fact.get(fact_ref, [])
        if len(review_ids) != 4:
            raise RuntimeError(f"{fact_ref} must have four S15-P2 review items")
        readiness_rows.append(
            _readiness_row(index=index, fact_row=fact_row, review_item_ids=review_ids, generated_at=generated_at)
        )

    summary = {
        "fact_output_interface_contract_count": 1,
        "future_salary_system_readiness_row_count": len(readiness_rows),
        "human_approval_boundary_count": len(readiness_rows),
        "pending_review_item_count": len(review_items),
        "salary_calculation_count": 0,
        "wage_calculation_count": 0,
        "bonus_approval_count": 0,
        "payroll_export_count": 0,
        "final_compensation_decision_count": 0,
        "final_payment_count": 0,
        "payment_execution_count": 0,
        "report_grade_visible": "D",
    }
    manifest: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "v014_s15_p3_salary_boundary_manifest",
        "project_id": "KMFA",
        "version": "0.1.4",
        "stage_id": "S15",
        "phase_id": "S15-P3",
        "phase_scope": PHASE_SCOPE,
        "task_id": TASK_ID,
        "acceptance_ids": [ACCEPTANCE_ID],
        "completed_task_ids": ["S15P3T01", "S15P3T02", "S15P3T03"],
        "status": "completed_validated_local_only_no_go_upload_deferred_salary_boundary_locked",
        "generated_at": generated_at,
        "branch": git_output(["branch", "--show-current"]),
        "git_head": git_output(["rev-parse", "HEAD"]),
        "s15_p2_dependency_validated": True,
        "historical_s15_p3_public_safe_baseline_validated": True,
        "v14_taskpack_baseline": baseline,
        "legacy_baseline_summary": {
            "stage_phase": legacy_manifest.get("stage_phase"),
            "interface_contract_count": legacy_manifest.get("summary", {}).get("fact_interface_contract_count"),
            "future_salary_system_readiness_row_count": len(legacy_readiness_rows),
            "salary_calculation_count": legacy_manifest.get("summary", {}).get("salary_calculation_count"),
            "bonus_approval_count": legacy_manifest.get("summary", {}).get("bonus_approval_count"),
            "payroll_export_count": legacy_manifest.get("summary", {}).get("payroll_export_count"),
            "interface_status": legacy_interface.get("interface_status"),
        },
        "upstream_refs": {
            "s15_p2_manifest": S15P2_MANIFEST_PATH.as_posix(),
            "s15_p2_fact_table": S15P2_FACT_TABLE_PATH.as_posix(),
            "s15_p2_review_items": S15P2_REVIEW_ITEMS_PATH.as_posix(),
        },
        "stage15_phase_progress": {
            "completed_phase_count": 3,
            "total_phase_count": 3,
            "derived_percent_bps": 10000,
            "derived_percent_label": "100.00%",
            "s15_p1_performed": True,
            "s15_p2_performed": True,
            "s15_p3_performed": True,
            "stage15_review_performed": False,
        },
        "salary_boundary_summary": summary,
        "artifact_refs": {
            "manifest": MANIFEST_PATH.as_posix(),
            "fact_output_interface_contract": INTERFACE_CONTRACT_PATH.as_posix(),
            "future_salary_system_readiness_draft": READINESS_DRAFT_PATH.as_posix(),
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
            "stage15_review_not_performed",
            "github_upload_deferred_until_v014_stage1_18_complete",
            "business_execution_blocked",
        ],
        "s15_p2_dependency_status": {
            "task_id": s15_p2.get("task_id"),
            "status": s15_p2.get("status"),
            "next_phase": s15_p2.get("next_phase"),
        },
        "next_phase": "S15_STAGE_REVIEW",
        "next_required_step": NEXT_REQUIRED_STEP,
    }
    manifest["content_hash"] = sha256_ref(
        json.dumps([manifest, interface_contract, readiness_rows], ensure_ascii=False, sort_keys=True)
    )
    return manifest, interface_contract, readiness_rows


def write_outputs(
    manifest: dict[str, Any],
    interface_contract: dict[str, Any],
    readiness_rows: list[dict[str, Any]],
) -> None:
    write_json(MANIFEST_PATH, manifest)
    write_json(INTERFACE_CONTRACT_PATH, interface_contract)
    write_jsonl(READINESS_DRAFT_PATH, readiness_rows)
    summary = manifest["salary_boundary_summary"]
    write_text(
        REPORT_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 S15-P3 Salary Boundary",
                "",
                f"- task_id: `{TASK_ID}`",
                "- status: `completed_validated_local_only_no_go_upload_deferred_salary_boundary_locked`",
                "- scope: reserved fact output interface and future system read draft only",
                f"- fact_output_interface_contract_count: `{summary['fact_output_interface_contract_count']}`",
                f"- future_salary_system_readiness_rows: `{summary['future_salary_system_readiness_row_count']}`",
                f"- pending_review_items: `{summary['pending_review_item_count']}`",
                "- salary_calculation_allowed: `false`",
                "- bonus_approval_allowed: `false`",
                "- payroll_export_allowed: `false`",
                "- final_compensation_decision_allowed: `false`",
                "- final_payment_allowed: `false`",
                "- payment_execution_allowed: `false`",
                "- final_approval_must_be_human: `true`",
                "- payment_release_must_be_human: `true`",
                "- live_integration_allowed: `false`",
                "- stage15_review_performed: `false`",
                "- github_upload_performed: `false`",
                "- raw_inbox_access_by_this_phase: `false`",
                "- next_phase: `S15_STAGE_REVIEW`",
                "",
                "## Evidence",
                "",
                f"- `{MANIFEST_PATH.as_posix()}`",
                f"- `{INTERFACE_CONTRACT_PATH.as_posix()}`",
                f"- `{READINESS_DRAFT_PATH.as_posix()}`",
                "",
            ]
        ),
    )
    write_text(
        TEST_RESULTS_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 S15-P3 Test Results",
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
                "# KMFA v0.1.4 S15-P3 Risk Register",
                "",
                "| Risk | Control |",
                "|---|---|",
                "| Boundary contract is mistaken for live salary integration | API, connector, file export and live read flags remain false |",
                "| Future read draft is mistaken for payroll approval | salary, bonus, payroll, final payment and payment execution gates remain false |",
                "| Phase drifts into Stage 15 review or upload | Stage review and upload flags remain false |",
                "| Raw/private material leaks into public evidence | Evidence stores public-safe refs, hashes, counts and status only |",
                "",
            ]
        ),
    )
    write_text(
        ROLLBACK_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 S15-P3 Rollback Plan",
                "",
                "- Revert the local S15-P3 commit if validation fails before any later stage review.",
                "- Remove only `KMFA/stage_artifacts/V014_S15_P3_SALARY_BOUNDARY/` and v0.1.4 S15-P3 governance references if this phase is discarded.",
                "- Do not modify the operator-designated raw/private inbox during rollback.",
                "",
            ]
        ),
    )


def generate(generated_at: str | None = None) -> dict[str, Any]:
    manifest, interface_contract, readiness_rows = build_artifacts(generated_at)
    write_outputs(manifest, interface_contract, readiness_rows)
    return manifest


def main() -> int:
    manifest = generate()
    summary = manifest["salary_boundary_summary"]
    print(
        "PASS: KMFA v0.1.4 S15-P3 salary boundary generated "
        f"(interface_contracts={summary['fact_output_interface_contract_count']}, "
        f"readiness_rows={summary['future_salary_system_readiness_row_count']}, "
        "future_read_draft=true, live_integration=false, "
        "salary=false, bonus=false, payroll=false, final_payment=false, "
        "stage15_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
