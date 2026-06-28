from __future__ import annotations

import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

import pfi_v02.stage_v0211_ui_recovery as recovery


class VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._ignored_depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self._ignored_depth:
            self._ignored_depth += 1
            return
        if tag in {"script", "style"}:
            self._ignored_depth += 1
            return
        attr_map = {key: value or "" for key, value in attrs}
        if "hidden" in attr_map:
            self._ignored_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"} and self._ignored_depth:
            self._ignored_depth -= 1
            return
        if self._ignored_depth:
            self._ignored_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._ignored_depth:
            return
        clean = " ".join(data.split())
        if clean:
            self.parts.append(clean)


def visible_text(html: str) -> str:
    parser = VisibleTextParser()
    parser.feed(html)
    return "\n".join(parser.parts)


class V0211Stage2PageSkeletonContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.html = (self.root / "web" / "index.html").read_text(encoding="utf-8")
        self.js = (self.root / "web" / "app" / "shell.js").read_text(encoding="utf-8")

    def test_contract_locks_stage2_scope_and_page_skeletons(self) -> None:
        self.assertTrue(hasattr(recovery, "build_v0211_stage2_contract"))
        contract = recovery.build_v0211_stage2_contract()

        self.assertEqual(contract["stage"], "S2 页面骨架与去 AI 化")
        self.assertEqual(contract["task_id"], "V0211-S2-T01")
        self.assertIn("清理正式 UI 中开发者词", "\n".join(contract["delivery_focus"]))
        self.assertIn("不做数据库 migration", "\n".join(contract["forbidden_work"]))
        self.assertIn("不伪造趋势数据", "\n".join(contract["forbidden_work"]))
        self.assertEqual(set(contract["page_skeletons"]), set(recovery.STAGE2_PAGE_SKELETONS))
        self.assertEqual(
            tuple(contract["page_skeletons"]["sync"]["secondary_tabs"]),
            ("上传中心", "导入中心", "数据源管理", "待复核", "导入历史"),
        )
        self.assertIn("策略实验室", contract["page_skeletons"]["market_research"]["secondary_tabs"])

    def test_shell_has_real_secondary_tabs_for_each_primary_page(self) -> None:
        self.assertIn('data-secondary-tabs', self.html)
        self.assertIn("renderSecondaryTabs", self.js)

        for workspace_id, skeleton in recovery.STAGE2_PAGE_SKELETONS.items():
            self.assertIn(f"{workspace_id}: [", self.js)
            for tab in skeleton.secondary_tabs:
                self.assertIn(tab, self.js)

    def test_default_visible_shell_has_no_developer_or_demo_pollution(self) -> None:
        text = visible_text(self.html)
        forbidden = (
            "运行边界",
            "使用限制",
            "隐私边界",
            "不做实盘自动下单",
            "Task Pack",
            "Demo",
            "Prototype",
            "AI 演示",
            "运行反馈控制台",
            "多模态交互反馈",
            "手机预览",
            "证据抽屉",
            "运行证据",
            "任务中心",
        )
        for phrase in forbidden:
            self.assertNotIn(phrase, text)

    def test_home_shell_uses_owner_task_language(self) -> None:
        text = visible_text(self.html)

        for phrase in ("净资产", "现金余额", "投资市值", "本月支出", "待复核交易", "数据源状态"):
            self.assertIn(phrase, text)
        for phrase in ("上传数据", "复核流水", "查看投资", "生成报告"):
            self.assertIn(phrase, text)
        self.assertNotRegex(text, re.compile(r"\b(runtime|Boundary|Evidence|Source|Model)\b"))

    def test_settings_feedback_is_not_a_default_business_page_panel(self) -> None:
        main_before_settings = self.html.split('<section class="settings-feedback-console"', 1)[0]

        self.assertNotIn("反馈偏好", main_before_settings)
        self.assertIn('data-settings-feedback-console hidden', self.html)
        self.assertIn("反馈偏好", self.js)


if __name__ == "__main__":
    unittest.main()
