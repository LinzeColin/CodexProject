# KMFA S15-P1 绩效事实字段完成记录

更新时间: 2026-07-01

## 目标

基于 v1.2 task pack / roadmap 的 `S15-P1｜绩效事实字段`，建立 public-safe 绩效事实字段定义、字段绑定和缺失人工复核标记。只完成字段层，不输出绩效事实表、不生成异常项目复核清单、不计算工资或奖金、不执行 Stage 15 整体复审或 GitHub upload。

## 范围

已覆盖字段:

- `invoice_amount`
- `gross_margin_rate`
- `settlement_speed`
- `collection_speed`
- `audit_variance`
- `customer_relationship_rate`

已建立绑定:

- 开票金额绑定 S09 项目成本事实层和 S14 开票纳税 planning evidence。
- 毛利率绑定 S09 毛利与现金毛利 evidence。
- 结算速度、回款速度绑定 S13 回款应收账龄与经营报表 evidence，同时因 authoritative window 不足标记人工复核。
- 审计偏差绑定 S13 跨表复核/差异队列 evidence，同时标记人工复核。
- 客情费率当前无 public-safe authoritative source mapping，标记人工复核。

## 公开仓库边界

- 只保存字段 ID、source lane ID、hash/ref/status、证据路径和门禁状态。
- 未写入 raw business data、zip、Excel、PDF、私有 CSV、SQLite/DB、字段明文、真实金额、真实客户/项目明细或凭证。
- `performance_fact_table_output_allowed=false`
- `abnormal_project_review_list_allowed=false`
- `salary_calculation_allowed=false`
- `bonus_approval_allowed=false`
- `payroll_export_allowed=false`
- `stage15_review_allowed=false`
- `github_upload_allowed=false`

## 产物

- `KMFA/tools/performance_fact_fields.py`
- `KMFA/tools/check_s15_p1_performance_fact_fields.py`
- `KMFA/tests/test_performance_fact_fields.py`
- `KMFA/metadata/reports/performance_fact_fields_manifest.json`
- `KMFA/metadata/reports/performance_fact_field_definitions.jsonl`
- `KMFA/metadata/reports/performance_fact_field_bindings.jsonl`
- `KMFA/metadata/reports/performance_fact_manual_review_fields.jsonl`
- `KMFA/stage_artifacts/S15_P1_performance_fact_fields/machine/s15_p1_manifest.json`
- `KMFA/stage_artifacts/S15_P1_performance_fact_fields/human/test_results.md`

## 结论

S15-P1 已完成本地 public-safe 实现与验证。下一步只能作为新 run work 执行 `S15-P2｜绩效复核清单`；不得直接进入 S15-P3、Stage 15 整体复审、GitHub upload、lineage full check、正式报告、工资计算、奖金审批、薪资导出或外部接口。
