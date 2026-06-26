from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from econ_bleed_analyzer.advice import build_budget_pressure_radar, build_control_plan


class AdviceTests(unittest.TestCase):
    def test_pending_review_gets_p0_action(self):
        plan = build_control_plan(
            {"total_expense": 100_000_00, "pending_review": 20_000_00},
            [{"level": "主类", "main_category": "生活刚需", "amount_cents": 80_000_00}],
            [],
        )
        self.assertEqual(plan[0]["priority"], "P0")
        self.assertEqual(plan[0]["focus_area"], "大额待复核")
        self.assertEqual(plan[0]["review_needed"], "是")

    def test_optimizable_spending_gets_saving_estimate(self):
        plan = build_control_plan(
            {"total_expense": 100_000_00, "pending_review": 0},
            [
                {"level": "主类", "main_category": "可优化消费", "amount_cents": 20_000_00},
                {"level": "子类", "main_category": "可优化消费", "sub_category": "外卖即时零售", "amount_cents": 12_000_00},
            ],
            [],
        )
        focus = {item["focus_area"]: item for item in plan}
        self.assertIn("可优化消费", focus)
        self.assertGreater(focus["可优化消费"]["estimated_saving_cents"], 0)
        self.assertLess(focus["可优化消费"]["suggested_cap_cents"], focus["可优化消费"]["current_amount_cents"])

    def test_budget_pressure_radar_prioritizes_over_budget_items(self):
        rows = build_budget_pressure_radar(
            {"total_expense": 100_000_00, "pending_review": 5_000_00},
            [
                {"level": "主类", "main_category": "可优化消费", "amount_cents": 12_000_00},
                {"level": "子类", "main_category": "可优化消费", "sub_category": "低复购购物", "amount_cents": 8_000_00},
                {"level": "主类", "main_category": "社交家庭", "amount_cents": 4_000_00},
            ],
            [{"risk_tag": "长期扣费", "amount_cents": 3_000_00}],
        )
        by_dimension = {item["dimension"]: item for item in rows}
        self.assertEqual(by_dimension["大额待复核"]["priority"], "P0")
        self.assertEqual(by_dimension["可优化消费"]["status"], "超压")
        self.assertGreater(by_dimension["低复购购物"]["pressure_score"], 100)


if __name__ == "__main__":
    unittest.main()
