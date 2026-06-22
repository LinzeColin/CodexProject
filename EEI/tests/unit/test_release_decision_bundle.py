from __future__ import annotations

import copy
import json
from argparse import Namespace
from pathlib import Path

import pytest

from scripts import validate_release_decision_bundle as bundle


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


def test_release_decision_template_validates_but_is_not_release_evidence() -> None:
    template = bundle.read_json(bundle.DEFAULT_TEMPLATE)

    bundle.validate_template_bundle(template)

    with pytest.raises(ValueError, match="template-only bundle is not signed"):
        bundle.validate_signed_decision_bundle(template)


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
            "evidence_uri": "internal://source-license/NVDA-ANCHOR-002",
        }
    )

    with pytest.raises(ValueError, match="missing signed decision field: signature"):
        bundle.validate_signed_decision_bundle(signed)


def test_signed_decision_bundle_is_complete_but_not_release_ready(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    signed = copy.deepcopy(bundle.read_json(bundle.DEFAULT_TEMPLATE))
    signed["bundle_status"] = "SIGNED_DECISION_BUNDLE"
    signed["release_gate_closure_allowed"] = True
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
                "supporting_anchor_ids": ["NVDA-ANCHOR-002", "NVDA-ANCHOR-003"],
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
