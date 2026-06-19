# 09 Deployment Guide

## MVP Environment

Target:

- macOS local machine.
- Python 3.10+.
- SQLite.
- Optional moomoo/OpenD local gateway.
- Optional Apple Mail configured for sending or drafting.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -r requirements.txt
python -m app.cli init-db
python -m app.cli doctor
```

## Manual Run

```bash
python -m app.cli run --slot R7 --dry-run
```

## launchd Scheduling

Create one launchd job that runs a scheduler dispatcher every few minutes, or create per-slot jobs. The dispatcher is preferred.

Dispatcher command:

```bash
python -m app.cli scheduler-tick --dry-run
```

The scheduler must evaluate Beijing time, not local system assumptions.

## Mail Notification

MVP should default to:

1. Render notification Markdown.
2. Create Apple Mail draft or `.eml`.
3. Optionally send local macOS notification.
4. Run `python -m app.cli mail-smoke --json` for draft-only Mail readiness.
5. Send actual email only when user confirms with `SERENITY_MAIL_SEND_ENABLED=true` and `--confirm-real-send SEND`.

Recipient:

```text
linzezhang35@gmail.com
```

## Operational Modes

- `dry_run=true`: no real email send, no browser extraction, no external write.
- `SERENITY_MAIL_SEND_ENABLED=true`: allow Mail send after explicit user confirmation and `mail-smoke` real-send validation.
- `fallback_aggregated_enabled=true`: allow downgraded fallback data.

## Rollback

- Disable launchd plist.
- Keep SQLite DB and reports for audit.
- Re-run with `--dry-run`.
- Restore previous config from backup.
