from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from salary_logic import calculate, score_invoice, score_payback, score_settlement  # noqa: E402


class SalaryLogicBoundaryTests(unittest.TestCase):
    def test_day_score_functions_reject_zero_and_negative_days(self) -> None:
        for scorer, label in (
            (score_settlement, "结算时间"),
            (score_invoice, "开票时间"),
            (score_payback, "回款时间"),
        ):
            with self.subTest(label=label, days=0):
                with self.assertRaisesRegex(ValueError, f"{label}必须 >= 1"):
                    scorer(0)
            with self.subTest(label=label, days=-1):
                with self.assertRaisesRegex(ValueError, f"{label}必须 >= 1"):
                    scorer(-1)

    def test_calculate_rejects_zero_day_inputs_before_weighted_total(self) -> None:
        base = {
            "year_target": 5_000_000,
            "quarter_actual": 250_000,
            "margin": 0.25,
            "settlement_days": 10,
            "invoice_days": 10,
            "payback_days": 30,
            "audit_bias": 0.01,
            "customer_rate": 0.01,
            "province": "湖北",
        }
        for field, label in (
            ("settlement_days", "结算时间"),
            ("invoice_days", "开票时间"),
            ("payback_days", "回款时间"),
        ):
            values = dict(base)
            values[field] = 0
            with self.subTest(field=field):
                with self.assertRaisesRegex(ValueError, f"{label}必须 >= 1"):
                    calculate(**values)

    def test_existing_one_day_boundaries_stay_stable(self) -> None:
        self.assertEqual(score_settlement(1), 200)
        self.assertEqual(score_invoice(1), 150)
        self.assertEqual(score_payback(1), 200)

        result = calculate(
            year_target=5_000_000,
            quarter_actual=250_000,
            margin=0.25,
            settlement_days=1,
            invoice_days=1,
            payback_days=1,
            audit_bias=0.01,
            customer_rate=0.01,
            province="湖北",
        )
        self.assertEqual(len(result.breakdown), 7)
        self.assertTrue(all(row["原始得分"] is not None for row in result.breakdown))


if __name__ == "__main__":
    unittest.main()
