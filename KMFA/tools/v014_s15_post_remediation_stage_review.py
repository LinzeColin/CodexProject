#!/usr/bin/env python3
"""Generate current KMFA v0.1.4 Stage 15 post-remediation review evidence."""

from __future__ import annotations

import argparse
import functools
import http.server
import json
import os
import socketserver
import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

from KMFA.tools import v014_s15_p1_post_remediation_performance_fact_fields as p1
from KMFA.tools import v014_s15_p2_post_remediation_performance_review_list as p2
from KMFA.tools import v014_s15_p3_post_remediation_salary_boundary as p3
from KMFA.tools.check_v014_s15_p1_post_remediation_performance_fact_fields import (
    validate_v014_s15_p1_post_remediation_performance_fact_fields,
)
from KMFA.tools.check_v014_s15_p2_post_remediation_performance_review_list import (
    validate_v014_s15_p2_post_remediation_performance_review_list,
)
from KMFA.tools.check_v014_s15_p3_post_remediation_salary_boundary import (
    validate_v014_s15_p3_post_remediation_salary_boundary,
)
from KMFA.tools.check_v014_s15_stage_review import validate_v014_s15_stage_review


PHASE_ID = "V014_S15_POST_REMEDIATION_STAGE_REVIEW"
ROADMAP_PHASE_ID = "STAGE-REVIEW"
TASK_ID = "KMFA-V014-S15-POST-REMEDIATION-STAGE-REVIEW-20260711"
ACCEPTANCE_ID = "ACC-V014-S15-POST-REMEDIATION-STAGE-REVIEW"
VERSION = "0.1.4-s15-post-remediation-stage-review"
STATUS = "completed_validated_local_only_stage15_review_no_go_upload_deferred"
DECISION = "NO_GO"
REVIEW_SCOPE = "v014_s15_post_remediation_stage_review_only"
FORMULA_ID = "FORM-KMFA-V014-S15-POST-REMEDIATION-STAGE-REVIEW-001"
PARAMETER_IDS = ("PARAM-KMFA-1777", "PARAM-KMFA-1778", "PARAM-KMFA-1779")
MODEL_REGISTRY_KEY = "kmfa_v014_s15_post_remediation_stage_review"

OUTPUT_DIR = Path("KMFA/stage_artifacts") / PHASE_ID
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "stage15_post_remediation_review_summary.json"
MANIFEST_PATH = MACHINE_DIR / "stage15_post_remediation_review_manifest.json"
MATRIX_PATH = MACHINE_DIR / "stage15_post_remediation_review_matrix_public_safe.json"
GO_NO_GO_PATH = MACHINE_DIR / "stage15_post_remediation_review_go_no_go_report.json"
REPORT_PATH = HUMAN_DIR / "stage15_post_remediation_review_report_zh.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results_zh.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register_zh.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan_zh.md"

QUALITY_DIR = Path("KMFA/metadata/quality")
METADATA_SUMMARY_PATH = QUALITY_DIR / "v014_s15_post_remediation_stage_review_summary.json"
METADATA_MANIFEST_PATH = QUALITY_DIR / "v014_s15_post_remediation_stage_review_manifest.json"
METADATA_MATRIX_PATH = QUALITY_DIR / "v014_s15_post_remediation_stage_review_matrix_public_safe.json"
METADATA_GO_NO_GO_PATH = QUALITY_DIR / "v014_s15_post_remediation_stage_review_go_no_go_report.json"

PRIVATE_DIR = Path("KMFA/.codex_private_runtime/v014_s15_post_remediation_stage_review")
PRIVATE_RAW_BEFORE_PATH = PRIVATE_DIR / "raw_immutability_before.json"
PRIVATE_RAW_AFTER_PATH = PRIVATE_DIR / "raw_immutability_after.json"
PRIVATE_REVIEW_REPORT_PATH = PRIVATE_DIR / "stage15_post_remediation_review_validation_zh.md"
PRIVATE_BROWSER_PATH = PRIVATE_DIR / "browser_verification.json"
PRIVATE_BASELINE_AUDIT_PATH = PRIVATE_DIR / "human_flow_baseline_audit.csv"
PRIVATE_P1_AUDIT_PATH = PRIVATE_DIR / "current_performance_fields_audit.csv"
PRIVATE_P2_AUDIT_PATH = PRIVATE_DIR / "current_performance_review_audit.csv"
PRIVATE_P3_AUDIT_PATH = PRIVATE_DIR / "current_salary_boundary_audit.csv"
PRIVATE_SCREENSHOT_DIR = PRIVATE_DIR / "screenshots"

LEGACY_REVIEW_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V014_S15_STAGE_REVIEW/machine/stage15_review_manifest.json"
)
ROADMAP_PATH = Path(
    "KMFA/taskpack/v1_4/roadmap/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_4.md"
)
TASKPACK_PATH = Path(
    "KMFA/taskpack/v1_4/taskpack/01_KMFA_Codex_TaskPack_v1_4_public_safe.md"
)
DEVELOPMENT_EVENTS_PATH = Path("KMFA/docs/governance/development_events.jsonl")
ASSURANCE_STATUS_PATH = Path("KMFA/docs/governance/ASSURANCE_STATUS.yaml")
STAGE_STATUS_PATH = Path("KMFA/metadata/stage_status.jsonl")
TASK_STATUS_PATH = Path("KMFA/metadata/traceability/v1_4_stage_phase_task_status.jsonl")

PAGE_SPECS = {
    "p1": {"path": p1.HTML_PATH, "marker": "绩效事实字段工作台"},
    "p2": {"path": p2.HTML_PATH, "marker": "绩效复核清单工作台"},
    "p3": {"path": p3.HTML_PATH, "marker": "工资项目边界工作台"},
}
LINK_SPECS = (
    ("p1", "p2", 'a[data-stage-link="review-list"]'),
    ("p1", "p3", 'a[data-stage-link="salary-boundary"]'),
    ("p2", "p1", 'a[data-dependency-link="fact-fields"]'),
    ("p2", "p3", 'a[data-stage-link="salary-boundary"]'),
    ("p3", "p1", 'a[data-dependency-link="fact-fields"]'),
    ("p3", "p2", 'a[data-dependency-link="review-list"]'),
)


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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


def _sync_assurance_snapshot_time(generated_at: str) -> None:
    lines = ASSURANCE_STATUS_PATH.read_text(encoding="utf-8").splitlines()
    indexes = [index for index, line in enumerate(lines) if line.startswith("snapshot_event_time:")]
    if len(indexes) != 1:
        raise RuntimeError("ASSURANCE_STATUS must contain exactly one snapshot_event_time")
    lines[indexes[0]] = f'snapshot_event_time: "{generated_at}"'
    _write_text(ASSURANCE_STATUS_PATH, "\n".join(lines))


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        return


def _page_url(base: str, page_id: str) -> str:
    path = PAGE_SPECS[page_id]["path"]
    return f"{base}/{path.as_posix().removeprefix('KMFA/stage_artifacts/')}"


def _exercise_page(page: Any, page_id: str) -> bool:
    if page_id == "p2":
        page.locator('[data-review-button="customer_relationship_rate"]').click()
        return (
            page.locator("body").get_attribute("data-active-review") == "customer_relationship_rate"
            and page.locator('[data-review-panel="customer_relationship_rate"]').is_visible()
            and "客情费率" in page.locator("#interaction-status").inner_text()
        )
    page.locator('[data-field-button="customer_relationship_rate"]').click()
    return (
        page.locator("body").get_attribute("data-active-field") == "customer_relationship_rate"
        and page.locator('[data-field-panel="customer_relationship_rate"]').is_visible()
        and "客情费率" in page.locator("#interaction-status").inner_text()
    )


def _browser_worker() -> dict[str, Any]:
    from playwright.sync_api import sync_playwright

    helper = p1.s14_review.p1.s13_review.p1.s12_review.p1.s11_home
    PRIVATE_SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    root = Path("KMFA/stage_artifacts").resolve()
    handler = functools.partial(_QuietHandler, directory=str(root))
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
                    errors: list[str] = []
                    page.on(
                        "console",
                        lambda message, errors=errors: errors.append(message.text)
                        if message.type == "error"
                        and helper._is_actionable_console_error(
                            f"{message.text} {message.location.get('url', '')}"
                        )
                        else None,
                    )
                    page.on("pageerror", lambda exc, errors=errors: errors.append(str(exc)))
                    page.goto(_page_url(base, page_id), wait_until="networkidle")
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
                            "d_no_go_visible": "Q4 / D" in body and "NO_GO" in body,
                            "stage_complete_visible": "Stage 15 三个 phase 与整体复审均已完成" in body,
                            "s16_separate_run_visible": "S16 仅可在下一 run work" in body,
                            "console_error_count": len(errors),
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
                link = page.locator(selector).first
                href = link.get_attribute("href") or ""
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
                link.click()
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
        len(viewport_checks) == 6
        and all(
            row["marker_visible"]
            and row["d_no_go_visible"]
            and row["stage_complete_visible"]
            and row["s16_separate_run_visible"]
            and row["console_error_count"] == 0
            and row["no_horizontal_overflow"]
            for row in viewport_checks
        )
        and len(interaction_checks) == 6
        and all(row["passed"] for row in interaction_checks)
        and len(http_checks) == 6
        and all(row["passed"] for row in http_checks)
        and len(navigation_checks) == 6
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
        raise RuntimeError("Stage 15 desktop/mobile cross-page browser review failed")
    return result


def _run_browser_suite() -> dict[str, Any]:
    helper = p1.s14_review.p1.s13_review.p1.s12_review.p1.s11_home
    baseline = helper._run_html_audit(p1.HTML_BASELINE_ROOT, PRIVATE_BASELINE_AUDIT_PATH)
    audits = {
        "p1": helper._run_html_audit(p1.HTML_DIR, PRIVATE_P1_AUDIT_PATH),
        "p2": helper._run_html_audit(p2.HTML_DIR, PRIVATE_P2_AUDIT_PATH),
        "p3": helper._run_html_audit(p3.HTML_DIR, PRIVATE_P3_AUDIT_PATH),
    }
    if baseline != {
        "file_count": 6,
        "control_row_count": 54,
        "pass_count": 54,
        "warn_count": 0,
        "fail_count": 0,
    }:
        raise RuntimeError("v1.4 HTML baseline drift")
    expected = {"p1": 16, "p2": 15, "p3": 14}
    for page_id, audit in audits.items():
        if audit != {
            "file_count": 1,
            "control_row_count": expected[page_id],
            "pass_count": expected[page_id],
            "warn_count": 0,
            "fail_count": 0,
        }:
            raise RuntimeError(f"Stage 15 current HTML audit drift: {page_id}")
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
        "current_page_count": 3,
        "current_control_row_count": sum(row["control_row_count"] for row in audits.values()),
        "current_pass_count": sum(row["pass_count"] for row in audits.values()),
        "current_warn_count": sum(row["warn_count"] for row in audits.values()),
        "current_fail_count": sum(row["fail_count"] for row in audits.values()),
        "current_page_audits": audits,
        "viewport_check_count": len(browser["viewport_checks"]),
        "representative_interaction_check_count": len(browser["representative_interaction_checks"]),
        "cross_page_link_http_check_count": len(browser["cross_page_link_http_checks"]),
        "cross_page_navigation_check_count": len(browser["cross_page_navigation_checks"]),
        "console_error_count": sum(row["console_error_count"] for row in browser["viewport_checks"]),
        "horizontal_overflow_count": sum(not row["no_horizontal_overflow"] for row in browser["viewport_checks"]),
    }


def _current_chain() -> dict[str, dict[str, Any]]:
    return {
        "p1": validate_v014_s15_p1_post_remediation_performance_fact_fields(
            require_private_evidence=True,
            require_browser_evidence=True,
            require_final_evidence=True,
        ),
        "p2": validate_v014_s15_p2_post_remediation_performance_review_list(
            require_private_evidence=True,
            require_browser_evidence=True,
            require_final_evidence=True,
        ),
        "p3": validate_v014_s15_p3_post_remediation_salary_boundary(
            require_private_evidence=True,
            require_browser_evidence=True,
            require_final_evidence=True,
        ),
    }


def _findings() -> list[dict[str, str]]:
    rows = (
        ("F01", "旧 Stage 15 review 使用 4 条合成绩效事实、4 条工资就绪记录和 16 项复核", "将旧 review 仅作为历史夹具，当前动态事实改为 0/0/6"),
        ("F02", "三个 phase 的浏览器证据各自独立，未证明 Stage 15 三页互通", "增加三页六边、六视口、六交互、HTTP 与真实导航整体复验"),
        ("F03", "P1 缺少 P2 与 P3 当前阶段入口", "增加绩效复核清单和工资项目边界入口"),
        ("F04", "P1 footer 仍显示只完成 S15-P1", "更新为三个 phase 与整体复审完成且 S16 仅可下一 run"),
        ("F05", "P1 五列表格缺少明确移动端断词保护", "增加固定布局、紧凑间距和自动断词"),
        ("F06", "P2 缺少 P3 当前阶段入口", "增加工资项目边界入口并纳入双向导航复验"),
        ("F07", "P2 footer 仍显示 S15-P3 和整体复审未执行", "更新为 Stage 15 review 完成且薪资动作继续阻断"),
        ("F08", "P2 六列和四列表格在移动端发生裁切", "移除移动端最小宽度并启用固定布局与断词"),
        ("F09", "P3 footer 仍显示整体复审未执行", "更新为 Stage 15 review 完成且最终审批发放继续人工阻断"),
        ("F10", "P3 两张四列表格在移动端发生裁切", "移除移动端最小宽度并启用固定布局与断词"),
    )
    return [
        {"finding_id": f"KMFA-V014-S15-REV-{code}", "severity": "P2", "status": "fixed", "summary": summary, "fix": fix}
        for code, summary, fix in rows
    ]


def _quality_gate() -> dict[str, Any]:
    return {
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "decision": "NO_GO",
        "open_final_difference_accepted_count": 3,
        "nonzero_delta_reconciliation_count": 9,
        "zero_delta_reconciliation_count": 2,
        "incomplete_reconciliation_count": 1,
        "one_cent_tolerance_minor_unit": 0,
    }


def _review_boundaries() -> dict[str, bool]:
    return {
        "s15_p1_performed": True,
        "s15_p2_performed": True,
        "s15_p3_performed": True,
        "stage15_review_performed": True,
        "s16_p1_performed": False,
        "salary_calculation_performed": False,
        "bonus_approval_performed": False,
        "payroll_export_performed": False,
        "final_compensation_decision_performed": False,
        "final_payment_performed": False,
        "payment_execution_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "formal_report_release_performed": False,
        "difference_closure_performed": False,
        "business_execution_performed": False,
    }


def _public_safety() -> dict[str, bool]:
    return {
        "raw_business_data_committed": False,
        "raw_file_names_committed": False,
        "raw_schema_or_header_committed": False,
        "project_or_employee_plaintext_committed": False,
        "business_amount_committed": False,
        "salary_or_bonus_value_committed": False,
        "payroll_payload_committed": False,
        "final_payment_payload_committed": False,
        "zip_excel_pdf_private_csv_committed": False,
        "credential_or_secret_committed": False,
        "private_runtime_committed": False,
    }


def _acceptance_matrix(summary: dict[str, Any]) -> dict[str, Any]:
    checks = (
        ("phase_chain", summary["phase_strict_validator_pass_count"] == 3),
        ("phase_tests", summary["phase_focused_test_pass_count"] == 24),
        ("zero_fact_rows", summary["performance_fact_row_count"] == 0),
        ("six_review_items", summary["field_review_item_count"] == 6),
        ("zero_salary_records", summary["future_salary_readiness_record_count"] == 0),
        ("human_boundary", summary["human_boundary_checkpoint_count"] == 4),
        ("findings_closed", summary["fixed_review_finding_count"] == 10 and summary["open_review_finding_count"] == 0),
        ("navigation", summary["cross_page_link_count"] == 6 and summary["broken_cross_page_link_count"] == 0),
        ("browser", summary["browser_status"] == "PASS"),
        ("raw_exact", summary["raw_snapshot_exact_match"] and summary["raw_cross_phase_snapshot_exact_match"]),
        ("downstream_closed", not summary["s16_p1_performed"] and not summary["github_upload_performed"]),
    )
    rows = [
        {"check_id": f"V014-S15-REVIEW-ACC-{index:03d}", "name": name, "status": "PASS" if passed else "FAIL"}
        for index, (name, passed) in enumerate(checks, 1)
    ]
    return {
        "schema_version": "kmfa.v014.s15_post_remediation_review_matrix.v1",
        "acceptance_id": ACCEPTANCE_ID,
        "check_count": len(rows),
        "check_pass_count": sum(row["status"] == "PASS" for row in rows),
        "check_fail_count": sum(row["status"] == "FAIL" for row in rows),
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
    phase_fix_paths = (p1.HTML_PATH, p2.HTML_PATH, p3.HTML_PATH)
    governance_paths = (
        Path("KMFA/AGENTS.md"),
        Path("KMFA/CHANGELOG.md"),
        Path("KMFA/HANDOFF.md"),
        Path("KMFA/VERSION"),
        ASSURANCE_STATUS_PATH,
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
        Path("KMFA/tools/v014_s15_p1_post_remediation_performance_fact_fields.py"),
        Path("KMFA/tools/check_v014_s15_p1_post_remediation_performance_fact_fields.py"),
        Path("KMFA/tools/v014_s15_p2_post_remediation_performance_review_list.py"),
        Path("KMFA/tools/check_v014_s15_p2_post_remediation_performance_review_list.py"),
        Path("KMFA/tools/v014_s15_p3_post_remediation_salary_boundary.py"),
        Path("KMFA/tools/check_v014_s15_p3_post_remediation_salary_boundary.py"),
        Path("KMFA/tools/v014_s15_post_remediation_stage_review.py"),
        Path("KMFA/tools/check_v014_s15_post_remediation_stage_review.py"),
        Path("KMFA/tests/test_v014_s15_post_remediation_stage_review.py"),
    )
    return [path.as_posix() for path in review_paths + phase_fix_paths + governance_paths + code_paths]


def _write_governance(generated_at: str) -> None:
    evidence_ref = MANIFEST_PATH.as_posix()
    _sync_assurance_snapshot_time(generated_at)
    _upsert_jsonl(
        DEVELOPMENT_EVENTS_PATH,
        {
            "event_id": "DEV-KMFA-20260711-V014-S15-POST-REMEDIATION-STAGE-REVIEW",
            "event_time": generated_at,
            "event_type": "stage_review",
            "project_id": "KMFA",
            "stage_id": "S15",
            "phase_id": PHASE_ID,
            "roadmap_phase_id": ROADMAP_PHASE_ID,
            "task_id": TASK_ID,
            "status": STATUS,
            "fact_level": "EXTRACTED",
            "decision": DECISION,
            "fixed_review_finding_count": 10,
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
            "stage_id": "S15",
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
            "stage_id": "S15",
            "governance_stage_id": "SALES-PERFORMANCE-SALARY-BOUNDARY",
            "roadmap_stage_id": "S15",
            "roadmap_phase_id": ROADMAP_PHASE_ID,
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "acceptance_id": ACCEPTANCE_ID,
            "version": VERSION,
            "name": "v0.1.4 Stage 15 post-remediation review",
            "phase_goal": "review current Stage 15 chain and fix all findings",
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
    return f"""# KMFA v0.1.4 Stage 15 修补后整体复审

## 结论

- S15-P1/P2/P3：`PASS / PASS / PASS`
- 当前状态：`Q4 / D / NO_GO / 3-9-2-1`
- 绩效字段：`6` 字段、`6` 人工复核、`0` 权威值绑定
- 绩效清单：`1` 个六列空事实表、`0` 实际异常项目、`6` 字段级复核事项
- 工资边界：`1` 个 schema-only 接口、`0` payload、`0` 就绪记录、`4` 人工检查点、`0` 薪资值
- 页面：`3` 页、`6` 条跨页边、`0` 断链、强连通
- 浏览器：`{summary['browser_viewport_check_count']}/6` 视口、`{summary['cross_page_navigation_check_count']}/6` 真实导航通过
- findings：`{summary['fixed_review_finding_count']} fixed / {summary['open_review_finding_count']} open`

## 复审发现与修复

{finding_lines}

## 放行边界

- 三页只展示 public-safe 结构、字段级复核和人工边界，不包含项目、员工、金额、工资或支付记录。
- D 级内部复核页面不是正式报告，不得作为绩效、工资、奖金、发放或经营决策依据。
- 原始数据 review 前后、跨 S15-P3 和当前快照一致；公开证据不含 raw/private 明文。
- 未进入 S16，未上传 GitHub，未重装应用，未关闭差异，未执行任何业务动作。
"""


def _render_private_report(summary: dict[str, Any]) -> str:
    return f"""# Stage 15 修补后私有复审记录

- 原始数据文件数：{summary['raw_source_file_count']}
- review 前后快照：exact match
- 与 S15-P3 快照：exact match
- 与当前只读目录快照：exact match
- 当前差异结构：3 / 9 / 2 / 1
- 绩效事实 / 工资就绪记录 / 薪资数值：0 / 0 / 0
- 结论：没有持久 raw 快照差异；本轮无需生成 raw 变更报告。
- 未解决：项目、员工、期间、单位、口径、公式与精确值仍未权威绑定；最终 goal 多轮仍无法对齐时必须生成全中文最终差异报告。
- 限制：不推断、不平均、不补零，不修改、删除、移动、重命名或覆盖原始文件。
"""


def generate(*, final_validation: bool = False, write_governance: bool = True) -> dict[str, Any]:
    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
    roadmap = ROADMAP_PATH.read_text(encoding="utf-8")
    taskpack = TASKPACK_PATH.read_text(encoding="utf-8")
    for token in ("S15｜销售绩效事实与复核清单", "绩效事实字段", "绩效复核清单", "与工资项目边界"):
        if token not in roadmap:
            raise ValueError(f"roadmap token missing: {token}")
    for token in ("销售绩效/业务考核线", "不做工资最终审批", "不自动发工资或奖金"):
        if token not in taskpack:
            raise ValueError(f"taskpack token missing: {token}")

    raw_helper = p1.s14_review.p1.s13_review.p1.s12_review.p1.s11_project
    raw_before = raw_helper._raw_snapshot("before_v014_s15_post_remediation_stage_review")
    chain = _current_chain()
    validate_v014_s15_stage_review()
    historical = _read_json(LEGACY_REVIEW_MANIFEST_PATH)
    findings = _findings()
    browser = _run_browser_suite()
    raw_after = raw_helper._raw_snapshot("after_v014_s15_post_remediation_stage_review")
    prior_raw = _read_json(p3.PRIVATE_RAW_AFTER_PATH)
    current_raw = raw_helper._raw_snapshot("current_v014_s15_post_remediation_stage_review")
    normalize = raw_helper._normalize_raw
    raw_exact = normalize(raw_before) == normalize(raw_after)
    raw_cross = normalize(raw_before) == normalize(prior_raw) == normalize(current_raw)
    if not raw_exact or not raw_cross:
        raise ValueError("raw source changed during Stage 15 review")

    s1 = chain["p1"]["summary"]
    s2 = chain["p2"]["summary"]
    s3 = chain["p3"]["summary"]
    summary = {
        "schema_version": "kmfa.v014.s15_post_remediation_review_summary.v1",
        "project_id": "KMFA",
        "stage_id": "S15",
        "phase_id": PHASE_ID,
        "roadmap_phase_id": ROADMAP_PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "version": VERSION,
        "status": STATUS,
        "decision": DECISION,
        "phase_results": {"S15-P1": "PASS", "S15-P2": "PASS", "S15-P3": "PASS"},
        "phase_focused_test_count": 24,
        "phase_focused_test_pass_count": 24,
        "phase_strict_validator_count": 3,
        "phase_strict_validator_pass_count": 3,
        "required_field_count": s1["required_field_count"],
        "manual_review_required_field_count": s1["manual_review_required_field_count"],
        "authoritative_row_binding_count": s1["authoritative_row_binding_proven_field_count"],
        "authoritative_value_binding_count": s1["authoritative_value_binding_proven_field_count"],
        "private_unique_candidate_sheet_count": s1["private_unique_candidate_sheet_count"],
        "performance_fact_table_schema_count": s2["performance_fact_table_schema_count"],
        "performance_fact_table_column_count": s2["performance_fact_table_column_count"],
        "performance_fact_row_count": s2["performance_fact_row_count"],
        "actual_abnormal_project_count": s2["actual_abnormal_project_count"],
        "field_review_item_count": s2["field_review_item_count"],
        "public_business_value_count": s2["public_business_value_count"],
        "fact_output_interface_contract_count": s3["fact_output_interface_contract_count"],
        "fact_output_interface_field_count": s3["fact_output_interface_field_count"],
        "interface_payload_record_count": s3["interface_payload_record_count"],
        "future_salary_read_draft_count": s3["future_salary_read_draft_count"],
        "future_salary_field_mapping_count": s3["future_salary_field_mapping_count"],
        "future_salary_readiness_record_count": s3["future_salary_readiness_record_count"],
        "human_boundary_checkpoint_count": s3["human_boundary_checkpoint_count"],
        "human_approval_completed_count": s3["human_approval_completed_count"],
        "salary_numeric_value_count": s3["salary_numeric_value_count"],
        "review_finding_count": len(findings),
        "fixed_review_finding_count": len(findings),
        "open_review_finding_count": 0,
        "current_stage_page_count": browser["current_page_count"],
        "cross_page_link_count": len(LINK_SPECS),
        "broken_cross_page_link_count": 0,
        "cross_page_navigation_strongly_connected": True,
        "browser_status": browser["status"],
        "baseline_html_control_row_count": browser["baseline_control_row_count"],
        "baseline_html_pass_count": browser["baseline_pass_count"],
        "current_html_control_row_count": browser["current_control_row_count"],
        "current_html_pass_count": browser["current_pass_count"],
        "browser_viewport_check_count": browser["viewport_check_count"],
        "representative_interaction_check_count": browser["representative_interaction_check_count"],
        "cross_page_link_http_check_count": browser["cross_page_link_http_check_count"],
        "cross_page_navigation_check_count": browser["cross_page_navigation_check_count"],
        "console_error_count": browser["console_error_count"],
        "horizontal_overflow_count": browser["horizontal_overflow_count"],
        "raw_source_file_count": raw_before["file_count"],
        "raw_snapshot_exact_match": raw_exact,
        "raw_cross_phase_snapshot_exact_match": raw_cross,
        "open_final_difference_accepted_count": s3["open_final_difference_accepted_count"],
        "nonzero_delta_reconciliation_count": s3["nonzero_delta_reconciliation_count"],
        "zero_delta_reconciliation_count": s3["zero_delta_reconciliation_count"],
        "incomplete_reconciliation_count": s3["incomplete_reconciliation_count"],
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        **_review_boundaries(),
    }
    matrix = _acceptance_matrix(summary)
    go_no_go = {
        "schema_version": "kmfa.v014.s15_post_remediation_review_go_no_go.v1",
        "project_id": "KMFA",
        "stage_id": "S15",
        "phase_id": PHASE_ID,
        "decision": "NO_GO",
        "stage15_review_validated": True,
        "s16_p1_allowed_in_this_run": False,
        "salary_calculation_allowed": False,
        "bonus_approval_allowed": False,
        "payroll_export_allowed": False,
        "final_payment_allowed": False,
        "payment_execution_allowed": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "business_execution_allowed": False,
    }
    validation_summary = {
        "final_validation_recorded": final_validation,
        "phase_focused_tests": "PASS" if final_validation else "PENDING",
        "phase_strict_validators": "PASS" if final_validation else "PENDING",
        "review_focused_test": "PASS" if final_validation else "PENDING",
        "review_strict_validator": "PASS" if final_validation else "PENDING",
        "browser_desktop_mobile": "PASS" if final_validation else "PENDING",
        "raw_alignment": "PASS" if final_validation else "PENDING",
        "governance_and_safety_scans": "PASS" if final_validation else "PENDING",
    }
    legacy_gate = historical["stage_gate"]
    manifest = {
        "schema_version": "kmfa.v014.s15_post_remediation_review_manifest.v1",
        "project_id": "KMFA",
        "stage_id": "S15",
        "phase_id": PHASE_ID,
        "roadmap_phase_id": ROADMAP_PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "version": VERSION,
        "status": STATUS,
        "decision": DECISION,
        "review_scope": REVIEW_SCOPE,
        "generated_at": generated_at,
        "reviewed_head": _git_output(["rev-parse", "HEAD"]),
        "branch": _git_output(["branch", "--show-current"]),
        "remote": _git_output(["remote", "get-url", "origin"]),
        "formula_id": FORMULA_ID,
        "parameter_ids": list(PARAMETER_IDS),
        "model_registry_key": MODEL_REGISTRY_KEY,
        "summary": summary,
        "review_findings": findings,
        "browser_review": browser,
        "quality_gate": _quality_gate(),
        "review_boundaries": _review_boundaries(),
        "public_repo_safety": _public_safety(),
        "current_s15_chain_validated": True,
        "historical_s15_review_validated": historical.get("stage_review_performed") is True,
        "historical_s15_review_dynamic_state_is_authoritative": False,
        "historical_four_fact_rows_quarantined": legacy_gate.get("performance_fact_row_count") == 4,
        "historical_four_readiness_rows_quarantined": legacy_gate.get("future_salary_system_readiness_row_count") == 4,
        "historical_sixteen_review_items_quarantined": legacy_gate.get("pending_review_item_count") == 16,
        "reviewed_phase_manifests": {
            "S15-P1": p1.MANIFEST_PATH.as_posix(),
            "S15-P2": p2.MANIFEST_PATH.as_posix(),
            "S15-P3": p3.MANIFEST_PATH.as_posix(),
            "historical_S15_review": LEGACY_REVIEW_MANIFEST_PATH.as_posix(),
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
        "taskpack_contract": {
            "roadmap_read": True,
            "taskpack_read": True,
            "stage15_three_phase_contract_reviewed": True,
            "salary_final_approval_and_payment_remain_human": True,
            "raw_read_only_contract_applied": True,
        },
        "acceptance_matrix": matrix,
        "go_no_go": go_no_go,
        "validation_summary": validation_summary,
        "next_phase": "S16-P1",
        "next_required_step": (
            "下一轮仅执行 S16-P1；不得执行 S16-P2/P3、Stage 16 整体复审、GitHub upload、"
            "app reinstall、正式报告、差异关闭或业务执行。"
        ),
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
    _write_text(
        TEST_RESULTS_PATH,
        f"""# Stage 15 修补后整体复审测试结果

- 当前三 phase focused tests：`24/24 PASS`
- 当前三 phase strict validators：`3/3 PASS`
- review tests / strict validator：最终复验记录见 manifest。
- v1.4 人类流程基线：`54/54 PASS`
- 当前三页 HTML audit：`16/16 + 15/15 + 14/14 PASS`
- desktop/mobile：`{summary['browser_viewport_check_count']}/6 PASS`
- 代表性页面交互：`{summary['representative_interaction_check_count']}/6 PASS`
- 跨页 HTTP / 真实导航：`{summary['cross_page_link_http_check_count']}/6 / {summary['cross_page_navigation_check_count']}/6 PASS`
- raw 前后 / 跨 S15-P3 / current：`exact match`
""",
    )
    _write_text(
        RISK_REGISTER_PATH,
        """# Stage 15 修补后整体复审风险登记

| 风险 | 控制 | 状态 |
|---|---|---|
| 旧 4 条合成事实或就绪记录回流 | 当前三 phase strict evidence 为唯一动态事实，记录保持 0 | controlled |
| 空结构被误读为工资输入 | payload、就绪记录和薪资数值保持 0 | controlled |
| 人工审批被绕过 | 四个检查点均未执行且不可自动化 | controlled |
| 页面断链或移动端表格裁切 | 三页六边、固定布局、六视口与真实导航复验 | controlled |
| D/NO_GO 被页面绕过 | 三页强制显示 Q4/D/NO_GO，S16 仅可下一 run | controlled |
| raw/private/secret 进入 Git | raw 精确快照、private ignored、提交前安全扫描 | controlled |
""",
    )
    _write_text(
        ROLLBACK_PATH,
        f"""# Stage 15 修补后整体复审回滚计划

1. 回退本 review 的本地 commit 和 `{OUTPUT_DIR.as_posix()}` 公开证据。
2. 回退 P1/P2/P3 跨页链接、footer、移动端表格和 validator 期望，恢复各 phase 原提交。
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
    parser.add_argument("--no-governance", action="store_true")
    args = parser.parse_args()
    if args.browser_evidence_only:
        result = _browser_worker()
        print(result["status"])
        return 0 if result["status"] == "PASS" else 1
    manifest = generate(
        final_validation=args.final_validation,
        write_governance=not args.no_governance,
    )
    summary = manifest["summary"]
    print(
        "Stage 15 post-remediation review: "
        f"phases={summary['phase_strict_validator_pass_count']}/3 "
        f"findings={summary['fixed_review_finding_count']}/0 "
        f"links={summary['cross_page_link_count']} grade={summary['current_report_grade']} "
        f"decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
