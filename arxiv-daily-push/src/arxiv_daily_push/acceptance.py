"""Phase 11 acceptance and handoff readiness gate."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .config import DEFAULT_RECIPIENT
from .handoff import validate_handoff
from .trial import TRIAL_EVIDENCE_VALIDATOR_ID


class AcceptanceError(ValueError):
    """Raised when the Phase 11 package would make an unsupported acceptance claim."""


PRODUCTION_REQUIREMENTS = (
    ("thirty_day_trial_passed", "30 unique-date operational coverage evidence"),
    ("scheduler_operational", "05:00 scheduler and manual rerun evidence"),
    ("text_artifacts_verified", "Stage 1 text artifact evidence"),
    ("real_smtp_verified", "real SMTP notification evidence"),
    ("resource_pressure_ok", "disk, cache, memory, and secret hygiene evidence"),
)


def build_acceptance_package(
    handoff: Mapping[str, Any],
    *,
    generated_at: str,
    operational_evidence: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    handoff_errors = validate_handoff(handoff)
    if handoff_errors:
        raise AcceptanceError("; ".join(handoff_errors))

    evidence = _normalize_operational_evidence(operational_evidence or {})
    requirements = [
        {
            "requirement_id": key,
            "description": description,
            "passed": _requirement_passed(evidence, key),
            "evidence_ref": str(evidence.get(f"{key}_ref") or ""),
        }
        for key, description in PRODUCTION_REQUIREMENTS
    ]
    accepted_for_production = all(requirement["passed"] for requirement in requirements)
    blocking_reasons = [] if accepted_for_production else [
        f"missing {requirement['description']}"
        for requirement in requirements
        if not requirement["passed"]
    ]
    handoff_id = str(handoff.get("handoff_id") or "handoff:unknown")
    return {
        "acceptance_id": f"acceptance:{handoff_id}",
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "handoff_id": handoff_id,
        "run_id": str(handoff.get("run_id") or ""),
        "recipient": str((handoff.get("email_transport_gate") or {}).get("recipient") or DEFAULT_RECIPIENT),
        "dry_run_handoff_status": "pass",
        "production_acceptance_status": "pass" if accepted_for_production else "blocked",
        "accepted_for_production": accepted_for_production,
        "requirements": requirements,
        "evidence_validator": str(evidence.get("_validated_by") or ""),
        "trial_evidence_id": str(evidence.get("_trial_evidence_id") or ""),
        "blocking_reasons": blocking_reasons,
        "no_claims": {
            "does_not_claim_30_day_trial": not accepted_for_production,
            "does_not_claim_real_smtp_sent": not accepted_for_production,
            "does_not_claim_text_artifacts_verified": not accepted_for_production,
            "does_not_claim_release_uploaded": True,
            "does_not_claim_scheduler_enabled": not accepted_for_production,
        },
        "local_pressure_policy": {
            "media_artifacts_retained": False,
            "model_cache_retained": False,
            "dependency_cache_retained": False,
            "secrets_in_repository_allowed": False,
        },
        "next_actions": [
            "provision private self-hosted runner and scheduler evidence",
            "configure external SMTP secret and verify real notification delivery",
            "verify Stage 1 text artifacts in GitHub Actions artifacts",
            "run and archive 30 unique-date operational coverage evidence",
            "rerun acceptance with operational_evidence refs before claiming production pass",
        ],
    }


def validate_acceptance_package(package: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    requirements = package.get("requirements")
    if not isinstance(requirements, list) or not requirements:
        errors.append("acceptance.requirements must be a non-empty list")
        return errors

    accepted = bool(package.get("accepted_for_production"))
    failed_requirements = [
        str(requirement.get("requirement_id"))
        for requirement in requirements
        if isinstance(requirement, Mapping) and requirement.get("passed") is not True
    ]
    blocking_reasons = package.get("blocking_reasons")
    if accepted and failed_requirements:
        errors.append("accepted_for_production cannot be true when requirements are missing: " + ", ".join(failed_requirements))
    if accepted and blocking_reasons:
        errors.append("accepted_for_production cannot be true with blocking_reasons")
    if accepted and package.get("evidence_validator") != TRIAL_EVIDENCE_VALIDATOR_ID:
        errors.append("accepted_for_production requires validated trial evidence")
    if accepted and not str(package.get("trial_evidence_id") or "").strip():
        errors.append("accepted_for_production requires trial_evidence_id")
    if not accepted and not blocking_reasons:
        errors.append("blocked acceptance must include blocking_reasons")
    no_claims = package.get("no_claims")
    if not accepted:
        if not isinstance(no_claims, Mapping) or no_claims.get("does_not_claim_30_day_trial") is not True:
            errors.append("blocked acceptance must explicitly avoid claiming a 30-day trial")
    return errors


def _requirement_passed(evidence: Mapping[str, Any], key: str) -> bool:
    return (
        evidence.get("_validated_by") == TRIAL_EVIDENCE_VALIDATOR_ID
        and evidence.get("_validated_report") is True
        and bool(evidence.get(key))
        and bool(str(evidence.get(f"{key}_ref") or "").strip())
    )


def _normalize_operational_evidence(evidence: Mapping[str, Any]) -> Mapping[str, Any]:
    if evidence.get("validator_id") == TRIAL_EVIDENCE_VALIDATOR_ID and isinstance(evidence.get("operational_evidence"), Mapping):
        normalized = dict(evidence["operational_evidence"])
        normalized["_validated_report"] = True
        return normalized
    return evidence
