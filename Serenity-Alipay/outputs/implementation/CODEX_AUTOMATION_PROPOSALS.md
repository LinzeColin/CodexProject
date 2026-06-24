# Serenity Daily Analysis Codex App Automations

Generated: 2026-06-13

Codex app cron automations are retained but paused for sidebar hygiene:

1. `serenity-daily-analysis-beijing-hour-slots` - PAUSED legacy whole-hour wakeup group.
2. `serenity-daily-analysis-beijing-half-hour-slots` - PAUSED legacy Codex cron group.

Local `launchd` now owns recurring execution so automatic production ticks do not create Codex sidebar chats. The CLI still self-gates the true Beijing due slot before running the strategy pipeline.

## Runtime Command

The retained Codex cron definitions use the same deterministic command if manually re-enabled:

```bash
/opt/anaconda3/bin/python -m app.cli automation-tick --no-dry-run --send-mail --local --require-production --json
```

## Safety Contract

- The command runs preflight before a due-slot strategy run.
- If preflight is not production-ready, the command exits non-zero through `--require-production` and reports blockers.
- If OpenD was already running, it leaves OpenD running.
- If the tool starts OpenD, it cleans up only the process it started unless configured otherwise.
- No trading execution exists.
- Real Apple Mail send now follows the command-driven production path: `--send-mail` on a non-dry-run production-ready command. The one-off production verification run has already sent Mail and local notification successfully.

## Current Verification

- Latest verified run: `sda_20260612T232914Z_r7_3376fbc9`
- Slot: R7
- Beijing time: `2026-06-15T14:30:00+08:00`
- Data quality: `pass`
- Mail/local notification: sent
