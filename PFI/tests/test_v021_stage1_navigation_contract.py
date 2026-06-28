from __future__ import annotations

import re
import unittest
from pathlib import Path

from pfi_v02.stage_v021_frontend_contract import (
    STAGE1_TASK_IDS,
    build_v021_stage1_contract,
)
from pfi_v02.stage_v0211_ui_recovery import v0211_stage1_navigation_labels


class V021Stage1NavigationContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.html = (self.root / "web" / "index.html").read_text(encoding="utf-8")
        self.js = (self.root / "web" / "app" / "shell.js").read_text(encoding="utf-8")

    def test_stage1_contract_covers_all_four_roadmap_tasks(self) -> None:
        contract = build_v021_stage1_contract()

        self.assertEqual(contract["schema"], "PFIV021FrontendOptimizationStage1ContractV1")
        self.assertEqual(tuple(contract["task_ids"]), STAGE1_TASK_IDS)
        self.assertEqual(
            tuple(contract["visible_navigation_label_order"]),
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
        self.assertEqual(contract["single_route_contract"]["workspace"], "investment")
        self.assertFalse(contract["single_route_contract"]["creates_duplicate_workspace"])

    def test_web_shell_uses_one_unified_navigation_list_without_group_titles(self) -> None:
        labels = tuple(
            re.findall(
                r'<button[^>]*data-primary-entry="true"[^>]*>([^<]+)</button>',
                self.html,
            )
        )

        self.assertEqual(labels, v0211_stage1_navigation_labels())
        self.assertIn('data-primary-workspaces="10"', self.html)
        self.assertEqual(self.html.count('data-primary-entry="true"'), 10)
        self.assertNotIn("legacy-nav", self.html)
        self.assertNotIn('data-v01-entry="true"', self.html)
        for forbidden in build_v021_stage1_contract()["forbidden_visible_nav_group_labels"]:
            self.assertNotIn(forbidden, self.html)

    def test_upload_and_import_naming_are_user_visible_in_web_shell(self) -> None:
        web_text = self.html + self.js

        self.assertIn("数据源与上传", web_text)
        self.assertIn("导入中心", web_text)
        self.assertNotIn("数据源与同步", web_text)
        self.assertNotIn("低操作导入中心", web_text)

    def test_strategy_lab_routes_to_market_research_without_strategy_workspace(self) -> None:
        self.assertIn('data-workspace="market_research" data-route-alias="/market-research"', self.html)
        self.assertIn('data-command-workspace="market_research" data-command-route="/market-research/strategy-lab"', self.html)
        self.assertIn('"/strategy-lab": "/market-research/strategy-lab"', self.js)
        self.assertNotIn('data-workspace="strategy"', self.html)
        self.assertNotIn('workspace: "strategy"', self.js)
        self.assertIn('"single"', self.js)
        self.assertIn('"market_research"', self.js)

    def test_settings_and_data_system_are_clickable_workspace_targets(self) -> None:
        self.assertIn('data-command-workspace="settings" data-command-route="/settings?tab=data-system"', self.html)
        self.assertIn('data-workspace="settings" data-route-alias="/settings"', self.html)
        self.assertIn("WORKSPACES.settings", self.js)
        self.assertIn('setActiveWorkspace("settings"', self.js)

    def test_owner_docs_define_three_basic_files_and_ledger_standard(self) -> None:
        dev_record = (self.root / "开发记录.md").read_text(encoding="utf-8")
        feature_list = (self.root / "功能清单.md").read_text(encoding="utf-8")
        parameter_file = (self.root / "模型参数文件.md").read_text(encoding="utf-8")
        standard = (self.root / "docs" / "pfi_v02" / "LEDGER_CLASSIFICATION_STANDARD.md").read_text(encoding="utf-8")

        self.assertIn("开发日志", dev_record)
        self.assertIn("不全文复制 roadmap", dev_record)
        self.assertIn("功能目录", feature_list)
        self.assertIn("不记录逐轮开发流水", feature_list)
        self.assertIn("参数与规则依据", parameter_file)
        self.assertIn("规则优先级", parameter_file)
        self.assertIn("LCS-001", standard)
        self.assertIn("消费账户", standard)
        self.assertIn("复核阈值", standard)


if __name__ == "__main__":
    unittest.main()
