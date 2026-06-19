# 07 - MVP Roadmap

## 1. Delivery rule

MVP 由 acceptance gates 定义，不由页面数量或日历定义。推荐 15 个工作日等价工作量；7 天仅为 prototype，30 天为 robust extension。

## 2. Gates

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

## 3. MVP demo narrative

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

## 4. Scope control

- 一次一个 Gate；
- P0 失败时不得进入下一 Gate；
- live connector 不能阻塞 fixture-based UX；
- 不在 G4 前做复杂图数据库优化；
- 不为演示牺牲 provenance、unknown、tests 或 rollback。
