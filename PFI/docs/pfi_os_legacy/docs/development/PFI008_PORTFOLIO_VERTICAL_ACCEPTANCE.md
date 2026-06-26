# PFI-008 Portfolio Vertical Acceptance

Last updated: 2026-06-20 Australia/Sydney

PFI-008 advances Gate 3 for the Portfolio vertical slice. The acceptance goal
is a local, review-only chain from deterministic synthetic portfolio imports
into holding snapshot, reconciliation, corporate-action/FX/cash Golden checks,
risk constraints, decision proposal, same-shell Chinese UI controls,
Operational Store evidence, and rollback proof.

## Scope

- Workspace: `持仓`.
- Schema: `PFI008PortfolioVerticalAcceptanceV1`.
- UI read model: `PFI008PortfolioUIReadModelV1`.
- Source mode: deterministic synthetic import ledger.
- Storage mode: temporary Operational Store only.
- Safety: research-only, synthetic fixture only, no real broker connection, no
  broker calls, no live trading, no order execution, no holding mutation, and
  human review required.

## Acceptance Chain

`src/pfi_os/application/pfi008_portfolio_acceptance.py` proves:

- Data chain: synthetic multi-broker import ledger plus cash ledger -> reviewed
  holdings frame.
- Golden chain: one corporate-action adjustment, one FX conversion, one cash
  balance, stable total position value, and stable holding snapshot checksum.
- Domain chain: Phase B Portfolio workflow creates private-derived holding
  snapshot, quality/exposure/risk cards, and decision-support payload.
- Reconciliation chain: imported symbols and ledger value reconcile to the
  Operational Store holding snapshot.
- API/read-model chain: `PFI008PortfolioUIReadModelV1` exposes the portfolio
  route, primary feature view, reconciliation, Golden inputs, optimizer
  constraints, decision proposal, and safety boundary.
- UI chain: Web Shell has same-shell Chinese panels for `持仓垂直切片`,
  `导入对账`, `风险约束`, and `决策提案`.
- Optimizer/decision chain: max single, top3, cash buffer, and disabled
  auto-rebalance constraints are evaluated; target weight change remains `0.0`
  and no order intent is created.
- Evidence/task chain: source, evidence, completed job, human-review task, and
  private-derived holding snapshot records are written to Operational Store.
- Rollback proof: temporary source/evidence/job/task/snapshot rows are deleted
  and residue counts are zero.

## Runtime Evidence

Current local run:

```bash
scripts/pfi008PortfolioAcceptance.sh --summary-json
```

Observed:

- `status=Pass`
- `pass=16`
- `fail=0`
- `holding_count=5`
- `import_record_count=5`
- `broker_count=3`
- `constraint_violation_count=2`
- `reconciliation_status=Pass`
- `rollback_status=Pass`
- Focused PFI-008 contract: 6 passed.
- Related PFI-008/Web Shell/script contracts: 58 passed.
- Target gate: 64 passed, secret scan passed, `git diff --check` passed.

## Verification Commands

```bash
python -m pytest tests/contract/test_pfi008_portfolio_vertical_acceptance.py -q
scripts/pfi008PortfolioAcceptance.sh --summary-json
python -m pytest tests/contract/test_phase_b_portfolio_workflow.py tests/contract/test_pfi008_portfolio_vertical_acceptance.py -q
python -m pytest tests/contract/test_pfi_web_shell_contract.py tests/e2e/test_pfi_web_shell_static_flow.py tests/test_scripts.py -q
scripts/pfiGate.sh target
git diff --check
```

## Stop Condition

PFI-008 is locally closed when the PFI-008 contract tests pass, the acceptance
script returns `status=Pass`, target gate remains green, and GitHub CI passes.
With PFI-006 through PFI-009 now covered by local vertical acceptances, Gate 3
is closed for the current evidence scope and must be re-run in the final Gate 7
release package.
