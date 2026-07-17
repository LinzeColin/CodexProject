from __future__ import annotations

import unittest

from playwright.sync_api import Browser, Page, Playwright, sync_playwright

from KMFA.tools import build_v015_s11_p3_check_board_interface as builder


class CheckBoardInterfaceBrowserTests(unittest.TestCase):
    playwright: Playwright
    browser: Browser

    @classmethod
    def setUpClass(cls) -> None:
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.browser.close()
        cls.playwright.stop()

    def new_page(self, width: int = 1440, height: int = 760) -> tuple[Page, list[str], list[str]]:
        page = self.browser.new_page(viewport={"width": width, "height": height})
        page.set_default_timeout(8_000)
        errors: list[str] = []
        network: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
        page.on("request", lambda request: network.append(request.url) if not request.url.startswith("file:") else None)
        page.goto(builder.HTML_PATH.resolve().as_uri(), wait_until="networkidle")
        return page, errors, network

    def test_desktop_search_detail_action_and_exact_return_context(self) -> None:
        page, errors, network = self.new_page(1000, 760)
        try:
            self.assertEqual(page.title(), "KMFA 数据检查板")
            self.assertEqual(page.locator("#matrix-body tr").count(), 10)
            page.get_by_test_id("search-input").fill("回款")
            page.get_by_test_id("status-2").check()
            page.get_by_test_id("alert-only").check()
            page.locator("#table-scroll").evaluate("element => element.scrollLeft = 160")
            self.assertEqual(page.locator("#matrix-body tr").count(), 6)
            self.assertIn("找到 1 个", page.locator("#result-count").inner_text())

            target = page.locator("[data-detail]").last
            target_id = target.get_attribute("data-focus-node")
            backend_before = page.evaluate("window.__KMFA_S11_P3__.payload.backend_state_fingerprint")
            target.evaluate("element => element.click()")
            detail_text = page.locator("#detail-body").inner_text()
            for label in ("资料", "当前问题", "影响", "负责人", "建议下一步"):
                self.assertIn(label, detail_text)
            self.assertNotIn("technical_status", detail_text)

            page.locator("[data-start-action]").click()
            self.assertEqual(page.locator("#detail-title").inner_text(), "补充或重新提交资料")
            page.locator("[data-submit-action]").click()
            self.assertIn("状态没有被页面改写", page.locator("#completion-message").inner_text())
            page.locator("[data-complete-return]").click()
            page.wait_for_timeout(120)

            self.assertEqual(page.get_by_test_id("search-input").input_value(), "回款")
            self.assertTrue(page.get_by_test_id("status-2").is_checked())
            self.assertTrue(page.get_by_test_id("alert-only").is_checked())
            self.assertEqual(page.locator("#table-scroll").evaluate("element => element.scrollLeft"), 160)
            self.assertEqual(page.evaluate("document.activeElement && document.activeElement.dataset.focusNode"), target_id)
            self.assertEqual(page.evaluate("window.__KMFA_S11_P3__.state.requests[0].frontend_status_write_count"), 0)
            self.assertFalse(page.evaluate("window.__KMFA_S11_P3__.state.requests[0].status_change_requested"))
            self.assertEqual(page.evaluate("window.__KMFA_S11_P3__.payload.backend_state_fingerprint"), backend_before)
            self.assertEqual(errors, [])
            self.assertEqual(network, [])
        finally:
            page.close()

    def test_expand_collapse_and_keyboard_escape_restore_focus(self) -> None:
        page, errors, network = self.new_page()
        try:
            initial = page.locator("#matrix-body tr").count()
            first_toggle = page.locator("[data-toggle]").first
            self.assertEqual(first_toggle.get_attribute("aria-expanded"), "true")
            first_toggle.click()
            self.assertLess(page.locator("#matrix-body tr").count(), initial)
            self.assertEqual(page.locator("[data-toggle]").first.get_attribute("aria-expanded"), "false")
            page.locator("[data-detail]").first.focus()
            focused_id = page.locator("[data-detail]").first.get_attribute("data-focus-node")
            page.keyboard.press("Enter")
            self.assertEqual(page.locator("#detail-layer").get_attribute("data-open"), "true")
            page.keyboard.press("Escape")
            page.wait_for_timeout(80)
            self.assertEqual(page.locator("#detail-layer").get_attribute("data-open"), "false")
            self.assertEqual(page.evaluate("document.activeElement && document.activeElement.dataset.focusNode"), focused_id)
            self.assertEqual(errors, [])
            self.assertEqual(network, [])
        finally:
            page.close()

    def test_mobile_layout_keeps_controls_and_horizontal_matrix_usable(self) -> None:
        page, errors, network = self.new_page(390, 844)
        try:
            summary_columns = page.locator("#summary").evaluate("element => getComputedStyle(element).gridTemplateColumns")
            toolbar_columns = page.locator("#filter-form").evaluate("element => getComputedStyle(element).gridTemplateColumns")
            self.assertEqual(len(summary_columns.split()), 2)
            self.assertEqual(len(toolbar_columns.split()), 1)
            self.assertGreater(
                page.locator("#table-scroll").evaluate("element => element.scrollWidth"),
                page.locator("#table-scroll").evaluate("element => element.clientWidth"),
            )
            page.locator("[data-detail]").first.click()
            panel_width = page.locator(".detail-panel").evaluate("element => element.getBoundingClientRect().width")
            self.assertLessEqual(panel_width, 390)
            self.assertTrue(page.locator("#close-detail").is_visible())
            self.assertEqual(errors, [])
            self.assertEqual(network, [])
        finally:
            page.close()


if __name__ == "__main__":
    unittest.main()
