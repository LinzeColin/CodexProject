# Phase B Portfolio Vertical Slice

Schema: `PFIOSPhaseBPortfolioContractV1`

Status: first Portfolio vertical slice complete.

As of: 2026-06-20 Australia/Sydney

## Goal

Make the Portfolio workspace produce reviewable private holding, exposure,
concentration, and risk evidence before Phase C worker scheduling and Phase D
local model/deployment work.

## Current Slice

- Adds `pfi_os.application.portfolio_workflow`.
- Declares workflow schema `PFIOSPhaseBPortfolioWorkflowV1`.
- Consumes reviewed private holdings or sanitized fixtures only.
- Canonicalizes holdings through the existing holdings book adapter.
- Classifies the workflow output as `PRIVATE_DERIVED`.
- Builds private holding snapshot metadata, quality rows, exposure rows,
  concentration metrics, risk-review actions, and position guardrails.
- Emits compact Portfolio cards for private holdings, exposure/concentration,
  and risk review.
- Emits decision-support output with thesis, catalysts, counter-evidence,
  invalidation conditions, risks, portfolio effect, model versions, source ids,
  and `human_review_required: true`.
- Writes Portfolio source, evidence, job, human-review task, and holding
  snapshot records into the Operational Store.

## PFI-008 Promotion

PFI-008 promotes this Phase B workflow into a Gate 3 Portfolio acceptance
contract:

- `src/pfi_os/application/pfi008_portfolio_acceptance.py`
- `tests/contract/test_pfi008_portfolio_vertical_acceptance.py`
- `scripts/pfi008PortfolioAcceptance.sh`
- `docs/development/PFI008_PORTFOLIO_VERTICAL_ACCEPTANCE.md`

The promotion adds deterministic synthetic import ledgers, corporate-action
adjustment, FX conversion, cash Golden checks, broker-to-snapshot
reconciliation, optimizer constraints, a review-only decision proposal,
same-shell Chinese Web Shell controls, and rollback proof. The acceptance
remains synthetic and private-safe: it does not connect to real brokers, mutate
holdings, create order intent, or submit orders.

## Contract Tests

- `tests/contract/test_phase_b_portfolio_workflow.py`
- `tests/contract/test_pfi008_portfolio_vertical_acceptance.py`

The tests verify:

1. Portfolio workflow contract fields and non-regression constraints.
2. Private holdings are classified as `PRIVATE_DERIVED`.
3. Holding snapshots are persisted through Operational Store
   `holding_snapshots`.
4. Quality, exposure, concentration, risk-review, card, and decision fields are
   visible.
5. Workflow ids and holding snapshot checksums are stable for identical inputs.
6. Empty holdings block downstream use without creating order intent.
7. No live trading, broker call, order execution, holding mutation, or public
   Git private-data path is exposed.
8. PFI-008 import, reconciliation, risk-constraint, decision-proposal,
   same-shell UI, script, target-gate, and rollback contracts are wired.

## Out Of Scope

- Phase C worker scheduling, retry/backoff, SSE/WebSocket, and 60-second Fast
  Path acceptance.
- Broker or account integration.
- Automatic rebalancing, order routing, payment, or real-money execution.
- Public Git storage of private holdings, account screenshots, raw imports,
  Operational SQLite, local logs, tokens, or secrets.

## Next Iterations

1. Continue Gate 3 with PFI-009 Strategy vertical acceptance.
2. Start Phase C worker/reliability only after the four Phase B workflows have
   evidence contracts.
3. Keep Portfolio outputs private-derived until explicit public-safe summaries
   are designed and contract-tested.
