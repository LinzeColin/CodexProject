from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from playwright.sync_api import Browser, Page, Playwright, sync_playwright

from KMFA.tools import run_v015_s19_p1_tax_invoice_facts as runtime


REPO_ROOT = Path(__file__).resolve().parents[2]
SCREENSHOT_ROOT = REPO_ROOT / "KMFA/stage_artifacts/V015_S19_P1_TAX_INVOICE_FACTS/exports/screenshots"


class TaxInvoiceBrowserTests(unittest.TestCase):
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
        cls.browser.close()
        cls.playwright.stop()
        cls.server.shutdown()
        cls.server.server_close()
        cls.server_thread.join(timeout=3)
        cls.event_temp.cleanup()
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
        page.locator("#tax-invoice-view").wait_for(state="visible")
        page.wait_for_function("() => window.KMFA_TAX_INVOICE_TEST?.snapshot()?.all_fact_count === 8")
        page.locator("#ti-feedback", has_text="核对完成").wait_for()

    def test_01_desktop_shows_facts_and_management_boundary(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/tax-policy", wait_until="networkidle")
            self.wait_ready(page)
            self.assertEqual(page.locator("#ti-fact-body tr").count(), 8)
            self.assertIn("管理分析，不是正式申报", page.locator("#ti-boundary").inner_text())
            self.assertIn("不猜税率", page.locator("#ti-boundary").inner_text())
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_tax_invoice_facts_desktop.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_02_unknown_rate_is_waiting_confirmation_not_inferred(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/tax-policy", wait_until="networkidle")
            self.wait_ready(page)
            page.locator("#ti-status").select_option("PENDING_CONFIRMATION")
            page.wait_for_function("() => window.KMFA_TAX_INVOICE_TEST.snapshot()?.summary?.fact_count === 1")
            snapshot = page.evaluate("window.KMFA_TAX_INVOICE_TEST.snapshot()")
            self.assertEqual(snapshot["rows"][0]["tax_rate_display_zh"], "待确认")
            self.assertIsNone(snapshot["rows"][0]["tax_rate_bps"])
            self.assertEqual(snapshot["rate_inference_count"], 0)
            self.assertIn("待确认", page.locator("#ti-fact-body").inner_text())
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_tax_invoice_unknown_rate.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_03_anomalies_show_specific_evidence_and_no_adjustment(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/tax-policy", wait_until="networkidle")
            self.wait_ready(page)
            self.assertEqual(page.locator("#ti-anomaly-list .ti-anomaly-card").count(), 5)
            text = page.locator("#ti-anomaly-list").inner_text()
            for token in ("税率待确认", "主体不一致", "期间不一致", "项目不一致", "税率不一致", "票据事实与合同事实已关联", "仅人工核对"):
                self.assertIn(token, text)
            snapshot = page.evaluate("window.KMFA_TAX_INVOICE_TEST.snapshot()")
            self.assertEqual(snapshot["automatic_tax_adjustment_count"], 0)
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_tax_invoice_anomalies.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_04_filters_keep_summary_and_rows_in_sync(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/tax-policy", wait_until="networkidle")
            self.wait_ready(page)
            page.locator("#ti-direction").select_option("INPUT")
            page.locator("#ti-match").select_option("REVIEW_REQUIRED")
            page.wait_for_function("() => window.KMFA_TAX_INVOICE_TEST.snapshot()?.summary?.fact_count === 2")
            snapshot = page.evaluate("window.KMFA_TAX_INVOICE_TEST.snapshot()")
            self.assertTrue(all(row["direction"] == "INPUT" and row["match_state"] == "REVIEW_REQUIRED" for row in snapshot["rows"]))
            self.assertEqual(page.locator("#ti-fact-body tr").count(), 2)
            self.assertEqual(snapshot["anomaly_count"], 3)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_05_project_burden_is_management_only_and_reconciled(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/tax-policy", wait_until="networkidle")
            self.wait_ready(page)
            snapshot = page.evaluate("window.KMFA_TAX_INVOICE_TEST.snapshot()")
            self.assertEqual(page.locator("#ti-burden-body tr").count(), 3)
            for row in snapshot["project_burden"]:
                self.assertEqual(row["management_net_tax_pressure_cents"], row["output_tax_cents"] - row["eligible_input_tax_cents"])
                self.assertFalse(row["formal_filing_conclusion"])
            self.assertIn("不是正式申报结论", page.locator("#ti-burden-body").inner_text())
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_tax_invoice_project_burden.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_06_company_and_period_switch_remain_isolated(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/tax-policy", wait_until="networkidle")
            self.wait_ready(page)
            north = page.evaluate("window.KMFA_TAX_INVOICE_TEST.snapshot().summary.explicit_tax_cents")
            page.locator("#context-company").select_option("demo-west")
            page.locator("#context-period").select_option("2026-Q2")
            page.wait_for_function("() => window.KMFA_TAX_INVOICE_TEST.snapshot()?.company_id === 'demo-west' && window.KMFA_TAX_INVOICE_TEST.snapshot()?.period === '2026-Q2'")
            snapshot = page.evaluate("window.KMFA_TAX_INVOICE_TEST.snapshot()")
            self.assertTrue(all(row["company_id"] == "demo-west" for row in snapshot["rows"]))
            self.assertNotEqual(north, snapshot["summary"]["explicit_tax_cents"])
            self.assertEqual(snapshot["cross_company_leak_count"], 0)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_07_mobile_cards_touch_targets_and_no_overflow(self) -> None:
        page, errors = self.new_page(390, 844)
        try:
            page.goto(self.base_url + "/tax-policy", wait_until="networkidle")
            self.wait_ready(page)
            self.assertTrue(page.locator("#ti-fact-mobile").is_visible())
            self.assertEqual(page.locator("#ti-fact-mobile .ti-mobile-card").count(), 8)
            self.assertEqual(page.locator("#ti-burden-mobile .ti-mobile-card").count(), 3)
            self.assertTrue(page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1"))
            for selector in ("#ti-project", "#ti-direction", "#ti-status", "#ti-match"):
                self.assertGreaterEqual(page.locator(selector).evaluate("node => Math.round(node.getBoundingClientRect().height)"), 44)
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_tax_invoice_mobile.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()


if __name__ == "__main__":
    unittest.main()
