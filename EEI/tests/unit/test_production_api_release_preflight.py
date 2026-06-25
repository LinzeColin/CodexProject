from __future__ import annotations

import copy
import json
from pathlib import Path

from scripts import validate_production_api_release_preflight as preflight


def write_json(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_a203_preflight_is_fail_closed_for_repository_state() -> None:
    payload = preflight.build_preflight(generated_at="2026-06-24T00:00:00Z")

    preflight.validate_preflight(payload)

    assert payload["status"] == "A203_PRODUCTION_API_RELEASE_BLOCKED"
    assert payload["api_surface_ready"] is True
    assert payload["release_ready"] is False
    assert payload["production_graph_publication_allowed"] is False
    assert payload["score_publication_allowed"] is False
    assert (
        payload["gate_statuses"]["a203_contract"][
            "relationship_fact_candidates_in_graph_edges"
        ]
        is False
    )
    assert all(
        payload["gate_statuses"]["a203_contract"]["api_path_coverage"].values()
    )
    assert all(
        payload["gate_statuses"]["a203_contract"][
            "score_object_type_coverage"
        ].values()
    )
    assert (
        payload["gate_statuses"]["operator_soak_background_heartbeat"][
            "counts_as_release_ready"
        ]
        is False
    )
    gate_ids = {gate["gate_id"] for gate in payload["missing_gates"]}
    assert "A203_contract_status" not in gate_ids
    assert "A202_relationship_publication_clearance" in gate_ids
    assert "A204_A205_release_manager_activation" in gate_ids
    assert "A209_24h_operator_soak" in gate_ids


def test_a203_preflight_can_be_ready_only_with_all_release_gates(
    tmp_path: Path,
) -> None:
    a203 = copy.deepcopy(preflight.read_json(preflight.DEFAULT_A203_CONTRACT))
    a203["status"] = "DONE"

    release_decision = copy.deepcopy(
        preflight.read_json(preflight.DEFAULT_RELEASE_DECISION_CONTRACT)
    )
    release_decision["status"] = "RELEASE_READY"
    release_decision["release_gate_closed_by_contract"] = True
    release_decision["relationship_publication_allowed"] = True
    release_decision["public_brand_launch_allowed"] = True

    release_manager = copy.deepcopy(
        preflight.read_json(preflight.DEFAULT_RELEASE_MANAGER_PREFLIGHT)
    )
    release_manager["status"] = "RELEASE_MANAGER_ACTIVATION_READY"
    release_manager["activation_ready"] = True
    release_manager["release_manager_activation_allowed"] = True
    release_manager["relationship_publication_allowed"] = True
    release_manager["missing_gates"] = []

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

    heartbeat = copy.deepcopy(
        preflight.read_json(preflight.DEFAULT_OPERATOR_SOAK_HEARTBEAT)
    )
    heartbeat["status"] = "BACKGROUND_SOAK_COMPLETE_READY_FOR_EVIDENCE_VALIDATION"
    heartbeat["progress_status"] = "COMPLETE_READY_FOR_EVIDENCE_VALIDATION"
    heartbeat["progress"]["windows_completed"] = 288
    heartbeat["progress"]["windows_failed"] = 0
    heartbeat["progress"]["windows_remaining"] = 0
    heartbeat["progress"]["completion_percent"] = 100.0

    payload = preflight.build_preflight(
        a203_contract_path=write_json(tmp_path / "a203.json", a203),
        release_decision_contract_path=write_json(
            tmp_path / "release-decision.json",
            release_decision,
        ),
        release_manager_preflight_path=write_json(
            tmp_path / "release-manager.json",
            release_manager,
        ),
        operator_soak_evidence_path=write_json(tmp_path / "soak.json", soak),
        operator_soak_heartbeat_path=write_json(tmp_path / "heartbeat.json", heartbeat),
        generated_at="2026-06-24T00:00:00Z",
    )

    assert payload["status"] == "A203_PRODUCTION_API_RELEASE_READY"
    assert payload["api_surface_ready"] is True
    assert payload["release_ready"] is True
    assert payload["missing_gates"] == []
    assert payload["production_graph_publication_allowed"] is True
    preflight.validate_preflight(
        payload,
        a203_contract_path=tmp_path / "a203.json",
        release_decision_contract_path=tmp_path / "release-decision.json",
        release_manager_preflight_path=tmp_path / "release-manager.json",
        operator_soak_evidence_path=tmp_path / "soak.json",
        operator_soak_heartbeat_path=tmp_path / "heartbeat.json",
    )
