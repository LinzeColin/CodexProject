from __future__ import annotations

import unittest
from datetime import date, timedelta

from src.pfi_os.engine import _to_yahoo_symbol, build_thesis_queue, run_pfi_os_validation
from src.reporting.analysis import research_confidence_table


class PFIOSValidationTest(unittest.TestCase):
    def test_validation_requires_minimum_simulation_and_reruns(self) -> None:
        queue = self._queue("2026-01-15")
        with self.assertRaises(ValueError):
            run_pfi_os_validation("2026-01-15", queue, [], monte_carlo_runs=99_999, pipeline_reruns=2)
        with self.assertRaises(ValueError):
            run_pfi_os_validation("2026-01-15", queue, [], monte_carlo_runs=100_000, pipeline_reruns=1)

    def test_successful_validation_records_required_pfi_os_evidence(self) -> None:
        as_of = "2026-01-15"
        queue = self._queue(as_of)
        result = run_pfi_os_validation(
            as_of,
            queue,
            self._price_rows("TQQQ", date(2025, 10, 15), 80),
            monte_carlo_runs=100_000,
            pipeline_reruns=2,
        )
        row = result["results"][0]
        self.assertEqual(row["monte_carlo_runs"], 100_000)
        self.assertEqual(row["pipeline_reruns"], 2)
        self.assertEqual(row["data_quality"], "Pass")
        self.assertEqual(row["validation_status"], "ContinueResearch")
        self.assertEqual(row["risk_gate"], "Pass")

    def test_insufficient_history_is_not_promoted(self) -> None:
        as_of = "2026-01-16"
        result = run_pfi_os_validation(
            as_of,
            build_thesis_queue(as_of, self._factors(symbol="LOCALONLY", exchange="", asset_class="Fund"), self._advice(), []),
            self._price_rows("LOCALONLY", date(2026, 1, 1), 10),
            monte_carlo_runs=100_000,
            pipeline_reruns=2,
        )
        row = result["results"][0]
        self.assertEqual(row["data_quality"], "Insufficient")
        self.assertIn(row["validation_status"], {"DataQualityReview", "NeedsMoreEvidence"})
        self.assertEqual(row["risk_gate"], "Blocked")

    def test_research_confidence_uses_saved_pfi_os_result(self) -> None:
        as_of = "2026-01-17"
        factors = self._factors()
        advice = self._advice()
        queue = build_thesis_queue(as_of, factors, advice, [])
        run_pfi_os_validation(
            as_of,
            queue,
            self._price_rows("TQQQ", date(2025, 10, 15), 85),
            monte_carlo_runs=100_000,
            pipeline_reruns=2,
        )
        rendered = research_confidence_table(factors, advice, [], as_of)
        self.assertIn("验证通过-可继续研究", rendered)
        self.assertNotIn("ContinueResearch", rendered)
        self.assertNotIn("PFIOS未验证", rendered)

    def test_thesis_queue_covers_watchlist_factors_without_active_advice(self) -> None:
        as_of = "2026-01-18"
        factors = [
            *self._factors(symbol="TQQQ"),
            {
                "symbol": "QQQ",
                "name": "纳指100ETF",
                "exchange": "US",
                "asset_class": "ETF",
                "research_group": "纳指科技",
                "close": 100.0,
                "daily_change_pct": 0.003,
                "turnover": 1_000_000_000,
                "source_name": "unit-test",
            },
        ]
        queue = build_thesis_queue(as_of, factors, self._advice(), [])
        self.assertEqual({row["symbol"] for row in queue}, {"TQQQ", "QQQ"})
        qqq = next(row for row in queue if row["symbol"] == "QQQ")
        self.assertEqual(qqq["observation_status"], "基础验证-观望")
        self.assertIn("基础覆盖验证", qqq["evidence_summary"])

    def test_user_tradable_index_symbols_can_enter_external_history_validation(self) -> None:
        self.assertEqual(_to_yahoo_symbol({"symbol": "000688", "exchange": "SSE", "asset_class": "Index"}), "588090.SS")
        self.assertEqual(_to_yahoo_symbol({"symbol": "399986", "exchange": "SZSE", "asset_class": "Index"}), "512800.SS")
        self.assertEqual(_to_yahoo_symbol({"symbol": "000001", "exchange": "SSE", "asset_class": "Index"}), "")

    def _queue(self, as_of: str) -> list[dict[str, object]]:
        return build_thesis_queue(as_of, self._factors(), self._advice(), [])

    def _factors(self, symbol: str = "TQQQ", exchange: str = "US", asset_class: str = "ETF") -> list[dict[str, object]]:
        return [
            {
                "symbol": symbol,
                "name": "纳指科技ETF",
                "exchange": exchange,
                "asset_class": asset_class,
                "research_group": "纳指科技",
                "close": 100.0,
                "daily_change_pct": 0.012,
                "turnover": 1_000_000_000,
                "source_name": "unit-test",
            }
        ]

    def _advice(self) -> list[dict[str, object]]:
        return [
            {
                "Name": "纳指科技ETF",
                "Position": "建议买入-低仓位补足",
                "Volume": 0.04,
                "holding_amount": 1000.0,
                "risk_note": "测试风险提示",
            }
        ]

    def _price_rows(self, symbol: str, start: date, count: int) -> list[dict[str, str]]:
        rows = []
        for idx in range(count):
            rows.append(
                {
                    "date": (start + timedelta(days=idx)).isoformat(),
                    "symbol": symbol,
                    "close": str(100.0 * (1.001 ** idx)),
                    "volume": "1000000",
                    "turnover": "100000000",
                }
            )
        return rows


if __name__ == "__main__":
    unittest.main()
