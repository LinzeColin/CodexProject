# 10 - Update, Scheduling and Phase 2

## 1. Two separate schedules

### Data updates

按来源驱动：SEC 增量、官方公告、政府数据等各自有 cadence 和 disclosure lag。每日检查不代表所有事实每日变化。

### Model calibration

固定每 14 天一次，与数据抓取分开。校准检查覆盖、漂移、质量和参数敏感性；不自动激活建议。

## 2. Pipeline

```text
schedule -> fetch -> raw snapshot -> hash -> normalize -> validate
-> entity resolve -> transactional upsert -> derive -> score
-> diff/change -> freshness -> alerts -> report
```

相同 snapshot/profile 重跑幂等。失败不 partial publish。

## 3. Suggested source cadence

- SEC submissions: filing-hours incremental or daily batch；
- Company Facts: daily + filing-triggered；
- 13F: filing season checks but retain quarterly semantics；
- USAspending/GLEIF/LDA/USPTO/EIA: source-specific daily/weekly/monthly；
- company official announcements: event-driven watch queue；
- derived scores: only after successful data batch；
- calibration: every 14 days。

## 4. Change detection

- new/updated/superseded/revoked/conflict/stale/failure；
- new supplier/customer/contract；
- control or ownership threshold change；
- M&A status transition；
- facility/capacity/energy change；
- policy/export/regulatory change；
- source failure or score drift。

## 5. Phase 2 connectors

Prioritize:

1. USAspending；
2. GLEIF；
3. LDA；
4. USPTO；
5. FTC/DOJ；
6. EIA/energy/facility sources；
7. 13F/N-PORT/ADV；
8. optional licensed data adapters。

Every connector must preserve source-specific semantics and pass contract tests.

## 6. Review workflow

Phase 2 adds candidate queue, human approve/reject, conflict resolution and bounded alerts. LLM may propose candidates but cannot publish facts without deterministic validation/review.
