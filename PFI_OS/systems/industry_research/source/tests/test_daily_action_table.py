from __future__ import annotations

import unittest

from src.reporting.analysis import position_action_recommendations


class DailyActionTableTest(unittest.TestCase):
    def test_core_action_table_omits_zero_holding_background_rows(self) -> None:
        advice = [
            {
                "Name": "上证指数",
                "Position": "观望-指数背景",
                "Volume": 0.0,
                "holding_amount": 0.0,
                "pending_order_amount": 0.0,
                "risk_note": "指数背景。",
            },
            {
                "Name": "中证银行",
                "Position": "观望-指数背景",
                "Volume": 0.0,
                "holding_amount": 6669.88,
                "pending_order_amount": 0.0,
                "risk_note": "持仓观察。",
            },
            {
                "Name": "测试ETF",
                "Position": "账户待更新-买入候选",
                "Volume": 0.0,
                "holding_amount": 0.0,
                "pending_order_amount": 0.0,
                "risk_note": "账户待更新。",
                "entry_condition": "今日支付宝流水/持仓未更新或未确认；保留买入研究方向。原研究依据：趋势偏强但未过热，且当前持仓偏低；可按小额补足方式提高有效暴露。",
            },
        ]
        factors = [
            {"name": "上证指数", "daily_change_pct": -0.002, "source_name": "Moomoo OpenD"},
            {"name": "中证银行", "daily_change_pct": -0.011, "source_name": "Moomoo OpenD"},
            {"name": "测试ETF", "daily_change_pct": 0.005, "source_name": "Moomoo OpenD"},
        ]
        rendered = position_action_recommendations(
            "pre_open",
            advice,
            factors,
            {"total_holding_amount": 10000},
        )

        self.assertNotIn("| 上证指数 |", rendered)
        self.assertIn("| 中证银行 |", rendered)
        self.assertIn("| 测试ETF |", rendered)
        self.assertIn("复合质量分", rendered)
        self.assertIn("说服力", rendered)
        self.assertIn("操作结论", rendered)
        self.assertIn("纯背景/零持仓观望对象转入信号矩阵或市场结构", rendered)
        self.assertIn("账户未更新，Volume=0；原依据：趋势偏强", rendered)
        self.assertIn("涨跌0.500%", rendered)
        self.assertNotIn("账户缺口，执行归零", rendered)
        self.assertNotIn("更新交易明细、持仓截图或CSV", rendered)

    def test_user_tradable_index_funds_remain_core_objects_even_without_holding(self) -> None:
        advice = [
            {
                "Name": "科创50",
                "symbol": "SH.000688",
                "Position": "观望",
                "Volume": 0.0,
                "holding_amount": 0.0,
                "pending_order_amount": 0.0,
                "risk_note": "可交易对象，等待尾盘确认。",
            },
            {
                "Name": "中证银行",
                "symbol": "SZ.399986",
                "Position": "观望",
                "Volume": 0.0,
                "holding_amount": 0.0,
                "pending_order_amount": 0.0,
                "risk_note": "可交易对象，等待尾盘确认。",
            },
            {
                "Name": "上证指数",
                "symbol": "SH.000001",
                "Position": "观望-指数背景",
                "Volume": 0.0,
                "holding_amount": 0.0,
                "pending_order_amount": 0.0,
                "risk_note": "指数背景。",
            },
        ]
        factors = [
            {"name": "科创50", "symbol": "SH.000688", "daily_change_pct": -0.018, "source_name": "Moomoo OpenD"},
            {"name": "中证银行", "symbol": "SZ.399986", "daily_change_pct": 0.004, "source_name": "Moomoo OpenD"},
            {"name": "上证指数", "symbol": "SH.000001", "daily_change_pct": -0.002, "source_name": "Moomoo OpenD"},
        ]

        rendered = position_action_recommendations(
            "pre_open",
            advice,
            factors,
            {"total_holding_amount": 10000},
        )

        self.assertIn("| 科创50 |", rendered)
        self.assertIn("| 中证银行 |", rendered)
        self.assertNotIn("| 上证指数 |", rendered)


if __name__ == "__main__":
    unittest.main()
