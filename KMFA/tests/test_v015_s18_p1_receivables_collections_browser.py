from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from playwright.sync_api import Browser, Page, Playwright, sync_playwright

from KMFA.tools import run_v015_s18_p1_receivables_collections as runtime


REPO_ROOT = Path(__file__).resolve().parents[2]
SCREENSHOT_ROOT = REPO_ROOT / "KMFA/stage_artifacts/V015_S18_P1_RECEIVABLES_COLLECTIONS/exports/screenshots"


class ReceivablesBrowserTests(unittest.TestCase):
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
        cls.server, cls.server_thread, cls.base_url = runtime.start_server(
            event_path=Path(cls.event_temp.name) / "events.jsonl"
        )
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
        cls.event_temp.cleanup()
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

    def wait_ready(self, page: Page) -> None:
        page.locator("#receivables-view").wait_for(state="visible")
        page.wait_for_function("() => window.KMFA_RECEIVABLES_TEST?.snapshot()?.rows?.length === 6")
        page.locator("#receivables-feedback", has_text="核对完成").wait_for()

    def test_01_desktop_shows_plain_chinese_cutoff_and_separate_totals(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/collections", wait_until="networkidle")
            self.wait_ready(page)
            self.assertEqual(page.locator("#receivables-cutoff").inner_text(), "2026-07-15")
            self.assertIn("仅已开票金额减已回款金额计入应收", page.locator("#receivables-definition").inner_text())
            labels = page.locator("#receivables-summary .receivables-metric>span").all_inner_texts()
            self.assertEqual(labels, ["已开票", "已回款", "筛选后应收", "筛选后逾期", "未开票节点"])
            self.assertEqual(page.get_by_role("button", name="联系客户").count(), 0)
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_receivables_desktop.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_02_priority_is_visible_and_explainable(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/collections", wait_until="networkidle")
            self.wait_ready(page)
            first = page.locator("#receivables-table-body tr").first
            self.assertIn("优先复核", first.inner_text())
            first.locator("details summary").click()
            text = first.inner_text()
            for token in ("金额项", "逾期项", "信用项", "争议项", "紧迫度项", "内部下一步"):
                self.assertIn(token, text)
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_receivables_priority_explained.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_03_filters_recalculate_summary_and_detail_exactly(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/collections", wait_until="networkidle")
            self.wait_ready(page)
            page.locator("#receivables-project").select_option("PUB-PROJ-001")
            page.wait_for_function("() => window.KMFA_RECEIVABLES_TEST.snapshot().filters.project === 'PUB-PROJ-001'")
            snapshot = page.evaluate("window.KMFA_RECEIVABLES_TEST.snapshot()")
            self.assertTrue(all(row["project_id"] == "PUB-PROJ-001" for row in snapshot["rows"]))
            self.assertEqual(snapshot["summary"]["receivable_cents"], sum(row["receivable_cents"] for row in snapshot["rows"]))
            self.assertEqual(snapshot["group_difference_cents"], 0)
            page.locator("#receivables-aging").select_option("D90_PLUS")
            page.wait_for_function("() => window.KMFA_RECEIVABLES_TEST.snapshot().filters.aging_bucket === 'D90_PLUS'")
            self.assertTrue(page.evaluate("window.KMFA_RECEIVABLES_TEST.snapshot().rows.every(row => row.aging_bucket_id === 'D90_PLUS')"))
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_receivables_filtered.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_04_all_group_dimensions_match_visible_detail(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/collections", wait_until="networkidle")
            self.wait_ready(page)
            for dimension in ("project", "customer", "period", "owner"):
                page.locator("#receivables-group").select_option(dimension)
                page.wait_for_function(
                    "dimension => window.KMFA_RECEIVABLES_TEST.snapshot().group_by === dimension",
                    arg=dimension,
                )
                self.assertEqual(page.evaluate("window.KMFA_RECEIVABLES_TEST.snapshot().group_difference_cents"), 0)
                self.assertIn("相差 0 分", page.locator("#receivables-group-check").inner_text())
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_05_missing_evidence_and_unbilled_fail_closed(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/collections", wait_until="networkidle")
            self.wait_ready(page)
            missing = page.locator("#receivables-table-body tr", has_text="资料不足")
            self.assertEqual(missing.count(), 1)
            self.assertNotIn("内部下一步", missing.inner_text())
            self.assertEqual(page.locator("#unbilled-list .unbilled-card").count(), 1)
            self.assertIn("不计入应收", page.locator(".unbilled-section").inner_text())
            snapshot = page.evaluate("window.KMFA_RECEIVABLES_TEST.snapshot()")
            self.assertEqual(snapshot["unbilled_items"][0]["receivable_cents"], 0)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_06_company_switch_never_mixes_entities(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/collections", wait_until="networkidle")
            self.wait_ready(page)
            north_total = page.evaluate("window.KMFA_RECEIVABLES_TEST.snapshot().summary.receivable_cents")
            page.locator("#context-company").select_option("demo-west")
            page.wait_for_function("() => window.KMFA_RECEIVABLES_TEST.snapshot()?.company_id === 'demo-west'")
            self.assertTrue(page.evaluate("window.KMFA_RECEIVABLES_TEST.snapshot().rows.every(row => row.company_id === 'demo-west')"))
            self.assertEqual(page.evaluate("window.KMFA_RECEIVABLES_TEST.snapshot().cross_company_leak_count"), 0)
            self.assertNotEqual(north_total, page.evaluate("window.KMFA_RECEIVABLES_TEST.snapshot().summary.receivable_cents"))
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_receivables_company_isolated.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_07_global_period_changes_amounts_without_losing_scope(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/collections", wait_until="networkidle")
            self.wait_ready(page)
            july_total = page.evaluate("window.KMFA_RECEIVABLES_TEST.snapshot().summary.receivable_cents")
            page.locator("#context-period").select_option("2026-Q2")
            page.wait_for_function("() => window.KMFA_RECEIVABLES_TEST.snapshot()?.period === '2026-Q2'")
            self.assertNotEqual(july_total, page.evaluate("window.KMFA_RECEIVABLES_TEST.snapshot().summary.receivable_cents"))
            self.assertTrue(page.evaluate("window.KMFA_RECEIVABLES_TEST.snapshot().rows.every(row => row.company_id === 'demo-north')"))
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_08_mobile_uses_cards_without_horizontal_overflow(self) -> None:
        page, errors = self.new_page(390, 844)
        try:
            page.goto(self.base_url + "/collections", wait_until="networkidle")
            self.wait_ready(page)
            self.assertTrue(page.locator("#receivables-mobile-list").is_visible())
            self.assertEqual(page.locator(".receivables-mobile-card").count(), 6)
            self.assertTrue(page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1"))
            heights = page.locator(".receivables-filters select").evaluate_all("nodes => nodes.map(node => Math.round(node.getBoundingClientRect().height))")
            self.assertTrue(all(height >= 44 for height in heights))
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_receivables_mobile.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()


if __name__ == "__main__":
    unittest.main()
