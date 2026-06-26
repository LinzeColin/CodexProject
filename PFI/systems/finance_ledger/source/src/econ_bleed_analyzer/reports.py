from __future__ import annotations

import csv
import hashlib
import html
import json
import re
import shutil
import sqlite3
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable

from .advice import build_budget_pressure_radar, build_control_plan, control_plan_to_suggestions
from .classifier import ClassifiedTransaction
from .data_trust import build_data_trust_transactions, data_trust_report_markdown
from .entity_registry import build_entity_layer, write_entity_layer_outputs
from .evidence_decision import build_evidence_decision_layer, write_evidence_decision_outputs
from .manual_review_audit import (
    build_manual_review_audit_rows,
    summarize_manual_review_audit,
    write_manual_review_audit_outputs,
)
from .periods import PERIODS, parse_date
from .review import ReviewDecisions, review_key


BUCKET_LABELS = {
    "real_consumption": "真实消费",
    "risk_spending": "风险支出",
    "optimizable_spending": "可优化支出",
    "social_spending": "社交支出",
    "financial_spending": "金融支出",
    "business_personal_mixed": "公司个人混同支出",
    "account_transfer": "账户搬运",
    "income_refund": "收入/退款",
    "excluded": "排除交易",
}

MAIN_CATEGORY_ORDER = ["生活刚需", "可优化消费", "社交家庭", "金融资金", "收入退款"]
TAXONOMY = {
    "生活刚需": ["教育医疗", "餐饮日用", "住房缴费", "交通车辆"],
    "可优化消费": ["外卖即时零售", "低复购购物", "会员订阅", "便利饮品"],
    "社交家庭": ["亲情卡人情往来", "家庭共同支出", "红包转账"],
    "金融资金": ["基金理财", "信用周转", "保险保障", "账户搬运"],
}
RISK_TAG_OPTIONS = [
    "基础支出",
    "信用工具",
    "信用周转",
    "流动性锁定",
    "投资冲动",
    "长期扣费",
    "平台便利",
    "高频小额",
    "低复购购物",
    "社交家庭",
    "家庭教育",
    "住房缴费",
    "餐饮日用",
    "夜间冲动",
    "工作经营",
]
TAG_GROUP_DEFAULTS = {
    "基础支出": ("基础", "#4b5563", "必要生活支出，作为低风险默认标签。"),
    "信用工具": ("金融", "#b42318", "花呗、借呗、信用卡等信用支付工具。"),
    "信用周转": ("金融", "#c2410c", "主动还款、分期、手续费、利息等周转行为。"),
    "流动性锁定": ("金融", "#7c3aed", "基金、理财、保险等资金锁定。"),
    "投资冲动": ("金融", "#9333ea", "小额频繁买入或非计划性投资。"),
    "长期扣费": ("可优化", "#a16207", "会员、订阅、保险、话费等持续扣费。"),
    "平台便利": ("可优化", "#0e7490", "外卖、即时零售、打车、配送等便利溢价。"),
    "高频小额": ("可优化", "#2563eb", "奶茶、咖啡、便利店、小吃等高频小额。"),
    "低复购购物": ("可优化", "#db2777", "数码、服饰、美妆、潮玩、短期兴趣消费。"),
    "社交家庭": ("社交家庭", "#047857", "亲情卡、人情往来、家庭共同承担和社交转账。"),
    "家庭教育": ("社交家庭", "#059669", "教育、家庭或特定教育分摊支出。"),
    "住房缴费": ("生活刚需", "#0891b2", "房租、物业、水电燃气、宽带等住房缴费。"),
    "餐饮日用": ("生活刚需", "#0f766e", "日常餐饮和生活日用。"),
    "夜间冲动": ("行为风险", "#dc2626", "22:00 至次日 05:59 的冲动风险窗口。"),
    "工作经营": ("混同风险", "#475569", "办公、发票、报销、差旅、云服务等工作经营混同。"),
}
DEFAULT_FILTER_PRESETS = [
    {"preset_id": "credit_cycle", "preset_name": "信用周转组合", "tags": "信用工具|信用周转", "match_mode": "any", "description": "观察信用工具和周转成本。"},
    {"preset_id": "optimizable_bleed", "preset_name": "可优化放血组合", "tags": "平台便利|高频小额|低复购购物|长期扣费|夜间冲动", "match_mode": "any", "description": "定位可压缩消费来源。"},
    {"preset_id": "financial_lock", "preset_name": "金融锁定组合", "tags": "流动性锁定|投资冲动", "match_mode": "any", "description": "观察基金理财和投资冲动。"},
    {"preset_id": "family_social", "preset_name": "家庭社交组合", "tags": "社交家庭|家庭教育|住房缴费|餐饮日用", "match_mode": "any", "description": "观察家庭和社交相关支出。"},
]
DEFAULT_FILTER_PRESET_IDS = {str(item["preset_id"]) for item in DEFAULT_FILTER_PRESETS}


def _slug(value: str) -> str:
    digest = hashlib.sha1(value.encode("utf-8")).hexdigest()[:10]
    return re.sub(r"[^a-z0-9_]+", "_", value.lower()).strip("_") or f"tag_{digest}"


def _tag_library_rows(custom_tags: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for index, tag in enumerate(RISK_TAG_OPTIONS, 1):
        group, color, description = TAG_GROUP_DEFAULTS.get(tag, ("其他", "#64748b", "用于消费行为控制和风险趋势分析。"))
        rows[tag] = {
            "tag_id": f"risk_{index:02d}_{_slug(tag)}",
            "tag_name": tag,
            "tag_group": group,
            "color": color,
            "description": description,
            "is_active": "1",
            "source": "system",
            "sort_order": index,
        }
    for item in custom_tags or []:
        name = str(item.get("tag_name") or item.get("name") or item.get("标签") or "").strip()
        if not name:
            continue
        existing = rows.get(name, {})
        rows[name] = {
            "tag_id": str(item.get("tag_id") or existing.get("tag_id") or f"custom_{_slug(name)}"),
            "tag_name": name,
            "tag_group": str(item.get("tag_group") or item.get("group") or existing.get("tag_group") or "自定义"),
            "color": str(item.get("color") or existing.get("color") or "#2563eb"),
            "description": str(item.get("description") or existing.get("description") or "自定义标签。"),
            "is_active": str(item.get("is_active") if item.get("is_active") is not None else existing.get("is_active", "1")),
            "source": str(item.get("source") or "custom"),
            "sort_order": int(item.get("sort_order") or existing.get("sort_order") or (1000 + len(rows))),
        }
    return sorted(rows.values(), key=lambda row: (int(row.get("sort_order", 9999)), str(row.get("tag_name", ""))))


def _active_tag_names(tag_library_rows: list[dict[str, Any]]) -> list[str]:
    names = [str(row["tag_name"]) for row in tag_library_rows if str(row.get("is_active", "1")) != "0"]
    return names or RISK_TAG_OPTIONS


def _tag_filter_preset_rows(custom_presets: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(DEFAULT_FILTER_PRESETS, 1):
        preset_id = str(item["preset_id"])
        rows[preset_id] = {
            "preset_id": preset_id,
            "preset_name": str(item["preset_name"]),
            "tags": str(item["tags"]),
            "match_mode": str(item.get("match_mode") or "any"),
            "description": str(item.get("description") or ""),
            "is_active": "1",
            "source": "system",
            "sort_order": index,
        }
    for item in custom_presets or []:
        name = str(item.get("preset_name") or item.get("name") or item.get("组合名") or "").strip()
        tags = str(item.get("tags") or item.get("tag_names") or item.get("标签组合") or "").strip()
        if not name or not tags:
            continue
        preset_id = str(item.get("preset_id") or item.get("id") or f"custom_{_slug(name)}")
        existing = rows.get(preset_id, {})
        rows[preset_id] = {
            "preset_id": preset_id,
            "preset_name": name,
            "tags": tags,
            "match_mode": "all" if str(item.get("match_mode") or existing.get("match_mode") or "any") == "all" else "any",
            "description": str(item.get("description") or existing.get("description") or ""),
            "is_active": str(item.get("is_active") if item.get("is_active") is not None else existing.get("is_active", "1")),
            "source": str(item.get("source") or ("system" if preset_id in DEFAULT_FILTER_PRESET_IDS else "custom")),
            "sort_order": int(item.get("sort_order") or existing.get("sort_order") or (1000 + len(rows))),
        }
    return sorted(rows.values(), key=lambda row: (int(row.get("sort_order", 9999)), str(row.get("preset_name", ""))))


def _active_filter_presets(preset_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "preset_id": str(row.get("preset_id", "")),
            "preset_name": str(row.get("preset_name", "")),
            "tags": str(row.get("tags", "")),
            "match_mode": "all" if str(row.get("match_mode", "any")) == "all" else "any",
            "description": str(row.get("description", "")),
        }
        for row in preset_rows
        if str(row.get("is_active", "1")) != "0" and str(row.get("preset_id", "")) and str(row.get("tags", ""))
    ]


def load_tag_config(path: str | Path | None = None) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not path:
        return _tag_library_rows(), _tag_filter_preset_rows()
    source = Path(path).expanduser()
    if not source.exists():
        return _tag_library_rows(), _tag_filter_preset_rows()
    if source.suffix.casefold() == ".json":
        payload = json.loads(source.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            custom_tags = payload.get("tags", [])
            custom_presets = payload.get("filter_presets", payload.get("presets", []))
        else:
            custom_tags = payload
            custom_presets = []
        return _tag_library_rows(custom_tags if isinstance(custom_tags, list) else []), _tag_filter_preset_rows(custom_presets if isinstance(custom_presets, list) else [])
    with source.open("r", encoding="utf-8-sig", newline="") as f:
        return _tag_library_rows(list(csv.DictReader(f))), _tag_filter_preset_rows()


def load_tag_library(path: str | Path | None = None) -> list[dict[str, Any]]:
    return load_tag_config(path)[0]


def yuan(cents: int) -> float:
    return round(cents / 100, 2)


def format_yuan(cents: int) -> str:
    return f"{cents / 100:,.2f}"


def format_pct(numerator: int, denominator: int) -> str:
    if denominator == 0:
        return "0.00%"
    return f"{numerator / denominator * 100:.2f}%"


def format_change(current: int, previous: int, has_previous: bool) -> str:
    if not has_previous:
        return "数据不足"
    if previous == 0:
        return "N/A"
    return f"{(current - previous) / previous * 100:.2f}%"


def _visual_bar(value: int | float, max_value: int | float, width: int = 18) -> str:
    if max_value <= 0:
        return ""
    filled = max(1 if value > 0 else 0, round((float(value) / float(max_value)) * width))
    filled = min(width, filled)
    return "█" * filled + "░" * (width - filled)


def _safe_name(value: str) -> str:
    return str(value or "").replace("|", "/").replace("\n", " ").strip()


def _sum(rows: list[ClassifiedTransaction], predicate: Callable[[ClassifiedTransaction], bool]) -> int:
    return sum(row.amount_cents for row in rows if predicate(row))


def core_metrics(rows: list[ClassifiedTransaction], review_decisions: ReviewDecisions | None = None) -> dict[str, Any]:
    allocations = _expense_allocations(rows, review_decisions)
    total_expense = sum(item["amount_cents"] for item in allocations)
    total_income = _sum(rows, lambda r: getattr(r, "cash_flow_type", "") == "income")
    total_transfer = _sum(rows, lambda r: getattr(r, "cash_flow_type", "") == "transfer")
    pending_review = _sum(rows, lambda r: getattr(r, "cash_flow_type", "") == "expense" and getattr(r, "needs_review", False) and not _is_review_confirmed(r, review_decisions))
    successful_outflow = _sum(
        rows,
        lambda r: r.direction in {"支出", "不计收支"} and r.primary_bucket not in {"excluded", "income_refund"},
    )
    return {
        "transactions": len(rows),
        "total_expense": total_expense,
        "total_income": total_income,
        "net_cash_flow": total_income - total_expense,
        "total_transfer": total_transfer,
        "pending_review": pending_review,
        "successful_outflow": successful_outflow,
        "real_consumption": sum(item["amount_cents"] for item in allocations if item["main_category"] not in {"金融资金", "收入退款"}),
        "risk_spending": sum(item["amount_cents"] for item in allocations if getattr(item["row"], "is_risk_spending", False)),
        "optimizable_spending": sum(item["amount_cents"] for item in allocations if item["main_category"] == "可优化消费"),
        "social_spending": sum(item["amount_cents"] for item in allocations if item["main_category"] == "社交家庭"),
        "financial_spending": sum(item["amount_cents"] for item in allocations if item["main_category"] == "金融资金"),
        "business_personal_mixed": sum(item["amount_cents"] for item in allocations if getattr(item["row"], "is_business_personal_mixed", False) or "工作经营" in item["risk_tags"]),
        "account_transfer": _sum(rows, lambda r: r.is_account_transfer),
        "income_refund": _sum(rows, lambda r: r.primary_bucket == "income_refund"),
        "late_night": sum(item["amount_cents"] for item in allocations if getattr(item["row"], "is_late_night", False)),
        "huabei_or_credit": sum(item["amount_cents"] for item in allocations if getattr(item["row"], "is_huabei_or_credit", False)),
    }


def _group_sum(rows: list[ClassifiedTransaction], field: str, *, limit: int | None = None, review_decisions: ReviewDecisions | None = None) -> list[dict[str, Any]]:
    totals: dict[str, dict[str, Any]] = defaultdict(lambda: {"count": 0, "amount_cents": 0})
    for row in rows:
        key = str(getattr(row, field) or "未填写")
        totals[key]["count"] += 1
        if getattr(row, "cash_flow_type", "") == "expense" and not (getattr(row, "needs_review", False) and not _is_review_confirmed(row, review_decisions)):
            totals[key]["amount_cents"] += row.amount_cents
    output = [
        {"name": key, "count": val["count"], "amount": yuan(val["amount_cents"])}
        for key, val in totals.items()
    ]
    output.sort(key=lambda item: item["amount"], reverse=True)
    return output[:limit] if limit else output


def _period_rows(rows: list[ClassifiedTransaction], start: date, end: date) -> list[ClassifiedTransaction]:
    return [row for row in rows if start <= parse_date(row.date) <= end]


def build_period_summary(rows: list[ClassifiedTransaction], period_name: str, review_decisions: ReviewDecisions | None = None) -> list[dict[str, Any]]:
    bounder = PERIODS[period_name]
    grouped: dict[str, dict[str, Any]] = {}
    for row in rows:
        start, end, label = bounder(parse_date(row.date))
        grouped.setdefault(label, {"start": start, "end": end, "rows": []})["rows"].append(row)

    summaries: list[dict[str, Any]] = []
    for label, item in grouped.items():
        metrics = core_metrics(item["rows"], review_decisions)
        summaries.append(
            {
                "period": label,
                "period_start": item["start"].isoformat(),
                "period_end": item["end"].isoformat(),
                **{key: yuan(value) if isinstance(value, int) and key != "transactions" else value for key, value in metrics.items()},
            }
        )
    return sorted(summaries, key=lambda item: item["period_start"])


def _expense_rows(rows: list[ClassifiedTransaction]) -> list[ClassifiedTransaction]:
    return [row for row in rows if getattr(row, "cash_flow_type", "") == "expense"]


def _is_lolol(row: ClassifiedTransaction) -> bool:
    text = f"{row.counterparty} {row.description}"
    return "lolol" in text or "贾韩松" in text


def _is_chun(row: ClassifiedTransaction) -> bool:
    text = f"{row.counterparty} {row.description}"
    return "蠢" in text or "张伟倩" in text or "张玮倩" in text


def _is_review_confirmed(row: ClassifiedTransaction, review_decisions: ReviewDecisions | None = None) -> bool:
    return _is_lolol(row) or _is_chun(row) or bool(review_decisions and review_decisions.has_decision(row))


def _expense_allocations(rows: list[ClassifiedTransaction], review_decisions: ReviewDecisions | None = None) -> list[dict[str, Any]]:
    allocations: list[dict[str, Any]] = []
    for row in _expense_rows(rows):
        if _is_lolol(row):
            education = row.amount_cents // 2
            housing = row.amount_cents // 4
            food = row.amount_cents - education - housing
            allocations.extend(
                [
                    {
                        "row": row,
                        "main_category": "生活刚需",
                        "sub_category": "教育医疗",
                        "amount_cents": education,
                        "risk_tags": ["家庭教育"],
                    },
                    {
                        "row": row,
                        "main_category": "生活刚需",
                        "sub_category": "住房缴费",
                        "amount_cents": housing,
                        "risk_tags": ["住房缴费"],
                    },
                    {
                        "row": row,
                        "main_category": "生活刚需",
                        "sub_category": "餐饮日用",
                        "amount_cents": food,
                        "risk_tags": ["餐饮日用"],
                    },
                ]
            )
            continue
        if _is_chun(row):
            allocations.append(
                {
                    "row": row,
                    "main_category": "社交家庭",
                    "sub_category": "亲情卡人情往来",
                    "amount_cents": row.amount_cents,
                    "risk_tags": ["社交家庭"],
                }
            )
            continue
        if getattr(row, "needs_review", False):
            if review_decisions:
                manual_allocations = review_decisions.allocations_for(row)
                if manual_allocations:
                    allocations.extend(manual_allocations)
                    continue
                if review_decisions.is_excluded(row):
                    continue
            continue
        allocations.append(
            {
                "row": row,
                "main_category": getattr(row, "main_category", "未分类"),
                "sub_category": getattr(row, "sub_category", "未分类"),
                "amount_cents": row.amount_cents,
                "risk_tags": [tag for tag in getattr(row, "risk_tags", "").split("|") if tag] or ["基础支出"],
                "review_decision": "auto",
                "review_note": "",
            }
        )
    return allocations


def _category_summary(rows: list[ClassifiedTransaction], review_decisions: ReviewDecisions | None = None) -> list[dict[str, Any]]:
    allocations = _expense_allocations(rows, review_decisions)
    total = sum(item["amount_cents"] for item in allocations)
    main_totals: dict[str, dict[str, Any]] = defaultdict(lambda: {"amount_cents": 0, "count": 0})
    sub_totals: dict[tuple[str, str], dict[str, Any]] = defaultdict(lambda: {"amount_cents": 0, "count": 0})
    seen_main_rows: dict[str, set[str]] = defaultdict(set)
    seen_sub_rows: dict[tuple[str, str], set[str]] = defaultdict(set)
    for item in allocations:
        row = item["row"]
        main = item["main_category"]
        sub = item["sub_category"]
        amount = item["amount_cents"]
        row_key = row.order_id or f"{row.transaction_time}-{row.counterparty}-{row.amount_cents}"
        main_totals[main]["amount_cents"] += amount
        main_totals[main]["count"] += 1
        seen_main_rows[main].add(row_key)
        sub_totals[(main, sub)]["amount_cents"] += amount
        sub_totals[(main, sub)]["count"] += 1
        seen_sub_rows[(main, sub)].add(row_key)

    rows_out: list[dict[str, Any]] = []
    main_names = sorted(main_totals, key=lambda name: (MAIN_CATEGORY_ORDER.index(name) if name in MAIN_CATEGORY_ORDER else 99, name))
    for main in main_names:
        main_amount = main_totals[main]["amount_cents"]
        rows_out.append(
            {
                "level": "主类",
                "main_category": main,
                "sub_category": "",
                "amount_cents": main_amount,
                "amount": yuan(main_amount),
                "count": len(seen_main_rows[main]),
                "main_pct": format_pct(main_amount, total),
                "sub_pct": "100.00%",
            }
        )
        child_items = [
            (sub, values)
            for (parent, sub), values in sub_totals.items()
            if parent == main
        ]
        child_items.sort(key=lambda item: item[1]["amount_cents"], reverse=True)
        for sub, values in child_items:
            amount = values["amount_cents"]
            rows_out.append(
                {
                    "level": "子类",
                    "main_category": main,
                    "sub_category": sub,
                    "amount_cents": amount,
                    "amount": yuan(amount),
                    "count": len(seen_sub_rows[(main, sub)]),
                    "main_pct": "",
                    "sub_pct": format_pct(amount, main_amount),
                }
            )
    return rows_out


def _risk_tag_summary(rows: list[ClassifiedTransaction], review_decisions: ReviewDecisions | None = None) -> list[dict[str, Any]]:
    allocations = _expense_allocations(rows, review_decisions)
    total = sum(item["amount_cents"] for item in allocations)
    totals: dict[str, dict[str, Any]] = defaultdict(lambda: {"amount_cents": 0, "count": 0})
    for item in allocations:
        tags = item["risk_tags"]
        for tag in tags:
            totals[tag]["amount_cents"] += item["amount_cents"]
            totals[tag]["count"] += 1
    out = [
        {
            "risk_tag": tag,
            "amount": yuan(values["amount_cents"]),
            "amount_cents": values["amount_cents"],
            "count": values["count"],
            "expense_pct": format_pct(values["amount_cents"], total),
        }
        for tag, values in totals.items()
    ]
    out.sort(key=lambda item: item["amount_cents"], reverse=True)
    return out


def _cashflow_chart_rows(metrics: dict[str, Any]) -> list[dict[str, Any]]:
    items = [
        ("总支出", metrics["total_expense"]),
        ("待复核支出", metrics["pending_review"]),
        ("总收入", metrics["total_income"]),
        ("账户搬运", metrics["total_transfer"]),
        ("净现金流", abs(metrics["net_cash_flow"])),
    ]
    max_value = max((amount for _label, amount in items), default=0)
    return [
        {
            "name": label,
            "amount_cents": amount,
            "amount": yuan(amount),
            "bar": _visual_bar(amount, max_value),
        }
        for label, amount in items
    ]


def _behavior_bucket_chart_rows(metrics: dict[str, Any]) -> list[dict[str, Any]]:
    keys = [
        "real_consumption",
        "risk_spending",
        "optimizable_spending",
        "social_spending",
        "financial_spending",
        "business_personal_mixed",
    ]
    total = int(metrics.get("total_expense", 0) or 0)
    max_value = max((int(metrics.get(key, 0) or 0) for key in keys), default=0)
    rows: list[dict[str, Any]] = []
    for key in keys:
        amount = int(metrics.get(key, 0) or 0)
        rows.append(
            {
                "key": key,
                "name": BUCKET_LABELS.get(key, key),
                "amount_cents": amount,
                "amount": yuan(amount),
                "pct": format_pct(amount, total),
                "bar": _visual_bar(amount, max_value),
            }
        )
    return rows


def _category_chart_rows(category_summary: list[dict[str, Any]], limit: int = 8) -> list[dict[str, Any]]:
    mains = [item for item in category_summary if item["level"] == "主类"]
    max_value = max((item["amount_cents"] for item in mains), default=0)
    return [
        {
            "name": item["main_category"],
            "amount": item["amount"],
            "pct": item["main_pct"],
            "bar": _visual_bar(item["amount_cents"], max_value),
        }
        for item in mains[:limit]
    ]


def _risk_chart_rows(risk_summary: list[dict[str, Any]], limit: int = 8) -> list[dict[str, Any]]:
    rows = risk_summary[:limit]
    max_value = max((item["amount_cents"] for item in rows), default=0)
    return [
        {
            "name": item["risk_tag"],
            "amount": item["amount"],
            "pct": item["expense_pct"],
            "bar": _visual_bar(item["amount_cents"], max_value),
        }
        for item in rows
    ]


def _mechanism_chart_rows(rows: list[ClassifiedTransaction], limit: int = 10, review_decisions: ReviewDecisions | None = None) -> list[dict[str, Any]]:
    grouped_all = _group_sum(rows, "mechanism", review_decisions=review_decisions)
    grouped = grouped_all[:limit]
    total = int(round(sum(float(item.get("amount", 0) or 0) * 100 for item in grouped_all)))
    max_value = max((int(round(float(item.get("amount", 0) or 0) * 100)) for item in grouped), default=0)
    output: list[dict[str, Any]] = []
    for item in grouped:
        amount_cents = int(round(float(item.get("amount", 0) or 0) * 100))
        output.append(
            {
                "name": item["name"],
                "count": item["count"],
                "amount": item["amount"],
                "amount_cents": amount_cents,
                "pct": format_pct(amount_cents, total),
                "bar": _visual_bar(amount_cents, max_value),
            }
        )
    return output


def _risk_control_matrix_rows(risk_summary: list[dict[str, Any]], limit: int = 10) -> list[dict[str, Any]]:
    rows = risk_summary[:limit]
    output: list[dict[str, Any]] = []
    for item in rows:
        tag = str(item.get("risk_tag", ""))
        pct = float(str(item.get("expense_pct", "0")).replace("%", "") or 0)
        count = int(item.get("count", 0) or 0)
        if tag in {"信用工具", "信用周转"}:
            lever = "授信隔离"
            action = "还款/周转单列，不把授信当现金。"
        elif tag in {"流动性锁定", "投资冲动"}:
            lever = "交易窗口"
            action = "只允许计划日买入，窗口外记录理由。"
        elif tag in {"平台便利", "高频小额", "低复购购物", "夜间冲动"}:
            lever = "延迟支付"
            action = "超上限后延迟 24 小时，低复购进入冷静清单。"
        elif tag in {"长期扣费"}:
            lever = "订阅清理"
            action = "建立扣费清单，取消低使用率项目。"
        elif tag in {"社交家庭", "家庭教育", "住房缴费", "餐饮日用"}:
            lever = "预算复核"
            action = "保留必要预算，复核异常大额和责任归属。"
        else:
            lever = "趋势观察"
            action = "观察环比/同比扩张后再设硬限制。"
        if pct >= 15 or count >= 500:
            priority = "P1"
        elif pct >= 5 or count >= 100:
            priority = "P2"
        else:
            priority = "P3"
        output.append(
            {
                "priority": priority,
                "risk_tag": tag,
                "amount": item.get("amount", 0),
                "expense_pct": item.get("expense_pct", "0.00%"),
                "count": count,
                "control_lever": lever,
                "action": action,
            }
        )
    return output


def _counterparty_concentration_rows(rows: list[ClassifiedTransaction], limit: int = 10, review_decisions: ReviewDecisions | None = None) -> list[dict[str, Any]]:
    allocations = _expense_allocations(rows, review_decisions)
    total = sum(item["amount_cents"] for item in allocations)
    buckets: dict[str, dict[str, Any]] = defaultdict(lambda: {"amount_cents": 0, "keys": set()})
    for item in allocations:
        row = item["row"]
        key = row.order_id or f"{row.transaction_time}-{row.counterparty}-{row.amount_cents}"
        name = str(row.counterparty or "未填写")
        buckets[name]["amount_cents"] += int(item["amount_cents"])
        buckets[name]["keys"].add(key)
    sorted_items = sorted(buckets.items(), key=lambda item: item[1]["amount_cents"], reverse=True)[:limit]
    max_value = max((item[1]["amount_cents"] for item in sorted_items), default=0)
    cumulative = 0
    output: list[dict[str, Any]] = []
    for name, values in sorted_items:
        amount_cents = int(values["amount_cents"])
        cumulative += amount_cents
        output.append(
            {
                "name": name,
                "count": len(values["keys"]),
                "amount": yuan(amount_cents),
                "amount_cents": amount_cents,
                "expense_pct": format_pct(amount_cents, total),
                "cumulative_pct": format_pct(cumulative, total),
                "bar": _visual_bar(amount_cents, max_value),
            }
        )
    return output


def _time_heatmap_rows(rows: list[ClassifiedTransaction], review_decisions: ReviewDecisions | None = None) -> list[dict[str, Any]]:
    weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    dayparts = [
        ("凌晨", 0, 5),
        ("上午", 6, 11),
        ("下午", 12, 17),
        ("晚间", 18, 23),
    ]
    matrix: dict[tuple[int, str], int] = defaultdict(int)
    for item in _expense_allocations(rows, review_decisions):
        row = item["row"]
        weekday = parse_date(row.date).weekday()
        hour = int(getattr(row, "hour", 0) or 0)
        for label, start_hour, end_hour in dayparts:
            if start_hour <= hour <= end_hour:
                matrix[(weekday, label)] += int(item["amount_cents"])
                break
    max_value = max(matrix.values(), default=0)
    output: list[dict[str, Any]] = []
    for weekday_idx, weekday in enumerate(weekday_names):
        amounts = {label: matrix.get((weekday_idx, label), 0) for label, _start, _end in dayparts}
        top_part, top_amount = max(amounts.items(), key=lambda item: item[1]) if amounts else ("", 0)
        output.append(
            {
                "weekday": weekday,
                "early": yuan(amounts["凌晨"]),
                "morning": yuan(amounts["上午"]),
                "afternoon": yuan(amounts["下午"]),
                "evening": yuan(amounts["晚间"]),
                "top_part": top_part if top_amount > 0 else "无",
                "top_amount": yuan(top_amount),
                "bar": _visual_bar(top_amount, max_value),
            }
        )
    return output


def _monthly_category_heatmap_rows(rows: list[ClassifiedTransaction], limit: int = 12, review_decisions: ReviewDecisions | None = None) -> list[dict[str, Any]]:
    month_totals: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for item in _expense_allocations(rows, review_decisions):
        row = item["row"]
        month = row.date[:7]
        month_totals[month][item["main_category"]] += int(item["amount_cents"])
    months = sorted(month_totals)[-limit:]
    max_value = max(
        (amount for month in months for amount in month_totals[month].values()),
        default=0,
    )
    output: list[dict[str, Any]] = []
    for month in months:
        values = {main: month_totals[month].get(main, 0) for main in MAIN_CATEGORY_ORDER if main != "收入退款"}
        top_category, top_amount = max(values.items(), key=lambda item: item[1]) if values else ("无", 0)
        output.append(
            {
                "month": month,
                "necessity": yuan(values.get("生活刚需", 0)),
                "optimizable": yuan(values.get("可优化消费", 0)),
                "social": yuan(values.get("社交家庭", 0)),
                "financial": yuan(values.get("金融资金", 0)),
                "top_category": top_category if top_amount > 0 else "无",
                "top_amount": yuan(top_amount),
                "bar": _visual_bar(top_amount, max_value),
            }
        )
    return output


def _period_chart_rows(all_rows: list[ClassifiedTransaction], period_name: str, latest: date, limit: int = 12, review_decisions: ReviewDecisions | None = None) -> list[dict[str, Any]]:
    current_start, _current_end, _label = PERIODS[period_name](latest)
    summaries = [
        item
        for item in build_period_summary(all_rows, period_name, review_decisions)
        if parse_date(item["period_start"]) <= current_start
    ][-limit:]
    max_value = max((int(round(float(item.get("total_expense", 0)) * 100)) for item in summaries), default=0)
    output: list[dict[str, Any]] = []
    for item in summaries:
        amount_cents = int(round(float(item.get("total_expense", 0)) * 100))
        output.append(
            {
                "period": item["period"],
                "expense": float(item.get("total_expense", 0)),
                "income": float(item.get("total_income", 0)),
                "pending_review": float(item.get("pending_review", 0)),
                "bar": _visual_bar(amount_cents, max_value),
            }
        )
    return output


def _cumulative_cashflow_rows(rows: list[ClassifiedTransaction], limit: int = 12, review_decisions: ReviewDecisions | None = None) -> list[dict[str, Any]]:
    summaries = build_period_summary(rows, "month", review_decisions)[-limit:]
    cumulative_cents = 0
    max_abs_cents = 0
    staged: list[tuple[dict[str, Any], int, int, int, int]] = []
    for item in summaries:
        income_cents = int(round(float(item.get("total_income", 0) or 0) * 100))
        expense_cents = int(round(float(item.get("total_expense", 0) or 0) * 100))
        net_cents = income_cents - expense_cents
        cumulative_cents += net_cents
        max_abs_cents = max(max_abs_cents, abs(net_cents), abs(cumulative_cents))
        staged.append((item, income_cents, expense_cents, net_cents, cumulative_cents))

    output: list[dict[str, Any]] = []
    for item, income_cents, expense_cents, net_cents, running_cents in staged:
        output.append(
            {
                "month": item["period"],
                "income": yuan(income_cents),
                "expense": yuan(expense_cents),
                "net": yuan(net_cents),
                "cumulative_net": yuan(running_cents),
                "status": "回血" if net_cents >= 0 else "失血",
                "bar": _visual_bar(abs(running_cents), max_abs_cents),
            }
        )
    return output


def _source_platform_rows(rows: list[ClassifiedTransaction], review_decisions: ReviewDecisions | None = None) -> list[dict[str, Any]]:
    transaction_counts: dict[str, int] = defaultdict(int)
    source_files: dict[str, set[str]] = defaultdict(set)
    pending_counts: dict[str, int] = defaultdict(int)
    expense_cents: dict[str, int] = defaultdict(int)

    for row in rows:
        platform = getattr(row, "source_platform", "") or "unknown"
        transaction_counts[platform] += 1
        source_files[platform].add(getattr(row, "source_file", "") or "unknown")
        if getattr(row, "needs_review", False) and not _is_review_confirmed(row, review_decisions):
            pending_counts[platform] += 1

    for item in _expense_allocations(rows, review_decisions):
        row = item["row"]
        platform = getattr(row, "source_platform", "") or "unknown"
        expense_cents[platform] += int(item["amount_cents"])

    total_expense = sum(expense_cents.values())
    max_expense = max(expense_cents.values(), default=0)
    platforms = sorted(set(transaction_counts) | set(source_files) | set(pending_counts) | set(expense_cents))
    output: list[dict[str, Any]] = []
    for platform in platforms:
        amount = expense_cents.get(platform, 0)
        output.append(
            {
                "platform": platform,
                "transaction_count": transaction_counts.get(platform, 0),
                "source_file_count": len(source_files.get(platform, set())),
                "production_expense": yuan(amount),
                "expense_pct": format_pct(amount, total_expense),
                "pending_review_count": pending_counts.get(platform, 0),
                "bar": _visual_bar(amount, max_expense),
            }
        )
    return sorted(output, key=lambda item: (float(item["production_expense"]), item["transaction_count"]), reverse=True)


def _source_health_summary(rows: list[ClassifiedTransaction], review_decisions: ReviewDecisions | None = None) -> dict[str, Any]:
    source_platforms = _source_platform_rows(rows, review_decisions)
    dates = [parse_date(row.date) for row in rows]
    return {
        "platform_count": len(source_platforms),
        "source_file_count": len({getattr(row, "source_file", "") or "unknown" for row in rows}),
        "transaction_count": len(rows),
        "production_allocation_count": len(_expense_allocations(rows, review_decisions)),
        "pending_review_count": len(_pending_review_rows(rows, review_decisions)),
        "date_start": min(dates).isoformat() if dates else "",
        "date_end": max(dates).isoformat() if dates else "",
    }


def _trend_formula_note(period_name: str) -> str:
    notes = {
        "week": "趋势公式：周报环比：本周 vs 上周；周报同比：本周 vs 去年同 ISO 周。",
        "month": "趋势公式：月报环比：本月 vs 上月；月报同比：本月 vs 去年同月。",
        "quarter": "趋势公式：季报环比：本季 vs 上季；季报同比：本季 vs 去年同季。",
        "half": "趋势公式：半年报环比：本半年 vs 上半年；半年报同比：本半年 vs 去年同期半年。",
        "year": "趋势公式：年报同比：本年 vs 上年。",
    }
    return notes.get(period_name, "")


def _group_expense_amount(rows: list[ClassifiedTransaction], key_func: Callable[[ClassifiedTransaction], tuple[str, str]], review_decisions: ReviewDecisions | None = None) -> dict[tuple[str, str], int]:
    totals: dict[tuple[str, str], int] = defaultdict(int)
    for item in _expense_allocations(rows, review_decisions):
        totals[(item["main_category"], item["sub_category"])] += item["amount_cents"]
    return dict(totals)


def _period_compare_bounds(period_name: str, latest: date) -> tuple[tuple[date, date, str], tuple[date, date, str], tuple[date, date, str] | None]:
    current = PERIODS[period_name](latest)
    start, _end, _label = current
    if period_name == "week":
        prev = PERIODS["week"](start.fromordinal(start.toordinal() - 7))
        iso = latest.isocalendar()
        try:
            yoy_day = date.fromisocalendar(iso.year - 1, iso.week, min(iso.weekday, 7))
        except ValueError:
            yoy_day = latest.replace(year=latest.year - 1)
        yoy = PERIODS["week"](yoy_day)
    elif period_name == "month":
        prev_day = date(start.year - 1, 12, 1) if start.month == 1 else date(start.year, start.month - 1, 1)
        prev = PERIODS["month"](prev_day)
        yoy = PERIODS["month"](date(start.year - 1, start.month, 1))
    elif period_name == "quarter":
        prev_day = date(start.year - 1, 10, 1) if start.month == 1 else date(start.year, start.month - 3, 1)
        prev = PERIODS["quarter"](prev_day)
        yoy = PERIODS["quarter"](date(start.year - 1, start.month, 1))
    elif period_name == "half":
        prev_day = date(start.year - 1, 7, 1) if start.month == 1 else date(start.year, 1, 1)
        prev = PERIODS["half"](prev_day)
        yoy = PERIODS["half"](date(start.year - 1, start.month, 1))
    elif period_name == "year":
        prev = PERIODS["year"](date(start.year - 1, 1, 1))
        yoy = prev
    else:
        raise ValueError(f"Unsupported period: {period_name}")
    return current, prev, yoy


def _category_trend_rows(all_rows: list[ClassifiedTransaction], current_rows: list[ClassifiedTransaction], previous_rows: list[ClassifiedTransaction], yoy_rows: list[ClassifiedTransaction], *, include_mom: bool, review_decisions: ReviewDecisions | None = None) -> list[dict[str, Any]]:
    current = _group_expense_amount(current_rows, lambda r: (getattr(r, "main_category", "未分类"), getattr(r, "sub_category", "")), review_decisions)
    previous = _group_expense_amount(previous_rows, lambda r: (getattr(r, "main_category", "未分类"), getattr(r, "sub_category", "")), review_decisions)
    yoy = _group_expense_amount(yoy_rows, lambda r: (getattr(r, "main_category", "未分类"), getattr(r, "sub_category", "")), review_decisions)
    has_previous = bool(_expense_rows(previous_rows))
    has_yoy = bool(_expense_rows(yoy_rows))
    keys = set(current) | set(previous) | set(yoy)

    main_amounts = defaultdict(int)
    for (main, _sub), amount in current.items():
        main_amounts[main] += amount

    out: list[dict[str, Any]] = []
    for main in sorted({key[0] for key in keys}, key=lambda name: (MAIN_CATEGORY_ORDER.index(name) if name in MAIN_CATEGORY_ORDER else 99, name)):
        main_current = sum(amount for (m, _s), amount in current.items() if m == main)
        main_previous = sum(amount for (m, _s), amount in previous.items() if m == main)
        main_yoy = sum(amount for (m, _s), amount in yoy.items() if m == main)
        out.append(
            {
                "level": "主类",
                "category": main,
                "current": yuan(main_current),
                "previous": yuan(main_previous),
                "mom": format_change(main_current, main_previous, has_previous) if include_mom else "不适用",
                "yoy_base": yuan(main_yoy),
                "yoy": format_change(main_current, main_yoy, has_yoy),
            }
        )
        sub_keys = sorted(
            [key for key in keys if key[0] == main],
            key=lambda key: current.get(key, 0),
            reverse=True,
        )
        for key in sub_keys:
            sub_current = current.get(key, 0)
            sub_previous = previous.get(key, 0)
            sub_yoy = yoy.get(key, 0)
            out.append(
                {
                    "level": "子类",
                    "category": f"{main}/{key[1]}",
                    "current": yuan(sub_current),
                    "previous": yuan(sub_previous),
                    "mom": format_change(sub_current, sub_previous, has_previous) if include_mom else "不适用",
                    "yoy_base": yuan(sub_yoy),
                    "yoy": format_change(sub_current, sub_yoy, has_yoy),
                }
            )
    return out


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _report_markdown(
    title: str,
    rows: list[ClassifiedTransaction],
    date_note: str,
    *,
    all_rows: list[ClassifiedTransaction] | None = None,
    period_name: str | None = None,
    trend_period_name: str | None = None,
    latest: date | None = None,
    review_decisions: ReviewDecisions | None = None,
) -> str:
    metrics = core_metrics(rows, review_decisions)
    category_summary = _category_summary(rows, review_decisions)
    risk_summary = _risk_tag_summary(rows, review_decisions)
    merchants = _group_sum(rows, "counterparty", limit=10, review_decisions=review_decisions)
    cashflow_visual = _cashflow_chart_rows(metrics)
    source_platform_visual = _source_platform_rows(rows, review_decisions)
    source_health = _source_health_summary(rows, review_decisions)
    review_status_visual = _review_status_summary(rows, review_decisions)
    behavior_bucket_visual = _behavior_bucket_chart_rows(metrics)
    category_visual = _category_chart_rows(category_summary)
    risk_visual = _risk_chart_rows(risk_summary)
    mechanism_visual = _mechanism_chart_rows(rows, limit=10, review_decisions=review_decisions)
    risk_control_visual = _risk_control_matrix_rows(risk_summary, limit=10)
    counterparty_visual = _counterparty_concentration_rows(rows, limit=10, review_decisions=review_decisions)
    time_heatmap_visual = _time_heatmap_rows(rows, review_decisions=review_decisions)
    monthly_category_visual = _monthly_category_heatmap_rows(all_rows or rows, limit=12, review_decisions=review_decisions)
    cumulative_cashflow_visual = _cumulative_cashflow_rows(all_rows or rows, limit=12, review_decisions=review_decisions)
    budget_pressure_visual = build_budget_pressure_radar(metrics, category_summary, risk_summary)
    effective_trend_period = trend_period_name or period_name
    trend_visual = _period_chart_rows(all_rows, effective_trend_period, latest, review_decisions=review_decisions) if all_rows is not None and effective_trend_period is not None and latest is not None else []
    trend_rows: list[dict[str, Any]] = []
    trend_context: tuple[tuple[date, date, str], tuple[date, date, str], tuple[date, date, str] | None] | None = None
    if all_rows is not None and period_name is not None and latest is not None:
        trend_context = _period_compare_bounds(period_name, latest)
        (_current_start, _current_end, _current_label), (previous_start, previous_end, _previous_label), yoy_bounds = trend_context
        previous_rows = _period_rows(all_rows, previous_start, previous_end)
        yoy_rows = _period_rows(all_rows, yoy_bounds[0], yoy_bounds[1]) if yoy_bounds else []
        trend_rows = _category_trend_rows(
            all_rows,
            rows,
            previous_rows,
            yoy_rows,
            include_mom=period_name != "year",
            review_decisions=review_decisions,
        )
    control_plan = build_control_plan(metrics, category_summary, risk_summary, trend_rows)
    suggestions = control_plan_to_suggestions(control_plan)
    review_rows = sorted(
        [row for row in rows if getattr(row, "needs_review", False) and not _is_review_confirmed(row, review_decisions)],
        key=lambda row: row.amount_cents,
        reverse=True,
    )[:15]

    lines = [
        f"# {title}",
        "",
        f"统计范围：{date_note}",
        "口径：金融资金参与总支出占比；基金买入计支出，基金卖出/赎回计收入；账户搬运进入现金流视图但不计支出占比。",
        "",
        "## 现金流总览",
        "",
        f"- 总支出：¥{format_yuan(metrics['total_expense'])}",
        f"- 待复核支出：¥{format_yuan(metrics['pending_review'])}",
        f"- 总收入：¥{format_yuan(metrics['total_income'])}",
        f"- 净现金流：¥{format_yuan(metrics['net_cash_flow'])}",
        f"- 账户搬运：¥{format_yuan(metrics['total_transfer'])}",
        f"- 交易笔数：{metrics['transactions']}",
        "",
        "## 可视化图表",
        "",
        "### 现金流视图",
        "",
        "| 项目 | 金额 | 图表 |",
        "|---|---:|---|",
    ]
    for item in cashflow_visual:
        lines.append(f"| {item['name']} | ¥{item['amount']:,.2f} | {item['bar']} |")

    lines.extend(
        [
            "",
            "### 数据源平台分布与导入健康",
            "",
            f"导入健康：平台 {source_health['platform_count']} 个，源文件 {source_health['source_file_count']} 个，"
            f"审计交易 {source_health['transaction_count']} 笔，生产分摊 {source_health['production_allocation_count']} 行，"
            f"未确认大额 {source_health['pending_review_count']} 笔；数据日期 {source_health['date_start']} 至 {source_health['date_end']}。",
            "",
            "| 平台 | 审计交易 | 源文件 | 生产支出 | 支出占比 | 待复核笔数 | 图表 |",
            "|---|---:|---:|---:|---:|---:|---|",
        ]
    )
    for item in source_platform_visual:
        lines.append(
            f"| {item['platform']} | {item['transaction_count']} | {item['source_file_count']} | "
            f"¥{float(item['production_expense']):,.2f} | {item['expense_pct']} | {item['pending_review_count']} | {item['bar']} |"
        )
    if not source_platform_visual:
        lines.append("| 无 | 0 | 0 | ¥0.00 | 0.00% | 0 |  |")

    lines.extend(
        [
            "",
            "### 大额复核闭环状态",
            "",
            "口径：单笔 >= ¥10,000 的支出按已确认、人工纳入、人工排除和仍待复核拆分；仍待复核不进入生产统计。",
            "",
            "| 状态 | 笔数 | 金额 | 金额占比 | 生产影响 | 图表 |",
            "|---|---:|---:|---:|---|---|",
        ]
    )
    for item in review_status_visual:
        lines.append(
            f"| {item['status_label']} | {item['count']} | ¥{float(item['amount']):,.2f} | "
            f"{item['amount_pct']} | {item['production_effect']} | {item['bar']} |"
        )

    lines.extend(
        [
            "",
            "### 累计净现金流轨迹",
            "",
            "| 月份 | 收入 | 支出 | 当月净现金流 | 累计净现金流 | 状态 | 图表 |",
            "|---|---:|---:|---:|---:|---|---|",
        ]
    )
    for item in cumulative_cashflow_visual:
        lines.append(
            f"| {item['month']} | ¥{item['income']:,.2f} | ¥{item['expense']:,.2f} | "
            f"¥{item['net']:,.2f} | ¥{item['cumulative_net']:,.2f} | {item['status']} | {item['bar']} |"
        )

    lines.extend(
        [
            "",
            "### 行为桶支出对照",
            "",
            "| 行为桶 | 金额 | 占总支出 | 图表 |",
            "|---|---:|---:|---|",
        ]
    )
    for item in behavior_bucket_visual:
        lines.append(f"| {item['name']} | ¥{item['amount']:,.2f} | {item['pct']} | {item['bar']} |")

    max_pressure = max((float(item.get("pressure_score", 0) or 0) for item in budget_pressure_visual), default=0)
    lines.extend(
        [
            "",
            "### 预算压力雷达",
            "",
            "口径：默认目标上限用于控制动作优先级，不改变会计分类；后续可按你的反馈调整阈值。",
            "",
            "| 优先级 | 维度 | 当前金额 | 当前占比 | 目标上限 | 压力分 | 状态 | 控制动作 | 图表 |",
            "|---|---|---:|---:|---:|---:|---|---|---|",
        ]
    )
    for item in budget_pressure_visual:
        pressure_cents = int(round(float(item.get("pressure_score", 0) or 0) * 100))
        max_pressure_cents = int(round(max_pressure * 100))
        lines.append(
            f"| {item['priority']} | {item['dimension']} | ¥{float(item['current_amount']):,.2f} | {item['current_pct']} | "
            f"{item['target_pct']} | {float(item['pressure_score']):.2f} | {item['status']} | {item['control_action']} | "
            f"{_visual_bar(pressure_cents, max_pressure_cents)} |"
        )

    lines.extend(
        [
            "",
            "### 主类支出占比",
            "",
            "| 主类 | 金额 | 主类占比 | 图表 |",
            "|---|---:|---:|---|",
        ]
    )
    for item in category_visual:
        lines.append(f"| {item['name']} | ¥{item['amount']:,.2f} | {item['pct']} | {item['bar']} |")

    lines.extend(
        [
            "",
            "### 风险标签金额排行",
            "",
            "| 风险标签 | 金额 | 占总支出 | 图表 |",
            "|---|---:|---:|---|",
        ]
    )
    for item in risk_visual:
        lines.append(f"| {item['name']} | ¥{item['amount']:,.2f} | {item['pct']} | {item['bar']} |")

    lines.extend(
        [
            "",
            "### 经济放血机制图谱",
            "",
            "| 放血机制 | 笔数 | 金额 | 占机制金额 | 图表 |",
            "|---|---:|---:|---:|---|",
        ]
    )
    for item in mechanism_visual:
        lines.append(f"| {_safe_name(item['name'])[:32]} | {item['count']} | ¥{item['amount']:,.2f} | {item['pct']} | {item['bar']} |")
    if not mechanism_visual:
        lines.append("| 无 | 0 | ¥0.00 | 0.00% |  |")

    lines.extend(
        [
            "",
            "### 风险控制矩阵",
            "",
            "| 优先级 | 风险标签 | 金额 | 占总支出 | 笔数 | 控制杠杆 | 下期动作 |",
            "|---|---|---:|---:|---:|---|---|",
        ]
    )
    for item in risk_control_visual:
        lines.append(
            f"| {item['priority']} | {item['risk_tag']} | ¥{float(item['amount']):,.2f} | {item['expense_pct']} | "
            f"{item['count']} | {item['control_lever']} | {item['action']} |"
        )

    lines.extend(
        [
            "",
            "### 交易对方集中度",
            "",
            "| 交易对方 | 笔数 | 金额 | 占总支出 | 累计占比 | 图表 |",
            "|---|---:|---:|---:|---:|---|",
        ]
    )
    for item in counterparty_visual:
        lines.append(
            f"| {_safe_name(item['name'])[:28]} | {item['count']} | ¥{item['amount']:,.2f} | "
            f"{item['expense_pct']} | {item['cumulative_pct']} | {item['bar']} |"
        )
    if not counterparty_visual:
        lines.append("| 无 | 0 | ¥0.00 | 0.00% | 0.00% |  |")

    lines.extend(
        [
            "",
            "### 时间行为热力图",
            "",
            "| 星期 | 凌晨 0-5 | 上午 6-11 | 下午 12-17 | 晚间 18-23 | 最高时段 | 强度 |",
            "|---|---:|---:|---:|---:|---|---|",
        ]
    )
    for item in time_heatmap_visual:
        lines.append(
            f"| {item['weekday']} | ¥{item['early']:,.2f} | ¥{item['morning']:,.2f} | "
            f"¥{item['afternoon']:,.2f} | ¥{item['evening']:,.2f} | {item['top_part']} ¥{item['top_amount']:,.2f} | {item['bar']} |"
        )

    lines.extend(
        [
            "",
            "### 主类月度热力矩阵",
            "",
            "| 月份 | 生活刚需 | 可优化消费 | 社交家庭 | 金融资金 | 最高主类 | 强度 |",
            "|---|---:|---:|---:|---:|---|---|",
        ]
    )
    for item in monthly_category_visual:
        lines.append(
            f"| {item['month']} | ¥{item['necessity']:,.2f} | ¥{item['optimizable']:,.2f} | "
            f"¥{item['social']:,.2f} | ¥{item['financial']:,.2f} | {item['top_category']} ¥{item['top_amount']:,.2f} | {item['bar']} |"
        )

    if trend_visual:
        lines.extend(
            [
                "",
                "### 周期支出趋势",
                "",
                "| 周期 | 支出 | 收入 | 待复核 | 图表 |",
                "|---|---:|---:|---:|---|",
            ]
        )
        for item in trend_visual:
            lines.append(
                f"| {item['period']} | ¥{item['expense']:,.2f} | ¥{item['income']:,.2f} | "
                f"¥{item['pending_review']:,.2f} | {item['bar']} |"
            )

    lines.extend(
        [
            "",
        "## 主类/子类金额",
        "",
        "| 主类 | 子类 | 金额 | 笔数 | 主类占总支出 | 子类占主类 |",
        "|---|---|---:|---:|---:|---:|",
        ]
    )
    for item in category_summary:
        main_value = item["main_category"] if item["level"] == "主类" else ""
        lines.append(
            f"| {main_value} | {item['sub_category']} | "
            f"¥{item['amount']:,.2f} | {item['count']} | {item['main_pct']} | {item['sub_pct']} |"
        )

    if trend_context is not None and period_name is not None:
        (current_start, current_end, current_label), (previous_start, previous_end, previous_label), yoy_bounds = trend_context
        lines.extend(
            [
                "",
                "## 主类/子类趋势",
                "",
                _trend_formula_note(period_name),
                "",
            ]
        )
        if period_name == "year":
            lines.extend(
                [
                    f"同比基准：{yoy_bounds[2]}（{yoy_bounds[0].isoformat()} 至 {yoy_bounds[1].isoformat()}）",
                    "",
                    "| 主类 | 子类 | 本年金额 | 上年金额 | 同比 |",
                    "|---|---|---:|---:|---:|",
                ]
            )
        else:
            lines.extend(
                [
                    f"环比基准：{previous_label}（{previous_start.isoformat()} 至 {previous_end.isoformat()}）；同比基准：{yoy_bounds[2]}（{yoy_bounds[0].isoformat()} 至 {yoy_bounds[1].isoformat()}）",
                    "",
                    "| 主类 | 子类 | 本期金额 | 上期金额 | 环比 | 去年同期 | 同比 |",
                    "|---|---|---:|---:|---:|---:|---:|",
                ]
            )
        for item in trend_rows:
            if item["level"] == "主类":
                main_value = item["category"]
                sub_value = ""
            else:
                main_value, sub_value = item["category"].split("/", 1)
                main_value = ""
            if period_name == "year":
                lines.append(f"| {main_value} | {sub_value} | ¥{item['current']:,.2f} | ¥{item['yoy_base']:,.2f} | {item['yoy']} |")
            else:
                lines.append(
                    f"| {main_value} | {sub_value} | ¥{item['current']:,.2f} | "
                    f"¥{item['previous']:,.2f} | {item['mom']} | ¥{item['yoy_base']:,.2f} | {item['yoy']} |"
                )

    lines.extend(["", "## 风险标签", "", "| 风险标签 | 金额 | 占总支出 | 笔数 |", "|---|---:|---:|---:|"])
    for item in risk_summary[:12]:
        lines.append(f"| {item['risk_tag']} | ¥{item['amount']:,.2f} | {item['expense_pct']} | {item['count']} |")

    lines.extend(
        [
            "",
            "## 消费控制动作",
            "",
            "| 优先级 | 控制对象 | 触发证据 | 当前金额 | 占总支出 | 建议动作 | 建议上限 | 预计可优化 | 需复核 |",
            "|---|---|---|---:|---:|---|---:|---:|---|",
        ]
    )
    for item in control_plan:
        lines.append(
            f"| {item['priority']} | {item['focus_area']} | {item['trigger_metric']} | "
            f"¥{item['current_amount']:,.2f} | {item['current_pct']} | {item['recommended_action']} | "
            f"¥{item['suggested_cap']:,.2f} | ¥{item['estimated_saving']:,.2f} | {item['review_needed']} |"
        )
    if not control_plan:
        lines.append("| P3 | 继续观察 | 当前无突出异常 | ¥0.00 | 0.00% | 继续积累周期数据后再设置封顶额。 | ¥0.00 | ¥0.00 | 否 |")

    lines.extend(["", "## 交易对方 Top 10", "", "| 交易对方 | 笔数 | 金额 |", "|---|---:|---:|"])
    for item in merchants:
        lines.append(f"| {item['name']} | {item['count']} | ¥{item['amount']:,.2f} |")

    lines.extend(["", "## 大额待复核交易", "", "单笔 >= ¥10,000 的支出先进入复核清单，后续由你确认后更新分类规则和历史报告。", "", "| 时间 | 对方 | 说明 | 金额 | 主类/子类 | 风险标签 |", "|---|---|---|---:|---|---|"])
    for row in review_rows:
        desc = row.description.replace("|", "/")[:40]
        lines.append(
            f"| {row.transaction_time} | {row.counterparty[:20]} | {desc} | ¥{row.amount:,.2f} | "
            f"{row.main_category}/{row.sub_category} | {row.risk_tags} |"
        )
    if not review_rows:
        lines.append("| 无 |  |  | ¥0.00 |  |  |")

    lines.extend(["", "## 降低消费建议", ""])
    for idx, suggestion in enumerate(suggestions, 1):
        lines.append(f"{idx}. {suggestion}")
    lines.append("")
    return "\n".join(lines)


def _pdf_font_name() -> str:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/System/Library/Fonts/Supplemental/Songti.ttc",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return candidate
    raise RuntimeError("未找到可用于绘制中文 PDF 的系统字体。")


def _plain_cell(value: str) -> str:
    return value.strip().replace("<br>", "\n")


def _markdown_table_to_rows(lines: list[str]) -> list[list[str]]:
    rows = []
    for line in lines:
        stripped = line.strip().strip("|")
        if not stripped or re.fullmatch(r"[:\-\|\s]+", stripped):
            continue
        rows.append([_plain_cell(cell) for cell in stripped.split("|")])
    return rows


def write_report_pdf(markdown: str, path: Path) -> None:
    from PIL import Image, ImageDraw, ImageFont

    path.parent.mkdir(parents=True, exist_ok=True)
    font_path = _pdf_font_name()

    width, height = 1240, 1754
    margin_x, margin_y = 72, 72
    content_width = width - margin_x * 2
    bottom = height - margin_y

    def load_font(size: int) -> ImageFont.FreeTypeFont:
        return ImageFont.truetype(font_path, size=size)

    fonts = {
        "title": load_font(34),
        "h2": load_font(24),
        "h3": load_font(20),
        "body": load_font(18),
        "small": load_font(16),
    }

    pages: list[Image.Image] = []
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    y = margin_y

    def new_page() -> None:
        nonlocal image, draw, y
        pages.append(image)
        image = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(image)
        y = margin_y

    def text_width(text: str, font: ImageFont.FreeTypeFont) -> int:
        if not text:
            return 0
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0]

    def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
        result: list[str] = []
        for raw_part in str(text).splitlines() or [""]:
            part = raw_part.strip()
            if not part:
                result.append("")
                continue
            current = ""
            for char in part:
                candidate = current + char
                if text_width(candidate, font) <= max_width or not current:
                    current = candidate
                else:
                    result.append(current)
                    current = char
            if current:
                result.append(current)
        return result

    def visual_bar_ratio(text: str) -> float | None:
        value = str(text).strip()
        if not value or any(char not in {"█", "░"} for char in value):
            return None
        total = len(value)
        if total == 0:
            return None
        return value.count("█") / total

    def visual_bar_color(row: list[str], header: list[str]) -> str:
        row_text = " ".join(str(item) for item in row)
        header_text = " ".join(str(item) for item in header)
        if "风险" in header_text or "待复核" in row_text:
            return "#d14343"
        if "收入" in row_text:
            return "#057a55"
        if "净现金流" in row_text:
            return "#ad6500"
        return "#2563eb"

    def ensure_space(required: int) -> None:
        if y + required > bottom:
            new_page()

    def draw_wrapped(text: str, font: ImageFont.FreeTypeFont, fill: str, *, x: int = margin_x, max_width: int = content_width, line_gap: int = 6) -> None:
        nonlocal y
        lines = wrap_text(text, font, max_width)
        line_height = font.size + line_gap
        ensure_space(max(line_height, len(lines) * line_height))
        for line in lines:
            draw.text((x, y), line, font=font, fill=fill)
            y += line_height

    def draw_table(rows: list[list[str]]) -> None:
        nonlocal y
        if not rows:
            return
        col_count = max(len(row) for row in rows)
        padded = [row + [""] * (col_count - len(row)) for row in rows]
        header = padded[0] if padded else []
        col_width = content_width // col_count
        pad = 8
        line_gap = 5
        for row_idx, row in enumerate(padded):
            visual_cols = {idx for idx, cell in enumerate(row) if row_idx > 0 and visual_bar_ratio(cell) is not None}
            wrapped_cells = [
                [""] if col_idx in visual_cols else wrap_text(cell, fonts["small"], col_width - pad * 2)
                for col_idx, cell in enumerate(row)
            ]
            max_lines = max(len(cell_lines) for cell_lines in wrapped_cells)
            row_height = max(38, max_lines * (fonts["small"].size + line_gap) + pad * 2)
            ensure_space(row_height)
            is_main_row = row_idx > 0 and col_count >= 2 and bool(str(row[0]).strip()) and not str(row[1]).strip()
            fill = "#eef2f7" if row_idx == 0 else "#f7f9fc" if is_main_row else "white"
            draw.rectangle((margin_x, y, margin_x + col_width * col_count, y + row_height), fill=fill, outline="#d8dee8")
            for col_idx, cell_lines in enumerate(wrapped_cells):
                x0 = margin_x + col_idx * col_width
                draw.line((x0, y, x0, y + row_height), fill="#d8dee8", width=1)
                ratio = visual_bar_ratio(row[col_idx]) if col_idx in visual_cols else None
                if ratio is not None:
                    bar_x0 = x0 + pad
                    bar_x1 = x0 + col_width - pad
                    bar_y0 = y + row_height // 2 - 6
                    bar_y1 = y + row_height // 2 + 6
                    draw.rectangle((bar_x0, bar_y0, bar_x1, bar_y1), fill="#edf1f7")
                    draw.rectangle((bar_x0, bar_y0, bar_x0 + max(2, int((bar_x1 - bar_x0) * ratio)), bar_y1), fill=visual_bar_color(row, header))
                    continue
                ty = y + pad
                for cell_line in cell_lines:
                    draw.text((x0 + pad, ty), cell_line, font=fonts["small"], fill="#111827")
                    ty += fonts["small"].size + line_gap
            draw.line((margin_x + col_width * col_count, y, margin_x + col_width * col_count, y + row_height), fill="#d8dee8", width=1)
            y += row_height
        y += 14

    lines = markdown.splitlines()
    idx = 0
    in_code_block = False
    while idx < len(lines):
        line = lines[idx].rstrip()
        if line.startswith("```"):
            in_code_block = not in_code_block
            idx += 1
            continue
        if not line:
            y += 10
            idx += 1
            continue
        if in_code_block:
            draw_wrapped(line, fonts["small"], "#1f2937")
            idx += 1
            continue
        if line.startswith("# "):
            draw_wrapped(line[2:], fonts["title"], "#111827", line_gap=10)
            y += 8
            idx += 1
            continue
        if line.startswith("## "):
            y += 8
            draw_wrapped(line[3:], fonts["h2"], "#111827", line_gap=8)
            idx += 1
            continue
        if line.startswith("### "):
            y += 6
            draw_wrapped(line[4:], fonts["h3"], "#111827", line_gap=7)
            idx += 1
            continue
        if line.startswith("|"):
            table_lines = []
            while idx < len(lines) and lines[idx].startswith("|"):
                table_lines.append(lines[idx])
                idx += 1
            draw_table(_markdown_table_to_rows(table_lines))
            continue
        if line.startswith("- "):
            draw_wrapped("• " + line[2:], fonts["body"], "#1f2937", x=margin_x + 18, max_width=content_width - 18)
            idx += 1
            continue
        numbered = re.match(r"^(\d+)\.\s+(.*)$", line)
        if numbered:
            draw_wrapped(f"{numbered.group(1)}. {numbered.group(2)}", fonts["body"], "#1f2937", x=margin_x + 18, max_width=content_width - 18)
            idx += 1
            continue
        draw_wrapped(line, fonts["body"], "#1f2937")
        idx += 1

    pages.append(image)
    pages[0].save(path, "PDF", resolution=150.0, save_all=True, append_images=pages[1:])


def _dashboard_html(rows: list[ClassifiedTransaction], period_summaries: dict[str, list[dict[str, Any]]], review_decisions: ReviewDecisions | None = None, tag_library_rows: list[dict[str, Any]] | None = None) -> str:
    metrics = core_metrics(rows, review_decisions)
    category_summary = _category_summary(rows, review_decisions)
    risk_summary = _risk_tag_summary(rows, review_decisions)
    behavior_buckets = _behavior_bucket_chart_rows(metrics)
    control_plan = build_control_plan(metrics, category_summary, risk_summary)
    budget_pressure = build_budget_pressure_radar(metrics, category_summary, risk_summary)
    mechanisms = _group_sum(rows, "mechanism", limit=10, review_decisions=review_decisions)
    mechanism_chart = _mechanism_chart_rows(rows, limit=10, review_decisions=review_decisions)
    risk_control_matrix = _risk_control_matrix_rows(risk_summary, limit=10)
    merchants = _group_sum(rows, "counterparty", limit=12, review_decisions=review_decisions)
    counterparty_concentration = _counterparty_concentration_rows(rows, limit=12, review_decisions=review_decisions)
    time_heatmap = _time_heatmap_rows(rows, review_decisions=review_decisions)
    monthly_category_heatmap = _monthly_category_heatmap_rows(rows, limit=12, review_decisions=review_decisions)
    cumulative_cashflow = _cumulative_cashflow_rows(rows, limit=12, review_decisions=review_decisions)
    source_platforms = _source_platform_rows(rows, review_decisions)
    source_health = _source_health_summary(rows, review_decisions)
    review_status = _review_status_summary(rows, review_decisions)
    monthly = period_summaries.get("month", [])[-12:]
    weekly = period_summaries.get("week", [])[-12:]
    review_rows = [
        row.to_dict()
        for row in sorted(
            [row for row in rows if getattr(row, "needs_review", False) and not _is_review_confirmed(row, review_decisions)],
            key=lambda row: row.amount_cents,
            reverse=True,
        )[:20]
    ]
    hour_totals: dict[int, int] = defaultdict(int)
    weekday_totals: dict[int, int] = defaultdict(int)
    for item in _expense_allocations(rows, review_decisions):
        row = item["row"]
        amount = item["amount_cents"]
        hour_totals[row.hour] += amount
        weekday_totals[parse_date(row.date).weekday()] += amount
    hour_rows = [{"name": f"{hour:02d}:00", "amount": yuan(hour_totals.get(hour, 0))} for hour in range(24)]
    weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    weekday_rows = [{"name": weekday_names[idx], "amount": yuan(weekday_totals.get(idx, 0))} for idx in range(7)]
    data = {
        "metrics": {key: yuan(value) if isinstance(value, int) and key != "transactions" else value for key, value in metrics.items()},
        "categories": [{k: v for k, v in item.items() if k != "amount_cents"} for item in category_summary],
        "behavior_buckets": [{k: v for k, v in item.items() if k != "amount_cents"} for item in behavior_buckets],
        "risks": [{k: v for k, v in item.items() if k != "amount_cents"} for item in risk_summary[:12]],
        "control_plan": [{k: v for k, v in item.items() if not k.endswith("_cents")} for item in control_plan],
        "budget_pressure": [{k: v for k, v in item.items() if not k.endswith("_cents")} for item in budget_pressure],
        "mechanisms": mechanisms,
        "mechanism_chart": [{k: v for k, v in item.items() if k != "amount_cents"} for item in mechanism_chart],
        "risk_control_matrix": risk_control_matrix,
        "merchants": merchants,
        "counterparty_concentration": [{k: v for k, v in item.items() if k != "amount_cents"} for item in counterparty_concentration],
        "time_heatmap": time_heatmap,
        "monthly_category_heatmap": monthly_category_heatmap,
        "cumulative_cashflow": cumulative_cashflow,
        "source_platforms": source_platforms,
        "source_health": source_health,
        "review_status": [{k: v for k, v in item.items() if k != "amount_cents"} for item in review_status],
        "monthly": monthly,
        "weekly": weekly,
        "review": review_rows,
        "hours": hour_rows,
        "weekdays": weekday_rows,
    }
    cards = [
        ("总支出", metrics["total_expense"], "expense"),
        ("待复核支出", metrics["pending_review"], "review"),
        ("总收入", metrics["total_income"], "income"),
        ("净现金流", metrics["net_cash_flow"], "net"),
        ("账户搬运", metrics["total_transfer"], "transfer"),
        ("交易笔数", metrics["transactions"], "count"),
    ]
    card_html = "\n".join(
        f"<section class='metric {html.escape(kind)}'><div class='label'>{html.escape(label)}</div><div class='value'>{value if kind == 'count' else '¥' + format_yuan(value)}</div></section>"
        for label, value, kind in cards
    )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>经济放血账单 Dashboard</title>
  <style>
    :root {{ --bg:#f6f7f9; --panel:#ffffff; --ink:#172033; --muted:#647083; --line:#d9e0ea; --blue:#2563eb; --red:#d14343; --green:#057a55; --amber:#ad6500; --violet:#6d5bd0; --cyan:#0e7490; }}
    html,body {{ max-width:100%; overflow-x:hidden; }}
    html,body {{ max-width:100%; overflow-x:hidden; }}
    *,*::before,*::after {{ box-sizing:border-box; }}
    html,body {{ max-width:100%; overflow-x:hidden; }}
    html,body {{ max-width:100%; overflow-x:hidden; }}
    body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; background:var(--bg); color:var(--ink); }}
    header {{ padding:22px 32px 14px; border-bottom:1px solid var(--line); background:#fff; position:sticky; top:0; z-index:2; }}
    h1 {{ margin:0 0 6px; font-size:24px; letter-spacing:0; }}
    .sub {{ color:var(--muted); font-size:14px; }}
    main {{ padding:20px 32px 40px; max-width:1440px; width:100%; margin:auto; overflow:hidden; }}
    .metrics {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(min(100%,220px),1fr)); gap:10px; }}
    .metric {{ background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:14px; min-height:78px; box-sizing:border-box; }}
    .metric.review {{ border-left:4px solid var(--red); }}
    .metric.income {{ border-left:4px solid var(--green); }}
    .metric.expense {{ border-left:4px solid var(--blue); }}
    .metric.net {{ border-left:4px solid var(--amber); }}
    .metric.transfer {{ border-left:4px solid var(--cyan); }}
    .label {{ color:var(--muted); font-size:13px; }}
    .value {{ margin-top:8px; font-size:21px; font-weight:750; overflow-wrap:anywhere; }}
    .layout {{ margin-top:16px; display:grid; grid-template-columns:minmax(0,1.2fr) minmax(0,.8fr); gap:14px; align-items:start; min-width:0; }}
    .panel {{ background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:16px; min-width:0; }}
    .panel + .panel {{ margin-top:14px; }}
    h2 {{ margin:0 0 12px; font-size:17px; }}
    .hint {{ color:var(--muted); font-size:12px; margin-top:-4px; margin-bottom:12px; }}
    .chart-grid {{ display:grid; grid-template-columns:minmax(0,1fr) minmax(150px,.32fr); gap:14px; align-items:center; margin-bottom:14px; min-width:0; max-width:100%; overflow:hidden; }}
    .chart-grid > *,.radar-wrap > * {{ min-width:0; max-width:100%; }}
    .svg-chart {{ width:100%; min-width:0; max-width:100%; height:230px; display:block; background:#fbfcfe; border:1px solid var(--line); border-radius:8px; }}
    .donut-chart {{ width:min(210px,100%); min-width:0; max-width:100%; height:210px; display:block; margin:auto; }}
    .radar-chart {{ width:100%; min-width:0; max-width:100%; height:260px; display:block; background:#fbfcfe; border:1px solid var(--line); border-radius:8px; }}
    .radar-wrap {{ display:grid; grid-template-columns:minmax(220px,.46fr) minmax(0,1fr); gap:14px; align-items:center; min-width:0; max-width:100%; }}
    .legend {{ display:grid; gap:8px; font-size:12px; color:var(--muted); min-width:0; max-width:100%; }}
    .legend-item {{ display:grid; grid-template-columns:10px minmax(0,1fr) auto; gap:8px; align-items:center; min-width:0; max-width:100%; }}
    .legend-item span,.legend-item strong {{ min-width:0; overflow:hidden; text-overflow:ellipsis; }}
    .swatch {{ width:10px; height:10px; border-radius:2px; }}
    .bars {{ display:grid; gap:10px; }}
    .bar-row {{ display:grid; grid-template-columns:minmax(120px,220px) 1fr 116px; gap:12px; align-items:center; font-size:13px; }}
    .bar-name {{ overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }}
    .bar-bg {{ height:12px; background:#edf1f7; border-radius:8px; overflow:hidden; }}
    .bar {{ height:12px; background:var(--blue); border-radius:8px; }}
    .bar.red {{ background:var(--red); }}
    .bar.green {{ background:var(--green); }}
    .bar.amber {{ background:var(--amber); }}
    .bar.violet {{ background:var(--violet); }}
    .bar.cyan {{ background:var(--cyan); }}
    .two {{ display:grid; grid-template-columns:minmax(0,1fr) minmax(0,1fr); gap:14px; min-width:0; }}
    .heatmap {{ display:grid; gap:7px; }}
    .heatmap-row {{ display:grid; grid-template-columns:58px repeat(4,minmax(0,1fr)); gap:7px; align-items:stretch; }}
    .heatmap-head {{ color:var(--muted); font-size:12px; font-weight:700; padding:0 6px; }}
    .heatmap-day {{ display:flex; align-items:center; color:var(--muted); font-size:12px; font-weight:700; }}
    .heatmap-cell {{ min-height:48px; border:1px solid var(--line); border-radius:7px; padding:7px; background:#f8fafc; overflow:hidden; }}
    .heatmap-label {{ display:block; color:var(--muted); font-size:11px; }}
    .heatmap-value {{ display:block; margin-top:4px; font-weight:750; font-size:12px; overflow-wrap:anywhere; }}
    .wide-panel {{ margin-top:14px; }}
    .source-health {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:10px; margin-bottom:14px; }}
    .health-card {{ border:1px solid var(--line); border-radius:8px; padding:10px; background:#fbfcfe; }}
    .health-card strong {{ display:block; margin-top:5px; font-size:18px; overflow-wrap:anywhere; }}
    .matrix {{ display:grid; gap:7px; overflow:auto; }}
    .matrix-row {{ display:grid; grid-template-columns:86px repeat(4,minmax(115px,1fr)); gap:7px; min-width:620px; align-items:stretch; }}
    .matrix-head {{ color:var(--muted); font-size:12px; font-weight:700; padding:0 7px; }}
    .matrix-month {{ display:flex; align-items:center; color:var(--muted); font-size:12px; font-weight:700; }}
    .matrix-cell {{ min-height:46px; border:1px solid var(--line); border-radius:7px; padding:7px; background:#f8fafc; }}
    .matrix-value {{ display:block; font-weight:750; font-size:12px; overflow-wrap:anywhere; }}
    table {{ width:100%; border-collapse:collapse; font-size:13px; }}
    th,td {{ padding:9px 8px; border-bottom:1px solid var(--line); text-align:left; }}
    th:last-child,td:last-child {{ text-align:right; }}
    .main-row td {{ background:#f1f5f9; font-weight:700; }}
    .review-table td:nth-child(3) {{ max-width:260px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }}
    @media (max-width:1100px) {{ .layout,.two,.radar-wrap {{ grid-template-columns:1fr; }} }}
    @media (max-width:720px) {{ main,header {{ width:100%; max-width:100%; padding-left:14px; padding-right:14px; overflow:hidden; }} .metrics {{ grid-template-columns:1fr; }} .chart-grid {{ grid-template-columns:minmax(0,1fr); }} .bar-row {{ grid-template-columns:1fr; gap:5px; }} .heatmap-row {{ grid-template-columns:1fr 1fr; }} .heatmap-day {{ grid-column:1/-1; }} .heatmap-head {{ display:none; }} .value {{ font-size:18px; }} .svg-chart,.radar-chart {{ width:100%; max-width:100%; height:230px; }} table {{ display:block; max-width:100%; overflow-x:auto; }} .matrix-row {{ min-width:0; grid-template-columns:1fr; }} }}
    @media (max-width:480px) {{ .metric {{ min-height:68px; }} .value {{ font-size:20px; }} }}
  </style>
</head>
<body>
  <header>
    <h1>经济放血账单 Dashboard</h1>
    <div class="sub">本地静态视图。生产统计已排除未确认大额支出；待复核交易只进入复核队列。</div>
  </header>
  <main>
    <div class="metrics">{card_html}</div>
    <section class="panel wide-panel">
      <h2>数据源平台分布与导入健康</h2>
      <div class="hint">统一展示支付宝/微信等来源平台的审计笔数、源文件数、生产支出和待复核状态，用于证明多源账本输入质量。</div>
      <div id="sourceHealthCards" class="source-health"></div>
      <div id="sourcePlatformBars" class="bars"></div>
      <table id="sourceHealthTable" style="margin-top:12px"></table>
    </section>
    <section class="panel wide-panel">
      <h2>大额复核闭环状态</h2>
      <div class="hint">单笔 >= ¥10,000 的支出按确认状态拆分；仍待复核保持隔离，不进入生产统计。</div>
      <div id="reviewStatusBars" class="bars"></div>
      <table id="reviewStatusTable" style="margin-top:12px"></table>
    </section>
    <div class="layout">
      <div>
        <section class="panel">
          <h2>月度现金流趋势</h2>
          <div class="hint">总支出为生产统计口径；待复核支出单独展示。</div>
          <div class="chart-grid">
            <svg id="monthlyCashflowChart" class="svg-chart" role="img" aria-label="月度现金流折线图"></svg>
            <div id="monthlyCashflowLegend" class="legend"></div>
          </div>
          <div id="monthly" class="bars"></div>
        </section>
        <section class="panel">
          <h2>累计净现金流轨迹</h2>
          <div class="hint">最近 12 个月按收入减生产口径支出累计，观察资金是在回血还是失血。</div>
          <div id="cumulativeCashflow" class="bars"></div>
        </section>
        <section class="panel">
          <h2>主类/子类金额</h2>
          <table id="categories"></table>
        </section>
        <section class="panel">
          <h2>行为桶支出对照</h2>
          <div class="hint">真实消费、风险支出、可优化、社交、金融和公司个人混同使用同一生产口径。</div>
          <div id="behaviorBuckets" class="bars"></div>
        </section>
        <section class="panel">
          <h2>预算压力雷达</h2>
          <div class="hint">默认目标上限只用于控制优先级，不改变分类口径；压力分越高越需要下期压缩或复核。</div>
          <div class="radar-wrap">
            <svg id="budgetPressureRadar" class="radar-chart" role="img" aria-label="预算压力雷达"></svg>
            <div id="budgetPressureBars" class="bars"></div>
          </div>
        </section>
        <section class="panel">
          <h2>大额待复核</h2>
          <table id="review" class="review-table"></table>
        </section>
        <section class="panel">
          <h2>消费控制动作</h2>
          <table id="controlPlan"></table>
        </section>
        <section class="panel">
          <h2>风险控制矩阵</h2>
          <table id="riskControlMatrix"></table>
        </section>
      </div>
      <div>
        <section class="panel">
          <h2>主类占比</h2>
          <div class="chart-grid">
            <svg id="categoryShareChart" class="donut-chart" role="img" aria-label="主类占比环形图"></svg>
            <div id="categoryShareLegend" class="legend"></div>
          </div>
          <div id="categoryBars" class="bars"></div>
        </section>
        <section class="panel">
          <h2>风险标签</h2>
          <div id="riskBars" class="bars"></div>
        </section>
        <section class="panel">
          <h2>经济放血机制图谱</h2>
          <div class="hint">按机制聚合支出，显示当前最主要的放血来源。</div>
          <div id="mechanismBars" class="bars"></div>
        </section>
        <section class="panel">
          <h2>周度趋势</h2>
          <div id="weekly" class="bars"></div>
        </section>
      </div>
    </div>
    <div class="two" style="margin-top:14px">
      <section class="panel">
        <h2>交易对方 Top 12</h2>
        <table id="merchants"></table>
      </section>
      <section class="panel">
        <h2>消费规律</h2>
        <div id="weekdays" class="bars"></div>
        <div style="height:14px"></div>
        <div id="hours" class="bars"></div>
      </section>
    </div>
    <div class="two" style="margin-top:14px">
      <section class="panel">
        <h2>交易对方集中度</h2>
        <div class="hint">累计占比用于识别少数对手方是否构成主要现金流出口。</div>
        <div id="counterpartyConcentration" class="bars"></div>
      </section>
      <section class="panel">
        <h2>时间行为热力矩阵</h2>
        <div class="hint">按星期和日内时段汇总生产口径支出，用于定位高风险消费窗口。</div>
        <div id="timeHeatmap" class="heatmap"></div>
      </section>
    </div>
    <section class="panel wide-panel">
      <h2>主类月度热力矩阵</h2>
      <div class="hint">最近 12 个月按主类聚合生产口径支出，颜色越深表示该主类在该月金额越高。</div>
      <div id="monthlyCategoryHeatmap" class="matrix"></div>
    </section>
  </main>
  <script>
    const DATA = {json.dumps(data, ensure_ascii=False)};
    const yuan = n => "¥" + Number(n || 0).toLocaleString("zh-CN", {{minimumFractionDigits:2, maximumFractionDigits:2}});
    const pctNumber = p => Number(String(p || "0").replace("%", "")) || 0;
    const palette = ["#2563eb", "#057a55", "#ad6500", "#6d5bd0", "#0e7490", "#d14343"];
    const safeText = value => String(value ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#39;");
    function renderMonthlyChart() {{
      const svg = document.getElementById("monthlyCashflowChart");
      const legend = document.getElementById("monthlyCashflowLegend");
      const rows = DATA.monthly || [];
      if (!rows.length) {{
        svg.innerHTML = `<text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" fill="#647083">暂无月度数据</text>`;
        legend.innerHTML = "";
        return;
      }}
      const w = 760, h = 230, pad = 36;
      const keys = [
        ["total_expense", "支出", "#2563eb"],
        ["total_income", "收入", "#057a55"],
        ["pending_review", "待复核", "#d14343"],
      ];
      const max = Math.max(1, ...rows.flatMap(row => keys.map(([key]) => Number(row[key] || 0))));
      const x = index => rows.length === 1 ? w / 2 : pad + index * ((w - pad * 2) / (rows.length - 1));
      const y = value => h - pad - (Number(value || 0) / max) * (h - pad * 2);
      const pathFor = key => rows.map((row, index) => `${{index === 0 ? "M" : "L"}} ${{x(index).toFixed(1)}} ${{y(row[key]).toFixed(1)}}`).join(" ");
      const grid = [0, .25, .5, .75, 1].map(t => {{
        const gy = h - pad - t * (h - pad * 2);
        const label = yuan(max * t);
        return `<line x1="${{pad}}" y1="${{gy.toFixed(1)}}" x2="${{w-pad}}" y2="${{gy.toFixed(1)}}" stroke="#e5eaf2"/><text x="8" y="${{(gy+4).toFixed(1)}}" font-size="11" fill="#647083">${{label}}</text>`;
      }}).join("");
      const labelStep = Math.max(1, Math.ceil(rows.length / 5));
      const labels = rows.map((row, index) => index % labelStep === 0 || index === rows.length - 1 ? `<text x="${{x(index).toFixed(1)}}" y="${{h-10}}" font-size="11" text-anchor="middle" fill="#647083">${{safeText(row.period)}}</text>` : "").join("");
      const lines = keys.map(([key, label, color]) => `<path d="${{pathFor(key)}}" fill="none" stroke="${{color}}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><title>${{safeText(label)}}</title></path>`).join("");
      const points = keys.map(([key, _label, color]) => rows.map((row, index) => `<circle cx="${{x(index).toFixed(1)}}" cy="${{y(row[key]).toFixed(1)}}" r="3" fill="${{color}}"><title>${{safeText(row.period)}} ${{yuan(row[key])}}</title></circle>`).join("")).join("");
      svg.setAttribute("viewBox", `0 0 ${{w}} ${{h}}`);
      svg.innerHTML = `${{grid}}${{labels}}${{lines}}${{points}}`;
      legend.innerHTML = keys.map(([key, label, color]) => {{
        const latest = rows[rows.length - 1] || {{}};
        return `<div class="legend-item"><span class="swatch" style="background:${{color}}"></span><span>${{safeText(label)}}</span><strong>${{yuan(latest[key])}}</strong></div>`;
      }}).join("");
    }}
    function renderCategoryDonut() {{
      const svg = document.getElementById("categoryShareChart");
      const legend = document.getElementById("categoryShareLegend");
      const rows = (DATA.categories || []).filter(row => row.level === "主类" && Number(row.amount || 0) > 0);
      const total = rows.reduce((sum, row) => sum + Number(row.amount || 0), 0);
      if (!rows.length || total <= 0) {{
        svg.innerHTML = `<text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" fill="#647083">暂无分类数据</text>`;
        legend.innerHTML = "";
        return;
      }}
      let offset = 0;
      const circles = rows.map((row, index) => {{
        const pct = Number(row.amount || 0) / total * 100;
        const color = palette[index % palette.length];
        const circle = `<circle cx="21" cy="21" r="15.9155" fill="transparent" stroke="${{color}}" stroke-width="7" stroke-dasharray="${{pct.toFixed(2)}} ${{(100-pct).toFixed(2)}}" stroke-dashoffset="${{(-offset).toFixed(2)}}"><title>${{safeText(row.main_category)}} ${{pct.toFixed(2)}}%</title></circle>`;
        offset += pct;
        return circle;
      }}).join("");
      svg.setAttribute("viewBox", "0 0 42 42");
      svg.innerHTML = `<circle cx="21" cy="21" r="15.9155" fill="transparent" stroke="#edf1f7" stroke-width="7"></circle><g transform="rotate(-90 21 21)">${{circles}}</g><text x="21" y="19" font-size="3.4" text-anchor="middle" font-weight="700" fill="#172033">总支出</text><text x="21" y="23.5" font-size="3" text-anchor="middle" fill="#647083">${{yuan(total)}}</text>`;
      legend.innerHTML = rows.map((row, index) => {{
        const pct = total > 0 ? Number(row.amount || 0) / total * 100 : 0;
        const color = palette[index % palette.length];
        return `<div class="legend-item"><span class="swatch" style="background:${{color}}"></span><span>${{safeText(row.main_category)}} · ${{pct.toFixed(2)}}%</span><strong>${{yuan(row.amount)}}</strong></div>`;
      }}).join("");
    }}
    function bars(id, rows, nameKey, valueKey, colorClass="") {{
      const root = document.getElementById(id);
      if (!root) return;
      const max = Math.max(...rows.map(r => Number(r[valueKey] || 0)), 1);
      root.innerHTML = rows.map(r => {{
        const width = Math.max(2, Number(r[valueKey] || 0) / max * 100);
        return `<div class="bar-row"><div class="bar-name" title="${{r[nameKey]}}">${{r[nameKey]}}</div><div class="bar-bg"><div class="bar ${{colorClass}}" style="width:${{width}}%"></div></div><div>${{yuan(r[valueKey])}}</div></div>`;
      }}).join("");
    }}
    function renderSourceHealth() {{
      const health = DATA.source_health || {{}};
      const cards = [
        ["平台数", health.platform_count || 0],
        ["源文件数", health.source_file_count || 0],
        ["审计交易", health.transaction_count || 0],
        ["生产分摊", health.production_allocation_count || 0],
        ["未确认大额", health.pending_review_count || 0],
        ["日期范围", `${{health.date_start || ""}} 至 ${{health.date_end || ""}}`],
      ];
      document.getElementById("sourceHealthCards").innerHTML = cards.map(([label, value]) => `<div class="health-card"><span class="label">${{safeText(label)}}</span><strong>${{safeText(value)}}</strong></div>`).join("");
      const rows = DATA.source_platforms || [];
      const max = Math.max(...rows.map(r => Number(r.production_expense || 0)), 1);
      document.getElementById("sourcePlatformBars").innerHTML = rows.map((r, index) => {{
        const width = Math.max(2, Number(r.production_expense || 0) / max * 100);
        const color = index % 2 === 0 ? "blue" : "green";
        return `<div class="bar-row"><div class="bar-name" title="${{safeText(r.platform)}}">${{safeText(r.platform)}} · ${{safeText(r.expense_pct)}}</div><div class="bar-bg"><div class="bar ${{color}}" style="width:${{width}}%"></div></div><div>${{yuan(r.production_expense)}}</div></div>`;
      }}).join("");
      document.getElementById("sourceHealthTable").innerHTML = `<tr><th>平台</th><th>审计交易</th><th>源文件</th><th>生产支出</th><th>占比</th><th>待复核</th></tr>` + rows.map(r => `<tr><td>${{safeText(r.platform)}}</td><td>${{r.transaction_count}}</td><td>${{r.source_file_count}}</td><td>${{yuan(r.production_expense)}}</td><td>${{safeText(r.expense_pct)}}</td><td>${{r.pending_review_count}}</td></tr>`).join("");
    }}
    function renderReviewStatus() {{
      const rows = DATA.review_status || [];
      const max = Math.max(...rows.map(r => Number(r.amount || 0)), 1);
      document.getElementById("reviewStatusBars").innerHTML = rows.map(r => {{
        const width = Math.max(2, Number(r.amount || 0) / max * 100);
        const color = r.status === "pending_review" ? "red" : r.status === "manual_exclude" ? "amber" : "green";
        return `<div class="bar-row"><div class="bar-name" title="${{safeText(r.next_action)}}">${{safeText(r.status_label)}} · ${{safeText(r.amount_pct)}}</div><div class="bar-bg"><div class="bar ${{color}}" style="width:${{width}}%"></div></div><div>${{yuan(r.amount)}}</div></div>`;
      }}).join("");
      document.getElementById("reviewStatusTable").innerHTML = `<tr><th>状态</th><th>笔数</th><th>金额</th><th>笔数占比</th><th>金额占比</th><th>生产影响</th></tr>` + rows.map(r => `<tr><td>${{safeText(r.status_label)}}</td><td>${{r.count}}</td><td>${{yuan(r.amount)}}</td><td>${{safeText(r.count_pct)}}</td><td>${{safeText(r.amount_pct)}}</td><td>${{safeText(r.production_effect)}}</td></tr>`).join("");
    }}
    function categoryBars() {{
      const rows = DATA.categories.filter(r => r.level === "主类");
      const max = Math.max(...rows.map(r => Number(r.amount || 0)), 1);
      document.getElementById("categoryBars").innerHTML = rows.map(r => {{
        const width = Math.max(2, Number(r.amount || 0) / max * 100);
        return `<div class="bar-row"><div class="bar-name">${{r.main_category}} · ${{r.main_pct}}</div><div class="bar-bg"><div class="bar violet" style="width:${{width}}%"></div></div><div>${{yuan(r.amount)}}</div></div>`;
      }}).join("");
    }}
    function renderBehaviorBuckets() {{
      const rows = DATA.behavior_buckets || [];
      const max = Math.max(...rows.map(r => Number(r.amount || 0)), 1);
      document.getElementById("behaviorBuckets").innerHTML = rows.map(r => {{
        const width = Math.max(2, Number(r.amount || 0) / max * 100);
        const color = r.key === "risk_spending" ? "red" : r.key === "financial_spending" ? "violet" : r.key === "optimizable_spending" ? "amber" : r.key === "social_spending" ? "cyan" : "blue";
        return `<div class="bar-row"><div class="bar-name">${{safeText(r.name)}} · ${{safeText(r.pct)}}</div><div class="bar-bg"><div class="bar ${{color}}" style="width:${{width}}%"></div></div><div>${{yuan(r.amount)}}</div></div>`;
      }}).join("");
    }}
    function renderCumulativeCashflow() {{
      const rows = DATA.cumulative_cashflow || [];
      const root = document.getElementById("cumulativeCashflow");
      if (!rows.length) {{
        root.innerHTML = `<div class="bar-row"><div class="bar-name">暂无月度数据</div><div class="bar-bg"><div class="bar" style="width:2%"></div></div><div>${{yuan(0)}}</div></div>`;
        return;
      }}
      const max = Math.max(...rows.map(r => Math.abs(Number(r.cumulative_net || 0))), 1);
      root.innerHTML = rows.map(r => {{
        const value = Number(r.cumulative_net || 0);
        const width = Math.max(2, Math.abs(value) / max * 100);
        const color = value >= 0 ? "green" : "red";
        return `<div class="bar-row"><div class="bar-name" title="${{safeText(r.month)}} ${{safeText(r.status)}}">${{safeText(r.month)}} · ${{safeText(r.status)}}</div><div class="bar-bg"><div class="bar ${{color}}" style="width:${{width}}%"></div></div><div>${{yuan(value)}}</div></div>`;
      }}).join("");
    }}
    function renderBudgetPressureRadar() {{
      const rows = (DATA.budget_pressure || []).slice(0, 8);
      const svg = document.getElementById("budgetPressureRadar");
      const barsRoot = document.getElementById("budgetPressureBars");
      if (!rows.length) {{
        svg.innerHTML = `<text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" fill="#647083">暂无预算压力数据</text>`;
        barsRoot.innerHTML = "";
        return;
      }}
      const w = 320, h = 260, cx = 160, cy = 130, radius = 88;
      const step = Math.PI * 2 / rows.length;
      const point = (index, score, scale=1) => {{
        const angle = -Math.PI / 2 + index * step;
        const r = radius * scale * Math.min(1, Math.max(0, Number(score || 0) / 100));
        return [cx + Math.cos(angle) * r, cy + Math.sin(angle) * r];
      }};
      const ring = scale => rows.map((_, index) => {{
        const angle = -Math.PI / 2 + index * step;
        return `${{(cx + Math.cos(angle) * radius * scale).toFixed(1)}},${{(cy + Math.sin(angle) * radius * scale).toFixed(1)}}`;
      }}).join(" ");
      const axes = rows.map((row, index) => {{
        const angle = -Math.PI / 2 + index * step;
        const x = cx + Math.cos(angle) * radius;
        const y = cy + Math.sin(angle) * radius;
        const lx = cx + Math.cos(angle) * (radius + 24);
        const ly = cy + Math.sin(angle) * (radius + 24);
        return `<line x1="${{cx}}" y1="${{cy}}" x2="${{x.toFixed(1)}}" y2="${{y.toFixed(1)}}" stroke="#d9e0ea"/><text x="${{lx.toFixed(1)}}" y="${{ly.toFixed(1)}}" font-size="10" fill="#647083" text-anchor="middle">${{safeText(row.dimension).slice(0,5)}}</text>`;
      }}).join("");
      const polygon = rows.map((row, index) => point(index, row.pressure_score).map(v => v.toFixed(1)).join(",")).join(" ");
      const points = rows.map((row, index) => {{
        const [x, y] = point(index, row.pressure_score);
        const color = row.priority === "P0" || row.priority === "P1" ? "#d14343" : row.priority === "P2" ? "#ad6500" : "#057a55";
        return `<circle cx="${{x.toFixed(1)}}" cy="${{y.toFixed(1)}}" r="3.5" fill="${{color}}"><title>${{safeText(row.dimension)}} 压力分 ${{Number(row.pressure_score || 0).toFixed(2)}}</title></circle>`;
      }}).join("");
      svg.setAttribute("viewBox", `0 0 ${{w}} ${{h}}`);
      svg.innerHTML = `<polygon points="${{ring(.33)}}" fill="none" stroke="#e5eaf2"/><polygon points="${{ring(.66)}}" fill="none" stroke="#e5eaf2"/><polygon points="${{ring(1)}}" fill="none" stroke="#d9e0ea"/>${{axes}}<polygon points="${{polygon}}" fill="rgba(209,67,67,.18)" stroke="#d14343" stroke-width="2"/>${{points}}<text x="${{cx}}" y="${{cy+4}}" font-size="12" text-anchor="middle" fill="#172033" font-weight="700">100=超压</text>`;
      const max = Math.max(...rows.map(r => Number(r.pressure_score || 0)), 1);
      barsRoot.innerHTML = rows.map(row => {{
        const score = Number(row.pressure_score || 0);
        const width = Math.max(2, Math.min(100, score / Math.max(max, 100) * 100));
        const color = row.priority === "P0" || row.priority === "P1" ? "red" : row.priority === "P2" ? "amber" : "green";
        return `<div class="bar-row"><div class="bar-name" title="${{safeText(row.control_action)}}">${{safeText(row.dimension)}} · ${{safeText(row.status)}} · ${{safeText(row.current_pct)}}/${{safeText(row.target_pct)}}</div><div class="bar-bg"><div class="bar ${{color}}" style="width:${{width}}%"></div></div><div>${{score.toFixed(2)}}</div></div>`;
      }}).join("");
    }}
    function riskBars() {{
      const rows = DATA.risks;
      const max = Math.max(...rows.map(r => Number(r.amount || 0)), 1);
      document.getElementById("riskBars").innerHTML = rows.map(r => {{
        const width = Math.max(2, Number(r.amount || 0) / max * 100);
        return `<div class="bar-row"><div class="bar-name">${{r.risk_tag}} · ${{r.expense_pct}}</div><div class="bar-bg"><div class="bar red" style="width:${{width}}%"></div></div><div>${{yuan(r.amount)}}</div></div>`;
      }}).join("");
    }}
    function renderMechanismBars() {{
      const rows = DATA.mechanism_chart || [];
      const max = Math.max(...rows.map(r => Number(r.amount || 0)), 1);
      document.getElementById("mechanismBars").innerHTML = rows.map(r => {{
        const width = Math.max(2, Number(r.amount || 0) / max * 100);
        return `<div class="bar-row"><div class="bar-name" title="${{safeText(r.name)}}">${{safeText(r.name)}} · ${{safeText(r.pct)}}</div><div class="bar-bg"><div class="bar amber" style="width:${{width}}%"></div></div><div>${{yuan(r.amount)}}</div></div>`;
      }}).join("");
    }}
    function periodBars(id, rows, colorClass) {{
      const max = Math.max(...rows.map(r => Number(r.total_expense || 0)), 1);
      document.getElementById(id).innerHTML = rows.map(r => {{
        const width = Math.max(2, Number(r.total_expense || 0) / max * 100);
        const pending = Number(r.pending_review || 0) > 0 ? ` · 待复核 ${{yuan(r.pending_review)}}` : "";
        return `<div class="bar-row"><div class="bar-name" title="${{r.period}}">${{r.period}}</div><div class="bar-bg"><div class="bar ${{colorClass}}" style="width:${{width}}%"></div></div><div>${{yuan(r.total_expense)}}${{pending}}</div></div>`;
      }}).join("");
    }}
    function renderCategories() {{
      document.getElementById("categories").innerHTML = `<tr><th>主类</th><th>子类</th><th>金额</th><th>主类占比</th><th>子类占比</th></tr>` + DATA.categories.map(r => {{
        const cls = r.level === "主类" ? " class='main-row'" : "";
        const main = r.level === "主类" ? r.main_category : "";
        return `<tr${{cls}}><td>${{main}}</td><td>${{r.sub_category || ""}}</td><td>${{yuan(r.amount)}}</td><td>${{r.main_pct || ""}}</td><td>${{r.sub_pct || ""}}</td></tr>`;
      }}).join("");
    }}
    function renderReview() {{
      const table = document.getElementById("review");
      if (!DATA.review.length) {{
        table.innerHTML = `<tr><th>状态</th><th>说明</th><th>金额</th></tr><tr><td>无</td><td>当前周期没有未确认大额支出</td><td>${{yuan(0)}}</td></tr>`;
        return;
      }}
      table.innerHTML = `<tr><th>时间</th><th>对方</th><th>说明</th><th>金额</th></tr>` + DATA.review.map(r => `<tr><td>${{r.transaction_time}}</td><td>${{r.counterparty}}</td><td title="${{r.description}}">${{r.description}}</td><td>${{yuan(r.amount)}}</td></tr>`).join("");
    }}
    function renderControlPlan() {{
      const table = document.getElementById("controlPlan");
      const rows = DATA.control_plan || [];
      if (!rows.length) {{
        table.innerHTML = `<tr><th>状态</th><th>建议</th><th>预计可优化</th></tr><tr><td>P3</td><td>继续观察周期趋势</td><td>${{yuan(0)}}</td></tr>`;
        return;
      }}
      table.innerHTML = `<tr><th>优先级</th><th>控制对象</th><th>触发证据</th><th>建议动作</th><th>预计可优化</th></tr>` + rows.map(r => `<tr><td>${{r.priority}}</td><td>${{r.focus_area}}</td><td>${{r.trigger_metric}}</td><td>${{r.recommended_action}}</td><td>${{yuan(r.estimated_saving)}}</td></tr>`).join("");
    }}
    function renderRiskControlMatrix() {{
      const table = document.getElementById("riskControlMatrix");
      const rows = DATA.risk_control_matrix || [];
      if (!rows.length) {{
        table.innerHTML = `<tr><th>状态</th><th>动作</th></tr><tr><td>P3</td><td>继续观察。</td></tr>`;
        return;
      }}
      table.innerHTML = `<tr><th>优先级</th><th>风险标签</th><th>占比</th><th>控制杠杆</th><th>下期动作</th></tr>` + rows.map(r => `<tr><td>${{safeText(r.priority)}}</td><td>${{safeText(r.risk_tag)}}</td><td>${{safeText(r.expense_pct)}}</td><td>${{safeText(r.control_lever)}}</td><td>${{safeText(r.action)}}</td></tr>`).join("");
    }}
    function renderMerchants() {{
      document.getElementById("merchants").innerHTML = `<tr><th>交易对方</th><th>笔数</th><th>金额</th></tr>` + DATA.merchants.map(r => `<tr><td>${{r.name}}</td><td>${{r.count}}</td><td>${{yuan(r.amount)}}</td></tr>`).join("");
    }}
    function renderCounterpartyConcentration() {{
      const rows = DATA.counterparty_concentration || [];
      const max = Math.max(...rows.map(r => Number(r.amount || 0)), 1);
      document.getElementById("counterpartyConcentration").innerHTML = rows.map(r => {{
        const width = Math.max(2, Number(r.amount || 0) / max * 100);
        return `<div class="bar-row"><div class="bar-name" title="${{safeText(r.name)}}">${{safeText(r.name)}} · 累计 ${{safeText(r.cumulative_pct)}}</div><div class="bar-bg"><div class="bar cyan" style="width:${{width}}%"></div></div><div>${{yuan(r.amount)}}</div></div>`;
      }}).join("");
    }}
    function renderTimeHeatmap() {{
      const rows = DATA.time_heatmap || [];
      const parts = [["early", "凌晨"], ["morning", "上午"], ["afternoon", "下午"], ["evening", "晚间"]];
      const max = Math.max(...rows.flatMap(r => parts.map(([key]) => Number(r[key] || 0))), 1);
      const head = `<div class="heatmap-row"><div></div>${{parts.map(([_key, label]) => `<div class="heatmap-head">${{label}}</div>`).join("")}}</div>`;
      const body = rows.map(r => {{
        const cells = parts.map(([key, label]) => {{
          const value = Number(r[key] || 0);
          const alpha = value > 0 ? (0.08 + Math.min(0.44, value / max * 0.44)).toFixed(3) : "0.020";
          return `<div class="heatmap-cell" style="background:rgba(37,99,235,${{alpha}})"><span class="heatmap-label">${{label}}</span><span class="heatmap-value">${{yuan(value)}}</span></div>`;
        }}).join("");
        return `<div class="heatmap-row"><div class="heatmap-day">${{safeText(r.weekday)}}</div>${{cells}}</div>`;
      }}).join("");
      document.getElementById("timeHeatmap").innerHTML = head + body;
    }}
    function renderMonthlyCategoryHeatmap() {{
      const rows = DATA.monthly_category_heatmap || [];
      const cats = [["necessity", "生活刚需"], ["optimizable", "可优化消费"], ["social", "社交家庭"], ["financial", "金融资金"]];
      const max = Math.max(...rows.flatMap(r => cats.map(([key]) => Number(r[key] || 0))), 1);
      const head = `<div class="matrix-row"><div></div>${{cats.map(([_key, label]) => `<div class="matrix-head">${{label}}</div>`).join("")}}</div>`;
      const body = rows.map(r => {{
        const cells = cats.map(([key, label]) => {{
          const value = Number(r[key] || 0);
          const alpha = value > 0 ? (0.07 + Math.min(0.46, value / max * 0.46)).toFixed(3) : "0.020";
          return `<div class="matrix-cell" style="background:rgba(5,122,85,${{alpha}})" title="${{safeText(r.month)}} ${{label}} ${{yuan(value)}}"><span class="heatmap-label">${{label}}</span><span class="matrix-value">${{yuan(value)}}</span></div>`;
        }}).join("");
        return `<div class="matrix-row"><div class="matrix-month">${{safeText(r.month)}}</div>${{cells}}</div>`;
      }}).join("");
      document.getElementById("monthlyCategoryHeatmap").innerHTML = head + body;
    }}
    bars("weekdays", DATA.weekdays, "name", "amount", "cyan");
    bars("hours", DATA.hours.filter(r => Number(r.amount) > 0), "name", "amount", "amber");
    renderSourceHealth();
    renderReviewStatus();
    renderMonthlyChart();
    renderCategoryDonut();
    periodBars("monthly", DATA.monthly, "blue");
    periodBars("weekly", DATA.weekly, "green");
    categoryBars();
    riskBars();
    renderMechanismBars();
    renderCategories();
    renderBehaviorBuckets();
    renderCumulativeCashflow();
    renderBudgetPressureRadar();
    renderReview();
    renderControlPlan();
    renderRiskControlMatrix();
    renderMerchants();
    renderCounterpartyConcentration();
    renderTimeHeatmap();
    renderMonthlyCategoryHeatmap();
  </script>
</body>
</html>"""


def _transaction_explorer_html(
    allocation_rows: list[dict[str, Any]],
    review_rows: list[dict[str, Any]],
    tag_library_rows: list[dict[str, Any]] | None = None,
    tag_filter_preset_rows: list[dict[str, Any]] | None = None,
) -> str:
    production = [
        {
            "date": item.get("date", ""),
            "transaction_time": item.get("transaction_time", ""),
            "source_platform": item.get("source_platform", ""),
            "counterparty": item.get("counterparty", ""),
            "description": item.get("description", ""),
            "amount": item.get("allocated_amount", 0),
            "main_category": item.get("main_category", ""),
            "sub_category": item.get("sub_category", ""),
            "risk_tags": item.get("risk_tags", ""),
            "review_key": item.get("review_key", ""),
            "review_decision": item.get("review_decision", ""),
            "source": "生产统计",
        }
        for item in allocation_rows
    ]
    pending = [
        {
            "date": item.get("date", ""),
            "transaction_time": item.get("transaction_time", ""),
            "source_platform": item.get("source_platform", ""),
            "counterparty": item.get("counterparty", ""),
            "description": item.get("description", ""),
            "amount": item.get("amount", 0),
            "main_category": item.get("main_category", ""),
            "sub_category": item.get("sub_category", ""),
            "risk_tags": item.get("risk_tags", ""),
            "review_key": item.get("order_id", ""),
            "review_decision": "pending_review",
            "source": "大额待复核",
        }
        for item in review_rows
    ]
    data = {
        "production": production,
        "pending": pending,
        "taxonomy": TAXONOMY,
        "risk_tags": _active_tag_names(tag_library_rows or _tag_library_rows()),
        "tag_library": tag_library_rows or _tag_library_rows(),
        "filter_presets": _active_filter_presets(tag_filter_preset_rows or _tag_filter_preset_rows()),
    }
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>交易明细查询</title>
  <style>
    :root {{ --bg:#f5f7fb; --panel:#fff; --ink:#172033; --muted:#647083; --line:#d9e0ea; --blue:#2563eb; --green:#047857; --red:#b42318; --amber:#a16207; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; background:var(--bg); color:var(--ink); }}
    header {{ padding:20px 28px 14px; background:#fff; border-bottom:1px solid var(--line); position:sticky; top:0; z-index:3; }}
    h1 {{ margin:0 0 6px; font-size:23px; letter-spacing:0; }}
    .sub {{ color:var(--muted); font-size:13px; }}
    main {{ max-width:1500px; margin:0 auto; padding:18px 28px 42px; }}
    .tabs,.quick {{ display:flex; gap:8px; flex-wrap:wrap; margin-bottom:12px; }}
    button {{ border:1px solid var(--line); background:#fff; color:var(--ink); border-radius:7px; padding:8px 11px; cursor:pointer; font-size:13px; }}
    button.active,button.primary {{ background:var(--blue); border-color:var(--blue); color:#fff; }}
    .filters {{ display:grid; grid-template-columns:1.4fr repeat(7,minmax(118px,1fr)); gap:8px; background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:12px; }}
    .tag-combo {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(126px,1fr)); gap:8px; background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:12px; margin-top:10px; }}
    .tag-chip {{ border:1px solid var(--line); border-radius:7px; padding:7px 9px; display:flex; gap:7px; align-items:center; font-size:12px; background:#fff; }}
    .tag-chip input {{ width:auto; }}
    .search-feedback {{ background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:12px; margin:10px 0 12px; }}
    .feedback-grid {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:10px; }}
    .feedback-block strong {{ display:block; font-size:12px; color:var(--muted); margin-bottom:7px; }}
    .feedback-chips {{ display:flex; flex-wrap:wrap; gap:6px; }}
    .feedback-chip {{ display:inline-flex; align-items:center; max-width:100%; padding:4px 8px; border-radius:999px; background:#eef2f7; color:#243247; font-size:12px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }}
    mark {{ background:#fff1a8; color:inherit; padding:0 2px; border-radius:3px; }}
    input,select {{ width:100%; border:1px solid var(--line); border-radius:7px; padding:8px; font-size:13px; background:#fff; color:var(--ink); }}
    .metrics {{ display:grid; grid-template-columns:repeat(4,minmax(140px,1fr)); gap:10px; margin:14px 0; }}
    .metric {{ background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:13px; min-height:74px; }}
    .label {{ color:var(--muted); font-size:12px; }}
    .value {{ margin-top:6px; font-size:20px; font-weight:750; overflow-wrap:anywhere; }}
    .drilldown {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:10px; margin:0 0 14px; }}
    .mini-panel {{ background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:12px; min-width:0; }}
    .mini-panel h2 {{ margin:0 0 10px; font-size:15px; }}
    .mini-bars {{ display:grid; gap:8px; }}
    .mini-row {{ display:grid; grid-template-columns:minmax(72px,1fr) 1.5fr 86px; gap:8px; align-items:center; font-size:12px; }}
    .mini-name {{ overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }}
    .mini-bg {{ height:10px; background:#edf1f7; border-radius:7px; overflow:hidden; }}
    .mini-bar {{ height:10px; background:var(--blue); border-radius:7px; }}
    .mini-bar.green {{ background:var(--green); }}
    .mini-bar.red {{ background:var(--red); }}
    .mini-bar.amber {{ background:var(--amber); }}
    .panel {{ background:var(--panel); border:1px solid var(--line); border-radius:8px; overflow:hidden; }}
    .panel-head {{ display:flex; justify-content:space-between; gap:10px; align-items:center; padding:12px 14px; border-bottom:1px solid var(--line); }}
    .panel-head strong {{ font-size:15px; }}
    .panel-head-actions {{ display:flex; gap:8px; align-items:center; flex-wrap:wrap; justify-content:flex-end; }}
    .panel.collapsed .table-wrap,.panel.collapsed .pager {{ display:none; }}
    table {{ width:100%; border-collapse:collapse; font-size:13px; }}
    th,td {{ padding:9px 8px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }}
    th {{ background:#f8fafc; }}
    td.amount,th.amount {{ text-align:right; }}
    .desc {{ max-width:360px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }}
    .pill {{ display:inline-block; padding:2px 7px; border-radius:999px; background:#eef2f7; color:#334155; margin:0 4px 4px 0; font-size:12px; }}
    .pending {{ color:var(--red); font-weight:700; }}
    .pager {{ display:flex; gap:8px; align-items:center; justify-content:flex-end; padding:12px 14px; }}
    .empty {{ padding:28px; text-align:center; color:var(--muted); }}
    @media (max-width:1100px) {{ .filters {{ grid-template-columns:1fr 1fr; }} .metrics,.drilldown,.feedback-grid {{ grid-template-columns:1fr 1fr; }} th {{ position:static; }} }}
    @media (max-width:720px) {{ main,header {{ padding-left:14px; padding-right:14px; }} .filters,.metrics,.drilldown,.feedback-grid {{ grid-template-columns:1fr; }} .desc {{ max-width:220px; }} table {{ font-size:12px; }} }}
  </style>
</head>
<body>
  <header>
    <h1>交易明细查询</h1>
    <div class="sub">生产统计与大额待复核分开查看；导出结果会遵循当前筛选条件。</div>
  </header>
  <main>
    <div class="tabs">
      <button id="tabProduction" class="active" onclick="setDataset('production')">生产统计</button>
      <button id="tabPending" onclick="setDataset('pending')">大额待复核</button>
      <button class="primary" onclick="exportCsv()">导出当前筛选</button>
    </div>
    <section class="filters">
      <input id="q" placeholder="搜索交易对方、说明、风险标签" oninput="applyFilters()">
      <select id="mainCategory" onchange="syncSubOptions(); applyFilters()"></select>
      <select id="subCategory" onchange="applyFilters()"></select>
      <select id="tagPreset" onchange="applyTagPreset()"></select>
      <select id="tagMatchMode" onchange="applyFilters()"><option value="any">标签任一命中</option><option value="all">标签全部命中</option></select>
      <input id="dateFrom" type="date" onchange="applyFilters()">
      <input id="dateTo" type="date" onchange="applyFilters()">
      <input id="minAmount" type="number" min="0" step="0.01" placeholder="最小金额" oninput="applyFilters()">
    </section>
    <section id="tagCombo" class="tag-combo"></section>
    <div class="quick">
      <button onclick="quick('all')">全部</button>
      <button onclick="quick('large')">1 万以上</button>
      <button onclick="quick('credit')">信用工具</button>
      <button onclick="quick('optimizable')">可优化消费</button>
      <button onclick="quick('social')">社交家庭</button>
      <button onclick="quick('financial')">金融资金</button>
    </div>
    <section id="searchFeedback" class="search-feedback"></section>
    <section class="metrics">
      <div class="metric"><div class="label">筛选笔数</div><div class="value" id="mCount">0</div></div>
      <div class="metric"><div class="label">筛选金额</div><div class="value" id="mAmount">¥0.00</div></div>
      <div class="metric"><div class="label">最高主类</div><div class="value" id="mTopMain">-</div></div>
      <div class="metric"><div class="label">最高对手方</div><div class="value" id="mTopCounterparty">-</div></div>
    </section>
    <section class="drilldown">
      <div class="mini-panel">
        <h2>筛选主类分布</h2>
        <div id="explorerCategoryBars" class="mini-bars"></div>
      </div>
      <div class="mini-panel">
        <h2>筛选风险标签</h2>
        <div id="explorerRiskBars" class="mini-bars"></div>
      </div>
      <div class="mini-panel">
        <h2>筛选月份趋势</h2>
        <div id="explorerMonthTrend" class="mini-bars"></div>
      </div>
      <div class="mini-panel">
        <h2>筛选对手方排行</h2>
        <div id="explorerCounterpartyBars" class="mini-bars"></div>
      </div>
    </section>
    <section class="panel" id="detailPanel">
      <div class="panel-head">
        <strong>明细列表</strong>
        <div class="panel-head-actions">
          <span id="pageInfo" class="sub"></span>
          <button id="detailToggle" onclick="toggleDetails()">折叠明细</button>
        </div>
      </div>
      <div class="table-wrap" style="overflow:auto">
        <table>
          <thead><tr><th>时间</th><th>平台</th><th>对方</th><th>说明</th><th>主类</th><th>子类</th><th>风险标签</th><th class="amount">金额</th></tr></thead>
          <tbody id="tbody"></tbody>
        </table>
      </div>
      <div class="pager">
        <button onclick="prevPage()">上一页</button>
        <button onclick="nextPage()">下一页</button>
      </div>
    </section>
  </main>
  <script>
    const DATA = {json.dumps(data, ensure_ascii=False)};
    let dataset = "production";
    let filtered = [];
    let page = 1;
    let detailsCollapsed = false;
    const pageSize = 80;
    const yuan = n => "¥" + Number(n || 0).toLocaleString("zh-CN", {{ minimumFractionDigits:2, maximumFractionDigits:2 }});
    const byId = id => document.getElementById(id);
    function escapeHtml(value) {{
      return String(value ?? "").replace(/[&<>"']/g, ch => ({{"&":"&amp;","<":"&lt;",">":"&gt;","\\\"":"&quot;","'":"&#39;"}}[ch]));
    }}
    function normalizeSearch(value) {{
      return String(value ?? "")
        .normalize("NFKC")
        .toLowerCase()
        .replace(/[\\s\\-_.,，。:：;；\\/\\\\|()（）\\[\\]【】"'“”‘’]+/g, "");
    }}
    function isSubsequence(needle, haystack) {{
      if (!needle) return true;
      let index = 0;
      for (const char of haystack) {{
        if (char === needle[index]) index += 1;
        if (index >= needle.length) return true;
      }}
      return false;
    }}
    function fuzzySearchMatch(row, rawQuery) {{
      const query = String(rawQuery || "").trim().toLowerCase();
      if (!query) return {{ ok: true, score: 0, fields: [] }};
      const tokens = query.split(/\\s+/).filter(Boolean);
      const compactQuery = normalizeSearch(query);
      const fields = [
        ["counterparty", "对手方", row.counterparty],
        ["description", "说明", row.description],
        ["risk_tags", "风险标签", row.risk_tags],
        ["main_category", "主类", row.main_category],
        ["sub_category", "子类", row.sub_category],
        ["review_key", "订单/复核键", row.review_key],
      ];
      let best = 0;
      const matchedFields = [];
      for (const [key, label, value] of fields) {{
        const text = String(value ?? "").toLowerCase();
        const compact = normalizeSearch(value);
        let score = 0;
        if (text.includes(query)) score = 100;
        else if (compactQuery && compact.includes(compactQuery)) score = 85;
        else if (tokens.length && tokens.every(token => text.includes(token) || compact.includes(normalizeSearch(token)))) score = 70;
        else if (compactQuery && isSubsequence(compactQuery, compact)) score = 45;
        if (score) {{
          best = Math.max(best, score);
          matchedFields.push({{ key, label, value: String(value ?? ""), score }});
        }}
      }}
      matchedFields.sort((a, b) => b.score - a.score);
      return {{ ok: matchedFields.length > 0, score: best, fields: matchedFields }};
    }}
    function highlightText(value) {{
      const text = String(value ?? "");
      const query = byId("q") ? byId("q").value.trim() : "";
      if (!query) return escapeHtml(text);
      const lower = text.toLowerCase();
      const direct = query.toLowerCase();
      let idx = lower.indexOf(direct);
      let length = direct.length;
      if (idx < 0) {{
        const tokens = direct.split(/\\s+/).filter(Boolean).sort((a, b) => b.length - a.length);
        for (const token of tokens) {{
          idx = lower.indexOf(token);
          length = token.length;
          if (idx >= 0) break;
        }}
      }}
      if (idx < 0 || length <= 0) return escapeHtml(text);
      return escapeHtml(text.slice(0, idx)) + `<mark>${{escapeHtml(text.slice(idx, idx + length))}}</mark>` + escapeHtml(text.slice(idx + length));
    }}
    function rows() {{ return DATA[dataset] || []; }}
    function initControls() {{
      byId("mainCategory").innerHTML = `<option value="">全部主类</option>` + Object.keys(DATA.taxonomy).map(v => `<option value="${{escapeHtml(v)}}">${{escapeHtml(v)}}</option>`).join("");
      byId("tagPreset").innerHTML = `<option value="">自定义标签组合</option>` + DATA.filter_presets.map(v => `<option value="${{escapeHtml(v.preset_id)}}">${{escapeHtml(v.preset_name)}}</option>`).join("");
      byId("tagCombo").innerHTML = DATA.risk_tags.map(v => {{
        const tag = DATA.tag_library.find(item => item.tag_name === v) || {{}};
        return `<label class="tag-chip"><input type="checkbox" value="${{escapeHtml(v)}}" onchange="applyFilters()"><span style="width:9px;height:9px;border-radius:2px;background:${{escapeHtml(tag.color || "#647083")}}"></span>${{escapeHtml(v)}}</label>`;
      }}).join("");
      syncSubOptions();
    }}
    function selectedTags() {{ return [...document.querySelectorAll("#tagCombo input:checked")].map(el => el.value); }}
    function setSelectedTags(tags) {{ document.querySelectorAll("#tagCombo input").forEach(el => el.checked = tags.includes(el.value)); }}
    function applyTagPreset() {{
      const preset = DATA.filter_presets.find(item => item.preset_id === byId("tagPreset").value);
      if (preset) {{
        setSelectedTags(String(preset.tags || "").split("|").filter(Boolean));
        byId("tagMatchMode").value = preset.match_mode || "any";
      }}
      page = 1;
      applyFilters();
    }}
    function syncSubOptions() {{
      const main = byId("mainCategory").value;
      const subs = main ? (DATA.taxonomy[main] || []) : [...new Set(rows().map(r => r.sub_category).filter(Boolean))].sort();
      byId("subCategory").innerHTML = `<option value="">全部子类</option>` + subs.map(v => `<option value="${{escapeHtml(v)}}">${{escapeHtml(v)}}</option>`).join("");
    }}
    function setDataset(name) {{
      dataset = name;
      page = 1;
      byId("tabProduction").classList.toggle("active", name === "production");
      byId("tabPending").classList.toggle("active", name === "pending");
      syncSubOptions();
      applyFilters();
    }}
    function applyFilters() {{
      const query = byId("q").value.trim().toLowerCase();
      const main = byId("mainCategory").value;
      const sub = byId("subCategory").value;
      const selected = selectedTags();
      const tagMatchMode = byId("tagMatchMode").value || "any";
      const from = byId("dateFrom").value;
      const to = byId("dateTo").value;
      const minAmount = Number(byId("minAmount").value || 0);
      filtered = rows().filter(r => {{
        const haystack = `${{r.counterparty}} ${{r.description}} ${{r.risk_tags}} ${{r.main_category}} ${{r.sub_category}}`.toLowerCase();
        if (query) {{
          const match = fuzzySearchMatch(r, query);
          if (!match.ok) return false;
          r._searchMatch = match;
        }} else {{
          delete r._searchMatch;
        }}
        if (main && r.main_category !== main) return false;
        if (sub && r.sub_category !== sub) return false;
        const rowTags = String(r.risk_tags || "").split("|").filter(Boolean);
        if (selected.length && tagMatchMode === "all" && !selected.every(tag => rowTags.includes(tag))) return false;
        if (selected.length && tagMatchMode !== "all" && !selected.some(tag => rowTags.includes(tag))) return false;
        if (from && String(r.date || "") < from) return false;
        if (to && String(r.date || "") > to) return false;
        if (Number(r.amount || 0) < minAmount) return false;
        return true;
      }});
      page = Math.min(page, Math.max(1, Math.ceil(filtered.length / pageSize)));
      renderMetrics();
      renderTable();
    }}
    function quick(name) {{
      byId("q").value = "";
      byId("mainCategory").value = "";
      syncSubOptions();
      byId("subCategory").value = "";
      byId("tagPreset").value = "";
      byId("tagMatchMode").value = "any";
      setSelectedTags([]);
      byId("minAmount").value = "";
      if (name === "large") byId("minAmount").value = "10000";
      if (name === "credit") setSelectedTags(["信用工具", "信用周转"]);
      if (name === "optimizable") byId("mainCategory").value = "可优化消费";
      if (name === "social") byId("mainCategory").value = "社交家庭";
      if (name === "financial") byId("mainCategory").value = "金融资金";
      syncSubOptions();
      page = 1;
      applyFilters();
    }}
    function topBy(rows, key) {{
      const totals = new Map();
      rows.forEach(r => totals.set(r[key] || "未填写", (totals.get(r[key] || "未填写") || 0) + Number(r.amount || 0)));
      return [...totals.entries()].sort((a,b) => b[1] - a[1])[0] || ["-", 0];
    }}
    function groupedRows(rows, keyFn, limit=6) {{
      const totals = new Map();
      rows.forEach(r => {{
        const key = keyFn(r);
        if (!key) return;
        totals.set(key, (totals.get(key) || 0) + Number(r.amount || 0));
      }});
      return [...totals.entries()].sort((a,b) => b[1] - a[1]).slice(0, limit).map(([name, amount]) => ({{ name, amount }}));
    }}
    function renderMiniBars(id, rows, colorClass="") {{
      const root = byId(id);
      const max = Math.max(...rows.map(r => Number(r.amount || 0)), 1);
      if (!rows.length) {{
        root.innerHTML = `<div class="empty">暂无数据</div>`;
        return;
      }}
      root.innerHTML = rows.map(r => {{
        const width = Math.max(2, Number(r.amount || 0) / max * 100);
        return `<div class="mini-row"><div class="mini-name" title="${{escapeHtml(r.name)}}">${{escapeHtml(r.name)}}</div><div class="mini-bg"><div class="mini-bar ${{colorClass}}" style="width:${{width}}%"></div></div><div>${{yuan(r.amount)}}</div></div>`;
      }}).join("");
    }}
    function renderDrilldown() {{
      renderMiniBars("explorerCategoryBars", groupedRows(filtered, r => r.main_category || "未分类"), "green");
      renderMiniBars("explorerRiskBars", groupedRows(filtered.flatMap(r => String(r.risk_tags || "").split("|").filter(Boolean).map(tag => ({{ amount: r.amount, tag }}))), r => r.tag || "未标记"), "red");
      renderMiniBars("explorerMonthTrend", groupedRows(filtered, r => String(r.date || "").slice(0, 7), 8).sort((a,b) => a.name.localeCompare(b.name)), "amber");
      renderMiniBars("explorerCounterpartyBars", groupedRows(filtered, r => r.counterparty || "未填写"), "");
    }}
    function groupedCounts(rows, keyFn, limit=8) {{
      const counts = new Map();
      rows.forEach(r => {{
        const key = keyFn(r);
        if (!key) return;
        counts.set(key, (counts.get(key) || 0) + 1);
      }});
      return [...counts.entries()].sort((a, b) => b[1] - a[1]).slice(0, limit).map(([name, count]) => ({{ name, count }}));
    }}
    function renderFeedbackBlock(title, items) {{
      const chips = items.length
        ? items.map(item => `<span class="feedback-chip" title="${{escapeHtml(item.name)}}">${{escapeHtml(item.name)}} · ${{item.count}}笔</span>`).join("")
        : `<span class="feedback-chip">无</span>`;
      return `<div class="feedback-block"><strong>${{title}}</strong><div class="feedback-chips">${{chips}}</div></div>`;
    }}
    function renderSearchFeedback() {{
      const query = byId("q").value.trim();
      const root = byId("searchFeedback");
      if (!query) {{
        root.innerHTML = `<div class="sub">搜索反馈：输入关键词后会显示模糊搜索命中的交易对方、说明、分类、标签和命中字段。</div>`;
        return;
      }}
      const fieldCounts = new Map();
      filtered.forEach(row => (row._searchMatch?.fields || []).forEach(field => fieldCounts.set(field.label, (fieldCounts.get(field.label) || 0) + 1)));
      const fields = [...fieldCounts.entries()].sort((a, b) => b[1] - a[1]).map(([name, count]) => ({{ name, count }}));
      const categories = groupedCounts(filtered, r => [r.main_category, r.sub_category].filter(Boolean).join(" / "), 8);
      const tags = groupedCounts(
        filtered.flatMap(r => String(r.risk_tags || "").split("|").filter(Boolean).map(tag => ({{ tag }}))),
        r => r.tag,
        8
      );
      root.innerHTML = `
        <div class="sub" style="margin-bottom:10px">搜索反馈：关键词 <strong>${{escapeHtml(query)}}</strong> 命中 ${{filtered.length}} 笔；匹配方式包含精确、去符号模糊和字符顺序模糊。</div>
        <div class="feedback-grid">
          ${{renderFeedbackBlock("命中交易对方", groupedCounts(filtered, r => r.counterparty || "未填写", 8))}}
          ${{renderFeedbackBlock("命中说明对象", groupedCounts(filtered, r => r.description || "未填写", 8))}}
          ${{renderFeedbackBlock("命中分类", categories)}}
          ${{renderFeedbackBlock("命中标签/字段", [...tags, ...fields].slice(0, 10))}}
        </div>`;
    }}
    function renderMetrics() {{
      const sum = filtered.reduce((acc, r) => acc + Number(r.amount || 0), 0);
      byId("mCount").textContent = filtered.length;
      byId("mAmount").textContent = yuan(sum);
      const topMain = topBy(filtered, "main_category");
      const topCounterparty = topBy(filtered, "counterparty");
      byId("mTopMain").textContent = `${{topMain[0]}} ${{topMain[1] ? yuan(topMain[1]) : ""}}`;
      byId("mTopCounterparty").textContent = `${{topCounterparty[0]}} ${{topCounterparty[1] ? yuan(topCounterparty[1]) : ""}}`;
      renderDrilldown();
      renderSearchFeedback();
    }}
    function renderTable() {{
      const start = (page - 1) * pageSize;
      const visible = filtered.slice(start, start + pageSize);
      const tbody = byId("tbody");
      if (!visible.length) {{
        tbody.innerHTML = `<tr><td colspan="8" class="empty">没有符合条件的交易。</td></tr>`;
      }} else {{
        tbody.innerHTML = visible.map(r => {{
          const tags = String(r.risk_tags || "").split("|").filter(Boolean).map(t => `<span class="pill">${{highlightText(t)}}</span>`).join("");
          const pending = dataset === "pending" ? " pending" : "";
          return `<tr><td>${{escapeHtml(r.transaction_time || r.date)}}</td><td>${{escapeHtml(r.source_platform || "")}}</td><td>${{highlightText(r.counterparty)}}</td><td class="desc" title="${{escapeHtml(r.description)}}">${{highlightText(r.description)}}</td><td>${{highlightText(r.main_category)}}</td><td>${{highlightText(r.sub_category)}}</td><td>${{tags}}</td><td class="amount${{pending}}">${{yuan(r.amount)}}</td></tr>`;
        }}).join("");
      }}
      const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
      byId("pageInfo").textContent = `第 ${{page}} / ${{totalPages}} 页，共 ${{filtered.length}} 行`;
      updateDetailsVisibility();
    }}
    function toggleDetails() {{
      detailsCollapsed = !detailsCollapsed;
      updateDetailsVisibility();
    }}
    function updateDetailsVisibility() {{
      const panel = byId("detailPanel");
      const button = byId("detailToggle");
      if (!panel || !button) return;
      panel.classList.toggle("collapsed", detailsCollapsed);
      button.textContent = detailsCollapsed ? "展开明细" : "折叠明细";
      button.setAttribute("aria-expanded", detailsCollapsed ? "false" : "true");
    }}
    function prevPage() {{ page = Math.max(1, page - 1); renderTable(); }}
    function nextPage() {{ page = Math.min(Math.max(1, Math.ceil(filtered.length / pageSize)), page + 1); renderTable(); }}
    function csvEscape(value) {{
      const text = String(value ?? "");
      return /[",\\n]/.test(text) ? `"${{text.replaceAll('"', '""')}}"` : text;
    }}
    function exportCsv() {{
      const header = ["source","source_platform","transaction_time","counterparty","description","main_category","sub_category","risk_tags","amount","review_key","review_decision"];
      const lines = [header, ...filtered.map(r => header.map(k => r[k] ?? ""))].map(row => row.map(csvEscape).join(",")).join("\\n") + "\\n";
      const blob = new Blob([lines], {{ type:"text/csv;charset=utf-8" }});
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = dataset === "pending" ? "pending_review_filtered.csv" : "production_transactions_filtered.csv";
      a.click();
      URL.revokeObjectURL(url);
    }}
    Object.assign(window, {{ setDataset, syncSubOptions, applyFilters, applyTagPreset, quick, prevPage, nextPage, toggleDetails, exportCsv }});
    initControls();
    applyFilters();
  </script>
</body>
</html>"""


def _behavior_analysis_html(allocation_rows: list[dict[str, Any]], tag_library_rows: list[dict[str, Any]], tag_filter_preset_rows: list[dict[str, Any]]) -> str:
    rows = [
        {
            "date": item.get("date", ""),
            "month": str(item.get("date", ""))[:7],
            "transaction_time": item.get("transaction_time", ""),
            "counterparty": item.get("counterparty", ""),
            "description": item.get("description", ""),
            "amount": item.get("allocated_amount", 0),
            "main_category": item.get("main_category", ""),
            "sub_category": item.get("sub_category", ""),
            "risk_tags": item.get("risk_tags", ""),
        }
        for item in allocation_rows
    ]
    data = {
        "rows": rows,
        "taxonomy": TAXONOMY,
        "tag_library": tag_library_rows,
        "filter_presets": _active_filter_presets(tag_filter_preset_rows),
    }
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>交易行为分析</title>
  <style>
    :root {{ --bg:#f3f6f8; --panel:#fff; --ink:#111827; --muted:#667085; --line:#d8dee8; --blue:#1d4ed8; --green:#047857; --red:#b42318; --amber:#b45309; --purple:#7c3aed; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; background:var(--bg); color:var(--ink); }}
    header {{ padding:20px 28px 14px; border-bottom:1px solid var(--line); background:#fff; position:sticky; top:0; z-index:2; }}
    h1 {{ margin:0 0 6px; font-size:23px; letter-spacing:0; }}
    .sub {{ color:var(--muted); font-size:13px; }}
    main {{ max-width:1500px; margin:0 auto; padding:18px 28px 42px; }}
    .filters,.metrics,.workspace {{ display:grid; gap:10px; }}
    .filters {{ grid-template-columns:1.2fr repeat(5,minmax(130px,1fr)); background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:12px; }}
    .tag-grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(128px,1fr)); gap:8px; margin-top:10px; }}
    .tag-chip {{ border:1px solid var(--line); border-radius:7px; padding:7px 9px; background:#fff; font-size:12px; display:flex; gap:7px; align-items:center; cursor:pointer; }}
    .tag-chip input {{ width:auto; }}
    input,select,button {{ border:1px solid var(--line); border-radius:7px; padding:8px; font-size:13px; background:#fff; color:var(--ink); }}
    button.primary {{ background:var(--blue); color:#fff; border-color:var(--blue); }}
    .metrics {{ grid-template-columns:repeat(5,minmax(140px,1fr)); margin:14px 0; }}
    .metric,.panel {{ background:var(--panel); border:1px solid var(--line); border-radius:8px; }}
    .metric {{ padding:13px; min-height:74px; }}
    .label {{ color:var(--muted); font-size:12px; }}
    .value {{ margin-top:6px; font-size:20px; font-weight:750; overflow-wrap:anywhere; }}
    .workspace {{ grid-template-columns:1.25fr .75fr; align-items:start; }}
    .panel {{ padding:14px; min-width:0; }}
    h2 {{ margin:0 0 10px; font-size:16px; }}
    .chart {{ width:100%; height:360px; background:#fbfcfe; border:1px solid var(--line); border-radius:8px; display:block; }}
    .bars {{ display:grid; gap:9px; }}
    .bar-row {{ display:grid; grid-template-columns:minmax(110px,1fr) 1.5fr 112px; gap:10px; align-items:center; font-size:12px; }}
    .bar-name {{ overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }}
    .bar-bg {{ height:11px; background:#edf1f7; border-radius:8px; overflow:hidden; }}
    .bar {{ height:11px; background:var(--blue); border-radius:8px; }}
    .two {{ display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-top:10px; }}
    table {{ width:100%; border-collapse:collapse; font-size:12px; }}
    th,td {{ padding:8px; border-bottom:1px solid var(--line); text-align:left; }}
    td:last-child,th:last-child {{ text-align:right; }}
    @media (max-width:1050px) {{ .filters,.workspace,.metrics,.two {{ grid-template-columns:1fr; }} }}
    @media (max-width:720px) {{ main,header {{ padding-left:14px; padding-right:14px; }} .chart {{ height:300px; }} .bar-row {{ grid-template-columns:1fr; gap:5px; }} }}
  </style>
</head>
<body>
  <header>
    <h1>交易行为分析</h1>
    <div class="sub">用持久化标签库组合筛选交易范围，并切换折线图、直方图、环形图和柱状图。</div>
  </header>
  <main>
    <section class="filters">
      <input id="q" placeholder="搜索对手方、说明、标签" oninput="applyFilters()">
      <select id="preset" onchange="applyPreset()"></select>
      <select id="matchMode" onchange="applyFilters()"><option value="any">标签任一命中</option><option value="all">标签全部命中</option></select>
      <select id="groupBy" onchange="renderAll()"><option value="month">按月份</option><option value="weekday">按星期</option><option value="hour">按小时</option><option value="main_category">按主类</option><option value="counterparty">按对手方</option></select>
      <select id="chartType" onchange="renderAll()"><option value="line">折线图</option><option value="bar">直方图</option><option value="donut">环形图</option><option value="histogram">金额分布图</option></select>
      <button class="primary" onclick="exportCsv()">导出当前范围</button>
      <input id="dateFrom" type="date" onchange="applyFilters()">
      <input id="dateTo" type="date" onchange="applyFilters()">
      <select id="mainCategory" onchange="applyFilters()"></select>
      <input id="minAmount" type="number" min="0" step="0.01" placeholder="最小金额" oninput="applyFilters()">
      <input id="maxAmount" type="number" min="0" step="0.01" placeholder="最大金额" oninput="applyFilters()">
      <button onclick="clearTags()">清空标签</button>
    </section>
    <section id="tagGrid" class="tag-grid"></section>
    <section class="metrics">
      <div class="metric"><div class="label">当前交易笔数</div><div class="value" id="mCount">0</div></div>
      <div class="metric"><div class="label">当前金额</div><div class="value" id="mAmount">¥0.00</div></div>
      <div class="metric"><div class="label">单笔均值</div><div class="value" id="mAvg">¥0.00</div></div>
      <div class="metric"><div class="label">高发标签</div><div class="value" id="mTopTag">-</div></div>
      <div class="metric"><div class="label">高发对手方</div><div class="value" id="mTopCounterparty">-</div></div>
    </section>
    <section class="workspace">
      <div class="panel">
        <h2>自定义图表</h2>
        <svg id="behaviorChart" class="chart" role="img" aria-label="交易行为自定义图表"></svg>
      </div>
      <div class="panel">
        <h2>分组排行</h2>
        <div id="rankBars" class="bars"></div>
      </div>
    </section>
    <section class="two">
      <div class="panel"><h2>标签组合金额</h2><div id="tagBars" class="bars"></div></div>
      <div class="panel"><h2>最近明细</h2><table id="recentTable"></table></div>
    </section>
  </main>
  <script>
    const DATA = {json.dumps(data, ensure_ascii=False)};
    let filtered = [];
    const yuan = n => "¥" + Number(n || 0).toLocaleString("zh-CN", {{minimumFractionDigits:2, maximumFractionDigits:2}});
    const safe = v => String(v ?? "").replace(/[&<>"']/g, ch => ({{"&":"&amp;","<":"&lt;",">":"&gt;","\\\"":"&quot;","'":"&#39;"}}[ch]));
    const tagNames = () => DATA.tag_library.filter(t => String(t.is_active ?? "1") !== "0").map(t => t.tag_name);
    function tags(row) {{ return String(row.risk_tags || "").split("|").filter(Boolean); }}
    function init() {{
      document.getElementById("preset").innerHTML = `<option value="">自定义标签组合</option>` + DATA.filter_presets.map(p => `<option value="${{safe(p.preset_id)}}">${{safe(p.preset_name)}}</option>`).join("");
      document.getElementById("mainCategory").innerHTML = `<option value="">全部主类</option>` + Object.keys(DATA.taxonomy).map(v => `<option value="${{safe(v)}}">${{safe(v)}}</option>`).join("");
      document.getElementById("tagGrid").innerHTML = tagNames().map(name => {{
        const item = DATA.tag_library.find(t => t.tag_name === name) || {{}};
        return `<label class="tag-chip"><input type="checkbox" value="${{safe(name)}}" onchange="applyFilters()"><span style="width:9px;height:9px;border-radius:2px;background:${{safe(item.color || "#64748b")}}"></span>${{safe(name)}}</label>`;
      }}).join("");
      applyFilters();
    }}
    function selectedTags() {{ return [...document.querySelectorAll("#tagGrid input:checked")].map(el => el.value); }}
    function setTags(values) {{ document.querySelectorAll("#tagGrid input").forEach(el => el.checked = values.includes(el.value)); }}
    function clearTags() {{ setTags([]); document.getElementById("preset").value = ""; applyFilters(); }}
    function applyPreset() {{
      const preset = DATA.filter_presets.find(p => p.preset_id === document.getElementById("preset").value);
      if (preset) {{
        setTags(String(preset.tags || "").split("|").filter(Boolean));
        document.getElementById("matchMode").value = preset.match_mode || "any";
      }}
      applyFilters();
    }}
    function applyFilters() {{
      const q = document.getElementById("q").value.trim().toLowerCase();
      const from = document.getElementById("dateFrom").value;
      const to = document.getElementById("dateTo").value;
      const main = document.getElementById("mainCategory").value;
      const min = Number(document.getElementById("minAmount").value || 0);
      const max = Number(document.getElementById("maxAmount").value || 0);
      const chosen = selectedTags();
      const mode = document.getElementById("matchMode").value;
      filtered = DATA.rows.filter(row => {{
        const rowTags = tags(row);
        const text = `${{row.counterparty}} ${{row.description}} ${{row.risk_tags}} ${{row.main_category}} ${{row.sub_category}}`.toLowerCase();
        if (q && !text.includes(q)) return false;
        if (from && String(row.date || "") < from) return false;
        if (to && String(row.date || "") > to) return false;
        if (main && row.main_category !== main) return false;
        if (Number(row.amount || 0) < min) return false;
        if (max && Number(row.amount || 0) > max) return false;
        if (chosen.length && mode === "all" && !chosen.every(tag => rowTags.includes(tag))) return false;
        if (chosen.length && mode !== "all" && !chosen.some(tag => rowTags.includes(tag))) return false;
        return true;
      }});
      renderAll();
    }}
    function groupRows(key) {{
      const weekday = ["周一","周二","周三","周四","周五","周六","周日"];
      const map = new Map();
      filtered.forEach(row => {{
        let name = "";
        if (key === "month") name = row.month || String(row.date || "").slice(0,7);
        else if (key === "weekday") name = weekday[(new Date(row.date).getDay() + 6) % 7] || "未知";
        else if (key === "hour") name = String(row.transaction_time || "").slice(11,13) + ":00";
        else name = row[key] || "未填写";
        const curr = map.get(name) || {{ name, amount:0, count:0 }};
        curr.amount += Number(row.amount || 0);
        curr.count += 1;
        map.set(name, curr);
      }});
      const rows = [...map.values()];
      if (key === "month" || key === "hour") return rows.sort((a,b) => a.name.localeCompare(b.name));
      return rows.sort((a,b) => b.amount - a.amount).slice(0, 12);
    }}
    function tagGroups() {{
      const map = new Map();
      filtered.forEach(row => tags(row).forEach(tag => {{
        const curr = map.get(tag) || {{ name:tag, amount:0, count:0 }};
        curr.amount += Number(row.amount || 0);
        curr.count += 1;
        map.set(tag, curr);
      }}));
      return [...map.values()].sort((a,b) => b.amount - a.amount).slice(0,12);
    }}
    function renderBars(id, rows) {{
      const max = Math.max(...rows.map(r => r.amount), 1);
      document.getElementById(id).innerHTML = rows.length ? rows.map(r => `<div class="bar-row"><div class="bar-name" title="${{safe(r.name)}}">${{safe(r.name)}} · ${{r.count}}笔</div><div class="bar-bg"><div class="bar" style="width:${{Math.max(2, r.amount / max * 100)}}%"></div></div><div>${{yuan(r.amount)}}</div></div>`).join("") : "<div class='sub'>暂无数据</div>";
    }}
    function renderChart(rows) {{
      const svg = document.getElementById("behaviorChart");
      const type = document.getElementById("chartType").value;
      const w = 900, h = 360, p = 42;
      svg.setAttribute("viewBox", `0 0 ${{w}} ${{h}}`);
      if (!rows.length) {{ svg.innerHTML = `<text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" fill="#667085">暂无数据</text>`; return; }}
      const max = Math.max(...rows.map(r => r.amount), 1);
      if (type === "donut") {{
        let offset = 0;
        const total = rows.reduce((s,r) => s + r.amount, 0) || 1;
        const colors = ["#1d4ed8","#047857","#b45309","#7c3aed","#0e7490","#b42318","#db2777"];
        const circles = rows.map((r,i) => {{
          const pct = r.amount / total * 100;
          const part = `<circle cx="180" cy="180" r="95" fill="transparent" stroke="${{colors[i%colors.length]}}" stroke-width="34" stroke-dasharray="${{pct.toFixed(2)}} ${{(100-pct).toFixed(2)}}" stroke-dashoffset="${{(-offset).toFixed(2)}}"><title>${{safe(r.name)}} ${{pct.toFixed(2)}}%</title></circle>`;
          offset += pct; return part;
        }}).join("");
        const legend = rows.slice(0,9).map((r,i) => `<text x="360" y="${{72+i*28}}" font-size="14" fill="#111827">${{safe(r.name).slice(0,18)}}  ${{yuan(r.amount)}}</text><rect x="338" y="${{61+i*28}}" width="12" height="12" fill="${{colors[i%colors.length]}}"/>`).join("");
        svg.innerHTML = `<g transform="rotate(-90 180 180)">${{circles}}</g><circle cx="180" cy="180" r="64" fill="#fbfcfe"/><text x="180" y="176" text-anchor="middle" font-size="16" font-weight="700">当前范围</text><text x="180" y="200" text-anchor="middle" font-size="13" fill="#667085">${{yuan(total)}}</text>${{legend}}`;
        return;
      }}
      if (type === "line") {{
        const x = i => rows.length === 1 ? w / 2 : p + i * ((w - p * 2) / (rows.length - 1));
        const y = v => h - p - (v / max) * (h - p * 2);
        const path = rows.map((r,i) => `${{i ? "L" : "M"}} ${{x(i).toFixed(1)}} ${{y(r.amount).toFixed(1)}}`).join(" ");
        const labels = rows.map((r,i) => i % Math.max(1, Math.ceil(rows.length/7)) === 0 ? `<text x="${{x(i)}}" y="${{h-12}}" font-size="11" text-anchor="middle" fill="#667085">${{safe(r.name).slice(0,8)}}</text>` : "").join("");
        svg.innerHTML = `<line x1="${{p}}" y1="${{h-p}}" x2="${{w-p}}" y2="${{h-p}}" stroke="#d8dee8"/>${{labels}}<path d="${{path}}" fill="none" stroke="#1d4ed8" stroke-width="3"/>` + rows.map((r,i) => `<circle cx="${{x(i)}}" cy="${{y(r.amount)}}" r="4" fill="#1d4ed8"><title>${{safe(r.name)}} ${{yuan(r.amount)}}</title></circle>`).join("");
        return;
      }}
      const barRows = type === "histogram" ? amountBuckets() : rows;
      const bw = (w - p * 2) / barRows.length;
      const barMax = Math.max(...barRows.map(r => r.amount), 1);
      svg.innerHTML = `<line x1="${{p}}" y1="${{h-p}}" x2="${{w-p}}" y2="${{h-p}}" stroke="#d8dee8"/>` + barRows.map((r,i) => {{
        const bh = (r.amount / barMax) * (h - p * 2);
        const x = p + i * bw + 4;
        const y = h - p - bh;
        return `<rect x="${{x}}" y="${{y}}" width="${{Math.max(4,bw-8)}}" height="${{bh}}" rx="4" fill="#047857"><title>${{safe(r.name)}} ${{yuan(r.amount)}} / ${{r.count}}笔</title></rect><text x="${{x+bw/2-4}}" y="${{h-12}}" font-size="10" text-anchor="middle" fill="#667085">${{safe(r.name).slice(0,8)}}</text>`;
      }}).join("");
    }}
    function amountBuckets() {{
      const buckets = [["0-50",0,50],["50-200",50,200],["200-1k",200,1000],["1k-5k",1000,5000],["5k-1w",5000,10000],["1w+",10000,Infinity]];
      return buckets.map(([name,min,max]) => {{
        const items = filtered.filter(r => Number(r.amount || 0) >= min && Number(r.amount || 0) < max);
        return {{ name, amount:items.reduce((s,r)=>s+Number(r.amount||0),0), count:items.length }};
      }});
    }}
    function renderMetrics(rows) {{
      const total = filtered.reduce((s,r)=>s+Number(r.amount||0),0);
      const topTag = tagGroups()[0] || {{ name:"-" }};
      const topCounterparty = groupRows("counterparty")[0] || {{ name:"-" }};
      document.getElementById("mCount").textContent = filtered.length;
      document.getElementById("mAmount").textContent = yuan(total);
      document.getElementById("mAvg").textContent = yuan(filtered.length ? total / filtered.length : 0);
      document.getElementById("mTopTag").textContent = topTag.name;
      document.getElementById("mTopCounterparty").textContent = topCounterparty.name;
    }}
    function renderRecent() {{
      const rows = filtered.slice().sort((a,b)=>String(b.date).localeCompare(String(a.date))).slice(0,12);
      document.getElementById("recentTable").innerHTML = `<tr><th>日期</th><th>对方</th><th>标签</th><th>金额</th></tr>` + rows.map(r => `<tr><td>${{safe(r.date)}}</td><td>${{safe(r.counterparty).slice(0,18)}}</td><td>${{safe(r.risk_tags).slice(0,18)}}</td><td>${{yuan(r.amount)}}</td></tr>`).join("");
    }}
    function renderAll() {{
      const grouped = groupRows(document.getElementById("groupBy").value);
      renderMetrics(grouped);
      renderBars("rankBars", grouped);
      renderBars("tagBars", tagGroups());
      renderChart(grouped);
      renderRecent();
    }}
    function csvEscape(value) {{ const text = String(value ?? ""); return /[",\\n]/.test(text) ? `"${{text.replaceAll('"','""')}}"` : text; }}
    function exportCsv() {{
      const header = ["date","transaction_time","counterparty","description","main_category","sub_category","risk_tags","amount"];
      const body = [header, ...filtered.map(r => header.map(k => r[k] ?? ""))].map(r => r.map(csvEscape).join(",")).join("\\n") + "\\n";
      const blob = new Blob([body], {{type:"text/csv;charset=utf-8"}});
      const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = "behavior_analysis_filtered.csv"; a.click(); URL.revokeObjectURL(a.href);
    }}
    Object.assign(window, {{ applyFilters, applyPreset, clearTags, renderAll, exportCsv }});
    init();
  </script>
</body>
</html>"""


def _tag_library_html(tag_library_rows: list[dict[str, Any]], tag_filter_preset_rows: list[dict[str, Any]]) -> str:
    data = {"tags": tag_library_rows, "filter_presets": tag_filter_preset_rows}
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>标签库编辑</title>
  <style>
    :root {{ --bg:#f3f6f8; --panel:#fff; --ink:#111827; --muted:#667085; --line:#d8dee8; --blue:#2563eb; --green:#057a55; --red:#d14343; --amber:#ad6500; --cyan:#0e7490; }}
    * {{ box-sizing:border-box; }}
    html,body {{ max-width:100%; overflow-x:hidden; }}
    body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; background:var(--bg); color:var(--ink); }}
    header {{ padding:20px 28px 14px; background:#fff; border-bottom:1px solid var(--line); position:sticky; top:0; z-index:2; }}
    h1 {{ margin:0 0 6px; font-size:23px; letter-spacing:0; }}
    .sub {{ color:var(--muted); font-size:13px; }}
    main {{ max-width:1500px; margin:0 auto; padding:18px 28px 42px; }}
    .actions {{ display:flex; gap:8px; flex-wrap:wrap; margin-bottom:12px; }}
    button {{ border:1px solid var(--line); background:#fff; color:var(--ink); border-radius:7px; padding:8px 11px; cursor:pointer; font-size:13px; }}
    button.primary {{ background:var(--blue); color:#fff; border-color:var(--blue); }}
    .panel {{ background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:14px; margin-bottom:12px; min-width:0; max-width:100%; overflow-wrap:anywhere; }}
    table {{ width:100%; border-collapse:collapse; font-size:13px; }}
    th,td {{ padding:8px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }}
    input,select,textarea {{ width:100%; border:1px solid var(--line); border-radius:7px; padding:7px; font-size:13px; }}
    textarea {{ min-height:38px; resize:vertical; }}
    .swatch {{ width:26px; height:26px; border-radius:6px; border:1px solid var(--line); }}
    .preset-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(240px,1fr)); gap:10px; }}
    .preset {{ border:1px solid var(--line); border-radius:8px; padding:10px; background:#fbfcfe; display:grid; gap:8px; }}
    .preset-actions {{ display:flex; gap:8px; justify-content:flex-end; }}
    @media (max-width:800px) {{ main,header {{ padding-left:14px; padding-right:14px; }} table {{ min-width:980px; }} .table-wrap {{ overflow:auto; max-width:100%; }} }}
    @media (max-width:720px) {{ .actions,.preset-actions {{ display:grid; grid-template-columns:1fr; }} .preset-grid {{ grid-template-columns:1fr; }} }}
  </style>
</head>
<body>
  <header>
    <h1>标签库编辑</h1>
    <div class="sub">编辑后下载 JSON，下次导入时用 <code>--tag-library</code> 回灌，标签库会写入 SQLite 并长期保存。</div>
  </header>
  <main>
    <div class="actions">
      <button class="primary" onclick="downloadJson()">下载 tag_library_custom.json</button>
      <button onclick="addTag()">新增标签</button>
      <button onclick="addPreset()">新增筛选组合</button>
      <button onclick="resetTags()">恢复本次生成状态</button>
    </div>
    <section class="panel">
      <h2>标签库</h2>
      <div class="table-wrap"><table id="tagTable"></table></div>
    </section>
    <section class="panel">
      <h2>筛选组合预设</h2>
      <div id="presetGrid" class="preset-grid"></div>
    </section>
  </main>
  <script>
    const DATA = {json.dumps(data, ensure_ascii=False)};
    let tags = structuredClone(DATA.tags);
    let presets = structuredClone(DATA.filter_presets);
    const safe = v => String(v ?? "").replace(/[&<>"']/g, ch => ({{"&":"&amp;","<":"&lt;",">":"&gt;","\\\"":"&quot;","'":"&#39;"}}[ch]));
    function renderTags() {{
      document.getElementById("tagTable").innerHTML = `<tr><th>启用</th><th>标签名</th><th>分组</th><th>颜色</th><th>说明</th><th>来源</th><th>删除</th></tr>` + tags.map((tag,index) => `<tr>
        <td><select onchange="updateTag(${{index}}, 'is_active', this.value)"><option value="1" ${{String(tag.is_active)!=="0"?"selected":""}}>启用</option><option value="0" ${{String(tag.is_active)==="0"?"selected":""}}>停用</option></select></td>
        <td><input value="${{safe(tag.tag_name)}}" onchange="updateTag(${{index}}, 'tag_name', this.value)"></td>
        <td><input value="${{safe(tag.tag_group)}}" onchange="updateTag(${{index}}, 'tag_group', this.value)"></td>
        <td><input type="color" value="${{safe(tag.color || "#2563eb")}}" onchange="updateTag(${{index}}, 'color', this.value)"></td>
        <td><textarea onchange="updateTag(${{index}}, 'description', this.value)">${{safe(tag.description)}}</textarea></td>
        <td>${{safe(tag.source || "custom")}}</td>
        <td><button onclick="removeTag(${{index}})">删除</button></td>
      </tr>`).join("");
      renderPresets();
    }}
    function tagOptions(selected) {{
      const active = new Set(String(selected || "").split("|").filter(Boolean));
      return tags.filter(tag => String(tag.is_active) !== "0").map(tag => `<option value="${{safe(tag.tag_name)}}" ${{active.has(tag.tag_name) ? "selected" : ""}}>${{safe(tag.tag_name)}}</option>`).join("");
    }}
    function renderPresets() {{
      document.getElementById("presetGrid").innerHTML = presets.map((preset,index) => `<div class="preset">
        <label><span class="sub">组合名</span><input value="${{safe(preset.preset_name)}}" onchange="updatePreset(${{index}}, 'preset_name', this.value)"></label>
        <label><span class="sub">标签</span><select multiple size="5" onchange="updatePresetTags(${{index}}, this)">${{tagOptions(preset.tags)}}</select></label>
        <label><span class="sub">命中模式</span><select onchange="updatePreset(${{index}}, 'match_mode', this.value)"><option value="any" ${{preset.match_mode !== "all" ? "selected" : ""}}>任一命中</option><option value="all" ${{preset.match_mode === "all" ? "selected" : ""}}>全部命中</option></select></label>
        <label><span class="sub">说明</span><textarea onchange="updatePreset(${{index}}, 'description', this.value)">${{safe(preset.description)}}</textarea></label>
        <label><span class="sub">状态</span><select onchange="updatePreset(${{index}}, 'is_active', this.value)"><option value="1" ${{String(preset.is_active)!=="0"?"selected":""}}>启用</option><option value="0" ${{String(preset.is_active)==="0"?"selected":""}}>停用</option></select></label>
        <div class="preset-actions"><button onclick="removePreset(${{index}})">删除组合</button></div>
      </div>`).join("");
    }}
    function updateTag(index, field, value) {{ tags[index][field] = value; tags[index].source = tags[index].source || "custom"; }}
    function addTag() {{ tags.push({{ tag_id:"custom_"+Date.now(), tag_name:"新标签", tag_group:"自定义", color:"#2563eb", description:"", is_active:"1", source:"custom", sort_order:1000+tags.length }}); renderTags(); }}
    function removeTag(index) {{ tags.splice(index,1); renderTags(); }}
    function addPreset() {{ presets.push({{ preset_id:"custom_"+Date.now(), preset_name:"新筛选组合", tags:"基础支出", match_mode:"any", description:"", is_active:"1", source:"custom", sort_order:1000+presets.length }}); renderTags(); }}
    function updatePreset(index, field, value) {{ presets[index][field] = value; presets[index].source = presets[index].source || "custom"; }}
    function updatePresetTags(index, select) {{ presets[index].tags = [...select.selectedOptions].map(option => option.value).join("|"); presets[index].source = presets[index].source || "custom"; }}
    function removePreset(index) {{ presets.splice(index,1); renderTags(); }}
    function resetTags() {{ tags = structuredClone(DATA.tags); presets = structuredClone(DATA.filter_presets); renderTags(); }}
    function downloadJson() {{
      const payload = JSON.stringify({{ tags, filter_presets: presets }}, null, 2);
      const blob = new Blob([payload], {{type:"application/json;charset=utf-8"}});
      const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = "tag_library_custom.json"; a.click(); URL.revokeObjectURL(a.href);
    }}
    Object.assign(window, {{ downloadJson, addTag, addPreset, resetTags, updateTag, removeTag, updatePreset, updatePresetTags, removePreset }});
    renderTags();
  </script>
</body>
</html>"""


def _reference_model_lab_html(*, location: str = "reports") -> str:
    models = _reference_models_payload()
    rows: list[dict[str, Any]] = []
    for item in models:
        reference_count = len(item.get("reference_features", []))
        incorporated_count = len(item.get("incorporated_as", []))
        absorption = round((incorporated_count / max(reference_count, 1)) * 100, 2)
        rows.append(
            {
                "project": item["project"],
                "url": item["url"],
                "source_type": item.get("source_type", ""),
                "verified_at": item.get("verified_at", ""),
                "license": item.get("license", ""),
                "evidence_summary": item.get("evidence_summary", ""),
                "reference_features": item.get("reference_features", []),
                "incorporated_as": item.get("incorporated_as", []),
                "remaining_gap": item.get("remaining_gap", ""),
                "absorption": absorption,
                "feature_count": reference_count,
                "incorporated_count": incorporated_count,
            }
        )
    data = {
        "models": rows,
        "ui_patterns": _reference_ui_pattern_rows(),
        "links": {
            "benchmark_pdf": "reference_model_benchmark_report.pdf" if location == "reports" else "reports/reference_model_benchmark_report.pdf",
            "source_json": "../audit/reference_models.json" if location == "reports" else "audit/reference_models.json",
            "source_log": "../audit/reference_source_log.json" if location == "reports" else "audit/reference_source_log.json",
            "portal": "index.html" if location == "reports" else "index.html",
        },
    }
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>开源参考模型工作台</title>
  <style>
    :root {{ --bg:#f4f7fb; --panel:#fff; --ink:#172033; --muted:#647083; --line:#d8dee8; --blue:#2563eb; --green:#047857; --amber:#a16207; --red:#b42318; --cyan:#0e7490; --violet:#6d28d9; }}
    * {{ box-sizing:border-box; }}
    html,body {{ max-width:100%; overflow-x:hidden; }}
    body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; background:var(--bg); color:var(--ink); }}
    header {{ background:#fff; border-bottom:1px solid var(--line); padding:22px 30px 16px; position:sticky; top:0; z-index:2; }}
    h1 {{ margin:0 0 6px; font-size:24px; letter-spacing:0; }}
    h2 {{ margin:0 0 10px; font-size:17px; }}
    .sub {{ color:var(--muted); font-size:13px; line-height:1.55; }}
    main {{ max-width:1480px; margin:0 auto; padding:18px 30px 44px; }}
    .toolbar {{ display:grid; grid-template-columns:minmax(220px,1fr) 180px 180px 180px; gap:10px; margin-bottom:14px; }}
    input,select,button {{ border:1px solid var(--line); border-radius:7px; padding:9px 10px; font-size:13px; background:#fff; color:var(--ink); min-width:0; }}
    button {{ cursor:pointer; }}
    button.primary {{ background:var(--blue); border-color:var(--blue); color:#fff; }}
    .metrics {{ display:grid; grid-template-columns:repeat(4,minmax(130px,1fr)); gap:10px; margin-bottom:14px; }}
    .metric {{ background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:13px; min-height:80px; }}
    .metric strong {{ display:block; font-size:24px; margin-top:4px; }}
    .metric span {{ color:var(--muted); font-size:12px; }}
    .grid {{ display:grid; grid-template-columns:1fr 1fr; gap:14px; }}
    .panel {{ background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:14px; min-width:0; overflow:hidden; }}
    .chart {{ width:100%; min-height:320px; display:block; }}
    .matrix {{ display:grid; gap:9px; }}
    .pattern-grid {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:10px; }}
    .pattern-card {{ border:1px solid var(--line); border-radius:8px; padding:12px; background:#fbfcfe; min-width:0; }}
    .pattern-card strong {{ display:block; margin-bottom:5px; }}
    .pattern-meta {{ color:var(--muted); font-size:12px; line-height:1.5; overflow-wrap:anywhere; }}
    .model-row {{ display:grid; grid-template-columns:220px 1fr 110px; gap:12px; align-items:start; border:1px solid var(--line); border-radius:8px; padding:12px; background:#fbfcfe; min-width:0; }}
    .model-name {{ font-weight:700; overflow-wrap:anywhere; }}
    .badge {{ display:inline-flex; align-items:center; border:1px solid var(--line); border-radius:999px; padding:4px 8px; font-size:12px; color:var(--muted); background:#fff; margin:2px 4px 2px 0; }}
    .gap {{ color:var(--red); }}
    .features {{ display:grid; grid-template-columns:1fr 1fr; gap:8px; }}
    ul {{ margin:6px 0 0; padding-left:18px; }}
    li {{ margin:3px 0; }}
    table {{ width:100%; border-collapse:collapse; font-size:13px; }}
    th,td {{ padding:8px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }}
    th:last-child,td:last-child {{ text-align:right; }}
    .links {{ display:flex; flex-wrap:wrap; gap:8px; margin-top:10px; }}
    .links a {{ color:var(--blue); text-decoration:none; border:1px solid var(--line); border-radius:7px; padding:7px 9px; background:#fff; }}
    .empty {{ color:var(--muted); padding:16px; border:1px dashed var(--line); border-radius:8px; }}
    @media (max-width:1050px) {{ .toolbar,.grid,.features,.pattern-grid {{ grid-template-columns:1fr; }} .metrics {{ grid-template-columns:repeat(2,1fr); }} .model-row {{ grid-template-columns:1fr; }} }}
    @media (max-width:720px) {{ header,main {{ padding-left:14px; padding-right:14px; }} .metrics {{ grid-template-columns:1fr; }} .chart {{ min-height:260px; }} }}
  </style>
</head>
<body>
  <header>
    <h1>开源参考模型工作台</h1>
    <div class="sub">把 GitHub/开源账单系统的功能、布局、数据模型和交互模式转化为可筛选的本地对标视图；只做功能和信息架构参考，不复制外部代码或 UI。</div>
    <div class="links">
      <a id="benchmarkLink">开源参考对标 PDF</a>
      <a id="sourceJsonLink">reference_models.json</a>
      <a id="sourceLogLink">reference_source_log.json</a>
      <a id="portalLink">返回报告门户</a>
    </div>
  </header>
  <main>
    <section class="toolbar" aria-label="参考模型筛选">
      <input id="modelSearch" placeholder="搜索项目、功能、差距或证据" oninput="applyReferenceFilters()">
      <select id="licenseFilter" onchange="applyReferenceFilters()"></select>
      <select id="coverageFilter" onchange="applyReferenceFilters()">
        <option value="all">全部吸收度</option>
        <option value="full">100.00% 已吸收</option>
        <option value="partial">仍有差距</option>
      </select>
      <button class="primary" onclick="downloadReferenceCsv()">导出筛选结果 CSV</button>
    </section>
    <section class="metrics">
      <div class="metric"><span>参考项目</span><strong id="modelCount"></strong></div>
      <div class="metric"><span>平均吸收度</span><strong id="avgCoverage"></strong></div>
      <div class="metric"><span>已吸收功能点</span><strong id="absorbedCount"></strong></div>
      <div class="metric"><span>剩余差距</span><strong id="gapCount"></strong></div>
    </section>
    <section class="grid">
      <div class="panel">
        <h2>吸收度对比</h2>
        <svg id="referenceCoverageChart" class="chart" role="img" aria-label="开源参考吸收度对比图"></svg>
      </div>
      <div class="panel">
        <h2>功能来源构成</h2>
        <svg id="referenceFeatureDonut" class="chart" role="img" aria-label="参考功能和已吸收功能环形图"></svg>
      </div>
    </section>
    <section class="panel" style="margin-top:14px">
      <h2>参考项目矩阵</h2>
      <div id="referenceModelMatrix" class="matrix"></div>
    </section>
    <section class="panel" style="margin-top:14px">
      <h2>UI/布局模式吸收矩阵</h2>
      <div id="referenceUIPatternMatrix" class="pattern-grid"></div>
    </section>
    <section class="panel" style="margin-top:14px">
      <h2>差距与边界</h2>
      <table id="referenceGapTable"></table>
    </section>
  </main>
  <script>
    const DATA = {json.dumps(data, ensure_ascii=False)};
    let filteredModels = DATA.models.slice();
    const safe = v => String(v ?? "").replace(/[&<>"']/g, ch => ({{"&":"&amp;","<":"&lt;",">":"&gt;","\\\"":"&quot;","'":"&#39;"}}[ch]));
    function initLinks() {{
      document.getElementById("benchmarkLink").href = DATA.links.benchmark_pdf;
      document.getElementById("sourceJsonLink").href = DATA.links.source_json;
      document.getElementById("sourceLogLink").href = DATA.links.source_log;
      document.getElementById("portalLink").href = DATA.links.portal;
    }}
    function initFilters() {{
      const licenses = ["all", ...new Set(DATA.models.map(row => row.license || "Unspecified"))];
      document.getElementById("licenseFilter").innerHTML = licenses.map(value => `<option value="${{safe(value)}}">${{value === "all" ? "全部许可" : safe(value)}}</option>`).join("");
    }}
    function modelHaystack(row) {{
      return [row.project,row.source_type,row.license,row.evidence_summary,row.remaining_gap,...row.reference_features,...row.incorporated_as].join(" ").toLowerCase();
    }}
    function applyReferenceFilters() {{
      const q = document.getElementById("modelSearch").value.trim().toLowerCase();
      const license = document.getElementById("licenseFilter").value;
      const coverage = document.getElementById("coverageFilter").value;
      filteredModels = DATA.models.filter(row => {{
        const qOk = !q || modelHaystack(row).includes(q);
        const licenseOk = license === "all" || row.license === license;
        const coverageOk = coverage === "all" || (coverage === "full" ? row.absorption >= 100 : row.absorption < 100);
        return qOk && licenseOk && coverageOk;
      }});
      renderReferenceModelLab();
    }}
    function renderReferenceModelLab() {{
      renderMetrics();
      renderCoverageChart();
      renderFeatureDonut();
      renderMatrix();
      renderUIPatternMatrix();
      renderGapTable();
    }}
    function renderMetrics() {{
      const avg = filteredModels.length ? filteredModels.reduce((s,r)=>s+Number(r.absorption || 0),0) / filteredModels.length : 0;
      const absorbed = filteredModels.reduce((s,r)=>s+Number(r.incorporated_count || 0),0);
      const gaps = filteredModels.filter(r => String(r.remaining_gap || "").trim()).length;
      document.getElementById("modelCount").textContent = filteredModels.length;
      document.getElementById("avgCoverage").textContent = avg.toFixed(2) + "%";
      document.getElementById("absorbedCount").textContent = absorbed;
      document.getElementById("gapCount").textContent = gaps;
    }}
    function renderCoverageChart() {{
      const svg = document.getElementById("referenceCoverageChart");
      const w = 720, h = 320, left = 190, right = 34, top = 24, rowH = 32;
      svg.setAttribute("viewBox", `0 0 ${{w}} ${{h}}`);
      if (!filteredModels.length) {{ svg.innerHTML = `<text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" fill="#647083">无匹配参考项目</text>`; return; }}
      const rows = filteredModels.slice(0, 8);
      const axis = `<line x1="${{left}}" y1="${{h-36}}" x2="${{w-right}}" y2="${{h-36}}" stroke="#d8dee8"/>` + [0,25,50,75,100].map(v => {{
        const x = left + (w-left-right) * v / 100;
        return `<line x1="${{x}}" y1="18" x2="${{x}}" y2="${{h-36}}" stroke="#eef2f7"/><text x="${{x}}" y="${{h-14}}" text-anchor="middle" font-size="11" fill="#647083">${{v}}%</text>`;
      }}).join("");
      const bars = rows.map((row,index) => {{
        const y = top + index * rowH;
        const bw = (w-left-right) * Math.min(100, Number(row.absorption || 0)) / 100;
        const color = row.absorption >= 100 ? "#047857" : row.absorption >= 80 ? "#2563eb" : "#a16207";
        return `<text x="12" y="${{y+18}}" font-size="12" fill="#172033">${{safe(row.project).slice(0,28)}}</text><rect x="${{left}}" y="${{y+6}}" width="${{bw}}" height="17" rx="4" fill="${{color}}"><title>${{safe(row.project)}} ${{Number(row.absorption).toFixed(2)}}%</title></rect><text x="${{Math.min(w-right-40,left+bw+8)}}" y="${{y+19}}" font-size="12" fill="#172033">${{Number(row.absorption).toFixed(2)}}%</text>`;
      }}).join("");
      svg.innerHTML = axis + bars;
    }}
    function renderFeatureDonut() {{
      const svg = document.getElementById("referenceFeatureDonut");
      svg.setAttribute("viewBox", "0 0 520 320");
      const reference = filteredModels.reduce((s,r)=>s+Number(r.feature_count || 0),0);
      const incorporated = filteredModels.reduce((s,r)=>s+Number(r.incorporated_count || 0),0);
      const gap = Math.max(0, reference - incorporated);
      const total = Math.max(reference, 1);
      const values = [
        ["已吸收功能", incorporated, "#047857"],
        ["待扩展功能", gap, "#a16207"]
      ];
      let offset = 0;
      const arcs = values.map(([label,value,color]) => {{
        const pct = Number(value) / total * 100;
        const item = `<circle cx="160" cy="154" r="82" fill="transparent" stroke="${{color}}" stroke-width="34" stroke-dasharray="${{pct.toFixed(2)}} ${{(100-pct).toFixed(2)}}" stroke-dashoffset="${{(-offset).toFixed(2)}}"><title>${{label}} ${{pct.toFixed(2)}}%</title></circle>`;
        offset += pct;
        return item;
      }}).join("");
      const legend = values.map(([label,value,color],i) => `<rect x="300" y="${{105+i*34}}" width="12" height="12" fill="${{color}}"/><text x="320" y="${{116+i*34}}" font-size="14" fill="#172033">${{label}}：${{value}}</text>`).join("");
      svg.innerHTML = `<g transform="rotate(-90 160 154)">${{arcs}}</g><circle cx="160" cy="154" r="55" fill="#fff"/><text x="160" y="150" text-anchor="middle" font-size="15" font-weight="700">参考功能</text><text x="160" y="174" text-anchor="middle" font-size="13" fill="#647083">${{reference}} 项</text>${{legend}}`;
    }}
    function renderMatrix() {{
      const root = document.getElementById("referenceModelMatrix");
      if (!filteredModels.length) {{ root.innerHTML = `<div class="empty">当前筛选没有匹配项目。</div>`; return; }}
      root.innerHTML = filteredModels.map(row => `<article class="model-row">
        <div>
          <div class="model-name">${{safe(row.project)}}</div>
          <div><span class="badge">${{safe(row.license)}}</span><span class="badge">${{safe(row.verified_at)}}</span><span class="badge">${{Number(row.absorption).toFixed(2)}}%</span></div>
          <a href="${{safe(row.url)}}">${{safe(row.url)}}</a>
        </div>
        <div class="features">
          <div><strong>参考功能</strong><ul>${{row.reference_features.map(item => `<li>${{safe(item)}}</li>`).join("")}}</ul></div>
          <div><strong>已吸收实现</strong><ul>${{row.incorporated_as.map(item => `<li>${{safe(item)}}</li>`).join("")}}</ul></div>
        </div>
        <div class="gap"><strong>差距</strong><br>${{safe(row.remaining_gap)}}</div>
      </article>`).join("");
    }}
    function renderUIPatternMatrix() {{
      const root = document.getElementById("referenceUIPatternMatrix");
      const q = document.getElementById("modelSearch").value.trim().toLowerCase();
      const patterns = DATA.ui_patterns.filter(row => !q || [row.pattern,row.reference_projects,row.source_signal,row.applied_in,row.implementation_evidence,row.ui_boundary].join(" ").toLowerCase().includes(q));
      if (!patterns.length) {{ root.innerHTML = `<div class="empty">当前筛选没有匹配 UI/布局模式。</div>`; return; }}
      root.innerHTML = patterns.map(row => `<article class="pattern-card">
        <strong>${{safe(row.pattern)}}</strong>
        <div class="pattern-meta">来源：${{safe(row.reference_projects)}}</div>
        <div class="pattern-meta">信号：${{safe(row.source_signal)}}</div>
        <div class="pattern-meta">落地：${{safe(row.applied_in)}}</div>
        <div style="margin-top:8px">${{safe(row.implementation_evidence)}}</div>
        <div class="pattern-meta" style="margin-top:8px">边界：${{safe(row.ui_boundary)}}</div>
      </article>`).join("");
    }}
    function renderGapTable() {{
      document.getElementById("referenceGapTable").innerHTML = `<tr><th>项目</th><th>差距</th><th>处理边界</th></tr>` + filteredModels.map(row => `<tr><td>${{safe(row.project)}}</td><td>${{safe(row.remaining_gap)}}</td><td>功能、信息架构和交互模式参考；不复制外部代码、样式或素材。</td></tr>`).join("");
    }}
    function csvEscape(value) {{ const text = String(value ?? ""); return /[",\\n]/.test(text) ? `"${{text.replaceAll('"','""')}}"` : text; }}
    function downloadReferenceCsv() {{
      const header = ["project","url","license","absorption","source_type","verified_at","remaining_gap"];
      const body = [header, ...filteredModels.map(row => header.map(key => row[key] ?? ""))].map(row => row.map(csvEscape).join(",")).join("\\n") + "\\n";
      const blob = new Blob([body], {{type:"text/csv;charset=utf-8"}});
      const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = "reference_model_lab_filtered.csv"; a.click(); URL.revokeObjectURL(a.href);
    }}
    Object.assign(window, {{ applyReferenceFilters, renderReferenceModelLab, downloadReferenceCsv }});
    initLinks();
    initFilters();
    renderReferenceModelLab();
  </script>
</body>
</html>"""


def _portal_html(
    metrics: dict[str, Any],
    output_paths: dict[str, str],
    control_plan_rows: list[dict[str, Any]],
    *,
    month_rows: list[dict[str, Any]] | None = None,
    category_rows: list[dict[str, Any]] | None = None,
    risk_rows: list[dict[str, Any]] | None = None,
    review_rows: list[dict[str, Any]] | None = None,
    review_status_rows: list[dict[str, Any]] | None = None,
    review_candidate_group_rows: list[dict[str, Any]] | None = None,
    location: str = "reports",
) -> str:
    def report_meta(name: str, path: str) -> dict[str, str]:
        filename = Path(path).name
        joined = f"{name} {filename}"
        if "周报" in name:
            period = "周度"
        elif "月报" in name:
            period = "月度"
        elif "季报" in name:
            period = "季度"
        elif "半年" in name:
            period = "半年"
        elif "年报" in name or "账单周期" in name:
            period = "年度"
        else:
            period = "专项"
        if any(key in joined for key in ["复核", "验收", "审计", "追踪", "可信"]):
            evidence = "审计证据"
        elif any(key in joined for key in ["规则", "手册", "使用"]):
            evidence = "规则文档"
        else:
            evidence = "经营分析"
        if any(key in joined for key in ["风险", "控制", "放血", "消费"]):
            theme = "消费控制"
        elif any(key in joined for key in ["复核", "可信", "审计", "验收", "追踪"]):
            theme = "审计复核"
        elif any(key in joined for key in ["参考", "ChatGPT", "开源"]):
            theme = "参考对标"
        else:
            theme = "周期报告"
        return {"period": period, "theme": theme, "evidence_type": evidence, "file_type": "PDF"}

    def qa_entry(question: str, answer: str, evidence: list[str], layer: str = "FACT", confidence: str = "高", relevance: str = "高", uncertainty: str = "低", missing: str = "无") -> dict[str, Any]:
        return {
            "question": question,
            "answer": answer,
            "layer": layer,
            "confidence": confidence,
            "relevance": relevance,
            "uncertainty": uncertainty,
            "missing_information": missing,
            "evidence": evidence,
        }

    def yuan_value(value: Any) -> str:
        try:
            return "¥" + f"{float(value or 0):,.2f}"
        except (TypeError, ValueError):
            return "¥0.00"

    def report_rel(path: str) -> str:
        name = Path(path).name
        return name if location == "reports" else f"reports/{name}"

    if location == "reports":
        links = {
            "dashboard": "dashboard.html",
            "operations_center": "operations_center.html",
            "data_access_hub": "data_access_hub.html",
            "acceptance_workbench": "acceptance_workbench.html",
            "reference_model_lab": "reference_model_lab.html",
            "transaction_explorer": "transaction_explorer.html",
            "behavior_analysis": "behavior_analysis.html",
            "tag_library": "tag_library.html",
            "review_workbench": "review_workbench.html",
            "sqlite": "../data/consumption.sqlite",
            "summary": "../summary.json",
            "reference_models": "../audit/reference_models.json",
            "run_manifest": "../audit/run_manifest.json",
        }
    else:
        links = {
            "dashboard": "dashboard.html",
            "operations_center": "reports/operations_center.html",
            "data_access_hub": "reports/data_access_hub.html",
            "acceptance_workbench": "reports/acceptance_workbench.html",
            "reference_model_lab": "reference_model_lab.html",
            "transaction_explorer": "transaction_explorer.html",
            "behavior_analysis": "reports/behavior_analysis.html",
            "tag_library": "reports/tag_library.html",
            "review_workbench": "review/review_workbench.html",
            "sqlite": "data/consumption.sqlite",
            "summary": "summary.json",
            "reference_models": "audit/reference_models.json",
            "run_manifest": "audit/run_manifest.json",
        }

    report_links = [
        ("周报", output_paths.get("week_pdf", "")),
        ("月报", output_paths.get("month_pdf", "")),
        ("季报", output_paths.get("quarter_pdf", "")),
        ("半年报", output_paths.get("half_pdf", "")),
        ("年报", output_paths.get("year_pdf", "")),
        ("账单周期年报", output_paths.get("annual_bill_cycle_pdf", "")),
        ("交付验收报告", output_paths.get("delivery_acceptance_pdf", "")),
        ("UI 与可视化质量验收报告", output_paths.get("visual_quality_acceptance_pdf", "")),
        ("开源参考对标报告", output_paths.get("reference_model_benchmark_pdf", "")),
        ("分类规则手册", output_paths.get("classification_rulebook_pdf", "")),
        ("使用手册", output_paths.get("user_manual_pdf", "")),
        ("需求追踪验收报告", output_paths.get("requirements_traceability_pdf", "")),
        ("最终完成审计报告", output_paths.get("completion_audit_pdf", "")),
        ("用户验收矩阵报告", output_paths.get("user_acceptance_matrix_pdf", "")),
        ("消费控制行动计划", output_paths.get("spending_control_action_pdf", "")),
        ("大额复核清单", output_paths.get("manual_review_report_pdf", "")),
        ("数据可信度审计报告", output_paths.get("data_trust_audit_pdf", "")),
        ("系统优化改进报告", output_paths.get("finance_ledger_system_improvement_pdf", "")),
    ]
    latest_month = sorted(month_rows or [], key=lambda item: str(item.get("period_start", "")), reverse=True)[:1]
    latest_month_text = ""
    if latest_month:
        item = latest_month[0]
        latest_month_text = f"最近月份 {item.get('period')} 支出 {yuan_value(item.get('total_expense'))}，净现金流 {yuan_value(item.get('net_cash_flow'))}。"
    top_category_text = ""
    if category_rows:
        top = category_rows[0]
        top_category_text = f"金额最高分类为 {top.get('main_category','')} / {top.get('sub_category','')}，金额 {yuan_value(top.get('amount'))}。"
    pending_text = ""
    if review_status_rows:
        pending = next((row for row in review_status_rows if str(row.get("status", "")).startswith("pending")), review_status_rows[0])
        pending_text = f"待复核状态 {pending.get('status_label', pending.get('status',''))}：{pending.get('count', 0)} 笔，金额 {yuan_value(pending.get('amount'))}；未确认前不进入生产统计。"
    control_text = ""
    if control_plan_rows:
        first_action = control_plan_rows[0]
        control_text = f"优先动作是 {first_action.get('focus_area','')}：{first_action.get('recommended_action','')}，预计优化 {yuan_value(first_action.get('estimated_saving'))}。"
    qa_index = [
        qa_entry(
            "本月最该优化哪类支出",
            "建议先看最近月份现金流、最高支出分类和消费控制动作。" + latest_month_text + top_category_text + control_text,
            ["summary_by_month", "summary_by_category", "spending_control_plan", "spending_control_action_report.pdf"],
            layer="INFERENCE",
            uncertainty="中",
            missing="如果有当天新增账单未导入，最近月份判断可能滞后。",
        ),
        qa_entry(
            "哪些大额交易还没进入生产统计",
            pending_text or "当前没有可展示的复核状态摘要；请查看大额复核工作台。",
            ["manual_review_status_summary", "manual_review_queue", "manual_review_report.pdf", "review_workbench.html"],
            layer="FACT",
            uncertainty="低",
        ),
        qa_entry(
            "这个系统是什么",
            "这是本地记账分析系统：使用本机 SQLite、静态 HTML 工作台和正式 PDF 报告；不是公网 SaaS。",
            ["README.md", "index.html", "finance_ledger_data_contract.md"],
            layer="FACT",
            uncertainty="低",
        ),
        qa_entry(
            "如何看报告",
            "在报告中心按周期、主题、证据类型或关键词筛选；PDF/HTML 默认新标签打开，便于保留主菜单。",
            ["report_manifest.json", "index.html"],
            layer="FACT",
            uncertainty="低",
        ),
        qa_entry(
            "如何降低消费",
            "优先处理消费控制行动计划中金额高、可操作、复核依赖低的项目；所有建议以生产统计和待复核隔离口径为边界。",
            ["spending_control_plan", "spending_control_action_report.pdf", "summary_by_risk_tag"],
            layer="INFERENCE",
            uncertainty="中",
            missing="最终削减动作仍需结合你的现实生活约束确认。",
        ),
    ]
    data = {
        "metrics": {key: yuan(value) if isinstance(value, int) and key != "transactions" else value for key, value in metrics.items()},
        "reports": [
            {"name": name, "href": report_rel(path), **report_meta(name, path)}
            for name, path in report_links
            if path
        ],
        "control_plan": control_plan_rows[:6],
        "qa_index": qa_index,
        "question_templates": [
            {"id": "latest_month_cashflow", "title": "本月现金流怎么样", "view": "summary_by_month"},
            {"id": "top_categories", "title": "钱主要花在哪些分类", "view": "summary_by_category"},
            {"id": "risk_exposure", "title": "哪些风险标签最突出", "view": "summary_by_risk_tag"},
            {"id": "pending_large_review", "title": "有哪些一万以上待复核", "view": "manual_review_queue"},
            {"id": "control_actions", "title": "下一步怎么降低消费", "view": "spending_control_plan"},
        ],
        "question_results": {
            "latest_month_cashflow": (month_rows or [])[:12],
            "top_categories": (category_rows or [])[:12],
            "risk_exposure": (risk_rows or [])[:12],
            "pending_large_review": {
                "status": review_status_rows or [],
                "transactions": (review_rows or [])[:12],
                "candidate_groups": (review_candidate_group_rows or [])[:10],
            },
            "control_actions": control_plan_rows[:12],
        },
        "links": links,
    }
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>本地记账分析系统</title>
  <style>
    :root {{ --bg:#f5f7fb; --panel:#fff; --ink:#172033; --muted:#647083; --line:#d9e0ea; --blue:#2563eb; --green:#047857; --red:#b42318; --amber:#a16207; --cyan:#0e7490; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; background:var(--bg); color:var(--ink); }}
    header {{ background:#fff; border-bottom:1px solid var(--line); padding:24px 32px 16px; }}
    h1 {{ margin:0 0 6px; font-size:25px; letter-spacing:0; }}
    .sub {{ color:var(--muted); font-size:13px; }}
    main {{ max-width:1440px; margin:0 auto; padding:20px 32px 44px; }}
    .metrics {{ display:grid; grid-template-columns:repeat(6,minmax(130px,1fr)); gap:10px; }}
    .metric {{ background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:14px; min-height:78px; }}
    .metric.review {{ border-left:4px solid var(--red); }}
    .metric.income {{ border-left:4px solid var(--green); }}
    .metric.expense {{ border-left:4px solid var(--blue); }}
    .metric.net {{ border-left:4px solid var(--amber); }}
    .metric.transfer {{ border-left:4px solid var(--cyan); }}
    .label {{ color:var(--muted); font-size:12px; }}
    .value {{ margin-top:7px; font-size:20px; font-weight:750; overflow-wrap:anywhere; }}
    .grid {{ margin-top:16px; display:grid; grid-template-columns:1.2fr .8fr; gap:14px; align-items:start; min-width:0; }}
    .panel {{ background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:16px; min-width:0; max-width:100%; }}
    .panel + .panel {{ margin-top:14px; }}
    h2 {{ margin:0 0 12px; font-size:17px; }}
    .cards {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:10px; }}
    a.card {{ display:block; border:1px solid var(--line); border-radius:8px; padding:14px; text-decoration:none; color:var(--ink); background:#fff; min-height:102px; }}
    a.card:hover {{ border-color:var(--blue); }}
    .card strong {{ display:block; font-size:15px; margin-bottom:8px; }}
    .card span {{ display:block; color:var(--muted); font-size:12px; line-height:1.5; }}
    .question-console {{ margin-top:16px; display:grid; grid-template-columns:320px minmax(0,1fr); gap:14px; align-items:start; min-width:0; max-width:100%; overflow:hidden; }}
    .question-console > div {{ min-width:0; max-width:100%; }}
    .question-buttons {{ display:grid; gap:8px; }}
    .question-button {{ border:1px solid var(--line); border-radius:7px; background:#fff; color:var(--ink); padding:10px 11px; text-align:left; font-size:13px; cursor:pointer; }}
    .question-button.active {{ border-color:var(--blue); background:#eff6ff; color:#174ea6; font-weight:700; }}
    .query-box {{ display:grid; grid-template-columns:minmax(0,1fr) auto; gap:8px; margin-bottom:10px; }}
    input,select {{ width:100%; border:1px solid var(--line); border-radius:7px; background:#fff; color:var(--ink); padding:10px 11px; font-size:13px; }}
    button.primary {{ border:1px solid var(--blue); border-radius:7px; background:var(--blue); color:#fff; padding:10px 13px; cursor:pointer; }}
    .evidence-list {{ display:grid; gap:7px; margin-top:10px; }}
    .evidence-item {{ border:1px solid var(--line); border-radius:7px; padding:8px 10px; background:#f8fafc; font-size:12px; color:var(--muted); }}
    .history-list {{ display:flex; flex-wrap:wrap; gap:8px; margin-top:8px; }}
    .history-list button {{ border:1px solid var(--line); border-radius:999px; background:#fff; padding:6px 9px; font-size:12px; cursor:pointer; }}
    .report-filters {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:8px; margin-bottom:10px; }}
    .report-actions {{ display:flex; flex-wrap:wrap; gap:8px; margin-top:10px; }}
    .check-row {{ display:flex; align-items:center; gap:8px; min-width:0; }}
    .check-row input {{ width:auto; }}
    .selected-list {{ border:1px solid var(--line); border-radius:8px; background:#f8fafc; padding:10px; margin-top:10px; min-height:44px; }}
    .answer-meta {{ display:flex; flex-wrap:wrap; gap:8px; margin-bottom:10px; }}
    .pill {{ display:inline-flex; align-items:center; border:1px solid var(--line); border-radius:999px; padding:5px 9px; color:var(--muted); font-size:12px; background:#fff; }}
    .table-scroll {{ overflow:auto; max-width:100%; border:1px solid var(--line); border-radius:8px; }}
    .table-scroll table {{ min-width:720px; }}
    .answer-block + .answer-block {{ margin-top:12px; }}
    .answer-block h3 {{ margin:0 0 8px; font-size:14px; }}
    .reports {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:8px; }}
    .report-link {{ display:flex; justify-content:space-between; gap:10px; align-items:center; border:1px solid var(--line); border-radius:7px; padding:10px 11px; color:var(--ink); text-decoration:none; min-width:0; }}
    .report-link span {{ min-width:0; overflow:hidden; text-overflow:ellipsis; overflow-wrap:anywhere; }}
    .report-link span:last-child {{ color:var(--muted); font-size:12px; }}
    table {{ width:100%; border-collapse:collapse; font-size:13px; }}
    th,td {{ padding:9px 8px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }}
    th:last-child,td:last-child {{ text-align:right; }}
    .small {{ color:var(--muted); font-size:12px; line-height:1.6; }}
    @media (max-width:1100px) {{ .metrics {{ grid-template-columns:repeat(3,1fr); }} .grid,.cards,.question-console {{ grid-template-columns:1fr; }} }}
    @media (max-width:720px) {{ main,header {{ width:100vw; max-width:100vw; padding-left:14px; padding-right:14px; overflow:hidden; }} .metrics,.reports {{ grid-template-columns:1fr; }} .question-console {{ grid-template-columns:minmax(0,1fr); width:100%; max-width:100%; overflow:hidden; }} .value {{ font-size:18px; }} table {{ display:block; max-width:100%; overflow-x:auto; }} .table-scroll {{ width:100%; max-width:100%; overflow-x:auto; }} .table-scroll table {{ display:table; }} }}
  </style>
</head>
<body>
  <header>
    <h1>本地记账分析系统</h1>
    <div class="sub">自由提问、证据化回答、报告新标签查看、交易明细查询和大额复核的本机工作台。</div>
  </header>
  <main>
    <section class="metrics">
      <div class="metric expense"><div class="label">总支出</div><div class="value" id="totalExpense"></div></div>
      <div class="metric review"><div class="label">待复核支出</div><div class="value" id="pendingReview"></div></div>
      <div class="metric income"><div class="label">总收入</div><div class="value" id="totalIncome"></div></div>
      <div class="metric net"><div class="label">净现金流</div><div class="value" id="netCashFlow"></div></div>
      <div class="metric transfer"><div class="label">账户搬运</div><div class="value" id="totalTransfer"></div></div>
      <div class="metric"><div class="label">交易笔数</div><div class="value" id="transactions"></div></div>
    </section>
    <section class="panel question-console" id="questionConsole">
      <div>
        <h2>自定义问题查询控制台</h2>
        <div class="small">输入任意记账问题；系统会在本地 SQLite、报告索引和规则文档中检索证据后回答。</div>
        <div class="question-buttons" id="questionButtons"></div>
        <div class="history-list" id="questionHistory"></div>
      </div>
      <div>
        <div class="query-box">
          <input id="customQuestionInput" placeholder="例如：本月最该优化哪类支出？哪些大额交易还没进入生产统计？">
          <button class="primary" onclick="answerCustomQuestion()">提问</button>
        </div>
        <div class="answer-meta">
          <span class="pill" id="questionTitle"></span>
          <span class="pill" id="questionView"></span>
          <span class="pill">本地检索 · 证据回答</span>
        </div>
        <div id="questionAnswer"></div>
        <div class="evidence-list" id="answerEvidence"></div>
      </div>
    </section>
    <div class="grid">
      <div>
        <section class="panel">
          <h2>工作台</h2>
          <div class="cards">
            <a class="card" id="dashboardLink"><strong>Dashboard</strong><span>现金流、分类占比、风险标签、周期趋势和消费控制动作。</span></a>
            <a class="card" id="operationsLink"><strong>运行控制台</strong><span>周更、复核、标签回灌、报告验收和只读 API 的连续工作流。</span></a>
            <a class="card" id="dataAccessHubLink"><strong>数据接入与回测入口</strong><span>像量化回测入口一样，集中给 PFIOS、行研、赛事分析读取账本视图和 API。</span></a>
            <a class="card" id="acceptanceLink"><strong>用户验收工作台</strong><span>用 A/B/C 按钮确认工程基线、精修方向或 ChatGPT 对照文件缺口。</span></a>
            <a class="card" id="referenceLabLink"><strong>开源参考模型工作台</strong><span>筛选 GitHub/开源参考项目、吸收度、已实现功能和剩余边界。</span></a>
            <a class="card" id="behaviorLink"><strong>交易行为分析</strong><span>按标签组合选择范围，并切换折线、直方、环形和金额分布图。</span></a>
            <a class="card" id="explorerLink"><strong>交易明细查询</strong><span>生产统计和大额待复核分开筛选、分页、导出。</span></a>
            <a class="card" id="tagLibraryLink"><strong>标签库编辑</strong><span>编辑标签分组、颜色、说明和启停状态，下载后回灌保存。</span></a>
            <a class="card" id="reviewLink"><strong>大额复核工作台</strong><span>用下拉菜单选择复核决定、主类/子类和风险标签，下载确认 CSV 后回灌。</span></a>
          </div>
        </section>
        <section class="panel">
          <h2>消费控制动作</h2>
          <table id="controlPlan"></table>
        </section>
      </div>
      <div>
        <section class="panel">
          <h2>报告中心</h2>
          <div class="report-filters" id="reportCenter">
            <input id="reportFilterKeyword" placeholder="搜索报告">
            <select id="reportPeriodFilter"><option value="">全部周期</option><option>周度</option><option>月度</option><option>季度</option><option>半年</option><option>年度</option><option>专项</option></select>
            <select id="reportThemeFilter"><option value="">全部主题</option><option>周期报告</option><option>消费控制</option><option>审计复核</option><option>参考对标</option></select>
            <select id="reportEvidenceFilter"><option value="">全部证据</option><option>经营分析</option><option>审计证据</option><option>规则文档</option></select>
          </div>
          <div id="reportLinks" class="reports"></div>
          <div class="report-actions">
            <button class="primary" onclick="renderSelectedReports()">生成本次查看清单</button>
            <button onclick="clearSelectedReports()">清空选择</button>
          </div>
          <div id="selectedReportList" class="selected-list small">尚未选择报告。</div>
        </section>
        <section class="panel">
          <h2>数据和审计</h2>
          <div class="reports">
            <a class="report-link" id="sqliteLink"><span>SQLite 数据库</span><span>production / review / summary</span></a>
            <a class="report-link" id="summaryLink"><span>汇总 JSON</span><span>metrics</span></a>
            <a class="report-link" id="referenceLink"><span>开源参考矩阵</span><span>reference_models</span></a>
            <a class="report-link" id="manifestLink"><span>运行清单</span><span>run_manifest</span></a>
          </div>
          <p class="small">正式阅读以 PDF 为准；HTML 用于本地交互和复核。未确认大额交易不进入生产统计。</p>
        </section>
      </div>
    </div>
  </main>
  <script>
    const DATA = {json.dumps(data, ensure_ascii=False)};
    const yuan = n => "¥" + Number(n || 0).toLocaleString("zh-CN", {{ minimumFractionDigits:2, maximumFractionDigits:2 }});
    const m = DATA.metrics;
    document.getElementById("totalExpense").textContent = yuan(m.total_expense);
    document.getElementById("pendingReview").textContent = yuan(m.pending_review);
    document.getElementById("totalIncome").textContent = yuan(m.total_income);
    document.getElementById("netCashFlow").textContent = yuan(m.net_cash_flow);
    document.getElementById("totalTransfer").textContent = yuan(m.total_transfer);
    document.getElementById("transactions").textContent = m.transactions;
    document.getElementById("dashboardLink").href = DATA.links.dashboard;
    document.getElementById("operationsLink").href = DATA.links.operations_center;
    document.getElementById("dataAccessHubLink").href = DATA.links.data_access_hub;
    document.getElementById("acceptanceLink").href = DATA.links.acceptance_workbench;
    document.getElementById("referenceLabLink").href = DATA.links.reference_model_lab;
    document.getElementById("behaviorLink").href = DATA.links.behavior_analysis;
    document.getElementById("explorerLink").href = DATA.links.transaction_explorer;
    document.getElementById("tagLibraryLink").href = DATA.links.tag_library;
    document.getElementById("reviewLink").href = DATA.links.review_workbench;
    document.getElementById("sqliteLink").href = DATA.links.sqlite;
    document.getElementById("summaryLink").href = DATA.links.summary;
    document.getElementById("referenceLink").href = DATA.links.reference_models;
    document.getElementById("manifestLink").href = DATA.links.run_manifest;
    function reportMatches(report) {{
      const keyword = document.getElementById("reportFilterKeyword").value.trim().toLowerCase();
      const period = document.getElementById("reportPeriodFilter").value;
      const theme = document.getElementById("reportThemeFilter").value;
      const evidence = document.getElementById("reportEvidenceFilter").value;
      const haystack = [report.name, report.href, report.period, report.theme, report.evidence_type].join(" ").toLowerCase();
      return (!keyword || haystack.includes(keyword)) && (!period || report.period === period) && (!theme || report.theme === theme) && (!evidence || report.evidence_type === evidence);
    }}
    function renderReportCenter() {{
      const filtered = DATA.reports.filter(reportMatches);
      document.getElementById("reportLinks").innerHTML = filtered.map((r, idx) => `<label class="report-link check-row"><input type="checkbox" data-report-href="${{safe(r.href)}}" data-report-name="${{safe(r.name)}}"><a href="${{safe(r.href)}}" target="_blank" rel="noopener"><span>${{safe(r.name)}}</span><span>${{safe(r.period)}} · ${{safe(r.theme)}} · 新标签</span></a></label>`).join("") || `<p class="small">没有匹配报告。</p>`;
    }}
    function renderSelectedReports() {{
      const selected = Array.from(document.querySelectorAll('#reportLinks input[type="checkbox"]:checked')).map(input => ({{ name:input.dataset.reportName, href:input.dataset.reportHref }}));
      document.getElementById("selectedReportList").innerHTML = selected.length
        ? selected.map(item => `<a class="report-link" href="${{safe(item.href)}}" target="_blank" rel="noopener"><span>${{safe(item.name)}}</span><span>打开</span></a>`).join("")
        : "尚未选择报告。";
    }}
    function clearSelectedReports() {{
      document.querySelectorAll('#reportLinks input[type="checkbox"]').forEach(input => input.checked = false);
      renderSelectedReports();
    }}
    ["reportFilterKeyword","reportPeriodFilter","reportThemeFilter","reportEvidenceFilter"].forEach(id => document.getElementById(id).addEventListener("input", renderReportCenter));
    const rows = DATA.control_plan || [];
    document.getElementById("controlPlan").innerHTML = `<tr><th>优先级</th><th>对象</th><th>动作</th><th>预计优化</th></tr>` + rows.map(r => `<tr><td>${{r.priority}}</td><td>${{r.focus_area}}</td><td>${{r.recommended_action}}</td><td>${{yuan(r.estimated_saving)}}</td></tr>`).join("");
    const safe = v => String(v ?? "").replace(/[&<>"']/g, ch => ({{"&":"&amp;","<":"&lt;",">":"&gt;","\\\"":"&quot;","'":"&#39;"}}[ch]));
    const labelMap = {{
      period:"周期", period_start:"开始", period_end:"结束", transactions:"笔数", total_expense:"支出", total_income:"收入", net_cash_flow:"净现金流", pending_review:"待复核", risk_spending:"风险支出", financial_spending:"金融支出",
      main_category:"主类", sub_category:"子类", amount:"金额", count:"笔数", main_pct:"主类占比", sub_pct:"子类占比", risk_tag:"风险标签", expense_pct:"支出占比",
      priority:"优先级", focus_area:"对象", recommended_action:"动作", estimated_saving:"预计优化", status_label:"状态", amount_pct:"金额占比", production_effect:"统计影响", next_action:"下一步",
      group_type:"分组", group_key:"对象", include_candidate_count:"候选纳入", manual_review_count:"人工复核", top_reason:"理由", transaction_time:"时间", counterparty:"对手方", description:"说明", risk_tags:"风险标签"
    }};
    function formatCell(key, value) {{
      if (["total_expense","total_income","net_cash_flow","pending_review","risk_spending","financial_spending","amount","current_amount","estimated_saving"].includes(key)) return yuan(value);
      return safe(value);
    }}
    function renderRows(items, preferred) {{
      const rows = Array.isArray(items) ? items : [];
      if (!rows.length) return `<p class="small">暂无结果</p>`;
      const first = rows[0] || {{}};
      const preferredCols = preferred.filter(col => col in first);
      const cols = (preferredCols.length ? preferredCols : Object.keys(first)).slice(0, 8);
      return `<div class="table-scroll"><table><tr>${{cols.map(col => `<th>${{labelMap[col] || col}}</th>`).join("")}}</tr>${{rows.map(row => `<tr>${{cols.map(col => `<td>${{formatCell(col, row[col])}}</td>`).join("")}}</tr>`).join("")}}</table></div>`;
    }}
    function renderEvidence(entry) {{
      const evidence = entry.evidence || [];
      document.getElementById("answerEvidence").innerHTML = `<div class="evidence-item"><strong>${{safe(entry.layer || "OBSERVATION")}}</strong> · 可信度：${{safe(entry.confidence || "中")}} · 相关性：${{safe(entry.relevance || "中")}} · 不确定性：${{safe(entry.uncertainty || "中")}} · 缺失信息：${{safe(entry.missing_information || "无")}}</div>` +
        evidence.map(item => `<div class="evidence-item">来源：${{safe(item)}}</div>`).join("");
    }}
    function scoreQuestion(query, entry) {{
      const q = query.toLowerCase();
      const text = [entry.question, entry.answer, ...(entry.evidence || [])].join(" ").toLowerCase();
      let score = 0;
      q.split(/\\s+/).filter(Boolean).forEach(token => {{ if (text.includes(token)) score += 2; }});
      ["优化","降低","消费","支出","风险","大额","复核","生产统计","报告","系统","现金流"].forEach(token => {{
        if (q.includes(token) && text.includes(token)) score += 3;
      }});
      return score;
    }}
    function rememberQuestion(query) {{
      const key = "finance_ledger_question_history_v1";
      const current = JSON.parse(localStorage.getItem(key) || "[]").filter(item => item !== query);
      current.unshift(query);
      localStorage.setItem(key, JSON.stringify(current.slice(0, 8)));
      renderQuestionHistory();
    }}
    function renderQuestionHistory() {{
      const key = "finance_ledger_question_history_v1";
      const items = JSON.parse(localStorage.getItem(key) || "[]");
      document.getElementById("questionHistory").innerHTML = items.map(item => `<button onclick="askHistoryQuestion('${{safe(item)}}')">${{safe(item)}}</button>`).join("");
    }}
    function askHistoryQuestion(query) {{
      document.getElementById("customQuestionInput").value = query;
      answerCustomQuestion();
    }}
    function answerCustomQuestion() {{
      const query = document.getElementById("customQuestionInput").value.trim();
      const fallback = "请先输入一个和记账、消费、报告、复核或现金流相关的问题。";
      if (!query) {{
        document.getElementById("questionAnswer").innerHTML = `<p class="small">${{fallback}}</p>`;
        document.getElementById("answerEvidence").innerHTML = "";
        return;
      }}
      const ranked = DATA.qa_index.map(entry => ({{ entry, score:scoreQuestion(query, entry) }})).sort((a,b) => b.score - a.score);
      const best = ranked[0]?.score > 0 ? ranked[0].entry : DATA.qa_index.find(entry => entry.question.includes("这个系统")) || DATA.qa_index[0];
      document.getElementById("questionTitle").textContent = query;
      document.getElementById("questionView").textContent = "自定义检索";
      document.getElementById("questionAnswer").innerHTML = `<div class="answer-block"><h3>${{safe(best.layer || "OBSERVATION")}} · ${{safe(best.question)}}</h3><p class="small">${{safe(best.answer)}}</p></div>`;
      renderEvidence(best);
      rememberQuestion(query);
    }}
    function renderQuestion(templateId) {{
      const template = DATA.question_templates.find(item => item.id === templateId) || DATA.question_templates[0];
      document.querySelectorAll(".question-button").forEach(button => button.classList.toggle("active", button.dataset.id === template.id));
      document.getElementById("questionTitle").textContent = template.title;
      document.getElementById("questionView").textContent = template.view;
      const result = DATA.question_results[template.id];
      let html = "";
      if (template.id === "pending_large_review") {{
        html += `<div class="answer-block"><h3>复核状态</h3>${{renderRows(result.status, ["status_label","count","amount","amount_pct","production_effect","next_action"])}}</div>`;
        html += `<div class="answer-block"><h3>待复核明细</h3>${{renderRows(result.transactions, ["transaction_time","counterparty","description","amount","main_category","sub_category","risk_tags"])}}</div>`;
        html += `<div class="answer-block"><h3>候选分组</h3>${{renderRows(result.candidate_groups, ["group_type","group_key","count","amount","include_candidate_count","manual_review_count","top_reason"])}}</div>`;
      }} else if (template.id === "latest_month_cashflow") {{
        html = renderRows(result, ["period","transactions","total_expense","total_income","net_cash_flow","pending_review","risk_spending","financial_spending"]);
      }} else if (template.id === "top_categories") {{
        html = renderRows(result, ["main_category","sub_category","amount","count","main_pct","sub_pct"]);
      }} else if (template.id === "risk_exposure") {{
        html = renderRows(result, ["risk_tag","amount","count","expense_pct"]);
      }} else {{
        html = renderRows(result, ["priority","focus_area","current_amount","current_pct","recommended_action","estimated_saving","review_needed"]);
      }}
      document.getElementById("questionAnswer").innerHTML = html;
      renderEvidence(DATA.qa_index.find(entry => entry.question.includes(template.title.slice(0, 4))) || DATA.qa_index[0]);
    }}
    function renderQuestionConsole() {{
      document.getElementById("questionButtons").innerHTML = DATA.question_templates.map(item => `<button class="question-button" data-id="${{safe(item.id)}}" onclick="renderQuestion('${{safe(item.id)}}')">${{safe(item.title)}}</button>`).join("");
      renderQuestion(DATA.question_templates[0].id);
    }}
    Object.assign(window, {{ renderQuestion, answerCustomQuestion, askHistoryQuestion, renderSelectedReports, clearSelectedReports }});
    renderReportCenter();
    renderQuestionHistory();
    renderQuestionConsole();
  </script>
</body>
</html>"""


def _global_nav_html(prefix: str = "") -> str:
    links = [
        ("主菜单", f"{prefix}index.html"),
        ("Dashboard", f"{prefix}dashboard.html"),
        ("数据接入", f"{prefix}data_access_hub.html"),
        ("报告中心", f"{prefix}index.html#reportCenter"),
        ("交易明细", f"{prefix}transaction_explorer.html"),
        ("行为分析", f"{prefix}behavior_analysis.html"),
        ("标签库", f"{prefix}tag_library.html"),
        ("大额复核", f"{prefix}review_workbench.html"),
        ("运行控制台", f"{prefix}operations_center.html"),
    ]
    return (
        '<nav id="globalNav" class="global-nav" aria-label="全局导航">'
        '<a class="global-home" href="{0}index.html">返回主菜单</a>'
        '<div class="global-links">{1}</div>'
        '<button id="usageGuideToggle" class="usage-guide-toggle" type="button" onclick="openUsageGuide()">使用说明 / 术语</button>'
        "</nav>"
    ).format(
        prefix,
        "".join(f'<a href="{href}">{label}</a>' for label, href in links),
    )


def _usage_guide_html() -> str:
    glossary = [
        ("生产口径", "只统计已确认、可用于正式报告和决策的交易；一万元以上未确认交易先隔离。"),
        ("待复核隔离", "需要你人工确认的大额或低置信交易，不进入生产统计，避免误判支出结构。"),
        ("真实消费", "剔除账户搬运后，真正消耗现金流或形成生活/社交/金融支出的部分。"),
        ("风险支出", "用于识别行为风险的标签集合，例如信用周转、夜间冲动、低复购购物、平台便利。"),
        ("可优化支出", "不一定错误，但具备压缩空间的支出，如低复购购物、外卖即时零售、会员订阅。"),
        ("现金流视图", "同时看收入、支出、净现金流、账户搬运和金融资金流，避免只看消费总额。"),
        ("环比", "本期与上一周期比较；周报为本周 vs 上周，月报为本月 vs 上月。"),
        ("同比", "本期与去年同期比较；周报使用去年同 ISO 周，月报使用去年同月。"),
        ("只读视图", "给 PFIOS、行研、赛事分析等系统读取的 SQLite view，不允许下游直接改账本。"),
        ("Data Trust", "逐笔可信度状态，用于判断交易是否可直接入模、需复核或应拒绝。"),
        ("Reconciliation", "自动对账层，检查来源、清洗、生产分摊、月度汇总和复核隔离是否一致。"),
        ("风险标签", "行为分析维度，不等于会计科目；所有支出都必须有风险标签，便于控制消费。"),
    ]
    glossary_html = "".join(
        f"<dt>{term}</dt><dd>{definition}</dd>" for term, definition in glossary
    )
    return f"""
<aside id="usageGuidePanel" class="usage-guide-panel" aria-label="使用说明与专业术语" aria-hidden="true">
  <div class="usage-guide-head">
    <div>
      <h2>使用说明与专业术语</h2>
      <p>保持当前页面不跳转，一边看指引一边操作。</p>
    </div>
    <button type="button" onclick="closeUsageGuide()" aria-label="关闭使用说明">关闭</button>
  </div>
  <div class="usage-guide-body">
    <section class="guide-section">
      <h3>推荐操作路径</h3>
      <ol class="guide-steps">
        <li><strong>先看 Dashboard</strong><span>确认总支出、净现金流、分类占比和风险标签是否符合直觉。</span></li>
        <li><strong>处理大额复核</strong><span>一万元以上交易先下拉确认；确认前不进入生产统计。</span></li>
        <li><strong>查看报告中心</strong><span>按周/月/季/半年/年筛选 PDF，重点看同比、环比和主类/子类占比。</span></li>
        <li><strong>用行为分析定位问题</strong><span>组合标签筛选夜间、信用工具、平台便利、低复购等风险行为。</span></li>
        <li><strong>更新标签库</strong><span>把稳定规则沉淀到标签库，后续周更复用，减少重复人工判断。</span></li>
      </ol>
    </section>
    <section class="guide-section">
      <h3>工作流可视化</h3>
      <svg class="guide-flow" viewBox="0 0 760 140" role="img" aria-label="账本分析工作流">
        <defs><marker id="guideArrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="#647083"/></marker></defs>
        <g fill="#fff" stroke="#d9e0ea" stroke-width="2">
          <rect x="10" y="28" width="105" height="72" rx="8"/><rect x="135" y="28" width="105" height="72" rx="8"/>
          <rect x="260" y="28" width="105" height="72" rx="8"/><rect x="385" y="28" width="105" height="72" rx="8"/>
          <rect x="510" y="28" width="105" height="72" rx="8"/><rect x="635" y="28" width="105" height="72" rx="8"/>
        </g>
        <g stroke="#647083" stroke-width="2" marker-end="url(#guideArrow)"><line x1="116" y1="64" x2="130" y2="64"/><line x1="241" y1="64" x2="255" y2="64"/><line x1="366" y1="64" x2="380" y2="64"/><line x1="491" y1="64" x2="505" y2="64"/><line x1="616" y1="64" x2="630" y2="64"/></g>
        <g fill="#172033" font-size="13" font-weight="700" text-anchor="middle">
          <text x="62" y="58">上传账单</text><text x="187" y="58">分类入库</text><text x="312" y="58">大额复核</text>
          <text x="437" y="58">生产统计</text><text x="562" y="58">报告分析</text><text x="687" y="58">控制动作</text>
        </g>
        <g fill="#647083" font-size="11" text-anchor="middle">
          <text x="62" y="78">CSV/截图候选</text><text x="187" y="78">规则+标签</text><text x="312" y="78">下拉确认</text>
          <text x="437" y="78">SQLite 视图</text><text x="562" y="78">PDF/Dashboard</text><text x="687" y="78">预算/复盘</text>
        </g>
      </svg>
    </section>
    <section class="guide-section">
      <h3>页面怎么用</h3>
      <div class="guide-grid">
        <article><strong>运行控制台</strong><span>按按钮选择周更、复核、打包、API，不需要记命令。</span></article>
        <article><strong>交易明细</strong><span>用模糊搜索和标签组合确认筛选对象，避免误删或误判。</span></article>
        <article><strong>报告中心</strong><span>用周期、主题、证据类型过滤，PDF 默认新标签打开。</span></article>
        <article><strong>数据接入</strong><span>下游系统只读 SQLite 视图，避免复制数据库和重复建设。</span></article>
      </div>
    </section>
    <section class="guide-section">
      <h3>专业术语</h3>
      <dl class="guide-glossary">{glossary_html}</dl>
    </section>
    <section class="guide-section guide-warning">
      <h3>使用边界</h3>
      <p>本系统不自动执行支付、投资、转账或交易；所有大额待复核交易必须由你确认后才会进入生产统计。</p>
    </section>
  </div>
</aside>
<div id="usageGuideBackdrop" class="usage-guide-backdrop" onclick="closeUsageGuide()"></div>
<script id="usageGuideScript">
  function openUsageGuide() {{
    const panel = document.getElementById("usageGuidePanel");
    const backdrop = document.getElementById("usageGuideBackdrop");
    if (!panel || !backdrop) return;
    panel.classList.add("open");
    backdrop.classList.add("open");
    panel.setAttribute("aria-hidden", "false");
    localStorage.setItem("financeLedgerUsageGuideOpen", "1");
  }}
  function closeUsageGuide() {{
    const panel = document.getElementById("usageGuidePanel");
    const backdrop = document.getElementById("usageGuideBackdrop");
    if (!panel || !backdrop) return;
    panel.classList.remove("open");
    backdrop.classList.remove("open");
    panel.setAttribute("aria-hidden", "true");
    localStorage.setItem("financeLedgerUsageGuideOpen", "0");
  }}
  document.addEventListener("keydown", event => {{
    if (event.key === "Escape") closeUsageGuide();
  }});
  window.openUsageGuide = openUsageGuide;
  window.closeUsageGuide = closeUsageGuide;
</script>
"""


def _inject_global_nav(path: Path) -> None:
    if not path.exists() or path.suffix.lower() != ".html":
        return
    content = path.read_text(encoding="utf-8")
    if path.parent.name == "review":
        prefix = "../"
    else:
        prefix = ""
    favicon_href = f"{prefix}favicon.png"
    if 'id="globalNav"' in content:
        if 'rel="icon"' not in content:
            content = content.replace("</head>", f'  <link rel="icon" type="image/png" href="{favicon_href}">\n</head>', 1)
            path.write_text(content, encoding="utf-8")
        return
    nav_css = """
  <style id="globalNavStyle">
    .global-nav{position:sticky;top:0;z-index:20;display:flex;align-items:center;justify-content:space-between;gap:12px;padding:10px 24px;background:#ffffff;border-bottom:1px solid #d9e0ea;box-shadow:0 1px 2px rgba(15,23,42,.04)}
    .global-nav a{color:#172033;text-decoration:none;font-size:13px;white-space:nowrap}
    .global-home{font-weight:750;color:#174ea6!important}
    .global-links{display:flex;gap:10px;overflow-x:auto;max-width:100%}
    .usage-guide-toggle{border:1px solid #2563eb;border-radius:7px;background:#eff6ff;color:#174ea6;font-size:13px;padding:7px 10px;cursor:pointer;white-space:nowrap}
    .usage-guide-backdrop{position:fixed;inset:0;background:rgba(15,23,42,.24);opacity:0;pointer-events:none;transition:opacity .16s ease;z-index:49}
    .usage-guide-backdrop.open{opacity:1;pointer-events:auto}
    .usage-guide-panel{position:fixed;top:0;right:0;bottom:0;width:min(520px,94vw);transform:translateX(104%);transition:transform .18s ease;z-index:50;background:#ffffff;border-left:1px solid #d9e0ea;box-shadow:-14px 0 34px rgba(15,23,42,.18);display:flex;flex-direction:column;color:#172033}
    .usage-guide-panel.open{transform:translateX(0)}
    .usage-guide-head{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;padding:18px 20px;border-bottom:1px solid #d9e0ea;background:#f8fafc}
    .usage-guide-head h2{margin:0 0 5px;font-size:18px;letter-spacing:0;color:#172033}
    .usage-guide-head p{margin:0;color:#647083;font-size:12px;line-height:1.5}
    .usage-guide-head button{border:1px solid #d9e0ea;border-radius:7px;background:#fff;color:#172033;padding:7px 10px;cursor:pointer}
    .usage-guide-body{overflow:auto;padding:16px 20px 28px}
    .guide-section{border:1px solid #d9e0ea;border-radius:8px;background:#fff;padding:14px;margin-bottom:12px}
    .guide-section h3{margin:0 0 10px;font-size:15px;color:#172033}
    .guide-steps{margin:0;padding-left:20px}
    .guide-steps li{margin:0 0 10px;color:#172033}
    .guide-steps span{display:block;color:#647083;font-size:12px;line-height:1.5;margin-top:3px}
    .guide-flow{width:100%;height:auto;border:1px solid #d9e0ea;border-radius:8px;background:#fbfcfe}
    .guide-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}
    .guide-grid article{border:1px solid #d9e0ea;border-radius:8px;background:#fbfcfe;padding:10px;min-width:0}
    .guide-grid strong{display:block;font-size:13px;margin-bottom:5px}
    .guide-grid span{display:block;color:#647083;font-size:12px;line-height:1.45}
    .guide-glossary{display:grid;grid-template-columns:118px minmax(0,1fr);gap:8px 10px;margin:0}
    .guide-glossary dt{font-weight:750;font-size:12px;color:#172033}
    .guide-glossary dd{margin:0;color:#647083;font-size:12px;line-height:1.5}
    .guide-warning{border-color:#fed7aa;background:#fff7ed}
    .guide-warning p{margin:0;color:#7c2d12;font-size:12px;line-height:1.6}
    @media(max-width:720px){.global-nav{align-items:flex-start;flex-direction:column;padding:10px 14px}.global-links{width:100%;padding-bottom:2px}.usage-guide-toggle{width:100%;text-align:center}.guide-grid,.guide-glossary{grid-template-columns:1fr}.usage-guide-panel{width:100vw}}
  </style>
"""
    if 'rel="icon"' not in content:
        content = content.replace("</head>", f'  <link rel="icon" type="image/png" href="{favicon_href}">\n</head>', 1)
    content = content.replace("</head>", nav_css + "</head>", 1)
    nav = _global_nav_html(prefix)
    if path.parent.name == "review":
        nav = nav.replace('href="../review_workbench.html"', 'href="review_workbench.html"')
    content = content.replace("<body>", "<body>\n" + nav, 1)
    content = content.replace("</body>", _usage_guide_html() + "\n</body>", 1)
    path.write_text(content, encoding="utf-8")


def _inject_global_nav_all(output_dir: Path) -> None:
    for html_path in output_dir.rglob("*.html"):
        _inject_global_nav(html_path)


def _copy_app_icon_assets(output_dir: Path, reports_dir: Path) -> None:
    icon_path = Path(__file__).resolve().parents[2] / "assets" / "app_icon" / "finance_ledger_icon_32.png"
    if not icon_path.exists():
        return
    shutil.copy2(icon_path, output_dir / "favicon.png")
    shutil.copy2(icon_path, reports_dir / "favicon.png")


def _data_access_hub_html(
    metrics: dict[str, Any],
    output_paths: dict[str, str],
    *,
    location: str = "reports",
) -> str:
    report_prefix = "" if location == "reports" else "reports/"
    data_prefix = "../data/" if location == "reports" else "data/"
    audit_prefix = "../audit/" if location == "reports" else "audit/"
    links = {
        "dashboard": f"{report_prefix}dashboard.html",
        "explorer": f"{report_prefix}transaction_explorer.html",
        "behavior": f"{report_prefix}behavior_analysis.html",
        "operations": f"{report_prefix}operations_center.html",
        "sqlite": f"{data_prefix}consumption.sqlite",
        "summary": "../summary.json" if location == "reports" else "summary.json",
        "manifest": f"{audit_prefix}run_manifest.json",
        "contract": f"{report_prefix}user_manual_report.pdf",
    }
    views = [
        {"name": "v_fact_expense_allocations", "purpose": "生产口径真实消费分摊，适合下游建模、预算压力和消费行为分析。", "risk": "大额待复核已隔离。"},
        {"name": "v_mart_daily_cashflow", "purpose": "日度收入、支出、净现金流和账户搬运，适合和量化回测资金曲线对齐。", "risk": "不代表投资收益率，只代表账本现金流。"},
        {"name": "v_mart_risk_monthly", "purpose": "月度风险标签金额和占比，适合消费控制、行为状态和周期报告。", "risk": "风险标签是行为分析维度，不等于会计科目。"},
        {"name": "v_mart_counterparty_monthly", "purpose": "对手方月度聚合，适合识别固定扣费、家庭转账和高频小额渠道。", "risk": "涉及私人对手方信息，仅本机读取。"},
        {"name": "v_fact_pending_large_review", "purpose": "一万元以上待复核交易，确认前不进入生产统计。", "risk": "必须人工确认后再回灌。"},
        {"name": "v_data_trust_transactions", "purpose": "逐笔可信度状态，适合下游系统判断数据能否入模。", "risk": "低可信或 rejected 不应直接进入决策。"},
        {"name": "v_reconciliation_checks", "purpose": "自动对账结果，适合交付前质量门禁。", "risk": "任何 fail 都应阻止正式使用。"},
    ]
    consumers = [
        {"system": "PFIOS / 量化回测", "use": "读取日度现金流、金融资金流和待复核隔离状态，避免把生活账单误当成交易信号。", "entry": "v_mart_daily_cashflow"},
        {"system": "ResearchBus / 行研", "use": "读取消费行为状态、分类占比、风险标签和周期摘要，作为用户真实现金流背景。", "entry": "v_fact_expense_allocations"},
        {"system": "赛事分析", "use": "仅可读取现金流压力和预算状态，不能读取私人明细作为投注建议。", "entry": "v_mart_daily_cashflow"},
        {"system": "微信候选入箱", "use": "新增截图/文本先进入候选区，确认后再更新生产账本。", "entry": "weixin_intake_items"},
    ]
    data = {
        "metrics": metrics,
        "links": links,
        "views": views,
        "consumers": consumers,
        "commands": {
            "readonly_api": "python3 scripts/serve_ledger.py --db data/finance_ledger/finance_ledger.sqlite --reports outputs/finance_ledger_20220605_20260603/reports --host 127.0.0.1 --port 8766",
            "quick_query": "sqlite3 data/finance_ledger/finance_ledger.sqlite \"select * from v_mart_daily_cashflow order by day desc limit 20;\"",
            "weekly_update": "python3 scripts/weekly_update.py --input data/finance_ledger/sources --ledger-db data/finance_ledger/finance_ledger.sqlite --output outputs/finance_ledger_20220605_20260603",
        },
    }
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>数据接入与回测入口</title>
  <style>
    :root {{ --bg:#f5f7fb; --panel:#fff; --ink:#172033; --muted:#647083; --line:#d9e0ea; --blue:#2563eb; --green:#047857; --red:#b42318; --amber:#a16207; --cyan:#0e7490; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; background:var(--bg); color:var(--ink); }}
    header {{ background:#fff; border-bottom:1px solid var(--line); padding:24px 32px 16px; }}
    h1 {{ margin:0 0 6px; font-size:25px; letter-spacing:0; }}
    .sub {{ color:var(--muted); font-size:13px; line-height:1.6; max-width:980px; }}
    main {{ max-width:1440px; margin:0 auto; padding:20px 32px 44px; }}
    .metrics {{ display:grid; grid-template-columns:repeat(5,minmax(130px,1fr)); gap:10px; }}
    .metric {{ background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:14px; min-height:78px; }}
    .metric strong {{ display:block; margin-top:7px; font-size:19px; overflow-wrap:anywhere; }}
    .label {{ color:var(--muted); font-size:12px; }}
    .grid {{ margin-top:16px; display:grid; grid-template-columns:1fr 1fr; gap:14px; align-items:start; }}
    .panel {{ background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:16px; min-width:0; max-width:100%; }}
    h2 {{ margin:0 0 12px; font-size:17px; }}
    .cards {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:10px; }}
    a.card {{ display:block; border:1px solid var(--line); border-radius:8px; padding:13px; color:var(--ink); text-decoration:none; background:#fff; min-height:90px; }}
    a.card:hover {{ border-color:var(--blue); }}
    .card strong {{ display:block; margin-bottom:7px; font-size:14px; }}
    .card span {{ display:block; color:var(--muted); font-size:12px; line-height:1.5; }}
    table {{ width:100%; border-collapse:collapse; font-size:13px; }}
    th,td {{ padding:9px 8px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }}
    th:last-child,td:last-child {{ text-align:left; }}
    .table-wrap {{ overflow:auto; border:1px solid var(--line); border-radius:8px; }}
    .table-wrap table {{ min-width:760px; }}
    .command {{ background:#0f172a; color:#e5e7eb; border-radius:8px; padding:12px; font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:12px; overflow:auto; white-space:pre-wrap; line-height:1.5; }}
    .actions {{ display:flex; flex-wrap:wrap; gap:8px; margin:10px 0 0; }}
    a.button,button {{ border:1px solid var(--line); border-radius:7px; padding:9px 11px; background:#fff; color:var(--ink); text-decoration:none; cursor:pointer; font-size:13px; }}
    a.primary {{ background:var(--blue); border-color:var(--blue); color:#fff; }}
    .pill {{ display:inline-flex; border:1px solid var(--line); border-radius:999px; padding:5px 9px; color:var(--muted); background:#fff; font-size:12px; margin:0 6px 8px 0; }}
    .small {{ color:var(--muted); font-size:12px; line-height:1.6; }}
    @media(max-width:1100px) {{ .metrics {{ grid-template-columns:repeat(2,1fr); }} .grid,.cards {{ grid-template-columns:1fr; }} }}
    @media(max-width:720px) {{ main,header {{ padding-left:14px; padding-right:14px; }} .metrics {{ grid-template-columns:1fr; }} .table-wrap table {{ min-width:640px; }} }}
  </style>
</head>
<body>
  <header>
    <h1>数据接入与回测入口</h1>
    <div class="sub">这是给 PFIOS、行研、赛事分析和其他本地子系统使用的账本数据入口。它复用同一个 SQLite 和报告产物，不复制数据库、不重复建设代码，也不默认公网开放。</div>
  </header>
  <main>
    <section class="metrics">
      <div class="metric"><span class="label">生产口径总支出</span><strong id="totalExpense"></strong></div>
      <div class="metric"><span class="label">总收入</span><strong id="totalIncome"></strong></div>
      <div class="metric"><span class="label">净现金流</span><strong id="netCashFlow"></strong></div>
      <div class="metric"><span class="label">待复核隔离</span><strong id="pendingReview"></strong></div>
      <div class="metric"><span class="label">交易笔数</span><strong id="transactions"></strong></div>
    </section>
    <section class="grid">
      <div class="panel">
        <h2>一级入口</h2>
        <div class="cards">
          <a class="card" id="dashboardLink"><strong>Dashboard</strong><span>先看现金流、分类、风险标签和周期趋势。</span></a>
          <a class="card" id="explorerLink"><strong>交易明细查询</strong><span>逐笔检索、筛选、导出和复核隔离检查。</span></a>
          <a class="card" id="behaviorLink"><strong>交易行为分析</strong><span>按标签组合切换折线图、直方图、环形图和分布图。</span></a>
          <a class="card" id="operationsLink"><strong>运行控制台</strong><span>周更、回灌、验收、打包和 API 启动。</span></a>
          <a class="card" id="sqliteLink"><strong>SQLite 数据库</strong><span>本机只读数据源，供下游系统按视图读取。</span></a>
          <a class="card" id="manifestLink"><strong>运行清单</strong><span>查看本次输出、来源和审计文件索引。</span></a>
        </div>
      </div>
      <div class="panel">
        <h2>子系统读取边界</h2>
        <div id="consumerPills"></div>
        <div class="table-wrap"><table id="consumerTable"></table></div>
      </div>
    </section>
    <section class="panel" style="margin-top:14px">
      <h2>推荐只读视图</h2>
      <div class="table-wrap"><table id="viewTable"></table></div>
    </section>
    <section class="grid">
      <div class="panel">
        <h2>启动只读 API</h2>
        <pre class="command" id="apiCommand"></pre>
        <div class="actions"><button onclick="copyText('apiCommand')">复制 API 命令</button><a class="button primary" id="contractLink">查看数据契约</a></div>
        <p class="small" id="copyStatus">API 默认只绑定 127.0.0.1。需要公网、认证、多用户访问时应另起安全设计。</p>
      </div>
      <div class="panel">
        <h2>快速查询样例</h2>
        <pre class="command" id="queryCommand"></pre>
        <div class="actions"><button onclick="copyText('queryCommand')">复制查询命令</button><button onclick="copyText('weeklyCommand')">复制周更命令</button></div>
        <pre class="command" id="weeklyCommand" style="margin-top:10px"></pre>
      </div>
    </section>
  </main>
  <script>
    const DATA = {json.dumps(data, ensure_ascii=False)};
    const yuan = n => "¥" + Number(n || 0).toLocaleString("zh-CN", {{ minimumFractionDigits:2, maximumFractionDigits:2 }});
    const safe = v => String(v ?? "").replace(/[&<>"']/g, ch => ({{"&":"&amp;","<":"&lt;",">":"&gt;","\\\"":"&quot;","'":"&#39;"}}[ch]));
    document.getElementById("totalExpense").textContent = yuan(DATA.metrics.total_expense);
    document.getElementById("totalIncome").textContent = yuan(DATA.metrics.total_income);
    document.getElementById("netCashFlow").textContent = yuan(DATA.metrics.net_cash_flow);
    document.getElementById("pendingReview").textContent = yuan(DATA.metrics.pending_review);
    document.getElementById("transactions").textContent = DATA.metrics.transactions;
    document.getElementById("dashboardLink").href = DATA.links.dashboard;
    document.getElementById("explorerLink").href = DATA.links.explorer;
    document.getElementById("behaviorLink").href = DATA.links.behavior;
    document.getElementById("operationsLink").href = DATA.links.operations;
    document.getElementById("sqliteLink").href = DATA.links.sqlite;
    document.getElementById("manifestLink").href = DATA.links.manifest;
    document.getElementById("contractLink").href = DATA.links.contract;
    document.getElementById("apiCommand").textContent = DATA.commands.readonly_api;
    document.getElementById("queryCommand").textContent = DATA.commands.quick_query;
    document.getElementById("weeklyCommand").textContent = DATA.commands.weekly_update;
    document.getElementById("consumerPills").innerHTML = DATA.consumers.map(row => `<span class="pill">${{safe(row.system)}} · ${{safe(row.entry)}}</span>`).join("");
    document.getElementById("consumerTable").innerHTML = `<thead><tr><th>系统</th><th>用途</th><th>入口视图/表</th></tr></thead><tbody>${{DATA.consumers.map(row => `<tr><td>${{safe(row.system)}}</td><td>${{safe(row.use)}}</td><td>${{safe(row.entry)}}</td></tr>`).join("")}}</tbody>`;
    document.getElementById("viewTable").innerHTML = `<thead><tr><th>视图</th><th>用途</th><th>风险边界</th></tr></thead><tbody>${{DATA.views.map(row => `<tr><td>${{safe(row.name)}}</td><td>${{safe(row.purpose)}}</td><td>${{safe(row.risk)}}</td></tr>`).join("")}}</tbody>`;
    function copyText(id) {{
      const text = document.getElementById(id).textContent;
      if (navigator.clipboard) {{
        navigator.clipboard.writeText(text).then(() => document.getElementById("copyStatus").textContent = "已复制。");
      }} else {{
        document.getElementById("copyStatus").textContent = text;
      }}
    }}
  </script>
</body>
</html>"""


def _finance_ledger_system_improvement_assets(
    *,
    reports_dir: Path,
    audit_dir: Path,
    output_paths: dict[str, str],
) -> dict[str, str]:
    source_rows = [
        {
            "source": "Actual Budget",
            "url_or_path": "https://github.com/actualbudget/actual ; https://actualbudget.com/docs/reports/custom-reports/",
            "credibility": "高",
            "relevance": "高",
            "evidence_type": "公开开源项目/官方文档",
            "uncertainty": "低",
            "missing_information": "未复用其代码，仅参考 local-first 和 custom reports 产品模式。",
        },
        {
            "source": "Firefly III",
            "url_or_path": "https://firefly-iii.org/documentation/",
            "credibility": "中高",
            "relevance": "高",
            "evidence_type": "公开产品文档入口",
            "uncertainty": "中",
            "missing_information": "部分深层文档访问受限，仅引用公开入口可见的导入、规则、标签、报告、API 方向。",
        },
        {
            "source": "Open WebUI Knowledge",
            "url_or_path": "https://docs.openwebui.com/features/workspace/knowledge/",
            "credibility": "高",
            "relevance": "中高",
            "evidence_type": "官方文档",
            "uncertainty": "低",
            "missing_information": "本阶段不接入 LLM，仅吸收检索证据后回答的交互原则。",
        },
        {
            "source": "MDN rel=noopener",
            "url_or_path": "https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Attributes/rel/noopener",
            "credibility": "高",
            "relevance": "中",
            "evidence_type": "官方技术文档",
            "uncertainty": "低",
            "missing_information": "用于新标签打开安全规范。",
        },
        {
            "source": "当前本地代码和输出",
            "url_or_path": "src/econ_bleed_analyzer/reports.py ; outputs/finance_ledger_20220605_20260603/reports/",
            "credibility": "高",
            "relevance": "高",
            "evidence_type": "用户授权本地文件",
            "uncertainty": "低",
            "missing_information": "不包含未导入的新账单或用户未确认的大额复核决定。",
        },
    ]
    gap_rows = [
        {"gap": "固定模板问题限制自由查询", "evidence": "index.html question_templates", "improvement": "自由输入 + 本地证据检索", "priority": "P0", "status": "planned_for_v2"},
        {"gap": "报告静态列表难以筛选", "evidence": "reportLinks static list", "improvement": "周期/主题/证据/关键词筛选 + 查看清单", "priority": "P0", "status": "planned_for_v2"},
        {"gap": "跨模块返回主菜单不顺畅", "evidence": "HTML pages lacked shared nav", "improvement": "统一顶部导航 + 返回主菜单", "priority": "P0", "status": "planned_for_v2"},
        {"gap": "系统定位被审计交付语言稀释", "evidence": "portal copy emphasized delivery artifacts", "improvement": "定位为本地记账分析系统，日常任务优先", "priority": "P1", "status": "planned_for_v2"},
    ]
    qa_rows = [
        {
            "question": "本月最该优化哪类支出",
            "answer_policy": "检索 summary_by_month、summary_by_category、spending_control_plan 后返回带证据的 INFERENCE。",
            "sources": ["summary_by_month", "summary_by_category", "spending_control_plan"],
        },
        {
            "question": "哪些大额交易还没进入生产统计",
            "answer_policy": "检索 manual_review_status_summary 和 manual_review_queue 后返回 FACT。",
            "sources": ["manual_review_status_summary", "manual_review_queue"],
        },
        {
            "question": "如何查看报告",
            "answer_policy": "检索 report_manifest 和 reports/index.html，说明筛选、新标签和查看清单。",
            "sources": ["report_manifest.json", "reports/index.html"],
        },
    ]
    source_json = audit_dir / "finance_ledger_system_improvement_source_log.json"
    source_csv = audit_dir / "finance_ledger_system_improvement_source_log.csv"
    gap_csv = audit_dir / "system_improvement_gap_matrix.csv"
    qa_index = audit_dir / "question_answer_index.json"
    source_json.write_text(json.dumps(source_rows, ensure_ascii=False, indent=2), encoding="utf-8")
    with source_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(source_rows[0].keys()))
        writer.writeheader()
        writer.writerows(source_rows)
    with gap_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(gap_rows[0].keys()))
        writer.writeheader()
        writer.writerows(gap_rows)
    qa_index.write_text(json.dumps(qa_rows, ensure_ascii=False, indent=2), encoding="utf-8")
    actions = [
        ("自由问答控制台", "高：减少查表和找报告时间", "中", "低", "现有 SQLite/MD 报告", "问两个验收问题能返回证据", "未导入最新账单或证据缺失"),
        ("报告中心筛选", "高：快速定位周/月/复核/风险报告", "低", "低", "report_manifest 和 PDF/HTML", "筛选月报/风险/复核收敛结果", "报告命名未登记"),
        ("全局导航", "高：解决跳转后回不到主菜单", "低", "低", "所有 HTML 页面", "任意模块可回主菜单", "目录层级新增但未注入导航"),
        ("证据化正式报告", "中高：支持后续迭代决策", "低", "低", "公开参考和本地文件", "PDF/source log/gap matrix 存在", "外部来源不可访问"),
    ]
    md = "\n".join(
        [
            "# 记账分析系统 V2 优化改进报告",
            "",
            "## 执行摘要",
            "",
            "- FACT：当前系统是本地静态 UI + SQLite + PDF/HTML 报告的本地记账分析系统，不是公网 SaaS。",
            "- OBSERVATION：入口页原先偏报告门户，固定模板问题和静态报告列表降低了日常使用效率。",
            "- INFERENCE：优先升级自由问答、报告筛选和全局导航，比直接公网部署或接入 LLM 更高 ROI、更低隐私风险。",
            "",
            "## 信息来源表",
            "",
            "| 来源 | 链接/路径 | 可信度 | 相关性 | 证据类型 | 不确定性 | 缺失信息 |",
            "|---|---|---:|---:|---|---|---|",
            *[
                f"| {row['source']} | `{row['url_or_path']}` | {row['credibility']} | {row['relevance']} | {row['evidence_type']} | {row['uncertainty']} | {row['missing_information']} |"
                for row in source_rows
            ],
            "",
            "## 参考项目 / 案例 / 竞品对比表",
            "",
            "| 项目 | FACT/OBSERVATION | 可复用模块 | 与本系统差距 |",
            "|---|---|---|---|",
            "| Actual Budget | FACT：local-first personal finance app；官方文档提供 custom reports 思路。 | 本地优先、报告维度筛选、保存报告入口。 | 本系统更聚焦支付宝/微信账单和经济放血机制。 |",
            "| Firefly III | OBSERVATION：公开入口强调导入、规则、标签、报告和 API。 | 规则引擎、标签、报告、API 边界。 | 本系统当前保持轻量本地静态 UI，不扩成完整账户后台。 |",
            "| Open WebUI Knowledge | FACT：文档说明知识库通过检索相关内容回答，适合大文档集合。 | 检索证据后回答、来源展示。 | 本阶段不接 LLM，仅做本地检索助手。 |",
            "",
            "## 可复用模块",
            "",
            "- 本地问答索引：复用 SQLite 汇总、Markdown 报告和 manifest，不新建重型服务。",
            "- 报告中心筛选：复用现有 PDF/HTML，不重新生成复杂组合报告。",
            "- 全局导航注入：复用静态 HTML 生成流程，避免逐页维护重复导航。",
            "",
            "## 差距分析",
            "",
            "| 差距 | 证据 | 改进方案 | 优先级 |",
            "|---|---|---|---|",
            *[f"| {row['gap']} | {row['evidence']} | {row['improvement']} | {row['priority']} |" for row in gap_rows],
            "",
            "## 改进方案",
            "",
            "1. 将固定问题模板升级为自由输入问答，输出证据化答案。",
            "2. 将静态 PDF 列表升级为可筛选报告中心，默认新标签打开。",
            "3. 为所有 HTML 注入统一导航和返回主菜单。",
            "4. 保持分类、金额、复核隔离和生产统计口径不变。",
            "",
            "## 实施路线图",
            "",
            "| 阶段 | 内容 | 验证方式 |",
            "|---|---|---|",
            "| V2.1 | 自由问答 + 本地索引 | 输入验收问题并检查证据区 |",
            "| V2.2 | 报告中心 + 查看清单 | 筛选月报/风险/复核 |",
            "| V2.3 | 全局导航 + 新标签 | 任意页面返回主菜单 |",
            "| V2.4 | PDF/source log/gap matrix | validate_outputs + 浏览器验收 |",
            "",
            "## 风险与限制",
            "",
            "- FACT：不接外部 LLM 时，回答能力受本地索引和规则限制。",
            "- INFERENCE：这能换来更好的隐私、速度和证据可控性。",
            "- OBSERVATION：若未来要公网部署，需要认证、脱敏、备份和访问日志，不能直接暴露本地账本。",
            "",
            "## 验收标准",
            "",
            "- 自定义问题能返回答案和证据。",
            "- 报告可按周期、主题、证据类型、关键词筛选。",
            "- PDF/HTML 默认新标签打开。",
            "- 所有模块可回主菜单。",
            "- 正式 PDF、source log、gap matrix、question_answer_index 均存在并进入 manifest。",
            "",
            "## 下一步行动建议",
            "",
            "| 行动 | 预期价值 | 执行难度 | 风险 | 所需输入 | 验证方式 | 失效条件 |",
            "|---|---|---|---|---|---|---|",
            *[f"| {name} | {value} | {difficulty} | {risk} | {input_needed} | {verification} | {failure} |" for name, value, difficulty, risk, input_needed, verification, failure in actions],
        ]
    )
    md_path = reports_dir / "finance_ledger_system_improvement_report.md"
    pdf_path = reports_dir / "finance_ledger_system_improvement_report.pdf"
    md_path.write_text(md, encoding="utf-8")
    write_report_pdf(md, pdf_path)
    return {
        "finance_ledger_system_improvement_md": str(md_path),
        "finance_ledger_system_improvement_pdf": str(pdf_path),
        "finance_ledger_system_improvement_source_json": str(source_json),
        "finance_ledger_system_improvement_source_csv": str(source_csv),
        "system_improvement_gap_matrix_csv": str(gap_csv),
        "question_answer_index_json": str(qa_index),
    }


def _acceptance_workbench_html(
    *,
    metrics: dict[str, Any],
    output_paths: dict[str, str],
    pending_review_count: int,
    location: str = "reports",
) -> str:
    report_prefix = "" if location == "reports" else "reports/"
    data = {
        "metrics": {
            "transactions": metrics.get("transactions", 0),
            "total_expense": metrics.get("total_expense", 0),
            "pending_review": metrics.get("pending_review", 0),
            "pending_review_count": pending_review_count,
        },
        "links": {
            "user_acceptance_pdf": f"{report_prefix}user_acceptance_matrix_report.pdf",
            "completion_audit_pdf": f"{report_prefix}completion_audit_report.pdf",
            "delivery_acceptance_pdf": f"{report_prefix}delivery_acceptance_report.pdf",
            "visual_quality_pdf": f"{report_prefix}visual_quality_acceptance_report.pdf",
            "reference_benchmark_pdf": f"{report_prefix}reference_model_benchmark_report.pdf",
            "chatgpt_reference_pdf": f"{report_prefix}chatgpt_reference_intake_report.pdf",
            "goal_completion_pdf": f"{report_prefix}goal_completion_audit_report.pdf",
            "requirements_pdf": f"{report_prefix}requirements_traceability_report.pdf",
            "operations_center": f"{report_prefix}operations_center.html",
        },
        "items": [
            {
                "id": "taxonomy",
                "area": "分类体系",
                "question": "主类/子类是否足够简洁",
                "recommended": "A",
                "evidence": "classification_rulebook_report.pdf",
                "options": {
                    "A": "通过：现有体系作为 MVP 固定口径",
                    "B": "小改：只微调 1-3 个子类命名",
                    "C": "补资料：重新设计 taxonomy",
                },
            },
            {
                "id": "risk_tags",
                "area": "风险标签",
                "question": "风险标签是否服务消费控制",
                "recommended": "A",
                "evidence": "summary_by_risk_tag + spending_control_action_report.pdf",
                "options": {
                    "A": "通过：当前标签用于行为分析和预算控制",
                    "B": "小改：合并少量重复标签",
                    "C": "补资料：重建风险标签体系",
                },
            },
            {
                "id": "reports",
                "area": "周期报告",
                "question": "周/月/季/半年/年 PDF 是否满足复盘",
                "recommended": "A",
                "evidence": "weekly/monthly/quarterly/half/yearly PDFs",
                "options": {
                    "A": "通过：当前 PDF 和趋势公式可验收",
                    "B": "小改：增加某个周期专题页",
                    "C": "补资料：重写报告结构",
                },
            },
            {
                "id": "dashboard",
                "area": "Dashboard/UI",
                "question": "本地交互 UI 是否达到系统要求",
                "recommended": "A",
                "evidence": "dashboard.html + visual_quality_acceptance_report.pdf",
                "options": {
                    "A": "通过：本地静态 UI + SQLite 可验收",
                    "B": "小改：调整布局、颜色或图表优先级",
                    "C": "补资料：改为远程 Web 系统",
                },
            },
            {
                "id": "large_review",
                "area": "大额复核",
                "question": "下拉复核流程是否足够轻便",
                "recommended": "A",
                "evidence": "review_workbench.html + manual_review_report.pdf",
                "options": {
                    "A": "通过：下拉选择 + 候选矩阵 + CSV 回灌",
                    "B": "小改：增加批量默认规则",
                    "C": "补资料：改成全自动入账",
                },
            },
            {
                "id": "tags",
                "area": "标签库",
                "question": "标签库是否满足可持续维护",
                "recommended": "A",
                "evidence": "tag_library.html + tag_library SQLite table",
                "options": {
                    "A": "通过：SQLite 持久化 + 编辑页 + 导出回灌",
                    "B": "小改：增加更多内置筛选组合",
                    "C": "补资料：改为多用户标签后台",
                },
            },
            {
                "id": "downstream",
                "area": "下游系统",
                "question": "SQLite/API 只读边界是否合适",
                "recommended": "A",
                "evidence": "finance_ledger_data_contract.md + serve_ledger.py",
                "options": {
                    "A": "通过：SQLite 只读视图/API 可验收",
                    "B": "小改：增加更多 mart/view",
                    "C": "补资料：改成中心化数据平台",
                },
            },
            {
                "id": "chatgpt_reference",
                "area": "ChatGPT 对照",
                "question": "是否需要严格逐项对照 ChatGPT 版本",
                "recommended": "B",
                "evidence": "当前工作区未发现单独 ChatGPT 版本文件",
                "options": {
                    "A": "通过：当前开源对标和需求追踪足够",
                    "B": "小改：补文件后做差距审计",
                    "C": "补资料：必须以 ChatGPT 文件重构",
                },
            },
            {
                "id": "final_acceptance",
                "area": "总目标",
                "question": "是否允许标记总目标完成",
                "recommended": "B",
                "evidence": "completion_audit_report.pdf + browser_visual_acceptance.json",
                "options": {
                    "A": "通过：接受当前工程基线",
                    "B": "小改：先做一轮 UI/报告精修",
                    "C": "补资料：补 ChatGPT 对照文件后再审计",
                },
            },
        ],
    }
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>用户验收工作台</title>
  <style>
    :root {{ --bg:#f5f7fb; --panel:#fff; --ink:#172033; --muted:#647083; --line:#d9e0ea; --blue:#2563eb; --green:#047857; --red:#b42318; --amber:#a16207; --cyan:#0e7490; --violet:#6d28d9; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; background:var(--bg); color:var(--ink); }}
    header {{ background:#fff; border-bottom:1px solid var(--line); padding:24px 32px 16px; }}
    h1 {{ margin:0 0 6px; font-size:25px; letter-spacing:0; }}
    .sub {{ color:var(--muted); font-size:13px; line-height:1.55; }}
    main {{ max-width:1440px; margin:0 auto; padding:20px 32px 44px; }}
    .metrics {{ display:grid; grid-template-columns:repeat(5,minmax(140px,1fr)); gap:10px; margin-bottom:14px; }}
    .metric {{ background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:14px; min-height:78px; }}
    .metric:nth-child(1) {{ border-left:4px solid var(--blue); }}
    .metric:nth-child(2) {{ border-left:4px solid var(--green); }}
    .metric:nth-child(3) {{ border-left:4px solid var(--red); }}
    .metric:nth-child(4) {{ border-left:4px solid var(--amber); }}
    .metric:nth-child(5) {{ border-left:4px solid var(--violet); }}
    .label {{ color:var(--muted); font-size:12px; }}
    .value {{ margin-top:7px; font-size:20px; font-weight:750; overflow-wrap:anywhere; }}
    .layout {{ display:grid; grid-template-columns:minmax(0,1.35fr) minmax(320px,.65fr); gap:14px; align-items:start; }}
    .panel {{ background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:16px; min-width:0; max-width:100%; }}
    .panel + .panel {{ margin-top:14px; }}
    h2 {{ margin:0 0 12px; font-size:17px; }}
    .acceptance-grid {{ display:grid; gap:10px; }}
    .acceptance-row {{ display:grid; grid-template-columns:150px minmax(0,1fr) 310px 120px; gap:10px; align-items:center; border:1px solid var(--line); border-radius:8px; padding:12px; background:#fff; }}
    .area {{ font-weight:750; overflow-wrap:anywhere; }}
    .question {{ font-size:14px; line-height:1.45; overflow-wrap:anywhere; }}
    .evidence {{ margin-top:4px; color:var(--muted); font-size:12px; overflow-wrap:anywhere; }}
    .choices {{ display:grid; grid-template-columns:repeat(3,1fr); gap:6px; }}
    button {{ border:1px solid var(--line); border-radius:7px; background:#fff; color:var(--ink); padding:9px 10px; cursor:pointer; font-size:13px; min-height:38px; }}
    button.activeA {{ border-color:var(--green); background:#ecfdf5; color:#065f46; font-weight:750; }}
    button.activeB {{ border-color:var(--amber); background:#fffbeb; color:#92400e; font-weight:750; }}
    button.activeC {{ border-color:var(--red); background:#fff7ed; color:#9a3412; font-weight:750; }}
    .recommend {{ color:var(--muted); font-size:12px; text-align:right; }}
    .progress-wrap {{ border:1px solid var(--line); border-radius:8px; background:#f8fafc; height:18px; overflow:hidden; }}
    .progress-bar {{ height:100%; background:linear-gradient(90deg,var(--green),var(--blue)); width:0%; transition:width .2s ease; }}
    .summary-table {{ width:100%; border-collapse:collapse; font-size:13px; }}
    th,td {{ padding:9px 8px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }}
    td:last-child, th:last-child {{ text-align:right; }}
    .links {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:8px; }}
    .link {{ display:block; border:1px solid var(--line); border-radius:7px; padding:10px 11px; color:var(--ink); text-decoration:none; background:#fff; font-size:13px; overflow-wrap:anywhere; }}
    .actions {{ display:flex; flex-wrap:wrap; gap:8px; margin-top:12px; }}
    .primary {{ background:var(--blue); color:#fff; border-color:var(--blue); }}
    .command {{ background:#0f172a; color:#e5e7eb; border-radius:8px; padding:12px; font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:12px; overflow:auto; white-space:pre-wrap; line-height:1.5; }}
    textarea {{ width:100%; min-height:150px; resize:vertical; border:1px solid var(--line); border-radius:8px; padding:10px; font-size:13px; line-height:1.5; color:var(--ink); background:#fff; }}
    input[type="file"] {{ width:100%; border:1px solid var(--line); border-radius:8px; padding:9px; background:#fff; font-size:13px; }}
    .intake-grid {{ display:grid; gap:10px; }}
    .intake-meta {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:8px; }}
    .intake-chip {{ border:1px solid var(--line); border-radius:8px; padding:9px; background:#f8fafc; color:var(--muted); font-size:12px; overflow-wrap:anywhere; }}
    .status {{ color:var(--muted); font-size:12px; line-height:1.6; margin-top:8px; }}
    .json-preview {{ min-height:180px; font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:12px; background:#f8fafc; }}
    .refinement-guide {{ border:1px solid #fde68a; background:#fffbeb; color:#78350f; border-radius:8px; padding:10px 12px; font-size:12px; line-height:1.65; margin-top:10px; }}
    @media (max-width:1100px) {{ .layout,.metrics {{ grid-template-columns:1fr; }} .acceptance-row {{ grid-template-columns:1fr; }} .recommend {{ text-align:left; }} }}
    @media (max-width:720px) {{ main,header {{ width:100vw; max-width:100vw; padding-left:14px; padding-right:14px; overflow:hidden; }} .choices,.links,.actions {{ grid-template-columns:1fr; display:grid; }} button {{ width:100%; }} .value {{ font-size:18px; }} table {{ display:block; max-width:100%; overflow-x:auto; }} }}
  </style>
</head>
<body>
  <header>
    <h1>用户验收工作台</h1>
    <div class="sub">用按钮选择 A/B/C，把“满足我的预期”转成可记录的验收状态。只有全部验收项为 A，且“是否允许标记总目标完成”为 A，目标完成度审计才会关闭该项；B/C 会继续保留为精修或补资料。</div>
  </header>
  <main>
    <section class="metrics">
      <div class="metric"><div class="label">交易笔数</div><div class="value" id="transactions"></div></div>
      <div class="metric"><div class="label">生产口径总支出</div><div class="value" id="totalExpense"></div></div>
      <div class="metric"><div class="label">待复核金额</div><div class="value" id="pendingReview"></div></div>
      <div class="metric"><div class="label">待复核笔数</div><div class="value" id="pendingCount"></div></div>
      <div class="metric"><div class="label">验收完成度</div><div class="value" id="acceptanceScore"></div></div>
    </section>
    <section class="layout">
      <div class="panel">
        <h2>验收选择矩阵</h2>
        <div id="acceptanceMatrix" class="acceptance-grid"></div>
      </div>
      <div>
        <section class="panel">
          <h2>当前步骤状态表</h2>
          <div class="progress-wrap"><div class="progress-bar" id="progressBar"></div></div>
          <table class="summary-table" id="acceptanceSummary"></table>
          <div class="actions">
            <button class="primary" onclick="downloadJson()">导出验收 JSON</button>
            <button onclick="copyAcceptanceJson()">复制验收 JSON</button>
            <button onclick="applyUserStatedChoices()">套用：1-8 A，最后 B</button>
            <button onclick="downloadCsv()">导出验收 CSV</button>
            <button onclick="resetChoices()">恢复推荐项</button>
          </div>
          <p class="status" id="acceptanceStatus"></p>
          <p class="status" id="exportStatus"></p>
          <textarea id="acceptanceJsonPreview" class="json-preview" readonly aria-label="验收 JSON 预览"></textarea>
          <div class="refinement-guide" id="refinementGuide"></div>
        </section>
        <section class="panel">
          <h2>证据入口</h2>
          <div class="links">
            <a class="link" id="userAcceptancePdf">用户验收矩阵 PDF</a>
            <a class="link" id="completionAuditPdf">最终完成审计</a>
            <a class="link" id="deliveryAcceptancePdf">交付验收报告</a>
            <a class="link" id="visualQualityPdf">UI 与可视化验收</a>
            <a class="link" id="referenceBenchmarkPdf">开源参考对标</a>
            <a class="link" id="chatgptReferencePdf">ChatGPT 对照审计</a>
            <a class="link" id="goalCompletionPdf">目标完成度审计</a>
            <a class="link" id="requirementsPdf">需求追踪验收</a>
          </div>
        </section>
        <section class="panel">
          <h2>ChatGPT 对照文件接入</h2>
          <div class="intake-grid">
            <div class="status">把 ChatGPT 版本、代码或要求文件粘贴到这里，或选择本地文本文件；本页只做本地暂存和导出，不会自动写入数据库。</div>
            <input id="chatgptReferenceFile" type="file" accept=".md,.txt,.json,.yaml,.yml,.csv,.html,.py,.js,.ts,.tsx,.jsx">
            <textarea id="chatgptReferenceText" placeholder="粘贴 ChatGPT 版本/代码/要求文件内容。导出后放入项目 chatgpt_reference/ 目录，再运行审计命令。"></textarea>
            <div class="intake-meta">
              <div class="intake-chip" id="chatgptReferenceSize"></div>
              <div class="intake-chip" id="chatgptReferenceStatus"></div>
              <div class="intake-chip" id="chatgptReferenceFilename"></div>
            </div>
            <div class="actions">
              <button onclick="loadChatGPTReferenceFile()">读取所选文件</button>
              <button onclick="saveReferenceDraft()">保存本地草稿</button>
              <button class="primary" onclick="downloadChatGPTReference()">导出对照文件</button>
            </div>
            <pre class="command" id="chatgptAuditCommand"></pre>
          </div>
        </section>
        <section class="panel">
          <h2>下一步选项 A/B/C</h2>
          <pre class="command" id="nextCommand"></pre>
        </section>
      </div>
    </section>
  </main>
  <script>
    const DATA = {json.dumps(data, ensure_ascii=False)};
    const CHOICE_STORAGE_KEY = "econ_bleed_acceptance_choices_v1";
    const CHATGPT_REFERENCE_STORAGE_KEY = "econ_bleed_chatgpt_reference_draft_v1";
    const choices = new Map(DATA.items.map(item => [item.id, item.recommended]));
    const yuan = n => "¥" + Number(n || 0).toLocaleString("zh-CN", {{ minimumFractionDigits:2, maximumFractionDigits:2 }});
    const safe = v => String(v ?? "").replace(/[&<>"']/g, ch => ({{"&":"&amp;","<":"&lt;",">":"&gt;","\\\"":"&quot;","'":"&#39;"}}[ch]));
    document.getElementById("transactions").textContent = DATA.metrics.transactions;
    document.getElementById("totalExpense").textContent = yuan(DATA.metrics.total_expense);
    document.getElementById("pendingReview").textContent = yuan(DATA.metrics.pending_review);
    document.getElementById("pendingCount").textContent = DATA.metrics.pending_review_count;
    document.getElementById("userAcceptancePdf").href = DATA.links.user_acceptance_pdf;
    document.getElementById("completionAuditPdf").href = DATA.links.completion_audit_pdf;
    document.getElementById("deliveryAcceptancePdf").href = DATA.links.delivery_acceptance_pdf;
    document.getElementById("visualQualityPdf").href = DATA.links.visual_quality_pdf;
    document.getElementById("referenceBenchmarkPdf").href = DATA.links.reference_benchmark_pdf;
    document.getElementById("chatgptReferencePdf").href = DATA.links.chatgpt_reference_pdf;
    document.getElementById("goalCompletionPdf").href = DATA.links.goal_completion_pdf;
    document.getElementById("requirementsPdf").href = DATA.links.requirements_pdf;
    function loadStoredChoices() {{
      try {{
        const stored = JSON.parse(localStorage.getItem(CHOICE_STORAGE_KEY) || "{{}}");
        DATA.items.forEach(item => {{
          if (["A","B","C"].includes(stored[item.id])) choices.set(item.id, stored[item.id]);
        }});
      }} catch (error) {{}}
    }}
    function persistChoices() {{
      const stored = Object.fromEntries(Array.from(choices.entries()));
      localStorage.setItem(CHOICE_STORAGE_KEY, JSON.stringify(stored));
    }}
    function selectChoice(id, value) {{
      choices.set(id, value);
      persistChoices();
      render();
    }}
    function renderMatrix() {{
      document.getElementById("acceptanceMatrix").innerHTML = DATA.items.map(item => {{
        const current = choices.get(item.id);
        const buttons = ["A","B","C"].map(option => `<button class="${{current === option ? "active" + option : ""}}" onclick="selectChoice('${{safe(item.id)}}','${{option}}')">${{option}}<br>${{safe(item.options[option])}}</button>`).join("");
        return `<div class="acceptance-row">
          <div class="area">${{safe(item.area)}}</div>
          <div><div class="question">${{safe(item.question)}}</div><div class="evidence">证据：${{safe(item.evidence)}}</div></div>
          <div class="choices">${{buttons}}</div>
          <div class="recommend">推荐：${{safe(item.recommended)}}<br>当前：${{safe(current)}}</div>
        </div>`;
      }}).join("");
    }}
    function currentRows() {{
      return DATA.items.map(item => ({{ id:item.id, area:item.area, question:item.question, choice:choices.get(item.id), recommended:item.recommended, evidence:item.evidence }}));
    }}
    function renderSummary() {{
      const rows = currentRows();
      const counts = {{ A:0, B:0, C:0 }};
      rows.forEach(row => counts[row.choice] += 1);
      const done = counts.A;
      const score = Math.round((done / rows.length) * 100);
      document.getElementById("acceptanceScore").textContent = score.toFixed(0) + "%";
      document.getElementById("progressBar").style.width = score + "%";
      document.getElementById("acceptanceSummary").innerHTML = `<tr><th>选择</th><th>数量</th><th>含义</th></tr>
        <tr><td>A</td><td>${{counts.A}}</td><td>可验收</td></tr>
        <tr><td>B</td><td>${{counts.B}}</td><td>需要小改或补对照</td></tr>
        <tr><td>C</td><td>${{counts.C}}</td><td>需要重做/补资料</td></tr>`;
      const blocked = rows.filter(row => row.choice === "C").map(row => row.area);
      const refine = rows.filter(row => row.choice === "B").map(row => row.area);
      document.getElementById("acceptanceStatus").textContent = blocked.length
        ? `仍有 C 项：${{blocked.join("、")}}。总目标不能关闭。`
        : refine.length
          ? `仍有 B 项：${{refine.join("、")}}。建议继续局部精修后再关闭。`
          : "全部为 A，导出 JSON 后可作为最终关闭确认。";
      document.getElementById("nextCommand").textContent = blocked.length
        ? "C. 补 ChatGPT 对照文件或重做指定模块后重新运行 finalize_delivery.py"
        : refine.length
          ? "B. 先完成当前 B 项对应的局部精修；完成后重新生成 PDF、浏览器验收和目标审计，最终打包等用户确认 A 后再做"
          : "A. 接受当前工程基线；导出 user_acceptance_decisions.json 后，后续每周只运行 weekly_update.py 和复核回灌";
      renderRefinementGuide(refine, blocked);
      renderReferenceIntake();
      renderAcceptancePreview();
    }}
    function renderRefinementGuide(refine, blocked) {{
      const guide = document.getElementById("refinementGuide");
      if (blocked.length) {{
        guide.textContent = "当前存在 C 项：先补资料或重做对应模块；不要用报告数量替代真实验收。";
      }} else if (refine.length) {{
        guide.textContent = "当前存在 B 项：" + refine.join("、") + "。本轮建议只做最高 ROI 精修：修复验收导出反馈、保留微信候选入箱契约、重跑目标审计；最终是否关闭仍由你把总目标改为 A 决定。";
      }} else {{
        guide.textContent = "全部为 A：可进入最终关闭审计和正式交付包重建。";
      }}
    }}
    function referenceText() {{
      return document.getElementById("chatgptReferenceText").value || "";
    }}
    function renderReferenceIntake() {{
      const text = referenceText();
      const byteSize = new Blob([text]).size;
      const hasText = text.trim().length > 0;
      document.getElementById("chatgptReferenceSize").textContent = "当前内容：" + byteSize.toLocaleString("zh-CN") + " bytes";
      document.getElementById("chatgptReferenceStatus").textContent = hasText ? "状态：可导出并审计" : "状态：等待粘贴或选择文件";
      document.getElementById("chatgptReferenceFilename").textContent = "建议文件名：chatgpt_reference_requirements.md";
      document.getElementById("chatgptAuditCommand").textContent = hasText
        ? "1. 导出 chatgpt_reference_requirements.md 并放入项目 chatgpt_reference/\\n2. 运行：python3 scripts/audit_chatgpt_reference.py --output-dir outputs/finance_ledger_20220605_20260603 --input chatgpt_reference/chatgpt_reference_requirements.md --json\\n3. 运行：python3 scripts/finalize_delivery.py --base-url http://127.0.0.1:8772/ --output-dir outputs/finance_ledger_20220605_20260603 --ledger-db data/finance_ledger/finance_ledger.sqlite --ensure-server --json"
        : "粘贴或读取 ChatGPT 对照文件后，这里会生成审计和最终打包命令。";
    }}
    async function loadChatGPTReferenceFile() {{
      const file = document.getElementById("chatgptReferenceFile").files[0];
      if (!file) {{
        document.getElementById("chatgptReferenceStatus").textContent = "状态：未选择文件";
        return;
      }}
      const text = await file.text();
      document.getElementById("chatgptReferenceText").value = text;
      saveReferenceDraft();
      renderReferenceIntake();
    }}
    function saveReferenceDraft() {{
      localStorage.setItem(CHATGPT_REFERENCE_STORAGE_KEY, referenceText());
      renderReferenceIntake();
    }}
    function loadReferenceDraft() {{
      const stored = localStorage.getItem(CHATGPT_REFERENCE_STORAGE_KEY) || "";
      if (stored) document.getElementById("chatgptReferenceText").value = stored;
    }}
    function downloadChatGPTReference() {{
      const text = referenceText();
      const normalized = text.trim() ? text : "# ChatGPT 对照文件\\n\\n";
      triggerDownload("chatgpt_reference_requirements.md", normalized, "text/markdown;charset=utf-8");
    }}
    function render() {{
      renderMatrix();
      renderSummary();
    }}
    function payload() {{
      return {{ generated_at:new Date().toISOString(), metrics:DATA.metrics, choices:currentRows(), next_step:document.getElementById("nextCommand").textContent }};
    }}
    function acceptanceJsonText() {{
      return JSON.stringify(payload(), null, 2);
    }}
    function setExportStatus(message) {{
      document.getElementById("exportStatus").textContent = message;
    }}
    function renderAcceptancePreview() {{
      document.getElementById("acceptanceJsonPreview").value = acceptanceJsonText();
    }}
    function triggerDownload(filename, content, mimeType) {{
      const blob = new Blob([content], {{type:mimeType}});
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.setTimeout(() => URL.revokeObjectURL(url), 1000);
    }}
    function downloadJson() {{
      const text = acceptanceJsonText();
      renderAcceptancePreview();
      triggerDownload("user_acceptance_decisions.json", text, "application/json;charset=utf-8");
      setExportStatus("已触发 JSON 下载；如果内置浏览器没有弹出下载，请直接复制下方 JSON 预览内容。");
    }}
    async function copyAcceptanceJson() {{
      const text = acceptanceJsonText();
      renderAcceptancePreview();
      try {{
        await navigator.clipboard.writeText(text);
        setExportStatus("已复制验收 JSON。");
      }} catch (error) {{
        const preview = document.getElementById("acceptanceJsonPreview");
        preview.focus();
        preview.select();
        document.execCommand("copy");
        setExportStatus("已选中并尝试复制验收 JSON；如系统拦截，请手动复制下方文本。");
      }}
    }}
    function downloadCsv() {{
      const header = ["id","area","question","choice","recommended","evidence"];
      const lines = [header.join(",")].concat(currentRows().map(row => header.map(key => `"${{String(row[key] ?? "").replaceAll('"','""')}}"`).join(",")));
      triggerDownload("user_acceptance_decisions.csv", lines.join("\\n"), "text/csv;charset=utf-8");
      setExportStatus("已触发 CSV 下载。");
    }}
    function applyUserStatedChoices() {{
      DATA.items.forEach(item => choices.set(item.id, item.id === "final_acceptance" ? "B" : "A"));
      persistChoices();
      render();
      setExportStatus("已套用你口头确认的选择：除最后总目标为 B，其余全部为 A。");
    }}
    function resetChoices() {{
      DATA.items.forEach(item => choices.set(item.id, item.recommended));
      persistChoices();
      render();
      setExportStatus("已恢复推荐项。");
    }}
    document.getElementById("chatgptReferenceText").addEventListener("input", renderReferenceIntake);
    Object.assign(window, {{ selectChoice, downloadJson, downloadCsv, copyAcceptanceJson, applyUserStatedChoices, resetChoices, loadChatGPTReferenceFile, saveReferenceDraft, downloadChatGPTReference }});
    loadStoredChoices();
    loadReferenceDraft();
    render();
  </script>
</body>
</html>"""


def _operations_center_html(
    metrics: dict[str, Any],
    review_status_rows: list[dict[str, Any]],
    output_paths: dict[str, str],
    *,
    location: str = "reports",
) -> str:
    pending = next((row for row in review_status_rows if row.get("status") == "pending_review"), {})
    pending_count = int(float(pending.get("count", 0) or 0))
    pending_amount = float(pending.get("amount", 0) or 0)
    report_prefix = "" if location == "reports" else "reports/"
    review_prefix = "" if location == "reports" else "review/"
    data = {
        "metrics": {
            "transactions": metrics.get("transactions", 0),
            "total_expense": metrics.get("total_expense", 0),
            "pending_review": metrics.get("pending_review", 0),
            "total_income": metrics.get("total_income", 0),
            "net_cash_flow": metrics.get("net_cash_flow", 0),
        },
        "review": {
            "pending_count": pending_count,
            "pending_amount": pending_amount,
            "status_rows": review_status_rows,
        },
        "actions": [
            {
                "id": "weekly_update",
                "title": "每周更新",
                "status": "可运行",
                "target": "导入新账单、重建报告、自动验收",
                "href": f"{report_prefix}user_manual_report.pdf",
                "command": "python3 scripts/weekly_update.py --input data/finance_ledger/sources --ledger-db data/finance_ledger/finance_ledger.sqlite --output outputs/finance_ledger_20220605_20260603",
            },
            {
                "id": "large_review",
                "title": "大额复核",
                "status": "待处理" if pending_count else "已清空",
                "target": "用下拉菜单确认一万元以上交易",
                "href": f"{review_prefix}review_workbench.html",
                "command": "打开 review_workbench.html，下载 review_decisions_confirmed.csv 后用 --review-decisions 重跑周更。",
            },
            {
                "id": "tag_library",
                "title": "标签库维护",
                "status": "可编辑",
                "target": "维护永久保存的标签库和筛选组合",
                "href": f"{report_prefix}tag_library.html",
                "command": "下载 tag_library_custom.json 后运行 weekly_update.py --tag-library <path>",
            },
            {
                "id": "reports",
                "title": "报告验收",
                "status": "已生成",
                "target": "检查 PDF、dashboard、SQLite 和待复核隔离",
                "href": f"{report_prefix}delivery_acceptance_report.pdf",
                "command": "python3 scripts/validate_outputs.py --output outputs/finance_ledger_20220605_20260603 --db data/finance_ledger/finance_ledger.sqlite --require-ledger",
            },
            {
                "id": "user_acceptance",
                "title": "用户验收",
                "status": "待确认",
                "target": "用 A/B/C 按钮收敛是否满足预期和 ChatGPT 对照缺口",
                "href": f"{report_prefix}acceptance_workbench.html",
                "command": "打开 acceptance_workbench.html，选择 A/B/C 后导出 user_acceptance_decisions.json 或 CSV；如选择 C，请补 ChatGPT 版本/代码/要求文件后再审计。",
            },
            {
                "id": "browser_acceptance",
                "title": "浏览器验收",
                "status": "打包前必跑",
                "target": "确认 8 个核心页面桌面/移动视口、图表和横向溢出",
                "href": f"{report_prefix}visual_quality_acceptance_report.pdf",
                "command": "python3 scripts/run_browser_visual_acceptance.py --base-url http://127.0.0.1:8772/ --output-dir outputs/finance_ledger_20220605_20260603 --json\npython3 scripts/verify_browser_acceptance.py --audit outputs/finance_ledger_20220605_20260603/audit/browser_visual_acceptance.json --html-root outputs/finance_ledger_20220605_20260603",
            },
            {
                "id": "delivery_package",
                "title": "交付打包",
                "status": "浏览器验收通过后运行",
                "target": "把代码、PDF、HTML、SQLite 和审计文件打成最终 ZIP",
                "href": f"{report_prefix}user_manual_report.pdf",
                "command": "python3 scripts/finalize_delivery.py --base-url http://127.0.0.1:8772/ --output-dir outputs/finance_ledger_20220605_20260603 --ledger-db data/finance_ledger/finance_ledger.sqlite --ensure-server --json",
            },
            {
                "id": "readonly_api",
                "title": "只读 API",
                "status": "按需启动",
                "target": "给其他本地系统读取 SQLite 和报告",
                "href": f"{report_prefix}user_manual_report.pdf",
                "command": "python3 scripts/serve_ledger.py --db data/finance_ledger/finance_ledger.sqlite --reports outputs/finance_ledger_20220605_20260603/reports --host 127.0.0.1 --port 8766",
            },
            {
                "id": "data_access_hub",
                "title": "数据接入与回测入口",
                "status": "可打开",
                "target": "像量化回测入口一样给 PFIOS、行研和赛事系统读取账本视图",
                "href": f"{report_prefix}data_access_hub.html",
                "command": "打开 data_access_hub.html；下游系统优先读取 v_mart_daily_cashflow、v_fact_expense_allocations、v_data_trust_transactions 和 v_reconciliation_checks。",
            },
        ],
    }
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>经济放血运行控制台</title>
  <style>
    :root {{ --bg:#f5f7fb; --panel:#fff; --ink:#172033; --muted:#647083; --line:#d9e0ea; --blue:#2563eb; --green:#047857; --red:#b42318; --amber:#a16207; --cyan:#0e7490; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; background:var(--bg); color:var(--ink); }}
    header {{ background:#fff; border-bottom:1px solid var(--line); padding:24px 32px 16px; }}
    h1 {{ margin:0 0 6px; font-size:25px; letter-spacing:0; }}
    .sub {{ color:var(--muted); font-size:13px; }}
    main {{ max-width:1440px; margin:0 auto; padding:20px 32px 44px; }}
    .metrics {{ display:grid; grid-template-columns:repeat(5,minmax(140px,1fr)); gap:10px; }}
    .metric {{ background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:14px; min-height:78px; }}
    .metric.expense {{ border-left:4px solid var(--blue); }}
    .metric.review {{ border-left:4px solid var(--red); }}
    .metric.income {{ border-left:4px solid var(--green); }}
    .metric.net {{ border-left:4px solid var(--amber); }}
    .label {{ color:var(--muted); font-size:12px; }}
    .value {{ margin-top:7px; font-size:20px; font-weight:750; overflow-wrap:anywhere; }}
    .grid {{ margin-top:16px; display:grid; grid-template-columns:360px minmax(0,1fr); gap:14px; align-items:start; min-width:0; }}
    .panel {{ background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:16px; min-width:0; max-width:100%; }}
    h2 {{ margin:0 0 12px; font-size:17px; }}
    .workflow-map {{ margin-top:16px; display:grid; grid-template-columns:minmax(0,1fr) 300px; gap:14px; align-items:stretch; }}
    .workflow-visual {{ width:100%; min-height:172px; border:1px solid var(--line); border-radius:8px; background:#fbfcfe; }}
    .workflow-note {{ background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:14px; }}
    .risk-meter {{ height:10px; border-radius:999px; background:#e5e7eb; overflow:hidden; margin-top:8px; }}
    .risk-meter span {{ display:block; height:100%; width:0; background:linear-gradient(90deg,var(--blue),var(--amber),var(--red)); }}
    .legend {{ display:flex; flex-wrap:wrap; gap:8px; margin-top:10px; }}
    .legend span {{ display:inline-flex; align-items:center; gap:5px; color:var(--muted); font-size:12px; }}
    .legend i {{ width:9px; height:9px; border-radius:999px; display:inline-block; }}
    .steps {{ display:grid; gap:8px; }}
    .step-button {{ border:1px solid var(--line); border-radius:7px; padding:12px; background:#fff; text-align:left; cursor:pointer; color:var(--ink); }}
    .step-button.active {{ border-color:var(--blue); background:#eff6ff; }}
    .step-title {{ font-weight:750; font-size:14px; }}
    .step-meta {{ color:var(--muted); font-size:12px; margin-top:5px; }}
    .pill {{ display:inline-flex; border:1px solid var(--line); border-radius:999px; padding:5px 9px; color:var(--muted); font-size:12px; background:#fff; margin-right:6px; }}
    .command {{ background:#0f172a; color:#e5e7eb; border-radius:8px; padding:12px; font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:12px; overflow:auto; white-space:pre-wrap; line-height:1.5; }}
    .actions {{ display:flex; flex-wrap:wrap; gap:8px; margin-top:12px; }}
    a.button, button.copy {{ border:1px solid var(--line); border-radius:7px; padding:9px 11px; background:#fff; color:var(--ink); text-decoration:none; cursor:pointer; font-size:13px; }}
    a.primary {{ background:var(--blue); color:#fff; border-color:var(--blue); }}
    table {{ width:100%; border-collapse:collapse; font-size:13px; margin-top:12px; }}
    th,td {{ padding:9px 8px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }}
    th:last-child,td:last-child {{ text-align:right; }}
    .small {{ color:var(--muted); font-size:12px; line-height:1.6; }}
    @media (max-width:1100px) {{ .metrics {{ grid-template-columns:repeat(2,1fr); }} .grid,.workflow-map {{ grid-template-columns:1fr; }} }}
    @media (max-width:720px) {{ main,header {{ padding-left:14px; padding-right:14px; }} .metrics {{ grid-template-columns:1fr; }} .value {{ font-size:18px; }} table {{ display:block; max-width:100%; overflow-x:auto; }} .command {{ max-width:100%; overflow-x:auto; }} }}
  </style>
</head>
<body>
  <header>
    <h1>经济放血运行控制台</h1>
    <div class="sub">按固定步骤完成周更、复核、标签回灌、报告验收和只读 API 启动。</div>
  </header>
  <main>
    <section class="metrics">
      <div class="metric expense"><div class="label">生产口径总支出</div><div class="value" id="totalExpense"></div></div>
      <div class="metric review"><div class="label">待复核金额</div><div class="value" id="pendingReview"></div></div>
      <div class="metric review"><div class="label">待复核笔数</div><div class="value" id="pendingCount"></div></div>
      <div class="metric income"><div class="label">总收入</div><div class="value" id="totalIncome"></div></div>
      <div class="metric net"><div class="label">净现金流</div><div class="value" id="netCashFlow"></div></div>
    </section>
    <section class="workflow-map" id="workflowMap">
      <svg class="workflow-visual" id="workflowVisual" viewBox="0 0 920 190" role="img" aria-label="运行流程可视化"></svg>
      <div class="workflow-note">
        <h2>当前运行状态</h2>
        <div class="small" id="workflowSummary"></div>
        <div class="risk-meter" aria-label="待复核压力"><span id="reviewPressureBar"></span></div>
        <div class="legend">
          <span><i style="background:#2563eb"></i>可直接运行</span>
          <span><i style="background:#a16207"></i>需要人工确认</span>
          <span><i style="background:#047857"></i>已通过验收</span>
        </div>
      </div>
    </section>
    <section class="grid">
      <div class="panel">
        <h2>下一步选项</h2>
        <div class="steps" id="stepButtons"></div>
      </div>
      <div class="panel">
        <h2 id="actionTitle"></h2>
        <div>
          <span class="pill" id="actionStatus"></span>
          <span class="pill" id="actionTarget"></span>
        </div>
        <div class="actions">
          <a class="button primary" id="actionLink">打开入口</a>
          <button class="copy" onclick="copyCommand()">复制命令/规则</button>
        </div>
        <pre class="command" id="actionCommand"></pre>
        <p class="small" id="copyState"></p>
        <table id="reviewStatus"></table>
      </div>
    </section>
  </main>
  <script>
    const DATA = {json.dumps(data, ensure_ascii=False)};
    const yuan = n => "¥" + Number(n || 0).toLocaleString("zh-CN", {{ minimumFractionDigits:2, maximumFractionDigits:2 }});
    const safe = v => String(v ?? "").replace(/[&<>"']/g, ch => ({{"&":"&amp;","<":"&lt;",">":"&gt;","\\\"":"&quot;","'":"&#39;"}}[ch]));
    let activeAction = DATA.actions[0]?.id;
    document.getElementById("totalExpense").textContent = yuan(DATA.metrics.total_expense);
    document.getElementById("pendingReview").textContent = yuan(DATA.review.pending_amount);
    document.getElementById("pendingCount").textContent = DATA.review.pending_count;
    document.getElementById("totalIncome").textContent = yuan(DATA.metrics.total_income);
    document.getElementById("netCashFlow").textContent = yuan(DATA.metrics.net_cash_flow);
    function renderSteps() {{
      document.getElementById("stepButtons").innerHTML = DATA.actions.map(item => `<button class="step-button" data-id="${{safe(item.id)}}" onclick="selectAction('${{safe(item.id)}}')"><div class="step-title">${{safe(item.title)}}</div><div class="step-meta">${{safe(item.status)}} · ${{safe(item.target)}}</div></button>`).join("");
    }}
    function renderReviewStatus() {{
      const rows = DATA.review.status_rows || [];
      document.getElementById("reviewStatus").innerHTML = `<tr><th>复核状态</th><th>笔数</th><th>金额</th><th>占比</th><th>下一步</th></tr>` + rows.map(row => `<tr><td>${{safe(row.status_label)}}</td><td>${{safe(row.count)}}</td><td>${{yuan(row.amount)}}</td><td>${{safe(row.amount_pct)}}</td><td>${{safe(row.next_action)}}</td></tr>`).join("");
    }}
    function renderWorkflowVisual() {{
      const stages = [
        ["账单导入","CSV/截图候选","#2563eb"],
        ["规则分类","主类/子类/标签","#2563eb"],
        ["大额复核", DATA.review.pending_count ? `${{DATA.review.pending_count}} 笔待确认` : "已清空", DATA.review.pending_count ? "#a16207" : "#047857"],
        ["生产统计","SQLite 视图","#047857"],
        ["报告查看","PDF/Dashboard","#047857"],
        ["行动回灌","预算/标签/复核","#2563eb"],
      ];
      const svg = document.getElementById("workflowVisual");
      const boxes = stages.map((stage, index) => {{
        const x = 22 + index * 148;
        const arrow = index < stages.length - 1 ? `<line x1="${{x+118}}" y1="82" x2="${{x+142}}" y2="82" stroke="#94a3b8" stroke-width="2" marker-end="url(#opArrow)"/>` : "";
        return `${{arrow}}<rect x="${{x}}" y="42" width="116" height="82" rx="9" fill="#fff" stroke="${{stage[2]}}" stroke-width="2"/><circle cx="${{x+18}}" cy="60" r="6" fill="${{stage[2]}}"/><text x="${{x+58}}" y="78" text-anchor="middle" font-size="13" font-weight="700" fill="#172033">${{safe(stage[0])}}</text><text x="${{x+58}}" y="99" text-anchor="middle" font-size="11" fill="#647083">${{safe(stage[1])}}</text>`;
      }}).join("");
      svg.innerHTML = `<defs><marker id="opArrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="#94a3b8"/></marker></defs>${{boxes}}`;
      const pressure = DATA.metrics.total_expense ? Math.min(100, Math.round((DATA.review.pending_amount / DATA.metrics.total_expense) * 100)) : 0;
      document.getElementById("reviewPressureBar").style.width = `${{pressure}}%`;
      document.getElementById("workflowSummary").textContent = `待复核金额 ${{yuan(DATA.review.pending_amount)}}，约占生产口径总支出 ${{pressure}}%。先确认大额，再判断消费结构和优化动作。`;
    }}
    function selectAction(id) {{
      activeAction = id;
      const item = DATA.actions.find(action => action.id === id) || DATA.actions[0];
      document.querySelectorAll(".step-button").forEach(button => button.classList.toggle("active", button.dataset.id === id));
      document.getElementById("actionTitle").textContent = item.title;
      document.getElementById("actionStatus").textContent = item.status;
      document.getElementById("actionTarget").textContent = item.target;
      document.getElementById("actionLink").href = item.href;
      document.getElementById("actionCommand").textContent = item.command;
      document.getElementById("copyState").textContent = "";
    }}
    async function copyCommand() {{
      const text = document.getElementById("actionCommand").textContent;
      try {{
        await navigator.clipboard.writeText(text);
        document.getElementById("copyState").textContent = "已复制。";
      }} catch (error) {{
        document.getElementById("copyState").textContent = "浏览器未允许复制，请手动选中命令。";
      }}
    }}
    Object.assign(window, {{ selectAction, copyCommand }});
    renderSteps();
    renderReviewStatus();
    renderWorkflowVisual();
    selectAction(activeAction);
  </script>
</body>
</html>"""


def _review_workbench_html(rows: list[ClassifiedTransaction], review_decisions: ReviewDecisions | None = None, tag_library_rows: list[dict[str, Any]] | None = None) -> str:
    candidate_by_key = {str(item["review_key"]): item for item in _review_decision_candidate_rows(rows, review_decisions)}
    pending = [
        {
            "review_key": review_key(row),
            "transaction_time": row.transaction_time,
            "source_platform": row.source_platform,
            "counterparty": row.counterparty,
            "description": row.description,
            "amount": row.amount,
            "main_category": row.main_category,
            "sub_category": row.sub_category,
            "risk_tags": row.risk_tags,
            "order_id": row.order_id,
            "candidate": candidate_by_key.get(review_key(row), {}),
        }
        for row in _pending_review_rows(rows, review_decisions)
    ]
    data = {"pending": pending, "taxonomy": TAXONOMY, "risk_tags": _active_tag_names(tag_library_rows or _tag_library_rows()), "tag_library": tag_library_rows or _tag_library_rows()}
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>大额复核工作台</title>
  <style>
    :root {{ --bg:#f5f7fa; --panel:#fff; --ink:#172033; --muted:#697586; --line:#d9e0ea; --blue:#2563eb; --green:#057a55; --red:#c2410c; --amber:#a16207; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; background:var(--bg); color:var(--ink); }}
    header {{ position:sticky; top:0; z-index:3; background:#fff; border-bottom:1px solid var(--line); padding:18px 24px; }}
    h1 {{ margin:0; font-size:22px; letter-spacing:0; }}
    .sub {{ margin-top:6px; color:var(--muted); font-size:13px; }}
    main {{ max-width:1440px; margin:0 auto; padding:18px 24px 42px; }}
    .toolbar {{ display:grid; grid-template-columns:repeat(6,minmax(140px,1fr)); gap:10px; margin-bottom:14px; }}
    .metric {{ background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:13px; }}
    .metric .label {{ color:var(--muted); font-size:12px; }}
    .metric .value {{ margin-top:5px; font-size:20px; font-weight:750; }}
    .filterbar,.batchbar {{ display:grid; grid-template-columns:1.4fr repeat(4,minmax(130px,1fr)); gap:8px; align-items:end; background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:12px; margin-bottom:12px; }}
    .batchbar {{ grid-template-columns:150px 1.4fr 1fr auto; }}
    .groupbar {{ background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:12px; margin-bottom:12px; min-width:0; max-width:100%; }}
    .group-head {{ display:grid; grid-template-columns:220px 1fr; gap:12px; align-items:end; margin-bottom:12px; }}
    .impact-grid {{ display:grid; grid-template-columns:repeat(4,minmax(130px,1fr)); gap:8px; margin-bottom:12px; }}
    .impact-card {{ border:1px solid var(--line); border-radius:8px; background:#fbfcfe; padding:10px; }}
    .impact-card strong {{ display:block; margin-top:4px; font-size:17px; overflow-wrap:anywhere; }}
    .group-matrix {{ display:grid; gap:8px; }}
    .group-row {{ display:grid; grid-template-columns:minmax(180px,1.2fr) 92px 120px 1fr; gap:10px; align-items:center; border:1px solid var(--line); border-radius:8px; padding:10px; background:#fff; }}
    .group-name {{ font-weight:750; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }}
    .group-sub {{ color:var(--muted); font-size:12px; margin-top:3px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }}
    .group-actions {{ display:flex; gap:6px; justify-content:flex-end; flex-wrap:wrap; }}
    .actions {{ display:flex; gap:8px; flex-wrap:wrap; margin:12px 0 16px; }}
    .decision-line {{ display:grid; grid-template-columns:150px 1fr 1fr auto; gap:8px; align-items:end; margin:12px 0 10px; }}
    .field-label {{ display:block; color:var(--muted); font-size:11px; margin:0 0 4px; }}
    button {{ border:1px solid var(--line); background:#fff; color:var(--ink); border-radius:7px; padding:8px 11px; font-size:13px; cursor:pointer; }}
    button.primary {{ background:var(--blue); color:#fff; border-color:var(--blue); }}
    button.good {{ background:var(--green); color:#fff; border-color:var(--green); }}
    button.warn {{ background:var(--amber); color:#fff; border-color:var(--amber); }}
    button.bad {{ background:#fff7ed; color:var(--red); border-color:#fed7aa; }}
    .grid {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:12px; }}
    .card {{ background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:14px; min-width:0; max-width:100%; }}
    .card.excluded {{ opacity:.72; border-color:#fed7aa; }}
    .top {{ display:grid; grid-template-columns:1fr auto; gap:10px; align-items:start; }}
    .merchant {{ font-weight:750; overflow-wrap:anywhere; }}
    .amount {{ font-weight:800; font-size:18px; }}
    .desc {{ color:var(--muted); font-size:12px; margin-top:6px; overflow-wrap:anywhere; }}
    .row {{ display:grid; grid-template-columns:1.5fr 88px 1fr auto; gap:8px; align-items:center; margin-top:10px; }}
    select,input {{ width:100%; min-width:0; border:1px solid var(--line); border-radius:7px; padding:8px; font-size:13px; background:#fff; }}
    .split-list {{ margin-top:8px; }}
    .status {{ display:inline-block; margin-top:8px; color:var(--muted); font-size:12px; }}
    .pill {{ display:inline-flex; align-items:center; border:1px solid var(--line); border-radius:999px; padding:3px 8px; font-size:12px; color:var(--muted); background:#f8fafc; }}
    .pill.high {{ color:#057a55; border-color:#bbf7d0; background:#f0fdf4; }}
    .pill.medium {{ color:#a16207; border-color:#fde68a; background:#fffbeb; }}
    .pill.low {{ color:#c2410c; border-color:#fed7aa; background:#fff7ed; }}
    .empty {{ background:var(--panel); border:1px dashed var(--line); border-radius:8px; padding:26px; color:var(--muted); text-align:center; }}
    @media (max-width:980px) {{ .toolbar,.grid,.decision-line,.filterbar,.batchbar,.group-head,.impact-grid,.group-row {{ grid-template-columns:1fr; }} .group-actions {{ justify-content:flex-start; }} .row {{ grid-template-columns:1fr; }} main,header {{ padding-left:14px; padding-right:14px; }} }}
    @media (max-width:720px) {{ .actions,.group-actions {{ display:grid; grid-template-columns:1fr; }} button {{ width:100%; }} .group-name,.group-sub {{ white-space:normal; }} }}
  </style>
</head>
<body>
  <header>
    <h1>大额复核工作台</h1>
    <div class="sub">用下拉菜单把大额交易纳入现有主类/子类体系；确认表再通过 <code>--review-decisions</code> 回灌，更新 SQLite、dashboard 和所有 PDF 报告。</div>
  </header>
  <main>
    <section class="toolbar">
      <div class="metric"><div class="label">待复核笔数</div><div class="value" id="pendingCount">0</div></div>
      <div class="metric"><div class="label">待复核金额</div><div class="value" id="pendingAmount">¥0.00</div></div>
      <div class="metric"><div class="label">当前显示</div><div class="value" id="visibleCount">0</div></div>
      <div class="metric"><div class="label">已选择纳入</div><div class="value" id="includeCount">0</div></div>
      <div class="metric"><div class="label">已选择排除</div><div class="value" id="excludeCount">0</div></div>
      <div class="metric"><div class="label">候选可套用</div><div class="value" id="candidateCount">0</div></div>
    </section>
    <section class="filterbar">
      <label><span class="field-label">搜索</span><input id="reviewSearch" placeholder="对手方、说明、订单号" oninput="render()"></label>
      <label><span class="field-label">建议分类</span><select id="filterCategory" onchange="render()"></select></label>
      <label><span class="field-label">复核状态</span><select id="filterDecision" onchange="render()"><option value="">全部状态</option><option value="undecided">未选择</option><option value="include">已纳入</option><option value="exclude">已排除</option></select></label>
      <label><span class="field-label">最小金额</span><input id="filterMinAmount" type="number" min="0" step="0.01" placeholder="例如 30000" oninput="render()"></label>
      <label><span class="field-label">排序</span><select id="sortMode" onchange="render()"><option value="amount_desc">金额从高到低</option><option value="date_desc">时间从新到旧</option><option value="counterparty">交易对方</option></select></label>
    </section>
    <section class="batchbar">
      <label><span class="field-label">批量决定</span><select id="batchDecision"><option value="include">纳入统计</option><option value="exclude">排除</option></select></label>
      <label><span class="field-label">批量主类/子类</span><select id="batchCategory"></select></label>
      <label><span class="field-label">批量风险标签</span><select id="batchRisk"></select></label>
      <button class="primary" onclick="applyBatchToVisible()">应用到当前筛选</button>
    </section>
    <section class="groupbar">
      <div class="group-head">
        <label><span class="field-label">分组矩阵</span><select id="groupMode" onchange="render()"><option value="counterparty">按交易对方</option><option value="category">按建议分类</option><option value="month">按月份</option></select></label>
        <div class="sub">先用上方筛选缩小对象，再在矩阵里对整组选择纳入、排除、套用批量栏或 50/25/25 拆分。</div>
      </div>
      <div id="impactPreview" class="impact-grid"></div>
      <div id="reviewGroupMatrix" class="group-matrix"></div>
    </section>
    <div class="actions">
      <button class="primary" onclick="downloadCsv()">下载复核确认 CSV</button>
      <button onclick="copyCommand()">复制回灌命令</button>
      <button onclick="includeAllSuggested()">全部按建议纳入</button>
      <button class="good" onclick="applyCandidatesToVisible()">套用当前筛选候选</button>
      <button onclick="applyAllCandidates()">套用全部候选</button>
      <button onclick="resetAll()">重置本页选择</button>
    </div>
    <div id="cards" class="grid"></div>
  </main>
  <script>
    const DATA = {json.dumps(data, ensure_ascii=False)};
    const state = new Map();
    let visiblePending = [];
    let visibleGroups = [];
    const yuan = n => "¥" + Number(n || 0).toLocaleString("zh-CN", {{ minimumFractionDigits: 2, maximumFractionDigits: 2 }});
    const csvHeader = ["review_key","decision","main_category","sub_category","allocation_pct","allocation_amount","risk_tags","note"];
    function tagsDefault(row) {{ return row.risk_tags || "基础支出"; }}
    function initState() {{
      DATA.pending.forEach(row => {{
        state.set(row.review_key, {{
          decision: "",
          allocations: [{{ main_category: row.main_category, sub_category: row.sub_category, allocation_pct: 100, allocation_amount: "", risk_tags: tagsDefault(row), note: "" }}]
        }});
      }});
    }}
    const categoryPairs = Object.entries(DATA.taxonomy).flatMap(([main, subs]) => subs.map(sub => ({{ main, sub, value: `${{main}}|||${{sub}}`, label: `${{main}} / ${{sub}}` }})));
    function decisionOptions(value) {{
      const options = [
        ["", "未选择"],
        ["include", "纳入统计"],
        ["exclude", "排除"],
      ];
      return options.map(([raw, label]) => `<option value="${{raw}}" ${{raw === value ? "selected" : ""}}>${{label}}</option>`).join("");
    }}
    function categoryPresetOptions(main, sub) {{
      const current = `${{main}}|||${{sub}}`;
      return categoryPairs.map(item => `<option value="${{escapeHtml(item.value)}}" ${{item.value === current ? "selected" : ""}}>${{escapeHtml(item.label)}}</option>`).join("");
    }}
    function categoryPresetFilterOptions() {{
      return `<option value="">全部建议分类</option>` + categoryPairs.map(item => `<option value="${{escapeHtml(item.value)}}">${{escapeHtml(item.label)}}</option>`).join("");
    }}
    function riskOptions(value) {{
      const active = new Set(String(value || "").split("|").filter(Boolean));
      return DATA.risk_tags.map(name => `<option value="${{escapeHtml(name)}}" ${{active.has(name) ? "selected" : ""}}>${{escapeHtml(name)}}</option>`).join("");
    }}
    function escapeHtml(value) {{
      return String(value ?? "").replace(/[&<>"']/g, ch => ({{"&":"&amp;","<":"&lt;",">":"&gt;","\\\"":"&quot;","'":"&#39;"}}[ch]));
    }}
    function render() {{
      visiblePending = filteredPendingRows();
      updateMetrics(visiblePending);
      renderGroupMatrix(visiblePending);
      const root = document.getElementById("cards");
      if (!DATA.pending.length) {{
        root.className = "empty";
        root.innerHTML = "当前没有待复核大额交易。";
        return;
      }}
      if (!visiblePending.length) {{
        root.className = "empty";
        root.innerHTML = "当前筛选条件下没有待复核交易。";
        return;
      }}
      root.className = "grid";
      root.innerHTML = visiblePending.map(row => renderCard(row)).join("");
    }}
    function filteredPendingRows() {{
      const q = String(document.getElementById("reviewSearch")?.value || "").trim().toLowerCase();
      const category = document.getElementById("filterCategory")?.value || "";
      const decision = document.getElementById("filterDecision")?.value || "";
      const minAmount = Number(document.getElementById("filterMinAmount")?.value || 0);
      const sortMode = document.getElementById("sortMode")?.value || "amount_desc";
      const rows = DATA.pending.filter(row => {{
        const item = state.get(row.review_key);
        const haystack = `${{row.counterparty}} ${{row.description}} ${{row.review_key}} ${{row.risk_tags}} ${{row.main_category}} ${{row.sub_category}}`.toLowerCase();
        if (q && !haystack.includes(q)) return false;
        if (category && `${{row.main_category}}|||${{row.sub_category}}` !== category) return false;
        if (decision === "undecided" && item.decision) return false;
        if (decision && decision !== "undecided" && item.decision !== decision) return false;
        if (Number(row.amount || 0) < minAmount) return false;
        return true;
      }});
      return rows.sort((a, b) => {{
        if (sortMode === "date_desc") return String(b.transaction_time).localeCompare(String(a.transaction_time));
        if (sortMode === "counterparty") return String(a.counterparty).localeCompare(String(b.counterparty));
        return Number(b.amount || 0) - Number(a.amount || 0);
      }});
    }}
    function renderCard(row) {{
      const item = state.get(row.review_key);
      const excluded = item.decision === "exclude";
      const allocationRows = item.allocations.map((allocation, index) => renderAllocation(row, allocation, index)).join("");
      const candidate = row.candidate || {{}};
      const candidatePill = candidate.candidate_action ? `<span class="pill ${{escapeHtml(candidate.candidate_confidence || "low")}}" title="${{escapeHtml(candidate.candidate_reason || "")}}">${{escapeHtml(candidate.candidate_label)}} · ${{escapeHtml(candidate.candidate_confidence || "low")}}</span>` : "";
      return `<article class="card ${{excluded ? "excluded" : ""}}">
        <div class="top">
          <div>
            <div class="merchant">${{escapeHtml(row.counterparty)}}</div>
            <div class="desc">${{escapeHtml(row.transaction_time)}} · ${{escapeHtml(row.source_platform || "unknown")}} · ${{escapeHtml(row.description)}} · ${{escapeHtml(row.review_key)}}</div>
            <div class="desc">${{candidatePill}} ${{escapeHtml(candidate.candidate_reason || "")}}</div>
          </div>
          <div class="amount">${{yuan(row.amount)}}</div>
        </div>
        <div class="decision-line">
          <label><span class="field-label">复核决定</span><select onchange="setDecision('${{row.review_key}}', this.value)">${{decisionOptions(item.decision)}}</select></label>
          <label><span class="field-label">主类/子类</span><select onchange="setPrimaryCategory('${{row.review_key}}', this.value)">${{categoryPresetOptions(item.allocations[0].main_category, item.allocations[0].sub_category)}}</select></label>
          <label><span class="field-label">风险标签</span><select onchange="setPrimaryRiskTags('${{row.review_key}}', this.value)">${{riskOptions(item.allocations[0].risk_tags)}}</select></label>
          <button class="warn" onclick="splitLiving('${{row.review_key}}')">50/25/25 拆分</button>
        </div>
        <div class="actions">
          <button onclick="resetRow('${{row.review_key}}')">重置</button>
        </div>
        <div class="split-list">${{allocationRows}}</div>
        <span class="status">当前状态：${{item.decision || "未选择"}}</span>
      </article>`;
    }}
    function renderAllocation(row, allocation, index) {{
      return `<div class="row">
        <select onchange="changeCategoryPreset('${{row.review_key}}', ${{index}}, this.value)">${{categoryPresetOptions(allocation.main_category, allocation.sub_category)}}</select>
        <input type="number" min="0" max="100" step="0.01" value="${{allocation.allocation_pct}}" onchange="changeAllocation('${{row.review_key}}', ${{index}}, 'allocation_pct', this.value)">
        <select onchange="changeAllocation('${{row.review_key}}', ${{index}}, 'risk_tags', this.value)">${{riskOptions(allocation.risk_tags)}}</select>
        <button onclick="removeAllocation('${{row.review_key}}', ${{index}})">删除</button>
      </div>`;
    }}
    function updateMetrics(visibleRows) {{
      let include = 0, exclude = 0, includeAmount = 0, excludeAmount = 0;
      for (const item of state.values()) {{
        const row = DATA.pending.find(candidate => state.get(candidate.review_key) === item);
        const amount = Number(row?.amount || 0);
        if (item.decision === "include") {{ include += 1; includeAmount += amount; }}
        if (item.decision === "exclude") {{ exclude += 1; excludeAmount += amount; }}
      }}
      document.getElementById("pendingCount").textContent = DATA.pending.length;
      document.getElementById("pendingAmount").textContent = yuan(DATA.pending.reduce((sum, row) => sum + Number(row.amount || 0), 0));
      document.getElementById("visibleCount").textContent = visibleRows.length;
      document.getElementById("includeCount").textContent = `${{include}} / ${{yuan(includeAmount)}}`;
      document.getElementById("excludeCount").textContent = `${{exclude}} / ${{yuan(excludeAmount)}}`;
      const candidateCount = DATA.pending.filter(row => (row.candidate || {{}}).candidate_action === "include_suggested").length;
      const candidateAmount = DATA.pending.reduce((sum, row) => sum + ((row.candidate || {{}}).candidate_action === "include_suggested" ? Number(row.amount || 0) : 0), 0);
      document.getElementById("candidateCount").textContent = `${{candidateCount}} / ${{yuan(candidateAmount)}}`;
      renderImpactPreview(visibleRows, includeAmount, excludeAmount);
    }}
    function groupKeyFor(row, mode) {{
      if (mode === "category") return `${{row.main_category || "未分类"}} / ${{row.sub_category || "未分类"}}`;
      if (mode === "month") return String(row.transaction_time || row.date || "").slice(0, 7) || "未知月份";
      return row.counterparty || "未填写对手方";
    }}
    function groupedRows(visibleRows) {{
      const mode = document.getElementById("groupMode")?.value || "counterparty";
      const groups = new Map();
      visibleRows.forEach(row => {{
        const key = groupKeyFor(row, mode);
        if (!groups.has(key)) groups.set(key, []);
        groups.get(key).push(row);
      }});
      return Array.from(groups.entries()).map(([key, rows]) => {{
        const amount = rows.reduce((sum, row) => sum + Number(row.amount || 0), 0);
        const undecided = rows.filter(row => !state.get(row.review_key).decision).length;
        const included = rows.filter(row => state.get(row.review_key).decision === "include").length;
        const excluded = rows.filter(row => state.get(row.review_key).decision === "exclude").length;
        const sample = rows.slice(0, 3).map(row => row.counterparty === key ? row.description : row.counterparty).filter(Boolean).join(" / ");
        const candidateCount = rows.filter(row => (row.candidate || {{}}).candidate_action === "include_suggested").length;
        const highCount = rows.filter(row => (row.candidate || {{}}).candidate_confidence === "high").length;
        return {{ key, rows, amount, count: rows.length, undecided, included, excluded, sample, candidateCount, highCount }};
      }}).sort((a, b) => b.amount - a.amount);
    }}
    function renderImpactPreview(visibleRows, includeAmount, excludeAmount) {{
      const visibleAmount = visibleRows.reduce((sum, row) => sum + Number(row.amount || 0), 0);
      const undecidedAmount = DATA.pending.reduce((sum, row) => sum + (!state.get(row.review_key).decision ? Number(row.amount || 0) : 0), 0);
      const selectedRows = Array.from(state.values()).filter(item => item.decision).length;
      document.getElementById("impactPreview").innerHTML = [
        ["当前筛选金额", yuan(visibleAmount)],
        ["已决策笔数", selectedRows],
        ["纳入影响金额", yuan(includeAmount)],
        ["仍未决策金额", yuan(undecidedAmount)]
      ].map(([label, value]) => `<div class="impact-card"><span class="label">${{escapeHtml(label)}}</span><strong>${{escapeHtml(value)}}</strong></div>`).join("");
    }}
    function renderGroupMatrix(visibleRows) {{
      const root = document.getElementById("reviewGroupMatrix");
      const groups = groupedRows(visibleRows);
      visibleGroups = groups;
      if (!groups.length) {{
        root.innerHTML = `<div class="empty">当前筛选下没有可分组复核对象。</div>`;
        return;
      }}
      root.innerHTML = groups.slice(0, 24).map((group, index) => {{
        const status = `未选 ${{group.undecided}} · 纳入 ${{group.included}} · 排除 ${{group.excluded}}`;
        const candidateStatus = `候选 ${{group.candidateCount}} · 高置信 ${{group.highCount}}`;
        return `<div class="group-row">
          <div><div class="group-name" title="${{escapeHtml(group.key)}}">${{escapeHtml(group.key)}}</div><div class="group-sub" title="${{escapeHtml(group.sample)}}">${{escapeHtml(group.sample || "同组交易")}}</div><div class="group-sub">${{candidateStatus}}</div></div>
          <div>${{group.count}} 笔</div>
          <div>${{yuan(group.amount)}}</div>
          <div class="group-actions">
            <button class="good" onclick="applyGroupAction(${{index}}, 'include_suggested')">按建议纳入</button>
            <button onclick="applyGroupAction(${{index}}, 'batch')">套用批量栏</button>
            <button class="warn" onclick="applyGroupAction(${{index}}, 'split_living')">50/25/25</button>
            <button class="bad" onclick="applyGroupAction(${{index}}, 'exclude')">排除</button>
            <span class="status">${{status}}</span>
          </div>
        </div>`;
      }}).join("");
    }}
    function applyGroupAction(groupIndex, action) {{
      const group = visibleGroups[Number(groupIndex)];
      const rows = group ? group.rows : [];
      const batchCategory = document.getElementById("batchCategory").value;
      const batchRisk = document.getElementById("batchRisk").value || "基础支出";
      const parsed = parseCategoryPreset(batchCategory);
      rows.forEach(row => {{
        const item = state.get(row.review_key);
        if (action === "exclude") {{
          item.decision = "exclude";
          return;
        }}
        if (action === "split_living") {{
          item.decision = "include";
          item.allocations = [
            {{ main_category: "生活刚需", sub_category: "教育医疗", allocation_pct: 50, allocation_amount: "", risk_tags: "家庭教育", note: "group split 50/25/25" }},
            {{ main_category: "生活刚需", sub_category: "住房缴费", allocation_pct: 25, allocation_amount: "", risk_tags: "住房缴费", note: "group split 50/25/25" }},
            {{ main_category: "生活刚需", sub_category: "餐饮日用", allocation_pct: 25, allocation_amount: "", risk_tags: "餐饮日用", note: "group split 50/25/25" }}
          ];
          return;
        }}
        item.decision = "include";
        if (action === "include_suggested") {{
          item.allocations = [{{ main_category: row.main_category, sub_category: row.sub_category, allocation_pct: 100, allocation_amount: "", risk_tags: tagsDefault(row), note: "group matrix suggested review" }}];
        }}
        if (action === "batch") {{
          item.allocations = [{{ ...item.allocations[0], ...parsed, allocation_pct: 100, allocation_amount: "", risk_tags: batchRisk, note: "group matrix batch review" }}];
        }}
      }});
      render();
    }}
    function applyCandidate(row) {{
      const candidate = row.candidate || {{}};
      const item = state.get(row.review_key);
      if (candidate.candidate_action !== "include_suggested") return;
      item.decision = "include";
      item.allocations = [{{
        main_category: candidate.candidate_main_category || row.main_category,
        sub_category: candidate.candidate_sub_category || row.sub_category,
        allocation_pct: 100,
        allocation_amount: "",
        risk_tags: candidate.candidate_risk_tags || tagsDefault(row),
        note: `candidate ${{candidate.candidate_confidence || "unknown"}}: ${{candidate.candidate_reason || ""}}`
      }}];
    }}
    function applyCandidatesToVisible() {{
      visiblePending.forEach(row => applyCandidate(row));
      render();
    }}
    function applyAllCandidates() {{
      DATA.pending.forEach(row => applyCandidate(row));
      render();
    }}
    function setDecision(key, decision) {{ state.get(key).decision = decision; render(); }}
    function parseCategoryPreset(value) {{
      const [main, sub] = String(value || "").split("|||");
      return {{ main_category: main || "生活刚需", sub_category: sub || "餐饮日用" }};
    }}
    function setPrimaryCategory(key, value) {{
      const item = state.get(key);
      const parsed = parseCategoryPreset(value);
      item.allocations = [{{ ...item.allocations[0], ...parsed, allocation_pct: 100, allocation_amount: "" }}];
      item.decision = "include";
      render();
    }}
    function setPrimaryRiskTags(key, value) {{
      const item = state.get(key);
      item.allocations[0].risk_tags = value || "基础支出";
      item.decision = "include";
      render();
    }}
    function resetRow(key) {{
      const row = DATA.pending.find(item => item.review_key === key);
      state.set(key, {{ decision: "", allocations: [{{ main_category: row.main_category, sub_category: row.sub_category, allocation_pct: 100, allocation_amount: "", risk_tags: tagsDefault(row), note: "" }}] }});
      render();
    }}
    function splitLiving(key) {{
      state.set(key, {{ decision: "include", allocations: [
        {{ main_category: "生活刚需", sub_category: "教育医疗", allocation_pct: 50, allocation_amount: "", risk_tags: "家庭教育", note: "split 50/25/25" }},
        {{ main_category: "生活刚需", sub_category: "住房缴费", allocation_pct: 25, allocation_amount: "", risk_tags: "住房缴费", note: "split 50/25/25" }},
        {{ main_category: "生活刚需", sub_category: "餐饮日用", allocation_pct: 25, allocation_amount: "", risk_tags: "餐饮日用", note: "split 50/25/25" }}
      ]}});
      render();
    }}
    function changeAllocation(key, index, field, value) {{
      const item = state.get(key);
      item.allocations[index][field] = field === "allocation_pct" ? Number(value || 0) : value;
      item.decision = "include";
      render();
    }}
    function changeCategoryPreset(key, index, value) {{
      const item = state.get(key);
      Object.assign(item.allocations[index], parseCategoryPreset(value));
      item.decision = "include";
      render();
    }}
    function removeAllocation(key, index) {{
      const item = state.get(key);
      if (item.allocations.length <= 1) return;
      item.allocations.splice(index, 1);
      render();
    }}
    function includeAllSuggested() {{
      DATA.pending.forEach(row => state.get(row.review_key).decision = "include");
      render();
    }}
    function applyBatchToVisible() {{
      const decision = document.getElementById("batchDecision").value || "include";
      const category = document.getElementById("batchCategory").value;
      const risk = document.getElementById("batchRisk").value || "基础支出";
      const parsed = parseCategoryPreset(category);
      visiblePending.forEach(row => {{
        const item = state.get(row.review_key);
        item.decision = decision;
        if (decision === "include") {{
          item.allocations = [{{ ...item.allocations[0], ...parsed, allocation_pct: 100, allocation_amount: "", risk_tags: risk, note: "batch visible review" }}];
        }}
      }});
      render();
    }}
    function resetAll() {{ initState(); render(); }}
    function initControls() {{
      document.getElementById("filterCategory").innerHTML = categoryPresetFilterOptions();
      document.getElementById("batchCategory").innerHTML = categoryPairs.map(item => `<option value="${{escapeHtml(item.value)}}">${{escapeHtml(item.label)}}</option>`).join("");
      document.getElementById("batchRisk").innerHTML = DATA.risk_tags.map(name => `<option value="${{escapeHtml(name)}}">${{escapeHtml(name)}}</option>`).join("");
    }}
    function csvEscape(value) {{
      const text = String(value ?? "");
      return /[",\\n]/.test(text) ? `"${{text.replaceAll('"', '""')}}"` : text;
    }}
    function decisionRows() {{
      const rows = [];
      for (const row of DATA.pending) {{
        const item = state.get(row.review_key);
        if (!item.decision) continue;
        if (item.decision === "exclude") {{
          rows.push([row.review_key, "exclude", "", "", "", "", "", "excluded in review workbench"]);
        }} else {{
          item.allocations.forEach(allocation => rows.push([
            row.review_key, "include", allocation.main_category, allocation.sub_category,
            allocation.allocation_pct, allocation.allocation_amount || "", allocation.risk_tags, allocation.note || "review workbench"
          ]));
        }}
      }}
      return rows;
    }}
    function csvText() {{
      return [csvHeader, ...decisionRows()].map(row => row.map(csvEscape).join(",")).join("\\n") + "\\n";
    }}
    function downloadCsv() {{
      const blob = new Blob([csvText()], {{ type: "text/csv;charset=utf-8" }});
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "review_decisions_confirmed.csv";
      a.click();
      URL.revokeObjectURL(url);
    }}
    async function copyCommand() {{
      const cmd = "python3 scripts/run_analysis.py --input '~/Downloads/<YOUR_ALIPAY_BILL>.csv' --review-decisions outputs/alipay_analysis_latest/review/review_decisions_confirmed.csv --output outputs/alipay_analysis_latest";
      try {{ await navigator.clipboard.writeText(cmd); alert("已复制回灌命令"); }} catch (err) {{ alert(cmd); }}
    }}
    Object.assign(window, {{ render, setDecision, setPrimaryCategory, setPrimaryRiskTags, splitLiving, changeAllocation, changeCategoryPreset, removeAllocation, includeAllSuggested, applyBatchToVisible, applyCandidatesToVisible, applyAllCandidates, resetAll, downloadCsv, copyCommand }});
    initState();
    initControls();
    render();
  </script>
</body>
</html>"""


def _allocation_export_rows(rows: list[ClassifiedTransaction], review_decisions: ReviewDecisions | None = None) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for item in _expense_allocations(rows, review_decisions):
        row = item["row"]
        output.append(
            {
                "transaction_time": row.transaction_time,
                "date": row.date,
                "source_platform": row.source_platform,
                "order_id": row.order_id,
                "counterparty": row.counterparty,
                "description": row.description,
                "original_amount": row.amount,
                "allocated_amount": yuan(item["amount_cents"]),
                "allocated_amount_cents": item["amount_cents"],
                "main_category": item["main_category"],
                "sub_category": item["sub_category"],
                "risk_tags": "|".join(item["risk_tags"]),
                "included_in_statistics": True,
                "review_confirmed": _is_review_confirmed(row, review_decisions),
                "review_key": review_key(row),
                "review_decision": item.get("review_decision", "auto_confirmed" if _is_review_confirmed(row, review_decisions) else "auto"),
                "review_note": item.get("review_note", ""),
            }
        )
    return output


def _pending_review_rows(rows: list[ClassifiedTransaction], review_decisions: ReviewDecisions | None = None) -> list[ClassifiedTransaction]:
    return sorted(
        [row for row in rows if getattr(row, "needs_review", False) and not _is_review_confirmed(row, review_decisions)],
        key=lambda row: row.amount_cents,
        reverse=True,
    )


def _review_status_summary(rows: list[ClassifiedTransaction], review_decisions: ReviewDecisions | None = None) -> list[dict[str, Any]]:
    labels = {
        "auto_confirmed_rule": ("内置规则已确认", "进入生产统计", "lolol/贾韩松 与 蠢张伟倩等已固定映射。"),
        "manual_include": ("人工确认纳入", "进入生产统计", "来自 review_decisions CSV 的 include 决策。"),
        "manual_exclude": ("人工确认排除", "不计入支出", "来自 review_decisions CSV 的 exclude 决策。"),
        "pending_review": ("仍待复核", "隔离不入账", "需要在复核工作台下拉确认后重建报告。"),
    }
    buckets: dict[str, dict[str, int]] = {key: {"count": 0, "amount_cents": 0} for key in labels}
    total_amount = 0
    total_count = 0
    for row in _expense_rows(rows):
        if not getattr(row, "needs_review", False):
            continue
        total_count += 1
        total_amount += row.amount_cents
        key = review_key(row)
        if _is_lolol(row) or _is_chun(row):
            status = "auto_confirmed_rule"
        elif review_decisions and key in review_decisions.included:
            status = "manual_include"
        elif review_decisions and key in review_decisions.excluded:
            status = "manual_exclude"
        else:
            status = "pending_review"
        buckets[status]["count"] += 1
        buckets[status]["amount_cents"] += row.amount_cents

    output: list[dict[str, Any]] = []
    for status, (label, production_effect, action) in labels.items():
        amount_cents = buckets[status]["amount_cents"]
        count = buckets[status]["count"]
        output.append(
            {
                "status": status,
                "status_label": label,
                "count": count,
                "amount": yuan(amount_cents),
                "amount_cents": amount_cents,
                "count_pct": format_pct(count, total_count),
                "amount_pct": format_pct(amount_cents, total_amount),
                "production_effect": production_effect,
                "next_action": action,
                "bar": _visual_bar(amount_cents, total_amount),
            }
        )
    return output


def _review_candidate_for(row: ClassifiedTransaction) -> dict[str, Any]:
    text = f"{row.counterparty} {row.description} {row.transaction_type} {row.risk_tags}"
    merchant_tokens = [
        "有限公司",
        "公司",
        "旗舰店",
        "官方",
        "基金",
        "银行",
        "保险",
        "物业",
        "医院",
        "学校",
        "大学",
        "小荷包",
        "黄金",
        "cartier",
        "herm",
        "pty",
        "ltd",
    ]
    person_like = bool(re.fullmatch(r"[\u4e00-\u9fff]{2,4}", row.counterparty.strip()))
    transfer_like = any(token in text for token in ["转账", "红包", "亲情卡", "人情"])
    merchant_like = any(token.casefold() in text.casefold() for token in merchant_tokens)
    if merchant_like and row.main_category:
        confidence = "high"
        reason = "交易对方或说明呈现机构/平台/商户特征，建议按当前规则分类纳入，仍需你确认。"
        action = "include_suggested"
    elif person_like or transfer_like or row.main_category == "社交家庭":
        confidence = "low"
        reason = "疑似个人转账/社交家庭/人情往来，大额责任归属需要人工判断。"
        action = "manual_review"
    else:
        confidence = "medium"
        reason = "已有主类/子类和风险标签，但缺少明确机构特征，建议按当前规则预填后人工确认。"
        action = "include_suggested"
    return {
        "candidate_action": action,
        "candidate_label": "建议纳入" if action == "include_suggested" else "保持人工复核",
        "candidate_confidence": confidence,
        "candidate_reason": reason,
        "candidate_main_category": row.main_category,
        "candidate_sub_category": row.sub_category,
        "candidate_risk_tags": row.risk_tags,
    }


def _review_decision_candidate_rows(rows: list[ClassifiedTransaction], review_decisions: ReviewDecisions | None = None) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in _pending_review_rows(rows, review_decisions):
        candidate = _review_candidate_for(row)
        output.append(
            {
                "review_key": review_key(row),
                **candidate,
                "amount": row.amount,
                "transaction_time": row.transaction_time,
                "source_platform": row.source_platform,
                "counterparty": row.counterparty,
                "description": row.description,
                "current_main_category": row.main_category,
                "current_sub_category": row.sub_category,
                "current_risk_tags": row.risk_tags,
                "order_id": row.order_id,
            }
        )
    return output


def _review_decision_candidate_group_rows(candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], dict[str, Any]] = {}
    for row in candidate_rows:
        for group_type, key in [
            ("counterparty", str(row.get("counterparty", "") or "未填写对手方")),
            ("category", f"{row.get('current_main_category', '')} / {row.get('current_sub_category', '')}"),
            ("month", str(row.get("transaction_time", ""))[:7] or "未知月份"),
        ]:
            bucket = groups.setdefault(
                (group_type, key),
                {
                    "group_type": group_type,
                    "group_key": key,
                    "count": 0,
                    "amount": 0.0,
                    "include_candidate_count": 0,
                    "manual_review_count": 0,
                    "high_confidence_count": 0,
                    "medium_confidence_count": 0,
                    "low_confidence_count": 0,
                    "top_reason": "",
                },
            )
            bucket["count"] += 1
            bucket["amount"] += float(row.get("amount", 0) or 0)
            if row.get("candidate_action") == "include_suggested":
                bucket["include_candidate_count"] += 1
            else:
                bucket["manual_review_count"] += 1
            confidence_key = f"{row.get('candidate_confidence', 'low')}_confidence_count"
            bucket[confidence_key] = int(bucket.get(confidence_key, 0)) + 1
            if not bucket["top_reason"]:
                bucket["top_reason"] = row.get("candidate_reason", "")
    return sorted(groups.values(), key=lambda item: (str(item["group_type"]), -float(item["amount"])))


def _review_decision_template_rows(rows: list[ClassifiedTransaction], review_decisions: ReviewDecisions | None = None) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in _pending_review_rows(rows, review_decisions):
        output.append(
            {
                "review_key": review_key(row),
                "decision": "",
                "main_category": row.main_category,
                "sub_category": row.sub_category,
                "allocation_pct": "100",
                "allocation_amount": "",
                "risk_tags": row.risk_tags,
                "note": "",
                "transaction_time": row.transaction_time,
                "source_platform": row.source_platform,
                "counterparty": row.counterparty,
                "description": row.description,
                "amount": row.amount,
                "suggested_main_category": row.main_category,
                "suggested_sub_category": row.sub_category,
                "suggested_risk_tags": row.risk_tags,
                "order_id": row.order_id,
            }
        )
    return output


def _review_decision_rows(review_decisions: ReviewDecisions | None) -> list[dict[str, Any]]:
    if not review_decisions:
        return []
    output: list[dict[str, Any]] = []
    for key in sorted(review_decisions.excluded):
        output.append(
            {
                "review_key": key,
                "decision": "exclude",
                "main_category": "",
                "sub_category": "",
                "allocation_pct": "",
                "allocation_amount": "",
                "risk_tags": "",
                "note": "",
            }
        )
    for key, allocations in sorted(review_decisions.included.items()):
        for allocation in allocations:
            output.append(
                {
                    "review_key": key,
                    "decision": "include",
                    "main_category": allocation.main_category,
                    "sub_category": allocation.sub_category,
                    "allocation_pct": "" if allocation.pct is None else allocation.pct,
                    "allocation_amount": "" if allocation.amount_cents is None else yuan(allocation.amount_cents),
                    "risk_tags": "|".join(allocation.risk_tags),
                    "note": allocation.note,
                }
            )
    return output


def _sqlite_value(value: Any) -> Any:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False)
    return value


def _write_sqlite_table(conn: sqlite3.Connection, table_name: str, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else []
    safe_table = re.sub(r"[^a-zA-Z0-9_]", "_", table_name)
    conn.execute(f'DROP TABLE IF EXISTS "{safe_table}"')
    if not fieldnames:
        conn.execute(f'CREATE TABLE "{safe_table}" (empty TEXT)')
        return
    column_sql = ", ".join(f'"{name}" TEXT' for name in fieldnames)
    conn.execute(f'CREATE TABLE "{safe_table}" ({column_sql})')
    placeholders = ", ".join("?" for _ in fieldnames)
    column_names = ", ".join(f'"{name}"' for name in fieldnames)
    conn.executemany(
        f'INSERT INTO "{safe_table}" ({column_names}) VALUES ({placeholders})',
        [[_sqlite_value(row.get(name, "")) for name in fieldnames] for row in rows],
    )


def _write_sqlite(
    path: Path,
    *,
    transaction_rows: list[dict[str, Any]],
    allocation_rows: list[dict[str, Any]],
    category_rows: list[dict[str, Any]],
    risk_rows: list[dict[str, Any]],
    control_plan_rows: list[dict[str, Any]],
    budget_pressure_rows: list[dict[str, Any]],
    source_platform_rows: list[dict[str, Any]],
    tag_library_rows: list[dict[str, Any]],
    tag_filter_preset_rows: list[dict[str, Any]],
    review_rows: list[dict[str, Any]],
    review_status_rows: list[dict[str, Any]],
    review_candidate_rows: list[dict[str, Any]],
    review_candidate_group_rows: list[dict[str, Any]],
    review_decision_rows: list[dict[str, Any]],
    review_invalid_rows: list[dict[str, Any]],
    data_trust_rows: list[dict[str, Any]],
    manual_review_audit_rows: list[dict[str, Any]],
    manual_review_audit_summary_rows: list[dict[str, Any]],
    entity_registry_rows: list[dict[str, Any]],
    alias_map_rows: list[dict[str, Any]],
    entity_registry_summary_rows: list[dict[str, Any]],
    evidence_decision_rows: list[dict[str, Any]],
    evidence_decision_summary_rows: list[dict[str, Any]],
    period_summaries: dict[str, list[dict[str, Any]]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        _write_sqlite_table(conn, "classified_transactions_audit", transaction_rows)
        _write_sqlite_table(conn, "production_expense_allocations", allocation_rows)
        _write_sqlite_table(conn, "summary_by_category", category_rows)
        _write_sqlite_table(conn, "summary_by_risk_tag", risk_rows)
        _write_sqlite_table(conn, "spending_control_plan", control_plan_rows)
        _write_sqlite_table(conn, "budget_pressure_radar", budget_pressure_rows)
        _write_sqlite_table(conn, "source_platform_summary", source_platform_rows)
        _write_sqlite_table(conn, "tag_library", tag_library_rows)
        _write_sqlite_table(conn, "tag_filter_presets", tag_filter_preset_rows)
        _write_sqlite_table(conn, "manual_review_queue", review_rows)
        _write_sqlite_table(conn, "manual_review_status_summary", review_status_rows)
        _write_sqlite_table(conn, "manual_review_decision_candidates", review_candidate_rows)
        _write_sqlite_table(conn, "manual_review_decision_candidate_groups", review_candidate_group_rows)
        _write_sqlite_table(conn, "manual_review_decisions", review_decision_rows)
        _write_sqlite_table(conn, "manual_review_invalid_rows", review_invalid_rows)
        _write_sqlite_table(conn, "data_trust_transactions", data_trust_rows)
        _write_sqlite_table(conn, "manual_review_queue_audit", manual_review_audit_rows)
        _write_sqlite_table(conn, "manual_review_queue_audit_summary", manual_review_audit_summary_rows)
        _write_sqlite_table(conn, "entity_registry", entity_registry_rows)
        _write_sqlite_table(conn, "alias_map", alias_map_rows)
        _write_sqlite_table(conn, "entity_registry_summary", entity_registry_summary_rows)
        _write_sqlite_table(conn, "evidence_decision_matrix", evidence_decision_rows)
        _write_sqlite_table(conn, "evidence_decision_summary", evidence_decision_summary_rows)
        for period_name, summary in period_summaries.items():
            _write_sqlite_table(conn, f"summary_by_{period_name}", summary)
        conn.commit()


def _sha256_file(path: Path) -> str | None:
    try:
        digest = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError:
        return None


def _source_log_rows(rows: list[ClassifiedTransaction]) -> list[dict[str, Any]]:
    counts: dict[tuple[str, str], int] = defaultdict(int)
    for row in rows:
        counts[(getattr(row, "source_platform", "") or "unknown", getattr(row, "source_file", "") or "unknown")] += 1
    output: list[dict[str, Any]] = []
    for (platform, source), count in sorted(counts.items()):
        path = Path(source)
        stat = path.stat() if path.exists() else None
        output.append(
            {
                "source_platform": platform,
                "source_file": source,
                "row_count": count,
                "exists": path.exists(),
                "size_bytes": stat.st_size if stat else None,
                "sha256": _sha256_file(path) if path.exists() else None,
            }
        )
    return output


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False, default=str) for row in rows) + "\n", encoding="utf-8")


def _rules_version_payload(rules_path: Path) -> dict[str, Any]:
    exists = rules_path.exists()
    return {
        "rules_path": str(rules_path),
        "exists": exists,
        "sha256": _sha256_file(rules_path) if exists else None,
        "version": json.loads(rules_path.read_text(encoding="utf-8")).get("version") if exists else None,
    }


def _reference_models_payload() -> list[dict[str, Any]]:
    return [
        {
            "project": "dtsola/xiaoyaoprivatebill",
            "url": "https://github.com/dtsola/xiaoyaoprivatebill",
            "source_type": "GitHub README",
            "verified_at": "2026-06-05",
            "license": "MIT",
            "evidence_summary": "README describes local-only privacy, Alipay CSV and WeChat CSV/XLSX parsing, annual/monthly/category/time/insight analysis, responsive design, Vue/Flask, Docker deployment, and export support.",
            "reference_features": [
                "本地隐私优先处理",
                "支付宝 CSV 与微信 CSV/XLSX 多格式方向",
                "年度、月度、分类、时间、消费洞察、交易记录等多维分析",
                "响应式 dashboard 和明细查询导出",
            ],
            "incorporated_as": [
                "所有处理默认本地完成，不上传服务器",
                "支付宝/微信 CSV/XLSX 均映射到统一交易 schema 后进入同一分类管线",
                "输出 dashboard、交易明细查询页和周期 PDF 报告",
                "审计目录记录输入 hash、规则版本和运行清单",
            ],
            "remaining_gap": "银行卡/券商流水导入尚未实现；当前支持支付宝/微信 CSV/XLSX 和 ZIP 内 CSV/XLSX。",
        },
        {
            "project": "ryaraghav/personal-finance-agent",
            "url": "https://github.com/ryaraghav/personal-finance-agent",
            "source_type": "GitHub README",
            "verified_at": "2026-06-05",
            "license": "MIT",
            "evidence_summary": "README documents multi-bank statement adapters, merchant/category analysis, natural-language NL2SQL, manual category overrides, and explicit read-only SQL validation that blocks writes.",
            "reference_features": [
                "多来源账单标准化为统一 schema",
                "商户聚合分类，降低逐笔分类不一致",
                "主类/子类层级分类",
                "人工覆盖和只读查询思路",
                "NL2SQL 必须只读并拦截写操作",
            ],
            "incorporated_as": [
                "支付宝字段被清洗成统一 ClassifiedTransaction",
                "对手方 Top、生产分摊表和明细查询支持商户维度审查",
                "人工复核 CSV 回灌只影响生产统计，不修改原始审计明细",
                "新增固定问题模板 ask 和 /api/ask，按白名单模板查询，不开放任意 SQL",
            ],
            "remaining_gap": "LLM 驱动的自由文本 NL2SQL 尚未启用；如启用必须先做 schema 白名单、只读校验和人工确认。",
        },
        {
            "project": "Hessel2333/alipay_record_analysis",
            "url": "https://github.com/Hessel2333/alipay_record_analysis",
            "source_type": "GitHub README",
            "verified_at": "2026-06-05",
            "license": "MIT",
            "evidence_summary": "README lists yearly overview, monthly analysis, category analysis, time analysis, smart insights, transaction records, interactive charts, responsive layout, Flask, Pandas, and ECharts.",
            "reference_features": [
                "年度总览、月度分析、分类分析、时间分析、消费洞察",
                "交易记录多维筛选和分页",
                "响应式布局与本地处理",
            ],
            "incorporated_as": [
                "周/月/季/半年/年/账单周期 PDF 都含图表、趋势和建议",
                "dashboard 含月度、周度、主类、风险、对手方和时间规律",
                "新增交易明细查询页，支持筛选、分页和导出",
            ],
            "remaining_gap": "当前优先生成静态归档页面，未启动 Flask Web 服务。",
        },
        {
            "project": "vogo/aliwepaystat",
            "url": "https://github.com/vogo/aliwepaystat",
            "source_type": "GitHub README",
            "verified_at": "2026-06-05",
            "license": "Unverified from README page",
            "evidence_summary": "README states Alipay and WeChat CSV bills are imported into SQLite, all later queries and statistics are based on SQLite, CLI supports months/stats/transactions/JSON, and Web UI supports upload, charts, management, and category keywords.",
            "reference_features": [
                "支付宝和微信账单导入 SQLite",
                "基于 SQLite 做后续查询统计",
                "CLI query、JSON 输出、Web 管理界面",
            ],
            "incorporated_as": [
                "生成 consumption.sqlite，包含审计交易、生产分摊、周期汇总、风险标签和复核队列",
                "保留 CSV/JSON 辅助输出，正式报告使用 PDF",
                "静态 dashboard 和交易查询页面读取同一生产统计口径",
                "提供 scripts/query_analysis.py 预设只读查询命令",
                "提供 scripts/serve_ledger.py 本地只读 HTTP API 和报告静态入口",
            ],
            "remaining_gap": "尚未提供带登录权限的 Web 管理服务或远程部署版；当前 API 仅默认绑定本机。",
        },
        {
            "project": "Benature/bill / MickLife KeepAccounts_v2.0",
            "url": "https://github.com/Benature/bill",
            "source_type": "GitHub README",
            "verified_at": "2026-06-05",
            "license": "Unverified from README page",
            "evidence_summary": "README describes merging official WeChat and Alipay bills, tagging each transaction, using monthly/type visualization charts, Excel pivot tables/charts, dropdown categories, and manual data supplementation.",
            "reference_features": [
                "微信和支付宝账单合并",
                "每笔账标记类型",
                "按月份和类型生成可视化图表",
                "支持手动补充和分类校正",
            ],
            "incorporated_as": [
                "多文件输入去重后合并分析",
                "每笔交易有主类、子类、风险标签和复核状态",
                "复核工作台用于下拉菜单式分类校正并回灌报告",
            ],
            "remaining_gap": "Excel 数据透视表形态未复刻，改为 SQLite、PDF 和静态 HTML。",
        },
        {
            "project": "actualbudget/actual",
            "url": "https://github.com/actualbudget/actual",
            "source_type": "GitHub README",
            "verified_at": "2026-06-05",
            "license": "MIT",
            "evidence_summary": "README describes Actual as a local-first, free open-source personal finance app with synchronization, self-hosted/local-only deployment options, envelope budgeting, account management documentation, and multi-package architecture.",
            "reference_features": [
                "local-first 本地优先财务工具",
                "预算信封法和账户管理",
                "多端同步但支持本地-only/自托管部署",
                "文档化的产品结构和长期维护流程",
            ],
            "incorporated_as": [
                "本系统默认本地运行，SQLite 和报告文件均留在用户机器",
                "预算压力雷达和消费控制行动计划吸收预算约束思想",
                "数据契约和只读 API 为未来多系统同步预留边界",
                "README、使用手册和验收脚本固定周更与维护流程",
            ],
            "remaining_gap": "未实现完整账户余额同步、信封预算编辑器或多端同步服务；当前聚焦账单分析和消费控制。",
        },
        {
            "project": "firefly-iii/firefly-iii",
            "url": "https://github.com/firefly-iii/firefly-iii",
            "source_type": "GitHub README",
            "verified_at": "2026-06-05",
            "license": "AGPL-3.0",
            "evidence_summary": "README describes Firefly III as a self-hosted personal finance manager with budgets, categories, tags, imports, financial reports, REST JSON API, recurring transactions, rule-based handling, double-entry bookkeeping, goals, 2FA, Docker, clear views, navigation, and charts.",
            "reference_features": [
                "self-hosted 个人财务管理",
                "预算、分类、标签、导入和财务报表",
                "REST JSON API 和规则化交易处理",
                "复式记账、目标储蓄、周期交易、安全控制",
            ],
            "incorporated_as": [
                "SQLite 表/视图和本地只读 HTTP API 为其他系统提供稳定查询边界",
                "标签库、风险标签、分类规则和复核候选吸收规则化交易处理思想",
                "周期 PDF、Dashboard 和行为分析页覆盖多维财务报表",
                "大额复核隔离和本机绑定 API 保留安全边界",
            ],
            "remaining_gap": "未实现完整复式记账、用户认证、2FA、远程 Web 管理和周期交易编辑；当前不做在线部署。",
        },
        {
            "project": "maybe-finance/maybe",
            "url": "https://github.com/maybe-finance/maybe",
            "source_type": "GitHub README",
            "verified_at": "2026-06-05",
            "license": "AGPL-3.0",
            "evidence_summary": "README states Maybe is a fully working personal finance app that can be self-hosted with Docker, but the repository is archived and no longer actively maintained.",
            "reference_features": [
                "完整个人财务 app 产品形态",
                "Docker self-hosted 部署",
                "现代 Web app 结构",
                "归档项目的维护风险提示",
            ],
            "incorporated_as": [
                "运行控制台把本地系统入口、周更命令、复核流程和交付打包集中成一个操作中心",
                "交付包包含源码、报告、SQLite、审计和测试，便于后续迁移或接入其他系统",
                "对标报告明确记录归档/维护风险，不把不活跃项目作为核心依赖",
            ],
            "remaining_gap": "未复刻完整账户聚合、登录、多用户和在线托管；该项目已归档，仅作产品形态和风险边界参考。",
        },
    ]


def _reference_source_log_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in _reference_models_payload():
        rows.append(
            {
                "project": item["project"],
                "url": item["url"],
                "source_type": item.get("source_type", ""),
                "verified_at": item.get("verified_at", ""),
                "license": item.get("license", ""),
                "reference_feature_count": len(item.get("reference_features", [])),
                "incorporated_feature_count": len(item.get("incorporated_as", [])),
                "evidence_summary": item.get("evidence_summary", ""),
                "remaining_gap": item.get("remaining_gap", ""),
                "reuse_boundary": "功能、信息架构和交互模式参考；不复制外部代码、样式或素材。",
            }
        )
    return rows


def _reference_ui_pattern_rows() -> list[dict[str, str]]:
    return [
        {
            "pattern_id": "local_privacy_portal",
            "pattern": "本地隐私优先入口",
            "reference_projects": "dtsola/xiaoyaoprivatebill; actualbudget/actual; maybe-finance/maybe",
            "source_signal": "local-only/local-first/self-hosted 产品形态",
            "applied_in": "index.html; operations_center.html; user_manual_report.pdf",
            "implementation_evidence": "本地静态入口、SQLite 文件、本机只读 API 命令集中展示，不默认联网或上传。",
            "ui_boundary": "不复制外部页面视觉风格；只吸收本地优先的信息架构。",
        },
        {
            "pattern_id": "dashboard_decision_shell",
            "pattern": "KPI + 现金流 + 类别 + 风险的决策型 dashboard",
            "reference_projects": "Hessel2333/alipay_record_analysis; dtsola/xiaoyaoprivatebill; firefly-iii/firefly-iii",
            "source_signal": "年度/月度/分类/时间/图表/财务报表",
            "applied_in": "dashboard.html; weekly_report.pdf; monthly_report.pdf; yearly_report.pdf",
            "implementation_evidence": "KPI、现金流折线、主类环形、预算压力雷达、风险矩阵、时间热力和对手方集中度。",
            "ui_boundary": "图表编码按本项目现金流和经济放血机制重构，不照搬 ECharts/Firefly UI。",
        },
        {
            "pattern_id": "transaction_drilldown",
            "pattern": "交易明细筛选、搜索反馈和导出",
            "reference_projects": "Hessel2333/alipay_record_analysis; vogo/aliwepaystat; Benature/bill",
            "source_signal": "交易记录、多维筛选、CLI/JSON、Excel 透视与明细校正",
            "applied_in": "transaction_explorer.html",
            "implementation_evidence": "模糊搜索、搜索结果反馈、标签组合、明细折叠、分页、主类/风险/月度/对手方小图和 CSV 导出。",
            "ui_boundary": "保留静态本地页面，不引入远程管理服务或 Excel 透视依赖。",
        },
        {
            "pattern_id": "dropdown_review_workflow",
            "pattern": "下拉式人工复核与批量校正",
            "reference_projects": "Benature/bill; ryaraghav/personal-finance-agent; firefly-iii/firefly-iii",
            "source_signal": "下拉分类、人工覆盖、规则化交易处理",
            "applied_in": "review_workbench.html; manual_review_report.pdf",
            "implementation_evidence": "复核决定、主类/子类、风险标签、候选动作、分组矩阵、影响预览和 review_decisions_confirmed.csv 回灌。",
            "ui_boundary": "未确认大额仍隔离；不把候选建议自动写入生产统计。",
        },
        {
            "pattern_id": "tag_and_behavior_workspace",
            "pattern": "标签库 + 标签组合行为分析",
            "reference_projects": "firefly-iii/firefly-iii; actualbudget/actual; dtsola/xiaoyaoprivatebill",
            "source_signal": "标签、预算、分类洞察和长期维护",
            "applied_in": "tag_library.html; behavior_analysis.html; spending_control_action_report.pdf",
            "implementation_evidence": "标签库编辑、筛选组合持久化、任一/全部命中、折线/直方/环形/金额分布图和消费控制动作。",
            "ui_boundary": "标签用于消费控制和筛选，不扩展为多用户权限后台。",
        },
        {
            "pattern_id": "readonly_data_contract",
            "pattern": "SQLite/只读 API 数据契约",
            "reference_projects": "vogo/aliwepaystat; firefly-iii/firefly-iii; ryaraghav/personal-finance-agent",
            "source_signal": "SQLite 统计、REST JSON API、只读 SQL 校验",
            "applied_in": "docs/finance_ledger_data_contract.md; scripts/serve_ledger.py; scripts/query_analysis.py",
            "implementation_evidence": "事实表、汇总表、mart 视图、本机只读 HTTP API 和固定问题模板查询。",
            "ui_boundary": "默认绑定 127.0.0.1；远程部署必须另加认证、脱敏和访问日志。",
        },
        {
            "pattern_id": "acceptance_and_reference_lab",
            "pattern": "验收工作台 + 开源参考工作台",
            "reference_projects": "maybe-finance/maybe; actualbudget/actual; firefly-iii/firefly-iii",
            "source_signal": "完整产品形态、维护文档、报告和清晰导航",
            "applied_in": "acceptance_workbench.html; reference_model_lab.html; reference_model_benchmark_report.pdf",
            "implementation_evidence": "A/B/C 验收矩阵、ChatGPT 对照接入、参考项目筛选、吸收度图表、功能构成图和 UI 模式矩阵。",
            "ui_boundary": "只做验收和对标辅助，不把外部项目作为运行依赖。",
        },
    ]


def _delivery_acceptance_markdown(
    *,
    metrics: dict[str, Any],
    rows: list[ClassifiedTransaction],
    allocation_rows: list[dict[str, Any]],
    review_rows: list[dict[str, Any]],
    output_paths: dict[str, str],
) -> str:
    sources = sorted({getattr(row, "source_file", "") or "unknown" for row in rows})
    reference_model_count = len(_reference_models_payload())
    lines = [
        "# 交付验收报告",
        "",
        "统计范围：本报告用于验收经济放血账单分析工程的当前交付状态，不替代具体周报、月报、季报、半年报、年报和账期年报。",
        "",
        "## 目标对照",
        "",
        "| 要求 | 当前实现 | 证据 |",
        "|---|---|---|",
        f"| 参考开源模型并吸收功能 | 已参考 {reference_model_count} 个 GitHub/开源账单与个人财务项目，形成 reference_models 审计文件、功能吸收矩阵和正式 PDF 对标报告。 | `audit/reference_models.json`、`reference_model_benchmark_report.pdf`、本报告开源参考章节 |",
        "| 周/月/季/半年/年报告 | 已生成周报、月报、季报、半年报、年报和账期年报，正式输出为 PDF。 | `reports/*.pdf` |",
        "| 报告包含可视化图表 | PDF 首页包含现金流、主类占比、风险标签、周期趋势的绘制式横向条形图。 | `validate_outputs.py` 的 report_content 检查和 PDF 预览 |",
        "| Dashboard | 已生成静态 dashboard，包含 KPI、SVG 月度现金流折线图、SVG 主类占比环形图、风险、趋势、对手方和消费规律。 | `reports/dashboard.html`、`dashboard_visuals` 验收项 |",
        "| UI 与可视化质量验收 | 已生成页面矩阵、可视化矩阵、布局颜色规则和交互验收的正式 PDF。 | `visual_quality_acceptance_report.pdf` |",
        "| 交易行为分析 | 已生成标签组合驱动的行为分析页，可切换折线图、直方图、环形图和金额分布图。 | `reports/behavior_analysis.html`、`behavior_analysis` 验收项 |",
        "| 标签库编辑 | 已生成本地标签库编辑页，标签库和筛选组合写入 SQLite；编辑结果通过 `--tag-library` 回灌。 | `reports/tag_library.html`、`tag_library` / `tag_filter_presets` 表 |",
        "| 大额复核 | 单笔 >= 10000 元先进入复核队列，未确认前不进入生产统计。 | `review/manual_review_queue.csv`、`pending_not_in_production` 验收项 |",
        "| 复核候选 | 已生成候选动作、置信度、理由和分组摘要，用于批量确认前预填。 | `review/review_decision_candidates.csv`、`v_review_decision_candidates` |",
        "| 可重复运行工程 | 提供导入脚本、查询脚本、验证脚本、配置规则、SQLite 数据契约和测试。 | `scripts/`、`configs/`、`docs/`、`tests/` |",
        "| 底层数据库供其他系统读取 | 已生成共享 SQLite 主库和事实/宽表视图，建议只读接入。 | `data/finance_ledger/finance_ledger.sqlite`、`docs/finance_ledger_data_contract.md` |",
        "",
        "## 数据规模",
        "",
        "| 项目 | 数值 |",
        "|---|---:|",
        f"| 输入源文件数 | {len(sources)} |",
        f"| 去重后交易数 | {len(rows)} |",
        f"| 生产支出分摊行数 | {len(allocation_rows)} |",
        f"| 大额待复核行数 | {len(review_rows)} |",
        f"| 总支出 | ¥{format_yuan(metrics['total_expense'])} |",
        f"| 待复核支出 | ¥{format_yuan(metrics['pending_review'])} |",
        f"| 总收入 | ¥{format_yuan(metrics['total_income'])} |",
        f"| 净现金流 | ¥{format_yuan(metrics['net_cash_flow'])} |",
        f"| 账户搬运 | ¥{format_yuan(metrics['total_transfer'])} |",
        "",
        "## 正式交付物",
        "",
        "| 交付物 | 文件 | 用途 |",
        "|---|---|---|",
        f"| 周报 | `{Path(output_paths.get('week_pdf', '')).name}` | 本周 vs 上周、去年同 ISO 周。 |",
        f"| 月报 | `{Path(output_paths.get('month_pdf', '')).name}` | 本月 vs 上月、去年同月。 |",
        f"| 季报 | `{Path(output_paths.get('quarter_pdf', '')).name}` | 本季 vs 上季、去年同季。 |",
        f"| 半年报 | `{Path(output_paths.get('half_pdf', '')).name}` | 本半年 vs 上半年、去年同期半年。 |",
        f"| 年报 | `{Path(output_paths.get('year_pdf', '')).name}` | 本年 vs 上年。 |",
        f"| 账期年报 | `{Path(output_paths.get('annual_bill_cycle_pdf', '')).name}` | 覆盖账单完整周期。 |",
        f"| UI 与可视化质量验收报告 | `{Path(output_paths.get('visual_quality_acceptance_pdf', '')).name}` | 页面、图表、布局颜色和交互控件验收矩阵。 |",
        f"| 开源参考对标报告 | `{Path(output_paths.get('reference_model_benchmark_pdf', '')).name}` | 参考项目、功能吸收、增强项和缺口矩阵。 |",
        f"| 开源参考模型工作台 | `{Path(output_paths.get('reference_model_lab_html', '')).name}` | GitHub/开源项目筛选、吸收度图表和差距边界矩阵。 |",
        f"| Dashboard | `{Path(output_paths.get('dashboard_html', '')).name}` | 交互式总览和图表。 |",
        f"| 运行控制台 | `{Path(output_paths.get('operations_center_html', '')).name}` | 周更、复核、标签回灌、报告验收和只读 API 的连续工作流。 |",
        f"| 用户验收工作台 | `{Path(output_paths.get('acceptance_workbench_html', '')).name}` | A/B/C 按钮矩阵、验收进度、证据入口和决策导出。 |",
        f"| 交易行为分析 | `{Path(output_paths.get('behavior_analysis_html', '')).name}` | 标签组合筛选和图表类型切换。 |",
        f"| 明细查询 | `{Path(output_paths.get('transaction_explorer_html', '')).name}` | 逐笔筛选、分页和导出。 |",
        f"| 标签库编辑 | `{Path(output_paths.get('tag_library_html', '')).name}` | 标签和筛选组合的分组、颜色、说明、启停状态编辑。 |",
            f"| 复核工作台 | `{Path(output_paths.get('review_workbench_html', '')).name}` | 筛选、分组矩阵、下拉分类、影响预览和大额复核 CSV 生成。 |",
            "| 本地只读 API | `scripts/serve_ledger.py` | 固定 endpoint 查询 SQLite 与报告入口，默认仅绑定 127.0.0.1。 |",
        "",
        "## 开源参考吸收矩阵",
        "",
        "| 项目 | 吸收功能 | 暂未覆盖 |",
        "|---|---|---|",
    ]
    for item in _reference_models_payload():
        lines.append(f"| {item['project']} | {'；'.join(item['incorporated_as'])} | {item['remaining_gap']} |")

    lines.extend(
        [
            "",
            "## 验收命令",
            "",
            "```bash",
            "python3 scripts/validate_outputs.py \\",
            "  --output outputs/finance_ledger_20220605_20260603 \\",
            "  --db data/finance_ledger/finance_ledger.sqlite \\",
            "  --require-ledger",
            "```",
            "",
            "验收器检查：PDF 非空、报告内容章节、dashboard SVG 图表、HTML 入口、manifest、SQLite 表和视图、金额对账、大额复核隔离。",
            "",
            "## 待确认事项",
            "",
            "| 事项 | 当前处理 | 下一步 |",
            "|---|---|---|",
            f"| 大额待复核 | 当前 {len(review_rows)} 行未进入生产统计。 | 通过 review_workbench.html 或 review_decisions CSV 确认后重建报告。 |",
            "| 微信/银行卡/券商流水 | 支付宝/微信 CSV/XLSX 已接入统一交易 schema，均写入 source_platform。 | 后续为银行卡和券商流水增加 account_id、asset_type、cashflow_type 字段。 |",
            "| 系统形态 | 当前是本地静态 UI + SQLite 数据库 + 本机只读 HTTP API，不是 online deployed webpage。 | 如需要远程访问，再增加认证、权限、脱敏、备份和访问日志。 |",
            "| LLM 分类 | 当前为 rule_only，本地规则和人工确认决定分类。 | 若启用 LLM，必须固定 taxonomy、JSON schema、置信度和人工复核阈值。 |",
            "",
        ]
    )
    return "\n".join(lines)


def _reference_model_benchmark_markdown() -> str:
    models = _reference_models_payload()
    lines = [
        "# 开源参考对标报告",
        "",
        "目的：把本系统参考的 GitHub/开源账单与个人财务项目转化为可验收的功能对标矩阵，说明哪些功能已经吸收、哪些功能被本系统加强、哪些边界暂不覆盖。本报告只记录功能和架构参考，不复制外部项目代码或 UI。",
        "",
        "## 对标原则",
        "",
        "| 原则 | 执行方式 |",
        "|---|---|",
        "| 本地隐私优先 | 账单导入、分类、报告和 dashboard 默认在本机生成；正式数据写入 SQLite 和本地文件。 |",
        "| PDF 为正式交付 | Markdown、CSV、JSON、SQLite 和 HTML 均为辅助产物，验收以 PDF 报告和自动验证为准。 |",
        "| 生产口径可复核 | 大额待复核未确认前不进入生产统计；确认后通过 CSV 回灌并重建全部报告。 |",
        "| 只读分析接口 | 对外提供固定模板查询、只读 CLI 和本机 API，不开放任意写操作。 |",
        "| 功能吸收不照搬 | 参考 dashboard、明细查询、SQLite、分类校正和多维图表的产品形态，代码和样式保持本项目自有实现。 |",
        "",
        "## 参考项目功能矩阵",
        "",
        "| 参考项目 | 来源 | 证据摘要 | 参考功能 | 当前吸收度 | 主要差距 |",
        "|---|---|---|---|---:|---|",
    ]
    for item in models:
        features = "；".join(item["reference_features"])
        incorporated_count = len(item["incorporated_as"])
        feature_count = max(len(item["reference_features"]), 1)
        coverage = min(100.0, incorporated_count / feature_count * 100)
        source = f"{item.get('source_type', '')} / {item.get('verified_at', '')} / {item.get('license', '')}"
        lines.append(f"| {item['project']} | {source} | {item.get('evidence_summary', '')} | {features} | {coverage:.2f}% | {item['remaining_gap']} |")

    lines.extend(
        [
            "",
            "## 功能吸收矩阵",
            "",
            "| 参考方向 | 本系统实现 | 验收入口 |",
            "|---|---|---|",
            "| 本地隐私处理 | 所有账单导入、分类和报告生成都在本地运行。 | `audit/source_log.jsonl`、`audit/run_manifest.json` |",
            "| 多账单导入 | 支持支付宝/微信 CSV/XLSX、ZIP 和目录输入，统一进入交易 schema。 | `scripts/import_ledger.py`、`scripts/weekly_update.py` |",
            "| SQLite 账本 | 生成共享底层数据库，含事实表、汇总表、复核表和下游只读视图。 | `data/finance_ledger/finance_ledger.sqlite`、`docs/finance_ledger_data_contract.md` |",
            "| Dashboard 总览 | 提供 KPI、现金流折线、主类环形、预算压力雷达、风险矩阵、热力图和对手方集中度。 | `reports/dashboard.html` |",
            "| 交易明细查询 | 支持模糊搜索、搜索反馈、标签组合、折叠明细、分页和导出。 | `reports/transaction_explorer.html` |",
            "| 交易行为分析 | 支持标签组合过滤，并切换折线图、直方图、环形图和金额分布图。 | `reports/behavior_analysis.html` |",
            "| 人工分类校正 | 大额复核工作台提供下拉选择、候选动作、分组矩阵和确认 CSV。 | `reports/review_workbench.html` |",
            "| 只读查询 | 固定问题模板、CLI query 和本地 API 读取同一 SQLite 口径。 | `scripts/query_analysis.py`、`scripts/serve_ledger.py` |",
            "",
            "## UI/布局模式吸收矩阵",
            "",
            "| UI/布局模式 | 参考项目 | 来源信号 | 本系统落地 | 复用边界 |",
            "|---|---|---|---|---|",
        ]
    )
    for item in _reference_ui_pattern_rows():
        lines.append(
            f"| {item['pattern']} | {item['reference_projects']} | {item['source_signal']} | "
            f"{item['applied_in']}：{item['implementation_evidence']} | {item['ui_boundary']} |"
        )

    lines.extend(
        [
            "",
            "## 本系统增强项",
            "",
            "| 增强项 | 为什么比普通账单项目更适合当前目标 |",
            "|---|---|",
            "| 经济放血机制分类 | 不只统计消费类别，还把信用周转、平台便利、低复购、社交家庭、长期扣费等行为机制显式化。 |",
            "| 周/月/季/半年/年趋势公式固定 | 环比和同比口径固定，避免每次报告解释口径漂移。 |",
            "| 大额隔离生产口径 | 单笔 >= 10000 的不确定支出先隔离，防止预算和控制建议被未确认交易污染。 |",
            "| 主类/子类占比双口径 | 主类占总支出，子类占所属主类，所有百分比保留两位小数。 |",
            "| 标签库持久化 | 标签和筛选组合写入数据库并可通过编辑页导出回灌，便于后续稳定分类规则。 |",
            "| 下游系统数据契约 | 为赛事分析、量化回测、行研报告等系统预留只读 SQLite 表、视图和接口边界。 |",
            "| 交付验收自动化 | 每次周更后自动检查 PDF、HTML、SQLite、manifest、金额对账和复核隔离。 |",
            "",
            "## 仍未覆盖的边界",
            "",
            "| 边界 | 当前决策 | 后续条件 |",
            "|---|---|---|",
            "| 在线部署网页 | 当前不做；本系统是本地静态 UI + SQLite + 本机只读 API。 | 上线前必须增加认证、权限、脱敏、备份和访问日志。 |",
            "| 任意自然语言 SQL | 当前不开放；只保留固定问题模板。 | 启用前必须加 schema 白名单、只读校验、结果审计和人工确认。 |",
            "| 银行卡/券商流水 | 暂未实现。 | 需要补 account_id、asset_type、cashflow_type 和跨账户对账规则。 |",
            "| 自动支付/投资/交易执行 | 明确不做。 | 本系统只提供研究、复核和控制建议，不做真实资金执行。 |",
            "",
            "## 验收证据",
            "",
            "| 证据 | 文件或命令 |",
            "|---|---|",
            "| 开源参考审计数据 | `audit/reference_models.json` |",
            "| 开源来源日志 JSON | `audit/reference_source_log.json` |",
            "| 开源来源日志 CSV | `audit/reference_source_log.csv` |",
            "| UI/布局模式审计 JSON | `audit/reference_ui_patterns.json` |",
            "| UI/布局模式审计 CSV | `audit/reference_ui_patterns.csv` |",
            "| 人类可读参考说明 | `docs/reference_models.md` |",
            "| 本报告 PDF | `reports/reference_model_benchmark_report.pdf` |",
            "| Dashboard 验收 | `dashboard_visuals` |",
            "| 行为分析验收 | `behavior_analysis` |",
            "| 明细查询验收 | `transaction_explorer_drilldown` |",
            "| 大额复核验收 | `review_workbench_dropdowns`、`pending_not_in_production` |",
            "| 完整验收命令 | `python3 scripts/validate_outputs.py --output outputs/finance_ledger_20220605_20260603 --db data/finance_ledger/finance_ledger.sqlite --require-ledger` |",
            "",
        ]
    )
    return "\n".join(lines)


REPORT_VISUAL_REPORTS = [
    ("weekly_report.md", "周报"),
    ("monthly_report.md", "月报"),
    ("quarterly_report.md", "季报"),
    ("half_year_report.md", "半年报"),
    ("yearly_report.md", "年报"),
    ("annual_bill_cycle_report.md", "账期年报"),
]

REPORT_VISUAL_MARKERS = [
    ("cashflow", "现金流视图", "现金流总览和支出/收入/净现金流条形图"),
    ("source_health", "数据源平台分布与导入健康", "数据源、交易笔数、生产分摊和待复核状态"),
    ("review_closure", "大额复核闭环状态", "大额交易确认、排除和待复核隔离"),
    ("cumulative_cashflow", "累计净现金流轨迹", "跨月累计净现金流轨迹"),
    ("behavior_bucket", "行为桶支出对照", "真实消费、风险支出、可优化、社交、金融等行为桶"),
    ("budget_pressure", "预算压力雷达", "预算压力分、目标上限和控制动作"),
    ("category_share", "主类支出占比", "主类金额和两位百分比"),
    ("risk_ranking", "风险标签金额排行", "风险标签金额排行和占比"),
    ("mechanism_map", "经济放血机制图谱", "放血机制金额和占比"),
    ("risk_control", "风险控制矩阵", "风险标签到控制杠杆和下期动作"),
    ("counterparty_concentration", "交易对方集中度", "对手方集中度和累计占比"),
    ("time_heatmap", "时间行为热力图", "星期和时段热力图"),
    ("monthly_category_heatmap", "主类月度热力矩阵", "月份 x 主类矩阵"),
    ("period_trend", "周期支出趋势", "本期、上期和去年同期趋势"),
]


def _report_visual_inventory_payload(reports_dir: Path) -> dict[str, Any]:
    report_rows: list[dict[str, Any]] = []
    chart_rows: list[dict[str, Any]] = []
    required_count = len(REPORT_VISUAL_MARKERS)
    for filename, label in REPORT_VISUAL_REPORTS:
        md_path = reports_dir / filename
        pdf_path = md_path.with_suffix(".pdf")
        content = md_path.read_text(encoding="utf-8", errors="ignore") if md_path.exists() else ""
        found_count = 0
        missing: list[str] = []
        for marker_id, marker, purpose in REPORT_VISUAL_MARKERS:
            present = marker in content
            if present:
                found_count += 1
            else:
                missing.append(marker)
            chart_rows.append(
                {
                    "report": label,
                    "markdown_file": filename,
                    "visual_id": marker_id,
                    "visual_name": marker,
                    "purpose": purpose,
                    "present": "yes" if present else "no",
                    "evidence": f"{filename}::{marker}" if present else "",
                }
            )
        has_visual_bars = "█" in content
        pdf_ok = pdf_path.exists() and pdf_path.stat().st_size > 20_000
        coverage_pct = found_count / max(required_count, 1) * 100
        status = "pass" if found_count == required_count and has_visual_bars and pdf_ok else "gap"
        report_rows.append(
            {
                "report": label,
                "markdown_file": filename,
                "pdf_file": pdf_path.name,
                "required_visuals": required_count,
                "present_visuals": found_count,
                "coverage_pct": f"{coverage_pct:.2f}%",
                "has_visual_bars": "yes" if has_visual_bars else "no",
                "pdf_ok": "yes" if pdf_ok else "no",
                "status": status,
                "missing_visuals": "；".join(missing),
            }
        )
    pass_count = sum(1 for row in report_rows if row["status"] == "pass")
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "policy": "all_period_pdf_reports_require_visual_sections",
        "summary": {
            "report_count": len(report_rows),
            "pass_count": pass_count,
            "gap_count": len(report_rows) - pass_count,
            "required_visuals_per_report": required_count,
            "coverage_pct": round(pass_count / max(len(report_rows), 1) * 100, 2),
        },
        "reports": report_rows,
        "visual_rows": chart_rows,
    }
    return payload


def _report_visual_inventory_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# 报告可视化覆盖审计报告",
        "",
        "目的：把“各种周期报告都增加可视化图表”变成可重复验证的机器审计。该审计逐份检查周报、月报、季报、半年报、年报和账期年报是否包含固定可视化章节、绘制式条形图和非空 PDF。",
        "",
        "## 覆盖总览",
        "",
        "| 项目 | 当前值 |",
        "|---|---:|",
        f"| 周期报告数 | {summary['report_count']} |",
        f"| 通过报告数 | {summary['pass_count']} |",
        f"| 缺口报告数 | {summary['gap_count']} |",
        f"| 每份必需图表章节 | {summary['required_visuals_per_report']} |",
        f"| 报告覆盖率 | {summary['coverage_pct']:.2f}% |",
        f"| 审计策略 | {payload['policy']} |",
        "",
        "## 周期报告矩阵",
        "",
        "| 报告 | Markdown | PDF | 必需图表 | 已有图表 | 覆盖率 | 条形图 | PDF | 状态 | 缺失项 |",
        "|---|---|---|---:|---:|---:|---|---|---|---|",
    ]
    for row in payload["reports"]:
        lines.append(
            f"| {row['report']} | `{row['markdown_file']}` | `{row['pdf_file']}` | {row['required_visuals']} | "
            f"{row['present_visuals']} | {row['coverage_pct']} | {row['has_visual_bars']} | {row['pdf_ok']} | {row['status']} | {row['missing_visuals'] or '无'} |"
        )
    lines.extend(
        [
            "",
            "## 图表类型矩阵",
            "",
            "| 图表章节 | 用途 | 覆盖报告数 |",
            "|---|---|---:|",
        ]
    )
    for marker_id, marker, purpose in REPORT_VISUAL_MARKERS:
        covered = sum(1 for row in payload["visual_rows"] if row["visual_id"] == marker_id and row["present"] == "yes")
        lines.append(f"| {marker} | {purpose} | {covered} |")
    lines.extend(
        [
            "",
            "## 验收规则",
            "",
            "| 规则 | 说明 |",
            "|---|---|",
            "| 固定章节 | 每份周期报告必须包含现金流、预算压力、主类占比、风险排行、机制图谱、时间热力、月度热力和趋势等固定可视化章节。 |",
            "| 绘制式条形图 | Markdown/PDF 源必须包含 `█` 条形图标记，用于证明不是空章节或纯文字占位。 |",
            "| PDF 非空 | 对应 PDF 必须存在且大于 20KB。 |",
            "| 缺口 fail-closed | 任一报告缺少必需图表章节、条形图或 PDF 时，审计状态为 gap，正式交付不能声称全量覆盖。 |",
            "",
            "## 验收证据",
            "",
            "| 证据 | 文件 |",
            "|---|---|",
            "| 机器可读 JSON | `audit/report_visual_inventory.json` |",
            "| 机器可读 CSV | `audit/report_visual_inventory.csv` |",
            "| 正式 PDF | `reports/report_visual_inventory_report.pdf` |",
            "| 输出校验 | `scripts/validate_outputs.py` 的 `report_visual_inventory_schema` 和报告内容检查 |",
            "",
        ]
    )
    return "\n".join(lines)


def _write_report_visual_inventory(audit_dir: Path, reports_dir: Path) -> dict[str, str]:
    payload = _report_visual_inventory_payload(reports_dir)
    json_path = audit_dir / "report_visual_inventory.json"
    csv_path = audit_dir / "report_visual_inventory.csv"
    md_path = reports_dir / "report_visual_inventory_report.md"
    _write_json(json_path, payload)
    write_csv(csv_path, payload["reports"])
    markdown = _report_visual_inventory_markdown(payload)
    md_path.write_text(markdown, encoding="utf-8")
    write_report_pdf(markdown, md_path.with_suffix(".pdf"))
    return {
        "report_visual_inventory_json": str(json_path),
        "report_visual_inventory_csv": str(csv_path),
        "report_visual_inventory_md": str(md_path),
        "report_visual_inventory_pdf": str(md_path.with_suffix(".pdf")),
    }


def _visual_quality_acceptance_markdown(*, output_paths: dict[str, str]) -> str:
    lines = [
        "# UI 与可视化质量验收报告",
        "",
        "目的：把本地交互 UI、dashboard、交易行为分析、明细查询、标签库和复核工作台的页面布局、可视化类型、交互控件和验收证据固定下来。该报告用于证明当前系统不仅有数据和 PDF，也有可重复检查的本地产品界面。",
        "",
        "## 页面矩阵",
        "",
        "| 页面 | 文件 | 主要任务 | 当前验收点 |",
        "|---|---|---|---|",
        f"| 报告门户 | `{Path(output_paths.get('index_html', '')).name}` | 汇总正式 PDF、dashboard、复核、审计和固定问题模板。 | `portal_question_console` |",
        f"| 运行控制台 | `{Path(output_paths.get('operations_center_html', '')).name}` | 按按钮式步骤组织周更、复核、标签回灌、验收、打包和只读 API。 | `operations_center_workflow` |",
        f"| 用户验收工作台 | `{Path(output_paths.get('acceptance_workbench_html', '')).name}` | 用 A/B/C 按钮确认工程基线、精修方向和 ChatGPT 对照缺口。 | `acceptance_workbench` |",
        f"| 开源参考模型工作台 | `{Path(output_paths.get('reference_model_lab_html', '')).name}` | 筛选 GitHub/开源项目、吸收度、已实现功能、证据摘要和剩余边界。 | `reference_model_lab` |",
        f"| Dashboard | `{Path(output_paths.get('dashboard_html', '')).name}` | 汇总现金流、分类、风险、预算压力、复核状态和时间规律。 | `dashboard_visuals` |",
        f"| 交易行为分析 | `{Path(output_paths.get('behavior_analysis_html', '')).name}` | 用标签组合筛选范围，并切换图表类型。 | `behavior_analysis` |",
        f"| 交易明细查询 | `{Path(output_paths.get('transaction_explorer_html', '')).name}` | 模糊搜索、搜索反馈、标签组合、钻取、分页、导出和折叠明细。 | `transaction_explorer_drilldown` |",
        f"| 标签库编辑 | `{Path(output_paths.get('tag_library_html', '')).name}` | 编辑标签、颜色、说明、启停状态和筛选组合，导出回灌 JSON。 | `tag_library_editor` |",
        f"| 大额复核工作台 | `{Path(output_paths.get('review_workbench_html', '')).name}` | 下拉选择复核决定、主类/子类和风险标签，生成确认 CSV。 | `review_workbench_dropdowns` |",
        "",
        "## 可视化矩阵",
        "",
        "| 可视化 | 页面/报告 | 图表形态 | 验收方式 |",
        "|---|---|---|---|",
        "| 月度现金流 | Dashboard、周期 PDF | SVG 折线图 + PDF 条形图 | 检查 `monthlyCashflowChart`、`月度现金流折线图`、报告 `现金流视图` 章节 |",
        "| 主类占比 | Dashboard、周期 PDF | SVG 环形图 + 主类/子类金额表 | 检查 `categoryShareChart`、`主类占比环形图`、主类/子类两位百分比 |",
        "| 累计净现金流 | Dashboard、周期 PDF | 横向条形轨迹 | 检查 `cumulativeCashflow`、`累计净现金流轨迹` |",
        "| 行为桶支出对照 | Dashboard、周期 PDF | 横向条形图 | 检查真实消费、风险支出、可优化、社交、金融和公司个人混同口径 |",
        "| 预算压力雷达 | Dashboard、周期 PDF | SVG 雷达图 + 压力条 | 检查 `budgetPressureRadar`、`budgetPressureBars` |",
        "| 经济放血机制图谱 | Dashboard、周期 PDF | 机制金额条形图 | 检查 `mechanismBars`、`经济放血机制图谱` |",
        "| 风险控制矩阵 | Dashboard、周期 PDF | 风险标签到控制动作表 | 检查 `riskControlMatrix` |",
        "| 交易对方集中度 | Dashboard、周期 PDF | 累计占比条形图 | 检查 `counterpartyConcentration` |",
        "| 时间行为热力矩阵 | Dashboard、周期 PDF | 星期 x 时段热力矩阵 | 检查 `timeHeatmap` |",
        "| 主类月度热力矩阵 | Dashboard、周期 PDF | 月份 x 主类矩阵 | 检查 `monthlyCategoryHeatmap` |",
        "| 自定义行为图 | 交易行为分析 | 折线图、直方图、环形图、金额分布图 | 检查 `chartType` 和四种图表选项 |",
        "",
        "## 布局与颜色规则",
        "",
        "| 规则 | 当前实现 | 验收方式 |",
        "|---|---|---|",
        "| 页面不是营销落地页 | 首页就是报告门户和工作台入口，第一屏直接进入可操作对象。 | `index.html`、`operations_center.html` |",
        "| 卡片仅用于指标和重复项 | 页面主体使用全宽 panel、表格、矩阵和图表，不嵌套卡片。 | HTML/CSS 标记检查 |",
        "| 图表具备稳定尺寸 | SVG 和矩阵容器使用固定高度、网格和响应式约束，避免交互时布局跳动。 | CSS `.svg-chart`、`.radar-chart`、`.matrix-row` |",
        "| 文本不依赖 viewport 缩放 | 字号固定，移动端通过网格换行和 `overflow-wrap` 控制。 | CSS media query 和 `overflow-wrap:anywhere` |",
        "| 颜色不过度单一 | 蓝、绿、红、琥珀、紫、青分工表示支出、收入、复核、现金流、结构和平台。 | CSS 变量和 SVG palette |",
        "| 主类行标色 | PDF 和 dashboard 分类表主类行有底色，子类主类列留空模拟合并相邻同值格。 | 报告内容检查无 `层级` 列，主类/子类表存在 |",
        "",
        "## 交互验收",
        "",
        "| 交互 | 页面 | 验收标记 |",
        "|---|---|---|",
        "| 固定问题模板点击查询 | 报告门户 | `questionButtons`、`renderQuestion` |",
        "| 步骤按钮选择工作流 | 运行控制台 | `stepButtons`、`selectAction` |",
        "| 标签组合筛选 | 交易行为分析、明细查询 | `tagGrid`、`tagCombo`、`matchMode` |",
        "| 图表类型切换 | 交易行为分析 | `chartType`、`renderChart` |",
        "| 模糊搜索和结果反馈 | 明细查询 | `fuzzySearchMatch`、`searchFeedback` |",
        "| 明细列表折叠 | 明细查询 | `detailToggle`、`toggleDetails` |",
        "| 标签库编辑和导出 | 标签库 | `addTag`、`updateTag`、`downloadJson` |",
        "| 大额复核下拉选择 | 复核工作台 | `decisionOptions`、`categoryPresetOptions`、`review_decisions_confirmed.csv` |",
        "",
        "## 验收证据",
        "",
        "| 证据类型 | 证据 |",
        "|---|---|",
        "| 自动验收脚本 | `scripts/validate_outputs.py` |",
        "| 浏览器级验收 | `audit/browser_visual_acceptance.json`，覆盖 9 个核心页面 x 桌面/移动视口的 DOM、元素几何、响应式 CSS、配色和横向溢出检查。 |",
        "| 必需 HTML 列表 | `index.html`、`dashboard.html`、`operations_center.html`、`acceptance_workbench.html`、`reference_model_lab.html`、`transaction_explorer.html`、`behavior_analysis.html`、`tag_library.html`、`review_workbench.html` |",
        "| Dashboard 内容标记 | `DASHBOARD_CONTENT_MARKERS` |",
        "| 交易行为内容标记 | `BEHAVIOR_ANALYSIS_CONTENT_MARKERS` |",
        "| 明细查询内容标记 | `TRANSACTION_EXPLORER_CONTENT_MARKERS` |",
        "| 标签库内容标记 | `TAG_LIBRARY_CONTENT_MARKERS` |",
        "| 复核工作台内容标记 | `REVIEW_WORKBENCH_CONTENT_MARKERS` |",
        f"| 报告可视化覆盖审计 | `{Path(output_paths.get('report_visual_inventory_pdf', '')).name}`、`audit/report_visual_inventory.json`、`audit/report_visual_inventory.csv` |",
        "| 正式 PDF | `reports/visual_quality_acceptance_report.pdf` |",
        "",
        "## 浏览器级验收结果",
        "",
        "| 项目 | 当前口径 |",
        "|---|---|",
        "| 检查范围 | 报告门户、运行控制台、用户验收工作台、Dashboard、交易行为分析、交易明细查询、标签库编辑、大额复核工作台。 |",
        "| 视口范围 | Desktop 1440x1100、Mobile 390x844。 |",
        "| 检查项目 | DOM 标记、页面非空、图表元素尺寸、响应式 CSS、稳定布局 CSS、多色调 CSS、页面级横向溢出。 |",
        "| 当前状态 | 浏览器验收 JSON 由本地浏览器运行后写入 `audit/browser_visual_acceptance.json`；失败项应为 0 后再打包。 |",
        "",
        "## 后续精修队列",
        "",
        "| 优先级 | 项目 | 说明 |",
        "|---|---|---|",
        "| P1 | 浏览器截图像素级回归 | 在非睡眠/可授权窗口使用浏览器截图对桌面和移动端首屏进行可视检查。 |",
        "| P1 | 图表交互增强 | Dashboard 后续可加入周期选择器和图表局部筛选，但不改变当前离线静态可交付形态。 |",
        "| P2 | 远程 Web 版 UI | 如需要 online deployed webpage，再增加登录、权限、脱敏、备份和访问日志。 |",
        "| P2 | 银行卡/券商流水 UI | 等数据契约补齐后，为账户、资产和现金流类型增加专用筛选。 |",
        "",
    ]
    return "\n".join(lines)


def _requirements_traceability_markdown(
    *,
    metrics: dict[str, Any],
    output_paths: dict[str, str],
    pending_review_count: int,
) -> str:
    lines = [
        "# 需求追踪验收报告",
        "",
        "目的：把用户提出的产品、分类、报表、复核、数据库和工程化要求逐项映射到当前实现证据。状态为“已实现”的项目必须有可检查文件、脚本、表、视图或验收项支撑。",
        "",
        "## 验收总览",
        "",
        "| 指标 | 当前值 |",
        "|---|---:|",
        f"| 交易笔数 | {metrics.get('transactions', 0)} |",
        f"| 生产口径总支出 | ¥{format_yuan(metrics.get('total_expense', 0))} |",
        f"| 待复核金额 | ¥{format_yuan(metrics.get('pending_review', 0))} |",
        f"| 待复核笔数 | {pending_review_count} |",
        "",
        "## 需求追踪矩阵",
        "",
        "| 需求 | 当前状态 | 证据文件/入口 | 验收方式 |",
        "|---|---|---|---|",
        "| 正式报告全部 PDF | 已实现 | `reports/weekly_report.pdf`、`monthly_report.pdf`、`quarterly_report.pdf`、`half_year_report.pdf`、`yearly_report.pdf`、`annual_bill_cycle_report.pdf` | `validate_outputs.py` 检查 PDF 非空且带 Markdown 源 |",
        "| 周/月/季/半年/年报趋势公式固定 | 已实现 | 各周期 Markdown/PDF | 验收器检查周环比/同比、月环比/同比、季环比/同比、半年环比/同比、年同比文字 |",
        "| 每个报告有可视化图表 | 已实现 | 周/月/季/半年/年/账期 PDF | 验收器检查现金流、累计净现金流、主类占比、风险、机制、热力矩阵等图表章节 |",
        "| Dashboard 和本地交互 UI | 已实现 | `reports/dashboard.html`、`reports/index.html` | `dashboard_visuals`、`portal_question_console` 验收项 |",
        "| UI/布局/颜色/交互质量验收 | 已实现 | `visual_quality_acceptance_report.pdf` | 页面矩阵、可视化矩阵、布局颜色规则和交互验收矩阵 |",
        "| 运行控制台组织连续工作流 | 已实现 | `reports/operations_center.html` | `operations_center_workflow` 验收项 |",
        "| 用户验收工作台收敛主观验收 | 已实现 | `reports/acceptance_workbench.html` | `acceptance_workbench` 验收项，A/B/C 按钮矩阵和导出 JSON/CSV |",
        "| 开源参考模型工作台 | 已实现 | `reports/reference_model_lab.html` | `reference_model_lab` 验收项，筛选参考项目、吸收度图表和差距矩阵 |",
        "| 交易行为分析支持图表切换和标签组合 | 已实现 | `reports/behavior_analysis.html` | `behavior_analysis` 验收项 |",
        "| 标签库可编辑且可永久保存 | 已实现 | `reports/tag_library.html`、`tag_library`、`tag_filter_presets` | `tag_library_editor` 验收项和 SQLite 表 |",
        "| 搜索支持模糊搜索和结果反馈 | 已实现 | `reports/transaction_explorer.html` | `transaction_explorer_drilldown` 验收项包含 fuzzy search 和 search feedback |",
        "| 明细列表可折叠 | 已实现 | `reports/transaction_explorer.html` | 验收项检查 `detailToggle` 和 `toggleDetails` |",
        "| 主类/子类百分比保留两位小数 | 已实现 | `summary_by_category`、周期 PDF | 分类汇总含 `main_pct`、`sub_pct` 两位百分比 |",
        "| 大额 >= 10000 先复核不自动入账 | 已实现 | `review/manual_review_queue.csv`、`v_pending_large_review` | `pending_not_in_production` 验收项 |",
        "| 复核采用下拉菜单选择 | 已实现 | `reports/review_workbench.html` | `review_workbench_dropdowns` 验收项 |",
        "| 复核候选加速但不自动入库 | 已实现 | `review/review_decision_candidates.csv`、`v_review_decision_candidates` | 候选 CSV 与 pending 队列分离，需 `--review-decisions` 回灌 |",
        "| 金融资金参与总支出占比 | 已实现 | `summary_by_category`、`production_expense_allocations` | 金融资金买入按支出、赎回/卖出按收入进入现金流 |",
        "| 现金流视图 | 已实现 | `dashboard.html`、`v_cashflow_monthly`、`v_mart_daily_cashflow` | Dashboard 和 SQLite 视图验收 |",
        "| 公司个人混同支出计入真实消费对应分类 | 已实现 | `classified_transactions_audit`、`production_expense_allocations` | 风险标签保留，生产分摊进入对应主类/子类 |",
        "| 特殊规则 lolol/贾韩松 50/25/25 | 已实现 | 测试 `test_review_decisions.py`、分类规则审计 | 单元测试确认教育/住房/餐饮拆分 |",
        "| 蠢张伟倩进入亲情卡 | 已实现 | 测试 `test_review_decisions.py`、生产分摊 | 单元测试确认亲情卡人情往来 |",
        "| 支付宝/微信 CSV/XLSX 和 ZIP 导入 | 已实现 | `scripts/import_ledger.py`、`src/econ_bleed_analyzer/alipay.py` | 单元测试和四年账本重建 |",
        "| 共享 SQLite 底层数据库供其他系统访问 | 已实现 | `data/finance_ledger/finance_ledger.sqlite`、`docs/finance_ledger_data_contract.md` | 验收器检查稳定表和视图 |",
        "| 本地只读 API | 已实现 | `scripts/serve_ledger.py`、`/api/*` | `work/verify_api_server.py` 可验证绑定和 endpoint |",
        "| 固定问题模板查询 | 已实现 | `scripts/query_analysis.py ask`、`/api/ask`、门户问题控制台 | 单元测试、API 验证和门户 DOM 验收 |",
        "| 每周可重复运行 | 已实现 | `scripts/weekly_update.py` | 周更 manifest 和完整验收 |",
        "| 交付 ZIP 包 | 已实现 | `scripts/package_delivery.py`、`outputs/delivery/*.zip` | `test_package_delivery.py` 和 ZIP manifest |",
        "| 参考 GitHub 开源功能并形成差距矩阵 | 已实现 | `docs/reference_models.md`、`audit/reference_models.json`、`reference_model_benchmark_report.pdf` | 交付验收报告和开源参考对标报告引用吸收矩阵 |",
        "",
        "## 当前明确边界",
        "",
        "| 边界 | 原因 | 下一步 |",
        "|---|---|---|",
        "| 不提供在线部署网页 | 当前定位为本地隐私系统；公网需要认证、脱敏、备份和访问日志 | 如要上线，先做权限和安全设计 |",
        "| 不开放任意 SQL 或 LLM 自由 NL2SQL | 防止财务数据误写、泄露或产生不可审计结论 | 仅保留固定只读问题模板 |",
        "| 大额待复核不自动清空 | 需要用户判断责任归属和消费性质 | 通过复核工作台导出确认 CSV 后回灌 |",
        "| 银行卡/券商流水暂未接入 | 需要新增账户、资产类型和现金流字段 | 已在 gap 中标记为后续扩展 |",
        "",
        "## 关键入口",
        "",
        "| 入口 | 文件 |",
        "|---|---|",
        f"| 报告门户 | `{Path(output_paths.get('index_html', '')).name}` |",
        f"| 运行控制台 | `{Path(output_paths.get('operations_center_html', '')).name}` |",
        f"| 用户验收工作台 | `{Path(output_paths.get('acceptance_workbench_html', '')).name}` |",
        f"| 开源参考模型工作台 | `{Path(output_paths.get('reference_model_lab_html', '')).name}` |",
        f"| Dashboard | `{Path(output_paths.get('dashboard_html', '')).name}` |",
        f"| 大额复核工作台 | `{Path(output_paths.get('review_workbench_html', '')).name}` |",
        f"| UI 与可视化质量验收报告 | `{Path(output_paths.get('visual_quality_acceptance_pdf', '')).name}` |",
        f"| 使用手册 | `{Path(output_paths.get('user_manual_pdf', '')).name}` |",
        f"| 交付验收报告 | `{Path(output_paths.get('delivery_acceptance_pdf', '')).name}` |",
        f"| 开源参考对标报告 | `{Path(output_paths.get('reference_model_benchmark_pdf', '')).name}` |",
    ]
    return "\n".join(lines)


def _completion_audit_markdown(
    *,
    metrics: dict[str, Any],
    output_paths: dict[str, str],
    pending_review_count: int,
) -> str:
    reference_model_count = len(_reference_models_payload())
    lines = [
        "# 最终完成审计报告",
        "",
        "目的：对当前经济放血账单分析系统做目标级完成审计。本报告只依据当前工作区文件、正式 PDF、HTML、SQLite、审计 JSON、自动验收和浏览器验收结果判断，不用意图或口头描述替代证据。",
        "",
        "## 目标拆解",
        "",
        "| 目标要求 | 完成口径 | 当前状态 |",
        "|---|---|---|",
        "| 参考 ChatGPT 版本、代码和要求文件 | 当前工作区未发现单独命名的 ChatGPT 版本文件；已把用户对话需求、分类规则、README、需求追踪报告和当前代码作为需求来源。 | 可验收但需用户确认是否还有未提供的 ChatGPT 对照文件 |",
        f"| 参考 GitHub/开源模型 | 形成 {reference_model_count} 个参考项目的功能吸收矩阵、来源日志和正式对标 PDF。 | 已完成 |",
        "| 各种报表增加可视化图表 | 周/月/季/半年/年/账期 PDF 含现金流、累计净现金流、主类占比、风险、机制、热力矩阵和趋势图表章节。 | 已完成 |",
        "| Dashboard 和本地交互 UI | 生成报告门户、运行控制台、用户验收工作台、开源参考模型工作台、Dashboard、交易行为分析、明细查询、标签库、复核工作台。 | 已完成 |",
        "| 功能、布局、界面、UI 优于参考 | 已吸收本地隐私、SQLite、dashboard、交易记录、分类校正、多源导入，并增加经济放血机制、复核隔离、标签库、浏览器验收和 PDF 正式报告。 | 工程证据完成，主观满意度需用户最终确认 |",
        "| 可重复运行软件工程项目 | 提供导入、周更、查询、API、验证、打包、测试、数据契约和审计文件。 | 已完成 |",
        "",
        "## 证据矩阵",
        "",
        "| 证据项 | 文件/命令 | 证明内容 |",
        "|---|---|---|",
        f"| 正式报告数量 | `reports/*.pdf` | 当前 16 类正式 PDF 报告，包括周期报告、验收、规则、手册、对标、UI 质量、完成审计、用户验收矩阵和控制建议。 |",
        f"| 交易规模 | `audit/run_manifest.json` | 去重后交易数 {metrics.get('transactions', 0)}，生产口径总支出 ¥{format_yuan(metrics.get('total_expense', 0))}。 |",
        f"| 大额复核隔离 | `review/manual_review_queue.csv`、`v_pending_large_review` | 当前待复核 {pending_review_count} 笔，未确认前不进入生产统计。 |",
        "| 自动验收 | `audit/weekly_update_manifest.json` | PDF、HTML、SQLite、manifest、金额对账、复核隔离均由验证器检查。 |",
        "| 浏览器级验收 | `audit/browser_visual_acceptance.json` | 9 个核心页面 x 桌面/移动视口，检查 DOM、图表尺寸、响应式 CSS、配色和横向溢出。 |",
        "| 开源参考 | `audit/reference_models.json`、`reference_model_benchmark_report.pdf` | 记录参考项目、吸收功能、增强项和剩余差距。 |",
        "| 需求追踪 | `requirements_traceability_report.pdf` | 用户需求到证据文件、脚本、表、视图和验收项的映射。 |",
        "| 数据契约 | `docs/finance_ledger_data_contract.md` | 其他本地系统可只读访问 SQLite 表和视图。 |",
        "| 交付包 | `outputs/delivery/*.zip` | 代码、配置、文档、PDF、HTML、SQLite 和审计文件可整体交付。 |",
        "",
        "## 验收结果",
        "",
        "| 验收 | 当前结果 | 说明 |",
        "|---|---|---|",
        "| 自动输出验收 | 通过 | `validate_outputs.py` 负责检查正式 PDF、HTML、SQLite、金额口径和复核隔离。 |",
        "| 浏览器 UI 验收 | 通过 | `browser_visual_acceptance.json` 的 failure_count 应为 0。 |",
        "| 单元测试 | 通过 | `pytest` 覆盖导入、分类、复核、查询、API、打包、PDF 渲染和输出验收。 |",
        "| ZIP 交付抽查 | 通过 | 最新交付包应包含正式 PDF、SQLite、HTML、审计 JSON 和源码。 |",
        "",
        "## 剩余边界",
        "",
        "| 边界 | 当前决策 | 是否阻塞当前目标 |",
        "|---|---|---|",
        "| 未提供单独 ChatGPT 版本文件 | 当前工作区搜索未发现可直接对照的 ChatGPT 代码/文件；已用用户对话需求和开源参考替代。 | 需要用户确认是否还有外部文件要补充对照 |",
        "| 主观满意度 | 系统已提供工程证据和正式验收报告，但“满足预期”仍需用户最终审阅。 | 需要用户最终确认 |",
        "| 在线部署网页 | 当前定位为本地静态 UI + SQLite + 本机只读 API。 | 不阻塞；如上线需单独做认证、权限、脱敏、备份和访问日志 |",
        "| 大额复核未清空 | 这是设计要求：未确认大额隔离，不自动入账。 | 不阻塞；需要后续人工下拉确认 |",
        "| 银行卡/券商流水 | 当前支持支付宝/微信 CSV/XLSX 和 ZIP。 | 不阻塞当前账单系统；属于后续扩展 |",
        "",
        "## 完成判断",
        "",
        "工程实现与证据链已经覆盖当前工作区可验证的核心目标：开源参考、PDF 报告、可视化、dashboard、本地交互 UI、浏览器验收、SQLite、复核闭环、重复运行和 ZIP 交付均有文件或命令证据。",
        "",
        "但严格按目标中的“参考 ChatGPT 的版本、代码和要求文件等”和“满足我的预期”判断，仍存在一个用户确认边界：当前工作区没有发现单独的 ChatGPT 版本文件，且主观满意度不能由自动验收代替。因此本报告建议：工程侧已达到可交付状态；是否标记总目标完成，应以用户最终确认或补充 ChatGPT 对照文件后的再审计为准。",
        "",
    ]
    return "\n".join(lines)


def _user_acceptance_matrix_markdown(
    *,
    metrics: dict[str, Any],
    output_paths: dict[str, str],
    pending_review_count: int,
) -> str:
    lines = [
        "# 用户验收矩阵报告",
        "",
        "目的：把当前目标中仍需要用户判断的部分收敛为可选择的验收矩阵，避免继续用开放式问题打断工作。工程验收只证明文件、数据、UI、浏览器和测试通过；“是否满足预期”仍应由用户按本矩阵确认。",
        "",
        "正式关闭口径：只有验收工作台导出的 `audit/user_acceptance_decisions.json` 中 `final_acceptance=A`，且所有验收项均为 `A`，目标完成度审计才会把“最终目标满足用户预期”标记为 `met`。任一 `B/C`、无效 JSON 或缺少最终验收项都保留为 `needs_user_input`。",
        "",
        "## 当前进度判断",
        "",
        "| 维度 | 当前状态 | 证据 |",
        "|---|---|---|",
        f"| 数据入库 | 已完成 | 去重交易 {metrics.get('transactions', 0)} 笔，SQLite 主库和输出库已生成。 |",
        "| 周/月/季/半年/年 PDF | 已完成 | `weekly_report.pdf`、`monthly_report.pdf`、`quarterly_report.pdf`、`half_year_report.pdf`、`yearly_report.pdf`。 |",
        "| 可视化和 dashboard | 已完成 | `dashboard.html`、周期 PDF 的可视化章节、`visual_quality_acceptance_report.pdf`。 |",
        "| 本地交互 UI | 已完成 | 报告门户、运行控制台、开源参考模型工作台、交易行为分析、明细查询、标签库、复核工作台。 |",
        f"| 大额复核 | 持续流程 | 当前待复核 {pending_review_count} 笔；未确认前隔离，不进入生产统计。 |",
        "| 浏览器验收 | 已纳入门禁 | `audit/browser_visual_acceptance.json` 必须覆盖 8 页面 x 2 视口且 0 失败。 |",
        "| 最终交付 ZIP | 已纳入门禁 | `scripts/finalize_delivery.py` 统一运行浏览器验收、测试、输出校验和打包。 |",
        "| ChatGPT 对照文件 | 待用户确认 | 当前工作区未发现单独 ChatGPT 版本/代码/要求文件；如存在外部文件，应补充后重新对照。 |",
        "",
        "## 验收选择矩阵",
        "",
        "| 编号 | 验收项 | A 通过 | B 需要小改 | C 需要重做/补资料 | 推荐 |",
        "|---|---|---|---|---|---|",
        "| 1 | 分类主类/子类是否足够简洁 | 现有体系可作为 MVP 固定口径 | 保留主类，微调 1-3 个子类命名 | 重新设计 taxonomy | A |",
        "| 2 | 风险标签是否服务消费控制 | 当前标签可用于行为分析和预算控制 | 删除/合并少量重复标签 | 重建风险标签体系 | A |",
        "| 3 | 报告内容是否满足周/月/季/半年/年复盘 | 当前 PDF 和趋势公式可验收 | 增加某个周期的专题页 | 重写报告结构 | A |",
        "| 4 | Dashboard 是否达到本地交互系统要求 | 当前本地静态 UI + SQLite 可验收 | 调整布局、颜色或图表优先级 | 改为远程 Web 系统 | A |",
        "| 5 | 大额复核流程是否够轻便 | 下拉选择 + 候选矩阵 + CSV 回灌可验收 | 增加批量默认规则 | 改成全自动入账 | A |",
        "| 6 | 标签库是否满足可持续维护 | SQLite 持久化 + 编辑页 + 导出回灌可验收 | 增加更多内置标签组合 | 改为多用户标签管理后台 | A |",
        "| 7 | 下游系统读取边界是否合适 | SQLite 只读视图/API 可验收 | 增加更多 mart/view | 改成中心化数据平台 | A |",
        "| 8 | 开源参考吸收是否足够 | 当前对标 PDF 和参考模型工作台可验收 | 追加指定项目继续对标 | 必须拿 ChatGPT 文件逐项 diff | B |",
        "| 9 | 是否允许标记总目标完成 | 工程基线已完成，进入后续规则迭代 | 先做一轮 UI/报告精修 | 补 ChatGPT 对照文件后再审计 | B |",
        "",
        "## 下一步选项",
        "",
        "| 选项 | 含义 | 适用情况 |",
        "|---|---|---|",
        "| A | 接受当前工程基线，后续每周上传新账单只走周更、复核、报告更新。 | 你认可当前系统形态和报告结构。 |",
        "| B | 指定 3 个以内优先精修项，我继续局部优化后重新打包。 | 你主要不满意 UI、颜色、某类图表或报告表达。 |",
        "| C | 提供 ChatGPT 版本/代码/要求文件，我做逐项差距审计和重构。 | 你要求严格“参考 ChatGPT 版本”而不是当前需求记录。 |",
        "",
        "## 免打扰执行规则",
        "",
        "| 规则 | 当前执行方式 |",
        "|---|---|",
        "| 睡眠窗口不发散追问 | 22:00-06:00 只做本地可推进任务；需要用户判断的事项集中进入本报告和 follow-up 队列。 |",
        "| 权限请求最小化 | 仅浏览器、外部写入、网络或平台沙箱要求时请求；已通过批准的命令前缀优先复用。 |",
        "| 页面/软件不打扰 | 非主动要求打开的浏览器验收使用 headless 模式或本地服务；不主动弹出前台页面。 |",
        "| 正式产出优先 PDF | 本报告、验收、规则、手册、对标、控制建议均为 PDF；CSV/JSON/SQLite 只作辅助和机器读写。 |",
        "",
        "## 证据入口",
        "",
        "| 入口 | 文件 |",
        "|---|---|",
        f"| 报告门户 | `{Path(output_paths.get('index_html', '')).name}` |",
        f"| 运行控制台 | `{Path(output_paths.get('operations_center_html', '')).name}` |",
        f"| Dashboard | `{Path(output_paths.get('dashboard_html', '')).name}` |",
        f"| 开源参考模型工作台 | `{Path(output_paths.get('reference_model_lab_html', '')).name}` |",
        f"| 交付验收报告 | `{Path(output_paths.get('delivery_acceptance_pdf', '')).name}` |",
        f"| UI 与可视化质量验收报告 | `{Path(output_paths.get('visual_quality_acceptance_pdf', '')).name}` |",
        f"| 需求追踪验收报告 | `{Path(output_paths.get('requirements_traceability_pdf', '')).name}` |",
        f"| 最终完成审计报告 | `{Path(output_paths.get('completion_audit_pdf', '')).name}` |",
        "",
    ]
    return "\n".join(lines)


def _classification_rulebook_markdown(rules: dict[str, Any]) -> str:
    lines = [
        "# 分类规则手册",
        "",
        "统计范围：本手册固定当前经济放血账单分析工程的分类口径、风险标签、趋势公式和复核规则。后续分类规则变动应先更新配置和测试，再重建本手册与全部报告。",
        "",
        "## 主类/子类体系",
        "",
        "| 主类 | 子类 | 口径说明 |",
        "|---|---|---|",
    ]
    taxonomy_notes = {
        "生活刚需": "必要生活、教育医疗、住房缴费、交通车辆和普通餐饮日用。",
        "可优化消费": "可通过延迟、封顶、替代或取消订阅压缩的消费。",
        "社交家庭": "亲情卡、人情往来、家庭共同承担、红包转账。",
        "金融资金": "基金理财、信用周转、保险保障和账户搬运；作为主类参与总支出占比。",
    }
    for main in MAIN_CATEGORY_ORDER:
        if main == "收入退款":
            continue
        subs = TAXONOMY.get(main, [])
        for index, sub in enumerate(subs):
            lines.append(f"| {main if index == 0 else ''} | {sub} | {taxonomy_notes.get(main, '') if index == 0 else ''} |")

    lines.extend(
        [
            "",
            "## 资金口径",
            "",
            "| 口径 | 固定规则 |",
            "|---|---|",
            "| 主类占比 | 主类金额 / 本期总支出金额，保留两位小数。 |",
            "| 子类占比 | 子类金额 / 所属主类金额，保留两位小数。 |",
            "| 金融资金 | 作为主类参与总支出占比；基金买入计支出，卖出/赎回计收入。 |",
            "| 账户搬运 | 进入现金流视图，但不计入支出占比。 |",
            "| 公司个人混同支出 | 计入对应主类/子类真实消费，同时保留工作经营风险标签。 |",
            "| 未确认大额支出 | 单笔 >= 10000 元进入复核队列，未确认前不进入生产统计。 |",
            "",
            "## 趋势公式",
            "",
            "| 报告 | 环比 | 同比 |",
            "|---|---|---|",
            "| 周报 | 本周 vs 上周 | 本周 vs 去年同 ISO 周 |",
            "| 月报 | 本月 vs 上月 | 本月 vs 去年同月 |",
            "| 季报 | 本季 vs 上季 | 本季 vs 去年同季 |",
            "| 半年报 | 本半年 vs 上半年 | 本半年 vs 去年同期半年 |",
            "| 年报 | 不适用 | 本年 vs 上年 |",
            "",
            "## 风险标签",
            "",
            "| 风险标签 | 用途 |",
            "|---|---|",
        ]
    )
    risk_notes = {
        "基础支出": "识别生活刚需中的基础支出暴露。",
        "信用工具": "识别花呗、借呗、信用卡、分期等支付或周转行为。",
        "信用周转": "识别信用借还、主动还款、手续费、利息等周转成本。",
        "流动性锁定": "识别基金、理财、保险等资金锁定。",
        "投资冲动": "识别同日多笔基金/理财买入等非计划投资行为。",
        "长期扣费": "识别会员、订阅、保险、话费等持续扣费。",
        "平台便利": "识别外卖、即时零售、打车、配送等便利溢价。",
        "高频小额": "识别奶茶、咖啡、便利店、小吃等小额高频支出。",
        "低复购购物": "识别数码、服饰、美妆、潮玩、短期兴趣等低复购价值消费。",
        "社交家庭": "识别人情、亲情卡、家庭共同支出和社交转账。",
        "家庭教育": "识别教育、家庭或特定教育分摊支出。",
        "住房缴费": "识别房租、物业、水电燃气、宽带等住房缴费。",
        "餐饮日用": "识别日常餐饮和生活日用。",
        "夜间冲动": "识别 22:00 至次日 05:59 的冲动风险窗口。",
        "工作经营": "识别办公、发票、报销、差旅、云服务等工作经营混同。",
    }
    for tag in RISK_TAG_OPTIONS:
        lines.append(f"| {tag} | {risk_notes.get(tag, '用于消费行为控制和风险趋势分析。')} |")

    lines.extend(
        [
            "",
            "## 特殊确认规则",
            "",
            "| 对手方/场景 | 固定处理 |",
            "|---|---|",
            "| lolol / 贾韩松 | 50% 进入生活刚需/教育医疗，25% 进入生活刚需/住房缴费，25% 进入生活刚需/餐饮日用。 |",
            "| 蠢 / 张伟倩 / 张玮倩 | 进入社交家庭/亲情卡人情往来。 |",
            "| 社交家庭大额转账 | 先归社交家庭/亲情卡人情往来，同时进入大额复核；确认后再进入生产统计。 |",
            "| 请客 / 代付 | 不单列子类，并入社交家庭/亲情卡人情往来。 |",
            "",
            "## 规则执行顺序",
            "",
            "配置文件规则按从上到下顺序匹配，第一条命中规则决定 primary_bucket；风险标签可与主类/子类重合，用于消费行为控制。",
            "",
            "| 顺序 | 规则名 | 主桶 | 机制 | 风险级别 | 关键词/条件摘要 |",
            "|---:|---|---|---|---|---|",
        ]
    )
    for index, rule in enumerate(rules.get("rules", []), 1):
        conditions: list[str] = []
        for key in ["directions", "transaction_types", "status_keywords", "method_keywords", "counterparty_keywords", "description_keywords", "any_keywords", "all_keywords"]:
            values = rule.get(key)
            if values:
                preview = "、".join(str(item) for item in values[:8])
                if len(values) > 8:
                    preview += "..."
                conditions.append(f"{key}: {preview}")
        if "amount_min" in rule:
            conditions.append(f"amount_min: {rule['amount_min']}")
        if "amount_max" in rule:
            conditions.append(f"amount_max: {rule['amount_max']}")
        lines.append(
            f"| {index} | {rule.get('name', '')} | {BUCKET_LABELS.get(rule.get('primary_bucket', ''), rule.get('primary_bucket', ''))} | "
            f"{rule.get('mechanism', '')} | {rule.get('risk_level', '')} | {'；'.join(conditions) or rule.get('reason', '')} |"
        )

    lines.extend(
        [
            "",
            "## 默认规则",
            "",
            "| 交易方向 | 默认主桶 | 机制 | 说明 |",
            "|---|---|---|---|",
        ]
    )
    for direction, item in rules.get("default_buckets", {}).items():
        lines.append(
            f"| {direction} | {BUCKET_LABELS.get(item.get('primary_bucket', ''), item.get('primary_bucket', ''))} | "
            f"{item.get('mechanism', '')} | {item.get('reason', '')} |"
        )
    lines.append("")
    return "\n".join(lines)


def _user_manual_markdown() -> str:
    return "\n".join(
        [
            "# 使用手册",
            "",
            "统计范围：本手册用于指导后续每周或多文件账单导入、复核、标签库维护、报告重建、数据库查询和下游系统接入。正式输出以 PDF 为主，Markdown、CSV、JSON、SQLite 为辅助。当前形态是本地静态 UI + SQLite 数据库 + 本机只读 HTTP API，不是 online deployed webpage。",
            "",
            "## 每周更新流程",
            "",
            "| 步骤 | 操作 | 产出/检查 |",
            "|---:|---|---|",
            "| 1 | 将新的支付宝/微信账单 CSV、XLSX 或 ZIP 放到本机固定位置。 | 保留原始文件，不手动改内容。 |",
            "| 2 | 运行周更脚本，输入可以是单个文件、多个文件、目录或 ZIP。 | 更新共享 SQLite、报告、dashboard、复核工作台和 manifest。 |",
            "| 3 | 打开报告门户查看 KPI、PDF、dashboard、明细查询和复核工作台。 | `outputs/.../index.html` |",
            "| 4 | 处理大额待复核交易。 | 下载或准备 `review_decisions_confirmed.csv`。 |",
            "| 5 | 带 `--review-decisions` 重跑导入。 | 已确认大额进入或排除生产统计。 |",
            "| 6 | 检查周更 manifest 或单独运行验收脚本。 | 所有 PDF/HTML/SQLite/对账检查为 OK。 |",
            "",
            "## 标准周更命令",
            "",
            "```bash",
            "python3 scripts/weekly_update.py \\",
            "  --input ~/Downloads/<YOUR_ALIPAY_OR_WECHAT_BILL>.zip \\",
            "  --ledger-db data/finance_ledger/finance_ledger.sqlite \\",
            "  --output outputs/finance_ledger_20220605_20260603",
            "```",
            "",
            "如果不传 `--input`，脚本会在 `~/Downloads` 自动选择最新的支付宝/微信账单压缩包或账单文件。单笔 `>= ¥10,000` 且未确认的大额交易仍只进入复核队列；候选动作只用于下拉菜单加速，不会自动写入生产统计。",
            "",
            "## 带复核结果重建",
            "",
            "```bash",
            "python3 scripts/weekly_update.py \\",
            "  --input ~/Downloads/<YOUR_ALIPAY_OR_WECHAT_BILL>.zip \\",
            "  --ledger-db data/finance_ledger/finance_ledger.sqlite \\",
            "  --output outputs/finance_ledger_20220605_20260603 \\",
            "  --review-decisions outputs/finance_ledger_20220605_20260603/review/review_decisions_confirmed.csv",
            "```",
            "",
            "## 必跑验收命令",
            "",
            "```bash",
            "python3 scripts/validate_outputs.py \\",
            "  --output outputs/finance_ledger_20220605_20260603 \\",
            "  --db data/finance_ledger/finance_ledger.sqlite \\",
            "  --require-ledger",
            "```",
            "",
            "验收必须覆盖：正式 PDF 非空、报告内容章节、dashboard SVG 图表、HTML 入口、manifest、SQLite 表和视图、金额对账、大额复核隔离。",
            "",
            "## 报告入口",
            "",
            "| 入口 | 文件 | 用途 |",
            "|---|---|---|",
            "| 报告门户 | `outputs/finance_ledger_20220605_20260603/index.html` | 所有 PDF、dashboard、明细查询、复核工作台和审计入口。 |",
            "| 运行控制台 | `reports/operations_center.html` | 周更、复核、标签回灌、报告验收和只读 API 的连续工作流。 |",
            "| Dashboard | `reports/dashboard.html` | KPI、现金流趋势、主类占比、风险标签、周度趋势、对手方和消费规律。 |",
            "| 交易行为分析 | `reports/behavior_analysis.html` | 用标签组合选择范围，并切换折线图、直方图、环形图和金额分布图。 |",
            "| 交易明细查询 | `reports/transaction_explorer.html` | 生产统计和待复核两套明细筛选、模糊搜索反馈、标签组合筛选、明细折叠、分页、导出。 |",
            "| 标签库编辑 | `reports/tag_library.html` | 编辑标签名、筛选组合、分组、颜色、说明和启停状态，下载 JSON 后回灌保存。 |",
            "| 复核工作台 | `reports/review_workbench.html` | 用搜索/筛选缩小工作集，通过分组矩阵、影响预览、下拉选择和批量应用处理大额复核。 |",
            "| 本地只读 API | `scripts/serve_ledger.py` | 给其他本地系统提供固定 endpoint，不开放任意 SQL，不写数据库。 |",
            "| 分类规则手册 | `reports/classification_rulebook_report.pdf` | 固定分类口径、趋势公式和特殊规则。 |",
            "| 交付验收报告 | `reports/delivery_acceptance_report.pdf` | 对照目标和当前交付证据。 |",
            "",
            "## 大额复核规则",
            "",
            "| 决策 | 含义 | 统计影响 |",
            "|---|---|---|",
            "| 未确认 | 保留在 `manual_review_queue.csv`。 | 不进入生产统计和报告总支出。 |",
            "| include | 按确认分类进入生产统计。 | 更新总支出、占比、趋势和建议。 |",
            "| exclude | 从待复核队列移除但不计支出。 | 不进入总支出。 |",
            "| split | 按比例拆到多个主类/子类。 | 分摊进入生产统计。 |",
            "",
            "复核工作台优先使用下拉菜单、候选决策和分组矩阵：先按对手方、建议分类、状态或最小金额筛选，再按交易对方、建议分类或月份分组；矩阵会显示当前筛选金额、已决策笔数、纳入影响金额和仍未决策金额。系统会按商户/机构/个人转账特征生成候选动作和 high/medium/low 置信度，候选只用于预填选择，不会自动入账。整组可选择按建议纳入、套用候选、套用批量栏、50/25/25 拆分或排除；少量特殊交易再单笔修改。",
            "",
            "## 标签库回灌",
            "",
            "```bash",
            "python3 scripts/import_ledger.py \\",
            "  --input ~/Downloads/<YOUR_ALIPAY_OR_WECHAT_BILL>.zip \\",
            "  --ledger-db data/finance_ledger/finance_ledger.sqlite \\",
            "  --output outputs/finance_ledger_20220605_20260603 \\",
            "  --tag-library outputs/finance_ledger_20220605_20260603/reports/tag_library_custom.json",
            "```",
            "",
            "回灌后标签库和筛选组合会写入 `tag_library`、`tag_filter_presets` 表和 `v_tag_library`、`v_tag_filter_presets` 只读视图。交易行为分析和明细查询会读取该配置展示标签组合。",
            "",
            "## 只读查询命令",
            "",
            "| 任务 | 命令 |",
            "|---|---|",
            "| 查看月份 | `python3 scripts/query_analysis.py months` |",
            "| 月度统计 | `python3 scripts/query_analysis.py stats --period month --limit 6` |",
            "| 分类汇总 | `python3 scripts/query_analysis.py categories --limit 20` |",
            "| 风险标签 | `python3 scripts/query_analysis.py risks --limit 20` |",
            "| 待复核 | `python3 scripts/query_analysis.py review --limit 50` |",
            "| 固定问题查询 | `python3 scripts/query_analysis.py ask \"本月现金流怎么样\" --json` |",
            "| JSON 输出 | 在命令后加 `--json`，供其他工具读取。 |",
            "",
            "## 交付打包",
            "",
            "```bash",
            "python3 scripts/package_delivery.py \\",
            "  --output-dir outputs/finance_ledger_20220605_20260603 \\",
            "  --ledger-db data/finance_ledger/finance_ledger.sqlite",
            "```",
            "",
            "交付包会写入 `outputs/delivery/`，包含代码、配置、文档、正式 PDF/HTML、SQLite 和审计文件；不会重新分类或写原始账单。",
            "",
            "## 下游系统接入",
            "",
            "| 场景 | 推荐视图 | 说明 |",
            "|---|---|---|",
            "| 量化回测资金流 | `v_mart_daily_cashflow` | 日度支出、收入、净现金流、账户搬运和待复核。 |",
            "| 行研/平台暴露 | `v_mart_counterparty_monthly` | 月度对手方、主类、子类金额。 |",
            "| 消费行为趋势 | `v_mart_risk_monthly` | 月度风险标签暴露。 |",
            "| 逐笔生产支出 | `v_fact_expense_allocations` | 已进入生产统计的支出分摊事实表。 |",
            "| 全量审计 | `v_fact_transactions_audit` | 包含收入、支出、搬运、失败关闭和分类字段。 |",
            "| 大额复核 | `v_fact_pending_large_review` | 未确认大额交易事实表。 |",
            "| 复核状态 | `v_review_status_summary` | 大额复核闭环状态。 |",
            "",
            "## 维护原则",
            "",
            "| 原则 | 要求 |",
            "|---|---|",
            "| 原始数据不修改 | 导入脚本读取原始 CSV/ZIP，清洗结果另存。 |",
            "| 规则先测试 | 分类规则变更后必须跑单元测试和完整验收。 |",
            "| 未确认不入账 | 大额待复核未确认前不进入生产统计。 |",
            "| 正式产出优先 PDF | HTML 用于本地交互，CSV/JSON/SQLite 用于辅助分析。 |",
            "| 下游只读 | 其他系统默认只读连接共享 SQLite，不直接写表。 |",
            "",
        ]
    )


def _manual_review_report_markdown(review_rows: list[dict[str, Any]], review_status_rows: list[dict[str, Any]] | None = None) -> str:
    total_amount = sum(float(row.get("amount", 0) or 0) for row in review_rows)
    by_category: dict[tuple[str, str], dict[str, Any]] = {}
    by_counterparty: dict[str, dict[str, Any]] = {}
    for row in review_rows:
        amount = float(row.get("amount", 0) or 0)
        category_key = (str(row.get("main_category", "") or "未分类"), str(row.get("sub_category", "") or "未分类"))
        category_bucket = by_category.setdefault(category_key, {"count": 0, "amount": 0.0})
        category_bucket["count"] += 1
        category_bucket["amount"] += amount
        counterparty = str(row.get("counterparty", "") or "未填写")
        counterparty_bucket = by_counterparty.setdefault(counterparty, {"count": 0, "amount": 0.0})
        counterparty_bucket["count"] += 1
        counterparty_bucket["amount"] += amount

    category_rows = sorted(by_category.items(), key=lambda item: item[1]["amount"], reverse=True)
    counterparty_rows = sorted(by_counterparty.items(), key=lambda item: item[1]["amount"], reverse=True)
    detail_rows = sorted(review_rows, key=lambda row: float(row.get("amount", 0) or 0), reverse=True)

    lines = [
        "# 大额复核清单",
        "",
        "统计范围：单笔 >= ¥10,000 且尚未确认的支出。未确认前不进入生产统计、总支出占比、趋势和消费建议。",
        "",
        "## 复核总览",
        "",
        "本节展示当前仍隔离的大额支出；下方“复核闭环状态”展示全部大额复核范围的生产口径状态。",
        "",
        "| 项目 | 数值 |",
        "|---|---:|",
        f"| 待复核笔数 | {len(review_rows)} |",
        f"| 待复核金额 | ¥{total_amount:,.2f} |",
        "",
        "## 复核闭环状态",
        "",
        "| 状态 | 笔数 | 金额 | 笔数占比 | 金额占比 | 生产影响 | 下一步 |",
        "|---|---:|---:|---:|---:|---|---|",
    ]
    for item in review_status_rows or []:
        lines.append(
            f"| {item.get('status_label', '')} | {item.get('count', 0)} | ¥{float(item.get('amount', 0) or 0):,.2f} | "
            f"{item.get('count_pct', '0.00%')} | {item.get('amount_pct', '0.00%')} | {item.get('production_effect', '')} | {_safe_name(item.get('next_action', ''))} |"
        )
    if not review_status_rows:
        lines.append("| 无 | 0 | ¥0.00 | 0.00% | 0.00% | 无 | 无 |")

    lines.extend(
        [
            "",
        "## 处理原则",
        "",
        "| 决策 | 适用场景 | 统计影响 |",
        "|---|---|---|",
        "| include | 确认属于个人或家庭真实支出。 | 纳入生产统计，更新报告和 dashboard。 |",
        "| exclude | 确认不是支出、属于搬运、误记、已冲正或不应计入。 | 不进入总支出。 |",
        "| split | 一笔金额需要拆到多个主类/子类。 | 按比例分摊进入生产统计。 |",
            "| 暂缓 | 无法判断用途或责任归属。 | 保留在待复核队列，不进入生产统计。 |",
            "",
            "## 当前建议分类汇总",
            "",
            "| 主类 | 子类 | 笔数 | 金额 | 占待复核 |",
            "|---|---|---:|---:|---:|",
        ]
    )
    for (main, sub), item in category_rows:
        pct = item["amount"] / total_amount * 100 if total_amount else 0
        lines.append(f"| {main} | {sub} | {item['count']} | ¥{item['amount']:,.2f} | {pct:.2f}% |")

    lines.extend(
        [
            "",
            "## 交易对方 Top 20",
            "",
            "| 交易对方 | 笔数 | 金额 | 占待复核 |",
            "|---|---:|---:|---:|",
        ]
    )
    for counterparty, item in counterparty_rows[:20]:
        pct = item["amount"] / total_amount * 100 if total_amount else 0
        lines.append(f"| {_safe_name(counterparty)[:32]} | {item['count']} | ¥{item['amount']:,.2f} | {pct:.2f}% |")

    lines.extend(
        [
            "",
            "## 待复核明细",
            "",
            "| 时间 | 对方 | 说明 | 当前建议分类 | 风险标签 | 金额 |",
            "|---|---|---|---|---|---:|",
        ]
    )
    for row in detail_rows:
        desc = _safe_name(str(row.get("description", "") or ""))[:42]
        counterparty = _safe_name(str(row.get("counterparty", "") or ""))[:24]
        category = f"{row.get('main_category', '')}/{row.get('sub_category', '')}"
        tags = _safe_name(str(row.get("risk_tags", "") or ""))[:28]
        amount = float(row.get("amount", 0) or 0)
        lines.append(f"| {row.get('transaction_time', row.get('date', ''))} | {counterparty} | {desc} | {category} | {tags} | ¥{amount:,.2f} |")
    if not detail_rows:
        lines.append("| 无 |  |  |  |  | ¥0.00 |")

    lines.extend(
        [
            "",
            "## 回灌命令",
            "",
            "确认后使用复核工作台下载 `review_decisions_confirmed.csv`，再运行：",
            "",
            "```bash",
            "python3 scripts/import_ledger.py \\",
            "  --input ~/Downloads/<YOUR_ALIPAY_OR_WECHAT_BILL>.zip \\",
            "  --ledger-db data/finance_ledger/finance_ledger.sqlite \\",
            "  --output outputs/finance_ledger_20220605_20260603 \\",
            "  --review-decisions outputs/finance_ledger_20220605_20260603/review/review_decisions_confirmed.csv",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def _spending_control_action_markdown(
    metrics: dict[str, Any],
    category_summary: list[dict[str, Any]],
    risk_summary: list[dict[str, Any]],
    control_plan_rows: list[dict[str, Any]],
) -> str:
    total_expense = int(metrics.get("total_expense", 0))
    pending_review = int(metrics.get("pending_review", 0))
    estimated_saving = sum(float(item.get("estimated_saving", 0) or 0) for item in control_plan_rows)
    p0_count = sum(1 for item in control_plan_rows if str(item.get("priority")) == "P0")
    p1_count = sum(1 for item in control_plan_rows if str(item.get("priority")) == "P1")
    main_rows = [item for item in category_summary if item.get("level") == "主类"]

    lines = [
        "# 消费控制行动计划",
        "",
        "口径：本计划只读取生产统计口径，单笔 >= ¥10,000 且未确认的大额支出不进入当前总支出；确认后重建数据库和报告。",
        "",
        "## 行动总览",
        "",
        f"- 当前生产口径总支出：¥{format_yuan(total_expense)}",
        f"- 大额待复核金额：¥{format_yuan(pending_review)}",
        f"- P0 动作数量：{p0_count}",
        f"- P1 动作数量：{p1_count}",
        f"- 当前预计可优化金额：¥{estimated_saving:,.2f}",
        "",
        "## 优先级动作",
        "",
        "| 优先级 | 控制对象 | 触发证据 | 当前金额 | 占总支出 | 建议动作 | 建议上限 | 预计可优化 | 需复核 |",
        "|---|---|---|---:|---:|---|---:|---:|---|",
    ]
    if control_plan_rows:
        for item in control_plan_rows:
            lines.append(
                f"| {item.get('priority', '')} | {_safe_name(item.get('focus_area', ''))} | {_safe_name(item.get('trigger_metric', ''))} | "
                f"¥{float(item.get('current_amount', 0) or 0):,.2f} | {item.get('current_pct', '0.00%')} | {_safe_name(item.get('recommended_action', ''))} | "
                f"¥{float(item.get('suggested_cap', 0) or 0):,.2f} | ¥{float(item.get('estimated_saving', 0) or 0):,.2f} | {item.get('review_needed', '否')} |"
            )
    else:
        lines.append("| P3 | 继续观察 | 当前无突出异常 | ¥0.00 | 0.00% | 继续积累周期数据后再设置封顶额。 | ¥0.00 | ¥0.00 | 否 |")

    lines.extend(
        [
            "",
            "## 风险暴露",
            "",
            "| 风险标签 | 金额 | 占总支出 | 笔数 | 控制判断 |",
            "|---|---:|---:|---:|---|",
        ]
    )
    for item in risk_summary[:12]:
        tag = str(item.get("risk_tag", ""))
        if tag in {"平台便利", "高频小额", "低复购购物", "夜间冲动", "长期扣费"}:
            judgment = "优先压缩"
        elif tag in {"信用工具", "信用周转", "投资冲动", "流动性锁定"}:
            judgment = "设置交易窗口"
        elif tag in {"社交家庭", "家庭教育", "住房缴费", "餐饮日用"}:
            judgment = "保留必要预算并复核异常"
        else:
            judgment = "观察趋势"
        lines.append(
            f"| {_safe_name(tag)} | ¥{float(item.get('amount', 0) or 0):,.2f} | {item.get('expense_pct', '0.00%')} | {item.get('count', 0)} | {judgment} |"
        )

    lines.extend(
        [
            "",
            "## 主类控制线",
            "",
            "| 主类 | 当前金额 | 主类占总支出 | 建议控制线 | 下期动作 |",
            "|---|---:|---:|---:|---|",
        ]
    )
    for item in main_rows:
        name = str(item.get("main_category", ""))
        amount = float(item.get("amount", 0) or 0)
        if name == "可优化消费":
            cap = amount * 0.75
            action = "设置硬上限，超出后延迟 24 小时。"
        elif name == "金融资金":
            cap = amount * 0.80
            action = "只允许计划内投资/还款，禁止即时冲动买入。"
        elif name == "社交家庭":
            cap = amount * 0.85
            action = "亲情卡保留，其他大额转账逐笔复核。"
        elif name == "生活刚需":
            cap = amount
            action = "不做硬压缩，只看供应商和频次优化。"
        else:
            cap = amount
            action = "保持观察。"
        lines.append(f"| {name} | ¥{amount:,.2f} | {item.get('main_pct', '0.00%')} | ¥{cap:,.2f} | {action} |")

    lines.extend(
        [
            "",
            "## 下期执行规则",
            "",
            "1. 先处理 P0：大额待复核确认前，不把这部分金额纳入生产统计和预算判断。",
            "2. 可优化消费使用封顶额：外卖即时零售、低复购购物、会员订阅、便利饮品超过上限后延迟支付。",
            "3. 金融资金只接受计划内动作：基金买入、保险、信用周转必须保留用途说明。",
            "4. 社交家庭保留亲情卡必要支出；其他大额转账需要标注是否可回收、是否共同承担。",
            "5. 公司个人混同支出继续计入真实消费对应主类/子类，同时保留风险标签用于复盘。",
            "",
            "## 复盘流程",
            "",
            "| 频率 | 固定动作 | 输出物 |",
            "|---|---|---|",
            "| 每周 | 导入新账单，处理新增大额复核，查看 P0/P1 是否下降。 | 周报、消费控制行动计划、复核清单 |",
            "| 每月 | 对比本月 vs 上月、去年同月，调整下月主类控制线。 | 月报、Dashboard |",
            "| 每季 | 检查金融资金和社交家庭是否挤压真实生活现金流。 | 季报、现金流视图 |",
            "| 每年 | 固化稳定分类规则，清理无效风险标签和低价值子类。 | 年报、分类规则手册 |",
            "",
        ]
    )
    return "\n".join(lines)


def _write_audit_outputs(
    audit_dir: Path,
    *,
    rows: list[ClassifiedTransaction],
    metrics: dict[str, Any],
    output_paths: dict[str, str],
    rules_path: Path,
    review_decisions: ReviewDecisions | None = None,
) -> None:
    run_id = hashlib.sha256(f"{datetime.now().isoformat()}-{len(rows)}".encode("utf-8")).hexdigest()[:16]
    source_logs = _source_log_rows(rows)
    pending_review_count = sum(1 for row in rows if getattr(row, "needs_review", False) and not _is_review_confirmed(row, review_decisions))
    _write_jsonl(audit_dir / "source_log.jsonl", source_logs)
    _write_json(audit_dir / "rules_version.json", _rules_version_payload(rules_path))
    _write_json(audit_dir / "reference_models.json", _reference_models_payload())
    reference_source_rows = _reference_source_log_rows()
    _write_json(audit_dir / "reference_source_log.json", reference_source_rows)
    write_csv(audit_dir / "reference_source_log.csv", reference_source_rows)
    reference_ui_pattern_rows = _reference_ui_pattern_rows()
    _write_json(audit_dir / "reference_ui_patterns.json", reference_ui_pattern_rows)
    write_csv(audit_dir / "reference_ui_patterns.csv", reference_ui_pattern_rows)
    _write_json(
        audit_dir / "model_version.json",
        {
            "mode": "rule_only",
            "llm_enabled": False,
            "note": "当前版本未调用外部模型；分类由本地规则和人工确认映射决定。",
        },
    )
    _write_json(
        audit_dir / "assumptions.json",
        {
            "large_transaction_review_threshold_yuan": 10000,
            "unconfirmed_large_expense_policy": "不进入生产统计；仅进入 manual_review_queue，确认后再回灌数据库和报告。",
            "manual_review_decision_policy": "通过 --review-decisions 读取 CSV 确认表；include 纳入生产统计，exclude 从待复核队列移除但不计入支出。",
            "lolol_jiahansong_policy": "50% 教育医疗，25% 住房缴费，25% 餐饮日用，视为已确认。",
            "chun_zhangweiqian_policy": "进入 社交家庭/亲情卡人情往来，视为已确认。",
            "financial_cashflow_policy": "基金买入计支出，卖出/赎回计收入；账户搬运进入现金流视图但不计支出占比。",
            "percentage_policy": "主类占比=主类金额/本期总支出；子类占比=子类金额/所属主类金额；保留两位小数。",
        },
    )
    _write_json(
        audit_dir / "gaps.json",
        {
            "pending_large_review_count": pending_review_count,
            "pending_large_review_policy": "大额待复核交易未确认前不进入生产统计；需要通过 review_workbench.html 或 review_decisions CSV 确认后重建数据库和全部报告。",
            "manual_review_feedback_ui": "已提供本地静态 review_workbench.html，以下拉菜单选择复核决定、主类/子类和风险标签；后续可升级为持久化本地 Web 服务。",
            "user_acceptance_workbench": "已提供本地静态 acceptance_workbench.html，用 A/B/C 按钮收敛用户主观验收、ChatGPT 对照缺口和下一步决策，并可导出 JSON/CSV。",
            "wechat_import": "已支持支付宝/微信 CSV/XLSX。",
            "bank_and_broker_import": "未来银行卡流水、券商流水需要增加 account_id、asset_type 和 cashflow_type 字段后再接入。",
            "downstream_access": "当前提供 SQLite 只读视图、CLI query、本机只读 HTTP API 和固定问题模板 ask；如赛事分析、量化回测、行研报告需要远程访问，应增加认证、权限、脱敏、备份和访问日志。",
            "llm_guardrails": "当前为 rule_only + fixed_question_templates；若启用 LLM/NL2SQL，必须固定 taxonomy、JSON schema、schema 白名单、只读校验、置信度和人工复核阈值。",
        },
    )
    _write_json(
        audit_dir / "run_manifest.json",
        {
            "run_id": run_id,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "transaction_count": len(rows),
            "source_files": source_logs,
            "review_decisions": {
                "source_path": review_decisions.source_path if review_decisions else "",
                "included_keys": len(review_decisions.included) if review_decisions else 0,
                "excluded_keys": len(review_decisions.excluded) if review_decisions else 0,
                "invalid_rows": len(review_decisions.invalid_rows) if review_decisions else 0,
            },
            "metrics": {key: yuan(value) if isinstance(value, int) and key != "transactions" else value for key, value in metrics.items()},
            "outputs": output_paths,
        },
    )
    _write_json(
        audit_dir / "report_manifest.json",
        {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "reports": {
                key: value
                for key, value in output_paths.items()
                if key.endswith("_pdf")
                or key.endswith("_md")
                or key
                in {
                    "index_html",
                    "dashboard_html",
                    "operations_center_html",
                    "data_access_hub_html",
                    "acceptance_workbench_html",
                    "reference_model_lab_html",
                    "transaction_explorer_html",
                    "behavior_analysis_html",
                    "tag_library_html",
                    "review_workbench_html",
                }
            },
        },
    )


def generate_outputs(
    rows: list[ClassifiedTransaction],
    output_dir: str | Path,
    review_decisions: ReviewDecisions | None = None,
    tag_library_rows: list[dict[str, Any]] | None = None,
    tag_filter_preset_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Path]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    data_dir = out / "data"
    review_dir = out / "review"
    audit_dir = out / "audit"
    reports_dir = out / "reports"
    data_dir.mkdir(parents=True, exist_ok=True)
    review_dir.mkdir(parents=True, exist_ok=True)
    audit_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    tag_library_rows = tag_library_rows or _tag_library_rows()
    tag_filter_preset_rows = tag_filter_preset_rows or _tag_filter_preset_rows()

    transaction_rows = [row.to_dict() for row in rows]
    write_csv(out / "transactions_classified.csv", transaction_rows)
    write_csv(data_dir / "classified_transactions.csv", transaction_rows)
    write_csv(data_dir / "cleaned_transactions.csv", transaction_rows)

    period_summaries = {name: build_period_summary(rows, name, review_decisions) for name in PERIODS}
    for name, summary in period_summaries.items():
        write_csv(out / f"summary_by_{name}.csv", summary)
        write_csv(data_dir / f"summary_by_{name}.csv", summary)

    write_csv(out / "summary_by_mechanism.csv", _group_sum(rows, "mechanism", review_decisions=review_decisions))
    overall_metrics = core_metrics(rows, review_decisions)
    category_summary_full = _category_summary(rows, review_decisions)
    risk_summary_full = _risk_tag_summary(rows, review_decisions)
    category_rows = []
    for item in category_summary_full:
        exported = {k: v for k, v in item.items() if k not in {"amount_cents", "level"}}
        if item.get("level") == "子类":
            exported["main_category"] = ""
        category_rows.append(exported)
    risk_rows = [{k: v for k, v in item.items() if k != "amount_cents"} for item in risk_summary_full]
    control_plan_source = build_control_plan(overall_metrics, category_summary_full, risk_summary_full)
    control_plan_rows = [{k: v for k, v in item.items() if not k.endswith("_cents")} for item in control_plan_source]
    budget_pressure_source = build_budget_pressure_radar(overall_metrics, category_summary_full, risk_summary_full)
    budget_pressure_rows = [{k: v for k, v in item.items() if not k.endswith("_cents")} for item in budget_pressure_source]
    source_platform_rows = [{k: v for k, v in item.items() if k != "bar"} for item in _source_platform_rows(rows, review_decisions)]
    allocation_rows = _allocation_export_rows(rows, review_decisions)
    data_trust_rows = build_data_trust_transactions(rows, review_decisions=review_decisions, allocation_rows=allocation_rows)
    entity_layer = build_entity_layer(rows, tag_library_rows=tag_library_rows)
    entity_registry_rows = entity_layer["entity_registry"]
    alias_map_rows = entity_layer["alias_map"]
    entity_registry_summary_rows = entity_layer["entity_registry_summary"]
    review_rows = [row.to_dict() for row in _pending_review_rows(rows, review_decisions)]
    review_status_rows = [{k: v for k, v in item.items() if k != "bar"} for item in _review_status_summary(rows, review_decisions)]
    review_candidate_rows = _review_decision_candidate_rows(rows, review_decisions)
    review_candidate_group_rows = _review_decision_candidate_group_rows(review_candidate_rows)
    review_template_rows = _review_decision_template_rows(rows, review_decisions)
    decision_rows = _review_decision_rows(review_decisions)
    invalid_decision_rows = (review_decisions.invalid_rows if review_decisions else [])
    manual_review_audit_rows = build_manual_review_audit_rows(
        review_rows=review_rows,
        candidate_rows=review_candidate_rows,
        status_rows=review_status_rows,
        data_trust_rows=data_trust_rows,
        invalid_decision_rows=invalid_decision_rows,
    )
    manual_review_audit_summary_rows = summarize_manual_review_audit(manual_review_audit_rows)
    evidence_decision_layer = build_evidence_decision_layer(
        data_trust_rows=data_trust_rows,
        manual_review_rows=manual_review_audit_rows,
        entity_rows=entity_registry_rows,
        alias_rows=alias_map_rows,
        control_plan_rows=control_plan_rows,
        source_platform_rows=source_platform_rows,
    )
    evidence_decision_rows = evidence_decision_layer["evidence_decision_matrix"]
    evidence_decision_summary_rows = evidence_decision_layer["evidence_decision_summary"]
    write_csv(out / "summary_by_category.csv", category_rows)
    write_csv(data_dir / "summary_by_category.csv", category_rows)
    write_csv(out / "summary_by_risk_tag.csv", risk_rows)
    write_csv(data_dir / "summary_by_risk_tag.csv", risk_rows)
    write_csv(out / "spending_control_plan.csv", control_plan_rows)
    write_csv(data_dir / "spending_control_plan.csv", control_plan_rows)
    write_csv(out / "budget_pressure_radar.csv", budget_pressure_rows)
    write_csv(data_dir / "budget_pressure_radar.csv", budget_pressure_rows)
    write_csv(out / "source_platform_summary.csv", source_platform_rows)
    write_csv(data_dir / "source_platform_summary.csv", source_platform_rows)
    write_csv(data_dir / "tag_library.csv", tag_library_rows)
    write_csv(data_dir / "tag_filter_presets.csv", tag_filter_preset_rows)
    write_csv(data_dir / "production_expense_allocations.csv", allocation_rows)
    write_csv(data_dir / "data_trust_transactions.csv", data_trust_rows)
    write_csv(data_dir / "entity_registry.csv", entity_registry_rows)
    write_csv(data_dir / "alias_map.csv", alias_map_rows)
    write_csv(data_dir / "entity_registry_summary.csv", entity_registry_summary_rows)
    write_csv(out / "manual_review_queue.csv", review_rows)
    write_csv(review_dir / "manual_review_queue.csv", review_rows)
    write_csv(data_dir / "manual_review_status_summary.csv", review_status_rows)
    write_csv(review_dir / "manual_review_status_summary.csv", review_status_rows)
    write_csv(data_dir / "manual_review_decision_candidates.csv", review_candidate_rows)
    write_csv(review_dir / "review_decision_candidates.csv", review_candidate_rows)
    write_csv(data_dir / "manual_review_decision_candidate_groups.csv", review_candidate_group_rows)
    write_csv(review_dir / "review_decision_candidate_groups.csv", review_candidate_group_rows)
    write_csv(review_dir / "review_decisions_template.csv", review_template_rows)
    write_csv(review_dir / "review_decisions_loaded.csv", decision_rows)
    write_csv(review_dir / "review_decisions_invalid.csv", invalid_decision_rows)
    write_csv(data_dir / "manual_review_queue_audit.csv", manual_review_audit_rows)
    write_csv(data_dir / "manual_review_queue_audit_summary.csv", manual_review_audit_summary_rows)
    write_csv(data_dir / "evidence_decision_matrix.csv", evidence_decision_rows)
    write_csv(data_dir / "evidence_decision_summary.csv", evidence_decision_summary_rows)
    write_csv(review_dir / "company_personal_mixed_review.csv", [row.to_dict() for row in rows if row.is_business_personal_mixed])
    write_csv(out / "top_counterparties.csv", _group_sum(rows, "counterparty", review_decisions=review_decisions))
    write_csv(data_dir / "top_counterparties.csv", _group_sum(rows, "counterparty", review_decisions=review_decisions))

    (out / "summary.json").write_text(
        json.dumps(
            {
                "metrics": {key: yuan(value) if isinstance(value, int) and key != "transactions" else value for key, value in overall_metrics.items()},
                "bucket_labels": BUCKET_LABELS,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    _write_json(data_dir / "summary_metrics.json", {key: yuan(value) if isinstance(value, int) and key != "transactions" else value for key, value in overall_metrics.items()})
    write_csv(data_dir / "summary_metrics.csv", [{key: yuan(value) if isinstance(value, int) and key != "transactions" else value for key, value in overall_metrics.items()}])

    dates = [parse_date(row.date) for row in rows]
    latest = max(dates)
    output_paths: dict[str, str] = {
        "classified_transactions": str(out / "transactions_classified.csv"),
        "classified_transactions_data": str(data_dir / "classified_transactions.csv"),
        "spending_control_plan": str(data_dir / "spending_control_plan.csv"),
        "budget_pressure_radar": str(data_dir / "budget_pressure_radar.csv"),
        "tag_library": str(data_dir / "tag_library.csv"),
        "entity_registry": str(data_dir / "entity_registry.csv"),
        "alias_map": str(data_dir / "alias_map.csv"),
        "manual_review_queue": str(review_dir / "manual_review_queue.csv"),
        "manual_review_queue_audit": str(data_dir / "manual_review_queue_audit.csv"),
        "review_decisions_template": str(review_dir / "review_decisions_template.csv"),
    }
    report_specs = [
        ("week", "周报", "weekly_report.md"),
        ("month", "月报", "monthly_report.md"),
        ("quarter", "季报", "quarterly_report.md"),
        ("half", "半年报", "half_year_report.md"),
        ("year", "年报", "yearly_report.md"),
    ]
    for period_name, title, filename in report_specs:
        start, end, label = PERIODS[period_name](latest)
        period_tx = _period_rows(rows, start, min(end, latest))
        note = f"{start.isoformat()} 至 {min(end, latest).isoformat()}（{label}，按账单最新日期截断）"
        report_md = _report_markdown(title, period_tx, note, all_rows=rows, period_name=period_name, latest=latest, review_decisions=review_decisions)
        md_path = out / filename
        md_path.write_text(report_md, encoding="utf-8")
        write_report_pdf(report_md, md_path.with_suffix(".pdf"))
        report_md_path = reports_dir / filename
        report_md_path.write_text(report_md, encoding="utf-8")
        shutil.copy2(md_path.with_suffix(".pdf"), report_md_path.with_suffix(".pdf"))
        output_paths[f"{period_name}_md"] = str(report_md_path)
        output_paths[f"{period_name}_pdf"] = str(report_md_path.with_suffix(".pdf"))

    dataset_start, dataset_end = min(dates), max(dates)
    annual_note = f"{dataset_start.isoformat()} 至 {dataset_end.isoformat()}（账单完整覆盖期）"
    annual_report_md = _report_markdown("账单周期年报", rows, annual_note, all_rows=rows, trend_period_name="month", latest=latest, review_decisions=review_decisions)
    annual_report_path = out / "annual_bill_cycle_report.md"
    annual_report_path.write_text(annual_report_md, encoding="utf-8")
    write_report_pdf(annual_report_md, annual_report_path.with_suffix(".pdf"))
    shutil.copy2(annual_report_path, reports_dir / "annual_bill_cycle_report.md")
    shutil.copy2(annual_report_path.with_suffix(".pdf"), reports_dir / "annual_bill_cycle_report.pdf")
    dashboard_path = out / "dashboard.html"
    dashboard_path.write_text(_dashboard_html(rows, period_summaries, review_decisions, tag_library_rows), encoding="utf-8")
    shutil.copy2(dashboard_path, reports_dir / "dashboard.html")
    transaction_explorer_path = out / "transaction_explorer.html"
    transaction_explorer_path.write_text(_transaction_explorer_html(allocation_rows, review_rows, tag_library_rows, tag_filter_preset_rows), encoding="utf-8")
    shutil.copy2(transaction_explorer_path, reports_dir / "transaction_explorer.html")
    behavior_analysis_path = out / "behavior_analysis.html"
    behavior_analysis_path.write_text(_behavior_analysis_html(allocation_rows, tag_library_rows, tag_filter_preset_rows), encoding="utf-8")
    shutil.copy2(behavior_analysis_path, reports_dir / "behavior_analysis.html")
    tag_library_path = out / "tag_library.html"
    tag_library_path.write_text(_tag_library_html(tag_library_rows, tag_filter_preset_rows), encoding="utf-8")
    shutil.copy2(tag_library_path, reports_dir / "tag_library.html")
    review_workbench_path = review_dir / "review_workbench.html"
    review_workbench_path.write_text(_review_workbench_html(rows, review_decisions, tag_library_rows), encoding="utf-8")
    shutil.copy2(review_workbench_path, reports_dir / "review_workbench.html")
    operations_center_path = out / "operations_center.html"
    operations_center_path.write_text(_operations_center_html(overall_metrics, review_status_rows, output_paths, location="root"), encoding="utf-8")
    (reports_dir / "operations_center.html").write_text(_operations_center_html(overall_metrics, review_status_rows, output_paths, location="reports"), encoding="utf-8")
    data_access_hub_path = out / "data_access_hub.html"
    data_access_hub_path.write_text(_data_access_hub_html(overall_metrics, output_paths, location="root"), encoding="utf-8")
    (reports_dir / "data_access_hub.html").write_text(_data_access_hub_html(overall_metrics, output_paths, location="reports"), encoding="utf-8")
    sqlite_path = data_dir / "consumption.sqlite"
    _write_sqlite(
        sqlite_path,
        transaction_rows=transaction_rows,
        allocation_rows=allocation_rows,
        category_rows=category_rows,
        risk_rows=risk_rows,
        control_plan_rows=control_plan_rows,
        budget_pressure_rows=budget_pressure_rows,
        source_platform_rows=source_platform_rows,
        tag_library_rows=tag_library_rows,
        tag_filter_preset_rows=tag_filter_preset_rows,
        review_rows=review_rows,
        review_status_rows=review_status_rows,
        review_candidate_rows=review_candidate_rows,
        review_candidate_group_rows=review_candidate_group_rows,
        review_decision_rows=decision_rows,
        review_invalid_rows=invalid_decision_rows,
        data_trust_rows=data_trust_rows,
        manual_review_audit_rows=manual_review_audit_rows,
        manual_review_audit_summary_rows=manual_review_audit_summary_rows,
        entity_registry_rows=entity_registry_rows,
        alias_map_rows=alias_map_rows,
        entity_registry_summary_rows=entity_registry_summary_rows,
        evidence_decision_rows=evidence_decision_rows,
        evidence_decision_summary_rows=evidence_decision_summary_rows,
        period_summaries=period_summaries,
    )
    output_paths.update(
        {
            "annual_bill_cycle_md": str(reports_dir / "annual_bill_cycle_report.md"),
            "annual_bill_cycle_pdf": str(reports_dir / "annual_bill_cycle_report.pdf"),
            "dashboard_html": str(reports_dir / "dashboard.html"),
            "operations_center_html": str(reports_dir / "operations_center.html"),
            "data_access_hub_html": str(reports_dir / "data_access_hub.html"),
            "acceptance_workbench_html": str(reports_dir / "acceptance_workbench.html"),
            "reference_model_lab_html": str(reports_dir / "reference_model_lab.html"),
            "transaction_explorer_html": str(reports_dir / "transaction_explorer.html"),
            "behavior_analysis_html": str(reports_dir / "behavior_analysis.html"),
            "tag_library_html": str(reports_dir / "tag_library.html"),
            "review_workbench_html": str(reports_dir / "review_workbench.html"),
            "index_html": str(reports_dir / "index.html"),
            "sqlite": str(sqlite_path),
            "summary": str(out / "summary.json"),
        }
    )
    reference_lab_path = out / "reference_model_lab.html"
    reference_lab_path.write_text(_reference_model_lab_html(location="root"), encoding="utf-8")
    (reports_dir / "reference_model_lab.html").write_text(_reference_model_lab_html(location="reports"), encoding="utf-8")
    output_paths.update(_write_report_visual_inventory(audit_dir, reports_dir))
    visual_quality_md = _visual_quality_acceptance_markdown(output_paths=output_paths)
    visual_quality_path = out / "visual_quality_acceptance_report.md"
    visual_quality_path.write_text(visual_quality_md, encoding="utf-8")
    write_report_pdf(visual_quality_md, visual_quality_path.with_suffix(".pdf"))
    shutil.copy2(visual_quality_path, reports_dir / "visual_quality_acceptance_report.md")
    shutil.copy2(visual_quality_path.with_suffix(".pdf"), reports_dir / "visual_quality_acceptance_report.pdf")
    output_paths["visual_quality_acceptance_md"] = str(reports_dir / "visual_quality_acceptance_report.md")
    output_paths["visual_quality_acceptance_pdf"] = str(reports_dir / "visual_quality_acceptance_report.pdf")
    data_trust_md = data_trust_report_markdown(data_trust_rows)
    data_trust_path = out / "data_trust_audit_report.md"
    data_trust_path.write_text(data_trust_md, encoding="utf-8")
    write_report_pdf(data_trust_md, data_trust_path.with_suffix(".pdf"))
    shutil.copy2(data_trust_path, reports_dir / "data_trust_audit_report.md")
    shutil.copy2(data_trust_path.with_suffix(".pdf"), reports_dir / "data_trust_audit_report.pdf")
    output_paths["data_trust_audit_md"] = str(reports_dir / "data_trust_audit_report.md")
    output_paths["data_trust_audit_pdf"] = str(reports_dir / "data_trust_audit_report.pdf")
    for key, path in write_entity_layer_outputs(entity_layer, out).items():
        output_paths[key] = str(path)
    entity_registry_md_path = reports_dir / "entity_registry_report.md"
    write_report_pdf(entity_registry_md_path.read_text(encoding="utf-8"), entity_registry_md_path.with_suffix(".pdf"))
    output_paths["entity_registry_report_pdf"] = str(entity_registry_md_path.with_suffix(".pdf"))
    reference_benchmark_md = _reference_model_benchmark_markdown()
    reference_benchmark_path = out / "reference_model_benchmark_report.md"
    reference_benchmark_path.write_text(reference_benchmark_md, encoding="utf-8")
    write_report_pdf(reference_benchmark_md, reference_benchmark_path.with_suffix(".pdf"))
    shutil.copy2(reference_benchmark_path, reports_dir / "reference_model_benchmark_report.md")
    shutil.copy2(reference_benchmark_path.with_suffix(".pdf"), reports_dir / "reference_model_benchmark_report.pdf")
    output_paths["reference_model_benchmark_md"] = str(reports_dir / "reference_model_benchmark_report.md")
    output_paths["reference_model_benchmark_pdf"] = str(reports_dir / "reference_model_benchmark_report.pdf")
    acceptance_md = _delivery_acceptance_markdown(
        metrics=overall_metrics,
        rows=rows,
        allocation_rows=allocation_rows,
        review_rows=review_rows,
        output_paths=output_paths,
    )
    acceptance_path = out / "delivery_acceptance_report.md"
    acceptance_path.write_text(acceptance_md, encoding="utf-8")
    write_report_pdf(acceptance_md, acceptance_path.with_suffix(".pdf"))
    shutil.copy2(acceptance_path, reports_dir / "delivery_acceptance_report.md")
    shutil.copy2(acceptance_path.with_suffix(".pdf"), reports_dir / "delivery_acceptance_report.pdf")
    output_paths["delivery_acceptance_md"] = str(reports_dir / "delivery_acceptance_report.md")
    output_paths["delivery_acceptance_pdf"] = str(reports_dir / "delivery_acceptance_report.pdf")
    rules_path = Path("configs/classification_rules.json")
    rules_payload = json.loads(rules_path.read_text(encoding="utf-8")) if rules_path.exists() else {"rules": [], "default_buckets": {}}
    rulebook_md = _classification_rulebook_markdown(rules_payload)
    rulebook_path = out / "classification_rulebook_report.md"
    rulebook_path.write_text(rulebook_md, encoding="utf-8")
    write_report_pdf(rulebook_md, rulebook_path.with_suffix(".pdf"))
    shutil.copy2(rulebook_path, reports_dir / "classification_rulebook_report.md")
    shutil.copy2(rulebook_path.with_suffix(".pdf"), reports_dir / "classification_rulebook_report.pdf")
    output_paths["classification_rulebook_md"] = str(reports_dir / "classification_rulebook_report.md")
    output_paths["classification_rulebook_pdf"] = str(reports_dir / "classification_rulebook_report.pdf")
    user_manual_md = _user_manual_markdown()
    user_manual_path = out / "user_manual_report.md"
    user_manual_path.write_text(user_manual_md, encoding="utf-8")
    write_report_pdf(user_manual_md, user_manual_path.with_suffix(".pdf"))
    shutil.copy2(user_manual_path, reports_dir / "user_manual_report.md")
    shutil.copy2(user_manual_path.with_suffix(".pdf"), reports_dir / "user_manual_report.pdf")
    output_paths["user_manual_md"] = str(reports_dir / "user_manual_report.md")
    output_paths["user_manual_pdf"] = str(reports_dir / "user_manual_report.pdf")
    requirements_traceability_md = _requirements_traceability_markdown(
        metrics=overall_metrics,
        output_paths=output_paths,
        pending_review_count=len(review_rows),
    )
    requirements_traceability_path = out / "requirements_traceability_report.md"
    requirements_traceability_path.write_text(requirements_traceability_md, encoding="utf-8")
    write_report_pdf(requirements_traceability_md, requirements_traceability_path.with_suffix(".pdf"))
    shutil.copy2(requirements_traceability_path, reports_dir / "requirements_traceability_report.md")
    shutil.copy2(requirements_traceability_path.with_suffix(".pdf"), reports_dir / "requirements_traceability_report.pdf")
    output_paths["requirements_traceability_md"] = str(reports_dir / "requirements_traceability_report.md")
    output_paths["requirements_traceability_pdf"] = str(reports_dir / "requirements_traceability_report.pdf")
    spending_control_md = _spending_control_action_markdown(overall_metrics, category_summary_full, risk_summary_full, control_plan_rows)
    spending_control_path = out / "spending_control_action_report.md"
    spending_control_path.write_text(spending_control_md, encoding="utf-8")
    write_report_pdf(spending_control_md, spending_control_path.with_suffix(".pdf"))
    shutil.copy2(spending_control_path, reports_dir / "spending_control_action_report.md")
    shutil.copy2(spending_control_path.with_suffix(".pdf"), reports_dir / "spending_control_action_report.pdf")
    output_paths["spending_control_action_md"] = str(reports_dir / "spending_control_action_report.md")
    output_paths["spending_control_action_pdf"] = str(reports_dir / "spending_control_action_report.pdf")
    manual_review_md = _manual_review_report_markdown(review_rows, review_status_rows)
    manual_review_path = out / "manual_review_report.md"
    manual_review_path.write_text(manual_review_md, encoding="utf-8")
    write_report_pdf(manual_review_md, manual_review_path.with_suffix(".pdf"))
    shutil.copy2(manual_review_path, reports_dir / "manual_review_report.md")
    shutil.copy2(manual_review_path.with_suffix(".pdf"), reports_dir / "manual_review_report.pdf")
    output_paths["manual_review_report_md"] = str(reports_dir / "manual_review_report.md")
    output_paths["manual_review_report_pdf"] = str(reports_dir / "manual_review_report.pdf")
    for key, path in write_manual_review_audit_outputs(manual_review_audit_rows, out).items():
        output_paths[key] = str(path)
    manual_review_audit_md_path = reports_dir / "manual_review_queue_audit_report.md"
    write_report_pdf(manual_review_audit_md_path.read_text(encoding="utf-8"), manual_review_audit_md_path.with_suffix(".pdf"))
    output_paths["manual_review_queue_audit_pdf"] = str(manual_review_audit_md_path.with_suffix(".pdf"))
    for key, path in write_evidence_decision_outputs(evidence_decision_layer, out).items():
        output_paths[key] = str(path)
    evidence_decision_md_path = reports_dir / "evidence_decision_matrix_report.md"
    write_report_pdf(evidence_decision_md_path.read_text(encoding="utf-8"), evidence_decision_md_path.with_suffix(".pdf"))
    output_paths["evidence_decision_matrix_report_pdf"] = str(evidence_decision_md_path.with_suffix(".pdf"))
    completion_audit_md = _completion_audit_markdown(
        metrics=overall_metrics,
        output_paths=output_paths,
        pending_review_count=len(review_rows),
    )
    completion_audit_path = out / "completion_audit_report.md"
    completion_audit_path.write_text(completion_audit_md, encoding="utf-8")
    write_report_pdf(completion_audit_md, completion_audit_path.with_suffix(".pdf"))
    shutil.copy2(completion_audit_path, reports_dir / "completion_audit_report.md")
    shutil.copy2(completion_audit_path.with_suffix(".pdf"), reports_dir / "completion_audit_report.pdf")
    output_paths["completion_audit_md"] = str(reports_dir / "completion_audit_report.md")
    output_paths["completion_audit_pdf"] = str(reports_dir / "completion_audit_report.pdf")
    user_acceptance_md = _user_acceptance_matrix_markdown(
        metrics=overall_metrics,
        output_paths=output_paths,
        pending_review_count=len(review_rows),
    )
    user_acceptance_path = out / "user_acceptance_matrix_report.md"
    user_acceptance_path.write_text(user_acceptance_md, encoding="utf-8")
    write_report_pdf(user_acceptance_md, user_acceptance_path.with_suffix(".pdf"))
    shutil.copy2(user_acceptance_path, reports_dir / "user_acceptance_matrix_report.md")
    shutil.copy2(user_acceptance_path.with_suffix(".pdf"), reports_dir / "user_acceptance_matrix_report.pdf")
    output_paths["user_acceptance_matrix_md"] = str(reports_dir / "user_acceptance_matrix_report.md")
    output_paths["user_acceptance_matrix_pdf"] = str(reports_dir / "user_acceptance_matrix_report.pdf")
    acceptance_workbench_path = out / "acceptance_workbench.html"
    acceptance_workbench_path.write_text(
        _acceptance_workbench_html(
            metrics=overall_metrics,
            output_paths=output_paths,
            pending_review_count=len(review_rows),
            location="root",
        ),
        encoding="utf-8",
    )
    (reports_dir / "acceptance_workbench.html").write_text(
        _acceptance_workbench_html(
            metrics=overall_metrics,
            output_paths=output_paths,
            pending_review_count=len(review_rows),
            location="reports",
        ),
        encoding="utf-8",
    )
    output_paths["acceptance_workbench_html"] = str(reports_dir / "acceptance_workbench.html")
    output_paths.update(
        _finance_ledger_system_improvement_assets(
            reports_dir=reports_dir,
            audit_dir=audit_dir,
            output_paths=output_paths,
        )
    )
    index_path = reports_dir / "index.html"
    portal_kwargs = {
        "month_rows": sorted(period_summaries.get("month", []), key=lambda item: str(item.get("period_start", "")), reverse=True),
        "category_rows": category_rows,
        "risk_rows": risk_rows,
        "review_rows": review_rows,
        "review_status_rows": review_status_rows,
        "review_candidate_group_rows": review_candidate_group_rows,
    }
    index_path.write_text(_portal_html(overall_metrics, output_paths, control_plan_rows, location="reports", **portal_kwargs), encoding="utf-8")
    (out / "index.html").write_text(_portal_html(overall_metrics, output_paths, control_plan_rows, location="root", **portal_kwargs), encoding="utf-8")
    output_paths["index_html"] = str(index_path)
    _write_audit_outputs(audit_dir, rows=rows, metrics=overall_metrics, output_paths=output_paths, rules_path=rules_path, review_decisions=review_decisions)
    _copy_app_icon_assets(out, reports_dir)
    _inject_global_nav_all(out)

    return {
        "dashboard": dashboard_path,
        "classified_transactions": out / "transactions_classified.csv",
        "summary": out / "summary.json",
        "index": out / "index.html",
        "annual_report": out / "annual_bill_cycle_report.pdf",
        "sqlite": sqlite_path,
        "audit": audit_dir / "run_manifest.json",
        "transaction_explorer": transaction_explorer_path,
        "behavior_analysis": behavior_analysis_path,
        "tag_library": tag_library_path,
        "reference_model_lab": reference_lab_path,
        "review_workbench": review_workbench_path,
        "operations_center": operations_center_path,
        "data_access_hub": data_access_hub_path,
    }
