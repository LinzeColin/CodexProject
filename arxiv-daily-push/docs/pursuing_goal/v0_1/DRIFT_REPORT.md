# DRIFT_REPORT · Verified / Unknown / Assumption（S0-P02 事实汇总）

> 任务 `ADP-S0-P02-T007` 交付物。汇总 T004（公开面）、T005（Git/配置/文档）、T006（Cloudflare 私有基线）。
> 机器可读见同目录 `FACT_LEDGER.csv`（20 行）；阻断项见 `BLOCKING_LIST.md`。
> **硬规则：任何需求不得由 UNKNOWN 直接推导；P0 未知项已分配到明确任务/门。**

## 1. 已核实（VERIFIED）

**公开面（T004）**：两域名 × 6 路由 = 12/12 HTTP 200；headers 逐字一致（no-store + 自托管 CSP media-src 'self'）；六主题（warm/minimal/fresh/techno/cosmos/forest）+ 3 自托管 hero 视频 + cosmic 仪表盘 + fx 层 + ChatGPT 深追全在；双域名 Today 归一化相似 0.9973。

**Git/配置（T005）**：main `a4a9954b`（程序推进后）；Worker adp-cloud / worker_cloud.js / compat 2026-07-01 / D1 DB→adp-mirror / cron `30 20 * * *`；schema_cloud.sql 8 张 cn_*；boards registry boards-v03-2（5 板块 41 源）；5 关键文件 git blob 可重查。

**私有基线（T006，read-only，changed_db=false）**：D1 adp-mirror 1.05MB / 14 表 / region OC-BNE / 24h read 3,503·write 3,864·rows_read 221,565·rows_written 13,426；cn_items 682 / cn_sources 33 / cn_selections 1 / cn_lessons 1 / cn_meta 0；**R2 NOT_ENABLED**；live 版本 455afd98。

## 2. 漂移（DRIFT，只登记，本轮不修复）

| id | 漂移 | 证据 | 派往 |
|---|---|---|---|
| DRIFT-FACT-006 | 来源真相：board3 config(Google News 按部委+RSSHub) ≠ worker 硬编码(含人民网/中新网/新浪) | T005 | 后续来源真相任务（S1/S2） |
| DRIFT-FACT-007 | 状态文档：STATUS.yaml J5 云原生与 R6 隧道/Mac 并存，R6 未标 superseded | T005+T006 | 后续治理一致性任务 |
| DRIFT-FACT-011 | 线上 D1 含 6 张 R6 遗留表(events_inbox/*_mirror)，超 schema_cloud.sql 8 张 cn_* | T006 | 后续 D1 清理任务（须回滚方案） |

三处漂移互相印证 R6（隧道/Mac 镜像）虽退役、仍有代码/配置/DB 残留；但**不在 S0 修复**（避免顺带重构，违反任务禁止事项）。

## 3. 未知（UNKNOWN / UNVERIFIED_PRIVATE）—— 已分配，不得据以推导需求

| fact | 未知 | 为何未知 | 派往 |
|---|---|---|---|
| FACT-013 | Cloudflare 套餐/账单/AI·Queues·Workflows 用量 | CLI 不暴露，仅 Owner 后台 | **S0 Exit（Owner）** |
| FACT-015 | 私有分支/未提交代码/未纳入公开仓库的实现 | 需 Owner/仓库只读盘点 | **S0 Exit（Owner）** |
| FACT-014 | 严格「每次部署后双域名恒为同一 build」 | wrangler 按 Worker 而非按 host 报版本 | PARTIAL；后续 S1 部署纪律 |

## 4. 假设（ASSUMPTION，非需求）

- FACT-016：10M 文档 / 30M 版本 / 20TB 是容量压测包络。**T006 实测 D1 仅 1.05MB、数据极早期** → 任何容量/成本/采购决策以真实起点为准，**不得**按 20TB 臆造。

## 5. 过期（STALE）

- FACT-005：旧记录「最新公开提交 242c7e3」已过期 → 现 main `a4a9954b`。

## 6. 结论

- S0-P02 把「公开事实 / Owner 指令 / 推断(PARTIAL) / 未知 / 过期 / 漂移 / 假设」完全分开（FACT_LEDGER.csv）。
- 2 个 P0 未知（FACT-013、FACT-015）已明确派到 S0 Exit Owner 门；3 处漂移派到具名后续任务。
- 幻觉风险已转为**可审计缺口**：后续任何任务若需引用某事实，先查 FACT_LEDGER.csv 的 classification 与 verification_status，UNKNOWN 不得直接变需求。
