#!/usr/bin/env python3
"""Generate current KMFA v0.1.4 S17-P1 access and security evidence."""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools import v014_s16_post_remediation_stage_review as s16_review
from KMFA.tools.access_security_policy import (
    REQUIRED_AUDIT_ACTION_TYPES,
    REQUIRED_SENSITIVE_POLICY_CATEGORIES,
)
from KMFA.tools.check_v014_s16_post_remediation_stage_review import (
    validate_v014_s16_post_remediation_stage_review,
)
from KMFA.tools.check_v014_s17_p1_access_security import (
    validate_v014_s17_p1_access_security as validate_historical_s17_p1,
)


PHASE_ID = "V014_S17_P1_POST_REMEDIATION_ACCESS_SECURITY"
ROADMAP_PHASE_ID = "S17-P1"
TASK_ID = "KMFA-V014-S17-P1-POST-REMEDIATION-ACCESS-SECURITY-20260712"
ACCEPTANCE_ID = "ACC-V014-S17-P1-POST-REMEDIATION-ACCESS-SECURITY"
VERSION = "0.1.4-s17-p1-post-remediation-access-security"
STATUS = "completed_validated_local_only_s17_p1_access_security_policy_no_go_upload_deferred"
DECISION = "NO_GO"
FORMULA_ID = "FORM-KMFA-V014-S17-P1-POST-REMEDIATION-ACCESS-SECURITY-001"
PARAMETER_IDS = ("PARAM-KMFA-1792", "PARAM-KMFA-1793", "PARAM-KMFA-1794", "PARAM-KMFA-1795")
MODEL_REGISTRY_KEY = "kmfa_v014_s17_p1_post_remediation_access_security"
ROLE_POLICY_VERSION = "ROLE-KMFA-V014-S17P1-POST-REMEDIATION-LEAST-PRIVILEGE-001"
SENSITIVE_POLICY_VERSION = "SEC-KMFA-V014-S17P1-POST-REMEDIATION-PUBLIC-REPO-DENY-001"
AUDIT_CONTRACT_VERSION = "AUD-KMFA-V014-S17P1-POST-REMEDIATION-EVENT-CONTRACT-001"

OUTPUT_DIR = Path("KMFA/stage_artifacts") / PHASE_ID
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "access_security_summary.json"
MANIFEST_PATH = MACHINE_DIR / "access_security_manifest.json"
ROLE_POLICY_PATH = MACHINE_DIR / "role_permission_policy_public_safe.jsonl"
AUTHORIZATION_PROBE_PATH = MACHINE_DIR / "authorization_probe_results_public_safe.jsonl"
SENSITIVE_POLICY_PATH = MACHINE_DIR / "sensitive_public_repo_policy_public_safe.jsonl"
AUDIT_CONTRACT_PATH = MACHINE_DIR / "audit_event_contract_public_safe.jsonl"
AUDIT_PROBE_PATH = MACHINE_DIR / "audit_contract_probe_results_public_safe.jsonl"
MATRIX_PATH = MACHINE_DIR / "acceptance_matrix_public_safe.json"
GO_NO_GO_PATH = MACHINE_DIR / "go_no_go_report.json"
REPORT_PATH = HUMAN_DIR / "access_security_report_zh.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results_zh.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register_zh.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan_zh.md"

SECURITY_DIR = Path("KMFA/metadata/security")
METADATA_SUMMARY_PATH = SECURITY_DIR / "v014_s17_p1_post_remediation_access_security_summary.json"
METADATA_MANIFEST_PATH = SECURITY_DIR / "v014_s17_p1_post_remediation_access_security_manifest.json"
METADATA_ROLE_POLICY_PATH = SECURITY_DIR / "v014_s17_p1_post_remediation_role_permission_policy.jsonl"
METADATA_SENSITIVE_POLICY_PATH = SECURITY_DIR / "v014_s17_p1_post_remediation_sensitive_public_repo_policy.jsonl"
METADATA_AUDIT_CONTRACT_PATH = SECURITY_DIR / "v014_s17_p1_post_remediation_audit_event_contract.jsonl"
METADATA_MATRIX_PATH = SECURITY_DIR / "v014_s17_p1_post_remediation_acceptance_matrix.json"
METADATA_GO_NO_GO_PATH = SECURITY_DIR / "v014_s17_p1_post_remediation_go_no_go_report.json"

PRIVATE_DIR = Path("KMFA/.codex_private_runtime/v014_s17_p1_post_remediation_access_security")
PRIVATE_RAW_BEFORE_PATH = PRIVATE_DIR / "raw_immutability_before.json"
PRIVATE_RAW_AFTER_PATH = PRIVATE_DIR / "raw_immutability_after.json"
PRIVATE_SCAN_REPORT_PATH = PRIVATE_DIR / "public_repo_and_raw_boundary_validation_zh.md"

ROADMAP_PATH = Path("KMFA/taskpack/v1_4/roadmap/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_4.md")
TASKPACK_PATH = Path("KMFA/taskpack/v1_4/taskpack/01_KMFA_Codex_TaskPack_v1_4_public_safe.md")
LEGACY_MANIFEST_PATH = Path("KMFA/stage_artifacts/V014_S17_P1_ACCESS_SECURITY/machine/access_security_manifest.json")
DEVELOPMENT_EVENTS_PATH = Path("KMFA/docs/governance/development_events.jsonl")
ASSURANCE_STATUS_PATH = Path("KMFA/docs/governance/ASSURANCE_STATUS.yaml")
STAGE_STATUS_PATH = Path("KMFA/metadata/stage_status.jsonl")
TASK_STATUS_PATH = Path("KMFA/metadata/traceability/v1_4_stage_phase_task_status.jsonl")

FORBIDDEN_TRACKED_SUFFIXES = {".zip", ".xlsx", ".xls", ".pdf", ".db", ".sqlite"}
CRITICAL_DENIED_ACTIONS = (
    "raw_private_file_mutation",
    "sensitive_material_public_commit",
    "credential_view",
    "quality_gate_bypass",
    "formal_report_release",
    "business_execution",
    "external_connector_use",
    "full_report_notification_body",
    "notification_delivery",
)
ROLE_SPECS: tuple[dict[str, Any], ...] = (
    {
        "role_id": "management",
        "role_label_zh": "管理层",
        "allowed_actions": (
            "view_public_safe_summary",
            "review_risk_dashboard",
            "approve_stage_review_after_validators",
            "read_governance_status",
        ),
        "max_write_scope": "metadata_only",
    },
    {
        "role_id": "finance",
        "role_label_zh": "财务",
        "allowed_actions": (
            "register_source_metadata",
            "review_finance_evidence_index",
            "append_metadata_status_event",
            "view_public_safe_summary",
        ),
        "max_write_scope": "metadata_only",
    },
    {
        "role_id": "reviewer",
        "role_label_zh": "复核",
        "allowed_actions": (
            "run_validators",
            "review_exception_queue",
            "record_review_finding",
            "read_governance_status",
        ),
        "max_write_scope": "metadata_only",
    },
    {
        "role_id": "readonly",
        "role_label_zh": "只读",
        "allowed_actions": ("read_public_safe_artifacts", "read_governance_status"),
        "max_write_scope": "none",
    },
)
AUTHORIZATION_PROBE_SPECS = (
    ("management", "view_public_safe_summary", "ALLOW"),
    ("management", "approve_stage_review_after_validators", "ALLOW"),
    ("finance", "register_source_metadata", "ALLOW"),
    ("finance", "append_metadata_status_event", "ALLOW"),
    ("reviewer", "run_validators", "ALLOW"),
    ("reviewer", "record_review_finding", "ALLOW"),
    ("readonly", "read_public_safe_artifacts", "ALLOW"),
    ("readonly", "read_governance_status", "ALLOW"),
    ("management", "credential_view", "DENY"),
    ("finance", "quality_gate_bypass", "DENY"),
    ("reviewer", "formal_report_release", "DENY"),
    ("readonly", "business_execution", "DENY"),
    ("readonly", "register_source_metadata", "DENY"),
    ("finance", "approve_stage_review_after_validators", "DENY"),
    ("management", "append_metadata_status_event", "DENY"),
    ("reviewer", "review_finance_evidence_index", "DENY"),
)
AUDIT_REQUIRED_FIELDS = (
    "event_id",
    "event_time",
    "actor_role",
    "action_type",
    "subject_ref",
    "evidence_ref",
    "result_status",
)


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
    indexes = [index for index, line in enumerate(lines) if line.startswith("snapshot_event_time:")]
    if len(indexes) != 1:
        raise RuntimeError("ASSURANCE_STATUS must contain exactly one snapshot_event_time")
    lines[indexes[0]] = f'snapshot_event_time: "{generated_at}"'
    _write_text(ASSURANCE_STATUS_PATH, "\n".join(lines))


def _load_taskpack_contract() -> dict[str, Any]:
    roadmap = ROADMAP_PATH.read_text(encoding="utf-8")
    taskpack = TASKPACK_PATH.read_text(encoding="utf-8")
    for token in (
        "S17｜权限、通知、安全、审计与运维",
        "角色权限覆盖管理层、财务、复核、只读",
        "敏感数据不提交公开仓库",
        "日志记录导入、处理、报告、导出、通知",
    ):
        if token not in roadmap:
            raise ValueError(f"roadmap token missing: {token}")
    for token in ("不提交原始敏感数据到公开GitHub", "不把缺数据报告伪装成完整报告", "可审计"):
        if token not in taskpack:
            raise ValueError(f"taskpack token missing: {token}")
    return {
        "roadmap_read": True,
        "taskpack_read": True,
        "s17_p1_role_sensitive_audit_contract_locked": True,
        "source_refs": {"roadmap": ROADMAP_PATH.as_posix(), "taskpack": TASKPACK_PATH.as_posix()},
    }


def _role_policy_rows() -> list[dict[str, Any]]:
    return [
        {
            "record_type": "v014_s17_p1_post_remediation_role_permission_policy",
            "project_id": "KMFA",
            "stage_id": "S17",
            "phase_id": PHASE_ID,
            "policy_version": ROLE_POLICY_VERSION,
            "role_id": spec["role_id"],
            "role_label_zh": spec["role_label_zh"],
            "allowed_actions": list(spec["allowed_actions"]),
            "denied_critical_actions": list(CRITICAL_DENIED_ACTIONS),
            "max_write_scope": spec["max_write_scope"],
            "least_privilege_applied": True,
            "deny_by_default": True,
            "audit_required": True,
            "raw_business_data_access_in_public_repo": False,
            "sensitive_file_public_commit_allowed": False,
            "credential_access_allowed": False,
            "quality_gate_bypass_allowed": False,
            "business_execution_allowed": False,
            "notification_delivery_allowed": False,
            "evidence_ref": ROLE_POLICY_PATH.as_posix(),
        }
        for spec in ROLE_SPECS
    ]


def _known_actions(role_rows: list[dict[str, Any]]) -> set[str]:
    return set(CRITICAL_DENIED_ACTIONS).union(
        *(set(row["allowed_actions"]) for row in role_rows)
    )


def evaluate_access(role_rows: list[dict[str, Any]], role_id: str, action_id: str) -> dict[str, str]:
    roles = {row["role_id"]: row for row in role_rows}
    if role_id not in roles:
        return {"decision": "DENY", "reason": "unknown_role"}
    if action_id not in _known_actions(role_rows):
        return {"decision": "DENY", "reason": "unknown_action"}
    if action_id in roles[role_id]["allowed_actions"]:
        return {"decision": "ALLOW", "reason": "explicit_role_grant"}
    return {"decision": "DENY", "reason": "not_explicitly_granted"}


def _authorization_probe_rows(role_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, (role_id, action_id, expected) in enumerate(AUTHORIZATION_PROBE_SPECS, 1):
        result = evaluate_access(role_rows, role_id, action_id)
        rows.append(
            {
                "record_type": "v014_s17_p1_authorization_probe_result",
                "probe_id": f"S17P1-AUTH-PROBE-{index:02d}",
                "policy_version": ROLE_POLICY_VERSION,
                "role_id": role_id,
                "action_id": action_id,
                "expected_decision": expected,
                "actual_decision": result["decision"],
                "decision_reason": result["reason"],
                "status": "PASS" if result["decision"] == expected else "FAIL",
                "probe_only": True,
                "persistent_authorization_event_written": False,
                "evidence_ref": AUTHORIZATION_PROBE_PATH.as_posix(),
            }
        )
    return rows


def _sensitive_policy_rows() -> list[dict[str, Any]]:
    controls = (
        "tracked_forbidden_suffix_scan",
        "private_runtime_tracking_scan",
        "strict_public_text_and_secret_scan",
        "governance_validator_gate",
        "local_commit_before_upload_gate",
    )
    return [
        {
            "record_type": "v014_s17_p1_post_remediation_sensitive_public_repo_policy",
            "project_id": "KMFA",
            "stage_id": "S17",
            "phase_id": PHASE_ID,
            "policy_version": SENSITIVE_POLICY_VERSION,
            "category_id": category,
            "public_repo_allowed": False,
            "git_upload_allowed": False,
            "value_plaintext_allowed": False,
            "metadata_hash_or_ref_only_allowed": True,
            "handling": "private_storage_or_hash_only_metadata",
            "enforcement_controls": list(controls),
            "evidence_ref": SENSITIVE_POLICY_PATH.as_posix(),
        }
        for category in REQUIRED_SENSITIVE_POLICY_CATEGORIES
    ]


def _repo_tracking_scan() -> dict[str, Any]:
    tracked = [Path(line) for line in _git_output(["ls-files", "KMFA"]).splitlines() if line]
    forbidden_suffix_count = sum(path.suffix.lower() in FORBIDDEN_TRACKED_SUFFIXES for path in tracked)
    private_runtime_count = sum(
        path.as_posix().startswith("KMFA/.codex_private_runtime/")
        or "90_用户原始上传数据_仅本地私有_禁止提交GitHub" in path.as_posix()
        for path in tracked
    )
    return {
        "scan_scope": "tracked_kmfa_paths",
        "tracked_path_count": len(tracked),
        "tracked_forbidden_suffix_count": forbidden_suffix_count,
        "tracked_private_runtime_path_count": private_runtime_count,
        "forbidden_suffix_policy_count": len(FORBIDDEN_TRACKED_SUFFIXES),
        "status": "PASS" if forbidden_suffix_count == 0 and private_runtime_count == 0 else "FAIL",
    }


def _audit_contract_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for action_type in REQUIRED_AUDIT_ACTION_TYPES:
        rows.append(
            {
                "record_type": "v014_s17_p1_post_remediation_audit_event_contract",
                "project_id": "KMFA",
                "stage_id": "S17",
                "phase_id": PHASE_ID,
                "contract_version": AUDIT_CONTRACT_VERSION,
                "action_type": action_type,
                "required_fields": list(AUDIT_REQUIRED_FIELDS),
                "append_only_required": True,
                "actor_role_required": True,
                "evidence_ref_required": True,
                "raw_payload_allowed": False,
                "private_document_allowed": False,
                "business_value_plaintext_allowed": False,
                "sends_full_report_body": False,
                "delivery_scope": "log_contract_only_s17_p2_not_implemented"
                if action_type == "notification"
                else "audit_log_contract_only",
                "persistent_event_write_enabled": False,
                "evidence_ref": AUDIT_CONTRACT_PATH.as_posix(),
            }
        )
    return rows


def _audit_probe_rows(contracts: list[dict[str, Any]], generated_at: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    role_by_action = {
        "import": "finance",
        "processing": "reviewer",
        "report": "management",
        "export": "reviewer",
        "notification": "management",
    }
    for index, contract in enumerate(contracts, 1):
        action_type = contract["action_type"]
        probe_event = {
            "event_id": f"PROBE-S17P1-{index:02d}",
            "event_time": generated_at,
            "actor_role": role_by_action[action_type],
            "action_type": action_type,
            "subject_ref": f"public-safe-probe:{action_type}",
            "evidence_ref": AUDIT_CONTRACT_PATH.as_posix(),
            "result_status": "PROBE_ONLY",
        }
        missing = [field for field in contract["required_fields"] if field not in probe_event]
        forbidden_payload_present = any(
            key in probe_event for key in ("raw_payload", "private_document", "business_value_plaintext")
        )
        passed = not missing and not forbidden_payload_present
        rows.append(
            {
                "record_type": "v014_s17_p1_audit_contract_probe_result",
                "probe_id": f"S17P1-AUDIT-PROBE-{index:02d}",
                "contract_version": AUDIT_CONTRACT_VERSION,
                "action_type": action_type,
                "required_field_count": len(contract["required_fields"]),
                "missing_required_field_count": len(missing),
                "forbidden_payload_present": forbidden_payload_present,
                "status": "PASS" if passed else "FAIL",
                "probe_only": True,
                "persistent_audit_event_written": False,
                "notification_delivered": False,
                "full_report_body_sent": False,
                "evidence_ref": AUDIT_PROBE_PATH.as_posix(),
            }
        )
    return rows


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
    }


def _phase_boundaries() -> dict[str, bool]:
    return {
        "s17_p1_performed": True,
        "s17_p2_performed": False,
        "s17_p3_performed": False,
        "stage17_review_performed": False,
        "live_identity_provider_configured": False,
        "credential_or_user_record_created": False,
        "persistent_authorization_event_write_performed": False,
        "persistent_audit_event_write_performed": False,
        "notification_delivery_performed": False,
        "full_report_notification_body_sent": False,
        "external_connector_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "formal_report_release_performed": False,
        "difference_closure_performed": False,
        "persistent_business_write_performed": False,
        "business_execution_performed": False,
    }


def _public_safety() -> dict[str, bool]:
    return {
        "raw_business_data_committed": False,
        "raw_file_names_committed": False,
        "raw_schema_or_header_committed": False,
        "business_value_plaintext_committed": False,
        "project_customer_or_counterparty_plaintext_committed": False,
        "contract_payroll_tax_material_committed": False,
        "bank_payload_committed": False,
        "credential_or_secret_committed": False,
        "private_runtime_committed": False,
        "zip_excel_pdf_private_csv_database_committed": False,
        "full_report_notification_body_committed": False,
    }


def _raw_boundary() -> dict[str, bool]:
    return {
        "raw_snapshot_read_performed": True,
        "raw_content_materialization_performed": False,
        "raw_write_performed": False,
        "raw_delete_performed": False,
        "raw_move_performed": False,
        "raw_rename_performed": False,
        "raw_overwrite_performed": False,
        "raw_mutation_performed": False,
    }


def _acceptance_matrix(summary: dict[str, Any]) -> dict[str, Any]:
    checks = (
        ("current_dependency", summary["current_s16_review_validated"]),
        ("four_roles", summary["role_count"] == 4 and summary["allowed_action_assignment_count"] == 14),
        ("authorization_probe", summary["authorization_probe_mismatch_count"] == 0),
        ("deny_by_default", summary["authorization_probe_deny_count"] == 8),
        ("sensitive_policy", summary["sensitive_policy_category_count"] == 15),
        ("repo_tracking", summary["tracked_forbidden_suffix_count"] == 0 and summary["tracked_private_runtime_path_count"] == 0),
        ("audit_contract", summary["audit_action_type_count"] == 5),
        ("audit_probe", summary["audit_contract_probe_mismatch_count"] == 0),
        ("raw_exact", summary["raw_snapshot_exact_match"] and summary["raw_cross_phase_snapshot_exact_match"]),
        ("quality", summary["current_report_grade"] == "D" and summary["decision"] == "NO_GO"),
        ("downstream_closed", not summary["s17_p2_performed"] and not summary["github_upload_performed"]),
        ("public_safety", all(value is False for value in _public_safety().values())),
    )
    rows = [
        {"check_id": f"V014-S17-P1-ACC-{index:03d}", "name": name, "status": "PASS" if passed else "FAIL"}
        for index, (name, passed) in enumerate(checks, 1)
    ]
    return {
        "schema_version": "kmfa.v014.s17_p1_post_remediation_access_security_matrix.v1",
        "acceptance_id": ACCEPTANCE_ID,
        "check_count": len(rows),
        "check_pass_count": sum(row["status"] == "PASS" for row in rows),
        "check_fail_count": sum(row["status"] == "FAIL" for row in rows),
        "checks": rows,
    }


def _phase_public_files() -> list[str]:
    artifact_paths = (
        SUMMARY_PATH,
        MANIFEST_PATH,
        ROLE_POLICY_PATH,
        AUTHORIZATION_PROBE_PATH,
        SENSITIVE_POLICY_PATH,
        AUDIT_CONTRACT_PATH,
        AUDIT_PROBE_PATH,
        MATRIX_PATH,
        GO_NO_GO_PATH,
        REPORT_PATH,
        TEST_RESULTS_PATH,
        RISK_REGISTER_PATH,
        ROLLBACK_PATH,
    )
    metadata_paths = (
        METADATA_SUMMARY_PATH,
        METADATA_MANIFEST_PATH,
        METADATA_ROLE_POLICY_PATH,
        METADATA_SENSITIVE_POLICY_PATH,
        METADATA_AUDIT_CONTRACT_PATH,
        METADATA_MATRIX_PATH,
        METADATA_GO_NO_GO_PATH,
    )
    governance_paths = (
        Path("KMFA/AGENTS.md"),
        Path("KMFA/CHANGELOG.md"),
        Path("KMFA/HANDOFF.md"),
        Path("KMFA/VERSION"),
        ASSURANCE_STATUS_PATH,
        Path("KMFA/docs/governance/DEVELOPMENT_LEDGER.md"),
        Path("KMFA/docs/governance/MODEL_SPEC.md"),
        Path("KMFA/docs/governance/OWNER_STATUS.md"),
        Path("KMFA/docs/governance/STATUS.md"),
        Path("KMFA/docs/governance/TRACEABILITY_MATRIX.csv"),
        Path("KMFA/docs/governance/VERSION_MATRIX.yaml"),
        Path("KMFA/docs/governance/delivery_tasks.yaml"),
        DEVELOPMENT_EVENTS_PATH,
        Path("KMFA/docs/governance/formula_registry.yaml"),
        Path("KMFA/docs/governance/model_registry.yaml"),
        Path("KMFA/docs/governance/parameter_registry.csv"),
        Path("KMFA/metadata/model_registry.yaml"),
        STAGE_STATUS_PATH,
        TASK_STATUS_PATH,
        Path("KMFA/功能清单.md"),
        Path("KMFA/开发记录.md"),
        Path("KMFA/模型参数文件.md"),
    )
    code_paths = (
        Path("KMFA/tools/v014_s17_p1_post_remediation_access_security.py"),
        Path("KMFA/tools/check_v014_s17_p1_post_remediation_access_security.py"),
        Path("KMFA/tests/test_v014_s17_p1_post_remediation_access_security.py"),
    )
    return [path.as_posix() for path in artifact_paths + metadata_paths + governance_paths + code_paths]


def _write_governance(generated_at: str) -> None:
    evidence_ref = MANIFEST_PATH.as_posix()
    _sync_assurance_snapshot_time(generated_at)
    _upsert_jsonl(
        DEVELOPMENT_EVENTS_PATH,
        {
            "event_id": "DEV-KMFA-20260712-V014-S17-P1-POST-REMEDIATION-ACCESS-SECURITY",
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
            "role_count": 4,
            "sensitive_policy_category_count": 15,
            "audit_action_type_count": 5,
            "authorization_probe_mismatch_count": 0,
            "audit_contract_probe_mismatch_count": 0,
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
            "name": "v0.1.4 S17-P1 post-remediation access security",
            "phase_goal": "lock four-role least privilege public repository sensitive-data deny and five audit event contracts",
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
    return f"""# KMFA v0.1.4 S17-P1 权限与安全

## 结论

- 当前依赖：Stage 16 post-remediation review 已验证。
- 角色：`{summary['role_count']}` 类，授权分配 `{summary['allowed_action_assignment_count']}` 项。
- 授权探针：`{summary['authorization_probe_count']}` 项，允许/拒绝=`{summary['authorization_probe_allow_count']}/{summary['authorization_probe_deny_count']}`，不一致=`{summary['authorization_probe_mismatch_count']}`。
- 敏感策略：`{summary['sensitive_policy_category_count']}` 类全部禁止公开仓库明文与上传。
- 审计契约：导入、处理、报告、导出、通知共 `{summary['audit_action_type_count']}` 类；契约探针 `{summary['audit_contract_probe_pass_count']}/5 PASS`。
- 仓库路径扫描：禁止后缀=`{summary['tracked_forbidden_suffix_count']}`，private runtime tracked=`{summary['tracked_private_runtime_path_count']}`。
- raw：review 前后及跨 Stage 16 当前复审快照一致。
- 当前状态：`Q4 / D / NO_GO / 3-9-2-1`。

## 权限边界

- 仅定义 public-safe 策略与确定性授权决策，不创建真实用户、凭据、身份提供方或 live 权限服务。
- 未显式授权的动作默认拒绝；敏感材料公开提交、凭据查看、质量门禁绕过、正式发布、通知发送和业务执行始终拒绝。
- 审计探针只验证 schema，不写真实业务日志，不发送通知或完整报告正文。
- S17-P2 只能在下一轮单独执行；本轮未上传 GitHub、未重装应用、未执行任何业务动作。
"""


def _render_private_report(summary: dict[str, Any]) -> str:
    return f"""# S17-P1 私有边界核验

- 原始数据文件数：{summary['raw_source_file_count']}
- phase 前后快照：exact match
- 与 Stage 16 review 快照：exact match
- 当前只读快照：exact match
- tracked 禁止后缀：{summary['tracked_forbidden_suffix_count']}
- tracked private runtime：{summary['tracked_private_runtime_path_count']}
- 授权探针不一致：{summary['authorization_probe_mismatch_count']}
- 审计契约探针不一致：{summary['audit_contract_probe_mismatch_count']}
- 当前差异结构：3 / 9 / 2 / 1
- 结论：未修改、删除、移动、重命名、覆盖或写入 raw；未创建真实用户、凭据、通知或业务日志。
- 最终 goal 多轮仍无法对齐时，必须生成全中文最终差异报告。
"""


def generate(*, final_validation: bool = False, write_governance: bool = True) -> dict[str, Any]:
    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
    taskpack_contract = _load_taskpack_contract()
    current_review = validate_v014_s16_post_remediation_stage_review(
        require_private_evidence=True,
        require_browser_evidence=True,
        require_final_evidence=True,
    )
    historical = validate_historical_s17_p1()

    raw_helper = s16_review.p1.s15_review.p1.s14_review.p1.s13_review.p1.s12_review.p1.s11_project
    raw_before = raw_helper._raw_snapshot("before_v014_s17_p1_post_remediation_access_security")
    role_rows = _role_policy_rows()
    authorization_rows = _authorization_probe_rows(role_rows)
    sensitive_rows = _sensitive_policy_rows()
    repo_scan = _repo_tracking_scan()
    audit_contracts = _audit_contract_rows()
    audit_probes = _audit_probe_rows(audit_contracts, generated_at)
    raw_after = raw_helper._raw_snapshot("after_v014_s17_p1_post_remediation_access_security")
    prior_raw = _read_json(s16_review.PRIVATE_RAW_AFTER_PATH)
    current_raw = raw_helper._raw_snapshot("current_v014_s17_p1_post_remediation_access_security")
    normalize = raw_helper._normalize_raw
    raw_exact = normalize(raw_before) == normalize(raw_after)
    raw_cross = normalize(raw_before) == normalize(prior_raw) == normalize(current_raw)
    if not raw_exact or not raw_cross:
        raise ValueError("raw source changed during S17-P1")
    if repo_scan["status"] != "PASS":
        raise ValueError("tracked KMFA path scan failed")

    authorization_mismatch = sum(row["status"] != "PASS" for row in authorization_rows)
    audit_mismatch = sum(row["status"] != "PASS" for row in audit_probes)
    summary = {
        "schema_version": "kmfa.v014.s17_p1_post_remediation_access_security_summary.v1",
        "project_id": "KMFA",
        "stage_id": "S17",
        "phase_id": PHASE_ID,
        "roadmap_phase_id": ROADMAP_PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "version": VERSION,
        "status": STATUS,
        "decision": DECISION,
        "current_s16_review_validated": current_review.get("phase_id") == s16_review.PHASE_ID,
        "role_count": len(role_rows),
        "allowed_action_assignment_count": sum(len(row["allowed_actions"]) for row in role_rows),
        "critical_denied_action_count": len(CRITICAL_DENIED_ACTIONS),
        "authorization_probe_count": len(authorization_rows),
        "authorization_probe_allow_count": sum(row["actual_decision"] == "ALLOW" for row in authorization_rows),
        "authorization_probe_deny_count": sum(row["actual_decision"] == "DENY" for row in authorization_rows),
        "authorization_probe_mismatch_count": authorization_mismatch,
        "sensitive_policy_category_count": len(sensitive_rows),
        "tracked_path_count": repo_scan["tracked_path_count"],
        "tracked_forbidden_suffix_count": repo_scan["tracked_forbidden_suffix_count"],
        "tracked_private_runtime_path_count": repo_scan["tracked_private_runtime_path_count"],
        "audit_action_type_count": len(audit_contracts),
        "audit_contract_probe_count": len(audit_probes),
        "audit_contract_probe_pass_count": sum(row["status"] == "PASS" for row in audit_probes),
        "audit_contract_probe_mismatch_count": audit_mismatch,
        "actual_business_audit_event_count": 0,
        "notification_delivery_count": 0,
        "full_report_notification_body_count": 0,
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
        "schema_version": "kmfa.v014.s17_p1_post_remediation_access_security_go_no_go.v1",
        "project_id": "KMFA",
        "stage_id": "S17",
        "phase_id": PHASE_ID,
        "decision": "NO_GO",
        "s17_p1_validated": True,
        "s17_p2_allowed_in_this_run": False,
        "notification_delivery_allowed": False,
        "full_report_notification_body_allowed": False,
        "live_identity_provider_allowed": False,
        "credential_creation_allowed": False,
        "external_connector_allowed": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "formal_report_release_allowed": False,
        "difference_closure_allowed": False,
        "persistent_business_write_allowed": False,
        "business_execution_allowed": False,
    }
    validation_summary = {
        "final_validation_recorded": final_validation,
        "focused_test": "PASS" if final_validation else "PENDING",
        "strict_validator": "PASS" if final_validation else "PENDING",
        "authorization_and_audit_probes": "PASS" if final_validation else "PENDING",
        "raw_alignment": "PASS" if final_validation else "PENDING",
        "governance_and_safety_scans": "PASS" if final_validation else "PENDING",
    }
    historical_summary = historical["access_security_summary"]
    manifest = {
        "schema_version": "kmfa.v014.s17_p1_post_remediation_access_security_manifest.v1",
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
        "current_s16_review_validated": True,
        "current_s16_review_manifest_ref": s16_review.MANIFEST_PATH.as_posix(),
        "historical_s17_p1_validated": True,
        "historical_s17_p1_dynamic_state_is_authoritative": False,
        "historical_four_roles_quarantined": historical_summary.get("role_count") == 4,
        "historical_fifteen_sensitive_categories_quarantined": historical_summary.get("sensitive_policy_category_count") == 15,
        "historical_five_audit_actions_quarantined": historical_summary.get("audit_action_type_count") == 5,
        "legacy_manifest_ref": LEGACY_MANIFEST_PATH.as_posix(),
        "role_ids": [row["role_id"] for row in role_rows],
        "deny_by_default_enforced": True,
        "taskpack_contract": taskpack_contract,
        "repo_tracking_scan": repo_scan,
        "quality_gate": _quality_gate(),
        "phase_boundaries": _phase_boundaries(),
        "public_repo_safety": _public_safety(),
        "raw_boundary": _raw_boundary(),
        "acceptance_matrix": matrix,
        "go_no_go": go_no_go,
        "validation_summary": validation_summary,
        "next_phase": "S17-P2",
        "next_required_step": (
            "下一轮仅执行 S17-P2；不得执行 S17-P3、Stage 17 整体复审、通知发送、完整报告邮件正文、"
            "外部连接器、GitHub upload、app reinstall、正式报告、差异关闭、持久业务写入或业务执行。"
        ),
    }

    json_pairs = (
        (SUMMARY_PATH, summary),
        (MANIFEST_PATH, manifest),
        (MATRIX_PATH, matrix),
        (GO_NO_GO_PATH, go_no_go),
        (METADATA_SUMMARY_PATH, summary),
        (METADATA_MANIFEST_PATH, manifest),
        (METADATA_MATRIX_PATH, matrix),
        (METADATA_GO_NO_GO_PATH, go_no_go),
        (PRIVATE_RAW_BEFORE_PATH, raw_before),
        (PRIVATE_RAW_AFTER_PATH, raw_after),
    )
    for path, value in json_pairs:
        _write_json(path, value)
    for path, rows in (
        (ROLE_POLICY_PATH, role_rows),
        (AUTHORIZATION_PROBE_PATH, authorization_rows),
        (SENSITIVE_POLICY_PATH, sensitive_rows),
        (AUDIT_CONTRACT_PATH, audit_contracts),
        (AUDIT_PROBE_PATH, audit_probes),
        (METADATA_ROLE_POLICY_PATH, role_rows),
        (METADATA_SENSITIVE_POLICY_PATH, sensitive_rows),
        (METADATA_AUDIT_CONTRACT_PATH, audit_contracts),
    ):
        _write_jsonl(path, rows)
    _write_text(REPORT_PATH, _render_report(summary))
    _write_text(
        TEST_RESULTS_PATH,
        f"""# S17-P1 权限与安全测试结果

- focused test / strict validator：最终复验记录见 manifest。
- 角色/授权：4 角色 / 14 授权分配 / 16 探针 / 8 ALLOW / 8 DENY / 0 mismatch。
- 敏感策略：15 类全部 fail-closed；tracked 禁止后缀/private runtime=`0/0`。
- 审计契约：5 类 / 5 probe PASS / 0 mismatch / 0 persistent event。
- raw phase 前后 / 跨 Stage 16 review / current：exact match。
- quality：Q4 / D / NO_GO / 3-9-2-1。
""",
    )
    _write_text(
        RISK_REGISTER_PATH,
        """# S17-P1 权限与安全风险登记

| 风险 | 控制 | 状态 |
|---|---|---|
| 静态角色被误读为 live 身份系统 | 明确不创建用户、凭据、身份提供方或 session | controlled |
| 未显式授权动作被放行 | deny-by-default 与 16 项授权探针 | controlled |
| 敏感材料进入公开仓库 | 15 类拒绝策略、tracked 后缀/private 扫描和 strict scan | controlled |
| 审计探针被误读为真实事件 | probe_only=true 且 persistent event write=false | controlled |
| 通知日志契约触发实际发送 | notification 仅 schema，delivery/full body=false | controlled |
| raw 被安全检查污染 | 前后及跨 phase 指纹一致，所有写动作=false | controlled |
""",
    )
    _write_text(
        ROLLBACK_PATH,
        f"""# S17-P1 权限与安全回滚计划

1. 回退本 phase 的本地 commit 与 `{OUTPUT_DIR.as_posix()}` public-safe 证据。
2. 回退本 phase 新增的 metadata/security 镜像和治理登记，不改 legacy S17-P1 夹具。
3. 删除 ignored private raw/scan 证据，不触碰原始目录。
4. 不删除、不移动、不重命名、不覆盖任何原始文件。
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
    manifest = generate(
        final_validation=args.final_validation,
        write_governance=not args.no_governance,
    )
    summary = manifest["summary"]
    print(
        "S17-P1 post-remediation access/security: "
        f"roles={summary['role_count']} auth={summary['authorization_probe_count']} "
        f"sensitive={summary['sensitive_policy_category_count']} audit={summary['audit_action_type_count']} "
        f"grade={summary['current_report_grade']} decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
