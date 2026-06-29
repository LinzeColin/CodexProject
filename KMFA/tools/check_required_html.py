#!/usr/bin/env python3
"""Validate KMFA v1.2 HTML/UIUX/report acceptance samples.

This is a repository-side gate. It checks the public-safe task-pack baseline
under KMFA/taskpack/v1_2, not the private raw source package.
"""

from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "taskpack" / "v1_2"

REQUIRED_HTML = [
    "20_HTML_UIUX_报告预览/00_HTML总入口_KMFA_v1_2.html",
    "20_HTML_UIUX_报告预览/01_核心HTML验收样板/KMFA_系统首页预览_v4_blue.html",
    "20_HTML_UIUX_报告预览/01_核心HTML验收样板/KMFA_经营分析报告预览_v3_blue.html",
    "20_HTML_UIUX_报告预览/01_核心HTML验收样板/KMFA_数据源检查板_v0_5_blue.html",
    "20_HTML_UIUX_报告预览/01_核心HTML验收样板/KMFA_项目成本专题报告预览_v0_6_blue_zero_delta.html",
    "20_HTML_UIUX_报告预览/01_核心HTML验收样板/KMFA_Resolution_Workbench_v0_4.html",
    "20_HTML_UIUX_报告预览/01_核心HTML验收样板/KMFA_Ring5_Final_Task_Control_Board.html",
    "20_HTML_UIUX_报告预览/01_核心HTML验收样板/KMFA_阶段三任务控制台预览_v1_0.html",
]


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def main() -> int:
    if not BASELINE.is_dir():
        fail("missing baseline directory: KMFA/taskpack/v1_2")

    missing = [rel for rel in REQUIRED_HTML if not (BASELINE / rel).is_file()]
    if missing:
        fail("missing required HTML files: " + ", ".join(missing))

    html_files = list((BASELINE / "20_HTML_UIUX_报告预览").rglob("*.html"))
    core_html_files = list((BASELINE / "20_HTML_UIUX_报告预览" / "01_核心HTML验收样板").glob("*.html"))
    if len(html_files) != 45:
        fail(f"expected 45 HTML files from v1.2 FULL_HTML baseline, found {len(html_files)}")
    if len(core_html_files) != 7:
        fail(f"expected 7 core HTML acceptance samples, found {len(core_html_files)}")

    print("PASS: required KMFA v1.2 HTML/UIUX/report samples are present (html=45, core=7).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
