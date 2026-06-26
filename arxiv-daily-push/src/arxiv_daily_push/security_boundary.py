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
    "workflow_audit",
    "action_reference_policy",
    "dependency_vulnerability_gate",
    "secret_exposure_boundary",
    "artifact_provenance_required",
)
S2PMT01_APPROVED_MUTABLE_ACTION_REFS = {
    "actions/checkout@v4": "GitHub-owned action pinned to major version for existing ADP CI compatibility; production enablement still requires independent review.",
    "actions/checkout@v5": "GitHub-owned action pinned to major version for project governance CI compatibility; production enablement still requires independent review.",
    "actions/setup-python@v5": "GitHub-owned action pinned to major version for existing ADP CI compatibility; production enablement still requires independent review.",
    "actions/setup-python@v6": "GitHub-owned action pinned to major version for project governance CI compatibility; production enablement still requires independent review.",
    "actions/upload-artifact@v4": "GitHub-owned action pinned to major version for existing evidence artifact compatibility; production enablement still requires independent review.",
    "actions/upload-artifact@v7": "GitHub-owned action pinned to major version for project governance evidence artifacts; production enablement still requires independent review.",
}
S2PMT01_BLOCKING_VULNERABILITY_SEVERITIES = ("critical", "high")


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


def build_supply_chain_baseline(
    *,
    workflow_files: Sequence[str],
    dependency_files: Sequence[str],
    workflow_contents: Mapping[str, str] | None = None,
    vulnerability_findings: Sequence[Mapping[str, Any]] | None = None,
    approved_vulnerability_exceptions: Sequence[Mapping[str, Any]] | None = None,
    approved_mutable_action_refs: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    action_policy = dict(S2PMT01_APPROVED_MUTABLE_ACTION_REFS)
    if approved_mutable_action_refs:
        action_policy.update({str(ref): str(reason) for ref, reason in approved_mutable_action_refs.items()})
    workflow_audit = audit_workflow_supply_chain(workflow_contents or {}, approved_mutable_action_refs=action_policy)
    vulnerability_gate = build_dependency_vulnerability_gate(
        vulnerability_findings or [],
        approved_exceptions=approved_vulnerability_exceptions or [],
    )
    return {
        "model_id": S2PMT01_SECURITY_MODEL_ID,
        "task_id": S2PMT01_TASK_ID,
        "acceptance_id": S2PMT01_ACCEPTANCE_ID,
        "controls": {
            "dependency_inventory": sorted(str(path) for path in dependency_files),
            "workflow_permission_review": sorted(str(path) for path in workflow_files),
            "action_reference_inventory": sorted(str(path) for path in workflow_files),
            "workflow_audit": workflow_audit,
            "action_reference_policy": {
                "full_commit_sha_allowed": True,
                "mutable_action_refs_require_approval": True,
                "approved_mutable_action_refs": action_policy,
            },
            "dependency_vulnerability_gate": vulnerability_gate,
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
    workflow_audit = controls.get("workflow_audit") if isinstance(controls.get("workflow_audit"), Mapping) else {}
    for issue in workflow_audit.get("issues") or []:
        errors.append(f"supply_chain.workflow_audit: {issue}")
    if workflow_audit.get("status") not in {None, "pass"}:
        errors.append("supply_chain.workflow_audit.status must be pass")
    vulnerability_gate = (
        controls.get("dependency_vulnerability_gate")
        if isinstance(controls.get("dependency_vulnerability_gate"), Mapping)
        else {}
    )
    for issue in vulnerability_gate.get("issues") or []:
        errors.append(f"supply_chain.dependency_vulnerability_gate: {issue}")
    if vulnerability_gate.get("status") not in {None, "pass"}:
        errors.append("supply_chain.dependency_vulnerability_gate.status must be pass")
    if baseline.get("production_side_effects") is not False:
        errors.append("supply chain baseline must not create production side effects")
    return errors


def audit_workflow_supply_chain(
    workflow_contents: Mapping[str, str],
    *,
    approved_mutable_action_refs: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Audit workflow permissions and action refs without executing workflows."""

    approvals = approved_mutable_action_refs or S2PMT01_APPROVED_MUTABLE_ACTION_REFS
    issues: list[str] = []
    action_refs: list[dict[str, Any]] = []
    permission_refs: list[dict[str, Any]] = []
    for path, text in sorted((str(path), str(text)) for path, text in workflow_contents.items()):
        for line_number, raw_line in enumerate(text.splitlines(), start=1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if re.match(r"^permissions:\s*write-all\s*$", line):
                issues.append(f"{path}:{line_number} permissions: write-all is forbidden")
            permission_match = re.match(r"^([A-Za-z0-9_-]+):\s*(read|write|none)\s*(?:#.*)?$", line)
            if permission_match:
                scope, access = permission_match.groups()
                if scope in {"contents", "actions", "checks", "deployments", "id-token", "issues", "packages", "pull-requests"}:
                    permission_refs.append({"path": path, "line": line_number, "scope": scope, "access": access})
                    if access == "write":
                        issues.append(f"{path}:{line_number} permission {scope}: write is forbidden for ADP supply-chain baseline")
            uses_match = re.match(r"^(?:-\s*)?uses:\s*([^\s#]+)", line)
            if not uses_match:
                continue
            ref = uses_match.group(1).strip().strip("'\"")
            status = "local" if ref.startswith("./") else "external"
            reason = ""
            if status == "external":
                if "@" not in ref:
                    issues.append(f"{path}:{line_number} action reference {ref} is missing an explicit ref")
                    status = "invalid"
                else:
                    _action, version = ref.rsplit("@", 1)
                    if re.fullmatch(r"[0-9a-fA-F]{40}", version):
                        status = "sha_pinned"
                    elif ref in approvals and approvals[ref]:
                        status = "approved_mutable_ref"
                        reason = str(approvals[ref])
                    else:
                        status = "unapproved_mutable_ref"
                        issues.append(f"{path}:{line_number} action reference {ref} is not SHA-pinned or approved")
            action_refs.append({"path": path, "line": line_number, "ref": ref, "status": status, "approval_reason": reason})
    return {
        "status": "pass" if not issues else "blocked",
        "workflow_count": len(workflow_contents),
        "action_refs": action_refs,
        "permission_refs": permission_refs,
        "issues": issues,
    }


def build_dependency_vulnerability_gate(
    vulnerability_findings: Sequence[Mapping[str, Any]],
    *,
    approved_exceptions: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    approved = {str(item.get("finding_id") or item.get("id")): item for item in approved_exceptions if item.get("finding_id") or item.get("id")}
    issues: list[str] = []
    normalized_findings: list[dict[str, Any]] = []
    normalized_exceptions: list[dict[str, Any]] = []
    for exception in approved.values():
        exception_id = str(exception.get("finding_id") or exception.get("id") or "")
        missing = [key for key in ("approved_by", "expires_at", "rationale") if not str(exception.get(key) or "").strip()]
        if missing:
            issues.append(f"vulnerability exception {exception_id} missing {', '.join(missing)}")
        normalized_exceptions.append(
            {
                "finding_id": exception_id,
                "approved_by": str(exception.get("approved_by") or ""),
                "expires_at": str(exception.get("expires_at") or ""),
                "rationale": str(exception.get("rationale") or ""),
            }
        )
    for finding in vulnerability_findings:
        finding_id = str(finding.get("finding_id") or finding.get("id") or "")
        severity = str(finding.get("severity") or "").lower()
        package = str(finding.get("package") or finding.get("dependency") or "")
        normalized_findings.append({"finding_id": finding_id, "severity": severity, "package": package})
        if severity in S2PMT01_BLOCKING_VULNERABILITY_SEVERITIES and finding_id not in approved:
            issues.append(f"{severity} vulnerability {finding_id or '<missing-id>'} for {package or '<unknown-package>'} has no approved exception")
    return {
        "status": "pass" if not issues else "blocked",
        "blocking_severities": list(S2PMT01_BLOCKING_VULNERABILITY_SEVERITIES),
        "findings": normalized_findings,
        "approved_exceptions": normalized_exceptions,
        "issues": issues,
    }


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
