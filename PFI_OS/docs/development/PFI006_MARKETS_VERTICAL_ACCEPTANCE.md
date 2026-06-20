# PFI-006 Markets Vertical Acceptance

Last updated: 2026-06-20 Australia/Sydney

PFI-006 advances Gate 3 for the Markets vertical slice. The acceptance goal is
not to fetch live market data. It is to prove a complete local-first research
chain from deterministic observed market bars into reviewable UI, evidence,
tasks, saved views, alerts, Golden metrics, and rollback proof.

## Scope

- Workspace: `市场`.
- Schema: `PFI006MarketsVerticalAcceptanceV1`.
- UI read model: `PFI006MarketsUIReadModelV1`.
- Source mode: deterministic local Golden fixture.
- Storage mode: temporary Operational Store only.
- Safety: research-only, no provider fetch, no broker calls, no order
  execution, no private holdings.

## Acceptance Chain

`src/pfi_os/application/pfi006_markets_acceptance.py` proves:

- Data chain: local observed bars -> `PFIOSMarketEventLogV1`.
- Domain chain: market event card, hotspot card, sentiment card, and
  decision-support object.
- API/read-model chain: `PFI006MarketsUIReadModelV1` exposes the market route,
  primary feature view, card summaries, alerts, saved views, and portfolio
  overlay.
- UI chain: Web Shell has same-shell Chinese panels for `市场垂直切片`,
  `组合影响覆盖层`, and `提醒与保存视图`.
- Evidence/task chain: source, evidence, completed job, and human-review task
  records are written to Operational Store.
- Portfolio overlay: target weight change is fixed at `0.0`, private holdings
  are not read, and portfolio effect remains a review input.
- Alert/saved view: freshness and hotspot divergence reminders plus read-only
  saved views are present.
- Golden metrics: workflow id, checksum, event count, symbol count, focus rows,
  confidence, alert count, and saved-view count are deterministic.
- Rollback proof: temporary source/evidence/job/task rows are deleted and
  residue counts are zero.

## Runtime Evidence

Current local run:

```bash
scripts/pfi006MarketsAcceptance.sh --summary-json
```

Observed:

- `status=Pass`
- `pass=13`
- `fail=0`
- `event_count=90`
- `alert_count=2`
- `saved_view_count=2`
- `rollback_status=Pass`
- Focused Markets/Web Shell contracts: 62 passed.
- Target gate: 52 passed, secret scan passed.
- UI visual acceptance after Web Shell market changes: 98 passed, 0 failed.
- `git diff --check`: passed.

## Verification Commands

```bash
python -m pytest tests/contract/test_pfi006_markets_vertical_acceptance.py -q
scripts/pfi006MarketsAcceptance.sh --summary-json
python -m pytest tests/contract/test_phase_b_markets_workflow.py tests/contract/test_pfi006_markets_vertical_acceptance.py -q
python -m pytest tests/contract/test_pfi_web_shell_contract.py tests/e2e/test_pfi_web_shell_static_flow.py tests/test_scripts.py -q
scripts/pfiGate.sh target
git diff --check
```

## Stop Condition

PFI-006 is locally closed when the PFI-006 contract tests pass, the acceptance
script returns `status=Pass`, target gate remains green, and GitHub CI passes.
With PFI-006 through PFI-009 now covered by local vertical acceptances, Gate 3
is closed for the current evidence scope and must be re-run in the final Gate 7
release package.
