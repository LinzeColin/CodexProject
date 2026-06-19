import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import pandas as pd

from quantlab.data.models import BarDataRequest
from quantlab.data.validation import save_cross_source_validation_result, validate_close_across_sources


class FakeProvider:
    def __init__(self, name, close_offset):
        self.name = name
        self.close_offset = close_offset

    def get_bars(self, request):
        return pd.DataFrame(
            {
                "datetime": pd.date_range("2024-01-01", periods=3, freq="D"),
                "close": [10 + self.close_offset, 11 + self.close_offset, 12 + self.close_offset],
            }
        )


class ValidationTests(unittest.TestCase):
    def test_cross_source_validation_passes_close_sources(self):
        def factory(name):
            return FakeProvider(name, 0.0 if name == "a" else 0.001)

        with patch("quantlab.data.validation.make_provider", side_effect=factory):
            result = validate_close_across_sources(["a", "b"], BarDataRequest(symbol="TEST"), tolerance_pct=0.01)
        self.assertEqual(result.status, "Pass")
        self.assertEqual(result.overlap_rows, 3)

    def test_cross_source_validation_flags_large_difference(self):
        def factory(name):
            return FakeProvider(name, 0.0 if name == "a" else 2.0)

        with patch("quantlab.data.validation.make_provider", side_effect=factory):
            result = validate_close_across_sources(["a", "b"], BarDataRequest(symbol="TEST"), tolerance_pct=0.01)
        self.assertEqual(result.status, "Review")

    def test_save_cross_source_validation_result(self):
        def factory(name):
            return FakeProvider(name, 0.0 if name == "a" else 0.001)

        with patch("quantlab.data.validation.make_provider", side_effect=factory):
            result = validate_close_across_sources(["a", "b"], BarDataRequest(symbol="TEST", market="US"), tolerance_pct=0.01)

        with TemporaryDirectory() as tmp:
            path = save_cross_source_validation_result(result, output_dir=tmp)

            self.assertTrue(Path(path).exists())
            text = Path(path).read_text(encoding="utf-8")
            self.assertIn('"status": "Pass"', text)
            self.assertIn('"details"', text)


if __name__ == "__main__":
    unittest.main()
