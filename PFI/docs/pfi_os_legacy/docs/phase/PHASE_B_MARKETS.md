# Phase B Markets Vertical Slice

Schema: `PFIOSPhaseBMarketsContractV1`

Status: first Markets vertical slice complete.

As of: 2026-06-19 Australia/Sydney

## Goal

Make the Markets workspace produce reviewable market evidence from local
observed bars before Phase C worker scheduling and 60-second Fast Path are
implemented.

## Current Slice

- Adds `pfi_os.application.markets_workflow`.
- Declares workflow schema `PFIOSPhaseBMarketsWorkflowV1`.
- Consumes already-observed local bars; provider fetch and live push remain
  Phase C concerns.
- Builds a Market Event Log using `pfi_os.data.market_events`.
- Builds hotspot summaries using `pfi_os.analysis.market_hotspots`.
- Builds sentiment summaries using `pfi_os.analysis.sentiment`.
- Emits compact market cards for events, hotspots, and sentiment.
- Exposes data freshness, source ids, evidence class, and coverage metadata.
- Emits a decision-support object with thesis, catalysts, counter-evidence,
  invalidation conditions, risks, model versions, source ids, and
  `human_review_required: true`.
- Writes Markets source, evidence, job, and review-task records into the
  Operational Store.

## Contract Tests

- `tests/contract/test_phase_b_markets_workflow.py`

The tests verify:

1. Markets workflow contract fields and non-regression constraints.
2. Market event, hotspot, and sentiment cards are produced from local bars.
3. Data freshness and source ids are visible on every card.
4. Decision-support output includes counter-evidence and invalidation
   conditions.
5. Workflow ids and event checksums are stable for identical inputs.
6. Operational Store receives source, evidence, job, and human-review task
   records.
7. No live trading, broker call, or order execution path is exposed.

## Out Of Scope

- Phase C fetch worker, scheduler, retry/backoff, SSE/WebSocket, and 60-second
  Fast Path acceptance.
- Direct provider fetching inside this workflow.
- Portfolio impact calculations that require private holdings.
- Full Web Shell Markets UI migration.
- Research + Policy and Portfolio vertical slices are covered by their Phase B
  workflow docs.

## Next Iterations

1. Promote the Phase B workflow set into Web Shell read models.
2. Start Phase C worker/reliability only after the four Phase B workflows have
   evidence contracts.
