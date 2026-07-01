# S16-P1 外协采购归集完成记录

更新时间: 2026-07-01

## 范围

- Phase: `S16-P1｜外协采购归集`
- Task: `S16PAT01-S16PAT03`
- 目标: 建立 public-safe 外协费用、采购、付款按项目匹配证据；未匹配进入未归集成本池；识别重复付款和跨项目费用候选。
- 非目标: 不执行 S16-P2、S16-P3、Stage 16 review、GitHub upload、lineage full check、正式报告、采购执行、付款审批、付款执行、银行操作或外部 connector。

## 输出

| 类型 | 路径 |
|---|---|
| implementation | `KMFA/tools/subcontract_procurement_aggregation.py` |
| validator | `KMFA/tools/check_s16_p1_subcontract_procurement.py` |
| unit tests | `KMFA/tests/test_subcontract_procurement_aggregation.py` |
| manifest | `KMFA/metadata/reports/subcontract_procurement_aggregation_manifest.json` |
| source lanes | `KMFA/metadata/reports/subcontract_procurement_source_lanes.jsonl` |
| project matches | `KMFA/metadata/reports/subcontract_project_matches.jsonl` |
| unallocated pool | `KMFA/metadata/reports/subcontract_unallocated_cost_pool.jsonl` |
| anomaly candidates | `KMFA/metadata/reports/subcontract_anomaly_candidates.jsonl` |
| stage manifest | `KMFA/stage_artifacts/S16_P1_subcontract_procurement_aggregation/machine/s16_p1_manifest.json` |
| test results | `KMFA/stage_artifacts/S16_P1_subcontract_procurement_aggregation/human/test_results.md` |

## 验收结果

- 生成 4 条 public-safe source lane: 外协费用结构线、采购登记结构线、付款登记结构线、项目身份桥接线。
- 生成 5 条项目匹配记录: 2 条 matched、1 条 cross-project candidate、2 条 unmatched。
- 2 条 unmatched 记录已进入未归集成本池，状态为 `pending_project_assignment_or_owner_review`。
- 生成 4 条异常候选: 2 条重复付款候选、2 条跨项目费用候选，均为人工复核，不触发业务执行动作。
- 报告等级继续显示 `D`，12 条 pending reconciliation 继续阻断正式报告和经营决策依据。
- 公开仓库只保存 source/hash/status/evidence metadata，不保存 raw business data、zip、Excel、PDF、private CSV、字段明文、真实金额、真实账号、银行流水、合同、薪资、税务申报材料或 credentials。

## 风险与边界

- S16-P1 输出只能作为复核队列和结构证据，不能作为付款、采购、银行、供应商结算或经营决策依据。
- 未归集成本池和异常候选需要 owner 或授权人员复核后，才可能进入后续人工处理或重跑流程。
- 本 phase 未做 Stage 16 整体复审，不能上传 GitHub。

## 下一步

下一轮只能执行 `S16-P2｜项目状态生命周期`；不得跳到 S16-P3、Stage 16 review、GitHub upload、lineage full check、正式报告或外部接口。
