# S06-P3 校验证据输出完成记录

## 范围

- Stage/Phase: `S06-P3`
- Task: `S6PCT01-S6PCT03`
- 目标: 将 S06-P1/S06-P2 的 public-safe 校验结果输出为 stage evidence，并写入 `KMFA/metadata/quality` 公开安全证据面。

## 已完成

- 新增 `KMFA/tools/validation_evidence_output.py`。
- 新增 `KMFA/tools/check_s06_p3_validation_evidence.py`。
- 新增 `KMFA/tests/test_validation_evidence_output.py`。
- 新增 `KMFA/stage_artifacts/S06_P3_validation_evidence_output/machine/zero_delta_result.json`。
- 新增 `KMFA/stage_artifacts/S06_P3_validation_evidence_output/machine/mismatch_report.csv`。
- 新增 `KMFA/stage_artifacts/S06_P3_validation_evidence_output/machine/project_validation_status.jsonl`。
- 将 S06-P3 public-safe 结果写入 `KMFA/metadata/quality/zero_delta_results.jsonl`、`data_quality_results.jsonl`、`source_difference_queue.jsonl` 和 `mismatch_report.csv`。

## 任务映射

- `S6PCT01`: 输出 S06-P3 `zero_delta_result.json` 和 sanitized `mismatch_report.csv`；stage artifact 不 inline mismatch 详情。
- `S6PCT02`: 输出每个 synthetic project ref 的 validation status，包含 `blocked`、`quality_grade=Q4`、`q5_allowed=false` 和 A 级报告阻断状态。
- `S6PCT03`: 将 zero-delta summary、project quality status、source difference queue status 和 sanitized mismatch index 写入 `metadata/quality`。

## 边界

- 只消费 S06-P1/S06-P2 已存在的 public-safe synthetic evidence；不读取真实 Excel、PDF、zip、私有 CSV 或业务源文件。
- `metadata/quality` 只保存 hash/ref/status/evidence；不新增字段明文、权威原值、系统原值、PDF 原值或 Excel 原值。
- 不关闭差异、不自动修正、不平均、不四舍五入掩盖、不自动选边。
- 未关闭差异和零差异失败仍阻断 A 级报告；本 phase 不生成正式报告、不实现事实层、lineage 完整检查、UI、外部接口、Stage 6 复审或 GitHub upload。

## 回滚

- 删除 `KMFA/tools/validation_evidence_output.py`。
- 删除 `KMFA/tools/check_s06_p3_validation_evidence.py`。
- 删除 `KMFA/tests/test_validation_evidence_output.py`。
- 删除 `KMFA/stage_artifacts/S06_P3_validation_evidence_output/`。
- 从 `KMFA/metadata/quality/*.jsonl` 和 `KMFA/metadata/quality/mismatch_report.csv` 移除 `S06-P3` public-safe synthetic records。
- 恢复 S06-P3 governance/status 记录为 planned。
