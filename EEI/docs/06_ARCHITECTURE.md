# 06 - Architecture

## 1. System shape

```text
Next.js Web
  -> Home / Industry / Focus Workspace / Models / Calibrations
  -> FastAPI OpenAPI service
      -> PostgreSQL system of record
      -> Ingestion package
      -> Graph query service
      -> Scoring service
      -> Calibration scheduler/worker
      -> Export service
```

## 2. Web

- Next.js App Router + TypeScript strict；
- Cytoscape.js 用于有界关系网络；
- ECharts 用于供应链阶段、Sankey、timeline、matrix；
- server components 用于首页/档案初始数据；
- client state 管理 reroot、pins、selection 和 layout；
- URL 是可分享/恢复的 canonical exploration state；
- 表格替代视图与 evidence drawer 为 P0。

## 3. API services

- identity/search；
- industry landscape；
- recursive explore/reroot/expand；
- path queries；
- entity empire/supply-chain/capital/policy/strategy；
- watchlists；
- scoring model/profile/preview/explain；
- operation logs；
- calibration runs；
- ingestion/freshness/change/export。

契约见 `specs/api_contract.yaml`。

## 4. Graph query strategy

MVP 使用 PostgreSQL edge tables 和 bounded recursive CTE：

- root + direction + families + as-of；
- hops <=2；
- materiality/evidence/profile 排序；
- max nodes/edges；
- cursor-based expansion；
- path length <=8；
- explain truncation。

不引入 Neo4j，除非 benchmark/ADR 证明 PostgreSQL 不能满足路径和性能门槛。

## 5. Scoring service

纯函数优先：

```text
facts + evidence + as-of + model version + profile version
  -> normalized inputs
  -> component scores
  -> raw priority
  -> evidence quality
  -> adjusted priority
  -> explanation
```

所有运行保存 snapshot/hash 和 contributions。Preview 使用临时参数，不写正式结果；保存 profile 后异步/事务性重算。

## 6. Calibration scheduler

- cadence = 14 days；
- manual trigger；
- 基于最近 successful snapshot；
- 产生 coverage/drift/quality/proposal；
- proposal 不自动 activate；
- 失败写 change feed 和 operation log；
- fixture clock 支持 deterministic tests。

## 7. Ingestion

Connector interface：

```python
fetch -> snapshot -> normalize -> validate -> resolve -> upsert -> derive -> report
```

- dry-run/fixture/live；
- raw snapshot + hash；
- transactional batch；
- retry/circuit breaker；
- replay-safe checkpoint；
- source-specific semantics preserved。

## 8. Observability

- request ID 和 session ID；
- graph query budget/latency/truncation；
- reroot count and failure；
- scoring run/profile version；
- calibration status；
- source freshness and ingest errors；
- no secrets or full sensitive payloads in logs。

## 9. Failure behavior

- DB failure：read-only stale cache 可选，禁止假装成功；
- scoring failure：显示上次成功结果和 stale 标记；
- calibration failure：active profile 不变；
- source failure：不 partial publish；
- graph over-budget：返回 truncated + reason + continuation；
- invalid weights：422，不写 profile/log success。

## 10. Deployment

MVP local Docker Compose。环境变量通过 `.env.example`；网络默认 off；production deployment 属 Robust track。
