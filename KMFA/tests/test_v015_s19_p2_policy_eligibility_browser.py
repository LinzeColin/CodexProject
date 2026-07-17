from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from playwright.sync_api import Browser, Page, Playwright, sync_playwright

from KMFA.tools import run_v015_s19_p2_policy_eligibility as runtime


REPO_ROOT = Path(__file__).resolve().parents[2]
SCREENSHOT_ROOT = REPO_ROOT / "KMFA/stage_artifacts/V015_S19_P2_POLICY_ELIGIBILITY/exports/screenshots"


class PolicyEligibilityBrowserTests(unittest.TestCase):
    playwright: Playwright
    browser: Browser

    @classmethod
    def setUpClass(cls) -> None:
        global SCREENSHOT_ROOT
        cls.screenshot_temp = None
        if os.environ.get("KMFA_PRESERVE_TRACKED_SCREENSHOTS") == "1":
            cls.screenshot_temp = tempfile.TemporaryDirectory()
            SCREENSHOT_ROOT = Path(cls.screenshot_temp.name)
        cls.event_temp = tempfile.TemporaryDirectory()
        cls.server, cls.server_thread, cls.base_url = runtime.start_server(event_path=Path(cls.event_temp.name) / "events.jsonl")
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
        cls.event_temp.cleanup()
        if cls.screenshot_temp is not None:
            cls.screenshot_temp.cleanup()

    def new_page(self, width: int = 1440, height: int = 1000) -> tuple[Page, list[str]]:
        page = self.browser.new_page(viewport={"width": width, "height": height})
        page.set_default_timeout(10_000)
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("console", lambda message: errors.append(message.text) if message.type == "error" and not message.text.startswith("Failed to load resource:") else None)
        return page, errors

    def wait_ready(self, page: Page) -> None:
        page.locator("#policy-eligibility-view").wait_for(state="visible")
        page.wait_for_function("() => window.KMFA_POLICY_ELIGIBILITY_TEST?.snapshot()?.summary?.policy_count === 6")
        page.locator("#pe-feedback", has_text="核对完成").wait_for()

    def test_01_desktop_registry_and_boundary(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/policy-eligibility", wait_until="networkidle")
            self.wait_ready(page)
            self.assertEqual(page.locator("#pe-registry .pe-policy-card").count(), 6)
            boundary = page.locator("#pe-boundary").inner_text()
            self.assertIn("不判断申报资格", boundary)
            self.assertIn("不得伪造", boundary)
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_policy_registry_desktop.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_02_superseded_policy_is_blocked(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/policy-eligibility", wait_until="networkidle")
            self.wait_ready(page)
            page.locator("#pe-policy-select").select_option("POLICY-HIGH-TECH-LEGACY")
            page.wait_for_function("() => window.KMFA_POLICY_ELIGIBILITY_TEST.snapshot()?.selected_policy_id === 'POLICY-HIGH-TECH-LEGACY'")
            snapshot = page.evaluate("window.KMFA_POLICY_ELIGIBILITY_TEST.snapshot()")
            self.assertEqual(snapshot["policy_readiness"]["status"], "POLICY_BLOCKED")
            card = page.locator('[data-policy-id="POLICY-HIGH-TECH-LEGACY"]')
            self.assertEqual(card.get_attribute("data-refresh"), "BLOCKED_SUPERSEDED")
            self.assertIn("已停止使用", card.inner_text())
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_policy_superseded_blocked.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_03_readiness_shows_gaps_without_conclusion(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/policy-eligibility", wait_until="networkidle")
            self.wait_ready(page)
            snapshot = page.evaluate("window.KMFA_POLICY_ELIGIBILITY_TEST.snapshot()")
            self.assertEqual(page.locator("#pe-readiness .pe-readiness-card").count(), 6)
            self.assertEqual(snapshot["formal_eligibility_conclusion_count"], 0)
            self.assertEqual(snapshot["fabricated_evidence_count"], 0)
            self.assertIn("不产生", page.locator("#pe-readiness-summary").inner_text())
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_policy_evidence_readiness.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_04_missing_source_task_cannot_complete(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/policy-eligibility", wait_until="networkidle")
            self.wait_ready(page)
            task = page.locator('[data-task-id="POLTASK-001"]')
            self.assertEqual(task.get_attribute("data-status"), "MISSING_SOURCE")
            task.locator("button").click()
            page.locator("#pe-feedback", has_text="无来源材料").wait_for()
            self.assertEqual(task.get_attribute("data-status"), "MISSING_SOURCE")
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_policy_task_missing_source.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_05_verified_source_task_completes(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/policy-eligibility", wait_until="networkidle")
            self.wait_ready(page)
            task = page.locator('[data-task-id="POLTASK-006"]')
            self.assertEqual(task.get_attribute("data-status"), "READY_TO_COMPLETE")
            task.locator("button").click()
            page.wait_for_function("() => window.KMFA_POLICY_ELIGIBILITY_TEST.snapshot()?.summary?.completed_task_count === 1")
            page.locator("#pe-feedback", has_text="任务已完成").wait_for()
            self.assertEqual(page.locator('[data-task-id="POLTASK-006"]').get_attribute("data-status"), "COMPLETED")
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_policy_task_completed.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_06_policy_filter_updates_readiness_and_tasks(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/policy-eligibility", wait_until="networkidle")
            self.wait_ready(page)
            page.locator("#pe-policy-select").select_option("POLICY-RD-DEDUCTION")
            page.wait_for_function("() => window.KMFA_POLICY_ELIGIBILITY_TEST.snapshot()?.selected_policy_id === 'POLICY-RD-DEDUCTION'")
            snapshot = page.evaluate("window.KMFA_POLICY_ELIGIBILITY_TEST.snapshot()")
            self.assertEqual(snapshot["policy_readiness"]["required_category_count"], 2)
            self.assertEqual(page.locator("#pe-task-list .pe-task-card").count(), 2)
            self.assertTrue(all("POLICY-RD-DEDUCTION" in row["policy_ids"] for row in snapshot["tasks"]))
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_07_company_and_period_switch_are_isolated(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/policy-eligibility", wait_until="networkidle")
            self.wait_ready(page)
            page.locator("#context-company").select_option("demo-west")
            page.locator("#context-period").select_option("2026-Q2")
            page.wait_for_function("() => window.KMFA_POLICY_ELIGIBILITY_TEST.snapshot()?.company_id === 'demo-west' && window.KMFA_POLICY_ELIGIBILITY_TEST.snapshot()?.period === '2026-Q2'")
            snapshot = page.evaluate("window.KMFA_POLICY_ELIGIBILITY_TEST.snapshot()")
            self.assertTrue(all(row["company_id"] == "demo-west" and row["period"] == "2026-Q2" for row in snapshot["evidence_items"]))
            self.assertEqual(snapshot["summary"]["completed_task_count"], 0)
            self.assertEqual(snapshot["cross_company_leak_count"], 0)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_08_mobile_touch_targets_and_no_overflow(self) -> None:
        page, errors = self.new_page(390, 844)
        try:
            page.goto(self.base_url + "/policy-eligibility", wait_until="networkidle")
            self.wait_ready(page)
            self.assertTrue(page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1"))
            for selector in ("#pe-policy-select", ".pe-back", '[data-task-id="POLTASK-001"] button'):
                self.assertGreaterEqual(page.locator(selector).evaluate("node => Math.round(node.getBoundingClientRect().height)"), 44)
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_policy_mobile.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()


if __name__ == "__main__":
    unittest.main()
