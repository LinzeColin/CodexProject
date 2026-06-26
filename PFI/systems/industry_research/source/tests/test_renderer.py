from __future__ import annotations

import unittest

from reportlab.lib.units import mm

from src.models import Source
from src.reporting.renderer import _auto_col_widths, _desired_col_width, _position_row_style_commands, source_list


class RendererTableSizingTest(unittest.TestCase):
    def test_new_decision_columns_get_room_for_readable_text(self) -> None:
        self.assertGreaterEqual(_desired_col_width("高概率盈利条件", 80), 48 * mm)
        self.assertGreaterEqual(_desired_col_width("事件原文核验", 60), 42 * mm)
        self.assertLessEqual(_desired_col_width("概率等级", 20), 22 * mm)

    def test_auto_widths_fit_new_weekly_composite_table(self) -> None:
        rows = [
            ["Name", "Position", "复合质量分", "策略胜率代理", "概率等级", "高概率盈利条件", "事件原文核验", "操作策略", "失败动作"],
            ["测试ETF", "建议买入-降额", "60.000%", "55.000%", "中概率候选", "尾盘止跌且事件原文无负面扩散", "已核验原文", "证据不足时不执行，验证后重算Volume", "取消买入"],
        ]
        widths = _auto_col_widths(rows, 270 * mm)
        self.assertEqual(len(widths), len(rows[0]))
        self.assertLessEqual(sum(widths), 270 * mm + 0.001)

    def test_position_rows_apply_full_row_buy_red_and_sell_green_styles(self) -> None:
        rows = [
            ["Name", "Position", "Volume"],
            ["买入ETF", "建议买入-下跌承接", "0.000%"],
            ["卖出ETF", "建议卖出-上涨减仓", "2.000%"],
            ["观察ETF", "观望", "0.000%"],
        ]
        commands = _position_row_style_commands(rows)
        backgrounds = [command for command in commands if command[0] == "BACKGROUND"]

        self.assertEqual(str(backgrounds[0][3]), "Color(.972549,.843137,.854902,1)")
        self.assertEqual(backgrounds[0][1:3], ((0, 1), (-1, 1)))
        self.assertEqual(str(backgrounds[1][3]), "Color(.847059,.952941,.862745,1)")
        self.assertEqual(backgrounds[1][1:3], ((0, 2), (-1, 2)))
        self.assertEqual(len(backgrounds), 2)

    def test_source_list_keeps_details_out_of_report_body(self) -> None:
        rendered = source_list(
            [
                Source(
                    source_name="测试来源",
                    source_url="https://example.com/detail",
                    fetch_time="2026-06-06T00:00:00Z",
                    data_version="2026-06-06",
                )
            ]
        )

        self.assertIn("source log", rendered)
        self.assertNotIn("https://example.com/detail", rendered)
        self.assertNotIn("抓取时间", rendered)


if __name__ == "__main__":
    unittest.main()
