from __future__ import annotations

import unittest
from pathlib import Path

from pfi_v02.stage_v021_frontend_contract import (
    STAGE3_TASK_IDS,
    build_v021_stage3_contract,
)


class V021Stage3SettingsSearchContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.html = (self.root / "web" / "index.html").read_text(encoding="utf-8")
        self.js = (self.root / "web" / "app" / "shell.js").read_text(encoding="utf-8")
        self.css = (self.root / "web" / "styles" / "tokens.css").read_text(encoding="utf-8")
        self.web_source = "\n".join((self.html, self.js, self.css))

    def test_stage3_contract_covers_settings_and_global_search_tasks(self) -> None:
        contract = build_v021_stage3_contract()

        self.assertEqual(contract["schema"], "PFIV021FrontendOptimizationStage3ContractV1")
        self.assertEqual(tuple(contract["task_ids"]), STAGE3_TASK_IDS)
        self.assertEqual(contract["settings_contract"]["route"], "/settings")
        self.assertEqual(contract["settings_contract"]["presentation"], "primary_workspace")
        self.assertFalse(contract["settings_contract"]["default_business_pages_show_settings_sidebar"])
        self.assertIn("V021-P3-S3-T01", contract["task_ids"])
        self.assertIn("V021-P3-S3-T02", contract["task_ids"])

    def test_settings_route_is_primary_workspace_not_right_side_settings_panel(self) -> None:
        contract = build_v021_stage3_contract()

        self.assertIn('data-workspace="settings" data-route-alias="/settings"', self.html)
        self.assertIn('data-command-workspace="settings" data-command-route="/settings?tab=data-system"', self.html)
        self.assertIn('"/data-system": "/settings?tab=data-system"', self.js)
        self.assertIn('main.dataset.settingsSurface = workspaceId === "settings" ? "primary_workspace" : "none"', self.js)
        self.assertIn("data-settings-feedback-console", self.html)
        self.assertIn('settingsConsole.hidden = workspaceId !== "settings"', self.js)
        self.assertIn("syncBrowserRoute", self.js)
        self.assertIn("workspaceTargetFromRoute", self.js)
        self.assertIn("routeAliasFromLocation", self.js)
        for forbidden in contract["settings_contract"]["forbidden_surfaces"]:
            self.assertNotIn(forbidden, self.web_source)

    def test_feedback_console_controls_are_visible_only_as_settings_capabilities(self) -> None:
        contract = build_v021_stage3_contract()

        for control in contract["settings_contract"]["feedback_controls"]:
            self.assertIn(control, self.js)
        self.assertIn("运行反馈控制台", self.js)
        self.assertIn("触感反馈强度", self.js)
        self.assertIn("声音反馈", self.js)
        self.assertIn("视觉反馈", self.js)
        self.assertIn("通知反馈", self.js)
        self.assertIn("业务页默认不常驻反馈控制台", self.js)

    def test_global_search_dom_contract_and_fuzzy_functions_exist(self) -> None:
        search = build_v021_stage3_contract()["global_search_contract"]

        self.assertIn('data-search-surface="global"', self.html)
        self.assertIn('id="global-search"', self.html)
        self.assertIn('data-global-search-input', self.html)
        self.assertIn('role="combobox"', self.html)
        self.assertIn('aria-controls="global-search-results"', self.html)
        self.assertIn('id="global-search-results"', self.html)
        self.assertIn('role="listbox"', self.html)
        self.assertIn(".global-search-results", self.css)
        self.assertIn("buildGlobalSearchIndex", self.js)
        self.assertIn("fuzzySearchItems", self.js)
        self.assertIn("subsequenceScore", self.js)
        self.assertIn("SEARCH_ALIASES", self.js)
        self.assertIn("handleGlobalSearchKeydown", self.js)
        self.assertIn("focusGlobalSearch", self.js)
        self.assertEqual(search["empty_state"], "没有匹配结果")

    def test_global_search_scope_and_keyboard_contract_are_locked(self) -> None:
        search = build_v021_stage3_contract()["global_search_contract"]

        for scope in ("15 个一级导航入口", "工作区功能卡", "功能面板", "任务中心条目", "决策队列表格行", "设置页反馈控制项"):
            self.assertIn(scope, search["scope"])
        for mode in ("substring", "subsequence", "alias_keywords"):
            self.assertIn(mode, search["fuzzy_match_modes"])
        for key in ("ArrowDown", "ArrowUp", "Enter", "Escape", "Meta/Ctrl+K"):
            self.assertIn(key, search["keyboard_contract"])
        self.assertIn("VS Code / Google Chrome", search["ui_reference"])


if __name__ == "__main__":
    unittest.main()
