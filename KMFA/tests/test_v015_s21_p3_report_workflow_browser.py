from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from playwright.sync_api import Browser, Page, Playwright, sync_playwright

from KMFA.tools import run_v015_s21_p3_report_workflow as runtime


REPO_ROOT = Path(__file__).resolve().parents[2]
SCREENSHOT_ROOT = REPO_ROOT / "KMFA/stage_artifacts/V015_S21_P3_REPORT_WORKFLOW/exports/screenshots"


class ReportWorkflowBrowserTests(unittest.TestCase):
    playwright: Playwright
    browser: Browser

    @classmethod
    def setUpClass(cls) -> None:
        global SCREENSHOT_ROOT
        cls.screenshot_temp = None
        if os.environ.get("KMFA_PRESERVE_TRACKED_SCREENSHOTS") == "1":
            cls.screenshot_temp = tempfile.TemporaryDirectory()
            SCREENSHOT_ROOT = Path(cls.screenshot_temp.name)
        cls.temporary = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temporary.name)
        cls.model_path = cls.root / "models.jsonl"
        cls.export_path = cls.root / "exports.jsonl"
        cls.workflow_path = cls.root / "workflows.jsonl"
        cls.bundle_root = cls.root / "bundles"
        cls.server, cls.server_thread, cls.base_url = runtime.start_server(
            event_path=cls.root / "base.jsonl", data_root=cls.root / "data-update",
            confirmation_event_path=cls.root / "confirmation.jsonl", publication_event_path=cls.root / "publication.jsonl",
            report_model_event_path=cls.model_path, export_event_path=cls.export_path,
            export_bundle_root=cls.bundle_root, workflow_event_path=cls.workflow_path,
        )
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
        cls.temporary.cleanup()
        if cls.screenshot_temp is not None:
            cls.screenshot_temp.cleanup()

    def setUp(self) -> None:
        for path in (self.model_path, self.export_path, self.workflow_path):
            path.unlink(missing_ok=True)
            path.with_suffix(path.suffix + ".lock").unlink(missing_ok=True)
        if self.bundle_root.is_dir():
            for path in sorted(self.bundle_root.rglob("*"), reverse=True):
                path.unlink() if path.is_file() else path.rmdir()
        self.server.report_model_journal = runtime.base_runtime.base_runtime.kernel.ReportModelJournal(self.model_path)
        self.server.report_export_journal = runtime.base_runtime.kernel.ReportExportJournal(self.export_path, self.bundle_root)
        self.server.report_workflow_journal = runtime.kernel.ReportWorkflowJournal(self.workflow_path)
        self.report = self.server.report_model_journal.create(
            company_id="demo-north", period_kind="MONTHLY", period_key="2026-07",
            source_bindings=runtime.base_runtime.base_runtime.kernel.default_source_bindings(),
            formula_bindings=runtime.base_runtime.base_runtime.kernel.default_formula_bindings(),
            created_by="浏览器测试负责人", idempotency_key="browser-s21p3-model-001",
            recorded_at="2026-07-17T00:00:00+00:00",
        )
        self.export = self.server.report_export_journal.create(
            self.report, idempotency_key="browser-s21p3-export-001", recorded_at="2026-07-17T00:01:00+00:00"
        )

    def new_page(self, width=1440, height=1000) -> tuple[Page, list[str]]:
        page = self.browser.new_page(viewport={"width": width, "height": height})
        page.set_default_timeout(15_000)
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("console", lambda message: errors.append(message.text) if message.type == "error" and not message.text.startswith("Failed to load resource:") else None)
        return page, errors

    def open_workflow(self, page: Page) -> None:
        page.goto(self.base_url + "/report-workflow", wait_until="networkidle")
        page.locator("#report-workflow-view").wait_for(state="visible")
        page.wait_for_function("() => window.KMFA_REPORT_WORKFLOW_TEST?.snapshot()?.reports?.report_version_count === 1")
        self.assertFalse(page.locator("#not-found-view").is_visible())
        self.assertFalse(page.locator("#experience-workspace").is_visible())
        self.assertFalse(page.locator("#access-workspace").is_visible())

    def preview(self, page: Page) -> None:
        page.locator("#rw-preview").click()
        page.wait_for_function("() => window.KMFA_REPORT_WORKFLOW_TEST.snapshot()?.current?.state === 'PREVIEWED'")

    def complete(self, page: Page) -> None:
        self.preview(page)
        for button, state in (
            ("#rw-submit", "IN_REVIEW"), ("#rw-review-pass", "REVIEWED"),
            ("#rw-approve", "APPROVED"), ("#rw-publish", "PUBLISHED_INTERNAL"),
        ):
            page.locator(button).click()
            page.wait_for_function(f"() => window.KMFA_REPORT_WORKFLOW_TEST.snapshot()?.current?.state === '{state}'")

    def test_predecessor_page_links_to_report_workflow(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/report-generation", wait_until="networkidle")
            link = page.get_by_role("link", name="报告工作流")
            self.assertTrue(link.is_visible())
            link.click()
            page.locator("#report-workflow-view").wait_for(state="visible")
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_five_step_workflow_records_roles_and_publishes_internal_only(self) -> None:
        page, errors = self.new_page()
        try:
            self.open_workflow(page)
            self.complete(page)
            snapshot = page.evaluate("window.KMFA_REPORT_WORKFLOW_TEST.snapshot().current")
            self.assertEqual((snapshot["state"], snapshot["event_count"]), ("PUBLISHED_INTERNAL", 5))
            self.assertEqual([row["actor_role"] for row in snapshot["events"]], ["finance", "finance", "reviewer", "reviewer", "management"])
            self.assertFalse(snapshot["external_publication_performed"])
            page.screenshot(path=str(SCREENSHOT_ROOT / "report_workflow_published.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_buttons_enforce_workflow_order_and_quality_gate(self) -> None:
        page, errors = self.new_page()
        try:
            self.open_workflow(page)
            self.assertTrue(page.locator("#rw-publish").is_disabled())
            self.preview(page)
            self.assertFalse(page.locator("#rw-submit").is_disabled())
            self.assertTrue(page.locator("#rw-publish").is_disabled())
            page.screenshot(path=str(SCREENSHOT_ROOT / "report_workflow_preview.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_revision_adds_version_and_explains_source_change(self) -> None:
        page, errors = self.new_page()
        try:
            self.open_workflow(page)
            page.locator("#rw-revise").click()
            page.wait_for_function("() => window.KMFA_REPORT_WORKFLOW_TEST.snapshot()?.reports?.report_version_count === 2")
            comparison = page.evaluate("window.KMFA_REPORT_WORKFLOW_TEST.snapshot().comparison")
            self.assertGreaterEqual(comparison["source_difference_count"], 1)
            self.assertEqual(comparison["unexplained_difference_count"], 0)
            self.assertTrue(comparison["publication_allowed"])
            self.assertGreaterEqual(page.locator(".rw-change").count(), 1)
            page.screenshot(path=str(SCREENSHOT_ROOT / "report_revision_comparison.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_report_center_filters_and_management_download_permission(self) -> None:
        page, errors = self.new_page()
        try:
            self.open_workflow(page)
            self.complete(page)
            page.locator("#rw-center-status").select_option("PUBLISHED_INTERNAL")
            page.locator("#rw-center-refresh").click()
            page.wait_for_function("() => window.KMFA_REPORT_WORKFLOW_TEST.snapshot()?.center?.result_count === 1")
            center = page.evaluate("window.KMFA_REPORT_WORKFLOW_TEST.snapshot().center")
            self.assertEqual(set(center["reports"][0]["download_formats"]), {"HTML", "PDF", "CSV"})
            self.assertEqual(center["public_link_count"], 0)
            page.screenshot(path=str(SCREENSHOT_ROOT / "report_center_management.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_tax_role_can_view_but_has_no_download_or_public_link(self) -> None:
        page, errors = self.new_page()
        try:
            self.open_workflow(page)
            self.complete(page)
            page.locator("#rw-center-role").select_option("tax")
            page.wait_for_function("() => window.KMFA_REPORT_WORKFLOW_TEST.snapshot()?.center?.role_id === 'tax'")
            center = page.evaluate("window.KMFA_REPORT_WORKFLOW_TEST.snapshot().center")
            self.assertEqual(center["reports"][0]["download_formats"], [])
            self.assertFalse(center["reports"][0]["share_link_enabled"])
            self.assertIn("没有下载权限", page.locator("#rw-center").inner_text())
            page.screenshot(path=str(SCREENSHOT_ROOT / "report_center_tax_view.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_protected_download_requires_identity_and_survives_refresh(self) -> None:
        page, errors = self.new_page()
        try:
            self.open_workflow(page)
            self.complete(page)
            unauthenticated = page.request.get(f"{self.base_url}/api/report-exports/{self.export['export_id']}/pdf")
            authenticated = page.request.get(
                f"{self.base_url}/api/report-exports/{self.export['export_id']}/pdf",
                headers={"X-KMFA-User": "demo-owner", "X-KMFA-Role": "management", "X-KMFA-Company": "demo-north"},
            )
            self.assertEqual(unauthenticated.status, 403)
            self.assertTrue(authenticated.ok and authenticated.body().startswith(b"%PDF"))
            page.reload(wait_until="networkidle")
            page.wait_for_function("() => window.KMFA_REPORT_WORKFLOW_TEST?.snapshot()?.current?.state === 'PUBLISHED_INTERNAL'")
            self.assertEqual(page.locator(".rw-event").count(), 5)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_mobile_has_no_overflow_and_visible_targets_are_44px(self) -> None:
        page, errors = self.new_page(390, 844)
        try:
            self.open_workflow(page)
            metrics = page.evaluate("""() => ({overflow:document.documentElement.scrollWidth-window.innerWidth,heights:[...document.querySelectorAll('#report-workflow-view button,#report-workflow-view a,#report-workflow-view select,#report-workflow-view input')].filter(n=>n.offsetParent!==null).map(n=>n.getBoundingClientRect().height)})""")
            self.assertLessEqual(metrics["overflow"], 1)
            self.assertTrue(metrics["heights"] and min(metrics["heights"]) >= 44)
            page.screenshot(path=str(SCREENSHOT_ROOT / "report_workflow_mobile.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()


if __name__ == "__main__":
    unittest.main()
