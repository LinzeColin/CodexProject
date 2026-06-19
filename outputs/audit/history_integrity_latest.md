# 历史完整性审计

- 状态：pass
- 生成时间：2026-06-14T10:37:29+08:00
- 基线文件：`/Users/linzezhang/Documents/Codex/2026-06-12/codex-dev-automation-using-model-5/outputs/audit/history_integrity_baseline.json`
- 报告/文件时间线：`/Users/linzezhang/Documents/Codex/2026-06-12/codex-dev-automation-using-model-5/outputs/audit/history_artifact_timeline.csv`
- 快照表时间线：`/Users/linzezhang/Documents/Codex/2026-06-12/codex-dev-automation-using-model-5/outputs/audit/history_snapshot_table_timeline.csv`
- SQLite 保护表：21
- SQLite 保护行：15239
- 历史文件：142
- 违规数：0

## 规则

- 允许新增新的运行、新的快照、新的报告和新的通知记录。
- 不允许修改、删除或覆盖已经进入基线的历史行和历史文件。
- UI、报告模板、策略逻辑和功能迭代只能生成新的事实，不得重写旧事实。

## 违规

- None
