from __future__ import annotations

import csv
import io
import os
import tempfile
import unittest
from pathlib import Path

from playwright.sync_api import Browser, Page, Playwright, sync_playwright

from KMFA.tools import run_v015_s21_p2_report_generation as runtime


REPO_ROOT = Path(__file__).resolve().parents[2]
SCREENSHOT_ROOT = REPO_ROOT / "KMFA/stage_artifacts/V015_S21_P2_REPORT_GENERATION/exports/screenshots"


class ReportGenerationBrowserTests(unittest.TestCase):
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
        cls.model_path = cls.root / "report-models.jsonl"
        cls.export_path = cls.root / "exports.jsonl"
        cls.bundle_root = cls.root / "bundles"
        cls.server, cls.server_thread, cls.base_url = runtime.start_server(
            event_path=cls.root / "base.jsonl", data_root=cls.root / "data-update",
            confirmation_event_path=cls.root / "confirmation.jsonl", publication_event_path=cls.root / "publication.jsonl",
            report_model_event_path=cls.model_path, export_event_path=cls.export_path, export_bundle_root=cls.bundle_root,
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
        self.model_path.unlink(missing_ok=True)
        self.model_path.with_suffix(".jsonl.lock").unlink(missing_ok=True)
        self.export_path.unlink(missing_ok=True)
        self.export_path.with_suffix(".jsonl.lock").unlink(missing_ok=True)
        if self.bundle_root.is_dir():
            for path in sorted(self.bundle_root.rglob("*"), reverse=True):
                path.unlink() if path.is_file() else path.rmdir()
        self.server.report_model_journal = runtime.base_runtime.kernel.ReportModelJournal(self.model_path)
        self.server.report_export_journal = runtime.kernel.ReportExportJournal(self.export_path, self.bundle_root)
        self.server.report_model_journal.create(
            company_id="demo-north", period_kind="MONTHLY", period_key="2026-07",
            source_bindings=runtime.base_runtime.kernel.default_source_bindings(),
            formula_bindings=runtime.base_runtime.kernel.default_formula_bindings(),
            created_by="浏览器测试负责人", idempotency_key="browser-model-001",
            recorded_at="2026-07-17T00:00:00+00:00",
        )

    def new_page(self, width=1440, height=1000) -> tuple[Page, list[str]]:
        page = self.browser.new_page(viewport={"width": width, "height": height})
        page.set_default_timeout(15_000)
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("console", lambda message: errors.append(message.text) if message.type == "error" and not message.text.startswith("Failed to load resource:") else None)
        return page, errors

    def open_workbench(self, page: Page) -> None:
        page.goto(self.base_url + "/report-generation", wait_until="networkidle")
        page.locator("#report-generation-view").wait_for(state="visible")
        page.wait_for_function("() => window.KMFA_REPORT_GENERATION_TEST?.snapshot()?.reports?.report_version_count === 1")

    def generate(self, page: Page) -> dict:
        page.locator("#rg-create-form button[type=submit]").click()
        page.wait_for_function("() => window.KMFA_REPORT_GENERATION_TEST.snapshot()?.exports?.export_count === 1")
        return page.evaluate("window.KMFA_REPORT_GENERATION_TEST.snapshot().current")

    def test_predecessor_page_has_report_generation_entry(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/report-model", wait_until="networkidle")
            entry = page.get_by_role("link", name="报告生成")
            self.assertTrue(entry.is_visible())
            entry.click()
            page.locator("#report-generation-view").wait_for(state="visible")
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_generate_three_formats_and_zero_difference(self) -> None:
        page, errors = self.new_page()
        try:
            self.open_workbench(page)
            export = self.generate(page)
            self.assertEqual(export["cross_format_consistency"]["difference_integer"], 0)
            self.assertEqual(page.locator(".rg-downloads a").count(), 3)
            self.assertIn("三种格式数字一致", page.locator(".rg-export").inner_text())
            page.screenshot(path=str(SCREENSHOT_ROOT / "report_generation_bundle.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_html_report_has_navigation_print_design_and_sources(self) -> None:
        page, errors = self.new_page()
        try:
            self.open_workbench(page)
            export = self.generate(page)
            page.goto(f"{self.base_url}/api/report-exports/{export['export_id']}/html", wait_until="networkidle")
            self.assertEqual(page.locator('nav[aria-label="章节导航"] a').count(), 6)
            self.assertTrue(page.locator("#sources").is_visible())
            self.assertEqual(page.locator("[data-raw-integer]").count(), 21)
            page.screenshot(path=str(SCREENSHOT_ROOT / "report_html_full.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_html_source_section_is_readable_and_bound_to_versions(self) -> None:
        page, errors = self.new_page()
        try:
            self.open_workbench(page)
            export = self.generate(page)
            page.goto(f"{self.base_url}/api/report-exports/{export['export_id']}/html", wait_until="networkidle")
            page.locator("#sources").scroll_into_view_if_needed()
            text = page.locator("#sources").inner_text()
            self.assertIn("PUB-S20P3-0001", text)
            self.assertIn("来源与专业附表", text)
            page.screenshot(path=str(SCREENSHOT_ROOT / "report_html_sources.png"), full_page=False)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_pdf_download_is_real_pdf_and_csv_is_exact(self) -> None:
        page, errors = self.new_page()
        try:
            self.open_workbench(page)
            export = self.generate(page)
            pdf = page.request.get(f"{self.base_url}/api/report-exports/{export['export_id']}/pdf")
            csv_response = page.request.get(f"{self.base_url}/api/report-exports/{export['export_id']}/appendix.csv")
            self.assertTrue(pdf.ok and pdf.body().startswith(b"%PDF"))
            rows = list(csv.DictReader(io.StringIO(csv_response.body().decode("utf-8-sig"))))
            self.assertEqual(len(rows), 21)
            self.assertTrue(all(int(row["difference_integer"]) == 0 for row in rows))
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_refresh_recovers_identical_export_and_downloads(self) -> None:
        page, errors = self.new_page()
        try:
            self.open_workbench(page)
            before = self.generate(page)["event_hash"]
            page.reload(wait_until="networkidle")
            page.wait_for_function("() => window.KMFA_REPORT_GENERATION_TEST?.snapshot()?.exports?.export_count === 1")
            after = page.evaluate("window.KMFA_REPORT_GENERATION_TEST.snapshot().current.event_hash")
            self.assertEqual(after, before)
            self.assertEqual(page.locator(".rg-downloads a").count(), 3)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_workbench_mobile_has_no_overflow_and_44px_targets(self) -> None:
        page, errors = self.new_page(390, 844)
        try:
            self.open_workbench(page)
            metrics = page.evaluate("""() => ({overflow:document.documentElement.scrollWidth-window.innerWidth,heights:[...document.querySelectorAll('#report-generation-view button,#report-generation-view a,#report-generation-view select')].filter(n=>n.offsetParent!==null).map(n=>n.getBoundingClientRect().height)})""")
            self.assertLessEqual(metrics["overflow"], 1)
            self.assertTrue(metrics["heights"] and min(metrics["heights"]) >= 44)
            page.screenshot(path=str(SCREENSHOT_ROOT / "report_generation_mobile.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_html_report_mobile_has_no_page_overflow(self) -> None:
        page, errors = self.new_page(390, 844)
        try:
            self.open_workbench(page)
            export = self.generate(page)
            page.goto(f"{self.base_url}/api/report-exports/{export['export_id']}/html", wait_until="networkidle")
            overflow = page.evaluate("document.documentElement.scrollWidth-window.innerWidth")
            self.assertLessEqual(overflow, 1)
            page.screenshot(path=str(SCREENSHOT_ROOT / "report_html_mobile.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()


if __name__ == "__main__":
    unittest.main()
