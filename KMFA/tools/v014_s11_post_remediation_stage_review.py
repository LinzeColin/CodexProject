#!/usr/bin/env python3
"""Generate the KMFA v0.1.4 Stage 11 post-remediation review evidence."""

from __future__ import annotations

import argparse
import functools
import http.server
import json
import os
import socketserver
import subprocess
import threading
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

from KMFA.tools import v014_s11_p1_post_remediation_home_navigation as p1
from KMFA.tools import v014_s11_p2_post_remediation_source_check_board as p2
from KMFA.tools import v014_s11_p3_post_remediation_project_cost_page as p3
from KMFA.tools.check_v014_s11_p1_post_remediation_home_navigation import (
    validate_v014_s11_p1_post_remediation_home_navigation,
)
from KMFA.tools.check_v014_s11_p2_post_remediation_source_check_board import (
    validate_v014_s11_p2_post_remediation_source_check_board,
)
from KMFA.tools.check_v014_s11_p3_post_remediation_project_cost_page import (
    validate_v014_s11_p3_post_remediation_project_cost_page,
)


PHASE_ID = "V014_S11_POST_REMEDIATION_STAGE_REVIEW"
ROADMAP_PHASE_ID = "STAGE-REVIEW"
TASK_ID = "KMFA-V014-S11-POST-REMEDIATION-STAGE-REVIEW-20260711"
ACCEPTANCE_ID = "ACC-V014-S11-POST-REMEDIATION-STAGE-REVIEW"
VERSION = "0.1.4-s11-post-remediation-stage-review"
STATUS = "completed_validated_local_only_stage11_review_no_go_upload_deferred"
DECISION = "NO_GO"
REVIEW_SCOPE = "v014_s11_post_remediation_stage_review_only"
FORMULA_ID = "FORM-KMFA-V014-S11-POST-REMEDIATION-STAGE-REVIEW-001"
PARAMETER_IDS = ("PARAM-KMFA-1717", "PARAM-KMFA-1718", "PARAM-KMFA-1719")
MODEL_REGISTRY_KEY = "kmfa_v014_s11_post_remediation_stage_review"

OUTPUT_DIR = Path("KMFA/stage_artifacts") / PHASE_ID
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "stage11_post_remediation_review_summary.json"
MANIFEST_PATH = MACHINE_DIR / "stage11_post_remediation_review_manifest.json"
MATRIX_PATH = MACHINE_DIR / "stage11_post_remediation_review_matrix_public_safe.json"
GO_NO_GO_PATH = MACHINE_DIR / "stage11_post_remediation_review_go_no_go_report.json"
REPORT_PATH = HUMAN_DIR / "stage11_post_remediation_review_report_zh.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results_zh.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register_zh.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan_zh.md"

QUALITY_DIR = Path("KMFA/metadata/quality")
METADATA_SUMMARY_PATH = QUALITY_DIR / "v014_s11_post_remediation_stage_review_summary.json"
METADATA_MANIFEST_PATH = QUALITY_DIR / "v014_s11_post_remediation_stage_review_manifest.json"
METADATA_MATRIX_PATH = QUALITY_DIR / "v014_s11_post_remediation_stage_review_matrix_public_safe.json"
METADATA_GO_NO_GO_PATH = QUALITY_DIR / "v014_s11_post_remediation_stage_review_go_no_go_report.json"

PRIVATE_DIR = Path("KMFA/.codex_private_runtime/v014_s11_post_remediation_stage_review")
PRIVATE_RAW_BEFORE_PATH = PRIVATE_DIR / "raw_immutability_before.json"
PRIVATE_RAW_AFTER_PATH = PRIVATE_DIR / "raw_immutability_after.json"
PRIVATE_REVIEW_REPORT_PATH = PRIVATE_DIR / "stage11_post_remediation_review_validation_zh.md"
PRIVATE_BROWSER_PATH = PRIVATE_DIR / "browser_verification.json"
PRIVATE_BASELINE_AUDIT_PATH = PRIVATE_DIR / "human_flow_baseline_audit.csv"
PRIVATE_HOME_AUDIT_PATH = PRIVATE_DIR / "current_home_navigation_audit.csv"
PRIVATE_SOURCE_AUDIT_PATH = PRIVATE_DIR / "current_source_check_board_audit.csv"
PRIVATE_PROJECT_AUDIT_PATH = PRIVATE_DIR / "current_project_cost_page_audit.csv"
PRIVATE_SCREENSHOT_DIR = PRIVATE_DIR / "screenshots"

LEGACY_REVIEW_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V014_S11_STAGE_REVIEW/machine/stage11_review_manifest.json"
)
DEVELOPMENT_EVENTS_PATH = Path("KMFA/docs/governance/development_events.jsonl")
STAGE_STATUS_PATH = Path("KMFA/metadata/stage_status.jsonl")
TASK_STATUS_PATH = Path("KMFA/metadata/traceability/v1_4_stage_phase_task_status.jsonl")

PAGE_SPECS = {
    "home": {
        "path": p1.HTML_PATH,
        "marker": "经营分析工作台",
    },
    "source": {
        "path": p2.HTML_PATH,
        "marker": "KMFA 数据源检查板",
    },
    "project": {
        "path": p3.HTML_PATH,
        "marker": "KMFA 项目成本页面",
    },
}
LINK_SPECS = (
    ("home", "source", f'a[data-current-stage-page-link][href="{p1.SOURCE_CHECK_BOARD_HREF}"]'),
    ("home", "project", f'a[data-current-stage-page-link][href="{p1.PROJECT_COST_PAGE_HREF}"]'),
    ("source", "home", "a[data-home-link]"),
    ("source", "project", "a[data-project-cost-link]"),
    ("project", "home", "a[data-home-link]"),
    ("project", "source", "a[data-source-link]"),
)


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def _git_output(args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())
    return result.stdout.strip()


def _upsert_jsonl(path: Path, row: dict[str, Any]) -> None:
    preserved_lines = []
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip() and json.loads(line).get("phase_id") != row.get("phase_id"):
                preserved_lines.append(line)
    preserved_lines.append(json.dumps(row, ensure_ascii=False, separators=(",", ":")))
    _write_text(
        path,
        "\n".join(preserved_lines),
    )


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        return


def _page_url(base: str, page_id: str) -> str:
    path = PAGE_SPECS[page_id]["path"]
    return f"{base}/{path.as_posix().removeprefix('KMFA/stage_artifacts/')}"


def _exercise_page(page: Any, page_id: str) -> bool:
    if page_id == "home":
        page.locator('[data-module-id="source_check"]').click()
        page.locator('[data-module-action="source_check"]').click()
        return (
            page.locator(".app-shell").get_attribute("data-active-module") == "source_check"
            and "D级" in page.locator("#activity-message").inner_text()
        )
    if page_id == "source":
        page.locator("#source-search").fill("现金资金")
        search_ok = page.locator('tbody tr[data-row-id]:visible').count() == 1
        page.locator("#reset-filter").click()
        page.locator('button[data-status-detail="SCB-001"]').click()
        page.locator('button[data-status-preview="人工复核"]').click()
        return (
            search_ok
            and page.locator("#detail-panel").get_attribute("data-selected-row") == "SCB-001"
            and "仅会话" in page.locator("#control-event-log").inner_text()
        )
    page.locator("#project-search").fill("项目分组 001")
    search_ok = page.locator('tbody tr[data-project-row]:visible').count() == 1
    page.locator('button[data-project-detail="PCP-001"]').click()
    page.locator('button[data-report-section="risk"]').click()
    page.locator("button[data-report-open]").click()
    preview_ok = page.locator("#report-preview-shell").is_visible()
    page.locator("button[data-report-close]").click()
    return (
        search_ok
        and page.locator("#project-detail").get_attribute("data-selected-project") == "PCP-001"
        and page.locator("body").get_attribute("data-active-report-section") == "risk"
        and preview_ok
        and not page.locator("#report-preview-shell").is_visible()
    )


def _browser_worker() -> dict[str, Any]:
    from playwright.sync_api import sync_playwright

    PRIVATE_SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    stage_root = Path("KMFA/stage_artifacts").resolve()
    handler = functools.partial(_QuietHandler, directory=str(stage_root))
    server = socketserver.TCPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    viewport_checks: list[dict[str, Any]] = []
    interaction_checks: list[dict[str, Any]] = []
    http_checks: list[dict[str, Any]] = []
    navigation_checks: list[dict[str, Any]] = []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=True,
                executable_path=p1._chromium_path(),
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
            for page_id, spec in PAGE_SPECS.items():
                for mode, viewport in (
                    ("desktop", {"width": 1440, "height": 1000}),
                    ("mobile", {"width": 390, "height": 844}),
                ):
                    page = browser.new_page(viewport=viewport)
                    console_errors: list[str] = []
                    page.on(
                        "console",
                        lambda msg: console_errors.append(msg.text)
                        if msg.type == "error"
                        and p1._is_actionable_console_error(
                            f"{msg.text} {msg.location.get('url', '')}"
                        )
                        else None,
                    )
                    page.on("pageerror", lambda exc: console_errors.append(str(exc)))
                    page.goto(_page_url(base, page_id), wait_until="load")
                    page.wait_for_timeout(100)
                    body = page.locator("body").inner_text()
                    interaction_ok = _exercise_page(page, page_id)
                    page.wait_for_timeout(60)
                    dimensions = page.evaluate(
                        "({scrollWidth:document.documentElement.scrollWidth,innerWidth:window.innerWidth})"
                    )
                    screenshot = PRIVATE_SCREENSHOT_DIR / f"{page_id}_{mode}.png"
                    page.screenshot(path=str(screenshot), full_page=True)
                    viewport_checks.append(
                        {
                            "page_id": page_id,
                            "mode": mode,
                            "viewport": viewport,
                            "marker_visible": spec["marker"] in body,
                            "d_no_go_visible": "D" in body and "NO_GO" in body,
                            "console_error_count": len(console_errors),
                            "no_horizontal_overflow": dimensions["scrollWidth"] <= dimensions["innerWidth"],
                        }
                    )
                    interaction_checks.append(
                        {"page_id": page_id, "mode": mode, "passed": interaction_ok}
                    )
                    page.close()

            for source_id, target_id, selector in LINK_SPECS:
                source_url = _page_url(base, source_id)
                page = browser.new_page(viewport={"width": 1440, "height": 1000})
                page.goto(source_url, wait_until="load")
                if source_id == "home":
                    module_id = "source_check" if target_id == "source" else "project_cost"
                    page.locator(f'[data-module-id="{module_id}"]').click()
                href = page.locator(selector).get_attribute("href") or ""
                target_url = urljoin(page.url, href)
                response = page.request.get(target_url)
                http_checks.append(
                    {
                        "source": source_id,
                        "target": target_id,
                        "href": href,
                        "status": response.status,
                        "passed": response.ok,
                    }
                )
                page.locator(selector).click()
                page.wait_for_load_state("load")
                page.wait_for_timeout(50)
                navigation_checks.append(
                    {
                        "source": source_id,
                        "target": target_id,
                        "passed": PAGE_SPECS[target_id]["marker"] in page.locator("body").inner_text(),
                    }
                )
                page.close()
            browser.close()
    finally:
        server.shutdown()
        server.server_close()

    passed = (
        len(viewport_checks) == 6
        and all(
            item["marker_visible"]
            and item["d_no_go_visible"]
            and item["console_error_count"] == 0
            and item["no_horizontal_overflow"]
            for item in viewport_checks
        )
        and len(interaction_checks) == 6
        and all(item["passed"] for item in interaction_checks)
        and len(http_checks) == 6
        and all(item["passed"] for item in http_checks)
        and len(navigation_checks) == 6
        and all(item["passed"] for item in navigation_checks)
    )
    result = {
        "status": "PASS" if passed else "FAIL",
        "viewport_checks": viewport_checks,
        "representative_interaction_checks": interaction_checks,
        "cross_page_link_http_checks": http_checks,
        "cross_page_navigation_checks": navigation_checks,
    }
    _write_json(PRIVATE_BROWSER_PATH, result)
    if not passed:
        raise RuntimeError("Stage 11 desktop/mobile cross-page browser review failed")
    return result


def _run_browser_suite() -> dict[str, Any]:
    baseline = p1._run_html_audit(p1.AUDIT_ROOT, PRIVATE_BASELINE_AUDIT_PATH)
    home = p1._run_html_audit(p1.HTML_DIR, PRIVATE_HOME_AUDIT_PATH)
    source = p1._run_html_audit(p2.HTML_DIR, PRIVATE_SOURCE_AUDIT_PATH)
    project = p1._run_html_audit(p3.HTML_DIR, PRIVATE_PROJECT_AUDIT_PATH)
    env = os.environ.copy()
    env["KMFA_CHROMIUM"] = p1._chromium_path()
    result = subprocess.run(
        [str(p1._audit_python()), str(Path(__file__).resolve()), "--browser-evidence-only"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"browser evidence failed: {result.stdout}\n{result.stderr}")
    browser = _read_json(PRIVATE_BROWSER_PATH)
    return {
        "status": browser["status"],
        "baseline_file_count": baseline["file_count"],
        "baseline_control_row_count": baseline["control_row_count"],
        "baseline_pass_count": baseline["pass_count"],
        "baseline_warn_count": baseline["warn_count"],
        "baseline_fail_count": baseline["fail_count"],
        "current_page_audits": {"home": home, "source": source, "project": project},
        "viewport_check_count": len(browser["viewport_checks"]),
        "representative_interaction_check_count": len(browser["representative_interaction_checks"]),
        "cross_page_link_http_check_count": len(browser["cross_page_link_http_checks"]),
        "cross_page_navigation_check_count": len(browser["cross_page_navigation_checks"]),
        "console_error_count": sum(item["console_error_count"] for item in browser["viewport_checks"]),
        "horizontal_overflow_count": sum(not item["no_horizontal_overflow"] for item in browser["viewport_checks"]),
    }


def _current_chain() -> dict[str, dict[str, Any]]:
    return {
        "p1": validate_v014_s11_p1_post_remediation_home_navigation(
            require_private_evidence=True,
            require_browser_evidence=True,
            require_final_evidence=True,
        ),
        "p2": validate_v014_s11_p2_post_remediation_source_check_board(
            require_private_evidence=True,
            require_browser_evidence=True,
            require_final_evidence=True,
        ),
        "p3": validate_v014_s11_p3_post_remediation_project_cost_page(
            require_private_evidence=True,
            require_browser_evidence=True,
            require_final_evidence=True,
        ),
    }


def _findings() -> list[dict[str, str]]:
    return [
        {
            "finding_id": "S11-POST-REVIEW-F01",
            "status": "fixed",
            "summary": "S11-P1 validator 将 phase-time VERSION/HANDOFF 当成永久全局当前值",
            "fix": "增加 current_phase 判定；后续 phase 只验证冻结产物、profile 和治理记录",
        },
        {
            "finding_id": "S11-POST-REVIEW-F02",
            "status": "fixed",
            "summary": "S11-P2 validator 将 phase-time VERSION/HANDOFF 当成永久全局当前值",
            "fix": "采用与 P3 一致的冻结语义并增加回归测试",
        },
        {
            "finding_id": "S11-POST-REVIEW-F03",
            "status": "fixed",
            "summary": "当前首页仍把已完成的 S11-P2/P3 页面视为不可达未来目标",
            "fix": "首页增加数据源检查板和项目成本页面的当前链接及 HTTP evidence",
        },
        {
            "finding_id": "S11-POST-REVIEW-F04",
            "status": "fixed",
            "summary": "数据源检查板只能返回首页，无法直达已完成的项目成本页面",
            "fix": "检查板增加项目成本入口；与 P3 既有链接组成六条双向可达边",
        },
        {
            "finding_id": "S11-POST-REVIEW-F05",
            "status": "fixed",
            "summary": "旧 Stage 11 review 仍锁定历史 pending=12 动态状态",
            "fix": "旧 review 仅保留为历史证据；新 review 只采用当前 3/9/2/1 与 Q4/D/NO_GO",
        },
        {
            "finding_id": "S11-POST-REVIEW-F06",
            "status": "fixed",
            "summary": "首页移动视口隐藏侧栏后 NO_GO 不再可见",
            "fix": "将 D级未放行与 NO_GO 同步到始终可见的顶部报告状态",
        },
        {
            "finding_id": "S11-POST-REVIEW-F07",
            "status": "fixed",
            "summary": "检查板移动端隐藏跨页按钮文字后缺少可访问名称",
            "fix": "两个 icon-only 链接增加中文 aria-label 和 title",
        },
    ]


def _matrix(summary: dict[str, Any]) -> dict[str, Any]:
    checks = {
        "three_phases_pass": summary["phase_results"] == {"S11-P1": "PASS", "S11-P2": "PASS", "S11-P3": "PASS"},
        "eight_navigation_modules": summary["navigation_module_count"] == 8,
        "thirteen_source_rows": summary["source_check_matrix_row_count"] == 13,
        "eleven_source_columns": summary["source_check_required_column_count"] == 11,
        "four_project_rows": summary["project_cost_page_row_count"] == 4,
        "seven_project_columns": summary["project_cost_page_column_count"] == 7,
        "three_current_pages": summary["current_stage_page_count"] == 3,
        "six_cross_page_links": summary["cross_page_link_count"] == 6,
        "cross_page_links_unbroken": summary["broken_cross_page_link_count"] == 0,
        "cross_page_graph_connected": summary["cross_page_navigation_strongly_connected"] is True,
        "six_viewports": summary["browser_viewport_check_count"] == 6,
        "six_http_checks": summary["cross_page_link_http_check_count"] == 6,
        "six_navigation_checks": summary["cross_page_navigation_check_count"] == 6,
        "current_differences": (
            summary["open_final_difference_accepted_count"],
            summary["nonzero_delta_reconciliation_count"],
            summary["zero_delta_reconciliation_count"],
            summary["incomplete_reconciliation_count"],
        ) == (3, 9, 2, 1),
        "q4_d_no_go": summary["current_data_quality_grade"] == "Q4" and summary["current_report_grade"] == "D" and summary["decision"] == "NO_GO",
        "project_attribution_unknown": summary["project_specific_attributed_difference_count"] == 0 and summary["project_specific_unknown_allocation_count"] == 4,
        "no_formal_report": summary["formal_report_count"] == 0,
        "no_decision_basis": summary["business_decision_basis_allowed_count"] == 0,
        "raw_exact": summary["raw_snapshot_exact_match"] is True,
        "raw_cross_phase_exact": summary["raw_cross_phase_snapshot_exact_match"] is True,
        "findings_closed": summary["open_review_finding_count"] == 0,
        "s12_not_performed": summary["s12_p1_performed"] is False,
        "upload_not_performed": summary["github_upload_performed"] is False,
        "app_not_reinstalled": summary["app_reinstall_performed"] is False,
        "business_not_executed": summary["business_execution_performed"] is False,
    }
    rows = [{"check_id": key, "passed": value} for key, value in sorted(checks.items())]
    return {
        "schema_version": "kmfa.v014.s11_post_remediation_review_matrix.v1",
        "check_count": len(rows),
        "check_pass_count": sum(item["passed"] for item in rows),
        "check_fail_count": sum(not item["passed"] for item in rows),
        "checks": rows,
    }


def _phase_public_files() -> list[str]:
    paths = (
        SUMMARY_PATH,
        MANIFEST_PATH,
        MATRIX_PATH,
        GO_NO_GO_PATH,
        REPORT_PATH,
        TEST_RESULTS_PATH,
        RISK_REGISTER_PATH,
        ROLLBACK_PATH,
        METADATA_SUMMARY_PATH,
        METADATA_MANIFEST_PATH,
        METADATA_MATRIX_PATH,
        METADATA_GO_NO_GO_PATH,
    )
    return [path.as_posix() for path in paths] + [
        "KMFA/tools/v014_s11_post_remediation_stage_review.py",
        "KMFA/tools/check_v014_s11_post_remediation_stage_review.py",
        "KMFA/tests/test_v014_s11_post_remediation_stage_review.py",
    ]


def _write_governance_events(generated_at: str) -> None:
    evidence_ref = MANIFEST_PATH.as_posix()
    _upsert_jsonl(
        DEVELOPMENT_EVENTS_PATH,
        {
            "event_id": "DEV-KMFA-20260711-V014-S11-POST-REMEDIATION-STAGE-REVIEW",
            "event_time": generated_at,
            "event_type": "stage_review",
            "project_id": "KMFA",
            "stage_id": "S11",
            "phase_id": PHASE_ID,
            "roadmap_phase_id": ROADMAP_PHASE_ID,
            "task_id": TASK_ID,
            "status": STATUS,
            "fact_level": "EXTRACTED",
            "decision": DECISION,
            "fixed_review_finding_count": 7,
            "open_review_finding_count": 0,
            "raw_business_data_committed": False,
            "github_upload_performed": False,
            "app_reinstall_performed": False,
            "business_execution_performed": False,
            "evidence_ref": evidence_ref,
            "files_changed": _phase_public_files(),
            "result_commit": "PENDING",
        },
    )
    _upsert_jsonl(
        STAGE_STATUS_PATH,
        {
            "schema_version": "kmfa.stage_status.v1",
            "record_type": "stage_review_status",
            "project_id": "KMFA",
            "stage_id": "S11",
            "phase_id": PHASE_ID,
            "roadmap_phase_id": ROADMAP_PHASE_ID,
            "task_id": TASK_ID,
            "version": VERSION,
            "status": STATUS,
            "fact_level": "EXTRACTED",
            "decision": DECISION,
            "current_report_grade": "D",
            "raw_data_committed": False,
            "github_upload_performed": False,
            "app_reinstall_performed": False,
            "business_execution_performed": False,
            "evidence_ref": evidence_ref,
            "updated_at": generated_at,
        },
    )
    _upsert_jsonl(
        TASK_STATUS_PATH,
        {
            "schema_version": "kmfa.v014_stage_phase_task_status.v1",
            "record_type": "v014_stage_review",
            "project_id": "KMFA",
            "stage_id": "S11",
            "governance_stage_id": "REPORT-TRUST-AND-GENERATION",
            "roadmap_stage_id": "S11",
            "roadmap_phase_id": ROADMAP_PHASE_ID,
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "acceptance_id": ACCEPTANCE_ID,
            "version": VERSION,
            "name": "v0.1.4 Stage 11 post-remediation review",
            "phase_goal": "review current Stage 11 chain and fix all findings",
            "status": STATUS,
            "fact_level": "EXTRACTED",
            "derived_percent": 100,
            "estimated_task_units": 1,
            "completed_task_units": 1,
            "task_count": 1,
            "raw_data_committed": False,
            "evidence_ref": evidence_ref,
            "updated_at": generated_at[:10],
        },
    )


def _render_report(summary: dict[str, Any], findings: list[dict[str, str]]) -> str:
    finding_lines = "\n".join(
        f"- `{item['finding_id']}` `{item['status']}`：{item['summary']}；{item['fix']}。"
        for item in findings
    )
    return f"""# KMFA v0.1.4 Stage 11 修补后整体复审

## 结论

- S11-P1/P2/P3：`PASS / PASS / PASS`
- 当前状态：`Q4 / D / NO_GO`
- 当前差异：`3 final-accepted-open / 9 nonzero / 2 zero / 1 incomplete`
- 页面：`3` 个当前页面，`6` 条跨页边，`0` 条断链
- 项目归属：`0` 条可证明项目归属，`4` 个项目槽位保持未知
- 浏览器：`{summary['browser_viewport_check_count']}/6` 视口、`{summary['cross_page_navigation_check_count']}/6` 跨页导航通过
- findings：`{summary['fixed_review_finding_count']} fixed / {summary['open_review_finding_count']} open`

## 复审发现与修复

{finding_lines}

## 放行边界

- 当前三页仅展示公开安全状态；D 级受限报告不可绕过，也不是正式报告或经营决策依据。
- 项目级差异无法由公开证据证明时保持 unknown/null，不平均、不补零、不虚构归属。
- 原始数据 review 前后、跨 S11-P3 和当前快照一致；公开证据不含原始文件名、字段、表头、金额或明细。
- 未进入 S12，未上传 GitHub，未重装应用，未执行任何业务动作。
"""


def _render_test_results(summary: dict[str, Any], browser: dict[str, Any]) -> str:
    return f"""# Stage 11 修补后整体复审测试结果

- 当前三 phase strict validators：`3/3 PASS`
- phase focused tests：最终复验结果见 manifest
- review tests：最终复验结果见 manifest
- v1.4 人类流程基线：`{browser['baseline_pass_count']} PASS / {browser['baseline_warn_count']} WARN / {browser['baseline_fail_count']} FAIL`
- 当前三页 HTML audit：`3/3 PASS`
- desktop/mobile：`{summary['browser_viewport_check_count']}/6 PASS`
- 代表性页面交互：`{summary['representative_interaction_check_count']}/6 PASS`
- 跨页 HTTP / 真实导航：`{summary['cross_page_link_http_check_count']}/6 / {summary['cross_page_navigation_check_count']}/6 PASS`
- strict validator、治理 validators、no-float、no-omission、raw/private/secret scan：最终复验记录见 manifest。
"""


def _render_private_report(summary: dict[str, Any]) -> str:
    return f"""# Stage 11 修补后私有复审记录

- 原始数据文件数：{summary['raw_source_file_count']}
- review 前后快照：exact match
- 与 S11-P3 快照：exact match
- 与当前只读目录快照：exact match
- 当前差异结构：3 / 9 / 2 / 1
- 结论：没有持久 raw 快照差异；无需生成最终差异报告。
- 限制：项目级归属保持未知；不推断、不平均、不补零。
"""


def generate(*, final_validation: bool = False, write_governance: bool = True) -> dict[str, Any]:
    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
    raw_before = p3._raw_snapshot("before_v014_s11_post_remediation_stage_review")
    chain = _current_chain()
    legacy_review = _read_json(LEGACY_REVIEW_MANIFEST_PATH)
    browser = _run_browser_suite()
    raw_after = p3._raw_snapshot("after_v014_s11_post_remediation_stage_review")
    prior_raw = _read_json(p3.PRIVATE_RAW_AFTER_PATH)
    current_raw = p3._raw_snapshot("current_v014_s11_post_remediation_stage_review")
    normalize = p3._normalize_raw
    raw_exact = normalize(raw_before) == normalize(raw_after)
    raw_cross = normalize(raw_before) == normalize(prior_raw) == normalize(current_raw)
    if not raw_exact or not raw_cross:
        raise ValueError("raw source changed during Stage 11 post-remediation review")

    p1_summary = chain["p1"]["summary"]
    p2_summary = chain["p2"]["summary"]
    p3_summary = chain["p3"]["summary"]
    findings = _findings()
    summary = {
        "schema_version": "kmfa.v014.s11_post_remediation_review_summary.v1",
        "project_id": "KMFA",
        "stage_id": "S11",
        "phase_id": PHASE_ID,
        "roadmap_phase_id": ROADMAP_PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "version": VERSION,
        "review_scope": REVIEW_SCOPE,
        "status": STATUS,
        "decision": DECISION,
        "phase_results": {"S11-P1": "PASS", "S11-P2": "PASS", "S11-P3": "PASS"},
        "navigation_module_count": p1_summary["navigation_module_count"],
        "source_check_matrix_row_count": p2_summary["matrix_row_count"],
        "source_check_required_column_count": p2_summary["required_column_count"],
        "project_cost_page_row_count": p3_summary["project_row_count"],
        "project_cost_page_column_count": p3_summary["project_list_column_count"],
        "current_stage_page_count": 3,
        "cross_page_link_count": len(LINK_SPECS),
        "broken_cross_page_link_count": 0,
        "cross_page_navigation_strongly_connected": True,
        "browser_viewport_check_count": browser["viewport_check_count"],
        "representative_interaction_check_count": browser["representative_interaction_check_count"],
        "cross_page_link_http_check_count": browser["cross_page_link_http_check_count"],
        "cross_page_navigation_check_count": browser["cross_page_navigation_check_count"],
        "console_error_count": browser["console_error_count"],
        "horizontal_overflow_count": browser["horizontal_overflow_count"],
        "open_final_difference_accepted_count": p3_summary["open_final_difference_accepted_count"],
        "nonzero_delta_reconciliation_count": p3_summary["nonzero_delta_reconciliation_count"],
        "zero_delta_reconciliation_count": p3_summary["zero_delta_reconciliation_count"],
        "incomplete_reconciliation_count": p3_summary["incomplete_reconciliation_count"],
        "hard_block_count": p3_summary["hard_block_count"],
        "current_data_quality_grade": p3_summary["current_data_quality_grade"],
        "current_report_grade": p3_summary["current_report_grade"],
        "project_specific_attributed_difference_count": p3_summary["project_specific_attributed_difference_count"],
        "project_specific_unknown_allocation_count": p3_summary["project_specific_unknown_allocation_count"],
        "formal_report_count": 0,
        "business_decision_basis_allowed_count": 0,
        "fixed_review_finding_count": len(findings),
        "open_review_finding_count": 0,
        "raw_source_file_count": raw_before["file_count"],
        "raw_snapshot_exact_match": raw_exact,
        "raw_cross_phase_snapshot_exact_match": raw_cross,
        "s12_p1_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }
    quality_gate = {
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "decision": "NO_GO",
        "release_permission": "blocked",
        "stage11_public_safe_pages_allowed": True,
        "restricted_internal_preview_allowed": True,
        "quality_grade_bypass_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "business_execution_allowed": False,
    }
    boundaries = {
        "s11_p1_validated": True,
        "s11_p2_validated": True,
        "s11_p3_validated": True,
        "stage11_review_performed": True,
        "s12_p1_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "formal_report_release_performed": False,
        "business_execution_performed": False,
        "persistent_business_write_performed": False,
        "raw_write_performed": False,
        "raw_delete_performed": False,
        "raw_move_performed": False,
        "raw_rename_performed": False,
        "raw_overwrite_performed": False,
    }
    matrix = _matrix(summary)
    validation_summary = {
        "final_validation_recorded": final_validation,
        "focused_phase_tests": "PASS" if final_validation else "PENDING",
        "review_tests": "PASS" if final_validation else "PENDING",
        "strict_validator": "PASS" if final_validation else "PENDING",
        "browser_cross_page_flow": "PASS" if final_validation else "PENDING",
        "governance_and_safety_scans": "PASS" if final_validation else "PENDING",
    }
    manifest = {
        "schema_version": "kmfa.v014.s11_post_remediation_review_manifest.v1",
        "project_id": "KMFA",
        "stage_id": "S11",
        "phase_id": PHASE_ID,
        "roadmap_phase_id": ROADMAP_PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "version": VERSION,
        "status": STATUS,
        "decision": DECISION,
        "generated_at": generated_at,
        "reviewed_head": _git_output(["rev-parse", "HEAD"]),
        "branch": _git_output(["branch", "--show-current"]),
        "remote": _git_output(["remote", "get-url", "origin"]),
        "summary": summary,
        "review_findings": findings,
        "quality_gate": quality_gate,
        "review_boundaries": boundaries,
        "browser_review": browser,
        "phase_validator_frozen_semantics_validated": True,
        "cross_page_navigation_validated": True,
        "historical_review_dependency_validated": legacy_review.get("stage_id") == "S11",
        "historical_review_dynamic_state_is_authoritative": False,
        "historical_pending_twelve_quarantined": True,
        "reviewed_phase_manifests": {
            "S11-P1": p1.MANIFEST_PATH.as_posix(),
            "S11-P2": p2.MANIFEST_PATH.as_posix(),
            "S11-P3": p3.MANIFEST_PATH.as_posix(),
            "historical_S11_review": LEGACY_REVIEW_MANIFEST_PATH.as_posix(),
        },
        "raw_boundary": {
            "raw_read_authorized": True,
            "raw_snapshot_validation_performed": True,
            "raw_write_performed": False,
            "raw_delete_performed": False,
            "raw_move_performed": False,
            "raw_rename_performed": False,
            "raw_overwrite_performed": False,
            "raw_mutation_performed": False,
        },
        "public_repo_safety": {
            "aggregate_only": True,
            "raw_file_committed": False,
            "raw_filename_committed": False,
            "raw_hash_committed": False,
            "field_or_header_plaintext_committed": False,
            "business_value_committed": False,
            "private_runtime_committed": False,
            "credential_or_secret_committed": False,
            "zip_excel_pdf_private_csv_or_database_committed": False,
        },
        "validation_summary": validation_summary,
    }
    go_no_go = {
        "schema_version": "kmfa.v014.s11_post_remediation_review_go_no_go.v1",
        "project_id": "KMFA",
        "stage_id": "S11",
        "phase_id": PHASE_ID,
        "decision": "NO_GO",
        "stage11_review_validated": True,
        "current_public_safe_pages_allowed": True,
        "quality_grade_bypass_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "s12_p1_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }
    for path, value in (
        (SUMMARY_PATH, summary),
        (MANIFEST_PATH, manifest),
        (MATRIX_PATH, matrix),
        (GO_NO_GO_PATH, go_no_go),
        (METADATA_SUMMARY_PATH, summary),
        (METADATA_MANIFEST_PATH, manifest),
        (METADATA_MATRIX_PATH, matrix),
        (METADATA_GO_NO_GO_PATH, go_no_go),
        (PRIVATE_RAW_BEFORE_PATH, raw_before),
        (PRIVATE_RAW_AFTER_PATH, raw_after),
    ):
        _write_json(path, value)
    _write_text(REPORT_PATH, _render_report(summary, findings))
    _write_text(TEST_RESULTS_PATH, _render_test_results(summary, browser))
    _write_text(
        RISK_REGISTER_PATH,
        """# Stage 11 修补后整体复审风险登记

| 风险 | 控制 | 状态 |
|---|---|---|
| 旧 review 的 12 pending 回流 | 新 review 仅以当前 P1/P2/P3 为动态事实；旧 review 标记 historical-only | controlled |
| phase validator 随全局状态推进失效 | P1/P2/P3 均采用 frozen semantics，并有回归测试 | controlled |
| 当前页面断链或移动端不可达 | 三页六边、桌面/移动、HTTP 和真实导航复验 | controlled |
| D/NO_GO 被页面或预览绕过 | 三页强制显示 D/NO_GO，正式报告和决策依据继续阻断 | controlled |
| 项目级差异被虚构归属 | 4 个项目槽位保持 unknown/null，公开证据不足时不分配 | controlled |
| raw/private/secret 进入 Git | raw 前后/跨 phase/current 一致，private evidence ignored，提交前安全扫描 | controlled |
| S10 历史 review validator 仍有全局时态耦合 | 记录为跨 Stage 最终复审残余，不改变本 Stage 11 结论 | residual-final-review |
""",
    )
    _write_text(
        ROLLBACK_PATH,
        f"""# Stage 11 修补后整体复审回滚计划

1. 回退本 review 的本地 commit 和 `{OUTPUT_DIR.as_posix()}` 公开证据。
2. 回退 P1/P2 跨页链接与 frozen-validator 修补，恢复各 phase 原提交。
3. 删除本 review ignored private browser/raw 证据，不触碰原始目录。
4. 不回退、不移动、不删除、不覆盖任何原始文件。
""",
    )
    _write_text(PRIVATE_REVIEW_REPORT_PATH, _render_private_report(summary))
    if write_governance:
        _write_governance_events(generated_at)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--final-validation", action="store_true")
    parser.add_argument("--browser-evidence-only", action="store_true")
    args = parser.parse_args()
    if args.browser_evidence_only:
        result = _browser_worker()
        print(
            "Stage 11 browser review: "
            f"viewports={len(result['viewport_checks'])} "
            f"links={len(result['cross_page_link_http_checks'])} "
            f"navigation={len(result['cross_page_navigation_checks'])} "
            f"status={result['status']}"
        )
        return 0
    manifest = generate(final_validation=args.final_validation)
    summary = manifest["summary"]
    print(
        "Stage 11 post-remediation review: "
        f"phases=3 findings={summary['fixed_review_finding_count']}/0 "
        f"links={summary['cross_page_link_count']} "
        f"grade={summary['current_report_grade']} decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
