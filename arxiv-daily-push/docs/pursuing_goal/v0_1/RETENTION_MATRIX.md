# Retention Matrix · ADP-S2-P03-T029

数据生命周期分类：**永久（PERMANENT，永不删除）** vs **可再生（REGENERABLE，可安全丢弃并从永久源+代码重建）**。
机器可读副本在 `tools/restore_drill.py` 的 `RETENTION_MATRIX`；本演练强制：恢复只重建可再生视图，**永久类零删除**。

| 数据类 | 保留 | 删除策略 | 理由 |
|---|---|---|---|
| 原始官方 artifact（R2 内容寻址，A0–A2 官方原文原始字节） | **PERMANENT** | **never** | 事实源；丢失不可再生 |
| 已发布 DocumentVersion（append-only 版本链 + content_hash） | **PERMANENT** | **never** | 不可变历史；删除即改写记录 |
| Canonical 文档身份（canonical_id、sources） | **PERMANENT** | **never** | 转载/修订间稳定身份 |
| Factsheet / L0–L3 人话版 / 缺陷扫描 | REGENERABLE | safe-to-drop | 由原始 + 代码确定性重建 |
| 月度 Parquet 快照 / manifest | REGENERABLE | safe-to-drop | 由版本记录（T027）重建 |
| 派生索引 / dashboards / D1 mirror 视图 | REGENERABLE | safe-to-drop | 由永久源物化 |

## 执行保证（演练实测）

- **永久源只读**：恢复演练前后，永久源文件 sha256 **逐字不变**（`permanent_stores_unchanged=true`）。
- **永久类零删除**：演练对永久类发起的删除数 = **0**（`permanent_delete_count=0`）。
- **隔离**：恢复写入一次性内存 SQLite，**生产 D1/R2 未触碰**。
- **可恢复性**：2016-01 / 2020-07 / 当前月 2026-07 均可从开放快照 + 永久原始证据恢复；随机正文/附件/关系/计数一致。

## 与 DIR-007 的关系

保留策略不改变免费额度约束：永久 artifact 仍走 R2 内容寻址 + DIR-007 预算硬停；可再生视图可按需清理以省额度，但**永久类不得为省额度而删除**（若空间逼近额度，先清可再生、再由 Owner 决策，见 [[FREE_TIER_BUDGET]]/DIR-007）。
