# KMFA ChatGPT 阶段三交付包 v1.4｜人类流程核验与原始数据只读协议补发版

本包修正上一版交付中最严重的问题：HTML/UIUX 不能只是“看起来有页面”，必须能够按真实用户路径点击、筛选、状态变更、处理差异、生成影响预览、重跑链路和查看报告。

## 关键入口

| 文件/目录 | 用途 |
|---|---|
| `01_KMFA_Codex_TaskPack_v1_4_完整防遗漏_含HTML与本机原始数据协议.md` | 给 Codex 的完整任务包，包含 v1.4 补漏规则 |
| `02_KMFA_Codex_Development_Roadmap_18_Stages_v1_4.md` | 给 Codex 的 18 Stage 开发路线图 |
| `20_HTML_UIUX_报告预览/03_v1_4可点击验收样板/` | 当前唯一有效的 HTML/UIUX 验收样板 |
| `30_UIUX自动化验收/KMFA_v1_4修复版HTML点击审计结果.csv` | 本地 Playwright 点击审计结果：54 PASS / 0 WARN / 0 FAIL |
| `30_UIUX自动化验收/kmfa_html_human_flow_audit.py` | 可复用 HTML 人类流程点击审计脚本 |
| `40_本机原始数据协议/` | `/Users/linzezhang/Downloads/KMFA_MetaData` 只读原始数据根目录协议 |
| `41_Codex本机读取提示词/` | Codex 在本机读取原始数据前必须使用的只读启动提示词 |
| `90_用户原始上传数据_仅本地私有_禁止提交GitHub/` | 用户上传原始资料的本地私有归档，禁止提交公开 GitHub |

## 结论

- v1.2 HTML 仅作为历史追溯，不作为验收标准。
- v1.4 HTML 是当前 UIUX 验收基线。
- Codex 不能只按 Roadmap 写代码；必须读取 TaskPack、Roadmap、HTML、数据治理协议、点击审计结果和原始数据只读协议。
- 原始数据目录 `/Users/linzezhang/Downloads/KMFA_MetaData` 只读，所有派生数据必须写入 KMFA 自己的 local_runtime 或 metadata，不得污染原始文件。

