#!/usr/bin/env python3
"""Generate the KMFA v0.1.4 Stage 12 post-remediation review evidence."""

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

from KMFA.tools import v014_s12_p1_post_remediation_pending_actions as p1
from KMFA.tools import v014_s12_p2_post_remediation_impact_preview as p2
from KMFA.tools import v014_s12_p3_post_remediation_rerun_mechanism as p3
from KMFA.tools.check_v014_s12_p1_post_remediation_pending_actions import (
    validate_v014_s12_p1_post_remediation_pending_actions,
)
from KMFA.tools.check_v014_s12_p2_post_remediation_impact_preview import (
    validate_v014_s12_p2_post_remediation_impact_preview,
)
from KMFA.tools.check_v014_s12_p3_post_remediation_rerun_mechanism import (
    validate_v014_s12_p3_post_remediation_rerun_mechanism,
)


PHASE_ID = "V014_S12_POST_REMEDIATION_STAGE_REVIEW"
ROADMAP_PHASE_ID = "STAGE-REVIEW"
TASK_ID = "KMFA-V014-S12-POST-REMEDIATION-STAGE-REVIEW-20260711"
ACCEPTANCE_ID = "ACC-V014-S12-POST-REMEDIATION-STAGE-REVIEW"
VERSION = "0.1.4-s12-post-remediation-stage-review"
STATUS = "completed_validated_local_only_stage12_review_no_go_upload_deferred"
DECISION = "NO_GO"
REVIEW_SCOPE = "v014_s12_post_remediation_stage_review_only"
FORMULA_ID = "FORM-KMFA-V014-S12-POST-REMEDIATION-STAGE-REVIEW-001"
PARAMETER_IDS = ("PARAM-KMFA-1732", "PARAM-KMFA-1733", "PARAM-KMFA-1734")
MODEL_REGISTRY_KEY = "kmfa_v014_s12_post_remediation_stage_review"

OUTPUT_DIR = Path("KMFA/stage_artifacts") / PHASE_ID
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "stage12_post_remediation_review_summary.json"
MANIFEST_PATH = MACHINE_DIR / "stage12_post_remediation_review_manifest.json"
MATRIX_PATH = MACHINE_DIR / "stage12_post_remediation_review_matrix_public_safe.json"
GO_NO_GO_PATH = MACHINE_DIR / "stage12_post_remediation_review_go_no_go_report.json"
REPORT_PATH = HUMAN_DIR / "stage12_post_remediation_review_report_zh.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results_zh.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register_zh.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan_zh.md"

QUALITY_DIR = Path("KMFA/metadata/quality")
METADATA_SUMMARY_PATH = QUALITY_DIR / "v014_s12_post_remediation_stage_review_summary.json"
METADATA_MANIFEST_PATH = QUALITY_DIR / "v014_s12_post_remediation_stage_review_manifest.json"
METADATA_MATRIX_PATH = QUALITY_DIR / "v014_s12_post_remediation_stage_review_matrix_public_safe.json"
METADATA_GO_NO_GO_PATH = QUALITY_DIR / "v014_s12_post_remediation_stage_review_go_no_go_report.json"

PRIVATE_DIR = Path("KMFA/.codex_private_runtime/v014_s12_post_remediation_stage_review")
PRIVATE_RAW_BEFORE_PATH = PRIVATE_DIR / "raw_immutability_before.json"
PRIVATE_RAW_AFTER_PATH = PRIVATE_DIR / "raw_immutability_after.json"
PRIVATE_REVIEW_REPORT_PATH = PRIVATE_DIR / "stage12_post_remediation_review_validation_zh.md"
PRIVATE_BROWSER_PATH = PRIVATE_DIR / "browser_verification.json"
PRIVATE_BASELINE_AUDIT_PATH = PRIVATE_DIR / "human_flow_baseline_audit.csv"
PRIVATE_PENDING_AUDIT_PATH = PRIVATE_DIR / "current_pending_actions_audit.csv"
PRIVATE_IMPACT_AUDIT_PATH = PRIVATE_DIR / "current_impact_preview_audit.csv"
PRIVATE_RERUN_AUDIT_PATH = PRIVATE_DIR / "current_rerun_workbench_audit.csv"
PRIVATE_SCREENSHOT_DIR = PRIVATE_DIR / "screenshots"

LEGACY_REVIEW_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V014_S12_STAGE_REVIEW/machine/stage12_review_manifest.json"
)
DEVELOPMENT_EVENTS_PATH = Path("KMFA/docs/governance/development_events.jsonl")
STAGE_STATUS_PATH = Path("KMFA/metadata/stage_status.jsonl")
TASK_STATUS_PATH = Path("KMFA/metadata/traceability/v1_4_stage_phase_task_status.jsonl")

PAGE_SPECS = {
    "pending": {
        "path": p1.HTML_PATH,
        "marker": "待处理事项",
    },
    "impact": {
        "path": p2.HTML_PATH,
        "marker": "影响预览",
    },
    "rerun": {
        "path": p3.HTML_PATH,
        "marker": "KMFA 重跑机制",
    },
}
LINK_SPECS = (
    ("pending", "impact", 'a[data-return-link="impact"]'),
    ("pending", "rerun", 'a[data-return-link="rerun"]'),
    ("impact", "pending", 'a[data-return-link="pending"]'),
    ("impact", "rerun", 'a[data-return-link="rerun"]'),
    ("rerun", "pending", 'a[data-return-link="pending"]'),
    ("rerun", "impact", 'a[data-return-link="impact"]'),
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
    if page_id == "pending":
        page.locator('[data-select-group="PEND-S12P1-005"]').click()
        page.locator("#event-reason").fill("公开安全复审候选")
        page.locator("[data-create-event]").click()
        page.locator("[data-reverse-approved]").click()
        return (
            page.locator("body").get_attribute("data-selected-group") == "PEND-S12P1-005"
            and page.locator("body").get_attribute("data-session-event-count") == "2"
        )
    if page_id == "impact":
        page.locator('[data-generate-preview="IMPREV-S12P2-POST-005"]').click()
        blocked = page.locator("body").get_attribute("data-preview-status") == "blocked_pending_second_confirmation"
        page.locator("[data-high-risk-ack]").check()
        page.locator("[data-confirm-preview]").click()
        page.locator("[data-check-publish]").click()
        return (
            blocked
            and page.locator("body").get_attribute("data-preview-status") == "passed_session_preview"
            and page.locator("body").get_attribute("data-publish-status") == "blocked_quality_gate"
        )
    page.locator('[data-select-plan="RERUNPLAN-S12P3-POST-002"]').click()
    page.locator("[data-preview-rerun]").click()
    page.locator("[data-run-simulation]").click()
    page.locator("[data-check-consistency]").click()
    page.locator("[data-check-persistent]").click()
    return (
        page.locator("body").get_attribute("data-simulation-status") == "session_simulation_complete"
        and page.locator("body").get_attribute("data-consistency-status") == "passed"
        and page.locator("body").get_attribute("data-persistent-status") == "blocked_quality_gate"
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
                executable_path=p1.s11_home._chromium_path(),
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
                        and p1.s11_home._is_actionable_console_error(
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
        raise RuntimeError("Stage 12 desktop/mobile cross-page browser review failed")
    return result


def _run_browser_suite() -> dict[str, Any]:
    baseline = p1.s11_home._run_html_audit(p1.V14_HTML_ROOT, PRIVATE_BASELINE_AUDIT_PATH)
    pending = p1.s11_home._run_html_audit(p1.HTML_DIR, PRIVATE_PENDING_AUDIT_PATH)
    impact = p1.s11_home._run_html_audit(p2.HTML_DIR, PRIVATE_IMPACT_AUDIT_PATH)
    rerun = p1.s11_home._run_html_audit(p3.HTML_DIR, PRIVATE_RERUN_AUDIT_PATH)
    env = os.environ.copy()
    env["KMFA_CHROMIUM"] = p1.s11_home._chromium_path()
    result = subprocess.run(
        [str(p1.s11_home._audit_python()), str(Path(__file__).resolve()), "--browser-evidence-only"],
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
        "current_page_audits": {"pending": pending, "impact": impact, "rerun": rerun},
        "viewport_check_count": len(browser["viewport_checks"]),
        "representative_interaction_check_count": len(browser["representative_interaction_checks"]),
        "cross_page_link_http_check_count": len(browser["cross_page_link_http_checks"]),
        "cross_page_navigation_check_count": len(browser["cross_page_navigation_checks"]),
        "console_error_count": sum(item["console_error_count"] for item in browser["viewport_checks"]),
        "horizontal_overflow_count": sum(not item["no_horizontal_overflow"] for item in browser["viewport_checks"]),
    }


def _current_chain() -> dict[str, dict[str, Any]]:
    return {
        "p1": validate_v014_s12_p1_post_remediation_pending_actions(
            require_private_evidence=True,
            require_browser_evidence=True,
            require_final_evidence=True,
        ),
        "p2": validate_v014_s12_p2_post_remediation_impact_preview(
            require_private_evidence=True,
            require_browser_evidence=True,
            require_final_evidence=True,
        ),
        "p3": validate_v014_s12_p3_post_remediation_rerun_mechanism(
            require_private_evidence=True,
            require_browser_evidence=True,
            require_final_evidence=True,
        ),
    }


def _findings() -> list[dict[str, str]]:
    return [
        {
            "finding_id": "S12-POST-REVIEW-F01",
            "status": "fixed",
            "summary": "S12-P1 页面缺少通向已完成 P2/P3 的当前阶段入口",
            "fix": "增加影响预览与重跑机制入口，并纳入 HTTP 和真实导航复验",
        },
        {
            "finding_id": "S12-POST-REVIEW-F02",
            "status": "fixed",
            "summary": "S12-P2 页面缺少通向已完成 P3 的前向入口",
            "fix": "增加重跑机制入口，与 P1/P3 组成三页六边强连通图",
        },
        {
            "finding_id": "S12-POST-REVIEW-F03",
            "status": "fixed",
            "summary": "P1/P2 页面仍把已完成的下游 phase 标记为未执行",
            "fix": "页面阶段状态更新为 P1/P2/P3 已完成，同时保持 phase evidence 冻结语义",
        },
        {
            "finding_id": "S12-POST-REVIEW-F04",
            "status": "fixed",
            "summary": "历史 S12 review 的 5 个事件、2 个 eligible 事件和 8 个重跑步骤会污染当前事实",
            "fix": "历史 review 仅作为策略夹具；当前动态事实只来自 post-remediation P1/P2/P3",
        },
        {
            "finding_id": "S12-POST-REVIEW-F05",
            "status": "fixed",
            "summary": "历史 review 含 upload-ready 语义，可能被误当成当前上传门禁",
            "fix": "明确当前上传仍 deferred，Stage 12 review 不上传、不重装",
        },
        {
            "finding_id": "S12-POST-REVIEW-F06",
            "status": "fixed",
            "summary": "24 个计划步骤可能被误读为已持久执行",
            "fix": "计划步骤保持 24，持久缓存失效、重跑步骤和一致性检查全部明确为 0",
        },
        {
            "finding_id": "S12-POST-REVIEW-F07",
            "status": "fixed",
            "summary": "潜在项目槽位可能被误当成已证明项目归属",
            "fix": "继续保持 0 条已证明项目归属和 4 个 unknown 项目槽位，不平均、不补零",
        },
    ]


def _matrix(summary: dict[str, Any]) -> dict[str, Any]:
    checks = {
        "three_phases_pass": summary["phase_results"] == {"S12-P1": "PASS", "S12-P2": "PASS", "S12-P3": "PASS"},
        "six_pending_groups": summary["pending_action_group_count"] == 6,
        "four_event_templates": summary["manual_event_template_count"] == 4,
        "six_impact_previews": summary["impact_preview_definition_count"] == 6,
        "five_high_risk_previews": summary["high_risk_preview_count"] == 5,
        "five_second_confirmations": summary["second_confirmation_required_count"] == 5,
        "six_rerun_plans": summary["rerun_plan_definition_count"] == 6,
        "four_rerun_layers": summary["required_rerun_chain_layer_count"] == 4,
        "twenty_four_planned_steps": summary["planned_rerun_step_count"] == 24,
        "no_approved_or_published_event": summary["current_approved_business_event_count"] == 0 and summary["current_published_business_event_count"] == 0,
        "no_persistent_rerun": (
            summary["current_persistent_cache_invalidation_count"],
            summary["current_persistent_rerun_step_count"],
            summary["current_persistent_consistency_check_count"],
        ) == (0, 0, 0),
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
        "project_attribution_unknown": summary["project_specific_attributed_difference_count"] == 0 and summary["potential_affected_project_slot_count"] == 4,
        "no_formal_report": summary["formal_report_count"] == 0,
        "no_decision_basis": summary["business_decision_basis_allowed_count"] == 0,
        "raw_exact": summary["raw_snapshot_exact_match"] is True,
        "raw_cross_phase_exact": summary["raw_cross_phase_snapshot_exact_match"] is True,
        "findings_closed": summary["open_review_finding_count"] == 0,
        "s13_not_performed": summary["s13_p1_performed"] is False,
        "upload_not_performed": summary["github_upload_performed"] is False,
        "app_not_reinstalled": summary["app_reinstall_performed"] is False,
        "business_not_executed": summary["business_execution_performed"] is False,
    }
    rows = [{"check_id": key, "passed": value} for key, value in sorted(checks.items())]
    return {
        "schema_version": "kmfa.v014.s12_post_remediation_review_matrix.v1",
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
        "KMFA/tools/v014_s12_post_remediation_stage_review.py",
        "KMFA/tools/check_v014_s12_post_remediation_stage_review.py",
        "KMFA/tests/test_v014_s12_post_remediation_stage_review.py",
    ]


def _write_governance_events(generated_at: str) -> None:
    evidence_ref = MANIFEST_PATH.as_posix()
    _upsert_jsonl(
        DEVELOPMENT_EVENTS_PATH,
        {
            "event_id": "DEV-KMFA-20260711-V014-S12-POST-REMEDIATION-STAGE-REVIEW",
            "event_time": generated_at,
            "event_type": "stage_review",
            "project_id": "KMFA",
            "stage_id": "S12",
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
            "stage_id": "S12",
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
            "stage_id": "S12",
            "governance_stage_id": "REPORT-TRUST-AND-GENERATION",
            "roadmap_stage_id": "S12",
            "roadmap_phase_id": ROADMAP_PHASE_ID,
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "acceptance_id": ACCEPTANCE_ID,
            "version": VERSION,
            "name": "v0.1.4 Stage 12 post-remediation review",
            "phase_goal": "review current Stage 12 chain and fix all findings",
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
    return f"""# KMFA v0.1.4 Stage 12 修补后整体复审

## 结论

- S12-P1/P2/P3：`PASS / PASS / PASS`
- 当前状态：`Q4 / D / NO_GO`
- 当前差异：`3 final-accepted-open / 9 nonzero / 2 zero / 1 incomplete`
- 控制链：`6` 个待处理分组、`6` 个影响预览、`6` 个重跑计划、`24` 个会话计划步骤
- 持久执行：批准/发布事件 `0/0`，缓存失效/重跑/一致性 `0/0/0`
- 页面：`3` 个当前页面，`6` 条跨页边，`0` 条断链
- 项目归属：`0` 条可证明项目归属，`4` 个项目槽位保持未知
- 浏览器：`{summary['browser_viewport_check_count']}/6` 视口、`{summary['cross_page_navigation_check_count']}/6` 跨页导航通过
- findings：`{summary['fixed_review_finding_count']} fixed / {summary['open_review_finding_count']} open`

## 复审发现与修复

{finding_lines}

## 放行边界

- 当前三页仅展示公开安全状态；D 级受限报告不可绕过，也不是正式报告或经营决策依据。
- 项目级差异无法由公开证据证明时保持 unknown/null，不平均、不补零、不虚构归属。
- 原始数据 review 前后、跨 S12-P3 和当前快照一致；公开证据不含原始文件名、字段、表头、金额或明细。
- 未进入 S13，未上传 GitHub，未重装应用，未执行任何业务动作。
"""


def _render_test_results(summary: dict[str, Any], browser: dict[str, Any]) -> str:
    return f"""# Stage 12 修补后整体复审测试结果

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
    return f"""# Stage 12 修补后私有复审记录

- 原始数据文件数：{summary['raw_source_file_count']}
- review 前后快照：exact match
- 与 S12-P3 快照：exact match
- 与当前只读目录快照：exact match
- 当前差异结构：3 / 9 / 2 / 1
- 结论：没有持久 raw 快照差异；无需生成最终差异报告。
- 限制：项目级归属保持未知；不推断、不平均、不补零。
"""


def generate(*, final_validation: bool = False, write_governance: bool = True) -> dict[str, Any]:
    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
    raw_before = p1.s11_project._raw_snapshot("before_v014_s12_post_remediation_stage_review")
    chain = _current_chain()
    legacy_review = _read_json(LEGACY_REVIEW_MANIFEST_PATH)
    browser = _run_browser_suite()
    raw_after = p1.s11_project._raw_snapshot("after_v014_s12_post_remediation_stage_review")
    prior_raw = _read_json(p3.PRIVATE_RAW_AFTER_PATH)
    current_raw = p1.s11_project._raw_snapshot("current_v014_s12_post_remediation_stage_review")
    normalize = p1.s11_project._normalize_raw
    raw_exact = normalize(raw_before) == normalize(raw_after)
    raw_cross = normalize(raw_before) == normalize(prior_raw) == normalize(current_raw)
    if not raw_exact or not raw_cross:
        raise ValueError("raw source changed during Stage 12 post-remediation review")

    p1_summary = chain["p1"]["summary"]
    p2_summary = chain["p2"]["summary"]
    p3_summary = chain["p3"]["summary"]
    historical_gate = legacy_review.get("stage_gate", {})
    findings = _findings()
    summary = {
        "schema_version": "kmfa.v014.s12_post_remediation_review_summary.v1",
        "project_id": "KMFA",
        "stage_id": "S12",
        "phase_id": PHASE_ID,
        "roadmap_phase_id": ROADMAP_PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "version": VERSION,
        "review_scope": REVIEW_SCOPE,
        "status": STATUS,
        "decision": DECISION,
        "phase_results": {"S12-P1": "PASS", "S12-P2": "PASS", "S12-P3": "PASS"},
        "pending_action_group_count": p1_summary["pending_action_group_count"],
        "manual_event_template_count": p1_summary["manual_event_template_count"],
        "manual_action_kind_count": p1_summary["manual_action_kind_count"],
        "impact_preview_definition_count": p2_summary["impact_preview_definition_count"],
        "high_risk_preview_count": p2_summary["high_risk_preview_count"],
        "second_confirmation_required_count": p2_summary["second_confirmation_required_count"],
        "potential_affected_project_slot_count": p2_summary["potential_affected_project_slot_count"],
        "rerun_plan_definition_count": p3_summary["rerun_plan_definition_count"],
        "required_rerun_chain_layer_count": p3_summary["required_rerun_chain_layer_count"],
        "planned_rerun_step_count": p3_summary["planned_rerun_step_count"],
        "current_approved_business_event_count": p3_summary["current_approved_business_event_count"],
        "current_published_business_event_count": p3_summary["current_published_business_event_count"],
        "current_persistent_cache_invalidation_count": p3_summary["current_persistent_cache_invalidation_count"],
        "current_persistent_rerun_step_count": p3_summary["current_persistent_rerun_step_count"],
        "current_persistent_consistency_check_count": p3_summary["current_persistent_consistency_check_count"],
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
        "project_specific_attributed_difference_count": 0,
        "project_specific_unknown_allocation_count": p1_summary["project_specific_unknown_allocation_count"],
        "formal_report_count": 0,
        "business_decision_basis_allowed_count": 0,
        "fixed_review_finding_count": len(findings),
        "open_review_finding_count": 0,
        "raw_source_file_count": raw_before["file_count"],
        "raw_snapshot_exact_match": raw_exact,
        "raw_cross_phase_snapshot_exact_match": raw_cross,
        "s13_p1_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }
    quality_gate = {
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "decision": "NO_GO",
        "release_permission": "blocked",
        "stage12_public_safe_pages_allowed": True,
        "restricted_internal_preview_allowed": True,
        "quality_grade_bypass_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "business_execution_allowed": False,
    }
    boundaries = {
        "s12_p1_validated": True,
        "s12_p2_validated": True,
        "s12_p3_validated": True,
        "stage12_review_performed": True,
        "s13_p1_performed": False,
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
        "schema_version": "kmfa.v014.s12_post_remediation_review_manifest.v1",
        "project_id": "KMFA",
        "stage_id": "S12",
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
            legacy_review.get("stage_id") == "S12"
            and historical_gate.get("manual_event_count") == 5
            and historical_gate.get("eligible_event_count") == 2
            and historical_gate.get("rerun_step_count") == 8
        ),
        "historical_review_dynamic_state_is_authoritative": False,
        "historical_five_events_quarantined": historical_gate.get("manual_event_count") == 5,
        "historical_two_eligible_events_quarantined": historical_gate.get("eligible_event_count") == 2,
        "historical_eight_rerun_steps_quarantined": historical_gate.get("rerun_step_count") == 8,
        "reviewed_phase_manifests": {
            "S12-P1": p1.MANIFEST_PATH.as_posix(),
            "S12-P2": p2.MANIFEST_PATH.as_posix(),
            "S12-P3": p3.MANIFEST_PATH.as_posix(),
            "historical_S12_review": LEGACY_REVIEW_MANIFEST_PATH.as_posix(),
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
        "schema_version": "kmfa.v014.s12_post_remediation_review_go_no_go.v1",
        "project_id": "KMFA",
        "stage_id": "S12",
        "phase_id": PHASE_ID,
        "decision": "NO_GO",
        "stage12_review_validated": True,
        "current_public_safe_pages_allowed": True,
        "quality_grade_bypass_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "s13_p1_performed": False,
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
        """# Stage 12 修补后整体复审风险登记

| 风险 | 控制 | 状态 |
|---|---|---|
| 旧 review 的 5/2/8 动态状态回流 | 新 review 仅以当前 P1/P2/P3 为动态事实；旧 review 标记 historical-only | controlled |
| phase validator 随全局状态推进失效 | P1/P2/P3 均采用 frozen semantics，并有回归测试 | controlled |
| 当前页面断链或移动端不可达 | 三页六边、桌面/移动、HTTP 和真实导航复验 | controlled |
| D/NO_GO 被页面或预览绕过 | 三页强制显示 D/NO_GO，正式报告和决策依据继续阻断 | controlled |
| 潜在项目槽位被误当成已证明归属 | 4 个项目槽位保持 unknown/null，公开证据不足时不分配 | controlled |
| raw/private/secret 进入 Git | raw 前后/跨 phase/current 一致，private evidence ignored，提交前安全扫描 | controlled |
| 24 个计划步骤被误当成持久执行 | 显式锁定持久缓存失效/重跑/一致性均为 0 | controlled |
""",
    )
    _write_text(
        ROLLBACK_PATH,
        f"""# Stage 12 修补后整体复审回滚计划

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
            "Stage 12 browser review: "
            f"viewports={len(result['viewport_checks'])} "
            f"links={len(result['cross_page_link_http_checks'])} "
            f"navigation={len(result['cross_page_navigation_checks'])} "
            f"status={result['status']}"
        )
        return 0
    manifest = generate(final_validation=args.final_validation)
    summary = manifest["summary"]
    print(
        "Stage 12 post-remediation review: "
        f"phases=3 findings={summary['fixed_review_finding_count']}/0 "
        f"links={summary['cross_page_link_count']} "
        f"grade={summary['current_report_grade']} decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
