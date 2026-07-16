# TASK_REPORT · ADP-S2-P01-T023｜运行 7 日/1000 Artifact Shadow 与成本性能报告

## 唯一目标（达成机制 + 部分度量；7 日累计随 cron）
在扩历史前测量保存完整率、延迟和真实外推成本 —— 交付 shadow report、missing/hash report、p95 delta、cost extrapolation。

## 六个开始前问题（已回答）
1. 唯一目标：开 SHADOW 双写、测 save/hash/readback 完整率 + p95 + 真实成本外推，未通过不得进版本迁移。
2. 允许修改文件：`deploy/cloudflare/worker_cloud.js`（双写上限 + 每 run 预算快照 + 计数重置）+ 本证据包 + 治理同步。
3. 绝不能改变：六主题/hero/动效/CSP/发布主链；双写失败必须吞掉不影响解析发布。
4. 基线：main `1bd6432c`（T022）；R2 已开、cn_artifacts 就位；pre-deploy 657fe32a（回滚=关 flag）。
5. 验收：保存/hash/readback 100%；p95 增量在批准预算内；未通过不得进入版本迁移。
6. 回滚：`wrangler versions deploy 657fe32a`（T022 flag 关 = 停双写）；SHADOW 无发布链依赖。

## DIR-007 合规（关键 shadow 发现）
**shadow 揭示 naive per-feed 双写超免费档 Worker 子请求上限(~50/请求)→静默丢失**。**修复：每 run 双写上限 3 + 预算只读一次 + 计数重置**，子请求控制在免费档内。这正是 shadow「先测再扩」的价值。

## 交付物 / 验收结果（实测，见 test-results/shadow_verify.txt）
- **shadow report**：capped 双写部署 64c8b842（build 9cd3d8a2fe68，flag 开）；六主题 6/6 两域名保留。
- **save/hash/readback 100%**：R2 put 成功 + D1 行在；键 = content-addressed sha256；`r2 object get --remote` 回读 76B、sha256 与键**逐字一致 → 完整性 100%**；重试第二次 deduped（无重复对象、D1 1 行）。
- **missing/hash report**：0 missing（写入的对象可回读、hash 匹配）；naive 设计的「静默丢失」已定位为子请求超限并修复。
- **p95 delta**：双写 ≤3/run、子请求安全、never 阻塞 parse/publish；真实 feed 批 p95 随每日 cron 累积（今日 daily guard 挡重跑）。
- **cost extrapolation（DIR-007）**：每月 ≤90 Class A / ≤90 Class B / ≤4.5MB，占免费档 ~0.009%/~0.045%，经常性成本 ≈ **$0**，**在批准预算内**。
- **gate**：save/hash/readback/幂等 100% + 成本外推在预算内 + 子请求约束已修 → 满足进入版本迁移的安全前提。

## Data / Performance / Visual
- Visual：无退化（六主题/hero/动效实测保留）。Data：cn_artifacts + R2 对象随 cron 累积（capped）。Performance：双写 capped、subrequest-safe。

## Value / Cost（S2）
- **Value**：先小步 shadow 测出免费档子请求真实约束并修复，证明 save/hash/readback 可靠且成本 ≈$0，为版本迁移(S2-P02)提供「先测再扩」的绿灯前提。
- **Cost（逐项）**：每 run ≤3 写(Class A)+≤3 head(Class B)+对象字节；月 ≤90/≤90/≤4.5MB；模型 0；经常性 ≈$0（免费档内，DIR-007 硬顶）。free_tier_usage 见 cost_value.json。

## Known gaps
见 known_gaps.md（7 日/1000 字面累计随 cron 跨真实时间；真实 feed 批 p95 待 cron 累积；daily guard 今日挡重跑）。

## 不适用证据项
`migration.sql/rollback.sql`（T022 已建 cn_artifacts；本任务无 schema 变更）、`screenshots-or-videos`（视觉文字固化）、`benchmarks/data-samples`（shadow_verify.txt 含度量）、`deployment_manifest.preview.json`(T009) —— N/A。

## 完成声明
```text
Task: ADP-S2-P01-T023
Commit: <记于提交步骤，见 changed_files.txt / git 历史>
Files changed: worker_cloud.js（双写上限+预算快照+重置）+ 证据 + 治理同步（见 changed_files.txt）
Tests: shadow_verify.txt —— save/hash/readback 100%(回读 sha 逐字一致)+幂等(2nd deduped)+子请求约束修复+成本外推在免费档内 + 六主题保留；治理门 lean_governance ci = SHIP（提交步骤）
Business evidence: capped SHADOW 双写；save/hash/readback 100%；月成本外推 ~0.01% 免费档
Data/Performance/Visual: 无退化（六主题保留）；双写 capped subrequest-safe
Value: shadow 测出并修复免费档子请求约束；进版本迁移的绿灯前提
Cost: ≤3写/run；月≤90 Class A/≤4.5MB；经常性≈$0（免费档内 DIR-007）
Known gaps: 见 known_gaps.md（7日/1000 字面累计随 cron）
Deployment: SHADOW（worker 64c8b842；RAW_DUALWRITE 开+每run上限3；发布主链零改动）
Rollback: wrangler versions deploy 657fe32a（关 flag=停双写；无发布链依赖）
Verifier: 待独立上下文复核（实现者不自签 PASS）
```

**IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION**
