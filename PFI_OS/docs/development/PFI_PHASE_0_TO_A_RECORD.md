# PFI Phase 0 To A Development Record

Last updated: 2026-06-19 Australia/Sydney

This file is the compact GitHub handoff record for the current PFI OS rebuild.
It consolidates completed work, open tasks, key files, parameter contracts,
and verification commands so a future Codex run can continue without relying
on chat history.

## Scope

- Product: `PFI OS` in repository directory `PFI_OS/`.
- Execution span: PFI-001 through PFI-004 plus the first Phase A data
  foundation slices.
- Change policy: local-first, research-only, human-reviewed, no autonomous
  live trading, no private runtime data in public Git.

## Completed Development Record

| Work item | Status | Main evidence |
| --- | --- | --- |
| PFI-001 product contracts | Complete | `docs/product/*`, `docs/data/*`, `docs/ux/PFI_UX_CONTRACT.md`, `docs/architecture/PFI_TARGET_ARCHITECTURE.md`, `tests/test_pfi_product_contracts.py` |
| PFI-002 retired workflow cleanup | Complete | active code/docs/tests exclude the retired value-ledger surface; historical context remains in `docs/archive/legacy-migration.md` |
| PFI-003 identity migration | Complete | active naming, scripts, tests, docs, env examples, and app labels use PFI naming |
| PFI-004 Web Shell skeleton | Complete | `web/index.html`, `web/styles/tokens.css`, `web/app/shell.js`, `src/pfi_os/ui_contracts/web_shell.py`, Web Shell contract/e2e/visual tests |
| Phase A operational store | In progress | `src/pfi_os/application/operational_store.py`, official SQLite tables, data domains, fail-closed required fact fields |
| Phase A source registry | In progress | `src/pfi_os/application/source_registry.py`, private URI redaction, freshness summary, point-in-time source replay |
| Phase A homepage read model | In progress | `src/pfi_os/application/homepage_summary.py`, `PFIOSHomeSummaryV1`, Web Shell runtime injection |
| Phase A thin repositories | Complete | `src/pfi_os/application/repositories.py`, entity, evidence search, job execution, task queue, and holding snapshot adapters |
| Phase A data-home boundary audit | Complete | `src/pfi_os/application/data_home_audit.py`, `$PFI_OS_DATA_HOME` outside Git checks, private/runtime/secret fixture scans |
| Phase A homepage cache ingestion | Complete | `src/pfi_os/application/homepage_ingestion.py`, command-center latest cache to Operational Store source/evidence/job/task records |

## Open Backlog

1. Merge or continue draft PR #2 as the current integration path; do not use
   the superseded backup-only PR #1.
2. Move legacy Streamlit direct reads onto Operational Store repositories one
   vertical slice at a time.
3. Add source ingestion adapters with checksum, provenance, and domain
   enforcement.
4. Prepare Phase B vertical workflow slices after Phase A contracts are stable.

## Key File Map

| Area | Files |
| --- | --- |
| Product contracts | `docs/product/PFI_OS_PRODUCT_CONSTITUTION.md`, `docs/product/PFI_OS_INFORMATION_ARCHITECTURE.md`, `docs/product/PFI_FEATURE_DISPOSITION.md` |
| Data contracts | `docs/data/PFI_DATA_BOUNDARIES.md`, `docs/data/PFI_SOURCE_OF_TRUTH.md`, `docs/phase/PHASE_A_DATA_FOUNDATION.md` |
| UX and shell contracts | `docs/ux/PFI_UX_CONTRACT.md`, `docs/ux/PFI_WEB_SHELL_ACCEPTANCE.md`, `web/index.html`, `web/app/shell.js`, `web/styles/tokens.css` |
| Target architecture | `docs/architecture/PFI_TARGET_ARCHITECTURE.md` |
| Operational store | `src/pfi_os/application/operational_store.py`, `src/pfi_os/application/source_registry.py`, `src/pfi_os/application/homepage_summary.py`, `src/pfi_os/application/homepage_ingestion.py`, `src/pfi_os/application/repositories.py`, `src/pfi_os/application/data_home_audit.py` |
| Streamlit bridge | `src/pfi_os/app/streamlit_app.py` |
| Contract tests | `tests/test_pfi_product_contracts.py`, `tests/contract/test_pfi_web_shell_contract.py`, `tests/contract/test_phase_a_operational_store.py`, `tests/contract/test_phase_a_source_registry_homepage.py`, `tests/contract/test_phase_a_repositories.py`, `tests/contract/test_phase_a_data_home_audit.py`, `tests/contract/test_phase_a_homepage_ingestion.py` |
| E2E and visual tests | `tests/e2e/test_pfi_web_shell_static_flow.py`, `tests/visual/test_pfi_web_shell_visual_baseline.py`, `web/tests/visual-baseline.json` |

## Model And Parameter Contracts

- Every fact-bearing operational record must include `source_id`, `as_of`, and
  `evidence_class`.
- Every strategy backtest result must preserve data range, provider,
  adjustment mode, strategy version, parameters, cost model, and run timestamp.
- Every decision-support output must expose assumptions, source ids,
  evidence, parameters, data window, and `human_review_required: true` where
  action could affect research or trading behavior.
- Web Shell Phase 0 does not integrate a local model. Future model providers
  must be optional, inspectable, and unable to place orders, mutate holdings,
  or bypass human review.
- Market-feel training remains under Strategy Lab training mode and must hide
  future bars in replay-style workflows.
- Strategy backtesting remains a core workflow and must not generate live
  broker orders.

## Data And Security Contracts

- Public Git may contain source code, docs, schemas, sanitized examples, and
  public-safe summaries.
- Public Git must not contain secrets, account credentials, private holdings,
  raw imports, runtime SQLite files, local logs, browser profiles, or broker
  state.
- Operational SQLite belongs at
  `$PFI_OS_DATA_HOME/private/operational/pfi.sqlite`.
- Private and secret URIs must be redacted in public read models.
- ResearchBus is an internal compatibility/event layer, not a canonical truth
  source.

## Verification Commands

Run the focused contract suite after edits:

```bash
python -m pytest tests/test_pfi_product_contracts.py -q
python -m pytest tests/contract/test_pfi_web_shell_contract.py tests/e2e/test_pfi_web_shell_static_flow.py tests/visual/test_pfi_web_shell_visual_baseline.py -q
python -m pytest tests/contract/test_phase_a_data_home_audit.py tests/contract/test_phase_a_homepage_ingestion.py -q
python -m pytest tests/contract/test_phase_a_operational_store.py tests/contract/test_phase_a_source_registry_homepage.py tests/contract/test_phase_a_repositories.py -q
python -m compileall src/pfi_os/application src/pfi_os/app/streamlit_app.py
git diff --check
```

Broader regression used in this phase:

```bash
python -m pytest tests/test_config.py tests/test_data.py tests/test_data_lake_manifest.py tests/test_holdings_book.py tests/test_research_bus.py tests/test_app_dashboard.py tests/test_workspace_shell.py tests/test_scripts.py -q
```
