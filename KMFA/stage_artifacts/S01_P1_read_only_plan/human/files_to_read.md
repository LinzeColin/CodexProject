# KMFA S01-P1 Files To Read

更新时间: 2026-06-29

## 1. 本轮已读取

| 文件 | 状态 | 用途 |
|---|---|---|
| `/Users/linzezhang/Downloads/KMFA v0.1/01_KMFA_Codex_TaskPack_v1_1_完整防遗漏.md` | READ | 项目身份、P0/P1目标、禁止事项、第一轮只读要求、验收定义 |
| `/Users/linzezhang/Downloads/KMFA v0.1/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_1.md` | READ | 18 Stage 结构与 S01-P1/P2/P3 边界 |
| `/Users/linzezhang/Downloads/KMFA v0.1/KMFA_ChatGPT_Stage3_Codex_Delivery_Pack_v1_1_18Stages.zip` | READ/INSPECTED | 包清单、第一轮提示词、辅助治理文件、参考工具 |
| `/tmp/kmfa_s01p1_pack/KMFA_ChatGPT_Stage3_Codex_Delivery_v1_1/03_KMFA_Codex_第一轮只读启动提示词_v1_1.md` | READ | PLAN / READ_ONLY 输出要求 |
| `/tmp/kmfa_s01p1_pack/KMFA_ChatGPT_Stage3_Codex_Delivery_v1_1/04_KMFA_需求追溯矩阵_v1_1.csv` | READ | P0/P1 需求覆盖、门禁、测试证据 |
| `/tmp/kmfa_s01p1_pack/KMFA_ChatGPT_Stage3_Codex_Delivery_v1_1/05_KMFA_数据治理与质量门禁_v1_1.md` | READ | metadata、质量等级、报告发布门禁 |
| `/tmp/kmfa_s01p1_pack/KMFA_ChatGPT_Stage3_Codex_Delivery_v1_1/06_KMFA_模型公式函数参数主注册表_v1_1.yaml` | READ | 金额精度、匹配权重、报告等级、质量门禁 |
| `/tmp/kmfa_s01p1_pack/KMFA_ChatGPT_Stage3_Codex_Delivery_v1_1/08_KMFA_零差异验证与测试计划_v1_1.md` | READ | 零差异定义、必测场景、通过标准 |
| `/tmp/kmfa_s01p1_pack/KMFA_ChatGPT_Stage3_Codex_Delivery_v1_1/09_KMFA_前端交互与人类可读报告规范_v1_1.md` | READ | 全中文、商务蓝、首页模块、前端写入限制 |
| `/tmp/kmfa_s01p1_pack/KMFA_ChatGPT_Stage3_Codex_Delivery_v1_1/10_KMFA_最终交付检查清单_v1_1.md` | READ | Stage 完成前检查、P0质量门禁、Go/No-Go |

## 2. 本轮应读但未发现

| 文件 | 状态 | 处理方式 |
|---|---|---|
| `CodexProject/AGENTS.md` | NOT FOUND | 不能伪造；S01-P2 前需在正确 checkout 中确认 |
| `CodexProject/docs/governance/STANDARD.md` | NOT FOUND | 不能伪造；S01-P2 前需在正确 checkout 中确认 |
| `CodexProject/KMFA` | NOT FOUND | 与用户说明一致；正式目录创建属于 S01-P2 |

## 3. S01-P2 必读

1. 正确 `LinzeColin/CodexProject` 本地 checkout 的根目录状态。
2. 根 `AGENTS.md`。
3. `docs/governance/STANDARD.md` 或同等治理文件。
4. 本轮产物: `stage_artifacts/S01_P1_read_only_plan/`。
5. 下载包内完整 `README.md`、需求追溯矩阵、治理文件、模型参数文件。
