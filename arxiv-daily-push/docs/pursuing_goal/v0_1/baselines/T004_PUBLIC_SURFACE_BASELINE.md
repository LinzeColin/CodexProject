# T004 · 线上公开面基线（两个域名 × 核心路由）

> 任务 `ADP-S0-P02-T004` 交付物。**采集时间（UTC）：2026-07-16T00:14Z**。只读采集；不可访问项标 `UNVERIFIED`，不把抓取失败写成站点失败。
> 原始证据：同任务 evidence 目录下 `route_status.json`（12 行）、`headers.txt`、`fingerprints.json`。

## 1. 域名与路由状态（12/12 = HTTP 200）

| 路由 | path | adp.linzezhang.com | adp-cloud.linzezhang35.workers.dev |
|---|---|---|---|
| Today | `/` | 200 | 200 |
| Review | `/review` | 200 | 200 |
| Radar | `/radar` | 200 | 200 |
| System | `/system` | 200 | 200 |
| Search | `/search` | 200 | 200 |
| History | `/history` | 200 | 200 |

两域名的六条核心路由全部 200，`content-type: text/html; charset=utf-8`。

## 2. 响应 headers（两域名根路由一致）

```
content-type: text/html; charset=utf-8
cache-control: no-store, must-revalidate
content-security-policy: default-src 'self'; img-src 'self' data:; media-src 'self';
    style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline';
    form-action 'self'; base-uri 'none'; frame-ancestors 'none'
referrer-policy: strict-origin-when-cross-origin
server: cloudflare
```

- `cache-control: no-store, must-revalidate` —— 防陈旧页（此前 `no-cache` 曾导致浏览器供旧页）。
- CSP `media-src 'self'` —— hero 视频自托管，无外部媒体依赖（CloudFront 已移除）。
- 两域名 headers **逐字一致**。

## 3. HTML 摘要与视觉基线（Today `/`）

- `<title>`：`ADP 前沿学习`（Radar/Review/Search/History 为 `<板块> · ADP 前沿学习`）。
- **六主题全部存在**（HTML 内含全部主题键）：`warm / minimal / fresh / techno / cosmos / forest`（count=6）。
- **高级动效基线在页**：主题选择器、hero 视频（`/media/velorah.mp4`、`/media/voyage.mp4`、`/media/aethera.mp4` 自托管）、cosmic 仪表盘（gauge/vitals 标记）、fx 氛围层（fx-cosmos/techno/minimal/forest-slopes）。
- **导航**：今天 / 复习 / 前沿雷达 / 系统 + 搜索框 + 主题下拉（截图时为「简约专注」minimal）。
- **ChatGPT 深度追问**跳转标记在页（`chatgpt.com`）。
- 实测截图（2026-07-16T00:14Z，adp.linzezhang.com，minimal 主题）：hero 视频首屏（星空/伏案学习）+ 标题 `Costly Attention and Retirement` + 副标题「跨 387 条候选选中（板块一·研究前沿）；主要因为 relevance、gap、diversity（总分 94.4/104）」+「开始学习↓」CTA + 下方「学习数据」仪表盘。视觉状态与受保护基线一致。

## 4. 双域名一致性（build 层面，初判）

- Today 页归一化（数字/空白规整后）相似度 **0.9973**，仅 **1 处** 结构段不同 → 差异为动态内容（日期/实时 vitals/运行日志），而非 build 分叉。
- headers 逐字一致 + 六主题/视频/仪表盘标记一致 → **初判两域名服务同一 build**。
- ⚠️ 严格的「每次部署后两域名恒为同一 build」属 **FACT-014**，需 build endpoint / Cloudflare 导出证实，是 **T006** 的私有基线工作；此处只作公开面初判，不下最终结论。

## 5. 未验证 / 边界

- 本任务只采集**公开只读**面；D1 行数、R2、套餐、私有分支等 = `UNVERIFIED_PRIVATE`（FACT-011..015，T006）。
- 截图为实测视觉核对；PNG 二进制不入仓（遵守 no-binary 契约），视觉状态以上文文字 + HTML 标记 + headers 固化，可复现命令见 evidence/commands.log。
- `/search` 未带 `?q=` 参数即返回 200（空搜索页）；带查询的结果状态未在本次基线内逐一采集，留作后续。
