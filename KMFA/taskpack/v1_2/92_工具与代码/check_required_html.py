#!/usr/bin/env python3
from pathlib import Path
import sys
root=Path(__file__).resolve().parents[1]
required=['20_HTML_UIUX_报告预览/00_HTML总入口_KMFA_v1_2.html','20_HTML_UIUX_报告预览/01_核心HTML验收样板/KMFA_系统首页预览_v4_blue.html','20_HTML_UIUX_报告预览/01_核心HTML验收样板/KMFA_经营分析报告预览_v3_blue.html','20_HTML_UIUX_报告预览/01_核心HTML验收样板/KMFA_数据源检查板_v0_5_blue.html','20_HTML_UIUX_报告预览/01_核心HTML验收样板/KMFA_项目成本专题报告预览_v0_6_blue_zero_delta.html','20_HTML_UIUX_报告预览/01_核心HTML验收样板/KMFA_Resolution_Workbench_v0_4.html']
missing=[p for p in required if not (root/p).exists()]
if missing:
    print('FAIL: missing required HTML files:'); print('\n'.join(missing)); sys.exit(1)
print('PASS: required HTML/UIUX/report preview files are present.')
