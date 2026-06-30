# S2PLT02-TERMINAL-CAPTURE-WAIT-STATE-READONLY-COMMAND-CONTRACT

- Timestamp: 2026-07-01 01:50:16 Australia/Sydney
- Status: blocked / no production side effects
- Parent task: `S2PLT02-TERMINAL-DELIVERY-PROOF`
- Current V7 task: `S2PMT07`
- Acceptance: `ACC-S2PLT02-2D`, `ACC-S2PMT07-FINAL-REVIEW`

## What Changed

`capture_wait_state_guard.allowed_readonly_commands[0]` now includes the required `--generated-at 2026-06-30T18:03:24+10:00` argument. The previous guard exposed a plan command without that argument, but the real CLI requires it and would return argparse usage instead of the blocked JSON plan.

## Evidence

- copy-paste command: `adp plan-s2plt02-terminal-delivery-proof-capture --repo-root . --generated-at 2026-06-30T18:03:24+10:00 --json`
- S2PLT02 capture plan state hash: `5b344929d8d00c9cf881accbbd9abd68963b5f40cbd975a805fa4da62a8a8a25`
- focused capture plan state hash: `8203f3c5d744fe829ee488a4402deb4a4cdcb0c1501192f8c0c96487253424a9`
- wait guard state hash: `581fe9f53d82db88959196f874d312e50b1739a839158f7bf2d38cc186c03506`
- focused wait guard state hash: `fb8f593d2d804687c9a12bc969659aa8c05a1d09ad49fc5b574a2182eeac5569`
- final-bundle prerequisite plan state hash: `8409313fd39c4627122aca97cc80d28480f65b5230f6982ae7e720b6e0134b73`
- final readiness state hash: `eef4f33e08feb99de67c24c9339ae204658f6b0ac4d0e5cd810092b5a3246aff`
- run manifest: `governance/run_manifests/ADP-S2PLT02-TERMINAL-CAPTURE-WAIT-STATE-READONLY-COMMAND-CONTRACT-20260701.json`

## Validation Intent

- TDD red: final-gate regression failed because the wait guard command lacked `--generated-at`.
- Green: final-gate and CLI regressions require the command to be parseable and to return blocked JSON, not argparse usage.

## Boundary

No S2PLT02/S2PLT03 terminal proof artifact, S2PLT04 completion report, final-bundle manifest/handoff/signoff/final-command proof, SMTP send, scheduler enable/install/kickstart, Release, restore, CURRENT/V7 change, public schema/DB/source/ranking/queue mutation, P0/P1 closure claim, S2PLT02/S2PLT03/S2PLT04/S2PMT07 acceptance, DAILY_OPERATION, Stage2/S3 production acceptance, or production side effect is introduced.
