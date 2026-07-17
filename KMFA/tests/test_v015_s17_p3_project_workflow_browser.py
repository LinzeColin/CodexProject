from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from playwright.sync_api import Browser, Error, Page, Playwright, sync_playwright

from KMFA.tools import run_v015_s17_p3_project_workflow as runtime


REPO_ROOT = Path(__file__).resolve().parents[2]
SCREENSHOT_ROOT = REPO_ROOT / "KMFA/stage_artifacts/V015_S17_P3_PROJECT_WORKFLOW/exports/screenshots"


class ProjectWorkflowBrowserTests(unittest.TestCase):
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
            headless=True, executable_path=str(chrome) if chrome.is_file() else None
        )
        SCREENSHOT_ROOT.mkdir(parents=True, exist_ok=True)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.browser.close()
        cls.playwright.stop()
        cls.server.shutdown()
        cls.server.server_close()
        cls.server_thread.join(timeout=5)
        cls.temp.cleanup()

    def new_page(self, width: int = 1440, height: int = 1100) -> tuple[Page, list[str]]:
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

    def wait_workflow(self, page: Page) -> None:
        page.locator("#project-detail-view").wait_for(state="visible")
        page.locator("#project-workflow-view").wait_for(state="visible")
        page.wait_for_function(
            "() => Boolean(window.KMFA_PROJECT_DETAIL_TEST?.snapshot()?.project?.project_id && window.KMFA_PROJECT_WORKFLOW_TEST?.snapshot()?.project_id)"
        )
        page.locator("#workflow-feedback", has_text="处理记录已读取").wait_for()

    def test_01_candidates_sources_and_impact_are_visible_before_confirmation(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/projects/PUB-PROJ-001", wait_until="networkidle")
            self.wait_workflow(page)
            self.assertEqual(page.locator(".candidate-option").count(), 3)
            self.assertEqual(page.locator(".source-compare tbody tr").count(), 2)
            self.assertIn("依据", page.locator("#assignment-preview").inner_text())
            self.assertIn("项目总成本不变", page.locator("#assignment-preview").inner_text())
            self.assertIn("差异", page.locator("#variance-summary").inner_text())
            page.locator("#project-workflow-view").screenshot(
                path=str(SCREENSHOT_ROOT / "kmfa_project_workflow_before.png")
            )
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_02_candidate_selection_updates_human_impact_preview(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/projects/PUB-PROJ-001", wait_until="networkidle")
            self.wait_workflow(page)
            page.locator('input[value="CAND-S17P3-003"]').check()
            preview = page.locator("#assignment-preview").inner_text()
            self.assertIn("项目不一致", preview)
            self.assertIn("禁止自动归集", preview)
            page.locator("#project-workflow-view").screenshot(
                path=str(SCREENSHOT_ROOT / "kmfa_project_workflow_candidate_preview.png")
            )
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_03_high_confidence_assignment_persists_and_updates_detail(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/projects/PUB-PROJ-001#cost", wait_until="networkidle")
            self.wait_workflow(page)
            page.evaluate(
                "window.KMFA_PROJECT_WORKFLOW_TEST.assign('CAND-S17P3-001','browser-assignment-001')"
            )
            page.wait_for_function(
                "() => window.KMFA_PROJECT_WORKFLOW_TEST.snapshot().event_count === 1 && window.KMFA_PROJECT_WORKFLOW_TEST.snapshot().projection.cost.unallocated.amount_cents === 0"
            )
            self.assertEqual(page.evaluate("window.KMFA_PROJECT_DETAIL_TEST.snapshot().cost.unallocated.amount_cents"), 0)
            self.assertEqual(page.locator("#workflow-events tr").count(), 1)
            self.assertIn("源数据没有修改", page.locator("#workflow-feedback").inner_text())
            page.locator("#project-workflow-view").screenshot(
                path=str(SCREENSHOT_ROOT / "kmfa_project_workflow_assignment.png")
            )
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_04_low_confidence_auto_assignment_fails_closed_without_new_event(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/projects/PUB-PROJ-001", wait_until="networkidle")
            self.wait_workflow(page)
            with self.assertRaises(Error):
                page.evaluate(
                    "window.KMFA_PROJECT_WORKFLOW_TEST.assign('CAND-S17P3-003','browser-low-confidence-001')"
                )
            page.locator("#workflow-feedback", has_text="低置信").wait_for()
            self.assertEqual(page.evaluate("window.KMFA_PROJECT_WORKFLOW_TEST.snapshot().event_count"), 1)
            page.locator("#project-workflow-view").screenshot(
                path=str(SCREENSHOT_ROOT / "kmfa_project_workflow_low_confidence_rejected.png")
            )
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_05_assignment_can_be_reversed_and_reconfirmed(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/projects/PUB-PROJ-001", wait_until="networkidle")
            self.wait_workflow(page)
            event_id = page.evaluate("window.KMFA_PROJECT_WORKFLOW_TEST.snapshot().events[0].event_id")
            page.evaluate(
                "([eventId]) => window.KMFA_PROJECT_WORKFLOW_TEST.reverse(eventId,'browser-reversal-001')",
                [event_id],
            )
            page.wait_for_function(
                "() => window.KMFA_PROJECT_WORKFLOW_TEST.snapshot().event_count === 2 && window.KMFA_PROJECT_WORKFLOW_TEST.snapshot().projection.cost.unallocated.amount_cents > 0"
            )
            page.evaluate(
                "window.KMFA_PROJECT_WORKFLOW_TEST.assign('CAND-S17P3-001','browser-assignment-002')"
            )
            page.wait_for_function(
                "() => window.KMFA_PROJECT_WORKFLOW_TEST.snapshot().event_count === 3 && window.KMFA_PROJECT_WORKFLOW_TEST.snapshot().projection.cost.unallocated.amount_cents === 0"
            )
            snapshot = page.evaluate("window.KMFA_PROJECT_WORKFLOW_TEST.snapshot()")
            self.assertEqual(snapshot["reversal_event_count"], 1)
            self.assertEqual(snapshot["active_domain_event_count"], 1)
            self.assertEqual(snapshot["source_data_write_count"], 0)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_06_variance_sources_and_impact_are_compared_before_confirmation(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/projects/PUB-PROJ-001", wait_until="networkidle")
            self.wait_workflow(page)
            source_amounts = page.evaluate(
                "window.KMFA_PROJECT_WORKFLOW_TEST.snapshot().variance_work_item.sources.map(row => row.amount_cents)"
            )
            self.assertEqual(len(source_amounts), 2)
            self.assertNotEqual(source_amounts[0], source_amounts[1])
            page.locator("#variance-option").select_option("USE_SETTLEMENT_SUPPORT")
            self.assertIn("确认后成本", page.locator("#variance-preview").inner_text())
            self.assertIn("页面、毛利和专题报告将一起重算", page.locator("#variance-preview").inner_text())
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_07_variance_confirmation_reruns_page_and_report_together(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/projects/PUB-PROJ-001", wait_until="networkidle")
            self.wait_workflow(page)
            page.evaluate(
                "window.KMFA_PROJECT_WORKFLOW_TEST.resolveVariance('USE_SETTLEMENT_SUPPORT','browser-variance-001')"
            )
            page.wait_for_function(
                "() => window.KMFA_PROJECT_WORKFLOW_TEST.snapshot().event_count === 5 && window.KMFA_PROJECT_WORKFLOW_TEST.snapshot().projection.workflow_projection.report_sync_status === 'PASS'"
            )
            workflow = page.evaluate("window.KMFA_PROJECT_WORKFLOW_TEST.snapshot()")
            detail = page.evaluate("window.KMFA_PROJECT_DETAIL_TEST.snapshot()")
            self.assertEqual(workflow["projection"]["cost"]["actual_total_cents"], detail["cost"]["actual_total_cents"])
            self.assertEqual(workflow["projection"]["workflow_projection"]["money_difference_cents"], 0)
            self.assertEqual(page.locator("#workflow-sync-state").inner_text(), "页面与报告一致")
            page.locator("#project-workflow-view").screenshot(
                path=str(SCREENSHOT_ROOT / "kmfa_project_workflow_variance_rerun.png")
            )
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_08_events_survive_runtime_restart(self) -> None:
        type(self).server.shutdown()
        type(self).server.server_close()
        type(self).server_thread.join(timeout=5)
        type(self).server, type(self).server_thread, type(self).base_url = runtime.start_server(
            event_path=type(self).event_path
        )
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/projects/PUB-PROJ-001", wait_until="networkidle")
            self.wait_workflow(page)
            snapshot = page.evaluate("window.KMFA_PROJECT_WORKFLOW_TEST.snapshot()")
            self.assertEqual(snapshot["event_count"], 5)
            self.assertEqual(snapshot["projection"]["workflow_projection"]["report_sync_status"], "PASS")
            self.assertEqual(snapshot["projection"]["cost"]["unallocated"]["amount_cents"], 0)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_09_html_pdf_xlsx_report_links_are_downloadable(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/projects/PUB-PROJ-001", wait_until="networkidle")
            self.wait_workflow(page)
            links = page.evaluate("window.KMFA_PROJECT_WORKFLOW_TEST.reportLinks()")
            self.assertEqual([urlsplit(link).path for link in links], [
                "/reports/project-cost.html",
                "/reports/project-cost.pdf",
                "/reports/project-cost.xlsx",
            ])
            for link in links:
                query = parse_qs(urlsplit(link).query)
                self.assertEqual(query["company_id"], ["demo-north"])
                self.assertEqual(query["project_id"], ["PUB-PROJ-001"])
            expected_types = ("text/html", "application/pdf", "spreadsheetml.sheet")
            for link, expected in zip(links, expected_types):
                response = page.request.get(self.base_url + link)
                self.assertEqual(response.status, 200)
                self.assertIn(expected, response.headers.get("content-type", ""))
                self.assertGreater(len(response.body()), 1_000)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_10_mobile_workflow_is_readable_and_does_not_overflow(self) -> None:
        page, errors = self.new_page(390, 844)
        try:
            page.goto(self.base_url + "/projects/PUB-PROJ-001", wait_until="networkidle")
            self.wait_workflow(page)
            self.assertTrue(page.locator(".workflow-card").first.is_visible())
            self.assertGreaterEqual(
                page.locator("#confirm-variance").evaluate("node => Math.round(node.getBoundingClientRect().height)"),
                42,
            )
            self.assertTrue(page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1"))
            page.screenshot(
                path=str(SCREENSHOT_ROOT / "kmfa_project_workflow_mobile.png"), full_page=True
            )
            self.assertEqual(errors, [])
        finally:
            page.close()


if __name__ == "__main__":
    unittest.main()
