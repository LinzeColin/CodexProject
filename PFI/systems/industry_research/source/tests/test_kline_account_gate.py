from __future__ import annotations

import unittest

from src.reporting.charts import _final_action, _indicator_action
from src.reporting.kline_report import _counter_conclusion, _operation_for_evidence_status


class KlineAccountGateTest(unittest.TestCase):
    def test_account_pending_buy_never_returns_executable_kline_rule(self) -> None:
        final_action, operation_rule = _final_action(
            "账户待更新-买入候选",
            total_score=5,
            quality="High",
            volume_score=1,
            boll_position=0.5,
        )

        self.assertEqual(final_action, "账户待更新-买入不执行")
        self.assertIn("Volume=0", operation_rule)
        self.assertIn("不执行", _indicator_action("账户待更新-买入候选", 1))

    def test_account_pending_sell_never_returns_executable_kline_rule(self) -> None:
        final_action, operation_rule = _final_action(
            "账户待更新-卖出候选",
            total_score=-2,
            quality="Medium",
            volume_score=0,
            boll_position=0.9,
        )

        self.assertEqual(final_action, "账户待更新-卖出不执行")
        self.assertIn("Volume=0", operation_rule)
        row = {"Position": "账户待更新-卖出候选", "quality": "High"}
        self.assertIn("当前卖出动作暂停", _counter_conclusion(row))
        self.assertIn("Volume为0", _operation_for_evidence_status(row, "NeedsMoreEvidence"))


if __name__ == "__main__":
    unittest.main()
