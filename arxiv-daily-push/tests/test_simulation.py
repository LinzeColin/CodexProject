from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from arxiv_daily_push.cli import main
from arxiv_daily_push.simulation import (
    TWO_DAY_SIMULATION_MODEL_ID,
    run_two_day_simulation,
    validate_two_day_simulation_report,
)


ROOT = Path(__file__).resolve().parents[2]


class TwoDaySimulationTests(unittest.TestCase):
    def test_two_day_simulation_passes_without_production_claim(self) -> None:
        report = run_two_day_simulation(
            path=ROOT,
            generated_at="2026-06-22T06:30:00+10:00",
            start_date="2026-06-22",
        )

        self.assertEqual(report["model_id"], TWO_DAY_SIMULATION_MODEL_ID)
        self.assertEqual(report["status"], "pass")
        self.assertTrue(report["two_day_simulation_ready"])
        self.assertEqual(report["observed_day_count"], 2)
        self.assertFalse(report["accepted_for_production"])
        self.assertFalse(report["production_acceptance_claimed"])
        self.assertFalse(report["side_effects_performed"])
        self.assertFalse(report["real_smtp_sent"])
        self.assertFalse(report["real_release_uploaded"])
        self.assertFalse(report["secret_values_logged"])
        self.assertEqual(report["simulation_policy"]["smtp"], "mocked")
        self.assertEqual(report["simulation_policy"]["release"], "mocked")
        self.assertEqual(len(report["scheduled_execution_summaries"]), 2)
        self.assertTrue(all(item["production_evidence_ready"] for item in report["scheduled_execution_summaries"]))
        daily_runs = report["trial_evidence"]["daily_runs"]
        self.assertEqual({run["date"] for run in daily_runs}, {"2026-06-22", "2026-06-23"})
        self.assertEqual(len({run["source_id"] for run in daily_runs}), 2)
        self.assertNotIn("configured-adp-smtp-password", json.dumps(report, ensure_ascii=False))
        self.assertFalse(validate_two_day_simulation_report(report))

    def test_two_day_simulation_blocks_invalid_start_date(self) -> None:
        report = run_two_day_simulation(
            path=ROOT,
            generated_at="2026-06-22T06:30:00+10:00",
            start_date="not-a-date",
        )

        self.assertEqual(report["status"], "blocked")
        self.assertFalse(report["two_day_simulation_ready"])
        self.assertIn("start_date must be ISO", " ".join(report["blocking_reasons"]))
        self.assertFalse(validate_two_day_simulation_report(report))

    def test_cli_run_two_day_simulation_outputs_json(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            result = main(
                [
                    "run-two-day-simulation",
                    "--path",
                    str(ROOT),
                    "--generated-at",
                    "2026-06-22T06:30:00+10:00",
                    "--start-date",
                    "2026-06-22",
                    "--json",
                ]
            )

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["model_id"], TWO_DAY_SIMULATION_MODEL_ID)
        self.assertTrue(payload["two_day_simulation_ready"])
        self.assertEqual(payload["observed_day_count"], 2)


if __name__ == "__main__":
    unittest.main()
