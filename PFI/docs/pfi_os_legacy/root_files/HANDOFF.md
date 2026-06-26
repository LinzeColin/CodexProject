# PFI OS Handoff

Last updated: 2026-06-27 Australia/Sydney

This repository is the current handoff surface for PFI OS. Treat files in
this checkout as the source of truth, then verify with local commands before
changing code or running heavier acceptance gates.

## Current Objective

Continue the controlled PFI OS rebuild under PFI V0.2. Stage 0 is the current
compatibility audit and boundary lock. The active product is a local-first,
single-user, research and decision-support operating system for personal
financial intelligence.

PFI V0.2 Stage 0 source of truth:

- `docs/pfi_v02/STAGE0_COMPATIBILITY_AUDIT.md`
- `src/pfi_os/ui_contracts/pfi_v02_stage0.py`
- `tests/contract/test_pfi_v02_stage0_compatibility.py`

Stage 0 locks this rule: v0.2 target IA has eight first-level entries, while
the current six Web Shell entries remain accessible as compatibility aliases
until Stage 1 UI migration. `PFI/大数据模拟器` maps to
`投资管理 > 策略实验室 / 大数据模拟器`. Active runtime paths are not moved.

Current sequence:

1. PFI-001 product contracts: complete.
2. PFI-002 retired value-ledger cleanup: complete.
3. PFI-003 identity, directory, namespace, app, script, and env migration:
   complete.
4. PFI-004 new PFI Web Shell skeleton: complete.
5. Phase A data foundation: complete for the data-boundary gate.
6. Phase B Strategy Lab vertical slice: complete.
7. Phase B Markets vertical slice: complete.
8. Phase B Research + Policy vertical slice: complete.
9. Phase B Portfolio vertical slice: complete.
10. Phase C workflow runtime read model: first slice complete.
11. Phase C worker scheduler, retry/backoff executor, and 60-second acceptance:
    second slice complete.
12. Phase C Web Shell workflow-card rendering and optional progress stream:
    workflow-card rendering complete; optional progress stream deferred.
13. Phase D local deployment, backup/restore, and model readiness:
    readiness and backup/restore acceptance complete.
14. Phase 5 package:
    engineering acceptance package complete; Phase 6 user materials remain
    external.
15. v0.1.1 preparation:
    P0/P1 findings baseline complete; runtime entry correction and legacy
    command-center cache isolation complete.
16. v0.2 PFI-goal execution:
    PFI-001 reproducible environment, lock, CI wiring, secret scan, explicit
    install/runtime separation, and clean-install/offline-start evidence are
    complete. Root GitHub Actions workflow `.github/workflows/pfi-os-smoke.yml`
    is now the real PR CI entry for the `LinzeColin/CodexProject` monorepo and
    runs from `working-directory: PFI_OS`. PR #2 run `27856494975` succeeded on
    commit `9ed86b6`, including target gate and injected-failure proof.
17. v0.2 PFI-003 runtime supervisor:
    Durable Job Store core lifecycle is implemented on top of `job_records`.
    It covers idempotent enqueue, atomic claim, lease, heartbeat, bounded
    retry, cancel/resume, expired-lease recovery, and dead letter.
    `scripts/pfiSupervisor.sh` now exposes contract/status/doctor/lifecycle
    commands plus double-worker, crash-recovery, and release acceptance smoke.
    The current acceptance harness covers real TERM/KILL child-worker recovery,
    deterministic sleep/wake recovery, SQLite backup manifest, private-log scan,
    simulated network recovery, sanitized launchd throttle/log-rotation
    artifacts, Web Shell/runtime `supervisor_runtime`, and no-execution
    boundary checks. No local PFI-003 implementation gap remains; release/CI
    replay is still required before final Gate 7 closure.
18. UI return/rework after user rejection:
    runtime entry stability and user-facing PFI Web Shell navigation were
    repaired. `scripts/startPFIOS.sh` now launches Streamlit through a
    detached Python subprocess so the service remains alive after the script
    returns. Core Web Shell function cards now open same-shell Chinese
    function panels for backtest, parameter scan, market-feel training,
    simulation, hotspots, reports, holdings, policy, data center, and strategy
    library. `scripts/uiVisualAcceptance.sh` now performs real click-through
    checks instead of href-only checks.
19. v0.2 PFI-004 Golden/PIT:
    Local proof is complete. Operational Store now rejects retrograde active
    source writes with `PIT_INVALID_WRITE`, PIT replay compares parsed `as_of`
    timestamps, and `PFI004GoldenPITAcceptanceV1` proves deterministic Golden
    financial metrics, point-in-time replay, dual-read reconciliation, active
    truth unchanged after invalid writes, and no-execution boundaries.
20. Gate 1:
    Closed for current evidence scope. PFI-001 PR CI, PFI-003 supervisor/
    double-worker/recovery evidence, Phase D backup/restore, and PFI-004
    Golden/PIT proof are all present. Gate 1 must still be re-run as part of
    final Gate 7 release packaging.
21. Gate 2 / PFI-005:
    Formal shell UAT acceptance is implemented. `scripts/pfiGate2ShellAcceptance.sh`
    emits `PFIGate2ShellAcceptanceV1` browser evidence for four named Chinese
    user journeys, same-shell function panels, WCAG structural proof, optional
    local axe scan, performance budgets, and no legacy-page primary navigation.
    Latest local browser run returned `status=Pass`, `pass=126`, `fail=0`,
    `info=2`.
    Gate 2 must still be re-run as part of final Gate 7 release packaging.
22. Gate 3 / PFI-006 Markets:
    Markets vertical acceptance is implemented. `scripts/pfi006MarketsAcceptance.sh`
    emits `PFI006MarketsVerticalAcceptanceV1` evidence for deterministic
    market bars -> event/hotspot/sentiment cards -> UI read model -> same-shell
    Chinese Web Shell controls -> task/evidence records -> portfolio overlay
    -> alerts/saved views -> Golden metrics -> rollback proof. Latest local
    run returned `status=Pass`, `pass=13`, `fail=0`, event_count=90,
    alerts=2, saved_views=2, rollback=Pass. Target gate passed 52 tests plus
    secret scan; UI visual acceptance passed 98/98 after market shell changes.
    Gate 3 current evidence scope is now closed after PFI-009.
23. Gate 3 / PFI-007 Research + Policy:
    Research + Policy vertical acceptance is implemented.
    `scripts/pfi007ResearchPolicyAcceptance.sh` emits
    `PFI007ResearchPolicyVerticalAcceptanceV1` evidence for reviewed policy
    opportunities and report decision payloads -> policy radar/report gaps ->
    UI read model -> same-shell Chinese research controls -> citation locator
    -> report manifest -> task/evidence records -> Golden metrics -> rollback
    proof. Latest local run returned `status=Pass`, `pass=14`, `fail=0`,
    policy_record_count=2, official_citation_count=1, report_gap_count=3,
    report_manifest_count=1, rollback=Pass. Target gate passed 58 tests plus
    secret scan; UI visual acceptance passed 98/98 after research shell
    changes. Gate 3 current evidence scope is now closed after PFI-009.
24. Gate 3 / PFI-008 Portfolio:
    Portfolio vertical acceptance is implemented.
    `scripts/pfi008PortfolioAcceptance.sh` emits
    `PFI008PortfolioVerticalAcceptanceV1` evidence for deterministic synthetic
    import ledger -> reviewed holdings -> private-derived holding snapshot ->
    broker-to-snapshot reconciliation -> corporate-action/FX/cash Golden
    checks -> risk constraints -> review-only decision proposal -> same-shell
    Chinese Portfolio controls -> task/evidence/snapshot records -> rollback
    proof. Latest local run returned `status=Pass`, `pass=16`, `fail=0`,
    holding_count=5, import_record_count=5, broker_count=3,
    constraint_violation_count=2, reconciliation=Pass, rollback=Pass. Focused
    PFI-008 contract passed 6/6; related Web Shell/script tests passed 58/58;
    target gate passed 64 tests plus secret scan and diff check. Gate 3
    current evidence scope is now closed after PFI-009.
25. Gate 3 / PFI-009 Strategy:
    Strategy vertical acceptance is implemented.
    `scripts/pfi009StrategyAcceptance.sh` emits
    `PFI009StrategyVerticalAcceptanceV1` evidence for deterministic PIT bars
    -> reproducible backtest -> train/test no-future-data validation ->
    walk-forward validation -> market-feel future hiding -> review-only
    strategy registry -> Durable Job Store cancel/resume -> same-shell Chinese
    Strategy controls -> task/evidence records -> rollback proof. Latest local
    run returned `status=Pass`, `pass=18`, `fail=0`, bar_count=360,
    trade_count=53, train_test=Pass, walk_forward=Pass, windows=2,
    registered_model_count=1, runtime_resume_count=1, rollback=Pass. Focused
    PFI-009 contract passed 7/7; related Web Shell/script tests passed 63/63;
    target gate passed 71 tests plus secret scan and diff check. Gate 3 is
    closed for the current local evidence scope and must be re-run in Gate 7.
26. Gate 4 / PFI-010 Minute Fast Path:
    Local deterministic evidence is implemented.
    `scripts/pfi010MinuteFastPathAcceptance.sh` emits
    `PFI010MinuteFastPathAcceptanceV1` evidence for three legal local sources,
    durable incremental worker refresh, p95 <= 60s, page-closed update
    completion, failure injection recovery, logical 1h/24h soak, Operational
    Store records, and Web Shell runtime dashboard exposure through
    `workflow_runtime.minute_fast_path`. Latest local run returned
    `status=Pass`, `pass=11`, `fail=0`, `source_count=3`, `sample_count=15`,
    `p95_seconds=44.0`, page_closed_updates=true, failure_injection=Pass,
    logical_1h_soak=Pass, and logical_24h_soak=Pass. Gate 4 is closed for the
    current deterministic local evidence scope and must be re-run in Gate 7.
27. Gate 5 / PFI-011 Local LLM Deep Path:
    Local evidence is implemented.
    `scripts/pfi011LocalLLMDeepPathAcceptance.sh` emits
    `PFI011LocalLLMDeepPathAcceptanceV1` evidence for hardware audit,
    provider interface, default DisabledProvider fallback, deterministic local
    provider output, schema/citation QA, timeout fallback, cancel proof,
    resource budget, prompt-injection blocking, Operational Store records, and
    Web Shell runtime dashboard exposure through
    `workflow_runtime.local_llm_deep_path`. Latest local run returned
    `status=Pass`, `pass=12`, `fail=0`, `hardware_status=Pass`,
    `citation_count=3`, timeout_fallback=Pass, cancel=Pass,
    resource_budget=Pass, prompt_injection=Pass, and
    disabled_provider_fallback=Pass. After user rejection, the Web Shell
    runtime dashboard was reworked so this path no longer exposes
    `PFI-011 Deep Path`, `Provider`, `QA`, or raw disabled-provider labels on
    the user-facing surface. Latest browser UI acceptance returned
    `status=Pass`, `pass=134`, `fail=0`, screenshot
    `data/systemAudit/UIVisualAcceptance_20260620_063836.png`. Gate 5 is
    closed for the current local evidence scope and must be re-run in Gate 7.
28. Gate 6 / Gate 7 / PFI-012 MVP Release Gate:
    Strict release-gate evidence is implemented and must be replayed for the
    current branch head before closeout.
    `scripts/pfi012MVPReleaseGate.sh` emits
    `PFI012MVPReleaseGateAcceptanceV1` evidence for PFI-001..012 and
    Gate1..7 matrix coverage, P0 open count zero, P1 release dispositions,
    latest UAT/vertical/gate artifacts, privacy audit, active legacy freeze,
    signed checksum manifest, Operational Store records, and external
    CI/rollback fail-closed state. Current release closeout uses GitHub
    `PFI_OS Smoke` on branch head, rollback tag
    `pfi-os-rollback-20260620-redo-final`, and strict
    `scripts/pfi012MVPReleaseGate.sh --require-external-release-evidence`.
    Gate 6 and Gate 7 are closed for the current evidence scope only after
    that strict replay passes; any new branch-head commit must repeat
    CI/tag/strict replay.

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
- Phase B Markets workflow contract for local observed market bars, market
  event logs, hotspot cards, sentiment cards, freshness metadata, and
  Operational Store evidence/job/review-task recording.
- Phase B Research + Policy workflow contract for reviewed policy
  opportunities, report evidence-gap tasks, authority/evidence cards,
  decision-support fields, and Operational Store evidence/job/review-task
  recording.
- Phase B Portfolio workflow contract for reviewed private holdings,
  private-derived holding snapshots, quality/exposure/concentration/risk cards,
  decision-support fields, and Operational Store source/evidence/job/task plus
  holding snapshot recording.
- Phase C workflow runtime read model for promoting the four Phase B workflow
  records into cached Web Shell runtime cards, Fast Path metadata, retry
  policy, background jobs, task-center rows, and Operational Store runtime
  evidence records without leaking private holdings.
- Phase C workflow runtime scheduler for idempotent cache-refresh job writes,
  bounded retry/backoff, 60-second cached acceptance metadata, runtime
  evidence recording, and fail-closed exhausted retries without provider,
  broker, LLM, network, order-execution, or holding-mutation dependencies.
- Phase C Web Shell workflow-card rendering for `workflow_cards`, including
  Fast Path badge updates, workflow evidence buttons, responsive card grid,
  private-safe evidence drawer population, and a rendered Chrome smoke check.
- Phase D local deployment readiness contract for required repo surfaces,
  data-home/Operational SQLite boundaries, backup/restore target paths,
  DisabledProvider/local-model optionality, and read-only safety constraints.
- Phase D backup/restore acceptance complete with private runtime SQLite
  backup, private restore staging, checksum/row-count validation,
  GitHub-safe sanitized public summary, and no Operational SQLite mutation.
- Phase 5 acceptance package complete as a GitHub-safe manifest and handoff
  document for Phase 6 deployment preparation, with private/user-supplied
  materials explicitly kept outside public Git.
- v0.1.1 findings baseline complete for the v0.2 handoff/iteration packs:
  12 P0 findings, 18 P1 findings, 1 closed, 18 partial, and 11 open.
- PFI Web Shell is now the default runtime path in `StartPFIOS.command`,
  `scripts/startPFIOS.sh`, `streamlit_app.py`, `web/index.html`, and the Web
  Shell contract; `PFI_UI_V2=0` remains the legacy opt-out.
- PFI-003 Durable Job Store first slice is implemented in
  `src/pfi_os/application/durable_jobs.py` with contract tests in
  `tests/contract/test_pfi003_durable_jobs.py`, CLI tests in
  `tests/contract/test_pfi003_supervisor_cli.py`, script entry
  `scripts/pfiSupervisor.sh`, and a development record in
  `docs/development/PFI003_DURABLE_JOB_STORE.md`.
- Downloads and Applications `PFI_OS.app` entries were reinstalled and verified
  against the current worktree. Desktop remains best-effort because macOS can
  attach Finder/resource metadata there.
- Homepage ingestion no longer falls back to retired command-center latest
  cache files; stale local SQLite rows containing retired value-ledger and
  command-center metadata are hidden from the active homepage summary.
- Cache cleanup was run through `scripts/cleanCache.sh --json`; only
  disposable pycache, pytest cache, and root runtime log files were deleted.
- User-facing UI return/rework complete after rejection: the PFI Web Shell no
  longer depends on direct old-page jumps for core feature cards. The current
  visual evidence is `data/systemAudit/UIVisualAcceptance_latest.json` with
  `status=Pass`, `pass=98`, `fail=0`, and `started_by_acceptance=false` for
  the manually started local service path. Screenshot:
  `data/systemAudit/UIVisualAcceptance_20260620_011640.png`.
- PFI-004 local Golden/PIT proof complete:
  `src/pfi_os/application/pfi004_truth_golden.py`,
  `tests/contract/test_pfi004_truth_golden.py`, and
  `docs/development/PFI004_GOLDEN_PIT.md`. Target tests passed 15/15 for
  Golden metrics, PIT replay, dual-read reconciliation, `PIT_INVALID_WRITE`,
  and no-execution boundaries.
- PFI-001 PR/CI injected-failure proof complete:
  root workflow `.github/workflows/pfi-os-smoke.yml`,
  `scripts/pfiCiInjectedFailureProof.sh`, and PR #2 GitHub Actions run
  `27856494975` on commit `9ed86b6dc43e769242db18d6b7bd60c1a7a538a8`.
  Successful job steps include `Run PFI target gate` and
  `Prove injected failure is blocked`.
- PFI-005 Gate 2 shell acceptance contract complete:
  `scripts/pfiGate2ShellAcceptance.sh`,
  `tests/contract/test_pfi005_gate2_shell_acceptance.py`, and
  `docs/development/PFI005_GATE2_SHELL_ACCEPTANCE.md`. It verifies four named
  browser UAT journeys, same-shell function panels, Chinese-first/no-legacy
  visible surface, WCAG structural proof, optional local axe scan, and
  interaction performance budgets. Latest local evidence: focused contracts
  63 passed; browser acceptance 126 pass / 0 fail; target gate 46 passed plus
  secret scan; legacy identity regression 2 passed; `git diff --check` passed.
- PFI-006 Markets vertical acceptance complete for local Gate 3 evidence:
  `src/pfi_os/application/pfi006_markets_acceptance.py`,
  `scripts/pfi006MarketsAcceptance.sh`,
  `tests/contract/test_pfi006_markets_vertical_acceptance.py`, and
  `docs/development/PFI006_MARKETS_VERTICAL_ACCEPTANCE.md`. Latest acceptance
  passed 13/13 with deterministic Golden metrics and rollback proof. Focused
  tests passed 62/62, target gate passed 52 tests plus secret scan, and UI
  visual acceptance passed 98/98.
- PFI-007 Research + Policy vertical acceptance complete for local Gate 3
  evidence:
  `src/pfi_os/application/pfi007_research_policy_acceptance.py`,
  `scripts/pfi007ResearchPolicyAcceptance.sh`,
  `tests/contract/test_pfi007_research_policy_vertical_acceptance.py`, and
  `docs/development/PFI007_RESEARCH_POLICY_VERTICAL_ACCEPTANCE.md`. Latest
  acceptance passed 14/14 with citation locator, report manifest, deterministic
  Golden metrics, and rollback proof. Focused tests passed 62/62, target gate
  passed 58 tests plus secret scan, and UI visual acceptance passed 98/98.
- PFI-008 Portfolio vertical acceptance complete for local Gate 3 evidence:
  `src/pfi_os/application/pfi008_portfolio_acceptance.py`,
  `scripts/pfi008PortfolioAcceptance.sh`,
  `tests/contract/test_pfi008_portfolio_vertical_acceptance.py`, and
  `docs/development/PFI008_PORTFOLIO_VERTICAL_ACCEPTANCE.md`. Latest
  acceptance passed 16/16 with synthetic import ledger, corporate-action/FX/
  cash Golden checks, broker-to-snapshot reconciliation, risk constraints,
  review-only decision proposal, same-shell Portfolio controls, holding
  snapshot records, and rollback proof. Focused PFI-008 contract passed 6/6;
  related Web Shell/script tests passed 58/58; target gate passed 64 tests plus
  secret scan and diff check.
- PFI-009 Strategy vertical acceptance complete for local Gate 3 evidence:
  `src/pfi_os/application/pfi009_strategy_acceptance.py`,
  `scripts/pfi009StrategyAcceptance.sh`,
  `tests/contract/test_pfi009_strategy_vertical_acceptance.py`, and
  `docs/development/PFI009_STRATEGY_VERTICAL_ACCEPTANCE.md`. Latest
  acceptance passed 18/18 with PIT bars, corporate-action/delisted fixture,
  train/test validation, walk-forward validation, no-future-data proof,
  market-feel future hiding, review-only strategy registry, cancel/resume
  runtime proof, same-shell Strategy controls, task/evidence records, and
  rollback proof. Focused PFI-009 contract passed 7/7; related Web
  Shell/script tests passed 63/63; target gate passed 71 tests plus secret
  scan and diff check.
- PFI-010 Minute Fast Path complete for local deterministic Gate 4 evidence:
  `src/pfi_os/application/pfi010_minute_fast_path.py`,
  `scripts/pfi010MinuteFastPathAcceptance.sh`,
  `tests/contract/test_pfi010_minute_fast_path.py`, and
  `docs/development/PFI010_MINUTE_FAST_PATH.md`. Latest acceptance passed
  11/11 with three legal local sources, durable incremental worker, p95=44.0s,
  page-closed update proof, failure injection recovery, logical 1h/24h soak,
  Operational Store records, and Web Shell runtime dashboard exposure.
- PFI-011 Local LLM Deep Path complete for local Gate 5 evidence:
  `src/pfi_os/application/pfi011_local_llm_deep_path.py`,
  `scripts/pfi011LocalLLMDeepPathAcceptance.sh`,
  `tests/contract/test_pfi011_local_llm_deep_path.py`, and
  `docs/development/PFI011_LOCAL_LLM_DEEP_PATH.md`. Latest acceptance passed
  12/12 with hardware audit, provider interface, DisabledProvider fallback,
  citation/schema QA, timeout fallback, cancel, resource budget,
  prompt-injection guard, Operational Store records, and Web Shell runtime
  dashboard exposure.
- PFI-012 MVP Release Gate complete for local release-candidate evidence:
  `src/pfi_os/application/pfi012_mvp_release_gate.py`,
  `scripts/pfi012MVPReleaseGate.sh`,
  `tests/contract/test_pfi012_mvp_release_gate.py`, and
  `docs/development/PFI012_MVP_RELEASE_GATE.md`. Latest local release gate
  passed 11/11 with PFI-001..012 and Gate1..7 matrix coverage, P0=0, P1
  dispositions, UAT/latest artifact checks, privacy audit, active legacy
  freeze, signed checksum manifest, and external CI/rollback state recorded as
  `PendingExternal`.

## Start Here

Read in this order:

1. `README.md`
2. `AGENTS.md`
3. `PLANS.md`
4. `docs/development/PFI_PHASE_0_TO_A_RECORD.md`
5. `docs/development/PFI_GOAL_GATE_MATRIX.md`
6. `docs/development/PFI_REPRODUCIBLE_ENV.md`
7. `docs/development/PFI004_GOLDEN_PIT.md`
8. `docs/development/PFI005_GATE2_SHELL_ACCEPTANCE.md`
9. `docs/development/PFI006_MARKETS_VERTICAL_ACCEPTANCE.md`
10. `docs/development/PFI007_RESEARCH_POLICY_VERTICAL_ACCEPTANCE.md`
11. `docs/development/PFI010_MINUTE_FAST_PATH.md`
12. `docs/development/PFI011_LOCAL_LLM_DEEP_PATH.md`
13. `docs/development/PFI012_MVP_RELEASE_GATE.md`
14. `docs/product/PFI_OS_PRODUCT_CONSTITUTION.md`
15. `docs/product/PFI_OS_INFORMATION_ARCHITECTURE.md`
16. `docs/data/PFI_DATA_BOUNDARIES.md`
17. `docs/data/PFI_SOURCE_OF_TRUTH.md`
18. `docs/ux/PFI_UX_CONTRACT.md`
19. `docs/ux/PFI_WEB_SHELL_ACCEPTANCE.md`
19. `docs/architecture/PFI_TARGET_ARCHITECTURE.md`
20. `docs/phase/PHASE_A_DATA_FOUNDATION.md`
21. `docs/phase/PHASE_A_COMPLETION_AUDIT.md`
22. `docs/phase/PHASE_B_MARKETS.md`
23. `docs/phase/PHASE_B_RESEARCH_POLICY.md`
24. `docs/phase/PHASE_B_STRATEGY_LAB.md`
25. `docs/phase/PHASE_B_PORTFOLIO.md`
26. `docs/phase/PHASE_C_WORKFLOW_RUNTIME.md`
27. `docs/phase/PHASE_D_DEPLOYMENT_READINESS.md`
28. `docs/phase/PHASE_5_ACCEPTANCE_PACKAGE.md`
29. `docs/phase/V0_1_1_FINDINGS_BASELINE.md`
30. `docs/archive/legacy-migration.md`

## Current Verification Evidence

Latest user-orientation repair verification, 2026-06-20:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' /opt/anaconda3/bin/python3.12 -m pytest tests/test_pfi_legacy_terms.py tests/test_pfi_product_contracts.py tests/contract/test_phase_a_homepage_ingestion.py tests/contract/test_pfi_web_shell_contract.py tests/e2e/test_pfi_web_shell_static_flow.py tests/test_scripts.py tests/test_macos_runtime_acceptance.py -q
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' /opt/anaconda3/bin/python3.12 -m pytest tests/test_app_dashboard.py tests/test_pfi_identity.py tests/test_macos_lifecycle_readiness.py tests/test_macos_app_acceptance_lite.py tests/test_macos_public_acceptance.py tests/test_pfi_legacy_terms.py tests/test_pfi_product_contracts.py -q
scripts/uiVisualAcceptance.sh --summary-json
scripts/macosAppAcceptanceLite.sh --summary-json
PYTHONDONTWRITEBYTECODE=1 /opt/anaconda3/bin/python3.12 -m py_compile src/pfi_os/app/streamlit_app.py src/pfi_os/system/macos_runtime_acceptance.py src/pfi_os/system/dev_readiness.py src/pfi_os/application/homepage_ingestion.py src/pfi_os/application/homepage_summary.py
zsh -o nobgnice -n StartPFIOS.command scripts/startPFIOS.sh scripts/stopPFIOS.sh scripts/uiVisualAcceptance.sh
git diff --check
scripts/statusPFIOS.sh --summary-json
```

Observed:

- Target Web Shell, product, legacy-term, homepage-ingestion, script, and macOS
  runtime tests passed: 72 passed.
- Related dashboard, identity, lifecycle, app-acceptance, public-acceptance,
  legacy-term, and product-contract tests passed: 72 passed.
- `scripts/uiVisualAcceptance.sh --summary-json` passed 66/66 checks against
  the actual Streamlit runtime at `http://127.0.0.1:8501`, including rendered
  PFI Web Shell iframe, Chinese primary surface, all six workspace switches,
  eight homepage feature links, six real function-page opens, no retired
  identity/value/search labels, no Streamlit chrome text, and screenshot capture
  (`data/systemAudit/UIVisualAcceptance_20260620_000915.png`,
  `screenshot_bytes=209512`).
- Homepage now keeps a stable direct function matrix for single-symbol
  backtest, parameter scan, market-feel training, hotspot analysis, reports,
  holdings, policy, and data center; runtime cache summaries cannot replace the
  core function matrix.
- The Web Shell date context now defaults to the browser-local current date on
  first open while preserving an existing user selection.
- Function pages hide Streamlit toolbar/menu/status chrome and use PFI_OS-first
  visible identity; the embedded shell, heartbeat, refresh, and countdown HTML
  now use the current iframe API rather than the deprecated component call.
- `StartPFIOS.command`, `scripts/startPFIOS.sh`, `scripts/stopPFIOS.sh`, and
  `scripts/statusPFIOS.sh` use Chinese-facing startup/status/stop output;
  startup and visual-acceptance scripts disable zsh background nice noise for
  real execution.
- `scripts/macosAppAcceptanceLite.sh --summary-json` passed with 29 pass, 0
  fail, and 2 info checks; Downloads/Applications app entries remain bound to
  the current project and runtime status reported stopped in Chinese.
- `py_compile`, low-noise `zsh -o nobgnice -n`, `git diff --check`, and final
  service-status checks passed; no PFI_OS service remained running on ports
  8501-8510.

Latest PFI-003 Durable Job Store verification, 2026-06-20:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' /opt/anaconda3/bin/python3.12 -m pytest tests/contract/test_pfi003_durable_jobs.py -q
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' /opt/anaconda3/bin/python3.12 -m pytest tests/contract/test_pfi003_supervisor_cli.py -q
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' /opt/anaconda3/bin/python3.12 -m pytest tests/contract/test_pfi003_durable_jobs.py tests/contract/test_pfi003_supervisor_cli.py tests/contract/test_phase_c_workflow_runtime_read_model.py tests/contract/test_pfi_web_shell_contract.py tests/e2e/test_pfi_web_shell_static_flow.py tests/test_scripts.py -q
PYTHONPYCACHEPREFIX=/private/tmp/pfi003-pycache /opt/anaconda3/bin/python3.12 -m py_compile src/pfi_os/application/durable_jobs.py src/pfi_os/examples/pfi_supervisor.py src/pfi_os/application/workflow_runtime_read_model.py src/pfi_os/application/__init__.py
PFI_PYTHON=/opt/anaconda3/bin/python3.12 scripts/pfiSupervisor.sh --db-path /private/tmp/pfi003-supervisor-smoke/pfi.sqlite --json doctor --recover-expired
PFI_PYTHON=/opt/anaconda3/bin/python3.12 scripts/pfiSupervisor.sh --db-path /private/tmp/pfi003-supervisor-smoke/pfi.sqlite --json smoke-double-worker --job-type shell_double_worker --idempotency-key shell-double-worker
PFI_PYTHON=/opt/anaconda3/bin/python3.12 scripts/pfiSupervisor.sh --db-path /private/tmp/pfi003-supervisor-smoke/pfi.sqlite --json smoke-crash-recovery --job-type shell_crash_recovery --idempotency-key shell-crash-recovery --lease-seconds 2 --advance-seconds 3
rm -rf /private/tmp/pfi003-supervisor-acceptance
mkdir -p /private/tmp/pfi003-supervisor-acceptance
PFI_PYTHON=/opt/anaconda3/bin/python3.12 scripts/pfiSupervisor.sh --db-path /private/tmp/pfi003-supervisor-acceptance/pfi.sqlite --json acceptance --runtime-dir /private/tmp/pfi003-supervisor-acceptance --lease-seconds 2 --advance-seconds 3 --worker-timeout-seconds 15 --sleep-wake-seconds 120 --hold-seconds 30
git diff --check
```

Observed: the focused durable job contract test passed 8/8 and the supervisor
CLI contract test passed 7/7. The related runtime/Web Shell target group passed
73/73. The contract covers
idempotency, atomic claim, active lease ownership, heartbeat extension,
owner-only completion/failure, bounded retry, dead letter, cancel/resume,
expired-lease recovery, Web/API/Worker readiness separation, and research-only
no-execution safety boundaries. The CLI smoke checks cover double-worker claim
exclusion and simulated crash recovery through expired lease recovery. The
release acceptance harness used a temporary SQLite DB under `/private/tmp`,
passed 10/10 checks, and produced
`pfi003_supervisor_acceptance_manifest.json`,
`pfi003_supervisor_acceptance_backup.sqlite`, and
`pfi003_supervisor_acceptance.jsonl`, plus sanitized launchd/log-rotation
artifacts. Phase C runtime read model now exposes PFI-003 durable jobs through
`supervisor_runtime`, and Web Shell consumes it in the Data/System workspace.

Latest PFI-001 reproducible-environment repair verification, 2026-06-20:

```bash
python -m pytest tests/contract/test_pfi_reproducible_env.py tests/test_scripts.py -q
scripts/secretScan.sh
rm -rf /tmp/pfi_os_clean_env_pfi001
PFI_PYTHON=/opt/anaconda3/bin/python3.12 PFI_VENV_DIR=/tmp/pfi_os_clean_env_pfi001 scripts/installLockedEnv.sh
PFI_PYTHON=/tmp/pfi_os_clean_env_pfi001/bin/python scripts/pfiGate.sh fast
PFI_PYTHON=/tmp/pfi_os_clean_env_pfi001/bin/python scripts/pfiGate.sh target
PFI_PYTHON=/tmp/pfi_os_clean_env_pfi001/bin/python PFI_UI_V2=1 scripts/startPFIOS.sh
curl http://127.0.0.1:8501/_stcore/health
scripts/stopPFIOS.sh
```

Observed: clean install from `requirements.lock` succeeded in
`/tmp/pfi_os_clean_env_pfi001`; fast gate passed 13 tests plus secret scan;
target gate passed 36 tests plus secret scan and diff check; offline warm start
reached Streamlit health without dependency installation output.

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
python -m pytest tests/contract/test_pfi_web_shell_contract.py tests/contract/test_phase_a_homepage_ingestion.py tests/contract/test_v011_findings_baseline.py tests/test_scripts.py::test_macos_app_installer_builds_standard_app_bundle -q
python -m compileall src/pfi_os/application src/pfi_os/app/streamlit_app.py
git diff --check
```

The focused suite passed locally before this handoff update. Re-run the target
commands after any follow-up edits.

Latest runtime smoke:

- `PFI_UI_V2=1 scripts/startPFIOS.sh` launched `http://127.0.0.1:8501`.
- Browser iframe text contained `PFI OS`, `首页`, `市场`, `研究`, `持仓`,
  `策略实验室`, and `数据与系统`.
- Browser iframe text did not contain retired navigation, retired value-ledger,
  retired command-center, retired value-artifact, or retired product identity
  text.
- `scripts/stopPFIOS.sh` stopped the local service after verification.

Latest user-facing PFI rejection rework, 2026-06-20:

- Root cause repaired: Streamlit now renders the inline PFI Web Shell only via
  `components.html`; the prior `st.iframe(markup, ...)` path could treat full
  HTML as a URL/text surface on compatible Streamlit versions.
- Browser state key moved from `pfi-context-v1` to `pfi-context-v2`, so stale
  pre-repair localStorage cannot keep users on old feature/detail state.
- Market workspace now exposes a direct `热点分析` feature button in addition
  to market slice, overlay, saved view, ETF, theme, watchlist, and source
  status controls.
- Web Shell feature cards open same-shell Chinese function panels first.
  Detailed Streamlit function pages open in a new tab because Streamlit
  component iframe sandboxing allows popups but blocks top-window navigation.
- `scripts/pfiGate2ShellAcceptance.sh --summary-json`: `Pass`, 228 pass /
  0 fail / 2 info. The real browser UAT covers six primary workspaces plus
  backtest, market-feel training, parameter scan, simulation, hotspots,
  reports/policy, portfolio holdings review, and data diagnostics.
- `scripts/uiVisualAcceptance.sh --summary-json`: `Pass`, 130 pass / 0 fail;
  screenshot:
  `data/systemAudit/UIVisualAcceptance_20260620_042620.png`.
- `scripts/macosAppAcceptanceLite.sh --summary-json`: `Pass`, 29 pass /
  0 fail / 2 info. Desktop, Downloads, and Applications app entries have
  `CFBundleDisplayName` and `CFBundleName` set to `PFI OS`, executable
  `PFI_OS`, and `PFI_OS_PROJECT_ROOT` bound to this checkout.
- `python -m pytest tests/contract/test_pfi_web_shell_contract.py tests/e2e/test_pfi_web_shell_static_flow.py -q`:
  22 passed.
- `PFI_PYTHON=/private/tmp/pfi_os_ci_repro/bin/python PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' scripts/pfiGate.sh target`:
  58 passed, 2 warnings; Secret scan passed.
- `scripts/statusPFIOS.sh` after acceptance: `PFI OS 未在端口 8501-8510 运行。`

## Not Done

- GitHub draft PR #2 is the current mergeable integration path for this work.
- Legacy Streamlit pages still contain provider/runtime workflows outside the
  new Web Shell, but remaining public `ROOT / "data"` top-level paths are
  contract-classified and no longer include private input ledgers, runtime
  acceptance evidence, vectorized latest JSON, or uploaded CSV temp files.
- Existing legacy holdings sync and ResearchBus workflows are not fully moved
  onto Operational Store repositories.
- DuckDB/Parquet query surfaces remain in the existing `DataStore`.
- Phase C SSE/WebSocket progress is not complete and should only be added if
  it materially improves local observability.
- Controlled local deployment acceptance is deferred unless the release gate
  requires a real service start/stop check.
- User-supplied Phase 6 deployment materials remain external: local repository
  backup, hardware/disk audit, sanitized holdings, representative symbols and
  policy documents, Fast Path target source list, workflow examples, and final
  subjective acceptance score.
- Tracked legacy command-center and value-ledger artifacts
  still exist as historical files. Active PFI homepage ingestion ignores them;
  physical deletion should be handled by a dedicated legacy-data migration run.
- PFI-003 still needs CI/release replay before Gate 7, but no local
  implementation gap remains for Gate 1.

## Next Step

Continue from v0.2 PFI-goal execution:

1. Use `docs/development/PFI_GOAL_GATE_MATRIX.md` as the active completion
   matrix for PFI-001 through PFI-012 and Gate 1 through Gate 7.
2. Next recommended issue: external Gate 7 evidence.
3. Attach GitHub CI pass URL and rollback ref, then rerun
   `scripts/pfi012MVPReleaseGate.sh --require-external-release-evidence`.

## Latest User Rejection Repair, 2026-06-20

User rejected the previous delivery because the running surface still looked
legacy, had too much English/raw technical text, and feature jumps/detail pages
were unusable. The repair run changed the user-visible PFI surface, not the
underlying research/business logic.

Changed:

- `web/app/shell.js`: feature jump URLs now resolve against the top-level PFI
  app URL or `document.referrer`, so Streamlit iframe links no longer resolve
  to the component iframe itself.
- `src/pfi_os/app/streamlit_app.py`: visible detail-page sidebar now uses the
  active PFI six-entry navigation; detail pages install compatibility wrappers
  for older Streamlit `dataframe`/`plotly_chart` width behavior and a
  `segmented_control` fallback; system self-check only appears on 总控驾驶舱
  and 数据中心.
- `src/pfi_os/integrations/holdings_book.py` and
  `src/pfi_os/integrations/external_systems.py`: user-facing holdings text now
  says `PFI OS` instead of `PFIOS`.
- `data/commandCenter/EVACommandCenter_*`: removed from the tracked working
  tree; `PFICommandCenter_20062026.*` and `PFICommandCenter_latest.*` were
  regenerated.
- Tests updated in `tests/e2e/test_pfi_web_shell_static_flow.py` and
  `tests/test_app_dashboard.py`.

Verification:

- UI/static/dashboard: 76 passed, 2 existing protobuf warnings.
- Holdings/Web focused: 30 passed, 4 existing pandas future warnings.
- Browser UI acceptance:
  `scripts/uiVisualAcceptance.sh --summary-json --start-timeout 120` =>
  `status=Pass`, 130 pass / 0 fail / 0 info.
- Target gate:
  `PFI_PYTHON=/private/tmp/pfi_os_ci_repro/bin/python PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' scripts/pfiGate.sh target`
  => 73 passed, secret scan passed, diff check passed.
- `git diff --check`: pass.

Additional Command Center display repair:

- `src/pfi_os/executive/command_center.py`: Markdown/PDF display layer now uses
  Chinese titles, sections, table headers, statuses, and action guidance while
  leaving JSON contract fields intact.
- PDF output now prefers a system-font visual PDF path so Chinese text renders
  without `????`; latest regenerated Markdown/PDF byte checks show no `????`,
  no `EVA`, no `PFIOS`, and no `PFI_OS`.
- `tests/test_command_center.py`: updated to enforce Chinese Markdown headings
  and no literal `????` in generated PDF bytes.

Next recommended issue after strict PFI-012 replay:
prepare merge/release handoff. Do not mark the long-running PFI-001..PFI-012
goal complete if another branch-head commit is added without rerunning
GitHub CI, refreshing rollback tag target, and rerunning strict PFI-012.

Follow-up rejection repair, 2026-06-20:

- User rejected the running delivery again for English/noisy visible text and
  unusable feature blocks.
- Verified installed user entry points: `~/Downloads/PFI_OS.app` and
  `/Applications/PFI_OS.app` both display `PFI OS` and bind
  `PFI_OS_PROJECT_ROOT` to this checkout; no `EVA` app was found in Downloads
  or Applications; no PFI service remained running on ports 8501-8510 before
  the acceptance rerun.
- `web/app/shell.js`: PFI-011 local-model runtime card now shows Chinese
  labels only: `本地模型`, `本地模型深度路径`, `模型 外部模型未启用`,
  `校验通过`, and `提示注入防护通过`.
- `tests/e2e/test_pfi_web_shell_static_flow.py`,
  `tests/contract/test_pfi011_local_llm_deep_path.py`, and
  `scripts/uiVisualAcceptance.sh` now reject visible/user-surface remnants:
  `DisabledProvider`, `Deep Path`, `Provider `, `QA `, and
  `PFI-011 Deep Path`.
- Verification:
  `tests/contract/test_pfi011_local_llm_deep_path.py` plus
  `tests/e2e/test_pfi_web_shell_static_flow.py` => 21 passed.
- Real browser verification:
  `scripts/uiVisualAcceptance.sh --summary-json` =>
  `PFIOSUIVisualAcceptanceV1`, `status=Pass`, 134 pass / 0 fail,
  screenshot bytes 145960.

Second user-facing rejection repair, 2026-06-20:

- User rejected the delivery again because the product still exposed
  English/noisy surfaces and function blocks did not behave as usable
  navigation.
- `web/index.html` and `web/app/shell.js`: primary feature actions now stay
  inside PFI Web Shell and reveal `data-function-runner`, a same-shell Chinese
  operation panel with steps, status, output fields, and explicit
  no-broker/no-order boundaries.
- `src/pfi_os/app/streamlit_app.py`: default entry no longer falls through to
  legacy Streamlit detail pages via `pfi_shell=0`; legacy detail pages require
  explicit `pfi_legacy=1` and are outside the default user path.
- `web/app/shell.js`: feature cards are no longer truncated after eight cards,
  so Strategy Lab exposes 模拟实验; Portfolio also exposes a direct 持仓 card.
- `scripts/pfiGate2ShellAcceptance.sh` and `scripts/uiVisualAcceptance.sh`:
  browser acceptance now fails if primary actions open a new legacy page instead
  of the same-shell operation panel.
- Verification:
  - Focused Web Shell/Gate2 contracts:
    `tests/contract/test_pfi_web_shell_contract.py`,
    `tests/e2e/test_pfi_web_shell_static_flow.py`, and
    `tests/contract/test_pfi005_gate2_shell_acceptance.py` => 30 passed.
  - Gate2 browser UAT:
    `PFIGate2ShellAcceptanceV1 status=Pass`, 228 pass / 0 fail / 2 info,
    screenshot
    `data/systemAudit/PFIGate2ShellAcceptance_20260620_071550.png`.
  - UI visual browser acceptance:
    `PFIOSUIVisualAcceptanceV1 status=Pass`, 146 pass / 0 fail / 0 info,
    screenshot `data/systemAudit/UIVisualAcceptance_20260620_071622.png`.
  - Target gate:
    `scripts/pfiGate.sh target` => 93 passed, secret scan passed.
  - `zsh -n`, `git diff --check`, and post-run service status all passed;
    no PFI OS service remained running on ports 8501-8510.

Third user-facing rejection redo, 2026-06-20:

- User rejected the delivery again because visible text still felt English/noisy
  and feature blocks/jumps were not usable enough for a user-facing PFI product.
- `web/app/shell.js`: every visible feature card now maps to a concrete
  same-shell function panel instead of passive workspace-only jumps. This covers
  公司研究, 基金研究, 指数与 ETF, 主题催化, 自选监控, 来源登记, 任务监控,
  隐私边界, 备份恢复, 组合暴露, 集中度风险, 纪律检查, 订单意图, and the
  existing core 回测/盘感/政策/数据 functions.
- Function-panel checks and descriptions were rewritten to Chinese user
  language; raw visible field names such as `bar_checksum`, `source_url`,
  `RunMetadata`, `NeedsMoreEvidence`, and `target_weight_change=0` are now
  blocked by contract tests for Web Shell function panels.
- `scripts/pfiGate2ShellAcceptance.sh`: Gate2 browser acceptance now
  exhaustively clicks every visible feature card across the six primary
  entrances. Each control must be a button, open a same-shell Chinese panel,
  reveal a same-shell operation panel, avoid new pages, and avoid
  `pfi_legacy=1`/`pfi_shell=0`.
- Verification:
  - Focused user-facing contracts:
    `tests/contract/test_pfi_web_shell_contract.py`,
    `tests/e2e/test_pfi_web_shell_static_flow.py`,
    `tests/contract/test_pfi005_gate2_shell_acceptance.py`, and
    `tests/contract/test_pfi007_research_policy_vertical_acceptance.py`
    => 38 passed.
  - Gate2 browser UAT:
    `PFIGate2ShellAcceptanceV1 status=Pass`, 844 pass / 0 fail / 2 info,
    `all_feature_control_panels_opened=46`, screenshot
    `data/systemAudit/PFIGate2ShellAcceptance_20260620_073524.png`.
  - UI visual browser acceptance:
    `PFIOSUIVisualAcceptanceV1 status=Pass`, 146 pass / 0 fail / 0 info,
    screenshot `data/systemAudit/UIVisualAcceptance_20260620_073602.png`.
