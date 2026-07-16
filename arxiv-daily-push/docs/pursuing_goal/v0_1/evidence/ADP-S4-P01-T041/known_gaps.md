# Known gaps · ADP-S4-P01-T041

- **NOT_DEPLOYED（任务边界，非缺陷）**：planner 只排分片计划 + cursor/checkpoint 语义 + resume；**未接真实回填抓取**。真实各源 2016+ 回填 = 官方适配器（T034-T036）+ 三车道自动暂停（T042）+ 云端接线，属后续。
- **分片粒度月度**：`plan_shards` 逐月（2016-01…2026-07 = 127 片）。稠密源可再细化到周/日分片；本任务月度足够演示可重试/可恢复/幂等。
- **幂等依赖内容寻址 id**：`process_shard` 的无重复靠上游给**内容寻址 id**（T024 canonical_id / T021 raw key）；若上游给非确定性 id，幂等不成立——回填接线时须用内容寻址键。
- **checkpoint schema 未落生产 D1**：`schemas/backfill_checkpoint.sql`（cn_backfill_shards）是 schema，未应用到生产（同 T025 NOT_DEPLOYED）；真实回填时按迁移落库。
- **resume 依赖排序稳定**：resume 用 `id ≤ last_confirmed_id`（排序序）跳过已确认；要求 id 排序稳定（sha 十六进制字符串排序稳定，满足）。
