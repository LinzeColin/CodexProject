#!/usr/bin/env python3
"""Build KMFA S12-P2 public-safe manual impact preview artifacts."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.manual_resolution_events import (
    DEFAULT_OUTPUT_EVENTS as DEFAULT_SOURCE_EVENTS,
    DEFAULT_OUTPUT_MANIFEST as DEFAULT_SOURCE_MANIFEST,
    read_json,
    read_jsonl,
    write_json,
    write_jsonl,
)


ROOT = Path(__file__).resolve().parents[1]

DEFAULT_OUTPUT_MANIFEST = ROOT / "metadata" / "approvals" / "manual_impact_preview_manifest.json"
DEFAULT_OUTPUT_PREVIEWS = ROOT / "metadata" / "approvals" / "manual_impact_previews.jsonl"
DEFAULT_OUTPUT_STAGE_MANIFEST = (
    ROOT / "stage_artifacts" / "S12_P2_manual_impact_preview" / "machine" / "s12_p2_manifest.json"
)
DEFAULT_HTML_OUTPUT = (
    ROOT
    / "stage_artifacts"
    / "S12_P2_manual_impact_preview"
    / "exports"
    / "html"
    / "kmfa_manual_impact_preview.html"
)

REQUIRED_IMPACT_DOMAINS = ("affected_projects", "affected_metrics", "affected_reports")
REQUIRED_PREVIEW_FIELDS = (
    "preview_id",
    "schema_version",
    "record_type",
    "stage_phase",
    "source_event_id",
    "source_event_type",
    "source_manual_action_kind",
    "preview_version",
    "preview_status",
    "preview_passed",
    "risk_level",
    "second_confirmation_required",
    "second_confirmation_status",
    "control_event_publish_allowed",
    "release_gate",
    "affected_projects",
    "affected_metrics",
    "affected_reports",
    "impact_reason",
    "raw_layer_write_allowed",
    "derived_rerun_executed",
    "formal_report_generated",
    "evidence_refs",
)
RISK_LEVELS = {"low", "medium", "high"}
PREVIEW_VERSION = "IMPACT-PREVIEW-KMFA-S12P2-001"
HTML_VERSION = "UI-KMFA-S12P2-IMPACT-PREVIEW-001"
PUBLIC_SAFETY_VERSION = "SAFE-KMFA-S12P2-PUBLIC-001"
PREVIEW_ID_RE = re.compile(r"^IMPREV-S12P2-[0-9]{3}$")

FORBIDDEN_PUBLIC_KEYS = {
    "amount_cents",
    "amount_yuan",
    "raw_value",
    "normalized_value",
    "original_value",
    "plaintext_value",
    "source_header_text",
    "raw_file_bytes",
    "original_filename",
    "private_csv",
    "bank_account_number",
    "account_number",
    "identity_document_number",
    "project_name_plaintext",
    "customer_name_plaintext",
    "counterparty_plaintext",
    "company_entity_plaintext",
    "password",
    "api_key",
    "private_key",
}
FORBIDDEN_PUBLIC_TEXT = (
    "private_ref://",
    "raw_value",
    "normalized_value",
    "plaintext_value",
    "source_header_text",
    "original_filename",
    "bank_account_number",
    "identity_document_number",
    "password",
    "api_key",
    "private_key",
)
FORBIDDEN_PUBLIC_SUFFIXES = (".zip", ".xls", ".xlsx", ".pdf", ".sqlite", ".db", ".parquet")


class ManualImpactPreviewError(ValueError):
    """Raised when S12-P2 manual impact preview artifacts are invalid."""


def _sha256_json(payload: Any) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _public_repo_safety() -> dict[str, bool]:
    return {
        "raw_business_values_committed": False,
        "normalized_business_values_committed": False,
        "field_plaintext_committed": False,
        "raw_file_committed": False,
        "private_tabular_files_committed": False,
        "excel_workbook_committed": False,
        "pdf_file_committed": False,
        "credential_secret_committed": False,
        "real_account_number_committed": False,
        "raw_layer_write_allowed": False,
    }


def _quality_gate() -> dict[str, Any]:
    return {
        "impact_preview_generation_allowed": True,
        "impact_preview_required_before_publish": True,
        "high_risk_second_confirmation_required": True,
        "unpassed_preview_publish_allowed": False,
        "raw_layer_write_allowed": False,
        "raw_source_mutation_allowed": False,
        "source_layer_write_allowed": False,
        "business_plaintext_commit_allowed": False,
        "derived_rerun_allowed": False,
        "derived_rerun_executed": False,
        "formal_report_allowed": False,
        "formal_report_generated": False,
        "business_decision_basis_allowed": False,
        "github_upload_allowed": False,
        "phase_completion_upload_allowed": False,
    }


def _stage_scope() -> dict[str, bool]:
    return {
        "s12_p1_manual_resolution_event_dependency_included": True,
        "s12_p2_impact_preview_scope_included": True,
        "s12_p3_rerun_mechanism_scope_included": False,
        "stage12_review_scope_included": False,
        "github_upload_scope_included": False,
        "lineage_full_check_scope_included": False,
        "formal_report_runtime_scope_included": False,
        "external_connector_scope_included": False,
        "difference_closure_scope_included": False,
    }


def _preview(
    *,
    index: int,
    source_event: dict[str, Any],
    risk_level: str,
    affected_projects: list[str],
    affected_metrics: list[str],
    affected_reports: list[str],
    impact_reason: str,
    generated_at: str,
) -> dict[str, Any]:
    high_risk = risk_level == "high"
    preview_passed = not high_risk
    row: dict[str, Any] = {
        "preview_id": f"IMPREV-S12P2-{index:03d}",
        "schema_version": "kmfa.manual_impact_preview.v1",
        "record_type": "manual_impact_preview",
        "project_id": "KMFA",
        "system_name": "KMFA 经营分析系统",
        "stage_phase": "S12-P2",
        "source_event_id": source_event["event_id"],
        "source_event_type": source_event["event_type"],
        "source_manual_action_kind": source_event["manual_action_kind"],
        "source_event_status": source_event["status"],
        "source_event_version": source_event["event_version"],
        "preview_version": f"{PREVIEW_VERSION}.{index:03d}",
        "preview_time": generated_at,
        "preview_status": "blocked_pending_second_confirmation" if high_risk else "passed_public_safe_preview",
        "preview_passed": preview_passed,
        "risk_level": risk_level,
        "second_confirmation_required": high_risk,
        "second_confirmation_status": "pending" if high_risk else "not_required",
        "control_event_publish_allowed": preview_passed,
        "release_gate": "blocked_pending_second_confirmation" if high_risk else "preview_passed_publish_allowed",
        "affected_projects": affected_projects,
        "affected_metrics": affected_metrics,
        "affected_reports": affected_reports,
        "impact_reason": impact_reason,
        "impact_preview_display_required": True,
        "raw_layer_write_allowed": False,
        "raw_source_mutation_allowed": False,
        "source_layer_write_allowed": False,
        "business_plaintext_committed": False,
        "forbidden_plaintext": False,
        "derived_cache_invalidated": False,
        "derived_rerun_executed": False,
        "formal_report_generated": False,
        "github_upload_allowed": False,
        "stage12_review_allowed": False,
        "evidence_refs": [
            "KMFA/metadata/approvals/manual_resolution_events.jsonl",
            "KMFA/taskpack/v1_2/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_2.md:S12-P2",
        ],
        "public_repo_safety": _public_repo_safety(),
        "content_hash": "",
    }
    row["content_hash"] = _sha256_json({key: value for key, value in row.items() if key != "content_hash"})
    return row


def _impact_profile(source_event: dict[str, Any]) -> tuple[str, list[str], list[str], list[str], str]:
    action_kind = source_event["manual_action_kind"]
    event_action = source_event.get("event_action", "")
    if action_kind == "field_mapping":
        return (
            "medium",
            ["project_group_public_a0_locked", "project_group_public_wps_support"],
            ["metric_project_cost_category", "metric_source_quality_status"],
            ["report_project_cost_preview", "report_source_check_board"],
            "字段映射调整会影响成本分类、来源状态和项目成本预览展示。",
        )
    if action_kind == "project_matching":
        return (
            "high",
            ["project_group_public_identity_queue", "project_group_public_cost_page", "project_group_public_report"],
            ["metric_project_match_score", "metric_project_margin", "metric_collection_status"],
            ["report_project_cost_preview", "report_business_overview_preview", "report_pending_actions"],
            "项目匹配会改变项目分组和报告汇总口径，发布前需要二次确认。",
        )
    if action_kind == "difference_handling" and event_action == "reverse_approved_event":
        return (
            "high",
            ["project_group_public_scope_reconciliation", "project_group_public_audit_log"],
            ["metric_difference_status", "metric_report_grade", "metric_manual_event_audit"],
            ["report_project_cost_preview", "report_management_summary_preview"],
            "反向事件会影响已批准差异处理状态和审计链，发布前需要二次确认。",
        )
    if action_kind == "difference_handling":
        return (
            "high",
            ["project_group_public_scope_reconciliation", "project_group_public_cost_page"],
            ["metric_difference_status", "metric_report_grade", "metric_pending_reconciliation_count"],
            ["report_project_cost_preview", "report_business_overview_preview"],
            "差异处理会影响报告等级、待处理事项和管理摘要口径，发布前需要二次确认。",
        )
    return (
        "low",
        ["project_group_public_manual_workbench"],
        ["metric_review_note_count", "metric_audit_log_status"],
        ["report_pending_actions"],
        "备注只影响人工处理工作台和待处理事项提示。",
    )


def _build_previews(source_events: list[dict[str, Any]], generated_at: str) -> list[dict[str, Any]]:
    previews: list[dict[str, Any]] = []
    for index, source_event in enumerate(source_events, start=1):
        risk_level, projects, metrics, reports, reason = _impact_profile(source_event)
        previews.append(
            _preview(
                index=index,
                source_event=source_event,
                risk_level=risk_level,
                affected_projects=projects,
                affected_metrics=metrics,
                affected_reports=reports,
                impact_reason=reason,
                generated_at=generated_at,
            )
        )
    return previews


def _render_html(previews: list[dict[str, Any]], manifest: dict[str, Any]) -> str:
    summary = manifest["summary"]
    cards = (
        f'<div class="card"><span>影响预览</span><b>{summary["impact_preview_count"]}</b><small>提交前展示</small></div>'
        f'<div class="card"><span>受影响项目</span><b>{summary["affected_project_count"]}</b><small>公开安全分组</small></div>'
        f'<div class="card"><span>受影响指标</span><b>{summary["affected_metric_count"]}</b><small>指标和状态</small></div>'
        f'<div class="card"><span>高风险二次确认</span><b>{summary["high_risk_count"]}</b><small>未确认不发布</small></div>'
    )
    rows = "\n".join(
        f"""          <tr>
            <td>{html.escape(preview["source_event_id"])}</td>
            <td>{html.escape(_action_label(preview["source_manual_action_kind"]))}</td>
            <td><span class="badge {html.escape(preview["risk_level"])}">{html.escape(_risk_label(preview["risk_level"]))}</span></td>
            <td>{html.escape("、".join(preview["affected_projects"]))}</td>
            <td>{html.escape("、".join(preview["affected_metrics"]))}</td>
            <td>{html.escape("、".join(preview["affected_reports"]))}</td>
            <td>{html.escape(_gate_label(preview["release_gate"]))}</td>
          </tr>"""
        for preview in previews
    )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>KMFA 影响预览</title>
  <style>
    :root {{
      --navy:#0b2447;
      --blue:#1d4ed8;
      --sky:#eaf3ff;
      --line:#d8e4f5;
      --text:#152033;
      --muted:#64748b;
      --bg:#f6f9fe;
      --card:#ffffff;
      --ok:#166534;
      --warn:#92400e;
      --risk:#9f1239;
    }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:var(--bg); color:var(--text); font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",Arial,sans-serif; }}
    .header {{ background:linear-gradient(135deg,var(--navy),#123a70 55%,#2563eb); color:#fff; padding:30px 40px; }}
    .brand {{ display:flex; align-items:center; gap:14px; }}
    .logo {{ width:52px; height:52px; border:1px solid rgba(255,255,255,.45); border-radius:8px; display:flex; align-items:center; justify-content:center; font-weight:800; background:rgba(255,255,255,.10); }}
    h1 {{ margin:0; font-size:28px; letter-spacing:0; }}
    .sub {{ margin-top:8px; color:#d6e7ff; line-height:1.65; }}
    .wrap {{ max-width:1260px; margin:0 auto; padding:24px; }}
    .cards {{ display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin-bottom:18px; }}
    .card {{ background:#fff; border:1px solid var(--line); border-radius:8px; padding:16px; box-shadow:0 12px 28px rgba(17,45,88,.06); }}
    .card span {{ display:block; color:var(--muted); font-size:13px; }}
    .card b {{ display:block; color:#0b2b59; font-size:26px; margin:6px 0; }}
    .card small {{ color:#475569; }}
    .panel {{ background:#fff; border:1px solid var(--line); border-radius:8px; padding:16px; margin-bottom:14px; }}
    .panel h2 {{ margin:0 0 10px; color:#0b2b59; font-size:18px; }}
    .note {{ color:#475569; line-height:1.7; max-width:900px; }}
    .rules {{ display:grid; grid-template-columns:repeat(3,1fr); gap:10px; }}
    .rule {{ border:1px solid #bfdbfe; background:#f8fbff; color:#1e3a5f; border-radius:8px; padding:12px; line-height:1.6; }}
    table {{ width:100%; border-collapse:separate; border-spacing:0; }}
    th {{ background:#0f2f5f; color:#fff; text-align:left; font-size:13px; padding:12px; }}
    td {{ padding:12px; font-size:13px; line-height:1.55; border-bottom:1px solid #edf2f7; vertical-align:top; }}
    .badge {{ display:inline-flex; border-radius:999px; padding:5px 9px; font-weight:800; white-space:nowrap; }}
    .badge.low {{ background:#dcfce7; color:var(--ok); }}
    .badge.medium {{ background:#fef3c7; color:var(--warn); }}
    .badge.high {{ background:#ffe4e6; color:var(--risk); }}
    .footer {{ margin-top:14px; color:#64748b; font-size:12px; line-height:1.6; }}
    @media(max-width:980px) {{ .cards,.rules {{ grid-template-columns:1fr 1fr; }} }}
    @media(max-width:720px) {{ .cards,.rules {{ grid-template-columns:1fr; }} .wrap {{ padding:16px; }} .header {{ padding:24px; }} table {{ display:block; overflow-x:auto; }} }}
  </style>
</head>
<body>
  <header class="header">
    <div class="brand"><div class="logo">KM</div><div><h1>KMFA 影响预览</h1><div class="sub">处理事件提交前展示受影响项目、指标和报告；未通过预览不得发布。</div></div></div>
  </header>
  <main class="wrap">
    <section class="cards" aria-label="影响预览摘要">{cards}</section>
    <section class="panel">
      <h2>发布门禁</h2>
      <p class="note">S12-P2 只生成影响预览，不失效派生缓存，不重跑字段映射、事实层、指标或报告引用。高风险处理需要二次确认，未通过预览不得发布，正式报告仍为阻断状态。</p>
      <div class="rules">
        <div class="rule">受影响项目、受影响指标、受影响报告必须同时展示。</div>
        <div class="rule">高风险二次确认未完成时，控制事件发布被阻断。</div>
        <div class="rule">重跑未执行，派生链路留到 S12-P3。</div>
      </div>
    </section>
    <section class="panel" aria-label="影响预览列表">
      <h2>影响预览列表</h2>
      <table>
        <thead><tr><th>事件</th><th>动作</th><th>风险</th><th>受影响项目</th><th>受影响指标</th><th>受影响报告</th><th>门禁</th></tr></thead>
        <tbody>
{rows}
        </tbody>
      </table>
    </section>
    <div class="footer">KMFA 经营分析系统 · S12-P2 影响预览 · 本页面不执行重跑机制、Stage 12 复审、上传、完整追溯检查、正式报告或外部接口。</div>
  </main>
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


def _risk_label(risk_level: str) -> str:
    return {"low": "低风险", "medium": "中风险", "high": "高风险"}[risk_level]


def _gate_label(release_gate: str) -> str:
    return {
        "blocked_pending_second_confirmation": "等待二次确认",
        "preview_passed_publish_allowed": "预览通过",
    }[release_gate]


def build_default_manual_impact_preview_artifacts(
    *,
    source_event_manifest: dict[str, Any],
    source_events: list[dict[str, Any]],
    generated_at: str = "2026-07-01T13:00:00+10:00",
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, dict[str, str]]]:
    if source_event_manifest.get("stage_phase") != "S12-P1":
        raise ManualImpactPreviewError("S12-P2 impact preview requires S12-P1 manual resolution events")
    previews = _build_previews(source_events, generated_at)
    project_refs = sorted({item for preview in previews for item in preview["affected_projects"]})
    metric_refs = sorted({item for preview in previews for item in preview["affected_metrics"]})
    report_refs = sorted({item for preview in previews for item in preview["affected_reports"]})
    high_risk = [preview for preview in previews if preview["risk_level"] == "high"]
    blocked = [preview for preview in previews if not preview["control_event_publish_allowed"]]
    manifest: dict[str, Any] = {
        "schema_version": "kmfa.manual_impact_preview_manifest.v1",
        "record_type": "manual_impact_preview_manifest",
        "project_id": "KMFA",
        "system_name": "KMFA 经营分析系统",
        "stage_phase": "S12-P2",
        "runtime_status": "public_safe_manual_impact_preview_generated_local_only",
        "impact_preview_version": PREVIEW_VERSION,
        "html_version": HTML_VERSION,
        "public_safety_version": PUBLIC_SAFETY_VERSION,
        "generated_at": generated_at,
        "required_impact_domains": list(REQUIRED_IMPACT_DOMAINS),
        "required_preview_fields": list(REQUIRED_PREVIEW_FIELDS),
        "source_taskpack_refs": {
            "roadmap_s12_p2": "KMFA/taskpack/v1_2/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_2.md:S12-P2",
            "resolution_workbench_sample": (
                "KMFA/taskpack/v1_2/20_HTML_UIUX_报告预览/01_核心HTML验收样板/"
                "KMFA_Resolution_Workbench_v0_4.html"
            ),
            "upstream_manual_resolution_events": "KMFA/metadata/approvals/manual_resolution_events.jsonl",
            "upstream_manual_resolution_manifest": "KMFA/metadata/approvals/manual_resolution_event_manifest.json",
        },
        "quality_gate": _quality_gate(),
        "stage_scope": _stage_scope(),
        "public_repo_safety": _public_repo_safety(),
        "artifact_refs": {
            "manual_impact_preview_manifest": "KMFA/metadata/approvals/manual_impact_preview_manifest.json",
            "manual_impact_previews": "KMFA/metadata/approvals/manual_impact_previews.jsonl",
            "html_export": "KMFA/stage_artifacts/S12_P2_manual_impact_preview/exports/html/kmfa_manual_impact_preview.html",
            "validator": "KMFA/tools/check_s12_p2_manual_impact_preview.py",
            "completion_record": "KMFA/stage_artifacts/S12_P2_manual_impact_preview/human/s12_p2_completion_record.md",
            "test_results": "KMFA/stage_artifacts/S12_P2_manual_impact_preview/human/test_results.md",
            "stage_manifest": "KMFA/stage_artifacts/S12_P2_manual_impact_preview/machine/s12_p2_manifest.json",
        },
        "summary": {
            "source_event_count": len(source_events),
            "impact_preview_count": len(previews),
            "affected_project_count": len(project_refs),
            "affected_metric_count": len(metric_refs),
            "affected_report_count": len(report_refs),
            "high_risk_count": len(high_risk),
            "second_confirmation_required_count": len(high_risk),
            "blocked_publish_count": len(blocked),
            "raw_layer_write_count": 0,
            "derived_rerun_count": 0,
            "formal_report_count": 0,
            "github_upload_count": 0,
        },
        "limitations": [
            "S12-P2 只生成处理事件提交前的影响预览，不执行派生链路重跑。",
            "高风险处理需要二次确认，二次确认未完成时不得发布控制事件。",
            "未通过影响预览不得发布；正式报告、Stage 12 review 和 GitHub upload 仍阻断。",
            "公开仓库只保存 public-safe impact metadata、hash、状态、证据索引和 HTML 样张。",
        ],
        "content_hash": "",
    }
    manifest["content_hash"] = _sha256_json({key: value for key, value in manifest.items() if key != "content_hash"})
    render_outputs = {"html": {"kmfa_manual_impact_preview": _render_html(previews, manifest)}}
    return manifest, previews, render_outputs


def _assert_public_safe(payload: Any) -> None:
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key in FORBIDDEN_PUBLIC_KEYS:
                raise ManualImpactPreviewError(f"forbidden public key found: {key}")
            _assert_public_safe(value)
        return
    if isinstance(payload, list):
        for value in payload:
            _assert_public_safe(value)
        return
    if isinstance(payload, str):
        lowered = payload.lower()
        for forbidden in FORBIDDEN_PUBLIC_TEXT:
            if forbidden in lowered:
                raise ManualImpactPreviewError(f"forbidden private token found: {forbidden}")
        for suffix in FORBIDDEN_PUBLIC_SUFFIXES:
            if suffix in lowered:
                raise ManualImpactPreviewError(f"forbidden public artifact suffix found: {suffix}")


def validate_manual_impact_preview_artifacts(
    manifest: dict[str, Any],
    previews: list[dict[str, Any]],
    render_outputs: dict[str, dict[str, str]],
    source_events: list[dict[str, Any]],
) -> None:
    if manifest.get("stage_phase") != "S12-P2":
        raise ManualImpactPreviewError("manifest stage_phase must be S12-P2")
    if tuple(manifest.get("required_impact_domains", [])) != REQUIRED_IMPACT_DOMAINS:
        raise ManualImpactPreviewError("required impact domains mismatch")
    source_event_ids = {event.get("event_id") for event in source_events}
    preview_event_ids = {preview.get("source_event_id") for preview in previews}
    if preview_event_ids != source_event_ids:
        raise ManualImpactPreviewError("impact previews must cover every S12-P1 source event exactly once")
    if manifest.get("quality_gate", {}).get("derived_rerun_allowed") is not False:
        raise ManualImpactPreviewError("S12-P2 must not allow derived rerun")
    if manifest.get("stage_scope", {}).get("s12_p3_rerun_mechanism_scope_included") is not False:
        raise ManualImpactPreviewError("S12-P2 must not include S12-P3 rerun scope")
    if manifest.get("stage_scope", {}).get("stage12_review_scope_included") is not False:
        raise ManualImpactPreviewError("S12-P2 must not include Stage 12 review")
    if manifest.get("stage_scope", {}).get("github_upload_scope_included") is not False:
        raise ManualImpactPreviewError("S12-P2 must not include GitHub upload")

    project_refs = set()
    metric_refs = set()
    report_refs = set()
    high_risk_count = 0
    blocked_publish_count = 0
    for preview in previews:
        for required_field in REQUIRED_PREVIEW_FIELDS:
            if required_field not in preview:
                raise ManualImpactPreviewError(f"missing preview field: {required_field}")
        if not PREVIEW_ID_RE.match(str(preview["preview_id"])):
            raise ManualImpactPreviewError(f"invalid preview id: {preview['preview_id']}")
        if preview["risk_level"] not in RISK_LEVELS:
            raise ManualImpactPreviewError(f"invalid risk level: {preview['risk_level']}")
        for field in REQUIRED_IMPACT_DOMAINS:
            value = preview[field]
            if not isinstance(value, list) or not value:
                raise ManualImpactPreviewError(f"{preview['preview_id']} missing {field}")
        if preview["raw_layer_write_allowed"] is not False:
            raise ManualImpactPreviewError("impact preview must not write raw layer")
        if preview.get("derived_rerun_executed") is not False:
            raise ManualImpactPreviewError("S12-P2 must not execute derived rerun")
        if preview.get("formal_report_generated") is not False:
            raise ManualImpactPreviewError("S12-P2 must not generate formal report")
        if not preview["preview_passed"] and preview["control_event_publish_allowed"]:
            raise ManualImpactPreviewError("unpassed impact preview cannot publish")
        if preview["risk_level"] == "high":
            high_risk_count += 1
            if preview["second_confirmation_required"] is not True:
                raise ManualImpactPreviewError("high risk preview must require second confirmation")
            if preview["second_confirmation_status"] != "confirmed" and preview["control_event_publish_allowed"]:
                raise ManualImpactPreviewError("high risk preview cannot publish without confirmed second confirmation")
            if preview["second_confirmation_status"] != "confirmed" and preview["release_gate"] != "blocked_pending_second_confirmation":
                raise ManualImpactPreviewError("high risk pending preview must have blocked release gate")
        if not preview["control_event_publish_allowed"]:
            blocked_publish_count += 1
        project_refs.update(preview["affected_projects"])
        metric_refs.update(preview["affected_metrics"])
        report_refs.update(preview["affected_reports"])

    summary = manifest.get("summary", {})
    expected_summary = {
        "source_event_count": len(source_events),
        "impact_preview_count": len(previews),
        "affected_project_count": len(project_refs),
        "affected_metric_count": len(metric_refs),
        "affected_report_count": len(report_refs),
        "high_risk_count": high_risk_count,
        "second_confirmation_required_count": high_risk_count,
        "blocked_publish_count": blocked_publish_count,
        "raw_layer_write_count": 0,
        "derived_rerun_count": 0,
        "formal_report_count": 0,
        "github_upload_count": 0,
    }
    for key, expected in expected_summary.items():
        if summary.get(key) != expected:
            raise ManualImpactPreviewError(f"summary mismatch for {key}: {summary.get(key)} != {expected}")

    html_text = render_outputs.get("html", {}).get("kmfa_manual_impact_preview", "")
    for required_text in (
        "KMFA 影响预览",
        "受影响项目",
        "受影响指标",
        "受影响报告",
        "高风险二次确认",
        "未通过预览不得发布",
        "重跑未执行",
    ):
        if required_text not in html_text:
            raise ManualImpactPreviewError(f"HTML missing required text: {required_text}")
    _assert_public_safe(manifest)
    _assert_public_safe(previews)
    _assert_public_safe(render_outputs)


def write_manual_impact_preview_artifacts(
    *,
    manifest: dict[str, Any],
    previews: list[dict[str, Any]],
    render_outputs: dict[str, dict[str, str]],
    output_manifest: Path = DEFAULT_OUTPUT_MANIFEST,
    output_previews: Path = DEFAULT_OUTPUT_PREVIEWS,
    output_stage_manifest: Path = DEFAULT_OUTPUT_STAGE_MANIFEST,
    output_html: Path = DEFAULT_HTML_OUTPUT,
) -> None:
    write_json(output_manifest, manifest)
    write_jsonl(output_previews, previews)
    output_html.parent.mkdir(parents=True, exist_ok=True)
    output_html.write_text(render_outputs["html"]["kmfa_manual_impact_preview"], encoding="utf-8")
    stage_manifest = {
        "schema_version": "kmfa.stage_artifact_manifest.v1",
        "record_type": "stage_artifact_manifest",
        "project_id": "KMFA",
        "stage_phase": "S12-P2",
        "status": "completed_validated_local_only",
        "artifact_refs": manifest["artifact_refs"],
        "summary": manifest["summary"],
        "quality_gate": manifest["quality_gate"],
        "stage_scope": manifest["stage_scope"],
        "content_hash": _sha256_json({"manifest": manifest, "previews": previews}),
    }
    write_json(output_stage_manifest, stage_manifest)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build KMFA S12-P2 public-safe impact preview artifacts.")
    parser.add_argument("--source-manifest", type=Path, default=DEFAULT_SOURCE_MANIFEST)
    parser.add_argument("--source-events", type=Path, default=DEFAULT_SOURCE_EVENTS)
    parser.add_argument("--output-manifest", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    parser.add_argument("--output-previews", type=Path, default=DEFAULT_OUTPUT_PREVIEWS)
    parser.add_argument("--output-stage-manifest", type=Path, default=DEFAULT_OUTPUT_STAGE_MANIFEST)
    parser.add_argument("--output-html", type=Path, default=DEFAULT_HTML_OUTPUT)
    parser.add_argument("--generated-at", default="2026-07-01T13:00:00+10:00")
    args = parser.parse_args(argv)

    source_event_manifest = read_json(args.source_manifest)
    source_events = read_jsonl(args.source_events)
    manifest, previews, render_outputs = build_default_manual_impact_preview_artifacts(
        source_event_manifest=source_event_manifest,
        source_events=source_events,
        generated_at=args.generated_at,
    )
    validate_manual_impact_preview_artifacts(manifest, previews, render_outputs, source_events)
    write_manual_impact_preview_artifacts(
        manifest=manifest,
        previews=previews,
        render_outputs=render_outputs,
        output_manifest=args.output_manifest,
        output_previews=args.output_previews,
        output_stage_manifest=args.output_stage_manifest,
        output_html=args.output_html,
    )
    summary = manifest["summary"]
    print(
        "PASS: KMFA S12-P2 manual impact preview artifacts generated "
        f"(previews={summary['impact_preview_count']}, "
        f"projects={summary['affected_project_count']}, "
        f"metrics={summary['affected_metric_count']}, "
        f"reports={summary['affected_report_count']}, "
        f"high_risk={summary['high_risk_count']}, "
        f"blocked_publish={summary['blocked_publish_count']}, "
        "rerun=false, formal_report=false, stage12_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
