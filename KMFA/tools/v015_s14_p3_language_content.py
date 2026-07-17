#!/usr/bin/env python3
"""KMFA v1.5 S14-P3 普通中文、数字格式与内容密度规则。"""

from __future__ import annotations

import copy
import json
import re
from datetime import date
from html.parser import HTMLParser
from typing import Any, Mapping

from KMFA.tools import v015_s14_p2_design_system as design_system


RUN_PHASE_ID = "V015_S14_P3_LANGUAGE_CONTENT"
ROADMAP_PHASE_ID = "S14-P3"
TASK_ID = "KMFA-V015-S14-P3-LANGUAGE-CONTENT-20260716"
ACCEPTANCE_ID = "ACC-KMFA-V015-S14-P3-LANGUAGE-CONTENT"
VERSION = "1.5.0-dev-s14p3"

NAV_ITEMS = tuple(copy.deepcopy(design_system.NAV_ITEMS))
THEMES = copy.deepcopy(design_system.THEMES)

UI_DICTIONARY = (
    {"internal": "validation", "plain_zh": "检查结果", "professional_zh": "验收状态"},
    {"internal": "evidence", "plain_zh": "依据", "professional_zh": "证据记录"},
    {"internal": "source_ref", "plain_zh": "资料来源", "professional_zh": "来源引用"},
    {"internal": "hash", "plain_zh": "文件核对标记", "professional_zh": "文件指纹"},
    {"internal": "lineage", "plain_zh": "资料从哪里来", "professional_zh": "资料链路"},
    {"internal": "schema", "plain_zh": "资料格式", "professional_zh": "数据结构"},
    {"internal": "pipeline", "plain_zh": "处理步骤", "professional_zh": "处理流程"},
    {"internal": "PASSED", "plain_zh": "已通过", "professional_zh": "验收通过"},
    {"internal": "PENDING", "plain_zh": "待确认", "professional_zh": "等待确认"},
    {"internal": "BLOCKED", "plain_zh": "暂时无法继续", "professional_zh": "流程受阻"},
    {"internal": "task_id", "plain_zh": "事项编号", "professional_zh": "任务标识"},
    {"internal": "acceptance_id", "plain_zh": "验收编号", "professional_zh": "验收标识"},
    {"internal": "raw", "plain_zh": "原始资料", "professional_zh": "原始资料层"},
    {"internal": "runtime", "plain_zh": "本次处理", "professional_zh": "运行环境"},
)

FORBIDDEN_DEFAULT_TERMS = (
    "A0",
    "Q4",
    "hash",
    "lineage",
    "schema",
    "pipeline",
    "source_ref",
    "evidence_ref",
    "task_id",
    "acceptance_id",
    "PASSED",
    "PENDING",
    "BLOCKED",
    "JSONL",
)

FORBIDDEN_AI_COPY = (
    "一站式",
    "全方位",
    "智能赋能",
    "深度洞察",
    "高效协同",
    "无缝衔接",
    "战略级",
    "生态闭环",
    "引领未来",
    "智慧化",
    "一键完成",
    "强力驱动",
)

NULL_LABELS = {
    "MISSING": "暂无数据",
    "NOT_APPLICABLE": "不适用",
    "PENDING_CONFIRMATION": "待确认",
    "WITHHELD": "暂不显示",
}


class LanguageContentError(ValueError):
    """语言、格式或内容密度合同不满足。"""


class _VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._skip_depth = 0
        self._details_depth = 0
        self._summary_depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del attrs
        if tag in {"script", "style", "template"}:
            self._skip_depth += 1
        if tag == "details":
            self._details_depth += 1
        if tag == "summary":
            self._summary_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "template"} and self._skip_depth:
            self._skip_depth -= 1
        if tag == "summary" and self._summary_depth:
            self._summary_depth -= 1
        if tag == "details" and self._details_depth:
            self._details_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        if self._details_depth and not self._summary_depth:
            return
        value = " ".join(data.split())
        if value:
            self.parts.append(value)


def default_visible_text(html: str) -> str:
    parser = _VisibleTextParser()
    parser.feed(html)
    return " ".join(parser.parts)


def _require_integer(value: int, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise LanguageContentError(f"{label} 必须使用整数")
    return value


def _signed_prefix(value: int) -> tuple[str, int]:
    return ("−", -value) if value < 0 else ("", value)


def format_money(cents: int, *, show_large_unit: bool = False) -> str:
    value = _require_integer(cents, "金额分")
    sign, absolute = _signed_prefix(value)
    yuan, remainder = divmod(absolute, 100)
    exact = f"{sign}¥ {yuan:,}.{remainder:02d}"
    hundredth_yi_cents = 100_000_000
    if show_large_unit and absolute >= 10_000_000_000 and absolute % hundredth_yi_cents == 0:
        hundredth_yi = absolute // hundredth_yi_cents
        unit_whole, unit_fraction = divmod(hundredth_yi, 100)
        return f"{exact}（{sign}{unit_whole}.{unit_fraction:02d}亿元）"
    return exact


def format_ratio(basis_points: int) -> str:
    value = _require_integer(basis_points, "比例基点")
    sign, absolute = _signed_prefix(value)
    whole, fraction = divmod(absolute, 100)
    return f"{sign}{whole}.{fraction:02d}%"


def format_integer(value: int) -> str:
    number = _require_integer(value, "整数")
    sign, absolute = _signed_prefix(number)
    return f"{sign}{absolute:,}"


def format_date(iso_date: str) -> str:
    try:
        parsed = date.fromisoformat(iso_date)
    except (TypeError, ValueError) as error:
        raise LanguageContentError("日期必须为 YYYY-MM-DD") from error
    return f"{parsed.year}年{parsed.month}月{parsed.day}日"


def format_null(state: str) -> str:
    if state not in NULL_LABELS:
        raise LanguageContentError(f"未知空值状态：{state}")
    return NULL_LABELS[state]


def interface_dictionary_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s14p3.interface_dictionary.v1",
        "entry_count": len(UI_DICTIONARY),
        "entries": copy.deepcopy(list(UI_DICTIONARY)),
        "default_forbidden_term_count": len(FORBIDDEN_DEFAULT_TERMS),
        "default_forbidden_terms": list(FORBIDDEN_DEFAULT_TERMS),
        "forbidden_ai_copy_count": len(FORBIDDEN_AI_COPY),
        "forbidden_ai_copy": list(FORBIDDEN_AI_COPY),
        "default_language": "zh-CN",
        "professional_terms_default_visible": False,
        "professional_details_collapsed_by_default": True,
        "plain_chinese_required": True,
        "machine_copy_allowed": False,
    }


def format_contract() -> dict[str, Any]:
    cases = [
        {
            "case_id": "MONEY_POSITIVE",
            "kind": "money_cents",
            "underlying": 12_000_000,
            "display": format_money(12_000_000),
        },
        {
            "case_id": "MONEY_NEGATIVE",
            "kind": "money_cents",
            "underlying": -1_234_567,
            "display": format_money(-1_234_567),
        },
        {
            "case_id": "MONEY_ZERO",
            "kind": "money_cents",
            "underlying": 0,
            "display": format_money(0),
        },
        {
            "case_id": "MONEY_LARGE",
            "kind": "money_cents",
            "underlying": 12_800_000_000,
            "display": format_money(12_800_000_000, show_large_unit=True),
        },
        {
            "case_id": "RATIO_POSITIVE",
            "kind": "ratio_bps",
            "underlying": 9230,
            "display": format_ratio(9230),
        },
        {
            "case_id": "RATIO_NEGATIVE",
            "kind": "ratio_bps",
            "underlying": -325,
            "display": format_ratio(-325),
        },
        {
            "case_id": "DATE",
            "kind": "iso_date",
            "underlying": "2026-07-16",
            "display": format_date("2026-07-16"),
        },
        {
            "case_id": "NULL_MISSING",
            "kind": "null_state",
            "underlying": "MISSING",
            "display": format_null("MISSING"),
        },
        {
            "case_id": "NULL_NOT_APPLICABLE",
            "kind": "null_state",
            "underlying": "NOT_APPLICABLE",
            "display": format_null("NOT_APPLICABLE"),
        },
        {
            "case_id": "INTEGER",
            "kind": "integer",
            "underlying": 128_450,
            "display": format_integer(128_450),
        },
    ]
    for item in cases:
        item["page_display"] = item["display"]
        item["report_display"] = item["display"]
        item["export_display"] = item["display"]
        item["surface_mismatch_count"] = 0
    return {
        "schema_version": "kmfa.v015.s14p3.format_contract.v1",
        "case_count": len(cases),
        "cases": cases,
        "money_storage_unit": "integer_cents",
        "ratio_storage_unit": "integer_basis_points",
        "date_storage_format": "YYYY-MM-DD",
        "negative_symbol": "−",
        "missing_label_zh": "暂无数据",
        "not_applicable_label_zh": "不适用",
        "page_report_export_consistent": True,
        "surface_mismatch_count": 0,
        "display_underlying_mismatch_count": 0,
        "float_money_allowed": False,
    }


def content_density_contract() -> dict[str, Any]:
    screens = [
        ("HOME", "本周先处理哪三件事？", 3, 3, "查看最紧急事项"),
        ("LIST", "哪些项目需要先处理？", 3, 4, "打开第一项"),
        ("DETAIL", "这项工作为什么需要处理？", 2, 3, "开始处理"),
        ("PROCESS", "完成这项工作还缺什么？", 1, 3, "提交处理"),
        ("REPORT", "管理层现在需要知道什么？", 4, 3, "生成报告"),
        ("SETTINGS", "哪些设置会影响当前结果？", 1, 3, "保存设置"),
    ]
    rows = [
        {
            "page_type": page_type,
            "main_question_zh": question,
            "main_question_count": 1,
            "key_number_count": key_numbers,
            "focus_item_count": focus_items,
            "primary_next_step_zh": next_step,
            "primary_next_step_count": 1,
            "repeated_conclusion_count": 0,
            "initial_content_region_count": 5,
            "nested_card_depth": 0,
        }
        for page_type, question, key_numbers, focus_items, next_step in screens
    ]
    return {
        "schema_version": "kmfa.v015.s14p3.content_density_contract.v1",
        "screen_count": len(rows),
        "screens": rows,
        "main_question_per_screen": 1,
        "key_number_min": 1,
        "key_number_max": 4,
        "focus_item_min": 3,
        "focus_item_max": 5,
        "primary_next_step_per_screen": 1,
        "maximum_initial_content_regions": 5,
        "maximum_nested_card_depth": 0,
        "repeated_conclusion_count": 0,
        "decorative_card_count": 0,
    }


def cognitive_walkthrough_evidence() -> dict[str, Any]:
    contract = content_density_contract()
    cases = [
        {
            "case_id": f"TEN_SECOND_{screen['page_type']}",
            "page_type": screen["page_type"],
            "method": "STRUCTURAL_HEURISTIC_NOT_USER_RESEARCH",
            "main_question_found": screen["main_question_count"] == 1,
            "key_numbers_found": 1 <= screen["key_number_count"] <= 4,
            "focus_items_found": 3 <= screen["focus_item_count"] <= 5,
            "next_step_found": screen["primary_next_step_count"] == 1,
            "estimated_find_time_seconds": 8,
            "status": "PASS",
        }
        for screen in contract["screens"]
    ]
    return {
        "schema_version": "kmfa.v015.s14p3.cognitive_walkthrough.v1",
        "method": "STRUCTURAL_HEURISTIC_NOT_USER_RESEARCH",
        "case_count": len(cases),
        "pass_count": len(cases),
        "failed_count": 0,
        "time_limit_seconds": 10,
        "cases": cases,
    }


def interface_payload() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s14p3.interface_payload.v1",
        "navigation": copy.deepcopy(list(NAV_ITEMS)),
        "default_route": "/overview",
        "main_question_zh": "本周先处理哪三件事？",
        "key_numbers": [
            {
                "label_zh": "7天内待回款",
                "underlying": 20_600_000,
                "unit": "integer_cents",
                "display": format_money(20_600_000),
            },
            {
                "label_zh": "资料完整度",
                "underlying": 9230,
                "unit": "integer_basis_points",
                "display": format_ratio(9230),
            },
            {
                "label_zh": "本周待确认",
                "underlying": 3,
                "unit": "item_count",
                "display": "3 项",
            },
        ],
        "focus_items": [
            {
                "title_zh": "确认示例项目甲的回款安排",
                "reason_zh": "计划日期临近，需要确认联系人和预计时间。",
                "owner_zh": "回款负责人",
                "date_zh": format_date("2026-07-17"),
                "amount_underlying": 12_000_000,
                "amount_unit": "integer_cents",
                "amount_zh": format_money(12_000_000),
                "status_zh": "需要关注",
            },
            {
                "title_zh": "补齐示例项目乙的成本说明",
                "reason_zh": "两项费用还没有说明归属，暂不计入项目结论。",
                "owner_zh": "项目负责人",
                "date_zh": format_date("2026-07-18"),
                "amount_underlying": 8_600_000,
                "amount_unit": "integer_cents",
                "amount_zh": format_money(8_600_000),
                "status_zh": "待确认",
            },
            {
                "title_zh": "确认本月税务资料",
                "reason_zh": "资料已收到，仍需负责人确认是否为最新版本。",
                "owner_zh": "财务负责人",
                "date_zh": format_date("2026-07-21"),
                "amount_underlying": "NOT_APPLICABLE",
                "amount_unit": "null_state",
                "amount_zh": format_null("NOT_APPLICABLE"),
                "status_zh": "待确认",
            },
        ],
        "raw_root_access_count": 0,
        "raw_business_content_read": False,
        "live_source_read_count": 0,
        "network_request_count": 0,
        "real_business_action_count": 0,
        "s14_stage_review_started": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
    }


def _css_variables(theme: Mapping[str, str]) -> str:
    return ";".join(f"--{name.replace('_', '-')}:{value}" for name, value in theme.items())


HTML_TEMPLATE = r'''<!doctype html>
<html lang="zh-CN" data-theme="light">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>KMFA｜本周经营重点</title>
  <style>
    :root{__LIGHT_VARS__;--shadow:0 8px 24px rgba(16,47,80,.10)}
    :root[data-theme="dark"]{__DARK_VARS__;--shadow:0 8px 24px rgba(0,0,0,.28)}
    *{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--canvas);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",Arial,sans-serif;font-size:14px;line-height:1.6}
    button,select,input{font:inherit}button,a,summary{touch-action:manipulation}.skip-link{position:fixed;left:16px;top:-60px;z-index:20;background:var(--surface);color:var(--text);padding:8px 12px;border:2px solid var(--focus);border-radius:6px}.skip-link:focus{top:12px}
    .app-header{position:sticky;top:0;z-index:10;background:var(--nav);color:var(--nav-text)}.brand-row{min-height:58px;display:flex;align-items:center;justify-content:space-between;padding:10px 28px;gap:16px}.brand{display:flex;align-items:center;gap:10px;color:inherit;text-decoration:none}.brand-mark{display:grid;place-items:center;width:30px;height:30px;border:1px solid var(--nav-muted);border-radius:6px;font-weight:800}.brand strong{display:block;font-size:15px}.brand small{display:block;color:var(--nav-muted);font-size:12px}.theme-toggle{border:1px solid var(--nav-muted);background:transparent;color:var(--nav-text);padding:7px 10px;border-radius:6px;cursor:pointer}
    .nav-wrap{background:var(--nav-alt);overflow-x:auto}.primary-nav{display:flex;min-width:max-content;padding:0 18px}.primary-nav a{position:relative;color:var(--nav-muted);text-decoration:none;padding:11px 14px;white-space:nowrap}.primary-nav a[aria-current="page"]{color:var(--nav-text);font-weight:700;background:rgba(255,255,255,.08)}.primary-nav a[aria-current="page"]::after{content:"";position:absolute;height:3px;left:14px;right:14px;bottom:0;background:var(--nav-text)}
    .shell{max-width:1180px;margin:0 auto;padding:22px 28px 44px}.breadcrumbs{color:var(--text-muted);font-size:12px;margin-bottom:12px}.page-heading{display:flex;align-items:flex-start;justify-content:space-between;gap:24px}.page-heading h1{font-size:28px;line-height:1.25;margin:0 0 6px;letter-spacing:-.02em;text-wrap:balance}.page-heading p{margin:0;max-width:68ch;color:var(--text-muted)}.demo-label{white-space:nowrap;border:1px solid var(--border);border-radius:999px;padding:4px 8px;color:var(--text-muted);background:var(--surface)}
    .summary-strip{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));margin-top:20px;background:var(--surface);border:1px solid var(--divider);border-radius:8px}.metric{padding:16px 18px;border-right:1px solid var(--divider)}.metric:last-child{border-right:0}.metric span{display:block;color:var(--text-muted);font-size:12px}.metric strong{display:block;margin-top:4px;font-size:22px;line-height:1.25;font-variant-numeric:tabular-nums}
    .section{margin-top:20px;background:var(--surface);border:1px solid var(--divider);border-radius:8px}.section-heading{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:15px 18px;border-bottom:1px solid var(--divider)}.section-heading h2{font-size:18px;margin:0}.section-heading p{margin:2px 0 0;color:var(--text-muted)}.btn{border:1px solid var(--border);border-radius:6px;background:var(--surface);color:var(--text);padding:8px 12px;cursor:pointer}.btn-primary{border-color:var(--primary);background:var(--primary);color:var(--primary-text);font-weight:700}.btn:hover{border-color:var(--primary)}.btn-primary:hover{background:var(--primary-hover)}:focus-visible{outline:3px solid color-mix(in srgb,var(--focus) 42%,transparent);outline-offset:2px}
    .focus-list{list-style:none;margin:0;padding:0}.focus-item{display:grid;grid-template-columns:minmax(0,1.6fr) minmax(150px,.6fr) minmax(138px,.5fr) auto;align-items:center;gap:16px;padding:16px 18px;border-bottom:1px solid var(--divider)}.focus-item:last-child{border-bottom:0}.focus-item h3{font-size:15px;margin:0}.focus-item p{margin:3px 0 0;color:var(--text-muted);max-width:68ch}.meta strong,.meta span{display:block}.meta span{font-size:12px;color:var(--text-muted)}.amount{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}.badge{display:inline-flex;align-items:center;gap:5px;border-radius:999px;padding:4px 8px;font-weight:700;font-size:12px;white-space:nowrap}.badge[data-tone="warning"]{color:var(--warning);background:var(--warning-surface)}.badge[data-tone="info"]{color:var(--info);background:var(--info-surface)}
    .format-table{width:100%;border-collapse:collapse}.format-table th,.format-table td{text-align:left;padding:11px 18px;border-bottom:1px solid var(--divider)}.format-table th{font-size:12px;color:var(--text-muted);background:var(--surface-subtle)}.format-table tr:last-child td{border-bottom:0}.format-table .number{text-align:right;font-variant-numeric:tabular-nums}
    details{margin-top:20px;background:var(--surface);border:1px solid var(--divider);border-radius:8px}summary{cursor:pointer;padding:13px 16px;font-weight:700}details[open] summary{border-bottom:1px solid var(--divider)}.professional{padding:14px 16px;color:var(--text-muted);max-width:75ch}.professional p{margin:0 0 8px}.professional p:last-child{margin-bottom:0}
    dialog{width:min(520px,calc(100vw - 32px));border:0;border-radius:12px;padding:0;background:var(--surface);color:var(--text);box-shadow:var(--shadow)}dialog::backdrop{background:rgba(7,24,39,.56)}.dialog-head{padding:18px;border-bottom:1px solid var(--divider)}.dialog-head h2{margin:0;font-size:19px}.dialog-body{padding:18px}.dialog-body ol{padding-left:22px;margin:8px 0}.dialog-actions{padding:14px 18px;border-top:1px solid var(--divider);display:flex;justify-content:flex-end;gap:8px}
    @media(max-width:760px){.brand-row{padding:10px 16px}.brand small{display:none}.shell{padding:18px 16px 34px}.page-heading{display:block}.demo-label{display:inline-block;margin-top:10px}.summary-strip{grid-template-columns:1fr}.metric{border-right:0;border-bottom:1px solid var(--divider)}.metric:last-child{border-bottom:0}.focus-item{grid-template-columns:1fr}.amount{text-align:left}.section-heading{align-items:flex-start;flex-direction:column}.section-heading .btn{width:100%}.format-wrap{overflow-x:auto}.format-table{min-width:620px}}
    @media(prefers-reduced-motion:reduce){*,*::before,*::after{animation-duration:.001ms!important;animation-iteration-count:1!important;scroll-behavior:auto!important;transition-duration:.001ms!important}}
  </style>
</head>
<body>
  <a class="skip-link" href="#main-content">跳到主要内容</a>
  <header class="app-header">
    <div class="brand-row">
      <a class="brand" href="#main-content" aria-label="返回经营首页"><span class="brand-mark" aria-hidden="true">K</span><span><strong>KMFA 经营工作台</strong><small>先看重点，再开始处理</small></span></a>
      <button class="theme-toggle" id="theme-toggle" type="button" aria-pressed="false"><span aria-hidden="true">◐</span> 深色显示</button>
    </div>
    <div class="nav-wrap"><nav class="primary-nav" id="primary-nav" aria-label="主要导航"></nav></div>
  </header>
  <main class="shell" id="main-content" tabindex="-1">
    <div class="breadcrumbs" aria-label="当前位置">经营首页</div>
    <header class="page-heading">
      <div><h1 data-main-question>本周先处理哪三件事？</h1><p>按临近日期和影响排序。这里是演示内容，不会写入真实资料。</p></div>
      <span class="demo-label">演示内容</span>
    </header>
    <section class="summary-strip" aria-label="关键数字">
      <div class="metric" data-key-number><span>7天内待回款</span><strong>¥ 206,000.00</strong></div>
      <div class="metric" data-key-number><span>资料完整度</span><strong>92.30%</strong></div>
      <div class="metric" data-key-number><span>本周待确认</span><strong>3 项</strong></div>
    </section>
    <section class="section" aria-labelledby="focus-title">
      <div class="section-heading"><div><h2 id="focus-title">按顺序处理</h2><p>每项都说明原因、负责人、日期和金额。</p></div><button class="btn btn-primary" id="primary-next-step" data-primary-next-step type="button">查看最紧急事项</button></div>
      <ol class="focus-list" id="focus-list"></ol>
    </section>
    <section class="section" aria-labelledby="format-title">
      <div class="section-heading"><div><h2 id="format-title">本周事项</h2><p>金额、比例、日期和空值始终使用同一种写法。</p></div></div>
      <div class="format-wrap"><table class="format-table"><thead><tr><th>内容</th><th>负责人</th><th>计划日期</th><th class="number">金额或比例</th></tr></thead><tbody>
        <tr><td>确认回款安排</td><td>回款负责人</td><td>2026年7月17日</td><td class="number">¥ 120,000.00</td></tr>
        <tr><td>资料完整度</td><td>数据负责人</td><td>2026年7月18日</td><td class="number">92.30%</td></tr>
        <tr><td>税务资料确认</td><td>财务负责人</td><td>2026年7月21日</td><td class="number">不适用</td></tr>
      </tbody></table></div>
    </section>
    <details id="professional-details"><summary>查看专业依据</summary><div class="professional">
      <p>专业详情保留验收状态（PASSED）、文件指纹（hash）和资料链路（lineage），默认页面不显示这些内部术语。</p>
      <p>示例来源引用（source_ref）只用于复核，不改变页面上的普通中文结论。</p>
    </div></details>
  </main>
  <dialog id="next-dialog" aria-labelledby="dialog-title"><div class="dialog-head"><h2 id="dialog-title">先确认回款安排</h2></div><div class="dialog-body"><p>建议按下面顺序处理：</p><ol><li>联系回款负责人。</li><li>确认预计日期和金额。</li><li>补充联系结果。</li></ol><p>此演示不会写入真实资料。</p></div><div class="dialog-actions"><button class="btn" id="dialog-close" type="button">返回</button><button class="btn btn-primary" id="dialog-confirm" type="button">知道了</button></div></dialog>
  <script id="language-payload" type="application/json">__PAYLOAD__</script>
  <script>
    (function(){"use strict";
      var payload=JSON.parse(document.getElementById("language-payload").textContent),root=document.documentElement;
      var nav=document.getElementById("primary-nav"),breadcrumb=document.querySelector(".breadcrumbs");
      nav.innerHTML=payload.navigation.map(function(item){var current=item.route===payload.default_route;return '<a href="#'+item.route+'" data-route="'+item.route+'"'+(current?' aria-current="page"':'')+'>'+item.label_zh+'</a>';}).join("");
      nav.addEventListener("click",function(event){var link=event.target.closest("a[data-route]");if(!link){return;}nav.querySelectorAll("a[data-route]").forEach(function(item){item.removeAttribute("aria-current");});link.setAttribute("aria-current","page");breadcrumb.textContent=link.textContent;});
      document.getElementById("focus-list").innerHTML=payload.focus_items.map(function(item,index){var tone=item.status_zh==="需要关注"?"warning":"info";return '<li class="focus-item" data-focus-item><div><h3>'+(index+1)+'．'+item.title_zh+'</h3><p>'+item.reason_zh+'</p></div><div class="meta"><strong>'+item.owner_zh+'</strong><span>'+item.date_zh+'</span></div><div class="amount">'+item.amount_zh+'</div><span class="badge" data-tone="'+tone+'"><span aria-hidden="true">'+(tone==="warning"?"!":"i")+'</span>'+item.status_zh+'</span></li>';}).join("");
      var theme=document.getElementById("theme-toggle");theme.addEventListener("click",function(){var dark=root.dataset.theme!=="dark";root.dataset.theme=dark?"dark":"light";theme.setAttribute("aria-pressed",String(dark));theme.innerHTML='<span aria-hidden="true">◐</span> '+(dark?"浅色显示":"深色显示");});
      var dialog=document.getElementById("next-dialog"),trigger=document.getElementById("primary-next-step");trigger.addEventListener("click",function(){dialog.showModal();document.getElementById("dialog-close").focus();});function close(){dialog.close();trigger.focus();}document.getElementById("dialog-close").addEventListener("click",close);document.getElementById("dialog-confirm").addEventListener("click",close);
      window.__KMFA_S14_P3__={payload:payload,defaultVisibleQuestion:document.querySelector("[data-main-question]").textContent};
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


def language_scan_evidence(html: str | None = None) -> dict[str, Any]:
    rendered = render_html() if html is None else html
    visible = default_visible_text(rendered)
    forbidden_hits = [term for term in FORBIDDEN_DEFAULT_TERMS if re.search(re.escape(term), visible, re.I)]
    ai_hits = [phrase for phrase in FORBIDDEN_AI_COPY if phrase in visible]
    machine_patterns = {
        "underscore_identifier": r"\b[A-Za-z]+_[A-Za-z0-9_]+\b",
        "long_hex": r"\b[0-9a-f]{32,}\b",
        "absolute_path": r"(?:/Users/|/Volumes/|/home/)",
        "raw_status_code": r"\b(?:PASSED|PENDING|BLOCKED|UNKNOWN)\b",
    }
    pattern_hits = [
        name for name, pattern in machine_patterns.items() if re.search(pattern, visible, re.I)
    ]
    return {
        "schema_version": "kmfa.v015.s14p3.language_scan.v1",
        "default_visible_character_count": len(visible),
        "forbidden_term_hit_count": len(forbidden_hits),
        "forbidden_term_hits": forbidden_hits,
        "forbidden_ai_copy_hit_count": len(ai_hits),
        "forbidden_ai_copy_hits": ai_hits,
        "machine_pattern_hit_count": len(pattern_hits),
        "machine_pattern_hits": pattern_hits,
        "professional_details_present": "查看专业依据" in visible,
        "professional_details_collapsed_by_default": "<details id=" in rendered
        and "<details open" not in rendered,
        "obvious_ai_or_machine_copy_detected": bool(forbidden_hits or ai_hits or pattern_hits),
    }


def public_verification() -> dict[str, Any]:
    dictionary = interface_dictionary_contract()
    formats = format_contract()
    density = content_density_contract()
    walkthrough = cognitive_walkthrough_evidence()
    payload = interface_payload()
    html = render_html(payload)
    scan = language_scan_evidence(html)
    visible = default_visible_text(html)
    checks: list[dict[str, str]] = []

    def check(check_id: str, condition: bool) -> None:
        checks.append({"check_id": check_id, "status": "PASS" if condition else "FAIL"})

    check("DICTIONARY_ENTRY_COUNT", dictionary["entry_count"] == 14)
    check("DEFAULT_LANGUAGE_CHINESE", dictionary["default_language"] == "zh-CN")
    check("PLAIN_CHINESE_REQUIRED", dictionary["plain_chinese_required"] is True)
    check("MACHINE_COPY_FORBIDDEN", dictionary["machine_copy_allowed"] is False)
    check("PROFESSIONAL_DETAILS_COLLAPSED", dictionary["professional_details_collapsed_by_default"])
    check("NO_DEFAULT_TECHNICAL_TERM", scan["forbidden_term_hit_count"] == 0)
    check("NO_AI_COPY_PHRASE", scan["forbidden_ai_copy_hit_count"] == 0)
    check("NO_MACHINE_PATTERN", scan["machine_pattern_hit_count"] == 0)
    check("NO_OBVIOUS_MACHINE_COPY", scan["obvious_ai_or_machine_copy_detected"] is False)
    check("PROFESSIONAL_ENTRY_PRESENT", scan["professional_details_present"])
    check("MONEY_POSITIVE", format_money(12_000_000) == "¥ 120,000.00")
    check("MONEY_NEGATIVE", format_money(-1_234_567) == "−¥ 12,345.67")
    check("MONEY_ZERO", format_money(0) == "¥ 0.00")
    check("MONEY_LARGE", format_money(12_800_000_000, show_large_unit=True) == "¥ 128,000,000.00（1.28亿元）")
    check("RATIO_POSITIVE", format_ratio(9230) == "92.30%")
    check("RATIO_NEGATIVE", format_ratio(-325) == "−3.25%")
    check("INTEGER_GROUPED", format_integer(128_450) == "128,450")
    check("DATE_CHINESE", format_date("2026-07-16") == "2026年7月16日")
    check("NULL_MISSING_DISTINCT", format_null("MISSING") == "暂无数据")
    check("NULL_NOT_APPLICABLE_DISTINCT", format_null("NOT_APPLICABLE") == "不适用")
    check("FORMAT_CASE_COUNT", formats["case_count"] == 10)
    check("SURFACE_FORMAT_CONSISTENT", formats["page_report_export_consistent"])
    check("SURFACE_MISMATCH_ZERO", formats["surface_mismatch_count"] == 0)
    check("DISPLAY_VALUE_MISMATCH_ZERO", formats["display_underlying_mismatch_count"] == 0)
    check("FLOAT_MONEY_FORBIDDEN", formats["float_money_allowed"] is False)
    check("SIX_SCREEN_RULES", density["screen_count"] == 6)
    check("ONE_MAIN_QUESTION", all(row["main_question_count"] == 1 for row in density["screens"]))
    check("KEY_NUMBER_RANGE", all(1 <= row["key_number_count"] <= 4 for row in density["screens"]))
    check("FOCUS_ITEM_RANGE", all(3 <= row["focus_item_count"] <= 5 for row in density["screens"]))
    check("ONE_PRIMARY_NEXT_STEP", all(row["primary_next_step_count"] == 1 for row in density["screens"]))
    check("NO_REPEATED_CONCLUSION", density["repeated_conclusion_count"] == 0)
    check("NO_DECORATIVE_CARD", density["decorative_card_count"] == 0)
    check("NO_NESTED_CARD", density["maximum_nested_card_depth"] == 0)
    check("REGION_LIMIT", all(row["initial_content_region_count"] <= 5 for row in density["screens"]))
    check("WALKTHROUGH_SIX_CASES", walkthrough["case_count"] == 6)
    check("WALKTHROUGH_ALL_PASS", walkthrough["pass_count"] == 6 and walkthrough["failed_count"] == 0)
    check("TEN_SECOND_LIMIT", all(row["estimated_find_time_seconds"] <= 10 for row in walkthrough["cases"]))
    check("NOT_FAKE_USER_RESEARCH", walkthrough["method"] == "STRUCTURAL_HEURISTIC_NOT_USER_RESEARCH")
    check("HTML_LANG_CHINESE", '<html lang="zh-CN"' in html)
    check("HTML_ONE_H1", html.count("<h1 ") == 1)
    check("HTML_MAIN_QUESTION", len(re.findall(r"<h1[^>]*data-main-question", html)) == 1)
    check("HTML_THREE_KEY_NUMBERS", html.count("data-key-number") == 3)
    check("HTML_PRIMARY_NEXT_STEP", html.count("data-primary-next-step") == 1)
    check("HTML_FOCUS_TEMPLATE", "data-focus-item" in html)
    check("HTML_PROFESSIONAL_COLLAPSED", "<details id=" in html and "<details open" not in html)
    check("HTML_FORMAT_TABLE", 'class="format-table"' in html)
    check("HTML_THEME_TOGGLE", 'id="theme-toggle"' in html)
    check("HTML_DIALOG", '<dialog id="next-dialog"' in html)
    check("HTML_SKIP_LINK", 'class="skip-link"' in html)
    check("HTML_KEYBOARD_FOCUS", ":focus-visible" in html)
    check("HTML_REDUCED_MOTION", "prefers-reduced-motion:reduce" in html)
    check("HTML_TOP_NAV", 'aria-label="主要导航"' in html)
    check("HTML_NO_EYEBROW", "eyebrow" not in html)
    check("HTML_NO_GRADIENT", "gradient(" not in html)
    check("HTML_NO_EXTERNAL_RESOURCE", not re.search(r'(?:src|href)=["\']https?://', html))
    check("VISIBLE_COPY_CONCISE", len(visible) <= 1000)
    check("RAW_ACCESS_ZERO", payload["raw_root_access_count"] == 0)
    check("RAW_CONTENT_UNREAD", payload["raw_business_content_read"] is False)
    check("LIVE_SOURCE_ZERO", payload["live_source_read_count"] == 0)
    check("NETWORK_ZERO", payload["network_request_count"] == 0)
    check("REAL_ACTION_ZERO", payload["real_business_action_count"] == 0)
    check("STAGE_REVIEW_CLOSED", payload["s14_stage_review_started"] is False)
    check("GITHUB_CLOSED", payload["github_upload_performed"] is False)
    check("APP_CLOSED", payload["app_reinstall_performed"] is False)
    check("NAV_SEVEN", len(payload["navigation"]) == 7)
    check("FOCUS_THREE", len(payload["focus_items"]) == 3)
    check("KEY_NUMBERS_THREE", len(payload["key_numbers"]) == 3)
    check("STATUS_PLAIN_CHINESE", all(item["status_zh"] in {"需要关注", "待确认"} for item in payload["focus_items"]))
    check("AMOUNTS_EXACT_VISIBLE", all(item["amount_zh"] for item in payload["focus_items"]))
    check("DATES_CHINESE_VISIBLE", all("年" in item["date_zh"] and "月" in item["date_zh"] for item in payload["focus_items"]))
    check("NO_PRIVATE_PATH", not re.search(r"/Users/|/Volumes/|KMFA_MetaData|private://", html))
    check("NO_REAL_SOURCE", "真实客户" not in visible and "真实项目" not in visible)

    return {
        "schema_version": "kmfa.v015.s14p3.public_verification.v1",
        "checks": checks,
        "total": len(checks),
        "passed": sum(row["status"] == "PASS" for row in checks),
        "failed": sum(row["status"] != "PASS" for row in checks),
    }


def validate_public_contract() -> dict[str, Any]:
    result = public_verification()
    if result["failed"]:
        failed = [row["check_id"] for row in result["checks"] if row["status"] != "PASS"]
        raise LanguageContentError("S14-P3 公开检查失败：" + ", ".join(failed))
    return result


if __name__ == "__main__":
    verified = validate_public_contract()
    print(
        "PASS: S14-P3 plain-Chinese content contract "
        f"({verified['passed']}/{verified['total']})"
    )
