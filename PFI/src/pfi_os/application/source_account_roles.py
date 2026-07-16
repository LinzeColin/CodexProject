from __future__ import annotations

import hashlib
import json
import re
from datetime import date
from pathlib import Path
from typing import Any, Mapping

from jsonschema import Draft202012Validator

from pfi_os.domain.source_accounts import (
    AccountRoleAssignment,
    RoleReviewItem,
    RoleRoutingDecision,
    SourceProfile,
)


VERSION = "v0.2.5"
STAGE = 3
PHASE_ID = "V025-S3-P3.1"
TASK_IDS = ("S3-P1-T1", "S3-P1-T2", "S3-P1-T3", "S3-P1-T4")
CONTRACT_ID = "PFI-V025-STAGE3-PHASE31-SOURCE-ACCOUNT"
ACCEPTANCE_ID = "ACC-PFI-V025-S3-P31-SOURCE-ACCOUNT"

PFI_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_ROOT = PFI_ROOT / "config" / "schemas" / "v025"
POLICY_PATH = PFI_ROOT / "config" / "sources" / "v025_phase_3_1_source_account_policy.json"
SCHEMA_FILES = (
    "parser_provenance.schema.json",
    "source_profile.schema.json",
    "account_role_assignment.schema.json",
    "role_review_item.schema.json",
)

_FORBIDDEN_PUBLIC_KEYS = {
    "absolute_path",
    "account_id",
    "account_number",
    "amount",
    "balance",
    "credential",
    "password",
    "private_key",
    "raw_row",
    "secret",
    "token",
    "transaction",
}
_CREDENTIAL_RE = re.compile(
    r"(?i)(?:api[-_]?key|access[-_]?token|password|authorization|client[-_]?secret|private[-_]?key)"
    r"[\"']?\s*[:=]"
)


def build_phase31_contract() -> dict[str, Any]:
    return {
        "schema": "PFIV025Stage3Phase31ContractV1",
        "version": VERSION,
        "stage": STAGE,
        "phase_id": PHASE_ID,
        "contract_id": CONTRACT_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "acceptance_id_origin": "project_governance_assigned_not_taskpack",
        "task_ids": list(TASK_IDS),
        "current_phase_only": True,
        "real_financial_data_read": False,
        "real_financial_data_mutated": False,
        "source_name_classification": False,
        "financial_fixture_fallback_used": False,
        "finder_used": False,
        "risk_tier": "T3_FINANCIAL_SCHEMA_PRIVACY",
        "explicitly_not_done": [
            "Phase 3.2",
            "Phase 3.3",
            "real financial source reads or writes",
            "database migration",
            "GitHub push",
            "canonical App install",
            "Stage 3 whole-stage acceptance",
        ],
    }


def load_phase31_policy(path: Path | str = POLICY_PATH) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Phase 3.1 policy must be a JSON object")
    roles = payload.get("role_registry")
    if not isinstance(roles, list) or not roles or len(roles) != len(set(roles)):
        raise ValueError("role_registry must contain unique roles")
    if payload.get("unknown_role_policy") != "review_queue":
        raise ValueError("unknown_role_policy must be review_queue")
    if payload.get("unknown_role_publish_allowed") is not False:
        raise ValueError("unknown roles must not be publishable")
    if payload.get("source_name_classification") is not False:
        raise ValueError("source-name classification is forbidden")
    assert_public_safe_payload(payload)
    return payload


def route_account_role(
    profile: SourceProfile,
    *,
    account_ref: str,
    proposed_role: str,
    effective_from: date,
    policy: Mapping[str, Any],
    created_at: str,
    effective_to: date | None = None,
) -> RoleRoutingDecision:
    role_registry = set(policy.get("role_registry", ()))
    identity_parts = (
        profile.source_id,
        account_ref,
        proposed_role,
        effective_from.isoformat(),
        effective_to.isoformat() if effective_to else "open",
    )
    if proposed_role not in role_registry:
        review_item = RoleReviewItem(
            review_id=_stable_id("role_review", *identity_parts),
            source_id=profile.source_id,
            account_ref=account_ref,
            proposed_role=proposed_role,
            effective_from=effective_from,
            effective_to=effective_to,
            reason_code="unknown_role",
            created_at=created_at,
        )
        return RoleRoutingDecision(
            status="review_required",
            publish_allowed=False,
            assignment=None,
            review_item=review_item,
        )

    assignment = AccountRoleAssignment(
        assignment_id=_stable_id("role_assignment", *identity_parts),
        account_ref=account_ref,
        source_id=profile.source_id,
        role=proposed_role,
        effective_from=effective_from,
        effective_to=effective_to,
    )
    return RoleRoutingDecision(
        status="publishable",
        publish_allowed=True,
        assignment=assignment,
        review_item=None,
    )


def build_schema_inventory(schema_root: Path | str = SCHEMA_ROOT) -> dict[str, Any]:
    root = Path(schema_root)
    hashes: dict[str, str] = {}
    for filename in SCHEMA_FILES:
        path = root / filename
        schema = json.loads(path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        hashes[filename] = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
    return {
        "schema": "PFIV025Stage3Phase31SchemaInventoryV1",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "status": "pass",
        "schema_count": len(hashes),
        "schemas": hashes,
        "source_type_extension_policy": "lowercase_namespaced_token",
        "capability_extension_policy": "lowercase_namespaced_token",
        "source_name_enumeration_count": 0,
        "real_financial_data_read": False,
    }


def build_review_queue_summary() -> dict[str, Any]:
    return {
        "schema": "PFIV025Stage3Phase31ReviewQueueSummaryV1",
        "status": "pass",
        "unknown_role_policy": "review_queue",
        "unknown_role_publish_allowed": False,
        "source_name_classification": False,
        "private_account_identifiers_emitted": 0,
        "financial_records_read": 0,
        "financial_values_emitted": 0,
    }


def assert_public_safe_payload(payload: Any) -> None:
    def visit(value: Any) -> None:
        if isinstance(value, dict):
            for key, nested in value.items():
                if str(key).lower() in _FORBIDDEN_PUBLIC_KEYS:
                    raise ValueError(f"forbidden public key: {key}")
                visit(nested)
        elif isinstance(value, (list, tuple)):
            for nested in value:
                visit(nested)
        elif isinstance(value, str):
            if value.startswith(("/Users/", "/private/", "file://")):
                raise ValueError("absolute private path is forbidden")
            if _CREDENTIAL_RE.search(value):
                raise ValueError("credential-like content is forbidden")

    visit(payload)


def _stable_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()[:20]
    return f"{prefix}_{digest}"
