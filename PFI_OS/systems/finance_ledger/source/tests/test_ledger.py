from __future__ import annotations

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from econ_bleed_analyzer.ledger import extract_zip_sources, install_master_ledger


REQUIRED_TABLES = [
    "classified_transactions_audit",
    "production_expense_allocations",
    "manual_review_queue",
    "manual_review_status_summary",
    "manual_review_decision_candidates",
    "manual_review_decision_candidate_groups",
    "manual_review_queue_audit",
    "manual_review_queue_audit_summary",
    "summary_by_category",
    "summary_by_risk_tag",
    "spending_control_plan",
    "source_platform_summary",
    "data_trust_transactions",
    "reconciliation_checks",
    "entity_registry",
    "alias_map",
    "entity_registry_summary",
    "evidence_decision_matrix",
    "evidence_decision_summary",
    "summary_by_week",
    "summary_by_month",
    "summary_by_quarter",
    "summary_by_half",
    "summary_by_year",
]


class LedgerTests(unittest.TestCase):
    def test_extract_zip_sources_keeps_stable_bill_period(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "账单.zip"
            with ZipFile(archive, "w") as z:
                z.writestr("支付宝交易明细/支付宝交易明细(20220101-20220131).csv", "交易时间,交易分类\n")
                z.writestr("微信交易明细/微信交易明细(20220201-20220228).xlsx", "xlsx payload")
                z.writestr("__MACOSX/._ignored.csv", "ignored")
                z.writestr("支付宝交易明细/.DS_Store", "ignored")
            rows = extract_zip_sources(archive, root / "sources")
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["bill_period"], "20220101-20220131")
            self.assertEqual(rows[1]["bill_period"], "20220201-20220228")
            self.assertTrue(Path(str(rows[0]["extracted_path"])).exists())
            self.assertTrue(str(rows[1]["extracted_path"]).endswith(".xlsx"))

    def test_install_master_ledger_adds_metadata_and_views(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report_db = root / "report.sqlite"
            with sqlite3.connect(report_db) as conn:
                for table in REQUIRED_TABLES:
                    conn.execute(f'create table "{table}" (id text)')
                conn.commit()
            ledger_db = root / "finance_ledger.sqlite"
            install_master_ledger(
                report_db,
                ledger_db,
                source_archives=[{"source_type": "zip_member", "bill_period": "20220101-20220131"}],
                transaction_count=1,
                date_start="2022-01-01",
                date_end="2022-01-31",
                output_dir=root / "outputs",
            )
            with sqlite3.connect(ledger_db) as conn:
                metadata = dict(conn.execute("select key,value from ledger_metadata").fetchall())
                self.assertEqual(metadata["transaction_count"], "1")
                self.assertEqual(conn.execute("select bill_period from source_archives").fetchone()[0], "20220101-20220131")
                views = {row[0] for row in conn.execute("select name from sqlite_master where type='view'")}
                self.assertIn("v_production_transactions", views)
                self.assertIn("v_cashflow_monthly", views)
                self.assertIn("v_fact_expense_allocations", views)
                self.assertIn("v_source_platform_summary", views)
                self.assertIn("v_data_trust_transactions", views)
                self.assertIn("v_data_trust_sources", views)
                self.assertIn("v_data_trust_summary", views)
                self.assertIn("v_reconciliation_checks", views)
                self.assertIn("v_reconciliation_failures", views)
                self.assertIn("v_reconciliation_summary", views)
                self.assertIn("v_entity_registry", views)
                self.assertIn("v_alias_map", views)
                self.assertIn("v_entity_registry_summary", views)
                self.assertIn("v_entity_alias_conflicts", views)
                self.assertIn("v_evidence_decision_matrix", views)
                self.assertIn("v_evidence_decision_actionable", views)
                self.assertIn("v_evidence_decision_watchlist", views)
                self.assertIn("v_evidence_decision_summary", views)
                self.assertIn("v_review_status_summary", views)
                self.assertIn("v_manual_review_queue_audit", views)
                self.assertIn("v_manual_review_queue_blockers", views)
                self.assertIn("v_manual_review_queue_summary", views)
                self.assertEqual(conn.execute("select data_trust_status from data_trust_sources").fetchone()[0], "RAW_IMPORTED")
                self.assertGreater(conn.execute("select count(*) from reconciliation_checks").fetchone()[0], 0)
                self.assertGreater(conn.execute("select count(*) from evidence_decision_matrix").fetchone()[0], 0)
                self.assertGreater(conn.execute("select count(*) from evidence_decision_summary").fetchone()[0], 0)
                self.assertIn("v_review_decision_candidates", views)
                self.assertIn("v_review_decision_candidate_groups", views)
                self.assertIn("v_mart_daily_cashflow", views)


if __name__ == "__main__":
    unittest.main()
