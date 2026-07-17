from __future__ import annotations

import unittest
from pathlib import Path

from playwright.sync_api import Browser, Page, Playwright, sync_playwright

from KMFA.tools import build_v015_s16_stage_review as builder
from KMFA.tools import run_v015_s16_p3_homepage_usability as runtime


class S16StageReviewBrowserTests(unittest.TestCase):
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
        builder.SCREENSHOT_ROOT.mkdir(parents=True, exist_ok=True)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.browser.close()
        cls.playwright.stop()
        cls.server.shutdown()
        cls.server.server_close()
        cls.server_thread.join(timeout=3)

    def new_page(
        self, width: int = 1440, height: int = 1000, *, touch: bool = False
    ) -> tuple[Page, list[str], list[str]]:
        page = self.browser.new_page(
            viewport={"width": width, "height": height},
            has_touch=touch,
            is_mobile=touch,
        )
        page.set_default_timeout(10_000)
        errors: list[str] = []
        external: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on(
            "console",
            lambda message: errors.append(message.text)
            if message.type == "error"
            and not message.text.startswith("Failed to load resource:")
            else None,
        )
        page.on(
            "request",
            lambda request: external.append(request.url)
            if not request.url.startswith(self.base_url)
            else None,
        )
        return page, errors, external

    def wait_ready(self, page: Page) -> None:
        page.locator("#homepage-view").wait_for(state="visible")
        page.locator("#priority-preview li").nth(2).wait_for()
        page.locator("#homepage-metrics .summary-item").nth(4).wait_for()
        page.locator("#homepage-feedback", has_text="资料已核对").wait_for()
        page.wait_for_function(
            "() => window.KMFA_HOMEPAGE_USABILITY_TEST?.snapshot()?.usability_state === 'ready'"
        )

    def wait_detail(self, page: Page) -> None:
        page.locator("#drilldown-view").wait_for(state="visible")
        page.locator("#drilldown-feedback", has_text="已核对").wait_for()
        page.wait_for_function("() => Boolean(window.KMFA_DRILLDOWN_TEST?.snapshot())")

    def assert_clean(self, errors: list[str], external: list[str]) -> None:
        self.assertEqual(errors, [])
        self.assertEqual(external, [])

    def test_01_desktop_home_detail_and_return_are_one_flow(self) -> None:
        page, errors, external = self.new_page()
        try:
            page.goto(self.base_url + "/overview", wait_until="networkidle")
            self.wait_ready(page)
            page.screenshot(path=str(builder.DESKTOP_SCREENSHOT_PATH), full_page=False)
            homepage_value = page.locator(
                '[data-metric-id="AVAILABLE_CASH"] .summary-value'
            ).inner_text()
            page.locator('[data-metric-id="AVAILABLE_CASH"] .summary-link').click()
            self.wait_detail(page)
            self.assertEqual(page.locator("#drilldown-value").inner_text(), homepage_value)
            page.locator("#drilldown-back").click()
            self.wait_ready(page)
            self.assert_clean(errors, external)
        finally:
            page.close()

    def test_02_all_four_filters_survive_drilldown(self) -> None:
        page, errors, external = self.new_page()
        try:
            page.goto(
                self.base_url
                + "/overview?company=demo-west&period=2026-H1&project_status=normal&report_version=approved",
                wait_until="networkidle",
            )
            self.wait_ready(page)
            page.locator(
                '[data-metric-id="PROJECT_GROSS_PROFIT"] .summary-link'
            ).click()
            self.wait_detail(page)
            snapshot = page.evaluate("window.KMFA_DRILLDOWN_TEST.snapshot()")
            self.assertEqual(
                {key: snapshot["context"][key] for key in (
                    "company", "period", "project_status", "report_version"
                )},
                {
                    "company": "demo-west",
                    "period": "2026-H1",
                    "project_status": "normal",
                    "report_version": "approved",
                },
            )
            page.screenshot(path=str(builder.DRILLDOWN_SCREENSHOT_PATH), full_page=True)
            self.assert_clean(errors, external)
        finally:
            page.close()

    def test_03_delayed_old_company_response_is_ignored(self) -> None:
        page, errors, external = self.new_page()
        try:
            page.add_init_script(
                """() => {
                  const original = window.fetch.bind(window);
                  window.fetch = (input, options) => {
                    const url = new URL(String(input), location.origin);
                    const response = original(input, options);
                    const oldCompany = url.pathname === '/api/homepage' &&
                      url.searchParams.get('company_id') === 'demo-north';
                    return oldCompany
                      ? response.then(value => new Promise(resolve => setTimeout(() => resolve(value), 450)))
                      : response;
                  };
                }"""
            )
            page.goto(self.base_url + "/overview", wait_until="domcontentloaded")
            page.locator("#context-company").select_option("demo-west")
            page.wait_for_function(
                "() => window.KMFA_HOMEPAGE_TEST?.snapshot()?.context?.company_id === 'demo-west'"
            )
            page.wait_for_function(
                "() => window.KMFA_HOMEPAGE_USABILITY_TEST?.snapshot()?.context?.company_id === 'demo-west'"
            )
            page.wait_for_timeout(550)
            self.assertEqual(page.input_value("#context-company"), "demo-west")
            self.assertGreaterEqual(
                page.evaluate(
                    "window.KMFA_HOMEPAGE_USABILITY_STATE.ignoredStaleResponses()"
                ),
                1,
            )
            self.assert_clean(errors, external)
        finally:
            page.close()

    def test_04_fault_state_has_one_visible_announcement(self) -> None:
        page, errors, external = self.new_page()
        try:
            page.goto(self.base_url + "/overview", wait_until="networkidle")
            self.wait_ready(page)
            page.evaluate("window.KMFA_HOMEPAGE_USABILITY_TEST.setState('error')")
            page.locator("#homepage-state-panel").wait_for(state="visible")
            self.assertTrue(page.locator("#homepage-feedback").is_hidden())
            self.assertEqual(page.locator('[aria-live]:visible').count(), 1)
            page.screenshot(path=str(builder.FAULT_SCREENSHOT_PATH), full_page=False)
            self.assert_clean(errors, external)
        finally:
            page.close()

    def test_05_empty_and_stale_states_hide_unverified_values(self) -> None:
        page, errors, external = self.new_page()
        try:
            page.goto(self.base_url + "/overview", wait_until="networkidle")
            self.wait_ready(page)
            for state in ("empty", "stale"):
                page.evaluate(
                    "state => window.KMFA_HOMEPAGE_USABILITY_TEST.setState(state)",
                    state,
                )
                page.wait_for_function(
                    "state => window.KMFA_HOMEPAGE_USABILITY_TEST.snapshot()?.usability_state === state",
                    arg=state,
                )
                self.assertTrue(page.locator("#ten-second-overview").is_hidden())
                self.assertTrue(page.locator("#business-summary-section").is_hidden())
                self.assertEqual(page.locator("#homepage-metrics .summary-item").count(), 0)
            self.assert_clean(errors, external)
        finally:
            page.close()

    def test_06_touch_context_controls_are_at_least_44_pixels(self) -> None:
        page, errors, external = self.new_page(390, 844, touch=True)
        try:
            page.goto(self.base_url + "/overview", wait_until="networkidle")
            self.wait_ready(page)
            self.assertTrue(page.evaluate("matchMedia('(pointer:coarse)').matches"))
            heights = page.locator("#context-form select").evaluate_all(
                "nodes => nodes.map(node => node.getBoundingClientRect().height)"
            )
            self.assertEqual(len(heights), 4)
            self.assertGreaterEqual(min(heights), 44)
            page.screenshot(path=str(builder.MOBILE_SCREENSHOT_PATH), full_page=True)
            self.assert_clean(errors, external)
        finally:
            page.close()

    def test_07_mobile_first_scan_and_report_navigation_are_reachable(self) -> None:
        page, errors, external = self.new_page(390, 844, touch=True)
        try:
            page.goto(self.base_url + "/overview", wait_until="networkidle")
            self.wait_ready(page)
            self.assertLessEqual(
                page.locator("#priority-preview li").nth(2).evaluate(
                    "node => Math.ceil(node.getBoundingClientRect().bottom)"
                ),
                844,
            )
            self.assertTrue(
                page.evaluate(
                    "document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1"
                )
            )
            report = page.locator('[data-nav-id="reports"]')
            report.scroll_into_view_if_needed()
            report.focus()
            self.assertEqual(
                page.evaluate("document.activeElement.dataset.navId"), "reports"
            )
            page.keyboard.press("Enter")
            page.wait_for_url("**/reports?**")
            self.assert_clean(errors, external)
        finally:
            page.close()

    def test_08_tablet_has_no_horizontal_overflow(self) -> None:
        page, errors, external = self.new_page(820, 1180)
        try:
            page.goto(self.base_url + "/overview", wait_until="networkidle")
            self.wait_ready(page)
            self.assertTrue(
                page.evaluate(
                    "document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1"
                )
            )
            page.screenshot(path=str(builder.TABLET_SCREENSHOT_PATH), full_page=True)
            self.assert_clean(errors, external)
        finally:
            page.close()

    def test_09_keyboard_focus_and_reduced_motion_are_supported(self) -> None:
        page, errors, external = self.new_page()
        try:
            page.emulate_media(reduced_motion="reduce")
            page.goto(self.base_url + "/overview", wait_until="networkidle")
            self.wait_ready(page)
            page.locator('[data-metric-id="AVAILABLE_CASH"] .summary-link').focus()
            self.assertEqual(
                page.evaluate("document.activeElement.classList.contains('summary-link')"),
                True,
            )
            self.assertTrue(page.evaluate("matchMedia('(prefers-reduced-motion: reduce)').matches"))
            self.assertEqual(
                page.locator("#scan-summary").evaluate(
                    "node => getComputedStyle(node).animationDuration"
                ),
                "0s",
            )
            self.assert_clean(errors, external)
        finally:
            page.close()

    def test_10_browser_history_preserves_context(self) -> None:
        page, errors, external = self.new_page()
        try:
            page.goto(
                self.base_url
                + "/overview?company=demo-west&period=2026-Q2&project_status=attention&report_version=approved",
                wait_until="networkidle",
            )
            self.wait_ready(page)
            page.locator('[data-metric-id="OVERDUE_RECEIVABLE"] .summary-link').click()
            self.wait_detail(page)
            page.go_back(wait_until="networkidle")
            self.wait_ready(page)
            self.assertEqual(page.input_value("#context-company"), "demo-west")
            self.assertEqual(page.input_value("#context-period"), "2026-Q2")
            page.go_forward(wait_until="networkidle")
            self.wait_detail(page)
            snapshot = page.evaluate("window.KMFA_DRILLDOWN_TEST.snapshot()")
            self.assertEqual(snapshot["context"]["company"], "demo-west")
            self.assertEqual(snapshot["context"]["period"], "2026-Q2")
            self.assert_clean(errors, external)
        finally:
            page.close()


if __name__ == "__main__":
    unittest.main()
