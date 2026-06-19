# PFI OS Handoff

Last updated: 2026-06-19 Australia/Sydney

This checkout is still physically under `EVA_OS/`, but the active product
direction is PFI OS. The target product is a local-first, single-user,
research and decision-support operating system for personal financial
intelligence.

## Current Objective

Continue the controlled migration toward PFI OS without large-bang rewrites.
The current sequence is:

1. PFI-001 product contracts: complete.
2. PFI-002 retired value-ledger cleanup: active in this handoff.
3. PFI-003 identity, directory, namespace, app, script, and env migration.
4. PFI-004 new PFI Web Shell.
5. Post-shell MVP phases: data/workflow foundation, four vertical slices,
   one-minute worker reliability, local deployment, local LLM as optional
   deep-analysis provider, and full MVP acceptance.

## Boundaries

- Research, evidence, backtesting, simulation, reports, review queues, and
  human-approved order-intent style outputs only.
- No autonomous real-money trading.
- No unattended broker order placement.
- No payments, bank actions, betting execution, or account mutation.
- No stored brokerage passwords, tokens, API keys, private holdings,
  private imports, raw account screenshots, runtime SQLite state, local logs,
  or secrets in public Git.

## PFI-002 State

The retired value-ledger product surface must stay removed from active code.
Do not restore its modules, shell scripts, UI route, command-center source,
runtime summary target, dedicated tests, formal docs, schema, or public
example.

Historical context is allowed only in:

```text
docs/archive/legacy-migration.md
```

The user runtime data directory is intentionally not deleted by this cleanup.

## Start Here

Read in this order:

1. `README.md`
2. `AGENTS.md`
3. `PLANS.md`
4. `docs/product/PFI_OS_PRODUCT_CONSTITUTION.md`
5. `docs/product/PFI_OS_INFORMATION_ARCHITECTURE.md`
6. `docs/data/PFI_DATA_BOUNDARIES.md`
7. `docs/ux/PFI_UX_CONTRACT.md`
8. `docs/architecture/PFI_TARGET_ARCHITECTURE.md`
9. `docs/archive/legacy-migration.md`

## Verification

For PFI-002 use:

```bash
python -m pytest tests/test_app_dashboard.py tests/test_command_center.py tests/test_workspace_shell.py -q
python -m pytest tests/test_pfi_product_contracts.py tests/test_runtime_summary_refresh.py tests/test_scripts.py -q
PFI_RETIRED_VALUE_REGEX='<see task pack PFI-002 pattern>'
rg -n --hidden --glob '!data/**' --glob '!docs/archive/legacy-migration.md' "$PFI_RETIRED_VALUE_REGEX" .
git diff --check
```

Do not run heavy release gates by default. `scripts/finalAcceptanceCheck.sh`,
`scripts/ciSmoke.sh`, full pytest, browser automation, or real runtime app
acceptance should only run when explicitly required for a release gate.

## Next Step

Finish PFI-002 verification. If it passes, move to PFI-003 from the
`CodexProject` parent directory so `git mv EVA_OS PFI_OS` can preserve history.
