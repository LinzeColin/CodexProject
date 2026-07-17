from __future__ import annotations

import csv
import os
import tempfile
import unittest
from pathlib import Path

from playwright.sync_api import Browser, Page, Playwright, sync_playwright

from KMFA.tools import run_v015_s18_p3_relation_reporting as runtime


REPO_ROOT = Path(__file__).resolve().parents[2]
SCREENSHOT_ROOT = REPO_ROOT / "KMFA/stage_artifacts/V015_S18_P3_RELATION_REPORTING/exports/screenshots"


class RelationReportingBrowserTests(unittest.TestCase):
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
        page.locator("#funds-report-view").wait_for(state="visible")
        page.wait_for_function("() => window.KMFA_RELATION_TEST?.snapshot()?.dual_view?.rows?.length === 6")
        page.locator("#rr-feedback", has_text="核对完成").wait_for()

    def test_01_desktop_shows_dual_view_in_plain_chinese(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/funds-report", wait_until="networkidle")
            self.wait_ready(page)
            self.assertEqual(page.locator("#rr-dual-body tr").count(), 6)
            basis = page.locator("#rr-basis-title").inner_text() + page.locator(".rr-basis p").inner_text()
            for token in ("两套口径", "项目利润", "资金占用", "不能互相替代"):
                self.assertIn(token, basis)
            self.assertIn("金额相差 0 分", page.locator("#rr-basis-check").inner_text())
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_relation_dual_view_desktop.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_02_profit_never_substitutes_for_cash(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/funds-report", wait_until="networkidle")
            self.wait_ready(page)
            snapshot = page.evaluate("window.KMFA_RELATION_TEST.snapshot()")
            self.assertEqual(snapshot["profit_used_as_cash_count"], 0)
            for row in snapshot["dual_view"]["rows"]:
                self.assertEqual(row["revenue_cents"], row["cost_cents"] + row["gross_profit_cents"])
                self.assertEqual(row["cash_occupied_cents"], row["open_receivable_cents"] + row["unbilled_cents"])
                self.assertNotEqual(row["profit_basis_zh"], row["cash_basis_zh"])
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_relation_cross_basis.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_03_alerts_use_external_thresholds_and_minimal_detail(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/funds-report", wait_until="networkidle")
            self.wait_ready(page)
            self.assertEqual(page.locator("#rr-alert-list .rr-alert-card").count(), 5)
            self.assertEqual(page.locator("#rr-alert-list .rr-alert-action").count(), 5)
            text = page.locator("#rr-alert-list").inner_text()
            for token in ("重大逾期", "资金缺口", "贷款到期", "内部下一步", "打开回款明细", "打开资金明细"):
                self.assertIn(token, text)
            first_href = page.locator("#rr-alert-list .rr-alert-action").first.get_attribute("href") or ""
            self.assertIn("/collections?", first_href)
            self.assertIn("company_id=demo-north", first_href)
            self.assertIn("period=2026-07", first_href)
            self.assertIn("阈值版本", page.locator("#rr-threshold-version").inner_text())
            snapshot = page.evaluate("window.KMFA_RELATION_TEST.snapshot().alert_view")
            self.assertEqual(snapshot["alert_type_count"], 3)
            self.assertEqual(snapshot["full_sensitive_detail_count"], 0)
            self.assertEqual(snapshot["notification_send_count"], 0)
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_relation_alerts.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_04_scenario_switch_changes_only_funding_gap_alert(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/funds-report", wait_until="networkidle")
            self.wait_ready(page)
            delayed = page.evaluate("window.KMFA_RELATION_TEST.snapshot()")
            page.locator("#rr-scenario").select_option("base")
            page.wait_for_function("() => window.KMFA_RELATION_TEST.snapshot()?.scenario_id === 'base'")
            base = page.evaluate("window.KMFA_RELATION_TEST.snapshot()")
            self.assertEqual(delayed["dual_view"], base["dual_view"])
            self.assertEqual(delayed["alert_view"]["alert_count_by_type"]["FUNDING_GAP"], 1)
            self.assertEqual(base["alert_view"]["alert_count_by_type"]["FUNDING_GAP"], 0)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_05_html_period_report_matches_page(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/funds-report", wait_until="networkidle")
            self.wait_ready(page)
            snapshot = page.evaluate("window.KMFA_RELATION_TEST.snapshot()")
            href = page.locator("#rr-html-export").get_attribute("href")
            self.assertIsNotNone(href)
            page.goto(self.base_url + str(href), wait_until="networkidle")
            self.assertIn("利润和现金是两套数字", page.locator("body").inner_text())
            self.assertEqual(page.locator("tbody tr").count(), 6)
            first = page.locator("tbody tr").first
            self.assertEqual(int(first.get_attribute("data-revenue") or "-1"), snapshot["report"]["page_rows"][0]["revenue_cents"])
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_relation_period_report.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_06_csv_download_matches_page_amounts(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/funds-report", wait_until="networkidle")
            self.wait_ready(page)
            expected = [row["cash_occupied_cents"] for row in page.evaluate("window.KMFA_RELATION_TEST.snapshot().report.page_rows")]
            with page.expect_download() as info:
                page.locator("#rr-csv-export").click()
            download = info.value
            rows = list(csv.DictReader(Path(download.path()).read_text(encoding="utf-8-sig").splitlines()))
            self.assertEqual([int(row["资金占用(分)"]) for row in rows], expected)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_07_unverified_data_degrades_and_hides_numbers(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/funds-report", wait_until="networkidle")
            self.wait_ready(page)
            page.locator("#rr-verification").select_option("UNVERIFIED")
            page.wait_for_function("() => window.KMFA_RELATION_TEST.snapshot()?.verification_state === 'UNVERIFIED'")
            page.locator("#rr-feedback", has_text="报告已降级").wait_for()
            snapshot = page.evaluate("window.KMFA_RELATION_TEST.snapshot()")
            self.assertTrue(snapshot["report_degraded"])
            self.assertEqual(snapshot["report"]["report_grade"], "D")
            self.assertEqual(snapshot["alert_view"]["alert_count"], 0)
            self.assertTrue(all(row["revenue_cents"] is None and row["cash_occupied_cents"] is None for row in snapshot["dual_view"]["rows"]))
            self.assertTrue(all(value == "暂不可用" for value in page.locator("#rr-dual-body tr td:nth-child(2)").all_inner_texts()))
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_relation_degraded.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_08_company_and_period_switch_stay_isolated(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/funds-report", wait_until="networkidle")
            self.wait_ready(page)
            north = page.evaluate("window.KMFA_RELATION_TEST.snapshot().dual_view.totals.cash_occupied_cents")
            page.locator("#context-company").select_option("demo-west")
            page.locator("#context-period").select_option("2026-Q2")
            page.wait_for_function("() => window.KMFA_RELATION_TEST.snapshot()?.company_id === 'demo-west' && window.KMFA_RELATION_TEST.snapshot()?.period === '2026-Q2'")
            snapshot = page.evaluate("window.KMFA_RELATION_TEST.snapshot()")
            self.assertTrue(all(row["company_id"] == "demo-west" for row in snapshot["dual_view"]["rows"]))
            self.assertNotEqual(north, snapshot["dual_view"]["totals"]["cash_occupied_cents"])
            self.assertEqual(snapshot["dual_view"]["cross_company_leak_count"], 0)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_09_mobile_cards_have_no_horizontal_overflow(self) -> None:
        page, errors = self.new_page(390, 844)
        try:
            page.goto(self.base_url + "/funds-report", wait_until="networkidle")
            self.wait_ready(page)
            self.assertTrue(page.locator("#rr-dual-mobile").is_visible())
            self.assertEqual(page.locator("#rr-dual-mobile .rr-mobile-card").count(), 6)
            self.assertTrue(page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1"))
            for selector in ("#rr-scenario", "#rr-verification"):
                height = page.locator(selector).evaluate("node => Math.round(node.getBoundingClientRect().height)")
                self.assertGreaterEqual(height, 44)
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_relation_mobile.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()


if __name__ == "__main__":
    unittest.main()
