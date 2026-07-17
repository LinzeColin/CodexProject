from __future__ import annotations

import csv
import os
import tempfile
import unittest
from pathlib import Path

from playwright.sync_api import Browser, Page, Playwright, sync_playwright

from KMFA.tools import run_v015_s17_p1_project_list as runtime


REPO_ROOT = Path(__file__).resolve().parents[2]
SCREENSHOT_ROOT = REPO_ROOT / "KMFA/stage_artifacts/V015_S17_P1_PROJECT_LIST/exports/screenshots"


class ProjectListBrowserTests(unittest.TestCase):
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
        cls.browser = cls.playwright.chromium.launch(headless=True, executable_path=str(chrome) if chrome.is_file() else None)
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
        page = self.browser.new_page(viewport={"width": width, "height": height}, accept_downloads=True)
        page.set_default_timeout(10_000)
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("console", lambda message: errors.append(message.text) if message.type == "error" and not message.text.startswith("Failed to load resource:") else None)
        return page, errors

    def wait_ready(self, page: Page) -> None:
        page.locator("#project-list-view").wait_for(state="visible")
        page.locator("#project-feedback", has_text="项目已核对").wait_for()
        page.locator("#project-table-body tr[data-project-id]").nth(3).wait_for(state="attached")
        page.wait_for_function("() => window.KMFA_PROJECT_LIST_TEST?.snapshot()?.filtered_count === 6")

    def test_01_desktop_default_is_clear_and_not_overloaded(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/projects", wait_until="networkidle")
            self.wait_ready(page)
            self.assertEqual(page.locator("#project-table-head th").count(), 8)
            self.assertEqual(page.locator("#project-table-body tr[data-project-id]").count(), 4)
            self.assertIn("没有隐藏评分", page.locator("#project-order-explanation").inner_text())
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_projects_desktop.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_02_filter_group_sort_and_pagination_keep_project_ids_aligned(self) -> None:
        page, errors = self.new_page()
        try:
            page.emulate_media(reduced_motion="reduce")
            page.goto(self.base_url + "/projects", wait_until="networkidle")
            self.wait_ready(page)
            first_ids = page.locator("#project-table-body tr[data-project-id]").evaluate_all("rows => rows.map(row => row.dataset.projectId)")
            page.locator("#project-next").click()
            page.wait_for_function("() => window.KMFA_PROJECT_LIST_TEST.snapshot().page === 2")
            second_ids = page.locator("#project-table-body tr[data-project-id]").evaluate_all("rows => rows.map(row => row.dataset.projectId)")
            self.assertEqual(len(set(first_ids + second_ids)), 6)
            page.locator("#project-risk").select_option("HIGH")
            page.wait_for_function("() => window.KMFA_PROJECT_LIST_TEST.snapshot().filtered_count === 1")
            self.assertEqual(page.locator("#project-table-body tr[data-project-id]").count(), 1)
            page.locator("#project-risk").select_option("all")
            page.locator("#project-group").select_option("risk")
            page.locator("#project-sort").select_option("margin")
            page.wait_for_function("() => window.KMFA_PROJECT_LIST_TEST.snapshot().group_by === 'risk' && window.KMFA_PROJECT_LIST_TEST.snapshot().sort_by === 'margin'")
            page.locator("#project-feedback", has_text="项目已核对").wait_for()
            page.evaluate("document.activeElement?.blur()")
            self.assertGreaterEqual(page.locator(".project-group-row").count(), 2)
            self.assertIn("毛利率最低优先", page.locator("#project-order-explanation").inner_text())
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_projects_grouped.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_03_column_configuration_persists_without_changing_facts(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/projects", wait_until="networkidle")
            self.wait_ready(page)
            before = page.evaluate("window.KMFA_PROJECT_LIST_TEST.snapshot().rows.map(row => [row.project_id,row.revenue_cents])")
            page.locator("#project-columns summary").click()
            page.locator('#project-column-options input[value="client"]').uncheck()
            page.locator('#project-column-options input[value="revenue"]').check()
            self.assertIn("收入", page.locator("#project-table-head").inner_text())
            self.assertNotIn("客户", page.locator("#project-table-head").inner_text())
            page.reload(wait_until="networkidle")
            self.wait_ready(page)
            self.assertIn("收入", page.locator("#project-table-head").inner_text())
            after = page.evaluate("window.KMFA_PROJECT_LIST_TEST.snapshot().rows.map(row => [row.project_id,row.revenue_cents])")
            self.assertEqual(before, after)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_04_batch_compare_totals_match_selected_rows(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/projects", wait_until="networkidle")
            self.wait_ready(page)
            page.locator("#project-table-body .row-select").nth(0).check()
            page.locator("#project-table-body .row-select").nth(1).check()
            self.assertEqual(page.locator("#project-selected-count").inner_text(), "2")
            page.locator("#project-compare").click()
            page.locator("#project-comparison").wait_for(state="visible")
            self.assertEqual(page.locator("#project-comparison-body tr").count(), 2)
            self.assertIn("没有修改项目事实", page.locator("#project-feedback").inner_text())
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_projects_comparison.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_05_export_contains_same_projects_and_source_columns(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/projects", wait_until="networkidle")
            self.wait_ready(page)
            page.locator("#project-table-body .row-select").nth(0).check()
            page.locator("#project-table-body .row-select").nth(1).check()
            selected = page.evaluate("window.KMFA_PROJECT_LIST_TEST.selected()")
            with page.expect_download() as download_info:
                page.locator("#project-export").click()
            content = Path(download_info.value.path()).read_text(encoding="utf-8-sig")
            rows = list(csv.DictReader(content.splitlines()))
            self.assertEqual([row["项目编号"] for row in rows], selected)
            self.assertTrue(all(row["来源说明"] and row["来源编号"] and row["数据截止日"] for row in rows))
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_06_global_company_and_status_filters_refresh_without_cross_scope_rows(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/projects", wait_until="networkidle")
            self.wait_ready(page)
            page.locator("#context-company").select_option("demo-west")
            page.wait_for_function("() => window.KMFA_PROJECT_LIST_TEST.snapshot()?.context.company_id === 'demo-west'")
            self.assertTrue(page.evaluate("window.KMFA_PROJECT_LIST_TEST.snapshot().rows.every(row => row.company_id === 'demo-west')"))
            page.locator("#context-project_status").select_option("attention")
            page.wait_for_function("() => window.KMFA_PROJECT_LIST_TEST.snapshot()?.context.project_status === 'attention'")
            self.assertTrue(page.evaluate("window.KMFA_PROJECT_LIST_TEST.snapshot().rows.every(row => row.status === 'ATTENTION')"))
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_07_mobile_uses_cards_without_horizontal_overflow(self) -> None:
        page, errors = self.new_page(390, 844)
        try:
            page.goto(self.base_url + "/projects", wait_until="networkidle")
            self.wait_ready(page)
            self.assertTrue(page.locator("#project-mobile-list").is_visible())
            self.assertEqual(page.locator(".project-card").count(), 4)
            self.assertTrue(page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1"))
            self.assertGreaterEqual(page.locator("#project-risk").evaluate("node => Math.round(node.getBoundingClientRect().height)"), 44)
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_projects_mobile.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_08_batch_selection_survives_pagination_but_clears_on_scope_change(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/projects", wait_until="networkidle")
            self.wait_ready(page)
            page.locator("#project-table-body .row-select").first.check()
            page.locator("#project-next").click()
            page.wait_for_function("() => window.KMFA_PROJECT_LIST_TEST.snapshot().page === 2")
            self.assertEqual(page.locator("#project-selected-count").inner_text(), "1")
            page.locator("#context-company").select_option("demo-south")
            page.wait_for_function("() => window.KMFA_PROJECT_LIST_TEST.snapshot()?.context.company_id === 'demo-south'")
            self.assertEqual(page.evaluate("window.KMFA_PROJECT_LIST_TEST.selected().length"), 0)
            self.assertEqual(errors, [])
        finally:
            page.close()


if __name__ == "__main__":
    unittest.main()
