from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from playwright.sync_api import Browser, Page, Playwright, sync_playwright

from KMFA.tools import run_v015_s19_p3_tax_policy_reporting as runtime


REPO_ROOT = Path(__file__).resolve().parents[2]
SCREENSHOT_ROOT = REPO_ROOT / "KMFA/stage_artifacts/V015_S19_P3_TAX_POLICY_REPORTING/exports/screenshots"


class TaxPolicyReportingBrowserTests(unittest.TestCase):
    playwright: Playwright
    browser: Browser

    @classmethod
    def setUpClass(cls) -> None:
        global SCREENSHOT_ROOT
        cls.screenshot_temp = None
        if os.environ.get("KMFA_PRESERVE_TRACKED_SCREENSHOTS") == "1":
            cls.screenshot_temp = tempfile.TemporaryDirectory()
            SCREENSHOT_ROOT = Path(cls.screenshot_temp.name)
        cls.event_temp = tempfile.TemporaryDirectory()
        cls.server, cls.server_thread, cls.base_url = runtime.start_server(event_path=Path(cls.event_temp.name) / "events.jsonl")
        cls.playwright = sync_playwright().start()
        chrome = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
        cls.browser = cls.playwright.chromium.launch(headless=True, executable_path=str(chrome) if chrome.is_file() else None)
        SCREENSHOT_ROOT.mkdir(parents=True, exist_ok=True)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.browser.close(); cls.playwright.stop(); cls.server.shutdown(); cls.server.server_close(); cls.server_thread.join(timeout=3); cls.event_temp.cleanup()
        if cls.screenshot_temp is not None:
            cls.screenshot_temp.cleanup()

    def new_page(self, width: int = 1440, height: int = 1000) -> tuple[Page, list[str]]:
        page = self.browser.new_page(viewport={"width": width, "height": height})
        page.set_default_timeout(10_000)
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("console", lambda message: errors.append(message.text) if message.type == "error" and not message.text.startswith("Failed to load resource:") else None)
        return page, errors

    def wait_ready(self, page: Page) -> None:
        page.locator("#tax-policy-report-view").wait_for(state="visible")
        page.wait_for_function("() => window.KMFA_TAX_POLICY_REPORT_TEST?.snapshot()?.tax_risk_summary?.review_invoice_count === 4")
        page.locator("#tpr-feedback", has_text="报告已整理").wait_for()

    def set_role(self, page: Page, role: str) -> None:
        page.evaluate("async role => { await window.KMFA_ROLE_TEST.setIdentity('demo-owner', role); await window.KMFA_TAX_POLICY_REPORT_TEST.load(); }", role)
        page.wait_for_function("role => window.KMFA_TAX_POLICY_REPORT_TEST.snapshot()?.review_permission?.role_id === role", arg=role)

    def test_01_desktop_report_and_boundary(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/tax-policy-report", wait_until="networkidle")
            self.wait_ready(page)
            self.assertEqual(page.locator("#tpr-metrics .tpr-metric").count(), 4)
            self.assertIn("不是税务申报", page.locator("#tpr-boundary").inner_text())
            page.screenshot(path=str(SCREENSHOT_ROOT / "tax_policy_report_desktop.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_02_risk_summary_is_plain_and_traceable(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/tax-policy-report", wait_until="networkidle"); self.wait_ready(page)
            self.assertEqual(page.locator("#tpr-risk-list .tpr-risk-card").count(), 4)
            text = page.locator("#tpr-risk-list").inner_text()
            self.assertIn("还没有明确依据", text)
            self.assertNotIn("巨额罚款", text)
            page.locator("#tpr-risk-list details").first.locator("summary").click()
            self.assertIn("PUBLIC-SYNTHETIC", page.locator("#tpr-risk-list details").first.inner_text())
            page.screenshot(path=str(SCREENSHOT_ROOT / "tax_risk_plain_language.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_03_period_switch_updates_cycle_without_conclusion(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/tax-policy-report", wait_until="networkidle"); self.wait_ready(page)
            page.locator("#context-period").select_option("2026-Q2")
            page.wait_for_function("() => window.KMFA_TAX_POLICY_REPORT_TEST.snapshot()?.policy_preparation_report?.cycle_id === 'QUARTERLY'")
            snapshot = page.evaluate("window.KMFA_TAX_POLICY_REPORT_TEST.snapshot()")
            self.assertEqual(snapshot["policy_preparation_report"]["formal_eligibility_conclusion_count"], 0)
            self.assertIn("季度", page.locator("#tpr-cycle").inner_text())
            page.screenshot(path=str(SCREENSHOT_ROOT / "policy_periodic_report.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_04_management_review_is_visibly_blocked(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/tax-policy-report", wait_until="networkidle"); self.wait_ready(page)
            self.set_role(page, "management")
            self.assertEqual(page.locator("#tpr-permission").get_attribute("data-allowed"), "false")
            self.assertTrue(page.locator("#tpr-submit").is_disabled())
            self.assertIn("只有税务或审核角色", page.locator("#tpr-permission").inner_text())
            page.screenshot(path=str(SCREENSHOT_ROOT / "professional_review_blocked.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_05_tax_role_records_append_only_review(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/tax-policy-report", wait_until="networkidle"); self.wait_ready(page)
            self.set_role(page, "tax")
            self.assertFalse(page.locator("#tpr-submit").is_disabled())
            page.locator("#tpr-comment").fill("已核对当前票据和合同依据，建议继续补证。")
            page.locator("#tpr-submit").click()
            page.wait_for_function("() => window.KMFA_TAX_POLICY_REPORT_TEST.snapshot()?.review_event_count === 1")
            self.assertIn("原始事实没有改变", page.locator("#tpr-feedback").inner_text())
            self.assertIn("税务", page.locator("#tpr-events").inner_text())
            page.screenshot(path=str(SCREENSHOT_ROOT / "professional_review_recorded.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_06_company_and_period_keep_review_events_isolated(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/tax-policy-report", wait_until="networkidle"); self.wait_ready(page); self.set_role(page, "tax")
            page.locator("#context-company").select_option("demo-west")
            page.locator("#context-period").select_option("2026-H1")
            page.wait_for_function("() => window.KMFA_TAX_POLICY_REPORT_TEST.snapshot()?.company_id === 'demo-west' && window.KMFA_TAX_POLICY_REPORT_TEST.snapshot()?.period === '2026-H1'")
            snapshot = page.evaluate("window.KMFA_TAX_POLICY_REPORT_TEST.snapshot()")
            self.assertEqual(snapshot["review_event_count"], 0)
            self.assertEqual(snapshot["cross_company_review_leak_count"], 0)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_07_existing_s19_routes_remain_navigable(self) -> None:
        page, errors = self.new_page()
        try:
            for route, selector in (("/policy-eligibility", "#policy-eligibility-view"), ("/tax-policy", "#tax-invoice-view")):
                page.goto(self.base_url + route, wait_until="networkidle")
                page.locator(selector).wait_for(state="visible")
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_08_mobile_touch_targets_and_no_overflow(self) -> None:
        page, errors = self.new_page(390, 844)
        try:
            page.goto(self.base_url + "/tax-policy-report", wait_until="networkidle"); self.wait_ready(page); self.set_role(page, "tax")
            self.assertTrue(page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1"))
            for selector in ("#tpr-basis", "#tpr-opinion", "#tpr-submit", ".tpr-back"):
                self.assertGreaterEqual(page.locator(selector).evaluate("node => Math.round(node.getBoundingClientRect().height)"), 44)
            page.screenshot(path=str(SCREENSHOT_ROOT / "tax_policy_report_mobile.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()


if __name__ == "__main__":
    unittest.main()
