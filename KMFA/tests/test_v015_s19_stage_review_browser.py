from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from playwright.sync_api import Browser, Page, Playwright, sync_playwright

from KMFA.tools import run_v015_s19_p3_tax_policy_reporting as runtime


REPO_ROOT = Path(__file__).resolve().parents[2]
SCREENSHOT_ROOT = REPO_ROOT / "KMFA/stage_artifacts/V015_S19_STAGE_REVIEW/exports/screenshots"


class S19StageReviewBrowserTests(unittest.TestCase):
    playwright: Playwright
    browser: Browser

    @classmethod
    def setUpClass(cls) -> None:
        global SCREENSHOT_ROOT
        cls.temp = tempfile.TemporaryDirectory()
        if os.environ.get("KMFA_PRESERVE_TRACKED_SCREENSHOTS") == "1":
            SCREENSHOT_ROOT = Path(cls.temp.name) / "screenshots"
        cls.event_path = Path(cls.temp.name) / "events.jsonl"
        cls.server, cls.thread, cls.base_url = runtime.start_server(event_path=cls.event_path)
        cls.playwright = sync_playwright().start()
        chrome = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
        cls.browser = cls.playwright.chromium.launch(headless=True, executable_path=str(chrome) if chrome.is_file() else None)
        SCREENSHOT_ROOT.mkdir(parents=True, exist_ok=True)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.browser.close(); cls.playwright.stop(); cls.server.shutdown(); cls.server.server_close(); cls.thread.join(timeout=3); cls.temp.cleanup()

    def setUp(self) -> None:
        self.event_path.unlink(missing_ok=True)

    def page(self, width: int = 1440, height: int = 1000) -> tuple[Page, list[str]]:
        page = self.browser.new_page(viewport={"width": width, "height": height})
        page.set_default_timeout(12_000)
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("console", lambda message: errors.append(message.text) if message.type == "error" and not message.text.startswith("Failed to load resource:") else None)
        return page, errors

    @staticmethod
    def wait_report(page: Page) -> None:
        page.locator("#tax-policy-report-view").wait_for(state="visible")
        page.wait_for_function("() => window.KMFA_TAX_POLICY_REPORT_TEST?.snapshot()?.tax_risk_summary?.review_invoice_count === 4")

    def test_01_desktop_three_step_navigation(self) -> None:
        page, errors = self.page()
        try:
            page.goto(self.base_url + "/tax-policy", wait_until="networkidle")
            page.locator("#tax-invoice-view").wait_for(state="visible")
            page.locator("#tax-invoice-view .s19-next").click()
            page.wait_for_function("() => location.pathname === '/policy-eligibility'")
            page.locator("#policy-eligibility-view").wait_for(state="visible")
            page.locator("#policy-eligibility-view .s19-next").click()
            page.wait_for_function("() => location.pathname === '/tax-policy-report'")
            self.wait_report(page)
            self.assertEqual(page.locator(".tpr-risk-card").count(), 4)
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_s19_review_dashboard.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_02_policy_materials_reach_periodic_report(self) -> None:
        page, errors = self.page()
        try:
            page.goto(self.base_url + "/policy-eligibility", wait_until="networkidle")
            page.locator("#policy-eligibility-view").wait_for(state="visible")
            page.wait_for_function("() => window.KMFA_POLICY_ELIGIBILITY_TEST?.snapshot()?.summary?.evidence_item_count === 12")
            self.assertEqual(page.locator(".pe-readiness-card").count(), 6)
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_s19_review_policy_materials.png"), full_page=True)
            page.locator("#policy-eligibility-view .s19-next").click(); self.wait_report(page)
            self.assertIn("7 份材料已有来源", page.locator("#tpr-policy-summary").inner_text())
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_03_review_permission_and_append_only_flow(self) -> None:
        page, errors = self.page()
        try:
            page.goto(self.base_url + "/tax-policy-report", wait_until="networkidle"); self.wait_report(page)
            self.assertTrue(page.locator("#tpr-submit").is_disabled())
            page.evaluate("async () => { await window.KMFA_ROLE_TEST.setIdentity('demo-owner', 'tax'); await window.KMFA_TAX_POLICY_REPORT_TEST.load(); }")
            page.wait_for_function("() => window.KMFA_TAX_POLICY_REPORT_TEST.snapshot()?.review_permission?.allowed === true")
            page.locator("#tpr-comment").fill("已核对当前报告依据，建议继续补充材料。")
            page.locator("#tpr-submit").click()
            page.wait_for_function("() => window.KMFA_TAX_POLICY_REPORT_TEST.snapshot()?.review_event_count === 1")
            self.assertIn("原始事实没有改变", page.locator("#tpr-feedback").inner_text())
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_s19_review_professional_integrity.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_04_tablet_navigation_has_no_overflow(self) -> None:
        page, errors = self.page(820, 1180)
        try:
            page.goto(self.base_url + "/policy-eligibility", wait_until="networkidle")
            page.locator("#policy-eligibility-view").wait_for(state="visible")
            self.assertTrue(page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1"))
            self.assertTrue(all(value >= 44 for value in page.locator("#policy-eligibility-view .s19-journey a").evaluate_all("nodes => nodes.map(node => Math.round(node.getBoundingClientRect().height))")))
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_s19_review_tablet.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_05_mobile_report_has_no_overflow(self) -> None:
        page, errors = self.page(390, 844)
        try:
            page.goto(self.base_url + "/tax-policy-report", wait_until="networkidle"); self.wait_report(page)
            self.assertTrue(page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1"))
            for selector in (".tpr-back", "#tpr-basis", "#tpr-opinion", "#tpr-submit"):
                self.assertGreaterEqual(page.locator(selector).evaluate("node => Math.round(node.getBoundingClientRect().height)"), 44)
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_s19_review_mobile.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()


if __name__ == "__main__":
    unittest.main()
