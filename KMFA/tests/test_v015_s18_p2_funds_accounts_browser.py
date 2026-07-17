from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from playwright.sync_api import Browser, Page, Playwright, sync_playwright

from KMFA.tools import run_v015_s18_p2_funds_accounts as runtime


REPO_ROOT = Path(__file__).resolve().parents[2]
SCREENSHOT_ROOT = REPO_ROOT / "KMFA/stage_artifacts/V015_S18_P2_FUNDS_ACCOUNTS/exports/screenshots"


class FundsAccountsBrowserTests(unittest.TestCase):
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
        page.locator("#funds-view").wait_for(state="visible")
        page.wait_for_function("() => window.KMFA_FUNDS_TEST?.snapshot()?.accounts?.accounts?.length === 4")
        page.locator("#funds-feedback", has_text="核对完成").wait_for()

    def test_01_desktop_explains_facts_plans_and_assumptions(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/funds", wait_until="networkidle")
            self.wait_ready(page)
            self.assertEqual(page.locator("#funds-cutoff").inner_text(), "2026-07-15")
            basis = page.locator(".funds-basis").inner_text()
            for token in ("事实", "计划", "情景假设", "不会写回事实"):
                self.assertIn(token, basis)
            self.assertIn("不是确定值", page.locator("#funds-summary").inner_text())
            self.assertEqual(page.get_by_role("button", name="付款").count(), 0)
            self.assertEqual(page.get_by_role("button", name="还款").count(), 0)
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_funds_desktop.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_02_accounts_are_masked_sourced_and_reconciled(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/funds", wait_until="networkidle")
            self.wait_ready(page)
            rows = page.locator("#accounts-body tr")
            self.assertEqual(rows.count(), 4)
            self.assertTrue(all(value.startswith("****") for value in rows.locator("td:nth-child(2)").all_inner_texts()))
            self.assertIn("相差 0 分", page.locator("#accounts-check").inner_text())
            self.assertIn("已排除在余额合计之外", page.locator("#unknown-warning").inner_text())
            self.assertIn("¥0.00", page.locator("#unknown-warning").inner_text())
            snapshot = page.evaluate("window.KMFA_FUNDS_TEST.snapshot()")
            self.assertEqual(snapshot["accounts"]["unknown_amount_in_total_cents"], 0)
            self.assertEqual(snapshot["accounts"]["bank_reconciliation_difference_cents"], 0)
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_funds_account_reconciliation.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_03_scenarios_change_only_explicit_assumptions(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/funds", wait_until="networkidle")
            self.wait_ready(page)
            base_snapshot = page.evaluate("window.KMFA_FUNDS_TEST.snapshot().forecast")
            page.locator("#funds-scenario").select_option("collection_delay")
            page.wait_for_function("() => window.KMFA_FUNDS_TEST.snapshot()?.forecast?.scenario_id === 'collection_delay'")
            delayed = page.evaluate("window.KMFA_FUNDS_TEST.snapshot().forecast")
            self.assertEqual(base_snapshot["opening_cash_cents"], delayed["opening_cash_cents"])
            self.assertEqual(base_snapshot["events"], delayed["events"])
            self.assertNotEqual(base_snapshot["rows"][-1]["scenario_closing_cents"], delayed["rows"][-1]["scenario_closing_cents"])
            self.assertEqual(delayed["scenario_difference_cents"], 0)
            self.assertIn("65%", page.locator("#forecast-note").inner_text())
            self.assertIn("不是确定值", page.locator("#forecast-body").inner_text())
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_funds_scenario.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_04_loans_show_maturity_interest_margin_and_gap_without_execution(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/funds", wait_until="networkidle")
            self.wait_ready(page)
            self.assertEqual(page.locator("#loan-list .loan-card").count(), 3)
            loan_text = page.locator("#loan-list").inner_text()
            for token in ("到期", "本金", "预计利息", "保证金", "内部下一步"):
                self.assertIn(token, loan_text)
            self.assertEqual(page.locator("#gap-list .gap-card").count(), 4)
            self.assertIn("资金缺口", page.locator("#loans-title").inner_text())
            self.assertEqual(page.locator("button").filter(has_text="付款").count(), 0)
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_funds_loan_gap.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_05_company_switch_is_exact_and_never_mixed(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/funds", wait_until="networkidle")
            self.wait_ready(page)
            north = page.evaluate("window.KMFA_FUNDS_TEST.snapshot().summary.available_cash_cents")
            page.locator("#context-company").select_option("demo-west")
            page.wait_for_function("() => window.KMFA_FUNDS_TEST.snapshot()?.company_id === 'demo-west'")
            snapshot = page.evaluate("window.KMFA_FUNDS_TEST.snapshot()")
            self.assertTrue(all(row["company_id"] == "demo-west" for row in snapshot["accounts"]["accounts"]))
            self.assertEqual(snapshot["cross_company_leak_count"], 0)
            self.assertNotEqual(north, snapshot["summary"]["available_cash_cents"])
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_funds_company_isolated.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_06_period_switch_scopes_accounts_forecast_and_loans_together(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/funds", wait_until="networkidle")
            self.wait_ready(page)
            july = page.evaluate("window.KMFA_FUNDS_TEST.snapshot().summary.available_cash_cents")
            page.locator("#context-period").select_option("2026-Q2")
            page.wait_for_function("() => window.KMFA_FUNDS_TEST.snapshot()?.period === '2026-Q2'")
            snapshot = page.evaluate("window.KMFA_FUNDS_TEST.snapshot()")
            self.assertNotEqual(july, snapshot["summary"]["available_cash_cents"])
            self.assertEqual(snapshot["accounts"]["period"], "2026-Q2")
            self.assertEqual(snapshot["forecast"]["period"], "2026-Q2")
            self.assertEqual(snapshot["funding_plan"]["period"], "2026-Q2")
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_07_unknown_account_is_never_aggregated_in_any_scenario(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/funds", wait_until="networkidle")
            self.wait_ready(page)
            for scenario in ("base", "collection_delay", "cost_pressure"):
                page.locator("#funds-scenario").select_option(scenario)
                page.wait_for_function("value => window.KMFA_FUNDS_TEST.snapshot()?.forecast?.scenario_id === value", arg=scenario)
                snapshot = page.evaluate("window.KMFA_FUNDS_TEST.snapshot()")
                self.assertEqual(snapshot["accounts"]["unknown_amount_in_total_cents"], 0)
                self.assertEqual(snapshot["forecast"]["opening_cash_cents"], snapshot["accounts"]["total_available_cents"])
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_08_mobile_uses_cards_without_horizontal_overflow(self) -> None:
        page, errors = self.new_page(390, 844)
        try:
            page.goto(self.base_url + "/funds", wait_until="networkidle")
            self.wait_ready(page)
            self.assertTrue(page.locator("#accounts-mobile").is_visible())
            self.assertEqual(page.locator("#accounts-mobile .funds-mobile-card").count(), 4)
            self.assertEqual(page.locator("#forecast-mobile .funds-mobile-card").count(), 4)
            self.assertTrue(page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1"))
            height = page.locator("#funds-scenario").evaluate("node => Math.round(node.getBoundingClientRect().height)")
            self.assertGreaterEqual(height, 44)
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_funds_mobile.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()


if __name__ == "__main__":
    unittest.main()
