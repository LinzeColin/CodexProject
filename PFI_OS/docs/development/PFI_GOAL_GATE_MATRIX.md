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
| PFI-001 | Reproducible env, lock, CI, secret scan, clean install, offline warm start | **Implemented this run** | `.python-version`, `requirements.lock`, `scripts/installLockedEnv.sh`, `scripts/pfiGate.sh`, `scripts/secretScan.sh`, `.github/workflows/smoke.yml`, `tests/contract/test_pfi_reproducible_env.py`; clean install to `/tmp/pfi_os_clean_env_pfi001`; `scripts/pfiGate.sh fast/target`; offline `scripts/startPFIOS.sh` health check | CI server result and injected-failure proof still need PR/CI evidence |
| PFI-002 | Active PFI identity, retired value-ledger removed from active paths | Mostly complete | `tests/test_pfi_product_contracts.py`, active Web Shell scan, archive-only policy | Re-run controlled search in release gate; preserve approved archive list |
| PFI-003 | Supervisor, durable Job Store, lifecycle, backup/restore, crash recovery | Partial | Existing start/stop/status, launch lock, shutdown monitor, Phase C scheduler, Phase D backup/restore tests | Dedicated supervisor/job lease/cancel/resume/dead-letter and sleep/wake/crash matrix not fully proven |
| PFI-004 | Single truth source, evidence/PIT contracts, Golden fixtures | Partial | Operational Store, source registry, Phase A contracts, homepage ingestion, Phase B workflow evidence | Full authoritative-store enforcement, dual-read reconciliation, PIT invalid-write rejection, financial Golden suite still incomplete |
| PFI-005 | Six-workspace UI Shell, context, feedback, a11y, visual/perf | Partial to strong | `web/`, `src/pfi_os/ui_contracts/web_shell.py`, Web Shell contract/e2e/visual tests, `scripts/uiVisualAcceptance.sh --summary-json` passed 31/31 with six workspace switches and strategy feature links for回测/扫描/盘感训练 | Four named fixture UAT journeys, axe/WCAG proof, performance budget and no legacy-page import gate still need explicit artifacts |
| PFI-006 | Markets vertical slice from source event to UI/action | Partial | Phase B Markets workflow contracts and Operational Store records | Full UI journey, portfolio overlay, alert/saved view, Golden metrics and browser E2E still need release-grade evidence |
| PFI-007 | Research/policy vertical slice with official evidence and citations | Partial | Phase B Research + Policy workflow contracts, report gap tasks | Unified research workspace, citation locator, report manifest and browser E2E still incomplete |
| PFI-008 | Portfolio vertical slice with import, reconciliation, risk, decision proposal | Partial | Phase B Portfolio workflow contracts, private boundary tests | Synthetic broker import ledger, corporate action/FX/cash Golden, optimizer constraints and E2E still incomplete |
| PFI-009 | Strategy vertical slice with PIT backtest, train/test, walk-forward | Partial | Strategy Lab workflow, backtest engine, market-feel training retained | Deterministic hash, no-future-data, delisted/corporate-action fixture, cancel/resume and model registry still incomplete |
| PFI-010 | Minute Fast Path: 3 sources p95 <= 60s, page closed still updates | Not complete | Phase C cached runtime and scheduler give local 60-second metadata only | Legal source selection, incremental worker, UI push, latency measurement, failure injection and soak missing |
| PFI-011 | Local LLM Deep Path with DisabledProvider fallback, citations, QA | Not complete | DisabledProvider boundary and local-model optionality docs | Hardware audit, provider interface, schema/citation tests, timeout/cancel/resource/prompt-injection QA missing |
| PFI-012 | MVP Release Gate: P0=0, P1 disposition, full release matrix, UAT, signed manifest | Not complete | Phase 5 engineering handoff package and current focused tests | Full Gate1-7 evidence, 24h soak, manual UAT, checksum manifest, rollback tag and CI evidence missing |

## Gate Matrix

| Gate | Required condition | Status | Evidence | Missing |
|---|---|---:|---|---|
| Gate 1 | P0 blockers closed; backup/restore, double instance and Golden pass | Partial | PFI-001 now has clean install/offline start; some Phase D backup/restore evidence exists | PFI-003 lifecycle matrix and PFI-004 Golden/PIT proof still missing |
| Gate 2 | Six-workspace fixture shell journeys, interaction and performance budgets | Partial | Web Shell tests, visual baseline, runtime smoke | Four formal fixture UAT journeys, axe/performance budgets |
| Gate 3 | Four vertical slices each have data, domain, API, UI, tasks, evidence, tests, rollback | Partial | Phase B workflow contracts | UI/API closure and rollback evidence per slice |
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

Continue with PFI-003 before expanding vertical features. Gate 1 cannot close
without stronger supervisor/job/lifecycle evidence, and PFI-003 is a dependency
for reliable PFI-010 Fast Path and PFI-012 Release Gate.
