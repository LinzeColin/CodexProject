#!/usr/bin/env python3
"""Generate KMFA v0.1.4 S17-P3 operations SOP evidence.

This phase locks public-safe operations runbooks, finance SOP knowledge-index
entries, and metadata-only error/backup drill logs. It does not read raw
private inbox content, perform production restore, invoke external services,
enter Stage 17 review, upload to GitHub, release a formal report, reinstall
an app, or execute business actions.
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

from KMFA.tools.check_v014_s17_p2_notification_policy import (  # noqa: E402
    validate_v014_s17_p2_notification_policy,
)
from KMFA.tools.operations_sop import (  # noqa: E402
    POLICY_VERSION as LEGACY_S17_P3_POLICY_VERSION,
    REQUIRED_DRILL_TYPES,
    REQUIRED_KNOWLEDGE_ITEM_TYPES,
    REQUIRED_RUNBOOK_TYPES,
    build_default_operations_sop,
    validate_operations_sop_artifacts,
)


TASK_ID = "KMFA-V014-S17-P3-OPERATIONS-SOP-20260705"
ACCEPTANCE_ID = "ACC-V014-S17-P3-OPERATIONS-SOP"
SCHEMA_VERSION = "kmfa.v014_s17_p3_operations_sop.v1"
PHASE_SCOPE = "v014_s17_p3_operations_sop_only"
POLICY_LOCK_VERSION = "LOCK-KMFA-V014-S17P3-OPERATIONS-SOP-PUBLIC-SAFE-001"
FORMULA_ID = "FORM-KMFA-V014-S17P3-OPERATIONS-SOP-001"
MAPPING_VERSION = "MAP-KMFA-V014-S17P3-OPERATIONS-SOP-v1"

REQUIRED_V014_RUNBOOK_TYPES = REQUIRED_RUNBOOK_TYPES
REQUIRED_V014_KNOWLEDGE_ITEM_TYPES = REQUIRED_KNOWLEDGE_ITEM_TYPES
REQUIRED_V014_DRILL_TYPES = REQUIRED_DRILL_TYPES

OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_S17_P3_OPERATIONS_SOP")
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
METADATA_DIR = Path("KMFA/metadata/operations")

MANIFEST_PATH = MACHINE_DIR / "operations_sop_manifest.json"
RUNBOOK_LOCK_PATH = MACHINE_DIR / "operations_runbook_lock.jsonl"
KNOWLEDGE_INDEX_PATH = MACHINE_DIR / "finance_sop_knowledge_index_lock.jsonl"
DRILL_LOG_PATH = MACHINE_DIR / "error_backup_drill_log.jsonl"
METADATA_MANIFEST_PATH = METADATA_DIR / "v014_s17_p3_operations_sop_manifest.json"
METADATA_RUNBOOKS_PATH = METADATA_DIR / "v014_s17_p3_operations_runbooks.jsonl"
METADATA_KNOWLEDGE_INDEX_PATH = METADATA_DIR / "v014_s17_p3_finance_sop_knowledge_index.jsonl"
METADATA_DRILL_LOG_PATH = METADATA_DIR / "v014_s17_p3_error_backup_drill_log.jsonl"

REPORT_PATH = HUMAN_DIR / "operations_sop_report.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

V14_TASKPACK_PATH = Path("KMFA/taskpack/v1_4/taskpack/01_KMFA_Codex_TaskPack_v1_4_public_safe.md")
V14_ROADMAP_PATH = Path("KMFA/taskpack/v1_4/roadmap/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_4.md")
RAW_INBOX_REF = "operator-designated raw/private inbox outside repository"
NEXT_PHASE = "S17_STAGE_REVIEW"
NEXT_REQUIRED_STEP = (
    "Proceed to v0.1.4 Stage 17 overall review as a separate run only after user instruction. "
    "Do not perform GitHub upload, S18, app reinstall, raw inbox access, production restore, external "
    "service calls, formal report release, full report email body, or business execution in S17-P3."
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


def write_test_results_placeholder() -> None:
    if TEST_RESULTS_PATH.exists():
        existing = TEST_RESULTS_PATH.read_text(encoding="utf-8")
        if (
            "focused v0.1.4 S17-P3 unit test: PASS" in existing
            and "scoped S17-P3 public artifact boundary scan: PASS" in existing
        ):
            return
    write_text(
        TEST_RESULTS_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 S17-P3 Operations SOP Test Results",
                "",
                "- generator: pending final validation replay",
                "- validator: pending final validation replay",
                "- focused_unittest: pending final validation replay",
                "- governance_validation: pending final validation replay",
                "- raw_secret_scan: pending final validation replay",
                "",
            ]
        ),
    )


def validate_s17_p2_dependency() -> dict[str, Any]:
    result = validate_v014_s17_p2_notification_policy()
    if result.get("stage_id") != "S17" or result.get("phase_id") != "S17-P2":
        raise RuntimeError("S17-P3 requires validated v0.1.4 S17-P2 evidence")
    if result.get("next_phase") != "S17-P3":
        raise RuntimeError("S17-P2 must route to S17-P3")
    progress = result.get("stage17_phase_progress", {})
    if progress.get("s17_p1_performed") is not True or progress.get("s17_p2_performed") is not True:
        raise RuntimeError("S17-P3 requires completed S17-P1 and S17-P2")
    if progress.get("s17_p3_performed") is not False:
        raise RuntimeError("S17-P2 dependency must not already include S17-P3")
    if result.get("github_upload", {}).get("github_upload_performed") is not False:
        raise RuntimeError("v1.4 GitHub upload must remain deferred")
    return result


def validate_legacy_s17_p3_artifacts() -> tuple[
    dict[str, Any],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    artifacts = build_default_operations_sop(generated_at="2026-07-05T15:20:00+10:00")
    validate_operations_sop_artifacts(*artifacts)
    return artifacts


def load_v14_taskpack_baseline() -> dict[str, Any]:
    taskpack_text = V14_TASKPACK_PATH.read_text(encoding="utf-8")
    roadmap_text = V14_ROADMAP_PATH.read_text(encoding="utf-8")
    for token in (
        "运维与SOP",
        "导入、复核、发布、回滚操作手册",
        "财务SOP和交接材料进入知识索引",
        "错误处理和备份恢复演练",
    ):
        if token not in roadmap_text:
            raise RuntimeError(f"v1.4 roadmap missing S17-P3 marker {token}")
    for token in ("不提交原始敏感数据到公开GitHub", "不把缺数据报告伪装成完整报告", "可审计"):
        if token not in taskpack_text:
            raise RuntimeError(f"v1.4 taskpack missing S17-P3 safety marker {token}")
    return {
        "taskpack_read": True,
        "roadmap_read": True,
        "roadmap_includes_s17_p3_requirements": True,
        "taskpack_includes_operations_safety_boundary": True,
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
        "office_workbook_committed": False,
        "source_document_committed": False,
        "raw_or_private_table_committed": False,
        "local_database_committed": False,
        "auth_material_committed": False,
        "connector_auth_material_committed": False,
        "field_plaintext_committed": False,
        "source_header_plaintext_committed": False,
        "raw_file_names_committed": False,
        "raw_file_hashes_committed": False,
        "source_record_payload_committed": False,
        "normalized_source_values_committed": False,
        "business_numeric_payload_committed": False,
        "project_or_customer_plaintext_committed": False,
        "private_sop_document_committed": False,
        "backup_archive_committed": False,
        "production_restore_payload_committed": False,
        "business_decision_basis_committed": False,
    }


def _quality_gate() -> dict[str, Any]:
    return {
        "operation_runbooks_complete": True,
        "finance_sop_indexed": True,
        "handoff_materials_indexed": True,
        "error_handling_drill_recorded": True,
        "backup_recovery_drill_recorded": True,
        "metadata_only": True,
        "manual_execution_only": True,
        "append_only_required": True,
        "raw_payload_allowed": False,
        "private_document_allowed": False,
        "live_connector_allowed": False,
        "external_service_call_allowed": False,
        "production_restore_allowed": False,
        "formal_report_allowed": False,
        "full_report_email_allowed": False,
        "business_decision_basis_allowed": False,
        "business_execution_allowed": False,
        "automatic_payment_allowed": False,
        "bank_operation_allowed": False,
        "invoice_issue_allowed": False,
        "tax_formal_action_allowed": False,
        "legal_collection_allowed": False,
        "salary_action_allowed": False,
        "lineage_full_check_allowed": False,
        "stage17_review_allowed": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "phase_completion_upload_allowed": False,
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "release_permission": "blocked",
        "release_block_reason": "s17_p3_is_local_public_safe_operations_sop_only",
    }


def _phase_boundaries() -> dict[str, bool]:
    return {
        "s17_p2_dependency_reused": True,
        "legacy_s17_p3_public_safe_baseline_reused": True,
        "s17_p3_operations_scope_included": True,
        "s17_p1_access_security_scope_included": False,
        "s17_p2_notification_scope_included": False,
        "stage17_review_scope_included": False,
        "github_upload_scope_included": False,
        "s18_scope_included": False,
        "production_restore_scope_included": False,
        "external_connector_scope_included": False,
        "live_connector_scope_included": False,
        "app_reinstall_scope_included": False,
        "formal_report_runtime_scope_included": False,
        "full_report_email_body_scope_included": False,
        "business_execution_scope_included": False,
        "raw_inbox_access_scope_included": False,
    }


def _github_upload() -> dict[str, Any]:
    return {
        "github_upload_performed": False,
        "github_upload_ready_next_gate": False,
        "github_upload_deferred_until_v014_stage1_18_complete": True,
        "github_upload_status": "not_uploaded_deferred_until_v014_stage1_18_complete",
    }


def _runbook_locks(
    legacy_runbooks: list[dict[str, Any]],
    generated_at: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for legacy in legacy_runbooks:
        runbook_type = str(legacy["runbook_type"])
        rows.append(
            {
                "record_type": "v014_s17_p3_operation_runbook_lock",
                "project_id": "KMFA",
                "version": "0.1.4",
                "stage_id": "S17",
                "phase_id": "S17-P3",
                "task_id": "S17P3T01",
                "lock_version": POLICY_LOCK_VERSION,
                "mapping_version": MAPPING_VERSION,
                "generated_at": generated_at,
                "runbook_id": f"v014_s17p3_operation_runbook_{runbook_type}",
                "runbook_type": runbook_type,
                "owner_role": legacy["owner_role"],
                "execution_mode": "manual_sop_only",
                "precheck_required": True,
                "precheck_ref": legacy["precheck_ref"],
                "primary_step_ref": legacy["primary_step_ref"],
                "rollback_step_ref": legacy["rollback_step_ref"],
                "append_only": True,
                "metadata_target": METADATA_RUNBOOKS_PATH.as_posix(),
                "evidence_ref": RUNBOOK_LOCK_PATH.as_posix(),
                "source_baseline_ref": legacy["evidence_ref"],
                "raw_business_data_required": False,
                "private_document_required": False,
                "live_connector_required": False,
                "external_service_required": False,
                "production_restore_allowed": False,
                "business_execution_allowed": False,
                "formal_report_release_allowed": False,
                "stage_review_allowed": False,
                "github_upload_allowed": False,
            }
        )
    return rows


def _knowledge_locks(
    legacy_items: list[dict[str, Any]],
    generated_at: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for legacy in legacy_items:
        item_type = str(legacy["item_type"])
        rows.append(
            {
                "record_type": "v014_s17_p3_operations_knowledge_index_lock",
                "project_id": "KMFA",
                "version": "0.1.4",
                "stage_id": "S17",
                "phase_id": "S17-P3",
                "task_id": "S17P3T02",
                "lock_version": POLICY_LOCK_VERSION,
                "mapping_version": MAPPING_VERSION,
                "generated_at": generated_at,
                "knowledge_item_id": f"v014_s17p3_operations_knowledge_{item_type}",
                "item_type": item_type,
                "owner_role": legacy["owner_role"],
                "storage_mode": "public_safe_index_only",
                "knowledge_ref": legacy["knowledge_ref"],
                "handoff_required": True,
                "append_only": True,
                "metadata_target": METADATA_KNOWLEDGE_INDEX_PATH.as_posix(),
                "evidence_ref": KNOWLEDGE_INDEX_PATH.as_posix(),
                "private_document_committed": False,
                "raw_business_data_committed": False,
                "credential_material_committed": False,
                "business_decision_basis_allowed": False,
                "external_service_required": False,
                "production_restore_allowed": False,
                "github_upload_allowed": False,
            }
        )
    return rows


def _drill_locks(
    legacy_drills: list[dict[str, Any]],
    generated_at: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for legacy in legacy_drills:
        drill_type = str(legacy["drill_type"])
        rows.append(
            {
                "record_type": "v014_s17_p3_operations_drill_log",
                "project_id": "KMFA",
                "version": "0.1.4",
                "stage_id": "S17",
                "phase_id": "S17-P3",
                "task_id": "S17P3T03",
                "lock_version": POLICY_LOCK_VERSION,
                "mapping_version": MAPPING_VERSION,
                "generated_at": generated_at,
                "drill_id": f"v014_s17p3_operations_drill_{drill_type}",
                "drill_type": drill_type,
                "scenario_ref": legacy["scenario_ref"],
                "execution_mode": "metadata_drill_only",
                "result_status": "simulated_passed",
                "recovery_evidence_ref": DRILL_LOG_PATH.as_posix(),
                "append_only": True,
                "metadata_target": METADATA_DRILL_LOG_PATH.as_posix(),
                "evidence_ref": DRILL_LOG_PATH.as_posix(),
                "production_restore_executed": False,
                "raw_business_data_required": False,
                "private_document_required": False,
                "external_service_called": False,
                "live_connector_called": False,
                "business_execution_allowed": False,
                "github_upload_allowed": False,
            }
        )
    return rows


def _summary(
    runbooks: list[dict[str, Any]],
    knowledge_items: list[dict[str, Any]],
    drill_logs: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "operation_runbook_count": len(runbooks),
        "knowledge_item_count": len(knowledge_items),
        "drill_log_count": len(drill_logs),
        "runbook_type_count": len({row["runbook_type"] for row in runbooks}),
        "knowledge_item_type_count": len({row["item_type"] for row in knowledge_items}),
        "drill_type_count": len({row["drill_type"] for row in drill_logs}),
        "production_restore_count": sum(1 for row in drill_logs if row["production_restore_executed"]),
        "external_service_call_count": sum(1 for row in drill_logs if row["external_service_called"]),
        "live_connector_call_count": sum(1 for row in drill_logs if row["live_connector_called"]),
        "business_execution_count": 0,
        "raw_inbox_access_count": 0,
        "formal_report_count": 0,
        "app_reinstall_count": 0,
        "report_grade_visible": "D",
    }


def build_manifest(generated_at: str | None = None) -> tuple[
    dict[str, Any],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    generated_at = generated_at or datetime.now().replace(microsecond=0).isoformat()
    s17_p2 = validate_s17_p2_dependency()
    legacy_manifest, legacy_runbooks, legacy_items, legacy_drills = validate_legacy_s17_p3_artifacts()
    baseline = load_v14_taskpack_baseline()
    runbooks = _runbook_locks(legacy_runbooks, generated_at)
    knowledge_items = _knowledge_locks(legacy_items, generated_at)
    drill_logs = _drill_locks(legacy_drills, generated_at)
    summary = _summary(runbooks, knowledge_items, drill_logs)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "v014_s17_p3_operations_sop_manifest",
        "project_id": "KMFA",
        "version": "0.1.4",
        "stage_id": "S17",
        "phase_id": "S17-P3",
        "phase_scope": PHASE_SCOPE,
        "task_id": TASK_ID,
        "acceptance_ids": [ACCEPTANCE_ID],
        "completed_task_ids": ["S17P3T01", "S17P3T02", "S17P3T03"],
        "status": "completed_validated_local_only_no_go_upload_deferred_operations_sop_locked",
        "generated_at": generated_at,
        "branch": git_output(["branch", "--show-current"]),
        "git_head": git_output(["rev-parse", "HEAD"]),
        "s17_p2_dependency_validated": True,
        "s17_p2_dependency_task_id": s17_p2["task_id"],
        "historical_s17_p3_public_safe_baseline_validated": True,
        "historical_s17_p3_policy_version": legacy_manifest["policy_version"],
        "v14_taskpack_baseline": baseline,
        "required_runbook_types": list(REQUIRED_V014_RUNBOOK_TYPES),
        "required_knowledge_item_types": list(REQUIRED_V014_KNOWLEDGE_ITEM_TYPES),
        "required_drill_types": list(REQUIRED_V014_DRILL_TYPES),
        "operations_sop_summary": summary,
        "stage17_phase_progress": {
            "completed_phase_count": 3,
            "total_phase_count": 3,
            "derived_percent_bps": 10000,
            "derived_percent_label": "100.00%",
            "s17_p1_performed": True,
            "s17_p2_performed": True,
            "s17_p3_performed": True,
            "stage17_review_performed": False,
        },
        "quality_gate": _quality_gate(),
        "phase_boundaries": _phase_boundaries(),
        "raw_data_boundary": _raw_boundary(),
        "public_repo_safety": _public_repo_safety(),
        "metadata_outputs": {
            "manifest": METADATA_MANIFEST_PATH.as_posix(),
            "runbooks": METADATA_RUNBOOKS_PATH.as_posix(),
            "knowledge_index": METADATA_KNOWLEDGE_INDEX_PATH.as_posix(),
            "drill_log": METADATA_DRILL_LOG_PATH.as_posix(),
        },
        "evidence_refs": {
            "human_report": REPORT_PATH.as_posix(),
            "test_results": TEST_RESULTS_PATH.as_posix(),
            "risk_register": RISK_REGISTER_PATH.as_posix(),
            "rollback_plan": ROLLBACK_PATH.as_posix(),
            "machine_manifest": MANIFEST_PATH.as_posix(),
            "runbook_lock": RUNBOOK_LOCK_PATH.as_posix(),
            "knowledge_index": KNOWLEDGE_INDEX_PATH.as_posix(),
            "drill_log": DRILL_LOG_PATH.as_posix(),
            "validator": "KMFA/tools/check_v014_s17_p3_operations_sop.py",
            "focused_test": "KMFA/tests/test_v014_s17_p3_operations_sop.py",
        },
        "github_upload": _github_upload(),
        "next_phase": NEXT_PHASE,
        "next_required_step": NEXT_REQUIRED_STEP,
        "fact_level": "EXTRACTED",
    }
    return manifest, runbooks, knowledge_items, drill_logs


def write_artifacts(
    manifest: dict[str, Any],
    runbooks: list[dict[str, Any]],
    knowledge_items: list[dict[str, Any]],
    drill_logs: list[dict[str, Any]],
) -> None:
    write_json(MANIFEST_PATH, manifest)
    write_jsonl(RUNBOOK_LOCK_PATH, runbooks)
    write_jsonl(KNOWLEDGE_INDEX_PATH, knowledge_items)
    write_jsonl(DRILL_LOG_PATH, drill_logs)
    write_json(METADATA_MANIFEST_PATH, manifest)
    write_jsonl(METADATA_RUNBOOKS_PATH, runbooks)
    write_jsonl(METADATA_KNOWLEDGE_INDEX_PATH, knowledge_items)
    write_jsonl(METADATA_DRILL_LOG_PATH, drill_logs)

    summary = manifest["operations_sop_summary"]
    write_text(
        REPORT_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 S17-P3 Operations SOP Report",
                "",
                f"- task_id: `{TASK_ID}`",
                f"- acceptance_id: `{ACCEPTANCE_ID}`",
                f"- status: `{manifest['status']}`",
                f"- operation_runbook_count: `{summary['operation_runbook_count']}`",
                f"- knowledge_item_count: `{summary['knowledge_item_count']}`",
                f"- drill_log_count: `{summary['drill_log_count']}`",
                f"- production_restore_count: `{summary['production_restore_count']}`",
                f"- external_service_call_count: `{summary['external_service_call_count']}`",
                f"- live_connector_call_count: `{summary['live_connector_call_count']}`",
                f"- business_execution_count: `{summary['business_execution_count']}`",
                f"- raw_inbox_access_count: `{summary['raw_inbox_access_count']}`",
                f"- report_grade_visible: `{summary['report_grade_visible']}`",
                "- GitHub upload: `deferred_until_v014_stage1_18_complete`",
                "",
                "This phase is public-safe and local-only. It records manual operations SOP metadata, finance knowledge-index refs, and metadata-only drill logs without production restore, external service calls, raw inbox access, formal report release, or business execution.",
                "",
            ]
        ),
    )
    write_test_results_placeholder()
    write_text(
        RISK_REGISTER_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 S17-P3 Operations SOP Risk Register",
                "",
                "- risk: Public-safe SOP metadata could be mistaken for production execution.",
                "  mitigation: All runbooks use manual_sop_only and all drills use metadata_drill_only; restore and business execution counts remain zero.",
                "- risk: Knowledge-index refs could be mistaken for private SOP documents.",
                "  mitigation: Storage mode is public_safe_index_only and private documents are blocked from public evidence.",
                "",
            ]
        ),
    )
    write_text(
        ROLLBACK_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 S17-P3 Operations SOP Rollback Plan",
                "",
                "- Remove only `KMFA/stage_artifacts/V014_S17_P3_OPERATIONS_SOP/` and `KMFA/metadata/operations/v014_s17_p3_*` if rollback is required.",
                "- Remove paired v014 S17-P3 governance entries only after confirming no later phase depends on them.",
                "- Do not touch raw/private inbox contents or production runtime state.",
                "",
            ]
        ),
    )


def generate(generated_at: str | None = None) -> dict[str, Any]:
    manifest, runbooks, knowledge_items, drill_logs = build_manifest(generated_at=generated_at)
    write_artifacts(manifest, runbooks, knowledge_items, drill_logs)
    return manifest


def main() -> int:
    manifest = generate()
    summary = manifest["operations_sop_summary"]
    print(
        "PASS: KMFA v0.1.4 S17-P3 operations SOP generated "
        f"(runbooks={summary['operation_runbook_count']}, knowledge={summary['knowledge_item_count']}, "
        f"drills={summary['drill_log_count']}, production_restore={summary['production_restore_count']}, "
        f"external_service={summary['external_service_call_count']}, business_execution={summary['business_execution_count']}, "
        f"raw_inbox_access={summary['raw_inbox_access_count']}, "
        f"stage17_review={manifest['stage17_phase_progress']['stage17_review_performed']}, "
        f"github_upload={manifest['github_upload']['github_upload_performed']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
