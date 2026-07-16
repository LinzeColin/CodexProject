# TASK_REPORT · ADP-S2-P01-T022｜实现 Feature-flagged RawArtifact Dual-write

## 唯一目标（达成）
现有抓取成功后旁路保存原始字节，不改变发布主链 —— 交付 R2 writer、D1 artifact row、feature flag、retry/idempotency。

## 六个开始前问题（已回答）
1. 唯一目标：实现 feature-flagged R2 原始字节双写（SHADOW），关 flag=基线，重试不产生重复对象。
2. 允许修改文件：`deploy/cloudflare/{worker_cloud.js, wrangler_cloud.jsonc, schema_cloud.sql}` + 本证据包 + 治理同步。
3. 绝不能改变：六主题/hero/动效/CSP/发布主链；**flag 默认关=部署即基线**。
4. 基线：main `4475a8c3`（DIR-007 已合入）；R2 已启用（Owner 2026-07-16）；pre-deploy 版本 3816d21c（回滚目标）。
5. 验收：关闭 flag 时行为与基线相同；重试不产生重复对象。
6. 回滚：`wrangler versions deploy 3816d21c` + `rollback.sql`（DROP cn_artifacts）；SHADOW 特性无发布链依赖。

## DIR-007 合规
R2 写路径**内置免费档硬预算停**（写前核对 Class A/B/bytes 月累计 vs 10GB/1e6/1e7，guard 0.9，超则 quarantine 不写）；每次报当前用量。

## 交付物
- `worker_cloud.js`：dualWriteArtifact()（sha256 content-addressed 键 + HEAD 幂等 + 预算硬停 + R2 put + D1 行）、`RAW_DUALWRITE` flag（默认 false）、fetchFeedText 抓取后旁路 hook、`/api/raw-selftest` 验证路由。
- `wrangler_cloud.jsonc`：R2 binding `RAW`→adp-raw-artifacts。
- `schema_cloud.sql` + `migration.sql`：cn_artifacts 表（object_key PK => 幂等）；`rollback.sql`：DROP。

## 验收结果（实测，见 test-results/dualwrite_verify.txt）
- **关 flag=基线**：RAW_DUALWRITE=false 部署（版本 657fe32a）；实测两域名六主题 6/6 + 3 hero 视频 + 仪表盘 + fx + ChatGPT 全保留、7 路由 200、/build.json 一致（build e377c9bd1e20）。pipeline 双写未激活。
- **重试不产生重复对象**：POST /api/raw-selftest 写同字节 2 次 → first {wrote:true}、second {deduped:true, wrote:false, 同键} → **idempotent: true**；D1 cn_artifacts **1 行**（ON CONFLICT DO NOTHING）。
- **预算（DIR-007）**：月用量 Class A 1 / Class B 2 / bytes 76，占额度 ~0.0001%；写前预算硬停就位。
- **node --check**：OK（部署前后）。

## Data / Performance / Visual（受保护基线核对）
- **Visual：无退化**（六主题/hero/动效实测保留；仅新增 /api/raw-selftest 管理端点与页脚 build 更新）。
- Data：新增 cn_artifacts 表 + 1 测试行；R2 1 测试对象（76B）。Performance：dualWriteArtifact 仅在 flag 开时进 pipeline；HEAD+put 各 1 次/对象。

## Value / Cost（S2 = 不可变原始证据）
- **Value**：抓取成功后可旁路存**不可变原始字节**（content-addressed 幂等、发布主链零改动），为 T023 shadow + 版本链打底；DIR-007 预算内。
- **Cost（逐项，未知不填 0）**：新增请求 = 每对象 1 HEAD(Class B)+按需 1 PUT(Class A)；D1 每对象 ≤1 行写；R2 bytes = 原始字节；模型 0；本次验证用量 Class A 1/Class B 2/76B。经常性成本 ≈ **$0**（免费档内，DIR-007 硬顶）。free_tier_usage 见 cost_value.json。

## Known gaps
见 known_gaps.md（flag 仍关，SHADOW 真跑=T023；压缩存 none 保原始字节；selftest 对象保留为证据）。

## 不适用证据项
`benchmarks`、`screenshots-or-videos`（视觉文字+HTML 标记固化）、`data-samples`、`deployment_manifest.preview.json`(T009覆盖) —— N/A。`migration.sql`+`rollback.sql` 已附。

## 完成声明
```text
Task: ADP-S2-P01-T022
Commit: <记于提交步骤，见 changed_files.txt / git 历史>
Files changed: worker_cloud.js + wrangler_cloud.jsonc + schema_cloud.sql + migration/rollback + 证据 + 治理同步（见 changed_files.txt）
Tests: dualwrite_verify.txt —— flag关=基线(六主题+7路由200) + 重试幂等(second deduped,D1 1行) + 预算 Class A1/B2/76B + node --check OK；治理门 lean_governance ci = SHIP（提交步骤）
Business evidence: feature-flagged R2 dual-write（content-addressed 幂等 + DIR-007 预算硬停）
Data/Performance/Visual: 无退化（六主题/hero/动效保留）；+cn_artifacts 表 +1 测试对象
Value: 不可变原始字节旁路存储（发布主链零改动，T023 打底）
Cost: HEAD+PUT/对象 / D1 ≤1行 / 模型0 / 本次 Class A1·B2·76B；经常性≈$0（免费档内）
Known gaps: 见 known_gaps.md（SHADOW 真跑=T023）
Deployment: PRODUCTION（worker 657fe32a；RAW_DUALWRITE flag 默认关=基线；R2 binding + cn_artifacts 就位）
Rollback: wrangler versions deploy 3816d21c + rollback.sql（无发布链依赖，已验证幂等）
Verifier: 待独立上下文复核（实现者不自签 PASS）
```

**IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION**
