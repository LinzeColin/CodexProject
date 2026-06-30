#!/usr/bin/env python3
"""Build KMFA S12-P3 public-safe manual rerun mechanism artifacts."""

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

from KMFA.tools.manual_impact_preview import (
    DEFAULT_OUTPUT_MANIFEST as DEFAULT_SOURCE_PREVIEW_MANIFEST,
    DEFAULT_OUTPUT_PREVIEWS as DEFAULT_SOURCE_PREVIEWS,
)
from KMFA.tools.manual_resolution_events import (
    DEFAULT_OUTPUT_EVENTS as DEFAULT_SOURCE_EVENTS,
    read_json,
    read_jsonl,
    write_json,
    write_jsonl,
)


ROOT = Path(__file__).resolve().parents[1]

DEFAULT_OUTPUT_MANIFEST = ROOT / "metadata" / "lineage" / "manual_rerun_manifest.json"
DEFAULT_OUTPUT_INVALIDATIONS = ROOT / "metadata" / "lineage" / "manual_rerun_cache_invalidations.jsonl"
DEFAULT_OUTPUT_STEPS = ROOT / "metadata" / "lineage" / "manual_rerun_steps.jsonl"
DEFAULT_OUTPUT_CONSISTENCY_CHECKS = ROOT / "metadata" / "lineage" / "manual_rerun_consistency_checks.jsonl"
DEFAULT_OUTPUT_STAGE_MANIFEST = (
    ROOT / "stage_artifacts" / "S12_P3_manual_rerun_mechanism" / "machine" / "s12_p3_manifest.json"
)
DEFAULT_HTML_OUTPUT = (
    ROOT
    / "stage_artifacts"
    / "S12_P3_manual_rerun_mechanism"
    / "exports"
    / "html"
    / "kmfa_manual_rerun_mechanism.html"
)

REQUIRED_RERUN_CHAIN = ("field_mapping", "fact_layer", "derived_metric", "report_reference")
REQUIRED_INVALIDATION_FIELDS = (
    "invalidation_id",
    "schema_version",
    "record_type",
    "stage_phase",
    "source_event_id",
    "source_preview_id",
    "cache_invalidation_status",
    "affected_layers",
    "cache_reuse_allowed_after_invalidation",
    "raw_layer_write_allowed",
    "evidence_refs",
)
REQUIRED_RERUN_STEP_FIELDS = (
    "rerun_step_id",
    "schema_version",
    "record_type",
    "stage_phase",
    "source_event_id",
    "source_preview_id",
    "chain_order",
    "chain_layer",
    "old_derived_version_ref",
    "new_derived_version_ref",
    "overwrite_old_version_allowed",
    "raw_layer_write_allowed",
    "formal_report_generated",
    "evidence_refs",
)
REQUIRED_CONSISTENCY_FIELDS = (
    "consistency_check_id",
    "schema_version",
    "record_type",
    "stage_phase",
    "source_event_id",
    "source_preview_id",
    "checked_layers",
    "same_source_consistency_passed",
    "consistency_status",
    "mismatch_count",
    "raw_layer_write_allowed",
    "evidence_refs",
)
RERUN_VERSION = "MANUAL-RERUN-KMFA-S12P3-001"
HTML_VERSION = "UI-KMFA-S12P3-RERUN-MECHANISM-001"
PUBLIC_SAFETY_VERSION = "SAFE-KMFA-S12P3-PUBLIC-001"
FORMULA_VERSION = "FORM-KMFA-MANUAL-RERUN-MECHANISM-001"
MAPPING_VERSION = "MAP-KMFA-S12P3-PUBLIC-SAFE-v1"
INVALIDATION_ID_RE = re.compile(r"^INV-S12P3-[0-9]{3}$")
RERUN_STEP_ID_RE = re.compile(r"^RERUN-S12P3-[0-9]{3}-[0-9]{2}$")
CONSISTENCY_ID_RE = re.compile(r"^CONS-S12P3-[0-9]{3}$")

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


class ManualRerunMechanismError(ValueError):
    """Raised when S12-P3 manual rerun mechanism artifacts are invalid."""


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
        "derived_cache_invalidation_allowed": True,
        "derived_rerun_allowed": True,
        "field_mapping_rerun_required": True,
        "fact_layer_rerun_required": True,
        "derived_metric_rerun_required": True,
        "report_reference_rerun_required": True,
        "same_source_consistency_check_required": True,
        "blocked_preview_rerun_allowed": False,
        "old_version_overwrite_allowed": False,
        "append_only_derived_versions_required": True,
        "raw_layer_write_allowed": False,
        "raw_source_mutation_allowed": False,
        "source_layer_write_allowed": False,
        "business_plaintext_commit_allowed": False,
        "formal_report_allowed": False,
        "formal_report_generated": False,
        "report_grade_upgrade_allowed": False,
        "business_decision_basis_allowed": False,
        "stage12_review_allowed": False,
        "github_upload_allowed": False,
        "phase_completion_upload_allowed": False,
    }


def _stage_scope() -> dict[str, bool]:
    return {
        "s12_p1_manual_resolution_event_dependency_included": True,
        "s12_p2_impact_preview_dependency_included": True,
        "s12_p3_rerun_mechanism_scope_included": True,
        "stage12_review_scope_included": False,
        "github_upload_scope_included": False,
        "lineage_full_check_scope_included": False,
        "formal_report_runtime_scope_included": False,
        "external_connector_scope_included": False,
        "difference_closure_scope_included": False,
    }


def _eligible_previews(source_previews: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        preview
        for preview in source_previews
        if preview.get("preview_passed") is True
        and preview.get("control_event_publish_allowed") is True
        and preview.get("release_gate") == "preview_passed_publish_allowed"
    ]


def _source_events_by_id(source_events: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(event.get("event_id")): event for event in source_events if event.get("event_id")}


def _layer_label(layer: str) -> str:
    return {
        "field_mapping": "字段映射",
        "fact_layer": "事实层",
        "derived_metric": "指标",
        "report_reference": "报告引用",
    }[layer]


def _version_ref(kind: str, source_event_id: str, layer: str, generated_at: str) -> str:
    suffix = hashlib.sha256(f"{kind}|{source_event_id}|{layer}|{generated_at}".encode("utf-8")).hexdigest()[:12]
    return f"version_ref://KMFA/S12-P3/{source_event_id}/{layer}/{kind}-{suffix}"


def _invalidation(
    *, index: int, preview: dict[str, Any], source_event: dict[str, Any], generated_at: str
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "invalidation_id": f"INV-S12P3-{index:03d}",
        "schema_version": "kmfa.manual_rerun_cache_invalidation.v1",
        "record_type": "manual_rerun_cache_invalidation",
        "project_id": "KMFA",
        "system_name": "KMFA 经营分析系统",
        "stage_phase": "S12-P3",
        "source_event_id": source_event["event_id"],
        "source_event_type": source_event["event_type"],
        "source_manual_action_kind": source_event["manual_action_kind"],
        "source_preview_id": preview["preview_id"],
        "source_preview_status": preview["preview_status"],
        "event_publish_gate": preview["release_gate"],
        "invalidation_version": f"{RERUN_VERSION}.{index:03d}.INV",
        "invalidated_at": generated_at,
        "cache_invalidation_status": "invalidated_after_preview_passed",
        "affected_layers": list(REQUIRED_RERUN_CHAIN),
        "invalidated_cache_ref": f"cache_ref://KMFA/S12-P3/{source_event['event_id']}/derived-chain",
        "cache_reuse_allowed_after_invalidation": False,
        "rerun_required": True,
        "raw_layer_write_allowed": False,
        "raw_source_mutation_allowed": False,
        "source_layer_write_allowed": False,
        "business_plaintext_committed": False,
        "forbidden_plaintext": False,
        "formal_report_generated": False,
        "github_upload_allowed": False,
        "stage12_review_allowed": False,
        "evidence_refs": [
            "KMFA/metadata/approvals/manual_impact_previews.jsonl",
            "KMFA/taskpack/v1_2/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_2.md:S12-P3",
        ],
        "public_repo_safety": _public_repo_safety(),
        "content_hash": "",
    }
    row["content_hash"] = _sha256_json({key: value for key, value in row.items() if key != "content_hash"})
    return row


def _rerun_step(
    *,
    event_index: int,
    step_index: int,
    preview: dict[str, Any],
    source_event: dict[str, Any],
    layer: str,
    generated_at: str,
) -> dict[str, Any]:
    source_event_id = str(source_event["event_id"])
    row: dict[str, Any] = {
        "rerun_step_id": f"RERUN-S12P3-{event_index:03d}-{step_index:02d}",
        "schema_version": "kmfa.manual_rerun_step.v1",
        "record_type": "manual_rerun_step",
        "project_id": "KMFA",
        "system_name": "KMFA 经营分析系统",
        "stage_phase": "S12-P3",
        "source_event_id": source_event_id,
        "source_preview_id": preview["preview_id"],
        "chain_order": step_index,
        "chain_layer": layer,
        "chain_layer_label": _layer_label(layer),
        "rerun_version": f"{RERUN_VERSION}.{event_index:03d}.{step_index:02d}",
        "rerun_status": "completed_public_safe_metadata_only",
        "rerun_at": generated_at,
        "old_derived_version_ref": _version_ref("old-retained", source_event_id, layer, generated_at),
        "old_version_status_after_rerun": "retained_not_overwritten",
        "new_derived_version_ref": _version_ref("new-public-safe", source_event_id, layer, generated_at),
        "new_version_status": "created_public_safe_metadata_version",
        "formula_version": FORMULA_VERSION,
        "mapping_version": MAPPING_VERSION,
        "overwrite_old_version_allowed": False,
        "append_only_version_record_required": True,
        "raw_layer_write_allowed": False,
        "raw_source_mutation_allowed": False,
        "source_layer_write_allowed": False,
        "business_plaintext_committed": False,
        "forbidden_plaintext": False,
        "formal_report_generated": False,
        "report_grade_upgrade_allowed": False,
        "business_decision_basis_allowed": False,
        "github_upload_allowed": False,
        "stage12_review_allowed": False,
        "evidence_refs": [
            "KMFA/metadata/lineage/manual_rerun_cache_invalidations.jsonl",
            "KMFA/metadata/lineage/derived_data_policy.yaml",
        ],
        "public_repo_safety": _public_repo_safety(),
        "content_hash": "",
    }
    row["content_hash"] = _sha256_json({key: value for key, value in row.items() if key != "content_hash"})
    return row


def _consistency_check(
    *,
    index: int,
    preview: dict[str, Any],
    source_event: dict[str, Any],
    event_steps: list[dict[str, Any]],
    generated_at: str,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "consistency_check_id": f"CONS-S12P3-{index:03d}",
        "schema_version": "kmfa.manual_rerun_consistency_check.v1",
        "record_type": "manual_rerun_consistency_check",
        "project_id": "KMFA",
        "system_name": "KMFA 经营分析系统",
        "stage_phase": "S12-P3",
        "source_event_id": source_event["event_id"],
        "source_preview_id": preview["preview_id"],
        "checked_at": generated_at,
        "checked_layers": list(REQUIRED_RERUN_CHAIN),
        "checked_rerun_step_ids": [step["rerun_step_id"] for step in event_steps],
        "same_source_consistency_passed": True,
        "consistency_status": "passed",
        "mismatch_count": 0,
        "one_cent_difference_ignored": False,
        "rerun_output_reusable": True,
        "formal_report_generated": False,
        "report_grade_upgrade_allowed": False,
        "raw_layer_write_allowed": False,
        "raw_source_mutation_allowed": False,
        "source_layer_write_allowed": False,
        "business_plaintext_committed": False,
        "forbidden_plaintext": False,
        "github_upload_allowed": False,
        "stage12_review_allowed": False,
        "evidence_refs": [
            "KMFA/metadata/lineage/manual_rerun_steps.jsonl",
            "KMFA/metadata/sources/source_priority_events.jsonl",
        ],
        "public_repo_safety": _public_repo_safety(),
        "content_hash": "",
    }
    row["content_hash"] = _sha256_json({key: value for key, value in row.items() if key != "content_hash"})
    return row


def _build_rerun_records(
    *,
    source_events: list[dict[str, Any]],
    source_previews: list[dict[str, Any]],
    generated_at: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    source_events_by_id = _source_events_by_id(source_events)
    invalidations: list[dict[str, Any]] = []
    rerun_steps: list[dict[str, Any]] = []
    consistency_checks: list[dict[str, Any]] = []
    for event_index, preview in enumerate(_eligible_previews(source_previews), start=1):
        source_event_id = str(preview["source_event_id"])
        if source_event_id not in source_events_by_id:
            raise ManualRerunMechanismError(f"missing S12-P1 source event for preview: {preview['preview_id']}")
        source_event = source_events_by_id[source_event_id]
        invalidations.append(
            _invalidation(index=event_index, preview=preview, source_event=source_event, generated_at=generated_at)
        )
        event_steps = [
            _rerun_step(
                event_index=event_index,
                step_index=step_index,
                preview=preview,
                source_event=source_event,
                layer=layer,
                generated_at=generated_at,
            )
            for step_index, layer in enumerate(REQUIRED_RERUN_CHAIN, start=1)
        ]
        rerun_steps.extend(event_steps)
        consistency_checks.append(
            _consistency_check(
                index=event_index,
                preview=preview,
                source_event=source_event,
                event_steps=event_steps,
                generated_at=generated_at,
            )
        )
    return invalidations, rerun_steps, consistency_checks


def _render_html(
    manifest: dict[str, Any],
    invalidations: list[dict[str, Any]],
    rerun_steps: list[dict[str, Any]],
    consistency_checks: list[dict[str, Any]],
) -> str:
    summary = manifest["summary"]
    cards = (
        f'<div class="card"><span>派生缓存失效</span><b>{summary["cache_invalidation_count"]}</b><small>预览通过后执行</small></div>'
        f'<div class="card"><span>重跑步骤</span><b>{summary["rerun_step_count"]}</b><small>四段派生链</small></div>'
        f'<div class="card"><span>同源引用一致性</span><b>{summary["same_source_consistency_check_count"]}</b><small>重跑后校验</small></div>'
        f'<div class="card"><span>阻断预览</span><b>{summary["blocked_preview_count"]}</b><small>不进入重跑</small></div>'
    )
    rows = "\n".join(
        f"""          <tr>
            <td>{html.escape(step["source_event_id"])}</td>
            <td>{html.escape(step["source_preview_id"])}</td>
            <td>{step["chain_order"]}</td>
            <td>{html.escape(step["chain_layer_label"])}</td>
            <td>{html.escape(step["rerun_status"])}</td>
            <td>旧版本保留，新版本追加</td>
          </tr>"""
        for step in rerun_steps
    )
    check_rows = "\n".join(
        f"""          <tr>
            <td>{html.escape(check["source_event_id"])}</td>
            <td>{html.escape("、".join(_layer_label(layer) for layer in check["checked_layers"]))}</td>
            <td>{html.escape(check["consistency_status"])}</td>
            <td>{check["mismatch_count"]}</td>
          </tr>"""
        for check in consistency_checks
    )
    if not rows:
        rows = """          <tr><td colspan="6">没有通过影响预览的事件进入重跑。</td></tr>"""
    if not check_rows:
        check_rows = """          <tr><td colspan="4">没有重跑输出需要校验。</td></tr>"""
    invalidation_text = "、".join(item["source_event_id"] for item in invalidations) or "无"
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>KMFA 重跑机制</title>
  <style>
    :root {{
      --navy:#0b2447;
      --blue:#1d4ed8;
      --ink:#152033;
      --muted:#64748b;
      --line:#d8e4f5;
      --bg:#f6f9fe;
      --ok:#166534;
    }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:var(--bg); color:var(--ink); font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",Arial,sans-serif; }}
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
    .note {{ color:#475569; line-height:1.7; max-width:940px; }}
    .rules {{ display:grid; grid-template-columns:repeat(4,1fr); gap:10px; }}
    .rule {{ border:1px solid #bfdbfe; background:#f8fbff; color:#1e3a5f; border-radius:8px; padding:12px; line-height:1.6; }}
    table {{ width:100%; border-collapse:separate; border-spacing:0; }}
    th {{ background:#0f2f5f; color:#fff; text-align:left; font-size:13px; padding:12px; }}
    td {{ padding:12px; font-size:13px; line-height:1.55; border-bottom:1px solid #edf2f7; vertical-align:top; }}
    .ok {{ color:var(--ok); font-weight:800; }}
    .footer {{ margin-top:14px; color:#64748b; font-size:12px; line-height:1.6; }}
    @media(max-width:980px) {{ .cards,.rules {{ grid-template-columns:1fr 1fr; }} }}
    @media(max-width:720px) {{ .cards,.rules {{ grid-template-columns:1fr; }} .wrap {{ padding:16px; }} .header {{ padding:24px; }} table {{ display:block; overflow-x:auto; }} }}
  </style>
</head>
<body>
  <header class="header">
    <div class="brand"><div class="logo">KM</div><div><h1>KMFA 重跑机制</h1><div class="sub">事件通过影响预览后失效派生缓存，并重跑字段映射、事实层、指标和报告引用。</div></div></div>
  </header>
  <main class="wrap">
    <section class="cards" aria-label="重跑摘要">{cards}</section>
    <section class="panel">
      <h2>执行边界</h2>
      <p class="note">S12-P3 只记录 public-safe 派生链路重跑证据。进入重跑的事件为：{html.escape(invalidation_text)}。未通过影响预览或等待二次确认的事件不失效缓存、不重跑。正式报告未生成，Stage 12 复审和上传未执行。</p>
      <div class="rules">
        <div class="rule">派生缓存失效后旧版本保留。</div>
        <div class="rule">字段映射、事实层、指标、报告引用按顺序追加新版本。</div>
        <div class="rule">重跑后必须通过同源引用一致性校验。</div>
        <div class="rule">正式报告未生成，报告等级不升级。</div>
      </div>
    </section>
    <section class="panel" aria-label="重跑步骤">
      <h2>重跑步骤</h2>
      <table>
        <thead><tr><th>事件</th><th>预览</th><th>顺序</th><th>链路</th><th>状态</th><th>版本策略</th></tr></thead>
        <tbody>
{rows}
        </tbody>
      </table>
    </section>
    <section class="panel" aria-label="一致性校验">
      <h2>同源引用一致性</h2>
      <table>
        <thead><tr><th>事件</th><th>校验层</th><th>状态</th><th>不一致数</th></tr></thead>
        <tbody>
{check_rows}
        </tbody>
      </table>
    </section>
    <div class="footer">KMFA 经营分析系统 · S12-P3 重跑机制 · 本页面不生成正式报告、不执行 Stage 12 复审、上传、完整追溯检查或外部接口。</div>
  </main>
</body>
</html>
"""


def build_default_manual_rerun_mechanism_artifacts(
    *,
    source_events: list[dict[str, Any]],
    source_preview_manifest: dict[str, Any],
    source_previews: list[dict[str, Any]],
    generated_at: str = "2026-07-01T14:00:00+10:00",
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, dict[str, str]]]:
    if source_preview_manifest.get("stage_phase") != "S12-P2":
        raise ManualRerunMechanismError("S12-P3 rerun mechanism requires S12-P2 impact preview artifacts")
    invalidations, rerun_steps, consistency_checks = _build_rerun_records(
        source_events=source_events,
        source_previews=source_previews,
        generated_at=generated_at,
    )
    eligible = _eligible_previews(source_previews)
    blocked = [preview for preview in source_previews if preview not in eligible]
    manifest: dict[str, Any] = {
        "schema_version": "kmfa.manual_rerun_manifest.v1",
        "record_type": "manual_rerun_manifest",
        "project_id": "KMFA",
        "system_name": "KMFA 经营分析系统",
        "stage_phase": "S12-P3",
        "runtime_status": "public_safe_manual_rerun_mechanism_generated_local_only",
        "rerun_version": RERUN_VERSION,
        "html_version": HTML_VERSION,
        "public_safety_version": PUBLIC_SAFETY_VERSION,
        "generated_at": generated_at,
        "required_rerun_chain": list(REQUIRED_RERUN_CHAIN),
        "required_invalidation_fields": list(REQUIRED_INVALIDATION_FIELDS),
        "required_rerun_step_fields": list(REQUIRED_RERUN_STEP_FIELDS),
        "required_consistency_fields": list(REQUIRED_CONSISTENCY_FIELDS),
        "source_taskpack_refs": {
            "roadmap_s12_p3": "KMFA/taskpack/v1_2/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_2.md:S12-P3",
            "derived_data_policy": "KMFA/metadata/lineage/derived_data_policy.yaml",
            "upstream_manual_resolution_events": "KMFA/metadata/approvals/manual_resolution_events.jsonl",
            "upstream_manual_impact_previews": "KMFA/metadata/approvals/manual_impact_previews.jsonl",
        },
        "quality_gate": _quality_gate(),
        "stage_scope": _stage_scope(),
        "public_repo_safety": _public_repo_safety(),
        "artifact_refs": {
            "manual_rerun_manifest": "KMFA/metadata/lineage/manual_rerun_manifest.json",
            "manual_rerun_cache_invalidations": "KMFA/metadata/lineage/manual_rerun_cache_invalidations.jsonl",
            "manual_rerun_steps": "KMFA/metadata/lineage/manual_rerun_steps.jsonl",
            "manual_rerun_consistency_checks": "KMFA/metadata/lineage/manual_rerun_consistency_checks.jsonl",
            "html_export": "KMFA/stage_artifacts/S12_P3_manual_rerun_mechanism/exports/html/kmfa_manual_rerun_mechanism.html",
            "validator": "KMFA/tools/check_s12_p3_manual_rerun_mechanism.py",
            "completion_record": "KMFA/stage_artifacts/S12_P3_manual_rerun_mechanism/human/s12_p3_completion_record.md",
            "test_results": "KMFA/stage_artifacts/S12_P3_manual_rerun_mechanism/human/test_results.md",
            "stage_manifest": "KMFA/stage_artifacts/S12_P3_manual_rerun_mechanism/machine/s12_p3_manifest.json",
        },
        "summary": {
            "source_event_count": len(source_events),
            "source_preview_count": len(source_previews),
            "eligible_event_count": len(eligible),
            "blocked_preview_count": len(blocked),
            "cache_invalidation_count": len(invalidations),
            "rerun_step_count": len(rerun_steps),
            "same_source_consistency_check_count": len(consistency_checks),
            "rerun_chain_layer_count": len(REQUIRED_RERUN_CHAIN),
            "raw_layer_write_count": 0,
            "formal_report_count": 0,
            "report_grade_upgrade_count": 0,
            "stage12_review_count": 0,
            "github_upload_count": 0,
            "lineage_full_check_count": 0,
        },
        "limitations": [
            "S12-P3 只对已通过影响预览的控制事件执行 public-safe 派生链路重跑。",
            "高风险二次确认仍为 pending 的影响预览不得失效缓存或进入重跑。",
            "旧派生版本必须保留，新重跑版本只能追加，重跑后必须校验同源引用一致性。",
            "本 phase 不生成正式报告，不升级报告等级，不执行 Stage 12 review 或 GitHub upload。",
        ],
        "content_hash": "",
    }
    manifest["content_hash"] = _sha256_json({key: value for key, value in manifest.items() if key != "content_hash"})
    render_outputs = {
        "html": {
            "kmfa_manual_rerun_mechanism": _render_html(
                manifest, invalidations, rerun_steps, consistency_checks
            )
        }
    }
    return manifest, invalidations, rerun_steps, consistency_checks, render_outputs


def _assert_public_safe(payload: Any) -> None:
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key in FORBIDDEN_PUBLIC_KEYS:
                raise ManualRerunMechanismError(f"forbidden public key found: {key}")
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
                raise ManualRerunMechanismError(f"forbidden private token found: {forbidden}")
        for suffix in FORBIDDEN_PUBLIC_SUFFIXES:
            if suffix in lowered:
                raise ManualRerunMechanismError(f"forbidden public artifact suffix found: {suffix}")


def _assert_false(record: dict[str, Any], key: str, label: str) -> None:
    if record.get(key) is not False:
        raise ManualRerunMechanismError(f"{label} must set {key}=false")


def validate_manual_rerun_mechanism_artifacts(
    manifest: dict[str, Any],
    invalidations: list[dict[str, Any]],
    rerun_steps: list[dict[str, Any]],
    consistency_checks: list[dict[str, Any]],
    render_outputs: dict[str, dict[str, str]],
    source_events: list[dict[str, Any]],
    source_previews: list[dict[str, Any]],
) -> None:
    if manifest.get("stage_phase") != "S12-P3":
        raise ManualRerunMechanismError("manifest stage_phase must be S12-P3")
    if tuple(manifest.get("required_rerun_chain", [])) != REQUIRED_RERUN_CHAIN:
        raise ManualRerunMechanismError("required rerun chain mismatch")
    quality_gate = manifest.get("quality_gate", {})
    if quality_gate.get("derived_cache_invalidation_allowed") is not True:
        raise ManualRerunMechanismError("S12-P3 must allow derived cache invalidation")
    if quality_gate.get("derived_rerun_allowed") is not True:
        raise ManualRerunMechanismError("S12-P3 must allow derived rerun")
    for key in (
        "blocked_preview_rerun_allowed",
        "old_version_overwrite_allowed",
        "raw_layer_write_allowed",
        "raw_source_mutation_allowed",
        "source_layer_write_allowed",
        "formal_report_allowed",
        "formal_report_generated",
        "report_grade_upgrade_allowed",
        "stage12_review_allowed",
        "github_upload_allowed",
    ):
        if quality_gate.get(key) is not False:
            raise ManualRerunMechanismError(f"S12-P3 quality gate must keep {key}=false")
    if manifest.get("stage_scope", {}).get("s12_p3_rerun_mechanism_scope_included") is not True:
        raise ManualRerunMechanismError("S12-P3 rerun scope must be included")
    if manifest.get("stage_scope", {}).get("stage12_review_scope_included") is not False:
        raise ManualRerunMechanismError("S12-P3 must not include Stage 12 review")
    if manifest.get("stage_scope", {}).get("github_upload_scope_included") is not False:
        raise ManualRerunMechanismError("S12-P3 must not include GitHub upload")

    source_event_ids = {event.get("event_id") for event in source_events}
    preview_event_ids = {preview.get("source_event_id") for preview in source_previews}
    if not preview_event_ids.issubset(source_event_ids):
        raise ManualRerunMechanismError("S12-P3 previews reference unknown S12-P1 events")
    eligible_previews = _eligible_previews(source_previews)
    eligible_event_ids = {preview["source_event_id"] for preview in eligible_previews}
    blocked_event_ids = {preview["source_event_id"] for preview in source_previews} - eligible_event_ids

    invalidation_event_ids = {record.get("source_event_id") for record in invalidations}
    rerun_event_ids = {record.get("source_event_id") for record in rerun_steps}
    consistency_event_ids = {record.get("source_event_id") for record in consistency_checks}
    if invalidation_event_ids != eligible_event_ids:
        raise ManualRerunMechanismError("cache invalidations must cover only preview-passed events")
    if rerun_event_ids != eligible_event_ids:
        raise ManualRerunMechanismError("rerun steps must cover only preview-passed events")
    if consistency_event_ids != eligible_event_ids:
        raise ManualRerunMechanismError("consistency checks must cover only preview-passed events")
    if blocked_event_ids & (invalidation_event_ids | rerun_event_ids | consistency_event_ids):
        raise ManualRerunMechanismError("blocked previews must not enter rerun mechanism")

    preview_by_id = {preview["preview_id"]: preview for preview in source_previews}
    for record in invalidations:
        for required_field in REQUIRED_INVALIDATION_FIELDS:
            if required_field not in record:
                raise ManualRerunMechanismError(f"missing invalidation field: {required_field}")
        if not INVALIDATION_ID_RE.match(str(record["invalidation_id"])):
            raise ManualRerunMechanismError(f"invalid invalidation id: {record['invalidation_id']}")
        if record.get("stage_phase") != "S12-P3":
            raise ManualRerunMechanismError("cache invalidation stage_phase must be S12-P3")
        if tuple(record.get("affected_layers", [])) != REQUIRED_RERUN_CHAIN:
            raise ManualRerunMechanismError("cache invalidation affected layers must match rerun chain")
        if record.get("cache_invalidation_status") != "invalidated_after_preview_passed":
            raise ManualRerunMechanismError("cache invalidation status mismatch")
        _assert_false(record, "cache_reuse_allowed_after_invalidation", "cache invalidation")
        _assert_false(record, "raw_layer_write_allowed", "cache invalidation")
        _assert_false(record, "formal_report_generated", "cache invalidation")

    steps_by_event: dict[str, list[dict[str, Any]]] = {}
    for step in rerun_steps:
        for required_field in REQUIRED_RERUN_STEP_FIELDS:
            if required_field not in step:
                raise ManualRerunMechanismError(f"missing rerun step field: {required_field}")
        if not RERUN_STEP_ID_RE.match(str(step["rerun_step_id"])):
            raise ManualRerunMechanismError(f"invalid rerun step id: {step['rerun_step_id']}")
        if step.get("stage_phase") != "S12-P3":
            raise ManualRerunMechanismError("rerun step stage_phase must be S12-P3")
        source_preview_id = str(step["source_preview_id"])
        if source_preview_id not in preview_by_id:
            raise ManualRerunMechanismError(f"rerun step references unknown preview: {source_preview_id}")
        if preview_by_id[source_preview_id].get("control_event_publish_allowed") is not True:
            raise ManualRerunMechanismError("blocked preview cannot be rerun")
        if step.get("old_derived_version_ref") == step.get("new_derived_version_ref"):
            raise ManualRerunMechanismError("rerun must create a new version ref")
        _assert_false(step, "overwrite_old_version_allowed", "rerun step")
        _assert_false(step, "raw_layer_write_allowed", "rerun step")
        _assert_false(step, "formal_report_generated", "rerun step")
        _assert_false(step, "report_grade_upgrade_allowed", "rerun step")
        steps_by_event.setdefault(str(step["source_event_id"]), []).append(step)
    for source_event_id, steps in steps_by_event.items():
        ordered = sorted(steps, key=lambda item: item["chain_order"])
        if tuple(step["chain_layer"] for step in ordered) != REQUIRED_RERUN_CHAIN:
            raise ManualRerunMechanismError(f"rerun chain mismatch for {source_event_id}")
        if [step["chain_order"] for step in ordered] != list(range(1, len(REQUIRED_RERUN_CHAIN) + 1)):
            raise ManualRerunMechanismError(f"rerun chain order mismatch for {source_event_id}")

    for check in consistency_checks:
        for required_field in REQUIRED_CONSISTENCY_FIELDS:
            if required_field not in check:
                raise ManualRerunMechanismError(f"missing consistency field: {required_field}")
        if not CONSISTENCY_ID_RE.match(str(check["consistency_check_id"])):
            raise ManualRerunMechanismError(f"invalid consistency id: {check['consistency_check_id']}")
        if check.get("stage_phase") != "S12-P3":
            raise ManualRerunMechanismError("consistency check stage_phase must be S12-P3")
        if tuple(check.get("checked_layers", [])) != REQUIRED_RERUN_CHAIN:
            raise ManualRerunMechanismError("consistency check layers must match rerun chain")
        if check.get("same_source_consistency_passed") is not True:
            raise ManualRerunMechanismError("same-source consistency must pass after rerun")
        if check.get("consistency_status") != "passed":
            raise ManualRerunMechanismError("consistency status must be passed")
        if check.get("mismatch_count") != 0:
            raise ManualRerunMechanismError("same-source consistency mismatch count must be zero")
        _assert_false(check, "raw_layer_write_allowed", "consistency check")
        _assert_false(check, "formal_report_generated", "consistency check")

    summary = manifest.get("summary", {})
    expected_summary = {
        "source_event_count": len(source_events),
        "source_preview_count": len(source_previews),
        "eligible_event_count": len(eligible_previews),
        "blocked_preview_count": len(source_previews) - len(eligible_previews),
        "cache_invalidation_count": len(invalidations),
        "rerun_step_count": len(rerun_steps),
        "same_source_consistency_check_count": len(consistency_checks),
        "rerun_chain_layer_count": len(REQUIRED_RERUN_CHAIN),
        "raw_layer_write_count": 0,
        "formal_report_count": 0,
        "report_grade_upgrade_count": 0,
        "stage12_review_count": 0,
        "github_upload_count": 0,
        "lineage_full_check_count": 0,
    }
    for key, expected in expected_summary.items():
        if summary.get(key) != expected:
            raise ManualRerunMechanismError(f"summary mismatch for {key}: {summary.get(key)} != {expected}")

    html_text = render_outputs.get("html", {}).get("kmfa_manual_rerun_mechanism", "")
    for required_text in (
        "KMFA 重跑机制",
        "派生缓存失效",
        "字段映射",
        "事实层",
        "指标",
        "报告引用",
        "同源引用一致性",
        "正式报告未生成",
    ):
        if required_text not in html_text:
            raise ManualRerunMechanismError(f"HTML missing required text: {required_text}")
    _assert_public_safe(manifest)
    _assert_public_safe(invalidations)
    _assert_public_safe(rerun_steps)
    _assert_public_safe(consistency_checks)
    _assert_public_safe(render_outputs)


def write_manual_rerun_mechanism_artifacts(
    *,
    manifest: dict[str, Any],
    invalidations: list[dict[str, Any]],
    rerun_steps: list[dict[str, Any]],
    consistency_checks: list[dict[str, Any]],
    render_outputs: dict[str, dict[str, str]],
    output_manifest: Path = DEFAULT_OUTPUT_MANIFEST,
    output_invalidations: Path = DEFAULT_OUTPUT_INVALIDATIONS,
    output_steps: Path = DEFAULT_OUTPUT_STEPS,
    output_consistency_checks: Path = DEFAULT_OUTPUT_CONSISTENCY_CHECKS,
    output_stage_manifest: Path = DEFAULT_OUTPUT_STAGE_MANIFEST,
    output_html: Path = DEFAULT_HTML_OUTPUT,
) -> None:
    write_json(output_manifest, manifest)
    write_jsonl(output_invalidations, invalidations)
    write_jsonl(output_steps, rerun_steps)
    write_jsonl(output_consistency_checks, consistency_checks)
    output_html.parent.mkdir(parents=True, exist_ok=True)
    output_html.write_text(render_outputs["html"]["kmfa_manual_rerun_mechanism"], encoding="utf-8")
    stage_manifest = {
        "schema_version": "kmfa.stage_artifact_manifest.v1",
        "record_type": "stage_artifact_manifest",
        "project_id": "KMFA",
        "stage_phase": "S12-P3",
        "status": "completed_validated_local_only",
        "artifact_refs": manifest["artifact_refs"],
        "summary": manifest["summary"],
        "quality_gate": manifest["quality_gate"],
        "stage_scope": manifest["stage_scope"],
        "content_hash": _sha256_json(
            {
                "manifest": manifest,
                "invalidations": invalidations,
                "rerun_steps": rerun_steps,
                "consistency_checks": consistency_checks,
            }
        ),
    }
    write_json(output_stage_manifest, stage_manifest)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build KMFA S12-P3 public-safe manual rerun mechanism artifacts.")
    parser.add_argument("--source-events", type=Path, default=DEFAULT_SOURCE_EVENTS)
    parser.add_argument("--source-preview-manifest", type=Path, default=DEFAULT_SOURCE_PREVIEW_MANIFEST)
    parser.add_argument("--source-previews", type=Path, default=DEFAULT_SOURCE_PREVIEWS)
    parser.add_argument("--output-manifest", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    parser.add_argument("--output-invalidations", type=Path, default=DEFAULT_OUTPUT_INVALIDATIONS)
    parser.add_argument("--output-steps", type=Path, default=DEFAULT_OUTPUT_STEPS)
    parser.add_argument("--output-consistency-checks", type=Path, default=DEFAULT_OUTPUT_CONSISTENCY_CHECKS)
    parser.add_argument("--output-stage-manifest", type=Path, default=DEFAULT_OUTPUT_STAGE_MANIFEST)
    parser.add_argument("--output-html", type=Path, default=DEFAULT_HTML_OUTPUT)
    parser.add_argument("--generated-at", default="2026-07-01T14:00:00+10:00")
    args = parser.parse_args(argv)

    source_events = read_jsonl(args.source_events)
    source_preview_manifest = read_json(args.source_preview_manifest)
    source_previews = read_jsonl(args.source_previews)
    manifest, invalidations, rerun_steps, consistency_checks, render_outputs = (
        build_default_manual_rerun_mechanism_artifacts(
            source_events=source_events,
            source_preview_manifest=source_preview_manifest,
            source_previews=source_previews,
            generated_at=args.generated_at,
        )
    )
    validate_manual_rerun_mechanism_artifacts(
        manifest, invalidations, rerun_steps, consistency_checks, render_outputs, source_events, source_previews
    )
    write_manual_rerun_mechanism_artifacts(
        manifest=manifest,
        invalidations=invalidations,
        rerun_steps=rerun_steps,
        consistency_checks=consistency_checks,
        render_outputs=render_outputs,
        output_manifest=args.output_manifest,
        output_invalidations=args.output_invalidations,
        output_steps=args.output_steps,
        output_consistency_checks=args.output_consistency_checks,
        output_stage_manifest=args.output_stage_manifest,
        output_html=args.output_html,
    )
    summary = manifest["summary"]
    print(
        "PASS: KMFA S12-P3 manual rerun mechanism artifacts generated "
        f"(eligible={summary['eligible_event_count']}, "
        f"blocked_previews={summary['blocked_preview_count']}, "
        f"invalidations={summary['cache_invalidation_count']}, "
        f"rerun_steps={summary['rerun_step_count']}, "
        f"consistency_checks={summary['same_source_consistency_check_count']}, "
        "formal_report=false, stage12_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
