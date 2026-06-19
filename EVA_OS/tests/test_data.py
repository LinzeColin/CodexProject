import unittest

import pandas as pd

from quantlab.data.cleaner import normalize_ohlcv, resample_bars
from quantlab.data.intervals import get_bars_with_interval_fallback, pandas_interval_rule
from quantlab.data.models import BarDataRequest
from quantlab.data.providers.sample_provider import SampleDataProvider
from quantlab.data.store import DataStore


class MonthlyOnlyProvider:
    name = "monthly_only"

    def get_bars(self, request: BarDataRequest) -> pd.DataFrame:
        if request.interval != "1m":
            raise NotImplementedError(f"Unsupported interval: {request.interval}")
        return normalize_ohlcv(
            pd.DataFrame(
                {
                    "datetime": pd.date_range("2024-01-31", periods=12, freq="ME"),
                    "open": range(1, 13),
                    "high": range(2, 14),
                    "low": range(0, 12),
                    "close": range(1, 13),
                    "volume": [100] * 12,
                }
            ),
            symbol=request.symbol,
            market=request.market,
        )


class DataTests(unittest.TestCase):
    def test_normalize(self):
        raw = pd.DataFrame(
            {
                "date": ["2024-01-02", "2024-01-01"],
                "open": [10, 9],
                "high": [11, 10],
                "low": [9, 8],
                "close": [10.5, 9.5],
                "volume": [1000, 900],
            }
        )
        data = normalize_ohlcv(raw, symbol="TEST", market="US")
        self.assertEqual(data.iloc[0]["close"], 9.5)
        self.assertEqual(data.iloc[0]["symbol"], "TEST")

    def test_resample(self):
        raw = pd.DataFrame(
            {
                "datetime": pd.date_range("2024-01-01 09:30", periods=5, freq="min"),
                "open": [1, 2, 3, 4, 5],
                "high": [2, 3, 4, 5, 6],
                "low": [0, 1, 2, 3, 4],
                "close": [1.5, 2.5, 3.5, 4.5, 5.5],
                "volume": [10, 20, 30, 40, 50],
            }
        )
        data = normalize_ohlcv(raw, symbol="TEST", market="US")
        out = resample_bars(data, "5min")
        self.assertEqual(len(out), 1)
        self.assertEqual(out.iloc[0]["volume"], 150)

    def test_yearly_interval_falls_back_to_monthly_resample(self):
        data, resampled_from = get_bars_with_interval_fallback(
            MonthlyOnlyProvider(),
            BarDataRequest(symbol="TEST", market="US", interval="1y", start="2024-01-01", end="2024-12-31"),
        )

        self.assertEqual(resampled_from, "1m")
        self.assertEqual(len(data), 1)
        self.assertEqual(data.iloc[0]["close"], 12)
        self.assertEqual(data.iloc[0]["volume"], 1200)

    def test_sample_provider_supports_yearly_interval(self):
        data = SampleDataProvider(seed=100).get_bars(
            BarDataRequest(symbol="TEST", market="US", interval="1y", start="2020-01-01", end="2024-12-31")
        )

        self.assertGreaterEqual(len(data), 4)
        self.assertEqual(data.iloc[0]["symbol"], "TEST")

    def test_sample_provider_overlap_is_stable_when_start_changes(self):
        provider = SampleDataProvider(seed=101)
        wide = provider.get_bars(BarDataRequest(symbol="TEST", market="US", interval="1d", start="2023-01-01", end="2024-12-31"))
        narrow = provider.get_bars(BarDataRequest(symbol="TEST", market="US", interval="1d", start="2024-01-01", end="2024-12-31"))

        overlap = wide[wide["datetime"].isin(narrow["datetime"])].reset_index(drop=True)
        pd.testing.assert_series_equal(overlap["close"], narrow["close"], check_names=False)
        pd.testing.assert_series_equal(overlap["volume"], narrow["volume"], check_names=False)

    def test_sample_provider_intraday_overlap_is_stable_when_start_changes(self):
        provider = SampleDataProvider(seed=102)
        wide = provider.get_bars(BarDataRequest(symbol="TEST", market="US", interval="60min", start="2024-01-01", end="2024-01-05"))
        narrow = provider.get_bars(BarDataRequest(symbol="TEST", market="US", interval="60min", start="2024-01-03", end="2024-01-05"))

        overlap = wide[wide["datetime"].isin(narrow["datetime"])].reset_index(drop=True)
        pd.testing.assert_series_equal(overlap["close"], narrow["close"], check_names=False)
        pd.testing.assert_series_equal(overlap["volume"], narrow["volume"], check_names=False)

    def test_interval_rules_include_quarter_and_year(self):
        self.assertEqual(pandas_interval_rule("1q"), "1QE")
        self.assertEqual(pandas_interval_rule("1y"), "1YE")

    def test_store_round_trip(self):
        raw = pd.DataFrame(
            {
                "datetime": pd.date_range("2024-01-01", periods=3, freq="D"),
                "open": [1, 2, 3],
                "high": [2, 3, 4],
                "low": [0, 1, 2],
                "close": [1.5, 2.5, 3.5],
                "volume": [10, 20, 30],
            }
        )
        store = DataStore(root="/tmp/quantlab-test-store", format="csv")
        store.save_bars(raw, symbol="TEST", market="US", interval="1d")
        loaded = store.load_bars("TEST", "US", "1d")
        self.assertEqual(len(loaded), 3)
        self.assertEqual(loaded.iloc[-1]["close"], 3.5)


if __name__ == "__main__":
    unittest.main()
