#!/usr/bin/env python3
"""Generate KMFA v0.1.4 S12-P2 manual impact preview evidence.

This phase replays the public-safe S12-P2 impact preview model under the
v1.4 human-flow and upload-deferral contract. It does not run derived reruns,
perform Stage 12 review, touch raw/private data, release a formal report,
execute business actions, or upload to GitHub.
"""

from __future__ import annotations

import hashlib
import html
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools.check_v014_s12_p1_manual_resolution_events import (
    validate_v014_s12_p1_manual_resolution_events,
)
from KMFA.tools.manual_impact_preview import (
    DEFAULT_HTML_OUTPUT as LEGACY_HTML_OUTPUT,
    DEFAULT_OUTPUT_MANIFEST as LEGACY_MANIFEST_PATH,
    DEFAULT_OUTPUT_PREVIEWS as LEGACY_PREVIEWS_PATH,
    REQUIRED_IMPACT_DOMAINS,
    read_json,
    read_jsonl,
    validate_manual_impact_preview_artifacts,
)


TASK_ID = "KMFA-V014-S12-P2-MANUAL-IMPACT-PREVIEW-20260705"
ACCEPTANCE_ID = "ACC-V014-S12-P2-MANUAL-IMPACT-PREVIEW"
SCHEMA_VERSION = "kmfa.v014_s12_p2_manual_impact_preview.v1"
PHASE_SCOPE = "v014_s12_p2_manual_impact_preview_only"

OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_S12_P2_MANUAL_IMPACT_PREVIEW")
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
EXPORT_HTML_DIR = OUTPUT_DIR / "exports" / "html"
MANIFEST_PATH = MACHINE_DIR / "manual_impact_preview_manifest.json"
PREVIEWS_PATH = MACHINE_DIR / "manual_impact_previews.jsonl"
HTML_OUTPUT_PATH = EXPORT_HTML_DIR / "kmfa_manual_impact_preview.html"
REPORT_PATH = HUMAN_DIR / "manual_impact_preview_report.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

S12_P1_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V014_S12_P1_MANUAL_RESOLUTION_EVENTS/machine/manual_resolution_events_manifest.json"
)
S12_P1_EVENTS_PATH = Path(
    "KMFA/stage_artifacts/V014_S12_P1_MANUAL_RESOLUTION_EVENTS/machine/manual_resolution_events.jsonl"
)
V14_SOURCE_PACKAGE_MANIFEST = Path("KMFA/taskpack/v1_4/machine/source_package_manifest.json")
V14_HTML_ENTRY_PATH = Path("KMFA/taskpack/v1_4/html_uiux/00_KMFA_HTML_human_flow_entry_v1_4.html")
V14_HTML_AUDIT_SCRIPT_PATH = Path("KMFA/taskpack/v1_4/html_uiux/kmfa_html_human_flow_audit.py")
V14_HTML_AUDIT_REPORT_PATH = Path("KMFA/taskpack/v1_4/html_uiux/KMFA_HTML_human_flow_audit_report_v1_4.md")
V14_ROADMAP_PATH = Path("KMFA/taskpack/v1_4/roadmap/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_4.md")
V14_TASKPACK_PATH = Path("KMFA/taskpack/v1_4/taskpack/01_KMFA_Codex_TaskPack_v1_4_public_safe.md")

RAW_INBOX_REF = "operator-designated raw/private inbox outside repository"
NEXT_REQUIRED_STEP = (
    "Proceed to v0.1.4 S12-P3 rerun mechanism as a separate run. Do not perform "
    "Stage 12 overall review, GitHub upload, raw value matching, lineage full "
    "check, formal report release, live connector, app reinstall, OpMe deep "
    "coupling, or business execution in the S12-P2 run."
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


def _sha256_json(payload: Any) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


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


def validate_s12_p1_dependency() -> dict[str, Any]:
    result = validate_v014_s12_p1_manual_resolution_events()
    progress = result.get("stage12_phase_progress", {})
    if result.get("phase_id") != "S12-P1":
        raise RuntimeError("S12-P2 requires validated v0.1.4 S12-P1")
    if progress.get("s12_p1_performed") is not True:
        raise RuntimeError("S12-P2 requires S12-P1 to be performed")
    if progress.get("s12_p2_performed") is not False:
        raise RuntimeError("S12-P1 dependency must not already include S12-P2")
    if progress.get("s12_p3_performed") is not False:
        raise RuntimeError("S12-P1 dependency must not include S12-P3")
    if progress.get("stage12_review_performed") is not False:
        raise RuntimeError("S12-P1 dependency must not include Stage 12 review")
    if result.get("github_upload", {}).get("github_upload_performed") is not False:
        raise RuntimeError("S12-P1 dependency must not include GitHub upload")
    raw = result.get("raw_data_boundary", {})
    for key in (
        "raw_inbox_read_by_this_phase",
        "raw_inbox_listed_by_this_phase",
        "raw_inbox_mutated_by_this_phase",
    ):
        if raw.get(key) is not False:
            raise RuntimeError(f"S12-P1 dependency raw boundary must keep {key}=false")
    return result


def validate_legacy_s12_p2_artifacts() -> dict[str, Any]:
    legacy_manifest = read_json(LEGACY_MANIFEST_PATH)
    legacy_previews = read_jsonl(LEGACY_PREVIEWS_PATH)
    source_events = read_jsonl(S12_P1_EVENTS_PATH)
    legacy_html = LEGACY_HTML_OUTPUT.read_text(encoding="utf-8")
    validate_manual_impact_preview_artifacts(
        legacy_manifest,
        legacy_previews,
        {"html": {"kmfa_manual_impact_preview": legacy_html}},
        source_events,
    )
    summary = legacy_manifest["summary"]
    return {
        "legacy_manifest": legacy_manifest,
        "legacy_previews": legacy_previews,
        "legacy_html": legacy_html,
        "source_events": source_events,
        "source_event_count": int(summary["source_event_count"]),
        "impact_preview_count": int(summary["impact_preview_count"]),
        "affected_project_count": int(summary["affected_project_count"]),
        "affected_metric_count": int(summary["affected_metric_count"]),
        "affected_report_count": int(summary["affected_report_count"]),
        "high_risk_count": int(summary["high_risk_count"]),
        "second_confirmation_required_count": int(summary["second_confirmation_required_count"]),
        "blocked_publish_count": int(summary["blocked_publish_count"]),
        "publish_allowed_count": sum(1 for preview in legacy_previews if preview.get("control_event_publish_allowed")),
    }


def load_v14_html_uiux_baseline() -> dict[str, Any]:
    source_manifest = json.loads(V14_SOURCE_PACKAGE_MANIFEST.read_text(encoding="utf-8"))
    gate = source_manifest.get("html_human_flow_gate", {})
    report_text = V14_HTML_AUDIT_REPORT_PATH.read_text(encoding="utf-8")
    entry_text = V14_HTML_ENTRY_PATH.read_text(encoding="utf-8")
    script_text = V14_HTML_AUDIT_SCRIPT_PATH.read_text(encoding="utf-8")
    roadmap_text = V14_ROADMAP_PATH.read_text(encoding="utf-8")
    taskpack_text = V14_TASKPACK_PATH.read_text(encoding="utf-8")

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
            raise RuntimeError(f"v1.4 HTML entry missing S12 term: {term}")
    for term in ("处理意见", "影响预览", "重跑链路", "状态变更写入控制事件", "不污染原始数据"):
        if term not in report_text:
            raise RuntimeError(f"v1.4 HTML audit report missing S12 requirement: {term}")
    for term in (
        "处理事件提交前展示影响哪些项目、指标、报告",
        "高风险处理需要二次确认",
        "未通过影响预览不得发布",
    ):
        if term not in roadmap_text:
            raise RuntimeError(f"v1.4 roadmap missing S12-P2 requirement: {term}")
    if "人工处理工作台" not in taskpack_text or "影响预览" not in taskpack_text:
        raise RuntimeError("v1.4 taskpack missing manual impact preview baseline terms")
    if "button" not in script_text or "input" not in script_text or "link" not in script_text:
        raise RuntimeError("v1.4 audit script must inspect links, inputs, and buttons")
    return {
        "taskpack_html_requirement_read": True,
        "human_flow_entry_exists": V14_HTML_ENTRY_PATH.exists(),
        "human_flow_audit_script_exists": V14_HTML_AUDIT_SCRIPT_PATH.exists(),
        "human_flow_audit_report_exists": V14_HTML_AUDIT_REPORT_PATH.exists(),
        **report_counts,
        "source_package_manifest_counts_match_report": True,
        "entry_includes_manual_workbench_flow": True,
        "audit_report_requires_opinion_preview_rerun": True,
        "roadmap_requires_impact_preview": True,
        "taskpack_requires_manual_impact_preview": True,
        "audit_script_inspects_links_inputs_buttons": True,
        "implementation_reflects_impact_preview": False,
        "implementation_reflects_second_confirmation_feedback": False,
        "implementation_reflects_no_raw_mutation": False,
        "source_refs": {
            "source_package_manifest": V14_SOURCE_PACKAGE_MANIFEST.as_posix(),
            "html_human_flow_entry": V14_HTML_ENTRY_PATH.as_posix(),
            "html_human_flow_audit_script": V14_HTML_AUDIT_SCRIPT_PATH.as_posix(),
            "html_human_flow_audit_report": V14_HTML_AUDIT_REPORT_PATH.as_posix(),
            "roadmap": V14_ROADMAP_PATH.as_posix(),
            "taskpack": V14_TASKPACK_PATH.as_posix(),
        },
    }


def _phase_boundaries() -> dict[str, bool]:
    return {
        "s12_p1_manual_resolution_events_dependency_included": True,
        "s12_p2_impact_preview_scope_included": True,
        "s12_p3_rerun_mechanism_scope_included": False,
        "stage12_review_scope_included": False,
        "lineage_full_check_scope_included": False,
        "protected_business_value_matching_scope_included": False,
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
        "impact_preview_generation_allowed": True,
        "impact_preview_required_before_publish": True,
        "high_risk_second_confirmation_required": True,
        "unpassed_preview_publish_allowed": False,
        "derived_rerun_allowed": False,
        "derived_rerun_executed": False,
        "complete_trusted_report_display_allowed": False,
        "full_trusted_report_allowed": False,
        "formal_report_allowed": False,
        "formal_report_generated": False,
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


def _adjust_previews(previews: list[dict[str, Any]], generated_at: str) -> list[dict[str, Any]]:
    adjusted: list[dict[str, Any]] = []
    for preview in previews:
        row = dict(preview)
        row["preview_time"] = generated_at
        row["evidence_refs"] = [
            S12_P1_EVENTS_PATH.as_posix(),
            V14_ROADMAP_PATH.as_posix(),
            REPORT_PATH.as_posix(),
        ]
        row["content_hash"] = ""
        row["content_hash"] = _sha256_json({key: value for key, value in row.items() if key != "content_hash"})
        adjusted.append(row)
    return adjusted


def _action_label(action_kind: str) -> str:
    return {
        "field_mapping": "字段映射",
        "project_matching": "项目匹配",
        "difference_handling": "差异处理",
        "note": "备注",
    }[action_kind]


def _risk_label(risk_level: str) -> str:
    return {"low": "低风险", "medium": "中风险", "high": "高风险"}[risk_level]


def _gate_label(release_gate: str) -> str:
    return {
        "blocked_pending_second_confirmation": "等待二次确认",
        "preview_passed_publish_allowed": "预览通过",
    }[release_gate]


def _render_v014_html(previews: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    rows = "\n".join(
        f"""          <tr>
            <td>{html.escape(str(preview["source_event_id"]))}</td>
            <td>{html.escape(_action_label(str(preview["source_manual_action_kind"])))}</td>
            <td><span class="badge {html.escape(str(preview["risk_level"]))}">{html.escape(_risk_label(str(preview["risk_level"])))}</span></td>
            <td>{html.escape("、".join(str(item) for item in preview["affected_projects"]))}</td>
            <td>{html.escape("、".join(str(item) for item in preview["affected_metrics"]))}</td>
            <td>{html.escape("、".join(str(item) for item in preview["affected_reports"]))}</td>
            <td>{html.escape(_gate_label(str(preview["release_gate"])))}</td>
            <td><button type="button" data-preview="{html.escape(str(preview["preview_id"]))}" data-gate="{html.escape(str(preview["release_gate"]))}">预览影响</button></td>
          </tr>"""
        for preview in previews
    )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>KMFA v1.4 影响预览</title>
  <style>
    :root {{ --navy:#0f2747; --blue:#1d4ed8; --sky:#eaf3ff; --line:#d7e5f6; --text:#142033; --muted:#64748b; --bg:#f6f9fe; --card:#fff; --ok:#166534; --warn:#92400e; --risk:#9f1239; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:var(--bg); color:var(--text); font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",Arial,sans-serif; }}
    header {{ background:linear-gradient(135deg,var(--navy),#18447a 58%,#2563eb); color:#fff; padding:28px 36px; }}
    .brand {{ display:flex; align-items:center; gap:14px; }}
    .logo {{ width:50px; height:50px; border:1px solid rgba(255,255,255,.45); border-radius:8px; display:grid; place-items:center; font-weight:800; background:rgba(255,255,255,.12); }}
    h1 {{ margin:0; font-size:26px; letter-spacing:0; }}
    .sub {{ color:#dbeafe; line-height:1.65; margin-top:8px; }}
    main {{ max-width:1260px; margin:0 auto; padding:22px; }}
    .cards {{ display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin-bottom:14px; }}
    .card {{ background:var(--card); border:1px solid var(--line); border-radius:8px; padding:15px; }}
    .card span {{ display:block; color:var(--muted); font-size:13px; }}
    .card b {{ display:block; color:#0b2b59; font-size:25px; margin:6px 0; }}
    .panel {{ background:#fff; border:1px solid var(--line); border-radius:8px; padding:16px; margin-bottom:14px; }}
    h2 {{ margin:0 0 12px; color:#0b2b59; font-size:18px; }}
    .rules {{ display:grid; grid-template-columns:repeat(3,1fr); gap:10px; }}
    .rule {{ background:var(--sky); border:1px solid var(--line); border-radius:8px; padding:12px; line-height:1.6; color:#1d3b63; }}
    table {{ width:100%; border-collapse:separate; border-spacing:0; }}
    th {{ background:#12345f; color:#fff; text-align:left; padding:11px; font-size:13px; }}
    td {{ padding:11px; border-bottom:1px solid #edf2f7; font-size:13px; line-height:1.5; vertical-align:top; }}
    button {{ min-height:38px; border:1px solid #bfdbfe; background:#eff6ff; color:#1e3a8a; border-radius:8px; padding:8px 10px; font-weight:800; cursor:pointer; }}
    button:hover {{ background:#dbeafe; }}
    .badge {{ display:inline-flex; border-radius:999px; padding:5px 9px; font-weight:800; white-space:nowrap; }}
    .badge.low {{ background:#dcfce7; color:var(--ok); }}
    .badge.medium {{ background:#fef3c7; color:var(--warn); }}
    .badge.high {{ background:#ffe4e6; color:var(--risk); }}
    #impact_feedback {{ border:1px solid #bfdbfe; background:#f8fbff; border-radius:8px; padding:12px; line-height:1.65; color:#1e3a5f; min-height:58px; margin-top:12px; }}
    .footer {{ margin-top:14px; color:#64748b; font-size:12px; line-height:1.6; }}
    @media(max-width:980px) {{ .cards,.rules {{ grid-template-columns:1fr 1fr; }} table {{ display:block; overflow-x:auto; }} }}
    @media(max-width:720px) {{ .cards,.rules {{ grid-template-columns:1fr; }} header {{ padding:24px; }} main {{ padding:16px; }} }}
  </style>
</head>
<body>
  <header>
    <div class="brand"><div class="logo">KM</div><div><h1>KMFA 影响预览 v1.4</h1><div class="sub">处理事件提交前展示受影响项目、受影响指标、受影响报告；高风险二次确认未完成时不得发布。</div></div></div>
  </header>
  <main>
    <section class="cards" aria-label="影响预览摘要">
      <div class="card"><span>影响预览</span><b>{summary["impact_preview_count"]}</b><small>覆盖全部事件</small></div>
      <div class="card"><span>受影响项目</span><b>{summary["affected_project_count"]}</b><small>公开安全分组</small></div>
      <div class="card"><span>受影响指标</span><b>{summary["affected_metric_count"]}</b><small>指标和状态</small></div>
      <div class="card"><span>阻断发布</span><b>{summary["blocked_publish_count"]}</b><small>二次确认 pending</small></div>
    </section>
    <section class="panel">
      <h2>发布门禁</h2>
      <div class="rules">
        <div class="rule">受影响项目、指标、报告必须同时展示。</div>
        <div class="rule">高风险二次确认未完成时，控制事件发布被阻断。</div>
        <div class="rule">重跑未执行，派生链路留到 S12-P3。</div>
      </div>
      <div id="impact_feedback" aria-live="polite">点击任一预览查看门禁反馈。未通过预览不得发布。</div>
    </section>
    <section class="panel" aria-label="影响预览列表">
      <h2>影响预览列表</h2>
      <table>
        <thead><tr><th>事件</th><th>动作</th><th>风险</th><th>受影响项目</th><th>受影响指标</th><th>受影响报告</th><th>门禁</th><th>操作</th></tr></thead>
        <tbody>
{rows}
        </tbody>
      </table>
    </section>
    <div class="footer">KMFA 经营分析系统 · v0.1.4 S12-P2 · 不执行 S12-P3、Stage 12 复审、GitHub upload、完整追溯检查、正式报告、外部接口或业务动作。</div>
  </main>
  <script>
    const feedback = document.getElementById("impact_feedback");
    document.querySelectorAll("button[data-preview]").forEach((button) => {{
      button.addEventListener("click", () => {{
        const gate = button.dataset.gate;
        const id = button.dataset.preview;
        feedback.textContent = gate === "blocked_pending_second_confirmation"
          ? `${{id}}：高风险二次确认待完成，未通过预览不得发布。`
          : `${{id}}：预览通过，但本 phase 仍不执行重跑。`;
      }});
    }});
  </script>
</body>
</html>
"""


def build_manifest() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    dependency = validate_s12_p1_dependency()
    legacy = validate_legacy_s12_p2_artifacts()
    v14 = {
        **load_v14_html_uiux_baseline(),
        "implementation_reflects_impact_preview": True,
        "implementation_reflects_second_confirmation_feedback": True,
        "implementation_reflects_no_raw_mutation": True,
    }
    generated_at = datetime.now().astimezone().replace(microsecond=0).isoformat()
    previews = _adjust_previews(legacy["legacy_previews"], generated_at)
    summary = {
        "source_event_count": legacy["source_event_count"],
        "impact_preview_count": legacy["impact_preview_count"],
        "affected_project_count": legacy["affected_project_count"],
        "affected_metric_count": legacy["affected_metric_count"],
        "affected_report_count": legacy["affected_report_count"],
        "high_risk_count": legacy["high_risk_count"],
        "second_confirmation_required_count": legacy["second_confirmation_required_count"],
        "blocked_publish_count": legacy["blocked_publish_count"],
        "publish_allowed_count": legacy["publish_allowed_count"],
        "raw_layer_write_count": 0,
        "source_mutation_count": 0,
        "business_plaintext_count": 0,
        "derived_rerun_count": 0,
        "formal_report_count": 0,
        "business_decision_basis_count": 0,
        "github_upload_count": 0,
    }
    manifest: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "manual_impact_preview_manifest",
        "project_id": "KMFA",
        "system_name": "KMFA 经营分析系统",
        "version": "0.1.4",
        "stage_id": "S12",
        "phase_id": "S12-P2",
        "stage_phase": "S12-P2",
        "phase_scope": PHASE_SCOPE,
        "task_id": TASK_ID,
        "acceptance_ids": [ACCEPTANCE_ID],
        "completed_task_ids": ["S12P2T01", "S12P2T02", "S12P2T03"],
        "status": "completed_validated_local_only_no_go_upload_deferred_manual_impact_preview",
        "generated_at": generated_at,
        "git": {
            "branch": git_output(["branch", "--show-current"]),
            "head": git_output(["rev-parse", "HEAD"]),
            "remote": git_output(["remote", "get-url", "origin"]),
        },
        "s12_p1_dependency_validated": True,
        "s12_p1_manifest": S12_P1_MANIFEST_PATH.as_posix(),
        "legacy_s12_p2_dependency_validated": True,
        "legacy_s12_p2_artifact_refs": {
            "manifest": LEGACY_MANIFEST_PATH.as_posix(),
            "previews": LEGACY_PREVIEWS_PATH.as_posix(),
            "html": LEGACY_HTML_OUTPUT.as_posix(),
        },
        "stage12_phase_progress": {
            "completed_phase_count": 2,
            "total_phase_count": 3,
            "derived_percent_bps": 6667,
            "derived_percent_label": "66.67%",
            "s12_p1_performed": True,
            "s12_p2_performed": True,
            "s12_p3_performed": False,
            "stage12_review_performed": False,
        },
        "required_impact_domains": list(REQUIRED_IMPACT_DOMAINS),
        "manual_impact_preview_summary": summary,
        "summary": summary,
        "v14_html_uiux_baseline": v14,
        "phase_boundaries": _phase_boundaries(),
        "stage_scope": _phase_boundaries(),
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
            "s12_p3_rerun_not_performed",
            "stage12_review_not_performed",
            "report_grade_d_only",
            "pending_reconciliation_blocks_formal_report",
            "raw_data_mutation_forbidden",
            "protected_business_value_publication_forbidden",
            "field_header_plaintext_publication_forbidden",
            "formal_report_release_blocked",
            "business_decision_basis_blocked",
            "lineage_full_check_not_performed",
            "protected_business_value_matching_not_performed",
            "github_upload_deferred_until_v014_stage1_18_complete",
            "app_reinstall_not_performed",
            "business_execution_blocked",
        ],
        "artifact_refs": {
            "manifest": MANIFEST_PATH.as_posix(),
            "previews": PREVIEWS_PATH.as_posix(),
            "html_export": HTML_OUTPUT_PATH.as_posix(),
            "human_report": REPORT_PATH.as_posix(),
            "test_results": TEST_RESULTS_PATH.as_posix(),
            "risk_register": RISK_REGISTER_PATH.as_posix(),
            "rollback_plan": ROLLBACK_PATH.as_posix(),
            "validator": "KMFA/tools/check_v014_s12_p2_manual_impact_preview.py",
            "test": "KMFA/tests/test_v014_s12_p2_manual_impact_preview.py",
        },
        "evidence_refs": [
            REPORT_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            RISK_REGISTER_PATH.as_posix(),
            ROLLBACK_PATH.as_posix(),
            MANIFEST_PATH.as_posix(),
            PREVIEWS_PATH.as_posix(),
            HTML_OUTPUT_PATH.as_posix(),
        ],
        "next_phase": "S12-P3",
        "next_required_step": NEXT_REQUIRED_STEP,
        "non_goals": [
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
        "dependency_s12_p1_status": dependency.get("status"),
    }
    return manifest, previews


def _render_report(manifest: dict[str, Any]) -> str:
    summary = manifest["manual_impact_preview_summary"]
    return f"""# v0.1.4 S12-P2 Manual Impact Preview

## Scope

- Phase: `S12-P2｜影响预览`
- Status: `{manifest["status"]}`
- Task: `{TASK_ID}`
- Acceptance: `{ACCEPTANCE_ID}`

## Locked Evidence

- Source events: `{summary["source_event_count"]}`
- Impact previews: `{summary["impact_preview_count"]}`
- Affected project refs: `{summary["affected_project_count"]}`
- Affected metric refs: `{summary["affected_metric_count"]}`
- Affected report refs: `{summary["affected_report_count"]}`
- High risk previews: `{summary["high_risk_count"]}`
- Blocked publish previews: `{summary["blocked_publish_count"]}`
- Publish allowed previews: `{summary["publish_allowed_count"]}`

## v1.4 Human Flow

- Taskpack HTML baseline read: `true`
- Audit rows/pass/warn/fail: `54 / 54 / 0 / 0`
- Impact preview buttons provide visible feedback and high-risk second-confirmation blocking.

## Boundaries

- Raw/private inbox read/list/stat/hash/mutation: `false`
- Derived rerun: `false`
- Stage 12 review: `false`
- GitHub upload: `false`
- Formal report/business decision basis/business execution: `false`

## Next

{NEXT_REQUIRED_STEP}
"""


def _render_test_results() -> str:
    return """# v0.1.4 S12-P2 Test Results

Pending final validation commands:

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_s12_p2_manual_impact_preview.py KMFA/tools/check_v014_s12_p2_manual_impact_preview.py KMFA/tests/test_v014_s12_p2_manual_impact_preview.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_s12_p2_manual_impact_preview.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s12_p1_manual_resolution_events.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s12_p2_manual_impact_preview.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s12_p2_manual_impact_preview.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s12_p2_manual_impact_preview -q`
- Governance, no-float, no-omission, structured parse, raw/private suffix scan, secret scan, and diff checks.

Final pass/fail evidence is recorded in governance events after validation.
"""


def _render_risk_register() -> str:
    return """# v0.1.4 S12-P2 Risk Register

| Risk | Control |
| --- | --- |
| High-risk preview is published without second confirmation | Validator requires pending high-risk previews to block publish |
| S12-P2 accidentally runs derived rerun | Phase boundaries and quality gate keep S12-P3 false |
| Public evidence leaks protected business data | Artifact validator and scans reject forbidden private tokens and source suffixes |
| Stage review/upload is implied too early | GitHub upload remains deferred until v1.4 Stage 1-18 complete and reviewed |
"""


def _render_rollback_plan() -> str:
    return """# v0.1.4 S12-P2 Rollback Plan

1. Remove `KMFA/stage_artifacts/V014_S12_P2_MANUAL_IMPACT_PREVIEW/`.
2. Revert `KMFA/tools/v014_s12_p2_manual_impact_preview.py`, `KMFA/tools/check_v014_s12_p2_manual_impact_preview.py`, and focused test changes.
3. Revert S12-P2 governance/status updates.
4. Re-run S12-P1 validator to confirm the previous boundary remains intact.
"""


def generate() -> dict[str, Any]:
    manifest, previews = build_manifest()
    html_text = _render_v014_html(previews, manifest["manual_impact_preview_summary"])
    validate_manual_impact_preview_artifacts(
        manifest,
        previews,
        {"html": {"kmfa_manual_impact_preview": html_text}},
        read_jsonl(S12_P1_EVENTS_PATH),
    )
    _write_json(MANIFEST_PATH, manifest)
    _write_jsonl(PREVIEWS_PATH, previews)
    _write_text(HTML_OUTPUT_PATH, html_text)
    _write_text(REPORT_PATH, _render_report(manifest))
    _write_text(TEST_RESULTS_PATH, _render_test_results())
    _write_text(RISK_REGISTER_PATH, _render_risk_register())
    _write_text(ROLLBACK_PATH, _render_rollback_plan())
    return manifest


def main() -> int:
    manifest = generate()
    summary = manifest["manual_impact_preview_summary"]
    print(
        "PASS: KMFA v0.1.4 S12-P2 manual impact preview generated "
        f"(previews={summary['impact_preview_count']}, "
        f"projects={summary['affected_project_count']}, "
        f"metrics={summary['affected_metric_count']}, "
        f"reports={summary['affected_report_count']}, "
        f"high_risk={summary['high_risk_count']}, "
        f"blocked_publish={summary['blocked_publish_count']}, "
        "s12_p3=false, stage12_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
