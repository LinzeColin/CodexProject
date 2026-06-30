# S2PMT07 Final Bundle S2PLT02 Terminal Count Split

| Field | Value |
|---|---|
| Task | `S2PMT07-FINAL-BUNDLE-S2PLT02-TERMINAL-COUNT-SPLIT` |
| Phase | `S2PL` |
| Gate | `S2PMT07_FINAL_BUNDLE_S2PLT02_TERMINAL_COUNT_SPLIT_BLOCKED_NO_PRODUCTION` |
| Status | `blocked` |
| Acceptance | `ACC-S2PMT07-FINAL-REVIEW`, `ACC-S2PLT02-2D` |
| Timestamp | `2026-07-01 00:13:52 Australia/Sydney` |
| Run manifest | [`governance/run_manifests/ADP-S2PMT07-FINAL-BUNDLE-S2PLT02-TERMINAL-COUNT-SPLIT-20260701.json`](../../governance/run_manifests/ADP-S2PMT07-FINAL-BUNDLE-S2PLT02-TERMINAL-COUNT-SPLIT-20260701.json) |

## Objective

Make S2PLT02 final-bundle summaries separate existing real SMTP input counts from the current capture-window additions, so a future reviewer cannot treat the 2026-06-29/2026-06-30 dry-run window as the second real terminal delivery day.

## Current Evidence

- `plan-final-bundle-prerequisites --json` remains blocked / exit 2 with `state_hash=fb04c0b2582c24bdecf9d6d33658f25139ab8cf656cd6e22c69f01e5a3e1c419`.
- `validate-final-acceptance-bundle --repo-root . --json` remains blocked / exit 2 with `state_hash=7527930ba22a849c42ff55a0e65ea3c4b242e6c629f51db671468b63a1925a2b`.
- `plan-s2plt02-terminal-delivery-proof-capture --repo-root . --generated-at 2026-06-30T18:03:24+10:00 --json` remains blocked / exit 2 with `state_hash=e7c9834eca19f665f1b57566f47cbd03ecaaf95fa9eb538187af3c3f7e1aa7f1`.
- Existing validated terminal inputs: `observed_real_delivery_days=1`, `observed_real_email_count=4`.
- Current capture-window additions: `current_capture_window_real_delivery_days_added=0`, `current_capture_window_real_email_count_added=0`.
- Rejected dry-run count: `current_capture_window_dry_run_email_count_rejected=8`.
- Terminal proof after current window remains `1/2` real days and `4/8` real emails; remaining gaps are `1` real day and `4` real emails.

## Boundary

No S2PLT02/S2PLT03 terminal proof artifact, S2PLT04 completion report, final-bundle manifest/handoff/signoff/final-command proof, SMTP send, scheduler enable/install/kickstart, Release, restore, CURRENT/V7 change, public schema/DB/source/ranking/queue mutation, P0/P1 closure claim, S2PLT02/S2PLT03/S2PLT04/S2PMT07 acceptance, DAILY_OPERATION, Stage2/S3 production acceptance, or production side effect is introduced.

## Validation

- TDD red: focused final-gate tests failed with missing `observed_real_counts_source` and terminal proof after-current-window fields.
- TDD green: focused final-gate tests passed 3 OK after the split fields and validators were added.
- Full project validation is recorded in the run closeout, not as production acceptance.
