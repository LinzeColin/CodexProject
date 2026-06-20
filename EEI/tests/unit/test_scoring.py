from apps.api.app.scoring import (
    candidate_score_metrics,
    entity_score_metrics,
    event_score_metrics,
    industry_score_metrics,
    relationship_score_metrics,
)


def test_candidate_score_metrics_penalize_missing_publication_inputs() -> None:
    metrics = candidate_score_metrics(
        confidence=0.88,
        independent_source_count=1,
        source_threshold_met=False,
        review_status="machine_verified",
        publication_status="ready_for_review",
        parser_version_present=True,
        evidence_present=True,
    )

    assert metrics["raw_score"] == 88
    assert metrics["evidence_quality"] == 50
    assert metrics["adjusted_score"] == 44
    assert metrics["coverage"] == 100
    assert metrics["source_threshold"]["minimum_independent_sources"] == 2
    assert metrics["missing_inputs"] == [
        "independent_source_threshold>=2",
        "human_review_verification",
        "published_relationship_version",
    ]


def test_candidate_score_metrics_full_quality_when_publication_gates_pass() -> None:
    metrics = candidate_score_metrics(
        confidence=0.72,
        independent_source_count=3,
        source_threshold_met=True,
        review_status="human_verified",
        publication_status="published",
        parser_version_present=True,
        evidence_present=True,
    )

    assert metrics["raw_score"] == 72
    assert metrics["evidence_quality"] == 100
    assert metrics["adjusted_score"] == 72
    assert metrics["missing_inputs"] == []


def test_relationship_score_metrics_require_versioned_published_evidence() -> None:
    metrics = relationship_score_metrics(
        confidence=0.91,
        independent_source_count=1,
        source_threshold_met=True,
        review_status="human_verified",
        publication_status="published",
        fact_version_present=True,
        evidence_present=True,
        minimum_independent_sources=2,
    )

    assert metrics["raw_score"] == 91
    assert metrics["evidence_quality"] == 50
    assert metrics["adjusted_score"] == 45.5
    assert metrics["source_threshold"] == {
        "minimum_independent_sources": 2,
        "independent_source_count": 1,
        "met": True,
    }
    assert metrics["missing_inputs"] == []


def test_relationship_score_metrics_penalize_unversioned_unreviewed_edges() -> None:
    metrics = relationship_score_metrics(
        confidence=0.55,
        independent_source_count=0,
        source_threshold_met=False,
        review_status="unreviewed",
        publication_status="reported",
        fact_version_present=False,
        evidence_present=False,
        minimum_independent_sources=2,
    )

    assert metrics["raw_score"] == 55
    assert metrics["evidence_quality"] == 0
    assert metrics["adjusted_score"] == 0
    assert metrics["missing_inputs"] == [
        "independent_source_threshold>=2",
        "human_review_verification",
        "published_relationship_version",
        "relationship_fact_version",
        "evidence_chain",
    ]


def test_entity_score_metrics_full_quality_when_context_is_versioned() -> None:
    metrics = entity_score_metrics(
        identifier_count=1,
        alias_count=2,
        relationship_count=6,
        relationship_family_count=4,
        independent_source_count=3,
        industry_membership_count=1,
        status="active",
        fact_version_present=True,
    )

    assert metrics["raw_score"] == 100
    assert metrics["evidence_quality"] == 100
    assert metrics["adjusted_score"] == 100
    assert metrics["coverage"] == 100
    assert metrics["source_threshold"] == {
        "minimum_independent_sources": 1,
        "independent_source_count": 3,
        "met": True,
    }
    assert metrics["missing_inputs"] == []


def test_entity_score_metrics_surfaces_missing_entity_context() -> None:
    metrics = entity_score_metrics(
        identifier_count=0,
        alias_count=0,
        relationship_count=1,
        relationship_family_count=1,
        independent_source_count=0,
        industry_membership_count=0,
        status="inactive",
        fact_version_present=False,
    )

    assert metrics["raw_score"] == 11.67
    assert metrics["evidence_quality"] == 0
    assert metrics["adjusted_score"] == 9.34
    assert metrics["coverage"] == 37.5
    assert metrics["missing_inputs"] == [
        "entity_identifier",
        "entity_alias",
        "relationship_family_context>=3",
        "entity_independent_source_threshold>=1",
        "industry_membership",
        "active_entity_status",
        "entity_fact_version",
    ]


def test_event_score_metrics_full_quality_when_context_is_versioned() -> None:
    metrics = event_score_metrics(
        participant_count=2,
        independent_source_count=1,
        status="reported",
        timing_context_present=True,
        amount_semantics_present=True,
        fact_version_present=True,
        evidence_present=True,
    )

    assert metrics["raw_score"] == 100
    assert metrics["evidence_quality"] == 100
    assert metrics["adjusted_score"] == 100
    assert metrics["coverage"] == 100
    assert metrics["source_threshold"] == {
        "minimum_independent_sources": 1,
        "independent_source_count": 1,
        "met": True,
    }
    assert metrics["missing_inputs"] == []


def test_event_score_metrics_surfaces_missing_event_context() -> None:
    metrics = event_score_metrics(
        participant_count=0,
        independent_source_count=0,
        status="revoked",
        timing_context_present=False,
        amount_semantics_present=False,
        fact_version_present=False,
        evidence_present=False,
    )

    assert metrics["raw_score"] == 0
    assert metrics["evidence_quality"] == 0
    assert metrics["adjusted_score"] == 0
    assert metrics["coverage"] == 14.29
    assert metrics["missing_inputs"] == [
        "event_participant_context>=1",
        "event_independent_source_threshold>=1",
        "event_timing_context",
        "event_amount_semantics",
        "active_event_status",
        "event_evidence_chain",
        "event_fact_version",
    ]


def test_industry_score_metrics_full_quality_when_context_is_versioned() -> None:
    metrics = industry_score_metrics(
        entity_count=3,
        relationship_count=3,
        relationship_family_count=3,
        independent_source_count=2,
        taxonomy_context_present=True,
        active=True,
        fact_version_present=True,
    )

    assert metrics["raw_score"] == 100
    assert metrics["evidence_quality"] == 100
    assert metrics["adjusted_score"] == 100
    assert metrics["coverage"] == 100
    assert metrics["source_threshold"] == {
        "minimum_independent_sources": 1,
        "independent_source_count": 2,
        "met": True,
    }
    assert metrics["missing_inputs"] == []


def test_industry_score_metrics_surfaces_missing_industry_context() -> None:
    metrics = industry_score_metrics(
        entity_count=1,
        relationship_count=0,
        relationship_family_count=0,
        independent_source_count=0,
        taxonomy_context_present=False,
        active=False,
        fact_version_present=False,
    )

    assert metrics["raw_score"] == 6.67
    assert metrics["evidence_quality"] == 0
    assert metrics["adjusted_score"] == 5.34
    assert metrics["coverage"] == 0
    assert metrics["missing_inputs"] == [
        "industry_entity_context>=3",
        "industry_relationship_context>=3",
        "industry_relationship_family_context>=3",
        "industry_independent_source_threshold>=1",
        "industry_taxonomy_hierarchy",
        "active_industry_status",
        "industry_fact_version",
    ]
