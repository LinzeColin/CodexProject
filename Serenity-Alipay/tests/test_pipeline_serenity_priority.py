from dataclasses import replace

from app.adapters.manual_sources import Candidate
from app.core.pipeline import _action_pool_requires_manual_review, _action_pool_rows, _ranked_recommendation_rows, _target_weights
from app.core.scoring import ScoreResult


def _candidate(asset_code: str, theme: str = "AI scarce layer") -> Candidate:
    return Candidate(
        asset_id=asset_code,
        asset_code=asset_code,
        asset_name=f"{asset_code} Fund",
        asset_type="off_platform_fund",
        market="CN",
        fund_company="Manual",
        risk_level="high",
        theme=theme,
        is_off_platform_fund=True,
        is_excluded=False,
        exclusion_reason="",
        official_source_count=2,
        fallback_aggregated=False,
        evidence_level="Strong",
        source_name="official",
        source_type="official",
        source_url="manual",
        missing_nav_days=0,
        missing_holding_days=0,
        conflict_flag=False,
        as_of="2026-06-12",
    )


def _score(total_score: float, grade: str = "Action-Ready") -> ScoreResult:
    return ScoreResult(
        total_score=total_score,
        data_score=25.0,
        timeliness_score=15.0,
        source_score=15.0,
        return_score=15.0,
        risk_score=20.0,
        executable_score=10.0,
        evidence_coverage=1.0,
        grade=grade,
        hard_block_reason=None,
        action_label="Increase",
        trigger_reason="serenity judgment supported by evidence confidence",
        manual_review_required=False,
        missing_fields=(),
    )


def _manual_review_score(total_score: float = 99.0) -> ScoreResult:
    return replace(
        _score(total_score, grade="Manual Review"),
        action_label="Manual Review",
        trigger_reason="fee/redemption/subscription status missing or closed",
        manual_review_required=True,
    )


def test_serenity_priority_ranks_before_confidence_score():
    rows = [
        {"candidate_index": 0, "candidate": _candidate("SERENITY_FIRST"), "score": _score(70.0)},
        {"candidate_index": 1, "candidate": _candidate("HIGHER_SCORE_SECOND"), "score": _score(99.0)},
        {"candidate_index": 2, "candidate": _candidate("BLOCKED"), "score": _score(100.0, grade="Block")},
    ]

    ranked = _ranked_recommendation_rows(rows)

    assert [row["candidate"].asset_code for row in ranked] == ["SERENITY_FIRST", "HIGHER_SCORE_SECOND"]


def test_manual_review_candidate_is_demoted_below_executable_serenity_candidate():
    rows = [
        {"candidate_index": 0, "candidate": _candidate("LIMITED_SUBSCRIPTION"), "score": _manual_review_score(99.0)},
        {"candidate_index": 1, "candidate": _candidate("EXECUTABLE_SERENITY"), "score": _score(70.0)},
    ]

    ranked = _ranked_recommendation_rows(rows)

    assert [row["candidate"].asset_code for row in ranked] == ["EXECUTABLE_SERENITY", "LIMITED_SUBSCRIPTION"]


def test_target_weights_use_score_as_bounded_confidence_modifier():
    rows = [
        {"candidate_index": 0, "candidate": _candidate("SERENITY_FIRST"), "score": _score(55.0)},
        {"candidate_index": 1, "candidate": _candidate("HIGHER_SCORE_SECOND"), "score": _score(100.0)},
        {"candidate_index": 2, "candidate": _candidate("THIRD"), "score": _score(90.0)},
        {"candidate_index": 3, "candidate": _candidate("FOURTH"), "score": _score(90.0)},
        {"candidate_index": 4, "candidate": _candidate("FIFTH"), "score": _score(90.0)},
    ]

    weights = _target_weights(rows)

    assert weights["SERENITY_FIRST"] > weights["HIGHER_SCORE_SECOND"]
    assert abs(sum(weights.values()) - 1.0) < 0.000001


def test_same_serenity_priority_uses_confidence_score_as_tiebreaker():
    base = {"candidate_index": 0, "candidate": _candidate("LOW_SCORE"), "score": _score(70.0)}
    higher = {
        "candidate_index": 0,
        "candidate": replace(_candidate("HIGH_SCORE"), theme="same scarce layer"),
        "score": _score(95.0),
    }

    ranked = _ranked_recommendation_rows([base, higher])

    assert [row["candidate"].asset_code for row in ranked] == ["HIGH_SCORE", "LOW_SCORE"]


def test_observation_pool_manual_review_does_not_lock_action_pool():
    recommendations = [
        {"rank": 1, "asset_code": "TOP1", "manual_review_required": False},
        {"rank": 2, "asset_code": "TOP2", "manual_review_required": False},
        {"rank": 3, "asset_code": "TOP3", "manual_review_required": False},
        {"rank": 4, "asset_code": "TOP4", "manual_review_required": False},
        {"rank": 5, "asset_code": "TOP5", "manual_review_required": False},
        {"rank": 6, "asset_code": "WATCH6", "manual_review_required": True},
        {"rank": 7, "asset_code": "WATCH7", "manual_review_required": True},
    ]

    assert [row["asset_code"] for row in _action_pool_rows(recommendations)] == [
        "TOP1",
        "TOP2",
        "TOP3",
        "TOP4",
        "TOP5",
    ]
    assert _action_pool_requires_manual_review(recommendations) is False


def test_top5_manual_review_locks_action_pool():
    recommendations = [
        {"rank": 1, "asset_code": "TOP1", "manual_review_required": False},
        {"rank": 5, "asset_code": "TOP5", "manual_review_required": True},
        {"rank": 6, "asset_code": "WATCH6", "manual_review_required": False},
    ]

    assert _action_pool_requires_manual_review(recommendations) is True
