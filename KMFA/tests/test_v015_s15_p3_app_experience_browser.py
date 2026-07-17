from __future__ import annotations

import unittest
from pathlib import Path

from playwright.sync_api import Browser, Page, Playwright, sync_playwright

from KMFA.tools import run_v015_s15_p3_app_experience as runtime


REPO_ROOT = Path(__file__).resolve().parents[2]
SCREENSHOT_ROOT = REPO_ROOT / "KMFA/stage_artifacts/V015_S15_P3_APP_EXPERIENCE/exports/screenshots"


class AppExperienceBrowserTests(unittest.TestCase):
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

    def setUp(self) -> None:
        with self.server.experience_store.lock:
            self.server.experience_store.recent_by_user.clear()
            self.server.experience_store.preferences_by_user.clear()
            self.server.experience_store.preference_revision.clear()

    def new_page(self, width: int = 1440, height: int = 1000) -> tuple[Page, list[str]]:
        page = self.browser.new_page(viewport={"width": width, "height": height})
        page.set_default_timeout(8_000)
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
        page.locator("#page-view:not([hidden])").wait_for()
        page.locator("#context-status strong", has_text="已更新").wait_for()
        page.locator('#role-feedback[data-state="allowed"]').wait_for()
        page.locator("#experience-workspace").wait_for()
        page.wait_for_function("() => Boolean(window.KMFA_EXPERIENCE_TEST && window.KMFA_ROLE_TEST)")

    def test_01_search_source_navigation_and_recent_survive_reload(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/overview", wait_until="networkidle")
            self.wait_ready(page)
            page.fill("#global-search", "报告")
            page.locator("#global-search-form button[type=submit]").click()
            page.locator("#search-results .result-title", has_text="月度经营报告").wait_for()
            self.assertIn("经营报告中心", page.locator("#search-results").inner_text())
            page.locator('#search-results [data-recent-item="SEARCH-REPORT-MONTHLY"]').click()
            page.wait_for_url("**/reports/demo-business-report?**")
            page.locator("#page-title", has_text="示例经营报告").wait_for()
            page.locator('[data-open-experience="search"]').click()
            page.locator("#recent-list a", has_text="月度经营报告").wait_for()
            page.reload(wait_until="networkidle")
            self.wait_ready(page)
            page.locator("#recent-list a", has_text="月度经营报告").wait_for()
            page.fill("#global-search", "报告")
            page.locator("#global-search-form button[type=submit]").click()
            page.locator("#search-results .result-title", has_text="月度经营报告").wait_for()
            SCREENSHOT_ROOT.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_app_experience_search.png"), full_page=False)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_02_sensitive_search_is_removed_and_rechecked_after_role_change(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/overview", wait_until="networkidle")
            self.wait_ready(page)
            page.fill("#global-search", "敏感来源")
            page.locator("#global-search-form button[type=submit]").click()
            page.locator("#experience-feedback", has_text="没有可查看").wait_for()
            self.assertNotIn("敏感来源核对", page.locator("#search-results").inner_text())
            page.evaluate("window.KMFA_ROLE_TEST.setIdentity('demo-owner','finance')")
            page.locator("#active-role-chip", has_text="财务").wait_for()
            page.evaluate("window.KMFA_EXPERIENCE_TEST.search('敏感来源','ALL')")
            page.locator("#search-results .result-title", has_text="敏感来源核对").wait_for()
            page.evaluate("window.KMFA_ROLE_TEST.setIdentity('demo-owner','management')")
            page.locator("#active-role-chip", has_text="经营负责人").wait_for()
            page.evaluate("window.KMFA_EXPERIENCE_TEST.search('敏感来源','ALL')")
            page.locator("#experience-feedback", has_text="没有可查看").wait_for()
            self.assertNotIn("敏感来源核对", page.locator("#search-results").inner_text())
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_03_notification_center_has_action_for_every_visible_item(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/overview", wait_until="networkidle")
            self.wait_ready(page)
            page.evaluate("window.KMFA_ROLE_TEST.setIdentity('demo-owner','finance')")
            page.locator("#active-role-chip", has_text="财务").wait_for()
            page.locator('[data-open-experience="notifications"]').click()
            page.locator("#notification-list .notification-row").nth(3).wait_for()
            self.assertEqual(page.locator("#notification-list .notification-row").count(), 4)
            self.assertEqual(page.locator("#notification-list .notification-row .result-action").count(), 4)
            categories = page.locator("#notification-list .notice-category").all_inner_texts()
            self.assertEqual(set(categories), {"数据更新", "差异", "报告", "风险事项"})
            self.assertTrue(all(text.strip() for text in page.locator("#notification-list .result-action").all_inner_texts()))
            SCREENSHOT_ROOT.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_app_experience_notifications.png"), full_page=False)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_04_preferences_persist_after_reload_without_auto_changing_facts(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/overview", wait_until="networkidle")
            self.wait_ready(page)
            original_company = page.input_value("#context-company")
            original_metric = page.locator("#metric-visible").inner_text()
            page.locator('[data-open-experience="preferences"]').click()
            page.select_option("#preference-company", "demo-west")
            page.select_option("#preference-period", "2026-H1")
            page.select_option("#preference-density", "comfortable")
            page.locator('#preference-columns input[value="updated_at"]').uncheck()
            page.locator("#preference-form button[type=submit]").click()
            page.locator('#experience-feedback[data-state="saved"]').wait_for()
            self.assertEqual(page.input_value("#context-company"), original_company)
            self.assertEqual(page.locator("#metric-visible").inner_text(), original_metric)
            self.assertEqual(page.get_attribute("body", "data-density"), "comfortable")
            page.reload(wait_until="networkidle")
            self.wait_ready(page)
            page.locator('[data-open-experience="preferences"]').click()
            page.wait_for_function("() => document.querySelector('#preference-company').value === 'demo-west'")
            self.assertEqual(page.input_value("#preference-period"), "2026-H1")
            self.assertEqual(page.input_value("#preference-density"), "comfortable")
            self.assertFalse(page.locator('#preference-columns input[value="updated_at"]').is_checked())
            self.assertEqual(page.input_value("#context-company"), original_company)
            SCREENSHOT_ROOT.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_app_experience_preferences.png"), full_page=False)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_05_preference_isolation_and_authorized_common_company(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/overview", wait_until="networkidle")
            self.wait_ready(page)
            page.locator('[data-open-experience="preferences"]').click()
            page.select_option("#preference-company", "demo-south")
            page.select_option("#preference-density", "comfortable")
            page.locator("#preference-form button[type=submit]").click()
            page.locator('#experience-feedback[data-state="saved"]').wait_for()
            page.select_option("#identity-user", "demo-finance")
            page.locator("#active-role-chip", has_text="财务").wait_for()
            page.wait_for_function("() => document.querySelector('#preference-company').value === 'demo-north'")
            self.assertEqual(page.input_value("#preference-density"), "compact")
            self.assertEqual(page.locator("#preference-company option").count(), 1)
            self.assertEqual(page.locator("#preference-company option").inner_text(), "北区示例公司")
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_06_keyboard_shortcut_tabs_and_mobile_layout_remain_usable(self) -> None:
        page, errors = self.new_page(390, 844)
        try:
            page.goto(self.base_url + "/overview", wait_until="networkidle")
            self.wait_ready(page)
            page.keyboard.press("Control+K")
            self.assertEqual(page.evaluate("document.activeElement.id"), "global-search")
            self.assertEqual(page.locator(".sidebar").count(), 0)
            page.locator("#tab-notifications").click()
            self.assertEqual(page.get_attribute("#tab-notifications", "aria-selected"), "true")
            page.locator("#notification-list .notification-row").nth(2).wait_for()
            self.assertTrue(page.locator("#global-search").is_visible())
            self.assertTrue(page.locator("#preference-form button[type=submit]").count() == 1)
            SCREENSHOT_ROOT.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_app_experience_mobile.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()


if __name__ == "__main__":
    unittest.main()
