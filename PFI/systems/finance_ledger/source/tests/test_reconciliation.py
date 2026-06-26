from __future__ import annotations

import hashlib
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from econ_bleed_analyzer.reconciliation import build_reconciliation_checks, write_reconciliation_outputs


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _make_reconciled_db(path: Path, source_file: Path, *, source_hash: str) -> None:
    with sqlite3.connect(path) as conn:
        conn.execute("create table source_archives (extracted_path text, member_sha256 text)")
        conn.execute("insert into source_archives values (?,?)", (str(source_file), source_hash))
        conn.execute("create table classified_transactions_audit (id text)")
        conn.executemany("insert into classified_transactions_audit values (?)", [("p1",), ("r1",)])
        conn.execute("create table data_trust_transactions (review_key text, data_trust_status text)")
        conn.executemany("insert into data_trust_transactions values (?,?)", [("p1", "RECONCILED"), ("r1", "NEEDS_REVIEW")])
        conn.execute("create table production_expense_allocations (review_key text, allocated_amount_cents text)")
        conn.execute("insert into production_expense_allocations values ('p1','10000')")
        conn.execute("create table summary_by_month (total_expense text)")
        conn.execute("insert into summary_by_month values ('100.00')")
        conn.execute(
            "create table manual_review_queue (order_id text, transaction_time text, counterparty text, amount_cents text, description text)"
        )
        conn.execute("insert into manual_review_queue values ('r1','2026-01-01','counterparty','2000000','review')")
        conn.commit()


class ReconciliationTests(unittest.TestCase):
    def test_reconciliation_checks_pass_for_consistent_ledger(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.csv"
            payload = b"date,amount\n2026-01-01,100\n"
            source.write_bytes(payload)
            output = root / "outputs"
            (output / "reports").mkdir(parents=True)
            (output / "audit").mkdir(parents=True)
            (output / "reports" / "data_trust_audit_report.pdf").write_bytes(b"%PDF-" + b"0" * 25_000)
            (output / "audit" / "report_manifest.json").write_text('{"reports":{}}', encoding="utf-8")
            handoff = root / "HANDOFF.md"
            handoff.write_text(str(output), encoding="utf-8")
            db = root / "ledger.sqlite"
            _make_reconciled_db(db, source, source_hash=_sha256(payload))

            with sqlite3.connect(db) as conn:
                checks = build_reconciliation_checks(conn, output_dir=output, handoff_path=handoff)
            failures = [item for item in checks if item["status"] == "fail"]
            self.assertEqual(failures, [])

            paths = write_reconciliation_outputs(checks, output)
            self.assertTrue(paths["reconciliation_checks_json"].exists())
            self.assertTrue(paths["reconciliation_checks_csv"].exists())
            self.assertTrue(paths["reconciliation_audit_pdf"].exists())
            manifest = (output / "audit" / "report_manifest.json").read_text(encoding="utf-8")
            self.assertIn("reconciliation_audit_pdf", manifest)

    def test_reconciliation_detects_source_hash_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.csv"
            source.write_bytes(b"actual")
            output = root / "outputs"
            (output / "reports").mkdir(parents=True)
            (output / "audit").mkdir(parents=True)
            (output / "reports" / "data_trust_audit_report.pdf").write_bytes(b"%PDF-" + b"0" * 25_000)
            (output / "audit" / "report_manifest.json").write_text('{"reports":{}}', encoding="utf-8")
            handoff = root / "HANDOFF.md"
            handoff.write_text(str(output), encoding="utf-8")
            db = root / "ledger.sqlite"
            _make_reconciled_db(db, source, source_hash=_sha256(b"expected"))

            with sqlite3.connect(db) as conn:
                checks = build_reconciliation_checks(conn, output_dir=output, handoff_path=handoff)
            failures = {item["check_id"]: item for item in checks if item["status"] == "fail"}
            self.assertIn("source_hash_match", failures)


if __name__ == "__main__":
    unittest.main()
