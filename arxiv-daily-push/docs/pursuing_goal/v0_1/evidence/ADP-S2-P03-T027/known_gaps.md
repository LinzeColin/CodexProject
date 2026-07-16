# Known gaps · ADP-S2-P03-T027

- **NOT_DEPLOYED（任务边界，非缺陷）**：`snapshot_writer.py` 只从 **D1 抽样**离线生成快照，**未接生产 D1/R2**。真实月度快照的落地目标是 R2（内容寻址 + DIR-007 预算硬停），并需与恢复演练（T028）联动——属后续任务，各自过 gate + 六主题基线复验。
- **新增开发依赖 pyarrow==17.0.0**：为产出**真实 Apache Parquet**，向用户的 Python 3.9 user-site 安装了 `pyarrow`（标准 Parquet 参考实现）。这是**离线证据生成用的开发依赖**，worker/云端运行时不使用；无 pyarrow 时 writer 自动退化为**确定性 NDJSON**，`logical_hash` 完全一致，快照仍可生成/分析/验证。已在 `cost_value.json` 与本文件登记。
- **物理字节跨引擎不保证一致**：Parquet 流内嵌 writer 版本串（`created_by`），故不同 pyarrow 版本产出的 `.parquet` 字节不同。**可重复性锚点是版本无关的 `logical_hash`**（manifest 同时记录 `physical_sha256` 作环境指纹）；`evidence/logical_snapshot/*.jsonl` 可离线重算全部 92 个 logical_hash，无需 pyarrow。
- **抽样而非全量**：用 500 条真实抽样（2016-01…2026-07，46 个月；本行末月曾误写 2025-10，经 T028 更正）演示机制与验收；全量历史（cn_items 682+，及 2016+ 全量恢复）在恢复/回填任务里跑，快照器本身对全量无结构性限制。
- **版本链深度受抽样限制**：单次快照下多数 canonical 文档只有 v1；500 版本 vs 498 文档来自 2 条改写转载形成的 2 段真实多版本链。跨时间的深版本链由 cron/回填随真实时间累积（T026 fixtures 已单独验证多版本逻辑）。
- **仅两张表**：本快照覆盖 `cn_documents` + `cn_document_versions`（身份 + 版本轴）。原文 artifact（R2）、selections/lessons、五板块 factsheet 的快照化可按同一 partition/schema/manifest 机制扩展，未包含在本任务范围。
- **committed 仅 2 个样例 parquet**：为遵守「排除二进制/大数据」约定，只提交 manifest（含 92 分区全部哈希）+ 可验证的 `logical_snapshot/*.jsonl` + 2 个代表性样例 `.parquet`（2016-01 稀疏 / 2025-06 稠密）。其余 90 个分区可由 writer 从 logical_snapshot 确定性重建并对 manifest 校验。
