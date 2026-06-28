from __future__ import annotations

import re
import unittest
from pathlib import Path

import pfi_v02.stage_v0211_ui_recovery as recovery


class V0211Stage1ProductShellContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.html = (self.root / "web" / "index.html").read_text(encoding="utf-8")
        self.js = (self.root / "web" / "app" / "shell.js").read_text(encoding="utf-8")

    def _side_nav_html(self) -> str:
        match = re.search(r'<nav class="side-nav"[\s\S]*?</nav>', self.html)
        self.assertIsNotNone(match)
        return match.group(0)

    def test_contract_locks_stage1_scope_and_acceptance(self) -> None:
        self.assertTrue(hasattr(recovery, "build_v0211_stage1_contract"))
        contract = recovery.build_v0211_stage1_contract()

        self.assertEqual(contract["stage"], "S1 产品壳与路由")
        self.assertEqual(contract["task_id"], "V0211-S1-T01")
        self.assertEqual(contract["primary_navigation_count"], 10)
        self.assertEqual(tuple(contract["primary_navigation"]), recovery.v0211_stage1_navigation_labels())
        self.assertIn("浏览器前进后退可用", "\n".join(contract["acceptance_gate"]))
        self.assertIn("不做图表", "\n".join(contract["forbidden_work"]))
        self.assertIn("不做持仓编辑", "\n".join(contract["forbidden_work"]))

    def test_formal_primary_navigation_has_only_ten_owner_entries(self) -> None:
        side_nav = self._side_nav_html()
        labels = tuple(
            re.findall(
                r'<button[^>]*data-primary-entry="true"[^>]*>([^<]+)</button>',
                side_nav,
            )
        )

        self.assertEqual(labels, recovery.v0211_stage1_navigation_labels())
        self.assertIn('data-primary-workspaces="10"', side_nav)
        self.assertEqual(side_nav.count('data-primary-entry="true"'), 10)
        self.assertNotIn("nav-alias", side_nav)
        self.assertNotIn('data-entry-type="v01_alias"', side_nav)
        for old_label in ("首页", "市场", "研究", "持仓", "策略实验室", "数据与系统"):
            self.assertNotIn(old_label, labels)

    def test_legacy_entries_are_route_aliases_not_main_navigation(self) -> None:
        contract = recovery.build_v0211_stage1_contract()

        self.assertEqual(contract["legacy_route_aliases"]["首页"], "/home")
        self.assertEqual(contract["legacy_route_aliases"]["市场"], "/market-research?tab=market")
        self.assertEqual(contract["legacy_route_aliases"]["研究"], "/market-research?tab=research")
        self.assertEqual(contract["legacy_route_aliases"]["持仓"], "/investment?tab=holdings")
        self.assertEqual(contract["legacy_route_aliases"]["策略实验室"], "/market-research/strategy-lab")
        self.assertEqual(contract["legacy_route_aliases"]["数据与系统"], "/settings?tab=data-system")
        self.assertIn("LEGACY_ROUTE_ALIAS_TARGETS", self.js)
        self.assertIn('"/strategy-lab": "/market-research/strategy-lab"', self.js)

    def test_shell_uses_real_route_state_and_browser_back_forward(self) -> None:
        self.assertIn("pushState", self.js)
        self.assertIn("popstate", self.js)
        self.assertIn("skipRouteSync", self.js)
        self.assertIn('"/market-research/strategy-lab"', self.js)
        self.assertNotIn('"/investment/strategy-lab"', self._side_nav_html())

    def test_home_page_does_not_default_to_settings_or_demo_pollution(self) -> None:
        main_prefix = self.html.split('<section class="settings-feedback-console"', 1)[0]

        for forbidden in (
            "运行边界",
            "Task Pack",
            "Demo",
            "Prototype",
            "手机预览",
            "运行反馈控制台",
            "多模态交互反馈",
        ):
            self.assertNotIn(forbidden, main_prefix)
        self.assertIn('data-settings-feedback-console hidden', self.html)
        self.assertIn("数据源与上传", self.html)
        self.assertIn("市场与研究", self.html)


if __name__ == "__main__":
    unittest.main()
