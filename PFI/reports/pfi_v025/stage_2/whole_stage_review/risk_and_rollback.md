# Stage 2 Whole-Stage Review — Risk and Rollback

## Residual risks

- production FX 仍 `not_loaded`；任何非 null rate 必须来自未来实际 snapshot。
- 余额、负债、持仓与市场价格来源仍 `not_loaded`；五个财务指标保持 blocked/null。
- canonical private root 观察到 mode `0755`，operational SQLite 观察到 mode `0644`；本只读 Stage 不改变权限，该风险由用户在中间 Stage 范围内接受，但不构成 production security acceptance。
- 只有 transaction_time 有 aggregate coverage；其余七个时间字段保持 `not_verified`。
- 三次性能基线是本机 observation，不是 SLA。

## Rollback

回退本 whole-stage review 单一提交，恢复 Stage 2 `in_progress` 与 Stage 3 未授权状态；保留 Phase 2.1/2.2/2.3 历史提交和 evidence。不触碰真实数据、数据库、临时副本、App、remote refs 或用户配置。
