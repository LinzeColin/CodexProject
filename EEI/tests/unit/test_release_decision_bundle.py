from __future__ import annotations

import copy
import json
from argparse import Namespace
from pathlib import Path

import pytest

from scripts import validate_release_decision_bundle as bundle

SIGNED_FIXTURE = (
    bundle.ROOT
    / "tests/fixtures/release_decision_bundle/a202_a210_signed_decision_bundle_contract_test.json"
)


def test_release_decision_bundle_contract_is_fail_closed() -> None:
    contract = bundle.build_contract(generated_at="2026-06-22T00:00:00Z")

    bundle.validate_contract(contract)

    assert contract["status"] == "PENDING_SIGNED_DECISIONS"
    assert contract["release_gate_closed_by_contract"] is False
    assert contract["relationship_publication_allowed"] is False
    assert contract["public_brand_launch_allowed"] is False
    assert contract["a202_gate_statuses"]["source_license_review"] == "missing"
    assert contract["a202_gate_statuses"]["production_owner_signoff"] == "missing"
    assert contract["a210_current_clearance_status"]["formal_legal_clearance"] == "NOT_COMPLETE"
    assert contract["signed_contract_test_summary"]["passage_reviews"] == 2
    assert (
        contract["source_files"]["golden_vertical_fact_candidates"]
        == "data/golden_vertical_fact_candidates.json"
    )
    assert contract["candidate_source_anchor_requirements"] == {
        "GV-FACT-001": ["GV-SNAPSHOT-001", "GV-SNAPSHOT-003"],
        "GV-FACT-002": ["GV-SNAPSHOT-002", "GV-SNAPSHOT-004"],
    }
    assert (
        contract["validation_policy"][
            "publication_passage_reviews_must_cover_candidate_source_anchors"
        ]
        is True
    )
    assert (
        contract["source_files"]["signed_contract_test_bundle"]
        == "tests/fixtures/release_decision_bundle/"
        "a202_a210_signed_decision_bundle_contract_test.json"
    )
    assert contract["validation_policy"]["signed_contract_test_counts_as_clearance"] is False
    assert (
        contract["validation_policy"]["production_owner_publication_requires_signed_bundle"]
        is True
    )


def test_release_decision_template_validates_but_is_not_release_evidence() -> None:
    template = bundle.read_json(bundle.DEFAULT_TEMPLATE)

    bundle.validate_template_bundle(template)

    with pytest.raises(ValueError, match="template-only bundle is not signed"):
        bundle.validate_signed_decision_bundle(template)


def signed_a202_intake_from_template() -> dict:
    payload = bundle.build_intake_template(generated_at="2026-06-22T00:00:00Z")
    payload["bundle_status"] = bundle.SIGNED_A202_INTAKE_STATUS
    payload["release_gate_closure_allowed"] = True
    payload["relationship_publication_allowed"] = True
    requirements = bundle.candidate_source_anchor_requirements()
    for entry in payload["source_license_reviews"]:
        entry.update(
            {
                "source_license_status": "approved_for_public_release",
                "allowed_use_scope": "EEI evidence review and relationship publication",
                "evidence_uri": f"internal://source-license/{entry['anchor_id']}",
                "reviewer": "source-reviewer",
                "reviewed_at": "2026-06-22T00:00:00Z",
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
                "reviewed_at": "2026-06-22T00:00:00Z",
                "signature": f"signed-passage-{entry['candidate_key']}",
            }
        )
    for entry in payload["production_owner_signoffs"]:
        entry.update(
            {
                "owner_actor": "release-owner",
                "owner_role": "production-owner",
                "authority_scope": "A202 source/legal/owner relationship publication",
                "signed_at": "2026-06-22T00:00:00Z",
                "signature": f"signed-owner-{entry['candidate_key']}",
            }
        )
    payload["legal_release_clearance"].update(
        {
            "legal_reviewer": "legal-reviewer",
            "clearance_status": "RISK_WAIVER_ACCEPTED",
            "clearance_scope": "A202 relationship evidence publication",
            "risk_waiver_id_or_opinion_ref": "internal://legal/a202-waiver",
            "signed_at": "2026-06-22T00:00:00Z",
            "signature": "signed-a202-legal",
        }
    )
    payload["attestation"].update(
        {
            "signed_by": "release-manager",
            "signed_at": "2026-06-22T00:00:00Z",
            "signature": "signed-a202-intake",
        }
    )
    return payload


def test_a202_release_decision_intake_template_is_fail_closed() -> None:
    payload = bundle.build_intake_template(generated_at="2026-06-22T00:00:00Z")

    bundle.validate_intake_template(payload)

    assert payload["schema_version"] == bundle.INTAKE_SCHEMA_VERSION
    assert payload["bundle_status"] == "TEMPLATE_ONLY"
    assert payload["release_gate_closure_allowed"] is False
    assert payload["relationship_publication_allowed"] is False
    assert payload["template_counts_as_clearance"] is False
    assert payload["candidate_source_anchor_requirements"] == {
        "GV-FACT-001": ["GV-SNAPSHOT-001", "GV-SNAPSHOT-003"],
        "GV-FACT-002": ["GV-SNAPSHOT-002", "GV-SNAPSHOT-004"],
    }
    assert {entry["anchor_id"] for entry in payload["source_license_reviews"]} == {
        "GV-SNAPSHOT-001",
        "GV-SNAPSHOT-002",
        "GV-SNAPSHOT-003",
        "GV-SNAPSHOT-004",
    }

    with pytest.raises(ValueError, match="not signed release evidence"):
        bundle.validate_signed_intake_bundle(payload)


def test_signed_a202_intake_validates_but_is_not_release_ready(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    payload = signed_a202_intake_from_template()
    path = tmp_path / "signed-a202-intake.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    bundle.validate_signed_intake(
        Namespace(
            bundle=path,
            a202_packet=bundle.DEFAULT_A202_PACKET,
            fact_candidates=bundle.DEFAULT_FACT_CANDIDATES,
        )
    )

    result = json.loads(capsys.readouterr().out)
    assert result["valid"] is True
    assert result["a202_clearance_complete"] is True
    assert result["release_ready"] is False
    assert "A209_24h_operator_soak" in result["remaining_external_gates"]
    assert result["source_license_reviews"] == 4
    assert result["passage_reviews"] == 2
    assert result["owner_signoffs"] == 2
    assert result["signed_intake_source_boundary"]["closure_allowed"] is True
    assert (
        result["signed_intake_source_boundary"]["source_kind"]
        == "external_operator_file"
    )


def test_signed_a202_intake_rejects_repository_fixture_path() -> None:
    fixture_like_path = (
        bundle.ROOT / "tests/fixtures/release_decision_bundle/signed-a202-intake.json"
    )

    with pytest.raises(
        ValueError,
        match="A202 signed intake must be operator-supplied",
    ):
        bundle.validate_signed_intake_source_path(fixture_like_path)


def test_signed_a202_intake_allows_operator_input_path() -> None:
    operator_path = bundle.ROOT / "artifacts/operator_inputs/signed-a202-intake.json"

    boundary = bundle.validate_signed_intake_source_path(operator_path)

    assert boundary["closure_allowed"] is True
    assert boundary["source_kind"] == "repository_operator_input"


def test_signed_decision_bundle_requires_every_signature() -> None:
    signed = copy.deepcopy(bundle.read_json(bundle.DEFAULT_TEMPLATE))
    signed["bundle_status"] = "SIGNED_DECISION_BUNDLE"
    signed["release_gate_closure_allowed"] = True
    signed["decision_scope"] = {
        "relationship_publication": False,
        "public_brand_launch": False,
        "release_clearance": False,
    }
    signed["source_license_reviews"][0].update(
        {
            "reviewer": "source-reviewer",
            "reviewed_at": "2026-06-22T00:00:00Z",
            "source_license_status": "approved_for_public_release",
            "allowed_use_scope": "EEI relationship review and evidence snippets",
            "evidence_uri": f"internal://source-license/{signed['source_license_reviews'][0]['anchor_id']}",
        }
    )

    with pytest.raises(ValueError, match="missing signed decision field: signature"):
        bundle.validate_signed_decision_bundle(signed)


def test_signed_decision_bundle_requires_candidate_source_anchor_coverage() -> None:
    signed = copy.deepcopy(bundle.read_json(SIGNED_FIXTURE))
    signed["passage_level_relationship_reviews"][0]["supporting_anchor_ids"] = [
        "GV-SNAPSHOT-001"
    ]

    with pytest.raises(
        ValueError,
        match="GV-FACT-001 passage review missing candidate source anchors: GV-SNAPSHOT-003",
    ):
        bundle.validate_signed_decision_bundle(signed)


def test_signed_decision_bundle_rejects_unknown_source_review_anchor() -> None:
    signed = copy.deepcopy(bundle.read_json(SIGNED_FIXTURE))
    extra = copy.deepcopy(signed["source_license_reviews"][0])
    extra["anchor_id"] = "GV-SNAPSHOT-999"
    extra["signature"] = "signed-source-GV-SNAPSHOT-999"
    signed["source_license_reviews"].append(extra)

    with pytest.raises(
        ValueError,
        match=(
            "source_license_reviews reference unknown candidate source anchors: "
            "GV-SNAPSHOT-999"
        ),
    ):
        bundle.validate_signed_decision_bundle(signed)


def test_signed_decision_bundle_rejects_duplicate_passage_review() -> None:
    signed = copy.deepcopy(bundle.read_json(SIGNED_FIXTURE))
    signed["passage_level_relationship_reviews"].append(
        copy.deepcopy(signed["passage_level_relationship_reviews"][0])
    )

    with pytest.raises(
        ValueError,
        match="passage reviews duplicate relationship candidates: GV-FACT-001",
    ):
        bundle.validate_signed_decision_bundle(signed)


def test_signed_decision_bundle_rejects_duplicate_owner_signoff() -> None:
    signed = copy.deepcopy(bundle.read_json(SIGNED_FIXTURE))
    signed["production_owner_signoffs"].append(
        copy.deepcopy(signed["production_owner_signoffs"][0])
    )

    with pytest.raises(
        ValueError,
        match="production_owner_signoffs duplicate relationship candidates: GV-FACT-001",
    ):
        bundle.validate_signed_decision_bundle(signed)


def test_signed_decision_bundle_is_complete_but_not_release_ready(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    signed = copy.deepcopy(bundle.read_json(bundle.DEFAULT_TEMPLATE))
    signed["bundle_status"] = "SIGNED_DECISION_BUNDLE"
    signed["release_gate_closure_allowed"] = True
    requirements = bundle.candidate_source_anchor_requirements()
    for entry in signed["source_license_reviews"]:
        entry.update(
            {
                "reviewer": "source-reviewer",
                "reviewed_at": "2026-06-22T00:00:00Z",
                "source_license_status": "approved_for_public_release",
                "allowed_use_scope": "EEI evidence review and release packet",
                "evidence_uri": f"internal://source-license/{entry['anchor_id']}",
                "signature": f"signed-source-{entry['anchor_id']}",
            }
        )
    for entry in signed["passage_level_relationship_reviews"]:
        entry.update(
            {
                "supporting_anchor_ids": requirements[entry["candidate_key"]],
                "supporting_passage_locator": f"internal://passage/{entry['candidate_key']}",
                "counter_evidence_reviewed": True,
                "decision": "approved_for_publication",
                "reviewer": "relationship-reviewer",
                "reviewed_at": "2026-06-22T00:00:00Z",
                "signature": f"signed-passage-{entry['candidate_key']}",
            }
        )
    for entry in signed["production_owner_signoffs"]:
        entry.update(
            {
                "owner_actor": "release-owner",
                "owner_role": "production-owner",
                "authority_scope": "A202/A210 release packet review",
                "signed_at": "2026-06-22T00:00:00Z",
                "signature": f"signed-owner-{entry['candidate_key']}",
            }
        )
    signed["legal_release_clearance"].update(
        {
            "legal_reviewer": "legal-reviewer",
            "clearance_status": "RISK_WAIVER_ACCEPTED",
            "clearance_scope": "A202 evidence and A210 brand release packet",
            "risk_waiver_id_or_opinion_ref": "internal://legal/waiver",
            "signed_at": "2026-06-22T00:00:00Z",
            "signature": "signed-legal",
        }
    )
    signed["brand_clearance_or_risk_waiver"].update(
        {
            "decision": "RISK_WAIVER_ACCEPTED",
            "scope": "EEI public brand launch surfaces",
            "evidence_uri": "internal://brand/waiver",
            "signed_by": "brand-owner",
            "signed_at": "2026-06-22T00:00:00Z",
            "signature": "signed-brand",
        }
    )
    signed["attestation"].update(
        {
            "signed_by": "release-manager",
            "signed_at": "2026-06-22T00:00:00Z",
            "signature": "signed-release-packet",
        }
    )
    signed_path = tmp_path / "signed-release-decision-bundle.json"
    signed_path.write_text(json.dumps(signed), encoding="utf-8")

    bundle.validate_bundle(Namespace(bundle=signed_path, template_only=False))

    result = json.loads(capsys.readouterr().out)
    assert result["signed_decision_complete"] is True
    assert result["release_ready"] is False
    assert "A209_24h_operator_soak" in result["remaining_external_gates"]


def test_signed_decision_fixture_validates_but_still_requires_external_gates(
    capsys: pytest.CaptureFixture[str],
) -> None:
    signed = bundle.read_json(SIGNED_FIXTURE)

    summary = bundle.validate_signed_decision_bundle(signed)
    assert summary["source_license_reviews"] == 4
    assert summary["passage_reviews"] == 2
    assert summary["owner_signoffs"] == 2
    assert summary["legal_clearance_status"] == "RISK_WAIVER_ACCEPTED"
    assert summary["brand_decision"] == "RISK_WAIVER_ACCEPTED"
    assert summary["candidate_source_anchor_coverage"]["GV-FACT-001"] == {
        "required_anchor_ids": ["GV-SNAPSHOT-001", "GV-SNAPSHOT-003"],
        "supporting_anchor_ids": ["GV-SNAPSHOT-001", "GV-SNAPSHOT-003"],
        "missing_passage_anchor_ids": [],
    }

    bundle.validate_bundle(Namespace(bundle=SIGNED_FIXTURE, template_only=False))

    result = json.loads(capsys.readouterr().out)
    assert result["signed_decision_complete"] is True
    assert result["release_ready"] is False
    assert result["bundle"].endswith(
        "tests/fixtures/release_decision_bundle/"
        "a202_a210_signed_decision_bundle_contract_test.json"
    )
