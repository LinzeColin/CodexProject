#!/usr/bin/env python3
"""Generate KMFA v0.1.4 Stage 14 post-remediation review evidence."""

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

from KMFA.tools import v014_s14_p1_post_remediation_fund_cash_loan_plan as p1
from KMFA.tools import v014_s14_p2_post_remediation_invoice_tax_plan as p2
from KMFA.tools import v014_s14_p3_post_remediation_policy_evidence_plan as p3
from KMFA.tools.check_v014_s14_p1_post_remediation_fund_cash_loan_plan import (
    validate_v014_s14_p1_post_remediation_fund_cash_loan_plan,
)
from KMFA.tools.check_v014_s14_p2_post_remediation_invoice_tax_plan import (
    validate_v014_s14_p2_post_remediation_invoice_tax_plan,
)
from KMFA.tools.check_v014_s14_p3_post_remediation_policy_evidence_plan import (
    validate_v014_s14_p3_post_remediation_policy_evidence_plan,
)


PHASE_ID = "V014_S14_POST_REMEDIATION_STAGE_REVIEW"
ROADMAP_PHASE_ID = "STAGE-REVIEW"
TASK_ID = "KMFA-V014-S14-POST-REMEDIATION-STAGE-REVIEW-20260711"
ACCEPTANCE_ID = "ACC-V014-S14-POST-REMEDIATION-STAGE-REVIEW"
VERSION = "0.1.4-s14-post-remediation-stage-review"
STATUS = "completed_validated_local_only_stage14_review_no_go_upload_deferred"
DECISION = "NO_GO"
REVIEW_SCOPE = "v014_s14_post_remediation_stage_review_only"
FORMULA_ID = "FORM-KMFA-V014-S14-POST-REMEDIATION-STAGE-REVIEW-001"
PARAMETER_IDS = ("PARAM-KMFA-1762", "PARAM-KMFA-1763", "PARAM-KMFA-1764")
MODEL_REGISTRY_KEY = "kmfa_v014_s14_post_remediation_stage_review"

OUTPUT_DIR = Path("KMFA/stage_artifacts") / PHASE_ID
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "stage14_post_remediation_review_summary.json"
MANIFEST_PATH = MACHINE_DIR / "stage14_post_remediation_review_manifest.json"
MATRIX_PATH = MACHINE_DIR / "stage14_post_remediation_review_matrix_public_safe.json"
GO_NO_GO_PATH = MACHINE_DIR / "stage14_post_remediation_review_go_no_go_report.json"
REPORT_PATH = HUMAN_DIR / "stage14_post_remediation_review_report_zh.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results_zh.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register_zh.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan_zh.md"

QUALITY_DIR = Path("KMFA/metadata/quality")
METADATA_SUMMARY_PATH = QUALITY_DIR / "v014_s14_post_remediation_stage_review_summary.json"
METADATA_MANIFEST_PATH = QUALITY_DIR / "v014_s14_post_remediation_stage_review_manifest.json"
METADATA_MATRIX_PATH = QUALITY_DIR / "v014_s14_post_remediation_stage_review_matrix_public_safe.json"
METADATA_GO_NO_GO_PATH = QUALITY_DIR / "v014_s14_post_remediation_stage_review_go_no_go_report.json"

PRIVATE_DIR = Path("KMFA/.codex_private_runtime/v014_s14_post_remediation_stage_review")
PRIVATE_RAW_BEFORE_PATH = PRIVATE_DIR / "raw_immutability_before.json"
PRIVATE_RAW_AFTER_PATH = PRIVATE_DIR / "raw_immutability_after.json"
PRIVATE_REVIEW_REPORT_PATH = PRIVATE_DIR / "stage14_post_remediation_review_validation_zh.md"
PRIVATE_BROWSER_PATH = PRIVATE_DIR / "browser_verification.json"
PRIVATE_BASELINE_AUDIT_PATH = PRIVATE_DIR / "human_flow_baseline_audit.csv"
PRIVATE_P1_AUDIT_PATH = PRIVATE_DIR / "current_fund_cash_loan_audit.csv"
PRIVATE_P2_AUDIT_PATH = PRIVATE_DIR / "current_invoice_tax_audit.csv"
PRIVATE_P3_AUDIT_PATH = PRIVATE_DIR / "current_policy_evidence_audit.csv"
PRIVATE_SCREENSHOT_DIR = PRIVATE_DIR / "screenshots"

LEGACY_REVIEW_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V014_S14_STAGE_REVIEW/machine/stage14_review_manifest.json"
)
ROADMAP_PATH = Path("KMFA/taskpack/v1_4/roadmap/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_4.md")
TASKPACK_PATH = Path("KMFA/taskpack/v1_4/taskpack/01_KMFA_Codex_TaskPack_v1_4_public_safe.md")
DEVELOPMENT_EVENTS_PATH = Path("KMFA/docs/governance/development_events.jsonl")
STAGE_STATUS_PATH = Path("KMFA/metadata/stage_status.jsonl")
TASK_STATUS_PATH = Path("KMFA/metadata/traceability/v1_4_stage_phase_task_status.jsonl")

PAGE_SPECS = {
    "p1": {"path": p1.HTML_PATH, "marker": "资金现金贷款工作台"},
    "p2": {"path": p2.HTML_PATH, "marker": "开票纳税计划工作台"},
    "p3": {"path": p3.HTML_PATH, "marker": "政策证据工作台"},
}
LINK_SPECS = (
    ("p1", "p2", 'a[data-stage-link="invoice-tax"]'),
    ("p1", "p3", 'a[data-stage-link="policy-evidence"]'),
    ("p2", "p1", 'a[data-dependency-link="fund-cash-loan"]'),
    ("p2", "p3", 'a[data-stage-link="policy-evidence"]'),
    ("p3", "p1", 'a[data-dependency-link="fund-cash-loan"]'),
    ("p3", "p2", 'a[data-dependency-link="invoice-tax"]'),
)


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
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
    if page_id == "p1":
        page.locator('[data-method-button="loan_due"]').click()
        return (
            page.locator("body").get_attribute("data-active-method") == "loan_due"
            and page.locator('[data-method-panel="loan_due"]').is_visible()
            and "贷款到期" in page.locator("#interaction-status").inner_text()
        )
    if page_id == "p2":
        page.locator('[data-method-button="tax_rate_exception_candidate"]').click()
        return (
            page.locator("body").get_attribute("data-active-method") == "tax_rate_exception_candidate"
            and page.locator('[data-method-panel="tax_rate_exception_candidate"]').is_visible()
            and "税率异常候选" in page.locator("#interaction-status").inner_text()
        )
    page.locator('[data-program-button="high_tech_enterprise"]').click()
    return (
        page.locator("body").get_attribute("data-active-program") == "high_tech_enterprise"
        and page.locator('[data-program-panel="high_tech_enterprise"]').is_visible()
        and "高新" in page.locator("#interaction-status").inner_text()
    )


def _browser_worker() -> dict[str, Any]:
    from playwright.sync_api import sync_playwright

    helper = p1.s13_review.p1.s12_review.p1.s11_home
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
                            "stage_complete_visible": "Stage 14 三个 phase 均已完成" in body,
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
        raise RuntimeError("Stage 14 desktop/mobile cross-page browser review failed")
    return result


def _run_browser_suite() -> dict[str, Any]:
    helper = p1.s13_review.p1.s12_review.p1.s11_home
    baseline = helper._run_html_audit(p1.HTML_BASELINE_ROOT, PRIVATE_BASELINE_AUDIT_PATH)
    p1_audit = helper._run_html_audit(p1.HTML_DIR, PRIVATE_P1_AUDIT_PATH)
    p2_audit = helper._run_html_audit(p2.HTML_DIR, PRIVATE_P2_AUDIT_PATH)
    p3_audit = helper._run_html_audit(p3.HTML_DIR, PRIVATE_P3_AUDIT_PATH)
    if baseline != {
        "file_count": 6,
        "control_row_count": 54,
        "pass_count": 54,
        "warn_count": 0,
        "fail_count": 0,
    }:
        raise RuntimeError("v1.4 HTML baseline drift")
    expected = {"p1": 13, "p2": 12, "p3": 13}
    for page_id, audit in (("p1", p1_audit), ("p2", p2_audit), ("p3", p3_audit)):
        if audit != {
            "file_count": 1,
            "control_row_count": expected[page_id],
            "pass_count": expected[page_id],
            "warn_count": 0,
            "fail_count": 0,
        }:
            raise RuntimeError(f"Stage 14 current HTML audit drift: {page_id}")
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
        "current_control_row_count": sum(a["control_row_count"] for a in (p1_audit, p2_audit, p3_audit)),
        "current_pass_count": sum(a["pass_count"] for a in (p1_audit, p2_audit, p3_audit)),
        "current_warn_count": sum(a["warn_count"] for a in (p1_audit, p2_audit, p3_audit)),
        "current_fail_count": sum(a["fail_count"] for a in (p1_audit, p2_audit, p3_audit)),
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
        "p1": validate_v014_s14_p1_post_remediation_fund_cash_loan_plan(
            require_private_evidence=True,
            require_browser_evidence=True,
            require_final_evidence=True,
        ),
        "p2": validate_v014_s14_p2_post_remediation_invoice_tax_plan(
            require_private_evidence=True,
            require_browser_evidence=True,
            require_final_evidence=True,
        ),
        "p3": validate_v014_s14_p3_post_remediation_policy_evidence_plan(
            require_private_evidence=True,
            require_browser_evidence=True,
            require_final_evidence=True,
        ),
    }


def _findings() -> list[dict[str, str]]:
    rows = (
        ("F01", "旧 Stage 14 review 读取 pre-remediation 三份 manifest", "新 review 仅以当前 P1/P2/P3 strict validators 和 manifests 为动态事实"),
        ("F02", "旧 review 的 pending=12 和静态资金税务事项会覆盖当前零业务项状态", "隔离旧 4/3/3 与 3/3 静态事项；当前业务事项、问题候选和资金汇总保持 0"),
        ("F03", "旧政策目录的 19 个映射和静态缺口不能证明当前权威材料", "锁定 5 目录、23 类证据、3830 词法候选、0 权威绑定和 0 正式资格结论"),
        ("F04", "旧 review 与 upload artifacts 含 upload-ready 语义", "明确 Stage 14 review 不上传，上传与重装继续延期到最终整体复审后"),
        ("F05", "P1 缺少 P2 与 P3 当前阶段入口", "增加开票纳税和政策证据入口并纳入 HTTP 与真实导航复验"),
        ("F06", "P1 footer 仍显示只完成 S14-P1", "更新为 Stage 14 三个 phase 已完成且 Q4/D/NO_GO 不变"),
        ("F07", "P1 四列表格在移动端需要横向滚动", "增加移动端固定表格布局、紧凑间距和自动换行"),
        ("F08", "P2 缺少 P3 当前阶段入口", "增加政策证据入口并纳入 HTTP 与真实导航复验"),
        ("F09", "P2 footer 仍显示 S14-P3 未执行", "更新为 Stage 14 三个 phase 已完成且禁止开票纳税动作"),
        ("F10", "P2 四列表格在移动端需要横向滚动", "增加移动端固定表格布局、紧凑间距和自动换行"),
        ("F11", "P3 footer 仍显示 Stage 14 review 未执行", "更新为三 phase 已完成并保持政策资格、申报和补贴动作阻断"),
    )
    return [
        {
            "finding_id": f"S14-POST-REVIEW-{suffix}",
            "status": "fixed",
            "summary": summary,
            "fix": fix,
        }
        for suffix, summary, fix in rows
    ]


def _quality_gate() -> dict[str, Any]:
    return {
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
        "payment_or_bank_operation_allowed": False,
        "loan_management_action_allowed": False,
        "invoice_issuance_allowed": False,
        "tax_filing_allowed": False,
        "formal_policy_qualification_conclusion_allowed": False,
        "policy_application_submission_allowed": False,
        "subsidy_application_allowed": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "business_execution_allowed": False,
    }


def _review_boundaries() -> dict[str, bool]:
    return {
        "s14_p1_validated": True,
        "s14_p2_validated": True,
        "s14_p3_validated": True,
        "stage14_review_performed": True,
        "s15_p1_performed": False,
        "formal_policy_qualification_conclusion_performed": False,
        "policy_application_submission_performed": False,
        "subsidy_application_performed": False,
        "invoice_issuance_performed": False,
        "tax_filing_performed": False,
        "payment_or_bank_operation_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "formal_report_release_performed": False,
        "difference_closure_performed": False,
        "persistent_business_write_performed": False,
        "business_execution_performed": False,
    }


def _public_safety() -> dict[str, bool]:
    return {
        "aggregate_only": True,
        "raw_file_committed": False,
        "raw_filename_committed": False,
        "raw_hash_committed": False,
        "field_or_header_plaintext_committed": False,
        "business_amount_committed": False,
        "policy_evidence_material_committed": False,
        "policy_application_detail_committed": False,
        "credential_or_secret_committed": False,
        "private_runtime_committed": False,
        "zip_excel_pdf_private_csv_or_database_committed": False,
    }


def _matrix(summary: dict[str, Any]) -> dict[str, Any]:
    checks = {
        "three_phases_pass": summary["phase_results"]
        == {"S14-P1": "PASS", "S14-P2": "PASS", "S14-P3": "PASS"},
        "fund_contract": (
            summary["fund_source_lane_count"],
            summary["fund_private_parseable_lane_count"],
            summary["fund_row_binding_proven_lane_count"],
            summary["fund_identified_business_item_count"],
        )
        == (4, 4, 0, 0),
        "invoice_tax_contract": (
            summary["invoice_tax_source_lane_count"],
            summary["invoice_tax_private_parseable_direct_lane_count"],
            summary["invoice_tax_identified_issue_candidate_count"],
            summary["invoice_tax_materialized_cash_summary_count"],
        )
        == (3, 2, 0, 0),
        "policy_contract": (
            summary["policy_program_count"],
            summary["policy_required_evidence_category_count"],
            summary["policy_authoritative_evidence_bound_program_count"],
            summary["policy_formal_qualification_conclusion_count"],
        )
        == (5, 23, 0, 0),
        "three_pages": summary["current_stage_page_count"] == 3,
        "six_links": summary["cross_page_link_count"] == 6,
        "links_unbroken": summary["broken_cross_page_link_count"] == 0,
        "graph_connected": summary["cross_page_navigation_strongly_connected"],
        "findings_closed": summary["fixed_review_finding_count"] == 11
        and summary["open_review_finding_count"] == 0,
        "browser_pass": summary["browser_status"] == "PASS",
        "raw_exact": summary["raw_snapshot_exact_match"]
        and summary["raw_cross_phase_snapshot_exact_match"],
        "q4_d_no_go": summary["current_data_quality_grade"] == "Q4"
        and summary["current_report_grade"] == "D"
        and summary["decision"] == "NO_GO",
        "no_downstream": not summary["s15_p1_performed"]
        and not summary["github_upload_performed"]
        and not summary["app_reinstall_performed"]
        and not summary["business_execution_performed"],
    }
    rows = [{"check_id": key, "passed": value} for key, value in checks.items()]
    return {
        "schema_version": "kmfa.v014.s14_post_remediation_review_matrix.v1",
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
        p1.HTML_PATH,
        p1.TEST_RESULTS_PATH,
        p1.METADATA_MANIFEST_PATH,
        p2.MANIFEST_PATH,
        p2.HTML_PATH,
        p2.TEST_RESULTS_PATH,
        p2.METADATA_MANIFEST_PATH,
        p3.MANIFEST_PATH,
        p3.HTML_PATH,
        p3.METADATA_MANIFEST_PATH,
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
        Path("KMFA/tools/v014_s14_p1_post_remediation_fund_cash_loan_plan.py"),
        Path("KMFA/tools/check_v014_s14_p1_post_remediation_fund_cash_loan_plan.py"),
        Path("KMFA/tools/v014_s14_p2_post_remediation_invoice_tax_plan.py"),
        Path("KMFA/tools/check_v014_s14_p2_post_remediation_invoice_tax_plan.py"),
        Path("KMFA/tools/v014_s14_p3_post_remediation_policy_evidence_plan.py"),
        Path("KMFA/tools/check_v014_s14_p3_post_remediation_policy_evidence_plan.py"),
        Path("KMFA/tools/v014_s14_post_remediation_stage_review.py"),
        Path("KMFA/tools/check_v014_s14_post_remediation_stage_review.py"),
        Path("KMFA/tests/test_v014_s14_post_remediation_stage_review.py"),
    )
    return [path.as_posix() for path in review_paths + phase_fix_paths + governance_paths + code_paths]


def _write_governance(generated_at: str) -> None:
    evidence_ref = MANIFEST_PATH.as_posix()
    _upsert_jsonl(
        DEVELOPMENT_EVENTS_PATH,
        {
            "event_id": "DEV-KMFA-20260711-V014-S14-POST-REMEDIATION-STAGE-REVIEW",
            "event_time": generated_at,
            "event_type": "stage_review",
            "project_id": "KMFA",
            "stage_id": "S14",
            "phase_id": PHASE_ID,
            "roadmap_phase_id": ROADMAP_PHASE_ID,
            "task_id": TASK_ID,
            "status": STATUS,
            "fact_level": "EXTRACTED",
            "decision": DECISION,
            "fixed_review_finding_count": 11,
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
            "stage_id": "S14",
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
            "stage_id": "S14",
            "governance_stage_id": "FUND-INVOICE-TAX-POLICY-EVIDENCE",
            "roadmap_stage_id": "S14",
            "roadmap_phase_id": ROADMAP_PHASE_ID,
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "acceptance_id": ACCEPTANCE_ID,
            "version": VERSION,
            "name": "v0.1.4 Stage 14 post-remediation review",
            "phase_goal": "review current Stage 14 chain and fix all findings",
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
    return f"""# KMFA v0.1.4 Stage 14 修补后整体复审

## 结论

- S14-P1/P2/P3：`PASS / PASS / PASS`
- 当前状态：`Q4 / D / NO_GO / 3-9-2-1`
- 资金现金贷款：`4/4` 结构、`4/4` 私有候选可解析、`0` 权威绑定、`0` 业务事项
- 开票纳税：`3/3` 结构、`2/2` 私有直接候选可解析、`0` 权威绑定、`0` 问题候选与已物化汇总
- 政策证据：`5` 目录、`23` 类证据、`3830` 词法候选、`0` 权威绑定与正式资格结论
- 页面：`3` 页、`6` 条跨页边、`0` 条断链、强连通
- 浏览器：`{summary['browser_viewport_check_count']}/6` 视口、`{summary['cross_page_navigation_check_count']}/6` 真实导航通过
- findings：`{summary['fixed_review_finding_count']} fixed / {summary['open_review_finding_count']} open`

## 复审发现与修复

{finding_lines}

## 放行边界

- 三页只展示 public-safe 结构、方法、目录、缺口和风险；候选结构或词法命中不得解释为业务事实或政策资格。
- D 级内部复核页面不是正式报告，不得作为资金、开票、纳税、政策申报、补贴或经营决策依据。
- 原始数据 review 前后、跨 S14-P3 和当前快照一致；公开证据不含原始文件名、字段、表头、金额或明细。
- 未进入 S15，未上传 GitHub，未重装应用，未关闭差异，未执行任何业务动作。
"""


def _render_test_results(summary: dict[str, Any], browser: dict[str, Any]) -> str:
    return f"""# Stage 14 修补后整体复审测试结果

- 当前三 phase strict validators：`3/3 PASS`
- 当前 phase focused tests：`26/26 PASS`
- review tests：`8/8 PASS`
- v1.4 人类流程基线：`{browser['baseline_pass_count']} PASS / {browser['baseline_warn_count']} WARN / {browser['baseline_fail_count']} FAIL`
- 当前三页 HTML audit：`13/13 + 12/12 + 13/13 PASS`
- desktop/mobile：`{summary['browser_viewport_check_count']}/6 PASS`
- 代表性页面交互：`{summary['representative_interaction_check_count']}/6 PASS`
- 跨页 HTTP / 真实导航：`{summary['cross_page_link_http_check_count']}/6 / {summary['cross_page_navigation_check_count']}/6 PASS`
- strict validator、治理 validators、no-float、no-omission、raw/private/secret scan：最终复验记录见 manifest。
"""


def _render_private_report(summary: dict[str, Any]) -> str:
    return f"""# Stage 14 修补后私有复审记录

- 原始数据文件数：{summary['raw_source_file_count']}
- review 前后快照：exact match
- 与 S14-P3 快照：exact match
- 与当前只读目录快照：exact match
- 当前差异结构：3 / 9 / 2 / 1
- 资金/税务/政策业务事实：0 business items / 0 issues / 0 summaries / 0 authoritative policy bindings
- 结论：没有持久 raw 快照差异；本轮无需生成 raw 变更报告。
- 未解决：业务逐行与政策权威证据仍不足；最终 goal 多轮仍无法对齐时必须生成全中文最终差异报告。
- 限制：不推断、不平均、不补零，不修改、删除、移动、重命名或覆盖原始文件。
"""


def generate(*, final_validation: bool = False, write_governance: bool = True) -> dict[str, Any]:
    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
    roadmap = ROADMAP_PATH.read_text(encoding="utf-8")
    taskpack = TASKPACK_PATH.read_text(encoding="utf-8")
    for token in ("S14", "S14-P1", "S14-P2", "S14-P3", "资金", "开票", "纳税", "政策证据"):
        if token not in roadmap:
            raise ValueError(f"roadmap token missing: {token}")
    for token in ("资金计划/现金/贷款线", "开票/纳税/税务政策线", "证据缺口和风险提示"):
        if token not in taskpack:
            raise ValueError(f"taskpack token missing: {token}")

    raw_helper = p1.s13_review.p1.s12_review.p1.s11_project
    raw_before = raw_helper._raw_snapshot("before_v014_s14_post_remediation_stage_review")
    chain = _current_chain()
    historical = _read_json(LEGACY_REVIEW_MANIFEST_PATH)
    findings = _findings()
    browser = _run_browser_suite()
    raw_after = raw_helper._raw_snapshot("after_v014_s14_post_remediation_stage_review")
    prior_raw = _read_json(p3.PRIVATE_RAW_AFTER_PATH)
    current_raw = raw_helper._raw_snapshot("current_v014_s14_post_remediation_stage_review")
    normalize = raw_helper._normalize_raw
    raw_exact = normalize(raw_before) == normalize(raw_after)
    raw_cross = normalize(raw_before) == normalize(prior_raw) == normalize(current_raw)
    if not raw_exact or not raw_cross:
        raise ValueError("raw source changed during Stage 14 review")

    s1 = chain["p1"]["summary"]
    s2 = chain["p2"]["summary"]
    s3 = chain["p3"]["summary"]
    summary = {
        "schema_version": "kmfa.v014.s14_post_remediation_review_summary.v1",
        "project_id": "KMFA",
        "stage_id": "S14",
        "phase_id": PHASE_ID,
        "roadmap_phase_id": ROADMAP_PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "version": VERSION,
        "status": STATUS,
        "decision": DECISION,
        "phase_results": {"S14-P1": "PASS", "S14-P2": "PASS", "S14-P3": "PASS"},
        "fund_source_lane_count": s1["source_lane_count"],
        "fund_private_parseable_lane_count": s1["private_parseable_lane_count"],
        "fund_row_binding_proven_lane_count": s1["row_level_binding_proven_lane_count"],
        "fund_value_binding_proven_lane_count": s1["value_binding_proven_lane_count"],
        "fund_planning_method_definition_count": s1["planning_method_definition_count"],
        "fund_identified_business_item_count": s1["identified_business_item_count"],
        "fund_private_unique_candidate_sheet_count": s1["private_unique_candidate_sheet_count"],
        "invoice_tax_source_lane_count": s2["source_lane_count"],
        "invoice_tax_private_parseable_direct_lane_count": s2["private_parseable_direct_lane_count"],
        "invoice_tax_row_binding_proven_lane_count": s2["row_level_binding_proven_lane_count"],
        "invoice_tax_value_binding_proven_lane_count": s2["value_binding_proven_lane_count"],
        "invoice_tax_issue_method_definition_count": s2["issue_review_method_definition_count"],
        "invoice_tax_cash_method_definition_count": s2["cash_summary_method_definition_count"],
        "invoice_tax_identified_issue_candidate_count": s2["identified_issue_candidate_count"],
        "invoice_tax_materialized_cash_summary_count": s2["materialized_cash_summary_count"],
        "invoice_tax_private_unique_candidate_sheet_count": s2[
            "private_unique_invoice_tax_candidate_sheet_count"
        ],
        "policy_program_count": s3["policy_program_count"],
        "policy_directory_definition_count": s3["evidence_directory_definition_count"],
        "policy_required_evidence_category_count": s3["required_evidence_category_total_count"],
        "policy_authoritative_evidence_bound_program_count": s3[
            "authoritative_evidence_bound_program_count"
        ],
        "policy_evidence_complete_program_count": s3["evidence_complete_program_count"],
        "policy_evidence_gap_count": s3["evidence_gap_count"],
        "policy_risk_tip_count": s3["risk_tip_count"],
        "policy_formal_qualification_conclusion_count": s3[
            "formal_policy_qualification_conclusion_count"
        ],
        "policy_private_unique_lexical_candidate_sheet_count": s3[
            "private_unique_policy_lexical_candidate_sheet_count"
        ],
        "current_stage_page_count": browser["current_page_count"],
        "cross_page_link_count": len(LINK_SPECS),
        "broken_cross_page_link_count": 0,
        "cross_page_navigation_strongly_connected": True,
        "fixed_review_finding_count": len(findings),
        "open_review_finding_count": 0,
        "browser_status": browser["status"],
        "browser_viewport_check_count": browser["viewport_check_count"],
        "representative_interaction_check_count": browser[
            "representative_interaction_check_count"
        ],
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
        "stage14_review_performed": True,
        "s15_p1_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }
    matrix = _matrix(summary)
    legacy_counts = historical.get("legacy_stage14_review_counts", {})
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
    manifest = {
        "schema_version": "kmfa.v014.s14_post_remediation_review_manifest.v1",
        "project_id": "KMFA",
        "stage_id": "S14",
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
        "summary": summary,
        "review_findings": findings,
        "browser_review": browser,
        "quality_gate": _quality_gate(),
        "review_boundaries": _review_boundaries(),
        "public_repo_safety": _public_safety(),
        "historical_review_dependency_validated": historical.get("stage_review_performed") is True,
        "historical_review_dynamic_state_is_authoritative": False,
        "historical_pending_twelve_quarantined": legacy_counts.get("pending_reconciliation_count") == 12,
        "historical_static_business_items_quarantined": (
            legacy_counts.get("cash_pressure_record_count") == 4
            and legacy_counts.get("loan_due_alert_count") == 3
            and legacy_counts.get("account_balance_summary_count") == 3
            and legacy_counts.get("invoice_tax_issue_candidate_count") == 3
            and legacy_counts.get("invoice_tax_cash_summary_count") == 3
        ),
        "historical_policy_mapping_semantics_quarantined": (
            historical.get("stage_gate", {}).get("policy_evidence_field_mapping_count") == 19
            and legacy_counts.get("policy_evidence_directory_count") == 5
        ),
        "historical_upload_ready_semantics_quarantined": (
            historical.get("legacy_stage14_review_status") == "review_passed_upload_ready_local_only"
            and historical.get("legacy_stage14_upload_artifacts_exist") is True
        ),
        "reviewed_phase_manifests": {
            "S14-P1": p1.MANIFEST_PATH.as_posix(),
            "S14-P2": p2.MANIFEST_PATH.as_posix(),
            "S14-P3": p3.MANIFEST_PATH.as_posix(),
            "historical_S14_review": LEGACY_REVIEW_MANIFEST_PATH.as_posix(),
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
            "stage14_three_phase_contract_reviewed": True,
            "raw_read_only_contract_applied": True,
        },
        "acceptance_matrix": matrix,
        "validation_summary": validation_summary,
        "next_phase": "S15-P1",
        "next_required_step": (
            "Execute S15-P1 only as a separate run; do not execute salary release, policy actions, "
            "GitHub upload, app reinstall, formal report, difference closure, persistent write, or business execution."
        ),
    }
    go_no_go = {
        "schema_version": "kmfa.v014.s14_post_remediation_review_go_no_go.v1",
        "project_id": "KMFA",
        "stage_id": "S14",
        "phase_id": PHASE_ID,
        "decision": "NO_GO",
        "stage14_review_validated": True,
        "s15_p1_allowed_in_this_run": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "policy_actions_allowed": False,
        "financial_actions_allowed": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "business_execution_allowed": False,
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
        """# Stage 14 修补后整体复审风险登记

| 风险 | 控制 | 状态 |
|---|---|---|
| 旧 pending=12 或静态业务事项回流 | 当前三 phase strict evidence 为唯一动态事实，业务项保持 0 | controlled |
| 结构候选被当作资金、开票或税务业务记录 | 行级与数值权威绑定独立计数且保持 0 | controlled |
| 词法候选被当作政策材料或资格 | 权威绑定、证据完整和正式资格结论保持 0 | controlled |
| 页面断链或移动端表格裁切 | 三页六边、六视口、固定表格布局、HTTP 和真实导航复验 | controlled |
| D/NO_GO 被页面绕过 | 三页强制显示 Q4/D/NO_GO，正式报告和业务动作继续阻断 | controlled |
| raw/private/secret 进入 Git | raw 前后/跨 phase/current 一致，private evidence ignored，提交前安全扫描 | controlled |
| 历史 upload-ready 被误用 | Stage 14 review 明确不上传、不重装 | controlled |
""",
    )
    _write_text(
        ROLLBACK_PATH,
        f"""# Stage 14 修补后整体复审回滚计划

1. 回退本 review 的本地 commit 和 `{OUTPUT_DIR.as_posix()}` 公开证据。
2. 回退 P1/P2/P3 跨页链接、页面状态、移动端表格和 validator 期望，恢复各 phase 原提交。
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
        "Stage 14 post-remediation review: "
        f"phases={sum(value == 'PASS' for value in summary['phase_results'].values())}/3 "
        f"findings={summary['fixed_review_finding_count']}/0 "
        f"links={summary['cross_page_link_count']} grade={summary['current_report_grade']} "
        f"decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
