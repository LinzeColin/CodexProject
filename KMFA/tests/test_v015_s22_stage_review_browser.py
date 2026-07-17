from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from playwright.sync_api import Browser, Page, Playwright, sync_playwright

from KMFA.tools import run_v015_s22_p3_operations_governance as runtime


REPO_ROOT = Path(__file__).resolve().parents[2]
SCREENSHOT_ROOT = (
    REPO_ROOT / "KMFA/stage_artifacts/V015_S22_STAGE_REVIEW/exports/screenshots"
)


class Stage22ReviewBrowserTests(unittest.TestCase):
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
        cls.notification_path = cls.root / "notifications.jsonl"
        cls.audit_path = cls.root / "audit.jsonl"
        cls.operations_root = cls.root / "operations"
        cls.auth_value = hashlib.sha256(
            (cls.temporary.name + "auth").encode()
        ).hexdigest()
        cls.signing_value = hashlib.sha256(
            (cls.temporary.name + "sign").encode()
        ).hexdigest()
        cls.secret_values = {
            "KMFA_LOCAL_AUTH_KEY": cls.auth_value,
            "KMFA_SESSION_SIGNING_KEY": cls.signing_value,
        }
        cls.server, cls.server_thread, cls.base_url = runtime.start_server(
            event_path=cls.root / "base.jsonl",
            data_root=cls.root / "data",
            confirmation_event_path=cls.root / "confirmation.jsonl",
            publication_event_path=cls.root / "publication.jsonl",
            report_model_event_path=cls.root / "models.jsonl",
            export_event_path=cls.root / "exports.jsonl",
            export_bundle_root=cls.root / "bundles",
            workflow_event_path=cls.root / "workflows.jsonl",
            notification_event_path=cls.notification_path,
            audit_event_path=cls.audit_path,
            operations_root=cls.operations_root,
            secret_values=cls.secret_values,
        )
        cls.playwright = sync_playwright().start()
        chrome = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
        cls.browser = cls.playwright.chromium.launch(
            headless=True,
            executable_path=str(chrome) if chrome.is_file() else None,
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
        for path in (self.notification_path, self.audit_path):
            path.unlink(missing_ok=True)
            path.with_suffix(path.suffix + ".lock").unlink(missing_ok=True)
        shutil.rmtree(self.operations_root, ignore_errors=True)
        self.server.notification_journal = runtime.notification_kernel.NotificationJournal(
            self.notification_path
        )
        self.server.security_workbench = runtime.base_runtime.kernel.SecurityWorkbench(
            self.audit_path,
            secret_values=self.secret_values,
        )
        self.server.operations_workbench = runtime.kernel.OperationsWorkbench(
            self.operations_root,
            self.server.security_workbench,
            state_provider=lambda: runtime._live_backup_state(self.server),
        )

    def new_page(
        self, width: int = 1440, height: int = 1000
    ) -> tuple[Page, list[str]]:
        page = self.browser.new_page(viewport={"width": width, "height": height})
        page.set_default_timeout(15_000)
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on(
            "console",
            lambda message: errors.append(message.text)
            if message.type == "error"
            and not message.text.startswith("Failed to load resource:")
            else None,
        )
        return page, errors

    def open_notifications(self, page: Page) -> None:
        page.goto(self.base_url + "/notification-delivery", wait_until="networkidle")
        page.locator("#notification-delivery-view").wait_for(state="visible")
        page.wait_for_function(
            "() => window.KMFA_NOTIFICATION_TEST?.snapshot()?.snapshot !== null"
        )

    def open_security(self, page: Page) -> None:
        page.goto(self.base_url + "/security-audit", wait_until="networkidle")
        page.locator("#security-audit-view").wait_for(state="visible")
        page.wait_for_function(
            "() => window.KMFA_SECURITY_TEST?.snapshot()?.snapshot !== null"
        )

    def open_operations(self, page: Page) -> None:
        page.goto(self.base_url + "/operations", wait_until="networkidle")
        page.locator("#operations-view").wait_for(state="visible")
        page.wait_for_function(
            "() => window.KMFA_OPERATIONS_TEST?.snapshot()?.overview !== null"
        )

    def login_security(self, page: Page, username: str = "finance.local") -> None:
        page.locator("#sa-username").select_option(username)
        page.locator("#sa-credential").fill(self.auth_value)
        page.locator("#sa-login").click()
        page.wait_for_function(
            "() => document.querySelector('#sa-session-state').textContent.includes('会话有效')"
        )

    def login_owner(self, page: Page) -> None:
        page.locator("#op-username").select_option("owner.local")
        page.locator("#op-credential").fill(self.auth_value)
        page.locator("#op-login").click()
        page.wait_for_function(
            "() => document.querySelector('#op-session').textContent.includes('会话有效')"
        )

    def test_unauthenticated_notification_mutation_is_blocked(self) -> None:
        page, errors = self.new_page()
        try:
            self.open_notifications(page)
            denied = page.evaluate(
                """() => window.KMFA_NOTIFICATION_TEST.sendReport()
                .then(() => ({code:'UNEXPECTED_PASS'}))
                .catch(error => ({code:error.payload?.code,status:error.status}))"""
            )
            self.assertEqual((denied["code"], denied["status"]), ("SESSION_INVALID", 401))
            self.assertEqual(self.server.notification_journal.snapshot()["event_count"], 0)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_login_continues_across_navigation_and_allows_safe_notification(self) -> None:
        page, errors = self.new_page()
        try:
            self.open_security(page)
            self.login_security(page)
            page.locator("#security-audit-view .s22-journey a[href='/notification-delivery']").click()
            page.locator("#notification-delivery-view").wait_for(state="visible")
            page.locator("#nd-send-report").click()
            page.wait_for_function(
                "() => document.querySelector('#nd-sent-count').textContent === '1'"
            )
            self.assertEqual(
                page.locator("#notification-delivery-view .s22-journey a[aria-current='step']").count(),
                1,
            )
            page.screenshot(
                path=str(SCREENSHOT_ROOT / "kmfa_s22_review_authenticated_journey.png"),
                full_page=True,
            )
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_audit_details_are_hidden_then_visible_after_login(self) -> None:
        page, errors = self.new_page()
        try:
            self.open_security(page)
            hidden = page.evaluate("window.KMFA_SECURITY_TEST.snapshot().snapshot")
            self.assertTrue(hidden["authentication_required"])
            self.assertEqual(hidden["query"]["events"], [])
            self.login_security(page)
            visible = page.evaluate("window.KMFA_SECURITY_TEST.snapshot().snapshot")
            self.assertFalse(visible["authentication_required"])
            self.assertGreaterEqual(visible["query"]["query_result_count"], 1)
            page.screenshot(
                path=str(SCREENSHOT_ROOT / "kmfa_s22_review_audit_authorized.png"),
                full_page=True,
            )
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_live_backup_restores_current_state_with_zero_difference(self) -> None:
        page, errors = self.new_page()
        try:
            self.open_operations(page)
            self.login_owner(page)
            page.locator("#operations-view .s22-journey a[href='/notification-delivery']").click()
            page.locator("#notification-delivery-view").wait_for(state="visible")
            page.locator("#nd-send-report").click()
            page.wait_for_function(
                "() => document.querySelector('#nd-sent-count').textContent === '1'"
            )
            page.locator("#notification-delivery-view .s22-journey a[href='/operations']").click()
            page.locator("#operations-view").wait_for(state="visible")
            page.wait_for_function(
                "() => document.querySelector('#op-session').textContent.includes('会话有效')"
            )
            page.evaluate("window.KMFA_OPERATIONS_TEST.createBackup()")
            page.evaluate("window.KMFA_OPERATIONS_TEST.verifyBackup()")
            restored = page.evaluate("window.KMFA_OPERATIONS_TEST.restoreDrill()")
            backup_id = page.evaluate("window.KMFA_OPERATIONS_TEST.snapshot().backupId")
            envelope = self.server.operations_workbench.backups._read(backup_id)
            datasets = envelope["payload"]["datasets"]
            self.assertEqual(
                (restored["difference_count"], restored["permission_difference_count"]),
                (0, 0),
            )
            self.assertEqual(datasets["PRIVATE_DERIVED"]["source"], "LIVE_RUNTIME")
            self.assertEqual(datasets["PRIVATE_DERIVED"]["notification_event_count"], 1)
            self.assertGreater(datasets["AUDIT_EVENTS"]["security_event_count"], 0)
            encoded = json.dumps(envelope, ensure_ascii=False)
            self.assertNotIn(self.auth_value, encoded)
            self.assertNotIn(self.signing_value, encoded)
            page.screenshot(
                path=str(SCREENSHOT_ROOT / "kmfa_s22_review_live_backup_restore.png"),
                full_page=True,
            )
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_health_failure_blocks_then_recovers(self) -> None:
        page, errors = self.new_page()
        try:
            self.open_operations(page)
            self.login_owner(page)
            value = page.evaluate("window.KMFA_OPERATIONS_TEST.healthDrill('STORAGE')")
            self.assertTrue(value["failure_detected"])
            self.assertTrue(value["critical_operation_blocked"])
            self.assertTrue(value["recovered"])
            self.assertEqual(page.locator("#op-production").inner_text(), "可以运行")
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_all_critical_operations_are_visible_in_authorized_audit(self) -> None:
        page, errors = self.new_page()
        try:
            self.open_operations(page)
            self.login_owner(page)
            page.evaluate("window.KMFA_OPERATIONS_TEST.healthDrill('COMPUTATION')")
            page.evaluate("window.KMFA_OPERATIONS_TEST.createBackup()")
            page.evaluate("window.KMFA_OPERATIONS_TEST.verifyBackup()")
            page.evaluate("window.KMFA_OPERATIONS_TEST.restoreDrill()")
            page.evaluate("window.KMFA_OPERATIONS_TEST.migrate()")
            page.evaluate("window.KMFA_OPERATIONS_TEST.rollback()")
            page.evaluate("window.KMFA_OPERATIONS_TEST.migrationDrill()")
            page.locator("#operations-view .s22-journey a[href='/security-audit']").click()
            page.locator("#security-audit-view").wait_for(state="visible")
            page.wait_for_function(
                "() => window.KMFA_SECURITY_TEST.snapshot().snapshot?.query?.query_result_count >= 8"
            )
            events = page.evaluate(
                "window.KMFA_SECURITY_TEST.snapshot().snapshot.query.events"
            )
            subjects = {row["subject_ref"] for row in events}
            self.assertTrue(
                {
                    "SERVICE::HEALTH-DRILL-S22P3",
                    "BACKUP::S22P3",
                    "BACKUP::VERIFY-S22P3",
                    "BACKUP::RESTORE-S22P3",
                    "MIGRATION::S22P3",
                    "MIGRATION::ROLLBACK-S22P3",
                    "MIGRATION::FAILURE-DRILL-S22P3",
                }
                <= subjects
            )
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_migration_is_idempotent_failure_safe_and_reversible(self) -> None:
        page, errors = self.new_page()
        try:
            self.open_operations(page)
            self.login_owner(page)
            first = page.evaluate("window.KMFA_OPERATIONS_TEST.migrate()")
            second = page.evaluate("window.KMFA_OPERATIONS_TEST.migrate()")
            rolled_back = page.evaluate("window.KMFA_OPERATIONS_TEST.rollback()")
            failure = page.evaluate("window.KMFA_OPERATIONS_TEST.migrationDrill()")
            self.assertEqual((first["status"], first["change_count"]), ("APPLIED", 4))
            self.assertEqual((second["status"], second["change_count"]), ("NOOP", 0))
            self.assertEqual(
                (rolled_back["difference_count"], rolled_back["permission_difference_count"]),
                (0, 0),
            )
            self.assertTrue(failure["failure_detected"] and failure["state_unchanged"])
            page.screenshot(
                path=str(SCREENSHOT_ROOT / "kmfa_s22_review_migration_rollback.png"),
                full_page=True,
            )
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_mobile_has_no_overflow_and_touch_targets_are_44px(self) -> None:
        page, errors = self.new_page(390, 844)
        try:
            self.open_operations(page)
            metrics = page.evaluate(
                """() => ({
                    overflow: document.documentElement.scrollWidth - window.innerWidth,
                    heights: [...document.querySelectorAll('#operations-view button,#operations-view a,#operations-view select,#operations-view input')]
                        .filter(node => node.offsetParent !== null)
                        .map(node => node.getBoundingClientRect().height)
                })"""
            )
            self.assertLessEqual(metrics["overflow"], 1)
            self.assertTrue(metrics["heights"] and min(metrics["heights"]) >= 44)
            page.screenshot(
                path=str(SCREENSHOT_ROOT / "kmfa_s22_review_mobile.png"),
                full_page=True,
            )
            self.assertEqual(errors, [])
        finally:
            page.close()


if __name__ == "__main__":
    unittest.main()
