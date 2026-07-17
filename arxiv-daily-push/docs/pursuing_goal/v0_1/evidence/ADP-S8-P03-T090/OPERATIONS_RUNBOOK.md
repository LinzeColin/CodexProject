# OPERATIONS RUNBOOK · ADP V0.1 (T090)

> live build 452f7c5de919 on adp.linzezhang.com; rollback target d5890974 (b189d3cc0703).

## deploy
edit deploy/cloudflare/worker_cloud.js -> node --check -> record current version -> cd deploy/cloudflare && npx wrangler@4 deploy --config wrangler_cloud.jsonc -> verify build.json + six themes + routes on adp.linzezhang.com

## rollback
npx wrangler@4 versions deploy <prior-version-id> --config wrangler_cloud.jsonc (current rollback target: d5890974 = b189d3cc0703)

## d1_migrate
npx wrangler@4 d1 execute adp-mirror --remote --file <ddl.sql> (idempotent CREATE ... IF NOT EXISTS)

## canary
each capability behind an independent flag (BOARD3_A0_ONLY / RAW_DUALWRITE / RUM_ENABLED + RUM_SAMPLE dial); kill switch = set flag off / lower RUM_SAMPLE; see CANARY_PLAN.md (T088)

## error_budget_autostop
DIR-007 R2_BUDGET fail-closed guard (guardFrac 0.9); on breach the write halts (over_budget)

## disaster_recovery
restore any month from the T027 open snapshot into isolated SQLite (T029/T086); every component recovers to a committed known point

## soak
run the daily cron (30 20) for 14 consecutive days appending a daily manifest; T089 closes at 14/14 with no Sev-1/2 (soak_stopline_drill.py schema)

## cost_monitoring
DIR-007 free-tier budget (R2 10GB / 1M Class A / 10M Class B); monitor per soak_framework; R2 dual-write is SHADOW-active (~90 Class A/mo)

## known gaps
- T089 14-day production soak (clause 1) is calendar-bound -- Owner-waived for release; the operator runs 14 daily crons to close it
- held capabilities (A1/A2 subnational, S5 multi-board depth, S6 prediction models) are proven-in-evidence but NOT deployed -- each is promotion-gated (per-capability Owner go)
- the CWV quality error-budget auto-stop is a defined rule that still needs deploy-side monitoring wiring (T088 known_gaps)
- R2 raw-artifact dual-write is SHADOW-active in production (RAW_DUALWRITE=true) within the free tier -- monitor per DIR-007

## next version backlog
- complete the 14-day soak (T089 clause 1) and close T090 traceability to 90/90 fully-terminal
- promote held capabilities via the T088 canary framework, each behind its Owner gate (A1/A2 cohorts, S5 depth, S6 model promotion)
- wire the CWV quality error-budget auto-stop to live monitoring
- add real screenshot/pixel layer over the T077 visual matrix (currently source-hash gate only)
