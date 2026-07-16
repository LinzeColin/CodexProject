# ADR · 编排与成本决策：Cron+Queue vs Workflows（ADP-S2-P03-T030）

**状态**：ACCEPTED（NOT_DEPLOYED —— 决策 + 实验，未改生产编排）。**日期**：2026-07-17。**取代**：无。
**依赖**：T023（R2 shadow 成本）、T026（版本幂等）、DIR-007（免费额度硬约束）。

## 背景

每日流水线当前为 **Cron Trigger（`30 20 * * *`）→ worker 内顺序处理 ~13 源 → 选择 → 讲义 → 发布**，
并已具备幂等（T022 R2 dual-write 的 HEAD 去重 + `cn_artifacts` PK 幂等）。问题：是否应引入
**Cloudflare Queues（Cron+Queue）** 或 **Cloudflare Workflows** 以提升可靠性（at-least-once、DLQ、可恢复多步）？

## 关键约束（决定性）

- **DIR-007 免费档硬约束**：整个 ADP 及所有 repo **不得超 Cloudflare 免费额度**，除非 Owner 再三确认授权。
- **Cloudflare Queues 与 Workflows 均需 Workers Paid 计划（$5/月起）**，Free 档不可用。因此
  **采用 Queue 或 Workflows = 离开免费档 = 触发 DIR-007 停线**，须 Owner 付费授权才可。
- 规模：**1 次 cron/天 × ~13 源**，低频、无强跨步持久化需求。

## 候选路径（成本 benchmark 见 `evidence/…/orchestration_report.json`）

| 路径 | 计划 | 需付费? | 月 Queue ops | 月 Workflow steps | 月 D1 ops≈ | 新增步骤 | DIR-007 |
|---|---|---|---|---|---|---|---|
| **A** Cron + worker 幂等 + D1 retry/DLQ | Free | **否** | 0 | 0 | ~780 | 0 | **OK** |
| B Cron + Queue | Workers Paid | 是 | ~1170 | 0 | ~780 | ~390 | 违反 |
| C Workflows | Workers Paid | 是 | 0 | ~480 | ~780 | ~480 | 违反 |

（工作量：13 源 × 30 天 = 390 消息/月；ops 为结构性计数，非厂商单价。）

## 可靠性论证（实验，见 `tools/idempotency_harness.py`）

在**免费档 Path A** 上模拟 **at-least-once 投递**（消息重复 2–3 次 + 瞬时失败重试 + poison 消息）：
- **exactly-once 效果**：40 逻辑任务、55 次投递（**确有重复**）、幂等键去重 → **36 个效果各只应用一次**（36 = 40 − 4 poison）；**无任何效果应用两次**。
- **DLQ**：4 个 poison 消息在 `max_attempts` 后**全部进 DLQ**，效果从不应用。
- 即：**Cron + 幂等键（D1 upsert）+ D1 DLQ 账本**在免费档即可得 at-least-once 下的 **exactly-once 效果**——Queues/Workflows 的可靠性收益在本规模**无增量**。

## 决策

**保持 Path A（免费 Cron + worker 内幂等 + D1 retry/DLQ 账本）。不引入 Queues 或 Workflows。**

理由：
1. **可靠性收益 = 0（本规模）**：Path A 已达 exactly-once 效果 + DLQ；B/C 不带来可测可靠性提升。
2. **成本 & 复杂度更高**：B/C 均需 Workers Paid（离开免费档，**DIR-007 禁止**），且新增 per-op/per-step 计费与维护（queue consumer / workflow 版本化 / DLQ 队列）。
3. 符合验收：**“Workflows 只有在可靠性收益高于新增步骤费用和维护复杂度时采用；否则保持简单路径。”** → 本例保持简单路径。

## 触发重估的条件（写死，便于将来）

仅当**同时**满足才重开此 ADR：(a) 真实可靠性缺口（如多次/天、强跨步持久化、长任务需断点续跑）；
**且** (b) Owner 明确授权 Workers Paid（DIR-007 例外）。届时优先 Queues（更简单）over Workflows，除非需要持久多步编排。

## 落地增量（Path A，本任务只给设计，不改生产）

- 幂等键：沿用内容寻址（T021/T022）+ `cn_artifacts` PK；处理效果一律 upsert。
- D1 retry/DLQ 账本：一张 `cn_task_dlq(idempotency_key PK, attempts, last_error, first_seen, status)`；`max_attempts` 后置 DLQ 状态，人工/后续任务重放（T026 replay 幂等保证安全）。
- 回滚：纯设计 + 实验，`git revert <sha>`；未改生产编排。
