"""Deterministic Phase 4 ranking and queue audit."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from .contracts import validate_evidence_claim, validate_source_item


COMPONENT_WEIGHTS: dict[str, float] = {
    "frontier_signal": 20.0,
    "evidence_reliability": 20.0,
    "novelty": 15.0,
    "transfer_value": 15.0,
    "problem_importance": 10.0,
    "taxonomy_priority": 10.0,
    "waiting_time": 5.0,
    "diversity": 5.0,
}
WEIGHT_TARGET = 100.0
WEIGHT_TOLERANCE = 0.0001


class RankingError(ValueError):
    """Raised when ranking input cannot be audited deterministically."""


def validate_ranking_weights(weights: Mapping[str, float] = COMPONENT_WEIGHTS) -> list[str]:
    errors: list[str] = []
    missing = sorted(set(COMPONENT_WEIGHTS) - set(weights))
    extra = sorted(set(weights) - set(COMPONENT_WEIGHTS))
    if missing:
        errors.append("ranking weights missing components: " + ", ".join(missing))
    if extra:
        errors.append("ranking weights contain unknown components: " + ", ".join(extra))
    total = sum(float(value) for value in weights.values())
    if abs(total - WEIGHT_TARGET) > WEIGHT_TOLERANCE:
        errors.append(f"ranking weights must sum to {WEIGHT_TARGET:g}; got {total:g}")
    return errors


def audit_candidate(candidate: Mapping[str, Any], *, recent_source_ids: Iterable[str] = ()) -> dict[str, Any]:
    source_item = candidate.get("source_item")
    evidence_claims = candidate.get("evidence_claims")
    recent = {str(item) for item in recent_source_ids}
    blocking_reasons = _eligibility_errors(source_item, evidence_claims, recent)
    component_scores: dict[str, float] = {}
    if not blocking_reasons:
        component_scores, blocking_reasons = _component_scores(candidate.get("signals"))
    total_score = round(sum(component_scores.values()), 4) if not blocking_reasons else 0.0
    source_id = _source_id(source_item)
    return {
        "source_id": source_id,
        "stable_id": source_item.get("stable_id", "") if isinstance(source_item, Mapping) else "",
        "title": source_item.get("title", "") if isinstance(source_item, Mapping) else "",
        "eligible": not blocking_reasons,
        "blocking_reasons": blocking_reasons,
        "component_scores": component_scores,
        "total_score": total_score,
        "weight_version": "adp-ranking-parameters-v1",
    }


def rank_candidates(candidates: Sequence[Mapping[str, Any]], *, recent_source_ids: Iterable[str] = ()) -> list[dict[str, Any]]:
    audits = [audit_candidate(candidate, recent_source_ids=recent_source_ids) for candidate in candidates]
    return sorted(audits, key=lambda audit: (not audit["eligible"], -float(audit["total_score"]), str(audit["source_id"])))


def selection_payload(candidates: Sequence[Mapping[str, Any]], *, recent_source_ids: Iterable[str] = ()) -> dict[str, Any]:
    audits = rank_candidates(candidates, recent_source_ids=recent_source_ids)
    selected = next((audit for audit in audits if audit["eligible"]), None)
    return {
        "status": "pass" if selected else "blocked",
        "selected": selected,
        "audits": audits,
    }


def select_daily_candidate(candidates: Sequence[Mapping[str, Any]], *, recent_source_ids: Iterable[str] = ()) -> dict[str, Any]:
    payload = selection_payload(candidates, recent_source_ids=recent_source_ids)
    if payload["selected"] is None:
        raise RankingError("No eligible candidates after evidence and metadata gates")
    return payload["selected"]


def _eligibility_errors(source_item: Any, evidence_claims: Any, recent_source_ids: set[str]) -> list[str]:
    errors: list[str] = []
    if not isinstance(source_item, Mapping):
        return ["candidate.source_item must be an object"]
    source_errors = validate_source_item(source_item)
    errors.extend("source_item: " + error for error in source_errors)
    source_id = _source_id(source_item)
    if source_id in recent_source_ids:
        errors.append("candidate was already selected recently")
    errors.extend(_metadata_conflict_errors(source_item))
    if not isinstance(evidence_claims, list) or not evidence_claims:
        errors.append("P0 evidence is required before ranking")
        return errors
    p0_count = 0
    for index, claim in enumerate(evidence_claims):
        if not isinstance(claim, Mapping):
            errors.append(f"evidence_claims[{index}] must be an object")
            continue
        claim_errors = validate_evidence_claim(claim)
        errors.extend(f"evidence_claims[{index}]: {error}" for error in claim_errors)
        if claim.get("source_id") != source_id:
            errors.append(f"evidence_claims[{index}].source_id must match candidate source_id")
        if claim.get("priority") == "P0":
            p0_count += 1
            if claim.get("support_status") != "supported":
                errors.append(f"evidence_claims[{index}] P0 support_status must be supported")
    if p0_count == 0:
        errors.append("at least one P0 evidence claim is required before ranking")
    return errors


def _metadata_conflict_errors(source_item: Mapping[str, Any]) -> list[str]:
    metadata = source_item.get("metadata")
    if not isinstance(metadata, Mapping):
        return []
    conflicts: list[str] = []
    if metadata.get("conflict") is True or metadata.get("status") == "conflict":
        conflicts.append("source metadata reports conflict")
    raw_conflicts = metadata.get("metadata_conflicts")
    if isinstance(raw_conflicts, list) and raw_conflicts:
        conflicts.append("source metadata_conflicts is non-empty")
    arxiv = metadata.get("arxiv")
    if isinstance(arxiv, Mapping):
        if arxiv.get("conflict") is True or arxiv.get("status") == "conflict":
            conflicts.append("arXiv metadata reports conflict")
        arxiv_conflicts = arxiv.get("metadata_conflicts")
        if isinstance(arxiv_conflicts, list) and arxiv_conflicts:
            conflicts.append("arXiv metadata_conflicts is non-empty")
    return conflicts


def _component_scores(signals: Any) -> tuple[dict[str, float], list[str]]:
    if not isinstance(signals, Mapping):
        return {}, ["candidate.signals must be an object"]
    errors: list[str] = []
    scores: dict[str, float] = {}
    for component, weight in COMPONENT_WEIGHTS.items():
        value = signals.get(component)
        if not isinstance(value, (int, float)):
            errors.append(f"signals.{component} must be a number between 0 and 1")
            continue
        numeric = float(value)
        if numeric < 0.0 or numeric > 1.0:
            errors.append(f"signals.{component} must be between 0 and 1")
            continue
        scores[component] = round(numeric * weight, 4)
    return ({} if errors else scores), errors


def _source_id(source_item: Any) -> str:
    if isinstance(source_item, Mapping):
        return str(source_item.get("source_id") or "")
    return ""
