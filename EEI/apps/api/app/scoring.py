from __future__ import annotations

from typing import Any

CANDIDATE_SOURCE_THRESHOLD_MIN = 2
ENTITY_SOURCE_THRESHOLD_MIN = 1
ENTITY_RELATIONSHIP_CONTEXT_MIN = 3
ENTITY_RELATIONSHIP_FAMILY_CONTEXT_MIN = 3


def candidate_score_metrics(
    *,
    confidence: float,
    independent_source_count: int,
    source_threshold_met: bool,
    review_status: str,
    publication_status: str,
    parser_version_present: bool,
    evidence_present: bool,
) -> dict[str, Any]:
    source_threshold_ratio = min(
        independent_source_count / CANDIDATE_SOURCE_THRESHOLD_MIN,
        1,
    )
    raw_score = round(confidence * 100, 2)
    evidence_quality = round(source_threshold_ratio * 100, 2)
    adjusted_score = round(raw_score * (evidence_quality / 100), 2)
    present_inputs = [
        confidence is not None,
        independent_source_count is not None,
        parser_version_present,
        bool(review_status),
        evidence_present,
    ]
    coverage = round((sum(1 for item in present_inputs if item) / len(present_inputs)) * 100, 2)
    missing_inputs: list[str] = []
    if not source_threshold_met:
        missing_inputs.append(
            f"independent_source_threshold>={CANDIDATE_SOURCE_THRESHOLD_MIN}"
        )
    if review_status != "human_verified":
        missing_inputs.append("human_review_verification")
    if publication_status != "published":
        missing_inputs.append("published_relationship_version")
    if not evidence_present:
        missing_inputs.append("evidence_chain")
    return {
        "source_threshold": {
            "minimum_independent_sources": CANDIDATE_SOURCE_THRESHOLD_MIN,
            "independent_source_count": independent_source_count,
            "met": source_threshold_met,
        },
        "raw_score": raw_score,
        "evidence_quality": evidence_quality,
        "adjusted_score": adjusted_score,
        "coverage": coverage,
        "contributions": [
            {
                "input": "candidate_confidence",
                "value": confidence,
                "score_points": raw_score,
            },
            {
                "input": "independent_source_count",
                "value": independent_source_count,
                "score_multiplier": source_threshold_ratio,
            },
            {
                "input": "review_status",
                "value": review_status,
                "publication_gate_passed": review_status == "human_verified",
            },
            {
                "input": "publication_status",
                "value": publication_status,
                "included_in_graph_edges": publication_status == "published",
            },
        ],
        "missing_inputs": missing_inputs,
    }


def relationship_score_metrics(
    *,
    confidence: float,
    independent_source_count: int,
    source_threshold_met: bool,
    review_status: str,
    publication_status: str,
    fact_version_present: bool,
    evidence_present: bool,
    minimum_independent_sources: int = CANDIDATE_SOURCE_THRESHOLD_MIN,
) -> dict[str, Any]:
    minimum_independent_sources = max(minimum_independent_sources, 1)
    source_threshold_ratio = min(
        independent_source_count / minimum_independent_sources,
        1,
    )
    raw_score = round(confidence * 100, 2)
    evidence_quality = round(source_threshold_ratio * 100, 2)
    adjusted_score = round(raw_score * (evidence_quality / 100), 2)
    present_inputs = [
        confidence is not None,
        independent_source_count is not None,
        bool(review_status),
        fact_version_present,
        evidence_present,
    ]
    coverage = round((sum(1 for item in present_inputs if item) / len(present_inputs)) * 100, 2)
    missing_inputs: list[str] = []
    if not source_threshold_met:
        missing_inputs.append(
            f"independent_source_threshold>={minimum_independent_sources}"
        )
    if review_status != "human_verified":
        missing_inputs.append("human_review_verification")
    if publication_status != "published":
        missing_inputs.append("published_relationship_version")
    if not fact_version_present:
        missing_inputs.append("relationship_fact_version")
    if not evidence_present:
        missing_inputs.append("evidence_chain")
    return {
        "source_threshold": {
            "minimum_independent_sources": minimum_independent_sources,
            "independent_source_count": independent_source_count,
            "met": source_threshold_met,
        },
        "raw_score": raw_score,
        "evidence_quality": evidence_quality,
        "adjusted_score": adjusted_score,
        "coverage": coverage,
        "contributions": [
            {
                "input": "relationship_confidence",
                "value": confidence,
                "score_points": raw_score,
            },
            {
                "input": "independent_source_count",
                "value": independent_source_count,
                "score_multiplier": source_threshold_ratio,
            },
            {
                "input": "review_status",
                "value": review_status,
                "publication_gate_passed": review_status == "human_verified",
            },
            {
                "input": "publication_status",
                "value": publication_status,
                "included_in_graph_edges": publication_status == "published",
            },
            {
                "input": "fact_version",
                "value": fact_version_present,
                "versioned_fact_available": fact_version_present,
            },
        ],
        "missing_inputs": missing_inputs,
    }


def entity_score_metrics(
    *,
    identifier_count: int,
    alias_count: int,
    relationship_count: int,
    relationship_family_count: int,
    independent_source_count: int,
    industry_membership_count: int,
    status: str,
    fact_version_present: bool,
    minimum_independent_sources: int = ENTITY_SOURCE_THRESHOLD_MIN,
    minimum_relationship_context: int = ENTITY_RELATIONSHIP_CONTEXT_MIN,
    minimum_relationship_family_context: int = ENTITY_RELATIONSHIP_FAMILY_CONTEXT_MIN,
) -> dict[str, Any]:
    minimum_independent_sources = max(minimum_independent_sources, 1)
    minimum_relationship_context = max(minimum_relationship_context, 1)
    minimum_relationship_family_context = max(minimum_relationship_family_context, 1)
    source_threshold_met = independent_source_count >= minimum_independent_sources
    source_threshold_ratio = min(
        independent_source_count / minimum_independent_sources,
        1,
    )
    identifier_ratio = min(identifier_count, 1)
    alias_ratio = min(alias_count, 1)
    relationship_ratio = min(
        relationship_count / minimum_relationship_context,
        1,
    )
    relationship_family_ratio = min(
        relationship_family_count / minimum_relationship_family_context,
        1,
    )
    industry_ratio = min(industry_membership_count, 1)
    fact_version_ratio = 1 if fact_version_present else 0
    raw_score = round(
        (identifier_ratio * 20)
        + (alias_ratio * 10)
        + (relationship_ratio * 20)
        + (relationship_family_ratio * 15)
        + (source_threshold_ratio * 15)
        + (industry_ratio * 10)
        + (fact_version_ratio * 10),
        2,
    )
    evidence_quality = round(source_threshold_ratio * 100, 2)
    status_multiplier = 1.0 if status == "active" else 0.8
    adjusted_score = round(raw_score * status_multiplier, 2)
    present_inputs = [
        identifier_count > 0,
        alias_count > 0,
        relationship_count > 0,
        relationship_family_count > 0,
        independent_source_count > 0,
        industry_membership_count > 0,
        bool(status),
        fact_version_present,
    ]
    coverage = round((sum(1 for item in present_inputs if item) / len(present_inputs)) * 100, 2)
    missing_inputs: list[str] = []
    if identifier_count <= 0:
        missing_inputs.append("entity_identifier")
    if alias_count <= 0:
        missing_inputs.append("entity_alias")
    if relationship_count <= 0:
        missing_inputs.append("relationship_context")
    if relationship_family_count < minimum_relationship_family_context:
        missing_inputs.append(
            f"relationship_family_context>={minimum_relationship_family_context}"
        )
    if not source_threshold_met:
        missing_inputs.append(
            f"entity_independent_source_threshold>={minimum_independent_sources}"
        )
    if industry_membership_count <= 0:
        missing_inputs.append("industry_membership")
    if status != "active":
        missing_inputs.append("active_entity_status")
    if not fact_version_present:
        missing_inputs.append("entity_fact_version")
    return {
        "source_threshold": {
            "minimum_independent_sources": minimum_independent_sources,
            "independent_source_count": independent_source_count,
            "met": source_threshold_met,
        },
        "raw_score": raw_score,
        "evidence_quality": evidence_quality,
        "adjusted_score": adjusted_score,
        "coverage": coverage,
        "contributions": [
            {
                "input": "entity_identifier_count",
                "value": identifier_count,
                "score_points": round(identifier_ratio * 20, 2),
            },
            {
                "input": "entity_alias_count",
                "value": alias_count,
                "score_points": round(alias_ratio * 10, 2),
            },
            {
                "input": "relationship_context_count",
                "value": relationship_count,
                "minimum_context_count": minimum_relationship_context,
                "score_points": round(relationship_ratio * 20, 2),
            },
            {
                "input": "relationship_family_count",
                "value": relationship_family_count,
                "minimum_family_count": minimum_relationship_family_context,
                "score_points": round(relationship_family_ratio * 15, 2),
            },
            {
                "input": "independent_source_count",
                "value": independent_source_count,
                "score_points": round(source_threshold_ratio * 15, 2),
            },
            {
                "input": "industry_membership_count",
                "value": industry_membership_count,
                "score_points": round(industry_ratio * 10, 2),
            },
            {
                "input": "entity_fact_version",
                "value": fact_version_present,
                "score_points": round(fact_version_ratio * 10, 2),
            },
            {
                "input": "entity_status",
                "value": status,
                "score_multiplier": status_multiplier,
            },
        ],
        "missing_inputs": missing_inputs,
    }
