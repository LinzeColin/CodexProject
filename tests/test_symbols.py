import unittest

from quantlab.data.symbols import normalize_a_share_symbol


class SymbolTests(unittest.TestCase):
    def test_plain_a_share_symbol_infers_exchange(self):
        self.assertEqual(normalize_a_share_symbol("000001").tushare, "000001.SZ")
        self.assertEqual(normalize_a_share_symbol("600000").tushare, "600000.SH")

    def test_prefixed_and_suffixed_symbols(self):
        self.assertEqual(normalize_a_share_symbol("SZ000001").akshare, "000001")
        self.assertEqual(normalize_a_share_symbol("600000.SH").display, "SH600000")

    def test_invalid_symbol_raises(self):
        with self.assertRaises(ValueError):
            normalize_a_share_symbol("AAPL")


if __name__ == "__main__":
    unittest.main()

