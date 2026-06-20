# PFI Goal and Gate Matrix

Last updated: 2026-06-20 Australia/Sydney

Source of truth for this matrix:

- Iteration pack: `PFI_OS_CODEX_ITERATION_PACK_v0.2`
- Task pack file: `15_CODEX_TASK_PACK_v0.2.md`
- Roadmap file: `13_MIGRATION_ROADMAP_AND_GO_NO_GO.md`
- Acceptance checklist: `17_ACCEPTANCE_CHECKLIST.md`
- Current repository evidence and local command output

This matrix tracks the active long-running goal: finish PFI-001 through PFI-012
and close Gate 1 through Gate 7. It is not a completion claim for the whole
goal. An item is complete only when the evidence listed here is current and
strong enough for the item's full acceptance scope.

## Issue Matrix

| Issue | Required end state | Current status | Current evidence | Remaining proof or work |
|---|---|---:|---|---|
| PFI-001 | Reproducible env, lock, CI, secret scan, clean install, offline warm start | Strong PR/CI evidence | `.python-version`, `requirements.lock`, `scripts/installLockedEnv.sh`, `scripts/pfiGate.sh`, `scripts/secretScan.sh`, `scripts/pfiCiInjectedFailureProof.sh`, root workflow `.github/workflows/pfi-os-smoke.yml`, `tests/contract/test_pfi_reproducible_env.py`; clean install to `/tmp/pfi_os_clean_env_pfi001`; `scripts/pfiGate.sh fast/target`; offline `scripts/startPFIOS.sh` health check; PR #2 GitHub Actions run `27856494975` succeeded on commit `9ed86b6`, including `Run PFI target gate` and `Prove injected failure is blocked` | Re-run in final Gate 7 release package; no local/PR PFI-001 gap currently listed |
| PFI-002 | Active PFI identity, retired value-ledger removed from active paths | Mostly complete | `tests/test_pfi_product_contracts.py`, active Web Shell scan, archive-only policy | Re-run controlled search in release gate; preserve approved archive list |
| PFI-003 | Supervisor, durable Job Store, lifecycle, backup/restore, crash recovery | Strong local evidence | Existing start/stop/status, launch lock, shutdown monitor, Phase C scheduler, Phase D backup/restore tests; `DurableJobStore` covers idempotency, atomic claim, lease, heartbeat, bounded retry, cancel/resume, expired-lease recovery, and dead letter; `scripts/pfiSupervisor.sh` exposes contract/status/doctor/lifecycle commands plus double-worker, crash-recovery, and release acceptance smoke; PFI-003 durable job tests passed 8/8, supervisor CLI tests passed 7/7, and acceptance passed 10/10 with real TERM/KILL child-worker recovery, deterministic sleep/wake recovery, simulated network recovery, SQLite backup manifest, sanitized launchd throttle/log-rotation artifacts, Web Shell/runtime `supervisor_runtime`, private-log scan, and no-execution boundary checks | Re-run in CI/release packaging before Gate 7; no local PFI-003 implementation gap currently listed |
| PFI-004 | Single truth source, evidence/PIT contracts, Golden fixtures | Strong local evidence | Operational Store, source registry, Phase A contracts, homepage ingestion, Phase B workflow evidence, `src/pfi_os/application/pfi004_truth_golden.py`, `tests/contract/test_pfi004_truth_golden.py`; PFI-004 target tests passed 15/15 with Golden metrics, PIT replay, dual-read reconciliation, and `PIT_INVALID_WRITE` rejection | Re-run in CI/release packaging before final Gate 7; no local PFI-004 implementation gap currently listed |
| PFI-005 | Six-workspace UI Shell, context, feedback, a11y, visual/perf | Strong local Gate 2 evidence | `web/`, `src/pfi_os/ui_contracts/web_shell.py`, Web Shell contract/e2e/visual tests, `scripts/uiVisualAcceptance.sh --summary-json` passed 66/66 with six workspace switches, eight homepage navigation links, six function-page opens, and strategy feature links for回测/扫描/盘感训练; `scripts/pfiGate2ShellAcceptance.sh`, `tests/contract/test_pfi005_gate2_shell_acceptance.py`, and `docs/development/PFI005_GATE2_SHELL_ACCEPTANCE.md` define four named UAT journeys, WCAG structural proof with optional local axe scan, performance budgets, no legacy-page primary navigation, and Chinese-first user surface checks; latest local Gate2 browser evidence returned `status=Pass`, `pass=126`, `fail=0`, `info=2` | Re-run browser acceptance in final Gate 7 release package; optional third-party axe dependency can be installed later if release policy requires package-backed axe evidence rather than local WCAG structural proof |
| PFI-006 | Markets vertical slice from source event to UI/action | Strong local Gate 3 Markets evidence | Phase B Markets workflow contracts and Operational Store records; `src/pfi_os/application/pfi006_markets_acceptance.py`, `tests/contract/test_pfi006_markets_vertical_acceptance.py`, `scripts/pfi006MarketsAcceptance.sh`, and `docs/development/PFI006_MARKETS_VERTICAL_ACCEPTANCE.md` prove deterministic data -> domain -> API/read model -> same-shell UI -> task/evidence -> portfolio overlay -> alert/saved view -> Golden metrics -> rollback chain; local acceptance passed 13/13 with event_count=90, alerts=2, saved_views=2, rollback=Pass; target gate passed 52 tests plus secret scan; UI visual acceptance passed 98/98 after market shell changes | Re-run in final Gate 7 package; Gate 3 still needs equivalent PFI-007 Research/Policy, PFI-008 Portfolio, and PFI-009 Strategy evidence |
| PFI-007 | Research/policy vertical slice with official evidence and citations | Strong local Gate 3 Research/Policy evidence | Phase B Research + Policy workflow contracts, report gap tasks; `src/pfi_os/application/pfi007_research_policy_acceptance.py`, `tests/contract/test_pfi007_research_policy_vertical_acceptance.py`, `scripts/pfi007ResearchPolicyAcceptance.sh`, and `docs/development/PFI007_RESEARCH_POLICY_VERTICAL_ACCEPTANCE.md` prove reviewed policy/report data -> policy radar/report gaps -> UI read model -> same-shell research controls -> citation locator -> report manifest -> task/evidence records -> Golden metrics -> rollback chain; local acceptance passed 14/14 with policy_record_count=2, official_citation_count=1, report_gap_count=3, report_manifest_count=1, rollback=Pass; target gate passed 58 tests plus secret scan; UI visual acceptance passed 98/98 after research shell changes | Re-run in final Gate 7 package; Gate 3 still needs equivalent PFI-008 Portfolio and PFI-009 Strategy evidence |
| PFI-008 | Portfolio vertical slice with import, reconciliation, risk, decision proposal | Partial | Phase B Portfolio workflow contracts, private boundary tests | Synthetic broker import ledger, corporate action/FX/cash Golden, optimizer constraints and E2E still incomplete |
| PFI-009 | Strategy vertical slice with PIT backtest, train/test, walk-forward | Partial | Strategy Lab workflow, backtest engine, market-feel training retained | Deterministic hash, no-future-data, delisted/corporate-action fixture, cancel/resume and model registry still incomplete |
| PFI-010 | Minute Fast Path: 3 sources p95 <= 60s, page closed still updates | Not complete | Phase C cached runtime and scheduler give local 60-second metadata only | Legal source selection, incremental worker, UI push, latency measurement, failure injection and soak missing |
| PFI-011 | Local LLM Deep Path with DisabledProvider fallback, citations, QA | Not complete | DisabledProvider boundary and local-model optionality docs | Hardware audit, provider interface, schema/citation tests, timeout/cancel/resource/prompt-injection QA missing |
| PFI-012 | MVP Release Gate: P0=0, P1 disposition, full release matrix, UAT, signed manifest | Not complete | Phase 5 engineering handoff package and current focused tests | Full Gate1-7 evidence, 24h soak, manual UAT, checksum manifest, rollback tag and CI evidence missing |

## Gate Matrix

| Gate | Required condition | Status | Evidence | Missing |
|---|---|---:|---|---|
| Gate 1 | P0 blockers closed; backup/restore, double instance and Golden pass | Closed for current evidence scope | PFI-001 clean install/offline start plus PR #2 GitHub Actions run `27856329389` failed first because the root workflow exposed missing Ubuntu `zsh`; run `27856494975` then succeeded after CI shell-runtime fix and includes target gate plus injected-failure proof. Phase D backup/restore evidence exists; PFI-003 has durable lifecycle, double-worker exclusion, real TERM/KILL recovery, deterministic sleep/wake recovery, network recovery, backup manifest, launchd throttle/log rotation, Web Shell read-model, and private-log scan evidence; PFI-004 has Golden/PIT proof with invalid-write rejection and dual-read reconciliation | Re-run as part of Gate 7 final release package |
| Gate 2 | Six-workspace fixture shell journeys, interaction and performance budgets | Closed for current evidence scope | Web Shell tests, visual baseline, runtime smoke, `scripts/pfiGate2ShellAcceptance.sh`, and `PFIGate2ShellAcceptanceV1` contract covering four named UAT journeys, same-shell function panels, WCAG structural proof, optional local axe scan, performance budgets, Chinese-first surface, and no legacy-page primary navigation; local run passed with 126 pass / 0 fail / 2 info | Re-run during Gate 7 final packaging with current browser evidence JSON |
| Gate 3 | Four vertical slices each have data, domain, API, UI, tasks, evidence, tests, rollback | Partial: Markets and Research/Policy slices strong | Phase B workflow contracts; PFI-006 Markets has acceptance script, Golden metrics, same-shell UI controls, alerts/saved views, portfolio overlay, task/evidence records, and rollback proof; PFI-007 Research/Policy has citation locator, report manifest, same-shell research controls, task/evidence records, Golden metrics, and rollback proof | Add equivalent closure for PFI-008 Portfolio and PFI-009 Strategy |
| Gate 4 | Minute SLA and resource budget pass | Not complete | None strong enough for PFI-010 | 3-source Fast Path, latency dashboard, 1h/24h soak |
| Gate 5 | Local deployment and LLM fallback; LLM outputs schema/citations/QA | Partial | PFI app entry, DisabledProvider boundary | Local LLM provider and QA gate evidence |
| Gate 6 | MVP release matrix, UAT, recovery, privacy audit, legacy freeze | Not complete | Phase 5 package only | Full release run and manual UAT |
| Gate 7 | Final delivery package, signed checksums, rollback tag, PR/CI green | Not complete | Current branch/PR comments from previous runs | Release tag, checksums, CI artifacts, final ZIP/PDF package |

## Current PFI-001 Evidence

Commands run locally during this repair:

```bash
rm -rf /tmp/pfi_os_clean_env_pfi001
PFI_PYTHON=/opt/anaconda3/bin/python3.12 PFI_VENV_DIR=/tmp/pfi_os_clean_env_pfi001 scripts/installLockedEnv.sh
PFI_PYTHON=/tmp/pfi_os_clean_env_pfi001/bin/python scripts/pfiGate.sh fast
PFI_PYTHON=/tmp/pfi_os_clean_env_pfi001/bin/python scripts/pfiGate.sh target
PFI_PYTHON=/tmp/pfi_os_clean_env_pfi001/bin/python PFI_UI_V2=1 scripts/startPFIOS.sh
curl http://127.0.0.1:8501/_stcore/health
scripts/stopPFIOS.sh
```

Observed results:

- Clean install from `requirements.lock` succeeded in `/tmp/pfi_os_clean_env_pfi001`.
- `pfiGate.sh fast` passed: 13 tests and secret scan.
- `pfiGate.sh target` passed: 36 tests, 2 deprecation warnings, secret scan, and `git diff --check`.
- Offline warm start used the locked environment, started Streamlit at `http://127.0.0.1:8501`, passed health check, and stopped cleanly.
- Startup output did not include `pip install` or dependency installation.

## Next Recommended Issue

Continue with Gate 3 / PFI-008 Portfolio vertical slice. Gate 1, Gate 2,
Markets, and Research/Policy are closed for the current evidence scope and
must be re-run in the final Gate 7 release package.
