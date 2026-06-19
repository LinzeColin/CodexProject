import os
import unittest
from unittest.mock import patch

from quantlab.data.models import BarDataRequest
from quantlab.data.providers.polygon_provider import PolygonProvider, _polygon_interval
from quantlab.data.providers.factory import make_provider


class FakeResponse:
    def raise_for_status(self):
        return None

    def json(self):
        return {
            "status": "OK",
            "results": [
                {"t": 1704153600000, "o": 100.0, "h": 105.0, "l": 99.0, "c": 104.0, "v": 1000},
                {"t": 1704240000000, "o": 104.0, "h": 108.0, "l": 103.0, "c": 107.0, "v": 1200},
            ],
        }


class PolygonProviderTests(unittest.TestCase):
    def test_interval_mapping(self):
        self.assertEqual(_polygon_interval("1d"), (1, "day"))
        self.assertEqual(_polygon_interval("5min"), (5, "minute"))

    def test_requires_api_key(self):
        old = os.environ.pop("POLYGON_API_KEY", None)
        old_env_file = os.environ.get("QUANTLAB_ENV_FILE")
        os.environ["QUANTLAB_ENV_FILE"] = "/tmp/quantlab-test-missing-env-file"
        try:
            with self.assertRaises(ValueError):
                PolygonProvider()
        finally:
            if old is not None:
                os.environ["POLYGON_API_KEY"] = old
            if old_env_file is None:
                os.environ.pop("QUANTLAB_ENV_FILE", None)
            else:
                os.environ["QUANTLAB_ENV_FILE"] = old_env_file

    @patch("quantlab.data.providers.polygon_provider.requests.get")
    def test_get_bars_normalizes_polygon_response(self, mock_get):
        mock_get.return_value = FakeResponse()
        provider = PolygonProvider(api_key="test-key")

        data = provider.get_bars(BarDataRequest(symbol="AAPL", market="US", interval="1d", start="2024-01-01", end="2024-01-03"))

        self.assertEqual(len(data), 2)
        self.assertEqual(data.iloc[0]["symbol"], "AAPL")
        self.assertEqual(data.iloc[-1]["close"], 107.0)
        self.assertIn("apiKey", mock_get.call_args.kwargs["params"])

    def test_factory_supports_polygon(self):
        old = os.environ.get("POLYGON_API_KEY")
        old_env_file = os.environ.get("QUANTLAB_ENV_FILE")
        os.environ["QUANTLAB_ENV_FILE"] = "/tmp/quantlab-test-missing-env-file"
        os.environ["POLYGON_API_KEY"] = "test-key"
        try:
            provider = make_provider("Polygon")
            self.assertEqual(provider.name, "polygon")
        finally:
            if old is None:
                os.environ.pop("POLYGON_API_KEY", None)
            else:
                os.environ["POLYGON_API_KEY"] = old
            if old_env_file is None:
                os.environ.pop("QUANTLAB_ENV_FILE", None)
            else:
                os.environ["QUANTLAB_ENV_FILE"] = old_env_file


if __name__ == "__main__":
    unittest.main()
