# Restore Runbook · ADP-S2-P03-T029

从**开放、永久证据**（T027 月度快照 + 永久原始官方 artifact）把任一月份**恢复到隔离副本**的可复现流程，
证明 2016 月 / 2020 月 / 当前月都可恢复，且**永不删除原始官方证据与已发布版本**。工具：`tools/restore_drill.py`。
**NOT_DEPLOYED**——恢复目标是**内存中的一次性 SQLite**（套用 T025 schema），**绝不触碰生产 D1/R2**。

## 前置

- **永久源（read-only）**：
  - 版本/文档记录 = T027 开放快照（`evidence/ADP-S2-P03-T027/logical_snapshot/*.jsonl` 或其 Parquet 分区）。
  - 原始官方 artifact = R2 内容寻址原文（本演练用 `evidence/ADP-S2-P03-T029/raw_evidence_sample.json` 作永久原始证据抽样）。
- 恢复引擎独立可移植（SQLite / DuckDB / D1 均可套 T025 schema）。

## 步骤

1. **建隔离库**：内存 SQLite，先建 `cn_meta`（模拟既有生产元表），再套 `schemas/document_version.migration.sql`（T025）。
2. **按月恢复（含引用闭包）**：对目标月，载入该月的 `cn_document_versions` 分区；**并对每个版本的父文档做引用闭包**——
   即使该文档的 `first_seen_month` 在更早分区，也一并拉入其 `cn_documents` 行（否则跨月版本链会把晚出现的版本孤立）。
   同时载入该月自身的文档分区。用 `INSERT OR IGNORE` 保证多月共享文档不重复。
3. **链接原始 artifact**：对抽样的原始证据，按 T024 身份定位 canonical_id，重算 `sha256(url)` 作 artifact key，写入对应版本的 `artifact_keys_json`。
4. **校验**（见验收）：计数、关系（0 孤儿）、随机正文（重算 content_hash 匹配）、随机附件（artifact key 命中）、结果哈希。
5. **保留策略校验**：演练**只写隔离库、只读永久源**；恢复前后对永久源文件做 sha256，必须**逐字不变**；对永久类**零删除**。

## 关键设计点（本演练发现并加固）

- **跨月引用闭包**：单月孤立恢复会把「文档首见于早月、却在目标月产生新版本」的版本**孤立**。恢复**必须引用闭包**：随版本拉入其父文档（跨分区）。本演练在 2026-07 命中该情形（+1 闭包文档），修复后 **0 孤儿**。
- **永久 vs 可再生**：见 `RETENTION_MATRIX.md`。恢复只重建**可再生视图**；**永久类（原始官方 artifact + 已发布版本 + canonical 身份）永不删除**。

## 回滚

隔离库是一次性内存对象，丢弃即回滚；生产从未变更。工具回滚 `git revert <sha>`。
