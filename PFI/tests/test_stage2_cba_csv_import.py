from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pfi_v02.core_models import LedgerEventType
from pfi_v02.stage2_import import detect_watch_folder_files, parse_cba_csv_bytes, reconcile_cba_transfer


CBA_CSV = """Date,Description,Debit,Credit,Account
27/06/2026,Salary from employer,,3200.00,acct_cba_main
28/06/2026,CBA transfer to Moomoo brokerage,5000.00,,acct_cba_main
29/06/2026,Credit card repayment,1200.00,,acct_cba_main
30/06/2026,ABC Bullion gold purchase,700.00,,acct_cba_main
"""


class Stage2CbaCsvImportTest(unittest.TestCase):
    def test_cba_csv_parser_normalizes_date_description_amount_direction_and_account(self) -> None:
        result = parse_cba_csv_bytes(CBA_CSV.encode("utf-8"))

        self.assertEqual(result.import_batch.source_id, "cba_bank")
        self.assertEqual(result.import_batch.parser_version, "cba_csv_v1")
        self.assertEqual(result.import_batch.raw_record_count, 4)
        self.assertEqual(len(result.raw_records), 4)
        self.assertEqual(len(result.transactions), 4)
        self.assertEqual(result.transactions[0].occurred_at, "2026-06-27")
        self.assertEqual(result.transactions[0].amount, 3200.0)
        self.assertEqual(result.transactions[1].amount, -5000.0)
        self.assertEqual(result.transactions[1].account_id, "acct_cba_main")

    def test_cba_import_traceability_includes_batch_raw_hash_and_parser_version(self) -> None:
        result = parse_cba_csv_bytes(CBA_CSV.encode("utf-8"))

        raw = result.raw_records[0]
        txn = result.transactions[0]
        self.assertEqual(raw.batch_id, result.import_batch.batch_id)
        self.assertEqual(txn.raw_id, raw.raw_id)
        self.assertEqual(len(result.import_batch.content_sha256), 64)
        self.assertEqual(len(raw.payload_sha256), 64)
        self.assertIn("private://imports/", raw.raw_payload_ref)

    def test_watch_folder_recognizes_cba_csv_and_dedupes_same_content(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            inbox = Path(temp_dir)
            (inbox / "cba-june.csv").write_text(CBA_CSV, encoding="utf-8")
            (inbox / "commbank-copy.csv").write_text(CBA_CSV, encoding="utf-8")
            (inbox / "notes.txt").write_text("ignore", encoding="utf-8")

            candidates = detect_watch_folder_files(inbox)

        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].source_id, "cba_bank")
        self.assertEqual(candidates[0].parser_hint, "cba_csv_v1")

    def test_transfer_matching_keeps_investment_credit_repayment_and_bullion_out_of_consumption(self) -> None:
        result = parse_cba_csv_bytes(CBA_CSV.encode("utf-8"))
        matches = [reconcile_cba_transfer(txn) for txn in result.transactions]
        matches = [match for match in matches if match is not None]
        by_type = {match.match_type: match for match in matches}

        self.assertIn("investment_deposit", by_type)
        self.assertIn("credit_card_repayment", by_type)
        self.assertIn("bullion_payment", by_type)
        for match in by_type.values():
            self.assertFalse(match.affects_consumption)

    def test_cba_transfer_and_bullion_events_are_not_ordinary_cash_consumption(self) -> None:
        result = parse_cba_csv_bytes(CBA_CSV.encode("utf-8"))
        event_types = {txn.description: txn.event_type for txn in result.transactions}

        self.assertEqual(event_types["CBA transfer to Moomoo brokerage"], LedgerEventType.TRANSFER)
        self.assertEqual(event_types["Credit card repayment"], LedgerEventType.TRANSFER)
        self.assertEqual(event_types["ABC Bullion gold purchase"], LedgerEventType.BUY_ASSET)


if __name__ == "__main__":
    unittest.main()
