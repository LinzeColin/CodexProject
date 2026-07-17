from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from playwright.sync_api import Browser, Page, Playwright, sync_playwright

from KMFA.tools import run_v015_s21_p3_report_workflow as runtime
from KMFA.tools import v015_s21_p1_report_model as p1
from KMFA.tools import v015_s21_p2_report_generation as p2
from KMFA.tools import v015_s21_p3_report_workflow as p3


REPO_ROOT = Path(__file__).resolve().parents[2]
SCREENSHOT_ROOT = REPO_ROOT / "KMFA/stage_artifacts/V015_S21_STAGE_REVIEW/exports/screenshots"


class Stage21ReviewBrowserTests(unittest.TestCase):
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
            confirmation_event_path=cls.root / "confirmation.jsonl",
            publication_event_path=cls.root / "publication.jsonl",
            report_model_event_path=cls.model_path, export_event_path=cls.export_path,
            export_bundle_root=cls.bundle_root, workflow_event_path=cls.workflow_path,
        )
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
        self.models = p1.ReportModelJournal(self.model_path)
        self.exports = p2.ReportExportJournal(self.export_path, self.bundle_root)
        self.workflows = p3.ReportWorkflowJournal(self.workflow_path)
        self.server.report_model_journal = self.models
        self.server.report_export_journal = self.exports
        self.server.report_workflow_journal = self.workflows
        self.north = self.models.create(
            company_id="demo-north", period_kind="MONTHLY", period_key="2026-07",
            source_bindings=p1.default_source_bindings(), formula_bindings=p1.default_formula_bindings(),
            created_by="浏览器测试负责人", idempotency_key="browser-review-north-v1",
            recorded_at="2026-07-17T00:00:00+00:00",
        )
        self.north_export = self.exports.create(
            self.north, idempotency_key="browser-review-export-north-v1",
            recorded_at="2026-07-17T00:01:00+00:00",
        )
        self.west = self.models.create(
            company_id="demo-west", period_kind="QUARTERLY", period_key="2026-Q3",
            source_bindings=p1.default_source_bindings(), formula_bindings=p1.default_formula_bindings(),
            created_by="浏览器测试负责人", idempotency_key="browser-review-west-v1",
            recorded_at="2026-07-17T00:02:00+00:00",
        )
        self.west_export = self.exports.create(
            self.west, idempotency_key="browser-review-export-west-v1",
            recorded_at="2026-07-17T00:03:00+00:00",
        )

    def new_page(self, width: int = 1440, height: int = 1000) -> tuple[Page, list[str]]:
        page = self.browser.new_page(viewport={"width": width, "height": height})
        page.set_default_timeout(15_000)
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("console", lambda message: errors.append(message.text) if message.type == "error" and not message.text.startswith("Failed to load resource:") else None)
        return page, errors

    def open_workflow(self, page: Page) -> None:
        page.goto(self.base_url + "/report-workflow", wait_until="networkidle")
        page.locator("#report-workflow-view").wait_for(state="visible")
        page.wait_for_function("() => window.KMFA_REPORT_WORKFLOW_TEST?.snapshot()?.reports?.report_version_count === 2")

    def choose(self, page: Page, report_version_id: str) -> None:
        page.locator("#rw-report-version").select_option(report_version_id)
        page.wait_for_function(
            "value => (window.KMFA_REPORT_WORKFLOW_TEST.snapshot().current?.report_version_id || null) === value",
            report_version_id if any(row["report_version_id"] == report_version_id for row in self.workflows.list()["cases"]) else None,
        )

    def complete_selected(self, page: Page, report_version_id: str | None = None) -> None:
        if report_version_id:
            page.locator("#rw-report-version").select_option(report_version_id)
        page.locator("#rw-preview").click()
        page.wait_for_function("() => window.KMFA_REPORT_WORKFLOW_TEST.snapshot()?.current?.state === 'PREVIEWED'")
        for button, state in (("#rw-submit", "IN_REVIEW"), ("#rw-review-pass", "REVIEWED"), ("#rw-approve", "APPROVED"), ("#rw-publish", "PUBLISHED_INTERNAL")):
            page.locator(button).click()
            page.wait_for_function(f"() => window.KMFA_REPORT_WORKFLOW_TEST.snapshot()?.current?.state === '{state}'")

    def seed_revision(self) -> tuple[dict, dict]:
        revised = self.models.revise(
            self.north["report_version_id"],
            source_bindings=p3.revision_bindings(self.north, {"key_matters": "S20P2-CONFIRMATIONS-2026-07-V2"}),
            revision_reason_zh="补充本期重点事项复核结果和负责人意见",
            created_by="浏览器测试负责人", idempotency_key="browser-review-north-v2",
            recorded_at="2026-07-17T00:10:00+00:00",
        )
        export = self.exports.create(
            revised, idempotency_key="browser-review-export-north-v2",
            recorded_at="2026-07-17T00:11:00+00:00",
        )
        return revised, export

    def test_three_step_navigation_has_one_visible_current_step(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/report-model", wait_until="networkidle")
            self.assertEqual(page.locator("#report-model-view .s21-journey a").count(), 3)
            self.assertEqual(page.locator("#report-model-view .s21-journey a[aria-current='step']").inner_text().splitlines()[1], "报告模型")
            page.locator("#report-model-view .s21-journey a[href='/report-generation']").click()
            page.locator("#report-generation-view").wait_for(state="visible")
            page.locator("#report-generation-view .s21-journey a[href='/report-workflow']").click()
            page.locator("#report-workflow-view").wait_for(state="visible")
            self.assertEqual(page.locator("#report-workflow-view .s21-journey a[aria-current='step']").count(), 1)
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_s21_review_three_step.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_end_to_end_internal_publication_records_five_events(self) -> None:
        page, errors = self.new_page()
        try:
            self.open_workflow(page)
            self.complete_selected(page, self.north["report_version_id"])
            current = page.evaluate("window.KMFA_REPORT_WORKFLOW_TEST.snapshot().current")
            self.assertEqual((current["state"], current["event_count"]), ("PUBLISHED_INTERNAL", 5))
            self.assertTrue(all(row.get("actor_label_zh") and row.get("occurred_at") and row.get("comment_zh") for row in current["events"]))
            self.assertFalse(current["external_publication_performed"])
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_s21_review_end_to_end.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_report_center_exposes_and_applies_five_business_filters(self) -> None:
        page, errors = self.new_page()
        try:
            self.open_workflow(page)
            self.complete_selected(page, self.north["report_version_id"])
            for selector in ("#rw-center-company", "#rw-center-period", "#rw-center-type", "#rw-center-status", "#rw-center-version"):
                self.assertTrue(page.locator(selector).is_visible())
            page.locator("#rw-center-company").select_option("demo-west")
            page.locator("#rw-center-period").select_option("2026-Q3")
            page.locator("#rw-center-type").select_option("QUARTERLY")
            page.locator("#rw-center-status").select_option("GENERATED")
            page.locator("#rw-center-version").select_option(self.west["report_version_id"])
            page.wait_for_function("() => window.KMFA_REPORT_WORKFLOW_TEST.snapshot()?.center?.filter_count === 4 && window.KMFA_REPORT_WORKFLOW_TEST.snapshot()?.center?.result_count === 1")
            center = page.evaluate("window.KMFA_REPORT_WORKFLOW_TEST.snapshot().center")
            self.assertEqual(center["reports"][0]["company_id"], "demo-west")
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_s21_review_filters.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_multi_company_preview_uses_selected_report_company(self) -> None:
        page, errors = self.new_page()
        try:
            self.open_workflow(page)
            page.locator("#rw-report-version").select_option(self.west["report_version_id"])
            page.locator("#rw-preview").click()
            page.wait_for_function("() => window.KMFA_REPORT_WORKFLOW_TEST.snapshot()?.current?.company_id === 'demo-west'")
            current = page.evaluate("window.KMFA_REPORT_WORKFLOW_TEST.snapshot().current")
            self.assertEqual(current["report_version_id"], self.west["report_version_id"])
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_selected_version_binds_matching_case_not_latest_case(self) -> None:
        revised, revised_export = self.seed_revision()
        for report, export, suffix in ((self.north, self.north_export, "v1"), (revised, revised_export, "v2")):
            self.workflows.preview(
                report, export, user_id="demo-owner", role_id="finance", company_id="demo-north",
                comment_zh="按所选版本建立独立预览流程", idempotency_key=f"browser-review-case-{suffix}",
                occurred_at="2026-07-17T00:12:00+00:00",
            )
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/report-workflow", wait_until="networkidle")
            page.wait_for_function("() => window.KMFA_REPORT_WORKFLOW_TEST?.snapshot()?.reports?.report_version_count === 3")
            for report_id in (self.north["report_version_id"], revised["report_version_id"]):
                page.locator("#rw-report-version").select_option(report_id)
                page.wait_for_function(
                    "value => window.KMFA_REPORT_WORKFLOW_TEST.snapshot()?.current?.report_version_id === value",
                    arg=report_id,
                )
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_s21_review_multi_version.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_revision_comparison_explains_change_and_preserves_old_version(self) -> None:
        page, errors = self.new_page()
        try:
            self.open_workflow(page)
            page.locator("#rw-revision-base").select_option(self.north["report_version_id"])
            page.locator("#rw-revise").click()
            page.wait_for_function("() => window.KMFA_REPORT_WORKFLOW_TEST.snapshot()?.reports?.report_version_count === 3")
            comparison = page.evaluate("window.KMFA_REPORT_WORKFLOW_TEST.snapshot().comparison")
            self.assertTrue(comparison["direct_revision"] and comparison["publication_allowed"])
            self.assertEqual(comparison["unexplained_difference_count"], 0)
            self.assertTrue(any(row["report_version_id"] == self.north["report_version_id"] for row in self.models.list()["reports"]))
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_tax_can_view_but_cannot_download_or_create_public_link(self) -> None:
        page, errors = self.new_page()
        try:
            self.open_workflow(page)
            self.complete_selected(page, self.north["report_version_id"])
            page.locator("#rw-center-company").select_option("demo-north")
            page.locator("#rw-center-role").select_option("tax")
            page.wait_for_function("() => window.KMFA_REPORT_WORKFLOW_TEST.snapshot()?.center?.role_id === 'tax' && window.KMFA_REPORT_WORKFLOW_TEST.snapshot()?.center?.company_id === 'demo-north'")
            center = page.evaluate("window.KMFA_REPORT_WORKFLOW_TEST.snapshot().center")
            report = next(row for row in center["reports"] if row["report_version_id"] == self.north["report_version_id"])
            self.assertEqual(report["download_formats"], [])
            self.assertFalse(report["share_link_enabled"])
            self.assertEqual(center["public_link_count"], 0)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_mobile_has_no_overflow_and_touch_targets_are_44px(self) -> None:
        page, errors = self.new_page(390, 844)
        try:
            self.open_workflow(page)
            metrics = page.evaluate("""() => ({overflow:document.documentElement.scrollWidth-window.innerWidth,heights:[...document.querySelectorAll('#report-workflow-view button,#report-workflow-view a,#report-workflow-view select,#report-workflow-view input')].filter(n=>n.offsetParent!==null).map(n=>n.getBoundingClientRect().height)})""")
            self.assertLessEqual(metrics["overflow"], 1)
            self.assertTrue(metrics["heights"] and min(metrics["heights"]) >= 44)
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_s21_review_mobile.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()


if __name__ == "__main__":
    unittest.main()
