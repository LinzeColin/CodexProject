from __future__ import annotations

import unittest
from pathlib import Path

from playwright.sync_api import Browser, Page, Playwright, sync_playwright

from KMFA.tools import run_v015_s16_p2_drilldown_explanation as runtime


REPO_ROOT = Path(__file__).resolve().parents[2]
SCREENSHOT_ROOT = REPO_ROOT / "KMFA/stage_artifacts/V015_S16_P2_DRILLDOWN_EXPLANATION/exports/screenshots"


class DrilldownBrowserTests(unittest.TestCase):
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
        page.set_default_timeout(10_000)
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on(
            "console",
            lambda message: errors.append(message.text)
            if message.type == "error" and not message.text.startswith("Failed to load resource:")
            else None,
        )
        return page, errors

    def wait_home(self, page: Page) -> None:
        page.locator("#homepage-view").wait_for(state="visible")
        page.locator("#homepage-metrics .summary-item").nth(4).wait_for()
        page.locator("#homepage-feedback", has_text="资料已核对").wait_for()

    def wait_detail(self, page: Page) -> None:
        page.locator("#drilldown-view").wait_for(state="visible")
        page.wait_for_function("() => Boolean(window.KMFA_DRILLDOWN_TEST?.snapshot())")
        page.locator("#drilldown-feedback", has_text="已核对").wait_for()

    def test_01_homepage_number_opens_matching_funds_detail(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/overview", wait_until="networkidle")
            self.wait_home(page)
            homepage_value = page.locator('[data-metric-id="AVAILABLE_CASH"] .summary-value').inner_text()
            page.locator('[data-metric-id="AVAILABLE_CASH"] .summary-link').click()
            page.wait_for_url("**/overview/detail/available-cash?**")
            self.wait_detail(page)
            self.assertEqual(page.locator("#drilldown-value").inner_text(), homepage_value)
            self.assertEqual(page.locator("#drilldown-body tr").count(), 3)
            self.assertIn("明细合计与首页数字一致", page.locator("#drilldown-feedback").inner_text())
            SCREENSHOT_ROOT.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_drilldown_funds.png"), full_page=False)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_02_company_period_status_and_version_survive_drilldown(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(
                self.base_url + "/overview?company=demo-west&period=2026-H1&project_status=normal&report_version=approved",
                wait_until="networkidle",
            )
            self.wait_home(page)
            page.locator('[data-metric-id="PROJECT_GROSS_PROFIT"] .summary-link').click()
            page.wait_for_url("**/overview/detail/project-gross-profit?**")
            self.wait_detail(page)
            snapshot = page.evaluate("window.KMFA_DRILLDOWN_TEST.snapshot()")
            self.assertEqual(
                {key: snapshot["context"][key] for key in ("company", "period", "project_status", "report_version")},
                {
                    "company": "demo-west",
                    "period": "2026-H1",
                    "project_status": "normal",
                    "report_version": "approved",
                },
            )
            self.assertIn("西区示例公司", page.locator("#drilldown-context").inner_text())
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_03_plain_explanation_is_default_and_professional_lineage_is_optional(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/overview/detail/project-gross-profit", wait_until="networkidle")
            self.wait_detail(page)
            self.assertTrue(page.locator("#drilldown-short-explanation").inner_text().strip())
            self.assertFalse(page.locator("#professional-evidence").evaluate("node => node.open"))
            page.locator("#professional-evidence summary").click()
            self.assertEqual(page.locator("#lineage-list .lineage-row").count(), 4)
            self.assertNotIn("技术日志", page.locator("#drilldown-view").inner_text())
            SCREENSHOT_ROOT.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_drilldown_professional.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_04_three_comparisons_work_and_mismatched_basis_is_blocked(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/overview/detail/available-cash", wait_until="networkidle")
            self.wait_detail(page)
            for kind in ("MOM", "YOY", "BASELINE"):
                page.evaluate("kind => window.KMFA_DRILLDOWN_TEST.setComparisonKind(kind)", kind)
                page.wait_for_function(
                    "kind => window.KMFA_DRILLDOWN_TEST.snapshot()?.comparison.comparison_kind === kind",
                    arg=kind,
                )
                self.assertTrue(page.evaluate("window.KMFA_DRILLDOWN_TEST.snapshot().comparison.comparison_allowed"))
            page.evaluate("window.KMFA_DRILLDOWN_TEST.setComparisonState('basis_mismatch')")
            page.wait_for_function("() => window.KMFA_DRILLDOWN_TEST.snapshot()?.comparison.comparison_allowed === false")
            self.assertIn("口径不同", page.locator("#comparison-feedback").inner_text())
            self.assertEqual(page.locator("#comparison-delta").inner_text(), "不可比较")
            SCREENSHOT_ROOT.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_drilldown_comparison_blocked.png"), full_page=False)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_05_missing_data_or_source_never_creates_unsupported_detail(self) -> None:
        page, errors = self.new_page()
        try:
            page.goto(self.base_url + "/overview/detail/overdue-receivable", wait_until="networkidle")
            self.wait_detail(page)
            page.evaluate("window.KMFA_DRILLDOWN_TEST.setDataState('partial')")
            page.wait_for_function("() => window.KMFA_DRILLDOWN_TEST.snapshot()?.detail_available === false")
            self.assertEqual(page.locator("#drilldown-body tr").count(), 0)
            self.assertTrue(page.locator("#drilldown-empty").is_visible())
            self.assertEqual(page.locator("#comparison-delta").inner_text(), "不可比较")
            page.evaluate("window.KMFA_DRILLDOWN_TEST.setDataState('complete')")
            page.evaluate("window.KMFA_DRILLDOWN_TEST.setLineageState('missing')")
            page.wait_for_function("() => window.KMFA_DRILLDOWN_TEST.snapshot()?.explanation.lineage_complete === false")
            self.assertIn("来源链不完整", page.locator("#drilldown-empty").inner_text())
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_06_all_five_detail_routes_are_live_and_return_home(self) -> None:
        page, errors = self.new_page()
        try:
            expected = {
                "available-cash": 3,
                "expected-flow": 3,
                "project-gross-profit": 4,
                "overdue-receivable": 3,
                "confirmations": 4,
            }
            for slug, row_count in expected.items():
                page.goto(self.base_url + "/overview/detail/" + slug, wait_until="networkidle")
                self.wait_detail(page)
                self.assertEqual(page.locator("#drilldown-body tr").count(), row_count)
            page.locator("#drilldown-back").click()
            page.wait_for_url("**/overview?**")
            self.wait_home(page)
            self.assertEqual(errors, [])
        finally:
            page.close()

    def test_07_mobile_detail_has_no_horizontal_overflow_and_touchable_controls(self) -> None:
        page, errors = self.new_page(390, 844)
        try:
            page.goto(self.base_url + "/overview/detail/expected-flow", wait_until="networkidle")
            self.wait_detail(page)
            self.assertTrue(page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1"))
            self.assertGreaterEqual(page.locator("#drilldown-back").evaluate("node => node.getBoundingClientRect().height"), 44)
            self.assertGreaterEqual(page.locator("#comparison-kind").evaluate("node => node.getBoundingClientRect().height"), 44)
            page.locator("#professional-evidence summary").scroll_into_view_if_needed()
            self.assertTrue(page.locator("#professional-evidence summary").is_visible())
            SCREENSHOT_ROOT.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(SCREENSHOT_ROOT / "kmfa_drilldown_mobile.png"), full_page=True)
            self.assertEqual(errors, [])
        finally:
            page.close()


if __name__ == "__main__":
    unittest.main()
