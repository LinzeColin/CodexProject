from __future__ import annotations

import unittest
from pathlib import Path

from playwright.sync_api import Browser, Page, Playwright, sync_playwright

from KMFA.tools import run_v015_s15_p1_app_shell as runtime


REPO_ROOT = Path(__file__).resolve().parents[2]
SCREENSHOT_ROOT = REPO_ROOT / "KMFA/stage_artifacts/V015_S15_P1_APP_SHELL/exports/screenshots"


class AppShellBrowserTests(unittest.TestCase):
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

    def test_deep_link_refresh_and_back_forward_restore_route(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/projects/demo-project/update", wait_until="networkidle")
            self.wait_ready(page)
            self.assertEqual(page.locator("#page-title").inner_text(), "更新项目资料")
            page.reload(wait_until="networkidle")
            self.wait_ready(page)
            self.assertEqual(page.locator("#page-title").inner_text(), "更新项目资料")
            page.locator('[data-route="/reports"]').first.click()
            self.wait_ready(page)
            self.assertEqual(page.locator("#page-title").inner_text(), "报告")
            page.go_back(wait_until="networkidle")
            self.wait_ready(page)
            self.assertEqual(page.locator("#page-title").inner_text(), "更新项目资料")
            page.go_forward(wait_until="networkidle")
            self.wait_ready(page)
            self.assertEqual(page.locator("#page-title").inner_text(), "报告")
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_context_switch_persists_in_url_reload_and_new_page(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/overview", wait_until="networkidle")
            self.wait_ready(page)
            page.select_option("#context-company", "demo-south")
            page.select_option("#context-period", "2026-Q2")
            page.select_option("#context-project_status", "attention")
            page.select_option("#context-report_version", "approved")
            self.wait_ready(page)
            self.assertIn("南区示例公司", page.locator("#context-status").inner_text())
            self.assertIn("company=demo-south", page.url)
            self.assertIn("period=2026-Q2", page.url)
            page.reload(wait_until="networkidle")
            self.wait_ready(page)
            self.assertEqual(page.input_value("#context-company"), "demo-south")
            self.assertEqual(page.input_value("#context-period"), "2026-Q2")
            self.assertEqual(page.input_value("#context-project_status"), "attention")
            self.assertEqual(page.input_value("#context-report_version"), "approved")
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_fast_company_switch_never_renders_late_previous_company(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/overview", wait_until="networkidle")
            self.wait_ready(page)
            page.evaluate("window.KMFA_TEST.setDelay(700)")
            page.select_option("#context-company", "demo-north")
            page.wait_for_timeout(60)
            page.evaluate("window.KMFA_TEST.setDelay(0)")
            page.select_option("#context-company", "demo-west")
            self.wait_ready(page)
            page.wait_for_timeout(850)
            self.assertIn("西区示例公司", page.locator("#context-status").inner_text())
            self.assertNotIn("北区示例公司", page.locator("#context-status").inner_text())
            ids = page.locator("#item-list li strong").all_inner_texts()
            self.assertTrue(ids)
            self.assertFalse(page.locator("#error-view").is_visible())
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_network_parse_calculation_and_permission_errors_recover(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/overview", wait_until="networkidle")
            self.wait_ready(page)
            expectations = {
                "network": "暂时无法连接",
                "parse": "返回内容无法读取",
                "calculation": "暂时无法完成计算",
                "permission": "当前账号不能查看",
            }
            for fault, title in expectations.items():
                page.evaluate("fault => window.KMFA_TEST.setFault(fault)", fault)
                page.evaluate("window.KMFA_TEST.load()")
                page.locator("#error-view:not([hidden])").wait_for()
                self.assertEqual(page.locator("#error-title").inner_text(), title)
                self.assertTrue(page.locator("#error-message").inner_text())
                page.locator("#error-action").click()
                self.wait_ready(page)
                self.assertFalse(page.locator("#error-view").is_visible())
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_unknown_route_has_recovery_and_mobile_shell_is_accessible(self) -> None:
        page, errors = self.new_page(390, 844)
        try:
            page.goto(self.base_url + "/missing", wait_until="networkidle")
            page.locator("#not-found-view:not([hidden])").wait_for()
            self.assertIn("暂时找不到", page.locator("#not-found-view h1").inner_text())
            page.locator('#not-found-view [data-route="/overview"]').click()
            self.wait_ready(page)
            self.assertEqual(page.locator("#page-title").inner_text(), "经营首页")
            nav = page.locator("#primary-nav")
            self.assertGreater(nav.evaluate("node => node.scrollWidth"), nav.evaluate("node => node.clientWidth"))
            self.assertEqual(page.locator(".sidebar").count(), 0)
            page.keyboard.press("Tab")
            focused = page.locator(":focus")
            self.assertTrue(focused.count() == 1)
            self.assertGreaterEqual(page.locator("label select").count(), 4)
            SCREENSHOT_ROOT.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_app_shell_mobile.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_desktop_ready_context_and_error_screenshots(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/overview", wait_until="networkidle")
            self.wait_ready(page)
            SCREENSHOT_ROOT.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_app_shell_desktop.png"), full_page=True)
            page.select_option("#context-company", "demo-south")
            page.select_option("#context-period", "2026-Q2")
            self.wait_ready(page)
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_app_shell_context.png"), full_page=True)
            page.evaluate("window.KMFA_TEST.setFault('calculation')")
            page.evaluate("window.KMFA_TEST.load()")
            page.locator("#error-view:not([hidden])").wait_for()
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_app_shell_error.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()


if __name__ == "__main__":
    unittest.main()
