from __future__ import annotations

import unittest
from pathlib import Path

from playwright.sync_api import Browser, Page, Playwright, sync_playwright

from KMFA.tools import run_v015_s15_p2_identity_roles as runtime


REPO_ROOT = Path(__file__).resolve().parents[2]
SCREENSHOT_ROOT = REPO_ROOT / "KMFA/stage_artifacts/V015_S15_P2_IDENTITY_ROLES/exports/screenshots"


class IdentityRoleBrowserTests(unittest.TestCase):
    playwright: Playwright
    browser: Browser

    @classmethod
    def setUpClass(cls) -> None:
        cls.server, cls.server_thread, cls.base_url = runtime.start_server()
        cls.playwright = sync_playwright().start()
        chrome = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
        cls.browser = cls.playwright.chromium.launch(
            headless=True,
            executable_path=str(chrome) if chrome.is_file() else None,
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.browser.close()
        cls.playwright.stop()
        cls.server.shutdown()
        cls.server.server_close()
        cls.server_thread.join(timeout=3)

    def new_page(self, width: int = 1440, height: int = 1000) -> tuple[Page, list[str]]:
        page = self.browser.new_page(viewport={"width": width, "height": height})
        page.set_default_timeout(8_000)
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on(
            "console",
            lambda message: errors.append(message.text)
            if message.type == "error" and not message.text.startswith("Failed to load resource:")
            else None,
        )
        return page, errors

    def wait_ready(self, page: Page) -> None:
        page.locator("#page-view:not([hidden])").wait_for()
        page.locator("#context-status strong", has_text="已更新").wait_for()
        page.locator('#role-feedback[data-state="allowed"]').wait_for()

    def test_role_switch_changes_permission_without_expanding_assignment(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/overview", wait_until="networkidle")
            self.wait_ready(page)
            self.assertEqual(page.locator("#active-role-chip").inner_text(), "经营负责人")
            self.assertEqual(page.locator("#permission-body tr").count(), 5)
            page.locator('[data-authorize="DATA_SOURCE:VIEW_SENSITIVE"]').click()
            page.locator('#role-feedback[data-state="blocked"]').wait_for()
            self.assertIn("没有这项权限", page.locator("#role-feedback").inner_text())
            page.select_option("#identity-role", "finance")
            page.fill("#role-switch-reason", "核对财务来源和报告")
            page.locator("#switch-role").click()
            page.locator("#active-role-chip", has_text="财务").wait_for()
            page.locator("#role-feedback", has_text="当前授权范围已按").wait_for()
            page.locator('[data-authorize="DATA_SOURCE:VIEW_SENSITIVE"]').click()
            page.locator("#role-feedback", has_text="拥有这项权限").wait_for()
            self.assertIn("拥有这项权限", page.locator("#role-feedback").inner_text())
            self.assertGreaterEqual(page.locator("#audit-list li").count(), 3)
            audit = page.locator("#audit-list").text_content() or ""
            self.assertIn("经营负责人", audit)
            self.assertIn("财务", audit)
            self.assertIn("理由", audit)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_unassigned_role_and_cross_company_scope_are_blocked(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/overview", wait_until="networkidle")
            self.wait_ready(page)
            result = page.evaluate(
                """async () => {
                  const response = await fetch('/api/role-switch', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({user_id:'demo-finance',from_role:'finance',to_role:'tax',company_id:'demo-north',reason:'尝试核对税务事项'})});
                  return {status:response.status,body:await response.json()};
                }"""
            )
            self.assertEqual(result["status"], 403)
            self.assertEqual(result["body"]["event"]["reason_code"], "ROLE_NOT_ASSIGNED")
            page.evaluate("window.KMFA_ROLE_TEST.setIdentity('demo-finance','finance')")
            page.select_option("#context-company", "demo-south")
            page.locator('#role-feedback[data-state="blocked"]').wait_for()
            self.assertIn("没有查看这个公司主体", page.locator("#role-feedback").inner_text())
            page.select_option("#context-company", "demo-north")
            page.locator('#role-feedback[data-state="allowed"]').wait_for()
            self.assertEqual(page.locator("#active-role-chip").inner_text(), "财务")
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_role_hat_persists_but_authorization_is_rechecked_on_reload(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/reports", wait_until="networkidle")
            self.wait_ready(page)
            page.select_option("#identity-role", "reviewer")
            page.fill("#role-switch-reason", "审核报告发布范围")
            page.locator("#switch-role").click()
            page.locator("#active-role-chip", has_text="审核").wait_for()
            page.reload(wait_until="networkidle")
            self.wait_ready(page)
            self.assertEqual(page.locator("#active-role-chip").inner_text(), "审核")
            self.assertEqual(page.input_value("#identity-user"), "demo-owner")
            self.assertEqual(page.input_value("#identity-role"), "reviewer")
            self.assertIn("确认发布报告", page.locator("#permission-body").inner_text())
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_approval_separates_roles_and_records_same_person_reason(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/reports", wait_until="networkidle")
            self.wait_ready(page)
            page.evaluate("window.KMFA_ROLE_TEST.setIdentity('demo-owner','finance')")
            page.fill("#operation-reason", "申请发布公开演示报告")
            created = page.evaluate("window.KMFA_ROLE_TEST.createApproval('REPORT_PUBLISH','申请发布公开演示报告')")
            self.assertTrue(created["ok"])
            request_id = created["data"]["request"]["request_id"]
            same_role = page.evaluate(
                "([requestId]) => window.KMFA_ROLE_TEST.approve(requestId,'尝试由原角色确认报告')",
                [request_id],
            )
            self.assertEqual(same_role["status"], 403)
            self.assertEqual(same_role["data"]["event"]["reason_code"], "SAME_ROLE_SEPARATION_REQUIRED")
            switched = page.evaluate("window.KMFA_ROLE_TEST.switchRole('reviewer','切换审核角色确认范围')")
            self.assertTrue(switched["ok"])
            approved = page.evaluate(
                "([requestId]) => window.KMFA_ROLE_TEST.approve(requestId,'审核发布理由与公开范围')",
                [request_id],
            )
            self.assertTrue(approved["ok"])
            self.assertEqual(approved["data"]["request"]["state"], "APPROVED_DEMO_ONLY")
            self.assertTrue(approved["data"]["request"]["approval"]["same_person_different_role"])
            self.assertFalse(approved["data"]["request"]["real_business_action_performed"])
            self.assertIn("已确认（仅演示）", page.locator("#approval-copy").inner_text())
            audit = page.locator("#audit-list").text_content() or ""
            self.assertIn("发起角色不能同时确认", audit)
            self.assertIn("审核发布理由与公开范围", audit)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_keyboard_mobile_and_permission_table_remain_usable(self) -> None:
        page, errors = self.new_page(390, 844)
        try:
            page.goto(self.base_url + "/overview", wait_until="networkidle")
            self.wait_ready(page)
            self.assertEqual(page.locator(".sidebar").count(), 0)
            self.assertEqual(page.locator("#permission-body tr").count(), 5)
            self.assertTrue(page.locator("#switch-role").is_visible())
            page.locator("#switch-role").focus()
            self.assertEqual(page.evaluate("document.activeElement.id"), "switch-role")
            self.assertEqual(page.locator('[role="status"]').count() >= 2, True)
            SCREENSHOT_ROOT.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_identity_roles_mobile.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_desktop_default_denied_and_approved_screenshots(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/overview", wait_until="networkidle")
            self.wait_ready(page)
            SCREENSHOT_ROOT.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_identity_roles_desktop.png"), full_page=False)
            page.locator('[data-authorize="DATA_SOURCE:VIEW_SENSITIVE"]').click()
            page.locator('#role-feedback[data-state="blocked"]').wait_for()
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_identity_roles_denied.png"), full_page=False)
            page.evaluate("window.KMFA_ROLE_TEST.setIdentity('demo-owner','finance')")
            created = page.evaluate("window.KMFA_ROLE_TEST.createApproval('REPORT_PUBLISH','申请发布公开演示报告')")
            request_id = created["data"]["request"]["request_id"]
            page.evaluate("window.KMFA_ROLE_TEST.switchRole('reviewer','切换审核角色确认范围')")
            page.evaluate(
                "([requestId]) => window.KMFA_ROLE_TEST.approve(requestId,'审核发布理由与公开范围')",
                [request_id],
            )
            page.locator("#approval-copy", has_text="已确认（仅演示）").wait_for()
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_identity_roles_approved.png"), full_page=False)
            self.assertEqual(errors, [])
        finally:
            page.close()


if __name__ == "__main__":
    unittest.main()
