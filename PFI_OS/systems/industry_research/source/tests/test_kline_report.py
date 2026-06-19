from __future__ import annotations

import unittest

from src.reporting.charts import _select_kline_universe, _to_yahoo_symbol
from src.reporting.kline_report import _kline_action_table, _selection_summary


class KlineReportTest(unittest.TestCase):
    def test_selection_summary_uses_decision_evidence_not_watchlist_snapshot_columns(self) -> None:
        selected = [
            {
                "symbol": "T1",
                "name": "标的1",
                "kline_group": "建议买入技术候选",
            }
        ]
        advice = [
            {
                "Name": "标的1",
                "Position": "账户待更新-买入候选",
                "Volume": "0.000%",
                "suggested_amount": "0.00",
            }
        ]
        technical_rows = [
            {
                "symbol": "T1",
                "quality": "Medium",
                "evidence": "MA20站稳、MACD改善、成交量倍率1.300。",
                "sample_to_wait": "等待收盘站稳MA20且成交量不缩。",
                "if_failed_action": "取消买入，改观望。",
                "final_action": "买入降额",
            }
        ]

        rendered = _selection_summary(selected, advice, technical_rows)

        for header in ["核心技术证据", "等待样本", "失效条件", "明确操作", "Volume闸门"]:
            self.assertIn(header, rendered)
        for old_header in ["持仓金额", "持有收益", "待确认金额", "现仓口径", "涨跌幅", "数据来源"]:
            self.assertNotIn(old_header, rendered)
        self.assertIn("账户未确认：Volume=0", rendered)

    def test_kline_action_table_is_technical_not_daily_account_snapshot(self) -> None:
        rendered = _kline_action_table(
            [
                {
                    "symbol": "T1",
                    "name": "标的1",
                    "Position": "账户待更新-买入候选",
                    "quality": "Medium",
                    "total_score": 2,
                    "final_action": "账户待更新-买入不执行",
                    "evidence": "MA20站稳、MACD改善、成交量倍率1.300。",
                    "if_failed_action": "取消买入，改观望。",
                }
            ],
            [{"Name": "标的1", "Position": "账户待更新-买入候选", "Volume": 0.04}],
            "2099-01-01",
        )

        for header in ["Name", "Position", "Volume", "复合质量分", "说服力", "操作结论", "依据", "风险点"]:
            self.assertIn(header, rendered)
        for old_header in ["建议金额", "持仓金额", "持有收益率", "现仓", "待确认金额", "当日涨跌", "执行窗口"]:
            self.assertNotIn(old_header, rendered)
        self.assertIn("账户未确认", rendered)
        self.assertIn("0.000%", rendered)

    def test_user_tradable_index_enters_kline_universe_through_proxy(self) -> None:
        self.assertEqual(_to_yahoo_symbol({"symbol": "000688", "exchange": "SSE", "asset_class": "Index"}), "588090.SS")
        self.assertEqual(_to_yahoo_symbol({"symbol": "399986", "exchange": "SZSE", "asset_class": "Index"}), "512800.SS")
        self.assertEqual(_to_yahoo_symbol({"symbol": "000001", "exchange": "SSE", "asset_class": "Index"}), "")
        factors = [
            {"symbol": "000688", "name": "科创50", "exchange": "SSE", "asset_class": "Index", "daily_change_pct": -0.01},
            {"symbol": "399986", "name": "中证银行", "exchange": "SZSE", "asset_class": "Index", "daily_change_pct": 0.01},
            *[
                {"symbol": f"T{idx}", "name": f"ETF{idx}", "exchange": "US", "asset_class": "ETF", "daily_change_pct": idx / 1000}
                for idx in range(1, 6)
            ],
        ]
        advice = [
            {"Name": "科创50", "Position": "账户待更新-买入候选"},
            {"Name": "中证银行", "Position": "账户待更新-卖出候选"},
        ]

        selected = _select_kline_universe(factors, advice)
        names = {str(row.get("name")) for row in selected}

        self.assertIn("科创50", names)
        self.assertIn("中证银行", names)


if __name__ == "__main__":
    unittest.main()
