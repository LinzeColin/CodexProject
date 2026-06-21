"""Phase 5 Claim Ledger and publication gate."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .contracts import stable_content_hash, validate_evidence_claim, validate_publication, validate_source_item


PEER_REVIEW_TERMS = ("peer reviewed", "peer-reviewed", "同行评审", "同儕審查")


class EvidenceGateError(ValueError):
    """Raised when evidence gate input cannot be evaluated."""


def build_claim_ledger(source_item: Mapping[str, Any], claims: Sequence[Mapping[str, Any]], *, extracted_at: str) -> dict[str, Any]:
    source_errors = validate_source_item(source_item)
    if source_errors:
        raise EvidenceGateError("; ".join(source_errors))
    source_id = str(source_item["source_id"])
    normalized_claims = [_normalize_claim(source_id, claim, index=index, extracted_at=extracted_at) for index, claim in enumerate(claims)]
    claim_results = [_evaluate_claim(source_item, claim, index=index) for index, claim in enumerate(normalized_claims)]
    blocking_reasons = [reason for result in claim_results for reason in result["blocking_reasons"]]
    blocking_reasons.extend(_metadata_blockers(source_item))
    return {
        "ledger_id": f"claim-ledger:{source_id}:{stable_content_hash({'claims': normalized_claims})[:12]}",
        "source_id": source_id,
        "status": "blocked" if blocking_reasons else "pass",
        "claims": normalized_claims,
        "claim_results": claim_results,
        "blocking_reasons": blocking_reasons,
        "extracted_at": extracted_at,
    }


def gate_publication(
    source_item: Mapping[str, Any],
    claims: Sequence[Mapping[str, Any]],
    *,
    run_id: str,
    publication_id: str,
    publication_type: str = "daily",
    created_at: str,
) -> dict[str, Any]:
    ledger = build_claim_ledger(source_item, claims, extracted_at=created_at)
    ledger_sha256 = stable_content_hash(ledger)
    publication = {
        "publication_id": publication_id,
        "run_id": run_id,
        "publication_type": publication_type,
        "status": "blocked" if ledger["blocking_reasons"] else "ready",
        "artifacts": [
            {
                "artifact_type": "claim_ledger",
                "path": ledger["ledger_id"],
                "sha256": ledger_sha256,
                "size_bytes": len(ledger_sha256),
            }
        ],
        "created_at": created_at,
    }
    publication_errors = validate_publication(publication)
    if publication_errors:
        raise EvidenceGateError("; ".join(publication_errors))
    return {
        "publish_allowed": not ledger["blocking_reasons"],
        "blocking_reasons": ledger["blocking_reasons"],
        "claim_count": len(ledger["claims"]),
        "p0_claim_count": sum(1 for claim in ledger["claims"] if claim.get("priority") == "P0"),
        "ledger": ledger,
        "publication": publication,
    }


def _normalize_claim(source_id: str, claim: Mapping[str, Any], *, index: int, extracted_at: str) -> dict[str, Any]:
    normalized = dict(claim)
    normalized.setdefault("source_id", source_id)
    normalized.setdefault("extracted_at", extracted_at)
    if not normalized.get("claim_id"):
        normalized["claim_id"] = f"claim:{source_id}:{index}:{stable_content_hash(normalized)[:8]}"
    return normalized



def _evaluate_claim(source_item: Mapping[str, Any], claim: Mapping[str, Any], *, index: int) -> dict[str, Any]:
    errors = [f"claim[{index}]: {error}" for error in validate_evidence_claim(claim)]
    if claim.get("source_id") != source_item.get("source_id"):
        errors.append(f"claim[{index}].source_id must match SourceItem.source_id")
    if claim.get("priority") == "P0" and claim.get("support_status") != "supported":
        errors.append(f"claim[{index}] P0 support_status must be supported")
    if claim.get("priority") == "P0" and _is_peer_review_claim(str(claim.get("statement") or "")):
        stable_url = str((claim.get("locator") or {}).get("stable_url") or "")
        if source_item.get("source_type") == "arxiv" and ("arxiv.org" in stable_url or not stable_url):
            errors.append(f"claim[{index}] peer-review status needs independent non-arXiv evidence")
    return {
        "claim_id": claim.get("claim_id", ""),
        "priority": claim.get("priority", ""),
        "support_status": claim.get("support_status", ""),
        "blocking_reasons": errors,
    }


def _metadata_blockers(source_item: Mapping[str, Any]) -> list[str]:
    metadata = source_item.get("metadata")
    if not isinstance(metadata, Mapping):
        return ["SourceItem.metadata must be an object"]
    blockers: list[str] = []
    if metadata.get("conflict") is True or metadata.get("status") == "conflict":
        blockers.append("source metadata reports conflict")
    conflicts = metadata.get("metadata_conflicts")
    if isinstance(conflicts, list) and conflicts:
        blockers.append("source metadata_conflicts is non-empty")
    arxiv = metadata.get("arxiv")
    if isinstance(arxiv, Mapping):
        if arxiv.get("conflict") is True or arxiv.get("status") == "conflict":
            blockers.append("arXiv metadata reports conflict")
        arxiv_conflicts = arxiv.get("metadata_conflicts")
        if isinstance(arxiv_conflicts, list) and arxiv_conflicts:
            blockers.append("arXiv metadata_conflicts is non-empty")
    return blockers


def _is_peer_review_claim(statement: str) -> bool:
    lower = statement.lower()
    return any(term in lower for term in PEER_REVIEW_TERMS)
