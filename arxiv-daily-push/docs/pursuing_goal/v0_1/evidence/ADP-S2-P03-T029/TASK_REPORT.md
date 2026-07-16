# TASK_REPORT · ADP-S2-P03-T029｜执行备份恢复与生命周期演练

## 唯一目标（达成）
证明 **2016 月 / 2020 月 / 当前月**都可从**开放永久证据**（T027 月度快照 + 永久原始官方 artifact）恢复到**隔离副本**，随机正文/附件/关系/计数一致；明确**永久 vs 可再生**数据，且**原始官方证据与已发布版本不得删除**。交付 restore runbook、isolation restore、retention matrix、result hashes。

## 六个开始前问题（已回答）
1. **唯一目标**：备份恢复 + 生命周期演练；三个代表月可恢复、随机正文/附件/关系/计数一致、永久类零删除。
2. **允许修改文件**：`docs/pursuing_goal/v0_1/{tools/restore_drill.py, RESTORE_RUNBOOK.md, RETENTION_MATRIX.md}` + 本证据包（raw_evidence_sample / restore_report / test-results / 报告）+ 治理同步。
3. **绝不能改变**：抓取行为、六主题动效、worker、生产 D1/R2、cron；**不改写既有生产数据**；不删除原始官方证据/发布版本。恢复只进**一次性内存 SQLite**。NOT_DEPLOYED。
4. **基线**：main `e0a00054`（T028 已合入）；永久源 = committed T027 `logical_snapshot/*.jsonl` + 本任务 `raw_evidence_sample.json`（3 目标月 7 条真实抽样）。
5. **验收**：随机正文/附件/关系/计数一致；原始官方证据和发布版本不得删除。
6. **回滚**：隔离库丢弃即回滚；`git revert <sha>`（离线工具，生产未变更）。

## 交付物
- `tools/restore_drill.py` —— 按月从开放快照恢复 docs+versions 到隔离 SQLite（套 T025 schema），**引用闭包**保证 0 孤儿；链接原始 artifact；校验计数/关系/随机正文/随机附件；`RETENTION_MATRIX`（永久 vs 可再生）；永久源只读 + 永久类零删除；每月 result hash。
- `RESTORE_RUNBOOK.md` —— 可复现恢复流程 + 跨月引用闭包设计点。
- `RETENTION_MATRIX.md` —— 永久（原始官方 artifact / 已发布版本 / canonical 身份）vs 可再生（factsheet / 人话版 / 快照 / 索引）。
- `evidence/.../restore_report.json` + `raw_evidence_sample.json`（永久原始证据抽样）。

## 验收结果（实测，见 test-results/restore_tests.txt，ACCEPTANCE = PASS，exit 0）
- **三个代表月可恢复**：**2016-01**（1 文档 / 1 版本）、**2020-07**（1 文档 / 1 版本）、**当前月 2026-07**（326 月文档 / 327 版本 / 327 含闭包文档）——全部恢复到隔离库。
- **计数一致**：每月恢复的版本数 = 快照该月分区数、月文档数 = 快照该月文档分区数。
- **关系一致**：隔离库 **孤儿版本 = 0**（引用闭包修复后）。
- **随机正文一致**：7 条抽样按 T026 引擎从原始 body 重算 content_hash → **全部匹配**恢复的版本 content_hash。
- **随机附件一致**：7 条抽样重算 `sha256(url)` artifact key → **全部命中**恢复版本的 `artifact_keys_json`。
- **原始官方证据/发布版本不得删除**：retention matrix 标原始 artifact + 已发布版本 + canonical 身份为 **PERMANENT/never**；演练**永久源 sha256 逐字不变**、**永久类删除数 = 0**、**生产 D1/R2 未触碰**（隔离内存 SQLite）。

## 实现中发现并加固的真实问题
**单月孤立恢复会孤立跨月版本**：某文档首见于早月、却在 2026-07 产生新版本；只恢复 2026-07 会得到该版本但缺其父文档 → 1 孤儿。**修复**：恢复改为**引用闭包**——随每个版本拉入其父文档（跨分区，`INSERT OR IGNORE`）→ **0 孤儿**。这是月度分区恢复的关键正确性点，已写入 runbook。

## Data / Performance / Visual
Data = 3 月恢复报告 + result hashes + 7 条原始证据抽样。无性能路径、无 UI 改动；六主题动效与线上 MVP 未触碰（NOT_DEPLOYED，隔离恢复）。

## Value / Cost（S2 Durable Evidence & Versioning）
- **Value**：2016+ 历史**可真实恢复**（不只归档）：早期/2020/当前稠密月都能从开放永久证据重建，正文/附件/关系/计数一致；保留策略保证原始官方原文与发布版本永不丢。
- **Cost（逐项，未知不填 0）**：新增请求 0；D1 读 0 / 写 0；R2 字节 0 / 操作 0；模型 0；人工维护 = 离线演练，未接生产。经常性云成本 delta = $0/月。

## Known gaps
见 `known_gaps.md`：NOT_DEPLOYED（未接备用 D1）；原始 artifact 用抽样占位（全量在 R2）；样本量小但覆盖三类月；跨月闭包已加固；未含 selections/lessons；保留策略为策略层非运行时闸门。

## 不适用证据项
`migration.sql/rollback.sql`（复用 T025 schema）、`screenshots-or-videos`、`benchmarks`、`deployment_manifest.preview.json` —— N/A。`data-samples` = restore_report.json + raw_evidence_sample.json。

## 完成声明
```text
Task: ADP-S2-P03-T029
Commit: <记于提交步骤，见 changed_files.txt / git 历史>
Files changed: tools/restore_drill.py + RESTORE_RUNBOOK.md + RETENTION_MATRIX.md + T029 证据包（raw_evidence_sample/restore_report/test-results/报告）+ 治理同步（见 changed_files.txt）
Tests: restore_tests.txt —— 2016/2020/当前月恢复 + 计数/关系(0孤儿)/随机正文7/7/随机附件7/7 一致 + 永久类零删除/永久源不变/隔离，ACCEPTANCE=PASS(exit 0)；治理门 lean_governance ci = SHIP（提交步骤）
Business evidence: 备份恢复+生命周期演练（三代表月可恢复、永久类不删）
Data/Performance/Visual: Data=恢复报告+result hashes；无性能/UI
Value: 2016+ 历史可真实恢复，原始官方证据/发布版本永不丢
Cost: 请求0 / D1 0 / R2 0 / 模型 0；经常性成本 0；隔离恢复未触生产
Known gaps: 见 known_gaps.md
Deployment: NOT_DEPLOYED（隔离内存 SQLite 恢复）
Rollback: 丢弃隔离库 / git revert <sha>
Verifier: 待独立上下文复核（实现者不自签 PASS）
```

**IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION**
