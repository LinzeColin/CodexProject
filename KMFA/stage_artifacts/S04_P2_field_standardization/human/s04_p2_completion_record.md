# S04-P2 字段标准化完成记录

更新时间: 2026-06-29

## 范围

- Stage: `S04｜金额精度、字段标准化与基础工具`
- Phase: `S04-P2｜字段标准化`
- Task: `S4PBT01-S4PBT03`
- 状态: `completed_validated_local_only`
- GitHub 上传: `not_allowed_until_stage4_review`

## 已完成

- 新增 `KMFA/tools/field_standardization.py`，支持字段别名解析、日期 `YYYY-MM-DD`、期间 `YYYY-MM`、公司主体、项目名称、客户/对手方、合同编号标准化。
- 新增 `KMFA/metadata/schema_maps/field_alias_dictionary.csv`，登记通用中文字段别名和 canonical field 映射。
- 新增 `KMFA/metadata/schema_maps/field_standardization_policy.yaml`，登记缺字段不得静默跳过、只写 metadata 质量状态、不写 raw 层的策略。
- 新增 `KMFA/metadata/quality/field_quality_status.jsonl` 协议 header，缺字段和无效字段只记录 metadata 质量状态。
- 更新 `KMFA/metadata/schema_maps/source_mapping_versions.yaml`，登记 S04-P2 通用 mapping version，不保存业务行或原始值。
- 新增 `KMFA/tests/test_field_standardization.py`，覆盖中文字段映射、日期/期间/主体/项目/客户/合同标准化、缺字段质量状态、异常字段质量状态和 CLI。

## 非范围

- 不解析或提交真实业务源数据。
- 不建立 A0 黄金基准。
- 不实现 zero-delta、事实层、报告、UI 或外部接口。
- 不执行 Stage 4 复审或 GitHub 上传。

## 验收

- `S4PBT01`: 标准化日期、期间、公司主体、项目名称、客户/对手方、合同编号。
- `S4PBT02`: 建立字段别名字典和中文字段映射。
- `S4PBT03`: 字段缺失进入质量状态，不静默跳过。

## 风险边界

- `standardize_record` 可在本地运行时输出标准化字段值；公开仓库只提交代码、策略、通用字段字典和合成测试，不提交真实业务值。
- 缺字段或异常字段只进入 `field_quality_status` metadata，`field_skipped_silently=false`。
- S04-P2 完成后 Stage 4 仍未完成；下一步只能执行 `S04-P3｜基础工具测试`。
