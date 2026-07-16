# Known gaps · ADP-S2-P03-T030

- **NOT_DEPLOYED（任务边界，非缺陷）**：本任务是**决策（ADR）+ 可靠性/成本实验**，不改生产编排。Path A 的 D1 `cn_task_dlq` retry/DLQ 账本是**设计**，尚未接线到 worker 的每日流水线（属后续 S3+ 若需）。
- **成本 benchmark 为结构性计数、非厂商单价**：给出各路径的月 Queue ops / Workflow steps / D1 ops **计数**与免费档/付费档归属，不臆造 Cloudflare 具体单价（未验证的价格不填）。决定性事实是**Queues 与 Workflows 均需 Workers Paid**（Free 不可用）→ DIR-007 阻断，这与单价无关。
- **可靠性模拟是确定性仿真、非真实 Queue**：`idempotency_harness.simulate()` 用确定性 at-least-once 投递 + 瞬时失败 + poison 建模，证明「幂等键 + D1 DLQ」在免费档得 exactly-once 效果；未在真实 Cloudflare Queue 上跑（那需付费档，DIR-007 阻断）。仿真的价值是证明**免费路径已足够**，无需为可靠性上付费编排。
- **样本规模固定**：n_tasks=40、13 源 × 30 天=390 消息/月，代表当前 1 cron/天低频规模；若未来多次/天或长任务断点续跑，触发 ADR 的「重估条件」并需 Owner 付费授权。
- **未含跨步持久化场景**：本 ADR 针对当前「抓取→选择→讲义→发布」单趟流水线；若引入需要长时间、跨执行边界断点续跑的多步骤（Workflows 的真正卖点），须按 ADR 重估条件重开评估。
