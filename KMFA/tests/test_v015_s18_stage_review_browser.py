from __future__ import annotations

import csv
import os
import tempfile
import unittest
from pathlib import Path

from playwright.sync_api import Browser, Page, Playwright, sync_playwright

from KMFA.tools import run_v015_s18_p3_relation_reporting as runtime


REPO_ROOT = Path(__file__).resolve().parents[2]
SCREENSHOT_ROOT = REPO_ROOT / "KMFA/stage_artifacts/V015_S18_STAGE_REVIEW/exports/screenshots"


class S18StageReviewBrowserTests(unittest.TestCase):
    playwright: Playwright
    browser: Browser

    @classmethod
    def setUpClass(cls) -> None:
        global SCREENSHOT_ROOT
        cls.temp = tempfile.TemporaryDirectory()
        if os.environ.get("KMFA_PRESERVE_TRACKED_SCREENSHOTS") == "1":
            SCREENSHOT_ROOT = Path(cls.temp.name) / "screenshots"
        cls.event_path = Path(cls.temp.name) / "events.jsonl"
        cls.server, cls.server_thread, cls.base_url = runtime.start_server(event_path=cls.event_path)
        cls.playwright = sync_playwright().start()
        chrome = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
        cls.browser = cls.playwright.chromium.launch(
            headless=True,
            executable_path=str(chrome) if chrome.is_file() else None,
        )
        SCREENSHOT_ROOT.mkdir(parents=True, exist_ok=True)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.browser.close()
        cls.playwright.stop()
        cls.server.shutdown()
        cls.server.server_close()
        cls.server_thread.join(timeout=3)
        cls.temp.cleanup()

    def setUp(self) -> None:
        if self.event_path.exists():
            self.event_path.unlink()

    def new_page(self, width: int = 1440, height: int = 1000) -> tuple[Page, list[str]]:
        page = self.browser.new_page(viewport={"width": width, "height": height})
        page.set_default_timeout(12_000)
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on(
            "console",
            lambda message: errors.append(message.text)
            if message.type == "error" and not message.text.startswith("Failed to load resource:")
            else None,
        )
        return page, errors

    def wait_report(self, page: Page) -> None:
        page.locator("#funds-report-view").wait_for(state="visible")
        page.wait_for_function("() => window.KMFA_RELATION_TEST?.snapshot()?.dual_view?.rows?.length === 6")
        page.locator("#rr-feedback", has_text="核对完成").wait_for()

    def wait_workflow(self, page: Page) -> None:
        page.locator("#project-detail-view").wait_for(state="visible")
        page.locator("#project-workflow-view").wait_for(state="visible")
        page.wait_for_function("() => Boolean(window.KMFA_PROJECT_WORKFLOW_TEST?.snapshot()?.project_id)")

    def test_01_desktop_connects_receivables_funds_and_report(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/funds-report", wait_until="networkidle")
            self.wait_report(page)
            self.assertEqual(page.locator("#rr-dual-body tr").count(), 6)
            self.assertEqual(page.locator(".rr-alert-action").count(), 5)
            self.assertIn("利润未替代现金", page.locator("#rr-basis-check").inner_text())
            page.screenshot(
                path=str(SCREENSHOT_ROOT / "kmfa_s18_review_dashboard.png"),
                full_page=True,
            )
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_02_current_project_cost_reaches_page_html_and_csv(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/projects/PUB-PROJ-001", wait_until="networkidle")
            self.wait_workflow(page)
            page.evaluate(
                "() => window.KMFA_PROJECT_WORKFLOW_TEST.resolveVariance('USE_SETTLEMENT_SUPPORT', 's18-review-browser-current-001')"
            )
            page.wait_for_function(
                "() => window.KMFA_PROJECT_WORKFLOW_TEST.snapshot().projection.cost.actual_total_cents === 234552000"
            )
            page.goto(self.base_url + "/funds-report", wait_until="networkidle")
            self.wait_report(page)
            snapshot = page.evaluate("window.KMFA_RELATION_TEST.snapshot()")
            current = next(row for row in snapshot["dual_view"]["rows"] if row["project_id"] == "PUB-PROJ-001")
            self.assertEqual(current["cost_cents"], 234_552_000)
            page.screenshot(
                path=str(SCREENSHOT_ROOT / "kmfa_s18_review_current_projection.png"),
                full_page=True,
            )
            href = page.locator("#rr-html-export").get_attribute("href")
            self.assertIsNotNone(href)
            page.goto(self.base_url + str(href), wait_until="networkidle")
            self.assertIn("¥2,345,520.00", page.locator("body").inner_text())

            page.goto(self.base_url + "/funds-report", wait_until="networkidle")
            self.wait_report(page)
            with page.expect_download() as info:
                page.locator("#rr-csv-export").click()
            rows = list(
                csv.DictReader(
                    Path(info.value.path()).read_text(encoding="utf-8-sig").splitlines()
                )
            )
            exported = next(row for row in rows if row["项目编号"] == "PUB-PROJ-001")
            self.assertEqual(int(exported["成本(分)"]), 234_552_000)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_03_alerts_open_the_right_detail_with_context(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/funds-report", wait_until="networkidle")
            self.wait_report(page)
            page.get_by_text("打开回款明细").first.click()
            page.wait_for_url("**/collections?**")
            page.locator("#receivables-view").wait_for(state="visible")
            self.assertIn("company=demo-north", page.url)
            self.assertIn("period=2026-07", page.url)
            page.screenshot(
                path=str(SCREENSHOT_ROOT / "kmfa_s18_review_alert_navigation.png"),
                full_page=True,
            )

            page.goto(self.base_url + "/funds-report", wait_until="networkidle")
            self.wait_report(page)
            page.get_by_text("打开资金明细").first.click()
            page.wait_for_url("**/funds?**")
            page.locator("#funds-view").wait_for(state="visible")
            self.assertIn("company=demo-north", page.url)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_04_tablet_unverified_mode_is_clear_and_safe(self) -> None:
        page, errors = self.new_page(820, 1180)
        try:
            page.goto(self.base_url + "/funds-report", wait_until="networkidle")
            self.wait_report(page)
            page.locator("#rr-verification").select_option("UNVERIFIED")
            page.wait_for_function("() => window.KMFA_RELATION_TEST.snapshot()?.verification_state === 'UNVERIFIED'")
            snapshot = page.evaluate("window.KMFA_RELATION_TEST.snapshot()")
            self.assertEqual(snapshot["alert_view"]["alert_count"], 0)
            self.assertTrue(all(value is None for value in snapshot["dual_view"]["totals"].values()))
            self.assertTrue(page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1"))
            page.screenshot(
                path=str(SCREENSHOT_ROOT / "kmfa_s18_review_tablet.png"),
                full_page=True,
            )
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_05_mobile_has_no_overflow_and_keeps_44px_actions(self) -> None:
        page, errors = self.new_page(390, 844)
        try:
            page.goto(self.base_url + "/funds-report", wait_until="networkidle")
            self.wait_report(page)
            self.assertTrue(page.locator("#rr-dual-mobile").is_visible())
            self.assertEqual(page.locator("#rr-dual-mobile .rr-mobile-card").count(), 6)
            self.assertTrue(page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1"))
            heights = page.locator(".rr-alert-action").evaluate_all(
                "nodes => nodes.map(node => Math.round(node.getBoundingClientRect().height))"
            )
            self.assertTrue(heights and min(heights) >= 44)
            page.screenshot(
                path=str(SCREENSHOT_ROOT / "kmfa_s18_review_mobile.png"),
                full_page=True,
            )
            self.assertEqual(errors, [])
        finally:
            page.close()


if __name__ == "__main__":
    unittest.main()
