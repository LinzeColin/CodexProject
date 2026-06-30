# S2PLT02 Terminal Proof Evidence Inventory Input Hardening

- Timestamp: 2026-06-30 16:36:09 Australia/Sydney
- Task ID: `S2PLT02-TERMINAL-PROOF-EVIDENCE-INVENTORY-INPUT-HARDENING`
- Parent task: `S2PLT02-TERMINAL-DELIVERY-PROOF`
- Acceptance: `ACC-S2PLT02-2D`
- Status: `blocked_s2plt02_inventory_launchctl_missing_file_fail_closed_no_production`

## What Changed

`audit-s2plt02-terminal-proof-evidence-inventory` now treats a missing `--launchctl-disabled-file` as a machine-readable blocker instead of raising `FileNotFoundError`.

The blocked JSON includes:

- `launchctl_disabled_file_missing`
- `launchctl_disabled_file_status=missing`
- `launchctl_disabled_file_ref`
- a recomputed `state_hash`
- no state validation error from hash drift

## Current Evidence

- Missing-file CLI result: blocked / exit 2
- Missing-file state hash: `b43760c8150155bb0f40e627cdec97443451bfad63e1257b08d1fd572dccda39`
- Normal read-only local inventory result: blocked / exit 2
- Normal read-only local inventory state hash: `d2f12b5f3fbe439fdd0b2d420706700f5a0aa6b3d9ba691da67f2ffe4758d117`
- Current observed real delivery days: `1/2`
- Current observed real emails: `4/8`
- Current nonterminal dry-run days: `2`

## Remaining S2PLT02 Inputs

- `SECOND_REAL_DELIVERY_DAY`
- `EIGHT_REAL_EMAILS`
- `REAL_SCHEDULER_PROOF`
- `S2PLT02_TERMINAL_DELIVERY_PROOF_ARTIFACT`

## Boundary

This change does not send SMTP, enable scheduler, install/kickstart launchd, upload Release assets, execute restore, mutate public schema/DB/source/ranking/queue, change CURRENT/V7, write `FINAL_ACCEPTANCE_BUNDLE/s2plt02_terminal_delivery_proof.json`, or claim S2PLT02/S2PLT03/S2PLT04/S2PMT07/Stage2/S3 production acceptance.

## Validation

- TDD red: focused CLI test failed with `FileNotFoundError`.
- TDD green: focused CLI test passed.
- Live missing-file CLI: blocked / exit 2 with no traceback.
- Normal local evidence inventory CLI: blocked / exit 2 with no state validation errors.

