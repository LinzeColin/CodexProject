from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from playwright.sync_api import Browser, Page, Playwright, sync_playwright

from KMFA.tools import run_v015_s22_p1_notifications as runtime


REPO_ROOT = Path(__file__).resolve().parents[2]
SCREENSHOT_ROOT = REPO_ROOT / "KMFA/stage_artifacts/V015_S22_P1_NOTIFICATIONS/exports/screenshots"


class NotificationBrowserTests(unittest.TestCase):
    playwright: Playwright
    browser: Browser

    @classmethod
    def setUpClass(cls) -> None:
        global SCREENSHOT_ROOT
        cls.screenshot_temp = None
        if os.environ.get("KMFA_PRESERVE_TRACKED_SCREENSHOTS") == "1":
            cls.screenshot_temp = tempfile.TemporaryDirectory(); SCREENSHOT_ROOT = Path(cls.screenshot_temp.name)
        cls.temporary = tempfile.TemporaryDirectory(); cls.root = Path(cls.temporary.name)
        cls.notification_path = cls.root / "notifications.jsonl"
        cls.server, cls.server_thread, cls.base_url = runtime.start_server(
            event_path=cls.root / "base.jsonl", data_root=cls.root / "data", confirmation_event_path=cls.root / "confirmation.jsonl",
            publication_event_path=cls.root / "publication.jsonl", report_model_event_path=cls.root / "models.jsonl",
            export_event_path=cls.root / "exports.jsonl", export_bundle_root=cls.root / "bundles",
            workflow_event_path=cls.root / "workflows.jsonl", notification_event_path=cls.notification_path,
        )
        cls.playwright = sync_playwright().start(); chrome = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
        cls.browser = cls.playwright.chromium.launch(headless=True, executable_path=str(chrome) if chrome.is_file() else None)
        SCREENSHOT_ROOT.mkdir(parents=True, exist_ok=True)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.browser.close(); cls.playwright.stop(); cls.server.shutdown(); cls.server.server_close(); cls.server_thread.join(timeout=3)
        cls.temporary.cleanup()
        if cls.screenshot_temp is not None: cls.screenshot_temp.cleanup()

    def setUp(self) -> None:
        self.notification_path.unlink(missing_ok=True); self.notification_path.with_suffix(".jsonl.lock").unlink(missing_ok=True)
        self.server.notification_journal = runtime.kernel.NotificationJournal(self.notification_path)

    def new_page(self, width=1440, height=1000) -> tuple[Page, list[str]]:
        page = self.browser.new_page(viewport={"width": width, "height": height}); page.set_default_timeout(15_000)
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("console", lambda message: errors.append(message.text) if message.type == "error" and not message.text.startswith("Failed to load resource:") else None)
        return page, errors

    def open_notifications(self, page: Page) -> None:
        page.goto(self.base_url + "/notification-delivery", wait_until="networkidle")
        page.locator("#notification-delivery-view").wait_for(state="visible")
        page.wait_for_function("() => window.KMFA_NOTIFICATION_TEST?.snapshot()?.options?.rule_catalog_count === 7")
        self.assertFalse(page.locator("#not-found-view").is_visible())

    def test_report_center_links_to_notification_center(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/report-workflow", wait_until="networkidle")
            link = page.get_by_role("link", name="通知中心"); self.assertTrue(link.is_visible()); link.click()
            page.locator("#notification-delivery-view").wait_for(state="visible")
            page.screenshot(path=str(SCREENSHOT_ROOT / "notification_entry.png"), full_page=True)
            self.assertEqual(errors, [])
        finally: page.close()

    def test_report_reminder_contains_only_safe_fields(self) -> None:
        page, errors = self.new_page()
        try:
            self.open_notifications(page); page.locator("#nd-send-report").click()
            page.wait_for_function("() => window.KMFA_NOTIFICATION_TEST.snapshot().snapshot.sent_sandbox_count === 1")
            notice = page.evaluate("window.KMFA_NOTIFICATION_TEST.snapshot().snapshot.notifications[0]")
            self.assertEqual({row["field"] for row in notice["message"]["body_fields"]}, {"kind", "period", "status", "safe_entry"})
            self.assertEqual((notice["message"]["amount_detail_count"], notice["message"]["attachment_count"], notice["message"]["external_network_request_count"]), (0, 0, 0))
            page.screenshot(path=str(SCREENSHOT_ROOT / "report_reminder_safe.png"), full_page=True); self.assertEqual(errors, [])
        finally: page.close()

    def test_duplicate_report_is_suppressed_without_second_delivery(self) -> None:
        page, errors = self.new_page()
        try:
            self.open_notifications(page)
            body = {"report_version_id":"REPORT-BROWSER-DUPLICATE","report_type":"MONTHLY","period_label":"2026年7月","report_status":"GENERATED","occurred_at":"2026-07-17T00:00:00+00:00"}
            first = page.request.post(self.base_url + "/api/notification-delivery/report", data={**body, "idempotency_key":"browser-duplicate-001"})
            second = page.request.post(self.base_url + "/api/notification-delivery/report", data={**body, "idempotency_key":"browser-duplicate-002", "occurred_at":"2026-07-17T00:01:00+00:00"})
            self.assertEqual((first.json()["status"], second.json()["suppression_reason"]), ("SENT_SANDBOX", "DUPLICATE_WINDOW"))
            page.evaluate("window.KMFA_NOTIFICATION_TEST.load()"); page.wait_for_function("() => window.KMFA_NOTIFICATION_TEST.snapshot().snapshot.suppressed_count === 1")
            page.screenshot(path=str(SCREENSHOT_ROOT / "duplicate_suppressed.png"), full_page=True); self.assertEqual(errors, [])
        finally: page.close()

    def test_five_alert_categories_are_enabled_and_unconfirmed_rule_disabled(self) -> None:
        page, errors = self.new_page()
        try:
            self.open_notifications(page); options = page.evaluate("window.KMFA_NOTIFICATION_TEST.snapshot().options")
            active = [row for row in options["rules"] if row["enabled"] and row["category"] != "REPORT"]
            self.assertEqual({row["category"] for row in active}, {"CASH", "RECEIVABLE", "TAX", "DATA_STALE", "IMPORT_FAILED"})
            self.assertTrue(page.eval_on_selector('#nd-alert-rule option[value="RULE-DRAFT-FORECAST-VARIANCE"]', "node => node.disabled"))
            page.screenshot(path=str(SCREENSHOT_ROOT / "alert_rules.png"), full_page=True); self.assertEqual(errors, [])
        finally: page.close()

    def test_rule_can_be_silenced_and_resumed(self) -> None:
        page, errors = self.new_page()
        try:
            self.open_notifications(page); page.evaluate("window.KMFA_NOTIFICATION_TEST.setSilenced('RULE-CASH-MAJOR-RISK',true)")
            page.wait_for_function("() => window.KMFA_NOTIFICATION_TEST.snapshot().snapshot.rules.find(r=>r.rule_id==='RULE-CASH-MAJOR-RISK').silenced")
            self.assertIn("已静默", page.locator("#nd-rules").inner_text())
            page.evaluate("window.KMFA_NOTIFICATION_TEST.setSilenced('RULE-CASH-MAJOR-RISK',false)")
            page.wait_for_function("() => !window.KMFA_NOTIFICATION_TEST.snapshot().snapshot.rules.find(r=>r.rule_id==='RULE-CASH-MAJOR-RISK').silenced")
            page.screenshot(path=str(SCREENSHOT_ROOT / "silence_resume.png"), full_page=True); self.assertEqual(errors, [])
        finally: page.close()

    def test_failed_alert_displays_reason_and_retries(self) -> None:
        page, errors = self.new_page()
        try:
            self.open_notifications(page); page.locator("#nd-alert-rule").select_option("RULE-IMPORT-FAILED"); page.locator("#nd-simulate-failure").check(); page.locator("#nd-send-alert").click()
            page.wait_for_function("() => window.KMFA_NOTIFICATION_TEST.snapshot().snapshot.failed_retryable_count === 1")
            self.assertIn("SANDBOX_TRANSIENT_FAILURE", page.locator("#nd-history").inner_text()); page.get_by_role("button", name="幂等重试").click()
            page.wait_for_function("() => window.KMFA_NOTIFICATION_TEST.snapshot().snapshot.retry_success_count === 1")
            page.screenshot(path=str(SCREENSHOT_ROOT / "failure_retry.png"), full_page=True); self.assertEqual(errors, [])
        finally: page.close()

    def test_delivery_log_survives_refresh(self) -> None:
        page, errors = self.new_page()
        try:
            self.open_notifications(page); page.locator("#nd-send-report").click(); page.wait_for_function("() => window.KMFA_NOTIFICATION_TEST.snapshot().snapshot.event_count === 1")
            page.reload(wait_until="networkidle"); page.wait_for_function("() => window.KMFA_NOTIFICATION_TEST?.snapshot()?.snapshot?.event_count === 1")
            self.assertEqual(page.locator(".nd-event").count(), 1); self.assertEqual(errors, [])
        finally: page.close()

    def test_mobile_has_no_overflow_and_targets_are_44px(self) -> None:
        page, errors = self.new_page(390, 844)
        try:
            self.open_notifications(page)
            metrics = page.evaluate("""() => ({overflow:document.documentElement.scrollWidth-window.innerWidth,heights:[...document.querySelectorAll('#notification-delivery-view button,#notification-delivery-view a,#notification-delivery-view select,#notification-delivery-view input:not([type=checkbox])')].filter(n=>n.offsetParent!==null).map(n=>n.getBoundingClientRect().height)})""")
            self.assertLessEqual(metrics["overflow"], 1); self.assertTrue(metrics["heights"] and min(metrics["heights"]) >= 44)
            page.screenshot(path=str(SCREENSHOT_ROOT / "notification_mobile.png"), full_page=True); self.assertEqual(errors, [])
        finally: page.close()


if __name__ == "__main__":
    unittest.main()
