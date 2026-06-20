from __future__ import annotations

from typing import Any

CANDIDATE_SOURCE_THRESHOLD_MIN = 2
ENTITY_SOURCE_THRESHOLD_MIN = 1
ENTITY_RELATIONSHIP_CONTEXT_MIN = 3
ENTITY_RELATIONSHIP_FAMILY_CONTEXT_MIN = 3
EVENT_SOURCE_THRESHOLD_MIN = 1
EVENT_PARTICIPANT_CONTEXT_MIN = 1
INDUSTRY_SOURCE_THRESHOLD_MIN = 1
INDUSTRY_ENTITY_CONTEXT_MIN = 3
INDUSTRY_RELATIONSHIP_CONTEXT_MIN = 3
INDUSTRY_RELATIONSHIP_FAMILY_CONTEXT_MIN = 3


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


def event_score_metrics(
    *,
    participant_count: int,
    independent_source_count: int,
    status: str,
    timing_context_present: bool,
    amount_semantics_present: bool,
    fact_version_present: bool,
    evidence_present: bool,
    minimum_independent_sources: int = EVENT_SOURCE_THRESHOLD_MIN,
    minimum_participant_context: int = EVENT_PARTICIPANT_CONTEXT_MIN,
) -> dict[str, Any]:
    minimum_independent_sources = max(minimum_independent_sources, 1)
    minimum_participant_context = max(minimum_participant_context, 1)
    source_threshold_met = independent_source_count >= minimum_independent_sources
    source_threshold_ratio = min(
        independent_source_count / minimum_independent_sources,
        1,
    )
    participant_ratio = min(participant_count / minimum_participant_context, 1)
    timing_ratio = 1 if timing_context_present else 0
    amount_ratio = 1 if amount_semantics_present else 0
    active_status = status not in {"superseded", "revoked"}
    status_ratio = 1 if active_status else 0
    evidence_ratio = 1 if evidence_present else 0
    fact_version_ratio = 1 if fact_version_present else 0
    raw_score = round(
        (participant_ratio * 20)
        + (source_threshold_ratio * 20)
        + (timing_ratio * 15)
        + (amount_ratio * 10)
        + (status_ratio * 10)
        + (evidence_ratio * 15)
        + (fact_version_ratio * 10),
        2,
    )
    evidence_quality = round(
        ((source_threshold_ratio * 0.7) + (evidence_ratio * 0.3)) * 100,
        2,
    )
    status_multiplier = 1.0 if active_status else 0.6
    adjusted_score = round(raw_score * status_multiplier, 2)
    present_inputs = [
        participant_count >= minimum_participant_context,
        independent_source_count > 0,
        bool(status),
        timing_context_present,
        amount_semantics_present,
        fact_version_present,
        evidence_present,
    ]
    coverage = round((sum(1 for item in present_inputs if item) / len(present_inputs)) * 100, 2)
    missing_inputs: list[str] = []
    if participant_count < minimum_participant_context:
        missing_inputs.append(f"event_participant_context>={minimum_participant_context}")
    if not source_threshold_met:
        missing_inputs.append(
            f"event_independent_source_threshold>={minimum_independent_sources}"
        )
    if not timing_context_present:
        missing_inputs.append("event_timing_context")
    if not amount_semantics_present:
        missing_inputs.append("event_amount_semantics")
    if not active_status:
        missing_inputs.append("active_event_status")
    if not evidence_present:
        missing_inputs.append("event_evidence_chain")
    if not fact_version_present:
        missing_inputs.append("event_fact_version")
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
                "input": "event_participant_count",
                "value": participant_count,
                "minimum_context_count": minimum_participant_context,
                "score_points": round(participant_ratio * 20, 2),
            },
            {
                "input": "independent_source_count",
                "value": independent_source_count,
                "score_points": round(source_threshold_ratio * 20, 2),
            },
            {
                "input": "event_timing_context",
                "value": timing_context_present,
                "score_points": round(timing_ratio * 15, 2),
            },
            {
                "input": "event_amount_semantics",
                "value": amount_semantics_present,
                "score_points": round(amount_ratio * 10, 2),
            },
            {
                "input": "event_status",
                "value": status,
                "score_points": round(status_ratio * 10, 2),
            },
            {
                "input": "event_evidence_chain",
                "value": evidence_present,
                "score_points": round(evidence_ratio * 15, 2),
            },
            {
                "input": "event_fact_version",
                "value": fact_version_present,
                "score_points": round(fact_version_ratio * 10, 2),
            },
        ],
        "missing_inputs": missing_inputs,
    }


def industry_score_metrics(
    *,
    entity_count: int,
    relationship_count: int,
    relationship_family_count: int,
    independent_source_count: int,
    taxonomy_context_present: bool,
    active: bool,
    fact_version_present: bool,
    minimum_independent_sources: int = INDUSTRY_SOURCE_THRESHOLD_MIN,
    minimum_entity_context: int = INDUSTRY_ENTITY_CONTEXT_MIN,
    minimum_relationship_context: int = INDUSTRY_RELATIONSHIP_CONTEXT_MIN,
    minimum_relationship_family_context: int = INDUSTRY_RELATIONSHIP_FAMILY_CONTEXT_MIN,
) -> dict[str, Any]:
    minimum_independent_sources = max(minimum_independent_sources, 1)
    minimum_entity_context = max(minimum_entity_context, 1)
    minimum_relationship_context = max(minimum_relationship_context, 1)
    minimum_relationship_family_context = max(minimum_relationship_family_context, 1)
    source_threshold_met = independent_source_count >= minimum_independent_sources
    source_threshold_ratio = min(independent_source_count / minimum_independent_sources, 1)
    entity_ratio = min(entity_count / minimum_entity_context, 1)
    relationship_ratio = min(relationship_count / minimum_relationship_context, 1)
    relationship_family_ratio = min(
        relationship_family_count / minimum_relationship_family_context,
        1,
    )
    taxonomy_ratio = 1 if taxonomy_context_present else 0
    active_ratio = 1 if active else 0
    fact_version_ratio = 1 if fact_version_present else 0
    raw_score = round(
        (entity_ratio * 20)
        + (relationship_ratio * 20)
        + (relationship_family_ratio * 15)
        + (source_threshold_ratio * 15)
        + (taxonomy_ratio * 10)
        + (active_ratio * 10)
        + (fact_version_ratio * 10),
        2,
    )
    evidence_quality = round(source_threshold_ratio * 100, 2)
    adjusted_score = round(raw_score * (1.0 if active else 0.8), 2)
    present_inputs = [
        entity_count >= minimum_entity_context,
        relationship_count >= minimum_relationship_context,
        relationship_family_count >= minimum_relationship_family_context,
        independent_source_count > 0,
        taxonomy_context_present,
        active,
        fact_version_present,
    ]
    coverage = round((sum(1 for item in present_inputs if item) / len(present_inputs)) * 100, 2)
    missing_inputs: list[str] = []
    if entity_count < minimum_entity_context:
        missing_inputs.append(f"industry_entity_context>={minimum_entity_context}")
    if relationship_count < minimum_relationship_context:
        missing_inputs.append(
            f"industry_relationship_context>={minimum_relationship_context}"
        )
    if relationship_family_count < minimum_relationship_family_context:
        missing_inputs.append(
            f"industry_relationship_family_context>={minimum_relationship_family_context}"
        )
    if not source_threshold_met:
        missing_inputs.append(
            f"industry_independent_source_threshold>={minimum_independent_sources}"
        )
    if not taxonomy_context_present:
        missing_inputs.append("industry_taxonomy_hierarchy")
    if not active:
        missing_inputs.append("active_industry_status")
    if not fact_version_present:
        missing_inputs.append("industry_fact_version")
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
                "input": "industry_entity_count",
                "value": entity_count,
                "minimum_context_count": minimum_entity_context,
                "score_points": round(entity_ratio * 20, 2),
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
                "input": "industry_taxonomy_hierarchy",
                "value": taxonomy_context_present,
                "score_points": round(taxonomy_ratio * 10, 2),
            },
            {
                "input": "industry_active",
                "value": active,
                "score_points": round(active_ratio * 10, 2),
            },
            {
                "input": "industry_fact_version",
                "value": fact_version_present,
                "score_points": round(fact_version_ratio * 10, 2),
            },
        ],
        "missing_inputs": missing_inputs,
    }
