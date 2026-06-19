# Serenity Daily Analysis Validation Summary

Generated: 20260614 - 09:47 CST / 20260614 - 11:47 AEST

## Commands Verified

```bash
python - <<'PY'
import sys
import types
from pathlib import Path
import pytest
root = Path.cwd()
package = types.ModuleType('tests')
package.__path__ = [str(root / 'tests')]
sys.modules['tests'] = package
sys.path.insert(0, str(root))
raise SystemExit(pytest.main(['-q']))
PY
pytest -q tests/test_completion_audit.py tests/test_scheduler.py tests/test_comparison.py
pytest -q tests/test_timezones.py tests/test_scheduler.py tests/test_automation_tick.py tests/test_completion_audit.py
pytest -q tests/test_comparison.py tests/test_scheduler.py tests/test_automation_tick.py tests/test_integration.py
pytest -q tests/test_production_action_queue.py tests/test_intake_validator.py tests/test_risk_gate_regression.py tests/test_completion_audit.py
pytest -q tests/test_reporting_ui.py tests/test_completion_audit.py
pytest -q tests/test_reporting_ui.py tests/test_application_server.py
python -m py_compile app/core/application_portal.py app/core/reporting.py app/core/completion_audit.py app/cli.py
python -m py_compile app/core/application_portal.py
python -m py_compile app/core/application_portal.py app/core/completion_audit.py
python -m py_compile app/core/notification.py app/core/reporting.py
python -m py_compile app/core/reporting.py app/core/pipeline.py app/core/completion_audit.py
python -m app.cli application-portal --json
pytest -q tests/test_reporting_ui.py tests/test_application_server.py tests/test_completion_audit.py
pytest -q tests/test_notification.py tests/test_automation_tick.py tests/test_integration.py
python -m pytest -q tests/test_reporting_ui.py tests/test_integration.py tests/test_notification.py
python -m pytest -q tests/test_completion_audit.py tests/test_reporting_ui.py tests/test_integration.py tests/test_notification.py
python -m pytest -q
python -m pytest --collect-only
python -m app.cli notify --run-id sda_20260613T053528Z_r8_2579b9f4 --dry-run --json
python - <<'PY'
from pathlib import Path
paths = [
    Path('outputs/application/serenity-app-icon.png'),
    Path('outputs/application/Serenity 每日分析.app/Contents/Resources/SerenityIcon.icns'),
    Path.home() / 'Downloads/Serenity 每日分析.app/Contents/Resources/SerenityIcon.icns',
    Path('/Applications/Serenity 每日分析.app/Contents/Resources/SerenityIcon.icns'),
]
for path in paths:
    print(path, path.exists(), path.stat().st_size if path.exists() else 0)
info = Path('/Applications/Serenity 每日分析.app/Contents/Info.plist').read_text(encoding='utf-8')
print('CFBundleIconFile' in info, 'SerenityIcon' in info)
PY
python - <<'PY'
from pathlib import Path
import re
html=Path('outputs/application/index.html').read_text()
m=re.search(r'<a class="action" href="([^"]+)">打开快照</a>', html)
print({'href': m.group(1) if m else None})
if m:
    p=(Path('outputs/application') / m.group(1)).resolve()
    print({'resolved': str(p), 'exists': p.exists()})
PY
python -m py_compile app/core/completion_audit.py app/core/comparison.py app/core/pipeline.py app/core/scheduler_runner.py
python -m py_compile app/scheduler.py app/core/completion_audit.py app/core/scheduler_runner.py app/core/automation_tick.py app/cli.py
python -m app.cli slots --json
python -m py_compile app/core/reporting.py
python -m py_compile app/adapters/mail_notifier.py app/core/reporting.py app/core/notification.py app/core/pipeline.py app/core/mail_smoke.py tests/test_mail_notifier.py tests/test_notification.py tests/test_mail_smoke.py
python -m pytest -q tests/test_mail_notifier.py tests/test_notification.py tests/test_mail_smoke.py tests/test_integration.py
python -m app.cli notify --run-id sda_20260613T094539Z_r7_31fb1cc3 --dry-run --json
python -m app.cli source-evidence-audit --json
python -m app.cli benchmark-smoke --json
python -m app.cli risk-gate-regression --require-pass --json
python -m app.cli production-unblock-matrix --json
python -m app.cli production-action-queue --json
SERENITY_MAIL_SEND_ENABLED=true python -m app.cli preflight --json
SERENITY_MAIL_SEND_ENABLED=true python -m app.cli automation-tick --now 2026-06-15T14:30:00+08:00 --allow-duplicate --no-dry-run --send-mail --local --require-production --json
SERENITY_MAIL_SEND_ENABLED=true python -m app.cli completion-audit --json
file outputs/preflight/PRODUCTION_READINESS_REPORT.pdf
mdls -name kMDItemNumberOfPages -name kMDItemContentType -name kMDItemFSSize outputs/preflight/PRODUCTION_READINESS_REPORT.pdf
sips -s format png outputs/preflight/PRODUCTION_READINESS_REPORT.pdf --out /tmp/serenity_readiness_report_page1.png
python -m app.cli package-delivery --json
unzip -tq outputs/package/serenity_daily_analysis_delivery.zip
```

## Results

- Prior full pytest before backfill display correction: 101 passed, 1 third-party moomoo DeprecationWarning
- Run-time display correction: future controlled backfills keep the latest recommendation and fund-fee data, but user-facing time labels show only the latest run time.
- Full pytest after backfill display correction: 103 tests collected and passed, 1 third-party moomoo DeprecationWarning
- Platform tradability advisory update: 104 tests collected and passed; `tests/test_scoring.py::test_platform_trade_status_is_advisory_only` confirms Alipay/MooMoo tradability is advisory-only and does not exclude Serenity candidates.
- Historical integrity guard update: 106 tests collected and passed; `tests/test_history_integrity.py` confirms historical rows/files allow append-only additions but block mutation, and `asset_master` keeps first-seen identity.
- Historical integrity baseline: `outputs/audit/history_integrity_baseline.json` covers 21 SQLite historical tables and 142 protected historical files; `history-integrity --require-pass` reports 0 violations.
- Historical artifact timeline update: `outputs/audit/history_artifact_timeline.csv` records protected report/snapshot file creation time, modification time, metadata-change time, size, SHA256, and linked run metadata; `outputs/audit/history_snapshot_table_timeline.csv` records protected SQLite snapshot table row counts, hashes, and first/last run creation times.
- User-facing run-time simplification: homepage and offline report index display only the latest run time; controlled-backfill responsibility remains internal to agent/audit code and is not shown to users.
- Targeted Gmail-compatible email tests: 6 passed for HTML notification drafts, Apple Mail HTML-send fallback, mail-smoke HTML artifacts, and integration notification paths.
- Schedule regression tests after 10-slot update: 25 passed
- Targeted UI/application/completion tests after app icon update: 19 passed
- Targeted completion/scheduler/comparison tests: 21 passed
- Targeted comparison/scheduler/automation/integration tests: 11 passed
- Targeted action-queue/intake/risk/completion tests: 20 passed
- Targeted UI/reporting/completion tests: 17 passed
- Completion audit after backfill display correction: `overall_status=complete`, `completion_percent=98.57%`.
- Email template: all active Mail paths now render Chinese action-first messages with Gmail-compatible HTML plus plain-text fallback. HTML mail includes H1/H2/H3 hierarchy, inline visual emphasis, highlighted required action behavior, and a current holding recommendation table; source chain, `sources_json`, `来源与时间戳`, and visible `运行 ID` are removed from email bodies.
- Email dry-run safety: `notify --dry-run` now writes a separate `_draft_preview` notification row and does not overwrite real sent notification evidence or `run_log.notification_status`.
- Latest Chinese draft preview: `data/notifications/sda_20260613T094539Z_r7_31fb1cc3_alert_mail.md` and `data/notifications/sda_20260613T094539Z_r7_31fb1cc3_alert_mail.html` render subject `[Serenity自动化][复核] 信号变化，保持当前持仓`, keep the latest production run status as `sent`, and have no source/timestamp evidence block.
- Formal strategy report template: `app/core/reporting.py::render_markdown_report` now renders the strategy Markdown/HTML report in Chinese; execution-lock markers, Top5 table, benchmark comparison, comparison section, rebalance matrix, evidence notes, and notification preview are all Chinese.
- Archived strategy reports: 24 existing Markdown/HTML report pairs in `data/reports` were regenerated with the Chinese report template; the offline report index was regenerated with Chinese status display.
- Latest strategy report language check: `data/reports/sda_20260613T053528Z_r8_2579b9f4_report.md` starts with `# Serenity 每日分析正式报告：...` and no longer contains the old `Serenity Daily Analysis Report`, `Run Status`, `Top5 Candidate Pool`, or `Execution Status` fields.
- Production preflight with `SERENITY_MAIL_SEND_ENABLED=true`: `production_ready=True`, blockers=0.
- Latest recommendation run remains `sda_20260613T094539Z_r7_31fb1cc3`; latest run time is displayed as plain `YYYYMMDD - HH:MM TimeZone`, data quality `pass`.
- Controlled backfill verification evidence: `sda_20260613T094539Z_r7_31fb1cc3`; run time `2026-06-15T14:30:00+08:00`, `verification_kind=future_controlled_backfill`, Mail/local notification sent. This is not a real 2026-06-15 market run.
- Baseline model: first run writes `baseline_snapshot`; daily updates compare against this Serenity baseline reference, not current Alipay holdings
- Top5 baseline: 007300, 008887, 110026, 011839, 013171
- Discipline state: latest production verification run has 5 baseline-relative Maintain labels and 1 rebalance review event.
- Source evidence audit: `status=pass`, rows=17, valid=17, invalid=0, local_hashes=3, urls=14
- Risk gate regression: `status=pass`, cases=`max_drawdown_block`, `recovery_time_block`
- Production action queue: `status=watch`, rows=4, priority_counts={'P2': 4}, blocker_counts={'benchmark_source_priority': 2, 'benchmark_history': 2}
- Schedule: Beijing `08:30-17:30` hourly, 10 runs total; configured slots are `R1=08:30`, `R2=09:30`, `R3=10:30`, `R4=11:30`, `R5=12:30`, `R6=13:30`, `R7=14:30`, `R8=15:30`, `R9=16:30`, `R10=17:30`; current Australia/Sydney display is `10:30-19:30 AEST`.
- Web entry: `outputs/application/index.html` is now a Chinese local app homepage with current holding recommendations, holdings advice, current/previous time context, weight timestamps, required action behavior, a run timeline above the operation-entry section, and a compact manual-review entry in the operation section. The duplicated `当前/上轮持仓对比` table has been removed; the holding-advice table is the single detailed weight comparison surface.
- Downloads app entry: `~/Downloads/Serenity 每日分析.app` is present as a clean shell `.app` bundle that opens the local homepage
- Applications app entry: `/Applications/Serenity 每日分析.app` is present as a clean shell `.app` bundle that opens the local homepage
- App icon: generated deterministic macOS icon resources at `outputs/application/serenity-app-icon.png`, `outputs/application/SerenityIcon.iconset/`, and `Contents/Resources/SerenityIcon.icns`; `Info.plist` sets `CFBundleIconFile=SerenityIcon`, uses a workspace-scoped bundle identifier, and writes `Contents/PkgInfo=APPL????`.
- App icon install verification: `SerenityIcon.icns` exists in `outputs/application/Serenity 每日分析.app`, `~/Downloads/Serenity 每日分析.app`, and `/Applications/Serenity 每日分析.app`; latest `.icns` size is 604959 bytes, all three icon SHA256 values match, LaunchServices was re-registered, and Finder/Dock were refreshed.
- Legacy entry cleanup: Serenity entries under `~/Downloads/application` were removed so the primary entry is not `~/Downloads/application`
- UI portal: Chinese operation homepage with fixed top-right refresh, local `/api/refresh` sync endpoint, refresh toast message in the requested `目前更新到最新时间 YYYYMMDD - HH:MM TimeZone ...` format, current-run and run-timeline labels displayed as latest run time instead of visible `R1-N` slot labels, cleaner current-holding recommendation cards, run timeline table/visual toggle with red buy markers, green sell markers and light-blue maintain markers, operation-entry fund-library panel showing all stored funds with subscription/redemption status, fee schedules, management/custody/sales-service/operating fees, source evidence, last candidate-entry time, current candidate-pool days and current candidate status, operation-entry usage-guide panel showing Skill selection logic, score formula, weight formula, adjustment logic, rebalance triggers, manual review and execution boundary, manual-review modal with decision selection/note/local-save/clear/copy actions, fund-detail click modal for current/previous Top5 holdings, first-Top5/last-candidate-entry/current-candidate-days/current-status/rule-snapshot timestamps, fee/status/source fields, command-copy feedback, and static HTML content checks for the new homepage requirements
- Browser UI verification: local HTTP preview opened `outputs/application/index.html`; clicking `基金库` opened 5 fund cards and clicking `查看详情` opened the single-fund detail modal with subscription/redemption fee schedule and management-fee fields; clicking `使用说明` opened 8 guide sections with score, weight, adjustment and execution-boundary logic visible
- Candidate-pool fund info browser verification: local HTTP preview opened `outputs/application/index.html`; clicking `基金库` opened 5 fund cards with `当前状态：在当前候选池` and `入池天数：3 天`; clicking `查看详情` opened the fund detail modal with `上次进入候选池时间`, `当前进入候选池天数`, `当前状态`, and `在当前候选池`; maintain/flat computed background is light blue `rgb(232, 244, 255)`.
- Snapshot report language verification: latest snapshot target remains `../../data/reports/sda_20260613T053528Z_r8_2579b9f4_report.html`; the regenerated report page title is `Serenity 每日分析正式报告 sda_20260613T053528Z_r8_2579b9f4`, and the visible report heading is `Serenity 每日分析正式报告`.
- Snapshot href regression: generated homepage href is `../../data/reports/sda_20260613T053528Z_r8_2579b9f4_report.html`, resolves to the existing report file, and the UI test blocks the prior invalid `../..//Users/...` absolute-path concatenation.
- Offline report index: regenerated in Chinese with search, status filters, run-id copy buttons, row-count feedback, and homepage return action
- Codex app automation: `serenity-daily-analysis-beijing-hour-slots` is PAUSED; `serenity-daily-analysis-beijing-half-hour-slots` is ACTIVE with current Australia/Sydney `10:30-19:30` half-hour wakeups, matching Beijing `08:30-17:30` hourly runs.
- Final ZIP: 356 members, `included_private_like_members=[]`; archive integrity check passed
- Formal readiness report and PDF regenerated in Chinese with baseline-first semantics and no absolute local path markers; PDF is 3 pages, size 764838 bytes, and first-page PNG rendering succeeded.
- README and data request contract updated: current Alipay holdings are optional overlay data only

## Key Evidence

- MooMoo/OpenD socket was already reachable; OpenD was user-opened and was not closed by this run
- MooMoo collection persisted 253 K-line rows in SQLite; US/HK proxies succeeded, selected CN market ETF/index probes are limited by quote permissions
- Benchmark smoke: `production_ready=True` with exact fallback windows; Shanghai Composite and S&P 500 1m/3m/10d windows are computable
- Benchmark caveat: exact benchmark history still uses public aggregation fallback where MooMoo/official exact index access is unavailable; MooMoo exact probes showed CN index permission rejection for `SH.000001` and unsupported/unknown exact SPX symbols, while SPY proxy was not promoted to exact production proof
- Hard risk gate evidence: deterministic synthetic regression now proves MDD >=40% creates Block/Clear/manual-review evidence and recovery >=365 days creates Manual Review/Block evidence
- Apple Mail: latest production verification sent a Mail alert/local notification successfully; recurring launchd plist still keeps `SERENITY_MAIL_SEND_ENABLED=false` by default
- No automatic trading/order execution code is present

## Remaining Warnings

- `shadow_ready_gate`: retained as a conservative warning because the installed launchd plist remains shadow-safe by default even though runtime preflight can pass with mail env enabled
- P2 benchmark quality upgrade: replace public aggregation fallback with exact MooMoo or official index/exchange evidence when permissions/data access allow; queue is now benchmark-specific instead of global-only

## Files To Open First

- `outputs/preflight/baseline_recommendation_latest.md`
- `outputs/preflight/PRODUCTION_READINESS_REPORT.md`
- `outputs/preflight/PRODUCTION_READINESS_REPORT.pdf`
- `outputs/preflight/PRODUCTION_DATA_REQUEST.md`
- `outputs/completion_audit/completion_audit_latest.md`
- `outputs/package/serenity_daily_analysis_delivery.zip`
