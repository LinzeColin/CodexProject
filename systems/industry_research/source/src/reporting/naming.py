from __future__ import annotations

from datetime import datetime


def compact_date(as_of: str) -> str:
    return datetime.strptime(as_of, "%Y-%m-%d").strftime("%d%m%Y")


def daily_report_name(session: str, as_of: str) -> str:
    prefix = {
        "pre_open": "1.",
        "midday": "2.",
        "post_close": "3.",
    }[session]
    label = {
        "pre_open": "盘前报告",
        "midday": "盘中报告",
        "post_close": "盘后报告",
    }[session]
    return f"{prefix} {compact_date(as_of)}_{label}"


def weekly_report_name(session: str, as_of: str) -> str:
    label = {
        "monday_pre_open": "周一报告",
        "friday_post_close": "周五报告",
    }[session]
    return f"{compact_date(as_of)}_{label}"


def kline_report_name(as_of: str) -> str:
    return f"4. {compact_date(as_of)}_K线分析报告"


def legacy_daily_report_name(session: str, as_of: str) -> str:
    prefix = {
        "pre_open": "1. 盘前报告",
        "midday": "2. 盘中报告",
        "post_close": "3. 盘后报告",
    }[session]
    return f"{prefix}_{compact_date(as_of)}"


def legacy_weekly_report_name(session: str, as_of: str) -> str:
    prefix = {
        "monday_pre_open": "周一报告",
        "friday_post_close": "周五报告",
    }[session]
    return f"{prefix}_{compact_date(as_of)}"


def legacy_kline_report_name(as_of: str) -> str:
    return f"4. K线分析报告_{compact_date(as_of)}"
