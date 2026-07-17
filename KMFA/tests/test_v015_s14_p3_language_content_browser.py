from __future__ import annotations

import unittest
from pathlib import Path

from playwright.sync_api import Browser, Page, Playwright, sync_playwright

from KMFA.tools import build_v015_s14_p3_language_content as builder
from KMFA.tools import v015_s14_p3_language_content as language


class LanguageContentBrowserTests(unittest.TestCase):
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

    def test_ten_second_structure_and_plain_chinese(self) -> None:
        page, errors, network = self.new_page()
        try:
            self.assertEqual(page.locator("h1[data-main-question]").count(), 1)
            self.assertEqual(page.locator("h1").inner_text(), "本周先处理哪三件事？")
            self.assertEqual(page.locator("[data-key-number]").count(), 3)
            self.assertEqual(page.locator("[data-focus-item]").count(), 3)
            self.assertEqual(page.locator("[data-primary-next-step]").count(), 1)
            visible = page.locator("body").inner_text()
            for term in (*language.FORBIDDEN_DEFAULT_TERMS, *language.FORBIDDEN_AI_COPY):
                self.assertNotIn(term, visible)
            builder.DESKTOP_LIGHT_SCREENSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(builder.DESKTOP_LIGHT_SCREENSHOT_PATH), full_page=True)
            self.assertEqual(errors, [])
            self.assertEqual(network, [])
        finally:
            page.close()

    def test_professional_terms_are_collapsed_by_default(self) -> None:
        page, errors, network = self.new_page()
        try:
            details = page.locator("#professional-details")
            self.assertFalse(details.evaluate("e => e.open"))
            visible = page.locator("body").inner_text()
            self.assertNotIn("PASSED", visible)
            self.assertNotIn("source_ref", visible)
            details.locator("summary").click()
            self.assertTrue(details.evaluate("e => e.open"))
            expanded = details.inner_text()
            self.assertIn("PASSED", expanded)
            self.assertIn("source_ref", expanded)
            self.assertEqual(errors, [])
            self.assertEqual(network, [])
        finally:
            page.close()

    def test_number_date_and_null_formats_are_exact(self) -> None:
        page, errors, network = self.new_page()
        try:
            body = page.locator("body").inner_text()
            for expected in ("¥ 206,000.00", "92.30%", "2026年7月17日", "¥ 120,000.00", "不适用"):
                self.assertIn(expected, body)
            payload = page.evaluate("window.__KMFA_S14_P3__.payload")
            self.assertEqual(payload["key_numbers"][0]["display"], "¥ 206,000.00")
            self.assertEqual(payload["key_numbers"][1]["display"], "92.30%")
            self.assertEqual(errors, [])
            self.assertEqual(network, [])
        finally:
            page.close()

    def test_primary_next_step_has_clear_feedback_and_returns_focus(self) -> None:
        page, errors, network = self.new_page(1100, 900)
        try:
            trigger = page.locator("#primary-next-step")
            trigger.click()
            dialog = page.locator("#next-dialog")
            self.assertTrue(dialog.evaluate("e => e.open"))
            self.assertEqual(dialog.locator("li").count(), 3)
            self.assertEqual(page.evaluate("document.activeElement.id"), "dialog-close")
            page.locator("#dialog-confirm").click()
            self.assertFalse(dialog.evaluate("e => e.open"))
            self.assertEqual(page.evaluate("document.activeElement.id"), "primary-next-step")
            self.assertEqual(errors, [])
            self.assertEqual(network, [])
        finally:
            page.close()

    def test_theme_mobile_and_no_page_overflow(self) -> None:
        page, errors, network = self.new_page()
        try:
            page.locator("#theme-toggle").click()
            self.assertEqual(page.locator("html").get_attribute("data-theme"), "dark")
            self.assertEqual(page.locator("#theme-toggle").get_attribute("aria-pressed"), "true")
            builder.DESKTOP_DARK_SCREENSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(builder.DESKTOP_DARK_SCREENSHOT_PATH), full_page=True)
            self.assertEqual(errors, [])
            self.assertEqual(network, [])
        finally:
            page.close()

        mobile, errors, network = self.new_page(390, 844)
        try:
            self.assertEqual(mobile.locator(".summary-strip .metric").count(), 3)
            columns = mobile.locator(".summary-strip").evaluate("e => getComputedStyle(e).gridTemplateColumns")
            self.assertEqual(len(columns.split()), 1)
            self.assertLessEqual(
                mobile.evaluate("document.documentElement.scrollWidth"),
                mobile.evaluate("window.innerWidth"),
            )
            builder.MOBILE_LIGHT_SCREENSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
            mobile.screenshot(path=str(builder.MOBILE_LIGHT_SCREENSHOT_PATH), full_page=True)
            self.assertEqual(errors, [])
            self.assertEqual(network, [])
        finally:
            mobile.close()


if __name__ == "__main__":
    unittest.main()
