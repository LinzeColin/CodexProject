#!/usr/bin/env python3
from pathlib import Path
import sys
root=Path(__file__).resolve().parents[1]
required_dirs=['20_HTML_UIUX_报告预览','21_前序生成包归档_可追溯','90_用户原始上传数据_仅本地私有_禁止提交GitHub','92_工具与代码']
required_files=['01_KMFA_Codex_TaskPack_v1_2_完整防遗漏_含HTML验收样板.md','02_KMFA_Codex_Development_Roadmap_18_Stages_v1_2.md','00_总索引与补漏复核/KMFA_补漏复核报告_v1_2.md','03_KMFA_Codex_第一轮只读启动提示词_v1_1.md','04_KMFA_需求追溯矩阵_v1_1.csv','05_KMFA_数据治理与质量门禁_v1_1.md','06_KMFA_模型公式函数参数主注册表_v1_1.yaml','07_KMFA_业务线模块矩阵_v1_1.csv','08_KMFA_零差异验证与测试计划_v1_1.md','09_KMFA_前端交互与人类可读报告规范_v1_1.md','10_KMFA_最终交付检查清单_v1_1.md']
missing=[d for d in required_dirs if not (root/d).is_dir()]+[f for f in required_files if not (root/f).is_file()]
if missing:
    print('FAIL: missing required package components:'); print('\n'.join(missing)); sys.exit(1)
print('PASS: v1.2 package required components present, including v1.1 formal files and HTML supplements.')
