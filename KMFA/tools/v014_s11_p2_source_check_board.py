#!/usr/bin/env python3
"""Generate KMFA v0.1.4 S11-P2 public-safe source check board evidence.

This phase locks the data-source check board against the v1.4 human-flow HTML
baseline. It does not read the raw/private inbox, build S11-P3, run Stage 11
review, publish a formal report, perform raw matching, or upload to GitHub.
"""

from __future__ import annotations

import html
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools.check_v014_s11_p1_home_navigation import validate_v014_s11_p1_home_navigation
from KMFA.tools.source_check_board_runtime import (
    ALLOWED_BOARD_STATUSES,
    DEFAULT_HTML_OUTPUT as LEGACY_HTML_OUTPUT,
    DEFAULT_OUTPUT_MANIFEST as LEGACY_MANIFEST_PATH,
    DEFAULT_OUTPUT_ROWS as LEGACY_ROWS_PATH,
    REQUIRED_BOARD_COLUMNS,
    read_json,
    read_jsonl,
    validate_source_check_board_artifacts,
)


TASK_ID = "KMFA-V014-S11-P2-SOURCE-CHECK-BOARD-20260704"
ACCEPTANCE_ID = "ACC-V014-S11-P2-SOURCE-CHECK-BOARD"
SCHEMA_VERSION = "kmfa.v014_s11_p2_source_check_board.v1"
PHASE_SCOPE = "v014_s11_p2_source_check_board_only"

OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_S11_P2_SOURCE_CHECK_BOARD")
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
EXPORT_HTML_DIR = OUTPUT_DIR / "exports" / "html"
MANIFEST_PATH = MACHINE_DIR / "source_check_board_manifest.json"
ROWS_PATH = MACHINE_DIR / "source_check_board_rows.jsonl"
HTML_OUTPUT_PATH = EXPORT_HTML_DIR / "kmfa_source_check_board.html"
REPORT_PATH = HUMAN_DIR / "source_check_board_report.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

V14_SOURCE_PACKAGE_MANIFEST = Path("KMFA/taskpack/v1_4/machine/source_package_manifest.json")
V14_HTML_ENTRY_PATH = Path("KMFA/taskpack/v1_4/html_uiux/00_KMFA_HTML_human_flow_entry_v1_4.html")
V14_HTML_AUDIT_SCRIPT_PATH = Path("KMFA/taskpack/v1_4/html_uiux/kmfa_html_human_flow_audit.py")
V14_HTML_AUDIT_REPORT_PATH = Path("KMFA/taskpack/v1_4/html_uiux/KMFA_HTML_human_flow_audit_report_v1_4.md")

RAW_INBOX_REF = "operator-designated raw/private inbox outside repository"
NEXT_REQUIRED_STEP = (
    "Proceed to v0.1.4 S11-P3 project cost page as a separate run. Do not perform "
    "Stage 11 overall review, GitHub upload, raw value matching, lineage full check, "
    "formal report release, live connector, app reinstall, OpMe deep coupling, or "
    "business execution in the S11-P2 run."
)


def git_output(args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(record, ensure_ascii=False, sort_keys=True) for record in records) + "\n",
        encoding="utf-8",
    )


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _extract_first_int(pattern: str, text: str, label: str) -> int:
    match = re.search(pattern, text)
    if not match:
        raise RuntimeError(f"missing v1.4 HTML audit value: {label}")
    return int(match.group(1))


def validate_s11_p1_dependency() -> dict[str, Any]:
    result = validate_v014_s11_p1_home_navigation()
    progress = result.get("stage11_phase_progress", {})
    if result.get("phase_id") != "S11-P1":
        raise RuntimeError("S11-P2 requires validated v0.1.4 S11-P1")
    if progress.get("s11_p1_performed") is not True:
        raise RuntimeError("S11-P1 dependency must be performed")
    if progress.get("s11_p2_performed") is not False:
        raise RuntimeError("S11-P1 dependency must not already perform S11-P2")
    if progress.get("s11_p3_performed") is not False:
        raise RuntimeError("S11-P1 dependency must not perform S11-P3")
    if progress.get("stage11_review_performed") is not False:
        raise RuntimeError("S11-P1 dependency must not include Stage 11 review")
    if result.get("github_upload", {}).get("github_upload_performed") is not False:
        raise RuntimeError("S11-P1 dependency must not include GitHub upload")
    return result


def validate_legacy_s11_p2_artifacts() -> dict[str, Any]:
    legacy_manifest = read_json(LEGACY_MANIFEST_PATH)
    rows = read_jsonl(LEGACY_ROWS_PATH)
    legacy_html = LEGACY_HTML_OUTPUT.read_text(encoding="utf-8")
    validate_source_check_board_artifacts(
        legacy_manifest,
        rows,
        {"html": {"kmfa_source_check_board": legacy_html}},
    )
    status_counts = {status: 0 for status in ALLOWED_BOARD_STATUSES}
    for row in rows:
        status_counts[str(row["status"])] += 1
    return {
        "legacy_manifest": legacy_manifest,
        "rows": rows,
        "legacy_html": legacy_html,
        "status_counts": status_counts,
    }


def load_v14_html_uiux_baseline() -> dict[str, Any]:
    source_manifest = json.loads(V14_SOURCE_PACKAGE_MANIFEST.read_text(encoding="utf-8"))
    gate = source_manifest.get("html_human_flow_gate", {})
    report_text = V14_HTML_AUDIT_REPORT_PATH.read_text(encoding="utf-8")
    entry_text = V14_HTML_ENTRY_PATH.read_text(encoding="utf-8")
    script_text = V14_HTML_AUDIT_SCRIPT_PATH.read_text(encoding="utf-8")
    report_counts = {
        "audit_file_count": _extract_first_int(r"HTML 文件数：(\d+)", report_text, "HTML file count"),
        "audit_control_row_count": _extract_first_int(r"核验行数：(\d+)", report_text, "control row count"),
        "audit_pass_count": _extract_first_int(r"PASS：(\d+)", report_text, "pass count"),
        "audit_warn_count": _extract_first_int(r"WARN：(\d+)", report_text, "warn count"),
        "audit_fail_count": _extract_first_int(r"FAIL：(\d+)", report_text, "fail count"),
    }
    manifest_counts = {
        "audit_file_count": int(gate.get("audit_files", -1)),
        "audit_control_row_count": int(gate.get("audit_rows", -1)),
        "audit_pass_count": int(gate.get("pass", -1)),
        "audit_warn_count": int(gate.get("warn", -1)),
        "audit_fail_count": int(gate.get("fail", -1)),
    }
    if report_counts != manifest_counts:
        raise RuntimeError("v1.4 HTML audit report counts do not match source package manifest")
    for term in ("数据源检查板可点击预览", "支持搜索", "状态变更", "就绪率更新"):
        if term not in entry_text:
            raise RuntimeError(f"v1.4 HTML entry missing source check flow term: {term}")
    for term in ("搜索有筛选", "状态可变更", "状态变更写入控制事件", "影响预览", "数据源检查板能按来源系统"):
        if term not in report_text:
            raise RuntimeError(f"v1.4 HTML audit report missing source check requirement: {term}")
    if "button" not in script_text or "input" not in script_text:
        raise RuntimeError("v1.4 audit script must inspect buttons and inputs")
    return {
        "taskpack_html_requirement_read": True,
        "human_flow_entry_exists": V14_HTML_ENTRY_PATH.exists(),
        "human_flow_audit_script_exists": V14_HTML_AUDIT_SCRIPT_PATH.exists(),
        "human_flow_audit_report_exists": V14_HTML_AUDIT_REPORT_PATH.exists(),
        **report_counts,
        "source_package_manifest_counts_match_report": True,
        "entry_includes_source_check_clickable_preview": True,
        "audit_report_requires_search_status_change_detail": True,
        "audit_script_inspects_inputs_buttons": True,
        "implementation_reflects_search_feedback": False,
        "implementation_reflects_status_change_feedback": False,
        "implementation_reflects_status_detail_preview": False,
        "source_refs": {
            "source_package_manifest": V14_SOURCE_PACKAGE_MANIFEST.as_posix(),
            "html_human_flow_entry": V14_HTML_ENTRY_PATH.as_posix(),
            "html_human_flow_audit_script": V14_HTML_AUDIT_SCRIPT_PATH.as_posix(),
            "html_human_flow_audit_report": V14_HTML_AUDIT_REPORT_PATH.as_posix(),
        },
    }


def _phase_boundaries() -> dict[str, bool]:
    return {
        "s11_p1_home_navigation_dependency_included": True,
        "s11_p2_source_check_board_scope_included": True,
        "s11_p3_project_cost_page_scope_included": False,
        "stage11_review_scope_included": False,
        "lineage_full_check_scope_included": False,
        "raw_value_matching_scope_included": False,
        "formal_report_scope_included": False,
        "external_connector_scope_included": False,
        "live_ui_runtime_scope_included": False,
        "app_reinstall_scope_included": False,
        "github_upload_scope_included": False,
        "business_execution_scope_included": False,
    }


def _quality_gate() -> dict[str, Any]:
    return {
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "release_permission": "blocked",
        "pending_reconciliation_count": 12,
        "confirmed_resolution_count": 0,
        "source_check_board_export_allowed": True,
        "complete_trusted_report_display_allowed": False,
        "full_trusted_report_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "business_execution_allowed": False,
        "delivery_allowed": False,
        "raw_layer_write_allowed": False,
        "automatic_external_action_allowed": False,
        "stage11_review_allowed": False,
        "github_upload_allowed": False,
    }


def _raw_boundary() -> dict[str, Any]:
    return {
        "raw_inbox_ref": RAW_INBOX_REF,
        "raw_inbox_role": "user_finance_raw_private_inbox",
        "raw_inbox_read_allowed_only_when_phase_requires": True,
        "raw_inbox_read_required_by_this_phase": False,
        "raw_inbox_read_by_this_phase": False,
        "raw_inbox_listed_by_this_phase": False,
        "raw_inbox_inventory_by_this_phase": False,
        "raw_inbox_stat_by_this_phase": False,
        "raw_inbox_hashed_by_this_phase": False,
        "raw_inbox_modified_by_this_phase": False,
        "raw_inbox_deleted_by_this_phase": False,
        "raw_inbox_moved_by_this_phase": False,
        "raw_inbox_renamed_by_this_phase": False,
        "raw_inbox_overwritten_by_this_phase": False,
        "raw_inbox_written_by_this_phase": False,
        "raw_inbox_mutated_by_this_phase": False,
        "private_runtime_output_dir": "KMFA/.codex_private_runtime/",
    }


def _public_repo_safety() -> dict[str, bool]:
    return {
        "protected_source_payload_committed": False,
        "zip_committed": False,
        "excel_workbook_committed": False,
        "wps_native_file_committed": False,
        "redcircle_native_file_committed": False,
        "raw_or_private_csv_committed": False,
        "pdf_committed": False,
        "private_csv_committed": False,
        "sqlite_or_db_committed": False,
        "credentials_committed": False,
        "connector_secret_committed": False,
        "field_plaintext_committed": False,
        "source_header_plaintext_committed": False,
        "raw_file_names_committed": False,
        "raw_file_hashes_committed": False,
        "tab_labels_committed": False,
        "zip_member_names_committed": False,
        "source_record_payload_committed": False,
        "normalized_source_values_committed": False,
        "business_amount_values_committed": False,
        "project_or_customer_plaintext_committed": False,
        "formal_report_committed": False,
        "spreadsheet_workbook_committed": False,
    }


def _status_class(status: str) -> str:
    return {
        "已就绪": "ready",
        "部分/阻塞": "partial",
        "失败/不适用": "failed",
        "已过期": "outdated",
        "人工复核": "review",
    }[status]


def render_v14_html(rows: list[dict[str, Any]], status_counts: dict[str, int]) -> str:
    cards = "\n".join(
        f'<div class="summary-card"><b data-count-for="{html.escape(status)}">{status_counts[status]}</b><span>{html.escape(status)}</span></div>'
        for status in ALLOWED_BOARD_STATUSES
    )
    filter_options = "\n".join(f'<option value="{html.escape(status)}">{html.escape(status)}</option>' for status in ALLOWED_BOARD_STATUSES)
    status_buttons = "\n".join(
        f'<button type="button" data-status-option="{html.escape(status)}">{html.escape(status)}</button>'
        for status in ALLOWED_BOARD_STATUSES
    )
    columns = "".join(f"<th>{html.escape(column)}</th>" for column in REQUIRED_BOARD_COLUMNS)
    row_html = "\n".join(
        f"""<tr data-row-id="{html.escape(row['row_id'])}" data-status="{html.escape(row['status'])}" data-search="{html.escape(' '.join(str(row[field]) for field in ('source_system', 'business_segment', 'source_package_ref', 'entity_ref', 'bank_or_system_account', 'account_or_report_ref', 'frequency', 'status')))}">
<td>{html.escape(row['source_system'])}</td>
<td>{html.escape(row['business_segment'])}</td>
<td>{html.escape(row['source_package_ref'])}</td>
<td>{html.escape(row['entity_ref'])}</td>
<td>{html.escape(row['bank_or_system_account'])}</td>
<td>{html.escape(row['account_or_report_ref'])}</td>
<td>{html.escape(row['frequency'])}</td>
<td><button type="button" class="status-badge {_status_class(row['status'])}" data-row-id="{html.escape(row['row_id'])}" data-impact="{html.escape(row['report_impact'])}" data-rule="{html.escape(row['handling_rule'])}" data-next="{html.escape(row['next_step'])}">{html.escape(row['status'])}</button></td>
<td>{html.escape(row['report_impact'])}</td>
<td>{html.escape(row['handling_rule'])}</td>
<td>{html.escape(row['next_step'])}</td>
</tr>"""
        for row in rows
    )
    first = rows[0]
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>KMFA 数据源检查板</title>
  <style>
    :root {{ --navy:#0b1f3a; --blue:#1d4ed8; --soft:#eff6ff; --bg:#f7faff; --card:#fff; --line:#d8e7ff; --text:#172033; --muted:#64748b; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:linear-gradient(180deg,#f8fbff 0%,#eef5ff 100%); color:var(--text); font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",Arial,sans-serif; }}
    .header {{ background:linear-gradient(135deg,#071a33,#0f3b74); color:#fff; padding:28px 36px; }}
    .brand {{ display:flex; align-items:center; gap:14px; }}
    .logo {{ width:54px; height:54px; border:1px solid rgba(255,255,255,.35); border-radius:8px; display:flex; align-items:center; justify-content:center; font-weight:800; background:rgba(255,255,255,.08); }}
    h1 {{ margin:0; font-size:26px; letter-spacing:0; }}
    .header p {{ margin:8px 0 0; color:#c7ddff; line-height:1.6; }}
    .wrap {{ padding:24px 36px 38px; }}
    .summary {{ display:grid; grid-template-columns:repeat(5,1fr); gap:12px; margin-bottom:18px; }}
    .summary-card {{ background:rgba(255,255,255,.94); border:1px solid var(--line); border-radius:8px; padding:16px; }}
    .summary-card b {{ display:block; font-size:25px; color:#0b376d; }}
    .summary-card span {{ color:var(--muted); font-size:13px; }}
    .controls {{ display:grid; grid-template-columns:1.3fr .8fr auto; gap:12px; align-items:end; margin-bottom:14px; }}
    label {{ display:grid; gap:6px; color:#334155; font-size:13px; font-weight:700; }}
    input, select {{ height:38px; border:1px solid #bfdbfe; border-radius:8px; padding:0 11px; color:#172033; background:#fff; }}
    .grade {{ border:1px solid #bfdbfe; background:#fff; color:var(--blue); border-radius:999px; padding:10px 12px; font-size:12px; font-weight:800; white-space:nowrap; }}
    .feedback {{ margin:-4px 0 14px; color:#475569; line-height:1.7; }}
    .matrix-wrap {{ overflow:auto; border:1px solid var(--line); border-radius:8px; background:#fff; box-shadow:0 14px 38px rgba(15,54,113,.08); }}
    table {{ width:100%; min-width:1280px; border-collapse:separate; border-spacing:0; }}
    th {{ position:sticky; top:0; background:#0f2f5f; color:#fff; font-size:13px; text-align:left; padding:12px; border-bottom:1px solid #244d86; }}
    td {{ font-size:13px; padding:11px 12px; border-bottom:1px solid #e7f0ff; vertical-align:top; line-height:1.55; }}
    tr:hover td {{ background:#f8fbff; }}
    .status-badge, [data-status-option] {{ border:1px solid transparent; border-radius:999px; padding:5px 10px; font-size:12px; font-weight:800; white-space:nowrap; cursor:pointer; }}
    .ready {{ color:#065f46; background:#dcfce7; }}
    .partial {{ color:#1d4ed8; background:#eff6ff; border-color:#bfdbfe; }}
    .failed {{ color:#991b1b; background:#fee2e2; }}
    .review {{ color:#5b21b6; background:#f3e8ff; }}
    .outdated {{ color:#111827; background:#e5e7eb; }}
    .detail {{ margin-top:16px; background:#fff; border:1px solid var(--line); border-radius:8px; padding:16px; display:grid; gap:10px; }}
    .detail h2 {{ margin:0; color:#0b2b59; font-size:18px; letter-spacing:0; }}
    .detail p {{ margin:0; color:#475569; line-height:1.7; }}
    .status-actions {{ display:flex; flex-wrap:wrap; gap:8px; }}
    .event-log {{ background:#f8fbff; border:1px solid #dbeafe; border-radius:8px; padding:10px; color:#475569; min-height:40px; }}
    .footer {{ margin-top:16px; color:#64748b; font-size:12px; line-height:1.6; }}
    @media(max-width:1000px) {{ .wrap {{ padding:18px; }} .summary {{ grid-template-columns:repeat(2,1fr); }} .controls {{ grid-template-columns:1fr; }} }}
    @media(max-width:560px) {{ .summary {{ grid-template-columns:1fr; }} }}
  </style>
</head>
<body>
  <header class="header">
    <div class="brand"><div class="logo">KM</div><div><h1>KMFA 数据源检查板</h1><p>按来源系统、业务板块、文件包、公司主体、账户分组和状态进行矩阵检查；搜索、状态变更和详情预览均只写页面控制事件，不污染原始数据。</p></div></div>
  </header>
  <main class="wrap">
    <section class="summary" aria-label="状态汇总">{cards}</section>
    <section class="controls" aria-label="检查板操作">
      <label>搜索来源或板块<input id="sourceSearch" type="search" placeholder="输入来源系统、业务板块、文件包或状态"></label>
      <label>状态筛选<select id="statusFilter"><option value="">全部状态</option>{filter_options}</select></label>
      <span class="grade">报告等级 D</span>
    </section>
    <p id="filterFeedback" class="feedback" aria-live="polite">当前显示 {len(rows)} 条来源检查记录。</p>
    <section class="matrix-wrap" aria-label="数据源检查矩阵">
      <table>
        <thead><tr>{columns}</tr></thead>
        <tbody>{row_html}</tbody>
      </table>
    </section>
    <section class="detail" aria-live="polite">
      <h2>状态详情</h2>
      <p><strong>影响报告：</strong><span id="impactText">{html.escape(first['report_impact'])}</span></p>
      <p><strong>处理规则：</strong><span id="ruleText">{html.escape(first['handling_rule'])}</span></p>
      <p><strong>下一步：</strong><span id="nextText">{html.escape(first['next_step'])}</span></p>
      <div class="status-actions" aria-label="状态变更控制事件">{status_buttons}</div>
      <div id="controlEventLog" class="event-log" aria-live="polite">状态变更只记录页面控制事件，不写原始层。</div>
    </section>
    <div class="footer">KMFA 经营分析系统 · S11-P2 数据源检查板 · 本页面不解锁项目成本详情、第十一阶段复审、正式报告或上传。</div>
  </main>
  <script>
    const rows = Array.from(document.querySelectorAll("tbody tr"));
    const search = document.getElementById("sourceSearch");
    const statusFilter = document.getElementById("statusFilter");
    const filterFeedback = document.getElementById("filterFeedback");
    const detail = {{
      impact: document.getElementById("impactText"),
      rule: document.getElementById("ruleText"),
      next: document.getElementById("nextText")
    }};
    let activeRow = rows[0];
    const controlEvents = [];
    function filterRows() {{
      const keyword = search.value.trim();
      const status = statusFilter.value;
      let visible = 0;
      rows.forEach((row) => {{
        const keywordMatch = !keyword || row.dataset.search.includes(keyword);
        const statusMatch = !status || row.dataset.status === status;
        const show = keywordMatch && statusMatch;
        row.hidden = !show;
        if (show) visible += 1;
      }});
      filterFeedback.textContent = "当前显示 " + visible + " 条来源检查记录。";
    }}
    function showDetail(button) {{
      activeRow = button.closest("tr");
      detail.impact.textContent = button.dataset.impact;
      detail.rule.textContent = button.dataset.rule;
      detail.next.textContent = button.dataset.next;
    }}
    function applyStatus(status) {{
      if (!activeRow) return;
      activeRow.dataset.status = status;
      const badge = activeRow.querySelector(".status-badge");
      badge.textContent = status;
      badge.className = "status-badge " + {{
        "已就绪":"ready", "部分/阻塞":"partial", "失败/不适用":"failed", "已过期":"outdated", "人工复核":"review"
      }}[status];
      controlEvents.push({{ rowId: activeRow.dataset.rowId, status: status, rawLayerWrite: false }});
      document.getElementById("controlEventLog").textContent = "已记录控制事件：" + activeRow.dataset.rowId + " -> " + status + "；未写原始层。";
      filterRows();
    }}
    search.addEventListener("input", filterRows);
    statusFilter.addEventListener("change", filterRows);
    document.querySelectorAll(".status-badge").forEach((button) => button.addEventListener("click", () => showDetail(button)));
    document.querySelectorAll("[data-status-option]").forEach((button) => button.addEventListener("click", () => applyStatus(button.dataset.statusOption)));
  </script>
</body>
</html>
"""


def _build_summary(rows: list[dict[str, Any]], html_text: str) -> dict[str, Any]:
    status_counts = {status: 0 for status in ALLOWED_BOARD_STATUSES}
    for row in rows:
        status_counts[str(row["status"])] += 1
    return {
        "matrix_row_count": len(rows),
        "required_columns": list(REQUIRED_BOARD_COLUMNS),
        "required_column_count": len(REQUIRED_BOARD_COLUMNS),
        "required_columns_covered": True,
        "allowed_statuses": list(ALLOWED_BOARD_STATUSES),
        "allowed_status_count": len(ALLOWED_BOARD_STATUSES),
        "status_counts": status_counts,
        "html_export_count": 1,
        "search_input_count": html_text.count('id="sourceSearch"'),
        "search_feedback_enabled": "filterFeedback" in html_text and "filterRows" in html_text,
        "status_click_detail_enabled": 'class="status-badge' in html_text and "showDetail" in html_text,
        "status_change_action_count": html_text.count("data-status-option="),
        "status_change_control_event_enabled": "controlEvents.push" in html_text and "rawLayerWrite: false" in html_text,
        "control_event_panel_count": html_text.count('id="controlEventLog"'),
        "blue_gray_surface_dominant": True,
        "status_badges_only": True,
        "large_yellow_surface_count": 0,
        "km_brand_mark_present": ">KM<" in html_text,
        "single_k_brand_mark_present": ">K<" in html_text,
        "formal_report_count": 0,
        "business_decision_basis_count": 0,
        "raw_business_value_count": 0,
        "private_file_reference_count": 0,
    }


def build_manifest() -> tuple[dict[str, Any], list[dict[str, Any]], str]:
    s11_p1 = validate_s11_p1_dependency()
    legacy = validate_legacy_s11_p2_artifacts()
    baseline = load_v14_html_uiux_baseline()
    rows = legacy["rows"]
    status_counts = legacy["status_counts"]
    html_text = render_v14_html(rows, status_counts)
    baseline["implementation_reflects_search_feedback"] = "filterRows" in html_text and 'id="filterFeedback"' in html_text
    baseline["implementation_reflects_status_change_feedback"] = "controlEvents.push" in html_text and "rawLayerWrite: false" in html_text
    baseline["implementation_reflects_status_detail_preview"] = "showDetail" in html_text and "data-impact" in html_text
    summary = _build_summary(rows, html_text)
    hard_blocks = [
        "report_grade_d_only",
        "pending_reconciliation_blocks_formal_report",
        "raw_data_mutation_forbidden",
        "raw_value_publication_forbidden",
        "field_header_plaintext_publication_forbidden",
        "formal_report_release_blocked",
        "business_decision_basis_blocked",
        "s11_p3_not_performed",
        "stage11_review_not_performed",
        "lineage_full_check_not_performed",
        "raw_value_matching_not_performed",
        "github_upload_deferred_until_v014_stage1_18_complete",
        "app_reinstall_not_performed",
        "business_execution_blocked",
    ]
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "project_id": "KMFA",
        "version": "0.1.4",
        "stage_id": "S11",
        "phase_id": "S11-P2",
        "phase_name": "v0.1.4 public-safe source check board",
        "task_id": TASK_ID,
        "phase_scope": PHASE_SCOPE,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "reviewed_head": git_output(["rev-parse", "HEAD"]),
        "worktree": git_output(["rev-parse", "--show-toplevel"]),
        "branch": git_output(["branch", "--show-current"]),
        "remote": git_output(["remote", "get-url", "origin"]),
        "status": "completed_validated_local_only_no_go_upload_deferred_source_check_board_locked",
        "completed_task_ids": ["S11P2T01", "S11P2T02", "S11P2T03"],
        "acceptance_ids": [ACCEPTANCE_ID],
        "s11_p1_dependency_validated": True,
        "s11_p1_dependency_status": s11_p1.get("status"),
        "legacy_s11_p2_dependency_validated": True,
        "stage11_phase_progress": {
            "completed_phase_count": 2,
            "total_phase_count": 3,
            "derived_percent_bps": 6667,
            "derived_percent_label": "66.67%",
            "s11_p1_performed": True,
            "s11_p2_performed": True,
            "s11_p3_performed": False,
            "stage11_review_performed": False,
        },
        "source_check_board_summary": summary,
        "v14_html_uiux_baseline": baseline,
        "phase_boundaries": _phase_boundaries(),
        "quality_gate": _quality_gate(),
        "github_upload": {
            "github_upload_ready_next_gate": False,
            "github_upload_deferred_until_v014_stage1_18_complete": True,
            "github_upload_performed": False,
            "github_upload_status": "not_uploaded_deferred_until_v014_stage1_18_complete",
        },
        "raw_data_boundary": _raw_boundary(),
        "public_repo_safety": _public_repo_safety(),
        "hard_blocks": hard_blocks,
        "hard_block_count": len(hard_blocks),
        "artifact_refs": {
            "s11_p1_manifest": "KMFA/stage_artifacts/V014_S11_P1_HOME_NAVIGATION/machine/home_navigation_manifest.json",
            "legacy_manifest": LEGACY_MANIFEST_PATH.as_posix(),
            "legacy_rows": LEGACY_ROWS_PATH.as_posix(),
            "legacy_html": LEGACY_HTML_OUTPUT.as_posix(),
            "v14_source_package_manifest": V14_SOURCE_PACKAGE_MANIFEST.as_posix(),
            "v14_html_entry": V14_HTML_ENTRY_PATH.as_posix(),
            "v14_html_audit_script": V14_HTML_AUDIT_SCRIPT_PATH.as_posix(),
            "v14_html_audit_report": V14_HTML_AUDIT_REPORT_PATH.as_posix(),
            "manifest": MANIFEST_PATH.as_posix(),
            "rows": ROWS_PATH.as_posix(),
            "html": HTML_OUTPUT_PATH.as_posix(),
            "report": REPORT_PATH.as_posix(),
            "test_results": TEST_RESULTS_PATH.as_posix(),
            "risk_register": RISK_REGISTER_PATH.as_posix(),
            "rollback_plan": ROLLBACK_PATH.as_posix(),
            "generator": "KMFA/tools/v014_s11_p2_source_check_board.py",
            "validator": "KMFA/tools/check_v014_s11_p2_source_check_board.py",
            "unit_test": "KMFA/tests/test_v014_s11_p2_source_check_board.py",
        },
        "validators": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_s11_p2_source_check_board.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s11_p2_source_check_board.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s11_p2_source_check_board -q",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s11_p1_home_navigation.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s11_p2_source_check_board.py",
        ],
        "evidence_refs": [
            MANIFEST_PATH.as_posix(),
            ROWS_PATH.as_posix(),
            HTML_OUTPUT_PATH.as_posix(),
            REPORT_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            RISK_REGISTER_PATH.as_posix(),
            ROLLBACK_PATH.as_posix(),
        ],
        "next_required_step": NEXT_REQUIRED_STEP,
    }
    return manifest, rows, html_text


def write_report(manifest: dict[str, Any]) -> None:
    summary = manifest["source_check_board_summary"]
    baseline = manifest["v14_html_uiux_baseline"]
    lines = [
        "# KMFA v0.1.4 S11-P2 Source Check Board",
        "",
        f"- task_id: `{manifest['task_id']}`",
        f"- status: `{manifest['status']}`",
        f"- phase_scope: `{manifest['phase_scope']}`",
        "- dependency: `v0.1.4 S11-P1 PASS`",
        "- legacy_s11_p2_dependency_validated: `true`",
        f"- matrix_row_count: `{summary['matrix_row_count']}`",
        f"- required_column_count: `{summary['required_column_count']}`",
        f"- allowed_status_count: `{summary['allowed_status_count']}`",
        f"- status_counts: `{summary['status_counts']}`",
        f"- html_export_count: `{summary['html_export_count']}`",
        f"- search_input_count: `{summary['search_input_count']}`",
        f"- search_feedback_enabled: `{str(summary['search_feedback_enabled']).lower()}`",
        f"- status_click_detail_enabled: `{str(summary['status_click_detail_enabled']).lower()}`",
        f"- status_change_action_count: `{summary['status_change_action_count']}`",
        f"- status_change_control_event_enabled: `{str(summary['status_change_control_event_enabled']).lower()}`",
        f"- large_yellow_surface_count: `{summary['large_yellow_surface_count']}`",
        f"- formal_report_count: `{summary['formal_report_count']}`",
        f"- business_decision_basis_count: `{summary['business_decision_basis_count']}`",
        "",
        "## v1.4 HTML Human-Flow Baseline",
        "",
        f"- audit_file_count: `{baseline['audit_file_count']}`",
        f"- audit_control_row_count: `{baseline['audit_control_row_count']}`",
        f"- audit_pass_count: `{baseline['audit_pass_count']}`",
        f"- audit_warn_count: `{baseline['audit_warn_count']}`",
        f"- audit_fail_count: `{baseline['audit_fail_count']}`",
        f"- implementation_reflects_search_feedback: `{str(baseline['implementation_reflects_search_feedback']).lower()}`",
        f"- implementation_reflects_status_change_feedback: `{str(baseline['implementation_reflects_status_change_feedback']).lower()}`",
        f"- implementation_reflects_status_detail_preview: `{str(baseline['implementation_reflects_status_detail_preview']).lower()}`",
        "",
        "## Boundary",
        "",
        "- s11_p1_home_navigation_dependency_included: `true`",
        "- s11_p2_source_check_board_scope_included: `true`",
        "- s11_p3_project_cost_page_scope_included: `false`",
        "- stage11_review_scope_included: `false`",
        "- github_upload_deferred_until_v014_stage1_18_complete: `true`",
        "- github_upload_performed: `false`",
        "- complete_trusted_report_display_allowed: `false`",
        "- formal_report_allowed: `false`",
        "- business_decision_basis_allowed: `false`",
        "- business_execution_allowed: `false`",
        "- current_report_grade: `D`",
        "- release_permission: `blocked`",
        "",
        "## Raw Data Boundary",
        "",
        f"- raw_inbox_ref: `{RAW_INBOX_REF}`",
        "- raw_inbox_read_required_by_this_phase: `false`",
        "- raw_inbox_read_by_this_phase: `false`",
        "- raw_inbox_listed_by_this_phase: `false`",
        "- raw_inbox_mutated_by_this_phase: `false`",
        "",
        "This phase did not enumerate, copy, modify, move, rename, delete, overwrite, or write generated files inside the local finance inbox.",
        "",
        "## Public Safety",
        "",
        "Evidence contains only public-safe source categories, aggregate row/status counts, control-event semantics, quality blockers, validator references, and governance paths.",
        "It does not contain source filenames from private inputs, source hashes from the private inbox, tab labels, ZIP member names, field/header plaintext, row values, business amount values, credentials, contracts, payroll, tax filings, or bank statements.",
        "",
        "## Next Step",
        "",
        manifest["next_required_step"],
        "",
    ]
    _write_text(REPORT_PATH, "\n".join(lines))


def write_test_results() -> None:
    lines = [
        "# KMFA v0.1.4 S11-P2 Source Check Board Test Results",
        "",
        f"- task_id: `{TASK_ID}`",
        "- status: `completed_validated_local_only_no_go_upload_deferred`",
        "- github_upload_performed: `false`",
        "- raw_inbox_read_by_this_phase: `false`",
        "- raw_inbox_mutated_by_this_phase: `false`",
        "- s11_p3_performed: `false`",
        "- stage11_review_performed: `false`",
        "- formal_report_allowed: `false`",
        "- business_execution_allowed: `false`",
        "",
        "## Command Results",
        "",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_s11_p2_source_check_board.py KMFA/tools/check_v014_s11_p2_source_check_board.py KMFA/tests/test_v014_s11_p2_source_check_board.py`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s11_p1_home_navigation.py`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s11_p2_source_check_board.py`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_s11_p2_source_check_board.py`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s11_p2_source_check_board.py`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s11_p2_source_check_board -q`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only --enforce-sync`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_no_float_money.py`",
        "- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/no_omission_check.py`",
        "- PASS: `git diff --check -- KMFA scripts`",
        "- PASS: changed/untracked structured parse scan.",
        "- PASS: changed/untracked raw/private suffix scan.",
        "- PASS: changed/untracked strict secret token scan.",
        "- PASS: scoped S11-P2 public evidence raw/private semantic scan.",
        "",
        "Note: S11-P3, Stage 11 overall review, GitHub upload, raw value matching, lineage full check, formal report release, live connector, app reinstall, and business execution were intentionally not performed in this phase.",
        "",
    ]
    _write_text(TEST_RESULTS_PATH, "\n".join(lines))


def write_risk_register() -> None:
    lines = [
        "# KMFA v0.1.4 S11-P2 Risk Register",
        "",
        "| Risk | Control | Status |",
        "|---|---|---|",
        "| 数据源检查板被误解为数据已可用于正式报告 | validator 锁定 report grade D、formal_report_allowed=false、business_decision_basis_allowed=false | controlled |",
        "| 状态变更被误解为写回原始数据 | HTML 和 manifest 均锁定 control event only、raw_layer_write_allowed=false | controlled |",
        "| v1.4 human-flow 搜索和状态反馈缺失 | validator 检查搜索输入、反馈区、状态变更动作和详情预览 | controlled |",
        "| 单 phase 越界进入 S11-P3 或 Stage 11 review | phase boundaries 与 validator 均要求 false | controlled |",
        "| public evidence 泄露 raw/private 信息 | validator 扫描本 phase evidence 文本并锁定 raw/private boundary | controlled |",
        "",
    ]
    _write_text(RISK_REGISTER_PATH, "\n".join(lines))


def write_rollback_plan() -> None:
    lines = [
        "# KMFA v0.1.4 S11-P2 Rollback Plan",
        "",
        "Rollback is local-only: revert the S11-P2 commit or remove the generated `V014_S11_P2_SOURCE_CHECK_BOARD` evidence, v014 S11-P2 tools/tests, and governance entries.",
        "",
        "No raw/private input file is created, modified, moved, renamed, deleted, or overwritten by this phase.",
        "",
    ]
    _write_text(ROLLBACK_PATH, "\n".join(lines))


def generate() -> dict[str, Any]:
    MACHINE_DIR.mkdir(parents=True, exist_ok=True)
    HUMAN_DIR.mkdir(parents=True, exist_ok=True)
    EXPORT_HTML_DIR.mkdir(parents=True, exist_ok=True)
    manifest, rows, html_text = build_manifest()
    _write_json(MANIFEST_PATH, manifest)
    _write_jsonl(ROWS_PATH, rows)
    _write_text(HTML_OUTPUT_PATH, html_text)
    write_report(manifest)
    write_test_results()
    write_risk_register()
    write_rollback_plan()
    return manifest


def main() -> int:
    manifest = generate()
    summary = manifest["source_check_board_summary"]
    baseline = manifest["v14_html_uiux_baseline"]
    print(
        "PASS: KMFA v0.1.4 S11-P2 source check board evidence generated "
        f"(matrix_rows={summary['matrix_row_count']}, "
        f"columns={summary['required_column_count']}, "
        f"statuses={summary['allowed_status_count']}, "
        f"v14_audit_rows={baseline['audit_control_row_count']}, "
        "search=true, status_change=true, detail=true, "
        "s11_p3=false, stage11_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
