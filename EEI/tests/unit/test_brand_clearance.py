from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from scripts import validate_brand_clearance as brand


def signed_bundle_from_template() -> dict:
    payload = copy.deepcopy(brand.build_intake_template())
    payload["bundle_status"] = "SIGNED_BRAND_CLEARANCE_BUNDLE"
    payload["release_gate_closure_allowed"] = True
    payload["public_brand_launch_allowed"] = True
    for entry in payload["trademark_knockout_reviews"]:
        entry.update(
            {
                "registry_or_search_system": f"{entry['jurisdiction']} trademark registry",
                "searched_at": "2026-06-24T00:00:00Z",
                "result_summary": "No blocking same-category conflict found.",
                "blocking_conflicts_found": False,
                "evidence_uri": f"internal://brand/trademark/{entry['jurisdiction']}",
                "reviewer": "brand-legal-reviewer",
                "signature": f"signed-trademark-{entry['jurisdiction']}",
            }
        )
    for entry in payload["market_surface_searches"]:
        entry.update(
            {
                "searched_at": "2026-06-24T00:00:00Z",
                "result_summary": "No blocking market-surface conflict found.",
                "blocking_conflicts_found": False,
                "evidence_uri": f"internal://brand/surface/{entry['surface']}",
                "reviewer": "brand-market-reviewer",
                "signature": f"signed-surface-{entry['surface']}",
            }
        )
    payload["phonetic_semantic_review"].update(
        {
            "chinese_reviewer": "zh-brand-reviewer",
            "english_reviewer": "en-brand-reviewer",
            "reviewed_at": "2026-06-24T00:00:00Z",
            "decision": "RISK_WAIVER_ACCEPTED",
            "evidence_uri": "internal://brand/phonetic-semantic-review",
            "signature": "signed-phonetic-semantic",
        }
    )
    payload["legal_or_owner_decision"].update(
        {
            "decision": "RISK_WAIVER_ACCEPTED",
            "scope": "EEI public brand launch surfaces",
            "opinion_or_waiver_ref": "internal://brand/risk-waiver",
            "signed_by": "brand-owner",
            "signed_role": "product_owner",
            "signed_at": "2026-06-24T00:00:00Z",
            "signature": "signed-brand-owner",
        }
    )
    payload["attestation"].update(
        {
            "signed_by": "release-manager",
            "signed_at": "2026-06-24T00:00:00Z",
            "signature": "signed-a210-attestation",
        }
    )
    return payload


def test_brand_clearance_intake_template_is_fail_closed() -> None:
    payload = brand.build_intake_template()

    brand.validate_intake_template(payload)

    assert payload["bundle_status"] == "TEMPLATE_ONLY"
    assert payload["release_gate_closure_allowed"] is False
    assert payload["public_brand_launch_allowed"] is False
    assert payload["template_counts_as_clearance"] is False
    assert {
        entry["jurisdiction"] for entry in payload["trademark_knockout_reviews"]
    } == brand.REQUIRED_TRADEMARK_JURISDICTIONS
    assert {entry["surface"] for entry in payload["market_surface_searches"]} == (
        brand.REQUIRED_SURFACES
    )

    with pytest.raises(AssertionError, match="signed bundle_status"):
        brand.validate_signed_intake_bundle(payload)


def test_brand_clearance_preflight_exposes_machine_policy_value() -> None:
    payload = brand.build_payload()
    source_boundary = payload["signed_bundle_source_boundary_policy"]

    assert (
        source_boundary["policy_value"]
        == "allow:artifacts/operator_inputs/|operator_inputs/|work/operator_inputs/;"
        "disallow:artifacts/tests/|data/|tests/|docs/|config/|brand/"
    )
    brand.validate_payload(payload)


def test_signed_brand_clearance_bundle_requires_no_blocking_conflicts() -> None:
    payload = signed_bundle_from_template()
    payload["trademark_knockout_reviews"][0]["blocking_conflicts_found"] = True

    with pytest.raises(AssertionError, match="trademark review has blocking conflict"):
        brand.validate_signed_intake_bundle(payload)


def test_signed_brand_clearance_bundle_validates_but_is_not_release_ready(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    payload = signed_bundle_from_template()
    path = tmp_path / "signed-a210-brand-clearance.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    brand.validate_signed_bundle(path)

    result = json.loads(capsys.readouterr().out)
    assert result["valid"] is True
    assert result["a210_clearance_complete"] is True
    assert result["release_ready"] is False
    assert result["signed_bundle_source_boundary"]["closure_allowed"] is True
    assert (
        result["signed_bundle_source_boundary"]["source_kind"]
        == "external_operator_file"
    )
    assert "A209_24h_operator_soak" in result["remaining_external_gates"]
    assert result["trademark_jurisdictions"] == sorted(
        brand.REQUIRED_TRADEMARK_JURISDICTIONS
    )
    assert result["market_surfaces"] == sorted(brand.REQUIRED_SURFACES)


def test_signed_brand_clearance_rejects_repository_template() -> None:
    with pytest.raises(AssertionError, match="repository_template"):
        brand.validate_signed_bundle(brand.ROOT / brand.INTAKE_TEMPLATE_PATH)


def test_signed_brand_clearance_rejects_repository_fixture(tmp_path: Path) -> None:
    payload = signed_bundle_from_template()
    fixture_dir = brand.ROOT / "artifacts/tests/a210"
    fixture_path = fixture_dir / "signed-a210-brand-clearance-fixture.json"
    fixture_path.write_text(json.dumps(payload), encoding="utf-8")
    try:
        with pytest.raises(AssertionError, match="repository_fixture_or_source"):
            brand.validate_signed_bundle(fixture_path)
    finally:
        fixture_path.unlink(missing_ok=True)


def test_signed_brand_clearance_allows_approved_operator_input_dir(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    payload = signed_bundle_from_template()
    operator_dir = brand.ROOT / "artifacts/operator_inputs/a210"
    operator_dir.mkdir(parents=True, exist_ok=True)
    operator_path = operator_dir / "signed-a210-brand-clearance-test.json"
    operator_path.write_text(json.dumps(payload), encoding="utf-8")
    try:
        brand.validate_signed_bundle(operator_path)

        result = json.loads(capsys.readouterr().out)
        assert result["signed_bundle_source_boundary"]["closure_allowed"] is True
        assert (
            result["signed_bundle_source_boundary"]["source_kind"]
            == "repository_operator_input"
        )
    finally:
        operator_path.unlink(missing_ok=True)
        try:
            operator_dir.rmdir()
            operator_dir.parent.rmdir()
        except OSError:
            pass
