# 01 Requirements

## Confirmed Schedule

All primary runs use Beijing time first. Australia/Sydney time is display-only and must be computed through IANA timezone data.

| Slot | Beijing Time | Purpose |
|---|---:|---|
| R1 | 08:30 | A-share pre-open fund candidate warmup |
| R2 | 09:30 | A-share open snapshot and anomaly check |
| R3 | 10:30 | Morning intraday comparison |
| R4 | 11:30 | Pre-lunch discipline audit |
| R5 | 12:30 | Midday evidence refresh and regime check |
| R6 | 13:30 | Main decision preview and target weight lock |
| R7 | 14:30 | Final pre-cutoff fee/status/evidence review |
| R8 | 15:30 | Post-cutoff review and next-day plan |
| R9 | 16:30 | Post-close archive and day comparison |
| R10 | 17:30 | Final daily archive and next-run preparation |

## Functional Requirements

1. Create a unique `run_id` for every run.
2. Persist raw inputs, normalized snapshots, scores, recommendations, notifications, and audit records.
3. Import current Alipay holdings from CSV/template in MVP.
4. Build a fund-first candidate universe.
5. Exclude conservative assets: bonds, money-market funds, Yu'e Bao, cash-management products, conservative structured products.
6. Score by data completeness, timeliness, source credibility, benchmark-relative return, risk, and execution feasibility.
7. Enforce hard risk gates:
   - Max drawdown >= 40.00% means Block / Clear / Reduce.
   - Recovery time to prior high >= 1 year means Manual Review or Block.
8. Compare each candidate against:
   - Shanghai Composite: 1 month, 3 months, latest 10 trading days.
   - S&P 500: 1 month, 3 months, latest 10 trading days.
9. Generate target weights for Top5 candidates.
10. Compare target weights with current holdings.
11. Trigger action labels: Maintain, Increase, Reduce, Pause New, Postpone, Clear, Manual Review, Block.
12. Trigger alerts when:
   - Deviation > 1.00%.
   - Top5 change rate > 20.00%.
   - New Top5 asset >= 1.
   - Replacement count >= 2.
   - Key field change > 1 sigma.
   - 7-day drawdown worsens > 5.00%.
   - Single position over-expansion occurs > 2 consecutive runs.
13. Generate Mail-ready notification content for `linzezhang35@gmail.com`.
14. Support dry-run mode by default.

## Non-Functional Requirements

- Local-first, reproducible, auditable.
- Minimal external dependencies.
- Deterministic scoring for same input.
- Explicit source chain for every critical field.
- No silent fallback.
- No hardcoded secrets.
- Clear run status: success, degraded, failed, blocked.
- CLI-first MVP; UI optional.

## Data Freshness Requirements

- NAV and holdings missing > 2 consecutive days: Manual Review.
- Fee or redemption status missing: No-New-Order.
- Official-grade source count < 2: cannot be Action-Ready.
- Aggregated-source fallback must be marked `fallback_aggregated=true`.

## Report Requirements

Each run report must include:

- Run metadata.
- Top5 and target weights.
- Current vs target deviation.
- Benchmark comparison.
- Drawdown and recovery-time metrics.
- Fees and redemption/subscription status.
- Evidence chain.
- Missing data and conflicts.
- Action labels.
- Notification summary.
- Next review time.
