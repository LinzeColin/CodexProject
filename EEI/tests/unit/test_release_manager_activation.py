from __future__ import annotations

import copy
import json
from pathlib import Path

from scripts import validate_release_manager_activation as preflight


def test_release_manager_preflight_is_fail_closed_for_repository_state() -> None:
    payload = preflight.build_preflight(generated_at="2026-06-23T00:00:00Z")

    preflight.validate_preflight(payload)

    assert payload["status"] == "RELEASE_MANAGER_ACTIVATION_BLOCKED"
    assert payload["activation_ready"] is False
    assert payload["release_manager_activation_allowed"] is False
    assert payload["relationship_publication_allowed"] is False
    assert payload["public_brand_launch_allowed"] is False
    gate_ids = {gate["gate_id"] for gate in payload["missing_gates"]}
    assert "A209_24h_operator_soak" in gate_ids
    assert "A210_brand_clearance_or_risk_waiver" in gate_ids
    assert "A026_entity_resolution_production_gold_set" in gate_ids
    assert "A027_relationship_extraction_production_gold_set" in gate_ids
    assert "A202_source_license_reviews" in gate_ids
    assert (
        payload["gate_statuses"]["release_decision"][
            "signed_contract_test_counts_as_clearance"
        ]
        is False
    )
    assert payload["gate_statuses"]["operator_soak"]["operator_4h"] == "PASS"
    assert (
        payload["gate_statuses"]["operator_soak"]["status"]
        == "EVIDENCE_READY_FOR_RELEASE_MANAGER_REVIEW"
    )
    assert payload["gate_statuses"]["operator_soak"]["operator_24h"] == "PASS"
    heartbeat = payload["gate_statuses"]["operator_soak_background_heartbeat"]
    assert heartbeat["status"] == "BACKGROUND_SOAK_OPERATOR_INTERVENTION_REQUIRED"
    assert heartbeat["counts_as_release_ready"] is False
    assert heartbeat["release_gate_closed_by_background_heartbeat"] is False
    assert isinstance(heartbeat["windows_completed"], int)
    assert "operator_soak_heartbeat" in payload["source_files"]
    assert "background heartbeat reports" in next(
        gate["reason"]
        for gate in payload["missing_gates"]
        if gate["gate_id"] == "A209_24h_operator_soak"
    )
    assert "288/288 windows, 0 failed" in next(
        gate["reason"]
        for gate in payload["missing_gates"]
        if gate["gate_id"] == "A209_24h_operator_soak"
    )


def write_json(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_release_manager_preflight_can_be_ready_only_with_all_real_gates(
    tmp_path: Path,
) -> None:
    decision_contract = copy.deepcopy(
        preflight.read_json(preflight.DEFAULT_RELEASE_DECISION_CONTRACT)
    )
    decision_contract["validation_policy"][
        "signed_contract_test_counts_as_clearance"
    ] = True
    decision_contract["release_gate_closed_by_contract"] = True
    signed_bundle = copy.deepcopy(preflight.read_json(preflight.DEFAULT_SIGNED_DECISION_BUNDLE))

    soak = copy.deepcopy(preflight.read_json(preflight.DEFAULT_OPERATOR_SOAK_EVIDENCE))
    soak["status"] = "RELEASE_READY"
    soak["release_gate_closed_by_validator"] = True
    for row in soak["results"]:
        if row["label"] == "operator_24h":
            row["status"] = "PASS"
            row.pop("missing", None)
            row["completed_duration_seconds"] = 86400
            row["windows_completed"] = 288
            row["checkpoint_windows"] = 288

    entity_gold = copy.deepcopy(preflight.read_json(preflight.DEFAULT_ENTITY_GOLD_EVALUATION))
    entity_gold["fixture_policy"]["production_gold_set"] = True
    entity_gold["focus_quality_result"]["status"] = "DONE"
    entity_gold["focus_quality_result"]["threshold_result"] = "PASS"
    entity_gold["focus_quality_result"]["release_gate_closure_allowed"] = True

    relationship_gold = copy.deepcopy(
        preflight.read_json(preflight.DEFAULT_RELATIONSHIP_GOLD_EVALUATION)
    )
    relationship_gold["fixture_policy"]["production_gold_set"] = True
    relationship_gold["focus_quality_result"]["status"] = "DONE"
    relationship_gold["focus_quality_result"]["threshold_result"] = "PASS"
    relationship_gold["focus_quality_result"]["release_gate_closure_allowed"] = True

    brand = copy.deepcopy(preflight.read_json(preflight.DEFAULT_BRAND_PREFLIGHT))
    brand["release_gate"]["status"] = "CLEARED"
    brand["release_gate"]["public_release_allowed"] = True
    brand["current_clearance_status"].update(
        {
            "formal_legal_clearance": "COMPLETE",
            "market_clearance": "COMPLETE",
            "signed_risk_waiver": "PROVIDED",
            "owner_signoff": "PROVIDED",
            "a210_status": "DONE",
        }
    )
    heartbeat = copy.deepcopy(preflight.read_json(preflight.DEFAULT_OPERATOR_SOAK_HEARTBEAT))
    heartbeat["status"] = "BACKGROUND_SOAK_COMPLETE_READY_FOR_EVIDENCE_VALIDATION"
    heartbeat["progress_status"] = "COMPLETE_READY_FOR_EVIDENCE_VALIDATION"
    heartbeat["release_gate_closed_by_background_heartbeat"] = False
    heartbeat["progress"]["windows_completed"] = 288
    heartbeat["progress"]["windows_failed"] = 0
    heartbeat["progress"]["windows_remaining"] = 0
    heartbeat["progress"]["completion_percent"] = 100.0
    heartbeat["progress"]["latest_successful_window"]["index"] = 288

    payload = preflight.build_preflight(
        release_decision_contract_path=write_json(tmp_path / "decision.json", decision_contract),
        signed_decision_bundle_path=write_json(tmp_path / "signed.json", signed_bundle),
        operator_soak_evidence_path=write_json(tmp_path / "soak.json", soak),
        operator_soak_heartbeat_path=write_json(tmp_path / "heartbeat.json", heartbeat),
        entity_gold_evaluation_path=write_json(tmp_path / "entity-gold.json", entity_gold),
        relationship_gold_evaluation_path=write_json(
            tmp_path / "relationship-gold.json",
            relationship_gold,
        ),
        brand_preflight_path=write_json(tmp_path / "brand.json", brand),
        generated_at="2026-06-23T00:00:00Z",
    )

    assert payload["status"] == "RELEASE_MANAGER_ACTIVATION_READY"
    assert payload["activation_ready"] is True
    assert payload["missing_gates"] == []
    preflight.validate_preflight(
        payload,
        release_decision_contract_path=tmp_path / "decision.json",
        signed_decision_bundle_path=tmp_path / "signed.json",
        operator_soak_evidence_path=tmp_path / "soak.json",
        operator_soak_heartbeat_path=tmp_path / "heartbeat.json",
        entity_gold_evaluation_path=tmp_path / "entity-gold.json",
        relationship_gold_evaluation_path=tmp_path / "relationship-gold.json",
        brand_preflight_path=tmp_path / "brand.json",
    )
