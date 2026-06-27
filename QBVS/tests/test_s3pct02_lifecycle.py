from __future__ import annotations

import json
import multiprocessing
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from qbvs.batch import stress_random_parallel
from qbvs.cache import cache_csv_ohlcv, refresh_cache_index
from qbvs.simulation import RandomPathConfig, generate_random_paths
from qbvs.strategies import generate_strategy_specs
from qbvs.tasks import build_cache_task_manifest, run_task_manifest
from qbvs.warehouse import export_warehouse_tables, import_runs_to_warehouse, warehouse_stats


class S3PCT02LifecycleTests(unittest.TestCase):
    def test_bounded_multiprocess_cache_sqlite_cancel_resume_cleanup(self) -> None:
        before_children = {child.pid for child in multiprocessing.active_children()}
        specs = generate_strategy_specs(2)

        parallel = stress_random_parallel(
            specs,
            RandomPathConfig(paths=2, days=90, seed=20260624),
            workers=2,
            chunk_size=1,
        )
        self.assertEqual(len(parallel), 4)
        self.assertFalse([child.pid for child in multiprocessing.active_children() if child.pid not in before_children])

        _, frame = generate_random_paths(RandomPathConfig(paths=1, days=160, seed=20260625))[0]
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            csv_path = root / "sample.csv"
            cache_dir = root / "cache"
            manifest_path = root / "manifest.csv"
            runs_dir = root / "runs"
            run_dir = runs_dir / "pfi_s3pct02"
            db_path = root / "warehouse" / "qbvs.sqlite"
            export_dir = root / "warehouse" / "export"

            frame.to_csv(csv_path, index=False)
            cache_csv_ohlcv(
                csv_path,
                cache_dir,
                "S3PCT02",
                "SIM",
                source="s3pct02_temp_csv",
                asset_class="SIMULATED",
                tradability="TEST_ONLY",
            )
            cache_index = refresh_cache_index(cache_dir)
            self.assertEqual(len(cache_index), 1)
            self.assertTrue((cache_dir / "cache_index.csv").is_file())

            manifest = build_cache_task_manifest(
                cache_dir / "cache_index.csv",
                specs,
                mode="rolling",
                window_lengths=[90],
                step=45,
                min_bars=80,
            )
            self.assertGreaterEqual(len(manifest), 2)
            manifest.to_csv(manifest_path, index=False)

            cancelled_status, cancelled_results, _ = run_task_manifest(
                manifest_path,
                run_dir,
                cancel_after_tasks=1,
            )
            self.assertIn("completed", set(cancelled_status["status"]))
            self.assertIn("cancelled", set(cancelled_status["status"]))
            self.assertEqual(len(cancelled_results), 1)
            first_control = json.loads((run_dir / "run_control.json").read_text(encoding="utf-8"))
            self.assertEqual(first_control["cancel_after_tasks"], 1)
            self.assertGreater(first_control["cancelled_tasks"], 0)

            resumed_status, resumed_results, resumed_summary = run_task_manifest(manifest_path, run_dir)
            self.assertIn("cached", set(resumed_status["status"]))
            self.assertIn("completed", set(resumed_status["status"]))
            self.assertNotIn("cancelled", set(resumed_status["status"]))
            self.assertEqual(len(resumed_results), len(manifest))
            self.assertFalse(resumed_summary.empty)

            imported = import_runs_to_warehouse(runs_dir, db_path)
            self.assertEqual(imported["runs"], 1)
            self.assertEqual(imported["validation_results"], len(resumed_results))
            stats = warehouse_stats(db_path)
            self.assertEqual(stats["validation_results"], len(resumed_results))
            exported = export_warehouse_tables(db_path, export_dir)
            self.assertTrue(exported["strategy_market_summary"].is_file())
            db_path.unlink()

        after_children = [child.pid for child in multiprocessing.active_children() if child.pid not in before_children]
        self.assertFalse(after_children)


if __name__ == "__main__":
    unittest.main()
