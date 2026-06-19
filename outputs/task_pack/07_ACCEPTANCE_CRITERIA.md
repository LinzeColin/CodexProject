# 07 Acceptance Criteria

## MVP Acceptance

The MVP is acceptable only if all required items pass.

| Area | Criteria |
|---|---|
| Database | SQLite DB created with required tables |
| Run log | Every run has `run_id`, Beijing time, Australia/Sydney time, slot, status |
| Schedule | 10 Beijing slots from 08:30 through 17:30 are represented exactly |
| Import | Alipay CSV import works and validates required columns |
| Candidate universe | Conservative assets are excluded |
| Source chain | Every critical field has source or missing-data record |
| Scoring | Score maps to Action-Ready / Watch / Manual Review / Block |
| Risk gates | MDD >= 40.00% and recovery >= 1 year hard downgrade |
| Benchmarks | 1m, 3m, 10 trading day comparison present |
| Discipline | Current vs target deviation and action labels present |
| Notification | Mail-ready body generated for alert/info/warn |
| Safety | No automatic real trade action exists |

## Strategy Acceptance

- The system treats outperforming Shanghai Composite and S&P 500 as a strategy target.
- It blocks or downgrades additions when benchmark-relative performance fails.
- It never claims guaranteed future outperformance.

## Data Quality Acceptance

- Missing NAV/holding > 2 days creates Manual Review.
- Missing fee/redemption status creates No-New-Order.
- Official-grade source count < 2 prevents Action-Ready.
- Aggregated fallback is visible in report.
- Conflicts are visible in conflict log.

## Notification Acceptance

Urgent notification triggers for:

- Hard risk gate hit.
- Deviation > 1.00% with sufficient evidence.
- Top5 change rate > 20.00%.
- New Top5 asset >= 1.
- Replacement count >= 2.

Warn notification triggers for:

- Data quality insufficient.
- Fee/redemption status missing.
- Source conflict.
- Evidence insufficient despite deviation.

Info notification triggers for:

- Discipline check completed with no new action.
