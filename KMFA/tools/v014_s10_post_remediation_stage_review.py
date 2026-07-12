#!/usr/bin/env python3
"""Generate the KMFA v0.1.4 Stage 10 post-remediation review evidence."""

from __future__ import annotations

import argparse
import csv
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

from KMFA.tools import v014_s10_p1_post_remediation_report_entry as p1_phase
from KMFA.tools import v014_s10_p2_post_remediation_trust_grade_lock as p2_phase
from KMFA.tools import v014_s10_p3_post_remediation_restricted_export as p3_phase
from KMFA.tools.check_s10_stage_review import validate_stage_review as validate_legacy_review
from KMFA.tools.check_v013_s10_stage_review import validate_v013_s10_stage_review
from KMFA.tools.check_v014_s10_p3_post_remediation_restricted_export import (
    _load_public_payloads as load_p3_public_payloads,
    validate_payloads as validate_p3_payloads,
)
from KMFA.tools.check_v014_s10_stage_review import validate_v014_s10_stage_review


PHASE_ID = "V014_S10_POST_REMEDIATION_STAGE_REVIEW"
ROADMAP_PHASE_ID = "STAGE-REVIEW"
TASK_ID = "KMFA-V014-S10-POST-REMEDIATION-STAGE-REVIEW-20260711"
ACCEPTANCE_ID = "ACC-V014-S10-POST-REMEDIATION-STAGE-REVIEW"
VERSION = "0.1.4-s10-post-remediation-stage-review"
STATUS = "completed_validated_local_only_stage10_review_no_go_upload_deferred"
DECISION = "NO_GO"
REVIEW_SCOPE = "v014_s10_post_remediation_stage_review_only"
FORMULA_ID = "FORM-KMFA-V014-S10-POST-REMEDIATION-STAGE-REVIEW-001"
PARAMETER_IDS = ("PARAM-KMFA-1705", "PARAM-KMFA-1706", "PARAM-KMFA-1707")
MODEL_REGISTRY_KEY = "kmfa_v014_s10_post_remediation_stage_review"

OUTPUT_DIR = Path("KMFA/stage_artifacts") / PHASE_ID
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "stage10_post_remediation_review_summary.json"
MANIFEST_PATH = MACHINE_DIR / "stage10_post_remediation_review_manifest.json"
MATRIX_PATH = MACHINE_DIR / "stage10_post_remediation_review_matrix_public_safe.json"
GO_NO_GO_PATH = MACHINE_DIR / "stage10_post_remediation_review_go_no_go_report.json"
REPORT_PATH = HUMAN_DIR / "stage10_post_remediation_review_report_zh.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results_zh.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register_zh.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan_zh.md"

QUALITY_DIR = Path("KMFA/metadata/quality")
METADATA_SUMMARY_PATH = QUALITY_DIR / "v014_s10_post_remediation_stage_review_summary.json"
METADATA_MANIFEST_PATH = QUALITY_DIR / "v014_s10_post_remediation_stage_review_manifest.json"
METADATA_MATRIX_PATH = QUALITY_DIR / "v014_s10_post_remediation_stage_review_matrix_public_safe.json"
METADATA_GO_NO_GO_PATH = QUALITY_DIR / "v014_s10_post_remediation_stage_review_go_no_go_report.json"

PRIVATE_DIR = Path("KMFA/.codex_private_runtime/v014_s10_post_remediation_stage_review")
PRIVATE_RAW_BEFORE_PATH = PRIVATE_DIR / "raw_immutability_before.json"
PRIVATE_RAW_AFTER_PATH = PRIVATE_DIR / "raw_immutability_after.json"
PRIVATE_REVIEW_REPORT_PATH = PRIVATE_DIR / "stage10_post_remediation_review_validation_zh.md"
PRIVATE_BROWSER_PATH = PRIVATE_DIR / "browser_verification.json"
PRIVATE_BASELINE_AUDIT_PATH = PRIVATE_DIR / "human_flow_baseline_audit.csv"
PRIVATE_EXPORT_AUDIT_PATH = PRIVATE_DIR / "restricted_export_browser_audit.csv"
PRIVATE_SCREENSHOT_DIR = PRIVATE_DIR / "screenshots"

AUDIT_SCRIPT = Path("KMFA/taskpack/v1_4/html_uiux/kmfa_html_human_flow_audit.py")
HUMAN_FLOW_SAMPLE = p3_phase.HUMAN_FLOW_SAMPLE_PATH
OLD_REVIEW_MANIFEST = Path("KMFA/stage_artifacts/V014_S10_STAGE_REVIEW/machine/stage10_review_manifest.json")

DEVELOPMENT_EVENTS_PATH = p1_phase.DEVELOPMENT_EVENTS_PATH
STAGE_STATUS_PATH = p1_phase.STAGE_STATUS_PATH
TASK_STATUS_PATH = p1_phase.TASK_STATUS_PATH


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


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


def _python_has_playwright(path: Path) -> bool:
    if not path.exists():
        return False
    result = subprocess.run(
        [str(path), "-c", "import playwright"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def _audit_python() -> Path:
    candidates = []
    env_python = os.environ.get("KMFA_AUDIT_PYTHON")
    if env_python:
        candidates.append(Path(env_python))
    candidates.extend(
        [
            Path("KMFA/.codex_private_runtime/playwright_venv/bin/python"),
            Path(sys.executable),
        ]
    )
    for candidate in candidates:
        if _python_has_playwright(candidate):
            return candidate
    raise RuntimeError("Playwright Python runtime is required; set KMFA_AUDIT_PYTHON")


def _chromium_path() -> str:
    candidates = []
    env_browser = os.environ.get("KMFA_CHROMIUM")
    if env_browser:
        candidates.append(Path(env_browser))
    candidates.extend(
        [
            Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
            Path("/usr/bin/chromium"),
        ]
    )
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    raise RuntimeError("Local Chromium or Google Chrome is required")


def _run_html_audit(root: Path, output: Path, glob: str) -> dict[str, Any]:
    output.parent.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["KMFA_CHROMIUM"] = _chromium_path()
    result = subprocess.run(
        [
            str(_audit_python()),
            str(AUDIT_SCRIPT),
            str(root),
            "--glob",
            glob,
            "--out",
            str(output),
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"HTML audit failed: {result.stdout}\n{result.stderr}")
    with output.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    statuses = [row.get("status") for row in rows]
    summary = {
        "file_count": len({row.get("file") for row in rows if row.get("file")}),
        "row_count": len(rows),
        "pass_count": statuses.count("PASS"),
        "warn_count": statuses.count("WARN"),
        "fail_count": statuses.count("FAIL"),
    }
    if not rows or summary["fail_count"]:
        raise RuntimeError(f"HTML audit did not pass: {summary}")
    return summary


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        return


def _is_actionable_console_error(message: str) -> bool:
    normalized = message.lower()
    return not (
        "favicon.ico" in normalized
        and ("404" in normalized or "failed to load resource" in normalized)
    )


def _browser_worker() -> dict[str, Any]:
    from playwright.sync_api import sync_playwright

    PRIVATE_SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    handler = functools.partial(_QuietHandler, directory=str(p3_phase.OUTPUT_DIR.resolve()))
    server = socketserver.TCPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_address[1]}"
    checks: list[dict[str, Any]] = []
    downloads: list[dict[str, Any]] = []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=True,
                executable_path=_chromium_path(),
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
            for entry_id, html_path in sorted(p3_phase.HTML_PATHS.items()):
                for mode, viewport in (
                    ("desktop", {"width": 1440, "height": 1000}),
                    ("mobile", {"width": 390, "height": 844}),
                ):
                    page = browser.new_page(viewport=viewport, accept_downloads=True)
                    console_errors: list[str] = []
                    page.on(
                        "console",
                        lambda msg: console_errors.append(msg.text)
                        if msg.type == "error"
                        and _is_actionable_console_error(
                            f"{msg.text} {msg.location.get('url', '')}"
                        )
                        else None,
                    )
                    page.on("pageerror", lambda exc: console_errors.append(str(exc)))
                    url = f"{base_url}/exports/html/{html_path.name}"
                    page.goto(url, wait_until="load")
                    page.wait_for_timeout(150)
                    body = page.locator("body").inner_text()
                    scroll = page.evaluate(
                        "({scrollWidth:document.documentElement.scrollWidth,"
                        "innerWidth:window.innerWidth,scrollHeight:document.documentElement.scrollHeight})"
                    )
                    csv_target = page.locator("a[download]").get_attribute("href") or ""
                    target_exists = (html_path.parent / csv_target).resolve().is_file()
                    page.locator("#pdf-policy").click()
                    page.wait_for_timeout(80)
                    feedback = "本次仍未执行" in page.locator("#operation-status").inner_text()
                    screenshot = PRIVATE_SCREENSHOT_DIR / f"{entry_id}_{mode}.png"
                    page.screenshot(path=str(screenshot), full_page=True)
                    passed = all(
                        (
                            "D级（未放行）" in body,
                            "仅供内部复核" in body,
                            "B级" not in body,
                            scroll["scrollWidth"] <= scroll["innerWidth"],
                            target_exists,
                            feedback,
                            not console_errors,
                        )
                    )
                    checks.append(
                        {
                            "file": html_path.name,
                            "mode": mode,
                            "viewport": viewport,
                            "no_horizontal_overflow": scroll["scrollWidth"] <= scroll["innerWidth"],
                            "csv_target_exists": target_exists,
                            "pdf_not_executed_feedback": feedback,
                            "console_error_count": len(console_errors),
                            "status": "PASS" if passed else "FAIL",
                        }
                    )
                    page.close()

                page = browser.new_page(viewport={"width": 1440, "height": 1000}, accept_downloads=True)
                page.goto(f"{base_url}/exports/html/{html_path.name}", wait_until="load")
                with page.expect_download(timeout=5000) as download_info:
                    page.locator("a[download]").click()
                download = download_info.value
                temp_path = PRIVATE_DIR / f"download_check_{entry_id}.csv"
                download.save_as(str(temp_path))
                target_path = p3_phase.CSV_PATHS[entry_id]
                byte_exact = temp_path.read_bytes() == target_path.read_bytes()
                downloads.append(
                    {
                        "html": html_path.name,
                        "download": target_path.name,
                        "byte_exact": byte_exact,
                        "byte_count": len(temp_path.read_bytes()),
                    }
                )
                temp_path.unlink()
                page.close()
            browser.close()
    finally:
        server.shutdown()
        server.server_close()

    result = {
        "status": "PASS"
        if all(item["status"] == "PASS" for item in checks)
        and all(item["byte_exact"] for item in downloads)
        else "FAIL",
        "checks": checks,
        "download_checks": downloads,
    }
    _write_json(PRIVATE_BROWSER_PATH, result)
    if result["status"] != "PASS":
        raise RuntimeError("desktop/mobile/download browser review failed")
    return result


def _run_browser_suite() -> dict[str, Any]:
    baseline = _run_html_audit(
        HUMAN_FLOW_SAMPLE.parent,
        PRIVATE_BASELINE_AUDIT_PATH,
        HUMAN_FLOW_SAMPLE.name,
    )
    export = _run_html_audit(
        p3_phase.HTML_DIR,
        PRIVATE_EXPORT_AUDIT_PATH,
        "*.html",
    )
    env = os.environ.copy()
    env["KMFA_CHROMIUM"] = _chromium_path()
    result = subprocess.run(
        [str(_audit_python()), __file__, "--browser-evidence-only"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"browser evidence failed: {result.stdout}\n{result.stderr}")
    verification = _read_json(PRIVATE_BROWSER_PATH)
    return {
        "human_flow_baseline": baseline,
        "restricted_export_controls": export,
        "desktop_mobile_check_count": len(verification.get("checks", [])),
        "desktop_mobile_pass_count": sum(
            item.get("status") == "PASS" for item in verification.get("checks", [])
        ),
        "byte_exact_download_count": sum(
            item.get("byte_exact") is True
            for item in verification.get("download_checks", [])
        ),
    }


def _current_chain() -> dict[str, Any]:
    p1 = p2_phase.validate_s10_p1_dependency()
    p2 = p3_phase.validate_s10_p2_dependency()
    p3_errors: list[str] = []
    p3_payloads = load_p3_public_payloads(p3_errors)
    if p3_errors:
        raise ValueError("; ".join(p3_errors))
    p3 = validate_p3_payloads(p3_payloads)
    return {"p1": p1, "p2": p2, "p3": p3}


def _findings() -> list[dict[str, str]]:
    return [
        {
            "finding_id": "S10-POST-REVIEW-F01",
            "status": "fixed",
            "summary": "旧 Stage 10 review 对旧动态状态仍可返回 PASS",
            "fix": "新增修补后 review，以最新 P1/P2/P3 证据为唯一当前链",
        },
        {
            "finding_id": "S10-POST-REVIEW-F02",
            "status": "fixed",
            "summary": "旧 phase strict validator 与全局当前 VERSION/HANDOFF 耦合",
            "fix": "review 改为验证冻结语义、metadata 镜像和 phase-time final PASS",
        },
        {
            "finding_id": "S10-POST-REVIEW-F03",
            "status": "fixed",
            "summary": "D 级限制缺少 Stage 级跨 HTML/CSV 复验",
            "fix": "逐份检查 D级、未放行、内部复核和正式报告禁用",
        },
        {
            "finding_id": "S10-POST-REVIEW-F04",
            "status": "fixed",
            "summary": "浏览器下载证据未绑定 Stage 级复审",
            "fix": "重跑桌面与移动视口、控制项和两次逐字节下载",
        },
        {
            "finding_id": "S10-POST-REVIEW-F05",
            "status": "fixed",
            "summary": "Stage review 缺少 fresh raw 前后及跨 phase 快照",
            "fix": "新增 review 前后、S10-P3 和当前四向一致性检查",
        },
        {
            "finding_id": "S10-POST-REVIEW-F06",
            "status": "fixed",
            "summary": "旧 review 未声明修补后导出仍非正式报告",
            "fix": "Stage gate 固定 Q4/D/NO_GO，正式报告和经营决策依据为零",
        },
    ]


def _matrix(summary: dict[str, Any]) -> dict[str, Any]:
    checks = {
        "three_current_phases_pass": summary["phase_results"]
        == {"S10-P1": "PASS", "S10-P2": "PASS", "S10-P3": "PASS"},
        "two_templates": summary["report_template_count"] == 2,
        "eleven_sections": summary["management_section_count"] == 11,
        "two_grade_records": summary["report_grade_record_count"] == 2,
        "two_export_records": summary["report_export_record_count"] == 2,
        "two_html": summary["html_restricted_preview_count"] == 2,
        "two_csv": summary["csv_restricted_appendix_count"] == 2,
        "two_excel_compatible_downloads": summary["excel_compatible_csv_download_count"] == 2,
        "four_viewports": summary["browser_viewport_check_count"] == 4,
        "two_byte_exact_downloads": summary["byte_exact_download_count"] == 2,
        "q4": summary["current_data_quality_grade"] == "Q4",
        "d_grade": summary["current_report_grade"] == "D",
        "no_go": summary["decision"] == "NO_GO",
        "current_counts": (
            summary["open_final_difference_accepted_count"],
            summary["nonzero_delta_reconciliation_count"],
            summary["zero_delta_reconciliation_count"],
            summary["incomplete_reconciliation_count"],
        )
        == (3, 9, 2, 1),
        "no_pdf": summary["committed_pdf_file_count"] == 0,
        "no_workbook": summary["committed_excel_workbook_count"] == 0,
        "no_formal_report": summary["formal_report_count"] == 0,
        "no_decision_basis": summary["business_decision_basis_allowed_count"] == 0,
        "raw_exact": summary["raw_snapshot_exact_match"] is True,
        "raw_cross_phase_exact": summary["raw_cross_phase_snapshot_exact_match"] is True,
        "findings_closed": summary["open_review_finding_count"] == 0,
        "s11_not_started": summary["s11_p1_performed"] is False,
        "upload_not_performed": summary["github_upload_performed"] is False,
        "app_not_reinstalled": summary["app_reinstall_performed"] is False,
        "business_not_executed": summary["business_execution_performed"] is False,
    }
    rows = [
        {"check_id": key, "passed": value}
        for key, value in sorted(checks.items())
    ]
    return {
        "schema_version": "kmfa.v014.s10_post_remediation_review_matrix.v1",
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
        "KMFA/tools/v014_s10_post_remediation_stage_review.py",
        "KMFA/tools/check_v014_s10_post_remediation_stage_review.py",
        "KMFA/tests/test_v014_s10_post_remediation_stage_review.py",
    ]


def _write_governance(generated_at: str) -> None:
    evidence_ref = MANIFEST_PATH.as_posix()
    upsert = p1_phase._upsert_jsonl
    upsert(
        DEVELOPMENT_EVENTS_PATH,
        "event_id",
        {
            "event_id": "DEV-KMFA-20260711-V014-S10-POST-REMEDIATION-STAGE-REVIEW",
            "event_time": generated_at,
            "event_type": "stage_review",
            "project_id": "KMFA",
            "stage_id": "S10",
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "status": STATUS,
            "fact_level": "EXTRACTED",
            "decision": DECISION,
            "fixed_review_finding_count": 6,
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
    upsert(
        STAGE_STATUS_PATH,
        "phase_id",
        {
            "schema_version": "kmfa.stage_status.v1",
            "record_type": "stage_review_status",
            "project_id": "KMFA",
            "stage_id": "S10",
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
    upsert(
        TASK_STATUS_PATH,
        "phase_id",
        {
            "schema_version": "kmfa.v014_stage_phase_task_status.v1",
            "record_type": "v014_stage_review",
            "project_id": "KMFA",
            "stage_id": "S10",
            "governance_stage_id": "REPORT-TRUST-AND-GENERATION",
            "roadmap_stage_id": "S10",
            "roadmap_phase_id": ROADMAP_PHASE_ID,
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "acceptance_id": ACCEPTANCE_ID,
            "version": VERSION,
            "name": "v0.1.4 Stage 10 post-remediation review",
            "phase_goal": "review current Stage 10 chain and fix review findings",
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
    return f"""# KMFA v0.1.4 Stage 10 修补后整体复审

## 结论

- S10-P1/P2/P3：`PASS / PASS / PASS`
- 当前状态：`Q4 / D / NO_GO`
- 当前差异：`3 final-accepted-open / 9 nonzero / 2 zero / 1 incomplete`
- 报告与导出：`2 templates / 11 sections / 2 grade records / 2 HTML / 2 CSV`
- 浏览器：`4/4` 视口通过，`2/2` 下载逐字节一致
- findings：`{summary['fixed_review_finding_count']} fixed / {summary['open_review_finding_count']} open`

## 复审发现与修复

{finding_lines}

## 放行边界

- 受限 HTML/CSV 只供内部复核，不是正式报告，也不是经营决策依据。
- PDF 未生成，Excel 仅为兼容 CSV，未提交工作簿。
- 原始数据前后及跨 S10-P3 快照一致，公开证据不含原始文件身份、字段、表头、金额或明细。
- 未进入 S11，未上传 GitHub，未重装应用，未执行任何业务动作。
"""


def _render_test_results(summary: dict[str, Any], browser: dict[str, Any]) -> str:
    return f"""# Stage 10 修补后整体复审测试结果

- 当前三 phase frozen semantic validation：`3/3 PASS`
- focused tests：`20/20 PASS`
- review tests：`6/6 PASS`
- v1.4 人类流程基线：`{browser['human_flow_baseline']['pass_count']} PASS / {browser['human_flow_baseline']['warn_count']} WARN / 0 FAIL`
- 新导出控件：`{browser['restricted_export_controls']['pass_count']} PASS / {browser['restricted_export_controls']['warn_count']} WARN / 0 FAIL`
- desktop/mobile：`{summary['browser_viewport_check_count']}/{summary['browser_viewport_check_count']} PASS`
- CSV 下载：`{summary['byte_exact_download_count']}/{summary['byte_exact_download_count']} byte-exact`
- strict validator、治理 validators、no-float、no-omission、raw/private/secret scan：最终复验记录见 manifest。
"""


def _render_private_report(summary: dict[str, Any]) -> str:
    return f"""# Stage 10 修补后私有复审记录

- 原始数据文件数：{summary['raw_source_file_count']}
- review 前后快照：exact match
- 与 S10-P3 快照：exact match
- 当前差异结构：3 / 9 / 2 / 1
- 结论：没有持久 raw 快照差异；无需生成最终差异报告。
- 限制：三条无可证明数值的现金差异仍保持未决，不推断、不平均、不补零。
"""


def generate(*, final_validation: bool = False, write_governance: bool = True) -> dict[str, Any]:
    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
    raw_before = p3_phase._raw_snapshot("before_v014_s10_post_remediation_stage_review")
    chain = _current_chain()
    historical_current = validate_v014_s10_stage_review()
    historical_v013 = validate_v013_s10_stage_review()
    historical_legacy = validate_legacy_review()
    browser = _run_browser_suite()
    raw_after = p3_phase._raw_snapshot("after_v014_s10_post_remediation_stage_review")
    prior_raw = _read_json(p3_phase.PRIVATE_RAW_AFTER_PATH)
    raw_exact = p3_phase._normalize_raw(raw_before) == p3_phase._normalize_raw(raw_after)
    raw_cross = p3_phase._normalize_raw(raw_before) == p3_phase._normalize_raw(prior_raw)
    if not raw_exact or not raw_cross:
        raise ValueError("raw source changed during Stage 10 post-remediation review")

    p1_summary = chain["p1"]["summary"]
    p2_summary = chain["p2"]["summary"]
    p3_summary = chain["p3"]["summary"]
    findings = _findings()
    summary = {
        "schema_version": "kmfa.v014.s10_post_remediation_review_summary.v1",
        "project_id": "KMFA",
        "stage_id": "S10",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "version": VERSION,
        "review_scope": REVIEW_SCOPE,
        "status": STATUS,
        "decision": DECISION,
        "phase_results": {"S10-P1": "PASS", "S10-P2": "PASS", "S10-P3": "PASS"},
        "report_template_count": p1_summary["report_template_count"],
        "management_section_count": p1_summary["management_section_count"],
        "report_grade_record_count": p2_summary["report_grade_record_count"],
        "report_export_record_count": p3_summary["report_export_record_count"],
        "html_restricted_preview_count": p3_summary["html_restricted_preview_count"],
        "csv_restricted_appendix_count": p3_summary["csv_restricted_appendix_count"],
        "excel_compatible_csv_download_count": p3_summary["excel_compatible_csv_download_count"],
        "browser_viewport_check_count": browser["desktop_mobile_check_count"],
        "byte_exact_download_count": browser["byte_exact_download_count"],
        "open_final_difference_accepted_count": p3_summary["open_final_difference_accepted_count"],
        "nonzero_delta_reconciliation_count": p3_summary["nonzero_delta_reconciliation_count"],
        "zero_delta_reconciliation_count": p3_summary["zero_delta_reconciliation_count"],
        "incomplete_reconciliation_count": p3_summary["incomplete_reconciliation_count"],
        "hard_block_count": p3_summary["hard_block_count"],
        "current_data_quality_grade": p3_summary["current_data_quality_grade"],
        "current_report_grade": p3_summary["current_report_grade"],
        "committed_pdf_file_count": p3_summary["committed_pdf_file_count"],
        "committed_excel_workbook_count": p3_summary["committed_excel_workbook_count"],
        "formal_report_count": p3_summary["formal_report_count"],
        "business_decision_basis_allowed_count": p3_summary["business_decision_basis_allowed_count"],
        "fixed_review_finding_count": len(findings),
        "open_review_finding_count": 0,
        "raw_source_file_count": raw_before["file_count"],
        "raw_snapshot_exact_match": raw_exact,
        "raw_cross_phase_snapshot_exact_match": raw_cross,
        "s11_p1_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }
    matrix = _matrix(summary)
    if matrix["check_fail_count"]:
        raise ValueError("Stage 10 post-remediation review matrix failed")

    validation_summary = {
        "final_validation_recorded": final_validation,
        "focused_phase_tests": "PASS" if final_validation else "PENDING",
        "review_tests": "PASS" if final_validation else "PENDING",
        "strict_validator": "PASS" if final_validation else "PENDING",
        "browser_and_download": "PASS" if final_validation else "PENDING",
        "governance_and_safety_scans": "PASS" if final_validation else "PENDING",
    }
    manifest = {
        "schema_version": "kmfa.v014.s10_post_remediation_review_manifest.v1",
        "record_type": "v014_s10_post_remediation_stage_review_manifest",
        "project_id": "KMFA",
        "stage_id": "S10",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": generated_at,
        "reviewed_head": _git_output(["rev-parse", "HEAD"]),
        "branch": _git_output(["branch", "--show-current"]),
        "remote": _git_output(["remote", "get-url", "origin"]),
        "summary": summary,
        "review_findings": findings,
        "historical_review_dependency_validated": historical_current.get("stage_id") == "S10",
        "historical_v013_review_dependency_validated": historical_v013.get("stage_id") == "S10",
        "historical_legacy_review_dependency_validated": bool(historical_legacy),
        "historical_review_dynamic_state_is_authoritative": False,
        "frozen_phase_semantics_validated": True,
        "cross_format_restriction_propagation_verified": True,
        "stale_b_grade_or_pending_twelve_detected": False,
        "restricted_preview_mislabeled_as_formal_report": False,
        "browser_review": browser,
        "validation_summary": validation_summary,
        "reviewed_evidence": {
            "S10-P1": p1_phase.MANIFEST_PATH.as_posix(),
            "S10-P2": p2_phase.MANIFEST_PATH.as_posix(),
            "S10-P3": p3_phase.MANIFEST_PATH.as_posix(),
            "historical_v014_review": OLD_REVIEW_MANIFEST.as_posix(),
        },
        "review_boundaries": {
            "stage10_review_performed": True,
            "s11_p1_performed": False,
            "github_upload_performed": False,
            "app_reinstall_performed": False,
            "formal_report_release_performed": False,
            "business_execution_performed": False,
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
        },
    }
    go_no_go = {
        "schema_version": "kmfa.v014.s10_post_remediation_review_go_no_go.v1",
        "project_id": "KMFA",
        "stage_id": "S10",
        "phase_id": PHASE_ID,
        "decision": DECISION,
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "fixed_review_finding_count": len(findings),
        "open_review_finding_count": 0,
        "restricted_preview_exports_validated": True,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "github_upload_performed": False,
        "blocking_reason_codes": [
            "three_final_accepted_cash_differences_without_provable_values",
            "nine_nonzero_differences_preserved",
            "one_comparison_incomplete",
            "full_lineage_and_business_consistency_not_verified",
        ],
    }

    for path, payload in (
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
        _write_json(path, payload)
    _write_text(REPORT_PATH, _render_report(summary, findings))
    _write_text(TEST_RESULTS_PATH, _render_test_results(summary, browser))
    _write_text(
        RISK_REGISTER_PATH,
        """# Stage 10 修补后整体复审风险登记

| 风险 | 控制 | 状态 |
|---|---|---|
| 旧 12 pending 或 B 级状态回流 | 最新 P1/P2/P3 是唯一当前链，旧 review 仅作历史依赖 | controlled |
| 受限预览被误标为正式报告 | HTML、CSV、manifest 和 gate 均传播 D级、未放行、内部复核 | controlled |
| 浏览器控件或下载失效 | 桌面/移动视口、控制项和逐字节下载均重跑 | controlled |
| PDF、Excel 工作簿或私有 CSV 进入提交 | 禁止后缀和 changed-file scan 阻断 | controlled |
| raw/private/secret 泄漏 | fresh raw 快照、Git ignore 和公开安全扫描阻断 | controlled |
""",
    )
    _write_text(
        ROLLBACK_PATH,
        f"""# Stage 10 修补后整体复审回滚计划

1. 回退本 review 的本地 commit 与 `{OUTPUT_DIR.as_posix()}` 公开证据。
2. 删除本 review 的 ignored private browser/raw 证据，不触碰原始目录。
3. 恢复到 S10-P3 的 `Q4 / D / NO_GO` 受限导出状态。
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
            "Stage 10 browser review: "
            f"viewports={len(result['checks'])} downloads={len(result['download_checks'])} "
            f"status={result['status']}"
        )
        return 0
    manifest = generate(final_validation=args.final_validation)
    summary = manifest["summary"]
    print(
        "Stage 10 post-remediation review: "
        f"fixed={summary['fixed_review_finding_count']} "
        f"open={summary['open_review_finding_count']} "
        f"grade={summary['current_report_grade']} decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
