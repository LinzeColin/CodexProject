# S2PMT07 Authorized Controlled Real Run Acceptance

## Result

Status: `pass_controlled_real_run_evidence_rechecked_no_new_send`

The owner authorized exactly one controlled foreground real-run acceptance check:
`允许一次受控真实运行验收，临时启用发送后立马禁止，不产生后台内存线程压力`.

The foreground `local-runner daily --allow-smtp-send` command completed for service date
`2026-07-01` with `status=pass`, `real_smtp_sent=true`, `sent_mail_count=4`, and
M1/M2/M3/M4 all sent. The command reused the existing `2026-07-01`
daily input report and consumed already-recorded sent evidence from the local ledger,
so no duplicate SMTP send was attempted in this run:

- `newly_sent_mail_products=[]`
- `historical_sent_mail_products=[M1,M2,M3,M4]`
- `duplicate_smtp_send_avoided=true`

## Evidence

- Run manifest: `governance/run_manifests/ADP-S2PMT07-AUTHORIZED-CONTROLLED-REAL-RUN-ACCEPTANCE-20260701.json`
- Runtime report: `/Users/linzezhang/.adp/arxiv-daily-push/runs/20260701/adp-local-runner-report.json`
- Runtime report sha256: `123d516e640aa6549b32ff50ce927a71adc7a765175f8a16ea6a6f6be50f401e`
- Pre-run backup: `/Users/linzezhang/.adp/arxiv-daily-push/runs/20260701_before_authorized_controlled_acceptance_20260701T061024Z`

## Safety Boundary

This evidence does not write `INTEGRATED_PRODUCTION_ACCEPTED`, does not enable
`DAILY_OPERATION`, and does not install or enable scheduler, Release, or production
restore. Post-run safety state:

- persistent `ADP_ALLOW_SMTP_SEND=false`
- process `ADP_ALLOW_SMTP_SEND=false`
- `com.linze.adp.local.daily`, `com.linze.adp.local.health`, and
  `com.linze.adp.local.watchdog` remain disabled
- no ADP background process remains

## Next Step

The next S2PMT07 boundary remains an explicit production acceptance/write decision
or a deliberate pause. This controlled foreground run is evidence, not a standing
production permission.
