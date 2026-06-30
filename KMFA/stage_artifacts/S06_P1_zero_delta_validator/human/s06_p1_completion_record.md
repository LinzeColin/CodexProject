# S06-P1 零差异校验器完成记录

## 范围

- Stage/Phase: `S06-P1`
- Task: `S6PAT01-S6PAT03`
- 目标: 实现 `zero_delta_validator`，对 public-safe 已结构化整数分字段进行逐字段零差异校验。

## 已完成

- 新增 `KMFA/tools/zero_delta_validator.py`。
- 新增 `KMFA/tests/test_zero_delta_validator.py`。
- 新增 public-safe synthetic fixture 和 synthetic mismatch evidence，用于证明任意 1 分差异失败并生成 mismatch report。

## 任务映射

- `S6PAT01`: 已实现 `validate_zero_delta`，按 `key_fields` 对齐记录，并逐字段比较 `amount_fields` 的整数分值。
- `S6PAT02`: 任意 1 分差异返回 `status=failed`、`zero_delta_passed=false`，CLI 失败退出并可写出 mismatch report。
- `S6PAT03`: mismatch report 字段包含 `source`、`field`、`authoritative_value_cents`、`system_value_cents`、`difference_cents`，并附带 public-safe `record_id`。

## 边界

- 只接受已结构化、公开安全的 fixture；不读取 Excel、PDF、zip、私有 CSV 或真实业务源文件。
- 只比较整数分，不使用 float；float、布尔值和非整数字符串输入会被拒绝。
- 不写入 `KMFA/metadata/quality/zero_delta_results.jsonl` 或 `KMFA/metadata/quality/mismatch_report.csv`，这些属于 S06-P3。
- 不创建跨源差异处理队列、不关闭差异、不改变报告等级、不做事实层、UI、正式报告或外部接口。
- 中间 Phase 不上传 GitHub。

## 回滚

- 删除 `KMFA/tools/zero_delta_validator.py`。
- 删除 `KMFA/tests/test_zero_delta_validator.py`。
- 删除 `KMFA/stage_artifacts/S06_P1_zero_delta_validator/`。
- 恢复 S06-P1 governance/status 记录为 planned。
