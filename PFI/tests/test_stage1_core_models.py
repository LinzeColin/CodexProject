from __future__ import annotations

import unittest

from pfi_v02.core_models import (
    Account,
    AccountSnapshot,
    AccountType,
    AcquisitionMode,
    AssetInstrument,
    AssetType,
    CredentialRef,
    CredentialScope,
    DataSource,
    DataSourceCapability,
    HoldingSnapshot,
    ImportBatch,
    LedgerEvent,
    LedgerEventType,
    NormalizedTransaction,
    RawRecord,
    ValuationSnapshot,
    build_stage1_model_contract,
    default_stage1_sources,
)


class Stage1CoreModelContractTest(unittest.TestCase):
    def test_data_sources_support_required_platforms_modes_and_non_trading_credentials(self) -> None:
        sources = {source.source_id: source for source in default_stage1_sources()}

        for source_id in ["alipay_daily", "alipay_fund", "moomoo_au", "cn_broker", "abc_bullion", "cba_bank", "wechat_pay"]:
            self.assertIn(source_id, sources)
            sources[source_id].validate()
            self.assertTrue(sources[source_id].read_only)

        self.assertIn(AcquisitionMode.OPEND_READ_ONLY, sources["moomoo_au"].acquisition_modes)
        self.assertIn(AcquisitionMode.BROWSER_ASSISTED_READ, sources["abc_bullion"].acquisition_modes)
        self.assertIn(AcquisitionMode.WATCH_FOLDER, sources["cba_bank"].acquisition_modes)

    def test_credential_ref_rejects_trading_password_requirement(self) -> None:
        credential = CredentialRef(
            "bad_trade_credential",
            (CredentialScope.READ_BALANCE,),
            trading_password_required=True,
        )

        with self.assertRaises(ValueError):
            credential.validate()

    def test_account_and_asset_instrument_cover_payment_bank_broker_fund_bullion_credit_cash(self) -> None:
        account_types = {item.value for item in AccountType}
        asset_types = {item.value for item in AssetType}

        for expected in ["PAYMENT", "BANK", "BROKERAGE", "FUND_PLATFORM", "BULLION_PLATFORM", "CREDIT_CARD", "CASH"]:
            self.assertIn(expected, account_types)
        for expected in ["CASH", "EQUITY", "ETF", "FUND", "BULLION", "CREDIT", "FX"]:
            self.assertIn(expected, asset_types)

        account = Account("acct_moomoo", "moomoo_au", AccountType.BROKERAGE, "Moomoo AU", "AUD")
        instrument = AssetInstrument("gold_oz", AssetType.BULLION, "ABC Gold", "AUD", unit="oz")

        self.assertEqual(account.source_id, "moomoo_au")
        self.assertEqual(instrument.asset_type, AssetType.BULLION)

    def test_import_batch_and_raw_record_provide_hash_parser_version_and_traceability(self) -> None:
        batch = ImportBatch("batch_cba_001", "cba_bank", "2026-06-27T10:00:00+10:00", "cba_csv_v1", "a" * 64, 2)
        raw = RawRecord("raw_001", batch.batch_id, "line-1", "b" * 64, "private://imports/cba.csv#line=1")

        self.assertEqual(batch.parser_version, "cba_csv_v1")
        self.assertEqual(len(batch.content_sha256), 64)
        self.assertEqual(raw.batch_id, batch.batch_id)
        self.assertIn("private://", raw.raw_payload_ref)

    def test_ledger_event_types_cover_cash_transfer_asset_fund_fee_tax_fx(self) -> None:
        event_types = {item.value for item in LedgerEventType}

        for expected in ["CASH", "TRANSFER", "BUY_ASSET", "SELL_ASSET", "FUND", "FEE", "TAX", "FX", "REFUND", "VALUATION"]:
            self.assertIn(expected, event_types)

    def test_normalized_transaction_and_ledger_event_separate_consumption_and_investment_effects(self) -> None:
        transaction = NormalizedTransaction(
            "txn_001",
            "cba_bank",
            "raw_001",
            "acct_cba",
            LedgerEventType.TRANSFER,
            -1000.0,
            "AUD",
            "2026-06-27",
            "CBA to Moomoo transfer",
            0.98,
        )
        event = LedgerEvent(
            "evt_001",
            transaction.transaction_id,
            transaction.event_type,
            transaction.account_id,
            transaction.amount,
            transaction.currency,
            "raw_001",
            affects_consumption=False,
            affects_investment=True,
        )

        self.assertFalse(event.affects_consumption)
        self.assertTrue(event.affects_investment)
        self.assertEqual(event.event_type, LedgerEventType.TRANSFER)

    def test_snapshot_models_are_point_in_time_and_do_not_replace_ledger_history(self) -> None:
        account_snapshot = AccountSnapshot("snap_acct", "acct_cba", "2026-06-27", 1200.0, "AUD", "cba_bank")
        holding_snapshot = HoldingSnapshot("snap_hold", "acct_moomoo", "AAPL", "2026-06-27", 3.0, 650.0, "USD", "moomoo_au")
        valuation_snapshot = ValuationSnapshot("snap_val", "gold_oz", "2026-06-27", 3500.0, "AUD", "abc_bullion")

        self.assertEqual(account_snapshot.as_of, "2026-06-27")
        self.assertEqual(holding_snapshot.instrument_id, "AAPL")
        self.assertEqual(valuation_snapshot.source_id, "abc_bullion")

    def test_model_contract_is_serializable_and_names_all_core_models(self) -> None:
        contract = build_stage1_model_contract()
        models = contract["models"]

        for expected in [
            "CredentialRef",
            "DataSource",
            "Account",
            "AssetInstrument",
            "ImportBatch",
            "RawRecord",
            "NormalizedTransaction",
            "LedgerEvent",
            "AccountSnapshot",
            "HoldingSnapshot",
            "ValuationSnapshot",
        ]:
            self.assertIn(expected, models)
        self.assertIn("No trading password", contract["boundary"])

    def test_data_source_validation_rejects_write_enabled_source(self) -> None:
        source = DataSource(
            "bad_write_source",
            "Broker",
            "Bad Broker",
            (DataSourceCapability.ORDERS,),
            (AcquisitionMode.API_READ_ONLY,),
            None,
            "daily",
            read_only=False,
        )

        with self.assertRaises(ValueError):
            source.validate()


if __name__ == "__main__":
    unittest.main()
