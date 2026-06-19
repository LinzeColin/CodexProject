# Serenity Daily Analysis Delivery Package Manifest

Generated: 2026-06-13 11:14 AEST / 2026-06-13 09:14 Beijing

## Included Delivery Areas

- Source code: `app/`
- Tests: `tests/`
- Runtime metadata: `pyproject.toml`, `README.md`, `HANDOFF.md`
- Intake templates: `app/templates/`
- Sample/manual data: `data/imports/`, `data/manual/`
- SQLite audit DB: `data/serenity_daily.sqlite`
- Latest reports and notifications: `data/reports/`, `data/notifications/`
- MooMoo read-only collection output: `data/moomoo/`
- Requirements and PRD: `outputs/requirements/`
- Task Pack: `outputs/task_pack/`
- Audit notes: `outputs/audit/`
- Implementation and automation docs: `outputs/implementation/`
- launchd install guide: `outputs/implementation/LAUNCHD_INSTALL_GUIDE.md`
- launchd runtime status: `outputs/implementation/LAUNCHD_STATUS.md`, `outputs/implementation/LAUNCHD_STATUS.json`
- Codex automation proposal notes: `outputs/implementation/CODEX_AUTOMATION_PROPOSALS.md`
- Production preflight docs: `outputs/preflight/`
- Production unblock evidence matrix: `outputs/preflight/PRODUCTION_UNBLOCK_EVIDENCE_MATRIX.md`, `outputs/preflight/production_unblock_evidence_matrix.csv`
- Source evidence reference gate: enforced in `app/core/intake_validator.py` for Alipay `source_note`, fund-rule `url_or_path`, and candidate `source_url`
- Source evidence audit manifest: `outputs/preflight/source_evidence_audit_latest.md`, `outputs/preflight/source_evidence_audit_latest.csv`, `outputs/preflight/source_evidence_audit_latest.json`
- Source evidence SQLite archive: `data/serenity_daily.sqlite` table `source_evidence_audit_snapshot`
- Evidence intake guide: `outputs/intake_pack/EVIDENCE_INTAKE_GUIDE.md`
- Alipay/off-platform fund execution-window evidence: `outputs/preflight/ALIPAY_FUND_EXECUTION_WINDOW_EVIDENCE.md`
- Alipay/QuantLab holdings review matrix: `outputs/preflight/alipay_holdings_review_matrix.csv`
- Production intake pack: `outputs/intake_pack/`
- Review-assisted intake helpers: `outputs/intake_pack/06_alipay_positions_review_prefill.csv`, `outputs/intake_pack/07_special_fund_rule_checklist.csv`, `outputs/intake_pack/08_fund_rules_from_review_checklist.csv`, `outputs/intake_pack/09_candidate_source_review_prefill.csv`
- Completion audit: `outputs/completion_audit/`
- Benchmark dynamic window gate: `benchmark-smoke` defaults to latest Beijing weekday plus 103-day lookback, checked by `benchmark_dynamic_window`
- Business-day schedule gate: recurring automation skips Beijing weekends by default and records `non_business_day`
- Formal report path-redaction gate: checked in completion audit for `PRODUCTION_READINESS_REPORT.md` and `.pdf`
- Formal readiness/package consistency gate: checked in completion audit against `outputs/package/package_latest.json`
- Execution-lock zero-order guard: checked by completion audit to keep degraded reports at `No-New-Order`, suggested amount `0.00`, and suggested units `0`
- launchd runtime gate: checked by completion audit to verify loaded runtime evidence, safe dry-run tick, disabled real mail sending, and no automatic trading
- Production alert-send gate: `mail_send_config` blocks production readiness while `SERENITY_MAIL_SEND_ENABLED=false`
- Apple Mail smoke artifact: `outputs/preflight/apple_mail_smoke_latest.md`, `outputs/preflight/apple_mail_smoke_latest.json`
- Validation summary: `outputs/tests/VALIDATION_SUMMARY.md`
- Formal readiness PDF: `outputs/preflight/PRODUCTION_READINESS_REPORT.pdf`
- Privacy-aware package build report: `outputs/package/package_latest.md`, `outputs/package/package_latest.json`
- Chinese local app homepage with current holding recommendations, update/compare timestamps, weight timestamps, merged current/previous strategy-share comparison, fixed refresh backed by the local `/api/refresh` server endpoint, and current/previous Top5 fund-detail modal with first-Top5, rule-snapshot, fee/status/source fields: `outputs/application/index.html`
- macOS app bundle entry: `outputs/application/Serenity 每日分析.app`
- Downloads installed app entry: `~/Downloads/Serenity 每日分析.app`
- macOS Applications installed app entry: `/Applications/Serenity 每日分析.app`

## Final Sample Run

- Run ID: `sda_20260612T232914Z_r7_3376fbc9`
- Slot: R7, Beijing `2026-06-15T14:00:00+08:00`
- Status: `success`, data quality `pass`, notification `sent;local=sent`
- Markdown: `data/reports/sda_20260612T232914Z_r7_3376fbc9_report.md`
- Offline HTML: `data/reports/sda_20260612T232914Z_r7_3376fbc9_report.html`
- Offline index: `data/reports/index.html`
- Notification: `data/notifications/sda_20260612T232914Z_r7_3376fbc9_info_mail.md`
- Baseline discipline: 5 `Maintain` labels, 0 rebalance events, baseline-relative deviation `0.00%`

## Latest MooMoo Collection

- Run ID: `moomoo_collect_20260612T133659Z_c879eddf`
- Status: `success`
- Snapshot: `data/moomoo/moomoo_collect_20260612T133659Z_c879eddf/snapshot.json`
- Daily K-line: `data/moomoo/moomoo_collect_20260612T133659Z_c879eddf/US_SPY_K_DAY_2026-06-01_2026-06-12.csv`
- SQLite evidence: MooMoo source entries and 10 `market_kline_snapshot` rows
- OpenD lifecycle: socket was already reachable, `started_by_tool=false`, no cleanup attempted

## Latest Benchmark Smoke

- Status: `pass`
- Production-ready by benchmark: Shanghai Composite `true`, S&P 500 `true`
- Default window: dynamic latest Beijing weekday plus 103-day lookback; latest run resolved to 2026-03-01 through 2026-06-12
- Source: exact Yahoo Finance chart fallback, source priority 5 public aggregation
- Generated history: `data/manual/benchmark_price_history.csv`
- Shanghai Composite rows: 70
- S&P 500 rows: 73
- MooMoo proxy evidence: `US.SPY` and `US.VOO` each returned 73 rows, but proxy ETF data remains warning-only and cannot unlock exact benchmark proof
- Report: `outputs/preflight/benchmark_smoke_latest.md`
- Formal production readiness report: `outputs/preflight/PRODUCTION_READINESS_REPORT.pdf`

## Production Gate

- Preflight status: `production_ready=true`, `shadow_ready=true`
- `SERENITY_MAIL_SEND_ENABLED=true python -m app.cli preflight --json`: production-ready with blockers=0, warnings=1
- Automation entrypoint: `/opt/anaconda3/bin/python -m app.cli automation-tick --no-dry-run --send-mail --local --json`
- Controlled Mail smoke entrypoint: `python -m app.cli mail-smoke --json`
- Intake pack entrypoint: `python -m app.cli production-intake-pack --scan-path ~/Downloads --scan-path ~/Documents --json`
- Intake promotion entrypoint: `python -m app.cli promote-intake-pack --apply --json`
- Completion audit entrypoint: `python -m app.cli completion-audit --require-complete --json`
- Delivery package entrypoint: `python -m app.cli package-delivery --json`
- Remaining warning: launchd template remains shadow-safe with real mail disabled by default; production mail requires explicit runtime env enablement

## Exclusions

- Python cache files are excluded.
- Private evidence directories are excluded by default: `evidence/`, `outputs/intake_pack/evidence/`, `data/backups/`.
- `outputs/package/package_latest.*` is treated as an external build log and is excluded from the ZIP to avoid stale self-references.
- No secrets, cookies, passwords, or API keys are included.
- No automatic trading credentials or order-execution logic is included.
