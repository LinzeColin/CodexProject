# Memory Atlas v1.2 S05 P3 Evidence Refs Review

## 结论

S05 P3 已完成。任务 ID 为 `MA-V12-S05P3`，验收 ID 为
`ACC-MA-V12-S05P3`，状态为
`phase_s05_p3_evidence_refs_completed_pending_s05_review`。

本 phase 将 canonical behavior events 升级为轻量 `evidence_refs` 模式。当前
`data/derived/behavior_intelligence/events.json` 包含 217 条 events 和 434 条
evidence_refs。每条 event 均保留 `source_id`、`record_id` 和至少一条 evidence ref，
证据引用指向 raw、manifest、derived 或 missing reason。

## 验收范围

- `scripts/extract_memory_atlas_facets.py` 生成 S05 P3 evidence contract。
- `scripts/atlasctl.py analyze --stage facets` 接入 S05 P3 输出。
- `data/derived/behavior_intelligence/events.json` 包含 `evidence_refs`。
- `validate:v1.2-s05-p3` 覆盖 extractor、events、文档、记录和边界。
- ChatGPT 和 Codex 事件来自真实已有 public raw、processed manifest 或 derived 输入。
- future_agent 当前无 public raw，只保留 missing reason，不生成 fake event。

## 边界

- No fake events。
- No raw mutation in this phase。
- No GitHub main upload in this phase。
- No remote push in this phase。
- No Raw-to-Insight Replay UI in this phase。
- No app reinstall in this phase。

## 下一步

下一步只允许进入 S05 Review。S05 Review 前不得进入 S06，不得上传 GitHub main，
不得把本地开发分支推送到远端。
