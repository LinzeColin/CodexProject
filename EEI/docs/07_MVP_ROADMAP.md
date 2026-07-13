# 07 - MVP Roadmap

## 1. Delivery rule

MVP 由 acceptance gates 定义，不由页面数量或日历定义。推荐 15 个工作日等价工作量；7 天仅为 prototype，30 天为 robust extension。

## 2. Pursuing Goal Execution Roadmap

This section is a pursuing-goal reference for future bounded Run Contracts, not a standalone canonical task plan. Concrete execution must still bind to the governed task records, `acceptance_traceability`, validation commands, rollback, stop conditions, and current-result evidence before development starts.

### Stage 1 - Runtime, Data, API, and Core MVP Implementation

目标：补齐 EEI MVP 真实运行能力。

- Phase 1.1：PostgreSQL 数据库、迁移、schema、seed/fixture 策略。
- Phase 1.2：真实数据采集、实体解析、证据链、source/evidence schema。
- Phase 1.3：生产 API、递归图查询、评分服务、cache/search。
- Phase 1.4：模型配置版本、事务性激活、原子全局刷新。
- Phase 1.5：后台调度、自动唤醒、幂等、重试、dead-letter。
- Phase 1.6：服务端保存视图、冲突控制、恢复。

Phase 1.1 status (2026-07-13): `DONE_FOR_IMPLEMENTATION`. `T101/A005` proves an
isolated PostgreSQL 16 Compose clean start, health, SQL identity and full teardown
without restarting the active A209 PostgreSQL/worker containers. Existing
`T200-T208/A011-A028`, `T905/A119-A120` and `T1300/A201` evidence covers reversible
migrations, schema invariants and deterministic seed/fixture strategy. A026/A027
remain separate T904 production gold-set release-quality gates and do not become
PASS through Phase 1.1 closure. This status does not imply MVP release readiness.

Phase 1.2 status (2026-07-13): `IN_PROGRESS`. `T700-T703/A096-A103` are
implemented locally with a fail-closed SEC EDGAR client that requires a descriptive
application identity and operator contact email, allows only exact HTTPS SEC hosts,
does not follow redirects, and serializes every request attempt at a fixed `0.125s`
interval (`<=8 requests/sec`). Timeout, at most three attempts, bounded exponential
backoff/jitter and 429/503 handling are covered by mock HTTP. Successful raw JSON
response bytes are SHA-256 cached per canonical URL so unchanged content skips
duplicate downstream processing; this does not skip the network fetch or provide
persistent cache storage. Typed normalizers now preserve Submissions accession/form/
filed/report/accepted/document fields and Company Facts concept/unit/period/form/
filed/frame fields. Parallel-array drift, fixture-to-live relabeling and invalid
period/value semantics fail closed; `/A` filings and same-period revisions remain
separate records rather than being collapsed. Golden payloads are synthetic fixtures.
T703 adds explicit fixture and dry-run execution, structured checkpoint/count/status/
error reports, and idempotent PostgreSQL upsert: an isolated PostgreSQL 16 probe
inserted two source documents and two raw snapshots on the first run, reused all four
rows on the second run, and wrote nothing during dry-run. It also proved complete
temporary-resource cleanup without changing active A209 PostgreSQL/worker container
identity. T704 adds a PostgreSQL-backed `/v1/sources/freshness` API and connected UI
for connector attempt/success/failure, document date and report period. Latest report
period start/end stay paired to the same SEC fact period; retrieval time is never
substituted for document or report time. Isolated PostgreSQL integration covers a
latest-failure injection and cleanup, while browser E2E proves server hydration and
visible server-error behavior. No live SEC request is part of the acceptance evidence.
`T705-T706` remain open, and these tasks do not close `T1301/A202`, production ingestion, external source/
legal/owner clearance, A209, or MVP release readiness. Remote CI is pending.

每个 task 必须绑定已有 Acceptance IDs；如果 `acceptance_traceability` 没有映射，先记录 gap，不直接开发。

### Stage 2 - Frontend, Scale, and Operational Evidence

目标：把 EEI 变成可运行、可验证、可交互的 MVP。

- Phase 2.1：生产组件化前端、真实路由、真实控件连接。
- Phase 2.2：商业版图、集团结构、业务板块、供应链、资本网络、并购交易、控制关系、政策环境、战略信号、时间演变、证据中心、模型中心、数据中心、我的关注、探索记录、系统状态等导航功能落地。
- Phase 2.3：10k、100k、1m 关系规模测试。
- Phase 2.4：4h soak、24h soak、A209 release gate。
- Phase 2.5：品牌法律与市场清权记录。
- Phase 2.6：release evidence、finalization、governance sync、CI 或本地等价验证。

### Stage 3 - MVP v0.1 Release Acceptance

目标：只在所有 release gate 通过后进入 release-ready。

- Phase 3.1：`validate_operator_soak_evidence.py validate --require-release-ready` PASS。
- Phase 3.2：`make verify` PASS。
- Phase 3.3：release decision bundle / external evidence bundle / governance validators PASS。
- Phase 3.4：commit、push、CI 或明确本地等价证据。
- Phase 3.5：最终交付说明，列出剩余非 MVP 项和风险。

### Execution Rules

- 每轮只执行一个 bounded Run Contract。
- 每个 task 必须有 Acceptance IDs、验证命令、风险、回滚、停止条件。
- 不在主仓库直接开发。
- 不混入 ADP/PFI/Alpha/Serenity。
- 不伪造通过，不声明 MVP ready。
- A209 24h soak 是 Stage 2/3 release gate，不阻塞 Stage 1/2 功能开发，但最终 release-ready 前必须通过。

## 3. Gates

### G0 - Plan and ADR

输出 exact files、commands、tests、risks、rollback；ADR 覆盖 graph budget、URL state、score versioning、append-only log、14-day calibration。

### G1 - Platform

Monorepo、Compose、Makefile、health、lockfiles、CI skeleton。

### G2 - Data foundation

Schema、migrations、30 P0 seed、140 research universe、industry/supply-chain taxonomy、fixtures、data checks。

### G3 - Home and discovery

行业、Watchlist、search、recent paths、changes、freshness、model status。

### G4 - Recursive explorer

Explore API、reroot、expand、breadcrumb、URL/back state、graph budget、table fallback、three-reroot E2E。

### G5 - Company empire and supply chain

八层焦点页、business/structure、supply-chain stages、paths、human summary、evidence drawer。

### G6 - Models and governance

Formula explain、default/custom profiles、preview/save/activate/rollback/reset、operation logs、14-day calibration。

### G7 - Live provenance

SEC connector、snapshot/hash/idempotency/freshness/change。

### G8 - Capital/policy/strategy

Capital River、M&A、policy map、strategic signals、timeline、export。

### G9 - Release

Performance、a11y、security、failure injection、migration rollback、clean-room run、release report。

## 4. MVP demo narrative

1. 首页进入半导体行业；
2. 打开 NVIDIA fixture；
3. 阅读人类摘要；
4. 查看全链条阶段；
5. reroot 到 foundry -> equipment -> materials；
6. 返回原路径，跳到数据中心 -> 电力；
7. 调整供应链权重，preview 并保存；
8. 查看日志；
9. 运行 calibration fixture；
10. 打开证据、时间和 unknown；
11. 导出研究路径。

## 5. Scope control

- 一次一个 Gate；
- P0 失败时不得进入下一 Gate；
- live connector 不能阻塞 fixture-based UX；
- 不在 G4 前做复杂图数据库优化；
- 不为演示牺牲 provenance、unknown、tests 或 rollback。
