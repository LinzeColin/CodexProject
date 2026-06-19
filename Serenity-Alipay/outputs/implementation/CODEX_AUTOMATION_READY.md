# Serenity Daily Analysis: Codex Automation Ready

## Runtime Contract

- Default command: `/opt/anaconda3/bin/python -m app.cli automation-tick --no-dry-run --send-mail --local --require-production --json`
- Working directory: this delivery workspace root
- Primary timezone: `Asia/Shanghai`
- Secondary display timezone: `Australia/Sydney`
- Safety: no automatic trading; preflight failure forces dry-run; Beijing weekend ticks are skipped as `non_business_day`.

## Required Manual Smoke

```bash
python -m app.cli doctor
python -m app.cli init-db
python -m app.cli import-alipay --csv data/imports/alipay_positions.csv
python -m app.cli run --slot R7 --dry-run
python -m app.cli report
python -m app.cli notify --dry-run
python -m app.cli mail-smoke --json
python -m app.cli scheduler-tick --now 2026-06-12T14:30:00+08:00 --dry-run --allow-duplicate
python -m app.cli automation-tick --now 2026-06-12T15:30:00+08:00 --allow-duplicate --no-dry-run --json
python -m app.cli benchmark-smoke --require-production --json
python -m app.cli validate-intake --scan-path ~/Downloads --scan-path ~/Documents --json
python -m app.cli preflight --require-production --json
pytest -q
```

## launchd

Template: `outputs/implementation/com.serenity.daily-analysis.plist`

The template dispatches every 180 seconds and lets `automation-tick` decide whether a Beijing slot is due. Completion audit checks this schedule contract, the preflight-gated command, the workspace path, `SERENITY_DRY_RUN=true`, and `SERENITY_MAIL_SEND_ENABLED=false`. It uses `/opt/anaconda3/bin/python` because `/usr/bin/python3` does not have the MooMoo SDK in the current environment.

Install guide: `outputs/implementation/LAUNCHD_INSTALL_GUIDE.md`

Runtime status: `outputs/implementation/LAUNCHD_STATUS.md` and `outputs/implementation/LAUNCHD_STATUS.json`

Current local state: label `com.serenity.daily-analysis` is loaded; latest smoke wrote `non_business_day`, `dry_run=true`, stderr bytes `0`.

The shadow launchd plist does not send real email because it keeps `SERENITY_MAIL_SEND_ENABLED=false`. Real Apple Mail delivery is verified when the runtime explicitly supplies `SERENITY_MAIL_SEND_ENABLED=true` and the CLI is run non-dry-run.

## Codex App Automations

Codex app cron automation state for recurring wake-up execution:

- `serenity-daily-analysis-beijing-hour-slots`: PAUSED, retained only as the old whole-hour group.
- `serenity-daily-analysis-beijing-half-hour-slots`: ACTIVE, model `gpt-5.4`, reasoning `high`.

The active half-hour automation wakes on the current Australia/Sydney display times `10:30-19:30`, matching Beijing `08:30-17:30` hourly runs. The CLI still self-gates the true Beijing due slot.

Proposal details: `outputs/implementation/CODEX_AUTOMATION_PROPOSALS.md`

## Offline Webpage Platform

Open the local application portal:

```text
outputs/application/index.html
```

The Downloads app entry is available at:

```text
~/Downloads/Serenity 每日分析.app
```

Each completed run writes:

- Markdown report
- Offline HTML report
- Mail-ready notification draft
- SQLite records for audit and comparison

## Current Gate Status

- Shadow-ready: yes.
- Production-ready: yes when `SERENITY_MAIL_SEND_ENABLED=true` is supplied at runtime.
- Remaining blockers: none. Remaining watch items are P2 benchmark-source quality upgrades and live risk-gate regression evidence.
- Benchmark history: available through exact Yahoo Finance chart fallback, with source-priority warning.
- OpenD lifecycle: if already open, user-managed and left running; if auto-started by the tool, cleaned up after the run unless explicitly kept.
