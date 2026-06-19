import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from quantlab.approvals import StrategyApprovalRegistry
from quantlab.strategies import (
    DEFAULT_BUILT_IN_STRATEGY_PARAMETERS,
    RETURN_SOURCE_TAXONOMY,
    STRATEGY_PROFILES,
    DEFAULT_STRATEGY_ORDER,
    built_in_strategy_parameter_rows,
    clean_built_in_strategy_parameters,
    collect_strategy_profile_candidates,
    create_strategy_template,
    editable_strategy_profile_payload,
    evaluate_strategy_profile_candidate_quality,
    get_strategy_profile,
    get_built_in_strategy_parameters,
    load_built_in_strategy_parameter_overrides,
    load_strategy_order,
    load_strategy_profile_overrides,
    move_strategy_order_item,
    ordered_strategy_ids,
    parse_strategy_profile_candidate,
    save_strategy_order,
    save_built_in_strategy_parameters,
    save_strategy_profile_override,
    strategy_profile_candidate_rows,
    strategy_profile_rows,
)


class StrategyProfileTests(unittest.TestCase):
    def test_built_in_strategies_have_research_profiles(self):
        expected = {
            "ma_crossover",
            "rsi_reversion",
            "bollinger_reversion",
            "breakout",
            "momentum_rotation",
            "alipay",
            "alipay_enhanced",
        }
        self.assertEqual(set(STRATEGY_PROFILES), expected)
        for strategy_id in expected:
            profile = get_strategy_profile(strategy_id)
            self.assertEqual(profile.strategy_id, strategy_id)
            self.assertTrue(profile.display_name)
            self.assertTrue(profile.display_name_en)
            self.assertTrue(profile.thesis)
            self.assertTrue(profile.thesis_en)
            self.assertTrue(profile.earnings)
            self.assertTrue(profile.persistence)
            self.assertTrue(profile.failure)
            self.assertTrue(profile.default_parameter_note)

    def test_return_source_taxonomy_has_required_categories(self):
        sources = {item.source for item in RETURN_SOURCE_TAXONOMY}
        self.assertEqual(
            sources,
            {"风险溢价", "行为偏差", "信息优势", "结构性约束", "执行优势", "组合优势"},
        )

    def test_unknown_strategy_profile_requires_approval_context(self):
        profile = get_strategy_profile("custom_strategy")
        self.assertEqual(profile.strategy_id, "unknown")
        self.assertIn("审批", profile.approval_note)

    def test_strategy_profile_rows_are_ui_ready(self):
        rows = strategy_profile_rows()
        self.assertEqual(len(rows), 7)
        self.assertEqual(rows[0]["顺序 Order"], 1)
        self.assertIn("策略编号 Strategy Id", rows[0])
        self.assertIn("收益来源 Return Sources", rows[0])

    def test_strategy_order_is_persistent_and_appends_missing_profiles(self):
        with TemporaryDirectory() as tmp:
            order_path = Path(tmp) / "StrategyOrder.json"

            saved_path = save_strategy_order(["alipay_enhanced", "ma_crossover"], path=order_path)
            order = ordered_strategy_ids(order_path)
            rows = strategy_profile_rows(order_path=order_path)

            self.assertEqual(saved_path, order_path)
            self.assertEqual(load_strategy_order(order_path)[:2], ["alipay_enhanced", "ma_crossover"])
            self.assertEqual(order[:2], ["alipay_enhanced", "ma_crossover"])
            self.assertEqual(set(order), set(STRATEGY_PROFILES))
            self.assertEqual(rows[0]["策略编号 Strategy Id"], "alipay_enhanced")
            self.assertEqual(rows[1]["策略编号 Strategy Id"], "ma_crossover")

    def test_strategy_order_move_and_reset(self):
        with TemporaryDirectory() as tmp:
            order_path = Path(tmp) / "StrategyOrder.json"

            save_strategy_order(list(DEFAULT_STRATEGY_ORDER), path=order_path)
            move_strategy_order_item("rsi_reversion", "up", path=order_path)
            moved = ordered_strategy_ids(order_path)
            save_strategy_order(list(DEFAULT_STRATEGY_ORDER), path=order_path)

            self.assertEqual(moved[0], "rsi_reversion")
            self.assertEqual(ordered_strategy_ids(order_path), list(DEFAULT_STRATEGY_ORDER))

    def test_parses_custom_strategy_profile_candidate_from_markdown(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = StrategyApprovalRegistry(path=root / "StrategyApprovals.json")
            artifact = create_strategy_template(
                strategy_id="custom_momentum_filter",
                display_name="自定义动量过滤",
                display_name_en="Custom Momentum Filter",
                category="趋势跟随 Trend Following",
                return_source="行为偏差 Behavioral Bias",
                thesis="价格动量可能延续。",
                failure="震荡市场可能失效。",
                strategy_dir=root / "strategies",
                profile_dir=root / "profiles",
                approval_registry=registry,
            )

            candidate = parse_strategy_profile_candidate(artifact.profile_file)
            candidates = collect_strategy_profile_candidates(root / "profiles")
            rows = strategy_profile_candidate_rows(root / "profiles")

            self.assertEqual(candidate.strategy_id, "custom_momentum_filter")
            self.assertEqual(candidate.display_name, "自定义动量过滤")
            self.assertEqual(candidate.display_name_en, "Custom Momentum Filter")
            self.assertEqual(candidate.approval_status, "Pending")
            self.assertEqual(candidate.quality_status, "Incomplete")
            self.assertGreater(candidate.quality_score, 0)
            self.assertIn("参数设置 Parameter Settings", candidate.missing_items)
            self.assertIn("价格动量", candidate.thesis)
            self.assertEqual(len(candidates), 1)
            self.assertEqual(rows[0]["策略编号 Strategy Id"], "custom_momentum_filter")
            self.assertEqual(rows[0]["审批状态 Approval Status"], "Pending")
            self.assertEqual(rows[0]["质量状态 Quality Status"], "Incomplete")

    def test_candidate_quality_marks_complete_payload_ready_for_review(self):
        status, score, missing = evaluate_strategy_profile_candidate_quality(
            {
                "strategy_id": "custom_signal",
                "display_name": "自定义信号",
                "display_name_en": "Custom Signal",
                "version": "0.1.0",
                "category": "趋势跟随 Trend Following",
                "thesis": "动量延续可能存在。",
                "return_source": "行为偏差 Behavioral Bias",
                "failure": "震荡和反转环境可能失效。",
                "parameter_notes": "lookback: 20-120; threshold: 0.01-0.10.",
            }
        )
        self.assertEqual(status, "ReadyForReview")
        self.assertEqual(score, 100)
        self.assertEqual(missing, ())

    def test_builtin_strategy_profile_overrides_are_persistent(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            override_path = root / "StrategyProfileOverrides.json"
            original = get_strategy_profile("ma_crossover", override_path=override_path)
            payload = editable_strategy_profile_payload(original)
            payload["display_name"] = "测试均线交叉"
            payload["display_name_en"] = "Test Moving Average Crossover"
            payload["primary_sources"] = ["行为偏差", "执行优势"]

            saved_path = save_strategy_profile_override("ma_crossover", payload, path=override_path)
            overrides = load_strategy_profile_overrides(saved_path)
            updated = get_strategy_profile("ma_crossover", override_path=saved_path)

            self.assertEqual(saved_path, override_path)
            self.assertIn("ma_crossover", overrides)
            self.assertEqual(updated.display_name, "测试均线交叉")
            self.assertEqual(updated.display_name_en, "Test Moving Average Crossover")
            self.assertEqual(updated.primary_sources, ("行为偏差", "执行优势"))
            self.assertEqual(STRATEGY_PROFILES["ma_crossover"].display_name, "均线交叉")

    def test_builtin_strategy_parameters_are_persistent_and_validated(self):
        with TemporaryDirectory() as tmp:
            parameter_path = Path(tmp) / "BuiltInStrategyParameters.json"

            saved_path = save_built_in_strategy_parameters(
                "ma_crossover",
                {"short_window": 12, "long_window": 80},
                path=parameter_path,
            )
            overrides = load_built_in_strategy_parameter_overrides(saved_path)
            params = get_built_in_strategy_parameters("ma_crossover", path=saved_path)
            rows = built_in_strategy_parameter_rows("ma_crossover", path=saved_path)

            self.assertEqual(saved_path, parameter_path)
            self.assertEqual(overrides["ma_crossover"]["short_window"], 12)
            self.assertEqual(params, {"short_window": 12, "long_window": 80})
            self.assertEqual(rows[0]["是否已修改 Modified"], "是")
            self.assertEqual(DEFAULT_BUILT_IN_STRATEGY_PARAMETERS["ma_crossover"]["short_window"], 20)
            with self.assertRaises(ValueError):
                clean_built_in_strategy_parameters("ma_crossover", {"short_window": 90, "long_window": 20})

    def test_invalid_builtin_strategy_parameter_override_falls_back_to_system_default(self):
        with TemporaryDirectory() as tmp:
            parameter_path = Path(tmp) / "BuiltInStrategyParameters.json"
            parameter_path.write_text(
                '{"strategy_parameters": {"rsi_reversion": {"entry": 80, "exit": 20}}}',
                encoding="utf-8",
            )

            params = get_built_in_strategy_parameters("rsi_reversion", path=parameter_path)

            self.assertEqual(params, DEFAULT_BUILT_IN_STRATEGY_PARAMETERS["rsi_reversion"])

    def test_strategy_persistent_state_fail_closes_on_corrupt_json(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            order_path = root / "StrategyOrder.json"
            override_path = root / "StrategyProfileOverrides.json"
            parameter_path = root / "BuiltInStrategyParameters.json"
            for path in (order_path, override_path, parameter_path):
                path.write_text("{bad json", encoding="utf-8")

            with self.assertRaises(ValueError):
                load_strategy_order(order_path)
            with self.assertRaises(ValueError):
                load_strategy_profile_overrides(override_path)
            with self.assertRaises(ValueError):
                load_built_in_strategy_parameter_overrides(parameter_path)
            with self.assertRaises(ValueError):
                save_built_in_strategy_parameters(
                    "ma_crossover",
                    {"short_window": 12, "long_window": 80},
                    path=parameter_path,
                )
            self.assertEqual(parameter_path.read_text(encoding="utf-8"), "{bad json")

    def test_custom_strategy_template_can_create_complete_profile_with_parameter_notes(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = StrategyApprovalRegistry(path=root / "StrategyApprovals.json")
            artifact = create_strategy_template(
                strategy_id="custom_complete",
                display_name="完整策略",
                display_name_en="Complete Strategy",
                category="均值回归 Mean Reversion",
                return_source="行为偏差 Behavioral Bias",
                thesis="短期偏离后可能回归。",
                failure="趋势行情可能失效。",
                parameter_notes="lookback: 20-120; threshold: 1.0-3.0.",
                strategy_dir=root / "strategies",
                profile_dir=root / "profiles",
                approval_registry=registry,
            )

            candidate = parse_strategy_profile_candidate(artifact.profile_file)
            profile_text = Path(artifact.profile_file).read_text(encoding="utf-8")

            self.assertEqual(candidate.quality_status, "ReadyForReview")
            self.assertEqual(candidate.quality_score, 100)
            self.assertEqual(candidate.missing_items, ())
            self.assertIn("## 参数设置", profile_text)
            self.assertIn("## Parameter Settings", profile_text)


if __name__ == "__main__":
    unittest.main()
