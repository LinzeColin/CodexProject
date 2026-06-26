# PFI UX Contract

Version: PFI-001

PFI OS should feel like a dense, professional research workstation for repeated
daily use. It should not feel like a collection of scripts, internal buses, or
decorative dashboards.

## Page Shape

Every major page follows this order:

1. One-sentence conclusion
2. Data freshness and evidence status
3. Three to five key metrics
4. Main chart or main table
5. Impact, risk, and recommendation
6. Counter-evidence and invalidation conditions
7. Right evidence/parameter drawer
8. Recent history and executable next step

## Feedback SLA

| Time | Required feedback |
| --- | --- |
| 0-100ms | hover, pressed, focus, disabled state, or local state feedback |
| 100-300ms | page switch or cached result |
| over 300ms | skeleton or spinner |
| over 1s | explicit step, progress, and current phase |
| over 10s | background job with job id; user can leave the page |
| completion | toast plus local page update and result link |
| failure | inline error plus toast, retry, and cache fallback explanation |

## Interaction Rules

- Use business language, not script, worker, SQLite, bus, or internal module
  language.
- Do not use color as the only status signal.
- Important clickable targets are at least 44px.
- Tables support compact display, sort, filter, row selection, and export
  interface when relevant.
- Loading, empty, error, stale, blocked, and success states must be explicit.
- Long tasks never block the whole UI.
- All write actions require confirmation, undo, or explicit rollback path.
- A suggestion cannot be a bare buy/sell label. It must include action,
  horizon, evidence class, confidence, portfolio effect, risks, invalidation
  conditions, model versions, source ids, and `human_review_required: true`.

## Strategy Lab UX

- Backtest pages must show data range, provider, adjustment mode, strategy
  version, parameter set, costs, and run id before results are interpreted.
- Parameter-scan pages must show grid size, overfitting warning, stability,
  train/test status, and walk-forward status.
- Training mode must hide future bars before answer reveal and must not output
  live trading instructions.
- Market-feel training is for chart-reading practice and review, not a signal
  engine.
