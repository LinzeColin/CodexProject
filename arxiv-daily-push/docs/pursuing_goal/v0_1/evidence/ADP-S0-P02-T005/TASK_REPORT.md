# TASK_REPORT · ADP-S0-P02-T005｜采集 Git、配置和文档事实

## 唯一目标（达成）

固定当前 ADP commit、Worker 入口、source arrays、schema、cron 和互相矛盾文档 —— 交付 git_sha、file hashes、drift candidates、公开证据链接。

## 六个开始前问题（已回答，方允许编码）

1. 唯一目标：把仓库内可验证的 Git/配置/文档事实固化为可重查基线 + 列出文档冲突。
2. 允许修改文件：仅 `docs/pursuing_goal/v0_1/baselines/T005_GIT_CONFIG_DOC_FACTS.md` + 本证据包 + 治理同步文件；**只读**采集，不改任何代码/配置/schema。
3. 绝不能改变：已上线 MVP、六主题、高级动效、实时稳定与生产行为；不修复漂移（只登记）。NOT_DEPLOYED。
4. 基线：main `662a26df`（= origin/main，T004 已合入）；线上 worker = 自托管视频版；采集时间 2026-07-16T00:20Z。
5. 验收：最新 commit 与关键文件 hash 可重查（`git hash-object`）；文档冲突均列出。
6. 回滚：`git revert <sha>`；纯文档采集，NOT_DEPLOYED，无生产影响；未改写数据。

## 交付物

- `docs/pursuing_goal/v0_1/baselines/T005_GIT_CONFIG_DOC_FACTS.md` —— Git 事实、Worker 入口、D1 schema、source arrays、关键文件 blob hash、漂移候选、公开证据链接、边界。
- `evidence/ADP-S0-P02-T005/facts.json` —— 机器可读全量事实与漂移候选。

## 验收结果（实测）

- **git_sha**：main `662a26dfa9f10577c10d75c3efb515d6823a32ee`（可重查）。
- **file hashes**：5 个关键文件 git blob 已记录（worker_cloud.js `c0878f28`、wrangler_cloud.jsonc `bb889e6b`、schema_cloud.sql `1ad27d27`、boards_v0_3.yaml `fff7d37d`、STATUS.yaml `c7948faa`）；`git hash-object` 可重查。
- **Worker 入口**：name `adp-cloud`、main `worker_cloud.js`、compat `2026-07-01`、D1 `DB`→`adp-mirror`、cron `30 20 * * *`。
- **source arrays**：boards_v0_3.yaml（registry_ver `boards-v03-2`，5 板块，41 条源）已固定；board3 config = Google News 按部委 + RSSHub。
- **schema**：schema_cloud.sql 8 张 `cn_*` 表已列出（文件定义；线上实际属 T006）。
- **drift candidates（文档冲突均列出）**：
  - DRIFT-FACT-006 来源真相漂移（board3 config Google News/RSSHub ↔ worker 硬编码含 人民网/中新网/新浪）。
  - DRIFT-FACT-007 状态文档矛盾（STATUS.yaml J5 云原生 与 R6 隧道/Mac 镜像并存，R6 未标 superseded）。
- **公开证据链接**：GitHub blob permalink base @ 662a26df 已给出。

## Data / Performance / Visual

N/A —— 只读仓库内静态事实采集，无数据写入、无性能、无 UI/视觉变更。

## Value / Cost

- Value：避免按过期 README/配置开发；单一事实源漂移显性化，供 T007 漂移报告与后续来源真相/治理一致性任务。
- Cost：**0 经常性云成本**；只读本地 git/文件操作，无网络部署、无 D1/R2 操作。UNKNOWN 私有事实见 known_gaps.md（不记为 0）。

## Known gaps

见 `known_gaps.md`（漂移只登记不修复；线上运行时事实属 T006）。

## 不适用证据项

`migration.sql/rollback.sql`（无 schema 变更）、`screenshots-or-videos`（无 UI）、`benchmarks/before|after`（无性能）、`data-samples`（无数据）、`test-results`（无代码测试；治理门见提交步骤）、`deployment_manifest.preview.json`（NOT_DEPLOYED）—— 均标记 N/A。

## 完成声明

```text
Task: ADP-S0-P02-T005
Commit: <记于提交步骤，见 changed_files.txt / git 历史>
Files changed: 1 交付基线 + facts.json + 证据文本 + 治理同步（见 changed_files.txt）
Tests: git hash-object 5 文件可重查 + boards/schema/cron 提取 + 2 漂移候选列出（facts.json/commands.log）；治理门 lean_governance ci = SHIP（提交步骤）
Business evidence: T005_GIT_CONFIG_DOC_FACTS.md + facts.json（git_sha/hashes/drift/公开链接）
Data/Performance/Visual: N/A（只读静态事实）
Value: 避免按过期配置开发；单一事实源漂移显性化
Cost: 0 经常性云成本（UNKNOWN 私有事实待 T006，不记为 0）
Known gaps: 见 known_gaps.md
Deployment: NOT_DEPLOYED
Rollback: git revert <sha>（未改写生产数据，纯文档采集）
Verifier: 待独立上下文复核（实现者不自签 PASS）
```

**IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION**
