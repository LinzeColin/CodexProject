# PHASE S1-06 Scoring Queue Ledger

- task_id: `S1-06-SCORING-QUEUE-LEDGER-001`
- date: `2026-06-22`
- status: `completed`
- production_acceptance_claimed: `false`
- production_schedule_enabled: `false`
- real_smtp_sent: `false`
- real_release_uploaded: `false`

## Scope

Implemented the deterministic Stage 1 scoring, queue, and text-first content
ledger contract:

- 100-point research scoring from owner-controlled component weights;
- queue-priority scoring with deterministic tie ordering;
- 10,000 active item cap;
- inclusive 365-day age boundary and 366-day eviction;
- source-share cap behavior when multiple sources exist;
- lifecycle reason codes for retracted, superseded, reactivated, old, future,
  source-cap, and capacity outcomes;
- canonical text-first `CONTENT_LEDGER.csv` with report/email/video state
  columns; video fields remain `NOT_APPLICABLE` under the active V5 text
  delivery baseline.

## Verification

- focused owner/stage1/CLI tests: `18 tests OK`
- full arxiv-daily-push tests: `200 tests OK`
- semantic extractor: `41 active formulas and 292 active parameters checked`
- `git diff --check`: `PASS`

## Boundary

S1-06 proves deterministic fixture scoring and queue behavior. It does not
claim B1 report quality, real email delivery, scheduler readiness, two live
days, 30 historical previews, or `ARXIV_PRODUCTION_ACCEPTED`.
