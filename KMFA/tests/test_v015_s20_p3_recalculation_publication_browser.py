from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from playwright.sync_api import Browser, Page, Playwright, sync_playwright

from KMFA.tools import run_v015_s20_p3_recalculation_publication as runtime


REPO_ROOT = Path(__file__).resolve().parents[2]
SCREENSHOT_ROOT = REPO_ROOT / "KMFA/stage_artifacts/V015_S20_P3_RECALCULATION_PUBLICATION/exports/screenshots"


class RecalculationPublicationBrowserTests(unittest.TestCase):
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
        cls.server, cls.server_thread, cls.base_url = runtime.start_server(
            event_path=root / "base.jsonl", data_root=root / "data-update",
            confirmation_event_path=cls.confirmation_path, publication_event_path=cls.publication_path,
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
        self.confirmation_path.unlink(missing_ok=True)
        self.confirmation_path.with_suffix(".jsonl.lock").unlink(missing_ok=True)
        self.publication_path.unlink(missing_ok=True)
        self.publication_path.with_suffix(".jsonl.lock").unlink(missing_ok=True)
        confirmation = runtime.base_runtime.kernel.ConfirmationWorkbench(self.confirmation_path)
        preview = confirmation.preview("ISSUE-S20P2-001", "USE_REGISTERED_PROJECT", actor_role="ROLE::DATA_STEWARD")
        confirmation.confirm(
            "ISSUE-S20P2-001", "USE_REGISTERED_PROJECT", actor_id="browser-steward", actor_role="ROLE::DATA_STEWARD",
            reason_zh="已核对业务依据并允许受影响链重算", preview_id=preview["preview_id"],
            preview_token=preview["preview_token"], idempotency_key="browser-confirm-project-001",
        )
        self.server.confirmation_workbench = confirmation
        self.server.recalculation_workbench = runtime.kernel.RecalculationPublicationWorkbench(
            self.confirmation_path, self.publication_path,
        )

    def new_page(self, width=1440, height=1000) -> tuple[Page, list[str]]:
        page = self.browser.new_page(viewport={"width": width, "height": height})
        page.set_default_timeout(12_000)
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("console", lambda message: errors.append(message.text) if message.type == "error" and not message.text.startswith("Failed to load resource:") else None)
        return page, errors

    def open_workbench(self, page: Page) -> None:
        page.goto(self.base_url + "/recalculation-publication", wait_until="networkidle")
        page.locator("#recalculation-publication-view").wait_for(state="visible")
        page.wait_for_function("() => window.KMFA_RECALCULATION_TEST?.snapshot()?.current?.consistency?.view_count === 4")

    def start_recalculation(self, page: Page) -> None:
        page.locator("#rp-start").click()
        page.locator("#rp-comparison-card").wait_for(state="visible")
        page.wait_for_function("() => window.KMFA_RECALCULATION_TEST.snapshot()?.comparison?.report_change_count === 4")

    def test_confirmation_workbench_has_direct_entry(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/confirmation-workbench", wait_until="networkidle")
            entry = page.get_by_role("link", name="重新计算与发布联动")
            self.assertTrue(entry.is_visible())
            entry.click()
            page.locator("#recalculation-publication-view").wait_for(state="visible")
            page.wait_for_function("() => window.KMFA_RECALCULATION_TEST?.snapshot()?.eligible?.eligible_count === 1")
            page.screenshot(path=str(SCREENSHOT_ROOT / "recalculation_ready.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_start_recalculates_registered_affected_chain_only(self) -> None:
        page, errors = self.new_page()
        try:
            self.open_workbench(page)
            self.start_recalculation(page)
            job = page.evaluate("window.KMFA_RECALCULATION_TEST.snapshot().activeJob")
            self.assertEqual(job["affected_node_count"], 8)
            self.assertIn("FACT::UNRELATED_CASH_CENTS", job["unaffected_refs"])
            self.assertIn("未受影响", page.locator("#rp-impact").inner_text())
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_comparison_explains_numbers_and_all_reports(self) -> None:
        page, errors = self.new_page()
        try:
            self.open_workbench(page)
            self.start_recalculation(page)
            comparison = page.evaluate("window.KMFA_RECALCULATION_TEST.snapshot().comparison")
            self.assertGreaterEqual(comparison["numeric_change_count"], 3)
            self.assertEqual(comparison["report_change_count"], 4)
            self.assertTrue(all(row["explanation_zh"] for row in comparison["numeric_changes"] + comparison["report_changes"]))
            page.screenshot(path=str(SCREENSHOT_ROOT / "recalculation_comparison.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_user_can_retain_old_version(self) -> None:
        page, errors = self.new_page()
        try:
            self.open_workbench(page)
            before = page.locator("#rp-current-version").inner_text()
            self.start_recalculation(page)
            page.locator("#rp-decision").select_option("KEEP_CURRENT")
            page.locator("#rp-preview").click()
            page.locator("#rp-confirm").wait_for(state="visible")
            page.screenshot(path=str(SCREENSHOT_ROOT / "retain_old_version.png"), full_page=True)
            page.locator("#rp-confirm").click()
            page.wait_for_function("() => window.KMFA_RECALCULATION_TEST.snapshot()?.history?.event_count === 2")
            self.assertEqual(page.locator("#rp-current-version").inner_text(), before)
            self.assertIn("保留旧版本", page.locator("#rp-feedback").inner_text())
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_publish_requires_preview_and_advances_version(self) -> None:
        page, errors = self.new_page()
        try:
            self.open_workbench(page)
            self.start_recalculation(page)
            self.assertTrue(page.locator("#rp-confirm").is_disabled())
            page.locator("#rp-preview").click()
            page.wait_for_function("() => !!window.KMFA_RECALCULATION_TEST.snapshot()?.preview")
            self.assertFalse(page.locator("#rp-confirm").is_disabled())
            page.screenshot(path=str(SCREENSHOT_ROOT / "publication_preview.png"), full_page=True)
            page.locator("#rp-confirm").click()
            page.wait_for_function("() => window.KMFA_RECALCULATION_TEST.snapshot()?.current?.publication_version_id === 'PUB-S20P3-0002'")
            self.assertIn("同步发布", page.locator("#rp-feedback").inner_text())
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_four_pages_share_version_numbers_and_fingerprint(self) -> None:
        page, errors = self.new_page()
        try:
            self.open_workbench(page)
            self.start_recalculation(page)
            page.locator("#rp-preview").click()
            page.wait_for_function("() => !!window.KMFA_RECALCULATION_TEST.snapshot()?.preview")
            page.locator("#rp-confirm").click()
            page.wait_for_function("() => window.KMFA_RECALCULATION_TEST.snapshot()?.current?.publication_version_id === 'PUB-S20P3-0002'")
            snapshot = page.evaluate("window.KMFA_RECALCULATION_TEST.snapshot().views")
            self.assertEqual(len({row["publication_version_id"] for row in snapshot.values()}), 1)
            self.assertEqual(len({row["shared_metric_fingerprint"] for row in snapshot.values()}), 1)
            self.assertEqual(len({row["project_margin_cents"] for row in snapshot.values()}), 1)
            page.screenshot(path=str(SCREENSHOT_ROOT / "synchronized_views.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_refresh_recovers_same_synchronized_publication(self) -> None:
        page, errors = self.new_page()
        try:
            self.open_workbench(page)
            self.start_recalculation(page)
            page.locator("#rp-preview").click()
            page.wait_for_function("() => !!window.KMFA_RECALCULATION_TEST.snapshot()?.preview")
            page.locator("#rp-confirm").click()
            page.wait_for_function("() => window.KMFA_RECALCULATION_TEST.snapshot()?.current?.publication_version_id === 'PUB-S20P3-0002'")
            before = page.evaluate("window.KMFA_RECALCULATION_TEST.snapshot().current.snapshot_hash")
            page.reload(wait_until="networkidle")
            page.wait_for_function("() => window.KMFA_RECALCULATION_TEST?.snapshot()?.history?.event_count === 2")
            after = page.evaluate("window.KMFA_RECALCULATION_TEST.snapshot().current.snapshot_hash")
            self.assertEqual(after, before)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_mobile_has_no_overflow_and_44px_targets(self) -> None:
        page, errors = self.new_page(390, 844)
        try:
            self.open_workbench(page)
            metrics = page.evaluate("""() => ({overflow:document.documentElement.scrollWidth-window.innerWidth,heights:[...document.querySelectorAll('#recalculation-publication-view button,#recalculation-publication-view a,#recalculation-publication-view select,#recalculation-publication-view input')].filter(n=>n.offsetParent!==null).map(n=>n.getBoundingClientRect().height)})""")
            self.assertLessEqual(metrics["overflow"], 1)
            self.assertTrue(metrics["heights"] and min(metrics["heights"]) >= 44)
            page.screenshot(path=str(SCREENSHOT_ROOT / "recalculation_mobile.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()


if __name__ == "__main__":
    unittest.main()
