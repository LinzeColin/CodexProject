# PFI OS Handoff

Last updated: 2026-06-20 Australia/Sydney

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
    complete for the local repair scope. PFI-001 still needs PR/CI injected
    failure evidence before release Gate 1 is fully closed.
17. v0.2 PFI-003 runtime supervisor:
    Durable Job Store core lifecycle is implemented on top of `job_records`.
    It covers idempotent enqueue, atomic claim, lease, heartbeat, bounded
    retry, cancel/resume, expired-lease recovery, and dead letter.
    `scripts/pfiSupervisor.sh` now exposes contract/status/doctor/lifecycle
    commands plus double-worker and crash-recovery smoke. It is not yet the
    full release-grade supervisor/launchd/sleep-wake/crash matrix.

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
- Homepage ingestion no longer falls back to retired
  `EVACommandCenter_latest.json`; stale local SQLite rows containing retired
  value-ledger and command-center metadata are hidden from the active homepage
  summary.
- Cache cleanup was run through `scripts/cleanCache.sh --json`; only
  disposable pycache, pytest cache, and root runtime log files were deleted.

## Start Here

Read in this order:

1. `README.md`
2. `AGENTS.md`
3. `PLANS.md`
4. `docs/development/PFI_PHASE_0_TO_A_RECORD.md`
5. `docs/development/PFI_GOAL_GATE_MATRIX.md`
6. `docs/development/PFI_REPRODUCIBLE_ENV.md`
7. `docs/product/PFI_OS_PRODUCT_CONSTITUTION.md`
8. `docs/product/PFI_OS_INFORMATION_ARCHITECTURE.md`
9. `docs/data/PFI_DATA_BOUNDARIES.md`
10. `docs/data/PFI_SOURCE_OF_TRUTH.md`
11. `docs/ux/PFI_UX_CONTRACT.md`
12. `docs/ux/PFI_WEB_SHELL_ACCEPTANCE.md`
13. `docs/architecture/PFI_TARGET_ARCHITECTURE.md`
14. `docs/phase/PHASE_A_DATA_FOUNDATION.md`
15. `docs/phase/PHASE_A_COMPLETION_AUDIT.md`
16. `docs/phase/PHASE_B_MARKETS.md`
17. `docs/phase/PHASE_B_RESEARCH_POLICY.md`
18. `docs/phase/PHASE_B_STRATEGY_LAB.md`
19. `docs/phase/PHASE_B_PORTFOLIO.md`
20. `docs/phase/PHASE_C_WORKFLOW_RUNTIME.md`
21. `docs/phase/PHASE_D_DEPLOYMENT_READINESS.md`
22. `docs/phase/PHASE_5_ACCEPTANCE_PACKAGE.md`
23. `docs/phase/V0_1_1_FINDINGS_BASELINE.md`
24. `docs/archive/legacy-migration.md`

## Current Verification Evidence

Latest user-orientation repair verification, 2026-06-20:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' /opt/anaconda3/bin/python3.12 -m pytest tests/contract/test_pfi_web_shell_contract.py tests/e2e/test_pfi_web_shell_static_flow.py tests/test_scripts.py -q
zsh -n scripts/uiVisualAcceptance.sh scripts/startPFIOS.sh StartPFIOS.command
scripts/uiVisualAcceptance.sh --summary-json
scripts/installPFIOSEntryApps.sh
PFI_CLEANUP_PYTHON=/opt/anaconda3/bin/python3.12 scripts/cleanCache.sh --json
git diff --check
```

Observed:

- Target Web Shell/script tests passed: 48 passed.
- `git diff --check` passed.
- `scripts/uiVisualAcceptance.sh --summary-json` passed 31/31 checks against
  the actual Streamlit runtime at `http://127.0.0.1:8501`, including rendered
  PFI Web Shell iframe, Chinese primary surface, all six workspace switches,
  strategy feature links for `single`, `scan`, and `market_feel`, no visible
  `EVA`, `QuantLab`, `Token ROI`, `Global Search`, and screenshot capture
  (`screenshot_bytes=197759`).
- `scripts/startPFIOS.sh` now defaults to quiet background startup: user-facing
  output is Chinese and Streamlit ANSI/English runtime logs are redirected to
  `data/cache/pfi_os_streamlit.log`. `PFI_START_FOREGROUND=1` remains available
  for debugging.
- `StartPFIOS.command` and `scripts/startPFIOS.sh` only reuse a healthy service
  when the listening process belongs to the current PFI_OS project; unrelated
  Streamlit/EVA-era ports are ignored.
- `~/Downloads/PFI_OS.app` and `/Applications/PFI_OS.app` were reinstalled,
  bound to this checkout, and passed `codesign --verify --deep --strict`.
  Desktop remains an optional convenience copy; macOS Desktop/File Provider can
  attach Finder metadata that blocks strict signature verification there.
- No `EVA*.app` / `EVA_OS*.app` was found in Desktop, Downloads, or
  Applications.
- Cache cleanup removed 31 disposable cache items, 339 files, about 5.2 MB;
  reports, holdings, SQLite, market caches, source samples, and private data
  were outside the deletion policy.

Latest PFI-003 Durable Job Store verification, 2026-06-20:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' /opt/anaconda3/bin/python3.12 -m pytest tests/contract/test_pfi003_durable_jobs.py -q
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' /opt/anaconda3/bin/python3.12 -m pytest tests/contract/test_pfi003_supervisor_cli.py -q
PYTHONPYCACHEPREFIX=/private/tmp/pfi003-pycache /opt/anaconda3/bin/python3.12 -m py_compile src/pfi_os/application/durable_jobs.py src/pfi_os/examples/pfi_supervisor.py
PFI_PYTHON=/opt/anaconda3/bin/python3.12 scripts/pfiSupervisor.sh --db-path /private/tmp/pfi003-supervisor-smoke/pfi.sqlite --json doctor --recover-expired
PFI_PYTHON=/opt/anaconda3/bin/python3.12 scripts/pfiSupervisor.sh --db-path /private/tmp/pfi003-supervisor-smoke/pfi.sqlite --json smoke-double-worker --job-type shell_double_worker --idempotency-key shell-double-worker
PFI_PYTHON=/opt/anaconda3/bin/python3.12 scripts/pfiSupervisor.sh --db-path /private/tmp/pfi003-supervisor-smoke/pfi.sqlite --json smoke-crash-recovery --job-type shell_crash_recovery --idempotency-key shell-crash-recovery --lease-seconds 2 --advance-seconds 3
git diff --check
```

Observed: the focused durable job contract test passed 8/8 and the supervisor
CLI contract test passed 6/6. The contract covers
idempotency, atomic claim, active lease ownership, heartbeat extension,
owner-only completion/failure, bounded retry, dead letter, cancel/resume,
expired-lease recovery, Web/API/Worker readiness separation, and research-only
no-execution safety boundaries. The CLI smoke checks cover double-worker claim
exclusion and simulated crash recovery through expired lease recovery. The
actual shell smoke used a temporary SQLite DB under `/private/tmp` and passed
doctor `7/7`, double-worker `Pass`, and crash-recovery `Pass`.

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
- `st.components.v1.html` currently emits a Streamlit deprecation warning in
  the app runtime. Replace the embedding mechanism in a focused UI-runtime
  task before treating the Web Shell as a release-final surface.

## Next Step

Continue from v0.2 PFI-goal execution:

1. Use `docs/development/PFI_GOAL_GATE_MATRIX.md` as the active completion
   matrix for PFI-001 through PFI-012 and Gate 1 through Gate 7.
2. Next recommended issue: PFI-003 Supervisor/Durable Jobs/lifecycle. Gate 1
   cannot close until double-start, crash, sleep/wake, job lease, cancel,
   resume, dead-letter, backup/restore and private-log scan are proven.
3. Keep PFI-010/PFI-011/PFI-012 active but do not mark them complete until the
   matrix evidence is strong enough for the full acceptance scope.
