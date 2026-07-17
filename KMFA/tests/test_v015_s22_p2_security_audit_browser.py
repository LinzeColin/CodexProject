from __future__ import annotations

import hashlib
import os
import tempfile
import unittest
from pathlib import Path

from playwright.sync_api import Browser, Page, Playwright, sync_playwright

from KMFA.tools import run_v015_s22_p2_security_audit as runtime


REPO_ROOT = Path(__file__).resolve().parents[2]
SCREENSHOT_ROOT = REPO_ROOT / "KMFA/stage_artifacts/V015_S22_P2_SECURITY_AUDIT/exports/screenshots"


class SecurityAuditBrowserTests(unittest.TestCase):
    playwright: Playwright
    browser: Browser

    @classmethod
    def setUpClass(cls) -> None:
        global SCREENSHOT_ROOT
        cls.screenshot_temp = None
        if os.environ.get("KMFA_PRESERVE_TRACKED_SCREENSHOTS") == "1":
            cls.screenshot_temp = tempfile.TemporaryDirectory(); SCREENSHOT_ROOT = Path(cls.screenshot_temp.name)
        cls.temporary = tempfile.TemporaryDirectory(); cls.root = Path(cls.temporary.name)
        cls.audit_path = cls.root / "audit.jsonl"
        cls.auth_value = hashlib.sha256((cls.temporary.name + "auth").encode()).hexdigest()
        cls.signing_value = hashlib.sha256((cls.temporary.name + "sign").encode()).hexdigest()
        cls.secret_values = {"KMFA_LOCAL_AUTH_KEY": cls.auth_value, "KMFA_SESSION_SIGNING_KEY": cls.signing_value}
        cls.server, cls.server_thread, cls.base_url = runtime.start_server(
            event_path=cls.root / "base.jsonl", data_root=cls.root / "data", confirmation_event_path=cls.root / "confirmation.jsonl",
            publication_event_path=cls.root / "publication.jsonl", report_model_event_path=cls.root / "models.jsonl",
            export_event_path=cls.root / "exports.jsonl", export_bundle_root=cls.root / "bundles",
            workflow_event_path=cls.root / "workflows.jsonl", notification_event_path=cls.root / "notifications.jsonl",
            audit_event_path=cls.audit_path, secret_values=cls.secret_values,
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
        self.audit_path.unlink(missing_ok=True); self.audit_path.with_suffix(".jsonl.lock").unlink(missing_ok=True)
        self.server.security_workbench = runtime.kernel.SecurityWorkbench(self.audit_path, secret_values=self.secret_values)

    def new_page(self, width=1440, height=1000) -> tuple[Page, list[str]]:
        page = self.browser.new_page(viewport={"width": width, "height": height}); errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        return page, errors

    def open_security(self, page: Page) -> None:
        page.goto(self.base_url + "/security-audit", wait_until="networkidle")
        page.locator("#security-audit-view").wait_for(state="visible")
        page.wait_for_function("() => window.KMFA_SECURITY_TEST.snapshot().options !== null")

    def login(self, page: Page, username="finance.local") -> dict:
        return page.evaluate("([value,user]) => window.KMFA_SECURITY_TEST.login(value,user)", [self.auth_value, username])

    def test_notification_center_links_to_security_workbench(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/notification-delivery", wait_until="networkidle")
            link = page.get_by_role("link", name="安全与审计"); self.assertTrue(link.is_visible()); link.click()
            page.locator("#security-audit-view").wait_for(state="visible")
            page.screenshot(path=str(SCREENSHOT_ROOT / "security_entry.png"), full_page=True)
            self.assertEqual(errors, [])
        finally: page.close()

    def test_login_and_protected_action_are_audited(self) -> None:
        page, errors = self.new_page()
        try:
            self.open_security(page); login = self.login(page)
            self.assertEqual((login["authenticated"], login["session_token"]), (True, "[CLIENT_MEMORY_ONLY]"))
            value = page.evaluate("window.KMFA_SECURITY_TEST.action('SENSITIVE_VIEW')")
            self.assertEqual((value["action_type"], value["result"]), ("SENSITIVE_VIEW", "SUCCESS"))
            page.screenshot(path=str(SCREENSHOT_ROOT / "authenticated_audit.png"), full_page=True)
            self.assertEqual(errors, [])
        finally: page.close()

    def test_audit_query_filters_exact_action(self) -> None:
        page, errors = self.new_page()
        try:
            self.open_security(page); self.login(page)
            page.evaluate("window.KMFA_SECURITY_TEST.action('PROCESSING')")
            page.evaluate("window.KMFA_SECURITY_TEST.action('PUBLICATION')")
            page.locator("#sa-query-action").select_option("PUBLICATION"); page.locator("#sa-query-result").select_option("SUCCESS"); page.locator("#sa-query").click()
            page.wait_for_function("() => window.KMFA_SECURITY_TEST.snapshot().snapshot.query.query_result_count === 1")
            self.assertIn("PUBLICATION", page.locator("#sa-history").inner_text())
            page.screenshot(path=str(SCREENSHOT_ROOT / "audit_query.png"), full_page=True); self.assertEqual(errors, [])
        finally: page.close()

    def test_secret_values_never_render_and_input_is_cleared(self) -> None:
        page, errors = self.new_page()
        try:
            self.open_security(page); page.locator("#sa-credential").fill(self.auth_value); page.locator("#sa-login").click()
            page.wait_for_function("() => window.KMFA_SECURITY_TEST.snapshot().session?.role === 'FINANCE_ADMIN'")
            self.assertEqual(page.locator("#sa-credential").input_value(), "")
            text = page.locator("#security-audit-view").inner_text()
            self.assertNotIn(self.auth_value, text); self.assertNotIn(self.signing_value, text)
            self.assertIn("不显示值", text)
            page.screenshot(path=str(SCREENSHOT_ROOT / "secrets_redacted.png"), full_page=True); self.assertEqual(errors, [])
        finally: page.close()

    def test_five_attack_categories_are_rejected(self) -> None:
        page, errors = self.new_page()
        try:
            self.open_security(page); self.login(page)
            for category in ("INJECTION", "PATH_TRAVERSAL", "MALICIOUS_FILE", "FORMULA_INJECTION"):
                value = page.evaluate("category => window.KMFA_SECURITY_TEST.attack(category)", category)
                self.assertTrue(value["rejected"])
            denied = page.evaluate("window.KMFA_SECURITY_TEST.download('PUBLIC_LINK').catch(error => ({code:error.payload?.code}))")
            self.assertEqual(denied["code"], "PUBLIC_LINK_BLOCKED")
            page.evaluate("window.KMFA_SECURITY_TEST.load()")
            page.wait_for_function("() => window.KMFA_SECURITY_TEST.snapshot().snapshot.rejected_attack_count === 5")
            page.screenshot(path=str(SCREENSHOT_ROOT / "attack_samples_blocked.png"), full_page=True); self.assertEqual(errors, [])
        finally: page.close()

    def test_tamper_probe_blocks_production_continuation(self) -> None:
        page, errors = self.new_page()
        try:
            self.open_security(page); self.login(page)
            value = page.evaluate("window.KMFA_SECURITY_TEST.tamper()")
            self.assertTrue(value["tamper_detected"]); self.assertFalse(value["production_continuation_allowed"])
            self.assertEqual(errors, [])
        finally: page.close()

    def test_readonly_role_cannot_change_parameter(self) -> None:
        page, errors = self.new_page()
        try:
            self.open_security(page); self.login(page, "readonly.local")
            denied = page.evaluate("window.KMFA_SECURITY_TEST.action('PARAMETER_CHANGE').catch(error => ({code:error.payload?.code}))")
            self.assertEqual(denied["code"], "PERMISSION_DENIED")
            page.evaluate("window.KMFA_SECURITY_TEST.load()")
            page.wait_for_function("() => window.KMFA_SECURITY_TEST.snapshot().snapshot.audit.denied_event_count === 1")
            self.assertEqual(errors, [])
        finally: page.close()

    def test_audit_survives_refresh_without_session_persistence(self) -> None:
        page, errors = self.new_page()
        try:
            self.open_security(page); self.login(page); page.evaluate("window.KMFA_SECURITY_TEST.action('PROCESSING')")
            before = page.evaluate("window.KMFA_SECURITY_TEST.snapshot().snapshot.audit.audit_event_count")
            page.reload(wait_until="networkidle"); page.wait_for_function("() => window.KMFA_SECURITY_TEST.snapshot().snapshot?.audit.audit_event_count >= 2")
            snapshot = page.evaluate("window.KMFA_SECURITY_TEST.snapshot()")
            self.assertEqual(snapshot["snapshot"]["audit"]["audit_event_count"], before)
            self.assertIsNone(snapshot["session"]); self.assertEqual(errors, [])
        finally: page.close()

    def test_mobile_layout_has_no_overflow_and_usable_controls(self) -> None:
        page, errors = self.new_page(390, 844)
        try:
            self.open_security(page)
            metrics = page.evaluate("""() => ({overflow:document.documentElement.scrollWidth-window.innerWidth,heights:[...document.querySelectorAll('#security-audit-view button,#security-audit-view a,#security-audit-view select,#security-audit-view input')].filter(n=>n.offsetParent!==null).map(n=>n.getBoundingClientRect().height)})""")
            self.assertLessEqual(metrics["overflow"], 1); self.assertTrue(metrics["heights"] and min(metrics["heights"]) >= 44)
            page.screenshot(path=str(SCREENSHOT_ROOT / "security_mobile.png"), full_page=True); self.assertEqual(errors, [])
        finally: page.close()


if __name__ == "__main__":
    unittest.main()
