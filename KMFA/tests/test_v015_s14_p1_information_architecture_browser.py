from __future__ import annotations

import unittest
from pathlib import Path

from playwright.sync_api import Browser, Page, Playwright, sync_playwright

from KMFA.tools import build_v015_s14_p1_information_architecture as builder
from KMFA.tools import v015_s14_p1_information_architecture as ia


class InformationArchitectureBrowserTests(unittest.TestCase):
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

    def new_page(self, width: int = 1440, height: int = 1000) -> tuple[Page, list[str], list[str]]:
        page = self.browser.new_page(viewport={"width": width, "height": height})
        page.set_default_timeout(8_000)
        errors: list[str] = []
        network: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
        page.on("request", lambda request: network.append(request.url) if not request.url.startswith("file:") else None)
        page.goto(builder.HTML_PATH.resolve().as_uri(), wait_until="networkidle")
        return page, errors, network

    def test_desktop_seven_navigation_destinations_and_screenshot(self) -> None:
        page, errors, network = self.new_page()
        try:
            self.assertEqual(page.title(), "KMFA 经营工作台")
            self.assertEqual(page.locator("#primary-nav a").count(), 7)
            labels = page.locator("#primary-nav a").all_inner_texts()
            self.assertEqual(labels, ["经营首页", "项目", "回款", "资金", "税务与政策", "数据更新", "报告"])
            for item in ia.NAV_ITEMS:
                page.locator('[data-nav-id="' + item["nav_id"] + '"]').click()
                page.wait_for_function("location.hash === '#" + item["route"] + "'")
                self.assertEqual(
                    page.locator('[data-nav-id="' + item["nav_id"] + '"]').get_attribute("aria-current"),
                    "page",
                )
            builder.SCREENSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(builder.SCREENSHOT_PATH), full_page=True)
            self.assertEqual(errors, [])
            self.assertEqual(network, [])
        finally:
            page.close()

    def test_list_detail_process_breadcrumb_and_previous_task_return(self) -> None:
        page, errors, network = self.new_page(1100, 850)
        try:
            page.goto(builder.HTML_PATH.resolve().as_uri() + "#/projects", wait_until="networkidle")
            self.assertEqual(page.locator("h1").inner_text(), "项目")
            page.locator('[data-task-route="/projects/demo-project"]').click()
            page.wait_for_function("location.hash === '#/projects/demo-project'")
            self.assertEqual(page.locator("#breadcrumbs").inner_text().replace("\n", " "), "经营首页 › 项目 › 示例项目详情")
            page.locator('[data-task-route="/projects/demo-project/update"]').click()
            page.wait_for_function("location.hash === '#/projects/demo-project/update'")
            self.assertIn("项目 › 示例项目详情 › 更新项目资料", page.locator("#breadcrumbs").inner_text().replace("\n", " "))
            page.locator("[data-previous-task]").click()
            page.wait_for_function("location.hash === '#/projects/demo-project'")
            self.assertEqual(page.locator("h1").inner_text(), "示例项目详情")
            self.assertEqual(errors, [])
            self.assertEqual(network, [])
        finally:
            page.close()

    def test_report_settings_and_progressive_disclosure(self) -> None:
        page, errors, network = self.new_page()
        try:
            page.goto(builder.HTML_PATH.resolve().as_uri() + "#/reports/demo-business-report", wait_until="networkidle")
            details = page.locator("details")
            self.assertEqual(details.count(), 2)
            self.assertFalse(details.nth(0).evaluate("element => element.open"))
            self.assertFalse(details.nth(1).evaluate("element => element.open"))
            default_text = page.locator("body").inner_text()
            for term in ia.FORBIDDEN_DEFAULT_TERMS:
                self.assertNotIn(term.casefold(), default_text.casefold())
            details.nth(0).locator("summary").click()
            self.assertTrue(details.nth(0).evaluate("element => element.open"))
            self.assertIn("真实报告必须绑定", details.nth(0).inner_text())
            page.locator(".utility-link").click()
            page.wait_for_function("location.hash === '#/settings'")
            self.assertEqual(page.locator("h1").inner_text(), "页面设置")
            self.assertEqual(page.locator("#primary-nav a").count(), 7)
            self.assertEqual(errors, [])
            self.assertEqual(network, [])
        finally:
            page.close()

    def test_mobile_keeps_horizontal_top_navigation_and_readable_content(self) -> None:
        page, errors, network = self.new_page(390, 844)
        try:
            nav = page.locator("#primary-nav")
            self.assertGreater(nav.evaluate("element => element.scrollWidth"), nav.evaluate("element => element.clientWidth"))
            self.assertEqual(page.locator(".sidebar").count(), 0)
            self.assertEqual(page.locator(".fact-strip").evaluate("element => getComputedStyle(element).gridTemplateColumns").split().__len__(), 1)
            page.locator('[data-nav-id="data-update"]').click()
            page.wait_for_function("location.hash === '#/data-update'")
            self.assertEqual(page.locator("h1").inner_text(), "数据更新")
            self.assertTrue(page.locator("[data-previous-task]").is_visible())
            self.assertEqual(errors, [])
            self.assertEqual(network, [])
        finally:
            page.close()


if __name__ == "__main__":
    unittest.main()
