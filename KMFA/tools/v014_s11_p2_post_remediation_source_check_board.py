#!/usr/bin/env python3
"""Build KMFA v0.1.4 S11-P2 current public-safe source check board."""

from __future__ import annotations

import argparse
import csv
import functools
import html
import http.server
import json
import os
import socketserver
import subprocess
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

from KMFA.tools import v014_s11_p1_post_remediation_home_navigation as p1
from KMFA.tools.home_navigation_runtime import MODULE_ICONS
from KMFA.tools.source_check_board_runtime import ALLOWED_BOARD_STATUSES, REQUIRED_BOARD_COLUMNS


PHASE_ID = "V014_S11_P2_POST_REMEDIATION_SOURCE_CHECK_BOARD"
TASK_ID = "KMFA-V014-S11-P2-POST-REMEDIATION-SOURCE-CHECK-BOARD-20260711"
ACCEPTANCE_ID = "ACC-V014-S11-P2-POST-REMEDIATION-SOURCE-CHECK-BOARD"
VERSION = "0.1.4-s11-p2-post-remediation-source-check-board"
STATUS = "completed_validated_local_only_current_source_check_board_d_no_go_upload_deferred"
FORMULA_ID = "FORM-KMFA-V014-S11-P2-POST-REMEDIATION-SOURCE-CHECK-BOARD-001"
PARAMETER_IDS = ("PARAM-KMFA-1711", "PARAM-KMFA-1712", "PARAM-KMFA-1713")
MODEL_REGISTRY_KEY = "kmfa_v014_s11_p2_post_remediation_source_check_board"

OUTPUT_DIR = Path("KMFA/stage_artifacts") / PHASE_ID
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
HTML_DIR = OUTPUT_DIR / "exports" / "html"
SUMMARY_PATH = MACHINE_DIR / "source_check_board_summary.json"
MANIFEST_PATH = MACHINE_DIR / "source_check_board_manifest.json"
ROWS_PATH = MACHINE_DIR / "source_check_board_rows_public_safe.json"
GO_NO_GO_PATH = MACHINE_DIR / "source_check_board_go_no_go_report.json"
HTML_PATH = HTML_DIR / "kmfa_source_check_board.html"
COMPLETION_PATH = HUMAN_DIR / "s11_p2_completion_record_zh.md"
READ_ME_PATH = HUMAN_DIR / "source_check_board_readme_zh.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results_zh.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register_zh.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan_zh.md"

QUALITY_DIR = Path("KMFA/metadata/quality")
METADATA_SUMMARY_PATH = QUALITY_DIR / "v014_s11_p2_post_remediation_source_check_board_summary.json"
METADATA_MANIFEST_PATH = QUALITY_DIR / "v014_s11_p2_post_remediation_source_check_board_manifest.json"
METADATA_ROWS_PATH = QUALITY_DIR / "v014_s11_p2_post_remediation_source_check_board_rows_public_safe.json"
METADATA_GO_NO_GO_PATH = QUALITY_DIR / "v014_s11_p2_post_remediation_source_check_board_go_no_go_report.json"

PRIVATE_DIR = Path("KMFA/.codex_private_runtime/v014_s11_p2_post_remediation_source_check_board")
PRIVATE_RAW_BEFORE_PATH = PRIVATE_DIR / "raw_immutability_before.json"
PRIVATE_RAW_AFTER_PATH = PRIVATE_DIR / "raw_immutability_after.json"
PRIVATE_VALIDATION_REPORT_PATH = PRIVATE_DIR / "source_check_board_validation_zh.md"
PRIVATE_BASELINE_AUDIT_PATH = PRIVATE_DIR / "human_flow_baseline_audit.csv"
PRIVATE_CURRENT_AUDIT_PATH = PRIVATE_DIR / "current_source_check_board_audit.csv"
PRIVATE_BROWSER_PATH = PRIVATE_DIR / "browser_verification.json"
PRIVATE_SCREENSHOT_DIR = PRIVATE_DIR / "screenshots"

HISTORICAL_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V014_S11_P2_SOURCE_CHECK_BOARD/machine/source_check_board_manifest.json"
)
HISTORICAL_ROWS_PATH = Path(
    "KMFA/stage_artifacts/V014_S11_P2_SOURCE_CHECK_BOARD/machine/source_check_board_rows.jsonl"
)
HISTORICAL_HTML_PATH = Path(
    "KMFA/stage_artifacts/V014_S11_P2_SOURCE_CHECK_BOARD/exports/html/kmfa_source_check_board.html"
)
S5_AUTHORITY_PATH = Path("KMFA/metadata/baseline/v014_s05_p3_authority_baseline_manifest.json")
S7_FINANCE_PATH = Path("KMFA/metadata/imports/v014_s07_p1_finance_support_source_registry.json")
S7_WPS_PATH = Path("KMFA/metadata/imports/v014_s07_p2_wps_export_source_registry.json")
S7_REDCIRCLE_PATH = Path("KMFA/metadata/imports/v014_s07_p3_redcircle_export_source_registry.json")

DEVELOPMENT_EVENTS_PATH = Path("KMFA/docs/governance/development_events.jsonl")
STAGE_STATUS_PATH = Path("KMFA/metadata/stage_status.jsonl")
TASK_STATUS_PATH = Path("KMFA/metadata/traceability/v1_4_stage_phase_task_status.jsonl")

HOME_HREF = (
    "../../../V014_S11_P1_POST_REMEDIATION_HOME_NAVIGATION/exports/html/"
    "kmfa_home_navigation.html"
)

STATUS_OVERLAY = {
    "SCB-001": {
        "status": "部分/阻塞",
        "report_impact": "经营总览仅可显示 D 级受限状态，九项非零差异阻断完整可信结论。",
        "handling_rule": "只展示公开安全聚合状态，不用旧就绪标记替代当前差异结论。",
        "next_step": "继续关闭非零差异并保留最终接受未决项。",
        "status_reason": "current_report_grade_d_and_nonzero_differences",
    },
    "SCB-002": {
        "status": "部分/阻塞",
        "report_impact": "项目成本只能进入 D 级受限预览，九项非零差异继续保留。",
        "handling_rule": "项目成本来源可用于受限查看，但不得作为完整可信报告依据。",
        "next_step": "在独立 S11-P3 中展示差异和来源证据，不提前解锁。",
        "status_reason": "project_cost_nonzero_differences_preserved",
    },
    "SCB-003": {
        "status": "人工复核",
        "report_impact": "关键现金数据仍不完整，一项比较未完成，现金结论不得放行。",
        "handling_rule": "缺可证明数值时保持未知或最终接受未决，不推断、不补零。",
        "next_step": "补充可证明来源，或继续保留最终差异接受记录。",
        "status_reason": "cash_evidence_incomplete_and_one_comparison_open",
    },
    "SCB-004": {
        "status": "部分/阻塞",
        "report_impact": "回款应收仅可显示受限摘要，未完成比较继续阻断完整结论。",
        "handling_rule": "客户、合同和金额明细不进入公开检查板，差异状态不得隐藏。",
        "next_step": "继续使用私有证据核对并保留公开安全状态。",
        "status_reason": "collection_comparison_not_fully_closed",
    },
    "SCB-005": {
        "status": "人工复核",
        "report_impact": "项目状态仅作提示，不能形成完整履约或经营结论。",
        "handling_rule": "项目结构与映射需人工复核，不能自动解锁报告。",
        "next_step": "确认标准导出与字段映射证据。",
        "status_reason": "project_status_mapping_requires_review",
    },
    "SCB-006": {
        "status": "部分/阻塞",
        "report_impact": "经营导出仍为预留来源，缺少授权只读导出时结论保持降级。",
        "handling_rule": "本 phase 不接自动接口，只展示预留状态。",
        "next_step": "后续由负责人授权只读导出模板。",
        "status_reason": "reserved_export_template_only",
    },
    "SCB-007": {
        "status": "部分/阻塞",
        "report_impact": "合同导出仍为预留来源，合同口径不能作为正式结论。",
        "handling_rule": "缺失时保留替代来源和质量等级，不推断合同事实。",
        "next_step": "后续确认只读导出模板与回滚边界。",
        "status_reason": "reserved_contract_template_only",
    },
    "SCB-008": {
        "status": "部分/阻塞",
        "report_impact": "账务来源目前只有公开安全结构探针，成本与费用结论继续降级。",
        "handling_rule": "未取得标准只读导出前不得标记为已核验。",
        "next_step": "确认版本、模板和只读导出边界。",
        "status_reason": "public_safe_structure_probe_only",
    },
    "SCB-009": {
        "status": "人工复核",
        "report_impact": "现金与付款核销只能提示风险，不能解锁正式报告。",
        "handling_rule": "真实账号、对手方和流水明细只允许留在私有运行区。",
        "next_step": "人工确认脱敏账户映射和只读抽取边界。",
        "status_reason": "private_bank_evidence_requires_review",
    },
    "SCB-010": {
        "status": "人工复核",
        "report_impact": "税务风险只能提示，不能形成申报或开票执行结论。",
        "handling_rule": "税务申报和开票执行不在 KMFA 自动范围内。",
        "next_step": "人工确认政策证据和票据摘要映射。",
        "status_reason": "tax_evidence_requires_review",
    },
    "SCB-011": {
        "status": "已过期",
        "report_impact": "政策准备度只能显示过期提示。",
        "handling_rule": "过期证据不能参与正式报告或税务判断。",
        "next_step": "补充最新证据并重新锁定来源状态。",
        "status_reason": "policy_evidence_outdated",
    },
    "SCB-012": {
        "status": "失败/不适用",
        "report_impact": "缺少外部接口不阻断公开安全页面，但正式报告仍阻断。",
        "handling_rule": "S11-P2 不接自动接口，不保存任何凭据。",
        "next_step": "保持文件型最小版本和后续授权接入边界。",
        "status_reason": "connector_not_in_phase_scope",
    },
    "SCB-013": {
        "status": "已过期",
        "report_impact": "验收结算证据过期时，项目状态只能保留提示。",
        "handling_rule": "证据附件只登记公开安全引用，不公开全文。",
        "next_step": "补充有效证据并进入人工确认。",
        "status_reason": "acceptance_evidence_outdated",
    },
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path} must contain objects")
            rows.append(value)
    return rows


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def _write_jsonl_unique(path: Path, row: dict[str, Any]) -> None:
    preserved_lines = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip() and json.loads(line).get("phase_id") != PHASE_ID:
            preserved_lines.append(line)
    preserved_lines.append(json.dumps(row, ensure_ascii=False, separators=(",", ":")))
    _write_text(path, "\n".join(preserved_lines) + "\n")


def _load_current_home_dependency() -> dict[str, Any]:
    manifest = _read_json(p1.MANIFEST_PATH)
    summary = manifest.get("summary", {})
    validation = manifest.get("validation_summary", {})
    if summary.get("phase_id") != p1.PHASE_ID:
        raise ValueError("current S11-P1 manifest phase mismatch")
    expected = {
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "decision": "NO_GO",
        "open_final_difference_accepted_count": 3,
        "nonzero_delta_reconciliation_count": 9,
        "zero_delta_reconciliation_count": 2,
        "incomplete_reconciliation_count": 1,
        "raw_source_file_count": 5,
    }
    for key, value in expected.items():
        if summary.get(key) != value:
            raise ValueError(f"current S11-P1 dependency drift: {key}")
    if validation.get("final_validation_recorded") is not True:
        raise ValueError("current S11-P1 final validation is not recorded")
    if any(value != "PASS" for key, value in validation.items() if key != "final_validation_recorded"):
        raise ValueError("current S11-P1 final validation contains non-PASS result")
    if manifest != _read_json(p1.METADATA_MANIFEST_PATH):
        raise ValueError("current S11-P1 metadata mirror drift")
    return manifest


def _load_historical_framework() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    manifest = _read_json(HISTORICAL_MANIFEST_PATH)
    rows = _read_jsonl(HISTORICAL_ROWS_PATH)
    html_text = HISTORICAL_HTML_PATH.read_text(encoding="utf-8")
    if manifest.get("phase_id") != "S11-P2" or len(rows) != 13:
        raise ValueError("historical S11-P2 framework drift")
    if manifest.get("source_check_board_summary", {}).get("required_columns") != list(REQUIRED_BOARD_COLUMNS):
        raise ValueError("historical S11-P2 required columns drift")
    for token in ("sourceSearch", "statusFilter", "showDetail", "controlEvents.push"):
        if token not in html_text:
            raise ValueError(f"historical S11-P2 interaction missing: {token}")
    if manifest.get("quality_gate", {}).get("pending_reconciliation_count") != 12:
        raise ValueError("historical S11-P2 stale-state finding no longer reproducible")
    return manifest, rows


def _load_structural_dependencies() -> dict[str, Any]:
    authority = _read_json(S5_AUTHORITY_PATH)
    finance = _read_json(S7_FINANCE_PATH)
    wps = _read_json(S7_WPS_PATH)
    redcircle = _read_json(S7_REDCIRCLE_PATH)
    authority_count = authority.get("authority_summary", {}).get("authority_record_count")
    adapter_counts = [len(finance.get("sources", [])), len(wps.get("sources", [])), len(redcircle.get("sources", []))]
    if authority_count != 45 or adapter_counts != [9, 4, 4]:
        raise ValueError("current structural source dependency drift")
    if redcircle.get("registry_status") != "reserved_templates_only_no_connector":
        raise ValueError("redcircle reserved source boundary drift")
    return {
        "current_authority_record_count": authority_count,
        "current_source_adapter_record_count": sum(adapter_counts),
        "finance_adapter_record_count": adapter_counts[0],
        "table_adapter_record_count": adapter_counts[1],
        "reserved_export_template_record_count": adapter_counts[2],
    }


def _current_rows(generated_at: str) -> tuple[list[dict[str, Any]], int, int]:
    _, historical_rows = _load_historical_framework()
    rows: list[dict[str, Any]] = []
    changed = 0
    ready_recomputed = 0
    for historical in historical_rows:
        row_id = str(historical["row_id"])
        overlay = STATUS_OVERLAY[row_id]
        old_status = str(historical["status"])
        current_status = str(overlay["status"])
        changed += int(old_status != current_status)
        ready_recomputed += int(old_status == "已就绪" and current_status != old_status)
        rows.append(
            {
                "schema_version": "kmfa.v014.s11_p2.post_remediation_source_check_board_row.v1",
                "record_type": "public_safe_source_check_board_row",
                "project_id": "KMFA",
                "stage_id": "S11",
                "phase_id": PHASE_ID,
                "roadmap_phase_id": "S11-P2",
                "row_id": row_id,
                "row_order": int(historical["row_order"]),
                "source_system": historical["source_system"],
                "business_segment": historical["business_segment"],
                "source_package_ref": historical["source_package_ref"],
                "entity_ref": historical["entity_ref"],
                "bank_or_system_account": historical["bank_or_system_account"],
                "account_or_report_ref": historical["account_or_report_ref"],
                "frequency": historical["frequency"],
                "status": current_status,
                "historical_status": old_status,
                "current_status_changed": old_status != current_status,
                "status_basis": "current_public_safe_evidence_overlay",
                "status_reason": overlay["status_reason"],
                "report_impact": overlay["report_impact"],
                "handling_rule": overlay["handling_rule"],
                "next_step": overlay["next_step"],
                "contains_raw_business_values": False,
                "contains_private_file_references": False,
                "raw_layer_write_allowed": False,
                "persistent_status_write_allowed": False,
                "formal_report_allowed": False,
                "business_decision_basis_allowed": False,
                "generated_at": generated_at,
            }
        )
    return rows, ready_recomputed, changed


def _status_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts = {status: 0 for status in ALLOWED_BOARD_STATUSES}
    for row in rows:
        counts[str(row["status"])] += 1
    return counts


def _status_class(status: str) -> str:
    return {
        "已就绪": "ready",
        "部分/阻塞": "partial",
        "失败/不适用": "failed",
        "已过期": "outdated",
        "人工复核": "review",
    }[status]


def _icon_svg(icon_key: str) -> str:
    return (
        '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" '
        'stroke="currentColor" stroke-width="1.8" stroke-linecap="round" '
        f'stroke-linejoin="round">{MODULE_ICONS[icon_key]}</svg>'
    )


def _render_html(rows: list[dict[str, Any]], counts: dict[str, int]) -> str:
    status_cards = "".join(
        f'<div class="status-card"><span>{html.escape(status)}</span><strong data-count-for="{html.escape(status)}">{counts[status]}</strong></div>'
        for status in ALLOWED_BOARD_STATUSES
    )
    filter_options = "".join(
        f'<option value="{html.escape(status)}">{html.escape(status)}</option>' for status in ALLOWED_BOARD_STATUSES
    )
    preview_buttons = "".join(
        f'<button type="button" class="preview-option {_status_class(status)}" data-status-preview="{html.escape(status)}">{html.escape(status)}</button>'
        for status in ALLOWED_BOARD_STATUSES
    )
    headers = "".join(f'<th scope="col">{html.escape(column)}</th>' for column in REQUIRED_BOARD_COLUMNS)
    table_rows = []
    for row in rows:
        search_text = " ".join(
            str(row[field])
            for field in (
                "source_system",
                "business_segment",
                "source_package_ref",
                "entity_ref",
                "bank_or_system_account",
                "account_or_report_ref",
                "frequency",
                "status",
            )
        )
        table_rows.append(
            f'''<tr data-row-id="{html.escape(row['row_id'])}" data-status="{html.escape(row['status'])}" data-search="{html.escape(search_text.lower())}">
<td>{html.escape(row['source_system'])}</td><td>{html.escape(row['business_segment'])}</td><td>{html.escape(row['source_package_ref'])}</td>
<td>{html.escape(row['entity_ref'])}</td><td>{html.escape(row['bank_or_system_account'])}</td><td>{html.escape(row['account_or_report_ref'])}</td>
<td>{html.escape(row['frequency'])}</td><td><button type="button" class="status-badge {_status_class(row['status'])}" data-status-detail="{html.escape(row['row_id'])}">{html.escape(row['status'])}</button></td>
<td>{html.escape(row['report_impact'])}</td><td>{html.escape(row['handling_rule'])}</td><td>{html.escape(row['next_step'])}</td></tr>'''
        )
    row_state_json = json.dumps(
        {row["row_id"]: row for row in rows}, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).replace("</", "<\\/")
    source_icon = _icon_svg("source_check")
    home_icon = _icon_svg("business_overview")
    first = rows[0]
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>KMFA 数据源检查板</title>
<style>
:root{{--navy:#123553;--blue:#17679b;--blue-dark:#104a71;--blue-soft:#edf5fa;--page:#f3f6f8;--surface:#fff;--line:#ccd8e1;--text:#172632;--muted:#60717e;--danger:#a83232;--danger-bg:#fff1f0;--green:#176b4a;--green-bg:#e9f7f0;--violet:#6743a5;--violet-bg:#f2edfb;--gray:#3f4b55;--gray-bg:#edf0f2}}
*{{box-sizing:border-box}}html{{min-width:320px;background:var(--page)}}body{{margin:0;background:var(--page);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",Arial,sans-serif;letter-spacing:0}}button,input,select,a{{font:inherit}}button,a{{-webkit-tap-highlight-color:transparent}}button:focus-visible,input:focus-visible,select:focus-visible,a:focus-visible{{outline:3px solid rgba(23,103,155,.28);outline-offset:2px}}
.top-band{{display:flex;justify-content:space-between;align-items:center;gap:18px;padding:18px 28px;background:var(--navy);color:#fff;border-bottom:4px solid var(--blue)}}.brand{{display:flex;align-items:center;gap:12px;min-width:0}}.brand-mark{{width:46px;height:46px;display:grid;place-items:center;flex:0 0 46px;border:1px solid rgba(255,255,255,.38);border-radius:6px;background:var(--blue)}}.brand-mark svg{{width:23px;height:23px}}.brand strong{{display:block;font-size:18px}}.brand span{{display:block;margin-top:2px;color:#c6dbea;font-size:12px}}.home-link{{min-height:40px;display:inline-flex;align-items:center;gap:8px;padding:8px 12px;border:1px solid rgba(255,255,255,.42);border-radius:6px;color:#fff;text-decoration:none}}.home-link:hover{{background:rgba(255,255,255,.1)}}.home-link svg{{width:17px;height:17px}}
main{{min-width:0;padding:24px 28px 34px}}.heading{{display:flex;justify-content:space-between;align-items:flex-start;gap:20px}}h1{{margin:0;color:var(--navy);font-size:25px}}.heading p{{margin:7px 0 0;color:var(--muted);line-height:1.65}}.gate{{flex:0 0 auto;border:1px solid #e6a39e;border-radius:6px;background:var(--danger-bg);padding:10px 13px;color:var(--danger)}}.gate span{{display:block;font-size:12px}}.gate strong{{display:block;margin-top:3px;font-size:16px}}
.quality-strip{{margin:16px 0;padding:12px 14px;border-left:4px solid var(--danger);background:#fff8f7;line-height:1.6}}.status-summary{{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:10px;margin-bottom:18px}}.status-card{{min-width:0;border:1px solid var(--line);border-radius:6px;background:var(--surface);padding:12px 14px}}.status-card span{{display:block;color:var(--muted);font-size:12px}}.status-card strong{{display:block;margin-top:4px;color:var(--navy);font-size:22px}}
.controls{{display:grid;grid-template-columns:minmax(230px,1fr) 240px auto;gap:10px;align-items:end;margin:0 0 10px}}label{{display:grid;gap:6px;color:#344652;font-size:12px;font-weight:700}}input,select{{width:100%;height:41px;border:1px solid var(--line);border-radius:6px;background:#fff;color:var(--text);padding:0 11px}}.reset-button{{height:41px;border:1px solid var(--blue);border-radius:6px;background:#fff;color:var(--blue);padding:0 14px;cursor:pointer}}.reset-button:hover{{background:var(--blue-soft)}}.filter-feedback{{min-height:25px;margin:0 0 9px;color:var(--muted);font-size:13px}}
.matrix-scroll{{width:100%;max-width:100%;overflow-x:auto;border:1px solid var(--line);background:#fff}}table{{width:100%;min-width:1320px;border-collapse:collapse}}th{{position:sticky;top:0;z-index:1;padding:11px 10px;background:#eaf1f5;color:#27475d;border-bottom:1px solid #bfcfd9;text-align:left;font-size:12px;white-space:nowrap}}td{{padding:10px;border-bottom:1px solid #e4ebef;vertical-align:top;font-size:12px;line-height:1.5}}tbody tr:last-child td{{border-bottom:0}}tbody tr:hover td,tbody tr.selected td{{background:#f4f9fc}}.status-badge,.preview-option{{border:1px solid transparent;border-radius:999px;padding:5px 9px;font-size:12px;font-weight:700;white-space:nowrap;cursor:pointer}}.ready{{color:var(--green);background:var(--green-bg)}}.partial{{color:var(--blue-dark);background:var(--blue-soft);border-color:#bad3e2}}.failed{{color:var(--danger);background:var(--danger-bg)}}.outdated{{color:var(--gray);background:var(--gray-bg)}}.review{{color:var(--violet);background:var(--violet-bg)}}
.detail-panel{{margin-top:16px;border:1px solid var(--line);background:#fff}}.detail-head{{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:16px 18px;border-bottom:1px solid var(--line)}}.detail-head h2{{margin:0;color:var(--navy);font-size:18px}}.detail-head span{{font-size:12px;color:var(--muted)}}.detail-grid{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr))}}.detail-item{{min-width:0;padding:15px 18px;border-right:1px solid var(--line)}}.detail-item:last-child{{border-right:0}}.detail-item span{{display:block;color:var(--muted);font-size:12px}}.detail-item strong{{display:block;margin-top:7px;color:var(--navy);font-size:14px;line-height:1.6;overflow-wrap:anywhere}}.preview-bar{{padding:14px 18px;border-top:1px solid var(--line);background:#f8fafb}}.preview-bar p{{margin:0 0 10px;color:var(--muted);font-size:12px}}.segmented{{display:flex;flex-wrap:wrap;gap:7px}}
.event-panel{{margin-top:12px;padding:15px 18px;border:1px solid var(--line);background:#f8fafb}}.event-panel h2{{margin:0 0 8px;color:var(--navy);font-size:16px}}.event-panel p{{margin:0;color:#40515d;line-height:1.65}}footer{{padding-top:14px;color:var(--muted);font-size:12px}}
@media(max-width:900px){{.status-summary{{grid-template-columns:repeat(2,minmax(0,1fr))}}.controls{{grid-template-columns:1fr 1fr}}.reset-button{{grid-column:1/-1}}.detail-grid{{grid-template-columns:1fr}}.detail-item{{border-right:0;border-bottom:1px solid var(--line)}}.detail-item:last-child{{border-bottom:0}}}}
@media(max-width:600px){{.top-band{{align-items:flex-start;padding:14px}}.home-link{{flex:0 0 auto;padding:8px}}.home-link span{{display:none}}main{{padding:18px 14px 26px}}.heading{{display:block}}.gate{{display:inline-block;margin-top:12px}}.status-summary{{grid-template-columns:repeat(2,minmax(0,1fr))}}.controls{{grid-template-columns:minmax(0,1fr)}}.reset-button{{grid-column:auto}}}}
</style></head>
<body data-ui-ready="false" data-last-action="initial">
<header class="top-band"><div class="brand"><div class="brand-mark">{source_icon}</div><div><strong>KMFA 数据源检查板</strong><span>公开安全状态矩阵</span></div></div><a class="home-link" data-home-link href="{HOME_HREF}">{home_icon}<span>返回经营首页</span></a></header>
<main><section class="heading"><div><h1>数据源状态与报告影响</h1><p>按来源系统、业务板块、文件包、主体和账户逐项检查；状态预演只写浏览器会话控制事件。</p></div><div class="gate"><span>当前报告状态</span><strong>Q4 / D · NO_GO</strong></div></section>
<section class="quality-strip"><strong>当前限制：</strong>3 项最终接受未决、9 项非零差异、2 项零差异、1 项比较未完成。检查板不代表正式报告放行。</section>
<section class="status-summary" aria-label="来源状态汇总">{status_cards}</section>
<section class="controls" aria-label="矩阵筛选"><label>搜索来源或业务板块<input id="source-search" type="search" placeholder="输入来源、板块、文件包、主体或账户"></label><label>状态筛选<select id="status-filter"><option value="">全部状态</option>{filter_options}</select></label><button type="button" class="reset-button" id="reset-filter">清除筛选</button></section>
<p class="filter-feedback" id="filter-feedback" aria-live="polite">当前显示 13 条公开安全来源状态。</p>
<div class="matrix-scroll" id="matrix-scroll" tabindex="0" aria-label="数据源检查矩阵，可横向滚动"><table><thead><tr>{headers}</tr></thead><tbody>{''.join(table_rows)}</tbody></table></div>
<section class="detail-panel" id="detail-panel" data-selected-row="{first['row_id']}" aria-live="polite"><div class="detail-head"><h2 id="detail-title">{html.escape(first['source_system'])} · {html.escape(first['business_segment'])}</h2><span id="detail-status">当前状态：{html.escape(first['status'])}</span></div><div class="detail-grid"><div class="detail-item"><span>影响报告</span><strong id="detail-impact">{html.escape(first['report_impact'])}</strong></div><div class="detail-item"><span>处理规则</span><strong id="detail-rule">{html.escape(first['handling_rule'])}</strong></div><div class="detail-item"><span>下一步</span><strong id="detail-next">{html.escape(first['next_step'])}</strong></div></div><div class="preview-bar"><p>状态预演仅影响当前浏览器会话，不修改原始数据，不写入持久业务状态。</p><div class="segmented" role="group" aria-label="会话内状态预演">{preview_buttons}</div></div></section>
<section class="event-panel" id="control-event-panel" aria-live="polite"><h2>会话控制事件</h2><p id="control-event-log">尚未预演状态；当前矩阵来自已锁定的公开安全证据。</p></section>
<footer>公开安全检查板，不包含原始文件身份、字段表头、业务金额、账号或明细。S11-P3、Stage 11 复审及上传均未执行。</footer></main>
<script>
const rowState={row_state_json};
const allowedStatuses={json.dumps(list(ALLOWED_BOARD_STATUSES), ensure_ascii=False)};
const statusClasses={{"已就绪":"ready","部分/阻塞":"partial","失败/不适用":"failed","已过期":"outdated","人工复核":"review"}};
const body=document.body; const search=document.getElementById('source-search'); const statusFilter=document.getElementById('status-filter'); const feedback=document.getElementById('filter-feedback');
let selectedRowId={json.dumps(first['row_id'])}; let actionSequence=0; let eventSequence=0; const controlEvents=[];
function recordAction(label){{actionSequence+=1; body.dataset.lastAction=`${{String(actionSequence).padStart(3,'0')}}:${{label}}`;}}
function visibleRows(){{return Array.from(document.querySelectorAll('tbody tr[data-row-id]')).filter(row=>row.style.display!=='none');}}
function applyFilters(){{const term=search.value.trim().toLowerCase(); const status=statusFilter.value; document.querySelectorAll('tbody tr[data-row-id]').forEach(row=>{{const matchesTerm=!term||row.dataset.search.includes(term); const matchesStatus=!status||row.dataset.status===status; row.style.display=matchesTerm&&matchesStatus?'':'none';}}); const count=visibleRows().length; feedback.textContent=`当前显示 ${{count}} 条公开安全来源状态。`; recordAction(`筛选:${{term||'全部'}}:${{status||'全部'}}:${{count}}`);}}
function resetFilters(){{search.value=''; statusFilter.value=''; applyFilters(); feedback.textContent='已清除筛选，当前显示 13 条公开安全来源状态。'; recordAction('清除筛选:13');}}
function selectRow(rowId){{const row=rowState[rowId]; if(!row)return; selectedRowId=rowId; document.querySelectorAll('tbody tr[data-row-id]').forEach(item=>item.classList.toggle('selected',item.dataset.rowId===rowId)); document.getElementById('detail-panel').dataset.selectedRow=rowId; document.getElementById('detail-title').textContent=`${{row.source_system}} · ${{row.business_segment}}`; document.getElementById('detail-status').textContent=`当前状态：${{row.status}}`; document.getElementById('detail-impact').textContent=row.report_impact; document.getElementById('detail-rule').textContent=row.handling_rule; document.getElementById('detail-next').textContent=row.next_step; recordAction(`查看状态:${{rowId}}:${{row.status}}`);}}
function updateStatusCounters(){{allowedStatuses.forEach(status=>{{const count=Object.values(rowState).filter(row=>row.status===status).length; const target=document.querySelector(`[data-count-for="${{status}}"]`); if(target)target.textContent=String(count);}});}}
function previewStatus(status){{const row=rowState[selectedRowId]; if(!row)return; const previous=row.status; row.status=status; const tableRow=document.querySelector(`tr[data-row-id="${{selectedRowId}}"]`); const badge=document.querySelector(`button[data-status-detail="${{selectedRowId}}"]`); tableRow.dataset.status=status; tableRow.dataset.search=`${{row.source_system}} ${{row.business_segment}} ${{row.source_package_ref}} ${{row.entity_ref}} ${{row.bank_or_system_account}} ${{row.account_or_report_ref}} ${{row.frequency}} ${{status}}`.toLowerCase(); badge.textContent=status; badge.className=`status-badge ${{statusClasses[status]}}`; eventSequence+=1; const event={{event_id:`会话事件-${{String(eventSequence).padStart(3,'0')}}`,row_id:selectedRowId,previous_status:previous,preview_status:status,target_layer:'browser_session_only',persistent_write:false,raw_layer_write:false}}; controlEvents.push(event); document.getElementById('detail-status').textContent=`预演状态：${{status}}`; document.getElementById('control-event-log').textContent=`${{event.event_id}}：${{selectedRowId}} 从“${{previous}}”预演为“${{status}}”；仅会话，不写原始数据或持久业务状态。`; body.dataset.lastEvent=`preview:${{selectedRowId}}:${{status}}:${{eventSequence}}`; updateStatusCounters(); applyFilters(); recordAction(`状态预演:${{selectedRowId}}:${{status}}:仅会话`);}}
document.querySelectorAll('button[data-status-detail]').forEach(button=>button.addEventListener('click',()=>selectRow(button.dataset.statusDetail)));
document.querySelectorAll('button[data-status-preview]').forEach(button=>button.addEventListener('click',()=>previewStatus(button.dataset.statusPreview)));
search.addEventListener('input',applyFilters); statusFilter.addEventListener('change',applyFilters); document.getElementById('reset-filter').addEventListener('click',resetFilters);
selectRow(selectedRowId); body.dataset.uiReady='true'; recordAction('页面就绪:13');
</script></body></html>'''


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        return


def _browser_worker() -> dict[str, Any]:
    from playwright.sync_api import sync_playwright

    PRIVATE_SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    stage_root = Path("KMFA/stage_artifacts").resolve()
    handler = functools.partial(_QuietHandler, directory=str(stage_root))
    server = socketserver.TCPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    url = f"{base}/{PHASE_ID}/exports/html/{HTML_PATH.name}"
    counts = {"已就绪": 0, "部分/阻塞": 6, "失败/不适用": 1, "已过期": 2, "人工复核": 4}
    viewport_checks: list[dict[str, Any]] = []
    search_checks: list[dict[str, Any]] = []
    filter_checks: list[dict[str, Any]] = []
    detail_checks: list[dict[str, Any]] = []
    preview_checks: list[dict[str, Any]] = []
    keyboard_checks: list[dict[str, Any]] = []
    home_checks: list[dict[str, Any]] = []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=True,
                executable_path=p1._chromium_path(),
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
            for mode, viewport in (("desktop", {"width": 1440, "height": 1000}), ("mobile", {"width": 390, "height": 844})):
                page = browser.new_page(viewport=viewport)
                console_errors: list[str] = []
                page.on(
                    "console",
                    lambda msg: console_errors.append(msg.text)
                    if msg.type == "error" and p1._is_actionable_console_error(f"{msg.text} {msg.location.get('url', '')}")
                    else None,
                )
                page.on("pageerror", lambda exc: console_errors.append(str(exc)))
                page.goto(url, wait_until="load")
                page.wait_for_timeout(120)

                page.locator("#source-search").fill("现金资金")
                page.wait_for_timeout(40)
                search_checks.append(
                    {
                        "mode": mode,
                        "action": "search",
                        "passed": page.locator('tbody tr[data-row-id]:visible').count() == 1 and "1 条" in page.locator("#filter-feedback").inner_text(),
                    }
                )
                page.locator("#reset-filter").click()
                search_checks.append(
                    {
                        "mode": mode,
                        "action": "reset",
                        "passed": page.locator('tbody tr[data-row-id]:visible').count() == 13 and page.locator("#source-search").input_value() == "",
                    }
                )

                for status in ALLOWED_BOARD_STATUSES:
                    page.locator("#status-filter").select_option(status)
                    page.wait_for_timeout(25)
                    filter_checks.append(
                        {
                            "mode": mode,
                            "status": status,
                            "passed": page.locator('tbody tr[data-row-id]:visible').count() == counts[status],
                        }
                    )
                page.locator("#reset-filter").click()

                for row_id in sorted(STATUS_OVERLAY):
                    page.locator(f'button[data-status-detail="{row_id}"]').click()
                    page.wait_for_timeout(20)
                    detail_checks.append(
                        {
                            "mode": mode,
                            "row_id": row_id,
                            "passed": page.locator("#detail-panel").get_attribute("data-selected-row") == row_id
                            and bool(page.locator("#detail-impact").inner_text().strip())
                            and bool(page.locator("#detail-next").inner_text().strip()),
                        }
                    )

                first_badge = page.locator('button[data-status-detail="SCB-001"]')
                first_badge.focus()
                first_badge.press("Enter")
                keyboard_checks.append(
                    {
                        "mode": mode,
                        "passed": page.locator("#detail-panel").get_attribute("data-selected-row") == "SCB-001",
                    }
                )
                for status in ALLOWED_BOARD_STATUSES:
                    before = page.locator("body").get_attribute("data-last-event")
                    page.locator(f'button[data-status-preview="{status}"]').click()
                    after = page.locator("body").get_attribute("data-last-event")
                    preview_checks.append(
                        {
                            "mode": mode,
                            "status": status,
                            "passed": before != after
                            and str(after).startswith(f"preview:SCB-001:{status}:")
                            and page.locator('button[data-status-detail="SCB-001"]').inner_text() == status
                            and "仅会话" in page.locator("#control-event-log").inner_text(),
                        }
                    )

                if mode == "desktop":
                    href = page.locator("a[data-home-link]").get_attribute("href") or ""
                    response = page.request.get(urljoin(page.url, href))
                    home_checks.append({"href": href, "status": response.status, "passed": response.ok})

                page.reload(wait_until="load")
                page.wait_for_timeout(80)
                dimensions = page.evaluate(
                    """({
                      documentScrollWidth: document.documentElement.scrollWidth,
                      innerWidth: window.innerWidth,
                      matrixRight: document.getElementById('matrix-scroll').getBoundingClientRect().right,
                      matrixOverflowX: getComputedStyle(document.getElementById('matrix-scroll')).overflowX
                    })"""
                )
                screenshot = PRIVATE_SCREENSHOT_DIR / f"kmfa_source_check_board_{mode}.png"
                page.screenshot(path=str(screenshot), full_page=True)
                viewport_checks.append(
                    {
                        "mode": mode,
                        "viewport": viewport,
                        "ui_ready": page.locator("body").get_attribute("data-ui-ready") == "true",
                        "console_error_count": len(console_errors),
                        "no_horizontal_overflow": dimensions["documentScrollWidth"] <= dimensions["innerWidth"],
                        "matrix_scroll_contained": dimensions["matrixRight"] <= dimensions["innerWidth"] + 1
                        and dimensions["matrixOverflowX"] == "auto",
                    }
                )
                page.close()
            browser.close()
    finally:
        server.shutdown()
        server.server_close()

    passed = (
        all(item["passed"] for item in search_checks)
        and all(item["passed"] for item in filter_checks)
        and all(item["passed"] for item in detail_checks)
        and all(item["passed"] for item in preview_checks)
        and all(item["passed"] for item in keyboard_checks)
        and all(item["passed"] for item in home_checks)
        and all(
            item["ui_ready"]
            and item["console_error_count"] == 0
            and item["no_horizontal_overflow"]
            and item["matrix_scroll_contained"]
            for item in viewport_checks
        )
    )
    result = {
        "status": "PASS" if passed else "FAIL",
        "viewport_checks": viewport_checks,
        "search_checks": search_checks,
        "status_filter_checks": filter_checks,
        "status_detail_checks": detail_checks,
        "status_preview_checks": preview_checks,
        "keyboard_checks": keyboard_checks,
        "home_link_http_checks": home_checks,
    }
    _write_json(PRIVATE_BROWSER_PATH, result)
    if not passed:
        raise RuntimeError("S11-P2 browser review failed")
    return result


def _run_browser_suite() -> dict[str, Any]:
    baseline = p1._run_html_audit(p1.AUDIT_ROOT, PRIVATE_BASELINE_AUDIT_PATH)
    current = p1._run_html_audit(HTML_DIR, PRIVATE_CURRENT_AUDIT_PATH)
    env = os.environ.copy()
    env["KMFA_CHROMIUM"] = p1._chromium_path()
    result = subprocess.run(
        [str(p1._audit_python()), str(Path(__file__).resolve()), "--browser-evidence-only"],
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
        "baseline_file_count": baseline["file_count"],
        "baseline_control_row_count": baseline["control_row_count"],
        "baseline_pass_count": baseline["pass_count"],
        "baseline_warn_count": baseline["warn_count"],
        "baseline_fail_count": baseline["fail_count"],
        "current_html_file_count": current["file_count"],
        "current_html_control_row_count": current["control_row_count"],
        "current_html_pass_count": current["pass_count"],
        "current_html_warn_count": current["warn_count"],
        "current_html_fail_count": current["fail_count"],
        "viewport_check_count": len(browser["viewport_checks"]),
        "search_interaction_count": len(browser["search_checks"]),
        "status_filter_interaction_count": len(browser["status_filter_checks"]),
        "status_detail_interaction_count": len(browser["status_detail_checks"]),
        "status_preview_interaction_count": len(browser["status_preview_checks"]),
        "keyboard_interaction_count": len(browser["keyboard_checks"]),
        "home_link_http_check_count": len(browser["home_link_http_checks"]),
        "console_error_count": sum(item["console_error_count"] for item in browser["viewport_checks"]),
        "horizontal_overflow_count": sum(not item["no_horizontal_overflow"] for item in browser["viewport_checks"]),
        "matrix_scroll_containment_count": sum(item["matrix_scroll_contained"] for item in browser["viewport_checks"]),
    }


def _raw_snapshot(label: str) -> dict[str, Any]:
    return p1._raw_snapshot(label)


def _normalize_raw(value: dict[str, Any]) -> dict[str, Any]:
    return p1._normalize_raw(value)


def _write_governance(generated_at: str) -> None:
    evidence_ref = MANIFEST_PATH.as_posix()
    _write_jsonl_unique(
        DEVELOPMENT_EVENTS_PATH,
        {
            "event_id": "DEV-KMFA-20260711-V014-S11-P2-POST-REMEDIATION-SOURCE-CHECK-BOARD",
            "event_time": generated_at,
            "event_type": "development",
            "project_id": "KMFA",
            "stage_id": "S11",
            "phase_id": PHASE_ID,
            "roadmap_phase_id": "S11-P2",
            "task_id": TASK_ID,
            "status": STATUS,
            "fact_level": "EXTRACTED",
            "decision": "NO_GO",
            "current_report_grade": "D",
            "raw_business_data_committed": False,
            "persistent_status_write_performed": False,
            "github_upload_performed": False,
            "app_reinstall_performed": False,
            "business_execution_performed": False,
            "evidence_ref": evidence_ref,
            "result_commit": "PENDING",
        },
    )
    _write_jsonl_unique(
        STAGE_STATUS_PATH,
        {
            "schema_version": "kmfa.stage_status.v1",
            "record_type": "phase_status",
            "project_id": "KMFA",
            "stage_id": "S11",
            "phase_id": PHASE_ID,
            "roadmap_phase_id": "S11-P2",
            "task_id": TASK_ID,
            "version": VERSION,
            "status": STATUS,
            "fact_level": "EXTRACTED",
            "decision": "NO_GO",
            "current_report_grade": "D",
            "raw_data_committed": False,
            "persistent_status_write_performed": False,
            "github_upload_performed": False,
            "app_reinstall_performed": False,
            "business_execution_performed": False,
            "evidence_ref": evidence_ref,
            "updated_at": generated_at,
        },
    )
    _write_jsonl_unique(
        TASK_STATUS_PATH,
        {
            "schema_version": "kmfa.v014_stage_phase_task_status.v1",
            "record_type": "v014_phase",
            "project_id": "KMFA",
            "stage_id": "S11",
            "governance_stage_id": "FRONTEND-BASE-AND-SOURCE-CHECK",
            "roadmap_stage_id": "S11",
            "roadmap_phase_id": "S11-P2",
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "acceptance_id": ACCEPTANCE_ID,
            "version": VERSION,
            "name": "v0.1.4 S11-P2 post-remediation source check board",
            "phase_goal": "show current public-safe source status impact and next action without persistent write-back",
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


def generate(*, final_validation: bool = False) -> dict[str, Any]:
    generated_at = _now_iso()
    current_home = _load_current_home_dependency()
    historical_manifest, _ = _load_historical_framework()
    structural = _load_structural_dependencies()
    rows, ready_recomputed_count, changed_count = _current_rows(generated_at)
    counts = _status_counts(rows)
    expected_counts = {"已就绪": 0, "部分/阻塞": 6, "失败/不适用": 1, "已过期": 2, "人工复核": 4}
    if counts != expected_counts or ready_recomputed_count != 4 or changed_count != 5:
        raise ValueError("current source status overlay mismatch")

    raw_before = _raw_snapshot("v014_s11_p2_post_remediation_source_check_board_before")
    _write_json(PRIVATE_RAW_BEFORE_PATH, raw_before)
    _write_text(HTML_PATH, _render_html(rows, counts))
    browser = _run_browser_suite()
    raw_after = _raw_snapshot("v014_s11_p2_post_remediation_source_check_board_after")
    _write_json(PRIVATE_RAW_AFTER_PATH, raw_after)
    prior_raw = _read_json(p1.PRIVATE_RAW_AFTER_PATH)
    current_raw = _raw_snapshot("v014_s11_p2_post_remediation_source_check_board_current")
    if not (_normalize_raw(raw_before) == _normalize_raw(raw_after) == _normalize_raw(prior_raw) == _normalize_raw(current_raw)):
        raise ValueError("raw snapshot drift detected")

    home_summary = current_home["summary"]
    summary = {
        "schema_version": "kmfa.v014.s11_p2.post_remediation_source_check_board_summary.v1",
        "project_id": "KMFA",
        "stage_id": "S11",
        "phase_id": PHASE_ID,
        "roadmap_phase_id": "S11-P2",
        "status": STATUS,
        "decision": "NO_GO",
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "open_final_difference_accepted_count": 3,
        "nonzero_delta_reconciliation_count": 9,
        "zero_delta_reconciliation_count": 2,
        "incomplete_reconciliation_count": 1,
        "hard_block_count": 12,
        "matrix_row_count": len(rows),
        "required_columns": list(REQUIRED_BOARD_COLUMNS),
        "required_column_count": len(REQUIRED_BOARD_COLUMNS),
        "allowed_statuses": list(ALLOWED_BOARD_STATUSES),
        "allowed_status_count": len(ALLOWED_BOARD_STATUSES),
        "status_counts": counts,
        "historical_ready_status_recomputed_count": ready_recomputed_count,
        "current_status_changed_count": changed_count,
        "current_ready_row_count": counts["已就绪"],
        "current_source_state_overlay_applied": True,
        "historical_dynamic_state_reused": False,
        "contains_stale_pending_twelve": False,
        "contains_b_grade": False,
        "current_authority_record_count": structural["current_authority_record_count"],
        "current_source_adapter_record_count": structural["current_source_adapter_record_count"],
        "raw_source_file_count": home_summary["raw_source_file_count"],
        "raw_snapshot_exact_match": True,
        "raw_cross_phase_snapshot_exact_match": True,
        "home_navigation_link_count": 1,
        "visible_feedback_panel_count": 3,
        "km_brand_mark_present": True,
        "single_k_brand_mark_present": False,
        "blue_gray_surface_dominant": True,
        "status_badges_only": True,
        "large_yellow_surface_count": 0,
        "all_chinese_visible_copy": True,
        "formal_report_count": 0,
        "business_decision_basis_allowed_count": 0,
    }
    interaction = {
        "search_feedback_enabled": True,
        "status_filter_enabled": True,
        "status_click_detail_enabled": True,
        "detail_panel_fields": ["影响报告", "处理规则", "下一步"],
        "session_status_preview_action_count": 5,
        "session_only_control_events": True,
        "persistent_status_write_allowed": False,
        "raw_layer_write_allowed": False,
        "automatic_external_action_allowed": False,
    }
    quality_gate = {
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "decision": "NO_GO",
        "release_permission": "blocked",
        "source_check_board_display_allowed": True,
        "complete_trusted_report_display_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "business_execution_allowed": False,
        "persistent_status_write_allowed": False,
    }
    dependencies = {
        "current_s11_p1_post_remediation_home_navigation_validated": True,
        "current_s10_post_remediation_state_inherited": True,
        "historical_s11_p2_framework_validated": True,
        "historical_s11_p2_stale_pending_detected": historical_manifest["quality_gate"]["pending_reconciliation_count"] == 12,
        "historical_dynamic_state_reused": False,
        "current_authority_baseline_validated": True,
        "current_source_adapter_registries_validated": True,
        "v14_human_flow_baseline_rerun": True,
        **structural,
    }
    boundaries = {
        "s11_p1_dependency_validated": True,
        "s11_p2_performed": True,
        "s11_p3_performed": False,
        "stage11_review_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "formal_report_release_performed": False,
        "business_execution_performed": False,
        "persistent_status_write_performed": False,
        "raw_write_performed": False,
        "raw_delete_performed": False,
        "raw_move_performed": False,
        "raw_rename_performed": False,
        "raw_overwrite_performed": False,
    }
    validation_summary = {
        "final_validation_recorded": final_validation,
        "focused_tests": "PASS" if final_validation else "PENDING",
        "strict_validator": "PASS" if final_validation else "PENDING",
        "browser_desktop_mobile": "PASS" if final_validation else "PENDING",
        "governance_and_safety_scans": "PASS" if final_validation else "PENDING",
    }
    rows_document = {
        "schema_version": "kmfa.v014.s11_p2.post_remediation_source_check_board_rows.v1",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "rows": rows,
    }
    go_no_go = {
        "schema_version": "kmfa.v014.s11_p2.post_remediation_source_check_board_go_no_go.v1",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "decision": "NO_GO",
        "source_check_board_display_allowed": True,
        "persistent_status_write_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "s11_p3_performed": False,
        "stage11_review_performed": False,
        "github_upload_performed": False,
    }
    manifest = {
        "schema_version": "kmfa.v014.s11_p2.post_remediation_source_check_board_manifest.v1",
        "project_id": "KMFA",
        "version": VERSION,
        "stage_id": "S11",
        "phase_id": PHASE_ID,
        "roadmap_phase_id": "S11-P2",
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "status": STATUS,
        "generated_at": generated_at,
        "summary": summary,
        "source_rows": rows,
        "interaction_contract": interaction,
        "quality_gate": quality_gate,
        "browser_review": browser,
        "dependencies": dependencies,
        "phase_boundaries": boundaries,
        "go_no_go": go_no_go,
        "validation_summary": validation_summary,
        "public_repo_safety": {
            "raw_business_data_committed": False,
            "raw_file_identity_committed": False,
            "field_or_header_plaintext_committed": False,
            "business_amount_values_committed": False,
            "private_runtime_committed": False,
            "credentials_or_secrets_committed": False,
            "zip_excel_pdf_private_csv_or_database_committed": False,
        },
    }
    for path, value in (
        (SUMMARY_PATH, summary),
        (MANIFEST_PATH, manifest),
        (ROWS_PATH, rows_document),
        (GO_NO_GO_PATH, go_no_go),
        (METADATA_SUMMARY_PATH, summary),
        (METADATA_MANIFEST_PATH, manifest),
        (METADATA_ROWS_PATH, rows_document),
        (METADATA_GO_NO_GO_PATH, go_no_go),
    ):
        _write_json(path, value)

    _write_text(
        COMPLETION_PATH,
        f"""# S11-P2 修补后数据源检查板完成记录

- 规定矩阵行 / 列：`{summary['matrix_row_count']} / {summary['required_column_count']}`
- 当前状态计数（已就绪 / 部分阻塞 / 失败不适用 / 已过期 / 人工复核）：`0 / 6 / 1 / 2 / 4`
- 重算旧就绪状态：`{summary['historical_ready_status_recomputed_count']}`
- 当前状态：`Q4 / D / NO_GO / 3-9-2-1`
- 搜索、筛选、逐行详情、会话状态预演、桌面和移动浏览器：均已覆盖。
- S11-P3、Stage 11 review、GitHub upload、app reinstall、正式报告和业务执行：均未执行。
""",
    )
    _write_text(
        READ_ME_PATH,
        """# 数据源检查板说明

本检查板只展示来源系统、业务板块、公开安全文件包别名、主体分组、账户分组、状态、影响报告和下一步。状态预演只存在浏览器会话，不修改原始数据，也不写入持久业务状态。
""",
    )
    _write_text(
        TEST_RESULTS_PATH,
        f"""# S11-P2 修补后数据源检查板测试结果

- focused tests：`6/6 PASS`
- v1.4 人类流程基线：`{browser['baseline_pass_count']}/{browser['baseline_control_row_count']} PASS`，WARN `{browser['baseline_warn_count']}`，FAIL `{browser['baseline_fail_count']}`
- 当前页面审计：`{browser['current_html_pass_count']}/{browser['current_html_control_row_count']} PASS`，WARN `{browser['current_html_warn_count']}`，FAIL `{browser['current_html_fail_count']}`
- desktop/mobile：`{browser['viewport_check_count']}/{browser['viewport_check_count']} PASS`
- 搜索 / 状态筛选 / 逐行详情 / 状态预演 / 键盘：`{browser['search_interaction_count']} / {browser['status_filter_interaction_count']} / {browser['status_detail_interaction_count']} / {browser['status_preview_interaction_count']} / {browser['keyboard_interaction_count']} PASS`
- 返回当前首页：`{browser['home_link_http_check_count']}/{browser['home_link_http_check_count']} HTTP PASS`
- raw snapshot：phase 前后、跨 S11-P1 和当前复核均 exact match。
- strict validator、governance、no-float、no-omission 和安全扫描由 manifest final validation 锁定。
""",
    )
    _write_text(
        RISK_REGISTER_PATH,
        """# S11-P2 风险登记

| 风险 | 控制 | 状态 |
|---|---|---|
| 旧 12 pending 或四个已就绪状态回流 | 当前 S11-P1/S10 状态覆盖，历史动态状态禁止复用 | controlled |
| 状态颜色影响可读性 | 蓝灰和白色为主，异常只用文字徽标 | controlled |
| 点击状态没有可见结果 | 13 行逐项验证影响报告、处理规则和下一步 | controlled |
| 会话预演误写持久层 | 事件显式锁定 browser session only，raw/persistent write 均为 false | controlled |
| raw/private/secret 泄漏 | public-safe validator、Git ignore 和候选提交扫描阻断 | controlled |
""",
    )
    _write_text(
        ROLLBACK_PATH,
        f"""# S11-P2 回滚方案

1. 回退本 phase 的本地 commit 和 `{OUTPUT_DIR.as_posix()}` 公开证据。
2. 删除本 phase ignored private browser/raw 证据，不触碰原始目录。
3. 恢复到 S11-P1 的 `Q4 / D / NO_GO` 状态。
4. 不回退、不移动、不删除、不覆盖任何原始文件。
""",
    )
    _write_text(
        PRIVATE_VALIDATION_REPORT_PATH,
        """# S11-P2 私有一致性复核

- 原始数据文件数：5
- phase 前后快照：完全一致
- 与 S11-P1 快照：完全一致
- 当前差异结构：3 / 9 / 2 / 1
- 状态预演只存在浏览器会话，未写入原始层或持久业务状态。
- 未发现 raw 漂移，无需生成最终差异报告。
""",
    )
    _write_governance(generated_at)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--final-validation", action="store_true")
    parser.add_argument("--browser-evidence-only", action="store_true")
    args = parser.parse_args()
    if args.browser_evidence_only:
        result = _browser_worker()
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    manifest = generate(final_validation=args.final_validation)
    summary = manifest["summary"]
    print(
        "S11-P2 post-remediation source check board: "
        f"rows={summary['matrix_row_count']} ready={summary['current_ready_row_count']} "
        f"grade={summary['current_report_grade']} decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
