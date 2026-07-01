# S16-P3 客户经营分析完成记录

更新时间: 2026-07-01

## 范围

- Phase: `S16-P3｜客户经营分析`
- Task: `S16PCT01-S16PCT03`
- 目标: 基于既有 public-safe 客户/项目关系、项目毛利、回款质量、账龄风险和项目生命周期证据，生成客户经营摘要和异常复核清单。
- 非目标: 不执行 Stage 16 review、GitHub upload、lineage full check、正式报告、客户自动联系、自动催收、法律决策、付款审批、付款执行、银行操作、开票、纳税申报、工资/奖金/薪资导出、外部 connector 或业务 release。

## 输出

| 类型 | 路径 |
|---|---|
| implementation | `KMFA/tools/customer_business_analysis.py` |
| validator | `KMFA/tools/check_s16_p3_customer_business_analysis.py` |
| unit tests | `KMFA/tests/test_customer_business_analysis.py` |
| manifest | `KMFA/metadata/reports/customer_business_analysis_manifest.json` |
| source lanes | `KMFA/metadata/reports/customer_analysis_source_lanes.jsonl` |
| customer summaries | `KMFA/metadata/reports/customer_operating_summaries.jsonl` |
| exception items | `KMFA/metadata/reports/customer_analysis_exception_items.jsonl` |
| stage manifest | `KMFA/stage_artifacts/S16_P3_customer_business_analysis/machine/s16_p3_manifest.json` |
| test results | `KMFA/stage_artifacts/S16_P3_customer_business_analysis/human/test_results.md` |

## 验收结果

- 生成 5 条 public-safe source lane: 客户-项目-应收关系模型、项目毛利信号、回款质量信号、账龄风险信号、项目生命周期信号。
- 生成 4 条 public-safe customer operating summary，覆盖客户价值、项目毛利、回款质量、账龄风险 4 个维度。
- 生成 4 条异常事项: 账龄风险偏高、回款质量需复核、项目毛利需复核、项目生命周期需人工交接，均为 owner 或授权角色人工复核。
- 报告等级继续显示 `D`，12 条 pending reconciliation 继续阻断正式报告和经营决策依据。
- 公开仓库只保存 refs、hashes、statuses、evidence metadata，不保存 raw business data、zip、Excel、PDF、private CSV、字段明文、真实金额、真实客户/项目名称、银行流水、合同、薪资、税务申报材料或 credentials。

## 风险与边界

- S16-P3 输出只能作为客户经营复核队列和结构证据，不能作为正式经营决策、自动催收、客户联系、法律决策、开票、付款、银行或外部接口动作依据。
- 异常事项必须由 owner 或授权角色复核后，才可能进入后续人工处理或重跑流程。
- 本 phase 未做 Stage 16 整体复审，不能上传 GitHub。

## 下一步

下一轮只能执行 `Stage 16 整体复审`；不得直接进入 GitHub upload、lineage full check、正式报告、业务执行或外部接口。
