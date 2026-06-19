# 11 - Architecture and Product Decision Log

Append decisions; do not rewrite history.

## ADR-001 - PostgreSQL before graph database

**Status**: Accepted  
**Decision**: relational edge tables + bounded graph API。  
**Reason**: bounded queries、provenance/time constraints、lower operations。  
**Revisit**: measured p95 fails at expected scale or unbounded algorithms become P0。

## ADR-002 - Five coordinated views

**Status**: Accepted  
**Decision**: power、capital、signals、dossier、changes 分视图协同。  
**Reason**: 单一网络无法准确同时编码结构、金额、时间、证据和 uncertainty。

## ADR-003 - SEC first connector

**Status**: Accepted  
**Decision**: submissions/companyfacts live；private-company facts 用 curated official fixtures。  
**Reason**: strong IDs、official API、repeatability、provenance。

## ADR-004 - No direct investment signal

**Status**: Accepted  
**Decision**: Radar 显示证据组成，不显示 buy/sell 或 return probability。  
**Reason**: source lag、private-data gaps、model uncertainty。

## ADR-005 - Canonical LLM extraction deferred

**Status**: Accepted  
**Decision**: deterministic parsing + curated records 为 canonical。  
**Reason**: facts must be reproducible；LLM 以后仅提出 review candidates。

## Pending G0 decisions

- 精确 pinned versions。
- pnpm/uv workspace layout。
- people unified table vs dedicated table + unified API。
- graph layout worker/browser support。
- signal prototype thresholds/weights。

## ADR-006 through ADR-015 - 2026-06-19 - Phase 0 architecture freeze

**Status**: Accepted

**Decision**: The Phase 0 plan freezes the MVP architecture through ten ADR files under `docs/adr/`: runtime/repository layout, production database, graph query, API contract, calculation/snapshots, cache, search, frontend visualization, data ingestion, and fixture/live separation.

**Reason**: The pursuing goal now requires implementation toward MVP, so architecture choices must be explicit before product code expands.

**Consequences**: G1 and later gates must preserve Acceptance ID traceability and may not replace PostgreSQL, bounded graph queries, snapshot-scoped responses, fixture/live separation, or model-version immutability without a new ADR.


## D-UI-003 - 2026-06-19 - Visual workspace replaces industry card home

**Decision**: The default home is the current company graph workspace, selected from recent session or Watchlist. Industry is a side entry/empty state.

**Reason**: The product value is relationship exploration; an intermediate card dashboard delays the primary task and weakens visual continuity.

**Consequences**: Rewrite IA, state restoration, acceptance tests and copy. Retain industry taxonomy as navigation, not as a mandatory landing page.
