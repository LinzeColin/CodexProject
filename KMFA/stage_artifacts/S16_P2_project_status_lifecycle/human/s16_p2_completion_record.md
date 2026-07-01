# S16-P2 项目状态生命周期完成记录

更新时间: 2026-07-01

## 范围

- Phase: `S16-P2｜项目状态生命周期`
- Task: `S16PBT01-S16PBT03`
- 目标: 接入生产项目状态、开工、完工、结算、开票、回款六类 public-safe 状态线，生成项目生命周期与异常事项，并锁定现场施工、安全、技术签字的人工作业边界。
- 非目标: 不执行 S16-P1、S16-P3、Stage 16 review、GitHub upload、lineage full check、正式报告、现场施工、开工确认、完工验收、安全签字、技术签字、结算确认、发票开具、催收、付款、银行操作或外部 connector。

## 输出

| 类型 | 路径 |
|---|---|
| implementation | `KMFA/tools/project_status_lifecycle.py` |
| validator | `KMFA/tools/check_s16_p2_project_status_lifecycle.py` |
| unit tests | `KMFA/tests/test_project_status_lifecycle.py` |
| manifest | `KMFA/metadata/reports/project_status_lifecycle_manifest.json` |
| source lanes | `KMFA/metadata/reports/project_status_source_lanes.jsonl` |
| lifecycle records | `KMFA/metadata/reports/project_lifecycle_records.jsonl` |
| exception items | `KMFA/metadata/reports/project_lifecycle_exception_items.jsonl` |
| handoff guards | `KMFA/metadata/reports/project_lifecycle_handoff_guards.jsonl` |
| stage manifest | `KMFA/stage_artifacts/S16_P2_project_status_lifecycle/machine/s16_p2_manifest.json` |
| test results | `KMFA/stage_artifacts/S16_P2_project_status_lifecycle/human/test_results.md` |

## 验收结果

- 生成 6 条 public-safe source lane: 生产项目状态、开工状态、完工状态、结算状态、开票状态、回款状态。
- 生成 4 条 public-safe lifecycle record: 在建已开工、完工未结算、结算未开票、开票未回款。
- 生成 3 条异常事项: 完工未结算、结算未开票、开票未回款，均为人工复核，不触发开票、催收、付款、银行或现场动作。
- 生成 3 条 handoff guard: 现场施工、安全签字、技术验收/签字必须由 owner 或授权现场角色处理，KMFA 不代替执行。
- 报告等级继续显示 `D`，12 条 pending reconciliation 继续阻断正式报告和经营决策依据。
- 公开仓库只保存 refs、hashes、statuses、evidence metadata，不保存 raw business data、zip、Excel、PDF、private CSV、字段明文、真实金额、真实项目/客户名称、银行流水、合同、薪资、税务申报材料或 credentials。

## 风险与边界

- S16-P2 输出只能作为项目生命周期复核队列和结构证据，不能作为现场施工、安全、技术、结算、开票、催收、付款或银行动作依据。
- 异常事项必须由 owner 或授权角色复核后，才可能进入后续人工处理或重跑流程。
- 本 phase 未做 Stage 16 整体复审，不能上传 GitHub。

## 下一步

下一轮只能执行 `S16-P3｜客户经营分析`；不得直接进入 Stage 16 review、GitHub upload、lineage full check、正式报告或外部接口。
