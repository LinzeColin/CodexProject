"""S2PMT01 security and evidence boundary helpers."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any
from urllib.parse import urlsplit, urlunsplit


S2PMT01_SECURITY_MODEL_ID = "adp-s2pmt01-security-boundary-v1"
S2PMT01_ACCEPTANCE_ID = "ACC-S2PMT01-SECURITY"
S2PMT01_TASK_ID = "S2PMT01"
S2PMT01_UNTRUSTED_DATA_LABEL = "UNTRUSTED_DATA"
S2PMT01_ALLOWED_URL_SCHEMES = ("https", "http")
S2PMT01_HTTP_UPGRADE_HOSTS = ("arxiv.org", "www.arxiv.org")
S2PMT01_ALLOWED_URL_HOST_SUFFIXES = (
    "arxiv.org",
    "biorxiv.org",
    "medrxiv.org",
    "nature.com",
    "science.org",
    "thelancet.com",
    "github.com",
    "nih.gov",
    "ncbi.nlm.nih.gov",
    "example.test",
)
S2PMT01_FRONTSTAGE_STATEMENT_TYPES = ("fact", "inference", "hypothesis", "action")
S2PMT01_REQUIRED_BOUNDARY_FLAGS = (
    "untrusted_source_content",
    "typed_frontstage_statements",
    "safe_source_urls",
    "zero_critical_claim_blocks",
    "supply_chain_baseline_declared",
    "no_tool_execution_from_content",
    "no_secret_logging",
)
S2PMT01_REQUIRED_SUPPLY_CHAIN_CONTROLS = (
    "dependency_inventory",
    "workflow_permission_review",
    "action_reference_inventory",
    "secret_exposure_boundary",
    "artifact_provenance_required",
)


def sanitize_public_url(value: str, *, allow_http: bool = True) -> str:
    """Return a public URL safe for reports/emails, or an empty string."""

    raw = str(value or "").strip()
    if not raw or _has_control_char(raw):
        return ""
    try:
        parsed = urlsplit(raw)
    except ValueError:
        return ""
    scheme = parsed.scheme.lower()
    host = (parsed.hostname or "").lower().rstrip(".")
    if not scheme or not host:
        return ""
    if parsed.username or parsed.password:
        return ""
    if scheme not in S2PMT01_ALLOWED_URL_SCHEMES:
        return ""
    if scheme == "http" and host in S2PMT01_HTTP_UPGRADE_HOSTS:
        scheme = "https"
    elif scheme == "http" and not allow_http:
        return ""
    if not _host_allowed(host):
        return ""
    return urlunsplit((scheme, parsed.netloc, parsed.path, parsed.query, parsed.fragment))


def typed_fact(statement: str, *, claim_ids: Sequence[str], evidence_ids: Sequence[str]) -> dict[str, Any]:
    return {
        "statement_type": "fact",
        "text": _clean_text(statement),
        "claim_ids": [str(item) for item in claim_ids if str(item)],
        "evidence_ids": [str(item) for item in evidence_ids if str(item)],
    }


def typed_inference(
    statement: str,
    *,
    premise_claim_ids: Sequence[str],
    reasoning_version: str,
    confidence: float,
) -> dict[str, Any]:
    return {
        "statement_type": "inference",
        "text": _clean_text(statement),
        "premise_claim_ids": [str(item) for item in premise_claim_ids if str(item)],
        "reasoning_version": str(reasoning_version),
        "confidence": float(confidence),
    }


def typed_hypothesis(statement: str, *, premise_claim_ids: Sequence[str], confidence: float) -> dict[str, Any]:
    return {
        "statement_type": "hypothesis",
        "text": _clean_text(statement),
        "premise_claim_ids": [str(item) for item in premise_claim_ids if str(item)],
        "confidence": float(confidence),
    }


def typed_action(statement: str, *, premise_claim_ids: Sequence[str], action_scope: str) -> dict[str, Any]:
    return {
        "statement_type": "action",
        "text": _clean_text(statement),
        "premise_claim_ids": [str(item) for item in premise_claim_ids if str(item)],
        "action_scope": str(action_scope),
    }


def validate_typed_frontstage(frontstage: Mapping[str, Any], *, allowed_claim_ids: Sequence[str]) -> list[str]:
    """Validate S2PMT01 typed frontstage statement bindings."""

    errors: list[str] = []
    allowed = {str(item) for item in allowed_claim_ids if str(item)}
    statements = frontstage.get("typed_statements")
    if not isinstance(statements, list) or not statements:
        return ["frontstage.typed_statements must be a non-empty array"]
    seen_types: set[str] = set()
    for index, statement in enumerate(statements):
        if not isinstance(statement, Mapping):
            errors.append(f"frontstage.typed_statements[{index}] must be an object")
            continue
        statement_type = str(statement.get("statement_type") or "")
        seen_types.add(statement_type)
        if statement_type not in S2PMT01_FRONTSTAGE_STATEMENT_TYPES:
            errors.append(f"frontstage.typed_statements[{index}].statement_type is invalid")
        if not _clean_text(str(statement.get("text") or "")):
            errors.append(f"frontstage.typed_statements[{index}].text is required")
        if statement_type == "fact":
            _validate_claim_refs(errors, statement.get("claim_ids"), allowed, f"frontstage.typed_statements[{index}].claim_ids")
            evidence_ids = statement.get("evidence_ids")
            if not isinstance(evidence_ids, list) or not [item for item in evidence_ids if str(item)]:
                errors.append(f"frontstage.typed_statements[{index}].evidence_ids must be non-empty")
        elif statement_type in {"inference", "hypothesis", "action"}:
            _validate_claim_refs(
                errors,
                statement.get("premise_claim_ids"),
                allowed,
                f"frontstage.typed_statements[{index}].premise_claim_ids",
            )
            if statement_type == "inference":
                if not statement.get("reasoning_version"):
                    errors.append(f"frontstage.typed_statements[{index}].reasoning_version is required")
                if not _valid_confidence(statement.get("confidence")):
                    errors.append(f"frontstage.typed_statements[{index}].confidence must be between 0 and 1")
            if statement_type == "hypothesis" and not _valid_confidence(statement.get("confidence")):
                errors.append(f"frontstage.typed_statements[{index}].confidence must be between 0 and 1")
            if statement_type == "action" and not statement.get("action_scope"):
                errors.append(f"frontstage.typed_statements[{index}].action_scope is required")
    for required_type in ("fact", "inference", "action"):
        if required_type not in seen_types:
            errors.append(f"frontstage.typed_statements must include {required_type}")
    return errors


def build_trust_boundary_receipt(source_item: Mapping[str, Any]) -> dict[str, Any]:
    source_url = sanitize_public_url(str(source_item.get("canonical_url") or ""))
    refs = []
    for ref in source_item.get("content_refs") or []:
        if isinstance(ref, Mapping):
            safe = sanitize_public_url(str(ref.get("uri") or ref.get("url") or ""))
            if safe:
                refs.append(safe)
    return {
        "model_id": S2PMT01_SECURITY_MODEL_ID,
        "task_id": S2PMT01_TASK_ID,
        "acceptance_id": S2PMT01_ACCEPTANCE_ID,
        "source_content_trust": S2PMT01_UNTRUSTED_DATA_LABEL,
        "source_url": source_url,
        "content_ref_urls": refs,
        "tool_policy": {
            "source_content_can_request_tools": False,
            "model_can_execute_repository_writes": False,
            "model_can_send_email": False,
            "model_can_read_secrets": False,
            "executor_requires_schema_valid_action": True,
        },
        "output_policy": {
            "typed_frontstage_statements_required": True,
            "fact_requires_claim_ids_and_evidence_ids": True,
            "inference_requires_premises_reasoning_confidence": True,
            "unsafe_url_rendering_allowed": False,
        },
    }


def validate_trust_boundary_receipt(receipt: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if receipt.get("source_content_trust") != S2PMT01_UNTRUSTED_DATA_LABEL:
        errors.append("source content must be labeled UNTRUSTED_DATA")
    if not receipt.get("source_url"):
        errors.append("trust boundary receipt requires a safe source_url")
    tool_policy = receipt.get("tool_policy") if isinstance(receipt.get("tool_policy"), Mapping) else {}
    for key in (
        "source_content_can_request_tools",
        "model_can_execute_repository_writes",
        "model_can_send_email",
        "model_can_read_secrets",
    ):
        if tool_policy.get(key) is not False:
            errors.append(f"tool_policy.{key} must be false")
    if tool_policy.get("executor_requires_schema_valid_action") is not True:
        errors.append("tool_policy.executor_requires_schema_valid_action must be true")
    output_policy = receipt.get("output_policy") if isinstance(receipt.get("output_policy"), Mapping) else {}
    for key in (
        "typed_frontstage_statements_required",
        "fact_requires_claim_ids_and_evidence_ids",
        "inference_requires_premises_reasoning_confidence",
    ):
        if output_policy.get(key) is not True:
            errors.append(f"output_policy.{key} must be true")
    if output_policy.get("unsafe_url_rendering_allowed") is not False:
        errors.append("output_policy.unsafe_url_rendering_allowed must be false")
    return errors


def build_supply_chain_baseline(*, workflow_files: Sequence[str], dependency_files: Sequence[str]) -> dict[str, Any]:
    return {
        "model_id": S2PMT01_SECURITY_MODEL_ID,
        "task_id": S2PMT01_TASK_ID,
        "acceptance_id": S2PMT01_ACCEPTANCE_ID,
        "controls": {
            "dependency_inventory": sorted(str(path) for path in dependency_files),
            "workflow_permission_review": sorted(str(path) for path in workflow_files),
            "action_reference_inventory": sorted(str(path) for path in workflow_files),
            "secret_exposure_boundary": "secrets are never printed, committed, or copied into generated evidence",
            "artifact_provenance_required": True,
        },
        "production_side_effects": False,
    }


def validate_supply_chain_baseline(baseline: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    controls = baseline.get("controls") if isinstance(baseline.get("controls"), Mapping) else {}
    for key in S2PMT01_REQUIRED_SUPPLY_CHAIN_CONTROLS:
        if not controls.get(key):
            errors.append(f"supply_chain.controls.{key} is required")
    if baseline.get("production_side_effects") is not False:
        errors.append("supply chain baseline must not create production side effects")
    return errors


def _validate_claim_refs(errors: list[str], value: Any, allowed: set[str], path: str) -> None:
    if not isinstance(value, list) or not [item for item in value if str(item)]:
        errors.append(f"{path} must be non-empty")
        return
    unknown = sorted({str(item) for item in value if str(item)} - allowed)
    if unknown:
        errors.append(f"{path} contains unknown claim ids: {', '.join(unknown)}")


def _host_allowed(host: str) -> bool:
    return any(host == suffix or host.endswith("." + suffix) for suffix in S2PMT01_ALLOWED_URL_HOST_SUFFIXES)


def _has_control_char(value: str) -> bool:
    return any(ord(char) < 32 for char in value)


def _valid_confidence(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and 0.0 <= float(value) <= 1.0


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()
