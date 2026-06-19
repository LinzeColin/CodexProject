from __future__ import annotations

import tempfile
import unittest
import json
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from src.cli import _due_report_rows, _validate_weekly_session_date
from src.reporting.analysis import _decision_operation_conclusion, _weekly_operation_strategy
from src.reporting.naming import daily_report_name, kline_report_name, weekly_report_name
from src.reporting.paths import pdf_path
from src.reporting.quality_gate import (
    _policy_bridge_issues,
    _source_log_issues,
    allowed_week_pdf_names,
    expected_week_reports,
    pdf_page_count,
    quality_issues_for_content,
    week_report_status,
)


class ReportQualityGateTest(unittest.TestCase):
    def test_allows_explicit_buy_sell_but_rejects_legacy_sell_or_avoid(self) -> None:
        content = self._base_daily_content() + "\n建议买入 测试标的\n建议卖出 测试标的"
        self.assertFalse(any("Forbidden phrase found: 建议买入" in issue for issue in quality_issues_for_content(content, "pre_open")))
        content += "\nsell_or_avoid"
        issues = quality_issues_for_content(content, "pre_open")
        self.assertTrue(any("Forbidden phrase found: sell_or_avoid" in issue for issue in issues))

    def test_rejects_vague_review_language(self) -> None:
        issues = quality_issues_for_content(self._base_daily_content() + "\n尾盘复核后再说", "pre_open")
        self.assertTrue(any("Forbidden phrase found: 复核" in issue for issue in issues))

    def test_rejects_legacy_account_overview_layout_terms(self) -> None:
        content = self._base_daily_content() + "\n## 账户总体信息\n旧账户段落\n## 账户 Dashboard\n旧图表段落"
        issues = quality_issues_for_content(content, "pre_open")
        self.assertTrue(any("Forbidden phrase found: 账户总体信息" in issue for issue in issues))
        self.assertTrue(any("Forbidden phrase found: 账户 Dashboard" in issue for issue in issues))

    def test_rejects_policy_event_volume_ceiling_language(self) -> None:
        content = (
            self._base_daily_content()
            + "\n操作影响：农业/周期 买入类信号可保留原Volume上限；若量价背离则降到50%。"
        )
        issues = quality_issues_for_content(content, "pre_open")
        self.assertTrue(any("Forbidden phrase found: 可保留原Volume上限" in issue for issue in issues))

    def test_rejects_kline_needs_more_evidence_half_volume_language(self) -> None:
        content = self._base_daily_content() + "\n买入降额到50% Volume；样本不满足则取消买入。"
        issues = quality_issues_for_content(content, "kline")
        self.assertTrue(any("Forbidden phrase found: 买入降额到50% Volume" in issue for issue in issues))

    def test_rejects_ambiguous_partial_execution_language(self) -> None:
        content = self._base_daily_content() + "\n买入按Volume上限；卖出减半；买入降额。"
        issues = quality_issues_for_content(content, "pre_open")
        self.assertTrue(any("Forbidden phrase found: 按Volume上限" in issue for issue in issues))
        self.assertTrue(any("Forbidden phrase found: 卖出减半" in issue for issue in issues))
        self.assertTrue(any("Forbidden phrase found: 买入降额" in issue for issue in issues))

    def test_caps_confidence_when_pfi_os_needs_more_evidence(self) -> None:
        content = self._base_daily_content().replace(
            "| 测试ETF | 测试主题 | 0.700 | Medium Confidence Research | 完整 | 验证通过-可继续研究 | PFIOS风险闸门通过 |",
            "| 测试ETF | 测试主题 | 0.700 | High Confidence Research | 完整 | 证据不足-禁止执行买入 | PFIOS风险闸门未通过 |",
        )
        issues = quality_issues_for_content(content, "pre_open")
        self.assertTrue(any("Research confidence exceeds PFIOS cap" in issue for issue in issues))
        self.assertTrue(any("cannot support nonzero buy Volume" in issue for issue in issues))

    def test_rejects_raw_pfi_os_internal_status_in_report_body(self) -> None:
        content = self._base_daily_content().replace("验证通过-可继续研究", "NeedsMoreEvidence", 1)
        issues = quality_issues_for_content(content, "pre_open")
        self.assertTrue(any("Forbidden phrase found: NeedsMoreEvidence" in issue for issue in issues))

    def test_complete_daily_content_passes_content_quality_gate(self) -> None:
        self.assertEqual(quality_issues_for_content(self._base_daily_content(), "pre_open"), [])

    def test_report_body_rejects_source_list_section(self) -> None:
        issues = quality_issues_for_content(self._base_daily_content() + "\n## 来源清单\n- 测试来源", "pre_open")
        self.assertTrue(any("source list" in issue for issue in issues))

    def test_report_body_rejects_internal_local_paths_outside_images(self) -> None:
        content = self._base_daily_content() + "\n政策报告路径：/Users/example/LocalResearch/data/report_artifacts/policy/report.json"
        issues = quality_issues_for_content(content, "pre_open")

        self.assertTrue(any("leaks internal macOS user path" in issue for issue in issues))

    def test_report_body_rejects_internal_local_urls_outside_images(self) -> None:
        content = self._base_daily_content() + "\n来源链路：local://policy/status-only"
        issues = quality_issues_for_content(content, "pre_open")

        self.assertTrue(any("leaks internal local URL" in issue for issue in issues))

    def test_report_body_allows_image_artifact_paths_for_rendering(self) -> None:
        content = self._base_daily_content() + "\n![补充图](/Users/example/LocalResearch/data/report_artifacts/_images/chart.png)"
        issues = quality_issues_for_content(content, "pre_open")

        self.assertFalse(any("leaks internal" in issue for issue in issues))

    def test_core_action_table_rejects_zero_holding_background_rows(self) -> None:
        content = self._base_daily_content().replace(
            "| 测试ETF | 建议买入-下跌承接 | 4.000% | 60.000% | 中：可观察但需尾盘确认 | 400.00 | 1000.00 | -3.000% | 10.000% | 0.00 | -2.000% | 14:30-14:55 Australia/Sydney | 明确结论：买入候选保留；账户、PFIOS和尾盘量价通过后重算Volume | 跌幅项0.150%、亏损项0.350%、低仓项1.500%、放量扣减0.000%、目标/风险上限5.000%。 | 下跌承接 | 放量下跌 |",
            "| 上证指数 | 观望-指数背景 | 0.000% | 20.000% | 低：证据不足 | 0.00 | 0.00 | 0.000% | 0.000% | 0.00 | -0.200% | 14:30-14:55 Australia/Sydney | 观望 | Volume=0；无可执行仓位幅度。 | 指数背景 | 观察 |",
        )
        issues = quality_issues_for_content(content, "pre_open")

        self.assertTrue(any("zero-holding background row" in issue for issue in issues))

    def test_core_action_table_requires_persuasive_composite_fields(self) -> None:
        content = self._base_daily_content().replace(" | 说服力 |", " |", 1)
        issues = quality_issues_for_content(content, "pre_open")

        self.assertTrue(any("Core action table missing persuasive/composite field: 说服力" in issue for issue in issues))

    def test_core_action_table_requires_substantive_volume_basis(self) -> None:
        content = self._base_daily_content().replace(
            "跌幅项0.150%、亏损项0.350%、低仓项1.500%、放量扣减0.000%、目标/风险上限5.000%。",
            "按系统规则计算。",
        )
        issues = quality_issues_for_content(content, "pre_open")

        self.assertTrue(any("Volume basis is too weak" in issue for issue in issues))

    def test_core_action_table_volume_basis_requires_numeric_percentages(self) -> None:
        content = self._base_daily_content().replace(
            "跌幅项0.150%、亏损项0.350%、低仓项1.500%、放量扣减0.000%、目标/风险上限5.000%。",
            "跌幅项、亏损项、低仓项、放量扣减、目标/风险上限均已考虑。",
        )
        issues = quality_issues_for_content(content, "pre_open")

        self.assertTrue(any("Volume basis lacks numeric percentages" in issue for issue in issues))

    def test_signal_quality_matrix_must_live_in_research_confidence_section(self) -> None:
        content = self._base_daily_content().replace(
            "## 二、盘前 / 盘中 / 盘后对比复盘",
            "### 信号质量矩阵\n| Name | Position |\n| --- | --- |\n| 测试ETF | Medium |\n## 二、盘前 / 盘中 / 盘后对比复盘",
            1,
        )
        issues = quality_issues_for_content(content, "pre_open")

        self.assertTrue(any("Signal quality matrix must be moved into the research confidence section" in issue for issue in issues))

    def test_signal_quality_matrix_rejects_original_volume_for_non_executable_positions(self) -> None:
        content = self._base_daily_content().replace(
            "| 测试ETF | 建议买入-下跌承接 | Medium | 趋势区间结论：下跌承接可观察 | 动能结论：中性 | VOL结论：成交量确认 | 两类信号可用 | 需要尾盘止跌 | 明确结论：证据不足时不买；账户、PFIOS和尾盘量价同时通过后重算候选Volume |",
            "| 测试ETF | 账户待更新-买入候选 | Medium | 趋势区间结论：下跌承接可观察 | 动能结论：中性 | VOL结论：成交量确认 | 两类信号可用但仍有缺口：尾盘价格、成交额、事件方向满足则执行原Volume；任一不满足则降到50%或取消。 | 需要尾盘止跌 | 明确结论：等待账户确认；当前买入动作取消为可执行项，Volume 0 |",
        )
        issues = quality_issues_for_content(content, "pre_open")

        self.assertTrue(any("Signal matrix conflicts" in issue for issue in issues))

    def test_signal_quality_matrix_rejects_original_volume_cap_for_non_executable_positions(self) -> None:
        content = self._base_daily_content().replace(
            "| 测试ETF | 建议买入-下跌承接 | Medium | 趋势区间结论：下跌承接可观察 | 动能结论：中性 | VOL结论：成交量确认 | 两类信号可用 | 需要尾盘止跌 | 明确结论：证据不足时不买；账户、PFIOS和尾盘量价同时通过后重算候选Volume |",
            "| 测试ETF | 账户待更新-买入候选 | Medium | 趋势区间结论：下跌承接可观察 | 动能结论：中性 | VOL结论：一般确认，保持原Volume上限。 | 账户闸门未通过：技术信号只保留研究方向，不执行原Volume；更新支付宝流水/持仓并重生成后重算。 | 需要尾盘止跌 | 明确结论：等待账户确认；当前买入动作取消为可执行项，Volume 0 |",
        )
        issues = quality_issues_for_content(content, "pre_open")

        self.assertTrue(any("volume confirmation conflicts" in issue for issue in issues))

    def test_core_action_table_rejects_long_basis_or_risk_cells(self) -> None:
        long_text = "过长说明" * 60
        content = self._base_daily_content().replace("下跌承接 | 放量下跌 |", f"{long_text} | 放量下跌 |")
        issues = quality_issues_for_content(content, "pre_open")

        self.assertTrue(any("cell is too long" in issue for issue in issues))

    def test_source_log_quality_requires_artifact_and_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "missing_sources.json"
            with patch("src.reporting.quality_gate.source_log_path", return_value=path):
                issues = _source_log_issues("1. 05062026_盘前报告")

        self.assertTrue(any("Missing source log artifact" in issue for issue in issues))

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "report_sources.json"
            path.write_text(json.dumps({"report_name": "1. 05062026_盘前报告", "sources": [{"source_name": "Moomoo"}]}), encoding="utf-8")
            with patch("src.reporting.quality_gate.source_log_path", return_value=path):
                issues = _source_log_issues("1. 05062026_盘前报告")

        self.assertTrue(any("missing source_url" in issue for issue in issues))

    def test_source_log_quality_accepts_valid_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "report_sources.json"
            path.write_text(
                json.dumps(
                    {
                        "report_name": "1. 05062026_盘前报告",
                        "sources": [
                            {
                                "source_name": "Moomoo OpenD",
                                "source_url": "opend://127.0.0.1",
                                "fetch_time": "2026-06-05T08:40:00+10:00",
                                "data_version": "opend_snapshot_v1",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            with patch("src.reporting.quality_gate.source_log_path", return_value=path):
                issues = _source_log_issues("1. 05062026_盘前报告")

        self.assertEqual(issues, [])

    def test_weekly_report_rejects_raw_only_market_table(self) -> None:
        content = self._base_weekly_content() + "\n| 代码 | 名称 | 研究分组 | 价格 | 涨跌幅 | 成交额 |\n| --- | --- | --- | --- | --- | --- |\n"
        issues = quality_issues_for_content(content, "monday_pre_open")
        self.assertTrue(any("raw-only price/change/turnover" in issue for issue in issues))

    def test_weekly_report_rejects_symbol_level_market_table_without_composite_judgement(self) -> None:
        content = self._base_weekly_content() + """

| Name | 收盘价 | 涨跌幅 | 成交额 | 来源 |
| --- | --- | --- | --- | --- |
| 测试ETF | 1.000 | 2.000% | 1000000 | 测试 |
"""
        issues = quality_issues_for_content(content, "friday_post_close")
        self.assertTrue(any("standalone symbol-level market table" in issue for issue in issues))

    def test_daily_report_rejects_symbol_level_market_source_table_without_decision_context(self) -> None:
        content = self._base_daily_content() + """

| Name | 收盘价 | 涨跌幅 | 成交额 | 来源 |
| --- | --- | --- | --- | --- |
| 测试ETF | 1.000 | 2.000% | 1000000 | 测试 |
"""
        issues = quality_issues_for_content(content, "pre_open")
        self.assertTrue(any("Daily report contains a standalone symbol-level market/source table" in issue for issue in issues))

    def test_weekly_report_allows_sector_object_table_when_composite_section_exists(self) -> None:
        issues = quality_issues_for_content(self._base_weekly_content(), "monday_pre_open")
        self.assertFalse(any("standalone symbol-level market table" in issue for issue in issues))

    def test_weekly_report_rejects_simplified_event_table_without_source_verification(self) -> None:
        content = self._base_weekly_content() + """

| 事件时间（含年月日/来源当地时间） | 类型 | 标题 | 影响 | 来源 |
| --- | --- | --- | --- | --- |
| 2026-06-04 09:00 Asia/Shanghai | news | 测试新闻 | 正面 | 测试源 |
"""
        issues = quality_issues_for_content(content, "friday_post_close")
        self.assertTrue(any("low-value simplified event table" in issue for issue in issues))

    def test_market_structure_requires_four_axis_bubble_explanation(self) -> None:
        content = self._base_daily_content().replace("顶部横轴=左侧下跌承接/风险释放、右侧上涨兑现/趋势延续，", "")
        issues = quality_issues_for_content(content, "pre_open")
        self.assertTrue(any("Market structure chart explanation missing: 顶部横轴=" in issue for issue in issues))

    def test_market_structure_requires_readable_heatmap_background(self) -> None:
        content = self._base_daily_content().replace("热力图使用浅色背景和深色文字", "热力图使用高饱和背景")
        issues = quality_issues_for_content(content, "pre_open")

        self.assertTrue(any("Market structure chart explanation missing: 浅色背景" in issue for issue in issues))

    def test_event_catalyst_requires_original_source_chain(self) -> None:
        content = self._base_daily_content().replace("原文核验", "来源状态")
        issues = quality_issues_for_content(content, "pre_open")
        self.assertTrue(any("Event catalyst source chain missing: 原文核验" in issue for issue in issues))

    def test_event_catalyst_requires_policy_crawler_chain(self) -> None:
        content = self._base_daily_content().replace("独立爬虫", "外部任务")
        issues = quality_issues_for_content(content, "pre_open")
        self.assertTrue(any("Event catalyst source chain missing: 独立爬虫" in issue for issue in issues))

    def test_event_catalyst_rejects_local_paths_in_report_body(self) -> None:
        content = self._base_daily_content().replace("独立爬虫请求已记录。", "独立爬虫请求 /tmp/request.json。")
        issues = quality_issues_for_content(content, "pre_open")
        self.assertTrue(any("must not expose local file paths" in issue for issue in issues))

    def test_event_catalyst_rejects_stale_policy_noise(self) -> None:
        content = self._base_daily_content().replace("政府文件解读系统未命中高相关新政策", "国务院办公厅关于印发十四五现代物流发展规划的通知")
        issues = quality_issues_for_content(content, "pre_open")
        self.assertTrue(any("stale or low-relevance policy document" in issue for issue in issues))

    def test_event_catalyst_time_requires_full_date_and_timezone(self) -> None:
        content = self._base_daily_content().replace("2026-06-04 00:00 Asia/Shanghai", "00:00")
        issues = quality_issues_for_content(content, "pre_open")

        self.assertTrue(any("time missing full date" in issue for issue in issues))
        self.assertTrue(any("time missing timezone marker" in issue for issue in issues))

    def test_event_catalyst_time_requires_timezone_even_with_full_date(self) -> None:
        content = self._base_daily_content().replace("2026-06-04 00:00 Asia/Shanghai", "2026-06-04 00:00")
        issues = quality_issues_for_content(content, "pre_open")

        self.assertTrue(any("time missing timezone marker" in issue for issue in issues))

    def test_event_catalyst_empty_placeholder_does_not_require_time(self) -> None:
        content = self._base_daily_content().replace(
            "| 2026-06-04 00:00 Asia/Shanghai | government_policy_bridge | 测试主题 | 政府文件解读系统未命中高相关新政策 | 中性 | Medium | 政府文件解读系统 | 政府文件解读系统未返回原文URL；原文抓取状态 no_match；误读风险：高；不提高买入权重。 | 政府文件解读系统：db_cached；原文核验=未通过；原文抓取状态=no_match；误读风险=高；独立爬虫请求已记录。 | 继续抓取政策、公告、新闻和行情 | 不扩大买入 |",
            "|  | 暂无 |  | 暂无新增催化剂或风险事件 |  | Insufficient Evidence | 暂无官方源 | 未形成原文核验链路 | 无新增事件链路 | 下一轮自动抓取 | 不扩大买入 |",
        )
        issues = quality_issues_for_content(content, "pre_open")

        self.assertFalse(any("Event catalyst time missing" in issue for issue in issues))

    def test_requires_fact_inference_opinion_subsections(self) -> None:
        content = self._base_daily_content().replace("### 推论\n- 主题强弱需要成交额验证。\n", "")
        issues = quality_issues_for_content(content, "pre_open")
        self.assertTrue(any("Fact/inference/opinion layer missing: 推论" in issue for issue in issues))

    def test_requires_substantive_counter_thesis(self) -> None:
        content = self._base_daily_content().replace(
            "| 测试ETF | 买入假设可能错在把趋势下跌误判为低吸。 | 14:30-14:55 Australia/Sydney 检查尾盘样本。 | 期望跌幅收窄。 | 尾盘继续放量下跌 | 结论：买入可保留。 | 若反方触发：取消买入。 |",
            "| 测试ETF | 暂无 | 暂无 | 暂无 | 暂无 | 暂无 | 暂无 |",
        )
        issues = quality_issues_for_content(content, "pre_open")
        self.assertTrue(any("Counter-thesis table lacks substantive counter arguments" in issue for issue in issues))

    def test_requires_holding_discipline_core_items(self) -> None:
        content = self._base_daily_content().replace("| 情绪化追涨/补跌 | 需检查 | 单日涨跌触发必须经过反方和PFIOS验证 |", "")
        issues = quality_issues_for_content(content, "pre_open")
        self.assertTrue(any("Holding discipline check missing item: 情绪化" in issue for issue in issues))

    def test_daily_report_requires_close_execution_rule_checklist(self) -> None:
        content = self._base_daily_content().replace("## 七、收盘执行规则与风控", "## 七、旧执行依据")
        issues = quality_issues_for_content(content, "midday")
        self.assertTrue(any("Required section missing: 收盘执行规则与风控" in issue for issue in issues))

    def test_daily_report_rejects_old_raw_execution_evidence_table(self) -> None:
        content = self._base_daily_content() + """

| 排序 | 代码 | 名称 | 涨跌幅 | 成交额 | 数据来源 | Position | 执行价值 | 风险触发 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | TEST | 测试ETF | 2.000% | 1000000 | 测试 | 观察 | 低 | 无 |
"""
        issues = quality_issues_for_content(content, "post_close")
        self.assertTrue(any("low-value duplicate/raw table" in issue for issue in issues))

    def test_alipay_blocked_report_rejects_active_nonzero_buy_row(self) -> None:
        content = self._base_daily_content() + "\n- 执行金额闸门阻断：今日支付宝流水/持仓未更新或未确认。"
        issues = quality_issues_for_content(content, "pre_open")

        self.assertTrue(any("Alipay execution is blocked" in issue for issue in issues))
        self.assertTrue(any("must have Volume 0" in issue for issue in issues))
        self.assertTrue(any("must have suggested amount 0" in issue for issue in issues))

    def test_alipay_account_pending_report_accepts_zeroed_buy_row(self) -> None:
        content = (
            self._base_daily_content()
            .replace("建议买入-下跌承接", "账户待更新-买入候选")
            .replace("4.000%", "0.000%")
            .replace("400.00", "0.00")
            + "\n- 执行金额闸门阻断：今日支付宝流水/持仓未更新或未确认；本次可执行金额设为0。"
        )
        issues = quality_issues_for_content(content, "pre_open")

        self.assertFalse(any("Alipay" in issue for issue in issues))

    def test_alipay_account_pending_position_always_requires_zero_volume(self) -> None:
        content = self._base_daily_content().replace("建议买入-下跌承接", "账户待更新-买入候选")
        issues = quality_issues_for_content(content, "pre_open")

        self.assertTrue(any("must have Volume 0" in issue for issue in issues))

    def test_pfi_os_blocked_rejects_nonzero_buy_volume_and_buy_downsize_final_rule(self) -> None:
        content = (
            self._base_daily_content()
            .replace("Medium Confidence Research | 完整 | 验证通过-可继续研究 | PFIOS风险闸门通过", "Watch Only | 完整 | 证据不足-禁止执行买入 | PFIOS风险闸门未通过")
            .replace("| 测试ETF | 验证通过-可继续研究 | TEST | 可用历史样本 260 条 | 成本 | 100000次 | 全流程2次 | 通过 | 证据链完整 | 保留研究 | 验证通过 |", "| 测试ETF | 证据不足-禁止执行买入 | TEST | 可用历史样本 60 条 | 成本 | 100000次 | 全流程2次 | 阻断 | 需要尾盘止跌 | 买入降额 | 验证不足 |")
            .replace("| 测试ETF | 建议买入-下跌承接 | 14:30-14:55 Australia/Sydney | 账户闸门通过 | Medium | 尾盘止跌且无负面事件 | 取消买入 | 需要尾盘止跌 | 通过 | 明确结论：买入候选保留；账户、PFIOS和尾盘量价通过后重算Volume |", "| 测试ETF | 建议买入-下跌承接 | 14:30-14:55 Australia/Sydney | 账户闸门通过 | Medium | 尾盘止跌且无负面事件 | 取消买入 | 需要尾盘止跌 | 阻断 | 明确结论：买入降额 |")
        )
        issues = quality_issues_for_content(content, "pre_open")

        self.assertTrue(any("cannot support nonzero buy Volume" in issue for issue in issues))
        self.assertTrue(any("must end in cancel/watch/wait" in issue for issue in issues))

    def test_account_pending_buy_operation_conclusion_cancels_executable_action(self) -> None:
        text = _decision_operation_conclusion(
            {"Position": "账户待更新-买入候选"},
            {"daily_change_pct": -0.02, "turnover": 1_000_000},
            "NeedsMoreEvidence",
        )

        self.assertIn("等待账户确认", text)
        self.assertIn("Volume 0", text)
        self.assertNotIn("再买入", text)

    def test_weekly_account_pending_buy_strategy_cancels_executable_action(self) -> None:
        text = _weekly_operation_strategy(
            {"Position": "账户待更新-买入候选"},
            {"daily_change_pct": -0.02, "turnover": 1_000_000},
            60,
            0.5,
            {"validation_status": "NeedsMoreEvidence", "risk_gate": "Blocked"},
        )

        self.assertIn("等待账户确认", text)
        self.assertIn("取消", text)
        self.assertIn("Volume=0", text)
        self.assertNotIn("再决定是否买入", text)

    def test_report_quality_policy_bridge_requires_confirmed_refresh(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            status_dir = root / "status"
            event_dir = root / "events"
            status_dir.mkdir()
            event_dir.mkdir()
            (status_dir / "policy_bridge_status_2026-06-04.json").write_text(
                '{"refresh":{"status":"timeout"},"matched_event_count":1}',
                encoding="utf-8",
            )
            (event_dir / "policy_events_2026-06-04.csv").write_text(
                "\n".join(
                    [
                        "date,type,policy_match_basis,source_url,policy_original_fetch_status,policy_request_path,policy_operation_impact,policy_report_path",
                        "2026-06-04,government_policy_bridge,theme_match,https://www.gov.cn/policy.html,verified,/tmp/request.json,操作影响：观察,/tmp/report.pdf",
                    ]
                ),
                encoding="utf-8",
            )
            with patch("src.reporting.quality_gate.POLICY_STATUS_DIR", status_dir), patch(
                "src.reporting.quality_gate.POLICY_EVENT_DIR", event_dir
            ):
                issues = _policy_bridge_issues("2026-06-04", "pre_open", self._base_daily_content())

        self.assertTrue(any("Policy bridge refresh is not confirmed" in issue for issue in issues))
        self.assertTrue(any("Report includes government policy bridge text" in issue for issue in issues))

    def test_report_quality_policy_bridge_requires_original_source_for_matched_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            status_dir = root / "status"
            event_dir = root / "events"
            status_dir.mkdir()
            event_dir.mkdir()
            (status_dir / "policy_bridge_status_2026-06-04.json").write_text(
                '{"refresh":{"status":"refreshed"},"matched_event_count":1}',
                encoding="utf-8",
            )
            (event_dir / "policy_events_2026-06-04.csv").write_text(
                "\n".join(
                    [
                        "date,type,policy_match_basis,source_url,policy_original_fetch_status,policy_request_path,policy_operation_impact,policy_report_path",
                        "2026-06-04,government_policy_bridge,theme_match,local://status-only,missing,/tmp/request.json,操作影响：观察,/tmp/report.pdf",
                    ]
                ),
                encoding="utf-8",
            )
            with patch("src.reporting.quality_gate.POLICY_STATUS_DIR", status_dir), patch(
                "src.reporting.quality_gate.POLICY_EVENT_DIR", event_dir
            ):
                issues = _policy_bridge_issues("2026-06-04", "monday_pre_open", self._base_weekly_content())

        self.assertTrue(any("lack original government/news/source URL" in issue for issue in issues))

    def test_report_quality_policy_bridge_requires_verified_crawler_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            status_dir = root / "status"
            event_dir = root / "events"
            status_dir.mkdir()
            event_dir.mkdir()
            (status_dir / "policy_bridge_status_2026-06-04.json").write_text(
                '{"refresh":{"status":"refreshed"},"matched_event_count":1}',
                encoding="utf-8",
            )
            (event_dir / "policy_events_2026-06-04.csv").write_text(
                "\n".join(
                    [
                        "date,type,policy_match_basis,source_url,policy_original_fetch_status,policy_request_path,policy_operation_impact,policy_report_path",
                        "2026-06-04,government_policy_bridge,theme_match,https://www.gov.cn/policy.html,missing,,,",
                    ]
                ),
                encoding="utf-8",
            )
            with patch("src.reporting.quality_gate.POLICY_STATUS_DIR", status_dir), patch(
                "src.reporting.quality_gate.POLICY_EVENT_DIR", event_dir
            ):
                issues = _policy_bridge_issues("2026-06-04", "monday_pre_open", self._base_weekly_content())

        self.assertTrue(any("verified original fetch status" in issue for issue in issues))
        self.assertTrue(any("separate crawler request path" in issue for issue in issues))
        self.assertTrue(any("operation impact analysis" in issue for issue in issues))
        self.assertTrue(any("policy system report path" in issue for issue in issues))

    def test_allowed_week_pdf_names_are_the_standard_22_reports(self) -> None:
        expected = expected_week_reports("2026-06-03")
        self.assertEqual(len(expected), 22)
        self.assertEqual(expected[0]["report_kind"], "monday_pre_open")
        self.assertEqual(expected[-1]["report_kind"], "friday_post_close")
        names = allowed_week_pdf_names("2026-06-03")
        self.assertEqual(len(names), 22)
        self.assertIn("1. 03062026_盘前报告.pdf", names)
        self.assertIn("4. 05062026_K线分析报告.pdf", names)
        self.assertIn("01062026_周一报告.pdf", names)
        self.assertIn("05062026_周五报告.pdf", names)
        self.assertNotIn("1. 盘前报告_03062026.pdf", names)
        self.assertNotIn("行业报告_半导体_2026-06-03.pdf", names)

    def test_report_naming_uses_date_before_label(self) -> None:
        self.assertEqual(daily_report_name("pre_open", "2026-06-03"), "1. 03062026_盘前报告")
        self.assertEqual(daily_report_name("midday", "2026-06-03"), "2. 03062026_盘中报告")
        self.assertEqual(daily_report_name("post_close", "2026-06-03"), "3. 03062026_盘后报告")
        self.assertEqual(kline_report_name("2026-06-03"), "4. 03062026_K线分析报告")
        self.assertEqual(weekly_report_name("monday_pre_open", "2026-06-01"), "01062026_周一报告")
        self.assertEqual(weekly_report_name("friday_post_close", "2026-06-05"), "05062026_周五报告")

    def test_pdf_path_parses_new_old_and_iso_report_dates(self) -> None:
        self.assertIn("6月第2周 0806-1406", str(pdf_path("1. 12062026_盘前报告.pdf")))
        self.assertIn("6月第1周 0106-0706", str(pdf_path("1. 盘前报告_03062026.pdf")))
        self.assertIn("6月第1周 0106-0706", str(pdf_path("行业报告_半导体_2026-06-03.pdf")))

    def test_weekly_report_dates_must_match_session(self) -> None:
        _validate_weekly_session_date("2026-06-01", "monday_pre_open")
        _validate_weekly_session_date("2026-06-05", "friday_post_close")
        with self.assertRaises(ValueError):
            _validate_weekly_session_date("2026-06-03", "monday_pre_open")
        with self.assertRaises(ValueError):
            _validate_weekly_session_date("2026-06-03", "friday_post_close")

    def test_week_report_status_distinguishes_missing_and_future(self) -> None:
        payload = week_report_status("2026-06-03", through_date="2026-06-03", run_quality=False)
        self.assertEqual(payload["expected_total"], 22)
        self.assertIn("future", payload["status_counts"])
        self.assertTrue(any(row["status"] in {"missing", "present"} for row in payload["reports"] if row["report_date"] == "2026-06-03"))
        self.assertTrue(any(row["status"].startswith("historical_") for row in payload["reports"] if row["report_date"] < "2026-06-03"))
        self.assertTrue(any(row["pdf_name"] == "05062026_周五报告.pdf" and row["status"] == "future" for row in payload["reports"]))
        historical = next(row for row in payload["reports"] if row["status"].startswith("historical_"))
        future = next(row for row in payload["reports"] if row["status"] == "future")
        self.assertEqual(historical["repair_command"], "")
        self.assertEqual(historical["next_action"], "record_only_no_backfill")
        self.assertEqual(future["repair_command"], "")
        self.assertEqual(future["next_action"], "wait_until_report_time")

    def test_week_report_status_does_not_mark_same_day_later_reports_missing(self) -> None:
        payload = week_report_status(
            "2026-06-03",
            through_date="2026-06-03",
            run_quality=False,
            now=datetime(2026, 6, 3, 12, 30),
        )
        post_close = next(row for row in payload["reports"] if row["report_date"] == "2026-06-03" and row["report_kind"] == "post_close")
        kline = next(row for row in payload["reports"] if row["report_date"] == "2026-06-03" and row["report_kind"] == "kline")
        self.assertEqual(post_close["status"], "future")
        self.assertEqual(kline["status"], "future")
        self.assertEqual(post_close["repair_command"], "")
        self.assertEqual(kline["next_action"], "wait_until_report_time")

    def test_due_report_rows_only_selects_current_missing_or_quality_fail(self) -> None:
        payload = {
            "reports": [
                {"report_date": "2026-06-03", "report_kind": "pre_open", "status": "historical_missing"},
                {"report_date": "2026-06-04", "report_kind": "pre_open", "status": "missing"},
                {"report_date": "2026-06-04", "report_kind": "midday", "status": "quality_fail"},
                {"report_date": "2026-06-04", "report_kind": "post_close", "status": "future"},
                {"report_date": "2026-06-05", "report_kind": "pre_open", "status": "missing"},
            ]
        }
        rows = _due_report_rows(payload, "2026-06-04")
        self.assertEqual([row["report_kind"] for row in rows], ["pre_open", "midday"])

    def test_kline_quality_requires_indicator_coverage(self) -> None:
        content = self._base_kline_content().replace("### KDJ 单独/组合分析\n![KDJ](/tmp/KDJ.png)", "")
        issues = quality_issues_for_content(content, "kline")
        self.assertTrue(any("K-line indicator coverage missing: KDJ" in issue for issue in issues))

    def test_kline_quality_requires_indicator_detail_table(self) -> None:
        content = self._base_kline_content().replace("| MA | 读数 | 标准 | 判断结论：测试 | 建议操作：观望 |", "| MA | 读数 |  | 判断结论：测试 | 建议操作：观望 |")
        content = content.replace("| 维度 | 当前读数 | 参考标准 | 判断结论 | 建议操作 |", "| 维度 | 当前读数 | 判断结论 | 建议操作 |", 1)
        issues = quality_issues_for_content(content, "kline")
        self.assertTrue(any("K-line indicator detail table missing for MA: 参考标准" in issue for issue in issues))

    def test_kline_quality_requires_observation_mix(self) -> None:
        content = self._base_kline_content().replace(
            "| T5 | 标的5 | 建议卖出技术候选 | 观察 | Medium | MACD柱走弱、KDJ转弱 | 等待动能修复失败 | MACD重新翻红 | 卖出候选保留 | Volume=0 |",
            "| T5 | 标的5 | 中性观望候选 | 观察 | Medium | MACD柱走弱、KDJ转弱 | 等待动能修复失败 | MACD重新翻红 | 观望 | Volume=0 |",
        )
        issues = quality_issues_for_content(content, "kline")
        self.assertTrue(any("risk-reduction observation candidates fewer than 3" in issue for issue in issues))

    def test_kline_quality_rejects_daily_market_structure_duplicates(self) -> None:
        content = self._base_kline_content() + "\n![A股板块热力图](/tmp/heatmap.png)\n### 板块对象明细\n"
        issues = quality_issues_for_content(content, "kline")
        self.assertTrue(any("must not repeat A-share heatmap" in issue for issue in issues))
        self.assertTrue(any("must not include market-structure sector object table" in issue for issue in issues))

    def test_kline_candidate_pool_rejects_watchlist_snapshot_columns(self) -> None:
        content = self._base_kline_content().replace(
            "| 代码 | 名称 | K线研究分组 | Position | 信号质量 | 核心技术证据 | 等待样本 | 失效条件 | 明确操作 | Volume闸门 |",
            "| 代码 | 名称 | K线研究分组 | 观察状态 | 持仓金额 | 持有收益金额 | 持有收益 | 待确认金额 | 现仓口径 | 涨跌幅 | 数据来源 |",
        )
        issues = quality_issues_for_content(content, "kline")
        self.assertTrue(any("watchlist/account snapshot" in issue for issue in issues))
        self.assertTrue(any("missing high-value decision header: 核心技术证据" in issue for issue in issues))

    def test_kline_candidate_pool_rejects_repeated_generic_waiting_sample(self) -> None:
        repeated = "后续2日方向选择；未突破MA20/MA60前不升级。"
        content = (
            self._base_kline_content()
            .replace("等待收盘站稳MA20", repeated)
            .replace("等待量价同步", repeated)
            .replace("等待突破区间", repeated)
        )
        issues = quality_issues_for_content(content, "kline")
        self.assertTrue(any("repeated generic waiting sample" in issue for issue in issues))

    def test_kline_action_table_requires_composite_persuasive_operation_headers(self) -> None:
        content = self._base_kline_content().replace(" | 说服力 |", " |", 1)
        issues = quality_issues_for_content(content, "kline")

        self.assertTrue(any("K-line action table missing high-value operation header: 说服力" in issue for issue in issues))

    def test_kline_quality_rejects_generic_fact_event_sections_and_source_lists(self) -> None:
        content = self._base_kline_content() + "\n## 三、关键事实、事件与市场结构\n### 来源清单\n"
        issues = quality_issues_for_content(content, "kline")
        self.assertTrue(any("generic fact/event/market-structure" in issue for issue in issues))
        self.assertTrue(any("source list" in issue for issue in issues))

    def test_kline_quality_rejects_low_density_indicator_action(self) -> None:
        content = self._base_kline_content() + "\n观望但记录强弱变化"
        issues = quality_issues_for_content(content, "kline")

        self.assertTrue(any("Forbidden phrase found: 观望但记录强弱变化" in issue for issue in issues))

    def test_daily_quality_rejects_low_density_watch_decisions(self) -> None:
        content = self._base_daily_content().replace(
            "明确结论：买入候选保留；账户、PFIOS和尾盘量价通过后重算Volume",
            "明确结论：观望；只记录强弱变化。",
        )
        issues = quality_issues_for_content(content, "pre_open")
        self.assertTrue(any("Low-density decision phrase" in issue for issue in issues))

    def test_daily_quality_accepts_watch_decisions_with_trigger_metrics(self) -> None:
        content = self._base_daily_content().replace(
            "明确结论：买入候选保留；账户、PFIOS和尾盘量价通过后重算Volume",
            "明确结论：观望；只有成交额>0、事件/PFIOS同向且触发升级条件时才进入重点观察，否则不新增买卖。",
        )
        issues = quality_issues_for_content(content, "pre_open")
        self.assertFalse(any("Low-density decision phrase" in issue for issue in issues))
        self.assertFalse(any("Watch/wait decision lacks trigger" in issue for issue in issues))

    def test_daily_quality_rejects_low_density_sector_judgement(self) -> None:
        content = self._base_daily_content().replace(
            "下跌承接观察：平均涨跌-2.000%、质量分60.000、成交额1,000,000；14:30-14:55只看止跌和成交额收敛，放量破位或负面事件出现则取消买入候选。",
            "中性观察：等待量价、事件和PFIOS同向。",
        )
        issues = quality_issues_for_content(content, "pre_open")

        self.assertTrue(any("Low-density sector judgement" in issue for issue in issues))

    def test_daily_quality_accepts_sector_judgement_with_metrics_and_actions(self) -> None:
        issues = quality_issues_for_content(self._base_daily_content(), "pre_open")

        self.assertFalse(any("Low-density sector judgement" in issue for issue in issues))
        self.assertFalse(any("Sector judgement lacks metrics" in issue for issue in issues))

    def test_pdf_page_count_counts_page_objects(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.pdf"
            path.write_bytes(b"%PDF\n/Type /Pages\n/Type /Page\n/Type /Page\n")
            self.assertEqual(pdf_page_count(path), 2)

    def _base_daily_content(self) -> str:
        return """
# 每日仓位操作报告：2026-06-03 开盘前
## 目录
- [一、仓位操作建议](#h-test)
## 一、仓位操作建议
| Name | Position | Volume | 复合质量分 | 说服力 | 建议金额 | 持仓金额 | 持有收益率 | 现仓 | 待确认金额 | 当日涨跌 | 执行窗口 | 操作结论 | Volume依据 | 依据 | 风险点 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 测试ETF | 建议买入-下跌承接 | 4.000% | 60.000% | 中：可观察但需尾盘确认 | 400.00 | 1000.00 | -3.000% | 10.000% | 0.00 | -2.000% | 14:30-14:55 Australia/Sydney | 明确结论：买入候选保留；账户、PFIOS和尾盘量价通过后重算Volume | 跌幅项0.150%、亏损项0.350%、低仓项1.500%、放量扣减0.000%、目标/风险上限5.000%。 | 下跌承接 | 放量下跌 |
## 二、盘前 / 盘中 / 盘后对比复盘
- 开盘前报告为当天计划基准。
## 三、关键事实、事件与市场结构
### 事实
- 行情和账户数据已刷新。
### 推论
- 主题强弱需要成交额验证。
    ### 观点
    - 未验证前只进入观察。
    | 时间（含年月日/来源当地时区） | 类型 | 相关主题 | 事件/催化剂 | 影响方向 | 确定性 | 可验证数据 | 原文核验 | 来源链路 | 后续指标 | 操作影响 |
    | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
    | 2026-06-04 00:00 Asia/Shanghai | government_policy_bridge | 测试主题 | 政府文件解读系统未命中高相关新政策 | 中性 | Medium | 政府文件解读系统 | 政府文件解读系统未返回原文URL；原文抓取状态 no_match；误读风险：高；不提高买入权重。 | 政府文件解读系统：db_cached；原文核验=未通过；原文抓取状态=no_match；误读风险=高；独立爬虫请求已记录。 | 继续抓取政策、公告、新闻和行情 | 不扩大买入 |
    ![A股板块热力图](/tmp/heatmap.png)
    ![A股板块气泡图](/tmp/bubble.png)
    - 图表说明：热力图使用浅色背景和深色文字，按研究分组聚合，热力图每格列出该板块下明确对象名称、平均涨跌和对象数量；气泡图底部横轴=当日涨跌幅，顶部横轴=左侧下跌承接/风险释放、右侧上涨兑现/趋势延续，左侧纵轴=复合质量分（量价、PFIOS、风险闸门、成交额），右侧纵轴=质量分区（0-40低质量、40-60观察、60+重点跟踪），气泡大小=成交额，颜色=涨跌方向（红涨绿跌），气泡标注=对象名称。
    ### 板块对象明细
    | 板块/主题 | 明确对象名称 | 平均涨跌 | 合计成交额 | 复合质量分 | 判断结论 |
    | --- | --- | --- | --- | --- | --- |
    | 测试主题 | 测试ETF(-2.000%) | -2.000% | 1000000 | 60.000 | 下跌承接观察：平均涨跌-2.000%、质量分60.000、成交额1,000,000；14:30-14:55只看止跌和成交额收敛，放量破位或负面事件出现则取消买入候选。 |
## 四、研究可信度与 PFIOS 验证
| Name | 主题 | Research Confidence Score | 研究等级 | 数据完整性 | PFIOS状态 | 已处理/待跟踪事项 |
| --- | --- | --- | --- | --- | --- | --- |
| 测试ETF | 测试主题 | 0.700 | Medium Confidence Research | 完整 | 验证通过-可继续研究 | PFIOS风险闸门通过 |
### 信号质量矩阵（并入研究可信度）
| Name | Position | 信号质量 | MA/EMA/BOLL趋势区间 | MACD/RSI/KDJ动能 | VOL确认 | 混合结论 | 还需要的证据 | 明确操作结论 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 测试ETF | 建议买入-下跌承接 | Medium | 趋势区间结论：下跌承接可观察 | 动能结论：中性 | VOL结论：成交量确认 | 两类信号可用 | 需要尾盘止跌 | 明确结论：证据不足时不买；账户、PFIOS和尾盘量价同时通过后重算候选Volume |
| Name | 验证状态 | 回测对象 | 样本区间 | 成本假设 | 模拟次数 | 重跑要求 | 风险闸门 | 还需要的证据 | 验证队列操作行为 | 验证结论 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 测试ETF | 验证通过-可继续研究 | TEST | 可用历史样本 260 条 | 成本 | 100000次 | 全流程2次 | 通过 | 证据链完整 | 保留研究 | 验证通过 |
## 五、操作纪律与反方校验
| Name | 反方观点 | 等待样本 | 期望结果 | 推翻条件 | 明确结论 | 触发后操作 |
| --- | --- | --- | --- | --- | --- | --- |
| 测试ETF | 买入假设可能错在把趋势下跌误判为低吸。 | 14:30-14:55 Australia/Sydney 检查尾盘样本。 | 期望跌幅收窄。 | 尾盘继续放量下跌 | 结论：买入可保留。 | 若反方触发：取消买入。 |
| 纪律项 | 状态 | 说明 |
| --- | --- | --- |
| 待确认订单 | 正常 | 无 |
| 现金缓冲 | 正常 | 30.000% |
| 情绪化追涨/补跌 | 需检查 | 单日涨跌触发必须经过反方和PFIOS验证 |
## 六、技术面、基本面、价值面综合结论
- 技术面、基本面和价值面均已给出结论。
## 七、收盘执行规则与风控
| Name | Position | 检查时间 | 账户闸门 | 信号质量 | 成立条件 | 不成立动作 | 证据缺口 | PFIOS闸门 | 最终规则 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 测试ETF | 建议买入-下跌承接 | 14:30-14:55 Australia/Sydney | 账户闸门通过 | Medium | 尾盘止跌且无负面事件 | 取消买入 | 需要尾盘止跌 | 通过 | 明确结论：买入候选保留；账户、PFIOS和尾盘量价通过后重算Volume |
## 八、持仓与支付宝历史交易附图
![账户关键指标](/tmp/account.png)
""".strip()

    def _base_kline_content(self) -> str:
        return """
# 自选池技术观察报告：2026-06-03
## 目录
- [一、K线操作总表](#h-test)
## 一、K线操作总表
| Name | Position | Volume | 复合质量分 | 说服力 | 操作结论 | 依据 | 风险点 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 标的1 | 建议买入-下跌承接 | 4.000% | 60.000% | 中：技术信号可训练 | 买入候选保留 | MA20企稳 | 跌破MA20取消 |
## 二、信号质量矩阵
| 代码 | 名称 | K线分组 | Position | 信号质量 | 明确操作 | 趋势分 | 动能分 | 量能分 | 总分 | 执行规则 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T1 | 标的1 | 建议买入技术候选 | 建议买入-下跌承接 | Medium | 买入候选保留 | 1 | 1 | 0 | 2 | 账户/PFIOS/尾盘量价通过后重算Volume |
## 三、训练问题答案与分析逻辑
| 代码 | 名称 | 训练题答案 | 分析逻辑/思考过程 | 等待样本 | 期望结果 | 满足时操作 | 不满足时操作 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| T1 | 标的1 | 均值回归候选 | 趋势分1，动能分1 | 等待收盘站稳MA20 | 跌幅收窄 | 维持买入 | 取消买入 |
## 四、证据缺口与操作规则
| 代码 | 名称 | 验证状态 | 还需要的证据 | 原因 | 当前操作行为 |
| --- | --- | --- | --- | --- | --- |
| T1 | 标的1 | 证据不足-禁止执行买入 | 等待收盘站稳MA20 | 风险闸门未通过 | Volume=0，补足证据后重算 |
## 五、反方情景动作矩阵
| 代码 | 名称 | 反方情景 | 验证样本 | 明确结论 | 触发后操作 |
| --- | --- | --- | --- | --- | --- |
| T1 | 标的1 | 趋势下跌误判为低吸 | 等待收盘站稳MA20 | 保留买入候选但不执行 | 取消买入 |
## 六、K线候选池与强弱结论
| 代码 | 名称 | K线研究分组 | Position | 信号质量 | 核心技术证据 | 等待样本 | 失效条件 | 明确操作 | Volume闸门 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T1 | 标的1 | 建议买入技术候选 | 观察 | Medium | MA20站稳、MACD改善、成交量确认 | 等待收盘站稳MA20 | 跌破MA20且放量 | 买入候选保留 | Volume=0 |
| T2 | 标的2 | 建议买入技术候选 | 观察 | Medium | MA20站稳、RSI健康、成交量确认 | 等待收盘站稳MA20 | 跌破MA20且放量 | 买入候选保留 | Volume=0 |
| T3 | 标的3 | 建议买入技术替代-观望 | 观察 | Low | 趋势未确认，量能不足 | 等待量价同步 | 继续缩量下跌 | 观望 | Volume=0 |
| T4 | 标的4 | 建议卖出技术候选 | 观察 | High | 接近上轨、RSI过热、量能背离 | 等待尾盘不能放量突破 | 放量突破上轨 | 卖出候选保留 | Volume=0 |
| T5 | 标的5 | 建议卖出技术候选 | 观察 | Medium | MACD柱走弱、KDJ转弱 | 等待动能修复失败 | MACD重新翻红 | 卖出候选保留 | Volume=0 |
| T6 | 标的6 | 建议卖出技术替代-观望 | 观察 | Low | 趋势仍强但过热 | 等待回落确认 | 继续突破 | 观望 | Volume=0 |
| T7 | 标的7 | 中性观望候选 | 观察 | Low | 区间震荡且量能中性 | 等待突破区间 | 假突破 | 观望 | Volume=0 |
## 七、单标的多指标深度分析
### MA 单独/组合分析
![MA](/tmp/MA.png)
| 维度 | 当前读数 | 参考标准 | 判断结论 | 建议操作 |
| --- | --- | --- | --- | --- |
| MA | 读数 | 标准 | 判断结论：测试 | 建议操作：观望 |
### EMA 单独/组合分析
![EMA](/tmp/EMA.png)
| 维度 | 当前读数 | 参考标准 | 判断结论 | 建议操作 |
| --- | --- | --- | --- | --- |
| EMA | 读数 | 标准 | 判断结论：测试 | 建议操作：观望 |
### BOLL 单独/组合分析
![BOLL](/tmp/BOLL.png)
| 维度 | 当前读数 | 参考标准 | 判断结论 | 建议操作 |
| --- | --- | --- | --- | --- |
| BOLL | 读数 | 标准 | 判断结论：测试 | 建议操作：观望 |
### MACD 单独/组合分析
![MACD](/tmp/MACD.png)
| 维度 | 当前读数 | 参考标准 | 判断结论 | 建议操作 |
| --- | --- | --- | --- | --- |
| MACD | 读数 | 标准 | 判断结论：测试 | 建议操作：观望 |
### VOL 单独/组合分析
![VOL](/tmp/VOL.png)
| 维度 | 当前读数 | 参考标准 | 判断结论 | 建议操作 |
| --- | --- | --- | --- | --- |
| VOL | 读数 | 标准 | 判断结论：测试 | 建议操作：观望 |
### RSI 单独/组合分析
![RSI](/tmp/RSI.png)
| 维度 | 当前读数 | 参考标准 | 判断结论 | 建议操作 |
| --- | --- | --- | --- | --- |
| RSI | 读数 | 标准 | 判断结论：测试 | 建议操作：观望 |
### KDJ 单独/组合分析
![KDJ](/tmp/KDJ.png)
| 维度 | 当前读数 | 参考标准 | 判断结论 | 建议操作 |
| --- | --- | --- | --- | --- |
| KDJ | 读数 | 标准 | 判断结论：测试 | 建议操作：观望 |
### MIX 单独/组合分析
混合分析
## 八、K线训练结论
- 每个训练问题均给出答案、逻辑和后续操作。
## 九、持仓与支付宝历史交易附图
![账户关键指标](/tmp/account.png)
""".strip()

    def _base_weekly_content(self) -> str:
        return self._base_daily_content().replace(
            "## 二、盘前 / 盘中 / 盘后对比复盘",
            "## 二、周度对比复盘与优化结论",
        ) + """
## 七、复合判断质量、策略胜率与风险清单
- 策略胜率代理 = 1 - PFIOS 蒙特卡洛亏损概率。
| Name | Position | 主题 | 复合质量分 | 策略胜率代理 | 概率等级 | 准确性依据 | 高概率盈利条件 | 风险闸门 | 最大回撤 | Walk-forward | 量价证据 | 事件原文核验 | 政策/事件支持 | 操作策略 | 失败动作 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 测试ETF | 建议买入-待重算 | 测试主题 | 60.000% | 55.000% | 中概率候选 | 中概率 | 尾盘止跌且事件原文无负面扩散 | Blocked | -12.000% | 3.000% | 收盘1.000 | 已核验原文 | 未命中高相关政策催化 | 证据不足时不执行买入；验证后重算候选Volume | 取消买入 |
""".strip()


if __name__ == "__main__":
    unittest.main()
