from __future__ import annotations

import unittest
from pathlib import Path

from playwright.sync_api import Browser, Page, Playwright, sync_playwright

from KMFA.tools import build_v015_s14_p2_design_system as builder


class DesignSystemBrowserTests(unittest.TestCase):
    playwright: Playwright
    browser: Browser

    @classmethod
    def setUpClass(cls) -> None:
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

    def new_page(
        self, width: int = 1440, height: int = 1000, *, reduced_motion: bool = False
    ) -> tuple[Page, list[str], list[str]]:
        page = self.browser.new_page(
            viewport={"width": width, "height": height},
            reduced_motion="reduce" if reduced_motion else "no-preference",
        )
        page.set_default_timeout(8_000)
        errors: list[str] = []
        network: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
        page.on("request", lambda request: network.append(request.url) if not request.url.startswith("file:") else None)
        page.goto(builder.HTML_PATH.resolve().as_uri(), wait_until="networkidle")
        return page, errors, network

    def test_desktop_light_and_dark_theme_visual_regression(self) -> None:
        page, errors, network = self.new_page()
        try:
            self.assertEqual(page.title(), "KMFA 经营工作台")
            self.assertEqual(page.locator("#primary-nav a").count(), 7)
            self.assertEqual(page.locator("h1").inner_text(), "今天需要关注的事项")
            builder.DESKTOP_LIGHT_SCREENSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(builder.DESKTOP_LIGHT_SCREENSHOT_PATH), full_page=True)
            page.locator("#theme-toggle").click()
            self.assertEqual(page.locator("html").get_attribute("data-theme"), "dark")
            self.assertEqual(page.locator("#theme-toggle").get_attribute("aria-pressed"), "true")
            page.wait_for_timeout(240)
            self.assertEqual(
                page.locator("body").evaluate("e => getComputedStyle(e).backgroundColor"),
                "rgb(11, 23, 35)",
            )
            page.screenshot(path=str(builder.DESKTOP_DARK_SCREENSHOT_PATH), full_page=True)
            self.assertEqual(errors, [])
            self.assertEqual(network, [])
        finally:
            page.close()

    def test_dialog_drawer_toast_and_focus_return(self) -> None:
        page, errors, network = self.new_page(1100, 900)
        try:
            open_dialog = page.locator("#open-dialog")
            open_dialog.focus()
            open_dialog.click()
            self.assertTrue(page.locator("#follow-dialog").evaluate("e => e.open"))
            self.assertEqual(page.evaluate("document.activeElement.id"), "follow-name")
            page.locator("#dialog-confirm").click()
            self.assertFalse(page.locator("#follow-dialog").evaluate("e => e.open"))
            self.assertEqual(page.evaluate("document.activeElement.id"), "open-dialog")
            self.assertEqual(page.locator("#toast").get_attribute("data-open"), "true")
            drawer_trigger = page.locator("#open-drawer")
            drawer_trigger.click()
            self.assertEqual(page.locator("#detail-drawer").get_attribute("data-open"), "true")
            self.assertEqual(page.evaluate("document.activeElement.id"), "close-drawer")
            page.locator("#close-drawer").click()
            self.assertEqual(page.locator("#detail-drawer").get_attribute("data-open"), "false")
            self.assertEqual(page.evaluate("document.activeElement.id"), "open-drawer")
            self.assertEqual(errors, [])
            self.assertEqual(network, [])
        finally:
            page.close()

    def test_all_component_families_and_visible_states_exist(self) -> None:
        page, errors, network = self.new_page()
        try:
            for selector in (
                ".btn",
                ".field",
                "#status-filter",
                ".data-table",
                ".metric",
                ".chart",
                "#follow-dialog",
                "#detail-drawer",
                "#toast",
                ".empty",
                ".badge",
            ):
                self.assertGreater(page.locator(selector).count(), 0, selector)
            self.assertTrue(page.locator("button[disabled]").is_disabled())
            self.assertEqual(
                page.locator('[aria-busy="true"]').inner_text().replace("\n", ""),
                "…处理中",
            )
            self.assertEqual(page.locator('[aria-invalid="true"]').get_attribute("aria-describedby"), "error-message")
            self.assertIn("请选择计划日期", page.locator("#error-message").inner_text())
            for badge in page.locator(".badge").all():
                self.assertTrue(badge.inner_text().strip())
            self.assertEqual(errors, [])
            self.assertEqual(network, [])
        finally:
            page.close()

    def test_mobile_layout_and_warning_area_are_controlled(self) -> None:
        page, errors, network = self.new_page(390, 844)
        try:
            nav = page.locator("#primary-nav")
            self.assertGreater(nav.evaluate("e => e.scrollWidth"), nav.evaluate("e => e.clientWidth"))
            self.assertEqual(page.locator(".status-grid").evaluate("e => getComputedStyle(e).gridTemplateColumns").split().__len__(), 1)
            warning = page.locator('[data-tone="warning"]').first
            warning_area = warning.evaluate("e => {const r=e.getBoundingClientRect();return r.width*r.height;}")
            body_area = page.locator("body").evaluate("e => {const r=e.getBoundingClientRect();return r.width*r.height;}")
            self.assertLess(warning_area / body_area, 0.08)
            builder.MOBILE_LIGHT_SCREENSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(builder.MOBILE_LIGHT_SCREENSHOT_PATH), full_page=True)
            self.assertEqual(errors, [])
            self.assertEqual(network, [])
        finally:
            page.close()

    def test_keyboard_focus_reduced_motion_and_chart_alternatives(self) -> None:
        page, errors, network = self.new_page(reduced_motion=True)
        try:
            page.keyboard.press("Tab")
            focused = page.evaluate("document.activeElement.className")
            self.assertIn("skip-link", focused)
            transition_ms = page.locator("#detail-drawer").evaluate(
                "e => Math.max(...getComputedStyle(e).transitionDuration.split(',').map(v => parseFloat(v) * (v.includes('ms') ? 1 : 1000)))"
            )
            self.assertLessEqual(transition_ms, 1)
            self.assertEqual(page.locator(".chart[role='img']").count(), 1)
            self.assertEqual(page.locator(".sr-data caption").inner_text(), "近六周事项数据")
            self.assertIn("实线", page.locator(".legend").inner_text())
            self.assertIn("虚线", page.locator(".legend").inner_text())
            self.assertEqual(errors, [])
            self.assertEqual(network, [])
        finally:
            page.close()


if __name__ == "__main__":
    unittest.main()
