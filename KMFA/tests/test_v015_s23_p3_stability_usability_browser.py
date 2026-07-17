from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import time
import unittest
from pathlib import Path
from typing import Any

from playwright.sync_api import Browser, Page, Playwright, sync_playwright

from KMFA.tools import run_v015_s23_p1_end_to_end_business_flow as runtime


REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_ROOT = REPO_ROOT / "KMFA/stage_artifacts/V015_S23_P3_STABILITY_USABILITY"
SCREENSHOT_ROOT = ARTIFACT_ROOT / "exports/screenshots"
EVIDENCE_PATH = ARTIFACT_ROOT / "machine/browser_acceptance.json"


class StabilityUsabilityBrowserTests(unittest.TestCase):
    playwright: Playwright
    browser: Browser

    @classmethod
    def setUpClass(cls) -> None:
        global ARTIFACT_ROOT, SCREENSHOT_ROOT, EVIDENCE_PATH
        cls.artifact_temp = None
        if os.environ.get("KMFA_PRESERVE_TRACKED_S23P3_BROWSER") == "1":
            cls.artifact_temp = tempfile.TemporaryDirectory(prefix="kmfa-s23p3-browser-")
            ARTIFACT_ROOT = Path(cls.artifact_temp.name)
            SCREENSHOT_ROOT = ARTIFACT_ROOT / "exports/screenshots"
            EVIDENCE_PATH = ARTIFACT_ROOT / "machine/browser_acceptance.json"
        cls.temporary = tempfile.TemporaryDirectory(prefix="kmfa-s23p3-runtime-")
        cls.root = Path(cls.temporary.name)
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
                "KMFA_LOCAL_AUTH_KEY": hashlib.sha256(b"s23p3-browser-auth").hexdigest(),
                "KMFA_SESSION_SIGNING_KEY": hashlib.sha256(b"s23p3-browser-sign").hexdigest(),
            },
        )
        cls.playwright = sync_playwright().start()
        chrome = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
        cls.browser = cls.playwright.chromium.launch(
            headless=True, executable_path=str(chrome) if chrome.is_file() else None
        )
        SCREENSHOT_ROOT.mkdir(parents=True, exist_ok=True)
        EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.browser.close()
        cls.playwright.stop()
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)
        cls.temporary.cleanup()
        if cls.artifact_temp is not None:
            cls.artifact_temp.cleanup()

    def setUp(self) -> None:
        self.page_errors: list[str] = []
        self.external_requests: list[str] = []

    def new_page(self, width: int = 1440, height: int = 1000, *, touch: bool = False) -> Page:
        page = self.browser.new_page(viewport={"width": width, "height": height}, has_touch=touch)
        page.set_default_timeout(15_000)
        page.on("pageerror", lambda error: self.page_errors.append(str(error)))
        page.on(
            "console",
            lambda message: self.page_errors.append(message.text)
            if message.type == "error" and not message.text.startswith("Failed to load resource:")
            else None,
        )
        page.on(
            "request",
            lambda request: self.external_requests.append(request.url)
            if not request.url.startswith(self.base_url + "/")
            else None,
        )
        return page

    @staticmethod
    def screenshot_path(name: str) -> Path:
        return SCREENSHOT_ROOT / name

    @staticmethod
    def elapsed_ms(start_ns: int) -> int:
        return max(1, (time.perf_counter_ns() - start_ns + 999_999) // 1_000_000)

    def wait_home(self, page: Page) -> None:
        page.locator("#homepage-view").wait_for(state="visible")
        page.wait_for_function("() => document.querySelector('#active-role-chip')?.textContent === '经营负责人'")
        page.locator("#homepage-focus .primary-link").first.wait_for()

    @staticmethod
    def plain_language_findings(page: Page) -> list[str]:
        visible_text = page.locator("body").inner_text()
        return sorted(set(re.findall(r"(?i)\b(?:JSON|schema|API|fingerprint|manifest|raw|hash)\b", visible_text)))

    @staticmethod
    def mechanical_findings(page: Page) -> list[str]:
        visible_text = page.locator("main").inner_text()
        return sorted(set(re.findall(r"(?:Lorem ipsum|TODO|AI生成|测试按钮|占位按钮)", visible_text)))

    @staticmethod
    def contrast_sample(page: Page, selector: str, sample_id: str) -> dict[str, Any]:
        return page.locator(selector).first.evaluate(
            r"""(element, value) => {
              const parse = value => {
                const match = value.match(/[\d.]+/g) || [];
                return [Number(match[0] || 0), Number(match[1] || 0), Number(match[2] || 0), Number(match[3] ?? 1)];
              };
              const luminance = color => {
                const values = color.slice(0, 3).map(value => {
                  const normalized = value / 255;
                  return normalized <= .04045 ? normalized / 12.92 : Math.pow((normalized + .055) / 1.055, 2.4);
                });
                return .2126 * values[0] + .7152 * values[1] + .0722 * values[2];
              };
              const style = getComputedStyle(element);
              const foreground = parse(style.color);
              let node = element;
              let background = [255, 255, 255, 1];
              while (node) {
                const candidate = parse(getComputedStyle(node).backgroundColor);
                if (candidate[3] > .99) { background = candidate; break; }
                node = node.parentElement;
              }
              const high = Math.max(luminance(foreground), luminance(background));
              const low = Math.min(luminance(foreground), luminance(background));
              const ratio = (high + .05) / (low + .05);
              const size = parseFloat(style.fontSize);
              const weight = Number(style.fontWeight) || 400;
              const large = size >= 24 || (size >= 18.66 && weight >= 700);
              const threshold = large ? 3 : 4.5;
              return {sample_id:value.sampleId, selector:value.selector, ratio:Number(ratio.toFixed(2)), threshold, status:ratio >= threshold ? 'PASS' : 'FAIL'};
            }""",
            {"sampleId": sample_id, "selector": selector},
        )

    def test_real_role_tasks_and_accessibility_acceptance(self) -> None:
        task_rows: list[dict[str, Any]] = []
        screenshots: list[Path] = []

        # 经营视角：从首页找到当期首要事项并进入处理页面。
        page = self.new_page()
        try:
            started = time.perf_counter_ns()
            page.goto(self.base_url + "/overview", wait_until="networkidle")
            self.wait_home(page)
            primary_target = page.locator("#homepage-focus .primary-link").first
            target_path = primary_target.get_attribute("data-route")
            primary_target.click()
            page.wait_for_url("**/collections**")
            page.locator("#receivables-view").wait_for(state="visible")
            management_assertions = {
                "target_path_exact": target_path == "/collections" and page.url.split("?", 1)[0].endswith("/collections"),
                "business_view_visible": page.locator("#receivables-view").is_visible(),
                "business_title_exact": page.locator("#receivables-title").inner_text() == "先看欠款，再决定内部复核顺序",
            }
            findings = self.plain_language_findings(page)
            mechanical = self.mechanical_findings(page)
            target_failures = [key for key, passed in management_assertions.items() if not passed]
            shot = self.screenshot_path("01_management_task.png")
            page.screenshot(path=str(shot), full_page=True)
            screenshots.append(shot)
            task_rows.append({
                "role_id": "management", "role_label_zh": "经营负责人",
                "task_instruction_zh": "从经营首页找到本期首要事项并进入处理页面。",
                "status": "PASS" if not findings and not mechanical and not target_failures else "FAIL",
                "elapsed_ms": self.elapsed_ms(started), "interaction_count": 1,
                "target_path": target_path, "target_assertions": management_assertions,
                "documentation_open_count": 0, "technical_terms": findings,
                "issues": mechanical + target_failures,
                "issue_count": len(findings) + len(mechanical) + len(target_failures),
            })
        finally:
            page.close()

        # 财务视角：使用可见身份控件切换角色并进入报告入口。
        page = self.new_page()
        try:
            started = time.perf_counter_ns()
            page.goto(self.base_url + "/overview", wait_until="networkidle")
            self.wait_home(page)
            page.locator('[data-nav-id="reports"]').click()
            page.wait_for_url("**/reports**")
            page.locator(".identity-shell").wait_for(state="visible")
            page.locator("#identity-role").select_option("finance")
            page.locator("#role-switch-reason").fill("核对本期报告")
            page.locator("#switch-role").click()
            page.wait_for_function("() => document.querySelector('#active-role-chip')?.textContent === '财务'")
            page.locator("#page-title").wait_for(state="visible")
            page.reload(wait_until="networkidle")
            page.wait_for_function("() => document.querySelector('#active-role-chip')?.textContent === '财务'")
            finance_assertions = {
                "target_path_exact": page.url.split("?", 1)[0].endswith("/reports"),
                "business_view_visible": page.locator("#page-view").is_visible(),
                "business_title_exact": page.locator("#page-title").inner_text() == "报告",
                "role_persisted_after_refresh": page.locator("#active-role-chip").inner_text() == "财务",
            }
            findings = self.plain_language_findings(page)
            mechanical = self.mechanical_findings(page)
            target_failures = [key for key, passed in finance_assertions.items() if not passed]
            shot = self.screenshot_path("02_finance_task.png")
            page.screenshot(path=str(shot), full_page=True)
            screenshots.append(shot)
            task_rows.append({
                "role_id": "finance", "role_label_zh": "财务",
                "task_instruction_zh": "切换到财务角色并进入本期报告入口。",
                "status": "PASS" if not findings and not mechanical and not target_failures else "FAIL",
                "elapsed_ms": self.elapsed_ms(started), "interaction_count": 4,
                "target_path": "/reports", "target_assertions": finance_assertions,
                "documentation_open_count": 0, "technical_terms": findings,
                "issues": mechanical + target_failures,
                "issue_count": len(findings) + len(mechanical) + len(target_failures),
            })
        finally:
            page.close()

        # 税务视角：使用可见身份控件切换角色并进入税务与政策入口。
        page = self.new_page()
        try:
            started = time.perf_counter_ns()
            page.goto(self.base_url + "/overview", wait_until="networkidle")
            self.wait_home(page)
            page.locator('[data-nav-id="reports"]').click()
            page.wait_for_url("**/reports**")
            page.locator(".identity-shell").wait_for(state="visible")
            page.locator("#identity-role").select_option("tax")
            page.locator("#role-switch-reason").fill("核对本期税务事项")
            page.locator("#switch-role").click()
            page.wait_for_function("() => document.querySelector('#active-role-chip')?.textContent === '税务'")
            page.locator('[data-nav-id="tax-policy"]').click()
            page.wait_for_url("**/tax-policy**")
            page.locator("#tax-invoice-view").wait_for(state="visible")
            tax_assertions = {
                "target_path_exact": page.url.split("?", 1)[0].endswith("/tax-policy"),
                "business_view_visible": page.locator("#tax-invoice-view").is_visible(),
                "business_title_exact": page.locator("#tax-invoice-title").inner_text() == "先把税票事实对齐，再看项目税负",
                "active_role_exact": page.locator("#active-role-chip").inner_text() == "税务",
            }
            findings = self.plain_language_findings(page)
            mechanical = self.mechanical_findings(page)
            target_failures = [key for key, passed in tax_assertions.items() if not passed]
            shot = self.screenshot_path("03_tax_task.png")
            page.screenshot(path=str(shot), full_page=True)
            screenshots.append(shot)
            task_rows.append({
                "role_id": "tax", "role_label_zh": "税务",
                "task_instruction_zh": "切换到税务角色并进入本期税务与政策入口。",
                "status": "PASS" if not findings and not mechanical and not target_failures else "FAIL",
                "elapsed_ms": self.elapsed_ms(started), "interaction_count": 5,
                "target_path": "/tax-policy", "target_assertions": tax_assertions,
                "documentation_open_count": 0, "technical_terms": findings,
                "issues": mechanical + target_failures,
                "issue_count": len(findings) + len(mechanical) + len(target_failures),
            })
        finally:
            page.close()

        accessibility_checks: list[dict[str, Any]] = []

        def check(check_id: str, passed: bool, detail: Any) -> None:
            accessibility_checks.append({"check_id": check_id, "status": "PASS" if passed else "FAIL", "detail": detail})

        # 键盘、跳转链接、可见焦点和关键控件标签。
        page = self.new_page()
        try:
            page.goto(self.base_url + "/overview", wait_until="networkidle")
            self.wait_home(page)
            page.keyboard.press("Tab")
            check("keyboard_skip_link_focus", page.evaluate("document.activeElement.classList.contains('skip-link')"), "first Tab")
            page.keyboard.press("Enter")
            check("keyboard_skip_link_target", page.evaluate("document.activeElement.id === 'main-content'"), "main-content")
            report_link = page.locator('[data-nav-id="reports"]')
            report_link.focus()
            outline = report_link.evaluate("e => parseFloat(getComputedStyle(e).outlineWidth)")
            check("visible_focus_outline", outline >= 3, outline)
            shot = self.screenshot_path("04_keyboard_focus.png")
            page.screenshot(path=str(shot), full_page=False)
            screenshots.append(shot)
            page.keyboard.press("Enter")
            page.wait_for_url("**/reports**")
            check("keyboard_navigation_activation", "/reports" in page.url, page.url)

            page.goto(self.base_url + "/reports", wait_until="networkidle")
            page.locator(".identity-shell").wait_for(state="visible")
            # Native select popups are not keyboard-emulated by headless Chromium;
            # set the native option, then verify the remainder of the form by keyboard.
            page.locator("#identity-role").select_option("finance")
            page.locator("#identity-role").focus()
            self.assertEqual(page.locator("#identity-role").input_value(), "finance")
            page.keyboard.press("Tab")
            self.assertEqual(page.evaluate("document.activeElement.id"), "role-switch-reason")
            page.keyboard.press("Meta+A")
            page.keyboard.type("键盘切换财务角色")
            page.keyboard.press("Tab")
            self.assertEqual(page.evaluate("document.activeElement.id"), "switch-role")
            page.keyboard.press("Enter")
            page.wait_for_function("() => document.querySelector('#active-role-chip')?.textContent === '财务'")
            check("keyboard_role_switch", page.locator("#active-role-chip").inner_text() == "财务", "财务")

            for selector in ("#context-company", "#identity-user", "#identity-role", "#role-switch-reason", "#global-search"):
                labelled = page.locator(selector).evaluate(
                    "e => Boolean(e.labels?.length || e.getAttribute('aria-label') || e.getAttribute('aria-labelledby') || e.getAttribute('placeholder'))"
                )
                check("label_" + selector.removeprefix("#").replace("-", "_"), labelled, selector)

            page.goto(self.base_url + "/overview", wait_until="networkidle")
            page.locator("#homepage-view").wait_for(state="visible")
            page.wait_for_function("() => document.querySelector('#active-role-chip')?.textContent === '财务'")

            contrast_selectors = (
                (".brand strong", "brand"), (".homepage-cutoff strong", "cutoff"),
                (".homepage-kicker", "homepage_kicker"), ("#homepage-title", "homepage_title"),
                ("#homepage-summary", "homepage_summary"), ("#homepage-feedback", "homepage_feedback"),
                (".section-heading h2", "section_heading"), (".summary-label", "summary_label"),
                (".summary-value", "summary_value"), (".focus-copy strong", "focus_item"),
            )
            contrast_samples = [self.contrast_sample(page, selector, sample_id) for selector, sample_id in contrast_selectors]
            for row in contrast_samples:
                check("contrast_" + row["sample_id"], row["status"] == "PASS", row["ratio"])
        finally:
            page.close()

        # 200% 缩放后仍可读、可操作，标题与状态区域不重叠。
        page = self.new_page(1440, 900)
        try:
            page.goto(self.base_url + "/overview", wait_until="networkidle")
            self.wait_home(page)
            page.evaluate("document.documentElement.style.zoom='2'")
            title_visible = page.locator("#homepage-title").is_visible()
            action_visible = page.locator("#homepage-focus .primary-link").first.is_visible()
            no_overlap = page.evaluate(
                """() => { const a=document.querySelector('#homepage-title').getBoundingClientRect();
                const b=document.querySelector('#homepage-feedback').getBoundingClientRect(); return a.bottom <= b.top || b.bottom <= a.top; }"""
            )
            check("zoom_200_title_visible", title_visible, title_visible)
            check("zoom_200_action_visible", action_visible, action_visible)
            check("zoom_200_no_overlap", no_overlap, no_overlap)
            shot = self.screenshot_path("05_zoom_200.png")
            page.screenshot(path=str(shot), full_page=True)
            screenshots.append(shot)
        finally:
            page.close()

        narrow_results: list[dict[str, Any]] = []
        for width, height in ((390, 844), (320, 700)):
            page = self.new_page(width, height, touch=True)
            try:
                page.goto(self.base_url + "/overview", wait_until="networkidle")
                self.wait_home(page)
                overflow_free = page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1")
                touch_heights = page.locator(
                    '#primary-nav a,#context-form select,#switch-role,#homepage-focus .primary-link'
                ).evaluate_all(
                    "nodes => nodes.filter(node => node.offsetParent !== null).map(node => Math.round(node.getBoundingClientRect().height))"
                )
                touch_pass = bool(touch_heights) and min(touch_heights) >= 44
                narrow_results.append({"width": width, "height": height, "overflow_free": overflow_free, "minimum_touch_height": min(touch_heights) if touch_heights else 0})
                check(f"narrow_{width}_no_overflow", overflow_free, width)
                check(f"narrow_{width}_touch_targets", touch_pass, min(touch_heights) if touch_heights else 0)
                if width == 320:
                    shot = self.screenshot_path("06_narrow_320.png")
                    page.screenshot(path=str(shot), full_page=True)
                    screenshots.append(shot)
            finally:
                page.close()

        # 打印视图只保留业务内容；状态同时有文本/符号或边框，不只靠颜色。
        page = self.new_page()
        try:
            page.goto(self.base_url + "/overview", wait_until="networkidle")
            self.wait_home(page)
            page.emulate_media(media="print")
            print_title = page.locator("#homepage-title").is_visible()
            print_nav_hidden = page.locator(".topbar").evaluate("e => getComputedStyle(e).display === 'none'")
            print_tools_hidden = all(
                page.locator(selector).evaluate("e => getComputedStyle(e).display === 'none'")
                for selector in (".context-shell", ".identity-shell", ".quick-shell", "#access-workspace", "#experience-workspace")
            )
            check("print_business_content", print_title, print_title)
            check("print_navigation_hidden", print_nav_hidden, print_nav_hidden)
            check("print_tools_hidden", print_tools_hidden, print_tools_hidden)
            status_evidence = page.evaluate(
                """() => {
                  const statuses=[...document.querySelectorAll('.status-text')].filter(e=>e.offsetParent!==null);
                  const statusFailures=statuses.filter(e=>!e.textContent.trim() || ['none','normal',''].includes(getComputedStyle(e,'::before').content.replaceAll('"',''))).length;
                  const feedback=document.querySelector('#homepage-feedback');
                  return {status_count:statuses.length,status_failure_count:statusFailures,feedback_text:Boolean(feedback.textContent.trim()),feedback_border:parseFloat(getComputedStyle(feedback).borderLeftWidth)>0};
                }"""
            )
            check("status_text_present", status_evidence["status_count"] > 0 and status_evidence["status_failure_count"] == 0, status_evidence)
            check("feedback_not_color_only", status_evidence["feedback_text"] and status_evidence["feedback_border"], status_evidence)
            shot = self.screenshot_path("07_print_view.png")
            page.screenshot(path=str(shot), full_page=True)
            screenshots.append(shot)
        finally:
            page.close()

        check("page_errors_zero", not self.page_errors, list(self.page_errors))
        check("external_network_zero", not self.external_requests, list(self.external_requests))

        contrast_failures = [row for row in contrast_samples if row["status"] != "PASS"]
        check_failures = [row for row in accessibility_checks if row["status"] != "PASS"]
        issue_count = sum(row["issue_count"] for row in task_rows)
        total_elapsed_ms = sum(row["elapsed_ms"] for row in task_rows)
        usability_pass = all(row["status"] == "PASS" and row["elapsed_ms"] <= 15_000 for row in task_rows)
        accessibility_pass = not check_failures and len(accessibility_checks) >= 24
        screenshot_paths = [
            path.relative_to(REPO_ROOT).as_posix() if path.is_relative_to(REPO_ROOT) else path.as_posix()
            for path in screenshots
        ]
        evidence = {
            "schema_version": "kmfa.v015.s23p3.browser_acceptance.v1",
            "status": "PASS" if usability_pass and accessibility_pass else "FAIL",
            "browser": "Chromium headless",
            "observer_type": "AUTOMATED_ROLE_TASK_SIMULATION",
            "usability": {
                "status": "PASS" if usability_pass else "FAIL",
                "task_count": len(task_rows), "completed_task_count": sum(row["status"] == "PASS" for row in task_rows),
                "completion_rate_bps": sum(row["status"] == "PASS" for row in task_rows) * 10_000 // len(task_rows),
                "total_elapsed_ms": total_elapsed_ms, "total_elapsed_budget_ms": 30_000,
                "max_interaction_count": max(row["interaction_count"] for row in task_rows), "max_interaction_budget": 8,
                "business_target_assertion_count": sum(len(row["target_assertions"]) for row in task_rows),
                "business_target_assertion_fail_count": sum(
                    not passed
                    for row in task_rows
                    for passed in row["target_assertions"].values()
                ),
                "role_persistence_check_count": sum(
                    "role_persisted_after_refresh" in row["target_assertions"]
                    for row in task_rows
                ),
                "technical_document_dependency_count": sum(row["documentation_open_count"] for row in task_rows),
                "technical_term_exposure_count": sum(len(row["technical_terms"]) for row in task_rows),
                "mechanical_ai_issue_count": sum(len(row["issues"]) for row in task_rows),
                "issue_count": issue_count, "tasks": task_rows,
            },
            "accessibility": {
                "status": "PASS" if accessibility_pass else "FAIL",
                "check_count": len(accessibility_checks), "pass_count": len(accessibility_checks) - len(check_failures),
                "fail_count": len(check_failures), "checks": accessibility_checks,
                "keyboard_flow_count": 3,
                "visible_focus_pass_count": int(next(row for row in accessibility_checks if row["check_id"] == "visible_focus_outline")["status"] == "PASS"),
                "skip_link_pass_count": int(all(next(row for row in accessibility_checks if row["check_id"] == check_id)["status"] == "PASS" for check_id in ("keyboard_skip_link_focus", "keyboard_skip_link_target"))),
                "missing_label_count": sum(row["status"] != "PASS" for row in accessibility_checks if row["check_id"].startswith("label_")),
                "contrast_sample_count": len(contrast_samples), "contrast_fail_count": len(contrast_failures), "contrast_samples": contrast_samples,
                "zoom_200_pass_count": int(all(next(row for row in accessibility_checks if row["check_id"] == check_id)["status"] == "PASS" for check_id in ("zoom_200_title_visible", "zoom_200_action_visible", "zoom_200_no_overlap"))),
                "narrow_viewport_count": len(narrow_results),
                "narrow_overflow_count": sum(not row["overflow_free"] for row in narrow_results),
                "print_pass_count": int(print_title and print_tools_hidden),
                "print_navigation_hidden_count": int(print_nav_hidden),
                "color_only_critical_info_count": int(status_evidence["status_failure_count"] > 0 or not status_evidence["feedback_text"] or not status_evidence["feedback_border"]),
                "touch_target_fail_count": sum(row["minimum_touch_height"] < 44 for row in narrow_results),
                "page_error_count": len(self.page_errors), "external_network_request_count": len(self.external_requests),
                "narrow_viewports": narrow_results,
            },
            "screenshot_paths": screenshot_paths,
        }
        EVIDENCE_PATH.write_text(json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        self.assertEqual(task_rows, [row for row in task_rows if row["status"] == "PASS"])
        self.assertEqual(check_failures, [], json.dumps(check_failures, ensure_ascii=False))
        self.assertEqual(evidence["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
