# TASK_REPORT · ADP-S2-P03-T028｜用 DuckDB 独立验证开放历史

## 唯一目标（达成）
用**独立开放引擎 DuckDB**（区别于写快照的 pyarrow）读取 T027 的本地 Parquet 快照，**在无 R2 SQL / 无 R2 Data Catalog / 无 Cloudflare** 的情况下重建关键文档、版本、事件与信号计数——证明恢复/分析路径**不被单一 Cloudflare Beta 能力锁死**。交付 DuckDB checks、sample queries、rebuild report。

## 六个开始前问题（已回答）
1. **唯一目标**：DuckDB 独立重建开放历史的关键计数；无 R2 SQL/Data Catalog 也成立。
2. **允许修改文件**：`docs/pursuing_goal/v0_1/tools/duckdb_verify.py` + 本证据包（rebuild_report / sample_queries / test-results / 报告）+ **T027 描述性 errata 更正**（cost_value/TASK_REPORT/known_gaps/SNAPSHOT_SPEC 的月份范围串 + T027 CHANGELOG 行；append-only T027 事件不改）+ 治理同步。
3. **绝不能改变**：抓取行为、六主题动效、worker、生产 D1/R2、cron；不改写既有生产数据；不臆造无数据支撑的信号。NOT_DEPLOYED。
4. **基线**：main `deac8a48`（T027 月度开放快照已合入）；输入 = committed T027 `logical_snapshot/*.jsonl`（可离线物化全 92 分区）。
5. **验收**：无 R2 SQL/Data Catalog 也能重建关键文档、版本、事件和信号计数。
6. **回滚**：`git revert <sha>`（离线工具，NOT_DEPLOYED，生产未变更）。

## 交付物
- `tools/duckdb_verify.py` —— 用 DuckDB `read_parquet()` 直读本地 Parquet（**无任何 Cloudflare 依赖**），以可移植 SQL 重建：关键文档数、版本数、逐月版本创建事件、关系完整性（0 孤儿）、信号（转载/多源、多版本、状态分布、覆盖月数、最早/最晚月）。
- `evidence/.../rebuild_report.json` —— DuckDB 重建结果。
- `evidence/.../sample_queries.sql` —— 重建用的可移植 SQL（DuckDB/Trino/Spark 通用）。

## 验收结果（实测，见 test-results/duckdb_tests.txt，ACCEPTANCE = PASS，exit 0）
- **独立物化 + 重建**：从 committed T027 logical jsonl 物化全 **92 个 Parquet 分区**，DuckDB 1.1.3 直读重建。
- **关键计数（无 Cloudflare）**：documents **498**（distinct canonical_id 498）、versions **500**、逐月版本事件按月与逻辑真值**逐一致**、**孤儿版本 0**（关系完整）、覆盖 **46 个月**、范围 **2016-01 → 2026-07**、信号 repost/多源 **1**、多版本文档 **1**、状态分布 {active:500}。
- **交叉核对**：DuckDB 重建的 docs/versions/events/signals/months 与 committed **T027 manifest 及 logical 真值全部一致**；最早月 = 2016-01 证明 **2016+ 历史在开放格式中可恢复**。
- **不锁死**：重建路径只读本地开放 Parquet——**无 R2 SQL、无 R2 Data Catalog、无 Cloudflare Beta**；同一 SQL 可搬到任意标准引擎。

## 独立校验的额外发现（errata，诚实记录 —— 这正是本任务的价值）
T028 的独立 DuckDB 重建**发现 T027 把月份范围末尾误写为 `2025-10`**；真实最大月为 **`2026-07`**（此前 T027 的 46 月计数、manifest.months 列表、全部 Parquet/logical 哈希与数据**一向正确**，仅少量人读“范围串”写错）。本提交已更正 T027 的 evidence/spec 文档与 T027 CHANGELOG 行；**append-only 的 T027 机器事件保持不可变**，以本 errata + T028 事件透明记录。独立引擎交叉验证按设计发挥了作用。

## Data / Performance / Visual
Data = DuckDB 对 92 分区的重建报告 + 可移植 SQL。无性能路径、无 UI 改动；六主题动效与线上 MVP 未触碰（NOT_DEPLOYED，离线只读）。

## Value / Cost（S2 Durable Evidence & Versioning）
- **Value**：开放历史**可被任意标准引擎重建**，恢复/分析不依赖 Cloudflare R2 SQL/Data Catalog（Beta）——即便这些 Beta 不可用或被撤，2016+ 历史与关键计数仍可从开放 Parquet 完整重建。
- **Cost（逐项，未知不填 0）**：新增请求 0；D1 读 0 / 写 0；R2 字节 0 / 操作 0；模型 0；人工维护 = 离线校验器，未接生产；开发依赖 duckdb（运行时不用）。经常性云成本 delta = $0/月。

## Known gaps
见 `known_gaps.md`：NOT_DEPLOYED（真实恢复演练归 T029）；新增开发依赖 duckdb（运行时不用，正是可移植性证明）；events/signals 按开放快照可支持口径重建、不臆造；计数级重建（字节级正文/附件恢复归 T029）；T027 范围 errata。

## 不适用证据项
`migration.sql/rollback.sql`、`screenshots-or-videos`、`benchmarks`、`deployment_manifest.preview.json` —— N/A。`data-samples` = rebuild_report.json + sample_queries.sql（快照数据在 T027 已提交）。

## 完成声明
```text
Task: ADP-S2-P03-T028
Commit: <记于提交步骤，见 changed_files.txt / git 历史>
Files changed: tools/duckdb_verify.py + T028 证据包 + T027 errata 更正（cost_value/TASK_REPORT/known_gaps/SNAPSHOT_SPEC + T027 CHANGELOG 行）+ 治理同步（见 changed_files.txt）
Tests: duckdb_tests.txt —— DuckDB 从开放 Parquet 重建 docs 498/versions 500/逐月事件/信号/0 孤儿/46 月/2016+，与 T027 manifest+logical 全一致，无 Cloudflare，ACCEPTANCE=PASS(exit 0)；治理门 lean_governance ci = SHIP（提交步骤）
Business evidence: DuckDB 独立重建开放历史（关键文档/版本/事件/信号），恢复路径不锁死于 Cloudflare Beta
Data/Performance/Visual: Data=rebuild_report+可移植 SQL；无性能/UI
Value: 开放历史可被任意标准引擎重建，2016+ 恢复不依赖 R2 SQL/Data Catalog
Cost: 请求0 / D1 0 / R2 0 / 模型 0；经常性成本 0；开发依赖 duckdb 运行时不用
Known gaps: 见 known_gaps.md（含 T027 范围 errata）
Deployment: NOT_DEPLOYED（离线只读开放快照）
Rollback: git revert <sha>（离线工具）
Verifier: 待独立上下文复核（实现者不自签 PASS）
```

**IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION**
