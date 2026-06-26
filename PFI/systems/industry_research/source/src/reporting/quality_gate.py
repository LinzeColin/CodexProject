from __future__ import annotations

import json
import re
from datetime import date, datetime, timedelta
from pathlib import Path

from src.data_io import read_csv
from src.integrations.policy_system_bridge import EVENT_DIR as POLICY_EVENT_DIR
from src.integrations.policy_system_bridge import STATUS_DIR as POLICY_STATUS_DIR
from src.reporting.naming import (
    daily_report_name,
    kline_report_name,
    legacy_daily_report_name,
    legacy_kline_report_name,
    legacy_weekly_report_name,
    weekly_report_name,
)
from src.reporting.paths import markdown_path, pdf_path, pfi_os_dir, source_log_path, weekly_report_dir
from src.reporting.schedule import REPORT_DUE_TIMES
from src.monitoring.report_layer import report_layer_quality_issues


FORBIDDEN_PHRASES = [
    "交易建议系统",
    "交易建议动作",
    "交易动作",
    "交易证据",
    "可以卖出",
    "适合买入",
    "主动买入",
    "建议把资金",
    "sell_or_avoid",
    "账户总体信息",
    "账户 Dashboard",
    "必须复核",
    "复核",
    "投资决策质量 Dashboard",
    "等待更多样本",
    "当前结论可能被单日涨跌过度影响",
    "技术面偏强，但仍需确认",
    "仍需确认行业",
    "等待基本面",
    "观望但记录强弱变化",
    "低：账户缺口，执行归零；行情可核、成交额可核、PFIOS=NeedsMoreEvidence、风险闸门阻断",
    "可保留原Volume上限",
    "量价背离则降到50%",
    "买入降额到50% Volume",
    "只执行 50% Volume",
    "降到50% Volume",
    "降到50%或取消",
    "则执行原Volume",
    "保留原Volume",
    "保持原Volume",
    "原 Volume",
    "按报告 Volume 执行",
    "按报告 Volume 上限执行",
    "按Volume上限",
    "买入降额",
    "卖出降额",
    "卖出减半",
    "降额、暂停",
    "ContinueResearch",
    "ValidationQueued",
    "NeedsMoreEvidence",
    "DataQualityReview",
    "DoNotUse",
    "WatchOnly",
    "NotValidated",
]

MARKET_STRUCTURE_REPORTS = {"pre_open", "midday", "post_close", "monday_pre_open", "friday_post_close"}
KLINE_MIN_PDF_PAGES = 50
KLINE_REQUIRED_INDICATORS = ["MA", "EMA", "BOLL", "MACD", "VOL", "RSI", "KDJ"]
STALE_POLICY_EVENT_TERMS = [
    "十四五",
    "十三五",
    "十二五",
    "十一五",
    "第十四个五年规划",
    "第十三个五年规划",
    "第十二个五年规划",
    "第十一个五年规划",
    "信息处理费",
    "行政复议",
    "规章集中公开",
    "年度报告格式",
    "公共企事业单位信息公开",
]
REQUIRED_SECTIONS = {
    "pre_open": [
        "目录",
        "仓位操作建议",
        "信号质量矩阵",
        "盘前 / 盘中 / 盘后对比复盘",
        "关键事实、事件与市场结构",
        "研究可信度与 PFIOS 验证",
        "操作纪律与反方校验",
        "收盘执行规则与风控",
        "持仓与支付宝历史交易附图",
    ],
    "midday": [
        "目录",
        "仓位操作建议",
        "信号质量矩阵",
        "盘前 / 盘中 / 盘后对比复盘",
        "关键事实、事件与市场结构",
        "研究可信度与 PFIOS 验证",
        "操作纪律与反方校验",
        "收盘执行规则与风控",
        "持仓与支付宝历史交易附图",
    ],
    "post_close": [
        "目录",
        "仓位操作建议",
        "信号质量矩阵",
        "盘前 / 盘中 / 盘后对比复盘",
        "关键事实、事件与市场结构",
        "研究可信度与 PFIOS 验证",
        "操作纪律与反方校验",
        "收盘执行规则与风控",
        "持仓与支付宝历史交易附图",
    ],
    "kline": [
        "目录",
        "K线操作总表",
        "信号质量矩阵",
        "训练问题答案与分析逻辑",
        "证据缺口与操作规则",
        "反方情景动作矩阵",
        "K线候选池与强弱结论",
        "单标的多指标深度分析",
        "K线训练结论",
        "持仓与支付宝历史交易附图",
    ],
    "monday_pre_open": [
        "目录",
        "仓位操作建议",
        "信号质量矩阵",
        "周度对比复盘与优化结论",
        "关键事实、事件与市场结构",
        "研究可信度与 PFIOS 验证",
        "操作纪律与反方校验",
        "复合判断质量、策略胜率与风险清单",
        "持仓与支付宝历史交易附图",
    ],
    "friday_post_close": [
        "目录",
        "仓位操作建议",
        "信号质量矩阵",
        "周度对比复盘与优化结论",
        "关键事实、事件与市场结构",
        "研究可信度与 PFIOS 验证",
        "操作纪律与反方校验",
        "复合判断质量、策略胜率与风险清单",
        "持仓与支付宝历史交易附图",
    ],
}


def report_name_for_kind(report_kind: str, as_of: str) -> str:
    if report_kind in {"pre_open", "midday", "post_close"}:
        return daily_report_name(report_kind, as_of)
    if report_kind == "kline":
        return kline_report_name(as_of)
    if report_kind in {"monday_pre_open", "friday_post_close"}:
        return weekly_report_name(report_kind, as_of)
    raise ValueError(f"Unsupported report kind: {report_kind}")


def run_report_quality_gate(as_of: str, report_kind: str, strict_week_folder: bool = True) -> list[str]:
    report_name = report_name_for_kind(report_kind, as_of)
    issues: list[str] = []
    pdf = pdf_path(report_name + ".pdf")
    markdown = markdown_path(report_name + ".md")
    if not pdf.exists():
        issues.append(f"Missing PDF: {pdf}")
    elif pdf.stat().st_size < 10_000:
        issues.append(f"PDF is unexpectedly small: {pdf}")
    elif report_kind == "kline":
        page_count = pdf_page_count(pdf)
        if page_count < KLINE_MIN_PDF_PAGES:
            issues.append(f"K-line PDF has fewer than {KLINE_MIN_PDF_PAGES} pages: pages={page_count}, path={pdf}")
    issues.extend(_source_log_issues(report_name))
    if not markdown.exists():
        issues.append(f"Missing Markdown artifact: {markdown}")
        return issues
    content = markdown.read_text(encoding="utf-8")
    issues.extend(quality_issues_for_content(content, report_kind))
    issues.extend(_policy_bridge_issues(as_of, report_kind, content))
    issues.extend(_pfi_os_issues(as_of, content))
    issues.extend(_report_layer_issues(as_of))
    if strict_week_folder:
        issues.extend(_week_folder_issues(as_of))
    return issues


def quality_issues_for_content(content: str, report_kind: str) -> list[str]:
    issues = []
    for phrase in FORBIDDEN_PHRASES:
        if phrase in content:
            issues.append(f"Forbidden phrase found: {phrase}")
    for section in REQUIRED_SECTIONS[report_kind]:
        if section not in content:
            issues.append(f"Required section missing: {section}")
    issues.extend(_source_list_issues(content))
    issues.extend(_local_path_leak_issues(content))
    issues.extend(_fact_inference_opinion_issues(content))
    issues.extend(_confidence_table_issues(content))
    issues.extend(_counter_thesis_issues(content))
    issues.extend(_discipline_issues(content))
    issues.extend(_core_action_table_issues(content))
    issues.extend(_decision_density_issues(content, report_kind))
    issues.extend(_alipay_execution_gate_issues(content))
    issues.extend(_pfi_os_action_gate_issues(content))
    issues.extend(_signal_matrix_consistency_issues(content))
    if report_kind in MARKET_STRUCTURE_REPORTS:
        issues.extend(_market_structure_issues(content))
        issues.extend(_event_catalyst_issues(content))
    if report_kind in {"pre_open", "midday", "post_close"}:
        issues.extend(_daily_execution_rule_issues(content))
    if report_kind in {"monday_pre_open", "friday_post_close"}:
        issues.extend(_weekly_composite_issues(content))
    if report_kind == "kline":
        issues.extend(_kline_depth_issues(content))
    return issues


def _report_layer_issues(as_of: str) -> list[str]:
    return report_layer_quality_issues(as_of)


LOW_VALUE_DECISION_PHRASES = [
    "明确结论：观望；只记录强弱变化。",
    "普通观察：不占用资金，记录方向变化。",
    "维持观望；不因单日行情升级。",
    "结论：观望，等待升级证据。",
    "若反方触发：升级到重点观察；否则维持普通观望。",
]


def _decision_density_issues(content: str, report_kind: str) -> list[str]:
    if report_kind == "kline":
        return []
    issues = []
    for phrase in LOW_VALUE_DECISION_PHRASES:
        if phrase in content:
            issues.append(f"Low-density decision phrase must include trigger, metric, and fail action: {phrase}")
    sections = [
        _section_text(content, "仓位操作建议"),
        _section_text(content, "操作纪律与反方校验"),
        _section_text(content, "收盘执行规则与风控"),
        _section_text(content, "复合判断质量、策略胜率与风险清单"),
    ]
    decision_text = "\n".join(section for section in sections if section)
    if not decision_text:
        return issues
    conditional_markers = ["成交额", "PFIOS", "事件", "触发", "否则", "取消", "降额", "暂停", "升级", "Volume"]
    for line in decision_text.splitlines():
        stripped = line.strip()
        if not stripped or not any(token in stripped for token in ["观望", "等待确认", "等待账户确认"]):
            continue
        if not (stripped.startswith("|") or any(marker in stripped for marker in ["明确结论", "结论：", "普通观察", "维持观望", "若反方"])):
            continue
        if len(stripped) < 28:
            issues.append(f"Decision line too terse for business report: {stripped}")
            continue
        if "观望" in stripped and not any(marker in stripped for marker in conditional_markers):
            issues.append(f"Watch/wait decision lacks trigger metric or fail action: {stripped[:120]}")
    return issues


def pdf_page_count(path: Path) -> int:
    data = path.read_bytes()
    return len(re.findall(rb"/Type\s*/Page\b", data))


def allowed_week_pdf_names(as_of: str) -> set[str]:
    return {row["pdf_name"] for row in expected_week_reports(as_of)}


def legacy_report_name_for_kind(report_kind: str, as_of: str) -> str:
    if report_kind in {"pre_open", "midday", "post_close"}:
        return legacy_daily_report_name(report_kind, as_of)
    if report_kind == "kline":
        return legacy_kline_report_name(as_of)
    if report_kind in {"monday_pre_open", "friday_post_close"}:
        return legacy_weekly_report_name(report_kind, as_of)
    raise ValueError(f"Unsupported report kind: {report_kind}")


def expected_week_reports(as_of: str) -> list[dict[str, str]]:
    day = date.fromisoformat(as_of)
    monday = day - timedelta(days=day.weekday())
    friday = monday + timedelta(days=4)
    rows = [
        {
            "report_date": monday.isoformat(),
            "report_kind": "monday_pre_open",
            "pdf_name": weekly_report_name("monday_pre_open", monday.isoformat()) + ".pdf",
            "label": "周一报告",
        }
    ]
    for offset in range(5):
        current = (monday + timedelta(days=offset)).isoformat()
        rows.extend(
            [
                {
                    "report_date": current,
                    "report_kind": "pre_open",
                    "pdf_name": daily_report_name("pre_open", current) + ".pdf",
                    "label": "盘前报告",
                },
                {
                    "report_date": current,
                    "report_kind": "midday",
                    "pdf_name": daily_report_name("midday", current) + ".pdf",
                    "label": "盘中报告",
                },
                {
                    "report_date": current,
                    "report_kind": "post_close",
                    "pdf_name": daily_report_name("post_close", current) + ".pdf",
                    "label": "盘后报告",
                },
                {
                    "report_date": current,
                    "report_kind": "kline",
                    "pdf_name": kline_report_name(current) + ".pdf",
                    "label": "K线分析报告",
                },
            ]
        )
    rows.append(
        {
            "report_date": friday.isoformat(),
            "report_kind": "friday_post_close",
            "pdf_name": weekly_report_name("friday_post_close", friday.isoformat()) + ".pdf",
            "label": "周五报告",
        }
    )
    return rows


def week_report_status(
    as_of: str,
    through_date: str | None = None,
    run_quality: bool = True,
    now: datetime | None = None,
) -> dict[str, object]:
    through = date.fromisoformat(through_date or as_of)
    now_dt = now or datetime.now()
    folder = weekly_report_dir(as_of)
    rows = []
    for expected in expected_week_reports(as_of):
        report_date = date.fromisoformat(expected["report_date"])
        pdf = folder / expected["pdf_name"]
        display_pdf = pdf
        if report_date > through or (report_date == through and not _report_is_due(expected, report_date, now_dt)):
            status = "future"
            issues: list[str] = []
        elif report_date < through:
            historical_pdf = _existing_historical_pdf(folder, expected)
            if historical_pdf.exists():
                status = "historical_present"
                issues = []
                display_pdf = historical_pdf
            else:
                status = "historical_missing"
                issues = [f"Historical PDF missing and not backfilled by default: {pdf}"]
        elif not pdf.exists():
            status = "missing"
            issues = [f"Missing PDF: {pdf}"]
        elif run_quality:
            issues = run_report_quality_gate(expected["report_date"], expected["report_kind"], strict_week_folder=False)
            status = "quality_pass" if not issues else "quality_fail"
        else:
            status = "present"
            issues = []
        remediation = _remediation_for(status, expected, issues)
        rows.append(
            {
                **expected,
                "expected_pdf_name": expected["pdf_name"],
                "pdf_name": display_pdf.name,
                "pdf_path": str(display_pdf),
                "status": status,
                "issues": issues,
                "next_action": remediation["next_action"],
                "repair_command": remediation["repair_command"],
                "blocker_note": remediation["blocker_note"],
            }
        )
    folder_issues = _week_folder_issues(as_of) if folder.exists() else [f"Missing week report folder: {folder}"]
    return {
        "as_of": as_of,
        "through_date": through.isoformat(),
        "week_folder": str(folder),
        "expected_total": len(rows),
        "status_counts": _status_counts(rows),
        "folder_issues": folder_issues,
        "reports": rows,
    }


def _confidence_table_issues(content: str) -> list[str]:
    issues = []
    for row in _markdown_rows(content):
        if "研究等级" in row or len(row) < 6:
            continue
        level = next((cell for cell in row if cell in _LEVEL_ORDER), "")
        status = next((cell for cell in row if cell in _STATUS_CAPS), "")
        if not level or not status:
            continue
        cap = _STATUS_CAPS[status]
        if _LEVEL_ORDER[level] > _LEVEL_ORDER[cap]:
            issues.append(f"Research confidence exceeds PFIOS cap: level={level}, status={status}, row={' | '.join(row[:3])}")
    return issues


def _fact_inference_opinion_issues(content: str) -> list[str]:
    issues = []
    section = _section_text(content, "事实 / 推论 / 观点分层")
    if not section:
        section = _section_text(content, "关键事实、事件与市场结构")
    if not section:
        return issues
    for label in ["事实", "推论", "观点"]:
        marker = f"### {label}"
        if marker not in section:
            issues.append(f"Fact/inference/opinion layer missing: {label}")
            continue
        body = _subsection_text(section, marker)
        if len(_contentful_lines(body)) < 1:
            issues.append(f"Fact/inference/opinion layer is empty: {label}")
    return issues


def _counter_thesis_issues(content: str) -> list[str]:
    section = _section_text(content, "反方观点")
    if not section:
        section = _section_text(content, "操作纪律与反方校验") or _section_text(content, "基本面、价值面与反方校验")
    if not section:
        return []
    for table_rows in _markdown_tables(section):
        headers = table_rows[0]
        if "反方观点" not in headers:
            continue
        data_rows = [row for row in table_rows[1:] if any(cell and cell not in {"暂无", "无"} for cell in row)]
        if not data_rows:
            return ["Counter-thesis table has no substantive rows."]
        counter_idx = headers.index("反方观点")
        if all(counter_idx >= len(row) or len(row[counter_idx]) < 8 or row[counter_idx] in {"暂无", "无"} for row in data_rows):
            return ["Counter-thesis table lacks substantive counter arguments."]
        return []
    return ["Counter-thesis table missing."]


def _discipline_issues(content: str) -> list[str]:
    section = _section_text(content, "持仓纪律检查")
    if not section:
        section = _section_text(content, "操作纪律与反方校验") or _section_text(content, "基本面、价值面与反方校验")
    if not section:
        return []
    required_items = ["待确认订单", "现金缓冲", "情绪化"]
    return [f"Holding discipline check missing item: {item}" for item in required_items if item not in section]


def _core_action_table_issues(content: str) -> list[str]:
    section = _section_text(content, "仓位操作建议")
    if not section:
        return []
    issues = []
    if "信号质量矩阵" in section:
        issues.append("Signal quality matrix must be moved into the research confidence section, not nested under core action advice.")
    for table_rows in _markdown_tables(section):
        headers = table_rows[0]
        if not {"Name", "Position", "Volume"}.issubset(set(headers)):
            continue
        for required in ["复合质量分", "说服力", "操作结论", "Volume依据"]:
            if required not in headers:
                issues.append(f"Core action table missing persuasive/composite field: {required}")
        name_idx = headers.index("Name")
        position_idx = headers.index("Position")
        volume_idx = _first_index(headers, ["Volume"])
        volume_basis_idx = _first_index(headers, ["Volume依据", "volume_basis"])
        holding_idx = _first_index(headers, ["持仓金额", "holding_amount"])
        pending_idx = _first_index(headers, ["待确认金额", "pending_order_amount"])
        compact_text_indices = [idx for idx, header in enumerate(headers) if header in {"依据", "风险点", "Volume依据"}]
        for row in table_rows[1:]:
            if name_idx >= len(row) or position_idx >= len(row):
                continue
            for idx in compact_text_indices:
                if idx < len(row) and len(row[idx]) > 180:
                    issues.append(
                        "Core action table cell is too long for concise business layout: "
                        f"name={row[name_idx]}, header={headers[idx]}, length={len(row[idx])}"
                    )
            position = row[position_idx]
            volume = _numeric_cell_value(row[volume_idx]) if volume_idx is not None and volume_idx < len(row) else 0.0
            if abs(volume) > 1e-9 and volume_basis_idx is not None and volume_basis_idx < len(row):
                issues.extend(_volume_basis_issues(row[name_idx], position, row[volume_basis_idx]))
            if "指数背景" not in position and "汇率背景" not in position:
                continue
            holding = _numeric_cell_value(row[holding_idx]) if holding_idx is not None and holding_idx < len(row) else 0.0
            pending = _numeric_cell_value(row[pending_idx]) if pending_idx is not None and pending_idx < len(row) else 0.0
            if abs(holding) < 1e-9 and abs(pending) < 1e-9:
                issues.append(
                    "Core action table contains zero-holding background row; move it to signal matrix or market structure: "
                    f"name={row[name_idx]}, position={position}"
                )
    return issues


def _volume_basis_issues(name: str, position: str, basis: str) -> list[str]:
    text = str(basis or "").strip()
    if len(text) < 18:
        return [f"Core action table Volume basis is too weak: name={name}, position={position}"]
    dimension_groups = [
        ("price", ["跌幅项", "涨幅项", "价格", "涨跌"]),
        ("holding_return", ["亏损项", "收益项", "持有收益", "收益率"]),
        ("holding_weight", ["低仓项", "集中度项", "现仓", "持仓"]),
        ("volume_risk", ["放量扣减", "突破扣减", "量能", "成交额"]),
        ("cap", ["目标/风险上限", "现仓/单次上限", "上限"]),
    ]
    matched = [name for name, tokens in dimension_groups if any(token in text for token in tokens)]
    if len(matched) < 4:
        return [
            "Core action table Volume basis lacks enough sizing dimensions "
            f"(need price, holding return, holding weight, volume risk, cap): name={name}, position={position}"
        ]
    if not re.search(r"\d+(?:\.\d+)?%", text):
        return [f"Core action table Volume basis lacks numeric percentages: name={name}, position={position}"]
    return []


def _alipay_execution_gate_issues(content: str) -> list[str]:
    account_blocked = any(
        phrase in content
        for phrase in [
            "执行金额闸门阻断",
            "账户待更新",
            "账户更新确认前禁止",
            "本次可执行金额设为0",
            "今日支付宝流水/持仓未更新或未确认",
        ]
    )
    issues = []
    for table_rows in _markdown_tables(content):
        if not table_rows:
            continue
        headers = table_rows[0]
        position_idx = _first_index(headers, ["Position", "操作建议", "仓位动作", "操作"])
        if position_idx is None:
            continue
        volume_idx = _first_index(headers, ["Volume"])
        amount_idx = _first_index(headers, ["建议金额", "suggested_amount"])
        name_idx = _first_index(headers, ["Name", "名称", "代码", "Symbol"])
        for row in table_rows[1:]:
            if position_idx >= len(row):
                continue
            position = row[position_idx]
            if not _is_alipay_active_position(position):
                continue
            name = row[name_idx] if name_idx is not None and name_idx < len(row) else "unknown"
            account_pending = "账户待更新" in position
            if account_blocked and not account_pending:
                issues.append(
                    "Alipay execution is blocked but active buy/sell row is not marked account-update-pending: "
                    f"name={name}, position={position}"
                )
            if account_pending or account_blocked:
                if volume_idx is not None and volume_idx < len(row) and abs(_numeric_cell_value(row[volume_idx])) > 1e-9:
                    issues.append(
                        "Alipay account-update-pending buy/sell row must have Volume 0: "
                        f"name={name}, position={position}, volume={row[volume_idx]}"
                    )
                if amount_idx is not None and amount_idx < len(row) and abs(_numeric_cell_value(row[amount_idx])) > 1e-6:
                    issues.append(
                        "Alipay account-update-pending buy/sell row must have suggested amount 0: "
                        f"name={name}, position={position}, suggested_amount={row[amount_idx]}"
                    )
    return issues


def _pfi_os_action_gate_issues(content: str) -> list[str]:
    blocked = _pfi_os_blocked_names(content)
    if not blocked:
        return []
    issues = []
    for table_rows in _markdown_tables(content):
        if not table_rows:
            continue
        headers = table_rows[0]
        name_idx = _first_index(headers, ["Name", "名称", "代码", "Symbol"])
        position_idx = _first_index(headers, ["Position", "操作建议", "仓位动作", "操作"])
        volume_idx = _first_index(headers, ["Volume"])
        final_rule_idx = _first_index(headers, ["最终规则", "明确操作结论", "操作策略", "验证队列操作行为"])
        if name_idx is None:
            continue
        for row in table_rows[1:]:
            if name_idx >= len(row):
                continue
            name = row[name_idx]
            reason = blocked.get(name)
            if not reason:
                continue
            position = row[position_idx] if position_idx is not None and position_idx < len(row) else ""
            final_rule = row[final_rule_idx] if final_rule_idx is not None and final_rule_idx < len(row) else ""
            if _is_buy_action_text(position) and volume_idx is not None and volume_idx < len(row) and _numeric_cell_value(row[volume_idx]) > 0:
                issues.append(
                    "PFIOS blocked/insufficient validation cannot support nonzero buy Volume: "
                    f"name={name}, position={position}, volume={row[volume_idx]}, reason={reason}"
                )
            if _is_buy_action_text(position) and _pfi_os_final_rule_keeps_buy(final_rule):
                issues.append(
                    "PFIOS blocked/insufficient validation buy row must end in cancel/watch/wait, not buy-downsize: "
                    f"name={name}, position={position}, final_rule={final_rule}, reason={reason}"
                )
    return issues


def _signal_matrix_consistency_issues(content: str) -> list[str]:
    section = _section_text(content, "研究可信度与 PFIOS 验证")
    if not section or "信号质量矩阵" not in section:
        return []
    issues = []
    for table_rows in _markdown_tables(section):
        if not table_rows:
            continue
        headers = table_rows[0]
        position_idx = _first_index(headers, ["Position"])
        mixed_idx = _first_index(headers, ["混合结论"])
        volume_idx = _first_index(headers, ["VOL确认"])
        if position_idx is None:
            continue
        for row in table_rows[1:]:
            if len(row) <= position_idx:
                continue
            position = row[position_idx]
            mixed = row[mixed_idx] if mixed_idx is not None and mixed_idx < len(row) else ""
            if (
                any(token in position for token in ["账户待更新", "等待确认", "观望"])
                and ("执行原Volume" in mixed or "执行原 Volume" in mixed)
                and "不执行原Volume" not in mixed
                and "不执行原 Volume" not in mixed
            ):
                issues.append(f"Signal matrix conflicts with non-executable position by allowing original Volume: {position} | {mixed[:120]}")
            volume = row[volume_idx] if volume_idx is not None and volume_idx < len(row) else ""
            if any(token in position for token in ["账户待更新", "等待确认", "观望"]) and "保持原Volume上限" in volume:
                issues.append(f"Signal matrix volume confirmation conflicts with non-executable position: {position} | {volume[:120]}")
    return issues


def _pfi_os_blocked_names(content: str) -> dict[str, str]:
    blocked: dict[str, str] = {}
    blocked_statuses = {
        "NeedsMoreEvidence",
        "DataQualityReview",
        "DoNotUse",
        "证据不足-禁止执行买入",
        "数据质量待复核",
        "验证停用-不得执行",
    }
    for table_rows in _markdown_tables(content):
        if not table_rows:
            continue
        headers = table_rows[0]
        name_idx = _first_index(headers, ["Name", "名称"])
        status_idx = _first_index(headers, ["PFIOS状态", "验证状态"])
        gate_idx = _first_index(headers, ["风险闸门", "PFIOS闸门"])
        if name_idx is None or (status_idx is None and gate_idx is None):
            continue
        for row in table_rows[1:]:
            if name_idx >= len(row):
                continue
            name = row[name_idx]
            status = row[status_idx] if status_idx is not None and status_idx < len(row) else ""
            gate = row[gate_idx] if gate_idx is not None and gate_idx < len(row) else ""
            if status in blocked_statuses or gate in {"Blocked", "阻断"}:
                blocked[name] = f"status={status or 'unknown'}, gate={gate or 'unknown'}"
    return blocked


def _is_buy_action_text(value: str) -> bool:
    return any(token in value for token in ["买入", "补仓", "承接", "低仓位"])


def _pfi_os_final_rule_keeps_buy(value: str) -> bool:
    if not value:
        return False
    if any(token in value for token in ["取消", "观望", "等待", "暂停", "归零", "Volume 0", "Volume=0", "0%"]):
        return False
    return _is_buy_action_text(value)


def _is_alipay_active_position(value: str) -> bool:
    return any(token in value for token in ["买入", "补仓", "承接", "低仓位", "卖出", "减仓", "减暴露", "降暴露"])


def _numeric_cell_value(value: str) -> float:
    match = re.search(r"-?\d+(?:,\d{3})*(?:\.\d+)?|-?\d+(?:\.\d+)?", value.replace("，", ","))
    if not match:
        return 0.0
    return float(match.group(0).replace(",", ""))


def _market_structure_issues(content: str) -> list[str]:
    issues = []
    if "![A股板块热力图]" not in content:
        issues.append("A-share sector heatmap image missing.")
    if "![A股板块气泡图]" not in content:
        issues.append("A-share sector bubble map image missing.")
    for phrase in [
        "对象名称",
        "浅色背景",
        "热力图每格",
        "板块对象明细",
        "底部横轴=当日涨跌幅",
        "顶部横轴=",
        "左侧纵轴=复合质量分",
        "右侧纵轴=质量分区",
        "气泡大小=成交额",
        "颜色=涨跌方向",
        "气泡标注=对象名称",
    ]:
        if phrase not in content:
            issues.append(f"Market structure chart explanation missing: {phrase}")
    for phrase in [
        "中性观察：等待量价、事件和PFIOS同向。",
        "下跌但质量可跟踪：只看尾盘承接，放量破位则取消买入。",
        "强势且质量较高：保留重点跟踪，仍按单标的风险闸门决定Volume。",
        "质量偏低：不因单日涨跌扩大买卖。",
    ]:
        if phrase in content:
            issues.append(f"Low-density sector judgement must include metrics, trigger, and fail action: {phrase}")
    section = _section_text(content, "关键事实、事件与市场结构")
    if section and "板块对象明细" in section:
        for table_rows in _markdown_tables(section):
            if not table_rows or table_rows[0][:6] != ["板块/主题", "明确对象名称", "平均涨跌", "合计成交额", "复合质量分", "判断结论"]:
                continue
            for row in table_rows[2:]:
                if len(row) < 6:
                    continue
                judgement = row[-1]
                if "观察" in judgement or "跟踪" in judgement or "过滤" in judgement:
                    markers = ["平均涨跌", "质量分", "成交额"]
                    action_markers = ["升级条件", "取消", "降额", "不扩大", "Volume", "观望"]
                    if not all(marker in judgement for marker in markers) or not any(
                        marker in judgement for marker in action_markers
                    ):
                        issues.append(f"Sector judgement lacks metrics or action trigger: {judgement[:120]}")
    return issues


def _event_catalyst_issues(content: str) -> list[str]:
    section = _section_text(content, "关键事实、事件与市场结构")
    if not section:
        return []
    issues = []
    for phrase in ["原文核验", "来源链路", "操作影响", "政府文件解读系统", "原文抓取状态", "独立爬虫", "误读风险"]:
        if phrase not in section:
            issues.append(f"Event catalyst source chain missing: {phrase}")
    for phrase in STALE_POLICY_EVENT_TERMS:
        if phrase in section:
            issues.append(f"Event catalyst includes stale or low-relevance policy document: {phrase}")
    for line in section.splitlines():
        if line.lstrip().startswith("!["):
            continue
        if re.search(r"(独立爬虫请求|报告)\s+/(?:Users|private|tmp|var|Volumes)/", line):
            issues.append("Event catalyst must not expose local file paths in report body; keep paths in source logs.")
    issues.extend(_event_time_cell_issues(section))
    return issues


def _event_time_cell_issues(section: str) -> list[str]:
    issues = []
    for table_rows in _markdown_tables(section):
        if not table_rows:
            continue
        headers = table_rows[0]
        time_idx = _first_index(headers, ["时间（含年月日/来源当地时区）"])
        title_idx = _first_index(headers, ["事件/催化剂", "标题"])
        if time_idx is None:
            continue
        for row in table_rows[1:]:
            if time_idx >= len(row):
                continue
            title = row[title_idx] if title_idx is not None and title_idx < len(row) else ""
            if "暂无新增" in title or "暂无" == title:
                continue
            value = row[time_idx]
            if not re.search(r"\d{4}-\d{2}-\d{2}", value):
                issues.append(f"Event catalyst time missing full date: {value or '(empty)'}")
            if not _has_timezone_marker(value):
                issues.append(f"Event catalyst time missing timezone marker: {value or '(empty)'}")
    return issues


def _has_timezone_marker(value: str) -> bool:
    return bool(
        re.search(r"\b(?:Asia|Australia|America|Europe|UTC|GMT)/?[A-Za-z_]*\b", value)
        or re.search(r"(?:Z|[+-]\d{2}:?\d{2})\b", value)
    )


def _daily_execution_rule_issues(content: str) -> list[str]:
    section = _section_text(content, "收盘执行规则与风控")
    if not section:
        return ["Daily close execution rule section missing."]
    issues = []
    for phrase in ["检查时间", "账户闸门", "成立条件", "不成立动作", "证据缺口", "PFIOS闸门", "最终规则"]:
        if phrase not in section:
            issues.append(f"Daily close execution rule table missing: {phrase}")
    forbidden_headers = [
        ["排序", "代码", "名称", "涨跌幅", "成交额", "数据来源", "Position", "执行价值", "风险触发"],
        ["事件时间（含年月日/来源当地时间）", "类型", "标题", "影响", "来源"],
    ]
    for table_rows in _markdown_tables(content):
        if not table_rows:
            continue
        headers = table_rows[0]
        for forbidden in forbidden_headers:
            if all(header in headers for header in forbidden):
                issues.append("Daily report contains a low-value duplicate/raw table instead of the close execution rule checklist: " + ", ".join(headers))
    for headers in _raw_market_table_headers(content):
        issues.append(
            "Daily report contains a standalone symbol-level market/source table without composite quality, operation strategy, and failure action: "
            + ", ".join(headers)
        )
    return issues


def _weekly_composite_issues(content: str) -> list[str]:
    issues = []
    raw_header = "| 代码 | 名称 | 研究分组 | 价格 | 涨跌幅 | 成交额 |"
    if raw_header in content:
        issues.append("Weekly report still uses raw-only price/change/turnover table.")
    for headers in _raw_market_table_headers(content):
        issues.append(
            "Weekly report contains a standalone symbol-level market table without composite quality, win-rate proxy, operation strategy, and failure action: "
            + ", ".join(headers)
        )
    required = ["复合质量分", "策略胜率代理", "概率等级", "高概率盈利条件", "事件原文核验", "操作策略", "失败动作", "政策/事件支持", "量价证据"]
    for phrase in required:
        if phrase not in content:
            issues.append(f"Weekly composite strategy table missing: {phrase}")
    forbidden_event_headers = [
        ["事件时间（含年月日/来源当地时间）", "类型", "标题", "影响", "来源"],
        ["event_time", "type", "title", "impact", "source_name"],
    ]
    for table_rows in _markdown_tables(content):
        if not table_rows:
            continue
        headers = table_rows[0]
        for forbidden in forbidden_event_headers:
            if all(header in headers for header in forbidden):
                issues.append("Weekly report contains a low-value simplified event table; use the catalyst table with original-source verification instead: " + ", ".join(headers))
    return issues


def _raw_market_table_headers(content: str) -> list[list[str]]:
    weak_tables = []
    market_terms = {"价格", "收盘", "收盘价", "涨跌幅", "当日涨跌", "成交额", "成交量"}
    object_terms = {"Name", "名称", "代码", "Symbol", "标的"}
    required_composite_terms = {"复合质量分", "策略胜率代理", "事件原文核验", "操作策略", "失败动作"}
    for table_rows in _markdown_tables(content):
        if not table_rows:
            continue
        headers = table_rows[0]
        header_set = set(headers)
        has_object_column = bool(header_set & object_terms)
        market_hits = [header for header in headers if any(term == header or term in header for term in market_terms)]
        if not has_object_column or len(market_hits) < 2:
            continue
        if required_composite_terms.issubset(header_set):
            continue
        weak_tables.append(headers)
    return weak_tables


def _kline_depth_issues(content: str) -> list[str]:
    issues = []
    issues.extend(_kline_action_table_issues(content))
    issues.extend(_kline_low_value_duplicate_issues(content))
    issues.extend(_kline_candidate_pool_issues(content))
    for indicator in KLINE_REQUIRED_INDICATORS:
        if f"### {indicator} 单独/组合分析" not in content or f"![{indicator}]" not in content:
            issues.append(f"K-line indicator coverage missing: {indicator}")
            continue
        issues.extend(_kline_indicator_detail_issues(content, indicator))
    if "### MIX 单独/组合分析" not in content and "混合分析" not in content:
        issues.append("K-line mixed indicator analysis missing.")
    counts = _kline_observation_counts(content)
    if counts["total"] < 7:
        issues.append(f"K-line observation list has fewer than 7 symbols: total={counts['total']}")
    if counts["constructive"] < 3:
        issues.append(f"K-line constructive observation candidates fewer than 3: count={counts['constructive']}")
    if counts["risk_reduction"] < 3:
        issues.append(f"K-line risk-reduction observation candidates fewer than 3: count={counts['risk_reduction']}")
    if counts["watch"] < 1:
        issues.append(f"K-line watch-only observation candidates fewer than 1: count={counts['watch']}")
    return issues


def _kline_action_table_issues(content: str) -> list[str]:
    section = _section_text(content, "K线操作总表")
    if not section:
        return ["K-line action table section missing."]
    tables = _markdown_tables(section)
    if not tables:
        return ["K-line action table missing."]
    headers = tables[0][0]
    required = {"Name", "Position", "Volume", "复合质量分", "说服力", "操作结论", "依据", "风险点"}
    return [f"K-line action table missing high-value operation header: {header}" for header in sorted(required) if header not in headers]


def _kline_indicator_detail_issues(content: str, indicator: str) -> list[str]:
    section = _heading_section_text(content, f"### {indicator} 单独/组合分析")
    required = ["当前读数", "参考标准", "判断结论", "建议操作"]
    return [f"K-line indicator detail table missing for {indicator}: {phrase}" for phrase in required if phrase not in section]


def _kline_low_value_duplicate_issues(content: str) -> list[str]:
    forbidden = {
        "![A股板块热力图]": "K-line report must not repeat A-share heatmap from daily/weekly reports.",
        "![A股板块气泡图]": "K-line report must not repeat A-share bubble map from daily/weekly reports.",
        "板块对象明细": "K-line report must not include market-structure sector object table.",
        "关键事实、事件与市场结构": "K-line report must not repeat generic fact/event/market-structure section.",
        "事实 / 推论 / 观点分层": "K-line report must not repeat daily fact/inference/opinion block.",
        "催化剂与风险事件": "K-line report must not repeat event catalyst section.",
        "来源清单": "K-line report must not include source list; sources stay in logs.",
        "Source Log": "K-line report must not include source list; sources stay in logs.",
    }
    return [message for phrase, message in forbidden.items() if phrase in content]


def _kline_candidate_pool_issues(content: str) -> list[str]:
    section = _section_text(content, "K线候选池与强弱结论")
    if not section:
        return ["K-line candidate pool section missing."]
    tables = _markdown_tables(section)
    if not tables:
        return ["K-line candidate pool table missing."]
    headers = tables[0][0]
    issues = []
    forbidden_headers = {"持仓金额", "持有收益金额", "持有收益", "待确认金额", "现仓口径", "涨跌幅", "数据来源"}
    for header in forbidden_headers:
        if header in headers:
            issues.append(f"K-line candidate pool still looks like a watchlist/account snapshot; remove low-value header: {header}")
    required_headers = {"核心技术证据", "等待样本", "失效条件", "明确操作", "Volume闸门"}
    for header in required_headers:
        if header not in headers:
            issues.append(f"K-line candidate pool missing high-value decision header: {header}")
    wait_idx = _first_index(headers, ["等待样本"])
    if wait_idx is not None:
        wait_values = [
            row[wait_idx].strip()
            for row in tables[0][1:]
            if len(row) > wait_idx and row[wait_idx].strip()
        ]
        repeated = sorted({value for value in wait_values if wait_values.count(value) >= 3})
        for value in repeated:
            issues.append(f"K-line candidate pool uses repeated generic waiting sample; make it indicator-specific: {value[:80]}")
    return issues


def _kline_observation_counts(content: str) -> dict[str, int]:
    counts = {"total": 0, "constructive": 0, "risk_reduction": 0, "watch": 0}
    for table_rows in _markdown_tables(content):
        headers = table_rows[0]
        status_idx = _first_index(headers, ["K线研究分组", "观察状态", "Position"])
        if status_idx is None:
            continue
        if not any(header in headers for header in ["代码", "Symbol", "名称", "Name"]):
            continue
        for row in table_rows[1:]:
            if status_idx >= len(row):
                continue
            status = row[status_idx]
            if not status or status in {"观察状态", "Position", "K线研究分组"}:
                continue
            counts["total"] += 1
            if "买入" in status or "承接" in status or "低仓位" in status:
                counts["constructive"] += 1
            elif "卖出" in status or "减仓" in status or "减暴露" in status or "降暴露" in status:
                counts["risk_reduction"] += 1
            elif "观察" in status or "观望" in status:
                counts["watch"] += 1
    return counts


def _first_index(row: list[str], candidates: list[str]) -> int | None:
    for candidate in candidates:
        if candidate in row:
            return row.index(candidate)
    return None


def _section_text(content: str, heading_text: str) -> str:
    lines = content.splitlines()
    start = None
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("## ") and heading_text in stripped:
            start = idx + 1
            break
    if start is None:
        return ""
    end = len(lines)
    for idx in range(start, len(lines)):
        stripped = lines[idx].strip()
        if stripped.startswith("## "):
            end = idx
            break
    return "\n".join(lines[start:end]).strip()


def _subsection_text(section: str, marker: str) -> str:
    lines = section.splitlines()
    start = None
    for idx, line in enumerate(lines):
        if line.strip() == marker:
            start = idx + 1
            break
    if start is None:
        return ""
    end = len(lines)
    for idx in range(start, len(lines)):
        stripped = lines[idx].strip()
        if stripped.startswith("### ") and stripped != marker:
            end = idx
            break
    return "\n".join(lines[start:end]).strip()


def _heading_section_text(content: str, heading: str) -> str:
    lines = content.splitlines()
    start = None
    for idx, line in enumerate(lines):
        if line.strip() == heading:
            start = idx + 1
            break
    if start is None:
        return ""
    end = len(lines)
    for idx in range(start, len(lines)):
        stripped = lines[idx].strip()
        if stripped.startswith("## ") or stripped.startswith("### "):
            end = idx
            break
    return "\n".join(lines[start:end]).strip()


def _contentful_lines(text: str) -> list[str]:
    return [
        line
        for line in (item.strip() for item in text.splitlines())
        if line and not line.startswith("| ---") and not line.startswith("<!--")
    ]


def _source_list_issues(content: str) -> list[str]:
    issues = []
    forbidden_heading = re.compile(r"^#{1,6}\s*(来源清单|Source Log|Sources)\s*$", re.MULTILINE)
    if forbidden_heading.search(content):
        issues.append("Report must not include an in-body source list; sources must stay in source log artifacts.")
    return issues


def _local_path_leak_issues(content: str) -> list[str]:
    issues = []
    without_images = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", content)
    patterns = [
        (r"/Users/[^\s|)]+", "macOS user path"),
        (r"/private/(?:tmp|var)/[^\s|)]+", "private temp path"),
        (r"\bdata/report_artifacts/[^\s|)]+", "report artifact path"),
        (r"\b_source_logs\b|\b_markdown\b|\b_excel_outputs\b|\b_pfi_os\b", "internal artifact directory"),
        (r"\blocal://[^\s|)]+", "local URL"),
        (r"\bfile://[^\s|)]+", "file URL"),
    ]
    for pattern, label in patterns:
        match = re.search(pattern, without_images)
        if match:
            issues.append(f"Report body leaks internal {label}: {match.group(0)[:120]}")
    return issues


def _source_log_issues(report_name: str) -> list[str]:
    path = source_log_path(report_name)
    if not path.exists():
        return [f"Missing source log artifact: {path}"]
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"Source log JSON unreadable: {path}: {exc}"]
    issues = []
    if payload.get("report_name") != report_name:
        issues.append(f"Source log report_name mismatch: {path}")
    sources = payload.get("sources")
    if not isinstance(sources, list) or not sources:
        issues.append(f"Source log has no sources: {path}")
        return issues
    for idx, source in enumerate(sources):
        if not isinstance(source, dict):
            issues.append(f"Source log entry is not an object: index={idx}, path={path}")
            continue
        for field in ["source_name", "source_url", "fetch_time", "data_version"]:
            if not source.get(field):
                issues.append(f"Source log entry missing {field}: index={idx}, path={path}")
    return issues


def _policy_bridge_issues(as_of: str, report_kind: str, content: str) -> list[str]:
    issues = []
    status_path = POLICY_STATUS_DIR / f"policy_bridge_status_{as_of}.json"
    event_path = POLICY_EVENT_DIR / f"policy_events_{as_of}.csv"
    if not status_path.exists():
        return [f"Missing policy bridge status: {status_path}"]
    try:
        payload = json.loads(status_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"Policy bridge status JSON unreadable: {status_path}: {exc}"]
    refresh = payload.get("refresh") or {}
    refresh_status = str(refresh.get("status") or "unknown") if isinstance(refresh, dict) else "unknown"
    if refresh_status not in {"refreshed", "cached_refreshed"}:
        issues.append(f"Policy bridge refresh is not confirmed: status={refresh_status}")
    matched_event_count = int(payload.get("matched_event_count") or 0)
    event_rows = read_csv(event_path) if event_path.exists() else []
    if matched_event_count and not event_path.exists():
        issues.append(f"Missing policy bridge event log despite matched events: {event_path}")
    policy_rows = [row for row in event_rows if row.get("type") == "government_policy_bridge"]
    source_rows = [row for row in policy_rows if _has_original_source_url(row.get("source_url", ""))]
    non_no_match_rows = [row for row in policy_rows if row.get("policy_match_basis") != "no_high_relevance_policy_match"]
    if non_no_match_rows and not source_rows:
        issues.append("Policy catalyst rows lack original government/news/source URL verification.")
    for row in non_no_match_rows:
        if row.get("policy_original_fetch_status") != "verified":
            issues.append("Policy catalyst row lacks verified original fetch status.")
        if not row.get("policy_request_path"):
            issues.append("Policy catalyst row lacks separate crawler request path.")
        if not row.get("policy_operation_impact"):
            issues.append("Policy catalyst row lacks operation impact analysis.")
        if refresh_status in {"refreshed", "cached_refreshed"} and not row.get("policy_report_path"):
            issues.append("Policy catalyst row lacks policy system report path after refresh.")
    if "政府文件解读系统" in content and refresh_status not in {"refreshed", "cached_refreshed"}:
        issues.append("Report includes government policy bridge text but policy bridge refresh was not confirmed.")
    return issues


def _has_original_source_url(value: object) -> bool:
    url = str(value or "")
    if not url or "example.com" in url:
        return False
    return url.startswith("https://") or url.startswith("http://")


def _pfi_os_issues(as_of: str, content: str) -> list[str]:
    issues = []
    if "PFIOS 验证队列" not in content and "研究可信度与 PFIOS 验证" not in content:
        return issues
    summary_path = pfi_os_dir(as_of) / f"validation_summary_{as_of}.json"
    results_path = pfi_os_dir(as_of) / f"validation_results_{as_of}.csv"
    queue_path = pfi_os_dir(as_of) / f"thesis_queue_{as_of}.csv"
    for path in [summary_path, results_path, queue_path]:
        if not path.exists():
            issues.append(f"Missing PFIOS artifact: {path}")
    if summary_path.exists():
        payload = json.loads(summary_path.read_text(encoding="utf-8"))
        if int(payload.get("total") or 0) <= 0:
            issues.append("PFIOS summary has no validation rows.")
        if "100,000" not in str(payload.get("rule", "")) and "100000" not in str(payload.get("rule", "")):
            issues.append("PFIOS summary does not state the >=100,000 simulation rule.")
    if "100000次" not in content and "100,000" not in content:
        issues.append("Report does not show the PFIOS 100,000 simulation requirement/result.")
    if "全流程2次" not in content and "全流程>=2次" not in content:
        issues.append("Report does not show the PFIOS full-pipeline rerun requirement/result.")
    return issues


def _week_folder_issues(as_of: str) -> list[str]:
    folder = weekly_report_dir(as_of)
    issues = []
    if not folder.exists():
        return [f"Missing week report folder: {folder}"]
    allowed = allowed_week_pdf_names(as_of) | _allowed_historical_legacy_pdf_names(as_of)
    for path in sorted(folder.iterdir()):
        if path.is_dir():
            issues.append(f"Week folder contains subdirectory: {path}")
        elif path.suffix.lower() != ".pdf":
            issues.append(f"Week folder contains non-PDF artifact: {path}")
        elif path.name not in allowed:
            issues.append(f"Week folder contains unexpected PDF: {path.name}")
    return issues


def _allowed_historical_legacy_pdf_names(as_of: str) -> set[str]:
    day = date.fromisoformat(as_of)
    names = set()
    for row in expected_week_reports(as_of):
        if date.fromisoformat(row["report_date"]) < day:
            names.add(legacy_report_name_for_kind(row["report_kind"], row["report_date"]) + ".pdf")
    return names


def _existing_historical_pdf(folder: Path, expected: dict[str, str]) -> Path:
    current = folder / expected["pdf_name"]
    if current.exists():
        return current
    return folder / (legacy_report_name_for_kind(expected["report_kind"], expected["report_date"]) + ".pdf")


def _status_counts(rows: list[dict[str, object]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        status = str(row.get("status", ""))
        counts[status] = counts.get(status, 0) + 1
    return dict(sorted(counts.items()))


def _report_is_due(expected: dict[str, str], report_date: date, now: datetime) -> bool:
    if now.date() > report_date:
        return True
    if now.date() < report_date:
        return False
    due = REPORT_DUE_TIMES[expected["report_kind"]]
    return now.time() >= due


def _remediation_for(status: str, expected: dict[str, str], issues: list[str]) -> dict[str, str]:
    if status == "future":
        return {
            "next_action": "wait_until_report_time",
            "repair_command": "",
            "blocker_note": "报告日期晚于当前检查日期，或同日但尚未到生成时间；等待对应 automation 运行。",
        }
    if status in {"historical_present", "historical_missing"}:
        return {
            "next_action": "record_only_no_backfill",
            "repair_command": "",
            "blocker_note": "历史日期报告只做状态记录，不按最新框架自动补跑或重生成；避免用当前框架浪费资源更新过去报告。",
        }
    if status in {"missing", "quality_fail"}:
        report_date = expected["report_date"]
        report_kind = expected["report_kind"]
        generator = _generator_command(report_date, report_kind)
        if any("Missing Markdown artifact" in issue for issue in issues):
            action = "regenerate_report_artifacts"
        elif status == "missing":
            action = "generate_missing_report"
        else:
            action = "rerun_report_generation_and_quality_gate"
        return {
            "next_action": action,
            "repair_command": f"python3 -m src.cli pfi_os-refresh --date {report_date} && {generator}",
            "blocker_note": "正式补齐必须使用报告日期的可操作行情；若 OpenD/备用行情无法补齐，应失败，不应使用离线或错日数据。",
        }
    if status == "quality_pass":
        return {
            "next_action": "none",
            "repair_command": "",
            "blocker_note": "",
        }
    return {
        "next_action": "run_quality_check",
        "repair_command": f"python3 -m src.cli report-quality-check --date {expected['report_date']} --report-kind {expected['report_kind']}",
        "blocker_note": "",
    }


def _generator_command(report_date: str, report_kind: str) -> str:
    if report_kind in {"pre_open", "midday", "post_close"}:
        return f"python3 -m src.cli generate-daily --date {report_date} --session {report_kind}"
    if report_kind == "kline":
        return f"python3 -m src.cli generate-kline --date {report_date}"
    if report_kind in {"monday_pre_open", "friday_post_close"}:
        return f"python3 -m src.cli generate-weekly --date {report_date} --session {report_kind}"
    raise ValueError(f"Unsupported report kind: {report_kind}")


def _markdown_rows(content: str) -> list[list[str]]:
    return [row for table_rows in _markdown_tables(content) for row in table_rows]


def _markdown_tables(content: str) -> list[list[list[str]]]:
    tables = []
    current: list[list[str]] = []
    lines = content.splitlines()
    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped.startswith("|"):
            if current:
                tables.append(current)
                current = []
            continue
        if "---" in stripped:
            continue
        next_line = lines[index + 1].strip() if index + 1 < len(lines) else ""
        if current and next_line.startswith("|") and "---" in next_line:
            tables.append(current)
            current = []
        current.append([cell.strip() for cell in stripped.strip("|").split("|")])
    if current:
        tables.append(current)
    return tables


_LEVEL_ORDER = {
    "Insufficient Evidence": 0,
    "Watch Only": 1,
    "Low Confidence Research": 2,
    "Medium Confidence Research": 3,
    "High Confidence Research": 4,
}

_STATUS_CAPS = {
    "ContinueResearch": "High Confidence Research",
    "ValidationQueued": "Medium Confidence Research",
    "NeedsMoreEvidence": "Watch Only",
    "DataQualityReview": "Insufficient Evidence",
    "DoNotUse": "Insufficient Evidence",
    "WatchOnly": "Watch Only",
    "NotValidated": "Watch Only",
    "验证通过-可继续研究": "High Confidence Research",
    "排队验证-未完成": "Medium Confidence Research",
    "证据不足-禁止执行买入": "Watch Only",
    "数据质量待复核": "Insufficient Evidence",
    "验证停用-不得执行": "Insufficient Evidence",
    "仅观察": "Watch Only",
    "未验证-仅观察": "Watch Only",
}
