# PFI-009 Strategy Vertical Acceptance

Last updated: 2026-06-20 Australia/Sydney

PFI-009 closes the current Gate 3 vertical-slice evidence set for Strategy
Lab. The acceptance goal is a local, review-only chain from deterministic
point-in-time bars into PIT backtest, train/test validation, walk-forward
validation, market-feel training, strategy model registry, runtime
cancel/resume proof, Operational Store evidence, same-shell Chinese UI
controls, and rollback proof.

## Scope

- Workspace: `策略实验室`.
- Schema: `PFI009StrategyVerticalAcceptanceV1`.
- UI read model: `PFI009StrategyUIReadModelV1`.
- Model registry schema: `PFI009StrategyModelRegistryV1`.
- Source mode: deterministic synthetic PIT Golden fixture.
- Storage mode: temporary Operational Store only.
- Safety: research-only, synthetic fixture only, no provider fetch, no broker
  calls, no live trading, no order execution, no live signal, no holding
  mutation, and human review required.

## Acceptance Chain

`src/pfi_os/application/pfi009_strategy_acceptance.py` proves:

- Data chain: deterministic PIT OHLCV bars with stable checksum.
- Golden chain: one corporate-action adjustment plus one delisted symbol
  excluded from the PIT universe.
- Domain chain: Phase B Strategy Lab workflow creates reproducible backtest
  evidence and decision-support fields.
- Backtest chain: execution model remains `target_weight_next_bar_open`, so
  signals are executed on the next bar rather than using same-bar future data.
- Train/test chain: training period ends before testing period starts and the
  validation status is `Pass`.
- Walk-forward chain: each rolling train window ends before its test window and
  the validation status is `Pass`.
- Training chain: market-feel training remains retained and hides future bars
  before answer reveal.
- Model registry chain: strategy candidate is registered as review-only with
  `order_enabled=false` and `live_signal_enabled=false`.
- Runtime chain: durable job lifecycle proves cancel, resume, claim, and
  complete around the strategy acceptance job.
- Evidence/task chain: source, evidence, completed job, and human-review task
  records are written to Operational Store.
- UI chain: Web Shell has same-shell Chinese panels for `策略垂直切片`,
  `PIT回测`, `样本外验证`, `滚动验证`, and `策略注册`.
- Rollback proof: temporary source/evidence/job/task/runtime rows are deleted
  and residue counts are zero.

## Runtime Evidence

Current local run:

```bash
PFI_PYTHON=/private/tmp/pfi_os_ci_repro/bin/python scripts/pfi009StrategyAcceptance.sh --summary-json
```

Observed:

- `status=Pass`
- `pass=18`
- `fail=0`
- `bar_count=360`
- `trade_count=53`
- `train_test_status=Pass`
- `walk_forward_status=Pass`
- `walk_forward_window_count=2`
- `registered_model_count=1`
- `runtime_resume_count=1`
- `rollback_status=Pass`
- Focused PFI-009 contract: 7 passed.
- Related PFI-009/Strategy/Web Shell/script contracts: 63 passed.
- Target gate: 71 passed, secret scan passed, `git diff --check` passed.

## Verification Commands

```bash
python -m pytest tests/contract/test_pfi009_strategy_vertical_acceptance.py -q
scripts/pfi009StrategyAcceptance.sh --summary-json
python -m pytest tests/contract/test_phase_b_strategy_lab_workflow.py tests/contract/test_pfi009_strategy_vertical_acceptance.py -q
python -m pytest tests/contract/test_pfi_web_shell_contract.py tests/e2e/test_pfi_web_shell_static_flow.py tests/test_scripts.py -q
scripts/pfiGate.sh target
git diff --check
```

## Stop Condition

PFI-009 is locally closed when the PFI-009 contract tests pass, the acceptance
script returns `status=Pass`, target gate remains green, and GitHub CI passes.
With PFI-006, PFI-007, PFI-008, and PFI-009 all at this evidence level, Gate 3
is closed for the current local evidence scope and must be re-run in the final
Gate 7 release package.
