from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from playwright.sync_api import Browser, Page, Playwright, sync_playwright

from KMFA.tools import run_v015_s20_p1_data_update as runtime


REPO_ROOT = Path(__file__).resolve().parents[2]
SCREENSHOT_ROOT = REPO_ROOT / "KMFA/stage_artifacts/V015_S20_P1_DATA_UPDATE/exports/screenshots"


class DataUpdateBrowserTests(unittest.TestCase):
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
        cls.sample = root / "public-project-cost.csv"
        cls.sample.write_text("project,cost\nA,100\n", encoding="utf-8")
        cls.broken = root / "broken.pdf"
        cls.broken.write_bytes(b"not a pdf")
        cls.server, cls.server_thread, cls.base_url = runtime.start_server(
            event_path=root / "events.jsonl",
            data_root=root / "data-update",
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

    def new_page(self, width: int = 1440, height: int = 1000) -> tuple[Page, list[str]]:
        page = self.browser.new_page(viewport={"width": width, "height": height})
        page.set_default_timeout(12_000)
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("console", lambda message: errors.append(message.text) if message.type == "error" and not message.text.startswith("Failed to load resource:") else None)
        page.goto(self.base_url + "/overview", wait_until="networkidle")
        page.evaluate("localStorage.clear()")
        return page, errors

    def open_update(self, page: Page) -> None:
        page.goto(self.base_url + "/data-update", wait_until="networkidle")
        page.locator("#data-update-view").wait_for(state="visible")
        page.wait_for_function("() => document.querySelector('#du-source')?.options?.length === 3")
        page.locator("#du-upload-panel").wait_for(state="visible")

    def upload_preview(self, page: Page, file: Path | None = None) -> None:
        page.locator("#du-source").select_option("SRC-local-upload-a1b2c3d4")
        page.locator("#du-entity").select_option("demo-north")
        page.locator("#du-scope").select_option("SEGMENT::PROJECT_COST")
        page.locator("#du-period").fill("2026-07")
        page.locator("#du-file").set_input_files(str(file or self.sample))
        page.locator("#du-upload").click()
        page.locator("#du-preview-panel").wait_for(state="visible")
        page.wait_for_function("() => ['AWAITING_CONFIRMATION','PREVIEW_BLOCKED'].includes(window.KMFA_DATA_UPDATE_TEST.snapshot()?.status)")

    def complete(self, page: Page) -> None:
        self.upload_preview(page)
        page.locator("#du-confirm").click()
        page.locator("#du-result-panel").wait_for(state="visible")
        page.wait_for_function("() => window.KMFA_DATA_UPDATE_TEST.snapshot()?.status === 'COMPLETED'")

    def test_01_top_navigation_opens_real_data_update_workspace(self) -> None:
        page, errors = self.new_page()
        try:
            page.locator('#primary-nav a[data-nav-id="data-update"]').click()
            page.locator("#data-update-view").wait_for(state="visible")
            self.assertEqual(page.url.split("?")[0], self.base_url + "/data-update")
            self.assertIn("先上传检查，再确认处理", page.locator("#data-update-view").inner_text())
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_02_upload_reaches_preview_and_marks_automatic_detection(self) -> None:
        page, errors = self.new_page()
        try:
            self.open_update(page)
            self.upload_preview(page)
            snapshot = page.evaluate("window.KMFA_DATA_UPDATE_TEST.snapshot()")
            self.assertEqual(snapshot["status"], "AWAITING_CONFIRMATION")
            self.assertFalse(snapshot["preview"]["processing_allowed"])
            self.assertEqual(page.locator('.du-origin[data-origin="AUTO_DETECTED"]').count(), 1)
            self.assertIn("系统自动识别，需你确认", page.locator("#du-preview-fields").inner_text())
            self.assertIn("原文件未改动", snapshot["progress"][0]["detail_zh"])
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_data_update_preview.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_03_back_cancels_private_copy_and_returns_to_first_step(self) -> None:
        page, errors = self.new_page()
        try:
            self.open_update(page)
            self.upload_preview(page)
            page.locator("#du-back").click()
            page.locator("#du-upload-panel").wait_for(state="visible")
            self.assertIsNone(page.evaluate("localStorage.getItem('kmfa.v015.s20p1.data-update-job.v1')"))
            self.assertIn("已取消", page.locator("#du-feedback").inner_text())
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_04_confirmation_shows_real_import_validation_and_unexecuted_impact(self) -> None:
        page, errors = self.new_page()
        try:
            self.open_update(page)
            self.complete(page)
            snapshot = page.evaluate("window.KMFA_DATA_UPDATE_TEST.snapshot()")
            stages = {row["stage"]: row["status"] for row in snapshot["progress"]}
            self.assertEqual(stages["IMPORT"], "COMPLETED")
            self.assertEqual(stages["VALIDATE"], "COMPLETED")
            self.assertEqual(stages["RECALCULATE"], "NOT_EXECUTED")
            self.assertEqual(stages["REPORT"], "NOT_EXECUTED")
            self.assertIn("本阶段未执行重算", page.locator("#du-impact").inner_text())
            self.assertIn("项目成本专题报告", page.locator("#du-report-impact").inner_text())
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_data_update_result.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_05_refresh_restores_completed_job(self) -> None:
        page, errors = self.new_page()
        try:
            self.open_update(page)
            self.complete(page)
            job_id = page.evaluate("window.KMFA_DATA_UPDATE_TEST.snapshot().job_id")
            page.reload(wait_until="networkidle")
            page.locator("#du-result-panel").wait_for(state="visible")
            page.wait_for_function("() => window.KMFA_DATA_UPDATE_TEST.snapshot()?.status === 'COMPLETED'")
            self.assertEqual(page.evaluate("window.KMFA_DATA_UPDATE_TEST.snapshot().job_id"), job_id)
            self.assertIn("资料已完成隔离导入", page.locator("#du-feedback").inner_text())
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_06_broken_file_is_explained_and_confirmation_blocked(self) -> None:
        page, errors = self.new_page()
        try:
            self.open_update(page)
            self.upload_preview(page, self.broken)
            self.assertEqual(page.evaluate("window.KMFA_DATA_UPDATE_TEST.snapshot().status"), "PREVIEW_BLOCKED")
            self.assertTrue(page.locator("#du-confirm").is_disabled())
            self.assertIn("PDF", page.locator("#du-issues").inner_text())
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_data_update_blocked.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_07_mobile_flow_has_touch_targets_and_no_page_overflow(self) -> None:
        page, errors = self.new_page(390, 844)
        try:
            self.open_update(page)
            self.upload_preview(page)
            self.assertTrue(page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1"))
            for selector in ("#du-confirm", "#du-back", "#du-cancel"):
                self.assertGreaterEqual(page.locator(selector).evaluate("node => Math.round(node.getBoundingClientRect().height)"), 44)
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_data_update_mobile.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()


if __name__ == "__main__":
    unittest.main()
