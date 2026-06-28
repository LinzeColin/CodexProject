from __future__ import annotations

import re
import unittest
from pathlib import Path

from pfi_v02.stage_v021_frontend_contract import (
    BASE_CURRENCY,
    STAGE0_TASK_ID,
    UI_TARGET,
    VERSION_NAME,
    build_v021_stage0_contract,
    v021_navigation_labels,
    v021_stage_task_ids,
)


class V021Stage0FrontendContractTest(unittest.TestCase):
    def test_version_scope_and_non_goals_are_locked(self) -> None:
        contract = build_v021_stage0_contract()

        self.assertEqual(contract["version_name"], VERSION_NAME)
        self.assertEqual(VERSION_NAME, "v0.2.1 前端优化")
        self.assertEqual(contract["task_id"], STAGE0_TASK_ID)
        self.assertIn("持仓编辑持久化", contract["scope"])
        self.assertIn("CNY 基准与 CNY/AUD 顶栏汇率", contract["scope"])
        self.assertIn("不重构 QBVS", contract["non_scope"])
        self.assertIn("不把后续 stage 的 UI 实现塞进 stage0", contract["non_scope"])
        self.assertIn("Alpha", " ".join(contract["forbidden_product_l1_entries"]))
        self.assertIn("Development", " ".join(contract["forbidden_product_l1_entries"]))

    def test_currency_contract_uses_cny_base_and_all_page_top_right_badge(self) -> None:
        currency = build_v021_stage0_contract()["currency_contract"]

        self.assertEqual(BASE_CURRENCY, "CNY")
        self.assertEqual(currency["base_currency"], "CNY")
        self.assertEqual(currency["quote_pair"], "CNY/AUD")
        self.assertEqual(currency["placement"], "top_right")
        self.assertTrue(currency["visible_on_all_pages"])
        self.assertEqual(currency["snapshot_time_local"], "06:00")
        self.assertEqual(currency["snapshot_timezone"], "Australia/Sydney")
        self.assertEqual(currency["display_format"], "CNY/AUD=4.70（YYYY/MM/DD HH:MM）")
        self.assertRegex(
            currency["example_display"],
            re.compile(r"^CNY/AUD=\d+\.\d{2}（\d{4}/\d{2}/\d{2} \d{2}:\d{2}）$"),
        )
        self.assertIn("do not invent rates", currency["refresh_policy"])

    def test_html_multimodal_feedback_target_is_settings_only(self) -> None:
        feedback = build_v021_stage0_contract()["feedback_contract"]

        self.assertEqual(UI_TARGET, "PFI/web HTML shell")
        self.assertEqual(feedback["formal_delivery_surface"], "HTML")
        self.assertEqual(feedback["settings_route"], "/settings")
        self.assertFalse(feedback["default_visible_on_business_pages"])
        for item in ["反馈偏好", "触感反馈", "声音反馈", "视觉反馈", "通知反馈"]:
            self.assertIn(item, feedback["feedback_controls"])
        self.assertEqual(feedback["haptic_levels"], ("关闭", "轻", "标准", "强"))

    def test_navigation_contract_unifies_v02_and_v01_without_visible_group_titles(self) -> None:
        contract = build_v021_stage0_contract()

        self.assertEqual(
            v021_navigation_labels(),
            (
                "首页总览",
                "账户与资产",
                "账本流水",
                "投资管理",
                "消费管理",
                "数据源与上传",
                "建议与复盘",
                "报告与洞察",
                "首页",
                "市场",
                "研究",
                "持仓",
                "策略实验室",
                "数据与系统",
                "设置",
            ),
        )
        self.assertNotIn("数据源与同步", v021_navigation_labels())
        self.assertIn("PFI 1.0 兼容入口", contract["forbidden_visible_nav_group_labels"])
        self.assertIn("运行边界", contract["forbidden_visible_nav_group_labels"])

        route_by_label = {entry["label"]: entry["route"] for entry in contract["navigation_entries"]}
        owner_by_label = {entry["label"]: entry["page_owner"] for entry in contract["navigation_entries"]}
        self.assertEqual(route_by_label["策略实验室"], "/investment/strategy-lab")
        self.assertEqual(owner_by_label["策略实验室"], "投资管理")
        self.assertEqual(route_by_label["数据与系统"], "/settings?tab=data-system")
        self.assertEqual(route_by_label["设置"], "/settings")
        self.assertTrue(all(not entry["creates_duplicate_workspace"] for entry in contract["navigation_entries"]))

    def test_stage_plan_covers_all_roadmap_tasks_in_order(self) -> None:
        task_ids = v021_stage_task_ids()

        self.assertEqual(task_ids[0], "V021-P0-S0-T01")
        self.assertEqual(task_ids[-1], "V021-P8-S8-T03")
        self.assertEqual(len(task_ids), 24)
        for required in (
            "V021-P1-S1-T04",
            "V021-P3-S3-T02",
            "V021-P4-S4-T01",
            "V021-P6-S6-T03",
            "V021-P8-S8-T02",
        ):
            self.assertIn(required, task_ids)

    def test_stage0_records_exist_and_contain_acceptance_terms(self) -> None:
        root = Path(__file__).resolve().parents[1]
        record = root / "docs" / "pfi_v02" / "STAGE_V021_FRONTEND_OPTIMIZATION.md"
        version = root / "VERSION"
        dev_record = root / "开发记录.md"
        feature_list = root / "功能清单.md"
        parameter_file = root / "模型参数文件.md"

        for path in (record, version, dev_record, feature_list, parameter_file):
            self.assertTrue(path.exists(), path)

        record_text = record.read_text(encoding="utf-8")
        self.assertIn("v0.2.1 前端优化", record_text)
        self.assertIn("CNY/AUD=4.70（YYYY/MM/DD HH:MM）", record_text)
        self.assertIn("当日 06:00", record_text)
        self.assertIn("HTML Web Shell", record_text)
        self.assertIn("V021-P0-S0-T01", record_text)
        self.assertEqual(version.read_text(encoding="utf-8").strip(), "v0.2.1 前端优化")
        self.assertIn("v0.2.1 前端优化", dev_record.read_text(encoding="utf-8"))
        self.assertIn("数据源与上传", feature_list.read_text(encoding="utf-8"))
        self.assertIn("base_currency", parameter_file.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
