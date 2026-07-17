from __future__ import annotations

import hashlib
import os
import tempfile
import unittest
from pathlib import Path

from playwright.sync_api import Browser, Page, Playwright, sync_playwright

from KMFA.tools import run_v015_s23_p1_end_to_end_business_flow as runtime
from KMFA.tools import v015_s23_p1_end_to_end_business_flow as kernel


REPO_ROOT = Path(__file__).resolve().parents[2]
SCREENSHOT_ROOT = REPO_ROOT / "KMFA/stage_artifacts/V015_S23_P1_END_TO_END_BUSINESS_FLOW/exports/screenshots"


class EndToEndBusinessFlowBrowserTests(unittest.TestCase):
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
        cls.sample = cls.root / "public-project-cost.csv"
        cls.sample.write_text("project,cost\n示例厂房改造,420000\n", encoding="utf-8")
        cls.server, cls.thread, cls.base_url = runtime.start_server(
            event_path=cls.root / "base.jsonl",
            data_root=cls.root / "data",
            confirmation_event_path=cls.root / "confirmations.jsonl",
            publication_event_path=cls.root / "publications.jsonl",
            report_model_event_path=cls.root / "models.jsonl",
            export_event_path=cls.root / "exports.jsonl",
            export_bundle_root=cls.root / "bundles",
            workflow_event_path=cls.root / "workflows.jsonl",
            notification_event_path=cls.root / "notifications.jsonl",
            audit_event_path=cls.root / "audit.jsonl",
            operations_root=cls.root / "operations",
            xlsx_preview_root=cls.root / "xlsx-previews",
            secret_values={
                "KMFA_LOCAL_AUTH_KEY": hashlib.sha256(b"s23p1-browser-auth").hexdigest(),
                "KMFA_SESSION_SIGNING_KEY": hashlib.sha256(b"s23p1-browser-sign").hexdigest(),
            },
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

    def page(self, width: int = 1440, height: int = 1000) -> tuple[Page, list[str]]:
        page = self.browser.new_page(viewport={"width": width, "height": height})
        page.set_default_timeout(60_000)
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
    def complete_workflow(page: Page) -> None:
        page.locator("#rw-preview").click()
        page.wait_for_function("() => window.KMFA_REPORT_WORKFLOW_TEST.snapshot()?.current?.state === 'PREVIEWED'")
        for selector, state in (
            ("#rw-submit", "IN_REVIEW"),
            ("#rw-review-pass", "REVIEWED"),
            ("#rw-approve", "APPROVED"),
            ("#rw-publish", "PUBLISHED_INTERNAL"),
        ):
            page.locator(selector).click()
            page.wait_for_function(f"() => window.KMFA_REPORT_WORKFLOW_TEST.snapshot()?.current?.state === '{state}'")

    def test_complete_real_browser_flow_has_zero_difference_and_survives_refresh(self) -> None:
        page, errors = self.page()
        mobile = None
        try:
            page.goto(self.base_url + "/overview", wait_until="networkidle")
            page.wait_for_function("() => window.KMFA_HOMEPAGE_TEST?.snapshot()?.publication_version_id === 'PUB-S20P3-0001'")
            home_before = page.evaluate("window.KMFA_HOMEPAGE_TEST.snapshot()")
            self.assertEqual(home_before["summary_metrics"][2]["primary_value"], 32_000_000)
            page.screenshot(path=str(SCREENSHOT_ROOT / "01_homepage_authoritative_before.png"), full_page=True)
            project_link = page.locator('#homepage-focus a[data-route="/data-update"]').first
            self.assertTrue(project_link.is_visible())
            project_link.click()
            page.locator("#data-update-view").wait_for(state="visible")

            page.locator("#du-source").select_option("SRC-local-upload-a1b2c3d4")
            page.locator("#du-entity").select_option("demo-north")
            page.locator("#du-scope").select_option("SEGMENT::PROJECT_COST")
            page.locator("#du-period").fill("2026-07")
            page.locator("#du-file").set_input_files(str(self.sample))
            page.locator("#du-upload").click()
            page.locator("#du-preview-panel").wait_for(state="visible")
            page.wait_for_function("() => window.KMFA_DATA_UPDATE_TEST.snapshot()?.status === 'AWAITING_CONFIRMATION'")
            page.locator("#du-confirm").click()
            page.wait_for_function("() => window.KMFA_DATA_UPDATE_TEST.snapshot()?.status === 'COMPLETED'")
            page.screenshot(path=str(SCREENSHOT_ROOT / "02_project_cost_imported.png"), full_page=True)

            page.goto(self.base_url + "/confirmation-workbench", wait_until="networkidle")
            page.wait_for_function("() => window.KMFA_CONFIRMATION_TEST?.snapshot()?.list?.issue_count === 5")
            page.locator('.cw-issue[data-issue-id="ISSUE-S20P2-001"]').click()
            page.locator('input[name="cw-action"][value="USE_REGISTERED_PROJECT"]').check()
            page.locator("#cw-preview").click()
            page.locator("#cw-preview-card").wait_for(state="visible")
            page.locator("#cw-confirm").click()
            page.wait_for_function("() => window.KMFA_CONFIRMATION_TEST.snapshot()?.history?.event_count === 1")
            page.screenshot(path=str(SCREENSHOT_ROOT / "03_project_difference_confirmed.png"), full_page=True)

            page.goto(self.base_url + "/recalculation-publication", wait_until="networkidle")
            page.wait_for_function("() => window.KMFA_RECALCULATION_TEST?.snapshot()?.eligible?.eligible_count === 1")
            page.locator("#rp-start").click()
            page.locator("#rp-comparison-card").wait_for(state="visible")
            page.locator("#rp-preview").click()
            page.wait_for_function("() => !!window.KMFA_RECALCULATION_TEST.snapshot()?.preview")
            page.locator("#rp-confirm").click()
            page.wait_for_function("() => window.KMFA_RECALCULATION_TEST.snapshot()?.current?.publication_version_id === 'PUB-S20P3-0002'")
            recalc = page.evaluate("window.KMFA_RECALCULATION_TEST.snapshot()")
            self.assertEqual(len({row["publication_version_id"] for row in recalc["views"].values()}), 1)
            self.assertEqual(len({row["shared_metric_fingerprint"] for row in recalc["views"].values()}), 1)
            page.screenshot(path=str(SCREENSHOT_ROOT / "04_recalculated_four_views.png"), full_page=True)

            page.goto(self.base_url + "/overview", wait_until="networkidle")
            page.wait_for_function("() => window.KMFA_HOMEPAGE_TEST?.snapshot()?.publication_version_id === 'PUB-S20P3-0002'")
            home_after = page.evaluate("window.KMFA_HOMEPAGE_TEST.snapshot()")
            project_metric = next(row for row in home_after["summary_metrics"] if row["metric_id"] == "PROJECT_GROSS_PROFIT")
            self.assertEqual(project_metric["primary_value"], 35_700_000)
            self.assertEqual(project_metric["source_ref"], "PUB-S20P3-0002:project_margin_cents")

            page.goto(self.base_url + "/report-model", wait_until="networkidle")
            page.wait_for_function("() => !!window.KMFA_REPORT_MODEL_TEST")
            page.locator("#rm-create-form button[type=submit]").click()
            page.wait_for_function("() => window.KMFA_REPORT_MODEL_TEST.snapshot()?.list?.report_version_count === 1")
            first_report_id = page.evaluate("window.KMFA_REPORT_MODEL_TEST.snapshot().current.report_version_id")
            self.assertEqual(
                next(row for row in self.server.report_model_journal.get(first_report_id)["source_bindings"] if row["domain_id"] == "published_metrics")["version_ref"],
                "PUB-S20P3-0002",
            )

            page.goto(self.base_url + "/report-generation", wait_until="networkidle")
            page.wait_for_function("() => window.KMFA_REPORT_GENERATION_TEST?.snapshot()?.reports?.report_version_count === 1")
            page.locator("#rg-create-form button[type=submit]").click()
            page.wait_for_function("() => window.KMFA_REPORT_GENERATION_TEST.snapshot()?.exports?.export_count === 1")
            first_export = self.server.report_export_journal.list()["exports"][0]
            self.assertEqual(set(first_export["files"]), set(kernel.FORMATS))
            self.assertEqual(first_export["cross_format_consistency"]["difference_integer"], 0)

            page.goto(self.base_url + "/report-workflow", wait_until="networkidle")
            page.wait_for_function("() => window.KMFA_REPORT_WORKFLOW_TEST?.snapshot()?.reports?.report_version_count === 1")
            self.complete_workflow(page)
            page.screenshot(path=str(SCREENSHOT_ROOT / "05_report_approved_four_formats.png"), full_page=True)

            page.goto(self.base_url + "/end-to-end", wait_until="networkidle")
            page.wait_for_function("() => window.KMFA_END_TO_END_TEST?.snapshot()?.status === 'PASS'")
            first_status = page.evaluate("window.KMFA_END_TO_END_TEST.snapshot()")
            self.assertEqual((first_status["format_count"], first_status["difference_cents"]), (4, 0))
            self.assertEqual(page.locator("#e2e-downloads a").count(), 4)

            headers = {"X-KMFA-User": "demo-owner", "X-KMFA-Role": "management", "X-KMFA-Company": "demo-north"}
            downloaded = {}
            for suffix in ("html", "pdf", "appendix.csv", "report.xlsx"):
                response = page.request.get(
                    f"{self.base_url}/api/report-exports/{first_status['export_id']}/{suffix}", headers=headers
                )
                self.assertTrue(response.ok)
                downloaded[suffix] = response.body()
            self.assertTrue(downloaded["html"].startswith(b"<!doctype html>"))
            self.assertTrue(downloaded["pdf"].startswith(b"%PDF"))
            self.assertIn(b"report_version_id", downloaded["appendix.csv"])
            self.assertTrue(downloaded["report.xlsx"].startswith(b"PK"))

            page.goto(self.base_url + "/report-workflow", wait_until="networkidle")
            page.wait_for_function("() => window.KMFA_REPORT_WORKFLOW_TEST?.snapshot()?.current?.state === 'PUBLISHED_INTERNAL'")
            page.locator("#rw-revise").click()
            page.wait_for_function("() => window.KMFA_REPORT_WORKFLOW_TEST.snapshot()?.reports?.report_version_count === 2")
            comparison = page.evaluate("window.KMFA_REPORT_WORKFLOW_TEST.snapshot().comparison")
            self.assertGreaterEqual(comparison["source_difference_count"], 1)
            self.assertEqual(comparison["unexplained_difference_count"], 0)
            self.complete_workflow(page)
            page.screenshot(path=str(SCREENSHOT_ROOT / "06_revision_retains_history.png"), full_page=True)

            page.goto(self.base_url + "/end-to-end", wait_until="networkidle")
            page.wait_for_function("() => window.KMFA_END_TO_END_TEST?.snapshot()?.status === 'PASS'")
            final_status = page.evaluate("window.KMFA_END_TO_END_TEST.snapshot()")
            self.assertNotEqual(final_status["report_version_id"], first_report_id)
            self.assertEqual((final_status["format_count"], final_status["difference_cents"]), (4, 0))
            page.reload(wait_until="networkidle")
            page.wait_for_function("() => window.KMFA_END_TO_END_TEST?.snapshot()?.status === 'PASS'")
            refreshed = page.evaluate("window.KMFA_END_TO_END_TEST.snapshot()")
            self.assertEqual(refreshed["publication_version_id"], "PUB-S20P3-0002")
            self.assertEqual(refreshed["report_version_id"], final_status["report_version_id"])
            page.screenshot(path=str(SCREENSHOT_ROOT / "07_end_to_end_pass.png"), full_page=True)

            mobile, mobile_errors = self.page(390, 844)
            mobile.goto(self.base_url + "/end-to-end", wait_until="networkidle")
            mobile.wait_for_function("() => window.KMFA_END_TO_END_TEST?.snapshot()?.status === 'PASS'")
            self.assertTrue(mobile.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1"))
            self.assertTrue(all(value >= 44 for value in mobile.locator("#end-to-end-view a,#end-to-end-view button").evaluate_all("nodes => nodes.filter(n=>n.offsetParent!==null).map(n=>Math.round(n.getBoundingClientRect().height))")))
            mobile.screenshot(path=str(SCREENSHOT_ROOT / "08_end_to_end_mobile.png"), full_page=True)
            self.assertEqual(mobile_errors, [])
            self.assertEqual(errors, [])
        finally:
            if mobile is not None:
                mobile.close()
            page.close()


if __name__ == "__main__":
    unittest.main()
