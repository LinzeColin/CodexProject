from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from urllib.parse import urlencode

from playwright.sync_api import Browser, Error, Page, Playwright, sync_playwright

from KMFA.tools import run_v015_s17_p3_project_workflow as runtime


REPO_ROOT = Path(__file__).resolve().parents[2]
SCREENSHOT_ROOT = REPO_ROOT / "KMFA/stage_artifacts/V015_S17_STAGE_REVIEW/exports/screenshots"


class S17StageReviewBrowserTests(unittest.TestCase):
    playwright: Playwright
    browser: Browser

    @classmethod
    def setUpClass(cls) -> None:
        global SCREENSHOT_ROOT
        cls.original_now = runtime.kernel._now
        runtime.kernel._now = lambda: "2026-07-16T18:20:00+10:00"
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
        cls.server_thread.join(timeout=5)
        cls.temp.cleanup()
        runtime.kernel._now = cls.original_now

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

    def wait_list(self, page: Page) -> None:
        page.locator("#project-list-view").wait_for(state="visible")
        page.locator("#project-feedback", has_text="项目已核对").wait_for()
        page.wait_for_function("() => Boolean(window.KMFA_PROJECT_LIST_TEST?.snapshot()?.rows)")

    def wait_workflow(self, page: Page) -> None:
        page.locator("#project-detail-view").wait_for(state="visible")
        page.locator("#project-workflow-view").wait_for(state="visible")
        page.locator("#workflow-feedback", has_text="处理记录已读取").wait_for()
        page.wait_for_function(
            "() => Boolean(window.KMFA_PROJECT_DETAIL_TEST?.snapshot()?.project?.project_id && window.KMFA_PROJECT_WORKFLOW_TEST?.snapshot()?.project_id)"
        )

    def resolve_variance(self, page: Page, key: str) -> None:
        page.evaluate(
            "([idempotencyKey]) => window.KMFA_PROJECT_WORKFLOW_TEST.resolveVariance('USE_SETTLEMENT_SUPPORT', idempotencyKey)",
            [key],
        )
        page.wait_for_function(
            "() => window.KMFA_PROJECT_WORKFLOW_TEST.snapshot().projection.cost.actual_total_cents === 234552000"
        )

    @staticmethod
    def query(**extra: str) -> str:
        value = {
            "user_id": "demo-owner",
            "role_id": "management",
            "company_id": "demo-north",
            "period": "2026-07",
            "project_status": "all",
            "page": "1",
            "page_size": "6",
            "project_id": "PUB-PROJ-001",
        }
        value.update(extra)
        return urlencode(value)

    def test_01_list_detail_workflow_and_return_are_one_flow(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/projects", wait_until="networkidle")
            self.wait_list(page)
            page.locator("#project-group").select_option("risk")
            page.locator("#project-sort").select_option("margin")
            page.wait_for_function(
                "() => window.KMFA_PROJECT_LIST_TEST.snapshot().group_by === 'risk' && window.KMFA_PROJECT_LIST_TEST.snapshot().sort_by === 'margin'"
            )
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_s17_review_list.png"), full_page=True)
            page.locator('a[href^="/projects/PUB-PROJ-001?"]').first.click()
            self.wait_workflow(page)
            self.assertEqual(page.evaluate("window.KMFA_PROJECT_DETAIL_TEST.snapshot().project.project_id"), "PUB-PROJ-001")
            page.locator("#detail-return").click()
            self.wait_list(page)
            state = page.evaluate("window.KMFA_PROJECT_LIST_TEST.state()")
            self.assertEqual((state["group_by"], state["sort_by"]), ("risk", "margin"))
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_02_confirmed_variance_updates_detail_list_and_risk(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/projects/PUB-PROJ-001", wait_until="networkidle")
            self.wait_workflow(page)
            self.resolve_variance(page, "s17-review-browser-variance-02")
            detail = page.evaluate("window.KMFA_PROJECT_DETAIL_TEST.snapshot()")
            self.assertEqual(detail["cost"]["actual_total_cents"], 234_552_000)
            self.assertEqual(detail["project"]["risk_level"], "LOW")
            self.assertEqual(detail["overview"]["risk_zh"], "低风险")
            self.assertNotIn("成本偏差待复核", detail["overview"]["risk_reasons_zh"])
            self.assertIn("低风险", page.locator("#detail-panel-overview").inner_text())
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_s17_review_resolved_detail.png"), full_page=True)
            page.goto(self.base_url + "/projects", wait_until="networkidle")
            self.wait_list(page)
            payload = page.evaluate("window.KMFA_PROJECT_LIST_TEST.snapshot()")
            row = next(item for item in payload["rows"] if item["project_id"] == "PUB-PROJ-001")
            self.assertEqual(row["cost_cents"], detail["cost"]["actual_total_cents"])
            self.assertEqual((row["status"], row["risk_level"]), ("NORMAL", "LOW"))
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_03_current_html_report_uses_current_project_version(self) -> None:
        page, errors = self.new_page()
        report_page, report_errors = self.new_page()
        try:
            page.goto(self.base_url + "/projects/PUB-PROJ-001", wait_until="networkidle")
            self.wait_workflow(page)
            self.resolve_variance(page, "s17-review-browser-variance-03")
            workflow = page.evaluate("window.KMFA_PROJECT_WORKFLOW_TEST.snapshot()")
            href = page.locator('[data-report-format="html"]').get_attribute("href")
            self.assertIn("project_id=PUB-PROJ-001", href)
            self.assertIn("company_id=demo-north", href)
            report_page.goto(self.base_url + href, wait_until="networkidle")
            self.assertIn("2,345,520.00", report_page.locator("body").inner_text())
            self.assertIn(workflow["projection"]["workflow_projection"]["report_version"], report_page.locator("body").inner_text())
            report_page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_s17_review_current_report.png"), full_page=True)
            self.assertEqual(errors + report_errors, [])
        finally:
            report_page.close()
            page.close()

    def test_04_compare_and_export_apis_use_current_projection(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/projects/PUB-PROJ-001", wait_until="networkidle")
            self.wait_workflow(page)
            self.resolve_variance(page, "s17-review-browser-variance-04")
            query = self.query(project_ids="PUB-PROJ-001,PUB-PROJ-002")
            comparison = page.request.get(self.base_url + "/api/projects/compare?" + query).json()
            row = next(item for item in comparison["rows"] if item["project_id"] == "PUB-PROJ-001")
            self.assertEqual(row["cost_cents"], 234_552_000)
            exported = page.request.get(self.base_url + "/api/projects/export?" + query).text()
            self.assertIn("PUB-PROJ-001", exported)
            self.assertIn("234552000", exported)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_05_low_confidence_candidate_is_rejected_without_event(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/projects/PUB-PROJ-001", wait_until="networkidle")
            self.wait_workflow(page)
            with self.assertRaises(Error):
                page.evaluate(
                    "window.KMFA_PROJECT_WORKFLOW_TEST.assign('CAND-S17P3-003','s17-review-browser-low-05')"
                )
            page.locator("#workflow-feedback", has_text="低置信").wait_for()
            self.assertEqual(page.evaluate("window.KMFA_PROJECT_WORKFLOW_TEST.snapshot().event_count"), 0)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_06_reversal_restores_amount_and_risk_together(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/projects/PUB-PROJ-001", wait_until="networkidle")
            self.wait_workflow(page)
            self.resolve_variance(page, "s17-review-browser-variance-06")
            event_id = page.evaluate(
                "window.KMFA_PROJECT_WORKFLOW_TEST.snapshot().events.find(row => row.event_type === 'PROJECT_VARIANCE_RESOLVED').event_id"
            )
            page.evaluate(
                "([eventId]) => window.KMFA_PROJECT_WORKFLOW_TEST.reverse(eventId,'s17-review-browser-reverse-06')",
                [event_id],
            )
            page.wait_for_function(
                "() => window.KMFA_PROJECT_DETAIL_TEST.snapshot().cost.actual_total_cents === 235832000"
            )
            detail = page.evaluate("window.KMFA_PROJECT_DETAIL_TEST.snapshot()")
            self.assertEqual(detail["project"]["risk_level"], "MEDIUM")
            self.assertIn("成本偏差待复核", detail["project"]["risk_reasons_zh"])
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_07_company_and_project_event_boundaries_are_isolated(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/projects/PUB-PROJ-001", wait_until="networkidle")
            self.wait_workflow(page)
            self.resolve_variance(page, "s17-review-browser-variance-07")
            south = page.request.get(
                self.base_url
                + "/api/projects/workflow?"
                + self.query(company_id="demo-south", project_id="PUB-PROJ-001")
            ).json()
            other = page.request.get(
                self.base_url
                + "/api/projects/workflow?"
                + self.query(company_id="demo-north", project_id="PUB-PROJ-002")
            ).json()
            self.assertEqual(south["event_count"], 0)
            self.assertEqual(other["event_count"], 0)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_08_mobile_flow_is_readable_without_horizontal_overflow(self) -> None:
        page, errors = self.new_page(390, 844)
        try:
            page.goto(self.base_url + "/projects/PUB-PROJ-001", wait_until="networkidle")
            self.wait_workflow(page)
            self.assertGreaterEqual(
                page.locator("#confirm-variance").evaluate("node => Math.round(node.getBoundingClientRect().height)"),
                42,
            )
            self.assertTrue(page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1"))
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_s17_review_mobile.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_09_tablet_list_and_detail_do_not_overflow(self) -> None:
        page, errors = self.new_page(820, 1180)
        try:
            page.goto(self.base_url + "/projects", wait_until="networkidle")
            self.wait_list(page)
            self.assertTrue(page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1"))
            page.locator('a[href^="/projects/PUB-PROJ-001?"]').first.click()
            self.wait_workflow(page)
            self.assertTrue(page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1"))
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_s17_review_tablet.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_10_keyboard_focus_reduced_motion_and_report_labels_are_clear(self) -> None:
        page, errors = self.new_page()
        try:
            page.emulate_media(reduced_motion="reduce")
            page.goto(self.base_url + "/projects/PUB-PROJ-001", wait_until="networkidle")
            self.wait_workflow(page)
            page.locator("#confirm-assignment").focus()
            self.assertEqual(page.evaluate("document.activeElement.id"), "confirm-assignment")
            labels = page.locator(".workflow-reports a").all_inner_texts()
            self.assertEqual(labels, ["打开当前 HTML", "下载验收样例 PDF", "下载验收样例 Excel"])
            self.assertTrue(
                page.evaluate(
                    "matchMedia('(prefers-reduced-motion: reduce)').matches && getComputedStyle(document.querySelector('#project-workflow-view')).animationName === 'none'"
                )
            )
            self.assertEqual(errors, [])
        finally:
            page.close()


if __name__ == "__main__":
    unittest.main()
