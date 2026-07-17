from __future__ import annotations

import unittest
from pathlib import Path

from playwright.sync_api import Browser, Page, Playwright, sync_playwright

from KMFA.tools import run_v015_s16_p3_homepage_usability as runtime


REPO_ROOT = Path(__file__).resolve().parents[2]
SCREENSHOT_ROOT = REPO_ROOT / "KMFA/stage_artifacts/V015_S16_P3_HOMEPAGE_USABILITY_ACCEPTANCE/exports/screenshots"


class HomepageUsabilityBrowserTests(unittest.TestCase):
    playwright: Playwright
    browser: Browser

    @classmethod
    def setUpClass(cls) -> None:
        cls.server, cls.server_thread, cls.base_url = runtime.start_server()
        cls.playwright = sync_playwright().start()
        chrome = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
        cls.browser = cls.playwright.chromium.launch(
            headless=True,
            executable_path=str(chrome) if chrome.is_file() else None,
        )
        SCREENSHOT_ROOT.mkdir(parents=True, exist_ok=True)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.browser.close()
        cls.playwright.stop()
        cls.server.shutdown()
        cls.server.server_close()
        cls.server_thread.join(timeout=3)

    def new_page(self, width: int = 1440, height: int = 1000) -> tuple[Page, list[str]]:
        page = self.browser.new_page(viewport={"width": width, "height": height})
        page.set_default_timeout(10_000)
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on(
            "console",
            lambda message: errors.append(message.text)
            if message.type == "error" and not message.text.startswith("Failed to load resource:")
            else None,
        )
        return page, errors

    def wait_ready(self, page: Page) -> None:
        page.locator("#homepage-view").wait_for(state="visible")
        page.locator("#scan-summary", has_text="公开演示显示").wait_for()
        page.locator("#priority-preview li").nth(2).wait_for()
        page.locator("#homepage-metrics .summary-item").nth(4).wait_for()
        page.locator("#homepage-feedback", has_text="资料已核对").wait_for()
        page.wait_for_function("() => window.KMFA_HOMEPAGE_USABILITY_TEST?.snapshot()?.usability_state === 'ready'")

    def set_fault(self, page: Page, state: str) -> None:
        page.evaluate("state => window.KMFA_HOMEPAGE_USABILITY_TEST.setState(state)", state)
        page.wait_for_function(
            "state => window.KMFA_HOMEPAGE_USABILITY_TEST?.snapshot()?.usability_state === state",
            arg=state,
        )
        page.locator("#homepage-state-panel").wait_for(state="visible")

    def assert_first_scan_visible(self, page: Page, viewport_height: int) -> None:
        self.assertLessEqual(
            page.locator("#ten-second-overview").evaluate("node => Math.ceil(node.getBoundingClientRect().bottom)"),
            viewport_height,
        )
        self.assertEqual(page.locator("#priority-preview li").count(), 3)
        self.assertLessEqual(
            page.locator("#priority-preview li").nth(2).evaluate("node => Math.ceil(node.getBoundingClientRect().bottom)"),
            viewport_height,
        )

    def test_01_desktop_first_scan_exposes_state_three_priorities_and_next_step(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/overview", wait_until="networkidle")
            self.wait_ready(page)
            self.assert_first_scan_visible(page, 1000)
            summary = page.locator("#scan-summary").inner_text()
            self.assertIn("可用资金", summary)
            self.assertIn("预计净流入", summary)
            self.assertIn("逾期应收", summary)
            self.assertIn("先处理回款", summary)
            self.assertIn("核对逾期回款", page.locator("#priority-preview li").first.inner_text())
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_homepage_ten_second.png"), full_page=False)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_02_mobile_first_scan_is_visible_without_horizontal_overflow(self) -> None:
        page, errors = self.new_page(390, 844)
        try:
            page.goto(self.base_url + "/overview", wait_until="networkidle")
            self.wait_ready(page)
            self.assertTrue(page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1"))
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_homepage_mobile.png"), full_page=False)
            self.assert_first_scan_visible(page, 844)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def _assert_one_click_path(self, selector: str, target: str, expected_title: str) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/overview", wait_until="networkidle")
            self.wait_ready(page)
            link = page.locator(selector).first
            self.assertTrue(link.is_visible())
            link.click()
            page.wait_for_url(f"**{target}**")
            page.locator("#page-title", has_text=expected_title).wait_for()
            self.assertNotEqual(page.locator("#not-found-view").get_attribute("hidden"), None)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_03_projects_open_in_one_click(self) -> None:
        self._assert_one_click_path('#homepage-focus a[data-route="/projects"]', "/projects", "项目")

    def test_04_collection_issue_opens_in_one_click(self) -> None:
        self._assert_one_click_path('#homepage-focus a[data-route="/collections"]', "/collections", "回款")

    def test_05_reports_open_in_one_click(self) -> None:
        self._assert_one_click_path('nav a[data-route="/reports"]', "/reports", "报告")

    def test_06_empty_state_has_reason_impact_action_and_no_fake_zero(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/overview", wait_until="networkidle")
            self.wait_ready(page)
            self.set_fault(page, "empty")
            panel = page.locator("#homepage-state-panel")
            self.assertIn("没有可用资料", panel.inner_text())
            self.assertIn("不会用 0", panel.inner_text())
            self.assertIn("前往数据更新", panel.inner_text())
            self.assertTrue(page.locator("#ten-second-overview").is_hidden())
            self.assertTrue(page.locator("#business-summary-section").is_hidden())
            self.assertEqual(page.locator("#homepage-metrics .summary-item").count(), 0)
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_homepage_empty.png"), full_page=False)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_07_error_state_is_actionable_and_retry_recovers(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/overview", wait_until="networkidle")
            self.wait_ready(page)
            self.set_fault(page, "error")
            panel = page.locator("#homepage-state-panel")
            self.assertIn("暂时无法读取", panel.inner_text())
            self.assertIn("重新加载", panel.inner_text())
            self.assertTrue(page.locator("#business-summary-section").is_hidden())
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_homepage_error.png"), full_page=False)
            page.locator("#homepage-state-action").click()
            self.wait_ready(page)
            self.assertTrue(page.locator("#homepage-state-panel").is_hidden())
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_08_stale_state_blocks_old_values_and_routes_to_update(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/overview", wait_until="networkidle")
            self.wait_ready(page)
            self.set_fault(page, "stale")
            panel = page.locator("#homepage-state-panel")
            self.assertIn("资料已过期", panel.inner_text())
            self.assertIn("判断已暂停", panel.inner_text())
            self.assertEqual(page.locator("#homepage-state-action").get_attribute("data-route"), "/data-update")
            self.assertTrue(page.locator("#homepage-columns").is_hidden())
            self.assertEqual(page.locator("#homepage-metrics .summary-item").count(), 0)
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_homepage_stale.png"), full_page=False)
            self.assertEqual(errors, [])
        finally:
            page.close()


if __name__ == "__main__":
    unittest.main()
