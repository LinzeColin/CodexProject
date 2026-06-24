from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from salary_logic import calculate, round_money  # noqa: E402


class SalaryLogicRoundingTests(unittest.TestCase):
    def test_round_money_uses_decimal_half_up_to_cents(self) -> None:
        self.assertEqual(round_money(1.004), 1.0)
        self.assertEqual(round_money(1.005), 1.01)
        self.assertEqual(round_money(2.675), 2.68)

    def test_existing_hubei_fixture_money_outputs_stay_stable(self) -> None:
        result = calculate(
            year_target=5_000_000,
            quarter_actual=250_000,
            margin=0.25,
            settlement_days=10,
            invoice_days=10,
            payback_days=30,
            audit_bias=0.01,
            customer_rate=0.01,
            province="湖北",
        )
        self.assertAlmostEqual(result.total_score, 13.875, places=9)
        self.assertEqual(result.perf_money, 4995.0)
        self.assertEqual(result.total_salary, 22995.0)
        self.assertEqual(result.after_tax_salary, 22305.15)

    def test_requirements_are_exactly_pinned_for_deploy_reproducibility(self) -> None:
        requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
        self.assertEqual(requirements, ["streamlit==1.58.0", "pandas==3.0.3"])


if __name__ == "__main__":
    unittest.main()
