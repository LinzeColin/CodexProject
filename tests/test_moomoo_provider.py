import unittest

from quantlab.data.providers.moomoo_provider import _moomoo_symbol


class MoomooProviderTests(unittest.TestCase):
    def test_moomoo_symbol_formats_markets(self):
        self.assertEqual(_moomoo_symbol("AAPL", "US"), "US.AAPL")
        self.assertEqual(_moomoo_symbol("0700.HK", "HK"), "HK.00700")
        self.assertEqual(_moomoo_symbol("600000", "CN"), "SH.600000")
        self.assertEqual(_moomoo_symbol("000001", "CN"), "SZ.000001")


if __name__ == "__main__":
    unittest.main()
