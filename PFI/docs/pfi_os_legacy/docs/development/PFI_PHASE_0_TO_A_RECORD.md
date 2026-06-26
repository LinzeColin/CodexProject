# PFI Phase 0 To A Development Record

Last updated: 2026-06-20 Australia/Sydney

This file is the compact GitHub handoff record for the current PFI OS rebuild.
It consolidates completed work, open tasks, key files, parameter contracts,
and verification commands so a future Codex run can continue without relying
on chat history.

## Scope

- Product: `PFI OS` in repository directory `PFI_OS/`.
- Execution span: PFI-001 through PFI-004 plus the Phase A data-foundation
  boundary completion gate.
- Change policy: local-first, research-only, human-reviewed, no autonomous
  live trading, no private runtime data in public Git.

## Completed Development Record

| Work item | Status | Main evidence |
| --- | --- | --- |
| PFI-001 product contracts | Complete | `docs/product/*`, `docs/data/*`, `docs/ux/PFI_UX_CONTRACT.md`, `docs/architecture/PFI_TARGET_ARCHITECTURE.md`, `tests/test_pfi_product_contracts.py` |
| PFI-002 retired workflow cleanup | Complete | active code/docs/tests exclude the retired value-ledger surface; historical context remains in `docs/archive/legacy-migration.md` |
| PFI-003 identity migration | Complete | active naming, scripts, tests, docs, env examples, and app labels use PFI naming |
| PFI-004 Web Shell skeleton | Complete | `web/index.html`, `web/styles/tokens.css`, `web/app/shell.js`, `src/pfi_os/ui_contracts/web_shell.py`, Web Shell contract/e2e/visual tests |
| Phase A operational store | Complete | `src/pfi_os/application/operational_store.py`, official SQLite tables, data domains, fail-closed required fact fields |
| Phase A source registry | Complete | `src/pfi_os/application/source_registry.py`, private URI redaction, freshness summary, point-in-time source replay |
| Phase A homepage read model | Complete | `src/pfi_os/application/homepage_summary.py`, `PFIOSHomeSummaryV1`, Web Shell runtime injection |
| Phase A thin repositories | Complete | `src/pfi_os/application/repositories.py`, entity, evidence search, job execution, task queue, and holding snapshot adapters |
| Phase A data-home boundary audit | Complete | `src/pfi_os/application/data_home_audit.py`, `$PFI_OS_DATA_HOME` outside Git checks, private/runtime/secret fixture scans |
| Phase A homepage cache ingestion | Complete | `src/pfi_os/application/homepage_ingestion.py`, command-center latest cache to Operational Store source/evidence/job/task records |
| Phase A source ingestion | Complete | `src/pfi_os/application/source_ingestion.py`, file source checksum/provenance, public/private path enforcement, ephemeral source rejection |
| Phase A command-center vertical slice | Complete | `src/pfi_os/application/command_center_read_model.py`, legacy Streamlit command center renders sanitized Operational Store read model |
| Phase A vectorized research vertical slice | Complete | `src/pfi_os/application/vectorized_read_model.py`, legacy Streamlit Vectorized Research panel renders sanitized Operational Store read model |
| Phase A macOS runtime evidence vertical slice | Complete | `src/pfi_os/application/macos_runtime_read_model.py`, legacy Streamlit runtime evidence panel renders sanitized Operational Store read model |
| Phase A private reviewed-input ledgers | Complete | `src/pfi_os/application/private_reviewed_inputs.py`, cashflow/policy/consumption Streamlit inputs stored in private Operational Store with private derived snapshot outputs |
| Phase A Streamlit data-boundary classification | Complete | `tests/contract/test_phase_a_streamlit_data_boundary.py`, remaining Streamlit `ROOT / "data"` top-level paths are explicit public artifact/runtime categories and uploaded CSV uses private runtime storage |
| Phase A completion audit | Complete | `docs/phase/PHASE_A_COMPLETION_AUDIT.md`, `tests/contract/test_phase_a_completion_audit.py`, data-foundation completion gate evidence |
| Phase B Strategy Lab vertical slice | Complete | `src/pfi_os/application/strategy_lab_workflow.py`, strategy verification workflow, market-feel training retention, Operational Store evidence/task records |
| Phase B Markets vertical slice | Complete | `src/pfi_os/application/markets_workflow.py`, market event/hotspot/sentiment cards, freshness metadata, Operational Store evidence/task records |
| Phase B Research + Policy vertical slice | Complete | `src/pfi_os/application/research_policy_workflow.py`, policy authority cards, report evidence-gap tasks, Operational Store evidence/task records |
| Phase B Portfolio vertical slice | Complete | `src/pfi_os/application/portfolio_workflow.py`, private-derived holding snapshots, quality/exposure/concentration/risk cards, Operational Store evidence/task/snapshot records |
| Phase C workflow runtime read model | Complete first slice | `src/pfi_os/application/workflow_runtime_read_model.py`, `PFIOSPhaseCWorkflowRuntimeReadModelV1`, Fast Path metadata, retry policy, task-center rows, Web Shell cached runtime summary |
| Phase C workflow runtime scheduler | Complete second slice | `src/pfi_os/application/workflow_runtime_scheduler.py`, `PFIOSPhaseCWorkflowRuntimeSchedulerV1`, idempotent cache-refresh jobs, bounded retry/backoff, 60-second acceptance metadata, fail-closed exhausted retries |
| Phase C Web Shell workflow cards | Complete third slice | `web/index.html`, `web/app/shell.js`, `web/styles/tokens.css`, responsive `workflow_cards` rendering, Fast Path badge, private-safe evidence drawer updates, hidden-state visual guard |
| Phase D local deployment readiness | Complete first slice | `src/pfi_os/application/deployment_readiness.py`, `PFIOSPhaseDLocalDeploymentReadinessV1`, repo surface checks, data-home boundary, backup/restore path plan, DisabledProvider/local-model optionality |
| Phase D backup/restore acceptance | Complete second slice | `src/pfi_os/application/deployment_backup_restore.py`, `PFIOSPhaseDBackupRestoreAcceptanceV1`, private runtime backup, restore staging, checksum/row-count validation, GitHub-safe sanitized summary, `tests/contract/test_phase_d_backup_restore_acceptance.py` |
| Phase 5 acceptance package | Complete engineering handoff | `src/pfi_os/application/phase5_acceptance_package.py`, `docs/phase/PHASE_5_ACCEPTANCE_PACKAGE.md`, `PFIOSPhase5AcceptancePackageV1`, GitHub-safe file inventory, validation evidence matrix, Phase 6 user-material boundary, `tests/contract/test_phase5_acceptance_package.py` |
| PFI-005 Gate 2 shell acceptance | Complete local evidence contract | `scripts/pfiGate2ShellAcceptance.sh`, `tests/contract/test_pfi005_gate2_shell_acceptance.py`, `docs/development/PFI005_GATE2_SHELL_ACCEPTANCE.md`, eight named browser UAT journeys, WCAG structural proof, performance budgets, Chinese-first/no-legacy primary navigation checks, no raw-HTML iframe fallback |
| PFI-006 Markets vertical acceptance | Complete local Gate 3 Markets evidence | `src/pfi_os/application/pfi006_markets_acceptance.py`, `scripts/pfi006MarketsAcceptance.sh`, `tests/contract/test_pfi006_markets_vertical_acceptance.py`, `docs/development/PFI006_MARKETS_VERTICAL_ACCEPTANCE.md`, deterministic Golden market bars, UI read model, portfolio overlay, alerts/saved views, task/evidence records, rollback proof |
| PFI-007 Research + Policy vertical acceptance | Complete local Gate 3 Research/Policy evidence | `src/pfi_os/application/pfi007_research_policy_acceptance.py`, `scripts/pfi007ResearchPolicyAcceptance.sh`, `tests/contract/test_pfi007_research_policy_vertical_acceptance.py`, `docs/development/PFI007_RESEARCH_POLICY_VERTICAL_ACCEPTANCE.md`, citation locator, report manifest, UI read model, task/evidence records, rollback proof |
| PFI-008 Portfolio vertical acceptance | Complete local Gate 3 Portfolio evidence | `src/pfi_os/application/pfi008_portfolio_acceptance.py`, `scripts/pfi008PortfolioAcceptance.sh`, `tests/contract/test_pfi008_portfolio_vertical_acceptance.py`, `docs/development/PFI008_PORTFOLIO_VERTICAL_ACCEPTANCE.md`, synthetic import ledger, corporate action/FX/cash Golden checks, broker-to-snapshot reconciliation, risk constraints, review-only decision proposal, same-shell Portfolio UI controls, holding snapshot rollback proof |
| PFI-009 Strategy vertical acceptance | Complete local Gate 3 Strategy evidence | `src/pfi_os/application/pfi009_strategy_acceptance.py`, `scripts/pfi009StrategyAcceptance.sh`, `tests/contract/test_pfi009_strategy_vertical_acceptance.py`, `docs/development/PFI009_STRATEGY_VERTICAL_ACCEPTANCE.md`, PIT bars, corporate-action/delisted fixture, train/test validation, walk-forward validation, no-future-data proof, market-feel retention, review-only strategy registry, cancel/resume runtime proof, same-shell Strategy UI controls, rollback proof |
| PFI-010 Minute Fast Path | Complete local deterministic Gate 4 evidence | `src/pfi_os/application/pfi010_minute_fast_path.py`, `scripts/pfi010MinuteFastPathAcceptance.sh`, `tests/contract/test_pfi010_minute_fast_path.py`, `docs/development/PFI010_MINUTE_FAST_PATH.md`, three legal local sources, durable incremental worker, p95=44.0s, page-closed update proof, failure injection recovery, logical 1h/24h soak, Web Shell runtime dashboard |
| PFI-011 Local LLM Deep Path | Complete local Gate 5 evidence | `src/pfi_os/application/pfi011_local_llm_deep_path.py`, `scripts/pfi011LocalLLMDeepPathAcceptance.sh`, `tests/contract/test_pfi011_local_llm_deep_path.py`, `docs/development/PFI011_LOCAL_LLM_DEEP_PATH.md`, hardware audit, provider interface, DisabledProvider fallback, citation/schema QA, timeout fallback, cancel, resource budget, prompt-injection guard, Web Shell runtime dashboard |
| PFI-012 MVP Release Gate | Complete local release-candidate gate | `src/pfi_os/application/pfi012_mvp_release_gate.py`, `scripts/pfi012MVPReleaseGate.sh`, `tests/contract/test_pfi012_mvp_release_gate.py`, `docs/development/PFI012_MVP_RELEASE_GATE.md`, PFI-001..012 and Gate1..7 matrix, P0=0, P1 dispositions, UAT/latest artifact checks, privacy audit, active legacy freeze, signed checksum manifest, external CI/rollback fail-closed evidence |

## Open Backlog

1. Merge or continue draft PR #2 as the current integration path; do not use
   the superseded backup-only PR #1.
2. Move remaining legacy Streamlit direct reads onto Operational Store
   repositories one vertical slice at a time when those workflows enter scope.
3. Add SSE/WebSocket-style progress only if it improves local workflow
   observability enough to justify the added complexity.
4. Collect user-supplied Phase 6 deployment materials on the target Mac:
   repository backup, hardware/disk audit, sanitized holdings, representative
   symbols/policy documents, Fast Path source list, workflow examples, and
   final subjective acceptance score.
5. Attach final Gate 7 external evidence: GitHub CI pass URL and rollback ref,
   then rerun `scripts/pfi012MVPReleaseGate.sh --require-external-release-evidence`.

## Key File Map

| Area | Files |
| --- | --- |
| Product contracts | `docs/product/PFI_OS_PRODUCT_CONSTITUTION.md`, `docs/product/PFI_OS_INFORMATION_ARCHITECTURE.md`, `docs/product/PFI_FEATURE_DISPOSITION.md` |
| Data contracts | `docs/data/PFI_DATA_BOUNDARIES.md`, `docs/data/PFI_SOURCE_OF_TRUTH.md`, `docs/phase/PHASE_A_DATA_FOUNDATION.md`, `docs/phase/PHASE_A_COMPLETION_AUDIT.md`, `docs/phase/PHASE_B_MARKETS.md`, `docs/phase/PHASE_B_RESEARCH_POLICY.md`, `docs/phase/PHASE_B_STRATEGY_LAB.md`, `docs/phase/PHASE_B_PORTFOLIO.md`, `docs/phase/PHASE_C_WORKFLOW_RUNTIME.md`, `docs/phase/PHASE_D_DEPLOYMENT_READINESS.md`, `docs/phase/PHASE_5_ACCEPTANCE_PACKAGE.md`, `docs/development/PFI012_MVP_RELEASE_GATE.md` |
| UX and shell contracts | `docs/ux/PFI_UX_CONTRACT.md`, `docs/ux/PFI_WEB_SHELL_ACCEPTANCE.md`, `docs/development/PFI005_GATE2_SHELL_ACCEPTANCE.md`, `docs/development/PFI006_MARKETS_VERTICAL_ACCEPTANCE.md`, `docs/development/PFI007_RESEARCH_POLICY_VERTICAL_ACCEPTANCE.md`, `docs/development/PFI008_PORTFOLIO_VERTICAL_ACCEPTANCE.md`, `docs/development/PFI009_STRATEGY_VERTICAL_ACCEPTANCE.md`, `web/index.html`, `web/app/shell.js`, `web/styles/tokens.css` |
| Target architecture | `docs/architecture/PFI_TARGET_ARCHITECTURE.md` |
| Operational store | `src/pfi_os/application/operational_store.py`, `src/pfi_os/application/source_registry.py`, `src/pfi_os/application/source_ingestion.py`, `src/pfi_os/application/homepage_summary.py`, `src/pfi_os/application/homepage_ingestion.py`, `src/pfi_os/application/command_center_read_model.py`, `src/pfi_os/application/vectorized_read_model.py`, `src/pfi_os/application/macos_runtime_read_model.py`, `src/pfi_os/application/private_reviewed_inputs.py`, `src/pfi_os/application/strategy_lab_workflow.py`, `src/pfi_os/application/pfi009_strategy_acceptance.py`, `src/pfi_os/application/markets_workflow.py`, `src/pfi_os/application/pfi006_markets_acceptance.py`, `src/pfi_os/application/research_policy_workflow.py`, `src/pfi_os/application/pfi007_research_policy_acceptance.py`, `src/pfi_os/application/portfolio_workflow.py`, `src/pfi_os/application/pfi008_portfolio_acceptance.py`, `src/pfi_os/application/workflow_runtime_read_model.py`, `src/pfi_os/application/workflow_runtime_scheduler.py`, `src/pfi_os/application/deployment_readiness.py`, `src/pfi_os/application/deployment_backup_restore.py`, `src/pfi_os/application/phase5_acceptance_package.py`, `src/pfi_os/application/repositories.py`, `src/pfi_os/application/data_home_audit.py` |
| Streamlit bridge | `src/pfi_os/app/streamlit_app.py` |
| Contract tests | `tests/test_pfi_product_contracts.py`, `tests/contract/test_pfi_web_shell_contract.py`, `tests/contract/test_pfi005_gate2_shell_acceptance.py`, `tests/contract/test_pfi006_markets_vertical_acceptance.py`, `tests/contract/test_pfi007_research_policy_vertical_acceptance.py`, `tests/contract/test_pfi008_portfolio_vertical_acceptance.py`, `tests/contract/test_pfi009_strategy_vertical_acceptance.py`, `tests/contract/test_phase_a_operational_store.py`, `tests/contract/test_phase_a_source_registry_homepage.py`, `tests/contract/test_phase_a_repositories.py`, `tests/contract/test_phase_a_data_home_audit.py`, `tests/contract/test_phase_a_homepage_ingestion.py`, `tests/contract/test_phase_a_source_ingestion.py`, `tests/contract/test_phase_a_command_center_read_model.py`, `tests/contract/test_phase_a_vectorized_read_model.py`, `tests/contract/test_phase_a_macos_runtime_read_model.py`, `tests/contract/test_phase_a_private_reviewed_inputs.py`, `tests/contract/test_phase_a_streamlit_data_boundary.py`, `tests/contract/test_phase_a_completion_audit.py`, `tests/contract/test_phase_b_strategy_lab_workflow.py`, `tests/contract/test_phase_b_markets_workflow.py`, `tests/contract/test_phase_b_research_policy_workflow.py`, `tests/contract/test_phase_b_portfolio_workflow.py`, `tests/contract/test_phase_c_workflow_runtime_read_model.py`, `tests/contract/test_phase_c_workflow_runtime_scheduler.py`, `tests/contract/test_phase_d_deployment_readiness.py`, `tests/contract/test_phase_d_backup_restore_acceptance.py`, `tests/contract/test_phase5_acceptance_package.py` |
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
python -m pytest tests/contract/test_pfi005_gate2_shell_acceptance.py -q
scripts/pfiGate2ShellAcceptance.sh --summary-json
python -m pytest tests/contract/test_pfi006_markets_vertical_acceptance.py -q
scripts/pfi006MarketsAcceptance.sh --summary-json
python -m pytest tests/contract/test_pfi007_research_policy_vertical_acceptance.py -q
scripts/pfi007ResearchPolicyAcceptance.sh --summary-json
python -m pytest tests/contract/test_pfi008_portfolio_vertical_acceptance.py -q
scripts/pfi008PortfolioAcceptance.sh --summary-json
python -m pytest tests/contract/test_pfi009_strategy_vertical_acceptance.py -q
scripts/pfi009StrategyAcceptance.sh --summary-json
python -m pytest tests/contract/test_pfi010_minute_fast_path.py -q
scripts/pfi010MinuteFastPathAcceptance.sh --summary-json
python -m pytest tests/contract/test_pfi011_local_llm_deep_path.py -q
scripts/pfi011LocalLLMDeepPathAcceptance.sh --summary-json
python -m pytest tests/contract/test_phase_a_command_center_read_model.py -q
python -m pytest tests/contract/test_phase_a_vectorized_read_model.py -q
python -m pytest tests/contract/test_phase_a_macos_runtime_read_model.py -q
python -m pytest tests/contract/test_phase_a_private_reviewed_inputs.py -q
python -m pytest tests/contract/test_phase_a_streamlit_data_boundary.py -q
python -m pytest tests/contract/test_phase_a_completion_audit.py -q
python -m pytest tests/contract/test_phase_b_markets_workflow.py -q
python -m pytest tests/contract/test_phase_b_research_policy_workflow.py -q
python -m pytest tests/contract/test_phase_b_strategy_lab_workflow.py -q
python -m pytest tests/contract/test_phase_b_portfolio_workflow.py -q
python -m pytest tests/contract/test_phase_c_workflow_runtime_read_model.py -q
python -m pytest tests/contract/test_phase_c_workflow_runtime_scheduler.py -q
python -m pytest tests/contract/test_phase_d_deployment_readiness.py -q
python -m pytest tests/contract/test_phase_d_backup_restore_acceptance.py -q
python -m pytest tests/contract/test_phase5_acceptance_package.py -q
python -m pytest tests/contract/test_phase_a_data_home_audit.py tests/contract/test_phase_a_homepage_ingestion.py -q
python -m pytest tests/contract/test_phase_a_source_ingestion.py -q
python -m pytest tests/contract/test_phase_a_operational_store.py tests/contract/test_phase_a_source_registry_homepage.py tests/contract/test_phase_a_repositories.py -q
python -m compileall src/pfi_os/application src/pfi_os/app/streamlit_app.py
git diff --check
```

Broader regression used in this phase:

```bash
python -m pytest tests/test_config.py tests/test_data.py tests/test_data_lake_manifest.py tests/test_holdings_book.py tests/test_research_bus.py tests/test_app_dashboard.py tests/test_workspace_shell.py tests/test_scripts.py -q
```

## User-Facing Rework After Rejection, 2026-06-20

Scope: repair the rejected PFI user surface where the app still looked like a
legacy EVA/PFIOS system, feature blocks did not reliably jump to usable pages,
and Streamlit detail pages showed runtime tracebacks.

Changes:

- Web Shell feature links now resolve the top-level PFI app URL from
  `window.parent.location`, `document.referrer`, or a safe current-location
  fallback, instead of assuming iframe-relative query strings.
- Streamlit legacy/detail sidebar now exposes the active PFI six-entry user
  surface: 首页, 市场, 研究, 持仓, 策略实验室, 数据与系统. Legacy capabilities remain
  in code but are no longer primary navigation entries.
- Detail pages install a runtime compatibility shim so older Streamlit builds
  accept tables/charts that were authored with `width="stretch"`, and
  `segmented_control` falls back to a horizontal radio control.
- Detail pages no longer append the full system self-check to every function;
  that panel is limited to 总控驾驶舱 and 数据中心.
- 持仓空状态 now shows relative import directories rather than full local paths
  containing `PFI_OS`.
- Tracked legacy `data/commandCenter/EVACommandCenter_*` artifacts were removed
  from the working tree, and `scripts/commandCenter.sh --output-dir
  data/commandCenter` regenerated `PFICommandCenter_20062026.*` and latest
  pointers.

Verification:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' /private/tmp/pfi_os_ci_repro/bin/python -m pytest tests/e2e/test_pfi_web_shell_static_flow.py tests/contract/test_pfi_web_shell_contract.py tests/test_app_dashboard.py -q
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' /private/tmp/pfi_os_ci_repro/bin/python -m pytest tests/test_holdings_book.py tests/test_external_integrations.py tests/e2e/test_pfi_web_shell_static_flow.py -q
PFI_PYTHON=/private/tmp/pfi_os_ci_repro/bin/python PYTHONDONTWRITEBYTECODE=1 scripts/uiVisualAcceptance.sh --summary-json --start-timeout 120
PFI_PYTHON=/private/tmp/pfi_os_ci_repro/bin/python PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' scripts/pfiGate.sh target
git diff --check
```

Observed:

- UI/static/dashboard suite: 76 passed, 2 existing protobuf deprecation
  warnings.
- Holdings/Web focused suite: 30 passed, 4 existing pandas future warnings.
- Browser UI acceptance: `PFIOSUIVisualAcceptanceV1 status=Pass`, 130 pass /
  0 fail / 0 info.
- Target gate: 73 passed, 2 existing protobuf deprecation warnings; secret
  scan passed; diff check passed.

## User-Facing Rework After Second Rejection, 2026-06-20

Scope: repair the rejected PFI user path where feature blocks still depended on
legacy Streamlit detail pages and did not produce a visible Chinese operation
state inside PFI Web Shell.

Changes:

- Primary feature actions now open `data-function-runner`, a same-shell
  Chinese operation panel with steps, status, output fields, and explicit
  no-broker/no-order safety boundaries.
- Direct `?view=<feature>` entry points now remain on PFI Web Shell by default
  and auto-open the requested feature panel.
- Legacy Streamlit detail pages are no longer the default target for function
  navigation; they are only reachable through explicit `pfi_legacy=1`.
- Gate2 and visual browser acceptance now fail if primary feature actions open
  a new legacy page instead of same-shell operation panels.
- Strategy Lab feature rendering no longer truncates after eight cards; the
  required 模拟实验 card is visible and usable.
- Portfolio now includes a direct 持仓 card in addition to deeper reconciliation
  and risk panels.

Verification:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' /private/tmp/pfi_os_ci_repro/bin/python -m pytest tests/contract/test_pfi_web_shell_contract.py tests/e2e/test_pfi_web_shell_static_flow.py tests/contract/test_pfi005_gate2_shell_acceptance.py -q
PFI_PYTHON=/private/tmp/pfi_os_ci_repro/bin/python PYTHONDONTWRITEBYTECODE=1 scripts/pfiGate2ShellAcceptance.sh --summary-json --start-timeout 120
PFI_PYTHON=/private/tmp/pfi_os_ci_repro/bin/python PYTHONDONTWRITEBYTECODE=1 scripts/uiVisualAcceptance.sh --summary-json --start-timeout 120
PFI_PYTHON=/private/tmp/pfi_os_ci_repro/bin/python PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' scripts/pfiGate.sh target
zsh -n scripts/uiVisualAcceptance.sh scripts/pfiGate2ShellAcceptance.sh scripts/startPFIOS.sh
git diff --check
```

Observed:

- Focused Web Shell/Gate2 contracts: 30 passed, 2 existing protobuf
  deprecation warnings.
- Gate2 browser acceptance: `PFIGate2ShellAcceptanceV1 status=Pass`, 228 pass /
  0 fail / 2 info, screenshot
  `data/systemAudit/PFIGate2ShellAcceptance_20260620_071550.png`.
- Browser UI acceptance: `PFIOSUIVisualAcceptanceV1 status=Pass`, 146 pass /
  0 fail / 0 info, screenshot
  `data/systemAudit/UIVisualAcceptance_20260620_071622.png`.
- Target gate: 93 passed, 2 existing protobuf deprecation warnings; secret
  scan passed.
- `zsh -n` and `git diff --check`: passed.

## User-Facing Redo After Navigation Rejection, 2026-06-20

Scope: close the rejected-delivery gap where some function cards still behaved
like passive workspace jumps and several function-panel checks exposed raw
English field names instead of Chinese user-facing guidance.

Changes:

- All visible feature cards now map to concrete same-shell function views.
  Cards such as 公司研究, 基金研究, 指数与 ETF, 主题催化, 自选监控, 来源登记,
  任务监控, 隐私边界, 备份恢复, 组合暴露, 集中度风险, 纪律检查, and
  订单意图 no longer behave as silent workspace-only jumps.
- Function-panel copy now uses Chinese user language for checks and boundaries;
  raw field-name style text such as `bar_checksum`, `source_url`,
  `RunMetadata`, `NeedsMoreEvidence`, and `target_weight_change=0` is removed
  from the Web Shell function-panel contract.
- Gate2 browser acceptance now performs exhaustive replay of all visible
  feature controls across six entrances. Each control must be a button, open a
  same-shell Chinese function panel, show a same-shell operation panel, avoid
  opening new pages, and avoid `pfi_legacy=1`/`pfi_shell=0`.

Verification:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' /private/tmp/pfi_os_ci_repro/bin/python -m pytest tests/contract/test_pfi_web_shell_contract.py tests/e2e/test_pfi_web_shell_static_flow.py tests/contract/test_pfi005_gate2_shell_acceptance.py tests/contract/test_pfi007_research_policy_vertical_acceptance.py -q
zsh -n scripts/pfiGate2ShellAcceptance.sh
scripts/pfiGate2ShellAcceptance.sh --summary-json --start-timeout 120
scripts/uiVisualAcceptance.sh --summary-json --start-timeout 120
```

Observed:

- Focused user-facing contracts: 38 passed, 2 existing protobuf deprecation
  warnings.
- Gate2 browser acceptance: `PFIGate2ShellAcceptanceV1 status=Pass`, 844 pass /
  0 fail / 2 info, `all_feature_control_panels_opened=46`, screenshot
  `data/systemAudit/PFIGate2ShellAcceptance_20260620_073524.png`.
- Browser UI acceptance: `PFIOSUIVisualAcceptanceV1 status=Pass`, 146 pass /
  0 fail / 0 info, screenshot
  `data/systemAudit/UIVisualAcceptance_20260620_073602.png`.

## Command Center Chinese Delivery Patch, 2026-06-20

Scope: close the remaining user-facing gap where regenerated Command Center
Markdown/PDF artifacts were valid but still read like an English engineering
panel.

Changes:

- `command_center_markdown()` now renders Chinese section titles, table
  headers, status values, action guidance, and safety constraints.
- JSON payload fields remain unchanged for downstream contracts; only the
  Markdown/PDF display layer is localized.
- PDF generation now prefers a system-font image PDF path so Chinese glyphs
  render visually instead of falling back to `????` or ASCII-only output.
- Latest `data/commandCenter/PFICommandCenter_20062026.*` and
  `PFICommandCenter_latest.*` were regenerated.

Verification:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' /private/tmp/pfi_os_ci_repro/bin/python -m pytest tests/test_command_center.py -q
scripts/commandCenter.sh --output-dir data/commandCenter
```

Observed:

- Command Center tests: 6 passed.
- Latest Markdown/PDF byte checks: no `????`, no `EVA`, no `PFIOS`, no
  `PFI_OS`.
