# TASK_REPORT · ADP-S2-P03-T027｜生成 Monthly Parquet Snapshot 与 Manifest

## 唯一目标（达成）
把 CanonicalDocument（T024）+ DocumentVersion 版本链（T026）导出为**按月分区的开放列式快照（真实 Apache Parquet）+ manifest + hash**，为大规模历史分析、恢复与可回测预测提供开放格式。交付 partition writer、schema evolution、snapshot manifest、hash。

## 六个开始前问题（已回答）
1. **唯一目标**：月度分区开放快照（Parquet）+ manifest + hash；同一 logical snapshot 可重复生成、D1 抽样与 Parquet 行/关系一致。
2. **允许修改文件**：`docs/pursuing_goal/v0_1/{tools/snapshot_writer.py, SNAPSHOT_SPEC.md, schemas/snapshot_manifest.schema.json}` + 本证据包（manifest / logical_snapshot / sample_partitions / test-results / 报告）+ 治理同步。
3. **绝不能改变**：抓取行为、六主题动效、worker、生产 D1（adp-mirror）、R2、cron。**离线从 D1 抽样生成，NOT_DEPLOYED，未接生产读写**。
4. **基线**：main `63629f16`（T026 版本 Diff/噪声/replay 已合入）；建立在 T024 身份 + T026 版本链之上。真实抽样 = scratchpad/t020/{items_500.json, fs_500.json}（500 条真实 cn_items）。
5. **验收**：同一 logical snapshot 可重复生成；D1 抽样和 Parquet 行/关系一致。
6. **回滚**：`git revert <sha>`（纯离线工具/规则，NOT_DEPLOYED，生产未变更）。

## 交付物
- `tools/snapshot_writer.py` —— 从 D1 抽样经 T024 canonicalize + T026 version_engine 派生 `cn_documents` / `cn_document_versions` 两张逻辑表，**按月分区**；`logical_hash`（格式无关可重复锚点）；**真实 Parquet 写出**（pyarrow，compression none / stats off / v2.6；同环境字节确定）+ **NDJSON 确定性回退**（相同 logical_hash）；版本化 `SCHEMA_REGISTRY` + `evolve_schema`（加可空列向后兼容）；`snapshot_manifest`。
- `SNAPSHOT_SPEC.md` + `schemas/snapshot_manifest.schema.json` —— 分区/哈希/演进/manifest 规范与结构契约。
- `evidence/.../snapshot_manifest.json`（92 分区，logical+physical 哈希）+ `logical_snapshot/*.jsonl`（498+500 行，可离线重算全部 logical_hash）+ `sample_partitions/*.parquet`（2 个真实样例，PAR1）。

## 验收结果（实测，见 test-results/snapshot_tests.txt，ACCEPTANCE = PASS，exit 0）
- **规模（真实 500 抽样）**：**498 canonical docs / 500 versions / 46 个月（2016-01…2026-07）/ 92 分区**（2 表 × 46 月）；format=parquet，engine=pyarrow 17.0.0。（注：本行月份范围末尾曾误写为 2025-10，由 T028 DuckDB 独立校验发现并更正为真实的 2026-07；46 个月计数与全部哈希/数据一向正确。）
- **同一 logical snapshot 可重复生成**：连两次生成 → `snapshot_id` 相等、每分区 `logical_hash` 相等、同环境 `physical_sha256` 亦相等。
- **D1 抽样 ↔ Parquet 行/关系一致**：回读全部 Parquet 分区 → cn_documents 行 **498 == 抽样派生 498**、cn_document_versions 行 **500 == 抽样派生 500**、每个 version.canonical_id **全部** ∈ documents.canonical_id（**孤儿 0**）、每行落在正确月分区。
- **Schema 演进向后兼容**：v1→v2 追加可空列 `authority` → 旧 v1 分区在 v2 schema 下可读（新列 **null 填充**）、v1 分区 `logical_hash` **稳定不变**。
- **证据自洽**：committed `logical_snapshot/*.jsonl` 离线重算出 manifest **全部 92 个 logical_hash**（无需 pyarrow / 原始抽样）；manifest 通过 `snapshot_manifest.schema.json` 校验，负例（month `2016/01`）正确 INVALID；样例 parquet PAR1 魔数、pyarrow 可读（1 行 / 43 行）。

## 实现说明（诚实记录）
- 500 版本 vs 498 文档：2 条**改写转载**（同 canonical_id、不同 summary）经 T026 版本引擎正确形成 2 段真实多版本链——真数据上顺带验证了多版本逻辑。
- 环境无 pyarrow/pandas/fastparquet，为忠实产出**真实 Parquet** 安装了 `pyarrow==17.0.0`（标准参考实现）到用户 Python 3.9 user-site；**这是离线证据依赖，运行时/worker 不用**；无 pyarrow 时自动 NDJSON 回退且 logical_hash 一致。已在 cost/known_gaps 登记。

## Data / Performance / Visual
Data = 真实 500 抽样导出的 92 个月度分区（样例 2 个 parquet 已提交）。无性能路径、无 UI 改动；六主题动效与线上 MVP 未触碰（NOT_DEPLOYED，离线生成）。

## Value / Cost（S2 Durable Evidence & Versioning）
- **Value**：开放、按月分区、可被生态直接读取的列式历史快照，可重复（logical_hash 锚点）、与 D1 一致、支持 schema 演进——为 2016+ 大规模历史分析、恢复与可回测预测提供地基（S2-P03 首块）。
- **Cost（逐项，未知不填 0）**：新增请求 0；D1 读 0 / 写 0；R2 字节 0 / 操作 0；模型 0；人工维护 = 离线快照器，未接生产；开发依赖 pyarrow（运行时不用）。经常性云成本 delta = $0/月。

## Known gaps
见 `known_gaps.md`：NOT_DEPLOYED（未接生产 D1/R2，真实月度快照落 R2 归后续）；新增开发依赖 pyarrow（运行时不用/有 NDJSON 回退）；物理字节跨引擎不保证一致（锚 logical_hash）；抽样非全量；仅两张表；committed 仅 2 个样例 parquet。

## 不适用证据项
`migration.sql/rollback.sql`（沿用 T025 schema，本任务无 D1 schema 变更）、`screenshots-or-videos`、`benchmarks`、`deployment_manifest.preview.json` —— N/A。`data-samples` = snapshot_manifest.json + logical_snapshot/*.jsonl + sample_partitions/*.parquet。

## 完成声明
```text
Task: ADP-S2-P03-T027
Commit: <记于提交步骤，见 changed_files.txt / git 历史>
Files changed: tools/snapshot_writer.py + SNAPSHOT_SPEC.md + schemas/snapshot_manifest.schema.json + 证据包（snapshot_manifest/logical_snapshot/sample_partitions/test-results/TASK_REPORT/cost_value/known_gaps/commands.log/changed_files/git.diff）+ 治理同步（见 changed_files.txt）
Tests: snapshot_tests.txt —— 可重复(snapshot_id/logical_hash/physical 全等) + D1↔Parquet(498/500行/0孤儿/月分区正确) + schema演进向后兼容 全通过，ACCEPTANCE=PASS(exit 0)；manifest schema 校验 VALID+负例 INVALID；logical_snapshot 离线重算全部 92 logical_hash；治理门 lean_governance ci = SHIP（提交步骤）
Business evidence: 月度分区真实 Apache Parquet 快照 + manifest + hash（498 docs/500 versions/46 月/92 分区）
Data/Performance/Visual: Data=92 月度分区（2 样例 parquet 已提交）；无性能/UI
Value: 开放/可重复/与 D1 一致的历史快照，2016+ 分析·恢复·可回测预测地基
Cost: 请求0 / D1 0 / R2 0 / 模型 0；经常性成本 0；开发依赖 pyarrow 运行时不用
Known gaps: 见 known_gaps.md
Deployment: NOT_DEPLOYED（离线从 D1 抽样生成）
Rollback: git revert <sha>（离线工具/规则）
Verifier: 待独立上下文复核（实现者不自签 PASS）
```

**IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION**
