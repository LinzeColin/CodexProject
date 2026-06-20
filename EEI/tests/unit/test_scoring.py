from apps.api.app.scoring import candidate_score_metrics


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
