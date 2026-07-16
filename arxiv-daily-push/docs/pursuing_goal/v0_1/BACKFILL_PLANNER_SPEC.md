# Backfill Planner + Cursor Spec · ADP-S4-P01-T041

把 **2016+ 历史回填**拆成**小的年度/月度分片**，每片可重试、可恢复、幂等——历史回填永不重复、崩溃可从最后确认点续跑。
工具：`tools/backfill_planner.py`。**NOT_DEPLOYED**。对应目标「2016+ 可恢复历史」硬约束。

## Planner（分片）

`plan_shards(start='2016-01', end)` → 逐月分片 `backfill/YYYY-MM`（2016-01…2026-07 = **127 片**）。每片独立、小、可重试。

## Cursor / Checkpoint（可恢复）

`ShardCursor{shard_id, year, month, status(pending/in_progress/done), last_confirmed_id, processed, total}`。
- **幂等键 = 内容寻址 id**（T024 canonical_id / T021 raw key）。
- **checkpoint 在确认应用之后推进** `last_confirmed_id`：apply→checkpoint 之间崩溃安全（item 已在 applied 集，重放跳过，见 T026）。
- **schema**：`schemas/backfill_checkpoint.sql` = `cn_backfill_shards`（shard_id PK/status/last_confirmed_id/processed/total）+ status 索引 + `cn_meta.backfill_schema`。

## process_shard / resume

`process_shard(cursor, items, applied, stop_after=None)`：items 按 id 确定性排序；
- **resume**：跳过 id ≤ cursor.last_confirmed_id（已确认过）；
- **幂等**：跳过已在 `applied` 的 id（无重复）；
- **checkpoint**：每确认一条推进 last_confirmed_id；
- `stop_after`：模拟中断（返回半程 cursor）。
`resume(cursor, items, applied)`：从 checkpoint 续跑至 done。

## 验收（`test-results/backfill_tests.txt`，PASS）

- **planner**：127 月度分片，backfill/2016-01…backfill/2026-07。
- **同分片三次无重复**：run1 应用 10、run2/run3 各 0（已应用跳过）→ applied 集 10 唯一，**零重复**。
- **中断后从最后确认点恢复**：中断于第 4 条（status=in_progress，checkpoint 记录）→ resume 续跑恰好 6 条 → done、total 10，**无重做/无跳过/无重复**，resume 严格从 checkpoint 之后开始。

## 边界

planner 只排计划 + cursor 语义，**未接真实回填抓取**（真实各源回填 = 适配器 + 三车道 T042 + 云端接线）；分片粒度月度（可细化到周/日）；idempotency 依赖上游给内容寻址 id（T021/T024）。
