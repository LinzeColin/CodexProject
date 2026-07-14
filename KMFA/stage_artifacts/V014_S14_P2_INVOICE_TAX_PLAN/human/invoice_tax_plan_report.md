# KMFA v0.1.4 S14-P2 Invoice Tax Plan

- task_id: `KMFA-V014-S14-P2-INVOICE-TAX-PLAN-20260705`
- status: `completed_validated_local_only_no_go_upload_deferred`
- phase_scope: `v014_s14_p2_invoice_tax_plan_only`
- source_lanes: `3`
- source_count: `6`
- field_mappings: `30`
- issue_candidates: `3`
- cash_summaries: `3`
- pending_reconciliation_count: `12`
- report_grade_visible: `D`
- formal_report_allowed: `false`
- business_decision_basis_allowed: `false`
- tax_filing_allowed: `false`
- tax_declaration_generation_allowed: `false`
- invoice_issuance_allowed: `false`
- invoice_operation_allowed: `false`
- payment_or_bank_operation_count: `0`
- external_connector_action_count: `0`
- s14_p3_performed: `false`
- stage14_review_performed: `false`
- github_upload_performed: `false`
- raw_inbox_read_by_this_phase: `false`

## Coverage

- T1: 接入开票计划、纳税明细、开票纳税资金汇总 3 条 public-safe source lanes。
- T2: 输出待开票、已开票未回款、税率异常候选 3 类候选事项，以及 3 条开票纳税资金汇总状态。
- T3: 锁定不做纳税申报、申报文件生成、发票开具、发票接口调用、付款、银行操作、贷款管理、正式报告或业务执行。

## Boundary

- 不提交 raw business data、source schema plaintext、真实金额、真实税率值、真实发票号、税务申报号、Excel workbook、PDF、zip、sqlite/db、private CSV 或 credentials。
- 不执行 S14-P3、Stage 14 review、GitHub upload、protected source matching、lineage full check、正式报告、外部接口、付款、银行、贷款管理、开票、纳税申报、政策申报、补贴申请或业务执行。
