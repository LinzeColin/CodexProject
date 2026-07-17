from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from playwright.sync_api import Browser, Page, Playwright, sync_playwright

from KMFA.tools import run_v015_s17_p2_project_detail as runtime


REPO_ROOT = Path(__file__).resolve().parents[2]
SCREENSHOT_ROOT = REPO_ROOT / "KMFA/stage_artifacts/V015_S17_P2_PROJECT_DETAIL/exports/screenshots"


class ProjectDetailBrowserTests(unittest.TestCase):
    playwright: Playwright
    browser: Browser

    @classmethod
    def setUpClass(cls) -> None:
        global SCREENSHOT_ROOT
        cls.screenshot_temp = None
        if os.environ.get("KMFA_PRESERVE_TRACKED_SCREENSHOTS") == "1":
            cls.screenshot_temp = tempfile.TemporaryDirectory()
            SCREENSHOT_ROOT = Path(cls.screenshot_temp.name)
        cls.server, cls.server_thread, cls.base_url = runtime.start_server()
        cls.playwright = sync_playwright().start()
        chrome = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
        cls.browser = cls.playwright.chromium.launch(
            headless=True, executable_path=str(chrome) if chrome.is_file() else None
        )
        SCREENSHOT_ROOT.mkdir(parents=True, exist_ok=True)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.browser.close()
        cls.playwright.stop()
        cls.server.shutdown()
        cls.server.server_close()
        cls.server_thread.join(timeout=3)
        if cls.screenshot_temp is not None:
            cls.screenshot_temp.cleanup()

    def new_page(self, width: int = 1440, height: int = 1000) -> tuple[Page, list[str]]:
        page = self.browser.new_page(viewport={"width": width, "height": height})
        page.set_default_timeout(10_000)
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on(
            "console",
            lambda message: errors.append(message.text)
            if message.type == "error" and not message.text.startswith("Failed to load resource:")
            else None,
        )
        return page, errors

    def wait_detail(self, page: Page) -> None:
        page.locator("#project-detail-view").wait_for(state="visible")
        page.locator("#detail-feedback", has_text="项目详情已核对").wait_for()
        page.wait_for_function(
            "() => Boolean(window.KMFA_PROJECT_DETAIL_TEST?.snapshot()?.project?.project_id)"
        )

    def test_01_overview_answers_profitability_first(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/projects/PUB-PROJ-001", wait_until="networkidle")
            self.wait_detail(page)
            self.assertTrue(page.locator("#detail-panel-overview").is_visible())
            self.assertIn("项目目前赚钱", page.locator(".profit-verdict").inner_text())
            self.assertGreaterEqual(page.locator(".profit-reasons li").count(), 3)
            self.assertEqual(page.locator(".professional-basis").get_attribute("open"), None)
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_project_detail_overview.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_02_cost_chart_table_and_engine_totals_are_exact(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/projects/PUB-PROJ-001#cost", wait_until="networkidle")
            self.wait_detail(page)
            page.locator('#detail-tabs button[data-tab="cost"]').click()
            chart = page.evaluate("window.KMFA_PROJECT_DETAIL_TEST.chartAmounts()")
            table = page.evaluate("window.KMFA_PROJECT_DETAIL_TEST.tableAmounts()")
            snapshot = page.evaluate("window.KMFA_PROJECT_DETAIL_TEST.snapshot().cost")
            self.assertEqual(chart, table)
            self.assertEqual(sum(item[1] for item in chart) + snapshot["unallocated"]["amount_cents"], snapshot["actual_total_cents"])
            self.assertEqual(snapshot["engine_difference_cents"], 0)
            self.assertEqual(snapshot["chart_table_difference_cents"], 0)
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_project_detail_cost.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_03_cost_trend_and_unallocated_amount_are_visible(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/projects/PUB-PROJ-001#cost", wait_until="networkidle")
            self.wait_detail(page)
            self.assertEqual(page.locator(".trend-column").count(), 4)
            self.assertIn("未归集", page.locator(".unallocated-note").inner_text())
            self.assertEqual(
                page.evaluate("window.KMFA_PROJECT_DETAIL_TEST.snapshot().cost.trend_total_cents"),
                page.evaluate("window.KMFA_PROJECT_DETAIL_TEST.snapshot().cost.actual_total_cents"),
            )
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_04_revenue_collection_is_a_separate_business_flow(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/projects/PUB-PROJ-001", wait_until="networkidle")
            self.wait_detail(page)
            page.locator('#detail-tabs button[data-tab="revenue_collection"]').click()
            self.assertEqual(page.locator("#detail-panel-revenue_collection .flow-card").count(), 4)
            self.assertFalse(page.locator("#detail-panel-overview").is_visible())
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_project_detail_revenue.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_05_variance_rows_show_actual_baseline_difference_and_reason(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/projects/PUB-PROJ-001#variance", wait_until="networkidle")
            self.wait_detail(page)
            self.assertEqual(page.locator("#detail-panel-variance tbody tr").count(), 3)
            self.assertIn("不使用隐藏评分", page.locator("#detail-panel-variance").inner_text())
            rows = page.evaluate("window.KMFA_PROJECT_DETAIL_TEST.snapshot().variance.rows")
            self.assertTrue(all(row["variance_cents"] == row["actual_cents"] - row["baseline_cents"] for row in rows))
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_06_documents_do_not_repeat_financial_amounts(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/projects/PUB-PROJ-001#documents", wait_until="networkidle")
            self.wait_detail(page)
            self.assertEqual(page.locator(".document-item").count(), 6)
            documents = page.evaluate("window.KMFA_PROJECT_DETAIL_TEST.snapshot().documents.documents")
            self.assertTrue(all("amount_cents" not in row for row in documents))
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_project_detail_documents.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_07_list_to_detail_and_return_preserve_group_sort_and_page(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/projects", wait_until="networkidle")
            page.locator("#project-feedback", has_text="项目已核对").wait_for()
            page.locator("#project-group").select_option("risk")
            page.locator("#project-sort").select_option("margin")
            page.wait_for_function("() => window.KMFA_PROJECT_LIST_TEST.snapshot().group_by === 'risk' && window.KMFA_PROJECT_LIST_TEST.snapshot().sort_by === 'margin'")
            page.locator("#project-next").click()
            page.wait_for_function("() => window.KMFA_PROJECT_LIST_TEST.snapshot().page === 2")
            page.locator("#project-table-body .project-detail-link").first.click()
            self.wait_detail(page)
            page.locator("#detail-return").click()
            page.locator("#project-feedback", has_text="项目已核对").wait_for()
            state = page.evaluate("window.KMFA_PROJECT_LIST_TEST.state()")
            self.assertEqual((state["group_by"], state["sort_by"], state["page"]), ("risk", "margin", 2))
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_08_company_change_keeps_project_inside_selected_company(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/projects/PUB-PROJ-001", wait_until="networkidle")
            self.wait_detail(page)
            page.locator("#context-company").select_option("demo-west")
            page.wait_for_function("() => window.KMFA_PROJECT_DETAIL_TEST.snapshot()?.project?.company_id === 'demo-west'")
            self.assertEqual(page.evaluate("window.KMFA_PROJECT_DETAIL_TEST.snapshot().project.company_id"), "demo-west")
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_09_mobile_tabs_cards_and_tables_do_not_overflow(self) -> None:
        page, errors = self.new_page(390, 844)
        try:
            page.goto(self.base_url + "/projects/PUB-PROJ-001", wait_until="networkidle")
            self.wait_detail(page)
            self.assertGreaterEqual(page.locator(".detail-tab").first.evaluate("node => Math.round(node.getBoundingClientRect().height)"), 44)
            self.assertEqual(page.locator("#detail-panel-overview .detail-metric").count(), 8)
            self.assertTrue(page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1"))
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_project_detail_mobile.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()


if __name__ == "__main__":
    unittest.main()
