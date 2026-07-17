from __future__ import annotations

import unittest
from pathlib import Path

from playwright.sync_api import Browser, Page, Playwright, sync_playwright

from KMFA.tools import build_v015_s14_stage_review as builder
from KMFA.tools import v015_s14_p1_information_architecture as p1
from KMFA.tools import v015_s14_p2_design_system as p2
from KMFA.tools import v015_s14_p3_language_content as p3


class S14StageReviewBrowserTests(unittest.TestCase):
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

    def new_page(self, width: int = 1440, height: int = 1050) -> tuple[Page, list[str], list[str]]:
        page = self.browser.new_page(viewport={"width": width, "height": height})
        page.set_default_timeout(8_000)
        errors: list[str] = []
        network: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
        page.on("request", lambda request: network.append(request.url) if not request.url.startswith("file:") else None)
        page.goto(builder.HTML_PATH.resolve().as_uri(), wait_until="networkidle")
        return page, errors, network

    def test_seven_navigation_destinations_are_real_and_current_state_moves(self) -> None:
        page, errors, network = self.new_page()
        try:
            links = page.locator("#primary-nav a[data-route]")
            self.assertEqual(links.count(), 7)
            self.assertEqual(links.all_inner_texts(), [row["label_zh"] for row in p1.NAV_ITEMS])
            self.assertEqual(
                [links.nth(index).get_attribute("data-route") for index in range(links.count())],
                [row["route"] for row in p1.NAV_ITEMS],
            )
            links.nth(1).click()
            self.assertTrue(page.url.endswith("#/projects"))
            self.assertEqual(links.nth(1).get_attribute("aria-current"), "page")
            self.assertIsNone(links.nth(0).get_attribute("aria-current"))
            self.assertEqual(page.locator(".breadcrumbs").inner_text(), "项目")
            builder.DESKTOP_LIGHT_SCREENSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(builder.DESKTOP_LIGHT_SCREENSHOT_PATH), full_page=True)
            self.assertEqual(errors, [])
            self.assertEqual(network, [])
        finally:
            page.close()

    def test_plain_chinese_is_default_and_professional_terms_stay_collapsed(self) -> None:
        page, errors, network = self.new_page()
        try:
            self.assertEqual(page.locator("h1[data-main-question]").count(), 1)
            self.assertEqual(page.locator("[data-key-number]").count(), 3)
            self.assertEqual(page.locator("[data-focus-item]").count(), 3)
            self.assertEqual(page.locator("[data-primary-next-step]").count(), 1)
            details = page.locator("#professional-details")
            self.assertFalse(details.evaluate("element => element.open"))
            visible = page.locator("body").inner_text()
            for term in (*p3.FORBIDDEN_DEFAULT_TERMS, *p3.FORBIDDEN_AI_COPY):
                self.assertNotIn(term, visible)
            details.locator("summary").click()
            self.assertIn("PASSED", details.inner_text())
            self.assertIn("source_ref", details.inner_text())
            self.assertEqual(errors, [])
            self.assertEqual(network, [])
        finally:
            page.close()

    def test_light_and_dark_themes_reuse_the_exact_design_tokens(self) -> None:
        page, errors, network = self.new_page()
        try:
            for key in ("canvas", "surface", "text", "primary", "nav"):
                actual = page.evaluate(f"getComputedStyle(document.documentElement).getPropertyValue('--{key}').trim()")
                self.assertEqual(actual.casefold(), p2.THEMES["light"][key].casefold())
            page.locator("#theme-toggle").click()
            self.assertEqual(page.locator("html").get_attribute("data-theme"), "dark")
            for key in ("canvas", "surface", "text", "primary", "nav"):
                actual = page.evaluate(f"getComputedStyle(document.documentElement).getPropertyValue('--{key}').trim()")
                self.assertEqual(actual.casefold(), p2.THEMES["dark"][key].casefold())
            builder.DESKTOP_DARK_SCREENSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(builder.DESKTOP_DARK_SCREENSHOT_PATH), full_page=True)
            self.assertEqual(errors, [])
            self.assertEqual(network, [])
        finally:
            page.close()

    def test_displayed_numbers_recalculate_from_integer_values(self) -> None:
        page, errors, network = self.new_page()
        try:
            payload = page.evaluate("window.__KMFA_S14_P3__.payload")
            self.assertEqual(payload["key_numbers"][0]["display"], p3.format_money(payload["key_numbers"][0]["underlying"]))
            self.assertEqual(payload["key_numbers"][1]["display"], p3.format_ratio(payload["key_numbers"][1]["underlying"]))
            self.assertEqual(payload["focus_items"][0]["amount_zh"], p3.format_money(payload["focus_items"][0]["amount_underlying"]))
            self.assertEqual(payload["focus_items"][2]["amount_zh"], p3.format_null(payload["focus_items"][2]["amount_underlying"]))
            self.assertTrue(all(not isinstance(row["underlying"], float) for row in payload["key_numbers"]))
            self.assertEqual(errors, [])
            self.assertEqual(network, [])
        finally:
            page.close()

    def test_primary_next_step_explains_result_and_returns_keyboard_focus(self) -> None:
        page, errors, network = self.new_page(1100, 900)
        try:
            trigger = page.locator("#primary-next-step")
            trigger.click()
            dialog = page.locator("#next-dialog")
            self.assertTrue(dialog.evaluate("element => element.open"))
            self.assertEqual(dialog.locator("li").count(), 3)
            self.assertEqual(page.evaluate("document.activeElement.id"), "dialog-close")
            page.locator("#dialog-confirm").click()
            self.assertFalse(dialog.evaluate("element => element.open"))
            self.assertEqual(page.evaluate("document.activeElement.id"), "primary-next-step")
            self.assertEqual(errors, [])
            self.assertEqual(network, [])
        finally:
            page.close()

    def test_mobile_layout_has_no_page_overflow(self) -> None:
        page, errors, network = self.new_page(390, 844)
        try:
            self.assertEqual(page.locator(".summary-strip .metric").count(), 3)
            columns = page.locator(".summary-strip").evaluate("element => getComputedStyle(element).gridTemplateColumns")
            self.assertEqual(len(columns.split()), 1)
            self.assertLessEqual(
                page.evaluate("document.documentElement.scrollWidth"),
                page.evaluate("window.innerWidth"),
            )
            builder.MOBILE_LIGHT_SCREENSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(builder.MOBILE_LIGHT_SCREENSHOT_PATH), full_page=True)
            self.assertEqual(errors, [])
            self.assertEqual(network, [])
        finally:
            page.close()


if __name__ == "__main__":
    unittest.main()
