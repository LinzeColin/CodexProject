import unittest

import pandas as pd

from quantlab.indicators import rsi, sma


class IndicatorTests(unittest.TestCase):
    def test_sma(self):
        values = pd.Series([1, 2, 3, 4, 5])
        result = sma(values, 3)
        self.assertTrue(pd.isna(result.iloc[1]))
        self.assertEqual(result.iloc[-1], 4)

    def test_rsi_bounds(self):
        values = pd.Series([1, 2, 3, 2, 3, 4, 5, 4, 3, 4, 5, 6, 7, 8, 9, 10], dtype=float)
        result = rsi(values, 14).dropna()
        self.assertTrue(((result >= 0) & (result <= 100)).all())


if __name__ == "__main__":
    unittest.main()

