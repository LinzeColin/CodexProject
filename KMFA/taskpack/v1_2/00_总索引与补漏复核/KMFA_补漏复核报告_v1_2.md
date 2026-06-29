# KMFA ChatGPT 阶段三 v1.2｜补漏复核报告

## 1. 本次发现的实际遗漏

v1.1 交付包没有包含 HTML 文件。该遗漏会导致 Codex 虽然能看到 TaskPack 和 Roadmap，但缺少系统首页、报告、数据源检查板、人工处理工作台等 UIUX / 报告验收样板。

本版已修正：

| 类别 | 状态 |
|---|---:|
| HTML总入口 | 已补齐 |
| 核心HTML验收样板 | 7 个 |
| 前序HTML完整归档 | 37 个 |
| 包内HTML总数 | 45 个 |
| 前序生成包归档 | 12 个 |
| 用户原始上传数据归档 | 5 个 |
| 前序散件归档 | 23 个文件 |

## 2. 本包必须被 Codex 继承的目录

```text
01_KMFA_Codex_TaskPack_v1_2_完整防遗漏_含HTML验收样板.md
02_KMFA_Codex_Development_Roadmap_18_Stages_v1_2.md
03_KMFA_Codex_第一轮只读启动提示词_v1_1.md
04_KMFA_需求追溯矩阵_v1_1.csv
05_KMFA_数据治理与质量门禁_v1_1.md
06_KMFA_模型公式函数参数主注册表_v1_1.yaml
07_KMFA_业务线模块矩阵_v1_1.csv
08_KMFA_零差异验证与测试计划_v1_1.md
09_KMFA_前端交互与人类可读报告规范_v1_1.md
10_KMFA_最终交付检查清单_v1_1.md
20_HTML_UIUX_报告预览/
21_前序生成包归档_可追溯/
90_用户原始上传数据_仅本地私有_禁止提交GitHub/
91_前序散件归档/
92_工具与代码/
```

## 3. HTML 核心样板清单

| 文件 | 作用 |
|---|---|
| KMFA_系统首页预览_v4_blue.html | 系统首页、模块入口、商务蓝色系风格 |
| KMFA_经营分析报告预览_v3_blue.html | 经营报告样式、报告语气、表格与图表密度 |
| KMFA_数据源检查板_v0_5_blue.html | 多来源、多板块、多主体、多账户矩阵检查 |
| KMFA_项目成本专题报告预览_v0_6_blue_zero_delta.html | P0 项目成本报告与零差异门禁 |
| KMFA_Resolution_Workbench_v0_4.html | 人工差异处理、非污染写入、影响预览、重跑 |
| KMFA_Ring5_Final_Task_Control_Board.html | 阶段任务控制台与质量门禁 |
| KMFA_阶段三任务控制台预览_v1_0.html | Codex 开发阶段控制台验收样板 |

## 4. 数据与文件不遗漏规则

- 原始上传数据不应提交公开 GitHub，但本交付包已放在 `90_用户原始上传数据_仅本地私有_禁止提交GitHub/` 作为本地私有证据。
- 前序所有生成包已放在 `21_前序生成包归档_可追溯/`。
- 前序散件目录已放在 `91_前序散件归档/`。
- 所有正式开发必须从 TaskPack + Roadmap + HTML + 数据治理 + 前序归档共同读取，不能只读一个 Markdown。

## 5. 仍需人工注意

| 项目 | 说明 |
|---|---|
| 原始财务/项目数据 | 仅本地私有使用，不得提交公开 GitHub |
| 屏幕录制 | 已归档，但尚未做逐帧/逐秒需求解析；若视频里还有 UI 要求，阶段三前可单独提取 |
| PDF/Excel冲突 | 系统不自动选边，进入人工处理队列 |
| 金蝶/红圈自动接入 | 后置，MVP 文件型优先 |
| HTML样式 | 样板是验收基线，Codex 可优化但不能降低商务质感和人类可读性 |

## 6. 自检命令

```bash
python3 92_工具与代码/check_required_html.py
python3 92_工具与代码/check_v1_2_no_omission.py
python3 tools/no_omission_check.py
python3 tools/zero_delta_validator_reference.py
```
