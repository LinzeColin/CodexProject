from __future__ import annotations

import importlib
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TestV022Stage9VisualizationUIUX(unittest.TestCase):
    def _module(self):
        try:
            return importlib.import_module("pfi_v02.stage_v022_visualization_uiux")
        except ModuleNotFoundError as exc:
            self.fail(f"Stage 9 visualization/uiux module is missing: {exc}")

    def _catalog(self) -> dict[str, object]:
        governance = importlib.import_module("pfi_v02.stage_v022_database_governance")
        return governance.load_v022_parameter_catalog(ROOT / "config" / "pfi_parameters.yaml")

    def test_stage9_contract_locks_phase_task_acceptance_and_validation(self) -> None:
        governance = importlib.import_module("pfi_v02.stage_v022_database_governance")
        build_contract = getattr(governance, "build_v022_stage9_contract", None)
        self.assertIsNotNone(build_contract, "build_v022_stage9_contract() is required")

        contract = build_contract()

        self.assertEqual(contract["schema"], "PFIV022VisualizationUIUXStage9ContractV1")
        self.assertEqual(contract["stage"], "Stage 9")
        self.assertEqual(
            tuple(contract["task_ids"]),
            (
                "S9-P1-T1",
                "S9-P1-T2",
                "S9-P1-T3",
                "S9-P2-T1",
                "S9-P2-T2",
                "S9-P2-T3",
                "S9-P3-T1",
                "S9-P3-T2",
                "S9-P3-T3",
                "S9-P3-T4",
                "S9-P4-T1",
                "S9-P4-T2",
                "S9-P4-T3",
            ),
        )
        for required in (
            "参数中心",
            "Interconnection Map",
            "Metric Dependency Graph",
            "现金流阶梯图",
            "现金流瀑布图",
            "储备金安全带",
            "投资入金挤压图",
            "Metric Drilldown Debugger",
            "HTML 单文件可打开",
            "不依赖外网",
            "Stage 10 报告、建议与复盘不在本轮实现",
        ):
            self.assertIn(required, str(contract))

    def test_parameter_center_model_exposes_required_domains_and_chinese_explanations(self) -> None:
        module = self._module()
        parameter_center = module.build_parameter_center_model(self._catalog())

        self.assertEqual(parameter_center["schema"], "PFIV022Stage9ParameterCenterV1")
        required_domains = ("货币", "汇率", "分类", "标签", "阈值", "公式", "置信度", "现金流窗口")
        self.assertEqual(tuple(parameter_center["required_domains"]), required_domains)
        labels = tuple(item["domain_zh"] for item in parameter_center["items"])
        for domain in required_domains:
            self.assertIn(domain, labels)

        for item in parameter_center["items"]:
            with self.subTest(parameter=item["parameter_key"]):
                self.assertRegex(item["name_zh"], r"[\u4e00-\u9fff]")
                self.assertRegex(str(item["current_value"]), r".+")
                self.assertRegex(item["purpose_zh"], r"[\u4e00-\u9fff]")
                self.assertTrue(item["impact_surfaces"])
                self.assertIn("user_editable", item)

    def test_parameter_impact_preview_is_local_and_counts_records_tags_advice_and_charts(self) -> None:
        module = self._module()
        preview = module.calculate_parameter_impact_preview(
            parameter_key="confidence.review_threshold",
            old_value=70,
            new_value=75,
            sample_counts={"review_records": 406, "tags": 48, "advice_items": 12, "charts": 9},
        )

        self.assertEqual(preview["schema"], "PFIV022Stage9ParameterImpactPreviewV1")
        self.assertFalse(preview["network_allowed"])
        self.assertEqual(preview["affected_records"], 406)
        self.assertEqual(preview["affected_tags"], 48)
        self.assertEqual(preview["affected_advice_items"], 12)
        self.assertEqual(preview["affected_charts"], 9)
        self.assertIn("修改阈值前显示可能影响的记录数、标签数、建议数、图表数", preview["explanation_zh"])

    def test_interconnection_map_mermaid_draws_full_source_to_ui_chain(self) -> None:
        module = self._module()
        mermaid = module.build_interconnection_map_mermaid()

        self.assertIn("graph TD", mermaid)
        for node in ("source", "raw", "normalized", "group", "event", "ledger", "metrics", "UI"):
            self.assertIn(node, mermaid)
        self.assertRegex(mermaid, re.compile(r"source.*-->.*raw.*-->.*normalized.*-->.*group.*-->.*event.*-->.*ledger.*-->.*metrics.*-->.*UI", re.S))

    def test_visualization_payload_covers_required_modules_and_status_metadata(self) -> None:
        module = self._module()
        payload = module.build_stage9_visualization_payload(self._catalog())

        required_modules = (
            "首页总览",
            "参数中心",
            "Interconnection Map",
            "Metric Dependency Graph",
            "消费分类与标签",
            "投资模型",
            "消费模型",
            "现金流可视化",
            "Runtime Diff Dashboard",
            "Agent Review Queue",
            "验收清单",
        )
        self.assertEqual(tuple(payload["module_titles"]), required_modules)

        required_status_fields = (
            "数据来源覆盖率",
            "最近更新时间",
            "参数版本",
            "公式版本",
            "汇率快照 ID",
            "ledger_hash",
            "interconnection_hash",
            "是否存在未匹配记录",
            "是否存在低置信记录",
            "是否存在缓存",
            "是否需要重算",
            "UI 指标是否与报告一致",
        )
        for module_item in payload["modules"]:
            with self.subTest(module=module_item["title"]):
                for field in required_status_fields:
                    self.assertIn(field, module_item["data_status"])

    def test_cashflow_visualizations_cover_ladder_waterfall_safety_band_and_investment_squeeze(self) -> None:
        module = self._module()
        cashflow = module.build_cashflow_visualization_model()

        self.assertEqual(tuple(cashflow["windows_days"]), (7, 21, 30, 60, 90, 180, 360))
        self.assertEqual(
            tuple(cashflow["visualizations"]),
            ("现金流阶梯图", "现金流瀑布图", "储备金安全带", "投资入金挤压图"),
        )
        for component in ("当前现金", "收入", "退款", "固定支出", "弹性支出", "信用卡", "投资入金", "投资回流"):
            self.assertIn(component, cashflow["waterfall_components"])
        self.assertEqual(tuple(cashflow["reserve_safety_band"]), ("绿色", "黄色", "红色"))
        self.assertIn("投资入金对生活现金和储备金的影响", cashflow["investment_squeeze_explanation_zh"])

    def test_metric_drilldown_debugger_explains_included_excluded_adjusted_and_quality(self) -> None:
        module = self._module()
        debugger = module.build_metric_drilldown_debugger_model()

        self.assertEqual(debugger["schema"], "PFIV022Stage9MetricDrilldownDebuggerV1")
        for metric in ("本月消费", "投资资产", "现金流窗口"):
            self.assertIn(metric, debugger["metrics"])
            item = debugger["metrics"][metric]
            self.assertTrue(item["included"])
            self.assertTrue(item["excluded"])
            self.assertTrue(item["adjusted"])
            for quality in ("confidence", "match_rate", "last_updated", "compute_time_ms", "cache_status"):
                self.assertIn(quality, item["quality"])

    def test_stage9_html_docs_and_parameters_are_recorded(self) -> None:
        expected_docs = (
            ROOT / "docs" / "pfi_v022" / "STAGE9_VISUALIZATION_UIUX.md",
            ROOT / "docs" / "pfi_v022" / "INTERCONNECTION_MAP.md",
            ROOT / "docs" / "pfi_v022" / "ROADMAP_LOCK.md",
            ROOT / "web" / "interconnection-map.html",
            ROOT / "模型参数文件.md",
            ROOT / "功能清单.md",
            ROOT / "开发记录.md",
        )
        for path in expected_docs:
            self.assertTrue(path.exists(), f"{path} must exist for Stage 9")
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.name):
                self.assertIn("Stage 9 - 可视化与 UI/UX", text)
                self.assertIn("S9-P1-T1", text)
                self.assertIn("参数中心", text)
                self.assertIn("Interconnection Map", text)
                self.assertIn("Metric Dependency Graph", text)
                self.assertIn("现金流阶梯图", text)
                self.assertIn("Metric Drilldown Debugger", text)

        html = (ROOT / "web" / "interconnection-map.html").read_text(encoding="utf-8")
        self.assertIn("<!doctype html>", html.lower())
        self.assertNotRegex(html, re.compile(r"https?://|cdn\\.|<script\\s+src=|<link[^>]+href=['\\\"]https?://", re.I))
        for required in (
            "首页总览",
            "参数中心",
            "Interconnection Map",
            "Metric Dependency Graph",
            "消费分类与标签",
            "投资模型",
            "消费模型",
            "现金流可视化",
            "Runtime Diff Dashboard",
            "Agent Review Queue",
            "验收清单",
            "数据来源覆盖率",
            "ledger_hash",
            "interconnection_hash",
            "是否需要重算",
            "data-map-node",
            "data-drilldown-metric",
        ):
            self.assertIn(required, html)

        governance = importlib.import_module("pfi_v02.stage_v022_database_governance")
        catalog = self._catalog()
        self.assertEqual(catalog["schema"], "PFIParametersV022Stage9")
        self.assertEqual(catalog["current_stage"], "Stage 9 - 可视化与 UI/UX")
        self.assertEqual(catalog["stage9_task_ids"], list(governance.V022_STAGE9_TASK_IDS))
        self.assertFalse(catalog["parameters"]["visualization_uiux"]["local_html_external_network_allowed"]["value"])


if __name__ == "__main__":
    unittest.main()
