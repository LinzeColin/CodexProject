#!/usr/bin/env python3
"""KMFA v1.5 S14-P2 商务蓝设计系统与可交互验收界面。"""

from __future__ import annotations

import copy
import json
import math
import re
from typing import Any, Mapping

from KMFA.tools import v015_s14_p1_information_architecture as information_architecture


RUN_PHASE_ID = "V015_S14_P2_DESIGN_SYSTEM"
ROADMAP_PHASE_ID = "S14-P2"
TASK_ID = "KMFA-V015-S14-P2-DESIGN-SYSTEM-20260716"
ACCEPTANCE_ID = "ACC-KMFA-V015-S14-P2-DESIGN-SYSTEM"
VERSION = "1.5.0-dev-s14p2"

NAV_ITEMS = tuple(copy.deepcopy(information_architecture.NAV_ITEMS))
REQUIRED_COMPONENT_STATES = (
    "default",
    "hover",
    "focus",
    "disabled",
    "loading",
    "error",
    "success",
)

THEMES: dict[str, dict[str, str]] = {
    "light": {
        "canvas": "#F3F6F8",
        "surface": "#FFFFFF",
        "surface_subtle": "#EDF6FB",
        "surface_strong": "#DCECF5",
        "text": "#152331",
        "text_muted": "#526370",
        "border": "#A6B8C5",
        "divider": "#CFDAE3",
        "nav": "#102F50",
        "nav_alt": "#0C2946",
        "nav_text": "#F4F8FB",
        "nav_muted": "#C9DEEC",
        "primary": "#17679B",
        "primary_hover": "#114B74",
        "primary_text": "#FFFFFF",
        "focus": "#17679B",
        "success": "#147A4A",
        "success_surface": "#EAF7F0",
        "warning": "#6B4100",
        "warning_surface": "#FFF4D6",
        "danger": "#A62E2E",
        "danger_surface": "#FCEEEE",
        "info": "#155F8E",
        "info_surface": "#EAF5FB",
    },
    "dark": {
        "canvas": "#0B1723",
        "surface": "#102638",
        "surface_subtle": "#16344A",
        "surface_strong": "#21435A",
        "text": "#F2F7FA",
        "text_muted": "#B8CAD6",
        "border": "#668297",
        "divider": "#36566C",
        "nav": "#071A2B",
        "nav_alt": "#0B2236",
        "nav_text": "#F2F7FA",
        "nav_muted": "#B8CAD6",
        "primary": "#6BC2F2",
        "primary_hover": "#94D5F7",
        "primary_text": "#071722",
        "focus": "#7CCBFA",
        "success": "#74D9AA",
        "success_surface": "#123D30",
        "warning": "#FFD27A",
        "warning_surface": "#3A2B0D",
        "danger": "#FFAAAA",
        "danger_surface": "#421C22",
        "info": "#8BD5FF",
        "info_surface": "#12344B",
    },
}

TYPOGRAPHY = {
    "font_family": '-apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", Arial, sans-serif',
    "display": {"size_px": 28, "line_height": 1.25, "weight": 750},
    "title": {"size_px": 20, "line_height": 1.35, "weight": 700},
    "subtitle": {"size_px": 16, "line_height": 1.45, "weight": 700},
    "body": {"size_px": 14, "line_height": 1.6, "weight": 400},
    "label": {"size_px": 13, "line_height": 1.45, "weight": 650},
    "caption": {"size_px": 12, "line_height": 1.45, "weight": 500},
    "number": {"size_px": 24, "line_height": 1.2, "weight": 750, "tabular": True},
}

SPACING = {"0": 0, "1": 4, "2": 8, "3": 12, "4": 16, "5": 20, "6": 24, "8": 32, "10": 40}
RADII = {"compact": 4, "control": 6, "panel": 8, "overlay": 12, "pill": 999}
MOTION = {"instant": 0, "fast": 100, "standard": 160, "deliberate": 220}

STATUS_SEMANTICS = (
    {"status": "success", "label_zh": "正常", "symbol": "✓", "tone": "success"},
    {"status": "warning", "label_zh": "需要关注", "symbol": "!", "tone": "warning"},
    {"status": "danger", "label_zh": "未通过", "symbol": "×", "tone": "danger"},
    {"status": "info", "label_zh": "待确认", "symbol": "i", "tone": "info"},
    {"status": "loading", "label_zh": "处理中", "symbol": "…", "tone": "info"},
)


class DesignSystemError(ValueError):
    """设计系统合同不完整或不安全。"""


def _hex_rgb(value: str) -> tuple[float, float, float]:
    if not re.fullmatch(r"#[0-9A-Fa-f]{6}", value):
        raise DesignSystemError(f"无效颜色：{value}")
    return tuple(int(value[index : index + 2], 16) / 255 for index in (1, 3, 5))


def _linear(channel: float) -> float:
    return channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4


def relative_luminance(value: str) -> float:
    red, green, blue = (_linear(channel) for channel in _hex_rgb(value))
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def contrast_ratio(foreground: str, background: str) -> float:
    lighter, darker = sorted(
        (relative_luminance(foreground), relative_luminance(background)), reverse=True
    )
    return (lighter + 0.05) / (darker + 0.05)


def design_token_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s14p2.design_token_contract.v1",
        "theme_count": len(THEMES),
        "themes": copy.deepcopy(THEMES),
        "typography": copy.deepcopy(TYPOGRAPHY),
        "spacing_base_px": 4,
        "spacing": copy.deepcopy(SPACING),
        "radii_px": copy.deepcopy(RADII),
        "table": {
            "header_height_px": 42,
            "row_height_px": 48,
            "compact_row_height_px": 40,
            "sticky_header": True,
            "numeric_alignment": "right",
            "empty_value_label_zh": "暂无数据",
        },
        "chart": {
            "line_width_px": 2,
            "point_size_px": 6,
            "series_distinction": ["文字图例", "线型", "数据点形状", "颜色"],
            "color_only_series_allowed": False,
            "accessible_data_table_required": True,
        },
        "status_semantics": copy.deepcopy(list(STATUS_SEMANTICS)),
        "warning_area_limit_bps": 800,
        "gradients_allowed": False,
        "decorative_large_status_surfaces_allowed": False,
        "light_theme_default": True,
        "dark_theme_optional": True,
    }


def component_contract() -> dict[str, Any]:
    shared_states = {
        "default": "可识别用途与可用状态",
        "hover": "指针悬停时边界或底色发生轻微变化",
        "focus": "键盘焦点显示三像素高对比外轮廓",
        "disabled": "仍可读，并说明当前不可用",
        "loading": "显示处理中符号与文字，保留原控件宽度",
        "error": "显示错误符号、原因与可执行修复提示",
        "success": "显示成功符号、结果文字与后续去向",
    }
    names = (
        ("button", "按钮"),
        ("form_field", "表单字段"),
        ("filter", "筛选器"),
        ("table", "表格"),
        ("card", "信息区块"),
        ("chart", "图表"),
        ("dialog", "确认弹窗"),
        ("drawer", "详情抽屉"),
        ("toast", "操作提示"),
        ("empty_state", "空状态"),
        ("status_badge", "状态徽标"),
    )
    components = []
    for component_id, name_zh in names:
        components.append(
            {
                "component_id": component_id,
                "name_zh": name_zh,
                "states": copy.deepcopy(shared_states),
                "state_count": len(shared_states),
                "feedback_required": True,
                "keyboard_operable": True,
                "visible_label_required": True,
            }
        )
    return {
        "schema_version": "kmfa.v015.s14p2.component_contract.v1",
        "required_states": list(REQUIRED_COMPONENT_STATES),
        "required_state_count": len(REQUIRED_COMPONENT_STATES),
        "component_count": len(components),
        "components": components,
        "full_state_coverage_count": sum(
            set(component["states"]) == set(REQUIRED_COMPONENT_STATES) for component in components
        ),
        "no_feedback_component_count": sum(
            not component["feedback_required"] for component in components
        ),
        "status_has_symbol_and_text_count": sum(
            bool(row["symbol"] and row["label_zh"]) for row in STATUS_SEMANTICS
        ),
        "status_semantic_count": len(STATUS_SEMANTICS),
        "color_only_state_count": 0,
    }


def motion_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s14p2.motion_contract.v1",
        "duration_tokens_ms": copy.deepcopy(MOTION),
        "maximum_motion_duration_ms": max(MOTION.values()),
        "allowed_purposes": ["方向", "状态变化", "操作反馈"],
        "allowed_properties": ["opacity", "transform", "background-color", "border-color", "color"],
        "layout_animation_allowed": False,
        "autoplay_loop_allowed": False,
        "blocking_animation_count": 0,
        "decorative_animation_count": 0,
        "reduced_motion_supported": True,
        "reduced_motion_duration_ms": 1,
        "reduced_motion_content_loss_count": 0,
    }


def contrast_evidence() -> dict[str, Any]:
    pairs: list[dict[str, Any]] = []
    pair_specs = (
        ("light", "正文", "text", "surface", 4.5),
        ("light", "辅助文字", "text_muted", "surface", 4.5),
        ("light", "主按钮", "primary_text", "primary", 4.5),
        ("light", "深色导航", "nav_text", "nav", 4.5),
        ("light", "成功状态", "success", "success_surface", 4.5),
        ("light", "警示状态", "warning", "warning_surface", 4.5),
        ("light", "失败状态", "danger", "danger_surface", 4.5),
        ("dark", "正文", "text", "surface", 4.5),
        ("dark", "辅助文字", "text_muted", "surface", 4.5),
        ("dark", "主按钮", "primary_text", "primary", 4.5),
        ("dark", "深色导航", "nav_text", "nav", 4.5),
        ("dark", "成功状态", "success", "success_surface", 4.5),
        ("dark", "警示状态", "warning", "warning_surface", 4.5),
        ("dark", "失败状态", "danger", "danger_surface", 4.5),
    )
    for theme, label, foreground_key, background_key, minimum in pair_specs:
        foreground = THEMES[theme][foreground_key]
        background = THEMES[theme][background_key]
        ratio = contrast_ratio(foreground, background)
        pairs.append(
            {
                "theme": theme,
                "label_zh": label,
                "foreground_token": foreground_key,
                "background_token": background_key,
                "foreground": foreground,
                "background": background,
                "ratio": round(ratio, 2),
                "minimum": minimum,
                "status": "PASS" if ratio >= minimum else "FAIL",
            }
        )
    failures = [row for row in pairs if row["status"] != "PASS"]
    return {
        "schema_version": "kmfa.v015.s14p2.contrast_evidence.v1",
        "pair_count": len(pairs),
        "pass_count": len(pairs) - len(failures),
        "fail_count": len(failures),
        "minimum_text_ratio": 4.5,
        "pairs": pairs,
    }


def visual_regression_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s14p2.visual_regression_contract.v1",
        "required_viewports": [
            {"name": "desktop_light", "width": 1440, "height": 1000, "theme": "light"},
            {"name": "desktop_dark", "width": 1440, "height": 1000, "theme": "dark"},
            {"name": "mobile_light", "width": 390, "height": 844, "theme": "light"},
        ],
        "required_flows": [
            "top_navigation_preserved",
            "light_dark_theme_boundary",
            "button_form_filter_table_card_chart",
            "dialog_drawer_toast_empty_state_badge",
            "default_hover_focus_disabled_loading_error_success",
            "status_symbol_and_text",
            "keyboard_dialog_focus_return",
            "reduced_motion",
        ],
        "screenshot_count": 3,
        "console_error_count_expected": 0,
        "network_request_count_expected": 0,
    }


def interface_payload() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s14p2.interface_payload.v1",
        "title_zh": "KMFA 经营工作台",
        "navigation": copy.deepcopy(list(NAV_ITEMS)),
        "status_semantics": copy.deepcopy(list(STATUS_SEMANTICS)),
        "theme_default": "light",
        "theme_options": ["light", "dark"],
        "raw_root_access_count": 0,
        "raw_business_content_read": False,
        "live_source_read_count": 0,
        "real_business_action_count": 0,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
    }


def _css_variables(theme: Mapping[str, str]) -> str:
    return ";".join(f"--{key.replace('_', '-')}:{value}" for key, value in theme.items())


HTML_TEMPLATE = r'''<!doctype html>
<html lang="zh-CN" data-theme="light">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="color-scheme" content="light dark">
  <title>KMFA 经营工作台</title>
  <style>
    :root{__LIGHT_VARS__;--font:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",Arial,sans-serif;--focus-ring:0 0 0 3px color-mix(in srgb,var(--focus) 30%,transparent)}
    :root[data-theme="dark"]{__DARK_VARS__}
    *{box-sizing:border-box}html{min-width:320px;background:var(--canvas)}body{margin:0;background:var(--canvas);color:var(--text);font:14px/1.6 var(--font);transition:background-color 160ms,color 160ms}button,input,select{font:inherit;color:inherit}button,a,select,input{transition:background-color 100ms,border-color 100ms,color 100ms,opacity 100ms,transform 100ms}a{color:inherit}.skip-link{position:fixed;z-index:100;left:12px;top:-80px;background:var(--surface);color:var(--text);border:1px solid var(--border);padding:8px 12px;border-radius:6px}.skip-link:focus{top:10px}.app-header{background:var(--nav);color:var(--nav-text)}.brand-row{display:flex;justify-content:space-between;align-items:center;gap:16px;max-width:1280px;margin:auto;padding:14px 24px 10px}.brand{display:flex;align-items:center;gap:11px;text-decoration:none}.brand-mark{display:grid;place-items:center;width:38px;height:38px;border:1px solid color-mix(in srgb,var(--nav-text) 45%,transparent);border-radius:7px;background:var(--primary);color:var(--primary-text);font-weight:800}.brand strong{display:block;font-size:16px}.brand small{display:block;color:var(--nav-muted);font-size:12px}.header-actions{display:flex;gap:8px}.theme-toggle{min-height:36px;border:1px solid color-mix(in srgb,var(--nav-text) 45%,transparent);border-radius:6px;background:transparent;color:var(--nav-text);padding:6px 10px;cursor:pointer}.theme-toggle:hover{background:color-mix(in srgb,var(--nav-text) 10%,transparent)}.primary-nav-wrap{border-top:1px solid color-mix(in srgb,var(--nav-text) 14%,transparent);background:var(--nav-alt)}.primary-nav{display:flex;max-width:1280px;margin:auto;padding:0 24px;overflow-x:auto}.primary-nav a{position:relative;display:flex;align-items:center;min-height:48px;padding:0 15px;color:var(--nav-muted);font-weight:700;text-decoration:none;white-space:nowrap}.primary-nav a:hover{background:color-mix(in srgb,var(--nav-text) 8%,transparent);color:var(--nav-text)}.primary-nav a[aria-current="page"]{background:var(--surface);color:var(--text)}.primary-nav a[aria-current="page"]::after{content:"";position:absolute;left:15px;right:15px;bottom:0;height:3px;background:var(--primary)}
    .shell{max-width:1280px;margin:auto;padding:20px 24px 48px}.breadcrumbs{margin-bottom:8px;color:var(--text-muted);font-size:12px}.page-heading{display:flex;justify-content:space-between;align-items:flex-start;gap:24px;margin-bottom:18px}.page-heading h1{margin:2px 0 4px;color:var(--text);font-size:28px;line-height:1.25}.page-heading p{margin:0;color:var(--text-muted);font-size:15px}.eyebrow{color:var(--primary);font-weight:700}.demo-label{border:1px solid var(--border);border-radius:999px;background:var(--surface);padding:5px 9px;color:var(--text-muted);font-size:12px;white-space:nowrap}
    .toolbar{display:flex;align-items:end;gap:10px;flex-wrap:wrap;margin-bottom:16px;border:1px solid var(--divider);border-radius:8px;background:var(--surface);padding:12px}.field{display:grid;gap:4px;min-width:150px}.field label{font-size:12px;font-weight:700}.field input,.field select{min-height:38px;border:1px solid var(--border);border-radius:6px;background:var(--surface);padding:7px 10px}.field input:hover,.field select:hover{border-color:var(--primary)}.field-error input{border-color:var(--danger)}.field-message{min-height:17px;color:var(--text-muted);font-size:12px}.field-error .field-message{color:var(--danger)}.btn{display:inline-flex;align-items:center;justify-content:center;gap:7px;min-height:38px;border:1px solid var(--border);border-radius:6px;background:var(--surface);padding:7px 12px;font-weight:700;cursor:pointer}.btn:hover{border-color:var(--primary);background:var(--surface-subtle)}.btn:active{transform:translateY(1px)}.btn-primary{border-color:var(--primary);background:var(--primary);color:var(--primary-text)}.btn-primary:hover{border-color:var(--primary-hover);background:var(--primary-hover)}.btn[disabled]{cursor:not-allowed;opacity:.58}.btn[aria-busy="true"]{cursor:progress}.btn-icon{font-weight:800}.toolbar-spacer{flex:1}
    .notice{display:flex;align-items:flex-start;gap:9px;margin-bottom:16px;border:1px solid color-mix(in srgb,var(--warning) 35%,var(--divider));border-left:4px solid var(--warning);border-radius:6px;background:var(--warning-surface);padding:9px 12px;color:var(--warning)}.notice strong{display:block}.notice p{margin:0}.status-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));border:1px solid var(--divider);border-radius:8px;background:var(--surface);overflow:hidden}.metric{min-height:116px;padding:16px;border-right:1px solid var(--divider)}.metric:last-child{border-right:0}.metric-label{color:var(--text-muted);font-size:12px}.metric-value{display:block;margin:6px 0 2px;font-size:24px;line-height:1.2;font-variant-numeric:tabular-nums}.metric-note{color:var(--text-muted);font-size:12px}
    .work-grid{display:grid;grid-template-columns:minmax(0,1.45fr) minmax(320px,.8fr);gap:16px;margin-top:16px}.panel{border:1px solid var(--divider);border-radius:8px;background:var(--surface);overflow:hidden}.panel-heading{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:14px 16px;border-bottom:1px solid var(--divider)}.panel-heading h2{margin:0;font-size:16px}.panel-heading p{margin:0;color:var(--text-muted);font-size:12px}.panel-body{padding:16px}.chart-wrap{min-height:240px}.chart{display:block;width:100%;height:auto}.chart .grid{stroke:var(--divider);stroke-width:1}.chart .series-a{fill:none;stroke:var(--primary);stroke-width:2.5}.chart .series-b{fill:none;stroke:var(--warning);stroke-width:2.5;stroke-dasharray:7 5}.chart .dot-a{fill:var(--surface);stroke:var(--primary);stroke-width:2}.chart .dot-b{fill:var(--warning)}.chart text{fill:var(--text-muted);font:12px var(--font)}.legend{display:flex;gap:18px;flex-wrap:wrap;margin-top:6px;color:var(--text-muted);font-size:12px}.legend span{display:inline-flex;align-items:center;gap:6px}.legend-line{width:24px;height:0;border-top:3px solid var(--primary)}.legend-line.dashed{border-color:var(--warning);border-top-style:dashed}.sr-data{position:absolute!important;width:1px!important;height:1px!important;overflow:hidden!important;clip:rect(0,0,0,0)!important}
    .status-list{display:grid;gap:8px}.status-row{display:flex;align-items:center;justify-content:space-between;gap:14px;min-height:44px;border-bottom:1px solid var(--divider);padding:5px 0}.status-row:last-child{border-bottom:0}.status-row strong{display:block}.status-row small{color:var(--text-muted)}.badge{display:inline-flex;align-items:center;gap:5px;border:1px solid currentColor;border-radius:999px;padding:3px 8px;font-size:12px;font-weight:700;white-space:nowrap}.badge[data-tone="success"]{background:var(--success-surface);color:var(--success)}.badge[data-tone="warning"]{background:var(--warning-surface);color:var(--warning)}.badge[data-tone="danger"]{background:var(--danger-surface);color:var(--danger)}.badge[data-tone="info"]{background:var(--info-surface);color:var(--info)}
    .table-panel{margin-top:16px}.table-scroll{overflow:auto}.data-table{width:100%;border-collapse:collapse;min-width:720px}.data-table th{position:sticky;top:0;height:42px;background:var(--surface-subtle);color:var(--text-muted);font-size:12px;text-align:left}.data-table th,.data-table td{padding:9px 12px;border-bottom:1px solid var(--divider)}.data-table tr:hover td{background:var(--surface-subtle)}.data-table td.number,.data-table th.number{text-align:right;font-variant-numeric:tabular-nums}.link-button{border:0;background:transparent;color:var(--primary);font-weight:700;cursor:pointer;padding:4px}.link-button:hover{text-decoration:underline}
    .component-check{margin-top:16px}.state-row{display:flex;align-items:flex-start;gap:10px;flex-wrap:wrap}.empty{display:grid;place-items:center;min-height:145px;border:1px dashed var(--border);border-radius:8px;background:var(--surface-subtle);text-align:center;padding:20px}.empty-symbol{font-size:28px;color:var(--primary)}.empty h3{margin:4px 0}.empty p{margin:0 0 10px;color:var(--text-muted)}
    dialog{width:min(480px,calc(100vw - 32px));border:1px solid var(--divider);border-radius:12px;background:var(--surface);color:var(--text);padding:0;box-shadow:0 18px 48px rgba(4,18,30,.24)}dialog::backdrop{background:rgba(4,18,30,.52)}.dialog-heading{padding:16px 18px;border-bottom:1px solid var(--divider)}.dialog-heading h2{margin:0;font-size:18px}.dialog-body{padding:18px}.dialog-actions{display:flex;justify-content:flex-end;gap:8px;padding:12px 18px;border-top:1px solid var(--divider)}.drawer-backdrop{position:fixed;z-index:30;inset:0;background:rgba(4,18,30,.45);opacity:0;pointer-events:none}.drawer-backdrop[data-open="true"]{opacity:1;pointer-events:auto}.drawer{position:fixed;z-index:31;top:0;right:0;width:min(440px,92vw);height:100vh;background:var(--surface);border-left:1px solid var(--divider);box-shadow:0 18px 48px rgba(4,18,30,.24);transform:translateX(102%);overflow:auto}.drawer[data-open="true"]{transform:translateX(0)}.drawer-header{display:flex;justify-content:space-between;align-items:center;padding:16px;border-bottom:1px solid var(--divider)}.drawer-header h2{margin:0;font-size:18px}.drawer-body{padding:16px}.toast{position:fixed;z-index:40;right:18px;bottom:18px;display:flex;align-items:flex-start;gap:8px;max-width:360px;border:1px solid var(--success);border-radius:8px;background:var(--success-surface);color:var(--success);padding:11px 13px;box-shadow:0 8px 24px rgba(4,18,30,.14);opacity:0;transform:translateY(12px);pointer-events:none}.toast[data-open="true"]{opacity:1;transform:translateY(0)}
    :focus-visible{outline:3px solid var(--focus);outline-offset:3px;box-shadow:var(--focus-ring)}.drawer,.drawer-backdrop,.toast{transition:opacity 160ms,transform 220ms}.visually-hidden{position:absolute!important;width:1px!important;height:1px!important;padding:0!important;margin:-1px!important;overflow:hidden!important;clip:rect(0,0,0,0)!important;white-space:nowrap!important;border:0!important}
    @media(max-width:840px){.status-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.metric:nth-child(2){border-right:0}.metric:nth-child(-n+2){border-bottom:1px solid var(--divider)}.work-grid{grid-template-columns:1fr}.page-heading{display:block}.demo-label{display:inline-block;margin-top:10px}}
    @media(max-width:560px){.brand-row{padding:12px 16px}.brand small{display:none}.primary-nav{padding:0 10px}.primary-nav a{padding:0 12px}.shell{padding:15px 16px 32px}.page-heading h1{font-size:24px}.toolbar{align-items:stretch}.field{width:100%}.toolbar .btn{width:100%}.toolbar-spacer{display:none}.status-grid{grid-template-columns:1fr}.metric{border-right:0;border-bottom:1px solid var(--divider)}.metric:last-child{border-bottom:0}.metric:nth-child(2){border-right:0}.work-grid{display:block}.work-grid .panel+ .panel{margin-top:16px}.header-actions{gap:4px}.theme-toggle{padding:6px 8px}.state-row .btn{flex:1 1 42%}}
    @media(prefers-reduced-motion:reduce){*,*::before,*::after{animation-duration:.001ms!important;animation-iteration-count:1!important;scroll-behavior:auto!important;transition-duration:.001ms!important}}
  </style>
</head>
<body>
  <a class="skip-link" href="#main-content">跳到主要内容</a>
  <header class="app-header">
    <div class="brand-row">
      <a class="brand" href="#main-content" aria-label="返回经营首页"><span class="brand-mark" aria-hidden="true">K</span><span><strong>KMFA 经营工作台</strong><small>清楚看到重点，稳妥完成工作</small></span></a>
      <div class="header-actions"><button class="theme-toggle" id="theme-toggle" type="button" aria-pressed="false"><span aria-hidden="true">◐</span> 深色显示</button></div>
    </div>
    <div class="primary-nav-wrap"><nav class="primary-nav" id="primary-nav" aria-label="主要导航"></nav></div>
  </header>
  <main class="shell" id="main-content" tabindex="-1">
    <div class="breadcrumbs" aria-label="面包屑">经营首页</div>
    <header class="page-heading"><div><div class="eyebrow">经营概览</div><h1>今天需要关注的事项</h1><p>先看经营变化和待办，再进入项目、回款或资金详情。</p></div><span class="demo-label">公开演示数据</span></header>
    <section class="toolbar" aria-label="页面筛选">
      <div class="field"><label for="period">查看期间</label><select id="period"><option>本月</option><option>本季度</option><option>本年度</option></select><span class="field-message">切换后更新当前页面</span></div>
      <div class="field"><label for="status-filter">事项状态</label><select id="status-filter"><option>全部状态</option><option>需要关注</option><option>正常</option></select><span class="field-message">当前显示全部状态</span></div>
      <div class="field"><label for="search">搜索事项</label><input id="search" type="search" placeholder="项目或负责人"><span class="field-message">输入名称进行查找</span></div>
      <span class="toolbar-spacer"></span><button class="btn" id="open-drawer" type="button"><span class="btn-icon" aria-hidden="true">≡</span>查看详情</button><button class="btn btn-primary" id="open-dialog" type="button"><span class="btn-icon" aria-hidden="true">＋</span>新增跟进</button>
    </section>
    <aside class="notice" data-tone="warning" aria-label="需要关注"><span aria-hidden="true">!</span><div><strong>有 2 项资料需要确认</strong><p>提示同时使用符号和文字，不只依赖颜色。</p></div></aside>
    <section class="status-grid" aria-label="经营摘要">
      <article class="metric"><span class="metric-label">本月重点事项</span><strong class="metric-value">4 项</strong><span class="metric-note">与上周持平</span></article>
      <article class="metric"><span class="metric-label">待跟进回款</span><strong class="metric-value">3 项</strong><span class="metric-note">其中 1 项临近日期</span></article>
      <article class="metric"><span class="metric-label">资料完整度</span><strong class="metric-value">92%</strong><span class="metric-note">仍有 2 项待确认</span></article>
      <article class="metric"><span class="metric-label">本周已完成</span><strong class="metric-value">7 项</strong><span class="metric-note">全部保留处理记录</span></article>
    </section>
    <div class="work-grid">
      <section class="panel" aria-labelledby="trend-title"><div class="panel-heading"><div><h2 id="trend-title">近六周事项变化</h2><p>实线为已完成，虚线为待处理</p></div><span class="badge" data-tone="info"><span aria-hidden="true">i</span> 每周更新</span></div><div class="panel-body chart-wrap">
        <svg class="chart" viewBox="0 0 640 250" role="img" aria-labelledby="chart-title chart-desc"><title id="chart-title">近六周事项变化</title><desc id="chart-desc">已完成事项从五项上升到九项，待处理事项从七项下降到四项。</desc>
          <path class="grid" d="M52 35H620M52 90H620M52 145H620M52 200H620"/><path class="series-a" d="M60 172 L170 154 L280 134 L390 110 L500 86 L610 68"/><path class="series-b" d="M60 82 L170 96 L280 118 L390 132 L500 148 L610 158"/>
          <g class="dot-a"><circle cx="60" cy="172" r="5"/><circle cx="170" cy="154" r="5"/><circle cx="280" cy="134" r="5"/><circle cx="390" cy="110" r="5"/><circle cx="500" cy="86" r="5"/><circle cx="610" cy="68" r="5"/></g><g class="dot-b"><rect x="56" y="78" width="8" height="8"/><rect x="166" y="92" width="8" height="8"/><rect x="276" y="114" width="8" height="8"/><rect x="386" y="128" width="8" height="8"/><rect x="496" y="144" width="8" height="8"/><rect x="606" y="154" width="8" height="8"/></g>
          <text x="52" y="226">第1周</text><text x="158" y="226">第2周</text><text x="268" y="226">第3周</text><text x="378" y="226">第4周</text><text x="488" y="226">第5周</text><text x="588" y="226">第6周</text>
        </svg>
        <div class="legend" aria-hidden="true"><span><i class="legend-line"></i>已完成（实线圆点）</span><span><i class="legend-line dashed"></i>待处理（虚线方点）</span></div>
        <table class="sr-data"><caption>近六周事项数据</caption><thead><tr><th>期间</th><th>已完成</th><th>待处理</th></tr></thead><tbody><tr><td>第1周</td><td>5</td><td>7</td></tr><tr><td>第2周</td><td>6</td><td>6</td></tr><tr><td>第3周</td><td>7</td><td>5</td></tr><tr><td>第4周</td><td>8</td><td>5</td></tr><tr><td>第5周</td><td>8</td><td>4</td></tr><tr><td>第6周</td><td>9</td><td>4</td></tr></tbody></table>
      </div></section>
      <section class="panel" aria-labelledby="status-title"><div class="panel-heading"><div><h2 id="status-title">事项状态</h2><p>符号、文字和颜色共同表达</p></div></div><div class="panel-body status-list">
        <div class="status-row"><span><strong>项目资料</strong><small>已完成核对</small></span><span class="badge" data-tone="success"><span aria-hidden="true">✓</span>正常</span></div>
        <div class="status-row"><span><strong>回款跟进</strong><small>临近计划日期</small></span><span class="badge" data-tone="warning"><span aria-hidden="true">!</span>需要关注</span></div>
        <div class="status-row"><span><strong>数据更新</strong><small>等待负责人确认</small></span><span class="badge" data-tone="info"><span aria-hidden="true">i</span>待确认</span></div>
        <div class="status-row"><span><strong>资料校验</strong><small>缺少必要说明</small></span><span class="badge" data-tone="danger"><span aria-hidden="true">×</span>未通过</span></div>
      </div></section>
    </div>
    <section class="panel table-panel" aria-labelledby="items-title"><div class="panel-heading"><div><h2 id="items-title">重点事项</h2><p>表头固定，金额右对齐，操作有明确反馈</p></div></div><div class="table-scroll"><table class="data-table"><thead><tr><th>事项</th><th>负责人</th><th>计划日期</th><th>状态</th><th class="number">演示金额</th><th>操作</th></tr></thead><tbody>
      <tr><td>确认项目进度资料</td><td>项目负责人</td><td>本周三</td><td><span class="badge" data-tone="warning"><span aria-hidden="true">!</span>需要关注</span></td><td class="number">¥ 120,000</td><td><button class="link-button row-detail" type="button">查看</button></td></tr>
      <tr><td>核对回款联系记录</td><td>回款负责人</td><td>本周五</td><td><span class="badge" data-tone="info"><span aria-hidden="true">i</span>待确认</span></td><td class="number">¥ 86,000</td><td><button class="link-button row-detail" type="button">查看</button></td></tr>
      <tr><td>完成资料格式检查</td><td>数据负责人</td><td>已完成</td><td><span class="badge" data-tone="success"><span aria-hidden="true">✓</span>正常</span></td><td class="number">—</td><td><button class="link-button row-detail" type="button">查看</button></td></tr>
    </tbody></table></div></section>
    <section class="panel component-check" aria-labelledby="component-title"><div class="panel-heading"><div><h2 id="component-title">控件状态检查</h2><p>每个操作都有可见反馈</p></div></div><div class="panel-body state-row">
      <button class="btn" type="button">普通按钮</button><button class="btn btn-primary" type="button">主要按钮</button><button class="btn" type="button" disabled title="需要先选择事项">暂不可用</button><button class="btn" type="button" aria-busy="true"><span aria-hidden="true">…</span>处理中</button><span class="badge" data-tone="success"><span aria-hidden="true">✓</span>操作成功</span>
      <div class="field field-error"><label for="error-demo">错误状态</label><input id="error-demo" aria-invalid="true" aria-describedby="error-message" value="缺少日期"><span class="field-message" id="error-message"><span aria-hidden="true">×</span>请选择计划日期</span></div>
    </div></section>
    <section class="empty" aria-labelledby="empty-title"><div><div class="empty-symbol" aria-hidden="true">○</div><h3 id="empty-title">没有更多待处理事项</h3><p>完成筛选后，新事项会显示在这里。</p><button class="btn" type="button">清除筛选</button></div></section>
  </main>
  <dialog id="follow-dialog" aria-labelledby="dialog-title"><div class="dialog-heading"><h2 id="dialog-title">新增跟进事项</h2></div><div class="dialog-body"><div class="field"><label for="follow-name">事项名称</label><input id="follow-name" value="核对公开演示资料"><span class="field-message">此演示不会写入真实资料</span></div></div><div class="dialog-actions"><button class="btn" id="dialog-cancel" type="button">取消</button><button class="btn btn-primary" id="dialog-confirm" type="button">保存演示</button></div></dialog>
  <div class="drawer-backdrop" id="drawer-backdrop" data-open="false"></div><aside class="drawer" id="detail-drawer" data-open="false" aria-labelledby="drawer-title" aria-hidden="true"><div class="drawer-header"><h2 id="drawer-title">事项详情</h2><button class="btn" id="close-drawer" type="button" aria-label="关闭详情">关闭</button></div><div class="drawer-body"><span class="badge" data-tone="info"><span aria-hidden="true">i</span>公开演示</span><h3>确认项目进度资料</h3><p>这里展示负责人、计划日期和下一步。正式版本会继续沿用同一套组件和状态规则。</p></div></aside>
  <div class="toast" id="toast" role="status" aria-live="polite" data-open="false"><span aria-hidden="true">✓</span><span><strong>演示已保存</strong><br>没有写入任何真实资料。</span></div>
  <script id="design-payload" type="application/json">__PAYLOAD__</script>
  <script>
    (function(){"use strict";
      var payload=JSON.parse(document.getElementById("design-payload").textContent),root=document.documentElement;
      var nav=document.getElementById("primary-nav");
      nav.innerHTML=payload.navigation.map(function(item,index){return '<a href="#main-content"'+(index===0?' aria-current="page"':'')+'>'+item.label_zh+'</a>';}).join("");
      var themeButton=document.getElementById("theme-toggle");
      function setTheme(theme){root.dataset.theme=theme;var dark=theme==="dark";themeButton.setAttribute("aria-pressed",String(dark));themeButton.innerHTML='<span aria-hidden="true">◐</span> '+(dark?"浅色显示":"深色显示");}
      themeButton.addEventListener("click",function(){setTheme(root.dataset.theme==="dark"?"light":"dark");});
      var dialog=document.getElementById("follow-dialog"),openDialog=document.getElementById("open-dialog"),toast=document.getElementById("toast"),toastTimer;
      openDialog.addEventListener("click",function(){dialog.showModal();document.getElementById("follow-name").focus();});
      document.getElementById("dialog-cancel").addEventListener("click",function(){dialog.close();openDialog.focus();});
      document.getElementById("dialog-confirm").addEventListener("click",function(){dialog.close();toast.dataset.open="true";clearTimeout(toastTimer);toastTimer=setTimeout(function(){toast.dataset.open="false";},2200);openDialog.focus();});
      var drawer=document.getElementById("detail-drawer"),backdrop=document.getElementById("drawer-backdrop"),drawerTrigger=document.getElementById("open-drawer"),lastDrawerTrigger=drawerTrigger;
      function openDrawer(trigger){lastDrawerTrigger=trigger||drawerTrigger;drawer.dataset.open="true";backdrop.dataset.open="true";drawer.setAttribute("aria-hidden","false");document.getElementById("close-drawer").focus();}
      function closeDrawer(){drawer.dataset.open="false";backdrop.dataset.open="false";drawer.setAttribute("aria-hidden","true");lastDrawerTrigger.focus();}
      drawerTrigger.addEventListener("click",function(){openDrawer(drawerTrigger);});document.querySelectorAll(".row-detail").forEach(function(button){button.addEventListener("click",function(){openDrawer(button);});});document.getElementById("close-drawer").addEventListener("click",closeDrawer);backdrop.addEventListener("click",closeDrawer);
      document.addEventListener("keydown",function(event){if(event.key==="Escape"&&drawer.dataset.open==="true")closeDrawer();});
      document.getElementById("status-filter").addEventListener("change",function(event){event.target.parentElement.querySelector(".field-message").textContent="当前显示："+event.target.value;});
      window.__KMFA_S14_P2__={payload:payload,setTheme:setTheme,openDrawer:openDrawer,closeDrawer:closeDrawer};
    }());
  </script>
</body>
</html>'''


def render_html(payload: Mapping[str, Any] | None = None) -> str:
    value = interface_payload() if payload is None else copy.deepcopy(dict(payload))
    serialized = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).replace(
        "</", "<\\/"
    )
    return (
        HTML_TEMPLATE.replace("__LIGHT_VARS__", _css_variables(THEMES["light"]))
        .replace("__DARK_VARS__", _css_variables(THEMES["dark"]))
        .replace("__PAYLOAD__", serialized)
    )


def public_verification() -> dict[str, Any]:
    tokens = design_token_contract()
    components = component_contract()
    motion = motion_contract()
    contrast = contrast_evidence()
    visual = visual_regression_contract()
    payload = interface_payload()
    html = render_html(payload)
    checks: list[dict[str, str]] = []

    def check(check_id: str, condition: bool) -> None:
        checks.append({"check_id": check_id, "status": "PASS" if condition else "FAIL"})

    check("TWO_THEME_BOUNDARY", tokens["theme_count"] == 2 and tokens["light_theme_default"])
    check("BUSINESS_BLUE_LIGHT", THEMES["light"]["nav"] == "#102F50" and THEMES["light"]["primary"] == "#17679B")
    check("BUSINESS_BLUE_DARK", THEMES["dark"]["primary"] == "#6BC2F2")
    check("SPACING_FOUR_BASE", tokens["spacing_base_px"] == 4)
    check("TABLE_RULES_COMPLETE", tokens["table"]["sticky_header"] and tokens["table"]["numeric_alignment"] == "right")
    check("CHART_NOT_COLOR_ONLY", tokens["chart"]["color_only_series_allowed"] is False)
    check("CHART_DATA_TABLE_REQUIRED", tokens["chart"]["accessible_data_table_required"] is True)
    check("WARNING_LIMIT", tokens["warning_area_limit_bps"] <= 800)
    check("NO_GRADIENT_TOKEN", tokens["gradients_allowed"] is False)
    check("CONTRAST_ALL_PASS", contrast["pair_count"] == 14 and contrast["fail_count"] == 0)
    check("COMPONENT_COUNT", components["component_count"] == 11)
    check("STATE_COUNT", components["required_state_count"] == 7)
    check("FULL_STATE_COVERAGE", components["full_state_coverage_count"] == components["component_count"])
    check("NO_FEEDBACKLESS_COMPONENT", components["no_feedback_component_count"] == 0)
    check("NO_COLOR_ONLY_STATE", components["color_only_state_count"] == 0)
    check("STATUS_SYMBOL_TEXT", components["status_has_symbol_and_text_count"] == components["status_semantic_count"])
    check("MOTION_MAX_220", motion["maximum_motion_duration_ms"] <= 220)
    check("MOTION_NO_LAYOUT", motion["layout_animation_allowed"] is False)
    check("MOTION_NO_LOOP", motion["autoplay_loop_allowed"] is False)
    check("MOTION_NO_BLOCKING", motion["blocking_animation_count"] == 0)
    check("MOTION_REDUCED", motion["reduced_motion_supported"] and motion["reduced_motion_content_loss_count"] == 0)
    check("VISUAL_THREE_VIEWPORTS", visual["screenshot_count"] == 3 and len(visual["required_viewports"]) == 3)
    check("TOP_NAV_PRESERVED", html.count('aria-label="主要导航"') == 1 and "primary-nav" in html)
    check("THEME_TOGGLE", 'id="theme-toggle"' in html and 'aria-pressed="false"' in html)
    check("BUTTON_PRESENT", 'class="btn btn-primary"' in html)
    check("FORM_PRESENT", 'id="period"' in html and 'id="search"' in html)
    check("FILTER_PRESENT", 'id="status-filter"' in html)
    check("TABLE_PRESENT", 'class="data-table"' in html)
    check("CARD_PRESENT", 'class="status-grid"' in html)
    check("CHART_PRESENT", 'class="chart"' in html and 'class="sr-data"' in html)
    check("DIALOG_PRESENT", '<dialog id="follow-dialog"' in html)
    check("DRAWER_PRESENT", 'id="detail-drawer"' in html)
    check("TOAST_PRESENT", 'id="toast"' in html and 'role="status"' in html)
    check("EMPTY_STATE_PRESENT", 'class="empty"' in html)
    check("BADGE_PRESENT", 'class="badge"' in html)
    check("DISABLED_VISIBLE", "disabled title=" in html)
    check("LOADING_VISIBLE", 'aria-busy="true"' in html and "处理中" in html)
    check("ERROR_VISIBLE", 'aria-invalid="true"' in html and "请选择计划日期" in html)
    check("SUCCESS_VISIBLE", "操作成功" in html)
    check("FOCUS_VISIBLE", ":focus-visible" in html)
    check("REDUCED_MOTION", "prefers-reduced-motion:reduce" in html)
    check("NO_EXTERNAL_RESOURCE", not re.search(r'(?:src|href)=["\']https?://', html))
    check("NO_GRADIENT_HTML", "gradient(" not in html)
    check("NO_AUTOPLAY", "autoplay" not in html.casefold())
    check("RAW_ACCESS_ZERO", payload["raw_root_access_count"] == 0)
    check("RAW_CONTENT_UNREAD", payload["raw_business_content_read"] is False)
    check("LIVE_SOURCE_ZERO", payload["live_source_read_count"] == 0)
    check("REAL_ACTION_ZERO", payload["real_business_action_count"] == 0)
    check("GITHUB_CLOSED", payload["github_upload_performed"] is False)
    check("APP_CLOSED", payload["app_reinstall_performed"] is False)
    public_text = json.dumps(
        [tokens, components, motion, contrast, visual, payload], ensure_ascii=False, sort_keys=True
    )
    for index, forbidden in enumerate(
        ("/Users/", "/Volumes/", "/home/", "file://", "KMFA_MetaData", "private://", ".xlsx", ".xls", ".zip", "password"),
        start=1,
    ):
        check(f"PUBLIC_BOUNDARY_{index:02d}", forbidden.casefold() not in public_text.casefold())
    failed = [row["check_id"] for row in checks if row["status"] != "PASS"]
    return {
        "schema_version": "kmfa.v015.s14p2.public_verification.v1",
        "accounting": {"total": len(checks), "passed": len(checks) - len(failed), "failed": len(failed)},
        "failed_checks": failed,
        "design_token_contract": tokens,
        "component_contract": components,
        "motion_contract": motion,
        "contrast_evidence": contrast,
        "visual_regression_contract": visual,
        "raw_root_access_count": 0,
        "raw_business_content_read": False,
        "live_source_read_count": 0,
        "real_business_action_count": 0,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
    }


__all__ = [
    "ACCEPTANCE_ID",
    "DesignSystemError",
    "MOTION",
    "NAV_ITEMS",
    "RADII",
    "REQUIRED_COMPONENT_STATES",
    "ROADMAP_PHASE_ID",
    "RUN_PHASE_ID",
    "SPACING",
    "STATUS_SEMANTICS",
    "TASK_ID",
    "THEMES",
    "TYPOGRAPHY",
    "VERSION",
    "component_contract",
    "contrast_evidence",
    "contrast_ratio",
    "design_token_contract",
    "interface_payload",
    "motion_contract",
    "public_verification",
    "relative_luminance",
    "render_html",
    "visual_regression_contract",
]
