#!/usr/bin/env python3
"""Anomaly rule names and safety labels for KMFA S19."""

from __future__ import annotations


MORNING_PENDING_LABEL = "待确认异常"
EVENING_EXCEPTION_LABELS = (
    "迟到",
    "早退",
    "缺卡",
    "待审批",
    "待补卡",
    "待核查",
)


def morning_absence_label() -> str:
    return MORNING_PENDING_LABEL
