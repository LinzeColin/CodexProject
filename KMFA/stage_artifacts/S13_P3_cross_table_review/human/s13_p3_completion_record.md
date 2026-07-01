# S13-P3｜跨表复核完成记录

## 目标

基于已完成的 S13-P1 财务经营报表初稿和 S13-P2 回款应收账龄草案，完成 public-safe 跨表复核：

- 项目一致性检查
- 客户一致性检查
- 金额一致性检查
- 时间一致性检查
- 不一致进入人工差异队列
- 输出经营报表质量报告

## 本地输出

| 类型 | 文件 |
|---|---|
| runtime | `KMFA/tools/cross_table_review.py` |
| validator | `KMFA/tools/check_s13_p3_cross_table_review.py` |
| test | `KMFA/tests/test_cross_table_review.py` |
| manifest | `KMFA/metadata/reports/cross_table_review_manifest.json` |
| review checks | `KMFA/metadata/reports/cross_table_review_checks.jsonl` |
| difference queue | `KMFA/metadata/reports/cross_table_difference_queue.jsonl` |
| quality report | `KMFA/metadata/reports/operating_report_quality_report.json` |
| HTML evidence | `KMFA/stage_artifacts/S13_P3_cross_table_review/exports/html/cross_table_quality_report.html` |
| stage manifest | `KMFA/stage_artifacts/S13_P3_cross_table_review/machine/s13_p3_manifest.json` |

## 结果

- `review_dimension_count=4`
- `difference_queue_count=4`
- `quality_report_count=1`
- `pending_reconciliation_count=12`
- `report_grade_visible=D`
- `formal_report_allowed=false`
- `business_decision_basis_allowed=false`
- `difference_auto_resolution_allowed=false`
- `stage13_review_allowed=false`
- `github_upload_allowed=false`

## 边界

S13-P3 不提交 raw business data、zip、Excel、PDF、私有 CSV、字段明文、真实金额、真实客户/项目明细、真实账号或 credentials。

本 phase 不执行 Stage 13 整体复审、GitHub upload、lineage full check、正式报告、差异关闭、外部接口、开票、付款、银行、税务或法务催收动作。

## 下一步

Stage 13 三个 phase 均已本地完成。下一轮应执行 Stage 13 整体复审，复跑 S13-P1/P2/P3 validators、治理 validator、raw/secret scan、parse checks，修复 findings 后才能进入 final GitHub upload。
