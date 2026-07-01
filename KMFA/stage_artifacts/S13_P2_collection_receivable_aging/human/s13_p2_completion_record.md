# S13-P2｜回款应收账龄完成记录

- project_id: `KMFA`
- stage_phase: `S13-P2`
- completed_at: `2026-07-01T18:00:00+10:00`
- status: `completed_validated_local_only`
- scope: `回款表、应收账龄、客户账龄、日记账、开票计划的 public-safe source lane；已开票未回款、完工未结算、结算未开票、超期应收四类问题；回款优先级和责任事项草案`

## 产物

- `KMFA/tools/collection_receivable_aging.py`
- `KMFA/tools/check_s13_p2_collection_receivable_aging.py`
- `KMFA/tests/test_collection_receivable_aging.py`
- `KMFA/metadata/reports/collection_receivable_aging_manifest.json`
- `KMFA/metadata/reports/collection_receivable_aging_source_lanes.jsonl`
- `KMFA/metadata/reports/collection_receivable_aging_priority_items.jsonl`
- `KMFA/metadata/reports/collection_receivable_aging_responsibility_items.jsonl`
- `KMFA/stage_artifacts/S13_P2_collection_receivable_aging/machine/s13_p2_manifest.json`
- `KMFA/stage_artifacts/S13_P2_collection_receivable_aging/exports/html/collection_receivable_aging_priority.html`

## 验收结果

- source lanes: `5`
- issue types: `4`
- priority items: `4`
- responsibility items: `4`
- pending reconciliation: `12`
- report grade visible: `D`
- formal_report_allowed: `false`
- business_decision_basis_allowed: `false`
- legal_collection_decision_allowed: `false`
- payment_or_bank_operation_allowed: `false`
- s13_p3_scope_included: `false`
- stage13_review_scope_included: `false`
- github_upload_scope_included: `false`

## 边界

本 phase 不提交 raw business data、zip、Excel、PDF、私有 CSV、字段明文、真实金额、真实客户/项目明细、银行账号或 credentials。

本 phase 不执行 S13-P3、Stage 13 整体复审、GitHub upload、lineage full check、正式报告、差异关闭、外部接口、开票、付款、银行、税务或法务催收动作。

## 下一步

下一轮只能执行 `S13-P3｜跨表复核`；S13-P3 完成并本地验证后，才能进入 Stage 13 整体复审。
