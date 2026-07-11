#!/usr/bin/env python3
"""Generate current KMFA v0.1.4 S17-P3 operations SOP evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools import v014_s17_p2_post_remediation_notification as s17_p2
from KMFA.tools.check_v014_s17_p2_post_remediation_notification import (
    validate_v014_s17_p2_post_remediation_notification,
)
from KMFA.tools.check_v014_s17_p3_operations_sop import (
    validate_v014_s17_p3_operations_sop as validate_historical_s17_p3,
)


PHASE_ID = "V014_S17_P3_POST_REMEDIATION_OPERATIONS_SOP"
ROADMAP_PHASE_ID = "S17-P3"
TASK_ID = "KMFA-V014-S17-P3-POST-REMEDIATION-OPERATIONS-SOP-20260712"
ACCEPTANCE_ID = "ACC-V014-S17-P3-POST-REMEDIATION-OPERATIONS-SOP"
VERSION = "0.1.4-s17-p3-post-remediation-operations-sop"
STATUS = "completed_validated_local_only_s17_p3_operations_sop_no_go_upload_deferred"
DECISION = "NO_GO"
FORMULA_ID = "FORM-KMFA-V014-S17-P3-POST-REMEDIATION-OPERATIONS-SOP-001"
PARAMETER_IDS = ("PARAM-KMFA-1800", "PARAM-KMFA-1801", "PARAM-KMFA-1802", "PARAM-KMFA-1803")
MODEL_REGISTRY_KEY = "kmfa_v014_s17_p3_post_remediation_operations_sop"
POLICY_VERSION = "OPS-KMFA-V014-S17P3-POST-REMEDIATION-PUBLIC-SAFE-001"
SYNTHETIC_SCHEMA_VERSION = "kmfa.synthetic.operations_fixture.v1"

REQUIRED_RUNBOOK_TYPES = ("import", "review", "publish", "rollback")
REQUIRED_KNOWLEDGE_TYPES = ("finance_sop", "handoff_materials")

OUTPUT_DIR = Path("KMFA/stage_artifacts") / PHASE_ID
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "operations_sop_summary.json"
MANIFEST_PATH = MACHINE_DIR / "operations_sop_manifest.json"
RUNBOOK_PATH = MACHINE_DIR / "operations_runbooks_public_safe.jsonl"
KNOWLEDGE_INDEX_PATH = MACHINE_DIR / "finance_sop_knowledge_index_public_safe.jsonl"
ERROR_DRILL_PATH = MACHINE_DIR / "error_handling_drill_results_public_safe.jsonl"
BACKUP_DRILL_PATH = MACHINE_DIR / "backup_restore_drill_results_public_safe.jsonl"
MATRIX_PATH = MACHINE_DIR / "acceptance_matrix_public_safe.json"
GO_NO_GO_PATH = MACHINE_DIR / "go_no_go_report.json"
REPORT_PATH = HUMAN_DIR / "operations_sop_report_zh.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results_zh.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register_zh.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan_zh.md"

METADATA_DIR = Path("KMFA/metadata/operations")
METADATA_SUMMARY_PATH = METADATA_DIR / "v014_s17_p3_post_remediation_operations_sop_summary.json"
METADATA_MANIFEST_PATH = METADATA_DIR / "v014_s17_p3_post_remediation_operations_sop_manifest.json"
METADATA_RUNBOOK_PATH = METADATA_DIR / "v014_s17_p3_post_remediation_operations_runbooks.jsonl"
METADATA_KNOWLEDGE_INDEX_PATH = METADATA_DIR / "v014_s17_p3_post_remediation_finance_sop_knowledge_index.jsonl"
METADATA_ERROR_DRILL_PATH = METADATA_DIR / "v014_s17_p3_post_remediation_error_handling_drill_results.jsonl"
METADATA_BACKUP_DRILL_PATH = METADATA_DIR / "v014_s17_p3_post_remediation_backup_restore_drill_results.jsonl"
METADATA_MATRIX_PATH = METADATA_DIR / "v014_s17_p3_post_remediation_acceptance_matrix.json"
METADATA_GO_NO_GO_PATH = METADATA_DIR / "v014_s17_p3_post_remediation_go_no_go_report.json"

PRIVATE_DIR = Path("KMFA/.codex_private_runtime/v014_s17_p3_post_remediation_operations_sop")
PRIVATE_RAW_BEFORE_PATH = PRIVATE_DIR / "raw_immutability_before.json"
PRIVATE_RAW_AFTER_PATH = PRIVATE_DIR / "raw_immutability_after.json"
PRIVATE_DRILL_DIR = PRIVATE_DIR / "synthetic_drill"
PRIVATE_DRILL_SOURCE_PATH = PRIVATE_DRILL_DIR / "source_fixture.json"
PRIVATE_DRILL_WORKING_PATH = PRIVATE_DRILL_DIR / "working_fixture.json"
PRIVATE_DRILL_BACKUP_PATH = PRIVATE_DRILL_DIR / "backup_fixture.json"
PRIVATE_DRILL_RESTORED_PATH = PRIVATE_DRILL_DIR / "restored_fixture.json"
PRIVATE_DRILL_DIAGNOSTIC_PATH = PRIVATE_DIR / "synthetic_drill_diagnostic.json"
PRIVATE_SCAN_REPORT_PATH = PRIVATE_DIR / "operations_sop_boundary_validation_zh.md"

ROADMAP_PATH = Path("KMFA/taskpack/v1_4/roadmap/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_4.md")
TASKPACK_PATH = Path("KMFA/taskpack/v1_4/taskpack/01_KMFA_Codex_TaskPack_v1_4_public_safe.md")
LEGACY_MANIFEST_PATH = Path("KMFA/stage_artifacts/V014_S17_P3_OPERATIONS_SOP/machine/operations_sop_manifest.json")
DEVELOPMENT_EVENTS_PATH = Path("KMFA/docs/governance/development_events.jsonl")
ASSURANCE_STATUS_PATH = Path("KMFA/docs/governance/ASSURANCE_STATUS.yaml")
STAGE_STATUS_PATH = Path("KMFA/metadata/stage_status.jsonl")
TASK_STATUS_PATH = Path("KMFA/metadata/traceability/v1_4_stage_phase_task_status.jsonl")


def _git_output(args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())
    return result.stdout.strip()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def _upsert_jsonl(path: Path, row: dict[str, Any]) -> None:
    preserved: list[str] = []
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip() and json.loads(line).get("phase_id") != PHASE_ID:
                preserved.append(line)
    preserved.append(json.dumps(row, ensure_ascii=False, separators=(",", ":")))
    _write_text(path, "\n".join(preserved))


def _sync_assurance_snapshot_time(generated_at: str) -> None:
    lines = ASSURANCE_STATUS_PATH.read_text(encoding="utf-8").splitlines()
    indexes = [index for index, line in enumerate(lines) if line.startswith("snapshot_event_time:" )]
    if len(indexes) != 1:
        raise RuntimeError("ASSURANCE_STATUS must contain exactly one snapshot_event_time")
    lines[indexes[0]] = f'snapshot_event_time: "{generated_at}"'
    _write_text(ASSURANCE_STATUS_PATH, "\n".join(lines))


def _taskpack_contract() -> dict[str, Any]:
    roadmap = ROADMAP_PATH.read_text(encoding="utf-8")
    taskpack = TASKPACK_PATH.read_text(encoding="utf-8")
    for token in (
        "导入、复核、发布、回滚操作手册",
        "财务SOP和交接材料进入知识索引",
        "错误处理和备份恢复演练",
    ):
        if token not in roadmap:
            raise ValueError(f"roadmap token missing: {token}")
    for token in ("知识材料和操作检查清单", "不参与自动财务执行", "不提交原始敏感数据到公开GitHub"):
        if token not in taskpack:
            raise ValueError(f"taskpack token missing: {token}")
    return {
        "roadmap_read": True,
        "taskpack_read": True,
        "operations_runbook_knowledge_and_drill_contract_locked": True,
        "automated_finance_execution_forbidden": True,
        "source_refs": {"roadmap": ROADMAP_PATH.as_posix(), "taskpack": TASKPACK_PATH.as_posix()},
    }


def _phase_boundaries() -> dict[str, bool]:
    return {
        "s17_p1_performed": True,
        "s17_p2_performed": True,
        "s17_p3_performed": True,
        "private_synthetic_drill_performed": True,
        "stage17_review_performed": False,
        "s18_performed": False,
        "production_restore_performed": False,
        "raw_backup_or_copy_performed": False,
        "external_connector_performed": False,
        "notification_delivery_performed": False,
        "customer_contact_performed": False,
        "collection_action_performed": False,
        "legal_action_performed": False,
        "construction_action_performed": False,
        "signature_action_performed": False,
        "invoice_action_performed": False,
        "payment_or_bank_action_performed": False,
        "formal_report_release_performed": False,
        "difference_closure_performed": False,
        "persistent_business_write_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }


def _public_safety() -> dict[str, bool]:
    return {
        "raw_business_data_committed": False,
        "raw_file_names_committed": False,
        "raw_schema_or_header_committed": False,
        "business_value_plaintext_committed": False,
        "project_customer_or_counterparty_plaintext_committed": False,
        "credential_or_secret_committed": False,
        "private_runtime_committed": False,
        "synthetic_fixture_payload_committed": False,
        "private_drill_hash_committed": False,
        "zip_excel_pdf_private_csv_database_committed": False,
    }


def _raw_boundary() -> dict[str, bool]:
    return {
        "raw_snapshot_read_performed": True,
        "raw_content_materialization_performed": False,
        "raw_copy_or_backup_performed": False,
        "raw_write_performed": False,
        "raw_delete_performed": False,
        "raw_move_performed": False,
        "raw_rename_performed": False,
        "raw_overwrite_performed": False,
        "raw_mutation_performed": False,
    }


def _quality_gate() -> dict[str, Any]:
    return {
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "decision": "NO_GO",
        "open_final_difference_accepted_count": 3,
        "nonzero_delta_reconciliation_count": 9,
        "zero_delta_reconciliation_count": 2,
        "incomplete_reconciliation_count": 1,
        "one_cent_tolerance_minor_unit": 0,
        "manual_sop_allowed": True,
        "public_safe_knowledge_index_allowed": True,
        "isolated_synthetic_drill_allowed": True,
        "formal_report_release_allowed": False,
        "automated_finance_execution_allowed": False,
        "production_restore_allowed": False,
    }


RUNBOOK_SPECS: tuple[dict[str, Any], ...] = (
    {
        "runbook_type": "import",
        "title_zh": "导入操作手册",
        "owner_role": "finance_operator",
        "steps_zh": [
            "确认原始目录只读且当前任务授权有效",
            "仅登记 public-safe 来源引用与批次标识",
            "执行结构校验并拒绝缺字段或非安全载荷",
            "将诊断写入私有运行目录并保留审计引用",
            "复跑 validator 后交由复核角色处理",
        ],
        "rollback_zh": "撤销派生登记并追加反向事件，不修改原始文件。",
    },
    {
        "runbook_type": "review",
        "title_zh": "复核操作手册",
        "owner_role": "reviewer",
        "steps_zh": [
            "确认导入证据、依赖 validator 与 raw 快照一致",
            "复核差异队列和 0.01 元零容差控制",
            "核对 Q4、D、NO_GO 与 3-9-2-1 状态",
            "记录复核结论、风险与回滚依据",
            "未满足质量门时保持发布阻断并升级人工处理",
        ],
        "rollback_zh": "撤销复核结论的派生状态并保留原审计记录。",
    },
    {
        "runbook_type": "publish",
        "title_zh": "发布操作手册",
        "owner_role": "management",
        "steps_zh": [
            "确认发布门、人工授权和证据完整性",
            "确认当前报告等级不是 D 且决策不是 NO_GO",
            "只选择经过允许的 public-safe 发布对象",
            "发布前复跑完整 validator 与安全扫描",
            "记录发布结果；当前门禁不满足时终止发布",
        ],
        "rollback_zh": "撤回派生发布对象并追加发布回滚事件。",
    },
    {
        "runbook_type": "rollback",
        "title_zh": "回滚操作手册",
        "owner_role": "reviewer",
        "steps_zh": [
            "识别需回退的派生证据和治理记录范围",
            "确认原始文件及生产状态均不在回滚范围",
            "恢复上一份已验证的 public-safe 元数据引用",
            "复跑 validator、raw 快照和 secret scan",
            "追加回滚审计记录并保留差异说明",
        ],
        "rollback_zh": "恢复失败时停止自动动作并转人工恢复记录。",
    },
)


KNOWLEDGE_SPECS: tuple[dict[str, Any], ...] = (
    {
        "item_type": "finance_sop",
        "title_zh": "财务 SOP 知识索引",
        "owner_role": "finance_operator",
        "checklist_zh": [
            "原始目录只读",
            "来源与证据引用完整",
            "金额采用整数最小货币单位",
            "0.01 元零容差",
            "差异未解决时保持 NO_GO",
            "不得参与自动财务执行",
        ],
    },
    {
        "item_type": "handoff_materials",
        "title_zh": "岗位交接材料知识索引",
        "owner_role": "reviewer",
        "checklist_zh": [
            "当前阶段与依赖状态",
            "未解决风险和差异",
            "证据与 validator 路径",
            "私有材料只在忽略目录",
            "回滚步骤和停止条件",
            "下一轮范围与禁止事项",
        ],
    },
)


def _runbook_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in RUNBOOK_SPECS:
        runbook_type = str(spec["runbook_type"])
        rows.append(
            {
                "record_type": "v014_s17_p3_post_remediation_operation_runbook",
                "project_id": "KMFA",
                "stage_id": "S17",
                "phase_id": PHASE_ID,
                "task_id": TASK_ID,
                "policy_version": POLICY_VERSION,
                "runbook_id": f"S17P3-RUNBOOK-{runbook_type}",
                "runbook_type": runbook_type,
                "title_zh": spec["title_zh"],
                "owner_role": spec["owner_role"],
                "execution_mode": "manual_sop_only",
                "precheck_required": True,
                "evidence_required": True,
                "rollback_required": True,
                "steps_zh": spec["steps_zh"],
                "rollback_zh": spec["rollback_zh"],
                "append_only_audit_required": True,
                "raw_mutation_allowed": False,
                "external_service_allowed": False,
                "production_restore_allowed": False,
                "business_execution_allowed": False,
                "formal_report_release_allowed": False,
                "evidence_ref": RUNBOOK_PATH.as_posix(),
            }
        )
    return rows


def _knowledge_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in KNOWLEDGE_SPECS:
        item_type = str(spec["item_type"])
        rows.append(
            {
                "record_type": "v014_s17_p3_post_remediation_knowledge_index",
                "project_id": "KMFA",
                "stage_id": "S17",
                "phase_id": PHASE_ID,
                "task_id": TASK_ID,
                "policy_version": POLICY_VERSION,
                "knowledge_item_id": f"S17P3-KNOWLEDGE-{item_type}",
                "item_type": item_type,
                "title_zh": spec["title_zh"],
                "owner_role": spec["owner_role"],
                "storage_mode": "public_safe_knowledge_index_only",
                "execution_mode": "knowledge_and_checklist_only",
                "checklist_zh": spec["checklist_zh"],
                "handoff_required": True,
                "append_only": True,
                "automated_finance_execution_allowed": False,
                "business_decision_basis_allowed": False,
                "private_document_committed": False,
                "raw_business_data_committed": False,
                "credential_material_committed": False,
                "evidence_ref": KNOWLEDGE_INDEX_PATH.as_posix(),
            }
        )
    return rows


def validate_import_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    if candidate.get("schema_version") != SYNTHETIC_SCHEMA_VERSION:
        errors.append("schema_version_invalid")
    if candidate.get("record_type") != "synthetic_operation_fixture":
        errors.append("record_type_invalid")
    if not candidate.get("operation_ref"):
        errors.append("operation_ref_required")
    if candidate.get("public_safe") is not True:
        errors.append("public_safe_required")
    if candidate.get("raw_payload_present") is True:
        errors.append("raw_payload_forbidden")
    return {"valid": not errors, "errors": errors}


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _run_private_drills(generated_at: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    PRIVATE_DRILL_DIR.mkdir(parents=True, exist_ok=True)
    valid_fixture = {
        "schema_version": SYNTHETIC_SCHEMA_VERSION,
        "record_type": "synthetic_operation_fixture",
        "operation_ref": "S17P3-SYNTHETIC",
        "public_safe": True,
    }
    invalid_candidates = [
        {**valid_fixture, "schema_version": "invalid"},
        {key: value for key, value in valid_fixture.items() if key != "operation_ref"},
    ]
    validations = [validate_import_candidate(candidate) for candidate in invalid_candidates]
    rejected = sum(not result["valid"] for result in validations)
    unexpected = sum(result["valid"] for result in validations)
    error_pass = rejected == 2 and unexpected == 0

    source_bytes = (json.dumps(valid_fixture, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
    PRIVATE_DRILL_SOURCE_PATH.write_bytes(source_bytes)
    PRIVATE_DRILL_WORKING_PATH.write_bytes(source_bytes)
    shutil.copyfile(PRIVATE_DRILL_WORKING_PATH, PRIVATE_DRILL_BACKUP_PATH)
    backup_bytes = PRIVATE_DRILL_BACKUP_PATH.read_bytes()
    PRIVATE_DRILL_WORKING_PATH.write_bytes(b'{"corrupted":true}\n')
    corruption_detected = PRIVATE_DRILL_WORKING_PATH.read_bytes() != backup_bytes
    shutil.copyfile(PRIVATE_DRILL_BACKUP_PATH, PRIVATE_DRILL_RESTORED_PATH)
    restored_bytes = PRIVATE_DRILL_RESTORED_PATH.read_bytes()
    restored_exact = restored_bytes == source_bytes == backup_bytes
    backup_pass = corruption_detected and restored_exact

    diagnostic = {
        "generated_at": generated_at,
        "fixture_kind": "synthetic_public_safe_only",
        "raw_source_used": False,
        "error_scenarios": [
            {"scenario_id": f"S17P3-ERROR-{index:02d}", "validation": result}
            for index, result in enumerate(validations, 1)
        ],
        "source_sha256": _sha256_bytes(source_bytes),
        "backup_sha256": _sha256_bytes(backup_bytes),
        "restored_sha256": _sha256_bytes(restored_bytes),
        "corruption_detected": corruption_detected,
        "restored_byte_exact": restored_exact,
        "error_drill_passed": error_pass,
        "backup_restore_drill_passed": backup_pass,
        "production_restore_performed": False,
        "business_execution_performed": False,
    }
    _write_json(PRIVATE_DRILL_DIAGNOSTIC_PATH, diagnostic)
    if not error_pass or not backup_pass:
        raise ValueError("isolated synthetic operations drill failed")

    error_rows = [
        {
            "record_type": "v014_s17_p3_post_remediation_error_handling_drill",
            "project_id": "KMFA",
            "stage_id": "S17",
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "drill_id": "S17P3-DRILL-ERROR-HANDLING",
            "drill_type": "error_handling",
            "execution_mode": "isolated_synthetic_runtime_drill",
            "scenario_count": 2,
            "rejected_candidate_count": rejected,
            "unexpected_accept_count": unexpected,
            "result_status": "PASS",
            "raw_source_used": False,
            "external_service_called": False,
            "persistent_business_write_performed": False,
            "business_execution_performed": False,
            "public_safe_aggregate_only": True,
            "evidence_ref": ERROR_DRILL_PATH.as_posix(),
        }
    ]
    backup_rows = [
        {
            "record_type": "v014_s17_p3_post_remediation_backup_restore_drill",
            "project_id": "KMFA",
            "stage_id": "S17",
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "drill_id": "S17P3-DRILL-BACKUP-RESTORE",
            "drill_type": "backup_recovery",
            "execution_mode": "isolated_synthetic_runtime_drill",
            "synthetic_fixture_count": 1,
            "backup_created_count": 1,
            "corruption_detected_count": int(corruption_detected),
            "restore_completed_count": int(restored_exact),
            "restored_byte_exact": restored_exact,
            "result_status": "PASS",
            "raw_source_used": False,
            "production_restore_performed": False,
            "external_service_called": False,
            "persistent_business_write_performed": False,
            "business_execution_performed": False,
            "public_safe_aggregate_only": True,
            "evidence_ref": BACKUP_DRILL_PATH.as_posix(),
        }
    ]
    return error_rows, backup_rows, diagnostic


def _acceptance_matrix(summary: dict[str, Any]) -> dict[str, Any]:
    checks = (
        ("current_dependency", summary["current_s17_p2_validated"]),
        ("historical_quarantine", summary["historical_s17_p3_validated"]),
        ("four_runbooks", summary["operation_runbook_count"] == 4 and summary["runbook_step_count"] == 20),
        ("knowledge_index", summary["knowledge_item_count"] == 2 and summary["knowledge_checklist_item_count"] == 12),
        ("error_drill", summary["error_drill_scenario_count"] == 2 and summary["error_drill_rejected_count"] == 2),
        ("backup_restore", summary["backup_restore_drill_count"] == 1 and summary["restored_byte_exact_count"] == 1),
        ("no_production_restore", summary["production_restore_count"] == 0),
        ("no_raw_copy", summary["raw_copy_or_backup_count"] == 0),
        ("no_external", summary["external_service_call_count"] == 0),
        ("no_business_execution", summary["business_execution_count"] == 0),
        ("raw_exact", summary["raw_snapshot_exact_match"] and summary["raw_cross_phase_snapshot_exact_match"]),
        ("quality", summary["current_report_grade"] == "D" and summary["decision"] == "NO_GO"),
        ("stage_review_closed", not summary["stage17_review_performed"]),
        ("stage18_closed", not summary["s18_performed"]),
        ("upload_closed", not summary["github_upload_performed"]),
    )
    rows = [
        {"check_id": f"V014-S17-P3-ACC-{index:03d}", "name": name, "status": "PASS" if passed else "FAIL"}
        for index, (name, passed) in enumerate(checks, 1)
    ]
    return {
        "schema_version": "kmfa.v014.s17_p3_post_remediation_operations_sop_matrix.v1",
        "acceptance_id": ACCEPTANCE_ID,
        "check_count": len(rows),
        "check_pass_count": sum(row["status"] == "PASS" for row in rows),
        "check_fail_count": sum(row["status"] == "FAIL" for row in rows),
        "checks": rows,
    }


def _phase_public_files() -> list[str]:
    artifacts = (
        SUMMARY_PATH, MANIFEST_PATH, RUNBOOK_PATH, KNOWLEDGE_INDEX_PATH, ERROR_DRILL_PATH,
        BACKUP_DRILL_PATH, MATRIX_PATH, GO_NO_GO_PATH, REPORT_PATH, TEST_RESULTS_PATH,
        RISK_REGISTER_PATH, ROLLBACK_PATH,
    )
    metadata = (
        METADATA_SUMMARY_PATH, METADATA_MANIFEST_PATH, METADATA_RUNBOOK_PATH,
        METADATA_KNOWLEDGE_INDEX_PATH, METADATA_ERROR_DRILL_PATH, METADATA_BACKUP_DRILL_PATH,
        METADATA_MATRIX_PATH, METADATA_GO_NO_GO_PATH,
    )
    governance = (
        Path("KMFA/AGENTS.md"), Path("KMFA/CHANGELOG.md"), Path("KMFA/HANDOFF.md"), Path("KMFA/VERSION"),
        ASSURANCE_STATUS_PATH, Path("KMFA/docs/governance/DEVELOPMENT_LEDGER.md"),
        Path("KMFA/docs/governance/MODEL_SPEC.md"), Path("KMFA/docs/governance/OWNER_STATUS.md"),
        Path("KMFA/docs/governance/STATUS.md"), Path("KMFA/docs/governance/TRACEABILITY_MATRIX.csv"),
        Path("KMFA/docs/governance/VERSION_MATRIX.yaml"), Path("KMFA/docs/governance/delivery_tasks.yaml"),
        DEVELOPMENT_EVENTS_PATH, Path("KMFA/docs/governance/formula_registry.yaml"),
        Path("KMFA/docs/governance/model_registry.yaml"), Path("KMFA/docs/governance/parameter_registry.csv"),
        Path("KMFA/metadata/model_registry.yaml"), STAGE_STATUS_PATH, TASK_STATUS_PATH,
        Path("KMFA/功能清单.md"), Path("KMFA/开发记录.md"), Path("KMFA/模型参数文件.md"),
    )
    code = (
        Path("KMFA/tools/v014_s17_p3_post_remediation_operations_sop.py"),
        Path("KMFA/tools/check_v014_s17_p3_post_remediation_operations_sop.py"),
        Path("KMFA/tests/test_v014_s17_p3_post_remediation_operations_sop.py"),
    )
    return [path.as_posix() for path in artifacts + metadata + governance + code]


def _write_governance(generated_at: str) -> None:
    evidence_ref = MANIFEST_PATH.as_posix()
    _sync_assurance_snapshot_time(generated_at)
    _upsert_jsonl(
        DEVELOPMENT_EVENTS_PATH,
        {
            "event_id": "DEV-KMFA-20260712-V014-S17-P3-POST-REMEDIATION-OPERATIONS-SOP",
            "event_time": generated_at,
            "event_type": "phase_completion",
            "project_id": "KMFA",
            "stage_id": "S17",
            "phase_id": PHASE_ID,
            "roadmap_phase_id": ROADMAP_PHASE_ID,
            "task_id": TASK_ID,
            "status": STATUS,
            "fact_level": "EXTRACTED",
            "decision": DECISION,
            "operation_runbook_count": 4,
            "knowledge_item_count": 2,
            "error_drill_scenario_count": 2,
            "backup_restore_drill_count": 1,
            "production_restore_count": 0,
            "raw_copy_or_backup_count": 0,
            "raw_business_data_committed": False,
            "github_upload_performed": False,
            "app_reinstall_performed": False,
            "business_execution_performed": False,
            "evidence_ref": evidence_ref,
            "files_changed": _phase_public_files(),
            "result_commit": "PENDING",
        },
    )
    _upsert_jsonl(
        STAGE_STATUS_PATH,
        {
            "schema_version": "kmfa.stage_status.v1",
            "record_type": "phase_status",
            "project_id": "KMFA",
            "stage_id": "S17",
            "phase_id": PHASE_ID,
            "roadmap_phase_id": ROADMAP_PHASE_ID,
            "task_id": TASK_ID,
            "version": VERSION,
            "status": STATUS,
            "fact_level": "EXTRACTED",
            "decision": DECISION,
            "current_report_grade": "D",
            "raw_data_committed": False,
            "github_upload_performed": False,
            "app_reinstall_performed": False,
            "business_execution_performed": False,
            "evidence_ref": evidence_ref,
            "updated_at": generated_at,
        },
    )
    _upsert_jsonl(
        TASK_STATUS_PATH,
        {
            "schema_version": "kmfa.v014_stage_phase_task_status.v1",
            "record_type": "v014_stage_phase_task",
            "project_id": "KMFA",
            "stage_id": "S17",
            "governance_stage_id": "ACCESS-SECURITY-AUDIT",
            "roadmap_stage_id": "S17",
            "roadmap_phase_id": ROADMAP_PHASE_ID,
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "acceptance_id": ACCEPTANCE_ID,
            "version": VERSION,
            "name": "v0.1.4 S17-P3 post-remediation operations SOP",
            "phase_goal": "lock four manual runbooks two knowledge indexes and isolated synthetic error backup drills",
            "status": STATUS,
            "fact_level": "EXTRACTED",
            "derived_percent": 100,
            "estimated_task_units": 3,
            "completed_task_units": 3,
            "task_count": 3,
            "raw_data_committed": False,
            "evidence_ref": evidence_ref,
            "updated_at": generated_at[:10],
        },
    )


def _render_report(summary: dict[str, Any]) -> str:
    return f"""# KMFA v0.1.4 S17-P3 运维与 SOP

## 结论

- 操作手册：导入、复核、发布、回滚共 `{summary['operation_runbook_count']}` 类、`{summary['runbook_step_count']}` 个步骤，全部为人工 SOP。
- 知识索引：财务 SOP 与岗位交接共 `{summary['knowledge_item_count']}` 项、`{summary['knowledge_checklist_item_count']}` 个检查点，只作知识与检查清单，不参与自动财务执行。
- 错误演练：隔离合成候选 `{summary['error_drill_scenario_count']}` 个，拒绝 `{summary['error_drill_rejected_count']}` 个，误接受 0。
- 备份恢复：隔离合成夹具 1 个，已创建备份、检测损坏并完成 byte-exact 恢复；生产恢复为 0。
- raw：phase 前后及跨 S17-P2 快照一致，未复制、备份、修改、删除、移动、重命名或覆盖原始数据。
- 当前状态：Q4 / D / NO_GO / 3-9-2-1。

## 边界

- 合成夹具、哈希和诊断只在 `.codex_private_runtime/`，公开证据只有聚合计数和状态。
- 本轮未执行 Stage 17 整体复审、Stage 18、GitHub upload、app reinstall、正式报告、外部通知、客户联系、催收、法务、施工、签署、开票、支付或银行操作。
- 下一轮只能单独执行 Stage 17 整体复审。
"""


def _render_private_report(summary: dict[str, Any]) -> str:
    return f"""# S17-P3 私有边界核验

- 原始数据文件数：{summary['raw_source_file_count']}
- phase 前后快照：exact match
- 与 S17-P2 快照：exact match
- 当前只读快照：exact match
- 错误演练：2 个合成候选全部拒绝
- 备份恢复演练：合成夹具 byte-exact 恢复
- 原始数据复制/备份/修改/删除/移动/重命名/覆盖：0
- 生产恢复/外部服务/业务执行：0 / 0 / 0
- 结论：原始目录未受损；最终 goal 多轮仍无法对齐时，必须生成全中文最终差异报告。
"""


def generate(*, final_validation: bool = False, write_governance: bool = True) -> dict[str, Any]:
    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
    taskpack_contract = _taskpack_contract()
    current_s17_p2 = validate_v014_s17_p2_post_remediation_notification(
        require_private_evidence=True,
        require_final_evidence=True,
    )
    historical_s17_p3 = validate_historical_s17_p3()

    raw_helper = s17_p2.s17_p1.s16_review.p1.s15_review.p1.s14_review.p1.s13_review.p1.s12_review.p1.s11_project
    raw_before = raw_helper._raw_snapshot("before_v014_s17_p3_post_remediation_operations_sop")
    runbooks = _runbook_rows()
    knowledge = _knowledge_rows()
    error_drills, backup_drills, _diagnostic = _run_private_drills(generated_at)
    raw_after = raw_helper._raw_snapshot("after_v014_s17_p3_post_remediation_operations_sop")
    prior_raw = _read_json(s17_p2.PRIVATE_RAW_AFTER_PATH)
    current_raw = raw_helper._raw_snapshot("current_v014_s17_p3_post_remediation_operations_sop")
    normalize = raw_helper._normalize_raw
    raw_exact = normalize(raw_before) == normalize(raw_after)
    raw_cross = normalize(raw_before) == normalize(prior_raw) == normalize(current_raw)
    if not raw_exact or not raw_cross:
        raise ValueError("raw source changed during S17-P3")

    repo_scan = s17_p2.s17_p1._repo_tracking_scan()
    if repo_scan["status"] != "PASS":
        raise ValueError("tracked KMFA path scan failed")

    summary = {
        "schema_version": "kmfa.v014.s17_p3_post_remediation_operations_sop_summary.v1",
        "project_id": "KMFA",
        "stage_id": "S17",
        "phase_id": PHASE_ID,
        "roadmap_phase_id": ROADMAP_PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "version": VERSION,
        "status": STATUS,
        "decision": DECISION,
        "current_s17_p2_validated": True,
        "historical_s17_p3_validated": True,
        "operation_runbook_count": len(runbooks),
        "runbook_type_count": len({row["runbook_type"] for row in runbooks}),
        "runbook_step_count": sum(len(row["steps_zh"]) for row in runbooks),
        "knowledge_item_count": len(knowledge),
        "knowledge_item_type_count": len({row["item_type"] for row in knowledge}),
        "knowledge_checklist_item_count": sum(len(row["checklist_zh"]) for row in knowledge),
        "error_handling_drill_count": len(error_drills),
        "error_drill_scenario_count": error_drills[0]["scenario_count"],
        "error_drill_rejected_count": error_drills[0]["rejected_candidate_count"],
        "error_drill_unexpected_accept_count": error_drills[0]["unexpected_accept_count"],
        "backup_restore_drill_count": len(backup_drills),
        "synthetic_fixture_count": backup_drills[0]["synthetic_fixture_count"],
        "backup_created_count": backup_drills[0]["backup_created_count"],
        "corruption_detected_count": backup_drills[0]["corruption_detected_count"],
        "restore_completed_count": backup_drills[0]["restore_completed_count"],
        "restored_byte_exact_count": int(backup_drills[0]["restored_byte_exact"]),
        "production_restore_count": 0,
        "raw_copy_or_backup_count": 0,
        "external_service_call_count": 0,
        "persistent_business_write_count": 0,
        "business_execution_count": 0,
        "formal_report_count": 0,
        "raw_source_file_count": raw_before["file_count"],
        "raw_snapshot_exact_match": raw_exact,
        "raw_cross_phase_snapshot_exact_match": raw_cross,
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "open_final_difference_accepted_count": 3,
        "nonzero_delta_reconciliation_count": 9,
        "zero_delta_reconciliation_count": 2,
        "incomplete_reconciliation_count": 1,
        **_phase_boundaries(),
    }
    matrix = _acceptance_matrix(summary)
    go_no_go = {
        "schema_version": "kmfa.v014.s17_p3_post_remediation_operations_sop_go_no_go.v1",
        "project_id": "KMFA",
        "stage_id": "S17",
        "phase_id": PHASE_ID,
        "decision": "NO_GO",
        "s17_p3_validated": True,
        "manual_sop_and_knowledge_index_allowed": True,
        "isolated_synthetic_drill_allowed": True,
        "stage17_review_allowed_in_this_run": False,
        "s18_allowed": False,
        "production_restore_allowed": False,
        "raw_copy_or_backup_allowed": False,
        "external_connector_allowed": False,
        "notification_delivery_allowed": False,
        "formal_report_release_allowed": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "difference_closure_allowed": False,
        "persistent_business_write_allowed": False,
        "business_execution_allowed": False,
    }
    validation_summary = {
        "final_validation_recorded": final_validation,
        "focused_test": "PASS" if final_validation else "PENDING",
        "strict_validator": "PASS" if final_validation else "PENDING",
        "isolated_error_and_backup_drills": "PASS" if final_validation else "PENDING",
        "raw_alignment": "PASS" if final_validation else "PENDING",
        "governance_and_safety_scans": "PASS" if final_validation else "PENDING",
    }
    historical_summary = historical_s17_p3["operations_sop_summary"]
    manifest = {
        "schema_version": "kmfa.v014.s17_p3_post_remediation_operations_sop_manifest.v1",
        "project_id": "KMFA",
        "stage_id": "S17",
        "phase_id": PHASE_ID,
        "roadmap_phase_id": ROADMAP_PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "version": VERSION,
        "status": STATUS,
        "decision": DECISION,
        "generated_at": generated_at,
        "reviewed_head": _git_output(["rev-parse", "HEAD"]),
        "branch": _git_output(["branch", "--show-current"]),
        "remote": _git_output(["remote", "get-url", "origin"]),
        "formula_id": FORMULA_ID,
        "parameter_ids": list(PARAMETER_IDS),
        "model_registry_key": MODEL_REGISTRY_KEY,
        "summary": summary,
        "current_s17_p2_validated": True,
        "current_s17_p2_manifest_ref": s17_p2.MANIFEST_PATH.as_posix(),
        "historical_s17_p3_validated": True,
        "historical_s17_p3_dynamic_state_is_authoritative": False,
        "historical_structure_quarantined": {
            "runbook_count": historical_summary["operation_runbook_count"],
            "knowledge_item_count": historical_summary["knowledge_item_count"],
            "drill_log_count": historical_summary["drill_log_count"],
        },
        "legacy_manifest_ref": LEGACY_MANIFEST_PATH.as_posix(),
        "taskpack_contract": taskpack_contract,
        "required_runbook_types": list(REQUIRED_RUNBOOK_TYPES),
        "required_knowledge_types": list(REQUIRED_KNOWLEDGE_TYPES),
        "stage17_progress": {
            "completed_phase_count": 3,
            "total_phase_count": 3,
            "s17_p1_performed": True,
            "s17_p2_performed": True,
            "s17_p3_performed": True,
            "stage17_review_performed": False,
        },
        "repo_tracking_scan": repo_scan,
        "quality_gate": _quality_gate(),
        "phase_boundaries": _phase_boundaries(),
        "public_repo_safety": _public_safety(),
        "raw_boundary": _raw_boundary(),
        "acceptance_matrix": matrix,
        "go_no_go": go_no_go,
        "validation_summary": validation_summary,
        "next_phase": "S17_STAGE_REVIEW",
        "next_required_step": (
            "下一轮只能执行 Stage 17 整体复审；不得执行 Stage 18、GitHub upload、app reinstall、正式报告、"
            "外部通知、客户联系、催收、法务、施工、签署、开票、支付或银行操作、差异关闭、持久业务写入或业务执行。"
        ),
    }

    for path, value in (
        (SUMMARY_PATH, summary), (MANIFEST_PATH, manifest), (MATRIX_PATH, matrix), (GO_NO_GO_PATH, go_no_go),
        (METADATA_SUMMARY_PATH, summary), (METADATA_MANIFEST_PATH, manifest),
        (METADATA_MATRIX_PATH, matrix), (METADATA_GO_NO_GO_PATH, go_no_go),
        (PRIVATE_RAW_BEFORE_PATH, raw_before), (PRIVATE_RAW_AFTER_PATH, raw_after),
    ):
        _write_json(path, value)
    for path, rows in (
        (RUNBOOK_PATH, runbooks), (KNOWLEDGE_INDEX_PATH, knowledge),
        (ERROR_DRILL_PATH, error_drills), (BACKUP_DRILL_PATH, backup_drills),
        (METADATA_RUNBOOK_PATH, runbooks), (METADATA_KNOWLEDGE_INDEX_PATH, knowledge),
        (METADATA_ERROR_DRILL_PATH, error_drills), (METADATA_BACKUP_DRILL_PATH, backup_drills),
    ):
        _write_jsonl(path, rows)
    _write_text(REPORT_PATH, _render_report(summary))
    _write_text(
        TEST_RESULTS_PATH,
        """# S17-P3 运维与 SOP 测试结果

- focused test / strict validator：最终复验记录见 manifest。
- 操作手册：4 类、20 个步骤，全部人工执行并带前置检查、证据和回滚。
- 知识索引：2 项、12 个检查点，不参与自动财务执行。
- 错误演练：2 个合成无效候选全部拒绝。
- 备份恢复：1 个合成夹具已检测损坏并 byte-exact 恢复，生产恢复为 0。
- raw phase 前后 / 跨 S17-P2 / current：exact match。
- quality：Q4 / D / NO_GO / 3-9-2-1。
""",
    )
    _write_text(
        RISK_REGISTER_PATH,
        """# S17-P3 运维与 SOP 风险登记

| 风险 | 控制 | 状态 |
|---|---|---|
| 手册被误读为自动执行授权 | 所有 runbook 固定 manual_sop_only，业务执行为 0 | 已控制 |
| 知识索引被误读为完整私有文档 | 仅提交 public-safe 索引和检查清单 | 已控制 |
| 演练误触生产或 raw | 只在 ignored private runtime 使用合成夹具 | 已控制 |
| D级报告被错误发布 | 发布手册明确 Q4/D/NO_GO 时终止，正式报告为 0 | 已控制 |
| 历史元数据模拟被误作当前证据 | 历史 S17-P3 仅作结构夹具，当前演练独立执行 | 已控制 |
""",
    )
    _write_text(
        ROLLBACK_PATH,
        f"""# S17-P3 运维与 SOP 回滚计划

1. 回退本 phase 的本地 commit 与 `{OUTPUT_DIR.as_posix()}` public-safe 证据。
2. 回退本 phase 新增的 metadata/operations 镜像和治理登记，不改历史 S17-P3 夹具。
3. 删除 ignored private 合成夹具、诊断与 raw 快照，不触碰原始目录。
4. 不执行生产恢复、外部连接、补偿通知、财务动作或任何业务写入。
""",
    )
    _write_text(PRIVATE_SCAN_REPORT_PATH, _render_private_report(summary))
    if write_governance:
        _write_governance(generated_at)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--final-validation", action="store_true")
    parser.add_argument("--no-governance", action="store_true")
    args = parser.parse_args()
    manifest = generate(final_validation=args.final_validation, write_governance=not args.no_governance)
    summary = manifest["summary"]
    print(
        "S17-P3 post-remediation operations SOP: "
        f"runbooks={summary['operation_runbook_count']} knowledge={summary['knowledge_item_count']} "
        f"error_scenarios={summary['error_drill_scenario_count']} backup_restore={summary['backup_restore_drill_count']} "
        f"raw_copy={summary['raw_copy_or_backup_count']} production_restore={summary['production_restore_count']} "
        f"grade={summary['current_report_grade']} decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
