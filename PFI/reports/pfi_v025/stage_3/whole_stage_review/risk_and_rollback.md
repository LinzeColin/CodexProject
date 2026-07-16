# Stage 3 whole-stage risk and rollback

- 1,250 条转账候选和 249 条退款候选仍未确认；review queue 是 fail-closed 证据，不是业务链路确认。
- review queue 持久化未改变；Stage 4、production 数据联通、估值与最终验收均未执行。
- 来源时间仅有日期粒度；标准化时间不能被解释为精确交易时刻。
- 回滚仅需 revert 本地 Stage 3 whole-review 提交并将 Stage 3 恢复为 `in_progress`；保留 Phase 3.1–3.3 immutable evidence。
- 回滚不触碰真实数据、数据库、App 或远端引用；无需 production rollback。
