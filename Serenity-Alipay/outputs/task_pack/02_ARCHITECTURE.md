# 02 Architecture

## Recommended MVP Architecture

```text
serenity_daily_analysis/
  app/
    cli.py
    config.py
    scheduler.py
    db.py
    models.py
    adapters/
      moomoo_adapter.py
      alipay_importer.py
      fund_official_adapter.py
      aggregator_adapter.py
      mail_notifier.py
      macos_notifier.py
    core/
      universe.py
      quality.py
      metrics.py
      scoring.py
      benchmarks.py
      discipline.py
      comparison.py
      reporting.py
      audit.py
    templates/
      alipay_positions_template.csv
      mail_urgent.md
      mail_info.md
      mail_warn.md
  data/
    serenity_daily.sqlite
    imports/
    reports/
    notifications/
  tests/
```

## Component Responsibilities

| Component | Responsibility |
|---|---|
| CLI | Run one slot, import holdings, generate report, test notification |
| Config | Paths, timezone, thresholds, source priorities, dry-run |
| Scheduler | Map Beijing slots to local execution; MVP can be manual or launchd-ready |
| DB | SQLite schema creation, migrations, transactions |
| Moomoo Adapter | Preferred market K-line/index/quote source; fail explicit if unavailable |
| Alipay Importer | Read CSV/template holdings and platform evidence |
| Fund Official Adapter | Store fund company official rule/NAV evidence; MVP may use manual URL snapshots |
| Aggregator Adapter | Fallback only, always downgraded |
| Quality Engine | Missing, stale, duplicate, abnormal, conflict checks |
| Metrics Engine | Return, volatility, MDD, recovery time, benchmark comparison |
| Scoring Engine | Rule-based deterministic score |
| Discipline Engine | Target/current deviation and action labels |
| Comparison Engine | Same-day, previous-day, previous-week, previous-month comparison |
| Reporting | Markdown report and notification body generation |
| Notifiers | Mail-ready files, optional Apple Mail send, local notification |

## Data Flow

1. Load config and create `run_id`.
2. Resolve schedule slot and timezone display.
3. Ingest holdings import if available.
4. Ingest candidate universe.
5. Fetch or load market/fund data by source priority.
6. Normalize snapshots.
7. Run data quality checks.
8. Compute metrics and benchmark comparison.
9. Score candidates.
10. Apply hard gates.
11. Generate Top5 and target weights.
12. Compare with current holdings.
13. Generate report and notifications.
14. Persist all outputs.

## Failure Mode

No silent success. A run can be:

- `success`: all key data present and no critical conflict.
- `degraded`: fallback or partial data used; no Action-Ready unless rules permit.
- `manual_review`: user confirmation needed.
- `blocked`: critical data/risk/execution gate failed.
- `failed`: runtime error, database error, or unavailable required local resource.

