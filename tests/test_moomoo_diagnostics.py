import tempfile
import unittest
from pathlib import Path

import pandas as pd

from quantlab.data.moomoo_diagnostics import diagnose_moomoo_quote


class FakeMoomooProvider:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port

    def get_bars(self, request):
        return pd.DataFrame(
            {
                "datetime": pd.date_range("2024-01-01", periods=3, freq="D"),
                "open": [100.0, 101.0, 102.0],
                "high": [101.0, 102.0, 103.0],
                "low": [99.0, 100.0, 101.0],
                "close": [100.5, 101.5, 102.5],
                "volume": [1000, 1100, 1200],
            }
        )


class MoomooDiagnosticsTests(unittest.TestCase):
    def test_missing_futu_package_returns_needs_package(self):
        result = diagnose_moomoo_quote(package_checker=lambda _: False)

        self.assertEqual(result.status, "NeedsPackage")
        self.assertFalse(result.package_available)
        self.assertFalse(result.quote_check)

    def test_missing_opend_returns_needs_opend(self):
        result = diagnose_moomoo_quote(
            package_checker=lambda _: True,
            connection_checker=lambda host, port, timeout: False,
        )

        self.assertEqual(result.status, "NeedsOpenD")
        self.assertTrue(result.package_available)
        self.assertFalse(result.opend_reachable)

    def test_invalid_port_returns_needs_config(self):
        result = diagnose_moomoo_quote(port="not-a-port")

        self.assertEqual(result.status, "NeedsConfig")
        self.assertEqual(result.port, 0)

    def test_quote_fetch_creates_quality_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = diagnose_moomoo_quote(
                package_checker=lambda _: True,
                connection_checker=lambda host, port, timeout: True,
                provider_factory=lambda host, port: FakeMoomooProvider(host, port),
                quality_output_dir=tmp,
            )

            self.assertEqual(result.status, "Ready")
            self.assertEqual(result.rows, 3)
            self.assertEqual(result.quality_status, "Pass")
            self.assertTrue(Path(result.quality_report_path).exists())


if __name__ == "__main__":
    unittest.main()
