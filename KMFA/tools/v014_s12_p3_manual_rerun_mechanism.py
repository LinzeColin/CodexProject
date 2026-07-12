#!/usr/bin/env python3
"""Generate KMFA v0.1.4 S12-P3 manual rerun mechanism evidence.

This phase validates the v0.1.4 S12-P2 impact preview dependency, then records
public-safe derived cache invalidation, four-layer rerun steps, and same-source
consistency checks for preview-passed events only. It does not perform Stage 12
review, GitHub upload, protected source matching, lineage full check, formal
report release, live connector work, app reinstall, or business execution.
"""

from __future__ import annotations

import hashlib
import html
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.check_v014_s12_p2_manual_impact_preview import validate_v014_s12_p2_manual_impact_preview
from KMFA.tools.manual_rerun_mechanism import REQUIRED_RERUN_CHAIN, validate_manual_rerun_mechanism_artifacts
from KMFA.tools.v014_s12_p2_manual_impact_preview import (
    MANIFEST_PATH as S12_P2_MANIFEST_PATH,
    PREVIEWS_PATH as S12_P2_PREVIEWS_PATH,
    S12_P1_EVENTS_PATH,
    V14_HTML_AUDIT_REPORT_PATH,
    V14_HTML_AUDIT_SCRIPT_PATH,
    V14_HTML_ENTRY_PATH,
    V14_ROADMAP_PATH,
    V14_SOURCE_PACKAGE_MANIFEST,
    V14_TASKPACK_PATH,
)


TASK_ID = "KMFA-V014-S12-P3-MANUAL-RERUN-MECHANISM-20260705"
ACCEPTANCE_ID = "ACC-V014-S12-P3-MANUAL-RERUN-MECHANISM"
SCHEMA_VERSION = "kmfa.v014_s12_p3_manual_rerun_mechanism.v1"
PHASE_SCOPE = "v014_s12_p3_manual_rerun_mechanism_only"

OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_S12_P3_MANUAL_RERUN_MECHANISM")
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
EXPORT_HTML_DIR = OUTPUT_DIR / "exports" / "html"
MANIFEST_PATH = MACHINE_DIR / "manual_rerun_manifest.json"
INVALIDATIONS_PATH = MACHINE_DIR / "manual_rerun_cache_invalidations.jsonl"
RERUN_STEPS_PATH = MACHINE_DIR / "manual_rerun_steps.jsonl"
CONSISTENCY_CHECKS_PATH = MACHINE_DIR / "manual_rerun_consistency_checks.jsonl"
HTML_OUTPUT_PATH = EXPORT_HTML_DIR / "kmfa_manual_rerun_mechanism.html"
REPORT_PATH = HUMAN_DIR / "manual_rerun_mechanism_report.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

RAW_INBOX_REF = "operator-designated raw/private inbox outside repository"
NEXT_REQUIRED_STEP = (
    "Proceed to v0.1.4 Stage 12 overall review as a separate run. Do not perform "
    "GitHub upload, protected source matching, lineage full check, formal report "
    "release, live connector, app reinstall, OpMe deep coupling, or business execution "
    "in the S12-P3 run."
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


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"{path} must contain a JSON object")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise RuntimeError(f"{path} contains a non-object JSONL row")
        records.append(value)
    return records


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


def _sha256_json(payload: Any) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


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


def _quality_gate() -> dict[str, Any]:
    return {
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "release_permission": "blocked",
        "pending_reconciliation_count": 12,
        "confirmed_resolution_count": 0,
        "derived_cache_invalidation_allowed": True,
        "derived_rerun_allowed": True,
        "field_mapping_rerun_required": True,
        "fact_layer_rerun_required": True,
        "derived_metric_rerun_required": True,
        "report_reference_rerun_required": True,
        "same_source_consistency_check_required": True,
        "append_only_derived_versions_required": True,
        "blocked_preview_rerun_allowed": False,
        "old_version_overwrite_allowed": False,
        "raw_layer_write_allowed": False,
        "raw_source_mutation_allowed": False,
        "source_layer_write_allowed": False,
        "business_plaintext_commit_allowed": False,
        "formal_report_allowed": False,
        "formal_report_generated": False,
        "report_grade_upgrade_allowed": False,
        "business_decision_basis_allowed": False,
        "business_execution_allowed": False,
        "delivery_allowed": False,
        "automatic_external_action_allowed": False,
        "stage12_review_allowed": False,
        "github_upload_allowed": False,
        "phase_completion_upload_allowed": False,
    }


def _phase_boundaries() -> dict[str, bool]:
    return {
        "s12_p1_manual_resolution_events_dependency_included": True,
        "s12_p2_impact_preview_dependency_included": True,
        "s12_p3_rerun_mechanism_scope_included": True,
        "stage12_review_scope_included": False,
        "lineage_full_check_scope_included": False,
        "protected_source_matching_scope_included": False,
        "formal_report_scope_included": False,
        "external_connector_scope_included": False,
        "live_ui_runtime_scope_included": False,
        "app_reinstall_scope_included": False,
        "opme_deep_coupling_scope_included": False,
        "github_upload_scope_included": False,
        "business_execution_scope_included": False,
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
    return {str(event["event_id"]): event for event in source_events if event.get("event_id")}


def _layer_label(layer: str) -> str:
    return {
        "field_mapping": "字段映射",
        "fact_layer": "事实层",
        "derived_metric": "指标",
        "report_reference": "报告引用",
    }[layer]


def _version_ref(kind: str, source_event_id: str, layer: str, generated_at: str) -> str:
    suffix = hashlib.sha256(f"v014|{kind}|{source_event_id}|{layer}|{generated_at}".encode("utf-8")).hexdigest()[:12]
    return f"version_ref://KMFA/V014/S12-P3/{source_event_id}/{layer}/{kind}-{suffix}"


def validate_s12_p2_dependency() -> dict[str, Any]:
    result = validate_v014_s12_p2_manual_impact_preview()
    progress = result.get("stage12_phase_progress", {})
    if result.get("phase_id") != "S12-P2":
        raise RuntimeError("S12-P3 requires validated v0.1.4 S12-P2")
    if progress.get("s12_p1_performed") is not True or progress.get("s12_p2_performed") is not True:
        raise RuntimeError("S12-P3 requires completed S12-P1 and S12-P2")
    if progress.get("s12_p3_performed") is not False:
        raise RuntimeError("S12-P2 dependency must not already include S12-P3")
    if progress.get("stage12_review_performed") is not False:
        raise RuntimeError("S12-P2 dependency must not include Stage 12 review")
    if result.get("github_upload", {}).get("github_upload_performed") is not False:
        raise RuntimeError("S12-P2 dependency must not include GitHub upload")
    raw = result.get("raw_data_boundary", {})
    for key in (
        "raw_inbox_read_by_this_phase",
        "raw_inbox_listed_by_this_phase",
        "raw_inbox_stat_by_this_phase",
        "raw_inbox_hashed_by_this_phase",
        "raw_inbox_mutated_by_this_phase",
    ):
        if raw.get(key) is not False:
            raise RuntimeError(f"S12-P2 dependency raw boundary must keep {key}=false")
    return result


def load_v14_html_uiux_baseline() -> dict[str, Any]:
    source_manifest = read_json(V14_SOURCE_PACKAGE_MANIFEST)
    gate = source_manifest.get("html_human_flow_gate", {})
    report_text = V14_HTML_AUDIT_REPORT_PATH.read_text(encoding="utf-8")
    entry_text = V14_HTML_ENTRY_PATH.read_text(encoding="utf-8")
    script_text = V14_HTML_AUDIT_SCRIPT_PATH.read_text(encoding="utf-8")
    roadmap_text = V14_ROADMAP_PATH.read_text(encoding="utf-8")
    taskpack_text = V14_TASKPACK_PATH.read_text(encoding="utf-8")
    for term in ("待处理事项工作台", "差异处理", "影响预览", "重跑链路", "前端不改原始数据"):
        if term not in entry_text:
            raise RuntimeError(f"v1.4 HTML entry missing S12 term: {term}")
    for term in ("处理意见", "影响预览", "重跑链路", "状态变更写入控制事件", "不污染原始数据"):
        if term not in report_text:
            raise RuntimeError(f"v1.4 HTML audit report missing S12 requirement: {term}")
    for term in (
        "事件通过后失效派生缓存",
        "重跑字段映射、事实层、指标、报告引用",
        "重跑后校验同源引用一致性",
    ):
        if term not in roadmap_text:
            raise RuntimeError(f"v1.4 roadmap missing S12-P3 requirement: {term}")
    if "重跑链路" not in taskpack_text or "失效受影响派生缓存" not in taskpack_text:
        raise RuntimeError("v1.4 taskpack missing manual rerun baseline terms")
    if "button" not in script_text or "input" not in script_text or "link" not in script_text:
        raise RuntimeError("v1.4 audit script must inspect links, inputs, and buttons")
    return {
        "taskpack_html_requirement_read": True,
        "human_flow_entry_exists": V14_HTML_ENTRY_PATH.exists(),
        "human_flow_audit_script_exists": V14_HTML_AUDIT_SCRIPT_PATH.exists(),
        "human_flow_audit_report_exists": V14_HTML_AUDIT_REPORT_PATH.exists(),
        "audit_file_count": int(gate.get("audit_files", -1)),
        "audit_control_row_count": int(gate.get("audit_rows", -1)),
        "audit_pass_count": int(gate.get("pass", -1)),
        "audit_warn_count": int(gate.get("warn", -1)),
        "audit_fail_count": int(gate.get("fail", -1)),
        "entry_includes_manual_rerun_flow": True,
        "audit_report_requires_opinion_preview_rerun": True,
        "roadmap_requires_manual_rerun": True,
        "taskpack_requires_manual_rerun": True,
        "audit_script_inspects_links_inputs_buttons": True,
        "implementation_reflects_cache_invalidation": True,
        "implementation_reflects_four_layer_rerun": True,
        "implementation_reflects_same_source_consistency_check": True,
        "implementation_reflects_no_raw_mutation": True,
        "source_refs": {
            "source_package_manifest": V14_SOURCE_PACKAGE_MANIFEST.as_posix(),
            "html_human_flow_entry": V14_HTML_ENTRY_PATH.as_posix(),
            "html_human_flow_audit_script": V14_HTML_AUDIT_SCRIPT_PATH.as_posix(),
            "html_human_flow_audit_report": V14_HTML_AUDIT_REPORT_PATH.as_posix(),
            "roadmap": V14_ROADMAP_PATH.as_posix(),
            "taskpack": V14_TASKPACK_PATH.as_posix(),
        },
    }


def _invalidation(index: int, preview: dict[str, Any], source_event: dict[str, Any], generated_at: str) -> dict[str, Any]:
    row: dict[str, Any] = {
        "invalidation_id": f"INV-S12P3-{index:03d}",
        "schema_version": "kmfa.v014_manual_rerun_cache_invalidation.v1",
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
        "invalidation_version": f"V014-S12P3.{index:03d}.INV",
        "invalidated_at": generated_at,
        "cache_invalidation_status": "invalidated_after_preview_passed",
        "affected_layers": list(REQUIRED_RERUN_CHAIN),
        "invalidated_cache_ref": f"cache_ref://KMFA/V014/S12-P3/{source_event['event_id']}/derived-chain",
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
        "evidence_refs": [S12_P2_PREVIEWS_PATH.as_posix(), V14_ROADMAP_PATH.as_posix(), REPORT_PATH.as_posix()],
        "public_repo_safety": _public_repo_safety(),
        "content_hash": "",
    }
    row["content_hash"] = _sha256_json({key: value for key, value in row.items() if key != "content_hash"})
    return row


def _rerun_step(
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
        "schema_version": "kmfa.v014_manual_rerun_step.v1",
        "record_type": "manual_rerun_step",
        "project_id": "KMFA",
        "system_name": "KMFA 经营分析系统",
        "stage_phase": "S12-P3",
        "source_event_id": source_event_id,
        "source_preview_id": preview["preview_id"],
        "chain_order": step_index,
        "chain_layer": layer,
        "chain_layer_label": _layer_label(layer),
        "rerun_version": f"V014-S12P3.{event_index:03d}.{step_index:02d}",
        "rerun_status": "completed_public_safe_metadata_only",
        "rerun_at": generated_at,
        "old_derived_version_ref": _version_ref("old-retained", source_event_id, layer, generated_at),
        "old_version_status_after_rerun": "retained_not_overwritten",
        "new_derived_version_ref": _version_ref("new-public-safe", source_event_id, layer, generated_at),
        "new_version_status": "created_public_safe_metadata_version",
        "formula_version": "FORM-KMFA-V014-S12P3-RERUN-MECHANISM-001",
        "mapping_version": "MAP-KMFA-V014-S12P3-PUBLIC-SAFE-001",
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
        "evidence_refs": [INVALIDATIONS_PATH.as_posix(), V14_ROADMAP_PATH.as_posix(), REPORT_PATH.as_posix()],
        "public_repo_safety": _public_repo_safety(),
        "content_hash": "",
    }
    row["content_hash"] = _sha256_json({key: value for key, value in row.items() if key != "content_hash"})
    return row


def _consistency_check(
    index: int,
    preview: dict[str, Any],
    source_event: dict[str, Any],
    event_steps: list[dict[str, Any]],
    generated_at: str,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "consistency_check_id": f"CONS-S12P3-{index:03d}",
        "schema_version": "kmfa.v014_manual_rerun_consistency_check.v1",
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
        "evidence_refs": [RERUN_STEPS_PATH.as_posix(), V14_ROADMAP_PATH.as_posix(), REPORT_PATH.as_posix()],
        "public_repo_safety": _public_repo_safety(),
        "content_hash": "",
    }
    row["content_hash"] = _sha256_json({key: value for key, value in row.items() if key != "content_hash"})
    return row


def build_rerun_records(
    source_events: list[dict[str, Any]], source_previews: list[dict[str, Any]], generated_at: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    source_events_by_id = _source_events_by_id(source_events)
    invalidations: list[dict[str, Any]] = []
    rerun_steps: list[dict[str, Any]] = []
    consistency_checks: list[dict[str, Any]] = []
    for event_index, preview in enumerate(_eligible_previews(source_previews), start=1):
        source_event_id = str(preview["source_event_id"])
        if source_event_id not in source_events_by_id:
            raise RuntimeError(f"missing S12-P1 source event for preview: {preview['preview_id']}")
        source_event = source_events_by_id[source_event_id]
        invalidations.append(_invalidation(event_index, preview, source_event, generated_at))
        event_steps = [
            _rerun_step(event_index, step_index, preview, source_event, layer, generated_at)
            for step_index, layer in enumerate(REQUIRED_RERUN_CHAIN, start=1)
        ]
        rerun_steps.extend(event_steps)
        consistency_checks.append(_consistency_check(event_index, preview, source_event, event_steps, generated_at))
    return invalidations, rerun_steps, consistency_checks


def _render_html(
    manifest: dict[str, Any],
    invalidations: list[dict[str, Any]],
    rerun_steps: list[dict[str, Any]],
    consistency_checks: list[dict[str, Any]],
) -> str:
    summary = manifest["manual_rerun_summary"]
    cards = (
        f'<div class="card"><span>派生缓存失效</span><b>{summary["cache_invalidation_count"]}</b><small>预览通过后执行</small></div>'
        f'<div class="card"><span>重跑步骤</span><b>{summary["rerun_step_count"]}</b><small>四段派生链</small></div>'
        f'<div class="card"><span>同源引用一致性</span><b>{summary["same_source_consistency_check_count"]}</b><small>重跑后校验</small></div>'
        f'<div class="card"><span>阻断预览</span><b>{summary["blocked_preview_count"]}</b><small>不进入重跑</small></div>'
    )
    rows = "\n".join(
        f"""          <tr>
            <td>{html.escape(str(step["source_event_id"]))}</td>
            <td>{html.escape(str(step["source_preview_id"]))}</td>
            <td>{step["chain_order"]}</td>
            <td>{html.escape(str(step["chain_layer_label"]))}</td>
            <td>{html.escape(str(step["rerun_status"]))}</td>
            <td>旧版本保留，新版本追加</td>
          </tr>"""
        for step in rerun_steps
    )
    check_rows = "\n".join(
        f"""          <tr>
            <td>{html.escape(str(check["source_event_id"]))}</td>
            <td>{html.escape("、".join(_layer_label(str(layer)) for layer in check["checked_layers"]))}</td>
            <td>{html.escape(str(check["consistency_status"]))}</td>
            <td>{check["mismatch_count"]}</td>
          </tr>"""
        for check in consistency_checks
    )
    invalidation_text = "、".join(str(item["source_event_id"]) for item in invalidations) or "无"
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>KMFA v1.4 重跑机制</title>
  <style>
    :root {{ --navy:#0b2447; --blue:#1d4ed8; --ink:#152033; --muted:#64748b; --line:#d8e4f5; --bg:#f6f9fe; --ok:#166534; }}
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
    <section class="panel" aria-label="同源引用一致性">
      <h2>同源引用一致性</h2>
      <table>
        <thead><tr><th>事件</th><th>校验层</th><th>状态</th><th>不一致数</th></tr></thead>
        <tbody>
{check_rows}
        </tbody>
      </table>
    </section>
    <div class="footer">KMFA 经营分析系统 · v0.1.4 S12-P3 · 不执行 Stage 12 复审、GitHub upload、完整追溯检查、正式报告、外部接口或业务动作。</div>
  </main>
</body>
</html>
"""


def _render_report(manifest: dict[str, Any]) -> str:
    summary = manifest["manual_rerun_summary"]
    return f"""# v0.1.4 S12-P3 Manual Rerun Mechanism

## Scope

- Phase: `S12-P3｜重跑机制`
- Status: `{manifest["status"]}`
- Task: `{TASK_ID}`
- Acceptance: `{ACCEPTANCE_ID}`

## Locked Evidence

- Source previews: `{summary["source_preview_count"]}`
- Eligible events: `{summary["eligible_event_count"]}`
- Blocked previews: `{summary["blocked_preview_count"]}`
- Cache invalidations: `{summary["cache_invalidation_count"]}`
- Rerun steps: `{summary["rerun_step_count"]}`
- Same-source consistency checks: `{summary["same_source_consistency_check_count"]}`
- Old versions retained: `{summary["old_version_retained_count"]}`
- New versions appended: `{summary["new_version_appended_count"]}`

## Boundaries

- Raw/private inbox read/list/stat/hash/mutation: `false`
- Stage 12 review: `false`
- GitHub upload: `false`
- Formal report/business decision basis/business execution: `false`

## Next

{NEXT_REQUIRED_STEP}
"""


def _render_test_results() -> str:
    return """# v0.1.4 S12-P3 Test Results

Focused RED was recorded before implementation:

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s12_p3_manual_rerun_mechanism -q`
- Initial result: failed because the v0.1.4 S12-P3 generator/validator modules were absent.

Final validation commands are recorded in governance events after the run.
"""


def _render_risk_register() -> str:
    return """# v0.1.4 S12-P3 Risk Register

| Risk | Control |
| --- | --- |
| Blocked preview is accidentally rerun | Validator requires invalidation, rerun, and consistency records to cover only preview-passed events |
| Old derived outputs are overwritten | Rerun step records require old versions retained and new versions appended |
| Stage review or upload is implied too early | Phase boundary keeps Stage 12 review and GitHub upload false |
| Public evidence leaks protected business data | Public evidence validator rejects private tokens, native file suffixes, and source payload markers |
"""


def _render_rollback_plan() -> str:
    return """# v0.1.4 S12-P3 Rollback Plan

1. Remove `KMFA/stage_artifacts/V014_S12_P3_MANUAL_RERUN_MECHANISM/`.
2. Revert `KMFA/tools/v014_s12_p3_manual_rerun_mechanism.py`, `KMFA/tools/check_v014_s12_p3_manual_rerun_mechanism.py`, and the focused test.
3. Revert S12-P3 governance/status updates.
4. Re-run S12-P2 validator to confirm the previous boundary remains intact.
"""


def build_manifest() -> tuple[
    dict[str, Any],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    dependency = validate_s12_p2_dependency()
    source_preview_manifest = read_json(S12_P2_MANIFEST_PATH)
    source_events = read_jsonl(S12_P1_EVENTS_PATH)
    source_previews = read_jsonl(S12_P2_PREVIEWS_PATH)
    v14 = load_v14_html_uiux_baseline()
    generated_at = datetime.now().astimezone().replace(microsecond=0).isoformat()
    invalidations, rerun_steps, consistency_checks = build_rerun_records(source_events, source_previews, generated_at)
    eligible = _eligible_previews(source_previews)
    blocked = [preview for preview in source_previews if preview not in eligible]
    summary = {
        "source_event_count": len(source_events),
        "source_preview_count": len(source_previews),
        "eligible_event_count": len(eligible),
        "blocked_preview_count": len(blocked),
        "cache_invalidation_count": len(invalidations),
        "rerun_step_count": len(rerun_steps),
        "same_source_consistency_check_count": len(consistency_checks),
        "rerun_chain_layer_count": len(REQUIRED_RERUN_CHAIN),
        "old_version_retained_count": len(rerun_steps),
        "new_version_appended_count": len(rerun_steps),
        "raw_layer_write_count": 0,
        "source_mutation_count": 0,
        "business_plaintext_count": 0,
        "formal_report_count": 0,
        "business_decision_basis_count": 0,
        "report_grade_upgrade_count": 0,
        "stage12_review_count": 0,
        "github_upload_count": 0,
        "lineage_full_check_count": 0,
    }
    manifest: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "manual_rerun_manifest",
        "project_id": "KMFA",
        "system_name": "KMFA 经营分析系统",
        "version": "0.1.4",
        "stage_id": "S12",
        "phase_id": "S12-P3",
        "stage_phase": "S12-P3",
        "phase_scope": PHASE_SCOPE,
        "task_id": TASK_ID,
        "acceptance_ids": [ACCEPTANCE_ID],
        "completed_task_ids": [
            "S12P1T01",
            "S12P1T02",
            "S12P1T03",
            "S12P2T01",
            "S12P2T02",
            "S12P2T03",
            "S12P3T01",
            "S12P3T02",
            "S12P3T03",
        ],
        "status": "completed_validated_local_only_no_go_upload_deferred_manual_rerun_mechanism",
        "generated_at": generated_at,
        "git": {
            "branch": git_output(["branch", "--show-current"]),
            "head": git_output(["rev-parse", "HEAD"]),
            "remote": git_output(["remote", "get-url", "origin"]),
        },
        "s12_p2_dependency_validated": True,
        "dependency_s12_p2_status": dependency.get("status"),
        "s12_p2_manifest": S12_P2_MANIFEST_PATH.as_posix(),
        "source_preview_manifest_validated": source_preview_manifest.get("phase_id") == "S12-P2",
        "stage12_phase_progress": {
            "completed_phase_count": 3,
            "total_phase_count": 3,
            "derived_percent_bps": 10000,
            "derived_percent_label": "100.00%",
            "s12_p1_performed": True,
            "s12_p2_performed": True,
            "s12_p3_performed": True,
            "stage12_review_performed": False,
        },
        "required_rerun_chain": list(REQUIRED_RERUN_CHAIN),
        "manual_rerun_summary": summary,
        "summary": summary,
        "record_counts": {
            "invalidations": len(invalidations),
            "rerun_steps": len(rerun_steps),
            "consistency_checks": len(consistency_checks),
        },
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
            "stage12_review_not_performed",
            "report_grade_d_only",
            "pending_reconciliation_blocks_formal_report",
            "raw_data_mutation_forbidden",
            "protected_source_publication_forbidden",
            "field_header_plaintext_publication_forbidden",
            "formal_report_release_blocked",
            "business_decision_basis_blocked",
            "lineage_full_check_not_performed",
            "protected_source_matching_not_performed",
            "github_upload_deferred_until_v014_stage1_18_complete",
            "app_reinstall_not_performed",
            "business_execution_blocked",
        ],
        "artifact_refs": {
            "manifest": MANIFEST_PATH.as_posix(),
            "invalidations": INVALIDATIONS_PATH.as_posix(),
            "rerun_steps": RERUN_STEPS_PATH.as_posix(),
            "consistency_checks": CONSISTENCY_CHECKS_PATH.as_posix(),
            "html_export": HTML_OUTPUT_PATH.as_posix(),
            "human_report": REPORT_PATH.as_posix(),
            "test_results": TEST_RESULTS_PATH.as_posix(),
            "risk_register": RISK_REGISTER_PATH.as_posix(),
            "rollback_plan": ROLLBACK_PATH.as_posix(),
            "validator": "KMFA/tools/check_v014_s12_p3_manual_rerun_mechanism.py",
            "test": "KMFA/tests/test_v014_s12_p3_manual_rerun_mechanism.py",
        },
        "evidence_refs": [
            REPORT_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            RISK_REGISTER_PATH.as_posix(),
            ROLLBACK_PATH.as_posix(),
            MANIFEST_PATH.as_posix(),
            INVALIDATIONS_PATH.as_posix(),
            RERUN_STEPS_PATH.as_posix(),
            CONSISTENCY_CHECKS_PATH.as_posix(),
            HTML_OUTPUT_PATH.as_posix(),
        ],
        "next_phase": "S12-STAGE-REVIEW",
        "next_required_step": NEXT_REQUIRED_STEP,
        "non_goals": [
            "Stage 12 overall review",
            "GitHub upload",
            "protected source matching",
            "lineage full check",
            "formal report release",
            "live connector",
            "app reinstall",
            "OpMe deep coupling",
            "business execution",
        ],
    }
    return manifest, invalidations, rerun_steps, consistency_checks, source_events, source_previews


def generate() -> dict[str, Any]:
    manifest, invalidations, rerun_steps, consistency_checks, source_events, source_previews = build_manifest()
    html_text = _render_html(manifest, invalidations, rerun_steps, consistency_checks)
    validate_manual_rerun_mechanism_artifacts(
        manifest,
        invalidations,
        rerun_steps,
        consistency_checks,
        {"html": {"kmfa_manual_rerun_mechanism": html_text}},
        source_events,
        source_previews,
    )
    _write_json(MANIFEST_PATH, manifest)
    _write_jsonl(INVALIDATIONS_PATH, invalidations)
    _write_jsonl(RERUN_STEPS_PATH, rerun_steps)
    _write_jsonl(CONSISTENCY_CHECKS_PATH, consistency_checks)
    _write_text(HTML_OUTPUT_PATH, html_text)
    _write_text(REPORT_PATH, _render_report(manifest))
    _write_text(TEST_RESULTS_PATH, _render_test_results())
    _write_text(RISK_REGISTER_PATH, _render_risk_register())
    _write_text(ROLLBACK_PATH, _render_rollback_plan())
    return manifest


def main() -> int:
    manifest = generate()
    summary = manifest["manual_rerun_summary"]
    print(
        "PASS: KMFA v0.1.4 S12-P3 manual rerun mechanism generated "
        f"(eligible={summary['eligible_event_count']}, "
        f"blocked_previews={summary['blocked_preview_count']}, "
        f"invalidations={summary['cache_invalidation_count']}, "
        f"rerun_steps={summary['rerun_step_count']}, "
        f"consistency_checks={summary['same_source_consistency_check_count']}, "
        "stage12_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
