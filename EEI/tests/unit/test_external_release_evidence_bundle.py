from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.validate_external_release_evidence_bundle import (
    build_operator_intake_packet,
    build_preflight,
    validate_operator_intake_packet,
    validate_preflight,
)


def write_json(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def release_decision(*, ready: bool) -> dict:
    return {
        "status": "RELEASE_DECISION_READY" if ready else "PENDING_SIGNED_DECISIONS",
        "release_gate_closed_by_contract": ready,
        "relationship_publication_allowed": ready,
        "public_brand_launch_allowed": ready,
    }


def a202_operator_review_packet() -> dict:
    return {
        "status": "PENDING_OWNER_LEGAL_CLEARANCE",
        "source_capture_artifact": (
            "artifacts/tests/a202/t1301_live_official_selected_capture_evidence.json"
        ),
        "source_capture_artifact_sha256": "capture-sha",
        "counts": {
            "anchors_ready_for_review": 3,
            "anchors_with_source_text_committed": 0,
            "relationship_candidates_ready_for_review": 2,
            "relationship_candidate_source_anchors": 4,
            "relationship_fact_candidates_allowed": 0,
            "relationships_publishable": 0,
        },
        "closure_gates": [
            {"gate_id": "live_capture_ready_for_review", "status": "present"},
            {"gate_id": "source_license_review", "status": "missing"},
            {"gate_id": "passage_level_relationship_review", "status": "missing"},
            {"gate_id": "production_owner_signoff", "status": "missing"},
            {"gate_id": "legal_release_clearance", "status": "missing"},
            {"gate_id": "a209_24h_operator_soak", "status": "missing"},
        ],
        "publication_policy": {
            "relationship_fact_publication_allowed": False,
            "relationship_edge_publication_allowed": False,
            "release_clearance": False,
        },
        "validation_summary": {
            "full_text_committed": False,
            "release_clearance": False,
            "relationship_publication": False,
        },
    }


def brand(*, ready: bool) -> dict:
    return {
        "release_gate": {
            "status": "READY" if ready else "BLOCKING",
            "public_release_allowed": ready,
        },
        "current_clearance_status": {
            "a210_status": "DONE" if ready else "IN_PROGRESS",
            "formal_legal_clearance": "CLEARED" if ready else "NOT_COMPLETE",
            "market_clearance": "CLEARED" if ready else "NOT_COMPLETE",
            "signed_risk_waiver": "NOT_REQUIRED" if ready else "NOT_PROVIDED",
            "owner_signoff": "SIGNED" if ready else "NOT_PROVIDED",
        },
    }


def gold(*, acceptance_id: str, ready: bool) -> dict:
    return {
        "focus_acceptance_id": acceptance_id,
        "fixture_policy": {"production_gold_set": ready},
        "focus_quality_result": {
            "status": "DONE" if ready else "IN_PROGRESS",
            "threshold_result": "PASS" if ready else "FAIL_CLOSED",
            "release_gate_closure_allowed": ready,
            "metrics": {
                "sample_count": 100 if acceptance_id == "A026" else 150,
                "precision": 0.98 if acceptance_id == "A026" else 0.93,
                "source_coverage_min": 1.0,
            },
        },
    }


def finalization(*, ready: bool, windows_completed: int = 113) -> dict:
    return {
        "status": "A209_FINALIZATION_READY_FOR_RELEASE_GATE_REGEN"
        if ready
        else "A209_FINALIZATION_BLOCKED_RUNNING_PARTIAL",
        "a209_evidence_ready_for_release_manager": ready,
        "downstream_release_gate_refresh_allowed": ready,
        "release_gate_closed_by_finalizer": False,
        "source_statuses": {
            "heartbeat": {
                "windows_completed": 288 if ready else windows_completed,
                "target_windows": 288,
                "windows_failed": 0,
                "progress_status": "COMPLETE_READY_FOR_EVIDENCE_VALIDATION"
                if ready
                else "RUNNING_PARTIAL",
            }
        },
    }


def paths(tmp_path: Path, *, ready: bool) -> dict[str, Path]:
    return {
        "release_decision_contract_path": write_json(
            tmp_path / "release_decision.json", release_decision(ready=ready)
        ),
        "a202_operator_review_packet_path": write_json(
            tmp_path / "a202_operator_review_packet.json", a202_operator_review_packet()
        ),
        "brand_preflight_path": write_json(tmp_path / "brand.json", brand(ready=ready)),
        "entity_gold_evaluation_path": write_json(
            tmp_path / "entity_gold.json", gold(acceptance_id="A026", ready=ready)
        ),
        "relationship_gold_evaluation_path": write_json(
            tmp_path / "relationship_gold.json", gold(acceptance_id="A027", ready=ready)
        ),
        "operator_soak_finalization_path": write_json(
            tmp_path / "finalization.json", finalization(ready=ready)
        ),
    }


def test_bundle_blocks_when_external_inputs_are_missing(tmp_path: Path) -> None:
    input_paths = paths(tmp_path, ready=False)

    payload = build_preflight(generated_at="2026-06-24T00:00:00Z", **input_paths)

    assert payload["status"] == "EXTERNAL_RELEASE_EVIDENCE_BUNDLE_BLOCKED"
    assert payload["external_release_evidence_ready"] is False
    assert payload["release_manager_preflight_refresh_allowed"] is False
    assert payload["release_gate_closed_by_bundle_preflight"] is False
    assert {row["acceptance_id"] for row in payload["missing_external_inputs"]} == {
        "A202",
        "A210",
        "A026",
        "A027",
        "A209",
    }
    assert (
        payload["gate_statuses"]["a202_operator_review"]["live_capture_ready_for_review"]
        is True
    )
    assert (
        payload["gate_statuses"]["a202_operator_review"]["relationship_fact_candidates_allowed"]
        == 0
    )
    a202_missing = next(
        row
        for row in payload["missing_external_inputs"]
        if row["input_id"] == "A202_source_license_passage_owner_legal_release"
    )
    assert "operator review packet is present for review" in a202_missing["reason"]
    validate_preflight(payload, **input_paths)


def test_bundle_allows_refresh_only_when_every_external_input_is_ready(
    tmp_path: Path,
) -> None:
    input_paths = paths(tmp_path, ready=True)

    payload = build_preflight(generated_at="2026-06-24T00:00:00Z", **input_paths)

    assert payload["status"] == "EXTERNAL_RELEASE_EVIDENCE_BUNDLE_READY"
    assert payload["external_release_evidence_ready"] is True
    assert payload["release_manager_preflight_refresh_allowed"] is True
    assert payload["mvp_release_gate_refresh_allowed"] is True
    assert payload["missing_external_inputs"] == []
    validate_preflight(payload, **input_paths)


def test_bundle_validation_detects_source_hash_drift(tmp_path: Path) -> None:
    input_paths = paths(tmp_path, ready=True)
    payload = build_preflight(generated_at="2026-06-24T00:00:00Z", **input_paths)
    write_json(input_paths["brand_preflight_path"], brand(ready=False))

    with pytest.raises(ValueError, match="external release evidence bundle drift"):
        validate_preflight(payload, **input_paths)


def test_bundle_validation_detects_a202_review_packet_drift(tmp_path: Path) -> None:
    input_paths = paths(tmp_path, ready=False)
    payload = build_preflight(generated_at="2026-06-24T00:00:00Z", **input_paths)
    changed = a202_operator_review_packet()
    changed["closure_gates"][0]["status"] = "missing"
    write_json(input_paths["a202_operator_review_packet_path"], changed)

    with pytest.raises(ValueError, match="external release evidence bundle drift"):
        validate_preflight(payload, **input_paths)


def packet_paths(tmp_path: Path, *, ready: bool) -> dict[str, Path]:
    input_paths = paths(tmp_path, ready=ready)
    preflight = build_preflight(generated_at="2026-06-24T00:00:00Z", **input_paths)
    return {
        **input_paths,
        "preflight_path": write_json(tmp_path / "preflight.json", preflight),
        "a202_intake_template_path": write_json(
            tmp_path / "a202_template.json",
            {"bundle_status": "TEMPLATE_ONLY", "template": "a202"},
        ),
        "brand_intake_template_path": write_json(
            tmp_path / "brand_template.json",
            {"bundle_status": "TEMPLATE_ONLY", "template": "brand"},
        ),
        "gold_intake_template_path": write_json(
            tmp_path / "gold_template.json",
            {"bundle_status": "TEMPLATE_ONLY", "template": "gold"},
        ),
    }


def test_operator_intake_packet_lists_required_blocked_inputs(tmp_path: Path) -> None:
    input_paths = packet_paths(tmp_path, ready=False)

    payload = build_operator_intake_packet(
        generated_at="2026-06-24T00:00:00Z",
        preflight_path=input_paths["preflight_path"],
        a202_intake_template_path=input_paths["a202_intake_template_path"],
        a202_operator_review_packet_path=input_paths["a202_operator_review_packet_path"],
        brand_intake_template_path=input_paths["brand_intake_template_path"],
        gold_intake_template_path=input_paths["gold_intake_template_path"],
        operator_soak_finalization_path=input_paths["operator_soak_finalization_path"],
    )

    assert payload["task_id"] == "T1303"
    assert payload["packet_status"] == "WAITING_FOR_OPERATOR_INPUTS"
    assert payload["release_gate_closed_by_operator_packet"] is False
    assert payload["missing_input_ids"] == [
        "A202_source_license_passage_owner_legal_release",
        "A210_brand_legal_market_clearance_or_risk_waiver",
        "A026_entity_resolution_production_gold_set",
        "A027_relationship_extraction_production_gold_set",
        "A209_24h_operator_soak_finalization",
    ]
    assert all(
        item["template_or_partial_evidence_counts_as_clearance"] is False
        for item in payload["required_operator_inputs"]
    )
    a202_item = payload["required_operator_inputs"][0]
    assert a202_item["input_id"] == "A202_source_license_passage_owner_legal_release"
    assert a202_item["supporting_sources"] == [
        payload["source_files"]["a202_operator_review_packet"]
    ]
    validate_operator_intake_packet(
        payload,
        preflight_path=input_paths["preflight_path"],
        a202_intake_template_path=input_paths["a202_intake_template_path"],
        a202_operator_review_packet_path=input_paths["a202_operator_review_packet_path"],
        brand_intake_template_path=input_paths["brand_intake_template_path"],
        gold_intake_template_path=input_paths["gold_intake_template_path"],
        operator_soak_finalization_path=input_paths["operator_soak_finalization_path"],
    )


def test_operator_intake_packet_allows_preflight_only_after_all_inputs_ready(
    tmp_path: Path,
) -> None:
    input_paths = packet_paths(tmp_path, ready=True)

    payload = build_operator_intake_packet(
        generated_at="2026-06-24T00:00:00Z",
        preflight_path=input_paths["preflight_path"],
        a202_intake_template_path=input_paths["a202_intake_template_path"],
        a202_operator_review_packet_path=input_paths["a202_operator_review_packet_path"],
        brand_intake_template_path=input_paths["brand_intake_template_path"],
        gold_intake_template_path=input_paths["gold_intake_template_path"],
        operator_soak_finalization_path=input_paths["operator_soak_finalization_path"],
    )

    assert payload["packet_status"] == "READY_FOR_RELEASE_MANAGER_PREFLIGHT"
    assert payload["missing_input_ids"] == []
    assert payload["ready_input_ids"] == payload["operator_submission_order"]
    validate_operator_intake_packet(
        payload,
        preflight_path=input_paths["preflight_path"],
        a202_intake_template_path=input_paths["a202_intake_template_path"],
        a202_operator_review_packet_path=input_paths["a202_operator_review_packet_path"],
        brand_intake_template_path=input_paths["brand_intake_template_path"],
        gold_intake_template_path=input_paths["gold_intake_template_path"],
        operator_soak_finalization_path=input_paths["operator_soak_finalization_path"],
    )


def test_operator_intake_packet_validation_detects_template_hash_drift(
    tmp_path: Path,
) -> None:
    input_paths = packet_paths(tmp_path, ready=False)
    payload = build_operator_intake_packet(
        generated_at="2026-06-24T00:00:00Z",
        preflight_path=input_paths["preflight_path"],
        a202_intake_template_path=input_paths["a202_intake_template_path"],
        a202_operator_review_packet_path=input_paths["a202_operator_review_packet_path"],
        brand_intake_template_path=input_paths["brand_intake_template_path"],
        gold_intake_template_path=input_paths["gold_intake_template_path"],
        operator_soak_finalization_path=input_paths["operator_soak_finalization_path"],
    )
    write_json(
        input_paths["gold_intake_template_path"],
        {"bundle_status": "TEMPLATE_ONLY", "template": "changed"},
    )

    with pytest.raises(ValueError, match="external release operator intake packet drift"):
        validate_operator_intake_packet(
            payload,
            preflight_path=input_paths["preflight_path"],
            a202_intake_template_path=input_paths["a202_intake_template_path"],
            a202_operator_review_packet_path=input_paths["a202_operator_review_packet_path"],
            brand_intake_template_path=input_paths["brand_intake_template_path"],
            gold_intake_template_path=input_paths["gold_intake_template_path"],
            operator_soak_finalization_path=input_paths["operator_soak_finalization_path"],
        )
