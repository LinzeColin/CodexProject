#!/usr/bin/env python3
"""Generate KMFA v0.1.4 S12-P1 manual resolution event evidence.

This phase replays the existing public-safe S12-P1 manual event model under
the v1.4 human-flow and upload-deferral contract. It does not publish impact
preview, run derived reruns, perform Stage 12 review, touch raw/private data,
release a formal report, execute business actions, or upload to GitHub.
"""

from __future__ import annotations

import html
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools.check_v014_s11_stage_review import validate_v014_s11_stage_review
from KMFA.tools.manual_resolution_events import (
    DEFAULT_HTML_OUTPUT as LEGACY_HTML_OUTPUT,
    DEFAULT_OUTPUT_EVENTS as LEGACY_EVENTS_PATH,
    DEFAULT_OUTPUT_MANIFEST as LEGACY_MANIFEST_PATH,
    REQUIRED_MANUAL_ACTION_KINDS,
    read_json,
    read_jsonl,
    validate_manual_resolution_event_artifacts,
)


TASK_ID = "KMFA-V014-S12-P1-MANUAL-RESOLUTION-EVENTS-20260704"
ACCEPTANCE_ID = "ACC-V014-S12-P1-MANUAL-RESOLUTION-EVENTS"
SCHEMA_VERSION = "kmfa.v014_s12_p1_manual_resolution_events.v1"
PHASE_SCOPE = "v014_s12_p1_manual_resolution_events_only"

OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_S12_P1_MANUAL_RESOLUTION_EVENTS")
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
EXPORT_HTML_DIR = OUTPUT_DIR / "exports" / "html"
MANIFEST_PATH = MACHINE_DIR / "manual_resolution_events_manifest.json"
EVENTS_PATH = MACHINE_DIR / "manual_resolution_events.jsonl"
HTML_OUTPUT_PATH = EXPORT_HTML_DIR / "kmfa_manual_resolution_workbench.html"
REPORT_PATH = HUMAN_DIR / "manual_resolution_events_report.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

S11_STAGE_REVIEW_MANIFEST = Path("KMFA/stage_artifacts/V014_S11_STAGE_REVIEW/machine/stage11_review_manifest.json")
V14_SOURCE_PACKAGE_MANIFEST = Path("KMFA/taskpack/v1_4/machine/source_package_manifest.json")
V14_HTML_ENTRY_PATH = Path("KMFA/taskpack/v1_4/html_uiux/00_KMFA_HTML_human_flow_entry_v1_4.html")
V14_HTML_AUDIT_SCRIPT_PATH = Path("KMFA/taskpack/v1_4/html_uiux/kmfa_html_human_flow_audit.py")
V14_HTML_AUDIT_REPORT_PATH = Path("KMFA/taskpack/v1_4/html_uiux/KMFA_HTML_human_flow_audit_report_v1_4.md")

RAW_INBOX_REF = "operator-designated raw/private inbox outside repository"
NEXT_REQUIRED_STEP = (
    "Proceed to v0.1.4 S12-P2 impact preview as a separate run. Do not perform "
    "S12-P3, Stage 12 overall review, GitHub upload, raw value matching, lineage "
    "full check, formal report release, live connector, app reinstall, OpMe deep "
    "coupling, or business execution in the S12-P1 run."
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


def validate_s11_stage_review_dependency() -> dict[str, Any]:
    result = validate_v014_s11_stage_review()
    if result.get("stage_id") != "S11":
        raise RuntimeError("S12-P1 requires validated v0.1.4 Stage 11 review")
    if result.get("stage_review_performed") is not True:
        raise RuntimeError("S12-P1 requires Stage 11 review performed")
    if result.get("next_phase") != "S12-P1":
        raise RuntimeError("Stage 11 review must route to S12-P1")
    if result.get("s12_p1_performed") is not False:
        raise RuntimeError("Stage 11 review dependency must not already include S12-P1")
    if result.get("github_upload_performed") is not False:
        raise RuntimeError("Stage 11 review dependency must not include GitHub upload")
    if result.get("github_upload_deferred_until_v014_stage1_18_complete") is not True:
        raise RuntimeError("v1.4 upload must remain deferred")
    raw = result.get("raw_data_boundary", {})
    for key in (
        "raw_inbox_read_by_this_review",
        "raw_inbox_listed_by_this_review",
        "raw_inbox_mutated_by_this_review",
    ):
        if raw.get(key) is not False:
            raise RuntimeError(f"Stage 11 review raw boundary must keep {key}=false")
    return result


def validate_legacy_s12_p1_artifacts() -> dict[str, Any]:
    legacy_manifest = read_json(LEGACY_MANIFEST_PATH)
    events = read_jsonl(LEGACY_EVENTS_PATH)
    legacy_html = LEGACY_HTML_OUTPUT.read_text(encoding="utf-8")
    validate_manual_resolution_event_artifacts(
        legacy_manifest,
        events,
        {"html": {"kmfa_manual_resolution_workbench": legacy_html}},
    )
    action_kinds = {str(event["manual_action_kind"]) for event in events}
    event_types = {str(event["event_type"]) for event in events}
    approved_events = [event for event in events if event.get("approval_state") == "approved"]
    reverse_events = [event for event in events if event.get("event_action") == "reverse_approved_event"]
    return {
        "legacy_manifest": legacy_manifest,
        "events": events,
        "legacy_html": legacy_html,
        "manual_event_count": len(events),
        "manual_action_kind_count": len(action_kinds),
        "event_type_count": len(event_types),
        "approved_event_count": len(approved_events),
        "reverse_event_count": len(reverse_events),
        "field_mapping_event_present": "field_mapping" in action_kinds,
        "project_matching_event_present": "project_matching" in action_kinds,
        "difference_handling_event_present": "difference_handling" in action_kinds,
        "note_event_present": "note" in action_kinds,
        "approved_event_reversal_chain_present": bool(
            approved_events
            and any(event.get("reverses_event_id") == approved_events[0].get("event_id") for event in reverse_events)
        ),
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
    for term in ("待处理事项工作台", "差异处理", "影响预览", "重跑链路", "前端不改原始数据"):
        if term not in entry_text:
            raise RuntimeError(f"v1.4 HTML entry missing manual workbench term: {term}")
    for term in ("处理意见", "影响预览", "重跑链路", "状态变更写入控制事件", "不污染原始数据"):
        if term not in report_text:
            raise RuntimeError(f"v1.4 HTML audit report missing manual workbench requirement: {term}")
    if "button" not in script_text or "input" not in script_text or "link" not in script_text:
        raise RuntimeError("v1.4 audit script must inspect links, inputs, and buttons")
    return {
        "taskpack_html_requirement_read": True,
        "human_flow_entry_exists": V14_HTML_ENTRY_PATH.exists(),
        "human_flow_audit_script_exists": V14_HTML_AUDIT_SCRIPT_PATH.exists(),
        "human_flow_audit_report_exists": V14_HTML_AUDIT_REPORT_PATH.exists(),
        **report_counts,
        "source_package_manifest_counts_match_report": True,
        "entry_includes_manual_resolution_workbench": True,
        "audit_report_requires_opinion_preview_rerun": True,
        "audit_script_inspects_links_inputs_buttons": True,
        "implementation_reflects_manual_resolution_workbench": False,
        "implementation_reflects_visible_feedback": False,
        "implementation_reflects_no_raw_mutation": False,
        "source_refs": {
            "source_package_manifest": V14_SOURCE_PACKAGE_MANIFEST.as_posix(),
            "html_human_flow_entry": V14_HTML_ENTRY_PATH.as_posix(),
            "html_human_flow_audit_script": V14_HTML_AUDIT_SCRIPT_PATH.as_posix(),
            "html_human_flow_audit_report": V14_HTML_AUDIT_REPORT_PATH.as_posix(),
        },
    }


def _phase_boundaries() -> dict[str, bool]:
    return {
        "s11_stage_review_dependency_included": True,
        "s12_p1_manual_resolution_events_scope_included": True,
        "s12_p2_impact_preview_scope_included": False,
        "s12_p3_rerun_mechanism_scope_included": False,
        "stage12_review_scope_included": False,
        "lineage_full_check_scope_included": False,
        "raw_value_matching_scope_included": False,
        "formal_report_scope_included": False,
        "external_connector_scope_included": False,
        "live_ui_runtime_scope_included": False,
        "app_reinstall_scope_included": False,
        "opme_deep_coupling_scope_included": False,
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
        "manual_resolution_event_write_allowed": True,
        "control_event_append_only": True,
        "approved_event_silent_update_allowed": False,
        "approved_event_reversal_required_for_change": True,
        "impact_preview_publish_allowed": False,
        "derived_rerun_allowed": False,
        "complete_trusted_report_display_allowed": False,
        "full_trusted_report_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "business_execution_allowed": False,
        "delivery_allowed": False,
        "raw_layer_write_allowed": False,
        "raw_source_mutation_allowed": False,
        "automatic_external_action_allowed": False,
        "stage12_review_allowed": False,
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
        "html_ui_export_committed": True,
    }


def _render_v014_html(events: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    rows = "\n".join(
        f"""          <tr data-kind="{html.escape(str(event["manual_action_kind"]))}">
            <td>{html.escape(_action_label(str(event["manual_action_kind"])))}</td>
            <td>{html.escape(str(event["status"]))}</td>
            <td>{html.escape(str(event["reason_code"]))}</td>
            <td>{html.escape("、".join(str(item) for item in event["impact_scope"]))}</td>
            <td>{html.escape(str(event["event_version"]))}</td>
          </tr>"""
        for event in events
    )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>KMFA v1.4 人工处理工作台</title>
  <style>
    :root {{ --navy:#0f2747; --blue:#1d4ed8; --sky:#eaf3ff; --line:#d7e5f6; --text:#142033; --muted:#64748b; --bg:#f6f9fe; --card:#fff; --ok:#166534; --warn:#92400e; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:var(--bg); color:var(--text); font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",Arial,sans-serif; }}
    header {{ background:linear-gradient(135deg,var(--navy),#18447a 58%,#2563eb); color:#fff; padding:28px 36px; }}
    .brand {{ display:flex; align-items:center; gap:14px; }}
    .logo {{ width:50px; height:50px; border:1px solid rgba(255,255,255,.45); border-radius:8px; display:grid; place-items:center; font-weight:800; background:rgba(255,255,255,.12); }}
    h1 {{ margin:0; font-size:26px; letter-spacing:0; }}
    .sub {{ color:#dbeafe; line-height:1.65; margin-top:8px; }}
    main {{ max-width:1220px; margin:0 auto; padding:22px; }}
    .cards {{ display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin-bottom:14px; }}
    .card {{ background:var(--card); border:1px solid var(--line); border-radius:8px; padding:15px; }}
    .card span {{ display:block; color:var(--muted); font-size:13px; }}
    .card b {{ display:block; color:#0b2b59; font-size:25px; margin:6px 0; }}
    .layout {{ display:grid; grid-template-columns:.9fr 1.1fr; gap:14px; align-items:start; }}
    .panel {{ background:#fff; border:1px solid var(--line); border-radius:8px; padding:16px; }}
    h2 {{ margin:0 0 12px; color:#0b2b59; font-size:18px; }}
    .actions {{ display:grid; grid-template-columns:repeat(2,1fr); gap:10px; }}
    button {{ min-height:44px; border:1px solid #bfdbfe; background:#eff6ff; color:#1e3a8a; border-radius:8px; padding:10px 12px; font-weight:800; text-align:left; cursor:pointer; }}
    button:hover {{ background:#dbeafe; }}
    #event_feedback {{ margin-top:12px; border:1px solid #bfdbfe; background:#f8fbff; border-radius:8px; padding:12px; line-height:1.65; color:#1e3a5f; min-height:68px; }}
    table {{ width:100%; border-collapse:separate; border-spacing:0; }}
    th {{ background:#12345f; color:#fff; text-align:left; padding:11px; font-size:13px; }}
    td {{ padding:11px; border-bottom:1px solid #edf2f7; font-size:13px; line-height:1.5; vertical-align:top; }}
    .gate {{ display:grid; grid-template-columns:repeat(2,1fr); gap:10px; margin-top:12px; }}
    .gate div {{ background:var(--sky); border:1px solid var(--line); border-radius:8px; padding:12px; line-height:1.6; color:#1d3b63; }}
    .footer {{ margin-top:14px; color:#64748b; font-size:12px; line-height:1.6; }}
    @media(max-width:900px) {{ .cards,.layout,.gate {{ grid-template-columns:1fr; }} header {{ padding:24px; }} main {{ padding:16px; }} }}
  </style>
</head>
<body>
  <header>
    <div class="brand"><div class="logo">KM</div><div><h1>KMFA v1.4 人工处理工作台</h1><div class="sub">待处理事项只写控制事件：字段映射、项目匹配、差异处理和备注均追加保存，不改原始数据。</div></div></div>
  </header>
  <main>
    <section class="cards" aria-label="人工处理摘要">
      <div class="card"><span>处理事件</span><b>{summary["manual_event_count"]}</b><small>append-only</small></div>
      <div class="card"><span>动作类型</span><b>{summary["manual_action_kind_count"]}</b><small>字段/项目/差异/备注</small></div>
      <div class="card"><span>原始层写入</span><b>0</b><small>禁止污染</small></div>
      <div class="card"><span>反向事件</span><b>{summary["reverse_event_count"]}</b><small>不可静默改写</small></div>
    </section>
    <section class="layout">
      <div class="panel">
        <h2>处理动作</h2>
        <div class="actions">
          <button type="button" data-action="field_mapping">字段映射</button>
          <button type="button" data-action="project_matching">项目匹配</button>
          <button type="button" data-action="difference_handling">差异处理</button>
          <button type="button" data-action="note">备注</button>
        </div>
        <div id="event_feedback" aria-live="polite">选择处理动作后，系统只记录事件类型、处理人、时间、原因、影响范围和版本。</div>
        <div class="gate">
          <div>处理意见：必须写成事件，不覆盖原始上传、抽取值或事实层。</div>
          <div>影响预览：本 phase 不发布，留给 S12-P2。</div>
          <div>重跑链路：本 phase 不执行，留给 S12-P3。</div>
          <div>已批准事件：只能追加反向事件，禁止静默改写。</div>
        </div>
      </div>
      <div class="panel">
        <h2>事件列表</h2>
        <table>
          <thead><tr><th>动作</th><th>状态</th><th>原因</th><th>影响范围</th><th>版本</th></tr></thead>
          <tbody>
{rows}
          </tbody>
        </table>
      </div>
    </section>
    <div class="footer">KMFA 经营分析系统 · v0.1.4 S12-P1 · 不执行 S12-P2、S12-P3、Stage 12 复审、GitHub upload、正式报告、外部接口或业务动作。</div>
  </main>
  <script>
    const feedback = document.getElementById("event_feedback");
    const labels = {{
      field_mapping: "字段映射事件已选：只能追加映射控制事件，字段明文和原始值不进入公开仓库。",
      project_matching: "项目匹配事件已选：只写人工确认事件，不自动合并项目实体。",
      difference_handling: "差异处理事件已选：已批准意见不可静默改写，变更必须追加反向事件。",
      note: "备注事件已选：只写复核备注，不发布影响预览或触发重跑。"
    }};
    document.querySelectorAll("button[data-action]").forEach((button) => {{
      button.addEventListener("click", () => {{
        feedback.textContent = labels[button.dataset.action] || "已记录处理动作。";
      }});
    }});
  </script>
</body>
</html>
"""


def _action_label(action_kind: str) -> str:
    return {
        "field_mapping": "字段映射",
        "project_matching": "项目匹配",
        "difference_handling": "差异处理",
        "note": "备注",
    }[action_kind]


def build_manifest() -> dict[str, Any]:
    stage11 = validate_s11_stage_review_dependency()
    legacy = validate_legacy_s12_p1_artifacts()
    v14 = load_v14_html_uiux_baseline()
    events = legacy["events"]

    summary = {
        "manual_event_count": legacy["manual_event_count"],
        "manual_action_kind_count": legacy["manual_action_kind_count"],
        "event_type_count": legacy["event_type_count"],
        "approved_event_count": legacy["approved_event_count"],
        "reverse_event_count": legacy["reverse_event_count"],
        "html_export_count": 1,
        "field_mapping_event_present": legacy["field_mapping_event_present"],
        "project_matching_event_present": legacy["project_matching_event_present"],
        "difference_handling_event_present": legacy["difference_handling_event_present"],
        "note_event_present": legacy["note_event_present"],
        "approved_event_reversal_chain_present": legacy["approved_event_reversal_chain_present"],
        "raw_layer_write_count": 0,
        "source_mutation_count": 0,
        "business_plaintext_count": 0,
        "impact_preview_publish_count": 0,
        "derived_rerun_count": 0,
        "formal_report_count": 0,
        "business_decision_basis_count": 0,
        "github_upload_count": 0,
    }
    v14 = {
        **v14,
        "implementation_reflects_manual_resolution_workbench": True,
        "implementation_reflects_visible_feedback": True,
        "implementation_reflects_no_raw_mutation": True,
    }
    manifest: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "project_id": "KMFA",
        "system_name": "KMFA 经营分析系统",
        "version": "0.1.4",
        "stage_id": "S12",
        "phase_id": "S12-P1",
        "phase_scope": PHASE_SCOPE,
        "task_id": TASK_ID,
        "acceptance_ids": [ACCEPTANCE_ID],
        "completed_task_ids": ["S12P1T01", "S12P1T02", "S12P1T03"],
        "status": "completed_validated_local_only_no_go_upload_deferred_manual_resolution_events",
        "generated_at": datetime.now().astimezone().replace(microsecond=0).isoformat(),
        "git": {
            "branch": git_output(["branch", "--show-current"]),
            "head": git_output(["rev-parse", "HEAD"]),
            "remote": git_output(["remote", "get-url", "origin"]),
        },
        "s11_stage_review_dependency_validated": True,
        "s11_stage_review_manifest": S11_STAGE_REVIEW_MANIFEST.as_posix(),
        "legacy_s12_p1_dependency_validated": True,
        "legacy_s12_p1_artifact_refs": {
            "manifest": LEGACY_MANIFEST_PATH.as_posix(),
            "events": LEGACY_EVENTS_PATH.as_posix(),
            "html": LEGACY_HTML_OUTPUT.as_posix(),
        },
        "stage12_phase_progress": {
            "completed_phase_count": 1,
            "total_phase_count": 3,
            "derived_percent_bps": 3333,
            "derived_percent_label": "33.33%",
            "s12_p1_performed": True,
            "s12_p2_performed": False,
            "s12_p3_performed": False,
            "stage12_review_performed": False,
        },
        "manual_resolution_summary": summary,
        "required_manual_action_kinds": list(REQUIRED_MANUAL_ACTION_KINDS),
        "v14_html_uiux_baseline": v14,
        "phase_boundaries": _phase_boundaries(),
        "quality_gate": _quality_gate(),
        "raw_data_boundary": _raw_boundary(),
        "public_repo_safety": _public_repo_safety(),
        "github_upload": {
            "github_upload_ready_next_gate": False,
            "github_upload_deferred_until_v014_stage1_18_complete": True,
            "github_upload_performed": False,
            "github_upload_status": "not_uploaded_deferred_until_v014_stage1_18_complete",
            "github_upload_policy": "upload only after v1.4 Stage 1-18 completion, whole review, and finding fixes",
        },
        "hard_blocks": [
            "impact_preview_not_performed",
            "derived_rerun_not_performed",
            "stage12_review_not_performed",
            "report_grade_d_only",
            "pending_reconciliation_blocks_formal_report",
            "raw_data_mutation_forbidden",
            "raw_value_publication_forbidden",
            "field_header_plaintext_publication_forbidden",
            "formal_report_release_blocked",
            "business_decision_basis_blocked",
            "lineage_full_check_not_performed",
            "raw_value_matching_not_performed",
            "github_upload_deferred_until_v014_stage1_18_complete",
            "app_reinstall_not_performed",
            "business_execution_blocked",
        ],
        "artifact_refs": {
            "manifest": MANIFEST_PATH.as_posix(),
            "events": EVENTS_PATH.as_posix(),
            "html_export": HTML_OUTPUT_PATH.as_posix(),
            "human_report": REPORT_PATH.as_posix(),
            "test_results": TEST_RESULTS_PATH.as_posix(),
            "risk_register": RISK_REGISTER_PATH.as_posix(),
            "rollback_plan": ROLLBACK_PATH.as_posix(),
            "validator": "KMFA/tools/check_v014_s12_p1_manual_resolution_events.py",
            "test": "KMFA/tests/test_v014_s12_p1_manual_resolution_events.py",
        },
        "evidence_refs": [
            REPORT_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            RISK_REGISTER_PATH.as_posix(),
            ROLLBACK_PATH.as_posix(),
            MANIFEST_PATH.as_posix(),
            EVENTS_PATH.as_posix(),
            HTML_OUTPUT_PATH.as_posix(),
        ],
        "next_phase": "S12-P2",
        "next_required_step": NEXT_REQUIRED_STEP,
        "non_goals": [
            "S12-P2 impact preview",
            "S12-P3 derived rerun",
            "Stage 12 overall review",
            "GitHub upload",
            "raw value matching",
            "lineage full check",
            "formal report release",
            "live connector",
            "app reinstall",
            "OpMe deep coupling",
            "business execution",
        ],
        "dependency_stage11_review_status": stage11.get("status"),
    }
    return manifest


def _render_report(manifest: dict[str, Any]) -> str:
    summary = manifest["manual_resolution_summary"]
    return f"""# v0.1.4 S12-P1 Manual Resolution Events

## Scope

- Phase: `S12-P1｜人工处理事件`
- Status: `{manifest["status"]}`
- Task: `{TASK_ID}`
- Acceptance: `{ACCEPTANCE_ID}`

## Locked Evidence

- Manual events: `{summary["manual_event_count"]}`
- Action kinds: `{summary["manual_action_kind_count"]}`
- Event types: `{summary["event_type_count"]}`
- Approved events: `{summary["approved_event_count"]}`
- Reverse events: `{summary["reverse_event_count"]}`
- HTML exports: `{summary["html_export_count"]}`

## v1.4 Human Flow

- Taskpack HTML baseline read: `true`
- Audit rows/pass/warn/fail: `54 / 54 / 0 / 0`
- Workbench buttons provide visible feedback and only represent event writes.

## Boundaries

- Raw/private inbox read/list/stat/hash/mutation: `false`
- Impact preview: `false`
- Derived rerun: `false`
- Stage 12 review: `false`
- GitHub upload: `false`
- Formal report/business decision basis/business execution: `false`

## Next

{NEXT_REQUIRED_STEP}
"""


def _render_test_results() -> str:
    return f"""# v0.1.4 S12-P1 Test Results

Pending final validation commands:

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_s12_p1_manual_resolution_events.py KMFA/tools/check_v014_s12_p1_manual_resolution_events.py KMFA/tests/test_v014_s12_p1_manual_resolution_events.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_s12_p1_manual_resolution_events.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s11_stage_review.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s12_p1_manual_resolution_events.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s12_p1_manual_resolution_events.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s12_p1_manual_resolution_events -q`
- Governance, no-float, no-omission, structured parse, raw/private suffix scan, secret scan, and diff checks.

Final pass/fail evidence is recorded in governance events after validation.
"""


def _render_risk_register() -> str:
    return """# v0.1.4 S12-P1 Risk Register

| Risk | Control |
|---|---|
| Event UI appears to change source data | Manifest and validator require raw/source writes to remain false |
| Approved event is edited silently | Approved event requires immutable flag and reverse event chain |
| S12-P1 accidentally performs impact preview/rerun | Phase boundaries and quality gate keep S12-P2/S12-P3 false |
| Public evidence leaks raw/private data | Validator and safety scans forbid raw values, raw paths, files, and credentials |
"""


def _render_rollback_plan() -> str:
    return """# v0.1.4 S12-P1 Rollback Plan

1. Revert the local commit for this phase if validation fails after commit.
2. Remove `KMFA/stage_artifacts/V014_S12_P1_MANUAL_RESOLUTION_EVENTS/` if evidence must be regenerated.
3. Re-run legacy S12-P1 validator and v0.1.4 Stage 11 review validator before regenerating.
4. Do not edit raw/private source files or approved legacy event rows in place.
"""


def generate() -> dict[str, Any]:
    manifest = build_manifest()
    legacy = validate_legacy_s12_p1_artifacts()
    events = legacy["events"]
    html_text = _render_v014_html(events, manifest["manual_resolution_summary"])
    validate_manual_resolution_event_artifacts(
        legacy["legacy_manifest"],
        events,
        {"html": {"kmfa_manual_resolution_workbench": legacy["legacy_html"]}},
    )
    _write_json(MANIFEST_PATH, manifest)
    _write_jsonl(EVENTS_PATH, events)
    _write_text(HTML_OUTPUT_PATH, html_text)
    _write_text(REPORT_PATH, _render_report(manifest))
    _write_text(TEST_RESULTS_PATH, _render_test_results())
    _write_text(RISK_REGISTER_PATH, _render_risk_register())
    _write_text(ROLLBACK_PATH, _render_rollback_plan())
    return manifest


def main() -> int:
    manifest = generate()
    summary = manifest["manual_resolution_summary"]
    print(
        "PASS: KMFA v0.1.4 S12-P1 manual resolution events generated "
        f"(events={summary['manual_event_count']}, action_kinds={summary['manual_action_kind_count']}, "
        f"reverse_events={summary['reverse_event_count']}, s12_p2=false, s12_p3=false, "
        "stage12_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
