import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import pandas as pd
from quantlab.analysis import default_sentiment_universe
from quantlab.strategies import save_strategy_order

from quantlab.app.dashboard import (
    backtest_result_judgements,
    buy_and_hold_metrics,
    command_center_next_actions,
    daily_runbook_items,
    parameter_scan_term_rows,
    quick_actions,
    readiness_summary,
    single_backtest_steps,
    usage_guide_sections,
)
from quantlab.app.streamlit_app import (
    HOTSPOT_MAX_DISPLAY_SNAPSHOTS,
    INTERVAL_OPTIONS,
    STRATEGY_OPTIONS,
    TERM_HELP,
    VIEW_OPTIONS,
    apply_research_chart_ux,
    _auto_refresh_component_html,
    _countdown_component_html,
    _market_feel_answer_feedback,
    _market_feel_return_interval_options,
    _escape_html,
    _display_holdings_frame,
    _sentiment_payloads,
    _payloads_to_sentiment_instruments,
    _holding_sentiment_options,
    _side_cell_style,
    _safe_heartbeat_url,
    _sentiment_instruments_from_selection,
    _sentiment_option_label,
    _sentiment_symbol_for_provider,
    _custom_scan_strategy_factory,
    built_in_strategy_options,
    clean_scan_param_grid,
    default_parameter_grid_text,
    english_name_from_chinese,
    fetch_sentiment_rows,
    hotspot_quick_preflight,
    hotspot_workbench_profile,
    hotspot_evidence_gate_rows,
    hotspot_timeline_frame,
    hotspot_timeline_state,
    indicator_warmup_start,
    infer_custom_strategy_profile,
    limit_hotspot_instruments,
    parameter_grid_run_count,
    parameter_scan_preflight,
    metric_comparison_rows,
    parse_parameter_grid_text,
    parameter_heatmap_frame,
    research_chart_config,
    resolve_hotspot_snapshot,
    sentiment_evidence_gate_rows,
    sentiment_distribution_frame,
    strategy_comparison_return_frame,
    strategy_comparison_rows,
    strategy_target_return_frame,
    term_badge,
    top_experiment_runs_frame,
    trade_marker_style,
    strategy_id_from_names,
    go,
)


class AppDashboardTests(unittest.TestCase):
    def test_navigation_order_matches_daily_research_workflow(self):
        self.assertEqual(
            list(VIEW_OPTIONS.values()),
            ["总控驾驶舱", "Token ROI", "现金流", "政策雷达", "消费守卫", "单标的回测", "情绪分析", "热点分析", "盘感训练", "持仓", "报告中心", "行研报告", "研究总线", "大数据模拟", "个人画像", "参数扫描", "组合轮动", "数据中心", "策略库"],
        )
        self.assertNotIn("策略审批", VIEW_OPTIONS.values())
        self.assertNotIn("使用指导", VIEW_OPTIONS.values())

    def test_market_feel_training_feedback_scores_three_levels(self):
        row = {"actual_direction": "上涨", "actual_return_interval": "2.00%至5.00%", "actual_return": 0.031}

        beginner = _market_feel_answer_feedback(row, "入门", "上涨", "", None, 12.0, 20)
        medium = _market_feel_answer_feedback(row, "中等", "上涨", "2.00%至5.00%", None, 30.0, 35)
        expert = _market_feel_answer_feedback(row, "专家", "上涨", "2.00%至5.00%", 3.0, 40.0, 60)

        self.assertTrue(beginner["passed"])
        self.assertTrue(medium["passed"])
        self.assertTrue(expert["passed"])
        self.assertGreaterEqual(expert["score"], 95.0)

    def test_market_feel_return_interval_options_cover_negative_and_positive_ranges(self):
        options = _market_feel_return_interval_options()

        self.assertEqual(options[0], "-5.00%以下")
        self.assertEqual(options[-1], "5.00%以上")
        self.assertIn("0.00%至2.00%", options)

    def test_quick_actions_cover_daily_workflow(self):
        actions = quick_actions()
        targets = {action.target_en for action in actions}

        self.assertEqual(len(actions), 11)
        self.assertIn("Executive Command Center", targets)
        self.assertIn("Company CashFlow Command", targets)
        self.assertIn("Policy Intelligence Radar", targets)
        self.assertIn("Consumption Guard", targets)
        self.assertIn("Single Backtest", targets)
        self.assertIn("Sentiment Analysis", targets)
        self.assertIn("Market Hotspots", targets)
        self.assertIn("Technical Market Feel", targets)
        self.assertIn("Holdings", targets)
        self.assertIn("Report Center", targets)
        self.assertIn("Big Data Simulation", targets)
        for action in actions:
            self.assertTrue(action.title_cn)
            self.assertTrue(action.title_en)
            self.assertTrue(action.description_cn)
            self.assertTrue(action.description_en)

    def test_command_center_next_actions_prioritizes_router_without_running_workflows(self):
        payload = {
            "command_status": "NeedsReview",
            "action_queue": [
                {
                    "priority": "P0",
                    "status": "Open",
                    "owner": "EVA_OS",
                    "action": "复跑总集成审计并处理 Review/Fail 项。",
                    "source": "Integration Audit",
                },
                {
                    "priority": "P1",
                    "status": "Open",
                    "owner": "QuantLab",
                    "action": "生成正式 Word 报告。",
                    "source": "Report Evidence",
                },
            ],
        }

        router = command_center_next_actions(payload)
        rows = router["rows"]
        view_keys = {row["view"] for row in rows}

        self.assertEqual(router["schema"], "EVAOSCommandCenterActionRouterV1")
        self.assertEqual(router["status"], "Blocked")
        self.assertEqual(rows[0]["优先级"], "P0")
        self.assertEqual(rows[0]["view"], "command")
        self.assertIn("hotspots", view_keys)
        self.assertIn("scan", view_keys)
        self.assertIn("reports", view_keys)
        self.assertTrue(all(row["view"] in VIEW_OPTIONS for row in rows))
        self.assertIn("does not scan reports, load market data, run backtests", router["token_policy"])
        self.assertIn("no browser automation", router["safety_boundary"])

    def test_hotspot_workbench_default_limits_expensive_runs(self):
        fast = hotspot_workbench_profile("快速预览")
        full = hotspot_workbench_profile("完整复盘")

        self.assertLess(fast["max_snapshots"], full["max_snapshots"])
        self.assertEqual(full["max_snapshots"], HOTSPOT_MAX_DISPLAY_SNAPSHOTS)
        self.assertLessEqual(fast["object_limit"], 12)
        self.assertIn("热点工作台模式", TERM_HELP)
        self.assertIn("52ETF公开参考", TERM_HELP)

    def test_hotspot_quick_preflight_guides_before_expensive_generation(self):
        ready = hotspot_quick_preflight(
            workbench_mode="快速预览",
            requested_count=11,
            active_count=11,
            skipped_count=0,
            max_snapshots=96,
            request_cache_status={"state": "miss"},
            directory_summary={"file_count": 0, "total_kb": 0.0},
            data_source="Sample",
            interval="60min",
        )
        hit = hotspot_quick_preflight(
            workbench_mode="快速预览",
            requested_count=11,
            active_count=11,
            skipped_count=0,
            max_snapshots=96,
            request_cache_status={"state": "hit", "remaining_seconds": 1200},
            directory_summary={"file_count": 1, "total_kb": 12.5},
            data_source="Sample",
            interval="60min",
        )
        large = hotspot_quick_preflight(
            workbench_mode="完整复盘",
            requested_count=60,
            active_count=60,
            skipped_count=0,
            max_snapshots=720,
            request_cache_status={"state": "miss"},
            directory_summary={"file_count": 0, "total_kb": 0.0},
            data_source="Sample",
            interval="60min",
        )
        missing = hotspot_quick_preflight(
            workbench_mode="快速预览",
            requested_count=0,
            active_count=0,
            skipped_count=0,
            max_snapshots=96,
            request_cache_status={"state": "miss"},
            directory_summary={"file_count": 0, "total_kb": 0.0},
            data_source="Sample",
            interval="60min",
        )

        self.assertEqual(ready["status"], "Ready")
        self.assertEqual(ready["expected_provider_requests"], 11)
        self.assertEqual(hit["status"], "CacheHit")
        self.assertEqual(hit["expected_provider_requests"], 0)
        self.assertEqual(large["status"], "LargeRun")
        self.assertEqual(missing["status"], "NeedsInput")
        self.assertIn("does not load market bars", ready["token_policy"])

    def test_research_chart_config_enables_tradingview_like_interaction(self):
        config = research_chart_config("eva_os_test_chart")

        self.assertFalse(config["displaylogo"])
        self.assertTrue(config["scrollZoom"])
        self.assertTrue(config["responsive"])
        self.assertEqual(config["toImageButtonOptions"]["filename"], "eva_os_test_chart")
        self.assertIn("lasso2d", config["modeBarButtonsToRemove"])

    def test_apply_research_chart_ux_sets_crosshair_and_rangeslider(self):
        if go is None:
            self.skipTest("plotly is not installed")
        fig = go.Figure()

        apply_research_chart_ux(fig, height=320, x_range_slider=True, x_range_selector=True)
        layout = fig.to_dict()["layout"]

        self.assertEqual(layout["height"], 320)
        self.assertEqual(layout["hovermode"], "x unified")
        self.assertEqual(layout["dragmode"], "pan")
        self.assertTrue(layout["xaxis"]["showspikes"])
        self.assertTrue(layout["xaxis"]["rangeslider"]["visible"])
        self.assertEqual(layout["xaxis"]["rangeselector"]["buttons"][-1]["label"], "全部")
        self.assertTrue(layout["yaxis"]["showspikes"])

    def test_hotspot_instrument_limit_keeps_first_items_and_reports_skipped(self):
        instruments = default_sentiment_universe("US")[:5]

        limited, skipped = limit_hotspot_instruments(instruments, 3)

        self.assertEqual([item.symbol for item in limited], [item.symbol for item in instruments[:3]])
        self.assertEqual(skipped, 2)

    def test_readiness_summary_prioritizes_review_items(self):
        cn, en = readiness_summary(pass_count=6, review_count=1, info_count=2)

        self.assertIn("Review", cn)
        self.assertIn("Review", en)

    def test_readiness_summary_allows_info_only_state(self):
        cn, en = readiness_summary(pass_count=6, review_count=0, info_count=3)

        self.assertIn("核心环境可用", cn)
        self.assertIn("Core environment is ready", en)

    def test_single_backtest_steps_cover_simple_workflow(self):
        steps = single_backtest_steps()
        cn_titles = [step.step_cn for step in steps]
        en_titles = [step.step_en for step in steps]

        self.assertEqual(len(steps), 4)
        self.assertEqual(cn_titles, ["选择数据", "选择策略", "运行回测", "复核风险"])
        self.assertEqual(en_titles, ["Choose Data", "Choose Strategy", "Run Backtest", "Review Risk"])
        for step in steps:
            self.assertTrue(step.detail_cn)
            self.assertTrue(step.detail_en)

    def test_single_backtest_interval_options_cover_minute_to_year(self):
        self.assertEqual(
            list(INTERVAL_OPTIONS),
            ["1min", "5min", "15min", "30min", "60min", "1d", "1w", "1m", "1q", "1y"],
        )

    def test_alipay_strategy_is_available_in_single_backtest(self):
        self.assertIn("追跌杀涨", STRATEGY_OPTIONS)
        self.assertIn("追跌杀涨增强", STRATEGY_OPTIONS)

    def test_single_backtest_strategy_options_follow_strategy_library_order(self):
        with TemporaryDirectory() as tmp:
            order_path = Path(tmp) / "StrategyOrder.json"
            save_strategy_order(["alipay_enhanced", "ma_crossover"], path=order_path)

            ordered_options = built_in_strategy_options(order_path=order_path)

            self.assertEqual(list(ordered_options)[0], "追跌杀涨增强")
            self.assertEqual(list(ordered_options)[1], "均线交叉 MA")

    def test_daily_runbook_covers_personal_daily_research_flow(self):
        items = daily_runbook_items()
        phases_cn = [item.phase_cn for item in items]
        phases_en = [item.phase_en for item in items]

        self.assertEqual(len(items), 4)
        self.assertEqual(phases_cn, ["启动前", "首次运行", "真实数据", "研究决策"])
        self.assertEqual(phases_en, ["Before Start", "First Run", "Real Data", "Research Decision"])
        self.assertTrue(any("Polygon" in item.action_en for item in items))
        self.assertTrue(any("风险闸门" in item.pass_rule_cn for item in items))
        for item in items:
            self.assertTrue(item.action_cn)
            self.assertTrue(item.action_en)
            self.assertTrue(item.pass_rule_cn)
            self.assertTrue(item.pass_rule_en)

    def test_usage_guide_sections_cover_all_workspace_areas(self):
        sections = usage_guide_sections()

        self.assertEqual([section.title for section in sections], list(VIEW_OPTIONS.values()))
        for section in sections:
            self.assertTrue(section.purpose)
            self.assertTrue(section.best_for)
            self.assertGreaterEqual(len(section.steps), 5)
            self.assertGreaterEqual(len(section.checks), 3)
            self.assertGreaterEqual(len(section.outputs), 3)
            self.assertGreaterEqual(len(section.risks), 2)
            self.assertIn(section.target_key, VIEW_OPTIONS)

    def test_countdown_and_hourly_refresh_components_auto_tick(self):
        countdown = _countdown_component_html("abc123", 100.0, 30)
        refresh = _auto_refresh_component_html(3600)

        self.assertIn("setInterval", countdown)
        self.assertIn("Date.now()", countdown)
        self.assertIn("自动倒计时", countdown)
        self.assertIn('role="timer"', countdown)
        self.assertIn("已超时", countdown)
        self.assertIn("window.parent.location.reload()", refresh)
        self.assertIn('role="timer"', refresh)
        self.assertIn("1 小时缓存刷新规则", refresh)
        self.assertIn("3600", refresh)

    def test_term_help_covers_training_sentiment_and_hotspot_controls(self):
        for term in [
            "训练难度",
            "判断周期",
            "收益区间判断",
            "偏热比例",
            "偏冷比例",
            "时间切片",
            "热点状态",
            "分析范围",
            "证据闸门",
            "热点证据闸门",
            "数据覆盖率",
            "刷新粒度",
            "热度集中度",
            "热点运行摘要",
            "52ETF热点对照",
            "自定义时间查看",
            "研究观察",
            "指标预热窗口",
            "展示窗口",
            "样本点",
            "失败率",
            "数据新鲜度",
            "情绪集中度",
        ]:
            self.assertIn(term, TERM_HELP)
            self.assertGreater(len(TERM_HELP[term]), 20)

    def test_indicator_warmup_start_separates_calculation_and_display_windows(self):
        display_start = pd.Timestamp("2026-06-01")

        daily_start = indicator_warmup_start(display_start, "1d")
        hourly_start = indicator_warmup_start(display_start, "60min")

        self.assertEqual((display_start - daily_start).days, 260)
        self.assertEqual((display_start - hourly_start).days, 120)
        self.assertLess(hourly_start, display_start)

    def test_sentiment_fetch_warmup_is_anchored_to_end_date(self):
        captured_starts: list[str] = []

        class FakeProvider:
            def get_bars(self, request):
                captured_starts.append(request.start)
                index = pd.date_range("2025-01-01", periods=90, freq="B")
                close = pd.Series(range(100, 190), dtype=float)
                return pd.DataFrame(
                    {
                        "datetime": index,
                        "symbol": request.symbol,
                        "market": request.market,
                        "open": close,
                        "high": close * 1.01,
                        "low": close * 0.99,
                        "close": close,
                        "volume": 100000,
                    }
                )

        end = pd.Timestamp("2026-06-30")
        expected_start = indicator_warmup_start(end, "1d").date().isoformat()
        instrument = default_sentiment_universe("US")[0]
        with patch("quantlab.app.streamlit_app.make_provider", return_value=FakeProvider()):
            rows, errors = fetch_sentiment_rows("Fake", "US", [instrument], pd.Timestamp("2026-06-01"), end)

        self.assertFalse(rows.empty)
        self.assertEqual(errors, [])
        self.assertEqual(captured_starts, [expected_start])

    def test_removed_standalone_approval_and_usage_views_do_not_reappear(self):
        source = Path("src/quantlab/app/streamlit_app.py").read_text(encoding="utf-8")

        self.assertNotIn("def strategy_approval_view", source)
        self.assertNotIn("def usage_guide_view", source)
        self.assertNotIn('st.subheader("策略审批")', source)
        self.assertNotIn('st.subheader("使用指导")', source)

    def test_sentiment_distribution_frame_covers_state_mix(self):
        rows = pd.DataFrame(
            [
                {"sentiment_state": "偏热", "sentiment_score": 70},
                {"sentiment_state": "偏热", "sentiment_score": 80},
                {"sentiment_state": "偏冷", "sentiment_score": 35},
            ]
        )

        distribution = sentiment_distribution_frame(rows)

        hot = distribution[distribution["情绪状态"].eq("偏热")].iloc[0]
        cold = distribution[distribution["情绪状态"].eq("偏冷")].iloc[0]
        self.assertEqual(int(hot["对象数量"]), 2)
        self.assertAlmostEqual(float(hot["平均情绪分"]), 75.0)
        self.assertAlmostEqual(float(cold["占比"]), 1 / 3)

    def test_sentiment_evidence_gate_rows_flag_sample_and_failure_risk(self):
        rows = pd.DataFrame(
            [
                {"sentiment_score": 80, "sentiment_state": "过热", "latest_date": "2026-06-05", "data_points": 45},
                {"sentiment_score": 78, "sentiment_state": "偏热", "latest_date": "2026-06-05", "data_points": 45},
            ]
        )

        gate = sentiment_evidence_gate_rows(rows, [{"代码": "BAD", "错误": "missing"}], "Sample")
        status_by_check = {row["检查项"]: row["状态"] for row in gate}

        self.assertEqual(status_by_check["数据源"], "Review")
        self.assertEqual(status_by_check["对象覆盖"], "Review")
        self.assertEqual(status_by_check["失败率"], "Review")
        self.assertEqual(status_by_check["样本长度"], "Review")
        self.assertEqual(status_by_check["情绪集中度"], "Review")

    def test_hotspot_timeline_frame_sorts_and_counts_strength(self):
        history = pd.DataFrame(
            [
                {"snapshot_time": "2026-01-01T11:30:00", "symbol": "A", "heat_score": 80, "hotspot_state": "强势扩散"},
                {"snapshot_time": "2026-01-01T10:30:00", "symbol": "A", "heat_score": 30, "hotspot_state": "局部偏弱"},
                {"snapshot_time": "2026-01-01T11:30:00", "symbol": "B", "heat_score": 50, "hotspot_state": "中性轮动"},
            ]
        )

        timeline = hotspot_timeline_frame(history)

        self.assertEqual(list(timeline["snapshot_time"]), ["2026-01-01T10:30:00", "2026-01-01T11:30:00"])
        self.assertEqual(int(timeline.iloc[0]["偏弱对象"]), 1)
        self.assertEqual(int(timeline.iloc[1]["偏强对象"]), 1)
        self.assertAlmostEqual(float(timeline.iloc[1]["平均热度"]), 65.0)

    def test_hotspot_snapshot_resolver_and_state_support_custom_time_review(self):
        options = [
            "2026-01-01T10:30:00",
            "2026-01-01T11:30:00",
            "2026-01-01T12:30:00",
        ]
        timeline = pd.DataFrame(
            [
                {"snapshot_time": options[0], "平均热度": 50.0, "偏强对象": 1, "偏弱对象": 0, "对象数量": 3},
                {"snapshot_time": options[1], "平均热度": 56.0, "偏强对象": 2, "偏弱对象": 0, "对象数量": 3},
            ]
        )

        self.assertEqual(resolve_hotspot_snapshot(options, "11:30"), options[1])
        self.assertEqual(resolve_hotspot_snapshot(options, "2026-01-01 12:00"), options[1])
        self.assertEqual(hotspot_timeline_state(timeline)["状态"], "热点扩散")

    def test_hotspot_evidence_gate_rows_are_strict_for_research_use(self):
        history = pd.DataFrame(
            [
                {
                    "snapshot_time": "2026-06-05T10:30:00",
                    "symbol": "A",
                    "heat_score": 82,
                    "hotspot_state": "强势扩散",
                    "data_points": 45,
                },
                {
                    "snapshot_time": "2026-06-05T11:30:00",
                    "symbol": "A",
                    "heat_score": 85,
                    "hotspot_state": "强势扩散",
                    "data_points": 45,
                },
                {
                    "snapshot_time": "2026-06-05T10:30:00",
                    "symbol": "B",
                    "heat_score": 74,
                    "hotspot_state": "局部偏强",
                    "data_points": 45,
                },
                {
                    "snapshot_time": "2026-06-05T11:30:00",
                    "symbol": "B",
                    "heat_score": 75,
                    "hotspot_state": "局部偏强",
                    "data_points": 45,
                },
                {
                    "snapshot_time": "2026-06-05T10:30:00",
                    "symbol": "C",
                    "heat_score": 52,
                    "hotspot_state": "中性轮动",
                    "data_points": 45,
                },
                {
                    "snapshot_time": "2026-06-05T11:30:00",
                    "symbol": "C",
                    "heat_score": 54,
                    "hotspot_state": "中性轮动",
                    "data_points": 45,
                },
            ]
        )

        rows = hotspot_evidence_gate_rows(history, [{"代码": "BAD", "错误": "missing"}], "Sample", "60min")
        status_by_check = {row["检查项"]: row["状态"] for row in rows}

        self.assertEqual(status_by_check["数据源"], "Review")
        self.assertEqual(status_by_check["数据覆盖率"], "Review")
        self.assertEqual(status_by_check["失败率"], "Review")
        self.assertEqual(status_by_check["样本长度"], "Review")
        self.assertEqual(status_by_check["时间切片"], "Block")
        self.assertEqual(status_by_check["刷新粒度"], "Pass")
        self.assertIn(status_by_check["热度集中度"], {"Pass", "Review"})

    def test_term_badge_uses_native_hover_title(self):
        badge = term_badge("时间切片")

        self.assertIn("ql-term-inline", badge)
        self.assertIn("title=", badge)
        self.assertIn("时间切片", badge)

    def test_sentiment_payload_roundtrip_is_cache_safe(self):
        instruments = default_sentiment_universe("US")[:2]
        payloads = _sentiment_payloads(instruments)
        restored = _payloads_to_sentiment_instruments(payloads)

        self.assertIsInstance(payloads, tuple)
        self.assertEqual([item.symbol for item in restored], [item.symbol for item in instruments])

    def test_buy_and_hold_metrics_and_result_judgements(self):
        data = pd.DataFrame({"close": [100.0, 110.0, 121.0]})
        buy_hold = buy_and_hold_metrics(data, annualization=252)
        metrics = {
            "total_return": 0.30,
            "annualized_return": 0.20,
            "max_drawdown": -0.10,
            "cost_total": 100.0,
            "ending_equity": 130000.0,
        }
        judgements = backtest_result_judgements(metrics, buy_hold)

        self.assertAlmostEqual(buy_hold["buy_hold_total_return"], 0.21)
        self.assertIn("buy_hold_sharpe", buy_hold)
        self.assertLess(buy_hold["buy_hold_max_drawdown"], 0.001)
        self.assertEqual(len(judgements), 3)
        self.assertEqual(judgements[0].status, "Pass")
        self.assertEqual(judgements[1].status, "Review")
        self.assertEqual(judgements[2].status, "Pass")

    def test_metric_comparison_rows_include_relative_values_and_win_rate_definition_scope(self):
        rows = metric_comparison_rows(
            {
                "total_return": 0.30,
                "annualized_return": 0.20,
                "sharpe": 1.50,
                "max_drawdown": -0.10,
                "win_rate": 0.60,
                "trade_count": 12,
                "buy_count": 7,
                "sell_count": 5,
                "cost_total": 123.45,
            },
            {
                "buy_hold_total_return": 0.21,
                "buy_hold_annualized_return": 0.12,
                "buy_hold_sharpe": 0.90,
                "buy_hold_max_drawdown": -0.25,
            },
        )

        self.assertEqual(rows[0]["相对"], "9.00%")
        self.assertEqual(rows[2]["相对"], "0.60")
        self.assertEqual(rows[3]["相对"], "15.00%")
        self.assertEqual(rows[4]["买入持有"], "不适用")
        self.assertEqual(rows[6]["指标"], "买入次数")
        self.assertEqual(rows[6]["策略"], "7")
        self.assertEqual(rows[7]["指标"], "卖出次数")
        self.assertEqual(rows[7]["策略"], "5")

    def test_strategy_comparison_rows_compare_two_strategies_and_buy_hold(self):
        rows = strategy_comparison_rows(
            {"total_return": 0.30, "annualized_return": 0.18, "sharpe": 1.2, "max_drawdown": -0.08, "buy_count": 4, "sell_count": 2},
            {"total_return": 0.22, "annualized_return": 0.12, "sharpe": 0.9, "max_drawdown": -0.15, "buy_count": 6, "sell_count": 3},
            {
                "buy_hold_total_return": 0.20,
                "buy_hold_annualized_return": 0.10,
                "buy_hold_sharpe": 0.7,
                "buy_hold_max_drawdown": -0.20,
            },
        )

        self.assertEqual(rows[0]["策略一"], "30.00%")
        self.assertEqual(rows[0]["策略二"], "22.00%")
        self.assertEqual(rows[0]["策略一相对买入持有"], "10.00%")
        self.assertEqual(rows[0]["策略二相对买入持有"], "2.00%")
        self.assertEqual(rows[3]["策略一减策略二"], "7.00%")
        self.assertEqual(rows[6]["策略一减策略二"], "-2")

    def test_strategy_target_return_frame_adds_relative_return(self):
        data = pd.DataFrame(
            {
                "datetime": pd.date_range("2024-01-01", periods=3, freq="D"),
                "close": [100.0, 110.0, 105.0],
            }
        )
        result = type(
            "Result",
            (),
            {
                "equity_curve": pd.DataFrame(
                    {
                        "datetime": pd.date_range("2024-01-01", periods=3, freq="D"),
                        "equity": [100000.0, 108000.0, 112000.0],
                    }
                )
            },
        )()

        frame = strategy_target_return_frame(data, result)

        self.assertIn("relative_return", frame.columns)
        self.assertAlmostEqual(frame.loc[1, "relative_return"], -0.02)
        self.assertAlmostEqual(frame.loc[2, "relative_return"], 0.07)

    def test_holdings_display_hides_source_path_and_adds_holding_return_rate(self):
        holdings = pd.DataFrame(
            [
                {
                    "source_system": "支付宝持仓账本",
                    "source_file": "/private/path/current_positions.csv",
                    "symbol": "510300",
                    "name": "沪深300ETF",
                    "market": "CN",
                    "quantity": 100,
                    "cost_basis": 10000,
                    "position_value": 11000,
                    "unrealized_pnl": 1000,
                    "weight": 1.0,
                    "updated_at": "2026-06-05",
                    "source_modified_time": "2026-06-05",
                }
            ]
        )

        display = _display_holdings_frame(holdings)

        self.assertNotIn("来源文件", display.columns)
        self.assertNotIn("来源修改时间", display.columns)
        self.assertIn("持有收益", display.columns)
        self.assertIn("持有收益率", display.columns)
        self.assertEqual(display.iloc[0]["持有收益"], "1,000.00")
        self.assertEqual(display.iloc[0]["持有收益率"], "10.00%")

    def test_sentiment_selection_combines_market_holdings_and_custom_symbols(self):
        market_options = {_sentiment_option_label(item): item for item in default_sentiment_universe("CN")}
        holdings = pd.DataFrame(
            [
                {"symbol": "510300", "name": "沪深300ETF", "market": "CN", "position_value": 12000, "weight": 0.75},
                {"symbol": "AAPL", "name": "Apple", "market": "US", "position_value": 4000, "weight": 0.25},
            ]
        )
        holding_options = {_sentiment_option_label(item, include_weight=True): item for item in _holding_sentiment_options(holdings, "CN")}

        instruments = _sentiment_instruments_from_selection(
            market="CN",
            market_options=market_options,
            selected_market_labels=list(market_options)[:2],
            holding_options=holding_options,
            selected_holding_labels=list(holding_options)[:1],
            custom_symbols="518880 510300",
        )

        symbols = [item.symbol for item in instruments]
        self.assertIn("000001", symbols)
        self.assertIn("510300", symbols)
        self.assertIn("518880", symbols)
        self.assertEqual(symbols.count("510300"), 1)

    def test_holding_sentiment_options_use_proxy_when_holding_symbol_is_missing(self):
        holdings = pd.DataFrame(
            [
                {
                    "symbol": "",
                    "name": "国泰黄金ETF联接A",
                    "market": "CN",
                    "position_value": 12000,
                    "weight": 1.0,
                }
            ]
        )

        instruments = _holding_sentiment_options(holdings, "CN")

        self.assertEqual(len(instruments), 1)
        self.assertEqual(instruments[0].symbol, "518880")
        self.assertEqual(instruments[0].role, "持仓代理")
        self.assertEqual(getattr(instruments[0], "holding_name"), "国泰黄金ETF联接A")

    def test_strategy_comparison_return_frame_adds_relative_paths(self):
        data = pd.DataFrame(
            {
                "datetime": pd.date_range("2024-01-01", periods=3, freq="D"),
                "close": [100.0, 110.0, 120.0],
            }
        )
        result_a = type(
            "ResultA",
            (),
            {"equity_curve": pd.DataFrame({"datetime": pd.date_range("2024-01-01", periods=3, freq="D"), "equity": [100000.0, 105000.0, 125000.0]})},
        )()
        result_b = type(
            "ResultB",
            (),
            {"equity_curve": pd.DataFrame({"datetime": pd.date_range("2024-01-01", periods=3, freq="D"), "equity": [100000.0, 108000.0, 115000.0]})},
        )()

        frame = strategy_comparison_return_frame(data, result_a, result_b)

        self.assertIn("strategy_a_relative_return", frame.columns)
        self.assertIn("strategy_b_relative_return", frame.columns)
        self.assertAlmostEqual(frame.loc[2, "strategy_a_minus_b_return"], 0.10)

    def test_parameter_scan_visual_frames_support_heatmaps_and_top_runs(self):
        summary = pd.DataFrame(
            {
                "run_id": ["a", "b", "c", "d"],
                "param_short_window": [5, 5, 10, 10],
                "param_long_window": [30, 60, 30, 60],
                "total_return": [0.10, 0.12, -0.02, 0.05],
                "sharpe": [1.0, 1.2, -0.1, 0.6],
                "max_drawdown": [-0.05, -0.08, -0.20, -0.10],
            }
        )

        heatmap = parameter_heatmap_frame(summary, "sharpe")
        top = top_experiment_runs_frame(summary, n=2)

        self.assertEqual(heatmap.loc[30, 5], 1.0)
        self.assertEqual(heatmap.loc[60, 10], 0.6)
        self.assertEqual(len(top), 2)
        self.assertIn("run_label", top.columns)

    def test_parameter_scan_grid_text_parses_and_filters_ma_constraints(self):
        grid = parse_parameter_grid_text("short_window=10,20\nlong_window=30,60\n# ignored\n")
        cleaned = clean_scan_param_grid("ma_crossover", grid)

        self.assertEqual(cleaned["short_window"], [10, 20])
        self.assertEqual(cleaned["long_window"], [30, 60])
        self.assertEqual(parameter_grid_run_count(cleaned), 4)

    def test_parameter_scan_preflight_blocks_bad_or_expensive_runs(self):
        ready = parameter_scan_preflight(
            strategy_id="ma_crossover",
            strategy_kind="built_in",
            param_grid={"short_window": [10, 20], "long_window": [60, 90]},
            max_runs=36,
            symbol_valid=True,
            data_source="Sample",
            interval="1d",
        )
        too_many = parameter_scan_preflight(
            strategy_id="ma_crossover",
            strategy_kind="built_in",
            param_grid={"a": list(range(10)), "b": list(range(10))},
            max_runs=36,
            symbol_valid=True,
            data_source="Sample",
            interval="1d",
        )
        invalid = parameter_scan_preflight(
            strategy_id="ma_crossover",
            strategy_kind="built_in",
            param_grid={},
            max_runs=36,
            symbol_valid=True,
            grid_error="参数网格不能为空。",
            data_source="Sample",
            interval="1d",
        )
        blocked = parameter_scan_preflight(
            strategy_id="ma_crossover",
            strategy_kind="built_in",
            param_grid={"short_window": [10], "long_window": [60]},
            max_runs=36,
            symbol_valid=False,
            data_source="Sample",
            interval="1d",
        )

        self.assertEqual(ready["schema"], "EVAOSParameterScanPreflightV1")
        self.assertEqual(ready["status"], "Ready")
        self.assertEqual(ready["run_count"], 4)
        self.assertEqual(too_many["status"], "TooMany")
        self.assertEqual(invalid["status"], "InvalidGrid")
        self.assertEqual(blocked["status"], "Blocked")
        self.assertIn("does not load market bars", ready["token_policy"])

    def test_default_parameter_grid_supports_custom_strategy_spec(self):
        spec = type(
            "Spec",
            (),
            {
                "strategy_id": "custom_demo",
                "settings": {"rsi": {"window": 14, "entry": 30.0}},
                "to_dict": lambda self: {
                    "strategy_id": "custom_demo",
                    "version": "0.1.0",
                    "display_name": "自定义演示",
                    "display_name_en": "Custom Demo",
                    "logic_key": "mean_reversion",
                    "indicator_keys": ["rsi"],
                    "settings": {"rsi": {"window": 14, "entry": 30.0}},
                    "category": "均值回归",
                    "return_source": "行为偏差",
                    "return_source_en": "Behavioral Bias",
                    "thesis": "短期过度偏离后可能回归。",
                    "thesis_en": "Short-term dislocation may revert.",
                    "failure": "单边趋势可能失效。",
                    "failure_en": "One-way trends may invalidate it.",
                    "parameter_notes": "RSI 入场。",
                    "parameter_notes_en": "RSI entry.",
                },
            },
        )()

        text = default_parameter_grid_text({"kind": "custom", "spec": spec})

        self.assertIn("weight=0.50,0.75,1.00", text)
        self.assertIn("rsi.window", text)

    def test_custom_scan_strategy_factory_overrides_nested_settings(self):
        spec_payload = {
            "strategy_id": "custom_demo",
            "version": "0.1.0",
            "display_name": "自定义演示",
            "display_name_en": "Custom Demo",
            "logic_key": "mean_reversion",
            "indicator_keys": ["rsi"],
            "settings": {"rsi": {"window": 14, "entry": 30.0, "exit": 55.0}},
            "category": "均值回归",
            "return_source": "行为偏差",
            "return_source_en": "Behavioral Bias",
            "thesis": "短期过度偏离后可能回归。",
            "thesis_en": "Short-term dislocation may revert.",
            "failure": "单边趋势可能失效。",
            "failure_en": "One-way trends may invalidate it.",
            "parameter_notes": "RSI 入场。",
            "parameter_notes_en": "RSI entry.",
        }

        factory = _custom_scan_strategy_factory(type("Spec", (), {"strategy_id": "custom_demo", "to_dict": lambda self: spec_payload})())
        strategy = factory(weight=0.75, **{"rsi.window": 10, "rsi.entry": 25.0})

        self.assertEqual(strategy.weight, 0.75)
        self.assertEqual(strategy.spec.settings["rsi"]["window"], 10)
        self.assertEqual(strategy.spec.settings["rsi"]["entry"], 25.0)

    def test_parameter_scan_terms_cover_core_concepts(self):
        rows = parameter_scan_term_rows()
        terms = {row["术语"] for row in rows}

        self.assertGreaterEqual(len(rows), 18)
        for required in ["参数扫描", "热力图", "Sharpe", "最大回撤", "Train-Test 验证", "Walk-Forward 验证", "过拟合", "交易摩擦"]:
            self.assertIn(required, terms)
        for row in rows:
            self.assertTrue(row["解释"])
            self.assertTrue(row["使用方法"])
            self.assertTrue(row["风险提示"])

    def test_buy_and_hold_max_drawdown_sorts_by_datetime(self):
        data = pd.DataFrame(
            {
                "datetime": ["2024-01-03", "2024-01-01", "2024-01-02"],
                "close": [80.0, 100.0, 120.0],
            }
        )

        buy_hold = buy_and_hold_metrics(data, annualization=252)

        self.assertAlmostEqual(buy_hold["buy_hold_total_return"], -0.20)
        self.assertAlmostEqual(buy_hold["buy_hold_max_drawdown"], -1 / 3)

    def test_drawdown_judgement_compares_strategy_with_buy_hold(self):
        metrics = {
            "total_return": 0.10,
            "annualized_return": 0.08,
            "max_drawdown": -0.10,
            "cost_total": 100.0,
            "ending_equity": 110000.0,
        }
        buy_hold = {
            "buy_hold_total_return": 0.05,
            "buy_hold_annualized_return": 0.04,
            "buy_hold_max_drawdown": -0.20,
        }

        judgements = backtest_result_judgements(metrics, buy_hold)

        self.assertEqual(judgements[1].title_cn, "相对买入持有回撤")
        self.assertIn("策略最大回撤相比买入持有最大回撤为", judgements[1].detail_cn)

    def test_trade_side_cell_style_uses_requested_colors(self):
        self.assertIn("#991b1b", _side_cell_style("BUY"))
        self.assertIn("#166534", _side_cell_style("SELL"))
        self.assertEqual(_side_cell_style("HOLD"), "")

    def test_trade_marker_style_uses_lightweight_non_triangle_marks(self):
        buy = trade_marker_style("BUY")
        sell = trade_marker_style("SELL")

        self.assertEqual(buy["symbol"], "circle-open")
        self.assertEqual(sell["symbol"], "x-thin")
        self.assertNotIn("triangle", str(buy["symbol"]).lower())
        self.assertNotIn("triangle", str(sell["symbol"]).lower())
        self.assertLessEqual(int(buy["size"]), 8)
        self.assertLessEqual(int(sell["size"]), 8)

    def test_sentiment_html_and_heartbeat_inputs_are_sanitized(self):
        self.assertEqual(_escape_html("<script>alert(1)</script>"), "&lt;script&gt;alert(1)&lt;/script&gt;")
        self.assertEqual(_safe_heartbeat_url("https://example.com/heartbeat"), "")
        self.assertEqual(_safe_heartbeat_url("http://127.0.0.1:9501/heartbeat"), "http://127.0.0.1:9501/heartbeat")

    def test_cn_sentiment_symbol_mapping_uses_index_and_etf_overrides(self):
        self.assertEqual(_sentiment_symbol_for_provider("000001", "CN", "Yahoo Finance"), "000001.SS")
        self.assertEqual(_sentiment_symbol_for_provider("399006", "CN", "Yahoo Finance"), "399006.SZ")
        self.assertEqual(_sentiment_symbol_for_provider("510300", "CN", "Yahoo Finance"), "510300.SS")
        self.assertEqual(_sentiment_symbol_for_provider("600519.SH", "CN", "Yahoo Finance"), "600519.SS")

    def test_custom_strategy_name_and_profile_inference(self):
        english_name = english_name_from_chinese("自定义均值回归策略")
        strategy_id = strategy_id_from_names("自定义均值回归策略", english_name)
        inferred = infer_custom_strategy_profile(
            "mean_reversion",
            ["rsi", "bollinger", "atr_risk"],
            {"rsi": {"window": 14}, "bollinger": {"window": 20}, "atr_risk": {"window": 14}},
        )

        self.assertEqual(english_name, "Custom Mean Reversion Strategy")
        self.assertEqual(strategy_id, "custom_mean_reversion_strategy")
        self.assertIn("均值回归", inferred["category"])
        self.assertIn("行为偏差", inferred["return_source"])
        self.assertIn("执行优势", inferred["return_source"])
        self.assertIn("参数", inferred["parameter_notes"])


if __name__ == "__main__":
    unittest.main()
