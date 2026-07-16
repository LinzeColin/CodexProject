# TASK_REPORT · ADP-S3-P03-T040｜Board 3 官方视图 Canary 与可回滚切换

## 唯一目标（达成）
**Owner S3 Exit 门已批准 A0 晋级** → 实现 Board 3 官方视图的**可回滚 canary 切换**：将媒体降为 discovery、官方原文成为默认证据。交付 feature flag、canary cohort、rollback、manifest update。**切换后官方证据率 100%；P0 解析/延迟回归可在一个部署内回滚。** release_mode=CANARY。

## 六个开始前问题（已回答）
1. **唯一目标**：Board 3 A0 官方视图 canary 切换 + 一次部署回滚；官方证据率 100%；flag OFF 生产不变。
2. **允许修改文件**：`deploy/cloudflare/worker_cloud.js`（flag + 门 + canary 端点 + build hash）+ `docs/pursuing_goal/v0_1/` 证据包 + 治理同步（product_capability_change：parameter_registry + TRACEABILITY/VERSION/delivery + manifest）。
3. **绝不能改变**：**六主题高级动效、线上 MVP、抓取主链**——flag **默认 OFF** = 生产 Board 3（媒体）与六主题**逐字不变**；canary 端点**非破坏性**（不写生产）。
4. **基线**：main `2027e012`（T039 shadow 已合入，建议 READY）；**Owner 已批准 A0 晋级进 T040**；live worker `64c8b842`（回滚目标）。
5. **验收**：切换后官方证据率 100%；出现 P0 解析/延迟回归可在一个部署内回滚。
6. **回滚**：flag 置 `BOARD3_A0_ONLY=false` 一次部署（当前即此态）；或 `wrangler versions deploy 64c8b842`。

## 交付物
- `worker_cloud.js` —— **feature flag** `BOARD3_A0_ONLY`（默认 OFF）+ **A0 准入门** `a0Board3Eligible`（Board 3 仅央级 .gov.cn/A0 白名单源作证据，媒体降 discovery）+ selectDaily 门控（flag OFF 无改动）+ **非破坏性 canary 端点** `/api/a0-canary`（实抓 gov.cn 政策原文 + 应用门 + 报告官方证据率，不写生产）；build hash 自排除重算 `9cd3d8a2fe68→b189d3cc0703`。
- **deploy**：adp-cloud version `5bcd9f21`（build b189d3cc0703）；rollback = 64c8b842 / flag off。
- **manifest update** + 治理（product_capability_change）。

## 验收结果（实测生产，见 test-results/deploy_verify.txt + canary_live_response.json）
- **切换后官方证据率 100%**：`/api/a0-canary`（生产，非破坏性）实抓 **8 篇真实 gov.cn 政策原文**（中华人民共和国政府信息公开条例、国务院办公厅通知…）→ **official_evidence_rate = 1.0（100%）**、official_eligible 8/8、**media_evidence_rate_under_gate = 0**、board3_media_in_db 105 → 门下全部降 discovery。
- **P0 回归可一个部署内回滚**：`rollback = 置 BOARD3_A0_ONLY=false 一次部署`（当前即此态）；版本回滚 `wrangler versions deploy 64c8b842`。
- **生产 MVP 不变（flag OFF）**：两域名 **六主题 6/6**（cosmos/forest/fresh/minimal/techno/warm）、hero 视频在、build 页脚 b189d3cc0703；**8 条路由全 200**（today/queue/radar/system/history/search/build.json/a0-canary）。
- **非破坏性**：canary 只读实抓 + 只读 DB，**writes nothing to production**。

## Data / Performance / Visual
Data = canary 实抓 8 篇 gov.cn 政策原文 + 105 board3 媒体门控预览。Performance = canary 1 子请求/调用（手动，非 cron），DIR-007 预算内。Visual = **六主题 6/6 两域名保留**（flag OFF，MVP 未触）。

## Value / Cost（S3 China A0 Official Pilot）
- **Value**：A0 官方视图的**可逆切换已上线**——门 + flag 使官方原文可成 Board 3 默认证据、媒体降 discovery；canary 用真实 gov.cn 原文证明官方证据率 100%；**flag OFF 保线上 MVP + 六主题零风险**，回滚一次部署。落实 Owner S3 Exit 批准，但**留安全阀**（完整翻转待适配器接 cron + 真实 14 天 shadow）。
- **Cost（逐项，未知不填 0）**：新增请求 1（canary/调用，手动）；D1 读 105（canary board3 预览）/ 写 0；R2 0；模型 0；人工维护 = flag/门/canary。经常性云成本 delta = $0/月（flag OFF，cron 路径不变、0 新子请求）。

## Known gaps
见 `known_gaps.md`：flag 默认 OFF 官方未成生产默认（完整翻转待适配器接 cron + 真实 shadow）；canary 官方内容实时抓取非落库；A0 门为最小实现；build.json 边缘缓存自愈；回滚双路径。

## 不适用证据项
`migration.sql/rollback.sql`、`screenshots-or-videos`、`benchmarks`、`deployment_manifest.preview.json`（用真实 manifest 更新）—— N/A。`data-samples` = canary_live_response.json + deploy_verify.txt。

## 完成声明
```text
Task: ADP-S3-P03-T040
Commit: <记于提交步骤，见 changed_files.txt / git 历史>
Deploy: adp-cloud version 5bcd9f21 (build b189d3cc0703); rollback 64c8b842 / flag BOARD3_A0_ONLY=false
Files changed: deploy/cloudflare/worker_cloud.js（flag+A0门+canary端点+build hash）+ T040 证据包 + 治理同步(product_capability: parameter_registry+TRACEABILITY+VERSION+delivery+manifest；见 changed_files.txt)
Tests: deploy_verify.txt + canary_live_response.json —— 两域名六主题6/6+hero+8路由200；/api/a0-canary 8真实gov.cn原文/官方证据率1.0/媒体门下0/非破坏性/flag OFF；回滚一次部署，ACCEPTANCE 满足；治理门 lean_governance ci = SHIP（提交步骤）
Business evidence: Board 3 A0 官方视图可回滚 canary 切换（官方证据率100%，flag OFF 保MVP，回滚一次部署）
Data/Performance/Visual: Data=canary 8原文+105媒体预览；Perf=1子请求/调用DIR-007内；Visual=六主题6/6两域名保留
Value: A0官方视图可逆切换上线，官方证据率100%，MVP/六主题零风险
Cost: 请求1(canary手动) / D1读105 / R2 0 / 模型 0；经常性成本 0(flag OFF)
Known gaps: 见 known_gaps.md（完整翻转待适配器接cron+真实shadow）
Deployment: CANARY（version 5bcd9f21, flag OFF；生产Board3+六主题不变）
Rollback: BOARD3_A0_ONLY=false 一次部署 / wrangler versions deploy 64c8b842
Verifier: 待独立上下文复核（实现者不自签 PASS）
```

**IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION**
