# TASK_REPORT · ADP-S0-P02-T004｜采集两个线上域名与核心路由基线

## 唯一目标（达成）

记录 Today、Radar、Review、System、Search、History 的实际响应和视觉状态 —— 交付 headers、HTML 摘要、路由状态、视觉核对、采集时间。

## 六个开始前问题（已回答，方允许编码）

1. 唯一目标：采集两域名 × 六路由的真实用户面基线（只读）。
2. 允许修改文件：仅 `docs/pursuing_goal/v0_1/baselines/T004_PUBLIC_SURFACE_BASELINE.md` + 本证据包 + 治理同步文件；无代码/worker/schema/CSP。
3. 绝不能改变：已上线 MVP、六主题、高级动效、实时稳定与生产行为。**只读采集，NOT_DEPLOYED**。
4. 基线：main `def790d3`（= origin/main，T003 已合入）；线上 worker = 自托管视频版；采集时间 2026-07-16T00:14Z。
5. 验收：不可访问项标 UNVERIFIED；不得把抓取失败写成站点失败；产出 headers/HTML 摘要/路由状态/视觉状态/采集时间。
6. 回滚：`git revert <sha>`；纯文档采集，NOT_DEPLOYED，无生产影响；未改写数据。

## 交付物

- `docs/pursuing_goal/v0_1/baselines/T004_PUBLIC_SURFACE_BASELINE.md` —— 路由状态表、headers、HTML 摘要与视觉基线、双域名一致性初判、未验证边界。
- 原始证据：`evidence/ADP-S0-P02-T004/route_status.json`（12 行）、`headers.txt`、`fingerprints.json`。

## 验收结果（实测）

- **路由状态**：两域名 × 六路由 = **12/12 HTTP 200**（route_status.json）。
- **headers**：两域名根路由逐字一致；`cache-control: no-store, must-revalidate`；CSP `media-src 'self'`（自托管视频，无外部媒体）。
- **HTML 摘要**：六主题键全在（warm/minimal/fresh/techno/cosmos/forest，count=6）；hero 视频三源 `/media/{velorah,voyage,aethera}.mp4`；cosmic 仪表盘/fx 氛围层/ChatGPT 深度追问标记均在页。
- **视觉核对**：实测截图（adp.linzezhang.com，minimal 主题）hero 视频首屏 + 标题 `Costly Attention and Retirement` + 候选评分副标 + 「开始学习↓」+「学习数据」仪表盘 —— 与受保护基线一致。
- **双域名一致性**：Today 归一化相似度 0.9973、仅 1 处动态段不同 → 初判同一 build（严格结论属 FACT-014 / T006）。
- **UNVERIFIED 标注**：私有事实（D1/R2/套餐/私有分支 = FACT-011..015）未采集，明确标 UNVERIFIED_PRIVATE；无抓取失败项（若有会标 UNVERIFIED_FETCH_ERROR 而非站点失败）。

## Data / Performance / Visual

- Data：无写入（只读 12 次 GET）。
- Performance：未做性能压测；仅记录 200 与 headers。
- Visual：before→after 无变更（未改动线上）；视觉状态为**基线记录**，非改动。

## Value / Cost

- Value：得到真实用户面基线（路由/headers/主题/动效/一致性初判），供后续漂移检测与 S7 视觉基线锚点。
- Cost：只读请求量 —— 约 24 次 GET（状态探测 12 + 抓取 12）+ 2 次根 header + 少量指纹抓取；**0 经常性云成本增量**，NOT_DEPLOYED。私有账单 UNKNOWN（不记为 0）。

## Known gaps

见 `known_gaps.md`（截图 PNG 不入仓；带 `?q=` 搜索结果未逐一采集；FACT-014 严格一致性属 T006）。

## 不适用证据项

`migration.sql/rollback.sql`（无 schema）、`benchmarks/before|after`（无性能压测）、`data-samples`（无数据写入）、`test-results`（无代码测试；治理门见提交步骤）、`deployment_manifest.preview.json`（NOT_DEPLOYED）、`screenshots-or-videos/`（实测视觉已核对并文字固化；PNG 二进制不入仓，遵守 no-binary 契约）—— 均标记 N/A 或以文字/指纹替代。

## 完成声明

```text
Task: ADP-S0-P02-T004
Commit: <记于提交步骤，见 changed_files.txt / git 历史>
Files changed: 1 交付基线 + 3 原始证据 + 证据文本 + 治理同步（见 changed_files.txt）
Tests: 路由 12/12 200 + headers 一致 + 六主题/视频/仪表盘标记在页（route_status.json/fingerprints.json/headers.txt）；治理门 lean_governance ci = SHIP（提交步骤）
Business evidence: T004_PUBLIC_SURFACE_BASELINE.md + route_status.json + headers.txt + fingerprints.json
Data/Performance/Visual: 无变更（基线记录；视觉与受保护基线一致）
Value: 真实用户面基线（含双域名一致性初判 0.9973）
Cost: 只读约 24 次 GET；0 经常性云成本增量（私有账单 UNKNOWN，不记为 0）
Known gaps: 见 known_gaps.md
Deployment: NOT_DEPLOYED
Rollback: git revert <sha>（未改写生产数据，纯文档采集）
Verifier: 待独立上下文复核（实现者不自签 PASS）
```

**IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION**
