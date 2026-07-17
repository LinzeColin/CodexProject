from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from playwright.sync_api import Browser, Page, Playwright, sync_playwright

from KMFA.tools import run_v015_s21_p1_report_model as runtime


REPO_ROOT = Path(__file__).resolve().parents[2]
SCREENSHOT_ROOT = REPO_ROOT / "KMFA/stage_artifacts/V015_S21_P1_REPORT_MODEL/exports/screenshots"


class ReportModelBrowserTests(unittest.TestCase):
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
        root = Path(cls.temporary.name)
        cls.report_path = root / "report_models.jsonl"
        cls.server, cls.server_thread, cls.base_url = runtime.start_server(
            event_path=root / "base.jsonl", data_root=root / "data-update",
            confirmation_event_path=root / "confirmation.jsonl",
            publication_event_path=root / "publication.jsonl",
            report_model_event_path=cls.report_path,
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
        self.report_path.unlink(missing_ok=True)
        self.report_path.with_suffix(".jsonl.lock").unlink(missing_ok=True)
        self.server.report_model_journal = runtime.kernel.ReportModelJournal(self.report_path)

    def new_page(self, width=1440, height=1000) -> tuple[Page, list[str]]:
        page = self.browser.new_page(viewport={"width": width, "height": height})
        page.set_default_timeout(12_000)
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("console", lambda message: errors.append(message.text) if message.type == "error" and not message.text.startswith("Failed to load resource:") else None)
        return page, errors

    def open_workbench(self, page: Page) -> None:
        page.goto(self.base_url + "/report-model", wait_until="networkidle")
        page.locator("#report-model-view").wait_for(state="visible")
        page.wait_for_function("() => window.KMFA_REPORT_MODEL_TEST?.snapshot()?.list?.report_version_count === 0")

    def create(self, page: Page, *, readiness="COMPLETE") -> None:
        page.locator("#rm-readiness").select_option(readiness)
        page.locator("#rm-create-form button[type=submit]").click()
        page.wait_for_function("() => window.KMFA_REPORT_MODEL_TEST.snapshot()?.list?.report_version_count === 1")

    def test_predecessor_page_has_report_model_entry(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/recalculation-publication", wait_until="networkidle")
            entry = page.get_by_role("link", name="报告模型")
            self.assertTrue(entry.is_visible())
            entry.click()
            page.locator("#report-model-view").wait_for(state="visible")
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_create_complete_report_model_binds_inputs_and_formulas(self) -> None:
        page, errors = self.new_page()
        try:
            self.open_workbench(page)
            self.create(page)
            snapshot = page.evaluate("window.KMFA_REPORT_MODEL_TEST.snapshot().current")
            self.assertEqual((len(snapshot["source_bindings"]), len(snapshot["formula_bindings"])), (6, 2))
            self.assertEqual(page.locator("#rm-source-count").inner_text(), "6 / 6")
            self.assertIn("资料齐备", page.locator("#rm-trust-status").inner_text())
            page.screenshot(path=str(SCREENSHOT_ROOT / "report_model_complete.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_period_selector_covers_week_month_quarter_half_year_and_year(self) -> None:
        page, errors = self.new_page()
        try:
            self.open_workbench(page)
            expected = {
                "WEEKLY": "2026-W29", "MONTHLY": "2026-07", "QUARTERLY": "2026-Q3",
                "HALF_YEAR": "2026-H1", "YEARLY": "2026",
            }
            for kind, key in expected.items():
                page.locator("#rm-period-kind").select_option(kind)
                self.assertEqual(page.locator("#rm-period-key").input_value(), key)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_revision_adds_version_and_preserves_initial_history(self) -> None:
        page, errors = self.new_page()
        try:
            self.open_workbench(page)
            self.create(page)
            first = page.evaluate("window.KMFA_REPORT_MODEL_TEST.snapshot().current")
            page.locator("#rm-revision-form button[type=submit]").click()
            page.wait_for_function("() => window.KMFA_REPORT_MODEL_TEST.snapshot()?.list?.report_version_count === 2")
            current = page.evaluate("window.KMFA_REPORT_MODEL_TEST.snapshot().current")
            self.assertEqual((first["version_number"], current["version_number"]), (1, 2))
            self.assertEqual(current["supersedes_version_id"], first["report_version_id"])
            self.assertEqual(page.locator("#rm-history button").count(), 2)
            page.screenshot(path=str(SCREENSHOT_ROOT / "report_model_revision_history.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_management_and_professional_layers_are_human_readable(self) -> None:
        page, errors = self.new_page()
        try:
            self.open_workbench(page)
            self.create(page)
            self.assertEqual(page.locator("#rm-sections .rm-section").count(), 5)
            management_text = page.locator("#rm-sections").inner_text().casefold()
            self.assertFalse(any(term in management_text for term in runtime.kernel.VISIBLE_TECHNICAL_TERMS))
            page.get_by_role("button", name="专业附表").click()
            page.wait_for_function("() => window.KMFA_REPORT_MODEL_TEST.snapshot()?.audience?.audience === 'PROFESSIONAL'")
            self.assertEqual(page.locator("#rm-sections .rm-section").count(), 1)
            self.assertIn("专业附表", page.locator("#rm-sections").inner_text())
            page.screenshot(path=str(SCREENSHOT_ROOT / "report_model_audience_layers.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_missing_critical_data_never_claims_complete_report(self) -> None:
        page, errors = self.new_page()
        try:
            self.open_workbench(page)
            self.create(page, readiness="MISSING")
            current = page.evaluate("window.KMFA_REPORT_MODEL_TEST.snapshot().current")
            self.assertFalse(current["trust_and_limitations"]["complete_report_claim_allowed"])
            self.assertIn("不能称为完整报告", page.locator("#rm-trust-copy").inner_text())
            self.assertEqual(page.locator("#rm-trust").get_attribute("data-complete"), "false")
            page.screenshot(path=str(SCREENSHOT_ROOT / "report_model_incomplete.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_refresh_recovers_identical_report_version(self) -> None:
        page, errors = self.new_page()
        try:
            self.open_workbench(page)
            self.create(page)
            before = page.evaluate("window.KMFA_REPORT_MODEL_TEST.snapshot().current.event_hash")
            page.reload(wait_until="networkidle")
            page.wait_for_function("() => window.KMFA_REPORT_MODEL_TEST?.snapshot()?.list?.report_version_count === 1")
            after = page.evaluate("window.KMFA_REPORT_MODEL_TEST.snapshot().current.event_hash")
            self.assertEqual(after, before)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_mobile_has_no_overflow_and_44px_targets(self) -> None:
        page, errors = self.new_page(390, 844)
        try:
            self.open_workbench(page)
            metrics = page.evaluate("""() => ({overflow:document.documentElement.scrollWidth-window.innerWidth,heights:[...document.querySelectorAll('#report-model-view button,#report-model-view a,#report-model-view select,#report-model-view input')].filter(n=>n.offsetParent!==null).map(n=>n.getBoundingClientRect().height)})""")
            self.assertLessEqual(metrics["overflow"], 1)
            self.assertTrue(metrics["heights"] and min(metrics["heights"]) >= 44)
            page.screenshot(path=str(SCREENSHOT_ROOT / "report_model_mobile.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()


if __name__ == "__main__":
    unittest.main()
