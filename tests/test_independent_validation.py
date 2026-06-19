from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from quantlab.integrations.independent_validation import independent_validation_runs_frame, run_independent_validation, write_manifest


class IndependentValidationTest(unittest.TestCase):
    def test_synthetic_billion_row_dry_run_is_sharded_without_loading_data(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "ResearchBus.sqlite"

            result = run_independent_validation(
                db_path=db_path,
                synthetic_rows=1_000_000_000,
                rows_per_shard=100_000_000,
                output_dir=root / "runs",
            )
            frame = independent_validation_runs_frame(db_path)

            with sqlite3.connect(db_path) as conn:
                shard_count = conn.execute("SELECT COUNT(*) FROM independent_validation_shards").fetchone()[0]

            self.assertEqual(result.total_rows, 1_000_000_000)
            self.assertEqual(result.shard_count, 10)
            self.assertEqual(shard_count, 10)
            self.assertEqual(frame.iloc[0]["status"], "Planned")

    def test_checksum_mode_executes_synthetic_shards_without_loading_data(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "ResearchBus.sqlite"

            result = run_independent_validation(
                db_path=db_path,
                synthetic_rows=1_000,
                rows_per_shard=400,
                mode="checksum",
                output_dir=root / "runs",
            )

            with sqlite3.connect(db_path) as conn:
                rows = conn.execute(
                    """
                    SELECT status, payload_json
                    FROM independent_validation_shards
                    ORDER BY shard_index
                    """
                ).fetchall()

            self.assertEqual(result.status, "Completed")
            self.assertEqual(result.shard_count, 3)
            self.assertEqual([row[0] for row in rows], ["Completed", "Completed", "Completed"])
            payloads = [json.loads(row[1]) for row in rows]
            self.assertEqual(sum(payload["observed_rows"] for payload in payloads), 1_000)
            self.assertTrue(all(payload["checksum"] for payload in payloads))
            self.assertTrue(all(payload["execution_mode"] == "checksum" for payload in payloads))

    def test_ten_billion_worker_pool_checksum_records_execution_tier(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "ResearchBus.sqlite"

            result = run_independent_validation(
                db_path=db_path,
                synthetic_rows=10_000_000_000,
                rows_per_shard=1_000_000_000,
                mode="checksum",
                worker_count=4,
                output_dir=root / "runs",
            )

            with sqlite3.connect(db_path) as conn:
                run_payload = json.loads(conn.execute("SELECT payload_json FROM independent_validation_runs").fetchone()[0])
                shard_count = conn.execute("SELECT COUNT(*) FROM independent_validation_shards WHERE status='Completed'").fetchone()[0]

            self.assertEqual(result.total_rows, 10_000_000_000)
            self.assertEqual(result.shard_count, 10)
            self.assertEqual(result.status, "Completed")
            self.assertEqual(result.execution_tier, "local_worker_pool")
            self.assertEqual(result.worker_count, 4)
            self.assertEqual(run_payload["execution_tier"], "local_worker_pool")
            self.assertEqual(run_payload["worker_count"], 4)
            self.assertEqual(shard_count, 10)

    def test_checksum_mode_streams_csv_manifest_shards(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "ResearchBus.sqlite"
            csv_path = root / "sample.csv"
            csv_path.write_text(
                "date,close\n"
                "2026-01-01,10\n"
                "2026-01-02,11\n"
                "2026-01-03,12\n"
                "2026-01-04,13\n"
                "2026-01-05,14\n",
                encoding="utf-8",
            )
            manifest_path = write_manifest([csv_path], root / "manifest.json")

            result = run_independent_validation(
                manifest_path,
                db_path=db_path,
                rows_per_shard=2,
                mode="checksum",
                output_dir=root / "runs",
            )

            with sqlite3.connect(db_path) as conn:
                rows = conn.execute(
                    """
                    SELECT status, start_row, end_row, payload_json
                    FROM independent_validation_shards
                    ORDER BY shard_index
                    """
                ).fetchall()

            payloads = [json.loads(row[3]) for row in rows]
            self.assertEqual(result.status, "Completed")
            self.assertEqual(result.total_rows, 5)
            self.assertEqual([(row[1], row[2]) for row in rows], [(0, 2), (2, 4), (4, 5)])
            self.assertEqual([row[0] for row in rows], ["Completed", "Completed", "Completed"])
            self.assertEqual(sum(payload["observed_rows"] for payload in payloads), 5)
            self.assertTrue(all(payload["checksum"] for payload in payloads))


if __name__ == "__main__":
    unittest.main()
