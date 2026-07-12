#!/usr/bin/env python3
"""Build KMFA S17-P1 access, security and audit policy artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

DEFAULT_OUTPUT_MANIFEST = ROOT / "metadata" / "security" / "access_security_policy_manifest.json"
DEFAULT_OUTPUT_ROLE_MATRIX = ROOT / "metadata" / "security" / "role_permission_matrix.jsonl"
DEFAULT_OUTPUT_SENSITIVE_POLICY = ROOT / "metadata" / "security" / "public_repo_sensitive_data_policy.jsonl"
DEFAULT_OUTPUT_AUDIT_POLICY = ROOT / "metadata" / "security" / "audit_log_policy.jsonl"
DEFAULT_OUTPUT_STAGE_MANIFEST = (
    ROOT
    / "stage_artifacts"
    / "S17_P1_access_security"
    / "machine"
    / "s17_p1_manifest.json"
)

REQUIRED_ROLES = (
    "management",
    "finance",
    "reviewer",
    "readonly",
)

REQUIRED_SENSITIVE_POLICY_CATEGORIES = (
    "raw_business_data",
    "zip_archive",
    "excel_workbook",
    "pdf_document",
    "private_csv",
    "sqlite_database",
    "bank_statement",
    "contract_document",
    "payroll_salary",
    "tax_filing",
    "credential_secret",
    "field_plaintext",
    "true_account_identifier",
    "true_money_amount",
    "true_customer_or_project_name",
)

REQUIRED_AUDIT_ACTION_TYPES = (
    "import",
    "processing",
    "report",
    "export",
    "notification",
)

POLICY_VERSION = "KMFA-S17P1-ACCESS-SECURITY-OWNER-PLAINTEXT-002"
ROLE_POLICY_VERSION = "ROLE-KMFA-S17P1-LEAST-PRIVILEGE-001"
SENSITIVE_POLICY_VERSION = "SEC-KMFA-S17P1-PUBLIC-REPO-OWNER-PLAINTEXT-002"
SECRET_POLICY_VERSION = "SEC-KMFA-S17P1-CREDENTIAL-SECRET-DENY-002"
AUDIT_POLICY_VERSION = "AUD-KMFA-S17P1-ACTION-LOG-001"

OWNER_AUTHORIZED_PLAINTEXT_ALLOWED_CATEGORIES = tuple(
    category for category in REQUIRED_SENSITIVE_POLICY_CATEGORIES if category != "credential_secret"
)

FORBIDDEN_PUBLIC_TEXT = (
    "raw_value",
    "normalized_value",
    "plaintext_value",
    "source_header_text",
    "original_filename",
    "private://",
    "private_ref://",
    ".zip",
    ".xlsx",
    ".xls",
    ".pdf",
    ".sqlite",
    ".db",
    "bank_account_number",
    "identity_document_number",
    '"amount_cents":',
    '"amount_yuan":',
    '"project_name_plaintext":',
    '"customer_name_plaintext":',
    "sk-",
    "-----BEGIN",
)


class AccessSecurityPolicyError(ValueError):
    """Raised when S17-P1 access/security artifacts are invalid."""


def _sha256_json(payload: Any) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AccessSecurityPolicyError(f"{path} must contain a JSON object")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            value = json.loads(line)
            if not isinstance(value, dict):
                raise AccessSecurityPolicyError(f"{path} contains a non-object JSONL record")
            rows.append(value)
    return rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )


def _public_repo_safety() -> dict[str, bool]:
    return {
        "raw_business_data_committed": False,
        "private_tabular_material_committed": False,
        "source_document_committed": False,
        "field_text_committed": False,
        "true_money_committed": False,
        "true_customer_project_committed": False,
        "credential_committed": False,
        "contract_payroll_tax_material_committed": False,
    }


def _stage_scope() -> dict[str, bool]:
    return {
        "s17_p1_scope_included": True,
        "s17_p2_scope_included": False,
        "s17_p3_scope_included": False,
        "stage17_review_scope_included": False,
        "github_upload_scope_included": False,
        "lineage_full_check_scope_included": False,
        "formal_report_scope_included": False,
        "external_connector_scope_included": False,
        "business_execution_scope_included": False,
        "notification_delivery_scope_included": False,
    }


def _quality_gate() -> dict[str, Any]:
    return {
        "role_permission_matrix_complete": True,
        "sensitive_public_repo_policy_enforced": True,
        "audit_log_policy_complete": True,
        "raw_sensitive_public_repo_allowed": True,
        "credential_secret_public_repo_allowed": False,
        "notification_delivery_allowed": False,
        "notification_full_report_body_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "business_execution_allowed": False,
        "external_connector_allowed": False,
        "lineage_full_check_allowed": False,
        "stage17_review_allowed": False,
        "github_upload_allowed": True,
        "phase_completion_upload_allowed": True,
        "release_block_reason": "owner_authorized_plaintext_github_policy_only_not_business_release",
    }


def _role_matrix() -> list[dict[str, Any]]:
    common_denied = [
        "source_document_open_without_owner_authorization",
        "sensitive_material_public_commit_without_owner_authorization",
        "credential_view",
        "quality_gate_bypass",
        "formal_report_release",
        "business_execution",
        "external_connector_use",
        "full_report_notification_body",
    ]
    rows = [
        {
            "role_id": "management",
            "role_label": "management",
            "allowed_public_safe_actions": [
                "view_public_safe_summary",
                "review_risk_dashboard",
                "approve_stage_review_after_validators",
                "authorize_owner_plaintext_github_upload",
            ],
            "max_write_scope": "metadata_and_owner_authorized_plaintext_upload_manifest",
        },
        {
            "role_id": "finance",
            "role_label": "finance",
            "allowed_public_safe_actions": [
                "register_source_metadata",
                "review_finance_evidence_index",
                "append_metadata_status_event",
                "prepare_owner_authorized_plaintext_upload_manifest",
            ],
            "max_write_scope": "metadata_and_owner_authorized_plaintext_upload_manifest",
        },
        {
            "role_id": "reviewer",
            "role_label": "reviewer",
            "allowed_public_safe_actions": [
                "run_validators",
                "review_exception_queue",
                "record_review_finding",
                "validate_owner_authorized_plaintext_upload_manifest",
            ],
            "max_write_scope": "metadata_and_owner_authorized_plaintext_upload_manifest",
        },
        {
            "role_id": "readonly",
            "role_label": "readonly",
            "allowed_public_safe_actions": [
                "read_public_safe_artifacts",
                "read_governance_status",
            ],
            "max_write_scope": "none",
        },
    ]
    for row in rows:
        owner_authorized_commit_allowed = row["role_id"] != "readonly"
        row.update(
            {
                "record_type": "access_role_permission",
                "policy_version": ROLE_POLICY_VERSION,
                "denied_actions": common_denied,
                "raw_business_data_access_in_public_repo": owner_authorized_commit_allowed,
                "sensitive_file_public_commit_allowed": owner_authorized_commit_allowed,
                "owner_authorization_required_for_sensitive_commit": owner_authorized_commit_allowed,
                "credential_access_allowed": False,
                "business_execution_allowed": False,
                "bypass_quality_gate_allowed": False,
                "notification_body_report_allowed": False,
                "audit_required": True,
                "least_privilege_applied": True,
                "evidence_ref": "KMFA/metadata/security/role_permission_matrix.jsonl",
            }
        )
    return rows


def _sensitive_policies() -> list[dict[str, Any]]:
    controls = [
        "explicit_owner_authorization_required",
        "owner_authorized_upload_manifest_required",
        "secret_scan_before_upload",
        "git_history_bloat_review",
        "local_commit_before_upload_gate",
    ]
    rows: list[dict[str, Any]] = []
    for category in REQUIRED_SENSITIVE_POLICY_CATEGORIES:
        allowed = category in OWNER_AUTHORIZED_PLAINTEXT_ALLOWED_CATEGORIES
        rows.append(
            {
                "record_type": "public_repo_sensitive_data_policy",
                "category_id": category,
                "policy_version": SENSITIVE_POLICY_VERSION if allowed else SECRET_POLICY_VERSION,
                "public_repo_allowed": allowed,
                "git_upload_allowed": allowed,
                "value_plaintext_allowed": allowed,
                "metadata_hash_or_ref_only_allowed": not allowed,
                "metadata_hash_or_ref_allowed": True,
                "requires_explicit_owner_authorization": allowed,
                "credential_secret_allowed": False,
                "handling": "owner_authorized_plaintext_github_upload"
                if allowed
                else "secret_or_credential_never_plaintext_public_repo",
                "enforcement_controls": controls,
                "evidence_ref": "KMFA/metadata/security/public_repo_sensitive_data_policy.jsonl",
            }
        )
    return rows


def _owner_authorized_plaintext_github_policy() -> dict[str, Any]:
    return {
        "policy_version": SENSITIVE_POLICY_VERSION,
        "policy_mode": "owner_authorized_plaintext_github_upload",
        "allowed": True,
        "allowed_categories": list(OWNER_AUTHORIZED_PLAINTEXT_ALLOWED_CATEGORIES),
        "denied_categories": ["credential_secret"],
        "requires_explicit_owner_authorization": True,
        "requires_upload_manifest": True,
        "owner_authorization_source": "current_thread_owner_instruction_or_signed_upload_manifest",
        "tracked_upload_manifest": "KMFA/metadata/security/owner_authorized_plaintext_upload_manifest.jsonl",
        "credential_secret_public_repo_allowed": False,
        "actual_plaintext_files_committed_by_this_manifest": False,
    }


def _audit_policies() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    action_labels = {
        "import": "source metadata registration",
        "processing": "metadata transformation or validator run",
        "report": "draft or grade-aware report artifact operation",
        "export": "public-safe artifact export operation",
        "notification": "notification event logging policy",
    }
    for action_type in REQUIRED_AUDIT_ACTION_TYPES:
        rows.append(
            {
                "record_type": "audit_log_policy",
                "action_type": action_type,
                "action_label": action_labels[action_type],
                "policy_version": AUDIT_POLICY_VERSION,
                "metadata_target": "KMFA/metadata/security/audit_events.jsonl",
                "required_fields": [
                    "event_id",
                    "event_time",
                    "actor_role",
                    "action_type",
                    "subject_ref",
                    "evidence_ref",
                    "result_status",
                ],
                "append_only": True,
                "requires_actor_role": True,
                "requires_event_time": True,
                "requires_evidence_ref": True,
                "raw_payload_allowed": False,
                "private_document_allowed": False,
                "business_value_plaintext_allowed": False,
                "sends_full_report_body": False,
                "delivery_scope": "log_policy_only_s17_p2_not_implemented"
                if action_type == "notification"
                else "audit_log_policy_only",
                "evidence_ref": "KMFA/metadata/security/audit_log_policy.jsonl",
            }
        )
    return rows


def build_default_access_security_policy(
    *, generated_at: str = "2026-07-01T23:55:00+10:00"
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    role_matrix = _role_matrix()
    sensitive_policies = _sensitive_policies()
    audit_policies = _audit_policies()
    manifest: dict[str, Any] = {
        "record_type": "s17_p1_access_security_manifest",
        "project_id": "KMFA",
        "stage": "S17",
        "phase": "P1",
        "stage_phase": "S17-P1",
        "policy_version": POLICY_VERSION,
        "generated_at": generated_at,
        "taskpack_refs": [
            "KMFA/taskpack/v1_2/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_2.md:S17-P1",
            "KMFA/metadata/stage_status.jsonl:S17PAT01-S17PAT03",
        ],
        "required_roles": list(REQUIRED_ROLES),
        "required_sensitive_policy_categories": list(REQUIRED_SENSITIVE_POLICY_CATEGORIES),
        "required_audit_action_types": list(REQUIRED_AUDIT_ACTION_TYPES),
        "summary": {
            "role_count": len(role_matrix),
            "sensitive_policy_category_count": len(sensitive_policies),
            "audit_action_type_count": len(audit_policies),
            "public_repo_safety_status": "owner_authorized_plaintext_github_allowed_except_credentials",
            "notification_scope": "log_policy_only_no_delivery_in_s17_p1",
        },
        "public_repo_safety": _public_repo_safety(),
        "owner_authorized_plaintext_github_policy": _owner_authorized_plaintext_github_policy(),
        "stage_scope": _stage_scope(),
        "quality_gate": _quality_gate(),
        "output_refs": {
            "manifest": "KMFA/metadata/security/access_security_policy_manifest.json",
            "role_matrix": "KMFA/metadata/security/role_permission_matrix.jsonl",
            "sensitive_policy": "KMFA/metadata/security/public_repo_sensitive_data_policy.jsonl",
            "audit_policy": "KMFA/metadata/security/audit_log_policy.jsonl",
            "stage_manifest": "KMFA/stage_artifacts/S17_P1_access_security/machine/s17_p1_manifest.json",
        },
        "evidence_refs": [
            "KMFA/tools/access_security_policy.py",
            "KMFA/tools/check_s17_p1_access_security.py",
            "KMFA/tests/test_access_security_policy.py",
            "KMFA/stage_artifacts/S17_P1_access_security/human/s17_p1_completion_record.md",
            "KMFA/stage_artifacts/S17_P1_access_security/human/test_results.md",
        ],
    }
    manifest["content_hash"] = _sha256_json(
        {
            "manifest_without_hash": {k: v for k, v in manifest.items() if k != "content_hash"},
            "role_matrix": role_matrix,
            "sensitive_policies": sensitive_policies,
            "audit_policies": audit_policies,
        }
    )
    return manifest, role_matrix, sensitive_policies, audit_policies


def _require_equal(label: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        raise AccessSecurityPolicyError(f"{label}: expected {expected!r}, got {actual!r}")


def _require_true(label: str, actual: Any) -> None:
    if actual is not True:
        raise AccessSecurityPolicyError(f"{label}: expected true, got {actual!r}")


def _require_false(label: str, actual: Any) -> None:
    if actual is not False:
        raise AccessSecurityPolicyError(f"{label}: expected false, got {actual!r}")


def _assert_public_payload_safe(payload: Any) -> None:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    for forbidden_text in FORBIDDEN_PUBLIC_TEXT:
        if forbidden_text in encoded:
            raise AccessSecurityPolicyError(f"public payload contains forbidden text: {forbidden_text}")


def validate_access_security_policy_artifacts(
    manifest: dict[str, Any],
    role_matrix: list[dict[str, Any]],
    sensitive_policies: list[dict[str, Any]],
    audit_policies: list[dict[str, Any]],
) -> None:
    _assert_public_payload_safe([manifest, role_matrix, sensitive_policies, audit_policies])

    _require_equal("manifest.stage_phase", manifest.get("stage_phase"), "S17-P1")
    _require_equal("manifest.required_roles", tuple(manifest.get("required_roles", [])), REQUIRED_ROLES)
    _require_equal(
        "manifest.required_sensitive_policy_categories",
        tuple(manifest.get("required_sensitive_policy_categories", [])),
        REQUIRED_SENSITIVE_POLICY_CATEGORIES,
    )
    _require_equal(
        "manifest.required_audit_action_types",
        tuple(manifest.get("required_audit_action_types", [])),
        REQUIRED_AUDIT_ACTION_TYPES,
    )
    _require_equal("manifest.summary.role_count", manifest.get("summary", {}).get("role_count"), 4)
    _require_equal(
        "manifest.summary.sensitive_policy_category_count",
        manifest.get("summary", {}).get("sensitive_policy_category_count"),
        len(REQUIRED_SENSITIVE_POLICY_CATEGORIES),
    )
    _require_equal(
        "manifest.summary.audit_action_type_count",
        manifest.get("summary", {}).get("audit_action_type_count"),
        5,
    )

    public_repo_safety = manifest.get("public_repo_safety")
    if not isinstance(public_repo_safety, dict):
        raise AccessSecurityPolicyError("manifest.public_repo_safety must be an object")
    for key, value in public_repo_safety.items():
        _require_false(f"manifest.public_repo_safety.{key}", value)

    stage_scope = manifest.get("stage_scope")
    if not isinstance(stage_scope, dict):
        raise AccessSecurityPolicyError("manifest.stage_scope must be an object")
    _require_true("manifest.stage_scope.s17_p1_scope_included", stage_scope.get("s17_p1_scope_included"))
    for key in (
        "s17_p2_scope_included",
        "s17_p3_scope_included",
        "stage17_review_scope_included",
        "github_upload_scope_included",
        "lineage_full_check_scope_included",
        "formal_report_scope_included",
        "external_connector_scope_included",
        "business_execution_scope_included",
        "notification_delivery_scope_included",
    ):
        _require_false(f"manifest.stage_scope.{key}", stage_scope.get(key))

    quality_gate = manifest.get("quality_gate")
    if not isinstance(quality_gate, dict):
        raise AccessSecurityPolicyError("manifest.quality_gate must be an object")
    for key in (
        "role_permission_matrix_complete",
        "sensitive_public_repo_policy_enforced",
        "audit_log_policy_complete",
        "raw_sensitive_public_repo_allowed",
        "github_upload_allowed",
        "phase_completion_upload_allowed",
    ):
        _require_true(f"manifest.quality_gate.{key}", quality_gate.get(key))
    for key in (
        "credential_secret_public_repo_allowed",
        "notification_delivery_allowed",
        "notification_full_report_body_allowed",
        "formal_report_allowed",
        "business_decision_basis_allowed",
        "business_execution_allowed",
        "external_connector_allowed",
        "lineage_full_check_allowed",
        "stage17_review_allowed",
    ):
        _require_false(f"manifest.quality_gate.{key}", quality_gate.get(key))

    owner_policy = manifest.get("owner_authorized_plaintext_github_policy")
    if not isinstance(owner_policy, dict):
        raise AccessSecurityPolicyError("manifest.owner_authorized_plaintext_github_policy must be an object")
    _require_true("owner_policy.allowed", owner_policy.get("allowed"))
    _require_true(
        "owner_policy.requires_explicit_owner_authorization",
        owner_policy.get("requires_explicit_owner_authorization"),
    )
    _require_true("owner_policy.requires_upload_manifest", owner_policy.get("requires_upload_manifest"))
    _require_false(
        "owner_policy.credential_secret_public_repo_allowed",
        owner_policy.get("credential_secret_public_repo_allowed"),
    )
    _require_equal(
        "owner_policy.allowed_categories",
        tuple(owner_policy.get("allowed_categories", [])),
        OWNER_AUTHORIZED_PLAINTEXT_ALLOWED_CATEGORIES,
    )

    roles = {str(row.get("role_id")): row for row in role_matrix}
    _require_equal("role ids", set(roles), set(REQUIRED_ROLES))
    for role_id in REQUIRED_ROLES:
        row = roles[role_id]
        _require_equal(f"{role_id}.record_type", row.get("record_type"), "access_role_permission")
        actions = row.get("allowed_public_safe_actions")
        if not isinstance(actions, list) or len(actions) < 2:
            raise AccessSecurityPolicyError(f"{role_id}.allowed_public_safe_actions must contain at least two actions")
        owner_authorized_commit_allowed = role_id != "readonly"
        if role_id == "readonly":
            _require_equal(f"{role_id}.max_write_scope", row.get("max_write_scope"), "none")
        else:
            _require_equal(
                f"{role_id}.max_write_scope",
                row.get("max_write_scope"),
                "metadata_and_owner_authorized_plaintext_upload_manifest",
            )
        for key in ("raw_business_data_access_in_public_repo", "sensitive_file_public_commit_allowed"):
            if owner_authorized_commit_allowed:
                _require_true(f"{role_id}.{key}", row.get(key))
            else:
                _require_false(f"{role_id}.{key}", row.get(key))
        if owner_authorized_commit_allowed:
            _require_true(
                f"{role_id}.owner_authorization_required_for_sensitive_commit",
                row.get("owner_authorization_required_for_sensitive_commit"),
            )
        for key in ("credential_access_allowed", "business_execution_allowed", "bypass_quality_gate_allowed", "notification_body_report_allowed"):
            _require_false(f"{role_id}.{key}", row.get(key))
        _require_true(f"{role_id}.audit_required", row.get("audit_required"))
        _require_true(f"{role_id}.least_privilege_applied", row.get("least_privilege_applied"))

    categories = {str(row.get("category_id")): row for row in sensitive_policies}
    _require_equal("sensitive policy categories", set(categories), set(REQUIRED_SENSITIVE_POLICY_CATEGORIES))
    for category in REQUIRED_SENSITIVE_POLICY_CATEGORIES:
        row = categories[category]
        _require_equal(f"{category}.record_type", row.get("record_type"), "public_repo_sensitive_data_policy")
        if category == "credential_secret":
            for key in ("public_repo_allowed", "git_upload_allowed", "value_plaintext_allowed"):
                _require_false(f"{category}.{key}", row.get(key))
            _require_true(
                f"{category}.metadata_hash_or_ref_only_allowed",
                row.get("metadata_hash_or_ref_only_allowed"),
            )
            _require_false(f"{category}.credential_secret_allowed", row.get("credential_secret_allowed"))
            _require_equal(
                f"{category}.handling",
                row.get("handling"),
                "secret_or_credential_never_plaintext_public_repo",
            )
        else:
            for key in ("public_repo_allowed", "git_upload_allowed", "value_plaintext_allowed"):
                _require_true(f"{category}.{key}", row.get(key))
            _require_false(
                f"{category}.metadata_hash_or_ref_only_allowed",
                row.get("metadata_hash_or_ref_only_allowed"),
            )
            _require_true(
                f"{category}.requires_explicit_owner_authorization",
                row.get("requires_explicit_owner_authorization"),
            )
            _require_equal(f"{category}.handling", row.get("handling"), "owner_authorized_plaintext_github_upload")
        controls = row.get("enforcement_controls")
        if not isinstance(controls, list) or "explicit_owner_authorization_required" not in controls:
            raise AccessSecurityPolicyError(
                f"{category}.enforcement_controls missing explicit_owner_authorization_required"
            )

    actions = {str(row.get("action_type")): row for row in audit_policies}
    _require_equal("audit action types", set(actions), set(REQUIRED_AUDIT_ACTION_TYPES))
    for action_type in REQUIRED_AUDIT_ACTION_TYPES:
        row = actions[action_type]
        _require_equal(f"{action_type}.record_type", row.get("record_type"), "audit_log_policy")
        _require_equal(
            f"{action_type}.metadata_target",
            row.get("metadata_target"),
            "KMFA/metadata/security/audit_events.jsonl",
        )
        required_fields = row.get("required_fields")
        if not isinstance(required_fields, list):
            raise AccessSecurityPolicyError(f"{action_type}.required_fields must be a list")
        for field in ("event_id", "event_time", "actor_role", "action_type", "evidence_ref"):
            if field not in required_fields:
                raise AccessSecurityPolicyError(f"{action_type}.required_fields missing {field}")
        for key in ("append_only", "requires_actor_role", "requires_event_time", "requires_evidence_ref"):
            _require_true(f"{action_type}.{key}", row.get(key))
        for key in ("raw_payload_allowed", "private_document_allowed", "business_value_plaintext_allowed"):
            _require_false(f"{action_type}.{key}", row.get(key))
        if action_type == "notification":
            _require_false("notification.sends_full_report_body", row.get("sends_full_report_body"))
            _require_equal(
                "notification.delivery_scope",
                row.get("delivery_scope"),
                "log_policy_only_s17_p2_not_implemented",
            )


def write_default_artifacts(
    *,
    generated_at: str,
    manifest_path: Path = DEFAULT_OUTPUT_MANIFEST,
    role_matrix_path: Path = DEFAULT_OUTPUT_ROLE_MATRIX,
    sensitive_policy_path: Path = DEFAULT_OUTPUT_SENSITIVE_POLICY,
    audit_policy_path: Path = DEFAULT_OUTPUT_AUDIT_POLICY,
    stage_manifest_path: Path = DEFAULT_OUTPUT_STAGE_MANIFEST,
) -> dict[str, Any]:
    manifest, role_matrix, sensitive_policies, audit_policies = build_default_access_security_policy(
        generated_at=generated_at
    )
    validate_access_security_policy_artifacts(manifest, role_matrix, sensitive_policies, audit_policies)
    stage_manifest = dict(manifest)
    stage_manifest.update(
        {
            "record_type": "s17_p1_stage_manifest",
            "status": "completed_validated_local_only",
            "role_permission_matrix_path": str(role_matrix_path.relative_to(ROOT.parent)),
            "sensitive_policy_path": str(sensitive_policy_path.relative_to(ROOT.parent)),
            "audit_policy_path": str(audit_policy_path.relative_to(ROOT.parent)),
            "manifest_path": str(manifest_path.relative_to(ROOT.parent)),
        }
    )
    write_json(manifest_path, manifest)
    write_jsonl(role_matrix_path, role_matrix)
    write_jsonl(sensitive_policy_path, sensitive_policies)
    write_jsonl(audit_policy_path, audit_policies)
    write_json(stage_manifest_path, stage_manifest)
    return {
        "manifest": manifest,
        "role_matrix": role_matrix,
        "sensitive_policies": sensitive_policies,
        "audit_policies": audit_policies,
        "stage_manifest": stage_manifest,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build KMFA S17-P1 access/security artifacts.")
    parser.add_argument("--generated-at", default="2026-07-01T23:55:00+10:00")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    parser.add_argument("--role-matrix", type=Path, default=DEFAULT_OUTPUT_ROLE_MATRIX)
    parser.add_argument("--sensitive-policy", type=Path, default=DEFAULT_OUTPUT_SENSITIVE_POLICY)
    parser.add_argument("--audit-policy", type=Path, default=DEFAULT_OUTPUT_AUDIT_POLICY)
    parser.add_argument("--stage-manifest", type=Path, default=DEFAULT_OUTPUT_STAGE_MANIFEST)
    args = parser.parse_args(argv)

    artifacts = write_default_artifacts(
        generated_at=args.generated_at,
        manifest_path=args.manifest,
        role_matrix_path=args.role_matrix,
        sensitive_policy_path=args.sensitive_policy,
        audit_policy_path=args.audit_policy,
        stage_manifest_path=args.stage_manifest,
    )
    summary = artifacts["manifest"]["summary"]
    print(
        "PASS: generated KMFA S17-P1 access/security artifacts "
        f"(roles={summary['role_count']}, "
        f"sensitive_categories={summary['sensitive_policy_category_count']}, "
        f"audit_actions={summary['audit_action_type_count']}, "
        "owner_authorized_plaintext_github=true, credential_secret=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
