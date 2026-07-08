#!/usr/bin/env python3
"""Report rendering contracts for KMFA S19 attendance reports."""

from __future__ import annotations

from typing import Any


MANAGEMENT_REPORT_SECTIONS = (
    "一、总体情况",
    "二、今日异常人员",
    "三、建议动作",
    "四、系统运行状态",
)

HR_REPORT_SECTIONS = (
    "一、异常明细",
    "二、连续异常人员",
    "三、数据质量与系统运行状态",
)


def render_management_report(context: dict[str, Any]) -> str:
    title = context.get("title", "开明考勤管理报告｜待运行｜北京时间")
    lines = [f"# {title}", ""]
    for section in MANAGEMENT_REPORT_SECTIONS:
        lines.extend([f"## {section}", context.get(section, "待真实数据运行后生成。"), ""])
    return "\n".join(lines).strip() + "\n"


def render_hr_report(context: dict[str, Any]) -> str:
    title = context.get("title", "开明考勤 HR 报告｜待运行｜北京时间")
    lines = [f"# {title}", ""]
    for section in HR_REPORT_SECTIONS:
        lines.extend([f"## {section}", context.get(section, "待真实数据运行后生成。"), ""])
    return "\n".join(lines).strip() + "\n"
