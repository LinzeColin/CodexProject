# PFI_OS Agent Continuity

Last updated: 2026-06-17

This repository is the handoff surface for continuing PFI_OS / PFI_OS development without replaying the full Codex thread. Treat the files in this repo as the current engineering source of truth, then verify with local commands before making changes.

## Current Operating Name

- Product name: `PFI_OS`
- Historical / repo name: `PFI_OS`
- Quant subsystem name retained in code: `PFIOS`

## Current Local Source

The latest prepared workspace at the time of upload was:

```text
$PFI_OS_HOME
```

The workspace was copied from the historical implementation path:

```text
$PFI_OS_HOME
```

The upload intentionally excludes virtual environments, caches, private holdings/imports, raw video frames, local logs, SQLite runtime state, and secrets. See `UPLOAD_MANIFEST.md`.

`data/researchBus/ResearchBusSnapshot.json` is runtime state and must stay local/private. The public repository keeps only `data/researchBus/ResearchBusSnapshot.example.json`.

## Local App Entry Points

Installed local launchers:

```text
~/Desktop/PFI_OS.app
~/Downloads/PFI_OS.app
/Applications/PFI_OS.app
```

Repository template and installer:

```text
macos/PFI_OS.app
scripts/installPFIOSEntryApps.sh
```

## Start Here

Read these first, in order:

1. `README.md`
2. `HANDOFF.md`
3. `docs/PFI_OS.md`
4. `docs/Index.md`
5. `docs/MacOSAppAcceptanceLite.md`
6. `docs/MacOSLifecycleReadiness.md`
7. `docs/MacOSRuntimeAcceptance.md`
8. `15_OPEN_QUESTIONS.md`
9. `UPLOAD_MANIFEST.md`
10. `docs/SystemsMigrationPlan.md`
11. `docs/ThreadHandshakeManifest.md`
12. `systems/README.md`
13. `shared/security/system_permissions.json`
14. `systems/finance_ledger/README.md`
15. `systems/industry_research/README.md`
16. `systems/policy_intelligence/README.md`

## Completed Foundation

The system already has these productized layers or MVPs:

| Layer | Current artifact |
| --- | --- |
| Market Event Layer | `src/pfi_os/data/market_events.py`, `scripts/marketEventLayer.sh`, `docs/MarketEventLayer.md` |
| Reproducible Data Lake | `src/pfi_os/data/lake.py`, `scripts/dataLakeManifest.sh`, `docs/ReproducibleDataLake.md` |
| Event Replay MVP | `src/pfi_os/data/replay.py`, `scripts/eventReplay.sh`, `docs/EventReplay.md` |
| macOS PFI_OS entry apps | `macos/PFI_OS.app`, `macos/PFI_OS_launcher.c`, `scripts/installPFIOSEntryApps.sh` |
| macOS App Acceptance Lite | `PFIOSMacOSAppAcceptanceLiteV1`, `scripts/macosAppAcceptanceLite.sh`, `docs/MacOSAppAcceptanceLite.md` |
| macOS Lifecycle Readiness | `PFIOSMacOSLifecycleReadinessV1`, `scripts/macosLifecycleReadiness.sh`, `docs/MacOSLifecycleReadiness.md` |
| macOS Runtime Acceptance | `PFIOSMacOSRuntimeAcceptanceV1`, `scripts/macosRuntimeAcceptance.sh`, `docs/MacOSRuntimeAcceptance.md` |
| macOS Acceptance Hub | `PFIOSMacOSAcceptanceHubV1`, `scripts/macosAcceptance.sh`, `docs/MacOSAcceptanceHub.md` |
| Report Validation Hub | `PFIOSReportValidationHubV1`, `scripts/reportValidation.sh`, `docs/ReportValidationHub.md` |
| Company CashFlow Command | `PFIOSCompanyCashFlowRuntimeSummaryV1`, `PFIOSCompanyCashFlowReviewedInputRefreshV1`, `docs/CompanyCashFlowCommand.md`, public-safe runtime summaries and reviewed-input example in `data/cashflow` |
| Policy Intelligence Radar | `PFIOSPolicyIntelligenceRuntimeSummaryV1`, `PFIOSPolicyReviewedInputRefreshV1`, `docs/PolicyIntelligenceRadar.md`, public-safe reviewed-input example in `data/policy` |
| Consumption Guard | `PFIOSConsumptionGuardRuntimeSummaryV1`, `PFIOSConsumptionGuardReviewedInputRefreshV1`, `docs/ConsumptionGuard.md`, public-safe reviewed-input example in `data/consumption` |
| Executive Command Center | `runtime_summary_sources`, `src/pfi_os/executive/command_center.py`, `scripts/commandCenter.sh`, `docs/ExecutiveCommandCenter.md` |
| Runtime Summary Refresh | `PFIOSRuntimeSummaryRefreshV1`, `scripts/refreshRuntimeSummaries.sh`, `src/pfi_os/executive/runtime_summary_refresh.py` |
| CashFlow reviewed input refresh | `scripts/cashFlowReviewedInputRefresh.sh`, `data/private/cashflow/CompanyCashFlowReviewedInput.json`, `shared/schema/company_cashflow_reviewed_input.schema.json` |
| Policy reviewed input refresh | `scripts/policyReviewedInputRefresh.sh`, `data/private/policy/PolicyReviewedInput.json`, `shared/schema/policy_reviewed_input.schema.json` |
| Consumption reviewed input refresh | `scripts/consumptionReviewedInputRefresh.sh`, `data/private/consumption/ConsumptionGuardReviewedInput.json`, `shared/schema/consumption_guard_reviewed_input.schema.json` |
| Workspace system manifest adapter | `src/pfi_os/integrations/workspace_systems.py`, `scripts/syncWorkspaceSystemSummaries.sh` |
| Unified UI Shell status | `src/pfi_os/app/dashboard.py`, `src/pfi_os/app/streamlit_app.py`, `tests/test_workspace_shell.py` |
| macOS runtime acceptance | `scripts/pfiRuntime.sh`, `scripts/startPFIOS.sh`, `StartPFIOS.command`, `scripts/finalAcceptanceCheck.sh` |
| UI Shell lifecycle panel | `macos_lifecycle_summary()`, `render_macos_lifecycle_panel()` |
| Vectorized Research Mode | `src/pfi_os/research/vectorized.py`, `scripts/vectorizedResearch.sh`, `docs/VectorizedResearchMode.md` |
| Hotspot Runtime Summary | `hotspot_runtime_summary()`, `scripts/hotspotRuntimeSummary.sh`, `PFIOSHotspotRuntimeSummaryV1` |
| Hotspot Quick Preflight | `hotspot_quick_preflight()`, `render_hotspot_preflight()`, `PFIOSHotspotQuickPreflightV1` |
| Hotspot Persisted Cache | `PFIOSHotspotPersistedCacheV1`, `data/cache/hotspots/`, `--use-persisted-cache` |
| Parameter Scan Preflight | `parameter_scan_preflight()`, `render_parameter_scan_preflight()`, `PFIOSParameterScanPreflightV1` |
| Command Center Action Router | `command_center_next_actions()`, `render_command_center_action_router()`, `PFIOSCommandCenterActionRouterV1` |
| 52ETF Read-Only Reference | `PFIOS52ETFPublicSnapshotV1`, `PFIOS52ETFHotspotComparisonV1`, `scripts/site52etfSnapshot.sh`, `render_site52etf_hotspot_comparison()` |
| Research Chart UX Controls | `apply_research_chart_ux()`, `research_chart_config()`, hotspot/vectorized Plotly charts |

## Current Architecture Direction

PFI_OS is moving toward:

1. event-driven market layer,
2. reproducible data lake,
3. deterministic event replay,
4. three-mode backtest/simulation core,
5. TradingView-like chart and strategy UX,
6. Moomoo-like realtime research workflow,
7. fail-closed evidence, risk, and approval gates.

The reference concepts are LEAN, vectorbt, Kafka, Arrow, QuestDB, ClickHouse, ABIDES, and StockSim. These are architecture references, not mandatory dependencies.

## Validation Discipline

- Default to focused validation for iterative subsystem work: `scripts/macosAppAcceptanceLite.sh --summary-json`, `scripts/macosLifecycleReadiness.sh --summary-json`, `scripts/macosRuntimeAcceptance.sh --summary-json` when real local start/stop is intended, targeted pytest files, `git diff --check`, sensitive scans, app dry-run checks, and explicit local health checks.
- Do not run heavy smoke suites such as `scripts/finalAcceptanceCheck.sh` or `scripts/ciSmoke.sh` by default. Run them only when the user asks for full smoke, when preparing a formal release, or when a change touches cross-system acceptance gates and the user accepts the cost/noise.
- Heavy SmokeTest scripts are guarded locally and require `PFI_OS_ALLOW_HEAVY_SMOKE=1`; this is intentional to prevent accidental repeated SmokeTest Fail noise.
- GitHub smoke is retained for pull requests and manual `workflow_dispatch`, but is not attached to every `main` push.
- If a heavy acceptance script was started and the user asks not to trigger SmokeTest Fail, stop the script and record the last completed evidence instead of rerunning it.

## Latest Verified Run

Latest verified engineering step: `macOS App Runtime Acceptance hardening without heavy smoke`.

Validated evidence from the 2026-06-17 macOS app runtime acceptance hardening run:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -m pytest tests/test_macos_runtime_acceptance.py tests/test_macos_app_acceptance_lite.py tests/test_macos_acceptance_hub.py tests/test_scripts.py -q -p no:cacheprovider: 42 passed
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -c "import ast, pathlib; [ast.parse(pathlib.Path(p).read_text(encoding='utf-8'), filename=p) for p in ['src/pfi_os/system/macos_runtime_acceptance.py']]; print('ast syntax ok')": ast syntax ok
Desktop PFI_OS.app runtime acceptance: status=Pass pass=10 fail=0 launch_method=app app_lite=Pass post_healthy_ports=[]
Downloads PFI_OS.app runtime acceptance: status=Pass pass=10 fail=0 launch_method=app app_lite=Pass post_healthy_ports=[]
Applications PFI_OS.app runtime acceptance: status=Pass pass=10 fail=0 launch_method=app app_lite=Pass post_healthy_ports=[]
git diff --check: passed
./scripts/devReadyCheck.sh --summary-json returned status=Pass pass=40 fail=0 info=1
./scripts/cleanCache.sh --dry-run --json returned candidate_count=0 candidate_file_count=0 candidate_dir_count=0 candidate_kb=0.0
./scripts/macosAcceptance.sh --summary-json returned PFIOSMacOSAcceptanceHubV1 status=Pass mode=daily pass=2 fail=0 info=0 starts_service=false opens_browser=false heavy_smoke=false
No scripts/finalAcceptanceCheck.sh, scripts/ciSmoke.sh, full pytest, browser automation, browser-open action, market refresh, broker connection, order, payment, or holdings write was run in this step
```

Earlier verified engineering step: `Command Center Action Router without heavy smoke`.

Validated evidence from the 2026-06-17 command center action router run:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -m pytest tests/test_app_dashboard.py tests/test_scripts.py -q -p no:cacheprovider: 81 passed
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -c "import ast, pathlib; [ast.parse(pathlib.Path(p).read_text(encoding='utf-8'), filename=p) for p in ['src/pfi_os/app/dashboard.py', 'src/pfi_os/app/streamlit_app.py']]; print('ast syntax ok')": ast syntax ok
git diff --check: passed
./scripts/devReadyCheck.sh --summary-json returned status=Pass pass=40 fail=0 info=1
./scripts/cleanCache.sh --dry-run --json returned candidate_count=0 candidate_file_count=0 candidate_dir_count=0 candidate_kb=0.0
Post-push ./scripts/macosAcceptance.sh --summary-json returned PFIOSMacOSAcceptanceHubV1 status=Pass mode=daily pass=2 fail=0 info=0; starts_service=false opens_browser=false heavy_smoke=false
No scripts/finalAcceptanceCheck.sh, scripts/ciSmoke.sh, full pytest, browser automation, browser-open action, market refresh, broker connection, order, payment, or holdings write was run in this step
```

Earlier verified engineering step: `Parameter Scan Preflight without heavy smoke`.

Validated evidence from the 2026-06-17 parameter scan preflight run:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -m pytest tests/test_app_dashboard.py tests/test_scripts.py -q -p no:cacheprovider: 80 passed
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -c "import ast, pathlib; [ast.parse(pathlib.Path(p).read_text(encoding='utf-8'), filename=p) for p in ['src/pfi_os/app/streamlit_app.py']]; print('ast syntax ok')": ast syntax ok
git diff --check: passed
./scripts/devReadyCheck.sh --summary-json returned status=Pass pass=40 fail=0 info=1
./scripts/cleanCache.sh --dry-run --json returned candidate_count=0 candidate_file_count=0 candidate_dir_count=0 candidate_kb=0.0
No scripts/finalAcceptanceCheck.sh, scripts/ciSmoke.sh, full pytest, browser automation, browser-open action, market refresh, broker connection, order, payment, or holdings write was run in this step
```

Earlier verified engineering step: `Report Validation Hub consolidation without heavy smoke`.

Validated evidence from the 2026-06-17 report validation hub run:

```text
./scripts/reportValidation.sh returned PFIOSReportValidationHubV1 status=Pass mode=daily report_records=32 needs_more=32 gap_tasks=170 validation_queue_candidates=7058 prioritized=120
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -m pytest tests/test_report_validation_hub.py tests/test_scripts.py tests/test_dev_readiness.py -q -p no:cacheprovider: 34 passed
./scripts/devReadyCheck.sh --summary-json returned status=Pass pass=40 fail=0 info=1
./scripts/cleanCache.sh --dry-run --json returned candidate_count=0 candidate_file_count=0 candidate_dir_count=0 candidate_kb=0.0
No scripts/finalAcceptanceCheck.sh, scripts/ciSmoke.sh, full pytest, browser automation, browser-open action, market refresh, broker connection, order, payment, or holdings write was run in this step
```

Earlier verified engineering step: `macOS Acceptance Hub consolidation without full smoke`.

Validated evidence from the 2026-06-17 macOS acceptance hub run:

```text
./scripts/macosAcceptance.sh returned PFIOSMacOSAcceptanceHubV1 status=Pass mode=daily pass=2 fail=0
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -m pytest tests/test_macos_acceptance_hub.py tests/test_scripts.py tests/test_dev_readiness.py tests/test_workspace_shell.py -q -p no:cacheprovider: 41 passed
zsh -n scripts/macosAcceptance.sh && zsh -n scripts/devReadyCheck.sh && zsh -n scripts/finalAcceptanceCheck.sh: passed
```

Earlier verified engineering step: `macOS Runtime Acceptance without full smoke`.

Validated evidence from the 2026-06-16 runtime acceptance run:

```text
py_compile passed for macOS runtime acceptance module, CLI, system exports, dashboard, and tests
zsh -n passed for scripts/cleanCache.sh, scripts/macosRuntimeAcceptance.sh, and scripts/finalAcceptanceCheck.sh
tests/test_macos_runtime_acceptance.py tests/test_macos_lifecycle_readiness.py tests/test_workspace_shell.py tests/test_scripts.py: 36 passed
post timeout-handling regression tests/test_macos_app_acceptance_lite.py tests/test_macos_runtime_acceptance.py tests/test_scripts.py: 30 passed
scripts/macosRuntimeAcceptance.sh --summary-json --start-timeout 120 returned status=Pass pass=10 fail=0 info=0 started_by_acceptance=True failed_checks=[]
post-run scripts/statusPFIOS.sh returned PFIOS is not running on ports 8501-8510 and pgrep found no streamlit_app.py process
scripts/cleanCache.sh now uses scoped port + process cwd detection so cache delete mode refuses a relative-path Streamlit launch from this checkout
App Lite dry-run timeout handling now returns a structured Fail check instead of traceback
No scripts/finalAcceptanceCheck.sh, scripts/ciSmoke.sh, full pytest, browser automation, browser-open action, market refresh, broker connection, order, payment, or holdings write was run in this step
```

Earlier macOS Lifecycle Readiness evidence:

```text
py_compile passed for macOS lifecycle readiness module, CLI, system exports, dashboard, streamlit app, and new test
zsh -n passed for scripts/macosLifecycleReadiness.sh and scripts/finalAcceptanceCheck.sh
tests/test_macos_lifecycle_readiness.py tests/test_macos_app_acceptance_lite.py tests/test_workspace_shell.py tests/test_scripts.py: 35 passed
post lazy-import regression tests/test_macos_lifecycle_readiness.py tests/test_scripts.py: 26 passed
scripts/macosLifecycleReadiness.sh --summary-json after scoped cache guard returned status=Pass pass=29 fail=0 info=0 runtime=Stopped cache_candidates=4 cache_kb=109.34 app_acceptance=Pass
scripts/cleanCache.sh --dry-run --json produced no runpy warning after lazy-loading cache cleanup from lifecycle readiness
No scripts/finalAcceptanceCheck.sh, scripts/ciSmoke.sh, full pytest, browser automation, app start, service stop, cache delete, market refresh, broker connection, order, payment, or holdings write was run in this step
```

Earlier macOS App Acceptance Lite evidence:

```text
py_compile passed for macOS acceptance module, CLI, system exports, dashboard, streamlit app, and new test
zsh -n passed for scripts/macosAppAcceptanceLite.sh and scripts/finalAcceptanceCheck.sh
tests/test_macos_app_acceptance_lite.py tests/test_workspace_shell.py tests/test_scripts.py: 31 passed
scripts/macosAppAcceptanceLite.sh --summary-json returned status=Pass pass=29 fail=0 info=2 runtime=Stopped
No scripts/finalAcceptanceCheck.sh, scripts/ciSmoke.sh, full pytest, browser automation, market refresh, broker connection, order, payment, or holdings write was run in this step
```

Earlier macOS runtime hardening evidence:

```text
Desktop, Downloads, and Applications PFI_OS.app refreshed from repo template
codesign --verify --deep passed for all three installed app bundles
scripts/startPFIOS.sh started Streamlit at http://localhost:8501
/_stcore/health returned ok
scripts/statusPFIOS.sh detected the running service
scripts/finalAcceptanceCheck.sh completed with PASS: 131, FAIL: 0
full pytest inside final acceptance: 352 passed, 2 skipped, 3 subtests passed in 128.00s
non-network daily check passed; readiness remains NeedsReview because data/provider evidence gates still require review/config
```

Latest lifecycle/cache bridge evidence:

```text
scripts/finalAcceptanceCheck.sh completed with PASS: 138, FAIL: 0
full pytest inside final acceptance: 357 passed, 2 skipped, 3 subtests passed in 66.23s
scripts/cleanCache.sh --dry-run --json reported 26 candidate paths, 182 files, 2929.39 KB
scripts/cleanCache.sh --json removed 26 paths, 182 files, 2929.57 KB
```

Latest vectorized research evidence:

```text
scripts/vectorizedResearch.sh --symbol SPY --market US --interval 1d --param short_window=2,3 --param long_window=4,5 returned status=Pass rows=7 runs=4/4
scripts/finalAcceptanceCheck.sh completed with PASS: 144, FAIL: 0
full pytest inside final acceptance: 361 passed, 2 skipped, 3 subtests passed in 97.14s
generated outputs: data/vectorized/VectorizedResearch_latest.{json,csv,md}
```

Latest vectorized UI bridge evidence:

```text
tests/test_workspace_shell.py tests/test_scripts.py tests/test_vectorized_research.py: 25 passed
curl http://127.0.0.1:8501/_stcore/health returned ok
scripts/statusPFIOS.sh detected http://localhost:8501
Browser visual verification is still blocked by local Browser runtime kernel-asset initialization failure
scripts/finalAcceptanceCheck.sh completed with PASS: 148, FAIL: 0
full pytest inside final acceptance: 363 passed, 2 skipped, 3 subtests passed in 94.83s
scripts/cleanCache.sh --json removed 2 paths, 6 files, 557.69 KB
```

Latest hotspot runtime optimization evidence:

```text
tests/test_market_hotspots.py tests/test_app_dashboard.py tests/test_scripts.py: 73 passed
scripts/hotspotRuntimeSummary.sh --limit 6 returned status=Review objects=6/6 slices=96 rows=576 ttl=3600
scripts/verifyPFIOS.sh completed; full pytest 367 passed, 2 skipped, 3 subtests passed
scripts/finalAcceptanceCheck.sh completed with PASS: 155, FAIL: 0
scripts/cleanCache.sh --json removed 20 paths, 90 files, 1549.09 KB
github_ready/PFI_OS mirror rsync transferred 15 files
```

Latest hotspot persisted cache evidence:

```text
tests/test_market_hotspots.py tests/test_scripts.py tests/test_app_dashboard.py: 75 passed
scripts/hotspotRuntimeSummary.sh --use-persisted-cache first run: cache=computed
scripts/hotspotRuntimeSummary.sh --use-persisted-cache second run: cache=persisted
scripts/finalAcceptanceCheck.sh completed with PASS: 158, FAIL: 0
full pytest inside final acceptance: 369 passed, 2 skipped, 3 subtests passed in 129.06s
```

Latest 52ETF read-only reference evidence:

```text
web check of https://52etf.site/ showed public 大盘云图 / A股热力图 page with A股 board tabs and operating notes
PFIOS52ETFPublicSnapshotV1 writes local latest snapshot without raw HTML and can feed PFIOS52ETFHotspotComparisonV1
Hotspot UI prefers data/integrations/site52etf/Site52ETFPublicSnapshot_latest.json before cached live fetch
data/integrations/site52etf/*.json is gitignored and only .gitkeep is committed
urllib certificate-chain failures fall back to system /usr/bin/curl; curl failure still returns Unavailable/NeedsReview
tests/test_site52etf.py tests/test_app_dashboard.py tests/test_scripts.py: 76 passed
live /tmp snapshot smoke returned status=Available artifact_status=Pass board_count=7 cadence=8 raw_html_stored=False
```

Latest research chart UX evidence:

```text
py_compile passed for src/pfi_os/app/streamlit_app.py
tests/test_app_dashboard.py tests/test_scripts.py: 64 passed
scripts/finalAcceptanceCheck.sh completed with PASS: 164, FAIL: 0
full pytest inside final acceptance: 373 passed, 2 skipped, 3 subtests passed in 129.43s
curl http://localhost:8501 returned 200 OK and /_stcore/health returned ok
scripts/cleanCache.sh --json removed 18 paths, 88 files, 1511.43 KB
```


```text
```

Latest Company CashFlow runtime summary evidence:

```text
py_compile passed for src/pfi_os/business/cashflow.py, src/pfi_os/examples/cashflow_command.py, and src/pfi_os/app/streamlit_app.py
tests/test_cashflow_command.py tests/test_scripts.py tests/test_app_dashboard.py: 70 passed
scripts/cashFlowCommand.sh --summary-json returned PFIOSCompanyCashFlowRuntimeSummaryV1 status=Blocked cashflow_status=MissingBalance entry_count=0 and no full entries
scripts/cashFlowCommand.sh --as-of 2026-06-16 --output-dir /tmp/pfi_cashflow_smoke wrote JSON/CSV/MD/PDF/latest/runtime summary
scripts/finalAcceptanceCheck.sh completed with PASS: 173, FAIL: 0
full pytest inside final acceptance: 376 passed, 2 skipped, 3 subtests passed in 125.37s
scripts/cleanCache.sh --json removed 20 paths, 90 files, 1561.46 KB
```

Latest Policy Intelligence runtime summary evidence:

```text
py_compile passed for src/pfi_os/policy/radar.py, src/pfi_os/examples/policy_radar.py, and src/pfi_os/app/streamlit_app.py
tests/test_policy_radar.py tests/test_scripts.py tests/test_app_dashboard.py: 71 passed
scripts/policyRadar.sh --summary-json returned PFIOSPolicyIntelligenceRuntimeSummaryV1 status=Blocked policy_status=MissingPolicyEvidence opportunity_count=0 and no full opportunities
scripts/policyRadar.sh --as-of 2026-06-16 --output-dir /tmp/pfi_policy_smoke wrote JSON/CSV/MD/PDF/latest/runtime summary
scripts/finalAcceptanceCheck.sh completed with PASS: 177, FAIL: 0
full pytest inside final acceptance: 378 passed, 2 skipped, 3 subtests passed in 116.09s
curl http://localhost:8501 returned 200 OK and /_stcore/health returned ok
scripts/cleanCache.sh --json removed 20 paths, 90 files, 1562.31 KB
```

Latest Consumption Guard runtime summary evidence:

```text
py_compile passed for src/pfi_os/consumption/guard.py, src/pfi_os/examples/consumption_guard.py, and src/pfi_os/app/streamlit_app.py
tests/test_consumption_guard.py tests/test_scripts.py tests/test_app_dashboard.py: 72 passed
scripts/consumptionGuard.sh --summary-json returned PFIOSConsumptionGuardRuntimeSummaryV1 status=Blocked guard_status=MissingConsumptionEvidence event_count=0 and no full events
scripts/consumptionGuard.sh --as-of 2026-06-16 --output-dir /tmp/pfi_consumption_smoke --monthly-investable-budget 1000 wrote JSON/CSV/MD/PDF/latest/runtime summary
scripts/finalAcceptanceCheck.sh completed with PASS: 181, FAIL: 0
full pytest inside final acceptance: 380 passed, 2 skipped, 3 subtests passed in 125.89s
curl http://localhost:8501 returned 200 OK and /_stcore/health returned ok
scripts/cleanCache.sh --json removed 20 paths, 90 files, 1567.97 KB
```

Latest Executive Command Center runtime summary aggregation evidence:

```text
py_compile passed for src/pfi_os/executive/command_center.py and src/pfi_os/examples/command_center.py
tests/test_command_center.py tests/test_scripts.py tests/test_app_dashboard.py: 74 passed
scripts/commandCenter.sh default repo smoke returned status=NeedsReview with PDF output verified; earlier repo data fell back to full_snapshot where standalone runtime latest files were absent
scripts/finalAcceptanceCheck.sh completed with PASS: 186, FAIL: 0
full pytest inside final acceptance: 382 passed, 2 skipped, 3 subtests passed in 103.38s
curl http://localhost:8501 returned 200 OK and /_stcore/health returned ok
scripts/cleanCache.sh --json removed 19 paths, 89 files, 1074.3 KB
```

Latest Runtime Summary Refresh evidence:

```text
scripts/refreshRuntimeSummaries.sh --as-of 2026-06-16 --monthly-investable-budget 1000 returned PFIOSRuntimeSummaryRefreshV1 status=Pass summaries=4
runtime summary safety check showed no full records/entries/opportunities/events keys and no local absolute project path in the four latest JSON files
scripts/commandCenter.sh real repo smoke loaded all four sources with mode=runtime_summary and produced a valid PDF
tests/test_runtime_summary_refresh.py tests/test_command_center.py tests/test_scripts.py: 28 passed
scripts/finalAcceptanceCheck.sh completed with PASS: 201, FAIL: 0
full pytest inside final acceptance: 384 passed, 2 skipped, 3 subtests passed in 194.97s
curl http://127.0.0.1:8501 returned 200 OK and /_stcore/health returned ok
scripts/statusPFIOS.sh after stop reported not running on ports 8501-8510
scripts/cleanCache.sh --json removed 19 paths, 90 files, 1033.76 KB
```

Latest Company CashFlow reviewed input refresh evidence:

```text
scripts/cashFlowReviewedInputRefresh.sh --as-of 2026-06-16 --json returned PFIOSCompanyCashFlowReviewedInputRefreshV1 status=Blocked cashflow_status=MissingReviewedInput with outputs={}
scripts/cashFlowReviewedInputRefresh.sh --as-of 2026-06-16 --entry-path data/cashflow/CompanyCashFlowReviewedInput.example.json --output-dir /tmp/pfi_cashflow_reviewed_smoke returned status=Pass cashflow_status=Stable balance=18000.0 net=3840.0 runway_days=1500.0
scripts/refreshRuntimeSummaries.sh --project-root /tmp/pfi_runtime_summary_cashflow_smoke --cashflow-entry-path <repo>/data/cashflow/CompanyCashFlowReviewedInput.example.json returned Company CashFlow runtime_status=Pass
scripts/commandCenter.sh --project-root /tmp/pfi_runtime_summary_cashflow_smoke loaded Company CashFlow from runtime_summary with Stable status and valid PDF output
tests/test_cashflow_reviewed_input_refresh.py tests/test_cashflow_command.py tests/test_runtime_summary_refresh.py tests/test_scripts.py: 31 passed
scripts/finalAcceptanceCheck.sh completed with PASS: 212, FAIL: 0
full pytest inside final acceptance: 388 passed, 2 skipped, 3 subtests passed in 244.62s
curl http://127.0.0.1:8501 returned 200 OK and /_stcore/health returned ok
scripts/statusPFIOS.sh after stop reported not running on ports 8501-8510
scripts/cleanCache.sh --json removed 20 paths, 93 files, 1045.33 KB
```

Latest Policy reviewed-input and native macOS app launch evidence:

```text
scripts/policyReviewedInputRefresh.sh missing default private input returned PFIOSPolicyReviewedInputRefreshV1 status=Blocked policy_status=MissingReviewedInput and wrote no outputs
scripts/policyReviewedInputRefresh.sh --entry-path data/policy/PolicyReviewedInput.example.json returned status=Pass policy_status=Actionable opportunities=2 actionable=1
scripts/refreshRuntimeSummaries.sh --policy-entry-path data/policy/PolicyReviewedInput.example.json produced Policy runtime_status=Pass
scripts/commandCenter.sh temp smoke loaded Policy Intelligence from runtime_summary with value=Actionable and PDF magic %PDF-1.4
macos/PFI_OS_launcher.c now builds a native Mach-O launcher; installed Desktop, Downloads, and Applications apps bind Contents/Resources/PFI_OS_PROJECT_ROOT to the current local checkout
PFI_OS_APP_LAUNCH_DRY_RUN=1 on installed apps points to local StartPFIOS.command and github_fallback=absent
open -n ~/Downloads/PFI_OS.app returned 0, started local PFI_OS, /_stcore/health returned ok, and service was stopped afterward
```

Latest Consumption reviewed-input evidence:

```text
scripts/consumptionReviewedInputRefresh.sh missing default private input returned PFIOSConsumptionGuardReviewedInputRefreshV1 status=Blocked guard_status=MissingReviewedInput and wrote no outputs
scripts/consumptionReviewedInputRefresh.sh --event-path data/consumption/ConsumptionGuardReviewedInput.example.json returned status=NeedsReview guard_status=Watch events=3 counted=3 impulse_spend=420.0
scripts/refreshRuntimeSummaries.sh --consumption-event-path data/consumption/ConsumptionGuardReviewedInput.example.json produced Consumption Guard runtime_status=NeedsReview
scripts/commandCenter.sh temp smoke loaded Consumption Guard from runtime_summary with value=Watch and PDF magic %PDF-1.4
focused pytest: tests/test_consumption_reviewed_input_refresh.py tests/test_consumption_guard.py tests/test_runtime_summary_refresh.py tests/test_scripts.py -> 31 passed
heavy smoke note: do not run finalAcceptanceCheck or ciSmoke by default after user requested no repeated SmokeTest Fail triggers
```

Runtime notes:

- Normal app launch installs/reuses `.[app]` only through `scripts/pfiRuntime.sh`.
- Verification scripts install `.[test]` only when pytest is missing.
- `.venv/.pfi_os_app_ready` is a local marker and must not be committed.
- `openpyxl>=3.1` is now a base dependency because Excel holdings files are a supported integration path.
- In-app Browser visual automation was not completed because the Browser runtime failed to initialize local kernel assets; use HTTP health/final acceptance evidence until Browser tooling is healthy.
- The UI Shell now includes `macOS 生命周期`, showing app entry points, lifecycle commands, and cache dry-run counts. Only allowlisted local lifecycle scripts can execute from the page; `scripts/cleanCache.sh` fails closed while the service is running and preserves reports, holdings, imports, SQLite databases, migrated source samples, and market bar caches.

Previous verified engineering step: `policy_intelligence migration and ResearchBus workspace manifest adapter`.

Current in-progress UI Shell step: Streamlit `system_status_panel()` now renders a
`统一 Workspace Shell` block from compact manifests plus `ResearchBus` registry/state.
This is the first UI acceptance bridge for the canonical workspace systems; it does not
scan subsystem source trees.

Current canonical systems in `ResearchBus` are:

```text
finance_ledger
industry_research
policy_intelligence
```

The adapter reads `systems/*/SYSTEM_MANIFEST.json` and publishes compact status only. It intentionally excludes legacy absolute roots, private runtime SQLite, report bodies, account data, and caches.

Previous verified engineering step: `PFI_OS app identity, icon, and legacy launcher cleanup`.

Validated evidence from the implementation run:

```text
PFI_OS app plist/icon check: passed for Desktop, Downloads, and Applications
legacy-name scan: no deprecated product-name text or filename residue in scoped project
deleted old legacy PDFs: 3 historical 2026-06-07 PDFs
py_compile: passed for renamed app/report/data/integration modules
target pytest: 28 passed in 31.48s
```

The old historical `.venv` was deleted during slimming. The current checkout can recreate a runtime through the maintained scripts:

```bash
./scripts/startPFIOS.sh
./scripts/verifyPFIOS.sh
./scripts/finalAcceptanceCheck.sh
```

## Safety Boundaries

- No autonomous real-money trading.
- No unattended broker order placement.
- No stored brokerage passwords or API secrets.
- No automatic payments, bank transfers, tax filings, or government submissions.
- All trading-adjacent outputs are research, review queues, simulations, or broker-ready intents requiring explicit human confirmation.

## Recommended Next Run

Next subsystem options:

2. Expand persisted hotspot cache with manual invalidation and cache metrics if repeated large-object runs still feel slow.
3. Add private-data import helpers around Consumption Guard only after the reviewed-input contract is stable.

See `15_OPEN_QUESTIONS.md` for remaining scope and sequencing.

## Latest Sync And Slimming Run

The 2026-06-15 pursuing-goal baseline added:

- `systems/*/SYSTEM_MANIFEST.json` for finance ledger, industry research, and policy intelligence;
- `shared/security/system_permissions.json` with fail-closed cross-system scopes;
- `shared/schema/*.json` for child-system manifests and research events;
- `.github/workflows/smoke.yml` and `scripts/ciSmoke.sh`;
- public-safe `data/researchBus/ResearchBusSnapshot.example.json`;
- removal of tracked `data/researchBus/ResearchBusSnapshot.json` runtime state.

The follow-on finance ledger migration moved the first child system beyond manifest-only:

- `systems/finance_ledger/source/` now contains source, tests, docs, scripts, configs, AGENTS/HANDOFF/README, and public-safe icon assets;
- `systems/finance_ledger/samples/` contains only synthetic Alipay/WeChat sample bills;
- root `scripts/ciSmoke.sh` now also compiles finance ledger source and runs parser/classifier/reconciliation smoke tests;
- private `data/`, `outputs/`, `work/`, SQLite databases, generated reports, raw bills, and transaction-level outputs remain excluded.

The follow-on industry research migration moved the second child system beyond manifest-only:

- `systems/industry_research/source/` now contains source, tests, docs, scripts, configs, prompts, templates, AGENTS/HANDOFF/README, doctor/setup/Makefile, and sanitized sample fixtures;
- `systems/industry_research/source/data/sample/` is public-safe fixture data only;
- root `scripts/ciSmoke.sh` now also compiles industry source, runs focused tests, and checks CLI help;
- private Alipay data, real holdings, moomoo local databases, report artifacts, generated PDFs/Word/Excel files, cookies, API keys, and runtime logs remain excluded;
- migrated full suite evidence: `198 passed, 9 subtests passed`.

The follow-on policy intelligence migration moved the third child system beyond manifest-only:

- `systems/policy_intelligence/source/` now contains source, tests, docs, scripts, configs, rules, README/HANDOFF, and pyproject metadata;
- `systems/policy_intelligence/source/data/sample/` contains only synthetic or structurally anonymized fixtures;
- root `scripts/ciSmoke.sh` now also compiles policy source, checks the report runner shell syntax, runs focused policy tests, and checks CLI help;
- runtime SQLite databases, automation state, monitor status, run logs, snapshots, reports, Chrome profiles, cookies, platform auth, API keys, raw HTML dumps, and local logs remain excluded.

Thread handoff routing has been consolidated in:

```text
docs/ThreadHandshakeManifest.md
```

It records the read-only handoff results from the Consumption Analysis Original, Government Document Interpretation, and Industry Research source threads, including roots, sensitive boundaries, migrated state, and next migration steps.

The earlier 2026-06-13 GitHub sync and local slimming run added public-safe launcher templates, refreshed handoff boundaries, and documented local retention/deletion policy in:

```text
cleanup/PFI_OS_GitHub_Sync_Local_Slimming_20260613.md
```

## 2026-06-16 macOS App Runtime Acceptance Stabilization

This run addressed the user complaint that repeated SmokeTest Fail events were creating noise.

What changed:

- Native `PFI_OS.app` launcher uses `/bin/zsh -f` for local `StartPFIOS.command`.
- The launcher no longer names Terminal or GitHub fallback and uses short health-port curl timeouts.
- `scripts/installPFIOSEntryApps.sh` signs in a temporary staging directory, then installs to Desktop, Downloads, and Applications with `ditto --norsrc --noextattr --noacl`.
- `scripts/stopPFIOS.sh` now stops project-scoped launcher processes as well as Streamlit.
- `scripts/macosRuntimeAcceptance.sh --launch-method app` defaults to a 300-second app wait window and falls back from macOS `open -n` to the same bundle executable if no log/health signal appears.

Verified without heavy SmokeTest:

```text
targeted pytest: 38 passed
syntax checks: StartPFIOS.command, stopPFIOS.sh, installPFIOSEntryApps.sh, macosRuntimeAcceptance.sh, finalAcceptanceCheck.sh passed
App Lite: status=Pass pass=29 fail=0 info=2
App Runtime: status=Pass pass=10 fail=0 post_healthy_ports=[]
git diff --check: passed
sensitive diff scan: no hits
```

Operational instruction for next agents:

- Do not run `scripts/finalAcceptanceCheck.sh`, `scripts/ciSmoke.sh`, full pytest, or git hooks unless explicitly requested as a release gate.
- Use App Lite, Runtime Acceptance, focused pytest, syntax checks, `git diff --check`, and sensitive scans for normal iteration.

## 2026-06-16 Hotspot Cache Control And Low-Token Runtime

This run continued the user goal of reducing slow hotspot generation and token/context pressure.

What changed:

- `src/pfi_os/analysis/market_hotspots.py` now exposes `PFIOSHotspotCacheStatusV1`, `PFIOSHotspotCacheDirectorySummaryV1`, current request cache status, directory summary, and current request invalidation.
- `src/pfi_os/app/streamlit_app.py` now renders `热点缓存` before generation with current request state, age, remaining TTL, directory file count, and a button to clear only the active request-key cache.
- `src/pfi_os/examples/hotspot_runtime_summary.py` and `scripts/hotspotRuntimeSummary.sh` support CLI-only `--cache-status` and `--invalidate-cache`.
- Acceptance checklist now requires cache status visibility and current-request-only invalidation.

Verified without heavy SmokeTest:

```text
targeted pytest: tests/test_market_hotspots.py tests/test_scripts.py -> 39 passed
syntax checks: hotspotRuntimeSummary.sh and finalAcceptanceCheck.sh passed
CLI cache status: PFIOSHotspotCacheStatusV1 returned without market-bar loading
CLI cache loop: computed summary -> cache hit -> invalidate Deleted 381228 bytes
git diff --check: passed
sensitive diff scan: no hits
post-test cache cleanup: 1 cache dir, 4 files, about 16 KB
```

Operational instruction:

- Use `./scripts/hotspotRuntimeSummary.sh --cache-status --json-only ...` to debug slow hotspot requests before recomputing them.
- Use `--invalidate-cache` only for the current request fingerprint; do not delete `data/cache/market_data` or other subsystem caches for hotspot refresh.

## 2026-06-16 Hotspot Per-Symbol Timing Trace

This run made hotspot slowness observable at symbol level.

What changed:

- `PFIOSHotspotRequestTraceV1` was added to `src/pfi_os/analysis/market_hotspots.py`.
- Hotspot UI renders `数据请求耗时` with request count, success/failure, total elapsed time, slowest request, and slowest per-symbol rows.
- CLI hotspot summary now records trace timing for Sample runs, persists it in hotspot cache, and includes it in cached summary output.
- Persisted cache stores compact diagnostics only, not raw provider payloads or raw price frames.

Verified without heavy SmokeTest:

```text
targeted pytest: tests/test_market_hotspots.py tests/test_scripts.py -> 41 passed
syntax checks: hotspotRuntimeSummary.sh and finalAcceptanceCheck.sh passed
CLI trace summary: PFIOSHotspotRequestTraceV1 request_count=5 success_count=5 failed_count=0
CLI cache hit preserved request_trace.request_count=5
CLI invalidate removed 384423 bytes
git diff --check: passed
sensitive diff scan: no hits
post-test cache cleanup: 1 cache dir, 4 files, about 16 KB
```

Operational instruction:

- When the user says hotspot generation is slow, first inspect `request_trace.slowest` before increasing timeouts or changing provider logic.
- Continue avoiding `ciSmoke.sh`, `finalAcceptanceCheck.sh`, full pytest, and hooks unless explicitly requested.

## 2026-06-16 Development Ready Check Without Heavy Smoke

What changed:

- Added `src/pfi_os/system/dev_readiness.py`, `src/pfi_os/examples/dev_ready_check.py`, and `scripts/devReadyCheck.sh`.
- `scripts/devReadyCheck.sh --summary-json` now emits `PFIOSDevReadyCheckV1` for normal development checks.
- It checks executable entrypoints, selected zsh syntax, selected Python AST syntax, runtime status, cache dry-run, and git status only.
- Dirty worktree is informational, not failing.
- The shell entry does not run final acceptance, CI smoke, full pytest, browser automation, market refresh, broker/order flows, or strategy smoke gates.
- `scripts/cleanCache.sh` now prevents repo-local pycache creation while checking or deleting cache by exporting `PYTHONDONTWRITEBYTECODE=1` and `PYTHONPYCACHEPREFIX=/private/tmp/pfi_os-pycache`.
- `README.md`, `docs/Testing.md`, `docs/AcceptanceChecklist.md`, `scripts/finalAcceptanceCheck.sh`, and tests were updated to make this the default low-noise path.

Verified without heavy SmokeTest:

```text
devReadyCheck summary: PFIOSDevReadyCheckV1 status=Pass pass=26 fail=0 info=1
targeted pytest: tests/test_dev_readiness.py tests/test_scripts.py -> 26 passed
syntax checks: devReadyCheck.sh and finalAcceptanceCheck.sh passed
cache cleanup: removed 49 paths, 262 files, 48 directories, 3269.6 KB total; final dry-run candidate_count=0
```

Operational instruction:

- For day-to-day progress, run `./scripts/devReadyCheck.sh --summary-json` before focused tests.
- Reserve `scripts/finalAcceptanceCheck.sh`, `scripts/ciSmoke.sh`, full pytest, and git hooks for explicit release acceptance only.

## 2026-06-16 Dev Ready Check In UI Shell

What changed:

- `src/pfi_os/app/streamlit_app.py` now allowlists `scripts/devReadyCheck.sh` and renders a `开发检查` button in the `macOS 生命周期` panel.
- `src/pfi_os/app/dashboard.py` now includes `Dev Ready Check` as a UI-mode lifecycle action.
- `src/pfi_os/system/macos_lifecycle.py` now checks `DevReadyScriptExecutable` and UI allowlist coverage for `scripts/devReadyCheck.sh`.
- QuickStart, Docs Index, MacOSLifecycleReadiness docs, ReleaseNotes, and final acceptance static checks now reflect that Dev Ready is the normal first check.

Verified without heavy SmokeTest:

```text
targeted pytest: tests/test_workspace_shell.py tests/test_scripts.py tests/test_dev_readiness.py tests/test_macos_lifecycle_readiness.py -> 35 passed
devReadyCheck summary: PFIOSDevReadyCheckV1 status=Pass pass=26 fail=0 info=1
macOS lifecycle readiness summary: PFIOSMacOSLifecycleReadinessV1 status=Pass pass=29 fail=0
syntax checks: devReadyCheck.sh, cleanCache.sh, macosLifecycleReadiness.sh, finalAcceptanceCheck.sh passed
```

Operational instruction:

- In UI Shell work, keep `Final Acceptance` Terminal-only and keep `Dev Ready Check` as the default UI-runnable verifier.

## 2026-06-16 Runtime Acceptance Evidence Card

What changed:

- `src/pfi_os/app/dashboard.py` now exposes `macos_runtime_evidence_summary(payload)` with schema `MacOSRuntimeEvidenceSummaryV1`.
- `src/pfi_os/app/streamlit_app.py` now renders a read-only `运行时验收证据` section in the `macOS 生命周期` panel.
- The UI reads `data/systemAudit/MacOSRuntimeAcceptance_latest.json` only; it does not run `scripts/macosRuntimeAcceptance.sh`.
- Missing runtime evidence is shown as `Missing` with Terminal commands instead of failing the page.
- Acceptance docs now state that runtime acceptance evidence is displayed read-only and refreshed only from Terminal.

Verified without heavy SmokeTest:

```text
targeted pytest: tests/test_workspace_shell.py tests/test_scripts.py tests/test_macos_runtime_acceptance.py tests/test_dev_readiness.py -> 39 passed
devReadyCheck summary: PFIOSDevReadyCheckV1 status=Pass pass=26 fail=0 info=1
syntax checks: devReadyCheck.sh, cleanCache.sh, macosRuntimeAcceptance.sh, finalAcceptanceCheck.sh passed
```

Operational instruction:

- Do not add `scripts/macosRuntimeAcceptance.sh` to `LIFECYCLE_SCRIPT_ALLOWLIST`; keep it as evidence display plus Terminal commands only.

## 2026-06-16 Real Script Runtime Acceptance Evidence

What happened:

- Ran `./scripts/macosRuntimeAcceptance.sh --output-dir data/systemAudit --summary-json` on the local Mac.
- Result was `PFIOSMacOSRuntimeAcceptanceV1 status=Pass pass=10 fail=0 info=0`.
- It started and stopped local Streamlit successfully, verified health, verified running cache cleanup refusal, and ended with `post_healthy_ports=[]`.
- App Lite precheck also passed inside the run: `pass=29 fail=0 info=2`.
- The UI evidence summary reads the latest JSON as `MacOSRuntimeEvidenceSummaryV1 status=Pass` with cards `Pass / 10/10 / Today / script`.

Local evidence boundary:

- Evidence files are local-only because they include this Mac's absolute project root:
  - `data/systemAudit/MacOSRuntimeAcceptance_16062026.json`
  - `data/systemAudit/MacOSRuntimeAcceptance_latest.json`
- `.gitignore` excludes `data/systemAudit/MacOSRuntimeAcceptance*.json`; do not commit those files unless a sanitized artifact is generated.

Operational instruction:

- Next real acceptance step is app open-path runtime acceptance from Terminal, not Streamlit UI.

## 2026-06-16 Real App Open-Path Runtime Acceptance Evidence

What happened:

- Ran Downloads `PFI_OS.app` open-path runtime acceptance from Terminal:
  `./scripts/macosRuntimeAcceptance.sh --launch-method app --app-path "$HOME/Downloads/PFI_OS.app" --output-dir data/systemAudit --summary-json`
- Result was `PFIOSMacOSRuntimeAcceptanceV1 status=Pass pass=10 fail=0 info=0`.
- `launch_method=app`; the real app entry launched the local service, health appeared, cache cleanup refused delete mode while running, stop completed, and post-stop health was empty.
- App Lite precheck passed inside the run: `pass=29 fail=0 info=2`.
- UI evidence summary now reads the latest local evidence as `MacOSRuntimeEvidenceSummaryV1 status=Pass` with cards `Pass / 10/10 / Today / app`.

Local evidence boundary:

- Latest raw local files are still excluded from Git because they include this Mac's absolute project root:
  - `data/systemAudit/MacOSRuntimeAcceptance_16062026.json`
  - `data/systemAudit/MacOSRuntimeAcceptance_latest.json`

Operational instruction:

- The next high-ROI acceptance slice is visual/browser verification of the already validated app-open path.

## 2026-06-17 macOS UI Visual Acceptance Without Heavy Smoke

What changed:

- Added `scripts/uiVisualAcceptance.sh` with schema `PFIOSUIVisualAcceptanceV1`.
- The script verifies the local Streamlit workbench with headless Chrome, checks `PFI_OS`, `工作台状态`, `macOS 生命周期`, `运行时验收证据`, cache preview text, and visible lifecycle buttons.
- It starts Streamlit only when no healthy local service exists and stops only the service it started.
- It writes local JSON and PNG evidence under `data/systemAudit/UIVisualAcceptance*`, which remains gitignored because it contains local browser/runtime evidence.
- `scripts/devReadyCheck.sh`, docs, and targeted tests now include the visual acceptance entrypoint.

Verified without heavy SmokeTest:

```text
./scripts/uiVisualAcceptance.sh --summary-json
PFIOSUIVisualAcceptanceV1 status=Pass pass=16 fail=0 screenshot_bytes=278744 started_by_acceptance=true

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -m pytest tests/test_scripts.py tests/test_dev_readiness.py -q -p no:cacheprovider
28 passed

./scripts/devReadyCheck.sh --summary-json
PFIOSDevReadyCheckV1 status=Pass pass=28 fail=0 info=1 cache_candidate_count=0

git diff --check
passed

./scripts/cleanCache.sh --json
removed 23 cache paths, 113 files, 23 dirs, 1591.58 KB; final dry-run candidate_count=0

./scripts/statusPFIOS.sh
PFIOS is not running on ports 8501-8510.
```

Operational instruction:

- For routine macOS UI evidence, use `./scripts/uiVisualAcceptance.sh --summary-json`; do not run `scripts/finalAcceptanceCheck.sh`, `scripts/ciSmoke.sh`, full pytest, or git hooks unless the user explicitly asks for a release/full-acceptance gate.

## 2026-06-17 GitHub-Safe macOS Public Acceptance Summary

What changed:

- Added `scripts/macosPublicAcceptanceSummary.sh` and schema `PFIOSMacOSPublicAcceptanceSummaryV1`.
- Added `src/pfi_os/system/macos_public_acceptance.py` and CLI `pfi_os.examples.macos_public_acceptance`.
- Generated GitHub-safe public artifacts under `docs/evidence/`:
  - `MacOSAcceptancePublicSummary_20260617.json`
  - `MacOSAcceptancePublicSummary_latest.json`
  - `MacOSAcceptancePublicSummary_latest.md`
- The summary reads local runtime/UI evidence but strips absolute project paths, browser executable paths, screenshot paths, process IDs, raw logs, and private data.

Verified without heavy SmokeTest:

```text
./scripts/macosPublicAcceptanceSummary.sh
PFIOSMacOSPublicAcceptanceSummaryV1 status=Pass sources_pass=2/2 runtime=Pass ui=Pass

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -m pytest tests/test_macos_public_acceptance.py tests/test_scripts.py tests/test_dev_readiness.py -q -p no:cacheprovider
32 passed

./scripts/devReadyCheck.sh --summary-json
PFIOSDevReadyCheckV1 status=Pass pass=32 fail=0 info=1

leak scan on docs/evidence
no /Users, /Applications, browser executable, screenshot path, PID, log, or file URL matches
```

Operational instruction:

- Commit `docs/evidence/MacOSAcceptancePublicSummary_latest.*` for handoff, but keep raw `data/systemAudit/MacOSRuntimeAcceptance*` and `data/systemAudit/UIVisualAcceptance*` local and gitignored.

## 2026-06-17 macOS Acceptance Hub Consolidation

What changed:

- Added `scripts/macosAcceptance.sh` as the user-friendly default macOS acceptance entrypoint.
- Added schema `PFIOSMacOSAcceptanceHubV1`, module `src/pfi_os/system/macos_acceptance_hub.py`, and CLI `pfi_os.examples.macos_acceptance_hub`.
- Default no-arg behavior is `--mode daily --summary-json`, combining `devReadyCheck` and `macosPublicAcceptanceSummary`.
- Explicit modes remain available for component evidence: `app-entry`, `lifecycle`, `runtime`, `app-runtime`, `ui`, and `public-summary`.
- Unified Workspace now shows one primary `日常验收` button; `开发检查`, `轻量验收`, and `生命周期验收` moved under `高级单项验收`.

Verified without heavy SmokeTest:

```text
./scripts/macosAcceptance.sh
PFIOSMacOSAcceptanceHubV1 status=Pass mode=daily pass=2 fail=0

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -m pytest tests/test_macos_acceptance_hub.py tests/test_scripts.py tests/test_dev_readiness.py tests/test_workspace_shell.py -q -p no:cacheprovider
41 passed

zsh -n scripts/macosAcceptance.sh && zsh -n scripts/devReadyCheck.sh && zsh -n scripts/finalAcceptanceCheck.sh
passed
```

Operational instruction:

- For normal use and handoff, run `./scripts/macosAcceptance.sh` first.
- Use component scripts only when debugging or refreshing specific evidence; keep `runtime`, `app-runtime`, and `ui` as explicit modes because they may start services or browsers.
