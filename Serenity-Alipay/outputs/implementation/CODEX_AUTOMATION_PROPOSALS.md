# Serenity Daily Analysis Codex App Automations

Generated: 2026-06-13

Codex app cron automations are installed with the new 10-run Beijing schedule:

1. `serenity-daily-analysis-beijing-hour-slots` - PAUSED legacy whole-hour wakeup group.
2. `serenity-daily-analysis-beijing-half-hour-slots` - ACTIVE, current Australia/Sydney `10:30-19:30`, matching Beijing `08:30-17:30` hourly runs.

The active automation maps the requested Beijing schedule into the current Australia/Sydney display timezone and avoids broad extra runs. The CLI still self-gates the true Beijing due slot before running the strategy pipeline.

## Runtime Command

Both automations use the same deterministic command:

```bash
/opt/anaconda3/bin/python -m app.cli automation-tick --no-dry-run --send-mail --local --require-production --json
```

## Safety Contract

- The command runs preflight before a due-slot strategy run.
- If preflight is not production-ready, the command exits non-zero through `--require-production` and reports blockers.
- If OpenD was already running, it leaves OpenD running.
- If the tool starts OpenD, it cleans up only the process it started unless configured otherwise.
- No trading execution exists.
- Real Apple Mail send requires `SERENITY_MAIL_SEND_ENABLED=true` in the runtime environment; the one-off production verification run has already sent Mail and local notification successfully.

## Current Verification

- Latest verified run: `sda_20260612T232914Z_r7_3376fbc9`
- Slot: R7
- Beijing time: `2026-06-15T14:30:00+08:00`
- Data quality: `pass`
- Mail/local notification: sent
