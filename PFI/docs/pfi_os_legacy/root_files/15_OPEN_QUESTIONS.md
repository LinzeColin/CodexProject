# 15 Open Questions / Unfinished Work

Last updated: 2026-06-13

These are the current unfinished items that future agents should preserve and work through one subsystem at a time.

1. **Vectorized Research Mode MVP**
   Read `EventReplay_latest.json`, rebuild OHLCV DataFrame, and connect to fast parameter scans without changing UI.

2. **Discrete Event Simulation Mode**
   Advance events one by one, model transaction cost, slippage, position state, and risk gates.

3. **Agent Market Simulation Mode**
   Feed deterministic replay events into an agent decision loop with full audit logs and no live order execution.

4. **Replay Cursor Pagination**
   Improve `next_after` for multiple events sharing the same timestamp by adding an event-id cursor.

5. **Bar Cache Replay**
   Extend Event Replay from `market_events` JSONL to structured `data/cache/<MARKET>/<interval>/<symbol>.csv/parquet`.

6. **Multi-Asset Replay**
   Support synchronized replay across multiple symbols and intervals with deterministic merge order.

7. **TradingView-like UX**
   Add chart, indicator, strategy selection, and scan controls after the simulation core is stable.

8. **Moomoo-like Realtime Research Flow**
   Add read-only OpenD adapter readiness, quote/event ingestion, and fail-closed status reporting. Do not enable unattended trading.

9. **52ETF Integration**
   Continue the 52ETF feature as a research/reference ingestion path with source logs and no unapproved scraping assumptions.

10. **Hotspot Analysis Performance**
   Keep reducing slow button-trigger behavior by caching, precomputing, or routing through lower-token summary artifacts.

11. **Workbench Consolidation**
   Continue reducing token pressure by merging overlapping workbench views into summary-first command surfaces.

12. **Business Subsystem Evidence Completion**
   CashFlow, Policy, and Consumption systems still need real reviewed evidence snapshots before total command center can become fully actionable.

13. **Full Test Suite Stability**
   Full pytest did not complete in the latest run. Identify slow/hanging tests and split smoke, target, and full gates clearly.

14. **Public GitHub Data Boundary**
   The GitHub repo is public. Do not upload private holdings, raw portfolio videos, SQLite runtime state, credentials, or local logs.

15. **Formal Audit Pack / ZIP Delivery**
   Regenerate `pfi_os_dev_audit_pack` only after the next stable subsystem run or when explicitly requested.
