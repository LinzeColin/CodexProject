# S14-P2 开票纳税完成记录

- completed_at: `2026-07-01T23:00:00+10:00`
- scope: `开票计划、纳税明细、开票纳税资金汇总 public-safe 结构接入；待开票、已开票未回款、税率异常候选识别；不做纳税申报和发票开具`
- status: `completed_validated_local_only`
- task_ids: `S14PBT01-S14PBT03`
- report_grade_visible: `D`
- pending_reconciliation_count: `12`

## 输出

| 输出 | 结果 |
|---|---|
| source lanes | `3` 条：`invoice_plan`, `tax_detail`, `invoice_tax_cash_summary` |
| issue candidates | `3` 条：`pending_invoice`, `invoiced_not_collected`, `tax_rate_exception_candidate` |
| cash summaries | `3` 条：开票预计现金流入、纳税预计现金流出、开票纳税净资金压力 |
| HTML evidence | `KMFA/stage_artifacts/S14_P2_invoice_tax_plan/exports/html/invoice_tax_plan_overview.html` |
| validator | `KMFA/tools/check_s14_p2_invoice_tax_plan.py` |

## 公开仓库边界

- 不提交 raw business data、zip、Excel、PDF、sqlite/db、private CSV、银行流水、合同、薪资、税务申报文件或 credentials。
- 不提交字段明文、真实金额、真实税率值、真实发票号、真实账号、真实客户/项目明细。
- 只保存 source refs、字段 key refs、hash/ref/status、候选类型、D 级门禁和证据索引。

## 操作边界

- `tax_filing_allowed=false`
- `tax_declaration_generation_allowed=false`
- `invoice_issuance_allowed=false`
- `invoice_operation_allowed=false`
- `payment_approval_allowed=false`
- `bank_operation_allowed=false`
- `formal_report_allowed=false`
- `business_decision_basis_allowed=false`
- `s14_p3_allowed=false`
- `stage14_review_allowed=false`
- `github_upload_allowed=false`

## 下一步

继续 KMFA，只执行一个 phase：`S14-P3｜政策证据`。先确认 git root、branch、remote、HEAD、status。不得执行 Stage 14 整体复审、GitHub upload、lineage full check、正式报告、差异关闭、外部接口、发票开具、纳税申报、付款、银行、贷款管理或政策资格正式结论。验收必须包含 tests、validator、evidence 和 local commit。
