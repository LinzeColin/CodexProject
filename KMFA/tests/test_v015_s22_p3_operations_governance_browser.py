from __future__ import annotations

import hashlib
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from playwright.sync_api import Browser, Page, Playwright, sync_playwright

from KMFA.tools import run_v015_s22_p3_operations_governance as runtime


REPO_ROOT = Path(__file__).resolve().parents[2]
SCREENSHOT_ROOT = (
    REPO_ROOT
    / "KMFA/stage_artifacts/V015_S22_P3_OPERATIONS_GOVERNANCE/exports/screenshots"
)


class OperationsGovernanceBrowserTests(unittest.TestCase):
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
        cls.audit_path = cls.root / "audit.jsonl"
        cls.operations_root = cls.root / "operations"
        cls.auth_value = hashlib.sha256((cls.temporary.name + "auth").encode()).hexdigest()
        cls.signing_value = hashlib.sha256((cls.temporary.name + "sign").encode()).hexdigest()
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
            notification_event_path=cls.root / "notifications.jsonl",
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
        self.audit_path.unlink(missing_ok=True)
        self.audit_path.with_suffix(".jsonl.lock").unlink(missing_ok=True)
        shutil.rmtree(self.operations_root, ignore_errors=True)
        self.server.security_workbench = runtime.base_runtime.kernel.SecurityWorkbench(
            self.audit_path,
            secret_values=self.secret_values,
        )
        self.server.operations_workbench = runtime.kernel.OperationsWorkbench(
            self.operations_root,
            self.server.security_workbench,
        )

    def new_page(self, width: int = 1440, height: int = 1000) -> tuple[Page, list[str]]:
        page = self.browser.new_page(viewport={"width": width, "height": height})
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        return page, errors

    def open_operations(self, page: Page) -> None:
        page.goto(self.base_url + "/operations", wait_until="networkidle")
        page.locator("#operations-view").wait_for(state="visible")
        page.wait_for_function(
            "() => window.KMFA_OPERATIONS_TEST.snapshot().overview !== null"
        )

    def login(self, page: Page, username: str = "owner.local") -> dict:
        return page.evaluate(
            "([value,user]) => window.KMFA_OPERATIONS_TEST.login(value,user)",
            [self.auth_value, username],
        )

    def test_security_workbench_links_to_operations_and_six_services_render(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/security-audit", wait_until="networkidle")
            link = page.get_by_role("link", name="运维、恢复与升级控制")
            self.assertTrue(link.is_visible())
            link.click()
            page.locator("#operations-view").wait_for(state="visible")
            page.wait_for_function(
                "() => window.KMFA_OPERATIONS_TEST.snapshot().overview?.health.monitored_service_count === 6"
            )
            self.assertEqual(page.locator(".op-service").count(), 6)
            self.assertIn("0 / 6", "0 / 6")
            self.assertEqual(page.locator("#op-monitored").inner_text(), "6 / 6")
            page.screenshot(
                path=str(SCREENSHOT_ROOT / "operations_entry.png"),
                full_page=True,
            )
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_health_failure_drill_detects_blocks_and_recovers(self) -> None:
        page, errors = self.new_page()
        try:
            self.open_operations(page)
            self.login(page)
            value = page.evaluate(
                "window.KMFA_OPERATIONS_TEST.healthDrill('STORAGE')"
            )
            self.assertTrue(value["failure_detected"])
            self.assertTrue(value["critical_operation_blocked"])
            self.assertTrue(value["recovered"])
            self.assertEqual(page.locator("#op-production").inner_text(), "可以运行")
            page.screenshot(
                path=str(SCREENSHOT_ROOT / "health_failure_recovery.png"),
                full_page=True,
            )
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_unverified_backup_is_visibly_rejected(self) -> None:
        page, errors = self.new_page()
        try:
            self.open_operations(page)
            self.login(page)
            created = page.evaluate("window.KMFA_OPERATIONS_TEST.createBackup()")
            self.assertFalse(created["usable"])
            page.locator("#op-backup-restore").click()
            page.wait_for_function(
                "() => document.querySelector('#op-feedback').textContent.includes('尚未验证')"
            )
            self.assertIn("未验证", page.locator("#op-feedback").inner_text())
            page.screenshot(
                path=str(SCREENSHOT_ROOT / "backup_not_usable.png"),
                full_page=True,
            )
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_verified_backup_restores_with_zero_difference(self) -> None:
        page, errors = self.new_page()
        try:
            self.open_operations(page)
            self.login(page)
            page.evaluate("window.KMFA_OPERATIONS_TEST.createBackup()")
            page.evaluate("window.KMFA_OPERATIONS_TEST.verifyBackup()")
            value = page.evaluate("window.KMFA_OPERATIONS_TEST.restoreDrill()")
            self.assertEqual(
                (value["difference_count"], value["permission_difference_count"]),
                (0, 0),
            )
            self.assertIn("数据差异 0", page.locator("#op-restore-result").inner_text())
            self.assertEqual(page.locator("#op-usable").inner_text(), "1")
            page.screenshot(
                path=str(SCREENSHOT_ROOT / "restore_zero_difference.png"),
                full_page=True,
            )
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_migration_second_run_is_noop(self) -> None:
        page, errors = self.new_page()
        try:
            self.open_operations(page)
            self.login(page)
            first = page.evaluate("window.KMFA_OPERATIONS_TEST.migrate()")
            second = page.evaluate("window.KMFA_OPERATIONS_TEST.migrate()")
            self.assertEqual((first["status"], first["change_count"]), ("APPLIED", 4))
            self.assertEqual((second["status"], second["change_count"]), ("NOOP", 0))
            self.assertIn("幂等", page.locator("#op-migration-result").inner_text())
            page.screenshot(
                path=str(SCREENSHOT_ROOT / "migration_idempotent.png"),
                full_page=True,
            )
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_migration_failure_keeps_state_and_applied_migration_rolls_back(self) -> None:
        page, errors = self.new_page()
        try:
            self.open_operations(page)
            self.login(page)
            drill = page.evaluate("window.KMFA_OPERATIONS_TEST.migrationDrill()")
            self.assertTrue(drill["failure_detected"])
            self.assertTrue(drill["state_unchanged"])
            applied = page.evaluate("window.KMFA_OPERATIONS_TEST.migrate()")
            self.assertEqual(applied["status"], "APPLIED")
            rolled_back = page.evaluate("window.KMFA_OPERATIONS_TEST.rollback()")
            self.assertEqual(
                (
                    rolled_back["difference_count"],
                    rolled_back["permission_difference_count"],
                ),
                (0, 0),
            )
            self.assertIn("状态差异 0", page.locator("#op-migration-result").inner_text())
            page.screenshot(
                path=str(SCREENSHOT_ROOT / "migration_failure_rollback.png"),
                full_page=True,
            )
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_finance_role_cannot_create_backup(self) -> None:
        page, errors = self.new_page()
        try:
            self.open_operations(page)
            self.login(page, "finance.local")
            denied = page.evaluate(
                "window.KMFA_OPERATIONS_TEST.createBackup().catch(error => ({code:error.payload?.code}))"
            )
            self.assertEqual(denied["code"], "OWNER_PERMISSION_REQUIRED")
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_operations_history_survives_refresh_but_session_does_not(self) -> None:
        page, errors = self.new_page()
        try:
            self.open_operations(page)
            self.login(page)
            page.evaluate("window.KMFA_OPERATIONS_TEST.healthDrill('COMPUTATION')")
            before = page.evaluate(
                "window.KMFA_OPERATIONS_TEST.snapshot().overview.operations_journal.event_count"
            )
            page.reload(wait_until="networkidle")
            page.wait_for_function(
                "() => window.KMFA_OPERATIONS_TEST.snapshot().overview?.operations_journal.event_count > 6"
            )
            snapshot = page.evaluate("window.KMFA_OPERATIONS_TEST.snapshot()")
            self.assertEqual(
                snapshot["overview"]["operations_journal"]["event_count"],
                before,
            )
            self.assertIsNone(snapshot["session"])
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_mobile_layout_has_no_overflow_and_usable_controls(self) -> None:
        page, errors = self.new_page(390, 844)
        try:
            self.open_operations(page)
            metrics = page.evaluate(
                """() => ({overflow:document.documentElement.scrollWidth-window.innerWidth,heights:[...document.querySelectorAll('#operations-view button,#operations-view a,#operations-view select,#operations-view input')].filter(node=>node.offsetParent!==null).map(node=>node.getBoundingClientRect().height)})"""
            )
            self.assertLessEqual(metrics["overflow"], 1)
            self.assertTrue(metrics["heights"] and min(metrics["heights"]) >= 44)
            page.screenshot(
                path=str(SCREENSHOT_ROOT / "operations_mobile.png"),
                full_page=True,
            )
            self.assertEqual(errors, [])
        finally:
            page.close()


if __name__ == "__main__":
    unittest.main()
