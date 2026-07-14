# KMFA v0.1.3 S01-P1 阻塞清单

## 读取范围

- `KMFA/stage_artifacts/S18_STAGE_REVIEW/`
- `KMFA/stage_artifacts/S18_GITHUB_UPLOAD/`
- `KMFA/stage_artifacts/LINEAGE_REPORT_GATE/`
- `KMFA/stage_artifacts/S09_P3_scope_reconciliation/`
- `KMFA/metadata/quality/lineage_report_release_gate_review.json`
- `KMFA/metadata/quality/scope_reconciliation_records.jsonl`
- `KMFA/metadata/reports/report_grade_runtime_records.jsonl`
- `KMFA/metadata/lineage/field_lineage.jsonl`
- `KMFA/metadata/lineage/metric_lineage.jsonl`
- `KMFA/metadata/lineage/report_lineage.jsonl`

## 阻塞明细

| ID | 类型 | 当前状态 | 影响 | 后续 Roadmap |
|---|---|---|---|---|
| `B-V013-S01P1-001` | Lineage | field/metric/report lineage 只有 protocol header，actual rows = 0 | 阻断完整 lineage full check、正式报告、经营决策依据 | S04 |
| `B-V013-S01P1-002` | Reconciliation | S09-P3 仍有 12 条 pending owner/authorized review | 阻断派生重跑、报告等级提升、正式报告 | S03 |
| `B-V013-S01P1-003` | Report grade | 2 条 report grade runtime 均为 D | 阻断完整可信报告显示、正式发布、经营决策依据 | S05 |
| `B-V013-S01P1-004` | Release flags | delivery/formal report/business execution 均为 false | 只能继续修复，不能对外发布或执行业务动作 | S01-P3, S10 |
| `B-V013-S01P1-005` | Version state | `KMFA/VERSION` 尚未进入 v0.1.3 | 需要后续 scope freeze 和封版阶段统一处理 | S01-P2, S10 |

## 禁止误判

- Stage 18 upload 只代表 public-safe GitHub backup，不代表 delivery。
- S10 HTML/CSV preview 只代表 D 级预览，不代表正式报告。
- S00 app entry 只代表本机入口可打开，不代表业务系统可用。
