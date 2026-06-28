from __future__ import annotations

import copy
import importlib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TestV022Stage8RuntimeDiff(unittest.TestCase):
    def _module(self):
        try:
            return importlib.import_module("pfi_v02.stage_v022_runtime_diff")
        except ModuleNotFoundError as exc:
            self.fail(f"Stage 8 runtime diff module is missing: {exc}")

    def _real_inputs(self) -> dict[str, object]:
        module = self._module()
        loaded = module.load_stage8_runtime_diff_inputs_from_canonical_sources(ROOT)
        summary = loaded["source_summary"]
        self.assertGreaterEqual(summary["raw_file_count"], 4)
        self.assertGreaterEqual(summary["normalized_transaction_count"], 8000)
        self.assertEqual(summary["interconnection_state_zh"], module.STAGE8_INTERCONNECTION_EMPTY_STATE_ZH)
        return copy.deepcopy(loaded["inputs"])

    def test_stage8_contract_locks_phase_task_acceptance_and_validation(self) -> None:
        governance = importlib.import_module("pfi_v02.stage_v022_database_governance")
        build_contract = getattr(governance, "build_v022_stage8_contract", None)
        self.assertIsNotNone(build_contract, "build_v022_stage8_contract() is required")

        contract = build_contract()

        self.assertEqual(contract["schema"], "PFIV022RuntimeDiffStage8ContractV1")
        self.assertEqual(contract["stage"], "Stage 8")
        self.assertEqual(
            tuple(contract["task_ids"]),
            (
                "S8-P1-T1",
                "S8-P1-T2",
                "S8-P1-T3",
                "S8-P2-T1",
                "S8-P2-T2",
                "S8-P2-T3",
                "S8-P2-T4",
                "S8-P3-T1",
                "S8-P3-T2",
                "S8-P3-T3",
            ),
        )
        for required in (
            "原始数据、标准化交易、账本事件、interconnection、参数、分类、标签、汇率快照 hash",
            "无 diff 不联网、不生成 Codex ticket、不触发 LLM",
            "有 diff 时只重算受影响指标",
            "P0 核心指标仅包括",
            "Stage 9 可视化与 UI/UX 不在本轮实现",
            "PFI/review_queue/CODEX_REVIEW_TICKET_TEMPLATE.md",
        ):
            self.assertIn(required, str(contract))

    def test_dependency_hash_snapshot_is_stable_and_covers_all_required_dependencies(self) -> None:
        module = self._module()
        inputs = self._real_inputs()
        snapshot = module.build_dependency_hash_snapshot(inputs, run_id="stage8-test")
        repeat = module.build_dependency_hash_snapshot(inputs, run_id="stage8-test-repeat")

        self.assertEqual(snapshot["schema"], "PFIV022RuntimeDiffSnapshotV1")
        self.assertEqual(tuple(snapshot["dependency_hashes"].keys()), module.STAGE8_DEPENDENCY_HASH_KEYS)
        for hash_value in snapshot["dependency_hashes"].values():
            self.assertRegex(hash_value, r"^[0-9a-f]{64}$")
        self.assertEqual(snapshot["dependency_hashes"], repeat["dependency_hashes"])
        self.assertEqual(snapshot["run_hash"], repeat["run_hash"])

        changed_inputs = self._real_inputs()
        changed_tags = copy.deepcopy(changed_inputs["tags"])
        changed_tags["default_tag_library"] = (
            {**changed_tags["default_tag_library"][0], "label_zh": "计划内复核"},
            *changed_tags["default_tag_library"][1:],
        )
        changed_inputs["tags"] = changed_tags
        changed = module.build_dependency_hash_snapshot(changed_inputs, run_id="stage8-test-changed")
        diff = module.compare_dependency_snapshots(snapshot, changed)

        self.assertEqual(diff["changed_dependency_keys"], ("tag_hash",))
        self.assertTrue(diff["has_diff"])
        self.assertEqual(diff["unchanged_dependency_keys"].count("raw_data_hash"), 1)

    def test_no_diff_never_triggers_network_llm_or_codex_ticket(self) -> None:
        module = self._module()
        snapshot = module.build_dependency_hash_snapshot(self._real_inputs(), run_id="same")
        diff = module.compare_dependency_snapshots(snapshot, snapshot)
        report = module.build_impacted_metrics_report(diff)

        self.assertFalse(diff["has_diff"])
        self.assertEqual(report["recompute_scope"], "none")
        self.assertFalse(report["network_allowed"])
        self.assertFalse(report["external_analysis_required"])
        self.assertFalse(report["llm_review_required"])
        self.assertFalse(report["codex_ticket_required"])
        self.assertEqual(report["direct_impacted_metrics"], {"P0": (), "P1": (), "P2": ()})

    def test_tag_display_name_diff_does_not_pollute_core_financial_metrics(self) -> None:
        module = self._module()
        inputs = self._real_inputs()
        before = module.build_dependency_hash_snapshot(inputs, run_id="before")
        changed_inputs = self._real_inputs()
        changed_tags = copy.deepcopy(changed_inputs["tags"])
        changed_tags["default_tag_library"] = (
            {**changed_tags["default_tag_library"][0], "label_zh": "计划内复核"},
            *changed_tags["default_tag_library"][1:],
        )
        changed_inputs["tags"] = changed_tags
        after = module.build_dependency_hash_snapshot(changed_inputs, run_id="after")
        diff = module.compare_dependency_snapshots(before, after)
        report = module.build_impacted_metrics_report(diff)

        self.assertEqual(diff["changed_dependency_keys"], ("tag_hash",))
        self.assertFalse(report["full_recompute"])
        self.assertEqual(report["recompute_scope"], "changed_dependency_only")
        self.assertEqual(report["direct_impacted_metrics"]["P0"], ())
        self.assertIn("标签视图", report["direct_impacted_metrics"]["P1"])
        self.assertIn("辅助说明", report["direct_impacted_metrics"]["P2"])
        for metric in ("净资产", "投资收益", "现金流窗口"):
            self.assertIn(metric, report["not_impacted_metrics"])

    def test_p0_p1_p2_metric_boundaries_are_tight_and_separated(self) -> None:
        module = self._module()

        self.assertEqual(
            module.STAGE8_P0_CORE_METRICS,
            (
                "净资产",
                "生活现金",
                "投资资产",
                "消费总流出",
                "生活消费",
                "投资收益",
                "现金流窗口",
                "待复核数量",
                "Interconnection 异常数量",
            ),
        )
        for required_p1 in ("分类占比", "标签视图", "订阅", "夜间", "大额", "投资风格", "交易频率", "费用拖累", "现金拖累"):
            self.assertIn(required_p1, module.STAGE8_P1_ANALYSIS_METRICS)
        for required_p2 in ("图表排序", "趋势图", "辅助说明", "tooltip", "参数中心展示"):
            self.assertIn(required_p2, module.STAGE8_P2_DISPLAY_METRICS)
        self.assertTrue(set(module.STAGE8_P0_CORE_METRICS).isdisjoint(module.STAGE8_P1_ANALYSIS_METRICS))
        self.assertTrue(set(module.STAGE8_P0_CORE_METRICS).isdisjoint(module.STAGE8_P2_DISPLAY_METRICS))

    def test_llm_trigger_policy_only_allows_business_or_conflict_review_reasons(self) -> None:
        module = self._module()
        policy = module.build_llm_trigger_policy()

        for reason in (
            "业务语义变化",
            "公式逻辑变化",
            "分类冲突",
            "标签冲突",
            "跨板块不一致",
            "测试无法解释",
        ):
            with self.subTest(reason=reason):
                self.assertTrue(module.should_trigger_llm_review(reason, policy=policy))

        for reason in ("无 diff", "只刷新缓存", "只重绘图表", "汇率快照未变", "参数未变", "普通本地重算"):
            with self.subTest(reason=reason):
                self.assertFalse(module.should_trigger_llm_review(reason, policy=policy))

    def test_codex_review_ticket_template_is_chinese_actionable_and_local_only(self) -> None:
        module = self._module()
        before = module.build_dependency_hash_snapshot(self._real_inputs(), run_id="before")
        changed_inputs = self._real_inputs()
        changed_categories = copy.deepcopy(changed_inputs["categories"])
        changed_categories["consumption_taxonomy"] = (
            {**changed_categories["consumption_taxonomy"][0], "review_label_zh": "餐饮食品复核"},
            *changed_categories["consumption_taxonomy"][1:],
        )
        changed_inputs["categories"] = changed_categories
        after = module.build_dependency_hash_snapshot(changed_inputs, run_id="after")
        diff = module.compare_dependency_snapshots(before, after)
        report = module.build_impacted_metrics_report(diff, trigger_reason="分类冲突")
        ticket = module.build_codex_review_ticket(report, trigger_reason="分类冲突")

        self.assertEqual(ticket["schema"], "PFIV022CodexReviewTicketTemplateV1")
        for field in ("触发原因", "影响指标", "涉及文件", "期望检查", "禁止事项", "中文业务解释"):
            self.assertIn(field, ticket)
            self.assertRegex(str(ticket[field]), r"[\u4e00-\u9fff]")
        self.assertIn("不得联网", str(ticket["禁止事项"]))
        self.assertIn("不得全仓无差别扫描", str(ticket["禁止事项"]))
        self.assertIn("分类冲突", ticket["触发原因"])

    def test_stage8_docs_parameters_and_review_queue_are_recorded(self) -> None:
        expected_docs = (
            ROOT / "docs" / "pfi_v022" / "STAGE8_RUNTIME_DIFF_IMPACTED_METRICS.md",
            ROOT / "docs" / "pfi_v022" / "ROADMAP_LOCK.md",
            ROOT / "review_queue" / "CODEX_REVIEW_TICKET_TEMPLATE.md",
            ROOT / "模型参数文件.md",
            ROOT / "功能清单.md",
            ROOT / "开发记录.md",
        )
        for path in expected_docs:
            self.assertTrue(path.exists(), f"{path} must exist for Stage 8")
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.name):
                if path.name in {"STAGE8_RUNTIME_DIFF_IMPACTED_METRICS.md", "CODEX_REVIEW_TICKET_TEMPLATE.md"}:
                    self.assertIn("Stage 8 - 本地运行 Diff 与 Impacted Metrics", text)
                else:
                    self.assertIn("Stage 13 - 后置触发型复核", text)
                self.assertIn("S8-P1-T1", text)
                self.assertIn("P0 核心指标", text)
                self.assertIn("P1 分析指标", text)
                self.assertIn("P2 展示指标", text)
                self.assertIn("无 diff 不联网", text)
                self.assertIn("Codex Review Ticket", text)

        governance = importlib.import_module("pfi_v02.stage_v022_database_governance")
        catalog = governance.load_v022_parameter_catalog(ROOT / "config" / "pfi_parameters.yaml")
        self.assertEqual(catalog["schema"], "PFIParametersV022Stage13")
        self.assertEqual(catalog["current_stage"], "Stage 13 - 后置触发型复核")
        self.assertEqual(catalog["stage8_task_ids"], list(governance.V022_STAGE8_TASK_IDS))
        self.assertFalse(catalog["parameters"]["runtime_refresh_policy"]["default_network_refresh"]["value"])
        self.assertEqual(
            catalog["parameters"]["runtime_refresh_policy"]["no_diff_behavior"]["value"],
            "不联网、不生成 Codex ticket、不触发 LLM",
        )


if __name__ == "__main__":
    unittest.main()
