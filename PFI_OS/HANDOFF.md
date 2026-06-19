# PFI OS Handoff

Last updated: 2026-06-19 Australia/Sydney

This repository is the current handoff surface for PFI OS. Treat files in
this checkout as the source of truth, then verify with local commands before
changing code or running heavier acceptance gates.

## Current Objective

Continue the controlled PFI OS rebuild after the Phase 0 transition contracts.
The active product is a local-first, single-user, research and
decision-support operating system for personal financial intelligence.

Current sequence:

1. PFI-001 product contracts: complete.
2. PFI-002 retired value-ledger cleanup: complete.
3. PFI-003 identity, directory, namespace, app, script, and env migration:
   complete.
4. PFI-004 new PFI Web Shell skeleton: complete.
5. Phase A data foundation: complete for the data-boundary gate.
6. Phase B Strategy Lab vertical slice: in progress.

## Current Local State

- Repository root: `CodexProject`.
- Product directory: `PFI_OS/`.
- Runtime/private data root: `$PFI_OS_DATA_HOME`, outside public Git.
- Official operational SQLite path:
  `$PFI_OS_DATA_HOME/private/operational/pfi.sqlite`.
- ResearchBus remains an internal compatibility/event layer, not a truth
  source or user-facing product boundary.

## Boundaries

- Research, evidence, backtesting, simulation, reports, review queues, and
  human-reviewed order-intent style outputs only.
- No autonomous real-money trading.
- No unattended broker order placement.
- No payments, bank actions, betting execution, or account mutation.
- No stored brokerage passwords, tokens, API keys, private holdings, private
  imports, raw account screenshots, runtime SQLite state, local logs, or
  secrets in public Git.

## Completed In This Phase

- Product constitution, six-workspace information architecture, data boundary,
  source-of-truth, UX contract, target architecture, legacy migration archive,
  and product contract tests.
- Active product surface cleanup for the retired value-ledger workflow, while
  preserving historical context only in the archive and leaving user runtime
  data untouched.
- PFI identity migration across active code, docs, scripts, tests, app naming,
  and env examples.
- New static PFI Web Shell with six primary workspaces, global context, task
  center, evidence drawer, keyboard shortcuts, visual baseline contracts, and
  optional Streamlit embedding through `PFI_UI_V2=1`.
- Phase A operational store contract with official source, source-version,
  entity, evidence, job, task, and holding snapshot tables.
- Source registry, homepage summary read model, entity repository, evidence
  repository, job repository, task repository, holding snapshot repository,
  source version history, and point-in-time source replay.
- Data-home boundary audit for `$PFI_OS_DATA_HOME`, Operational SQLite, and
  public Git private/runtime/secret fixture paths.
- Command-center latest cache ingestion into Operational Store source,
  evidence, job, and task records before Web Shell homepage summary rendering.
- Sanitized command-center read model for the legacy Streamlit total-control
  page; rendering is now read-only over Operational Store evidence metadata.
- File-source ingestion adapter with checksum, provenance, public
  project-relative URI enforcement, private-source-outside-Git enforcement,
  and ephemeral runtime source rejection.
- Vectorized Research latest cache ingestion into Operational Store and a
  sanitized read model for the legacy Streamlit Vectorized Research panel.
- macOS runtime acceptance latest cache ingestion into Operational Store as
  private derived evidence and a sanitized read model for the legacy Streamlit
  runtime evidence panel.
- Private reviewed-input ledger adapter for cashflow, policy radar, and
  consumption guard Streamlit inputs; user-entered rows now stay in private
  Operational Store and snapshots go under `$PFI_OS_DATA_HOME/private/derived`.
- Streamlit data-boundary contract for remaining public `ROOT / "data"`
  top-level paths, plus private runtime storage for uploaded market CSV files
  under `$PFI_OS_DATA_HOME/runtime/uploads`.
- Phase A completion audit for the data-foundation boundary, including the
  evidence map, product non-regression constraints, and out-of-scope follow-up
  list.
- Phase B Strategy Lab workflow contract for approved-strategy backtests,
  reproducibility hashes, market-feel training retention, decision-support
  evidence fields, and Operational Store evidence/job/review-task recording.

## Start Here

Read in this order:

1. `README.md`
2. `AGENTS.md`
3. `PLANS.md`
4. `docs/development/PFI_PHASE_0_TO_A_RECORD.md`
5. `docs/product/PFI_OS_PRODUCT_CONSTITUTION.md`
6. `docs/product/PFI_OS_INFORMATION_ARCHITECTURE.md`
7. `docs/data/PFI_DATA_BOUNDARIES.md`
8. `docs/data/PFI_SOURCE_OF_TRUTH.md`
9. `docs/ux/PFI_UX_CONTRACT.md`
10. `docs/ux/PFI_WEB_SHELL_ACCEPTANCE.md`
11. `docs/architecture/PFI_TARGET_ARCHITECTURE.md`
12. `docs/phase/PHASE_A_DATA_FOUNDATION.md`
13. `docs/phase/PHASE_A_COMPLETION_AUDIT.md`
14. `docs/phase/PHASE_B_STRATEGY_LAB.md`
15. `docs/archive/legacy-migration.md`

## Current Verification Evidence

Latest focused verification for PFI-001 through PFI-004 and Phase A:

```bash
python -m pytest tests/test_pfi_product_contracts.py -q
python -m pytest tests/test_config.py tests/test_data.py tests/test_data_lake_manifest.py tests/test_holdings_book.py tests/test_research_bus.py tests/test_app_dashboard.py tests/test_workspace_shell.py tests/test_scripts.py -q
python -m pytest tests/contract/test_pfi_web_shell_contract.py tests/e2e/test_pfi_web_shell_static_flow.py tests/visual/test_pfi_web_shell_visual_baseline.py -q
python -m pytest tests/contract/test_phase_a_command_center_read_model.py -q
python -m pytest tests/contract/test_phase_a_vectorized_read_model.py -q
python -m pytest tests/contract/test_phase_a_macos_runtime_read_model.py -q
python -m pytest tests/contract/test_phase_a_private_reviewed_inputs.py -q
python -m pytest tests/contract/test_phase_a_streamlit_data_boundary.py -q
python -m pytest tests/contract/test_phase_a_completion_audit.py -q
python -m pytest tests/contract/test_phase_b_strategy_lab_workflow.py -q
python -m pytest tests/contract/test_phase_a_data_home_audit.py tests/contract/test_phase_a_homepage_ingestion.py -q
python -m pytest tests/contract/test_phase_a_source_ingestion.py -q
python -m pytest tests/contract/test_phase_a_operational_store.py tests/contract/test_phase_a_source_registry_homepage.py tests/contract/test_phase_a_repositories.py -q
python -m compileall src/pfi_os/application src/pfi_os/app/streamlit_app.py
git diff --check
```

The focused suite passed locally before this handoff update. Re-run the target
commands after any follow-up edits.

## Not Done

- GitHub draft PR #2 is the current mergeable integration path for this work.
- Legacy Streamlit pages still contain provider/runtime workflows outside the
  new Web Shell, but remaining public `ROOT / "data"` top-level paths are
  contract-classified and no longer include private input ledgers, runtime
  acceptance evidence, vectorized latest JSON, or uploaded CSV temp files.
- Existing legacy holdings sync and ResearchBus workflows are not fully moved
  onto Operational Store repositories.
- DuckDB/Parquet query surfaces remain in the existing `DataStore`.
- Full vertical workflow migration is not complete.
- Markets, Research + Policy, and Portfolio Phase B vertical slices are not
  complete.

## Next Step

Continue from the Phase A completion baseline:

1. Prepare Phase B vertical workflow slices or Phase 5 packaging from
   `docs/phase/PHASE_A_COMPLETION_AUDIT.md`.
2. Continue Phase B with Markets, Research + Policy, or Portfolio vertical
   slices.
3. Replace remaining legacy Streamlit direct reads one vertical slice at a
   time when those workflows enter scope.
