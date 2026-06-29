# KMFA S01-P1 Implementation Plan

更新时间: 2026-06-29
阶段: S01｜只读启动与项目治理基线
本轮 Phase: P1｜只读检查与范围锁定
模式: PLAN / READ_ONLY

## 1. 本轮目标

完成第一轮只读计划与范围锁定，不做业务实现，不创建正式 `KMFA/` 项目骨架，不写 UI，不生成经营报告，不接任何外部自动接口。

本轮只交付计划、文件清单、测试命令、回滚方案、风险登记、停止条件与防遗漏验证结果。

## 2. 已验证事实

| 项目 | 状态 | 证据 |
|---|---|---|
| 当前工作目录 | VERIFIED | `/Users/linzezhang/Documents/KMFA v0.1` |
| 当前仓库 | VERIFIED | 空 Git 仓库，仅有 `.git`，当前分支 `main`，未配置 remote |
| 指定 GitHub 路径 | USER-PROVIDED | `LinzeColin/CodexProject/KMFA` |
| 任务包路径 | VERIFIED | `/Users/linzezhang/Downloads/KMFA v0.1/01_KMFA_Codex_TaskPack_v1_1_完整防遗漏.md` |
| Roadmap 路径 | VERIFIED | `/Users/linzezhang/Downloads/KMFA v0.1/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_1.md` |
| 交付包 zip | VERIFIED | `/Users/linzezhang/Downloads/KMFA v0.1/KMFA_ChatGPT_Stage3_Codex_Delivery_Pack_v1_1_18Stages.zip` |
| `CodexProject/KMFA` 本地目录 | NOT FOUND | 当前浅查未发现可用 checkout |
| `CodexProject/AGENTS.md` | NOT FOUND | 当前浅查未发现文件 |
| `CodexProject/docs/governance/STANDARD.md` | NOT FOUND | 当前浅查未发现文件 |

## 3. Stage/Phase 边界

本轮只执行 `S01-P1`。

`S01-P2` 的内容包括创建 `KMFA/` 目录草案、README、功能清单、开发记录、模型参数文件、governance/project 配置草案。本轮不执行这些动作。

`S01-P3` 的内容包括导入需求追溯矩阵、新增 `no_omission` 检查脚本、建立 Stage/Phase/Task 状态登记文件。本轮不执行这些动作。

## 4. 双平面结构约束

后续正式 `KMFA/` 目录应按双平面组织:

| 平面 | 目的 | S01-P2 推荐入口 |
|---|---|---|
| 人类可读面 | 给管理者、开发者、复审者阅读 | `KMFA/README.md`, `KMFA/功能清单.md`, `KMFA/开发记录.md`, `KMFA/模型参数.md` |
| 机器可读面 | 给校验、CI、治理、追溯使用 | `KMFA/metadata/project/project.yaml`, `KMFA/metadata/stage_status.jsonl`, `KMFA/metadata/traceability/requirements.csv`, `KMFA/metadata/model_registry.yaml` |

三中文入口建议锁定为:

1. `KMFA/README.md`
2. `KMFA/功能清单.md`
3. `KMFA/开发记录.md`

`KMFA/模型参数.md` 必须同步维护，但不建议算作三入口之一；它应同时有机器可读镜像 `KMFA/metadata/model_registry.yaml`。

## 5. P0/P1 基线

P0 是文件型项目成本分析 MVP，优先覆盖项目成本权威基准、金额精度、零差异、原始数据不可污染、引用一致性、数据源检查矩阵、真实经营报告可读性、防遗漏协议。

P1 包括经营报表、回款应收、销售绩效事实、资金计划、开票纳税证据、外协采购归集、项目交付状态、客户经营分析。

P2 后续项不进入第一轮 MVP，尤其红圈自动接入、OpMe 接入、财务 SOP 深度化。

## 6. 后续 Phase 计划

| Phase | 目标 | 推荐动作 |
|---|---|---|
| S01-P2 | 项目骨架与中文入口 | 在正确的 `CodexProject/KMFA` 位置创建正式目录和双平面入口 |
| S01-P3 | 防遗漏基线 | 导入需求追溯矩阵，新增 no_omission 脚本，建立状态登记 |
| S01 复审 | Stage 级复审 | 统一检查 S01-P1/P2/P3 产物，修复复审问题后再准备 GitHub 上传 |

## 7. 不做事项

- 不直接写 UI。
- 不直接生成经营报告。
- 不接红圈、金蝶、WPS、银行、税务自动接口。
- 不提交或复制原始敏感经营数据到公开仓库。
- 不修改原始下载包或原始上传数据。
- 不实现业务金额计算。
- 不创建正式 `KMFA/` 项目骨架。
- 不上传 GitHub。
