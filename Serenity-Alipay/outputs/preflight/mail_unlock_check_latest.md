# Mail Unlock Check

- Generated: 2026-06-13T04:46:40+08:00
- Status: pass
- Workflow ready: True
- Production send ready now: False
- Mail send enabled now: False
- Recipient: `linzezhang35@gmail.com`
- Production plist generated: True
- Production plist path: `outputs/implementation/com.serenity.daily-analysis.production-mail.plist`

## Required Manual Gate

Run the real-send smoke only after production data gates pass and you explicitly want a real test email:

```bash
SERENITY_MAIL_SEND_ENABLED=true python -m app.cli mail-smoke --send --confirm-real-send SEND --require-send-ready --json
```

Install the production-mail launchd plist only after the real-send smoke succeeds:

```bash
cp outputs/implementation/com.serenity.daily-analysis.production-mail.plist ~/Library/LaunchAgents/com.serenity.daily-analysis.plist && plutil -lint ~/Library/LaunchAgents/com.serenity.daily-analysis.plist && launchctl kickstart -k "gui/$(id -u)/com.serenity.daily-analysis"
```

Rollback command:

```bash
cp outputs/implementation/com.serenity.daily-analysis.plist ~/Library/LaunchAgents/com.serenity.daily-analysis.plist && launchctl kickstart -k "gui/$(id -u)/com.serenity.daily-analysis"
```

## Boundary

- This command does not send mail.
- This command does not install or reload launchd.
- This command does not place trades.
- Current production remains blocked until data gates pass and a real-send smoke is explicitly approved.
