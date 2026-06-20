from __future__ import annotations

from typing import Any

CANDIDATE_SOURCE_THRESHOLD_MIN = 2


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
