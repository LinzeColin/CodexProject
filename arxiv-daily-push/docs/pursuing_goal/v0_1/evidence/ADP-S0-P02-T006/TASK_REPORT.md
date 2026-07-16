# TASK_REPORT · ADP-S0-P02-T006｜采集 Cloudflare/D1/R2/Cron/费用私有基线

## 唯一目标（达成）

只读导出生产部署、数据库、对象存储、计划任务和近 31 天用量 —— 交付 deployment export、D1 schema/count/metrics、R2 usage、plan/billing snapshot、cron。

## 六个开始前问题（已回答，方允许编码）

1. 唯一目标：用 wrangler 只读导出 Cloudflare 生产私有基线，补齐 FACT-011..015。
2. 允许修改文件：仅 `docs/pursuing_goal/v0_1/baselines/T006_CLOUDFLARE_PRIVATE_BASELINE.md` + 本证据包 + 治理同步文件；**只读 API**，0 资源创建，不改代码/配置/schema/设置。
3. 绝不能改变：已上线 MVP、六主题、高级动效、实时稳定与生产行为；**不开 R2、不改任何设置、不写任何数据**。NOT_DEPLOYED。
4. 基线：main `a17e89de`（= origin/main，T005 已合入）；线上 worker = adp-cloud 版本 455afd98；采集时间 2026-07-16T00:31Z。
5. 验收：所有数值含时间范围和单位；无法访问项标 UNVERIFIED；不泄露 secret。
6. 回滚：`git revert <sha>`（纯文档采集，NOT_DEPLOYED）；只读操作无需回滚生产（未写数据、未建资源）。

## 交付物

- `docs/pursuing_goal/v0_1/baselines/T006_CLOUDFLARE_PRIVATE_BASELINE.md` —— 账户/部署、D1、R2、计划账单、漂移发现、事实状态更新、边界与安全。
- `evidence/ADP-S0-P02-T006/private_baseline.json` —— 机器可读全量。
- 原始只读输出：`d1_info.txt`、`d1_counts.txt`、`r2.txt`、`deployments_recent.txt`（已确认无 token）。

## 验收结果（实测，read-only）

- **deployment export**：adp-cloud 当前线上版本 `455afd98-027a-4ace-9619-736a464f9bd3`（2026-07-15T09:39:45Z）；cron `30 20 * * *`。
- **D1 schema/count/metrics**：`adp-mirror`，**14 表**（8 云原生 cn_* + 6 遗留 mirror/inbox），size **1.05 MB**，region OC/BNE，created 2026-07-14T22:00Z，replication disabled；近 24h read 3,503 / write 3,864 queries，rows_read 221,565 / rows_written 13,426；逐表 COUNT 已记录（cn_items 682、cn_sources 33、cn_selections/cn_lessons 各 1、cn_meta 0…）。
- **R2 usage**：**NOT_ENABLED**（API code 10042）；未代开。
- **plan/billing snapshot**：**UNVERIFIED_PRIVATE**（CLI 不暴露；用量在免费档包络内但非套餐确认）。
- **单位/时间范围**：D1 指标标「近 24h」+ 计数/字节/MB 单位齐全。
- **无 secret 泄露**：OAuth token / API key 一律未记录；token 扫描 clean。
- **只读证明**：所有 D1 读 `changed_db=false`、`rows_written=0`（SELECT）。

## Data / Performance / Visual

- Data：只读，未写入任何行（changed_db=false）；记录真实行数为容量基线。
- Performance：D1 单查询 sql_duration ~0.47ms（示例）；未做压测。
- Visual：无变更。

## Value / Cost

- Value：为容量、成本和迁移决策提供**真实起点**（1.05MB / 682 items / R2 未启用 / 数据早期），取代 20TB 压测包络的臆测。
- Cost：**只读 API，0 资源创建**，0 经常性云成本增量。套餐/账单本身 UNVERIFIED（不记为 0）。

## Known gaps

见 `known_gaps.md`（FACT-013 套餐/账单、FACT-015 私有分支仍 UNVERIFIED，交 S0 Exit Owner）。

## 不适用证据项

`migration.sql/rollback.sql`（未改 schema）、`screenshots-or-videos`（无 UI）、`benchmarks/before|after`（无压测）、`test-results`（无代码测试；治理门见提交步骤）、`deployment_manifest.preview.json`（NOT_DEPLOYED；线上 manifest 以 deployments_recent.txt 记录）—— 均标记 N/A 或以只读导出替代。

## 完成声明

```text
Task: ADP-S0-P02-T006
Commit: <记于提交步骤，见 changed_files.txt / git 历史>
Files changed: 1 交付基线 + private_baseline.json + 4 原始只读输出 + 证据文本 + 治理同步（见 changed_files.txt）
Tests: wrangler 只读导出（d1 info/execute SELECT/deployments/r2）；changed_db=false；token 扫描 clean（commands.log）；治理门 lean_governance ci = SHIP（提交步骤）
Business evidence: T006_CLOUDFLARE_PRIVATE_BASELINE.md + private_baseline.json（部署/D1/R2/cron/用量，含时间范围与单位）
Data/Performance/Visual: 只读（未写数据）；D1 14 表/1.05MB；无 UI 变更
Value: 容量/成本/迁移的真实起点（R2 未启用、数据早期、1.05MB）
Cost: 只读 API、0 资源创建、0 经常性云成本增量；套餐/账单 UNVERIFIED（不记为 0）
Known gaps: 见 known_gaps.md（FACT-013/FACT-015 待 Owner）
Deployment: NOT_DEPLOYED
Rollback: git revert <sha>（纯文档；只读操作无生产写入需回滚）
Verifier: 待独立上下文复核（实现者不自签 PASS）
```

**IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION**
