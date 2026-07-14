# KMFA v0.1.4 S13-P2 Collection Receivable Aging

- task_id: `KMFA-V014-S13-P2-COLLECTION-RECEIVABLE-AGING-20260705`
- status: `completed_validated_local_only_no_go_upload_deferred`
- phase_scope: `v014_s13_p2_collection_receivable_aging_only`
- source_lanes: `5`
- sources: `5`
- field_mappings: `25`
- issue_types: `4`
- priority_items: `4`
- responsibility_items: `4`
- html_drafts: `1`
- pending_reconciliation_count: `12`
- report_grade_visible: `D`
- formal_report_allowed: `false`
- business_decision_basis_allowed: `false`
- legal_collection_decision_allowed: `false`
- payment_or_bank_operation_allowed: `false`
- s13_p3_performed: `false`
- stage13_review_performed: `false`
- github_upload_performed: `false`
- raw_inbox_read_by_this_phase: `false`

## Coverage

- T1: 接入回款表、应收账龄、客户账龄、日记账、开票计划 5 条 public-safe source lanes。
- T2: 锁定已开票未回款、完工未结算、结算未开票、超期应收 4 类问题候选。
- T3: 输出 4 条回款优先级草案和 4 条责任事项草案，并显示报告等级 D 与执行限制。

## Boundary

- 不提交 raw business data、字段明文、真实金额、真实账号、Excel workbook、PDF、zip、sqlite/db、private CSV 或 credentials。
- 不执行 S13-P3、Stage 13 review、GitHub upload、protected source matching、lineage full check、正式报告、催收、法务、付款、银行、开票、税务或业务执行。
