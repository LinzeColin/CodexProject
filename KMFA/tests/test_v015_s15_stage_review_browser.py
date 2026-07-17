from __future__ import annotations

import unittest
from pathlib import Path

from playwright.sync_api import Browser, Page, Playwright, sync_playwright

from KMFA.tools import run_v015_s15_p3_app_experience as runtime


REPO_ROOT = Path(__file__).resolve().parents[2]
SCREENSHOT_ROOT = REPO_ROOT / "KMFA/stage_artifacts/V015_S15_STAGE_REVIEW/exports/screenshots"


class S15StageReviewBrowserTests(unittest.TestCase):
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
        with self.server.authorization_store.lock:
            self.server.authorization_store.events.clear()
            self.server.authorization_store.requests.clear()

    def new_page(
        self, width: int = 1440, height: int = 1000, *, touch: bool = False
    ) -> tuple[Page, list[str]]:
        page = self.browser.new_page(
            viewport={"width": width, "height": height}, has_touch=touch
        )
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
        page.locator("#page-view:not([hidden])").wait_for()
        page.locator("#context-status strong", has_text="已更新").wait_for()
        page.locator('#role-feedback[data-state="allowed"]').wait_for()
        page.wait_for_function(
            "() => Boolean(window.KMFA_EXPERIENCE_TEST && window.KMFA_ROLE_TEST)"
        )
        page.wait_for_function(
            "() => !document.querySelector('#apply-preferred-context').disabled"
        )

    def test_01_all_three_parts_share_one_live_page(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/overview", wait_until="networkidle")
            self.wait_ready(page)
            self.assertEqual(page.locator("#primary-nav a").count(), 7)
            self.assertEqual(page.locator("#context-form select").count(), 4)
            self.assertEqual(page.locator("#permission-body tr").count(), 5)
            self.assertEqual(page.locator('[role="tab"]').count(), 3)
            page.fill("#global-search", "报告")
            page.locator("#global-search-form button[type=submit]").click()
            page.locator("#search-results .result-title", has_text="月度经营报告").wait_for()
            SCREENSHOT_ROOT.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_s15_review_desktop.png"))
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_02_stale_identity_and_sensitive_search_responses_are_ignored(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/overview", wait_until="networkidle")
            self.wait_ready(page)
            page.evaluate(
                """() => {
                  const original = window.fetch.bind(window);
                  window.fetch = (input, options) => {
                    const url = String(input);
                    const response = original(input, options);
                    const parsed = new URL(url, location.origin);
                    const delayed = parsed.searchParams.get('role_id') === 'finance' &&
                      (parsed.pathname === '/api/identity' || parsed.pathname === '/api/search');
                    return delayed ? response.then(value => new Promise(resolve => setTimeout(() => resolve(value), 350))) : response;
                  };
                }"""
            )
            page.evaluate(
                "() => { void window.KMFA_ROLE_TEST.setIdentity('demo-owner','finance'); }"
            )
            page.evaluate("window.KMFA_ROLE_TEST.setIdentity('demo-owner','management')")
            page.locator("#active-role-chip", has_text="经营负责人").wait_for()
            page.evaluate("window.KMFA_ROLE_TEST.setIdentity('demo-owner','finance')")
            page.locator("#active-role-chip", has_text="财务").wait_for()
            page.evaluate(
                "() => { void window.KMFA_EXPERIENCE_TEST.search('敏感来源','ALL'); }"
            )
            page.evaluate("window.KMFA_ROLE_TEST.setIdentity('demo-owner','management')")
            page.locator("#active-role-chip", has_text="经营负责人").wait_for()
            page.wait_for_timeout(500)
            self.assertNotIn("敏感来源核对", page.locator("#search-results").inner_text())
            self.assertIn("经营负责人", page.locator("#active-role-chip").inner_text())
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_03_restricted_user_is_moved_to_an_authorized_company(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/overview", wait_until="networkidle")
            self.wait_ready(page)
            page.select_option("#context-company", "demo-south")
            page.locator("#context-status", has_text="南区示例公司").wait_for()
            page.select_option("#identity-user", "demo-finance")
            page.wait_for_function(
                "() => document.querySelector('#context-company').value === 'demo-north'"
            )
            page.locator("#active-role-chip", has_text="财务").wait_for()
            page.locator('#role-feedback[data-state="allowed"]').wait_for()
            self.assertEqual(page.input_value("#context-company"), "demo-north")
            SCREENSHOT_ROOT.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_s15_review_restricted_user.png"))
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_04_tablist_supports_arrow_home_and_end_keys(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/overview", wait_until="networkidle")
            self.wait_ready(page)
            page.locator("#tab-search").focus()
            page.keyboard.press("ArrowRight")
            self.assertEqual(page.evaluate("document.activeElement.id"), "tab-notifications")
            self.assertEqual(page.get_attribute("#tab-notifications", "aria-selected"), "true")
            page.keyboard.press("End")
            self.assertEqual(page.evaluate("document.activeElement.id"), "tab-preferences")
            self.assertEqual(page.get_attribute("#tab-preferences", "aria-selected"), "true")
            page.keyboard.press("Home")
            self.assertEqual(page.evaluate("document.activeElement.id"), "tab-search")
            self.assertEqual(page.get_attribute("#tab-search", "aria-selected"), "true")
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_05_search_and_notification_routes_keep_global_context(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/overview", wait_until="networkidle")
            self.wait_ready(page)
            page.select_option("#context-period", "2026-Q2")
            page.fill("#global-search", "报告")
            page.locator("#global-search-form button[type=submit]").click()
            page.locator('#search-results [data-recent-item="SEARCH-REPORT-MONTHLY"]').click()
            page.wait_for_url("**/reports/demo-business-report?**")
            self.assertIn("period=2026-Q2", page.url)
            page.locator('[data-open-experience="notifications"]').click()
            page.locator("#notification-list .notification-row").nth(2).wait_for()
            page.locator("#notification-list .result-action").first.click()
            page.wait_for_url("**/data-update/check-result?**")
            self.assertIn("period=2026-Q2", page.url)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_06_old_user_preferences_cannot_be_applied_during_identity_change(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/overview", wait_until="networkidle")
            self.wait_ready(page)
            page.locator('[data-open-experience="preferences"]').click()
            page.select_option("#preference-company", "demo-west")
            page.locator("#preference-form button[type=submit]").click()
            page.locator('#experience-feedback[data-state="saved"]').wait_for()
            page.evaluate(
                """() => {
                  const original = window.fetch.bind(window);
                  window.fetch = (input, options) => {
                    const url = String(input);
                    const response = original(input, options);
                    return url.includes('/api/preferences?') && url.includes('demo-finance')
                      ? response.then(value => new Promise(resolve => setTimeout(() => resolve(value), 300)))
                      : response;
                  };
                }"""
            )
            page.select_option("#identity-user", "demo-finance")
            page.wait_for_function(
                "() => document.querySelector('#apply-preferred-context').disabled"
            )
            page.wait_for_function(
                "() => !document.querySelector('#apply-preferred-context').disabled"
            )
            self.assertEqual(page.input_value("#preference-company"), "demo-north")
            self.assertEqual(page.input_value("#context-company"), "demo-north")
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_07_tablet_layout_has_no_horizontal_overflow(self) -> None:
        page, errors = self.new_page(820, 1180, touch=True)
        try:
            page.goto(self.base_url + "/overview", wait_until="networkidle")
            self.wait_ready(page)
            page.locator('[data-open-experience="notifications"]').click()
            page.locator("#notification-list .notification-row").nth(2).wait_for()
            overflow = page.evaluate(
                "document.documentElement.scrollWidth - document.documentElement.clientWidth"
            )
            self.assertLessEqual(overflow, 1)
            SCREENSHOT_ROOT.mkdir(parents=True, exist_ok=True)
            page.screenshot(
                path=str(SCREENSHOT_ROOT / "kmfa_s15_review_tablet.png"), full_page=True
            )
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_08_mobile_touch_targets_and_full_flow_remain_usable(self) -> None:
        page, errors = self.new_page(390, 844, touch=True)
        try:
            page.goto(self.base_url + "/overview", wait_until="networkidle")
            self.wait_ready(page)
            self.assertTrue(page.evaluate("matchMedia('(pointer:coarse)').matches"))
            page.locator("#tab-search").focus()
            page.keyboard.press("ArrowRight")
            page.locator("#notification-list .notification-row").nth(2).wait_for()
            heights = page.evaluate(
                """() => [...document.querySelectorAll('.quick-actions button,.experience-tabs button,.notification-row .result-action')]
                  .filter(node => node.offsetParent !== null).map(node => node.getBoundingClientRect().height)"""
            )
            self.assertTrue(heights and min(heights) >= 44)
            overflow = page.evaluate(
                "document.documentElement.scrollWidth - document.documentElement.clientWidth"
            )
            self.assertLessEqual(overflow, 1)
            SCREENSHOT_ROOT.mkdir(parents=True, exist_ok=True)
            page.screenshot(
                path=str(SCREENSHOT_ROOT / "kmfa_s15_review_mobile.png"), full_page=True
            )
            self.assertEqual(errors, [])
        finally:
            page.close()


if __name__ == "__main__":
    unittest.main()
