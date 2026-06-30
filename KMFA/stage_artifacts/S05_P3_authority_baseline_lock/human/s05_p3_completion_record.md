# S05-P3 权威基准锁定完成记录

## 范围

- Stage/Phase: `S05-P3`
- Task: `S5PCT01-S5PCT03`
- 目标: 基于 S05-P1 A0 文件登记、S05-P2 字段候选与 active owner/授权降级决策，建立 public-safe A0 权威基准锁定证据。

## 已完成

- 新增 `KMFA/tools/a0_authority_baseline_lock.py`，从 S05-P2 A0 golden fixture candidates 和 active owner/授权降级决策生成 S05-P3 权威基准锁定 metadata。
- 新增 `KMFA/tools/check_a0_authority_baseline_lock.py`，验证 S05-P3 manifest、field lock records、content hash、Q4/Q5 lock 边界、排除记录和公开仓库安全边界。
- 新增 `KMFA/tests/test_s05_p3_authority_baseline_lock.py`，覆盖 public-safe Q5 lock、Excel downgrade exclusion、禁止明文键和文件输出。
- 新增 `KMFA/metadata/baseline/a0_authority_baseline_manifest.json`，锁定 baseline version、content hash、确认角色、确认时间和计数。
- 新增 `KMFA/metadata/baseline/a0_authority_baseline_records.jsonl`，记录 45 条 authority baseline field lock/exclusion 记录。

## 锁定结果

- `q5_locked_field_count`: `40`
- `excluded_field_count`: `5`
- `authority_records`: `45`
- `baseline_version`: `KMFA-A0-Q5-20260630-S05P3-PUBLIC-SAFE-HASH-LOCK`
- `baseline_content_hash`: `sha256:dbb55ffb4e3608e49dbcf91e97fc0f19395a8269ff7c8f4d5c3f8ca398c03670`
- Excel candidate `A0-CAND-70023EFC7305` 依据 S05-P2 active owner/授权降级决策排除为 `cross_source_support_only`，不进入 Q5 calculation baseline。

## 边界

- S05-P3 只锁定 hash/source-anchor 完整的 40 条 PDF 字段记录。
- S05-P3 不提交合同额、支出合计、毛利、毛利率、成本分类明文。
- S05-P3 不提交 `销售绩效考核.zip`、`财务.zip`、PDF、Excel、私有 CSV 或解包文件。
- S05-P3 不生成正式报告，不执行 zero-delta，不建立事实层，不做 UI，不上传 GitHub。
- `formal_report_allowed=false`，因为 Stage 5 review、zero-delta、lineage 和报告发布门禁尚未完成。

## 任务映射

- `S5PCT01`: 已将 40 条 public-safe hash/source-anchor 完整字段升级为 Q5 calculation baseline allowed；未确认/被降级字段不进入 Q5。
- `S5PCT02`: 已锁定 baseline version、content hash、authorized delegate、锁定时间和证据引用。
- `S5PCT03`: 已用 5 条 exclusion records 明确未确认 Excel 字段不得用于正式报告。

## 回滚

- 删除 `KMFA/tools/a0_authority_baseline_lock.py`
- 删除 `KMFA/tools/check_a0_authority_baseline_lock.py`
- 删除 `KMFA/tests/test_s05_p3_authority_baseline_lock.py`
- 删除 `KMFA/metadata/baseline/a0_authority_baseline_manifest.json`
- 删除 `KMFA/metadata/baseline/a0_authority_baseline_records.jsonl`
- 删除 `KMFA/stage_artifacts/S05_P3_authority_baseline_lock/`
- 恢复 S05-P3 governance/status 记录为 planned。
