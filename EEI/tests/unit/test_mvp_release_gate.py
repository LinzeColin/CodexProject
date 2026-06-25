from __future__ import annotations

import copy
import json
from pathlib import Path

from scripts import validate_mvp_release_gate as release_gate


def write_json(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_mvp_release_gate_is_fail_closed_for_repository_state() -> None:
    payload = release_gate.build_preflight(generated_at="2026-06-24T00:00:00Z")

    release_gate.validate_preflight(payload)

    assert payload["schema_version"] == "eei-t1303-mvp-release-gate-preflight-v1"
    assert payload["status"] == "MVP_RELEASE_BLOCKED"
    assert payload["release_ready"] is False
    assert payload["production_publication_allowed"] is False
    assert payload["score_publication_allowed"] is False
    assert payload["public_brand_launch_allowed"] is False
    assert payload["gate_statuses"]["production_api"]["api_surface_ready"] is True
    assert (
        payload["gate_statuses"]["operator_soak_background_heartbeat"][
            "counts_as_release_ready"
        ]
        is False
    )
    gate_ids = {row["gate_id"] for row in payload["missing_gates"]}
    assert gate_ids == set(release_gate.REQUIRED_GATE_IDS)
    assert payload["validation_policy"]["repository_fixtures_count_as_clearance"] is False
    assert payload["validation_policy"]["templates_count_as_clearance"] is False


def test_mvp_release_gate_can_be_ready_only_when_all_gates_are_ready(
    tmp_path: Path,
) -> None:
    release_decision = copy.deepcopy(
        release_gate.read_json(release_gate.DEFAULT_RELEASE_DECISION_CONTRACT)
    )
    release_decision.update(
        {
            "status": "RELEASE_DECISION_READY",
            "release_gate_closed_by_contract": True,
            "relationship_publication_allowed": True,
            "public_brand_launch_allowed": True,
        }
    )

    production_api = copy.deepcopy(
        release_gate.read_json(release_gate.DEFAULT_PRODUCTION_API_PREFLIGHT)
    )
    production_api.update(
        {
            "status": "A203_PRODUCTION_API_RELEASE_READY",
            "release_ready": True,
            "production_graph_publication_allowed": True,
            "score_publication_allowed": True,
            "missing_gates": [],
        }
    )

    release_manager = copy.deepcopy(
        release_gate.read_json(release_gate.DEFAULT_RELEASE_MANAGER_PREFLIGHT)
    )
    release_manager.update(
        {
            "status": "RELEASE_MANAGER_ACTIVATION_READY",
            "activation_ready": True,
            "release_manager_activation_allowed": True,
            "relationship_publication_allowed": True,
            "public_brand_launch_allowed": True,
            "missing_gates": [],
        }
    )

    soak = copy.deepcopy(release_gate.read_json(release_gate.DEFAULT_OPERATOR_SOAK_EVIDENCE))
    soak["status"] = "RELEASE_READY"
    soak["release_gate_closed_by_validator"] = True
    for row in soak["results"]:
        if row["label"] == "operator_24h":
            row["status"] = "PASS"
            row.pop("missing", None)
            row["completed_duration_seconds"] = 86400
            row["windows_completed"] = 288
            row["checkpoint_windows"] = 288

    heartbeat = copy.deepcopy(
        release_gate.read_json(release_gate.DEFAULT_OPERATOR_SOAK_HEARTBEAT)
    )
    heartbeat["progress"]["windows_completed"] = 288
    heartbeat["progress"]["windows_failed"] = 0
    heartbeat["progress"]["windows_remaining"] = 0
    heartbeat["progress"]["completion_percent"] = 100.0

    brand = copy.deepcopy(release_gate.read_json(release_gate.DEFAULT_BRAND_PREFLIGHT))
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

    entity_gold = copy.deepcopy(
        release_gate.read_json(release_gate.DEFAULT_ENTITY_GOLD_EVALUATION)
    )
    entity_gold["fixture_policy"]["production_gold_set"] = True
    entity_gold["focus_quality_result"]["status"] = "DONE"
    entity_gold["focus_quality_result"]["threshold_result"] = "PASS"
    entity_gold["focus_quality_result"]["release_gate_closure_allowed"] = True

    relationship_gold = copy.deepcopy(
        release_gate.read_json(release_gate.DEFAULT_RELATIONSHIP_GOLD_EVALUATION)
    )
    relationship_gold["fixture_policy"]["production_gold_set"] = True
    relationship_gold["focus_quality_result"]["status"] = "DONE"
    relationship_gold["focus_quality_result"]["threshold_result"] = "PASS"
    relationship_gold["focus_quality_result"]["release_gate_closure_allowed"] = True

    payload = release_gate.build_preflight(
        release_decision_contract_path=write_json(
            tmp_path / "release-decision.json",
            release_decision,
        ),
        production_api_preflight_path=write_json(
            tmp_path / "production-api.json",
            production_api,
        ),
        release_manager_preflight_path=write_json(
            tmp_path / "release-manager.json",
            release_manager,
        ),
        operator_soak_evidence_path=write_json(tmp_path / "soak.json", soak),
        operator_soak_heartbeat_path=write_json(tmp_path / "heartbeat.json", heartbeat),
        brand_preflight_path=write_json(tmp_path / "brand.json", brand),
        entity_gold_evaluation_path=write_json(tmp_path / "entity-gold.json", entity_gold),
        relationship_gold_evaluation_path=write_json(
            tmp_path / "relationship-gold.json",
            relationship_gold,
        ),
        generated_at="2026-06-24T00:00:00Z",
    )

    assert payload["status"] == "MVP_RELEASE_READY"
    assert payload["release_ready"] is True
    assert payload["missing_gates"] == []
    assert payload["production_publication_allowed"] is True
    release_gate.validate_preflight(
        payload,
        release_decision_contract_path=tmp_path / "release-decision.json",
        production_api_preflight_path=tmp_path / "production-api.json",
        release_manager_preflight_path=tmp_path / "release-manager.json",
        operator_soak_evidence_path=tmp_path / "soak.json",
        operator_soak_heartbeat_path=tmp_path / "heartbeat.json",
        brand_preflight_path=tmp_path / "brand.json",
        entity_gold_evaluation_path=tmp_path / "entity-gold.json",
        relationship_gold_evaluation_path=tmp_path / "relationship-gold.json",
    )
