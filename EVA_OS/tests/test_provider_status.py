import os
import unittest
from unittest.mock import patch

from quantlab.data import market_symbol_examples, provider_status_rows
from quantlab.data.provider_status import _moomoo_status


class ProviderStatusTests(unittest.TestCase):
    def test_provider_status_includes_core_sources(self):
        rows = provider_status_rows()
        providers = {row["provider"] for row in rows}

        self.assertIn("Sample", providers)
        self.assertIn("Moomoo", providers)
        self.assertIn("AKShare", providers)
        self.assertIn("TuShare", providers)
        self.assertIn("Yahoo Finance", providers)
        self.assertIn("Alpha Vantage", providers)
        self.assertIn("Polygon", providers)

    def test_token_status_reflects_environment(self):
        old_value = os.environ.pop("TUSHARE_TOKEN", None)
        old_env_file = os.environ.get("QUANTLAB_ENV_FILE")
        os.environ["QUANTLAB_ENV_FILE"] = "/tmp/quantlab-test-missing-env-file"
        try:
            rows = provider_status_rows()
            tushare = next(row for row in rows if row["provider"] == "TuShare")
            self.assertEqual(tushare["status"], "NeedsConfig")

            os.environ["TUSHARE_TOKEN"] = "test-token"
            rows = provider_status_rows()
            tushare = next(row for row in rows if row["provider"] == "TuShare")
            self.assertEqual(tushare["status"], "Ready")
        finally:
            if old_value is not None:
                os.environ["TUSHARE_TOKEN"] = old_value
            else:
                os.environ.pop("TUSHARE_TOKEN", None)
            if old_env_file is None:
                os.environ.pop("QUANTLAB_ENV_FILE", None)
            else:
                os.environ["QUANTLAB_ENV_FILE"] = old_env_file

    def test_market_symbol_examples_cover_cn_us_hk(self):
        examples = market_symbol_examples()
        markets = {row["市场 Market"] for row in examples}

        self.assertIn("CN A 股", markets)
        self.assertIn("US 美股", markets)
        self.assertIn("HK 港股", markets)

    @patch("quantlab.data.provider_status._package_available", return_value=False)
    def test_moomoo_status_reports_missing_package(self, _mock_package):
        self.assertEqual(_moomoo_status(), "NeedsPackage")

    @patch("quantlab.data.provider_status._port_reachable", return_value=False)
    @patch("quantlab.data.provider_status._package_available", return_value=True)
    def test_moomoo_status_reports_missing_opend(self, _mock_package, _mock_port):
        self.assertEqual(_moomoo_status(), "NeedsOpenD")

    @patch("quantlab.data.provider_status._port_reachable", return_value=True)
    @patch("quantlab.data.provider_status._package_available", return_value=True)
    def test_moomoo_status_reports_ready(self, _mock_package, _mock_port):
        self.assertEqual(_moomoo_status(), "Ready")


if __name__ == "__main__":
    unittest.main()
