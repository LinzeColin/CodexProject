from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from quantlab.integrations.consumer_behavior import consumer_behavior_state_frame, read_consumer_behavior_state, sync_consumer_behavior_state


class ConsumerBehaviorIntegrationTest(unittest.TestCase):
    def test_consumer_behavior_sqlite_state_is_synced_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_db = root / "consumption.sqlite"
            with sqlite3.connect(source_db) as conn:
                conn.execute("CREATE TABLE runs (run_id TEXT PRIMARY KEY, generated_at TEXT, created_at TEXT)")
                conn.execute("CREATE TABLE transactions_ledger (unique_key TEXT PRIMARY KEY, amount TEXT, risk_label TEXT, main_category TEXT, needs_manual_review INTEGER)")
                conn.execute("CREATE TABLE latest_summary_metrics (metric TEXT PRIMARY KEY, value TEXT)")
                conn.execute("INSERT INTO runs VALUES ('run_1', '2026-06-04T10:00:00', '2026-06-04T10:00:00')")
                conn.execute("INSERT INTO transactions_ledger VALUES ('a', '12.50', 'normal', 'food', 0)")
                conn.execute("INSERT INTO transactions_ledger VALUES ('b', '30.00', 'review', 'investing', 1)")
                conn.execute("INSERT INTO latest_summary_metrics VALUES ('total_spend', '42.50')")
            bus_db = root / "ResearchBus.sqlite"

            state = read_consumer_behavior_state(source_db)
            result = sync_consumer_behavior_state([source_db], bus_db_path=bus_db)
            frame = consumer_behavior_state_frame(bus_db)

            self.assertEqual(state["ledger_count"], 2)
            self.assertEqual(state["manual_review_count"], 1)
            self.assertEqual(result.records, 1)
            self.assertEqual(frame.iloc[0]["transaction_count"], 0)
            self.assertEqual(frame.iloc[0]["ledger_count"], 2)


if __name__ == "__main__":
    unittest.main()
