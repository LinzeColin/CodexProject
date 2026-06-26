# PHASE S2PLT01 - Replay Evidence Gate

Task: `S2PLT01-REPLAY-EVIDENCE-GATE`
Parent Task: `S2PLT01`
Acceptance: `ACC-S2PLT01-30D`
Status: `local_validation_passed_pending_pr_ci`

## Purpose

This record adds a machine gate that can consume already-produced S2PLT01
evidence records for 30 historical replay days, 120 M1-M4
`EMAIL_LEARNING_V1` mail previews, and D1-D4 terminal source states without
executing replay or creating production side effects.

## Current Result

The helper `build_s2plt01_replay_evidence_from_records` now validates:

- 30 unique passing replay dates.
- D1-D4 source-domain coverage in replay records.
- B1-B6 reading-board coverage in replay records.
- 120 no-send M1/M2/M3/M4 mail preview records using `EMAIL_LEARNING_V1`.
- D1-D4 terminal source states with `production_inclusion` false.
- zero future leakage and zero replay P0/P1 blocker counters.
- non-empty evidence references for accepted replay, mail, and terminal-source
  records.

`build_s2plt01_entry_precheck_report` can consume a passing replay evidence
state and remove replay/mail/source blockers while still remaining blocked by
inherited V7.1 P0=8 and P1=37. `ACC-S2PLT01-30D` is not accepted by this
record.

## Scope

- Local helper: `arxiv_daily_push.stage2_replay_gate`.
- Focused tests for passing evidence, missing mail previews, missing terminal
  domains, consumed replay evidence, inherited blocker preservation, and
  no-production flags.
- Governance refresh for `FORM-ADP-103`, `MOD-ADP-101` evidence references,
  traceability, delivery task, event, and run manifest.

## Non Scope

No real 30-day replay execution, no S2PLT01 acceptance, no S2PLT04 completion,
no integrated production acceptance, no DAILY_OPERATION, no real SMTP send, no
scheduler enablement, no Release upload, no production queue mutation, no public
schema change, no DB migration, no source adapter or ranking change, no CURRENT
pointer change, no V7.1 baseline change, and no V7.2 contract-file change.

## Next

Use this gate after actual S2PLT01 replay/mail/source evidence exists. S2PLT01
remains blocked until inherited P0/P1 are zero and the replay evidence payload is
provided and independently reviewed. S2PLT04 and S2PMT07 remain blocked.
