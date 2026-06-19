import tempfile
import unittest

import pandas as pd

from quantlab.data.quality import assess_bars, save_quality_report
from quantlab.data.providers.factory import make_provider
from quantlab.data.providers.sample_provider import SampleDataProvider


class DataQualityTests(unittest.TestCase):
    def test_assess_bars_passes_clean_data(self):
        data = pd.DataFrame(
            {
                "datetime": pd.date_range("2024-01-01", periods=3, freq="D"),
                "open": [1.0, 2.0, 3.0],
                "high": [2.0, 3.0, 4.0],
                "low": [0.5, 1.5, 2.5],
                "close": [1.5, 2.5, 3.5],
                "volume": [100, 200, 300],
            }
        )
        report = assess_bars(data, provider="sample", symbol="TEST", market="US", interval="1d")
        self.assertEqual(report.quality_status, "Pass")
        self.assertEqual(report.row_count, 3)
        self.assertTrue(report.checksum)

    def test_save_quality_report(self):
        data = pd.DataFrame(
            {
                "datetime": pd.date_range("2024-01-01", periods=1, freq="D"),
                "open": [1.0],
                "high": [2.0],
                "low": [0.5],
                "close": [1.5],
                "volume": [100],
            }
        )
        report = assess_bars(data, provider="sample", symbol="TEST", market="US", interval="1d")
        with tempfile.TemporaryDirectory() as tmp:
            path = save_quality_report(report, output_dir=tmp)
            self.assertTrue(path.exists())
            self.assertIn("DataQuality_sample_US_TEST", path.name)

    def test_factory_sample(self):
        provider = make_provider("Sample")
        self.assertIsInstance(provider, SampleDataProvider)


if __name__ == "__main__":
    unittest.main()

