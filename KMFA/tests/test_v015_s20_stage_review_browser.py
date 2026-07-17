from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from playwright.sync_api import Browser, Page, Playwright, sync_playwright

from KMFA.tools import run_v015_s20_p3_recalculation_publication as runtime


REPO_ROOT = Path(__file__).resolve().parents[2]
SCREENSHOT_ROOT = REPO_ROOT / "KMFA/stage_artifacts/V015_S20_STAGE_REVIEW/exports/screenshots"


class S20StageReviewBrowserTests(unittest.TestCase):
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
        cls.confirmation_path = root / "confirmation.jsonl"
        cls.publication_path = root / "publication.jsonl"
        cls.server, cls.thread, cls.base_url = runtime.start_server(
            event_path=root / "base.jsonl",
            data_root=root / "data-update",
            confirmation_event_path=cls.confirmation_path,
            publication_event_path=cls.publication_path,
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
        cls.thread.join(timeout=3)
        cls.temporary.cleanup()
        if cls.screenshot_temp is not None:
            cls.screenshot_temp.cleanup()

    def setUp(self) -> None:
        for path in (self.confirmation_path, self.publication_path):
            path.unlink(missing_ok=True)
            path.with_suffix(path.suffix + ".lock").unlink(missing_ok=True)
        self.server.confirmation_workbench = runtime.base_runtime.kernel.ConfirmationWorkbench(self.confirmation_path)
        self.server.recalculation_workbench = runtime.kernel.RecalculationPublicationWorkbench(
            self.confirmation_path, self.publication_path
        )

    def page(self, width: int = 1440, height: int = 1000) -> tuple[Page, list[str]]:
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

    @staticmethod
    def open_confirmation(page: Page, base_url: str) -> None:
        page.goto(base_url + "/confirmation-workbench", wait_until="networkidle")
        page.locator("#confirmation-workbench-view").wait_for(state="visible")
        page.wait_for_function("() => window.KMFA_CONFIRMATION_TEST?.snapshot()?.list?.issue_count === 5")

    @staticmethod
    def confirm_first(page: Page) -> None:
        page.locator('.cw-issue[data-issue-id="ISSUE-S20P2-001"]').click()
        page.locator("#cw-detail-card").wait_for(state="visible")
        page.locator("#cw-preview").click()
        page.locator("#cw-preview-card").wait_for(state="visible")
        page.locator("#cw-confirm").click()
        page.wait_for_function("() => window.KMFA_CONFIRMATION_TEST.snapshot()?.history?.event_count === 1")

    @staticmethod
    def open_recalculation(page: Page, base_url: str) -> None:
        page.goto(base_url + "/recalculation-publication", wait_until="networkidle")
        page.locator("#recalculation-publication-view").wait_for(state="visible")
        page.wait_for_function("() => window.KMFA_RECALCULATION_TEST?.snapshot()?.current?.consistency?.view_count === 4")

    @staticmethod
    def start_and_publish(page: Page) -> None:
        page.locator("#rp-start").click()
        page.locator("#rp-comparison-card").wait_for(state="visible")
        page.wait_for_function("() => window.KMFA_RECALCULATION_TEST.snapshot()?.comparison?.report_change_count === 4")
        page.locator("#rp-preview").click()
        page.wait_for_function("() => !!window.KMFA_RECALCULATION_TEST.snapshot()?.preview")
        page.locator("#rp-confirm").click()
        page.wait_for_function("() => window.KMFA_RECALCULATION_TEST.snapshot()?.current?.publication_version_id === 'PUB-S20P3-0002'")

    def test_01_desktop_three_step_navigation(self) -> None:
        page, errors = self.page()
        try:
            page.goto(self.base_url + "/data-update", wait_until="networkidle")
            page.locator("#data-update-view").wait_for(state="visible")
            self.assertEqual(page.locator("#data-update-view .s20-journey a").count(), 3)
            page.locator("#data-update-view .s20-next").click()
            page.wait_for_function("() => location.pathname === '/confirmation-workbench'")
            page.locator("#confirmation-workbench-view").wait_for(state="visible")
            page.locator("#confirmation-workbench-view .s20-next").click()
            page.wait_for_function("() => location.pathname === '/recalculation-publication'")
            page.locator("#recalculation-publication-view").wait_for(state="visible")
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_02_confirmation_reaches_comparison_and_four_view_publication(self) -> None:
        page, errors = self.page()
        try:
            self.open_confirmation(page, self.base_url)
            page.locator('.cw-issue[data-issue-id="ISSUE-S20P2-001"]').click()
            page.locator("#cw-detail-card").wait_for(state="visible")
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_s20_review_confirmation.png"), full_page=True)
            page.locator("#cw-preview").click()
            page.locator("#cw-preview-card").wait_for(state="visible")
            page.locator("#cw-confirm").click()
            page.wait_for_function("() => window.KMFA_CONFIRMATION_TEST.snapshot()?.history?.event_count === 1")
            page.locator("#confirmation-workbench-view .s20-next").click()
            page.locator("#recalculation-publication-view").wait_for(state="visible")
            page.wait_for_function("() => window.KMFA_RECALCULATION_TEST?.snapshot()?.eligible?.eligible_count === 1")
            self.start_and_publish(page)
            views = page.evaluate("window.KMFA_RECALCULATION_TEST.snapshot().views")
            self.assertEqual(len({row["publication_version_id"] for row in views.values()}), 1)
            self.assertEqual(len({row["shared_metric_fingerprint"] for row in views.values()}), 1)
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_s20_review_end_to_end.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_03_wrong_confirmation_lineage_fails_closed(self) -> None:
        confirmation = runtime.base_runtime.kernel.ConfirmationWorkbench(self.confirmation_path)
        preview = confirmation.preview("ISSUE-S20P2-001", "USE_REGISTERED_PROJECT", actor_role="ROLE::DATA_STEWARD")
        event = confirmation.confirm(
            "ISSUE-S20P2-001", "USE_REGISTERED_PROJECT", actor_id="browser-steward",
            actor_role="ROLE::DATA_STEWARD", reason_zh="已核对业务依据",
            preview_id=preview["preview_id"], preview_token=preview["preview_token"],
            idempotency_key="browser-review-confirm-001",
        )["event"]
        workbench = runtime.kernel.RecalculationPublicationWorkbench(self.confirmation_path, self.publication_path)
        workbench.start_recalculation(
            event["event_id"], actor_id="browser-steward", actor_role="ROLE::DATA_STEWARD",
            idempotency_key="browser-review-recalculate-001",
        )
        value = json.loads(self.publication_path.read_text(encoding="utf-8").splitlines()[0])
        value["trigger_control_event_hash"] = "sha256:" + "0" * 64
        value["event_hash"] = runtime.kernel._fingerprint(runtime.kernel._event_body(value))
        self.publication_path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        self.server.confirmation_workbench = confirmation
        self.server.recalculation_workbench = runtime.kernel.RecalculationPublicationWorkbench(
            self.confirmation_path, self.publication_path
        )
        page, errors = self.page()
        try:
            page.goto(self.base_url + "/recalculation-publication", wait_until="networkidle")
            page.locator("#recalculation-publication-view").wait_for(state="visible")
            page.wait_for_function("() => document.querySelector('#rp-feedback')?.dataset?.state === 'error'")
            self.assertIn("不一致", page.locator("#rp-feedback").inner_text())
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_s20_review_lineage_integrity.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_04_tablet_confirmation_has_no_overflow(self) -> None:
        page, errors = self.page(820, 1180)
        try:
            self.open_confirmation(page, self.base_url)
            self.assertTrue(page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1"))
            self.assertTrue(all(value >= 44 for value in page.locator("#confirmation-workbench-view .s20-journey a").evaluate_all("nodes => nodes.map(node => Math.round(node.getBoundingClientRect().height))")))
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_s20_review_tablet.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_05_mobile_recalculation_has_no_overflow(self) -> None:
        page, errors = self.page(390, 844)
        try:
            page.goto(self.base_url + "/recalculation-publication", wait_until="networkidle")
            page.locator("#recalculation-publication-view").wait_for(state="visible")
            page.wait_for_function("() => window.KMFA_RECALCULATION_TEST?.snapshot()?.current?.consistency?.view_count === 4")
            self.assertTrue(page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1"))
            self.assertTrue(all(value >= 44 for value in page.locator("#recalculation-publication-view .s20-journey a").evaluate_all("nodes => nodes.map(node => Math.round(node.getBoundingClientRect().height))")))
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_s20_review_mobile.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()


if __name__ == "__main__":
    unittest.main()
