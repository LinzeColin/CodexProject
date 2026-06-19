import unittest
from unittest.mock import Mock, patch

from quantlab.data.symbol_search import search_symbols


class SymbolSearchTests(unittest.TestCase):
    @patch("quantlab.data.symbol_search.requests.get")
    def test_yahoo_symbol_search_returns_prefixed_us_matches(self, mock_get):
        response = Mock()
        response.json.return_value = {"quotes": [{"symbol": "AAPL", "shortname": "Apple Inc."}, {"symbol": "0700.HK", "shortname": "Tencent"}]}
        response.raise_for_status.return_value = None
        mock_get.return_value = response

        rows = search_symbols("A", "US")

        self.assertEqual(rows[0].symbol, "AAPL")
        self.assertEqual(rows[0].provider, "Yahoo Finance")
        self.assertTrue(all(".HK" not in row.symbol for row in rows))

    def test_fallback_search_supports_cn_code_contains(self):
        rows = search_symbols("1", "CN")

        self.assertTrue(any("1" in row.symbol for row in rows))

    def test_fallback_search_supports_hk_code_contains(self):
        rows = search_symbols("7", "HK")

        self.assertTrue(any("7" in row.symbol for row in rows))


if __name__ == "__main__":
    unittest.main()
