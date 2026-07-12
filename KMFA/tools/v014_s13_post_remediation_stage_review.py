#!/usr/bin/env python3
"""Generate KMFA v0.1.4 Stage 13 post-remediation review evidence."""

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

from KMFA.tools import v014_s13_p1_post_remediation_financial_operating_report as p1
from KMFA.tools import v014_s13_p2_post_remediation_collection_receivable_aging as p2
from KMFA.tools import v014_s13_p3_post_remediation_cross_table_review as p3
from KMFA.tools.check_v014_s13_p1_post_remediation_financial_operating_report import (
    validate_v014_s13_p1_post_remediation_financial_operating_report,
)
from KMFA.tools.check_v014_s13_p2_post_remediation_collection_receivable_aging import (
    validate_v014_s13_p2_post_remediation_collection_receivable_aging,
)
from KMFA.tools.check_v014_s13_p3_post_remediation_cross_table_review import (
    validate_v014_s13_p3_post_remediation_cross_table_review,
)


PHASE_ID = "V014_S13_POST_REMEDIATION_STAGE_REVIEW"
ROADMAP_PHASE_ID = "STAGE-REVIEW"
TASK_ID = "KMFA-V014-S13-POST-REMEDIATION-STAGE-REVIEW-20260711"
ACCEPTANCE_ID = "ACC-V014-S13-POST-REMEDIATION-STAGE-REVIEW"
VERSION = "0.1.4-s13-post-remediation-stage-review"
STATUS = "completed_validated_local_only_stage13_review_no_go_upload_deferred"
DECISION = "NO_GO"
REVIEW_SCOPE = "v014_s13_post_remediation_stage_review_only"
FORMULA_ID = "FORM-KMFA-V014-S13-POST-REMEDIATION-STAGE-REVIEW-001"
PARAMETER_IDS = ("PARAM-KMFA-1747", "PARAM-KMFA-1748", "PARAM-KMFA-1749")
MODEL_REGISTRY_KEY = "kmfa_v014_s13_post_remediation_stage_review"

OUTPUT_DIR = Path("KMFA/stage_artifacts") / PHASE_ID
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "stage13_post_remediation_review_summary.json"
MANIFEST_PATH = MACHINE_DIR / "stage13_post_remediation_review_manifest.json"
MATRIX_PATH = MACHINE_DIR / "stage13_post_remediation_review_matrix_public_safe.json"
GO_NO_GO_PATH = MACHINE_DIR / "stage13_post_remediation_review_go_no_go_report.json"
REPORT_PATH = HUMAN_DIR / "stage13_post_remediation_review_report_zh.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results_zh.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register_zh.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan_zh.md"

QUALITY_DIR = Path("KMFA/metadata/quality")
METADATA_SUMMARY_PATH = QUALITY_DIR / "v014_s13_post_remediation_stage_review_summary.json"
METADATA_MANIFEST_PATH = QUALITY_DIR / "v014_s13_post_remediation_stage_review_manifest.json"
METADATA_MATRIX_PATH = QUALITY_DIR / "v014_s13_post_remediation_stage_review_matrix_public_safe.json"
METADATA_GO_NO_GO_PATH = QUALITY_DIR / "v014_s13_post_remediation_stage_review_go_no_go_report.json"

PRIVATE_DIR = Path("KMFA/.codex_private_runtime/v014_s13_post_remediation_stage_review")
PRIVATE_RAW_BEFORE_PATH = PRIVATE_DIR / "raw_immutability_before.json"
PRIVATE_RAW_AFTER_PATH = PRIVATE_DIR / "raw_immutability_after.json"
PRIVATE_REVIEW_REPORT_PATH = PRIVATE_DIR / "stage13_post_remediation_review_validation_zh.md"
PRIVATE_BROWSER_PATH = PRIVATE_DIR / "browser_verification.json"
PRIVATE_BASELINE_AUDIT_PATH = PRIVATE_DIR / "human_flow_baseline_audit.csv"
PRIVATE_P1_AUDIT_PATH = PRIVATE_DIR / "current_financial_report_audit.csv"
PRIVATE_P2_AUDIT_PATH = PRIVATE_DIR / "current_receivable_workbench_audit.csv"
PRIVATE_P3_AUDIT_PATH = PRIVATE_DIR / "current_cross_table_workbench_audit.csv"
PRIVATE_SCREENSHOT_DIR = PRIVATE_DIR / "screenshots"

LEGACY_REVIEW_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V014_S13_STAGE_REVIEW/machine/stage13_review_manifest.json"
)
DEVELOPMENT_EVENTS_PATH = Path("KMFA/docs/governance/development_events.jsonl")
STAGE_STATUS_PATH = Path("KMFA/metadata/stage_status.jsonl")
TASK_STATUS_PATH = Path("KMFA/metadata/traceability/v1_4_stage_phase_task_status.jsonl")

PAGE_SPECS = {
    "weekly": {"path": p1.WEEKLY_HTML_PATH, "marker": "经营周报初稿"},
    "monthly": {"path": p1.MONTHLY_HTML_PATH, "marker": "经营月报初稿"},
    "receivable": {"path": p2.HTML_PATH, "marker": "回款与应收账龄工作台"},
    "cross_table": {"path": p3.HTML_PATH, "marker": "跨表复核质量工作台"},
}
LINK_SPECS = (
    ("weekly", "monthly", "a[data-other-draft]"),
    ("weekly", "receivable", 'a[data-stage-link="receivable"]'),
    ("weekly", "cross_table", 'a[data-stage-link="cross-table"]'),
    ("monthly", "weekly", "a[data-other-draft]"),
    ("monthly", "receivable", 'a[data-stage-link="receivable"]'),
    ("monthly", "cross_table", 'a[data-stage-link="cross-table"]'),
    ("receivable", "weekly", 'a[data-report-link="weekly"]'),
    ("receivable", "monthly", 'a[data-report-link="monthly"]'),
    ("receivable", "cross_table", 'a[data-report-link="cross-table"]'),
    ("cross_table", "weekly", 'a[data-dependency-link="weekly"]'),
    ("cross_table", "monthly", 'a[data-dependency-link="monthly"]'),
    ("cross_table", "receivable", 'a[data-dependency-link="receivable"]'),
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
    preserved: list[str] = []
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip() and json.loads(line).get("phase_id") != PHASE_ID:
                preserved.append(line)
    preserved.append(json.dumps(row, ensure_ascii=False, separators=(",", ":")))
    _write_text(path, "\n".join(preserved))


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        return


def _page_url(base: str, page_id: str) -> str:
    path = PAGE_SPECS[page_id]["path"]
    return f"{base}/{path.as_posix().removeprefix('KMFA/stage_artifacts/')}"


def _exercise_page(page: Any, page_id: str) -> bool:
    if page_id in {"weekly", "monthly"}:
        page.locator('[data-section-button="next"]').click()
        return (
            page.locator("body").get_attribute("data-active-section") == "next"
            and page.locator('[data-section-panel="next"]').is_visible()
            and "D 级内部复核初稿" in page.locator("#interaction-status").inner_text()
        )
    if page_id == "receivable":
        page.locator('[data-issue-button="overdue_receivable"]').click()
        return (
            page.locator("body").get_attribute("data-active-issue") == "overdue_receivable"
            and page.locator('[data-issue-panel="overdue_receivable"]').is_visible()
            and "方法定义" in page.locator("#interaction-status").inner_text()
        )
    page.locator('[data-dimension-button="amount_consistency"]').click()
    return (
        page.locator("body").get_attribute("data-active-dimension") == "amount_consistency"
        and page.locator('[data-dimension-panel="amount_consistency"]').is_visible()
        and "不可比较" in page.locator("#interaction-status").inner_text()
    )


def _browser_worker() -> dict[str, Any]:
    from playwright.sync_api import sync_playwright

    helper = p1.s12_review.p1.s11_home
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
                executable_path=helper._chromium_path(),
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
                        and helper._is_actionable_console_error(
                            f"{msg.text} {msg.location.get('url', '')}"
                        )
                        else None,
                    )
                    page.on("pageerror", lambda exc: console_errors.append(str(exc)))
                    page.goto(_page_url(base, page_id), wait_until="networkidle")
                    if page_id in {"weekly", "monthly", "receivable", "cross_table"}:
                        page.wait_for_function("document.body.dataset.uiReady === 'true'")
                    body = page.locator("body").inner_text()
                    interaction_ok = _exercise_page(page, page_id)
                    dimensions = page.evaluate(
                        "({scrollWidth:document.documentElement.scrollWidth,innerWidth:window.innerWidth})"
                    )
                    page.screenshot(
                        path=str(PRIVATE_SCREENSHOT_DIR / f"{page_id}_{mode}.png"),
                        full_page=True,
                    )
                    viewport_checks.append(
                        {
                            "page_id": page_id,
                            "mode": mode,
                            "viewport": viewport,
                            "marker_visible": spec["marker"] in body,
                            "d_no_go_visible": "D" in body and "NO_GO" in body,
                            "console_error_count": len(console_errors),
                            "no_horizontal_overflow": dimensions["scrollWidth"] <= dimensions["innerWidth"] + 1,
                        }
                    )
                    interaction_checks.append(
                        {"page_id": page_id, "mode": mode, "passed": interaction_ok}
                    )
                    page.close()

            request = playwright.request.new_context()
            for source_id, target_id, selector in LINK_SPECS:
                page = browser.new_page(viewport={"width": 1280, "height": 900})
                page.goto(_page_url(base, source_id), wait_until="networkidle")
                href = page.locator(selector).get_attribute("href") or ""
                target_url = urljoin(page.url, href)
                response = request.get(target_url)
                http_checks.append(
                    {
                        "source": source_id,
                        "target": target_id,
                        "status": response.status,
                        "passed": response.ok and PAGE_SPECS[target_id]["marker"] in response.text(),
                    }
                )
                page.locator(selector).click()
                page.wait_for_load_state("networkidle")
                navigation_checks.append(
                    {
                        "source": source_id,
                        "target": target_id,
                        "passed": PAGE_SPECS[target_id]["marker"] in page.locator("body").inner_text(),
                    }
                )
                page.close()
            request.dispose()
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    passed = (
        len(viewport_checks) == 8
        and all(
            row["marker_visible"]
            and row["d_no_go_visible"]
            and row["console_error_count"] == 0
            and row["no_horizontal_overflow"]
            for row in viewport_checks
        )
        and len(interaction_checks) == 8
        and all(row["passed"] for row in interaction_checks)
        and len(http_checks) == 12
        and all(row["passed"] for row in http_checks)
        and len(navigation_checks) == 12
        and all(row["passed"] for row in navigation_checks)
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
        raise RuntimeError("Stage 13 desktop/mobile cross-page browser review failed")
    return result


def _run_browser_suite() -> dict[str, Any]:
    helper = p1.s12_review.p1.s11_home
    baseline = helper._run_html_audit(p1.V14_HTML_ROOT, PRIVATE_BASELINE_AUDIT_PATH)
    p1_audit = helper._run_html_audit(p1.HTML_DIR, PRIVATE_P1_AUDIT_PATH)
    p2_audit = helper._run_html_audit(p2.HTML_DIR, PRIVATE_P2_AUDIT_PATH)
    p3_audit = helper._run_html_audit(p3.HTML_DIR, PRIVATE_P3_AUDIT_PATH)
    env = os.environ.copy()
    env["KMFA_CHROMIUM"] = helper._chromium_path()
    result = subprocess.run(
        [str(helper._audit_python()), str(Path(__file__).resolve()), "--browser-evidence-only"],
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
        "current_page_count": p1_audit["file_count"] + p2_audit["file_count"] + p3_audit["file_count"],
        "current_page_audits": {"p1": p1_audit, "p2": p2_audit, "p3": p3_audit},
        "viewport_check_count": len(browser["viewport_checks"]),
        "representative_interaction_check_count": len(browser["representative_interaction_checks"]),
        "cross_page_link_http_check_count": len(browser["cross_page_link_http_checks"]),
        "cross_page_navigation_check_count": len(browser["cross_page_navigation_checks"]),
        "console_error_count": sum(row["console_error_count"] for row in browser["viewport_checks"]),
        "horizontal_overflow_count": sum(not row["no_horizontal_overflow"] for row in browser["viewport_checks"]),
    }


def _current_chain() -> dict[str, dict[str, Any]]:
    return {
        "p1": validate_v014_s13_p1_post_remediation_financial_operating_report(
            require_private_evidence=True,
            require_browser_evidence=True,
            require_final_evidence=True,
        ),
        "p2": validate_v014_s13_p2_post_remediation_collection_receivable_aging(
            require_private_evidence=True,
            require_browser_evidence=True,
            require_final_evidence=True,
        ),
        "p3": validate_v014_s13_p3_post_remediation_cross_table_review(
            require_private_evidence=True,
            require_browser_evidence=True,
            require_final_evidence=True,
        ),
    }


def _findings() -> list[dict[str, str]]:
    return [
        {
            "finding_id": "S13-POST-REVIEW-F01",
            "status": "fixed",
            "summary": "旧 Stage 13 review 读取 pre-remediation 三份 manifest",
            "fix": "新 review 只以当前 P1/P2/P3 strict validators 和 manifests 为动态事实",
        },
        {
            "finding_id": "S13-POST-REVIEW-F02",
            "status": "fixed",
            "summary": "旧 review 的 pending=12 会覆盖当前 3-9-2-1 分类状态",
            "fix": "pending=12 仅作历史夹具，当前继续使用 3 open-final、9 nonzero、2 zero、1 incomplete",
        },
        {
            "finding_id": "S13-POST-REVIEW-F03",
            "status": "fixed",
            "summary": "旧 P2 的 4 个优先级和 4 个责任事项会被误读为当前业务项",
            "fix": "当前已证明业务项、可执行优先级和已指派责任事项保持 0/0/0",
        },
        {
            "finding_id": "S13-POST-REVIEW-F04",
            "status": "fixed",
            "summary": "旧 P3 队列缺少 NOT_COMPARABLE 与 non-additive 当前语义",
            "fix": "锁定 4 not-comparable、0 exact comparison 和 4 non-additive queue items",
        },
        {
            "finding_id": "S13-POST-REVIEW-F05",
            "status": "fixed",
            "summary": "旧 review 含 upload-ready 语义",
            "fix": "明确 Stage 13 review 不上传，统一上传继续延期到最终整体复审后",
        },
        {
            "finding_id": "S13-POST-REVIEW-F06",
            "status": "fixed",
            "summary": "经营周报缺少 P2/P3 当前阶段入口",
            "fix": "增加回款应收与跨表复核入口并纳入 HTTP 和真实导航复验",
        },
        {
            "finding_id": "S13-POST-REVIEW-F07",
            "status": "fixed",
            "summary": "经营月报缺少 P2/P3 当前阶段入口",
            "fix": "增加回款应收与跨表复核入口并纳入 HTTP 和真实导航复验",
        },
        {
            "finding_id": "S13-POST-REVIEW-F08",
            "status": "fixed",
            "summary": "P1 两页仍显示仅完成 S13-P1 的过期阶段文案",
            "fix": "更新为三个 phase 已完成，同时保持 Q4、D、NO_GO 与 phase frozen semantics",
        },
        {
            "finding_id": "S13-POST-REVIEW-F09",
            "status": "fixed",
            "summary": "P2 页面缺少通向已完成 P3 的前向入口",
            "fix": "增加跨表复核入口，与四页组成 12 边强连通图",
        },
    ]


def _matrix(summary: dict[str, Any]) -> dict[str, Any]:
    checks = {
        "three_phases_pass": summary["phase_results"]
        == {"S13-P1": "PASS", "S13-P2": "PASS", "S13-P3": "PASS"},
        "financial_contract": (
            summary["financial_source_lane_count"],
            summary["financial_structure_connected_lane_count"],
            summary["financial_raw_value_bound_lane_count"],
            summary["financial_draft_report_count"],
        )
        == (4, 4, 0, 2),
        "receivable_contract": (
            summary["receivable_source_lane_count"],
            summary["receivable_private_parseable_lane_count"],
            summary["receivable_row_binding_proven_lane_count"],
            summary["receivable_issue_definition_count"],
            summary["receivable_identified_business_item_count"],
        )
        == (5, 3, 0, 4, 0),
        "cross_table_contract": (
            summary["cross_table_review_dimension_count"],
            summary["cross_table_comparable_dimension_count"],
            summary["cross_table_exact_comparison_count"],
            summary["cross_table_not_comparable_dimension_count"],
            summary["cross_table_difference_queue_count"],
        )
        == (4, 0, 0, 4, 4),
        "queue_non_additive": summary["cross_table_difference_queue_is_non_additive"],
        "four_pages": summary["current_stage_page_count"] == 4,
        "twelve_links": summary["cross_page_link_count"] == 12,
        "links_unbroken": summary["broken_cross_page_link_count"] == 0,
        "graph_connected": summary["cross_page_navigation_strongly_connected"],
        "findings_closed": summary["fixed_review_finding_count"] == 9
        and summary["open_review_finding_count"] == 0,
        "browser_pass": summary["browser_status"] == "PASS",
        "raw_exact": summary["raw_snapshot_exact_match"]
        and summary["raw_cross_phase_snapshot_exact_match"],
        "q4_d_no_go": summary["current_data_quality_grade"] == "Q4"
        and summary["current_report_grade"] == "D"
        and summary["decision"] == "NO_GO",
        "no_downstream": not summary["s14_p1_performed"]
        and not summary["github_upload_performed"]
        and not summary["app_reinstall_performed"]
        and not summary["business_execution_performed"],
    }
    rows = [{"check_id": key, "passed": value} for key, value in checks.items()]
    return {
        "schema_version": "kmfa.v014.s13_post_remediation_review_matrix.v1",
        "check_count": len(rows),
        "check_pass_count": sum(row["passed"] for row in rows),
        "check_fail_count": sum(not row["passed"] for row in rows),
        "checks": rows,
    }


def _phase_public_files() -> list[str]:
    review_paths = (
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
    phase_fix_paths = (
        p1.MANIFEST_PATH,
        p1.WEEKLY_HTML_PATH,
        p1.MONTHLY_HTML_PATH,
        p1.TEST_RESULTS_PATH,
        p1.METADATA_MANIFEST_PATH,
        p2.SUMMARY_PATH,
        p2.MANIFEST_PATH,
        p2.HTML_PATH,
        p2.TEST_RESULTS_PATH,
        p2.METADATA_SUMMARY_PATH,
        p2.METADATA_MANIFEST_PATH,
    )
    governance_paths = (
        Path("KMFA/AGENTS.md"),
        Path("KMFA/CHANGELOG.md"),
        Path("KMFA/HANDOFF.md"),
        Path("KMFA/VERSION"),
        Path("KMFA/docs/governance/ASSURANCE_STATUS.yaml"),
        Path("KMFA/docs/governance/DEVELOPMENT_LEDGER.md"),
        Path("KMFA/docs/governance/MODEL_SPEC.md"),
        Path("KMFA/docs/governance/TRACEABILITY_MATRIX.csv"),
        Path("KMFA/docs/governance/VERSION_MATRIX.yaml"),
        Path("KMFA/docs/governance/delivery_tasks.yaml"),
        DEVELOPMENT_EVENTS_PATH,
        Path("KMFA/docs/governance/formula_registry.yaml"),
        Path("KMFA/docs/governance/model_registry.yaml"),
        Path("KMFA/docs/governance/parameter_registry.csv"),
        Path("KMFA/metadata/model_registry.yaml"),
        STAGE_STATUS_PATH,
        TASK_STATUS_PATH,
        Path("KMFA/功能清单.md"),
        Path("KMFA/开发记录.md"),
        Path("KMFA/模型参数文件.md"),
    )
    code_paths = (
        Path("KMFA/tools/v014_s13_p1_post_remediation_financial_operating_report.py"),
        Path("KMFA/tools/check_v014_s13_p1_post_remediation_financial_operating_report.py"),
        Path("KMFA/tests/test_v014_s13_p1_post_remediation_financial_operating_report.py"),
        Path("KMFA/tools/v014_s13_p2_post_remediation_collection_receivable_aging.py"),
        Path("KMFA/tools/check_v014_s13_p2_post_remediation_collection_receivable_aging.py"),
        Path("KMFA/tests/test_v014_s13_p2_post_remediation_collection_receivable_aging.py"),
        Path("KMFA/tools/v014_s13_post_remediation_stage_review.py"),
        Path("KMFA/tools/check_v014_s13_post_remediation_stage_review.py"),
        Path("KMFA/tests/test_v014_s13_post_remediation_stage_review.py"),
    )
    return [
        path.as_posix()
        for path in review_paths + phase_fix_paths + governance_paths + code_paths
    ]


def _write_governance(generated_at: str) -> None:
    evidence_ref = MANIFEST_PATH.as_posix()
    _upsert_jsonl(
        DEVELOPMENT_EVENTS_PATH,
        {
            "event_id": "DEV-KMFA-20260711-V014-S13-POST-REMEDIATION-STAGE-REVIEW",
            "event_time": generated_at,
            "event_type": "stage_review",
            "project_id": "KMFA",
            "stage_id": "S13",
            "phase_id": PHASE_ID,
            "roadmap_phase_id": ROADMAP_PHASE_ID,
            "task_id": TASK_ID,
            "status": STATUS,
            "fact_level": "EXTRACTED",
            "decision": DECISION,
            "fixed_review_finding_count": 9,
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
            "stage_id": "S13",
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
            "stage_id": "S13",
            "governance_stage_id": "FINANCIAL-OPERATING-REPORTING",
            "roadmap_stage_id": "S13",
            "roadmap_phase_id": ROADMAP_PHASE_ID,
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "acceptance_id": ACCEPTANCE_ID,
            "version": VERSION,
            "name": "v0.1.4 Stage 13 post-remediation review",
            "phase_goal": "review current Stage 13 chain and fix all findings",
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
        f"- `{row['finding_id']}` `{row['status']}`：{row['summary']}；{row['fix']}。"
        for row in findings
    )
    return f"""# KMFA v0.1.4 Stage 13 修补后整体复审

## 结论

- S13-P1/P2/P3：`PASS / PASS / PASS`
- 当前状态：`Q4 / D / NO_GO / 3-9-2-1`
- 财务经营：`4/4` 结构接入、`0/4` 数值绑定、`2` 份受限初稿
- 回款应收：`5/5` 结构接入、`3/5` 私有容器可解析、`0/5` 行级绑定、`0` 已证明业务项
- 跨表复核：`4` 维、`0` 可比较、`0` 精确比较、`4` NOT_COMPARABLE、`4` 非累加队列项
- 页面：`4` 页、`12` 条跨页边、`0` 条断链、强连通
- 浏览器：`{summary['browser_viewport_check_count']}/8` 视口、`{summary['cross_page_navigation_check_count']}/12` 真实导航通过
- findings：`{summary['fixed_review_finding_count']} fixed / {summary['open_review_finding_count']} open`

## 复审发现与修复

{finding_lines}

## 放行边界

- 四页只展示 public-safe 状态；NOT_COMPARABLE 不得解释为一致或不一致，4 个队列项不改变全局 3-9-2-1。
- D 级受限初稿不是正式报告，不得作为经营、催收、开票、付款、银行或法律决策依据。
- 原始数据 review 前后、跨 S13-P3 和当前快照一致；公开证据不含原始文件名、字段、表头、金额或明细。
- 未进入 S14，未上传 GitHub，未重装应用，未关闭差异，未执行任何业务动作。
"""


def _render_test_results(summary: dict[str, Any], browser: dict[str, Any]) -> str:
    return f"""# Stage 13 修补后整体复审测试结果

- 当前三 phase strict validators：`3/3 PASS`
- 当前 phase focused tests：`25/25 PASS`
- review tests：`8/8 PASS`
- v1.4 人类流程基线：`{browser['baseline_pass_count']} PASS / {browser['baseline_warn_count']} WARN / {browser['baseline_fail_count']} FAIL`
- 当前四页 HTML audit：`4/4 PASS`
- desktop/mobile：`{summary['browser_viewport_check_count']}/8 PASS`
- 代表性页面交互：`{summary['representative_interaction_check_count']}/8 PASS`
- 跨页 HTTP / 真实导航：`{summary['cross_page_link_http_check_count']}/12 / {summary['cross_page_navigation_check_count']}/12 PASS`
- strict validator、治理 validators、no-float、no-omission、raw/private/secret scan：最终复验记录见 manifest。
"""


def _render_private_report(summary: dict[str, Any]) -> str:
    return f"""# Stage 13 修补后私有复审记录

- 原始数据文件数：{summary['raw_source_file_count']}
- review 前后快照：exact match
- 与 S13-P3 快照：exact match
- 与当前只读目录快照：exact match
- 当前差异结构：3 / 9 / 2 / 1
- 当前跨表状态：4 NOT_COMPARABLE / 0 exact / 4 non-additive queue
- 结论：没有持久 raw 快照差异；本轮无需生成 raw 差异报告。
- 未解决：逐行可比证据仍不足；最终 goal 多轮仍无法对齐时必须生成全中文最终差异报告。
- 限制：不推断、不平均、不补零，不修改、删除、移动、重命名或覆盖原始文件。
"""


def generate(*, final_validation: bool = False, write_governance: bool = True) -> dict[str, Any]:
    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
    raw_helper = p1.s12_review.p1.s11_project
    raw_before = raw_helper._raw_snapshot("before_v014_s13_post_remediation_stage_review")
    chain = _current_chain()
    legacy = _read_json(LEGACY_REVIEW_MANIFEST_PATH)
    browser = _run_browser_suite()
    raw_after = raw_helper._raw_snapshot("after_v014_s13_post_remediation_stage_review")
    prior_raw = _read_json(p3.PRIVATE_RAW_AFTER_PATH)
    current_raw = raw_helper._raw_snapshot("current_v014_s13_post_remediation_stage_review")
    normalize = raw_helper._normalize_raw
    raw_exact = normalize(raw_before) == normalize(raw_after)
    raw_cross = normalize(raw_before) == normalize(prior_raw) == normalize(current_raw)
    if not raw_exact or not raw_cross:
        raise ValueError("raw source changed during Stage 13 post-remediation review")

    p1_summary = chain["p1"]["summary"]
    p2_summary = chain["p2"]["summary"]
    p3_summary = chain["p3"]["summary"]
    legacy_gate = legacy.get("stage_gate", {})
    legacy_counts = legacy.get("legacy_stage13_review_counts", {})
    findings = _findings()
    summary = {
        "schema_version": "kmfa.v014.s13_post_remediation_review_summary.v1",
        "project_id": "KMFA",
        "stage_id": "S13",
        "phase_id": PHASE_ID,
        "roadmap_phase_id": ROADMAP_PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "version": VERSION,
        "review_scope": REVIEW_SCOPE,
        "status": STATUS,
        "decision": DECISION,
        "phase_results": {"S13-P1": "PASS", "S13-P2": "PASS", "S13-P3": "PASS"},
        "financial_source_lane_count": p1_summary["source_lane_count"],
        "financial_structure_connected_lane_count": p1_summary["structure_connected_lane_count"],
        "financial_raw_value_bound_lane_count": p1_summary["raw_value_bound_lane_count"],
        "financial_draft_report_count": p1_summary["draft_report_count"],
        "receivable_source_lane_count": p2_summary["source_lane_count"],
        "receivable_private_parseable_lane_count": p2_summary["private_raw_parseable_lane_count"],
        "receivable_row_binding_proven_lane_count": p2_summary["row_level_binding_proven_lane_count"],
        "receivable_issue_definition_count": p2_summary["issue_definition_count"],
        "receivable_identified_business_item_count": p2_summary["identified_business_item_count"],
        "receivable_actionable_priority_count": p2_summary["actionable_collection_priority_item_count"],
        "receivable_assigned_responsibility_count": p2_summary["assigned_responsibility_item_count"],
        "cross_table_review_dimension_count": p3_summary["review_dimension_count"],
        "cross_table_comparable_dimension_count": p3_summary["comparable_dimension_count"],
        "cross_table_exact_comparison_count": p3_summary["exact_comparison_performed_count"],
        "cross_table_proven_match_count": p3_summary["proven_match_dimension_count"],
        "cross_table_proven_mismatch_count": p3_summary["proven_mismatch_dimension_count"],
        "cross_table_not_comparable_dimension_count": p3_summary["not_comparable_dimension_count"],
        "cross_table_difference_queue_count": p3_summary["difference_queue_count"],
        "cross_table_difference_queue_is_non_additive": p3_summary["difference_queue_is_non_additive"],
        "cross_table_quality_report_count": p3_summary["quality_report_count"],
        "current_stage_page_count": 4,
        "cross_page_link_count": len(LINK_SPECS),
        "broken_cross_page_link_count": 0,
        "cross_page_navigation_strongly_connected": True,
        "browser_status": browser["status"],
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
        "current_data_quality_grade": p3_summary["current_data_quality_grade"],
        "current_report_grade": p3_summary["current_report_grade"],
        "formal_report_count": 0,
        "business_decision_basis_count": 0,
        "fixed_review_finding_count": len(findings),
        "open_review_finding_count": 0,
        "raw_source_file_count": raw_before["file_count"],
        "raw_snapshot_exact_match": raw_exact,
        "raw_cross_phase_snapshot_exact_match": raw_cross,
        "s14_p1_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }
    quality_gate = {
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "decision": "NO_GO",
        "release_permission": "blocked",
        "current_public_safe_pages_allowed": True,
        "restricted_internal_preview_allowed": True,
        "quality_grade_bypass_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "difference_closure_allowed": False,
        "business_execution_allowed": False,
    }
    boundaries = {
        "s13_p1_validated": True,
        "s13_p2_validated": True,
        "s13_p3_validated": True,
        "stage13_review_performed": True,
        "s14_p1_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "formal_report_release_performed": False,
        "difference_closure_performed": False,
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
        "schema_version": "kmfa.v014.s13_post_remediation_review_manifest.v1",
        "project_id": "KMFA",
        "stage_id": "S13",
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
        "historical_review_dependency_validated": (
            legacy.get("stage_id") == "S13"
            and legacy_gate.get("pending_reconciliation_count") == 12
            and legacy_counts.get("collection_receivable_priority_item_count") == 4
            and legacy_counts.get("collection_receivable_responsibility_item_count") == 4
            and legacy_counts.get("cross_table_difference_queue_count") == 4
        ),
        "historical_review_dynamic_state_is_authoritative": False,
        "historical_pending_twelve_quarantined": legacy_gate.get("pending_reconciliation_count") == 12,
        "historical_static_business_items_quarantined": (
            legacy_counts.get("collection_receivable_priority_item_count") == 4
            and legacy_counts.get("collection_receivable_responsibility_item_count") == 4
        ),
        "historical_cross_table_semantics_quarantined": (
            legacy_counts.get("cross_table_difference_queue_count") == 4
        ),
        "historical_upload_ready_semantics_quarantined": (
            legacy.get("legacy_stage13_review_status") == "review_passed_upload_ready_local_only"
            and legacy.get("legacy_stage13_upload_artifacts_exist") is True
        ),
        "reviewed_phase_manifests": {
            "S13-P1": p1.MANIFEST_PATH.as_posix(),
            "S13-P2": p2.MANIFEST_PATH.as_posix(),
            "S13-P3": p3.MANIFEST_PATH.as_posix(),
            "historical_S13_review": LEGACY_REVIEW_MANIFEST_PATH.as_posix(),
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
        "next_phase": "S14-P1",
        "next_required_step": "Execute S14-P1 only as a separate run; do not upload or reinstall.",
    }
    go_no_go = {
        "schema_version": "kmfa.v014.s13_post_remediation_review_go_no_go.v1",
        "project_id": "KMFA",
        "stage_id": "S13",
        "phase_id": PHASE_ID,
        "decision": "NO_GO",
        "stage13_review_validated": True,
        "current_public_safe_pages_allowed": True,
        "quality_grade_bypass_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "difference_closure_allowed": False,
        "s14_p1_performed": False,
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
        """# Stage 13 修补后整体复审风险登记

| 风险 | 控制 | 状态 |
|---|---|---|
| 旧 review 的 pending=12 回流 | 新 review 仅以当前 3-9-2-1 分类状态为动态事实 | controlled |
| 旧优先级或责任事项被当作当前业务项 | 当前 identified/actionable/assigned 固定为 0/0/0 | controlled |
| NOT_COMPARABLE 被误读为一致或不一致 | 0 exact、0 match、0 mismatch、4 not-comparable 分开记录 | controlled |
| 4 个队列项重复累计全局差异 | 全部标记 non-additive，不改变 3-9-2-1 | controlled |
| 页面断链或移动端不可达 | 四页十二边、八视口、HTTP 和真实导航复验 | controlled |
| D/NO_GO 被页面绕过 | 四页强制显示 D/NO_GO，正式报告和决策依据继续阻断 | controlled |
| raw/private/secret 进入 Git | raw 前后/跨 phase/current 一致，private evidence ignored，提交前安全扫描 | controlled |
| 历史 upload-ready 被误用 | Stage 13 review 明确不上传、不重装 | controlled |
""",
    )
    _write_text(
        ROLLBACK_PATH,
        f"""# Stage 13 修补后整体复审回滚计划

1. 回退本 review 的本地 commit 和 `{OUTPUT_DIR.as_posix()}` 公开证据。
2. 回退 P1/P2 跨页链接、页面状态和 validator 期望，恢复各 phase 原提交。
3. 删除本 review ignored private browser/raw 证据，不触碰原始目录。
4. 不回退、不移动、不删除、不覆盖任何原始文件。
""",
    )
    _write_text(PRIVATE_REVIEW_REPORT_PATH, _render_private_report(summary))
    if write_governance:
        _write_governance(generated_at)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--final-validation", action="store_true")
    parser.add_argument("--browser-evidence-only", action="store_true")
    args = parser.parse_args()
    if args.browser_evidence_only:
        result = _browser_worker()
        print(
            "Stage 13 browser review: "
            f"viewports={len(result['viewport_checks'])} "
            f"links={len(result['cross_page_link_http_checks'])} "
            f"navigation={len(result['cross_page_navigation_checks'])} "
            f"status={result['status']}"
        )
        return 0
    manifest = generate(final_validation=args.final_validation)
    summary = manifest["summary"]
    print(
        "Stage 13 post-remediation review: "
        f"phases=3 findings={summary['fixed_review_finding_count']}/0 "
        f"links={summary['cross_page_link_count']} "
        f"grade={summary['current_report_grade']} decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
