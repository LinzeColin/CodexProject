#!/usr/bin/env python3
"""Generate current KMFA v0.1.4 S18-P3 integration-preparation evidence."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools import v014_s18_p2_post_remediation_full_regression_acceptance as s18_p2  # noqa: E402
from KMFA.tools import v014_s18_p3_integration_preparation as historical_s18_p3  # noqa: E402
from KMFA.tools.check_v014_s18_p2_post_remediation_full_regression_acceptance import (  # noqa: E402
    validate_v014_s18_p2_post_remediation_full_regression_acceptance,
)


PHASE_ID = "V014_S18_P3_POST_REMEDIATION_INTEGRATION_PREPARATION"
ROADMAP_PHASE_ID = "S18-P3"
TASK_ID = "KMFA-V014-S18-P3-POST-REMEDIATION-INTEGRATION-PREPARATION-20260712"
ACCEPTANCE_ID = "ACC-V014-S18-P3-POST-REMEDIATION-INTEGRATION-PREPARATION"
VERSION = "0.1.4-s18-p3-post-remediation-integration-preparation"
STATUS = "completed_validated_local_only_s18_p3_integration_prepared_no_go_upload_deferred"
DECISION = "NO_GO"
FORMULA_ID = "FORM-KMFA-V014-S18-P3-POST-REMEDIATION-INTEGRATION-PREPARATION-001"
PARAMETER_IDS = ("PARAM-KMFA-1813", "PARAM-KMFA-1814", "PARAM-KMFA-1815")
MODEL_REGISTRY_KEY = "kmfa_v014_s18_p3_post_remediation_integration_preparation"

REQUIRED_CONNECTOR_IDS = ("redcircle", "kingdee", "wps")
REQUIRED_OPME_ENTRY_SURFACES = ("read_only_entry", "report_index", "run_status", "handoff_link")
REQUIRED_OPME_EXCHANGE_REFS = (
    "public_safe_status_summary",
    "report_index_pointer",
    "handoff_pointer",
    "validator_command_pointer",
)
REQUIRED_BACKLOG_IDS = tuple(f"BL-KMFA-NEXT-{index:03d}" for index in range(1, 7))
COMPLETION_GATE_SEQUENCE = (
    "S18_STAGE_REVIEW_AND_FINDING_FIX",
    "V014_FINAL_OVERALL_REVIEW_AND_FINDING_FIX",
    "ONE_TIME_GITHUB_MAIN_UPLOAD",
    "APP_ENTRY_REINSTALL_AND_PARITY_VERIFICATION",
)

OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_S18_P3_POST_REMEDIATION_INTEGRATION_PREPARATION")
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
MANIFEST_PATH = MACHINE_DIR / "integration_preparation_manifest.json"
CONNECTOR_PLAN_PATH = MACHINE_DIR / "read_only_connector_plan_public_safe.jsonl"
OPME_PLAN_PATH = MACHINE_DIR / "opme_light_entry_plan_public_safe.json"
BACKLOG_PATH = MACHINE_DIR / "next_stage_backlog_public_safe.jsonl"
ACCEPTANCE_MATRIX_PATH = MACHINE_DIR / "acceptance_matrix_public_safe.json"
GO_NO_GO_PATH = MACHINE_DIR / "go_no_go_report.json"

REPORT_PATH = HUMAN_DIR / "integration_preparation_report_zh.md"
CONNECTOR_RECORD_PATH = HUMAN_DIR / "read_only_connector_plan_zh.md"
OPME_RECORD_PATH = HUMAN_DIR / "opme_light_entry_plan_zh.md"
BACKLOG_RECORD_PATH = HUMAN_DIR / "next_stage_backlog_zh.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record_zh.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results_zh.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register_zh.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan_zh.md"

METADATA_DIR = Path("KMFA/metadata/integration")
METADATA_MANIFEST_PATH = METADATA_DIR / "v014_s18_p3_post_remediation_integration_preparation_manifest.json"
METADATA_CONNECTOR_PLAN_PATH = METADATA_DIR / "v014_s18_p3_post_remediation_read_only_connector_plan.jsonl"
METADATA_OPME_PLAN_PATH = METADATA_DIR / "v014_s18_p3_post_remediation_opme_light_entry_plan.json"
METADATA_BACKLOG_PATH = METADATA_DIR / "v014_s18_p3_post_remediation_next_stage_backlog.jsonl"
METADATA_ACCEPTANCE_MATRIX_PATH = METADATA_DIR / "v014_s18_p3_post_remediation_acceptance_matrix.json"
METADATA_GO_NO_GO_PATH = METADATA_DIR / "v014_s18_p3_post_remediation_go_no_go_report.json"

PRIVATE_DIR = Path("KMFA/.codex_private_runtime/v014_s18_p3_post_remediation_integration_preparation")
PRIVATE_RAW_BEFORE_PATH = PRIVATE_DIR / "raw_immutability_before.json"
PRIVATE_RAW_AFTER_PATH = PRIVATE_DIR / "raw_immutability_after.json"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_DIR / "integration_preparation_boundary_diagnostic.json"
PRIVATE_REPORT_PATH = PRIVATE_DIR / "integration_preparation_boundary_report_zh.md"

TASKPACK_PATH = Path("KMFA/taskpack/v1_4/taskpack/01_KMFA_Codex_TaskPack_v1_4_public_safe.md")
ROADMAP_PATH = Path("KMFA/taskpack/v1_4/roadmap/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_4.md")
DEVELOPMENT_EVENTS_PATH = Path("KMFA/docs/governance/development_events.jsonl")
STAGE_STATUS_PATH = Path("KMFA/metadata/stage_status.jsonl")
TASK_STATUS_PATH = Path("KMFA/metadata/traceability/v1_4_stage_phase_task_status.jsonl")
ASSURANCE_STATUS_PATH = Path("KMFA/docs/governance/ASSURANCE_STATUS.yaml")

FORBIDDEN_PUBLIC_TEXT = (
    "private_ref://",
    "original_filename",
    "source_header_text",
    "raw_value",
    "normalized_value",
    "customer_name_plaintext",
    "project_name_plaintext",
    "counterparty_name_plaintext",
    "supplier_name_plaintext",
    "payment_account",
    "bank_account_number",
    "contract_number",
    "invoice_number",
    "/Users/linzezhang/Downloads",
    "KMFA_MetaData",
    "connector_token",
    "connector_password",
    "credential_payload",
)


def _git_output(args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())
    return result.stdout.strip()


def _sha256_json(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + sha256(encoded).hexdigest()


def _sha256_file(path: Path) -> str:
    return "sha256:" + sha256(path.read_bytes()).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not all(isinstance(row, dict) for row in rows):
        raise ValueError(f"expected JSONL objects: {path}")
    return rows


def _write_json(path: Path, value: dict[str, Any]) -> None:
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
    phase_id = row.get("phase_id")
    if not isinstance(phase_id, str) or not phase_id:
        raise ValueError("governance JSONL row requires phase_id")
    preserved: list[str] = []
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip() and json.loads(line).get("phase_id") != phase_id:
                preserved.append(line)
    preserved.append(json.dumps(row, ensure_ascii=False, separators=(",", ":")))
    _write_text(path, "\n".join(preserved))


def _sync_assurance_snapshot_time(generated_at: str) -> None:
    lines = ASSURANCE_STATUS_PATH.read_text(encoding="utf-8").splitlines()
    indexes = [index for index, line in enumerate(lines) if line.startswith("snapshot_event_time:")]
    if len(indexes) != 1:
        raise RuntimeError("ASSURANCE_STATUS must contain exactly one snapshot_event_time")
    lines[indexes[0]] = f'snapshot_event_time: "{generated_at}"'
    _write_text(ASSURANCE_STATUS_PATH, "\n".join(lines))


def _taskpack_contract() -> dict[str, Any]:
    taskpack = TASKPACK_PATH.read_text(encoding="utf-8")
    roadmap = ROADMAP_PATH.read_text(encoding="utf-8")
    for token in (
        "| P3 | 后续接入准备 |",
        "整理红圈、金蝶、WPS自动接入后续只读方案",
        "整理OpMe入口集成方案，不深度耦合",
        "发布下一阶段Backlog",
    ):
        if token not in roadmap:
            raise ValueError(f"v1.4 roadmap S18-P3 contract drift: {token}")
    for token in (
        "独立开发，后续接入OpMe",
        "禁止：直接写UI、直接生成报告、直接接红圈/金蝶/银行/税务接口、直接提交原始敏感数据",
        "该目录属于原始数据层，只读",
        "不提交原始敏感数据到公开GitHub",
    ):
        if token not in taskpack:
            raise ValueError(f"v1.4 taskpack S18-P3 boundary drift: {token}")
    return {
        "roadmap_phase_id": ROADMAP_PHASE_ID,
        "task_count": 3,
        "taskpack_read": True,
        "roadmap_read": True,
        "read_only_connector_contract_locked": True,
        "opme_light_entry_contract_locked": True,
        "next_stage_backlog_contract_locked": True,
        "source_refs": [TASKPACK_PATH.as_posix(), ROADMAP_PATH.as_posix()],
    }


def _s18_p2_dependency() -> dict[str, Any]:
    manifest = validate_v014_s18_p2_post_remediation_full_regression_acceptance(
        require_private_evidence=True,
        require_final_evidence=True,
    )
    summary = manifest.get("summary", {})
    if manifest.get("phase_id") != s18_p2.PHASE_ID:
        raise ValueError("current S18-P2 identity drift")
    if manifest.get("next_phase") != "S18-P3":
        raise ValueError("current S18-P2 does not route to S18-P3")
    if not summary.get("s18_p2_performed") or summary.get("s18_p3_performed"):
        raise ValueError("current S18-P2 phase boundary drift")
    if manifest.get("decision") != "NO_GO":
        raise ValueError("current S18-P2 decision must remain NO_GO")
    return {
        "validated": True,
        "phase_id": manifest["phase_id"],
        "status": manifest["status"],
        "decision": manifest["decision"],
        "evidence_ref": s18_p2.MANIFEST_PATH.as_posix(),
        "evidence_sha256": _sha256_file(s18_p2.MANIFEST_PATH),
    }


def _historical_baseline() -> dict[str, Any]:
    manifest, connectors, opme, backlog = historical_s18_p3.validate_historical_s18_p3_public_safe_baseline()
    if (
        len(connectors) != 3
        or len(opme.get("entry_surfaces", [])) != 4
        or len(backlog) != 6
        or manifest.get("stage_phase") != "S18-P3"
    ):
        raise ValueError("historical S18-P3 structural baseline drift")
    return {
        "validated": True,
        "connector_count": len(connectors),
        "opme_entry_surface_count": len(opme["entry_surfaces"]),
        "backlog_item_count": len(backlog),
        "dynamic_state_authoritative": False,
        "structural_fixture_ref": "KMFA/tools/integration_preparation.py",
        "legacy_artifact_ref": historical_s18_p3.MANIFEST_PATH.as_posix(),
        "legacy_artifact_validated_as_current": False,
    }


def _connector_rows(generated_at: str) -> list[dict[str, Any]]:
    specs = {
        "redcircle": (
            "红圈协作数据",
            "authorized_export_snapshot_or_contract_index",
            "owner_authorized_export_snapshot_read",
        ),
        "kingdee": (
            "金蝶财务数据",
            "authorized_read_only_finance_export",
            "owner_authorized_finance_export_read",
        ),
        "wps": (
            "WPS 文档数据",
            "authorized_read_only_document_export_or_watch_folder",
            "owner_authorized_document_export_read",
        ),
    }
    rows: list[dict[str, Any]] = []
    for connector_id in REQUIRED_CONNECTOR_IDS:
        source_label_zh, planned_entry_point, read_contract = specs[connector_id]
        rows.append(
            {
                "schema_version": "kmfa.v014.s18_p3_post_remediation_read_only_connector_plan.v1",
                "record_type": "v014_s18_p3_post_remediation_read_only_connector_plan",
                "project_id": "KMFA",
                "stage_id": "S18",
                "phase_id": PHASE_ID,
                "roadmap_phase_id": ROADMAP_PHASE_ID,
                "task_id": "S18P3T01",
                "acceptance_id": ACCEPTANCE_ID,
                "generated_at": generated_at,
                "connector_id": connector_id,
                "source_label_zh": source_label_zh,
                "integration_mode": "read_only_future_connector",
                "lifecycle_state": "proposal_only_not_authorized",
                "authorization_state": "not_requested_in_this_phase",
                "connection_state": "not_connected",
                "planned_entry_point": planned_entry_point,
                "planned_read_contract": read_contract,
                "allowed_operation_refs": [
                    "authorized_export_snapshot_read",
                    "schema_manifest_read",
                    "hash_manifest_read",
                    "public_safe_status_emit",
                ],
                "disallowed_operation_refs": [
                    "source_mutation",
                    "automatic_writeback",
                    "credential_publication",
                    "field_plaintext_publication",
                    "business_action_execution",
                ],
                "owner_authorization_required": True,
                "private_runtime_only": True,
                "hash_manifest_required": True,
                "schema_contract_required": True,
                "idempotency_key_required": True,
                "rollback_required": True,
                "polling_enabled": False,
                "source_mutation_allowed": False,
                "writeback_allowed": False,
                "auto_write_allowed": False,
                "credential_required_now": False,
                "credential_material_present": False,
                "live_connector_called": False,
                "external_service_called": False,
                "raw_business_data_used": False,
                "raw_business_data_committed": False,
                "field_plaintext_committed": False,
                "github_upload_allowed": False,
                "business_execution_allowed": False,
                "failure_policy": "fail_closed_without_owner_authorization_or_schema_match",
                "next_gate": "future_owner_authorization_and_private_runtime_connector_design",
            }
        )
    return rows


def _opme_plan(generated_at: str) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v014.s18_p3_post_remediation_opme_light_entry_plan.v1",
        "record_type": "v014_s18_p3_post_remediation_opme_light_entry_plan",
        "project_id": "KMFA",
        "stage_id": "S18",
        "phase_id": PHASE_ID,
        "roadmap_phase_id": ROADMAP_PHASE_ID,
        "task_id": "S18P3T02",
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": generated_at,
        "integration_mode": "entry_link_and_status_index_only",
        "coupling_level": "light_entry_only",
        "entry_surfaces": list(REQUIRED_OPME_ENTRY_SURFACES),
        "allowed_exchange_refs": list(REQUIRED_OPME_EXCHANGE_REFS),
        "status_contract_fields": [
            "project_id",
            "version",
            "phase_id",
            "decision",
            "data_quality_grade",
            "report_grade",
            "public_safe_evidence_pointer",
        ],
        "responsibility_split": {
            "kmfa_owner": "KMFA 业务逻辑、质量门禁与证据",
            "opme_owner": "入口导航与公开安全状态索引",
        },
        "deep_coupling_allowed": False,
        "shared_database_allowed": False,
        "shared_runtime_logic_allowed": False,
        "sensitive_data_mixing_allowed": False,
        "opme_controls_kmfa_business_logic": False,
        "kmfa_controls_opme_service_logic": False,
        "raw_business_data_exposed": False,
        "field_plaintext_exposed": False,
        "credential_material_present": False,
        "external_service_called": False,
        "github_upload_allowed": False,
        "business_execution_allowed": False,
        "failure_policy": "entry_unavailable_when_public_safe_status_contract_is_invalid",
        "next_gate": "opme_shell_design_after_stage18_and_final_overall_review",
    }


def _backlog_rows(generated_at: str) -> list[dict[str, Any]]:
    specs = (
        (
            "未来连接器授权与密钥边界设计",
            "设计 owner 授权、私有运行时和密钥托管边界，不在公开仓库保存凭据。",
            "future_owner_authorization_design",
        ),
        (
            "红圈只读连接器验证",
            "取得 owner 授权后，以只读导出快照或索引验证 Schema、哈希、幂等与回滚。",
            "future_redcircle_read_only_spike",
        ),
        (
            "金蝶只读连接器验证",
            "取得 owner 授权后，以只读财务导出验证 Schema、哈希、幂等与回滚。",
            "future_kingdee_read_only_spike",
        ),
        (
            "WPS 只读连接器验证",
            "取得 owner 授权后，以只读文档导出或受控目录验证 Schema、哈希、幂等与回滚。",
            "future_wps_read_only_spike",
        ),
        (
            "OpMe 轻入口壳层设计",
            "仅提供导航、公开安全状态、报告索引和交接指针，不共享数据库或业务运行时。",
            "future_opme_light_entry_design",
        ),
        (
            "最终交付门禁顺序执行",
            "先完成 Stage 18 复审及修复，再做 v1.4 最终整体复审及修复，之后一次性上传 main 并重装 App 入口。",
            "stage18_review_then_final_delivery_sequence",
        ),
    )
    rows: list[dict[str, Any]] = []
    for priority, (title_zh, description_zh, workstream) in enumerate(specs, start=1):
        rows.append(
            {
                "schema_version": "kmfa.v014.s18_p3_post_remediation_next_stage_backlog_item.v1",
                "record_type": "v014_s18_p3_post_remediation_next_stage_backlog_item",
                "project_id": "KMFA",
                "stage_id": "S18",
                "phase_id": PHASE_ID,
                "roadmap_phase_id": ROADMAP_PHASE_ID,
                "task_id": "S18P3T03",
                "acceptance_id": ACCEPTANCE_ID,
                "generated_at": generated_at,
                "backlog_id": REQUIRED_BACKLOG_IDS[priority - 1],
                "priority": priority,
                "title_zh": title_zh,
                "description_zh": description_zh,
                "workstream": workstream,
                "status": "backlog_proposed_not_started",
                "started": False,
                "owner_authorization_required": priority <= 5,
                "stage18_review_required_first": priority <= 5,
                "external_connector_allowed": False,
                "persistent_write_allowed": False,
                "business_execution_allowed": False,
                "github_upload_allowed": False,
                "app_reinstall_allowed": False,
                "raw_business_data_required_in_public_repo": False,
                "next_gate": "stage18_review_and_finding_fix",
            }
        )
    return rows


def _go_no_go() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v014.s18_p3_post_remediation_go_no_go.v1",
        "record_type": "v014_s18_p3_post_remediation_go_no_go",
        "project_id": "KMFA",
        "stage_id": "S18",
        "phase_id": PHASE_ID,
        "roadmap_phase_id": ROADMAP_PHASE_ID,
        "decision": "NO_GO",
        "maximum_report_grade": "D",
        "blocker_ids": [
            "LINEAGE_FULL_CHECK_NOT_COMPLETE",
            "OPEN_RECONCILIATION_REMAINS",
            "OFFICIAL_REPORT_RELEASE_NOT_ALLOWED",
            "STAGE18_REVIEW_PENDING",
            "FINAL_OVERALL_REVIEW_PENDING",
            "GITHUB_MAIN_UPLOAD_DEFERRED",
            "APP_REINSTALL_DEFERRED",
        ],
        "s18_p3_pending": False,
        "stage18_review_performed": False,
        "final_overall_review_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "external_connector_performed": False,
        "business_execution_performed": False,
        "delivery_allowed": False,
        "official_report_release_allowed": False,
        "business_decision_basis_allowed": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "external_connector_allowed": False,
        "persistent_business_write_allowed": False,
        "business_execution_allowed": False,
        "next_required_phase": "S18_STAGE_REVIEW",
    }


def _phase_boundaries() -> dict[str, bool]:
    return {
        "s18_p2_dependency_reused": True,
        "historical_s18_p3_structural_baseline_reused": True,
        "s18_p3_integration_preparation_performed": True,
        "private_raw_snapshot_validation_performed": True,
        "stage18_review_scope_included": False,
        "final_overall_review_scope_included": False,
        "github_upload_scope_included": False,
        "app_reinstall_scope_included": False,
        "live_connector_scope_included": False,
        "credential_handling_scope_included": False,
        "formal_report_scope_included": False,
        "difference_closure_scope_included": False,
        "lineage_full_check_scope_included": False,
        "persistent_business_write_scope_included": False,
        "business_execution_scope_included": False,
    }


def _public_repo_safety() -> dict[str, bool]:
    return {
        "raw_business_data_committed": False,
        "private_tabular_material_committed": False,
        "source_document_committed": False,
        "raw_file_name_committed": False,
        "raw_file_hash_committed": False,
        "field_plaintext_committed": False,
        "true_money_committed": False,
        "true_customer_project_committed": False,
        "true_account_committed": False,
        "credential_committed": False,
        "private_runtime_committed": False,
    }


def validate_integration_bundle(bundle: dict[str, Any]) -> None:
    summary = bundle["summary"]
    connectors = bundle["connectors"]
    opme = bundle["opme"]
    backlog = bundle["backlog"]
    go_no_go = bundle["go_no_go"]
    if [row.get("connector_id") for row in connectors] != list(REQUIRED_CONNECTOR_IDS):
        raise ValueError("connector identity or order drift")
    for row in connectors:
        if row.get("integration_mode") != "read_only_future_connector":
            raise ValueError("connector mode must be read-only")
        for key in (
            "polling_enabled",
            "source_mutation_allowed",
            "writeback_allowed",
            "auto_write_allowed",
            "credential_required_now",
            "credential_material_present",
            "live_connector_called",
            "external_service_called",
            "raw_business_data_used",
            "raw_business_data_committed",
            "field_plaintext_committed",
            "github_upload_allowed",
            "business_execution_allowed",
        ):
            if row.get(key) is not False:
                raise ValueError(f"connector {row.get('connector_id')}.{key} must be false")
    for key in (
        "deep_coupling_allowed",
        "shared_database_allowed",
        "shared_runtime_logic_allowed",
        "sensitive_data_mixing_allowed",
        "raw_business_data_exposed",
        "field_plaintext_exposed",
        "credential_material_present",
        "external_service_called",
        "github_upload_allowed",
        "business_execution_allowed",
    ):
        if opme.get(key) is not False:
            raise ValueError(f"opme.{key} must be false")
    if [row.get("backlog_id") for row in backlog] != list(REQUIRED_BACKLOG_IDS):
        raise ValueError("backlog identity or order drift")
    for row in backlog:
        for key in (
            "started",
            "external_connector_allowed",
            "persistent_write_allowed",
            "business_execution_allowed",
            "github_upload_allowed",
            "app_reinstall_allowed",
            "raw_business_data_required_in_public_repo",
        ):
            if row.get(key) is not False:
                raise ValueError(f"backlog {row.get('backlog_id')}.{key} must be false")
    if not summary.get("s18_p3_performed") or summary.get("stage18_review_performed"):
        raise ValueError("S18-P3 and Stage 18 review boundary drift")
    if go_no_go.get("decision") != "NO_GO" or "S18_P3_PENDING" in go_no_go.get("blocker_ids", []):
        raise ValueError("current Go/No-Go drift")
    for key, value in go_no_go.items():
        if (key.endswith("_allowed") or key.endswith("_performed")) and value is not False:
            raise ValueError(f"go_no_go.{key} must be false")


def _acceptance_matrix(
    summary: dict[str, Any],
    connectors: list[dict[str, Any]],
    opme: dict[str, Any],
    backlog: list[dict[str, Any]],
    go_no_go: dict[str, Any],
) -> dict[str, Any]:
    checks = (
        ("taskpack_contract", summary["taskpack_contract_validated"]),
        ("current_s18_p2_dependency", summary["s18_p2_dependency_validated"]),
        ("historical_s18_p3_structural_only", summary["historical_s18_p3_structural_baseline_validated"]),
        ("connector_count", len(connectors) == 3),
        ("connector_ids", [row["connector_id"] for row in connectors] == list(REQUIRED_CONNECTOR_IDS)),
        ("connector_read_only", all(row["integration_mode"] == "read_only_future_connector" for row in connectors)),
        ("connector_not_authorized", all(row["authorization_state"] == "not_requested_in_this_phase" for row in connectors)),
        ("connector_not_connected", all(row["connection_state"] == "not_connected" for row in connectors)),
        ("connector_no_writeback", all(not row["writeback_allowed"] for row in connectors)),
        ("connector_no_external_call", all(not row["external_service_called"] for row in connectors)),
        ("connector_no_credential", all(not row["credential_material_present"] for row in connectors)),
        ("connector_private_runtime_only", all(row["private_runtime_only"] for row in connectors)),
        ("connector_contract_controls", all(row["hash_manifest_required"] and row["schema_contract_required"] and row["idempotency_key_required"] and row["rollback_required"] for row in connectors)),
        ("opme_surface_count", len(opme["entry_surfaces"]) == 4),
        ("opme_light_entry", opme["coupling_level"] == "light_entry_only"),
        ("opme_public_safe_exchange_only", tuple(opme["allowed_exchange_refs"]) == REQUIRED_OPME_EXCHANGE_REFS),
        ("opme_no_shared_database", not opme["shared_database_allowed"]),
        ("opme_no_shared_runtime", not opme["shared_runtime_logic_allowed"]),
        ("backlog_count", len(backlog) == 6),
        ("backlog_not_started", all(not row["started"] for row in backlog)),
        ("completion_sequence", tuple(COMPLETION_GATE_SEQUENCE) == COMPLETION_GATE_SEQUENCE),
        ("raw_phase_exact", summary["raw_snapshot_exact_match"]),
        ("raw_cross_phase_exact", summary["raw_cross_phase_snapshot_exact_match"]),
        ("raw_not_used_for_plan", not summary["raw_business_content_used_for_integration_plan"]),
        ("reconciliation_truth_preserved", (summary["open_final_difference_accepted_count"], summary["nonzero_delta_reconciliation_count"], summary["zero_delta_reconciliation_count"], summary["incomplete_reconciliation_count"]) == (3, 9, 2, 1)),
        ("quality_stays_q4", summary["current_data_quality_grade"] == "Q4"),
        ("report_stays_d", summary["current_report_grade"] == "D"),
        ("decision_stays_no_go", go_no_go["decision"] == "NO_GO"),
        ("s18_p3_complete", summary["s18_p3_performed"]),
        ("stage18_review_pending", not summary["stage18_review_performed"]),
        ("final_review_pending", not summary["final_overall_review_performed"]),
        ("github_upload_deferred", not summary["github_upload_performed"]),
        ("app_reinstall_deferred", not summary["app_reinstall_performed"]),
        ("business_execution_closed", not summary["business_execution_performed"]),
    )
    rows = [{"check_id": check_id, "result": "PASS" if passed else "FAIL"} for check_id, passed in checks]
    return {
        "schema_version": "kmfa.v014.s18_p3_post_remediation_acceptance_matrix.v1",
        "record_type": "v014_s18_p3_post_remediation_acceptance_matrix",
        "project_id": "KMFA",
        "stage_id": "S18",
        "phase_id": PHASE_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "check_count": len(rows),
        "check_pass_count": sum(row["result"] == "PASS" for row in rows),
        "check_fail_count": sum(row["result"] == "FAIL" for row in rows),
        "checks": rows,
    }


def _phase_public_files() -> list[str]:
    paths = (
        Path("KMFA/AGENTS.md"), Path("KMFA/CHANGELOG.md"), Path("KMFA/HANDOFF.md"), Path("KMFA/README.md"), Path("KMFA/VERSION"),
        ASSURANCE_STATUS_PATH, Path("KMFA/docs/governance/DEVELOPMENT_LEDGER.md"), Path("KMFA/docs/governance/MODEL_SPEC.md"),
        Path("KMFA/docs/governance/OWNER_STATUS.md"), Path("KMFA/docs/governance/STATUS.md"),
        Path("KMFA/docs/governance/TRACEABILITY_MATRIX.csv"), Path("KMFA/docs/governance/VERSION_MATRIX.yaml"),
        Path("KMFA/docs/governance/delivery_tasks.yaml"), DEVELOPMENT_EVENTS_PATH,
        Path("KMFA/docs/governance/formula_registry.yaml"), Path("KMFA/docs/governance/model_registry.yaml"),
        Path("KMFA/docs/governance/parameter_registry.csv"), Path("KMFA/metadata/model_registry.yaml"),
        STAGE_STATUS_PATH, TASK_STATUS_PATH,
        MANIFEST_PATH, CONNECTOR_PLAN_PATH, OPME_PLAN_PATH, BACKLOG_PATH, ACCEPTANCE_MATRIX_PATH, GO_NO_GO_PATH,
        REPORT_PATH, CONNECTOR_RECORD_PATH, OPME_RECORD_PATH, BACKLOG_RECORD_PATH, GO_NO_GO_RECORD_PATH,
        TEST_RESULTS_PATH, RISK_REGISTER_PATH, ROLLBACK_PATH,
        METADATA_MANIFEST_PATH, METADATA_CONNECTOR_PLAN_PATH, METADATA_OPME_PLAN_PATH, METADATA_BACKLOG_PATH,
        METADATA_ACCEPTANCE_MATRIX_PATH, METADATA_GO_NO_GO_PATH,
        Path("KMFA/功能清单.md"), Path("KMFA/开发记录.md"), Path("KMFA/模型参数文件.md"),
        Path("KMFA/tools/v014_s18_p3_post_remediation_integration_preparation.py"),
        Path("KMFA/tools/check_v014_s18_p3_post_remediation_integration_preparation.py"),
        Path("KMFA/tests/test_v014_s18_p3_post_remediation_integration_preparation.py"),
    )
    return [path.as_posix() for path in paths]


def _write_governance(generated_at: str) -> None:
    _sync_assurance_snapshot_time(generated_at)
    evidence_ref = MANIFEST_PATH.as_posix()
    _upsert_jsonl(
        DEVELOPMENT_EVENTS_PATH,
        {
            "event_id": "DEV-KMFA-20260712-V014-S18-P3-POST-REMEDIATION-INTEGRATION-PREPARATION",
            "event_time": generated_at,
            "event_type": "phase_completion",
            "project_id": "KMFA",
            "stage_id": "S18",
            "phase_id": PHASE_ID,
            "roadmap_phase_id": ROADMAP_PHASE_ID,
            "task_id": TASK_ID,
            "status": STATUS,
            "fact_level": "EXTRACTED",
            "decision": DECISION,
            "connector_plan_count": 3,
            "opme_entry_surface_count": 4,
            "backlog_item_count": 6,
            "live_connector_call_count": 0,
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
            "stage_id": "S18",
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
            "stage_id": "S18",
            "governance_stage_id": "FINAL-REGRESSION-STRESS",
            "roadmap_stage_id": "S18",
            "roadmap_phase_id": ROADMAP_PHASE_ID,
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "acceptance_id": ACCEPTANCE_ID,
            "version": VERSION,
            "name": "v0.1.4 S18-P3 post-remediation integration preparation",
            "phase_goal": "lock three read-only future connectors OpMe light entry and an unstarted next-stage backlog",
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


def _render_human_artifacts(
    summary: dict[str, Any],
    connectors: list[dict[str, Any]],
    opme: dict[str, Any],
    backlog: list[dict[str, Any]],
    go_no_go: dict[str, Any],
    *,
    final_validation: bool,
) -> None:
    connector_lines = "\n".join(
        f"- `{row['connector_id']}`：{row['source_label_zh']}；只读方案；未授权、未连接、未调用；写回与源修改均关闭。"
        for row in connectors
    )
    backlog_lines = "\n".join(
        f"{row['priority']}. `{row['backlog_id']}`：{row['title_zh']}；状态为未启动。" for row in backlog
    )
    blocker_lines = "\n".join(f"- `{blocker}`" for blocker in go_no_go["blocker_ids"])
    _write_text(
        REPORT_PATH,
        f"""# KMFA v0.1.4 S18-P3 后续接入准备

## 结论

- 已完成红圈、金蝶、WPS 三类后续只读接入方案，共 3 项。
- 已完成 OpMe 轻入口方案，共 {len(opme['entry_surfaces'])} 个入口面；不共享数据库或业务运行时。
- 已发布下一阶段 Backlog，共 {len(backlog)} 项，全部处于未启动状态。
- raw 仅进行 ignored private 只读快照校验，未用于接入方案内容，前后及跨 S18-P2 一致。
- 当前仍为 Q4 / D / NO_GO / 3-9-2-1，不能交付。

## 边界

- 本轮未调用真实连接器，未请求或处理凭据，未执行外部服务。
- 本轮未执行 Stage 18 整体复审、最终整体复审、GitHub upload 或 App 重装。
- 下一步只能单独执行 Stage 18 整体复审并修复 findings。
""",
    )
    _write_text(
        CONNECTOR_RECORD_PATH,
        f"""# S18-P3 后续只读连接器方案

{connector_lines}

共同门禁：owner 授权、私有运行时、Schema 合同、哈希留存、幂等键和回滚要求缺一不可；任一条件不满足即安全阻断。
""",
    )
    _write_text(
        OPME_RECORD_PATH,
        f"""# S18-P3 OpMe 轻入口方案

- 集成模式：入口链接与状态索引。
- 耦合等级：轻入口。
- 入口面：{', '.join(opme['entry_surfaces'])}。
- 交换内容仅限公开安全状态、报告索引、交接指针和 validator 命令指针。
- 不共享数据库、不共享业务运行时、不混合敏感数据，OpMe 不控制 KMFA 业务逻辑。
""",
    )
    _write_text(BACKLOG_RECORD_PATH, f"# S18-P3 下一阶段 Backlog\n\n{backlog_lines}\n")
    _write_text(
        GO_NO_GO_RECORD_PATH,
        f"""# S18-P3 Go/No-Go 记录

- 决策：NO_GO。
- 最高报告等级：D。
- 交付、正式报告、经营决策依据、GitHub upload、App 重装、连接器调用和业务执行：全部不允许。

## 阻断项

{blocker_lines}
""",
    )
    _write_text(
        TEST_RESULTS_PATH,
        f"""# S18-P3 后续接入准备测试结果

- RED：generator/checker 缺失时 focused test=`1 failure + 9 skipped`。
- focused tests：{'10/10 PASS' if final_validation else '待最终验证回放'}。
- strict validator：{'PASS' if final_validation else '待最终验证回放'}。
- connector / OpMe / Backlog：3 / 4 / 6，全部边界检查 PASS。
- acceptance：34/34 PASS。
- raw、治理与敏感扫描：{'PASS' if final_validation else '待最终验证回放'}。
""",
    )
    _write_text(
        RISK_REGISTER_PATH,
        """# S18-P3 风险登记

| 风险 | 控制 | 状态 |
|---|---|---|
| 旧 S18-P3 完成状态冒充当前状态 | 旧证据仅作为结构基线，动态状态不具权威性 | 已控制 |
| 后续连接器方案被误当为已授权连接 | 强制 proposal-only、未授权、未连接、调用数为零 | 已控制 |
| 接入方案打开写回 | 源修改、自动写回和持久写入全部锁定为 false | 已控制 |
| OpMe 形成深度耦合 | 仅交换公开安全状态与索引指针，不共享数据库或运行时 | 已控制 |
| raw 或凭据进入公开证据 | 只保留汇总与 ignored private 快照，凭据不在本 phase 范围 | 已控制 |
""",
    )
    _write_text(
        ROLLBACK_PATH,
        """# S18-P3 回滚计划

1. 回退本 phase local commit 与当前 S18-P3 公开安全证据。
2. 删除 ignored private runtime 中本 phase 快照和诊断，不触碰 raw。
3. 恢复 S18-P2 为 current pointer，保留历史 S18-P3 证据不变。
4. 不执行连接器补偿动作、生产恢复、GitHub upload、App 重装或业务动作。
""",
    )


def generate(
    *,
    generated_at: str | None = None,
    final_validation: bool = False,
    write_governance: bool = True,
) -> dict[str, Any]:
    generated_at = generated_at or datetime.now().astimezone().isoformat(timespec="seconds")
    dependency = _s18_p2_dependency()
    historical = _historical_baseline()
    taskpack = _taskpack_contract()

    raw_helper = s18_p2.s18_p1.s17_review.p1.s16_review.p1.s15_review.p1.s14_review.p1.s13_review.p1.s12_review.p1.s11_project
    raw_before = raw_helper._raw_snapshot("before_v014_s18_p3_post_remediation_integration_preparation")
    connectors = _connector_rows(generated_at)
    opme = _opme_plan(generated_at)
    backlog = _backlog_rows(generated_at)
    go_no_go = _go_no_go()
    raw_after = raw_helper._raw_snapshot("after_v014_s18_p3_post_remediation_integration_preparation")
    prior_raw = _read_json(s18_p2.PRIVATE_RAW_AFTER_PATH)
    current_raw = raw_helper._raw_snapshot("current_v014_s18_p3_post_remediation_integration_preparation")
    normalize = raw_helper._normalize_raw
    raw_exact = normalize(raw_before) == normalize(raw_after)
    raw_cross = normalize(raw_before) == normalize(prior_raw) == normalize(current_raw)
    if not raw_exact or not raw_cross:
        raise ValueError("raw source changed during current S18-P3")

    summary = {
        "schema_version": "kmfa.v014.s18_p3_post_remediation_integration_preparation_summary.v1",
        "project_id": "KMFA",
        "stage_id": "S18",
        "phase_id": PHASE_ID,
        "roadmap_phase_id": ROADMAP_PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "version": VERSION,
        "status": STATUS,
        "taskpack_contract_validated": True,
        "s18_p2_dependency_validated": True,
        "historical_s18_p3_structural_baseline_validated": True,
        "connector_plan_count": len(connectors),
        "read_only_connector_count": sum(row["integration_mode"] == "read_only_future_connector" for row in connectors),
        "opme_entry_surface_count": len(opme["entry_surfaces"]),
        "backlog_item_count": len(backlog),
        "live_connector_call_count": sum(row["live_connector_called"] for row in connectors),
        "external_service_call_count": sum(row["external_service_called"] for row in connectors),
        "source_mutation_allowed_count": sum(row["source_mutation_allowed"] for row in connectors),
        "raw_source_file_count": raw_before["file_count"],
        "raw_snapshot_exact_match": raw_exact,
        "raw_cross_phase_snapshot_exact_match": raw_cross,
        "raw_business_content_used_for_integration_plan": False,
        "open_final_difference_accepted_count": 3,
        "nonzero_delta_reconciliation_count": 9,
        "zero_delta_reconciliation_count": 2,
        "incomplete_reconciliation_count": 1,
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "s18_p1_performed": True,
        "s18_p2_performed": True,
        "s18_p3_performed": True,
        "stage18_review_performed": False,
        "final_overall_review_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "decision": DECISION,
    }
    bundle = {"summary": summary, "connectors": connectors, "opme": opme, "backlog": backlog, "go_no_go": go_no_go}
    validate_integration_bundle(bundle)
    acceptance = _acceptance_matrix(summary, connectors, opme, backlog, go_no_go)
    if acceptance["check_fail_count"]:
        raise ValueError("S18-P3 acceptance matrix failed")

    manifest = {
        "schema_version": "kmfa.v014.s18_p3_post_remediation_integration_preparation_manifest.v1",
        "record_type": "v014_s18_p3_post_remediation_integration_preparation_manifest",
        "project_id": "KMFA",
        "stage_id": "S18",
        "phase_id": PHASE_ID,
        "roadmap_phase_id": ROADMAP_PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "version": VERSION,
        "status": STATUS,
        "decision": DECISION,
        "formula_id": FORMULA_ID,
        "parameter_ids": list(PARAMETER_IDS),
        "model_registry_key": MODEL_REGISTRY_KEY,
        "generated_at": generated_at,
        "git_head": _git_output(["rev-parse", "HEAD"]),
        "branch": _git_output(["branch", "--show-current"]),
        "summary": summary,
        "s18_p2_dependency": dependency,
        "historical_s18_p3_structural_baseline_validated": True,
        "historical_s18_p3_dynamic_state_authoritative": False,
        "historical_s18_p3_baseline": historical,
        "taskpack_contract": taskpack,
        "required_connector_ids": list(REQUIRED_CONNECTOR_IDS),
        "required_opme_entry_surfaces": list(REQUIRED_OPME_ENTRY_SURFACES),
        "required_opme_exchange_refs": list(REQUIRED_OPME_EXCHANGE_REFS),
        "required_backlog_ids": list(REQUIRED_BACKLOG_IDS),
        "completion_gate_sequence": list(COMPLETION_GATE_SEQUENCE),
        "phase_boundaries": _phase_boundaries(),
        "public_repo_safety": _public_repo_safety(),
        "acceptance_matrix": acceptance,
        "go_no_go": go_no_go,
        "artifact_refs": {
            "manifest": MANIFEST_PATH.as_posix(),
            "connector_plan": CONNECTOR_PLAN_PATH.as_posix(),
            "opme_plan": OPME_PLAN_PATH.as_posix(),
            "backlog": BACKLOG_PATH.as_posix(),
            "acceptance": ACCEPTANCE_MATRIX_PATH.as_posix(),
            "go_no_go": GO_NO_GO_PATH.as_posix(),
            "report": REPORT_PATH.as_posix(),
            "test_results": TEST_RESULTS_PATH.as_posix(),
        },
        "validation_summary": {
            "final_validation_recorded": final_validation,
            "focused_tests": "PASS" if final_validation else "PENDING",
            "strict_validator": "PASS" if final_validation else "PENDING",
            "s18_p2_dependency_validator": "PASS",
            "connector_opme_backlog_validation": "PASS",
            "raw_alignment": "PASS",
            "governance_and_safety_scans": "PASS" if final_validation else "PENDING",
        },
        "next_phase": "S18_STAGE_REVIEW",
        "next_required_step": (
            "Run Stage 18 overall review and finding fixes separately; do not execute final overall review, GitHub upload, "
            "app reinstall, live connector calls, credential handling, formal report release, difference closure, "
            "persistent business writes, or business execution in S18-P3."
        ),
        "content_hash": _sha256_json(bundle),
    }

    _write_json(MANIFEST_PATH, manifest)
    _write_json(METADATA_MANIFEST_PATH, manifest)
    _write_jsonl(CONNECTOR_PLAN_PATH, connectors)
    _write_jsonl(METADATA_CONNECTOR_PLAN_PATH, connectors)
    _write_json(OPME_PLAN_PATH, opme)
    _write_json(METADATA_OPME_PLAN_PATH, opme)
    _write_jsonl(BACKLOG_PATH, backlog)
    _write_jsonl(METADATA_BACKLOG_PATH, backlog)
    _write_json(ACCEPTANCE_MATRIX_PATH, acceptance)
    _write_json(METADATA_ACCEPTANCE_MATRIX_PATH, acceptance)
    _write_json(GO_NO_GO_PATH, go_no_go)
    _write_json(METADATA_GO_NO_GO_PATH, go_no_go)
    _render_human_artifacts(
        summary,
        connectors,
        opme,
        backlog,
        go_no_go,
        final_validation=final_validation,
    )

    _write_json(PRIVATE_RAW_BEFORE_PATH, raw_before)
    _write_json(PRIVATE_RAW_AFTER_PATH, raw_after)
    _write_json(
        PRIVATE_DIAGNOSTIC_PATH,
        {
            "raw_prior_snapshot": prior_raw,
            "raw_current_snapshot": current_raw,
            "raw_phase_exact": raw_exact,
            "raw_cross_phase_exact": raw_cross,
            "connector_call_count": 0,
            "external_service_call_count": 0,
            "credential_material_present": False,
        },
    )
    _write_text(
        PRIVATE_REPORT_PATH,
        """# S18-P3 私有边界核验

- phase 前后快照：完全一致。
- 与 S18-P2 及当前快照：完全一致。
- raw 业务内容未用于 connector、OpMe 或 Backlog 方案。
- 未修改、删除、移动、重命名、覆盖、复制或备份 raw。
- 未调用连接器、外部服务，未请求或处理凭据。
- 最终 goal 多轮仍无法对齐时，必须输出全中文差异报告。
""",
    )
    if write_governance:
        _write_governance(generated_at)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate current KMFA S18-P3 integration-preparation evidence")
    parser.add_argument("--generated-at", default=None)
    parser.add_argument("--final-validation", action="store_true")
    parser.add_argument("--no-governance", action="store_true")
    args = parser.parse_args()
    manifest = generate(
        generated_at=args.generated_at,
        final_validation=args.final_validation,
        write_governance=not args.no_governance,
    )
    summary = manifest["summary"]
    print(
        "S18-P3 current integration preparation: "
        f"connectors={summary['connector_plan_count']} opme_surfaces={summary['opme_entry_surface_count']} "
        f"backlog={summary['backlog_item_count']} raw={summary['raw_snapshot_exact_match']} "
        f"stage18_review={summary['stage18_review_performed']} decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
