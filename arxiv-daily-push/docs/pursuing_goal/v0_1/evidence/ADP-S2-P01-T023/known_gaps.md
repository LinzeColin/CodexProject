# Known gaps · ADP-S2-P01-T023

- **7 日/1000 artifact 字面累计跨真实时间**：capped SHADOW 已上线，每日 cron 双写 ≤3 artifact；1000/7 日的字面累计随真实时间由 cron 累积（一个 session 无法压缩 7 天）。本任务证明了机制(save/hash/readback 100%)+成本(在免费档内)+修复了子请求约束，是版本迁移的安全前提。
- **真实 feed 批 p95 待 cron 累积**：今日 daily-run 幂等 guard 挡住重跑，故真实 feed 批的 p95 增量随明日起 cron 累积；已知：双写 capped、subrequest-safe、never 阻塞 parse/publish。
- **每 run 上限 3 是保守值**：为稳妥留足免费档子请求余量；1000 累计会较慢（3/日）——如需更快可小幅提高上限并重测子请求预算，但不得超免费档（DIR-007）。
- **save/hash/readback 在管理端 selftest artifact 上验证**：real feed artifact 的同类验证随 cron 首批产生后可复核（回读同法）。
- 独立验证：以 IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION 结束，实现者不自签。
