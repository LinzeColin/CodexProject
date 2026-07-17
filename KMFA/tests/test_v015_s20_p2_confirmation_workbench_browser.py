from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from playwright.sync_api import Browser, Page, Playwright, sync_playwright

from KMFA.tools import run_v015_s20_p2_confirmation_workbench as runtime
from KMFA.tools import v015_s20_p2_confirmation_workbench as kernel


REPO_ROOT = Path(__file__).resolve().parents[2]
SCREENSHOT_ROOT = REPO_ROOT / "KMFA/stage_artifacts/V015_S20_P2_CONFIRMATION_WORKBENCH/exports/screenshots"


class ConfirmationWorkbenchBrowserTests(unittest.TestCase):
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
        cls.server, cls.server_thread, cls.base_url = runtime.start_server(
            event_path=root / "base.jsonl", data_root=root / "data-update", confirmation_event_path=cls.confirmation_path,
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
        self.server.confirmation_workbench = kernel.ConfirmationWorkbench(self.confirmation_path)

    def new_page(self, width: int = 1440, height: int = 1000) -> tuple[Page, list[str]]:
        page = self.browser.new_page(viewport={"width": width, "height": height})
        page.set_default_timeout(12_000)
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("console", lambda message: errors.append(message.text) if message.type == "error" and not message.text.startswith("Failed to load resource:") else None)
        page.goto(self.base_url + "/overview", wait_until="networkidle")
        page.evaluate("localStorage.clear()")
        return page, errors

    def open_workbench(self, page: Page) -> None:
        page.goto(self.base_url + "/confirmation-workbench", wait_until="networkidle")
        page.locator("#confirmation-workbench-view").wait_for(state="visible")
        page.wait_for_function("() => window.KMFA_CONFIRMATION_TEST?.snapshot()?.list?.issue_count === 5")

    def open_first_detail(self, page: Page) -> None:
        page.locator('.cw-issue[data-issue-id="ISSUE-S20P2-001"]').click()
        page.locator("#cw-detail-card").wait_for(state="visible")
        page.wait_for_function("() => window.KMFA_CONFIRMATION_TEST.snapshot()?.detail?.issue_id === 'ISSUE-S20P2-001'")

    def confirm_first(self, page: Page) -> None:
        self.open_first_detail(page)
        page.locator("#cw-preview").click()
        page.locator("#cw-preview-card").wait_for(state="visible")
        page.locator("#cw-confirm").click()
        page.wait_for_function("() => window.KMFA_CONFIRMATION_TEST.snapshot()?.history?.event_count === 1")

    def test_data_update_has_direct_workbench_entry(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/data-update", wait_until="networkidle")
            entry = page.get_by_role("link", name="打开人工确认工作台")
            self.assertTrue(entry.is_visible())
            entry.click()
            page.locator("#confirmation-workbench-view").wait_for(state="visible")
            page.wait_for_function("() => window.KMFA_CONFIRMATION_TEST?.snapshot()?.list?.issue_count === 5")
            page.screenshot(path=str(SCREENSHOT_ROOT / "confirmation_issue_list.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_default_list_is_sorted_and_excludes_governance(self) -> None:
        page, errors = self.new_page()
        try:
            self.open_workbench(page)
            snapshot = page.evaluate("window.KMFA_CONFIRMATION_TEST.snapshot().list")
            self.assertEqual(snapshot["issue_count"], 5)
            self.assertEqual(snapshot["governance_log_count_in_main_list"], 0)
            self.assertEqual([row["issue_id"] for row in snapshot["issues"][:3]], ["ISSUE-S20P2-001", "ISSUE-S20P2-002", "ISSUE-S20P2-003"])
            self.assertNotIn("治理检查记录", page.locator("#cw-list").inner_text())
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_detail_is_business_first_side_by_side_and_technical_collapsed(self) -> None:
        page, errors = self.new_page()
        try:
            self.open_workbench(page)
            self.open_first_detail(page)
            self.assertIn("当前资料", page.locator("#cw-detail-card").inner_text())
            self.assertIn("参考资料", page.locator("#cw-detail-card").inner_text())
            self.assertIn("可能影响", page.locator("#cw-detail-card").inner_text())
            self.assertFalse(page.locator("#cw-technical").evaluate("node => node.open"))
            self.assertEqual(page.locator('#cw-detail-card input[type="text"]').count(), 0)
            page.screenshot(path=str(SCREENSHOT_ROOT / "confirmation_issue_detail.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_high_impact_requires_preview_and_confirmation_records_history(self) -> None:
        page, errors = self.new_page()
        try:
            self.open_workbench(page)
            result = page.evaluate("""async () => { const r=await fetch('/api/confirmation/issues/ISSUE-S20P2-001/confirm',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action_id:'USE_REGISTERED_PROJECT',actor_id:'demo-owner',actor_role:'ROLE::DATA_STEWARD',reason_zh:'绕过预览',idempotency_key:'browser-no-preview-001'})}); return {status:r.status,body:await r.json()}; }""")
            self.assertEqual((result["status"], result["body"]["code"]), (409, "HIGH_IMPACT_PREVIEW_REQUIRED"))
            self.open_first_detail(page)
            page.locator("#cw-preview").click()
            page.locator("#cw-preview-card").wait_for(state="visible")
            self.assertIn("高影响", page.locator("#cw-preview-risk").inner_text())
            page.screenshot(path=str(SCREENSHOT_ROOT / "confirmation_impact_preview.png"), full_page=True)
            page.locator("#cw-confirm").click()
            page.wait_for_function("() => window.KMFA_CONFIRMATION_TEST.snapshot()?.history?.event_count === 1")
            self.assertEqual(page.locator("#cw-list .cw-issue").count(), 4)
            self.assertIn("处理已登记", page.locator("#cw-feedback").inner_text())
            page.screenshot(path=str(SCREENSHOT_ROOT / "confirmation_history.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_refresh_recovers_confirmed_projection_and_history(self) -> None:
        page, errors = self.new_page()
        try:
            self.open_workbench(page)
            self.confirm_first(page)
            page.reload(wait_until="networkidle")
            page.locator("#confirmation-workbench-view").wait_for(state="visible")
            page.wait_for_function("() => window.KMFA_CONFIRMATION_TEST?.snapshot()?.history?.event_count === 1")
            snapshot = page.evaluate("window.KMFA_CONFIRMATION_TEST.snapshot()")
            self.assertEqual(snapshot["list"]["issue_count"], 4)
            self.assertEqual(snapshot["history"]["event_count"], 1)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_undo_requires_preview_reopens_issue_and_keeps_history(self) -> None:
        page, errors = self.new_page()
        try:
            self.open_workbench(page)
            self.confirm_first(page)
            page.get_by_role("button", name="先看撤销影响").click()
            page.locator("#cw-preview-card").wait_for(state="visible")
            self.assertIn("撤销前影响预览", page.locator("#cw-preview-title").inner_text())
            page.locator("#cw-confirm").click()
            page.wait_for_function("() => window.KMFA_CONFIRMATION_TEST.snapshot()?.history?.event_count === 2")
            snapshot = page.evaluate("window.KMFA_CONFIRMATION_TEST.snapshot()")
            self.assertEqual(snapshot["list"]["issue_count"], 5)
            self.assertEqual(snapshot["history"]["event_count"], 2)
            self.assertIn("ACTION_UNDONE", [row["event_type"] for row in snapshot["history"]["events"]])
            page.screenshot(path=str(SCREENSHOT_ROOT / "confirmation_undo_history.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_mobile_has_no_horizontal_overflow_and_touch_targets(self) -> None:
        page, errors = self.new_page(390, 844)
        try:
            self.open_workbench(page)
            self.open_first_detail(page)
            metrics = page.evaluate("""() => ({overflow:document.documentElement.scrollWidth-window.innerWidth, heights:[...document.querySelectorAll('#confirmation-workbench-view button,#confirmation-workbench-view a')].filter(n=>n.offsetParent!==null).map(n=>n.getBoundingClientRect().height)})""")
            self.assertLessEqual(metrics["overflow"], 1)
            self.assertTrue(metrics["heights"] and min(metrics["heights"]) >= 44)
            page.screenshot(path=str(SCREENSHOT_ROOT / "confirmation_mobile.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()


if __name__ == "__main__":
    unittest.main()
