# Phase 11 SMTP Delivery Boundary

Project: `arxiv-daily-push`
Task: `ADP-PHASE11-SMTP-DELIVERY-007`
Acceptance: `ADP-ACC-PHASE11-SMTP-DELIVERY`
Version: `0.11.6`
Generated: `2026-06-21`

## Objective

Add a fail-closed SMTP notification boundary so the system can produce
notification delivery evidence by default and attempt real SMTP only when
explicitly allowed.

## Implemented

- Added `src/arxiv_daily_push/smtp_delivery.py`.
- Added `adp send-notification`.
- Added `schemas/smtp_delivery.schema.json`.
- Added tests for dry-run delivery, missing SMTP environment blocking, mocked
  SMTP send, TLS startup, recipient targeting, and CLI dry-run JSON.
- Updated the production trial runbook with dry-run and explicit `--allow-send`
  commands.

## Safety Boundary

- Dry-run is the default and makes no SMTP connection.
- Real SMTP requires `--allow-send`.
- Real SMTP requires `ADP_SMTP_HOST`, `ADP_SMTP_PORT`,
  `ADP_SMTP_USERNAME`, and `ADP_SMTP_PASSWORD`.
- TLS is required before login.
- Delivery reports include recipient, subject, body SHA256, key names, and
  status only.
- SMTP secret values and email body text are not logged.
- Wrong recipient, missing environment keys, invalid port, SMTP exception, or
  refused recipient blocks delivery evidence.

## Current Status

`pass for code gate`

This phase does not claim real production SMTP delivery. Production acceptance
still requires archived real SMTP evidence to `linzezhang35@gmail.com` generated
on the provisioned runner during the 30-day trial.

## Validation

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_smtp_target PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_notifications.py arxiv-daily-push/tests/test_cli.py -q`: 9 focused tests OK.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_smtp_cli PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push send-notification --run-id run-001 --summary 'Daily status' --date 2026-06-21 --generated-at 2026-06-21T05:00:00+10:00 --json`: dry-run evidence emitted.

Full validation results are recorded in the governance run manifest after the
complete local validation suite.

## Remaining Risks

- SMTP secrets are not configured in this local environment.
- Real SMTP delivery against the production SMTP provider is not verified.
- Production acceptance still requires runner provisioning, CA trust repair,
  Release configuration, scheduler, weekly/monthly replay, recovery drill, and
  30-day evidence.

## Rollback

Revert `smtp_delivery.py`, the `send-notification` CLI command,
`smtp_delivery.schema.json`, related tests, runbook updates, and restore
version `0.11.5`.
