# PFI v0.2.5 Stage 11 Phase 11.3 产品与数据域边界

## Run contract

- Phase / tasks：`V025-S11-P11.3` / `S11-P3-T1..T4`
- Acceptance：`ACC-PFI-V025-STAGE11-WHOLE-REVIEW`
- 风险路由：`T2_PRIVACY_DISTRIBUTION_CONTEXT_RELEASE_IDENTITY`
- implementation base：`599c64eb00d2c725a4817deb050312a91462774e`
- product commit：`890d38a759b9689a65152aa20527bde7ba04b52e`
- 唯一目标：隔离 public Cloudflare surface，建立 Alpha-only 最小只读 Context，完成分发边界扫描并形成 Phase candidate evidence。
- 停止点：12/12 Stage 11 phase tasks 只达到 `candidate_complete`；Stage 11 整阶段独立审查、整改、复审和用户阶段验收未开始。

## S11-P3-T1：public Cloudflare isolation

`web/cloudflare-public` 不再展示 dashboard、allocation preview、产品导航或应用 workspace。当前 surface 只包含静态边界说明：

- HTML/CSS/JSON only；无 JavaScript、form、button、input、iframe、canvas 或 application navigation marker。
- `public-surface.json` 固定 `surface_type=static_boundary_notice`、`active_ui=false`、`application_routes_enabled=false`、`worker_runtime_enabled=false`、`local_runtime_connection=false`、`pfi_context_export_exposed=false`。
- 无账户、凭证、余额、持仓、交易、报告、私有数据库、外部执行或本机 runtime 连接。
- Wrangler 仅发布 static assets，无 Worker/runtime binding；`not_found_handling=404-page`，未知路径不会回退到 index 并伪装成应用 route。
- public source 与隔离 build output 由通用 distribution scanner 和 Stage 11 scanner 双重验证。

Cloudflare 官方文档说明 `single-page-application` 会把未知路径交给根 index，而 `404-page` 会使用最近的 `404.html`；本 Phase 因而选择后者，保持“无应用路由”边界。

## S11-P3-T2：最小只读 PFI Context

唯一 Context schema 是 `pfi_context.v1`，唯一 consumer 是独立系统 `Alpha`。合同由 `config/data_domains/stage11_distribution_boundaries.json`、`shared/context/pfi_context_v1.schema.json` 与 `pfi_os.security.pfi_context_export` 共同约束。

Metadata 精确为七项：

1. `schema_version`
2. `as_of`
3. `source_or_read_model_hash`
4. `privacy_classification`
5. `consumer`
6. `read_only`
7. `writeback_allowed`

Payload 精确为八项：

1. `net_worth_state`
2. `investable_cash_state`
3. `cashflow_pressure`
4. `asset_allocation`
5. `risk_budget`
6. `investment_behavior_tags`
7. `consumption_pressure_summary`
8. `data_freshness`

Payload 只接受封闭状态词表，不接受金额、比例、任意文本或额外字段。`consumer=Alpha`、`read_only=true`、`writeback_allowed=false` 为不可覆盖常量；`as_of` 必须含时区，provenance 必须为小写 SHA-256。

旧 Stage 3/4 synthetic dashboard 不构成 v0.2.5 financial truth。当前 active Stage 5 adapter 只对旧输入做 provenance hash；在没有当前已验证 read model 的情况下，六个业务状态保持 `blocked`、freshness=`not_loaded`、behavior=`review_required`，不会把旧金额或 allocation 数值升级为 Context truth。主页、Stage 6 gate 与正式 Shell 已切换到新合同，不再读取旧 `constraints` 或金额型字段。

CLI `scripts/v025/pfi_context_export.py` 只接受精确 state-only input，最大 64 KiB。输出目录必须为 private `0700`，文件为 `0600`；已有文件、symlink、group/other-readable 目录和 public distribution 路径全部拒绝，receipt 不包含本机路径或财务值。

## S11-P3-T3：分发与排除系统扫描

`scan_stage11_distribution_boundaries.py` fail closed 检查：

- public source/dist 文件类型、私密域标识、credentials、绝对路径、本机 runtime、runtime API、金额形态和 Context field exposure；
- public manifest 与 Wrangler static/404/no-binding contract；
- 正式本地 UI 仍精确 10 个一级入口，Alpha、Ralpha、Serenity-Alipay 均未成为 workspace；
- Context required/properties 精确相等、`additionalProperties=false`、无旧金额字段、sample schema/validator 通过；
- active Python dependency AST 中 Ralpha/Serenity-Alipay import 为 0。

负向测试向隔离 public copy 注入 JavaScript 与 Context field，scanner 必须返回 fail；这证明零发现不是 scanner 恒真。

## 验证与 evidence

- focused Phase 11.3 + legacy adapter：`35/35`。
- Phase 11.3/11.2/11.1 + Stage 5/6 + release identity + shell closeout：`77/77`。
- public `npm run build`、通用 source scan、隔离 dist scan与 Stage 11 boundary scan：全部 pass，finding=0。
- machine 与 embedded release manifest 的 frontend/backend hash 一致；version、build id 与 release commit 未改变。
- TaskPack evidence schema、完整 Git archive + exact overlay governance、双 Python renderer、privacy scan 与 artifact hashes 是 evidence builder 的停止条件。

本 Phase 没有读取或写入 canonical private PFI database，没有读取真实财务行，没有输出金额，没有部署 Cloudflare，没有修改 Alpha repository，也没有启动 Ralpha/Serenity-Alipay。官方网络研究只读取 `developers.cloudflare.com` 文档；产品和测试 runtime 外部网络调用为 0。

## Scope override

TaskPack 的 Stage 11 literal allowlist 包含 security/scripts/config/shared/context/test/docs/reports，但遗漏了本任务明确要求整改的现有 public surface，也遗漏了当前活动旧 Context adapter 与 release identity closure。standing authorization 下仅扩展以下必要范围，并保留 `allowed_files_obeyed=false`：

- `PFI/web/cloudflare-public/**`：把现有 pseudo-dashboard 收敛为真实静态边界。
- `PFI/src/pfi_v02/stage5_advice_report_alpha.py`、`stage6_e2e_stabilization.py`、`PFI/src/pfi_os/application/homepage_summary.py`、`PFI/web/app/shell.js`：移除活动金额型 Context 消费链。
- `PFI/src/pfi_v02/stage_v021_runtime_api.py`、`PFI/config/release_manifest.json`、`PFI/web/index.html`、release identity tests：把新 Context security/CLI/scanner/schema 和活动 adapter 纳入 backend identity，并同步 frontend hash。

没有扩大到 Stage 11 whole review、Stage 12、canonical DB、部署、push 或安装。

## Rollback

先 revert Phase 11.3 evidence/governance commit，再 revert product commit `890d38a759b9689a65152aa20527bde7ba04b52e`。由于没有 canonical DB、远端部署、App 安装或外部系统写入，不需要数据、Cloudflare、Alpha、App 或 GitHub 回滚。
