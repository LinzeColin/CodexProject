# T006 · Cloudflare / D1 / R2 / Cron / 费用 私有基线

> 任务 `ADP-S0-P02-T006` 交付物。**采集时间（UTC）：2026-07-16T00:31Z**。只读导出（wrangler 4.111.0：whoami / d1 info / d1 execute SELECT --remote / deployments list / r2 bucket list）。
> **所有 D1 读操作 `changed_db=false`；未创建任何资源、未改任何设置、未记录任何 secret。** 无法访问项标 `UNVERIFIED`。机器可读全量见 evidence `private_baseline.json`。

## 1. 账户与部署

- 账户：`Linzezhang35@gmail.com's Account`（account_id `a8e86fa4be62ee3f9b5873b2aa934256`，已在公开 wrangler 配置中；**OAuth token 未记录**）。
- Worker：`adp-cloud`。**当前线上版本** `455afd98-027a-4ace-9619-736a464f9bd3`（2026-07-15T09:39:45Z，author linzezhang35@gmail.com）；2026-07-15 有多次部署，此为最新 100% 版本。
- Cron：`30 20 * * *`（每日 UTC 20:30，定义于 wrangler_cloud.jsonc，已部署）。

## 2. D1 数据库 `adp-mirror`（时间范围与单位齐全）

| 项 | 值 |
|---|---|
| database_id | `d0a7fc44-6de5-4bf4-bd71-7df868a410a3` |
| created | 2026-07-14T22:00:46Z |
| region | OC（served_by_colo BNE） |
| database_size | **1.05 MB**（1,052,672 bytes） |
| num_tables | **14** |
| read_replication | disabled |
| **近 24h**（截至 2026-07-16T00:31Z） | read_queries **3,503** · write_queries **3,864** · rows_read **221,565** · rows_written **13,426** |

### 表与行数（read-only COUNT）

**云原生 `cn_*`（schema_cloud.sql 定义，8 张）**：cn_sources **33** · cn_items **682** · cn_selections **1** · cn_lessons **1** · cn_reviews **2** · cn_events **1** · cn_run_log **2** · cn_meta **0**。

**遗留 mirror/inbox（schema_cloud.sql 未定义，6 张）**：events_inbox 1 · lessons_mirror 4 · manifests_mirror 5 · mirror_meta 3 · review_mirror 2 · selections_mirror 4。

## 3. R2

- **状态：NOT_ENABLED**。`wrangler r2 bucket list` → Cloudflare API `code 10042`「Please enable R2 through the Cloudflare Dashboard」。
- **未由 agent 开启**：开启 R2 是 dashboard/计费/条款动作，Owner 明确不愿代按（「我不会开」），本任务只读、0 资源创建，故记为 NOT_ENABLED，不代开。

## 4. 计划 / 账单

- **UNVERIFIED_PRIVATE**：wrangler CLI 不暴露套餐等级或账单，仅 Owner 后台可见。
- 参考（仅信息，非套餐确认）：D1 用量（1.05MB 存储、24h rows_read 221,565 / rows_written 13,426）落在 D1 免费档典型日限内（5GB / 5M 读 / 10万写）；**这不等于确认账户在免费档**。

## 5. 漂移发现

- **DRIFT-FACT-011 · D1 schema 漂移**：线上 D1 = 14 表 = 8 云原生 `cn_*`（与 schema_cloud.sql 一致）+ **6 张遗留 mirror/inbox 表**（来自已退役 R6 Mac 镜像/隧道架构）。schema_cloud.sql 只定义 8 张 → 线上多出 6 张历史残留。与 DRIFT-FACT-007（R6 退役但残留）呼应。
- **DATA-EARLY-STAGE · 数据量早期**：cn_items 682、cn_sources 33，但 cn_selections 1 / cn_lessons 1 / cn_meta 0 → 云端每日精选/讲义流水线目前只落了极少行；容量/成本决策应以此真实起点为准，而非 20TB 压测包络。

## 6. 事实状态更新（供 T007 漂移报告）

| Fact | 采前 | 采后 |
|---|---|---|
| FACT-011 D1 schema/行数/大小/延迟 | UNVERIFIED_PRIVATE | **VERIFIED**（14 表 / 1.05MB / 逐表计数 / 24h 指标） |
| FACT-012 R2 状态 | UNVERIFIED_PRIVATE | **VERIFIED：NOT_ENABLED** |
| FACT-013 套餐/账单 | UNVERIFIED_PRIVATE | **仍 UNVERIFIED_PRIVATE**（CLI 不可见；用量在免费档包络内但非套餐确认） |
| FACT-014 build↔双域名一致 | UNVERIFIED_PRIVATE | **PARTIAL**：当前 adp-cloud 版本 455afd98；公开面相似度 0.9973（T004）；严格逐 host build 相等未单独证实 |
| FACT-015 私有分支/未提交代码 | UNVERIFIED_PRIVATE | 未在本任务范围（需 Owner/仓库只读盘点） |

## 7. 边界与安全

- 全程只读：D1 仅 `SELECT`（`changed_db=false`）、其余为 list/info；**未创建资源、未开 R2、未改设置、未写数据**。
- 未记录任何 secret：OAuth token、API key 一律不入证据；仅记录 account_id/database_id/version_id 等已公开标识符。
- FACT-013 与 FACT-015 明确留 UNVERIFIED，交 S0 Exit 由 Owner 补充或确认无关键遗漏。
