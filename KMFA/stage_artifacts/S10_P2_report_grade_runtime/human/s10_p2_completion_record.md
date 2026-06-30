# S10-P2｜报告可信等级完成记录

## 结论

`S10-P2｜报告可信等级` 已完成本地验证。当前只锁定 public-safe 报告等级运行时证据，不生成正式经营报告，不执行导出，不执行 Stage 10 整体复审或 GitHub upload。

## 实现范围

- 新增 `KMFA/tools/report_grade_runtime.py`，基于 S10-P1 报告模板、S02-P3 报告等级门禁、S06-P3 data quality / zero-delta 状态和 S09-P3 reconciliation 状态生成报告可信等级记录。
- 新增 `KMFA/tools/check_s10_p2_report_grade_runtime.py`，验证等级记录、版本绑定、阻断规则、public-safe 边界和 S10-P3/export scope 均未开启。
- 新增 `KMFA/tests/test_report_grade_runtime.py`，覆盖 S10-P2 required reports、A/B/C/D 阻断、每个报告版本/公式/字段映射版本和 public-safe payload。
- 生成 `KMFA/metadata/reports/report_grade_runtime_manifest.json` 和 `KMFA/metadata/reports/report_grade_runtime_records.jsonl`。
- 生成 `KMFA/stage_artifacts/S10_P2_report_grade_runtime/machine/s10_p2_manifest.json`。

## 等级锁定

- 报告记录数: `2`
- 覆盖模板: `project_cost_special_report`, `business_overview_report`
- grade distribution: `D=2`
- source quality grade: `Q4`
- zero_delta_passed: `false`
- pending_reconciliation_count: `12`
- complete_trusted_report_display_allowed: `false`
- formal_report_allowed: `false`
- business_decision_basis_allowed: `false`
- export_artifact_count: `0`

## 阻断原因

每条报告等级记录均记录以下 hard blocks:

- `zero_delta_failed`
- `unresolved_critical_difference`
- `missing_required_lineage`
- `missing_human_confirmation_for_A`

因此缺关键数据、未关闭差异或缺人工确认时，不会显示为完整可信报告。

## 版本绑定

每条报告等级记录均绑定:

- `report_record_version`: `RPTREC-KMFA-S10P2-REPORT-GRADE-001`
- `template_version`: `TPL-KMFA-S10P1-REPORT-TEMPLATES-001`
- `template_content_hash`: 继承 S10-P1 report template manifest
- `formula_version`: `FORM-KMFA-S10P2-REPORT-GRADE-RUNTIME-001`
- `mapping_version`: `MAP-KMFA-S10P2-PUBLIC-SAFE-v1`
- `field_mapping_version`: `MAP-KMFA-S10P1-PUBLIC-SAFE-v1`
- `grade_policy_version`: `kmfa.report_grade_policy.v1`
- `release_gate_version`: `kmfa.report_release_gate.v1`

## Public-Safe 边界

- 未提交 raw business data。
- 未提交 zip、Excel、PDF、SQLite、private CSV 或字段明文。
- metadata 只保存等级、状态、hash/ref、版本、scope gate 和 evidence refs。
- 不关闭 S09-P3 pending owner/授权复核差异。
- 不生成 HTML、CSV、Excel 或 PDF 导出。
- 不执行 Stage 10 整体复审或 GitHub upload。

## 下一步

下一轮只允许执行 `S10-P3｜导出`。S10-P3 完成后，才能进入 Stage 10 整体复审；复审完成并修复 findings 后，才能执行 Stage 10 upload。
