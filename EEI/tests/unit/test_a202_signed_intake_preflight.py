from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from scripts import validate_a202_signed_intake_preflight as preflight
from scripts import validate_release_decision_bundle as decisions


def signed_a202_intake() -> dict:
    payload = decisions.build_intake_template(generated_at="2026-06-24T00:00:00Z")
    payload["bundle_status"] = decisions.SIGNED_A202_INTAKE_STATUS
    payload["release_gate_closure_allowed"] = True
    payload["relationship_publication_allowed"] = True
    requirements = decisions.candidate_source_anchor_requirements()
    for entry in payload["source_license_reviews"]:
        entry.update(
            {
                "source_license_status": "approved_for_public_release",
                "allowed_use_scope": "EEI evidence review and relationship publication",
                "evidence_uri": f"internal://source-license/{entry['anchor_id']}",
                "reviewer": "source-reviewer",
                "reviewed_at": "2026-06-24T00:00:00Z",
                "signature": f"signed-source-{entry['anchor_id']}",
            }
        )
    for entry in payload["passage_level_relationship_reviews"]:
        entry.update(
            {
                "supporting_anchor_ids": requirements[entry["candidate_key"]],
                "supporting_passage_locator": f"internal://passage/{entry['candidate_key']}",
                "counter_evidence_reviewed": True,
                "decision": "approved_for_publication",
                "reviewer": "relationship-reviewer",
                "reviewed_at": "2026-06-24T00:00:00Z",
                "signature": f"signed-passage-{entry['candidate_key']}",
            }
        )
    for entry in payload["production_owner_signoffs"]:
        entry.update(
            {
                "owner_actor": "release-owner",
                "owner_role": "production-owner",
                "authority_scope": "A202 source/legal/owner relationship publication",
                "signed_at": "2026-06-24T00:00:00Z",
                "signature": f"signed-owner-{entry['candidate_key']}",
            }
        )
    payload["legal_release_clearance"].update(
        {
            "legal_reviewer": "legal-reviewer",
            "clearance_status": "RISK_WAIVER_ACCEPTED",
            "clearance_scope": "A202 relationship evidence publication",
            "risk_waiver_id_or_opinion_ref": "internal://legal/a202-waiver",
            "signed_at": "2026-06-24T00:00:00Z",
            "signature": "signed-a202-legal",
        }
    )
    payload["attestation"].update(
        {
            "signed_by": "release-manager",
            "signed_at": "2026-06-24T00:00:00Z",
            "signature": "signed-a202-intake",
        }
    )
    return payload


def write_json(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_template_preflight_is_missing_signed_inputs() -> None:
    payload = preflight.build_preflight(generated_at="2026-06-24T00:00:00Z")

    assert payload["status"] == "A202_SIGNED_INTAKE_MISSING"
    assert payload["a202_clearance_complete"] is False
    assert payload["relationship_publication_allowed"] is False
    assert payload["release_gate_closed_by_preflight"] is False
    assert payload["release_ready"] is False
    assert payload["signed_intake_source_boundary"]["closure_allowed"] is False
    assert (
        payload["signed_intake_source_boundary"]["source_kind"]
        == "repository_template"
    )
    assert {item["input_id"] for item in payload["missing_signed_inputs"]} == set(
        preflight.MISSING_SIGNED_INPUTS
    )
    preflight.validate_preflight(payload)


def test_signed_intake_preflight_completes_a202_but_not_release(
    tmp_path: Path,
) -> None:
    signed_path = write_json(tmp_path / "signed-a202-intake.json", signed_a202_intake())

    payload = preflight.build_preflight(
        signed_intake_path=signed_path,
        generated_at="2026-06-24T00:00:00Z",
    )

    assert payload["status"] == "A202_SIGNED_INTAKE_COMPLETE"
    assert payload["a202_clearance_complete"] is True
    assert payload["relationship_publication_allowed"] is True
    assert payload["release_gate_closed_by_preflight"] is False
    assert payload["release_ready"] is False
    assert payload["missing_signed_inputs"] == []
    assert payload["signed_intake_source_boundary"]["closure_allowed"] is True
    assert (
        payload["signed_intake_source_boundary"]["source_kind"]
        == "external_operator_file"
    )
    assert payload["signed_intake_summary"]["source_license_reviews"] == 4
    assert payload["signed_intake_summary"]["passage_reviews"] == 2
    assert "A209_24h_operator_soak" in payload[
        "remaining_external_gates_after_a202_clearance"
    ]
    preflight.validate_preflight(payload, signed_intake_path=signed_path)


def test_preflight_validation_detects_signed_source_drift(tmp_path: Path) -> None:
    signed = signed_a202_intake()
    signed_path = write_json(tmp_path / "signed-a202-intake.json", signed)
    payload = preflight.build_preflight(
        signed_intake_path=signed_path,
        generated_at="2026-06-24T00:00:00Z",
    )

    changed = copy.deepcopy(signed)
    changed["source_license_reviews"][0]["signature"] = "different"
    write_json(signed_path, changed)

    with pytest.raises(ValueError, match="A202 signed-intake preflight drift"):
        preflight.validate_preflight(payload, signed_intake_path=signed_path)


def test_signed_intake_preflight_rejects_duplicate_owner_signoff(tmp_path: Path) -> None:
    signed = signed_a202_intake()
    signed["production_owner_signoffs"].append(
        copy.deepcopy(signed["production_owner_signoffs"][0])
    )
    signed_path = write_json(tmp_path / "signed-a202-intake.json", signed)

    with pytest.raises(
        ValueError,
        match="production_owner_signoffs duplicate relationship candidates: GV-FACT-001",
    ):
        preflight.build_preflight(signed_intake_path=signed_path)
