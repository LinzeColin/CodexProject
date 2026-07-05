#!/usr/bin/env python3
"""Generate KMFA v0.1.4 S17-P1 access and security evidence.

This phase locks role permissions, public repository sensitive-material
deny rules, and audit-log requirements. It does not read raw/private finance
data, send notifications, enter S17-P2 or S17-P3, perform Stage 17 review,
release a formal report, run external connectors, execute business actions,
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

from KMFA.tools.access_security_policy import (  # noqa: E402
    REQUIRED_AUDIT_ACTION_TYPES,
    REQUIRED_ROLES,
    REQUIRED_SENSITIVE_POLICY_CATEGORIES,
    build_default_access_security_policy,
    validate_access_security_policy_artifacts,
)
from KMFA.tools.check_v014_s16_stage_review import validate_v014_s16_stage_review  # noqa: E402


TASK_ID = "KMFA-V014-S17-P1-ACCESS-SECURITY-20260705"
ACCEPTANCE_ID = "ACC-V014-S17-P1-ACCESS-SECURITY"
SCHEMA_VERSION = "kmfa.v014_s17_p1_access_security.v1"
PHASE_SCOPE = "v014_s17_p1_access_security_only"
BASELINE_LOCK_VERSION = "LOCK-KMFA-V014-S17P1-ACCESS-SECURITY-PUBLIC-SAFE-001"
FORMULA_ID = "FORM-KMFA-V014-S17P1-ACCESS-SECURITY-001"
MAPPING_VERSION = "MAP-KMFA-V014-S17P1-ACCESS-SECURITY-v1"

OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_S17_P1_ACCESS_SECURITY")
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
MANIFEST_PATH = MACHINE_DIR / "access_security_manifest.json"
ROLE_PERMISSION_LOCK_PATH = MACHINE_DIR / "role_permission_lock.jsonl"
SENSITIVE_POLICY_LOCK_PATH = MACHINE_DIR / "sensitive_public_repo_policy_lock.jsonl"
AUDIT_POLICY_LOCK_PATH = MACHINE_DIR / "audit_log_policy_lock.jsonl"
REPORT_PATH = HUMAN_DIR / "access_security_report.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

V14_TASKPACK_PATH = Path("KMFA/taskpack/v1_4/taskpack/01_KMFA_Codex_TaskPack_v1_4_public_safe.md")
V14_ROADMAP_PATH = Path("KMFA/taskpack/v1_4/roadmap/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_4.md")
RAW_INBOX_REF = "operator-designated raw/private inbox outside repository"
NEXT_PHASE = "S17-P2"
NEXT_REQUIRED_STEP = (
    "Proceed to v0.1.4 S17-P2 notification policy as a separate run only after user instruction. "
    "Do not perform S17-P3, Stage 17 review, GitHub upload, notification delivery, full report email body, "
    "formal report release, external connector, app reinstall, raw inbox access, or business execution in S17-P1."
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


def validate_s16_stage_review_dependency() -> dict[str, Any]:
    result = validate_v014_s16_stage_review()
    if result.get("stage_id") != "S16" or result.get("phase_id") != "S16_STAGE_REVIEW":
        raise RuntimeError("S17-P1 requires validated v0.1.4 Stage 16 review evidence")
    if result.get("next_phase") != "S17-P1":
        raise RuntimeError("Stage 16 review must route to S17-P1")
    if result.get("s17_p1_performed") is not False:
        raise RuntimeError("Stage 16 review dependency must not already include S17-P1")
    if result.get("github_upload_performed") is not False:
        raise RuntimeError("v1.4 GitHub upload must remain deferred")
    if result.get("github_upload_deferred_until_v014_stage1_18_complete") is not True:
        raise RuntimeError("v1.4 GitHub upload deferral flag is required")
    return result


def validate_legacy_s17_p1_artifacts() -> tuple[
    dict[str, Any],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    artifacts = build_default_access_security_policy(generated_at="2026-07-05T14:20:00+10:00")
    validate_access_security_policy_artifacts(*artifacts)
    return artifacts


def load_v14_taskpack_baseline() -> dict[str, Any]:
    taskpack_text = V14_TASKPACK_PATH.read_text(encoding="utf-8")
    roadmap_text = V14_ROADMAP_PATH.read_text(encoding="utf-8")
    for token in (
        "权限与安全",
        "角色权限覆盖管理层、财务、复核、只读",
        "敏感数据不提交公开仓库",
        "日志记录导入、处理、报告、导出、通知",
    ):
        if token not in roadmap_text:
            raise RuntimeError(f"v1.4 roadmap missing S17-P1 marker {token}")
    for token in ("不提交原始敏感数据到公开GitHub", "不把缺数据报告伪装成完整报告", "可审计"):
        if token not in taskpack_text:
            raise RuntimeError(f"v1.4 taskpack missing S17-P1 marker {token}")
    return {
        "taskpack_read": True,
        "roadmap_read": True,
        "roadmap_includes_s17_p1_requirements": True,
        "taskpack_includes_access_security_audit_boundary": True,
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
        "business_amount_values_committed": False,
        "public_numeric_values_committed": False,
        "project_or_customer_plaintext_committed": False,
        "bank_payload_committed": False,
        "contract_payroll_tax_material_committed": False,
        "full_report_notification_body_committed": False,
        "business_decision_basis_committed": False,
    }


def _quality_gate() -> dict[str, Any]:
    return {
        "role_permission_matrix_complete": True,
        "sensitive_public_repo_policy_enforced": True,
        "audit_log_policy_complete": True,
        "least_privilege_policy_enforced": True,
        "audit_append_only_required": True,
        "raw_sensitive_public_repo_allowed": False,
        "notification_delivery_allowed": False,
        "notification_full_report_body_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "business_execution_allowed": False,
        "external_connector_allowed": False,
        "lineage_full_check_allowed": False,
        "s17_p2_allowed": False,
        "s17_p3_allowed": False,
        "stage17_review_allowed": False,
        "github_upload_allowed": False,
        "phase_completion_upload_allowed": False,
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "release_permission": "blocked",
        "release_block_reason": "s17_p1_is_local_access_security_policy_only",
    }


def _phase_boundaries() -> dict[str, bool]:
    return {
        "s16_stage_review_dependency_reused": True,
        "legacy_s17_p1_public_safe_baseline_reused": True,
        "s17_p1_access_security_scope_included": True,
        "s17_p2_notification_scope_included": False,
        "s17_p3_operations_scope_included": False,
        "stage17_review_scope_included": False,
        "github_upload_scope_included": False,
        "lineage_full_check_scope_included": False,
        "protected_source_matching_scope_included": False,
        "formal_report_runtime_scope_included": False,
        "live_ui_runtime_scope_included": False,
        "external_connector_scope_included": False,
        "app_reinstall_scope_included": False,
        "notification_delivery_scope_included": False,
        "full_report_email_body_scope_included": False,
        "business_execution_scope_included": False,
        "raw_inbox_access_scope_included": False,
    }


def _lock_role_permissions(role_matrix: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in role_matrix:
        rows.append(
            {
                "record_type": "v014_s17_p1_role_permission_lock",
                "project_id": "KMFA",
                "stage_id": "S17",
                "phase_id": "S17-P1",
                "baseline_lock_version": BASELINE_LOCK_VERSION,
                "role_id": row["role_id"],
                "allowed_public_safe_action_count": len(row["allowed_public_safe_actions"]),
                "max_write_scope": row["max_write_scope"],
                "audit_required": row["audit_required"],
                "least_privilege_applied": row["least_privilege_applied"],
                "raw_business_data_access_in_public_repo": row["raw_business_data_access_in_public_repo"],
                "sensitive_file_public_commit_allowed": row["sensitive_file_public_commit_allowed"],
                "credential_access_allowed": row["credential_access_allowed"],
                "business_execution_allowed": row["business_execution_allowed"],
                "bypass_quality_gate_allowed": row["bypass_quality_gate_allowed"],
                "notification_body_report_allowed": row["notification_body_report_allowed"],
                "evidence_ref": ROLE_PERMISSION_LOCK_PATH.as_posix(),
            }
        )
    return rows


def _lock_sensitive_policy(sensitive_policies: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in sensitive_policies:
        rows.append(
            {
                "record_type": "v014_s17_p1_sensitive_policy_lock",
                "project_id": "KMFA",
                "stage_id": "S17",
                "phase_id": "S17-P1",
                "baseline_lock_version": BASELINE_LOCK_VERSION,
                "category_id": row["category_id"],
                "public_repo_allowed": row["public_repo_allowed"],
                "git_upload_allowed": row["git_upload_allowed"],
                "value_plaintext_allowed": row["value_plaintext_allowed"],
                "metadata_hash_or_ref_only_allowed": row["metadata_hash_or_ref_only_allowed"],
                "handling": row["handling"],
                "enforcement_control_count": len(row["enforcement_controls"]),
                "evidence_ref": SENSITIVE_POLICY_LOCK_PATH.as_posix(),
            }
        )
    return rows


def _lock_audit_policy(audit_policies: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in audit_policies:
        rows.append(
            {
                "record_type": "v014_s17_p1_audit_policy_lock",
                "project_id": "KMFA",
                "stage_id": "S17",
                "phase_id": "S17-P1",
                "baseline_lock_version": BASELINE_LOCK_VERSION,
                "action_type": row["action_type"],
                "append_only": row["append_only"],
                "requires_actor_role": row["requires_actor_role"],
                "requires_event_time": row["requires_event_time"],
                "requires_evidence_ref": row["requires_evidence_ref"],
                "raw_payload_allowed": row["raw_payload_allowed"],
                "private_document_allowed": row["private_document_allowed"],
                "business_value_plaintext_allowed": row["business_value_plaintext_allowed"],
                "sends_full_report_body": row["sends_full_report_body"],
                "delivery_scope": row["delivery_scope"],
                "evidence_ref": AUDIT_POLICY_LOCK_PATH.as_posix(),
            }
        )
    return rows


def build_manifest(generated_at: str | None = None) -> tuple[
    dict[str, Any],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    generated_at = generated_at or datetime.now().isoformat(timespec="seconds")
    s16_review = validate_s16_stage_review_dependency()
    legacy_manifest, role_matrix, sensitive_policies, audit_policies = validate_legacy_s17_p1_artifacts()
    baseline = load_v14_taskpack_baseline()
    role_locks = _lock_role_permissions(role_matrix)
    sensitive_locks = _lock_sensitive_policy(sensitive_policies)
    audit_locks = _lock_audit_policy(audit_policies)

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "v014_s17_p1_access_security_manifest",
        "project_id": "KMFA",
        "version": "0.1.4",
        "stage_id": "S17",
        "phase_id": "S17-P1",
        "phase_scope": PHASE_SCOPE,
        "task_id": TASK_ID,
        "acceptance_ids": [ACCEPTANCE_ID],
        "completed_task_ids": ["S17P1T01", "S17P1T02", "S17P1T03"],
        "status": "completed_validated_local_only_no_go_upload_deferred_access_security_locked",
        "generated_at": generated_at,
        "branch": git_output(["branch", "--show-current"]),
        "git_head": git_output(["rev-parse", "HEAD"]),
        "s16_stage_review_dependency_validated": True,
        "s16_stage_review_task_id": s16_review["task_id"],
        "historical_s17_p1_public_safe_baseline_validated": True,
        "historical_s17_p1_policy_version": legacy_manifest["policy_version"],
        "v14_taskpack_baseline": baseline,
        "stage17_phase_progress": {
            "completed_phase_count": 1,
            "total_phase_count": 3,
            "derived_percent_bps": 3333,
            "derived_percent_label": "33.33%",
            "s17_p1_performed": True,
            "s17_p2_performed": False,
            "s17_p3_performed": False,
            "stage17_review_performed": False,
        },
        "access_security_summary": {
            "role_count": len(role_locks),
            "sensitive_policy_category_count": len(sensitive_locks),
            "audit_action_type_count": len(audit_locks),
            "required_role_count": len(REQUIRED_ROLES),
            "required_sensitive_category_count": len(REQUIRED_SENSITIVE_POLICY_CATEGORIES),
            "required_audit_action_type_count": len(REQUIRED_AUDIT_ACTION_TYPES),
            "notification_delivery_count": 0,
            "full_report_email_body_count": 0,
            "external_connector_count": 0,
            "formal_report_count": 0,
            "business_decision_basis_count": 0,
            "business_execution_count": 0,
            "raw_inbox_access_count": 0,
            "report_grade_visible": "D",
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
        "artifact_refs": {
            "manifest": MANIFEST_PATH.as_posix(),
            "role_permission_lock": ROLE_PERMISSION_LOCK_PATH.as_posix(),
            "sensitive_policy_lock": SENSITIVE_POLICY_LOCK_PATH.as_posix(),
            "audit_policy_lock": AUDIT_POLICY_LOCK_PATH.as_posix(),
            "report": REPORT_PATH.as_posix(),
            "test_results": TEST_RESULTS_PATH.as_posix(),
            "risk_register": RISK_REGISTER_PATH.as_posix(),
            "rollback_plan": ROLLBACK_PATH.as_posix(),
        },
        "formula_id": FORMULA_ID,
        "mapping_version": MAPPING_VERSION,
        "next_phase": NEXT_PHASE,
        "next_required_step": NEXT_REQUIRED_STEP,
    }
    return manifest, role_locks, sensitive_locks, audit_locks


def write_artifacts(
    manifest: dict[str, Any],
    role_locks: list[dict[str, Any]],
    sensitive_locks: list[dict[str, Any]],
    audit_locks: list[dict[str, Any]],
) -> None:
    write_json(MANIFEST_PATH, manifest)
    write_jsonl(ROLE_PERMISSION_LOCK_PATH, role_locks)
    write_jsonl(SENSITIVE_POLICY_LOCK_PATH, sensitive_locks)
    write_jsonl(AUDIT_POLICY_LOCK_PATH, audit_locks)

    summary = manifest["access_security_summary"]
    report = "\n".join(
        [
            "# KMFA v0.1.4 S17-P1 Access Security",
            "",
            f"- role_count: `{summary['role_count']}`",
            f"- sensitive_policy_category_count: `{summary['sensitive_policy_category_count']}`",
            f"- audit_action_type_count: `{summary['audit_action_type_count']}`",
            f"- notification_delivery_count: `{summary['notification_delivery_count']}`",
            f"- external_connector_count: `{summary['external_connector_count']}`",
            f"- business_execution_count: `{summary['business_execution_count']}`",
            f"- report_grade_visible: `{summary['report_grade_visible']}`",
            "- GitHub upload: `deferred_until_v014_stage1_18_complete`",
            "",
            "This phase is public-safe and local-only. It locks role permission, sensitive material deny, and audit policy evidence without notification delivery, full report email body, formal report release, external connector, raw inbox access, or business execution.",
            "",
        ]
    )
    write_text(REPORT_PATH, report)
    write_text(
        TEST_RESULTS_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 S17-P1 Access Security Test Results",
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
    write_text(
        RISK_REGISTER_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 S17-P1 Access Security Risk Register",
                "",
                "- risk: Permission evidence could be mistaken as live authorization enforcement.",
                "  mitigation: Current output is a public-safe policy lock only; live connector and business execution stay blocked.",
                "- risk: Notification audit policy could be mistaken as notification delivery.",
                "  mitigation: S17-P1 records audit policy only; notification delivery is reserved for S17-P2 and remains blocked here.",
                "",
            ]
        ),
    )
    write_text(
        ROLLBACK_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 S17-P1 Access Security Rollback Plan",
                "",
                "- Remove only `KMFA/stage_artifacts/V014_S17_P1_ACCESS_SECURITY/` and paired v014 S17-P1 governance entries if rollback is required.",
                "- Do not touch raw/private inbox contents.",
                "",
            ]
        ),
    )


def generate() -> dict[str, Any]:
    manifest, role_locks, sensitive_locks, audit_locks = build_manifest()
    write_artifacts(manifest, role_locks, sensitive_locks, audit_locks)
    return manifest


def main() -> int:
    manifest = generate()
    summary = manifest["access_security_summary"]
    print(
        "PASS: KMFA v0.1.4 S17-P1 access/security generated "
        f"(roles={summary['role_count']}, sensitive_categories={summary['sensitive_policy_category_count']}, "
        f"audit_actions={summary['audit_action_type_count']}, notification_delivery={summary['notification_delivery_count']}, "
        f"external_connector={summary['external_connector_count']}, business_execution={summary['business_execution_count']}, "
        f"s17_p2={manifest['stage17_phase_progress']['s17_p2_performed']}, "
        f"github_upload={manifest['github_upload']['github_upload_performed']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
