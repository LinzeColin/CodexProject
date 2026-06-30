# S07-P1 财务文件适配完成记录

## 范围

- phase: `S07-P1｜财务文件适配`
- taskpack: `KMFA/taskpack/v1_2/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_2.md`
- 执行时间: `2026-06-30T16:00:00+10:00`
- 状态: `completed_validated_local_only`

## 已完成

- 建立财务支撑源文件登记：`KMFA/metadata/imports/finance_support_source_registry.json`
- 建立字段候选映射：`KMFA/metadata/schema_maps/finance_field_candidates.jsonl`
- 建立财务适配 manifest：`KMFA/metadata/schema_maps/finance_file_adapter_manifest.json`
- 输出只读字段报告：`KMFA/stage_artifacts/S07_P1_finance_file_adapter/machine/finance_readonly_field_report.jsonl`
- 新增工具与 validator：
  - `KMFA/tools/finance_file_adapter.py`
  - `KMFA/tools/check_s07_p1_finance_file_adapter.py`
  - `KMFA/tests/test_finance_file_adapter.py`

## 覆盖类别

S07-P1 已覆盖 9 类财务支撑源：`operating_analysis`、`journal`、`customer_aging`、`cash`、`tax`、`invoice`、`account`、`loan`、`r_and_d_expense`。

每类文件输出一个只读解析字段报告；本 phase 的公开证据只保存 `file_hash`、`source_ref`、`source_header_hash`、`source_header_private_ref`、canonical field key、质量状态和证据引用。

## 公开仓库安全边界

- 未提交 raw business data、zip、Excel、PDF、私有 CSV、银行流水、合同、薪资、税务申报或 credentials。
- 未提交来源表头明文；字段候选只保存 hash 和 private refs。
- 未写入 raw layer；所有登记均为 metadata/stage evidence。
- 未进入 WPS 文件适配、红圈导出策略、事实层、lineage、UI、正式报告或自动接口。
- `formal_report_allowed=false`，`q5_calculation_baseline_allowed=false`，后续下游使用需等待 Stage 7 完整复审。

## 回滚

如需回滚 S07-P1，本地删除以下新增文件，并恢复中文入口与 governance 状态到 S06 upload 后：

- `KMFA/tools/finance_file_adapter.py`
- `KMFA/tools/check_s07_p1_finance_file_adapter.py`
- `KMFA/tests/test_finance_file_adapter.py`
- `KMFA/metadata/imports/finance_support_source_registry.json`
- `KMFA/metadata/schema_maps/finance_file_adapter_manifest.json`
- `KMFA/metadata/schema_maps/finance_field_candidates.jsonl`
- `KMFA/stage_artifacts/S07_P1_finance_file_adapter/`

## 下一步

下一轮只执行 `S07-P2｜WPS 文件适配`。不得在下一轮跳到红圈、事实层、lineage、UI、正式报告、自动接口或 Stage 7 整体复审。
