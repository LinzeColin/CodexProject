#!/usr/bin/env python3
"""Build KMFA S12-P1 public-safe manual resolution event artifacts."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

DEFAULT_OUTPUT_MANIFEST = ROOT / "metadata" / "approvals" / "manual_resolution_event_manifest.json"
DEFAULT_OUTPUT_EVENTS = ROOT / "metadata" / "approvals" / "manual_resolution_events.jsonl"
DEFAULT_OUTPUT_STAGE_MANIFEST = (
    ROOT / "stage_artifacts" / "S12_P1_manual_resolution_events" / "machine" / "s12_p1_manifest.json"
)
DEFAULT_HTML_OUTPUT = (
    ROOT
    / "stage_artifacts"
    / "S12_P1_manual_resolution_events"
    / "exports"
    / "html"
    / "kmfa_manual_resolution_workbench.html"
)

REQUIRED_MANUAL_ACTION_KINDS = ("field_mapping", "project_matching", "difference_handling", "note")
REQUIRED_EVENT_TYPES = ("mapping_rule", "approval_event", "resolution_event", "comment")
REQUIRED_EVENT_FIELDS = (
    "event_id",
    "schema_version",
    "record_type",
    "stage_phase",
    "event_type",
    "manual_action_kind",
    "actor_ref",
    "actor_role",
    "event_time",
    "reason_code",
    "reason_summary",
    "impact_scope",
    "event_version",
    "target_layer",
    "target_ref",
    "status",
    "append_only",
    "raw_layer_write_allowed",
    "raw_source_mutation_allowed",
    "source_layer_write_allowed",
    "business_plaintext_committed",
    "forbidden_plaintext",
    "evidence_refs",
)
ALLOWED_EVENT_TYPES = {
    "mapping_rule",
    "resolution_event",
    "approval_event",
    "comment",
    "rerun_request",
    "invalidation_request",
}
ALLOWED_TARGET_LAYERS = {"schema_maps", "approvals", "lineage", "quality", "reports"}
APPROVED_EVENT_ID = "MANEVT-S12P1-003"
MANUAL_EVENT_VERSION = "MANUAL-EVENT-KMFA-S12P1-001"
WORKBENCH_VERSION = "UI-KMFA-S12P1-MANUAL-WORKBENCH-001"
PUBLIC_SAFETY_VERSION = "SAFE-KMFA-S12P1-PUBLIC-001"
EVENT_ID_RE = re.compile(r"^MANEVT-S12P1-[0-9]{3}$")

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


class ManualResolutionEventError(ValueError):
    """Raised when S12-P1 manual resolution event artifacts are invalid."""


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ManualResolutionEventError(f"{path} contains a non-object JSONL row")
            rows.append(value)
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )


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
        "manual_resolution_event_write_allowed": True,
        "control_event_append_only": True,
        "approved_event_silent_update_allowed": False,
        "approved_event_reversal_required_for_change": True,
        "raw_layer_write_allowed": False,
        "raw_source_mutation_allowed": False,
        "source_layer_write_allowed": False,
        "business_plaintext_commit_allowed": False,
        "impact_preview_publish_allowed": False,
        "derived_rerun_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "github_upload_allowed": False,
        "phase_completion_upload_allowed": False,
    }


def _stage_scope() -> dict[str, bool]:
    return {
        "s12_p1_manual_resolution_event_scope_included": True,
        "s12_p2_impact_preview_scope_included": False,
        "s12_p3_rerun_mechanism_scope_included": False,
        "stage12_review_scope_included": False,
        "github_upload_scope_included": False,
        "lineage_full_check_scope_included": False,
        "formal_report_runtime_scope_included": False,
        "external_connector_scope_included": False,
        "difference_closure_scope_included": False,
    }


def _event(
    *,
    index: int,
    event_type: str,
    manual_action_kind: str,
    event_action: str,
    actor_role: str,
    reason_code: str,
    reason_summary: str,
    impact_scope: list[str],
    target_layer: str,
    target_ref: str,
    status: str,
    event_time: str,
    evidence_refs: list[str],
    approval_state: str = "draft",
    approved_event_immutable: bool = False,
    silent_update_allowed: bool = False,
    reversal_required_for_change: bool = False,
    reverses_event_id: str | None = None,
) -> dict[str, Any]:
    event_id = f"MANEVT-S12P1-{index:03d}"
    row: dict[str, Any] = {
        "event_id": event_id,
        "schema_version": "kmfa.manual_resolution_event.v1",
        "record_type": "manual_resolution_event",
        "project_id": "KMFA",
        "system_name": "KMFA 经营分析系统",
        "stage_phase": "S12-P1",
        "event_type": event_type,
        "manual_action_kind": manual_action_kind,
        "event_action": event_action,
        "actor_ref": "actor_ref://owner_or_authorized_delegate/s12p1-public-safe",
        "actor_role": actor_role,
        "event_time": event_time,
        "reason_code": reason_code,
        "reason_summary": reason_summary,
        "impact_scope": impact_scope,
        "event_version": f"{MANUAL_EVENT_VERSION}.{index:03d}",
        "target_layer": target_layer,
        "target_ref": target_ref,
        "status": status,
        "approval_state": approval_state,
        "approved_event_immutable": approved_event_immutable,
        "silent_update_allowed": silent_update_allowed,
        "reversal_required_for_change": reversal_required_for_change,
        "reverses_event_id": reverses_event_id,
        "append_only": True,
        "raw_layer_write_allowed": False,
        "raw_source_mutation_allowed": False,
        "source_layer_write_allowed": False,
        "business_plaintext_committed": False,
        "forbidden_plaintext": False,
        "evidence_refs": evidence_refs,
        "public_repo_safety": _public_repo_safety(),
        "content_hash": "",
    }
    row["content_hash"] = _sha256_json({key: value for key, value in row.items() if key != "content_hash"})
    return row


def _manual_events(generated_at: str) -> list[dict[str, Any]]:
    return [
        _event(
            index=1,
            event_type="mapping_rule",
            manual_action_kind="field_mapping",
            event_action="propose_field_mapping_rule",
            actor_role="owner_or_authorized_delegate",
            reason_code="FIELD_ALIAS_REVIEW_REQUIRED",
            reason_summary="公开安全字段映射规则需要人工确认后追加为控制事件。",
            impact_scope=["field_mapping_catalog", "source_check_board_status"],
            target_layer="schema_maps",
            target_ref="MAP-KMFA-S12P1-FIELD-ALIAS-REVIEW",
            status="recorded_pending_approval",
            event_time=generated_at,
            evidence_refs=["KMFA/metadata/schema_maps/field_alias_dictionary.csv", "KMFA/tools/manual_resolution_events.py"],
        ),
        _event(
            index=2,
            event_type="approval_event",
            manual_action_kind="project_matching",
            event_action="confirm_project_match_review",
            actor_role="owner_or_authorized_delegate",
            reason_code="PROJECT_MATCH_REVIEW_REQUIRED",
            reason_summary="项目匹配需要人工确认为公开安全匹配控制事件，不自动合并实体。",
            impact_scope=["project_identity_review_queue", "project_cost_page_pending_actions"],
            target_layer="approvals",
            target_ref="PMATCH-KMFA-S12P1-PROJECT-GROUP-REVIEW",
            status="recorded_pending_approval",
            event_time=generated_at,
            evidence_refs=[
                "KMFA/metadata/quality/project_identity_review_queue.jsonl",
                "KMFA/metadata/quality/entity_matching_review_queue.jsonl",
            ],
        ),
        _event(
            index=3,
            event_type="resolution_event",
            manual_action_kind="difference_handling",
            event_action="approve_difference_handling_note",
            actor_role="owner_or_authorized_delegate",
            reason_code="DIFFERENCE_HANDLING_APPROVED",
            reason_summary="差异处理意见已批准为事件版本，但不写入原始层且不触发本 phase 重跑。",
            impact_scope=["scope_reconciliation_queue", "project_cost_report_preview_grade"],
            target_layer="quality",
            target_ref="S09P3-REC-001",
            status="approved",
            event_time=generated_at,
            evidence_refs=[
                "KMFA/metadata/quality/scope_reconciliation_records.jsonl",
                "KMFA/stage_artifacts/S09_P3_scope_reconciliation/human/s09_p3_completion_record.md",
            ],
            approval_state="approved",
            approved_event_immutable=True,
            silent_update_allowed=False,
            reversal_required_for_change=True,
        ),
        _event(
            index=4,
            event_type="comment",
            manual_action_kind="note",
            event_action="add_review_note",
            actor_role="owner_or_authorized_delegate",
            reason_code="OWNER_NOTE_RECORDED",
            reason_summary="人工备注只作为追加事件保存，供后续影响预览和复核队列读取。",
            impact_scope=["manual_resolution_workbench", "review_note_log"],
            target_layer="approvals",
            target_ref="NOTE-KMFA-S12P1-BOARD-QUESTION",
            status="recorded_pending_approval",
            event_time=generated_at,
            evidence_refs=["KMFA/stage_artifacts/S12_P1_manual_resolution_events/human/s12_p1_completion_record.md"],
        ),
        _event(
            index=5,
            event_type="resolution_event",
            manual_action_kind="difference_handling",
            event_action="reverse_approved_event",
            actor_role="owner_or_authorized_delegate",
            reason_code="APPROVED_EVENT_REVERSAL_RECORDED",
            reason_summary="已批准事件需要变更时只能追加反向事件，不能静默改写原事件。",
            impact_scope=["scope_reconciliation_queue", "manual_resolution_audit_log"],
            target_layer="quality",
            target_ref="S09P3-REC-001",
            status="reverse_event_recorded",
            event_time=generated_at,
            evidence_refs=["KMFA/metadata/approvals/manual_resolution_events.jsonl"],
            approval_state="reversal_recorded",
            reverses_event_id=APPROVED_EVENT_ID,
        ),
    ]


def _render_html(events: list[dict[str, Any]], manifest: dict[str, Any]) -> str:
    summary = manifest["summary"]
    cards = (
        f'<div class="card"><span>处理事件</span><b>{summary["manual_event_count"]}</b><small>只追加写入</small></div>'
        f'<div class="card"><span>动作类型</span><b>{summary["manual_action_kind_count"]}</b><small>字段/项目/差异/备注</small></div>'
        f'<div class="card"><span>原始数据 0 写入</span><b>0</b><small>只写控制事件</small></div>'
        f'<div class="card"><span>追加反向事件</span><b>{summary["reverse_event_count"]}</b><small>禁止静默改写</small></div>'
    )
    rows = "\n".join(
        f"""          <tr>
            <td>{html.escape(_action_label(event["manual_action_kind"]))}</td>
            <td>{html.escape(event["status"])}</td>
            <td>{html.escape(event["reason_code"])}</td>
            <td>{html.escape("、".join(event["impact_scope"]))}</td>
            <td>{html.escape(event["event_version"])}</td>
          </tr>"""
        for event in events
    )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>KMFA 人工处理工作台</title>
  <style>
    :root {{
      --navy:#0b1f3a;
      --blue:#1d4ed8;
      --sky:#eaf3ff;
      --line:#d8e4f5;
      --text:#152033;
      --muted:#64748b;
      --bg:#f6f9fe;
      --card:#ffffff;
      --ok:#166534;
      --review:#5b21b6;
    }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:var(--bg); color:var(--text); font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",Arial,sans-serif; }}
    .header {{ background:linear-gradient(135deg,var(--navy),#123a70 55%,#2563eb); color:#fff; padding:30px 40px; }}
    .brand {{ display:flex; align-items:center; gap:14px; }}
    .logo {{ width:52px; height:52px; border:1px solid rgba(255,255,255,.45); border-radius:12px; display:flex; align-items:center; justify-content:center; font-weight:800; background:rgba(255,255,255,.10); }}
    h1 {{ margin:0; font-size:28px; letter-spacing:0; }}
    .sub {{ margin-top:8px; color:#d6e7ff; line-height:1.65; }}
    .wrap {{ max-width:1220px; margin:0 auto; padding:24px; }}
    .cards {{ display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin-bottom:18px; }}
    .card {{ background:#fff; border:1px solid var(--line); border-radius:8px; padding:16px; box-shadow:0 12px 28px rgba(17,45,88,.06); }}
    .card span {{ display:block; color:var(--muted); font-size:13px; }}
    .card b {{ display:block; color:#0b2b59; font-size:26px; margin:6px 0; }}
    .card small {{ color:#475569; }}
    .toolbar {{ display:flex; justify-content:space-between; gap:16px; align-items:flex-start; margin-bottom:14px; }}
    .note {{ color:#475569; line-height:1.7; max-width:760px; }}
    .pill {{ border:1px solid #bfdbfe; background:#fff; color:var(--blue); border-radius:999px; padding:7px 12px; font-size:12px; font-weight:800; white-space:nowrap; }}
    .grid {{ display:grid; grid-template-columns:1.15fr .85fr; gap:14px; align-items:start; }}
    .panel {{ background:#fff; border:1px solid var(--line); border-radius:8px; padding:16px; }}
    .panel h2 {{ margin:0 0 10px; color:#0b2b59; font-size:18px; }}
    .actions {{ display:grid; grid-template-columns:repeat(2,1fr); gap:10px; }}
    button {{ border:1px solid #bfdbfe; background:#eff6ff; color:#1e3a8a; border-radius:8px; padding:11px 12px; font-weight:800; text-align:left; }}
    button.secondary {{ background:#f8fafc; color:#334155; }}
    table {{ width:100%; border-collapse:separate; border-spacing:0; }}
    th {{ background:#0f2f5f; color:#fff; text-align:left; font-size:13px; padding:12px; }}
    td {{ padding:12px; font-size:13px; line-height:1.55; border-bottom:1px solid #edf2f7; vertical-align:top; }}
    .audit {{ display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-top:12px; }}
    .audit div {{ border:1px solid var(--line); border-radius:8px; background:var(--sky); padding:12px; color:#1e3a5f; line-height:1.6; }}
    .footer {{ margin-top:14px; color:#64748b; font-size:12px; line-height:1.6; }}
    @media(max-width:980px) {{ .cards,.grid {{ grid-template-columns:1fr 1fr; }} .toolbar {{ display:block; }} .pill {{ display:inline-flex; margin-top:10px; }} }}
    @media(max-width:720px) {{ .cards,.grid,.actions,.audit {{ grid-template-columns:1fr; }} .wrap {{ padding:16px; }} .header {{ padding:24px; }} }}
  </style>
</head>
<body>
  <header class="header">
    <div class="brand"><div class="logo">KM</div><div><h1>KMFA 人工处理工作台</h1><div class="sub">差异处理工作台采用 v1.2 蓝色商务样板，只写处理事件，不修改原始上传数据。</div></div></div>
  </header>
  <main class="wrap">
    <section class="cards" aria-label="人工处理摘要">{cards}</section>
    <section class="toolbar">
      <div class="note">本页展示 S12-P1 事件写入协议：字段映射、项目匹配、差异处理和备注均写为追加事件。影响预览未发布，重跑未执行，正式报告仍阻断。</div>
      <span class="pill">S12-P1 local only</span>
    </section>
    <section class="grid">
      <div class="panel">
        <h2>处理事件</h2>
        <div class="actions">
          <button type="button">字段映射</button>
          <button type="button">项目匹配</button>
          <button type="button">差异处理</button>
          <button type="button" class="secondary">备注</button>
        </div>
        <div class="audit">
          <div>处理人、时间、原因、影响范围、版本均为必填。</div>
          <div>已批准事件不可静默改写，只能追加反向事件。</div>
          <div>影响预览未发布，高风险二次确认留到 S12-P2。</div>
          <div>重跑未执行，派生链路留到 S12-P3。</div>
        </div>
      </div>
      <div class="panel">
        <h2>治理门禁</h2>
        <p class="note">原始文件、原始抽取、历史报告和已批准历史处理事件不可被前端覆盖。当前只验证事件结构和不可污染边界。</p>
      </div>
    </section>
    <section class="panel" style="margin-top:14px" aria-label="事件列表">
      <h2>事件列表</h2>
      <table>
        <thead><tr><th>动作</th><th>状态</th><th>原因</th><th>影响范围</th><th>版本</th></tr></thead>
        <tbody>
{rows}
        </tbody>
      </table>
    </section>
    <div class="footer">KMFA 经营分析系统 · S12-P1 人工处理事件 · 本页面不执行影响预览、重跑机制、Stage 12 复审、上传、完整追溯检查或外部接口。</div>
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


def build_default_manual_resolution_event_artifacts(
    *,
    generated_at: str = "2026-07-01T12:00:00+10:00",
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, dict[str, str]]]:
    events = _manual_events(generated_at)
    action_kinds = {event["manual_action_kind"] for event in events}
    approved_events = [event for event in events if event.get("approval_state") == "approved"]
    reverse_events = [event for event in events if event.get("event_action") == "reverse_approved_event"]
    manifest: dict[str, Any] = {
        "schema_version": "kmfa.manual_resolution_event_manifest.v1",
        "record_type": "manual_resolution_event_manifest",
        "project_id": "KMFA",
        "system_name": "KMFA 经营分析系统",
        "stage_phase": "S12-P1",
        "runtime_status": "public_safe_manual_resolution_events_generated_local_only",
        "manual_event_version": MANUAL_EVENT_VERSION,
        "workbench_version": WORKBENCH_VERSION,
        "public_safety_version": PUBLIC_SAFETY_VERSION,
        "generated_at": generated_at,
        "required_manual_action_kinds": list(REQUIRED_MANUAL_ACTION_KINDS),
        "required_event_types": list(REQUIRED_EVENT_TYPES),
        "required_event_fields": list(REQUIRED_EVENT_FIELDS),
        "source_taskpack_refs": {
            "roadmap_s12_p1": "KMFA/taskpack/v1_2/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_2.md:S12-P1",
            "resolution_workbench_sample": (
                "KMFA/taskpack/v1_2/20_HTML_UIUX_报告预览/01_核心HTML验收样板/"
                "KMFA_Resolution_Workbench_v0_4.html"
            ),
            "control_event_policy": "KMFA/metadata/approvals/control_event_policy.yaml",
            "upstream_reconciliation": "KMFA/metadata/quality/scope_reconciliation_records.jsonl",
            "upstream_project_page": "KMFA/metadata/reports/project_cost_page_manifest.json",
        },
        "quality_gate": _quality_gate(),
        "stage_scope": _stage_scope(),
        "public_repo_safety": _public_repo_safety(),
        "artifact_refs": {
            "manual_resolution_event_manifest": "KMFA/metadata/approvals/manual_resolution_event_manifest.json",
            "manual_resolution_events": "KMFA/metadata/approvals/manual_resolution_events.jsonl",
            "html_export": "KMFA/stage_artifacts/S12_P1_manual_resolution_events/exports/html/kmfa_manual_resolution_workbench.html",
            "validator": "KMFA/tools/check_s12_p1_manual_resolution_events.py",
            "completion_record": "KMFA/stage_artifacts/S12_P1_manual_resolution_events/human/s12_p1_completion_record.md",
            "test_results": "KMFA/stage_artifacts/S12_P1_manual_resolution_events/human/test_results.md",
            "stage_manifest": "KMFA/stage_artifacts/S12_P1_manual_resolution_events/machine/s12_p1_manifest.json",
        },
        "summary": {
            "manual_event_count": len(events),
            "manual_action_kind_count": len(action_kinds),
            "event_type_count": len({event["event_type"] for event in events}),
            "approved_event_count": len(approved_events),
            "reverse_event_count": len(reverse_events),
            "raw_layer_write_count": 0,
            "source_mutation_count": 0,
            "business_plaintext_count": 0,
            "impact_preview_publish_count": 0,
            "derived_rerun_count": 0,
            "formal_report_count": 0,
            "github_upload_count": 0,
        },
        "limitations": [
            "S12-P1 只建立人工处理事件结构和工作台证据，不发布影响预览。",
            "本 phase 不执行派生链路重跑，不关闭差异，不升级报告等级。",
            "已批准事件需要变更时只能追加反向事件，不允许静默覆盖原事件。",
            "公开仓库只保存 public-safe 事件 metadata、hash、状态、证据索引和 HTML 样张。",
        ],
    }
    render_outputs = {"html": {"kmfa_manual_resolution_workbench": _render_html(events, manifest)}}
    manifest["content_hash"] = _sha256_json({"manifest": manifest, "events": events, "render_outputs": render_outputs})
    return manifest, events, render_outputs


def _looks_like_forbidden_private_file(value: str) -> bool:
    lowered = value.lower()
    return any(suffix in lowered for suffix in FORBIDDEN_PUBLIC_SUFFIXES)


def _ensure_no_forbidden_public_payload(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in FORBIDDEN_PUBLIC_KEYS:
                raise ManualResolutionEventError(f"forbidden public key found: {key}")
            _ensure_no_forbidden_public_payload(item)
    elif isinstance(value, list):
        for item in value:
            _ensure_no_forbidden_public_payload(item)
    elif isinstance(value, str):
        lowered = value.lower()
        if _looks_like_forbidden_private_file(value):
            raise ManualResolutionEventError(f"forbidden private business file reference found: {value}")
        if any(forbidden in lowered for forbidden in FORBIDDEN_PUBLIC_TEXT):
            raise ManualResolutionEventError(f"forbidden private token found: {value}")


def _require_non_empty(value: Any, label: str) -> None:
    if value is None:
        raise ManualResolutionEventError(f"{label} is required")
    if isinstance(value, str) and not value.strip():
        raise ManualResolutionEventError(f"{label} is required")
    if isinstance(value, list) and not value:
        raise ManualResolutionEventError(f"{label} is required")


def _validate_event(event: dict[str, Any], expected_index: int) -> None:
    label = str(event.get("event_id") or f"event-{expected_index}")
    missing = [field for field in REQUIRED_EVENT_FIELDS if field not in event]
    if missing:
        raise ManualResolutionEventError(f"{label} missing fields: {', '.join(missing)}")
    for field in REQUIRED_EVENT_FIELDS:
        _require_non_empty(event[field], f"{label}.{field}")
    if not EVENT_ID_RE.match(str(event["event_id"])):
        raise ManualResolutionEventError(f"{label}.event_id format mismatch")
    if event["record_type"] != "manual_resolution_event":
        raise ManualResolutionEventError(f"{label}.record_type mismatch")
    if event["stage_phase"] != "S12-P1":
        raise ManualResolutionEventError(f"{label}.stage_phase must be S12-P1")
    if event["event_type"] not in ALLOWED_EVENT_TYPES:
        raise ManualResolutionEventError(f"{label}.event_type not allowed")
    if event["manual_action_kind"] not in REQUIRED_MANUAL_ACTION_KINDS:
        raise ManualResolutionEventError(f"{label}.manual_action_kind not allowed")
    if event["target_layer"] not in ALLOWED_TARGET_LAYERS:
        raise ManualResolutionEventError(f"{label}.target_layer not allowed")
    for flag in (
        "raw_layer_write_allowed",
        "raw_source_mutation_allowed",
        "source_layer_write_allowed",
        "business_plaintext_committed",
        "forbidden_plaintext",
        "silent_update_allowed",
    ):
        if event.get(flag) is not False:
            raise ManualResolutionEventError(f"{label}.{flag} must be false")
    if event.get("append_only") is not True:
        raise ManualResolutionEventError(f"{label}.append_only must be true")
    if event.get("approval_state") == "approved":
        if event.get("approved_event_immutable") is not True:
            raise ManualResolutionEventError(f"{label}.approved_event_immutable must be true")
        if event.get("reversal_required_for_change") is not True:
            raise ManualResolutionEventError(f"{label}.reversal_required_for_change must be true")
    if event.get("event_action") == "reverse_approved_event" and not event.get("reverses_event_id"):
        raise ManualResolutionEventError(f"{label}.reverses_event_id is required")


def _validate_html(html_text: str) -> None:
    if not html_text.startswith("<!doctype html>"):
        raise ManualResolutionEventError("html output must start with doctype")
    required_texts = (
        "KMFA 人工处理工作台",
        "处理事件",
        "字段映射",
        "项目匹配",
        "差异处理",
        "备注",
        "追加反向事件",
        "原始数据 0 写入",
        "影响预览未发布",
        "重跑未执行",
    )
    for text in required_texts:
        if text not in html_text:
            raise ManualResolutionEventError(f"html missing required text: {text}")
    lowered = html_text.lower()
    for forbidden in ("private_ref://", "source_ref://", "validator", "manifest", "metadata"):
        if forbidden in lowered:
            raise ManualResolutionEventError(f"html exposes internal token: {forbidden}")
    for suffix in FORBIDDEN_PUBLIC_SUFFIXES:
        if suffix in lowered:
            raise ManualResolutionEventError(f"html exposes forbidden suffix: {suffix}")


def validate_manual_resolution_event_artifacts(
    manifest: dict[str, Any],
    events: list[dict[str, Any]],
    render_outputs: dict[str, dict[str, str]],
) -> None:
    if manifest.get("record_type") != "manual_resolution_event_manifest":
        raise ManualResolutionEventError("manifest record_type mismatch")
    if manifest.get("stage_phase") != "S12-P1":
        raise ManualResolutionEventError("manifest stage_phase must be S12-P1")
    if tuple(manifest.get("required_manual_action_kinds", [])) != REQUIRED_MANUAL_ACTION_KINDS:
        raise ManualResolutionEventError("manual action kind contract mismatch")
    if tuple(manifest.get("required_event_types", [])) != REQUIRED_EVENT_TYPES:
        raise ManualResolutionEventError("event type contract mismatch")
    if manifest["summary"].get("manual_event_count") != len(events):
        raise ManualResolutionEventError("manual event count mismatch")
    if manifest["summary"].get("manual_event_count") != 5:
        raise ManualResolutionEventError("S12-P1 must expose five public-safe event records")
    if {event.get("manual_action_kind") for event in events} != set(REQUIRED_MANUAL_ACTION_KINDS):
        raise ManualResolutionEventError("S12-P1 action kind coverage mismatch")
    approved_events = [event for event in events if event.get("approval_state") == "approved"]
    reverse_events = [event for event in events if event.get("event_action") == "reverse_approved_event"]
    if len(approved_events) != 1:
        raise ManualResolutionEventError("expected exactly one approved event fixture")
    if len(reverse_events) != 1:
        raise ManualResolutionEventError("expected exactly one reverse event fixture")
    approved_by_id = {event["event_id"]: event for event in approved_events}
    reverse = reverse_events[0]
    reversed_event = approved_by_id.get(str(reverse.get("reverses_event_id")))
    if reversed_event is None:
        raise ManualResolutionEventError("reverse event must reference an approved event")
    if reverse.get("target_ref") != reversed_event.get("target_ref"):
        raise ManualResolutionEventError("reverse event target_ref must match approved event target_ref")
    for index, event in enumerate(events, start=1):
        _validate_event(event, index)
    for flag in (
        "raw_layer_write_allowed",
        "raw_source_mutation_allowed",
        "source_layer_write_allowed",
        "business_plaintext_commit_allowed",
        "impact_preview_publish_allowed",
        "derived_rerun_allowed",
        "formal_report_allowed",
        "business_decision_basis_allowed",
        "github_upload_allowed",
    ):
        if manifest["quality_gate"].get(flag) is not False:
            raise ManualResolutionEventError(f"quality gate {flag} must be false")
    for flag in (
        "s12_p2_impact_preview_scope_included",
        "s12_p3_rerun_mechanism_scope_included",
        "stage12_review_scope_included",
        "github_upload_scope_included",
        "lineage_full_check_scope_included",
        "formal_report_runtime_scope_included",
        "external_connector_scope_included",
        "difference_closure_scope_included",
    ):
        if manifest["stage_scope"].get(flag) is not False:
            raise ManualResolutionEventError(f"stage scope {flag} must be false")
    html_text = render_outputs.get("html", {}).get("kmfa_manual_resolution_workbench")
    if not html_text:
        raise ManualResolutionEventError("missing html render output")
    _validate_html(html_text)
    _ensure_no_forbidden_public_payload(manifest)
    _ensure_no_forbidden_public_payload(events)
    _ensure_no_forbidden_public_payload(render_outputs)


def write_manual_resolution_event_artifacts(
    manifest: dict[str, Any],
    events: list[dict[str, Any]],
    render_outputs: dict[str, dict[str, str]],
    *,
    manifest_path: Path = DEFAULT_OUTPUT_MANIFEST,
    events_path: Path = DEFAULT_OUTPUT_EVENTS,
    stage_manifest_path: Path = DEFAULT_OUTPUT_STAGE_MANIFEST,
    html_path: Path = DEFAULT_HTML_OUTPUT,
) -> None:
    validate_manual_resolution_event_artifacts(manifest, events, render_outputs)
    write_json(manifest_path, manifest)
    write_jsonl(events_path, events)
    write_json(stage_manifest_path, manifest)
    html_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.write_text(render_outputs["html"]["kmfa_manual_resolution_workbench"], encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build KMFA S12-P1 manual resolution event artifacts.")
    parser.add_argument("--generated-at", default="2026-07-01T12:00:00+10:00")
    args = parser.parse_args(argv)

    manifest, events, render_outputs = build_default_manual_resolution_event_artifacts(generated_at=args.generated_at)
    write_manual_resolution_event_artifacts(manifest, events, render_outputs)
    summary = manifest["summary"]
    print(
        "PASS: KMFA S12-P1 manual resolution event artifacts generated "
        f"(events={summary['manual_event_count']}, "
        f"action_kinds={summary['manual_action_kind_count']}, "
        f"approved_events={summary['approved_event_count']}, "
        f"reverse_events={summary['reverse_event_count']}, "
        "raw_layer_write_allowed=false, approved_silent_update=false, "
        "impact_preview=false, rerun=false, formal_report_allowed=false, "
        "stage12_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
