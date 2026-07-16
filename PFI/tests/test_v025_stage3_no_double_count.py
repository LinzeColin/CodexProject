from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from pfi_os.application.stage3_reconciliation import (
    build_interconnection_matrix,
    build_metric_read_model_contract,
    run_phase33_real_reconciliation,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
PFI_ROOT = REPO_ROOT / "PFI"
REPORT_ROOT = PFI_ROOT / "reports" / "pfi_v025" / "stage_3" / "phase_3_3"
MATRIX_SCHEMA_PATH = PFI_ROOT / "config" / "schemas" / "v025" / "interconnection_matrix.schema.json"
OBSERVED_AT = "2026-07-14T12:00:00Z"


def _json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


@pytest.fixture(scope="module")
def real_run():
    return run_phase33_real_reconciliation(REPO_ROOT, observed_at=OBSERVED_AT)


def test_same_economic_event_counts_once_per_metric_and_hash_is_page_independent(real_run) -> None:
    duplicated = real_run.ledger_events + (real_run.ledger_events[0],)
    contract = build_metric_read_model_contract(
        duplicated,
        metric_ids=("living_consumption", "activity_outflow", "investment_allocation"),
        page_ids=("homepage", "consumption", "investment", "cashflow", "report"),
    )

    assert contract["status"] == "pass"
    assert contract["input_ledger_event_count"] == 6880
    assert contract["unique_economic_event_count"] == 6879
    assert contract["duplicate_economic_event_count"] == 1
    assert contract["same_economic_event_per_metric_max_count"] == 1
    assert contract["per_metric_duplicate_count"] == 0
    assert len(set(contract["page_read_model_hashes"].values())) == 1
    assert next(iter(contract["page_read_model_hashes"].values())) == contract["read_model_hash"]
    assert contract["financial_values_emitted"] == 0
    assert contract["private_identifiers_emitted"] == 0


def test_real_snapshot_read_model_has_no_duplicate_event_count(real_run) -> None:
    contract = real_run.read_model_contract

    assert contract["status"] == "pass"
    assert contract["input_ledger_event_count"] == 6879
    assert contract["unique_economic_event_count"] == 6879
    assert contract["duplicate_economic_event_count"] == 0
    assert contract["per_metric_duplicate_count"] == 0
    assert len(set(contract["page_read_model_hashes"].values())) == 1


def test_interconnection_matrix_is_formal_ui_contract_for_all_required_paths(real_run) -> None:
    matrix = build_interconnection_matrix(real_run)
    schema = _json(MATRIX_SCHEMA_PATH)
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(matrix)

    rows = {row["event_type"]: row for row in matrix["event_types"]}
    required = {
        "own_account_transfer",
        "credit_card_repayment",
        "refund",
        "investment_funding",
        "fund_subscription",
        "gold_subscription",
        "investment_purchase",
        "investment_sale",
    }
    assert required <= rows.keys()
    assert matrix["main_path_coverage_count"] == 8
    assert matrix["main_path_required_count"] == 8
    assert matrix["status"] == "pass"
    assert rows["own_account_transfer"]["impact_flags"]["net_worth_effect"] == "neutral"
    assert rows["credit_card_repayment"]["impact_flags"]["living_consumption_included"] is False
    assert rows["refund"]["impact_flags"]["requires_offset_event_id"] is True
    transfer_pool = next(item for item in matrix["review_pools"] if item["review_pool_id"] == "unresolved_transfer")
    assert transfer_pool["record_count"] == 1250
    assert transfer_pool["additive_across_event_rows"] is False
    assert set(transfer_pool["candidate_event_types"]) == {
        "own_account_transfer",
        "credit_card_repayment",
        "investment_funding",
    }
    for event_type in transfer_pool["candidate_event_types"]:
        assert rows[event_type]["real_snapshot_review_count"] == 0
        assert rows[event_type]["review_pool_ids"] == ["unresolved_transfer"]
    for event_type in ("investment_funding", "fund_subscription", "gold_subscription", "investment_purchase"):
        assert rows[event_type]["impact_flags"]["investment_allocation_included"] is True
        assert rows[event_type]["impact_flags"]["living_consumption_included"] is False
    assert matrix["same_economic_event_per_metric_max_count"] == 1
    assert matrix["read_model_hash_scope"] == "snapshot_not_page"
    assert matrix["financial_values_emitted"] == 0
    assert matrix["private_identifiers_emitted"] == 0


def test_tracked_interconnection_matrix_and_read_model_contract_match_runtime() -> None:
    evidence = _json(REPORT_ROOT / "evidence.json")
    run = run_phase33_real_reconciliation(REPO_ROOT, observed_at=str(evidence["observed_at"]))

    assert _json(REPORT_ROOT / "event_type_matrix.json") == build_interconnection_matrix(run)
    assert _json(REPORT_ROOT / "read_model_contract.json") == run.read_model_contract
    assert _json(REPORT_ROOT / "lineage_samples_redacted.json") == run.lineage_samples_redacted
