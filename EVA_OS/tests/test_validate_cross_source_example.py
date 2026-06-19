import os
import unittest
from unittest.mock import patch

from quantlab.examples.validate_cross_source import _providers_for_market


class ValidateCrossSourceExampleTests(unittest.TestCase):
    def test_us_providers_include_keyed_sources_when_configured(self):
        old_alpha = os.environ.get("ALPHA_VANTAGE_API_KEY")
        old_polygon = os.environ.get("POLYGON_API_KEY")
        old_env_file = os.environ.get("QUANTLAB_ENV_FILE")
        os.environ["ALPHA_VANTAGE_API_KEY"] = "alpha"
        os.environ["POLYGON_API_KEY"] = "polygon"
        os.environ["QUANTLAB_ENV_FILE"] = "/tmp/quantlab-test-missing-env-file"
        try:
            self.assertEqual(_providers_for_market("US"), ["Yahoo Finance", "Alpha Vantage", "Polygon"])
        finally:
            _restore("ALPHA_VANTAGE_API_KEY", old_alpha)
            _restore("POLYGON_API_KEY", old_polygon)
            _restore("QUANTLAB_ENV_FILE", old_env_file)

    def test_cn_providers_include_tushare_when_configured(self):
        old_token = os.environ.get("TUSHARE_TOKEN")
        old_env_file = os.environ.get("QUANTLAB_ENV_FILE")
        os.environ["TUSHARE_TOKEN"] = "token"
        os.environ["QUANTLAB_ENV_FILE"] = "/tmp/quantlab-test-missing-env-file"
        try:
            self.assertEqual(_providers_for_market("CN"), ["AKShare", "TuShare"])
        finally:
            _restore("TUSHARE_TOKEN", old_token)
            _restore("QUANTLAB_ENV_FILE", old_env_file)

    @patch.dict(os.environ, {"QUANTLAB_ENV_FILE": "/tmp/quantlab-test-missing-env-file"}, clear=False)
    def test_provider_lists_skip_missing_keyed_sources(self):
        for key in ["TUSHARE_TOKEN", "ALPHA_VANTAGE_API_KEY", "POLYGON_API_KEY"]:
            os.environ.pop(key, None)

        self.assertEqual(_providers_for_market("US"), ["Yahoo Finance"])
        self.assertEqual(_providers_for_market("CN"), ["AKShare"])


def _restore(key: str, value: str | None) -> None:
    if value is None:
        os.environ.pop(key, None)
    else:
        os.environ[key] = value


if __name__ == "__main__":
    unittest.main()
