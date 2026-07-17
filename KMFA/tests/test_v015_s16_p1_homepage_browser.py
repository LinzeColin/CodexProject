from __future__ import annotations

import unittest
from pathlib import Path

from playwright.sync_api import Browser, Page, Playwright, sync_playwright

from KMFA.tools import run_v015_s16_p1_homepage as runtime


REPO_ROOT = Path(__file__).resolve().parents[2]
SCREENSHOT_ROOT = REPO_ROOT / "KMFA/stage_artifacts/V015_S16_P1_HOMEPAGE_FIRST_SCREEN/exports/screenshots"


class HomepageBrowserTests(unittest.TestCase):
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
        page.locator("#homepage-metrics .summary-item").nth(4).wait_for()
        page.locator("#homepage-feedback", has_text="资料已核对").wait_for()
        page.wait_for_function("() => Boolean(window.KMFA_HOMEPAGE_TEST && window.KMFA_EXPERIENCE_TEST && window.KMFA_ROLE_TEST)")

    def test_01_desktop_summary_shows_source_cutoff_and_completeness(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/overview", wait_until="networkidle")
            self.wait_ready(page)
            self.assertEqual(page.locator("#homepage-metrics .summary-item").count(), 5)
            sources = page.locator("#homepage-metrics .summary-source").all_inner_texts()
            self.assertTrue(all("来源：" in value and "截止：2026-07-15" in value and "资料已齐" in value for value in sources))
            values = page.locator("#homepage-metrics .summary-value").all_inner_texts()
            self.assertTrue(all(value.strip() for value in values))
            self.assertNotIn("资料不足", values)
            SCREENSHOT_ROOT.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_homepage_desktop.png"), full_page=False)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_02_partial_data_is_visible_and_never_shown_as_zero(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/overview", wait_until="networkidle")
            self.wait_ready(page)
            page.evaluate("window.KMFA_HOMEPAGE_TEST.setDataState('partial')")
            page.locator('#homepage-feedback[data-state="incomplete"]', has_text="资料不完整").wait_for()
            overdue = page.locator('[data-metric-id="OVERDUE_RECEIVABLE"]')
            self.assertEqual(overdue.locator(".summary-value").inner_text(), "资料不足")
            self.assertIn("资料未齐", overdue.inner_text())
            self.assertNotIn("¥0", overdue.inner_text())
            snapshot = page.evaluate("window.KMFA_HOMEPAGE_TEST.snapshot()")
            self.assertFalse(snapshot["complete_management_conclusion_available"])
            SCREENSHOT_ROOT.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_homepage_partial.png"), full_page=False)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_03_five_focus_items_have_one_action_and_route_without_dead_end(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/overview", wait_until="networkidle")
            self.wait_ready(page)
            rows = page.locator("#homepage-focus .focus-row")
            self.assertEqual(rows.count(), 5)
            self.assertEqual(page.locator("#homepage-focus .primary-link").count(), 5)
            self.assertTrue(all(row.locator(".primary-link").count() == 1 for row in rows.all()))
            page.locator("#homepage-focus .primary-link", has_text="查看逾期回款").click()
            page.wait_for_url("**/collections?**")
            page.locator("#page-title", has_text="回款").wait_for()
            self.assertTrue(page.locator("#homepage-view").is_hidden())
            page.locator('[data-nav-id="overview"]').click()
            page.wait_for_url("**/overview?**")
            self.wait_ready(page)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_04_trends_have_visible_table_and_project_matrix_is_readable(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/overview", wait_until="networkidle")
            self.wait_ready(page)
            self.assertEqual(page.locator("#homepage-trends .trend-item").count(), 3)
            self.assertEqual(page.locator("#trend-table-body tr").count(), 3)
            self.assertEqual(page.locator("#trend-table-head th").count(), 5)
            self.assertEqual(page.locator("#portfolio-body tr").count(), 4)
            self.assertEqual(page.locator("#portfolio-body .status-text").count(), 4)
            self.assertIn("需要关注", page.locator("#portfolio-body").inner_text())
            self.assertNotIn("雷达", page.locator("#homepage-trends").inner_text())
            SCREENSHOT_ROOT.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_homepage_portfolio.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_05_company_period_and_restricted_user_refresh_without_leak(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/overview", wait_until="networkidle")
            self.wait_ready(page)
            original = page.locator('[data-metric-id="AVAILABLE_CASH"] .summary-value').inner_text()
            page.select_option("#context-company", "demo-south")
            page.wait_for_function("() => window.KMFA_HOMEPAGE_TEST.snapshot()?.context.company_id === 'demo-south'")
            south = page.locator('[data-metric-id="AVAILABLE_CASH"] .summary-value').inner_text()
            self.assertNotEqual(original, south)
            page.select_option("#context-period", "2026-Q2")
            page.wait_for_function("() => window.KMFA_HOMEPAGE_TEST.snapshot()?.context.period === '2026-Q2'")
            page.select_option("#identity-user", "demo-finance")
            page.wait_for_function("() => document.querySelector('#context-company').value === 'demo-north'")
            page.wait_for_function("() => window.KMFA_HOMEPAGE_TEST.snapshot()?.context.company_id === 'demo-north'")
            self.assertEqual(page.input_value("#context-company"), "demo-north")
            self.assertEqual(page.locator("#homepage-feedback").get_attribute("data-state"), None)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_06_mobile_layout_has_no_horizontal_overflow_and_actions_are_touchable(self) -> None:
        page, errors = self.new_page(390, 844)
        try:
            page.goto(self.base_url + "/overview", wait_until="networkidle")
            self.wait_ready(page)
            self.assertTrue(page.locator("#homepage-view").is_visible())
            self.assertEqual(page.locator("#homepage-metrics .summary-item").count(), 5)
            self.assertTrue(page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1"))
            action_heights = page.locator("#homepage-focus .primary-link").evaluate_all("nodes => nodes.map(node => node.getBoundingClientRect().height)")
            self.assertTrue(all(height >= 44 for height in action_heights))
            page.locator("#portfolio-body tr").nth(3).scroll_into_view_if_needed()
            self.assertTrue(page.locator("#portfolio-body tr").nth(3).is_visible())
            SCREENSHOT_ROOT.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_homepage_mobile.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()


if __name__ == "__main__":
    unittest.main()
