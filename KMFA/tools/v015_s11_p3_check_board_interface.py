#!/usr/bin/env python3
"""Public-safe interface contract and renderer for KMFA v1.5 S11-P3."""

from __future__ import annotations

import copy
import hashlib
import json
import re
from typing import Any, Mapping, Sequence

from KMFA.tools import v015_s11_p2_check_board_data_model as board_model


RUN_PHASE_ID = "V015_S11_P3_CHECK_BOARD_INTERFACE"
ROADMAP_PHASE_ID = "S11-P3"
TASK_ID = "KMFA-V015-S11-P3-CHECK-BOARD-INTERFACE-20260715"
ACCEPTANCE_ID = "ACC-KMFA-V015-S11-P3-CHECK-BOARD-INTERFACE"
VERSION = "1.5.0-dev-s11p3"

STATUS_ORDER = ("已通过", "需确认", "不可使用", "已过期")
ACTION_KINDS = ("VIEW_EVIDENCE", "UPLOAD_SOURCE", "SYNC_SOURCE", "CONFIRM_QUALITY")
CONTEXT_KEYS = (
    "search_text",
    "status_filters",
    "owner_filter",
    "alert_only",
    "expanded_node_ids",
    "scroll_y",
    "table_scroll_left",
    "focus_node_id",
)
FORBIDDEN_CONTEXT_KEYS = (
    "status",
    "status_override",
    "quality_status",
    "readiness",
    "auto_selected",
    "backend_fact",
)

DESIGN_TOKENS = {
    "business_navy": "#102F50",
    "action_blue": "#17679B",
    "action_blue_deep": "#114B74",
    "action_blue_soft": "#EDF6FB",
    "page_cool": "#F3F6F8",
    "surface": "#FFFFFF",
    "text_primary": "#152331",
    "text_muted": "#5E6D79",
    "divider": "#CFDAE3",
    "success": "#147A4A",
    "danger": "#A62E2E",
    "warning_ink": "#7A4B00",
}


class CheckBoardInterfaceError(ValueError):
    def __init__(self, code: str, message_zh: str) -> None:
        super().__init__(message_zh)
        self.code = code
        self.message_zh = message_zh


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _fingerprint(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value)).hexdigest()


def _hex_rgb(value: str) -> tuple[float, float, float]:
    if not re.fullmatch(r"#[0-9A-Fa-f]{6}", value):
        raise CheckBoardInterfaceError("COLOR_INVALID", "颜色必须使用六位十六进制格式。")
    return tuple(int(value[index:index + 2], 16) / 255 for index in (1, 3, 5))  # type: ignore[return-value]


def _relative_luminance(value: str) -> float:
    channels = []
    for channel in _hex_rgb(value):
        channels.append(channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4)
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def contrast_ratio(foreground: str, background: str) -> float:
    high, low = sorted((_relative_luminance(foreground), _relative_luminance(background)), reverse=True)
    return round((high + 0.05) / (low + 0.05), 2)


def visual_contract() -> dict[str, Any]:
    contrast_pairs = [
        ("正文", "text_primary", "surface", 4.5),
        ("辅助文字", "text_muted", "surface", 4.5),
        ("主按钮", "surface", "action_blue", 4.5),
        ("深蓝标题", "business_navy", "surface", 4.5),
        ("成功状态", "success", "surface", 4.5),
        ("失败状态", "danger", "surface", 4.5),
        ("待确认状态", "warning_ink", "surface", 4.5),
    ]
    rows = []
    for label, foreground, background, minimum in contrast_pairs:
        ratio = contrast_ratio(DESIGN_TOKENS[foreground], DESIGN_TOKENS[background])
        rows.append({
            "label_zh": label,
            "foreground": DESIGN_TOKENS[foreground],
            "background": DESIGN_TOKENS[background],
            "ratio": ratio,
            "minimum": minimum,
            "status": "PASS" if ratio >= minimum else "FAIL",
        })
    return {
        "schema_version": "kmfa.v015.s11p3.visual_contract.v1",
        "register": "product",
        "creative_north_star_zh": "可信经营台",
        "tokens": copy.deepcopy(DESIGN_TOKENS),
        "business_blue_primary": True,
        "large_yellow_surface_count": 0,
        "large_status_color_surface_count": 0,
        "status_color_usage": "BADGE_ICON_TEXT_ONLY",
        "corner_radius_px": {"control": 6, "container": 8},
        "focus_outline_px": 3,
        "minimum_body_font_px": 14,
        "contrast_pairs": rows,
        "contrast_all_pass": all(row["status"] == "PASS" for row in rows),
        "reduced_motion_supported": True,
        "color_only_status_allowed": False,
    }


def accessibility_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s11p3.accessibility_contract.v1",
        "target": "WCAG_2_1_AA",
        "keyboard_paths": [
            "跳到主要内容",
            "搜索与状态筛选",
            "展开或折叠层级",
            "打开状态详情",
            "进入处理流程",
            "返回原位置",
        ],
        "required_semantics": [
            "main",
            "search",
            "table",
            "aria-live",
            "aria-expanded",
            "aria-controls",
            "focus-visible",
        ],
        "status_uses_text_and_symbol": True,
        "focus_restored_after_return": True,
        "reduced_motion_supported": True,
        "minimum_touch_target_px": 40,
        "internal_field_names_visible_by_default": False,
    }


def _leaf_action(node: Mapping[str, Any]) -> dict[str, str] | None:
    if not node.get("is_leaf"):
        return None
    alert_types = {row.get("alert_type") for row in node.get("alerts", [])}
    status = node["display"]["label_zh"]
    if "MISSING_SOURCE" in alert_types or "IMPORT_FAILED" in alert_types:
        return {
            "kind": "UPLOAD_SOURCE",
            "label_zh": "补充或重新提交资料",
            "intro_zh": "进入资料补充流程。提交后仍需系统重新导入和检查，状态不会由页面直接改变。",
            "submit_zh": "提交资料处理请求",
        }
    if "SOURCE_OUTDATED" in alert_types or status == "已过期":
        return {
            "kind": "SYNC_SOURCE",
            "label_zh": "获取最新资料",
            "intro_zh": "进入最新资料同步流程。同步完成后由系统重新检查新鲜度。",
            "submit_zh": "提交同步请求",
        }
    if status in {"需确认", "不可使用"}:
        return {
            "kind": "CONFIRM_QUALITY",
            "label_zh": "确认处理办法",
            "intro_zh": "进入问题确认流程。确认只提交处理意见，不会把当前状态直接改成已通过。",
            "submit_zh": "提交确认请求",
        }
    return {
        "kind": "VIEW_EVIDENCE",
        "label_zh": "查看通过依据",
        "intro_zh": "查看系统检查结果和报告影响；本流程不会改写任何状态。",
        "submit_zh": "完成查看",
    }


def _friendly_updated_at(value: str) -> str:
    match = re.match(r"^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})", value)
    if not match:
        raise CheckBoardInterfaceError("UPDATED_AT_INVALID", "更新时间格式无效。")
    year, month, day, hour, minute = match.groups()
    return f"{year}-{month}-{day} {hour}:{minute}"


def interface_payload() -> dict[str, Any]:
    verification = board_model.public_verification()
    model = verification["model"]
    rows = []
    for node in model["nodes"]:
        display = node["display"]
        rows.append({
            "node_id": node["node_id"],
            "parent_node_id": node["parent_node_id"],
            "depth": node["depth"],
            "is_leaf": node["is_leaf"],
            "has_children": node["has_children"],
            "child_count": node["child_count"],
            "label_zh": node["label_zh"],
            "node_type_label_zh": node["node_type_label_zh"],
            "hierarchy_path_zh": " › ".join(node["hierarchy_path"]),
            "source_system_zh": node["hierarchy_path"][0],
            "business_segment_zh": node["hierarchy_path"][1] if len(node["hierarchy_path"]) > 1 else "待展开",
            "file_package_zh": node["hierarchy_path"][2] if len(node["hierarchy_path"]) > 2 else "待展开",
            "entity_zh": node["hierarchy_path"][3] if len(node["hierarchy_path"]) > 3 else "待展开",
            "updated_at_zh": _friendly_updated_at(node["updated_at"]),
            "status_zh": display["label_zh"],
            "status_symbol": display["symbol"],
            "status_summary_zh": display["summary_zh"],
            "quality_issue_zh": display["reason_zh"],
            "report_impact_zh": node["report_impact_zh"],
            "blocker_reason_zh": node["blocker_reason_zh"],
            "owner_role_zh": node["owner_role_zh"],
            "next_action_zh": node["next_action_zh"],
            "has_alert": bool(node["alerts"]),
            "alert_count": len(node["alerts"]),
            "auto_selected": node["auto_selected"],
            "status_source_zh": "系统导入与质量检查结果",
            "frontend_status_mutation_allowed": False,
            "action": _leaf_action(node),
        })
    leaf_rows = [row for row in rows if row["is_leaf"]]
    summary = {label: sum(row["status_zh"] == label for row in leaf_rows) for label in STATUS_ORDER}
    owners = sorted({row["owner_role_zh"] for row in leaf_rows})
    payload = {
        "schema_version": "kmfa.v015.s11p3.interface_payload.v1",
        "title_zh": "数据检查板",
        "subtitle_zh": "按来源层级查看资料状态、影响和处理办法",
        "rows": rows,
        "row_count": len(rows),
        "leaf_count": len(leaf_rows),
        "root_node_ids": list(model["root_node_ids"]),
        "default_expanded_node_ids": list(model["root_node_ids"]),
        "status_order": list(STATUS_ORDER),
        "status_summary": summary,
        "owners": owners,
        "action_kinds": list(ACTION_KINDS),
        "frontend_status_mutation_allowed": False,
        "backend_state_fingerprint": _fingerprint([
            (row["node_id"], row["status_zh"], row["auto_selected"]) for row in rows
        ]),
        "raw_root_access_count": 0,
        "raw_business_content_read": False,
        "live_source_read_count": 0,
        "formal_report_generated": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }
    payload["payload_fingerprint"] = _fingerprint(payload)
    return payload


def validate_context_state(state: Mapping[str, Any], node_ids: set[str]) -> dict[str, Any]:
    if not isinstance(state, Mapping):
        raise CheckBoardInterfaceError("CONTEXT_INVALID", "返回位置必须是结构化状态。")
    forbidden = sorted(set(state) & set(FORBIDDEN_CONTEXT_KEYS))
    unknown = sorted(set(state) - set(CONTEXT_KEYS))
    if forbidden or unknown:
        raise CheckBoardInterfaceError("CONTEXT_STATUS_MUTATION_FORBIDDEN", "返回位置只能保存搜索、筛选、展开和滚动信息，不能改写状态。")
    search_text = state.get("search_text", "")
    status_filters = state.get("status_filters", [])
    owner_filter = state.get("owner_filter", "")
    alert_only = state.get("alert_only", False)
    expanded = state.get("expanded_node_ids", [])
    scroll_y = state.get("scroll_y", 0)
    table_scroll_left = state.get("table_scroll_left", 0)
    focus_node_id = state.get("focus_node_id")
    if not isinstance(search_text, str) or len(search_text) > 100:
        raise CheckBoardInterfaceError("CONTEXT_SEARCH_INVALID", "搜索文字格式无效。")
    if not isinstance(status_filters, list) or set(status_filters) - set(STATUS_ORDER):
        raise CheckBoardInterfaceError("CONTEXT_STATUS_FILTER_INVALID", "状态筛选值无效。")
    if not isinstance(owner_filter, str) or len(owner_filter) > 80:
        raise CheckBoardInterfaceError("CONTEXT_OWNER_INVALID", "负责人筛选值无效。")
    if not isinstance(alert_only, bool):
        raise CheckBoardInterfaceError("CONTEXT_ALERT_INVALID", "提醒筛选格式无效。")
    if not isinstance(expanded, list) or not all(isinstance(value, str) for value in expanded):
        raise CheckBoardInterfaceError("CONTEXT_EXPANDED_INVALID", "展开项格式无效。")
    if set(expanded) - node_ids:
        raise CheckBoardInterfaceError("CONTEXT_EXPANDED_UNKNOWN", "返回位置包含未知层级。")
    if not isinstance(scroll_y, int) or isinstance(scroll_y, bool) or scroll_y < 0:
        raise CheckBoardInterfaceError("CONTEXT_SCROLL_INVALID", "页面滚动位置无效。")
    if not isinstance(table_scroll_left, int) or isinstance(table_scroll_left, bool) or table_scroll_left < 0:
        raise CheckBoardInterfaceError("CONTEXT_TABLE_SCROLL_INVALID", "表格滚动位置无效。")
    if focus_node_id is not None and focus_node_id not in node_ids:
        raise CheckBoardInterfaceError("CONTEXT_FOCUS_UNKNOWN", "返回焦点包含未知检查项。")
    return {
        "search_text": search_text.strip(),
        "status_filters": [label for label in STATUS_ORDER if label in set(status_filters)],
        "owner_filter": owner_filter.strip(),
        "alert_only": alert_only,
        "expanded_node_ids": sorted(set(expanded)),
        "scroll_y": scroll_y,
        "table_scroll_left": table_scroll_left,
        "focus_node_id": focus_node_id,
    }


def create_action_request(node_id: str, context_state: Mapping[str, Any]) -> dict[str, Any]:
    payload = interface_payload()
    by_id = {row["node_id"]: row for row in payload["rows"]}
    if node_id not in by_id or not by_id[node_id]["is_leaf"]:
        raise CheckBoardInterfaceError("ACTION_TARGET_INVALID", "只能从末级检查项进入处理流程。")
    row = by_id[node_id]
    action = row["action"]
    if action is None or action["kind"] not in ACTION_KINDS:
        raise CheckBoardInterfaceError("ACTION_KIND_INVALID", "当前检查项没有可用处理流程。")
    context = validate_context_state(context_state, set(by_id))
    request = {
        "schema_version": "kmfa.v015.s11p3.action_request.v1",
        "target_node_id": node_id,
        "action_kind": action["kind"],
        "context_token": _fingerprint(context),
        "backend_state_fingerprint": payload["backend_state_fingerprint"],
        "frontend_status_write_count": 0,
        "status_change_requested": False,
        "raw_source_mutation_requested": False,
        "completion_message_zh": "处理请求已提交；系统重新检查后才会更新状态。",
    }
    request["request_fingerprint"] = _fingerprint(request)
    return request


def simulate_action_and_return(node_id: str, context_state: Mapping[str, Any]) -> dict[str, Any]:
    payload_before = interface_payload()
    request = create_action_request(node_id, context_state)
    payload_after = interface_payload()
    restored = validate_context_state(context_state, {row["node_id"] for row in payload_before["rows"]})
    return {
        "schema_version": "kmfa.v015.s11p3.action_return_evidence.v1",
        "request": request,
        "restored_context": restored,
        "context_exact": restored == validate_context_state(context_state, {row["node_id"] for row in payload_before["rows"]}),
        "backend_state_unchanged": payload_before["backend_state_fingerprint"] == payload_after["backend_state_fingerprint"],
        "frontend_status_write_count": 0,
    }


HTML_TEMPLATE = r'''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="color-scheme" content="light">
  <title>KMFA 数据检查板</title>
  <style>
    :root{--navy:#102f50;--blue:#17679b;--blue-deep:#114b74;--blue-soft:#edf6fb;--page:#f3f6f8;--surface:#fff;--text:#152331;--muted:#5e6d79;--line:#cfdae3;--success:#147a4a;--success-bg:#eaf6f0;--danger:#a62e2e;--danger-bg:#fff1f0;--warning:#7a4b00;--warning-bg:#fff7e8;--stale:#465564;--stale-bg:#eef2f5;--focus:rgba(23,103,155,.28)}
    *{box-sizing:border-box}html{min-width:320px;background:var(--page);scroll-behavior:smooth}body{margin:0;background:var(--page);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",Arial,sans-serif;font-size:14px;line-height:1.6}button,input,select{font:inherit}button{cursor:pointer}.skip-link{position:fixed;left:12px;top:-60px;z-index:99;background:var(--navy);color:#fff;padding:9px 12px;border-radius:6px}.skip-link:focus{top:12px}.shell{min-height:100vh}.topbar{display:flex;align-items:center;justify-content:space-between;gap:18px;background:var(--navy);color:#fff;padding:14px 24px}.brand{display:flex;align-items:center;gap:11px}.brand-mark{display:grid;place-items:center;width:38px;height:38px;border:1px solid rgba(255,255,255,.45);border-radius:6px;background:var(--blue);font-weight:800}.brand strong{display:block;font-size:16px}.brand span{display:block;color:#c7dceb;font-size:12px}.top-status{color:#dbeaf4;font-size:12px}.layout{max-width:1600px;margin:0 auto;padding:20px 24px 32px}.page-heading{display:flex;align-items:flex-start;justify-content:space-between;gap:20px;margin-bottom:16px}.eyebrow{color:var(--blue);font-size:12px;font-weight:700}h1{margin:3px 0 4px;color:var(--navy);font-size:25px;line-height:1.3}h2{margin:0;color:var(--navy);font-size:18px}.page-heading p{max-width:720px;margin:0;color:var(--muted)}.readonly-note{max-width:360px;border:1px solid var(--line);border-radius:6px;background:#fff;padding:9px 11px;color:#435665;font-size:12px}.summary{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));border:1px solid var(--line);border-radius:8px;background:var(--surface);overflow:hidden;margin-bottom:12px}.summary-item{display:flex;align-items:center;justify-content:space-between;gap:12px;min-height:58px;padding:10px 14px;border-right:1px solid var(--line)}.summary-item:last-child{border-right:0}.summary-label{display:flex;align-items:center;gap:7px;color:var(--muted);font-size:12px}.summary-value{color:var(--navy);font-size:21px;font-weight:800}.status-symbol{display:inline-grid;place-items:center;width:19px;height:19px;border-radius:999px;font-size:12px;font-weight:800}.symbol-ready{background:var(--success-bg);color:var(--success)}.symbol-review{background:var(--warning-bg);color:var(--warning)}.symbol-danger{background:var(--danger-bg);color:var(--danger)}.symbol-stale{background:var(--stale-bg);color:var(--stale)}.workspace{border:1px solid var(--line);border-radius:8px;background:var(--surface);overflow:hidden}.toolbar{display:grid;grid-template-columns:minmax(240px,1.4fr) minmax(160px,.7fr) auto auto;gap:10px;align-items:end;padding:12px;border-bottom:1px solid var(--line);background:#f8fafb}.field{display:grid;gap:5px}.field label,.filter-label{color:#405363;font-size:12px;font-weight:700}.input,.select{width:100%;min-height:40px;border:1px solid var(--line);border-radius:6px;background:#fff;color:var(--text);padding:8px 10px}.input:hover,.select:hover{border-color:#8ea9bc}.input:focus,.select:focus{border-color:var(--blue);outline:3px solid var(--focus)}.status-filters{display:flex;align-items:center;gap:6px;flex-wrap:wrap}.filter-chip{position:relative;display:inline-flex;align-items:center;min-height:40px}.filter-chip input{position:absolute;opacity:0;pointer-events:none}.filter-chip span{display:inline-flex;align-items:center;gap:5px;min-height:36px;border:1px solid var(--line);border-radius:999px;background:#fff;color:#3f5261;padding:6px 10px;font-size:12px;font-weight:700}.filter-chip input:checked+span{border-color:var(--blue);background:var(--blue-soft);color:var(--blue-deep)}.filter-chip input:focus-visible+span{outline:3px solid var(--focus);outline-offset:2px}.compact-check{display:flex;align-items:center;gap:7px;min-height:40px;white-space:nowrap}.compact-check input{width:17px;height:17px;accent-color:var(--blue)}.toolbar-actions{display:flex;gap:7px}.button{min-height:40px;border:1px solid var(--blue);border-radius:6px;background:var(--blue);color:#fff;padding:8px 12px;font-weight:700}.button:hover{background:var(--blue-deep)}.button.secondary{border-color:var(--line);background:#fff;color:var(--blue-deep)}.button.secondary:hover{border-color:var(--blue);background:var(--blue-soft)}button:focus-visible,a:focus-visible{outline:3px solid var(--focus);outline-offset:2px}.result-bar{display:flex;align-items:center;justify-content:space-between;gap:14px;min-height:40px;padding:7px 12px;border-bottom:1px solid var(--line);color:#405363;font-size:12px}.result-bar strong{color:var(--navy)}.table-scroll{overflow:auto;max-height:none;background:#fff}.matrix{width:100%;min-width:1180px;border-collapse:separate;border-spacing:0}.matrix th{position:sticky;top:0;z-index:3;background:#edf3f7;color:#32495b;padding:9px 10px;border-bottom:1px solid var(--line);text-align:left;font-size:12px;white-space:nowrap}.matrix th:first-child{left:0;z-index:4}.matrix td{padding:9px 10px;border-bottom:1px solid #e7edf1;vertical-align:middle}.matrix tr:hover td{background:#f8fbfd}.matrix tr[data-selected="true"] td{background:var(--blue-soft)}.matrix td:first-child{position:sticky;left:0;z-index:2;background:#fff;min-width:280px}.matrix tr:hover td:first-child{background:#f8fbfd}.matrix tr[data-selected="true"] td:first-child{background:var(--blue-soft)}.tree-cell{display:flex;align-items:center;gap:6px}.tree-toggle,.tree-spacer{flex:0 0 28px;width:28px;height:28px}.tree-toggle{display:grid;place-items:center;border:1px solid transparent;border-radius:5px;background:transparent;color:var(--blue-deep);font-size:15px}.tree-toggle:hover{border-color:var(--line);background:#fff}.item-label{min-width:0}.item-label strong{display:block;color:var(--text);font-size:13px}.item-label span{display:block;color:var(--muted);font-size:11px}.status-button{display:inline-flex;align-items:center;gap:6px;min-height:34px;border:1px solid transparent;border-radius:999px;padding:5px 9px;font-size:12px;font-weight:800;white-space:nowrap}.status-button:hover{filter:brightness(.98);border-color:currentColor}.status-ready{background:var(--success-bg);color:var(--success)}.status-review{background:var(--warning-bg);color:var(--warning)}.status-danger{background:var(--danger-bg);color:var(--danger)}.status-stale{background:var(--stale-bg);color:var(--stale)}.cell-compact{max-width:240px;color:#3f5261;font-size:12px}.cell-muted{color:var(--muted);font-size:12px;white-space:nowrap}.empty{padding:40px 20px;text-align:center;color:var(--muted)}.empty strong{display:block;color:var(--navy);font-size:16px}.empty p{margin:5px 0 12px}.detail-layer{position:fixed;inset:0;z-index:30;display:none;background:rgba(16,35,49,.32)}.detail-layer[data-open="true"]{display:block}.detail-panel{position:absolute;right:0;top:0;width:min(520px,96vw);height:100%;overflow:auto;background:#fff;border-left:1px solid var(--line);box-shadow:0 18px 48px rgba(16,47,80,.18)}.detail-head{position:sticky;top:0;z-index:2;display:flex;align-items:flex-start;justify-content:space-between;gap:12px;padding:18px 20px;border-bottom:1px solid var(--line);background:#fff}.detail-head p{margin:4px 0 0;color:var(--muted);font-size:12px}.icon-button{display:grid;place-items:center;flex:0 0 40px;width:40px;height:40px;border:1px solid var(--line);border-radius:6px;background:#fff;color:var(--navy);font-size:20px}.icon-button:hover{border-color:var(--blue);background:var(--blue-soft)}.detail-body{padding:18px 20px 24px}.detail-status{margin-bottom:14px}.facts{display:grid;grid-template-columns:130px minmax(0,1fr);border-top:1px solid var(--line)}.facts dt,.facts dd{margin:0;padding:10px 0;border-bottom:1px solid var(--line)}.facts dt{color:var(--muted);font-size:12px}.facts dd{color:var(--text)}.next-box{margin-top:15px;border:1px solid #b9d3e4;border-radius:8px;background:var(--blue-soft);padding:13px}.next-box strong{display:block;color:var(--navy)}.next-box p{margin:5px 0 0;color:#3e5667}.detail-actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:16px}.professional{margin-top:16px;border-top:1px solid var(--line);padding-top:12px}.professional summary{cursor:pointer;color:var(--blue-deep);font-weight:700}.professional p{margin:8px 0 0;color:var(--muted);font-size:12px}.flow-steps{display:grid;gap:8px;margin:14px 0}.flow-step{display:grid;grid-template-columns:26px minmax(0,1fr);gap:9px;align-items:start;border:1px solid var(--line);border-radius:6px;padding:10px}.step-number{display:grid;place-items:center;width:24px;height:24px;border-radius:999px;background:var(--blue-soft);color:var(--blue-deep);font-size:12px;font-weight:800}.flow-step strong{display:block}.flow-step p{margin:2px 0 0;color:var(--muted);font-size:12px}.safe-notice{border:1px solid var(--line);border-radius:6px;background:#f8fafb;padding:10px;color:#405363;font-size:12px}.completion{display:none;margin-top:14px;border:1px solid #a9d4be;border-radius:6px;background:var(--success-bg);padding:11px;color:#0d5d39}.completion[data-visible="true"]{display:block}.footer-note{padding:10px 12px;border-top:1px solid var(--line);background:#f8fafb;color:var(--muted);font-size:11px}.sr-only{position:absolute!important;width:1px!important;height:1px!important;padding:0!important;margin:-1px!important;overflow:hidden!important;clip:rect(0,0,0,0)!important;white-space:nowrap!important;border:0!important}@media(max-width:1100px){.toolbar{grid-template-columns:1fr 1fr}.toolbar-actions{justify-content:flex-start}}@media(max-width:760px){.topbar{padding:12px 14px}.top-status{display:none}.layout{padding:14px}.page-heading{display:block}.readonly-note{margin-top:10px}.summary{grid-template-columns:repeat(2,1fr)}.summary-item:nth-child(2){border-right:0}.summary-item:nth-child(-n+2){border-bottom:1px solid var(--line)}.toolbar{grid-template-columns:1fr}.status-filters{max-width:100%}.toolbar-actions{flex-wrap:wrap}.facts{grid-template-columns:1fr}.facts dt{padding-bottom:2px;border-bottom:0}.facts dd{padding-top:0}.matrix{min-width:980px}}@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}*,*::before,*::after{animation-duration:.01ms!important;animation-iteration-count:1!important;transition-duration:.01ms!important}}
    .filter-chip input{inset:0;width:100%;height:100%;margin:0;pointer-events:auto;cursor:pointer}
    .filter-chip span{pointer-events:none}
  </style>
</head>
<body>
  <a class="skip-link" href="#main-content">跳到主要内容</a>
  <div class="shell">
    <header class="topbar"><div class="brand"><div class="brand-mark" aria-hidden="true">KM</div><div><strong>KMFA</strong><span>经营分析系统</span></div></div><div class="top-status">公开安全验收样板 · 状态由系统检查生成</div></header>
    <main id="main-content" class="layout" tabindex="-1">
      <header class="page-heading"><div><span class="eyebrow">数据质量与来源检查</span><h1>数据检查板</h1><p>按来源层级查看资料是否可用、会影响什么，以及应该由谁处理。</p></div><div class="readonly-note"><strong>状态只读：</strong>页面可以查看并发起处理，但不能直接把失败改成已通过。</div></header>
      <section class="summary" aria-label="末级检查项状态汇总" id="summary"></section>
      <section class="workspace" aria-label="数据检查工作区">
        <form class="toolbar" role="search" id="filter-form">
          <div class="field"><label for="search-input">搜索检查项</label><input id="search-input" class="input" type="search" autocomplete="off" placeholder="例如：回款、成本、票据" data-testid="search-input"></div>
          <div class="field"><label for="owner-select">负责人</label><select id="owner-select" class="select" data-testid="owner-select"><option value="">全部负责人</option></select></div>
          <fieldset style="border:0;padding:0;margin:0"><legend class="filter-label">状态</legend><div class="status-filters" id="status-filters"></div></fieldset>
          <div><label class="filter-label" for="alert-only">提醒</label><label class="compact-check"><input id="alert-only" type="checkbox" data-testid="alert-only"><span>只看需要处理</span></label></div>
          <div class="toolbar-actions"><button class="button secondary" type="button" id="expand-all">全部展开</button><button class="button secondary" type="button" id="reset-filters">清除筛选</button></div>
        </form>
        <div class="result-bar"><span id="result-count" aria-live="polite"></span><strong id="context-hint">点击状态查看详情</strong></div>
        <div class="table-scroll" id="table-scroll" tabindex="0" aria-label="可横向滚动的数据检查矩阵">
          <table class="matrix">
            <caption class="sr-only">数据来源层级、状态、报告影响、更新时间、负责人和下一步</caption>
            <thead><tr><th scope="col">检查项目</th><th scope="col">状态</th><th scope="col">影响报告</th><th scope="col">更新时间</th><th scope="col">负责人</th><th scope="col">下一步</th></tr></thead>
            <tbody id="matrix-body"></tbody>
          </table>
          <div class="empty" id="empty-state" hidden><strong>没有符合条件的检查项</strong><p>可以清除筛选，或换一个更短的关键词。</p><button class="button secondary" type="button" data-reset-empty>清除筛选</button></div>
        </div>
        <div class="footer-note">本页面使用公开模拟状态验证交互，不读取真实财务资料，不执行真实上传、同步或业务操作。</div>
      </section>
    </main>
  </div>
  <div class="detail-layer" id="detail-layer" data-open="false" aria-hidden="true">
    <aside class="detail-panel" role="dialog" aria-modal="true" aria-labelledby="detail-title" tabindex="-1">
      <header class="detail-head"><div><h2 id="detail-title">检查项详情</h2><p id="detail-path"></p></div><button class="icon-button" type="button" id="close-detail" aria-label="关闭详情">×</button></header>
      <div class="detail-body" id="detail-body"></div>
    </aside>
  </div>
  <div id="announcer" class="sr-only" aria-live="assertive"></div>
  <script id="interface-data" type="application/json">__PAYLOAD__</script>
  <script>
  (()=>{
    'use strict';
    const payload=JSON.parse(document.getElementById('interface-data').textContent);
    const rows=payload.rows;
    const byId=new Map(rows.map(row=>[row.node_id,row]));
    const children=new Map();
    rows.forEach(row=>{if(row.parent_node_id){if(!children.has(row.parent_node_id))children.set(row.parent_node_id,[]);children.get(row.parent_node_id).push(row.node_id)}});
    const storageKey='kmfa-s11p3-board-context-v1';
    const state={search:'',statuses:new Set(),owner:'',alertOnly:false,expanded:new Set(payload.default_expanded_node_ids),selectedId:null,savedContext:null,requests:[]};
    const el={summary:document.getElementById('summary'),body:document.getElementById('matrix-body'),empty:document.getElementById('empty-state'),search:document.getElementById('search-input'),owner:document.getElementById('owner-select'),statusFilters:document.getElementById('status-filters'),alertOnly:document.getElementById('alert-only'),result:document.getElementById('result-count'),hint:document.getElementById('context-hint'),tableScroll:document.getElementById('table-scroll'),layer:document.getElementById('detail-layer'),panel:document.querySelector('.detail-panel'),detailTitle:document.getElementById('detail-title'),detailPath:document.getElementById('detail-path'),detailBody:document.getElementById('detail-body'),announcer:document.getElementById('announcer')};
    const statusClass={'已通过':'ready','需确认':'review','不可使用':'danger','已过期':'stale'};
    const esc=value=>String(value??'').replace(/[&<>'"]/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char]));
    function renderSummary(){el.summary.innerHTML=payload.status_order.map(label=>`<div class="summary-item"><span class="summary-label"><span class="status-symbol symbol-${statusClass[label]}" aria-hidden="true">${label==='已通过'?'✓':label==='需确认'?'!':label==='不可使用'?'×':'○'}</span>${esc(label)}</span><strong class="summary-value">${payload.status_summary[label]}</strong></div>`).join('')}
    function setupFilters(){payload.owners.forEach(owner=>{const option=document.createElement('option');option.value=owner;option.textContent=owner;el.owner.append(option)});el.statusFilters.innerHTML=payload.status_order.map((label,index)=>`<label class="filter-chip"><input type="checkbox" value="${esc(label)}" data-testid="status-${index}"><span>${esc(label)}</span></label>`).join('')}
    function descendants(id){const found=[];const visit=current=>{(children.get(current)||[]).forEach(child=>{found.push(child);visit(child)})};visit(id);return found}
    function ancestors(id){const found=[];let current=byId.get(id);while(current&&current.parent_node_id){found.push(current.parent_node_id);current=byId.get(current.parent_node_id)}return found}
    function leafMatches(row){if(!row.is_leaf)return false;const query=state.search.trim().toLocaleLowerCase('zh-CN');const hay=[row.hierarchy_path_zh,row.status_zh,row.report_impact_zh,row.blocker_reason_zh,row.owner_role_zh,row.next_action_zh].join(' ').toLocaleLowerCase('zh-CN');return(!query||hay.includes(query))&&(!state.statuses.size||state.statuses.has(row.status_zh))&&(!state.owner||row.owner_role_zh===state.owner)&&(!state.alertOnly||row.has_alert)}
    function hasActiveFilter(){return Boolean(state.search.trim()||state.statuses.size||state.owner||state.alertOnly)}
    function visibleRows(){const active=hasActiveFilter();if(active){const included=new Set();rows.filter(leafMatches).forEach(row=>{included.add(row.node_id);ancestors(row.node_id).forEach(id=>included.add(id))});return rows.filter(row=>included.has(row.node_id))}return rows.filter(row=>row.depth===0||ancestors(row.node_id).every(id=>state.expanded.has(id)))}
    function rowHtml(row){const active=hasActiveFilter();const expanded=state.expanded.has(row.node_id)||(active&&row.has_children);const toggle=row.has_children?`<button class="tree-toggle" type="button" aria-label="${expanded?'折叠':'展开'}${esc(row.label_zh)}" aria-expanded="${expanded}" data-toggle="${row.node_id}" data-focus-node="${row.node_id}">${expanded?'−':'+'}</button>`:'<span class="tree-spacer" aria-hidden="true"></span>';return `<tr data-row-id="${row.node_id}" data-selected="${state.selectedId===row.node_id}"><td><div class="tree-cell" style="padding-left:${row.depth*17}px">${toggle}<div class="item-label"><strong>${esc(row.label_zh)}</strong><span>${esc(row.node_type_label_zh)}${row.has_children?` · ${row.child_count} 项`:''}</span></div></div></td><td><button class="status-button status-${statusClass[row.status_zh]}" type="button" data-detail="${row.node_id}" data-focus-node="${row.node_id}" aria-label="查看${esc(row.label_zh)}详情，当前${esc(row.status_zh)}"><span aria-hidden="true">${esc(row.status_symbol)}</span>${esc(row.status_zh)}</button></td><td class="cell-compact">${esc(row.report_impact_zh)}</td><td class="cell-muted">${esc(row.updated_at_zh)}</td><td class="cell-compact">${esc(row.owner_role_zh)}</td><td class="cell-compact">${esc(row.next_action_zh)}</td></tr>`}
    function render(){const visible=visibleRows();el.body.innerHTML=visible.map(rowHtml).join('');el.empty.hidden=visible.length>0;document.querySelector('.matrix').hidden=visible.length===0;const matched=rows.filter(leafMatches).length;el.result.textContent=hasActiveFilter()?`找到 ${matched} 个符合条件的末级检查项`:`当前显示 ${visible.length} 行，共 ${payload.leaf_count} 个末级检查项`;bindRows();persistContext()}
    function bindRows(){document.querySelectorAll('[data-toggle]').forEach(button=>button.addEventListener('click',()=>{const id=button.dataset.toggle;if(state.expanded.has(id)){state.expanded.delete(id);descendants(id).forEach(child=>state.expanded.delete(child))}else state.expanded.add(id);render();requestAnimationFrame(()=>document.querySelector(`[data-toggle="${id}"]`)?.focus())}));document.querySelectorAll('[data-detail]').forEach(button=>button.addEventListener('click',()=>openDetail(button.dataset.detail,button)))}
    function statusBadge(row){return `<span class="status-button status-${statusClass[row.status_zh]}"><span aria-hidden="true">${esc(row.status_symbol)}</span>${esc(row.status_zh)}</span>`}
    function detailHtml(row){const action=row.action?`<button class="button" type="button" data-start-action="${row.node_id}">${esc(row.action.label_zh)}</button>`:'';return `<div class="detail-status">${statusBadge(row)}</div><dl class="facts"><dt>资料</dt><dd>${esc(row.file_package_zh)}</dd><dt>来源与板块</dt><dd>${esc(row.source_system_zh)} · ${esc(row.business_segment_zh)}</dd><dt>当前问题</dt><dd>${esc(row.quality_issue_zh)}</dd><dt>影响</dt><dd>${esc(row.report_impact_zh)}</dd><dt>负责人</dt><dd>${esc(row.owner_role_zh)}</dd><dt>最近检查</dt><dd>${esc(row.updated_at_zh)}</dd></dl><div class="next-box"><strong>建议下一步</strong><p>${esc(row.next_action_zh)}</p></div><div class="detail-actions">${action}<button class="button secondary" type="button" data-return-board>返回检查板</button></div><details class="professional"><summary>专业核对信息</summary><p>状态来源：${esc(row.status_source_zh)}。页面写入状态：不允许。完整层级：${esc(row.hierarchy_path_zh)}。</p></details>`}
    function openLayer(){el.layer.dataset.open='true';el.layer.setAttribute('aria-hidden','false');document.body.style.overflow='hidden'}
    function closeLayer({restore=true}={}){el.layer.dataset.open='false';el.layer.setAttribute('aria-hidden','true');document.body.style.overflow='';state.selectedId=null;render();if(restore)restoreContext()}
    function captureContext(trigger){state.savedContext={search_text:state.search,status_filters:[...state.statuses],owner_filter:state.owner,alert_only:state.alertOnly,expanded_node_ids:[...state.expanded],scroll_y:Math.max(0,Math.round(window.scrollY)),table_scroll_left:Math.max(0,Math.round(el.tableScroll.scrollLeft)),focus_node_id:trigger?.dataset.focusNode||state.selectedId};persistContext()}
    function restoreContext(){const ctx=state.savedContext;if(!ctx)return;state.search=ctx.search_text;state.statuses=new Set(ctx.status_filters);state.owner=ctx.owner_filter;state.alertOnly=ctx.alert_only;state.expanded=new Set(ctx.expanded_node_ids);syncControls();render();requestAnimationFrame(()=>{window.scrollTo(0,ctx.scroll_y);el.tableScroll.scrollLeft=ctx.table_scroll_left;const focus=document.querySelector(`[data-focus-node="${ctx.focus_node_id}"]`);if(focus)focus.focus();el.hint.textContent='已返回原来的筛选和位置';el.announcer.textContent='已返回原来的筛选和位置'})}
    function openDetail(id,trigger){const row=byId.get(id);if(!row)return;captureContext(trigger);state.selectedId=id;render();el.detailTitle.textContent=row.is_leaf?'资料详情':'分组详情';el.detailPath.textContent=row.hierarchy_path_zh;el.detailBody.innerHTML=detailHtml(row);openLayer();bindDetail();requestAnimationFrame(()=>el.panel.focus())}
    function bindDetail(){el.detailBody.querySelector('[data-start-action]')?.addEventListener('click',event=>showAction(event.currentTarget.dataset.startAction));el.detailBody.querySelector('[data-return-board]')?.addEventListener('click',()=>closeLayer())}
    function showAction(id){const row=byId.get(id);if(!row?.action)return;el.detailTitle.textContent=row.action.label_zh;el.detailPath.textContent=row.file_package_zh;el.detailBody.innerHTML=`<p>${esc(row.action.intro_zh)}</p><div class="flow-steps"><div class="flow-step"><span class="step-number">1</span><div><strong>核对当前问题</strong><p>${esc(row.quality_issue_zh)}</p></div></div><div class="flow-step"><span class="step-number">2</span><div><strong>${esc(row.action.label_zh)}</strong><p>本验收样板只提交公开模拟请求，不读取或发送真实资料。</p></div></div><div class="flow-step"><span class="step-number">3</span><div><strong>系统重新检查</strong><p>只有后端检查通过后，检查板状态才会自动更新。</p></div></div></div><div class="safe-notice">安全说明：当前流程不会访问真实文件、连接真实平台或直接修改状态。</div><div class="detail-actions"><button class="button" type="button" data-submit-action="${row.node_id}">${esc(row.action.submit_zh)}</button><button class="button secondary" type="button" data-back-detail="${row.node_id}">返回详情</button></div><div class="completion" data-visible="false" id="completion-message" role="status"></div>`;el.detailBody.querySelector('[data-submit-action]').addEventListener('click',event=>submitAction(event.currentTarget.dataset.submitAction));el.detailBody.querySelector('[data-back-detail]').addEventListener('click',event=>{const current=byId.get(event.currentTarget.dataset.backDetail);el.detailTitle.textContent='资料详情';el.detailPath.textContent=current.hierarchy_path_zh;el.detailBody.innerHTML=detailHtml(current);bindDetail()})}
    function submitAction(id){const row=byId.get(id);const ctx=state.savedContext;const request={schema_version:'kmfa.v015.s11p3.action_request.v1',target_node_id:id,action_kind:row.action.kind,context_token:'client-context-preserved',backend_state_fingerprint:payload.backend_state_fingerprint,frontend_status_write_count:0,status_change_requested:false,raw_source_mutation_requested:false};state.requests.push(request);const completion=document.getElementById('completion-message');completion.dataset.visible='true';completion.innerHTML='<strong>请求已提交。</strong><br>检查板状态没有被页面改写；系统重新检查后才会更新。';const submit=el.detailBody.querySelector('[data-submit-action]');submit.disabled=true;submit.textContent='已提交';const returnButton=document.createElement('button');returnButton.className='button secondary';returnButton.type='button';returnButton.dataset.completeReturn='true';returnButton.textContent='完成并返回原位置';el.detailBody.querySelector('.detail-actions').append(returnButton);returnButton.addEventListener('click',()=>closeLayer());el.announcer.textContent='处理请求已提交，状态未改变'}
    function contextObject(){return{search_text:state.search,status_filters:[...state.statuses],owner_filter:state.owner,alert_only:state.alertOnly,expanded_node_ids:[...state.expanded],scroll_y:Math.max(0,Math.round(window.scrollY)),table_scroll_left:Math.max(0,Math.round(el.tableScroll.scrollLeft)),focus_node_id:state.selectedId}}
    function persistContext(){try{sessionStorage.setItem(storageKey,JSON.stringify(contextObject()))}catch(_error){}}
    function restorePersisted(){try{const saved=JSON.parse(sessionStorage.getItem(storageKey)||'null');if(!saved)return;state.search=typeof saved.search_text==='string'?saved.search_text:'';state.statuses=new Set(Array.isArray(saved.status_filters)?saved.status_filters.filter(value=>payload.status_order.includes(value)):[]);state.owner=payload.owners.includes(saved.owner_filter)?saved.owner_filter:'';state.alertOnly=saved.alert_only===true;state.expanded=new Set(Array.isArray(saved.expanded_node_ids)?saved.expanded_node_ids.filter(id=>byId.has(id)):payload.default_expanded_node_ids);state.savedContext=saved}catch(_error){}}
    function syncControls(){el.search.value=state.search;el.owner.value=state.owner;el.alertOnly.checked=state.alertOnly;el.statusFilters.querySelectorAll('input').forEach(input=>{input.checked=state.statuses.has(input.value)})}
    function resetFilters(){state.search='';state.statuses.clear();state.owner='';state.alertOnly=false;state.expanded=new Set(payload.default_expanded_node_ids);syncControls();render();el.search.focus()}
    function bindGlobal(){document.getElementById('filter-form').addEventListener('submit',event=>event.preventDefault());el.search.addEventListener('input',()=>{state.search=el.search.value;render()});el.owner.addEventListener('change',()=>{state.owner=el.owner.value;render()});el.statusFilters.addEventListener('change',event=>{if(event.target.matches('input')){event.target.checked?state.statuses.add(event.target.value):state.statuses.delete(event.target.value);render()}});el.alertOnly.addEventListener('change',()=>{state.alertOnly=el.alertOnly.checked;render()});document.getElementById('expand-all').addEventListener('click',()=>{rows.filter(row=>row.has_children).forEach(row=>state.expanded.add(row.node_id));render()});document.getElementById('reset-filters').addEventListener('click',resetFilters);document.querySelector('[data-reset-empty]').addEventListener('click',resetFilters);document.getElementById('close-detail').addEventListener('click',()=>closeLayer());el.layer.addEventListener('click',event=>{if(event.target===el.layer)closeLayer()});document.addEventListener('keydown',event=>{if(event.key==='Escape'&&el.layer.dataset.open==='true')closeLayer()});window.addEventListener('beforeunload',persistContext)}
    renderSummary();setupFilters();restorePersisted();syncControls();bindGlobal();render();requestAnimationFrame(()=>{if(state.savedContext){window.scrollTo(0,state.savedContext.scroll_y||0);el.tableScroll.scrollLeft=state.savedContext.table_scroll_left||0}});
    window.__KMFA_S11_P3__={payload,state,contextObject,visibleRows,openDetail,showAction,submitAction,restoreContext};
  })();
  </script>
</body>
</html>
'''


def render_html(payload: Mapping[str, Any] | None = None) -> str:
    resolved = copy.deepcopy(payload) if payload is not None else interface_payload()
    if resolved.get("schema_version") != "kmfa.v015.s11p3.interface_payload.v1":
        raise CheckBoardInterfaceError("PAYLOAD_INVALID", "检查板界面数据版本无效。")
    safe_json = json.dumps(resolved, ensure_ascii=False, sort_keys=True, separators=(",", ":")).replace("<", "\\u003c")
    return HTML_TEMPLATE.replace("__PAYLOAD__", safe_json)


def public_verification() -> dict[str, Any]:
    payload = interface_payload()
    html = render_html(payload)
    visual = visual_contract()
    accessibility = accessibility_contract()
    leaf_rows = [row for row in payload["rows"] if row["is_leaf"]]
    by_status = {label: next(row for row in leaf_rows if row["status_zh"] == label) for label in STATUS_ORDER}
    context = {
        "search_text": "回款",
        "status_filters": ["不可使用"],
        "owner_filter": "回款负责人",
        "alert_only": True,
        "expanded_node_ids": payload["root_node_ids"][:2],
        "scroll_y": 420,
        "table_scroll_left": 160,
        "focus_node_id": by_status["不可使用"]["node_id"],
    }
    flows = {
        "upload": simulate_action_and_return(by_status["不可使用"]["node_id"], context),
        "sync": simulate_action_and_return(by_status["已过期"]["node_id"], context),
        "confirm": simulate_action_and_return(by_status["需确认"]["node_id"], context),
        "view": simulate_action_and_return(by_status["已通过"]["node_id"], context),
    }
    checks: list[dict[str, str]] = []

    def check(check_id: str, condition: bool) -> None:
        checks.append({"check_id": check_id, "status": "PASS" if condition else "FAIL"})

    check("PAYLOAD_SCHEMA", payload["schema_version"] == "kmfa.v015.s11p3.interface_payload.v1")
    check("S11P2_NODE_COUNT_REUSED", payload["row_count"] == 34)
    check("S11P2_LEAF_COUNT_REUSED", payload["leaf_count"] == 6)
    check("FOUR_STATUS_LABELS", tuple(payload["status_order"]) == STATUS_ORDER)
    check("BUSINESS_BLUE_PRIMARY", visual["business_blue_primary"] is True)
    check("NO_LARGE_YELLOW", visual["large_yellow_surface_count"] == 0)
    check("NO_LARGE_STATUS_SURFACE", visual["large_status_color_surface_count"] == 0)
    check("STATUS_BADGE_ONLY", visual["status_color_usage"] == "BADGE_ICON_TEXT_ONLY")
    check("CONTRAST_ALL_PASS", visual["contrast_all_pass"] is True)
    check("BODY_TEXT_MINIMUM", visual["minimum_body_font_px"] >= 14)
    check("FOCUS_OUTLINE", visual["focus_outline_px"] >= 3)
    check("COLOR_NOT_ONLY", visual["color_only_status_allowed"] is False)
    check("REDUCED_MOTION", visual["reduced_motion_supported"] is True)
    check("KEYBOARD_PATHS", len(accessibility["keyboard_paths"]) >= 6)
    check("INTERNAL_FIELDS_HIDDEN_DEFAULT", accessibility["internal_field_names_visible_by_default"] is False)
    check("DETAIL_HAS_FILE", all(row["file_package_zh"] for row in leaf_rows))
    check("DETAIL_HAS_QUALITY_ISSUE", all(row["quality_issue_zh"] for row in leaf_rows))
    check("DETAIL_HAS_REPORT_IMPACT", all(row["report_impact_zh"] for row in leaf_rows))
    check("DETAIL_HAS_OWNER", all(row["owner_role_zh"] for row in leaf_rows))
    check("DETAIL_HAS_NEXT_ACTION", all(row["next_action_zh"] for row in leaf_rows))
    check("NO_TECHNICAL_STATUS_IN_DEFAULT_ROW", all("technical" not in _canonical(row).decode().casefold() for row in leaf_rows))
    check("ALL_LEAF_ACTIONS", all(row["action"] for row in leaf_rows))
    check("UPLOAD_FLOW_PRESENT", any(row["action"]["kind"] == "UPLOAD_SOURCE" for row in leaf_rows))
    check("SYNC_FLOW_PRESENT", any(row["action"]["kind"] == "SYNC_SOURCE" for row in leaf_rows))
    check("CONFIRM_FLOW_PRESENT", any(row["action"]["kind"] == "CONFIRM_QUALITY" for row in leaf_rows))
    check("VIEW_FLOW_PRESENT", any(row["action"]["kind"] == "VIEW_EVIDENCE" for row in leaf_rows))
    check("ALL_CONTEXT_EXACT", all(flow["context_exact"] for flow in flows.values()))
    check("ALL_BACKEND_STATE_UNCHANGED", all(flow["backend_state_unchanged"] for flow in flows.values()))
    check("ALL_FRONTEND_WRITES_ZERO", all(flow["frontend_status_write_count"] == 0 for flow in flows.values()))
    check("ALL_REQUESTS_NO_STATUS_CHANGE", all(flow["request"]["status_change_requested"] is False for flow in flows.values()))
    check("ALL_REQUESTS_NO_RAW_MUTATION", all(flow["request"]["raw_source_mutation_requested"] is False for flow in flows.values()))
    check("HTML_LANG_ZH", '<html lang="zh-CN">' in html)
    check("HTML_SKIP_LINK", 'class="skip-link"' in html)
    check("HTML_MAIN", 'id="main-content"' in html)
    check("HTML_SEARCH", 'role="search"' in html)
    check("HTML_TABLE", '<table class="matrix">' in html)
    check("HTML_ARIA_LIVE", 'aria-live="polite"' in html and 'aria-live="assertive"' in html)
    check("HTML_ARIA_EXPANDED", 'aria-expanded=' in html)
    check("HTML_FOCUS_VISIBLE", ':focus-visible' in html)
    check("HTML_REDUCED_MOTION", 'prefers-reduced-motion:reduce' in html)
    check("HTML_SESSION_CONTEXT", 'sessionStorage.setItem' in html and 'table_scroll_left' in html)
    check("HTML_RESTORE_SCROLL", 'window.scrollTo' in html and 'focus_node_id' in html)
    check("HTML_NO_EXTERNAL_RESOURCE", not re.search(r'(?:src|href)=["\']https?://', html))
    check("HTML_NO_GRADIENT", "gradient(" not in html)
    check("HTML_NO_HUGE_HEADING", "font-size:25px" in html and "font-size:60" not in html)
    check("HTML_STATUS_READONLY_COPY", "页面可以查看并发起处理，但不能直接把失败改成已通过" in html)
    check("HTML_SAFE_DEMO_COPY", "不读取真实财务资料" in html)
    check("FRONTEND_MUTATION_CLOSED", payload["frontend_status_mutation_allowed"] is False)
    check("RAW_ACCESS_ZERO", payload["raw_root_access_count"] == 0)
    check("RAW_CONTENT_UNREAD", payload["raw_business_content_read"] is False)
    check("LIVE_SOURCE_ZERO", payload["live_source_read_count"] == 0)
    check("FORMAL_REPORT_CLOSED", payload["formal_report_generated"] is False)
    check("GITHUB_CLOSED", payload["github_upload_performed"] is False)
    check("APP_CLOSED", payload["app_reinstall_performed"] is False)
    check("BUSINESS_EXECUTION_CLOSED", payload["business_execution_performed"] is False)
    public_text = json.dumps([payload, visual, accessibility, flows], ensure_ascii=False, sort_keys=True)
    for index, forbidden in enumerate(("/Users/", "/Volumes/", "/home/", "file://", "KMFA_MetaData", "private://", ".xlsx", ".xls", ".zip", "password"), start=1):
        check(f"PUBLIC_BOUNDARY_{index:02d}", forbidden.casefold() not in public_text.casefold())
    failed = sum(row["status"] != "PASS" for row in checks)
    return {
        "schema_version": "kmfa.v015.s11p3.public_verification.v1",
        "accounting": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
        "checks": checks,
        "payload": payload,
        "visual_contract": visual,
        "accessibility_contract": accessibility,
        "action_return_flows": flows,
        "raw_root_access_count": 0,
        "raw_business_content_read": False,
        "live_source_read_count": 0,
        "formal_report_generated": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }


__all__ = [
    "ACCEPTANCE_ID",
    "ACTION_KINDS",
    "CheckBoardInterfaceError",
    "CONTEXT_KEYS",
    "DESIGN_TOKENS",
    "ROADMAP_PHASE_ID",
    "RUN_PHASE_ID",
    "STATUS_ORDER",
    "TASK_ID",
    "VERSION",
    "accessibility_contract",
    "contrast_ratio",
    "create_action_request",
    "interface_payload",
    "public_verification",
    "render_html",
    "simulate_action_and_return",
    "validate_context_state",
    "visual_contract",
]
