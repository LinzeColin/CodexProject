from __future__ import annotations

import copy
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from apps.api.app.ingest.sec_normalizer import (
    SEC_COMPANY_FACTS_NORMALIZER_VERSION,
    SEC_SUBMISSIONS_NORMALIZER_VERSION,
    SecNormalizationError,
    normalize_sec_company_facts,
    normalize_sec_submissions,
)
from scripts.validate_sec_normalization_contract import build_contracts, validate_contracts

ROOT = Path(__file__).resolve().parents[2]
SUBMISSIONS_FIXTURE = ROOT / "tests/fixtures/sec/submissions_golden.json"
COMPANY_FACTS_FIXTURE = ROOT / "tests/fixtures/sec/companyfacts_golden.json"


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    assert isinstance(payload, dict)
    return payload


def test_submissions_golden_preserves_required_filing_fields() -> None:
    normalized = normalize_sec_submissions(
        load_json(SUBMISSIONS_FIXTURE),
        record_mode="fixture",
    )

    assert normalized.schema_version == SEC_SUBMISSIONS_NORMALIZER_VERSION
    assert normalized.record_mode == "fixture"
    assert normalized.cik == "0000000001"
    assert normalized.entity_name == "EEI SEC Golden Fixture Corp"
    assert len(normalized.filings) == 2

    original, amendment = normalized.filings
    assert original.accession_number == "0000000001-25-000001"
    assert original.form == "10-K"
    assert original.base_form == "10-K"
    assert original.is_amendment is False
    assert original.filed_date.isoformat() == "2025-02-01"
    assert original.report_date and original.report_date.isoformat() == "2024-12-31"
    assert original.accepted_at == datetime(2025, 2, 1, 18, 30, tzinfo=UTC)
    assert original.primary_document == "fixture-2024-10k.htm"

    assert amendment.accession_number == "0000000001-25-000002"
    assert amendment.form == "10-K/A"
    assert amendment.base_form == "10-K"
    assert amendment.is_amendment is True
    assert amendment.report_date is None
    assert amendment.primary_document == "fixture-2024-10ka.htm"
    assert amendment.to_dict()["accepted_at"] == "2025-02-10T19:45:30Z"

    assert [item.to_dict() for item in normalized.additional_files] == [
        {
            "name": "CIK0000000001-submissions-001.json",
            "filing_from": "2020-01-01",
            "filing_to": "2023-12-31",
        }
    ]


def test_submissions_rejects_parallel_array_length_drift() -> None:
    payload = load_json(SUBMISSIONS_FIXTURE)
    payload["filings"]["recent"]["reportDate"].pop()

    with pytest.raises(SecNormalizationError, match="reportDate length"):
        normalize_sec_submissions(payload, record_mode="fixture")


def test_submissions_rejects_timezone_free_acceptance_timestamp() -> None:
    payload = load_json(SUBMISSIONS_FIXTURE)
    payload["filings"]["recent"]["acceptanceDateTime"][0] = "2025-02-01T18:30:00"

    with pytest.raises(SecNormalizationError, match="must include a timezone"):
        normalize_sec_submissions(payload, record_mode="fixture")


def test_submissions_preserves_unknown_document_as_none() -> None:
    payload = load_json(SUBMISSIONS_FIXTURE)
    payload["filings"]["recent"]["primaryDocument"][1] = ""

    normalized = normalize_sec_submissions(payload, record_mode="fixture")

    assert normalized.filings[1].primary_document is None


def test_synthetic_submissions_fixture_cannot_be_relabeled_live() -> None:
    with pytest.raises(SecNormalizationError, match="cannot be relabeled"):
        normalize_sec_submissions(
            load_json(SUBMISSIONS_FIXTURE),
            record_mode="live",
        )


def test_company_facts_golden_preserves_concept_unit_period_form_filed_and_frame() -> None:
    normalized = normalize_sec_company_facts(
        load_json(COMPANY_FACTS_FIXTURE),
        record_mode="fixture",
    )

    assert normalized.schema_version == SEC_COMPANY_FACTS_NORMALIZER_VERSION
    assert normalized.record_mode == "fixture"
    assert normalized.cik == "0000000001"
    assert len(normalized.facts) == 3

    assets = next(fact for fact in normalized.facts if fact.concept == "Assets")
    assert assets.taxonomy == "us-gaap"
    assert assets.unit == "USD"
    assert assets.period_kind == "instant"
    assert assets.period_start is None
    assert assets.period_end.isoformat() == "2024-12-31"
    assert assets.form == "10-K"
    assert assets.filed_date.isoformat() == "2025-02-01"
    assert assets.frame == "CY2024Q4I"

    revenue = [
        fact
        for fact in normalized.facts
        if fact.concept == "RevenueFromContractWithCustomerExcludingAssessedTax"
    ]
    assert len(revenue) == 2
    original, amendment = revenue
    assert original.unit == amendment.unit == "USD"
    assert original.period_kind == amendment.period_kind == "duration"
    assert original.period_start == amendment.period_start
    assert original.period_end == amendment.period_end
    assert original.value == 100
    assert original.form == "10-K"
    assert original.is_amendment is False
    assert original.frame == "CY2024"
    assert amendment.value == 105
    assert amendment.form == "10-K/A"
    assert amendment.base_form == "10-K"
    assert amendment.is_amendment is True
    assert amendment.filed_date > original.filed_date
    assert amendment.frame is None
    assert amendment.to_dict()["period"] == {
        "start": "2024-01-01",
        "end": "2024-12-31",
        "kind": "duration",
    }


def test_company_facts_does_not_mutate_or_collapse_revision_fixture() -> None:
    payload = load_json(COMPANY_FACTS_FIXTURE)
    original_payload = copy.deepcopy(payload)

    normalized = normalize_sec_company_facts(payload, record_mode="fixture")

    assert payload == original_payload
    accessions = [fact.accession_number for fact in normalized.facts]
    assert accessions.count("0000000001-25-000001") == 2
    assert accessions.count("0000000001-25-000002") == 1


def test_company_facts_rejects_non_scalar_value_and_inverted_period() -> None:
    payload = load_json(COMPANY_FACTS_FIXTURE)
    entries = payload["facts"]["us-gaap"][
        "RevenueFromContractWithCustomerExcludingAssessedTax"
    ]["units"]["USD"]
    entries[0]["val"] = {"not": "scalar"}

    with pytest.raises(SecNormalizationError, match="val must be a JSON scalar"):
        normalize_sec_company_facts(payload, record_mode="fixture")

    payload = load_json(COMPANY_FACTS_FIXTURE)
    entries = payload["facts"]["us-gaap"][
        "RevenueFromContractWithCustomerExcludingAssessedTax"
    ]["units"]["USD"]
    entries[0]["start"] = "2025-01-01"
    with pytest.raises(SecNormalizationError, match="start must be <= end"):
        normalize_sec_company_facts(payload, record_mode="fixture")


def test_synthetic_company_facts_fixture_cannot_be_relabeled_live() -> None:
    with pytest.raises(SecNormalizationError, match="cannot be relabeled"):
        normalize_sec_company_facts(
            load_json(COMPANY_FACTS_FIXTURE),
            record_mode="live",
        )


def test_normalization_contract_artifacts_are_fixture_only_and_fail_closed() -> None:
    a100, a101 = build_contracts()

    validate_contracts(a100, a101)

    assert a100["contract"]["fields_preserved"] == [
        "accession",
        "form",
        "filed",
        "report",
        "accepted",
        "document",
    ]
    assert a101["contract"]["same_period_revisions_preserved_without_collapse"] is True
    assert a101["contract"]["restatement_inferred_without_source_evidence"] is False
    assert a101["release_scope"]["live_sec_request_performed"] is False
    assert a101["release_scope"]["mvp_release_ready"] is False
