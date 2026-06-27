from __future__ import annotations

import unittest
from pathlib import Path

from pfi_v02.stage_v021_frontend_contract import (
    BASE_CURRENCY,
    STAGE4_TASK_IDS,
    build_v021_stage4_contract,
)


class V021Stage4TrendContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.html = (self.root / "web" / "index.html").read_text(encoding="utf-8")
        self.js = (self.root / "web" / "app" / "shell.js").read_text(encoding="utf-8")
        self.css = (self.root / "web" / "styles" / "tokens.css").read_text(encoding="utf-8")
        self.web_source = "\n".join((self.html, self.js, self.css))

    def test_stage4_contract_locks_unified_trend_data_for_three_pages(self) -> None:
        contract = build_v021_stage4_contract()
        trend = contract["trend_data_contract"]

        self.assertEqual(contract["schema"], "PFIV021FrontendOptimizationStage4ContractV1")
        self.assertEqual(tuple(contract["task_ids"]), STAGE4_TASK_IDS)
        self.assertEqual(trend["object_name"], "UNIFIED_TREND_DATA")
        self.assertEqual(trend["base_currency"], BASE_CURRENCY)
        self.assertEqual(trend["missing_data_state"], "趋势数据待更新")
        self.assertEqual(set(trend["required_pages"]), {"accounts", "investment", "consumption"})
        self.assertEqual(trend["required_pages"]["accounts"], ("现金", "净资产"))
        self.assertEqual(trend["required_pages"]["investment"], ("市值", "总收益", "现金仓位"))
        self.assertEqual(trend["required_pages"]["consumption"], ("支出", "预算", "现金流"))

    def test_chart_surface_has_accessible_html_markers_and_chinese_state(self) -> None:
        chart = build_v021_stage4_contract()["chart_contract"]

        for marker in chart["html_markers"]:
            self.assertIn(marker, self.html)
        self.assertIn('data-trend-canvas', self.html)
        self.assertIn('aria-label="统一趋势图"', self.html)
        self.assertIn("CNY 基准", self.html)
        self.assertIn("趋势数据待更新", self.html)
        self.assertIn(".trend-legend", self.css)
        self.assertIn(".trend-empty", self.css)

    def test_web_shell_uses_unified_trend_data_in_accounts_investment_consumption(self) -> None:
        self.assertIn("const UNIFIED_TREND_DATA", self.js)
        for workspace in ("accounts", "investment", "consumption"):
            self.assertIn(f"trend: UNIFIED_TREND_DATA.{workspace}", self.js)

        for metric in ("现金", "净资产", "市值", "总收益", "现金仓位", "支出", "预算", "现金流"):
            self.assertIn(metric, self.js)
        for series_id in (
            "cash_cny",
            "net_worth_cny",
            "market_value_cny",
            "total_return_cny",
            "cash_position_cny",
            "spend_cny",
            "budget_cny",
            "cashflow_cny",
        ):
            self.assertIn(series_id, self.js)

    def test_canvas_renderer_exposes_non_hover_reading_path(self) -> None:
        self.assertIn("function drawTrendChart", self.js)
        self.assertIn("function renderTrendLegend", self.js)
        self.assertIn("function drawTrendEndLabel", self.js)
        self.assertIn("formatTrendValue", self.js)
        self.assertIn("direct_labels", str(build_v021_stage4_contract()["chart_contract"]))
        self.assertIn("visible_without_hover", str(build_v021_stage4_contract()["chart_contract"]))

    def test_stage4_does_not_add_forbidden_product_entries_or_real_execution(self) -> None:
        forbidden = ("data-workspace=\"qbvs\"", "data-workspace=\"alpha\"", "data-action=\"trade\"", "data-action=\"pay\"", "data-action=\"broker-submit\"")
        for term in forbidden:
            self.assertNotIn(term, self.web_source)
        self.assertIn("不做实盘自动下单", self.web_source)


if __name__ == "__main__":
    unittest.main()
