# KMFA v0.1.4 S13-P1 Financial Operating Report

- task_id: `KMFA-V014-S13-P1-FINANCIAL-OPERATING-REPORT-20260705`
- status: `completed_validated_local_only_no_go_upload_deferred`
- phase_scope: `v014_s13_p1_financial_operating_report_only`
- source_lanes: `4`
- drafts: `2`
- html_drafts: `2`
- field_mappings: `39`
- pending_reconciliation_count: `12`
- report_grade_visible: `D`
- formal_report_allowed: `false`
- business_decision_basis_allowed: `false`
- s13_p2_performed: `false`
- s13_p3_performed: `false`
- stage13_review_performed: `false`
- github_upload_performed: `false`
- raw_inbox_read_by_this_phase: `false`

## Coverage

- T1: 接入经营情况、费用税金资产、现金情况、贷款明细 4 条 public-safe source lanes。
- T2: 生成经营周报初稿和经营月报初稿，两份 HTML draft 均为 public-safe。
- T3: 显示数据状态、报告等级 D、12 条 pending reconciliation 和正式报告/经营决策限制。

## Boundary

- 不提交 raw business data、字段明文、真实金额、真实账号、Excel workbook、PDF、zip、sqlite/db、private CSV 或 credentials。
- 不执行 S13-P2、S13-P3、Stage 13 review、GitHub upload、protected source matching、lineage full check、正式报告、外部接口、付款、贷款管理、税务申报或业务执行。
