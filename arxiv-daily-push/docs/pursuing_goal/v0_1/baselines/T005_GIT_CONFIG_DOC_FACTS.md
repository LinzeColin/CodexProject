# T005 · Git / 配置 / 文档 事实基线

> 任务 `ADP-S0-P02-T005` 交付物。**采集时间（UTC）：2026-07-16T00:20Z**。固定当前 ADP commit、Worker 入口、source arrays、schema、cron 和互相矛盾文档。
> 机器可读全量见同任务 evidence 目录 `facts.json`；命令见 `commands.log`。所有 hash 为 `git hash-object` blob，可重查。

## 1. Git 事实

- 仓库：`LinzeColin/CodexProject`；ADP 路径 `arxiv-daily-push`。
- main commit（基线）：`662a26dfa9f10577c10d75c3efb515d6823a32ee`。

## 2. Worker 入口与运行事实（`deploy/cloudflare/wrangler_cloud.jsonc`）

| 项 | 值 |
|---|---|
| Worker name | `adp-cloud` |
| 入口 main | `worker_cloud.js` |
| compatibility_date | `2026-07-01` |
| D1 binding | `DB` → database_name `adp-mirror` |
| Cron | `30 20 * * *`（每日 UTC 20:30） |

## 3. D1 schema（`deploy/cloudflare/schema_cloud.sql`）

表：`cn_sources`、`cn_items`、`cn_selections`、`cn_lessons`、`cn_reviews`、`cn_events`、`cn_run_log`、`cn_meta`（8 张，`cn_` 前缀）。
⚠️ schema 为**文件定义**；线上 D1 实际 schema/行数/大小属 `UNVERIFIED_PRIVATE`（FACT-011，T006）。

## 4. Source arrays（`config/boards_v0_3.yaml`，registry_ver `boards-v03-2`，共 41 条源）

| board | 名称 | status |
|---|---|---|
| board1 | 板块一 · 研究前沿 | live_selection（每日精选闭环） |
| board2 | 板块二 · 顶级期刊 | live_feed（Nature/Science/Cell 官方 RSS） |
| board3 | 板块三 · 中国政策法规 | live_feed（Google News 按部委聚合 + RSSHub gov 路由，均 official:false） |
| board4 | 板块四 · 美国科技金融 | live_feed |
| board5 | 板块五 · 跨板块总览 | aggregate |

## 5. 关键文件 hash（git blob，可重查）

| 文件 | blob | 行数 |
|---|---|---|
| `deploy/cloudflare/worker_cloud.js` | `c0878f28dcd0dc236e126313cae3df5c35bf70ba` | 1121 |
| `deploy/cloudflare/wrangler_cloud.jsonc` | `bb889e6b0f590d9e6f4f30c38dfc269e8351dc2b` | 26 |
| `deploy/cloudflare/schema_cloud.sql` | `1ad27d27c9343a89cb7740af02cb24371f30d4e7` | 70 |
| `config/boards_v0_3.yaml` | `fff7d37db17097a066b50f3da7aa73146be9701d` | 115 |
| `docs/v03/STATUS.yaml` | `c7948faa6b58a3acdbdeaa0233fecfcfd943051a` | 189 |

重查命令：`git -C <repo> hash-object arxiv-daily-push/<path>`（应等于上表）。

## 6. 漂移候选（互相矛盾，只记录不修复）

### DRIFT-FACT-006 · 来源真相漂移（board3 config ↔ worker 硬编码）
- **config 说**：`boards_v0_3.yaml` board3「板块三·中国政策法规」= Google News 按部委聚合（国务院/工信部/发改委、科技部/网信办、央行/证监会、AI 治理、药监）+ RSSHub `gov/zhengce/zuixin`，全部 `official:false`。
- **worker 实际**：`worker_cloud.js`（lines 36–51）雷达/中国源硬编码含 Google News + **人民网(×2) + 中国新闻网 + 新浪**。
- **差异**：worker 多出 人民网/中国新闻网/新浪（config 未定义），config 的按部委 Google News 查询 + RSSHub 路由并非线上真身 → **违反单一事实源**。
- 处置：worker 是已部署真身、boards 应与之对齐；本任务只登记，修复留后续 S1/S2 来源真相任务。

### DRIFT-FACT-007 · 状态文档自相矛盾（STATUS.yaml）
- `docs/v03/STATUS.yaml` 同时保留 **J5_cloud_native**（line ~120「网页即主体，整套系统跑云端，不依赖 Mac；全路由实测 200」）与 **R6**（line ~168「phone_access_full_system_via_tunnel_with_mirror_fallback」旧 Cloudflare Tunnel + 本机镜像回落设计）。
- **差异**：现状（J5 云原生）与已退役设计（R6 隧道/Mac 镜像）并存，R6 未标 superseded → **状态记录矛盾**。
- 处置：只登记；修复留后续治理一致性任务。

## 7. 公开证据链接（GitHub blob @ 662a26df）

`https://github.com/LinzeColin/CodexProject/blob/662a26dfa9f10577c10d75c3efb515d6823a32ee/arxiv-daily-push/{deploy/cloudflare/worker_cloud.js | deploy/cloudflare/wrangler_cloud.jsonc | deploy/cloudflare/schema_cloud.sql | config/boards_v0_3.yaml | docs/v03/STATUS.yaml}`

## 8. 边界

- 只固定**仓库内**可验证事实（commit/hash/config/schema-文件/cron/文档矛盾）；**线上运行时**事实（D1 实际行数、R2、套餐、私有分支 = FACT-011..015）属 T006。
- 漂移只**登记**，不在本任务修复（避免顺带重构，违反任务禁止事项）。
