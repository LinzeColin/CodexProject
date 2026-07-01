# S2PMT07 Controlled Real Run Dedupe Acceptance

- Task: `S2PMT07-CONTROLLED-REAL-RUN-DEDUPE-ACCEPTANCE`
- Time: `2026-07-01 14:38:36 Australia/Sydney`
- Scope: owner-authorized single foreground controlled real-run acceptance.
- Command style: foreground CLI only; no `launchctl kickstart`, no scheduler bootstrap, no background thread.

## Result

- Status: `pass`
- Service date: `2026-07-01`
- Planned mail products: `M1`, `M2`, `M3`, `M4`
- Sent mail count confirmed by ledger/history: `4 / 4`
- Newly sent mail products in this run: none
- Historical same-day sent products consumed: `M1`, `M2`, `M3`, `M4`
- Report SHA-256: `7e1c0a0a53db5f1adbb947313526c3f0ffda64da66a1d413754a087b5fe934b1`

## Evidence

- Run manifest: `governance/run_manifests/ADP-S2PMT07-CONTROLLED-REAL-RUN-DEDUPE-ACCEPTANCE-20260701T043836Z.json`
- Local runtime evidence: `/tmp/adp_controlled_real_run_20260701T043836Z.json`
- Runtime state dir: `/Users/linzezhang/.adp/arxiv-daily-push`

## Safety Closeout

- Persistent `ADP_ALLOW_SMTP_SEND=false` after the foreground run.
- `com.linze.adp.local.daily`, `com.linze.adp.local.health`, and `com.linze.adp.local.watchdog` remained disabled.
- No ADP background process remained after closeout.
- No SMTP duplicate was sent by this run.
- No scheduler, Release, restore, DAILY_OPERATION, CURRENT/V7 change, public schema change, DB migration, source adapter change, ranking change, or queue algorithm change was introduced.
- This is not `INTEGRATED_PRODUCTION_ACCEPTED` and not Stage2/S3 production accepted.
