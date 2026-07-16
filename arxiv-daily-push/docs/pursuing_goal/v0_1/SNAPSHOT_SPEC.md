# Monthly Snapshot Spec · ADP-S2-P03-T027

把 CanonicalDocument 身份（T024）与 DocumentVersion append-only 版本链（T026）导出为**按月分区的开放列式快照**，
供大规模历史分析、恢复与可回测预测使用。工具：`tools/snapshot_writer.py`（确定性，无网络/时钟/随机）。**NOT_DEPLOYED**——
只从 D1 抽样离线生成，不触生产 D1/R2；真实月度快照的落地目标是 R2（后续接线，须各自过 gate + DIR-007 预算）。

## 1. 两张逻辑表（均按月 `YYYY-MM` 分区）

| 表 | 分区键 | 列（schema v1） |
|---|---|---|
| `cn_documents` | `first_seen_month` | canonical_id, title_norm, sources_json, item_count, version_count, first_seen_month |
| `cn_document_versions` | `month` | version_id, canonical_id, version_no, content_hash, status, doc_date, month |

分区文件名：`data/{table}__{YYYY-MM}.{parquet|ndjson}`。真实 500 抽样 → 498 docs / 500 versions / **46 个月（2016-01…2025-10）** / 92 分区。

## 2. 物理格式（Parquet，带确定性回退）

- 有 pyarrow ⇒ 写**真实 Apache Parquet**（`compression=none`、`write_statistics=False`、`version=2.6`）——同环境同输入**字节确定**。
- 无 pyarrow ⇒ 写**确定性 NDJSON** 回退（相同 `logical_hash`），快照始终可生成、可分析。
- Parquet 流内嵌 writer 版本串（`created_by`），故**跨引擎版本字节不保证一致**——因此可重复性锚点是**逻辑哈希**，不是物理字节。

## 3. 可重复性 = 逻辑哈希（格式/引擎无关）

`logical_hash(table, rows, schema_version)` = 对**按主键规范排序、按 schema 列序、类型化**的行做 canonical JSON 后 sha256。
- **同一 logical snapshot 可重复生成**：同输入 ⇒ 每个分区的 `logical_hash` 与整体 `snapshot_id`（= 所有分区 `(table,month,logical_hash)` 的 sha256）**逐一致**，且同环境下 Parquet `physical_sha256` 亦一致。
- manifest 同时记录 `logical_hash`（版本无关，权威）与 `physical_sha256`（环境相关，物理指纹）。
- 证据自洽：`evidence/…/logical_snapshot/*.jsonl` 可**离线重算全部 92 个 manifest logical_hash**，无需 pyarrow 或原始抽样。

## 4. Schema 演进（向后兼容）

`SCHEMA_REGISTRY[table]` 保存**版本化列集**；`evolve_schema(table, new_col)` **追加一个可空列 ⇒ 新 schema 版本**：
- 旧分区保留其 `schema_version`，仍可读；读者在新 schema 下**对新列 null 填充**（schema-on-read 向后兼容）。
- 旧分区的 `logical_hash`（在其自身 schema 版本下）**不因演进而改变**。
- manifest 逐分区记录 `schema_version`，故新旧快照混存可读。

## 5. Manifest（`snapshot_manifest.json`，schema 见 `schemas/snapshot_manifest.schema.json`）

字段：`snapshot_spec_version`、`snapshot_id`、`format`、`engine`、`generated_from`、`reproducibility`、
`schemas`（每表当前列集）、`totals`（docs/versions/months/partitions）、`canonicalize_summary`、
`partitions[]`（每分区 `{table, month, rows, schema_version, logical_hash, path, physical_sha256, bytes}`）。

## 6. 验收（`evidence/ADP-S2-P03-T027/test-results/snapshot_tests.txt`，PASS exit 0）

- **可重复**：连两次生成 ⇒ `snapshot_id`、每分区 `logical_hash`、`physical_sha256` 全等。
- **D1 抽样 ↔ Parquet 行/关系一致**：回读全部 Parquet 分区 ⇒ doc 行=498=抽样派生、version 行=500=抽样派生、
  version.canonical_id **全部** ∈ documents.canonical_id（**0 孤儿**）、每行落在正确月分区。
- **Schema 演进**：v1→v2 加可空列 ⇒ 旧分区在 v2 下可读（新列 null）、v1 `logical_hash` 稳定。

## 7. CLI

```
python3 tools/snapshot_writer.py --items items.json --factsheets fs.json --out-dir OUT [--fallback ndjson]
```
输出 `OUT/snapshot_manifest.json` + `OUT/data/{table}__{month}.{parquet|ndjson}`。
