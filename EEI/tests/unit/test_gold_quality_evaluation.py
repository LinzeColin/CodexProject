from __future__ import annotations

import copy

import pytest

from scripts import validate_gold_quality_evaluation as gold


def test_repository_gold_fixture_is_fail_closed_for_small_samples() -> None:
    contract = gold.build_contract(gold.DEFAULT_LABELS, generated_at="2026-06-22T00:00:00Z")

    assert contract["status"] == "GOLD_EVALUATION_FAIL_CLOSED"
    assert contract["release_gate_closure_allowed"] is False
    assert contract["quality_results"]["A026"]["status"] == "IN_PROGRESS"
    assert contract["quality_results"]["A027"]["status"] == "IN_PROGRESS"
    assert (
        "sample_count 6 < required 50"
        in contract["quality_results"]["A026"]["closure_blockers"]
    )
    assert (
        "sample_count 6 < required 100"
        in contract["quality_results"]["A027"]["closure_blockers"]
    )
    assert (
        "repository fixture is not production_gold_set"
        in contract["quality_results"]["A026"]["closure_blockers"]
    )
    assert contract["quality_results"]["A026"]["metrics"]["precision"] == 0.8
    assert contract["quality_results"]["A027"]["metrics"]["precision"] == 0.75


def test_contract_validator_rejects_closure_without_blocker_consistency() -> None:
    contract = gold.build_contract(gold.DEFAULT_LABELS, generated_at="2026-06-22T00:00:00Z")
    payload = gold.focus_payload(contract, "A026")
    payload["quality_results"]["A026"]["release_gate_closure_allowed"] = True

    with pytest.raises(ValueError, match="cannot allow closure while blockers exist"):
        gold.validate_contract(payload, focus_acceptance_id="A026")


def test_complete_production_gold_set_can_pass_threshold_math() -> None:
    labels = gold.read_json(gold.DEFAULT_LABELS)
    labels = copy.deepcopy(labels)
    labels["fixture_policy"]["production_gold_set"] = True
    labels["entity_resolution_cases"] = [
        {
            **copy.deepcopy(labels["entity_resolution_cases"][0]),
            "case_id": f"ENT-PROD-{index:03d}",
        }
        for index in range(50)
    ]
    labels["relationship_cases"] = [
        {
            **copy.deepcopy(labels["relationship_cases"][0]),
            "case_id": f"REL-PROD-{index:03d}",
        }
        for index in range(100)
    ]

    entity = gold.entity_stats(labels["entity_resolution_cases"])
    relationship = gold.relationship_stats(labels["relationship_cases"])
    a026 = gold.acceptance_payload(
        acceptance_id="A026",
        stats=entity,
        min_cases=gold.ENTITY_MIN_CASES,
        min_precision=gold.ENTITY_MIN_PRECISION,
        production_gold_set=True,
    )
    a027 = gold.acceptance_payload(
        acceptance_id="A027",
        stats=relationship,
        min_cases=gold.RELATIONSHIP_MIN_CASES,
        min_precision=gold.RELATIONSHIP_MIN_PRECISION,
        production_gold_set=True,
    )

    assert a026["release_gate_closure_allowed"] is True
    assert a027["release_gate_closure_allowed"] is True
    assert a026["metrics"]["precision"] == 1.0
    assert a027["metrics"]["precision"] == 1.0


def test_missing_counter_evidence_review_is_rejected() -> None:
    labels = gold.read_json(gold.DEFAULT_LABELS)
    labels = copy.deepcopy(labels)
    labels["entity_resolution_cases"][0]["source_coverage"]["counter_evidence_reviewed"] = False

    with pytest.raises(ValueError, match="counter_evidence_reviewed must be true"):
        gold.validate_label_payload(labels)
