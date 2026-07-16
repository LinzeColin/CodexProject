from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from pfi_os.application.read_models.account_balance import (
    build_account_home_api_contract,
    build_current_account_read_model,
    reconcile_cash,
)
from pfi_os.domain.accounts import AccountSnapshot, CashReconciliationInput


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_cash_reconciliation_uses_exact_decimal_formula_only_with_complete_evidence() -> None:
    result = reconcile_cash(
        CashReconciliationInput(
            opening_balance=Decimal("10.00"),
            confirmed_net_flows=Decimal("3.00"),
            adjustments=Decimal("-1.00"),
            observed_closing_balance=Decimal("12.00"),
            currency="CNY",
            source_ids=("SRC-ACCOUNT-BALANCES",),
            coverage_start=date(2026, 7, 1),
            coverage_end=date(2026, 7, 14),
            data_as_of=date(2026, 7, 14),
            source_content_hash="sha256:" + "a" * 64,
        )
    )

    assert result["status"] == "ready"
    assert result["expected_closing_balance"] == "12.00"
    assert result["observed_closing_balance"] == "12.00"
    assert result["discrepancy"] == "0.00"
    assert result["formula_id"] == "FORM-PFI-008"
    assert result["calculation_state"] == "calculated"


def test_cash_reconciliation_fails_closed_on_discrepancy() -> None:
    result = reconcile_cash(
        CashReconciliationInput(
            opening_balance=Decimal("10.00"),
            confirmed_net_flows=Decimal("3.00"),
            adjustments=Decimal("-1.00"),
            observed_closing_balance=Decimal("11.99"),
            currency="CNY",
            source_ids=("SRC-ACCOUNT-BALANCES",),
            coverage_start=date(2026, 7, 1),
            coverage_end=date(2026, 7, 14),
            data_as_of=date(2026, 7, 14),
            source_content_hash="sha256:" + "b" * 64,
        )
    )

    assert result["status"] == "reconciliation_failed"
    assert result["value"] is None
    assert result["discrepancy"] == "-0.01"


def test_cash_reconciliation_rejects_float_and_incomplete_lineage() -> None:
    with pytest.raises(TypeError, match="Decimal"):
        CashReconciliationInput(
            opening_balance=10.0,  # type: ignore[arg-type]
            confirmed_net_flows=Decimal("3"),
            adjustments=Decimal("0"),
            observed_closing_balance=Decimal("13"),
            currency="CNY",
            source_ids=("SRC-ACCOUNT-BALANCES",),
            coverage_start=date(2026, 7, 1),
            coverage_end=date(2026, 7, 14),
            data_as_of=date(2026, 7, 14),
            source_content_hash="sha256:" + "c" * 64,
        )
    with pytest.raises(ValueError, match="source_ids"):
        CashReconciliationInput(
            opening_balance=Decimal("10"),
            confirmed_net_flows=Decimal("3"),
            adjustments=Decimal("0"),
            observed_closing_balance=Decimal("13"),
            currency="CNY",
            source_ids=(),
            coverage_start=date(2026, 7, 1),
            coverage_end=date(2026, 7, 14),
            data_as_of=date(2026, 7, 14),
            source_content_hash="sha256:" + "c" * 64,
        )
    with pytest.raises(ValueError, match="source_id"):
        AccountSnapshot(
            snapshot_id="snapshot-contract-test",
            snapshot_kind="liability",
            account_ref="opaque-contract-ref",
            source_id="SRC-ACCOUNT-BALANCES",
            currency="CNY",
            opening_balance=Decimal("1"),
            closing_balance=Decimal("1"),
            coverage_start=date(2026, 7, 1),
            coverage_end=date(2026, 7, 14),
            data_as_of=date(2026, 7, 14),
            source_record_count=1,
            source_content_hash="sha256:" + "d" * 64,
        )


def test_home_and_accounts_api_share_the_exact_same_snapshot_hash() -> None:
    read_model = build_current_account_read_model(REPO_ROOT)
    api = build_account_home_api_contract(read_model)

    assert api["status"] == "not_loaded"
    assert api["surface_ids"] == ["homepage", "accounts"]
    assert api["surface_read_model_hashes"]["homepage"] == read_model["read_model_hash"]
    assert api["surface_read_model_hashes"]["accounts"] == read_model["read_model_hash"]
    assert api["surfaces"]["homepage"]["metrics"] == api["surfaces"]["accounts"]["metrics"]
    assert api["same_source_hash"] is True
