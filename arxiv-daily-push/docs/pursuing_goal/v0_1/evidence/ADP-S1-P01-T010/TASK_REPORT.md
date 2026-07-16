# TASK_REPORT · ADP-S1-P01-T010｜发布只读 Build Endpoint 与低干扰版本标识

## 唯一目标（达成）

让两个域名和测试工具能确认实际运行 build —— 交付 `/build.json` 端点 + 页脚 build id。

## 六个开始前问题（已回答，方允许编码）

1. 唯一目标：发布只读 build 标识，使两域名可确认线上跑的是哪套 build。
2. 允许修改文件：仅 `deploy/cloudflare/worker_cloud.js`（外科手术式加 BUILD 常量 + `/build.json` 路由 + 页脚 build id）+ 本证据包 + 治理同步（含 parameter_registry 再证明）。
3. 绝不能改变：六主题、hero 视频、cosmic 仪表盘、fx 氛围层、ChatGPT 深追、CSP、no-store、实时稳定——**全部实测保留**。
4. 基线：main `0aa4c1d7`；部署前 live 版本 `455afd98`（回滚目标）；部署后 `3816d21c`。
5. 验收：两域名 build id/bundle hash/source hash/schema version 一致；不暴露 secret。
6. 回滚：`wrangler rollback`（或 `wrangler versions deploy 455afd98...`）；纯加法、无 schema/数据变更。

## 交付物

- `/build.json` 只读端点：`{"build_id","source_sha256","schema_version","built_at"}`。
- 页脚 build id：`build bd67a78020a3`（链到 /build.json）。
- BUILD 常量：build_id/source_sha256 为**自排除哈希**（把两字段值重置为 '0'×12 与 '0'×64 后 sha256 文件即复现 source_sha256）。

## 验收结果（实测，见 test-results/deploy_verify.txt）

- **两域名 /build.json 逐字一致**：`{"build_id":"bd67a78020a3","source_sha256":"bd67a78020a3…ead084","schema_version":"cn_v0_3","built_at":"2026-07-16"}` —— adp.linzezhang.com == workers.dev ✓。
- **build id / bundle+source hash / schema version 一致**：build_id `bd67a78020a3`、source_sha256（bundle=source，单文件 worker）、schema_version `cn_v0_3` 两域名相同。
- **不暴露 secret**：/build.json 扫描无 token/db-id/account-id/secret；只含 build 标识。
- **7 路由 200**（两域名）：/ /radar /review /system /search /history /build.json。
- **自排除哈希本地校验**：True。
- **node 语法检查**：OK（部署前后）。

## Data / Performance / Visual（受保护基线核对）

- **Visual before→after：无退化**。两域名实测：六主题 6/6（warm/minimal/fresh/techno/cosmos/forest）、hero 视频 3（velorah/voyage/aethera）、cosmic 仪表盘、fx 氛围层、ChatGPT 深追**全部保留**；页脚新增一个 `build …` 链接（唯一可见变化）。
- Data：无 schema/数据变更。Performance：/build.json 为极小静态 JSON，无 D1 访问。

## Value / Cost（S1 = Truth & Content Stabilization）

- **Value（S1 指标）**：两域名与测试工具现在可一键确认线上真身 build（build_id/source_sha/schema），直接支撑 FACT-014（build↔域名一致）验证与后续漂移检测；本次已实证两域名 = 同一 build（`bd67a78020a3`）。
- **Cost（逐项，未知不填 0）**：新增请求 = /build.json 偶发只读（极小 JSON，无 D1）；D1 行读写 **0**（路由不查库）；R2 **0**；模型调用 **0**；人工维护 = build id 由部署时脚本/自排除哈希自动生成。经常性云成本增量 ≈ **$0**（Free 档，请求量微不足道）。

## Known gaps

见 `known_gaps.md`（build id = 源自排除哈希，非 git sha；FACT-014 逐 host 更强绑定可后续加）。

## 不适用证据项

`migration.sql/rollback.sql`（无 schema 变更）、`benchmarks`（无性能压测）、`data-samples`（无数据）—— N/A。`deployment_manifest.preview.json` 由 T009 生成器覆盖。截图以文字+HTML 标记固化（二进制不入仓）。

## 完成声明

```text
Task: ADP-S1-P01-T010
Commit: <记于提交步骤，见 changed_files.txt / git 历史>
Files changed: worker_cloud.js（+7/-1，纯加法）+ parameter_registry 再证明 + 证据 + 治理同步（见 changed_files.txt）
Tests: deploy_verify.txt —— 两域名 /build.json 逐字一致 / 7 路由 200 / 无 secret / 六主题+hero+动效保留 / 自排除哈希 True / node --check OK；治理门 lean_governance ci = SHIP（提交步骤）
Business evidence: /build.json（build_id bd67a78020a3，两域名一致）+ 页脚 build id
Data/Performance/Visual: 无退化（六主题/hero/动效实测保留；页脚新增 build 链接）
Value: 两域名可确认线上真身 build（FACT-014 支撑）
Cost: 新增请求=极小只读 / D1 0 / R2 0 / 模型 0 / 人工≈0；经常性成本≈$0（Free 档）
Known gaps: 见 known_gaps.md
Deployment: PRODUCTION（adp-cloud 版本 3816d21c；两域名 + cron 保留）
Rollback: wrangler 回滚到 455afd98（pre-deploy 版本，已记录；纯加法无数据变更）
Verifier: 待独立上下文复核（实现者不自签 PASS）
```

**IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION**
