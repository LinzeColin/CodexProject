# EVA_OS Handoff

Last updated: 2026-06-17 Australia/Sydney

This file is the public-safe handoff for `LinzeColin/EVA_OS`. It is designed so a future agent can continue development without replaying the previous Codex thread. Local private run history, private holdings/imports, runtime SQLite state, and raw account screenshots are intentionally excluded from the public repository.

## Current Objective

EVA_OS is the renamed product direction for the former EVA_OS / QuantLab workspace. The current goal is to turn the personal research middle-platform into a lower-token, reproducible, product-grade research operating system.

Primary product boundaries:

- research, evidence, backtesting, simulation, reports, review queues, and human-approved order intents only;
- no autonomous real-money trading;
- no unattended broker order placement;
- no stored brokerage passwords, tokens, or API secrets;
- no private holdings/import screenshots in public GitHub.

## Current Source Of Truth

GitHub project:

```text
https://github.com/LinzeColin/EVA_OS
```

Current local working copy:

```text
$EVA_OS_HOME
```

Historical duplicate source path before slimming:

```text
$EVA_OS_HOME
```

The historical path was a subset of the current working copy at this handoff and can be removed after GitHub push verification.

## Start Here

Future agents should read these files first:

1. `README.md`
2. `AGENT_CONTINUITY.md`
3. `15_OPEN_QUESTIONS.md`
4. `UPLOAD_MANIFEST.md`
5. `cleanup/EVA_OS_GitHub_Sync_Local_Slimming_20260613.md`
6. `docs/EVA_OS.md`
7. `docs/Index.md`
8. `docs/MacOSAppAcceptanceLite.md`
9. `docs/MacOSLifecycleReadiness.md`
10. `docs/MacOSRuntimeAcceptance.md`
11. `docs/SystemsMigrationPlan.md`
12. `systems/README.md`
13. `shared/security/system_permissions.json`
14. `systems/finance_ledger/README.md`
15. `systems/industry_research/README.md`

## Delivery Standard

For every meaningful subsystem run:

- work on one subsystem at a time unless the user explicitly expands scope;
- update `HANDOFF.md` only when the status materially changes;
- update docs/tests/scripts affected by the change;
- run focused validation or explain exactly why it could not run;
- do not run heavy smoke suites such as `scripts/finalAcceptanceCheck.sh` or `scripts/ciSmoke.sh` by default; use `scripts/macosAppAcceptanceLite.sh --summary-json`, targeted tests, `git diff --check`, sensitive scans, and explicit app health checks unless the user requests full smoke or a release gate requires it;
- heavy SmokeTest scripts require `EVA_OS_ALLOW_HEAVY_SMOKE=1` for local execution; use this only for deliberate release gates, not routine agent turns;
- GitHub smoke remains available on pull requests and manual dispatch, but is not configured for every `main` push;
- keep public GitHub free of private holdings, account screenshots, raw imports, secrets, venvs, caches, logs, locks, and SQLite runtime state;
- push continuity-critical changes to `LinzeColin/EVA_OS`.

## Completed Foundation

| Area | Status | Main artifacts |
| --- | --- | --- |
| EVA_OS rename direction | Partial | `README.md`, `docs/EVA_OS.md`, `AGENT_CONTINUITY.md` |
| Market Event Layer MVP | Complete MVP | `src/quantlab/data/market_events.py`, `scripts/marketEventLayer.sh`, `docs/MarketEventLayer.md` |
| Reproducible Data Lake MVP | Complete MVP | `src/quantlab/data/lake.py`, `scripts/dataLakeManifest.sh`, `docs/ReproducibleDataLake.md` |
| Event Replay MVP | Complete MVP | `src/quantlab/data/replay.py`, `scripts/eventReplay.sh`, `docs/EventReplay.md` |
| Vectorized Research Mode MVP | Implemented MVP | `src/quantlab/research/vectorized.py`, `scripts/vectorizedResearch.sh`, `docs/VectorizedResearchMode.md` |
| Research chart UX controls | Implemented MVP | `apply_research_chart_ux()`, `research_chart_config()`, hotspot/vectorized Plotly charts |
| Hotspot quick preflight | Implemented default guidance | `EVAOSHotspotQuickPreflightV1`, `hotspot_quick_preflight()`, `render_hotspot_preflight()` |
| Parameter scan preflight | Implemented default guidance | `EVAOSParameterScanPreflightV1`, `parameter_scan_preflight()`, `render_parameter_scan_preflight()` |
| Command Center action router | Implemented default guidance | `EVAOSCommandCenterActionRouterV1`, `command_center_next_actions()`, `render_command_center_action_router()` |
| 52ETF read-only reference | Productized snapshot + comparison | `EVAOS52ETFPublicSnapshotV1`, `EVAOS52ETFHotspotComparisonV1`, `scripts/site52etfSnapshot.sh`, `docs/52ETFReadOnlyReference.md` |
| Executive Command Center | Productized aggregation | `runtime_summary_sources`, `src/quantlab/executive/command_center.py`, `scripts/commandCenter.sh`, `docs/ExecutiveCommandCenter.md` |
| Token ROI | Productized MVP + reviewed value evidence refresh | `EVATokenROIRuntimeSummaryV1`, `EVATokenROIReviewedValueEvidenceRefreshV1`, `docs/TokenROI.md`, `scripts/tokenRoiReviewedValueRefresh.sh` |
| Cashflow | Productized MVP + reviewed-input refresh | `EVAOSCompanyCashFlowRuntimeSummaryV1`, `EVAOSCompanyCashFlowReviewedInputRefreshV1`, `docs/CompanyCashFlowCommand.md`, `scripts/cashFlowReviewedInputRefresh.sh` |
| Policy Intelligence Radar | Productized MVP + reviewed-input refresh | `EVAOSPolicyIntelligenceRuntimeSummaryV1`, `EVAOSPolicyReviewedInputRefreshV1`, `docs/PolicyIntelligenceRadar.md`, `scripts/policyReviewedInputRefresh.sh` |
| Consumption Guard | Productized MVP + reviewed-input refresh | `EVAOSConsumptionGuardRuntimeSummaryV1`, `EVAOSConsumptionGuardReviewedInputRefreshV1`, `docs/ConsumptionGuard.md`, `scripts/consumptionReviewedInputRefresh.sh` |
| Runtime Summary Refresh | Complete low-token refresh | `scripts/refreshRuntimeSummaries.sh`, `EVAOSRuntimeSummaryRefreshV1`, `data/*/*RuntimeSummary_latest.json` |
| macOS entry apps | Complete native launcher | `macos/EVA_OS.app`, `macos/EVA_OS_launcher.c`, `scripts/installEVAOSEntryApps.sh` |
| macOS app acceptance lite | Complete daily entry gate | `EVAOSMacOSAppAcceptanceLiteV1`, `scripts/macosAppAcceptanceLite.sh`, `docs/MacOSAppAcceptanceLite.md` |
| macOS lifecycle readiness | Complete read-only lifecycle gate | `EVAOSMacOSLifecycleReadinessV1`, `scripts/macosLifecycleReadiness.sh`, `docs/MacOSLifecycleReadiness.md` |
| macOS runtime acceptance | Controlled real runtime gate | `EVAOSMacOSRuntimeAcceptanceV1`, `scripts/macosRuntimeAcceptance.sh`, `docs/MacOSRuntimeAcceptance.md` |
| macOS acceptance hub | Complete default user gate | `EVAOSMacOSAcceptanceHubV1`, `scripts/macosAcceptance.sh`, `docs/MacOSAcceptanceHub.md` |
| Report Validation Hub | Complete low-token default entry | `EVAOSReportValidationHubV1`, `scripts/reportValidation.sh`, `docs/ReportValidationHub.md` |
| Unified systems workspace | Finance, industry, and policy source migrated | `systems/*/SYSTEM_MANIFEST.json`, `systems/finance_ledger/source`, `systems/industry_research/source`, `systems/policy_intelligence/source`, `shared/security/system_permissions.json`, `shared/schema/*.json`, `.github/workflows/smoke.yml` |
| ResearchBus workspace adapter | Implemented MVP | `src/quantlab/integrations/workspace_systems.py`, `scripts/syncWorkspaceSystemSummaries.sh`, `tests/test_workspace_systems.py` |
| Unified UI Shell status | Implemented MVP | `src/quantlab/app/dashboard.py`, `src/quantlab/app/streamlit_app.py`, `tests/test_workspace_shell.py` |
| macOS runtime acceptance | Verified on this Mac | `scripts/quantlabRuntime.sh`, `scripts/startQuantLab.sh`, `StartQuantLab.command`, `scripts/finalAcceptanceCheck.sh` |

## 2026-06-16 Token ROI Reviewed Value Evidence Refresh MVP

Completed:

- Added `EVATokenROIReviewedValueEvidenceRefreshV1` for local reviewed value evidence refresh.
- Default private input is `data/private/value/TokenROIReviewedValueEvidence.json`; public GitHub only contains `data/value/TokenROIReviewedValueEvidence.example.json` and `shared/schema/token_roi_reviewed_value_evidence.schema.json`.
- `scripts/tokenRoiReviewedValueRefresh.sh` can build Token ROI ledger outputs and compact runtime summary from reviewed value evidence.
- `scripts/tokenRoiLedger.sh` now accepts `--manual-entry-path`; `scripts/refreshRuntimeSummaries.sh` now accepts `--token-roi-entry-path`.
- `data/value/TokenROIManualEntries.json` is gitignored to reduce accidental upload risk for UI-entered financial evidence.
- Missing private input fails closed with `status=Blocked`, `roi_status=MissingReviewedInput`, no outputs, and no local `/Users/...` report-root leak in the refresh payload.

Focused validation:

```text
py_compile passed for Token ROI reviewed value modules and runtime summary refresh modules
zsh -n passed for tokenRoiReviewedValueRefresh.sh, tokenRoiLedger.sh, refreshRuntimeSummaries.sh, finalAcceptanceCheck.sh
pytest tests/test_token_roi_reviewed_value_refresh.py tests/test_token_roi_ledger.py tests/test_runtime_summary_refresh.py tests/test_scripts.py -q: 31 passed
tokenRoiReviewedValueRefresh.sh missing input: Blocked MissingReviewedInput external_report_root and no /Users leak
tokenRoiReviewedValueRefresh.sh public example: status=Pass roi_status=Quantified records=184 quantified=2 benefit=1420.0 cost=95.5
refreshRuntimeSummaries.sh with --token-roi-entry-path: Token ROI runtime_status=Pass and records_in_summary=False
commandCenter.sh temp smoke: Token ROI source mode=runtime_summary, schema=EVATokenROIRuntimeSummaryV1, PDF magic %PDF-1.4
```

Safety boundary:

- No fabricated revenue, cost saving, avoided loss, asset reuse value, or ROI.
- No live trading, real orders, broker action, payment, bank transfer, or real-money execution.
- Generated full ledgers from private evidence can contain reviewed financial totals and must be inspected before committing or sharing.

## 2026-06-16 macOS Runtime Acceptance

Completed:

- Replaced the `EVA_OS.app` shell executable with a native Mach-O launcher built from `macos/EVA_OS_launcher.c`.
- Installed Desktop, Downloads, and Applications apps now bind `Contents/Resources/EVA_OS_PROJECT_ROOT` to the current local checkout and do not fall back to GitHub.
- `open -n ~/Downloads/EVA_OS.app` was verified to start local EVA_OS, with `/_stcore/health` returning `ok`.
- `StartQuantLab.command` now writes launch-lock pid metadata and removes stale locks without pid metadata; `scripts/stopQuantLab.sh` removes the launch lock during stop.
- Added shared runtime resolver `scripts/quantlabRuntime.sh`.
- Daily launchers now install only `.[app]`, reuse `.venv/.quantlab_app_ready`, honor `QUANTLAB_PYTHON` / `EVA_PYTHON`, avoid the broken local Anaconda runtime, and set `PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python`.
- Moved heavy Word-report exports out of Streamlit top-level imports and made `quantlab.reports` lazy.
- `scripts/installEVAOSEntryApps.sh` now clears extended attributes and ad-hoc signs Desktop, Downloads, and Applications app bundles.
- Added `openpyxl>=3.1` because holdings Excel import/export is a real product path.
- Verification scripts now install test extras only for verification, not for normal app startup.

Verified evidence:

```text
./scripts/installEVAOSEntryApps.sh: installed Desktop, Downloads, Applications EVA_OS.app
codesign --verify --deep: passed for all three installed apps
./scripts/startQuantLab.sh: started Streamlit at http://localhost:8501
curl http://127.0.0.1:8501/_stcore/health: ok
./scripts/statusQuantLab.sh: detected running service, then service was stopped after validation
./scripts/finalAcceptanceCheck.sh: PASS 131, FAIL 0
full pytest inside final acceptance: 352 passed, 2 skipped, 3 subtests passed in 128.00s
non-network daily check: passed, readiness remains NeedsReview due data/provider evidence gates
```

Known validation limitation:

- In-app Browser automation failed before page inspection because the Browser runtime could not initialize local kernel assets. The app itself was validated through Streamlit health, HTTP shell, process status, signed macOS app bundles, and final acceptance. Re-run visual browser acceptance when the Browser plugin/runtime is healthy.

## 2026-06-16 macOS App Acceptance Lite

Completed:

- Added `EVAOSMacOSAppAcceptanceLiteV1` and `scripts/macosAppAcceptanceLite.sh` for daily app-entry acceptance without triggering full smoke.
- Checks Desktop, Downloads, and Applications `EVA_OS.app` bundles, native launcher executable, Info.plist identity, project binding, absence of GitHub fallback, codesign, launcher dry-run, local `_stcore/health`, and status script output.
- Source template `macos/EVA_OS.app` is checked for bundle/executable/Info.plist/fallback/dry-run, but codesign is only required after installation to avoid false failures.
- Streamlit `macOS 生命周期` panel now exposes a `轻量验收` button through the lifecycle allowlist.
- Docs now route daily app-entry diagnosis to `scripts/macosAppAcceptanceLite.sh --summary-json`; `scripts/finalAcceptanceCheck.sh` remains a deliberate release/full-acceptance gate.

Focused validation:

```text
py_compile passed for macOS acceptance module, CLI, system exports, dashboard, streamlit app, and new test
zsh -n passed for scripts/macosAppAcceptanceLite.sh and scripts/finalAcceptanceCheck.sh
pytest tests/test_macos_app_acceptance_lite.py tests/test_workspace_shell.py tests/test_scripts.py -q: 31 passed
scripts/macosAppAcceptanceLite.sh --summary-json: status=Pass pass=29 fail=0 info=2 runtime=Stopped
No scripts/finalAcceptanceCheck.sh, scripts/ciSmoke.sh, full pytest, browser automation, market refresh, broker connection, order, payment, or holdings write was run in this step.
```

Safety boundary:

- This is read-only local app-entry verification plus launcher dry-run mode.
- Do not commit generated `MacOSAppAcceptanceLite_*.json` from this Mac if it contains local absolute paths unless the path data is intentionally sanitized first.

## 2026-06-16 macOS Lifecycle Readiness

Completed:

- Added `EVAOSMacOSLifecycleReadinessV1` and `scripts/macosLifecycleReadiness.sh` for read-only lifecycle readiness without triggering full smoke.
- Checks executable start/stop/status/cache/app-acceptance scripts, localhost Streamlit settings, launch lock, heartbeat shutdown monitor, sanitized UI heartbeat, scoped stop logic, cache cleanup guard, UI allowlist, cache dry-run summary, and app acceptance lite summary.
- Streamlit `macOS 生命周期` panel now exposes a `生命周期验收` button through the lifecycle allowlist.
- Docs now route lifecycle diagnosis to `scripts/macosLifecycleReadiness.sh --summary-json`; `scripts/finalAcceptanceCheck.sh` remains a deliberate release/full-acceptance gate.

Focused validation:

```text
py_compile passed for macOS lifecycle readiness module, CLI, system exports, dashboard, streamlit app, and new test
zsh -n passed for scripts/macosLifecycleReadiness.sh and scripts/finalAcceptanceCheck.sh
pytest tests/test_macos_lifecycle_readiness.py tests/test_macos_app_acceptance_lite.py tests/test_workspace_shell.py tests/test_scripts.py -q: 35 passed
post lazy-import regression pytest tests/test_macos_lifecycle_readiness.py tests/test_scripts.py -q: 26 passed
scripts/macosLifecycleReadiness.sh --summary-json after scoped cache guard: status=Pass pass=29 fail=0 info=0 runtime=Stopped cache_candidates=4 cache_kb=109.34 app_acceptance=Pass
scripts/cleanCache.sh --dry-run --json: no runpy warning after lazy-loading cache cleanup from lifecycle readiness
No scripts/finalAcceptanceCheck.sh, scripts/ciSmoke.sh, full pytest, browser automation, app start, service stop, cache delete, market refresh, broker connection, order, payment, or holdings write was run in this step.
```

Safety boundary:

- This is read-only local lifecycle inspection. It may run `statusQuantLab.sh`, build cache dry-run summary, and call App Lite Acceptance summary.
- It does not start services, stop services, delete caches, run `finalAcceptanceCheck.sh`, run `ciSmoke.sh`, run full pytest, open browsers, refresh market data, connect brokers, create orders, pay, or mutate holdings.
- Do not commit generated `MacOSLifecycleReadiness_*.json` from this Mac if it contains local absolute paths unless the path data is intentionally sanitized first.

## 2026-06-16 macOS Runtime Acceptance

Completed:

- Added `EVAOSMacOSRuntimeAcceptanceV1` and `scripts/macosRuntimeAcceptance.sh` for controlled real local start/health/cache-guard/stop acceptance.
- Default behavior fail-closes when an existing service is already healthy on 8501-8510, avoiding accidental stop of a user session.
- The script launches `scripts/startQuantLab.sh` in controlled background mode, waits for local `/_stcore/health`, verifies `cleanCache.sh --json` refuses while running, stops with `scripts/stopQuantLab.sh`, verifies health disappears, then verifies post-stop cache dry-run JSON.
- Streamlit `macOS 生命周期` panel lists `运行时验收` as a Terminal command only; it is intentionally not in the page allowlist.

Focused validation:

```text
py_compile passed for macOS runtime acceptance module, CLI, system exports, dashboard, and tests
zsh -n passed for scripts/cleanCache.sh, scripts/macosRuntimeAcceptance.sh, and scripts/finalAcceptanceCheck.sh
pytest tests/test_macos_runtime_acceptance.py tests/test_macos_lifecycle_readiness.py tests/test_workspace_shell.py tests/test_scripts.py -q: 36 passed
post timeout-handling regression pytest tests/test_macos_app_acceptance_lite.py tests/test_macos_runtime_acceptance.py tests/test_scripts.py -q: 30 passed
scripts/macosRuntimeAcceptance.sh --summary-json --start-timeout 120: status=Pass pass=10 fail=0 info=0 started_by_acceptance=True failed_checks=[]
post-run scripts/statusQuantLab.sh: QuantLab is not running on ports 8501-8510; no streamlit_app.py pgrep result
Fixed scripts/cleanCache.sh running-service detection from absolute-path pgrep to scoped port + process cwd detection so cache delete mode refuses a relative-path Streamlit launch from this checkout.
Fixed App Lite dry-run timeout handling so launcher timeout returns a structured Fail check instead of traceback.
```

Safety boundary:

- This is controlled local runtime acceptance. It really starts and stops the local Streamlit service that it started.
- It does not open a browser, run `finalAcceptanceCheck.sh`, run `ciSmoke.sh`, run full pytest, run browser automation, refresh market data, connect brokers, create orders, pay, or mutate holdings.
- Do not commit generated `MacOSRuntimeAcceptance_*.json` from this Mac if it contains local absolute paths unless the path data is intentionally sanitized first.

## 2026-06-16 ResearchBus Workspace Adapter

Completed:

- Added a compact manifest adapter for `finance_ledger`, `industry_research`, and `policy_intelligence`.
- Updated `system_orchestrator.default_child_systems()` so `ResearchBus` registers the canonical workspace system ids while keeping legacy child-system names.
- Extended interop audit and smoke coverage to check the canonical systems.

Current acceptance evidence should be refreshed with:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m pytest tests/test_workspace_systems.py tests/test_system_orchestrator.py tests/test_research_bus_audit.py -q
./scripts/syncWorkspaceSystemSummaries.sh --check --json
./scripts/orchestrateSystems.sh register --json
./scripts/ciSmoke.sh
```

Recommended next run: build the unified UI Shell status page from `system_state` and `system_registry`, using compact summaries instead of reading each subsystem's full source tree.

## 2026-06-16 Unified UI Shell Status MVP

Completed:

- Added `workspace_shell_summary()` as a pure helper for UI cards and canonical system rows.
- Rendered `统一 Workspace Shell` inside the existing Streamlit `system_status_panel()`.
- The page reads compact manifest summaries plus `ResearchBus` registry/state, not subsystem source trees.
- Added the `macOS 生命周期` panel to the same UI Shell block.
- Lifecycle actions now show app entry points, start/stop/status/cache-clean/final-acceptance commands, cache dry-run counts, and only allowlisted local status/stop/cache-clean scripts can run from the page.
- `scripts/cleanCache.sh --dry-run --json` now emits `EVACacheCleanupReportV1` counts and preserves reports, holdings, imports, SQLite databases, migrated source samples, and market bar caches.

Recommended next run: move to vectorized research mode or 52ETF depending on user priority.

## 2026-06-16 Vectorized Research Mode MVP

Completed:

- Added `src/quantlab/research/vectorized.py` to convert `EventReplay_latest.json` `BarClosed` records into stable OHLCV frames.
- Added deterministic `ma_crossover` parameter-scan adapter using the existing `ExperimentRunner`.
- Added `scripts/vectorizedResearch.sh` and `src/quantlab/examples/vectorized_research.py`.
- Added `docs/VectorizedResearchMode.md` and acceptance coverage.

Boundary:

- Reads local replay output only.
- Does not refresh market data, connect to Moomoo/brokers, create orders, or mutate holdings.
- Invalid strategy grids fail closed as `Blocked`.

Recommended next run: expose the vectorized summary in UI Shell charts or use it to optimize hotspot parameter scans.

## 2026-06-16 Vectorized Research UI/Chart Bridge

Completed:

- Added `vectorized_research_shell_summary()` for compact summary cards, top scan rows, and chart-ready rows.
- Added `render_vectorized_research_panel()` inside `工作台状态` / `统一 Workspace Shell`.
- The panel reads `data/vectorized/VectorizedResearch_latest.json` only; it does not reload `EventReplay` records or rerun parameter scans on page render.
- Added static acceptance gates and focused tests for the read-only UI bridge.

Boundary:

- Read-only display of existing vectorized output.
- No market refresh, broker calls, orders, holdings mutation, or background parameter scan execution.
- Browser visual verification is still limited by the local in-app Browser runtime failing to initialize kernel assets; HTTP health and code acceptance remain valid.

Recommended next run: use the chart-ready vectorized rows to optimize hotspot analysis runtime or start the 52ETF read-only integration.

## 2026-06-16 Hotspot Runtime Optimization MVP

Completed:

- Added `EVAOSHotspotRuntimeSummaryV1` in `src/quantlab/analysis/market_hotspots.py`.
- Added stable `hotspot_runtime_cache_key()` and compact `hotspot_runtime_summary()` for the slow `生成热点分析` button path.
- Moved hotspot evidence gate row construction into the analysis layer so UI, tests, and smoke scripts share one evidence contract.
- Streamlit `热点分析` now shows `热点运行摘要` with request key, object coverage, slice count, cache TTL, evidence status, and read-only safety boundary.
- Added Sample-only smoke entrypoint `scripts/hotspotRuntimeSummary.sh`; it does not open Streamlit, use network, connect brokers, create orders, or mutate holdings.
- Updated Handbook, Feature Specification, Acceptance Checklist, Release Notes, shell syntax checks, and final acceptance checks.

Boundary:

- This is a compact runtime summary and cache-key visibility layer, not a live market-data prefetch daemon.
- It preserves the 3600-second cache TTL and existing workbench object/snapshot limits.
- It does not connect to Moomoo/brokers, refresh real market data outside the existing button path, create orders, or modify holdings.

Recommended next run: either add a persisted local precompute store for hotspot results, or move to 52ETF read-only comparison / TradingView-like chart UX, depending on user priority.

## 2026-06-16 Hotspot Persisted Precompute Store

Completed:

- Added `EVAOSHotspotPersistedCacheV1` local derived cache under gitignored `data/cache/hotspots/`.
- Same hotspot request key now tries persisted cache before provider calls and writes computed hotspot rows back after a successful run.
- Runtime summary now marks `cache_source`, `cache_hit`, and persisted cache age, so the UI can distinguish computed results from cross-restart cache hits.
- `scripts/hotspotRuntimeSummary.sh --use-persisted-cache` validates the first run as `cache=computed` and the second run as `cache=persisted`.

Boundary:

- Cache TTL remains 3600 seconds.
- Cache stores derived hotspot rows, errors, compact summary metadata, and safety boundary only.
- Cache does not store raw provider frames, secrets, broker tokens, orders, or holdings mutations.
- `data/cache/hotspots/` is runtime-local and excluded from GitHub by `.gitignore`.

Recommended next run: continue with 52ETF read-only comparison / TradingView-like chart UX, or start the next productization pass for Token ROI, cashflow, policy, and consumption.

## 2026-06-16 52ETF Read-Only Hotspot Comparison

Completed:

- Added `EVAOS52ETFPublicSnapshotV1` in `src/quantlab/integrations/site52etf.py`.
- Added `scripts/site52etfSnapshot.sh` and `src/quantlab/examples/site52etf_snapshot.py` to write local `Site52ETFPublicSnapshot_latest.json`.
- Hotspot UI now prefers the local latest 52ETF snapshot before cached live fetch, reducing page wait and network dependency.
- The snapshot records public boards, metrics, visible operating notes, parsed 8-second refresh cadence, interaction hints, evidence gates, token policy, and safety boundary.
- Python `urllib` strict fetch falls back to system `/usr/bin/curl` on local certificate-chain failures; if curl also fails, the snapshot remains `Unavailable/NeedsReview`.
- Added `EVAOS52ETFHotspotComparisonV1` in `src/quantlab/integrations/site52etf.py`.
- The comparison maps 52ETF public A-share market-cloud boards to the current EVA_OS hotspot object pool.
- Hotspot UI now renders `52ETF 与 EVA 热点对照` after a selected hotspot slice when `显示 52ETF 公开参考` is enabled.
- The comparison shows market fit, board mapping, EVA hotspot slice counts, methodology differences, and safety boundary.
- Added focused tests for CN mapping, non-CN downgrade, UI term coverage, and final acceptance static gates.

Boundary:

- 52ETF remains a public read-only UI/reference source.
- It does not replace local/provider data quality gates.
- It is not written into backtests, orders, holdings, or pre-trade evidence.
- Snapshot artifacts under `data/integrations/site52etf/*.json` are runtime-local and gitignored; the repo keeps only `.gitkeep`.

Focused validation:

```text
web check of https://52etf.site/ showed public 大盘云图 / A股热力图 page with A股 board tabs and operating notes
py_compile passed for src/quantlab/integrations/site52etf.py, src/quantlab/examples/site52etf_snapshot.py, src/quantlab/app/streamlit_app.py, src/quantlab/integrations/__init__.py
zsh -n passed for scripts/site52etfSnapshot.sh and scripts/finalAcceptanceCheck.sh
pytest tests/test_site52etf.py tests/test_app_dashboard.py tests/test_scripts.py -q: 76 passed
scripts/site52etfSnapshot.sh --output-dir /tmp/eva_site52etf_snapshot_smoke --summary-json: EVAOS52ETFPublicSnapshotV1 status=Available artifact_status=Pass board_count=7 cadence=8 raw_html_stored=False
```

Recommended next run: continue unified UI shell/macOS acceptance, or add more hotspot cache controls if repeated large-object runs still feel slow.

## 2026-06-16 Research Chart UX Controls

Completed:

- Added shared Plotly chart helpers `research_chart_config()` and `apply_research_chart_ux()`.
- Applied the shared interaction layer to the vectorized research chart, hotspot timeline, hotspot heatmap, and hotspot bubble chart.
- Enabled scroll zoom, responsive rendering, drag pan or zoom, hover spike/crosshair behavior, and PNG export.
- Added timeline range slider and quick range selector buttons for recent slices, recent day window, and full history review.
- Updated acceptance gates, focused tests, Handbook, Feature Specification, Vectorized Research guide, and Release Notes.

Boundary:

- Chart interaction changes only the browser-side view of already generated compact results.
- It does not refetch market data, rerun parameter scans, trigger backtests, connect brokers, create orders, or mutate holdings.
- In-app Browser visual automation is still blocked by the local Browser runtime kernel-asset initialization failure; HTTP health and full acceptance were used as current UI reachability evidence.

Verified evidence:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -m py_compile src/quantlab/app/streamlit_app.py: passed
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -m pytest tests/test_app_dashboard.py tests/test_scripts.py -q: 64 passed
./scripts/finalAcceptanceCheck.sh: PASS 164, FAIL 0
full pytest inside final acceptance: 373 passed, 2 skipped, 3 subtests passed in 129.43s
curl -I http://localhost:8501: HTTP/1.1 200 OK
curl http://localhost:8501/_stcore/health: ok
./scripts/cleanCache.sh --json: removed 18 paths, 88 files, 1511.43 KB
```

Recommended next run: continue productizing Token ROI, cashflow, policy, and consumption, or add manual hotspot cache invalidation and cache metrics if the hotspot button remains slow on large object pools.

## 2026-06-16 Token ROI Runtime Summary

Completed:

- Added `EVATokenROIRuntimeSummaryV1` compact summary to the Token ROI value layer.
- `build_token_roi_ledger()` now includes a compact runtime summary without full `records`.
- `write_token_roi_ledger()` now writes `EVATokenROIRuntimeSummary_DDMMYYYY.json` and `EVATokenROIRuntimeSummary_latest.json` next to the full ledger artifacts.
- `scripts/tokenRoiLedger.sh --summary-json` prints only the low-token summary for agent handoff, smoke checks, and UI status.
- Streamlit `Token ROI` now shows `运行摘要与证据闸门` before the full table.
- Updated docs, acceptance gates, static checks, and tests.

Boundary:

- Full ledger records remain available in `EVATokenROILedger_*.json`.
- Runtime summary intentionally excludes full records and does not rescan artifacts beyond the ledger build.
- PendingReview financial hypotheses are counted for review but excluded from quantified financial totals.
- No fabricated revenue, cost saving, avoided loss, asset reuse value, or ROI; no trading, payments, orders, bank transfers, or real-money execution.

Verified evidence:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -m py_compile src/quantlab/value/token_roi.py src/quantlab/examples/token_roi_ledger.py src/quantlab/app/streamlit_app.py: passed
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -m pytest tests/test_token_roi_ledger.py tests/test_scripts.py tests/test_app_dashboard.py -q: 69 passed
./scripts/tokenRoiLedger.sh --summary-json: EVATokenROIRuntimeSummaryV1 status=NeedsReview record_count=182 records_in_summary=False
./scripts/tokenRoiLedger.sh --date 2026-06-16 --output-dir /tmp/eva_token_roi_smoke: wrote JSON/CSV/MD/PDF/latest/runtime summary
./scripts/finalAcceptanceCheck.sh: PASS 168, FAIL 0
full pytest inside final acceptance: 374 passed, 2 skipped, 3 subtests passed in 116.65s
./scripts/cleanCache.sh --json: removed 20 paths, 90 files, 1565.63 KB
```

Recommended next run: productize `Company CashFlow Command` with the same runtime-summary and evidence-gate pattern, then move to policy and consumption one subsystem at a time.

## 2026-06-16 Company CashFlow Runtime Summary

Completed:

- Added `EVAOSCompanyCashFlowRuntimeSummaryV1` compact summary to `Company CashFlow Command`.
- `build_cashflow_command()` now includes a compact runtime summary without full `entries`.
- `write_cashflow_command()` now writes `CompanyCashFlowRuntimeSummary_DDMMYYYY.json` and `CompanyCashFlowRuntimeSummary_latest.json`.
- `scripts/cashFlowCommand.sh --summary-json` prints only the low-token summary for agent handoff, smoke checks, and UI status.
- Streamlit `现金流` now shows `运行摘要与证据闸门` before the full ledger.
- `scripts/cashFlowCommand.sh` now supports `QUANTLAB_PYTHON -> .venv -> python3` fallback for local-slimming resilience.
- Updated docs, acceptance gates, static checks, and tests.

Boundary:

- Full cashflow entries remain available in `CompanyCashFlowCommand_*.json`.
- Runtime summary intentionally excludes full entries and does not connect external financial systems.
- Current real local state is `Blocked / MissingBalance` because no reviewed BalanceSnapshot evidence exists in the public-safe local ledger; this is the intended fail-closed state, not a code failure.
- No bank login, payment, transfer, payroll action, tax filing, accounting mutation, broker action, or real-money execution.

Verified evidence:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -m py_compile src/quantlab/business/cashflow.py src/quantlab/examples/cashflow_command.py src/quantlab/app/streamlit_app.py: passed
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -m pytest tests/test_cashflow_command.py tests/test_scripts.py tests/test_app_dashboard.py -q: 70 passed
./scripts/cashFlowCommand.sh --summary-json: EVAOSCompanyCashFlowRuntimeSummaryV1 status=Blocked cashflow_status=MissingBalance entry_count=0 entries_in_summary=False
./scripts/cashFlowCommand.sh --as-of 2026-06-16 --output-dir /tmp/eva_cashflow_smoke: wrote JSON/CSV/MD/PDF/latest/runtime summary
./scripts/finalAcceptanceCheck.sh: PASS 173, FAIL 0
full pytest inside final acceptance: 376 passed, 2 skipped, 3 subtests passed in 125.37s
./scripts/cleanCache.sh --json: removed 20 paths, 90 files, 1561.46 KB
```

Recommended next run: productize `Policy Intelligence Radar` with runtime summary and source/evidence gate, then productize `Consumption Guard`.

## 2026-06-16 Policy Intelligence Runtime Summary

Completed:

- Added `EVAOSPolicyIntelligenceRuntimeSummaryV1` compact summary to `Policy Intelligence Radar`.
- `build_policy_radar()` now includes a compact runtime summary without full `opportunities`.
- `write_policy_radar()` now writes `PolicyIntelligenceRuntimeSummary_DDMMYYYY.json` and `PolicyIntelligenceRuntimeSummary_latest.json`.
- `scripts/policyRadar.sh --summary-json` prints only the low-token summary for agent handoff, smoke checks, and UI status.
- Streamlit `政策雷达` now shows `运行摘要与证据闸门` before the full policy ledger.
- Updated docs, acceptance gates, static checks, and tests.

Boundary:

- Full policy opportunities remain available in `PolicyIntelligenceRadar_*.json`.
- Runtime summary intentionally excludes full opportunities and does not read live policy feeds.
- Current real local state is `Blocked / MissingPolicyEvidence` because no public-safe reviewed policy opportunity evidence exists in the local ledger; this is the intended fail-closed state, not a code failure.
- No government-portal login, application submission, payment, legal/tax/compliance/subsidy conclusion, investment conclusion, broker action, or real-money execution.

Verified evidence:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -m py_compile src/quantlab/policy/radar.py src/quantlab/examples/policy_radar.py src/quantlab/app/streamlit_app.py: passed
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -m pytest tests/test_policy_radar.py tests/test_scripts.py tests/test_app_dashboard.py -q: 71 passed
./scripts/policyRadar.sh --summary-json: EVAOSPolicyIntelligenceRuntimeSummaryV1 status=Blocked policy_status=MissingPolicyEvidence opportunity_count=0 opportunities_in_summary=False
./scripts/policyRadar.sh --as-of 2026-06-16 --output-dir /tmp/eva_policy_smoke: wrote JSON/CSV/MD/PDF/latest/runtime summary
./scripts/finalAcceptanceCheck.sh: PASS 177, FAIL 0
full pytest inside final acceptance: 378 passed, 2 skipped, 3 subtests passed in 116.09s
curl -I http://localhost:8501: HTTP/1.1 200 OK
curl http://localhost:8501/_stcore/health: ok
./scripts/cleanCache.sh --json: removed 20 paths, 90 files, 1562.31 KB
```

Recommended next run: productize `Consumption Guard` with the same runtime-summary and evidence-gate pattern, then refresh Executive Command Center aggregation if needed.

## 2026-06-16 Consumption Guard Runtime Summary

Completed:

- Added `EVAOSConsumptionGuardRuntimeSummaryV1` compact summary to `Consumption Guard`.
- `build_consumption_guard()` now includes a compact runtime summary without full `events`.
- `write_consumption_guard()` now writes `ConsumptionGuardRuntimeSummary_DDMMYYYY.json` and `ConsumptionGuardRuntimeSummary_latest.json`.
- `scripts/consumptionGuard.sh --summary-json` prints only the low-token summary for agent handoff, smoke checks, and UI status.
- Streamlit `消费守卫` now shows `运行摘要与证据闸门` before the full event ledger.
- Updated docs, acceptance gates, static checks, and tests.

Boundary:

- Full consumption events remain available in `ConsumptionGuard_*.json`.
- Runtime summary intentionally excludes full events and does not connect external financial or payment systems.
- Current real local state is `Blocked / MissingConsumptionEvidence` because no public-safe reviewed consumption evidence exists in the local ledger; this is the intended fail-closed state, not a code failure.
- No Alipay login, bank login, payroll/tax access, payment, transfer, refund, account freeze, broker action, or real-money execution.

Verified evidence:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -m py_compile src/quantlab/consumption/guard.py src/quantlab/examples/consumption_guard.py src/quantlab/app/streamlit_app.py: passed
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -m pytest tests/test_consumption_guard.py tests/test_scripts.py tests/test_app_dashboard.py -q: 72 passed
./scripts/consumptionGuard.sh --summary-json: EVAOSConsumptionGuardRuntimeSummaryV1 status=Blocked guard_status=MissingConsumptionEvidence event_count=0 events_in_summary=False
./scripts/consumptionGuard.sh --as-of 2026-06-16 --output-dir /tmp/eva_consumption_smoke --monthly-investable-budget 1000: wrote JSON/CSV/MD/PDF/latest/runtime summary
./scripts/finalAcceptanceCheck.sh: PASS 181, FAIL 0
full pytest inside final acceptance: 380 passed, 2 skipped, 3 subtests passed in 125.89s
curl -I http://localhost:8501: HTTP/1.1 200 OK
curl http://localhost:8501/_stcore/health: ok
./scripts/cleanCache.sh --json: removed 20 paths, 90 files, 1567.97 KB
```

Recommended next run: refresh Executive Command Center to prefer the compact runtime summaries for Token ROI, cashflow, policy, and consumption, then add real-input refresh workflows one subsystem at a time.

## 2026-06-16 Executive Command Center Runtime Summary Aggregation

Completed:

- Executive Command Center now prefers compact runtime summaries before full snapshots for Token ROI, cashflow, policy, and consumption.
- The command center payload now exposes `runtime_summary_sources` so agents can see whether each subsystem came from `runtime_summary` or `full_snapshot`.
- Scorecards, business summaries, action queue, evidence source schemas, and Markdown/PDF output now support the four runtime summary schemas.
- Backward-compatible fallback to full latest snapshots remains in place for older/local checkouts.
- Updated Command Center docs, acceptance checklist, release notes, static acceptance checks, and focused tests.

Boundary:

- No market refresh, OpenD connection, broker action, payment, bank action, or external account operation was added.
- Runtime summaries reduce token/context pressure only; they do not bypass subsystem evidence gates.
- Current repo data still falls back to `full_snapshot` unless the subsystem scripts write public-safe standalone runtime summaries into `data/*`.
- Runtime-first behavior was verified in an isolated temp `--project-root` with synthetic public-safe latest files.

Verified evidence:

```text
git diff --check: passed
py_compile: passed for src/quantlab/executive/command_center.py and src/quantlab/examples/command_center.py
target pytest: tests/test_command_center.py tests/test_scripts.py tests/test_app_dashboard.py -> 74 passed
default command center smoke: status=NeedsReview, PDF ok, current repo data runtime modes fell back to full_snapshot
runtime-first temp project smoke: modes=['runtime_summary','runtime_summary','runtime_summary','runtime_summary'] and schemas matched all four runtime summary schemas
./scripts/finalAcceptanceCheck.sh: PASS 186, FAIL 0
full pytest inside final acceptance: 382 passed, 2 skipped, 3 subtests passed in 103.38s
curl -I http://localhost:8501: HTTP/1.1 200 OK
curl http://localhost:8501/_stcore/health: ok
./scripts/cleanCache.sh --json: removed 19 paths, 89 files, 1074.3 KB
```

Recommended next run: generate or refresh public-safe runtime summary latest artifacts for the four subsystems under `data/*`, then start real-input refresh workflows one subsystem at a time.

## 2026-06-16 Runtime Summary Latest Artifact Refresh

Completed:

- Added `scripts/refreshRuntimeSummaries.sh` and `src/quantlab/executive/runtime_summary_refresh.py`.
- The refresh command writes only compact runtime summary JSON files for Token ROI, Company CashFlow, Policy Intelligence, and Consumption Guard.
- Added `EVAOSRuntimeSummaryRefreshV1` aggregate CLI output for low-token handoff verification.
- Generated public-safe latest artifacts:
  - `data/value/EVATokenROIRuntimeSummary_latest.json`
  - `data/cashflow/CompanyCashFlowRuntimeSummary_latest.json`
  - `data/policy/PolicyIntelligenceRuntimeSummary_latest.json`
  - `data/consumption/ConsumptionGuardRuntimeSummary_latest.json`
- Generated matching dated artifacts for `16062026`.
- Runtime summary `outputs` use repo-relative paths and do not include full records, entries, opportunities, events, private imports, holdings, credentials, or local absolute project paths.
- Command Center default real-repo smoke now reads all four value/business sources in `runtime_summary` mode.
- Updated docs, release notes, final acceptance gates, zsh syntax coverage, and focused tests.

Boundary:

- No market refresh, OpenD connection, broker action, payment, bank action, government portal login, Alipay login, tax/payroll action, or external account operation was added.
- The generated cashflow, policy, and consumption summaries remain `Blocked` because public-safe reviewed evidence is absent; this is intended fail-closed behavior.
- Token ROI remains `NeedsReview` because value records exist but quantified financial evidence is not fully reviewed.

Verified evidence:

```text
./scripts/refreshRuntimeSummaries.sh --as-of 2026-06-16 --monthly-investable-budget 1000: status=Pass summaries=4
runtime summary file safety check: no full records/entries/opportunities/events keys and no local absolute project path
command center real-repo smoke: runtime_modes=['runtime_summary','runtime_summary','runtime_summary','runtime_summary']; PDF magic=%PDF-1.4
py_compile: passed for runtime_summary_refresh.py, refresh_runtime_summaries.py, and executive/__init__.py
zsh -n scripts/refreshRuntimeSummaries.sh: passed
focused pytest: tests/test_runtime_summary_refresh.py tests/test_command_center.py tests/test_scripts.py -> 28 passed
./scripts/finalAcceptanceCheck.sh: PASS 201, FAIL 0
full pytest inside final acceptance: 384 passed, 2 skipped, 3 subtests passed in 194.97s
curl -I http://127.0.0.1:8501: HTTP/1.1 200 OK
curl http://127.0.0.1:8501/_stcore/health: ok
./scripts/statusQuantLab.sh after stop: not running on ports 8501-8510
./scripts/cleanCache.sh --json: removed 19 paths, 90 files, 1033.76 KB
```

Recommended next run: build real-input refresh workflows one subsystem at a time, starting with the subsystem with the highest immediate ROI and lowest private-data risk.

## 2026-06-16 Company CashFlow Reviewed Input Refresh MVP

Completed:

- Added `scripts/cashFlowReviewedInputRefresh.sh` and `src/quantlab/business/cashflow_reviewed_input.py`.
- Added `EVAOSCompanyCashFlowReviewedInputRefreshV1` so agents can verify reviewed-input refresh without reading full cashflow entries.
- Default real input path is `data/private/cashflow/CompanyCashFlowReviewedInput.json`, which is excluded from GitHub by `.gitignore`.
- Added public-safe template `data/cashflow/CompanyCashFlowReviewedInput.example.json`.
- Added schema `shared/schema/company_cashflow_reviewed_input.schema.json`.
- Extended `scripts/refreshRuntimeSummaries.sh` with `--cashflow-entry-path` so the aggregate low-token refresh can reuse the same reviewed input.
- Missing private input is fail-closed: returns `Blocked / MissingReviewedInput` and does not write output files.
- With reviewed input, the workflow writes full Company CashFlow JSON/CSV/Markdown/PDF/latest and compact runtime summary latest.

Boundary:

- Public GitHub contains only schema and synthetic sample input.
- Real cashflow evidence, raw balances, private account labels, receipts, invoices, and internal review notes stay under `data/private/cashflow` or another user-provided local private path.
- No bank login, payment provider login, payroll/tax access, accounting-system mutation, broker action, transfer, payment, or real-money execution.

Verified evidence:

```text
py_compile: passed for cashflow_reviewed_input.py, cashflow_reviewed_input_refresh.py, runtime_summary_refresh.py, refresh_runtime_summaries.py, and business/__init__.py
zsh syntax: cashFlowReviewedInputRefresh.sh and refreshRuntimeSummaries.sh passed
focused pytest: tests/test_cashflow_reviewed_input_refresh.py tests/test_cashflow_command.py tests/test_runtime_summary_refresh.py tests/test_scripts.py -> 31 passed
missing private input smoke: EVAOSCompanyCashFlowReviewedInputRefreshV1 status=Blocked cashflow_status=MissingReviewedInput input_status=Missing outputs={}
public example smoke: status=Pass cashflow_status=Stable balance=18000.0 net=3840.0 runway_days=1500.0
runtime summary refresh with --cashflow-entry-path: Company CashFlow runtime_status=Pass
command center temp smoke: cashflow_summary Stable, latest_balance=18000.0, net_cashflow=3840.0, runway_days=1500.0, runtime source=runtime_summary, PDF ok
git diff --check: passed
./scripts/finalAcceptanceCheck.sh: PASS 212, FAIL 0
full pytest inside final acceptance: 388 passed, 2 skipped, 3 subtests passed in 244.62s
curl -I http://127.0.0.1:8501: HTTP/1.1 200 OK
curl http://127.0.0.1:8501/_stcore/health: ok
./scripts/statusQuantLab.sh after stop: not running on ports 8501-8510
./scripts/cleanCache.sh --json: removed 20 paths, 93 files, 1045.33 KB
```

Recommended next run: continue with Token ROI reviewed value evidence or Consumption Guard reviewed-input verification, depending on current user priority.

## 2026-06-16 Consumption Guard Reviewed Input Refresh MVP

Completed:

- Added `scripts/consumptionReviewedInputRefresh.sh` and `src/quantlab/consumption/reviewed_input.py`.
- Added `EVAOSConsumptionGuardReviewedInputRefreshV1` so agents can verify reviewed-input refresh without reading full consumption events.
- Default real input path is `data/private/consumption/ConsumptionGuardReviewedInput.json`, which is excluded from GitHub by `.gitignore`.
- Added public-safe template `data/consumption/ConsumptionGuardReviewedInput.example.json`.
- Added schema `shared/schema/consumption_guard_reviewed_input.schema.json`.
- Extended `scripts/refreshRuntimeSummaries.sh` with `--consumption-event-path` so the aggregate low-token refresh can reuse the same reviewed input.
- Missing private input is fail-closed: returns `Blocked / MissingReviewedInput` and does not write output files.
- With reviewed input, the workflow writes full Consumption Guard JSON/CSV/Markdown/PDF/latest and compact runtime summary latest.

Boundary:

- Public GitHub contains only schema and synthetic sample input.
- Real bills, receipts, screenshots, Alipay/bank exports, merchant details, internal review notes, and private cashflow assumptions stay under `data/private/consumption` or another user-provided local private path.
- No Alipay login, bank login, payroll/tax access, payment-system login, payment, transfer, refund, account freeze, broker action, or real-money execution.

Verified evidence:

```text
py_compile: passed for consumption/reviewed_input.py, consumption_reviewed_input_refresh.py, runtime_summary_refresh.py, refresh_runtime_summaries.py, and consumption/__init__.py
zsh syntax: consumptionReviewedInputRefresh.sh and refreshRuntimeSummaries.sh passed
focused pytest: tests/test_consumption_reviewed_input_refresh.py tests/test_consumption_guard.py tests/test_runtime_summary_refresh.py tests/test_scripts.py -> 31 passed
missing private input smoke: EVAOSConsumptionGuardReviewedInputRefreshV1 status=Blocked guard_status=MissingReviewedInput input_status=Missing outputs={}
public example smoke: status=NeedsReview guard_status=Watch events=3 counted=3 impulse_spend=420.0
runtime summary refresh with --consumption-event-path: Consumption Guard runtime_status=NeedsReview
command center temp smoke: consumption summary Watch, counted_records=3, impulse_spend=420.0, runtime source=runtime_summary, PDF ok
git diff --check: passed
heavy smoke note: full final acceptance and ciSmoke are intentionally not run by default after user request to avoid repeated SmokeTest Fail noise
```

## Latest Verified Engineering Step

Latest verified engineering step:

```text
macOS App Runtime Acceptance hardening without heavy smoke
```

Verified evidence from the implementation run:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -m pytest tests/test_macos_runtime_acceptance.py tests/test_macos_app_acceptance_lite.py tests/test_macos_acceptance_hub.py tests/test_scripts.py -q -p no:cacheprovider -> 42 passed
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -c "import ast, pathlib; [ast.parse(pathlib.Path(p).read_text(encoding='utf-8'), filename=p) for p in ['src/quantlab/system/macos_runtime_acceptance.py']]; print('ast syntax ok')" -> ast syntax ok
Desktop EVA_OS.app runtime acceptance -> status=Pass pass=10 fail=0 launch_method=app app_lite=Pass post_healthy_ports=[]
Downloads EVA_OS.app runtime acceptance -> status=Pass pass=10 fail=0 launch_method=app app_lite=Pass post_healthy_ports=[]
Applications EVA_OS.app runtime acceptance -> status=Pass pass=10 fail=0 launch_method=app app_lite=Pass post_healthy_ports=[]
git diff --check -> passed
./scripts/devReadyCheck.sh --summary-json -> EVAOSDevReadyCheckV1 status=Pass pass=40 fail=0 info=1
./scripts/cleanCache.sh --dry-run --json -> candidate_count=0 candidate_file_count=0 candidate_dir_count=0 candidate_kb=0.0
./scripts/macosAcceptance.sh --summary-json -> EVAOSMacOSAcceptanceHubV1 status=Pass mode=daily pass=2 fail=0 info=0 starts_service=false opens_browser=false heavy_smoke=false
heavy smoke: not run by default; user explicitly asked to stop repeated SmokeTest Fail triggers
```

Important environment note:

```text
The old local .venv was deleted during slimming. The five report scripts used in this run now fall back to QUANTLAB_PYTHON or system python3 when .venv is absent. For full-suite work, recreate .venv or provide a complete QUANTLAB_PYTHON runtime.
```

Suggested setup:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[test,app,data]'
PYTHONPATH=src .venv/bin/python -m pytest tests/test_event_replay.py tests/test_data_lake_manifest.py tests/test_market_event_layer.py tests/test_scripts.py -q -p no:cacheprovider
```

## Current macOS Entry Points

Installed local entry apps:

```text
~/Desktop/EVA_OS.app
~/Downloads/EVA_OS.app
/Applications/EVA_OS.app
```

Portable template in repo:

```text
macos/EVA_OS.app
```

Reinstall command:

```bash
./scripts/installEVAOSEntryApps.sh
```

The app uses a native Mach-O launcher built from `macos/EVA_OS_launcher.c`, reads `Contents/Resources/EVA_OS_PROJECT_ROOT`, opens local `StartQuantLab.command`, and does not fall back to GitHub if no local project is found.

## Current Unresolved Work

High-priority remaining items:

1. Decide how Token ROI should accept reviewed value evidence without committing private financial assumptions.
2. Add any remaining private-data import helpers around Consumption Guard only after the reviewed-input contract is stable.
3. `Discrete Event Simulation Mode`: deterministic event-loop simulation over replay batches.
4. `Agent Market Simulation Mode`: ABIDES/StockSim-style research simulation boundary, no real orders.
5. TradingView-like chart and strategy UX beyond the current shared Plotly controls.
6. Moomoo-like realtime research adapter, read-only quote/research flow.
7. Merge workbench flows and UI status panels to reduce token/context pressure during daily operation.

## Current Known Issues

- Local `.venv` now exists for this checkout and passed final acceptance. It is ignored and must not be committed; recreate with `scripts/startQuantLab.sh` or `scripts/verifyQuantLab.sh` if removed.
- Public GitHub intentionally excludes private holdings/imports and runtime SQLite state; restore those only from local private sources if needed.
- `DataLakeManifest_latest.json` currently indexes the MVP event log only; broader bar cache/tick/news/policy assets are future work.
- Event replay currently supports local `market_events` JSONL only.
- Full regression was not completed after Event Replay; only focused validation and interrupted full-suite progress are known.

## Recommended Next Run Contract

Target:

```text
Unified UI shell / macOS acceptance pass
```

Minimal scope:

- keep the current one-subsystem-at-a-time cadence;
- choose the next macOS UI acceptance gap now that 52ETF has a local snapshot artifact;
- preserve compact runtime summary reads to reduce token/context pressure;
- keep private holdings/imports/raw evidence excluded from GitHub;
- preserve fail-closed evidence gates and no external execution.

Stop condition:

- The selected next subsystem has source, CLI/script, focused tests, docs, handoff updates, and GitHub push without running heavy smoke unless explicitly requested.

## Public Upload Boundary

Include in GitHub:

- source code, tests, scripts, docs, task pack, public-safe handoff files, public-safe deterministic sample data, and macOS launcher template.

Exclude from GitHub:

- `.venv`, caches, `.env`, secrets, `data/holdings/**`, `data/imports/**`, `data/researchBus/*.sqlite*`, private screenshots, local logs, pid files, and locks.

Also exclude from child-system migrations:

- finance ledger raw bills, ledger SQLite, transaction-detail HTML, and private review queues;
- industry research private holdings, Alipay confirmations, moomoo local databases, cookies, API keys, and real account data;
- policy intelligence `~/.policy-intelligence`, Chrome profile state, cookies, platform auth, API keys, raw HTML dumps, and local logs.

## 2026-06-15 Systems Workspace Baseline

This run began the pursuing-goal implementation path toward macOS acceptance and maximum user ROI.

Added baseline files:

- `systems/README.md`
- `systems/finance_ledger/SYSTEM_MANIFEST.json`
- `systems/industry_research/SYSTEM_MANIFEST.json`
- `systems/policy_intelligence/SYSTEM_MANIFEST.json`
- `shared/security/system_permissions.json`
- `shared/schema/system_manifest.schema.json`
- `shared/schema/research_event.schema.json`
- `.github/workflows/smoke.yml`
- `scripts/ciSmoke.sh`
- `docs/SystemsMigrationPlan.md`

Security behavior:

- cross-system permissions are fail-closed by default;
- undeclared scopes are denied;
- `execute=true` requires an `approval_id` plus the existing local execution environment gates;
- finance ledger cannot write policy state;
- industry research cannot write ledger state.

## 2026-06-15 Finance Ledger Source Migration

The `finance_ledger` child system has moved from manifest-only registration to source migration.

Added public-safe system files:

- `systems/finance_ledger/README.md`
- `systems/finance_ledger/source/`
- `systems/finance_ledger/samples/README.md`
- `systems/finance_ledger/samples/sanitized_alipay.csv`
- `systems/finance_ledger/samples/sanitized_wechat.csv`

Included:

- source code under `source/src/econ_bleed_analyzer`;
- launcher source under `source/src/native`;
- scripts, tests, docs, configs, AGENTS/HANDOFF/README, setup and Makefile;
- public-safe icon assets;
- synthetic sample bills.

Excluded:

- `data/`, `outputs/`, `work/`, `build/`, cache directories, `.sqlite`, `.db`, raw bills, generated HTML/PDF/ZIP outputs, transaction-detail dumps, private review queues, and local runtime logs.

Validation evidence:

```text
PYTHONPATH=<temp pytest deps> ./scripts/ciSmoke.sh
EVA_OS smoke: 37 passed, 2 skipped, 3 warnings
finance_ledger smoke: 10 passed
JSON validation: systems/finance_ledger/SYSTEM_MANIFEST.json ok
sensitive file scan: no sqlite/db/env/cookie/Login Data/zip/html/pdf under systems/finance_ledger
sensitive keyword scan: no raw transaction/secrets patterns under systems/finance_ledger
```

Next run should migrate `policy_intelligence` source/tests/docs/config examples only, then create the cross-system adapters in a separate run.

## 2026-06-15 Industry Research Source Migration

The `industry_research` child system has moved from manifest-only registration to source migration.

Added public-safe system files:

- `systems/industry_research/README.md`
- `systems/industry_research/source/`
- `systems/industry_research/source/data/sample/README.md`

Included:

- source code under `source/src`;
- tests under `source/tests`;
- docs, config, prompts, templates, scripts, AGENTS/HANDOFF/README, doctor/setup/Makefile;
- sanitized or public-safe sample data under `source/data/sample`;
- sanitized OpenD sample status with no local traceback or account path.

Excluded:

- `source/data/private`, `source/data/report_artifacts`, `source/02_reports`, report PDFs/Word/Excel outputs, real Alipay exports, screenshots/videos, real holdings, moomoo local databases, cookies, API keys, broker tokens, and runtime logs.

Migration hardening:

- policy bridge default root now uses `AI_RESEARCH_POLICY_ROOT` or the future `systems/policy_intelligence/source`;
- ResearchBus default SQLite path now points to the EVA_OS repo data boundary or `QUANTLAB_RESEARCH_BUS_DB`;
- moomoo workbench default now uses `MOOMOO_WORKBENCH_ROOT` or local private data;
- workflow test paths are portable when run from the EVA_OS root;
- Data Trust report-name date parsing now handles names such as `1. 05062026_盘前报告` without falling back to today's date.

Validation evidence:

```text
PYTHONPATH=<temp pytest deps> ./scripts/ciSmoke.sh
EVA_OS smoke: 37 passed, 2 skipped, 3 warnings
finance_ledger smoke: 10 passed
industry_research smoke: 15 passed

PYTHONPATH=systems/industry_research/source python3 -m pytest systems/industry_research/source/tests -q -p no:cacheprovider
industry_research full tests: 198 passed, 9 subtests passed
```

Next run should migrate `policy_intelligence` source/tests/docs/config examples only, with no auth/cookie/API-key/Chrome profile/runtime database state.

## 2026-06-16 Policy Intelligence Source Migration

The `policy_intelligence` child system has moved from manifest-only registration to source migration.

Added public-safe system files:

- `systems/policy_intelligence/README.md`
- `systems/policy_intelligence/source/`
- `systems/policy_intelligence/source/data/sample/README.md`
- `systems/policy_intelligence/source/data/sample/source_registry_sample.json`
- `systems/policy_intelligence/source/data/sample/policy_queue_sample.json`

Included:

- source code under `source/src/source_registry`;
- tests under `source/tests`;
- docs, config, rules, scripts, README/HANDOFF, and `pyproject.toml`;
- synthetic or structurally anonymized sample fixtures under `source/data/sample`.

Excluded:

- `source/data/*.sqlite`, `source/data/automation`, `source/data/monitor`, `source/data/run_logs`, `source/data/snapshots`, `source/reports`, app bundles, Chrome profiles, cookies, platform auth files, API keys, raw HTML dumps, local logs, and generated report archives.

Migration hardening:

- policy tests now include `tests/conftest.py` so the full suite can be run from the EVA_OS repo root while preserving the source package's expected working directory;
- quality gate rule loading now falls back to the migrated source root when a relative `rules/quality_gates.json` path is used from the monorepo root;
- root `scripts/ciSmoke.sh` compiles policy source, checks report runner shell syntax, runs focused tests, and checks CLI help.

Validation evidence:

```text
PYTHONPATH=<temp pytest deps>:systems/policy_intelligence/source/src python3 -m pytest systems/policy_intelligence/source/tests -q
policy_intelligence full tests: 244 passed, 5 warnings

PYTHONPATH=<temp pytest deps> ./scripts/ciSmoke.sh
EVA_OS smoke: 37 passed, 2 skipped, 3 warnings
finance_ledger smoke: 10 passed
industry_research smoke: 15 passed
policy_intelligence smoke: 31 passed

post-test cache cleanup: 45 cache dirs removed, about 6432 KB
sensitive file scan: no sqlite/db/env/zip/pdf/docx/xlsx/cookie/pyc under systems/policy_intelligence
```

Next run should create the first cross-system ResearchBus adapters for finance, industry, and policy summaries before starting the unified UI Shell.

## Local Private Continuity

This run preserved the old long-form local handoff as:

```text
HANDOFF_PRIVATE_LOCAL.md
```

It is ignored by git and must not be uploaded to the public repository.

## 2026-06-16 macOS App Runtime Acceptance Stabilization

Current status:

- Desktop, Downloads, and Applications `EVA_OS.app` entries are installed and point to this local checkout.
- Native launcher no longer routes to GitHub or Terminal; it invokes local `StartQuantLab.command` through `/bin/zsh -f`.
- Runtime acceptance app mode first tries macOS `open -n`; if LaunchServices produces no health/log signal, it falls back to the same app bundle executable at `Contents/MacOS/EVA_OS`.
- `stopQuantLab.sh` now also clears project-scoped `StartQuantLab.command` launcher processes and the launch lock.
- Do not run `scripts/finalAcceptanceCheck.sh`, `scripts/ciSmoke.sh`, full pytest, or pre-push hooks by default; use targeted checks unless a release gate explicitly asks for heavy smoke.

Validation evidence:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -m pytest tests/test_macos_runtime_acceptance.py tests/test_macos_app_acceptance_lite.py tests/test_workspace_shell.py tests/test_scripts.py -q
38 passed

zsh -n StartQuantLab.command && zsh -n scripts/stopQuantLab.sh && bash -n scripts/installEVAOSEntryApps.sh && zsh -n scripts/macosRuntimeAcceptance.sh && zsh -n scripts/finalAcceptanceCheck.sh
passed

./scripts/macosAppAcceptanceLite.sh --summary-json
status=Pass pass=29 fail=0 info=2

./scripts/macosRuntimeAcceptance.sh --launch-method app --app-path "$HOME/Downloads/EVA_OS.app" --summary-json
status=Pass pass=10 fail=0 post_healthy_ports=[]

git diff --check
passed
```

Next run:

- Continue unified UI Shell and productized subsystem work.
- Keep runtime acceptance targeted; reserve full smoke/final acceptance for explicit release gates.

## 2026-06-16 Hotspot Cache Control And Low-Token Runtime

Current status:

- Hotspot analysis now exposes `EVAOSHotspotCacheStatusV1` for the current request fingerprint.
- The Streamlit hotspot page shows current request cache state, age, remaining TTL, and hotspot cache directory size/count before the user clicks generate.
- The page has a `清除当前热点缓存` button that deletes only the current request-key derived cache under `data/cache/hotspots/`; it does not delete market bar cache, reports, holdings, SQLite files, or other subsystem caches.
- `scripts/hotspotRuntimeSummary.sh` supports `--cache-status` and `--invalidate-cache` for CLI-only diagnosis without opening Streamlit or reading market bars.

Validation evidence:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -m pytest tests/test_market_hotspots.py tests/test_scripts.py -q
39 passed

zsh -n scripts/hotspotRuntimeSummary.sh && zsh -n scripts/finalAcceptanceCheck.sh
passed

./scripts/hotspotRuntimeSummary.sh --cache-status --json-only --market US --interval 60min --limit 5
returned EVAOSHotspotCacheStatusV1 without market-bar loading

./scripts/hotspotRuntimeSummary.sh --use-persisted-cache --json-only --market US --interval 60min --limit 5
./scripts/hotspotRuntimeSummary.sh --cache-status --json-only --market US --interval 60min --limit 5
./scripts/hotspotRuntimeSummary.sh --invalidate-cache --json-only --market US --interval 60min --limit 5
computed summary -> cache hit -> Deleted 381228 bytes

git diff --check
passed
sensitive diff scan
no hits
```

Next run:

- Continue unified UI Shell and dynamic visualization work.
- If hotspot generation still feels slow on real providers, add provider-level request timing and per-symbol progress/error summaries before changing data-provider behavior.

## 2026-06-16 Hotspot Per-Symbol Timing Trace

Current status:

- Hotspot generation now emits `EVAOSHotspotRequestTraceV1` compact per-object diagnostics.
- The trace records symbol, name, market, provider symbol, status, elapsed milliseconds, returned row count, fallback note, and compact error text.
- The Streamlit hotspot page renders `数据请求耗时` after generation, showing request count, success/failure, total elapsed time, slowest request, and the slowest per-symbol rows.
- Persisted hotspot cache now preserves the compact trace so repeated cached views can still show which provider/symbol was slow during the original run.
- `scripts/hotspotRuntimeSummary.sh --json-only` includes `request_trace`; non-JSON output prints `elapsed_ms=`.

Validation evidence:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -m pytest tests/test_market_hotspots.py tests/test_scripts.py -q
41 passed

zsh -n scripts/hotspotRuntimeSummary.sh && zsh -n scripts/finalAcceptanceCheck.sh
passed

./scripts/hotspotRuntimeSummary.sh --use-persisted-cache --json-only --market US --interval 60min --limit 5
returned EVAOSHotspotRuntimeSummaryV1 with EVAOSHotspotRequestTraceV1 request_count=5 success_count=5 failed_count=0

repeat cached CLI run
cache_source=persisted and request_trace.request_count=5

./scripts/hotspotRuntimeSummary.sh --invalidate-cache --json-only --market US --interval 60min --limit 5
Deleted 384423 bytes

git diff --check
passed
sensitive diff scan
no hits
```

Next run:

- Continue with unified UI Shell and provider timing surfacing in broader workspace status.
- If real providers are still slow, add provider-level aggregate timing across requests before changing provider code.

## 2026-06-16 Development Ready Check Without Heavy Smoke

Current status:

- Added `EVAOSDevReadyCheckV1` and `scripts/devReadyCheck.sh --summary-json` as the default low-noise development gate.
- The new gate checks required executable scripts, selected zsh syntax, selected Python syntax via AST parse, `statusQuantLab.sh`, cache cleanup dry-run, and git status.
- Dirty worktree is recorded as `Info`, not a failure, so agents can run it during active development without manufacturing a failed acceptance state.
- The shell entry does not invoke final acceptance, CI smoke, full pytest, browser automation, market refresh, broker/order flows, or strategy smoke gates.
- `scripts/cleanCache.sh` now sets `PYTHONDONTWRITEBYTECODE=1` and `PYTHONPYCACHEPREFIX=/private/tmp/quantlab-pycache` so dry-run/delete checks do not create new repo-local `__pycache__` noise.
- README, Testing, Acceptance Checklist, final acceptance static coverage, and tests now document this split.

Validation evidence:

```text
./scripts/devReadyCheck.sh --summary-json
EVAOSDevReadyCheckV1 status=Pass pass=26 fail=0 info=1

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -m pytest tests/test_dev_readiness.py tests/test_scripts.py -q -p no:cacheprovider
26 passed

zsh -n scripts/devReadyCheck.sh && zsh -n scripts/finalAcceptanceCheck.sh
passed

./scripts/cleanCache.sh --json
removed 49 paths, 262 files, 48 directories, 3269.6 KB across this run

./scripts/cleanCache.sh --dry-run --json
candidate_count=0 candidate_file_count=0 candidate_dir_count=0
```

Next run:

- Use `scripts/devReadyCheck.sh --summary-json` as the first default verifier.
- Do not run `scripts/finalAcceptanceCheck.sh`, `scripts/ciSmoke.sh`, full pytest, or hooks unless the user explicitly asks for a release gate.
- Continue unified UI Shell and macOS real acceptance work from the lightweight gate.

## 2026-06-16 Dev Ready Check In UI Shell

Current status:

- Unified Workspace `macOS 生命周期` panel now includes a `开发检查` button wired to allowlisted `scripts/devReadyCheck.sh`.
- `macos_lifecycle_summary` now exposes `Dev Ready Check` as a UI-mode action before app/start/stop/release gates.
- Final acceptance static checks now cover the dev-ready UI button and dashboard action, but final acceptance remains a manual release gate.
- QuickStart, Docs Index, and MacOSLifecycleReadiness docs now list Dev Ready as the first daily development check.

Validation evidence:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -m pytest tests/test_workspace_shell.py tests/test_scripts.py tests/test_dev_readiness.py tests/test_macos_lifecycle_readiness.py -q -p no:cacheprovider
35 passed

./scripts/devReadyCheck.sh --summary-json
EVAOSDevReadyCheckV1 status=Pass pass=26 fail=0 info=1

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -m quantlab.examples.macos_lifecycle_readiness --summary-json --skip-app-acceptance
EVAOSMacOSLifecycleReadinessV1 status=Pass pass=29 fail=0

zsh -n scripts/devReadyCheck.sh && zsh -n scripts/cleanCache.sh && zsh -n scripts/macosLifecycleReadiness.sh && zsh -n scripts/finalAcceptanceCheck.sh
passed
```

Next run:

- Continue toward macOS real acceptance by adding a compact runtime evidence card to the UI Shell, still without running heavy smoke by default.

## 2026-06-16 Runtime Acceptance Evidence Card

Current status:

- Unified Workspace `macOS 生命周期` panel now renders `运行时验收证据`.
- The card reads only `data/systemAudit/MacOSRuntimeAcceptance_latest.json`.
- It shows runtime status, pass/total checks, latest run age, launch method, and failed check rows.
- If the latest JSON is missing, the UI fails closed as `Missing` and shows the Terminal commands.
- The UI still does not run `scripts/macosRuntimeAcceptance.sh`; runtime acceptance remains Terminal-only and outside the Streamlit allowlist.

Validation evidence:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -m pytest tests/test_workspace_shell.py tests/test_scripts.py tests/test_macos_runtime_acceptance.py tests/test_dev_readiness.py -q -p no:cacheprovider
39 passed

./scripts/devReadyCheck.sh --summary-json
EVAOSDevReadyCheckV1 status=Pass pass=26 fail=0 info=1

zsh -n scripts/devReadyCheck.sh && zsh -n scripts/cleanCache.sh && zsh -n scripts/macosRuntimeAcceptance.sh && zsh -n scripts/finalAcceptanceCheck.sh
passed
```

Next run:

- Generate a real `MacOSRuntimeAcceptance_latest.json` from Terminal only when ready for macOS runtime evidence refresh.
- Continue toward actual `.app` open-path acceptance and visual UI verification.

## 2026-06-16 Real Script Runtime Acceptance Evidence

Current status:

- Ran Terminal-only script-mode runtime acceptance on this Mac.
- Result: `EVAOSMacOSRuntimeAcceptanceV1 status=Pass pass=10 fail=0 info=0`.
- It started the local Streamlit service, observed health, verified `cleanCache.sh` refuses delete mode while running, stopped the service, confirmed no post-stop healthy ports, and ran post-stop cache dry-run.
- App Lite precheck inside runtime acceptance passed: `pass=29 fail=0 info=2`.
- Local evidence files were written:
  - `data/systemAudit/MacOSRuntimeAcceptance_16062026.json`
  - `data/systemAudit/MacOSRuntimeAcceptance_latest.json`
- The raw evidence contains this machine's absolute project root, so `.gitignore` now excludes `data/systemAudit/MacOSRuntimeAcceptance*.json`; do not upload those local evidence JSON files to GitHub.
- UI summary confirmed the same evidence as `MacOSRuntimeEvidenceSummaryV1 status=Pass cards=['Pass','10/10','Today','script']` with no `/Users/` path leak.

Validation evidence:

```text
./scripts/macosRuntimeAcceptance.sh --output-dir data/systemAudit --summary-json
EVAOSMacOSRuntimeAcceptanceV1 status=Pass pass=10 fail=0 info=0 started_by_acceptance=true launch_method=script

UI evidence summary
MacOSRuntimeEvidenceSummaryV1 Pass ['Pass', '10/10', 'Today', 'script'] rows=0 path_leak=False

./scripts/statusQuantLab.sh
QuantLab is not running on ports 8501-8510.
```

Next run:

- Run app open-path runtime acceptance when ready: `scripts/macosRuntimeAcceptance.sh --launch-method app --app-path ~/Downloads/EVA_OS.app --output-dir data/systemAudit --summary-json`.
- Keep runtime evidence files local unless they are sanitized.

## 2026-06-16 Real App Open-Path Runtime Acceptance Evidence

Current status:

- Ran real Downloads app open-path runtime acceptance on this Mac:
  `./scripts/macosRuntimeAcceptance.sh --launch-method app --app-path "$HOME/Downloads/EVA_OS.app" --output-dir data/systemAudit --summary-json`
- Result: `EVAOSMacOSRuntimeAcceptanceV1 status=Pass pass=10 fail=0 info=0`.
- `launch_method=app`, `started_by_acceptance=true`, `pre_existing_healthy_ports=[]`, `post_healthy_ports=[]`.
- All core checks passed:
  - `LiteAcceptancePasses`
  - `NoPreExistingService`
  - `AppOpenLaunched`
  - `HealthAfterStart`
  - `StatusSeesRunning`
  - `CleanCacheRefusesWhileRunning`
  - `StopScriptRuns`
  - `HealthAfterStop`
  - `StatusSeesStopped`
  - `CleanCacheDryRunAfterStop`
- UI evidence summary reads latest as `MacOSRuntimeEvidenceSummaryV1 Pass ['Pass', '10/10', 'Today', 'app']`, with no `/Users/` path leak.
- Raw local evidence still contains the absolute project root and remains gitignored:
  `data/systemAudit/MacOSRuntimeAcceptance*.json`.

Validation evidence:

```text
./scripts/macosRuntimeAcceptance.sh --launch-method app --app-path "$HOME/Downloads/EVA_OS.app" --output-dir data/systemAudit --summary-json
EVAOSMacOSRuntimeAcceptanceV1 status=Pass pass=10 fail=0 info=0 launch_method=app

UI evidence summary
MacOSRuntimeEvidenceSummaryV1 Pass ['Pass', '10/10', 'Today', 'app'] rows=0 path_leak=False

./scripts/statusQuantLab.sh
QuantLab is not running on ports 8501-8510.
```

Next run:

- Move to visual/browser acceptance of the running UI or generate a sanitized public runtime acceptance summary if GitHub-visible evidence is needed.

## 2026-06-17 macOS UI Visual Acceptance

Current status:

- Added lightweight browser evidence entrypoint `scripts/uiVisualAcceptance.sh`.
- The script starts the local workbench only if no healthy service is already present, verifies rendered UI through headless Chrome, captures a screenshot, writes local evidence, and then stops only the service it started.
- The accepted UI evidence schema is `EVAOSUIVisualAcceptanceV1`.
- Final local evidence passed with `status=Pass pass=16 fail=0`, `browser=/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`, and `screenshot_bytes=278744`.
- The current script scrolls to the `macOS 生命周期` area before checking lifecycle action buttons, avoiding false failures from Streamlit offscreen rendering.
- Evidence files are local-only and gitignored:
  - `data/systemAudit/UIVisualAcceptance_*.json`
  - `data/systemAudit/UIVisualAcceptance_latest.json`
  - `data/systemAudit/UIVisualAcceptance_*.png`
  - `data/systemAudit/UIVisualAcceptance_streamlit_*.log`

Validation evidence:

```text
./scripts/uiVisualAcceptance.sh --summary-json
EVAOSUIVisualAcceptanceV1 status=Pass pass=16 fail=0 started_by_acceptance=true screenshot_bytes=278744

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -m pytest tests/test_scripts.py tests/test_dev_readiness.py -q -p no:cacheprovider
28 passed

./scripts/devReadyCheck.sh --summary-json
EVAOSDevReadyCheckV1 status=Pass pass=28 fail=0 info=1 cache_candidate_count=0

git diff --check
passed

./scripts/cleanCache.sh --json
removed 23 cache paths, 113 files, 23 dirs, 1591.58 KB

./scripts/statusQuantLab.sh
QuantLab is not running on ports 8501-8510.
```

Next run:

- Continue toward macOS product acceptance by either generating a sanitized public visual-evidence summary or wiring UI visual acceptance into the documented release checklist; keep heavy SmokeTest gates explicit-only.

## 2026-06-17 GitHub-Safe macOS Public Acceptance Summary

Current status:

- Added `scripts/macosPublicAcceptanceSummary.sh`.
- Added sanitizer module `src/quantlab/system/macos_public_acceptance.py`.
- Added CLI `src/quantlab/examples/macos_public_acceptance.py`.
- Added guide `docs/MacOSPublicAcceptanceSummary.md`.
- Generated public evidence under `docs/evidence/`.
- Current public summary status is `Pass`, with runtime source `Pass 10/0`, UI source `Pass 16/0`, and 11 coverage gates passing.

Public artifacts:

- `docs/evidence/MacOSAcceptancePublicSummary_20260617.json`
- `docs/evidence/MacOSAcceptancePublicSummary_latest.json`
- `docs/evidence/MacOSAcceptancePublicSummary_latest.md`

Validation evidence:

```text
./scripts/macosPublicAcceptanceSummary.sh --summary-json
EVAOSMacOSPublicAcceptanceSummaryV1 status=Pass sources_pass=2/2 runtime=Pass ui=Pass

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -m pytest tests/test_macos_public_acceptance.py tests/test_scripts.py tests/test_dev_readiness.py -q -p no:cacheprovider
32 passed

./scripts/devReadyCheck.sh --summary-json
EVAOSDevReadyCheckV1 status=Pass pass=32 fail=0 info=1

rg leak scan against docs/evidence
no matches for local paths, browser executables, screenshot paths, logs, process ids, app open paths, or file URLs
```

Boundary:

- The public summary only stores schema, status, counts, gate names, and sanitized pass/fail evidence.
- Raw local runtime/UI evidence and screenshots remain gitignored under `data/systemAudit/`.

Next run:

- Build the final macOS delivery checklist/package around the three evidence layers: app-open runtime evidence, UI visual evidence, and public sanitized summary.

## 2026-06-17 macOS Acceptance Hub Consolidation

Current status:

- Added unified entrypoint `scripts/macosAcceptance.sh`.
- Added hub schema `EVAOSMacOSAcceptanceHubV1`.
- Added `src/quantlab/system/macos_acceptance_hub.py` and `src/quantlab/examples/macos_acceptance_hub.py`.
- Default no-arg mode is `daily`, which runs:
  - `scripts/devReadyCheck.sh --summary-json`
  - `scripts/macosPublicAcceptanceSummary.sh --summary-json`
- Advanced modes remain explicit:
  - `app-entry`
  - `lifecycle`
  - `runtime`
  - `app-runtime`
  - `ui`
  - `public-summary`
- Streamlit `macOS 生命周期` panel now has one primary `日常验收` button; older component checks remain under `高级单项验收`.

Validation evidence:

```text
./scripts/macosAcceptance.sh
EVAOSMacOSAcceptanceHubV1 status=Pass mode=daily pass=2 fail=0

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -m pytest tests/test_macos_acceptance_hub.py tests/test_scripts.py tests/test_dev_readiness.py tests/test_workspace_shell.py -q -p no:cacheprovider
41 passed

zsh -n scripts/macosAcceptance.sh && zsh -n scripts/devReadyCheck.sh && zsh -n scripts/finalAcceptanceCheck.sh
passed
```

Next run:

- Continue reducing UI/documentation clutter by applying the same "default hub + advanced component" pattern to hotspot/parameter-scan actions, one subsystem at a time.

## 2026-06-17 Report Validation Hub Consolidation

Current status:

- Added unified entrypoint `scripts/reportValidation.sh`.
- Added hub schema `EVAOSReportValidationHubV1`.
- Added `src/quantlab/system/report_validation_hub.py` and `src/quantlab/examples/report_validation_hub.py`.
- Default no-arg mode is `daily`, equivalent to `--mode daily --summary-json`.
- Default mode is read-only and compact:
  - report decision support counts;
  - report evidence gap candidate counts;
  - validation priority counts and a small top-task preview.
- Default mode does not write report outputs, append validation queue tasks, execute validation, refresh market data, connect brokers, create orders, or mutate holdings.
- Streamlit Report Center now shows one primary `报告验证工作台`; queue writes, priority-plan writes, validation execution, and report-index file writes are under explicit `高级动作`.

Validation evidence:

```text
./scripts/reportValidation.sh
EVAOSReportValidationHubV1 status=Pass mode=daily report_records=32 needs_more=32 gap_tasks=170 prioritized=120

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -m pytest tests/test_report_validation_hub.py tests/test_scripts.py tests/test_dev_readiness.py -q -p no:cacheprovider
34 passed

./scripts/devReadyCheck.sh --summary-json
EVAOSDevReadyCheckV1 status=Pass pass=40 fail=0 info=1

./scripts/cleanCache.sh --dry-run --json
candidate_count=0 candidate_file_count=0 candidate_dir_count=0 candidate_kb=0.0
```

Next run:

- Apply the same product pattern to hotspot/parameter-scan actions: one default quick path, explicit advanced modes, compact runtime summary first, and no accidental heavy smoke.

## 2026-06-17 Hotspot Quick Preflight

Current status:

- Added `EVAOSHotspotQuickPreflightV1` in the Streamlit hotspot workflow.
- `hotspot_quick_preflight()` classifies the selected hotspot request before generation:
  - `NeedsInput` when no object is selected;
  - `CacheHit` when current request can reuse persisted derived cache;
  - `LargeRun` for full replay or high cell-count requests;
  - `Ready` for normal quick preview.
- `render_hotspot_preflight()` displays recommendation, selected/active object count, max snapshots, expected provider requests, and cache state before the user clicks `生成热点分析`.
- Existing cache cleanup controls moved under `高级缓存与清理`, reducing default page noise.

Validation target:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -m pytest tests/test_app_dashboard.py tests/test_scripts.py tests/test_market_hotspots.py -q -p no:cacheprovider
```

Boundary:

- Preflight reads only UI selection, workbench profile, and cache metadata.
- It does not load market bars, generate hotspot history, refresh market data, connect brokers, create orders, pay, or mutate holdings.

## 2026-06-17 Parameter Scan Preflight

Current status:

- Added `EVAOSParameterScanPreflightV1` in the Streamlit parameter scan workflow.
- `parameter_scan_preflight()` classifies the selected scan before market data or backtests run:
  - `Ready` for normal scans;
  - `LargeRun` for scans close to the configured upper bound;
  - `TooMany` when combinations exceed `最大组合数`;
  - `InvalidGrid` for parse/cleaning errors;
  - `Blocked` when the selected symbol is invalid.
- `render_parameter_scan_preflight()` displays status, combination count, max-run usage, parameter count, strategy type, and next action.

Validation evidence:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -m pytest tests/test_app_dashboard.py tests/test_scripts.py -q -p no:cacheprovider -> 80 passed
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -c "import ast, pathlib; [ast.parse(pathlib.Path(p).read_text(encoding='utf-8'), filename=p) for p in ['src/quantlab/app/streamlit_app.py']]; print('ast syntax ok')" -> ast syntax ok
git diff --check -> passed
./scripts/devReadyCheck.sh --summary-json -> EVAOSDevReadyCheckV1 status=Pass pass=40 fail=0 info=1
./scripts/cleanCache.sh --dry-run --json -> candidate_count=0 candidate_file_count=0 candidate_dir_count=0 candidate_kb=0.0
post-push ./scripts/macosAcceptance.sh --summary-json -> EVAOSMacOSAcceptanceHubV1 status=Pass mode=daily pass=2 fail=0 info=0 starts_service=false opens_browser=false heavy_smoke=false
```

Boundary:

- Preflight parses only grid and selection metadata.
- It does not load market bars, run backtests, generate reports, connect brokers, create orders, pay, or mutate holdings.

## 2026-06-17 Command Center Action Router

Current status:

- Added `EVAOSCommandCenterActionRouterV1` to the command center dashboard.
- `command_center_next_actions()` converts the compact command-center payload into a small next-action route table.
- `render_command_center_action_router()` shows the recommended entry, P0/P1 counts, route count, and direct `?view=` links for hotspot preflight, parameter scan preflight, report validation, and macOS daily acceptance.

Validation evidence:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -m pytest tests/test_app_dashboard.py tests/test_scripts.py -q -p no:cacheprovider -> 81 passed
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -c "import ast, pathlib; [ast.parse(pathlib.Path(p).read_text(encoding='utf-8'), filename=p) for p in ['src/quantlab/app/dashboard.py', 'src/quantlab/app/streamlit_app.py']]; print('ast syntax ok')" -> ast syntax ok
git diff --check -> passed
./scripts/devReadyCheck.sh --summary-json -> EVAOSDevReadyCheckV1 status=Pass pass=40 fail=0 info=1
./scripts/cleanCache.sh --dry-run --json -> candidate_count=0 candidate_file_count=0 candidate_dir_count=0 candidate_kb=0.0
```

Boundary:

- Router reads only the compact command-center payload and static route metadata.
- It does not scan reports, load market data, run backtests, execute macOS scripts, clear cache, connect brokers, create orders, pay, or mutate holdings.

## 2026-06-17 macOS App Runtime Acceptance Hardening

Current status:

- Hardened `EVAOSMacOSRuntimeAcceptanceV1` support-script timeouts so `statusQuantLab.sh` and `cleanCache.sh --dry-run --json` do not false-fail during real `.app` open acceptance on a busy Mac.
- `macOS Runtime Acceptance` now retries transient App Lite precheck failures once, uses a longer dry-run window, and carries compact failed-check details in `app_acceptance`.
- Final-code real app-open acceptance passed for all installed entries: Desktop, Downloads, and Applications.

Validation evidence:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -m pytest tests/test_macos_runtime_acceptance.py tests/test_macos_app_acceptance_lite.py tests/test_macos_acceptance_hub.py tests/test_scripts.py -q -p no:cacheprovider -> 42 passed
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -c "import ast, pathlib; [ast.parse(pathlib.Path(p).read_text(encoding='utf-8'), filename=p) for p in ['src/quantlab/system/macos_runtime_acceptance.py']]; print('ast syntax ok')" -> ast syntax ok
./scripts/macosRuntimeAcceptance.sh --launch-method app --app-path "$HOME/Desktop/EVA_OS.app" --summary-json -> status=Pass pass=10 fail=0 post_healthy_ports=[]
./scripts/macosRuntimeAcceptance.sh --launch-method app --app-path "$HOME/Downloads/EVA_OS.app" --summary-json -> status=Pass pass=10 fail=0 post_healthy_ports=[]
./scripts/macosRuntimeAcceptance.sh --launch-method app --app-path "/Applications/EVA_OS.app" --summary-json -> status=Pass pass=10 fail=0 post_healthy_ports=[]
```

Boundary:

- This run did not execute `scripts/finalAcceptanceCheck.sh`, `scripts/ciSmoke.sh`, full pytest, market refresh, broker calls, orders, payments, or holdings writes.
- Raw local runtime evidence under `data/systemAudit/MacOSRuntimeAcceptance*` remains local-only and must not be uploaded to GitHub.
