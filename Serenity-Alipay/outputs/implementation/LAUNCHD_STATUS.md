# Serenity Daily Analysis launchd Runtime Status

Generated: 2026-06-13 02:18:18 AEST / 2026-06-13 00:18:18 Beijing

## Status

| Check | Result |
|---|---|
| launchd label | `com.serenity.daily-analysis` |
| install state | `loaded` |
| plist lint | `OK` |
| latest smoke action | `non_business_day` |
| latest smoke dry-run | `true` |
| stderr bytes | `0` |
| mail send enabled | `false` |
| automatic trading | `false` |
| production ready | `false` |
| shadow ready | `true` |

## Latest Tick

- Beijing time: `2026-06-13T00:16:53+08:00`
- Australia/Sydney time: `2026-06-13T02:16:53+10:00`
- Action: `non_business_day`
- Due slot: `none`
- Run ID: `none`
- Dry-run: `true`

## Safety

- Current prohibited action: `No-New-Order`
- Current blockers: `alipay_positions`, `candidate_universe`, `fund_rules`
- Real Apple Mail sending is disabled by config.
- No automatic trading path exists.
- Beijing weekend ticks are logged as `non_business_day` and do not run preflight or strategy reports.
- User-opened OpenD remains running; this launchd smoke did not start or stop OpenD.
