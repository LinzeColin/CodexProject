# S09-P2 毛利与现金毛利完成记录

- project_id: `KMFA`
- stage_phase: `S09-P2`
- task_ids: `S9PBT01-S9PBT03`
- completed_at: `2026-06-30T23:45:00+10:00`
- status: `completed_validated_local_only`
- github_upload_performed: `false`

## 完成范围

- 建立 public-safe 毛利与现金毛利计算层。
- 用整数分和 basis points 定义系统复算毛利、现金毛利和毛利率计算合同。
- 保留 A0 Q5 authority display value refs/hash 与 S09-P2 system recomputed refs/hash，禁止互相覆盖。
- 将 authority/system/cash 口径差异写入 `KMFA/metadata/quality/scope_difference_summary.jsonl`。

## 输出

- `KMFA/tools/project_margin_cash_margin.py`
- `KMFA/tools/check_s09_p2_margin_cash_margin.py`
- `KMFA/tests/test_project_margin_cash_margin.py`
- `KMFA/metadata/reports/project_margin_cash_margin_manifest.json`
- `KMFA/metadata/lineage/project_margin_cash_margin_records.jsonl`
- `KMFA/metadata/quality/scope_difference_summary.jsonl`
- `KMFA/stage_artifacts/S09_P2_margin_cash_margin/machine/s09_p2_manifest.json`

## 边界

- 不提交 raw business data、zip、Excel、PDF、private CSV、字段明文或真实业务值。
- 不覆盖权威显示值，也不用系统复算值替代权威值。
- 不执行 S09-P3 口径转换与差异核对。
- 不执行 Stage 9 整体复审。
- 不执行 lineage full check、正式报告、UI、外部接口或 GitHub upload。

## 风险与剩余问题

- S06/S08 未关闭的质量阻断仍然保留，正式报告仍不允许。
- S09-P2 只将差异进入摘要；差异原因、依据、责任人和处理状态的人类可读核对留给 S09-P3。

## 回滚

- 删除 S09-P2 新增工具、测试、metadata 输出和 `KMFA/stage_artifacts/S09_P2_margin_cash_margin/`。
- 从 governance registry、stage_status 和事件日志中移除本次 S09-P2 append-only 草案记录。
